"""
MRIDANSH : Civil & Geotechnical Viewport (Hardened Task 04)
Subsurface profile, ground stability scaffolding, and geotechnical metrics
rendered with strict engineering limitations, typed contracts, and honest data states.
"""

from typing import Any, Dict, Optional

import streamlit as st
from metrics import DashboardMetric, DataState, build_civil_metrics
from renderers.chart_renderers import (
    plot_3d_soil_stratification,
    plot_ground_stability_gauge,
)


def render_civil_viewport(soil_state: Any = None, civil_output: Any = None) -> None:
    """Renders the Civil & Geotechnical Domain Viewport.

    Parameters:
        soil_state: UnifiedSoilState instance, ObjectContainer, or None
        civil_output: CivilTranslator DomainOutput, dictionary, or None
    """
    st.title("🏗️ Civil & Ground Stability Command Dashboard")
    st.caption(
        "AETHER-MRID1607X Engine | Geotechnical Subsurface Scaffolding (Inference Disconnected)"
    )

    # Mandatory Civil Safety Banner (Preserved from Task 02)
    st.warning(
        "⚠️ **DEMO DATA — NOT FOR ENGINEERING USE:** Geotechnical indicators below are "
        "uncalibrated demonstration parameters. Real-world civil and structural engineering "
        "decisions require certified geotechnical borehole logs and laboratory soil testing."
    )

    # Normalize metrics through the shared typed contract
    civil_metrics: Dict[str, DashboardMetric] = build_civil_metrics(
        soil_state=soil_state,
        civil_output=civil_output,
    )

    m_stability = civil_metrics["ground_stability_index"]
    m_pressure = civil_metrics["pore_water_pressure_kPa"]
    m_density = civil_metrics["dry_bulk_density"]
    m_freshness = civil_metrics["observation_freshness_hrs"]
    m_bearing = civil_metrics["bearing_capacity_kPa"]
    m_cohesion = civil_metrics["effective_cohesion_kPa"]

    # 1. Civil Top KPI Summary Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        val_str = (
            f"{m_stability.value * 100:.1f}% (DEMO)"
            if m_stability.is_available and m_stability.is_demo
            else m_stability.display_value
        )
        delta_lbl = (
            "DEMO DATA"
            if m_stability.is_demo
            else ("LIVE ESTIMATE" if m_stability.is_available else "UNAVAILABLE")
        )
        st.metric(
            label=m_stability.label,
            value=val_str,
            delta=delta_lbl,
            help=m_stability.note,
        )

    with col2:
        val_str = (
            f"{m_pressure.value:.1f} kPa (DEMO)"
            if m_pressure.is_available and m_pressure.is_demo
            else m_pressure.display_value
        )
        delta_lbl = (
            "DEMO DATA"
            if m_pressure.is_demo
            else ("LIVE ESTIMATE" if m_pressure.is_available else "NO PIEZOMETER")
        )
        st.metric(
            label=m_pressure.label,
            value=val_str,
            delta=delta_lbl,
            help=m_pressure.note,
        )

    with col3:
        val_str = (
            f"{m_density.value:.2f} g/cm³ (DEMO)"
            if m_density.is_available and m_density.is_demo
            else m_density.display_value
        )
        delta_lbl = (
            "Assumed Baseline"
            if m_density.is_demo
            else ("LIVE ESTIMATE" if m_density.is_available else "UNAVAILABLE")
        )
        st.metric(
            label=m_density.label,
            value=val_str,
            delta=delta_lbl,
            help=m_density.note,
        )

    with col4:
        val_str = (
            f"{m_freshness.value:.1f} hrs ago"
            if m_freshness.is_available
            else "Disconnected"
        )
        delta_lbl = "No Live Feed" if not m_freshness.is_available else "Live Satellite"
        st.metric(
            label=m_freshness.label,
            value=val_str,
            delta=delta_lbl,
            help=m_freshness.note,
        )

    st.markdown("---")

    # 2. 3D Subsurface Soil Stratification Mesh & Stability Gauge
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("🌐 3D Subsurface Soil Stratification Mesh (Scaffolding)")
        fig_3d = plot_3d_soil_stratification()
        st.plotly_chart(fig_3d, use_container_width=True)

    with col_right:
        st.subheader("🛡️ Ground Stability Score")
        fig_gauge = plot_ground_stability_gauge(
            m_stability.value if m_stability.is_available else None,
            is_demo=m_stability.is_demo,
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        st.info(
            "ℹ️ **Geotechnical Assessment Notice (DEMO DATA — NOT FOR ENGINEERING USE):**\n\n"
            "• Ground stability index is an uncalibrated synthetic demonstration parameter.\n"
            "• In-situ shear strength and pore pressure sensors are not connected.\n"
            "• Foundation and slope stability cannot be inferred from this display."
        )

    st.markdown("---")

    # 3. Load Response & Operational Safety Status
    st.subheader("📉 Geotechnical Load-Response & Operational Assessment")

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.markdown("### 🚜 Civil Parameter Summary (Demonstration)")
        hydro_obj = getattr(soil_state, "hydro", None) if soil_state else None
        terrain_obj = getattr(soil_state, "terrain", None) if soil_state else None

        hydraulic_cond = getattr(hydro_obj, "hydraulic_cond", None)
        slope_deg = getattr(terrain_obj, "slope_deg", None)
        saturation_deg = getattr(hydro_obj, "saturation_degree", None)
        is_demo_mode = getattr(soil_state, "is_demo", False) if soil_state else False

        k_sat_str = f"{hydraulic_cond:.4e} cm/s (Assumed)" if hydraulic_cond is not None else "Unavailable"
        slope_str = f"{slope_deg:.1f}° (DEM Reference)" if slope_deg is not None else "Unavailable"
        sat_str = f"{saturation_deg * 100:.1f}% (Demo Scaffolding)" if saturation_deg is not None else "Unavailable"
        data_state_str = "DEMO / UNCALIBRATED" if is_demo_mode else "DISCONNECTED"

        st.json(
            {
                "Dominant Soil Layer": "Demonstration Horizon (Unverified)" if is_demo_mode else "Unavailable",
                "Hydraulic Conductivity (K_sat)": k_sat_str,
                "Slope Angle": slope_str,
                "Saturation Degree": sat_str,
                "Data State": data_state_str,
            }
        )

        # Bearing Capacity Section if available in Translator / Demo
        if m_bearing.is_available:
            st.info(
                f"**Nominal Bearing Capacity:** `{m_bearing.display_value}`\n\n"
                f"• **Effective Cohesion:** `{m_cohesion.display_value}`\n"
                f"• *Caveat: {m_bearing.note}*"
            )

    with col_c2:
        st.markdown("### 🚧 Heavy Equipment Operational Advisory")
        st.warning(
            "⚠️ **Geotechnical assessment unavailable — Geotechnical safety assessment unavailable: "
            "No validated site-specific engineering assessment is connected.**\n\n"
            "• **Bearing Capacity & Factor of Safety:** Bearing capacity and Factor of Safety "
            "have not been established by this dashboard. Do not use these outputs for construction, "
            "foundation design, or heavy-equipment safety decisions.\n\n"
            "• **Factor of Safety ($FS$):** Has **not** been calculated. Standard geotechnical "
            "practice requires $FS \\ge 3.0$ for permanent foundation design based on certified site investigations.\n\n"
            "• **California Bearing Ratio (CBR):** CBR and road subgrade compaction metrics are unavailable. "
            "No laboratory penetration testing (ASTM D1883 / AASHTO T193) or roadbed structural analysis is connected.\n\n"
            "• **Foundation Suitability:** Foundation suitability cannot be inferred from surface or uncalibrated "
            "satellite data. Certified structural engineering approval requires rotary boreholes, SPT/CPT sounding logs, "
            "and laboratory triaxial testing."
        )

        st.info(
            "ℹ️ *Note: Formal geotechnical calculation models will be wired under explicit "
            "engineering domain translator integration in future authorized phases.*"
        )
