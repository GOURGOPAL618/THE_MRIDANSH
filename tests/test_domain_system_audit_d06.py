"""
Task 06 — Final Verification, System Audit & Adversarial Release Tests
======================================================================
Adversarial test suite verifying the complete domain integration and translator path:
  1. Supported input with explicitly declared semantics.
  2. Unknown variable semantics rejected.
  3. Latent neural state strictly rejected/blocked.
  4. Water flux divergence strictly rejected/blocked.
  5. Incompatible units rejected.
  6. Shape mismatch fails explicitly.
  7. Nonfinite values on unmasked valid pixels rejected.
  8. Invalid pixels and all-invalid masks handled safely.
  9. Missing geospatial metadata remains None (no fabrication).
 10. Uncertainty type ambiguity explicitly recorded as 'unspecified'.
 11. Variance versus standard-deviation handling (no silent conversion).
 12. Translator exceptions propagated with clear context.
 13. Route separation: Agriculture vs Civil domain outputs isolated.
 14. Legacy translator compatibility preserved.
 15. Missing NDVI and density handled transparently without fabricated defaults.
 16. Deterministic repeated executions produce identical outputs.
 17. No fabricated fallback values inserted.
 18. Accurate status reporting (SUCCESS, BLOCKED, REJECTED).
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


class TestDomainSystemAuditD06(unittest.TestCase):

    def setUp(self):
        np.random.seed(42)
        self.router = DomainIntegrationRouter()

        # Deterministic 4x4 test grid
        self.valid_moisture = np.array([
            [0.18, 0.22, 0.26, 0.28],
            [0.30, 0.32, 0.34, 0.35],
            [0.22, 0.25, 0.29, 0.31],
            [0.20, 0.24, 0.27, 0.33],
        ], dtype=np.float32)

        self.valid_enkf_dict = {
            "posterior_soil_state": self.valid_moisture,
            "uncertainty_variance": np.float32(0.04),
            "kalman_gain": np.eye(16, dtype=np.float32),
        }

    # ─── 1. Supported Input with Explicit Semantics ───────────────────────────
    def test_adv_01_supported_input_explicit_semantics(self):
        """Declared volumetric_soil_moisture in m3/m3 routes successfully to both domains."""
        res = self.router.integrate_enkf_state(
            self.valid_enkf_dict,
            domain="both",
            state_variable="volumetric_soil_moisture",
            unit="m3/m3",
        )
        self.assertEqual(res.status, "SUCCESS")
        self.assertTrue(res.is_success)
        self.assertIn("agriculture", res.domain_output)
        self.assertIn("civil", res.domain_output)
        self.assertEqual(res.domain_output["agriculture"].domain, "agriculture")
        self.assertEqual(res.domain_output["civil"].domain, "civil")

    # ─── 2. Unknown Variable Semantics Rejected ───────────────────────────────
    def test_adv_02_unknown_variable_semantics_rejected(self):
        """Variables like 'hydraulic_gradient' or 'electrical_conductivity' are rejected."""
        with self.assertRaises(IntegrationValidationError) as ctx:
            self.router.integrate_enkf_state(
                self.valid_enkf_dict,
                state_variable="hydraulic_gradient",
                strict=True,
            )
        self.assertIn("Unsupported state variable", str(ctx.exception))

    # ─── 3. Latent Neural State Rejection ─────────────────────────────────────
    def test_adv_03_latent_state_rejection(self):
        """Latent features (B, D, H, W) are blocked; strict=True raises IntegrationBlockedError."""
        latent_dict = {
            "latent_representation": np.zeros((1, 128, 4, 4), dtype=np.float32),
            "feature_dim": 128,
        }
        with self.assertRaises(IntegrationBlockedError) as ctx:
            self.router.integrate_backbone_latent(latent_dict, strict=True)
        self.assertIn("latent feature tensor", str(ctx.exception))

    # ─── 4. Water Flux Rejection ──────────────────────────────────────────────
    def test_adv_04_water_flux_rejection(self):
        """Darcy water flux (cm/day) is blocked; strict=True raises IntegrationBlockedError."""
        flux_dict = {
            "water_flux": np.full((4, 4), -0.25, dtype=np.float32),
            "hydraulic_conductivity": np.full((4, 4), 10.5, dtype=np.float32),
        }
        with self.assertRaises(IntegrationBlockedError) as ctx:
            self.router.integrate_physics_output(flux_dict, strict=True)
        self.assertIn("water_flux (cm/day)", str(ctx.exception))

    # ─── 5. Incompatible Units Rejected ───────────────────────────────────────
    def test_adv_05_incompatible_units_rejected(self):
        """Pressure, percentage, or non-volumetric units raise IntegrationValidationError."""
        for bad_unit in ("psi", "bar", "percent", "kPa"):
            with self.assertRaises(IntegrationValidationError):
                self.router.integrate_enkf_state(
                    self.valid_enkf_dict,
                    unit=bad_unit,
                    strict=True,
                )

    # ─── 6. Shape Mismatch Fails Explicitly ───────────────────────────────────
    def test_adv_06_shape_mismatches_fail_explicitly(self):
        """Rank-1 state vectors or rank-4 tensors fail with IntegrationValidationError."""
        bad_shape_dict = {
            "posterior_soil_state": np.ones((16,), dtype=np.float32),  # 1-D vector
            "uncertainty_variance": 0.01,
        }
        with self.assertRaises(IntegrationValidationError) as ctx:
            self.router.integrate_enkf_state(bad_shape_dict, domain="civil")
        self.assertIn("at least 2 spatial dimensions", str(ctx.exception))

    # ─── 7. Nonfinite Valid Pixels Rejected ───────────────────────────────────
    def test_adv_07_nonfinite_valid_pixels_rejected(self):
        """NaN or Inf values on unmasked pixels raise IntegrationValidationError."""
        corrupted_state = self.valid_moisture.copy()
        corrupted_state[1, 1] = np.nan

        bad_dict = {
            "posterior_soil_state": corrupted_state,
            "uncertainty_variance": 0.01,
        }
        with self.assertRaises(IntegrationValidationError) as ctx:
            self.router.integrate_enkf_state(bad_dict, domain="agriculture")
        self.assertIn("non-finite", str(ctx.exception).lower())

    # ─── 8. Invalid Pixels and All-Invalid Masks ──────────────────────────────
    def test_adv_08_invalid_pixels_and_all_invalid_mask(self):
        """
        Masked invalid pixels are filled with NaN in rasters;
        All-invalid mask fails safely with IntegrationValidationError.
        """
        # Partial mask
        partial_mask = np.ones((4, 4), dtype=bool)
        partial_mask[0, 0] = False
        res = self.router.integrate_enkf_state(
            self.valid_enkf_dict, domain="civil", valid_data_mask=partial_mask
        )
        self.assertTrue(np.isnan(res.domain_output["bearing_capacity_matrix_kPa"][0, 0]))
        self.assertTrue(np.isfinite(res.domain_output["bearing_capacity_matrix_kPa"][0, 1]))

        # All-invalid mask
        empty_mask = np.zeros((4, 4), dtype=bool)
        with self.assertRaises(IntegrationValidationError) as ctx:
            self.router.integrate_enkf_state(
                self.valid_enkf_dict, domain="civil", valid_data_mask=empty_mask
            )
        self.assertIn("0 valid pixels", str(ctx.exception))

    # ─── 9. Missing Geospatial Metadata Remains None ──────────────────────────
    def test_adv_09_missing_geospatial_metadata_remains_none(self):
        """When CRS/bounds/transform are not supplied, they are not synthesized."""
        res = self.router.integrate_enkf_state(self.valid_enkf_dict, domain="civil")
        out = res.domain_output
        self.assertNotIn("crs", out.metadata)
        self.assertNotIn("transform", out.metadata)
        self.assertNotIn("bounds", out.metadata)

    # ─── 10. Uncertainty Type Ambiguity Explicitly Documented ─────────────────
    def test_adv_10_uncertainty_type_ambiguity(self):
        """Uncertainty supplied without uncertainty_type records 'unspecified' with warning."""
        res = self.router.integrate_direct_state(
            soil_state=self.valid_moisture,
            domain="agriculture",
            uncertainty=0.03,
            uncertainty_type=None,
        )
        out = res.domain_output
        self.assertEqual(out.uncertainty["input_uncertainty_type"], "unspecified")
        self.assertTrue(any("uncertainty_type" in w for w in out.warnings))

    # ─── 11. Variance vs Standard Deviation Handling ──────────────────────────
    def test_adv_11_variance_vs_std_dev_handling(self):
        """Ensemble variance 0.04 is preserved as 0.04 (not converted to std 0.20)."""
        res = self.router.integrate_enkf_state(self.valid_enkf_dict, domain="agriculture")
        unc = res.domain_output.uncertainty
        self.assertAlmostEqual(unc["input_soil_state_uncertainty"], 0.04, places=5)
        self.assertEqual(unc["input_uncertainty_type"], "ensemble_variance")
        self.assertNotAlmostEqual(unc["input_soil_state_uncertainty"], math.sqrt(0.04), places=5)

    # ─── 12. Translator Exceptions Propagated ─────────────────────────────────
    def test_adv_12_translator_exceptions_propagated(self):
        """Broad sanity violations (> 1.0 m3/m3) surface actionable error message."""
        out_of_bounds_state = self.valid_moisture.copy()
        out_of_bounds_state[0, 0] = 1.25  # Exceeds broad sanity limit [0.0, 1.0]

        bad_dict = {
            "posterior_soil_state": out_of_bounds_state,
            "uncertainty_variance": 0.01,
        }
        with self.assertRaises(IntegrationValidationError) as ctx:
            self.router.integrate_enkf_state(bad_dict, domain="civil")
        self.assertIn("broad physical sanity bounds [0.0, 1.0]", str(ctx.exception))

    # ─── 13. Route Separation: Agriculture vs Civil ───────────────────────────
    def test_adv_13_route_separation_agriculture_vs_civil(self):
        """Agriculture output has no civil keys; Civil output has no agriculture keys."""
        res_agro = self.router.route("enkf", self.valid_enkf_dict, domain="agriculture")
        res_civil = self.router.route("enkf", self.valid_enkf_dict, domain="civil")

        # Agriculture checks
        self.assertIn("irrigation_required_l_ha", res_agro.domain_output.metrics)
        self.assertNotIn("bearing_capacity_matrix_kPa", res_agro.domain_output.metrics)
        self.assertNotIn("site_trafficability", res_agro.domain_output.metrics)

        # Civil checks
        self.assertIn("bearing_capacity_matrix_kPa", res_civil.domain_output.metrics)
        self.assertIn("site_trafficability", res_civil.domain_output.metrics)
        self.assertNotIn("irrigation_required_l_ha", res_civil.domain_output.metrics)
        self.assertNotIn("crop_health_matrix", res_civil.domain_output.metrics)

    # ─── 14. Legacy Translator Compatibility ──────────────────────────────────
    def test_adv_14_legacy_translator_compatibility(self):
        """Legacy dictionary emulation (__getitem__, .get()) works seamlessly."""
        res = self.router.integrate_enkf_state(self.valid_enkf_dict, domain="civil")
        out = res.domain_output
        self.assertIsNotNone(out["bearing_capacity_matrix_kPa"])
        self.assertIsNotNone(out.get("site_trafficability"))
        self.assertIsNone(out.get("nonexistent_metric"))
        self.assertTrue("mean_bearing_kPa" in out)

    # ─── 15. Missing NDVI and Missing Geotechnical Density ────────────────────
    def test_adv_15_missing_ndvi_and_density_handling(self):
        """Missing NDVI omits crop_health_matrix; missing density applies default with warning."""
        res_agro = self.router.integrate_enkf_state(self.valid_enkf_dict, domain="agriculture", ndvi=None)
        self.assertIsNone(res_agro.domain_output["crop_health_matrix"])
        self.assertTrue(any("NDVI was not supplied" in w for w in res_agro.domain_output.warnings))

        res_civil = self.router.integrate_enkf_state(self.valid_enkf_dict, domain="civil", dry_density_g_cm3=None)
        self.assertAlmostEqual(res_civil.domain_output["dry_density_g_cm3"], 1.6)
        self.assertTrue(any("Default dry density" in w for w in res_civil.domain_output.warnings))

    # ─── 16. Deterministic Repeated Executions ────────────────────────────────
    def test_adv_16_deterministic_repeated_executions(self):
        """Repeated executions yield byte-identical numerical matrices."""
        res1 = self.router.integrate_enkf_state(self.valid_enkf_dict, domain="both")
        res2 = self.router.integrate_enkf_state(self.valid_enkf_dict, domain="both")

        np.testing.assert_array_equal(
            res1.domain_output["agriculture"]["irrigation_required_l_ha"],
            res2.domain_output["agriculture"]["irrigation_required_l_ha"],
        )
        np.testing.assert_array_equal(
            res1.domain_output["civil"]["bearing_capacity_matrix_kPa"],
            res2.domain_output["civil"]["bearing_capacity_matrix_kPa"],
        )

    # ─── 17. No Fabricated Fallback Values ─────────────────────────────────────
    def test_adv_17_no_fabricated_fallback_values(self):
        """No synthetic soil moisture is fabricated from missing inputs."""
        empty_dict = {}
        with self.assertRaises(IntegrationValidationError):
            self.router.integrate_enkf_state(empty_dict, domain="agriculture")

    # ─── 18. Accurate Status Reporting ────────────────────────────────────────
    def test_adv_18_accurate_status_reporting(self):
        """Verifies SUCCESS, BLOCKED, and REJECTED status reporting."""
        # Success
        res_ok = self.router.route("enkf", self.valid_enkf_dict, domain="civil")
        self.assertTrue(res_ok.is_success)
        self.assertEqual(res_ok.status, "SUCCESS")

        # Blocked
        res_blocked = self.router.route("backbone", {"latent_representation": np.zeros((1, 64, 4, 4))}, strict=False)
        self.assertTrue(res_blocked.is_blocked)
        self.assertEqual(res_blocked.status, "BLOCKED")
        self.assertIsNotNone(res_blocked.blocked_reason)

        # Rejected
        res_rejected = self.router.integrate_enkf_state(self.valid_enkf_dict, unit="percent", strict=False)
        self.assertTrue(res_rejected.is_rejected)
        self.assertEqual(res_rejected.status, "REJECTED")


if __name__ == "__main__":
    unittest.main()
