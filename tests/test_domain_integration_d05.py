"""
Task 05 — Core / Pipeline Integration & Uncertainty Propagation Tests
======================================================================
Tests the integration boundary in:
  4_domain_translators/domain_integrator.py

Verifies:
   1. Compatible, explicitly declared soil-moisture input reaches the appropriate translator.
   2. Latent or semantically unknown core outputs are rejected or marked blocked.
   3. Unsupported units are rejected.
   4. Shape mismatches fail explicitly.
   5. Validity masks preserve invalid pixels through integration.
   6. All-invalid inputs fail safely.
   7. Missing geospatial metadata remains missing rather than fabricated.
   8. Available CRS, transform, bounds, time, and provenance are preserved.
   9. Variance is not silently treated as standard deviation.
  10. Scalar uncertainty is not silently expanded into a calibrated uncertainty raster.
  11. Unknown uncertainty semantics remain explicit.
  12. Input uncertainty is not mislabeled as downstream metric uncertainty.
  13. Translator exceptions are surfaced or wrapped with meaningful context.
  14. Agriculture and Civil routes invoke only their intended translator.
  15. Legacy translator behavior remains compatible where the integration uses it.
  16. Repeated deterministic inputs produce deterministic integration behavior.
  17. No fallback path silently inserts fabricated soil moisture, NDVI, or geotechnical parameters.
  18. Physics flux divergence outputs are blocked by the semantic gate.
"""

import math
import os
import sys
import unittest
import numpy as np

# Establish package root
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_TRANSLATORS_DIR = os.path.join(_REPO_ROOT, "4_domain_translators")

for _p in (_REPO_ROOT, _TRANSLATORS_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from base import DomainInput, DomainOutput
from agronomy_translator import AgronomyHealthTranslator
from civil_translator import CivilLoadTranslator
from domain_integrator import (
    DomainIntegrationRouter,
    IntegrationResult,
    IntegrationBlockedError,
    IntegrationValidationError,
)


class TestDomainIntegrationD05(unittest.TestCase):

    def setUp(self):
        np.random.seed(42)
        self.router = DomainIntegrationRouter()

        # Deterministic mock posterior state (H=4, W=4)
        self.mock_posterior = np.array([
            [0.20, 0.22, 0.24, 0.26],
            [0.28, 0.30, 0.32, 0.34],
            [0.35, 0.36, 0.37, 0.38],
            [0.21, 0.23, 0.25, 0.27],
        ], dtype=np.float32)

        self.mock_enkf_output = {
            "posterior_soil_state": self.mock_posterior,
            "uncertainty_variance": np.float32(0.04),  # variance = 0.04 (std = 0.20)
            "kalman_gain": np.eye(16, dtype=np.float32),
        }

    # ─── 1. Compatible declared soil-moisture reaches translators ─────────────
    def test_t01_compatible_declared_soil_moisture_routes_cleanly(self):
        """Compatible EnKF output routes cleanly to Agriculture and Civil translators."""
        res = self.router.integrate_enkf_state(
            self.mock_enkf_output,
            domain="both",
            state_variable="volumetric_soil_moisture",
            unit="m3/m3",
        )
        self.assertTrue(res.is_success)
        self.assertEqual(res.status, "SUCCESS")
        self.assertIsInstance(res.domain_output, dict)
        self.assertIn("agriculture", res.domain_output)
        self.assertIn("civil", res.domain_output)

        out_agro = res.domain_output["agriculture"]
        out_civil = res.domain_output["civil"]

        self.assertIsInstance(out_agro, DomainOutput)
        self.assertIsInstance(out_civil, DomainOutput)
        self.assertEqual(out_agro.domain, "agriculture")
        self.assertEqual(out_civil.domain, "civil")

    # ─── 2. Latent backbone outputs blocked by semantic gate ──────────────────
    def test_t02_latent_backbone_outputs_blocked_by_semantic_gate(self):
        """Backbone latent features of shape (B, D, H, W) are blocked from being treated as soil moisture."""
        mock_backbone_output = {
            "latent_representation": np.random.randn(1, 64, 4, 4).astype(np.float32),
            "feature_dim": 64,
        }

        # Non-strict mode returns blocked IntegrationResult
        res = self.router.integrate_backbone_latent(mock_backbone_output, strict=False)
        self.assertTrue(res.is_blocked)
        self.assertEqual(res.status, "BLOCKED")
        self.assertIsNone(res.domain_output)
        self.assertIn("latent feature tensor", res.blocked_reason)
        self.assertIn("projection head", res.required_evidence)

        # Strict mode raises IntegrationBlockedError
        with self.assertRaises(IntegrationBlockedError) as ctx:
            self.router.integrate_backbone_latent(mock_backbone_output, strict=True)
        self.assertIn("latent feature tensor", str(ctx.exception))

    # ─── 3. Unsupported units rejected ────────────────────────────────────────
    def test_t03_unsupported_units_rejected(self):
        """Unsupported units (e.g. percentage or pressure) are rejected with clear error."""
        with self.assertRaises(IntegrationValidationError) as ctx:
            self.router.integrate_enkf_state(
                self.mock_enkf_output,
                unit="percent",
                strict=True,
            )
        self.assertIn("Unsupported unit", str(ctx.exception))

        # Non-strict returns REJECTED status
        res = self.router.integrate_enkf_state(
            self.mock_enkf_output,
            unit="kPa",
            strict=False,
        )
        self.assertTrue(res.is_rejected)
        self.assertIn("Unsupported unit", res.message)

    # ─── 4. Shape mismatches fail explicitly ──────────────────────────────────
    def test_t04_shape_mismatches_fail_explicitly(self):
        """Rank-1 or empty state arrays are rejected by the integration layer."""
        bad_enkf = {
            "posterior_soil_state": np.array([0.2, 0.3, 0.4], dtype=np.float32),  # 1-D
            "uncertainty_variance": 0.01,
        }
        with self.assertRaises(IntegrationValidationError) as ctx:
            self.router.integrate_enkf_state(bad_enkf, domain="agriculture")
        self.assertIn("at least 2 spatial dimensions", str(ctx.exception))

    # ─── 5. Validity masks preserve invalid pixels ────────────────────────────
    def test_t05_validity_masks_preserve_invalid_pixels(self):
        """Masked invalid pixels are propagated and isolated with NaNs in translated rasters."""
        mask = np.ones((4, 4), dtype=bool)
        mask[0, 0] = False
        mask[1, 1] = False

        res = self.router.integrate_enkf_state(
            self.mock_enkf_output,
            domain="civil",
            valid_data_mask=mask,
        )
        out_civil = res.domain_output
        self.assertIsInstance(out_civil, DomainOutput)
        self.assertIsNotNone(out_civil.valid_data_mask)
        self.assertFalse(out_civil.valid_data_mask[0, 0])

        bearing_raster = out_civil["bearing_capacity_matrix_kPa"]
        self.assertTrue(np.isnan(bearing_raster[0, 0]))
        self.assertTrue(np.isnan(bearing_raster[1, 1]))
        self.assertTrue(np.isfinite(bearing_raster[0, 1]))

    # ─── 6. All-invalid inputs fail safely ─────────────────────────────────────
    def test_t06_all_invalid_inputs_fail_safely(self):
        """Mask containing 100% False entries fails safely with explicit validation error."""
        all_false_mask = np.zeros((4, 4), dtype=bool)
        with self.assertRaises(IntegrationValidationError) as ctx:
            self.router.integrate_enkf_state(
                self.mock_enkf_output,
                valid_data_mask=all_false_mask,
            )
        self.assertIn("0 valid pixels", str(ctx.exception))

    # ─── 7. Missing geospatial metadata remains missing ───────────────────────
    def test_t07_missing_geospatial_metadata_remains_missing(self):
        """Omitted geospatial metadata remains None; never fabricated as EPSG:4326 or (0,0,0,0)."""
        res = self.router.integrate_enkf_state(
            self.mock_enkf_output,
            domain="agriculture",
            crs=None,
            transform=None,
            bounds=None,
        )
        out = res.domain_output
        self.assertNotIn("crs", out.metadata)
        self.assertNotIn("transform", out.metadata)
        self.assertNotIn("bounds", out.metadata)

    # ─── 8. Available geospatial metadata preserved ───────────────────────────
    def test_t08_available_geospatial_metadata_preserved(self):
        """When CRS, transform, bounds, and provenance are present, they are preserved intact."""
        transform = (10.0, 0.0, 300000.0, 0.0, -10.0, 4000000.0)
        bounds = (300000.0, 3999900.0, 300100.0, 4000000.0)
        prov = {"sensor": "Sentinel-1", "orbit": 45}

        res = self.router.integrate_enkf_state(
            self.mock_enkf_output,
            domain="agriculture",
            crs="EPSG:32645",
            transform=transform,
            bounds=bounds,
            resolution=(10.0, 10.0),
            acquisition_datetime="2026-10-09T00:00:00Z",
            provenance=prov,
        )
        out = res.domain_output
        self.assertEqual(out.metadata["crs"], "EPSG:32645")
        self.assertEqual(out.metadata["transform"], transform)
        self.assertEqual(out.metadata["bounds"], bounds)
        self.assertEqual(out.metadata["resolution"], (10.0, 10.0))
        self.assertEqual(out.metadata["acquisition_datetime"], "2026-10-09T00:00:00Z")
        self.assertEqual(out.metadata["provenance"], prov)

    # ─── 9. Variance not silently treated as std dev ──────────────────────────
    def test_t09_variance_not_silently_treated_as_std_dev(self):
        """EnKF posterior ensemble variance (0.04) is preserved as 0.04, NOT converted to 0.20."""
        res = self.router.integrate_enkf_state(
            self.mock_enkf_output,
            domain="agriculture",
        )
        out = res.domain_output
        self.assertIsNotNone(out.uncertainty)
        # Check numerical value is exactly 0.04 (variance), NOT sqrt(0.04) == 0.2
        self.assertAlmostEqual(out.uncertainty["input_soil_state_uncertainty"], 0.04, places=5)
        self.assertEqual(out.uncertainty["input_uncertainty_type"], "ensemble_variance")

    # ─── 10. Scalar uncertainty not expanded to raster ────────────────────────
    def test_t10_scalar_uncertainty_not_silently_expanded_to_raster(self):
        """Scalar uncertainty remains a scalar float, not a synthesized 2D array."""
        res = self.router.integrate_enkf_state(
            self.mock_enkf_output,
            domain="civil",
        )
        out = res.domain_output
        self.assertIsInstance(out.uncertainty["input_soil_state_uncertainty"], float)
        self.assertNotIsInstance(out.uncertainty["input_soil_state_uncertainty"], np.ndarray)

    # ─── 11. Unknown uncertainty semantics remain explicit ────────────────────
    def test_t11_unknown_uncertainty_semantics_remain_explicit(self):
        """Direct integration with uncertainty but no uncertainty_type records 'unspecified' with warning."""
        res = self.router.integrate_direct_state(
            soil_state=self.mock_posterior,
            domain="civil",
            uncertainty=0.03,
            uncertainty_type=None,
        )
        out = res.domain_output
        self.assertEqual(out.uncertainty["input_uncertainty_type"], "unspecified")
        self.assertTrue(any("uncertainty_type" in w for w in out.warnings))

    # ─── 12. Input uncertainty not mislabeled as downstream metric ────────────
    def test_t12_input_uncertainty_not_mislabeled_as_downstream_metric(self):
        """No false claim of bearing capacity uncertainty or crop health uncertainty."""
        res = self.router.integrate_enkf_state(self.mock_enkf_output, domain="both")
        out_agro = res.domain_output["agriculture"]
        out_civil = res.domain_output["civil"]

        self.assertEqual(out_agro.uncertainty["propagation_status"], "unpropagated")
        self.assertNotIn("crop_health_uncertainty", out_agro.uncertainty)
        self.assertNotIn("irrigation_uncertainty", out_agro.uncertainty)

        self.assertEqual(out_civil.uncertainty["propagation_status"], "unpropagated")
        self.assertNotIn("bearing_capacity_uncertainty", out_civil.uncertainty)
        self.assertNotIn("trafficability_uncertainty", out_civil.uncertainty)

    # ─── 13. Translator exceptions surfaced with context ──────────────────────
    def test_t13_translator_exceptions_surfaced_with_context(self):
        """Broad physical sanity violation (e.g. moisture > 1.0) is trapped and surfaced."""
        bad_moisture = self.mock_posterior.copy()
        bad_moisture[0, 0] = 1.35  # Exceeds broad sanity limit [0.0, 1.0]

        bad_enkf = {
            "posterior_soil_state": bad_moisture,
            "uncertainty_variance": 0.02,
        }
        with self.assertRaises(Exception) as ctx:
            self.router.integrate_enkf_state(bad_enkf, domain="civil")
        self.assertIn("broad physical sanity bounds [0.0, 1.0]", str(ctx.exception))

    # ─── 14. Domain routing invokes only intended translator ──────────────────
    def test_t14_domain_routing_invokes_only_intended_translator(self):
        """Requesting 'agriculture' invokes only agronomy; 'civil' invokes only civil."""
        res_agro = self.router.route("enkf", self.mock_enkf_output, domain="agriculture")
        self.assertEqual(res_agro.domain, "agriculture")
        self.assertEqual(res_agro.domain_output.domain, "agriculture")
        self.assertIn("crop_health_matrix", res_agro.domain_output.metrics)
        self.assertNotIn("bearing_capacity_matrix_kPa", res_agro.domain_output.metrics)

        res_civil = self.router.route("enkf", self.mock_enkf_output, domain="civil")
        self.assertEqual(res_civil.domain, "civil")
        self.assertEqual(res_civil.domain_output.domain, "civil")
        self.assertIn("bearing_capacity_matrix_kPa", res_civil.domain_output.metrics)
        self.assertNotIn("crop_health_matrix", res_civil.domain_output.metrics)

    # ─── 15. Legacy translator dict emulation compatibility ───────────────────
    def test_t15_legacy_translator_dict_emulation_compatibility(self):
        """Integrated outputs support dictionary indexing (__getitem__, .get())."""
        res = self.router.integrate_enkf_state(self.mock_enkf_output, domain="civil")
        out = res.domain_output
        self.assertIn("bearing_capacity_matrix_kPa", out)
        self.assertIsNotNone(out["bearing_capacity_matrix_kPa"])
        self.assertIsNotNone(out.get("site_trafficability"))
        self.assertIsNone(out.get("nonexistent_key"))

    # ─── 16. Repeated deterministic inputs produce deterministic outputs ──────
    def test_t16_repeated_deterministic_inputs_produce_deterministic_outputs(self):
        """Identical inputs yield byte-identical numerical outputs."""
        res1 = self.router.integrate_enkf_state(self.mock_enkf_output, domain="civil")
        res2 = self.router.integrate_enkf_state(self.mock_enkf_output, domain="civil")

        np.testing.assert_array_equal(
            res1.domain_output["bearing_capacity_matrix_kPa"],
            res2.domain_output["bearing_capacity_matrix_kPa"],
        )
        self.assertEqual(
            res1.domain_output["site_trafficability"],
            res2.domain_output["site_trafficability"],
        )

    # ─── 17. No fallback inserts fabricated parameters ────────────────────────
    def test_t17_no_fallback_inserts_fabricated_soil_moisture_or_ndvi(self):
        """Missing NDVI omits crop_health_matrix rather than fabricating a 0.5 default."""
        res = self.router.integrate_enkf_state(
            self.mock_enkf_output,
            domain="agriculture",
            ndvi=None,
        )
        out = res.domain_output
        self.assertIsNone(out["crop_health_matrix"])
        self.assertIsNone(out["mean_health_score"])
        self.assertTrue(any("NDVI was not supplied" in w for w in out.warnings))

    # ─── 18. Physics flux outputs blocked by semantic gate ────────────────────
    def test_t18_physics_flux_outputs_blocked_by_semantic_gate(self):
        """Richards physics engine outputs (cm/day) are blocked by the semantic gate."""
        mock_physics_output = {
            "hydraulic_conductivity": np.full((4, 4), 10.5, dtype=np.float32),
            "water_flux": np.full((4, 4), -0.15, dtype=np.float32),
            "physics_constraint_loss": 0.002,
        }

        # Non-strict mode returns BLOCKED status
        res = self.router.integrate_physics_output(mock_physics_output, strict=False)
        self.assertTrue(res.is_blocked)
        self.assertEqual(res.status, "BLOCKED")
        self.assertIn("water_flux (cm/day)", res.blocked_reason)
        self.assertIn("temporal state-integration solver", res.required_evidence)

        # Strict mode raises IntegrationBlockedError
        with self.assertRaises(IntegrationBlockedError) as ctx:
            self.router.integrate_physics_output(mock_physics_output, strict=True)
        self.assertIn("water_flux (cm/day)", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
