"""数据合并模块测试。

Extended with edge/boundary/error condition tests.
"""
import csv
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from core.data_merge import is_pass, is_fail, dedup_within_file, merge_horizontal, merge_t0_tx


# ═══════════════════════════════════════════════════════════════
#  is_pass / is_fail
# ═══════════════════════════════════════════════════════════════

class TestSoftBin:
    def test_pass_when_1(self):
        assert is_pass(1) is True
        assert is_pass("1") is True
        assert is_pass(1.0) is True

    def test_fail_when_not_1(self):
        assert is_pass(2) is False
        assert is_pass(0) is False
        assert is_pass("FAIL") is False
        assert is_fail(2) is True
        assert is_fail("FAIL") is True

    def test_pass_is_not_fail(self):
        assert is_fail(1) is False

    # ── Edge cases ──
    def test_is_pass_none(self):
        assert is_pass(None) is False

    def test_is_pass_nan(self):
        assert is_pass(float('nan')) is False

    def test_is_pass_empty_str(self):
        assert is_pass("") is False

    def test_is_pass_boolean_true(self):
        # int(True) == 1, so True → PASS
        assert is_pass(True) is True

    def test_is_pass_float_near_one(self):
        assert is_pass(1.0000000001) is True


# ═══════════════════════════════════════════════════════════════
#  dedup_within_file
# ═══════════════════════════════════════════════════════════════

class TestDedupWithinFile:

    def test_single_pass_kept(self):
        """单行 PASS → 保留"""
        df = pd.DataFrame({"PART_ID": ["A"], "SOFT_BIN": [1], "DC_T1": [1.0]})
        clean, conflicts = dedup_within_file(df, "f.csv")
        assert len(clean) == 1
        assert len(conflicts) == 0

    def test_pass_preferred_over_fail(self):
        """PASS + FAIL → 只保留 PASS"""
        df = pd.DataFrame({"PART_ID": ["A", "A"], "SOFT_BIN": [2, 1], "DC_T1": [2.0, 1.0]})
        clean, conflicts = dedup_within_file(df, "f.csv")
        assert len(clean) == 1
        assert clean.iloc[0]["SOFT_BIN"] == 1
        assert len(conflicts) == 0

    def test_multi_pass_first_kept(self):
        """多条 PASS → 取第一条"""
        df = pd.DataFrame({"PART_ID": ["A", "A"], "SOFT_BIN": [1, 1], "DC_T1": [1.0, 2.0]})
        clean, _ = dedup_within_file(df, "f.csv")
        assert clean.iloc[0]["DC_T1"] == 1.0

    def test_single_fail_kept(self):
        """单条 FAIL → 保留"""
        df = pd.DataFrame({"PART_ID": ["A"], "SOFT_BIN": [2], "DC_T1": [1.0]})
        clean, conflicts = dedup_within_file(df, "f.csv")
        assert len(clean) == 1
        assert len(conflicts) == 0

    def test_multi_fail_into_conflict(self):
        """多条 FAIL → 进冲突列表"""
        df = pd.DataFrame({"PART_ID": ["A", "A"], "SOFT_BIN": [2, 3], "DC_T1": [1.0, 2.0]})
        clean, conflicts = dedup_within_file(df, "f.csv")
        assert len(conflicts) == 1          # 一组冲突
        assert len(conflicts[0]) == 2       # 2条FAIL行
        # 第一条 FAIL 作为占位
        assert clean.iloc[0]["SOFT_BIN"] == 2

    def test_mixed_multiple_parts(self):
        """多个 PART_ID 混合：PASS优先 + 单FAIL + 多FAIL冲突"""
        df = pd.DataFrame({
            "PART_ID": ["A", "A", "B", "C", "C"],
            "SOFT_BIN": [1, 2, 2, 2, 3],
            "DC_T1": [1.0, 2.0, 3.0, 4.0, 5.0],
        })
        clean, conflicts = dedup_within_file(df, "f.csv")
        assert len(clean) == 3
        assert clean[clean.PART_ID == "A"].iloc[0]["SOFT_BIN"] == 1  # PASS
        assert clean[clean.PART_ID == "B"].iloc[0]["SOFT_BIN"] == 2  # 单FAIL
        assert clean[clean.PART_ID == "C"].iloc[0]["SOFT_BIN"] == 2  # 多FAIL占位
        assert len(conflicts) == 1  # C 进入冲突
        assert len(conflicts[0]) == 2

    def test_missing_required_columns(self):
        """缺少必要列 → 报错"""
        df = pd.DataFrame({"col1": [1]})
        with pytest.raises(ValueError, match="缺少必要列"):
            dedup_within_file(df, "f.csv")

    # ── Edge cases ──
    def test_dedup_empty_df(self):
        """Empty DataFrame → empty result."""
        df = pd.DataFrame(columns=["PART_ID", "SOFT_BIN", "DC_T1"])
        clean, conflicts = dedup_within_file(df, "f.csv")
        assert clean.empty
        assert conflicts == []

    def test_dedup_all_pass(self):
        """All PASS → retained, no conflicts."""
        df = pd.DataFrame({
            "PART_ID": ["A", "B", "C"],
            "SOFT_BIN": [1, 1, 1],
            "DC_T1": [1.0, 2.0, 3.0],
        })
        clean, conflicts = dedup_within_file(df, "f.csv")
        assert len(clean) == 3
        assert len(conflicts) == 0

    def test_dedup_all_fail_single(self):
        """All FAIL, each single row → kept, no conflicts."""
        df = pd.DataFrame({
            "PART_ID": ["A", "B"],
            "SOFT_BIN": [2, 3],
            "DC_T1": [1.0, 2.0],
        })
        clean, conflicts = dedup_within_file(df, "f.csv")
        assert len(clean) == 2
        assert len(conflicts) == 0


# ═══════════════════════════════════════════════════════════════
#  merge_horizontal
# ═══════════════════════════════════════════════════════════════

class TestMergeHorizontal:

    def test_single_frame(self):
        """单文件 → 原样返回"""
        df = pd.DataFrame({"PART_ID": ["A"], "group": ["g1"], "DC_T1": [1.0]})
        r = merge_horizontal([df])
        assert len(r) == 1 and "DC_T1" in r.columns

    def test_no_overlap_columns(self):
        """不同测试列 → 横向拼接"""
        df1 = pd.DataFrame({"PART_ID": ["A"], "group": ["g1"], "DC_T1": [1.0]})
        df2 = pd.DataFrame({"PART_ID": ["A"], "group": ["g1"], "AC_T1": [2.0]})
        r = merge_horizontal([df1, df2])
        assert "DC_T1" in r.columns and "AC_T1" in r.columns
        assert r.iloc[0]["DC_T1"] == 1.0
        assert r.iloc[0]["AC_T1"] == 2.0

    def test_multiple_keys(self):
        """多行多 key"""
        df1 = pd.DataFrame({"PART_ID": ["A", "B"], "group": ["g1", "g1"],
                            "DC_T1": [1.0, 3.0]})
        df2 = pd.DataFrame({"PART_ID": ["A", "B"], "group": ["g1", "g1"],
                            "AC_T1": [2.0, 4.0]})
        r = merge_horizontal([df1, df2], on=["PART_ID", "group"])
        assert len(r) == 2

    def test_empty_frames(self):
        """空列表 → 空 DataFrame"""
        r = merge_horizontal([])
        assert len(r) == 0

    # ── Edge cases ──
    def test_no_overlap_no_common_keys(self):
        """No overlapping PART_IDs → outer join with NaN."""
        df1 = pd.DataFrame({"PART_ID": ["A"], "group": ["g1"], "DC_T1": [1.0]})
        df2 = pd.DataFrame({"PART_ID": ["B"], "group": ["g2"], "AC_T1": [2.0]})
        r = merge_horizontal([df1, df2])
        assert len(r) == 2
        assert pd.isna(r.iloc[1]["DC_T1"])

    def test_conflict_callback(self):
        """Conflict callback receives overlapping columns."""
        df1 = pd.DataFrame({"PART_ID": ["A"], "group": ["g1"], "DC_T1": [1.0]})
        df2 = pd.DataFrame({"PART_ID": ["A"], "group": ["g1"], "DC_T1": [2.0]})
        collected = []

        def callback(conflicts):
            collected.extend(conflicts)
            return {}

        r = merge_horizontal([df1, df2], on_col_conflict=callback)
        assert len(collected) >= 1
        assert collected[0]["column"] == "DC_T1"

    def test_empty_frame_in_list(self):
        """One empty frame → handled."""
        df1 = pd.DataFrame({"PART_ID": ["A"], "group": ["g1"], "DC_T1": [1.0]})
        df2 = pd.DataFrame(columns=["PART_ID", "group", "AC_T1"])
        r = merge_horizontal([df1, df2])
        assert "DC_T1" in r.columns
        assert "AC_T1" in r.columns


# ═══════════════════════════════════════════════════════════════
#  merge_t0_tx 集成测试
# ═══════════════════════════════════════════════════════════════

class TestMergeT0TX:

    def test_t0_only(self):
        """只有 T0 文件"""
        t0 = str(Path("data/T0.csv").resolve())
        r = merge_t0_tx([t0], [])
        assert len(r) > 0
        assert "group" in r.columns
        assert (r["group"] == "T0").all()
        assert "filepath" in r.columns

    def test_tx_only(self):
        """只有 TX 文件"""
        tx_dir = Path("data/TX")
        tx = [str(p.resolve()) for p in sorted(tx_dir.glob("*.csv"))[:1]]
        r = merge_t0_tx([], tx)
        assert len(r) > 0
        assert "group" in r.columns
        assert (r["group"] != "T0").all()

    def test_t0_and_tx(self):
        """T0 + TX 合并"""
        t0 = str(Path("data/T0.csv").resolve())
        tx_dir = Path("data/TX")
        tx = [str(p.resolve()) for p in sorted(tx_dir.glob("*.csv"))[:2]]
        r = merge_t0_tx([t0], tx)
        assert len(r) > 0
        assert "T0" in r["group"].values
        assert any(g != "T0" for g in r["group"].values)
        # 必须包含关键列
        for col in ["PART_ID", "SOFT_BIN", "group", "filepath"]:
            assert col in r.columns

    def test_with_group_map(self):
        """传入文件名分组映射"""
        t0 = str(Path("data/T0.csv").resolve())
        tx_dir = Path("data/TX")
        tx_files = sorted(tx_dir.glob("*.csv"))[:2]
        tx = [str(p.resolve()) for p in tx_files]
        group_map = {f.name: "custom_group" for f in tx_files}
        r = merge_t0_tx([t0], tx, tx_group_map=group_map)
        tx_groups = r[r["group"] != "T0"]["group"].unique()
        for g in tx_groups:
            assert g == "custom_group"

    def test_no_files(self):
        """无文件 → 空 DataFrame"""
        r = merge_t0_tx([], [])
        assert len(r) == 0

    # ── Edge cases ──
    def test_merge_t0_tx_with_conflict_callback(self):
        """merge_t0_tx triggers on_conflict for FAIL multi-row groups."""
        with tempfile.TemporaryDirectory() as d:
            td = Path(d)
            # Create T0 file (1 PASS row)
            t0p = td / "T0.csv"
            with open(t0p, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["PART_ID", "SOFT_BIN", "DC_T1"])
                w.writerow(["Unit", "", "V"])
                w.writerow(["Lower Limit", "", "0"])
                w.writerow(["Higher Limit", "", "5"])
                w.writerow(["SN001", "1", "2.5"])

            # Create TX file with 2 FAIL rows for same PART_ID
            txp = td / "TX.csv"
            with open(txp, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["PART_ID", "SOFT_BIN", "DC_T1"])
                w.writerow(["Unit", "", "V"])
                w.writerow(["Lower Limit", "", "0"])
                w.writerow(["Higher Limit", "", "5"])
                w.writerow(["SN001", "2", "3.0"])
                w.writerow(["SN001", "3", "4.0"])

            conflicts_received = []

            def on_conflict(groups):
                conflicts_received.extend(groups)
                return []

            result = merge_t0_tx(
                [str(t0p)], [str(txp)],
                on_conflict=on_conflict,
            )
            # SN001 in TX has 2 FAIL rows → conflict triggered
            assert len(conflicts_received) >= 1
            assert "PART_ID" in result.columns
            assert "SN001" in result["PART_ID"].values
