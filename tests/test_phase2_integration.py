"""
THE MRIDANSH : Phase 2 End-to-End Integration Test Suite (Day 28)
Audits FastAPI REST Backend, Telemetry, Physics Predict Router & GIS Tile Router.
"""

import io
import sys
from pathlib import Path

import requests

# Force UTF-8 stdout so emoji/Unicode prints correctly on Windows cp1252 terminals
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Ensure repository root path is present
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

BASE_URL = "http://127.0.0.1:8000"


def test_phase2_pipeline():
    print("=" * 60)
    print(" [**] STARTING MRIDANSH PHASE 2 END-TO-END SYSTEM AUDIT ")
    print("=" * 60)

    # 1. Telemetry Health Endpoint Audit
    print("\n[1/4] Auditing Root & Health Endpoints...")
    res_health = requests.get(f"{BASE_URL}/health", timeout=5)
    assert res_health.status_code == 200, (
        f"Health Check Failed: {res_health.status_code}"
    )
    health_json = res_health.json()
    assert health_json.get("status") == "HEALTHY"
    print(
        f"  ✓ Health Telemetry Status: ONLINE | Service: {health_json.get('service')}"
    )

    # 2. V1 API Status Audit
    print("\n[2/4] Auditing /api/v1/status Subsystem Endpoint...")
    res_v1 = requests.get(f"{BASE_URL}/api/v1/status", timeout=5)
    assert res_v1.status_code == 200, f"V1 Status Failed: {res_v1.status_code}"
    v1_json = res_v1.json()
    assert v1_json.get("status") == "ONLINE"
    print(
        f"  ✓ V1 Subsystem: ONLINE | Active Routes: {len(v1_json.get('active_endpoints', []))}"
    )

    # 3. Physics Simulation POST Endpoint Audit
    print("\n[3/4] Auditing POST /api/v1/predict (Richards + EnKF Engine)...")
    payload = {
        "latitude": 20.2961,
        "longitude": 85.8245,
        "depth_profile_cm": [5.0, 15.0, 30.0, 60.0, 100.0],
        "simulation_days": 7,
        "include_enkf_assimilation": True,
    }

    res_predict = requests.post(f"{BASE_URL}/api/v1/predict", json=payload, timeout=5)
    assert res_predict.status_code == 200, (
        f"Predict route failed: {res_predict.status_code}"
    )
    pred_json = res_predict.json()
    assert pred_json.get("status") == "SUCCESS"
    assert len(pred_json.get("predicted_moisture_m3m3", [])) == 5
    print(
        f"  ✓ Richards-EnKF Physics Output Validated | Execution Time: {pred_json.get('execution_time_sec')}s"
    )

    # 4. GIS Layer GET Endpoint Audit
    print("\n[4/4] Auditing GET /api/v1/gis/layer (Sub-Grid Tiler Engine)...")
    gis_params = {
        "layer_type": "spatial_grid_mesh",
        "min_lon": 85.75,
        "min_lat": 20.20,
        "max_lon": 85.90,
        "max_lat": 20.35,
        "grid_rows": 4,
        "grid_cols": 4,
    }

    res_gis = requests.get(f"{BASE_URL}/api/v1/gis/layer", params=gis_params, timeout=5)
    assert res_gis.status_code == 200, f"GIS Route Failed: {res_gis.status_code}"
    gis_json = res_gis.json()
    assert gis_json.get("status") == "SUCCESS"
    features_len = len(gis_json.get("geojson_data", {}).get("features", []))
    assert features_len == 16
    print(
        f"  ✓ GIS Sub-Grid Mesh GeoJSON Validated | Received Polygons: {features_len}"
    )

    print("\n" + "=" * 82)
    print(" [OK] PHASE 2 AUDIT PASSED: ALL 4 REST PIPELINE ENDPOINTS VERIFIED ")
    print("=" * 82)


if __name__ == "__main__":
    test_phase2_pipeline()
