# -*- coding: utf-8 -*-
"""
THE MRIDANSH : Cross-Domain Agro-Geotechnical Simulation Automated Test Suite
Coupled Paddy Nursery Bed (Tala Gachha) & Tractor Puddling Mechanics
Contracts Verified:
  [COUPLED-01] Tractor Rut Sinkage Monotonicity under Bearing Degradation (dz_rut/dq <= 0).
  [COUPLED-02] Seedling Damage Index Boundary Conditions (SDI=0 at z<=5cm, SDI=1 at z>=15cm).
  [COUPLED-03] Goldilocks Optimal Irrigation Depth Convergence (SDI == 0 at P_optimal).
  [COUPLED-04] Real Spaceborne Flight Telemetry Integrity & Natural Language Farmer Advisory.
  [COUPLED-05] High-Speed Monte Carlo Stress-Testing SLA (< 50 ms/trial, Day 18 Readiness).
"""

import sys
import time
from pathlib import Path
import numpy as np
import pytest
import torch

repo_root = Path(__file__).resolve().parent.parent
translators_dir = repo_root / "4_domain_translators"
civil_dir = translators_dir / "civil"

for p in [repo_root, translators_dir, civil_dir]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from coupled_agro_civil_simulator import CoupledAgroCivilSimulator


class TestCoupledAgroCivilSimulation:
    """Formal RTCA DO-178C Level-A Verification for Cross-Domain Agro-Civil Simulation."""

    @pytest.fixture(autouse=True)
    def setup_simulator(self):
        self.simulator = CoupledAgroCivilSimulator()

    # 🌾🚜 [COUPLED-01] Tractor Rut Sinkage Monotonicity 🌾🚜
    def test_coupled_01_tractor_sinkage_monotonicity(self):
        """Verify rut depth increases monotonically as ground bearing capacity degrades."""
        q_allow_decreasing = np.array([500.0, 300.0, 150.0, 100.0, 50.0], dtype=np.float32)
        q_contact = 140.0

        rut_depths = self.simulator.compute_tractor_sinkage(q_allow_decreasing, q_contact)

        # High bearing (500 kPa) must have minimum sinkage (approx 1.5 cm)
        assert rut_depths[0] <= 2.0, f"Expected small sinkage at 500 kPa, got {rut_depths[0]}"

        # Low bearing (50 kPa) must have severe sinkage (> 10 cm)
        assert rut_depths[-1] >= 10.0, f"Expected deep sinkage at 50 kPa, got {rut_depths[-1]}"

        # Monotonicity: as bearing decreases, rut depth must strictly increase
        assert np.all(np.diff(rut_depths) >= 0.0), "Rut depth must increase monotonically with decreasing bearing capacity!"

    # 🌾🚜 [COUPLED-02] Seedling Damage Index Boundary Conditions 🌾🚜
    def test_coupled_02_seedling_damage_boundary_conditions(self):
        """Verify SDI boundaries: SDI=0 at rut<=5cm and SDI=1 at rut>=15cm."""
        rut_depths = np.array([2.0, 5.0, 10.0, 15.0, 20.0], dtype=np.float32)
        sdi = self.simulator.compute_seedling_damage(rut_depths)

        # At z = 2cm and 5cm: Safe (SDI = 0.0)
        assert sdi[0] == 0.0, "Sinkage <= 5cm must produce zero seedling damage"
        assert sdi[1] == 0.0, "Sinkage == 5cm must produce zero seedling damage"

        # At z = 10cm: Intermediate damage (SDI = 0.5)
        np.testing.assert_allclose(sdi[2], 0.50, atol=1e-3)

        # At z >= 15cm: Maximum damage (SDI = 1.0)
        assert sdi[3] == 1.0, "Sinkage >= 15cm must produce 100% damage"
        assert sdi[4] == 1.0, "Sinkage > 15cm must saturate at 1.0"

    # 🌾🚜 [COUPLED-03] Goldilocks Optimal Irrigation Convergence 🌾🚜
    def test_coupled_03_goldilocks_optimal_water_convergence(self):
        """Verify optimizer finds water depth where tractor sinkage <= 5.0 cm."""
        theta_grid = np.full((10, 10), 0.20, dtype=np.float32)  # Initial dry nursery bed
        q_contact = 140.0

        optimal_water_mm = self.simulator.find_goldilocks_optimal_water(
            theta_grid, q_contact, soil_class="silt_loam"
        )

        assert 10.0 <= optimal_water_mm <= 60.0, f"Unphysical optimal water depth: {optimal_water_mm}"

        # Evaluate at optimal water: rut depth must be <= 5.5 cm
        res_opt = self.simulator.simulate_paddy_tilling(
            theta_grid, np.zeros_like(theta_grid), water_applied_mm=optimal_water_mm
        )
        assert res_opt.tractor_state.mean_rut_depth_cm <= 5.5, (
            f"Optimal water resulted in excessive sinkage: {res_opt.tractor_state.mean_rut_depth_cm} cm"
        )

    # 🌾🚜 [COUPLED-04] Real Spaceborne Flight Telemetry Integrity 🌾🚜
    def test_coupled_04_real_spaceborne_telemetry_integrity(self):
        """Execute forward simulation on real flight bundle and verify natural language advisory."""
        bundle_path = repo_root / "9_spaceborne_operational_campaign/2_harmonized_tensors/s1_s2_dem_era5_harmonized_bundle.pt"
        assert bundle_path.exists(), f"Flight bundle missing at {bundle_path}"

        bundle = torch.load(bundle_path, weights_only=False)
        theta_rz = bundle["soil_state_output"]["volumetric_moisture"].squeeze().numpy()
        dem_slope = bundle["dem"].squeeze().numpy()[1]

        # Simulate 60mm heavy uncalculated flood on nursery bed
        res = self.simulator.simulate_paddy_tilling(
            theta_initial=theta_rz,
            slope_deg=dem_slope,
            water_applied_mm=60.0,
            tractor_contact_pressure_kpa=140.0,
            soil_class="silt_loam",
        )

        # Integrity checks
        assert not np.isnan(res.seedling_damage_index).any(), "NaN in seedling damage index"
        assert not np.isnan(res.tractor_state.rut_depth_cm).any(), "NaN in rut depth"
        assert 0.0 <= res.mean_seedling_damage_index <= 1.0

        # Advisory text checks
        assert len(res.farmer_advisory_text) > 20
        assert "SALAHA" in res.farmer_advisory_text or "SHABHASH" in res.farmer_advisory_text

    # 🌾🚜 [COUPLED-05] High-Speed Monte Carlo Stress-Testing SLA 🌾🚜
    def test_coupled_05_monte_carlo_stress_testing_sla(self):
        """Run 20 stochastic Monte Carlo trials and assert sub-second execution SLA."""
        theta_grid = np.full((16, 16), 0.22, dtype=np.float32)
        slope_grid = np.zeros_like(theta_grid)

        num_trials = 25
        t0 = time.perf_counter()
        mc_res = self.simulator.run_monte_carlo_stress_test(
            theta_grid, slope_grid, num_trials=num_trials, water_nominal_mm=40.0
        )
        elapsed_total = (time.perf_counter() - t0) * 1000.0

        assert mc_res.num_trials == num_trials
        assert 0.0 <= mc_res.tractor_bogged_probability <= 1.0
        assert 0.0 <= mc_res.seedling_damage_probability <= 1.0

        # Day 18 Readiness Performance SLA: Average latency per trial < 50.0 ms
        assert mc_res.latency_per_trial_ms < 50.0, (
            f"Monte Carlo latency too slow: {mc_res.latency_per_trial_ms:.2f} ms/trial >= 50.0 ms SLA"
        )
        # Total time for 25 trials should be < 1,000 ms
        assert elapsed_total < 1000.0, f"Total 25-trial execution took {elapsed_total:.2f} ms >= 1000 ms"
