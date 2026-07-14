"""Edge-case tests for DefaultCSVParser and data pipeline.

Covers:
1. Empty entire columns causing header-data misalignment (issue 4)
2. Ragged CSV rows (missing trailing commas) (issue 4)
3. Unit conversion integration — verify it IS applied during loading (issue 3)
"""
import csv
from pathlib import Path

import pandas as pd
import pytest

from core.file_parser import DefaultCSVParser, ParserManager
from core.unit_converter import UnitConverter


# ═══════════════════════════════════════════════════════════════════
#  Issue 4: Empty columns causing misalignment
# ═══════════════════════════════════════════════════════════════════


class TestEmptyColumnAlignment:

    def test_column_entirely_empty_in_data(self, tmp_data_dir):
        """When a test column has ALL empty values in data rows,
        the header and data should remain aligned (no column shift).

        CSV: header has 4 columns, data rows only have 3 values
        (last column entirely empty, no trailing comma).
        """
        p = tmp_data_dir / "empty_col.csv"
        rows = [
            ["PART_ID", "SOFT_BIN", "DC_T1", "DC_T2"],
            ["Unit", "", "V", "V"],
            ["Lower", "", "0", "0"],
            ["Higher", "", "5", "5"],
            ["SN001", "1", "1.5", ""],     # DC_T2 empty
            ["SN002", "1", "2.0", ""],     # DC_T2 empty
        ]
        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        parser = DefaultCSVParser()
        df = parser.read(str(p))

        # Must have all 4 columns
        expected = ["PART_ID", "SOFT_BIN", "DC_T1", "DC_T2"]
        actual = list(df.columns)
        assert actual == expected, (
            f"Column mismatch: expected {expected}, got {actual}"
        )
        # DC_T2 should be NaN (empty)
        assert df["DC_T2"].isna().all(), (
            "DC_T2 should be all NaN (empty column)"
        )

    def test_no_trailing_commas_ragged_data(self, tmp_data_dir):
        """Data rows with fewer columns than header (ragged).
        
        This simulates a CSV where the last column is entirely missing
        from data rows (no trailing commas). pandas should still align.
        """
        # Create a CSV manually to precisely control trailing commas
        p = tmp_data_dir / "ragged.csv"
        lines = [
            "PART_ID,SOFT_BIN,DC_T1,DC_T2,DC_T3",
            "Unit,,V,V,V",
            "Lower,,0,0,0",
            "Higher,,5,5,5",
            "SN001,1,1.5,2.5,3.5",
            "SN002,1,1.6,2.6",       # missing DC_T3 value, NO trailing comma
            "SN003,2,1.7,2.7",       # also missing DC_T3
        ]
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")

        parser = DefaultCSVParser()
        df = parser.read(str(p))

        # All 5 columns must be present
        expected = ["PART_ID", "SOFT_BIN", "DC_T1", "DC_T2", "DC_T3"]
        actual = list(df.columns)
        assert actual == expected, (
            f"Ragged data caused column misalignment: {actual}"
        )
        # SN002/SN003 should have NaN in DC_T3
        assert pd.isna(df.loc[df["PART_ID"] == "SN002", "DC_T3"].iloc[0]), (
            "SN002 DC_T3 should be NaN (missing value)"
        )

    def test_middle_column_entirely_empty(self, tmp_data_dir):
        """A column in the middle (not last) that's entirely empty.
        
        This is more challenging because CSV readers handle it differently.
        We need to ensure no column shift occurs.
        """
        p = tmp_data_dir / "mid_empty.csv"
        # DC_T2 column is entirely empty — commas present but no data
        lines = [
            "PART_ID,SOFT_BIN,DC_T1,DC_T2,DC_T3",
            "Unit,,V,V,V",
            "Lower,,0,0,0",
            "Higher,,5,5,5",
            "SN001,1,1.5,,3.5",
            "SN002,1,2.0,,4.0",
        ]
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")

        parser = DefaultCSVParser()
        df = parser.read(str(p))

        expected = ["PART_ID", "SOFT_BIN", "DC_T1", "DC_T2", "DC_T3"]
        actual = list(df.columns)
        assert actual == expected, (
            f"Middle empty column caused misalignment: {actual}"
        )
        assert df["DC_T2"].isna().all(), "DC_T2 should be all NaN"
        assert df["DC_T3"].iloc[0] == 3.5, "DC_T3 value should be preserved"

    def test_empty_column_with_split_header(self, tmp_data_dir):
        """Split-header CSV where a test column has entirely empty data."""
        p = tmp_data_dir / "split_empty.csv"
        # PART_ID on row 0, test headers on row 1, data from row 5
        rows = [
            ["PART_ID", "SOFT_BIN", "", "", ""],
            ["", "", "DC_IGSS_T1", "DC_BV_T1", "DC_TEMP_T1"],
            ["V", "", "uA", "V", "°C"],
            ["0", "1", "0", "0.5", "-40"],
            ["10", "10", "100", "3.3", "150"],
            ["DIE001", "1", "0.5", "2.5", "25"],
            ["DIE002", "1", "0.6", "", "85"],     # DC_BV_T1 empty
            ["DIE003", "2", "", "", "125"],        # DC_IGSS_T1 + DC_BV_T1 empty
        ]
        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        parser = DefaultCSVParser(
            part_id_row=0, soft_bin_row=0, data_start_row=5,
        )
        from core.format_detector import FormatInfo
        fmt_info = FormatInfo(
            format_id="split_test",
            header_rows=5,
            part_id_row=0, soft_bin_row=0, data_start_row=5,
            meta_schema={0: "part_id_header", 1: "header",
                         2: "unit", 3: "lower_limit", 4: "higher_limit"},
        )
        df = parser.read(str(p), fmt_info=fmt_info)

        expected = ["PART_ID", "SOFT_BIN", "DC_IGSS_T1", "DC_BV_T1", "DC_TEMP_T1"]
        actual = list(df.columns)
        assert actual == expected, (
            f"Split header with empty columns misaligned: {actual}"
        )
        # DIE003 should have NaN for DC_IGSS_T1 and DC_BV_T1
        die3 = df[df["PART_ID"] == "DIE003"].iloc[0]
        assert pd.isna(die3["DC_IGSS_T1"]), "DIE003 DC_IGSS_T1 should be NaN"
        assert pd.isna(die3["DC_BV_T1"]), "DIE003 DC_BV_T1 should be NaN"
        assert die3["DC_TEMP_T1"] == 125, "DIE003 DC_TEMP_T1 should be 125"

    def test_all_columns_empty_no_data(self, tmp_data_dir):
        """CSV with header but ALL data cells empty — should not crash."""
        p = tmp_data_dir / "all_empty.csv"
        rows = [
            ["PART_ID", "SOFT_BIN", "DC_T1", "DC_T2"],
            ["Unit", "", "V", "V"],
            ["Lower", "", "0", "0"],
            ["Higher", "", "5", "5"],
            ["", "", "", ""],  # Empty data row
            ["", "", "", ""],
        ]
        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        parser = DefaultCSVParser()
        df = parser.read(str(p))

        # Should not crash
        assert list(df.columns) == ["PART_ID", "SOFT_BIN", "DC_T1", "DC_T2"]


# ═══════════════════════════════════════════════════════════════════
#  Issue 3: Unit conversion — verify it's actually applied
# ═══════════════════════════════════════════════════════════════════


class TestUnitConversionPipeline:

    def test_unit_row_parsed_by_format_detector(self, tmp_data_dir):
        """The unit row (row 1 in standard CSV) should be parsed and
        available in FormatInfo.
        """
        from core.format_detector import FormatDetector

        p = tmp_data_dir / "with_units.csv"
        rows = [
            ["PART_ID", "SOFT_BIN", "DC_IGSS_1", "DC_BV_1", "DC_IDSS_T1"],
            ["Unit", "", "uA", "V", "A"],
            ["Lower Limit", "", "0", "0.5", "0"],
            ["Higher Limit", "", "100", "3.3", "0.001"],
            ["SN001", "1", "0.5", "2.5", "1.23e-05"],
        ]
        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        info = FormatDetector().detect(p)
        # unit_row should be set
        assert info.unit_row == 1, f"Expected unit_row=1, got {info.unit_row}"

    def test_unit_converter_class_works(self):
        """UnitConverter can parse and convert basic units. (Pre-existing)"""
        val, unit = UnitConverter.convert(50, "uA")
        assert val == pytest.approx(5e-5, rel=1e-12)
        assert unit == "A"

        val, unit = UnitConverter.convert(100, "mA")
        assert val == pytest.approx(0.1, rel=1e-12)
        assert unit == "A"

        val, unit = UnitConverter.convert(5, "kV")
        assert val == pytest.approx(5000, rel=1e-12)
        assert unit == "V"

    def test_unit_conversion_applied_with_fmt_info(self, tmp_data_dir):
        """When fmt_info is provided and unit row exists, values should
        be converted to SI units automatically.
        """
        from core.format_detector import FormatDetector

        p = tmp_data_dir / "microamp_data.csv"
        rows = [
            ["PART_ID", "SOFT_BIN", "DC_IGSS_1"],
            ["Unit", "", "uA"],
            ["Lower Limit", "", "0"],
            ["Higher Limit", "", "100"],
            ["SN001", "1", "50"],    # 50 uA → should become 5e-5 A
            ["SN002", "1", "100"],   # 100 uA → should become 1e-4 A
        ]
        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        # Use detect_and_read to pass fmt_info through the pipeline
        from core.file_parser import ParserManager
        mgr = ParserManager()
        mgr.register(DefaultCSVParser())
        df = mgr.detect_and_read(str(p))

        assert "DC_IGSS_1" in df.columns
        # Values should be converted: 50 uA → 5e-5 A
        assert df["DC_IGSS_1"].iloc[0] == pytest.approx(5e-5, rel=1e-12)
        assert df["DC_IGSS_1"].iloc[1] == pytest.approx(1e-4, rel=1e-12)

    def test_direct_parser_with_fmt_info_converts(self, tmp_data_dir):
        """Direct parser.read() with fmt_info should also convert."""
        from core.format_detector import FormatDetector

        p = tmp_data_dir / "milliamp_data.csv"
        rows = [
            ["PART_ID", "SOFT_BIN", "DC_IDSS_T1", "DC_VF_T1"],
            ["Unit", "", "mA", "V"],
            ["Lower Limit", "", "0", "0"],
            ["Higher Limit", "", "100", "5"],
            ["DIE001", "1", "50", "1.2"],    # 50 mA → 0.05 A
            ["DIE002", "1", "100", "2.5"],   # 100 mA → 0.1 A
        ]
        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        fmt_info = FormatDetector().detect(str(p))
        parser = DefaultCSVParser()
        df = parser.read(str(p), fmt_info=fmt_info)

        # mA → A conversion
        assert df["DC_IDSS_T1"].iloc[0] == pytest.approx(0.05, rel=1e-12)
        assert df["DC_IDSS_T1"].iloc[1] == pytest.approx(0.1, rel=1e-12)
        # V → no conversion needed
        assert df["DC_VF_T1"].iloc[0] == 1.2

    def test_mixed_units_across_files_converted(self, tmp_data_dir):
        """Two files with different units for same parameter should
        both be in SI units after conversion.
        """
        from core.file_parser import ParserManager
        mgr = ParserManager()
        mgr.register(DefaultCSVParser())

        # File 1: DC_IGSS_1 in uA
        p1 = tmp_data_dir / "file1_uA.csv"
        rows1 = [
            ["PART_ID", "SOFT_BIN", "DC_IGSS_1"],
            ["Unit", "", "uA"],
            ["Lower", "", "0"],
            ["Higher", "", "100"],
            ["DIE001", "1", "50"],
            ["DIE002", "1", "100"],
        ]
        with open(p1, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows1)

        # File 2: DC_IGSS_1 in mA
        p2 = tmp_data_dir / "file2_mA.csv"
        rows2 = [
            ["PART_ID", "SOFT_BIN", "DC_IGSS_1"],
            ["Unit", "", "mA"],
            ["Lower", "", "0"],
            ["Higher", "", "0.1"],
            ["DIE003", "1", "0.05"],
            ["DIE004", "1", "0.10"],
        ]
        with open(p2, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows2)

        df1 = mgr.detect_and_read(str(p1))
        df2 = mgr.detect_and_read(str(p2))

        # Both should now be in Amps
        # 50 uA = 5e-5 A, 0.05 mA = 5e-5 A → same value in SI
        assert df1["DC_IGSS_1"].iloc[0] == pytest.approx(5e-5, rel=1e-12)
        assert df2["DC_IGSS_1"].iloc[0] == pytest.approx(5e-5, rel=1e-12)
        # Both 100 uA and 0.10 mA = 1e-4 A
        assert df1["DC_IGSS_1"].iloc[1] == pytest.approx(1e-4, rel=1e-12)
        assert df2["DC_IGSS_1"].iloc[1] == pytest.approx(1e-4, rel=1e-12)

    def test_unit_conversion_no_unit_row_does_nothing(self, tmp_data_dir):
        """CSV without a unit row should not trigger conversion."""
        p = tmp_data_dir / "no_units.csv"
        rows = [
            ["PART_ID", "SOFT_BIN", "DC_T1", "DC_T2"],
            ["SN001", "1", "50", "1.5"],
            ["SN002", "1", "100", "2.5"],
            ["SN003", "2", "75", "3.0"],
        ]
        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        # Use parser directly without fmt_info (no unit conversion, no filtering)
        parser = DefaultCSVParser(skiprows=[])
        df = parser.read(str(p))
        # No unit row → values are raw
        assert df["DC_T1"].iloc[0] == 50
        assert df["DC_T2"].iloc[1] == 2.5

    def test_unit_conversion_in_pipeline_now(self):
        """Verify unit_converter is now imported by pipeline code."""
        import os
        pipeline_files = [
            "core/file_parser.py",
            "core/data_merge.py",
            "ui/gen/FTDataAnalisys.py",
        ]
        root = Path(__file__).resolve().parent.parent
        found = False
        for rel_path in pipeline_files:
            full_path = root / rel_path
            if full_path.exists():
                content = full_path.read_text(encoding="utf-8")
                if "unit_converter" in content:
                    found = True
                    break
        assert found, (
            "unit_converter should now be imported in at least one "
            "pipeline file (file_parser.py)"
        )


# ═══════════════════════════════════════════════════════════════════
#  Regression: existing parser behavior
# ═══════════════════════════════════════════════════════════════════


class TestRegression:

    def test_standard_csv_still_works(self, sample_csv):
        """Existing CSV parsing unchanged."""
        parser = DefaultCSVParser()
        df = parser.read(str(sample_csv))
        assert not df.empty
        assert "PART_ID" in df.columns
        assert len(df) == 3

    def test_bom_csv_still_works(self, sample_csv_bom):
        """BOM CSV parsing unchanged."""
        parser = DefaultCSVParser()
        df = parser.read(str(sample_csv_bom))
        assert len(df) == 2

    def test_no_data_rows(self, sample_csv_no_data):
        """No data rows still works."""
        parser = DefaultCSVParser()
        df = parser.read(str(sample_csv_no_data))
        assert df.empty or len(df) == 0

    def test_split_header_with_fmt_info(self, tmp_data_dir):
        """Split header parsing unchanged."""
        path = tmp_data_dir / "split_regression.csv"
        rows = [
            ["PART_ID", "SOFT_BIN", "", ""],
            ["", "", "DC_T1", "DC_T2"],
            ["V", "", "V", "V"],
            ["0", "0", "0", "0"],
            ["5", "5", "5", "5"],
            ["SN001", "1", "1.5", "2.5"],
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        from core.format_detector import FormatInfo
        fmt_info = FormatInfo(
            format_id="split_test",
            header_rows=5,
            part_id_row=0, soft_bin_row=0, data_start_row=5,
            meta_schema={0: "part_id_header", 1: "header",
                         2: "unit", 3: "lower_limit", 4: "higher_limit"},
        )
        parser = DefaultCSVParser()
        df = parser.read(str(path), fmt_info=fmt_info)
        assert list(df.columns) == ["PART_ID", "SOFT_BIN", "DC_T1", "DC_T2"]
        assert len(df) == 1
