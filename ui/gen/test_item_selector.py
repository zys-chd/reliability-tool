#!/usr/bin/env python3
"""
测试项选择组件 — 原始/候选/已选择三个 QListWidget。
原始 = 全部未选中的项
候选 = 原始中匹配筛选的项
已选择 = 用户勾选的项
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout,
    QWidget,
)

COLOR_T0   = "#f5deb3"
COLOR_TX   = "#add8e6"
COLOR_BOTH = "#90ee90"

STYLE = """
    QListWidget::item { padding: 4px 8px; }
    QListWidget::item:selected { background: #4a8cff; color: white; }
"""


class TestItemSelector(QWidget):

    def __init__(self, t0_cols: list[str], tx_cols: list[str], parent=None):
        super().__init__(parent)
        self._t0_set = set(t0_cols)
        self._tx_set = set(tx_cols)
        self._all_cols = sorted(set(t0_cols) | set(tx_cols))

        self._build_ui()
        self._rebuild()
        self._connect_signals()

    # ── 分类 ──────────────────────────────────────────────────

    def _cat(self, name: str) -> tuple[str, str]:
        t0, tx = name in self._t0_set, name in self._tx_set
        if t0 and tx:  return "(T0/TX) ", COLOR_BOTH
        if t0:         return "(T0) ",    COLOR_T0
        return                "(TX) ",    COLOR_TX

    def _dsp(self, name: str) -> str:
        return f"{self._cat(name)[0]}{name}"

    def _add(self, lst: QListWidget, name: str):
        item = QListWidgetItem(self._dsp(name))
        item.setData(Qt.ItemDataRole.UserRole, name)
        item.setBackground(QBrush(QColor(self._cat(name)[1])))
        lst.addItem(item)

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        cols = QHBoxLayout()

        # 原始
        vl = QVBoxLayout()
        vl.addWidget(QLabel("原始项目"))
        self._orig = QListWidget()
        self._orig.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)
        self._orig.setStyleSheet(STYLE)
        vl.addWidget(self._orig, 1)
        cols.addLayout(vl, 1)

        # 候选
        vl = QVBoxLayout()
        vl.addWidget(QLabel("候选项目"))
        self._cand = QListWidget()
        self._cand.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)
        self._cand.setStyleSheet(STYLE)
        vl.addWidget(self._cand, 1)
        cols.addLayout(vl, 1)

        # 中间按钮（候选 ↔ 已选择）
        btn_l = QVBoxLayout()
        btn_l.addStretch()
        self._to_right  = QPushButton(">");  self._to_right.setFixedWidth(40)
        self._to_left   = QPushButton("<");  self._to_left.setFixedWidth(40)
        self._all_right = QPushButton(">>"); self._all_right.setFixedWidth(40)
        self._all_left  = QPushButton("<<"); self._all_left.setFixedWidth(40)
        for b in (self._to_right, self._to_left, self._all_right, self._all_left):
            b.setFixedHeight(32)
        btn_l.addWidget(self._to_right)
        btn_l.addWidget(self._to_left)
        btn_l.addWidget(self._all_right)
        btn_l.addWidget(self._all_left)
        btn_l.addStretch()
        cols.addLayout(btn_l)

        # 已选择
        vl = QVBoxLayout()
        vl.addWidget(QLabel("已选择项目"))
        self._sel = QListWidget()
        self._sel.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)
        self._sel.setStyleSheet(STYLE)
        vl.addWidget(self._sel, 1)
        cols.addLayout(vl, 1)

        layout.addLayout(cols, 1)

    # ── 核心数据重建 ──────────────────────────────────────────

    def _rebuild(self, include: str = "", exclude: str = ""):
        """根据筛选重建三个列表。"""
        selected = set()
        for i in range(self._sel.count()):
            selected.add(self._sel.item(i).data(Qt.ItemDataRole.UserRole))

        self._orig.clear()
        self._cand.clear()

        incl_list = [s.strip() for s in include.split(";") if s.strip()]
        excl_list = [s.strip() for s in exclude.split(";") if s.strip()]

        for name in self._all_cols:
            if name in selected:
                continue
            display = self._dsp(name)

            # 包含=AND全部出现，排除=OR任一出现即排除
            if incl_list and not all(v.lower() in display.lower() for v in incl_list):
                self._add(self._orig, name)
                continue
            if excl_list and any(v.lower() in display.lower() for v in excl_list):
                self._add(self._orig, name)
                continue

            self._add(self._cand, name)

    # ── 信号 ──────────────────────────────────────────────────

    def _connect_signals(self):
        self._to_right.clicked.connect(self._move_right)
        self._to_left.clicked.connect(self._move_left)
        self._all_right.clicked.connect(self._move_all_right)
        self._all_left.clicked.connect(self._move_all_left)

    def _move_right(self):
        items = self._cand.selectedItems()
        if not items:
            QMessageBox.warning(self, "提示", "请先在候选项目中选中要添加的测试项")
            return
        for item in items:
            name = item.data(Qt.ItemDataRole.UserRole)
            self._cand.takeItem(self._cand.row(item))
            self._add(self._sel, name)

    def _move_left(self):
        items = self._sel.selectedItems()
        if not items:
            QMessageBox.warning(self, "提示", "请先在已选择项目中选中要移除的测试项")
            return
        for item in items:
            self._sel.takeItem(self._sel.row(item))
            # 不放回候选（候选由筛选决定），重建时自动归入原始或候选
        # 重建后 name 会回到原始（未选中）或候选（匹配筛选）
        inc = self._last_include or ""
        exc = self._last_exclude or ""
        self._rebuild(inc, exc)

    def _move_all_right(self):
        while self._cand.count():
            item = self._cand.takeItem(0)
            name = item.data(Qt.ItemDataRole.UserRole)
            self._add(self._sel, name)

    def _move_all_left(self):
        self._sel.clear()
        inc = self._last_include or ""
        exc = self._last_exclude or ""
        self._rebuild(inc, exc)

    # ── 外部接口 ──────────────────────────────────────────────

    _last_include = ""
    _last_exclude = ""

    def set_filter(self, include: str, exclude: str):
        self._last_include = include
        self._last_exclude = exclude
        self._rebuild(include, exclude)

    def set_columns(self, t0_cols: list[str], tx_cols: list[str]):
        """动态更新可用列（不清除已有选中项）"""
        self._t0_set = set(t0_cols)
        self._tx_set = set(tx_cols)
        self._all_cols = sorted(set(t0_cols) | set(tx_cols))
        # 移除选中项中不再存在的列
        to_remove = []
        for i in range(self._sel.count()):
            name = self._sel.item(i).data(Qt.ItemDataRole.UserRole)
            if name not in self._all_cols:
                to_remove.append(i)
        for i in reversed(to_remove):
            self._sel.takeItem(i)
        self._rebuild(self._last_include or "", self._last_exclude or "")

    def get_selected(self) -> list[str]:
        return [self._sel.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(self._sel.count())]

    def set_selected(self, names: list[str]):
        self._sel.clear()
        for n in names:
            if n in self._all_cols:
                self._add(self._sel, n)
        self._rebuild(self._last_include or "",
                      self._last_exclude or "")
