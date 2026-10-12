"""
Task 04 — Civil Load Translator Hardening & Geotechnical Parameterization Tests
================================================================================
Tests the hardened CivilLoadTranslator implementation in:
  4_domain_translators/civil_translator.py

Verifies:
   1. Valid DomainInput accepted with correct declared variable and units.
   2. Legacy array-based call remains compatible for documented valid inputs.
   3. Unsupported state variable or unit is rejected clearly.
   4. Dry density validation (positive, finite, numeric).
   5. Broad physical sanity bounds: [0.0, 1.0] m3/m3 enforced; non-plausible values rejected.
   6. Mask dtype and shape validation.
   7. Masked NaNs do not contaminate valid-pixel calculations.
   8. All-invalid mask is rejected.
   9. Invalid pixels do not affect aggregate means or trafficability grade.
  10. Valid-pixel outputs are finite.
  11. Geospatial metadata and provenance are preserved.
  12. Warnings distinguish heuristic models, absence of Factor of Safety (FS), and cohesion limits.
  13. Uncertainty semantics:
      a) Absent uncertainty remains None.
      b) Supported uncertainty preserves input_soil_state_uncertainty and type.
      c) Unspecified uncertainty type records 'unspecified' with warning.
      d) No false claim of bearing capacity or trafficability uncertainty.
  14. Output uses DomainOutput and preserves documented legacy metric access.
  15. Dimensional consistency of surcharge and cohesion reduction.
  16. Absent density uses documented default with parameter notice; atypical density warned.
  17. Conflicting arguments are rejected.
  18. Trafficability threshold classification verification.
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
from civil_translator import (
    CivilLoadTranslator,
    DEFAULT_DRY_DENSITY_G_CM3,
    TYPICAL_MIN_DRY_DENSITY_G_CM3,
    TYPICAL_MAX_DRY_DENSITY_G_CM3,
    REFERENCE_SATURATION_MOISTURE_M3M3,
    BASELINE_COHESION_KPA,
    COHESION_SATURATION_REDUCTION_FACTOR,
    TERZAGHI_NC,
    NOMINAL_FOOTING_DEPTH_M,
    GRAVITY_M_S2,
    SURCHARGE_DEPTH_FACTOR,
    TRAFFICABILITY_HEAVY_RIG_THRESHOLD_KPA,
    TRAFFICABILITY_LIGHT_VEHICLE_THRESHOLD_KPA,
)


class TestCivilTranslatorD04(unittest.TestCase):

    def setUp(self):
        np.random.seed(42)
        self.translator = CivilLoadTranslator()
        # Small deterministic test array (H=3, W=3)
        self.valid_moisture = np.array([
            [0.15, 0.20, 0.25],
            [0.28, 0.30, 0.32],
            [0.35, 0.38, 0.40],
        ], dtype=np.float32)

    # ─── 1. Valid DomainInput accepted ─────────────────────────────────────────
    def test_t01_valid_domain_input_accepted(self):
        """Standardized DomainInput with volumetric_soil_moisture and m3/m3 executes cleanly."""
        inp = DomainInput(
            soil_state=self.valid_moisture,
            state_variable="volumetric_soil_moisture",
            unit="m3/m3",
            dry_density_g_cm3=1.65,
        )
        out = self.translator.translate(inp)

        self.assertIsInstance(out, DomainOutput)
        self.assertEqual(out.domain, "civil")
        self.assertIn("bearing_capacity_matrix_kPa", out.metrics)
        self.assertIn("effective_cohesion_kPa", out.metrics)
        self.assertIn("site_trafficability", out.metrics)
        self.assertIn("mean_bearing_kPa", out.metrics)
        self.assertEqual(out["bearing_capacity_matrix_kPa"].shape, (3, 3))
        self.assertEqual(out["effective_cohesion_kPa"].shape, (3, 3))

    # ─── 2. Legacy array-based call compatible ─────────────────────────────────
    def test_t02_legacy_array_call_compatible(self):
        """Legacy positional and keyword invocations remain functional and return consistent results."""
        # Positional with density
        res_pos = self.translator.translate(self.valid_moisture, 1.7)
        self.assertIsInstance(res_pos, DomainOutput)
        self.assertEqual(res_pos.domain, "civil")
        self.assertAlmostEqual(res_pos["dry_density_g_cm3"], 1.7)

        # Keyword invocation
        res_kw = self.translator.translate(
            soil_moisture=self.valid_moisture, dry_density_g_cm3=1.7
        )
        self.assertIsInstance(res_kw, DomainOutput)
        self.assertEqual(res_kw["site_trafficability"], res_pos["site_trafficability"])
        self.assertAlmostEqual(res_kw["mean_bearing_kPa"], res_pos["mean_bearing_kPa"], places=4)

        # Default density call
        res_default = self.translator.translate(self.valid_moisture)
        self.assertAlmostEqual(res_default["dry_density_g_cm3"], DEFAULT_DRY_DENSITY_G_CM3)

    # ─── 3. Unsupported variable or unit rejected ──────────────────────────────
    def test_t03_unsupported_state_variable_or_unit_rejected(self):
        """Non-moisture state variables or incorrect units raise ValueError."""
        # Unsupported variable
        bad_var = DomainInput(
            soil_state=self.valid_moisture,
            state_variable="unconfined_compressive_strength",
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

    # ─── 4. Dry density validation ─────────────────────────────────────────────
    def test_t04_dry_density_validation(self):
        """Non-numeric, zero, negative, or non-finite dry density raises appropriate errors."""
        # Negative density
        with self.assertRaises(ValueError):
            self.translator.translate(self.valid_moisture, dry_density_g_cm3=-1.2)

        # Zero density
        with self.assertRaises(ValueError):
            self.translator.translate(self.valid_moisture, dry_density_g_cm3=0.0)

        # Non-finite (NaN)
        with self.assertRaises(ValueError):
            self.translator.translate(self.valid_moisture, dry_density_g_cm3=float("nan"))

        # Non-numeric
        with self.assertRaises(TypeError):
            self.translator.translate(self.valid_moisture, dry_density_g_cm3="1.65")  # type: ignore

    # ─── 5. Broad sanity bounds enforced ──────────────────────────────────────
    def test_t05_broad_sanity_bounds_enforced(self):
        """
        Moisture values outside [0.0, 1.0] m3/m3 are rejected as physical sanity violations,
        with error message documenting broad sanity bounds vs soil-specific porosity.
        """
        bad_neg = self.valid_moisture.copy()
        bad_neg[0, 0] = -0.05
        with self.assertRaises(ValueError) as ctx:
            self.translator.translate(bad_neg)
        self.assertIn("broad physical sanity bounds [0.0, 1.0]", str(ctx.exception))
        self.assertIn("soil-specific porosity is not validated", str(ctx.exception))

        bad_high = self.valid_moisture.copy()
        bad_high[0, 0] = 1.15
        with self.assertRaises(ValueError) as ctx:
            self.translator.translate(bad_high)
        self.assertIn("broad physical sanity bounds [0.0, 1.0]", str(ctx.exception))

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
        """NaN values at masked invalid pixels do not contaminate valid pixels or aggregate means."""
        moisture_with_nan = self.valid_moisture.copy()
        moisture_with_nan[0, 0] = np.nan
        moisture_with_nan[1, 1] = np.nan

        mask = np.ones((3, 3), dtype=bool)
        mask[0, 0] = False
        mask[1, 1] = False

        inp = DomainInput(soil_state=moisture_with_nan, valid_data_mask=mask)
        out = self.translator.translate(inp)

        # Aggregates must be strictly finite floats
        self.assertTrue(math.isfinite(out["mean_bearing_kPa"]))
        self.assertTrue(math.isfinite(out["mean_effective_cohesion_kPa"]))

        # Output rasters must have NaNs at invalid locations, and valid values at valid locations
        bearing_raster = out["bearing_capacity_matrix_kPa"]
        cohesion_raster = out["effective_cohesion_kPa"]

        self.assertTrue(np.isnan(bearing_raster[0, 0]))
        self.assertTrue(np.isnan(bearing_raster[1, 1]))
        self.assertTrue(np.isfinite(bearing_raster[0, 1]))

        self.assertTrue(np.isnan(cohesion_raster[0, 0]))
        self.assertTrue(np.isnan(cohesion_raster[1, 1]))
        self.assertTrue(np.isfinite(cohesion_raster[0, 1]))

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
    def test_t09_invalid_pixels_do_not_affect_aggregates_or_trafficability(self):
        """Corrupted values in masked pixels do not bias spatial means or trafficability."""
        moisture_clean = np.full((4, 4), 0.15, dtype=np.float32)  # High bearing -> HEAVY_RIG_PERMITTED
        mask = np.ones((4, 4), dtype=bool)

        out_clean = self.translator.translate(
            DomainInput(soil_state=moisture_clean, valid_data_mask=mask)
        )
        clean_mean = out_clean["mean_bearing_kPa"]
        clean_trafficability = out_clean["site_trafficability"]

        # Corrupt corner pixels with saturated moisture (low bearing capacity) but mask them out
        moisture_corrupted = moisture_clean.copy()
        moisture_corrupted[0, 0] = 0.45
        moisture_corrupted[0, 1] = 0.45
        mask[0, 0] = False
        mask[0, 1] = False

        out_masked = self.translator.translate(
            DomainInput(soil_state=moisture_corrupted, valid_data_mask=mask)
        )

        self.assertEqual(out_masked["site_trafficability"], clean_trafficability)
        self.assertAlmostEqual(out_masked["mean_bearing_kPa"], clean_mean, places=4)

    # ─── 10. Valid-pixel outputs are finite ────────────────────────────────────
    def test_t10_valid_pixel_outputs_are_finite(self):
        """All computed raster values on valid pixels are finite floats."""
        out = self.translator.translate(self.valid_moisture)
        bearing = out["bearing_capacity_matrix_kPa"]
        cohesion = out["effective_cohesion_kPa"]

        self.assertTrue(np.isfinite(bearing).all())
        self.assertTrue(np.isfinite(cohesion).all())
        self.assertTrue((bearing > 0.0).all())
        self.assertTrue((cohesion > 0.0).all())

    # ─── 11. Geospatial metadata and provenance preserved ─────────────────────
    def test_t11_geospatial_metadata_and_provenance_preserved(self):
        """CRS, transform, bounds, resolution, and provenance survive translation intact."""
        transform = (10.0, 0.0, 300000.0, 0.0, -10.0, 4000000.0)
        bounds = (300000.0, 3999900.0, 300100.0, 4000000.0)
        prov = {"sensor": "Sentinel-1/2", "scene": "S2_CIVIL_SITE"}

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

    # ─── 12. Warnings document geotechnical limitations ───────────────────────
    def test_t12_warnings_document_geotechnical_limitations(self):
        """Output contains explicit notices on uncalibrated heuristic models, FS absence, and lithology."""
        out = self.translator.translate(self.valid_moisture)
        self.assertTrue(len(out.warnings) >= 4)
        combined_warnings = " ".join(out.warnings)
        self.assertIn("Terzaghi-like heuristic", combined_warnings)
        self.assertIn("Factor of Safety", combined_warnings)
        self.assertIn("MUST NOT be used for foundation design", combined_warnings)
        self.assertIn("completely invalid for cohesionless", combined_warnings)
        self.assertIn("trafficability", combined_warnings.lower())

    # ─── 13. Uncertainty semantics verification ───────────────────────────────
    def test_t13_uncertainty_semantics_and_no_false_labeling(self):
        """
        Verifies:
          1. Absent uncertainty remains None.
          2. Supported uncertainty preserves input_soil_state_uncertainty and type.
          3. Unspecified uncertainty type records 'unspecified' with warning.
          4. Output does not label uncertainty as bearing capacity or trafficability uncertainty.
        """
        # Case a: Absent uncertainty
        inp_none = DomainInput(soil_state=self.valid_moisture, uncertainty=None)
        out_none = self.translator.translate(inp_none)
        self.assertIsNone(out_none.uncertainty)

        # Case b: Supported uncertainty with declared type
        inp_supported = DomainInput(
            soil_state=self.valid_moisture,
            uncertainty=0.025,
            uncertainty_type="posterior_variance",
        )
        out_supported = self.translator.translate(inp_supported)
        self.assertIsNotNone(out_supported.uncertainty)
        self.assertEqual(out_supported.uncertainty["input_soil_state_uncertainty"], 0.025)
        self.assertEqual(out_supported.uncertainty["input_uncertainty_type"], "posterior_variance")
        self.assertEqual(out_supported.uncertainty["propagation_status"], "unpropagated")
        self.assertNotIn("bearing_capacity_uncertainty", out_supported.uncertainty)
        self.assertNotIn("trafficability_uncertainty", out_supported.uncertainty)

        # Case c: Uncertainty provided without type
        inp_unspecified = DomainInput(
            soil_state=self.valid_moisture,
            uncertainty=0.015,
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
        res = self.translator.translate(self.valid_moisture)
        self.assertIn("bearing_capacity_matrix_kPa", res)
        self.assertIn("effective_cohesion_kPa", res)
        self.assertIn("site_trafficability", res)
        self.assertIn("mean_bearing_kPa", res)
        self.assertIsNotNone(res.get("bearing_capacity_matrix_kPa"))
        self.assertIsNone(res.get("nonexistent_key"))

    # ─── 15. Dimensional consistency of surcharge and cohesion reduction ──────
    def test_t15_dimensional_consistency_of_surcharge_and_cohesion(self):
        """
        Analytical verification of Terzaghi-like formula and surcharge evaluation:
          1. At saturation (theta = 0.45 m3/m3, Sr = 1.0):
             c = 35.0 * (1.0 - 0.6 * 1.0) = 14.0 kPa
             c * Nc = 14.0 * 5.7 = 79.8 kPa
             q = 1.6 * 9.81 * 1.5 = 23.544 kPa
             q_ult = 79.8 + 23.544 = 103.344 kPa
          2. At completely dry condition (theta = 0.0 m3/m3, Sr = 0.0):
             c = 35.0 * 1.0 = 35.0 kPa
             c * Nc = 35.0 * 5.7 = 199.5 kPa
             q = 23.544 kPa
             q_ult = 199.5 + 23.544 = 223.044 kPa
        """
        # Test saturated point
        sat_arr = np.full((2, 2), 0.45, dtype=np.float32)
        out_sat = self.translator.translate(sat_arr, dry_density_g_cm3=1.6)

        expected_c_sat = 14.0
        expected_q = 1.6 * 9.81 * 1.5  # 23.544 kPa
        expected_bearing_sat = expected_c_sat * 5.7 + expected_q  # 103.344 kPa

        np.testing.assert_allclose(out_sat["effective_cohesion_kPa"], expected_c_sat, rtol=1e-5)
        np.testing.assert_allclose(out_sat["bearing_capacity_matrix_kPa"], expected_bearing_sat, rtol=1e-5)
        self.assertAlmostEqual(out_sat["surcharge_kPa"], expected_q, places=3)
        self.assertAlmostEqual(out_sat["mean_bearing_kPa"], expected_bearing_sat, places=3)

        # Test dry point
        dry_arr = np.full((2, 2), 0.0, dtype=np.float32)
        out_dry = self.translator.translate(dry_arr, dry_density_g_cm3=1.6)

        expected_c_dry = 35.0
        expected_bearing_dry = expected_c_dry * 5.7 + expected_q  # 223.044 kPa

        np.testing.assert_allclose(out_dry["effective_cohesion_kPa"], expected_c_dry, rtol=1e-5)
        np.testing.assert_allclose(out_dry["bearing_capacity_matrix_kPa"], expected_bearing_dry, rtol=1e-5)
        self.assertAlmostEqual(out_dry["mean_bearing_kPa"], expected_bearing_dry, places=3)

    # ─── 16. Absent density uses documented default; atypical warned ───────────
    def test_t16_absent_density_uses_documented_default_and_warns_atypical(self):
        """Default dry density 1.60 g/cm3 is applied when omitted, and atypical density is warned."""
        # Omitted density
        out_default = self.translator.translate(self.valid_moisture)
        self.assertEqual(out_default["dry_density_g_cm3"], DEFAULT_DRY_DENSITY_G_CM3)
        self.assertTrue(any("Default dry density" in w for w in out_default.warnings))

        # Atypical high density (e.g., 2.7 g/cm3, typical upper limit is 2.4)
        out_high = self.translator.translate(self.valid_moisture, dry_density_g_cm3=2.7)
        self.assertEqual(out_high["dry_density_g_cm3"], 2.7)
        self.assertTrue(any("typical mineral soil range" in w for w in out_high.warnings))

    # ─── 17. Conflicting arguments rejected ───────────────────────────────────
    def test_t17_conflicting_arguments_rejected(self):
        """Conflicting soil_input and soil_moisture, or conflicting density raises ValueError."""
        inp = DomainInput(soil_state=self.valid_moisture, dry_density_g_cm3=1.6)

        # Both DomainInput and soil_moisture
        with self.assertRaises(ValueError):
            self.translator.translate(soil_input=inp, soil_moisture=self.valid_moisture)

        # Conflicting density in DomainInput and keyword
        with self.assertRaises(ValueError):
            self.translator.translate(soil_input=inp, dry_density_g_cm3=1.8)

        # No input provided
        with self.assertRaises(ValueError):
            self.translator.translate()

    # ─── 18. Trafficability threshold classification ──────────────────────────
    def test_t18_trafficability_threshold_classification(self):
        """
        Verifies classification boundaries:
          > 180.0 kPa -> HEAVY_RIG_PERMITTED
          > 120.0 kPa -> LIGHT_VEHICLE_ONLY
          <= 120.0 kPa -> HAZARDOUS_UNSTABLE_SOIL
        """
        # Dry soil -> bearing ~ 223 kPa -> HEAVY_RIG_PERMITTED
        out_heavy = self.translator.translate(np.full((2, 2), 0.05, dtype=np.float32))
        self.assertGreater(out_heavy["mean_bearing_kPa"], TRAFFICABILITY_HEAVY_RIG_THRESHOLD_KPA)
        self.assertEqual(out_heavy["site_trafficability"], "HEAVY_RIG_PERMITTED")

        # Intermediate moisture -> theta = 0.25 -> bearing ~ 156.5 kPa -> LIGHT_VEHICLE_ONLY
        out_light = self.translator.translate(np.full((2, 2), 0.25, dtype=np.float32))
        self.assertGreater(out_light["mean_bearing_kPa"], TRAFFICABILITY_LIGHT_VEHICLE_THRESHOLD_KPA)
        self.assertLessEqual(out_light["mean_bearing_kPa"], TRAFFICABILITY_HEAVY_RIG_THRESHOLD_KPA)
        self.assertEqual(out_light["site_trafficability"], "LIGHT_VEHICLE_ONLY")

        # Saturated soil -> theta = 0.45 -> bearing ~ 103.3 kPa -> HAZARDOUS_UNSTABLE_SOIL
        out_hazard = self.translator.translate(np.full((2, 2), 0.45, dtype=np.float32))
        self.assertLessEqual(out_hazard["mean_bearing_kPa"], TRAFFICABILITY_LIGHT_VEHICLE_THRESHOLD_KPA)
        self.assertEqual(out_hazard["site_trafficability"], "HAZARDOUS_UNSTABLE_SOIL")


if __name__ == "__main__":
    unittest.main()
