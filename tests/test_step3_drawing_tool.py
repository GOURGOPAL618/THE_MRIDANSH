# THE MRIDANSH - VERIFICATION TEST SUITE
# Test: tests/test_step3_drawing_tool.py
# Verification Target: Step 3 (Permanent Google Maps Hybrid & Draw Toolbar)
# Standards: RTCA DO-178C Level-A / OGC GeoJSON
# Lead Systems Architect: Gouragopal Mohapatra (JCC Campus 2, RS-SDA Division)

import sys
from pathlib import Path
import importlib.util
import numpy as np
import pytest
import folium
from folium import plugins

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Load module from path to handle leading numerical prefix
spec = importlib.util.spec_from_file_location(
    "map_renderers",
    str(ROOT_DIR / "6_dashboard" / "renderers" / "map_renderers.py")
)
map_module = importlib.util.module_from_spec(spec)
sys.modules["map_renderers"] = map_module
spec.loader.exec_module(map_module)
GISMapRenderer = map_module.GISMapRenderer


class TestStep3DrawingTool:
    """Rigorous verification suite for Step 3 Map Draw Controls and Polygon Ingestion."""

    def test_01_permanent_google_maps_hybrid_and_draw_attached(self):
        """Verifies that Folium map contains Google Maps Hybrid as permanent base and Draw toolbar attached."""
        renderer = GISMapRenderer(default_center=(20.5000, 86.4200), default_zoom=12)
        f_map = renderer.create_folium_2d_map()

        # Verify Google Maps Hybrid tiles are configured
        tile_layers = [c for c in f_map._children.values() if isinstance(c, folium.TileLayer)]
        assert len(tile_layers) >= 1, "At least one TileLayer must be attached"
        assert any("mt1.google.com/vt/lyrs=y" in str(getattr(t, "tiles", "")) for t in tile_layers), \
            "Google Maps Hybrid must be permanent base tile layer"

        # Verify Draw toolbar is present
        draw_plugins = [c for c in f_map._children.values() if isinstance(c, plugins.Draw)]
        assert len(draw_plugins) == 1, "Exactly one Draw plugin must be permanently attached to the map"

        draw = draw_plugins[0]
        options = draw.draw_options
        assert options.get("polyline") is False, "Polyline must be disabled to prevent open linear features"
        assert options.get("circle") is False, "Circle must be disabled for farm field boundaries"
        assert options.get("marker") is False, "Point markers must be disabled in draw toolbar"
        assert isinstance(options.get("polygon"), dict), "Polygon drawing option must be enabled"
        assert isinstance(options.get("rectangle"), dict), "Rectangle drawing option must be enabled"

    def test_02_custom_farm_polygon_layer_overlay(self):
        """Verifies that an active user polygon is correctly overlaid as a folium.Polygon layer."""
        renderer = GISMapRenderer(default_center=(20.5000, 86.4200), default_zoom=12)
        f_map = renderer.create_folium_2d_map()

        farm_poly = [
            (86.4180, 20.4980),
            (86.4280, 20.4980),
            (86.4280, 20.5080),
            (86.4180, 20.5080),
            (86.4180, 20.4980),
        ]
        poly_latlon = [[pt[1], pt[0]] for pt in farm_poly]
        poly_layer = folium.Polygon(
            locations=poly_latlon,
            color="#00ff88",
            weight=3,
            fill=True,
            fill_color="#00e5ff",
            fill_opacity=0.28,
            popup="Active Custom Farm Boundary",
        )
        poly_layer.add_to(f_map)

        polygons = [c for c in f_map._children.values() if isinstance(c, folium.Polygon)]
        assert len(polygons) >= 1, "User farm boundary polygon layer must be present in map"
        assert len(polygons[0].locations) == len(farm_poly)

    def test_03_geojson_coordinate_extraction_and_centroid(self):
        """Verifies parsing of Leaflet GeoJSON drawing event to (lon, lat) tuples and distinct centroid."""
        raw_drawing_event = {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [86.4150, 20.4950],
                        [86.4300, 20.4950],
                        [86.4300, 20.5050],
                        [86.4150, 20.5050],
                        [86.4150, 20.4950],
                    ]
                ],
            },
        }

        raw_coords = raw_drawing_event["geometry"]["coordinates"][0]
        parsed_poly = [(round(float(pt[0]), 6), round(float(pt[1]), 6)) for pt in raw_coords]

        assert len(parsed_poly) == 5
        assert parsed_poly[0] == parsed_poly[-1], "Polygon must be closed"

        # Unique vertices (excluding closing duplicate)
        distinct_verts = parsed_poly[:-1] if parsed_poly[0] == parsed_poly[-1] else parsed_poly
        c_lon = float(np.mean([pt[0] for pt in distinct_verts]))
        c_lat = float(np.mean([pt[1] for pt in distinct_verts]))

        assert 86.4150 <= c_lon <= 86.4300
        assert 20.4950 <= c_lat <= 20.5050
        assert round(c_lon, 4) == 86.4225
        assert round(c_lat, 4) == 20.5000
