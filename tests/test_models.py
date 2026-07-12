"""Tests for TDDB acceleration model fitting.

Tests E-model, 1/E model, V model and E-Arrhenius global fitting.
"""
import numpy as np
import pytest

from core.tddb.models import (
    fit_e_model,
    fit_1e_model,
    fit_v_model,
    fit_e_arrhenius,
    predict_lifetime,
    predict_failure_rate,
)


class TestFitEModel:
    """E-model: t = A * exp(-gamma * Eox), Eox = V/Tox."""

    def test_perfect_e_model_recovery(self):
        """Generate data from known E-model params and recover them."""
        gamma_true = 2.0  # cm/MV
        a_true = 1e20  # scaling factor
        tox = 5.0  # nm
        voltages = np.array([5.0, 5.5, 6.0, 6.5])
        # Eox in MV/cm: Eox = V / tox * 10 (tox in nm → cm conversion)
        eox = voltages / tox * 10.0
        etas = a_true * np.exp(-gamma_true * eox)

        result = fit_e_model(voltages, etas, tox)
        assert abs(result["gamma"] - gamma_true) < 0.1
        assert abs(result["a"] / a_true - 1.0) < 0.5  # order-of-magnitude

    def test_r_squared_good(self):
        tox = 5.0
        voltages = np.array([5.0, 5.5, 6.0])
        etas = np.array([500, 200, 80])
        result = fit_e_model(voltages, etas, tox)
        assert result["r2"] > 0.95

    def test_low_voltage_longer_life(self):
        """E-model predicts lower voltage → longer lifetime."""
        tox = 5.0
        voltages = np.array([4.5, 5.0, 5.5, 6.0])
        etas = np.array([800, 400, 150, 50])
        result = fit_e_model(voltages, etas, tox)
        # Predict at a voltage below the min test voltage
        pred_low = predict_lifetime("E", result, 3.3, 25, tox)
        pred_high = predict_lifetime("E", result, 6.0, 25, tox)
        assert pred_low > pred_high

    def test_requires_at_least_2_points(self):
        with pytest.raises(ValueError, match="at least 2"):
            fit_e_model(np.array([5.0]), np.array([100]), 5.0)


class TestFit1EModel:
    """1/E model: t = tau_0 * exp(G / Eox)."""

    def test_perfect_recovery(self):
        g_true = 50  # MV/cm
        tau_0 = 1e-15
        tox = 5.0
        voltages = np.array([5.0, 5.5, 6.0, 6.5])
        eox = voltages / tox * 10.0  # MV/cm
        etas = tau_0 * np.exp(g_true / eox)

        result = fit_1e_model(voltages, etas, tox)
        assert abs(result["g"] - g_true) < 2
        assert result["r2"] > 0.95

    def test_no_data_raises(self):
        with pytest.raises(ValueError):
            fit_1e_model(np.array([]), np.array([]), 5.0)


class TestFitVModel:
    """V-model: t = A * exp(-beta_v * Vg)."""

    def test_perfect_recovery(self):
        beta_v_true = 3.0
        a_true = 1e15
        voltages = np.array([5.0, 5.5, 6.0])
        etas = a_true * np.exp(-beta_v_true * voltages)

        result = fit_v_model(voltages, etas)
        assert abs(result["beta_v"] - beta_v_true) < 0.1
        assert result["r2"] > 0.95

    def test_no_data_raises(self):
        with pytest.raises(ValueError):
            fit_v_model(np.array([5.0]), np.array([100]))


class TestFitEArrhenius:
    """E-Arrhenius global fit: t ∝ exp(-gamma*Eox) * exp(Ea/kT)."""

    def test_perfect_recovery(self):
        gamma_true = 2.0
        ea_true = 0.6  # eV
        a_const = 1e-10
        tox = 5.0
        k = 8.617333262e-5  # eV/K

        # 3 voltages × 3 temperatures = 9 conditions
        voltages = np.array([5.0, 5.5, 6.0])
        temps_k = np.array([298, 358, 398])  # K

        etas_flat = []
        v_flat = []
        t_flat = []
        for v in voltages:
            for tk in temps_k:
                eox = v / tox * 10.0  # MV/cm
                eta = a_const * np.exp(-gamma_true * eox + ea_true / (k * tk))
                etas_flat.append(eta)
                v_flat.append(v)
                t_flat.append(tk)

        result = fit_e_arrhenius(np.array(v_flat), np.array(t_flat),
                                  np.array(etas_flat), tox)
        assert abs(result["gamma"] - gamma_true) < 0.3
        assert abs(result["ea"] - ea_true) < 0.1
        assert result["r2"] > 0.95

    def test_single_temperature_falls_back(self):
        """With only 1 temperature, should degrade to plain E-model."""
        voltages = np.array([5.0, 5.5, 6.0])
        temps = np.full_like(voltages, 298.0)
        etas = np.array([500, 200, 80])
        tox = 5.0

        result = fit_e_arrhenius(voltages, temps, etas, tox)
        assert "gamma" in result
        assert "ea" in result
        assert result["r2"] > 0.9

    def test_requires_multiple_voltages(self):
        with pytest.raises(ValueError):
            fit_e_arrhenius(np.array([5.0]), np.array([298.0]),
                            np.array([100]), 5.0)


class TestPredictLifetime:
    """Lifetime predictions from model parameters."""

    def test_e_model_lifetime(self):
        params = {"gamma": 2.0, "a": 1e20}
        lifetime = predict_lifetime("E", params, 3.3, 25, 5.0)
        assert lifetime > 0
        assert np.isfinite(lifetime)

    def test_1e_model_lifetime(self):
        params = {"g": 50, "tau_0": 1e-15}
        lifetime = predict_lifetime("1E", params, 3.3, 25, 5.0)
        assert lifetime > 0

    def test_v_model_lifetime(self):
        params = {"beta_v": 3.0, "a": 1e15}
        lifetime = predict_lifetime("V", params, 3.3, 25, 5.0)
        assert lifetime > 0

    def test_unknown_model_raises(self):
        with pytest.raises(ValueError, match="Unknown model"):
            predict_lifetime("X", {}, 3.3, 25, 5.0)


class TestPredictFailureRate:
    """Failure rate predictions from Weibull parameters."""

    def test_known_eta_beta(self):
        """F(t) = 1 - exp(-(t/eta)^beta)."""
        # At t = eta, F = 1 - 1/e ≈ 0.632
        fr = predict_failure_rate(eta=100, beta=2.0, t_operation=100)
        assert abs(fr - 0.632) < 0.01

    def test_short_time_low_failure(self):
        fr = predict_failure_rate(eta=1e6, beta=1.0, t_operation=1)
        assert 0 < fr < 0.01

    def test_long_time_high_failure(self):
        fr = predict_failure_rate(eta=100, beta=1.5, t_operation=1000)
        assert fr > 0.9

    def test_zero_eta_returns_zero(self):
        fr = predict_failure_rate(eta=0, beta=2.0, t_operation=100)
        assert fr == 0.0
