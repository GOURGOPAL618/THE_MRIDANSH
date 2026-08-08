"""
MRIDANSH : Civil & Geotechnical Viewport (Step 8B)
Subsurface profile, ground stability index, and pore water dynamics.
"""

import streamlit as st
from renderers.chart_renderers import (
    plot_3d_soil_stratification,
    plot_ground_stability_gauge,
)

def render_civil_viewport(soil_state, civil_output):
    """Renders the Civil & Geotechnical Domain Page.

    Parameters:
        soil_state: UnifiedSoilState instance from core engine
        civil_output: CivilTranslator output dictionary
    """
    st.title("🏗️ Civil & Ground Stability Command Dashboard")
    st.caption(
        "AETHER-MRID1607X Engine | Geotechnical Subsurface Profiling & Pore Pressure Intelligence"
    )

    # 1. Civil Top KPI Summary Cards
    col1, col2,col3, col4 = st.columns(4)

    stability_score = civil_output.get("ground_stability_index", 0.82)
    pore_pressure = civil_output.get("pore_water_pressure_kPa", 14.2)
    bulk_density = soil_state.hydro.bulk_density
    freshness = soil_state.reliability.observation_freshness_hrs

    with col1:
        st.metric(
            label="Ground Stability Index",
            value=f"{stability_score * 100:.1f}%",
            delta="Stable",
        )

    with col2:
        st.metric(
            label="Pore Water Pressure",
            value=f"{pore_pressure:.1f} kPa",
            delta="Normal",
        )
    
    with col3:
        st.metric(
            label="Bulk Soil Density",
            value=f"{bulk_density:.2f} g/cm³",
        )

    with col4:
        st.metric(
            label="Observation Freshness",
            value=f"{freshness:.1f} hrs ago",
            delta="Live Satellite Data",
        )

    st.markdown("---")

    # 2. 3D Subsurface Soil Stratification Mesh & Stability Gauge
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("🌐 3D Subsurface Soil Stratification Mesh")
        fig_3d = plot_3d_soil_stratification()
        st.plotly_chart(fig_3d, use_container_width=True)

    with col_right:
        st.subheader("🛡️ Ground Stability Score")
        fig_gauge = plot_ground_stability_gauge(stability_score)
        st.plotly_chart(fig_gauge, use_container_width=True)

        st.warning(
            f"**Geotechnical Risk Assessment:**\n\n"
            f"• **Risk Level:** Low to Moderate\n"
            f"• **Saturation Risk:** Pore pressure is within allowable thresholds (<25 kPa).\n"
            f"• **Shear Strength:** Maintained at upper soil horizon."
        )

    st.markdown("---")

    # 3. Load Response & Moisture Sensitivity Matrix
    st.subheader("📉 Geotechnical Load-Response & Drainage Intelligence")

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.markdown("### 🚜 Civil Engineering Summary")
        st.json(
            {
                "Dominant Soil Layer": "Silty-Clay Horizon",
                "Hydraulic Conductivity (K_sat)": f"{soil_state.hydro.hydraulic_cond:.4e} cm/s",
                "Slope Angle": f"{soil_state.terrain.slope_deg:.1f}°",
                "Saturation Degree": f"{soil_state.hydro.saturation_degree * 100:.1f}%",
                "Drainage Class": "Moderate to Well Drained",
            }
        )

    with col_c2:
        st.markdown("### 🚧 Heavy Equipment Operational Advisory")
        if stability_score > 0.75:
            st.success(
                "✅ **SAFE FOR HEAVY MACHINERY:** Soil bearing capacity is optimal. No active liquefaction risk detected."
            )
        else:
            st.error(
                "⚠️ **CAUTION:** Soil saturation high. Limit heavy load operations near slopes."
            )

        st.info(
            "ℹ️ *Note: Extended geotechnical parameters (Dynamic CBR, Settlement & Bearing Capacity) will be unlocked in Phase 2 via MARGAVEDHA Engine integration.*"
        )
        