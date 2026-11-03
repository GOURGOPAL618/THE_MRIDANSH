# THE MRIDANSH - VERIFICATION TEST SUITE
# Test: tests/test_zonal_field_extractor.py
# Verification Target: Subsystem 10 (Zonal Farm Analytics & Polygon Extraction Engine)
# Standards: RTCA DO-178C Level-A / ISO 19115 / FAO-56
# Lead Systems Architect: Gouragopal Mohapatra (JCC Campus 2, RS-SDA Division)

import sys
from pathlib import Path
import time
import numpy as np
import pytest

# Ensure root is on path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Dynamic import to handle numerical folder prefix
import importlib
zonal_module = importlib.import_module("4_domain_translators.zonal_field_extractor")
ZonalFieldExtractor = zonal_module.ZonalFieldExtractor
ZonalFieldResult = zonal_module.ZonalFieldResult


@pytest.fixture
def synthetic_flight_rasters():
    """Generates synthetic 64x64 calibrated physical soil rasters conforming to Kendrapara flight scene."""
    np.random.seed(42)
    # Surface moisture: 18% to 28%
    theta_surf = np.random.uniform(0.18, 0.28, size=(64, 64)).astype(np.float32)
    # Root moisture: 20% to 32%
    theta_root = theta_surf + np.random.uniform(0.015, 0.035, size=(64, 64)).astype(np.float32)
    # CWSI: 0.0 to 0.5
    cwsi = np.clip(1.0 - (theta_root / 0.35), 0.0, 1.0).astype(np.float32)
    # Allowable Bearing Capacity: 330 to 480 kPa
    q_allow_kpa = (500.0 - (theta_root * 500.0)).astype(np.float32)
    
    bbox = (86.35, 20.45, 86.50, 20.55)
    return theta_surf, theta_root, cwsi, q_allow_kpa, bbox


class TestZonalFieldExtractorDO178C:
    """Rigorous verification suite for boundary-constrained zonal polygon integration."""

    def test_zone_01_geometric_area_consistency(self, synthetic_flight_rasters):
        """ZONE-01: Verifies that geometric area and pixel count are strictly positive and consistent."""
        theta_surf, theta_root, cwsi, q_allow_kpa, bbox = synthetic_flight_rasters
        extractor = ZonalFieldExtractor()

        # Define ~2 hectare farm polygon near Kendrapara center
        farm_poly = [
            (86.4150, 20.4950),
            (86.4300, 20.4950),
            (86.4300, 20.5050),
            (86.4150, 20.5050),
            (86.4150, 20.4950),
        ]

        res = extractor.extract_from_rasters(
            polygon_coords=farm_poly,
            aoi_bbox=bbox,
            theta_surf=theta_surf,
            theta_root=theta_root,
            cwsi=cwsi,
            q_allow_kpa=q_allow_kpa,
            crop_name="paddy",
            soil_class="silt_loam",
        )

        assert isinstance(res, ZonalFieldResult)
        assert res.pixel_count > 0, "Pixel count must be strictly positive"
        assert res.area_ha > 0.0, "Farm area in hectares must be positive"
        assert res.area_acres == pytest.approx(res.area_ha * 2.4710538, rel=1e-3)
        assert res.area_m2 == pytest.approx(res.area_ha * 10000.0, rel=1e-3)
        assert len(res.polygon_coordinates) >= 4, "Polygon must be closed"

    def test_zone_02_physical_boundaries_and_zero_nan(self, synthetic_flight_rasters):
        """ZONE-02: Verifies that all statistical distributions are bounded with zero NaNs or Inf."""
        theta_surf, theta_root, cwsi, q_allow_kpa, bbox = synthetic_flight_rasters
        extractor = ZonalFieldExtractor()

        farm_poly = [
            (86.4000, 20.4800),
            (86.4250, 20.4800),
            (86.4250, 20.5000),
            (86.4000, 20.5000),
            (86.4000, 20.4800),
        ]

        res = extractor.extract_from_rasters(
            polygon_coords=farm_poly,
            aoi_bbox=bbox,
            theta_surf=theta_surf,
            theta_root=theta_root,
            cwsi=cwsi,
            q_allow_kpa=q_allow_kpa,
            crop_name="paddy",
            soil_class="silt_loam",
        )

        # Moisture boundaries: [0.05, 0.50]
        assert 0.05 <= res.theta_surf.min <= res.theta_surf.max <= 0.50
        assert 0.05 <= res.theta_root.min <= res.theta_root.max <= 0.50
        assert res.theta_surf.min <= res.theta_surf.mean <= res.theta_surf.max
        assert res.theta_root.min <= res.theta_root.mean <= res.theta_root.max

        # CWSI boundaries: [0.0, 1.0]
        assert 0.0 <= res.cwsi.min <= res.cwsi.max <= 1.0

        # Bearing capacity: [200, 600] kPa
        assert 200.0 <= res.bearing_capacity_kpa.min <= res.bearing_capacity_kpa.max <= 600.0

        # Provenance hash must be valid SHA-256 (64 hex characters)
        assert len(res.sha256_provenance_hash) == 64
        assert int(res.sha256_provenance_hash, 16) > 0

    def test_zone_03_water_volume_conservation(self, synthetic_flight_rasters):
        """ZONE-03: Verifies exact conservation between pixel deficit depth and integrated Litres."""
        theta_surf, theta_root, cwsi, q_allow_kpa, bbox = synthetic_flight_rasters
        extractor = ZonalFieldExtractor()

        farm_poly = [
            (86.4200, 20.5000),
            (86.4400, 20.5000),
            (86.4400, 20.5200),
            (86.4200, 20.5200),
            (86.4200, 20.5000),
        ]

        res = extractor.extract_from_rasters(
            polygon_coords=farm_poly,
            aoi_bbox=bbox,
            theta_surf=theta_surf,
            theta_root=theta_root,
            cwsi=cwsi,
            q_allow_kpa=q_allow_kpa,
            crop_name="paddy",
            soil_class="silt_loam",
        )

        # 1 mm over 100 m² = 100 Litres
        # Total Litres must equal mean_deficit * pixel_count * 100
        expected_litres = res.water_deficit_mm.mean * res.pixel_count * 100.0
        assert res.total_irrigation_prescription_litres == pytest.approx(expected_litres, rel=1e-3)
        assert res.recommended_water_mm_per_ha == pytest.approx(res.water_deficit_mm.mean, rel=1e-3)

    def test_zone_04_execution_latency_sla(self, synthetic_flight_rasters):
        """ZONE-04: Verifies DO-178C SLA: Sub-2ms execution latency for zero-lag interactive drawing."""
        theta_surf, theta_root, cwsi, q_allow_kpa, bbox = synthetic_flight_rasters
        extractor = ZonalFieldExtractor()

        farm_poly = [
            (86.4100, 20.4900),
            (86.4350, 20.4900),
            (86.4450, 20.5100),
            (86.4200, 20.5200),
            (86.4050, 20.5050),
            (86.4100, 20.4900),
        ]

        # Warmup
        _ = extractor.extract_from_rasters(farm_poly, bbox, theta_surf, theta_root, cwsi, q_allow_kpa)

        # Timed Execution (10 consecutive iterations)
        latencies_ms = []
        for _ in range(10):
            t0 = time.perf_counter()
            res = extractor.extract_from_rasters(farm_poly, bbox, theta_surf, theta_root, cwsi, q_allow_kpa)
            latencies_ms.append((time.perf_counter() - t0) * 1000.0)

        mean_latency = float(np.mean(latencies_ms))
        print(f"\n[BENCHMARK] Zonal Extraction Mean Latency: {mean_latency:.3f} ms (SLA: < 2.0 ms)")

        assert mean_latency < 2.0, f"Latency {mean_latency:.3f} ms exceeds 2.0 ms DO-178C SLA"
        assert res.trafficability_grade in ["SAFE_SMOOTH_TILLAGE", "MODERATE_RUT_RISK", "CRITICAL_BOGGING_HAZARD"]
