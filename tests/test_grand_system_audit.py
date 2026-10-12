"""
THE MRIDANSH : GRAND SYSTEM INTEGRITY & END-TO-END PIPELINE AUDIT
==================================================================
Ultra-Strict Verification Test Suite across the Complete Architecture:
  [Phase 1] 2_data_pipeline      : Ingestion schemas, Grid Tiler, Multi-modal Satellite Fusion
  [Phase 2] 3_core_engine        : Spatial-Temporal Encoder, Richards-1D PDE Physics, EnKF State Estimator
  [Phase 3] 4_domain_translators : DomainInput/Output Contracts, Semantic Gates, Agronomy & Civil Translators, Router
  [Phase 4] 6_dashboard          : Typed Metrics, Spatial Metadata, Map & Raster Renderers, FastAPI REST Backend
  [Phase 5] Grand End-to-End     : Unbroken data flow from Satellite Observation -> State Estimator -> Translator -> Dashboard

Execution Principle: BUILD → PROVE → BREAK → COMPARE → LOCK
"""

import math
import os
import sys
import unittest
from pathlib import Path

import numpy as np
import torch
import folium

# Configure sys.path for all modules
ROOT_DIR = Path(__file__).resolve().parent.parent
PIPELINE_DIR = ROOT_DIR / "2_data_pipeline"
CORE_DIR = ROOT_DIR / "3_core_engine"
TRANSLATORS_DIR = ROOT_DIR / "4_domain_translators"
DASHBOARD_DIR = ROOT_DIR / "6_dashboard"
API_DIR = DASHBOARD_DIR / "api"

for p in [ROOT_DIR, PIPELINE_DIR, CORE_DIR, TRANSLATORS_DIR, DASHBOARD_DIR, API_DIR]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# ---------------------------------------------------------------------------
# Module Imports
# ---------------------------------------------------------------------------
# 1. Pipeline
from schemas.satellite_schema import GeospatialRasterAsset
from preprocessing.grid_tiler import GeospatialGridTiler
from fusion.satellite_fusion import (
    SatelliteSAROpticalFusionEngine,
    MissingModalityError,
    InvalidModalityError,
    GridMismatchError,
)

# 2. Core Engine
from models.spatial_temporal_encoder import SpatialTemporalEncoderBackbone
from physics.richards_engine import RichardsSoilPhysicsEngine
from state_estimation.enkf_filter import EnsembleKalmanFilterEngine

# 3. Domain Translators
from base import DomainInput, DomainOutput
from agronomy_translator import AgronomyHealthTranslator
from civil_translator import CivilLoadTranslator
from domain_integrator import DomainIntegrationRouter

# 4. Dashboard
from metrics import (
    DashboardMetric,
    DataState,
    SpatialLayerMetadata,
    build_agronomy_metrics,
    build_civil_metrics,
    build_spatial_layer_metadata,
    convert_soil_bulk_density,
)
from renderers.map_renderers import GISMapRenderer, render_heatmap_folium_map
from renderers.raster_overlays import SpatialRasterOverlayEngine
from renderers.chart_renderers import (
    plot_moisture_depth_profile,
    plot_ground_stability_gauge,
    plot_npk_distribution,
)
from fastapi.testclient import TestClient
from main import app


def _create_mock_raster_asset(
    crs="EPSG:32645",
    res=(10.0, 10.0),
    bounds=(0.0, 90.0, 100.0, 100.0),
    valid=True,
    stac_id="MOCK_STAC_01",
    asset_key="B02",
) -> GeospatialRasterAsset:
    """Helper to construct valid GeospatialRasterAsset instances for fusion tests."""
    raw = np.ones((1, 10, 10), dtype=np.float32)
    mask = np.ones((1, 10, 10), dtype=bool) if valid else np.zeros((1, 10, 10), dtype=bool)
    return GeospatialRasterAsset(
        raw_array=raw,
        raw_dtype="float32",
        crs=crs,
        transform=(res[0], 0.0, bounds[0], 0.0, -res[1], bounds[3]),
        bounds=bounds,
        resolution=res,
        valid_data_mask=mask,
        stac_item_id=stac_id,
        asset_key=asset_key,
    )


class GrandSystemIntegrityAudit(unittest.TestCase):
    """Ultra-Strict End-to-End System Audit for THE MRIDANSH."""

    def setUp(self):
        torch.manual_seed(42)
        np.random.seed(42)
        self.api_client = TestClient(app)

    # =======================================================================
    # PHASE 1: DATA PIPELINE INTEGRITY (2_data_pipeline)
    # =======================================================================

    def test_01_grid_tiler_geometry_and_boundary_correctness(self):
        """[Pipeline] Verify GeospatialGridTiler enforces coordinate bounds and geometry contracts."""
        tiler = GeospatialGridTiler()
        bbox = [85.75, 20.20, 85.90, 20.35]
        tiles = tiler.create_spatial_subgrids(bbox, rows=4, cols=4)

        self.assertEqual(len(tiles), 16, "Must produce exactly 16 sub-grid tiles for 4x4 matrix")
        geojson = tiler.export_tiles_to_geojson(tiles)

        self.assertEqual(geojson["type"], "FeatureCollection")
        self.assertEqual(len(geojson["features"]), 16)

        for i, feat in enumerate(geojson["features"]):
            props = feat["properties"]
            self.assertIn("tile_id", props)
            self.assertIn("row", props)
            self.assertIn("col", props)
            self.assertNotIn("moisture_m3m3", props, "Tiler must not inject synthetic moisture measurements")

            coords = feat["geometry"]["coordinates"][0]
            for lon, lat in coords:
                self.assertGreaterEqual(lon, bbox[0] - 1e-5)
                self.assertLessEqual(lon, bbox[2] + 1e-5)
                self.assertGreaterEqual(lat, bbox[1] - 1e-5)
                self.assertLessEqual(lat, bbox[3] + 1e-5)

    def test_02_satellite_fusion_engine_strict_modality_trapping(self):
        """[Pipeline] Verify SatelliteSAROpticalFusionEngine rejects missing/corrupted modalities without fabrication."""
        engine = SatelliteSAROpticalFusionEngine(
            target_crs="EPSG:32645",
            target_resolution=(10.0, 10.0),
            target_bounds=(0.0, 90.0, 100.0, 100.0),
        )

        # 1. Missing required modality must raise MissingModalityError (no zero-filling)
        with self.assertRaises(MissingModalityError):
            engine.create_fused_spatial_tensor(
                sar_vv=_create_mock_raster_asset(),
                sar_vh=_create_mock_raster_asset(),
                ndvi=_create_mock_raster_asset(),
                ndmi=None,  # Missing NDMI
                dem_elevation=_create_mock_raster_asset(),
                dem_slope=_create_mock_raster_asset(),
            )

        # 2. 100% invalid masked modality must raise InvalidModalityError
        all_masked_asset = _create_mock_raster_asset(valid=False)
        with self.assertRaises(InvalidModalityError):
            engine.create_fused_spatial_tensor(
                sar_vv=all_masked_asset,
                sar_vh=_create_mock_raster_asset(),
                ndvi=_create_mock_raster_asset(),
                ndmi=_create_mock_raster_asset(),
                dem_elevation=_create_mock_raster_asset(),
                dem_slope=_create_mock_raster_asset(),
            )

        # 3. Misaligned bounds must raise GridMismatchError
        misaligned_asset = _create_mock_raster_asset(bounds=(50.0, 140.0, 150.0, 150.0))
        with self.assertRaises(GridMismatchError):
            engine._verify_alignment(misaligned_asset, "SAR_VV")

        # 4. Valid modalities fuse cleanly preserving shapes and masks
        fused = engine.create_fused_spatial_tensor(
            sar_vv=_create_mock_raster_asset(stac_id="S1_VV"),
            sar_vh=_create_mock_raster_asset(stac_id="S1_VH"),
            ndvi=_create_mock_raster_asset(stac_id="S2_NDVI"),
            ndmi=_create_mock_raster_asset(stac_id="S2_NDMI"),
            dem_elevation=_create_mock_raster_asset(stac_id="DEM_ELEV"),
            dem_slope=_create_mock_raster_asset(stac_id="DEM_SLOPE"),
        )
        self.assertEqual(fused["tensor_shape"], (10, 10, 7))
        self.assertEqual(fused["fused_validity_mask"].shape, (10, 10, 7))
        self.assertTrue(np.all(fused["fused_validity_mask"]))

    # =======================================================================
    # PHASE 2: CORE PHYSICS ENGINE & STATE ESTIMATION (3_core_engine)
    # =======================================================================

    def test_03_spatial_temporal_encoder_topology_and_finite_numerics(self):
        """[Core] Verify SpatialTemporalEncoder processes multi-modal satellite tensor with finite gradients."""
        encoder = SpatialTemporalEncoderBackbone(in_channels=5, feature_dim=16)
        x = torch.rand(2, 1, 5, 32, 32, dtype=torch.float32, requires_grad=True)

        out = encoder(x)
        self.assertIn("latent_representation", out)
        features = out["latent_representation"]
        self.assertEqual(features.shape, (2, 16, 32, 32), "Must map (B, T, C, H, W) to (B, feature_dim, H, W)")
        self.assertTrue(torch.isfinite(features).all(), "Encoder outputs must be 100% finite")

        loss = features.sum()
        loss.backward()
        self.assertIsNotNone(x.grad)
        self.assertTrue(torch.isfinite(x.grad).all(), "Backprop gradients must be finite")

    def test_04_richards_physics_engine_flux_conservation_invariants(self):
        """[Core] Verify RichardsSoilPhysicsEngine invariants: uniform gradient produces zero Darcian flux."""
        engine = RichardsSoilPhysicsEngine()

        # Invariant 1: Uniform moisture field across space must yield near-zero Darcian flux
        uniform_moisture = torch.full((1, 16, 16), 0.28, dtype=torch.float32)
        out = engine.compute_richards_flux(uniform_moisture, depth_interval_m=0.1)

        self.assertIn("water_flux", out)
        self.assertIn("hydraulic_conductivity", out)
        self.assertIn("physics_constraint_loss", out)

        flux = out["water_flux"].detach().numpy()
        self.assertTrue(np.allclose(flux, 0.0, atol=1e-4), "Zero moisture gradient must produce negligible spatial flux")

        # Invariant 2: Rank-1 tensor must be rejected (needs at least 2 spatial dimensions)
        rank1_moisture = torch.tensor([0.2, 0.3, 0.4])
        with self.assertRaises(ValueError):
            engine.compute_richards_flux(rank1_moisture)

    def test_05_enkf_state_estimator_zero_innovation_identity_and_determinism(self):
        """[Core] Verify EnsembleKalmanFilterEngine zero-innovation identity and determinism."""
        engine = EnsembleKalmanFilterEngine(num_ensembles=10, obs_noise_std=0.02)
        rng = np.random.default_rng(100)

        n_state = 16
        prior_mean_val = 0.30
        prior_ens = rng.normal(loc=prior_mean_val, scale=0.01, size=(n_state, 10)).astype(np.float32)
        exact_obs = np.full((n_state,), prior_mean_val, dtype=np.float32)

        out = engine.assimilate_observations(prior_ens, exact_obs, rng=np.random.default_rng(100))
        post_state = out["posterior_soil_state"]

        self.assertTrue(
            np.allclose(post_state, prior_mean_val, atol=0.02),
            f"Zero innovation must preserve prior mean (got {post_state.mean():.4f})"
        )

        # Invariant: NaN in observations must be trapped
        corrupted_obs = exact_obs.copy()
        corrupted_obs[0] = np.nan
        with self.assertRaises(ValueError):
            engine.assimilate_observations(prior_ens, corrupted_obs)

    # =======================================================================
    # PHASE 3: DOMAIN TRANSLATORS & INTEGRATION BOUNDARY (4_domain_translators)
    # =======================================================================

    def test_06_domain_input_contract_immutability_and_physical_bounds(self):
        """[Translators] Verify DomainInput strictly bounds physical variables and rejects invalid inputs."""
        valid_input = DomainInput(
            soil_state=np.array([[0.22, 0.28], [0.31, 0.34]]),
            state_variable="volumetric_soil_moisture",
            unit="m3/m3",
            valid_data_mask=np.ones((2, 2), dtype=bool),
            provenance={"source": "Core Richards Physics PDE Solver"},
        )
        self.assertEqual(valid_input.state_variable, "volumetric_soil_moisture")
        self.assertEqual(valid_input.soil_state.shape, (2, 2))

        # Check: non-finite values without mask must raise ValueError
        with self.assertRaises(ValueError):
            DomainInput(
                soil_state=np.array([[np.nan, 0.25], [0.20, 0.30]]),
                valid_data_mask=None,
            )

        # Check: invalid mask shape must raise ValueError
        with self.assertRaises(ValueError):
            DomainInput(
                soil_state=np.array([[0.25, 0.30], [0.20, 0.30]]),
                valid_data_mask=np.ones((3, 3), dtype=bool),  # Mismatched shape
            )

        # Check: rank-1 soil state must raise ValueError
        with self.assertRaises(ValueError):
            DomainInput(
                soil_state=np.array([0.25, 0.30]),
            )

        # Check: inverted bounds must raise ValueError
        with self.assertRaises(ValueError):
            DomainInput(
                soil_state=np.array([[0.25, 0.30], [0.20, 0.30]]),
                bounds=(100.0, 50.0, 50.0, 40.0),  # min > max
            )

        # Check: negative dry density must raise ValueError
        with self.assertRaises(ValueError):
            DomainInput(
                soil_state=np.array([[0.25, 0.30], [0.20, 0.30]]),
                dry_density_g_cm3=-1.5,
            )

    def test_07_semantic_gate_blocks_latent_representations_and_water_flux(self):
        """[Translators] Verify DomainIntegrationRouter semantic gate traps non-moisture variables."""
        router = DomainIntegrationRouter()

        # 1. Latent features from encoder must be blocked
        latent_payload = {"latent_representation": np.ones((2, 16, 16, 16))}
        ag_res = router.route("backbone", latent_payload, domain="agriculture")
        self.assertEqual(ag_res.status, "BLOCKED")
        self.assertIn("Latent-to-physical conversion blocked", ag_res.message)

        # 2. Water flux must be blocked from soil moisture translation
        flux_payload = {"water_flux": np.full((16, 16), 0.05)}
        civ_res = router.route("physics", flux_payload, domain="civil")
        self.assertEqual(civ_res.status, "BLOCKED")
        self.assertIn("hydraulic gradient flux divergence", civ_res.blocked_reason)

    def test_08_domain_translators_physical_derivation_and_honesty(self):
        """[Translators] Verify Agronomy and Civil translators enforce honest output limitations."""
        valid_input = DomainInput(
            soil_state=np.array([[0.25, 0.30], [0.28, 0.35]]),
            state_variable="volumetric_soil_moisture",
            unit="m3/m3",
            valid_data_mask=np.ones((2, 2), dtype=bool),
            provenance={"source": "Satellite EnKF Estimator"},
        )

        # Agronomy Translator Direct Execution
        ag_translator = AgronomyHealthTranslator()
        ag_out = ag_translator.translate(soil_input=valid_input)
        self.assertIn("mean_moisture_m3m3", ag_out.metrics)
        self.assertIn("irrigation_required_l_ha", ag_out.metrics)
        self.assertIsNone(ag_out.metrics.get("nitrogen_kg_ha"))
        self.assertIsNone(ag_out.metrics.get("phosphorus_kg_ha"))

        # Civil Translator Direct Execution
        civ_translator = CivilLoadTranslator()
        civ_out = civ_translator.translate(soil_input=valid_input, dry_density_g_cm3=1.6)
        self.assertIn("bearing_capacity_matrix_kPa", civ_out.metrics)
        self.assertIn("mean_bearing_kPa", civ_out.metrics)
        self.assertNotIn("factor_of_safety", civ_out.metrics)
        self.assertNotIn("california_bearing_ratio", civ_out.metrics)
        self.assertTrue(any("Factor of Safety" in w for w in civ_out.warnings))

    # =======================================================================
    # PHASE 4: DASHBOARD & TELEMETRY CONTRACT (6_dashboard)
    # =======================================================================

    def test_09_dashboard_metric_contract_and_demo_isolation(self):
        """[Dashboard] Verify DashboardMetric and SpatialLayerMetadata prevent fake LIVE claims."""
        # Metric with out-of-bounds moisture forced to ERROR
        metric = DashboardMetric(
            metric_id="root_zone_moisture",
            label="Root-Zone Moisture",
            value=1.5,
            unit="m³/m³",
            data_state=DataState.LIVE,
            provenance="Validation Test",
            is_valid=False,
        )
        self.assertFalse(metric.is_available, "Invalid metric cannot be available")

        # SpatialLayerMetadata prohibits LIVE state when provenance contains 'demo'
        with self.assertRaises(ValueError):
            SpatialLayerMetadata(
                layer_id="test_leakage",
                layer_type="soil_moisture_raster",
                crs="EPSG:4326",
                extent_bbox=[85.75, 20.20, 85.90, 20.35],
                data_state=DataState.LIVE,
                provenance="Synthetic Demonstration Scaffolding",
            )

        # Empty CRS must be rejected
        with self.assertRaises(ValueError):
            SpatialLayerMetadata(
                layer_id="test_crs",
                layer_type="spatial_grid_mesh",
                crs="",  # Empty
                extent_bbox=[85.75, 20.20, 85.90, 20.35],
                data_state=DataState.DEMO,
                provenance="Mesh Generator",
            )

        # Inverted bounding box must be rejected
        with self.assertRaises(ValueError):
            SpatialLayerMetadata(
                layer_id="test_bbox",
                layer_type="spatial_grid_mesh",
                crs="EPSG:4326",
                extent_bbox=[85.90, 20.35, 85.75, 20.20],  # Inverted min > max
                data_state=DataState.DEMO,
                provenance="Mesh Generator",
            )

    def test_10_map_renderer_distinguishes_geometry_from_measurement(self):
        """[Dashboard] Verify GISMapRenderer strictly separates geometry-only mesh from moisture choropleth."""
        renderer = GISMapRenderer()
        f_map = folium.Map(location=[20.2961, 85.8245])

        geom_only_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"tile_id": "T01", "row": 0, "col": 0},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[85.75, 20.20], [85.80, 20.20], [85.80, 20.25], [85.75, 20.25], [85.75, 20.20]]],
                    },
                }
            ],
        }

        renderer.add_soil_moisture_heatmap_overlay(f_map, geom_only_data)
        child_names = [child.layer_name for child in f_map._children.values() if hasattr(child, "layer_name")]
        self.assertTrue(
            any("Geometry Only" in name for name in child_names),
            "Unmeasured tiles must be visibly tagged as Geometry Only"
        )

        empty_data = {"type": "FeatureCollection", "features": [], "properties": {"message": "No data"}}
        renderer.add_soil_moisture_heatmap_overlay(f_map, empty_data)

    def test_11_rest_api_endpoints_scientific_integrity_and_demo_gates(self):
        """[Dashboard API] Verify FastAPI endpoints strictly enforce health, status, and prediction gates."""
        # 1. Health Endpoint
        res_health = self.api_client.get("/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json().get("status"), "HEALTHY")

        # 2. V1 Status Endpoint
        res_v1 = self.api_client.get("/api/v1/status")
        self.assertEqual(res_v1.status_code, 200)
        self.assertEqual(res_v1.json().get("status"), "ONLINE")

        # 3. Predict Endpoint: Live unverified request must return HTTP 503 UNAVAILABLE
        payload_live = {
            "latitude": 20.2961,
            "longitude": 85.8245,
            "depth_profile_cm": [5.0, 15.0, 30.0, 60.0, 100.0],
            "allow_demo": False,
        }
        res_pred_live = self.api_client.post("/api/v1/predict", json=payload_live)
        self.assertEqual(res_pred_live.status_code, 503)
        self.assertEqual(res_pred_live.json().get("detail", {}).get("status"), "UNAVAILABLE")

        # 4. Predict Endpoint: Explicit allow_demo returns HTTP 200 DEMO
        payload_demo = dict(payload_live, allow_demo=True)
        res_pred_demo = self.api_client.post("/api/v1/predict", json=payload_demo)
        self.assertEqual(res_pred_demo.status_code, 200)
        self.assertEqual(res_pred_demo.json().get("status"), "DEMO")
        self.assertIn("DEMO DATA", res_pred_demo.json().get("message", ""))

        # 5. GIS Layer Endpoint: Generates 16 tiles for 4x4 mesh
        res_gis = self.api_client.get("/api/v1/gis/layer?layer_type=spatial_grid_mesh&grid_rows=4&grid_cols=4")
        self.assertEqual(res_gis.status_code, 200)
        self.assertEqual(len(res_gis.json()["geojson_data"]["features"]), 16)

    # =======================================================================
    # PHASE 5: GRAND END-TO-END CROSS-MODULE PIPELINE AUDIT
    # =======================================================================

    def test_12_grand_unbroken_pipeline_data_flow(self):
        """[Grand E2E] Execute full pipeline journey: Pipeline -> Core Physics -> Translator -> Dashboard."""
        print("\n" + "=" * 70)
        print(" [**] EXECUTING GRAND END-TO-END UNBROKEN PIPELINE AUDIT ")
        print("=" * 70)

        # Step 1: Spatial Grid Tiling (Pipeline)
        bbox = [85.75, 20.20, 85.90, 20.35]
        tiler = GeospatialGridTiler()
        subgrid_tiles = tiler.create_spatial_subgrids(bbox, rows=2, cols=2)
        self.assertEqual(len(subgrid_tiles), 4)
        print("  [OK] Step 1 [Pipeline]: Generated 4 Spatial Subgrid Tiles (EPSG:4326)")

        # Step 2: Observation Assimilation via EnKF (Core Engine)
        enkf = EnsembleKalmanFilterEngine(num_ensembles=10, obs_noise_std=0.03)
        rng = np.random.default_rng(42)
        n_state = 4
        prior_ens = rng.uniform(0.22, 0.32, size=(n_state, 10)).astype(np.float32)
        sat_obs = np.array([0.26, 0.29, 0.24, 0.31], dtype=np.float32)

        assim_res = enkf.assimilate_observations(prior_ens, sat_obs, rng=rng)
        assimilated_moisture = assim_res["posterior_soil_state"].reshape(2, 2)
        self.assertEqual(assimilated_moisture.shape, (2, 2))
        self.assertTrue(np.all((assimilated_moisture >= 0.0) & (assimilated_moisture <= 1.0)))
        print(f"  [OK] Step 2 [Core Engine]: EnKF Assimilated 2x2 grid -> Mean: {assimilated_moisture.mean():.3f} m3/m3")

        # Step 3: Domain Integration Router EnKF Integration
        router = DomainIntegrationRouter()
        enkf_payload = {
            "posterior_soil_state": assimilated_moisture,
            "uncertainty_variance": 0.0009,
        }
        ag_result = router.integrate_enkf_state(enkf_payload, domain="agriculture")
        civ_result = router.integrate_enkf_state(enkf_payload, domain="civil", dry_density_g_cm3=1.6)

        self.assertEqual(ag_result.status, "SUCCESS")
        self.assertEqual(civ_result.status, "SUCCESS")

        ag_output = ag_result.domain_output
        civ_output = civ_result.domain_output

        mean_ag_moisture = ag_output.metrics["mean_moisture_m3m3"]
        bearing_cap = civ_output.metrics["mean_bearing_kPa"]
        print(f"  [OK] Step 3 & 4 [Translators]: Agronomy Moisture: {mean_ag_moisture:.3f} | Civil Bearing: {bearing_cap:.1f} kPa")

        # Step 5: Dashboard Metric Normalization (Dashboard)
        ag_dashboard_metrics = build_agronomy_metrics(agronomy_output=ag_output)
        civ_dashboard_metrics = build_civil_metrics(civil_output=civ_output)

        self.assertEqual(ag_dashboard_metrics["root_zone_moisture"].unit, "m³/m³")
        self.assertEqual(civ_dashboard_metrics["dry_bulk_density"].unit, "g/cm³")
        self.assertEqual(civ_dashboard_metrics["factor_of_safety"].data_state, DataState.UNAVAILABLE)
        self.assertIsNone(civ_dashboard_metrics["factor_of_safety"].value)
        print("  [OK] Step 5 [Dashboard Metrics]: Verified Units, Conversion & Strictly UNAVAILABLE Safety Metrics")

        # Step 6: Map & Chart Visualization Rendering Integrity
        chart_fig = plot_moisture_depth_profile([5, 15, 30, 60, 100], [0.22, 0.26, 0.29, 0.32, 0.34], is_demo=True)
        self.assertIn("DEMO DATA", chart_fig.layout.title.text)

        map_interaction = render_heatmap_folium_map(
            lat=20.2961, lon=85.8245,
            geojson_data=tiler.export_tiles_to_geojson(subgrid_tiles),
            domain_mode="agronomy",
            is_demo=True,
        )
        self.assertIsInstance(map_interaction, dict)
        self.assertIn("last_clicked", map_interaction)
        print("  [OK] Step 6 [Renderers]: Folium Map Canvas & Plotly Depth Profile Verified")

        # Step 7: REST API Scaffolding Verification
        res = self.api_client.post("/api/v1/predict", json={
            "latitude": 20.2961,
            "longitude": 85.8245,
            "allow_demo": True,
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "DEMO")
        print("  [OK] Step 7 [REST API]: Telemetry & Physics REST Ingress Verified")

        print("=" * 70)
        print(" [OK] GRAND END-TO-END PIPELINE AUDIT PASSED: ZERO BREACHES DETECTED ")
        print("=" * 70)


if __name__ == "__main__":
    unittest.main()
