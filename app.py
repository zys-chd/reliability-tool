"""
可靠性数据分析工具 - 启动入口
仅负责创建 QApplication 和显示主窗口。
"""

import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from ui.gen.mainWindow import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("可靠性工具")

    # ── 启动画面（必须在 QApplication 之后）──
    import SplashModule
    _splash = SplashModule.install()

    # ── Windows 任务栏图标 ──
    if sys.platform == "win32":
        try:
            import ctypes
            appid = "reliabilitytool.reliability-tool.v1"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
        except Exception:
            pass

    # ── 应用图标 ──
    icon_name = "icon.ico" if sys.platform == "win32" else "icon.png"
    icon_path = str(Path(__file__).parent / icon_name)
    if Path(icon_path).exists():
        app.setWindowIcon(QIcon(icon_path))

    # ── 启动主窗口 ──
    if _splash:
        _splash.show_message("正在加载界面...")
        QApplication.processEvents()
    window = MainWindow()

    if _splash:
        # 关闭 splash，2000ms 让主窗口有足够时间完成首帧绘制
        QTimer.singleShot(2000, SplashModule.close)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
