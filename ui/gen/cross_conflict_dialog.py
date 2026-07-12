#!/usr/bin/env python3
"""
跨文件列冲突选择对话框 — 当同 group + 同 PART_ID 的同一测试列
在多个 TX 文件中有不同值时弹出，让用户逐列选择使用哪个来源。
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QHeaderView,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout,
)


class CrossFileConflictDialog(QDialog):
    """跨文件列冲突选择对话框

    用法：
        dlg = CrossFileConflictDialog(conflicts, parent)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            choices = dlg.get_choices()  # {column: source_label}
    """

    def __init__(self, conflicts: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("测试列冲突 — 请选择数据来源")
        self.resize(800, 400)
        self.setModal(True)

        self._conflicts = conflicts
        self._combos: list[QComboBox] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        hint = QLabel("以下测试列在多个文件中存在不同值，请为每一列选择要使用的来源：")
        hint.setWordWrap(True)
        hint.setStyleSheet("font-weight: bold; padding: 4px;")
        layout.addWidget(hint)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["PART_ID", "group", "冲突列", "值来源", "保留来源"])
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._table)

        self._table.setRowCount(len(self._conflicts))

        for i, c in enumerate(self._conflicts):
            key = c["key"]
            pid = str(key.get("PART_ID", ""))
            grp = str(key.get("group", ""))
            col = c["column"]
            vals = c["values"]
            src_labels = list(vals.keys())

            self._table.setItem(i, 0, QTableWidgetItem(pid))
            self._table.setItem(i, 1, QTableWidgetItem(grp))
            self._table.setItem(i, 2, QTableWidgetItem(col))
            self._table.setItem(i, 3, QTableWidgetItem(
                " | ".join(f"{k}={v:.4e}" for k, v in vals.items())))

            combo = QComboBox()
            for label in src_labels:
                combo.addItem(label)
            combo.setCurrentIndex(0)
            self._table.setCellWidget(i, 4, combo)
            self._combos.append(combo)

        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.resizeColumnsToContents()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("确认选择")
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

    def get_choices(self) -> dict[str, str]:
        """返回 {column: source_label}"""
        result = {}
        for i, c in enumerate(self._conflicts):
            col = c["column"]
            chosen = self._combos[i].currentText()
            result[col] = chosen
        return result
