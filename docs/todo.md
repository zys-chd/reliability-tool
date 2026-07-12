# 待办与开发规划

## 近期（当前迭代）

- [x] **ConfigDialog 控件绑定** — 分组 tab 已对接 Designer UI
- [x] **分组功能** — 文件名分组 + SN 分组（含粘贴、去重、恢复）
- [x] **文件路径占位符** — `%DIR_TO_T0_FILE%` / `%DIR_TO_TX_FILE%` 自动解析
- [ ] **数据合并核心** — `core/data_merge.py`
  - [x] 文件内 PASS 优先去重
  - [x] 多条 FAIL 冲突收集
  - [ ] ConflictDialog 弹窗（用户选择保留行）
  - [ ] 跨文件横向拼接（同 group + 同 PART_ID）
  - [ ] 合并结果写入 CSV/Excel

## 中期

- [ ] **T0/TX 文件读取与解析**
  - [ ] CSV 解析
  - [ ] Excel (xlsx/xls) 解析
  - [ ] 数据预览表格
- [ ] **功能按钮实现**
  - [ ] 绘制 Excel — 模板文件 + 数据 → 输出 Excel
  - [ ] 合并文件 — T0 + TX 数据合并
  - [ ] 对比文件 — 两组数据对比
  - [ ] 绘图 — webResult 显示图表（matplotlib/plotly）
  - [ ] 保存图片
- [ ] **分组配置逻辑**
  - [ ] 按文件名分组
  - [ ] 按 SN 分组
  - [ ] 二者结合

## 远期

- [ ] 多语言支持（i18n）
- [ ] 插件系统
- [ ] 批量处理
- [ ] 报告生成（PDF/HTML）
- [ ] 测试覆盖

## 已知问题

- [ ] `QWebEngineView` 在某些环境可能缺少 webengine 后端
