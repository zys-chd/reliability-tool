"""Apply all changes to FT_file_parser.py"""
import re

path = "/run/media/zys/7C64A61F64A5DBE0/reliability-tool/core/FT_file_parser.py"
with open(path, "r") as f:
    content = f.read()

# 1. Remove META_COLUMNS
content = re.sub(
    r'# 标准元数据列.*?\nMETA_COLUMNS = \[.*?\n\]\n\n',
    '',
    content,
    flags=re.DOTALL
)

# 2. Add STS8200_FT_REV before DEFAULT_FT_FILE in DEFAULT_CONFIG_TOML
old_sig_block = """[[signatures]]
format_id = "DEFAULT_FT_FILE"
display_name = "默认FT文件"
header_identifiers = ["PART_ID", "SOFT_BIN"]
part_id_offset = 0
data_col_header_offset = 0
unit_offset = 1
lower_limit_offset = 2
higher_limit_offset = 3
data_start_offset = 4
pre_test_columns = ["SOFT_BIN"]
stop_at_blank_row = true
skip_blank_rows = true
delimiter = ","
encoding = "utf-8-sig"
skip_row_values = {PART_ID = ["1", "END"]}
column_map = {MODULE_ID = "PART_ID", BIN = "SOFT_BIN"}"""

new_sig_block = """[[signatures]]
format_id = "STS8200_FT_REV"
display_name = "STS8200 FT反向格式（meta头在后）"
header_identifiers = ["PART_ID", "SOFT_BIN"]
part_id_offset = 0
data_col_header_offset = -4
unit_offset = -3
lower_limit_offset = -2
higher_limit_offset = -1
data_start_offset = 1
pre_test_columns = ["TEST_NUM"]
stop_at_blank_row = true
skip_blank_rows = true
delimiter = ","
encoding = "utf-8-sig"
skip_row_values = {PART_ID = ["1", "END"]}
column_map = {}

""" + old_sig_block

content = content.replace(old_sig_block, new_sig_block, 1)

# 3. Update __init__
old_init = """    def __init__(self, path: str | Path, config_path: str | Path):
        self._path = Path(path)
        if not self._path.exists():
            raise FTParseError(f"文件不存在: {self._path}")

        cfg = Path(config_path) if config_path else Path(__file__).parent.parent / "config" / "ft_data_config.toml"
        if not cfg.exists():
            cfg.parent.mkdir(parents=True, exist_ok=True)
            cfg.write_text(DEFAULT_CONFIG_TOML, encoding="utf-8")
        self._config = self._load_config(cfg)

        self._meta_header: list[str] = []
        self._test_header: list[str] = []
        self._raw_lines: list[str] = []
        self._df: pd.DataFrame | None = None
        self._units: dict[str, str] = {}
        self._lower_limits: dict[str, float] = {}
        self._higher_limits: dict[str, float] = {}
        self._meta: dict = {}

        self._parse()"""

new_init = """    def __init__(self, path: str | Path, config_path: str | Path,
                 force_reparse: bool = False):
        self._path = Path(path)
        if not self._path.exists():
            raise FTParseError(f"文件不存在: {self._path}")

        self._meta_header: list[str] = []
        self._test_header: list[str] = []
        self._raw_lines: list[str] = []
        self._df: pd.DataFrame | None = None
        self._units: dict[str, str] = {}
        self._lower_limits: dict[str, float] = {}
        self._higher_limits: dict[str, float] = {}
        self._meta: dict = {}
        self._fmt: dict | None = None
        self._config: dict = {}

        if not force_reparse:
            from core.ft_cache import ft_cache
            cached = ft_cache.get(str(self._path))
            if cached is not None:
                self._load_state(cached)
                return

        cfg = Path(config_path) if config_path else Path(__file__).parent.parent / "config" / "ft_data_config.toml"
        if not cfg.exists():
            cfg.parent.mkdir(parents=True, exist_ok=True)
            cfg.write_text(DEFAULT_CONFIG_TOML, encoding="utf-8")
        self._config = self._load_config(cfg)

        self._parse()

        try:
            from core.ft_cache import ft_cache
            ft_cache.put(str(self._path), self._dump_state())
        except Exception:
            pass"""

content = content.replace(old_init, new_init, 1)

# 4. Add _dump_state/_load_state before "Public API"
content = content.replace(
    "    # ══════════════════════════════════════════════════════════════\n    #  Public API\n    # ══════════════════════════════════════════════════════════════",
    """    # ══════════════════════════════════════════════════════════════
    #  缓存序列化
    # ══════════════════════════════════════════════════════════════

    def _dump_state(self) -> dict:
        return {
            "_df": self._df,
            "_units": self._units,
            "_lower_limits": self._lower_limits,
            "_higher_limits": self._higher_limits,
            "_meta_header": self._meta_header,
            "_test_header": self._test_header,
            "_meta": self._meta,
            "_fmt": self._fmt,
            "_config": self._config,
        }

    def _load_state(self, state: dict):
        self._df = state.get("_df")
        self._units = state.get("_units", {})
        self._lower_limits = state.get("_lower_limits", {})
        self._higher_limits = state.get("_higher_limits", {})
        self._meta_header = state.get("_meta_header", [])
        self._test_header = state.get("_test_header", [])
        self._meta = state.get("_meta", {})
        self._fmt = state.get("_fmt")
        self._config = state.get("_config", {})

    # ══════════════════════════════════════════════════════════════
    #  Public API
    # ══════════════════════════════════════════════════════════════""",
    1
)

# 5. Save _fmt in _parse
content = content.replace(
    "        fmt = self._detect_format()\n        sig = fmt[\"sig\"]",
    "        fmt = self._detect_format()\n        self._fmt = fmt\n        sig = fmt[\"sig\"]",
    1
)

# 6. Update step labels
content = content.replace(
    "        # 11. 单位转换\n        self._apply_unit_conversion()\n\n        # 12. 过滤无效行\n        self._filter_rows()\n\n        # 13. 验证",
    "        # 11. 单位转换 + 统一数值列\n        self._apply_unit_conversion()\n\n        # 12. 过滤无效行\n        self._filter_rows()\n\n        # 13. 验证",
    1
)

# 7. Vectorized _apply_unit_conversion
old_uc = """    def _apply_unit_conversion(self):
        \"\"\"将数据部分的值转为 SI 单位。\"\"\"
        from core.unit_converter import UnitConverter

        if self._df is None or len(self._df) < 3:
            return

        for col in self._df.columns:
            if col in self._meta_header:
                continue
            unit_str = self._units.get(col, \"\")
            if not unit_str:
                continue

            si_unit, multiplier = UnitConverter.parse_unit(unit_str)
            for i in range(3, len(self._df)):
                try:
                    val = float(self._df.iloc[i][col])
                    if callable(multiplier):
                        self._df.iloc[i, self._df.columns.get_loc(col)] = multiplier(val)
                    elif multiplier != 1.0:
                        self._df.iloc[i, self._df.columns.get_loc(col)] = val * multiplier
                    else:
                        self._df.iloc[i, self._df.columns.get_loc(col)] = val
                except (ValueError, TypeError):
                    pass
            self._units[col] = si_unit if si_unit else unit_str"""

new_uc = """    def _apply_unit_conversion(self):
        \"\"\"将数据部分的值转为 SI 单位 + 统一数值列（向量化）。\"\"\"
        from core.unit_converter import UnitConverter

        if self._df is None or len(self._df) < 4:
            return

        meta_header_upper = {c.upper() for c in self._meta_header}
        data_idx = range(3, len(self._df))

        for col in self._df.columns:
            if col.upper() in meta_header_upper:
                continue
            unit_str = self._units.get(col, \"\")
            col_idx = self._df.columns.get_loc(col)

            raw = self._df.iloc[data_idx, col_idx]
            numeric = pd.to_numeric(raw, errors=\"coerce\")

            if unit_str:
                si_unit, multiplier = UnitConverter.parse_unit(unit_str)
                if callable(multiplier):
                    numeric = numeric.apply(multiplier)
                elif multiplier != 1.0:
                    numeric = numeric * multiplier
                self._units[col] = si_unit if si_unit else unit_str

            self._df.iloc[data_idx, col_idx] = numeric"""

content = content.replace(old_uc, new_uc, 1)

# 8. _filter_rows use self._fmt
content = content.replace(
    "        sig = self._detect_format()[\"sig\"]",
    "        sig = self._fmt[\"sig\"] if self._fmt else {}",
    1
)

# 9. data property with dtype conversion
old_data = """    @property
    def data(self) -> pd.DataFrame:
        if self._df is None or len(self._df) < 4:
            return pd.DataFrame()
        return self._df.iloc[3:].reset_index(drop=True)"""

new_data = """    @property
    def data(self) -> pd.DataFrame:
        if self._df is None or len(self._df) < 4:
            return pd.DataFrame()
        df = self._df.iloc[3:].reset_index(drop=True)
        for col in self._test_header:
            if col in df.columns:
                df[col] = df[col].astype(float)
        return df"""

content = content.replace(old_data, new_data, 1)

# 10. min_detected_cols in _detect_format
content = content.replace(
    "                id_count = len(identifiers)\n\n                if best is not None and id_count < best_id_count:",
    '                id_count = len(identifiers)\n                min_cols = sig.get("min_detected_cols", 0)\n\n                if best is not None and id_count < best_id_count:',
    1
)

content = content.replace(
    """                    if not all_hit:
                        continue

                    data_start_offset = sig.get("data_start_offset", 1)""",
    """                    if not all_hit:
                        continue

                    detected_cols = [c for c in cells if c.strip()]
                    if len(detected_cols) < min_cols:
                        continue

                    data_start_offset = sig.get("data_start_offset", 1)""",
    1
)

with open(path, "w") as f:
    f.write(content)

print("All changes applied successfully")
