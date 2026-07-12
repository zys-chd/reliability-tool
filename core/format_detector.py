"""
File format detector for semiconductor FT data.
Detects file type, metadata rows, encoding, delimiter, and column mapping.

文件格式约定（标准 4 行元数据格式）：
  行 1: 列名/表头           → PART_ID, SOFT_BIN, DC_IGSS_1, ...
  行 2: 单位 (unit)         → V, uA, ...
  行 3: 下限 (lower_limit)  → 0, 0.5, ...
  行 4: 上限 (higher_limit) → 3.3, 100, ...
  行 5+: 数据

检测流程：
  1. 读前 64 字节判定编码（BOM / UTF-8 / UTF-16）
  2. 读前 10 行统计分隔符（逗号/制表符/分号）
  3. 逐行分析：第 1 行列名 → 匹配签名关键词 → 判定设备类型
  4. 统计前导非数值行数量 → 确定实际 metadata 行数
  5. 按签名评分（关键词 + 分隔符 + 行数 + 有数据行）
  6. 自动检测列名映射（MODULE_ID → PART_ID 等）
"""

import csv
import io
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class FormatInfo:
    """Detected file format information.

    核心属性：
      format_id      唯一格式标识符，如 "ets_csv_v4"
      display_name   中文显示名，如 "ETS-300/400 CSV (4行元数据)"
      encoding       文件编码（自动检测）
      delimiter      CSV 分隔符（自动检测）
      header_rows    元数据行数（第 1 行算表头还是元数据？详见 description）
      column_map     列名映射 {原始列名: 标准列名}
      confidence     匹配置信度 0-1
      meta_schema    元数据行 schema 定义（哪行是 unit / lower / higher 等）
    """
    format_id: str = "unknown"
    display_name: str = "未知格式"
    encoding: str = "utf-8-sig"
    delimiter: str = ","
    header_rows: int = 4
    column_map: dict[str, str] = field(default_factory=dict)
    confidence: float = 0.0

    # ── 新增：元数据行 schema ──
    # 描述每一行元数据的含义。
    # 格式: {行号(0-indexed): 元数据类型}
    # 行号 0 = 第 1 行（通常是列名/表头）
    # 常见元数据类型：
    #   "header"       — 列名/表头（必须）
    #   "unit"         — 单位
    #   "lower_limit"  — 下限
    #   "higher_limit" — 上限
    #   "shift_limit"  — shift 极限
    #   "limit_side"   — limit 方向
    #   "shift_formula" — shift 公式
    #   "comment"      — 注释（需要保留但不用解析）
    #   "custom"       — 其他自定义元数据（原样保留）
    #   "blank"        — 空行
    meta_schema: dict[int, str] = field(default_factory=lambda: {
        0: "header",
        1: "unit",
        2: "lower_limit",
        3: "higher_limit",
    })

    # ── 新增：行位置跟踪 ──
    part_id_row: int = 0       # which row PART_ID is on (0 = same as header)
    soft_bin_row: int = 0      # which row SOFT_BIN is on (0 = same as header)
    data_start_row: int = -1   # which row data starts at (-1 = auto = header_rows)
    unit_row: int = -1          # which row unit info is on (-1 = not found)
    lower_limit_row: int = -1   # which row lower limit is on
    higher_limit_row: int = -1  # which row higher limit is on

    # NOTE: header_rows 的含义：
    #   - header_rows = 4：前 4 行全是元数据，第 5 行起是数据
    #   - header_rows = 1：前 1 行是列名，第 2 行起是数据


# ═══════════════════════════════════════════════════════════════════
#  设备签名表（内置默认值）
# ═══════════════════════════════════════════════════════════════════
# 添加新格式时在此列表尾部追加条目。
# 字段说明见上方的 EQUIPMENT_SIGNATURES。
#
# 检测原理（关键词匹配）：
#   系统读前 10 行后，提取第 1 行的列名（大写）与 keywords 逐项对比。
#   keywords 是预期在表头中出现的列名片段。
#   匹配命中越多 → 置信度越高。
#
# 列名自动映射：
#   系统检测到 MODULE_ID → 自动映射为 PART_ID
#   系统检测到 BIN       → 自动映射为 SOFT_BIN
#   其它列名原样保留作为测试项名称。
# ═══════════════════════════════════════════════════════════════════

BUILTIN_SIGNATURES = [
    # ── ETS-300/400 标准 CSV（4 行元数据） ──
    # 典型列名: PART_ID, SOFT_BIN, DC_IGSS_1, DC_BV_1, ...
    # 元数据: 行1=表头, 行2=单位, 行3=下限, 行4=上限, 行5+=数据
    # PART_ID 可能叫 MODULE_ID（ETS 旧版本）
    # SOFT_BIN 可能叫 BIN
    {
        "format_id": "ets_csv_v4",
        "display_name": "ETS-300/400 CSV (4行元数据)",
        "keywords": ["PART_ID", "MODULE_ID", "SOFT_BIN", "BIN"],
        "header_rows": 4,
        "delimiter": ",",
        "encoding": "utf-8-sig",
        "column_map": {"MODULE_ID": "PART_ID", "BIN": "SOFT_BIN"},
        "meta_schema": {0: "header", 1: "unit", 2: "lower_limit", 3: "higher_limit"},
        "min_confidence": 0.7,
    },

    # ── Epson FT CSV（无元数据） ──
    # 典型列名: Device, Site, Bin_No, Test_Item, Value
    # 元数据: 只有 1 行表头，无 unit/lower/higher 行
    # PART_ID → Device, SOFT_BIN → Bin_No
    {
        "format_id": "epson_csv",
        "display_name": "Epson FT CSV (无元数据)",
        "keywords": ["Device", "Site", "Bin_No", "Test_"],
        "header_rows": 1,
        "delimiter": ",",
        "encoding": "utf-8-sig",
        "column_map": {"Device": "PART_ID", "Site": "SITE", "Bin_No": "SOFT_BIN"},
        "meta_schema": {0: "header"},
        "min_confidence": 0.6,
    },

    # ── ETS-300/400 旧版 CSV（6 行元数据，含 shift_limit） ──
    # 典型列名: PART_ID, SOFT_BIN, DC_IGSS_1, ...
    # 元数据: 行1=表头, 行2=单位, 行3=下限, 行4=上限,
    #         行5=shift_limit, 行6=limit_side, 行7+=数据
    {
        "format_id": "ets_csv_v6",
        "display_name": "ETS-300/400 CSV (6行元数据)",
        "keywords": ["PART_ID", "SOFT_BIN", "DC_"],
        "header_rows": 6,
        "delimiter": ",",
        "encoding": "utf-8-sig",
        "column_map": {},
        "meta_schema": {
            0: "header", 1: "unit", 2: "lower_limit",
            3: "higher_limit", 4: "shift_limit", 5: "limit_side",
        },
        "min_confidence": 0.6,
    },

    # ── 通用 CSV ──
    # 无特定设备格式，只有 1 行表头
    {
        "format_id": "generic_csv",
        "display_name": "通用 CSV",
        "keywords": [],
        "header_rows": 1,
        "delimiter": ",",
        "encoding": "utf-8-sig",
        "column_map": {},
        "meta_schema": {0: "header"},
        "min_confidence": 0.3,
    },

    # ── 通用 TSV ──
    {
        "format_id": "generic_tsv",
        "display_name": "通用 TSV (制表符分隔)",
        "keywords": [],
        "header_rows": 1,
        "delimiter": "\t",
        "encoding": "utf-8-sig",
        "column_map": {},
        "meta_schema": {0: "header"},
        "min_confidence": 0.3,
    },
]

# ── 加载外部签名（合并到 EQUIPMENT_SIGNATURES） ──

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
            items.append(f'{k} = {_format_toml_value(v)}')
        return "{" + ", ".join(items) + "}"
    return str(val)


def _signature_to_toml(sig: dict) -> str:
    """Convert a signature dict to a [[signatures]] TOML block."""
    lines = ["[[signatures]]"]
    for key in ("format_id", "display_name", "keywords", "header_rows",
                "part_id_row", "soft_bin_row", "data_start_row",
                "delimiter", "encoding",
                "column_map", "meta_schema", "min_confidence"):
        if key in sig:
            lines.append(f'{key} = {_format_toml_value(sig[key])}')
    return "\n".join(lines)


def _write_default_signatures():
    """Write built-in signatures to the TOML file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    content = "# 格式签名配置 — 编辑此文件可添加新的 CSV 格式支持\n"
    content += "# 每新增一种格式，追加一段 [[signatures]]\n"
    content += "# 修改后重启应用生效\n\n"
    for sig in BUILTIN_SIGNATURES:
        content += _signature_to_toml(sig) + "\n\n"
    SIGNATURES_TOML.write_text(content, encoding="utf-8")
    logger.info(f"已生成默认签名配置: {SIGNATURES_TOML}")


def _load_external_signatures() -> list[dict]:
    """Load format signatures from external config/format_signatures.toml.
    
    If the file doesn't exist, creates it with built-in defaults.
    Falls back to built-in signatures if file is malformed.
    External signatures override built-in ones by format_id.
    """
    if not SIGNATURES_TOML.exists():
        _write_default_signatures()
        return list(BUILTIN_SIGNATURES)

    try:
        import tomllib
        with open(SIGNATURES_TOML, "rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        logger.warning(f"Failed to load {SIGNATURES_TOML}: {e}. Using built-in signatures.")
        return list(BUILTIN_SIGNATURES)

    external = data.get("signatures", [])
    if not external:
        return list(BUILTIN_SIGNATURES)

    # Normalize: convert string numeric meta_schema keys to int
    for ext_sig in external:
        ms = ext_sig.get("meta_schema", {})
        if ms and any(isinstance(k, str) and k.isdigit() for k in ms):
            ext_sig["meta_schema"] = {int(k): v for k, v in ms.items()}

        # Set defaults for new fields
        ext_sig.setdefault("part_id_row", 0)
        ext_sig.setdefault("soft_bin_row", 0)
        ext_sig.setdefault("data_start_row", -1)

    # Merge: start with built-in, then overlay external by format_id
    merged = {sig["format_id"]: dict(sig) for sig in BUILTIN_SIGNATURES}
    for ext_sig in external:
        fid = ext_sig.get("format_id")
        if fid:
            merged[fid] = dict(ext_sig)
    return list(merged.values())


# EQUIPMENT_SIGNATURES — the merged list used by FormatDetector
EQUIPMENT_SIGNATURES = _load_external_signatures()


class FormatDetector:
    """Detect FT data file format by examining headers and content.

    用法：
        detector = FormatDetector()
        info = detector.detect("data/T0/sample.csv")
        print(info.format_id, info.confidence)
        # → "ets_csv_v4", 0.95
    """

    # ── 识别列名关键词，用于定位表头行 ──
    HEADER_KEYWORDS = {
        "PART_ID", "MODULE_ID", "SOFT_BIN", "BIN", "BIN_NO",
        "DEVICE", "SITE", "GROUP", "LOT", "DIE_ID", "SN",
        "TEST_", "TEST_ITEM", "CONDITION", "FILE",
    }

    def detect(self, path: str | Path) -> FormatInfo:
        """检测文件格式。返回 FormatInfo。"""
        path = Path(path)
        if not path.exists():
            return FormatInfo(format_id="not_found", confidence=0)

        # Step 1: 读前 64 字节检测编码
        raw = path.read_bytes()[:64]
        encoding = self._detect_encoding(raw)

        # Step 2: 读前 20 行分析结构
        try:
            text = path.read_text(encoding=encoding)
        except (UnicodeDecodeError, LookupError):
            text = path.read_text(encoding="latin-1")
            encoding = "latin-1"

        lines = text.splitlines()
        if not lines:
            return FormatInfo(format_id="empty", confidence=0)

        # Step 3: 检测分隔符（过滤无分隔符的元数据行）
        delimiter = self._detect_delimiter(lines[:10])

        # Step 4: 解析 CSV 样本（前 20 行，给空白/不规则行更多空间）
        sample_lines = min(len(lines), 20)
        reader = csv.reader(io.StringIO("\n".join(lines[:sample_lines])), delimiter=delimiter)
        rows = list(reader)
        if not rows:
            return FormatInfo(format_id="empty", confidence=0)

        # Step 5: 查找实际表头行
        header_row_idx = self._find_header_row(rows, delimiter)

        # Step 6: 构建 meta_schema（分析表头前的行）
        meta_schema = self._build_meta_schema(rows, header_row_idx)

        # Step 7: 统计实际元数据行数（从 row 0 到第一个数据行）
        actual_header_rows = self._count_header_rows(rows)

        # Step 8: 提取表行列名
        header = [c.strip().upper() for c in rows[header_row_idx]]

        # Step 9: 匹配设备签名
        best_match = FormatInfo(
            format_id="unknown", encoding=encoding,
            delimiter=delimiter, header_rows=actual_header_rows,
            confidence=0,
        )

        for sig in EQUIPMENT_SIGNATURES:
            score = self._score_signature(header, rows, sig, delimiter,
                                          actual_header_rows)
            if score > best_match.confidence:
                # 合并签名信息到结果
                sig_meta = dict(sig.get("meta_schema", {0: "header"}))

                # 如果实际 schema 比签名多，补充自定义行
                max_schema_idx = max(
                    max(meta_schema.keys()) if meta_schema else 0,
                    max(sig_meta.keys()) if sig_meta else 0,
                )
                effective_schema = dict(sig_meta)
                for r in range(header_row_idx):
                    if r not in effective_schema and r in meta_schema:
                        effective_schema[r] = meta_schema[r]

                best_match = FormatInfo(
                    format_id=sig["format_id"],
                    display_name=sig["display_name"],
                    encoding=encoding,
                    delimiter=delimiter,
                    header_rows=actual_header_rows,
                    column_map=dict(sig["column_map"]),
                    meta_schema=effective_schema,
                    confidence=score,
                )

                # Set row-position fields from matched signature
                best_match.part_id_row = sig.get("part_id_row", 0)
                best_match.soft_bin_row = sig.get("soft_bin_row", 0)
                best_match.data_start_row = sig.get("data_start_row", -1)
                if best_match.data_start_row < 0:
                    best_match.data_start_row = best_match.header_rows

        # Step 10: 自动检测列名映射
        if best_match.confidence > 0:
            best_match.column_map.update(self._auto_column_map(rows[header_row_idx]))

        # Step 11: 填充行位置跟踪字段
        # Scan rows around the header to find unit/lower/higher metadata rows
        for row_idx in range(len(rows)):
            if row_idx >= len(rows):
                continue
            row = rows[row_idx]
            if not row or not any(c.strip() for c in row):
                continue
            first_col = row[0].strip().lower() if row else ""
            
            if first_col in ("unit", "units"):
                best_match.unit_row = row_idx
            elif first_col in ("lower", "lower limit", "lower_limit"):
                best_match.lower_limit_row = row_idx
            elif first_col in ("higher", "higher limit", "higher_limit",
                               "upper", "upper limit", "upper_limit"):
                best_match.higher_limit_row = row_idx

        # Detect PART_ID/SOFT_BIN rows: if not in header row, search earlier rows
        if header_row_idx < len(rows):
            header_cols = [c.strip().upper() for c in rows[header_row_idx]]
            for ci, col in enumerate(header_cols):
                mapped = best_match.column_map.get(rows[header_row_idx][ci].strip(), col)
                if mapped == "PART_ID":
                    best_match.part_id_row = header_row_idx
                elif mapped == "SOFT_BIN":
                    best_match.soft_bin_row = header_row_idx

        return best_match

    # ── 表头行查找 ──

    def _find_header_row(self, rows: list[list[str]], delimiter: str) -> int:
        """Find the row index that is the actual column header.

        Scans all rows looking for:
        1. Rows containing recognizable keywords (PART_ID, MODULE_ID, etc.)
        2. The row with the most test-item-like columns (using test_item_patterns)
        3. The row with the most non-empty cells (most likely the header)
        4. The last non-numeric row before data starts

        Returns: row index (0-based), or 0 if not found.
        """
        if not rows:
            return 0

        best_idx = 0
        max_cols = 0

        for i, row in enumerate(rows):
            # Remove empty trailing cells from ragged CSV rows
            clean_row = [c for c in row if c.strip()]

            if not clean_row:
                continue

            # Strategy 1: Check for recognizable keywords
            upper_cols = {c.strip().upper() for c in clean_row}
            matched_keywords = upper_cols & self.HEADER_KEYWORDS
            if len(matched_keywords) >= 2:
                return i  # Strong match with 2+ keywords

            # Track the row with the most non-empty columns
            if len(clean_row) > max_cols:
                max_cols = len(clean_row)
                best_idx = i

        # Strategy 2: Use test_item_patterns to find rows with most test-item columns
        from core.test_item_patterns import find_test_item_header_row
        tip_idx = find_test_item_header_row(rows)
        if tip_idx != best_idx and tip_idx > 0:
            return tip_idx

        # Strategy 3: Return the row with the most columns
        return best_idx

    # ── 元数据行 schema 构建 ──

    def _build_meta_schema(self, rows: list[list[str]],
                           header_row_idx: int) -> dict[int, str]:
        """Build a meta_schema by analyzing rows before the header.

        Examines each row between index 0 and header_row_idx:
        - Empty rows → "blank"
        - Rows with same column count as header → try to detect
          (unit: mostly non-numeric, limits: mostly numeric)
        - Other rows → "custom"
        """
        schema: dict[int, str] = {}

        if header_row_idx <= 0:
            return schema

        header_col_count = len(rows[header_row_idx]) if header_row_idx < len(rows) else 0

        for i in range(header_row_idx):
            if i >= len(rows):
                schema[i] = "custom"
                continue

            row = rows[i]
            clean_cells = [c for c in row if c.strip()]

            if not clean_cells:
                schema[i] = "blank"
                continue

            if len(row) == header_col_count and header_col_count > 0:
                # Same column count as header — try to detect type
                first_col = row[0].strip().lower() if row else ""
                
                # Check for known metadata labels in first column
                if first_col in self._META_LABELS:
                    if first_col in ("unit", "units"):
                        schema[i] = "unit"
                    elif first_col in ("lower", "lower limit", "lower_limit"):
                        schema[i] = "lower_limit"
                    elif first_col in ("higher", "higher limit", "higher_limit",
                                       "upper", "upper limit", "upper_limit"):
                        schema[i] = "higher_limit"
                    elif first_col in ("shift", "shift limit", "shift_limit"):
                        schema[i] = "shift_limit"
                    elif first_col in ("limit side", "limit_side"):
                        schema[i] = "limit_side"
                    elif first_col in ("formula", "shift formula", "shift_formula"):
                        schema[i] = "shift_formula"
                    else:
                        schema[i] = "custom"
                    continue
                
                # Check if most values are numbers (likely limits)
                numeric_count = sum(1 for c in row if self._is_number(c.strip()))
                if numeric_count >= len(row) * 0.5:
                    # Could be lower/higher limit
                    schema[i] = "limit"
                else:
                    # Could be unit row
                    schema[i] = "unit"
            else:
                schema[i] = "custom"

        return schema

    # ── 编码检测 ──

    def _detect_encoding(self, raw: bytes) -> str:
        """根据 BOM 检测文件编码。"""
        if raw.startswith(b'\xef\xbb\xbf'):
            return "utf-8-sig"           # UTF-8 with BOM（Windows 最常见）
        if raw.startswith(b'\xff\xfe'):
            return "utf-16-le"            # UTF-16 LE
        if raw.startswith(b'\xfe\xff'):
            return "utf-16-be"            # UTF-16 BE
        return "utf-8-sig"                # 默认 UTF-8（兼容 BOM）

    # ── 分隔符检测 ──

    def _detect_delimiter(self, lines: list[str]) -> str:
        """自动检测 CSV 分隔符。

        策略：统计前 10 行中逗号、制表符、分号的出现次数，
        过滤掉不含任何分隔符的行（元数据行）。
        选择出现次数最多且一致的那个。
        """
        # Filter out lines that don't have any candidate delimiters
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

        if not comma_counts and not tab_counts:
            return ","  # 无法检测，默认逗号

        # 制表符优先
        if tab_counts and (not comma_counts or max(tab_counts) > max(comma_counts)):
            return "\t"
        # 分号次之（欧洲 CSV 常用）
        if semicolon_counts and max(semicolon_counts) > max(comma_counts):
            return ";"
        return ","

    # ── 元数据行数检测 ──

    # Known label words that appear in the first column of metadata rows
    _META_LABELS = frozenset({
        "unit", "units", "lower", "lower limit", "lower_limit",
        "higher", "higher limit", "higher_limit",
        "upper", "upper limit", "upper_limit",
        "limit", "shift", "shift limit", "shift_limit",
        "limit side", "limit_side", "formula", "shift formula",
        "shift_formula", "comment", "备注", "注释",
    })

    def _count_header_rows(self, rows: list[list[str]]) -> int:
        """统计前导元数据行的数量（从 row 0 到第一个数据行）。

        使用 _find_header_row 定位实际表头，然后计算从 row 0
        到表头后第一个数据行之间的所有行。

        策略：从表头下一行开始扫描，遇到以下情况才认为是数据行：
        1. 首列不是已知的元数据标签（"Unit", "Lower Limit" 等）
        2. 并且数据列中包含数值

        返回值：实际元数据行数（至少 1）
        """
        if not rows:
            return 1

        # 找到表头行
        header_idx = self._find_header_row(rows, ",")

        # 从表头行之后找到第一个数据行
        data_start = len(rows)  # default: all rows are header/metadata
        for i in range(header_idx + 1, len(rows)):
            row = rows[i]
            if not row or all(not c.strip() for c in row):
                continue

            first_col = row[0].strip().lower() if row else ""

            # 如果首列是已知的元数据标签，跳过
            if first_col in self._META_LABELS:
                continue

            # 取数据列检查（跳过 PART_ID, SOFT_BIN 等非数值列）
            data_cols = row[2:] if len(row) > 2 else row[1:] if len(row) > 1 else []
            if data_cols and any(self._is_number(c) for c in data_cols):
                data_start = i
                break

        return max(data_start, 1)

    # ── 签名评分 ──

    def _score_signature(self, header: list[str], rows: list[list[str]],
                         sig: dict, detected_delim: str = ",",
                         actual_header_rows: int = 1) -> float:
        """计算文件与签名的匹配分数（0.0 ~ 1.0）。

        评分项：
        - 关键词命中（每命中 +0.2）：表头列名精确匹配签名的 keywords
        - 分隔符匹配（+0.3）：签名声明的分隔符与实际检测一致
        - 元数据行数匹配（+0.2）：签名声明的 header_rows 与实际一致
        - 有数据行（+0.2）：表头后至少有一行数值数据
        """
        score = 0.0

        # ① 关键词匹配（精确匹配列名，不是子串）
        for kw in sig.get("keywords", []):
            kw_upper = kw.upper()
            if any(kw_upper == c for c in header):
                score += 0.2

        # ② 分隔符匹配
        sig_delim = sig.get("delimiter", "")
        if sig_delim and sig_delim == detected_delim:
            score += 0.3

        # ③ 元数据行数匹配
        if actual_header_rows == sig.get("header_rows", 1):
            score += 0.2

        # ④ 确认有数据行
        if len(rows) > actual_header_rows:
            data_rows = [r for r in rows[actual_header_rows:]
                         if r and any(self._is_number(c) for c in r)]
            if len(data_rows) >= 1:
                score += 0.2

        return min(score, 1.0)

    # ── 辅助 ──

    @staticmethod
    def _is_number(s: str) -> bool:
        """判断字符串是否可转为数值。"""
        try:
            float(s.strip())
            return True
        except (ValueError, TypeError):
            return False

    def _auto_column_map(self, header_row: list[str]) -> dict[str, str]:
        """自动检测常见列名到标准列名的映射。

        当前支持的映射：
          MODULE_ID / MODULE / DEVICE / DIE_ID / SN / LOT → PART_ID
          BIN / BIN_NO / BIN_NUMBER / RESULT / HARD_BIN  → SOFT_BIN
          GROUP / TEST_CONDITION / CONDITION              → GROUP
        """
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
                    continue  # 已经是标准列名
                if col_upper in aliases:
                    mapping[col] = standard
                    break
        return mapping


# Convenience function
def detect_format(path: str | Path) -> FormatInfo:
    """快速检测文件格式。"""
    return FormatDetector().detect(path)
