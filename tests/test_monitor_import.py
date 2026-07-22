"""TDDB 监控数据导入和分析测试。"""
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

from core.tddb.monitor_import import (
    ColumnMapping,
    MonitoredChannel,
    TBDCandidate,
    QBDResult,
    generate_dummy_monitor_data,
    parse_monitor_file,
    parse_header_rows,
    get_sheet_names,
    detect_tbd_points,
    calculate_qbd,
    process_all_files,
    _find_first_by_current_drop,
    _find_first_by_rate_exceed,
    _find_first_by_current_limit,
    _exclude_half_failure,
)


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def dummy_file():
    """生成一个带失效的 dummy 文件供测试使用。"""
    path = generate_dummy_monitor_data(
        num_channels=4,
        num_points=50,
        voltage=-38.0,
        temperature=150.0,
        base_current_ua=0.5,
        failure_rate=0.5,  # 50% 通道失效 — 确保有数据
        seed=42,
        output_path=None,  # 临时文件
    )
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def default_mapping():
    return ColumnMapping(
        sheet_index=0,
        sheet_name="Sheet1",
        header_row=6,
        time_col="采样时间",
        time_from_sampling=True,
        voltage_col="电压(V)",
        current_keyword="电流",
        current_unit="uA",
        selected_channels=["电流1(uA)", "电流2(uA)", "电流3(uA)", "电流4(uA)"],
        has_temp=True,
        temp_col="烘箱温度(摄氏度)",
        temp_unit="℃",
    )


# ── Dummy 数据生成测试 ──────────────────────────────────────────


class TestGenerateDummyData:
    def test_generates_valid_excel(self):
        path = generate_dummy_monitor_data(
            num_channels=4, num_points=20, output_path=None)
        assert path.endswith(".xlsx")
        assert os.path.getsize(path) > 0
        os.unlink(path)

    def test_has_header_and_data(self, dummy_file):
        rows = parse_header_rows(dummy_file, 0, 50)
        assert len(rows) > 6  # 有标题行+空行+数据
        # 第7行（index 6）是表头
        header = rows[6]
        header_text = " | ".join(str(c) for c in header)
        assert "电流" in header_text
        assert "电压" in header_text

    def test_has_sheet_names(self, dummy_file):
        sheets = get_sheet_names(dummy_file)
        assert len(sheets) > 0
        assert "Sheet1" in sheets

    def test_csv_has_no_sheets(self):
        # CSV 无 sheet
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            f.write("a,b,c\n1,2,3\n")
            csv_path = f.name
        try:
            sheets = get_sheet_names(csv_path)
            assert sheets == []
        finally:
            os.unlink(csv_path)


# ── 文件解析测试 ────────────────────────────────────────────────


class TestParseMonitorFile:
    def test_parse_sampling_time(self, dummy_file, default_mapping):
        channels, voltage, temp = parse_monitor_file(dummy_file, default_mapping)
        assert len(channels) == 4
        assert voltage is not None and voltage != 0
        assert temp is not None
        for ch in channels:
            assert len(ch.time) > 0
            assert len(ch.current) > 0
            assert ch.time[0] >= 0  # 时间从 0 开始
            assert np.all(np.diff(ch.time) >= 0)  # 时间单调递增

    def test_parse_aging_time(self, dummy_file):
        mapping = ColumnMapping(
            sheet_index=0, header_row=6,
            time_col="老化时间(分)", time_from_sampling=False,
            aging_time_unit="分",
            voltage_fixed=-39.0,
            current_keyword="电流", current_unit="uA",
            selected_channels=["电流1(uA)", "电流2(uA)"],
            has_temp=True, temp_col="烘箱温度(摄氏度)", temp_unit="℃",
        )
        channels, voltage, temp = parse_monitor_file(dummy_file, mapping)
        assert len(channels) == 2
        # 老化时间单位是分，所以最后一秒 = 49 * 60 = 2940
        assert abs(channels[0].time[-1] - 49 * 60) < 1

    def test_parse_no_temp(self, dummy_file):
        mapping = ColumnMapping(
            sheet_index=0, header_row=6,
            time_col="采样时间", time_from_sampling=True,
            voltage_col="电压(V)",
            current_keyword="电流", current_unit="uA",
            selected_channels=["电流1(uA)"],
            has_temp=False, temp_col="", temp_unit="℃",
        )
        _, _, temp = parse_monitor_file(dummy_file, mapping)
        assert temp is None

    def test_parse_invalid_column(self, dummy_file):
        mapping = ColumnMapping(
            sheet_index=0, header_row=6,
            time_col="不存在的列", time_from_sampling=True,
            voltage_col="电压(V)",
            current_keyword="电流", current_unit="uA",
            selected_channels=["电流1(uA)"],
            has_temp=True, temp_col="烘箱温度(摄氏度)", temp_unit="℃",
        )
        with pytest.raises(ValueError, match="时间列"):
            parse_monitor_file(dummy_file, mapping)


# ── TBD 检测测试 ────────────────────────────────────────────────


class TestDetectTBD:
    def test_current_drop(self):
        t = np.array([0, 10, 20, 30, 40])
        c = np.array([0.5, 0.5, 0.0, 0.0, 0.0])
        idx = _find_first_by_current_drop(t, c, threshold=0.01)
        assert idx == 2  # 第 3 个点降为 0

    def test_rate_exceed(self):
        t = np.array([0, 10, 20, 30])
        c = np.array([0.5, 0.5, 0.6, 15.0])  # 15/0.6 = 25 > 10
        idx = _find_first_by_rate_exceed(t, c, rate_limit=10.0)
        assert idx == 3

    def test_current_limit(self):
        t = np.array([0, 10, 20, 30])
        c = np.array([0.3, 0.5, 1.5, 2.0])  # 1.5 > 1.0
        idx = _find_first_by_current_limit(t, c, current_limit=1.0)
        assert idx == 2

    def test_no_failure(self):
        t = np.array([0, 10, 20, 30])
        c = np.array([0.5, 0.5, 0.5, 0.5])
        idx = _find_first_by_current_drop(t, c)
        assert idx is None
        idx = _find_first_by_rate_exceed(t, c, rate_limit=10.0)
        assert idx is None

    def test_exclude_half_failure(self):
        candidates = [
            TBDCandidate("ch1", 100, 1.0, "drop", 0, confirmed=True),
            TBDCandidate("ch2", 100, 1.0, "drop", 0, confirmed=True),
            TBDCandidate("ch3", 100, 1.0, "drop", 0, confirmed=True),
            TBDCandidate("ch4", 200, 1.0, "drop", 0, confirmed=True),
        ]
        result = _exclude_half_failure(candidates, total_channels=4)
        # 3 个在 100s > 4/2=2 → 排除；1 个在 200s ≤ 2 → 保留
        assert len(result) == 1
        assert result[0].tbd_time == 200

    def test_integration_with_dummy_data(self, dummy_file, default_mapping):
        channels, _, _ = parse_monitor_file(dummy_file, default_mapping)
        all_candidates = []
        for ch in channels:
            cands = detect_tbd_points(
                ch, enable_drop=True, enable_rate=True, enable_limit=True,
                current_limit_ua=0.8, rate_limit=10.0,
            )
            all_candidates.extend(cands)
        # 应该有检测到失效点（50% 失效率）
        assert len(all_candidates) > 0
        for c in all_candidates:
            assert c.tbd_time > 0
            assert c.failure_reason

    def test_exclude_half_failure_integration(self, dummy_file):
        """验证排除超过一半同时失效的逻辑：模拟相同时间点多通道失效。"""
        from core.tddb.monitor_import import MonitoredChannel

        channels = []
        for i in range(5):
            t = np.array([0, 50, 100, 150, 200])
            c = np.array([0.5, 0.5, 0.0, 0.0, 0.0])
            channels.append(MonitoredChannel(
                name=f"ch{i}", time=t, current=c * 1e-6,
                voltage=-38, temperature=150, file_path=dummy_file))
        for i in range(3):
            t = np.array([0, 50, 100, 150, 200])
            c = np.array([0.5, 0.5, 0.5, 15.0, 15.0])
            channels.append(MonitoredChannel(
                name=f"ch{i+5}", time=t, current=c * 1e-6,
                voltage=-38, temperature=150, file_path=dummy_file))

        all_cands = []
        for ch in channels:
            cands = detect_tbd_points(ch, enable_drop=True, enable_limit=True,
                                       current_limit_ua=0.8)
            all_cands.extend(cands)

        assert len(all_cands) == 8, f"expected 8 candidates, got {len(all_cands)}"
        filtered = _exclude_half_failure(all_cands, total_channels=8)
        assert len(filtered) == 3, f"expected 3 after exclude, got {len(filtered)}"
        for f in filtered:
            assert f.tbd_time == 150, f"expected TBD at 150s, got {f.tbd_time}"


# ── QBD 计算测试 ────────────────────────────────────────────────
class TestCalculateQBD:
    def test_constant_current(self):
        ch = MonitoredChannel(
            name="test",
            time=np.array([0, 10, 20, 30]),
            current=np.array([1e-6, 1e-6, 1e-6, 1e-6]),
            voltage=5.0, temperature=25.0, file_path="test.xlsx",
        )
        # I = 1uA, t = 30s, Q = 30 * 1e-6 = 3e-5 C
        qbd = calculate_qbd(ch, 30)
        assert abs(qbd - 3e-5) < 1e-7

    def test_zero_current(self):
        ch = MonitoredChannel(
            name="test",
            time=np.array([0, 10, 20]),
            current=np.array([0.0, 0.0, 0.0]),
            voltage=5.0, temperature=25.0, file_path="test.xlsx",
        )
        qbd = calculate_qbd(ch, 20)
        assert qbd == 0.0

    def test_with_dummy_data(self, dummy_file, default_mapping):
        channels, _, _ = parse_monitor_file(dummy_file, default_mapping)
        for ch in channels:
            cands = detect_tbd_points(ch)
            if cands:
                qbd = calculate_qbd(ch, cands[0].tbd_time)
                assert qbd >= 0
                assert isinstance(qbd, float)


# ── 批量处理测试 ────────────────────────────────────────────────


class TestProcessAll:
    def test_process_one_file(self, dummy_file, default_mapping):
        configs = {dummy_file: default_mapping}
        results, rows = process_all_files(configs)
        assert len(rows) > 0
        for row in rows:
            assert "文件" in row
            assert "通道" in row
            assert "TBD时间(秒)" in row
