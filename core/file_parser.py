"""
文件解析器接口。

实际文件格式千差万别，你实现这个接口后通过 register_parser 注册，
核心逻辑自动调用。

支持自动格式检测 (FormatDetector) 和列名映射 (ColumnMapper)。
"""

from typing import Protocol, Optional, TYPE_CHECKING
from pathlib import Path
import pandas as pd

if TYPE_CHECKING:
    from .format_detector import FormatInfo


class FileParser(Protocol):
    """文件解析器协议。实现此协议后可注册到解析器管理器。"""

    def read(self, path: str) -> pd.DataFrame:
        """读取文件，返回统一格式的 DataFrame。

        返回的 DataFrame 必须包含以下列：
        - PART_ID : str       — 产品/模组标识
        - SOFT_BIN : int/str  — 1 为 PASS，其余为 FAIL
        - 其余列  : float    — 各测试项，列名格式 "{type}_{name}_{die}"

        文件前 4 行为元信息行（表头/单位/下限/上限），第 5 行起为数据。
        read() 应跳过前 4 行。
        """
        ...

    @property
    def supported_extensions(self) -> list[str]:
        """返回支持的文件扩展名列表，如 ['.csv', '.xlsx']"""
        ...


class ParserManager:
    """解析器管理器，按扩展名自动选择解析器。"""

    def __init__(self, default_parser: Optional[FileParser] = None):
        self._parsers: dict[str, FileParser] = {}
        if default_parser is not None:
            self.register(default_parser)

    def register(self, parser: FileParser):
        """注册解析器"""
        for ext in parser.supported_extensions:
            self._parsers[ext.lower()] = parser

    def read(self, path: str) -> pd.DataFrame:
        """按扩展名选择解析器并读取"""
        import os
        ext = os.path.splitext(path)[1].lower()
        parser = self._parsers.get(ext)
        if parser is None:
            raise ValueError(f"不支持的格式: {ext}，已注册: {list(self._parsers.keys())}")
        return parser.read(path)

    def detect_and_read(self, path: str) -> pd.DataFrame:
        """Auto-detect format, read, and map columns.

        Uses FormatDetector to analyze file structure and ColumnMapper
        to normalize column names. Passes FormatInfo to parser for
        unit conversion support.
        """
        from .format_detector import detect_format
        from .column_mapper import ColumnMapper

        fmt = detect_format(path)
        parser = self.get_parser(path, fmt)
        df = parser.read(path, fmt_info=fmt)

        mapper = ColumnMapper(fmt.column_map)
        col_map = mapper.auto_detect(list(df.columns))
        df = mapper.apply(df, col_map)
        return df

    def get_parser(self, path: str, fmt=None) -> FileParser:
        """Get the best parser for a given file path and format info.

        Uses format info to configure parser (skiprows, delimiter, encoding).
        Falls back to extension-based matching, then to a generic CSV parser.
        """
        ext = Path(path).suffix.lower()

        # Use format info to build a properly configured parser
        encoding = fmt.encoding if fmt else "utf-8-sig"
        delimiter = fmt.delimiter if fmt else ","

        # Calculate skiprows based on header_rows
        # Row 0 is always the header, skip rows 1..header_rows-1 (metadata rows)
        if fmt and fmt.header_rows > 1:
            skiprows = list(range(1, fmt.header_rows))
        elif fmt and fmt.header_rows == 1:
            skiprows = []  # no metadata rows to skip
        else:
            skiprows = [1, 2, 3]  # default for 4-row format

        # Match by extension
        for ext_key, parser in self._parsers.items():
            if ext == ext_key:
                # If we have format info, create a properly configured instance
                if isinstance(parser, DefaultCSVParser):
                    return DefaultCSVParser(
                        encoding=encoding,
                        delimiter=delimiter,
                        skiprows=skiprows,
                    )
                # For Excel parsers, apply skiprows if configurable
                if isinstance(parser, DefaultExcelParser) and hasattr(parser, 'skiprows'):
                    return DefaultExcelParser(skiprows=skiprows)
                return parser

        # Ultimate fallback: return CSV parser with format settings
        return DefaultCSVParser(
            encoding=encoding,
            delimiter=delimiter,
            skiprows=skiprows,
        )

    def list_parsers(self) -> list[dict]:
        """List all registered parsers with their info."""
        result = []
        for p in self._parsers.values():
            info = {
                "extensions": p.supported_extensions,
            }
            if hasattr(p, 'format_id'):
                info["format_id"] = p.format_id
            if hasattr(p, 'display_name'):
                info["display_name"] = p.display_name
            result.append(info)
        # Deduplicate by format_id
        seen = set()
        unique = []
        for info in result:
            fid = info.get("format_id", str(info["extensions"]))
            if fid not in seen:
                seen.add(fid)
                unique.append(info)
        return unique


# ── 默认的通用 CSV 解析器（跳过前 4 行元信息） ──

class DefaultCSVParser:
    """默认 CSV 解析器：跳过前 4 个元信息行，第 5 行起为数据

    支持自定义 encoding、delimiter 和 skiprows，适用于各种 CSV 格式。
    支持合并不同行列名 (part_id_row != header_row)。
    """

    def __init__(self, encoding: str = "utf-8-sig",
                 skiprows: list[int] | None = None,
                 delimiter: str = ",",
                 part_id_row: int = 0,
                 soft_bin_row: int = 0,
                 data_start_row: int = -1,
                 data_col_header_row: int = 0,
                 skip_row_values: dict | None = None,
                 stop_at_blank_row: bool = True):
        self.encoding = encoding
        self.skiprows = skiprows if skiprows is not None else [1, 2, 3]
        self.delimiter = delimiter
        self.part_id_row = part_id_row
        self.soft_bin_row = soft_bin_row
        self.data_start_row = data_start_row
        self.data_col_header_row = data_col_header_row
        self.skip_row_values = skip_row_values or {}
        self.stop_at_blank_row = stop_at_blank_row

    @property
    def supported_extensions(self) -> list[str]:
        return ['.csv', '.txt', '.dat']

    def _find_data_header_row(self, path: str) -> int:
        """Scan meta rows to find the row with test item column names.

        Used when part_id_row=0 but the actual data column headers
        are on a different row (split header format).
        Looks for the row with the most non-empty cells among rows [1, data_start_row).
        Returns: row index (0-based), or 0 if not found.
        """
        try:
            with open(path, 'r', encoding=self.encoding) as f:
                raw_lines = f.readlines()
            import csv, io
            from core.test_item_patterns import count_test_item_columns
            meta_text = ''.join(raw_lines[:self.data_start_row])
            reader = csv.reader(io.StringIO(meta_text), delimiter=self.delimiter)
            meta_rows = list(reader)
            best_idx, best_count = 0, 0
            for i in range(1, min(len(meta_rows), self.data_start_row)):
                row = meta_rows[i]
                cnt = count_test_item_columns(row)
                if cnt > best_count:
                    best_count, best_idx = cnt, i
            return best_idx if best_count > 0 else 0
        except Exception:
            return 0

    def read(self, path: str, fmt_info: 'FormatInfo | None' = None) -> pd.DataFrame:
        import pandas as pd

        # Use FormatInfo if provided
        if fmt_info is not None:
            self.part_id_row = fmt_info.part_id_row
            self.soft_bin_row = fmt_info.soft_bin_row
            self.data_start_row = fmt_info.data_start_row
            self.data_col_header_row = getattr(fmt_info, 'data_col_header_row', 0)
            self.skip_row_values = getattr(fmt_info, 'skip_row_values', {})
            self.stop_at_blank_row = getattr(fmt_info, 'stop_at_blank_row', True)
            # Recalculate skiprows based on data_start_row
            # data_start_row is the index of the FIRST DATA row;
            # skip rows 1..data_start_row-1 to preserve row 0 (header)
            if self.data_start_row > 1:
                self.skiprows = list(range(1, self.data_start_row))

        # Check if we need header merging (part_id_row differs from main header row)
        # Detect split headers via meta_schema or explicit row differences
        needs_merge = False
        main_header_row = 0

        if fmt_info is not None and hasattr(fmt_info, 'meta_schema'):
            for row_idx, schema_type in fmt_info.meta_schema.items():
                if schema_type == "header":
                    main_header_row = row_idx
                elif schema_type == "part_id_header":
                    needs_merge = True

        # Also detect if part_id_row is 0 but data_start_row > 1 (likely split header)
        if not needs_merge and self.data_start_row > 1:
            found = self._find_data_header_row(path)
            if found > 0:
                main_header_row = found
                needs_merge = True

        if needs_merge and self.data_start_row > 0:
            import csv
            import io

            with open(path, 'r', encoding=self.encoding) as f:
                raw_lines = f.readlines()

            # Find the main header row from meta_schema if fmt_info provided
            if fmt_info is not None and hasattr(fmt_info, 'meta_schema'):
                for row_idx, schema_type in fmt_info.meta_schema.items():
                    if schema_type == "header":
                        main_header_row = row_idx
                        break

            # Parse meta rows up to data_start_row
            meta_text = ''.join(raw_lines[:self.data_start_row])
            reader = csv.reader(io.StringIO(meta_text), delimiter=self.delimiter)
            meta_rows = list(reader)

            # Extract PART_ID/SOFT_BIN row and header row
            pid_row = meta_rows[self.part_id_row] if self.part_id_row < len(meta_rows) else []
            hdr_row = meta_rows[main_header_row] if main_header_row < len(meta_rows) else []

            # Merge: use hdr_row values, but fill empty cells from pid_row
            merged_header = []
            max_len = max(len(pid_row), len(hdr_row))
            for i in range(max_len):
                hdr_val = hdr_row[i].strip() if i < len(hdr_row) else ''
                pid_val = pid_row[i].strip() if i < len(pid_row) else ''
                merged_header.append(hdr_val if hdr_val else pid_val)

            # Read data starting from data_start_row
            data_text = ''.join(raw_lines[self.data_start_row:])
            if data_text.strip():
                df = pd.read_csv(
                    io.StringIO(data_text),
                    names=merged_header,
                    encoding=self.encoding,
                    delimiter=self.delimiter,
                    skipinitialspace=True,
                )
                # Unit conversion (after reading, before returning)
                self._apply_unit_conversion(df, path, fmt_info, raw_lines)
                return df

        # Fallback: original behavior
        df = pd.read_csv(
            path, skiprows=self.skiprows,
            encoding=self.encoding, delimiter=self.delimiter,
        )
        # Data filtering: remove skip rows, stop at blank rows
        self._filter_dataframe(df)
        # Unit conversion
        self._apply_unit_conversion(df, path, fmt_info)
        return df

    def _filter_dataframe(self, df: 'pd.DataFrame'):
        """In-place filter: remove skip_row_values rows and stop at blank."""
        # Remove rows matching skip_row_values (e.g., PART_ID="1" or "END")
        for col, values in self.skip_row_values.items():
            if col in df.columns:
                for val in values:
                    df.drop(df.index[df[col].astype(str).str.strip() == str(val)],
                            inplace=True, errors='ignore')

        # Stop at first entirely blank row
        if self.stop_at_blank_row:
            blank_mask = df.isna().all(axis=1) | df.eq("").all(axis=1)
            first_blank = blank_mask.idxmax() if blank_mask.any() else -1
            if first_blank > 0:
                df.drop(range(first_blank, len(df)), inplace=True, errors='ignore')

        df.reset_index(drop=True, inplace=True)

    def _apply_unit_conversion(self, df: 'pd.DataFrame', path: str,
                                fmt_info: 'FormatInfo | None' = None,
                                raw_lines: list[str] | None = None):
        """Convert numeric columns to SI units using the unit row.

        Reads the unit row (identified by meta_schema or unit_row in
        FormatInfo) and applies UnitConverter to each test column.
        Modifies df in-place.
        """
        if fmt_info is None or df is None or df.empty:
            return

        # Find the unit row index
        unit_row = -1
        meta_schema = getattr(fmt_info, 'meta_schema', {}) or {}
        for row_idx, schema_type in meta_schema.items():
            if schema_type == "unit":
                unit_row = row_idx
                break
        if unit_row < 0:
            unit_row = getattr(fmt_info, 'unit_row', -1)
        if unit_row < 0:
            return  # No unit information available

        # Read the unit row from the file
        if raw_lines is None:
            try:
                with open(path, 'r', encoding=self.encoding) as f:
                    raw_lines = f.readlines()
            except Exception:
                return

        if unit_row >= len(raw_lines):
            return

        import csv
        import io
        from core.unit_converter import UnitConverter

        reader = csv.reader(
            io.StringIO(raw_lines[unit_row]),
            delimiter=self.delimiter,
        )
        unit_cells = next(reader, [])
        # Trim unit_cells to match df columns
        # The first 2+ cells are PART_ID/SOFT_BIN units (usually empty)
        col_mapping: list[tuple[str, float]] = []  # (si_unit, multiplier)
        for i in range(len(df.columns)):
            if i < len(unit_cells):
                unit_str = unit_cells[i].strip()
            else:
                unit_str = ""
            si_unit, multiplier = UnitConverter.parse_unit(unit_str)
            col_mapping.append((si_unit, multiplier))

        # Apply conversion to each test column
        for i, col in enumerate(df.columns):
            if col in ("PART_ID", "SOFT_BIN", "group", "filepath", "SITE"):
                continue
            if i >= len(col_mapping):
                continue
            _, multiplier = col_mapping[i]
            # Ensure float dtype before any conversion (avoids FutureWarning
            # with int64 columns being set with float values)
            if callable(multiplier) or multiplier != 1.0:
                df[col] = df[col].astype(float)
            if callable(multiplier):
                # Non-linear conversion (e.g., °F → °C)
                _fn = multiplier
                df[col] = df[col].apply(_fn)
            elif multiplier != 1.0:
                df[col] = df[col] * multiplier


class DefaultExcelParser:
    """默认 Excel 解析器：跳过前 4 行元信息（同 CSV 行为）"""

    def __init__(self, skiprows: list[int] | None = None):
        # 与 CSV 一致：跳过第 2-4 行，保留第 1 行作为表头
        self.skiprows = skiprows if skiprows is not None else [1, 2, 3]

    @property
    def supported_extensions(self) -> list[str]:
        return ['.xlsx', '.xls']

    def read(self, path: str) -> pd.DataFrame:
        import pandas as pd
        # 不使用 dtype_backend='pyarrow'（非标准依赖，Windows 常见问题）
        return pd.read_excel(path, skiprows=self.skiprows)


# ── 全局单例 ──

_default_manager = ParserManager()
_default_manager.register(DefaultCSVParser())
_default_manager.register(DefaultExcelParser())


def get_parser_manager() -> ParserManager:
    return _default_manager


def read_file(path: str) -> pd.DataFrame:
    return _default_manager.read(path)

if __name__ == "__main__":
    print(_default_manager.read("/run/media/zys/7C64A61F64A5DBE0/reliability-tool/data/T0/T0_产线_A copy.csv"))
