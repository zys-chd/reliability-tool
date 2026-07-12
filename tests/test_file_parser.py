"""Tests for core/file_parser.py — DefaultCSVParser, DefaultExcelParser, ParserManager."""
import csv
from pathlib import Path

import pandas as pd
import pytest

from core.file_parser import (
    DefaultCSVParser,
    DefaultExcelParser,
    ParserManager,
    get_parser_manager,
    read_file,
)


# ═══════════════════════════════════════════════════════════════
#  DefaultCSVParser
# ═══════════════════════════════════════════════════════════════

class TestDefaultCSVParser:

    def test_supported_extensions(self):
        p = DefaultCSVParser()
        assert ".csv" in p.supported_extensions
        assert ".txt" in p.supported_extensions
        assert ".dat" in p.supported_extensions

    def test_read_valid_csv(self, sample_csv):
        """Typical: read a valid CSV with 4-row header."""
        p = DefaultCSVParser()
        df = p.read(str(sample_csv))
        assert not df.empty
        assert "PART_ID" in df.columns
        assert "SOFT_BIN" in df.columns
        assert "DC_IDSS_T1" in df.columns
        # 3 data rows starting at row 5 (0-indexed: 4)
        assert len(df) == 3
        assert df.iloc[0]["PART_ID"] == "SN001"

    def test_bom_csv(self, sample_csv_bom):
        """UTF-8 BOM should be handled correctly."""
        p = DefaultCSVParser()
        df = p.read(str(sample_csv_bom))
        assert len(df) == 2
        assert df.iloc[0]["PART_ID"] == "SN001"

    def test_empty_data(self, sample_csv_no_data):
        """CSV with headers only → empty DataFrame."""
        p = DefaultCSVParser()
        df = p.read(str(sample_csv_no_data))
        assert df.empty or len(df) == 0

    def test_non_existent_file(self, tmp_data_dir):
        """Non-existent file → FileNotFoundError."""
        p = DefaultCSVParser()
        fake = tmp_data_dir / "nonexistent.csv"
        with pytest.raises(FileNotFoundError):
            p.read(str(fake))

    def test_corrupt_csv(self, tmp_data_dir):
        """Binary junk → parsing error."""
        path = tmp_data_dir / "corrupt.csv"
        path.write_bytes(b"\x00\x01\x02\xff\xfe\xfd")
        p = DefaultCSVParser()
        with pytest.raises(Exception):
            p.read(str(path))

    def test_only_one_data_row(self, tmp_data_dir):
        """Single data row is fine."""
        path = tmp_data_dir / "single.csv"
        rows = [
            ["PART_ID", "SOFT_BIN", "DC_T1"],
            ["Unit", "", "V"],
            ["Lower Limit", "", "0"],
            ["Higher Limit", "", "5"],
            ["SN001", "1", "2.5"],
        ]
        with open(path, "w", newline="") as f:
            csv.writer(f).writerows(rows)
        df = DefaultCSVParser().read(str(path))
        assert len(df) == 1
        assert df.iloc[0]["PART_ID"] == "SN001"

    # ── Merged header tests ───────────────────────────────────

    def test_split_header_merged(self, tmp_data_dir):
        """PART_ID/SOFT_BIN on row 0, test headers on row 1, data from row 5."""
        path = tmp_data_dir / "split_header.csv"
        rows = [
            ["PART_ID", "SOFT_BIN", "", ""],                    # row 0: part_id/soft_bin only
            ["",          "",        "DC_IGSS_T1", "DC_IDSS_T2"], # row 1: test column headers
            ["V",         "V",       "uA",         "V"],           # row 2: unit
            ["0",         "1",       "0",          "0.5"],         # row 3: lower limit
            ["10",        "10",      "100",        "50"],          # row 4: higher limit
            ["DIE001",    "1",       "0.5",        "100.2"],       # row 5: data
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        p = DefaultCSVParser(
            part_id_row=0,
            soft_bin_row=0,
            data_start_row=5,
        )
        df = p.read(str(path))
        assert not df.empty
        expected_cols = ["PART_ID", "SOFT_BIN", "DC_IGSS_T1", "DC_IDSS_T2"]
        assert list(df.columns) == expected_cols, f"Got {list(df.columns)}"
        assert len(df) == 1
        assert df.iloc[0]["PART_ID"] == "DIE001"
        assert int(df.iloc[0]["SOFT_BIN"]) == 1

    def test_split_header_with_fmt_info(self, tmp_data_dir):
        """Pass FormatInfo to DefaultCSVParser.read()."""
        from core.format_detector import FormatInfo

        path = tmp_data_dir / "split_header2.csv"
        rows = [
            ["PART_ID", "SOFT_BIN", "", ""],
            ["",          "",        "DC_T1", "DC_T2"],
            ["V",         "",        "V",     "V"],
            ["0",         "0",       "0",     "0"],
            ["5",         "5",       "5",     "5"],
            ["SN001",    "1",       "1.5",   "2.5"],
            ["SN002",    "2",       "2.0",   "3.0"],
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        fmt_info = FormatInfo(
            format_id="split_test",
            encoding="utf-8-sig",
            delimiter=",",
            header_rows=5,
            part_id_row=0,
            soft_bin_row=0,
            data_start_row=5,
            meta_schema={0: "part_id_header", 1: "header", 2: "unit",
                         3: "lower_limit", 4: "higher_limit"},
        )
        p = DefaultCSVParser()
        df = p.read(str(path), fmt_info=fmt_info)
        assert not df.empty
        expected_cols = ["PART_ID", "SOFT_BIN", "DC_T1", "DC_T2"]
        assert list(df.columns) == expected_cols, f"Got {list(df.columns)}"
        assert len(df) == 2
        assert df.iloc[0]["DC_T1"] == 1.5
        assert df.iloc[1]["DC_T2"] == 3.0

    def test_normal_csv_still_works(self, sample_csv):
        """Existing behavior unchanged when no split header."""
        p = DefaultCSVParser()
        df = p.read(str(sample_csv))
        assert not df.empty
        assert "PART_ID" in df.columns
        assert "SOFT_BIN" in df.columns
        assert "DC_IDSS_T1" in df.columns
        assert len(df) == 3


# ═══════════════════════════════════════════════════════════════
#  DefaultExcelParser (basic smoke tests)
# ═══════════════════════════════════════════════════════════════

class TestDefaultExcelParser:

    def test_supported_extensions(self):
        p = DefaultExcelParser()
        assert ".xlsx" in p.supported_extensions
        assert ".xls" in p.supported_extensions

    def test_non_existent_file(self):
        p = DefaultExcelParser()
        with pytest.raises(FileNotFoundError):
            p.read("/nonexistent/path.xlsx")


# ═══════════════════════════════════════════════════════════════
#  ParserManager
# ═══════════════════════════════════════════════════════════════

class TestParserManager:

    def test_register_and_read_csv(self, sample_csv):
        """Register CSV parser and read a CSV file."""
        mgr = ParserManager()
        mgr.register(DefaultCSVParser())
        df = mgr.read(str(sample_csv))
        assert len(df) == 3

    def test_default_parser_in_constructor(self, sample_csv):
        """Pass default parser in constructor."""
        mgr = ParserManager(default_parser=DefaultCSVParser())
        df = mgr.read(str(sample_csv))
        assert len(df) == 3

    def test_unsupported_extension(self, tmp_data_dir):
        """Unsupported extension → ValueError."""
        mgr = ParserManager()
        fake = tmp_data_dir / "test.xyz"
        fake.touch()
        with pytest.raises(ValueError, match="不支持的格式"):
            mgr.read(str(fake))

    def test_unsupported_case_insensitive(self, sample_csv):
        """Extension matching should be case-insensitive."""
        mgr = ParserManager()
        mgr.register(DefaultCSVParser())
        # Rename to .CSV (uppercase)
        upper_path = sample_csv.with_suffix(".CSV")
        sample_csv.rename(upper_path)
        df = mgr.read(str(upper_path))
        assert len(df) == 3

    def test_get_parser_manager_singleton(self):
        """get_parser_manager() returns a singleton."""
        mgr1 = get_parser_manager()
        mgr2 = get_parser_manager()
        assert mgr1 is mgr2

    def test_read_file_top_level(self, sample_csv):
        """read_file() convenience function."""
        df = read_file(str(sample_csv))
        assert not df.empty

    def test_multiple_parsers(self):
        """Register multiple parsers for different extensions."""
        mgr = ParserManager()
        mgr.register(DefaultCSVParser())
        mgr.register(DefaultExcelParser())
        assert len(mgr._parsers) >= 4  # csv, txt, dat, xlsx, xls
