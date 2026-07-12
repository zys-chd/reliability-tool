# 可靠性数据分析工具

## 项目简介

基于 PySide6 的桌面应用，用于 FT（可靠性）数据分析、处理与可视化。

## 技术栈

| 组件 | 版本 |
|------|------|
| Python | 3.14 |
| PySide6 | 6.11.1 |
| Qt6 uic | 6.11.1 |

## 项目结构

```
├── app.py                          # 启动入口
├── scripts/
│   └── process_ui.py               # .ui → _ui.py 编译器
├── ui/
│   ├── *.ui                        # Qt Designer 设计文件
│   └── gen/
│       ├── *_ui.py                 # pyside6-uic 自动生成，不动
│       ├── *.py                    # 业务代码：继承 Ui_*，加信号+功能
│       ├── config_manager.py       # TOML 配置管理器
│       ├── config_schemas.py       # 配置项 schema 定义
│       └── logger.py               # 日志模块（文件 + 控制台 + UI）
├── config/
│   └── *.toml                      # 用户配置（运行时自动创建）
├── logs/
│   └── *.log                       # 运行日志
└── docs/
    ├── index.md                    # 本文件
    ├── changelog.md                # 变更日志
    ├── todo.md                     # 待办与规划
    └── architecture.md             # 架构说明
```

## 启动方式

```bash
cd /home/zys/Projects/reliability-tool
python app.py
```

## 开发流程

1. Qt Designer 编辑 `.ui` 文件
2. 重命名控件为有意义的名称
3. `python scripts/process_ui.py` 编译
4. 在 `ui/gen/` 下写同名 wrapper 类（不含 `_ui` 后缀）
5. 在 `mainWindow.py` 的 `_init_tabs()` 中注册新页面
