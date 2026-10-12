"""
THE MRIDANSH : Runtime Cache, State Manager & REST API Integration Client (Day 26)
Handles session state, unified soil state caching, and FastAPI backend integration.
"""

import sys
from pathlib import Path
from typing import Any

import numpy as np
import requests
import streamlit as st

# Ensure repository root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))


from enum import Enum


# ---------------------------------------------------------------------------
# 0. Explicit Dashboard Data State Contract
# ---------------------------------------------------------------------------
class DataState(str, Enum):
    """Explicit lifecycle and truth states for dashboard data consumption."""

    LIVE = "LIVE"
    DEMO = "DEMO"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    STALE = "STALE"


# ---------------------------------------------------------------------------
# 1. Soil State Container & Demonstration Cache Engine
# ---------------------------------------------------------------------------
class ObjectContainer:
    """Container for structured state objects with attribute and dict-like access."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@st.cache_resource
def get_unified_soil_engine_state():
    """Returns demonstration scaffolding soil state for UI development.

    NOTE: The dashboard is disconnected from the live physical inference engine
    and domain integration router. All metrics below are synthetic demonstration
    placeholders and must NOT be used for agronomic or civil engineering decisions.
    """

    # Hydro State - Uncalibrated Demo Placeholders
    hydro = ObjectContainer(
        moisture_profile=np.array([0.22, 0.28, 0.31, 0.33, 0.35]),
        saturation_degree=0.68,
        hydraulic_cond=0.0012,
        bulk_density=1.38,
        data_state=DataState.DEMO,
        is_demo=True,
    )

    # Bio Chemical State - Unconnected / Unavailable Sensors
    biogeo = ObjectContainer(
        nitrogen_est=None,
        phosphorus_est=None,
        potassium_est=None,
        organic_carbon=None,
        ph_level=None,
        data_state=DataState.UNAVAILABLE,
        is_demo=True,
    )

    # Terrain State - Fixed Geometric Reference
    terrain = ObjectContainer(
        elevation_m=245.0,
        slope_deg=4.2,
        aspect_deg=180.0,
        data_state=DataState.DEMO,
        is_demo=True,
    )

    # Reliability / Assimilation State - Engine Disconnected
    reliability = ObjectContainer(
        confidence_score=None,
        observation_freshness_hrs=None,
        ensemble_spread=None,
        status="DISCONNECTED",
        data_state=DataState.UNAVAILABLE,
        is_demo=True,
    )

    # Unified Soil State Container
    soil_state = ObjectContainer(
        hydro=hydro,
        biogeo=biogeo,
        terrain=terrain,
        reliability=reliability,
        data_state=DataState.DEMO,
        is_demo=True,
        provenance="Synthetic Demonstration Scaffolding (Not for Scientific/Field Use)",
    )

    # Translated Output Scaffolding - Clearly Isolated
    agronomy_output = {
        "data_state": DataState.DEMO,
        "is_demo": True,
        "provenance": "Synthetic Demonstration Scaffolding (Not for Agronomic Use)",
        "root_zone_moisture": 0.295,
        "organic_carbon_est": None,
        "npk_status": "Unavailable",
        "moisture_zone": "Uncalibrated Demo",
        "nutrient_recommendation": (
            "Nutrient recommendation unavailable — validated soil-chemistry inputs "
            "and a supported recommendation method are not connected."
        ),
    }

    civil_output = {
        "data_state": DataState.DEMO,
        "is_demo": True,
        "provenance": "Synthetic Demonstration Scaffolding (Not for Engineering Use)",
        "ground_stability_index": 0.84,
        "pore_water_pressure_kPa": 13.8,
        "bearing_capacity_est_kPa": None,
        "safety_assessment_available": False,
        "safety_status": (
            "Geotechnical safety assessment unavailable — no validated site-specific "
            "engineering assessment is connected."
        ),
    }

    return soil_state, agronomy_output, civil_output


# ---------------------------------------------------------------------------
# 2. FastAPI REST Client Wrapper (Day 26 Integration)
# ---------------------------------------------------------------------------


class FastAPIClient:
    """REST API Client Wrapper for Streamlit UI integration."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    def check_health(self) -> dict[str, Any]:
        """Fetch backend health and telemetry."""
        try:
            res = requests.get(f"{self.base_url}/health", timeout=3)
            if res.status_code == 200:
                data = res.json()
                data["data_state"] = DataState.LIVE
                data["inference_connected"] = False
                return data

        except Exception:
            pass
        return {
            "status": "OFFLINE",
            "service": "Backend Disconnected",
            "data_state": DataState.UNAVAILABLE,
            "inference_connected": False,
        }

    def fetch_gis_layer(
        self,
        layer_type: str = "spatial_grid_mesh",
        bbox: list | None = None,
        rows: int = 4,
        cols: int = 4,
    ) -> dict[str, Any]:
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
                f"{self.base_url}/api/v1/gis/layer", params=params, timeout=5
            )

            if res.status_code == 200:
                return res.json()

        except Exception as e:
            st.error(f"API GIS Layer Fetch Error: {e!s}")
        return {
            "status": "UNAVAILABLE",
            "data_state": DataState.UNAVAILABLE,
            "message": "GIS layer service unavailable",
        }

    def trigger_prediction(
        self,
        lat: float,
        lon: float,
        depths: list | None = None,
        days: int = 7,
        enkf: bool = False,
        allow_demo: bool = False,
    ) -> dict[str, Any]:
        """Execute physical model prediction via POST /api/v1/predict."""

        if depths is None:
            depths = [5.0, 15.0, 30.0, 60.0, 100.0]

        payload = {
            "latitude": lat,
            "longitude": lon,
            "depth_profile_cm": depths,
            "simulation_days": days,
            "include_enkf_assimilation": enkf,
            "allow_demo": allow_demo,
        }

        try:
            res = requests.post(
                f"{self.base_url}/api/v1/predict", json=payload, timeout=5
            )

            if res.status_code in (200, 503):
                return res.json()
            return {
                "status": "ERROR",
                "data_state": DataState.ERROR,
                "detail": f"HTTP {res.status_code}: {res.text}",
            }

        except Exception as e:
            return {
                "status": "ERROR",
                "data_state": DataState.ERROR,
                "detail": f"API Prediction Request Error: {e!s}",
            }


@st.cache_resource
def get_api_client() -> FastAPIClient:
    return FastAPIClient()
