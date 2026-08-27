"""
THE MRIDANSH : Runtime Cache, State Manager & REST API Integration Client (Day 26)
Handles session state, unified soil state caching, and FastAPI backend integration.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import requests
import streamlit as st

# Ensure repository root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))


# ---------------------------------------------------------------------------
# 1. Existing Soil State Container & Cache Engine
# ---------------------------------------------------------------------------
class ObjectContainer:
    """Dummy Container For Structured State Objects."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

@st.cache_resource
def get_unified_soil_engine_state():
    """Instantiates and caches the Unified Soil State and Domain Translators."""
    
    # Hydro State
    hydro = ObjectContainer(
        moisture_profile = np.array([0.22, 0.28, 0.31, 0.33, 0.35]),
        saturation_degree = 0.68,
        hydraulic_cond = 0.0012,
        bulk_density = 1.38,
    )

    # Bio Chemical State
    biogeo = ObjectContainer(
        nitrogen_est = 115.4,
        phosphorus_est = 28.2,
        potassium_est = 142.8,
        organic_carbon = 0.78,
        ph_level = 6.8,
    )

    # Terrain State
    terrain = ObjectContainer(
        elevation_m = 245.0,
        slope_deg = 4.2,
        aspect_deg = 180.0,
    )

    # Reliability / Assimilation State
    reliability = ObjectContainer(
        confidence_score = 0.92,
        observation_freshness_hrs = 1.5,
        ensemble_spread = 0.04,
    )

    # Unified Soil State Container
    soil_state = ObjectContainer(
        hydro = hydro,
        biogeo = biogeo,
        terrain = terrain,
        reliability = reliability,
    )

    # Translated Output Mock Rules
    agronomy_output = {
        "root_zone_moisture": 0.295,
        "organic_carbon_est": 0.78,
        "npk_status": "Optimal",
        "moisture_zone": "Field Capacity",
    }

    civil_output = {
        "ground_stability_index": 0.84,
        "pore_water_pressure_kPa": 13.8,
        "bearing_capacity_est_kPa": 185.0,
    }

    return soil_state, agronomy_output, civil_output


# ---------------------------------------------------------------------------
# 2. FastAPI REST Client Wrapper (Day 26 Integration)
# ---------------------------------------------------------------------------

class FastAPIClient:
    """REST API Client Wrapper for Streamlit UI integration."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    def check_health(self) -> Dict[str, Any]:
        """Fetch backend health and telemetry."""
        try:
            res = requests.get(f"{self.base_url}/health", timeout = 3)
            if res.status_code == 200:
                return res.json()

        except Exception:
            pass
        return {"status": "OFFLINE", "service": "Backend Disconnected"}

    def fetch_gis_layer(
        self,
        layer_type: str = "Spatial_grid_mesh",
        bbox: Optional[list] = None,
        rows: int = 4,
        cols: int = 4,
    ) -> Dict[str, Any]:
        """Request vector/grid layers from /api/v1/gis/layer."""
        if bbox is None:
            bbox = [85.75, 20.20, 85.90, 20.35]

        params = {
            "layer_type": layer_type,
            "min_lon": bbox[0],
            "min_lat": bbox[1],
            "max_lon": bbox[2],
            "max_lat": bbox[3],
            "grid_rows": rows,
            "grid_cols": cols,
        }

        try:
            res = requests.get(
                f"{self.base_url}/api/v1/gis/layer", params = params, timeout = 5
            )

            if res.status_code == 200:
                return res.json()
        
        except Exception as e:
            st.error(f"API GIS Layer Fetch Error: {str(e)}")
        return {}

    def trigger_prediction(
        self,
        lat: float,
        lon: float,
        depths: Optional[list] = None,
        days: int = 7,
        enkf:bool = True,
    ) -> Dict[str, Any]:
        """Execute physical model prediction via POST /api/v1/predict."""

        if depths is None:
            depths = [5.0, 15.0, 30.0, 60.0, 100.0]

        payload = {
            "latitude": lat,
            "longitude": lon,
            "depth_profile_cm": depths,
            "simulation_days": days,
            "include_enkf_assimilation": enkf,
        }

        try:
            res = requests.post(
                f"{self.base_url}/api/v1/predict", json=payload, timeout=5
            )

            if res.status_code == 200:
                return res.json()

        except Exception as e:
            st.error(f"API Prediction Request Error: {str(e)}")
        return {}

@st.cache_resource
def get_api_client() -> FastAPIClient:
    return FastAPIClient()
        