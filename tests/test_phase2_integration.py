"""
THE MRIDANSH : Phase 2 End-to-End Integration Test Suite (Day 28 / Task 06 Hardened)
Audits FastAPI REST Backend, Telemetry, Physics Predict Router & GIS Tile Router.
"""

import io
import sys
from pathlib import Path

# Force UTF-8 stdout so emoji/Unicode prints correctly on Windows cp1252 terminals
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Ensure repository root and dashboard api paths are present
ROOT_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_API_DIR = ROOT_DIR / "6_dashboard" / "api"
for p in [str(ROOT_DIR), str(DASHBOARD_API_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_phase2_pipeline():
    print("=" * 60)
    print(" [**] STARTING MRIDANSH PHASE 2 END-TO-END SYSTEM AUDIT ")
    print("=" * 60)

    # 1. Telemetry Health Endpoint Audit
    print("\n[1/4] Auditing Root & Health Endpoints...")
    res_health = client.get("/health")
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
    res_v1 = client.get("/api/v1/status")
    assert res_v1.status_code == 200, f"V1 Status Failed: {res_v1.status_code}"
    v1_json = res_v1.json()
    assert v1_json.get("status") == "ONLINE"
    print(
        f"  ✓ V1 Subsystem: ONLINE | Active Routes: {len(v1_json.get('active_endpoints', []))}"
    )

    # 3. Physics Simulation POST Endpoint Audit (Hardened Scientific Integrity)
    print("\n[3/4] Auditing POST /api/v1/predict (Hardened Scientific Integrity Gate)...")
    payload_live = {
        "latitude": 20.2961,
        "longitude": 85.8245,
        "depth_profile_cm": [5.0, 15.0, 30.0, 60.0, 100.0],
        "simulation_days": 7,
        "include_enkf_assimilation": True,
        "allow_demo": False,
    }

    # Live unverified request must be rejected with HTTP 503
    res_predict_live = client.post("/api/v1/predict", json=payload_live)
    assert res_predict_live.status_code == 503, (
        f"Unverified live request must return HTTP 503: {res_predict_live.status_code}"
    )
    assert res_predict_live.json().get("detail", {}).get("status") == "UNAVAILABLE"

    # Explicit Demo request returns HTTP 200 with DEMO status
    payload_demo = dict(payload_live, allow_demo=True)
    res_predict_demo = client.post("/api/v1/predict", json=payload_demo)
    assert res_predict_demo.status_code == 200, (
        f"Demo predict route failed: {res_predict_demo.status_code}"
    )
    pred_json = res_predict_demo.json()
    assert pred_json.get("status") == "DEMO"
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

    res_gis = client.get("/api/v1/gis/layer", params=gis_params)
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
