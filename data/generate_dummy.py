#!/usr/bin/env python3
"""
生成 dummy CSV 数据 — 新版。
- 随机 2-4 个可靠性试验
- 纯数字或数字字母混合 PART_ID
- 每个 ID 有 T0 + 各可靠性节点 FT 数据
- 测试项：IDSS IGSS VTH VF RDSON VDS + AC/DC + T1-T4 + Delta/Post/编号
- 文件名长度随机
- 包含失效数据（全部失效 / 部分失效）

用法：
    python data/generate_dummy.py          # 生成新数据（旧数据归档）
    python data/generate_dummy.py --clean  # 清理全部再生成
"""

import csv
import random
import shutil
import sys
from pathlib import Path

import numpy as np

DATA_DIR = Path(__file__).resolve().parent
random.seed(42)
np.random.seed(42)

# ── 可靠性试验 ──────────────────────────────────────────────
RELIABILITY_TESTS = ["HTRB", "HTSL", "TC", "HAST", "AC", "PC", "HTGB", "PR"]
DURATIONS = ["168H", "500H", "1000H", "2000H", "3000H"]
TEMPS = ["高温", "常温", "低温"]
CONDITIONS = ["AC", "DC"]

# ── 测试项 ──────────────────────────────────────────────────
TEST_NAMES = ["IDSS", "IGSS", "VTH", "VF", "RDSON", "VDS"]
UNITS = {"IDSS": "A", "IGSS": "A", "VTH": "V", "VF": "V", "RDSON": "ohm", "VDS": "V"}
# (lo, hi, k, scale) for weibull
TEST_PARAMS = {
    "IDSS":  (0, 1e-3,  0.8,  1e-5),
    "IGSS":  (0, 1e-4,  0.7,  5e-6),
    "VTH":   (1.5, 5.0,  3.0,  3.5),
    "VF":    (0.6, 2.0,  4.0,  1.2),
    "RDSON": (0.005, 0.030, 2.5,  0.015),
    "VDS":   (600, 1500,  5.0,  1000),
}
DICE = ["T1", "T2", "T3", "T4"]
SUFFIXES = ["", "_Delta", "_Post"]

# 文件名随机元素池（长度差异用）
FILE_EXTRA = ["v1", "v2", "revA", "retest", "final", "silicone", "epoxy",
              "noAP", "withAP", "空", ""]

# ── 工具 ────────────────────────────────────────────────────

def weibull_val(name: str) -> float:
    lo, hi, k, scale = TEST_PARAMS[name]
    v = np.random.weibull(k) * scale
    return float(np.clip(v, lo, hi))


def make_part_ids(n: int) -> list[str]:
    ids = set()
    while len(ids) < n:
        if random.random() < 0.5:
            pid = str(random.randint(10000, 99999))
        else:
            prefix = random.choice("ABCDEFGH")
            suffix = random.randint(1000, 9999)
            pid = f"{prefix}{suffix}"
        ids.add(pid)
    return sorted(ids)


def build_column_names() -> list[dict]:
    """生成所有测试列名"""
    cols = []
    for cond in CONDITIONS:
        for name in TEST_NAMES:
            unit = UNITS[name]
            lo, hi, _, _ = TEST_PARAMS[name]
            for suf in SUFFIXES:
                for die in DICE:
                    col_name = f"{cond}_{name}{suf}_{die}"
                    # 部分列加编号后缀增加长度差异
                    if random.random() < 0.15:
                        col_name += f"_{random.randint(1,9)}"
                    cols.append({"name": col_name, "unit": unit, "lo": lo, "hi": hi})
    return cols


def build_header(writer, columns, extra_cols=None):
    base = ["PART_ID", "SOFT_BIN"]
    if extra_cols:
        base.extend(extra_cols)
    writer.writerow(list(base) + [c["name"] for c in columns])
    writer.writerow(["Unit", ""] + ([""] * len(extra_cols or [])) + [c["unit"] for c in columns])
    writer.writerow(["Lower Limit", ""] + ([""] * len(extra_cols or [])) + [c["lo"] for c in columns])
    writer.writerow(["Higher Limit", ""] + ([""] * len(extra_cols or [])) + [c["hi"] for c in columns])


def gen_row(pid: str, columns: list[dict], fail_rate: float = 0.15) -> list:
    """生成一行数据，fail_rate 控制失效概率"""
    sb = 2 if random.random() < fail_rate else 1
    row = [pid, sb]
    for c in columns:
        row.append(f"{weibull_val(c['name'].split('_')[1]):.6e}")
    return row


def gen_fail_rows(pid: str, columns: list[dict], n: int, all_fail: bool = False) -> list[list]:
    """生成 n 行失效数据"""
    rows = []
    sb = 2  # 全部 FAIL
    for _ in range(n):
        row = [pid, sb]
        for c in columns:
            v = weibull_val(c['name'].split('_')[1]) * random.uniform(0.3, 3.0)
            row.append(f"{v:.6e}")
        rows.append(row)
    if not all_fail:
        # 加 1 条 PASS
        rows.append(gen_row(pid, columns, fail_rate=0))
    return rows


# ── 生成主流程 ──────────────────────────────────────────────

def gen_all(data_dir: Path):
    columns = build_column_names()
    col_map = {c["name"]: c for c in columns}

    # 随机选 2-4 个可靠性试验
    n_tests = random.randint(2, 4)
    chosen_tests = random.sample(RELIABILITY_TESTS, n_tests)
    print(f"可靠性试验: {chosen_tests}")

    # 每个试验生成一批 PART_ID（部分重叠模拟真实情况）
    all_part_ids = set()
    test_part_ids = {}
    for test in chosen_tests:
        n_ids = random.randint(6, 12)
        ids = make_part_ids(n_ids)
        test_part_ids[test] = ids
        all_part_ids.update(ids)
    all_part_ids = sorted(all_part_ids)
    print(f"PART_ID 总数: {len(all_part_ids)}")

    t0_dir = data_dir / "T0"
    t0_dir.mkdir(parents=True, exist_ok=True)
    tx_dir = data_dir / "TX"
    tx_dir.mkdir(parents=True, exist_ok=True)

    # ── T0：每个 PART_ID 一条（分散到 2-4 个文件） ──
    t0_rows = []
    for pid in all_part_ids:
        t0_rows.append(gen_row(pid, columns))
    random.shuffle(t0_rows)
    n_t0_files = random.randint(2, 4)
    chunks = [t0_rows[i::n_t0_files] for i in range(n_t0_files)]
    t0_names = [f"T0_产线_{chr(65+i)}.csv" for i in range(n_t0_files)]
    for i, chunk in enumerate(chunks):
        path = t0_dir / t0_names[i]
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            build_header(w, columns)
            for row in chunk:
                w.writerow(row)
        print(f"  T0/{t0_names[i]}: {len(chunk)} 行")

    # 完整 T0.csv（方便引用）
    t0_all = data_dir / "T0.csv"
    with open(t0_all, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        build_header(w, columns)
        for row in t0_rows:
            w.writerow(row)

    # ── TX：每个可靠性试验生成多个时间节点文件 ──
    total_tx = 0
    for test in chosen_tests:
        pids = test_part_ids[test]
        n_nodes = random.randint(2, 4)
        durs = random.sample(DURATIONS, n_nodes)
        for dur in durs:
            # 随机生成文件名
            extra_parts = random.sample(FILE_EXTRA, random.randint(0, 3))
            fn_parts = [test, dur, random.choice(TEMPS), random.choice(CONDITIONS)]
            fn_parts.extend(extra_parts)
            fn_parts = [p for p in fn_parts if p]
            fn = "_".join(fn_parts) + ".csv"

            rows = []
            # 哪些 PART_ID 出现重复/失效
            fail_ids = random.sample(pids, max(1, len(pids) // 3))
            for pid in pids:
                if pid in fail_ids:
                    mode = random.random()
                    if mode < 0.3:
                        # 全部失效：2-10 条 FAIL
                        rows.extend(gen_fail_rows(pid, columns, random.randint(2, 10), all_fail=True))
                    elif mode < 0.6:
                        # 部分失效：1-5 条 FAIL + 1 条 PASS
                        rows.extend(gen_fail_rows(pid, columns, random.randint(1, 5), all_fail=False))
                    else:
                        # 多条 PASS + 可能 FAIL
                        n_pass = random.randint(2, 5)
                        for _ in range(n_pass):
                            rows.append(gen_row(pid, columns, fail_rate=0))
                        if random.random() < 0.4:
                            rows.append(gen_row(pid, columns, fail_rate=1.0))
                else:
                    # 正常：1 条，85% PASS
                    rows.append(gen_row(pid, columns))

            random.shuffle(rows)
            fpath = tx_dir / fn
            with open(fpath, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                build_header(w, columns)
                for row in rows:
                    w.writerow(row)
            total_tx += 1
            print(f"  TX/{fn}: {len(rows)} 行 ({test}/{dur})")

    print(f"  TX 总计: {total_tx} 个文件")
    print(f"\n✅ 全部生成完毕 → {data_dir}/")


# ── TDDB 测试数据 ─────────────────────────────────────────────

def generate_tddb_data(data_dir: Path):
    """生成 TDDB 测试用 Excel 数据文件。"""
    print("生成 TDDB 测试数据...")

    # 内联生成（避免依赖 core 模块路径）
    import openpyxl
    from openpyxl import Workbook

    rng = np.random.RandomState(42)

    # E 模型加速
    GAMMA = 2.0  # cm/MV
    TOX = 5.0    # nm

    def eta_at_v(v, eta_ref, v_ref):
        eox_v = v / TOX * 10.0
        eox_ref = v_ref / TOX * 10.0
        return eta_ref * np.exp(GAMMA * (eox_ref - eox_v))

    voltages = [5.0, 5.5, 6.0]
    temperatures = [25, 125]
    groups = ["湿氧", "干氧"]
    eta_vmin = 500.0
    beta = 2.0
    n_per = 20
    v_ref = min(voltages)
    cumulative_current = 1e-6

    rows = []
    pid = 0
    for grp in groups:
        for temp in temperatures:
            for v in voltages:
                eta_v = eta_at_v(v, eta_vmin, v_ref)
                # Weibull samples
                u = rng.rand(n_per)
                tbds = eta_v * (-np.log(1 - u)) ** (1.0 / beta)
                for tbd in tbds:
                    pid += 1
                    qbd = tbd * cumulative_current
                    ignore = 1 if rng.rand() < 0.05 else 0
                    rows.append([
                        f"DUT_{pid:04d}", v, temp, 1.0,
                        round(tbd, 4), "s", round(qbd, 6), "C",
                        ignore, grp, f"CH{(pid % 48) + 1:02d}", "",
                    ])

    path = data_dir / "tddb_test_data.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "TDDB试验1"
    ws.append(["PART_ID", "Vgs", "Temperature", "Gate Oxide Area",
               "TBD", "TBD Unit", "QBD", "QBD Unit",
               "ignore", "group", "老化板通道", "comment"])
    for row in rows:
        ws.append(row)
    wb.save(path)
    wb.close()

    print(f"  ✅ TDDB 测试数据 → {path}")
    print(f"  {len(rows)} 行, {len(groups)} groups, "
          f"{len(voltages)} 电压, {len(temperatures)} 温度")


# ── 维护 ────────────────────────────────────────────────────

def archive_old(data_dir: Path):
    archive_dir = data_dir / "archive"
    existing = list(data_dir.glob("*.csv")) + [data_dir / "TX", data_dir / "T0"]
    existing = [p for p in existing if p.exists()]
    if not existing:
        return
    archive_dir.mkdir(parents=True, exist_ok=True)
    ver = 1
    for d in archive_dir.iterdir():
        if d.is_dir() and d.name.startswith("v"):
            try:
                ver = max(ver, int(d.name[1:]) + 1)
            except ValueError:
                pass
    dest = archive_dir / f"v{ver}"
    dest.mkdir(parents=True)
    for p in existing:
        shutil.move(str(p), str(dest / p.name))
    print(f"  🗂 旧数据 → {dest.relative_to(data_dir)}/")


def clean(data_dir: Path):
    for p in list(data_dir.glob("*.csv")) + [data_dir / "TX"]:
        if p.exists():
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
    print(f"  🧹 已清理 {data_dir}")


def main():
    if "--clean" in sys.argv:
        clean(DATA_DIR)
        return
    if "--tddb" in sys.argv:
        generate_tddb_data(DATA_DIR)
        return
    archive_old(DATA_DIR)
    gen_all(DATA_DIR)


if __name__ == "__main__":
    main()
