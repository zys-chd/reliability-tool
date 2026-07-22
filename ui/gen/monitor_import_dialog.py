"""TDDB 监控数据列映射配置对话框。"""
from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QRadioButton,
    QVBoxLayout, QWidget,
)

from core.tddb.monitor_import import (
    ColumnMapping,
    get_sheet_names,
    parse_header_rows,
)
from .TDDBMonitorImportDialog_ui import Ui_dlgMonitorImport
from .logger import create_logger, TabLoggerAdapter


class MonitorImportDialog(QDialog):
    """监控数据列映射对话框 — 支持多选批量配置。"""

    MAX_PREVIEW_ROWS = 10

    def __init__(
        self,
        file_paths: list[str],
        parent=None,
        logger: logging.Logger | None = None,
    ):
        super().__init__(parent)
        self.ui = Ui_dlgMonitorImport()
        self.ui.setupUi(self)

        self.setWindowTitle("监控数据列映射配置")
        self.resize(1200, 960)

        self._logger = TabLoggerAdapter(logger or create_logger("monitor_import"), "monitor")

        # ── 文件状态 ─────────────────────────────────────
        self._file_paths: list[str] = file_paths
        self._configs: dict[str, ColumnMapping] = {}


        # ── 预览缓存 ─────────────────────────────────────
        self._preview_rows: list[list[str]] = []
        self._preview_row_count: int = 0

        # 最近一次有效的配置（用于切换到下一个文件时保持）
        self._last_valid_config: ColumnMapping | None = None

        # 电流通道 checkbox 列表
        self._channel_checkboxes: list[QCheckBox] = []

        # ── 用 QButtonGroup 拆分两个 radio 组 ────────────
        self._time_group = QButtonGroup(self)
        self._time_group.addButton(self.ui.rdoSampleTimeFromCol)
        self._time_group.addButton(self.ui.rdoAgingTimeFromCol)
        self.ui.rdoSampleTimeFromCol.setChecked(True)

        self._voltage_group = QButtonGroup(self)
        self._voltage_group.addButton(self.ui.rdoVoltageFromCol)
        self._voltage_group.addButton(self.ui.rdoVoltageFixed)
        self.ui.rdoVoltageFromCol.setChecked(True)

        self._temp_group = QButtonGroup(self)
        self._temp_group.addButton(self.ui.rdoTempCol)
        self._temp_group.addButton(self.ui.rdoTempFixed)
        self.ui.rdoTempCol.setChecked(True)

        # ── 文件列表改用 QListWidget ────────────────────
        self._build_file_list()

        # ── 信号连接 ─── (信号阻塞避免初始化误触) ─────────
        self._connecting = False
        self._connect_signals()

        # ── 初始 UI 状态 ────────────────────────────────
        self._sync_ui_state()

    # ── 文件列表（QListWidget 支持多选） ────────────────

    def _build_file_list(self):
        """左侧文件列表。"""
        self._file_list = QListWidget()
        self._file_list.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection)
        self._file_list.setMinimumWidth(200)
        self._file_list.itemClicked.connect(self._on_file_selected)

        # 替换 scrollFileListContent 中的内容
        scroll_content = self.ui.scrollFileListContent
        layout = scroll_content.layout()
        if layout is None:
            layout = QVBoxLayout(scroll_content)
            layout.setContentsMargins(0, 0, 0, 0)
        else:
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
        layout.addWidget(self._file_list)

        for fp in self._file_paths:
            item = QListWidgetItem(Path(fp).name)
            item.setData(Qt.ItemDataRole.UserRole, fp)
            item.setToolTip(fp)
            self._file_list.addItem(item)

    def _on_file_selected(self, item: QListWidgetItem):
        """选中文件时加载预览。"""
        selected = self._get_selected_files()
        if not selected:
            return
        # 多选时按第一个文件读取
        first = selected[0]
        self._load_file_preview(first, keep_config=True)

    def _get_selected_files(self) -> list[str]:
        """获取当前选中的文件列表。"""
        items = self._file_list.selectedItems()
        return [it.data(Qt.ItemDataRole.UserRole) for it in items]

    def _get_all_items(self) -> list[QListWidgetItem]:
        return [self._file_list.item(i)
                for i in range(self._file_list.count())]

    # ── 文件预览加载 ────────────────────────────────────

    def _block_signals(self):
        self._connecting = True

    def _unblock_signals(self):
        self._connecting = False

    def _load_file_preview(self, file_path: str, keep_config: bool = False):
        """加载文件预览数据并填充下拉框。

        keep_config=True → 尽量保持当前界面配置作为下一个文件的模板。
        """
        self._block_signals()
        try:
            self._selected_file = file_path
            ext = Path(file_path).suffix.lower()

            # 1. Sheet
            self.ui.cmbSheet.clear()
            if ext == ".csv":
                self.ui.cmbSheet.addItem("CSV格式")
                self.ui.cmbSheet.setEnabled(False)
                sheet_index = 0
            else:
                sheets = get_sheet_names(file_path)
                if sheets:
                    self.ui.cmbSheet.addItems(sheets)
                    self.ui.cmbSheet.setEnabled(True)
                    if not keep_config and file_path in self._configs:
                        idx = self._configs[file_path].sheet_index
                        if 0 <= idx < len(sheets):
                            self.ui.cmbSheet.setCurrentIndex(idx)
                    sheet_index = self.ui.cmbSheet.currentIndex()
                else:
                    self.ui.cmbSheet.addItem("无可用Sheet")
                    self.ui.cmbSheet.setEnabled(False)
                    sheet_index = 0

            # 2. 读取预览行
            self._preview_rows = parse_header_rows(file_path, sheet_index,
                                                    max_rows=50)
            self._preview_row_count = min(self.MAX_PREVIEW_ROWS,
                                          len(self._preview_rows))

            # 3. 填充首行下拉框
            self._populate_header_row_combo()

            # 4. 加载已有配置（如果有）
            if file_path in self._configs:
                self._load_config_to_ui(self._configs[file_path])
            elif keep_config and self._last_valid_config:
                # 保持上次配置作为模板
                self._load_config_to_ui(self._last_valid_config)
            else:
                # 默认触发首行选择 → 填充列选择
                pass

            # 5. 自动触发首行列名提取
            self._on_header_row_changed()
        finally:
            self._unblock_signals()

    def _populate_header_row_combo(self):
        """填充首行选择下拉框。"""
        combo = self.ui.cmbHeaderRow
        combo.blockSignals(True)
        combo.clear()
        if not self._preview_rows:
            combo.blockSignals(False)
            return

        display_rows = self._preview_rows[:self._preview_row_count]
        for i, row in enumerate(display_rows):
            display = " | ".join(str(c)[:20] for c in row)
            combo.addItem(f"第{i+1}行: {display}", i)

        # "更多..."只在有更多行时添加
        if self._preview_row_count < len(self._preview_rows):
            combo.addItem("▼ 更多...", -1)

        combo.blockSignals(False)

    def _load_config_to_ui(self, cfg: ColumnMapping):
        """将配置应用到界面控件。"""
        # 首行
        idx = self.ui.cmbHeaderRow.findData(cfg.header_row)
        if idx >= 0:
            self.ui.cmbHeaderRow.setCurrentIndex(idx)

        # 时间方式
        if cfg.time_from_sampling:
            self.ui.rdoSampleTimeFromCol.setChecked(True)
        else:
            self.ui.rdoAgingTimeFromCol.setChecked(True)

        # 时间列
        self._set_combo_text(self.ui.cmbSampleTime, cfg.time_col,
                             cfg.time_from_sampling)
        self._set_combo_text(self.ui.cmbAgingTime, cfg.time_col,
                             not cfg.time_from_sampling)

        # 老化时间单位
        self._set_combo_text(self.ui.cmbAgingTimeUnit, cfg.aging_time_unit)

        # 电压
        if cfg.voltage_col:
            self.ui.rdoVoltageFromCol.setChecked(True)
            self._set_combo_text(self.ui.cmbVoltageCol, cfg.voltage_col)
        else:
            self.ui.rdoVoltageFixed.setChecked(True)
            self.ui.editVoltageFixed.setText(str(cfg.voltage_fixed))

        # 电流关键字
        self.ui.editCurrentKeyword.setText(cfg.current_keyword)
        self._set_combo_text(self.ui.cmbCurrentUnit, cfg.current_unit)

        # 温度
        if cfg.has_temp and cfg.temp_col:
            self.ui.rdoTempCol.setChecked(True)
            self._set_combo_text(self.ui.cmbTempCol, cfg.temp_col)
        else:
            self.ui.rdoTempFixed.setChecked(True)
            # 如果 cfg.temp_col 有值但 has_temp=False，用固定值
            if cfg.temp_col:
                self.ui.editTempFixed.setText(cfg.temp_col)
            else:
                self.ui.editTempFixed.setText("25")
        self._set_combo_text(self.ui.cmbTempUnit, cfg.temp_unit)

    def _set_combo_text(self, combo: QComboBox, text: str, must_match: bool = True):
        """设置 ComboBox 选中项。must_match=False 时不要求精确匹配（兼容不同文件列名）。"""
        idx = combo.findText(text)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        elif not must_match and combo.count() > 0:
            combo.setCurrentIndex(0)

    # ── 信号连接 ────────────────────────────────────────

    def _connect_signals(self):
        self.ui.cmbSheet.currentIndexChanged.connect(self._on_sheet_changed)
        self.ui.cmbHeaderRow.currentIndexChanged.connect(self._on_header_row_changed)
        self.ui.editCurrentKeyword.textChanged.connect(self._on_keyword_changed)
        self.ui.rdoTempCol.toggled.connect(self._on_temp_mode_changed)
        self.ui.pushButtonApply.clicked.connect(self._on_apply)
        self.ui.buttonBox.accepted.connect(self._on_ok)
        self.ui.buttonBox.rejected.connect(self.reject)

    def _on_sheet_changed(self):
        if self._connecting:
            return
        if not self._selected_file:
            return
        ext = Path(self._selected_file).suffix.lower()
        if ext == ".csv":
            return
        sheet_idx = self.ui.cmbSheet.currentIndex()
        self._preview_rows = parse_header_rows(self._selected_file,
                                                sheet_idx, max_rows=50)
        self._preview_row_count = min(self.MAX_PREVIEW_ROWS,
                                      len(self._preview_rows))
        self._populate_header_row_combo()

    def _on_header_row_changed(self):
        """首行选择变化时提取列名、填充下拉框。"""
        if self._connecting:
            return
        data = self.ui.cmbHeaderRow.currentData()
        if data is None:
            return
        if data == -1:
            self._show_more_rows()
            return

        header_row = data
        if header_row >= len(self._preview_rows):
            return

        header_cells = self._preview_rows[header_row]
        columns = [str(c).strip() for c in header_cells if str(c).strip()]

        self._populate_column_combos(columns)
        self._on_keyword_changed()

    def _show_more_rows(self):
        """增加 10 行显示。"""
        new_count = min(self._preview_row_count + 10, len(self._preview_rows))
        if new_count > self._preview_row_count:
            self._preview_row_count = new_count
            self._populate_header_row_combo()

    def _populate_column_combos(self, columns: list[str]):
        """填充所有列选择下拉框。"""
        for combo in [self.ui.cmbSampleTime, self.ui.cmbAgingTime,
                      self.ui.cmbVoltageCol, self.ui.cmbTempCol]:
            combo.blockSignals(True)
            current = combo.currentText()
            combo.clear()
            combo.addItems(columns)
            if current in columns:
                combo.setCurrentText(current)
            elif combo.count() > 0:
                combo.setCurrentIndex(0)
            combo.blockSignals(False)

    def _on_keyword_changed(self):
        """关键词变化时匹配电流通道。"""
        if self._connecting:
            return
        keyword = self.ui.editCurrentKeyword.text().strip()
        if not keyword:
            return

        columns = [self.ui.cmbSampleTime.itemText(i)
                   for i in range(self.ui.cmbSampleTime.count())]
        if not columns:
            return

        matched = [c for c in columns if keyword in c]
        self._update_channel_checkboxes(matched)

    def _update_channel_checkboxes(self, matched_columns: list[str]):
        """更新监控通道预览区域的 checkbox。"""
        # 保存之前勾选状态
        prev_checked = {cb.text() for cb in self._channel_checkboxes
                        if cb.isChecked()}

        for cb in self._channel_checkboxes:
            cb.deleteLater()
        self._channel_checkboxes.clear()

        scroll_content = self.ui.scrollChannelPreviewContent
        layout = scroll_content.layout()
        if layout is None:
            layout = QVBoxLayout(scroll_content)
            layout.setContentsMargins(2, 2, 2, 2)
            layout.setSpacing(2)
        else:
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()

        for col in matched_columns:
            cb = QCheckBox(col)
            # 保持之前的勾选；无历史时默认勾选含数字的列（数值型通道）
            if prev_checked:
                cb.setChecked(col in prev_checked)
            else:
                import re
                cb.setChecked(bool(re.search(r'\d', col)))
            cb.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(cb)
            self._channel_checkboxes.append(cb)

        layout.addStretch()

    def _on_temp_mode_changed(self, checked: bool):
        if self._connecting:
            return
        self.ui.cmbTempCol.setEnabled(checked)
        self.ui.cmbTempUnit.setEnabled(checked)

    # ── 应用配置 ────────────────────────────────────────

    def _on_apply(self):
        """将当前配置应用到所有选中的文件。"""
        selected = self._get_selected_files()
        if not selected:
            QMessageBox.warning(self, "提示", "请先在左侧选择要应用配置的文件")
            return

        cfg = self._gather_config()
        if cfg is None:
            return

        success_count = 0
        for fp in selected:
            try:
                # 轻量验证：只检查列名是否存在
                from core.tddb.monitor_import import get_sheet_names, parse_header_rows
                rows = parse_header_rows(fp, cfg.sheet_index, max_rows=cfg.header_row + 2)
                if cfg.header_row < len(rows):
                    columns = [str(c).strip() for c in rows[cfg.header_row]]
                    # Check required columns exist
                    if cfg.time_col and cfg.time_col not in columns:
                        raise ValueError(f"时间列 '{cfg.time_col}' 不存在")
                    if cfg.voltage_col and cfg.voltage_col not in columns:
                        raise ValueError(f"电压列 '{cfg.voltage_col}' 不存在")
                    for sc in cfg.selected_channels:
                        if sc not in columns:
                            raise ValueError(f"电流列 '{sc}' 不存在")
                self._configs[fp] = ColumnMapping(**{**cfg.__dict__})
                self._configs[fp].file_path = fp
                success_count += 1
            except Exception as e:
                self._logger.warning(f"文件 {Path(fp).name} 配置适配失败: {e}")
                QMessageBox.warning(
                    self, "配置不兼容",
                    f"文件 {Path(fp).name} 的列结构与当前配置不匹配，"
                    f"需要单独配置。\n\n错误: {e}",
                )

        # 更新文件列表显示
        self._update_file_status()

        if success_count > 0:
            # 保存为最近配置
            self._last_valid_config = cfg
            self._logger.info(f"已应用配置到 {success_count} 个文件")

    def _update_file_status(self):
        """更新文件列表的状态指示。"""
        for i in range(self._file_list.count()):
            item = self._file_list.item(i)
            fp = item.data(Qt.ItemDataRole.UserRole)
            name = Path(fp).name
            if fp in self._configs:
                item.setText(f"✓ {name}")
                item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                item.setText(name)
                item.setForeground(Qt.GlobalColor.black)

    def _gather_config(self) -> ColumnMapping | None:
        """从界面收集当前配置。"""
        try:
            time_from_sampling = self.ui.rdoSampleTimeFromCol.isChecked()
            header_row = self.ui.cmbHeaderRow.currentData()
            if header_row is None or header_row == -1:
                header_row = 0

            if self.ui.rdoVoltageFromCol.isChecked():
                voltage_col = self.ui.cmbVoltageCol.currentText()
                voltage_fixed = 0.0
            else:
                voltage_col = ""
                try:
                    voltage_fixed = float(
                        self.ui.editVoltageFixed.text() or "0")
                except ValueError:
                    voltage_fixed = 0.0

            selected_channels = [cb.text() for cb in self._channel_checkboxes
                                 if cb.isChecked()]
            if self.ui.rdoTempCol.isChecked():
                has_temp = True
                temp_col = self.ui.cmbTempCol.currentText()
            else:
                has_temp = False
                temp_col = ""

            return ColumnMapping(
                sheet_index=self.ui.cmbSheet.currentIndex(),
                sheet_name=self.ui.cmbSheet.currentText(),
                header_row=header_row,
                time_col=self.ui.cmbSampleTime.currentText()
                          if time_from_sampling
                          else self.ui.cmbAgingTime.currentText(),
                time_from_sampling=time_from_sampling,
                aging_time_unit=self.ui.cmbAgingTimeUnit.currentText(),
                voltage_col=voltage_col,
                voltage_fixed=voltage_fixed,
                current_keyword=self.ui.editCurrentKeyword.text().strip(),
                current_unit=self.ui.cmbCurrentUnit.currentText(),
                temp_col=temp_col,
                temp_unit=self.ui.cmbTempUnit.currentText(),
                has_temp=has_temp,
                selected_channels=selected_channels,
                file_path="",
                channel_columns=[cb.text() for cb in self._channel_checkboxes],
            )
        except Exception as e:
            QMessageBox.warning(self, "配置错误", f"配置有误: {e}")
            return None

    # ── OK / Cancel ─────────────────────────────────────

    def _on_ok(self):
        unapplied = [fp for fp in self._file_paths if fp not in self._configs]
        if unapplied:
            names = "\n".join(Path(fp).name for fp in unapplied[:10])
            msg = f"以下 {len(unapplied)} 个文件尚未应用配置：\n{names}"
            if len(unapplied) > 10:
                msg += f"\n...及其他 {len(unapplied) - 10} 个"
            msg += "\n\n确定要退出吗？未配置的文件将被跳过。"
            reply = QMessageBox.warning(
                self, "未完成配置", msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return
        self.accept()

    # ── UI 状态 ─────────────────────────────────────────

    def _sync_ui_state(self):
        self._on_temp_mode_changed(self.ui.rdoTempCol.isChecked())

    # ── 公开接口 ────────────────────────────────────────

    def get_configs(self) -> dict[str, ColumnMapping]:
        return self._configs
