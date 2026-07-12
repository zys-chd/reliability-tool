#!/usr/bin/env python3
"""
日志模块 - 封装 Python logging，同时输出到文件和 UI 面板。
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QTextEdit, QWidget


# 日志目录：Windows 上用 %APPDATA%，Linux/macOS 上用 ~/.config
import os
_log_root = Path(os.environ.get('APPDATA', str(Path.home() / '.config'))) / "可靠性数据分析工具" / "logs"
LOG_DIR = _log_root
LOG_DIR.mkdir(parents=True, exist_ok=True)


class LogSignal(QObject):
    """跨线程安全的 Qt 信号，将日志文本发射到 UI 线程"""
    message = Signal(str, int)  # text, levelno


class QtLogHandler(logging.Handler):
    """自定义 logging Handler：将日志发往 QTextEdit + Qt 信号"""

    def __init__(self, text_edit: QTextEdit | None = None):
        super().__init__()
        self._text_edit = text_edit
        self.signal = LogSignal()
        self._formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)-8s %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
        # 当有日志时，通过信号更新 UI（跨线程安全）
        self.signal.message.connect(self._append_to_edit)

    def set_text_edit(self, te: QTextEdit):
        self._text_edit = te

    def emit(self, record):
        text = self.format(record)
        # 写入文件由附加的 FileHandler 处理，QtLogHandler 只负责 UI
        if self._text_edit is not None:
            self.signal.message.emit(text, record.levelno)

    def _append_to_edit(self, text: str, levelno: int):
        if self._text_edit is None:
            return
        color = {
            logging.DEBUG:    "#888888",
            logging.INFO:     "#d4d4d4",
            logging.WARNING:  "#ffcc00",
            logging.ERROR:    "#ff5555",
            logging.CRITICAL: "#ff0000",
        }.get(levelno, "#d4d4d4")

        self._text_edit.append(f'<span style="color:{color}">{text}</span>')


def create_logger(name: str, text_edit: QTextEdit | None = None,
                  level: int = logging.DEBUG) -> logging.Logger:
    """创建 logger：同时输出到文件 + 可选的 UI 面板"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()  # 防止重复添加

    # ── 文件 Handler（RotatingFileHandler，按大小轮转） ──
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"{name}.log"
    fh = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(fh)

    # ── Qt UI Handler ──
    qh = QtLogHandler(text_edit)
    qh.setLevel(level)
    logger.addHandler(qh)

    # ── 控制台 Handler（开发时有用） ──
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(ch)

    # 记录启动日志
    logger.info("─" * 60)
    logger.info(f"Logger 初始化完成 → 文件: {log_file}")
    logger.info(f"Python {sys.version}")

    return logger
