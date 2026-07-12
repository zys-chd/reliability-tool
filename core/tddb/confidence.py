"""Confidence interval calculations for Weibull analysis.

Uses Fisher matrix approximation for parameter confidence bounds.
Based on Nelson's method for Weibull confidence intervals.
"""
import numpy as np
from scipy import stats as sp_stats

__all__ = [
    "weibull_ci_beta",
    "weibull_ci_eta",
    "lifetime_ci",
]


def _z_alpha(alpha: float) -> float:
    """Normal quantile for given alpha (two-tailed)."""
    return sp_stats.norm.ppf(1 - alpha / 2)


def weibull_ci_beta(
    beta_est: float,
    n: int,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """Confidence interval for Weibull shape parameter β.

    Uses the approximation: β follows lognormal distribution
    with variance ≈ 0.608 / (n * β²).

    Parameters
    ----------
    beta_est : float
        Estimated β.
    n : int
        Sample size.
    alpha : float, default=0.05
        Significance level (95% CI when alpha=0.05).

    Returns
    -------
    (lower, upper) tuple of CI bounds.
    """
    if n < 2:
        return (0.0, np.inf)

    z = _z_alpha(alpha)
    # Standard error of ln(β)
    se_ln_beta = 0.78 / np.sqrt(n - 1)  # Approximation from Nelson

    lo = beta_est * np.exp(-z * se_ln_beta)
    hi = beta_est * np.exp(z * se_ln_beta)
    return (float(lo), float(hi))


def weibull_ci_eta(
    eta_est: float,
    n: int,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """Confidence interval for Weibull scale parameter η.

    Parameters
    ----------
    eta_est : float
        Estimated η.
    n : int
        Sample size.
    alpha : float, default=0.05
        Significance level.

    Returns
    -------
    (lower, upper) tuple of CI bounds.
    """
    if n < 2:
        return (0.0, np.inf)

    z = _z_alpha(alpha)
    # Standard error for ln(η)
    se_ln_eta = 1.05 / (np.sqrt(n) * 1.0)  # Approximation

    lo = eta_est * np.exp(-z * se_ln_eta)
    hi = eta_est * np.exp(z * se_ln_eta)
    return (float(lo), float(hi))


def lifetime_ci(
    eta: float,
    beta: float,
    failure_fraction: float,
    n: int,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """Confidence interval for lifetime at a given failure fraction.

    The lifetime t_p for failure fraction p is:
        t_p = η * (-ln(1-p))^(1/β)

    CI uses delta method to combine uncertainty in η and β.

    Parameters
    ----------
    eta : float
        Characteristic life.
    beta : float
        Weibull slope.
    failure_fraction : float
        Target failure fraction (0-1).
    n : int
        Sample size.
    alpha : float, default=0.05
        Significance level.

    Returns
    -------
    (lower, upper) tuple of CI bounds in time units.
    """
    if n < 2 or failure_fraction <= 0 or failure_fraction >= 1:
        return (0.0, np.inf)

    z = _z_alpha(alpha)
    t_p = eta * (-np.log(1 - failure_fraction)) ** (1.0 / beta)

    if t_p <= 0:
        return (0.0, np.inf)

    # Approximate variance of ln(t_p) via delta method
    var_ln_eta = (1.05 / np.sqrt(n)) ** 2
    var_ln_beta = (0.78 / np.sqrt(n - 1)) ** 2

    # Sensitivity: ∂ln(t_p)/∂ln(η) = 1
    # ∂ln(t_p)/∂β = -ln(-ln(1-p))/β² (approximate)
    ln_y = np.log(-np.log(1 - failure_fraction))
    sensitivity_beta = -ln_y / (beta ** 2) if beta > 0 else 0

    var_ln_tp = var_ln_eta + (sensitivity_beta ** 2) * var_ln_beta * (beta ** 2)
    se_ln_tp = np.sqrt(max(var_ln_tp, 1e-15))

    lo = t_p * np.exp(-z * se_ln_tp)
    hi = t_p * np.exp(z * se_ln_tp)

    return (float(lo), float(hi))
