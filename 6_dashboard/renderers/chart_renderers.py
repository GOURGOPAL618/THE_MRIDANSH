"""
MRIDANSH : Chart Renderers Engine
Reusable Plotly 2D/3D Visualization Components (Hardened for Scientific Integrity)
"""

import math
from typing import Any, List, Optional, Union

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def plot_moisture_depth_profile(depths, moisture_profile, is_demo: bool = True):
    """Renders 2D Depth vs Volumetric Water Content Curve with honest empty-state handling."""
    if moisture_profile is None or len(moisture_profile) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="Soil-Moisture Profile Unavailable<br><sup>No verified depth measurements connected</sup>",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color="#AAAAAA"),
        )
        fig.update_layout(
            title="Volumetric Water Content vs Soil Depth (UNAVAILABLE)",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            template="plotly_dark",
            height=380,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        return fig

    # Convert to numpy array safely
    m_arr = np.asarray(moisture_profile, dtype=float)
    # Convert Infs to NaNs so they don't produce distorted spikes or zeros
    m_arr[np.isinf(m_arr)] = np.nan

    if np.all(np.isnan(m_arr)):
        fig = go.Figure()
        fig.add_annotation(
            text="Invalid Depth Profile<br><sup>All measurements are NaN / NoData</sup>",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color="#AAAAAA"),
        )
        fig.update_layout(
            title="Volumetric Water Content vs Soil Depth (INVALID DATA)",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            template="plotly_dark",
            height=380,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        return fig

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=m_arr * 100,
            y=depths,
            mode="lines+markers",
            name="Soil Moisture (%)",
            line=dict(color="#1f77b4", width=3),
            marker=dict(size=8, color="#0d47a1"),
            connectgaps=False,  # Preserve NaNs as gaps, do not plot as zero
        )
    )

    title_suffix = " (DEMO DATA)" if is_demo else ""
    fig.update_layout(
        title=f"Volumetric Water Content vs Soil Depth{title_suffix}",
        xaxis_title="Volumetric Moisture (%)",
        yaxis_title="Depth (cm)",
        yaxis=dict(autorange="reversed"),  # Surface at top
        template="plotly_dark",
        height=380,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    return fig


def plot_npk_distribution(nitrogen=None, phosphorus=None, potassium=None, is_demo: bool = True):
    """Renders Agronomic NPK Status Bar Chart or honest empty state."""
    if not is_demo and nitrogen is None and phosphorus is None and potassium is None:
        fig = go.Figure()
        fig.add_annotation(
            text="Biochemical Soil Nutrients Unavailable<br><sup>Connect verified chemical spectroscopy or soil laboratory inputs</sup>",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color="#AAAAAA"),
        )
        fig.update_layout(
            title="Soil Nutrient Concentrations (UNAVAILABLE)",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            template="plotly_dark",
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        return fig

    n_val = 120.0 if nitrogen is None else float(nitrogen)
    p_val = 30.0 if phosphorus is None else float(phosphorus)
    k_val = 150.0 if potassium is None else float(potassium)

    df_npk = pd.DataFrame(
        {
            "Nutrient": ["Nitrogen (N)", "Phosphorus (P)", "Potassium (K)"],
            "Estimated Level": [n_val, p_val, k_val],
            "Optimal Baseline": [120.0, 30.0, 150.0],
        }
    )

    title_text = "Estimated Soil Nutrient Concentration (DEMO DATA — NOT CALIBRATED)" if is_demo else "Soil Nutrient Concentration (kg/ha)"

    fig = px.bar(
        df_npk,
        x="Nutrient",
        y=["Estimated Level", "Optimal Baseline"],
        barmode="group",
        title=title_text,
        color_discrete_sequence=["#00cc96", "#ab63fa"],
        template="plotly_dark",
        height=350,
    )

    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    return fig


def plot_3d_soil_stratification():
    """Renders 3D GeoTechnical SubSurface Soil Profile Visualizer (Demonstration Scaffolding)."""

    x = np.linspace(0, 50, 20)
    y = np.linspace(0, 50, 20)
    X, Y = np.meshgrid(x, y)

    # Simulated geometric subsurface layers (Scaffolding only)
    Z_topsoil = -(0.1 * np.sin(X / 5) * np.cos(Y / 5) + 0.2)
    Z_subsoil = Z_topsoil - (0.5 * np.ones_like(X))
    Z_bedrock = Z_subsoil - (1.0 * np.ones_like(X))

    fig = go.Figure()

    # Layer 1 - Topsoil
    fig.add_trace(
        go.Surface(
            z=Z_topsoil,
            x=X,
            y=Y,
            colorscale="Greens",
            name="Topsoil (Synthetic Surface)",
            showscale=False,
        )
    )

    # Layer 2 - Intermediate
    fig.add_trace(
        go.Surface(
            z=Z_subsoil,
            x=X,
            y=Y,
            colorscale="YlOrBr",
            name="Clay/Silt (Synthetic Interface)",
            showscale=False,
        )
    )

    # Layer 3 - Bedrock Boundary
    fig.add_trace(
        go.Surface(
            z=Z_bedrock,
            x=X,
            y=Y,
            colorscale="Blues",
            name="Bedrock (Synthetic Boundary)",
            showscale=False,
        )
    )

    fig.update_layout(
        title="DEMO — Subsurface 3D Soil Stratification Mesh (Synthetic Geometric Scaffolding)",
        scene=dict(
            xaxis_title="East (m)",
            yaxis_title="North (m)",
            zaxis_title="Depth (m)",
            aspectratio=dict(x=1, y=1, z=0.4),
        ),
        template="plotly_dark",
        height=450,
        margin=dict(l=10, r=10, t=40, b=10),
    )

    return fig


def plot_ground_stability_gauge(stability_index: Optional[float] = None, is_demo: bool = True) -> go.Figure:
    """Renders Gauge Chart for GeoTechnical Ground Stability Index (DEMO DATA or UNAVAILABLE)."""
    if stability_index is None:
        fig = go.Figure()
        fig.add_annotation(
            text="⚠️ GROUND STABILITY GAUGE UNAVAILABLE<br>Sensor telemetry and stability model disconnected",
            showarrow=False,
            font=dict(size=14, color="#ef553b"),
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
        )
        fig.update_layout(
            template="plotly_dark",
            height=300,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            title="Ground Stability Score (UNAVAILABLE)",
        )
        return fig

    try:
        idx_val = float(stability_index)
        if not math.isfinite(idx_val) or idx_val < 0.0 or idx_val > 1.0:
            fig = go.Figure()
            fig.add_annotation(
                text="⚠️ INVALID STABILITY VALUE<br>Score outside valid [0.0, 1.0] range or non-finite",
                showarrow=False,
                font=dict(size=14, color="#ef553b"),
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
            )
            fig.update_layout(
                template="plotly_dark",
                height=300,
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                title="Ground Stability Score (INVALID DATA)",
            )
            return fig
    except (ValueError, TypeError):
        fig = go.Figure()
        fig.add_annotation(
            text="⚠️ CORRUPTED STABILITY INPUT",
            showarrow=False,
            font=dict(size=14, color="#ef553b"),
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
        )
        fig.update_layout(
            template="plotly_dark",
            height=300,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            title="Ground Stability Score (ERROR)",
        )
        return fig

    title_label = "Ground Stability Score (DEMO DATA — UNVALIDATED)" if is_demo else "Ground Stability Score (%)"

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=idx_val * 100,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": title_label},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#00cc96" if idx_val > 0.7 else "#ef553b"},
                "steps": [
                    {"range": [0, 40], "color": "rgba(239, 85, 59, 0.3)"},
                    {"range": [40, 70], "color": "rgba(255, 161, 90, 0.3)"},
                    {"range": [70, 100], "color": "rgba(0, 204, 150, 0.3)"},
                ],
            },
        )
    )

    fig.update_layout(template="plotly_dark", height=300)
    return fig
