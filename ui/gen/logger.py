#!/usr/bin/env python3
"""
日志模块 - 封装 Python logging，同时输出到文件和 UI 面板。
每个 tab 使用 TabLoggerAdapter 自动添加 [Tab名] 前缀。
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QTextEdit

import os
_log_root = Path(os.environ.get('APPDATA', str(Path.home() / '.config'))) / "可靠性数据分析工具" / "logs"
LOG_DIR = _log_root
LOG_DIR.mkdir(parents=True, exist_ok=True)


# 日志文件格式（被文件 handler 使用）
_FILE_FORMAT = "[%(asctime)s] %(levelname)-8s %(name)s | %(message)s"
_FILE_DATEFMT = "%Y-%m-%d %H:%M:%S"

# UI/控制台格式（不含 name，因为 TabLoggerAdapter 已嵌入到消息中）
_CONSOLE_FORMAT = "[%(asctime)s] %(levelname)-8s %(message)s"
_CONSOLE_DATEFMT = "%H:%M:%S"


# ── Tab 名称映射 ──
TAB_NAMES = {
    "ft_data": "FT 数据分析",
    "tddb": "TDDB 分析",
    "ut_tool": "UT 工具",
    "burnin": "Burn-In 评估",
    "life_model": "寿命模型",
    "shift_pred": "Shift 预测",
    "reliability-tool": "主程序",
    "global_setting": "全局设置",
}


def get_tab_display_name(logger_name: str) -> str:
    """返回 logger name 对应的中文 tab 显示名。"""
    return TAB_NAMES.get(logger_name, logger_name)


class LogSignal(QObject):
    """跨线程安全的 Qt 信号"""
    message = Signal(str, int)  # text, levelno


class QtLogHandler(logging.Handler):
    """将日志发往 QTextEdit + Qt 信号"""

    def __init__(self, text_edit: QTextEdit | None = None):
        super().__init__()
        self._text_edit = text_edit
        self.signal = LogSignal()
        self._formatter = logging.Formatter(_CONSOLE_FORMAT, datefmt=_CONSOLE_DATEFMT)
        self.signal.message.connect(self._append_to_edit)

    def set_text_edit(self, te: QTextEdit):
        self._text_edit = te

    def emit(self, record):
        text = self.format(record)
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


# ── 已创建的 logger 缓存（防止重复添加 handler） ──
_created_loggers: dict[str, logging.Logger] = {}


def create_logger(name: str, text_edit: QTextEdit | None = None,
                  level: int = logging.DEBUG) -> logging.Logger:
    """创建/获取 logger。相同 name 返回同一实例。"""
    if name in _created_loggers:
        logger = _created_loggers[name]
        # 更新 text_edit（如果提供）
        if text_edit is not None:
            for h in logger.handlers:
                if isinstance(h, QtLogHandler):
                    h.set_text_edit(text_edit)
        return logger

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()

    # ── 文件 Handler ──
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"{name}.log"
    fh = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(_FILE_FORMAT, datefmt=_FILE_DATEFMT))
    logger.addHandler(fh)

    # ── Qt UI Handler ──
    qh = QtLogHandler(text_edit)
    qh.setLevel(level)
    logger.addHandler(qh)

    # ── 控制台 Handler ──
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter(_CONSOLE_FORMAT, datefmt=_CONSOLE_DATEFMT))
    logger.addHandler(ch)

    logger.info("─" * 60)
    logger.info(f"Logger 初始化完成 → 文件: {log_file}")
    logger.info(f"Python {sys.version}")

    _created_loggers[name] = logger
    return logger


class TabLoggerAdapter(logging.LoggerAdapter):
    """为 logger 自动添加 [Tab显示名] 前缀。

    用法：
        self.log = TabLoggerAdapter(logger, "ft_data")
        self.log.info("消息")  # → "[FT 数据分析] 消息"
    """

    def __init__(self, logger: logging.Logger, tab_name: str):
        super().__init__(logger, {})
        self._tab_display = get_tab_display_name(tab_name)

    def process(self, msg, kwargs):
        return f"[{self._tab_display}] {msg}", kwargs
