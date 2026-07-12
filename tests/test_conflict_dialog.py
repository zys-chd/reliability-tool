"""
冲突对话框测试 — 验证 UI 创建和默认状态。
"""

import pandas as pd
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# 确保 QApplication 已创建
_app = QApplication.instance() or QApplication([])

from ui.gen.conflict_dialog import ConflictDialog
from ui.gen.cross_conflict_dialog import CrossFileConflictDialog


class TestConflictDialog:

    def test_create_with_two_rows(self):
        """2 行冲突数据 → 表格 2 行，默认选中第 0 行"""
        df = pd.DataFrame({
            "PART_ID": ["SN001", "SN001"],
            "SOFT_BIN": [2, 3],
            "group": ["g1", "g1"],
            "filepath": ["f1.csv", "f1.csv"],
            "DC_T1": [1.2e-5, 2.3e-5],
        })
        dlg = ConflictDialog(df)
        assert dlg._table.rowCount() == 2
        assert len(dlg._radio_buttons) == 2
        assert dlg._radio_buttons[0].isChecked() is True

    def test_single_row(self):
        """1 行 → 默认选中"""
        df = pd.DataFrame({"PART_ID": ["A"], "SOFT_BIN": [2], "group": ["g1"],
                           "filepath": ["f.csv"], "DC_T1": [1.0]})
        dlg = ConflictDialog(df)
        assert dlg._table.rowCount() == 1
        assert dlg._radio_buttons[0].isChecked() is True

    def test_accept_returns_index(self):
        """确认后返回选中行在原 DataFrame 中的 index"""
        df = pd.DataFrame({"PART_ID": ["A", "B"], "SOFT_BIN": [2, 3],
                           "group": ["g1", "g1"], "filepath": ["f1.csv", "f2.csv"],
                           "DC_T1": [1.0, 2.0]})
        dlg = ConflictDialog(df)
        # 模拟选中第 1 行
        dlg._radio_buttons[1].setChecked(True)
        dlg._on_accept()
        # 验证 selected_index 是原 df 的第 1 行
        assert dlg.selected_index == df.index[1]
        assert df.loc[dlg.selected_index, "PART_ID"] == "B"


class TestCrossFileConflictDialog:

    def test_single_conflict(self):
        """单条冲突 → 1 行表格"""
        conflicts = [{
            "key": {"PART_ID": "A", "group": "g1"},
            "column": "DC_T1",
            "values": {"f1.csv": 1.2e-5, "f2.csv": 2.3e-5},
        }]
        dlg = CrossFileConflictDialog(conflicts)
        assert dlg._table.rowCount() == 1
        assert len(dlg._combos) == 1

    def test_get_choices_default(self):
        """默认选第一个来源"""
        conflicts = [{
            "key": {"PART_ID": "A", "group": "g1"},
            "column": "DC_T1",
            "values": {"f1.csv": 1.2e-5, "f2.csv": 2.3e-5},
        }]
        dlg = CrossFileConflictDialog(conflicts)
        choices = dlg.get_choices()
        assert choices == {"DC_T1": "f1.csv"}

    def test_multiple_conflicts(self):
        """多条冲突"""
        conflicts = [
            {"key": {"PART_ID": "A", "group": "g1"}, "column": "DC_T1",
             "values": {"f1.csv": 1.0, "f2.csv": 2.0}},
            {"key": {"PART_ID": "A", "group": "g1"}, "column": "DC_T2",
             "values": {"f1.csv": 3.0, "f2.csv": 4.0}},
        ]
        dlg = CrossFileConflictDialog(conflicts)
        assert dlg._table.rowCount() == 2
        assert len(dlg._combos) == 2
