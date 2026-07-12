"""Tests for β diagnostic plots."""
import numpy as np
import pytest

from core.tddb.beta_diagnostics import (
    make_beta_vs_vgs_plot,
    make_beta_vs_temp_plot,
    make_beta_vs_area_plot,
)


class TestBetaDiagnostics:
    """β diagnostic plot generation."""

    @pytest.fixture
    def sample_beta_data(self):
        """Typical β data across conditions."""
        return {
            "Vgs": [5.0, 5.5, 6.0, 5.0, 5.5, 6.0],
            "Temperature": [25, 25, 25, 125, 125, 125],
            "Area": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            "beta": [1.8, 2.1, 1.9, 1.7, 2.0, 1.8],
            "group": ["A", "A", "A", "A", "A", "A"],
        }

    def test_beta_vs_vgs_returns_figure(self, sample_beta_data):
        fig = make_beta_vs_vgs_plot(sample_beta_data)
        assert fig is not None
        assert len(fig.data) > 0  # Has traces

    def test_beta_vs_vgs_by_group(self, sample_beta_data):
        """When multiple groups, each should be a separate trace."""
        data = sample_beta_data.copy()
        data["group"] = ["A", "A", "A", "B", "B", "B"]
        fig = make_beta_vs_vgs_plot(data)
        assert len(fig.data) == 2  # One trace per group

    def test_beta_vs_temp_returns_figure(self, sample_beta_data):
        fig = make_beta_vs_temp_plot(sample_beta_data)
        assert fig is not None
        assert len(fig.data) > 0

    def test_beta_vs_area_returns_figure(self, sample_beta_data):
        fig = make_beta_vs_area_plot(sample_beta_data)
        assert fig is not None
        assert len(fig.data) > 0

    def test_x_axis_labels(self, sample_beta_data):
        fig = make_beta_vs_vgs_plot(sample_beta_data)
        assert "Vgs" in fig.layout.xaxis.title.text or "V" in fig.layout.xaxis.title.text

    def test_y_axis_label_contains_beta(self, sample_beta_data):
        fig = make_beta_vs_vgs_plot(sample_beta_data)
        assert "β" in fig.layout.yaxis.title.text or "beta" in fig.layout.yaxis.title.text.lower()

    def test_empty_data_raises(self):
        with pytest.raises(ValueError):
            make_beta_vs_vgs_plot({"Vgs": [], "beta": [], "group": [], "Temperature": [], "Area": []})
