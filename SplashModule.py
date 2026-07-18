"""
可靠性工具 - 启动画面模块

功能：
- 关闭 PyInstaller 内置 splash（如果有）
- 显示 splash.jpg 背景 + 叠加文字（工具名、加载进度、版权）
- 主窗口就绪后自动关闭
"""
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen


_installed = False


def _close_pyi_splash():
    try:
        import os
        if '_PYI_SPLASH_IPC' in os.environ:
            import pyi_splash
            pyi_splash.close()
    except Exception:
        pass


def install():
    """安装 Qt 启动画面。"""
    global _installed, _splash
    if _installed:
        return
    _installed = True


    img_path = Path(__file__).parent / "splash.jpg"
    if not img_path.exists():
        return

    pixmap = QPixmap(str(img_path))
    _splash = SplashScreen(pixmap)
    _splash.show()
    _close_pyi_splash()
    QApplication.processEvents()  # 强制绘制文字
    return _splash


def message(msg: str):
    if _splash is not None:
        _splash.show_message(msg)
        QApplication.processEvents()


def close():
    global _splash, _installed
    if _splash is not None:
        _splash.close()
        _splash = None
    _installed = False


def is_active() -> bool:
    return _splash is not None and _splash.isVisible()


class SplashScreen(QSplashScreen):
    """带文字叠加的启动画面。"""

    def __init__(self, pixmap: QPixmap):
        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.SplashScreen)
        self._message = "正在初始化..."

    def show_message(self, text: str):
        self._message = text
        self.repaint()
        QApplication.processEvents()

    def drawContents(self, painter: QPainter):
        w = self.pixmap().width()
        h = self.pixmap().height()

        # 半透明遮罩（底部区域）
        painter.fillRect(0, int(h * 0.78), w, int(h * 0.22),
                         QColor(0, 0, 0, 160))

        # 工具名称
        painter.setPen(QColor(255, 255, 255))
        f = QFont()
        f.setFamilies(["Microsoft YaHei", "Noto Sans CJK SC",
                        "WenQuanYi Micro Hei", "sans-serif"])
        f.setPixelSize(28)
        f.setBold(True)
        painter.setFont(f)
        painter.drawText(40, int(h * 0.80), "可靠性数据分析工具")

        # 加载消息
        f.setPixelSize(16)
        f.setBold(False)
        painter.setFont(f)
        painter.setPen(QColor(200, 220, 255))
        painter.drawText(40, int(h * 0.88), self._message)

        # 版权
        f.setPixelSize(12)
        painter.setFont(f)
        painter.setPen(QColor(150, 150, 150))
        painter.drawText(40, int(h * 0.95),
                         "Copyright © 2026 Huawei Digital Power Technologies Co., Ltd.\nzhangyusong8@huawei.com")


_splash: SplashScreen | None = None
