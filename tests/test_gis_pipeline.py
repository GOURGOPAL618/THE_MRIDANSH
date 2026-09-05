"""
THE MRIDANSH : Phase 3 GIS Integration & Telementary Test Suite (Day 34)
Verifies GIS Sub-Grid Mesh Generation, GeoJSON Properties, and endpoint response structures.
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_gis_layer_endpoint_success():
    """Verify `/api/v1/gis/layer` returns valid GeoJSON structure."""
    response = client.get("/api/v1/gis/layer?layer_type=spatial_grid_mesh&rows=4&cols=4")
    assert response.status_code == 200

    data = response.json()
    assert data.get("status") == "SUCCESS"
    assert "geojson_data" in data

    geojson = data["geojson_data"]
    assert geojson.get("type") == "FeatureCollection"
    features = geojson.get("features", [])
    assert len(features) == 16   # 4x4 Grid = 16 sub-tiles

    # Check key polygon properties
    first_tile = features[0]
    assert first_tile.get("type") == "Feature"
    assert first_tile["geometry"]["type"] == "Polygon"
    assert "tile_id" in first_tile["properties"]
    assert "row" in first_tile["properties"]
    assert "col" in first_tile["properties"]

def test_gis_layer_invalid_type():
    """Verify error handling for unsupported GIS layer types."""
    response = client.get("/api/v1/gis/layer?layer_type=unknown_layer")
    assert response.status_code in [400, 422, 500]
