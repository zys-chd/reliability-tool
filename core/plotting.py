"""
绘图核心逻辑 — plotly 散点图，支持 CDF / Weibull。
"""

import math
import re
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ═══════════════════════════════════════════════════════════════
#  数据读取
# ═══════════════════════════════════════════════════════════════

def read_compare_file(path: str) -> pd.DataFrame:
    """读取对比结果 Excel。

    格式：
    第1行：测试项名称（合并3列：T0/TX/shift）
    第2-7行：元信息
    第8行：子表头（PART_ID, SOFT_BIN, GROUP, file, T0, TX, shift, ...）
    第9行起：数据

    返回: 列名为 "{测试项}_T0", "{测试项}_TX", "{测试项}_shift" 的 DataFrame
    """
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active

    rows_iter = ws.iter_rows(values_only=True)
    all_rows = list(rows_iter)
    wb.close()

    if len(all_rows) < 8:
        return pd.DataFrame()

    # 第1行：测试项名称
    row1 = list(all_rows[0])
    # 第8行：子表头（索引7）
    row8 = list(all_rows[7])
    # 数据从第9行起
    data_rows = all_rows[8:]

    # 构建列名：合并 row1（测试项名）和 row8（T0/TX/shift）
    # row8 的第0-3列是固定列 (PART_ID, SOFT_BIN, GROUP, file)
    # 从第4列开始是 T0/TX/shift 交替
    fixed_cols = ["PART_ID", "SOFT_BIN", "GROUP", "file"]
    columns = list(fixed_cols)

    # 从第5列（索引4）开始构建测试列名
    item_name = None
    for i in range(4, len(row1)):
        test_name = str(row1[i]) if row1[i] else None
        sub = str(row8[i]) if row8[i] else ""
        if test_name and test_name != "None":
            item_name = test_name
        if sub and sub != "None":
            col_name = f"{item_name}_{sub}" if item_name else sub
            columns.append(col_name)
        else:
            columns.append(f"col_{i}")

    # 构建 DataFrame
    df = pd.DataFrame(data_rows, columns=columns[:len(data_rows[0])] if data_rows else columns)
    # 数值化
    for col in df.columns:
        if col not in fixed_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 解析元信息（第2-7行）
    meta = {}
    meta_labels = ["unit", "lower_limit", "higher_limit", "shift_limit", "limit_side", "shift_formula"]
    for mi, label in enumerate(meta_labels):
        if mi + 1 < len(all_rows):
            r = list(all_rows[mi + 1])
            item_name = None
            meta[label] = {}
            for i in range(4, min(len(r), len(row1))):
                tn = str(row1[i]) if row1[i] else None
                if tn and tn != "None":
                    item_name = tn
                if item_name:
                    val = r[i] if i < len(r) else None
                    if val is not None:
                        meta[label][item_name] = val

    df.attrs["meta"] = meta
    return df


# ═══════════════════════════════════════════════════════════════
#  CDF / Weibull 计算
# ═══════════════════════════════════════════════════════════════

def calc_cdf(values: np.ndarray) -> np.ndarray:
    sorted_vals = np.sort(values)
    n = len(sorted_vals)
    ranks = np.arange(1, n + 1)
    return ranks / n


def calc_weibull(values: np.ndarray) -> np.ndarray:
    sorted_vals = np.sort(values)
    n = len(sorted_vals)
    ranks = np.arange(1, n + 1)
    median_rank = (ranks - 0.4) / (n + 0.3)
    median_rank = np.clip(median_rank, 1e-15, 1 - 1e-15)
    return np.log(-np.log(1 - median_rank))


# ═══════════════════════════════════════════════════════════════
#  分组提取数据
# ═══════════════════════════════════════════════════════════════

MARKER_SYMBOLS = ["circle", "square", "diamond", "cross", "x",
                  "triangle-up", "triangle-down", "star", "hexagon",
                  "pentagon"]


def get_marker(idx: int) -> str:
    return MARKER_SYMBOLS[idx % len(MARKER_SYMBOLS)]


def get_tx_col(test_item: str, df: pd.DataFrame) -> str | None:
    """返回测试项的 TX 列名（如果有）。"""
    candidates = [c for c in df.columns if c.startswith(f"{test_item}_TX")]
    return candidates[0] if candidates else None


def get_t0_col(test_item: str, df: pd.DataFrame) -> str | None:
    """返回测试项的 T0 列名（如果有）。"""
    candidates = [c for c in df.columns if c.startswith(f"{test_item}_T0")]
    return candidates[0] if candidates else None


def get_shift_col(test_item: str, df: pd.DataFrame) -> str | None:
    """返回测试项的 shift 列名（如果有）。"""
    candidates = [c for c in df.columns if c.startswith(f"{test_item}_shift")]
    return candidates[0] if candidates else None


def _extract_one_trace(
    vals: np.ndarray,
    part_ids: np.ndarray,
    y_mode: str,
    name: str,
    suffix: str,
    soft_bins: np.ndarray | None = None,
    group_total: int = 0,
    group_fail: int = 0,
) -> dict:
    """提取单个 trace 的排序后数据字典。"""
    sort_idx = np.argsort(vals)
    sorted_vals = vals[sort_idx]
    sorted_pids = part_ids[sort_idx]
    sorted_bins = soft_bins[sort_idx] if soft_bins is not None else None
    n = len(sorted_vals)
    ranks = np.arange(1, n + 1)
    item_fail = sum(1 for b in sorted_bins if b != 1) if sorted_bins is not None else 0
    if y_mode == "cdf":
        y_vals = calc_cdf(sorted_vals)
    else:
        y_vals = calc_weibull(sorted_vals)
    return {
        "name": name,
        "_suffix": suffix,
        "x": sorted_vals.tolist(),
        "y": y_vals.tolist(),
        "n": n,
        "part_ids": sorted_pids.tolist(),
        "ranks": ranks.tolist(),
        "soft_bins": sorted_bins.tolist() if sorted_bins is not None else [],
        "group_total": group_total,
        "group_fail": group_fail,
        "item_fail": item_fail,
    }


def extract_traces_by_group(df: pd.DataFrame, test_item: str,
                            y_mode: str) -> list[dict]:
    """"每个 group 生成 3 条 trace：T0 / TX / shift，用不同 marker 区分。"""
    groups = df["GROUP"].unique()
    traces = []
    tx_col = get_tx_col(test_item, df)
    t0_col = get_t0_col(test_item, df)
    shift_col = get_shift_col(test_item, df)
    if not any([tx_col, t0_col, shift_col]):
        return traces
    for grp in sorted(groups):
        mask = df["GROUP"] == grp
        group_df = df[mask]
        group_total = len(group_df)
        group_fail = int(group_df["SOFT_BIN"].apply(lambda b: b != 1).sum())
        for col, suffix in [(t0_col, "T0"), (tx_col, "TX"), (shift_col, "shift")]:
            if not col:
                continue
            sub = df.loc[mask, [col, "PART_ID", "SOFT_BIN"]].dropna(subset=[col])
            vals = sub[col].values
            part_ids = sub["PART_ID"].values
            soft_bins = sub["SOFT_BIN"].values
            if len(vals) == 0:
                continue
            traces.append(
                _extract_one_trace(vals, part_ids, y_mode,
                                   name=f"{grp}_{suffix}", suffix=suffix,
                                   soft_bins=soft_bins,
                                   group_total=group_total, group_fail=group_fail)
            )
    return traces


def extract_traces_by_item(df: pd.DataFrame, group_name: str,
                           test_items: list[str], y_mode: str) -> list[dict]:
    """每个测试项（子图 = group）生成 3 条 trace：T0 / TX / shift，用不同 marker 区分。"""
    mask = df["GROUP"] == group_name
    group_df = df[mask]
    group_total = len(group_df)
    group_fail = int(group_df["SOFT_BIN"].apply(lambda b: b != 1).sum())
    traces = []
    for item in test_items:
        tx_col = get_tx_col(item, df)
        t0_col = get_t0_col(item, df)
        shift_col = get_shift_col(item, df)
        if not any([tx_col, t0_col, shift_col]):
            continue
        for col, suffix in [(t0_col, "T0"), (tx_col, "TX"), (shift_col, "shift")]:
            if not col:
                continue
            sub = df.loc[mask, [col, "PART_ID", "SOFT_BIN"]].dropna(subset=[col])
            vals = sub[col].values
            part_ids = sub["PART_ID"].values
            soft_bins = sub["SOFT_BIN"].values
            if len(vals) == 0:
                continue
            traces.append(
                _extract_one_trace(vals, part_ids, y_mode,
                                   name=f"{item}_{suffix}", suffix=suffix,
                                   soft_bins=soft_bins,
                                   group_total=group_total, group_fail=group_fail)
            )
    return traces


# ═══════════════════════════════════════════════════════════════
#  构建图表
# ═══════════════════════════════════════════════════════════════

def build_plots(
    df: pd.DataFrame,
    test_items: list[str],
    group_by: str,
    y_mode: str,
    plot_config: dict,
) -> go.Figure:
    rows = plot_config.get("rows", 2)
    cols = plot_config.get("cols", 3)
    marker_size = plot_config.get("marker_size", 6)
    line_width = plot_config.get("line_width", 1)
    marker_opacity = plot_config.get("marker_opacity", 80) / 100.0
    line_opacity = plot_config.get("line_opacity", 80) / 100.0
    lineframe_width = plot_config.get("lineframe_width", 1)
    lineframe_width = max(0, int(lineframe_width)) if lineframe_width is not None else 1
    plot_type = plot_config.get("plot_type", "markers")
    theme = plot_config.get("theme", "plotly_white")
    title_fs = plot_config.get("title_font_size", 14)
    label_fs = plot_config.get("label_font_size", 12)
    legend_fs = plot_config.get("legend_font_size", 11)
    x_label = plot_config.get("x_label", "")
    x_min = plot_config.get("x_min")
    x_max = plot_config.get("x_max")
    y_min = plot_config.get("y_min")
    y_max = plot_config.get("y_max")
    cfg_width = plot_config.get("width", 1200)
    cfg_height = plot_config.get("height", 600)
    hover_template = plot_config.get("hover_template", "")
    tick_format = plot_config.get("tick_format", "")
    tick_decimals = plot_config.get("tick_decimals", -1)

    # --- (1) X/Y 轴 log/linear 尺度 ---
    x_scale = plot_config.get("x_scale", "linear")
    y_scale = plot_config.get("y_scale", "linear")

    # --- (3) Limit 配置 ---
    show_limit_line = plot_config.get("show_limit_line", False)
    draw_over_limit = plot_config.get("draw_over_limit", False)
    limit_map = plot_config.get("limit_map", {})
    direction_map = plot_config.get("direction_map", {})

    # --- (4) 绘制哪些数据 ---
    draw_t0 = plot_config.get("draw_t0", True)
    draw_tx = plot_config.get("draw_tx", True)
    draw_shift = plot_config.get("draw_shift", True)
    DRAW_MAP = {"T0": draw_t0, "TX": draw_tx, "shift": draw_shift}

    # --- (5) 进度报告 ---
    _progress = plot_config.get("_progress")
    _progress_total = plot_config.get("_progress_total", 1)

    def _get_limit(item: str) -> tuple[float | None, str | None]:
        """Return (limit_value, direction) for a test item. Robust float conversion."""
        direction = direction_map.get(item, "lower")
        lim = limit_map.get(item)
        if lim is None:
            return None, None
        # If limit_map[item] is nested dict: {"lower": X, "higher": Y, ...}
        if isinstance(lim, dict):
            # Use explicit None checks instead of `or` (0 is falsy!)
            val = lim.get(direction)
            if val is None:
                val = lim.get("lower")
            if val is None:
                val = lim.get("higher")
            if val is None:
                val = lim.get("shift")
            if val is None:
                return None, None
            return _to_float(val), direction
        # If limit_map[item] is a plain number or string
        return _to_float(lim), direction

    def _to_float(v: Any) -> float | None:
        """Safely convert a value to float; handles strings like '0.1'."""
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    mode_map = {"markers": "markers", "lines": "lines", "markers+lines": "markers+lines"}
    trace_mode = mode_map.get(plot_type, "markers")

    # --- (2) tick_format 科学记数法映射 ---
    tick_kw = {}
    if tick_format == "科学记数法":
        ndec = tick_decimals if tick_decimals >= 0 else 2
        tick_kw["tickformat"] = f".{ndec}e"
    elif tick_format == "普通数字":
        ndec = tick_decimals if tick_decimals >= 0 else 2
        tick_kw["tickformat"] = f".{ndec}f"
    elif tick_format:
        # 用户手动输入了格式字符串（如 ".3e"）
        if tick_decimals >= 0:
            base = "e" if "e" in tick_format.lower() else "f"
            tick_kw["tickformat"] = f".{tick_decimals}{base}"
        else:
            tick_kw["tickformat"] = tick_format
    else:
        # tick_format 为空时，仅看 tick_decimals
        if tick_decimals >= 0:
            tick_kw["tickformat"] = f".{tick_decimals}f"

    # 确定子图
    if group_by == "group":
        subplot_titles = test_items
        n_plots = len(test_items)
    else:
        groups = sorted(df["GROUP"].unique())
        subplot_titles = groups
        n_plots = len(groups)

    if n_plots == 0:
        fig = go.Figure()
        fig.add_annotation(text="无数据可绘制", showarrow=False, font=dict(size=20))
        return fig

    # 计算行列
    n_cols = max(1, cols)
    n_rows = (n_plots + n_cols - 1) // n_cols

    fig = make_subplots(
        rows=n_rows, cols=n_cols,
        subplot_titles=subplot_titles,
        horizontal_spacing=0.1,
    )

    y_label = "CDF" if y_mode.upper() == "CDF" else "ln(-ln(1-Median Rank))"

    # 每个子图独立图例 — 用子图的 yaxis.domain 精确定位到图区顶部
    legend_positions = {}
    for idx in range(n_plots):
        r = idx // n_cols + 1
        c = idx % n_cols + 1
        leg_name = f"legend{idx+1}" if idx > 0 else "legend"
        if n_cols == 1:
            x = 1.02
            xanchor = "left"
        elif c == 1:
            x = -0.15
            xanchor = "right"
        elif c == n_cols:
            x = 1.02
            xanchor = "left"
        else:
            x = -0.15 if idx % 2 == 0 else 1.02
            xanchor = "right" if x < 0 else "left"
        legend_positions[idx] = (leg_name, x, xanchor, r)

    formula_map = plot_config.get("formula_map", {})

    for idx, title in enumerate(subplot_titles):
        r = idx // n_cols + 1
        c = idx % n_cols + 1
        leg_name, lx, lxanchor, ly = legend_positions[idx]

        if group_by == "group":
            traces_data = extract_traces_by_group(df, title, y_mode)
        else:
            traces_data = extract_traces_by_item(df, title, test_items, y_mode)

        # 按 draw_t0/draw_tx/draw_shift 过滤 traces
        traces_data = [t for t in traces_data if DRAW_MAP.get(t.get("_suffix", ""), True)]

        # --- (5) Hover 富化: customdata + text ---
        # 收集当前子图所有 x 值，用于 limit 填充
        subplot_all_x = []
        for ti, tr in enumerate(traces_data):
            x_vals = tr["x"]
            y_vals = tr["y"]
            n = tr["n"]
            pids = tr.get("part_ids", [])
            ranks = tr.get("ranks", [])
            subplot_all_x.extend(x_vals)

            # 构造 customdata: [PART_ID, group_total, group_fail, limit_fail, rank]
            # limit_fail: 该 trace 中超出 limit 的数值个数
            limit_val_trace, dir_trace = _get_limit(title)
            limit_fail = 0
            if limit_val_trace is not None:
                if dir_trace == "lower":
                    limit_fail = sum(1 for v in x_vals if v < limit_val_trace)
                elif dir_trace == "upper":
                    limit_fail = sum(1 for v in x_vals if v > limit_val_trace)
                else:
                    limit_fail = sum(1 for v in x_vals if abs(v) > limit_val_trace)
            custom_arr = []
            for j in range(len(x_vals)):
                pid = str(pids[j]) if j < len(pids) else ""
                rk = int(ranks[j]) if j < len(ranks) else j + 1
                custom_arr.append([pid, tr["group_total"], tr["group_fail"],
                                   limit_fail, rk])

            # marker 边框
            marker_line = dict(width=lineframe_width, color='lightgray') if lineframe_width > 0 else None

            scatter_kw = dict(
                x=x_vals,
                y=y_vals,
                mode=trace_mode,
                name=tr["name"],
                legend=leg_name,
                showlegend=True,
                text=[tr["name"]] * len(x_vals),  # 分组名用于 hovertemplate 中的 %{text}
                customdata=custom_arr,
                hovertemplate=(
                    hover_template
                    if hover_template
                    else "<b>分组</b>: %{text}<br>"
                         "<b>x</b>: %{x}<br>"
                         "<b>y</b>: %{y}<br>"
                         "<b>PART_ID</b>: %{customdata[0]}<br>"
                         "<b>同组总数</b>: %{customdata[1]}<br>"
                         "<b>总体失效</b>: %{customdata[2]}/%{customdata[1]}<br>"
                         "<b>本项失效</b>: %{customdata[3]}/%{customdata[1]}<br>"
                         "<b>rank</b>: %{customdata[4]}<br>"
                         "<extra></extra>"
                ),
                marker=dict(
                    symbol=get_marker(ti),
                    size=marker_size,
                    opacity=marker_opacity,
                    line=marker_line,
                ),
                line=dict(width=line_width) if trace_mode != "markers" else None,
            )
            fig.add_trace(go.Scatter(**scatter_kw), row=r, col=c)

        # --- (3) Limit 红色虚线 + 超出区域 ---
        limit_val, direction = _get_limit(title)
        if limit_val is not None and show_limit_line:
            # 红色虚线
            fig.add_vline(
                x=limit_val,
                line_dash="dash",
                line_color="red",
                line_width=2,
                row=r,
                col=c,
            )
        if limit_val is not None and draw_over_limit and subplot_all_x:
            x_min_data = min(subplot_all_x)
            x_max_data = max(subplot_all_x)
            # 从 limit 到数据极值画半透明红色区域
            if direction == "upper":
                x0, x1 = limit_val, x_max_data
            elif direction == "lower":
                x0, x1 = x_min_data, limit_val
            else:
                x0, x1 = limit_val, x_max_data
            if x1 > x0:
                fig.add_vrect(
                    # type="rect",
                    x0=x0, x1=x1,
                    # y0=0, y1=1,
                    yref="paper",
                    fillcolor="red",
                    opacity=0.12,
                    line_width=0,
                    layer="below",
                    row=r,
                    col=c,
                )

        x_range = [x_min, x_max] if (x_min is not None or x_max is not None) else None
        y_range = [y_min, y_max] if (y_min is not None or y_max is not None) else None

        # 替换 x_label 中的 %formula%
        subplot_x_label = x_label
        if "%formula%" in subplot_x_label:
            if group_by == "group":
                formula = formula_map.get(title, "")
            else:
                formulas = set()
                for item in test_items:
                    f = formula_map.get(item, "")
                    if f:
                        formulas.add(f)
                formula = ", ".join(sorted(formulas))
            subplot_x_label = subplot_x_label.replace("%formula%", formula or "")

        # --- (1) X/Y 尺度 + (2) tick 格式 + (5) 字号配置 ---
        fig.update_xaxes(
            title_text=subplot_x_label or "原始数据",
            title_font=dict(size=label_fs),
            type=x_scale,
            tickangle=45,
            range=x_range,
            row=r,
            col=c,
            **tick_kw,
        )
        fig.update_yaxes(
            title_text=y_label,
            title_font=dict(size=label_fs),
            type=y_scale,
            range=y_range,
            row=r,
            col=c,
            **tick_kw,
        )

        # 进度报告
        if _progress and not _progress.cancelled:
            done = idx + 1
            _progress.advance(step=1, status=f"构建图表 ({done}/{_progress_total} 项)...")

    # 计算合理尺寸
    plot_width = max(cfg_width, n_cols * cfg_width)
    plot_height = max(cfg_height, n_rows * cfg_height)

    # 构建布局
    layout_kw = dict(
        title=dict(text="", font=dict(size=title_fs)),
        width=plot_width,
        height=plot_height,
        template=theme,
        hoverlabel=dict(font=dict(size=plot_config.get("hover_font_size", 11))),
        margin=dict(l=120, r=120, t=40, b=60),
    )
    # 每个子图的图例 — 用 yaxis.domain（图区顶部）精确定位
    for idx, title in enumerate(subplot_titles):
        leg_name, lx, lxanchor, r = legend_positions[idx]
        # 读取该子图的 yaxis domain 获取图区顶部
        yaxis_key = f"yaxis{idx+1}" if idx > 0 else "yaxis"
        domain = getattr(fig.layout, yaxis_key).domain
        ly = domain[1]  # 图区顶部
        kw = {
            "title": dict(text=title, font=dict(size=legend_fs)),
            "font": dict(size=legend_fs - 1),
            "x": lx, "xanchor": lxanchor,
            "y": ly, "yanchor": "top",
            "bgcolor": "rgba(255,255,255,0.8)",
        }
        layout_kw[leg_name] = kw
    # 默认隐藏全局 legend
    if "legend" not in layout_kw:
        layout_kw["showlegend"] = False
    fig.update_layout(**layout_kw)
    return fig


# ═══════════════════════════════════════════════════════════════
#  HTML 导出
# ═══════════════════════════════════════════════════════════════

def save_html(fig: go.Figure, path: str):
    fig.write_html(path)
#     """保存为可滚动 HTML（自适应宽度，高度按内容自动撑开）"""
#     html = fig.to_html(
#         include_plotlyjs="cdn",
#         full_html=False,
#         config={"responsive": True, "displayModeBar": True, "scrollZoom": True},
#     )
#     full_html = f"""<!DOCTYPE html>
# <html>
# <head>
# <meta charset="utf-8">
# <style>
# html, body {{ margin:0; padding:0; width:100%; height:100%; overflow:auto; }}
# #plotly-div {{ width:100%; min-height:100%; }}
# </style>
# </head>
# <body>
# {html}
# </body>
# </html>"""
#     Path(path).write_text(full_html, encoding="utf-8")
