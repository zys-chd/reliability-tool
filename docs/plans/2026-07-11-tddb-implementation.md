# TDDB 分析模块实现计划

> **目标：** 实现完整的 TDDB 数据分析功能，从 Excel 数据读取 → Weibull 拟合 → 寿命/失效率计算

**架构：**
- `core/tddb/` — 纯计算逻辑（numpy/scipy 实现，无 PySide6 依赖）
- `tests/` — 所有核心模块的单元测试（pytest）
- `ui/gen/tddb_tool.py` — UI wrapper，连接 Designer 布局与核心逻辑

**测试策略：**
- 每个 core 模块先写 test，TDD 逐步骤执行
- 测试数据用 Python 生成（不依赖外部 Excel 文件），只在集成测试中使用 Excel

**Tech Stack:** numpy, scipy (stats), pandas, plotly, pytest

---

### Phase 1: 测试数据 + Weibull 拟合核心

#### Task 1: 创建测试 TDDB 数据集生成器

**Objective:** 生产测试用 TDDB Excel 文件，包含多个电压/温度/面积条件、Weibull 分布的 TBD/QBD 值，用于后续所有测试

**Files:**
- Create: `core/tddb/test_data.py`
- Create: `tests/test_tddb_test_data.py`

**核心思路：**
- `make_tddb_dataset()` — 纯内存生成 DataFrame，不依赖文件
- `make_tddb_excel()` — 写入 Excel 供集成测试
- 参数可控：电压数、每组样本数、β、η、Ea、面积、group
- 多 group 模式下 TBD 用不同 β/η 生成

#### Task 2: Weibull 拟合核心 (weibull_fitter.py)

**Objective:** 对给定 TBD 数据做 Weibull 分布拟合，支持独立斜率与统一斜率模式

**Files:**
- Create: `core/tddb/weibull_fitter.py`
- Create: `tests/test_weibull_fitter.py`

**功能：**
- `fit_weibull(data)` — 最小二乘法拟合 ln(-ln(1-F)) vs ln(t)，返回 β, η, R²_raw, R²_log
- `fit_unified_slope(groups_data)` — 全局优化统一 β
- `compute_weibull_probabilities(data)` — 计算 Benard 中位秩

#### Task 3: E/1E/V 模型拟合 (models.py)

**Objective:** 电压加速模型拟合 + E-Arrhenius 二维全局拟合

**Files:**
- Create: `core/tddb/models.py`
- Create: `tests/test_models.py`

**功能：**
- `fit_e_model(voltages, etas, tox)` — t = A·exp(-γ·Eox)
- `fit_1e_model(voltages, etas, tox)` — t = τ₀·exp(G/Eox)
- `fit_v_model(voltages, etas)` — t = A·exp(-βv·Vg)
- `fit_e_arrhenius(voltages, temps, etas, tox)` — 全局拟合 γ + Ea
- `predict_lifetime(model, params, v_op, t_op, tox)` — 外推工作电压下特征寿命
- `predict_failure_rate(eta, beta, t_op)` — 计算指定时间累计失效率

#### Task 4: 面积缩放 + 置信区间 (area_scaling.py + confidence.py)

**Files:**
- Create: `core/tddb/area_scaling.py`
- Create: `core/tddb/confidence.py`
- Create: `tests/test_area_scaling.py`
- Create: `tests/test_confidence.py`

**area_scaling.py:**
- `scale_eta(eta_ref, area_ref, area_target, beta)` — Poisson 面积缩放

**confidence.py:**
- `weibull_ci(beta, eta, n, alpha)` — Fisher matrix 的 β/η 置信区间
- `lifetime_ci(eta, beta, failure_fraction, n, alpha)` — 指定失效率寿命的置信区间

#### Task 5: β 诊断图生成 (beta_diagnostics.py)

**Files:**
- Create: `core/tddb/beta_diagnostics.py`
- Create: `tests/test_beta_diagnostics.py`

**功能：**
- `make_beta_vs_vgs_plot(beta_data)` — β vs Vgs 的 plotly figure
- `make_beta_vs_temp_plot(beta_data)` — β vs Temperature
- `make_beta_vs_area_plot(beta_data)` — β vs Area

---

### Phase 2: UI Wrapper

#### Task 6: tddb_tool.py — 主 wrapper 类

**Files:**
- Create: `ui/gen/tddb_tool.py`
- Create: `tests/test_tddb_tool.py`（可选，UI 集成测试）

**功能：**
- `TDDBPage(QWidget)` — 继承 Ui_Form，连接所有按钮信号
- `_on_select_file()` — 文件对话框
- `_on_export_template()` — 导出模板
- `_on_weibull_fit()` — 读取数据、拟合、绘图
- `_on_add_custom_plot()` — 打开自定义对话框
- `_on_beta_diagnostic()` — 切换到 β 诊断图
- `_on_calc()` — 寿命/失效率计算
- `_on_simulate_oxide()` — 栅氧加厚弹窗
- `_on_raw_params_changed()` — 参数编辑联动

#### Task 7: 自定义图对话框 wrapper

**Files:**
- Create: `ui/gen/tddb_custom_draw.py`

#### Task 8: 集成到 mainWindow

**Files:**
- Modify: `ui/gen/mainWindow.py`
