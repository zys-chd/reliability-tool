"""Tests for core/plotting.py — read_compare_file, calc_cdf, calc_weibull,
extract_traces_*, build_plots, save_html."""
import os
import math

import numpy as np
import pandas as pd
import pytest

# Set offscreen mode for Qt/plotly
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from core.plotting import (
    read_compare_file,
    calc_cdf,
    calc_weibull,
    get_tx_col,
    get_t0_col,
    get_shift_col,
    _extract_one_trace,
    extract_traces_by_group,
    extract_traces_by_item,
    build_plots,
    save_html,
)


# ═══════════════════════════════════════════════════════════════
#  calc_cdf / calc_weibull
# ═══════════════════════════════════════════════════════════════

class TestCalcCDF:

    def test_typical(self):
        """CDF on normal values."""
        vals = np.array([1.0, 2.0, 3.0, 4.0])
        cdf = calc_cdf(vals)
        np.testing.assert_array_equal(cdf, [0.25, 0.5, 0.75, 1.0])

    def test_single_value(self):
        """Single value → CDF = [1.0]."""
        cdf = calc_cdf(np.array([5.0]))
        np.testing.assert_array_equal(cdf, [1.0])

    def test_identical_values(self):
        """All same values → CDF ranks still work."""
        cdf = calc_cdf(np.array([1.0, 1.0, 1.0]))
        np.testing.assert_array_equal(cdf, [1/3, 2/3, 1.0])

    def test_two_values(self):
        cdf = calc_cdf(np.array([10.0, 20.0]))
        np.testing.assert_array_equal(cdf, [0.5, 1.0])


class TestCalcWeibull:

    def test_typical(self):
        """Weibull transform on normal values."""
        vals = np.array([1.0, 2.0, 3.0, 4.0])
        weib = calc_weibull(vals)
        assert len(weib) == 4
        assert weib[0] < 0  # First median rank should be negative
        assert weib[-1] > 0  # Last should be positive

    def test_single_value(self):
        """Single value → finite result."""
        weib = calc_weibull(np.array([5.0]))
        assert np.isfinite(weib[0])

    def test_all_same(self):
        """All identical values → no crash."""
        weib = calc_weibull(np.array([1.0, 1.0, 1.0]))
        assert len(weib) == 3
        assert all(np.isfinite(w) for w in weib)

    def test_very_large_values(self):
        """Large values should not overflow."""
        vals = np.array([1e10, 2e10, 3e10])
        weib = calc_weibull(vals)
        assert all(np.isfinite(w) for w in weib)

    def test_very_small_positive_values(self):
        """Tiny positive values should not underflow."""
        vals = np.array([1e-10, 2e-10, 3e-10])
        weib = calc_weibull(vals)
        assert all(np.isfinite(w) for w in weib)


# ═══════════════════════════════════════════════════════════════
#  get_tx_col / get_t0_col / get_shift_col
# ═══════════════════════════════════════════════════════════════

class TestGetColHelpers:

    @pytest.fixture
    def df(self):
        return pd.DataFrame({
            "PART_ID": ["A"],
            "IDSS_T0": [1.0],
            "IDSS_TX": [2.0],
            "IDSS_shift": [0.5],
            "VTH_T0": [3.0],
        })

    def test_get_tx_col(self, df):
        assert get_tx_col("IDSS", df) == "IDSS_TX"
        assert get_tx_col("VTH", df) is None

    def test_get_t0_col(self, df):
        assert get_t0_col("IDSS", df) == "IDSS_T0"
        assert get_t0_col("VTH", df) == "VTH_T0"

    def test_get_shift_col(self, df):
        assert get_shift_col("IDSS", df) == "IDSS_shift"
        assert get_shift_col("VTH", df) is None


# ═══════════════════════════════════════════════════════════════
#  _extract_one_trace
# ═══════════════════════════════════════════════════════════════

class TestExtractOneTrace:

    def test_cdf_mode(self):
        vals = np.array([3.0, 1.0, 2.0])
        pids = np.array(["C", "A", "B"])
        trace = _extract_one_trace(vals, pids, "cdf", "group1_T0", "T0")
        assert trace["name"] == "group1_T0"
        assert trace["_suffix"] == "T0"
        assert trace["x"] == [1.0, 2.0, 3.0]  # sorted
        assert trace["part_ids"] == ["A", "B", "C"]  # sorted by val
        assert trace["n"] == 3
        assert len(trace["y"]) == 3

    def test_weibull_mode(self):
        vals = np.array([1.0, 2.0, 3.0])
        pids = np.array(["A", "B", "C"])
        trace = _extract_one_trace(vals, pids, "weibull", "g1_TX", "TX")
        assert trace["name"] == "g1_TX"
        assert len(trace["y"]) == 3
        # Weibull y should differ from CDF y
        cdf_trace = _extract_one_trace(vals, pids, "cdf", "g1_TX", "TX")
        assert trace["y"] != cdf_trace["y"]

    def test_single_value(self):
        vals = np.array([42.0])
        pids = np.array(["A"])
        trace = _extract_one_trace(vals, pids, "cdf", "single", "T0")
        assert trace["n"] == 1
        assert trace["x"] == [42.0]


# ═══════════════════════════════════════════════════════════════
#  read_compare_file
# ═══════════════════════════════════════════════════════════════

class TestReadCompareFile:

    def test_read_valid(self, compare_result_xlsx):
        """Read a valid compare result Excel file."""
        df = read_compare_file(str(compare_result_xlsx))
        assert not df.empty
        assert "PART_ID" in df.columns
        assert "GROUP" in df.columns
        assert "IDSS_T0" in df.columns
        assert "IDSS_TX" in df.columns
        assert "IDSS_shift" in df.columns
        assert "VTH_T0" in df.columns
        assert len(df) == 2  # 2 data rows

    def test_meta_parsed(self, compare_result_xlsx):
        """Meta dict should be populated from rows 2-7."""
        df = read_compare_file(str(compare_result_xlsx))
        meta = df.attrs.get("meta", {})
        assert "unit" in meta
        assert "IDSS" in meta.get("unit", {})
        assert meta["unit"]["IDSS"] == "A"

    def test_non_existent_file(self):
        """Non-existent file — openpyxl raises FileNotFoundError."""
        import openpyxl
        with pytest.raises(FileNotFoundError):
            read_compare_file("/nonexistent/path.xlsx")

    def test_no_data_rows(self, tmp_data_dir):
        """File with only 7 rows (no data) → empty."""
        from openpyxl import Workbook
        path = tmp_data_dir / "no_data.xlsx"
        wb = Workbook()
        ws = wb.active
        ws.append(["PART_ID", "SOFT_BIN"])
        for _ in range(6):
            ws.append([""])
        wb.save(path)
        wb.close()
        df = read_compare_file(str(path))
        assert df.empty

    def test_single_data_row(self, tmp_data_dir):
        """Single data row should parse correctly."""
        from openpyxl import Workbook
        path = tmp_data_dir / "single.xlsx"
        wb = Workbook()
        ws = wb.active
        ws.append(["PART_ID", "SOFT_BIN", "GROUP", "file", "IDSS", "", ""])
        # Rows 2-7: meta rows with empty test values
        ws.append(["unit", "", "", "", "A", "", ""])
        ws.append(["lower limit", "", "", "", "0", "", ""])
        ws.append(["higher limit", "", "", "", "0.001", "", ""])
        ws.append(["shift limit", "", "", "", "0.1", "", ""])
        ws.append(["limit side", "", "", "", "upper", "", ""])
        ws.append(["shift公式", "", "", "", "abs((TX-T0)/T0)", "", ""])
        # Row 8: sub-headers
        ws.append(["PART_ID", "SOFT_BIN", "GROUP", "file", "T0", "TX", "shift"])
        # Row 9: data
        ws.append(["SN001", "1", "HTRB", "tx.csv", 1.0, 2.0, 0.5])
        wb.save(path)
        wb.close()
        df = read_compare_file(str(path))
        assert len(df) >= 1
        assert "IDSS_T0" in df.columns
        assert df.iloc[0]["PART_ID"] == "SN001"


# ═══════════════════════════════════════════════════════════════
#  extract_traces_by_group / extract_traces_by_item
# ═══════════════════════════════════════════════════════════════

class TestExtractTraces:

    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            "PART_ID": ["SN001", "SN002", "SN003", "SN001", "SN002"],
            "SOFT_BIN": [1, 1, 1, 2, 2],
            "GROUP": ["HTRB_168H", "HTRB_168H", "HTRB_168H",
                      "HTSL_500H", "HTSL_500H"],
            "IDSS_T0": [1.0e-5, 2.0e-5, 3.0e-5, 1.0e-5, 2.0e-5],
            "IDSS_TX": [1.2e-5, 2.5e-5, 3.5e-5, 1.1e-5, 2.2e-5],
            "IDSS_shift": [0.2, 0.25, 0.17, 0.1, 0.1],
            "VTH_T0": [3.0, 3.5, 4.0, 3.0, 3.5],
            "VTH_TX": [3.1, 3.8, 4.2, 3.05, 3.6],
            "VTH_shift": [0.1, 0.3, 0.2, 0.05, 0.1],
        })

    def test_by_group(self, sample_df):
        """Extract traces grouped by GROUP."""
        traces = extract_traces_by_group(sample_df, "IDSS", "cdf")
        # 2 groups × 3 suffixes (T0, TX, shift) = 6 traces
        assert len(traces) == 6
        names = [t["name"] for t in traces]
        assert "HTRB_168H_T0" in names
        assert "HTRB_168H_TX" in names
        assert "HTRB_168H_shift" in names
        assert "HTSL_500H_T0" in names
        assert "HTSL_500H_TX" in names
        assert "HTSL_500H_shift" in names

    def test_by_group_weibull(self, sample_df):
        """Weibull mode still works."""
        traces = extract_traces_by_group(sample_df, "IDSS", "weibull")
        assert len(traces) == 6

    def test_by_group_nonexistent_item(self, sample_df):
        """Non-existent test item → empty list."""
        traces = extract_traces_by_group(sample_df, "NONEXIST", "cdf")
        assert traces == []

    def test_by_group_all_nan(self, sample_df):
        """All NaN values in a column → skip."""
        df = sample_df.copy()
        df["IDSS_T0"] = np.nan
        traces = extract_traces_by_group(df, "IDSS", "cdf")
        # T0 traces will have 0 values after dropna → skipped
        # So we get 4 traces (2 groups × 2 remaining suffixes)
        assert len(traces) == 4

    def test_by_item(self, sample_df):
        """Extract traces grouped by test item."""
        traces = extract_traces_by_item(sample_df, "HTRB_168H",
                                        ["IDSS", "VTH"], "cdf")
        # 2 items × 3 suffixes = 6 traces
        assert len(traces) == 6
        names = [t["name"] for t in traces]
        assert "IDSS_T0" in names
        assert "IDSS_TX" in names
        assert "VTH_T0" in names
        assert "VTH_shift" in names

    def test_by_item_empty_group(self, sample_df):
        """Group with no data → couldn't happen with proper df but check no crash."""
        traces = extract_traces_by_item(sample_df, "NONEXIST_GROUP",
                                        ["IDSS"], "cdf")
        assert traces == []

    def test_empty_dataframe(self):
        """Empty DataFrame → no traces."""
        df = pd.DataFrame(columns=["PART_ID", "SOFT_BIN", "GROUP", "IDSS_T0"])
        traces = extract_traces_by_group(df, "IDSS", "cdf")
        assert traces == []
        traces2 = extract_traces_by_item(df, "g1", ["IDSS"], "cdf")
        assert traces2 == []


# ═══════════════════════════════════════════════════════════════
#  build_plots  (smoke tests — return a Figure)
# ═══════════════════════════════════════════════════════════════

class TestBuildPlots:

    @pytest.fixture
    def sample_df(self):
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

    def test_build_by_group(self, sample_df):
        """Build plot grouped by group (each subplot = test item)."""
        config = {
            "rows": 2,
            "cols": 3,
            "marker_size": 6,
            "plot_type": "markers",
            "theme": "plotly_white",
        }
        fig = build_plots(sample_df, ["IDSS", "VTH"], "group", "cdf", config)
        assert fig is not None
        assert len(fig.data) >= 1

    def test_build_by_item(self, sample_df):
        """Build plot grouped by item (each subplot = group)."""
        config = {
            "rows": 1,
            "cols": 2,
            "marker_size": 6,
            "plot_type": "markers",
        }
        fig = build_plots(sample_df, ["IDSS", "VTH"], "item", "cdf", config)
        assert fig is not None

    def test_build_weibull(self, sample_df):
        """Weibull mode works."""
        config = {"rows": 1, "cols": 2, "plot_type": "markers"}
        fig = build_plots(sample_df, ["IDSS", "VTH"], "group", "weibull", config)
        assert fig is not None

    def test_empty_dataframe(self):
        """Empty DataFrame → figure with 'no data' annotation."""
        config = {"rows": 1, "cols": 1}
        fig = build_plots(pd.DataFrame(), [], "group", "cdf", config)
        annotations = fig.layout.annotations
        assert any("无数据" in (a.text or "") for a in annotations)

    def test_no_test_items(self, sample_df):
        """Empty test_items list → 'no data'."""
        config = {"rows": 1, "cols": 1}
        fig = build_plots(sample_df, [], "group", "cdf", config)
        annotations = fig.layout.annotations
        assert any("无数据" in (a.text or "") for a in annotations)

    def test_with_limit_line(self, sample_df):
        """Show limit lines."""
        config = {
            "rows": 1, "cols": 2,
            "show_limit_line": True,
            "limit_map": {"IDSS": 0.1, "VTH": 0.5},
            "direction_map": {"IDSS": "upper", "VTH": "upper"},
            "x_min": 0,
            "x_max": 1e-4,
        }
        fig = build_plots(sample_df, ["IDSS", "VTH"], "group", "cdf", config)
        assert fig is not None

    def test_with_draw_filter(self, sample_df):
        """Draw only T0 traces."""
        config = {
            "rows": 1, "cols": 2,
            "draw_t0": True,
            "draw_tx": False,
            "draw_shift": False,
        }
        fig = build_plots(sample_df, ["IDSS", "VTH"], "group", "cdf", config)
        assert fig is not None


# ═══════════════════════════════════════════════════════════════
#  save_html
# ═══════════════════════════════════════════════════════════════

class TestSaveHTML:

    def test_save_html(self, tmp_data_dir, sample_plot_df):
        """Save a figure as HTML file."""
        from pathlib import Path
        from core.plotting import build_plots, save_html
        config = {"rows": 1, "cols": 1, "plot_type": "markers"}
        fig = build_plots(sample_plot_df, ["IDSS"], "group", "cdf", config)
        out_path = str(tmp_data_dir / "test_plot.html")
        save_html(fig, out_path)
        assert Path(out_path).exists()
        content = Path(out_path).read_text(encoding="utf-8")
        assert "plotly" in content
        assert "html" in content


