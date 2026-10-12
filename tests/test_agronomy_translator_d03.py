"""
Task 03 — Agriculture Health Translator Hardening & Mask Validation Tests
========================================================================
Tests the hardened AgronomyHealthTranslator implementation in:
  4_domain_translators/agronomy_translator.py

Verifies:
  1. Valid DomainInput accepted with correct declared variable and units.
  2. Legacy array-based call remains compatible for documented valid inputs.
  3. Unsupported state variable or unit is rejected clearly.
  4. Missing NDVI does not trigger a fabricated default (omits crop_health_matrix).
  5. NDVI shape mismatch is rejected.
  6. Mask dtype and shape validation.
  7. Masked NaNs do not contaminate valid-pixel calculations.
  8. All-invalid mask is rejected.
  9. Invalid pixels do not affect aggregate means or classifications.
 10. Valid-pixel outputs are finite.
 11. Geospatial metadata and provenance are preserved.
 12. Warnings distinguish heuristic outputs from validated scientific measurements.
 13. Uncertainty semantics:
     a) Absent uncertainty remains None.
     b) Supported uncertainty preserves input_soil_state_uncertainty and type.
     c) Unspecified uncertainty type records 'unspecified' with warning.
     d) No false claim of downstream crop-health or irrigation uncertainty.
 14. Output uses DomainOutput and preserves documented legacy metric access.
 15. Broad sanity bounds: [0.0, 1.0] m3/m3 enforces numerical plausibility;
     out-of-bound values (< 0.0 or > 1.0) are rejected.
 16. Conflicting arguments are rejected.
 17. Finding A: Deterministic irrigation unit-conversion regression test.
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
from agronomy_translator import (
    AgronomyHealthTranslator,
    LITERS_PER_HA_PER_UNIT_DEFICIT,
    ASSUMED_ROOT_ZONE_DEPTH_M,
    DEFAULT_TARGET_MOISTURE_M3M3,
)


class TestAgronomyTranslatorD03(unittest.TestCase):

    def setUp(self):
        np.random.seed(42)
        self.translator = AgronomyHealthTranslator()
        # Small deterministic test arrays
        self.valid_moisture = np.array([
            [0.18, 0.22, 0.26],
            [0.30, 0.32, 0.34],
            [0.36, 0.38, 0.40],
        ], dtype=np.float32)

        self.valid_ndvi = np.array([
            [0.45, 0.50, 0.55],
            [0.60, 0.65, 0.70],
            [0.72, 0.75, 0.78],
        ], dtype=np.float32)

    # ─── 1. Valid DomainInput accepted ─────────────────────────────────────────
    def test_t01_valid_domain_input_accepted(self):
        """Standardized DomainInput with volumetric_soil_moisture and m3/m3 executes cleanly."""
        inp = DomainInput(
            soil_state=self.valid_moisture,
            state_variable="volumetric_soil_moisture",
            unit="m3/m3",
            ndvi=self.valid_ndvi,
        )
        out = self.translator.translate(inp)

        self.assertIsInstance(out, DomainOutput)
        self.assertEqual(out.domain, "agriculture")
        self.assertIn("crop_health_matrix", out.metrics)
        self.assertIn("irrigation_required_l_ha", out.metrics)
        self.assertIn("drought_risk_status", out.metrics)
        self.assertEqual(out["crop_health_matrix"].shape, (3, 3))

    # ─── 2. Legacy array-based call compatible ─────────────────────────────────
    def test_t02_legacy_array_call_compatible(self):
        """Legacy positional and keyword invocations remain functional."""
        # Positional
        res_pos = self.translator.translate(self.valid_moisture, self.valid_ndvi)
        self.assertIsInstance(res_pos, DomainOutput)
        self.assertEqual(res_pos.domain, "agriculture")
        self.assertIsNotNone(res_pos["crop_health_matrix"])

        # Keyword
        res_kw = self.translator.translate(
            soil_moisture=self.valid_moisture, ndvi=self.valid_ndvi
        )
        self.assertIsInstance(res_kw, DomainOutput)
        self.assertEqual(res_kw["drought_risk_status"], res_pos["drought_risk_status"])

    # ─── 3. Unsupported variable or unit rejected ──────────────────────────────
    def test_t03_unsupported_state_variable_or_unit_rejected(self):
        """Non-moisture state variables or incorrect units raise ValueError."""
        # Unsupported state variable (e.g., geotechnical shear strength)
        bad_var = DomainInput(
            soil_state=self.valid_moisture,
            state_variable="cohesion_shear_strength",
            unit="kPa",
        )
        with self.assertRaises(ValueError) as ctx:
            self.translator.translate(bad_var)
        self.assertIn("Unsupported state variable", str(ctx.exception))

        # Unsupported unit (e.g., percentage instead of volumetric fraction)
        bad_unit = DomainInput(
            soil_state=self.valid_moisture,
            state_variable="volumetric_soil_moisture",
            unit="percent",
        )
        with self.assertRaises(ValueError) as ctx:
            self.translator.translate(bad_unit)
        self.assertIn("Unsupported unit", str(ctx.exception))

    # ─── 4. Missing NDVI does not fabricate defaults ───────────────────────────
    def test_t04_missing_ndvi_omits_health_score_no_fabricated_default(self):
        """When NDVI is None, crop_health_matrix is set to None and documented with a warning."""
        inp = DomainInput(soil_state=self.valid_moisture, ndvi=None)
        out = self.translator.translate(inp)

        self.assertIsNone(out["crop_health_matrix"])
        self.assertIsNone(out["mean_health_score"])
        # Irrigation and drought risk still computed
        self.assertIsNotNone(out["irrigation_required_l_ha"])
        self.assertIsNotNone(out["drought_risk_status"])

        # Verify warning documents missing NDVI
        warning_texts = " ".join(out.warnings)
        self.assertIn("NDVI was not supplied", warning_texts)
        self.assertIn("no fabricated default", warning_texts)

    # ─── 5. NDVI shape mismatch is rejected ────────────────────────────────────
    def test_t05_ndvi_shape_mismatch_rejected(self):
        """Mismatched NDVI spatial dimensions raise ValueError."""
        bad_ndvi = np.ones((5, 5), dtype=np.float32)
        with self.assertRaises(ValueError):
            self.translator.translate(self.valid_moisture, ndvi=bad_ndvi)

    # ─── 6. Mask dtype and shape validation ────────────────────────────────────
    def test_t06_mask_dtype_and_shape_validation(self):
        """Invalid mask shape or non-boolean dtype raises ValueError."""
        bad_shape_mask = np.ones((5, 5), dtype=bool)
        with self.assertRaises(ValueError):
            DomainInput(soil_state=self.valid_moisture, valid_data_mask=bad_shape_mask)

        float_mask = np.ones((3, 3), dtype=np.float32)
        with self.assertRaises(ValueError):
            DomainInput(soil_state=self.valid_moisture, valid_data_mask=float_mask)

    # ─── 7. Masked NaNs do not contaminate calculations ────────────────────────
    def test_t07_masked_nans_do_not_contaminate_calculations(self):
        """NaN values at masked invalid pixels do not result in NaN outputs or contaminated aggregates."""
        moisture_with_nan = self.valid_moisture.copy()
        moisture_with_nan[0, 0] = np.nan
        moisture_with_nan[1, 1] = np.nan

        mask = np.ones((3, 3), dtype=bool)
        mask[0, 0] = False
        mask[1, 1] = False

        ndvi_with_nan = self.valid_ndvi.copy()
        ndvi_with_nan[0, 0] = np.nan
        ndvi_with_nan[1, 1] = np.nan

        inp = DomainInput(
            soil_state=moisture_with_nan,
            valid_data_mask=mask,
            ndvi=ndvi_with_nan,
        )
        out = self.translator.translate(inp)

        # Regional mean aggregates must be strictly finite
        self.assertTrue(math.isfinite(out["mean_moisture_m3m3"]))
        self.assertTrue(math.isfinite(out["mean_irrigation_l_ha"]))
        self.assertTrue(math.isfinite(out["mean_health_score"]))

        # Output rasters should have NaNs at invalid locations, and valid numbers at valid locations
        irr_raster = out["irrigation_required_l_ha"]
        self.assertTrue(np.isnan(irr_raster[0, 0]))
        self.assertTrue(np.isnan(irr_raster[1, 1]))
        self.assertTrue(np.isfinite(irr_raster[0, 1]))

        health_raster = out["crop_health_matrix"]
        self.assertTrue(np.isnan(health_raster[0, 0]))
        self.assertTrue(np.isfinite(health_raster[0, 1]))

    # ─── 8. All-invalid mask is rejected ───────────────────────────────────────
    def test_t08_all_invalid_mask_rejected(self):
        """A mask with 100% False entries is rejected with ValueError."""
        empty_mask = np.zeros((3, 3), dtype=bool)
        inp = DomainInput(
            soil_state=self.valid_moisture,
            valid_data_mask=empty_mask,
        )
        with self.assertRaises(ValueError) as ctx:
            self.translator.translate(inp)
        self.assertIn("0 valid pixels", str(ctx.exception))

    # ─── 9. Invalid pixels do not affect aggregates ───────────────────────────
    def test_t09_invalid_pixels_do_not_affect_aggregates_or_classifications(self):
        """Extreme values in masked pixels do not bias spatial means or classifications."""
        moisture_clean = np.full((4, 4), 0.30, dtype=np.float32)  # OPTIMAL_HYDRATION
        mask = np.ones((4, 4), dtype=bool)

        # Baseline clean run
        out_clean = self.translator.translate(
            DomainInput(soil_state=moisture_clean, valid_data_mask=mask)
        )
        self.assertEqual(out_clean["drought_risk_status"], "OPTIMAL_HYDRATION")
        self.assertAlmostEqual(out_clean["mean_moisture_m3m3"], 0.30, places=4)

        # Now set corner pixels to extreme drought (0.01) but MASK them out
        moisture_corrupted = moisture_clean.copy()
        moisture_corrupted[0, 0] = 0.01
        moisture_corrupted[0, 1] = 0.01
        mask[0, 0] = False
        mask[0, 1] = False

        out_masked = self.translator.translate(
            DomainInput(soil_state=moisture_corrupted, valid_data_mask=mask)
        )
        # Spatial mean and risk classification must remain EXACTLY identical
        self.assertEqual(out_masked["drought_risk_status"], "OPTIMAL_HYDRATION")
        self.assertAlmostEqual(out_masked["mean_moisture_m3m3"], 0.30, places=4)

    # ─── 10. Valid-pixel outputs are finite ────────────────────────────────────
    def test_t10_valid_pixel_outputs_are_finite(self):
        """All computed values on valid pixels are finite floats."""
        out = self.translator.translate(self.valid_moisture, self.valid_ndvi)
        health = out["crop_health_matrix"]
        irrigation = out["irrigation_required_l_ha"]

        self.assertTrue(np.isfinite(health).all())
        self.assertTrue(np.isfinite(irrigation).all())
        self.assertTrue((health >= 0.0).all() and (health <= 100.0).all())
        self.assertTrue((irrigation >= 0.0).all())

    # ─── 11. Geospatial metadata and provenance preserved ─────────────────────
    def test_t11_geospatial_metadata_and_provenance_preserved(self):
        """CRS, transform, bounds, resolution, and provenance survive translation intact."""
        transform = (10.0, 0.0, 300000.0, 0.0, -10.0, 4000000.0)
        bounds = (300000.0, 3999900.0, 300100.0, 4000000.0)
        prov = {"sensor": "Sentinel-1/2", "scene": "S2A_TEST"}

        inp = DomainInput(
            soil_state=self.valid_moisture,
            crs="EPSG:32645",
            transform=transform,
            bounds=bounds,
            resolution=(10.0, 10.0),
            acquisition_datetime="2026-10-09T00:00:00Z",
            provenance=prov,
        )
        out = self.translator.translate(inp)

        self.assertEqual(out.metadata.get("crs"), "EPSG:32645")
        self.assertEqual(out.metadata.get("transform"), transform)
        self.assertEqual(out.metadata.get("bounds"), bounds)
        self.assertEqual(out.metadata.get("resolution"), (10.0, 10.0))
        self.assertEqual(out.metadata.get("provenance"), prov)
        self.assertEqual(out.metadata.get("acquisition_datetime"), "2026-10-09T00:00:00Z")

    # ─── 12. Warnings distinguish heuristic from validated ─────────────────────
    def test_t12_warnings_document_heuristic_limitations(self):
        """Output contains explicit notices on uncalibrated heuristic models."""
        out = self.translator.translate(self.valid_moisture, self.valid_ndvi)
        self.assertTrue(len(out.warnings) >= 3)
        combined_warnings = " ".join(out.warnings)
        self.assertIn("uncalibrated", combined_warnings)
        self.assertIn("not a validated agronomic prescription", combined_warnings)
        self.assertIn("not a validated physiological plant stress measurement", combined_warnings)

    # ─── 13. Finding B: Uncertainty Semantics Verification ────────────────────
    def test_t13_uncertainty_semantics_and_no_false_labeling(self):
        """
        Verifies:
          1. Absent uncertainty remains None.
          2. Supported uncertainty records input_soil_state_uncertainty and preserves type.
          3. Unspecified uncertainty type records 'unspecified' with a warning.
          4. Output does not label uncertainty as crop health or irrigation uncertainty.
        """
        # Case a: Absent uncertainty
        inp_none = DomainInput(soil_state=self.valid_moisture, uncertainty=None)
        out_none = self.translator.translate(inp_none)
        self.assertIsNone(out_none.uncertainty)

        # Case b: Supported uncertainty with declared type
        inp_supported = DomainInput(
            soil_state=self.valid_moisture,
            uncertainty=0.035,
            uncertainty_type="ensemble_variance",
        )
        out_supported = self.translator.translate(inp_supported)
        self.assertIsNotNone(out_supported.uncertainty)
        self.assertEqual(out_supported.uncertainty["input_soil_state_uncertainty"], 0.035)
        self.assertEqual(out_supported.uncertainty["input_uncertainty_type"], "ensemble_variance")
        self.assertEqual(out_supported.uncertainty["propagation_status"], "unpropagated")
        self.assertNotIn("crop_health_uncertainty", out_supported.uncertainty)
        self.assertNotIn("irrigation_uncertainty", out_supported.uncertainty)

        # Case c: Uncertainty provided without type
        inp_unspecified = DomainInput(
            soil_state=self.valid_moisture,
            uncertainty=0.025,
            uncertainty_type=None,
        )
        out_unspecified = self.translator.translate(inp_unspecified)
        self.assertIsNotNone(out_unspecified.uncertainty)
        self.assertEqual(out_unspecified.uncertainty["input_uncertainty_type"], "unspecified")
        combined_warnings = " ".join(out_unspecified.warnings)
        self.assertIn("uncertainty_type", combined_warnings)

    # ─── 14. DomainOutput preserves legacy dict access ────────────────────────
    def test_t14_domain_output_preserves_legacy_dict_access(self):
        """Callers using dict indexing res['key'] or res.get('key') work seamlessly."""
        res = self.translator.translate(self.valid_moisture, self.valid_ndvi)
        self.assertEqual(res["drought_risk_status"], "OPTIMAL_HYDRATION")
        self.assertIn("irrigation_required_l_ha", res)
        self.assertIsNotNone(res.get("crop_health_matrix"))
        self.assertIsNone(res.get("nonexistent_metric"))

    # ─── 15. Finding C: Broad Sanity Bounds Documentation & Range Checks ──────
    def test_t15_broad_sanity_bounds_enforced(self):
        """
        Values outside [0.0, 1.0] m3/m3 are rejected as physical sanity violations,
        with error message documenting broad sanity bounds (not soil-specific porosity).
        """
        # Negative moisture
        bad_negative = self.valid_moisture.copy()
        bad_negative[0, 0] = -0.05
        with self.assertRaises(ValueError) as ctx:
            self.translator.translate(bad_negative)
        self.assertIn("broad physical sanity bounds [0.0, 1.0]", str(ctx.exception))
        self.assertIn("soil-specific porosity is not validated", str(ctx.exception))

        # Moisture > 1.0
        bad_high = self.valid_moisture.copy()
        bad_high[0, 0] = 1.25
        with self.assertRaises(ValueError) as ctx:
            self.translator.translate(bad_high)
        self.assertIn("broad physical sanity bounds [0.0, 1.0]", str(ctx.exception))

    # ─── 16. Conflicting arguments rejected ───────────────────────────────────
    def test_t16_conflicting_arguments_rejected(self):
        """Providing both DomainInput and soil_moisture raises ValueError."""
        inp = DomainInput(soil_state=self.valid_moisture)
        with self.assertRaises(ValueError):
            self.translator.translate(soil_input=inp, soil_moisture=self.valid_moisture)

    # ─── 17. Finding A: Deterministic Irrigation Unit-Conversion Test ──────────
    def test_t17_deterministic_irrigation_unit_conversion(self):
        """
        Deterministic unit-conversion regression test for irrigation calculation:
          Deficit: target - theta = 0.35 - 0.25 = 0.10 m3/m3
          Assumed root zone: 0.10 m
          Area: 1 ha = 10,000 m2
          Theoretical soil volume: 10,000 m2 * 0.10 m = 1,000 m3
          Water volume: 0.10 * 1,000 m3 = 100 m3
          Liters: 100 m3 * 1,000 L/m3 = 100,000 L/ha
          Multiplier: 10,000 * 0.10 * 1,000 = 1,000,000 L/ha per unit deficit
        """
        # 1. Verify constant definition
        expected_multiplier = 10000.0 * ASSUMED_ROOT_ZONE_DEPTH_M * 1000.0
        self.assertEqual(LITERS_PER_HA_PER_UNIT_DEFICIT, expected_multiplier)
        self.assertEqual(LITERS_PER_HA_PER_UNIT_DEFICIT, 1_000_000.0)

        # 2. Test exact numerical conversion with uniform moisture = 0.25
        uniform_moisture = np.full((2, 2), 0.25, dtype=np.float32)
        out = self.translator.translate(uniform_moisture)

        # Deficit = 0.35 - 0.25 = 0.10
        # Expected irrigation = 0.10 * 1,000,000 = 100,000 L/ha
        expected_irrigation = (0.35 - 0.25) * 1_000_000.0
        irr_raster = out["irrigation_required_l_ha"]
        np.testing.assert_allclose(irr_raster, expected_irrigation, rtol=1e-5)
        self.assertAlmostEqual(out["mean_irrigation_l_ha"], 100_000.0, places=1)

        # 3. Test moisture >= target (e.g. 0.35 or 0.40) yields exactly 0.0 deficit
        saturated_moisture = np.full((2, 2), 0.40, dtype=np.float32)
        out_sat = self.translator.translate(saturated_moisture)
        np.testing.assert_allclose(out_sat["irrigation_required_l_ha"], 0.0)
        self.assertEqual(out_sat["mean_irrigation_l_ha"], 0.0)


if __name__ == "__main__":
    unittest.main()
