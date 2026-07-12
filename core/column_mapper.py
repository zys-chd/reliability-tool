"""
Column name mapper for FT data files.
Maps equipment-specific column names to standard internal names.
"""

import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── External config loading ──

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
MAPPINGS_TOML = CONFIG_DIR / "column_mappings.toml"


def _write_default_mappings():
    """Write built-in mappings to the TOML file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    content = "# 列名映射配置 — 编辑此文件可添加新的列名映射规则\n"
    content += "# 格式: RAW_COLUMN_NAME = \"标准列名\"\n"
    content += "# 修改后重启应用生效\n\n"
    content += "[mappings]\n"
    builtin = {
        "MODULE_ID": "PART_ID", "MODULE": "PART_ID", "DEVICE": "PART_ID",
        "DIE_ID": "PART_ID", "SN": "PART_ID", "LOT": "PART_ID", "WAFER": "PART_ID",
        "BIN": "SOFT_BIN", "BIN_NO": "SOFT_BIN", "BIN_NUMBER": "SOFT_BIN",
        "BIN_NUM": "SOFT_BIN", "RESULT": "SOFT_BIN", "HARD_BIN": "SOFT_BIN",
        "TEST_RESULT": "SOFT_BIN", "PASS_FAIL": "SOFT_BIN", "PF": "SOFT_BIN",
        "CONDITION": "GROUP", "TEST_CONDITION": "GROUP", "TESTCOND": "GROUP",
        "SITE": "SITE", "DIE_X": "DIE_X", "DIE_Y": "DIE_Y",
        "X_COORD": "DIE_X", "Y_COORD": "DIE_Y",
    }
    for raw, std in sorted(builtin.items()):
        content += f'{raw} = "{std}"\n'
    MAPPINGS_TOML.write_text(content, encoding="utf-8")
    logger.info(f"已生成默认列映射配置: {MAPPINGS_TOML}")


def _load_external_mappings() -> dict[str, str]:
    """Load column mappings from external config/column_mappings.toml.

    If the file doesn't exist, creates it with built-in defaults.
    Falls back to built-in defaults if file is malformed.
    External mappings override built-in ones by key name.
    """
    builtin = {
        "MODULE_ID": "PART_ID", "MODULE": "PART_ID", "DEVICE": "PART_ID",
        "DIE_ID": "PART_ID", "SN": "PART_ID", "LOT": "PART_ID", "WAFER": "PART_ID",
        "PART": "PART_ID", "PARTNO": "PART_ID", "PART_NUMBER": "PART_ID",
        "BIN": "SOFT_BIN", "BIN_NO": "SOFT_BIN", "BIN_NUMBER": "SOFT_BIN",
        "BIN_NUM": "SOFT_BIN", "RESULT": "SOFT_BIN", "HARD_BIN": "SOFT_BIN",
        "TEST_RESULT": "SOFT_BIN", "PASS_FAIL": "SOFT_BIN", "PF": "SOFT_BIN",
        "GROUP": "GROUP", "CONDITION": "GROUP", "TEST_CONDITION": "GROUP",
        "TESTCOND": "GROUP",
        "SITE": "SITE", "DIE_X": "DIE_X", "DIE_Y": "DIE_Y",
        "X_COORD": "DIE_X", "Y_COORD": "DIE_Y",
    }

    if not MAPPINGS_TOML.exists():
        _write_default_mappings()
        return dict(builtin)

    try:
        import tomllib
        with open(MAPPINGS_TOML, "rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        logger.warning(
            f"Failed to load {MAPPINGS_TOML}: {e}. "
            f"Using built-in mappings."
        )
        return dict(builtin)

    external = data.get("mappings", {})
    if not external:
        return dict(builtin)

    # Merge: external overrides built-in
    merged = dict(builtin)
    merged.update(external)
    return merged


# Known mapping: raw column name (uppercase) → standard name
KNOWN_MAPPINGS = _load_external_mappings()


class ColumnMapper:
    """Map raw column names to standardized internal names."""

    def __init__(self, extra_mappings: dict[str, str] | None = None):
        self._mappings = dict(KNOWN_MAPPINGS)
        if extra_mappings:
            self._mappings.update({k.upper(): v for k, v in extra_mappings.items()})

    def auto_detect(self, columns: list[str]) -> dict[str, str]:
        """Auto-detect column mapping for the given column list.
        Returns: {original_name: standard_name, ...}
        """
        mapping = {}
        for col in columns:
            col_upper = col.strip().upper()
            if col_upper in self._mappings:
                std = self._mappings[col_upper]
                if std != col_upper:  # only map if different
                    mapping[col] = std
            # Test parameter columns (like DC_IGSS_1, IGSS@-1V) pass through
        return mapping

    def apply(self, df: 'pd.DataFrame', mapping: dict[str, str] | None = None) -> 'pd.DataFrame':
        """Apply column mapping to a DataFrame. Returns a new DataFrame."""
        import pandas as pd
        if mapping is None:
            mapping = self.auto_detect(list(df.columns))
        if mapping:
            return df.rename(columns=mapping)
        return df.copy()

    def add_mapping(self, raw_name: str, standard_name: str):
        """Add or override a column mapping."""
        self._mappings[raw_name.upper()] = standard_name

    @staticmethod
    def is_test_column(col_name: str) -> bool:
        """Check if a column name looks like a test parameter (not metadata)."""
        col_upper = col_name.strip().upper()
        if col_upper in KNOWN_MAPPINGS:
            return False
        if col_upper in {"PART_ID", "SOFT_BIN", "GROUP", "FILEPATH", "SITE",
                          "DIE_X", "DIE_Y", "FILE", "NAME"}:
            return False
        return True
