"""
FT 文件解析 — 统一的数据类。
"""
from __future__ import annotations

import csv
import io
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class FTParseError(Exception):
    """FT 文件解析失败时抛出。"""
    pass


DEFAULT_CONFIG_TOML = """
[[signatures]]
format_id = "STS8200_FT_REV"
display_name = "STS8200 FT反向格式（meta头在后）"
header_identifiers = ["SITE_NUM", "SOFT_BIN"]
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
column_map = {SN = "PART_ID"}

[[signatures]]
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
column_map = {MODULE_ID = "PART_ID", BIN = "SOFT_BIN"}

[meta_columns]
PART_ID = "PART_ID"
SOFT_BIN = "SOFT_BIN"
file = "file"
Product = "Product"
SubProduct = "SubProduct"
TestTime = "TestTime"
TestingTime = "TestingTime"
"""


class FTData:
    """一个 FT 数据文件的解析结果。

    Parameters
    ----------
    path : str | Path
        FT 数据文件路径（.csv / .xlsx / .txt / .dat）
    config_path : str | Path
        配置文件路径（ft_data_config.toml）。
    """

    def __init__(self, path: str | Path, config_path: str | Path):
        self._path = Path(path)
        if not self._path.exists():
            raise FTParseError(f"文件不存在: {self._path}")

        cfg = Path(config_path) if config_path else Path("ft_data_config.toml")
        if not cfg.exists():
            # 配置文件不存在则自动用默认配置新建
            cfg.parent.mkdir(parents=True, exist_ok=True)
            cfg.write_text(DEFAULT_CONFIG_TOML, encoding="utf-8")
        self._config = self._load_config(cfg)

        self._raw_lines: list[str] = []
        self._df: pd.DataFrame | None = None
        self._units: dict[str, str] = {}
        self._lower_limits: dict[str, float] = {}
        self._higher_limits: dict[str, float] = {}
        self._meta: dict = {}
        self._meta_header: list[str] = []
        self._test_header: list[str] = []

        self._parse()

    # ══════════════════════════════════════════════════════════════
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
    # ══════════════════════════════════════════════════════════════

    @property
    def data(self) -> pd.DataFrame:
        if self._df is None or len(self._df) < 4:
            return pd.DataFrame()
        df = self._df.iloc[3:].reset_index(drop=True)
        for col in self._test_header:
            if col in df.columns:
                df[col] = df[col].astype(float)
        return df

    @property
    def raw_df(self) -> pd.DataFrame:
        return self._df.copy() if self._df is not None else pd.DataFrame()

    @property
    def units(self) -> dict[str, str]:
        return dict(self._units)

    @property
    def lower_limits(self) -> dict[str, float]:
        return dict(self._lower_limits)

    @property
    def higher_limits(self) -> dict[str, float]:
        return dict(self._higher_limits)

    @property
    def test_columns(self) -> list[str]:
        if self._df is None:
            return []
        return list(self._test_header)

    @property
    def meta_columns(self) -> list[str]:
        if self._df is None:
            return []
        return list(self._meta_header)

    @property
    def path(self) -> Path:
        return self._path

    def __repr__(self) -> str:
        return (
            f"FTData({self._path.name}, "
            f"{len(self.test_columns)} tests, "
            f"{len(self.data)} rows)"
        )

    # ══════════════════════════════════════════════════════════════
    #  Config
    # ══════════════════════════════════════════════════════════════

    def _load_config(self, config_path: str | Path) -> dict:
        """加载 ft_data_config.toml，返回配置 dict。"""
        import tomllib
        config_path = Path(config_path)
        if not config_path.exists():
            raise FTParseError(f"配置文件不存在: {config_path}")

        with open(config_path, "rb") as f:
            return tomllib.load(f)

    # ══════════════════════════════════════════════════════════════
    #  主解析流程
    # ══════════════════════════════════════════════════════════════

    def _parse(self):
        # 1. 检测格式
        fmt = self._detect_format()
        self._fmt = fmt
        sig = fmt["sig"]
        delimiter = fmt["delimiter"]
        header_row = fmt["header_row"]
        header_cols_raw = fmt["header_cols"]

        # 2. 读原始行
        text = self._path.read_text(encoding=fmt["encoding"])
        self._raw_lines = text.splitlines()

        # 3. 合并 part_id 行和 data_col_header 行 → 完整列名
        #    part_id_offset: PART_ID/SOFT_BIN 所在行（相对 header_row）
        #    data_col_header_offset: 测试项列名行
        pid_off = sig.get("part_id_offset", 0)
        dch_off = sig.get("data_col_header_offset", 0)
        pid_row_idx = header_row + pid_off
        dch_row_idx = header_row + dch_off

        # 兼容：如果偏移相同就只用一行
        if pid_row_idx == dch_row_idx:
            merged_header = list(header_cols_raw)
        else:
            pid_cells = self._split_line(pid_row_idx, delimiter) if pid_row_idx < len(self._raw_lines) else []
            dch_cells = self._split_line(dch_row_idx, delimiter) if dch_row_idx < len(self._raw_lines) else []
            merged_header = self._merge_row_pair(pid_cells, dch_cells)

        # 4. 列名映射（column_map）
        column_map = sig.get("column_map", {})
        final_headers = [column_map.get(c, c) for c in merged_header]

        # 5. 用 pre_test_columns 定位测试列起始位置
        pre_cols: list[str] = sig.get("pre_test_columns", [])
        test_start = self._find_test_start(final_headers, pre_cols)
        if test_start < 0:
            raise FTParseError(
                f"签名 {sig.get('format_id')} pre_test_columns {pre_cols} "
                f"在表头中未找到: {final_headers}"
            )

        # 6. 拆分为 meta 列和测试列
        meta_header = final_headers[:test_start]
        test_header = final_headers[test_start:]
        self._meta_header = meta_header
        self._test_header = test_header

        # 7. 读取各偏移行的数据
        #    单位行 / 下限行 / 上限行 / 数据起始行
        unit_row = self._safe_row(header_row + sig.get("unit_offset", -1), delimiter)
        ll_row = self._safe_row(header_row + sig.get("lower_limit_offset", -1), delimiter)
        hl_row = self._safe_row(header_row + sig.get("higher_limit_offset", -1), delimiter)

        data_start = fmt["data_start"]
        data_rows_raw = self._raw_lines[data_start:] if data_start < len(self._raw_lines) else []

        # 8. 构建完整列名列表（meta 列 + 测试列）
        all_cols = meta_header + test_header

        # 9. 构建 DataFrame（三行 meta + 数据行）
        meta_data = []
        # 单位行
        if unit_row:
            meta_data.append(self._pad_to(unit_row, all_cols))
        else:
            meta_data.append([None] * len(all_cols))
        # 下限行
        if ll_row:
            meta_data.append(self._pad_to(ll_row, all_cols))
        else:
            meta_data.append([None] * len(all_cols))
        # 上限行
        if hl_row:
            meta_data.append(self._pad_to(hl_row, all_cols))
        else:
            meta_data.append([None] * len(all_cols))

        # 数据行
        parsed_data = []
        for line in data_rows_raw:
            stripped = line.strip()
            if not stripped:
                if sig.get("stop_at_blank_row", True):
                    break
                continue
            cells = self._split_delimiter(stripped, delimiter)
            parsed_data.append(self._pad_to(cells, all_cols))

        all_rows = meta_data + parsed_data
        self._df = pd.DataFrame(all_rows, columns=all_cols)

        # 10. 提取单位 / limit 到 dict
        self._extract_meta_rows()

        # 11. 单位转换 + 统一数值列
        self._apply_unit_conversion()

        # 12. 过滤无效行
        self._filter_rows()

        # 13. 验证
        self._validate()

    # ══════════════════════════════════════════════════════════════
    #  格式检测
    # ══════════════════════════════════════════════════════════════

    def _detect_format(self) -> dict[str, Any]:
        """检测文件格式，返回格式信息 dict。"""
        signatures: list[dict] = self._config.get("signatures", [])
        if not signatures:
            raise FTParseError("无可用的格式签名配置，请检查配置文件。")

        encodings: list[str] = []
        seen_enc = set()
        for sig in signatures:
            enc = sig.get("encoding", "utf-8-sig")
            if enc not in seen_enc:
                encodings.append(enc)
                seen_enc.add(enc)
        if "utf-8-sig" in encodings:
            encodings.remove("utf-8-sig")
            encodings.insert(0, "utf-8-sig")

        best: dict | None = None
        best_id_count = -1

        for enc in encodings:
            try:
                text = self._path.read_text(encoding=enc)
            except Exception:
                continue

            lines = text.splitlines()
            if not lines:
                continue

            for sig_idx, sig in enumerate(signatures):
                delimiter = sig.get("delimiter", ",")
                identifiers = sig.get("header_identifiers", [])
                if not identifiers:
                    continue

                id_count = len(identifiers)
                min_cols = sig.get("min_detected_cols", 0)

                if best is not None and id_count < best_id_count:
                    continue
                if best is not None and id_count == best_id_count and sig_idx >= signatures.index(best["sig"]):
                    continue

                idents: list[tuple[str, str]] = []
                for ident in identifiers:
                    id_up = ident.upper()
                    if id_up.endswith("_"):
                        idents.append(("startswith", id_up.rstrip("_")))
                    else:
                        idents.append(("exact", id_up))

                for row_idx, line in enumerate(lines):
                    stripped = line.strip()
                    if not stripped:
                        continue
                    cells = stripped.split(delimiter)
                    upper_cols = {c.strip().strip('\ufeff').upper()
                                  for c in cells if c.strip()}

                    all_hit = True
                    for mode, val in idents:
                        if mode == "exact":
                            if val not in upper_cols:
                                all_hit = False
                                break
                        elif mode == "startswith":
                            if not any(c.startswith(val) for c in upper_cols):
                                all_hit = False
                                break

                    if not all_hit:
                        continue

                    detected_cols = [c for c in cells if c.strip()]
                    if len(detected_cols) < min_cols:
                        continue

                    data_start_offset = sig.get("data_start_offset", 1)
                    best = {
                        "sig": sig,
                        "header_row": row_idx,
                        "header_cols": [c.strip().strip('\ufeff')
                                        for c in cells],
                        "data_start": row_idx + data_start_offset,
                        "encoding": enc,
                        "delimiter": delimiter,
                    }
                    best_id_count = id_count
                    break

        if best is None:
            raise FTParseError(
                f"无法识别文件格式: {self._path}\n已尝试 encoding: {encodings}"
            )
        return best

    # ══════════════════════════════════════════════════════════════
    #  辅助方法
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def _split_delimiter(line: str, delimiter: str) -> list[str]:
        """按分隔符拆分一行，返回清理后的单元格列表。"""
        return [c.strip().strip('\ufeff') for c in line.split(delimiter)]

    def _split_line(self, row_idx: int, delimiter: str) -> list[str]:
        """从 self._raw_lines 中按行号取一行并拆分。"""
        if row_idx < 0 or row_idx >= len(self._raw_lines):
            return []
        return self._split_delimiter(self._raw_lines[row_idx], delimiter)

    def _safe_row(self, row_idx: int, delimiter: str) -> list[str]:
        """安全取一行，越界返回空列表。
        允许负数索引（指向 header 之前的行）。"""
        return self._split_line(row_idx, delimiter) if 0 <= row_idx < len(self._raw_lines) else []

    @staticmethod
    def _merge_row_pair(row_a: list[str], row_b: list[str]) -> list[str]:
        """合并两行列名：优先取非空值。
        row_a 通常是 part_id 行（PART_ID, SOFT_BIN, 空, 空...）
        row_b 通常是 data_col_header 行（空, 空, DC_T1, DC_T2...）
        """
        max_len = max(len(row_a), len(row_b))
        merged = []
        for i in range(max_len):
            a = row_a[i].strip() if i < len(row_a) else ""
            b = row_b[i].strip() if i < len(row_b) else ""
            merged.append(a if a else b)
        return merged

    @staticmethod
    def _pad_to(cells: list[str], target_cols: list[str]) -> list:
        """将单元格列表填充/截断到目标列数。"""
        result: list = list(cells)
        while len(result) < len(target_cols):
            result.append(None)
        return result[:len(target_cols)]

    @staticmethod
    def _find_test_start(headers: list[str],
                         pre_test_columns: list[str]) -> int:
        """用 pre_test_columns 依次匹配，找到第一个存在的列名，
        返回该列之后的索引（即测试列起始位置）。

        如果 pre_test_columns 为空，返回 0（全部视为测试列）。
        如果所有 pre_test_columns 都不在 headers 中，返回 -1。
        """
        if not pre_test_columns:
            return 0

        headers_upper = [h.upper() for h in headers]

        for ptc in pre_test_columns:
            ptc_up = ptc.upper()
            for idx, h in enumerate(headers_upper):
                if h == ptc_up:
                    return idx + 1  # 这一列之后都是测试列

        return -1

    def _extract_meta_rows(self):
        """从 self._df 前三行提取 Unit/LL/HL。"""
        if self._df is None or len(self._df) < 3:
            return

        for col in self._df.columns:
            if col.upper() in {c.upper() for c in self._meta_header}:
                continue
            try:
                unit_val = str(self._df.iloc[0][col])
                if unit_val and unit_val not in ("nan", "None", ""):
                    self._units[col] = unit_val
            except Exception:
                pass
            try:
                ll_val = self._df.iloc[1][col]
                if ll_val is not None and str(ll_val) != "nan":
                    self._lower_limits[col] = float(ll_val)
            except (ValueError, TypeError):
                pass
            try:
                hl_val = self._df.iloc[2][col]
                if hl_val is not None and str(hl_val) != "nan":
                    self._higher_limits[col] = float(hl_val)
            except (ValueError, TypeError):
                pass

    def _apply_unit_conversion(self):
        """将数据部分的值转为 SI 单位 + 统一数值列（向量化）。"""
        from core.unit_converter import UnitConverter

        if self._df is None or len(self._df) < 4:
            return

        meta_header_upper = {c.upper() for c in self._meta_header}
        data_idx = range(3, len(self._df))

        for col in self._df.columns:
            if col.upper() in meta_header_upper:
                continue
            unit_str = self._units.get(col, "")
            col_idx = self._df.columns.get_loc(col)

            raw = self._df.iloc[data_idx, col_idx]
            numeric = pd.to_numeric(raw, errors="coerce")

            if unit_str:
                si_unit, multiplier = UnitConverter.parse_unit(unit_str)
                if callable(multiplier):
                    numeric = numeric.apply(multiplier)
                elif multiplier != 1.0:
                    numeric = numeric * multiplier
                self._units[col] = si_unit if si_unit else unit_str

            self._df.iloc[data_idx, col_idx] = numeric
            # 即使 multiplier=1 也做了 float 转换
            # 更新单位行为 SI 单位
            self._units[col] = si_unit if si_unit else unit_str

    def _filter_rows(self):
        """过滤无效行。

        - 跳过 PART_ID 为 "1" 或 "END" 的行
        - 遇到全空行停止（后续行丢弃）
        """
        if self._df is None or len(self._df) < 4:
            return

        sig = self._fmt["sig"] if self._fmt else {}
        skip_values = sig.get("skip_row_values", {})

        # 前 3 行（Unit/LL/HL）不动
        keep = list(range(3))
        for i in range(3, len(self._df)):
            row = self._df.iloc[i]

            # 检查是否要跳过
            skip_this = False
            for col, vals in skip_values.items():
                if col in self._df.columns:
                    cell_val = str(row[col]).strip()
                    if cell_val in vals:
                        skip_this = True
                        break
            if skip_this:
                continue

            # 检查是否全空 → 停止
            if row.isna().all() or all(str(v).strip() == "" for v in row):
                break

            keep.append(i)

        self._df = self._df.iloc[keep].reset_index(drop=True)

    def _validate(self):
        """验证解析结果。"""
        if self._df is None or self._df.empty:
            raise FTParseError(f"解析结果为空: {self._path}")

        if "PART_ID" not in self._df.columns:
            raise FTParseError(f"缺少关键列 PART_ID: {self._path}")

        if len(self._df) < 4:
            raise FTParseError(f"数据行不足（含 meta 仅 {len(self._df)} 行）: {self._path}")

        test_cols = self.test_columns
        if not test_cols:
            raise FTParseError(f"未找到测试列: {self._path}")
