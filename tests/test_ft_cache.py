"""Tests for FTCache — FT 文件三层缓存系统。"""
import csv
import os
import pickle
import tempfile
import time
from pathlib import Path

import pandas as pd
import pytest

from core.ft_cache import FTCache, ft_cache
from core.FT_file_parser import FTData


@pytest.fixture
def tmp_cache(tmp_path) -> FTCache:
    """Isolated FTCache in temp directory."""
    return FTCache(tmp_path / "ft_cache")


@pytest.fixture
def tmp_cfg(tmp_path) -> Path:
    """Minimal config for FTData."""
    p = tmp_path / "test.toml"
    p.write_text("""
[[signatures]]
format_id = "TEST"
header_identifiers = ["PART_ID", "SOFT_BIN"]
data_start_offset = 4
unit_offset = 1
lower_limit_offset = 2
higher_limit_offset = 3
pre_test_columns = ["SOFT_BIN"]
delimiter = ","
skip_row_values = {PART_ID = ["1", "END"]}
column_map = {}
""")
    return p


def make_csv(path: Path, rows: list[list]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    return path


# ═══════════════════════════════════════════════════════════════════
#  FTCache 核心功能
# ═══════════════════════════════════════════════════════════════════


class TestFTCacheCore:

    def test_put_and_get_memory(self, tmp_cache, tmp_path):
        """存入后从内存缓存取出。"""
        csv_path = make_csv(tmp_path / "test.csv", [
            ["PART_ID", "SOFT_BIN", "DC_T1"],
            ["Unit", "", "V"],
            ["Lower", "", "0"],
            ["Higher", "", "5"],
            ["SN001", "1", "2.5"],
        ])
        state = {"_df": pd.DataFrame({"a": [1]}), "_units": {}}
        tmp_cache.put(str(csv_path), state)
        got = tmp_cache.get(str(csv_path))
        assert got is not None
        assert "_df" in got
        assert got["_df"].iloc[0]["a"] == 1

    def test_cache_miss_no_file(self, tmp_cache):
        """不存在的文件返回 None。"""
        got = tmp_cache.get("/nonexistent/file.csv")
        assert got is None

    def test_cache_miss_modified_file(self, tmp_cache, tmp_path):
        """文件修改后缓存失效。"""
        p = make_csv(tmp_path / "test.csv", [
            ["PART_ID", "SOFT_BIN", "DC_T1"],
            ["SN001", "1", "2.5"],
        ])
        state = {"_df": pd.DataFrame({"x": [1]}), "_units": {}}
        tmp_cache.put(str(p), state)

        # 修改文件
        time.sleep(0.01)  # 确保 mtime 变化
        with open(p, "a") as f:
            f.write("extra\n")

        got = tmp_cache.get(str(p))
        assert got is None  # 文件已修改

    def test_get_meta(self, tmp_cache, tmp_path):
        """快速获取文件元数据。"""
        p = make_csv(tmp_path / "test.csv", [
            ["PART_ID", "SOFT_BIN", "DC_T1"],
            ["Unit", "", "V"],
            ["Lower", "", "0"],
            ["Higher", "", "5"],
            ["SN001", "1", "2.5"],
            ["SN002", "1", "3.0"],
        ])
        state = {
            "_df": pd.DataFrame({"PART_ID": ["SN001", "SN002"], "DC_T1": [2.5, 3.0]}),
            "_units": {"DC_T1": "V"},
            "_meta_header": ["PART_ID", "SOFT_BIN"],
            "_test_header": ["DC_T1"],
            "_fmt": {"sig": {"format_id": "TEST"}},
        }
        tmp_cache.put(str(p), state)

        meta = tmp_cache.get_meta(str(p))
        assert meta is not None
        assert meta["signature_id"] == "TEST"
        assert meta["row_count"] == 2  # 2 data rows in DF

    def test_invalidate(self, tmp_cache, tmp_path):
        """清除单文件缓存。"""
        p = make_csv(tmp_path / "test.csv", [
            ["PART_ID", "SOFT_BIN", "DC_T1"],
            ["SN001", "1", "2.5"],
        ])
        tmp_cache.put(str(p), {"_df": pd.DataFrame({"a": [1]}), "_units": {}})
        assert tmp_cache.get(str(p)) is not None
        tmp_cache.invalidate(str(p))
        assert tmp_cache.get(str(p)) is None

    def test_clear_all(self, tmp_cache, tmp_path):
        """清除全部缓存。"""
        for i in range(3):
            p = make_csv(tmp_path / f"test_{i}.csv", [
                ["PART_ID", "SOFT_BIN", "DC_T1"],
                [f"SN00{i}", "1", "2.5"],
            ])
            tmp_cache.put(str(p), {"_df": pd.DataFrame({"a": [i]}), "_units": {}})
        assert len(list(tmp_cache._pickle_dir.glob("*.pkl"))) == 3
        tmp_cache.clear_all()
        assert len(list(tmp_cache._pickle_dir.glob("*.pkl"))) == 0
        for i in range(3):
            assert tmp_cache.get(str(tmp_path / f"test_{i}.csv")) is None

    def test_sqlite_persistence(self, tmp_cache, tmp_path):
        """SQLite 缓存在新 FTCache 实例中可恢复。"""
        p = make_csv(tmp_path / "test.csv", [
            ["PART_ID", "SOFT_BIN", "DC_T1"],
            ["SN001", "1", "2.5"],
        ])
        state = {"_df": pd.DataFrame({"x": [42]}), "_units": {}}
        tmp_cache.put(str(p), state)

        # 模拟新进程：创建新 FTCache 实例，指向同一目录
        cache2 = FTCache(tmp_cache._cache_dir)
        got = cache2.get(str(p))
        assert got is not None
        assert got["_df"].iloc[0]["x"] == 42

    def test_memory_lru_eviction(self, tmp_path):
        """LRU 超出最大值时淘汰最久未用的。"""
        cache = FTCache(tmp_path / "lru_cache")
        cache._max_memory = 3  # 缩小

        files = []
        for i in range(5):
            p = make_csv(tmp_path / f"lru_{i}.csv", [
                ["PART_ID", "SOFT_BIN", "DC_T1"],
                [f"SN{i:03d}", "1", "2.5"],
            ])
            files.append(p)
            cache.put(str(p), {"_df": pd.DataFrame({"i": [i]}), "_units": {}})

        # 只有最后 3 个在内存
        assert len(cache._memory) == 3
        assert str(files[0]) not in cache._memory  # 被淘汰
        assert str(files[2]) in cache._memory       # 保留
        assert str(files[4]) in cache._memory       # 最新


# ═══════════════════════════════════════════════════════════════════
#  FTData 集成
# ═══════════════════════════════════════════════════════════════════


class TestFTDataCacheIntegration:

    def test_cached_ftdata_returns_same_data(self, tmp_path, tmp_cfg):
        """缓存前后的 FTData 返回相同数据。"""
        csv_path = make_csv(tmp_path / "test.csv", [
            ["PART_ID", "SOFT_BIN", "DC_T1", "DC_T2"],
            ["Unit", "", "V", "mA"],
            ["Lower", "", "0", "0"],
            ["Higher", "", "5", "100"],
            ["SN001", "1", "2.5", "50"],
            ["SN002", "1", "3.0", "75"],
        ])

        # 第一次读取（解析）
        ft1 = FTData(str(csv_path), str(tmp_cfg))

        # 第二次读取（缓存）
        ft2 = FTData(str(csv_path), str(tmp_cfg))

        assert len(ft1.data) == len(ft2.data)
        assert list(ft1.data.columns) == list(ft2.data.columns)
        assert ft1.data["DC_T1"].iloc[0] == ft2.data["DC_T1"].iloc[0]
        assert ft1.data["DC_T2"].iloc[0] == ft2.data["DC_T2"].iloc[0]

    def test_force_reparse(self, tmp_path, tmp_cfg):
        """force_reparse=True 跳过缓存重新解析。"""
        csv_path = make_csv(tmp_path / "test.csv", [
            ["PART_ID", "SOFT_BIN", "DC_T1"],
            ["Unit", "", "V"],
            ["Lower", "", "0"],
            ["Higher", "", "5"],
            ["SN001", "1", "2.5"],
        ])

        ft1 = FTData(str(csv_path), str(tmp_cfg))
        assert len(ft1.data) == 1

        # 修改文件
        make_csv(csv_path, [
            ["PART_ID", "SOFT_BIN", "DC_T1"],
            ["Unit", "", "V"],
            ["Lower", "", "0"],
            ["Higher", "", "5"],
            ["SN001", "1", "2.5"],
            ["SN002", "1", "3.0"],
        ])
        time.sleep(0.01)

        # 强制重新解析
        ft2 = FTData(str(csv_path), str(tmp_cfg), force_reparse=True)
        assert len(ft2.data) == 2

    def test_cached_meta_columns(self, tmp_path, tmp_cfg):
        """缓存后 test_columns / meta_columns 正确。"""
        csv_path = make_csv(tmp_path / "test.csv", [
            ["PART_ID", "SOFT_BIN", "DC_T1"],
            ["Unit", "", "V"],
            ["Lower", "", "0"],
            ["Higher", "", "5"],
            ["SN001", "1", "2.5"],
        ])
        ft1 = FTData(str(csv_path), str(tmp_cfg))
        ft2 = FTData(str(csv_path), str(tmp_cfg))
        assert ft1.test_columns == ft2.test_columns
        assert ft1.meta_columns == ft2.meta_columns
        assert ft1.units == ft2.units

    def test_cache_after_file_change(self, tmp_path, tmp_cfg):
        """文件修改后自动重解析（不传 force_reparse）。"""
        csv_path = make_csv(tmp_path / "test.csv", [
            ["PART_ID", "SOFT_BIN", "DC_T1"],
            ["Unit", "", "V"],
            ["Lower", "", "0"],
            ["Higher", "", "5"],
            ["SN001", "1", "2.5"],
        ])
        ft1 = FTData(str(csv_path), str(tmp_cfg))
        assert len(ft1.data) == 1

        # 文件变大
        time.sleep(0.01)
        make_csv(csv_path, [
            ["PART_ID", "SOFT_BIN", "DC_T1"],
            ["Unit", "", "V"],
            ["Lower", "", "0"],
            ["Higher", "", "5"],
            ["SN001", "1", "2.5"],
            ["SN002", "1", "3.0"],
            ["SN003", "1", "3.5"],
        ])

        # 文件已变 → 自动重解析
        ft2 = FTData(str(csv_path), str(tmp_cfg))
        assert len(ft2.data) == 3


# ═══════════════════════════════════════════════════════════════════
#  搜索功能
# ═══════════════════════════════════════════════════════════════════


class TestSearch:

    def test_search_by_columns(self, tmp_cache, tmp_path):
        """按测试列名搜索文件。"""
        for i in range(3):
            cols = ["PART_ID", "SOFT_BIN", f"DC_TEST_{i:03d}"]
            p = make_csv(tmp_path / f"f{i}.csv", [
                cols, ["Unit", "", "V"],
                ["Lower", "", "0"], ["Higher", "", "5"],
                ["SN001", "1", "2.5"],
            ])
            state = {
                "_df": pd.DataFrame({c: [1.0] for c in cols}),
                "_units": {},
                "_meta_header": ["PART_ID", "SOFT_BIN"],
                "_test_header": [f"DC_TEST_{i:03d}"],
                "_fmt": {"sig": {"format_id": "TEST"}},
            }
            tmp_cache.put(str(p), state)

        results = tmp_cache.search_by_columns("DC_TEST_001")
        assert len(results) == 1
        assert "f1.csv" in results[0]["file_path"]
