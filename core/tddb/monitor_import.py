"""监控数据导入、TBD 检测和 QBD 计算。

数据流: Excel/CSV → 按列映射配置解析 → 通道时间序列 → TBD 检测 → QBD 计算
"""
from __future__ import annotations

import logging
import math
import os
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── 数据类型 ──────────────────────────────────────────────────────────


@dataclass
class ColumnMapping:
    """单个文件的列映射配置。"""
    sheet_index: int = 0                # Sheet 序号（从 0 开始）
    sheet_name: str = ""                # Sheet 名（展示用）
    header_row: int = 0                 # 数据起始行（0-indexed 从文件算起）
    time_col: str = ""                  # 时间列列名（采样时间或老化时间）
    time_from_sampling: bool = True     # True=采样时间, False=老化时间
    aging_time_unit: str = "分"          # 老化时间单位
    voltage_col: str = ""               # 电压列列名（为空则用固定值）
    voltage_fixed: float = 0.0          # 固定电压值
    current_keyword: str = "电流"        # 监控电流关键字
    current_unit: str = "uA"            # 电流单位
    temp_col: str = ""                  # 温度列列名
    temp_unit: str = "℃"                # 温度单位
    has_temp: bool = True               # 是否有监控温度
    selected_channels: list[str] = field(default_factory=list)  # 选中的电流列名

    # 衍生（运行时填充）
    file_path: str = ""
    channel_columns: list[str] = field(default_factory=list)  # 匹配到的所有电流列


@dataclass
class MonitoredChannel:
    """单个监控通道的数据。"""
    name: str
    time: np.ndarray           # 时间（秒，float）
    current: np.ndarray        # 电流（A，float）
    voltage: float             # 施加电压（V）
    temperature: float | None  # 温度（℃）
    file_path: str             # 来源文件


@dataclass
class TBDCandidate:
    """一个 TBD 候选点。"""
    channel_name: str
    tbd_time: float          # TBD 时间（秒）
    tbd_current: float       # TBD 时刻的电流（A）
    failure_reason: str      # 失效原因描述
    index_in_series: int     # 在原始序列中的位置
    file_path: str = ""      # 来源文件路径
    confirmed: bool = True   # 用户确认
    note: str = ""           # 用户备注


@dataclass
class QBDResult:
    """QBD 计算结果。"""
    channel_name: str
    tbd_time: float          # TBD 时间（秒）
    tbd_current: float       # TBD 时刻电流（A）
    qbd: float               # QBD（库仑，C）
    voltage: float           # 电压（V）
    temperature: float | None  # 温度（℃）
    file_path: str


# ── 失效点判断逻辑 ─────────────────────────────────────────────────


def _find_first_by_current_drop(
    time: np.ndarray, current: np.ndarray, threshold: float = 0.0
) -> int | None:
    """条件1：监控电流降为 0（或低于 threshold）。"""
    mask = current <= threshold
    idx = np.where(mask)[0]
    return int(idx[0]) if len(idx) > 0 else None


def _find_first_by_rate_exceed(
    time: np.ndarray, current: np.ndarray, rate_limit: float = 10.0
) -> int | None:
    """条件2：相较前一时刻倍率超限。

    current[i] > current[i-1] * rate_limit
    """
    if len(current) < 2:
        return None
    ratios = current[1:] / np.maximum(current[:-1], 1e-30)
    idx = np.where(ratios > rate_limit)[0]
    return int(idx[0] + 1) if len(idx) > 0 else None


def _find_first_by_current_limit(
    time: np.ndarray, current: np.ndarray, current_limit: float
) -> int | None:
    """条件3：超过设定电流上限。"""
    mask = current > current_limit
    idx = np.where(mask)[0]
    return int(idx[0]) if len(idx) > 0 else None


def _exclude_half_failure(
    tbd_list: list[TBDCandidate],
    total_channels: int | None = None,
) -> list[TBDCandidate]:
    """条件4：排除超过一半同时失效时间。

    统计每个时间点的失效通道数，如果某时间点失效通道数 > 总通道数的一半，
    则这条记录可能是测试系统整体失效（如停电），排除。

    Args:
        tbd_list: TBD 候选列表
        total_channels: 监控总通道数。为 None 时从 tbd_list 推断（仅当所有通道都失效时生效）。
    """
    if not tbd_list:
        return tbd_list

    from collections import Counter
    time_counts = Counter()
    for tbd in tbd_list:
        time_counts[tbd.tbd_time] += 1

    # 总通道数：用传入值或从唯一通道名推断
    if total_channels is None:
        unique_channels = len({t.channel_name for t in tbd_list})
        total_channels = max(unique_channels, max(time_counts.values()))
    half = total_channels / 2.0

    return [t for t in tbd_list if time_counts[t.tbd_time] <= half]


def detect_tbd_points(
    channel: MonitoredChannel,
    enable_drop: bool = True,
    enable_rate: bool = True,
    enable_limit: bool = True,
    enable_half_exclude: bool = True,
    current_limit_ua: float = 1.0,
    rate_limit: float = 10.0,
    current_drop_threshold: float = 0.0,
) -> list[TBDCandidate]:
    """对单个通道检测所有 TBD 候选点。

    返回按时间排序的候选列表。可能包含多个候选（不同条件同时命中）。
    """
    t = channel.time
    c = channel.current  # 已经是 A

    logger.info(f"检测TBD: channel={channel.name}, file={Path(channel.file_path).name}, "
                f"data_points={len(t)}, drop={enable_drop}, rate={enable_rate}, limit={enable_limit}")

    # 负漏电流取绝对值（负栅压下漏电流为负值）
    c = np.abs(c)

    current_limit_a = current_limit_ua * 1e-6  # uA → A

    # ── 过滤起始零值和失效后连续零值 ──
    # 1. 跳过起始阶段未加压的零值点
    first_valid = 0
    while first_valid < len(c) and c[first_valid] <= current_drop_threshold * 2:
        first_valid += 1
    if first_valid > 0:
        logger.debug(f"通道 {channel.name}: 跳过起始 {first_valid} 个零值点")
        t = t[first_valid:]
        c = c[first_valid:]

    # 2. 连续零值去重：仅保留每个连续零值段中的第一个（首个降为0点保留，后续零点排除）
    if len(c) > 3:
        keep = [True] * len(c)
        in_zero_run = False
        zero_removed = 0
        for i in range(len(c)):
            if c[i] <= current_drop_threshold:
                if in_zero_run:
                    keep[i] = False  # 连续零点中仅保留第一个
                    zero_removed += 1
                else:
                    in_zero_run = True  # 第一个零点保留
            else:
                in_zero_run = False
        if zero_removed > 0:
            logger.debug(f"通道 {channel.name}: 去重 {zero_removed} 个连续零值点")
        t = t[keep]
        c = c[keep]

    # 3. 连续超限值去重：仅保留每个连续超限段中的第一个
    if len(c) > 3 and enable_limit:
        keep = [True] * len(c)
        in_limit_run = False
        limit_removed = 0
        for i in range(len(c)):
            if c[i] > current_limit_a:
                if in_limit_run:
                    keep[i] = False
                    limit_removed += 1
                else:
                    in_limit_run = True
            else:
                in_limit_run = False
        if limit_removed > 0:
            logger.debug(f"通道 {channel.name}: 去重 {limit_removed} 个连续超限值点")
        t = t[keep]
        c = c[keep]

    if len(t) < 3:
        logger.debug(f"通道 {channel.name}: 过滤后数据点不足3个，跳过")
        return []

    candidates: list[TBDCandidate] = []

    # 条件1：电流降为0
    if enable_drop:
        idx = _find_first_by_current_drop(t, c, current_drop_threshold)
        if idx is not None:
            logger.info(f"通道 {channel.name}: 条件1(电流降为0)命中, t={t[idx]:.2f}s, c={c[idx]:.6e}A")
            candidates.append(TBDCandidate(
                channel_name=channel.name,
                tbd_time=t[idx],
                tbd_current=c[idx],
                failure_reason="监控电流降为0",
                index_in_series=idx,
                file_path=channel.file_path,
            ))
        else:
            logger.debug(f"通道 {channel.name}: 条件1(电流降为0)未命中")

    # 条件2：倍率超限
    if enable_rate:
        idx = _find_first_by_rate_exceed(t, c, rate_limit)
        if idx is not None:
            logger.info(f"通道 {channel.name}: 条件2(倍率超限)命中, t={t[idx]:.2f}s, c={c[idx]:.6e}A")
            # 检查是否与已有候选同索引 → 合并原因
            existing = [ca for ca in candidates if ca.index_in_series == idx]
            if existing:
                existing[0].failure_reason += "; 倍率超限"
            else:
                candidates.append(TBDCandidate(
                    channel_name=channel.name,
                    tbd_time=t[idx],
                    tbd_current=c[idx],
                    failure_reason="倍率超限",
                    index_in_series=idx,
                    file_path=channel.file_path,
                ))
        else:
            logger.debug(f"通道 {channel.name}: 条件2(倍率超限)未命中")

    # 条件3：超过电流上限
    if enable_limit:
        idx = _find_first_by_current_limit(t, c, current_limit_a)
        if idx is not None:
            logger.info(f"通道 {channel.name}: 条件3(超过电流上限)命中, t={t[idx]:.2f}s, c={c[idx]:.6e}A")
            existing = [ca for ca in candidates if ca.index_in_series == idx]
            if existing:
                existing[0].failure_reason += "; 超过电流上限"
            else:
                candidates.append(TBDCandidate(
                    channel_name=channel.name,
                    tbd_time=t[idx],
                    tbd_current=c[idx],
                    failure_reason=f"超过电流上限({current_limit_ua}uA)",
                    index_in_series=idx,
                    file_path=channel.file_path,
                ))
        else:
            logger.debug(f"通道 {channel.name}: 条件3(超过电流上限)未命中")

    # 候选点可能有多个不同索引 → 都是有效候选，保留
    candidates.sort(key=lambda x: x.tbd_time)

    logger.info(f"通道 {channel.name}: TBD检测完成, 候选数={len(candidates)}")
    return candidates


def calculate_qbd(channel: MonitoredChannel, tbd_time: float) -> float:
    """计算 QBD = ∫I(t) dt 从 t=0 到 t=TBD。

    使用梯形法积分电流-时间曲线。
    """
    t = channel.time
    c = channel.current

    # 找到 TBD 时刻的索引
    idx = np.searchsorted(t, tbd_time, side="right") - 1
    if idx < 1:
        return 0.0

    # 截取到 TBD 时刻
    t_trunc = t[:idx + 1]
    c_trunc = c[:idx + 1]

    # 梯形积分
    qbd = np.trapezoid(c_trunc, t_trunc)
    return qbd


# ── 文件解析 ─────────────────────────────────────────────────────────


def parse_header_rows(
    file_path: str,
    sheet_index: int = 0,
    max_rows: int = 50,
) -> list[list[str]]:
    """读取文件的前 max_rows 行原始数据（不解析列名）。

    用于首行选择下拉框展示。
    返回每行的字符串列表。
    """
    ext = Path(file_path).suffix.lower()
    rows: list[list[str]] = []

    try:
        if ext == ".csv":
            # CSV: 逐行读取
            import csv
            with open(file_path, encoding="utf-8-sig", errors="replace") as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if i >= max_rows:
                        break
                    rows.append([str(c) if c is not None else "" for c in row])
        else:
            # Excel
            df = pd.read_excel(file_path, sheet_name=sheet_index, header=None,
                               nrows=max_rows, dtype=str)
            for _, row in df.iterrows():
                rows.append([str(v) if pd.notna(v) else "" for v in row])
    except Exception as e:
        logger.warning(f"读取文件前 {max_rows} 行失败: {e}")

    return rows


def get_sheet_names(file_path: str) -> list[str]:
    """获取 Excel 文件的 Sheet 名称列表。CSV 返回空列表。"""
    ext = Path(file_path).suffix.lower()
    if ext == ".csv":
        return []
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, read_only=True)
        sheets = wb.sheetnames
        wb.close()
        return sheets
    except Exception as e:
        logger.warning(f"获取 Sheet 列表失败: {e}")
        return []


def parse_monitor_file(
    file_path: str,
    mapping: ColumnMapping,
) -> tuple[list[MonitoredChannel], float | None, float | None]:
    """按列映射配置解析监控数据文件。

    Returns:
        (channels, voltage, temperature)
        channels: 所有选中通道的数据
        voltage: 施加电压（V），如果从列读取则为该列非0值均值
        temperature: 监控温度（℃），如果没有则为 None
    """
    ext = Path(file_path).suffix.lower()

    logger.info(f"解析监控文件: {file_path}, encoding_type={ext}, sheet_index={mapping.sheet_index}")

    # 读取数据 — 用 header=None 先全部读出，再手动指定列名
    try:
        if ext == ".csv":
            df_raw = pd.read_csv(file_path, header=None, encoding="utf-8-sig",
                                 dtype=str, skip_blank_lines=False)
        else:
            df_raw = pd.read_excel(file_path, sheet_name=mapping.sheet_index,
                                   header=None, dtype=str)
    except Exception as e:
        raise ValueError(f"无法读取文件: {e}")

    if df_raw.empty:
        raise ValueError("文件为空")

    # 用 header_row 行作为列名
    header_idx = mapping.header_row
    logger.info(f"使用第 {header_idx} 行作为列名")
    if header_idx >= len(df_raw):
        raise ValueError(f"首行设置超出文件范围（共 {len(df_raw)} 行，首行索引 {header_idx}）")

    columns_raw = [str(c) if pd.notna(c) else f"Unnamed_{i}"
                   for i, c in enumerate(df_raw.iloc[header_idx].values)]
    data_df = df_raw.iloc[header_idx + 1:].copy()
    data_df.columns = columns_raw
    data_df = data_df.reset_index(drop=True)
    df = data_df

    # 列名清理
    df.columns = [str(c).strip() for c in df.columns]

    # 时间列
    time_col = mapping.time_col
    logger.info(f"可用列: {list(df.columns)}")
    logger.info(f"请求时间列: '{time_col}'")
    if time_col not in df.columns:
        raise ValueError(f"时间列 '{time_col}' 在文件中未找到。可用列: {list(df.columns)}")

    time_raw = df[time_col].values

    # 解析时间
    if mapping.time_from_sampling:
        # 采样时间列 → 转换为相对于起始的秒数
        time_seconds = _parse_sampling_time_to_seconds(time_raw)
    else:
        # 老化时间列 → 按单位转换为秒
        time_seconds = _parse_aging_time_to_seconds(time_raw, mapping.aging_time_unit)

    # 电压
    voltage: float | None = None
    if mapping.voltage_col and mapping.voltage_col in df.columns:
        v_raw = pd.to_numeric(df[mapping.voltage_col], errors="coerce")
        non_zero = v_raw[v_raw != 0]
        voltage = float(non_zero.mean()) if len(non_zero) > 0 else 0.0
    elif mapping.voltage_fixed != 0:
        voltage = mapping.voltage_fixed

    # 温度
    temperature: float | None = None
    if mapping.has_temp and mapping.temp_col and mapping.temp_col in df.columns:
        t_raw = pd.to_numeric(df[mapping.temp_col], errors="coerce")
        temperature = float(_convert_temperature(t_raw.mean(), mapping.temp_unit))
    elif not mapping.has_temp:
        temperature = None

    # 电流通道
    channels: list[MonitoredChannel] = []
    current_mult = _current_unit_to_multiplier(mapping.current_unit)

    for col in mapping.selected_channels:
        if col not in df.columns:
            logger.warning(f"电流列 '{col}' 在文件中未找到，跳过")
            continue
        c_raw = pd.to_numeric(df[col], errors="coerce")

        # 过滤无效值和 time_seconds 中的 NaN
        valid = ~(np.isnan(c_raw) | np.isnan(time_seconds))
        t_valid = time_seconds[valid]
        c_valid = c_raw[valid].values * current_mult  # 转换为 A

        if len(t_valid) < 2:
            logger.warning(f"通道 '{col}' 有效数据不足，跳过")
            continue

        # 确保时间递增
        sort_idx = np.argsort(t_valid)
        t_valid = t_valid[sort_idx]
        c_valid = c_valid[sort_idx]

        channels.append(MonitoredChannel(
            name=col,
            time=t_valid.astype(float),
            current=c_valid.astype(float),
            voltage=voltage or 0.0,
            temperature=temperature,
            file_path=file_path,
        ))

    logger.info(f"解析完成: {len(channels)} 个通道, 电压={voltage}V, 温度={temperature}℃")
    return channels, voltage, temperature


def _parse_sampling_time_to_seconds(time_raw: np.ndarray) -> np.ndarray:
    """将采样时间列（日期时间字符串）转换为相对于起始的秒数。"""
    from dateutil import parser as dt_parser

    parsed = []
    for v in time_raw:
        s = str(v).strip()
        if not s:
            parsed.append(np.nan)
            continue
        try:
            parsed.append(dt_parser.parse(s))
        except Exception:
            parsed.append(np.nan)

    # 过滤 NaN
    valid = [p for p in parsed if isinstance(p, datetime)]
    if len(valid) < 2:
        return np.full(len(time_raw), np.nan)

    t0 = valid[0]
    seconds = np.array([
        (p - t0).total_seconds() if isinstance(p, datetime) else np.nan
        for p in parsed
    ])
    return seconds


def _parse_aging_time_to_seconds(time_raw: np.ndarray, unit: str) -> np.ndarray:
    """将老化时间列按单位转换为秒。"""
    nums = pd.to_numeric(pd.Series(time_raw), errors="coerce").values
    mult = _aging_unit_to_seconds(unit)
    return nums * mult


def _aging_unit_to_seconds(unit: str) -> float:
    """老化时间单位 → 秒的乘数。"""
    mapping = {
        "秒": 1.0,
        "分": 60.0,
        "小时": 3600.0,
        "天": 86400.0,
        "周": 604800.0,
        "月": 2592000.0,  # 30天
        "年": 31536000.0,  # 365天
    }
    return mapping.get(unit, 60.0)


def _current_unit_to_multiplier(unit: str) -> float:
    """电流单位 → A 的乘数。"""
    mapping = {
        "pA": 1e-12,
        "nA": 1e-9,
        "uA": 1e-6,
        "mA": 1e-3,
        "A": 1.0,
    }
    return mapping.get(unit, 1e-6)


def _convert_temperature(value: float, unit: str) -> float:
    """温度单位转换到 ℃。"""
    if unit == "℃":
        return value
    elif unit == "K":
        return value - 273.15
    elif unit == "F":
        return (value - 32) * 5.0 / 9.0
    return value


# ── Dummy 数据生成器（测试用） ──────────────────────────────────────


def generate_dummy_monitor_data(
    num_channels: int = 18,
    num_points: int = 120,
    voltage: float = -39.0,
    temperature: float = 150.0,
    base_current_ua: float = 0.5,
    failure_rate: float = 0.1,
    seed: int = 42,
    output_path: str | None = None,
) -> str:
    """生成 TDDB 监控数据的 dummy Excel 文件。

    产生的数据模拟：多个通道的恒定电压应力下的漏电流监控。
    部分通道会在随机时间发生击穿（电流跳变）。
    """
    random.seed(seed)
    np.random.seed(seed)

    start_time = datetime(2026, 7, 1, 12, 0, 0)

    rows = []
    # Header info
    rows.append({"参数名称：": "123"})
    rows.append({})
    rows.append({})
    rows.append({})
    rows.append({})

    # Column headers
    header_row = {
        "采样时间": "采样时间",
        "老化时间(分)": "老化时间(分)",
        "烘箱温度(摄氏度)": "烘箱温度(摄氏度)",
        "电压(V)": "电压(V)",
    }
    for i in range(num_channels):
        header_row[f"电流{i+1}(uA)"] = f"电流{i+1}(uA)"
    rows.append(header_row)

    # 每个通道的失效时间和类型
    fail_configs: dict[int, tuple] = {}
    # failure_type: "spike" (电流突增10x+), "drop" (突降为0), "multi" (先降0再恢复再突增)
    for ch in range(num_channels):
        if random.random() < failure_rate:
            fail_type = random.choices(
                ["spike", "drop", "multi"], weights=[0.35, 0.35, 0.30]
            )[0]
            if fail_type == "multi":
                # 两次失效：先降0，后突增（或再降0）
                t1 = random.uniform(10, num_points * 0.4)
                t2 = random.uniform(num_points * 0.5, num_points - 5)
                sub_type = random.choice(["spike", "drop"])
                fail_configs[ch] = (t1, t2, fail_type, sub_type)
            else:
                fail_time = random.uniform(10, num_points - 5)
                fail_configs[ch] = (fail_time, fail_type, None, None)

    for pt in range(num_points):
        t_minutes = pt
        cur_temp = temperature + np.random.normal(0, 2)
        if pt < 30:
            cur_voltage = voltage + (30 - pt) * 0.1
        else:
            cur_voltage = voltage + np.random.normal(0, 0.3)

        row = {
            "采样时间": (start_time + timedelta(minutes=pt)).strftime("%Y-%m-%d %H:%M:%S"),
            "老化时间(分)": t_minutes,
            "烘箱温度(摄氏度)": round(cur_temp, 1),
            "电压(V)": round(cur_voltage, 1),
        }

        for ch in range(num_channels):
            if ch in fail_configs:
                cfg = fail_configs[ch]
                fail_type = cfg[2] if len(cfg) >= 3 else None
                sub_type = cfg[3] if len(cfg) >= 4 else None
                t_minutes = pt

                if fail_type == "multi":
                    t1, t2 = cfg[0], cfg[1]
                    delta1 = t_minutes - t1
                    delta2 = t_minutes - t2

                    if delta1 < -2:
                        # 第一次失效前：基线+噪声
                        noise = np.random.normal(0, base_current_ua * 0.05)
                        current = max(0.001, base_current_ua + noise)
                    elif -2 <= delta1 < 0:
                        # 预兆
                        noise = np.random.normal(0, base_current_ua * 0.08)
                        current = base_current_ua * (1.0 + random.random() * 0.2) + noise
                    elif delta1 <= 0.1:
                        # 第一次失效：降为0
                        current = 0.0
                    elif delta1 > 0.1 and delta2 < -2:
                        # 两次失效之间：恢复并维持基线
                        recovery = min(1.0, (delta1 - 0.1) / 3.0)
                        current = base_current_ua * recovery * random.uniform(0.8, 1.2)
                    elif -2 <= delta2 < 0:
                        # 第二次失效预兆
                        noise = np.random.normal(0, base_current_ua * 0.1)
                        current = base_current_ua * (1.0 + random.random() * 0.3) + noise
                    elif delta2 <= 0.1:
                        # 第二次失效瞬间
                        if sub_type == "spike":
                            current = base_current_ua * random.uniform(10, 50)
                        else:
                            current = 0.0
                    else:
                        # 第二次失效后
                        if sub_type == "spike":
                            if delta2 < 3:
                                current = base_current_ua * random.uniform(2, 10)
                            elif delta2 < 10:
                                current = base_current_ua * random.uniform(0.5, 5)
                            else:
                                current = base_current_ua * random.random() * 0.3
                        else:
                            current = 0.0
                else:
                    fail_time = cfg[0]
                    fail_type = cfg[1]
                    delta = pt - fail_time

                    if delta < -2:
                        # 失效前：基线 + 小噪声
                        noise = np.random.normal(0, base_current_ua * 0.05)
                        current = max(0.001, base_current_ua + noise)
                    elif delta < 0:
                        noise = np.random.normal(0, base_current_ua * 0.08)
                        current = base_current_ua * (1.0 + np.random.random() * 0.2) + noise
                    elif -0.1 <= delta <= 0.1:
                        if fail_type == "spike":
                            current = base_current_ua * random.uniform(10, 50)
                        else:
                            current = 0.0
                    else:
                        if fail_type == "spike":
                            if delta < 3:
                                current = base_current_ua * random.uniform(2, 10)
                            elif delta < 10:
                                current = base_current_ua * random.uniform(0.5, 5)
                            else:
                                current = base_current_ua * random.random() * 0.3
                        else:
                            current = 0.0
            else:
                # 正常通道：基线 + 小噪声
                noise = np.random.normal(0, base_current_ua * 0.05)
                current = max(0.001, base_current_ua + noise)

            row[f"电流{ch+1}(uA)"] = round(current, 4)

        rows.append(row)

    df = pd.DataFrame(rows)

    if output_path:
        df.to_excel(output_path, index=False)
        logger.info(f"已生成 dummy 监控数据: {output_path} ({num_channels}通道, {num_points}点)")
        return output_path

    # 返回临时路径
    import tempfile
    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    df.to_excel(tmp.name, index=False)
    logger.info(f"已生成 dummy 监控数据: {tmp.name}")
    return tmp.name


# ── 批量处理 ─────────────────────────────────────────────────────────


def process_all_files(
    file_configs: dict[str, ColumnMapping],
    enable_drop: bool = True,
    enable_rate: bool = True,
    enable_limit: bool = True,
    enable_half_exclude: bool = True,
    current_limit_ua: float = 1.0,
    rate_limit: float = 10.0,
) -> tuple[list[QBDResult], list[dict]]:
    """处理所有已配置的文件，批量提取 TBD 并计算 QBD。

    Returns:
        (qbd_results, raw_tbd_rows)
    """
    all_channels: list[MonitoredChannel] = []
    all_tbd_candidates: list[TBDCandidate] = []

    for file_path, mapping in file_configs.items():
        try:
            channels, voltage, temp = parse_monitor_file(file_path, mapping)
            all_channels.extend(channels)

            for ch in channels:
                candidates = detect_tbd_points(
                    ch,
                    enable_drop=enable_drop,
                    enable_rate=enable_rate,
                    enable_limit=enable_limit,
                    current_limit_ua=current_limit_ua,
                    rate_limit=rate_limit,
                )
                all_tbd_candidates.extend(candidates)
        except Exception as e:
            logger.error(f"处理文件 {file_path} 失败: {e}")
            continue

    # 排除超过一半同时失效
    if enable_half_exclude:
        all_tbd_candidates = _exclude_half_failure(
            all_tbd_candidates, total_channels=len(all_channels))

    # 构建结果
    qbd_results: list[QBDResult] = []
    raw_tbd_rows: list[dict] = []

    for tbd in all_tbd_candidates:
        # 用 (文件路径, 通道名) 查找，避免不同文件同名通道冲突
        ch = None
        for c in all_channels:
            if c.file_path == tbd.file_path and c.name == tbd.channel_name:
                ch = c
                break
        if ch is None:
            continue

        qbd_val = calculate_qbd(ch, tbd.tbd_time)

        # QBD = 积分电流 = 库仑
        qbd_results.append(QBDResult(
            channel_name=tbd.channel_name,
            tbd_time=tbd.tbd_time,
            tbd_current=tbd.tbd_current,
            qbd=qbd_val,
            voltage=ch.voltage,
            temperature=ch.temperature,
            file_path=ch.file_path,
        ))

        raw_tbd_rows.append({
            "文件": Path(ch.file_path).name,
            "通道": tbd.channel_name,
            "TBD时间(秒)": round(tbd.tbd_time, 2),
            "TBD电流(A)": f"{tbd.tbd_current:.6e}",
            "失效原因": tbd.failure_reason,
            "QBD(C)": f"{qbd_val:.6e}",
            "电压(V)": ch.voltage,
            "温度(℃)": ch.temperature if ch.temperature is not None else "",
            "确认": "是" if tbd.confirmed else "否",
            "备注": tbd.note,
        })

    return qbd_results, raw_tbd_rows
