"""
数据合并核心逻辑。

职责：
1. 读取 T0 / TX 文件
2. 全部数据合为一张大表
3. 按 (PART_ID, group) 分组，组内横向拼接
4. 同列存在多个不同值 → 收集冲突供弹窗选择
5. 返回合并后的 DataFrame
"""

from pathlib import Path
from typing import Optional

import pandas as pd

from .file_parser import read_file


# ── 公共工具 ──────────────────────────────────────────────────

def is_pass(bin_val) -> bool:
    """SOFT_BIN = 1 为 PASS"""
    try:
        return str(int(bin_val)) == "1"
    except (ValueError, TypeError):
        return False


def is_fail(bin_val) -> bool:
    return not is_pass(bin_val)


# ── 组内横向合并 ────────────────────────────────────────────

def _merge_group_rows(rows: pd.DataFrame) -> tuple[dict, bool]:
    """将同 (PART_ID, group) 的多行横向合并。

    返回:
        merged_row: 合并后的单行 dict
        has_conflict: 是否有测试列冲突
    """
    if len(rows) == 1:
        return rows.iloc[0].to_dict(), False

    base = rows.iloc[0].to_dict()
    has_conflict = False

    for idx in range(1, len(rows)):
        row = rows.iloc[idx]
        for col in rows.columns:
            if col in ("filepath", "SOFT_BIN"):
                continue
            v_base = base.get(col)
            v_new = row[col]

            if pd.isna(v_base) and pd.isna(v_new):
                continue
            if pd.isna(v_base) and not pd.isna(v_new):
                base[col] = v_new
                continue
            if not pd.isna(v_base) and pd.isna(v_new):
                continue

            # 都有值 → 比较
            try:
                equal = (v_base == v_new) or (
                    isinstance(v_base, (int, float)) and
                    isinstance(v_new, (int, float)) and
                    abs(float(v_base) - float(v_new)) < abs(float(v_base)) * 1e-9
                )
            except (ValueError, TypeError):
                equal = str(v_base) == str(v_new)

            if not equal:
                has_conflict = True

    return base, has_conflict


# ── 完整合并流程 ──────────────────────────────────────────────

def merge_t0_tx(
    t0_paths: list[str],
    tx_paths: list[str],
    tx_group_map: Optional[dict[str, str]] = None,
    on_conflict: Optional[callable] = None,
    on_cross_conflict: Optional[callable] = None,
    progress: Optional['ProgressReporter'] = None,
    sn_map: Optional[dict[str, str]] = None,
    group_type: str = "filename",
) -> pd.DataFrame:
    """合并 T0 和 TX 数据。

    流程：
    1. 读所有文件，合为一张大表
    2. 按 (PART_ID, group) 分组
    3. 组内横向合并：同列有多个不同值 → 冲突
    4. 通过 on_conflict 回调让主线程处理冲突弹窗

    参数:
        on_conflict: 回调(conflicts: list[dict]) → dict {(PART_ID,group,column): chosen_value}
                      在主线程预扫描时收集所有冲突后一次性弹窗处理
    """
    all_rows = []
    total_steps = len(t0_paths) + len(tx_paths) + 3
    if progress:
        progress.set_total(total_steps)

    # ── 读取 T0 ──
    for i, p in enumerate(t0_paths):
        if progress and progress.cancelled:
            return pd.DataFrame()
        if progress:
            progress.advance(f"读取 T0 ({i+1}/{len(t0_paths)})")
        df = read_file(p)
        df["group"] = "T0"
        df["filepath"] = str(Path(p).name)
        all_rows.append(df)

    # ── 读取 TX ──
    for i, p in enumerate(tx_paths):
        if progress and progress.cancelled:
            return pd.DataFrame()
        if progress:
            progress.advance(f"读取 TX ({i+1}/{len(tx_paths)})")
        df = read_file(p)
        fname = Path(p).name
        if tx_group_map and fname in tx_group_map:
            df["group"] = tx_group_map[fname]
        else:
            df["group"] = fname

        # 按 SN 分组（如果配置了 sn_map）
        if sn_map and group_type in ("SN", "both"):
            filename_group = df["group"].iloc[0] if len(df) > 0 else fname
            def _sn_group(pid):
                pid_str = str(pid).strip()
                if pid_str in sn_map:
                    return sn_map[pid_str]
                for pattern, group in sn_map.items():
                    if pid_str.startswith(pattern):
                        return group
                return None
            sn_groups = df["PART_ID"].apply(_sn_group)
            sn_groups = sn_groups.fillna(filename_group)
            if group_type == "both":
                combined = filename_group + "+" + sn_groups
                mask = sn_groups == filename_group
                combined[mask] = filename_group
                df["group"] = combined
            else:
                df["group"] = sn_groups

        df["filepath"] = fname
        all_rows.append(df)

    if not all_rows:
        return pd.DataFrame()

    if progress:
        progress.advance("合并数据...")
    big_table = pd.concat(all_rows, ignore_index=True)

    if progress:
        progress.advance("分组横向合并...")

    # ── 按 (PART_ID, group) 分组，组内横向合并 ──
    merged_rows = []
    conflict_groups: list[pd.DataFrame] = []  # 有冲突的组的原始行

    for (pid, grp), group_df in big_table.groupby(
            ["PART_ID", "group"], sort=False):
        if len(group_df) == 1:
            merged_rows.append(group_df.iloc[0].to_dict())
            continue
        # 组内有 PASS(1) → 自动保留第一个 PASS 行，不弹窗
        pass_mask = group_df["SOFT_BIN"].apply(is_pass)
        if pass_mask.any():
            merged_rows.append(group_df[pass_mask].iloc[0].to_dict())
            continue
        # 全部 FAIL → 横向合并 + 检测测试列冲突
        merged, has_conflict = _merge_group_rows(group_df)
        if has_conflict:
            conflict_groups.append(group_df)
        merged_rows.append(merged)

    result = pd.DataFrame(merged_rows)

    # 统一列顺序
    cols = ["PART_ID", "SOFT_BIN", "group", "filepath"]
    remaining = [c for c in result.columns if c not in cols]
    result = result[cols + remaining]

    # ── 处理冲突：整行选择 ──
    if conflict_groups and on_conflict is not None:
        chosen_indices = on_conflict(conflict_groups)
        if chosen_indices:
            for cg_idx, group_df in enumerate(conflict_groups):
                if cg_idx >= len(chosen_indices):
                    break
                chosen_idx = chosen_indices[cg_idx]
                if chosen_idx is None or chosen_idx < 0:
                    continue
                chosen_row = group_df.iloc[chosen_idx]
                pid = chosen_row["PART_ID"]
                grp = chosen_row["group"]
                mask = (result["PART_ID"] == pid) & (result["group"] == grp)
                if mask.any():
                    # 用选取的行更新结果
                    for col in result.columns:
                        if col in chosen_row and col not in ("PART_ID", "group"):
                            result.loc[mask, col] = chosen_row[col]

    if progress:
        progress.advance("合并完成")

    return result


# ── 旧接口保留（文件内去重） ──────────────────────────────

def dedup_within_file(df: pd.DataFrame, filepath: str
                      ) -> tuple[pd.DataFrame, list[pd.DataFrame]]:
    """文件内按 PART_ID 去重（旧接口，仍可用）。

    返回:
        clean: 去重后的 DataFrame（PASS 优先）
        conflicts: 每个 PART_ID 的全部 FAIL 行列表（用于弹窗）
    """
    required = {"PART_ID", "SOFT_BIN"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"缺少必要列: {missing}")

    clean_rows = []
    conflict_groups = []

    for pid, group in df.groupby("PART_ID", sort=False):
        pass_rows = group[group["SOFT_BIN"].apply(is_pass)]
        fail_rows = group[group["SOFT_BIN"].apply(is_fail)]

        if len(pass_rows) >= 1:
            clean_rows.append(pass_rows.iloc[0])
        elif len(fail_rows) >= 1:
            if len(fail_rows) == 1:
                clean_rows.append(fail_rows.iloc[0])
            else:
                rows_with_source = fail_rows.copy()
                rows_with_source["_file"] = filepath
                conflict_groups.append(rows_with_source)
                clean_rows.append(fail_rows.iloc[0])

    result = pd.DataFrame(clean_rows) if clean_rows else pd.DataFrame(columns=df.columns)
    return result, conflict_groups


def merge_horizontal(frames: list[pd.DataFrame],
                     on: Optional[list[str]] = None,
                     source_labels: Optional[list[str]] = None,
                     on_col_conflict: Optional[callable] = None,
                     ) -> pd.DataFrame:
    """跨文件横向拼接（旧接口，仍可用）"""
    if not frames:
        return pd.DataFrame()
    if len(frames) == 1:
        return frames[0]

    on = on or ["PART_ID", "group"]
    source_labels = source_labels or [f"文件{i}" for i in range(len(frames))]

    result = frames[0].copy()
    for idx, df in enumerate(frames[1:]):
        merge_on = [c for c in on if c in result.columns and c in df.columns]
        overlap = [c for c in df.columns if c in result.columns and c not in merge_on]
        df_suf = df.rename(columns={c: f"{c}_{idx+1}" for c in overlap})
        result = pd.merge(
            result, df_suf,
            on=merge_on,
            how="outer",
        )

    import re
    suffix_pattern = re.compile(r"_(\d+)$")
    conflict_cols = [c for c in result.columns if suffix_pattern.search(c)]
    if not conflict_cols or on_col_conflict is None:
        for cc in conflict_cols:
            base = suffix_pattern.sub("", cc)
            if base in result.columns:
                null_mask = result[base].isna()
                if null_mask.any():
                    result.loc[null_mask, base] = result.loc[null_mask, cc]
                result.drop(columns=[cc], inplace=True)
            else:
                result.rename(columns={cc: base}, inplace=True)
        return result

    all_conflicts = []
    for cc in conflict_cols:
        base = suffix_pattern.sub("", cc)
        if base not in result.columns:
            continue
        m = suffix_pattern.search(cc)
        src_idx = int(m.group(1)) if m else 0
        for row_idx in result.index:
            v0 = result.loc[row_idx, base]
            v1 = result.loc[row_idx, cc]
            if pd.notna(v0) and pd.notna(v1) and v0 != v1:
                key_vals = {k: result.loc[row_idx, k] for k in on if k in result.columns}
                all_conflicts.append({
                    "row_idx": row_idx,
                    "key": key_vals,
                    "column": base,
                    "values": {source_labels[0]: v0, source_labels[idx + 1]: v1},
                })

    if all_conflicts and on_col_conflict is not None:
        user_choices = on_col_conflict(all_conflicts)
    else:
        user_choices = {}

    for cc in conflict_cols:
        base = suffix_pattern.sub("", cc)
        chosen_src = (user_choices or {}).get(base)
        if chosen_src is not None and chosen_src != source_labels[0]:
            result[base] = result[cc]
            result.drop(columns=[cc], inplace=True)
        else:
            if base in result.columns:
                null_mask = result[base].isna()
                if null_mask.any():
                    result.loc[null_mask, base] = result.loc[null_mask, cc]
                result.drop(columns=[cc], inplace=True)
            else:
                result.rename(columns={cc: base}, inplace=True)

    return result
