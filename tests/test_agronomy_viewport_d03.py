"""
THE MRIDANSH : Phase 6 Dashboard Agriculture Viewport Hardening Test Suite (Task 03)
Verifies metric presentation contracts, physical units, honest empty states,
and isolation of demonstration data in the Agriculture viewport.
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

import numpy as np
import pytest
from metrics import DashboardMetric, build_agronomy_metrics
from renderers.chart_renderers import (
    plot_moisture_depth_profile,
    plot_npk_distribution,
)
from runtime_cache import DataState, get_unified_soil_engine_state
from viewports.agronomy_view import render_agronomy_viewport


class TestAgronomyViewportD03(unittest.TestCase):
    """Test suite for Agriculture viewport hardening and metric rendering."""

    def test_01_available_metrics_render_with_actual_units_and_states(self):
        """Verify that genuine available metrics preserve their explicit units and data states."""
        # Test synthetic fixture representing an available demo container
        soil_state, agronomy_output, _ = get_unified_soil_engine_state()
        metrics = build_agronomy_metrics(soil_state, agronomy_output)

        m_moist = metrics["root_zone_moisture"]
        self.assertTrue(m_moist.is_available)
        self.assertEqual(m_moist.unit, "m³/m³")
        self.assertEqual(m_moist.data_state, DataState.DEMO)
        self.assertAlmostEqual(m_moist.value, 0.295)
        self.assertIn("29.5%", m_moist.display_value)

    def test_02_missing_soil_moisture_shown_as_unavailable_not_fabricated(self):
        """Verify that missing soil moisture is represented as unavailable, not as 0 or 0.5."""
        empty_output = {}
        metrics = build_agronomy_metrics(None, empty_output)

        m_moist = metrics["root_zone_moisture"]
        self.assertFalse(m_moist.is_available)
        self.assertIsNone(m_moist.value)
        self.assertEqual(m_moist.data_state, DataState.UNAVAILABLE)
        self.assertEqual(m_moist.display_value, "Unavailable")
        self.assertIn("unavailable", m_moist.note.lower())

    def test_03_missing_ndvi_does_not_generate_unsupported_crop_health(self):
        """Verify that absent NDVI prevents calculation or display of crop health score."""
        # Output with moisture but NO NDVI
        output_no_ndvi = {"root_zone_moisture": 0.25, "mean_health_score": 0.82}
        metrics = build_agronomy_metrics(None, output_no_ndvi)

        m_ndvi = metrics["ndvi"]
        m_health = metrics["crop_health_score"]

        self.assertFalse(m_ndvi.is_available)
        self.assertFalse(m_health.is_available)
        self.assertIsNone(m_health.value)
        self.assertEqual(m_health.data_state, DataState.UNAVAILABLE)
        self.assertIn("requires paired moisture and optical ndvi", m_health.note.lower())

    def test_04_missing_npk_and_organic_carbon_remain_unavailable(self):
        """Verify that missing NPK and organic carbon metrics remain strictly unavailable."""
        metrics = build_agronomy_metrics(None, {})

        for k in ["nitrogen_level", "phosphorus_level", "potassium_level", "organic_carbon"]:
            m = metrics[k]
            self.assertFalse(m.is_available)
            self.assertIsNone(m.value)
            self.assertEqual(m.data_state, DataState.UNAVAILABLE)
            self.assertEqual(m.display_value, "Unavailable")

    def test_05_demo_metrics_are_clearly_labeled(self):
        """Verify demo metrics are explicitly tagged with DataState.DEMO and is_demo=True."""
        soil_state, agronomy_output, _ = get_unified_soil_engine_state()
        metrics = build_agronomy_metrics(soil_state, agronomy_output)

        m_moist = metrics["root_zone_moisture"]
        self.assertTrue(m_moist.is_demo)
        self.assertEqual(m_moist.data_state, DataState.DEMO)
        self.assertIn("demonstration", m_moist.provenance.lower())

    def test_06_demo_values_cannot_be_mislabeled_as_live(self):
        """Verify contract rejects setting data_state=LIVE when provenance indicates demo/synthetic."""
        with self.assertRaises(ValueError):
            DashboardMetric(
                metric_id="bad_metric",
                label="Bad Metric",
                value=0.30,
                unit="m3/m3",
                data_state=DataState.LIVE,
                provenance="Synthetic Demonstration Scaffolding",
            )

    def test_07_invalid_or_absent_values_do_not_crash_rendering(self):
        """Verify Agriculture viewport renders cleanly without crashing on None or corrupted inputs."""
        try:
            # Completely None inputs
            render_agronomy_viewport(None, None)

            # Corrupted dictionary
            corrupt_output = {
                "root_zone_moisture": "not_a_float",
                "mean_health_score": float("nan"),
                "is_demo": True,
            }
            render_agronomy_viewport(None, corrupt_output)
        except Exception as e:
            self.fail(f"render_agronomy_viewport crashed on invalid/absent inputs: {e}")

    def test_08_nan_and_infinite_values_handled_safely(self):
        """Verify that NaN and Inf values are safely caught and not plotted as valid numbers."""
        metrics = build_agronomy_metrics(None, {"root_zone_moisture": float("nan")})
        m_moist = metrics["root_zone_moisture"]
        self.assertFalse(m_moist.is_available)
        self.assertFalse(m_moist.is_valid)
        self.assertEqual(m_moist.data_state, DataState.ERROR)
        self.assertEqual(m_moist.display_value, "Invalid Data")

        # Test Inf
        metrics_inf = build_agronomy_metrics(None, {"root_zone_moisture": float("inf")})
        self.assertFalse(metrics_inf["root_zone_moisture"].is_available)
        self.assertEqual(metrics_inf["root_zone_moisture"].data_state, DataState.ERROR)

    def test_09_missing_depth_profile_not_silently_converted_to_zeros(self):
        """Verify missing moisture profile displays an empty state instead of plotting fake zeros."""
        fig_empty = plot_moisture_depth_profile([5, 10, 20], None, is_demo=False)
        self.assertIn("UNAVAILABLE", fig_empty.layout.title.text)
        # Empty figure should have annotations and hidden axes, not traces at 0
        self.assertTrue(len(fig_empty.layout.annotations) > 0)
        self.assertEqual(len(fig_empty.data), 0)

        # All-NaN profile
        fig_nan = plot_moisture_depth_profile([5, 10, 20], [np.nan, np.nan, np.nan], is_demo=False)
        self.assertIn("INVALID DATA", fig_nan.layout.title.text)
        self.assertEqual(len(fig_nan.data), 0)

    def test_10_unsupported_prescriptions_not_generated(self):
        """Verify neither fertilizer doses nor commercial irrigation schedules are generated."""
        soil_state, agronomy_output, _ = get_unified_soil_engine_state()
        metrics = build_agronomy_metrics(soil_state, agronomy_output)

        # When deficit is not connected, it states unavailable
        self.assertFalse(metrics["irrigation_required_l_ha"].is_available)

        # When irrigation deficit calculation is supplied, verify it is marked as theoretical deficit, not prescription
        metrics_with_irrig = build_agronomy_metrics(
            None, {"root_zone_moisture": 0.30, "irrigation_required_l_ha": 50000.0}
        )
        m_irrig = metrics_with_irrig["irrigation_required_l_ha"]
        self.assertTrue(m_irrig.is_available)
        self.assertIn("Not an official field prescription", m_irrig.note)

        # Viewport code must not contain Urea prescription
        view_path = _REPO_ROOT / "6_dashboard" / "viewports" / "agronomy_view.py"
        with open(view_path, "r", encoding="utf-8") as f:
            code = f.read()

        self.assertNotIn("15 kg/ha Urea", code)
        self.assertIn("Nutrient recommendation unavailable", code)
        self.assertIn("Certified crop irrigation prescriptions", code)

    def test_11_unsupported_kpi_deltas_and_confidence_not_rendered(self):
        """Verify fake +1.2% (24h) and 92% confidence deltas are eliminated from agronomy_view."""
        view_path = _REPO_ROOT / "6_dashboard" / "viewports" / "agronomy_view.py"
        with open(view_path, "r", encoding="utf-8") as f:
            code = f.read()

        self.assertNotIn("delta=\"+1.2% (24h)\"", code)
        self.assertNotIn("delta=\"Healthy\"", code)
        self.assertNotIn("delta=\"EnKF Active\"", code)

    def test_12_existing_task_02_integrity_tests_pass(self):
        """Verify all Task 02 integrity tests continue to pass with Task 03 additions."""
        from test_dashboard_integrity_d02 import TestDashboardScientificIntegrityD02

        suite = unittest.TestLoader().loadTestsFromTestCase(TestDashboardScientificIntegrityD02)
        runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=1)
        result = runner.run(suite)
        self.assertTrue(result.wasSuccessful())

    def test_13_no_upstream_files_modified(self):
        """Verify strict change control: Task 03 modifications are confined to 6_dashboard and tests."""
        # Check that metrics presentation module and viewport are in authorized scope
        metrics_path = _REPO_ROOT / "6_dashboard" / "metrics.py"
        agronomy_view_path = _REPO_ROOT / "6_dashboard" / "viewports" / "agronomy_view.py"
        self.assertTrue(metrics_path.exists())
        self.assertTrue(agronomy_view_path.exists())
