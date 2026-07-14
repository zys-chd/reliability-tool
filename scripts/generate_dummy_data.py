"""Generate dummy FT/CSV data files for testing.

Supports various format scenarios:
- Standard 4-row header (PART_ID/SOFT_BIN/test columns)
- Different units per column (uA, mA, V, kV, °F, etc.)
- Blank rows between meta and data
- Entirely empty columns in data
- Junk rows before the real header
- Split header (part_id on different row from test headers)
- SITE_NUM as header marker
- Short files (< 50 lines)
- Epson-style format (1-row header, no meta)
- TSV format
"""
import csv
import os
from pathlib import Path


def write_csv(path: Path, rows: list[list], delimiter: str = ",",
              encoding: str = "utf-8"):
    """Write a CSV file with the given rows."""
    with open(path, "w", newline="", encoding=encoding) as f:
        writer = csv.writer(f, delimiter=delimiter)
        for r in rows:
            writer.writerow(r)
    return path


# ═══════════════════════════════════════════════════════════════════
#  Standard format variants
# ═══════════════════════════════════════════════════════════════════


def standard_4row(outdir: Path, name: str = "standard.csv"):
    """Standard 4-row header CSV with V and A units."""
    rows = [
        ["PART_ID", "SOFT_BIN", "DC_IGSS_1", "DC_BV_1", "DC_IDSS_T1"],
        ["Unit", "", "uA", "V", "A"],
        ["Lower Limit", "", "0", "0.5", "0"],
        ["Higher Limit", "", "100", "3.3", "0.001"],
        ["SN001", "1", "1.23e-05", "3.45e+00", "2.1e-05"],
        ["SN002", "2", "2.34e-05", "4.56e+00", "3.2e-05"],
        ["SN003", "1", "3.45e-05", "5.67e+00", "4.3e-05"],
    ]
    return write_csv(outdir / name, rows)


def with_mixed_units(outdir: Path, name: str = "mixed_units.csv"):
    """Test columns with different SI prefixes needing conversion."""
    rows = [
        ["PART_ID", "SOFT_BIN", "DC_IGSS_1", "DC_BV_1", "DC_RDSON_T1", "DC_TEMP_T1"],
        ["Unit", "", "uA", "kV", "mOhm", "°F"],
        ["Lower Limit", "", "0", "0", "0", "32"],
        ["Higher Limit", "", "100", "10", "100", "212"],
        ["DIE001", "1", "50", "5.0", "50", "212"],       # 50uA, 5kV, 50mOhm, 212°F
        ["DIE002", "1", "100", "3.3", "75", "100"],       # 100uA, 3.3kV, 75mOhm, 100°F
        ["DIE003", "2", "25", "1.0", "25", "32"],         # 25uA, 1kV, 25mOhm, 32°F
    ]
    return write_csv(outdir / name, rows)


# ═══════════════════════════════════════════════════════════════════
#  Blank rows between meta and data
# ═══════════════════════════════════════════════════════════════════


def with_blank_rows_after_meta(outdir: Path, name: str = "blanks_after_meta.csv",
                                n_blanks: int = 3):
    """Blank rows between the last meta row and the first data row."""
    rows = [
        ["PART_ID", "SOFT_BIN", "DC_T1", "DC_T2"],
        ["Unit", "", "V", "V"],
        ["Lower Limit", "", "0", "0"],
        ["Higher Limit", "", "5", "5"],
    ]
    for _ in range(n_blanks):
        rows.append([])
    rows.append(["DIE001", "1", "2.5", "3.0"])
    rows.append(["DIE002", "1", "3.0", "4.0"])
    rows.append(["DIE003", "2", "1.5", "2.0"])
    return write_csv(outdir / name, rows)


def with_blank_rows_interleaved(outdir: Path, name: str = "blanks_interleaved.csv"):
    """Blank rows interleaved between meta rows."""
    rows = [
        ["Lot:", "LOT-001"],
        [],
        ["PART_ID", "SOFT_BIN", "DC_T1"],
        [],
        ["Unit", "", "V"],
        ["Lower Limit", "", "0"],
        [],
        ["Higher Limit", "", "5"],
        [],
        ["DIE001", "1", "2.5"],
        ["DIE002", "1", "3.0"],
        ["DIE003", "2", "4.0"],
    ]
    return write_csv(outdir / name, rows)


# ═══════════════════════════════════════════════════════════════════
#  Empty columns in data
# ═══════════════════════════════════════════════════════════════════


def with_empty_column(outdir: Path, name: str = "empty_column.csv"):
    """A column that has ALL empty values in data rows."""
    rows = [
        ["PART_ID", "SOFT_BIN", "DC_T1", "DC_T2_EMPTY", "DC_T3"],
        ["Unit", "", "V", "V", "A"],
        ["Lower Limit", "", "0", "0", "0"],
        ["Higher Limit", "", "5", "5", "0.001"],
        ["DIE001", "1", "2.5", "", "1.2e-05"],          # DC_T2_EMPTY empty
        ["DIE002", "1", "3.0", "", "2.3e-05"],
        ["DIE003", "2", "1.5", "", "3.4e-05"],
    ]
    return write_csv(outdir / name, rows)


def with_no_trailing_commas(outdir: Path, name: str = "no_trailing_commas.csv"):
    """Last column entirely missing from data rows (no trailing commas)."""
    lines = [
        "PART_ID,SOFT_BIN,DC_T1,DC_T2",
        "Unit,,V,V",
        "Lower,,0,0",
        "Higher,,5,5",
        "DIE001,1,2.5",       # no DC_T2 value, no trailing comma
        "DIE002,1,3.0",
        "DIE003,2,1.5",
    ]
    p = outdir / name
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def with_middle_empty_column(outdir: Path, name: str = "middle_empty.csv"):
    """Middle column entirely empty (commas present but no data)."""
    lines = [
        "PART_ID,SOFT_BIN,DC_T1,DC_T2_EMPTY,DC_T3",
        "Unit,,V,V,V",
        "Lower,,0,0,0",
        "Higher,,5,5,5",
        "DIE001,1,2.5,,3.5",
        "DIE002,1,3.0,,4.0",
        "DIE003,2,1.5,,2.5",
    ]
    p = outdir / name
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


# ═══════════════════════════════════════════════════════════════════
#  Junk rows before header
# ═══════════════════════════════════════════════════════════════════


def with_junk_before_header(outdir: Path, n_junk: int = 200,
                             name: str | None = None):
    """Many junk rows before the real header."""
    if name is None:
        name = f"junk_{n_junk}_rows.csv"
    rows = []
    for i in range(n_junk):
        rows.append([f"junk_{i}", "xxx", "0", "0", "0"])
    rows.append(["PART_ID", "SOFT_BIN", "DC_IGSS_1", "DC_BV_1", "DC_IDSS_T1"])
    rows.append(["Unit", "", "uA", "V", "A"])
    rows.append(["Lower Limit", "", "0", "0.5", "0"])
    rows.append(["Higher Limit", "", "100", "3.3", "0.001"])
    rows.append(["SN001", "1", "0.5", "2.5", "1.23e-05"])
    rows.append(["SN002", "1", "0.6", "2.6", "2.34e-05"])
    return write_csv(outdir / name, rows)


# ═══════════════════════════════════════════════════════════════════
#  Split header (PART_ID on different row from test item headers)
# ═══════════════════════════════════════════════════════════════════


def split_header(outdir: Path, name: str = "split_header.csv"):
    """PART_ID/SOFT_BIN on row 0, test column headers on row 1."""
    rows = [
        ["PART_ID", "SOFT_BIN", "", ""],
        ["", "", "DC_IGSS_T1", "DC_IDSS_T2"],
        ["V", "", "uA", "V"],
        ["0", "1", "0", "0.5"],
        ["10", "10", "100", "50"],
        ["DIE001", "1", "0.5", "100.2"],
        ["DIE002", "1", "0.6", "200.3"],
        ["DIE003", "2", "0.7", "300.4"],
    ]
    return write_csv(outdir / name, rows)


# ═══════════════════════════════════════════════════════════════════
#  SITE_NUM as header marker
# ═══════════════════════════════════════════════════════════════════


def with_site_num_header(outdir: Path, name: str = "site_num.csv"):
    """Header starts with SITE_NUM column."""
    rows = [
        ["System:", "Tester-1"],
        ["Date:", "2024-06-15"],
        ["Operator:", "John"],
        ["", ""],
        ["SITE_NUM", "PART_ID", "SOFT_BIN", "DC_IGSS_1", "DC_BV_1"],
        ["Unit", "", "", "uA", "V"],
        ["Lower", "", "", "0", "0.5"],
        ["Higher", "", "", "100", "3.3"],
        ["1", "SN001", "1", "0.5", "2.5"],
        ["2", "SN002", "1", "0.6", "2.6"],
        ["1", "SN003", "2", "0.7", "2.7"],
    ]
    return write_csv(outdir / name, rows)


# ═══════════════════════════════════════════════════════════════════
#  Epson-style format (1-row header, no meta rows)
# ═══════════════════════════════════════════════════════════════════


def epson_format(outdir: Path, name: str = "epson_format.csv"):
    """Epson FT format: single-row header, no meta rows."""
    rows = [
        ["Device", "Site", "Bin_No", "Test_Item", "Value"],
        ["DIE001", "1", "1", "IGSS_1", "0.5"],
        ["DIE001", "1", "1", "BV_1", "2.5"],
        ["DIE002", "1", "1", "IGSS_1", "0.6"],
        ["DIE002", "1", "1", "BV_1", "2.6"],
        ["DIE003", "2", "2", "IGSS_1", "0.7"],
    ]
    return write_csv(outdir / name, rows)


# ═══════════════════════════════════════════════════════════════════
#  Short file (< 50 lines, no junk)
# ═══════════════════════════════════════════════════════════════════


def short_file(outdir: Path, name: str = "short.csv"):
    """Very short file with only header + 1 data row."""
    rows = [
        ["PART_ID", "SOFT_BIN", "DC_T1"],
        ["SN001", "1", "2.5"],
    ]
    return write_csv(outdir / name, rows)


# ═══════════════════════════════════════════════════════════════════
#  TSV format
# ═══════════════════════════════════════════════════════════════════


def tsv_format(outdir: Path, name: str = "data.tsv"):
    """Tab-separated file with 4-row header."""
    rows = [
        ["PART_ID", "SOFT_BIN", "DC_T1", "DC_T2"],
        ["Unit", "", "V", "mA"],
        ["Lower", "", "0", "0"],
        ["Higher", "", "5", "100"],
        ["DIE001", "1", "2.5", "50"],
        ["DIE002", "1", "3.0", "75"],
        ["DIE003", "2", "1.5", "25"],
    ]
    return write_csv(outdir / name, rows, delimiter="\t")


# ═══════════════════════════════════════════════════════════════════
#  All generators in one call
# ═══════════════════════════════════════════════════════════════════


def generate_all(outdir: str | Path = "dummy_data") -> list[Path]:
    """Generate all dummy data files, return list of created paths."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    generators = [
        ("standard_4row", standard_4row),
        ("with_mixed_units", lambda d: with_mixed_units(d)),
        ("with_blank_rows_after_meta", lambda d: with_blank_rows_after_meta(d)),
        ("with_blank_rows_interleaved", lambda d: with_blank_rows_interleaved(d)),
        ("with_empty_column", lambda d: with_empty_column(d)),
        ("with_no_trailing_commas", lambda d: with_no_trailing_commas(d)),
        ("with_middle_empty_column", lambda d: with_middle_empty_column(d)),
        ("with_junk_before_header", lambda d: with_junk_before_header(d, n_junk=200)),
        ("with_junk_50_before_header", lambda d: with_junk_before_header(d, n_junk=50, name="junk_50_rows.csv")),
        ("split_header", lambda d: split_header(d)),
        ("with_site_num_header", lambda d: with_site_num_header(d)),
        ("epson_format", lambda d: epson_format(d)),
        ("short_file", lambda d: short_file(d)),
        ("tsv_format", lambda d: tsv_format(d)),
    ]

    created = []
    for label, gen in generators:
        p = gen(outdir)
        created.append(p)
        print(f"  ✓ {p.name} ({p.stat().st_size:>6} bytes)")

    return created


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "dummy_data"
    print(f"Generating dummy data files in '{out}/' ...")
    files = generate_all(out)
    print(f"\nDone: {len(files)} files generated.")
