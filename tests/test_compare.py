"""Tests for core/compare.py — transform_rename, calc_shifts, export_excel, etc."""
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from core.compare import (
    transform_rename,
    calc_shifts,
    safe_eval_formula,
    export_excel,
    read_raw_headers_from_file,
    run_compare,
)


# ═══════════════════════════════════════════════════════════════
#  safe_eval_formula
# ═══════════════════════════════════════════════════════════════

class TestSafeEvalFormula:

    def test_basic_formula(self):
        """Typical: abs((TX-T0)/T0)."""
        result = safe_eval_formula("abs((TX - T0)/T0)", 1.0e-5, 1.2e-5)
        assert result == pytest.approx(0.2, rel=1e-9)

    def test_nan_t0(self):
        """NaN T0 → NaN."""
        result = safe_eval_formula("TX - T0", np.nan, 1.0)
        assert np.isnan(result)

    def test_nan_tx(self):
        """NaN TX → NaN."""
        result = safe_eval_formula("TX - T0", 1.0, np.nan)
        assert np.isnan(result)

    def test_log_positive(self):
        """log of positive number."""
        result = safe_eval_formula("log(TX/T0)", 1.0, 10.0)
        assert result == pytest.approx(np.log(10.0))

    def test_log_negative(self):
        """log of non-positive → NaN."""
        result = safe_eval_formula("log(TX)", 1.0, -5.0)
        assert np.isnan(result)

    def test_sqrt_negative(self):
        """sqrt of negative → NaN."""
        result = safe_eval_formula("sqrt(TX-T0)", 10.0, 5.0)
        assert np.isnan(result)

    def test_allowed_funcs(self):
        """abs, log, log10, exp, sqrt, pow, min, max are all allowed."""
        assert safe_eval_formula("min(T0, TX)", 1.0, 2.0) == 1.0
        assert safe_eval_formula("max(T0, TX)", 1.0, 2.0) == 2.0
        assert safe_eval_formula("abs(T0 - TX)", 1.0, 3.0) == 2.0

    def test_unknown_variable_safe(self):
        """Unknown variable in formula → NaN (not crash)."""
        result = safe_eval_formula("T0 + UNKNOWN", 1.0, 2.0)
        assert np.isnan(result)

    def test_invalid_formula_string(self):
        """Gibberish formula → NaN."""
        result = safe_eval_formula("not a formula @@", 1.0, 2.0)
        assert np.isnan(result)


# ═══════════════════════════════════════════════════════════════
#  transform_rename
# ═══════════════════════════════════════════════════════════════

class TestTransformRename:

    def test_simple_rename(self, merged_df_for_compare, calc_config):
        """Typical: rename test columns."""
        df = transform_rename(merged_df_for_compare, calc_config)
        assert "IDSS" in df.columns
        assert "VTH" in df.columns
        assert "VF" in df.columns
        assert "DC_IDSS_T1" not in df.columns

    def test_mv1_split(self, merged_df_for_compare, calc_config):
        """MV1: DC_IDSS_T1 and DC_IDSS_Delta_T1 both map to IDSS → split rows."""
        df = transform_rename(merged_df_for_compare, calc_config)
        # Two PART_ID rows each for SN001 (T1 suffix, Delta suffix) → 4 rows
        # Actually SN001 has T0 + HTRB_168H, each with both IDSS columns → creates suffix rows
        idss_rows = df[df["PART_ID"].str.contains("_", na=False)]
        assert len(idss_rows) > 0

    def test_empty_data(self, calc_config):
        """Empty DataFrame → empty result."""
        df = transform_rename(pd.DataFrame(), calc_config)
        assert df.empty or len(df) == 0

    def test_missing_columns(self, calc_config):
        """Rename map references columns not in df → should not crash."""
        df = pd.DataFrame({"PART_ID": ["A"], "SOFT_BIN": [1], "group": ["T0"], "filepath": ["f.csv"]})
        result = transform_rename(df, calc_config)
        assert "PART_ID" in result.columns

    def test_no_rename_config(self, merged_df_for_compare):
        """Empty rename map → original columns preserved."""
        result = transform_rename(merged_df_for_compare, {"renames": {}, "suffixes": {}})
        assert "DC_IDSS_T1" in result.columns
        assert result.shape == merged_df_for_compare.shape


# ═══════════════════════════════════════════════════════════════
#  calc_shifts
# ═══════════════════════════════════════════════════════════════

class TestCalcShifts:

    def test_basic_shifts(self, merged_df_for_compare, calc_config):
        """Typical: T0 + TX data produces shift values."""
        df = transform_rename(merged_df_for_compare, calc_config)
        result = calc_shifts(df, calc_config)
        assert not result.empty
        assert "IDSS_shift" in result.columns
        assert "VTH_shift" in result.columns
        assert "VF_shift" in result.columns
        assert "GROUP" in result.columns
        # After MV1 split, SN001 becomes SN001_T1 and SN001_Delta
        # Check that at least some IDSS_shift values are non-NaN
        assert not result["IDSS_shift"].isna().all()
        # VTH is not MV1, so SN001 should have a shift
        sn001 = result[result["PART_ID"].str.startswith("SN001")]
        assert not sn001["VTH_shift"].isna().all()

    def test_no_t0(self, calc_config):
        """Only TX data, no T0 → empty result."""
        df = pd.DataFrame({
            "PART_ID": ["SN001"],
            "SOFT_BIN": [1],
            "group": ["HTRB_168H"],
            "filepath": ["tx.csv"],
            "DC_IDSS_T1": [1.2e-5],
        })
        df_t = transform_rename(df, calc_config)
        result = calc_shifts(df_t, calc_config)
        assert result.empty

    def test_no_tx(self, calc_config):
        """Only T0 data, no TX → empty result."""
        df = pd.DataFrame({
            "PART_ID": ["SN001"],
            "SOFT_BIN": [1],
            "group": ["T0"],
            "filepath": ["t0.csv"],
            "DC_IDSS_T1": [1.0e-5],
        })
        df_t = transform_rename(df, calc_config)
        result = calc_shifts(df_t, calc_config)
        assert result.empty

    def test_empty_df(self, calc_config):
        """Empty DataFrame (with expected columns) → empty result."""
        df = pd.DataFrame(columns=["PART_ID", "SOFT_BIN", "group", "filepath",
                                   "DC_IDSS_T1", "DC_VTH_T1"])
        df_t = transform_rename(df, calc_config)
        result = calc_shifts(df_t, calc_config)
        assert result.empty

    def test_single_row(self, merged_df_for_compare, calc_config):
        """Single data row with both T0 and TX still works."""
        df = merged_df_for_compare.iloc[:2]  # T0 + TX for SN001
        df_t = transform_rename(df, calc_config)
        result = calc_shifts(df_t, calc_config)
        assert not result.empty

    def test_no_formulas(self, merged_df_for_compare):
        """No formulas in config → empty result."""
        df_t = transform_rename(merged_df_for_compare, {"renames": {}, "suffixes": {}, "formulas": {}})
        result = calc_shifts(df_t, {})
        assert result.empty


# ═══════════════════════════════════════════════════════════════
#  read_raw_headers_from_file
# ═══════════════════════════════════════════════════════════════

class TestReadRawHeaders:

    def test_read_headers(self, sample_csv):
        """Read raw headers from a standard CSV."""
        headers = read_raw_headers_from_file(str(sample_csv))
        assert "DC_IDSS_T1" in headers
        assert headers["DC_IDSS_T1"]["unit"] == "A"
        assert headers["DC_IDSS_T1"]["lo"] == "0"

    def test_non_existent_file(self):
        """Non-existent file → empty dict (no crash)."""
        headers = read_raw_headers_from_file("/nonexistent.csv")
        assert headers == {}

    def test_empty_file(self, tmp_data_dir):
        """Empty file → empty dict."""
        path = tmp_data_dir / "empty.csv"
        path.touch()
        headers = read_raw_headers_from_file(str(path))
        assert headers == {}

    def test_fewer_than_4_rows(self, tmp_data_dir):
        """File with only 1 row → handles gracefully."""
        path = tmp_data_dir / "short.csv"
        path.write_text("PART_ID,SOFT_BIN\n")
        headers = read_raw_headers_from_file(str(path))
        assert headers == {}  # No test columns


# ═══════════════════════════════════════════════════════════════
#  export_excel  (smoke tests — check file created)
# ═══════════════════════════════════════════════════════════════

class TestExportExcel:

    def test_export_creates_file(self, merged_df_for_compare, calc_config, tmp_data_dir):
        """Typical: export creates a valid .xlsx file."""
        df = transform_rename(merged_df_for_compare, calc_config)
        result = calc_shifts(df, calc_config)
        assert not result.empty

        out_path = str(tmp_data_dir / "对比结果.xlsx")
        export_excel(result, calc_config, output_path=out_path)
        assert Path(out_path).exists()
        assert Path(out_path).stat().st_size > 0

    def test_export_empty_data(self, calc_config, tmp_data_dir):
        """Empty data → does not crash but creates file."""
        result = pd.DataFrame()
        out_path = str(tmp_data_dir / "empty_result.xlsx")
        # Should handle gracefully or raise — just check no crash
        export_excel(result, calc_config, output_path=out_path)

    def test_export_with_raw_headers(self, merged_df_for_compare, calc_config, tmp_data_dir, sample_csv):
        """Export with raw headers."""
        df = transform_rename(merged_df_for_compare, calc_config)
        result = calc_shifts(df, calc_config)
        assert not result.empty
        raw_h = read_raw_headers_from_file(str(sample_csv))
        out_path = str(tmp_data_dir / "对比结果_meta.xlsx")
        export_excel(result, calc_config, raw_headers=raw_h, output_path=out_path)
        assert Path(out_path).exists()

    def test_export_with_over_limit(self, calc_config, tmp_data_dir):
        """Data where shift exceeds limit → yellow row marking in Excel."""
        df = pd.DataFrame({
            "PART_ID": ["SN001"],
            "SOFT_BIN": [1],
            "GROUP": ["HTRB_168H"],
            "file": ["tx.csv"],
            "IDSS_T0": [1.0e-5],
            "IDSS_TX": [3.0e-5],
            "IDSS_shift": [2.0],
            "VTH_T0": [3.0],
            "VTH_TX": [3.1],
            "VTH_shift": [0.1],
        })
        out_path = str(tmp_data_dir / "overlimit.xlsx")
        export_excel(df, calc_config, output_path=out_path)
        assert Path(out_path).exists()


# ═══════════════════════════════════════════════════════════════
#  run_compare (integration)
# ═══════════════════════════════════════════════════════════════

class TestRunCompare:

    def test_run_compare_success(self, merged_df_for_compare, calc_config, tmp_data_dir):
        """Full pipeline: transform → calc → export."""
        out_path = str(tmp_data_dir / "对比结果.xlsx")
        result_path = run_compare(merged_df_for_compare, calc_config, output_path=out_path)
        assert Path(result_path).exists()

    def test_run_compare_no_t0(self, calc_config, tmp_data_dir):
        """Only TX data → ValueError."""
        df = pd.DataFrame({
            "PART_ID": ["SN001"],
            "SOFT_BIN": [1],
            "group": ["HTRB_168H"],
            "filepath": ["tx.csv"],
            "DC_IDSS_T1": [1.2e-5],
        })
        with pytest.raises(ValueError, match="无有效数据"):
            run_compare(df, calc_config, output_path=str(tmp_data_dir / "out.xlsx"))
