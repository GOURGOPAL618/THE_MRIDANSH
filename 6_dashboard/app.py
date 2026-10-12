"""
THE MRIDANSH : Earth-Observation & Multi-Domain Soil Intelligence Workstation (Task 05)
AETHER-MRID1607X Core Engine — JCC Command Center
Tagline: FROM ORBIT TO ROOT
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

from metrics import DataState, build_spatial_layer_metadata
from renderers.map_renderers import render_heatmap_folium_map
from runtime_cache import get_api_client, get_unified_soil_engine_state
from viewports.agronomy_view import render_agronomy_viewport
from viewports.civil_view import render_civil_viewport

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="THE MRIDANSH | Earth-Observation Soil Intelligence Workstation",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load Technical Obsidian & Cyan Stylesheet
css_file_path = DASHBOARD_DIR / "assets" / "style.css"
if css_file_path.exists():
    with open(css_file_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Preset AOI Definitions
AOI_PRESETS = {
    "Grid-1607X (Bhubaneswar Coastal Basin, Odisha)": {
        "lat": 20.2961,
        "lon": 85.8245,
        "bbox": [85.75, 20.20, 85.90, 20.35],
        "sector_id": "MRID-SECTOR-1607X",
        "soil_class": "Lateritic / Alluvial Lowland",
    },
    "Grid-0892Y (Deccan Semi-Arid Plateau, Telangana)": {
        "lat": 17.3850,
        "lon": 78.4867,
        "bbox": [78.40, 17.30, 78.55, 17.45],
        "sector_id": "MRID-SECTOR-0892Y",
        "soil_class": "Black Cotton Soil / Vertisol",
    },
    "Grid-0341Z (Indo-Gangetic Alluvial Plain, UP)": {
        "lat": 26.8467,
        "lon": 80.9462,
        "bbox": [80.85, 26.75, 81.00, 26.90],
        "sector_id": "MRID-SECTOR-0341Z",
        "soil_class": "Gangetic Alluvium / Inceptisol",
    },
}


def main():
    api_client = get_api_client()
    soil_state, agronomy_output, civil_output = get_unified_soil_engine_state()

    # Session State Initialization
    if "selected_lat" not in st.session_state:
        st.session_state.selected_lat = 20.2961
    if "selected_lon" not in st.session_state:
        st.session_state.selected_lon = 85.8245
    if "active_bbox" not in st.session_state:
        st.session_state.active_bbox = [85.75, 20.20, 85.90, 20.35]
    if "live_geojson_mesh" not in st.session_state:
        st.session_state.live_geojson_mesh = None

    # -----------------------------------------------------------------------
    # Sidebar: Workspace Navigation & Spatial Controls
    # -----------------------------------------------------------------------
    with st.sidebar:
        st.markdown(
            """
            <div style="padding-bottom: 8px;">
                <span style="font-size: 1.25rem; font-weight: 800; letter-spacing: 1px; color: #00f0ff;">
                    THE MRIDANSH
                </span><br>
                <span style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1.5px; color: #94a3b8;">
                    FROM ORBIT TO ROOT
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("AETHER-MRID1607X Core Engine | Satellite Subsurface Intelligence")
        st.markdown("---")

        # 1. Primary Workspace Switcher
        st.subheader("🧭 Intelligence Workspace")
        selected_viewport = st.radio(
            "Select Operational Domain:",
            ["🌱 Agronomy & Soil Health", "🏗️ Civil & Geotechnical Stability"],
            index=0,
            label_visibility="collapsed",
        )
        st.markdown("---")

        # 2. Target Area of Interest (AOI) Selector
        st.subheader("📍 Target Area of Interest (AOI)")
        selected_aoi_name = st.selectbox(
            "Target Geographic Sector:",
            list(AOI_PRESETS.keys()) + ["Custom Coordinate Entry"],
            index=0,
        )

        if selected_aoi_name in AOI_PRESETS:
            preset = AOI_PRESETS[selected_aoi_name]
            st.session_state.active_bbox = preset["bbox"]
            sector_code = preset["sector_id"]
            soil_type = preset["soil_class"]
        else:
            sector_code = "CUSTOM-EXTENT"
            soil_type = "Unspecified Geographic Target"
            c_lat, c_lon = st.columns(2)
            with c_lat:
                custom_lat = st.number_input("Target Lat", value=float(st.session_state.selected_lat), format="%.4f")
            with c_lon:
                custom_lon = st.number_input("Target Lon", value=float(st.session_state.selected_lon), format="%.4f")
            st.session_state.selected_lat = custom_lat
            st.session_state.selected_lon = custom_lon
            st.session_state.active_bbox = [
                round(custom_lon - 0.08, 4),
                round(custom_lat - 0.08, 4),
                round(custom_lon + 0.08, 4),
                round(custom_lat + 0.08, 4),
            ]

        # Reset Target Coordinates Button
        if selected_aoi_name in AOI_PRESETS:
            preset = AOI_PRESETS[selected_aoi_name]
            if st.button("Center Map to Sector Target 🎯", use_container_width=True):
                st.session_state.selected_lat = preset["lat"]
                st.session_state.selected_lon = preset["lon"]
                st.session_state.active_bbox = preset["bbox"]
                st.rerun()

        st.markdown("---")

        # 3. GIS Layer & Mesh Generation Controls
        st.subheader("🗺️ Spatial Mesh Grid Controls")
        show_mesh_toggle = st.checkbox("Overlay Computational Sub-Grid Mesh", value=True)
        show_bbox_toggle = st.checkbox("Overlay AOI Boundary Box", value=True)

        grid_r = st.slider("Mesh Divisions (Rows)", 1, 8, 4)
        grid_c = st.slider("Mesh Divisions (Cols)", 1, 8, 4)

        if st.button("Fetch & Regenerate Sub-Grid Mesh ⚡", use_container_width=True):
            with st.spinner("Generating spatial grid mesh via API..."):
                gis_res = api_client.fetch_gis_layer(
                    layer_type="spatial_grid_mesh",
                    bbox=st.session_state.active_bbox,
                    rows=grid_r,
                    cols=grid_c,
                )
                if gis_res and gis_res.get("status") == "SUCCESS":
                    st.session_state.live_geojson_mesh = gis_res.get("geojson_data", {})
                    num_tiles = len(st.session_state.live_geojson_mesh.get("features", []))
                    st.success(f"Generated {num_tiles} Sub-Grid Polygon Tiles.")
                else:
                    st.error("Failed to generate GIS spatial layer.")

        st.markdown("---")

        # 4. Telemetry Status Card
        st.subheader("📡 Backend Service Telemetry")
        health_data = api_client.check_health()
        backend_online = health_data.get("status") == "HEALTHY"

        if backend_online:
            st.markdown("API Status: <span class='status-online'>● ONLINE (FastAPI)</span>", unsafe_allow_html=True)
            st.caption(f"Service: `{health_data.get('service', 'FastAPI')}` (Inference Disconnected)")
        else:
            st.markdown("API Status: <span class='status-offline'>● OFFLINE (Disconnected)</span>", unsafe_allow_html=True)
            st.caption("FastAPI telemetry backend is unreachable.")

        st.caption(
            "Engine: `AETHER-MRID1607X` | CRS: `EPSG:4326`\n\n"
            "Status: `DEMO SCAFFOLDING` | Standalone UI (Disconnected) | Live Pipeline: `DISCONNECTED`"
        )

    # -----------------------------------------------------------------------
    # Main Application Canvas: Command Header & Status Ribbon
    # -----------------------------------------------------------------------
    active_mode = "agronomy" if "Agronomy" in selected_viewport else "civil"

    # Command Header Block
    st.markdown(
        f"""
        <div class="mrid-header-ribbon">
            <div class="mrid-title-block">
                <h1>🌍 THE MRIDANSH Geospatial Intelligence Center</h1>
                <p>AETHER-MRID1607X Core Engine | Satellite Subsurface Hydrology & Geotechnical Profiling</p>
            </div>
            <div style="display: flex; gap: 8px; align-items: center;">
                <span class="status-pill pill-demo">DEMO SCAFFOLDING</span>
                <span class="status-pill pill-unavail">LIVE INFERENCE DISCONNECTED</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Secondary Status Ribbon
    ribbon_c1, ribbon_c2, ribbon_c3, ribbon_c4 = st.columns(4)
    with ribbon_c1:
        st.markdown(f"**Sector:** `{sector_code}`")
    with ribbon_c2:
        st.markdown(f"**Target Coordinate:** `{st.session_state.selected_lat:.4f}°N, {st.session_state.selected_lon:.4f}°E`")
    with ribbon_c3:
        st.markdown(f"**Geodetic Datum:** `WGS 84 (EPSG:4326)`")
    with ribbon_c4:
        st.markdown(f"**Domain Mode:** `{'AGRONOMY' if active_mode == 'agronomy' else 'CIVIL ENGINEERING'}`")

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Section 1: Geospatial Intelligence & Interactive Canvas
    # -----------------------------------------------------------------------
    st.subheader("🗺️ Geospatial Spatial Mesh & Target Inspection Canvas")

    map_col, inspect_col = st.columns([7, 3])

    with map_col:
        # Prepare mesh layer if toggle enabled
        active_geojson = st.session_state.live_geojson_mesh if show_mesh_toggle else None
        active_bbox_for_map = st.session_state.active_bbox if show_bbox_toggle else None

        # Render Folium Map
        map_output = render_heatmap_folium_map(
            lat=st.session_state.selected_lat,
            lon=st.session_state.selected_lon,
            zoom=11,
            geojson_data=active_geojson,
            domain_mode=active_mode,
            is_demo=True,
            aoi_bbox=active_bbox_for_map,
        )

        # Handle Click on Map Event
        if map_output and map_output.get("last_clicked"):
            clicked = map_output["last_clicked"]
            new_lat = round(clicked["lat"], 4)
            new_lon = round(clicked["lng"], 4)
            if new_lat != st.session_state.selected_lat or new_lon != st.session_state.selected_lon:
                st.session_state.selected_lat = new_lat
                st.session_state.selected_lon = new_lon
                st.rerun()

    with inspect_col:
        st.markdown("### 🎯 Target Cell Inspector")
        st.markdown(
            f"**Inspection Latitude:** `{st.session_state.selected_lat:.4f}°N`\n\n"
            f"**Inspection Longitude:** `{st.session_state.selected_lon:.4f}°E`\n\n"
            f"**Sector Classification:** {soil_type}\n\n"
            f"**Bounding Box Extent:**\n"
            f"`[{st.session_state.active_bbox[0]}, {st.session_state.active_bbox[1]}, "
            f"{st.session_state.active_bbox[2]}, {st.session_state.active_bbox[3]}]`"
        )

        if st.session_state.live_geojson_mesh:
            features = st.session_state.live_geojson_mesh.get("features", [])
            spatial_meta = build_spatial_layer_metadata(st.session_state.live_geojson_mesh)
            st.info(
                f"**Active Spatial Mesh:** `{len(features)} sub-grid polygons`\n\n"
                f"• **CRS:** `{spatial_meta.crs}`\n"
                f"• **Data State:** `{spatial_meta.data_state.value}`\n"
                f"• **Coverage Status:** `Geometry Only (No Sensors Attached)`\n\n"
                f"*{spatial_meta.note}*"
            )
        else:
            st.caption("ℹ️ Computational grid mesh not yet loaded. Click 'Fetch & Regenerate Sub-Grid Mesh' in sidebar.")

        st.caption("💡 *Click anywhere on the map to interactively update target coordinates.*")

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Section 2: Active Domain Viewport (Hardened Tasks 03 & 04)
    # -----------------------------------------------------------------------
    if "Agronomy" in selected_viewport:
        render_agronomy_viewport(soil_state, agronomy_output)
    else:
        render_civil_viewport(soil_state, civil_output)

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Section 3: Interactive REST Simulation Drawer (Optional Diagnostic Tool)
    # -----------------------------------------------------------------------
    with st.expander("⚡ Physics Simulation REST API Trigger (`/api/v1/predict`)", expanded=False):
        st.caption("Direct REST trigger for the AETHER Richards-1D + EnKF physics endpoint.")
        with st.form("simulation_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                lat_input = st.number_input("Target Latitude", value=float(st.session_state.selected_lat), format="%.4f")
            with c2:
                lon_input = st.number_input("Target Longitude", value=float(st.session_state.selected_lon), format="%.4f")
            with c3:
                day_input = st.slider("Simulation Horizon (Days)", min_value=1, max_value=30, value=7)

            enkf_toggle = st.checkbox("Enable EnKF Satellite Assimilation", value=False)
            demo_toggle = st.checkbox("Enable Synthetic Demo Profile (UI Scaffolding Only)", value=True)
            submit_btn = st.form_submit_button("Execute Physical Inference ⚡")

            if submit_btn:
                with st.spinner("Invoking FastAPI `/api/v1/predict`..."):
                    pred_res = api_client.trigger_prediction(
                        lat=lat_input,
                        lon=lon_input,
                        days=day_input,
                        enkf=enkf_toggle,
                        allow_demo=demo_toggle,
                    )

                if pred_res and pred_res.get("status") == "DEMO":
                    st.warning("⚠️ **DEMO PROFILE GENERATED — NOT FOR SCIENTIFIC OR FIELD USE**")
                    depths_data = pred_res.get("depths_cm") or [5, 15, 30, 60, 100]
                    moisture_data = pred_res.get("predicted_moisture_m3m3") or [0.0] * 5
                    uncertainty_data = pred_res.get("uncertainty_bounds") or [0.0] * 5

                    df_profile = pd.DataFrame(
                        {
                            "Depth (cm)": depths_data,
                            "Moisture (m³/m³) [DEMO]": moisture_data,
                            "Uncertainty (±) [DEMO]": uncertainty_data,
                        }
                    )
                    st.dataframe(df_profile, use_container_width=True)
                elif pred_res and (pred_res.get("status") == "UNAVAILABLE" or "detail" in pred_res):
                    detail_msg = pred_res.get("detail", {})
                    msg_text = detail_msg.get("message", "Inference engine is disconnected.") if isinstance(detail_msg, dict) else str(detail_msg)
                    st.info(f"ℹ️ **Simulation Engine Disconnected:** {msg_text}")
                else:
                    st.error("FastAPI Server offline or unreachable.")

    # -----------------------------------------------------------------------
    # Section 4: System Provenance & Scientific Integrity Footer
    # -----------------------------------------------------------------------
    st.markdown(
        """
        <div style="background: #121722; border: 1px solid #1e293b; border-radius: 6px; padding: 14px 20px; margin-top: 2rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.8rem; font-weight: 600; color: #94a3b8;">
                    THE MRIDANSH SCIENTIFIC INTEGRITY & PROVENANCE SPECIFICATION
                </span>
                <span class="status-pill pill-demo">TASK 05 GEOSPATIAL LOCK</span>
            </div>
            <div style="font-size: 0.78rem; color: #64748b; margin-top: 6px; line-height: 1.5;">
                • <b>Geodetic Datum:</b> WGS 84 (EPSG:4326) | <b>Nominal Spatial Resolution:</b> 10m (Sentinel-2 MSI) / 20m (Sentinel-1 SAR)<br>
                • <b>Hydrological Model:</b> Richards-1D Non-Linear PDE Finite Difference Solver | <b>Data Assimilation:</b> Ensemble Kalman Filter (EnKF)<br>
                • <b>Engineering Limitation:</b> Dashboard inference engine is disconnected pending pipeline router integration. All displayed profiles and grid meshes are explicit demonstration scaffolding.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
