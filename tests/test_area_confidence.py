"""Tests for area scaling and confidence interval calculations."""
import numpy as np
import pytest

from core.tddb.area_scaling import scale_eta
from core.tddb.confidence import (
    weibull_ci_beta,
    weibull_ci_eta,
    lifetime_ci,
)


class TestScaleEta:
    """Poisson area scaling: η₂ = η₁ * (A₁/A₂)^(1/β)."""

    def test_same_area_no_change(self):
        eta = scale_eta(eta_ref=100, area_ref=1.0, area_target=1.0, beta=2.0)
        assert eta == pytest.approx(100.0)

    def test_larger_area_shorter_life(self):
        """Larger area → more defects → shorter characteristic life."""
        eta = scale_eta(eta_ref=100, area_ref=1.0, area_target=4.0, beta=2.0)
        # η₂ = 100 * (1/4)^(1/2) = 100 * 0.5 = 50
        assert eta == pytest.approx(50.0)

    def test_smaller_area_longer_life(self):
        eta = scale_eta(eta_ref=100, area_ref=4.0, area_target=1.0, beta=2.0)
        # η₂ = 100 * (4/1)^(1/2) = 100 * 2 = 200
        assert eta == pytest.approx(200.0)

    def test_higher_beta_reduces_effect(self):
        """Higher β → tighter distribution → area scaling effect is smaller."""
        eta_low_beta = scale_eta(100, 1, 4, beta=1.0)   # 100 * 0.25 = 25
        eta_high_beta = scale_eta(100, 1, 4, beta=4.0)  # 100 * 0.5^0.25 ≈ 84
        assert eta_high_beta > eta_low_beta

    def test_area_ratio_less_than_one(self):
        """Area ratio < 1 should make eta larger."""
        eta = scale_eta(eta_ref=100, area_ref=4.0, area_target=1.0, beta=2.0)
        assert eta > 100

    def test_zero_beta_returns_inf(self):
        """β=0 → degenerate, area scaling undefined."""
        eta = scale_eta(100, 1, 4, beta=0)
        assert np.isinf(eta)


class TestWeibullCI:
    """Confidence intervals for Weibull parameters."""

    def test_ci_beta_contains_true(self):
        """The true β should be within the CI for large samples."""
        rng = np.random.default_rng(42)
        beta_true, eta_true = 2.0, 100.0
        data = eta_true * (-np.log(1 - rng.random(200))) ** (1 / beta_true)
        from core.tddb.weibull_fitter import fit_weibull
        result = fit_weibull(data)
        beta_est = result["beta"]
        lo, hi = weibull_ci_beta(beta_est, result["n"], alpha=0.05)
        assert lo < beta_true < hi, f"{lo} < {beta_true} < {hi}"

    def test_ci_eta_contains_true(self):
        rng = np.random.default_rng(42)
        beta_true, eta_true = 2.0, 100.0
        data = eta_true * (-np.log(1 - rng.random(200))) ** (1 / beta_true)
        from core.tddb.weibull_fitter import fit_weibull
        result = fit_weibull(data)
        eta_est = result["eta"]
        lo, hi = weibull_ci_eta(eta_est, result["n"], alpha=0.05)
        assert lo < eta_true < hi

    def test_wider_ci_for_smaller_sample(self):
        """Smaller samples should have wider confidence intervals."""
        result_small = {"beta": 2.0, "n": 5}
        result_large = {"beta": 2.0, "n": 50}
        lo_s, hi_s = weibull_ci_beta(2.0, 5, alpha=0.05)
        lo_l, hi_l = weibull_ci_beta(2.0, 50, alpha=0.05)
        assert (hi_s - lo_s) > (hi_l - lo_l)

    def test_ci_beta_symmetry(self):
        """CI for beta should widen symmetrically on log scale."""
        lo, hi = weibull_ci_beta(2.0, 20, alpha=0.05)
        assert lo < 2.0 < hi

    def test_ci_eta_symmetry(self):
        lo, hi = weibull_ci_eta(100.0, 20, alpha=0.05)
        assert lo < 100.0 < hi


class TestLifetimeCI:
    """Confidence intervals for lifetime at a given failure fraction."""

    def test_ci_at_632_percent(self):
        """At t=η, failure fraction should be ~63.2%, CI should bracket it."""
        lo, hi = lifetime_ci(eta=100, beta=2.0, failure_fraction=0.632,
                              n=20, alpha=0.05)
        assert lo < 100 < hi

    def test_ci_at_01_percent(self):
        """At very low failure fractions, CI should still contain the expected value."""
        lo, hi = lifetime_ci(eta=100, beta=2.0, failure_fraction=0.001,
                              n=30, alpha=0.05)
        # Expected t for F=0.001: t = η * (-ln(1-0.001))^(1/β)
        expected = 100 * (-np.log(0.999)) ** 0.5
        assert lo < expected < hi

    def test_wider_ci_for_smaller_sample(self):
        lo_s, hi_s = lifetime_ci(100, 2.0, 0.001, n=5, alpha=0.05)
        lo_l, hi_l = lifetime_ci(100, 2.0, 0.001, n=50, alpha=0.05)
        assert (hi_s - lo_s) > (hi_l - lo_l)
