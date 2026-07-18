"""Generate large dummy FT data files with realistic column names.

生成两种格式（STS8200_FT 标准 和 STS8200_FT_REV 反向），随机混合。
- STS8200_FT: 测试列名行在上，meta 行（PART_ID等）在下（标准格式）
- STS8200_FT_REV: 测试列名行在上，meta 行（SITE_NUM,SN等）在最下面（反向格式）

Column format: DC_{seq:04d}_{test_item}_{condition}
  e.g. DC_0001_IDSS_100V_T11, DC_0002_BV_30V_T25

~500 columns × 1000 data rows per file.
25 T0 + 25 TX files, randomly assigned to either format.
"""
import csv
import random
import sys
import time
from pathlib import Path

RNG = random.Random(42)

# ── Test item types ──────────────────────────────────────────────
# 使用真实 CSV 中的常用单位，FTData 会自动转换为 SI
TEST_ITEMS = [
    ("IDSS",   "A",   0,     0.001, "uA"),
    ("IGSS",   "A",   0,     0.001, "nA"),
    ("BV",     "V",   30,    100,   "V"),
    ("VTH",    "V",   0.5,   5.0,   "V"),
    ("RDSON",  "Ω",   0,     10,    "mOhm"),
    ("VF",     "V",   0.3,   2.0,   "V"),
    ("Delta",  "V",   -0.5,  0.5,   "mV"),
]

CONDITIONS = ["30V", "50V", "100V", "150V", "20V", "60V", "200V", "250V"]
TEMPS = ["T11", "T25", "T150", "T85", "T125", "T175"]

# ── Meta columns ─────────────────────────────────────────────────
# Standard format uses "PART_ID"; REV format uses "SN" (mapped via column_map)
META_COLS = ["SITE_NUM", "PART_ID", "PASSFG", "SOFT_BIN",
             "T_TIME", "X_COORD", "Y_COORD", "TEST_NUM"]
META_COLS_REV = ["SITE_NUM", "SN", "PASSFG", "SOFT_BIN",
                 "T_TIME", "X_COORD", "Y_COORD", "TEST_NUM"]

STS8200_JUNK = [
    ["STS8202 StationA"],
    ["Date:2024-5-21"],
    ["Tester ID:"],
    ["User:admin"],
    ["Program:D:\\ONLINE-TEST\\PMTR04021\\PMTR04021\\PMTR04021-OLD.pgs"],
    ["Handler: UF200.dll"],
    ["Site: All Sites"],
    ["Lot Id:P3AP04"],
    ["WAFER_ID:P3AP04-23"],
    [""],
    ["Average Test Time(ms): 377"],
    ["Idle Time: 0 day 0:3:21"],
    ["Beginning Time: 2024-5-21 16:01:48"],
    ["Ending Time: 2024-5-21 16:08:01"],
    ["Total Testing Time: 0 day 0:2:51"],
    [""],
    ["Total: 3484"],
    ["Pass: 2393   68.69%"],
    ["Fail: 1091   31.31%"],
]


def _make_bin_summaries():
    """Generate SOFT_BIN summary lines like the STS8200 template."""
    bin_names = [
        (1,  "Pass__Default"),
        (2,  "Fail__Default"),
        (6,  "Kelvin__AllFail"),
        (8,  "IGSSF5V__AllFail"),
        (9,  "IGSSR-5V__AllFail"),
        (10, "IDSS__AllFail"),
        (11, "IGSSF20V__AllFail"),
        (12, "IGSSR-20V__AllFail"),
        (13, "BV250uA__AllFail"),
        (14, "BV1mA__AllFail"),
        (15, "Delta__AllFail"),
        (16, "IDSS50V__AllFail"),
        (17, "IDSS60V__AllFail"),
        (18, "VTH250uA__AllFail"),
        (19, "RDSON__AllFail"),
        (20, "RDSON1__AllFail"),
        (21, "VF1A__AllFail"),
    ]
    total = 3484
    pass_count = 2393
    fail_count = total - pass_count
    lines = []
    lines.append([f"Total: {total}"])
    lines.append([f"Pass: {pass_count}   {pass_count/total*100:.2f}%"])
    lines.append([f"Fail: {fail_count}   {fail_count/total*100:.2f}%"])
    cumulative = 0
    for bin_num, bin_name in bin_names:
        count = RNG.randint(0, 200)
        if bin_num == 1:
            count = pass_count - cumulative
        cumulative += count
        pct = count / total * 100
        lines.append([f"SBin[{bin_num}]   {bin_name:30s} {count:>5}   {pct:.2f}%   {RNG.randint(1,5)}"])
    lines.append([""])
    return lines


def _make_column_names(n_total: int, rev: bool = False) -> list[str]:
    """Generate realistic column names.
    
    If rev=True, uses SN instead of PART_ID for the meta columns.
    """
    meta = META_COLS_REV if rev else META_COLS
    test = []
    n_test = n_total - len(meta)
    seq = 0
    while len(test) < n_test:
        for item_name, unit, lo, hi, display_unit in TEST_ITEMS:
            for cond in CONDITIONS:
                for temp in TEMPS:
                    if len(test) >= n_test:
                        break
                    seq += 1
                    col = f"DC_{seq:04d}_{item_name}_{cond}_{temp}"
                    test.append(col)
    return meta + test[:n_test]


def _get_meta_set(rev: bool = False) -> set[str]:
    return set(META_COLS_REV if rev else META_COLS)


def _make_unit_row(cols: list[str], rev: bool = False) -> list[str]:
    """Unit row: meta cols empty, test cols have realistic units."""
    meta_set = _get_meta_set(rev)
    result = []
    for c in cols:
        if c in meta_set:
            if c == "T_TIME":
                result.append("ms")
            else:
                result.append("")
        else:
            # Extract test item name from column name
            parts = c.split("_")
            if len(parts) >= 3:
                item = parts[2]
                for name, unit, lo, hi, display_unit in TEST_ITEMS:
                    if item == name:
                        result.append(display_unit)
                        break
                else:
                    result.append(RNG.choice(["V", "A", "Ohm"]))
            else:
                result.append("")
    return result


def _make_limit_row(cols: list[str], lower: bool, rev: bool = False) -> list[str]:
    """Lower/upper limit row — 每个测试类型统一 limit。"""
    meta_set = _get_meta_set(rev)
    result = []
    label = "LimitL" if lower else "LimitU"
    for c in cols:
        if c in meta_set:
            if c == "SITE_NUM":
                result.append(label)
            else:
                result.append("")
        else:
            parts = c.split("_")
            if len(parts) >= 3:
                item = parts[2]
                for name, unit, lo, hi, display_unit in TEST_ITEMS:
                    if item == name:
                        if lower:
                            result.append(f"{lo:.4f}")
                        else:
                            result.append(f"{hi:.4f}")
                        break
                else:
                    result.append("0.0000" if lower else "100.0000")
            else:
                result.append("")
    return result


def _make_data_value(col: str, row_idx: int, seed: int, rev: bool = False,
                     outlier_factor: float | None = None) -> str:
    """Generate realistic data value.

    If outlier_factor is set (e.g., 3.0), some test measurements are multiplied
    to create over-limit shifts in the comparison output.
    """
    local = random.Random(seed + row_idx)

    # Resolve column name for data generation logic
    col_key = col
    if rev and col == "SN":
        col_key = "PART_ID"

    if col_key == "SITE_NUM":
        return str(local.randint(1, 8))
    elif col_key == "PART_ID":
        return str(local.randint(1, 3000))
    elif col_key == "PASSFG":
        return "True" if local.random() > 0.25 else "False"
    elif col_key == "SOFT_BIN":
        r = local.random()
        if r < 0.70:
            return "1"
        elif r < 0.85:
            return str(local.choice([8, 9, 10, 11, 12, 13, 14, 15]))
        else:
            return str(local.choice([6, 16, 17, 18, 19, 20, 21]))
    elif col_key == "T_TIME":
        return f"{local.uniform(350, 450):.1f}"
    elif col_key in ("X_COORD",):
        return str(local.randint(100, 200))
    elif col_key == "Y_COORD":
        return str(local.randint(100, 200))
    elif col_key == "TEST_NUM":
        return str(local.randint(1, 20))
    elif col.startswith("DC_"):
        parts = col.split("_")
        if len(parts) >= 3:
            item = parts[2]
            for name, unit, lo, hi, display_unit in TEST_ITEMS:
                if item == name:
                    if unit == "A":
                        val = local.lognormvariate(-10, 2)
                    elif unit == "V":
                        val = local.uniform(lo * 0.8, hi * 1.2)
                    elif unit == "Ω":
                        val = local.uniform(0, hi * 0.9)
                    # Apply outlier factor to create over-limit shifts
                    if outlier_factor is not None:
                        val = val * outlier_factor
                    return f"{val:.6e}" if unit == "A" else f"{val:.4f}"
            val = local.uniform(0, 100)
            if outlier_factor is not None:
                val = val * outlier_factor
            return f"{val:.4f}"
    return ""


# ── File format generators ──────────────────────────────────────

def _generate_standard(path: Path, cols: list[str], n_data_rows: int,
                       seed_offset: int, deg_ratio: float = 0.0,
                       deg_factor: float = 3.0):
    """Write in STS8200_FT standard format: header first, then data."""
    meta_set = _get_meta_set(rev=False)
    n_meta = len(META_COLS)

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)

        # Junk lines
        for row in STS8200_JUNK:
            w.writerow(row)

        # Bin summaries
        for row in _make_bin_summaries():
            w.writerow(row)

        # Header: meta + test columns
        w.writerow(cols)
        w.writerow(_make_unit_row(cols, rev=False))
        w.writerow(_make_limit_row(cols, lower=True, rev=False))
        w.writerow(_make_limit_row(cols, lower=False, rev=False))
        w.writerow([])  # blank separator

        # Data
        for i in range(n_data_rows):
            of = deg_factor if random.Random(seed_offset + i).random() < deg_ratio else None
            row = [_make_data_value(c, i, seed_offset, rev=False, outlier_factor=of) for c in cols]
            w.writerow(row)


def _generate_rev(path: Path, cols: list[str], n_data_rows: int,
                  seed_offset: int, deg_ratio: float = 0.0,
                  deg_factor: float = 3.0):
    """Write in STS8200_FT_REV format: test header first, meta header last.
    
    File layout (like excample2.csv):
      Row -4: data_col_header (test column names, empty meta cols)
      Row -3: unit row
      Row -2: LimitL row
      Row -1: LimitU row
      Row  0: meta header row (SITE_NUM, SN, PASSFG, ...)
      Row  1+: data rows
    """
    n_meta = len(META_COLS_REV)
    meta_cols = cols[:n_meta]
    test_cols = cols[n_meta:]

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)

        # Row -4: data_col_header (test column names, empty meta cols)
        dch_row = [""] * n_meta + test_cols
        w.writerow(dch_row)

        # Row -3: Unit row（复用 _make_unit_row）
        w.writerow(_make_unit_row(cols, rev=True))

        # Row -2: LimitL row（复用 _make_limit_row）
        w.writerow(_make_limit_row(cols, lower=True, rev=True))

        # Row -1: LimitU row（复用 _make_limit_row）
        w.writerow(_make_limit_row(cols, lower=False, rev=True))

        # Row 0: Meta header row (SITE_NUM, SN, PASSFG, SOFT_BIN, ...)
        meta_row = meta_cols + [""] * len(test_cols)
        w.writerow(meta_row)

        # Data rows
        for i in range(n_data_rows):
            of = deg_factor if random.Random(seed_offset + i).random() < deg_ratio else None
            row = [_make_data_value(c, i, seed_offset, rev=True, outlier_factor=of) for c in cols]
            w.writerow(row)


# ── Public API ──────────────────────────────────────────────────

def generate_one_file(path: Path, n_total_cols: int = 500,
                      n_data_rows: int = 1000, seed_offset: int = 0,
                      rev: bool = False, deg_ratio: float = 0.0,
                      deg_factor: float = 3.0):
    """Generate one FT data file.

    Args:
        path: Output path.
        n_total_cols: Total columns (meta + test).
        n_data_rows: Number of data rows.
        seed_offset: Seed offset for reproducibility.
        rev: True for STS8200_FT_REV format, False for STS8200_FT standard.
        deg_ratio: Ratio of rows to degrade (create over-limit shifts). 0.0 = none.
        deg_factor: Multiplier for degraded test values.
    """
    cols = _make_column_names(n_total_cols, rev=rev)

    if rev:
        _generate_rev(path, cols, n_data_rows, seed_offset, deg_ratio, deg_factor)
    else:
        _generate_standard(path, cols, n_data_rows, seed_offset, deg_ratio, deg_factor)

    return path


def generate_batch(outdir: str | Path, n_per_group: int = 25,
                   n_cols: int = 500, n_rows: int = 1000,
                   rev_ratio: float = 0.5, deg_ratio: float = 0.1,
                   deg_factor: float = 3.0):
    """Generate T0 and TX file batches, randomly mixed format.

    Args:
        outdir: Output directory.
        n_per_group: Number of files per group (T0, TX).
        n_cols: Columns per file.
        n_rows: Data rows per file.
        rev_ratio: Probability of generating STS8200_FT_REV format (0.0-1.0).
        deg_ratio: Ratio of TX rows to degrade (outlier test values). T0 never degraded.
        deg_factor: Multiplier for degraded test values.
    """
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    created = []

    def _should_rev(index: int) -> bool:
        """Deterministic random assignment based on index."""
        return random.Random(index).random() < rev_ratio

    print(f"Generating {n_per_group} T0 files (rev_ratio={rev_ratio})...")
    t0_rev = 0
    for i in range(n_per_group):
        rev = _should_rev(i)
        if rev:
            t0_rev += 1
        name = f"T0_batch_{i+1:03d}.csv"
        # T0 文件不生成 outlier
        p = generate_one_file(outdir / name, n_cols, n_rows, i * 1000, rev=rev)
        created.append(p)
        if (i + 1) % 5 == 0:
            print(f"  ... {i+1}/{n_per_group} (rev: {t0_rev})")

    print(f"Generating {n_per_group} TX files (rev_ratio={rev_ratio}, deg_ratio={deg_ratio})...")
    tx_off = n_per_group * 1000 + 9999
    tx_rev = 0
    for i in range(n_per_group):
        rev = _should_rev(tx_off + i)
        if rev:
            tx_rev += 1
        name = f"TX_batch_{i+1:03d}.csv"
        # TX 文件生成少量 outlier 以便验证超限格式
        p = generate_one_file(outdir / name, n_cols, n_rows, tx_off + i,
                              rev=rev, deg_ratio=deg_ratio, deg_factor=deg_factor)
        created.append(p)
        if (i + 1) % 5 == 0:
            print(f"  ... {i+1}/{n_per_group} (rev: {tx_rev})")

    return created


def main(outdir: str = "benchmark_data", n_t0: int = 25,
         n_tx: int = 25, n_cols: int = 500, n_rows: int = 1000,
         rev_ratio: float = 0.5):
    start = time.time()
    files = generate_batch(outdir, n_t0, n_cols, n_rows, rev_ratio)
    elapsed = time.time() - start
    total_mb = sum(p.stat().st_size for p in files) / (1024 * 1024)

    rev_count = sum(1 for f in files if "_rev" in str(f.stem) or False)
    # Count rev files by checking the content
    rev_count = 0
    for f in files:
        txt = f.read_text(encoding="utf-8-sig")
        if "SN," in txt.splitlines()[-3]:  # meta header row has SN instead of PART_ID
            rev_count += 1

    print(f"\n{'='*55}")
    print(f"  T0: {n_t0} files, TX: {n_tx} files")
    print(f"  Columns: {n_cols} total (8 meta + {n_cols-8} test)")
    print(f"  Data rows per file: {n_rows}")
    print(f"  REV ratio: {rev_ratio:.0%} ({rev_count}/{len(files)} files)")
    print(f"  Total: {len(files)} files, {total_mb:.0f} MB")
    print(f"  Generated in {elapsed:.1f}s")
    return files


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "benchmark_data"
    rev_ratio = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
    main(out, rev_ratio=rev_ratio)
