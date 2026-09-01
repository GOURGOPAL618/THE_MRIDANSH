"""
MRIDANSH : Chart Renderers Engine
Reusable Plotly 2D/3D Visualization Components
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def plot_moisture_depth_profile(depths, moisture_profile):
    """Renders 2D Depth vs Volumetric Water Content Curve."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=moisture_profile * 100,
            y=depths,
            mode="lines+markers",
            name="Soil Moisture (%)",
            line=dict(color="#1f77b4", width=3),
            marker=dict(size=8, color="#0d47a1"),
        )
    )

    fig.update_layout(
        title="Volumetric Water Content vs Soil Depth",
        xaxis_title="Volumetric Moisture (%)",
        yaxis_title="Depth (cm)",
        yaxis=dict(autorange="reversed"),  # Surface at top
        template="plotly_dark",
        height=380,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    return fig


def plot_npk_distribution(nitrogen, phosphorus, potassium):
    """Renders Agronomic NPK Status Bar Chart."""
    df_npk = pd.DataFrame(
        {
            "Nutrient": ["Nitrogen (N)", "Phosphorus (P)", "Potassium (K)"],
            "Estimated Level": [nitrogen, phosphorus, potassium],
            "Optimal Baseline": [120.0, 30.0, 150.0],
        }
    )

    fig = px.bar(
        df_npk,
        x="Nutrient",
        y=["Estimated Level", "Optimal Baseline"],
        barmode="group",
        title="Estimated Soil Nutrient Concentration (kg/ha)",
        color_discrete_sequence=["#00cc96", "#ab63fa"],
        template="plotly_dark",
        height=350,
    )

    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    return fig


def plot_3d_soil_stratification():
    """Renders 3D GeoTechnical SubSurface Soil Profile Visualizer."""

    x = np.linspace(0, 50, 20)
    y = np.linspace(0, 50, 20)
    X, Y = np.meshgrid(x, y)

    # Simulated subsurface layers
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
            name="Topsoil (0-20cm)",
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
            name="Clay/Silt Layer (20-70cm)",
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
            name="Bedrock Boundary (70cm+)",
            showscale=False,
        )
    )

    fig.update_layout(
        title="Subsurface 3D Soil Stratification Mesh",
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


def plot_ground_stability_gauge(stability_index):
    """Renders Gauge Chart For Geo Technical Ground Stability Index."""

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=stability_index * 100,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Ground Stability Score (%)"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#00cc96" if stability_index > 0.7 else "#ef553b"},
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
