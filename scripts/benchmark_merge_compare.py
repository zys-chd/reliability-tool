"""Benchmark merge + compare pipeline — find speed bottlenecks."""
import sys
import time
import gc
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.FT_file_parser import FTData
from core.data_merge import merge_t0_tx, _merge_group_rows
from core.compare import transform_rename, calc_shifts, export_excel, read_raw_headers_from_file
import pandas as pd

DATA_DIR = PROJECT_ROOT / "benchmark_merge_test"
CFG = str(PROJECT_ROOT / "config" / "ft_data_config.toml")


def fmt(s: float) -> str:
    if s < 0.001: return f"{s*1e6:.0f}µs"
    elif s < 1: return f"{s*1e3:.1f}ms"
    else: return f"{s:.2f}s"


def find_files(data_dir: str | Path) -> tuple[list[str], list[str]]:
    d = Path(data_dir)
    t0 = sorted(str(p) for p in d.glob("T0_*.csv"))
    tx = sorted(str(p) for p in d.glob("TX_*.csv"))
    return t0, tx


def benchmark_pipeline(t0_paths, tx_paths):
    print(f"\n{'='*60}")
    n_t0, n_tx = len(t0_paths), len(tx_paths)
    print(f"  Merge + Compare Pipeline Benchmark")
    print(f"  T0: {n_t0} files, TX: {n_tx} files")

    # ── 1. File reading (the dominant cost) ──
    print(f"\n── 1. 文件读取 ──")
    gc.collect()
    t0 = time.perf_counter()
    all_rows = []
    for i, p in enumerate(t0_paths):
        ft = FTData(p, CFG)
        df = ft.data.copy()
        df["group"] = "T0"
        df["filepath"] = str(Path(p).name)
        all_rows.append(df)
    t_read_t0 = time.perf_counter() - t0
    print(f"  T0 读取 ({n_t0})    : {fmt(t_read_t0)}  (平均 {fmt(t_read_t0/n_t0)})")

    gc.collect()
    t0 = time.perf_counter()
    for i, p in enumerate(tx_paths):
        ft = FTData(p, CFG)
        df = ft.data.copy()
        df["group"] = Path(p).stem
        df["filepath"] = str(Path(p).name)
        all_rows.append(df)
    t_read_tx = time.perf_counter() - t0
    print(f"  TX 读取 ({n_tx})    : {fmt(t_read_tx)}  (平均 {fmt(t_read_tx/n_tx)})")

    gc.collect()
    t0 = time.perf_counter()
    big_table = pd.concat(all_rows, ignore_index=True)
    t_concat = time.perf_counter() - t0
    print(f"  concat            : {fmt(t_concat)}")
    print(f"  合并表: {len(big_table)} rows × {len(big_table.columns)} cols")
    t_read_total = t_read_t0 + t_read_tx + t_concat
    print(f"  读取总耗时: {fmt(t_read_total)}")

    # ── 2. GroupBy + 组内合并 ──
    print(f"\n── 2. GroupBy + 组内合并 ──")
    gc.collect()
    t0 = time.perf_counter()
    merged_rows = []
    conflict_ct = 0
    groups = list(big_table.groupby(["PART_ID", "group"], sort=False))
    for (pid, grp), group_df in groups:
        if len(group_df) == 1:
            merged_rows.append(group_df.iloc[0].to_dict())
        else:
            pass_mask = group_df["SOFT_BIN"].apply(lambda x: str(int(x)) == "1")
            if pass_mask.any():
                merged_rows.append(group_df[pass_mask].iloc[0].to_dict())
            else:
                merged, has_c = _merge_group_rows(group_df)
                merged_rows.append(merged)
                if has_c:
                    conflict_ct += 1
    merged_df = pd.DataFrame(merged_rows)
    t_group = time.perf_counter() - t0
    print(f"  groupby 合并     : {fmt(t_group)}  ({len(merged_rows)} groups)")
    print(f"  冲突组数        : {conflict_ct}")
    print(f"  合并后: {len(merged_df)} rows × {len(merged_df.columns)} cols")

    # ── 3. transform_rename ──
    print(f"\n── 3. transform_rename ──")
    # Build calc_config with all test columns
    test_cols = [c for c in merged_df.columns if c.startswith("DC_")]
    calc_config = {
        "renames": {},
        "suffixes": {},
        "formulas": {c: "TX - T0" for c in test_cols},
        "limits": {c: "10" for c in test_cols},
        "directions": {c: "upper" for c in test_cols},
    }
    gc.collect()
    t0 = time.perf_counter()
    renamed = transform_rename(merged_df, calc_config)
    t_rename = time.perf_counter() - t0
    print(f"  transform_rename : {fmt(t_rename)}")
    print(f"  → {len(renamed)} rows × {len(renamed.columns)} cols")

    # ── 4. calc_shifts ──
    print(f"\n── 4. calc_shifts ──")
    gc.collect()
    t0 = time.perf_counter()
    shifts = calc_shifts(renamed, calc_config)
    t_shifts = time.perf_counter() - t0
    print(f"  calc_shifts      : {fmt(t_shifts)}")
    print(f"  → {len(shifts)} rows")

    # ── 5. export_excel ──
    print(f"\n── 5. export_excel ──")
    gc.collect()
    t0 = time.perf_counter()
    raw_hdrs = {}
    for p in t0_paths:
        h = read_raw_headers_from_file(p)
        if len(h) > len(raw_hdrs):
            raw_hdrs = h
    outpath = str(PROJECT_ROOT / "benchmark_merge_test" / "result.xlsx")
    export_excel(shifts, calc_config, raw_headers=raw_hdrs, output_path=outpath)
    t_excel = time.perf_counter() - t0
    print(f"  export_excel     : {fmt(t_excel)}")

    # ── Summary ──
    total = t_read_total + t_group + t_rename + t_shifts + t_excel
    print(f"\n{'='*60}")
    print(f"  {'Phase':30s} {'Time':>10s} {'%':>6s}")
    print(f"  {'─'*48}")
    phases = [
        ("1. 文件读取", t_read_total),
        ("2. GroupBy合并", t_group),
        ("3. transform_rename", t_rename),
        ("4. calc_shifts", t_shifts),
        ("5. export_excel", t_excel),
    ]
    for name, t in phases:
        pct = t / total * 100 if total > 0 else 0
        bar = "█" * int(pct / 4)
        print(f"  {name:30s} {fmt(t):>10s} {pct:6.1f}%  {bar}")
    print(f"  {'─'*48}")
    print(f"  {'TOTAL':30s} {fmt(total):>10s}")
    print(f"{'='*60}")

    # ── Deeper dive into bottlenecks ──
    print(f"\n── 瓶颈深入分析 ──")
    print(f"  文件读取占总耗时 {t_read_total/total*100:.1f}%")
    if t_read_total / total > 0.3:
        # Show per-file variation
        all_files = t0_paths + tx_paths
        gc.collect()
        times = []
        for p in all_files:
            t0 = time.perf_counter()
            ft = FTData(p, CFG)
            _ = ft.data
            times.append(time.perf_counter() - t0)
        avg_read = sum(times) / len(times)
        # Separate standard vs rev
        std_times, rev_times = [], []
        for p, t in zip(all_files, times):
            txt = Path(p).read_text(encoding="utf-8-sig")
            if "SN," in txt.splitlines()[4] if len(txt.splitlines()) > 4 else "":
                rev_times.append(t)
            else:
                std_times.append(t)
        if std_times:
            print(f"  标准格式: avg={fmt(sum(std_times)/len(std_times))}  "
                  f"min={fmt(min(std_times))} max={fmt(max(std_times))}")
        if rev_times:
            print(f"  REV格式:  avg={fmt(sum(rev_times)/len(rev_times))}  "
                  f"min={fmt(min(rev_times))} max={fmt(max(rev_times))}")

    if t_rename / total > 0.15:
        print(f"  transform_rename 占比较高 → iterrows() 是瓶颈")
    if t_shifts / total > 0.15:
        print(f"  calc_shifts 占比较高 → iterrows() 是瓶颈")

    return total


if __name__ == "__main__":
    t0_files, tx_files = find_files(DATA_DIR)
    if not t0_files or not tx_files:
        print(f"No test files in {DATA_DIR}")
        sys.exit(1)
    benchmark_pipeline(t0_files, tx_files)
