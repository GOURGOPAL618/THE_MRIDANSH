"""
MRIDANSH Dashboard : Interactive Streamlit Command Center
Master Entry Point (Day 12 - Phase 1 Final)
"""

import sys
from pathlib import Path
import streamlit as st

# Setup Path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# Import Viewports & Runtime Cache
from runtime_cache import get_unified_soil_engine_state
from viewports.agronomy_view import render_agronomy_viewport
from viewports.civil_view import render_civil_viewport

# 1. Streamlit Page Configuration
st.set_page_config(
    page_title="MRIDANSH | Multi-Domain Soil Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Custom CSS Styling
css_file_path = Path(__file__).parent / "assets" / "style.css"
if css_file_path.exists():
    with open(css_file_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 3. Load Engine State & Translated Outputs
soil_state, agronomy_output, civil_output = get_unified_soil_engine_state()

# 4. Sidebar Controls & Navigation
st.sidebar.image(
    "https://img.icons8.com/isometric/100/earth-element.png", 
    width=70
)
st.sidebar.title("AETHER - MRIDANSH")
st.sidebar.caption("Unified Soil Physics & Intelligence Center")

st.sidebar.markdown("---")

# Navigation Selector
selected_viewport = st.sidebar.radio(
    "Select Intelligence Viewport:",
    ["🌱 Agronomy & Soil Health", "🏗️ Civil & Geotechnical Stability"],
    index=0
)

st.sidebar.markdown("---")

# Location & Region Filter Simulation
st.sidebar.subheader("📍 Target Region")
region = st.sidebar.selectbox(
    "Selected Grid Sector:",
    ["Grid-1607X (Bhubaneswar Corridor)", "Grid-0892Y (Deccan Plateau)", "Grid-0341Z (Indo-Gangetic Plain)"]
)

st.sidebar.info(
    f"**Engine Status:** Active\n\n"
    f"**Data Stream:** EnKF Assimilated\n\n"
    f"**Grid ID:** {region.split(' ')[0]}"
)

st.sidebar.markdown("---")
st.sidebar.caption("AETHER Framework v1.0 | Phase 1 Complete")

# 5. Main Viewport Routing
if "Agronomy" in selected_viewport:
    render_agronomy_viewport(soil_state, agronomy_output)
else:
    render_civil_viewport(soil_state, civil_output)