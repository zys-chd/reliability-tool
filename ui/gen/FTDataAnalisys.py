#!/usr/bin/env python3
"""
FT 数据分析页面 - 对应 FTDataAnalisys_ui.py
"""

import logging
import os
from pathlib import Path
import pandas as pd

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QFileDialog, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QScrollArea, QSplitter,
    QVBoxLayout, QWidget, QFrame,
)

from core.path_utils import check_path_length

# ParserManager with auto format detection
from core.file_parser import ParserManager
_parser_manager = ParserManager()

# QWebEngine is optional — if unavailable we fall back to system browser
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    QWebEngineView = None  # type: ignore[assignment,misc]

from .FTDataAnalisys_ui import Ui_FTDataAnalysisWidget
from .FTDataAnalisysConfig import ConfigDialog
from .config_manager import ConfigManager
from .config_schemas import FT_ANALYSIS_SCHEMA


FILE_FILTER = (
    "数据文件 (*.csv *.xlsx *.xls *.txt *.dat);;"
    "CSV 文件 (*.csv);;"
    "Excel 文件 (*.xlsx *.xls);;"
    "文本文件 (*.txt *.dat);;"
    "所有文件 (*)"
)


class _FilePanel:
    """封装一个文件选择面板（T0 或 TX）的逻辑"""

    def __init__(self, label: str, scroll_area: QScrollArea,
                 scroll_content: QWidget, logger: logging.Logger,
                 status_callback):
        self.label = label
        self.scroll_area = scroll_area
        self.scroll_content = scroll_content
        self.logger = logger
        self._set_status = status_callback
        self._files: dict[str, QCheckBox] = {}  # name → checkbox
        self._init_layout()

    def _init_layout(self):
        self._layout = QVBoxLayout(self.scroll_content)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(2)

    def get_filenames(self) -> list[str]:
        """返回所有文件名列表（用于文件名分组解析）"""
        return list(self._files.keys())

    def get_first_checked_dir(self) -> str:
        """返回第一个勾选文件所在目录，无则返回空"""
        for name, cb in self._files.items():
            if cb.isChecked():
                return str(Path(cb.toolTip()).parent)
        return ""

    def get_first_file_dir(self) -> str:
        """返回第一个文件所在目录（不管勾选），无则返回空"""
        if self._files:
            first = next(iter(self._files.values()))
            return str(Path(first.toolTip()).parent)
        return ""

    def add_files(self):
        paths, selected_filter = QFileDialog.getOpenFileNames(
            self.scroll_content, f"选择 {self.label} 文件", "", FILE_FILTER)
        if not paths:
            self.logger.debug(f"[{self.label}] 添加文件操作取消")
            return

        # Warn about Windows path-length limits
        for p in paths:
            for msg in check_path_length(p):
                self.logger.warning(f"[{self.label}] {msg}")

        added, skipped = 0, 0
        for p in paths:
            name = Path(p).name
            full_path = str(Path(p).resolve())
            if name in self._files:
                skipped += 1
                continue
            cb = QCheckBox(name)
            cb.setToolTip(full_path)
            cb.setChecked(False)
            self._files[name] = cb
            self._layout.addWidget(cb)
            added += 1
            self.logger.info(f"[{self.label}] 添加文件: {full_path}")

        if added:
            self._set_status(f"✅ {self.label}: 已添加 {added} 个文件")
            self.logger.info(f"[{self.label}] 本次添加 {added} 个文件，跳过 {skipped} 个重复")
        else:
            self._set_status(f"⚠ {self.label}: 文件已存在，未添加重复项")
            self.logger.warning(f"[{self.label}] 所有 {skipped} 个文件均为重复项")

    def remove_selected(self):
        checked = [cb for cb in self._files.values() if cb.isChecked()]
        if not checked:
            QMessageBox.warning(self.scroll_content, "提示", "请先勾选要删除的文件")
            self._set_status(f"⚠ {self.label}: 未选中任何文件")
            self.logger.warning(f"[{self.label}] 删除操作取消：未选中文件")
            return

        count = len(checked)
        for cb in checked:
            name = cb.text()
            self.logger.info(f"[{self.label}] 删除文件: {name}")
            del self._files[name]
            self._layout.removeWidget(cb)
            cb.deleteLater()

        self._set_status(f"🗑 {self.label}: 已删除 {count} 个文件")
        self.logger.info(f"[{self.label}] 批量删除 {count} 个文件，剩余 {len(self._files)} 个")

    def clear_all(self):
        if not self._files:
            return
        ret = QMessageBox.question(
            self.scroll_content, "确认",
            f"确定要删除 {self.label} 的全部文件吗？")
        if ret != QMessageBox.StandardButton.Yes:
            self.logger.debug(f"[{self.label}] 清空操作取消")
            return

        count = len(self._files)
        names = list(self._files.keys())
        for name in names:
            cb = self._files.pop(name)
            self._layout.removeWidget(cb)
            cb.deleteLater()
        self._set_status(f"🧹 {self.label}: 已清空 {count} 个文件")
        self.logger.warning(f"[{self.label}] 清空全部 {count} 个文件: {names}")


class FTDataAnalysisPage(QWidget, Ui_FTDataAnalysisWidget):

    def __init__(self, parent=None, logger: logging.Logger | None = None):
        super().__init__(parent)
        self.logger = logger or logging.getLogger("FTDataAnalysisPage")
        self._config: dict = {}
        self.setupUi(self)
        self._panels: dict[str, _FilePanel] = {}
        self._init_configs()
        self._init_panels()
        self._set_path_defaults()
        self._load_paths_from_config()
        self._load_file_lists()
        self._connect_signals()

        self.logger.info("FTDataAnalysisPage 初始化完成")
        self.logger.debug(f"UI geometry: {self.geometry().width()}x{self.geometry().height()}")

    def _init_configs(self):
        """初始化 FTDataAnalisys 的单一 ConfigManager"""
        from pathlib import Path
        cfg_dir = Path.cwd() / "config"
        self._cm = ConfigManager(
            cfg_dir / "FTDataAnalisys.toml", FT_ANALYSIS_SCHEMA, self.logger)
        self._cm.load()
        self._config = self._cm.as_dict()
        self.logger.info(f"配置加载完成: {self._cm.active_section}")

    def _init_panels(self):
        self._panels["T0"] = _FilePanel(
            "T0", self.scrollT0FileList, self.scrollT0FileListContent,
            self.logger, self._set_status)
        self._panels["TX"] = _FilePanel(
            "TX", self.scrollTxFileList, self.scrollTxFileListContent,
            self.logger, self._set_status)

    PATH_PATTERNS = {
        "editTxMergeFile":  ("%DIR_TO_TX_FILE%", "TX合并.xlsx"),
        "editCompareFile":  ("%DIR_TO_TX_FILE%", "对比.xlsx"),
    }

    def _set_path_defaults(self):
        """设置配置路径的默认值"""
        for attr, (var, name) in self.PATH_PATTERNS.items():
            edit = getattr(self, attr)
            # 使用 Path.joinpath 确保 Windows 上使用正确的分隔符
            edit.setText(str(Path(var).joinpath(name)))

    def _resolve_single_path(self, pattern: str) -> str:
        """将单个路径中的 % 占位符解析为第一个文件的目录（不改编辑框）"""
        if "%DIR_TO_T0_FILE%" in pattern:
            d = self._panels["T0"].get_first_file_dir()
            if d:
                pattern = pattern.replace("%DIR_TO_T0_FILE%", d)
        if "%DIR_TO_TX_FILE%" in pattern:
            d = self._panels["TX"].get_first_file_dir()
            if d:
                pattern = pattern.replace("%DIR_TO_TX_FILE%", d)
        # 确保路径分隔符正确
        return str(Path(pattern))

    def _load_paths_from_config(self):
        """从配置加载文件路径到编辑框"""
        for attr, key in [("editTxMergeFile", "tx_merge_path"),
                          ("editCompareFile", "compare_path")]:
            val = self._config.get(key, "")
            if val:
                getattr(self, attr).setText(val)

    def _save_paths_to_config(self):
        """将当前编辑框的路径保存到配置"""
        for attr, key in [("editTxMergeFile", "tx_merge_path"),
                          ("editCompareFile", "compare_path")]:
            val = getattr(self, attr).text().strip()
            if val:
                self._cm.set(key, val)

    def _save_file_lists(self):
        """将文件列表保存到配置"""
        for panel_key, cfg_key in [("T0", "t0_file_list"), ("TX", "tx_file_list")]:
            panel = self._panels[panel_key]
            paths = [cb.toolTip() for cb in panel._files.values()]
            self._cm.set(cfg_key, paths)
        self._cm.save()  # 立即写入 TOML 文件

    def _load_file_lists(self):
        """从配置恢复文件列表"""
        for cfg_key, panel_key in [("t0_file_list", "T0"), ("tx_file_list", "TX")]:
            paths = self._config.get(cfg_key, [])
            panel = self._panels[panel_key]
            if not paths:
                continue
            # Warn about Windows path-length limits during restore
            for full_path in paths:
                for msg in check_path_length(full_path):
                    self.logger.warning(f"[{panel_key}] {msg}")
            added = 0
            for full_path in paths:
                name = Path(full_path).name
                if name in panel._files:
                    continue
                from PySide6.QtWidgets import QCheckBox as QCB
                cb = QCB(name)
                cb.setToolTip(full_path)
                cb.setChecked(False)
                panel._files[name] = cb
                panel._layout.addWidget(cb)
                added += 1
            if added:
                self.logger.info(f"[{panel_key}] 从配置恢复 {added} 个文件")

    def _wrap_panel(self, panel_key: str, method_name: str):
        """包装 panel 方法使其在调用后自动保存文件列表"""
        panel = self._panels[panel_key]
        original = getattr(panel, method_name)
        def wrapped(*args, **kwargs):
            original(*args, **kwargs)
            self._save_file_lists()
        return wrapped

    def _connect_signals(self):
        # T0 文件（包装后自动保存文件列表）
        self.btnAddT0File.clicked.connect(self._wrap_panel("T0", "add_files"))
        self.btnRemoveT0File.clicked.connect(self._wrap_panel("T0", "remove_selected"))
        self.btnClearT0Files.clicked.connect(self._wrap_panel("T0", "clear_all"))
        # TX 文件
        self.btnAddTxFile.clicked.connect(self._wrap_panel("TX", "add_files"))
        self.btnRemoveTxFile.clicked.connect(self._wrap_panel("TX", "remove_selected"))
        self.btnClearTxFiles.clicked.connect(self._wrap_panel("TX", "clear_all"))

        # 配置区
        self.btnOpenTxFile.clicked.connect(lambda: self._open(self.editTxMergeFile, "合并结果"))
        self.btnSelectTxFile.clicked.connect(lambda: self._select_file(self.editTxMergeFile, "合并结果"))
        self.btnOpenCompareFile.clicked.connect(lambda: self._open(self.editCompareFile, "对比结果"))
        self.btnSelectCompareFile.clicked.connect(lambda: self._select_file(self.editCompareFile, "对比结果"))

        self.btnGroupConfig.clicked.connect(self._group_config)
        self.btnTemplateConfig.clicked.connect(self._template_config)
        self.btnPlotConfig.clicked.connect(self._plot_config)

        # 功能
        self.btnDrawExcel.clicked.connect(self._draw_excel)
        self.btnMergeFiles.clicked.connect(self._merge_files)
        self.btnCompareFiles.clicked.connect(self._compare_files)
        self.btnPlot.clicked.connect(self._plot)
        self.btnSaveImage.clicked.connect(self._save_image)
        self.btnReset.clicked.connect(self.reset)

    # ── 辅助 ──────────────────────────────────────────────────

    def _set_status(self, text: str):
        self.lblStatus.setText(text)

    def _select_file(self, edit: QLineEdit, label: str):
        path, _ = QFileDialog.getOpenFileName(
            self, f"选择 {label}", "", FILE_FILTER)
        if path:
            full = str(Path(path).resolve())
            edit.setText(full)
            self.logger.info(f"选择 {label}: {full}")
            self._set_status(f"📎 {label}: {Path(path).name}")

    def _open(self, edit: QLineEdit, label: str):
        path = edit.text().strip()
        if not path:
            QMessageBox.warning(self, "提示", f"请先选择 {label}")
            return
        # 解析 % 占位符（不改线编辑框内容）
        if "%" in path:
            path = self._resolve_single_path(path)
        if not Path(path).exists():
            name = Path(path).name
            QMessageBox.critical(self, "错误",
                f"文件不存在:\n{path}\n\n请先生成 {name} 后再打开")
            self.logger.error(f"{label} 文件不存在: {path}")
            return
        self.logger.info(f"打开 {label}: {path}")
        try:
            from core.open_file import open_file
            open_file(path)
            self._set_status(f"📂 {label}: {Path(path).name}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开文件失败:\n{e}")
            self.logger.error(f"打开文件失败: {e}")
        # TODO: 实际读取处理

    # ── 配置 ──────────────────────────────────────────────────

    def _get_test_columns(self) -> tuple[list[str], list[str]]:
        """从 T0/TX 文件获取测试列名（自动格式检测 + 列映射）"""
        skip = {"PART_ID", "SOFT_BIN", "group", "filepath"}
        t0_cols, tx_cols = set(), set()
        for cb in self._panels["T0"]._files.values():
            try:
                df = _parser_manager.detect_and_read(cb.toolTip())
                t0_cols |= {c for c in df.columns if c not in skip}
            except Exception:
                pass
        for cb in self._panels["TX"]._files.values():
            try:
                df = _parser_manager.detect_and_read(cb.toolTip())
                tx_cols |= {c for c in df.columns if c not in skip}
            except Exception:
                pass
        return sorted(t0_cols), sorted(tx_cols)

    def _open_config(self, tab_key: str, tab_widget_attr: str):
        tx_files = self._panels["TX"].get_filenames()
        t0_cols, tx_cols = self._get_test_columns()
        dlg = ConfigDialog(self._cm, tab_key, self.logger, self,
                           tx_filenames=tx_files,
                           t0_columns=t0_cols, tx_columns=tx_cols)
        tab_widget = getattr(dlg, tab_widget_attr)
        dlg.tabConfig.setCurrentWidget(tab_widget)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._config = self._cm.as_dict()
            self._save_paths_to_config()
            self._save_file_lists()  # 也保存 T0/TX 文件列表
            self._cm.save()
            self.logger.info(f"配置已确认: {self._config.get('_name')}")
            # try:
            #     zoom = plot_cfg.get("webengine_scale", 100)
            #     self.webResult.setZoomFactor(zoom / 100.0)
            # except:
            #     pass
            self._set_status(f"✅ 配置已保存")
        else:
            self._set_status(f"配置已取消")

    def _group_config(self):
        self._open_config("group", "tabGroup")

    def _template_config(self):
        self._open_config("template", "tabTemplate")

    def _plot_config(self):
        self._open_config("plot", "tabPlot")

    # ── 功能 ──────────────────────────────────────────────────

    def _draw_excel(self):
        """绘制 Excel — 生成统计汇总 + 分组明细 + 嵌入图表。"""
        self.logger.info("绘制 Excel")
        self._set_status("📊 绘制 Excel")

        # 检查对比文件
        compare_path = self._resolve_single_path(
            self.editCompareFile.text().strip())
        if not compare_path or not Path(compare_path).is_file():
            QMessageBox.warning(self, "提示", "请先执行「对比文件」生成对比结果")
            return

        # 获取配置
        calc_config = self._config.get("calc_config", {})
        if not calc_config or not calc_config.get("formulas"):
            QMessageBox.warning(self, "提示", "请先在「模板配置-数据计算/limit配置」中设置 shift 公式")
            return

        plot_config = self._config.get("plot_config", {})
        if not plot_config:
            self.logger.warning("绘图配置为空，使用默认值")
            plot_config = {}

        # 确保 plot_config 是 dict
        if isinstance(plot_config, str):
            import json
            plot_config = json.loads(plot_config) if plot_config else {}

        # 选择输出路径
        default_name = Path(compare_path).stem + "_绘制报告.xlsx"
        default_dir = str(Path(compare_path).parent)
        output_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "保存绘制 Excel",
            str(Path(default_dir) / default_name),
            "Excel 文件 (*.xlsx);;所有文件 (*)",
        )
        if not output_path:
            self.logger.debug("绘制 Excel 操作取消")
            return
        output_path = str(Path(output_path).resolve())

        # 执行绘制
        from ui.gen.progress_worker import ProgressDialog
        from core.draw_excel import export_draw_excel

        dlg_progress = ProgressDialog("绘制 Excel 中...", self)
        try:
            result_path = dlg_progress.run(
                lambda p: export_draw_excel(
                    compare_path=compare_path,
                    output_path=output_path,
                    plot_config=plot_config,
                    calc_config=calc_config,
                    progress=p,
                )
            )
            if result_path:
                self.logger.info(f"绘制 Excel 完成: {result_path}")
                self._set_status(f"✅ 绘制 Excel 完成: {Path(result_path).name}")
                from core.open_file import open_file
                open_file(result_path)
            else:
                self.logger.warning("绘制 Excel 被用户取消")
                self._set_status("⚠ 绘制 Excel 已取消")
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.logger.error(f"绘制 Excel 失败:\n{tb}")
            QMessageBox.critical(self, "错误",
                                 f"绘制 Excel 失败:\n{e}\n\n详细错误见日志")

    def _merge_files(self):
        """合并文件按钮 — 使用线程 + 进度条"""
        self.logger.info("开始合并文件")
        t0_files = [cb.toolTip() for cb in self._panels["T0"]._files.values()]
        tx_files = [cb.toolTip() for cb in self._panels["TX"]._files.values()]

        if not t0_files and not tx_files:
            QMessageBox.warning(self, "提示", "请先添加 T0 或 TX 文件")
            return

        tx_group_map = self._config.get("filename_rules", {})
        group_type = self._config.get("group_type", "filename")
        sn_map = self._config.get("SN", {})

        # ── 在主线程预扫描冲突 ──
        from core.data_merge import merge_t0_tx as run_merge
        from ui.gen.conflict_dialog import ConflictDialog

        chosen_indices: list[int | None] = []

        def on_conflict(conflict_groups: list[pd.DataFrame]):
            """一次性处理所有冲突组 — 每组的整行数据让用户单选"""
            nonlocal chosen_indices
            chosen_indices = []
            n = len(conflict_groups)
            self.logger.info(f"发现 {n} 组冲突")

            for i, group_df in enumerate(conflict_groups):
                pid = group_df.iloc[0]["PART_ID"]
                grp = group_df.iloc[0]["group"]
                dlg = ConflictDialog(group_df.copy(), self)
                dlg.setWindowTitle(
                    f"选择保留的数据 ({i+1}/{n}) — {pid} / {grp}")
                result = dlg.exec()

                if result == QDialog.DialogCode.Accepted and dlg.fix_in_excel:
                    # 用户点了「导出Excel自行修复」→ 一次性导出所有组
                    self.logger.info("用户选择导出Excel自行修复")
                    import pandas as pd
                    from pathlib import Path as PPath
                    import tempfile
                    tmp = PPath(tempfile.mktemp(suffix=".xlsx"))
                    try:
                        # 每个冲突组一个 sheet，每行标记在组内的行号
                        with pd.ExcelWriter(tmp, engine="openpyxl") as writer:
                            for j, gdf in enumerate(conflict_groups):
                                sheet_name = f"冲突_{j+1}"
                                export_df = gdf.copy()
                                export_df.insert(0, "_行号", range(len(export_df)))
                                export_df.to_excel(writer, sheet_name=sheet_name,
                                                   index=False)
                        # 打开文件让用户编辑
                        from core.open_file import open_file
                        open_file(str(tmp))
                        QMessageBox.information(
                            self, "提示",
                            f"已导出 {n} 组冲突到临时 Excel 文件。\n"
                            f"请在 Excel 中编辑：每个 sheet 只保留要保留的一行，"
                            f"删除其他行。\n保存并关闭 Excel 后点击确定继续。")
                        # 读取编辑后的文件
                        edited = pd.read_excel(tmp, sheet_name=None,
                                               engine="openpyxl")
                        # 解析每组的选择
                        for j in range(n):
                            sheet_name = f"冲突_{j+1}"
                            if sheet_name in edited:
                                sdf = edited[sheet_name]
                                if len(sdf) >= 1:
                                    first = sdf.iloc[0]
                                    chosen_indices.append(
                                        int(first["_行号"]))
                                else:
                                    chosen_indices.append(None)
                            else:
                                chosen_indices.append(None)
                        self.logger.info(f"Excel 修复完成: {len(chosen_indices)} 组")
                    except Exception as e:
                        self.logger.error(f"Excel 修复失败: {e}")
                        import traceback
                        self.logger.error(traceback.format_exc())
                        QMessageBox.critical(
                            self, "错误",
                            f"读取编辑后的 Excel 失败：{e}\n请重试")
                        chosen_indices = []
                        return chosen_indices
                    finally:
                        try:
                            tmp.unlink()
                        except OSError:
                            pass
                    break  # 退出循环，所有冲突已通过 Excel 处理

                elif result == QDialog.DialogCode.Accepted:
                    chosen_indices.append(dlg.selected_index)
                else:
                    chosen_indices.append(None)  # 放弃，用合并值

            return chosen_indices

        # 先在主线程跑一遍（不弹进度）收集冲突
        try:
            dummy_progress = type('DummyProgress', (), {
                'set_total': lambda self, n: None,
                'advance': lambda self, msg: None,
                'set_status': lambda self, msg: None,
                'cancelled': False,
            })()
            _ = run_merge(
                t0_files, tx_files,
                tx_group_map=tx_group_map,
                on_conflict=on_conflict,
                progress=dummy_progress,
                sn_map=sn_map,
                group_type=group_type,
            )
        except Exception as e:
            self.logger.warning(f"预扫描冲突失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

        # ── 在工作线程执行最终合并 ──
        from ui.gen.progress_worker import ProgressDialog

        dlg_progress = ProgressDialog("合并文件中...", self)
        try:
            result = dlg_progress.run(
                lambda p: run_merge(
                    t0_files, tx_files,
                    tx_group_map=tx_group_map,
                    on_conflict=lambda _: chosen_indices,
                    progress=p,
                    sn_map=sn_map,
                    group_type=group_type,
                )
            )
            if result is None or result.empty:
                self.logger.warning("合并结果为空或已取消")
                return

            self._merged_df = result
            self._save_merged_result(result)
            self._set_status(f"✅ 合并完成: {len(result)} 行 × {len(result.columns)} 列")
            self.logger.info(f"合并完成: {len(result)} 行, {len(result.columns)} 列")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"合并失败:\n{e}")
            self.logger.error(f"合并失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def _apply_sn_grouping(self, df):
        """根据配置的 SN 映射重新分配 group 列。"""
        if df is None or df.empty or "PART_ID" not in df.columns:
            return df
        sn_map = getattr(self, '_sn_map', {})
        if not sn_map:
            return df

        group_type = self._config.get("group_type", "filename")

        def _lookup_group(part_id):
            pid = str(part_id).strip()
            if pid in sn_map:
                return sn_map[pid]
            for pattern, group in sn_map.items():
                if pid.startswith(pattern):
                    return group
            return None

        df = df.copy()
        sn_groups = df["PART_ID"].apply(_lookup_group)
        # 未匹配到 SN 映射的，用原始文件名代替
        sn_groups = sn_groups.fillna(df["group"].astype(str))

        if group_type == "both":
            # 二者结合：filename_group + SN_group
            # 未匹配到 SN 的项，SN_group = filename_group，避免重复
            combined = df["group"].astype(str) + "+" + sn_groups
            # 如果 SN 组与原始组相同（未匹配），去掉重复
            mask = sn_groups == df["group"].astype(str)
            combined[mask] = df["group"].astype(str)
            df["group"] = combined
        else:
            # "SN" 模式：直接覆盖
            df["group"] = sn_groups

        self.logger.info(f"SN 分组完成: {df['group'].nunique()} 个分组")
        return df

    def _save_merged_result(self, df):
        """将合并结果保存到配置路径"""
        output_path = self.editTxMergeFile.text().strip()
        if not output_path:
            self.logger.warning("未配置输出路径，跳过保存")
            return
        if "%" in output_path:
            output_path = self._resolve_single_path(output_path)
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            if output_path.endswith(".xlsx"):
                df.to_excel(output_path, index=False)
            else:
                df.to_csv(output_path, index=False)
            self.logger.info(f"合并结果已保存: {output_path}")
            self._set_status(f"✅ 已保存: {Path(output_path).name}")
        except Exception as e:
            self.logger.error(f"保存失败: {e}")

    def _compare_files(self):
        self.logger.info("对比文件")
        self._set_status("🔍 对比文件")

        # 检查是否有合并结果（内存中或磁盘上）
        import pandas as pd
        df = getattr(self, "_merged_df", None)
        if df is None or df.empty:
            # 尝试从上次合并结果文件加载
            merge_path = self.editTxMergeFile.text().strip()
            if "%" in merge_path:
                merge_path = self._resolve_single_path(merge_path)
            if merge_path and Path(merge_path).is_file():
                self.logger.info(f"从文件加载合并结果: {merge_path}")
                try:
                    if merge_path.endswith(".xlsx"):
                        df = pd.read_excel(merge_path, engine="openpyxl")
                    else:
                        df = pd.read_csv(merge_path, encoding='utf-8-sig')
                    self._merged_df = df
                except Exception as e:
                    self.logger.warning(f"加载合并结果文件失败: {e}")
        if df is None or df.empty:
            QMessageBox.warning(self, "提示", "请先执行「合并文件」获得合并数据")
            return

        # 获取 calc_config
        calc_config = self._config.get("calc_config", {})
        if not calc_config or not calc_config.get("formulas"):
            QMessageBox.warning(self, "提示", "请先在「模板配置-数据计算/limit配置」中设置 shift 公式")
            return

        # 确定输出路径
        output_path = self.editCompareFile.text().strip()
        if not output_path:
            output_path = "对比结果.xlsx"
        if "%" in output_path:
            output_path = self._resolve_single_path(output_path)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 读取原始 CSV 的元信息（单位/上下限）
        from core.compare import read_raw_headers_from_file
        raw_headers = {}
        for src in ([self._panels["T0"]._files.values()] if hasattr(self, '_panels') else []):
            for cb in list(self._panels["T0"]._files.values())[:1]:
                raw_headers = read_raw_headers_from_file(cb.toolTip())
                break
            break

        # 执行对比
        from ui.gen.progress_worker import ProgressDialog
        from core.compare import run_compare

        dlg_progress = ProgressDialog("对比文件中...", self)
        try:
            result_path = dlg_progress.run(
                lambda p: run_compare(
                    self._merged_df, calc_config,
                    raw_headers=raw_headers,
                    output_path=output_path, progress=p,
                )
            )
            self.logger.info(f"对比完成: {result_path}")
            self._set_status(f"✅ 对比完成: {Path(result_path).name}")
            from core.open_file import open_file
            open_file(result_path)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"对比失败:\n{e}")
            self.logger.error(f"对比失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def _plot(self):
        self.logger.info("绘图")
        self._set_status("📈 绘图")

        # 获取数据
        compare_path = self._resolve_single_path(
            self.editCompareFile.text().strip())
        if not compare_path or not Path(compare_path).is_file():
            QMessageBox.warning(self, "提示", "请先执行「对比文件」生成对比结果")
            return

        # 获取配置
        calc_config = self._config.get("calc_config", {})
        test_items = self._config.get("selected_test_items", [])
        if not test_items or not calc_config.get("formulas"):
            QMessageBox.warning(self, "提示", "请先配置测试项和 shift 公式")
            return

        # 收集绘图配置
        import json
        plot_cfg_str = self._config.get("plot_config", "{}")
        if isinstance(plot_cfg_str, str):
            plot_cfg = json.loads(plot_cfg_str) if plot_cfg_str else {}
        else:
            plot_cfg = plot_cfg_str

        # 读取数据
        from core.plotting import read_compare_file, build_plots, save_html
        import pandas as pd

        # 预先定义，确保 except 中可访问
        group_by = plot_cfg.get("group_by", "group")
        items_to_plot = []
        plot_kw = {}

        try:
            self.logger.info(f"读取对比文件: {compare_path}")
            df_compare = read_compare_file(compare_path)
            if df_compare.empty:
                QMessageBox.warning(self, "提示", "对比文件无数据")
                return

            # 确定分组模式、Y轴模式
            group_by = plot_cfg.get("group_by", "group")  # group / item
            y_mode = plot_cfg.get("y_mode", "cdf")       # cdf / weibull

            # 确定哪些测试项有 TX 数据
            available = sorted(set(
                c.rsplit("_TX", 1)[0] for c in df_compare.columns
                if c.endswith("_TX")
            ))
            items_to_plot = [t for t in test_items if t in available]
            if not items_to_plot:
                items_to_plot = available[:min(6, len(available))]
            if not items_to_plot:
                QMessageBox.warning(self, "提示", "对比文件中无可用测试项数据")
                return

            self.logger.info(f"绘图: {len(items_to_plot)} 测试项, "
                             f"group_by={group_by}, y_mode={y_mode}")

            # 构建绘图配置
            # 从对比文件 meta 中读取 lower_limit / higher_limit / shift_limit
            meta = df_compare.attrs.get("meta", {})
            lower_limits = meta.get("lower_limit", {})
            higher_limits = meta.get("higher_limit", {})
            shift_limits = meta.get("shift_limit", {})
            # 合并为 limit_map: {test_item: {"lower": X, "higher": Y, "shift": Z}}
            limit_map = {}
            all_test_items = set(lower_limits) | set(higher_limits) | set(shift_limits)
            for item in all_test_items:
                limit_map[item] = {
                    "lower": lower_limits.get(item),
                    "higher": higher_limits.get(item),
                    "shift": shift_limits.get(item),
                }

            # 从 calc_config 读取 limits / directions
            calc_limits = calc_config.get("limits", {})
            calc_directions = calc_config.get("directions", {})

            # 构建绘图配置
            plot_kw = {
                "rows": plot_cfg.get("rows", 2),
                "cols": plot_cfg.get("cols", 3),
                "marker_size": plot_cfg.get("marker_size", 6),
                "line_width": plot_cfg.get("line_width", 1),
                "marker_opacity": plot_cfg.get("marker_opacity", 0.8),
                "line_opacity": plot_cfg.get("line_opacity", 0.8),
                "plot_type": plot_cfg.get("plot_type", "markers"),
                "theme": plot_cfg.get("theme", "plotly_white"),
                "title_font_size": plot_cfg.get("title_font_size", 14),
                "label_font_size": plot_cfg.get("label_font_size", 12),
                "legend_font_size": plot_cfg.get("legend_font_size", 11),
                "hover_font_size": plot_cfg.get("hover_font_size", 11),
                "x_label": plot_cfg.get("x_label", ""),
                "hover_template": plot_cfg.get("hover_template", ""),
                "x_min": plot_cfg.get("x_min"),
                "x_max": plot_cfg.get("x_max"),
                "y_min": plot_cfg.get("y_min"),
                "y_max": plot_cfg.get("y_max"),
                "width": plot_cfg.get("width", 1200),
                "height": plot_cfg.get("height", 600),
                "formula_map": calc_config.get("formulas", {}),
                # 坐标轴缩放
                "x_scale": plot_cfg.get("x_scale", "linear"),
                "y_scale": plot_cfg.get("y_scale", "linear"),
                # tick 格式
                "tick_format": plot_cfg.get("tick_format", ""),
                "tick_decimals": plot_cfg.get("tick_decimals", -1),
                # 限值线 & 超出区域
                "show_limit_line": plot_cfg.get("show_limit_line", False),
                "draw_over_limit": plot_cfg.get("draw_over_limit", False),
                # 方向映射 & 限值映射（优先用用户配置的 calc_limits）
                "direction_map": plot_cfg.get("direction_map", calc_directions),
                "limit_map": calc_limits,  # 用用户配置的 limit 值，不是 Excel meta
                # 绘制哪些数据
                "draw_t0": plot_cfg.get("draw_t0", True),
                "draw_tx": plot_cfg.get("draw_tx", True),
                "draw_shift": plot_cfg.get("draw_shift", True),
                # marker 边框
                "lineframe_width": plot_cfg.get("lineframe_width", 0),
            }

            # ── 在工作线程执行绘图 + 保存 ──
            from ui.gen.progress_worker import ProgressDialog
            dlg_progress = ProgressDialog("绘图中...", self)

            def _plot_work(p):
                n_items = len(items_to_plot)
                plot_kw["_progress"] = p
                plot_kw["_progress_total"] = n_items
                # 总工作量 = n_items 个子图 + 1 次保存
                p.set_total(n_items + 1)
                p.advance(step=0, status=f"构建图表 ({n_items} 项)...")
                fig = build_plots(
                    df_compare, items_to_plot, group_by, y_mode, plot_kw)

                # 保存到临时路径
                save_dir = plot_cfg.get("save_dir", "")
                if "%DIR_TO_PROGRAM%" in save_dir:
                    save_dir = str(Path(save_dir.replace(
                        "%DIR_TO_PROGRAM%", str(Path.cwd()))))
                if not save_dir:
                    save_dir = str(Path.cwd() / "plots")
                Path(save_dir).mkdir(parents=True, exist_ok=True)

                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                html_path = str(Path(save_dir) / f"FT-{timestamp}.html")

                p.advance(step=1, status="保存 HTML...")
                save_html(fig, html_path)
                # 记录保存目录以便退出时清理
                if not hasattr(self, '_ft_save_dirs'):
                    self._ft_save_dirs = set()
                self._ft_save_dirs.add(save_dir)
                return fig, html_path

            try:
                fig, html_path = dlg_progress.run(_plot_work)
                if fig is None:
                    return  # 用户取消
                self._current_fig = fig
                self._y_mode = y_mode
                self._current_plot_html = html_path

                # 显示在 QWebEngineView（若不可用则走系统浏览器）
                if QWebEngineView is not None:
                    from PySide6.QtCore import QUrl
                    try:
                        from PySide6.QtWebEngineCore import QWebEngineSettings
                    except ImportError:
                        from PySide6.QtWebEngineWidgets import QWebEngineSettings
                    self.webResult.settings().setAttribute(
                        QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
                    self.webResult.load(QUrl.fromLocalFile(html_path))

                    # 应用 webengine 缩放
                    zoom = plot_cfg.get("webengine_scale", 100)
                    try:
                        self.webResult.loadFinished.disconnect()
                    except TypeError:
                        pass
                    except Exception:
                        pass
                    def _apply_zoom(ok):
                        self.webResult.setZoomFactor(zoom / 100.0)
                        try:
                            self.webResult.loadFinished.disconnect(_apply_zoom)
                        except TypeError:
                            pass
                    self.webResult.loadFinished.connect(_apply_zoom)
                    self._webengine_zoom_saved = zoom
                    def _on_zoom_changed():
                        new_zoom = round(self.webResult.zoomFactor() * 100)
                        if new_zoom != self._webengine_zoom_saved:
                            self._webengine_zoom_saved = new_zoom
                            old = self._config.get("webengine_scale", 100)
                            if new_zoom != old:
                                self._cm.set("webengine_scale", new_zoom)
                                self._cm.save()
                                self.logger.info(f"WebEngine 缩放已保存: {new_zoom}%")
                    from PySide6.QtCore import QTimer
                    if hasattr(self, '_zoom_timer') and self._zoom_timer:
                        self._zoom_timer.stop()
                    self._zoom_timer = QTimer(self)
                    self._zoom_timer.timeout.connect(_on_zoom_changed)
                    self._zoom_timer.start(2000)
                else:
                    from core.open_file import open_file
                    self.logger.info("QWebEngine 不可用，在系统浏览器中打开 HTML")
                    open_file(html_path)

                self._set_status(f"✅ 绘图完成: {Path(html_path).name}")
                self.logger.info(f"绘图完成: {html_path}")

            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                self.logger.error(f"绘图失败:\\\\n{tb}")
                self.logger.error(f"绘图配置: rows={plot_kw.get('rows')}, cols={plot_kw.get('cols')}, "
                                  f"items={len(items_to_plot)}, group_by={group_by}")
                QMessageBox.critical(self, "错误",
                                     f"绘图失败:\\\\n{e}\\\\n\\\\n详细错误见日志文件")

        except Exception:
            pass  # 外层 try 已在内部 except 中处理

    def _save_image(self):
        """保存图片/HTML — 弹出 QFileDialog 选择路径和格式"""
        self.logger.info("保存图片")
        self._set_status("💾 保存图片")

        fig = getattr(self, "_current_fig", None)
        if fig is None:
            QMessageBox.warning(self, "提示", "请先生成图表")
            return

        y_mode = getattr(self, "_y_mode", "cdf")
        from datetime import datetime
        default_name = f"plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        # 弹出文件保存对话框
        from PySide6.QtWidgets import QFileDialog
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "保存图表",
            default_name,
            "HTML 文件 (*.html);;PNG 图片 (*.png);;PDF 文档 (*.pdf);;所有文件 (*)",
        )
        if not path:
            self.logger.debug("保存图片操作取消")
            return

        path_obj = Path(path)
        ext = path_obj.suffix.lower()

        try:
            if ext == ".html":
                from core.plotting import save_html
                save_html(fig, str(path_obj))
                self.logger.info(f"HTML 已保存: {path_obj}")
                self._set_status(f"✅ HTML 已保存: {path_obj.name}")

            elif ext in (".png", ".pdf", ".svg", ".jpeg", ".jpg"):
                # 尝试用 fig.write_image（需要 kaleido 或 orca）
                try:
                    fig.write_image(str(path_obj), width=fig.layout.width or 1200,
                                    height=fig.layout.height or 600)
                    self.logger.info(f"{ext.upper()} 已保存: {path_obj}")
                    self._set_status(f"✅ {ext.upper()} 已保存: {path_obj.name}")
                except Exception as e:
                    self.logger.warning(f"write_image 失败 ({e}) — 需要安装 kaleido")
                    # 不支持直接保存图片，降级为 HTML 保存
                    from core.plotting import save_html
                    html_path = path_obj.with_suffix(".html")
                    save_html(fig, str(html_path))
                    self.logger.info(f"已降级保存为 HTML: {html_path}")
                    self._set_status(f"⚠ {ext.upper()} 失败，已存为 HTML: {html_path.name}")
                    QMessageBox.warning(
                        self, "提示",
                        f"保存 {ext.upper()} 需要安装 kaleido 库。\n"
                        f"已将图表保存为 HTML 格式:\n{html_path.name}\n\n"
                        f"如需 PNG/PDF，请运行: pip install kaleido")

            else:
                QMessageBox.warning(self, "提示",
                                    f"不支持的格式: {ext}，请使用 .html / .png / .pdf / .svg / .jpeg / .jpg")
                return

        except Exception as e:
            self.logger.error(f"保存图片失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            QMessageBox.critical(self, "错误", f"保存失败:\n{e}")

    def reset(self):
        for key in ("T0", "TX"):
            self._panels[key].clear_all()
        self.editT0MergeFile.clear()
        self.editTxMergeFile.clear()
        self.editCompareFile.clear()
        self.logger.info("页面重置完成")
        self._set_status("🔄 已重置")

    def _cleanup_temp_files(self):
        """退出时清理 FT 临时 HTML 文件（FT-*.html）。"""
        dirs = getattr(self, '_ft_save_dirs', set())
        if not dirs:
            # fallback: 尝试默认 plots 目录
            dirs.add(str(Path.cwd() / "plots"))
        for d in dirs:
            if not os.path.isdir(d):
                continue
            try:
                for f in os.listdir(d):
                    if f.startswith("FT-") and f.endswith(".html"):
                        os.remove(os.path.join(d, f))
            except Exception as e:
                self.logger.warning(f"清理 FT 临时文件失败 [{d}]: {e}")
