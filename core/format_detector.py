"""File format detector for semiconductor FT data.
Detects file type, metadata rows, encoding, delimiter, and column mapping.

检测流程（新）：
  1. 读前 64 字节判定编码
  2. 读前 10 行统计分隔符
  3. 全文 CSV 解析 → rows
  4. 对每个 signature:
     a. 逐行找表头（header_identifiers 匹配 ≥ min_header_matches）
     b. 验证 pre_test_columns 在表头上按序存在
     c. 从表头按偏移量算出各元数据行位置
     d. 评分
  5. 取最高分 signature → FormatInfo

签名字段说明：
  header_identifiers    识别表头行的列名关键词
  min_header_matches    至少命中多少个关键词才算表头
  part_id_offset        相对表头的行偏移（PART_ID/SOFT_BIN 所在行）
  soft_bin_offset       同上
  data_col_header_offset 测试项列名所在行（0=与表头同行）
  unit_offset           单位行偏移（-1=无单位行）
  lower_limit_offset    下限行偏移（-1=无）
  higher_limit_offset   上限行偏移（-1=无）
  data_start_offset     数据从表头后第几行开始
  pre_test_columns      表头上测试列之前必须出现的列（有序）
  optional_pre_test_columns 可选的中间列
  skip_row_values       数据行中跳过条件 {列名: [值列表]}
  stop_at_blank_row     遇到空行是否停止读数据
  skip_blank_rows       meta→data 之间空行是否跳过
"""
import csv
import io
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class FormatInfo:
    """Detected file format information.

    核心属性：
      format_id      唯一格式标识符，如 "ets_csv_v4"
      display_name   中文显示名
      encoding       文件编码
      delimiter      CSV 分隔符
      header_rows    元数据行数（从 row 0 到第一个数据行）
      column_map     列名映射 {原始列名: 标准列名}
      confidence     匹配置信度 0-1
      meta_schema    元数据行 schema {行号: 类型}
      part_id_row    PART_ID 所在行
      soft_bin_row   SOFT_BIN 所在行
      data_start_row 第一个数据行的行号
      unit_row       单位行（-1 = 无）
      lower_limit_row 下限行
      higher_limit_row 上限行
    """
    format_id: str = "unknown"
    display_name: str = "未知格式"
    encoding: str = "utf-8-sig"
    delimiter: str = ","
    header_rows: int = 4
    column_map: dict[str, str] = field(default_factory=dict)
    confidence: float = 0.0

    # 元数据行 schema
    meta_schema: dict[int, str] = field(default_factory=lambda: {
        0: "header", 1: "unit", 2: "lower_limit", 3: "higher_limit",
    })

    # 行位置跟踪
    part_id_row: int = 0
    soft_bin_row: int = 0
    data_start_row: int = -1
    unit_row: int = -1
    lower_limit_row: int = -1
    higher_limit_row: int = -1

    # 新字段：用于 parser
    data_col_header_row: int = 0       # 测试项列名所在行
    skip_row_values: dict[str, list[str]] = field(default_factory=dict)
    stop_at_blank_row: bool = True


# ═══════════════════════════════════════════════════════════════════
#  设备签名表
# ═══════════════════════════════════════════════════════════════════

BUILTIN_SIGNATURES = [
    # ── ETS-300/400 标准 CSV（4 行元数据） ──
    # 行0: PART_ID, SOFT_BIN, DC_IGSS_1, DC_BV_1, ...    (header + data_col_header)
    # 行1: Unit
    # 行2: Lower Limit
    # 行3: Higher Limit
    # 行4+: Data
    {
        "format_id": "ets_csv_v4",
        "display_name": "ETS-300/400 CSV (4行元数据)",
        "header_identifiers": ["PART_ID", "MODULE_ID", "SOFT_BIN", "BIN"],
        "min_header_matches": 2,
        "part_id_offset": 0,
        "soft_bin_offset": 0,
        "data_col_header_offset": 0,
        "unit_offset": 1,
        "lower_limit_offset": 2,
        "higher_limit_offset": 3,
        "data_start_offset": 4,
        "pre_test_columns": ["PART_ID", "SOFT_BIN"],
        "optional_pre_test_columns": ["SITE_NUM", "SITE"],
        "skip_row_values": {"PART_ID": ["1", "END"]},
        "stop_at_blank_row": True,
        "skip_blank_rows": True,
        "delimiter": ",",
        "encoding": "utf-8-sig",
        "column_map": {"MODULE_ID": "PART_ID", "BIN": "SOFT_BIN"},
        "min_confidence": 0.7,
    },

    # ── Epson FT CSV（无元数据） ──
    # 行0: Device, Site, Bin_No, Test_Item, Value
    # 行1+: Data
    {
        "format_id": "epson_csv",
        "display_name": "Epson FT CSV (无元数据)",
        "header_identifiers": ["Device", "Site", "Bin_No", "Test_"],
        "min_header_matches": 2,
        "part_id_offset": 0,
        "soft_bin_offset": 0,
        "data_col_header_offset": 0,
        "unit_offset": -1,
        "lower_limit_offset": -1,
        "higher_limit_offset": -1,
        "data_start_offset": 1,
        "pre_test_columns": ["Device", "Site", "Bin_No", "Test_Item"],
        "skip_row_values": {},
        "stop_at_blank_row": True,
        "skip_blank_rows": True,
        "delimiter": ",",
        "encoding": "utf-8-sig",
        "column_map": {"Device": "PART_ID", "Site": "SITE", "Bin_No": "SOFT_BIN"},
        "min_confidence": 0.6,
    },

    # ── ETS-300/400 旧版 CSV（6 行元数据，含 shift_limit） ──
    {
        "format_id": "ets_csv_v6",
        "display_name": "ETS-300/400 CSV (6行元数据)",
        "header_identifiers": ["PART_ID", "SOFT_BIN", "DC_"],
        "min_header_matches": 2,
        "part_id_offset": 0,
        "soft_bin_offset": 0,
        "data_col_header_offset": 0,
        "unit_offset": 1,
        "lower_limit_offset": 2,
        "higher_limit_offset": 3,
        "shift_limit_offset": 4,
        "limit_side_offset": 5,
        "data_start_offset": 6,
        "pre_test_columns": ["PART_ID", "SOFT_BIN"],
        "skip_row_values": {"PART_ID": ["1", "END"]},
        "stop_at_blank_row": True,
        "skip_blank_rows": True,
        "delimiter": ",",
        "encoding": "utf-8-sig",
        "column_map": {},
        "min_confidence": 0.6,
    },

    # ── 通用 CSV ──
    {
        "format_id": "generic_csv",
        "display_name": "通用 CSV",
        "header_identifiers": [],
        "min_header_matches": 0,
        "part_id_offset": 0,
        "soft_bin_offset": 0,
        "data_col_header_offset": 0,
        "unit_offset": -1,
        "lower_limit_offset": -1,
        "higher_limit_offset": -1,
        "data_start_offset": 1,
        "pre_test_columns": [],
        "skip_row_values": {},
        "stop_at_blank_row": True,
        "skip_blank_rows": True,
        "delimiter": ",",
        "encoding": "utf-8-sig",
        "column_map": {},
        "min_confidence": 0.3,
    },

    # ── 通用 TSV ──
    {
        "format_id": "generic_tsv",
        "display_name": "通用 TSV (制表符分隔)",
        "header_identifiers": [],
        "min_header_matches": 0,
        "part_id_offset": 0,
        "soft_bin_offset": 0,
        "data_col_header_offset": 0,
        "unit_offset": -1,
        "lower_limit_offset": -1,
        "higher_limit_offset": -1,
        "data_start_offset": 1,
        "pre_test_columns": [],
        "skip_row_values": {},
        "stop_at_blank_row": True,
        "skip_blank_rows": True,
        "delimiter": "\t",
        "encoding": "utf-8-sig",
        "column_map": {},
        "min_confidence": 0.3,
    },
]


# ═══════════════════════════════════════════════════════════════════
#  TOML 加载 / 签名合并
# ═══════════════════════════════════════════════════════════════════

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
SIGNATURES_TOML = CONFIG_DIR / "format_signatures.toml"


def _format_toml_value(val) -> str:
    """Format a Python value as a TOML literal."""
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, str):
        escaped = val.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, (list, tuple)):
        items = [_format_toml_value(v) for v in val]
        return "[" + ", ".join(items) + "]"
    if isinstance(val, dict):
        items = []
        for k, v in val.items():
            k_str = str(k) if isinstance(k, int) else k
            items.append(f'{k_str} = {_format_toml_value(v)}')
        return "{" + ", ".join(items) + "}"
    return str(val)


def _signature_to_toml(sig: dict) -> str:
    """Convert a signature dict to a [[signatures]] TOML block."""
    lines = ["[[signatures]]"]
    for key in ("format_id", "display_name",
                "header_identifiers", "min_header_matches",
                "part_id_offset", "soft_bin_offset", "data_col_header_offset",
                "unit_offset", "lower_limit_offset", "higher_limit_offset",
                "shift_limit_offset", "limit_side_offset",
                "data_start_offset",
                "pre_test_columns", "optional_pre_test_columns",
                "skip_row_values", "stop_at_blank_row", "skip_blank_rows",
                "delimiter", "encoding",
                "column_map", "min_confidence"):
        if key in sig:
            lines.append(f'{key} = {_format_toml_value(sig[key])}')
    return "\n".join(lines)


def _write_default_signatures():
    """Write built-in signatures to the TOML file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    content = "# 格式签名配置 — 编辑此文件可添加新的 CSV 格式支持\n"
    content += "# 每新增一种格式，追加一段 [[signatures]]\n"
    content += "# 字段说明见 core/format_detector.py\n"
    content += "# 修改后重启应用生效\n\n"
    for sig in BUILTIN_SIGNATURES:
        content += _signature_to_toml(sig) + "\n\n"
    SIGNATURES_TOML.write_text(content, encoding="utf-8")
    logger.info(f"已生成默认签名配置: {SIGNATURES_TOML}")


def _load_external_signatures() -> list[dict]:
    """Load format signatures from external config/format_signatures.toml."""
    if not SIGNATURES_TOML.exists():
        _write_default_signatures()
        return [dict(s) for s in BUILTIN_SIGNATURES]

    try:
        import tomllib
        with open(SIGNATURES_TOML, "rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        logger.warning(f"加载签名配置失败: {e}，使用内置签名。")
        return [dict(s) for s in BUILTIN_SIGNATURES]

    external = data.get("signatures", [])
    if not external:
        return [dict(s) for s in BUILTIN_SIGNATURES]

    # Normalize external sigs
    for ext_sig in external:
        _normalize_signature(ext_sig)

    # Merge: start with built-in, overlay external by format_id
    merged = {sig["format_id"]: dict(sig) for sig in BUILTIN_SIGNATURES}
    for ext_sig in external:
        fid = ext_sig.get("format_id")
        if fid:
            base = merged.get(fid, {})
            for k, v in ext_sig.items():
                base[k] = v
    return list(merged.values())


def _normalize_signature(sig: dict):
    """Normalize a signature dict (set defaults for new fields)."""
    sig.setdefault("header_identifiers", sig.get("keywords", []))
    sig.setdefault("min_header_matches", 2)
    sig.setdefault("part_id_offset", 0)
    sig.setdefault("soft_bin_offset", 0)
    sig.setdefault("data_col_header_offset", 0)
    sig.setdefault("unit_offset", 1)
    sig.setdefault("lower_limit_offset", -1)
    sig.setdefault("higher_limit_offset", -1)
    sig.setdefault("data_start_offset", 1)
    sig.setdefault("pre_test_columns", [])
    sig.setdefault("optional_pre_test_columns", [])
    sig.setdefault("skip_row_values", {})
    sig.setdefault("stop_at_blank_row", True)
    sig.setdefault("skip_blank_rows", True)
    sig.setdefault("min_confidence", 0.3)
    sig.setdefault("encoding", "utf-8-sig")
    sig.setdefault("column_map", {})


EQUIPMENT_SIGNATURES = _load_external_signatures()


# ═══════════════════════════════════════════════════════════════════
#  FormatDetector
# ═══════════════════════════════════════════════════════════════════


class FormatDetector:
    """Detect FT data file format by scanning for header row."""

    def detect(self, path: str | Path) -> FormatInfo:
        """检测文件格式。返回 FormatInfo。"""
        path = Path(path)
        if not path.exists():
            return FormatInfo(format_id="not_found", confidence=0)

        # Step 1: 检测编码
        raw = path.read_bytes()[:64]
        encoding = self._detect_encoding(raw)

        # Step 2: 读取全文
        try:
            text = path.read_text(encoding=encoding)
        except (UnicodeDecodeError, LookupError):
            text = path.read_text(encoding="latin-1")
            encoding = "latin-1"

        lines = text.splitlines()
        if not lines:
            return FormatInfo(format_id="empty", confidence=0)

        # Step 3: 检测分隔符
        delimiter = self._detect_delimiter(lines[:10])

        # Step 4: 全文 CSV 解析
        rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
        if not rows:
            return FormatInfo(format_id="empty", confidence=0)

        # Step 5: 对每个 signature 尝试匹配
        best_match = FormatInfo(
            format_id="unknown", encoding=encoding,
            delimiter=delimiter, header_rows=1,
            confidence=0,
        )

        for sig in EQUIPMENT_SIGNATURES:
            # 5a. 找表头行
            header_row_idx = self._find_header_row(rows, sig)
            if header_row_idx < 0:
                continue

            header_cols = rows[header_row_idx]
            header_upper = [c.strip().strip('\ufeff').upper() for c in header_cols]

            # 5b. 验证 pre_test_columns 按序存在
            test_col_start = self._verify_pre_test_columns(header_upper, sig)
            if test_col_start < 0:
                continue

            # 5c. 检查是否有测试项列（pre_test 之后的列）
            test_col_count = len(header_cols) - test_col_start
            score = self._calculate_score(
                sig, header_upper, rows, header_row_idx, delimiter,
                test_col_count,
            )
            if score == 0:
                continue

            if score <= best_match.confidence:
                continue

            # 5d. 算偏移位置
            part_id_row = header_row_idx + sig.get("part_id_offset", 0)
            soft_bin_row = header_row_idx + sig.get("soft_bin_offset", 0)
            data_col_hdr = header_row_idx + sig.get("data_col_header_offset", 0)
            unit_row = self._resolve_offset(rows, header_row_idx,
                                            sig.get("unit_offset", -1))
            lower_limit_row = self._resolve_offset(rows, header_row_idx,
                                                    sig.get("lower_limit_offset", -1))
            higher_limit_row = self._resolve_offset(rows, header_row_idx,
                                                     sig.get("higher_limit_offset", -1))

            # 找数据起始行
            data_start_row = self._find_data_start(rows, header_row_idx, sig)

            # 5e. 构建 meta_schema
            meta_schema = {}
            meta_schema[header_row_idx] = "header"
            if data_col_hdr != header_row_idx:
                meta_schema[data_col_hdr] = "data_col_header"
            if unit_row >= 0:
                meta_schema[unit_row] = "unit"
            if lower_limit_row >= 0:
                meta_schema[lower_limit_row] = "lower_limit"
            if higher_limit_row >= 0:
                meta_schema[higher_limit_row] = "higher_limit"
            shift_off = sig.get("shift_limit_offset")
            if shift_off is not None and shift_off >= 0:
                r = header_row_idx + shift_off
                if r < len(rows):
                    meta_schema[r] = "shift_limit"
            side_off = sig.get("limit_side_offset")
            if side_off is not None and side_off >= 0:
                r = header_row_idx + side_off
                if r < len(rows):
                    meta_schema[r] = "limit_side"

            best_match = FormatInfo(
                format_id=sig["format_id"],
                display_name=sig["display_name"],
                encoding=encoding,
                delimiter=delimiter,
                header_rows=data_start_row,
                column_map=dict(sig.get("column_map", {})),
                meta_schema=meta_schema,
                confidence=score,
                part_id_row=part_id_row,
                soft_bin_row=soft_bin_row,
                data_start_row=data_start_row,
                data_col_header_row=data_col_hdr,
                unit_row=unit_row,
                lower_limit_row=lower_limit_row,
                higher_limit_row=higher_limit_row,
                skip_row_values=dict(sig.get("skip_row_values", {})),
                stop_at_blank_row=sig.get("stop_at_blank_row", True),
            )

        # Step 6: 自动检测列名映射
        if best_match.confidence > 0 and best_match.data_start_row <= len(rows):
            hdr_idx = best_match.data_col_header_row
            if hdr_idx < len(rows):
                best_match.column_map.update(
                    self._auto_column_map(rows[hdr_idx]))

        return best_match

    # ── 表头行查找 ──

    def _find_header_row(self, rows: list[list[str]],
                         sig: dict) -> int:
        """在全文 rows 中找第一个符合 header_identifiers 的行。

        返回行号（0-indexed），找不到返回 -1。
        """
        identifiers = sig.get("header_identifiers", [])
        min_matches = sig.get("min_header_matches", 1)

        if not identifiers:
            # 无标识符（generic_csv/tsv），用第一行
            for i, row in enumerate(rows):
                if row and any(c.strip() for c in row):
                    return i
            return 0

        # 把 identifiers 转为大写版本（支持子串匹配，如 "DC_" 匹配 "DC_IGSS_1"）
        idents_upper = []
        for ident in identifiers:
            id_upper = ident.upper()
            if ident.endswith("_"):
                idents_upper.append(("endswith", id_upper.rstrip("_")))
            else:
                idents_upper.append(("exact", id_upper))

        for i, row in enumerate(rows):
            if not row or not any(c.strip() for c in row):
                continue
            upper_cols = set()
            for c in row:
                cleaned = c.strip().strip('\ufeff').upper()
                if cleaned:
                    upper_cols.add(cleaned)

            matches = 0
            for mode, val in idents_upper:
                if mode == "exact":
                    if val in upper_cols:
                        matches += 1
                elif mode == "endswith":
                    if any(c.startswith(val) for c in upper_cols):
                        matches += 1

            if matches >= min_matches:
                return i

        return -1

    # ── pre_test_columns 验证 ──

    def _verify_pre_test_columns(self, header_upper: list[str],
                                 sig: dict) -> int:
        """验证 pre_test_columns 按序存在于表头上。

        返回第一个测试列的索引（从 0 开始），
        如果任一必选列不存在则返回 -1。
        """
        pre_cols = sig.get("pre_test_columns", [])
        if not pre_cols:
            return 0

        opt_cols = {c.upper() for c in sig.get("optional_pre_test_columns", [])}
        last_idx = -1

        for pc in pre_cols:
            pc_upper = pc.upper()
            found_idx = -1
            for j in range(last_idx + 1, len(header_upper)):
                if header_upper[j] == pc_upper:
                    found_idx = j
                    break

            if found_idx < 0:
                # 可选列跳过
                if pc_upper in opt_cols:
                    continue
                return -1

            last_idx = found_idx

        return last_idx + 1

    # ── 数据起始行查找 ──

    def _find_data_start(self, rows: list[list[str]],
                         header_row_idx: int, sig: dict) -> int:
        """找数据起始行。"""
        offset = sig.get("data_start_offset", 1)
        data_start = header_row_idx + offset

        # 边界保护
        if data_start >= len(rows):
            data_start = len(rows)

        if sig.get("skip_blank_rows", True):
            while data_start < len(rows):
                row = rows[data_start]
                if not row or all(not c.strip() for c in row):
                    data_start += 1
                else:
                    break

        return data_start

    # ── 偏移量解析（保护越界） ──

    @staticmethod
    def _resolve_offset(rows: list[list[str]], header_row_idx: int,
                         offset: int) -> int:
        """解析相对偏移，越界返回 -1。"""
        if offset < 0:
            return -1
        r = header_row_idx + offset
        if r >= len(rows):
            return -1
        return r

    # ── 评分 ──

    def _calculate_score(self, sig: dict,
                         header_upper: list[str],
                         rows: list[list[str]],
                         header_row_idx: int,
                         delimiter: str,
                         test_col_count: int) -> float:
        """计算签名的匹配分数。"""
        score = 0.0

        # ① 检查是否有测试列
        if test_col_count <= 0:
            return 0.0

        # ② 分隔符检查：如果签名指定了分隔符，实际不匹配则拒签
        sig_delim = sig.get("delimiter", "")
        if sig_delim:
            if sig_delim != delimiter:
                # 签名指定了特定分隔符但不匹配 → 不匹配此签名
                return 0.0
            score += 0.3

        # ③ 确认有数据行
        data_start = self._find_data_start(rows, header_row_idx, sig)
        if data_start < len(rows):
            data_rows = rows[data_start:]
            real_data = [r for r in data_rows
                         if r and any(self._is_number(c) for c in r)]
            if len(real_data) >= 1:
                score += 0.3

        # ④ header_identifiers 命中加分
        identifiers = sig.get("header_identifiers", [])
        hits = 0
        idents_upper = set(i.upper() for i in identifiers)
        header_set = set(header_upper)
        for ident in idents_upper:
            if ident.rstrip("_") in header_set or ident in header_set:
                hits += 1
        score += min(hits * 0.15, 0.4)

        return min(score, 1.0)

    # ── 编码检测 ──

    @staticmethod
    def _detect_encoding(raw: bytes) -> str:
        if raw.startswith(b'\xef\xbb\xbf'):
            return "utf-8-sig"
        if raw.startswith(b'\xff\xfe'):
            return "utf-16-le"
        if raw.startswith(b'\xfe\xff'):
            return "utf-16-be"
        return "utf-8-sig"

    # ── 分隔符检测 ──

    @staticmethod
    def _detect_delimiter(lines: list[str]) -> str:
        candidate_lines = [
            l for l in lines if l.strip()
            and any(d in l for d in [",", "\t", ";"])
        ]
        if not candidate_lines:
            candidate_lines = [l for l in lines if l.strip()]
        if not candidate_lines:
            return ","

        comma_counts = [l.count(",") for l in candidate_lines]
        tab_counts = [l.count("\t") for l in candidate_lines]
        semicolon_counts = [l.count(";") for l in candidate_lines]

        if tab_counts and (not comma_counts or max(tab_counts) > max(comma_counts)):
            return "\t"
        if semicolon_counts and max(semicolon_counts) > max(comma_counts):
            return ";"
        return ","

    # ── 辅助 ──

    @staticmethod
    def _is_number(s: str) -> bool:
        try:
            float(s.strip())
            return True
        except (ValueError, TypeError):
            return False

    def _auto_column_map(self, header_row: list[str]) -> dict[str, str]:
        mapping = {}
        known_patterns = {
            "PART_ID": ["MODULE_ID", "MODULE", "DEVICE", "DIE_ID", "SN", "LOT"],
            "SOFT_BIN": ["BIN", "BIN_NO", "BIN_NUMBER", "RESULT", "HARD_BIN"],
            "GROUP": ["GROUP", "TEST_CONDITION", "CONDITION"],
        }
        for col in header_row:
            col_upper = col.strip().upper()
            for standard, aliases in known_patterns.items():
                if col_upper == standard:
                    continue
                if col_upper in aliases:
                    mapping[col] = standard
                    break
        return mapping


# Convenience function
def detect_format(path: str | Path) -> FormatInfo:
    return FormatDetector().detect(path)
