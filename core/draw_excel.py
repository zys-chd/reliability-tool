"""
绘制 Excel — 生成统计汇总 + 分组/测试项明细 Excel 文件。

注意：T0 数据来自合并（merged）结果文件，而非直接从原始 CSV 读取。
写入 Excel 中的 T0 值来源于对比文件（该文件由合并文件生成），
但原始数据源头为合并结果。

结构：
  - Summary sheet：plot config + calc config + 分组统计 + 原始对比数据
  - 按 group_by 模式：
    * group_by="item"（按分组名分组）：每个分组一个 sheet
      PART_ID | SOFT_BIN | group | file | T0 | TX | shift | CDF | ln(-ln(1-F))
    * group_by="group"（按测试项分组）：每个测试项一个 sheet
      PART_ID | SOFT_BIN | group | file | T0 | TX | shift |
      per group: T0_CDF | T0_ln | TX_CDF | TX_ln | shift_CDF | shift_ln
  右侧嵌入 openpyxl ScatterChart 原生图表
"""

import logging
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from openpyxl.chart import ScatterChart, Reference, Series
from openpyxl.chart.label import DataLabelList

logger = logging.getLogger("draw_excel")

# Mapping of suffix -> display label
SUFFIX_LABEL = {"_T0": "T0", "_TX": "TX", "_shift": "shift"}
DRAW_KEYS = {"_T0": "draw_t0", "_TX": "draw_tx", "_shift": "draw_shift"}


# ═══════════════════════════════════════════════════════════════
#  Weibull 拟合（最小二乘 / 中位秩回归）
# ═══════════════════════════════════════════════════════════════


def fit_weibull(values: np.ndarray) -> tuple[float, float, float]:
    """2-参数 Weibull 拟合，返回 (β, η, R²)。

    使用中位秩回归（Median Rank Regression）：
      - 中位秩: (i - 0.4) / (n + 0.3)
      - x = ln(values), y = ln(-ln(1 - median_rank))
      - 线性回归得到 β (斜率) 和 η = exp(-intercept/slope)

    参数
    ----------
    values : np.ndarray
        需要拟合的数值（shift 值等）

    返回
    -------
    tuple[float, float, float]
        (β, η, R²)，若数据不足返回 (nan, nan, nan)
    """
    vals = np.array(values, dtype=float)
    vals = vals[np.isfinite(vals)]
    if len(vals) < 3:
        return np.nan, np.nan, np.nan

    sorted_vals = np.sort(vals)
    n = len(sorted_vals)
    ranks = np.arange(1, n + 1)

    # 中位秩（与 plotting.py 保持一致）
    median_rank = (ranks - 0.4) / (n + 0.3)
    median_rank = np.clip(median_rank, 1e-15, 1 - 1e-15)

    # Weibull 概率纸变换
    ln_x = np.log(sorted_vals)
    ln_y = np.log(-np.log(1 - median_rank))

    # 确保有限值
    mask = np.isfinite(ln_x) & np.isfinite(ln_y)
    ln_x = ln_x[mask]
    ln_y = ln_y[mask]

    if len(ln_x) < 3:
        return np.nan, np.nan, np.nan

    # 线性回归 y = a + b*x
    # b = β (形状参数), η = exp(-a/b)
    A = np.vstack([ln_x, np.ones_like(ln_x)]).T
    coeffs, residuals, _, _ = np.linalg.lstsq(A, ln_y, rcond=None)

    beta = coeffs[0]            # 斜率 = β (shape)
    intercept = coeffs[1]       # 截距
    eta = np.exp(-intercept / beta) if beta != 0 else np.nan

    # R²
    y_mean = np.mean(ln_y)
    ss_total = np.sum((ln_y - y_mean) ** 2)
    ss_res = np.sum((ln_y - (ln_x * beta + intercept)) ** 2)
    r_squared = 1 - ss_res / ss_total if ss_total > 0 else np.nan

    return float(beta), float(eta), float(r_squared)


def weibull_cdf(x: float, beta: float, eta: float) -> float:
    """Weibull 累积分布函数 F(x) = 1 - exp(-(x/η)^β)"""
    if beta <= 0 or eta <= 0 or x <= 0:
        return np.nan
    return 1.0 - np.exp(-((x / eta) ** beta))


# ═══════════════════════════════════════════════════════════════
#  统计量计算
# ═══════════════════════════════════════════════════════════════


def compute_statistics(values: np.ndarray) -> dict:
    """计算一组数值的统计量。

    返回: {mean, min, max, std, p75, p25, cv, n}
    """
    vals = np.array(values, dtype=float)
    vals = vals[np.isfinite(vals)]
    n = len(vals)

    if n == 0:
        return {"mean": np.nan, "min": np.nan, "max": np.nan,
                "std": np.nan, "p75": np.nan, "p25": np.nan,
                "cv": np.nan, "n": 0}

    mean = float(np.mean(vals))
    min_v = float(np.min(vals))
    max_v = float(np.max(vals))
    std = float(np.std(vals, ddof=1)) if n > 1 else 0.0
    p75 = float(np.percentile(vals, 75))
    p25 = float(np.percentile(vals, 25))
    cv = std / mean if mean != 0 else np.nan

    return {"mean": mean, "min": min_v, "max": max_v,
            "std": std, "p75": p75, "p25": p25,
            "cv": cv, "n": n}


# ═══════════════════════════════════════════════════════════════
#  CDF / Weibull 值计算（用于左侧数据列）
# ═══════════════════════════════════════════════════════════════


def calc_cdf_and_weibull_y(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """计算排序后的 CDF 和 ln(-ln(1-F)) 值"""
    sorted_vals = np.sort(values)
    n = len(sorted_vals)
    ranks = np.arange(1, n + 1)
    cdf = ranks / n

    median_rank = (ranks - 0.4) / (n + 0.3)
    median_rank = np.clip(median_rank, 1e-15, 1 - 1e-15)
    weibull_y = np.log(-np.log(1 - median_rank))

    return cdf, weibull_y


# ═══════════════════════════════════════════════════════════════
#  从对比数据中解析测试项列表
# ═══════════════════════════════════════════════════════════════


def _get_test_items(df: pd.DataFrame) -> list[str]:
    """从对比 DataFrame 中提取测试项名称列表。

    列名格式: {test_item}_T0, {test_item}_TX, {test_item}_shift
    """
    fixed = {"PART_ID", "SOFT_BIN", "GROUP", "file"}
    items = set()
    for col in df.columns:
        if col in fixed:
            continue
        # 匹配 _T0, _TX, _shift 后缀
        for suffix in ("_T0", "_TX", "_shift"):
            if col.endswith(suffix):
                item = col[: -len(suffix)]
                items.add(item)
                break
    return sorted(items)


# ═══════════════════════════════════════════════════════════════
#  data suffixes used (T0, TX, shift) — used across modes
# ═══════════════════════════════════════════════════════════════

_DATA_SUFFIXES = ["_T0", "_TX", "_shift"]

# Marker symbols for openpyxl ScatterChart (cycle per series)
_MARKER_SYMBOLS = ["circle", "diamond", "square", "triangle", "x",
                   "star", "dot", "diamond", "plus", "dash"]


def _make_marker(symbol: str, size: int):
    """Create an openpyxl Marker with a border stroke (width=size/4)."""
    from openpyxl.chart.marker import Marker
    from openpyxl.drawing.line import LineProperties
    m = Marker(symbol=symbol, size=size)
    if m.graphicalProperties is None:
        from openpyxl.chart.properties import GraphicalProperties
        m.graphicalProperties = GraphicalProperties()
    m.graphicalProperties.line = LineProperties()
    m.graphicalProperties.line.width = int(max(size / 4, 1) * 12700)
    return m


def _get_data_cols(test_item: str) -> list[str]:
    """Return [testitem_T0, testitem_TX, testitem_shift]"""
    return [f"{test_item}{suffix}" for suffix in _DATA_SUFFIXES]


# ═══════════════════════════════════════════════════════════════
#  主导出函数
# ═══════════════════════════════════════════════════════════════


def export_draw_excel(
    compare_path: str,
    output_path: str,
    plot_config: dict,
    calc_config: dict,
    progress: Optional[Any] = None,
) -> str:
    """生成绘制 Excel 文件（统计汇总 + 分组明细 + 嵌入图表）。

    注意：T0 数据来源于合并结果（merged）文件。对比文件中的 T0 值
    由合并结果经计算生成，写入此 Excel 中的 T0 值取自对比文件内容。

    步骤
    ----
    1. 读取对比文件
    2. 对每个测试项 × 分组计算统计量
    3. 创建 Summary sheet：plot config → 统计表 → 原始数据
    4. 按 group_by 模式创建明细 sheets：
       - group_by="group"：每个测试项一个 sheet，内部按组分列
       - group_by="item"：每个分组一个 sheet（原行为）
    5. 使用 openpyxl 原生 ScatterChart 嵌入图表

    参数
    ----
    compare_path : str
        对比文件路径（由 compare.py 生成）
    output_path : str
        输出 Excel 路径
    plot_config : dict
        绘图配置（cols, rows, scale, limit 等）
    calc_config : dict
        计算配置（formulas, limits, renames 等）
    progress : ProgressReporter, optional
        进度报告器

    返回
    ----
    str
        输出文件路径
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
    from openpyxl.utils import get_column_letter

    # 读取对比文件
    if progress:
        progress.set_status("读取对比文件...")
    from core.plotting import read_compare_file

    df = read_compare_file(compare_path)
    if df.empty:
        raise ValueError("对比文件无数据")

    test_items = _get_test_items(df)
    if not test_items:
        raise ValueError("对比文件中未找到测试项数据")

    if progress:
        progress.set_status("解析分组和测试项...")

    groups = sorted(df["GROUP"].unique())
    group_by = plot_config.get("group_by", "item")

    # 计算总步骤数 — 必须匹配所有 progress.advance() 调用次数
    if group_by == "group":
        # stats: each test_item x group; sheets: each test_item; charts: each test_item x group; save: 1
        total_steps = len(test_items) * len(groups) + len(test_items) + len(test_items) * len(groups) + 1
    else:
        # stats: each test_item x group; sheets: each group; charts: each group; save: 1
        total_steps = len(test_items) * len(groups) + len(groups) + len(groups) + 1
    if progress:
        progress.set_total(total_steps)

    # 样式
    header_font = Font(bold=True, size=11)
    title_font = Font(bold=True, size=13)
    normal_font = Font(size=10)
    small_font = Font(size=9, color="666666")
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    light_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")

    def _write_cell(ws, r, c, val, font=None, fill=None, align=None):
        cell = ws.cell(row=r, column=c, value=val)
        cell.font = font or normal_font
        cell.alignment = align or center_align
        cell.border = thin_border
        if fill:
            cell.fill = fill
        return cell

    wb = Workbook()

    # ══════════════════════════════════════════════════════════
    #  Sheet 1: Summary
    # ══════════════════════════════════════════════════════════
    ws_summary = wb.active
    ws_summary.title = "Summary"

    row = 1

    # --- Plot config 快照 ---
    _write_cell(ws_summary, row, 1, "绘图配置 (Plot Config)", font=title_font)
    row += 1
    config_keys = [
        "cols", "rows", "y_mode", "x_scale", "y_scale",
        "marker_size", "theme", "show_limit_line",
        "group_by", "x_label",
        "x_min", "x_max", "y_min", "y_max",
        "plot_type",
    ]
    for key in config_keys:
        val = plot_config.get(key, "")
        _write_cell(ws_summary, row, 1, key, font=header_font, align=left_align)
        _write_cell(ws_summary, row, 2, str(val), align=left_align)
        row += 1

    # Draw flags
    draw_t0 = plot_config.get("draw_t0", True)
    draw_tx = plot_config.get("draw_tx", True)
    draw_shift = plot_config.get("draw_shift", True)
    _write_cell(ws_summary, row, 1, "draw_t0", font=header_font, align=left_align)
    _write_cell(ws_summary, row, 2, str(draw_t0), align=left_align)
    row += 1
    _write_cell(ws_summary, row, 1, "draw_tx", font=header_font, align=left_align)
    _write_cell(ws_summary, row, 2, str(draw_tx), align=left_align)
    row += 1
    _write_cell(ws_summary, row, 1, "draw_shift", font=header_font, align=left_align)
    _write_cell(ws_summary, row, 2, str(draw_shift), align=left_align)
    row += 1

    # Test items list
    _write_cell(ws_summary, row, 1, "测试项列表 (Test Items)", font=header_font, align=left_align)
    _write_cell(ws_summary, row, 2, ", ".join(test_items), align=left_align)
    row += 1
    row += 1  # 空行分隔

    # --- Calc config 快照 ---
    _write_cell(ws_summary, row, 1, "计算配置 (Calc Config)", font=title_font)
    row += 1
    calc_config_keys = ["formulas", "limits", "directions", "renames"]
    for key in calc_config_keys:
        val = calc_config.get(key, {})
        val_str = str(val)
        _write_cell(ws_summary, row, 1, key, font=header_font, align=left_align)
        _write_cell(ws_summary, row, 2, val_str, align=left_align)
        row += 1
    row += 1  # 空行分隔

    # --- 统计数据表头 ---
    # PASS count inserted before n
    stat_headers = [
        "测试项", "分组", "PASS", "n", "Mean", "Min", "Max",
        "Std", "75%", "25%", "CV",
        "β (Weibull)", "η (Weibull)", "R²",
        "Limit", "F(Limit)",
    ]
    _write_cell(ws_summary, row, 1, "分组统计数据", font=title_font)
    row += 1
    for ci, h in enumerate(stat_headers, 1):
        _write_cell(ws_summary, row, ci, h, font=header_font, fill=header_fill)
    row += 1

    # 收集各组 limit 配置
    rename_map = calc_config.get("renames", {})
    calc_limits = calc_config.get("limits", {})
    calc_directions = calc_config.get("directions", {})

    # Determine which suffixes to include based on draw flags
    active_suffixes = []
    suffix_to_label = {"_T0": "T0", "_TX": "TX", "_shift": "shift"}
    if plot_config.get("draw_t0", True):
        active_suffixes.append("_T0")
    if plot_config.get("draw_tx", True):
        active_suffixes.append("_TX")
    if plot_config.get("draw_shift", True):
        active_suffixes.append("_shift")

    step_count = 0
    for test_item in test_items:
        limit_orig = next((k for k, v in rename_map.items() if v == test_item), test_item)
        limit_val = calc_limits.get(limit_orig)

        for grp in groups:
            if progress and progress.cancelled:
                return ""
            step_count += 1
            if progress:
                progress.advance(step=1, status=f"计算统计: {test_item} / {grp}")

            mask = df["GROUP"] == grp
            group_df = df[mask]

            # Use shift column for statistics (backward compatible)
            shift_col = f"{test_item}_shift"
            shift_vals = group_df[shift_col].dropna().values if shift_col in group_df.columns else np.array([])
            if len(shift_vals) == 0:
                continue

            stats = compute_statistics(shift_vals)
            beta, eta, r2 = fit_weibull(shift_vals)

            # PASS count: rows with SOFT_BIN==1 in this group
            pass_count = 0
            if "SOFT_BIN" in group_df.columns:
                pass_count = int(group_df["SOFT_BIN"].dropna().eq(1).sum())

            # CDF at limit
            limit_num = None
            if limit_val is not None:
                try:
                    limit_num = float(limit_val)
                except (ValueError, TypeError):
                    pass
            f_at_limit = weibull_cdf(limit_num, beta, eta) if (
                limit_num is not None and np.isfinite(beta) and np.isfinite(eta)
            ) else np.nan

            _write_cell(ws_summary, row, 1, test_item)
            _write_cell(ws_summary, row, 2, grp)
            _write_cell(ws_summary, row, 3, pass_count)       # PASS
            _write_cell(ws_summary, row, 4, stats["n"])       # n
            _write_cell(ws_summary, row, 5, _fmt(stats["mean"]))
            _write_cell(ws_summary, row, 6, _fmt(stats["min"]))
            _write_cell(ws_summary, row, 7, _fmt(stats["max"]))
            _write_cell(ws_summary, row, 8, _fmt(stats["std"]))
            _write_cell(ws_summary, row, 9, _fmt(stats["p75"]))
            _write_cell(ws_summary, row, 10, _fmt(stats["p25"]))
            _write_cell(ws_summary, row, 11, _fmt(stats["cv"]))
            _write_cell(ws_summary, row, 12, _fmt(beta))
            _write_cell(ws_summary, row, 13, _fmt(eta))
            _write_cell(ws_summary, row, 14, _fmt(r2))
            _write_cell(ws_summary, row, 15, _fmt(limit_num))
            _write_cell(ws_summary, row, 16, _fmt(f_at_limit))
            row += 1

    row += 2  # 空行

    # --- 原始对比数据 ---
    _write_cell(ws_summary, row, 1, "原始对比数据", font=title_font)
    row += 1

    # 写列头
    compare_cols = list(df.columns)
    for ci, col in enumerate(compare_cols, 1):
        _write_cell(ws_summary, row, ci, col, font=header_font, fill=header_fill)
    row += 1

    # 写数据
    for _, row_data in df.iterrows():
        for ci, col in enumerate(compare_cols, 1):
            val = row_data.get(col, "")
            if isinstance(val, float) and np.isnan(val):
                val = ""
            _write_cell(ws_summary, row, ci, val)
        row += 1

    # 列宽调整
    ws_summary.column_dimensions["A"].width = 22
    ws_summary.column_dimensions["B"].width = 22
    for ci in range(3, 17):
        ws_summary.column_dimensions[get_column_letter(ci)].width = 14

    # ══════════════════════════════════════════════════════════
    #  Detail sheets — mode depends on group_by
    # ══════════════════════════════════════════════════════════

    if group_by == "group":
        _write_group_mode_sheets(
            wb, df, test_items, groups, active_suffixes,
            plot_config, calc_config, progress, step_count,
            header_font, normal_font, center_align, thin_border,
            header_fill, _write_cell,
        )
    else:
        _write_item_mode_sheets(
            wb, df, test_items, groups, active_suffixes,
            plot_config, calc_config, progress, step_count,
            header_font, normal_font, center_align, thin_border,
            header_fill, _write_cell,
        )

    # 保存
    if progress:
        progress.set_status("保存 Excel...")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    wb.close()

    if progress:
        progress.advance(step=1, status="Excel 绘制完成")

    logger.info(f"绘制 Excel 完成: {output_path}")
    return output_path


# ═══════════════════════════════════════════════════════════════
#  group_by="item" mode — one sheet per group (original behavior)
# ═══════════════════════════════════════════════════════════════


def _write_item_mode_sheets(
    wb, df, test_items, groups, active_suffixes,
    plot_config, calc_config, progress, step_count,
    header_font, normal_font, center_align, thin_border,
    header_fill, _write_cell,
):
    """Original mode: one sheet per GROUP. Columns per test item:
    PART_ID | SOFT_BIN | GROUP | file | T0 | TX | shift | CDF | ln(-ln(1-F))
    Openpyxl native ScatterChart embedded on the right.
    """
    from openpyxl.utils import get_column_letter
    from openpyxl.chart import ScatterChart, Reference, Series

    for grp in groups:
        if progress and progress.cancelled:
            return
        step_count += 1
        if progress:
            progress.advance(step=1, status=f"创建分组 sheet: {grp}")

        mask = df["GROUP"] == grp
        group_df = df[mask].copy()

        ws = wb.create_sheet(title=str(grp)[:31])

        # Left columns
        left_cols = ["PART_ID", "SOFT_BIN", "GROUP", "file"]

        # Collect data columns for this group
        data_cols = []
        for item in test_items:
            for suffix in active_suffixes:
                col = f"{item}{suffix}"
                if col in group_df.columns:
                    data_cols.append(col)

        # Headers
        all_left_headers = left_cols + data_cols + ["CDF", "ln(-ln(1-F))"]
        for ci, h in enumerate(all_left_headers, 1):
            _write_cell(ws, 1, ci, h, font=header_font, fill=header_fill)

        # Collect shift values for CDF computation
        all_shift_vals = []
        for item in test_items:
            sc = f"{item}_shift"
            if sc in group_df.columns:
                sv = group_df[sc].dropna().values
                all_shift_vals.extend(sv)
        all_shift_vals = np.array(all_shift_vals)
        all_shift_vals = all_shift_vals[np.isfinite(all_shift_vals)]

        # Compute CDF and Weibull Y (based on sorted shift values)
        cdf_vals = None
        weibull_y_vals = None
        if len(all_shift_vals) >= 1:
            cdf_vals, weibull_y_vals = calc_cdf_and_weibull_y(all_shift_vals)

        # Sort by first shift column
        first_shift_col = None
        for item in test_items:
            sc = f"{item}_shift"
            if sc in group_df.columns:
                first_shift_col = sc
                break

        if first_shift_col:
            group_df = group_df.sort_values(first_shift_col, na_position="last").reset_index(drop=True)
        else:
            group_df = group_df.reset_index(drop=True)

        # Write data
        for r_idx, (_, row_data) in enumerate(group_df.iterrows()):
            excel_row = r_idx + 2
            ci = 1
            for col in left_cols:
                val = row_data.get(col, "")
                if isinstance(val, float) and np.isnan(val):
                    val = ""
                _write_cell(ws, excel_row, ci, val)
                ci += 1
            for col in data_cols:
                val = row_data.get(col, "")
                if isinstance(val, float) and np.isnan(val):
                    val = ""
                _write_cell(ws, excel_row, ci, val)
                ci += 1
            # CDF and Weibull Y — write as raw float so Excel charts can read them
            if cdf_vals is not None and r_idx < len(cdf_vals):
                _write_cell(ws, excel_row, ci, float(cdf_vals[r_idx]))
                ci += 1
                _write_cell(ws, excel_row, ci, float(weibull_y_vals[r_idx]))
            else:
                _write_cell(ws, excel_row, ci, "")
                ci += 1
                _write_cell(ws, excel_row, ci, "")

        # Embed openpyxl ScatterChart
        step_count = _embed_item_mode_chart(
            ws, group_df, test_items, grp, data_cols,
            all_left_headers, cdf_vals, plot_config, calc_config,
            step_count, progress, _write_cell, header_font, header_fill,
        )

        # Column widths
        for ci in range(1, len(all_left_headers) + 1):
            ws.column_dimensions[get_column_letter(ci)].width = 14

        # Comment on T0 source
        try:
            from openpyxl.comments import Comment
            comment = Comment("注意: T0 数据源自合并(merged)结果文件", "System")
            comment.width = 300
            comment.height = 50
            for ci, h in enumerate(all_left_headers, 1):
                if h.endswith("_T0"):
                    ws.cell(row=1, column=ci).comment = comment
                    break
        except ImportError:
            pass


def _embed_item_mode_chart(
    ws, group_df, test_items, grp, data_cols,
    all_left_headers, cdf_vals, plot_config, calc_config,
    step_count, progress, _write_cell, header_font, header_fill,
):
    """Embed openpyxl ScatterChart for item_mode sheet.
    Uses shift_CDF vs shift data from the sheet already written."""
    from openpyxl.chart import ScatterChart, Reference, Series

    if progress and progress.cancelled:
        return step_count

    # Find first test item with shift data
    chart_item = None
    for item in test_items:
        sc = f"{item}_shift"
        if sc in group_df.columns and group_df[sc].dropna().shape[0] >= 2:
            chart_item = item
            break

    if not chart_item:
        return step_count

    step_count += 1
    if progress:
        progress.advance(step=1, status=f"嵌入图表: {grp}")

    shift_col = f"{chart_item}_shift"
    shift_data = group_df[shift_col].dropna()
    num_points = len(shift_data)

    if num_points < 2:
        return step_count

    # Find column indices in the sheet
    # CDF is the 2nd-to-last header, ln is last
    # shift column is somewhere in data_cols
    cdf_col_idx = len(all_left_headers) - 1  # CDF column
    ln_col_idx = len(all_left_headers)       # ln(-ln(1-F)) column

    # Find shift column index
    shift_col_idx = None
    for ci, h in enumerate(all_left_headers, 1):
        if h == shift_col:
            shift_col_idx = ci
            break

    if shift_col_idx is None or cdf_col_idx is None:
        return step_count

    # Data starts at row 2
    data_start_row = 2
    data_end_row = 1 + num_points

    # Determine plot configs
    y_mode = plot_config.get("y_mode", "cdf")
    plot_type = plot_config.get("plot_type", "markers")
    x_scale = plot_config.get("x_scale", "linear")
    y_scale = plot_config.get("y_scale", "linear")
    marker_size = int(plot_config.get("marker_size", 6))
    line_width = int(plot_config.get("line_width", 2))
    x_label = plot_config.get("x_label", chart_item)
    # Resolve %formula% in x_label
    calc_formulas = calc_config.get("formulas", {})
    formula = calc_formulas.get(chart_item, "")
    if formula and "%formula%" in x_label:
        x_label = x_label.replace("%formula%", formula)

    y_col_idx = cdf_col_idx if str(y_mode).lower().startswith("cdf") else ln_col_idx
    y_label = "CDF" if str(y_mode).lower().startswith("cdf") else "ln(-ln(1-F))"

    from openpyxl.chart.marker import Marker

    # Item mode: only one group → one series → index 0
    marker_symbol = _MARKER_SYMBOLS[0 % len(_MARKER_SYMBOLS)]

    chart = ScatterChart()
    chart.title = f"{grp} - {chart_item}"
    chart.x_axis.title = y_label
    chart.y_axis.title = x_label
    chart.width = 18
    chart.height = 12

    # Log scale — swapped per user feedback
    if y_scale == "log":
        chart.x_axis.scaling.logBase = 10
    if x_scale == "log":
        chart.y_axis.scaling.logBase = 10

    # Data series
    if num_points > 0 and data_end_row >= data_start_row:
        x_ref = Reference(ws, min_col=shift_col_idx, min_row=data_start_row, max_row=data_end_row)
        y_ref = Reference(ws, min_col=y_col_idx, min_row=data_start_row, max_row=data_end_row)
        series = Series(y_ref, x_ref, title="shift")

        if plot_type == "lines":
            series.graphicalProperties.line.noFill = False
            series.graphicalProperties.line.width = line_width * 12700
            series.marker = None
        elif plot_type == "markers+lines":
            series.graphicalProperties.line.noFill = False
            series.graphicalProperties.line.width = line_width * 12700
            series.marker = _make_marker(symbol=marker_symbol, size=marker_size)
        else:  # "markers" (default)
            series.graphicalProperties.line.noFill = True
            series.marker = _make_marker(symbol=marker_symbol, size=marker_size)

        chart.series.append(series)

    # Limit line
    _add_limit_line_to_chart(chart, ws, chart_item, plot_config, calc_config,
                             data_start_row, data_end_row, shift_col_idx, y_col_idx)

    # Place chart
    chart_col = len(all_left_headers) + 3
    ws.add_chart(chart, f"{get_column_letter(chart_col)}2")

    return step_count


# ═══════════════════════════════════════════════════════════════
#  group_by="group" mode — one sheet per TEST ITEM
# ═══════════════════════════════════════════════════════════════


def _write_group_mode_sheets(
    wb, df, test_items, groups, active_suffixes,
    plot_config, calc_config, progress, step_count,
    header_font, normal_font, center_align, thin_border,
    header_fill, _write_cell,
):
    """Group mode: one sheet per TEST ITEM.
    Columns: PART_ID | SOFT_BIN | GROUP | file | T0 | TX | shift | CDF | ln(-ln(1-F))
    CDF/ln computed per-group (based on shift values) within this test item.
    Openpyxl ScatterChart embedded to the right of data with one series per group.
    """
    from openpyxl.utils import get_column_letter

    for test_item in test_items:
        if progress and progress.cancelled:
            return
        step_count += 1
        if progress:
            progress.advance(step=1, status=f"创建测试项 sheet: {test_item}")

        data_cols = _get_data_cols(test_item)
        available_data_cols = [c for c in data_cols if c in df.columns]

        if not available_data_cols:
            continue

        ws = wb.create_sheet(title=str(test_item)[:31])

        left_cols = ["PART_ID", "SOFT_BIN", "GROUP", "file"]

        # Headers: left_cols + data_cols + CDF + ln (single columns, not per-group)
        all_headers = left_cols + available_data_cols + ["CDF", "ln(-ln(1-F))"]
        for ci, h in enumerate(all_headers, 1):
            _write_cell(ws, 1, ci, h, font=header_font, fill=header_fill)

        # Sort by GROUP so each group's rows are contiguous
        sheet_df = df.copy()
        if "GROUP" in sheet_df.columns:
            sheet_df = sheet_df.sort_values("GROUP").reset_index(drop=True)

        # Precompute per-group CDF/ln on shift values
        shift_col = f"{test_item}_shift"
        group_cdf_data: dict = {}  # grp -> (sorted_vals, cdf_vals, ln_vals)
        for grp in groups:
            mask = sheet_df["GROUP"] == grp
            grp_vals = sheet_df.loc[mask, shift_col].dropna().values if shift_col in sheet_df.columns else np.array([])
            grp_vals = grp_vals[np.isfinite(grp_vals)]
            if len(grp_vals) >= 1:
                cdf_vals, ln_vals = calc_cdf_and_weibull_y(grp_vals)
                sorted_grp = np.sort(grp_vals)
                group_cdf_data[grp] = (sorted_grp, cdf_vals, ln_vals)
            else:
                group_cdf_data[grp] = (np.array([]), np.array([]), np.array([]))

        # Write data rows
        for r_idx, (_, row_data) in enumerate(sheet_df.iterrows()):
            excel_row = r_idx + 2
            ci = 1
            # Left cols
            for col in left_cols:
                val = row_data.get(col, "")
                if isinstance(val, float) and np.isnan(val):
                    val = ""
                _write_cell(ws, excel_row, ci, val)
                ci += 1
            # Data cols (T0, TX, shift)
            for col in available_data_cols:
                val = row_data.get(col, "")
                if isinstance(val, float) and np.isnan(val):
                    val = ""
                _write_cell(ws, excel_row, ci, val)
                ci += 1
            # CDF and ln — computed per group, written for this row
            row_group = row_data.get("GROUP", "")
            sorted_grp, cdf_vals, ln_vals = group_cdf_data.get(row_group, (np.array([]), np.array([]), np.array([])))
            if len(cdf_vals) > 0:
                row_val = row_data.get(shift_col)
                if row_val is not None and not (isinstance(row_val, float) and np.isnan(row_val)):
                    idx = np.searchsorted(sorted_grp, row_val)
                    if idx < len(sorted_grp) and abs(sorted_grp[idx] - row_val) > 1e-12:
                        idx = idx - 1
                    idx = max(0, min(idx, len(cdf_vals) - 1))
                    _write_cell(ws, excel_row, ci, float(cdf_vals[idx]))
                    ci += 1
                    _write_cell(ws, excel_row, ci, float(ln_vals[idx]))
                    ci += 1
                else:
                    _write_cell(ws, excel_row, ci, "")
                    ci += 1
                    _write_cell(ws, excel_row, ci, "")
                    ci += 1
            else:
                _write_cell(ws, excel_row, ci, "")
                ci += 1
                _write_cell(ws, excel_row, ci, "")
                ci += 1

        # Embed charts per group for this test item
        step_count = _embed_group_mode_charts(
            ws, df, test_items, test_item, groups, active_suffixes,
            left_cols, available_data_cols, all_headers,
            plot_config, calc_config,
            step_count, progress, _write_cell, header_font, header_fill,
        )

        # Column widths
        for ci in range(1, len(all_headers) + 1):
            ws.column_dimensions[get_column_letter(ci)].width = 12

        # Comment on T0 source
        try:
            from openpyxl.comments import Comment
            comment = Comment("注意: T0 数据源自合并(merged)结果文件", "System")
            comment.width = 300
            comment.height = 50
            for ci, h in enumerate(all_headers, 1):
                if h.endswith("_T0"):
                    ws.cell(row=1, column=ci).comment = comment
                    break
        except ImportError:
            pass


def _embed_group_mode_charts(
    ws, df, test_items, test_item, groups, active_suffixes,
    left_cols, available_data_cols, all_headers,
    plot_config, calc_config,
    step_count, progress, _write_cell, header_font, header_fill,
):
    """Embed openpyxl ScatterChart for group_mode sheet.
    One chart with one series per group, referencing contiguous rows.
    Chart placed to the RIGHT of the data columns.
    """
    from openpyxl.utils import get_column_letter
    from openpyxl.chart import ScatterChart, Reference, Series

    if progress and progress.cancelled:
        return step_count

    # Determine plot configs
    y_mode = plot_config.get("y_mode", "cdf")
    plot_type = plot_config.get("plot_type", "markers")
    x_scale = plot_config.get("x_scale", "linear")
    y_scale = plot_config.get("y_scale", "linear")
    marker_size = int(plot_config.get("marker_size", 6))
    line_width = int(plot_config.get("line_width", 2))
    x_label = plot_config.get("x_label", test_item)
    calc_formulas = calc_config.get("formulas", {})
    formula = calc_formulas.get(test_item, "")
    if formula and "%formula%" in x_label:
        x_label = x_label.replace("%formula%", formula)

    y_label = "CDF" if str(y_mode).lower().startswith("cdf") else "ln(-ln(1-F))"

    from openpyxl.chart.marker import Marker

    # Sort by GROUP to match the sheet layout
    sheet_df = df.copy()
    if "GROUP" in sheet_df.columns:
        sheet_df = sheet_df.sort_values("GROUP").reset_index(drop=True)

    num_total_rows = len(sheet_df)

    # Column indices (1-indexed) in the sheet
    shift_col = f"{test_item}_shift"
    shift_col_idx = None
    for ci, h in enumerate(all_headers, 1):
        if h == shift_col:
            shift_col_idx = ci
            break

    cdf_col_idx = len(left_cols) + len(available_data_cols) + 1   # CDF column
    ln_col_idx = cdf_col_idx + 1                                     # ln column
    y_col_idx = cdf_col_idx if str(y_mode).lower().startswith("cdf") else ln_col_idx

    if shift_col_idx is None:
        return step_count

    # Create chart
    chart = ScatterChart()
    chart.title = f"{test_item}"
    chart.x_axis.title = y_label
    chart.y_axis.title = x_label
    chart.width = 18
    chart.height = 12

    # Log scale — swapped per user feedback
    if y_scale == "log":
        chart.x_axis.scaling.logBase = 10
    if x_scale == "log":
        chart.y_axis.scaling.logBase = 10

    series_added = 0
    row_offset = 2  # Data starts at row 2 (header is row 1)

    for grp in groups:
        mask = sheet_df["GROUP"] == grp
        num_points = mask.sum()
        if num_points < 2:
            row_offset += num_points
            continue

        step_count += 1
        if progress:
            progress.advance(step=1, status=f"嵌入图表: {test_item} / {grp}")

        data_start = row_offset
        data_end = row_offset + num_points - 1

        # Reference only this group's contiguous rows
        x_ref = Reference(ws, min_col=shift_col_idx, min_row=data_start, max_row=data_end)
        y_ref = Reference(ws, min_col=y_col_idx, min_row=data_start, max_row=data_end)
        series = Series(y_ref, x_ref, title=str(grp))

        # Cycle marker symbol per series
        mi = series_added % len(_MARKER_SYMBOLS)
        sym = _MARKER_SYMBOLS[mi]

        if plot_type == "lines":
            series.graphicalProperties.line.noFill = False
            series.graphicalProperties.line.width = line_width * 12700
            series.marker = None
        elif plot_type == "markers+lines":
            series.graphicalProperties.line.noFill = False
            series.graphicalProperties.line.width = line_width * 12700
            series.marker = _make_marker(symbol=sym, size=marker_size)
        else:  # "markers" (default)
            series.graphicalProperties.line.noFill = True
            series.marker = _make_marker(symbol=sym, size=marker_size)

        chart.series.append(series)
        series_added += 1
        row_offset += num_points

    if series_added == 0:
        return step_count

    # Limit line
    _add_limit_line_to_chart(chart, ws, test_item, plot_config, calc_config,
                             2, 1 + num_total_rows, shift_col_idx, y_col_idx)

    # Place chart to the RIGHT of data columns
    chart_col = len(all_headers) + 2
    ws.add_chart(chart, f"{get_column_letter(chart_col)}2")

    return step_count


# ═══════════════════════════════════════════════════════════════
#  Chart helpers
# ═══════════════════════════════════════════════════════════════


def _add_limit_line_to_chart(
    chart, ws, test_item, plot_config, calc_config,
    data_start_row, data_end_row, shift_col_idx, y_col_idx,
):
    """Add a vertical limit line to the chart using an extra series.
    Y-axis range is read from actual data values in y_col_idx column.
    """
    show_limit_line = plot_config.get("show_limit_line", False)
    if not show_limit_line:
        return

    calc_limits = calc_config.get("limits", {})
    rename_map = calc_config.get("renames", {})
    orig_name = next((k for k, v in rename_map.items() if v == test_item), test_item)
    limit_val = calc_limits.get(orig_name)
    if limit_val is None:
        return

    try:
        limit_num = float(limit_val)
    except (ValueError, TypeError):
        return

    # Create a two-point vertical line series at x=limit_num
    from openpyxl.chart import Series as ChartSeries

    # Scan the Y data column for actual min/max (skip header at row 1)
    y_min, y_max = 0.0, 1.0
    y_vals = []
    for r in range(data_start_row, data_end_row + 1):
        cell = ws.cell(row=r, column=y_col_idx).value
        if isinstance(cell, (int, float)):
            y_vals.append(cell)
    if len(y_vals) >= 2:
        y_min = min(y_vals)
        y_max = max(y_vals)
        # Add a small margin (5%) so the limit line doesn't lie on data endpoints
        margin = (y_max - y_min) * 0.05
        y_min -= margin
        y_max += margin

    # Write limit line data to two cells in a hidden area
    limit_col = 50  # far right column — AX

    try:
        ws.cell(row=1, column=limit_col, value=None)  # header placeholder
        ws.cell(row=2, column=limit_col, value=limit_num)
        ws.cell(row=2, column=limit_col + 1, value=y_min)
        ws.cell(row=3, column=limit_col, value=limit_num)
        ws.cell(row=3, column=limit_col + 1, value=y_max)

        limit_x_ref = Reference(ws, min_col=limit_col, min_row=2, max_row=3)
        limit_y_ref = Reference(ws, min_col=limit_col + 1, min_row=2, max_row=3)
        limit_series = ChartSeries(limit_y_ref, limit_x_ref, title="Limit")
        limit_series.graphicalProperties.line.dashStyle = "dash"
        limit_series.graphicalProperties.line.solidFill = "FF0000"
        chart.series.append(limit_series)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════


def _fmt(val: Any) -> str:
    """格式化数值用于 Excel 单元格"""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    if isinstance(val, float):
        if abs(val) < 0.0001 and val != 0:
            return f"{val:.6e}"
        return f"{val:.6g}"
    return str(val)



