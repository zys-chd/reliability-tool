#!/usr/bin/env python3
"""
主窗口 - 对应 mainWindow_ui.py
初始化 logger，分发给所有子页面。
"""

import logging, sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QPushButton, QScrollArea, QTextEdit, QVBoxLayout, QWidget,
)

from .mainWindow_ui import Ui_MainWindow
from .logger import create_logger
from .FTDataAnalisys import FTDataAnalysisPage
from core.webengine_check import is_webengine_available
from .FTDataAnalisysConfig import ConfigDialog
from .tddb_tool import TDDBPage
from .global_setting import (
    GlobalSettingDialog, apply_global_settings,
    save_window_geometry, restore_window_geometry, get_global_cm,
)
from .BurnIn_ui import Ui_BurnInPage
from .LifeModel_ui import Ui_LifeModelPage
from .ShiftPred_ui import Ui_ShiftPredPage
from .UTtool_ui import Ui_UTPage


class AboutDialog(QDialog):
    """关于可靠性工具对话框"""

    def __init__(self, version: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于可靠性工具")
        self.setFixedSize(520, 420)
        self.setModal(True)

        # ── 外层布局 — scroll 区域 + 底部关闭按钮 ──
        self.setLayout(QVBoxLayout(self))
        layout = self.layout()  # type: QVBoxLayout
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 滚动区域 ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(scroll, stretch=1)

        # ── 滚动内容 ──
        content = QWidget()
        scroll.setWidget(content)
        vbox = QVBoxLayout(content)
        vbox.setContentsMargins(20, 20, 20, 10)
        vbox.setSpacing(12)

        # 标题
        lbl_title = QLabel("可靠性数据分析工具")
        lbl_title.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #1976D2;"
        )
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(lbl_title)

        # 版本
        lbl_version = QLabel(f"版本 {version}")
        lbl_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(lbl_version)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        vbox.addWidget(line)

        # 功能介绍
        info = QLabel(
            "本工具专为半导体可靠性工程中的良率测试（FT）和\n"
            "经时介质击穿（TDDB）数据分析而设计。\n\n"
            "主要功能：\n"
            "  • 多文件 FT 数据导入、自动格式检测与列映射\n"
            "  • 累积分布函数（CDF）与 Weibull 分布图交互绘制\n"
            "  • T0/TX/Shift 多批次对比分析\n"
            "  • TDDB Weibull 拟合、E/1E/V/E-Arrhenius 模型\n"
            "  • 面积缩放（Poisson 模型）与 β 诊断\n"
            "  • 开尔文测试结构合并与交叉对比\n"
            "  • Excel 报告自动生成"
        )
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignLeft)
        vbox.addWidget(info)

        # 分隔线
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        vbox.addWidget(line2)

        # 版权
        lbl_copyright = QLabel("Copyright © 2025 可靠性工程团队")
        lbl_copyright.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_copyright.setStyleSheet("color: #888888;")
        vbox.addWidget(lbl_copyright)

        vbox.addStretch()

        # ── 底部关闭按钮（不滚动） ──
        btn_container = QWidget()
        btn_container.setStyleSheet("background: palette(window);")
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(20, 6, 20, 10)
        btn_layout.addStretch()
        btn_close = QPushButton("关闭")
        btn_close.setFixedWidth(100)
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        layout.addWidget(btn_container)


class LogViewer(QDialog):
    """查看日志对话框"""

    def __init__(self, log_path: Path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("运行日志")
        self.resize(800, 500)
        self.setModal(True)

        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)

        # 读取日志文件
        if log_path.exists():
            content = log_path.read_text(encoding="utf-8")
            self.text_edit.setPlainText(content)
        else:
            self.text_edit.setPlainText("暂无日志")

        layout.addWidget(self.text_edit)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self._refresh)
        btn_layout.addWidget(btn_refresh)
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _refresh(self):
        log_path = Path.cwd() / "logs" / "reliability-tool.log"
        if log_path.exists():
            self.text_edit.setPlainText(log_path.read_text(encoding="utf-8"))


class UTPage(QWidget, Ui_UTPage):
    """UT 工具 — 占位页面"""
    def __init__(self, parent=None, logger: logging.Logger | None = None):
        super().__init__(parent)
        self.setupUi(self)
        self.logger = logger or create_logger("ut_tool")


class BurnInPage(QWidget, Ui_BurnInPage):
    """Burn-In 评估 — 占位页面"""
    def __init__(self, parent=None, logger: logging.Logger | None = None):
        super().__init__(parent)
        self.setupUi(self)
        self.logger = logger or create_logger("burnin")


class LifeModelPage(QWidget, Ui_LifeModelPage):
    """寿命模型 — 占位页面"""
    def __init__(self, parent=None, logger: logging.Logger | None = None):
        super().__init__(parent)
        self.setupUi(self)
        self.logger = logger or create_logger("life_model")


class ShiftPredPage(QWidget, Ui_ShiftPredPage):
    """Shift 预测 — 占位页面"""
    def __init__(self, parent=None, logger: logging.Logger | None = None):
        super().__init__(parent)
        self.setupUi(self)
        self.logger = logger or create_logger("shift_pred")


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # ── 设置窗口标题栏图标 ──
        icon_name = "icon.ico" if sys.platform == "win32" else "icon.png"
        if hasattr(sys, "__MEIPASS__"):
            icon_path = str(Path(sys._MEIPASS) / icon_name)
        else:
            icon_path = str(Path(__file__).parent.parent.parent / icon_name)
        self.setWindowIcon(QIcon(icon_path))

        if hasattr(sys, "__MEIPASS__"):
            # PyInstaller 打包时，资源文件在临时目录中
            version_path = Path(sys._MEIPASS) / "VERSION"
        else:
            version_path = Path(__file__).parent.parent.parent / "VERSION"
        version = version_path.read_text().strip()
        self._version = version
        self.setWindowTitle("可靠性工具" + " - V" + version)

        # ── 创建 logger ──
        self.logger = create_logger("reliability-tool")
        self.logger.info("程序启动")
        self.logger.info(f"日志文件：{Path.cwd() / 'logs' / 'reliability-tool.log'}")

        # ── 检查 QWebEngine 可用性 ──
        if not is_webengine_available():
            self.logger.warning(
                "QWebEngine 不可用，HTML 绘图将回退到系统浏览器。"
            )

        self._init_tabs()
        self._connect_signals()

        # 全局设置：恢复窗口位置 & 应用字体
        restore_window_geometry(self)
        apply_global_settings()

    def _init_tabs(self):
        self.ft_page = FTDataAnalysisPage(self, self.logger)
        self.tabWidget.addTab(self.ft_page, "FT 数据分析")

        self.tddb_page = TDDBPage(self, self.logger)
        self.tabWidget.addTab(self.tddb_page, "TDDB 分析")

        self.ut_page = UTPage(self, self.logger)
        self.tabWidget.addTab(self.ut_page, "UT 工具")

        self.burnin_page = BurnInPage(self, self.logger)
        self.tabWidget.addTab(self.burnin_page, "Burn-In 评估")

        self.life_model_page = LifeModelPage(self, self.logger)
        self.tabWidget.addTab(self.life_model_page, "寿命模型")

        self.shift_pred_page = ShiftPredPage(self, self.logger)
        self.tabWidget.addTab(self.shift_pred_page, "Shift 预测")

        self.logger.info(f"已加载 {self.tabWidget.count()} 个页面")

    def closeEvent(self, event):
        self.logger.info("程序关闭")
        # 保存窗口几何信息
        save_window_geometry(self)

        # 判断是否清理临时文件
        cm = get_global_cm()
        cfg = cm.as_dict()
        clean_on_exit = cfg.get("clean_on_exit", "是")

        if clean_on_exit == "是":
            for i in range(self.tabWidget.count()):
                page = self.tabWidget.widget(i)
                if hasattr(page, '_cleanup_temp_files'):
                    page._cleanup_temp_files()
        super().closeEvent(event)

    def _connect_signals(self):
        self.actExit.triggered.connect(self.close)
        self.actResetAll.triggered.connect(self._reset_all)
        self.actSaveConfig.triggered.connect(self._save_config)
        self.actConfigItems.triggered.connect(self._config_items)
        self.actViewLog.triggered.connect(self._view_log)
        self.actAbout.triggered.connect(self._show_about)
        self.actGlobalSetting.triggered.connect(self._show_global_setting)

        # 加载配置二级菜单 — 弹出时动态填充 section 列表
        self.menu.aboutToShow.connect(self._populate_config_menu)

    def _show_about(self):
        dlg = AboutDialog(self._version, self)
        dlg.exec()

    def _show_global_setting(self):
        """打开全局设置对话框。"""
        dlg = GlobalSettingDialog(self, self.logger)
        dlg.exec()

    def _apply_global_window_size(self):
        """应用全局设置中的窗口尺寸。"""
        cm = get_global_cm()
        cfg = cm.as_dict()
        w = int(cfg.get("window_width", self.width()))
        h = int(cfg.get("window_height", self.height()))
        self.resize(w, h)

    def _view_log(self):
        log_path = Path.cwd() / "logs" / "reliability-tool.log"
        dlg = LogViewer(log_path, self)
        dlg.exec()

    def _reset_all(self):
        ret = QMessageBox.question(self, "确认", "确定要重置所有内容吗？")
        if ret != QMessageBox.StandardButton.Yes:
            self.logger.debug("全局重置已取消")
            return
        self.logger.warning("用户触发了全局重置")
        for i in range(self.tabWidget.count()):
            page = self.tabWidget.widget(i)
            if hasattr(page, "reset"):
                page.reset()
        self.statusbar.showMessage("已重置所有", 3000)

    def _save_config(self):
        self.logger.info("保存配置（待实现）")
        self.statusbar.showMessage("保存配置 — 功能开发中", 3000)

    def _populate_config_menu(self):
        """填充加载配置二级菜单 — 每次弹出时动态刷新"""
        self.menu.clear()
        cm = self._get_current_cm()
        if not cm:
            action = self.menu.addAction("（当前页面无配置）")
            action.setEnabled(False)
            return
        for sec in cm.sections:
            action = self.menu.addAction(sec)
            action.setCheckable(True)
            action.setChecked(sec == cm.active_section)
            action.triggered.connect(lambda checked, s=sec: self._switch_config(s))
        # 分隔线 + 新建/删除
        if cm.sections:
            self.menu.addSeparator()
        new_action = self.menu.addAction("＋ 新建配置...")
        new_action.triggered.connect(self._new_config)
        del_action = self.menu.addAction("✕ 删除当前配置")
        del_action.setEnabled(len(cm.sections) > 1)  # 至少保留一个
        del_action.triggered.connect(self._delete_config)

    def _new_config(self):
        """新建配置 section"""
        from PySide6.QtWidgets import QInputDialog
        cm = self._get_current_cm()
        if not cm:
            return
        name, ok = QInputDialog.getText(self, "新建配置", "配置名称：")
        if not ok or not name.strip():
            return
        name = name.strip()
        if cm.add_section(name, copy_from=cm.active_section):
            cm.activate(name)
            cm.save()
            self.logger.info(f"新建配置: {name}")
            self.statusbar.showMessage(f"✅ 已新建配置: {name}", 3000)
            # 刷新当前页面
            page = self.tabWidget.currentWidget()
            if hasattr(page, '_load_config'):
                page._load_config()
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "提示", f"配置「{name}」已存在")

    def _delete_config(self):
        """删除当前配置 section"""
        from PySide6.QtWidgets import QMessageBox
        cm = self._get_current_cm()
        if not cm:
            return
        name = cm.active_section
        if len(cm.sections) <= 1:
            QMessageBox.warning(self, "提示", "至少保留一个配置")
            return
        ret = QMessageBox.question(self, "删除配置",
                                    f"确定删除配置「{name}」？\n该操作不可撤销。",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ret != QMessageBox.StandardButton.Yes:
            return
        cm.delete_section(name)
        cm.save()
        self.logger.info(f"已删除配置: {name}")
        self.statusbar.showMessage(f"已删除配置: {name}", 3000)
        page = self.tabWidget.currentWidget()
        if hasattr(page, '_load_config'):
            page._load_config()

    def _switch_config(self, section_name: str):
        """切换到指定配置 section"""
        cm = self._get_current_cm()
        if not cm:
            return
        if cm.activate(section_name):
            cm.save()
            self.logger.info(f"切换到配置: {section_name}")
            self.statusbar.showMessage(f"已切换到配置: {section_name}", 3000)
            # 通知当前页面刷新
            page = self.tabWidget.currentWidget()
            if hasattr(page, '_load_config'):
                page._load_config()
            elif hasattr(page, '_load_paths_from_config'):
                page._load_paths_from_config()
                page._load_file_lists()

    def _get_current_cm(self):
        """返回当前 tab 的 ConfigManager"""
        page = self.tabWidget.currentWidget()
        if hasattr(page, '_cm'):
            return page._cm
        return None

    def _config_items(self):
        self.logger.info("配置项（待实现）")
        self.statusbar.showMessage("配置项 — 功能开发中", 3000)
