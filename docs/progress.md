# 进度记录

> 按时间顺序记录开发过程中的关键决策、问题与解决方案。

## 2026-07-08

### 项目初始化
- 创建项目框架：mainWindow（QTabWidget）+ FTDataAnalysisPage
- 控件重命名：写 `process_ui.py` 批量重命名 .ui 控件
- 自研 .ui → .py 编译器（后因 `pyside6-uic` 可用而废弃）

### 命名规范调整
- `ui_*.py` → `*_ui.py`，更直观
- 编译器切换为标准 `pyside6-uic`

### 日志系统
- 初版用 `QDockWidget` 在主界面底部显示日志
- 后改为 `关于 → 查看日志` 弹窗，界面更清爽
- 日志目录从 `~/.reliability-tool/logs/` 改为 `./logs/`

### 配置管理器
- **三次迭代**：单文件→三文件→单文件
- 最终方案：一个 `FTDataAnalisys.toml` + 多 section
- 每个 section 包含三个 tab 的全部 12 个配置项
- `[meta]` 记录活跃 section，重启自动恢复

### 架构决策记录（ADR）

| 决策 | 方案 | 理由 |
|------|------|------|
| UI 绑定方式 | 多重继承（class Page(QWidget, Ui_Page)） | 标准 PySide6 模式，直接访问控件 |
| 编译器 | pyside6-uic | 官方工具，无需维护自定义编译器 |
| 配置格式 | TOML | Python 3.11+ 标准库 tomllib 支持 |
| 配置粒度 | 一个文件多 section | 逻辑内聚，切换 section 一次同步所有 tab |
| 日志存储 | 文件 + 控制台 + UI 弹窗 | 开发调试方便，用户可查看历史 |
