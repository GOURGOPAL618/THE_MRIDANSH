# -*- coding: utf-8 -*-
"""
THE MRIDANSH : Day 14 Phase 2 Civil & Geotechnical Domain Translator Automated Test Suite
Contracts Verified:
  [CIVIL-01] Bearing Capacity Positivity & Factor of Safety Invariant (q_ult / q_allow == 3.0).
  [CIVIL-02] Monotonicity of Meyerhof-Hansen Bearing Capacity Factors (Nc, Nq, Ngamma).
  [CIVIL-03] Slope Stability Flat Ground Limit (beta -> 0 => FS >= 1.5) & Hazard Zonation.
  [CIVIL-04] Spaceborne Flight Bundle Numerical Integrity (4,096 pixels, 0 NaNs, 0 Infs).
  [CIVIL-05] Real-Time Processing Latency Performance (< 0.010 ms/pixel DO-178C SLA).
"""

import sys
import time
from pathlib import Path
import numpy as np
import pytest
import torch

# Ensure repo root and civil module dir are on sys.path
repo_root = Path(__file__).resolve().parent.parent
civil_dir = repo_root / "4_domain_translators" / "civil"

for p in [repo_root, civil_dir]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from soil_mechanics_core import SoilMechanicsCoreEngine
from ground_stability_engine import GroundStabilityEngine
from slope_stability_engine import SlopeStabilityEngine


class TestDay14CivilDomainTranslator:
    """Formal RTCA DO-178C Level-A Verification Suite for Civil Domain Translator Phase 2."""

    @pytest.fixture(autouse=True)
    def setup_engines(self):
        self.soil_engine = SoilMechanicsCoreEngine()
        self.ground_engine = GroundStabilityEngine(self.soil_engine, target_factor_of_safety=3.0)
        self.slope_engine = SlopeStabilityEngine(self.soil_engine, slip_surface_depth_m=2.0)

    # ─── [CIVIL-01] Bearing Capacity Positivity & Safety Factor ────────────────
    def test_civil_01_bearing_capacity_and_safety_factor(self):
        """Verify q_ult > 0, q_allow > 0, and exact identity q_ult / q_allow == 3.0."""
        theta_grid = np.linspace(0.08, 0.42, 25, dtype=np.float32).reshape(5, 5)
        
        for sc in ["sand", "silt_loam", "clay"]:
            res = self.ground_engine.compute_bearing_capacity(theta_grid, soil_class=sc)
            assert np.all(res.q_ult_kpa > 0.0), f"Ultimate bearing capacity non-positive for {sc}"
            assert np.all(res.q_allow_kpa > 0.0), f"Allowable bearing capacity non-positive for {sc}"
            
            # Exact Factor of Safety ratio
            ratio = res.q_ult_kpa / res.q_allow_kpa
            assert np.allclose(ratio, 3.0, rtol=1e-5), f"Safety factor ratio {np.mean(ratio)} != 3.0 for {sc}"
            assert res.factor_of_safety == 3.0
            assert res.trafficability_grade in ["HEAVY_RIG_PERMITTED", "LIGHT_VEHICLE_ONLY", "HAZARDOUS_UNSTABLE_SOIL"]

    # ─── [CIVIL-02] Monotonicity of Bearing Factors ────────────────────────────
    def test_civil_02_bearing_capacity_factors_monotonicity(self):
        """Verify dNq/dphi > 0, dNc/dphi >= 0, dNgamma/dphi > 0 across [0, 45] degrees."""
        phi_sweep = np.linspace(0.0, 45.0, 50)
        nq_list, nc_list, ng_list = [], [], []
        
        for phi in phi_sweep:
            factors = self.ground_engine.compute_bearing_capacity_factors(float(phi))
            nq_list.append(factors.Nq)
            nc_list.append(factors.Nc)
            ng_list.append(factors.Ngamma)
            
        nq_arr = np.array(nq_list)
        nc_arr = np.array(nc_list)
        ng_arr = np.array(ng_list)
        
        # Invariants: strictly non-decreasing
        assert np.all(np.diff(nq_arr) >= 0.0), "Nq must be non-decreasing with friction angle!"
        assert np.all(np.diff(nc_arr) >= 0.0), "Nc must be non-decreasing with friction angle!"
        assert np.all(np.diff(ng_arr) >= 0.0), "Ngamma must be non-decreasing with friction angle!"
        assert nq_arr[0] == 1.0, "Nq(0) must equal 1.0"
        assert np.isclose(nc_arr[0], 5.14, atol=1e-2), "Nc(0) must equal Prandtl value 5.14"

    # ─── [CIVIL-03] Slope Stability Flat Ground Limit & Hazard ────────────────
    def test_civil_03_slope_stability_flat_ground_limit(self):
        """Verify flat slope limit beta -> 0 => FS >= 1.5, hazard classification bounds."""
        # Flat slope test
        slope_flat = np.zeros((4, 4), dtype=np.float32)
        theta_mid = np.full((4, 4), 0.25, dtype=np.float32)
        
        res_flat = self.slope_engine.compute_slope_stability(slope_flat, theta_mid, "silt_loam")
        assert np.all(res_flat.factor_of_safety >= 1.5), "Flat ground must have FS >= 1.5!"
        assert np.all(res_flat.hazard_class_raster == 0), "Flat ground must be classified as STABLE (0)"
        
        # Steep slope test (beta = 45 deg) with saturated soil => should produce marginal or hazard
        slope_steep = np.full((4, 4), 45.0, dtype=np.float32)
        theta_wet = np.full((4, 4), 0.40, dtype=np.float32)
        res_steep = self.slope_engine.compute_slope_stability(slope_steep, theta_wet, "silt_loam")
        
        assert np.all(res_steep.factor_of_safety < res_flat.factor_of_safety), "Steep slope must have lower FS than flat ground!"
        assert np.all(np.isin(res_steep.hazard_class_raster, [0, 1, 2]))

    # ─── [CIVIL-04] Spaceborne Flight Bundle Telemetry Integrity ───────────────
    def test_civil_04_spaceborne_telemetry_integrity(self):
        """Execute forward pass on real spaceborne flight bundle and assert 0 NaNs/Infs."""
        bundle_path = repo_root / "9_spaceborne_operational_campaign/2_harmonized_tensors/s1_s2_dem_era5_harmonized_bundle.pt"
        assert bundle_path.exists(), f"Flight bundle missing at {bundle_path}"
        
        bundle = torch.load(bundle_path, weights_only=False)
        theta_rz = bundle["soil_state_output"]["volumetric_moisture"].squeeze().numpy()  # [64, 64]
        dem_slope = bundle["dem"].squeeze().numpy()[1]  # Band 1: Slope in degrees [64, 64]
        
        H, W = theta_rz.shape
        assert (H, W) == (64, 64), f"Expected 64x64 grid, got {(H, W)}"
        
        # Ground Bearing Capacity
        bearing_res = self.ground_engine.compute_bearing_capacity(theta_rz, soil_class="silt_loam")
        assert not np.any(np.isnan(bearing_res.q_ult_kpa))
        assert not np.any(np.isinf(bearing_res.q_ult_kpa))
        assert not np.any(np.isnan(bearing_res.q_allow_kpa))
        assert np.all(bearing_res.q_ult_kpa > 0.0)
        assert np.all(bearing_res.q_allow_kpa > 0.0)
        
        # Slope Stability
        slope_res = self.slope_engine.compute_slope_stability(dem_slope, theta_rz, soil_class="silt_loam")
        assert not np.any(np.isnan(slope_res.factor_of_safety))
        assert not np.any(np.isinf(slope_res.factor_of_safety))
        assert np.all(slope_res.factor_of_safety > 0.0)
        assert slope_res.hazard_summary["total_pixels"] == 4096

    # ─── [CIVIL-05] Real-Time Latency SLA (< 0.010 ms/pixel) ───────────────────
    def test_civil_05_realtime_latency_sla(self):
        """Profile full execution latency and verify safety margin over DO-178C SLA."""
        bundle_path = repo_root / "9_spaceborne_operational_campaign/2_harmonized_tensors/s1_s2_dem_era5_harmonized_bundle.pt"
        bundle = torch.load(bundle_path, weights_only=False)
        theta_rz = bundle["soil_state_output"]["volumetric_moisture"].squeeze().numpy()
        dem_slope = bundle["dem"].squeeze().numpy()[1]
        
        total_pixels = theta_rz.size
        sla_limit_ms_per_pixel = 0.010000  # 10 microseconds per pixel SLA
        
        # Benchmark 5 passes
        latencies = []
        for _ in range(5):
            t0 = time.perf_counter()
            _ = self.ground_engine.compute_bearing_capacity(theta_rz, soil_class="silt_loam")
            _ = self.slope_engine.compute_slope_stability(dem_slope, theta_rz, soil_class="silt_loam")
            t_pass_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(t_pass_ms / total_pixels)
            
        mean_latency = float(np.mean(latencies))
        safety_margin = sla_limit_ms_per_pixel / mean_latency
        
        print(f"\n[BENCHMARK] Mean Civil Combined Latency: {mean_latency:.6f} ms/pixel ({safety_margin:.1f}x Faster than SLA)")
        assert mean_latency < sla_limit_ms_per_pixel, f"Latency {mean_latency} exceeds SLA {sla_limit_ms_per_pixel}"
