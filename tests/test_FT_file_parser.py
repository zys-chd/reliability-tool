"""Tests for FTData — unified FT file parser."""
import csv
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from core.FT_file_parser import FTData, FTParseError

# ── Default test config (embedded as TOML) ──

DEFAULT_CONFIG = """
[[signatures]]
format_id = "TEST"
header_identifiers = ["PART_ID", "SOFT_BIN"]
part_id_offset = 0
data_col_header_offset = 0
unit_offset = 1
lower_limit_offset = 2
higher_limit_offset = 3
data_start_offset = 4
pre_test_columns = ["SOFT_BIN"]
delimiter = ","
encoding = "utf-8-sig"
skip_row_values = {PART_ID = ["1", "END"]}
column_map = {}
"""


@pytest.fixture
def tmp_cfg(tmp_path) -> Path:
    """Write default config to a temp dir, return path."""
    p = tmp_path / "test.toml"
    p.write_text(DEFAULT_CONFIG)
    return p


def make_csv(rows: list[list], path: Path, encoding="utf-8"):
    with open(path, "w", newline="", encoding=encoding) as f:
        csv.writer(f).writerows(rows)
    return path


# ═══════════════════════════════════════════════════════════════════
#  Basic parse
# ═══════════════════════════════════════════════════════════════════


class TestBasicParse:

    def test_standard_csv(self, tmp_path, tmp_cfg):
        """Standard CSV with 4-row header + data."""
        csv_path = make_csv([
            ["PART_ID", "SOFT_BIN", "DC_IGSS_1", "DC_BV_1"],
            ["Unit", "", "uA", "V"],
            ["Lower Limit", "", "0", "0.5"],
            ["Higher Limit", "", "100", "3.3"],
            ["SN001", "1", "50", "2.5"],
            ["SN002", "1", "100", "3.0"],
        ], tmp_path / "test.csv")

        ft = FTData(str(csv_path), str(tmp_cfg))
        assert ft.test_columns == ["DC_IGSS_1", "DC_BV_1"]
        assert ft.units["DC_IGSS_1"] == "A"
        assert ft.units["DC_BV_1"] == "V"
        assert len(ft.data) == 2
        # Unit conversion: 50 uA → 5e-5 A
        assert ft.data["DC_IGSS_1"].iloc[0] == pytest.approx(5e-5, rel=1e-12)

    def test_column_mapping(self, tmp_path, tmp_cfg):
        """Column map renames MODULE_ID → PART_ID."""
        cfg = tmp_path / "cfg.toml"
        cfg.write_text("""
[[signatures]]
format_id = "TEST"
header_identifiers = ["MODULE_ID", "BIN"]
part_id_offset = 0
data_col_header_offset = 0
unit_offset = 1
lower_limit_offset = 2
higher_limit_offset = 3
data_start_offset = 4
pre_test_columns = ["SOFT_BIN"]
delimiter = ","
skip_row_values = {}
column_map = {MODULE_ID = "PART_ID", BIN = "SOFT_BIN"}
""")
        csv_path = make_csv([
            ["MODULE_ID", "BIN", "DC_T1"],
            ["Unit", "", "V"],
            ["Lower", "", "0"],
            ["Higher", "", "5"],
            ["SN001", "1", "2.5"],
        ], tmp_path / "test.csv")

        ft = FTData(str(csv_path), str(cfg))
        assert "PART_ID" in ft.data.columns
        assert ft.data["PART_ID"].iloc[0] == "SN001"

    def test_file_not_found(self, tmp_cfg):
        """Non-existent file raises FTParseError."""
        with pytest.raises(FTParseError, match="文件不存在"):
            FTData("/nonexistent/path.csv", str(tmp_cfg))

    def test_no_identifiers_match(self, tmp_path, tmp_cfg):
        """File without matching identifiers raises FTParseError."""
        csv_path = make_csv([
            ["ColA", "ColB", "ColC"],
            ["1", "2", "3"],
        ], tmp_path / "test.csv")
        with pytest.raises(FTParseError, match="无法识别文件格式"):
            FTData(str(csv_path), str(tmp_cfg))


# ═══════════════════════════════════════════════════════════════════
#  Format detection edge cases
# ═══════════════════════════════════════════════════════════════════


class TestFormatDetection:

    def test_with_blank_rows_before_header(self, tmp_path, tmp_cfg):
        """Blank rows before the header should be ignored."""
        csv_path = make_csv([
            ["Some", "junk"],
            [],
            [],
            ["PART_ID", "SOFT_BIN", "DC_T1"],
            ["Unit", "", "V"],
            ["Lower", "", "0"],
            ["Higher", "", "5"],
            ["DIE001", "1", "2.5"],
        ], tmp_path / "test.csv")
        ft = FTData(str(csv_path), str(tmp_cfg))
        assert len(ft.data) == 1
        assert ft.data["DC_T1"].iloc[0] == pytest.approx(2.5)

    def test_junk_rows_before_header(self, tmp_path, tmp_cfg):
        """Many junk rows before the real header."""
        rows = [[f"junk_{i}"] * 3 for i in range(100)]
        rows.append(["PART_ID", "SOFT_BIN", "DC_T1"])
        rows.append(["Unit", "", "V"])
        rows.append(["Lower", "", "0"])
        rows.append(["Higher", "", "5"])
        rows.append(["DIE001", "1", "2.5"])
        csv_path = make_csv(rows, tmp_path / "test.csv")
        ft = FTData(str(csv_path), str(tmp_cfg))
        assert len(ft.data) == 1

    def test_bom_csv(self, tmp_path, tmp_cfg):
        """UTF-8 BOM should be handled."""
        csv_path = tmp_path / "bom.csv"
        content = '\ufeff' + ','.join(["PART_ID", "SOFT_BIN", "DC_T1"]) + '\n'
        content += ','.join(["Unit", "", "V"]) + '\n'
        content += ','.join(["Lower", "", "0"]) + '\n'
        content += ','.join(["Higher", "", "5"]) + '\n'
        content += ','.join(["SN001", "1", "2.5"]) + '\n'
        csv_path.write_text(content, encoding="utf-8-sig")
        ft = FTData(str(csv_path), str(tmp_cfg))
        assert "PART_ID" in ft.data.columns
        assert len(ft.data) == 1

    def test_multiple_signatures_choose_best(self, tmp_path):
        """When multiple signatures match, the one with more identifiers wins."""
        cfg = tmp_path / "cfg.toml"
        cfg.write_text("""
[[signatures]]
format_id = "SIG_A"
header_identifiers = ["PART_ID"]
part_id_offset = 0
data_col_header_offset = 0
unit_offset = -1
lower_limit_offset = -1
higher_limit_offset = -1
data_start_offset = 1
pre_test_columns = []
delimiter = ","
skip_row_values = {}

[[signatures]]
format_id = "SIG_B"
header_identifiers = ["PART_ID", "SOFT_BIN"]
part_id_offset = 0
data_col_header_offset = 0
unit_offset = -1
lower_limit_offset = -1
higher_limit_offset = -1
data_start_offset = 1
pre_test_columns = []
delimiter = ","
skip_row_values = {}
""")
        csv_path = make_csv([
            ["PART_ID", "SOFT_BIN", "DC_T1"],
            ["SN001", "1", "2.5"],
        ], tmp_path / "test.csv")
        ft = FTData(str(csv_path), str(cfg))
        # SIG_B has more identifiers → should win
        assert "SOFT_BIN" in ft.data.columns

    def test_tsv_format(self, tmp_path):
        """Tab-separated file should be detected with tab delimiter."""
        cfg = tmp_path / "cfg.toml"
        cfg.write_text("""
[[signatures]]
format_id = "TSV"
header_identifiers = ["PART_ID", "SOFT_BIN"]
data_start_offset = 1
pre_test_columns = []
delimiter = "\\t"
skip_row_values = {}
""")
        csv_path = tmp_path / "test.tsv"
        csv_path.write_text("PART_ID\tSOFT_BIN\tDC_T1\nSN001\t1\t2.5\n")
        ft = FTData(str(csv_path), str(cfg))
        assert len(ft.data) == 1


# ═══════════════════════════════════════════════════════════════════
#  Unit conversion
# ═══════════════════════════════════════════════════════════════════


class TestUnitConversion:

    def test_uA_to_A(self, tmp_path, tmp_cfg):
        csv_path = make_csv([
            ["PART_ID", "SOFT_BIN", "DC_IGSS_1"],
            ["Unit", "", "uA"],
            ["Lower", "", "0"],
            ["Higher", "", "100"],
            ["SN001", "1", "50"],
            ["SN002", "1", "100"],
        ], tmp_path / "test.csv")
        ft = FTData(str(csv_path), str(tmp_cfg))
        assert ft.data["DC_IGSS_1"].iloc[0] == pytest.approx(5e-5, rel=1e-12)
        assert ft.data["DC_IGSS_1"].iloc[1] == pytest.approx(1e-4, rel=1e-12)
        assert ft.units["DC_IGSS_1"] == "A"

    def test_mA_to_A(self, tmp_path, tmp_cfg):
        csv_path = make_csv([
            ["PART_ID", "SOFT_BIN", "DC_IDSS_T1"],
            ["Unit", "", "mA"],
            ["Lower", "", "0"],
            ["Higher", "", "100"],
            ["DIE001", "1", "50"],
            ["DIE002", "1", "100"],
        ], tmp_path / "test.csv")
        ft = FTData(str(csv_path), str(tmp_cfg))
        assert ft.data["DC_IDSS_T1"].iloc[0] == pytest.approx(0.05, rel=1e-12)

    def test_kV_to_V(self, tmp_path, tmp_cfg):
        csv_path = make_csv([
            ["PART_ID", "SOFT_BIN", "DC_BV_1"],
            ["Unit", "", "kV"],
            ["Lower", "", "0"],
            ["Higher", "", "10"],
            ["DIE001", "1", "5"],
        ], tmp_path / "test.csv")
        ft = FTData(str(csv_path), str(tmp_cfg))
        assert ft.data["DC_BV_1"].iloc[0] == pytest.approx(5000.0, rel=1e-12)
        assert ft.units["DC_BV_1"] == "V"

    def test_V_no_conversion(self, tmp_path, tmp_cfg):
        csv_path = make_csv([
            ["PART_ID", "SOFT_BIN", "DC_VF_1"],
            ["Unit", "", "V"],
            ["Lower", "", "0"],
            ["Higher", "", "5"],
            ["DIE001", "1", "2.5"],
        ], tmp_path / "test.csv")
        ft = FTData(str(csv_path), str(tmp_cfg))
        assert ft.data["DC_VF_1"].iloc[0] == pytest.approx(2.5)
        assert ft.units["DC_VF_1"] == "V"


# ═══════════════════════════════════════════════════════════════════
#  Filtering: skip_row_values + stop_at_blank_row
# ═══════════════════════════════════════════════════════════════════


class TestFiltering:

    def test_skip_part_id_1_and_END(self, tmp_path, tmp_cfg):
        csv_path = make_csv([
            ["PART_ID", "SOFT_BIN", "DC_T1"],
            ["Unit", "", "V"],
            ["Lower", "", "0"],
            ["Higher", "", "5"],
            ["SN001", "1", "2.5"],
            ["1", "1", "99"],       # should be skipped
            ["SN002", "1", "3.0"],
            ["END", "1", "88"],     # should be skipped
            ["SN003", "1", "3.5"],
        ], tmp_path / "test.csv")
        ft = FTData(str(csv_path), str(tmp_cfg))
        assert len(ft.data) == 3
        assert list(ft.data["PART_ID"]) == ["SN001", "SN002", "SN003"]
        assert 99 not in ft.data["DC_T1"].values

    def test_stop_at_blank_row(self, tmp_path, tmp_cfg):
        csv_path = make_csv([
            ["PART_ID", "SOFT_BIN", "DC_T1"],
            ["Unit", "", "V"],
            ["Lower", "", "0"],
            ["Higher", "", "5"],
            ["SN001", "1", "1.0"],
            ["SN002", "1", "2.0"],
            [],          # blank → stop
            ["SN003", "1", "3.0"],
            ["SN004", "1", "4.0"],
        ], tmp_path / "test.csv")
        ft = FTData(str(csv_path), str(tmp_cfg))
        assert len(ft.data) == 2  # SN003, SN004 dropped


# ═══════════════════════════════════════════════════════════════════
#  Meta rows (Unit / LL / HL) and properties
# ═══════════════════════════════════════════════════════════════════


class TestMetaAndProperties:

    def test_units_property(self, tmp_path, tmp_cfg):
        csv_path = make_csv([
            ["PART_ID", "SOFT_BIN", "DC_T1", "DC_T2"],
            ["Unit", "", "V", "mA"],
            ["Lower", "", "0", "0"],
            ["Higher", "", "5", "100"],
            ["SN001", "1", "2.5", "50"],
        ], tmp_path / "test.csv")
        ft = FTData(str(csv_path), str(tmp_cfg))
        assert ft.units["DC_T1"] == "V"
        assert ft.units["DC_T2"] == "A"  # mA → A after conversion

    def test_lower_higher_limits(self, tmp_path, tmp_cfg):
        csv_path = make_csv([
            ["PART_ID", "SOFT_BIN", "DC_T1", "DC_T2"],
            ["Unit", "", "V", "V"],
            ["Lower", "", "0", "1.5"],
            ["Higher", "", "5", "3.3"],
            ["SN001", "1", "2.5", "2.0"],
        ], tmp_path / "test.csv")
        ft = FTData(str(csv_path), str(tmp_cfg))
        assert ft.lower_limits["DC_T1"] == pytest.approx(0)
        assert ft.lower_limits["DC_T2"] == pytest.approx(1.5)
        assert ft.higher_limits["DC_T1"] == pytest.approx(5)
        assert ft.higher_limits["DC_T2"] == pytest.approx(3.3)

    def test_data_property(self, tmp_path, tmp_cfg):
        """Data property should exclude first 3 rows (Unit/LL/HL)."""
        csv_path = make_csv([
            ["PART_ID", "SOFT_BIN", "DC_T1"],
            ["Unit", "", "V"],
            ["Lower", "", "0"],
            ["Higher", "", "5"],
            ["SN001", "1", "2.5"],
            ["SN002", "1", "3.0"],
        ], tmp_path / "test.csv")
        ft = FTData(str(csv_path), str(tmp_cfg))
        assert len(ft.raw_df) == 5  # 3 meta + 2 data (header row excluded from raw_df)
        assert len(ft.data) == 2   # data = raw_df[3:]
        assert "PART_ID" in ft.data.columns

    def test_test_columns(self, tmp_path, tmp_cfg):
        """test_columns should exclude META_COLUMNS."""
        csv_path = make_csv([
            ["PART_ID", "SOFT_BIN", "DC_T1", "DC_T2"],
            ["Unit", "", "V", "V"],
            ["Lower", "", "0", "0"],
            ["Higher", "", "5", "5"],
            ["SN001", "1", "1.0", "2.0"],
        ], tmp_path / "test.csv")
        ft = FTData(str(csv_path), str(tmp_cfg))
        assert "DC_T1" in ft.test_columns
        assert "DC_T2" in ft.test_columns
        assert "PART_ID" not in ft.test_columns
        assert "SOFT_BIN" not in ft.test_columns


# ═══════════════════════════════════════════════════════════════════
#  Split header (part_id row != data_col_header row)
# ═══════════════════════════════════════════════════════════════════


class TestSplitHeader:

    def test_split_header(self, tmp_path):
        """PART_ID on row 0, test headers on row 1."""
        cfg = tmp_path / "cfg.toml"
        cfg.write_text("""
[[signatures]]
format_id = "SPLIT"
header_identifiers = ["PART_ID", "SOFT_BIN"]
part_id_offset = 0
data_col_header_offset = 1
unit_offset = 2
lower_limit_offset = 3
higher_limit_offset = 4
data_start_offset = 5
pre_test_columns = ["SOFT_BIN"]
delimiter = ","
skip_row_values = {}
""")
        csv_path = make_csv([
            ["PART_ID", "SOFT_BIN", "", ""],
            ["", "", "DC_IGSS_T1", "DC_IDSS_T2"],
            ["V", "", "uA", "V"],
            ["0", "1", "0", "0.5"],
            ["10", "10", "100", "50"],
            ["DIE001", "1", "0.5", "100.2"],
        ], tmp_path / "test.csv")
        ft = FTData(str(csv_path), str(cfg))
        assert ft.test_columns == ["DC_IGSS_T1", "DC_IDSS_T2"]
        assert len(ft.data) == 1
        # uA → A conversion
        assert ft.data["DC_IGSS_T1"].iloc[0] == pytest.approx(5e-7, rel=1e-12)


# ═══════════════════════════════════════════════════════════════════
#  Empty / edge cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:

    def test_empty_data_no_error(self, tmp_path, tmp_cfg):
        """Empty file raises error."""
        csv_path = make_csv([], tmp_path / "test.csv")
        with pytest.raises(Exception):
            FTData(str(csv_path), str(tmp_cfg))

    def test_single_data_row(self, tmp_path, tmp_cfg):
        """Single data row is fine."""
        csv_path = make_csv([
            ["PART_ID", "SOFT_BIN", "DC_T1"],
            ["Unit", "", "V"],
            ["Lower", "", "0"],
            ["Higher", "", "5"],
            ["SN001", "1", "2.5"],
        ], tmp_path / "test.csv")
        ft = FTData(str(csv_path), str(tmp_cfg))
        assert len(ft.data) == 1
        assert ft.data["DC_T1"].iloc[0] == pytest.approx(2.5)

    def test_no_meta_rows(self, tmp_path):
        """File without Unit/LL/HL rows."""
        cfg = tmp_path / "cfg.toml"
        cfg.write_text("""
[[signatures]]
format_id = "NO_META"
header_identifiers = ["PART_ID", "SOFT_BIN"]
data_start_offset = 1
pre_test_columns = []
delimiter = ","
skip_row_values = {}
""")
        csv_path = make_csv([
            ["PART_ID", "SOFT_BIN", "DC_T1"],
            ["SN001", "1", "2.5"],
            ["SN002", "1", "3.0"],
        ], tmp_path / "test.csv")
        ft = FTData(str(csv_path), str(cfg))
        assert len(ft.data) == 2
        assert ft.units == {}  # no units
