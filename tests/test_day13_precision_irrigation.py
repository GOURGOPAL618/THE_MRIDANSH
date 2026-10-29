"""
THE MRIDANSH : AUTOMATED TEST SUITE — DAY 13 PRECISION VRI & CONFORMAL RISK DISPATCH
================================================================================
Mission: Phase 4 (Domain Translators & Downstream Intelligence) | Day 13
Subsystem: tests/test_day13_precision_irrigation.py
Standards: United Nations FAO-56, OGC GeoTIFF 1.1, DO-178C Level-A Avionics Rigor

Contracts Tested:
  • AGRI-06: Prescription Volume Non-Negativity (I_net >= 0.0, V_ha >= 0.0, V_px >= 0.0)
  • AGRI-07: Conformal Risk Ordering Invariants (I_min <= I_nominal <= I_max everywhere)
  • AGRI-08: Production GeoTIFF Geospatial & Metadata Integrity (EPSG:32645, 10m, 0 NaNs)
  • AGRI-09: End-to-End Real-Time Latency SLA (< 0.005000 ms/pixel for 64x64 scene)
  • AGRI-10: Monolithic Telemetry Pipeline Consistency & Water Conservation Invariant
================================================================================
"""

import sys
import time
from pathlib import Path
import numpy as np
import pytest
import rasterio
import torch

_REPO_ROOT = Path(__file__).resolve().parent.parent
_AGRI_DIR = _REPO_ROOT / "4_domain_translators" / "agronomy"
_GEOTIFF_DIR = _REPO_ROOT / "9_spaceborne_operational_campaign" / "7_production_geotiffs"

for p in [str(_REPO_ROOT), str(_AGRI_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from irrigation_prescription import (
    PrecisionIrrigationEngine,
    IrrigationStrategy,
    IrrigationSystemType,
    LITERS_PER_HA_PER_MM,
    LITERS_PER_10M_PIXEL_PER_MM,
)
from conformal_risk_dispatcher import ConformalRiskDispatcher, ConformalIrrigationDispatch
from agronomy_domain_engine import AgronomyDomainEngine


class TestDay13PrecisionIrrigation:
    """Rigorous verification suite for Day 13 Precision VRI and Conformal Risk Dispatch."""

    @pytest.fixture(autouse=True)
    def setup_day13_system(self):
        self.vri_engine = PrecisionIrrigationEngine()
        self.risk_dispatcher = ConformalRiskDispatcher(irrigation_engine=self.vri_engine)
        self.agri_engine = AgronomyDomainEngine()
        self.geotiff_dir = _GEOTIFF_DIR
        self.bundle_pt = (
            _REPO_ROOT
            / "9_spaceborne_operational_campaign"
            / "2_harmonized_tensors"
            / "s1_s2_dem_era5_harmonized_bundle.pt"
        )

    def test_agri_06_prescription_volume_non_negativity(self):
        """
        [CONTRACT AGRI-06] Validates that net irrigation depths, gross application volumes (L/ha),
        and pixel-level deliveries (L/pixel) are strictly non-negative under all operational conditions.
        """
        # Test synthetic scenarios spanning negative, zero, and high depletions
        dr_values = np.array([-50.0, -10.0, 0.0, 15.0, 40.0, 80.0, 150.0], dtype=np.float32)
        raw_val = 40.0
        taw_val = 100.0

        for strat in [IrrigationStrategy.STRESS_AVOIDANCE, IrrigationStrategy.FULL_RECHARGE]:
            presc = self.vri_engine.compute_prescription(
                dr_mm=dr_values,
                raw_mm=raw_val,
                taw_mm=taw_val,
                strategy=strat,
            )

            assert np.all(presc.net_irrigation_mm >= 0.0), f"Negative depth in {strat}"
            assert np.all(presc.gross_irrigation_mm >= 0.0), f"Negative gross depth in {strat}"
            assert np.all(presc.liters_per_hectare >= 0.0), f"Negative L/ha in {strat}"
            assert np.all(presc.liters_per_pixel >= 0.0), f"Negative L/pixel in {strat}"
            assert np.all(presc.liters_per_hectare <= taw_val * LITERS_PER_HA_PER_MM / 0.80), "Unbounded volume"

            # Check zero-stress condition: when Dr <= RAW, prescription must be 0 for STRESS_AVOIDANCE
            if strat == IrrigationStrategy.STRESS_AVOIDANCE:
                assert np.all(presc.net_irrigation_mm[:5] == 0.0), "Excess water allocated under non-stressed conditions"

    def test_agri_07_conformal_risk_ordering_invariants(self):
        """
        [CONTRACT AGRI-07] Asserts the fundamental decision-risk invariant:
        I_min <= I_nominal <= I_max and Delta_I >= 0 everywhere across varying uncertainty regimes.
        """
        H, W = 16, 16
        # Generate varied soil moisture field [0.10, 0.35] and uncertainty [0.005, 0.030]
        np.random.seed(1607)
        theta_rz_grid = np.random.uniform(0.12, 0.32, size=(H, W)).astype(np.float32)
        uncertainty_grid = np.random.uniform(0.008, 0.025, size=(H, W)).astype(np.float32)

        dispatch = self.risk_dispatcher.dispatch_risk_bounds(
            theta_rz=theta_rz_grid,
            uncertainty_2sigma=uncertainty_grid,
            theta_fc=0.32,
            theta_wp=0.12,
            theta_sat=0.45,
            z_r_m=0.75,
            raw_mm=45.0,
            taw_mm=110.0,
            strategy=IrrigationStrategy.FULL_RECHARGE,
        )

        assert dispatch.i_min_l_ha.shape == (H, W)
        assert dispatch.i_nominal_l_ha.shape == (H, W)
        assert dispatch.i_max_l_ha.shape == (H, W)
        assert dispatch.risk_spread_l_ha.shape == (H, W)

        # Invariant: I_min <= I_nominal <= I_max
        assert np.all(dispatch.i_min_l_ha <= dispatch.i_nominal_l_ha + 1e-4), "I_min > I_nominal invariant breach"
        assert np.all(dispatch.i_nominal_l_ha <= dispatch.i_max_l_ha + 1e-4), "I_nominal > I_max invariant breach"
        assert np.all(dispatch.risk_spread_l_ha >= 0.0), "Negative risk spread detected"
        assert np.allclose(dispatch.risk_envelope_l_ha, dispatch.risk_spread_l_ha / 2.0), "Risk envelope mismatch"

    def test_agri_08_geotiff_geospatial_and_metadata_integrity(self):
        """
        [CONTRACT AGRI-08] Validates the 4 exported production agronomic GeoTIFF rasters
        and master COG stack for OGC compliance, EPSG:32645 CRS, 10m resolution, and zero NaNs.
        """
        master_cog = self.geotiff_dir / "master_agronomic_vri_4layer_10m.tif"
        if not master_cog.exists():
            master_cog = self.geotiff_dir / "master_agronomic_vri_4layer_10m_target.tif"

        assert master_cog.exists(), f"Master COG missing at {master_cog}"

        with rasterio.open(master_cog) as src:
            assert src.count == 4, f"Expected 4 bands, got {src.count}"
            assert src.crs.to_string() == "EPSG:32645", f"CRS mismatch: {src.crs}"
            assert src.width == 64 and src.height == 64, f"Grid dimensions mismatch: {src.width}x{src.height}"
            assert np.isclose(src.transform[0], 10.0) and np.isclose(abs(src.transform[4]), 10.0), "Resolution not 10m"
            
            # Check bands data integrity
            for b in range(1, 5):
                data = src.read(b)
                assert not np.any(np.isnan(data)), f"DO-178C Violation: NaN found in band {b}"
                assert not np.any(np.isinf(data)), f"DO-178C Violation: Inf found in band {b}"
                assert np.min(data) >= 0.0, f"Negative value in band {b}"

        # Check manifest file
        manifest_path = self.geotiff_dir / "agronomic_geotiff_manifest.json"
        assert manifest_path.exists(), "Manifest missing"

    def test_agri_09_realtime_latency_sla(self):
        """
        [CONTRACT AGRI-09] Asserts that full VRI prescription and conformal 2-sigma risk dispatch
        across a 64x64 scene executes in < 0.005000 ms/pixel.
        """
        H, W = 64, 64
        theta_rz_grid = np.full((H, W), 0.22, dtype=np.float32)
        uncertainty_grid = np.full((H, W), 0.019, dtype=np.float32)

        # Warm-up pass
        _ = self.risk_dispatcher.dispatch_risk_bounds(
            theta_rz=theta_rz_grid,
            uncertainty_2sigma=uncertainty_grid,
            theta_fc=0.33,
            theta_wp=0.13,
            theta_sat=0.45,
            z_r_m=0.60,
            raw_mm=60.0,
            taw_mm=120.0,
        )

        # Timed benchmark pass
        t0 = time.perf_counter()
        dispatch = self.risk_dispatcher.dispatch_risk_bounds(
            theta_rz=theta_rz_grid,
            uncertainty_2sigma=uncertainty_grid,
            theta_fc=0.33,
            theta_wp=0.13,
            theta_sat=0.45,
            z_r_m=0.60,
            raw_mm=60.0,
            taw_mm=120.0,
        )
        elapsed = time.perf_counter() - t0
        latency_px = (elapsed * 1000.0) / (H * W)

        sla_limit = 0.005000  # ms/pixel SLA
        assert latency_px < sla_limit, f"Latency SLA breached: {latency_px:.6f} ms/px >= {sla_limit} ms/px"
        assert dispatch.latency_ms_per_pixel < sla_limit

    def test_agri_10_monolithic_telemetry_pipeline_consistency(self):
        """
        [CONTRACT AGRI-10] Executes end-to-end forward pipeline from spaceborne telemetry
        bundle through agronomic state and conformal VRI dispatch, validating complete system consistency.
        """
        assert self.bundle_pt.exists(), "Flight bundle missing"
        bundle = torch.load(self.bundle_pt, weights_only=False)

        opt_tensor = bundle["optical"].squeeze(0).numpy()
        soil_output = bundle["soil_state_output"]
        theta_surf = soil_output["volumetric_moisture"].squeeze().numpy()
        uncertainty_2sigma = soil_output["conformal_uncertainty"].squeeze().numpy()
        theta_rz = np.clip(theta_surf * 0.95 + 0.01, 0.05, 0.45)

        # 1. Forward agronomy
        agri_state = self.agri_engine.forward(
            optical_reflectance_or_ndvi=opt_tensor,
            theta_surf=theta_surf,
            theta_rz=theta_rz,
            soil_texture="silt_loam",
            crop_name="wheat",
        )

        # 2. Forward conformal risk dispatch
        dispatch = self.risk_dispatcher.dispatch_risk_bounds(
            theta_rz=theta_rz,
            uncertainty_2sigma=uncertainty_2sigma,
            theta_fc=0.33,
            theta_wp=0.13,
            theta_sat=0.45,
            z_r_m=agri_state.root_depth_m,
            raw_mm=agri_state.raw_mm,
            taw_mm=agri_state.taw_mm,
            strategy=IrrigationStrategy.FULL_RECHARGE,
            system_type=IrrigationSystemType.DRIP_MICRO,
        )

        # System consistency checks
        H, W = theta_surf.shape
        assert dispatch.i_nominal_l_ha.shape == (H, W)
        assert np.all(dispatch.i_min_l_ha <= dispatch.i_nominal_l_ha + 1e-4)
        assert np.all(dispatch.i_nominal_l_ha <= dispatch.i_max_l_ha + 1e-4)
        
        # Verify that total prescription volume is bounded by scene water capacity
        total_liters = np.sum(dispatch.i_nominal_l_ha / LITERS_PER_HA_PER_MM * LITERS_PER_10M_PIXEL_PER_MM)
        assert total_liters > 0.0, "Total water requirement must be positive"
        assert total_liters < 50_000_000.0, "Total water volume exceeds physical sanity bound"
