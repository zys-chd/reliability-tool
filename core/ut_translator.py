"""
UT 文件翻译器。

将 UT（Unit Test）文件中的测试列名按照 ut_config 映射为标准 FT 格式。
UT 文件指文件名中包含 "UT" 或 "ut" 的文件。
"""
import os
import tempfile
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from .file_parser import ParserManager

logger = logging.getLogger(__name__)


def is_ut_file(filepath: str) -> bool:
    """判断文件名是否包含 UT 标记"""
    basename = os.path.basename(filepath)
    return "UT" in basename or "ut" in basename


def build_column_mapping(ut_config: list[dict]) -> dict[str, str]:
    """从 ut_config 构建列名映射表 {原测试项: 输出测试项}

    Args:
        ut_config: UT 配置列表，每项为字典：
            {"测试机台": "...", "原测试项": "IGSS", ..., "输出测试项": "DC_IGSS", ...}

    Returns:
        映射字典，如 {"IGSS": "DC_IGSS"}
    """
    mapping = {}
    for row in ut_config:
        src = row.get("原测试项", "").strip()
        dst = row.get("输出测试项", "").strip()
        if src and dst:
            mapping[src] = dst
    return mapping


def translate_ut_file(
    filepath: str,
    column_mapping: dict[str, str],
    parser_manager: Optional[ParserManager] = None,
) -> Optional[str]:
    """翻译单个 UT 文件，返回临时 CSV 路径（或 None 表示无需翻译）"""
    import pandas as pd

    # 读取文件
    if parser_manager is not None:
        df = parser_manager.read(filepath)
    else:
        # 兜底：按 csv 读取
        try:
            df = pd.read_csv(filepath, skiprows=4, dtype=str)
        except Exception:
            logger.warning(f"无法读取 UT 文件: {filepath}")
            return None

    if df.empty:
        logger.warning(f"UT 文件为空: {filepath}")
        return None

    # 重命名匹配的列
    renamed = 0
    new_columns = []
    for col in df.columns:
        col_stripped = col.strip()
        if col_stripped in column_mapping:
            new_columns.append(column_mapping[col_stripped])
            renamed += 1
        else:
            new_columns.append(col)
    df.columns = new_columns

    if renamed == 0:
        logger.info(f"UT 文件 {filepath}: 没有匹配的列，按原样返回")
        return filepath

    # 写出临时 CSV（带标准表头行）
    fd, tmp_path = tempfile.mkstemp(suffix=".csv", prefix="ut_translated_")
    os.close(fd)
    # 写入元信息行（空行 + 标准结构）
    with open(tmp_path, "w", newline="") as f:
        # 写入4行元信息
        f.write("UT Translated File\n")
        f.write("header\n")
        f.write("lower\n")
        f.write("upper\n")
    # 追加 DataFrame 数据
    df.to_csv(tmp_path, mode="a", index=False)
    logger.info(f"UT 文件 {filepath} 已翻译 -> {tmp_path} ({renamed} 列映射)")
    return tmp_path


def translate_ut_files(
    file_paths: list[str],
    ut_config: list[dict],
    parser_manager: Optional[ParserManager] = None,
) -> list[str]:
    """翻译 UT 文件列表。

    UT 文件通过文件名中的 "UT"/"ut" 标记识别。
    将 UT 文件中的测试列名按照 ut_config 映射后输出为临时 CSV，
    返回原始非 UT 文件 + 翻译后 UT 文件的路径列表。

    Args:
        file_paths: 待处理的文件路径列表（混合 UT 和非 UT）
        ut_config: UT 配置列表，每项包含 "原测试项" 和 "输出测试项"
        parser_manager: 可选的解析器管理器实例

    Returns:
        处理后的文件路径列表（非 UT 文件原样保留 + UT 文件的翻译结果）
    """
    if not ut_config:
        # 没有 UT 配置时直接返回原列表
        return list(file_paths)

    column_mapping = build_column_mapping(ut_config)

    if not column_mapping:
        logger.warning("UT 配置中存在映射关系，跳过 UT 翻译")
        return list(file_paths)

    ut_files = []
    non_ut_files = []

    for fp in file_paths:
        if is_ut_file(fp):
            ut_files.append(fp)
        else:
            non_ut_files.append(fp)

    if not ut_files:
        return non_ut_files

    logger.info(f"发现 {len(ut_files)} 个 UT 文件，开始翻译")

    translated = []
    for fp in ut_files:
        result = translate_ut_file(fp, column_mapping, parser_manager)
        if result is not None:
            translated.append(result)
        else:
            # 翻译失败时保留原文件
            translated.append(fp)

    result_files = non_ut_files + translated
    return result_files
