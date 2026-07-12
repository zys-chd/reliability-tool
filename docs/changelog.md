# 变更日志

## [0.2.0] — 2026-07-08

### 新增
- 配置管理器：TOML 格式，多 section，自动补 key，活跃 section 持久化
- ConfigDialog：三个 tab（分组/模板/绘图配置），comboBox 切换 section
- 日志系统：文件 + 控制台双输出，RotatingFileHandler 自动轮转
- 查看日志：`关于 → 查看日志` 弹窗，支持刷新

### 修改
- `ui_*.py` → `*_ui.py` 命名规范
- 编译器从自实现改为 `pyside6-uic`
- 日志目录从 `~/.reliability-tool/logs/` 改为 `./logs/`
- 日志面板从主界面移除，改为菜单弹窗
- 配置按钮改为打开 ConfigDialog

### 技术债务
- `_load_config()` / `_collect_config()` 待实现具体控件绑定
- 保存/加载配置菜单待实现

---

## [0.1.0] — 2026-07-08

### 新增
- 项目初始化，PySide6 框架搭建
- mainWindow：QTabWidget + 菜单栏（文件/编辑/关于）
- FTDataAnalysisPage：T0/TX 文件选择、功能区、结果显示
- 控件重命名脚本：`pushButton` → `btnAddT0File` 等
- 自定义 .ui → .py 编译器（后替换为 pyside6-uic）
