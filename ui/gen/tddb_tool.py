"""TDDB 分析页面 - 对应 TDDBTool_ui.py

串联 Weibull 拟合 → 寿命模型 → 失效率计算全流程。
"""
import logging
import shutil
import sys, os
from pathlib import Path

import numpy as np
import pandas as pd
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (
    QDialog, QFileDialog, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidgetItem,
    QVBoxLayout, QWidget, QHeaderView,
)
from PySide6.QtWebEngineCore import QWebEngineSettings

from .TDDBTool_ui import Ui_Form
from .TDDBSetting_ui import Ui_Form as Ui_Settings
from .logger import create_logger, TabLoggerAdapter
from .config_manager import ConfigManager
from .config_schemas import TDDB_SCHEMA
from core.tddb.weibull_fitter import fit_weibull, fit_unified_slope, weibull_plot_data
from core.tddb.models import (
    fit_e_model, fit_1e_model, fit_v_model, fit_sqrt_e_model, fit_e_arrhenius,
    predict_lifetime, predict_failure_rate,
)
from core.tddb.area_scaling import scale_eta
from core.tddb.confidence import weibull_ci_beta, weibull_ci_eta, lifetime_ci
from core.tddb.beta_diagnostics import (
    make_beta_vs_vgs_plot,
    make_beta_vs_temp_plot,
    make_beta_vs_area_plot,
)
from core.tddb.test_data import make_tddb_dataset, make_tddb_excel

# ── Helpers ──────────────────────────────────────────────────────────

EXCEL_FILTER = "Excel 文件 (*.xlsx *.xls);;所有文件 (*)"
TEMPLATE_SOURCE = Path(__file__).parent.parent.parent / "TDDB_template.xlsx"

_FORMULA_MODEL_MAP = {
    "E模型": "e_model",
    "1/E模型": "1e_model",
    "V模型": "v_model",
    "√E模型": "sqrt_e_model",
}


def _get_formula_images_dir() -> Path:
    """返回预渲染公式图片所在目录（支持 PyInstaller 打包模式）。"""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "ui" / "gen" / "formula_images"
    return Path(__file__).parent / "formula_images"


def _load_formula_pixmap(stem: str) -> 'QPixmap | None':
    """从预渲染 PNG 加载公式图片。"""
    from PySide6.QtGui import QPixmap
    path = _get_formula_images_dir() / f"{stem}.png"
    if path.exists():
        return QPixmap(str(path))
    return None


def _set_webengine_settings(view):
    """Apply common QWebEngineView settings."""
    try:
        view.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )
    except Exception:
        pass


def _fmt_eta(val: float) -> str:
    """智能格式化 η：极小值用科学计数法，否则保留 2 位小数。"""
    if abs(val) < 0.01:
        return f"{val:.4e}"
    return f"{val:.2f}"


def _render_html_in_view(view, fig, temp_dir, file_type="TDDB"):
    """Render a plotly figure into a QWebEngineView."""
    # from plotly.offline import plot as plotly_plot
#     html = plotly_plot(fig, include_plotlyjs="cdn", output_type="div",
#                        config={"responsive": True, "displayModeBar": True, "scrollZoom": True})
#     full_html = f"""<!DOCTYPE html>
# <html><head><meta charset="utf-8">
# <style>
# html,body {{ margin:0; padding:0; width:100%; height:100%; overflow:auto; }}
# .plotly-div {{ width:100%; min-height:100%; }}
# </style></head><body>
# {html}
# </body></html>"""
    _set_webengine_settings(view)
    # view.setHtml(full_html)
    from PySide6.QtCore import QUrl
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(temp_dir, exist_ok=True)
    html_path = str(Path(temp_dir) / f"{file_type}-{timestamp}.html")
    fig.write_html(html_path)
    view.load(QUrl.fromLocalFile(html_path))


# ── Settings Dialog ─────────────────────────────────────────────

class SettingsDialog(QDialog):
    """TDDB 设置对话框。"""
    def __init__(self, parent=None, cm=None, ui_callback=None):
        super().__init__(parent)
        self.setWindowTitle("TDDB 设置")
        self.resize(550, 600)
        self._cm = cm
        self._ui_callback = ui_callback

        # 使用 Ui_Settings 布局
        self._ui = Ui_Settings()
        # Ui_Settings.setupUi expects a QWidget; we embed it
        layout = QVBoxLayout(self)
        self._settings_widget = QWidget()
        self._ui.setupUi(self._settings_widget)
        layout.addWidget(self._settings_widget)

        # 按钮行
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btnSaveDirBrowse = self._ui.btnBrowseSaveDir
        self.btnFileBrowse = self._ui.btnBrowseFile
        self.btnApply = QPushButton("应用")
        self.btnCancel = QPushButton("取消")
        btn_layout.addWidget(self.btnApply)
        btn_layout.addWidget(self.btnCancel)
        layout.addLayout(btn_layout)

        # 暴露常用控件属性
        self.editFilePath = self._ui.editFilePath
        self.cmbSheetName = self._ui.cmbSheetName
        self.spnWorkVoltage = self._ui.spnWorkVoltage
        self.spnWorkTemp = self._ui.spnWorkTemp
        self.spnOxideThickness = self._ui.spnOxideThickness
        self.cmbTDDBModel = self._ui.cmbTDDBModel
        self.cmbPickMethod = self._ui.cmbPickMethod
        self.editSaveDir = self._ui.editSaveDir

        # 信号
        self.btnApply.clicked.connect(self.accept)
        self.btnCancel.clicked.connect(self.reject)

        if callable(self._ui_callback):
            self._ui_callback(self._ui)

    @property
    def ui(self):
        return self._ui


# ── TDDB Page ─────────────────────────────────────────────────────

class TDDBPage(QWidget, Ui_Form):
    """TDDB 分析页面。"""

    # Weibull 拟合结果缓存
    _fit_results: dict = {}       # {(group, Vgs, T, A): {beta, eta, ...}}
    _beta_data: dict | None = None  # for diagnostic plots
    _current_plot_mode: str = "weibull"  # "weibull" | "beta"

    def __init__(self, parent=None, logger: logging.Logger | None = None):
        super().__init__(parent)
        self.setupUi(self)
        self.logger = TabLoggerAdapter(logger or create_logger("tddb_tool"), "tddb")
        self._data: pd.DataFrame | None = None
        self._fit_results_tbd: dict = {}  # TBD 拟合结果
        self._fit_results_qbd: dict = {}  # QBD 拟合结果
        self._beta_data = None
        self._current_data_type = "TBD"  # "TBD" 或 "QBD"
        self._current_plot_mode = "weibull"
        self._data_version = 0
        self._last_life_results: list[dict] = []
        self._last_fr_results: list[dict] = []
        self._last_curve_data: dict = {}  # {grp: {eta, beta}}
        self._last_model_params: dict = {}  # {grp: {gamma, g, beta_v, ea}}
        self._last_etas: dict = {}  # {key: 实际 η（平滑或 Weibull）}
        self._fitting_in_progress = False  # reentrant guard
        self._initialized = False  # 初始化完成后设为 True

        # ConfigManager — 使用项目 config/ 目录
        cfg_path = Path(__file__).parent.parent.parent / "config" / "tddb_tool.toml"
        self._cm = ConfigManager(cfg_path, TDDB_SCHEMA, logger=self.logger)
        self._load_config()

        self._connect_signals()
        self._init_settings_tab()

        self._initialized = True

    def closeEvent(self, event):
        """关闭页面时清理临时 HTML 文件（仅当保存目录存在时）。"""
        self._cleanup_temp_files()
        event.accept()

    def _cleanup_temp_files(self):
        """清理当前页面的临时 HTML 文件。主窗口关闭时也会调用此方法。"""
        try:
            if hasattr(self, 'save_dir') and self.save_dir and os.path.isdir(self.save_dir):
                for file in os.listdir(self.save_dir):
                    if file.startswith("TDDB") and file.endswith(".html"):
                        os.remove(os.path.join(self.save_dir, file))
        except Exception as e:
            self.logger.warning(f"清理临时文件时出错: {e}")

    # ── 当前数据类型的拟合结果访问器 ────────────────────────────

    @property
    def _fit_results(self):
        return self._fit_results_tbd if self._current_data_type == "TBD" else self._fit_results_qbd

    @_fit_results.setter
    def _fit_results(self, value):
        if self._current_data_type == "TBD":
            self._fit_results_tbd = value
        else:
            self._fit_results_qbd = value

    # ── 信号连接 ────────────────────────────────────────────────

    def _connect_signals(self):
        self.btnSelectFile.clicked.connect(self._on_select_file)
        self.btnExportTemplate.clicked.connect(self._on_export_template)
        self.btnWeibullFit.clicked.connect(self._on_weibull_fit_clicked)
        self.btnBetaDiagnostic.clicked.connect(self._on_beta_diagnostic)
        self.btnAddCustomPlot.clicked.connect(self._on_add_custom_plot)
        self.chkUnifySlope.stateChanged.connect(self._on_slope_changed)
        self.btnCalc.clicked.connect(self._on_calc)
        self.cmbTDDBModel.currentIndexChanged.connect(self._update_formula_display)
        self.cmbTDDBModel.currentIndexChanged.connect(
            lambda: self._on_calc() if self._fit_results else None)
        self.cmbPickMethod.currentIndexChanged.connect(
            lambda: self._on_calc() if self._fit_results else None)
        self.tblRawParams.itemChanged.connect(self._on_param_edited)

        # 原始数据刷新/写入
        self.btnRefreshData.clicked.connect(self._on_refresh_data)
        self.btnWriteData.clicked.connect(self._on_write_data)

        # ? 帮助按钮
        self.btnLifeHelp.clicked.connect(self._on_life_help)
        self.btnFailHelp.clicked.connect(self._on_fail_help)

        # TBD/QBD 切换 → 自动重新拟合
        self.rdoTBD.toggled.connect(self._on_data_type_changed)
        self.rdoQBD.toggled.connect(self._on_data_type_changed)

        # 设置按钮
        self.btnSetting.clicked.connect(self._on_open_settings)

        # 曲线绘制按钮
        self.btnPlotLifeFR.clicked.connect(self._on_plot_life_fr)
        self.btnPlotFailCurve.clicked.connect(self._on_plot_fail_curve)

        # 配置保存
        self.editWorkVoltage.editingFinished.connect(self._save_config)
        self.editOxideThickness.editingFinished.connect(self._save_config)
        self.editWorkTemp.editingFinished.connect(self._save_config)
        self.cmbTDDBModel.currentIndexChanged.connect(self._save_config)

        # Weibull 结果 tab 的 sub-tab: 点击时 if 是"拟合结果"tab 就重新布局
        self.twFitResult.currentChanged.connect(self._on_fit_result_tab_changed)

    # ── 设置对话框 ────────────────────────────────────────────

    def _init_settings_tab(self):
        """初始化设置对话框（由 btnSetting 触发）。"""
        self._settings_dialog = None  # lazy init

    def _on_open_settings(self):
        """打开设置对话框。"""
        if self._settings_dialog is None:
            self._settings_dialog = SettingsDialog(self, self._cm, self._settings_ui_callback)
            self._settings_dialog.finished.connect(self._on_settings_closed)
        self._sync_settings_to_dialog()
        self._settings_dialog.show()

    def _settings_ui_callback(self, ui):
        """给 SettingsDialog 提供顶层控件的引用以复用逻辑。"""
        pass

    def _sync_settings_to_dialog(self):
        """将当前配置同步到设置对话框。"""
        if self._settings_dialog is None:
            return
        dlg = self._settings_dialog
        dlg.editFilePath.setText(self.lblFilePath.text())
        dlg.cmbSheetName.clear()
        dlg.cmbSheetName.addItems([self.cmbSheetSelector.itemText(i)
                                   for i in range(self.cmbSheetSelector.count())])
        idx = self.cmbSheetSelector.currentIndex()
        if idx >= 0:
            dlg.cmbSheetName.setCurrentIndex(idx)
        dlg.spnWorkVoltage.setValue(self.editWorkVoltage.value())
        dlg.spnWorkTemp.setValue(self.editWorkTemp.value())
        dlg.spnOxideThickness.setValue(self.editOxideThickness.value())
        dlg.cmbTDDBModel.setCurrentIndex(self.cmbTDDBModel.currentIndex())
        dlg.cmbPickMethod.setCurrentIndex(self.cmbPickMethod.currentIndex())
        dlg.editSaveDir.setText(self.save_dir)

    def _apply_settings(self):
        """从设置对话框读取值，应用到主页面控件并保存。"""
        if self._settings_dialog is None:
            return
        dlg = self._settings_dialog
        self.editWorkVoltage.setValue(dlg.spnWorkVoltage.value())
        self.editWorkTemp.setValue(dlg.spnWorkTemp.value())
        self.editOxideThickness.setValue(dlg.spnOxideThickness.value())
        self.cmbTDDBModel.setCurrentIndex(dlg.cmbTDDBModel.currentIndex())
        self.cmbPickMethod.setCurrentIndex(dlg.cmbPickMethod.currentIndex())
        # save_dir
        sd = dlg.editSaveDir.text()
        if sd:
            self.save_dir = sd
            os.makedirs(self.save_dir, exist_ok=True)
        # sheet
        sheet = dlg.cmbSheetName.currentText()
        idx = self.cmbSheetSelector.findText(sheet)
        if idx >= 0:
            self.cmbSheetSelector.setCurrentIndex(idx)
        self._save_config()

    def _on_settings_closed(self, result):
        """设置对话框关闭时应用设置。"""
        if result == QDialog.DialogCode.Accepted:
            self._apply_settings()
        self._sync_settings_to_dialog()  # 即使取消也保持界面同步

    # ── 文件操作 ────────────────────────────────────────────────

    def _on_select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 TDDB 数据文件", "", EXCEL_FILTER)
        if not path:
            return
        self.lblFilePath.setText(path)
        self._load_excel(path)

    def _load_excel(self, path: str):
        """读取 Excel 并填充 sheet 选择框。"""
        try:
            import openpyxl
            wb = openpyxl.load_workbook(path, read_only=True)
            sheets = wb.sheetnames
            wb.close()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法读取文件：{e}")
            return

        self.cmbSheetSelector.clear()
        self.cmbSheetSelector.addItems(sheets)
        self.cmbSheetSelector.currentIndexChanged.connect(self._on_sheet_changed)
        self.cmbSheetSelector.currentIndexChanged.connect(self._save_config)
        self._on_sheet_changed()

    def _on_sheet_changed(self):
        """切换 sheet 时重新读取数据。"""
        path = self.lblFilePath.text()
        if not path or not Path(path).exists():
            return
        sheet = self.cmbSheetSelector.currentText()
        if not sheet:
            return
        try:
            df = pd.read_excel(path, sheet_name=sheet)
            self._data = df
            self._data_version += 1
            # 新数据，清除旧的拟合结果
            self._fit_results = {}
            self._last_life_results = []
            self._last_fr_results = []
            self.logger.info(f"已读取 {path}[{sheet}]: {len(df)} 行, {len(df.columns)} 列")
            self._populate_raw_data_tab()
        except Exception as e:
            self.logger.error(f"读取 Excel 失败: {e}")
            QMessageBox.critical(self, "错误", f"读取失败：{e}")

    def _populate_raw_data_tab(self):
        """填充原始数据 tab 的表格。"""
        if self._data is None:
            return
        df = self._data
        self.tblRawData.setColumnCount(len(df.columns))
        self.tblRawData.setHorizontalHeaderLabels(list(df.columns))
        self.tblRawData.setRowCount(len(df))
        for r in range(len(df)):
            for c in range(len(df.columns)):
                val = df.iloc[r, c]
                item = QTableWidgetItem(str(val) if not pd.isna(val) else "")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tblRawData.setItem(r, c, item)
        self.tblRawData.resizeColumnsToContents()

    def _on_export_template(self):
        """导出 TDDB 模板。"""
        target, _ = QFileDialog.getSaveFileName(self, "导出模板", "TDDB_template.xlsx",
                                                  "Excel 文件 (*.xlsx)")
        if not target:
            return
        try:
            shutil.copy2(TEMPLATE_SOURCE, target)
            QMessageBox.information(self, "完成", f"模板已导出到:\n{target}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败：{e}")

    # ── 刷新 / 写入 原始数据 ──────────────────────────────────

    def _on_refresh_data(self):
        self._on_sheet_changed()

    def _on_write_data(self):
        path = self.lblFilePath.text()
        if not path or not Path(path).exists():
            return
        sheet = self.cmbSheetSelector.currentText()
        try:
            # Reconstruct DataFrame from table
            headers = [self.tblRawData.horizontalHeaderItem(c).text()
                       for c in range(self.tblRawData.columnCount())]
            rows = []
            for r in range(self.tblRawData.rowCount()):
                row = []
                for c in range(self.tblRawData.columnCount()):
                    item = self.tblRawData.item(r, c)
                    row.append(item.text() if item else "")
                rows.append(row)
            df = pd.DataFrame(rows, columns=headers)
            with pd.ExcelWriter(path, mode="a", if_sheet_exists="replace",
                                engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name=sheet, index=False)
            self.logger.info(f"数据已写入 {path}[{sheet}]")
            QMessageBox.information(self, "完成", "写入成功")
        except Exception as e:
            self.logger.error(f"写入失败: {e}")
            QMessageBox.critical(self, "错误", f"写入失败：{e}")

    # ── 配置持久化 ────────────────────────────────────────────

    def _load_config(self):
        """从 ConfigManager 加载保存的参数。"""
        cfg = self._cm.as_dict()
        if cfg.get("file_path"):
            self.lblFilePath.setText(str(cfg["file_path"]))
        if cfg.get("sheet_name"):
            idx = self.cmbSheetSelector.findText(cfg["sheet_name"])
            if idx >= 0:
                self.cmbSheetSelector.setCurrentIndex(idx)
        if cfg.get("work_voltage"):
            self.editWorkVoltage.setValue(float(cfg["work_voltage"]))
        if cfg.get("oxide_thickness"):
            self.editOxideThickness.setValue(float(cfg["oxide_thickness"]))
        if cfg.get("work_temperature"):
            self.editWorkTemp.setValue(float(cfg["work_temperature"]))
        if cfg.get("tddb_model"):
            idx = self.cmbTDDBModel.findText(cfg["tddb_model"])
            if idx >= 0:
                self.cmbTDDBModel.setCurrentIndex(idx)
        if cfg.get("pick_method"):
            idx = self.cmbPickMethod.findText(cfg["pick_method"])
            if idx >= 0:
                self.cmbPickMethod.setCurrentIndex(idx)
        if cfg.get("save_dir"):
            self.save_dir = cfg["save_dir"]
        else:
            self.save_dir = os.path.join(os.getcwd(), "images")
        # 确保保存目录存在
        os.makedirs(self.save_dir, exist_ok=True)
        # 恢复手动修改的 β/η
        self._restore_fit_results(self._fit_results_tbd, cfg.get("fit_results_tbd", {}))
        self._restore_fit_results(self._fit_results_qbd, cfg.get("fit_results_qbd", {}))

    def _restore_fit_results(self, target_dict, saved: dict):
        """从保存的配置恢复到 fit_results 字典。"""
        for key_str, val in saved.items():
            # key_str is "(group, Vgs, Temp?, Area?)" from str(tuple)
            import ast
            try:
                key = ast.literal_eval(key_str)
                if isinstance(key, tuple) and len(key) >= 2:
                    target_dict[key] = {"beta": float(val["beta"]),
                                        "eta": float(val["eta"]),
                                        "n": 15, "r2_raw": 0, "r2_log": 0}
            except (ValueError, SyntaxError):
                continue

    def _save_config(self):
        """保存当前参数到 ConfigManager（含手动修改的 β/η）。"""
        self._cm.set("file_path", self.lblFilePath.text())
        self._cm.set("sheet_name", self.cmbSheetSelector.currentText())
        self._cm.set("work_voltage", str(self.editWorkVoltage.value()))
        self._cm.set("oxide_thickness", str(self.editOxideThickness.value()))
        self._cm.set("work_temperature", str(self.editWorkTemp.value()))
        self._cm.set("tddb_model", self.cmbTDDBModel.currentText())
        self._cm.set("pick_method", self.cmbPickMethod.currentText())
        self._cm.set("save_dir", self.save_dir)
        # 保存手动修改的 β/η
        self._cm.set("fit_results_tbd", {str(k): {"beta": v["beta"], "eta": v["eta"]}
                                          for k, v in self._fit_results_tbd.items()})
        self._cm.set("fit_results_qbd", {str(k): {"beta": v["beta"], "eta": v["eta"]}
                                          for k, v in self._fit_results_qbd.items()})
        self._cm.save()

    # ── Weibull 拟合核心 ────────────────────────────────────────

    def _on_weibull_fit_clicked(self):
        """点击 weibull 拟合按钮 → 始终从原始数据重新拟合，丢弃手动修改。"""
        self._on_weibull_fit()

    _last_fit_data_version: int = -1

    def _on_data_type_changed(self):
        """TBD/QBD 切换时重新拟合。"""
        if not self._initialized:
            return
        self._current_data_type = "TBD" if self.rdoTBD.isChecked() else "QBD"
        if self._data is not None:
            self._on_weibull_fit()

    def _on_slope_changed(self):
        """统一斜率勾选状态变化 → 重新拟合。"""
        if not self._initialized or self._data is None:
            return
        self._on_weibull_fit()

    def _on_weibull_fit(self):
        """执行 Weibull 拟合（带 reentrant guard + 异常捕获）。"""
        if self._fitting_in_progress:
            return
        self._fitting_in_progress = True
        try:
            new_results = self._do_weibull_fit()
            if new_results is not None:
                self._fit_results = new_results
                self._populate_fit_result_tab()
                self._populate_raw_params_tab()
                self._draw_weibull_plot()
                self._last_fit_data_version = self._data_version
                self.logger.info(
                    f"Weibull 拟合完成: {len(self._fit_results)} 个条件"
                )
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.logger.error(f"Weibull 拟合失败:\n{tb}")
            QMessageBox.critical(self, "拟合错误",
                f"Weibull 拟合失败：{e}\n\n详情请查看日志。")
        finally:
            self._fitting_in_progress = False

    def _do_weibull_fit(self) -> dict | None:
        """执行 Weibull 拟合核心逻辑。返回 new_results 字典，失败返回 None。"""
        if self._data is None:
            QMessageBox.warning(self, "提示", "请先选择数据文件")
            return None

        df = self._data.copy()
        # 过滤 ignore 行
        if "ignore" in df.columns:
            df = df[df["ignore"] != 1].copy()

        # 确定分析列：TBD 或 QBD
        use_tbd = self.rdoTBD.isChecked()
        data_col = "TBD" if use_tbd else "QBD"
        self._current_data_type = data_col

        if data_col not in df.columns:
            QMessageBox.warning(self, "提示", f"数据中缺少 '{data_col}' 列")
            return

        # 过滤空值
        df = df.dropna(subset=[data_col]).copy()
        if len(df) < 1:
            QMessageBox.warning(self, "提示", "无有效数据")
            return

        # 确定分组键
        group_key = "group" if "group" in df.columns else None
        cond_cols = ["Vgs"]
        if "Temperature" in df.columns:
            cond_cols.append("Temperature")
        if "Gate Oxide Area" in df.columns:
            cond_cols.append("Gate Oxide Area")

        new_results: dict = {}
        self._beta_data = {"Vgs": [], "Temperature": [], "Area": [],
                           "beta": [], "group": []}

        groups = df[group_key].unique() if group_key else ["All"]
        unify = self.chkUnifySlope.isChecked()

        for grp in groups:
            if group_key:
                grp_df = df[df[group_key] == grp]
            else:
                grp_df = df

            # 每个条件独立拟合
            conditions_data = {}
            for (conds), sub_df in grp_df.groupby(cond_cols):
                vals = sub_df[data_col].values
                if len(vals) < 2:
                    continue
                key = tuple(conds) if isinstance(conds, tuple) else (conds,)
                conditions_data[key] = vals

            if unify and len(conditions_data) > 1:
                # 统一斜率
                unified = fit_unified_slope(conditions_data)
                for key, data_vals in conditions_data.items():
                    eta = unified["etas"].get(key, 0)
                    cond_result = {
                        "beta": unified["beta"],
                        "eta": eta,
                        "r2_raw": 0.0,
                        "r2_log": 0.0,
                        "n": len(data_vals),
                        "eta_unified": eta,
                        "raw_vals": data_vals,
                    }
                    # 独立计算 R²
                    plot_d = weibull_plot_data(data_vals)
                    ln_t = plot_d["ln_t"]
                    wp = plot_d["weibull_prob"]
                    fitted = unified["beta"] * (ln_t - np.log(eta))
                    ss_res = np.sum((wp - fitted) ** 2)
                    ss_tot = np.sum((wp - np.mean(wp)) ** 2)
                    cond_result["r2_log"] = 1 - ss_res / ss_tot if ss_tot > 0 else 0
                    # 计算 r2_raw（原始尺度：经验 CDF vs 拟合 CDF）
                    empirical_f = plot_d["ranks"]
                    fitted_f = 1 - np.exp(-(plot_d["tbd"] / eta) ** unified["beta"])
                    res_raw = empirical_f - fitted_f
                    ss_res_raw = np.sum(res_raw ** 2)
                    ss_tot_raw = np.sum((empirical_f - np.mean(empirical_f)) ** 2)
                    cond_result["r2_raw"] = 1 - ss_res_raw / ss_tot_raw if ss_tot_raw > 0 else 0
                    new_results[(str(grp), *key)] = cond_result
            else:
                # 独立斜率
                for key, data_vals in conditions_data.items():
                    cond_result = fit_weibull(data_vals)
                    cond_result["raw_vals"] = data_vals
                    new_results[(str(grp), *key)] = cond_result

            # 收集 β 诊断数据
            if group_key:
                for key in conditions_data:
                    v = float(key[0]) if isinstance(key, tuple) else float(key)
                    t = float(key[1]) if isinstance(key, tuple) and len(key) > 1 else 25.0
                    a = float(key[2]) if isinstance(key, tuple) and len(key) > 2 else 1.0
                    self._beta_data["Vgs"].append(v)
                    self._beta_data["Temperature"].append(t)
                    self._beta_data["Area"].append(a)
                    self._beta_data["beta"].append(
                        new_results[(str(grp), *key)]["beta"]
                    )
                    self._beta_data["group"].append(str(grp))

        #[ display 和日志已移至 _on_weibull_fit ]
        return new_results if new_results else None

    # ── 拟合结果展示 ───────────────────────────────────────────

    def _populate_fit_result_tab(self):
        """在「拟合结果」子 tab 的 scrollArea 中动态生成条件 groupbox。"""
        try:
            scroll_content = self.saFitResultContent
            # 重用已有布局（不删除布局对象，否则 deleteLater 异步导致新布局装不上）
            old_layout = scroll_content.layout()
            if old_layout:
                while old_layout.count():
                    item = old_layout.takeAt(0)
                    if item and item.widget():
                        item.widget().deleteLater()
                layout = old_layout  # 复用旧布局
            else:
                layout = QVBoxLayout(scroll_content)
            layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            use_tbd = self.rdoTBD.isChecked()
            unit = "s" if use_tbd else "C"

            for key, result in sorted(self._fit_results.items()):
                grp_name, v = key[0], key[1]
                t = key[2] if len(key) > 2 else None
                area = key[3] if len(key) > 3 else None
                title_parts = [f"Vgs={v}V"]
                if t is not None:
                    title_parts.append(f"T={t}℃")
                if area is not None:
                    title_parts.append(f"A={area}")
                title = f"{grp_name} | {' | '.join(title_parts)}"

                gb = QGroupBox(title)
                gb_layout = QHBoxLayout(gb)

                # 回归方程
                beta = result['beta']
                formula_label = QLabel(
                    f"Y = {beta:.4f}·X + ln(-ln(1-F))\n"
                    f"R²_raw = {result['r2_raw']:.4f}\n"
                    f"R²_log = {result['r2_log']:.4f}"
                )
                gb_layout.addWidget(formula_label)

                # β
                bl = QVBoxLayout()
                bl.addWidget(QLabel(f"β:"))
                be = QLineEdit(f"{beta:.4f}")
                be.setObjectName(f"beta_{'_'.join(str(k) for k in key)}")
                be.editingFinished.connect(self._on_fit_param_edited)
                bl.addWidget(be)
                gb_layout.addLayout(bl)

                # η
                el = QVBoxLayout()
                el.addWidget(QLabel(f"η ({unit}):"))
                ee = QLineEdit(f"{_fmt_eta(result['eta'])}")
                ee.setObjectName(f"eta_{'_'.join(str(k) for k in key)}")
                ee.editingFinished.connect(self._on_fit_param_edited)
                el.addWidget(ee)
                gb_layout.addLayout(el)

                layout.addWidget(gb)
        except Exception as e:
            self.logger.error(f"拟合结果展示失败: {e}", exc_info=True)

    def _on_fit_result_tab_changed(self, index: int):
        """切换「拟合结果」/「原始数据」tab 时刷新。"""
        if index == 0 and self._fit_results:
            self._populate_fit_result_tab()
            self._draw_weibull_plot()

    def _on_fit_param_edited(self):
        """用户编辑了拟合结果中的 β/η。统一斜率时改 β 全局同步。"""
        sender = self.sender()
        if not sender:
            return
        name = sender.objectName()
        if not name:
            return
        parts = name.split("_", 1)
        if len(parts) != 2:
            return
        param_type = parts[0]
        try:
            val = float(sender.text())
        except ValueError:
            return

        # 找到匹配的 fit_key
        target_key = None
        for fit_key in self._fit_results:
            if "_".join(str(k) for k in fit_key) == parts[1]:
                target_key = fit_key
                break
        if target_key is None:
            return

        unify = self.chkUnifySlope.isChecked()

        if param_type == "beta" and unify:
            # 统一斜率下改 β → 所有条件同步
            same_group = target_key[0]
            for k in self._fit_results:
                if k[0] == same_group:
                    self._fit_results[k]["beta"] = val
                    # 重新计算 R²（用新 β、旧 η）
                    self._recalc_r2(k)
        elif param_type == "beta":
            self._fit_results[target_key]["beta"] = val
            self._recalc_r2(target_key)
        else:
            self._fit_results[target_key]["eta"] = val
            self._recalc_r2(target_key)

        self._draw_weibull_plot()
        self._sync_raw_params_tab()
        # 同步刷新拟合结果 groupbox 的显示
        self._populate_fit_result_tab()

    def _recalc_r2(self, key):
        """用缓存的 β/η 重新计算该条件的 R²。"""
        result = self._fit_results[key]
        beta, eta = result["beta"], result["eta"]
        data_vals = self._get_data_for_key(key)
        if data_vals is None or len(data_vals) < 2:
            return
        from core.tddb.weibull_fitter import weibull_plot_data
        pd_ = weibull_plot_data(data_vals)
        ln_t, wp = pd_["ln_t"], pd_["weibull_prob"]
        fitted = beta * (ln_t - np.log(eta))
        ss_res = np.sum((wp - fitted) ** 2)
        ss_tot = np.sum((wp - np.mean(wp)) ** 2)
        result["r2_log"] = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        # Raw R²
        ranks = pd_["ranks"]
        fitted_f = 1 - np.exp(-(np.sort(data_vals) / eta) ** beta)
        res_raw = ranks - fitted_f
        ss_res_raw = np.sum(res_raw ** 2)
        ss_tot_raw = np.sum((ranks - np.mean(ranks)) ** 2)
        result["r2_raw"] = 1 - ss_res_raw / ss_tot_raw if ss_tot_raw > 0 else 0

    # ── Weibull 绘图 ───────────────────────────────────────────

    def _draw_weibull_plot(self):
        """绘制 Weibull 分布图——每 group 一行，各条件散点+拟合线独立图例可分别开关，颜色配对。"""
        self._current_plot_mode = "weibull"
        if not self._fit_results or self._data is None:
            return

        use_tbd = self.rdoTBD.isChecked()
        data_col = "TBD" if use_tbd else "QBD"
        unit = "s" if use_tbd else "C"

        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        groups = sorted(set(k[0] for k in self._fit_results))
        n_groups = len(groups)

        fig = make_subplots(
            rows=n_groups, cols=1,
            subplot_titles=[f"Group: {g}" for g in groups],
            vertical_spacing=max(0.03, min(0.15, 1.0 / max(n_groups - 1, 1) - 0.01)),
        )

        # 调色板——每个条件一个颜色
        palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
                   "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]

        color_idx = 0
        custom_cols = [c for c in ["PART_ID", "Vgs", "Temperature", "Gate Oxide Area",
                                    data_col, "ignore", "group", "老化板通道", "comment"]
                       if self._data is not None and c in self._data.columns]

        for gi, grp in enumerate(groups):
            row = gi + 1
            for key, result in sorted(self._fit_results.items()):
                if key[0] != grp:
                    continue
                parts = [f"Vgs={key[1]}V"]
                if len(key) > 2:
                    parts.append(f"T={key[2]}℃")
                if len(key) > 3:
                    parts.append(f"A={key[3]}")
                cond_name = " | ".join(parts)
                beta = result["beta"]
                eta = result["eta"]
                r2 = result.get("r2_log", 0)

                data_vals = self._get_data_for_key(key, data_col)
                if data_vals is None or len(data_vals) < 2:
                    continue
                plot_d = weibull_plot_data(data_vals)
                color = palette[color_idx % len(palette)]
                color_idx += 1

                # ---- 散点 trace: x=TBD（原始值，对数坐标） ----
                tbd_vals = plot_d["tbd"]  # 原始 TBD 值（非 ln）
                rows_info = self._get_rows_for_key(key, data_col)
                scatter = go.Scatter(
                    x=tbd_vals, y=plot_d["weibull_prob"],
                    mode="markers",
                    name=f"{cond_name} 数据  β={beta:.3f} η={_fmt_eta(eta)}{unit}",
                    marker=dict(size=7, color=color),
                    customdata=rows_info,
                    hovertemplate=(
                        "<b>数据点</b><br>" +
                        "<br>".join(f"<b>{col}:</b> %{{customdata[{i}]}}"
                                    for i, col in enumerate(custom_cols)) +
                        f"<br>{data_col}=%{{x:.4e}}<br>ln(-ln(1-F))=%{{y:.4f}}<extra></extra>"
                    ),
                    showlegend=True,
                    legend=f"legend{row}" if row > 1 else "legend",
                )
                fig.add_trace(scatter, row=row, col=1)

                # ---- 拟合线 (对数坐标上为直线) ----
                t_fit = np.logspace(np.log10(min(tbd_vals)), np.log10(max(tbd_vals)), 100)
                wp_fit = beta * (np.log(t_fit) - np.log(eta))
                fit_line = go.Scatter(
                    x=t_fit, y=wp_fit,
                    mode="lines",
                    name=f"{cond_name} 拟合  R²={r2:.4f}",
                    line=dict(dash="dash", width=2, color=color),
                    hovertemplate=(
                        f"<b>拟合</b><br>"
                        f"β={beta:.4f} η={_fmt_eta(eta)}{unit}<br>"
                        f"R²_log={r2:.4f}<extra></extra>"
                    ),
                    showlegend=True,
                    legend=f"legend{row}" if row > 1 else "legend",
                )
                fig.add_trace(fit_line, row=row, col=1)

            # 每行独立图例
            leg_name = f"legend{row}" if row > 1 else "legend"
            fig.update_layout({
                leg_name: {
                    "x": 1.02, "y": 1 - (gi / n_groups),
                    "xanchor": "left", "yanchor": "top",
                    "font": dict(size=10),
                    "title": dict(text=f"Group: {grp}", font=dict(size=11)),
                }
            })
            fig.update_xaxes(title_text=f"{data_col} ({unit})", type="log", row=row, col=1)
            fig.update_yaxes(title_text="ln(-ln(1-F))", row=row, col=1)

        plot_height = max(400 * n_groups, 450)
        fig.update_layout(
            title_text=f"Weibull Distribution — {data_col} ({unit})",
            template="plotly_white", hovermode="closest",
            width=900, height=plot_height,
            margin=dict(l=60, r=220, t=50, b=60),
        )
        _render_html_in_view(self.wvWeibullPlot, fig, self.save_dir, "TDDB-weibullplot")

    def _get_data_for_key(self, key, data_col="TBD"):
        """从原始数据中提取指定 key 的 TBD/QBD 值。"""
        if self._data is None:
            return None
        df = self._data.copy()
        if "ignore" in df.columns:
            df = df[df["ignore"] != 1]
        grp_name = key[0]
        if self._has_col(df, "group"):
            df = df[df["group"] == grp_name]
        for i, col in enumerate(["Vgs", "Temperature", "Gate Oxide Area"]):
            if i + 1 < len(key) and self._has_col(df, col):
                df = df[df[col] == key[i + 1]]
        vals = df[data_col].dropna().values
        return vals if len(vals) >= 2 else None

    def _get_data_for_key_with_hover(self, key, data_col="TBD"):
        """提取数据 + hover 文本（PART_ID, 通道等）。"""
        if self._data is None:
            return None, None
        df = self._data.copy()
        if "ignore" in df.columns:
            df = df[df["ignore"] != 1]
        grp_name = key[0]
        if self._has_col(df, "group"):
            df = df[df["group"] == grp_name]
        for i, col in enumerate(["Vgs", "Temperature", "Gate Oxide Area"]):
            if i + 1 < len(key) and self._has_col(df, col):
                df = df[df[col] == key[i + 1]]
        sub = df.dropna(subset=[data_col])
        vals = sub[data_col].values
        if len(vals) < 2:
            return None, None

        # 构建 hover 文本
        hover_parts = []
        if "PART_ID" in sub.columns:
            hover_parts.append(sub["PART_ID"].astype(str))
        if "老化板通道" in sub.columns:
            hover_parts.append(sub["老化板通道"].astype(str))
        if "comment" in sub.columns:
            hover_parts.append(sub["comment"].astype(str))
        if hover_parts:
            hover_texts = ["<br>".join(
                f"{col}: {row[i]}" for i, col in enumerate(
                    [c for c in ["PART_ID", "老化板通道", "comment"] if c in sub.columns]
                )
            ) for _, row in sub.iterrows()]
        else:
            hover_texts = None

        return vals, hover_texts

    def _get_rows_for_key(self, key, data_col="TBD"):
        """返回每个数据点对应原始行的字段列表（用于 customdata）。"""
        if self._data is None:
            return None
        df = self._data.copy()
        if "ignore" in df.columns:
            df = df[df["ignore"] != 1]
        grp_name = key[0]
        if self._has_col(df, "group"):
            df = df[df["group"] == grp_name]
        for i, col in enumerate(["Vgs", "Temperature", "Gate Oxide Area"]):
            if i + 1 < len(key) and self._has_col(df, col):
                df = df[df[col] == key[i + 1]]
        sub = df.dropna(subset=[data_col]).sort_values(data_col)
        # 按 TBD/QBD 排序后，返回各行指定字段
        wanted = ["PART_ID", "Vgs", "Temperature", "Gate Oxide Area",
                   data_col, "ignore", "group", "老化板通道", "comment"]
        cols_in = [c for c in wanted if c in sub.columns]
        rows = []
        for _, row in sub.iterrows():
            rows.append([row[c] if not pd.isna(row.get(c)) else "" for c in cols_in])
        return rows if rows else None

    @staticmethod
    def _has_col(df, name):
        return name in df.columns

    # ── β 诊断 ─────────────────────────────────────────────────

    def _on_beta_diagnostic(self):
        """切换到 β 诊断图。"""
        if not self._beta_data or len(self._beta_data["Vgs"]) < 3:
            QMessageBox.warning(self, "提示", "数据不足，至少需要 3 个条件")
            return

        try:
            fig_vgs = make_beta_vs_vgs_plot(self._beta_data)
            fig_temp = make_beta_vs_temp_plot(self._beta_data)
            fig_area = make_beta_vs_area_plot(self._beta_data)

            import plotly.graph_objects as go
            from plotly.subplots import make_subplots

            fig = make_subplots(rows=1, cols=3,
                                subplot_titles=("β vs Vgs", "β vs Temp", "β vs Area"))
            for trace in fig_vgs.data:
                fig.add_trace(trace, row=1, col=1)
            for trace in fig_temp.data:
                fig.add_trace(trace, row=1, col=2)
            for trace in fig_area.data:
                fig.add_trace(trace, row=1, col=3)

            fig.update_layout(
                title="β Diagnostics",
                template="plotly_white",
                showlegend=True,
                height=400,
            )
            _render_html_in_view(self.wvWeibullPlot, fig, self.save_dir, "TDDB-beta-diagnos")
            self._current_plot_mode = "beta"
        except Exception as e:
            self.logger.error(f"β 诊断绘图失败: {e}")
            QMessageBox.critical(self, "错误", f"β 诊断绘图失败: {e}")

        # 切回 Weibull 图的逻辑通过再次点击"weibull拟合"按钮实现
        # 用户点击"β诊断"显示诊断图，重新拟合时自动切回

    # ── 参数编辑表 ─────────────────────────────────────────────

    def _populate_raw_params_tab(self):
        """填充「原始数据查看」tab 的参数编辑表（显示 TBD 和 QBD 各自的 η）。"""
        all_keys = set(self._fit_results_tbd.keys()) | set(self._fit_results_qbd.keys())
        if not all_keys:
            return
        tbl = self.tblRawParams
        tbl.setColumnCount(13)
        tbl.setHorizontalHeaderLabels([
            "Group", "Vgs", "Temp", "Area",
            "β", "η_TBD", "η_QBD",
            "R²_raw", "R²_log",
            "γ(cm/MV)", "G(MV/cm)", "βv(1/V)", "Ea(eV)",
        ])
        tbl.setRowCount(len(all_keys))
        tbl.blockSignals(True)
        for i, key in enumerate(sorted(all_keys)):
            r_tbd = self._fit_results_tbd.get(key)
            r_qbd = self._fit_results_qbd.get(key)
            r_cur = r_tbd or r_qbd  # preferred for β/R²
            tbl.setItem(i, 0, QTableWidgetItem(str(key[0])))
            tbl.setItem(i, 1, QTableWidgetItem(str(key[1])))
            tbl.setItem(i, 2, QTableWidgetItem(str(key[2]) if len(key) > 2 else ""))
            tbl.setItem(i, 3, QTableWidgetItem(str(key[3]) if len(key) > 3 else ""))
            # β (editable)
            beta_val = r_cur["beta"] if r_cur else 2.0
            item = QTableWidgetItem(f"{beta_val:.4f}")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            tbl.setItem(i, 4, item)
            # η_TBD (editable)
            eta_tbd = r_tbd["eta"] if r_tbd else 0.0
            item = QTableWidgetItem(f"{eta_tbd:.4f}")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            tbl.setItem(i, 5, item)
            # η_QBD (editable)
            eta_qbd = r_qbd["eta"] if r_qbd else 0.0
            item = QTableWidgetItem(f"{_fmt_eta(eta_qbd)}" if eta_qbd else "0")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            tbl.setItem(i, 6, item)
            # R² (read-only)
            for ci, val in [(7, r_cur.get("r2_raw", 0) if r_cur else 0),
                            (8, r_cur.get("r2_log", 0) if r_cur else 0)]:
                item = QTableWidgetItem(f"{val:.4f}")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                tbl.setItem(i, ci, item)
            # γ, G, βv, Ea (editable, placeholder)
            for ci in [9, 10, 11, 12]:
                item = QTableWidgetItem("0.0")
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                tbl.setItem(i, ci, item)
        tbl.blockSignals(False)
        tbl.resizeColumnsToContents()
        tbl.horizontalHeader().setStretchLastSection(True)

    def _sync_raw_params_tab(self):
        """同步参数编辑表中的 β/η 值（不重建立表结构）。"""
        tbl = self.tblRawParams
        tbl.blockSignals(True)
        for i, (key, result) in enumerate(sorted(self._fit_results.items())):
            for ci, val in [(4, result["beta"]), (5, result["eta"])]:
                item = tbl.item(i, ci)
                if item:
                    item.setText(f"{val:.4f}")
        tbl.blockSignals(False)

    def _on_param_edited(self, item: QTableWidgetItem):
        """用户编辑参数表 → 同步到缓存。"""
        row = item.row()
        col = item.column()
        tbl = self.tblRawParams
        if row >= len(self._fit_results) or col not in (4, 5, 9, 10, 11, 12):
            return

        key = list(sorted(self._fit_results.keys()))[row]
        try:
            val = float(item.text())
        except ValueError:
            return

        col_map = {4: "beta", 5: "eta", 9: "gamma", 10: "g", 11: "beta_v", 12: "ea"}
        param_name = col_map.get(col)
        if param_name in ("beta", "eta"):
            self._fit_results[key][param_name] = val
            self._draw_weibull_plot()
            # 更新拟合结果 tab 的编辑框
            self._populate_fit_result_tab()

    def _sync_model_params_to_table(self):
        """寿命计算后将模型参数回填到原始数据查看表。"""
        if not self._last_model_params:
            return
        tbl = self.tblRawParams
        tbl.blockSignals(True)
        for i in range(tbl.rowCount()):
            grp_item = tbl.item(i, 0)
            if grp_item is None:
                continue
            grp = grp_item.text()
            mp = self._last_model_params.get(grp)
            if mp is None:
                continue
            for ci, key in [(9, "gamma"), (10, "g"), (11, "beta_v"), (12, "ea")]:
                val = mp.get(key, 0)
                item = tbl.item(i, ci)
                if item:
                    item.setText(f"{val:.4e}" if abs(val) < 0.01 else f"{val:.4f}")
        tbl.blockSignals(False)

    # ── 寿命计算 ───────────────────────────────────────────────

    def _on_calc(self):
        """执行寿命/失效率计算。"""
        if not self._fit_results:
            QMessageBox.warning(self, "提示", "请先进行 Weibull 拟合")
            return

        try:
            v_op = self.editWorkVoltage.value()
            tox = self.editOxideThickness.value()
            t_op = self.editWorkTemp.value()
            v_assess = self.editStressVoltage.value()
            t_assess = self.editStressTemp.value()
        except (ValueError, AttributeError):
            QMessageBox.warning(self, "提示", "请填写有效的参数")
            return

        model = self.cmbTDDBModel.currentText()
        pick_method = self.cmbPickMethod.currentIndex()  # 0=weibull, 1=raw

        # 各组的 η 按 key 收集
        groups_data: dict[str, dict] = {}
        for key, result in self._fit_results.items():
            grp = key[0]
            if grp not in groups_data:
                groups_data[grp] = {"v": [], "eta": [], "temp": []}
            v = float(key[1])
            eta = result["eta"]
            # 原始数据平滑取点：对 TBD 排序→中位秩→PCHIP 插值→F=63.2% 处 η
            if pick_method == 1:
                raw_vals = result.get("raw_vals")
                if raw_vals is not None and len(raw_vals) > 1:
                    sorted_vals = np.sort(raw_vals)
                    n = len(sorted_vals)
                    ranks = (np.arange(1, n + 1, dtype=float) - 0.3) / (n + 0.4)
                    from scipy.interpolate import PchipInterpolator
                    interp = PchipInterpolator(ranks, sorted_vals)
                    eta = float(interp(0.6321205588285577))  # 1 - 1/e
            # 缓存各 key 对应的实际 η（平滑或 Weibull），供表格显示用
            self._last_etas[key] = eta
            t = float(key[2]) if len(key) > 2 else 25.0
            beta = result["beta"]
            groups_data[grp]["v"].append(v)
            groups_data[grp]["eta"].append(eta)
            groups_data[grp]["temp"].append(t)

        # 每个 group 独立拟合模型
        life_results = []
        fr_results = []

        for grp, gd in groups_data.items():
            v_arr = np.array(gd["v"])
            eta_arr = np.array(gd["eta"])
            t_arr = np.array(gd["temp"])

            # 确定是否有温度变化
            unique_temps = np.unique(t_arr)
            has_multiple_temps = len(unique_temps) > 1

            # 获取 beta（取第一个条件的 β）
            beta_val = self._fit_results[list(self._fit_results.keys())[0]]["beta"]

            if has_multiple_temps:
                # 多温度：先用 E-Arrhenius 拟合温度效应得到 Ea，再用选定电压模型
                ea_result = fit_e_arrhenius(v_arr, t_arr, eta_arr, tox)
                ea = ea_result["ea"]
                a_const = ea_result["a"]
                gamma_fit = ea_result.get("gamma", 0)

                # 用选定模型外推（将温度效应剥离后拟合电压模型）
                if model == "E模型":
                    model_result = {"gamma": gamma_fit, "a": a_const, "ea": ea,
                                    "r2": ea_result["r2"]}
                elif model == "1/E模型":
                    # 1/E 模型拟合（温度修正后）
                    t_k = np.where(t_arr < 100, t_arr + 273.15, t_arr)
                    inv_t = 1.0 / (8.617333262e-5 * t_k)
                    # 修正到工作温度
                    t_op_k = t_op + 273.15 if t_op < 100 else t_op
                    eta_corrected = eta_arr * np.exp(-ea * (inv_t - 1.0/(8.617333262e-5 * t_op_k)))
                    m = fit_1e_model(v_arr, eta_corrected, tox)
                    model_result = {"g": m["g"], "tau_0": m["tau_0"],
                                    "ea": ea, "r2": m["r2"]}
                elif model == "√E模型":
                    t_k = np.where(t_arr < 100, t_arr + 273.15, t_arr)
                    inv_t = 1.0 / (8.617333262e-5 * t_k)
                    t_op_k = t_op + 273.15 if t_op < 100 else t_op
                    eta_corrected = eta_arr * np.exp(-ea * (inv_t - 1.0/(8.617333262e-5 * t_op_k)))
                    m = fit_sqrt_e_model(v_arr, eta_corrected, tox)
                    model_result = {"s": m["s"], "a": m["a"],
                                    "ea": ea, "r2": m["r2"]}
                else:
                    # V 模型
                    t_k = np.where(t_arr < 100, t_arr + 273.15, t_arr)
                    inv_t = 1.0 / (8.617333262e-5 * t_k)
                    t_op_k = t_op + 273.15 if t_op < 100 else t_op
                    eta_corrected = eta_arr * np.exp(-ea * (inv_t - 1.0/(8.617333262e-5 * t_op_k)))
                    m = fit_v_model(v_arr, eta_corrected)
                    model_result = {"beta_v": m["beta_v"], "a": m["a"],
                                    "ea": ea, "r2": m["r2"]}
            else:
                # 单温度：用选定电压模型直接拟合
                if model == "E模型":
                    model_result = fit_e_model(v_arr, eta_arr, tox)
                elif model == "1/E模型":
                    model_result = fit_1e_model(v_arr, eta_arr, tox)
                elif model == "√E模型":
                    model_result = fit_sqrt_e_model(v_arr, eta_arr, tox)
                else:
                    model_result = fit_v_model(v_arr, eta_arr)

            # 预测工作电压下寿命
            if has_multiple_temps:
                # 多温度下统一用 E-Arrhenius 预测（含温度修正）
                eox = v_op / tox * 10.0
                t_op_k = t_op + 273.15 if t_op < 100 else t_op
                k = 8.617333262e-5
                if model == "1/E模型":
                    pred_eta = model_result["tau_0"] * np.exp(
                        model_result["g"] / eox + model_result["ea"] / (k * t_op_k))
                elif model == "V模型":
                    pred_eta = model_result["a"] * np.exp(
                        -model_result["beta_v"] * v_op + model_result["ea"] / (k * t_op_k))
                elif model == "√E模型":
                    pred_eta = model_result["a"] * np.exp(
                        -model_result["s"] * np.sqrt(eox) + model_result["ea"] / (k * t_op_k))
                else:
                    pred_eta = model_result["a"] * np.exp(
                        -model_result["gamma"] * eox + model_result["ea"] / (k * t_op_k))
            else:
                # 单温度：用选定模型直接预测
                model_short = {"E模型": "E", "1/E模型": "1E", "V模型": "V", "√E模型": "SQE"}[model]
                pred_eta = predict_lifetime(model_short, model_result, v_op, t_op, tox)

            use_tbd = self.rdoTBD.isChecked()
            unit = "s" if use_tbd else "C"

            # 寿命表：不同失效率下的寿命
            fr_levels = [0.632, 0.5, 0.001, 0.0001, 1e-5, 1e-6]
            life_row = {"group": grp}
            for fr in fr_levels:
                t_life = pred_eta * (-np.log(1 - fr)) ** (1.0 / beta_val)
                life_row[f"t@{fr}"] = t_life
            life_results.append(life_row)
            # 缓存 η/β 用于曲线绘制（不在表格中显示）
            self._last_curve_data[grp] = {"eta": pred_eta, "beta": beta_val}
            # 计算考核电压/温度下的 η_assess（与 pred_eta 同公式，换电压+温度）
            try:
                if has_multiple_temps:
                    eox_a = v_assess / tox * 10.0
                    t_assess_k = t_assess + 273.15 if t_assess < 100 else t_assess
                    k = 8.617333262e-5
                    if model == "1/E模型":
                        η_assess = model_result.get("tau_0", 0) * np.exp(
                            model_result.get("g", 0) / eox_a + model_result.get("ea", 0) / (k * t_assess_k))
                    elif model == "V模型":
                        η_assess = model_result.get("a", 0) * np.exp(
                            -model_result.get("beta_v", 0) * v_assess + model_result.get("ea", 0) / (k * t_assess_k))
                    elif model == "√E模型":
                        η_assess = model_result.get("a", 0) * np.exp(
                            -model_result.get("s", 0) * np.sqrt(eox_a) + model_result.get("ea", 0) / (k * t_assess_k))
                    else:
                        η_assess = model_result.get("a", 0) * np.exp(
                            -model_result.get("gamma", 0) * eox_a + model_result.get("ea", 0) / (k * t_assess_k))
                else:
                    η_assess = predict_lifetime(model_short, model_result, v_assess, t_op, tox)
                self._last_curve_data[grp]["eta_assess"] = float(η_assess)
            except Exception:
                self._last_curve_data[grp]["eta_assess"] = None
            # 缓存模型参数用于回填原始数据查看表
            self._last_model_params[grp] = {
                "gamma": model_result.get("gamma", 0),
                "g": model_result.get("g", 0),
                "s": model_result.get("s", 0),
                "beta_v": model_result.get("beta_v", 0),
                "ea": model_result.get("ea", 0),
            }

            # 失效率表：不同工作年限的累计失效率
            years = [1, 5, 10, 15, 20]
            seconds_per_year = 365.25 * 24 * 3600
            fr_row = {"group": grp}
            for yr in years:
                t_op_sec = yr * seconds_per_year
                cum_fr = predict_failure_rate(pred_eta, beta_val, t_op_sec)
                # 失效率的 CI（通过寿命 CI 间接计算）
                t_at_fr = pred_eta * (-np.log(1 - cum_fr)) ** (1.0 / beta_val) if cum_fr < 1 else pred_eta
                fr_row[f"{yr}yr"] = cum_fr
            fr_results.append(fr_row)

        # 显示结果
        self._populate_life_table(life_results)
        self._populate_fr_table(fr_results)
        self._draw_model_plot(groups_data, model_result, model, v_op, tox)
        self._update_formula_display()
        # 缓存按 group 聚合的结果（用于曲线绘制）
        self._last_life_results = life_results
        self._last_fr_results = fr_results
        # 回填模型参数到原始数据查看表
        self._sync_model_params_to_table()
        # 填充模型参数结果表
        self._populate_model_parameter_table(
            model, model_result, v_op, t_op, v_assess, t_assess, tox)

    def _populate_life_table(self, results: list[dict]):
        """填充寿命结果表。"""
        if not results:
            return
        tbl = self.tblLifeResult
        model = tbl.model()
        if model:
            # Clear existing model
            old_model = tbl.model()
            tbl.setModel(None)
            old_model.deleteLater()

        df = pd.DataFrame(results)
        from PySide6.QtCore import QAbstractTableModel, QModelIndex

        class PandasModel(QAbstractTableModel):
            def __init__(self, data):
                super().__init__()
                self._data = data
            def rowCount(self, parent=QModelIndex()): return len(self._data)
            def columnCount(self, parent=QModelIndex()): return len(self._data.columns)
            def data(self, index, role=Qt.ItemDataRole.DisplayRole):
                if role == Qt.ItemDataRole.DisplayRole:
                    val = self._data.iloc[index.row(), index.column()]
                    if isinstance(val, float):
                        return f"{val:.3e}"
                    return str(val)
                return None
            def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
                if role == Qt.ItemDataRole.DisplayRole:
                    if orientation == Qt.Orientation.Horizontal:
                        return self._data.columns[section]
                return None

        tbl.setModel(PandasModel(df))
        tbl.resizeColumnsToContents()

    def _populate_fr_table(self, results: list[dict]):
        """填充失效率结果表。"""
        if not results:
            return
        df = pd.DataFrame(results)
        tbl = self.tblFailResult
        model = tbl.model()
        if model:
            old_model = tbl.model()
            tbl.setModel(None)
            old_model.deleteLater()

        from PySide6.QtCore import QAbstractTableModel, QModelIndex

        class PandasModel(QAbstractTableModel):
            def __init__(self, data):
                super().__init__()
                self._data = data
            def rowCount(self, parent=QModelIndex()): return len(self._data)
            def columnCount(self, parent=QModelIndex()): return len(self._data.columns)
            def data(self, index, role=Qt.ItemDataRole.DisplayRole):
                if role == Qt.ItemDataRole.DisplayRole:
                    val = self._data.iloc[index.row(), index.column()]
                    if isinstance(val, float) and val < 1:
                        return f"{val:.4e}"
                    return str(val)
                return None
            def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
                if role == Qt.ItemDataRole.DisplayRole:
                    if orientation == Qt.Orientation.Horizontal:
                        return self._data.columns[section]
                return None

        tbl.setModel(PandasModel(df))
        tbl.resizeColumnsToContents()

    def _populate_model_parameter_table(
        self, model_name: str, model_result: dict,
        v_op: float, t_op: float, v_assess: float, t_assess: float,
        tox: float,
    ):
        """填充模型参数结果表 tblModelParameter。"""
        from PySide6.QtCore import QAbstractTableModel, QModelIndex

        # 确定当前模型的参数列
        model_short = {"E模型": "E", "1/E模型": "1E", "V模型": "V", "√E模型": "SQE"}.get(model_name, "E")
        if model_short == "E":
            param_keys = {"γ(cm/MV)": "gamma"}
        elif model_short == "1E":
            param_keys = {"G(MV/cm)": "g"}
        elif model_short == "SQE":
            param_keys = {"S(√(cm/MV))": "s"}
        else:
            param_keys = {"βv(1/V)": "beta_v"}

        # 收集每个条件的拟合结果
        rows = []
        model_short_calc = {"E模型": "E", "1/E模型": "1E", "V模型": "V", "√E模型": "SQE"}[model_name]

        for key, result in self._fit_results.items():
            grp = key[0]
            v = float(key[1])
            t = float(key[2]) if len(key) > 2 else None
            area = float(key[3]) if len(key) > 3 else None

            β = result.get("beta", None)
            η = self._last_etas.get(key, result.get("eta", None))
            r2_raw = result.get("r2_raw", None)
            r2_log = result.get("r2_log", None)

            # 从缓存读取 η_op 和 η_assess（已在 _on_calc 中按组正确计算）
            curve = self._last_curve_data.get(grp, {})
            η_op = curve.get("eta", None)
            η_assess = curve.get("eta_assess", None)
            af_op = η_op / η if (η is not None and η_op is not None and η > 0) else None
            af_assess = η_assess / η if (η is not None and η_assess is not None and η > 0) else None
            af_vassess_vop = η_op / η_assess if (η_assess is not None and η_op is not None and η_assess > 0) else None

            # 模型参数（只显示当前模型对应的，其余留空）
            gamma_val = model_result.get("gamma") if model_short == "E" else None
            g_val = model_result.get("g") if model_short == "1E" else None
            beta_v_val = model_result.get("beta_v") if model_short == "V" else None
            ea_val = model_result.get("ea", None)

            row = {
                "Group": grp,
                "Vgs(V)": v,
                "Temp(℃)": t if t is not None else "",
                "Area": area if area is not None else "",
                "β": β if (β is not None and β != 0) else "",
                "η_TBD(s)": η if (η is not None and η != 0) else "",
                "η_QBD(s)": "",  # QBD 填充在下面的另一个循环
                "R²_raw": r2_raw if r2_raw is not None else "",
                "R²_log": r2_log if r2_log is not None else "",
            }
            # 模型参数
            for label, key_name in param_keys.items():
                row[label] = model_result.get(key_name, "")
            # Ea 如有则显示
            if ea_val is not None and ea_val != 0:
                row["Ea(eV)"] = ea_val
            row["AF(考核)"] = af_op if (af_op is not None and af_op != 0) else ""
            row["AF(老化)"] = af_vassess_vop if (af_vassess_vop is not None and af_vassess_vop != 0) else ""
            rows.append(row)

        # 补充 QBD 结果
        if self._fit_results_qbd:
            for key, result in self._fit_results_qbd.items():
                for row in rows:
                    grp = row["Group"]
                    v = float(key[1])
                    t = float(key[2]) if len(key) > 2 else None
                    area = float(key[3]) if len(key) > 3 else None
                    if row["Vgs(V)"] == v and (t is None or row["Temp(℃)"] == t or row["Temp(℃)"] == ""):
                        η_qbd = result.get("eta", None)
                        row["η_QBD(s)"] = η_qbd if (η_qbd is not None and η_qbd != 0) else ""
                        β_qbd = result.get("beta", None)
                        if β_qbd is not None and β_qbd != 0 and row["β"] == "":
                            row["β"] = β_qbd
                        break

        if not rows:
            return

        df = pd.DataFrame(rows)
        # 排序
        df.sort_values(["Group", "Vgs(V)"], inplace=True, ignore_index=True)

        # 替换 0 为空字符串
        df = df.replace(0, "").replace(0.0, "")

        tbl = self.tblModelParameter
        old_model = tbl.model()
        if old_model:
            tbl.setModel(None)
            old_model.deleteLater()

        class PandasModel(QAbstractTableModel):
            def __init__(self, data):
                super().__init__()
                self._data = data
            def rowCount(self, parent=QModelIndex()): return len(self._data)
            def columnCount(self, parent=QModelIndex()): return len(self._data.columns)
            def data(self, index, role=Qt.ItemDataRole.DisplayRole):
                if role == Qt.ItemDataRole.DisplayRole:
                    val = self._data.iloc[index.row(), index.column()]
                    if isinstance(val, float):
                        if abs(val) < 0.01 or abs(val) >= 1e6:
                            return f"{val:.3e}"
                        return f"{val:.4f}"
                    return str(val) if val != "" else ""
                return None
            def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
                if role == Qt.ItemDataRole.DisplayRole:
                    if orientation == Qt.Orientation.Horizontal:
                        return self._data.columns[section]
                return None

        tbl.setModel(PandasModel(df))
        tbl.resizeColumnsToContents()

        # 同步填充 tblRawParams（可编辑版本）
        raw = self.tblRawParams
        raw.blockSignals(True)
        raw.clear()
        raw.setColumnCount(len(df.columns))
        raw.setHorizontalHeaderLabels(list(df.columns))
        raw.setRowCount(len(df))
        for r_idx in range(len(df)):
            for c_idx, col in enumerate(df.columns):
                val = df.iloc[r_idx, c_idx]
                txt = ""
                if isinstance(val, float):
                    if abs(val) < 0.01 or abs(val) >= 1e6:
                        txt = f"{val:.3e}"
                    else:
                        txt = f"{val:.4f}"
                elif val != "":
                    txt = str(val)
                item = QTableWidgetItem(txt)
                # β 和 η 列可编辑（列名包含 β 或 η）
                if any(k in col for k in ["β", "η", "AF"]):
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                raw.setItem(r_idx, c_idx, item)
        raw.blockSignals(False)
        raw.resizeColumnsToContents()

    def _draw_model_plot(self, groups_data, model_result, model_name, v_op, tox):
        """绘制模型拟合图。"""
        import plotly.graph_objects as go
        fig = go.Figure()

        for grp, gd in groups_data.items():
            v_arr = np.array(gd["v"])
            eta_arr = np.array(gd["eta"])
            fig.add_trace(go.Scatter(
                x=v_arr, y=eta_arr,
                mode="markers",
                name=f"{grp} (data)",
                marker=dict(size=10),
            ))

        # 拟合曲线
        v_fit = np.linspace(min(v_op, min(gd["v"])), max(gd["v"]), 100)
        model_short = {"E模型": "E", "1/E模型": "1E", "V模型": "V", "√E模型": "SQE"}.get(model_name, "E")
        eta_fit = []
        for v in v_fit:
            try:
                e = predict_lifetime(model_short, model_result, v, 25, tox)
                eta_fit.append(e)
            except Exception:
                eta_fit.append(np.nan)
        fig.add_trace(go.Scatter(
            x=v_fit, y=eta_fit,
            mode="lines",
            name=f"{model_name} fit",
            line=dict(dash="dash", color="red"),
        ))

        # 工作点
        eta_op = predict_lifetime(model_short, model_result, v_op, 25, tox)
        fig.add_trace(go.Scatter(
            x=[v_op], y=[eta_op],
            mode="markers",
            name=f"Work point ({v_op}V)",
            marker=dict(size=14, color="green", symbol="star"),
        ))

        fig.update_layout(
            title=f"{model_name} Fit — η vs V",
            xaxis_title="Voltage / V",
            yaxis_title="η (characteristic life)",
            yaxis_type="log",
            template="plotly_white",
        )
        _render_html_in_view(self.wvModelPlot, fig, self.save_dir, "TDDB-model-plot")

    # ── 公式显示 ───────────────────────────────────────────────

    def _update_formula_display(self):
        """更新公式 label 的显示（从预渲染 PNG 加载）。"""
        model = self.cmbTDDBModel.currentText()
        descs = {
            "E模型": "E 模型：η = A·exp(-γ·Eox)\nEox = V/Tox (MV/cm)，γ 为电场加速因子",
            "1/E模型": "1/E 模型：η = τ₀·exp(G/Eox)\nG 为击穿场强因子 (MV/cm)",
            "V模型": "V 模型：η = A·exp(-βv·V)\nβv 为电压加速因子 (1/V)",
            "√E模型": "√E 模型：η = A·exp(-S·√Eox)\nS 为 sqrt(E) 加速因子 (√(cm/MV))",
        }
        model_key = _FORMULA_MODEL_MAP.get(model)
        try:
            if model_key:
                life_pix = _load_formula_pixmap(f"life_{model_key}")
                if life_pix:
                    self.lblLifeFormula.setPixmap(life_pix)
                    self.lblLifeFormula.setToolTip(descs.get(model, ""))
                else:
                    self.lblLifeFormula.setText(f"{model} — 寿命公式")

                fail_pix = _load_formula_pixmap("fail_common")
                if fail_pix:
                    self.lblFailFormula.setPixmap(fail_pix)
                    self.lblFailFormula.setToolTip("F(t): 累计失效率, t: 工作时间")
                else:
                    self.lblFailFormula.setText("F(t) — 失效率公式")
            else:
                self.lblLifeFormula.clear()
                self.lblFailFormula.clear()
        except Exception as e:
            self.logger.warning(f"公式图片加载失败: {e}")
            self.lblLifeFormula.clear()
            self.lblFailFormula.clear()

    # ── 帮助弹窗 ───────────────────────────────────────────────

    def _on_life_help(self):
        """寿命计算方法说明。"""
        model = self.cmbTDDBModel.currentText()
        texts = {
            "E模型": (
                "📐 E 模型 (E-model)\n\n"
                "公式：η = A · exp(-γ · Eox)\n"
                "其中 Eox = V/Tox (MV/cm), V 单位为 V, Tox 单位为 nm\n\n"
                "物理意义：栅氧电场加速击穿过程，电场越大寿命越短。\n"
                "γ 为电场加速因子 (cm/MV)，典型值 1-3。\n\n"
                "外推方法：对 ln(η) vs Eox 做线性回归，\n"
                "斜率 = -γ，截距 = ln(A)。\n\n"
                "置信区间：基于 Fisher matrix 近似，\n"
                "用 Delta method 传播 β 和 η 的不确定性到寿命估计。"
            ),
            "1/E模型": (
                "📐 1/E 模型 (1/E-model)\n\n"
                "公式：η = τ₀ · exp(G / Eox)\n\n"
                "物理意义：基于 Fowler-Nordheim 隧穿机制，\n"
                "G 为击穿场强因子 (MV/cm)。\n\n"
                "外推方法：对 ln(η) vs 1/Eox 做线性回归。"
            ),
            "V模型": (
                "📐 V 模型 (V-model)\n\n"
                "公式：η = A · exp(-βv · V)\n\n"
                "物理意义：忽略 Tox 影响，直接对电压做指数拟合。\n"
                "βv 为电压加速因子 (1/V)。\n\n"
                "外推方法：对 ln(η) vs V 做线性回归。"
            ),
        }
        msg = QMessageBox(self)
        msg.setWindowTitle("寿命计算方法说明")
        msg.setText(texts.get(model, "未知模型"))
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def _on_fail_help(self):
        """失效率计算方法说明。"""
        msg = QMessageBox(self)
        msg.setWindowTitle("失效率计算方法说明")
        msg.setText(
            "📐 Weibull 失效率计算\n\n"
            "公式：F(t) = 1 - exp(-(t/η)^β)\n\n"
            "其中：\n"
            "  · t — 工作时间（与 η 单位一致）\n"
            "  · η — Weibull 特征寿命（63.2% 失效对应时间）\n"
            "  · β — Weibull 斜率（形状参数）\n\n"
            "工作年限换算：\n"
            "  1 年 = 365.25 × 24 × 3600 = 31,557,600 秒\n\n"
            "置信区间：通过寿命 CI 间接估计，\n"
            "方法为 Delta method (α=0.05)。"
        )
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    # ── 寿命-失效率曲线 ────────────────────────────────────────

    def _on_plot_life_fr(self):
        """在右边 wvModelPlot 绘制寿命 vs 失效率曲线 + 95% CI。"""
        if not self._last_curve_data:
            QMessageBox.warning(self, "提示", "请先计算寿命")
            return
        import plotly.graph_objects as go
        fig = go.Figure()
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

        for gi, (grp, cd) in enumerate(sorted(self._last_curve_data.items())):
            eta, beta = cd["eta"], cd["beta"]
            color = colors[gi % len(colors)]

            # 0～2×η 线性区间，密集点保证曲线光滑
            t_max = max(eta * 3, 1.0)
            t_vals = np.linspace(0, t_max, 500)
            fr_vals = np.where(t_vals > 0, 1 - np.exp(-(t_vals / eta) ** beta), 0.0)

            fig.add_trace(go.Scatter(
                x=t_vals, y=fr_vals, mode="lines", name=grp,
                line=dict(color=color, width=2),
                hovertemplate=f"<b>{grp}</b><br>寿命=%{{x:.2e}}s<br>失效率=%{{y:.4f}}<extra></extra>",
            ))

            # 完整95% CI：密集采样
            # 完整95% CI：密集采样
            n_ci = 50
            t_ci = np.linspace(0, t_max, n_ci)
            ci_lo, ci_hi = [], []
            for t in t_ci:
                if t <= 0:
                    ci_lo.append(0)
                    ci_hi.append(0)
                    continue
                fr_ref = 1 - np.exp(-(t / eta) ** beta)
                if fr_ref >= 0.999:
                    ci_lo.append(0)
                    ci_hi.append(1)
                    continue
                lo, hi = lifetime_ci(eta, beta, fr_ref, n=30, alpha=0.05)
                fr_lo = 1 - np.exp(-(lo / eta) ** beta) if lo > 0 else 0
                fr_hi = 1 - np.exp(-(hi / eta) ** beta) if hi > 0 else 1
                ci_lo.append(max(0, fr_lo))
                ci_hi.append(min(1, fr_hi))

            fig.add_trace(go.Scatter(
                x=t_ci, y=ci_lo, mode="lines", name=f"{grp} 95%CI下限",
                line=dict(dash="dot", color=color, width=1),
                hovertemplate=f"{grp} 95%CI下限<br>寿命=%{{x:.2e}}s<br>失效率=%{{y:.4f}}<extra></extra>",
                showlegend=True,
            ))
            fig.add_trace(go.Scatter(
                x=t_ci, y=ci_hi, mode="lines", name=f"{grp} 95%CI上限",
                line=dict(dash="dot", color=color, width=1),
                fill="tonexty", fillcolor=f"rgba{tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.1,)}",
                hovertemplate=f"{grp} 95%CI上限<br>寿命=%{{x:.2e}}s<br>失效率=%{{y:.4f}}<extra></extra>",
                showlegend=True,
            ))

        fig.update_layout(
            title="寿命 vs 累计失效率 (95% CI)",
            xaxis_title="寿命 / s",
            yaxis_title="累计失效率 F(t)",
            yaxis_range=[0, 1],
            template="plotly_white", hovermode="closest",
            height=450, margin=dict(l=60, r=40, t=50, b=60),
        )
        _render_html_in_view(self.wvModelPlot, fig, self.save_dir, "TDDB-plot-lift-fr")

    def _on_plot_fail_curve(self):
        """在右边 wvModelPlot 绘制失效率 vs 工作时间曲线 + 95% CI。"""
        if not self._last_curve_data:
            QMessageBox.warning(self, "提示", "请先计算寿命")
            return
        import plotly.graph_objects as go
        fig = go.Figure()
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
        sec_per_year = 365.25 * 24 * 3600

        for gi, (grp, cd) in enumerate(sorted(self._last_curve_data.items())):
            eta, beta = cd["eta"], cd["beta"]
            color = colors[gi % len(colors)]

            # 0～50年线性
            years = np.linspace(0, 50, 500)
            t_vals = years * sec_per_year
            fr_vals = np.where(years > 0, 1 - np.exp(-(t_vals / eta) ** beta), 0.0)

            fig.add_trace(go.Scatter(
                x=years, y=fr_vals, mode="lines", name=grp,
                line=dict(color=color, width=2),
                hovertemplate=f"<b>{grp}</b><br>时间=%{{x:.1f}}年<br>失效率=%{{y:.4f}}<extra></extra>",
            ))

            # CI
            n_ci = 50
            years_ci = np.linspace(0, 50, n_ci)
            ci_lo, ci_hi = [], []
            for yr in years_ci:
                if yr <= 0:
                    ci_lo.append(0)
                    ci_hi.append(0)
                    continue
                t_op = yr * sec_per_year
                fr_ref = 1 - np.exp(-(t_op / eta) ** beta)
                if fr_ref >= 0.999:
                    ci_lo.append(0)
                    ci_hi.append(1)
                    continue
                lo, hi = lifetime_ci(eta, beta, fr_ref, n=30, alpha=0.05)
                fr_lo = 1 - np.exp(-(lo / eta) ** beta) if lo > 0 else 0
                fr_hi = 1 - np.exp(-(hi / eta) ** beta) if hi > 0 else 1
                ci_lo.append(max(0, fr_lo))
                ci_hi.append(min(1, fr_hi))

            fig.add_trace(go.Scatter(
                x=years_ci, y=ci_lo, mode="lines", name=f"{grp} 95%CI下限",
                line=dict(dash="dot", color=color, width=1),
                showlegend=True,
                hovertemplate=f"{grp} 95%CI下限<br>时间=%{{x:.1f}}年<br>失效率=%{{y:.4f}}<extra></extra>",
            ))
            fig.add_trace(go.Scatter(
                x=years_ci, y=ci_hi, mode="lines", name=f"{grp} 95%CI上限",
                line=dict(dash="dot", color=color, width=1),
                fill="tonexty", fillcolor=f"rgba{tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.1,)}",
                showlegend=True,
                hovertemplate=f"{grp} 95%CI上限<br>时间=%{{x:.1f}}年<br>失效率=%{{y:.4f}}<extra></extra>",
            ))

        fig.update_layout(
            title="失效率 vs 工作时间 (95% CI)",
            xaxis_title="工作时间 / 年",
            yaxis_title="累计失效率 F(t)",
            yaxis_range=[0, 1],
            template="plotly_white", hovermode="closest",
            height=450, margin=dict(l=60, r=40, t=50, b=60),
        )
        _render_html_in_view(self.wvModelPlot, fig, self.save_dir, "TDDB-plot-fail-curve")

    # ── 自定义图 ───────────────────────────────────────────────

    def _on_add_custom_plot(self):
        """打开自定义图对话框，确认后绘制叠加的 Weibull 图。"""
        from .TDDB_custom_draw_ui import Ui_Dialog
        if self._data is None:
            QMessageBox.warning(self, "提示", "请先加载数据")
            return

        dlg = QDialog(self)
        ui = Ui_Dialog()
        ui.setupUi(dlg)

        # 填充可用选项
        if "group" in self._data.columns:
            ui.cmbGroup.addItems(sorted(self._data["group"].dropna().unique()))
        if "Vgs" in self._data.columns:
            ui.cmbVoltage.addItems(sorted(self._data["Vgs"].dropna().astype(str).unique()))
        if "Temperature" in self._data.columns:
            ui.cmbTemp.addItems(sorted(self._data["Temperature"].dropna().astype(str).unique()))
        if "Gate Oxide Area" in self._data.columns:
            ui.cmbArea.addItems(sorted(self._data["Gate Oxide Area"].dropna().astype(str).unique()))

        selected_items: list[dict] = []

        # 添加按钮逻辑
        managed_layout = ui.saItems.widget().layout() or QVBoxLayout(ui.saItems.widget())
        managed_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        def on_add():
            grp = ui.cmbGroup.currentText()
            v = ui.cmbVoltage.currentText()
            t = ui.cmbTemp.currentText()
            a = ui.cmbArea.currentText()
            # 去重
            item = {"group": grp, "v": v, "t": t, "a": a}
            key = (grp, v, t, a)
            if any((d["group"], d["v"], d["t"], d["a"]) == key for d in selected_items):
                return
            selected_items.append(item)
            label_text = f"{grp} | {v}V | {t}℃ | {a}μm²"
            label = QLabel(label_text)
            del_btn = QPushButton("✕")
            del_btn.setFixedWidth(30)
            hbox = QHBoxLayout()
            hbox.addWidget(label)
            hbox.addWidget(del_btn)
            hbox.addStretch()
            container = QWidget()
            container.setLayout(hbox)
            managed_layout.addWidget(container)
            del_btn.clicked.connect(
                lambda checked, k=key, c=container: (
                    selected_items.remove(next(d for d in selected_items
                                                if (d["group"], d["v"], d["t"], d["a"]) == k)),
                    c.deleteLater()
                )
            )

        ui.btnAdd.clicked.connect(on_add)

        if dlg.exec() == QDialog.DialogCode.Accepted and selected_items:
            self._draw_custom_weibull(selected_items)

    def _draw_custom_weibull(self, items: list[dict]):
        """叠加绘制自定义选择的 Weibull 曲线。"""
        if self._data is None:
            return
        use_tbd = self.rdoTBD.isChecked()
        data_col = "TBD" if use_tbd else "QBD"
        unit = "s" if use_tbd else "C"

        import plotly.graph_objects as go
        fig = go.Figure()
        palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
                   "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
        custom_cols = [c for c in ["PART_ID", "Vgs", "Temperature", "Gate Oxide Area",
                                    data_col, "ignore", "group", "老化板通道", "comment"]
                       if self._data is not None and c in self._data.columns]

        for ci, item in enumerate(items):
            df = self._data.copy()
            if "ignore" in df.columns:
                df = df[df["ignore"] != 1]
            if "group" in df.columns:
                df = df[df["group"] == item["group"]]
            if "Vgs" in df.columns:
                df = df[df["Vgs"].astype(str) == item["v"]]
            if "Temperature" in df.columns and item["t"]:
                df = df[df["Temperature"].astype(str) == item["t"]]
            if "Gate Oxide Area" in df.columns and item["a"]:
                df = df[df["Gate Oxide Area"].astype(str) == item["a"]]

            vals = df[data_col].dropna().values
            if len(vals) < 2:
                continue

            plot_d = weibull_plot_data(vals)
            label = f"{item['group']} | {item['v']}V"
            if item["t"]: label += f" | {item['t']}℃"
            if item["a"]: label += f" | {item['a']}μm²"

            result = fit_weibull(vals)
            color = palette[ci % len(palette)]
            beta, eta, r2 = result["beta"], result["eta"], result.get("r2_log", 0)

            # hover rows
            sub_df = df.dropna(subset=[data_col]).sort_values(data_col)
            rows_info = []
            for _, row in sub_df.iterrows():
                rows_info.append([str(row[c]) if not pd.isna(row.get(c)) else ""
                                  for c in custom_cols])

            # 散点
            fig.add_trace(go.Scatter(
                x=plot_d["tbd"], y=plot_d["weibull_prob"],
                mode="markers",
                name=f"{label} 数据  β={beta:.3f} η={_fmt_eta(eta)}{unit}",
                marker=dict(size=7, color=color),
                customdata=rows_info,
                hovertemplate=(
                    "<b>数据点</b><br>" +
                    "<br>".join(f"<b>{col}:</b> %{{customdata[{i}]}}"
                                for i, col in enumerate(custom_cols)) +
                    f"<br>{data_col}=%{{x:.4e}}<br>ln(-ln(1-F))=%{{y:.4f}}<extra></extra>"
                ),
                showlegend=True,
            ))

            # 拟合线
            t_fit = np.logspace(np.log10(min(plot_d["tbd"])),
                                np.log10(max(plot_d["tbd"])), 100)
            wp_fit = beta * (np.log(t_fit) - np.log(eta))
            fig.add_trace(go.Scatter(
                x=t_fit, y=wp_fit,
                mode="lines",
                name=f"{label} 拟合  R²={r2:.4f}",
                line=dict(dash="dash", width=2, color=color),
                hovertemplate=(
                    f"<b>拟合</b><br>β={beta:.4f} η={_fmt_eta(eta)}{unit}<br>"
                    f"R²_log={r2:.4f}<extra></extra>"
                ),
                showlegend=True,
            ))

        fig.update_layout(
            title=f"自定义 Weibull 对比图 — {data_col} ({unit})",
            xaxis_title=f"{data_col} ({unit})",
            xaxis_type="log",
            yaxis_title="ln(-ln(1-F))",
            template="plotly_white",
            hovermode="closest",
            height=500, width=900,
        )
        _render_html_in_view(self.wvWeibullPlot, fig, self.save_dir, "TDDB-custom-weibull")
