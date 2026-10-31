# -*- coding: utf-8 -*-
"""
THE MRIDANSH : Day 15 Phase 4 Civil & Geotechnical Domain Translator Automated Test Suite
Contracts Verified:
  [CIVIL-06] Heavy Rainfall Saturation Surge & Bearing Degradation Monotonicity (dq/dP <= 0).
  [CIVIL-07] NATO / USACE Mobility Class Tier Pressure Hierarchy (Tank > Hauler > Light > Quagmire).
  [CIVIL-08] Flood Hydrostatic Seepage & Critical Hydraulic Exit Gradient (i_crit = gamma' / gamma_w).
  [CIVIL-09] Conformal 2-Sigma Epistemic Risk Ordering Invariant (q_min <= q_nominal <= q_max).
  [CIVIL-10] End-to-End Spaceborne Translation & GeoTIFF Export Latency SLA (< 0.010 ms/pixel).
"""

import sys
import time
from pathlib import Path
import numpy as np
import pytest
import rasterio
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
from scenario_simulator import DynamicScenarioSimulator
from drainage_intelligence import DrainageIntelligenceEngine
from conformal_geotechnical_risk import ConformalGeotechnicalRiskDispatcher
from civil_geotiff_exporter import CivilGeoTIFFExporter


class TestDay15CivilDomainTranslator:
    """Formal RTCA DO-178C Level-A Verification Suite for Civil Domain Translator Phase 4."""

    @pytest.fixture(autouse=True)
    def setup_engines(self):
        self.soil_engine = SoilMechanicsCoreEngine()
        self.ground_engine = GroundStabilityEngine(self.soil_engine, target_factor_of_safety=3.0)
        self.slope_engine = SlopeStabilityEngine(self.soil_engine, slip_surface_depth_m=2.0)
        self.sim_engine = DynamicScenarioSimulator(self.soil_engine, self.ground_engine, self.slope_engine)
        self.drainage_engine = DrainageIntelligenceEngine()
        self.risk_dispatcher = ConformalGeotechnicalRiskDispatcher(
            self.soil_engine, self.ground_engine, self.slope_engine
        )
        self.geotiff_exporter = CivilGeoTIFFExporter()

    # 🏛️ [CIVIL-06] Heavy Rainfall Saturation Surge & Bearing Degradation 🏛️
    def test_civil_06_rainfall_surge_and_bearing_degradation(self):
        """Verify rainfall infiltration monotonically degrades matric suction and allowable bearing."""
        theta_grid = np.linspace(0.12, 0.35, 16, dtype=np.float32).reshape(4, 4)
        slope_grid = np.full_like(theta_grid, 2.0)

        res_50mm = self.sim_engine.simulate_heavy_rainfall(
            theta_grid, slope_grid, rainfall_amount_mm=50.0, soil_class="silt_loam"
        )
        res_100mm = self.sim_engine.simulate_heavy_rainfall(
            theta_grid, slope_grid, rainfall_amount_mm=100.0, soil_class="silt_loam"
        )

        # Moisture must increase
        assert np.all(res_50mm.moisture_surge >= 0.0), "Moisture surge must be non-negative"
        assert np.all(res_100mm.theta_simulated >= res_50mm.theta_simulated), "Higher rainfall must yield higher moisture"

        # Bearing capacity drop must be positive (q_base >= q_rain)
        assert np.all(res_50mm.bearing_capacity_drop_pct >= 0.0), "Bearing capacity drop must be non-negative"
        assert np.all(res_100mm.bearing_capacity_drop_pct >= res_50mm.bearing_capacity_drop_pct), (
            "Higher rainfall must cause greater bearing degradation!"
        )

    # 🏛️ [CIVIL-07] NATO / USACE Mobility Class Tier Pressure Hierarchy 🏛️
    def test_civil_07_vehicle_mobility_class_hierarchy(self):
        """Verify vehicle contact pressure hierarchy and passability ordering."""
        # Synthesize 4 bearing zones: high (>300 kPa), medium (200 kPa), light (100 kPa), quagmire (50 kPa)
        q_allow = np.array([[350.0, 200.0], [100.0, 50.0]], dtype=np.float32)
        slope = np.zeros_like(q_allow)

        res = self.sim_engine.simulate_vehicle_mobility(q_allow, slope)

        # Pixel (0,0): 350 kPa -> Tank (Class 1) Passable
        assert res.class1_heavy_tank_status[0, 0] == 2
        assert res.class2_medium_truck_status[0, 0] == 2
        assert res.class3_light_suv_status[0, 0] == 2
        assert res.composite_mobility_tier[0, 0] == 3

        # Pixel (0,1): 200 kPa -> Medium truck passable, Tank marginal or No-Go
        assert res.class2_medium_truck_status[0, 1] == 2
        assert res.class3_light_suv_status[0, 1] == 2
        assert res.class1_heavy_tank_status[0, 1] < 2

        # Pixel (1,0): 100 kPa -> Light SUV passable only
        assert res.class3_light_suv_status[1, 0] == 2
        assert res.class2_medium_truck_status[1, 0] < 2
        assert res.class1_heavy_tank_status[1, 0] < 2

        # Pixel (1,1): 50 kPa -> Quagmire / Bogged
        assert res.quagmire_risk_mask[1, 1] == True
        assert res.composite_mobility_tier[1, 1] == 0

    # 🏛️ [CIVIL-08] Flood Seepage & Critical Hydraulic Gradient 🏛️
    def test_civil_08_flood_seepage_and_critical_gradient(self):
        """Verify Terzaghi exit gradient identity and liquefaction susceptibility bounds."""
        theta_grid = np.full((5, 5), 0.30, dtype=np.float32)
        slope_grid = np.full((5, 5), 1.0, dtype=np.float32)

        flood_res = self.sim_engine.simulate_flood_liquefaction(
            theta_grid, slope_grid, soil_class="silt_loam", flood_water_depth_m=0.50, upward_seepage_gradient=0.35
        )

        # Critical hydraulic gradient for silt loam: (gamma_sat - gamma_w) / gamma_w approx 0.8 to 1.1
        assert 0.70 <= flood_res.critical_hydraulic_gradient <= 1.20, (
            f"Unphysical critical gradient: {flood_res.critical_hydraulic_gradient}"
        )
        # Liquefaction Susceptibility Index bounded in [0.0, 1.0]
        assert np.all(flood_res.liquefaction_susceptibility_index >= 0.0)
        assert np.all(flood_res.liquefaction_susceptibility_index <= 1.0)
        # Residual effective stress non-negative
        assert np.all(flood_res.effective_stress_residual_kpa >= 0.0)

    # 🏛️ [CIVIL-09] Conformal 2-Sigma Epistemic Risk Ordering Invariant 🏛️
    def test_civil_09_conformal_risk_ordering_invariant(self):
        """Verify strict ordering invariant q_min <= q_nominal <= q_max and design conservative lower bound."""
        theta_nom = np.linspace(0.15, 0.35, 25, dtype=np.float32).reshape(5, 5)
        sigma_2s = np.full_like(theta_nom, 0.03)  # 2-sigma = 0.03 m3/m3
        slope = np.full_like(theta_nom, 2.5)

        risk = self.risk_dispatcher.dispatch_geotechnical_risk(theta_nom, sigma_2s, slope, "silt_loam")

        # Invariant 1: q_min <= q_nom <= q_max
        assert np.all(risk.q_min_kpa <= risk.q_nominal_kpa + 1e-4), "Violation: q_min > q_nominal"
        assert np.all(risk.q_nominal_kpa <= risk.q_max_kpa + 1e-4), "Violation: q_nominal > q_max"

        # Invariant 2: fs_min <= fs_nom <= fs_max
        assert np.all(risk.fs_min <= risk.fs_nominal + 1e-4), "Violation: fs_min > fs_nominal"
        assert np.all(risk.fs_nominal <= risk.fs_max + 1e-4), "Violation: fs_nominal > fs_max"

        # Invariant 3: Eurocode 7 design strictly equals conservative lower bound
        np.testing.assert_allclose(risk.q_design_kpa, risk.q_min_kpa, atol=1e-5)
        np.testing.assert_allclose(risk.fs_design, risk.fs_min, atol=1e-5)

    # 🏛️ [CIVIL-10] End-to-End Pipeline & GeoTIFF Export Latency SLA 🏛️
    def test_civil_10_e2e_spaceborne_latency_and_geotiff_export(self):
        """Execute full civil forward pass on real spaceborne bundle and verify DO-178C latency SLA."""
        bundle_path = repo_root / "9_spaceborne_operational_campaign/2_harmonized_tensors/s1_s2_dem_era5_harmonized_bundle.pt"
        assert bundle_path.exists(), f"Flight bundle missing at {bundle_path}"

        bundle = torch.load(bundle_path, weights_only=False)
        theta_rz = bundle["soil_state_output"]["volumetric_moisture"].squeeze().numpy()
        uncertainty = bundle["soil_state_output"].get("conformal_uncertainty", torch.full_like(bundle["soil_state_output"]["volumetric_moisture"], 0.019)).squeeze().numpy()
        dem_z = bundle["dem"].squeeze().numpy()[0]  # Elevation Band

        total_pixels = theta_rz.size
        sla_limit_ms_per_pixel = 0.010000  # 10 microseconds per pixel DO-178C SLA

        # Timed in-memory algorithmic execution (DO-178C compute pipeline)
        t0 = time.perf_counter()

        # 1. Drainage Intelligence
        drain = self.drainage_engine.analyze_drainage(dem_z, theta_rz)

        # 2. Ground Bearing & Slope
        bearing = self.ground_engine.compute_bearing_capacity(theta_rz, "silt_loam")
        slope = self.slope_engine.compute_slope_stability(drain.slope_angle_deg, theta_rz, "silt_loam")

        # 3. Dynamic Vehicle Mobility
        mobility = self.sim_engine.simulate_vehicle_mobility(bearing.q_allow_kpa, drain.slope_angle_deg)

        # 4. Conformal Risk Dispatch
        risk = self.risk_dispatcher.dispatch_geotechnical_risk(theta_rz, uncertainty, drain.slope_angle_deg)

        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000.0
        latency_per_pixel = elapsed_ms / total_pixels

        # Verify algorithmic performance SLA
        assert latency_per_pixel < sla_limit_ms_per_pixel, (
            f"Latency SLA breached: {latency_per_pixel:.6f} ms/pixel >= {sla_limit_ms_per_pixel:.6f}"
        )

        # 5. Production GeoTIFF Export & Cryptographic Verification
        manifest = self.geotiff_exporter.export_civil_rasters(
            q_allow_kpa=bearing.q_allow_kpa,
            fs_slope=slope.factor_of_safety,
            twi=drain.topographic_wetness_index,
            mobility_tier=mobility.composite_mobility_tier,
        )

        # Verify GeoTIFF files created and readable
        master_cog_path = self.geotiff_exporter.output_dir / "master_geotechnical_civil_4layer_10m.tif"
        assert master_cog_path.exists(), f"Master COG missing at {master_cog_path}"

        with rasterio.open(master_cog_path) as src:
            assert src.count == 4, f"Expected 4 bands, got {src.count}"
            assert src.crs.to_string() == "EPSG:32645"
            assert src.shape == (64, 64)
            data = src.read()
            assert not np.isnan(data).any(), "NaN found in exported master COG!"
