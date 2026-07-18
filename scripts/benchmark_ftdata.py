"""Benchmark FTData reading performance.

Measures:
- Total time to read all files
- Per-file average, min, max
- Format detection time vs total time
- Memory usage estimate

Run BEFORE and AFTER cache optimization to compare.
"""
import sys
import time
import gc
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.FT_file_parser import FTData


def format_time(seconds: float) -> str:
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.0f}µs"
    elif seconds < 1.0:
        return f"{seconds * 1_000:.1f}ms"
    else:
        return f"{seconds:.2f}s"


def benchmark_read(files: list[Path], config_path: str,
                   label: str = "Benchmark") -> dict:
    """Read all files and return timing stats."""
    times = []
    errors = []
    total_start = time.perf_counter()

    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")

    for i, p in enumerate(files):
        gc.collect()  # Minimize GC interference
        start = time.perf_counter()
        try:
            ft = FTData(str(p), config_path)
            elapsed = time.perf_counter() - start
            times.append(elapsed)

            data = ft.data
            rows = len(data)
            cols = len(ft.test_columns)

            print(f"  [{i+1:03d}/{len(files):03d}] {p.name:30s} "
                  f"{format_time(elapsed):>10s}  "
                  f"{rows:>5} rows × {cols:>3} cols")
        except Exception as e:
            elapsed = time.perf_counter() - start
            errors.append((str(p.name), str(e)))
            print(f"  [{i+1:03d}/{len(files):03d}] {p.name:30s} "
                  f"{format_time(elapsed):>10s}  "
                  f"ERROR: {e}")

    total_elapsed = time.perf_counter() - total_start

    # Stats
    stats = {
        "label": label,
        "total_files": len(files),
        "success": len(times),
        "errors": len(errors),
        "total_time": total_elapsed,
    }

    if times:
        stats["avg"] = sum(times) / len(times)
        stats["min"] = min(times)
        stats["max"] = max(times)
        stats["median"] = sorted(times)[len(times) // 2]
    else:
        stats["avg"] = stats["min"] = stats["max"] = stats["median"] = 0

    # Print summary
    print(f"\n  {'─'*40}")
    print(f"  Success: {stats['success']}/{stats['total_files']}")
    if errors:
        print(f"  Errors: {len(errors)}")
        for fname, err in errors[:5]:
            print(f"    {fname}: {err}")
    print(f"  Total time:  {format_time(stats['total_time'])}")
    if times:
        print(f"  Average:     {format_time(stats['avg'])}")
        print(f"  Median:      {format_time(stats['median'])}")
        print(f"  Min:         {format_time(stats['min'])}")
        print(f"  Max:         {format_time(stats['max'])}")
    print(f"{'='*60}\n")

    return stats


def find_csv_files(data_dir: str) -> list[Path]:
    """Find all CSV files in the data directory."""
    d = Path(data_dir)
    if not d.exists():
        print(f"Data directory not found: {d}")
        print("Run 'python scripts/generate_benchmark_data.py' first.")
        sys.exit(1)
    files = sorted(d.glob("*.csv"))
    if not files:
        print(f"No CSV files found in {d}")
        sys.exit(1)
    return files


def run_benchmarks(data_dir: str = "benchmark_data",
                   config_path: str | None = None):
    """Run all benchmarks."""
    files = find_csv_files(data_dir)

    if config_path is None:
        config_path = str(PROJECT_ROOT / "config" / "ft_data_config.toml")

    total_est_mb = sum(p.stat().st_size for p in files) / (1024 * 1024)
    print(f"Found {len(files)} CSV files ({total_est_mb:.1f} MB total)")
    print(f"Config: {config_path}")
    print(f"Testing FTData reading performance...")

    # Single read + cache warm-up (first file)
    warmup = files[:1]
    print(f"\nWarm-up: reading 1 file to populate caches...")
    ft = FTData(str(warmup[0]), config_path)
    _ = ft.data
    print(f"  Done: {len(ft.data)} rows × {len(ft.test_columns)} test cols")

    # Full benchmark
    stats = benchmark_read(files, config_path, "FTData Read Benchmark")

    return stats


def compare_runs(before_label: str = "Before (no cache)",
                 after_label: str = "After (with cache)"):
    """Placeholder for comparing before/after optimization runs."""
    print("\nRun this script BEFORE optimization:")
    print("  python scripts/benchmark_ftdata.py")
    print("\nThen AFTER optimization (same command):")
    print("  python scripts/benchmark_ftdata.py")
    print("\nCompare the total times.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Benchmark FTData reading")
    parser.add_argument("data_dir", nargs="?", default="benchmark_data",
                        help="Directory with benchmark CSV files")
    parser.add_argument("--config", default=None,
                        help="Path to ft_data_config.toml")
    args = parser.parse_args()

    run_benchmarks(args.data_dir, args.config)
