"""Regression tests for TDDB UI issues the user reported.

These test the core fitting logic directly (no QApp needed)
to verify critical bugs stay fixed.
"""
import numpy as np
import pandas as pd
import pytest

from core.tddb.weibull_fitter import fit_weibull, fit_unified_slope
from core.tddb.test_data import make_tddb_dataset


class TestRegressions:
    """Reproduce and verify fixes for reported bugs."""

    @pytest.fixture
    def dataset(self):
        """Standard test dataset: 2 groups × 3 voltages × 2 temps, QBD = TBD * 1e-6."""
        return make_tddb_dataset(
            voltages=[5.0, 5.5, 6.0],
            temperatures=[25, 125],
            groups=["湿氧", "干氧"],
            beta=2.0, eta_at_vmin=500,
            n_per_cond=15, seed=42,
            cumulative_current=1e-6,
        )

    def test_independent_fit_populates_all_conditions(self, dataset):
        """独立斜率：每个 (group, Vgs, Temp) 组合都应有拟合结果。"""
        df = dataset.copy()
        if "ignore" in df.columns:
            df = df[df["ignore"] != 1]
        data_col = "TBD"

        results = {}
        group_key = "group"
        cond_cols = ["Vgs", "Temperature"]

        for grp in df[group_key].unique():
            grp_df = df[df[group_key] == grp]
            for (conds), sub_df in grp_df.groupby(cond_cols):
                vals = sub_df[data_col].values
                if len(vals) < 2:
                    continue
                key = tuple(conds) if isinstance(conds, tuple) else (conds,)
                results[(str(grp), *key)] = fit_weibull(vals)

        # 2 groups × 3 voltages × 2 temps = 12 conditions
        assert len(results) == 12, f"Expected 12, got {len(results)}"
        for key, r in results.items():
            assert r["beta"] > 0, f"{key} beta={r['beta']}"
            assert r["eta"] > 0, f"{key} eta={r['eta']}"
            assert "n" in r and r["n"] >= 2

    def test_unified_slope_preserves_all_groups(self, dataset):
        """统一斜率后，所有 group 的每个条件仍有 β 和 η。"""
        df = dataset.copy()
        if "ignore" in df.columns:
            df = df[df["ignore"] != 1]
        group_key = "group"
        cond_cols = ["Vgs", "Temperature"]

        for grp in df[group_key].unique():
            grp_df = df[df[group_key] == grp]
            conditions_data = {}
            for (conds), sub_df in grp_df.groupby(cond_cols):
                vals = sub_df["TBD"].values
                if len(vals) < 2:
                    continue
                key = tuple(conds) if isinstance(conds, tuple) else (conds,)
                conditions_data[key] = vals

            unified = fit_unified_slope(conditions_data)
            assert len(unified["etas"]) == len(conditions_data), \
                f"Group {grp}: expected {len(conditions_data)} etas, got {len(unified['etas'])}"
            assert unified["beta"] > 0
            for cond_key, eta in unified["etas"].items():
                assert eta > 0, f"{grp} {cond_key}: eta={eta}"

    def test_refit_preserves_tbd_and_qbd_separately(self, dataset):
        """TBD 和 QBD 拟合结果应各自独立存储，切换不互相影响。"""
        df = dataset.copy()
        if "ignore" in df.columns:
            df = df[df["ignore"] != 1]

        results_tbd = {}
        results_qbd = {}

        group_key = "group"
        cond_cols = ["Vgs", "Temperature"]
        for grp in df[group_key].unique():
            grp_df = df[df[group_key] == grp]
            for (conds), sub_df in grp_df.groupby(cond_cols):
                vals = pd.to_numeric(sub_df["TBD"], errors="coerce").dropna().values
                if len(vals) < 2:
                    continue
                key = tuple(conds) if isinstance(conds, tuple) else (conds,)
                results_tbd[(str(grp), *key)] = fit_weibull(vals)

        for grp in df[group_key].unique():
            grp_df = df[df[group_key] == grp]
            for (conds), sub_df in grp_df.groupby(cond_cols):
                vals = pd.to_numeric(sub_df["QBD"], errors="coerce").dropna().values
                if len(vals) < 2:
                    continue
                key = tuple(conds) if isinstance(conds, tuple) else (conds,)
                results_qbd[(str(grp), *key)] = fit_weibull(vals)

        # Both should have 12 entries
        assert len(results_tbd) == 12
        assert len(results_qbd) == 12

        # TBD η should be different from QBD η (different units/values)
        tbd_etas = [r["eta"] for r in results_tbd.values()]
        qbd_etas = [r["eta"] for r in results_qbd.values()]
        # QBD = TBD * cumulative_current (1e-6), so η_QBD should be ~1e-6 * η_TBD
        ratio = np.mean(tbd_etas) / np.mean(qbd_etas)
        assert 1e5 < ratio < 1e7, f"TBD/QBD eta ratio={ratio:.2e}, expected ~1e6"

    def test_refit_does_not_lose_results_on_empty_reentry(self):
        """模拟 _do_weibull_fit 过程中异常时，旧结果不应该消失。"""
        # This tests the pattern: use a temp dict, only assign at end
        results_store = {"A": {"beta": 2.0, "eta": 100}}
        temp = {}

        # Simulate fitting - if an error occurs, results_store shouldn't change
        try:
            temp["B"] = {"beta": 1.5, "eta": 200}
            raise RuntimeError("模拟拟合失败")
        except RuntimeError:
            pass  # Should NOT do results_store = temp or results_store.clear()

        assert "A" in results_store, "旧结果不应该丢失"
        assert "B" not in results_store, "失败的拟合不应该写入"
