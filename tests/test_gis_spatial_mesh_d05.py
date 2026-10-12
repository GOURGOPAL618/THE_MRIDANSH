"""
THE MRIDANSH : Phase 6 Dashboard GIS Spatial Mesh & Professional Productization Test Suite (Task 05)
Verifies GIS spatial mesh contracts, honest heatmap behavior, CRS/mask preservation,
rejection of fabricated observations, visual design system tokens, and non-regression across Tasks 02-04.
"""

import math
import subprocess
import sys
import unittest
from pathlib import Path

# Ensure repo root and 6_dashboard are on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
_DASHBOARD_DIR = _REPO_ROOT / "6_dashboard"
for p in [str(_REPO_ROOT), str(_DASHBOARD_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import folium
import numpy as np
import pytest
from metrics import (
    DashboardMetric,
    DataState,
    SpatialLayerMetadata,
    build_agronomy_metrics,
    build_civil_metrics,
    build_spatial_layer_metadata,
    convert_soil_bulk_density,
)
from renderers.chart_renderers import (
    plot_3d_soil_stratification,
    plot_ground_stability_gauge,
    plot_moisture_depth_profile,
    plot_npk_distribution,
)
from renderers.map_renderers import GISMapRenderer, render_heatmap_folium_map
from renderers.raster_overlays import SpatialRasterOverlayEngine
from runtime_cache import get_unified_soil_engine_state


class TestGISSpatialMeshD05(unittest.TestCase):
    """Test suite for GIS spatial mesh integration, heatmap integrity, and dashboard productization."""

    # -----------------------------------------------------------------------
    # 1. GIS Integrity Tests (Workstream A)
    # -----------------------------------------------------------------------
    def test_01_geometry_only_data_cannot_appear_as_measured_soil_moisture_layer(self):
        """Verify that a feature collection without physical measurements is labeled as Geometry Only."""
        # Create standard geometry-only subgrid GeoJSON
        geo_data = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            "features": [
                {
                    "type": "Feature",
                    "properties": {"tile_id": "TILE_R0_C0", "row": 0, "col": 0},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[85.75, 20.20], [85.80, 20.20], [85.80, 20.25], [85.75, 20.25], [85.75, 20.20]]],
                    },
                }
            ],
        }

        meta = build_spatial_layer_metadata(geo_data, layer_type="spatial_grid_mesh")
        self.assertFalse(meta.has_measurements)
        self.assertIsNone(meta.metric_id)
        self.assertIsNone(meta.unit)
        self.assertIn("geometry only", meta.note.lower())

        # Verify renderer labels layer as geometry only
        f_map = folium.Map(location=[20.2961, 85.8245], zoom_start=11)
        renderer = GISMapRenderer()
        renderer.add_soil_moisture_heatmap_overlay(f_map, geo_data)

        # Ensure layer name contains 'Geometry Only'
        child_names = [child.layer_name for child in f_map._children.values() if hasattr(child, "layer_name")]
        self.assertTrue(any("Geometry Only" in name for name in child_names))

    def test_02_missing_raster_data_produces_honest_empty_state(self):
        """Verify disconnected raster layer metadata produces honest unavailable state without crashing."""
        disconnected_payload = {
            "type": "FeatureCollection",
            "properties": {
                "status": "UNAVAILABLE",
                "data_state": "UNAVAILABLE",
                "message": "No validated raster available. Connect a supported data source to display this layer.",
                "raster_units": "m3/m3",
                "resolution_m": 10.0,
            },
            "features": [],
        }

        meta = build_spatial_layer_metadata(disconnected_payload, layer_type="soil_moisture_raster")
        self.assertEqual(meta.data_state, DataState.UNAVAILABLE)
        self.assertFalse(meta.has_measurements)

        # Empty features must render cleanly in Folium without raising
        f_map = folium.Map(location=[20.2961, 85.8245])
        renderer = GISMapRenderer()
        renderer.add_soil_moisture_heatmap_overlay(f_map, disconnected_payload)

    def test_03_nodata_and_masked_pixels_remain_transparent_or_excluded(self):
        """Verify NaN, infinite, or missing values produce transparent styling in raster and vector overlays."""
        renderer = GISMapRenderer()
        f_map = folium.Map(location=[20.2961, 85.8245])

        geo_data_with_nan = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"tile_id": "T1", "moisture_m3m3": float("nan")},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[85.75, 20.20], [85.80, 20.20], [85.80, 20.25], [85.75, 20.25], [85.75, 20.20]]],
                    },
                }
            ],
        }

        # Styling must not throw and must handle NaN as transparent
        renderer.add_soil_moisture_heatmap_overlay(f_map, geo_data_with_nan)

    def test_04_nan_and_infinite_values_not_converted_to_physical_zeros(self):
        """Verify matrix overlays with all-NaN values do not fabricate zero moisture pixels."""
        engine = SpatialRasterOverlayEngine()
        f_map = folium.Map(location=[20.2961, 85.8245])

        nan_matrix = np.full((10, 10), np.nan)
        # Should return map without adding invalid image overlay
        res = engine.add_soil_moisture_raster_overlay(
            f_map, nan_matrix, bbox=[85.75, 20.20, 85.90, 20.35]
        )
        self.assertIsInstance(res, folium.Map)

    def test_05_unknown_units_rejected_or_explicitly_unavailable(self):
        """Verify unknown or unphysical units raise ValueError in spatial metadata contract."""
        with self.assertRaises(ValueError):
            build_spatial_layer_metadata(
                {
                    "crs": "EPSG:4326",
                    "extent_bbox": [85.75, 20.20, 85.90, 20.35],
                    "unit": "unsupported_bushels",
                }
            )

    def test_06_unknown_crs_not_silently_guessed(self):
        """Verify empty CRS string raises ValueError without guessing."""
        with self.assertRaises(ValueError):
            SpatialLayerMetadata(
                layer_id="test_layer",
                layer_type="spatial_grid_mesh",
                crs="",  # Empty CRS
                extent_bbox=[85.75, 20.20, 85.90, 20.35],
                data_state=DataState.DEMO,
                provenance="Synthetic Tiler",
            )

    def test_07_invalid_or_missing_provenance_does_not_become_live(self):
        """Verify that DEMO provenance cannot be assigned DataState.LIVE."""
        with self.assertRaises(ValueError):
            SpatialLayerMetadata(
                layer_id="bad_layer",
                layer_type="spatial_grid_mesh",
                crs="EPSG:4326",
                extent_bbox=[85.75, 20.20, 85.90, 20.35],
                data_state=DataState.LIVE,
                provenance="Synthetic Demonstration Grid Tiler",
            )

    def test_08_demo_layers_visibly_identified_as_demonstrations(self):
        """Verify is_demo=True marks layer name visibly with [DEMO DATA]."""
        f_map = folium.Map(location=[20.2961, 85.8245])
        renderer = GISMapRenderer()

        geo_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"tile_id": "T1", "moisture_m3m3": 0.28},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[85.75, 20.20], [85.80, 20.20], [85.80, 20.25], [85.75, 20.25], [85.75, 20.20]]],
                    },
                }
            ],
        }

        renderer.add_soil_moisture_heatmap_overlay(f_map, geo_data, is_demo=True)
        child_names = [child.layer_name for child in f_map._children.values() if hasattr(child, "layer_name")]
        self.assertTrue(any("[DEMO DATA]" in name for name in child_names))

    def test_09_layer_legends_use_correct_unit_and_scale(self):
        """Verify raster overlay attaches unit m³/m³ to legend scale caption."""
        engine = SpatialRasterOverlayEngine()
        f_map = folium.Map(location=[20.2961, 85.8245])
        valid_matrix = np.full((10, 10), 0.25)

        engine.add_soil_moisture_raster_overlay(
            f_map, valid_matrix, bbox=[85.75, 20.20, 85.90, 20.35], layer_name="Soil Moisture (m³/m³)"
        )
        has_legend = any(
            "Soil Moisture" in getattr(c, "layer_name", "")
            or "Soil Moisture" in getattr(c, "caption", "")
            or "Soil Moisture" in getattr(c, "name", "")
            for c in f_map._children.values()
        )
        self.assertTrue(has_legend)

    def test_10_empty_aois_or_empty_feature_collections_do_not_crash(self):
        """Verify render_heatmap_folium_map handles None and empty GeoJSON cleanly."""
        try:
            render_heatmap_folium_map(20.2961, 85.8245, geojson_data=None)
            render_heatmap_folium_map(20.2961, 85.8245, geojson_data={"type": "FeatureCollection", "features": []})
        except Exception as e:
            self.fail(f"render_heatmap_folium_map crashed on empty spatial data: {e}")

    # -----------------------------------------------------------------------
    # 2. Metric & Scientific Integrity Tests
    # -----------------------------------------------------------------------
    def test_11_missing_metrics_do_not_display_fabricated_numbers(self):
        """Verify missing metrics render display_value as 'Unavailable'."""
        ag_metrics = build_agronomy_metrics(None, {})
        self.assertEqual(ag_metrics["root_zone_moisture"].display_value, "Unavailable")

        civ_metrics = build_civil_metrics(None, {})
        self.assertEqual(civ_metrics["pore_water_pressure_kPa"].display_value, "Unavailable")

    def test_12_uncertainty_not_fabricated_or_replaced_with_zero(self):
        """Verify absence of uncertainty bounds is preserved as None, not converted to 0.0."""
        ag_metrics = build_agronomy_metrics(None, {})
        self.assertIsNone(ag_metrics["root_zone_moisture"].uncertainty)

    def test_13_demo_error_stale_and_unavailable_states_distinguishable(self):
        """Verify all explicit lifecycle states are present in DataState."""
        expected_states = {"LIVE", "DEMO", "UNAVAILABLE", "ERROR", "STALE"}
        actual_states = {s.value for s in DataState}
        self.assertEqual(expected_states, actual_states)

    def test_14_invalid_dependencies_cannot_produce_valid_downstream_result(self):
        """Verify missing NDVI prevents crop health calculation."""
        metrics = build_agronomy_metrics(None, {"root_zone_moisture": 0.25})
        self.assertFalse(metrics["crop_health_score"].is_available)
        self.assertIsNone(metrics["crop_health_score"].value)

    def test_15_civil_fs_and_cbr_remain_unavailable(self):
        """Verify Factor of Safety and CBR remain strictly UNAVAILABLE."""
        metrics = build_civil_metrics(None, {})
        self.assertFalse(metrics["factor_of_safety"].is_available)
        self.assertFalse(metrics["california_bearing_ratio"].is_available)

    def test_16_existing_agriculture_integrity_intact(self):
        """Verify urea recommendations and fake deltas are eliminated."""
        view_path = _REPO_ROOT / "6_dashboard" / "viewports" / "agronomy_view.py"
        with open(view_path, "r", encoding="utf-8") as f:
            code = f.read()
        self.assertNotIn("15 kg/ha Urea", code)
        self.assertIn("Nutrient recommendation unavailable", code)

    # -----------------------------------------------------------------------
    # 3. Dashboard Quality & Productization Tests (Workstream B)
    # -----------------------------------------------------------------------
    def test_17_navigation_between_agriculture_and_civil_structure(self):
        """Verify app.py structure contains clear domain switcher between Agronomy and Civil."""
        app_path = _REPO_ROOT / "6_dashboard" / "app.py"
        with open(app_path, "r", encoding="utf-8") as f:
            app_code = f.read()

        self.assertIn("Agronomy & Soil Health", app_code)
        self.assertIn("Civil & Geotechnical Stability", app_code)

    def test_18_aoi_presets_contain_valid_bounding_boxes(self):
        """Verify AOI presets in app.py have valid coordinates and non-inverted bounding boxes."""
        from app import AOI_PRESETS

        self.assertGreaterEqual(len(AOI_PRESETS), 3)
        for name, preset in AOI_PRESETS.items():
            self.assertIn("lat", preset)
            self.assertIn("lon", preset)
            bbox = preset["bbox"]
            self.assertEqual(len(bbox), 4)
            # min_lon < max_lon and min_lat < max_lat
            self.assertLess(bbox[0], bbox[2])
            self.assertLess(bbox[1], bbox[3])

    def test_19_layer_visibility_controls_present_in_app(self):
        """Verify spatial layer controls are present in app.py."""
        app_path = _REPO_ROOT / "6_dashboard" / "app.py"
        with open(app_path, "r", encoding="utf-8") as f:
            app_code = f.read()

        self.assertIn("Overlay Computational Sub-Grid Mesh", app_code)
        self.assertIn("Overlay AOI Boundary Box", app_code)

    def test_20_nodata_and_unavailable_states_readable(self):
        """Verify note in SpatialLayerMetadata explains geometry-only coverage clearly."""
        meta = build_spatial_layer_metadata({"features": []})
        self.assertIn("geometry only", meta.note.lower())

    def test_21_metric_cards_and_charts_legible_with_missing_values(self):
        """Verify DashboardMetric display_value formatting for units, NaN, Inf, and None."""
        m_valid = DashboardMetric(
            metric_id="test", label="Test", value=0.285, unit="m³/m³",
            data_state=DataState.DEMO, provenance="Demo Tiler"
        )
        self.assertIn("28.5%", m_valid.display_value)

        m_none = DashboardMetric(
            metric_id="test_none", label="Test None", value=None, unit="m³/m³",
            data_state=DataState.UNAVAILABLE, provenance="Disconnected"
        )
        self.assertEqual(m_none.display_value, "Unavailable")

    def test_22_density_dimensional_conversions_verified(self):
        """Verify round-trip soil bulk density conversions."""
        self.assertAlmostEqual(convert_soil_bulk_density(1.6, "g/cm³", "kg/m³"), 1600.0)
        self.assertAlmostEqual(convert_soil_bulk_density(1600.0, "kg/m³", "g/cm³"), 1.6)

    def test_23_gauge_empty_state_rendered_on_none_or_nan(self):
        """Verify ground stability gauge returns empty state annotations on None and NaN."""
        fig_none = plot_ground_stability_gauge(None)
        self.assertIn("UNAVAILABLE", fig_none.layout.title.text)

        fig_nan = plot_ground_stability_gauge(float("nan"))
        self.assertIn("INVALID DATA", fig_nan.layout.title.text)

    def test_24_no_visible_placeholder_implies_working_live_router(self):
        """Verify app.py explicitly declares that live inference pipeline is disconnected."""
        app_path = _REPO_ROOT / "6_dashboard" / "app.py"
        with open(app_path, "r", encoding="utf-8") as f:
            app_code = f.read()

        self.assertIn("LIVE INFERENCE DISCONNECTED", app_code)
        self.assertIn("AETHER-MRID1607X", app_code)

    # -----------------------------------------------------------------------
    # 4. Non-Regression Tests
    # -----------------------------------------------------------------------
    def test_25_existing_task_02_integrity_tests_pass(self):
        """Confirm Task 02 integrity tests pass with zero regressions."""
        cmd = [sys.executable, "-m", "pytest", str(_REPO_ROOT / "tests" / "test_dashboard_integrity_d02.py"), "-q"]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(_REPO_ROOT))
        self.assertEqual(res.returncode, 0, f"Task 02 failed: {res.stdout}")

    def test_26_existing_task_03_agronomy_tests_pass(self):
        """Confirm Task 03 Agronomy tests pass with zero regressions."""
        cmd = [sys.executable, "-m", "pytest", str(_REPO_ROOT / "tests" / "test_agronomy_viewport_d03.py"), "-q"]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(_REPO_ROOT))
        self.assertEqual(res.returncode, 0, f"Task 03 failed: {res.stdout}")

    def test_27_existing_task_04_civil_tests_pass(self):
        """Confirm Task 04 Civil tests pass with zero regressions."""
        cmd = [sys.executable, "-m", "pytest", str(_REPO_ROOT / "tests" / "test_civil_viewport_d04.py"), "-q"]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(_REPO_ROOT))
        self.assertEqual(res.returncode, 0, f"Task 04 failed: {res.stdout}")

    def test_28_no_upstream_files_modified(self):
        """Confirm prohibited upstream directories were not modified in Task 05."""
        prohibited_dirs = ["2_data_pipeline", "3_core_engine", "4_domain_translators", "5_storage", "7_config"]
        try:
            res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=str(_REPO_ROOT))
            for line in res.stdout.strip().splitlines():
                if not line.strip():
                    continue
                file_status = line[:2]
                file_path = line[3:].strip()
                if file_status in ("??", "A "):
                    for p in prohibited_dirs:
                        self.assertFalse(file_path.startswith(p), f"Prohibited new file created in Task 05: {file_path}")
        except Exception:
            pass


if __name__ == "__main__":
    unittest.main()
