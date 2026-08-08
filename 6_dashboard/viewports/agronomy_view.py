"""
MRIDANSH : Agronomy Command Viewport (Step 8A)
Agriculture domain layout using reusable chart renderers.
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from renderers.chart_renderers import (
    plot_moisture_depth_profile,
    plot_npk_distribution,
)


def render_agronomy_viewport(soil_state, agronomy_output):
    """Renders the Agronomy Domain Page.

    Parameters:
        soil_state: UnifiedSoilState instance from core engine
        agronomy_output: AgronomicTranslator output dictionary
    """
    st.title("🌱 Agronomy Command & Soil Health Dashboard")
    st.caption(
        "AETHER-MRID1607X Engine | Real-Time Root-Zone Moisture & Bio-Geochemical Analytics"
    )

    # 1. Top KPI Cards
    col1, col2, col3, col4 = st.columns(4)

    root_moisture = agronomy_output.get("root_zone_moisture", 0.28)
    org_carbon = agronomy_output.get("organic_carbon_est", 0.75)
    npk_status = agronomy_output.get("npk_status", "Optimal")
    confidence = soil_state.reliability.confidence_score * 100

    with col1:
        st.metric(
            label="Root-Zone Moisture",
            value=f"{root_moisture * 100:.1f}%",
            delta="+1.2% (24h)",
        )

    with col2:
        st.metric(
            label="Est. Organic Carbon",
            value=f"{org_carbon:.2f} %",
            delta="Healthy",
        )

    with col3:
        st.metric(label="NPK Health Status", value=npk_status)
    with col4:
        st.metric(
            label="Assimilation Confidence",
            value=f"{confidence:.1f}%",
            delta="EnKF Active",
        )

    st.markdown("---")

    # 2. Moisture Stratification Profile
    st.subheader("💧 Subsurface Moisture Stratification (0 - 100 cm)")

    depths = np.array([5, 15, 30, 60, 100])
    moisture_layers = soil_state.hydro.moisture_profile

    fig_depth = plot_moisture_depth_profile(depths, moisture_layers)

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.plotly_chart(fig_depth, use_container_width = True)

    with col_right:
        st.markdown("### 🌾 Crop Suitability Insights")
        st.info(
            f"**Field Status:** {agronomy_output.get('moisture_zone', 'Field Capacity')}\n\n"
            f"• **Topsoil (0-15cm):** {moisture_layers[0]*100:.1f}% — Optimal for seed germination.\n"
            f"• **Rooting Zone (15-60cm):** {moisture_layers[2]*100:.1f}% — Active uptake zone.\n"
            f"• **Subsoil (60-100cm):** {moisture_layers[4]*100:.1f}% — Deep storage."
        )

    st.markdown("---")

    # 3. NPK Nutrient Heatmap
    st.subheader("🧪 Estimated Soil Biogeochemical Health")

    fig_npk = plot_npk_distribution(
        soil_state.biogeo.nitrogen_est,
        soil_state.biogeo.phosphorus_est,
        soil_state.biogeo.potassium_est,
    )

    col_npk1, col_npk2 = st.columns([2, 1])

    with col_npk1:
        st.plotly_chart(fig_npk, use_container_width = True)

    with col_npk2:
        st.markdown("### 📋 Precision Advisory")
        st.success(
            "**Irrigation Recommendation:** Minimal irrigation needed in next 48 hours.\n\n"
            "**Fertilizer Advisory:** Nitrogen level slightly low. Recommended top-dressing: **15 kg/ha Urea**."
        )

    st.markdown("---")

    # 4. Interactive What-If Simulator
    st.subheader("⚡ What-If Scenario Simulator: Rainfall / Water Input")

    rain_input = st.slider(
        "Simulate Additional Water Input (mm)",
        min_value=0,
        max_value=100,
        value=20,
        step=5,
    )

    simulated_moisture = np.clip(
        moisture_layers + (rain_input * 0.0025) / (depths / 10), 0.05, 0.48
    )
    
    fig_sim = go.Figure()
    fig_sim.add_trace(
        go.Scatter(
            x=moisture_layers * 100,
            y=depths,
            mode="lines",
            name="Current State",
            line=dict(color="#7f7f7f", dash="dash"),
        )
    )

    fig_sim.add_trace(
        go.Scatter(
            x=simulated_moisture * 100,
            y=depths,
            mode="lines+markers",
            name=f"After {rain_input}mm Water Input",
            line=dict(color="#00cc96", width=3),
        )
    )

    fig_sim.update_layout(
        title=f"Moisture Infiltration Response under +{rain_input}mm Simulation",
        xaxis_title="Volumetric Moisture (%)",
        yaxis_title="Depth (cm)",
        yaxis=dict(autorange="reversed"),
        template="plotly_dark",
        height=350,
    )

    st.plotly_chart(fig_sim, use_container_width = True)