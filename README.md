# Reliability Tool — 半导体可靠性数据分析工具

基于 PySide6 的半导体可靠性数据分析桌面应用，支持 FT（Final Test）和 TDDB（Time-Dependent Dielectric Breakdown）数据分析。

## 功能

### FT 数据分析
- CSV/TXT/DAT 格式文件解析（自动格式检测）
- 三层缓存系统（内存 LRU + SQLite + Pickle）
- T0/TX 数据合并与冲突处理
- 单位换算（自动识别单位前缀）
- CDF/Weibull 分布绘图（Plotly + QWebEngineView）
- Excel 导出（openpyxl，含图表）

### TDDB 分析
- Weibull 分布拟合（含统一斜率）
- 加速模型：E 模型、1/E 模型、V 模型、√E 模型
- E-Arrhenius 温度加速模型
- 面积缩放（Poisson 统计）
- 置信区间计算
- 寿命预测与失效率计算
- β 诊断工具

### 监控数据提取（新增）
- 机台监控结果导入（xlsx/csv）
- 列映射配置（Sheet/首行/时间/电压/电流/温度）
- 失效点检测（电流降零、倍率超限、超电流上限）
- QBD 计算（梯形积分）
- 多 TBD 候选支持（ComboBox 选择 + 自定义输入）
- 起始零值/连续零值/超限值去重过滤
- 监控曲线绘制（对数/线性坐标切换，图例切换）

## 环境要求

- Python 3.12+
- PySide6 6.9+
- 依赖详见 `requirements.txt`

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python app.py
```

## 项目结构

```
reliability-tool/
├── app.py                 # 启动入口
├── core/                  # 核心业务逻辑
│   ├── FT_file_parser.py  # FT 文件解析
│   ├── ft_cache.py        # 三层缓存系统
│   ├── ploting.py         # 绘图引擎
│   └── tddb/              # TDDB 分析子模块
│       ├── models.py      # 加速模型
│       ├── weibull_fitter.py
│       ├── monitor_import.py
│       └── ...
├── ui/                    # 用户界面
│   ├── *.ui               # Qt Designer 源文件
│   └── gen/               # 生成的 Python 代码
├── config/                # 配置文件
├── tests/                 # 测试（pytest）
└── packaging/             # 构建脚本
```

## 构建

```bash
# Linux
./packaging/build.sh

# Windows
./packaging/build.ps1
```

## License

Apache 2.0
