"""Tests for Weibull fitting core."""
import numpy as np
import pandas as pd
import pytest

from core.tddb.weibull_fitter import (
    benard_median_rank,
    fit_weibull,
    fit_unified_slope,
    weibull_plot_data,
)


class TestBenardMedianRank:
    """Benard's approximation for median rank (cumulative probability)."""

    def test_simple_sequence(self):
        ranks = benard_median_rank(5)
        assert len(ranks) == 5
        assert 0 < ranks[0] < ranks[-1] < 1
        # First rank should be approximately (1-0.3)/(5+0.4) ≈ 0.13
        assert abs(ranks[0] - (1 - 0.3) / (5 + 0.4)) < 1e-10

    def test_n_equals_1(self):
        ranks = benard_median_rank(1)
        assert len(ranks) == 1
        assert abs(ranks[0] - (1 - 0.3) / (1 + 0.4)) < 1e-10

    def test_ascending_order(self):
        """Ranks should be strictly increasing."""
        for n in [2, 3, 10, 100]:
            ranks = benard_median_rank(n)
            assert all(ranks[i] < ranks[i + 1] for i in range(n - 1))


class TestFitWeibull:
    """Weibull fitting with perfect and imperfect data."""

    def test_perfect_weibull_data(self):
        """Fit to data generated from a known Weibull distribution."""
        rng = np.random.default_rng(42)
        beta_true, eta_true = 2.0, 100.0
        u = rng.random(100)
        data = eta_true * (-np.log(1 - u)) ** (1.0 / beta_true)
        result = fit_weibull(data)
        assert "beta" in result and "eta" in result
        assert "r2_raw" in result and "r2_log" in result
        # With 100 samples, estimates should be close
        assert abs(result["beta"] - beta_true) < 0.3
        assert abs(result["eta"] - eta_true) < 15

    def test_returns_r_squared(self):
        data = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        result = fit_weibull(data)
        assert 0 <= result["r2_raw"] <= 1
        assert 0 <= result["r2_log"] <= 1

    def test_high_beta_steeper_slope(self):
        """Higher beta → steeper weibull → less spread."""
        low_beta = fit_weibull(np.array([10, 30, 50, 80, 150]))
        high_beta = fit_weibull(np.array([80, 90, 100, 110, 120]))
        assert high_beta["beta"] > low_beta["beta"]

    def test_eta_approximates_63p2_percentile(self):
        """η should be close to the 63.2% percentile for Weibull data."""
        rng = np.random.default_rng(123)
        data = 200.0 * (-np.log(1 - rng.random(500))) ** (1 / 1.5)
        result = fit_weibull(data)
        # η should be near the value where F(t) ≈ 0.632
        # For large samples, this should be close to the true eta
        assert abs(result["eta"] - 200.0) < 40

    def test_few_samples(self):
        """Should still work with minimal samples (n=3)."""
        data = np.array([5.0, 10.0, 20.0])
        result = fit_weibull(data)
        assert result["beta"] > 0
        assert result["eta"] > 0

    def test_all_identical_values(self):
        """Identical values are degenerate — beta should be very large."""
        data = np.full(10, 50.0)
        result = fit_weibull(data)
        assert np.isfinite(result["beta"])
        assert np.isfinite(result["eta"])

    def test_contains_beta_and_eta(self):
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = fit_weibull(data)
        for key in ("beta", "eta", "r2_raw", "r2_log", "n"):
            assert key in result


class TestFitUnifiedSlope:
    """Unified (common) slope fitting across multiple conditions."""

    def test_unified_beta_between_individual_betas(self):
        """The unified beta should be between the individual betas."""
        rng = np.random.default_rng(42)
        groups = {
            "cond1": 80.0 * (-np.log(1 - rng.random(20))) ** (1 / 1.8),
            "cond2": 40.0 * (-np.log(1 - rng.random(20))) ** (1 / 2.2),
            "cond3": 20.0 * (-np.log(1 - rng.random(20))) ** (1 / 1.5),
        }
        individual_betas = [fit_weibull(g)["beta"] for g in groups.values()]
        result = fit_unified_slope(groups)
        assert "beta" in result
        assert "etas" in result
        min_beta, max_beta = min(individual_betas), max(individual_betas)
        assert min_beta <= result["beta"] <= max_beta

    def test_returns_eta_per_group(self):
        groups = {
            "cond1": np.array([5, 10, 15, 20, 25]),
            "cond2": np.array([3, 6, 9, 12, 15]),
        }
        result = fit_unified_slope(groups)
        assert len(result["etas"]) == 2
        assert list(result["etas"].keys()) == ["cond1", "cond2"]

    def test_unified_r2_good_for_similar_betas(self):
        """When true betas are nearly identical, unified fit should have good R²."""
        rng = np.random.default_rng(42)
        groups = {
            "a": 100.0 * (-np.log(1 - rng.random(30))) ** (1 / 2.0),
            "b": 50.0 * (-np.log(1 - rng.random(30))) ** (1 / 2.0),
        }
        result = fit_unified_slope(groups)
        assert result["r2_overall"] > 0.8


class TestWeibullPlotData:
    """Weibull plot coordinate calculations."""

    def test_weibull_transform_increases_with_t(self):
        """ln(-ln(1-F)) should increase with ln(TBD)."""
        data = np.array([10, 20, 30, 40, 50])
        plot_data = weibull_plot_data(data)
        assert "ln_t" in plot_data
        assert "weibull_prob" in plot_data
        # Both should be strictly increasing
        assert all(plot_data["ln_t"][i] < plot_data["ln_t"][i + 1]
                   for i in range(len(data) - 1))
        assert all(plot_data["weibull_prob"][i] < plot_data["weibull_prob"][i + 1]
                   for i in range(len(data) - 1))

    def test_linear_in_weibull_space(self):
        """Perfect Weibull data should be approximately linear in Weibull space."""
        rng = np.random.default_rng(42)
        data = 100.0 * (-np.log(1 - rng.random(50))) ** (1 / 2.0)
        plot_data = weibull_plot_data(data)
        ln_t = plot_data["ln_t"]
        wp = plot_data["weibull_prob"]
        # Fit line and check R²
        coeffs = np.polyfit(ln_t, wp, 1)
        fitted = np.polyval(coeffs, ln_t)
        residuals = wp - fitted
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((wp - np.mean(wp)) ** 2)
        r2 = 1 - ss_res / ss_tot
        assert r2 > 0.95
