"""
对比文件核心逻辑：转换重命名 → Shift 计算 → Excel 导出。
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

    calc_config 格式:
        {
            "renames": {"原名": "新名"},
            "suffixes": {"原名": "后缀"},
        }

    返回:
        转换后的 DataFrame（列名无重复）
    """
    rename_map = calc_config.get("renames", {})
    suffix_map = calc_config.get("suffixes", {})

    # 找出 MV1 项目
    new_name_counts: dict[str, list[str]] = {}
    for orig, new in rename_map.items():
        new_name_counts.setdefault(new, []).append(orig)
    mv1_groups = {new: origs for new, origs in new_name_counts.items() if len(origs) > 1}

    # 构建最终列集合
    fixed_cols = {"PART_ID", "SOFT_BIN", "group", "filepath"}
    test_cols = [c for c in df.columns if c not in fixed_cols]
    all_new_cols = set(df.columns)
    for orig, new in rename_map.items():
        if orig in all_new_cols:
            all_new_cols.discard(orig)
            all_new_cols.add(new)
    all_new_cols = sorted(all_new_cols)

    new_rows = []
    for _, row in df.iterrows():
        base_row = {col: np.nan for col in all_new_cols}
        for c in fixed_cols:
            if c in row:
                base_row[c] = row[c]

        for col in test_cols:
            val = row.get(col, np.nan)
            if pd.isna(val):
                continue
            if col in rename_map:
                new_name = rename_map[col]
                if new_name in mv1_groups:
                    suffix = suffix_map.get(col, "")
                    if suffix:
                        nr = base_row.copy()
                        nr["PART_ID"] = f"{base_row['PART_ID']}_{suffix}"
                        nr[new_name] = val
                        new_rows.append(nr)
                else:
                    base_row[new_name] = val
            else:
                if col in all_new_cols:
                    base_row[col] = val
        new_rows.append(base_row)

    result = pd.DataFrame(new_rows)
    for col in all_new_cols:
        if col not in result.columns:
            result[col] = np.nan
    return result[all_new_cols]


# ═══════════════════════════════════════════════════════════════
#  2. Shift 计算
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


def calc_shifts(df: pd.DataFrame, calc_config: dict) -> pd.DataFrame:
    formulas = calc_config.get("formulas", {})
    if not formulas:
        return pd.DataFrame()

    df_t0 = df[df["group"] == "T0"].copy()
    df_tx = df[df["group"] != "T0"].copy()
    if df_t0.empty or df_tx.empty:
        return pd.DataFrame()

    rename_map = calc_config.get("renames", {})
    test_cols = set()
    for orig_name in formulas:
        final_name = rename_map.get(orig_name, orig_name)
        test_cols.add(final_name)
    test_cols = sorted(test_cols - {"PART_ID", "SOFT_BIN", "group", "filepath"})

    t0_cols = ["PART_ID"] + [c for c in test_cols if c in df_t0.columns]
    t0_vals = df_t0[t0_cols].drop_duplicates(subset="PART_ID").set_index("PART_ID")

    rows = []
    for _, tx_row in df_tx.iterrows():
        pid = tx_row["PART_ID"]
        row = {
            "PART_ID": pid,
            "SOFT_BIN": tx_row.get("SOFT_BIN", ""),
            "GROUP": tx_row["group"],
            "file": tx_row.get("filepath", ""),
        }
        for col in test_cols:
            tx_val = tx_row.get(col, np.nan)
            t0_val = t0_vals.loc[pid, col] if pid in t0_vals.index and col in t0_vals.columns else np.nan
            orig_name = next((k for k, v in rename_map.items() if v == col), col)
            formula = formulas.get(orig_name, "")
            shift_val = safe_eval_formula(formula, t0_val, tx_val) if formula else np.nan
            row[f"{col}_T0"] = t0_val
            row[f"{col}_TX"] = tx_val
            row[f"{col}_shift"] = shift_val
        rows.append(row)

    result = pd.DataFrame(rows)
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
#  4. Excel 导出（含格式）
# ═══════════════════════════════════════════════════════════════

def export_excel(
    data: pd.DataFrame,
    calc_config: dict,
    raw_headers: Optional[dict] = None,
    output_path: str = "对比结果.xlsx",
    progress: Optional[Any] = None,
):
    """导出 Excel，格式如示例。

    结构：
    行1: PART_ID | SOFT_BIN | GROUP | file | 测试项1(合并3列) | 测试项2(合并3列) | ...
    行2:         |         |       |      | unit | uA |   | unit | nA | ...
    行3:         |         |       |      | lower limit | 0 | | lower limit | 0 | ...
    行4:         |         |       |      | higher limit | 100 | | higher limit | 100 | ...
    行5:         |         |       |      | shift limit | 0.1 | | shift limit | 0.1 | ...
    行6:         |         |       |      | shift公式 | abs(T0/TX) | | shift公式 | abs(T0/TX) | ...
    行7:         |         |       |      | T0 | TX | shift | T0 | TX | shift | ...
    行8+: 数据
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    limits = calc_config.get("limits", {})
    directions = calc_config.get("directions", {})
    formulas = calc_config.get("formulas", {})
    rename_map = calc_config.get("renames", {})

    if progress:
        progress.set_status("构建 Excel...")

    wb = Workbook()
    ws = wb.active
    ws.title = "对比结果"

    # 确定测试项（按原始列名排序）
    fixed_cols = ["PART_ID", "SOFT_BIN", "GROUP", "file"]
    test_blocks = sorted(set(
        c.rsplit("_", 1)[0] for c in data.columns if c not in fixed_cols
    ))

    # 每个测试项占 3 列
    total_cols = len(fixed_cols) + len(test_blocks) * 3

    # ── 样式定义 ──
    header_font = Font(bold=True, size=10)
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    def write_cell(r, c, val, font=None, fill=None, align=None):
        cell = ws.cell(row=r, column=c, value=val)
        cell.font = font or Font(size=10)
        cell.alignment = align or center_align
        cell.border = thin_border
        if fill:
            cell.fill = fill
        return cell

    # ── 第1行：测试项名称（合并 3 列） ──
    for ci, col in enumerate(fixed_cols, 1):
        write_cell(1, ci, col, font=header_font)
    for bi, block in enumerate(test_blocks):
        start = len(fixed_cols) + bi * 3 + 1
        end = start + 2
        ws.merge_cells(start_row=1, start_column=start, end_row=1, end_column=end)
        write_cell(1, start, block, font=header_font)

    # ── 第2-7行：元信息 ──
    meta_labels = ["unit", "lower limit", "higher limit", "shift limit",
                   "limit side", "shift公式"]
    for mi, label in enumerate(meta_labels):
        r = mi + 2
        for ci in range(1, len(fixed_cols) + 1):
            write_cell(r, ci, "", font=Font(size=9, color="999999"))
        for bi, block in enumerate(test_blocks):
            start = len(fixed_cols) + bi * 3 + 1
            orig = next((k for k, v in rename_map.items() if v == block), block)
            if mi == 0:
                val = raw_headers.get(orig, {}).get("unit", "") if raw_headers else ""
            elif mi == 1:
                val = raw_headers.get(orig, {}).get("lo", "") if raw_headers else ""
            elif mi == 2:
                val = raw_headers.get(orig, {}).get("hi", "") if raw_headers else ""
            elif mi == 3:
                val = limits.get(orig, "")
            elif mi == 4:
                val = directions.get(orig, "upper")
            elif mi == 5:
                val = formulas.get(orig, "")
            write_cell(r, start, label, font=Font(size=9, color="666666"))
            write_cell(r, start + 1, val, font=Font(size=10))
            write_cell(r, start + 2, "", font=Font(size=9, color="999999"))

    # ── 第8行：子表头 T0 / TX / shift ──
    header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    for ci, col in enumerate(fixed_cols, 1):
        write_cell(8, ci, col, font=header_font, fill=header_fill)
    for bi, block in enumerate(test_blocks):
        start = len(fixed_cols) + bi * 3 + 1
        for si, sub in enumerate(["T0", "TX", "shift"]):
            write_cell(8, start + si, sub, font=header_font, fill=header_fill)

    # ── 第9行起：数据 ──
    red_bold = Font(bold=True, color="FF0000", size=10)
    yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    data_start = 9
    for r_idx, (_, row) in enumerate(data.iterrows()):
        r = data_start + r_idx
        # 检查是否有任何 shift 超限 → 整行标黄
        row_has_overlimit = False
        for bi, block in enumerate(test_blocks):
            shift_val = row.get(f"{block}_shift", np.nan)
            orig = next((k for k, v in rename_map.items() if v == block), block)
            limit_val = limits.get(orig)
            direction = directions.get(orig, "upper")
            if limit_val and isinstance(shift_val, (int, float)) and not np.isnan(shift_val):
                try:
                    if (direction == "lower" and float(shift_val) < float(limit_val)) or \
                       (direction == "upper" and float(shift_val) > float(limit_val)):
                        row_has_overlimit = True
                        break
                except (ValueError, TypeError):
                    pass
        row_fill = yellow_fill if row_has_overlimit else None

        for ci, col in enumerate(fixed_cols, 1):
            val = row.get(col, "")
            if isinstance(val, float) and np.isnan(val):
                val = ""
            write_cell(r, ci, val, fill=row_fill)
        for bi, block in enumerate(test_blocks):
            for si, sub in enumerate(["T0", "TX", "shift"]):
                cname = f"{block}_{sub}"
                val = row.get(cname, "")
                cell_val = val
                if isinstance(val, float) and np.isnan(val):
                    cell_val = ""
                c = len(fixed_cols) + bi * 3 + si + 1
                cell = write_cell(r, c, cell_val, fill=row_fill)

                # shift 列超限标红加粗
                if sub == "shift":
                    orig = next((k for k, v in rename_map.items() if v == block), block)
                    limit_val = limits.get(orig)
                    direction = directions.get(orig, "upper")
                    if limit_val and isinstance(val, (int, float)) and not np.isnan(val):
                        try:
                            lv = float(limit_val)
                            if (direction == "lower" and val < lv) or (direction == "upper" and val > lv):
                                cell.font = red_bold
                        except (ValueError, TypeError):
                            pass

    # ── 冻结窗格 ──
    ws.freeze_panes = ws.cell(row=data_start, column=len(fixed_cols) + 1)

    # ── 列宽 ──
    for ci in range(1, total_cols + 1):
        ws.column_dimensions[get_column_letter(ci)].width = 12

    # ── 确保输出目录存在 ──
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    wb.save(output_path)
    wb.close()  # 释放文件锁，Windows 上必须
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
