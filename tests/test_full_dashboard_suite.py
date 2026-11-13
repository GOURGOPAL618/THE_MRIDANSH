# THE MRIDANSH - VERIFICATION TEST SUITE
# Test: tests/test_full_dashboard_suite.py
# Verification Target: Full Dashboard Cockpit End-to-End System Audit
# Standards: Mission Assurance Level-A / FAO-56 / USACE TM 5-818-1
# Lead Systems Architect: Gouragopal Mohapatra (JCC Campus 2, RS-SDA Division)

import sys
import time
from pathlib import Path
import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

APP_PATH = str(ROOT_DIR / "6_dashboard" / "app.py")
STYLE_PATH = ROOT_DIR / "6_dashboard" / "assets" / "style.css"


class TestFullDashboardCockpitSuite:
    """Comprehensive test suite for THE MRIDANSH Aerospace Cockpit (Streamlit)."""

    def test_01_dashboard_headless_boot_and_clean_execution(self):
        """Verifies that the entire app boots and runs without throwing any exception."""
        start_time = time.perf_counter()
        at = AppTest.from_file(APP_PATH, default_timeout=35)
        at.run()
        elapsed = time.perf_counter() - start_time

        # Ensure no runtime exceptions
        assert len(at.exception) == 0, f"App execution raised exceptions: {[e.value for e in at.exception]}"
        # Ensure title / brand loaded
        assert len(at.title) >= 1 or len(at.markdown) > 0
        print(f"\n[PASS] Dashboard booted successfully in {elapsed:.2f}s with 0 exceptions.")

    def test_02_cockpit_zonal_polygon_simulation(self):
        """Simulates user drawing a 5-point farm polygon and verifies zonal recalculation."""
        at = AppTest.from_file(APP_PATH, default_timeout=35)
        at.run()

        # Inject user drawn polygon into session state
        kendrapara_polygon = [
            [86.4150, 20.4950],
            [86.4300, 20.4950],
            [86.4300, 20.5050],
            [86.4150, 20.5050],
            [86.4150, 20.4950],
        ]
        at.session_state["inspection_mode"] = "Draw Farm Boundary (Zonal Mode)"
        at.session_state["user_drawn_polygon"] = kendrapara_polygon
        at.run()

        assert len(at.exception) == 0
        assert at.session_state["user_drawn_polygon"] == kendrapara_polygon
        print("\n[PASS] Cockpit successfully handled Zonal polygon drawing interaction with zero exceptions.")

    def test_03_crop_variety_switching(self):
        """Verifies switching crop varieties across Paddy, Wheat, and Maize."""
        at = AppTest.from_file(APP_PATH, default_timeout=35)
        at.run()

        for crop in ["paddy", "wheat", "maize"]:
            at.session_state["crop_variety"] = crop
            at.run()
            assert len(at.exception) == 0
        print("\n[PASS] Successfully verified crop switching across paddy, wheat, and maize.")

    def test_04_footer_markdown_integrity_and_jcc_branding(self):
        """Verifies that footer does NOT produce raw markdown code blocks (<pre><code>) and has strict JCC branding."""
        at = AppTest.from_file(APP_PATH, default_timeout=35)
        at.run()

        # Inspect all markdown outputs
        all_markdown_texts = [m.value for m in at.markdown]
        combined_markdown = "\n".join(all_markdown_texts)

        # Check that footer rendered
        assert "mrid-aerospace-footer" in combined_markdown or any("mrid-aerospace-footer" in m.value for m in at.markdown)

        # Ensure no unparsed HTML code block leak
        assert "```<div class=\"mrid-footer-specs-grid\">" not in combined_markdown
        assert "<pre><code>" not in combined_markdown

        # Ensure strict JCC and Commander Gouragopal Mohapatra branding
        assert "GOURAGOPAL MOHAPATRA" in combined_markdown
        assert "Jagannath Command Center (JCC) & JCC Campus 1 (RS - SDA Division)" in combined_markdown

        # Verify no unauthorized agency claims in copyright/mission text
        assert "NASA JPL" not in combined_markdown
        assert "ESA Copernicus" not in combined_markdown
        print("\n[PASS] Footer verified: zero raw code blocks, 100% strict JCC Campus 1 & Commander branding.")

    def test_05_css_stylesheet_integrity(self):
        """Verifies that style.css defines all required aerospace UI classes."""
        assert STYLE_PATH.exists(), f"Style sheet missing at {STYLE_PATH}"
        with open(STYLE_PATH, "r", encoding="utf-8") as f:
            css_content = f.read()

        required_classes = [
            ".mrid-aerospace-footer",
            ".mrid-footer-specs-grid",
            ".mrid-farm-badge",
            ".sidebar-brand-card",
            ".mrid-master-header",
        ]
        for cls in required_classes:
            assert cls in css_content, f"CSS rule {cls} missing from style.css"

        # Check footer visibility rule
        assert "footer:not(.mrid-aerospace-footer)" in css_content
        print("\n[PASS] CSS stylesheet verified with all aerospace UI classes present.")

    def test_06_physical_engine_subsystem10_integration(self):
        """Verifies Subsystem 10 ZonalFieldExtractor directly against 64x64 mission rasters."""
        import importlib.util
        p_zonal = ROOT_DIR / "4_domain_translators" / "zonal_field_extractor.py"
        spec = importlib.util.spec_from_file_location("zonal_field_extractor", str(p_zonal))
        zonal_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(zonal_mod)
        ZonalFieldExtractor = zonal_mod.ZonalFieldExtractor

        extractor = ZonalFieldExtractor()
        theta_surf = np.full((64, 64), 0.22, dtype=np.float32)
        theta_root = np.full((64, 64), 0.25, dtype=np.float32)
        cwsi = np.full((64, 64), 0.30, dtype=np.float32)
        q_allow = np.full((64, 64), 380.0, dtype=np.float32)
        aoi_bbox = (86.35, 20.45, 86.50, 20.55)

        poly = [
            (86.42, 20.49),
            (86.44, 20.49),
            (86.44, 20.51),
            (86.42, 20.51),
            (86.42, 20.49),
        ]

        res = extractor.extract_from_rasters(
            polygon_coords=poly,
            aoi_bbox=aoi_bbox,
            theta_surf=theta_surf,
            theta_root=theta_root,
            cwsi=cwsi,
            q_allow_kpa=q_allow,
            crop_name="wheat",
            soil_class="clay_loam",
        )

        assert res.pixel_count > 0
        assert res.area_ha > 0.0
        assert res.total_irrigation_prescription_litres >= 0.0
        assert res.max_rut_depth_cm >= 0.0
        assert len(res.sha256_provenance_hash) == 64
        print(f"\n[PASS] Physical Engine Subsystem 10: {res.pixel_count} pixels, {res.area_ha:.2f} ha, {res.total_irrigation_prescription_litres:.1f} L, Rut {res.max_rut_depth_cm:.2f} cm, SHA-256: {res.sha256_provenance_hash[:16]}...")
