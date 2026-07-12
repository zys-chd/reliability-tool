# 打包与性能优化设计

## 一、当前依赖胖瘦分析

### 磁盘占用

| 依赖 | 安装大小 | 性质 |
|------|---------|------|
| **Qt6 WebEngine** (libQt6WebEngineCore.so) | **~203 MB** | 完整 Chromium 内核 |
| PySide6（不含 WebEngine） | ~49 MB | Qt6 Python 绑定额外 ~80 MB 动态库 |
| pandas + numpy | ~110 MB | 数据运算核心 |
| openpyxl | ~3 MB | Excel 读写 |
| plotly | ~15 MB | 交互式图表（纯 Python） |

### 运行时内存（当前状况）

| 场景 | 内存 | 触发时机 |
|------|------|---------|
| 仅 PySide6 GUI | ~80 MB | 启动即占 |
| **+ QtWebEngine Process** | **+120–200 MB** | **首个 QWebEngineView 创建时** |
| + pandas 加载 100MB CSV | +200–500 MB | 用户打开文件时 |
| + plotly 生成图表 | +20–50 MB | 用户点击绘图时 |

**关键结论：**
- WebEngine 是最大单项开销（203 MB 磁盘 + 120–200 MB 运行时）
- 但 plotly 交互图需要它，不能简单砍掉
- **优化方向不是砍掉，而是「延迟加载」+「用完释放」**

---

## 二、推荐方案

### 2.1 打包工具：PyInstaller + UPX

PyInstaller 最成熟，PySide6 支持已验证，Windows 打包文档丰富。

| 选项 | 推荐值 | 原因 |
|------|--------|------|
| 打包器 | **PyInstaller** | 稳定，社区成熟 |
| 压缩 | **UPX**（`--upx-dir`） | 可减少 50–60% 体积 |
| 单文件模式 | `--onefile` | 用户友好，但启动慢 |
| 单目录模式 | `--onedir` | 启动快，适合频繁使用 |
| 排除无用模块 | `--exclude-module` | 减体积 |

**推荐：`--onedir` + UPX**，兼顾体积和启动速度。

### 2.2 WebEngine 延迟初始化（最重要的优化）

QtWebEngine 只有在 **第一次创建 QWebEngineView 实例时** 才会启动 Chromium 子进程。利用这一点：

```python
class FTDataAnalysisPage(QWidget, Ui_FTDataAnalysisWidget):
    def __init__(self):
        self.setupUi(self)
        # 不要把 webResult 放在 ui 里自动创建！
        # 改为用一个占位 QWidget，需要时才替换为 QWebEngineView

    def _show_plot(self, html: str):
        """延迟创建 WebEngine 视图"""
        if not hasattr(self, '_plot_view'):
            # 第一次使用时才创建——此时 Chromium 进程才启动
            from PySide6.QtWebEngineWidgets import QWebEngineView
            self._plot_view = QWebEngineView()
            # 替换占位 widget
            layout = self.gbResultDisplay.layout()
            layout.replaceWidget(self.webResult, self._plot_view)
            self.webResult.hide()
        self._plot_view.setHtml(html)

    def _clear_plot(self):
        """关闭图表时释放 WebEngine 资源"""
        if hasattr(self, '_plot_view'):
            self._plot_view.deleteLater()
            del self._plot_view
            self.webResult.show()
```

效果：用户只看文件列表时内存 ≈ 80 MB，只有点击绘图后才 +120–200 MB。

### 2.3 PyInstaller 打包配置

```python
# scripts/build.py
a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebChannel',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'PIL', 'scipy',  # 无用大库
        'matplotlib.tests', 'pandas.tests',
        'numpy.random._examples',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)
exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
    [], name='ReliabilityTool', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, upx_exclude=[], runtime_tmpdir=None,
    console=False, disable_windowed_traceback=False, argv_emulation=False,
    target_arch=None, codesign_identity=None, entitlements_file=None,
    icon='icon.ico',
)
```

### 2.4 Pandas 内存优化

```python
# 1. 延迟导入
def load_data(self, path):
    import pandas as pd  # 用到才导入
    ...

# 2. 指定 dtype 减少内存
dtype_map = {
    'voltage': 'float32',     # 默认 float64 → 减半
    'current': 'float32',
    'temperature': 'float32',
    'sample_id': 'int32',     # 默认 int64 → 减半
    'status': 'category',     # 枚举用 category
}
df = pd.read_csv(path, dtype=dtype_map)

# 3. 大文件分块读取
for chunk in pd.read_csv(path, chunksize=50000):
    process(chunk)

# 4. 用完即释放
self.data = None  # del 不一定立刻 GC，赋 None + gc.collect()
```

### 2.5 Plotly 导出而非渲染

对于「保存图片」功能，plotly 可以直接导出为静态格式，**不需要 WebEngine**：

```python
import plotly.graph_objects as go
fig = go.Figure(...)
fig.write_image("chart.png")      # 需要 kaleido 或 orca
fig.write_html("chart.html")      # 独立 HTML，也可在 WebEngine 中打开
```

---

## 三、最终预估

### 打包后 exe 大小（PyInstaller + UPX，--onedir）

| 组件 | 预计大小 |
|------|---------|
| Python 解释器 + stdlib | ~25 MB |
| PySide6 核心 (Core/Gui/Widgets) | ~35 MB |
| **Qt6 WebEngine** (libQt6WebEngineCore 等) | **~45 MB (UPX 后)** |
| pandas + numpy | ~40 MB (UPX 后) |
| plotly + openpyxl + 其他 | ~10 MB |
| **合计** | **~130–180 MB** |

### 运行时内存（分阶段）

```
启动（仅 GUI）             →  ~80 MB     ← 未创建 WebEngine
选择文件 + 查看列表        →  ~120 MB    ← pandas 加载文件名
加载数据 CSV              →  ~150–400 MB ← 取决于文件大小
点击「绘图」（WebEngine 启动） → +120–200 MB
关闭绘图 / 关闭文件       →  回落到 ~80–120 MB
```

### 与不做优化的对比

| 场景 | 不优化 | 优化后 | 节省 |
|------|--------|--------|------|
| 空闲内存 | ~80 MB | ~80 MB | — |
| 看文件列表时 | ~280 MB（WebEngine 空跑） | ~80 MB | **200 MB** |
| 加载数据 | ~500+ MB | ~150–400 MB | dtype 优化 |
| 打包体积 | ~180 MB | ~130–180 MB | UPX 压缩 |

---

## 四、实施步骤

### Step 1: WebEngine 延迟初始化
- [ ] 修改 `FTDataAnalisys.ui`：`webResult` 保留为普通 `QWidget`
- [ ] 修改 `FTDataAnalisys.py`：`_show_plot(html)` 方法动态创建 `QWebEngineView`
- [ ] 添加 `_clear_plot()` 释放资源

### Step 2: Pandas 懒加载 + dtype 优化
- [ ] 所有 `import pandas` 放到函数内
- [ ] `read_csv` 添加 `dtype` 参数
- [ ] 大文件用 `chunksize`
- [ ] `close_tab` 时释放数据

### Step 3: 安装 PyInstaller + UPX
- [ ] `pip install pyinstaller`
- [ ] 下载 UPX 并配置 PATH
- [ ] 编写 `scripts/build.py`

### Step 4: Windows 测试
- [ ] 在 Windows VM 或实体机上测试打包
- [ ] 测试各功能是否正常
- [ ] 用 Process Explorer 查看实际内存

### 不涉及改动
- matplotlib 暂未使用，未来集成时直接走 `FigureCanvasQTAgg`
- plotly 交互图正常使用，只是 WebEngine 延迟加载
