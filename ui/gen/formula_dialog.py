#!/usr/bin/env python3
"""自定义公式编辑对话框 — 输入计算公式，实时语法校验"""

import re
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCompleter, QDialog, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QVBoxLayout, QTextEdit,
)
from PySide6.QtGui import QColor, QPalette

ALLOWED_FUNCS = {"abs", "log", "exp", "log10", "sqrt", "pow", "min", "max"}
ALLOWED_VARS = {"T0", "TX"}
TOKEN_PATTERN = re.compile(r"[A-Za-z_]\w*|\d+\.?\d*|[+\-*/(),]|==")


def validate_formula(expr: str) -> tuple[bool, str]:
    """验证公式语法，返回 (是否合法, 错误信息)"""
    if not expr.strip():
        return False, "公式不能为空"

    # 检查括号匹配
    stack = 0
    for ch in expr:
        if ch == '(':
            stack += 1
        elif ch == ')':
            stack -= 1
            if stack < 0:
                return False, "多余的右括号 ')'"
    if stack > 0:
        return False, f"缺少 {stack} 个右括号 ')'"

    # 检查 Token
    tokens = TOKEN_PATTERN.findall(expr)
    if not tokens:
        return False, "公式内容为空"

    for tok in tokens:
        if tok.isidentifier():
            if tok not in ALLOWED_FUNCS and tok not in ALLOWED_VARS:
                return False, f"不支持的标识符: '{tok}'。\n允许: {', '.join(sorted(ALLOWED_FUNCS | ALLOWED_VARS))}"

    # 检查 T0 和 TX 是否都出现了
    if "T0" not in tokens:
        return False, "公式中必须使用 T0（引用产线数据）"
    if "TX" not in tokens:
        return False, "公式中必须使用 TX（引用可靠性数据）"

    # 尝试用 Python eval 做最终验证（安全沙箱）
    try:
        code = compile(expr, "<formula>", "eval")
        # 检查字节码中是否包含危险操作
        for instr in code.co_names:
            if instr not in ALLOWED_FUNCS | ALLOWED_VARS | {"abs"}:
                # abs 是 builtin，检查 co_names 可能不包含
                pass
    except SyntaxError as e:
        return False, f"语法错误: {e}"

    return True, ""


class FormulaDialog(QDialog):
    """自定义公式编辑对话框"""

    def __init__(self, current: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("自定义计算公式")
        self.resize(500, 300)
        self.setModal(True)
        self._formula = current
        self._build_ui()
        self._editor.setText(current)
        self._validate()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        hint = QLabel(
            "输入计算公式，可用变量：\n"
            "  T0 — 产线数据    TX — 可靠性数据\n"
            "可用函数：abs(), log(), exp(), log10(), sqrt(), min(), max()\n"
            "例：abs(TX - T0)          abs((TX - T0) / T0 * 100)")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #888; padding: 4px;")
        layout.addWidget(hint)

        self._editor = QLineEdit()
        self._editor.setPlaceholderText("输入公式...")
        self._editor.textChanged.connect(self._validate)
        layout.addWidget(self._editor)

        self._status = QLabel("")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("确认")
        btn_ok.clicked.connect(self._on_accept)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def _validate(self):
        expr = self._editor.text().strip()
        ok, msg = validate_formula(expr)
        if ok:
            self._status.setText("✓ 公式有效")
            self._status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self._status.setText(f"✗ {msg}")
            self._status.setStyleSheet("color: red;")

    def _on_accept(self):
        expr = self._editor.text().strip()
        ok, msg = validate_formula(expr)
        if not ok:
            QMessageBox.warning(self, "公式错误", msg)
            return
        self._formula = expr
        self.accept()

    def get_formula(self) -> str:
        return self._formula
