# 架构说明

## 分层设计

```
app.py                     ← 入口：QApplication + MainWindow().show()
  └─ ui/gen/mainWindow.py  ← 主窗口：logger、tab 管理、菜单信号
      ├─ ui/gen/FTDataAnalisys.py  ← FT 数据分析 tab
      └─ ui/gen/*.py               ← 后续新增 tab
```

## 核心模块

### 1. UI 生成层 (`ui/gen/*_ui.py`)

由 `pyside6-uic` 从 `.ui` 文件自动生成，**禁止手动修改**。生成的文件以 `_ui.py` 结尾。

### 2. 业务层 (`ui/gen/*.py`)

继承对应的 `Ui_*` 类，通过多重继承模式关联：
```python
class FTDataAnalysisPage(QWidget, Ui_FTDataAnalysisWidget):
    def __init__(self):
        self.setupUi(self)  # Ui_* 类的方法，创建所有控件
```
- 构造函数：`setupUi()` → 初始化子模块 → `_connect_signals()`
- 所有控件通过 `self.btnXxx` 直接访问

### 3. 配置管理 (`config_manager.py`)

```
ConfigManager
├── 一个 TOML 文件 = 一个配置域（如 FTDataAnalisys）
├── 多个 section = 多套配置（default, test_v1, ...）
├── [meta] section 记录活跃 section 名
├── schema 定义 key + 默认值 + 类型
└── load() 时自动补全缺失 key
```

读写流程：
```
ConfigDialog → cm.set(key, val) → cm.save() → TOML 文件
ConfigDialog ← cm.get(key)      ← cm.load() ← TOML 文件
```

### 4. 日志 (`logger.py`)

三层输出：
- **文件**：`./logs/reliability-tool.log`，RotatingFileHandler（5MB × 3）
- **控制台**：开发时可见
- **UI**：`关于 → 查看日志` 弹窗，纯文本只读查看

## 数据流

```
用户操作 → 信号(signal) → 业务函数 → logger 记录
                              ├→ ConfigManager 读写
                              └→ 更新 UI（状态栏、控件）
```

## 配置热更新

新增 key 只需要在 `config_schemas.py` 的 schema 中定义默认值，
下次 `cm.load()` 时自动补充到所有已有 section。
