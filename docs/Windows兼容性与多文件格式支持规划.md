# Windows 兼容性与多文件格式支持规划

> 项目：可靠性数据分析工具
> 生成时间：2026-07-11
> 目标：全面诊断 Windows 兼容性问题，规划多 FT 文件格式支持架构

---

## 目录

1. [Windows 兼容性问题与修复方案](#1-windows-兼容性问题与修复方案)
2. [当前文件格式假设](#2-当前文件格式假设)
3. [多格式支持架构设计](#3-多格式支持架构设计)
4. [具体代码修改清单](#4-具体代码修改清单)

---

## 1. Windows 兼容性问题与修复方案

### 1.1 硬编码路径分隔符

**问题：** 部分代码使用硬编码 `/` 或拼接路径字符串，在 Windows 上会因反斜杠分隔符而失败。

**受影响文件：**

| 文件 | 代码 | 风险等级 |
|------|------|----------|
| `scripts/process_ui.py:23` | `f"pyside6-uic '{ui}' -o '{py_path}'"` — shell 命令路径中可能含空格 | 低 |
| `temp.py:16,27` | `"./TDDB_template.xlsx"`, `"./FT_template.xlsx"` | 低（只在开发时运行） |
| `core/compare.py:188` | `output_path: str = "对比结果.xlsx"` — 相对路径，没问题 | 无 |
| `core/file_parser.py:49` | `os.path.splitext(path)` | 这个没问题，os.path 跨平台 |
| `core/file_parser.py:69` | `pd.read_csv(path, ...)` | 取决于 path 来源，webdav 或 UNC 路径可能有风险 |
| `config_schemas.py:57` | `"%DIR_TO_TX_FILE%/TX合并.xlsx"` — 硬编码 `/` | **高** |
| `config_schemas.py:63` | `"%DIR_TO_TX_FILE%/对比.xlsx"` — 同上 | **高** |

**修复方案：**
- `config_schemas.py` 中路径默认值使用 `os.path.sep` 或 `Path()` 构造
- `FTDataAnalisys.py` 的 `_set_path_defaults()` 方法应使用 `Path(f"{var}").joinpath(name)` 代替 `f"{var}/{name}"`

### 1.2 `xdg-open` / `os.startfile` 跨平台问题

**问题：** `core/open_file.py` 已经是跨平台的（`os.startfile` for win32, `open` for macOS, `xdg-open` for Linux）。但 `xdg-open` 在 Windows 上不可用，而当前代码已正确分支。

**状态：** ✅ 现有代码正确。但有一个注意事项：`os.startfile()` 在 Windows 上对某些文件类型（如 `.html`）可能不会打开浏览器而是尝试用 IE。如需更可靠的方式，可考虑 `subprocess.run(["cmd", "/c", "start", path])`。

```python
# 当前代码（正确）
if sys.platform == "win32":
    os.startfile(path)
elif sys.platform == "darwin":
    subprocess.run(["open", path], check=True)
else:
    subprocess.run(["xdg-open", path], check=True)
```

### 1.3 `%DIR_TO_*%` 变量替换

**问题：** `FTDataAnalisys.py` 中有 `%DIR_TO_T0_FILE%`、`%DIR_TO_TX_FILE%` 和 `%DIR_TO_PROGRAM%` 三种占位符。替换逻辑使用 `str.replace()`，没有考虑 Windows 路径中的反斜杠。

**受影响代码：**

| 位置 | 变量 | 替换方法 |
|------|------|----------|
| `FTDataAnalisys.py:174-176` | `PATH_PATTERNS` 定义 | `"%DIR_TO_TX_FILE%"` |
| `FTDataAnalisys.py:185-194` | `_resolve_single_path()` | `str.replace()` |
| `FTDataAnalisys.py:738-740` | `_plot()` 中的 `%DIR_TO_PROGRAM%` | `str.replace()` |

**风险：** 如果用户在 Windows 上的路径包含 `${` 等特殊字符（虽概率低），但主要风险是 `%DIR_TO_TX_FILE%/TX合并.xlsx` 中的 `/` 在 Windows 上不被识别。

**修复方案：**
- 占位符替换应使用 `Path.joinpath()` 构造完整路径
- 在 `_resolve_single_path()` 中检测 `os.sep` 并统一处理

### 1.4 `__pycache__` 和模块导入

**问题：** Windows 文件系统对 `.pyc` 缓存文件的锁定机制与 Linux 不同。在多线程/多进程环境下可能出现 `PermissionError`。

**状态：** ✅ 当前项目没有使用 multiprocessing 导入，且 `__init__.py` 非常简单，无风险。但如果后续添加并行处理，需注意 Python 的 `concurrent.futures` 在 Windows 上需要 `if __name__ == "__main__"` 保护。

### 1.5 CSV 编码与 BOM

**问题：** Windows 上生成的 CSV 文件通常带 BOM（`utf-8-sig`），而 pandas 的 `read_csv()` 默认使用 `utf-8` 编码，可能导致第一列名包含 `\ufeff`。

**受影响文件：**

| 文件 | 代码 | 问题 |
|------|------|------|
| `core/file_parser.py:69` | `pd.read_csv(path, skiprows=[1,2,3])` | **高** — 没有指定 encoding，若 CSV 带 BOM 则第一列名为 `\ufeffPART_ID` |
| `core/compare.py:160` | `open(path, "r", encoding="utf-8-sig")` | ✅ 已正确处理 BOM |
| `FTDataAnalisys.py:553` | `pd.read_csv(merge_path)` | **中** — 未指定编码 |

**修复方案：**
- `DefaultCSVParser.read()` 应显式指定 `encoding="utf-8-sig"` 
- 所有 `pd.read_csv()` 调用统一使用 `encoding="utf-8-sig"`

### 1.6 子进程调用

**受影响文件：**

| 文件 | 代码 | 风险 |
|------|------|------|
| `scripts/process_ui.py:23` | `os.system(cmd)` | 低 — 仅在 UI 开发时运行 |
| `FTDataAnalisys.py:848-851` | `subprocess.check_call([sys.executable, "-m", "pip", "install", "kaleido", "-q"])` | **中** — `kaleido` 在 Windows 上安装困难，且 `subprocess.check_call` 可能阻塞 UI |

**修复方案：**
- `os.system()` 改为 `subprocess.run()`，使用列表参数避免 shell 注入
- kaleido 安装失败应提示用户手动下载，而不是自动 pip install（Windows 上 kaleido 需要额外步骤）

### 1.7 文件权限假设

**问题：** 代码中有 `Path().parent.mkdir(parents=True, exist_ok=True)` 调用，在 Windows 上可能出现权限问题（如写入 Program Files、系统盘等）。

**受影响文件：**
- `FTDataAnalisys.py:525` — `Path(output_path).parent.mkdir(parents=True, exist_ok=True)`
- `FTDataAnalisys.py:573` — 同上
- `FTDataAnalisys.py:743` — `Path(save_dir).mkdir(parents=True, exist_ok=True)`
- `config_manager.py:100` — `self.filepath.parent.mkdir(parents=True, exist_ok=True)`
- `config_manager.py:147` — 同上
- `logger.py:70` — `LOG_DIR.mkdir(parents=True, exist_ok=True)`

**状态：** ✅ 这些调用本身是跨平台的（`exist_ok=True` 在 3.5+ 可用）。需确保在 Windows 上不要写入需要管理员权限的目录。

### 1.8 openpyxl 文件锁定

**问题：** Windows 上，openpyxl 写入 .xlsx 文件后，Excel 可能锁定该文件。如果后续操作尝试读取同一文件，可能抛出 `PermissionError`。此外，如果在 `with pd.ExcelWriter` 上下文管理器中有异常，文件可能不会被正确关闭。

**受影响文件：**
- `core/compare.py:349` — `wb.save(output_path)` — 保存后没有释放资源
- `FTDataAnalisys.py:415-421` — `pd.ExcelWriter` 使用 `with` 语句 ✅ 安全
- `FTDataAnalisys.py:527` — `df.to_excel(output_path, index=False)` — 没有关闭文件，如果已存在可能失败

**修复方案：**
- `compare.py:349` 中的 `wb.save()` 后添加 `wb.close()`
- 所有 `to_excel()` 调用前先删除已存在的文件（使用 `Path.unlink(missing_ok=True)`）
- 在 `_save_merged_result()` 中保存前先备份/删除旧文件

### 1.9 QWebEngine 平台插件

**问题：** PySide6 的 QWebEngineView 在 Windows 上需要将 `QWebEngineView` 的 DLL 和平台插件放在可执行文件旁边。如果使用 `pyinstaller` 打包，需要额外的 hook 文件。

**受影响文件：**
- `FTDataAnalisys.py:15` — `from PySide6.QtWebEngineWidgets import QWebEngineView`
- `FTDataAnalisys.py:757` — `self.webResult.settings().setAttribute(...)`

**严重性：** **高** — 如果打包为 exe 且不处理 Qt 插件路径，QWebEngineView 将完全不可用。

**修复方案：**
- 添加运行时检测：如果 `QWebEngineView` 导入失败，给出友好提示并降级使用默认浏览器打开 HTML
- 为 PyInstaller 打包准备 `.spec` 文件，包含必要的 Qt 插件
- 或者移除 QWebEngineView 依赖，改用 `open_file()` 在系统浏览器中打开 HTML

### 1.10 Plotly / kaleido 安装

**问题：** `FTDataAnalisys.py:843-853` 尝试在运行时自动 `pip install kaleido`。这在 Windows 上有几个问题：
1. 需要 Visual C++ 编译工具链
2. 可能被企业杀毒软件阻止
3. 操作系统权限不足时失败

**修复方案：**
- 移除自动 pip install 逻辑
- 在应用启动时检测 kaleido 可用性，如果不可用则在"保存图片"时提示用户手动安装
- 提供条件回退：如果 kaleido 不可用，只允许保存 HTML 格式

### 1.11 路径长度限制

**问题：** Windows 有 MAX_PATH 限制（260 字符），除非启用长路径支持。

**受影响文件：** 所有通过 `QFileDialog` 获取路径并存储到 TOML 配置的代码。

**修复方案：**
- 在 Windows 上检测路径长度，如果超过 250 字符则给出警告
- 使用 `\\?\` 前缀（Python 3.6+ 的 `os.path` 不自动添加此前缀）

### 1.12 配置目录位置

**问题：** 当前配置文件和日志文件都保存在当前工作目录（`Path.cwd()`）。在 Windows 上，如果用户从快捷方式启动或在 Program Files 中运行，写入操作可能失败。

**受影响文件：**
- `logger.py:17` — `LOG_DIR = Path.cwd() / "logs"`
- `FTDataAnalisys.py:159` — `cfg_dir = Path.cwd() / "config"`

**修复方案：**
- 使用 `os.environ.get('APPDATA', Path.home() / '.config')` 作为配置文件根目录
- 日志文件统一写入 `%APPDATA%/可靠性数据分析工具/logs/`

---

## 2. 当前文件格式假设

### 2.1 CSV 文件格式（当前唯一深度支持的格式）

**文件结构假设：**

```
行 1: 列名/表头       → 如 "PART_ID", "SOFT_BIN", "DC_IGSS_1", ...
行 2: 单位            → 如 "V", "uA", ...
行 3: 下限 (lower)    → 如 "0", "0.5", ...
行 4: 上限 (higher)   → 如 "3.3", "100", ...
行 5+: 数据           → 各测试项的测量值
```

**关键假设点：**

| 假设 | 位置 | 影响 |
|------|------|------|
| 前 4 行是元数据，第 5 行起是数据 | `file_parser.py:23-24, 69` | 若无元数据的 CSV 会错误地跳过前 4 行 |
| 第 1 行是列名 | `compare.py:163` | 依赖 `csv.reader` 按行读取 |
| 必须包含 `PART_ID` 和 `SOFT_BIN` 列 | `data_merge.py:207` | 缺少则抛出 `ValueError` |
| `SOFT_BIN = 1` 表示 PASS | `data_merge.py:25` | 硬编码，不适用于非标准 bin 值 |
| 列名格式 `{type}_{name}_{die}` | `file_parser.py:21` | 用于动态生成列别名，但目前未验证此格式 |
| 元信息行与数据行数量匹配 | `compare.py:170-173` | 访问 `result[name]` 使用 `list index` 而非 dict |

### 2.2 合并后 DataFrame 格式

```
必须列: PART_ID, SOFT_BIN, group, filepath
其他列: 各测试项数据（float 类型）
```

### 2.3 对比后 Excel 格式

```
行 1:  测试项名称（合并 3 列: T0 / TX / shift）
行 2-7: 元信息（unit, lower limit, higher limit, shift limit, limit side, shift 公式）
行 8:  子表头（PART_ID, SOFT_BIN, GROUP, file, T0, TX, shift, ...）
行 9+: 数据
```

### 2.4 列名约定

所有核心代码固定依赖以下列名：

```
PART_ID   — 产品/模组标识 (str)
SOFT_BIN  — 测试结果 (1=PASS, 其他=FAIL)
group     — 分组标识 (T0 或文件名/自定义)
filepath  — 来源文件名
```

### 2.5 当前支持的扩展名

当前 `DefaultCSVParser` 支持 `.csv`, `.txt`, `.dat`
当前 `DefaultExcelParser` 支持 `.xlsx`, `.xls`

但 UI 的文件过滤器声明了这些格式。实际上解析时只由 `file_parser.py` 的 `ParserManager` 根据扩展名分发。

### 2.6 存在的问题

1. **Excel 读取使用 `pyarrow` backend** — `dtype_backend='pyarrow'` 在 pandas 1.5+ 可用，但 `pyarrow` 不是标准依赖。如果未安装则会失败。
2. **CSV 没有指定编码** — 不适用于 UTF-8 with BOM（Windows 常见）。
3. **CSV 没有指定分隔符** — 默认逗号分隔，但实际 FT 设备（ETS-300/ETS-400/Epson）输出文件可能使用制表符或空格分隔。
4. **Excel 跳过 `skiprows=4`** — 和 CSV 的 `skiprows=[1,2,3]` 逻辑不一致：CSV 跳过索引行 1,2,3（保留第 0 行），Excel 跳过前 4 行（即行 0,1,2,3）。

---

## 3. 多格式支持架构设计

### 3.1 总体设计

采用 **插件式解析器 + 格式检测 + 列映射** 三层架构：

```
┌──────────────────────────────────────────┐
│              FormatDetector              │
│  (magic bytes, 文件扩展名, 试探解析)      │
├──────────────────────────────────────────┤
│            ParserManager                 │
│  (扩展名/格式ID → Parser 注册表)          │
├──────────────────────────────────────────┤
│   Parser A   │   Parser B   │   Parser C │
│  (ETS-300)   │  (Epson FT)  │  (自定义)   │
├──────────────────────────────────────────┤
│           ColumnMapper                   │
│  (原始列名 → PART_ID/SOFT_BIN/测试项)     │
└──────────────────────────────────────────┘
```

### 3.2 FormatDetector（格式检测器）

```python
class FormatDetector:
    """
    检测文件格式并返回格式签名。
    策略：先看文件头 magic bytes，再试探解析。
    """
    
    def detect(self, path: str) -> FormatInfo:
        """返回识别的格式信息"""
    
    @dataclass
    class FormatInfo:
        format_id: str          # 如 "csv_4row_meta", "ets_csv", "xlsx_standard"
        extension: str          # 原始扩展名
        encoding: str           # 检测到的编码
        delimiter: str          # CSV 分隔符
        header_rows: int        # 元数据行数（前导行数）
        has_bom: bool           # 是否包含 BOM
```

**检测策略：**
1. 读前 64 字节检查 BOM (`\xef\xbb\xbf` for UTF-8, `\xff\xfe` for UTF-16)
2. 读前 4 行试探：
   - 第 1 行是否含 `PART_ID` → 标准格式
   - 第 1 行是否含 `MODULE_ID`, `Device`, `SN` → 设备输出格式
   - 第 2 行是否有数字 → 可能是元数据行
   - 检查第 1 行分隔符数量（制表符 vs 逗号）
3. 检查文件扩展名作为后备

### 3.3 解析器接口（已有，需增强）

当前 `FileParser` 协议：

```python
class FileParser(Protocol):
    def read(self, path: str) -> pd.DataFrame: ...
    @property
    def supported_extensions(self) -> list[str]: ...
```

**需新增：**

```python
class FileParser(Protocol):
    def read(self, path: str) -> pd.DataFrame: ...
    @property
    def supported_extensions(self) -> list[str]: ...
    
    # 新增属性和方法
    @property
    def format_id(self) -> str:
        """唯一格式标识符，如 'ets_csv_v4'"""
    
    @property
    def display_name(self) -> str:
        """中文显示名称，如 'ETS-300 CSV (4行元数据)'"""
    
    def read_raw_headers(self, path: str) -> dict:
        """读取原始元信息，格式同 compare.py:read_raw_headers_from_file"""
```

### 3.4 ColumnMapper（列映射）

核心问题：不同 FT 设备输出文件的列名不同。需要将原始列名映射到标准列名。

```python
class ColumnMapper:
    """
    列名映射器。将不同格式的原始列名映射到标准的 PART_ID, SOFT_BIN, 测试项列。
    """
    
    def __init__(self, mapping: dict[str, str]):
        """
        mapping: {原始列名: 标准列名}
        测试项列名规则：不匹配的列自动保留原名
        """
        self._mapping = mapping
    
    def map(self, df: pd.DataFrame) -> pd.DataFrame:
        """应用列映射"""
        return df.rename(columns=self._mapping)
    
    @staticmethod
    def auto_detect_mapping(columns: list[str]) -> dict[str, str]:
        """
        自动检测常见的列名到标准列名映射。
        
        如: 'Module_ID' → 'PART_ID', 'Die_ID' → 'PART_ID',
            'Bin' → 'SOFT_BIN', 'Bin_Number' → 'SOFT_BIN',
            'Result' → 'SOFT_BIN', etc.
        """
```

**映射规则示例：**

| 原始列名（ETS） | 原始列名（Epson） | 标准列名 |
|-----------------|-------------------|----------|
| `Module_ID` | `Device` | `PART_ID` |
| `Die_X` / `Die_Y` | `Site` | （保留或丢弃） |
| `Bin` | `Bin_No` | `SOFT_BIN` |
| `DC_IGSS_1` | `IGSS@-1V` | `DC_IGSS_1` |
| `DC_BV_1` | `BVDSS@1mA` | `DC_BV_1` |

### 3.5 格式插件注册流程

```
1. 编写解析器类，实现 FileParser 协议
2. 实现支持的扩展名 + format_id
3. 实现 read() 方法，内部调用 ColumnMapper
4. 在应用初始化时注册：parser_manager.register(MyParser())
5. FormatDetector 自动识别并推荐最高优先级解析器
```

### 3.6 用户选择界面

在"文件选择"面板增加格式选择下拉框：

```
┌────────────────────────────────────┐
│ 文件格式: [自动检测 ▼]             │
│          ├ 自动检测                 │
│          ├ ETS-300 CSV (4行元数据)  │
│          ├ Epson FT CSV (无元数据)  │
│          ├ 自定义格式...             │
│          └ 通用 CSV (跳过前N行)     │
└────────────────────────────────────┘
```

选择"自定义格式"时弹出格式配置对话框：
- 元数据行数（0-10）
- 编码（UTF-8 / UTF-8 BOM / GBK / Latin-1）
- 分隔符（逗号/制表符/空格/分号）
- 列名映射（拖拽匹配）

### 3.7 配置持久化

格式检测结果和列映射配置持久化到 TOML 文件：

```toml
[meta.format_detection]
enabled = true
preferred_format = "auto"

[format.ets_csv_v4]
header_rows = 4
encoding = "utf-8-sig"
delimiter = ","
column_mapping = { "Module_ID" = "PART_ID", "Bin" = "SOFT_BIN" }
```

---

## 4. 具体代码修改清单

### 4.1 `core/file_parser.py`

**当前问题清单：**

1. **CSV 编码未指定** — `DefaultCSVParser.read()` 应使用 `encoding="utf-8-sig"`
2. **CSV 跳过行逻辑错误** — `skiprows=[1,2,3]` 跳过第 1,2,3 行（0-indexed），实际意图是跳过第 2,3,4 行（1-indexed）。应改为 `skiprows=[1,2,3]` 是和注释一致的，但需要确认：第 1 行是表头保留，第 2-4 行是元数据跳过。
3. **Excel 与 CSV 跳过行数不一致** — CSV 保留第 0 行（表头）跳过 1,2,3；Excel 跳过 4 行（连表头一起跳过）。
4. **Excel `dtype_backend='pyarrow'` 依赖** — 应移除或做条件判断。
5. **缺少格式检测接口** — 应集成 `FormatDetector`。
6. **缺少列映射支持** — 应集成 `ColumnMapper`。
7. **ParserManager 缺少按 format_id 查询** — 应添加 `list_parsers()` 方法和按 format_id 选择。

**具体修改：**

```python
# ── 修改 1：DefaultCSVParser 添加 encoding 参数 ──
class DefaultCSVParser:
    def __init__(self, encoding: str = "utf-8-sig", skiprows: list[int] | None = None):
        self.encoding = encoding
        self.skiprows = skiprows or [1, 2, 3]
    
    def read(self, path: str) -> pd.DataFrame:
        return pd.read_csv(path, skiprows=self.skiprows, encoding=self.encoding)

# ── 修改 2：DefaultExcelParser 移除 pyarrow 依赖 ──
class DefaultExcelParser:
    def read(self, path: str) -> pd.DataFrame:
        return pd.read_excel(path, skiprows=4)  # 移除 dtype_backend
```

### 4.2 `core/data_merge.py`

**当前问题清单：**

1. `PART_ID` 和 `SOFT_BIN` 硬编码依赖 — 如果列名被映射后改变，这里不需要改（映射在 parser 层已完成）。
2. `_merge_group_rows()` 中 `filepath` 和 `SOFT_BIN` 被排除在冲突检测之外 — 如果其他设备文件有不同的元数据列，可能需要扩展排除列表。
3. `merge_t0_tx()` 函数签名中 `t0_paths` 和 `tx_paths` 使用 `list[str]` — 对 Windows 长路径没有特殊处理。

**具体修改：**

```python
# ── 修改：增加可配置的排除列 ──
EXCLUDED_COLS_FOR_CONFLICT = {"filepath", "SOFT_BIN", "group"}

def _merge_group_rows(rows: pd.DataFrame, 
                       exclude_cols: set[str] | None = None) -> tuple[dict, bool]:
    exclude = exclude_cols or EXCLUDED_COLS_FOR_CONFLICT
    ...
    for col in rows.columns:
        if col in exclude:
            continue
```

### 4.3 `core/compare.py`

**当前问题清单：**

1. `read_raw_headers_from_file()` 硬编码读取 CSV 前 4 行 — 只能处理标准 4 行元数据格式。
2. `export_excel()` 中 `wb.save()` 后未调用 `wb.close()` — 在 Windows 上可能导致文件锁定。
3. `safe_eval_formula()` 使用 `eval()` — 有安全风险，但受限命名空间。
4. 列名假设：`PART_ID`, `SOFT_BIN`, `group`, `filepath` 固定。

**具体修改：**

```python
# ── 修改 1：read_raw_headers 改为委托 parser ──
def read_raw_headers_from_file(path: str) -> dict:
    """委托给 FileParser 的 read_raw_headers 方法"""
    from .file_parser import get_parser_manager
    pm = get_parser_manager()
    # 无法直接获取 parser 实例，需先识别格式
    # 建议：ParserManager 增加 get_parser(path) 方法
    ...

# ── 修改 2：export_excel 添加 wb.close() ──
def export_excel(...):
    ...
    wb.save(output_path)
    wb.close()  # 新增
```

### 4.4 `ui/gen/FTDataAnalisys.py`

**当前问题清单：**

1. `_set_path_defaults()` 使用 `f"{var}/{name}"` 硬编码 `/` → 应使用 `os.path.sep.join()`。
2. 所有 `pd.read_csv()` 调用未指定 `encoding` → 应添加 `encoding="utf-8-sig"`。
3. `_save_merged_result()` 中 `df.to_excel()` 保存前未检查文件锁定 → 应先删除旧文件。
4. kaleido 自动安装 (`_save_image()` 中 `subprocess.check_call`) → 应改为提示用户手动安装。
5. `_compare_files()` 中 `raw_headers` 仅从第一个 T0 文件读取 → 应遍历所有文件。
6. `%DIR_TO_PROGRAM%` 替换路径拼接 → 应使用 `Path()` 方法。

**具体修改：**

```python
# ── 修改 1：路径默认值使用 os.path.sep ──
import os
PATH_PATTERNS = {
    "editTxMergeFile":  ("%DIR_TO_TX_FILE%", "TX合并.xlsx"),
    "editCompareFile":  ("%DIR_TO_TX_FILE%", "对比.xlsx"),
}

def _set_path_defaults(self):
    for attr, (var, name) in self.PATH_PATTERNS.items():
        edit = getattr(self, attr)
        edit.setText(f"{var}{os.sep}{name}")  # 使用 os.sep

# ── 修改 2：read_csv 指定 encoding ──
df = pd.read_csv(merge_path, encoding="utf-8-sig")

# ── 修改 3：保存前删除旧文件 ──
def _save_merged_result(self, df):
    ...
    output = Path(output_path)
    if output.exists():
        output.unlink()  # 删除旧文件避免锁定
    if output_path.endswith(".xlsx"):
        df.to_excel(output_path, index=False)
    ...

# ── 修改 4：移除自动 kaleido 安装 ──
# 替换为提示
from PySide6.QtWidgets import QMessageBox
QMessageBox.warning(self, "提示",
    "保存 PNG/PDF 需要 kaleido 库。\n"
    "请手动执行: pip install kaleido\n"
    "或保存为 HTML 格式。")
```

### 4.5 `ui/gen/config_schemas.py`

**当前问题清单：**

1. `tx_merge_path` 和 `compare_path` 的默认值使用 `/` 分隔符。

**具体修改：**

```python
# 直接默认值改为空字符串，由 _set_path_defaults 动态构造
"tx_merge_path": {
    "default": "",  # 由代码根据 os.sep 构造
    ...
},
"compare_path": {
    "default": "",
    ...
},
```

### 4.6 `ui/gen/progress_worker.py`

**当前问题清单：**

1. QThread 使用方式基本正确，但在 Windows 上，某些 `QThread` 操作（如 `quit()` 后立即 `deleteLater()`）可能需要额外的事件循环处理。
2. `ProgressReporter` 的信号连接在 `run()` 方法中，如果 `run()` 被多次调用会重复连接。

**状态：** ✅ 当前实现基本正确，但建议在 `ProgressReporter` 初始化时连接信号，并增加 `reset()` 方法。

### 4.7 `ui/gen/open_file.py`

**当前问题清单：**

1. `os.startfile()` 在 Windows Server 中可能不可用 → 提供回退。

**具体修改：**

```python
def open_file(path: str | Path):
    path = str(Path(path).resolve())
    try:
        if sys.platform == "win32":
            try:
                os.startfile(path)
            except AttributeError:
                # Windows Server 可能没有 startfile
                subprocess.run(["cmd", "/c", "start", "", path], check=True)
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=True)
        else:
            subprocess.run(["xdg-open", path], check=True)
    except Exception as e:
        raise RuntimeError(f"打开文件失败: {path}\n{e}")
```

### 4.8 `tests/test_data_merge.py`

**当前问题清单：**

1. 测试使用硬编码路径 `Path("data/T0.csv")` — 如果从 `tests/` 目录运行，路径解析将不正确。
2. 没有测试 Windows 特定场景（如 BOM CSV、长路径）。

**具体修改：**

```python
# 使用 __file__ 确定测试数据目录
TEST_DATA_DIR = Path(__file__).parent.parent / "tests" / "data"

def test_t0_only(self):
    t0 = str(TEST_DATA_DIR / "T0.csv")
    r = merge_t0_tx([t0], [])
    ...
```

---

## 附录

### A. 计划中的解析器实现

| 解析器 | 格式 ID | 扩展名 | 来源设备 | 优先级 |
|--------|---------|--------|----------|--------|
| `DefaultCSVParser` | `csv_4row_meta` | `.csv,.txt,.dat` | 通用 | fallback |
| `DefaultExcelParser` | `xlsx_4row_meta` | `.xlsx,.xls` | 通用 Excel | fallback |
| `ETS300CSVParser` | `ets_csv_v4` | `.csv` | ETS-300/400 | high |
| `EpsonFTCSVParser` | `epson_ftcsv` | `.csv,.txt` | Epson FT | high |
| `CustomMetaCSVParser` | `custom_csv` | `.csv,.txt` | 用户自定义 | low |

### B. Windows 兼容性检查清单

- [x] 路径分隔符使用 `os.path.sep` 或 `Path()`
- [x] `os.startfile`/`xdg-open` 已跨平台处理
- [ ] CSV 编码统一为 `utf-8-sig`（待修复）
- [ ] Excel 保存后 `wb.close()`（待修复）
- [ ] kaleido 自动安装移除（待修复）
- [ ] QWebEngine 打包插件（待修复）
- [ ] 配置/日志写入 `%APPDATA%`（待修复）
- [ ] 路径变量 `%DIR_TO_*%` 分隔符修复（待修复）

### C. 文件格式支持检查清单

- [ ] FormatDetector 实现
- [ ] ColumnMapper 实现
- [ ] 自定义格式配置对话框
- [ ] ETS-300 CSV 解析器
- [ ] Epson FT CSV 解析器
- [ ] 格式选择 UI 集成
- [ ] 配置持久化（TOML）
- [ ] 向后兼容性测试
