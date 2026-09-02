"""
THE MRIDANSH Dashboard : Dynamic Multi-Domain Soil Intelligence (Day 29)
Master Entry Point connecting Viewports, FastAPI Telemetry & Interactive GIS Map.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = Path(__file__).resolve().parent

for path in [str(ROOT_DIR), str(DASHBOARD_DIR)]:
    if path not in sys.path:
        sys.path.insert(0, path)

from renderers.map_renderers import render_heatmap_folium_map
from runtime_cache import get_api_client, get_unified_soil_engine_state
from viewports.agronomy_view import render_agronomy_viewport
from viewports.civil_view import render_civil_viewport

st.set_page_config(
    page_title="THE MRIDANSH | Multi-Domain Soil Intelligence Engine",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

css_file_path = DASHBOARD_DIR / "assets" / "style.css"
if css_file_path.exists():
    with open(css_file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown(
    """
    <style>
    .status-online { color: #00FF66; font-weight: bold; }
    .status-offline { color: #FF3333; font-weight: bold; }
    </style>
""",
    unsafe_allow_html=True,
)


def main():
    api_client = get_api_client()
    soil_state, agronomy_output, civil_output = get_unified_soil_engine_state()

    st.sidebar.image("https://img.icons8.com/isometric/100/earth-element.png", width=70)
    st.sidebar.title("AETHER-MRID1607X - THE MRIDANSH")
    st.sidebar.caption("Unified Soil Physics & Intelligence Center")
    st.sidebar.markdown("---")

    health_data = api_client.check_health()
    backend_online = health_data.get("status") == "HEALTHY"

    st.sidebar.subheader("📡 Backend Telemetry")
    if backend_online:
        st.sidebar.markdown(
            "Status: <span class='status-online'>● ONLINE (FastAPI)</span>",
            unsafe_allow_html=True,
        )
        st.sidebar.caption(
            f"Engine: {health_data.get('service', 'Async REST Backend')}"
        )
    else:
        st.sidebar.markdown(
            "Status: <span class='status-offline'>● OFFLINE (Fallback)</span>",
            unsafe_allow_html=True,
        )
        st.sidebar.caption("Start launcher `run.py` to connect REST API")

    st.sidebar.markdown("---")

    selected_viewport = st.sidebar.radio(
        "Select Intelligence Viewport:",
        ["🌱 Agronomy & Soil Health", "🏗️ Civil & Geotechnical Stability"],
        index=0,
    )

    st.sidebar.markdown("---")

    st.sidebar.subheader("📍Target Location")
    region = st.sidebar.selectbox(
        "Selected Grid Sector:",
        [
            "Grid-1607X (Bhubaneswar Corridor)",
            "Grid-0892Y (Deccan Plateau)",
            "Grid-0341Z (Indo-Gangetic Plain)",
        ],
    )

    st.sidebar.info(
        f"**Engine Status:** Active\n\n"
        f"**Data Stream:** EnKF Assimilated\n\n"
        f"**Grid ID:** {region.split(' ')[0]}"
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("THE MRIDANSH Architecture v1.0 | Day 29 Scaffolding")

    st.title("🌾 THE MRIDANSH Geospatial Intelligence Center")
    st.markdown(
        "Real-time integration of **Richards-1D Physics**, **Ensemble Kalman Filtering (EnKF)**, and **FastAPI Layer Service**."
    )

    with st.expander("⚡ Interactive REST API Trigger Panel", expanded=True):
        tab1, tab2 = st.tabs(
            ["🚀 Physics Simulation (`/predict`)", "🗺️ GIS Grid Mesh (`/gis/layer`)"]
        )

        with tab1:
            st.markdown("##### Execute Richards-1D + EnKF Simulation Engine")
            with st.form("simulation_form"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    lat_input = st.number_input(
                        "Target Latitude", value=20.2961, format="%.4f"
                    )
                with c2:
                    lon_input = st.number_input(
                        "Target Longitude", value=85.8245, format="%.4f"
                    )
                with c3:
                    day_input = st.slider(
                        "Simulation Days", min_value=1, max_value=30, value=7
                    )

                enkf_toggle = st.checkbox(
                    "Enable EnKF Satellite Assimilation", value=True
                )
                submit_btn = st.form_submit_button("Run Physics Simulation ⚡")

                if submit_btn:
                    with st.spinner("Invoking FastAPI `/api/v1/predict` Engine..."):
                        pred_res = api_client.trigger_prediction(
                            lat=lat_input,
                            lon=lon_input,
                            days=day_input,
                            enkf=enkf_toggle,
                        )

                    if pred_res and pred_res.get("status") == "SUCCESS":
                        st.success(
                            f"Simulation Executed In {pred_res.get('execution_time_sec')} sec!"
                        )
                        r_col1, r_col2 = st.columns(2)
                        with r_col1:
                            depths_data = pred_res.get("depths_cm") or [5, 15, 30, 60, 100]
                            moisture_data = pred_res.get("predicted_moisture_m3m3") or [0.0, 0.0, 0.0, 0.0, 0.0]
                            uncertainty_data = pred_res.get("uncertainty_bounds") or [0.0, 0.0, 0.0, 0.0, 0.0]

                            df_profile = pd.DataFrame(
                                {
                                    "Depth (cm)": depths_data,
                                    "Moisture (m³/m³)": moisture_data,
                                    "Uncertainty (±)": uncertainty_data,
                                }
                            )
                            st.dataframe(df_profile, use_container_width=True)

                        with r_col2:
                            st.line_chart(
                                data=df_profile.set_index("Depth (cm)")[
                                    "Moisture (m³/m³)"
                                ],
                                use_container_width=True,
                            )
                    else:
                        st.warning("FastAPI Server offline. Showing fallback profile.")

        # Tab 2: GIS Spatial Subgrid Mesh GET Endpoint (Day 30 Integration)
        with tab2:
            st.markdown("##### Dynamic Sub-Grid Mesh GeoJSON Integration")
            g1, g2 = st.columns([1, 2])

            # Initialize session state for persistent map rendering
            if "live_geojson_mesh" not in st.session_state:
                st.session_state.live_geojson_mesh = None

            with g1:
                grid_r = st.slider("Grid Row", 1, 8, 4, key="day30_row")
                grid_c = st.slider("Grid Col", 1, 8, 4, key="day30_col")
                fetch_gis_btn = st.button("Fetch & Overlay Sub-Grid Mesh 🗺️")

                if fetch_gis_btn:
                    with st.spinner("Requesting `/api/v1/gis/layer` GeoJSON..."):
                        gis_res = api_client.fetch_gis_layer(
                            layer_type="spatial_grid_mesh", rows=grid_r, cols=grid_c
                        )

                    if gis_res and gis_res.get("status") == "SUCCESS":
                        st.session_state.live_geojson_mesh = gis_res.get(
                            "geojson_data", {}
                        )
                        num_tiles = len(
                            st.session_state.live_geojson_mesh.get("features", [])
                        )
                        st.success(f"Rendered {num_tiles} Polygon Mesh Tiles!")

                    else:
                        st.error("Failed To Fetch GIS Layer From Backend.")

                if st.session_state.live_geojson_mesh:
                    with st.expander("🔍 Inspect Active GeoJSON Payload"):
                        st.json(st.session_state.live_geojson_mesh)

            with g2:
                # Day 31 Spatial Moisture Heatmap Viewport
                render_heatmap_folium_map(
                    lat = 20.2961,
                    lon = 85.8245,
                    zoom = 11,
                    geojson_data = st.session_state.live_geojson_mesh
                )

    st.markdown("---")

    if "Agronomy" in selected_viewport:
        render_agronomy_viewport(soil_state, agronomy_output)
    else:
        render_civil_viewport(soil_state, civil_output)


if __name__ == "__main__":
    main()
