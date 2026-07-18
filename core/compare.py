"""
对比文件核心逻辑：转换重命名 → Shift 计算 → Excel 导出。

v2 - 优化版：向量化替换 iterrows，开放pyxl样式缓存+预计算超限。
"""
import re
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd


# ═══════════════════════════════════════════════════════════════
#  1. 转换（重命名 + MV1 拆分）
# ═══════════════════════════════════════════════════════════════

def transform_rename(df: pd.DataFrame, calc_config: dict) -> pd.DataFrame:
    """根据 calc_config 中的重命名规则转换列名和 PART_ID。

    向量化实现（v2）：用 df.rename() + pd.melt() 替换 iterrows。
    """
    rename_map = calc_config.get("renames", {})
    suffix_map = calc_config.get("suffixes", {})

    fixed_cols_set = {"PART_ID", "SOFT_BIN", "group", "filepath"}
    test_cols = [c for c in df.columns if c not in fixed_cols_set]

    # 找出 MV1 项目（多个原列→同一新列）
    new_name_counts: dict[str, list[str]] = {}
    for orig, new in rename_map.items():
        new_name_counts.setdefault(new, []).append(orig)
    mv1_groups = {new: origs for new, origs in new_name_counts.items() if len(origs) > 1}

    # 所有输出列
    all_new_cols_set = set(df.columns)
    for orig, new in rename_map.items():
        if orig in all_new_cols_set:
            all_new_cols_set.discard(orig)
            all_new_cols_set.add(new)
    all_new_cols = sorted(all_new_cols_set)
    fixed_cols_in_df = [c for c in fixed_cols_set if c in df.columns]

    # ── 无 MV1 的快速路径 ──
    if not mv1_groups:
        renamed = df.rename(columns=rename_map)
        available = {c: renamed[c] for c in all_new_cols if c in renamed.columns}
        missing = {c: pd.Series(np.nan, index=df.index, name=c) for c in all_new_cols if c not in renamed.columns}
        parts = [*available.values(), *missing.values()]
        result = pd.concat(parts, axis=1) if len(parts) > 1 else parts[0]
        return result[all_new_cols]

    # ── 有 MV1 的路径 ──
    # 1) 简单重命名（非 MV1 列）
    mv1_origs: set[str] = set()
    for origs in mv1_groups.values():
        mv1_origs.update(origs)
    simple_renames = {k: v for k, v in rename_map.items() if k not in mv1_origs}

    simple_renamed = df.rename(columns=simple_renames)
    # 去重：fixed cols 已在 fixed_cols_in_df 中，all_new_cols 里排除它们
    simple_all_new = [c for c in all_new_cols if c not in mv1_groups
                      and c in simple_renamed.columns
                      and c not in fixed_cols_in_df]
    simple_part_cols = fixed_cols_in_df + simple_all_new
    simple_part = simple_renamed[simple_part_cols].copy()

    # 2) MV1 组：melt 展开为多行
    parts = [simple_part]
    for new_name, origs in mv1_groups.items():
        existing = [c for c in origs if c in df.columns]
        if not existing:
            continue
        mv1_df = df[fixed_cols_in_df + existing].copy()
        melted = mv1_df.melt(
            id_vars=fixed_cols_in_df,
            value_vars=existing,
            var_name="_src", value_name=new_name,
        )
        # 只保留有值的行
        melted = melted.dropna(subset=[new_name])
        if melted.empty:
            continue
        # 加 suffix 到 PART_ID
        melted["_sfx"] = melted["_src"].map(suffix_map).fillna("")
        has_sfx = melted["_sfx"] != ""
        melted.loc[has_sfx, "PART_ID"] = (
            melted.loc[has_sfx, "PART_ID"].astype(str) + "_" + melted.loc[has_sfx, "_sfx"]
        )
        melted = melted.drop(columns=["_src", "_sfx"])
        melted = melted.reset_index(drop=True)
        parts.append(melted)

    # 3) 合并
    final = pd.concat(parts, ignore_index=True) if len(parts) > 1 else parts[0]

    # 确保所有列存在
    for c in all_new_cols:
        if c not in final.columns:
            final[c] = np.nan

    return final[all_new_cols]


# ═══════════════════════════════════════════════════════════════
#  2. Shift 计算（向量化）
# ═══════════════════════════════════════════════════════════════

def safe_eval_formula(formula: str, t0_val: Any, tx_val: Any) -> Any:
    if pd.isna(t0_val) or pd.isna(tx_val):
        return np.nan
    try:
        T0 = float(t0_val)
        TX = float(tx_val)
        allowed = {"abs": abs, "log": lambda x: np.log(x) if x > 0 else np.nan,
                   "log10": lambda x: np.log10(x) if x > 0 else np.nan,
                   "exp": np.exp, "sqrt": lambda x: np.sqrt(x) if x >= 0 else np.nan,
                   "pow": pow, "min": min, "max": max}
        result = eval(formula, {"__builtins__": {}}, {"T0": T0, "TX": TX, **allowed})
        return float(result)
    except Exception:
        return np.nan


def _vectorized_formula(formula: str, t0_val: float, tx_vals: np.ndarray) -> np.ndarray:
    """向量化公式求值，常见公式直接 numpy 计算，否则回退到逐元素 eval。"""
    t0 = float(t0_val)
    # 常见公式快速路径
    if formula == "TX - T0" or formula == "TX-T0":
        return tx_vals.astype(float) - t0
    elif formula == "T0 - TX" or formula == "T0-TX":
        return t0 - tx_vals.astype(float)
    elif formula == "abs(TX - T0)" or formula == "abs(TX-T0)":
        return np.abs(tx_vals.astype(float) - t0)
    elif formula == "TX / T0" or formula == "TX/T0":
        tx_f = tx_vals.astype(float)
        return np.where(t0 != 0, tx_f / t0, np.nan)
    elif formula == "T0 / TX" or formula == "T0/TX":
        tx_f = tx_vals.astype(float)
        return np.where(tx_f != 0, t0 / tx_f, np.nan)
    elif formula == "abs(TX / T0 - 1)" or formula == "abs(TX/T0-1)":
        tx_f = tx_vals.astype(float)
        return np.where(t0 != 0, np.abs(tx_f / t0 - 1), np.nan)
    elif formula == "(TX - T0) / T0 * 100" or formula == "(TX-T0)/T0*100":
        tx_f = tx_vals.astype(float)
        return np.where(t0 != 0, (tx_f - t0) / t0 * 100, np.nan)
    elif formula == "log(TX / T0)" or formula == "log(TX/T0)":
        tx_f = tx_vals.astype(float)
        ratio = np.where(t0 != 0, tx_f / t0, np.nan)
        return np.where((ratio > 0) & ~np.isnan(ratio), np.log(ratio), np.nan)
    elif formula == "log10(TX / T0)" or formula == "log10(TX/T0)":
        tx_f = tx_vals.astype(float)
        ratio = np.where(t0 != 0, tx_f / t0, np.nan)
        return np.where((ratio > 0) & ~np.isnan(ratio), np.log10(ratio), np.nan)
    # 回退：逐元素 eval
    result = np.full(len(tx_vals), np.nan)
    for i, tx in enumerate(tx_vals):
        if not pd.isna(tx):
            result[i] = safe_eval_formula(formula, t0, tx)
    return result


def calc_shifts(df: pd.DataFrame, calc_config: dict) -> pd.DataFrame:
    """向量化的 shift 计算（v2）：用 merge 替换 iterrows。"""
    formulas = calc_config.get("formulas", {})
    if not formulas:
        return pd.DataFrame()

    df_t0 = df[df["group"] == "T0"].copy()
    df_tx = df[df["group"] != "T0"].copy()
    if df_t0.empty or df_tx.empty:
        return pd.DataFrame()

    rename_map = calc_config.get("renames", {})
    # 预计算反向映射
    reverse_map: dict[str, str] = {}
    for k, v in rename_map.items():
        reverse_map[v] = k

    # 确定测试列
    test_cols_set: set[str] = set()
    for orig_name in formulas:
        final_name = rename_map.get(orig_name, orig_name)
        test_cols_set.add(final_name)
    test_cols = sorted(test_cols_set - {"PART_ID", "SOFT_BIN", "group", "filepath"})
    avail_test = [c for c in test_cols if c in df_t0.columns or c in df_tx.columns]
    if not avail_test:
        return pd.DataFrame()

    # T0 基准值（去重后每 PART_ID 一行）
    t0_cols = ["PART_ID"] + [c for c in avail_test if c in df_t0.columns]
    t0_vals = df_t0[t0_cols].drop_duplicates(subset="PART_ID").set_index("PART_ID")

    # 批量处理所有 TX 行 × 测试列
    rows = []
    grp_cols = ["PART_ID", "SOFT_BIN", "group", "filepath"]
    tx_data = df_tx[grp_cols + avail_test].copy()

    for pid, tx_row in tx_data.groupby("PART_ID", sort=False, group_keys=False):
        if pid not in t0_vals.index:
            continue
        t0_row = t0_vals.loc[pid]
        n = len(tx_row)
        base = {
            "PART_ID": [pid] * n,
            "SOFT_BIN": tx_row["SOFT_BIN"].values,
            "GROUP": tx_row["group"].values,
            "file": tx_row["filepath"].values,
        }
        for col in avail_test:
            tx_vals = tx_row[col].values
            t0_val = t0_row[col] if col in t0_row.index else np.nan
            if pd.isna(t0_val):
                base[f"{col}_T0"] = np.full(n, np.nan)
                base[f"{col}_TX"] = tx_vals
                base[f"{col}_shift"] = np.full(n, np.nan)
                continue
            t0_series = np.full(n, t0_val, dtype=float)
            orig = reverse_map.get(col, col)
            formula = formulas.get(orig, "")
            if formula:
                shift_vals = _vectorized_formula(formula, t0_val, tx_vals)
            else:
                shift_vals = np.full(n, np.nan)
            base[f"{col}_T0"] = t0_series
            base[f"{col}_TX"] = tx_vals
            base[f"{col}_shift"] = shift_vals
        rows.append(pd.DataFrame(base))

    if not rows:
        return pd.DataFrame()
    result = pd.concat(rows, ignore_index=True)
    if not result.empty:
        result.sort_values(["GROUP", "PART_ID"], inplace=True, ignore_index=True)
    return result


# ═══════════════════════════════════════════════════════════════
#  3. 读取原始元信息
# ═══════════════════════════════════════════════════════════════

def read_raw_headers_from_file(path: str) -> dict:
    """从 CSV 文件前 4 行读取原始元信息。

    返回: {原始列名: {"unit": ..., "lo": ..., "hi": ...}}
    """
    import csv
    result = {}
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = [next(reader) for _ in range(4)]
        col_names = rows[0]
        units = rows[1] if len(rows) > 1 else []
        los = rows[2] if len(rows) > 2 else []
        his = rows[3] if len(rows) > 3 else []
        for i, name in enumerate(col_names):
            name = name.strip()
            if name and name != "PART_ID" and name != "SOFT_BIN":
                result[name] = {
                    "unit": units[i].strip() if i < len(units) else "",
                    "lo": los[i].strip() if i < len(los) else "",
                    "hi": his[i].strip() if i < len(his) else "",
                }
    except Exception:
        pass
    return result


# ═══════════════════════════════════════════════════════════════
#  4. Excel 导出（优化版 v3 — xlsxwriter）
# ═══════════════════════════════════════════════════════════════

# 单位前缀 → SI 倍数
_PREFIX_MAP = {
    "M": 1e6, "k": 1e3, "": 1,
    "m": 1e-3, "u": 1e-6, "n": 1e-9, "p": 1e-12,
}
_PREFIX_PATTERN = re.compile(r"^([Mkmunp])?(.*)$")


def _to_si_unit(unit: str) -> str:
    """将带前缀的单位转换为 SI 基本单位，如 'uA'→'A', 'mOhm'→'Ohm', 'mV'→'V'。"""
    m = _PREFIX_PATTERN.match(unit.strip())
    if m and m.group(2):
        return m.group(2)
    return unit


def _to_si_value(val_str: str, unit: str) -> str:
    """将带前缀单位的值转换为 SI 值，如 '0.001' + 'uA' → '1e-09'。"""
    m = _PREFIX_PATTERN.match(unit.strip())
    prefix = m.group(1) if m and m.group(1) else ""
    factor = _PREFIX_MAP.get(prefix, 1)
    try:
        val = float(val_str) * factor
        # 用科学计数法或小数字符串表示
        if abs(val) < 0.001 or abs(val) >= 1e6:
            return f"{val:.6e}"
        else:
            return f"{val:.6f}".rstrip("0").rstrip(".")
    except (ValueError, TypeError):
        return val_str

def export_excel(
    data: pd.DataFrame,
    calc_config: dict,
    raw_headers: Optional[dict] = None,
    output_path: str = "对比结果.xlsx",
    progress: Optional[Any] = None,
):
    """导出 Excel，格式如示例。

    v3 优化（xlsxwriter）：
    - 预定义 Format 对象替代 per-cell 样式创建
    - 预计算超限标志（向量化）
    - 预计算 reverse_map 避免 per-cell 反查
    """
    import xlsxwriter

    limits = calc_config.get("limits", {})
    directions = calc_config.get("directions", {})
    formulas = calc_config.get("formulas", {})
    rename_map = calc_config.get("renames", {})

    # 预计算反向映射
    reverse_map: dict[str, str] = {}
    for k, v in rename_map.items():
        reverse_map[v] = k

    if progress:
        progress.set_status("构建 Excel...")

    # 确定测试项
    fixed_cols = ["PART_ID", "SOFT_BIN", "GROUP", "file"]
    test_blocks = sorted(set(
        c.rsplit("_", 1)[0] for c in data.columns if c not in fixed_cols
    ))
    n_fixed = len(fixed_cols)
    n_blocks = len(test_blocks)
    total_cols = n_fixed + n_blocks * 3

    # 确保输出目录存在
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    wb = xlsxwriter.Workbook(output_path)
    ws = wb.add_worksheet("对比结果")

    # ═══ 预定义 Format 对象 ═══
    fmt_base = {
        "align": "center",
        "valign": "vcenter",
        "text_wrap": True,
        "border": 1,
        "font_size": 10,
    }
    FMT_HEADER = wb.add_format({"bold": True, **fmt_base})
    FMT_NORMAL = wb.add_format(fmt_base)
    FMT_GRAY = wb.add_format({"font_color": "#999999", "font_size": 9, **fmt_base})
    FMT_DARK = wb.add_format({"font_color": "#666666", "font_size": 9, **fmt_base})
    FMT_META = wb.add_format({"font_size": 10, **fmt_base})
    FMT_YELLOW = wb.add_format({"bg_color": "#FFFF00", **fmt_base})
    FMT_RED_BOLD = wb.add_format({"bold": True, "font_color": "#FF0000", **fmt_base})
    FMT_YELLOW_RED = wb.add_format({"bold": True, "font_color": "#FF0000",
                                     "bg_color": "#FFFF00", **fmt_base})
    FMT_HEADER_FILL = wb.add_format({"bold": True, "bg_color": "#D9E1F2", **fmt_base})
    FMT_YELLOW_HEADER = wb.add_format({"bold": True, "bg_color": "#FFFF00", **fmt_base})

    # ═══ 表头 ═══
    # 第1行：测试项名称（合并3列）
    for ci, col in enumerate(fixed_cols):
        ws.write(0, ci, col, FMT_HEADER)
    for bi, block in enumerate(test_blocks):
        start = n_fixed + bi * 3
        ws.merge_range(0, start, 0, start + 2, block, FMT_HEADER)

    # 第2行：Unit —每个子列对应值（归一化为 SI）
    ws.write(1, 0, "Unit", FMT_DARK)
    for ci in range(1, n_fixed):
        ws.write(1, ci, "", FMT_GRAY)
    for bi, block in enumerate(test_blocks):
        start = n_fixed + bi * 3
        orig = reverse_map.get(block, block)
        raw_unit = raw_headers.get(orig, {}).get("unit", "") if raw_headers else ""
        si_unit = _to_si_unit(raw_unit)
        ws.write(1, start, si_unit, FMT_META)        # T0 unit
        ws.write(1, start + 1, si_unit, FMT_META)    # TX unit
        ws.write(1, start + 2, "", FMT_GRAY)          # shift — 无单位

    # 第3行：LimitL（归一化为 SI）
    ws.write(2, 0, "LimitL", FMT_DARK)
    for ci in range(1, n_fixed):
        ws.write(2, ci, "", FMT_GRAY)
    for bi, block in enumerate(test_blocks):
        start = n_fixed + bi * 3
        orig = reverse_map.get(block, block)
        raw_unit = raw_headers.get(orig, {}).get("unit", "") if raw_headers else ""
        lo_raw = raw_headers.get(orig, {}).get("lo", "") if raw_headers else ""
        lo_si = _to_si_value(lo_raw, raw_unit) if lo_raw else ""
        shift_limit = limits.get(orig, "")
        direction = directions.get(orig, "upper")
        sl = shift_limit if direction == "lower" else ""
        ws.write(2, start, lo_si, FMT_META)           # T0 lo (SI)
        ws.write(2, start + 1, lo_si, FMT_META)       # TX lo (SI)
        ws.write(2, start + 2, sl, FMT_META)           # shift limit (lower)

    # 第4行：LimitU（归一化为 SI）
    ws.write(3, 0, "LimitU", FMT_DARK)
    for ci in range(1, n_fixed):
        ws.write(3, ci, "", FMT_GRAY)
    for bi, block in enumerate(test_blocks):
        start = n_fixed + bi * 3
        orig = reverse_map.get(block, block)
        raw_unit = raw_headers.get(orig, {}).get("unit", "") if raw_headers else ""
        hi_raw = raw_headers.get(orig, {}).get("hi", "") if raw_headers else ""
        hi_si = _to_si_value(hi_raw, raw_unit) if hi_raw else ""
        shift_limit = limits.get(orig, "")
        direction = directions.get(orig, "upper")
        sl = shift_limit if direction == "upper" else ""
        ws.write(3, start, hi_si, FMT_META)            # T0 hi (SI)
        ws.write(3, start + 1, hi_si, FMT_META)        # TX hi (SI)
        ws.write(3, start + 2, sl, FMT_META)           # shift limit (upper)

    # 第5行：shift公式（合并 3 列 — 与示例.xlsx一致）
    ws.write(4, 0, "shift公式", FMT_DARK)
    for ci in range(1, n_fixed):
        ws.write(4, ci, "", FMT_GRAY)
    for bi, block in enumerate(test_blocks):
        start = n_fixed + bi * 3
        orig = reverse_map.get(block, block)
        formula = formulas.get(orig, "")
        if formula:
            ws.merge_range(4, start, 4, start + 2, formula, FMT_META)
        else:
            ws.write(4, start, "", FMT_GRAY)
            ws.write(4, start + 1, "", FMT_GRAY)
            ws.write(4, start + 2, "", FMT_GRAY)

    # 第6行：子表头 T0 / TX / shift
    for ci, col in enumerate(fixed_cols):
        ws.write(5, ci, col, FMT_HEADER_FILL)
    for bi, block in enumerate(test_blocks):
        start = n_fixed + bi * 3
        for si, sub in enumerate(["T0", "TX", "shift"]):
            ws.write(5, start + si, sub, FMT_HEADER_FILL)

    # ═══ 预计算超限标志（T0/TX 超出规范 + shift 超出限值） ═══
    n_data = len(data)
    row_overlimit = np.zeros(n_data, dtype=bool)
    # 每列是否超限 → (block_bi, sub_idx, mask)   sub_idx: 0=T0, 1=TX, 2=shift
    col_overlimit: list[tuple[int, int, np.ndarray]] = []

    for bi, block in enumerate(test_blocks):
        orig = reverse_map.get(block, block)

        # ── T0 / TX 检查（超出 lower/higher limit） ──
        for si, sub in enumerate(["T0", "TX"]):
            col_name = f"{block}_{sub}"
            if col_name not in data.columns:
                continue
            # 从 raw_headers 读取 lower/higher limit，转为 SI
            lo_str = raw_headers.get(orig, {}).get("lo", "") if raw_headers else ""
            hi_str = raw_headers.get(orig, {}).get("hi", "") if raw_headers else ""
            raw_unit = raw_headers.get(orig, {}).get("unit", "") if raw_headers else ""
            lo_si_str = _to_si_value(lo_str, raw_unit) if lo_str else ""
            hi_si_str = _to_si_value(hi_str, raw_unit) if hi_str else ""
            try:
                lo = float(lo_si_str)
                hi = float(hi_si_str)
            except (ValueError, TypeError):
                continue
            vals = data[col_name].values.astype(float)
            is_num = ~np.isnan(vals)
            over = (is_num & (vals < lo - 1e-12)) | (is_num & (vals > hi + 1e-12))
            if over.any():
                row_overlimit |= over
                col_overlimit.append((bi, si, over))

        # ── shift 检查（超出 shift limit） ──
        shift_col = f"{block}_shift"
        if shift_col not in data.columns:
            continue
        limit_val = limits.get(orig)
        direction = directions.get(orig, "upper")
        if not limit_val:
            continue
        try:
            lv = float(limit_val)
        except (ValueError, TypeError):
            continue
        vals = data[shift_col].values.astype(float)
        is_num = ~np.isnan(vals)
        over = np.zeros(n_data, dtype=bool)
        if direction == "lower":
            over = is_num & (vals < lv)
        else:
            over = is_num & (vals > lv)
        if over.any():
            row_overlimit |= over
            col_overlimit.append((bi, 2, over))  # si=2 = "shift"

    # ═══ 第7行起（0-indexed row 6）：数据 ═══
    data_start = 6  # 0-indexed
    for r_idx in range(n_data):
        r = data_start + r_idx
        row = data.iloc[r_idx]
        is_yellow = row_overlimit[r_idx]

        # 预选该行的固定列格式
        fmt_fixed = FMT_YELLOW if is_yellow else FMT_NORMAL

        # Fixed cols
        for ci, col in enumerate(fixed_cols):
            val = row.get(col, "")
            if isinstance(val, float) and np.isnan(val):
                val = ""
            ws.write(r, ci, val, fmt_fixed)

        # Test blocks × (T0, TX, shift)
        for bi, block in enumerate(test_blocks):
            base_col = n_fixed + bi * 3
            for si, sub in enumerate(["T0", "TX", "shift"]):
                cname = f"{block}_{sub}"
                val = row.get(cname, "")
                if isinstance(val, float) and np.isnan(val):
                    val = ""

                # 选格式
                # 检查当前格是否超限
                is_over = any(
                    ov[0] == bi and ov[1] == si and ov[2][r_idx]
                    for ov in col_overlimit
                )
                if is_over and is_yellow:
                    fmt = FMT_YELLOW_RED
                elif is_over:
                    fmt = FMT_RED_BOLD
                elif is_yellow:
                    fmt = FMT_YELLOW
                else:
                    fmt = FMT_NORMAL

                ws.write(r, base_col + si, val, fmt)

    # ── 冻结窗格 ──
    ws.freeze_panes(data_start, n_fixed)

    # ── 列宽 ──
    ws.set_column(0, total_cols - 1, 12)

    wb.close()
    if progress:
        progress.advance("导出完成")


# ═══════════════════════════════════════════════════════════════
#  5. 主流程
# ═══════════════════════════════════════════════════════════════

def run_compare(
    merged_df: pd.DataFrame,
    calc_config: dict,
    raw_headers: Optional[dict] = None,
    output_path: str = "对比结果.xlsx",
    progress: Optional[Any] = None,
) -> str:
    if progress:
        progress.set_total(5)

    if progress:
        progress.advance("重命名转换...")
    df = transform_rename(merged_df, calc_config)

    if progress:
        progress.advance("计算 shift...")
    result = calc_shifts(df, calc_config)
    if result.empty:
        raise ValueError("无有效数据可计算（缺少 T0 或 TX 数据）")

    if progress:
        progress.advance("导出 Excel...")
    export_excel(result, calc_config, raw_headers=raw_headers,
                 output_path=output_path, progress=progress)

    if progress:
        progress.advance("对比完成")
    return output_path
