#!/usr/bin/env python3
"""
冲突选择对话框 - 当同 PART_ID 全部为 FAIL 且多条时弹出，
让用户选择保留哪一行。
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QButtonGroup, QDialog, QHBoxLayout, QHeaderView,
    QPushButton, QRadioButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)


class ConflictDialog(QDialog):
    """冲突行选择对话框

    用法：
        dlg = ConflictDialog(fail_rows_df, parent)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            selected_index = dlg.selected_index  # 在原 DataFrame 中的行号
    """

    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择保留的数据行")
        self.resize(900, 400)
        self.setModal(True)

        self._df = df
        self.selected_index: int | None = None
        self.fix_in_excel: bool = False  # True 表示用户点了「导出Excel自行修复」
        self._radio_buttons: list[QRadioButton] = []
        self._radio_group = QButtonGroup(self)

        self._build_ui()
        self._populate(df)

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # 提示
        from PySide6.QtWidgets import QLabel
        hint = QLabel(
            "以下 PART_ID 全部为 FAIL，请选择要保留的一行：")
        hint.setStyleSheet("font-weight: bold; padding: 4px;")
        layout.addWidget(hint)

        # 表格
        self._table = QTableWidget()
        self._table.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection)
        self._table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_export = QPushButton("导出Excel自行修复")
        btn_export.clicked.connect(self._on_export_excel)
        btn_layout.addWidget(btn_export)
        btn_layout.addStretch()
        btn_ok = QPushButton("确认")
        btn_ok.clicked.connect(self._on_accept)
        btn_cancel = QPushButton("放弃该组")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def _populate(self, df):
        # 把 filepath 和 group 移到最前面
        preferred = ["filepath", "group"]
        other_cols = [c for c in df.columns if c not in preferred]
        ordered_cols = preferred + other_cols
        df = df[ordered_cols]

        # 更新标题显示进度
        # (父 dialog 会在外部设置标题含 i/total)

        cols = ["保留"] + list(df.columns)
        self._table.setColumnCount(len(cols))
        self._table.setHorizontalHeaderLabels(cols)
        self._table.setRowCount(len(df))

        # 隐藏 _file, _source 等内部列
        for c in df.columns:
            idx = list(df.columns).index(c)
            if c.startswith("_"):
                self._table.setColumnHidden(idx + 1, True)

        for r in range(len(df)):
            # Radio 按钮列
            rb = QRadioButton()
            rb.setChecked(r == 0)  # 默认选第一条
            widget = QWidget()
            from PySide6.QtWidgets import QHBoxLayout
            hl = QHBoxLayout(widget)
            hl.addWidget(rb)
            hl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hl.setContentsMargins(0, 0, 0, 0)
            self._table.setCellWidget(r, 0, widget)
            self._radio_buttons.append(rb)
            self._radio_group.addButton(rb)

            # 数据列
            for c_idx, col in enumerate(df.columns):
                val = df.iloc[r][col]
                text = str(val) if val is not None else ""
                item = QTableWidgetItem(text)
                item.setToolTip(text)
                self._table.setItem(r, c_idx + 1, item)

        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.resizeColumnsToContents()

    def _on_accept(self):
        for i, rb in enumerate(self._radio_buttons):
            if rb.isChecked():
                self.selected_index = i  # 存行号（位置），不是 Index 标签
                break
        self.accept()

    def _on_export_excel(self):
        """标记用户选择导出Excel自行修复"""
        self.fix_in_excel = True
        self.accept()
