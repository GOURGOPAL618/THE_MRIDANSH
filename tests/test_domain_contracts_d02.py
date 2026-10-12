"""
Task 02 — Domain Translator Interface, Import & Schema Contracts Tests
======================================================================
Tests the standardized BaseDomainTranslator, DomainInput, and DomainOutput
specifications defined in 4_domain_translators/base.py.

Verifies:
  1. Shared contract construction for DomainInput and DomainOutput.
  2. Required field validation (soil_state array rank >= 2, non-empty domain string).
  3. Optional mask, uncertainty, and metadata handling without fabricated defaults.
  4. Consistent base/subclass interface signatures and normalize_input helper.
  5. Package exports and supported import mechanisms (importlib & sys.path).
  6. Rejection of invalid contract values (negative uncertainty, non-boolean mask, NaNs).
  7. Backward compatibility: existing translators continue to instantiate and execute.
"""

import importlib
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

# Import contracts using documented dynamic and sys.path mechanisms
from base import BaseDomainTranslator, DomainInput, DomainOutput


class TestDomainContractsD02(unittest.TestCase):

    def setUp(self):
        np.random.seed(42)
        self.valid_soil_state = np.random.uniform(0.15, 0.35, size=(10, 10)).astype(np.float32)

    # ─── 1. Shared contract construction ───────────────────────────────────────
    def test_tc_01_valid_contract_construction(self):
        """DomainInput and DomainOutput instantiate cleanly with documented fields."""
        inp = DomainInput(
            soil_state=self.valid_soil_state,
            state_variable="volumetric_soil_moisture",
            unit="m3/m3",
        )
        self.assertEqual(inp.state_variable, "volumetric_soil_moisture")
        self.assertEqual(inp.unit, "m3/m3")
        self.assertEqual(inp.soil_state.shape, (10, 10))

        out = DomainOutput(
            domain="agriculture",
            metrics={"crop_health_matrix": self.valid_soil_state, "mean_health": 85.0},
            warnings=["Uncalibrated heuristic model"],
        )
        self.assertEqual(out.domain, "agriculture")
        self.assertIn("crop_health_matrix", out.metrics)
        self.assertEqual(out["mean_health"], 85.0)  # dictionary emulation
        self.assertIn("mean_health", out)           # __contains__ emulation
        self.assertEqual(out.get("mean_health"), 85.0)

    # ─── 2. Required field validation ──────────────────────────────────────────
    def test_tc_02_required_field_validation(self):
        """Omitting required fields or providing invalid types fails with clear errors."""
        # Non-array soil_state
        with self.assertRaises(TypeError):
            DomainInput(soil_state="not_an_array")  # type: ignore

        # Rank-1 array (< 2 dimensions)
        with self.assertRaises(ValueError):
            DomainInput(soil_state=np.array([0.2, 0.3, 0.4]))

        # Empty domain identifier in DomainOutput
        with self.assertRaises(ValueError):
            DomainOutput(domain="", metrics={"score": 1.0})

        # Non-dict metrics in DomainOutput
        with self.assertRaises(TypeError):
            DomainOutput(domain="civil", metrics="not_a_dict")  # type: ignore

    # ─── 3. Optional mask, uncertainty and metadata handling ──────────────────
    def test_tc_03_optional_fields_handling(self):
        """Optional metadata, masks, and uncertainty are stored accurately."""
        mask = np.ones((10, 10), dtype=bool)
        mask[0, 0] = False
        transform = (10.0, 0.0, 300000.0, 0.0, -10.0, 4000000.0)
        bounds = (300000.0, 3999900.0, 300100.0, 4000000.0)
        resolution = (10.0, 10.0)
        prov = {"stac_id": "S2A_TEST_001"}

        inp = DomainInput(
            soil_state=self.valid_soil_state,
            valid_data_mask=mask,
            uncertainty=0.04,
            uncertainty_type="ensemble_variance",
            crs="EPSG:32645",
            transform=transform,
            bounds=bounds,
            resolution=resolution,
            acquisition_datetime="2026-10-09T12:00:00Z",
            provenance=prov,
        )

        self.assertEqual(inp.crs, "EPSG:32645")
        self.assertEqual(inp.uncertainty, 0.04)
        self.assertEqual(inp.uncertainty_type, "ensemble_variance")
        self.assertEqual(inp.transform, transform)
        self.assertEqual(inp.bounds, bounds)
        self.assertEqual(inp.resolution, resolution)
        self.assertEqual(inp.provenance, prov)
        self.assertEqual(inp.acquisition_datetime, "2026-10-09T12:00:00Z")

    # ─── 4. Missing metadata without fabricated defaults ───────────────────────
    def test_tc_04_missing_metadata_remains_none(self):
        """Omitted optional metadata fields remain None rather than having synthetic defaults."""
        inp = DomainInput(soil_state=self.valid_soil_state)
        self.assertIsNone(inp.crs)
        self.assertIsNone(inp.transform)
        self.assertIsNone(inp.bounds)
        self.assertIsNone(inp.resolution)
        self.assertIsNone(inp.valid_data_mask)
        self.assertIsNone(inp.uncertainty)
        self.assertIsNone(inp.uncertainty_type)
        self.assertIsNone(inp.acquisition_datetime)
        self.assertIsNone(inp.provenance)

    # ─── 5. Invalid contract values rejected with clear errors ────────────────
    def test_tc_05_invalid_contract_values_rejected(self):
        """Invalid contract values are trapped by __post_init__ validation."""
        # Negative scalar uncertainty
        with self.assertRaises(ValueError):
            DomainInput(soil_state=self.valid_soil_state, uncertainty=-0.05)

        # Mismatched mask shape
        bad_mask_shape = np.ones((5, 5), dtype=bool)
        with self.assertRaises(ValueError):
            DomainInput(soil_state=self.valid_soil_state, valid_data_mask=bad_mask_shape)

        # Non-boolean mask dtype
        float_mask = np.ones((10, 10), dtype=np.float32)
        with self.assertRaises(ValueError):
            DomainInput(soil_state=self.valid_soil_state, valid_data_mask=float_mask)

        # Unmasked NaN in soil_state
        nan_soil = self.valid_soil_state.copy()
        nan_soil[0, 0] = np.nan
        with self.assertRaises(ValueError):
            DomainInput(soil_state=nan_soil)

        # Masked NaN in soil_state is ALLOWED if masked out
        mask = np.ones((10, 10), dtype=bool)
        mask[0, 0] = False  # mask out the NaN pixel
        masked_inp = DomainInput(soil_state=nan_soil, valid_data_mask=mask)
        self.assertFalse(masked_inp.valid_data_mask[0, 0])

        # Negative / zero dry density
        with self.assertRaises(ValueError):
            DomainInput(soil_state=self.valid_soil_state, dry_density_g_cm3=0.0)

        # Inverted bounds (min >= max)
        with self.assertRaises(ValueError):
            DomainInput(soil_state=self.valid_soil_state, bounds=(100.0, 100.0, 50.0, 50.0))

    # ─── 6. Subclass interface compatibility & normalize_input ────────────────
    def test_tc_06_subclass_compatibility_and_normalization(self):
        """BaseDomainTranslator supports normalize_input and concrete subclassing."""
        # Verify ABC cannot be instantiated directly
        with self.assertRaises(TypeError):
            BaseDomainTranslator()  # type: ignore

        # Define a mock concrete translator
        class MockTranslator(BaseDomainTranslator):
            def translate(self, soil_input, **kwargs):
                inp = self.normalize_input(soil_input, **kwargs)
                return DomainOutput(
                    domain="test",
                    metrics={"processed_mean": float(np.mean(inp.soil_state))},
                    metadata={"crs": inp.crs},
                )

        translator = MockTranslator()

        # 1. Calling with DomainInput
        input_obj = DomainInput(soil_state=self.valid_soil_state, crs="EPSG:4326")
        out1 = translator.translate(input_obj)
        self.assertIsInstance(out1, DomainOutput)
        self.assertEqual(out1.domain, "test")
        self.assertEqual(out1.metadata["crs"], "EPSG:4326")

        # 2. Calling with raw numpy array + kwargs (legacy compatibility)
        out2 = translator.translate(self.valid_soil_state, crs="EPSG:32645")
        self.assertIsInstance(out2, DomainOutput)
        self.assertEqual(out2.metadata["crs"], "EPSG:32645")

    # ─── 7. Package exports and supported import mechanisms ───────────────────
    def test_tc_07_package_exports_and_imports(self):
        """Verifies package exports and documented import mechanisms."""
        # 1. Dynamic import via importlib
        mod = importlib.import_module("4_domain_translators")
        self.assertTrue(hasattr(mod, "BaseDomainTranslator"))
        self.assertTrue(hasattr(mod, "DomainInput"))
        self.assertTrue(hasattr(mod, "DomainOutput"))
        self.assertTrue(hasattr(mod, "AgronomyHealthTranslator"))
        self.assertTrue(hasattr(mod, "CivilLoadTranslator"))

        # Verify __all__ export declaration
        expected_exports = {
            "BaseDomainTranslator",
            "DomainInput",
            "DomainOutput",
            "AgronomyHealthTranslator",
            "CivilLoadTranslator",
        }
        self.assertEqual(set(mod.__all__), expected_exports)

    # ─── 8. Existing translator backward compatibility ────────────────────────
    def test_tc_08_existing_translators_backward_compatibility(self):
        """Existing AgronomyHealthTranslator and CivilLoadTranslator execute unchanged."""
        mod = importlib.import_module("4_domain_translators")
        agri_translator = mod.AgronomyHealthTranslator()
        civil_translator = mod.CivilLoadTranslator()

        # Verify Agronomy runs legacy call signature
        mock_moisture = np.random.uniform(0.12, 0.38, size=(20, 20)).astype(np.float32)
        mock_ndvi = np.random.uniform(0.30, 0.85, size=(20, 20)).astype(np.float32)

        agri_res = agri_translator.translate(mock_moisture, mock_ndvi)
        self.assertIn("crop_health_matrix", agri_res)
        self.assertIn("irrigation_required_l_ha", agri_res)
        self.assertIn("drought_risk_status", agri_res)
        self.assertEqual(agri_res["crop_health_matrix"].shape, (20, 20))

        # Verify Civil runs legacy call signature
        civil_res = civil_translator.translate(mock_moisture, dry_density_g_cm3=1.6)
        self.assertIn("bearing_capacity_matrix_kPa", civil_res)
        self.assertIn("site_trafficability", civil_res)
        self.assertEqual(civil_res["bearing_capacity_matrix_kPa"].shape, (20, 20))


if __name__ == "__main__":
    unittest.main()
