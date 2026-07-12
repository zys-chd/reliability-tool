"""β diagnostic plots for TDDB analysis.

Generates plotly figures showing β vs. stress conditions.
Helps identify whether the Weibull shape parameter depends
on voltage, temperature, or area — indicating possible
changes in breakdown mechanism.
"""
import numpy as np
import pandas as pd

# Import plotly lazily — only when generating plots

__all__ = [
    "make_beta_vs_vgs_plot",
    "make_beta_vs_temp_plot",
    "make_beta_vs_area_plot",
]


def _validate_beta_data(beta_data: dict) -> pd.DataFrame:
    """Validate and convert beta data dict to DataFrame."""
    required = {"Vgs", "Temperature", "Area", "beta", "group"}
    if not required.issubset(beta_data.keys()):
        missing = required - set(beta_data.keys())
        raise ValueError(f"Missing required fields: {missing}")

    df = pd.DataFrame(beta_data)
    if len(df) == 0:
        raise ValueError("Beta data is empty")

    return df


def _make_scatter_plot(
    df: pd.DataFrame,
    x_col: str,
    x_label: str,
    title: str,
) -> "plotly.graph_objects.Figure":
    """Create a scatter plot of β vs a given x variable, grouped by group."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig = go.Figure()

    for grp in sorted(df["group"].unique()):
        grp_df = df[df["group"] == grp].sort_values(x_col)
        fig.add_trace(go.Scatter(
            x=grp_df[x_col],
            y=grp_df["beta"],
            mode="markers+lines",
            name=str(grp),
            marker=dict(size=10),
            line=dict(dash="dash", width=1),
        ))

    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title="β (Weibull 斜率)",
        template="plotly_white",
        hovermode="closest",
    )

    return fig


def make_beta_vs_vgs_plot(beta_data: dict) -> "plotly.graph_objects.Figure":
    """β vs Vgs scatter plot, one trace per group."""
    df = _validate_beta_data(beta_data)
    return _make_scatter_plot(
        df, "Vgs", "Vgs / V",
        "β vs Vgs (固定温度/面积)",
    )


def make_beta_vs_temp_plot(beta_data: dict) -> "plotly.graph_objects.Figure":
    """β vs Temperature scatter plot, one trace per group."""
    df = _validate_beta_data(beta_data)
    return _make_scatter_plot(
        df, "Temperature", "Temperature / ℃",
        "β vs Temperature (固定电压/面积)",
    )


def make_beta_vs_area_plot(beta_data: dict) -> "plotly.graph_objects.Figure":
    """β vs Gate Oxide Area scatter plot, one trace per group."""
    df = _validate_beta_data(beta_data)
    return _make_scatter_plot(
        df, "Area", "Gate Oxide Area / μm²",
        "β vs Area (固定电压/温度)",
    )
