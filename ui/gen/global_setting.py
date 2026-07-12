"""全局设置对话框。"""
import logging
import os
from pathlib import Path

from PySide6.QtCore import Qt, QByteArray
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import (
    QApplication, QDialog, QHBoxLayout, QPushButton, QVBoxLayout, QWidget,
)

from .globalSetting_ui import Ui_Form
from .config_manager import ConfigManager
from .config_schemas import GLOBAL_SCHEMA


def get_global_cm() -> ConfigManager:
    """获取全局配置的 ConfigManager。"""
    cfg_path = Path(__file__).parent.parent.parent / "config" / "global_setting.toml"
    cm = ConfigManager(cfg_path, GLOBAL_SCHEMA, logger=logging.getLogger("global"))
    cm.load()
    return cm


def apply_global_settings(cm: ConfigManager | None = None):
    """将全局配置应用到 QApplication（字体等）。"""
    if cm is None:
        cm = get_global_cm()
    cfg = cm.as_dict()
    app = QApplication.instance()
    if app is None:
        return

    # 字体
    font_size = cfg.get("font_size", 12)
    font_cn = cfg.get("font_cn", "")
    font_en = cfg.get("font_en", "")
    families = []
    if font_en:
        families.append(font_en)
    families.append("sans-serif")
    font = QFont()
    if families:
        font.setFamilies(families)
    font.setPointSize(int(font_size))
    app.setFont(font)


def save_window_geometry(window, cm: ConfigManager | None = None):
    """保存窗口尺寸和几何信息到全局配置。"""
    if cm is None:
        cm = get_global_cm()
    geo = window.saveGeometry()
    cm.set("window_geometry", geo.toBase64().data().decode("ascii"))
    cm.set("window_width", window.width())
    cm.set("window_height", window.height())
    cm.save()


def restore_window_geometry(window, cm: ConfigManager | None = None):
    """从全局配置恢复窗口尺寸和位置。"""
    if cm is None:
        cm = get_global_cm()
    cfg = cm.as_dict()

    pos_mode = cfg.get("window_position", "记忆上次关闭时位置")
    if pos_mode == "记忆上次关闭时位置":
        geo_b64 = cfg.get("window_geometry", "")
        if geo_b64:
            ba = QByteArray.fromBase64(geo_b64.encode("ascii"))
            if window.restoreGeometry(ba):
                return

    # 没有保存的几何信息或用其他位置模式
    w = int(cfg.get("window_width", 910))
    h = int(cfg.get("window_height", 692))

    screen = window.screen()
    if screen is None:
        window.resize(w, h)
        return
    screen_geo = screen.availableGeometry()
    cx = screen_geo.center()
    sw, sh = screen_geo.width(), screen_geo.height()

    pos_map = {
        "中心": (cx.x() - w // 2, cx.y() - h // 2),
        "左上": (screen_geo.x(), screen_geo.y()),
        "右上": (screen_geo.x() + sw - w, screen_geo.y()),
        "左下": (screen_geo.x(), screen_geo.y() + sh - h),
        "右下": (screen_geo.x() + sw - w, screen_geo.y() + sh - h),
        "上方": (cx.x() - w // 2, screen_geo.y()),
        "下方": (cx.x() - w // 2, screen_geo.y() + sh - h),
        "左方": (screen_geo.x(), cx.y() - h // 2),
        "右方": (screen_geo.x() + sw - w, cx.y() - h // 2),
    }
    if pos_mode in pos_map:
        x, y = pos_map[pos_mode]
        window.setGeometry(x, y, w, h)
    else:
        window.resize(w, h)


class GlobalSettingDialog(QDialog):
    """全局设置对话框。"""

    def __init__(self, parent=None, logger: logging.Logger | None = None):
        super().__init__(parent)
        self.setWindowTitle("全局设置")
        self.resize(600, 700)
        self.logger = logger or logging.getLogger("global")

        # 配置
        self._cm = get_global_cm()

        # UI
        self._ui = Ui_Form()
        layout = QVBoxLayout(self)
        self._settings_widget = QWidget()
        self._ui.setupUi(self._settings_widget)
        layout.addWidget(self._settings_widget)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btnApply = QPushButton("应用")
        self.btnCancel = QPushButton("取消")
        btn_layout.addWidget(self.btnApply)
        btn_layout.addWidget(self.btnCancel)
        layout.addLayout(btn_layout)

        # 暴露控件
        self.spnWinHeight = self._ui.spnWinHeight
        self.spnWinWidth = self._ui.spnWinWidth
        self.cmbWinPosition = self._ui.cmbWinPosition
        self.spnFontSize = self._ui.spnFontSize
        self.cmbCnFont = self._ui.cmbCnFont
        self.cmbEnFont = self._ui.cmbEnFont
        self.cmbCleanOnExit = self._ui.cmbCleanOnExit

        # 填充字体列表
        families = QFontDatabase().families()
        cn_families = [f for f in families if any(kw in f.lower()
                      for kw in ["song", "hei", "kai", "fang", "ming",
                                  "noto sans cjk", "noto serif cjk",
                                  "wenquanyi", "droid sans fallback",
                                  "source han", "思源", "微软雅黑",
                                  "simsun", "simhei", "yahei"])]
        en_families = [f for f in families if not any(c > '\u4e00' and c < '\u9fff'
                      for c in f)]

        self.cmbCnFont.addItem("（使用系统默认）", "")
        self.cmbEnFont.addItem("（使用系统默认）", "")
        for f in cn_families:
            self.cmbCnFont.addItem(f, f)
        for f in en_families:
            self.cmbEnFont.addItem(f, f)

        # 信号
        self.btnApply.clicked.connect(self._on_apply)
        self.btnCancel.clicked.connect(self.reject)

        # 加载
        self._load_from_config()

    def _load_from_config(self):
        """从配置加载值到 UI 控件。"""
        cfg = self._cm.as_dict()
        self.spnWinHeight.setValue(int(cfg.get("window_height", 692)))
        self.spnWinWidth.setValue(int(cfg.get("window_width", 910)))
        idx = self.cmbWinPosition.findText(cfg.get("window_position", "记忆上次关闭时位置"))
        if idx >= 0:
            self.cmbWinPosition.setCurrentIndex(idx)
        self.spnFontSize.setValue(int(cfg.get("font_size", 12)))

        def _set_combo_value(cmb, val):
            for i in range(cmb.count()):
                if cmb.itemData(i) == val or cmb.itemText(i) == val:
                    cmb.setCurrentIndex(i)
                    return
        _set_combo_value(self.cmbCnFont, cfg.get("font_cn", ""))
        _set_combo_value(self.cmbEnFont, cfg.get("font_en", ""))
        idx = self.cmbCleanOnExit.findText(cfg.get("clean_on_exit", "是"))
        if idx >= 0:
            self.cmbCleanOnExit.setCurrentIndex(idx)

    def _on_apply(self):
        """应用设置并保存。"""
        self._cm.set("window_height", self.spnWinHeight.value())
        self._cm.set("window_width", self.spnWinWidth.value())
        self._cm.set("window_position", self.cmbWinPosition.currentText())
        self._cm.set("font_size", self.spnFontSize.value())
        self._cm.set("font_cn", self.cmbCnFont.currentData() or "")
        self._cm.set("font_en", self.cmbEnFont.currentData() or "")
        self._cm.set("clean_on_exit", self.cmbCleanOnExit.currentText())
        self._cm.save()

        # 立即应用字体
        apply_global_settings(self._cm)

        # 通知主窗口调整窗口
        parent = self.parent()
        if parent and hasattr(parent, '_apply_global_window_size'):
            parent._apply_global_window_size()

        self.accept()
