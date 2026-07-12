"""Poisson area scaling for TDDB."""
import numpy as np

__all__ = ["scale_eta"]


def scale_eta(
    eta_ref: float,
    area_ref: float,
    area_target: float,
    beta: float,
) -> float:
    """Scale characteristic life (η) from reference area to target area.

    Uses the Poisson defect model: η₂ = η₁ * (A₁/A₂)^(1/β)

    Parameters
    ----------
    eta_ref : float
        Characteristic life at reference area.
    area_ref : float
        Reference gate oxide area.
    area_target : float
        Target gate oxide area.
    beta : float
        Weibull shape parameter.

    Returns
    -------
    float
        η at target area (infinity if beta=0).
    """
    if beta <= 0:
        return np.inf
    return eta_ref * (area_ref / area_target) ** (1.0 / beta)
