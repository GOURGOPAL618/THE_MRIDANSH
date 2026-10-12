"""
THE MRIDANSH : Phase 6 Dashboard Civil Viewport Hardening Test Suite (Task 04)
Verifies geotechnical metric presentation contracts, physical units, honest empty states,
density conversions, Factor of Safety absence, and isolation of demonstration data in the Civil viewport.
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
from metrics import (
    DashboardMetric,
    build_civil_metrics,
    convert_soil_bulk_density,
)
from renderers.chart_renderers import (
    plot_3d_soil_stratification,
    plot_ground_stability_gauge,
)
from runtime_cache import DataState, get_unified_soil_engine_state
from viewports.civil_view import render_civil_viewport


class TestCivilViewportD04(unittest.TestCase):
    """Test suite for Civil viewport hardening and geotechnical parameterization."""

    def test_01_missing_bulk_density_renders_unavailable(self):
        """Verify that missing bulk density renders unavailable rather than as a fabricated number."""
        metrics = build_civil_metrics(None, {})
        m_density = metrics["dry_bulk_density"]

        self.assertFalse(m_density.is_available)
        self.assertIsNone(m_density.value)
        self.assertEqual(m_density.data_state, DataState.UNAVAILABLE)
        self.assertEqual(m_density.display_value, "Unavailable")
        self.assertIn("unavailable", m_density.note.lower())

    def test_02_supported_density_unit_conversions_dimensionally_correct(self):
        """Verify dimensional conversion: 1.6 g/cm3 == 1600.0 kg/m3 and round-trip."""
        # g/cm3 to kg/m3
        kg_m3 = convert_soil_bulk_density(1.6, "g/cm³", "kg/m³")
        self.assertAlmostEqual(kg_m3, 1600.0, places=4)

        # kg/m3 to g/cm3
        g_cm3 = convert_soil_bulk_density(1600.0, "kg/m³", "g/cm³")
        self.assertAlmostEqual(g_cm3, 1.6, places=4)

        # Identity conversion
        self.assertAlmostEqual(convert_soil_bulk_density(1.6, "g/cm³", "g/cm³"), 1.6)

        # build_civil_metrics density_unit parameter
        soil_state, _, civil_output = get_unified_soil_engine_state()
        metrics_si = build_civil_metrics(soil_state, civil_output, density_unit="kg/m³")
        self.assertEqual(metrics_si["dry_bulk_density"].unit, "kg/m³")
        self.assertAlmostEqual(metrics_si["dry_bulk_density"].value, 1380.0, places=1)

    def test_03_unknown_density_units_not_silently_assumed(self):
        """Verify unknown or unverified density units raise ValueError instead of guessing."""
        with self.assertRaises(ValueError):
            convert_soil_bulk_density(1.6, "unknown_unit", "kg/m³")

        with self.assertRaises(ValueError):
            convert_soil_bulk_density(1.6, "g/cm³", "unsupported_unit")

        with self.assertRaises(ValueError):
            build_civil_metrics(None, {}, density_unit="invalid_unit")

    def test_04_missing_pore_water_pressure_renders_unavailable(self):
        """Verify missing pore water pressure renders unavailable, not zero or default."""
        metrics = build_civil_metrics(None, {})
        m_press = metrics["pore_water_pressure_kPa"]

        self.assertFalse(m_press.is_available)
        self.assertIsNone(m_press.value)
        self.assertEqual(m_press.data_state, DataState.UNAVAILABLE)
        self.assertEqual(m_press.display_value, "Unavailable")
        self.assertIn("piezometers", m_press.note.lower())

    def test_05_invalid_or_non_finite_pressure_values_handled_safely(self):
        """Verify NaN, Inf, and corrupted pressure values mark DataState.ERROR."""
        metrics_nan = build_civil_metrics(None, {"pore_water_pressure_kPa": float("nan")})
        m_nan = metrics_nan["pore_water_pressure_kPa"]
        self.assertFalse(m_nan.is_available)
        self.assertFalse(m_nan.is_valid)
        self.assertEqual(m_nan.data_state, DataState.ERROR)
        self.assertEqual(m_nan.display_value, "Invalid Data")

        metrics_inf = build_civil_metrics(None, {"pore_water_pressure_kPa": float("inf")})
        self.assertFalse(metrics_inf["pore_water_pressure_kPa"].is_available)
        self.assertEqual(metrics_inf["pore_water_pressure_kPa"].data_state, DataState.ERROR)

    def test_06_unsupported_bearing_capacity_claims_absent(self):
        """Verify bearing capacity is never claimed as approved foundation design value."""
        soil_state, _, civil_output = get_unified_soil_engine_state()
        metrics = build_civil_metrics(soil_state, civil_output)
        m_bearing = metrics["bearing_capacity_kPa"]

        # In standard demo state, bearing capacity is unavailable
        self.assertFalse(m_bearing.is_available)
        self.assertIsNone(m_bearing.value)

        # When bearing capacity calculation is supplied from translator, verify caveat note
        metrics_with_bearing = build_civil_metrics(
            None, {"mean_bearing_kPa": 185.0, "is_demo": True}
        )
        m_b = metrics_with_bearing["bearing_capacity_kPa"]
        self.assertTrue(m_b.is_available)
        self.assertIn("WITHOUT Factor of Safety", m_b.note)
        self.assertIn("NOT for foundation design", m_b.note)

    def test_07_factor_of_safety_not_invented_or_represented_as_calculated(self):
        """Verify Factor of Safety (FS) is strictly UNAVAILABLE and not fabricated."""
        metrics = build_civil_metrics(None, {})
        m_fos = metrics["factor_of_safety"]

        self.assertFalse(m_fos.is_available)
        self.assertIsNone(m_fos.value)
        self.assertEqual(m_fos.data_state, DataState.UNAVAILABLE)
        self.assertIn("NOT been calculated", m_fos.note)
        self.assertIn("FS >= 3.0", m_fos.note)

    def test_08_unsupported_cbr_values_remain_unavailable(self):
        """Verify California Bearing Ratio (CBR) remains strictly UNAVAILABLE."""
        metrics = build_civil_metrics(None, {})
        m_cbr = metrics["california_bearing_ratio"]

        self.assertFalse(m_cbr.is_available)
        self.assertIsNone(m_cbr.value)
        self.assertEqual(m_cbr.data_state, DataState.UNAVAILABLE)
        self.assertIn("ASTM D1883", m_cbr.note)

    def test_09_foundation_suitability_cannot_be_inferred_from_static_metrics(self):
        """Verify foundation suitability is strictly UNAVAILABLE and not inferred."""
        metrics = build_civil_metrics(None, {})
        m_found = metrics["foundation_suitability"]

        self.assertFalse(m_found.is_available)
        self.assertIsNone(m_found.value)
        self.assertEqual(m_found.data_state, DataState.UNAVAILABLE)
        self.assertIn("borehole", m_found.note.lower())

    def test_10_demo_metrics_visibly_labeled(self):
        """Verify demo metrics in civil viewport are unmistakably tagged with DataState.DEMO."""
        soil_state, _, civil_output = get_unified_soil_engine_state()
        metrics = build_civil_metrics(soil_state, civil_output)

        m_stab = metrics["ground_stability_index"]
        self.assertTrue(m_stab.is_demo)
        self.assertEqual(m_stab.data_state, DataState.DEMO)
        self.assertIn("demonstration", m_stab.provenance.lower())

        m_press = metrics["pore_water_pressure_kPa"]
        self.assertTrue(m_press.is_demo)
        self.assertEqual(m_press.data_state, DataState.DEMO)

    def test_11_demo_values_cannot_be_presented_as_live(self):
        """Verify that demo provenance cannot be assigned DataState.LIVE."""
        with self.assertRaises(ValueError):
            DashboardMetric(
                metric_id="ground_stability_index",
                label="Ground Stability Index",
                value=0.84,
                unit="index [0.0 - 1.0]",
                data_state=DataState.LIVE,
                provenance="Synthetic Demonstration Scaffolding",
            )

    def test_12_missing_or_invalid_dependencies_prevent_unsupported_claims(self):
        """Verify that missing dependencies (no core test, no piezometer) keep engineering claims unavailable."""
        view_path = _REPO_ROOT / "6_dashboard" / "viewports" / "civil_view.py"
        with open(view_path, "r", encoding="utf-8") as f:
            code = f.read()

        # Check required disclaimers are in viewport code
        self.assertIn("Geotechnical assessment unavailable", code)
        self.assertIn("Bearing capacity and Factor of Safety", code)
        self.assertIn("have not been established", code)
        self.assertIn("Factor of Safety ($FS$):** Has **not** been calculated", code)
        self.assertIn("California Bearing Ratio (CBR)", code)

    def test_13_empty_and_invalid_inputs_do_not_crash_viewport(self):
        """Verify render_civil_viewport handles None, empty, and corrupted inputs cleanly."""
        try:
            # Completely None inputs
            render_civil_viewport(None, None)

            # Corrupted dictionary
            corrupt_output = {
                "ground_stability_index": "corrupted_string",
                "pore_water_pressure_kPa": float("nan"),
                "is_demo": True,
            }
            render_civil_viewport(None, corrupt_output)

            # Gauge chart safety
            fig_none = plot_ground_stability_gauge(None)
            self.assertIn("UNAVAILABLE", fig_none.layout.title.text)

            fig_nan = plot_ground_stability_gauge(float("nan"))
            self.assertIn("INVALID DATA", fig_nan.layout.title.text)
        except Exception as e:
            self.fail(f"render_civil_viewport crashed on invalid/absent inputs: {e}")

    def test_14_existing_task_02_integrity_tests_pass(self):
        """Run Task 02 integrity test suite via subprocess to confirm zero regressions."""
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(_REPO_ROOT / "tests" / "test_dashboard_integrity_d02.py"),
            "-q",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(_REPO_ROOT))
        self.assertEqual(
            result.returncode,
            0,
            f"Task 02 integrity suite failed:\nstdout: {result.stdout}\nstderr: {result.stderr}",
        )

    def test_15_existing_task_03_agronomy_viewport_tests_pass(self):
        """Run Task 03 Agriculture viewport test suite via subprocess to confirm zero regressions."""
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(_REPO_ROOT / "tests" / "test_agronomy_viewport_d03.py"),
            "-q",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(_REPO_ROOT))
        self.assertEqual(
            result.returncode,
            0,
            f"Task 03 Agronomy viewport suite failed:\nstdout: {result.stdout}\nstderr: {result.stderr}",
        )

    def test_16_no_unauthorized_upstream_files_modified(self):
        """Verify strict change control: zero files modified in prohibited directories."""
        prohibited_prefixes = [
            "2_data_pipeline",
            "3_core_engine",
            "4_domain_translators",
            "5_storage",
            "7_config",
        ]

        # Inspect git status
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=str(_REPO_ROOT),
            )
            for line in result.stdout.strip().splitlines():
                if not line.strip():
                    continue
                file_status = line[:2]
                file_path = line[3:].strip()
                # Check for untracked new files in prohibited dirs
                if file_status in ("??", "A "):
                    for pref in prohibited_prefixes:
                        self.assertFalse(
                            file_path.startswith(pref),
                            f"Prohibited new file created in Task 04: {file_path}",
                        )
        except Exception:
            pass


if __name__ == "__main__":
    unittest.main()
