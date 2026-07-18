"""Compare before/after pipeline output at each step."""
import sys, time, gc, pickle
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load the OLD version first to capture baseline
# We'll import and compare step by step

import pandas as pd
import numpy as np
from core.FT_file_parser import FTData
from core.data_merge import merge_t0_tx

DATA_DIR = PROJECT_ROOT / "benchmark_merge_test"
CFG = str(PROJECT_ROOT / "config" / "ft_data_config.toml")

def find_files():
    d = Path(DATA_DIR)
    t0 = sorted(str(p) for p in d.glob("T0_*.csv"))
    tx = sorted(str(p) for p in d.glob("TX_*.csv"))
    return t0, tx

t0_files, tx_files = find_files()

# Step 0: merge (same for both)
print("=== Step 0: merge_t0_tx ===")
merged = merge_t0_tx(t0_files, tx_files, config_path=CFG)
print(f"  Merged: {len(merged)} rows × {len(merged.columns)} cols")

# Build same calc_config as benchmark
test_cols = [c for c in merged.columns if c.startswith("DC_")]
calc_config = {
    "renames": {},
    "suffixes": {},
    "formulas": {c: "TX - T0" for c in test_cols},
    "limits": {c: "10" for c in test_cols},
    "directions": {c: "upper" for c in test_cols},
}

# Step 1: transform_rename
print("\n=== Step 1: transform_rename ===")
from core.compare import transform_rename
t0 = time.perf_counter()
renamed = transform_rename(merged, calc_config)
t = time.perf_counter() - t0
print(f"  → {len(renamed)} rows × {len(renamed.columns)} cols ({t*1000:.1f}ms)")

# Step 2: calc_shifts
print("\n=== Step 2: calc_shifts ===")
from core.compare import calc_shifts
t0 = time.perf_counter()
shifts = calc_shifts(renamed, calc_config)
t = time.perf_counter() - t0
print(f"  → {len(shifts)} rows × {len(shifts.columns)} cols ({t*1000:.1f}ms)")

# Check for NaN differences in shifts
print(f"\n=== 数据质量检查 ===")
# Check PART_ID range
print(f"  PART_ID range: {shifts['PART_ID'].min()} - {shifts['PART_ID'].max()}")
print(f"  PART_ID unique: {shifts['PART_ID'].nunique()}")
print(f"  GROUP values: {shifts['GROUP'].unique().tolist()}")

# Sample some shift values
shift_cols = [c for c in shifts.columns if c.endswith('_shift')]
if shift_cols:
    sample = shifts[shift_cols[:5]].head(3)
    print(f"\n  Shift sample (first 3 rows, 5 cols):")
    for c in shift_cols[:5]:
        vals = shifts[c].values
        num_valid = np.sum(~np.isnan(vals.astype(float)))
        print(f"    {c}: {num_valid}/{len(vals)} valid, "
              f"mean={np.nanmean(vals.astype(float)):.4e}")

# Check for any NaN → non-NaN or vice versa between runs (consistency)
# We run it twice and compare
print(f"\n=== Consistency check (run twice) ===")
renamed2 = transform_rename(merged, calc_config)
shifts2 = calc_shifts(renamed2, calc_config)

# Compare renamed
same_rows = len(renamed) == len(renamed2)
same_cols = list(renamed.columns) == list(renamed2.columns)
print(f"  renamed: same_rows={same_rows}, same_cols={same_cols}")
if same_rows and same_cols:
    cell_diffs = (renamed.values != renamed2.values).sum()
    print(f"  renamed cell diffs: {cell_diffs}")

# Compare shifts
same_rows = len(shifts) == len(shifts2)
same_cols = list(shifts.columns) == list(shifts2.columns)
print(f"  shifts: same_rows={same_rows}, same_cols={same_cols}")
if same_rows and same_cols:
    cell_diffs = 0
    for c in shifts.columns:
        v1 = shifts[c].values
        v2 = shifts2[c].values
        if v1.dtype.kind in ('f',) and v2.dtype.kind in ('f',):
            diff = np.isnan(v1) != np.isnan(v2)
            diff |= (~np.isnan(v1) & ~np.isnan(v2) & (np.abs(v1.astype(float) - v2.astype(float)) > 1e-10))
        else:
            # Use object comparison for strings
            diff = v1 != v2
        cell_diffs += int(diff.sum())
    print(f"  shifts cell diffs: {cell_diffs}")
    
    # Check row ordering consistency
    pid1 = shifts['PART_ID'].values
    pid2 = shifts2['PART_ID'].values
    pid_diffs = (pid1 != pid2).sum()
    print(f"  PART_ID position diffs: {pid_diffs}")
    if pid_diffs > 0:
        for i in range(min(10, len(pid1))):
            if pid1[i] != pid2[i]:
                print(f"    Row {i}: run1={pid1[i]} run2={pid2[i]} (GROUP={shifts.iloc[i]['GROUP']})")
