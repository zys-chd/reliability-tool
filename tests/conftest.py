"""Shared fixtures for all core module tests."""
import os
import csv
import tempfile
from pathlib import Path
from typing import Generator

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def tmp_data_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for test data files."""
    with tempfile.TemporaryDirectory(prefix="rt_test_") as d:
        yield Path(d)


# ── CSV sample data helpers ────────────────────────────────────

def make_csv_content(rows: list[list], header_row0: bool = True) -> str:
    """Build CSV string with optional 4-row header.

    Format:
        Row 0: column headers (PART_ID, SOFT_BIN, test_cols...)
        Row 1: Unit line
        Row 2: Lower limit line
        Row 3: Higher limit line
        Row 4+: data
    """
    lines = []
    for r in rows:
        lines.append(",".join(str(v) for v in r))
    return "\n".join(lines)


def write_csv(path: Path, rows: list[list]) -> Path:
    """Write a CSV with 4-row header + data rows."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for r in rows:
            writer.writerow(r)
    return path


@pytest.fixture
def sample_csv(tmp_data_dir) -> Path:
    """Create a minimal valid CSV with 4-row header."""
    path = tmp_data_dir / "test.csv"
    rows = [
        ["PART_ID", "SOFT_BIN", "DC_IDSS_T1", "DC_VTH_T1", "DC_VF_T1"],
        ["Unit", "", "A", "V", "V"],
        ["Lower Limit", "", "0", "1.5", "0.6"],
        ["Higher Limit", "", "0.001", "5.0", "2.0"],
        ["SN001", "1", "1.23e-05", "3.45e+00", "1.01e+00"],
        ["SN002", "2", "2.34e-05", "4.56e+00", "1.11e+00"],
        ["SN003", "1", "3.45e-05", "5.67e+00", "1.21e+00"],
    ]
    return write_csv(path, rows)


@pytest.fixture
def sample_csv_no_data(tmp_data_dir) -> Path:
    """CSV with headers only, no data rows."""
    path = tmp_data_dir / "empty_data.csv"
    rows = [
        ["PART_ID", "SOFT_BIN", "DC_IDSS_T1"],
        ["Unit", "", "A"],
        ["Lower Limit", "", "0"],
        ["Higher Limit", "", "0.001"],
    ]
    return write_csv(path, rows)


@pytest.fixture
def sample_csv_bom(tmp_data_dir) -> Path:
    """CSV with UTF-8 BOM (EF BB BF)."""
    path = tmp_data_dir / "bom.csv"
    rows = [
        ["PART_ID", "SOFT_BIN", "DC_IDSS_T1"],
        ["Unit", "", "A"],
        ["Lower Limit", "", "0"],
        ["Higher Limit", "", "0.001"],
        ["SN001", "1", "1.23e-05"],
        ["SN002", "2", "2.34e-05"],
    ]
    content = "\ufeff" + "\n".join(",".join(str(v) for v in r) for r in rows) + "\n"
    path.write_text(content, encoding="utf-8-sig")
    return path


# ── Compare / Shift test fixtures ──────────────────────────────

@pytest.fixture
def calc_config() -> dict:
    """A realistic calc_config with renames, suffixes, formulas, limits."""
    return {
        "renames": {
            "DC_IDSS_T1": "IDSS",
            "DC_IDSS_Delta_T1": "IDSS",
            "DC_VTH_T1": "VTH",
            "DC_VF_T1": "VF",
        },
        "suffixes": {
            "DC_IDSS_T1": "T1",
            "DC_IDSS_Delta_T1": "Delta",
            "DC_VTH_T1": "",
            "DC_VF_T1": "",
        },
        "formulas": {
            "DC_IDSS_T1": "abs((TX - T0)/T0)",
            "DC_VTH_T1": "TX - T0",
            "DC_VF_T1": "abs(TX - T0)",
        },
        "limits": {
            "DC_IDSS_T1": "0.1",
            "DC_VTH_T1": "0.5",
        },
        "directions": {
            "DC_IDSS_T1": "upper",
            "DC_VTH_T1": "upper",
        },
    }


@pytest.fixture
def merged_df_for_compare() -> pd.DataFrame:
    """A DataFrame as produced by merge_t0_tx, ready for transform_rename."""
    return pd.DataFrame({
        "PART_ID": ["SN001", "SN001", "SN002", "SN002"],
        "SOFT_BIN": [1, 1, 2, 2],
        "group": ["T0", "HTRB_168H", "T0", "HTRB_168H"],
        "filepath": ["T0.csv", "TX.csv", "T0.csv", "TX.csv"],
        "DC_IDSS_T1": [1.0e-5, 1.2e-5, 2.0e-5, 2.5e-5],
        "DC_IDSS_Delta_T1": [np.nan, 0.2e-5, np.nan, 0.5e-5],
        "DC_VTH_T1": [3.0, 3.1, 3.5, 3.8],
        "DC_VF_T1": [1.0, 1.05, 1.2, 1.3],
    })


# ── Plotting test fixtures ─────────────────────────────────────

@pytest.fixture
def compare_result_xlsx(tmp_data_dir, request) -> Path:
    """Create a minimal compare result Excel file for read_compare_file tests."""
    from openpyxl import Workbook
    path = tmp_data_dir / "对比结果.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "对比结果"

    # Row 1: test item names (merged across 3 cols)
    fixed = ["PART_ID", "SOFT_BIN", "GROUP", "file"]
    row1 = fixed + ["IDSS", "", "", "VTH", "", ""]
    ws.append(row1)

    # Row 2-7: meta info
    meta_labels = ["unit", "lower limit", "higher limit", "shift limit",
                   "limit side", "shift公式"]
    for mi, label in enumerate(meta_labels):
        r = [label, "", "", ""]
        if mi == 0:
            r += ["A", "", "", "V", "", ""]
        elif mi == 1:
            r += ["0", "", "", "1.5", "", ""]
        elif mi == 2:
            r += ["0.001", "", "", "5.0", "", ""]
        elif mi == 3:
            r += ["0.1", "", "", "0.5", "", ""]
        elif mi == 4:
            r += ["upper", "", "", "upper", "", ""]
        elif mi == 5:
            r += ["abs((TX-T0)/T0)", "", "", "TX-T0", "", ""]
        ws.append(r)

    # Row 8: sub-headers
    row8 = fixed + ["T0", "TX", "shift", "T0", "TX", "shift"]
    ws.append(row8)

    # Row 9+: data
    ws.append(["SN001", "1", "HTRB_168H", "TX.csv",
               1.0e-5, 1.2e-5, 0.2, 3.0, 3.1, 0.1])
    ws.append(["SN002", "2", "HTRB_168H", "TX.csv",
               2.0e-5, 2.5e-5, 0.25, 3.5, 3.8, 0.3])

    wb.save(path)
    wb.close()
    return path


# ── ConfigManager test fixture ─────────────────────────────────

@pytest.fixture
def config_schema() -> dict:
    return {
        "string_key": {"default": "hello", "type": str},
        "int_key": {"default": 42, "type": int},
        "float_key": {"default": 3.14, "type": float},
        "bool_key": {"default": True, "type": bool},
    }


# ── Generic sample DataFrame for plotting tests ────────────────

@pytest.fixture
def sample_plot_df() -> pd.DataFrame:
    """Minimal DataFrame for build_plots / save_html tests."""
    return pd.DataFrame({
        "PART_ID": ["SN001", "SN002", "SN003"],
        "SOFT_BIN": [1, 1, 2],
        "GROUP": ["HTRB_168H", "HTRB_168H", "HTSL_500H"],
        "IDSS_T0": [1.0e-5, 2.0e-5, 3.0e-5],
        "IDSS_TX": [1.2e-5, 2.5e-5, 3.5e-5],
        "IDSS_shift": [0.2, 0.25, 0.17],
        "VTH_T0": [3.0, 3.5, 4.0],
        "VTH_TX": [3.1, 3.8, 4.2],
        "VTH_shift": [0.1, 0.3, 0.2],
    })
