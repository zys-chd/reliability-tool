#!/usr/bin/env python3
"""
配置对话框 - 对应 FTDataAnalisysConfig_ui.py
对接 ConfigManager，三个 tab：分组配置 / 模板配置 / 绘图配置
分组 tab 的 UI 由 Qt Designer 设计，这里只连接信号和逻辑。
"""

import logging
import os
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFileDialog, QGridLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidgetItem,
    QVBoxLayout, QSpacerItem, QSizePolicy, QSpinBox
)

from .FTDataAnalisysConfig_ui import Ui_ConfigDialog
from .config_manager import ConfigManager


class ConfigDialog(QDialog, Ui_ConfigDialog):
    """配置对话框"""

    def __init__(self, config_manager, tab_name: str,
                 logger: logging.Logger | None = None,
                 parent=None, tx_filenames: list[str] | None = None,
                 t0_columns: list[str] | None = None,
                 tx_columns: list[str] | None = None):
        super().__init__(parent)
        self.setupUi(self)

        self._cm = config_manager
        self._tab_name = tab_name
        self._tx_filenames = tx_filenames or []
        self._t0_columns = t0_columns or []
        self._tx_columns = tx_columns or []
        self.logger = logger or logging.getLogger("ConfigDialog")

        self._init_group_tab()
        self._init_template_tab()
        self._init_calc_tab()
        self._init_ut_tab()
        self._init_signature_tab()
        self._connect_signals()
        self._load_sections()
        self._load_config()
        # 显示当前配置文件路径
        self.lblCurrentConfigFile.setText(f"当前配置文件：{self._cm.filepath}")
        self.logger.info(f"ConfigDialog 打开: {tab_name}")

    # ═══════════════════════════════════════════════════════════
    #  模板 tab - 测试项选择
    # ═══════════════════════════════════════════════════════════

    def _init_template_tab(self):
        from .test_item_selector import TestItemSelector
        self._item_selector = TestItemSelector(
            self._t0_columns, self._tx_columns, self.tabTestItems)

        # 隐藏 Designer 默认的 splitter/按钮，用 TestItemSelector 替代
        self.splitterTestItems.setVisible(False)
        self.frameMoveButtons.setVisible(False)

        # 放入 tabTestItems 的 layout 中（filter 后面），撑满剩余空间
        layout = self.tabTestItems.layout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        # QGridLayout，在第1行第0列放入，撑满
        layout.addWidget(self._item_selector, 1, 0)
        layout.setRowStretch(1, 1)

        # 连接筛选信号
        self.editInclude.textChanged.connect(self._on_filter_changed)
        self.editExclude.textChanged.connect(self._on_filter_changed)

        # ── 缓存地址 ──
        from core.ft_cache import _resolve_cache_path, ft_cache, _resolve_program_dir
        self.editCachePath.setText(self._cm.get("cache_path", "%PROGRAM_DIR%/cache"))

        def _on_open_cache():
            path = _resolve_cache_path(self.editCachePath.text())
            import subprocess, sys
            if sys.platform == "win32":
                os.startfile(str(path))
            else:
                subprocess.run(["xdg-open", str(path)], check=False)

        def _on_select_cache():
            from PySide6.QtWidgets import QFileDialog
            current = _resolve_cache_path(self.editCachePath.text())
            d = QFileDialog.getExistingDirectory(self, "选择缓存目录", str(current))
            if d:
                self.editCachePath.setText(d)

        self.btnOpenCachePath.clicked.connect(_on_open_cache)
        self.btnSelectCachePath.clicked.connect(_on_select_cache)
        self.editCachePath.textChanged.connect(self._on_cache_path_changed)

    def _on_cache_path_changed(self, text: str):
        """缓存地址变更时更新配置。"""
        from core.ft_cache import _resolve_cache_path, ft_cache
        resolved = str(_resolve_cache_path(text))
        ft_cache.set_cache_dir(resolved)
        self._cm.set("cache_path", text)

    def _on_filter_changed(self):
        inc = self.editInclude.text().strip()
        exc = self.editExclude.text().strip()
        self._item_selector.set_filter(inc, exc)

    # ═══════════════════════════════════════════════════════════
    #  数据计算 / limit 配置 tab
    # ═══════════════════════════════════════════════════════════

    def _init_calc_tab(self):
        """初始化表格 + 筛选 + 批量应用"""
        self._setup_calc_table()
        self._connect_calc_signals()
        self._last_calc_include = ""
        self._last_calc_exclude = ""
        self._saved_calc_config = {}

        # 设置预设公式（统一 cmbCalcPreset + FORMULA_PRESETS）
        self._init_calc_presets()

        # 连接管理公式按钮
        self.btnFormulaManage.clicked.connect(self._on_manage_formulas)

    COL_FORMULA = 2
    COL_LIMIT_DIR = 4
    FORMULA_PRESETS = [
        "abs(T0/TX)",
        "abs(1/((TX/T0)-1))",
    ]

    _custom_formulas: set = set()

    def _init_calc_presets(self):
        """统一 cmbCalcPreset 和 FORMULA_PRESETS"""
        self.cmbCalcPreset.blockSignals(True)
        self.cmbCalcPreset.clear()
        for f in self.FORMULA_PRESETS:
            self.cmbCalcPreset.addItem(f)
        self.cmbCalcPreset.addItem("自定义")
        self.cmbCalcPreset.blockSignals(False)
        self.cmbCalcPreset.currentTextChanged.connect(self._on_cmb_preset_changed)

    def _on_cmb_preset_changed(self, text: str):
        """预设 combo 变更 — 自定义由管理公式按钮处理"""
        pass

    def _on_manage_formulas(self):
        """管理公式对话框：显示所有公式（预设+自定义），支持删除和新增"""
        from PySide6.QtWidgets import (QDialog as QD, QVBoxLayout as QVL,
            QHBoxLayout as QHL, QListWidget, QPushButton, QInputDialog, QMessageBox)

        dlg = QD(self)
        dlg.setWindowTitle("管理公式")
        dlg.resize(400, 350)
        layout = QVL(dlg)

        lst = QListWidget()
        # 所有公式：预设 + 自定义
        all_formulas = list(self.FORMULA_PRESETS) + sorted(self._custom_formulas)
        for f in all_formulas:
            lst.addItem(f)
        layout.addWidget(lst)

        btn_row = QHL()
        btn_add = QPushButton("新增")
        btn_del = QPushButton("删除选中")
        btn_close = QPushButton("关闭")
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_del)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        def on_add():
            text, ok = QInputDialog.getText(dlg, "新增公式", "输入公式：")
            if ok and text.strip():
                formula = text.strip()
                if formula not in self.FORMULA_PRESETS:
                    self._custom_formulas.add(formula)
                    self._add_formula_to_all_combos(formula)
                # 列表中检查重复
                items = [lst.item(i).text() for i in range(lst.count())]
                if formula not in items:
                    lst.addItem(formula)
                else:
                    QMessageBox.information(dlg, "提示", "该公式已存在")

        def on_del():
            item = lst.currentItem()
            if not item:
                QMessageBox.warning(dlg, "提示", "请先选择要删除的公式")
                return
            formula = item.text()
            if formula in self.FORMULA_PRESETS:
                QMessageBox.warning(dlg, "提示", "预设公式不能删除")
                return
            self._custom_formulas.discard(formula)
            lst.takeItem(lst.row(item))

        btn_add.clicked.connect(on_add)
        btn_del.clicked.connect(on_del)
        btn_close.clicked.connect(dlg.accept)
        dlg.exec()

    def _setup_calc_table(self):
        tbl = self.tblCalcConfig
        headers = ["全选", "测试项", "shift公式", "shift limit",
                   "limit方向", "重命名为", "重命名id后缀"]
        tbl.setColumnCount(len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.setAlternatingRowColors(True)
        tbl.verticalHeader().setVisible(False)
        tbl.horizontalHeader().setStretchLastSection(True)

        # 点击表头「全选」列 → 切换所有 checkbox
        header = tbl.horizontalHeader()
        header.sectionClicked.connect(self._on_header_clicked)

    def _on_header_clicked(self, col: int):
        """点击表头列 — 仅第0列(全选)触发 toggle"""
        if col != 0:
            return
        # 统计当前已勾选数量
        checked_count = 0
        total_visible = 0
        for row in range(self.tblCalcConfig.rowCount()):
            if self.tblCalcConfig.isRowHidden(row):
                continue
            total_visible += 1
            cb = self.tblCalcConfig.cellWidget(row, 0)
            if cb and cb.isChecked():
                checked_count += 1
        # 如果全部已勾选 → 全部取消；否则全部勾选
        new_state = checked_count < total_visible
        for row in range(self.tblCalcConfig.rowCount()):
            if self.tblCalcConfig.isRowHidden(row):
                continue
            cb = self.tblCalcConfig.cellWidget(row, 0)
            if cb:
                cb.setChecked(new_state)

    def _populate_calc_table(self, test_items: list[str]):
        """用测试项填充表格"""
        self._calc_data = {}  # {item_name: row_data}
        tbl = self.tblCalcConfig
        tbl.setRowCount(0)
        for item in test_items:
            row = tbl.rowCount()
            tbl.insertRow(row)

            # 全选 checkbox
            cb = QCheckBox()
            tbl.setCellWidget(row, 0, cb)

            # 测试项名（只读）
            name_item = QTableWidgetItem(item)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            tbl.setItem(row, 1, name_item)

            # shift公式 — combo，加入已有自定义公式
            fm_cb = QComboBox()
            preset_list = list(self.FORMULA_PRESETS)
            for cf in self._custom_formulas:
                if cf not in preset_list:
                    preset_list.append(cf)
            saved = self._calc_data.get(item, {}).get("formula", "")
            if saved and saved not in preset_list:
                preset_list.append(saved)
            for f in preset_list:
                fm_cb.addItem(f)
            fm_cb.addItem("自定义...")
            if saved in preset_list:
                fm_cb.setCurrentText(saved)
            elif preset_list:
                fm_cb.setCurrentText(preset_list[0])
            fm_cb.currentTextChanged.connect(
                lambda txt, r=row: self._on_formula_changed(r, txt))
            tbl.setCellWidget(row, self.COL_FORMULA, fm_cb)

            # shift limit
            limit_item = QTableWidgetItem("")
            tbl.setItem(row, 3, limit_item)

            # limit方向 — combo
            dir_cb = QComboBox()
            dir_cb.addItems(["lower", "upper"])
            tbl.setCellWidget(row, self.COL_LIMIT_DIR, dir_cb)

            # 重命名为
            rename_item = QTableWidgetItem("")
            tbl.setItem(row, 5, rename_item)

            # 重命名id后缀
            suffix_item = QTableWidgetItem("")
            tbl.setItem(row, 6, suffix_item)

            # 背景色
            self._apply_row_color(row, item)

            # 存储行引用
            self._calc_data[item] = {
                "row": row, "formula": "", "limit": "", "direction": "lower",
                "rename": "", "suffix": "",
            }

        tbl.resizeColumnsToContents()

    def _apply_row_color(self, row: int, item_name: str):
        """根据 T0/TX 出现情况设置行背景色"""
        if not hasattr(self, "_item_selector"):
            return
        sel = self._item_selector
        in_t0 = item_name in sel._t0_set
        in_tx = item_name in sel._tx_set
        from PySide6.QtGui import QColor, QBrush
        if in_t0 and in_tx:
            color = QColor("#90ee90")  # 绿
        elif in_t0:
            color = QColor("#f5deb3")  # 浅棕
        else:
            color = QColor("#add8e6")  # 浅蓝
        for c in range(self.tblCalcConfig.columnCount()):
            item = self.tblCalcConfig.item(row, c)
            if item:
                item.setBackground(QBrush(color))
                item.setForeground(QBrush(QColor("#000000")))

    def _on_formula_changed(self, row: int, text: str):
        """公式 combo 变化"""
        if text == "自定义...":
            current = self._get_cell_text(row, 3)
            from .formula_dialog import FormulaDialog
            dlg = FormulaDialog(current, self)
            if dlg.exec() == FormulaDialog.DialogCode.Accepted:
                formula = dlg.get_formula()
                if formula:
                    self._custom_formulas.add(formula)
                    self._add_formula_to_all_combos(formula)
                    cmb = self.tblCalcConfig.cellWidget(row, self.COL_FORMULA)
                    if cmb:
                        cmb.setCurrentText(formula)
            else:
                cmb = self.tblCalcConfig.cellWidget(row, self.COL_FORMULA)
                if cmb:
                    cmb.setCurrentIndex(0)
        elif text and text not in self.FORMULA_PRESETS and text not in self._custom_formulas:
            # 非预设公式 → 也加到自定义集合和 cmbCalcPreset
            self._custom_formulas.add(text)
            self._add_formula_to_all_combos(text)

    def _add_formula_to_all_combos(self, formula: str):
        """将公式添加到 cmbCalcPreset 和所有行的 combo 中"""
        # cmbCalcPreset
        idx = self.cmbCalcPreset.findText(formula)
        if idx < 0:
            # 插入到「自定义」之前
            cc = self.cmbCalcPreset.count()
            # 最后一项是「自定义」
            self.cmbCalcPreset.insertItem(cc - 1, formula)

    def _get_cell_text(self, row: int, col: int) -> str:
        item = self.tblCalcConfig.item(row, col)
        return item.text() if item else ""

    def _connect_calc_signals(self):
        """连接计算 tab 的信号"""
        self.btnCalcApply.clicked.connect(self._on_calc_apply)
        self.editCalcInclude.textChanged.connect(self._on_calc_filter)
        self.editCalcExclude.textChanged.connect(self._on_calc_filter)

    def _on_calc_filter(self):
        """根据包含/排除筛选表格行"""
        inc = self.editCalcInclude.text().strip()
        exc = self.editCalcExclude.text().strip()
        self._last_calc_include = inc
        self._last_calc_exclude = exc
        incl_list = [s.strip() for s in inc.split(";") if s.strip()]
        excl_list = [s.strip() for s in exc.split(";") if s.strip()]
        for row in range(self.tblCalcConfig.rowCount()):
            item = self.tblCalcConfig.item(row, 1)
            if not item:
                continue
            name = item.text()
            visible = True
            if incl_list and not all(v.lower() in name.lower() for v in incl_list):
                visible = False
            if excl_list and any(v.lower() in name.lower() for v in excl_list):
                visible = False
            self.tblCalcConfig.setRowHidden(row, not visible)

    def _on_calc_apply(self):
        """批量应用：将当前批量设置写入所有**可见且勾选**的行"""
        try:
            # 公式来源：cmbCalcPreset（排除「自定义」）
            formula = self.cmbCalcPreset.currentText()
            if formula == "自定义":
                formula = ""
            limit_val = self.editCalcLimit.text().strip()
            direction = self.cmbCalcLimitDir.currentText()
            rename = self.editCalcRename.text().strip()
            suffix = self.editCalcRenameSuffix.text().strip()

            applied = 0
            for row in range(self.tblCalcConfig.rowCount()):
                if self.tblCalcConfig.isRowHidden(row):
                    continue
                cb = self.tblCalcConfig.cellWidget(row, 0)
                if not cb or not cb.isChecked():
                    continue
                applied += 1
                if formula:
                    cmb = self.tblCalcConfig.cellWidget(row, self.COL_FORMULA)
                    if cmb:
                        if formula not in [cmb.itemText(i) for i in range(cmb.count())]:
                            cmb.insertItem(cmb.count() - 1, formula)
                        cmb.setCurrentText(formula)
                if limit_val:
                    self.tblCalcConfig.item(row, 3).setText(limit_val)
                dir_cb = self.tblCalcConfig.cellWidget(row, self.COL_LIMIT_DIR)
                if dir_cb:
                    dir_cb.setCurrentText(direction)
                if rename:
                    self.tblCalcConfig.item(row, 5).setText(rename)
                if suffix:
                    self.tblCalcConfig.item(row, 6).setText(suffix)
            self.logger.info(f"批量应用：{applied} 行已更新")
            if applied == 0:
                QMessageBox.information(self, "提示", "请先勾选要应用的行（在「全选」列打勾）")
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.logger.error(f"批量应用失败:\n{tb}")
            QMessageBox.critical(self, "错误", f"批量应用失败：{e}")

    # ── Tab 切换 ──────────────────────────────────────────

    # ── 配置保存/加载 ──────────────────────────────────────────

    def _init_group_tab(self):
        """在 scrollAreaWidgetContents_5 中构建文件名分组网格"""
        if not self._tx_filenames:
            # 无 TX 文件时显示提示
            self._fg_files = []
            self._fg_elements = []
            self._fg_max_cols = 0
            self._fg_col_selectors = []
            self._fg_row_checks = []
            self._fg_row_results = []
            lbl = QLabel("请先在主界面添加 TX 文件后再进行文件名分组配置")
            lbl.setStyleSheet("color: #888; padding: 20px; font-size: 13px;")
            self.scrollFilenameContent.setLayout(QVBoxLayout())
            self.scrollFilenameContent.layout().addWidget(lbl)
            return

        # 解析文件名
        self._fg_files = sorted(set(self._tx_filenames))
        self._fg_elements = [Path(f).stem.split("_") for f in self._fg_files]
        self._fg_max_cols = max(len(p) for p in self._fg_elements) if self._fg_elements else 0
        if self._fg_max_cols == 0:
            return

        # 列全选按钮
        self._fg_col_selectors: list[QPushButton] = []
        # 每行元素按钮
        self._fg_row_checks: list[list[QPushButton | None]] = []
        # 每行结果编辑框
        self._fg_row_results: list[QLineEdit] = []

        content = self.scrollFilenameContent
        grid = QGridLayout(content)
        grid.setSpacing(2)
        grid.setContentsMargins(4, 4, 4, 4)

        # 第0行：列全选按钮
        for col in range(self._fg_max_cols):
            btn = QPushButton(f"元素 {col}")
            btn.setCheckable(True)
            btn.setChecked(False)
            btn.setFixedHeight(28)
            # btn.setStyleSheet(
            #     "QPushButton { background: #3a3a5a; color: #ccc; border: 1px solid #555; border-radius: 3px; padding: 2px 6px; }"
            #     "QPushButton:checked { background: #2a7a2a; color: #fff; }")
            btn.clicked.connect(lambda checked, c=col: self._fg_toggle_col(c, checked))
            grid.addWidget(btn, 0, col)
            self._fg_col_selectors.append(btn)
        grid.addWidget(QLabel("分组 key"), 0, self._fg_max_cols)

        # 数据行
        for row_idx, (fn, parts) in enumerate(zip(self._fg_files, self._fg_elements)):
            row_btns = []
            for col in range(self._fg_max_cols):
                if col < len(parts):
                    btn = QPushButton(parts[col])
                    btn.setCheckable(True)
                    btn.setChecked(False)
                    btn.setFixedHeight(28)
                    # btn.setStyleSheet(
                    #     "QPushButton { background: #3a3a5a; color: #ddd; border: 1px solid #555; border-radius: 3px; padding: 2px 6px; font-size: 11px; }"
                    #     "QPushButton:checked { background: #2a7a2a; color: #fff; }"
                    #     "QPushButton:hover { border-color: #888; }")
                    btn.clicked.connect(
                        lambda checked, r=row_idx, c=col: self._fg_toggle(r, c, checked))
                    grid.addWidget(btn, row_idx + 1, col)
                else:
                    placeholder = QLabel("—")
                    placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    placeholder.setFixedHeight(28)
                    placeholder.setStyleSheet("color: #555;")
                    grid.addWidget(placeholder, row_idx + 1, col)
                    btn = None
                row_btns.append(btn)
            self._fg_row_checks.append(row_btns)

            edit = QLineEdit()
            edit.setPlaceholderText("选择元素后自动生成，可前后追加自定义内容")
            edit.setFixedHeight(28)
            grid.addWidget(edit, row_idx + 1, self._fg_max_cols)
            self._fg_row_results.append(edit)
            self._fg_update_result(row_idx)

        grid.setColumnStretch(self._fg_max_cols, 1)
        grid.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding), len(self._fg_files)+1, 0)
        self._fg_update_col_states()

    def _fg_toggle_col(self, col: int, checked: bool):
        for row in self._fg_row_checks:
            if col < len(row) and row[col] is not None:
                row[col].setChecked(checked)
        self._fg_update_all_results()
        self._fg_update_col_states()

    def _fg_toggle(self, row: int, col: int, checked: bool):
        self._fg_update_result(row)
        self._fg_update_col_states()

    def _fg_update_result(self, row: int):
        parts = self._fg_elements[row]
        selected = []
        for col in range(min(len(parts), self._fg_max_cols)):
            btn = self._fg_row_checks[row][col]
            if btn and btn.isChecked():
                selected.append(parts[col])
        new_auto_key = "_".join(selected)

        edit = self._fg_row_results[row]
        current = edit.text()
        old_key = getattr(edit, '_fg_last_auto_key', None)

        if old_key and old_key in current:
            # 保留用户在自动 key 前后追加的内容
            idx = current.index(old_key)
            prefix = current[:idx]
            suffix = current[idx + len(old_key):]
            edit.setText(prefix + new_auto_key + suffix)
        else:
            # 首次或用户完全重写了 -> 直接设新值
            edit.setText(new_auto_key)

        edit._fg_last_auto_key = new_auto_key

    def _fg_update_all_results(self):
        for row in range(len(self._fg_files)):
            self._fg_update_result(row)

    def _fg_update_col_states(self):
        for col in range(self._fg_max_cols):
            checked = sum(1 for row in self._fg_row_checks
                          if col < len(row) and row[col] is not None and row[col].isChecked())
            total = sum(1 for row in self._fg_row_checks
                        if col < len(row) and row[col] is not None)
            btn = self._fg_col_selectors[col]
            if checked == total and total > 0:
                btn.setChecked(True)
                btn.setText(f"全选 {total}")
            elif checked == 0:
                btn.setChecked(False)
                btn.setText(f"全不选 {total}")
            else:
                btn.setChecked(False)
                btn.setText(f"☐ {checked}/{total}")

    def _fg_get_config(self) -> dict:
        if not self._fg_files:
            return {}
        return {fn: self._fg_row_results[r].text()
                for r, fn in enumerate(self._fg_files)}

    def _fg_set_config(self, data: dict):
        if not self._fg_files or not self._fg_row_results:
            return
        for r, fn in enumerate(self._fg_files):
            if fn in data:
                saved_text = data[fn]

                # 从文件名各段中找到在 saved_text 中连续出现的组合，
                # 逆序匹配最长的（避免短值误匹配）
                parts = self._fg_elements[r]
                best_auto = ""
                best_len = 0
                for start in range(len(parts)):
                    for end in range(start + 1, len(parts) + 1):
                        candidate = "_".join(parts[start:end])
                        if candidate in saved_text and len(candidate) > best_len:
                            best_auto = candidate
                            best_len = len(candidate)

                # 设置 checkbox：匹配到的段选中，其余不选
                if best_auto:
                    auto_parts = set(best_auto.split("_"))
                    for col in range(min(len(parts), self._fg_max_cols)):
                        btn = self._fg_row_checks[r][col]
                        if btn:
                            btn.setChecked(parts[col] in auto_parts)

                # 直接设 QLineEdit 文本，用保存的值完整保留
                edit = self._fg_row_results[r]
                edit.setText(saved_text)

                # 更新 _fg_last_auto_key 供后续 _fg_update_result 使用
                edit._fg_last_auto_key = best_auto

        self._fg_update_col_states()

    # ═══════════════════════════════════════════════════════════
    #  分组 tab - SN 分组
    # ═══════════════════════════════════════════════════════════

    def _init_sn_table(self):
        """初始化 SN 表格"""
        self.tblSN.setColumnCount(3)
        self.tblSN.setHorizontalHeaderLabels(["SN", "分组", "备注"])
        self.tblSN.horizontalHeader().setStretchLastSection(True)
        self.tblSN.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch)
        self.tblSN.setAlternatingRowColors(True)
        self.tblSN.verticalHeader().setVisible(False)

    def _sn_paste(self):
        from PySide6.QtWidgets import QApplication
        text = QApplication.clipboard().text()
        if not text.strip():
            QMessageBox.warning(self, "提示", "剪切板为空")
            return
        count = 0
        for line in text.strip().splitlines():
            parts = line.split("\t")
            sn = parts[0].strip() if parts else ""
            if not sn:
                continue
            grp = parts[1].strip() if len(parts) > 1 else ""
            note = parts[2].strip() if len(parts) > 2 else ""
            existing = False
            for r in range(self.tblSN.rowCount()):
                item = self.tblSN.item(r, 0)
                if item and item.text() == sn:
                    if grp:
                        self.tblSN.item(r, 1).setText(grp)
                    existing = True
                    break
            if not existing:
                row = self.tblSN.rowCount()
                self.tblSN.insertRow(row)
                self.tblSN.setItem(row, 0, QTableWidgetItem(sn))
                self.tblSN.setItem(row, 1, QTableWidgetItem(grp))
                self.tblSN.setItem(row, 2, QTableWidgetItem(note))
                count += 1
        self._sn_add_empty_row()
        if count:
            self.logger.info(f"粘贴了 {count} 行 SN 分组")

    def _sn_clear(self):
        ret = QMessageBox.question(self, "确认", "确定清空所有 SN 分组？")
        if ret != QMessageBox.StandardButton.Yes:
            return
        self.tblSN.setRowCount(0)
        self._sn_add_empty_row()

    def _sn_add_empty_row(self):
        row = self.tblSN.rowCount()
        self.tblSN.insertRow(row)
        self.tblSN.setItem(row, 0, QTableWidgetItem(""))
        self.tblSN.setItem(row, 1, QTableWidgetItem(""))
        self.tblSN.setItem(row, 2, QTableWidgetItem(""))

    def _sn_get_config(self) -> dict:
        result = {}
        for r in range(self.tblSN.rowCount()):
            s = self.tblSN.item(r, 0)
            g = self.tblSN.item(r, 1)
            if s and s.text().strip() and g and g.text().strip():
                result[s.text().strip()] = g.text().strip()
        return result

    def _sn_set_config(self, data: dict):
        self.tblSN.setRowCount(0)
        for sn, grp in data.items():
            row = self.tblSN.rowCount()
            self.tblSN.insertRow(row)
            self.tblSN.setItem(row, 0, QTableWidgetItem(sn))
            self.tblSN.setItem(row, 1, QTableWidgetItem(grp))
            self.tblSN.setItem(row, 2, QTableWidgetItem(""))
        self._sn_add_empty_row()

    # ═══════════════════════════════════════════════════════════
    #  FT 文件签名配置 tab
    # ═══════════════════════════════════════════════════════════

    def _init_signature_tab(self):
        """FT 文件签名配置 — 编辑 ft_data_config.toml 中的 [[signatures]]"""
        import tomllib

        self._sig_path = Path(__file__).parent.parent.parent / "config" / "ft_data_config.toml"
        self._sig_data: list[dict] = []
        self._sig_current_idx: int | None = None
        self._sig_fields = [
            ("format_id", "格式ID", str),
            ("display_name", "显示名称", str),
            ("header_identifiers", "表头标识符(逗号分隔)", list),
            ("part_id_offset", "PART_ID偏移", int),
            ("data_col_header_offset", "测试列名行偏移", int),
            ("unit_offset", "单位行偏移", int),
            ("lower_limit_offset", "下限行偏移", int),
            ("higher_limit_offset", "上限行偏移", int),
            ("data_start_offset", "数据起始偏移", int),
            ("pre_test_columns", "测试前列(逗号分隔)", list),
            ("delimiter", "分隔符", str),
            ("encoding", "编码", str),
            ("stop_at_blank_row", "遇空行停止", bool),
            ("skip_blank_rows", "跳过空行", bool),
            ("min_detected_cols", "最少检测列数(可选)", int),
        ]

        # ── 读取配置 ──
        self._load_signatures()

        # ── 构建UI ──
        from PySide6.QtWidgets import (
            QHBoxLayout, QSplitter, QTableWidget, QTableWidgetItem,
            QVBoxLayout, QPushButton, QGroupBox, QFormLayout,
            QLineEdit, QCheckBox, QSpinBox, QLabel, QMessageBox,
            QWidget, QHeaderView
        )

        self.tabSignature = QWidget()
        self.tabSignature.setObjectName("tabSignature")
        self.tabConfig.addTab(self.tabSignature, "文件签名")

        # 主布局：左侧列表 + 右侧编辑
        hl = QHBoxLayout(self.tabSignature)
        splitter = QSplitter(self.tabSignature)

        # ── 左侧：签名列表 ──
        left_w = QWidget()
        left_vl = QVBoxLayout(left_w)
        left_vl.setContentsMargins(0, 0, 0, 0)

        self._sig_table = QTableWidget()
        self._sig_table.setColumnCount(3)
        self._sig_table.setHorizontalHeaderLabels(["格式ID", "显示名称", "标识符"])
        self._sig_table.horizontalHeader().setStretchLastSection(True)
        self._sig_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._sig_table.setSelectionMode(QTableWidget.SingleSelection)
        self._sig_table.itemSelectionChanged.connect(self._on_sig_selected)

        left_vl.addWidget(self._sig_table)

        btn_hl = QHBoxLayout()
        self._btn_add_sig = QPushButton("添加")
        self._btn_del_sig = QPushButton("删除")
        self._btn_up_sig = QPushButton("上移")
        self._btn_down_sig = QPushButton("下移")
        btn_hl.addWidget(self._btn_add_sig)
        btn_hl.addWidget(self._btn_del_sig)
        btn_hl.addWidget(self._btn_up_sig)
        btn_hl.addWidget(self._btn_down_sig)
        btn_hl.addStretch()
        left_vl.addLayout(btn_hl)
        splitter.addWidget(left_w)

        # ── 右侧：编辑面板 ──
        right_w = QWidget()
        right_vl = QVBoxLayout(right_w)
        right_vl.setContentsMargins(0, 0, 0, 0)

        self._sig_grp = QGroupBox("签名详情")
        form = QFormLayout(self._sig_grp)
        self._sig_edits: dict[str, QLineEdit | QCheckBox | QSpinBox] = {}
        self._sig_meta_fields = {}

        for key, label, typ in self._sig_fields:
            if typ == str:
                w = QLineEdit()
                form.addRow(label + ":", w)
                self._sig_edits[key] = w
            elif typ == int:
                w = QSpinBox()
                w.setRange(-99, 99)
                form.addRow(label + ":", w)
                self._sig_edits[key] = w
            elif typ == bool:
                w = QCheckBox()
                form.addRow(label + ":", w)
                self._sig_edits[key] = w
            elif typ == list:
                w = QLineEdit()
                w.setPlaceholderText("用逗号分隔多个值")
                form.addRow(label + ":", w)
                self._sig_edits[key] = w
            self._sig_meta_fields[key] = label

        # skip_row_values 和 column_map 用简化的文本编辑
        self._edit_skip_row = QLineEdit()
        self._edit_skip_row.setPlaceholderText("例如: PART_ID=1,END 或 键1=值1,值2")
        form.addRow("跳过行值:", self._edit_skip_row)
        self._edit_col_map = QLineEdit()
        self._edit_col_map.setPlaceholderText("例如: SN=PART_ID 或 原名1=新名1")
        form.addRow("列名映射:", self._edit_col_map)

        self._sig_grp.setEnabled(False)
        right_vl.addWidget(self._sig_grp)

        self._btn_save_sig = QPushButton("保存修改")
        right_vl.addWidget(self._btn_save_sig)
        right_vl.addStretch()
        splitter.addWidget(right_w)

        splitter.setSizes([400, 600])
        hl.addWidget(splitter)

        # ── 信号连接 ──
        self._btn_add_sig.clicked.connect(self._on_sig_add)
        self._btn_del_sig.clicked.connect(self._on_sig_delete)
        self._btn_up_sig.clicked.connect(self._on_sig_move_up)
        self._btn_down_sig.clicked.connect(self._on_sig_move_down)
        self._btn_save_sig.clicked.connect(self._on_sig_save)

        # 填充表格
        self._refresh_sig_table()

    def _load_signatures(self):
        import tomllib
        try:
            raw = self._sig_path.read_bytes()
            cfg = tomllib.loads(raw.decode("utf-8"))
            self._sig_data = cfg.get("signatures", [])
        except Exception:
            self._sig_data = []

    def _refresh_sig_table(self):
        self._sig_table.setRowCount(len(self._sig_data))
        for i, sig in enumerate(self._sig_data):
            self._sig_table.setItem(i, 0, QTableWidgetItem(sig.get("format_id", "")))
            self._sig_table.setItem(i, 1, QTableWidgetItem(sig.get("display_name", "")))
            ids = sig.get("header_identifiers", [])
            self._sig_table.setItem(i, 2, QTableWidgetItem(", ".join(ids) if ids else ""))
        self._sig_table.resizeColumnsToContents()
        # 默认选中第一行
        if self._sig_data:
            self._sig_table.selectRow(0)

    def _sig_to_edit(self, sig: dict):
        """填充编辑面板"""
        for key, _, typ in self._sig_fields:
            val = sig.get(key)
            w = self._sig_edits[key]
            if val is None:
                if isinstance(w, QLineEdit):
                    w.clear()
                elif isinstance(w, QCheckBox):
                    w.setChecked(False)
                elif isinstance(w, QSpinBox):
                    w.setValue(0)
                continue
            if isinstance(w, QLineEdit):
                if typ == list:
                    w.setText(", ".join(str(v) for v in val))
                else:
                    w.setText(str(val))
            elif isinstance(w, QCheckBox):
                w.setChecked(bool(val))
            elif isinstance(w, QSpinBox):
                w.setValue(int(val))
        # skip_row_values
        sr = sig.get("skip_row_values", {})
        sr_parts = []
        for k, v in sr.items():
            vals = ", ".join(str(x) for x in (v if isinstance(v, list) else [v]))
            sr_parts.append(f"{k}={vals}")
        self._edit_skip_row.setText("; ".join(sr_parts))
        # column_map
        cm = sig.get("column_map", {})
        cm_parts = [f"{k}={v}" for k, v in cm.items()]
        self._edit_col_map.setText(", ".join(cm_parts))

    def _edit_to_sig(self) -> dict:
        """从编辑面板读取签名"""
        sig = {}
        for key, _, typ in self._sig_fields:
            w = self._sig_edits[key]
            if isinstance(w, QLineEdit):
                txt = w.text().strip()
                if typ == list:
                    sig[key] = [x.strip() for x in txt.split(",") if x.strip()]
                elif typ == str:
                    sig[key] = txt
            elif isinstance(w, QCheckBox):
                sig[key] = w.isChecked()
            elif isinstance(w, QSpinBox):
                sig[key] = w.value()
        # skip_row_values
        sr = {}
        sr_txt = self._edit_skip_row.text().strip()
        if sr_txt:
            for part in sr_txt.split(";"):
                part = part.strip()
                if "=" in part:
                    k, vs = part.split("=", 1)
                    vals = [x.strip() for x in vs.split(",") if x.strip()]
                    sr[k.strip()] = vals
        sig["skip_row_values"] = sr
        # column_map
        cm = {}
        cm_txt = self._edit_col_map.text().strip()
        if cm_txt:
            for part in cm_txt.split(","):
                part = part.strip()
                if "=" in part:
                    k, v = part.split("=", 1)
                    cm[k.strip()] = v.strip()
        sig["column_map"] = cm
        return sig

    def _on_sig_selected(self):
        rows = self._sig_table.selectedItems()
        if not rows:
            self._sig_grp.setEnabled(False)
            return
        idx = rows[0].row()
        if 0 <= idx < len(self._sig_data):
            self._sig_grp.setEnabled(True)
            self._sig_to_edit(self._sig_data[idx])
            self._sig_current_idx = idx

    def _on_sig_add(self):
        self._sig_data.append({
            "format_id": f"NEW_SIG_{len(self._sig_data)+1}",
            "display_name": "新签名",
            "header_identifiers": ["PART_ID", "SOFT_BIN"],
            "part_id_offset": 0,
            "data_col_header_offset": 0,
            "unit_offset": 1,
            "lower_limit_offset": 2,
            "higher_limit_offset": 3,
            "data_start_offset": 4,
            "pre_test_columns": ["SOFT_BIN"],
            "delimiter": ",",
            "encoding": "utf-8-sig",
            "stop_at_blank_row": True,
            "skip_blank_rows": True,
            "skip_row_values": {"PART_ID": ["1", "END"]},
            "column_map": {},
        })
        self._refresh_sig_table()
        self._sig_table.setCurrentCell(len(self._sig_data) - 1, 0)

    def _on_sig_delete(self):
        if self._sig_current_idx is None or self._sig_current_idx >= len(self._sig_data):
            return
        sig = self._sig_data[self._sig_current_idx]
        ret = QMessageBox.question(
            self, "删除签名", f"确定删除签名「{sig.get('format_id', '')}」？",
            QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            self._sig_data.pop(self._sig_current_idx)
            self._sig_current_idx = None
            self._sig_grp.setEnabled(False)
            self._refresh_sig_table()

    def _on_sig_move_up(self):
        if self._sig_current_idx is None or self._sig_current_idx <= 0:
            return
        i = self._sig_current_idx
        self._sig_data[i], self._sig_data[i-1] = self._sig_data[i-1], self._sig_data[i]
        self._sig_current_idx = i - 1
        self._refresh_sig_table()
        self._sig_table.setCurrentCell(self._sig_current_idx, 0)

    def _on_sig_move_down(self):
        if self._sig_current_idx is None or self._sig_current_idx >= len(self._sig_data) - 1:
            return
        i = self._sig_current_idx
        self._sig_data[i], self._sig_data[i+1] = self._sig_data[i+1], self._sig_data[i]
        self._sig_current_idx = i + 1
        self._refresh_sig_table()
        self._sig_table.setCurrentCell(self._sig_current_idx, 0)

    def _on_sig_save(self):
        if self._sig_current_idx is None or self._sig_current_idx >= len(self._sig_data):
            return
        self._sig_data[self._sig_current_idx] = self._edit_to_sig()
        # 写回 TOML
        self._write_signatures()
        self._refresh_sig_table()
        QMessageBox.information(self, "保存成功", "签名配置已保存到 ft_data_config.toml")

    def _write_signatures(self):
        """将 self._sig_data 写回 ft_data_config.toml，保留 meta_columns"""
        import tomllib
        # 读取原文件保留 meta_columns 等非 signatures 内容
        try:
            raw = self._sig_path.read_bytes()
            full = tomllib.loads(raw.decode("utf-8"))
        except Exception:
            full = {}
        # 更新 signatures
        full["signatures"] = self._sig_data
        # 序列化写回
        from .config_manager import _serialize_toml
        text = _serialize_toml(full)
        self._sig_path.write_text(text, encoding="utf-8")

    # ═══════════════════════════════════════════════════════════
    #  信号连接
    # ═══════════════════════════════════════════════════════════

    def _connect_signals(self):
        self.btnOK.clicked.connect(self._on_accept)
        self.btnCancel.clicked.connect(self.reject)
        self.btnAddConfig.clicked.connect(self._add_config)
        self.cmbConfig.currentTextChanged.connect(self._on_section_switch)

        # SN 分组（Designer 按钮）
        self.btnPasteSN.clicked.connect(self._sn_paste)
        self.btnClearSN.clicked.connect(self._sn_clear)

        self._init_sn_table()

        # 配置文件选择
        self.btnConfigFileSelect.clicked.connect(self._on_select_config_file)
        # 读取FT数据
        self.btnReadFTData.clicked.connect(self._on_read_ft_data)

        # hover 参数帮助
        self.btnHoverHelp.clicked.connect(self._on_hover_help)

        # UT 配置按钮
        self.btnUTPaste.clicked.connect(self._ut_paste)
        self.btnUTAddRow.clicked.connect(self._ut_add_row)
        self.btnUTDeleteRow.clicked.connect(self._ut_delete_row)
        self.btnUTClear.clicked.connect(self._ut_clear)

        # 自动范围：勾选时清空输入并禁用，取消时启用
        self.chkXAuto.toggled.connect(self._on_x_auto_toggled)
        self.chkYAuto.toggled.connect(self._on_y_auto_toggled)

    # ═══════════════════════════════════════════════════════════
    #  UT 配置 tab
    # ═══════════════════════════════════════════════════════════

    def _init_ut_tab(self):
        """初始化 UT 配置表格"""
        headers = ["测试机台", "原测试项", "input", "condition", "output", "输出测试项", "备注"]
        self.tblUTConfig.setColumnCount(len(headers))
        self.tblUTConfig.setHorizontalHeaderLabels(headers)
        self.tblUTConfig.setAlternatingRowColors(True)
        self.tblUTConfig.verticalHeader().setVisible(False)
        self.tblUTConfig.horizontalHeader().setStretchLastSection(True)

    def _ut_paste(self):
        """从剪切板读取数据，解析后填入表格"""
        from PySide6.QtWidgets import QApplication
        text = QApplication.clipboard().text()
        if not text.strip():
            QMessageBox.warning(self, "提示", "剪切板为空")
            return
        count = 0
        for line in text.strip().splitlines():
            parts = line.split("\t") if "\t" in line else line.split(",")
            parts = [p.strip() for p in parts]
            if not parts or not parts[0]:
                continue
            row = self.tblUTConfig.rowCount()
            self.tblUTConfig.insertRow(row)
            for col in range(min(len(parts), self.tblUTConfig.columnCount())):
                self.tblUTConfig.setItem(row, col, QTableWidgetItem(parts[col]))
            count += 1
        if count:
            self.logger.info(f"从剪切板粘贴了 {count} 行 UT 配置")

    def _ut_add_row(self):
        """添加一个空行"""
        row = self.tblUTConfig.rowCount()
        self.tblUTConfig.insertRow(row)
        for col in range(self.tblUTConfig.columnCount()):
            self.tblUTConfig.setItem(row, col, QTableWidgetItem(""))

    def _ut_delete_row(self):
        """删除选中的行（从下往上删，避免索引错乱）"""
        rows = set()
        for item in self.tblUTConfig.selectedItems():
            rows.add(item.row())
        if not rows:
            QMessageBox.warning(self, "提示", "请先选择要删除的行")
            return
        for r in sorted(rows, reverse=True):
            self.tblUTConfig.removeRow(r)
        self.logger.info(f"删除了 {len(rows)} 行 UT 配置")

    def _ut_clear(self):
        """清空所有行（带确认对话框）"""
        ret = QMessageBox.question(
            self, "确认", "确定清空所有 UT 配置行？")
        if ret != QMessageBox.StandardButton.Yes:
            return
        self.tblUTConfig.setRowCount(0)

    def _collect_ut_config(self) -> list[dict]:
        """收集 UT 配置表格数据"""
        headers = ["测试机台", "原测试项", "input", "condition", "output", "输出测试项", "备注"]
        result = []
        for r in range(self.tblUTConfig.rowCount()):
            row_data = {}
            has_data = False
            for c, h in enumerate(headers):
                item = self.tblUTConfig.item(r, c)
                val = item.text().strip() if item else ""
                if val:
                    has_data = True
                row_data[h] = val
            if has_data:
                result.append(row_data)
        return result

    def _load_ut_config(self, data: list[dict]):
        """加载 UT 配置数据到表格"""
        self.tblUTConfig.setRowCount(0)
        headers = ["测试机台", "原测试项", "input", "condition", "output", "输出测试项", "备注"]
        for row_data in data:
            row = self.tblUTConfig.rowCount()
            self.tblUTConfig.insertRow(row)
            for c, h in enumerate(headers):
                val = row_data.get(h, "")
                self.tblUTConfig.setItem(row, c, QTableWidgetItem(val))

    def _on_select_config_file(self):
        """选择新的配置文件（.toml）并加载到界面"""
        from pathlib import Path
        path, _ = QFileDialog.getOpenFileName(
            self, "选择配置文件", str(self._cm.filepath.parent),
            "TOML 文件 (*.toml)")
        if not path:
            return
        try:
            new_cm = ConfigManager(Path(path), self._cm.schema, self.logger)
            new_cm.load()
            # 替换当前 ConfigManager
            self._cm = new_cm
            self._load_sections()
            self._load_config()
            self.lblCurrentConfigFile.setText(f"当前配置文件：{path}")
            self.logger.info(f"切换配置文件: {path}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载配置文件失败：{e}")

    def _on_read_ft_data(self):
        """同步 calc 表和 item_selector 的已选项：删除多余、新增缺失、保留已有数据"""
        try:
            selected = self._item_selector.get_selected()
            selected_set = set(selected)

            # 收集当前表格中的数据
            current = {}
            for row in range(self.tblCalcConfig.rowCount()):
                item = self.tblCalcConfig.item(row, 1)
                if not item:
                    continue
                name = item.text()
                cb = self.tblCalcConfig.cellWidget(row, 0)
                cmb = self.tblCalcConfig.cellWidget(row, self.COL_FORMULA)
                dcb = self.tblCalcConfig.cellWidget(row, self.COL_LIMIT_DIR)
                current[name] = {
                    "checked": cb.isChecked() if cb else False,
                    "formula": cmb.currentText() if cmb else "",
                    "limit": self._get_cell_text(row, 3),
                    "direction": dcb.currentText() if dcb else "lower",
                    "rename": self._get_cell_text(row, 5),
                    "suffix": self._get_cell_text(row, 6),
                }

            current_set = set(current.keys())
            to_add = selected_set - current_set
            to_remove = current_set - selected_set

            if not to_add and not to_remove:
                self.logger.debug("刷新测试项条目: 无变化")
                return

            self.logger.info(f"刷新测试项条目: +{len(to_add)} / -{len(to_remove)}")

            # 删除不再选中的行（从后往前删，避免索引错乱）
            for row in range(self.tblCalcConfig.rowCount() - 1, -1, -1):
                item = self.tblCalcConfig.item(row, 1)
                if item and item.text() in to_remove:
                    self.tblCalcConfig.removeRow(row)

            # 新增选中但表格中没有的行
            for name in sorted(to_add):
                row = self.tblCalcConfig.rowCount()
                self.tblCalcConfig.insertRow(row)

                cb = QCheckBox()
                self.tblCalcConfig.setCellWidget(row, 0, cb)

                name_item = QTableWidgetItem(name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tblCalcConfig.setItem(row, 1, name_item)

                fm_cb = QComboBox()
                preset_list = list(self.FORMULA_PRESETS)
                for cf in self._custom_formulas:
                    if cf not in preset_list:
                        preset_list.append(cf)
                for f in preset_list:
                    fm_cb.addItem(f)
                fm_cb.addItem("自定义...")
                if preset_list:
                    fm_cb.setCurrentText(preset_list[0])
                fm_cb.currentTextChanged.connect(
                    lambda txt, r=row: self._on_formula_changed(r, txt))
                self.tblCalcConfig.setCellWidget(row, self.COL_FORMULA, fm_cb)

                limit_item = QTableWidgetItem("")
                self.tblCalcConfig.setItem(row, 3, limit_item)

                dir_cb = QComboBox()
                dir_cb.addItems(["lower", "upper"])
                self.tblCalcConfig.setCellWidget(row, self.COL_LIMIT_DIR, dir_cb)

                self.tblCalcConfig.setItem(row, 5, QTableWidgetItem(""))
                self.tblCalcConfig.setItem(row, 6, QTableWidgetItem(""))

                self._apply_row_color(row, name)

            self.tblCalcConfig.resizeColumnsToContents()
            self.logger.info(f"刷新测试项条目完成: {len(selected)} 项")
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.logger.error(f"刷新测试项条目失败:\n{tb}")
            QMessageBox.critical(self, "错误", f"刷新测试项条目失败：{e}")

    def _on_hover_help(self):
        """显示 hover 可用配置参数（可复制文本窗口）"""
        from PySide6.QtWidgets import QWidget, QTextEdit, QVBoxLayout
        w = QWidget(self, Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)
        w.setWindowTitle("可用配置参数")
        w.resize(420, 320)

        txt = QTextEdit(w)
        txt.setReadOnly(True)
        txt.setPlainText(
            "%{x}          — 当前点的 X 值\n"
            "%{y}          — 当前点的 Y 值\n"
            "%{text}       — 附加文本（如 PART_ID）\n"
            "%{customdata} — 自定义数据\n"
            "%{marker.size}  — 标记大小（如同组数量）\n"
            "%{marker.color} — 标记颜色\n\n"
            "示例：\n"
            "<b>PART_ID:</b> %{text}<br>"
            "<b>数量:</b> %{marker.size}"
        )

        layout = QVBoxLayout(w)
        layout.addWidget(txt)
        w.show()

    def _on_x_auto_toggled(self, checked: bool):
        """勾选 chkXAuto：清空 editXMin/editXMax 并禁用；取消时启用"""
        self.editXMin.clear()
        self.editXMax.clear()
        self.editXMin.setEnabled(not checked)
        self.editXMax.setEnabled(not checked)

    def _on_y_auto_toggled(self, checked: bool):
        """勾选 chkYAuto：清空 editYMin/editYMax 并禁用；取消时启用"""
        self.editYMin.clear()
        self.editYMax.clear()
        self.editYMin.setEnabled(not checked)
        self.editYMax.setEnabled(not checked)

    # ═══════════════════════════════════════════════════════════
    #  配置读写
    # ═══════════════════════════════════════════════════════════

    def _load_sections(self):
        self.cmbConfig.blockSignals(True)
        self.cmbConfig.clear()
        for sec in self._cm.sections:
            self.cmbConfig.addItem(sec)
        active = self._cm.active_section
        idx = self.cmbConfig.findText(active)
        if idx >= 0:
            self.cmbConfig.setCurrentIndex(idx)
        self.cmbConfig.blockSignals(False)
    def _load_config(self):
        """从 ConfigManager 加载到 UI 控件"""
        config = self._cm.active

        # 分组配置
        gt = config.get("group_type", "filename")
        self.rbByName.setChecked(gt == "filename")
        self.rbBySN.setChecked(gt == "SN")
        self.rbBoth.setChecked(gt == "both")
        self._fg_set_config(config.get("filename_rules", {}))
        self._sn_set_config(config.get("SN", {}))

        # 模板配置 - 测试项
        selected = config.get("selected_test_items", [])
        if hasattr(self, "_item_selector") and selected:
            self._item_selector.set_selected(selected)

        # 数据计算/limit 配置 — 从 item_selector 当前选中项填充
        self._saved_calc_config = config.get("calc_config", {})
        if hasattr(self, "_item_selector"):
            calc_items = self._item_selector.get_selected()
            if calc_items:
                self._populate_calc_table(calc_items)
                if self._saved_calc_config:
                    self._load_calc_config(self._saved_calc_config)

        # 绘图配置
        self._load_plot_config(config.get("plot_config", {}))

        # UT 配置
        ut_data = config.get("ut_config", [])
        self._load_ut_config(ut_data)

    def _load_plot_config(self, cfg: dict):
        """从配置加载绘图 tab 的控件值"""
        if not hasattr(self, 'cmbPlotType'):
            return
        # comboBox
        combo_map = {
            'cmbPlotType': 'plot_type', 'cmbGroupBy': 'group_by',
            'cmbYAxisData': 'y_mode', 'cmbTheme': 'theme',
            'cmbOutputFormat': 'output_format', 'cmbTickFormat': 'tick_format',
            'cmbXScale': 'x_scale', 'cmbYScale': 'y_scale',
        }
        for attr, key in combo_map.items():
            cb = getattr(self, attr, None)
            if cb and key in cfg:
                idx = cb.findText(str(cfg[key]))
                if idx >= 0:
                    cb.setCurrentIndex(idx)
        # checkBox
        chk_map = {
            'chkXAuto': 'x_auto', 'chkYAuto': 'y_auto',
            'chkDrawT0': 'draw_t0', 'chkDrawTx': 'draw_tx',
            'chkDrawShift': 'draw_shift', 'chkShowLimitLine': 'show_limit_line',
            'chkDrawOverLimit': 'draw_over_limit',
        }
        for attr, key in chk_map.items():
            cb = getattr(self, attr, None)
            if cb and key in cfg:
                cb.setChecked(bool(cfg[key]))
        # lineEdit (QLineEdit 用 setText)
        line_edit_map = {
            'editXMin': 'x_min', 'editXMax': 'x_max',
            'editYMin': 'y_min', 'editYMax': 'y_max',
            'editXLabel': 'x_label',
            'editSaveDir': 'save_dir',
        }
        for attr, key in line_edit_map.items():
            le = getattr(self, attr, None)
            if le and key in cfg:
                le.setText(str(cfg[key]))
        # QPlainTextEdit (用 setPlainText)
        pte_map = {
            'editHoverTemplate': 'hover_template',
        }
        for attr, key in pte_map.items():
            pte = getattr(self, attr, None)
            if pte and key in cfg:
                pte.setPlainText(str(cfg[key]))
        # spinBox
        spin_map = {
            'spnWidth': 'width', 'spnHeight': 'height',
            'spnPlotCols': 'cols', 'spnPlotRows': 'rows',
            'spnMarkerSize': 'marker_size', 'spnLineWidth': 'line_width',
            'spnLineframeWidth': 'lineframe_width',
            'spnMarkerOpacity': 'marker_opacity', 'spnLineOpacity': 'line_opacity',
            'spnTitleFontSize': 'title_font_size', 'spnLabelFontSize': 'label_font_size',
            'spnLegendFontSize': 'legend_font_size',            'spnHoverFontSize': 'hover_font_size',
            'spnTickDecimals': 'tick_decimals',
            'spnWebengineScale': 'webengine_scale',
        }
        for attr, key in spin_map.items():
            sp = getattr(self, attr, None)
            if sp and key in cfg:
                sp.setValue(int(cfg[key]))
        # radioButton
        if 't0_source' in cfg:
            if cfg['t0_source'] == 'raw':
                self.rdoDataRaw.setChecked(True)
            else:
                self.rdoDataMerged.setChecked(True)

    def _load_calc_config(self, config: dict):
        """从保存的配置恢复计算 tab 的表格数据"""
        items = config.get("items", [])
        formulas = config.get("formulas", {})  # {item: formula_str}
        limits = config.get("limits", {})
        directions = config.get("directions", {})
        renames = config.get("renames", {})
        suffixes = config.get("suffixes", {})

        for row in range(self.tblCalcConfig.rowCount()):
            item = self.tblCalcConfig.item(row, 1)
            if not item:
                continue
            name = item.text()
            if name in formulas:
                cmb = self.tblCalcConfig.cellWidget(row, self.COL_FORMULA)
                if cmb:
                    f = formulas[name]
                    if f not in self.FORMULA_PRESETS:
                        self._custom_formulas.add(f)
                        self._add_formula_to_all_combos(f)
                    if f not in [cmb.itemText(i) for i in range(cmb.count())]:
                        cmb.insertItem(cmb.count() - 1, f)
                    cmb.setCurrentText(f)
            if name in limits:
                self.tblCalcConfig.item(row, 3).setText(str(limits[name]))
            if name in directions:
                dcb = self.tblCalcConfig.cellWidget(row, self.COL_LIMIT_DIR)
                if dcb:
                    dcb.setCurrentText(directions[name])
            if name in renames:
                self.tblCalcConfig.item(row, 5).setText(renames[name])
            if name in suffixes:
                self.tblCalcConfig.item(row, 6).setText(suffixes[name])

    def _collect_calc_config(self) -> dict:
        """收集计算 tab 的数据"""
        items, formulas, limits, directions, renames, suffixes = [], {}, {}, {}, {}, {}
        for row in range(self.tblCalcConfig.rowCount()):
            item = self.tblCalcConfig.item(row, 1)
            if not item:
                continue
            name = item.text()
            items.append(name)
            cmb = self.tblCalcConfig.cellWidget(row, self.COL_FORMULA)
            if cmb and cmb.currentText() not in ("", "自定义..."):
                formulas[name] = cmb.currentText()
            limit_text = self._get_cell_text(row, 3)
            if limit_text:
                limits[name] = limit_text
            dcb = self.tblCalcConfig.cellWidget(row, self.COL_LIMIT_DIR)
            if dcb:
                directions[name] = dcb.currentText()
            rename_text = self._get_cell_text(row, 5)
            if rename_text:
                renames[name] = rename_text
            suffix_text = self._get_cell_text(row, 6)
            if suffix_text:
                suffixes[name] = suffix_text
        return {
            "items": items, "formulas": formulas, "limits": limits,
            "directions": directions, "renames": renames, "suffixes": suffixes,
        }

    def _collect_config(self):
        gt = "filename"
        if self.rbBySN.isChecked():
            gt = "SN"
        elif self.rbBoth.isChecked():
            gt = "both"
        self._cm.set("group_type", gt)
        self._cm.set("filename_rules", self._fg_get_config())
        self._cm.set("SN", self._sn_get_config())

        # 模板配置 - 测试项
        if hasattr(self, "_item_selector"):
            self._cm.set("selected_test_items",
                         self._item_selector.get_selected())

        # 数据计算/limit 配置
        if hasattr(self, "tblCalcConfig"):
            self._cm.set("calc_config", self._collect_calc_config())

        # UT 配置
        self._cm.set("ut_config", self._collect_ut_config())

        # 绘图配置
        self._cm.set("plot_config", self._collect_plot_config())

    def _collect_plot_config(self) -> dict:
        """从绘图 tab 收集配置"""
        cfg = {}
        if not hasattr(self, 'cmbPlotType'):
            return cfg
        cfg['plot_type'] = self.cmbPlotType.currentText()
        cfg['group_by'] = self.cmbGroupBy.currentText()
        cfg['y_mode'] = self.cmbYAxisData.currentText()
        cfg['theme'] = self.cmbTheme.currentText()
        cfg['output_format'] = self.cmbOutputFormat.currentText()
        cfg['tick_format'] = self.cmbTickFormat.currentText()
        cfg['x_scale'] = self.cmbXScale.currentText()
        cfg['y_scale'] = self.cmbYScale.currentText()
        # checkBox
        cfg['x_auto'] = self.chkXAuto.isChecked()
        cfg['y_auto'] = self.chkYAuto.isChecked()
        cfg['draw_t0'] = self.chkDrawT0.isChecked()
        cfg['draw_tx'] = self.chkDrawTx.isChecked()
        cfg['draw_shift'] = self.chkDrawShift.isChecked()
        cfg['show_limit_line'] = self.chkShowLimitLine.isChecked()
        cfg['draw_over_limit'] = self.chkDrawOverLimit.isChecked()
        # lineEdit
        cfg['x_min'] = self.editXMin.text()
        cfg['x_max'] = self.editXMax.text()
        cfg['y_min'] = self.editYMin.text()
        cfg['y_max'] = self.editYMax.text()
        cfg['x_label'] = self.editXLabel.text()
        cfg['hover_template'] = self.editHoverTemplate.toPlainText() if hasattr(self.editHoverTemplate, 'toPlainText') else self.editHoverTemplate.text()
        cfg['save_dir'] = self.editSaveDir.text()
        # spinBox
        cfg['width'] = self.spnWidth.value()
        cfg['height'] = self.spnHeight.value()
        cfg['cols'] = self.spnPlotCols.value()
        cfg['rows'] = self.spnPlotRows.value()
        cfg['marker_size'] = self.spnMarkerSize.value()
        cfg['line_width'] = self.spnLineWidth.value()
        cfg['lineframe_width'] = self.spnLineframeWidth.value()
        cfg['marker_opacity'] = self.spnMarkerOpacity.value()
        cfg['line_opacity'] = self.spnLineOpacity.value()
        cfg['title_font_size'] = self.spnTitleFontSize.value()
        cfg['label_font_size'] = self.spnLabelFontSize.value()
        cfg['legend_font_size'] = self.spnLegendFontSize.value()
        cfg['hover_font_size'] = self.spnHoverFontSize.value()
        cfg['tick_decimals'] = self.spnTickDecimals.value()
        cfg['webengine_scale'] = self.spnWebengineScale.value()
        # radio
        cfg['t0_source'] = 'raw' if self.rdoDataRaw.isChecked() else 'merged'
        return cfg

    def _on_section_switch(self, name: str):
        if name:
            self._cm.activate(name)
            self._load_config()

    def _add_config(self):
        name = self.editNewConfig.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入配置名称")
            return
        if not self._cm.add_section(name, copy_from=self._cm.active_section):
            QMessageBox.warning(self, "提示", f"配置「{name}」已存在")
            return
        self.cmbConfig.addItem(name)
        self.cmbConfig.setCurrentText(name)
        self.editNewConfig.clear()

    def _on_accept(self):
        # 校验 calc tab 的重命名是否有冲突
        if not self._validate_calc_rename():
            return
        self._collect_config()
        self._cm.save()
        self.accept()

    def _validate_calc_rename(self) -> bool:
        """校验 calc 表中重命名配置：同目标名必须有不同的后缀"""
        groups: dict[str, list[tuple[int, str]]] = {}  # {rename: [(row, suffix)]}
        for row in range(self.tblCalcConfig.rowCount()):
            rename = self._get_cell_text(row, 5)
            if not rename:
                continue
            suffix = self._get_cell_text(row, 6)
            groups.setdefault(rename, []).append((row, suffix))

        errors = []
        for rename, items in groups.items():
            if len(items) <= 1:
                continue
            # 检查后缀是否非空且唯一
            suffixes = [s for _, s in items]
            if len(set(suffixes)) != len(suffixes) or any(not s for s in suffixes):
                item_names = []
                for row, s in items:
                    name = self._get_cell_text(row, 1)
                    item_names.append(f"{name} → 后缀={s or '(空)'}")
                errors.append(f"目标名「{rename}」有 {len(items)} 项映射:\n" + "\n".join(f"  • {n}" for n in item_names))

        if errors:
            QMessageBox.warning(
                self, "重命名冲突",
                "以下目标名存在多个映射且后缀不唯一，请修正后再保存：\n\n" +
                "\n\n".join(errors) +
                "\n\n提示：多对一映射时每个原测试项必须填写不同的「重命名id后缀」")
            return False
        return True
