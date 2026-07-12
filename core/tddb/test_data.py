"""TDDB test data generators.

Produces realistic synthetic TDDB datasets for unit testing.
TBD values follow a Weibull distribution. Voltage acceleration
uses the E-model to scale eta with voltage.
"""
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from ..webengine_check import is_webengine_available

__all__ = [
    "generate_weibull_sample",
    "make_tddb_dataset",
    "make_tddb_excel",
    "TDDB_DEFAULT_COLUMNS",
]

TDDB_DEFAULT_COLUMNS = [
    "PART_ID", "Vgs", "Temperature", "Gate Oxide Area",
    "TBD", "QBD", "ignore", "group", "老化板通道", "comment",
]

# E-model acceleration parameters (for data generation)
# t = A * exp(-gamma * Eox), so eta scales as exp(gamma * (Eox_ref - Eox))
# gamma ≈ 1-3 cm/MV for typical SiO2
E_MODEL_GAMMA = 2.0  # cm/MV


def generate_weibull_sample(
    beta: float, eta: float, n: int, seed: int | None = None
) -> np.ndarray:
    """Generate `n` Weibull-distributed random samples.

    Parameters
    ----------
    beta : float
        Weibull shape parameter (slope).
    eta : float
        Weibull scale parameter (characteristic life, 63.2% percentile).
    n : int
        Number of samples.
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    np.ndarray
        Length `n` array of positive TBD values.
    """
    rng = np.random.default_rng(seed)
    # Weibull: F(t) = 1 - exp(-(t/eta)^beta)
    # Inverse CDF: t = eta * (-ln(1-U))^(1/beta)
    u = rng.random(n)
    return eta * (-np.log(1 - u)) ** (1.0 / beta)


def _eta_at_voltage(
    v: float,
    v_ref: float,
    eta_ref: float,
    tox: float = 5.0,
) -> float:
    """Scale eta from reference voltage to target voltage using E-model.

    Eox = V / Tox (MV/cm)
    eta ∝ exp(-gamma * Eox)
    So eta(v) = eta_ref * exp(gamma * (Eox_ref - Eox))
    """
    eox_v = v / tox
    eox_ref = v_ref / tox
    return eta_ref * np.exp(E_MODEL_GAMMA * (eox_ref - eox_v))


def make_tddb_dataset(
    voltages: list[float],
    beta: float = 2.0,
    eta_at_vmin: float = 500.0,
    n_per_cond: int = 20,
    groups: list[str] | None = None,
    temperatures: list[float] | None = None,
    areas: list[float] | None = None,
    seed: int | None = None,
    ignore_prob: float = 0.0,
    cumulative_current: float | None = None,
    tox: float = 5.0,
) -> pd.DataFrame:
    """Create a realistic TDDB test dataset as a DataFrame.

    Each unique combination of (Vgs, Temperature, Gate Oxide Area, group)
    generates `n_per_cond` samples with Weibull-distributed TBD values.

    Parameters
    ----------
    voltages : list[float]
        Stress voltages in Volts.
    beta : float, default=2.0
        Weibull shape parameter.
    eta_at_vmin : float, default=500
        Characteristic life (η) at the lowest voltage.
    n_per_cond : int, default=20
        Sample count per unique condition.
    groups : list[str], optional
        Group labels (e.g. ["湿氧", "干氧"]). Default: ["A"].
    temperatures : list[float], optional
        Temperatures in °C. Default: [25].
    areas : list[float], optional
        Gate oxide areas in µm². Default: [1.0].
    seed : int, optional
        Random seed.
    ignore_prob : float, default=0.0
        Probability of marking a row as ignore.
    cumulative_current : float, optional
        If provided, QBD = TBD * cumulative_current (Coulombs).
    tox : float, default=5.0
        Oxide thickness in nm.

    Returns
    -------
    pd.DataFrame
        Columns matching the TDDB template.
    """
    if groups is None:
        groups = ["A"]
    if temperatures is None:
        temperatures = [25.0]
    if areas is None:
        areas = [1.0]

    rng = np.random.default_rng(seed)
    v_min = min(voltages)

    rows: list[dict] = []
    part_counter = 0

    for group in groups:
        for temp in temperatures:
            for area in areas:
                for v in voltages:
                    eta_v = _eta_at_voltage(v, v_min, eta_at_vmin, tox)
                    tbds = generate_weibull_sample(beta, eta_v, n_per_cond, rng.integers(0, 2**31))
                    for tbd in tbds:
                        part_counter += 1
                        qbd = tbd * cumulative_current if cumulative_current else np.nan
                        ignore = 1 if rng.random() < ignore_prob else 0
                        rows.append({
                            "PART_ID": f"DUT_{part_counter:04d}",
                            "Vgs": v,
                            "Temperature": temp,
                            "Gate Oxide Area": area,
                            "TBD": round(tbd, 4),
                            "QBD": round(qbd, 6) if not np.isnan(qbd) else "",
                            "ignore": ignore,
                            "group": group,
                            "老化板通道": f"CH{(part_counter % 48) + 1:02d}",
                            "comment": "",
                        })

    df = pd.DataFrame(rows, columns=TDDB_DEFAULT_COLUMNS)
    return df


def make_tddb_excel(
    df: pd.DataFrame | None = None,
    path: str | Path | None = None,
    sheet_name: str = "Sheet1",
    **kwargs,
) -> Path:
    """Write a TDDB dataset to Excel file.

    Parameters
    ----------
    df : pd.DataFrame, optional
        Dataset to write. If None, generates one using **kwargs.
    path : str | Path, optional
        Output path. If None, uses current dir / "tddb_test_data.xlsx".
    sheet_name : str, default="Sheet1"
    **kwargs
        Passed to make_tddb_dataset if df is None.

    Returns
    -------
    Path
        Path to the written Excel file.
    """
    if df is None:
        df = make_tddb_dataset(**kwargs)

    if path is None:
        path = Path.cwd() / "tddb_test_data.xlsx"
    path = Path(path)

    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name

    # Header
    ws.append(list(df.columns))

    # Data
    for _, row in df.iterrows():
        ws.append([v if not (isinstance(v, float) and np.isnan(v)) else "" for v in row])

    wb.save(path)
    wb.close()
    return path
