"""
MRIDANSH : Agronomy Command Viewport (Hardened Step 8A - Task 03)
Agriculture domain layout with typed metric contracts, honest empty states, and scientific integrity.
"""

from typing import Any, Dict, Optional

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from metrics import DashboardMetric, build_agronomy_metrics
from renderers.chart_renderers import (
    plot_moisture_depth_profile,
    plot_npk_distribution,
)
from runtime_cache import DataState


def render_agronomy_viewport(soil_state: Any = None, agronomy_output: Any = None) -> None:
    """Renders the Agriculture & Soil Health Domain Viewport.

    Parameters:
        soil_state: UnifiedSoilState instance or container from core engine/cache
        agronomy_output: DomainOutput instance or dictionary from translator/cache
    """
    st.title("🌱 Agronomy Command & Soil Health Dashboard")
    st.caption(
        "AETHER-MRID1607X Engine | Physical Root-Zone Moisture & Soil Health Analytics"
    )

    # Standardize inputs into typed DashboardMetric instances
    metrics: Dict[str, DashboardMetric] = build_agronomy_metrics(soil_state, agronomy_output)

    m_moisture = metrics["root_zone_moisture"]
    m_ndvi = metrics["ndvi"]
    m_health = metrics["crop_health_score"]
    m_irrig = metrics["irrigation_required_l_ha"]
    m_drought = metrics["drought_risk_status"]
    m_nitrogen = metrics["nitrogen_level"]
    m_phosphorus = metrics["phosphorus_level"]
    m_potassium = metrics["potassium_level"]
    m_carbon = metrics["organic_carbon"]

    is_demo_mode = any(m.is_demo for m in metrics.values())

    # Mandatory Scientific Integrity Banner
    if is_demo_mode:
        st.warning(
            "⚠️ **DEMO DATA — NOT FOR FIELD USE:** Soil moisture and agronomic indicators "
            "below are uncalibrated demonstration placeholders. Field prescriptions require "
            "certified in-situ soil sampling."
        )
    else:
        st.info(
            "ℹ️ **SYSTEM STATUS: DISCONNECTED.** Live physical inference pipeline is "
            "disconnected. All agricultural metrics below reflect their actual available/unavailable states."
        )

    # 1. Top KPI Summary Cards (Explicit Semantics, Units, and States)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Root-Zone Moisture (m³/m³)",
            value=f"{m_moisture.value * 100:.1f}%" if m_moisture.is_available else "Unavailable",
        )
        st.caption(f"State: `{m_moisture.data_state.value}` | Unit: `m³/m³`")

    with col2:
        st.metric(
            label="Crop Health Index (0-1)",
            value=f"{m_health.value:.2f}" if m_health.is_available else "Unavailable",
        )
        st.caption(
            f"State: `{m_health.data_state.value}`"
            + (" (Missing NDVI)" if not m_ndvi.is_available else "")
        )

    with col3:
        st.metric(
            label="Theoretical Irrigation Deficit",
            value=f"{m_irrig.value:,.0f} L/ha" if m_irrig.is_available else "Unavailable",
        )
        st.caption(f"State: `{m_irrig.data_state.value}` | Unit: `L/ha`")

    with col4:
        st.metric(
            label="Soil Nutrients (NPK)",
            value="Unavailable",
        )
        st.caption("State: `UNAVAILABLE` | No Sensors")

    st.markdown("---")

    # 2. Moisture Stratification Profile (0 - 100 cm)
    st.subheader("💧 Subsurface Moisture Stratification (0 - 100 cm)")

    depths = np.array([5, 15, 30, 60, 100])
    raw_profile = getattr(getattr(soil_state, "hydro", None), "moisture_profile", None)

    fig_depth = plot_moisture_depth_profile(depths, raw_profile, is_demo=is_demo_mode)

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.plotly_chart(fig_depth, use_container_width=True)

    with col_right:
        st.markdown("### 🌾 Crop Suitability Insights")
        if m_moisture.is_available and raw_profile is not None and len(raw_profile) >= 5:
            d_val = m_drought.value if m_drought.is_available else "Uncalibrated Demo"
            st.info(
                f"**Field Status:** `{d_val}`\n\n"
                f"• **Topsoil (0-15cm):** {raw_profile[0] * 100:.1f}% (Demonstration value)\n"
                f"• **Rooting Zone (15-60cm):** {raw_profile[2] * 100:.1f}% (Demonstration value)\n"
                f"• **Subsoil (60-100cm):** {raw_profile[4] * 100:.1f}% (Demonstration value)\n\n"
                f"*Note: Volumetric water fractions theta are demonstration values for UI layout.*"
            )
        else:
            st.warning(
                "⚠️ **Depth Moisture Insights Unavailable:**\n\n"
                "No multi-layer Richards-1D numerical simulation or calibrated probe data is connected."
            )

    st.markdown("---")

    # 3. Biogeochemical Soil Nutrients (NPK) & Organic Carbon
    st.subheader("🧪 Soil Biogeochemical Health")
    if is_demo_mode:
        st.caption(
            "⚠️ **DEMO DATA — NOT FOR AGRONOMIC USE:** Biochemical nutrient concentrations "
            "are synthetic demonstration placeholders. No chemical spectrometry sensors are connected."
        )
    else:
        st.caption(
            "ℹ️ Chemical spectrometry and laboratory soil testing are disconnected. "
            "The AETHER core models soil hydrology, not biochemical nutrients."
        )

    n_val = getattr(getattr(soil_state, "biogeo", None), "nitrogen_est", None)
    p_val = getattr(getattr(soil_state, "biogeo", None), "phosphorus_est", None)
    k_val = getattr(getattr(soil_state, "biogeo", None), "potassium_est", None)

    fig_npk = plot_npk_distribution(n_val, p_val, k_val, is_demo=is_demo_mode)

    col_npk1, col_npk2 = st.columns([2, 1])

    with col_npk1:
        st.plotly_chart(fig_npk, use_container_width=True)

    with col_npk2:
        st.markdown("### 📋 Agronomic Advisory Status")
        st.info(
            "⚠️ **Nutrient recommendation unavailable — validated soil-chemistry inputs "
            "and a supported recommendation method are not connected.**\n\n"
            "• **Fertilizer Guidance:** Chemical nutrient sensing (N, P, K) and organic carbon "
            "testing are disconnected. No commercial application rates are generated.\n\n"
            "• **Irrigation Guidance:** Irrigation volume shown above is a theoretical volumetric "
            "deficit (L/ha) to target capacity (0.35 m³/m³). Certified crop irrigation prescriptions "
            "require local crop coefficients (Kc) and real-time evapotranspiration (ET₀)."
        )

    st.markdown("---")

    # 4. Interactive What-If Scenario Simulator
    st.subheader("⚡ What-If Scenario Simulator: Rainfall / Water Input")
    st.caption("ℹ️ Simplified educational heuristic — not calibrated with Richards-1D numerical PDE solution.")

    if raw_profile is not None and len(raw_profile) >= 5 and not np.all(np.isnan(raw_profile)):
        rain_input = st.slider(
            "Simulate Additional Water Input (mm)",
            min_value=0,
            max_value=100,
            value=20,
            step=5,
        )

        simulated_moisture = np.clip(
            raw_profile + (rain_input * 0.0025) / (depths / 10), 0.05, 0.48
        )

        fig_sim = go.Figure()
        fig_sim.add_trace(
            go.Scatter(
                x=raw_profile * 100,
                y=depths,
                mode="lines",
                name="Baseline State (Demo)",
                line=dict(color="#7f7f7f", dash="dash"),
            )
        )

        fig_sim.add_trace(
            go.Scatter(
                x=simulated_moisture * 100,
                y=depths,
                mode="lines+markers",
                name=f"Simulated (+{rain_input}mm Demo)",
                line=dict(color="#00cc96", width=3),
            )
        )

        fig_sim.update_layout(
            title=f"Moisture Response under +{rain_input}mm Simulation (DEMO HEURISTIC)",
            xaxis_title="Volumetric Moisture (%)",
            yaxis_title="Depth (cm)",
            yaxis=dict(autorange="reversed"),
            template="plotly_dark",
            height=350,
        )

        st.plotly_chart(fig_sim, use_container_width=True)
    else:
        st.warning("⚠️ **Scenario Simulation Unavailable:** Baseline soil moisture depth profile is disconnected.")

