"""Utilities for handling Windows path-length limitations.

On Windows the classic MAX_PATH (260) limit can cause silent failures when
writing output files. This module provides helpers to detect and warn about
excessively long paths before operations are attempted.
"""

import sys
from pathlib import Path
from typing import Union

#: Threshold (characters) above which a warning is emitted.
#: Windows default limit is 260, so 250 leaves a small safety margin.
MAX_PATH_WARN = 250

PathLike = Union[str, Path]


def check_path_length(path: PathLike) -> list[str]:
    """Return a list of warning messages if *path* is too long for Windows.

    On non-Windows platforms the list is always empty.
    """
    warnings: list[str] = []
    if sys.platform == "win32":
        p = str(path)
        if len(p) > MAX_PATH_WARN:
            warnings.append(
                f"路径过长 ({len(p)} 字符)，Windows 默认只能处理最多 260 字符。\n"
                f"建议将文件移到更短的路径下，或启用长路径支持。"
            )
    return warnings


def warn_on_long_path(path: PathLike) -> None:
    """Convenience: log any path-length warnings via ``logging.getLogger``.

    Uses a module-level logger named ``core.path_utils``.
    """
    import logging

    logger = logging.getLogger(__name__)
    for msg in check_path_length(path):
        logger.warning(msg)
