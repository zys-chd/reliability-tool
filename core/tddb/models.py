"""TDDB acceleration model fitting.

Implements E-model, 1/E model, V model, and E-Arrhenius global fitting
for lifetime extrapolation.
"""
import numpy as np

__all__ = [
    "fit_e_model",
    "fit_1e_model",
    "fit_v_model",
    "fit_sqrt_e_model",
    "fit_e_arrhenius",
    "predict_lifetime",
    "predict_failure_rate",
]

K_BOLTZMANN = 8.617333262e-5  # eV/K


def _validate_inputs(voltages, etas, min_points=2):
    """Validate input arrays."""
    v = np.asarray(voltages, dtype=float)
    e = np.asarray(etas, dtype=float)
    if len(v) < min_points or len(e) < min_points:
        raise ValueError(
            f"Need at least {min_points} data points, got {len(v)}"
        )
    mask = np.isfinite(v) & np.isfinite(e) & (e > 0)
    return v[mask], e[mask]


def fit_e_model(
    voltages: np.ndarray, etas: np.ndarray, tox: float
) -> dict:
    """Fit E-model: η = A * exp(-γ * Eox).

    Eox = V / Tox (MV/cm when V in V, Tox in nm × 10).

    Parameters
    ----------
    voltages : np.ndarray
        Stress voltages in V.
    etas : np.ndarray
        Characteristic life (η) at each voltage.
    tox : float
        Oxide thickness in nm.

    Returns
    -------
    dict with keys: gamma, a, r2
    """
    v, e = _validate_inputs(voltages, etas)
    eox = v / (tox / 10.0)  # Convert: nm → 10⁻⁷ cm → Eox in MV/cm
    # Actually: Eox = V / Tox where Tox in cm
    # Tox_nm = 5 → Tox_cm = 5e-7, Eox = V/5e-7 = V * 2e6 V/cm = V/5 MV/cm
    # Eox(MV/cm) = V / tox_nm * 10
    eox = v / tox * 10.0  # Eox in MV/cm

    ln_eta = np.log(e)
    coeffs = np.polyfit(eox, ln_eta, 1)
    gamma = -coeffs[0]  # slope = -gamma
    a = np.exp(coeffs[1])

    # R²
    fitted = np.polyval(coeffs, eox)
    ss_res = np.sum((ln_eta - fitted) ** 2)
    ss_tot = np.sum((ln_eta - np.mean(ln_eta)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    return {"gamma": float(gamma), "a": float(a), "r2": float(r2)}


def fit_1e_model(
    voltages: np.ndarray, etas: np.ndarray, tox: float
) -> dict:
    """Fit 1/E model: η = τ₀ * exp(G / Eox).

    Parameters
    ----------
    voltages : np.ndarray
        Stress voltages in V.
    etas : np.ndarray
        Characteristic life at each voltage.
    tox : float
        Oxide thickness in nm.

    Returns
    -------
    dict with keys: g, tau_0, r2
    """
    v, e = _validate_inputs(voltages, etas)
    eox = v / tox * 10.0  # MV/cm

    ln_eta = np.log(e)
    inv_eox = 1.0 / eox
    coeffs = np.polyfit(inv_eox, ln_eta, 1)
    g = coeffs[0]
    tau_0 = np.exp(coeffs[1])

    fitted = np.polyval(coeffs, inv_eox)
    ss_res = np.sum((ln_eta - fitted) ** 2)
    ss_tot = np.sum((ln_eta - np.mean(ln_eta)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    return {"g": float(g), "tau_0": float(tau_0), "r2": float(r2)}


def fit_v_model(voltages: np.ndarray, etas: np.ndarray) -> dict:
    """Fit V-model: η = A * exp(-βv * V).

    Parameters
    ----------
    voltages : np.ndarray
        Stress voltages in V.
    etas : np.ndarray
        Characteristic life at each voltage.

    Returns
    -------
    dict with keys: beta_v, a, r2
    """
    v, e = _validate_inputs(voltages, etas)

    ln_eta = np.log(e)
    coeffs = np.polyfit(v, ln_eta, 1)
    beta_v = -coeffs[0]
    a = np.exp(coeffs[1])

    fitted = np.polyval(coeffs, v)
    ss_res = np.sum((ln_eta - fitted) ** 2)
    ss_tot = np.sum((ln_eta - np.mean(ln_eta)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    return {"beta_v": float(beta_v), "a": float(a), "r2": float(r2)}


def fit_sqrt_e_model(
    voltages: np.ndarray, etas: np.ndarray, tox: float
) -> dict:
    """Fit √E model (E^{1/2}): η = A * exp(-S * sqrt(Eox)).

    Eox = V / Tox * 10 (MV/cm).
    sqrt(Eox) in sqrt(MV/cm).

    Parameters
    ----------
    voltages : np.ndarray
        Stress voltages in V.
    etas : np.ndarray
        Characteristic life at each voltage.
    tox : float
        Oxide thickness in nm.

    Returns
    -------
    dict with keys: s (sqrt-E factor), a, r2
    """
    v, e = _validate_inputs(voltages, etas)
    eox = v / tox * 10.0  # MV/cm
    sqrt_eox = np.sqrt(eox)

    ln_eta = np.log(e)
    coeffs = np.polyfit(sqrt_eox, ln_eta, 1)
    s = -coeffs[0]  # slope = -S
    a = np.exp(coeffs[1])

    fitted = np.polyval(coeffs, sqrt_eox)
    ss_res = np.sum((ln_eta - fitted) ** 2)
    ss_tot = np.sum((ln_eta - np.mean(ln_eta)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    return {"s": float(s), "a": float(a), "r2": float(r2)}


def fit_e_arrhenius(
    voltages: np.ndarray,
    temperatures: np.ndarray,
    etas: np.ndarray,
    tox: float,
) -> dict:
    """Fit E-Arrhenius model: η = A * exp(-γ·Eox + Ea/kT).

    Global fit across voltage AND temperature variations.

    Parameters
    ----------
    voltages : np.ndarray
        Stress voltages in V (one per data point).
    temperatures : np.ndarray
        Temperatures in °C or K (>100 treated as K).
    etas : np.ndarray
        Characteristic life at each condition.
    tox : float
        Oxide thickness in nm.

    Returns
    -------
    dict with keys: gamma, ea, a, r2
    """
    v = np.asarray(voltages, dtype=float)
    t = np.asarray(temperatures, dtype=float)
    e = np.asarray(etas, dtype=float)

    mask = np.isfinite(v) & np.isfinite(t) & np.isfinite(e) & (e > 0)
    v, t, e = v[mask], t[mask], e[mask]

    if len(v) < 3:
        raise ValueError(f"Need at least 3 data points for 2-param fit, got {len(v)}")

    # Convert °C to K if needed
    t_k = np.where(t < 100, t + 273.15, t)

    eox = v / tox * 10.0  # MV/cm
    ln_eta = np.log(e)
    inv_t = 1.0 / (K_BOLTZMANN * t_k)  # 1/(kT)

    # Multi-linear regression: ln(η) = ln(A) - γ·Eox + Ea/(kT)
    # y = a0 + a1*x1 + a2*x2
    # where y = ln(η), x1 = Eox, x2 = 1/(kT)
    # a1 = -γ, a2 = Ea, a0 = ln(A)
    A_mat = np.column_stack([np.ones_like(eox), eox, inv_t])
    coeffs, residuals, _, _ = np.linalg.lstsq(A_mat, ln_eta, rcond=None)

    ln_a, gamma, ea = coeffs[0], -coeffs[1], coeffs[2]
    a = np.exp(ln_a)

    # R²
    fitted = A_mat @ coeffs
    ss_res = np.sum((ln_eta - fitted) ** 2)
    ss_tot = np.sum((ln_eta - np.mean(ln_eta)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    return {
        "gamma": float(gamma),
        "ea": float(ea),
        "a": float(a),
        "r2": float(r2),
    }


def predict_lifetime(
    model: str,
    params: dict,
    v_op: float,
    t_op: float,
    tox: float,
) -> float:
    """Predict characteristic lifetime (η) at operating conditions.

    Parameters
    ----------
    model : str
        One of "E", "1E", "V".
    params : dict
        Fitted model parameters.
    v_op : float
        Operating voltage in V.
    t_op : float
        Operating temperature in °C.
    tox : float
        Oxide thickness in nm.

    Returns
    -------
    float
        Predicted η (characteristic life) in seconds.
    """
    if model == "E":
        eox = v_op / tox * 10.0
        return params["a"] * np.exp(-params["gamma"] * eox)
    elif model == "1E":
        eox = v_op / tox * 10.0
        return params["tau_0"] * np.exp(params["g"] / eox)
    elif model == "V":
        return params["a"] * np.exp(-params["beta_v"] * v_op)
    elif model == "SQE":
        eox = v_op / tox * 10.0
        return params["a"] * np.exp(-params["s"] * np.sqrt(eox))
    else:
        raise ValueError(f"Unknown model: {model}")


def predict_failure_rate(
    eta: float,
    beta: float,
    t_operation: float,
) -> float:
    """Compute cumulative failure rate at a given operation time.

    F(t) = 1 - exp(-(t/η)^β)

    Parameters
    ----------
    eta : float
        Characteristic life.
    beta : float
        Weibull slope.
    t_operation : float
        Operation time (same units as eta).

    Returns
    -------
    float
        Cumulative failure probability (0-1).
    """
    if eta <= 0 or beta <= 0:
        return 0.0
    return 1.0 - np.exp(-((t_operation / eta) ** beta))
