"""Weibull distribution fitting for TDDB analysis.

Provides Weibull fitting (independent and unified slope),
median rank calculation, and Weibull plot data preparation.
Uses only numpy/scipy — no PySide6 dependency.
"""
import numpy as np
from scipy import optimize as sp_optimize

__all__ = [
    "benard_median_rank",
    "fit_weibull",
    "fit_unified_slope",
    "weibull_plot_data",
]


def benard_median_rank(n: int) -> np.ndarray:
    """Compute Benard's approximation for median rank positions.

    F_i ≈ (i - 0.3) / (n + 0.4)

    Parameters
    ----------
    n : int
        Number of samples.

    Returns
    -------
    np.ndarray
        Array of length n with median rank (cumulative probability) values.
    """
    i = np.arange(1, n + 1)
    return (i - 0.3) / (n + 0.4)


def _least_squares_weibull(
    data: np.ndarray,
) -> tuple[float, float, float, float]:
    """Fit Weibull using least squares on ln(-ln(1-F)) vs ln(t).

    Returns (beta, eta, r2_raw, r2_log).
    """
    n = len(data)
    sorted_data = np.sort(data)
    ranks = benard_median_rank(n)

    # Weibull transform
    ln_t = np.log(sorted_data)
    weibull_prob = np.log(-np.log(1 - ranks))

    # Linear fit: weibull_prob = beta * ln_t - beta * ln(eta)
    # y = a + b*x  where b = beta, a = -beta * ln(eta)
    coeffs = np.polyfit(ln_t, weibull_prob, 1)
    beta = coeffs[0]
    a = coeffs[1]
    eta = np.exp(-a / beta) if beta != 0 else np.inf

    # R² in Weibull space (log)
    fitted = np.polyval(coeffs, ln_t)
    residuals = weibull_prob - fitted
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((weibull_prob - np.mean(weibull_prob)) ** 2)
    r2_log = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    # R² in raw (TBD) space — compare empirical CDF vs fitted CDF
    empirical_f = ranks
    fitted_f = 1 - np.exp(-(sorted_data / eta) ** beta)
    res_raw = empirical_f - fitted_f
    ss_res_raw = np.sum(res_raw ** 2)
    ss_tot_raw = np.sum((empirical_f - np.mean(empirical_f)) ** 2)
    r2_raw = 1 - ss_res_raw / ss_tot_raw if ss_tot_raw > 0 else 0.0

    return float(beta), float(eta), float(r2_raw), float(r2_log)


def fit_weibull(data: np.ndarray) -> dict:
    """Fit a Weibull distribution to the given data.

    Parameters
    ----------
    data : np.ndarray
        1D array of TBD values (positive).

    Returns
    -------
    dict with keys: beta, eta, r2_raw, r2_log, n
    """
    data = np.asarray(data, dtype=float)
    data = data[np.isfinite(data)]
    if len(data) < 2:
        return {"beta": 0.0, "eta": 0.0, "r2_raw": 0.0, "r2_log": 0.0, "n": len(data)}

    beta, eta, r2_raw, r2_log = _least_squares_weibull(data)

    return {
        "beta": beta,
        "eta": eta,
        "r2_raw": r2_raw,
        "r2_log": r2_log,
        "n": len(data),
    }


def fit_unified_slope(groups: dict[str, np.ndarray]) -> dict:
    """Fit a common Weibull slope (β) across multiple groups/conditions.

    All groups share one β, but each has its own η.

    Parameters
    ----------
    groups : dict[str, np.ndarray]
        Mapping of group name to its data array.

    Returns
    -------
    dict with keys:
        beta : float — common slope
        etas : dict[str, float] — eta per group
        r2_overall : float — overall R² across all groups
    """
    # For each group, fit independently to get initial B-estimates
    group_names = list(groups.keys())
    initial_fits = {name: fit_weibull(groups[name]) for name in group_names}

    # Use the median of individual betas as starting point
    initial_beta = np.median([f["beta"] for f in initial_fits.values()])

    # Objective: minimize sum of squared residuals across all groups
    # with a shared beta
    def objective(beta):
        total_ss = 0.0
        for name in group_names:
            data = groups[name]
            sorted_data = np.sort(data)
            n = len(data)
            ranks = benard_median_rank(n)
            ln_t = np.log(sorted_data)
            weibull_prob = np.log(-np.log(1 - ranks))

            # Optimal η for this group given the shared β
            # eta = exp(mean(ln_t - weibull_prob/beta))
            eta_opt = np.exp(np.mean(ln_t - weibull_prob / beta))
            fitted = beta * (ln_t - np.log(eta_opt))
            total_ss += np.sum((weibull_prob - fitted) ** 2)
        return total_ss

    # Optimize beta
    result = sp_optimize.minimize_scalar(objective, bounds=(0.1, 20.0), method="bounded")
    beta_unified = result.x

    # Compute eta for each group with unified beta
    etas = {}
    total_ss = 0.0
    total_ss_tot = 0.0

    for name in group_names:
        data = groups[name]
        sorted_data = np.sort(data)
        n = len(data)
        ranks = benard_median_rank(n)
        ln_t = np.log(sorted_data)
        weibull_prob = np.log(-np.log(1 - ranks))

        eta_opt = np.exp(np.mean(ln_t - weibull_prob / beta_unified))
        etas[name] = float(eta_opt)

        # For overall R²
        fitted_p = beta_unified * (ln_t - np.log(eta_opt))
        total_ss += np.sum((weibull_prob - fitted_p) ** 2)
        total_ss_tot += np.sum((weibull_prob - np.mean(weibull_prob)) ** 2)

    r2_overall = 1 - total_ss / total_ss_tot if total_ss_tot > 0 else 0.0

    return {
        "beta": float(beta_unified),
        "etas": etas,
        "r2_overall": float(r2_overall),
    }


def weibull_plot_data(data: np.ndarray) -> dict:
    """Prepare Weibull plot coordinates.

    Returns sorted data with Weibull probability transforms.

    Parameters
    ----------
    data : np.ndarray
        1D array of TBD values.

    Returns
    -------
    dict with keys:
        tbd : sorted TBD values
        ln_t : ln(TBD)
        ranks : median rank probabilities
        weibull_prob : ln(-ln(1-F))
    """
    data = np.asarray(data, dtype=float)
    data = data[np.isfinite(data)]
    n = len(data)

    sorted_data = np.sort(data)
    ranks = benard_median_rank(n)
    ln_t = np.log(sorted_data)
    weibull_prob = np.log(-np.log(1 - ranks))

    return {
        "tbd": sorted_data,
        "ln_t": ln_t,
        "ranks": ranks,
        "weibull_prob": weibull_prob,
    }
