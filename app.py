
"""
可靠性数据分析工具 - 启动入口
仅负责创建 QApplication 和显示主窗口。
"""

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from ui.gen.mainWindow import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("可靠性工具")

    # ── Windows 任务栏图标：注册 AppUserModel ID ──
    if sys.platform == "win32":
        try:
            import ctypes
            appid = "reliabilitytool.reliability-tool.v1"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
        except Exception:
            pass  # 非致命，仅影响任务栏图标

    # ── 设置应用图标（任务栏 & 标题栏默认图标）──
    icon_name = "icon.ico" if sys.platform == "win32" else "icon.png"
    icon_path = str(Path(__file__).parent / icon_name)
    app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    import SplashModule
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
