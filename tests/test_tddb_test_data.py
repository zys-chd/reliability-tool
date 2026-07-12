"""Tests for TDDB test data generation."""
import numpy as np
import pandas as pd
import pytest

from core.tddb.test_data import (
    make_tddb_dataset,
    generate_weibull_sample,
    make_tddb_excel,
)


class TestGenerateWeibullSample:
    """Test raw Weibull random sample generation."""

    def test_single_condition(self):
        data = generate_weibull_sample(beta=2.0, eta=100, n=20, seed=42)
        assert len(data) == 20
        assert np.all(data > 0)
        # With β=2, η=100, the median should be roughly in 50-200 range
        median = np.median(data)
        assert 20 < median < 500

    def test_different_seeds_different_data(self):
        a = generate_weibull_sample(beta=2.0, eta=100, n=50, seed=1)
        b = generate_weibull_sample(beta=2.0, eta=100, n=50, seed=2)
        # Same params but different seeds should differ
        assert not np.array_equal(a, b)

    def test_same_seed_reproducible(self):
        a = generate_weibull_sample(beta=1.5, eta=200, n=30, seed=42)
        b = generate_weibull_sample(beta=1.5, eta=200, n=30, seed=42)
        np.testing.assert_array_equal(a, b)


class TestMakeTDDBDataset:
    """Test the main dataset builder."""

    def test_basic_structure(self):
        df = make_tddb_dataset(
            voltages=[5.5, 5.8, 6.1],
            beta=2.0,
            eta_at_vmin=500,
            n_per_cond=15,
            seed=42,
        )
        assert isinstance(df, pd.DataFrame)
        expected_cols = {"PART_ID", "Vgs", "TBD", "QBD", "ignore",
                         "group", "Temperature", "Gate Oxide Area",
                         "老化板通道", "comment"}
        assert expected_cols.issubset(set(df.columns))

        # 3 voltages × 15 each = 45 rows
        assert len(df) == 45
        assert sorted(df["Vgs"].unique()) == [5.5, 5.8, 6.1]

    def test_eta_decreases_with_voltage(self):
        """Higher voltage → faster degradation → smaller TBD (lower η)."""
        df = make_tddb_dataset(
            voltages=[5.0, 5.5, 6.0],
            beta=2.0,
            eta_at_vmin=1000,
            n_per_cond=50,  # large sample for stable estimate
            seed=42,
        )
        medians = df.groupby("Vgs")["TBD"].median()
        # η decreases as voltage increases
        assert medians[5.0] > medians[5.5] > medians[6.0]

    def test_multiple_groups(self):
        df = make_tddb_dataset(
            voltages=[5.5, 5.8],
            groups=["湿氧", "干氧"],
            beta=2.0,
            eta_at_vmin=500,
            n_per_cond=10,
            seed=42,
        )
        assert sorted(df["group"].unique()) == ["干氧", "湿氧"]
        # 2 voltages × 2 groups × 10 = 40 rows
        assert len(df) == 40

    def test_temperature_column(self):
        df = make_tddb_dataset(
            voltages=[5.5, 5.8],
            temperatures=[25, 85, 125],
            beta=2.0,
            eta_at_vmin=500,
            n_per_cond=10,
            seed=42,
        )
        assert sorted(df["Temperature"].unique()) == [25, 85, 125]
        # 2V × 3T × 10 = 60
        assert len(df) == 60

    def test_area_column(self):
        df = make_tddb_dataset(
            voltages=[5.5, 5.8],
            areas=[1.0, 4.0],
            beta=2.0,
            eta_at_vmin=500,
            n_per_cond=10,
            seed=42,
        )
        assert sorted(df["Gate Oxide Area"].unique()) == [1.0, 4.0]
        # 2V × 2A × 10 = 40
        assert len(df) == 40

    def test_ignore_flag_some_rows(self):
        """Some rows should be randomly flagged as ignore (no check on exact count)."""
        df = make_tddb_dataset(
            voltages=[5.5, 5.8, 6.1],
            beta=2.0,
            eta_at_vmin=500,
            n_per_cond=20,
            seed=42,
            ignore_prob=0.1,
        )
        assert df["ignore"].sum() > 0
        assert df["ignore"].sum() < len(df)

    def test_qbd_column_non_null(self):
        """QBD should be non-NaN if cumulative_current is provided."""
        df = make_tddb_dataset(
            voltages=[5.5, 5.8],
            beta=2.0,
            eta_at_vmin=500,
            n_per_cond=10,
            seed=42,
            cumulative_current=1e-6,
        )
        assert df["QBD"].notna().all()
        assert (df["QBD"] > 0).all()

    def test_reproducible_seed(self):
        df1 = make_tddb_dataset(voltages=[5.5], beta=2.0, eta_at_vmin=500,
                                n_per_cond=10, seed=12345)
        df2 = make_tddb_dataset(voltages=[5.5], beta=2.0, eta_at_vmin=500,
                                n_per_cond=10, seed=12345)
        pd.testing.assert_frame_equal(df1, df2)


class TestMakeTDDBExcel:
    """Test Excel file generation (integration check)."""

    def test_excel_write(self, tmp_path):
        path = tmp_path / "tddb_test.xlsx"
        df = make_tddb_dataset(voltages=[5.5, 5.8], beta=2.0,
                               eta_at_vmin=500, n_per_cond=10, seed=42)
        result = make_tddb_excel(df, path)
        assert result.exists()
        assert result.stat().st_size > 0

        # Verify can read back with openpyxl
        import openpyxl
        wb = openpyxl.load_workbook(path)
        assert "Sheet1" in wb.sheetnames
        ws = wb["Sheet1"]
        header = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
        assert "PART_ID" in header
        assert "TBD" in header
        wb.close()

    def test_excel_with_multiple_sheets(self, tmp_path):
        df = make_tddb_dataset(voltages=[5.5, 5.8], beta=2.0,
                               eta_at_vmin=500, n_per_cond=5, seed=42)
        path = tmp_path / "multi_sheet.xlsx"
        make_tddb_excel(df, path, sheet_name="试验1")
        import openpyxl
        wb = openpyxl.load_workbook(path)
        assert "试验1" in wb.sheetnames
        wb.close()
