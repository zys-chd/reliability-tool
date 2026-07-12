#!/usr/bin/env python3
"""
可复用的进度对话框 + 工作线程。

用法：
    def my_work(progress):
        progress.set_total(10)
        for i in range(10):
            if progress.cancelled:
                return None
            progress.advance(f"处理第 {i+1}/10 项...")
            do_work()
        return result

    dlg = ProgressDialog("处理中...", parent)
    result = dlg.run(my_work)
    if result is not None:
        # 完成
"""

from typing import Any, Optional, Callable

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QVBoxLayout,
)


class ProgressReporter(QObject):
    """工作线程内使用的进度报告器。通过信号跨线程安全更新 UI。"""
    on_total   = Signal(int)           # 设置总工作量
    on_advance = Signal(int, str)       # 推进 (步进数, 状态文字)
    on_status  = Signal(str)            # 仅改状态文字
    on_done    = Signal(object)         # 完成 (result)
    on_error   = Signal(str)            # 出错

    def __init__(self):
        super().__init__()
        self._cancelled = False
        self._current = 0
        self._total = 0

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    def cancel(self):
        self._cancelled = True

    def set_total(self, n: int):
        self._total = n
        self._current = 0
        self.on_total.emit(n)

    def advance(self, status: str = "", step: int = 1):
        """推进进度"""
        if self._cancelled:
            return
        self._current += step
        self.on_advance.emit(self._current, status)

    def set_status(self, text: str):
        if not self._cancelled:
            self.on_status.emit(text)

    def done(self, result: Any):
        self.on_done.emit(result)

    def error_out(self, msg: str):
        self.on_error.emit(msg)


class ProgressDialog(QDialog):
    """进度对话框 — 在工作线程中执行耗时操作，UI 不卡顿。

    用法：
        dlg = ProgressDialog("合并文件中...", parent)
        result = dlg.run(lambda p: my_work(p))
        if result is not None: ...
    """

    def __init__(self, title: str = "处理中...", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(450, 150)
        self._result: Any = None
        self._exception: Optional[Exception] = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self._lbl_status = QLabel("准备中...")
        self._lbl_status.setWordWrap(True)
        layout.addWidget(self._lbl_status)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        layout.addWidget(self._progress)

        self._lbl_detail = QLabel("")
        self._lbl_detail.setStyleSheet("color: #888;")
        layout.addWidget(self._lbl_detail)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._btn_cancel = QPushButton("取消")
        self._btn_cancel.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self._btn_cancel)
        layout.addLayout(btn_layout)

    def _on_cancel(self):
        if self._reporter:
            self._reporter.cancel()
        self._btn_cancel.setEnabled(False)
        self._lbl_status.setText("正在取消...")

    def run(self, work_fn: Callable[[ProgressReporter], Any]) -> Any:
        """在工作线程中执行 work_fn，返回结果或 None（取消/出错）。

        work_fn 接收一个 ProgressReporter 对象，用来报告进度和检查取消。
        """
        self._reporter = ProgressReporter()
        self._reporter.on_total.connect(self._on_total)
        self._reporter.on_advance.connect(self._on_advance)
        self._reporter.on_status.connect(self._on_status)
        self._reporter.on_done.connect(self._on_done)
        self._reporter.on_error.connect(self._on_error)

        self._thread = QThread()
        self._worker = _Worker(work_fn, self._reporter)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self.accept)
        self._worker.error_occurred.connect(self._on_worker_error)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

        self.exec()  # 模态阻塞

        if self._exception:
            raise self._exception  # type: ignore[misc]

        return self._result

    # ── UI 更新槽（主线程） ──

    def _on_total(self, n: int):
        self._progress.setRange(0, n)
        self._progress.setValue(0)

    def _on_advance(self, current: int, status: str):
        self._progress.setValue(current)
        if status:
            self._lbl_status.setText(status)

    def _on_status(self, text: str):
        self._lbl_detail.setText(text)

    def _on_done(self, result: Any):
        self._result = result

    def _on_error(self, msg: str):
        self._exception = RuntimeError(msg)
        self.reject()

    def _on_worker_error(self, msg: str):
        self._exception = RuntimeError(msg)
        self.reject()


class _Worker(QObject):
    """内部工作器"""
    finished = Signal()
    error_occurred = Signal(str)

    def __init__(self, work_fn, reporter):
        super().__init__()
        self._work_fn = work_fn
        self._reporter = reporter

    def run(self):
        try:
            result = self._work_fn(self._reporter)
            if not self._reporter.cancelled:
                self._reporter.done(result)
            self.finished.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))
            self.finished.emit()
