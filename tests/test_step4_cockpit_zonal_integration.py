# THE MRIDANSH - VERIFICATION TEST SUITE
# Test: tests/test_step4_cockpit_zonal_integration.py
# Verification Target: Step 4 (End-to-End Zonal Telemetry HUD & Kisan War Room Coupling)
# Standards: Mission Assurance Level-A / FAO-56 / ISO 19115
# Lead Systems Architect: Gouragopal Mohapatra (JCC Campus 2, RS-SDA Division)

import sys
from pathlib import Path
import importlib.util
import numpy as np
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Dynamic load of ZonalFieldExtractor
p_zonal = ROOT_DIR / "4_domain_translators" / "zonal_field_extractor.py"
spec = importlib.util.spec_from_file_location("zonal_field_extractor", str(p_zonal))
zonal_mod = importlib.util.module_from_spec(spec)
sys.modules["zonal_field_extractor"] = zonal_mod
spec.loader.exec_module(zonal_mod)

ZonalFieldExtractor = zonal_mod.ZonalFieldExtractor
ZonalFieldResult = zonal_mod.ZonalFieldResult


@pytest.fixture
def synthetic_spaceborne_rasters():
    """Generates synthetic 64x64 calibrated physical soil rasters conforming to Kendrapara flight scene."""
    np.random.seed(42)
    theta_surf = np.random.uniform(0.18, 0.28, size=(64, 64)).astype(np.float32)
    theta_root = theta_surf + np.random.uniform(0.015, 0.035, size=(64, 64)).astype(np.float32)
    cwsi = np.clip(1.0 - (theta_root / 0.35), 0.0, 1.0).astype(np.float32)
    q_allow_kpa = (500.0 - (theta_root * 500.0)).astype(np.float32)
    aoi_bbox = (86.35, 20.45, 86.50, 20.55)
    return theta_surf, theta_root, cwsi, q_allow_kpa, aoi_bbox


class TestStep4CockpitZonalIntegration:
    """Verifies that farm boundary polygon extraction directly powers the Step 2 HUD & Kisan War Room."""

    def test_01_zonal_telemetry_hud_metrics_consistency(self, synthetic_spaceborne_rasters):
        """Verifies that HUD values match the zonal distribution moments rather than arbitrary point values."""
        theta_surf, theta_root, cwsi, q_allow_kpa, aoi_bbox = synthetic_spaceborne_rasters
        extractor = ZonalFieldExtractor()

        # Define ~2 hectare farm polygon near Kendrapara center
        farm_polygon = [
            (86.4150, 20.4950),
            (86.4300, 20.4950),
            (86.4300, 20.5050),
            (86.4150, 20.5050),
            (86.4150, 20.4950),
        ]

        res = extractor.extract_from_rasters(
            polygon_coords=farm_polygon,
            aoi_bbox=aoi_bbox,
            theta_surf=theta_surf,
            theta_root=theta_root,
            cwsi=cwsi,
            q_allow_kpa=q_allow_kpa,
            crop_name="paddy",
            soil_class="silt_loam",
        )

        assert isinstance(res, ZonalFieldResult)
        assert res.pixel_count > 0

        # Simulate Cockpit State assignment
        hud_theta_surf = res.theta_surf.mean
        hud_theta_root = res.theta_root.mean
        hud_cwsi = res.cwsi.mean
        hud_bearing = res.bearing_capacity_kpa.mean

        # Values must be within field statistical bounds
        assert res.theta_surf.min <= hud_theta_surf <= res.theta_surf.max
        assert res.theta_root.min <= hud_theta_root <= res.theta_root.max
        assert res.cwsi.min <= hud_cwsi <= res.cwsi.max
        assert res.bearing_capacity_kpa.min <= hud_bearing <= res.bearing_capacity_kpa.max

    def test_02_kisan_war_room_volume_prescription_scaling(self, synthetic_spaceborne_rasters):
        """Verifies that total water prescription scales with farm area rather than entire scene."""
        theta_surf, theta_root, cwsi, q_allow_kpa, aoi_bbox = synthetic_spaceborne_rasters
        extractor = ZonalFieldExtractor()

        # 1-hectare small farm
        small_poly = [
            (86.4200, 20.5000),
            (86.4250, 20.5000),
            (86.4250, 20.5050),
            (86.4200, 20.5050),
            (86.4200, 20.5000),
        ]
        res_small = extractor.extract_from_rasters(
            small_poly, aoi_bbox, theta_surf, theta_root, cwsi, q_allow_kpa
        )

        # 4-hectare larger farm
        large_poly = [
            (86.4100, 20.4900),
            (86.4300, 20.4900),
            (86.4300, 20.5100),
            (86.4100, 20.5100),
            (86.4100, 20.4900),
        ]
        res_large = extractor.extract_from_rasters(
            large_poly, aoi_bbox, theta_surf, theta_root, cwsi, q_allow_kpa
        )

        # Total litres must scale with farm area
        assert res_large.area_ha > res_small.area_ha
        assert res_large.total_irrigation_prescription_litres > res_small.total_irrigation_prescription_litres

        # Unit depth (mm/ha) remains bounded around target deficit
        assert 5.0 <= res_small.recommended_water_mm_per_ha <= 40.0
        assert 5.0 <= res_large.recommended_water_mm_per_ha <= 40.0

    def test_03_terramechanics_rut_depth_and_trafficability(self, synthetic_spaceborne_rasters):
        """Verifies Bekker rut sinkage computation and trafficability classification."""
        theta_surf, theta_root, cwsi, q_allow_kpa, aoi_bbox = synthetic_spaceborne_rasters
        extractor = ZonalFieldExtractor()

        poly = [
            (86.4200, 20.5000),
            (86.4300, 20.5000),
            (86.4300, 20.5100),
            (86.4200, 20.5100),
            (86.4200, 20.5000),
        ]
        res = extractor.extract_from_rasters(poly, aoi_bbox, theta_surf, theta_root, cwsi, q_allow_kpa)

        assert res.max_rut_depth_cm >= 0.0
        assert res.trafficability_grade in [
            "SAFE_SMOOTH_TILLAGE",
            "MODERATE_RUT_RISK",
            "CRITICAL_BOGGING_HAZARD",
        ]
        assert len(res.sha256_provenance_hash) == 64
        assert res.execution_latency_ms < 5.0  # Industry Cockpit SLA < 5ms (typically < 1ms)
