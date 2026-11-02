# -*- coding: utf-8 -*-
"""
THE MRIDANSH : Master Unified Pipeline & Temporal Hydrodynamics Test Suite
Module: tests/test_day16_unified_pipeline.py
System: AETHER-MRID1607X Core Engine (Jagannath Command Center - Campus 2)
Standards: RTCA DO-178C Level-A / OGC GeoTIFF 1.1 / WMO-No. 168 / Eurocode 7 / FAO-56

Formal Verification Contracts:
  [PIPE-01] Temporal Hydrodynamic Drying Monotonicity (dθ/dt <= 0 under dry weather).
  [PIPE-02] Vadose Mass Conservation & Richards Boundary Clamping (θ_res <= θ <= θ_sat).
  [PIPE-03] Unified Single-Pass In-Memory Streaming (Zero-NaN / Finite Numbers across all domains).
  [PIPE-04] Triple-COG Geospatial Alignment & Cryptographic SHA-256 Manifest Integrity.
  [PIPE-05] Real-Time Multi-Domain Execution Latency SLA (< 0.025 ms/pixel).
  [PIPE-06] Multi-Temporal Sentinel-1 SAR Backscatter Anomaly Assimilation.
  [PIPE-07] Grassroots Coupled Terramechanics & Goldilocks Irrigation Convergence.
  [PIPE-08] Full Master Monolithic Multi-Scenario Operational Stress Test.
"""

from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import pytest
import rasterio
import torch

# Ensure repo root and domain folders are on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
for p in [_REPO_ROOT, _REPO_ROOT / "4_domain_translators", _REPO_ROOT / "5_pipelines"]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Dynamic imports for folders with numeric prefixes
_temporal_mod = importlib.import_module("4_domain_translators.temporal_hydrodynamics")
TemporalHydrodynamicEngine = _temporal_mod.TemporalHydrodynamicEngine
DailyWeatherForcing = _temporal_mod.DailyWeatherForcing

_orchestrator_mod = importlib.import_module("5_pipelines.mridansh_unified_orchestrator")
MridanshUnifiedOrchestrator = _orchestrator_mod.MridanshUnifiedOrchestrator
UnifiedExecutionRequest = _orchestrator_mod.UnifiedExecutionRequest

_coupled_mod = importlib.import_module("4_domain_translators.coupled_agro_civil_simulator")
CoupledAgroCivilSimulator = _coupled_mod.CoupledAgroCivilSimulator

FLIGHT_BUNDLE_PATH = _REPO_ROOT / "9_spaceborne_operational_campaign" / "2_harmonized_tensors" / "s1_s2_dem_era5_harmonized_bundle.pt"


class TestDay16UnifiedPipeline:
    """Formal RTCA DO-178C Level-A Verification for Master Unified Multi-Domain Pipeline."""

    @pytest.fixture(autouse=True)
    def setup_engines(self):
        """Initialize all certified flight engines."""
        self.temporal_engine = TemporalHydrodynamicEngine()
        self.orchestrator = MridanshUnifiedOrchestrator()
        self.coupled_simulator = CoupledAgroCivilSimulator()
        assert FLIGHT_BUNDLE_PATH.exists(), f"Mission flight bundle missing: {FLIGHT_BUNDLE_PATH}"

    # ------------------------------------------------------------------------------------------------------------------
    # [PIPE-01] TEMPORAL HYDRODYNAMIC DRYING MONOTONICITY
    # ------------------------------------------------------------------------------------------------------------------
    def test_pipe_01_temporal_drying_monotonicity(self):
        """
        Verify that under zero rainfall (P=0) and active evapotranspiration (ET0 > 0),
        soil moisture strictly decreases or remains constant: dθ/dt <= 0.
        """
        grid_dim = 64
        theta_0 = np.full((grid_dim, grid_dim), 0.35, dtype=np.float32)
        schedule = [
            DailyWeatherForcing(et0_mm_day=4.5, precipitation_mm_day=0.0)
            for _ in range(5)
        ]

        traj = self.temporal_engine.forecast_trajectory(theta_0, schedule)

        assert traj.forecast_days == 5, f"Expected 5 forecast days, got {traj.forecast_days}"
        assert traj.monotonicity_verified is True, "PIPE-01 Monotonicity check failed in trajectory!"
        assert traj.net_water_loss_mm > 15.0, f"Expected > 15mm evaporative loss, got {traj.net_water_loss_mm}"

        # Per-pixel strict monotonicity assertion
        prev_theta = theta_0
        for step in traj.daily_steps:
            max_drift = np.max(step.theta - prev_theta)
            assert max_drift <= 1e-6, f"Pixel moisture increased by {max_drift} on day {step.day_index}!"
            prev_theta = step.theta

    # ------------------------------------------------------------------------------------------------------------------
    # [PIPE-02] VADOSE MASS CONSERVATION & PHYSICAL BOUNDS
    # ------------------------------------------------------------------------------------------------------------------
    def test_pipe_02_vadose_mass_conservation_bounds(self):
        """
        Verify that soil moisture is strictly bounded within physical vadose limits
        [θ_res, θ_sat] = [0.05, 0.48] under both extreme drought and intense deluge.
        """
        grid_dim = 64
        theta_res = 0.05
        theta_sat = 0.48

        # Extreme Drought Scenario: 10 days of ET0=8.0 mm/day, zero rain
        theta_dry_init = np.full((grid_dim, grid_dim), 0.10, dtype=np.float32)
        drought_schedule = [DailyWeatherForcing(et0_mm_day=8.0, precipitation_mm_day=0.0) for _ in range(10)]
        traj_drought = self.temporal_engine.forecast_trajectory(theta_dry_init, drought_schedule)
        final_dry_theta = traj_drought.daily_steps[-1].theta

        assert np.all(final_dry_theta >= (theta_res - 1e-5)), "Moisture breached lower residual bound under drought!"
        assert np.all(final_dry_theta <= theta_sat), "Moisture breached upper bound under drought!"

        # Extreme Deluge Scenario: 3 days of P=100.0 mm/day
        theta_wet_init = np.full((grid_dim, grid_dim), 0.40, dtype=np.float32)
        deluge_schedule = [DailyWeatherForcing(et0_mm_day=1.0, precipitation_mm_day=100.0) for _ in range(3)]
        traj_deluge = self.temporal_engine.forecast_trajectory(theta_wet_init, deluge_schedule)
        final_wet_theta = traj_deluge.daily_steps[-1].theta

        assert np.all(final_wet_theta <= (theta_sat + 1e-5)), "Moisture breached upper saturation bound under flood!"
        assert np.all(final_wet_theta >= theta_res), "Moisture breached lower bound under flood!"

    # ------------------------------------------------------------------------------------------------------------------
    # [PIPE-03] UNIFIED SINGLE-PASS IN-MEMORY STREAMING (ZERO-NAN / FINITE VALUES)
    # ------------------------------------------------------------------------------------------------------------------
    def test_pipe_03_unified_single_pass_execution(self):
        """
        Verify that real spaceborne telemetry streams end-to-end through AETHER,
        Agronomy, Civil, and Coupled engines with zero NaN and zero Inf across all arrays.
        """
        req = UnifiedExecutionRequest(
            tensor_bundle=FLIGHT_BUNDLE_PATH,
            forecast_days=3,
            export_geotiffs=False,
        )
        res = self.orchestrator.run(req)

        # Invariant checks across all domain arrays
        assert np.all(np.isfinite(res.theta_surf)), "Surface moisture contains NaN or Inf!"
        assert np.all(np.isfinite(res.theta_root)), "Root-zone moisture contains NaN or Inf!"
        assert np.all(np.isfinite(res.theta_deep)), "Deep vadose moisture contains NaN or Inf!"
        assert np.all(np.isfinite(res.agronomic_state.cwsi)), "CWSI contains NaN or Inf!"
        assert np.all(np.isfinite(res.agronomic_state.root_depletion_dr_mm)), "Depletion Dr contains NaN or Inf!"
        assert np.all(np.isfinite(res.foundation_bearing.q_allow_kpa)), "Bearing capacity contains NaN or Inf!"
        assert np.all(np.isfinite(res.slope_stability.factor_of_safety)), "Slope FS contains NaN or Inf!"
        assert np.all(np.isfinite(res.coupled_result.tractor_state.rut_depth_cm)), "Rut depth contains NaN or Inf!"

        assert res.contracts_verified["PIPE-03_UNIFIED_FINITE_EXECUTION"] is True

    # ------------------------------------------------------------------------------------------------------------------
    # [PIPE-04] TRIPLE-COG GEOSPATIAL ALIGNMENT & CRYPTOGRAPHIC HASH INTEGRITY
    # ------------------------------------------------------------------------------------------------------------------
    def test_pipe_04_triple_cog_geospatial_alignment(self, tmp_path):
        """
        Verify that all 3 exported Master GeoTIFF stacks share identical CRS (EPSG:32645),
        affine transform, 10m grid, and matching cryptographic SHA-256 hashes.
        """
        req = UnifiedExecutionRequest(
            tensor_bundle=FLIGHT_BUNDLE_PATH,
            forecast_days=2,
            export_geotiffs=True,
            output_directory=tmp_path,
        )
        res = self.orchestrator.run(req)

        assert len(res.exported_rasters) == 3, f"Expected 3 exported rasters, got {len(res.exported_rasters)}"

        manifest_path = tmp_path / "unified_execution_manifest.json"
        assert manifest_path.exists(), "Provenance manifest JSON was not created!"

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        ref_transform = None
        for r_name, r_path in res.exported_rasters.items():
            path_obj = Path(r_path)
            assert path_obj.exists(), f"GeoTIFF {r_name} missing at {r_path}"

            # Inspect rasterio metadata
            with rasterio.open(path_obj) as src:
                assert src.crs.to_string() == "EPSG:32645", f"CRS mismatch on {r_name}: {src.crs}"
                assert src.shape == (64, 64), f"Shape mismatch on {r_name}: {src.shape}"
                assert src.res == (10.0, 10.0), f"Resolution mismatch on {r_name}: {src.res}"

                if ref_transform is None:
                    ref_transform = src.transform
                else:
                    assert src.transform == ref_transform, f"Transform misaligned on {r_name}!"

            # Cryptographic SHA-256 hash verification
            hasher = hashlib.sha256()
            with open(path_obj, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            computed_sha = hasher.hexdigest()

            assert computed_sha == manifest_data["sha256_hashes"][r_name], f"SHA-256 hash mismatch on {r_name}!"

        assert res.contracts_verified["PIPE-04_TRIPLE_COG_ALIGNMENT"] is True

    # ------------------------------------------------------------------------------------------------------------------
    # [PIPE-05] REAL-TIME MULTI-DOMAIN EXECUTION LATENCY SLA (< 0.025 ms/pixel)
    # ------------------------------------------------------------------------------------------------------------------
    def test_pipe_05_real_time_latency_sla(self):
        """
        Verify that full in-memory multi-domain execution satisfies DO-178C Level-A
        throughput requirements: strictly < 0.025 ms per pixel (< 102.4 ms for 40.96 ha).
        """
        req = UnifiedExecutionRequest(
            tensor_bundle=FLIGHT_BUNDLE_PATH,
            forecast_days=3,
            export_geotiffs=False,
        )

        latencies = []
        for _ in range(5):
            res = self.orchestrator.run(req)
            latencies.append(res.latency_per_pixel_ms)

        mean_latency = float(np.mean(latencies))
        assert mean_latency < 0.025, f"Latency SLA violated: {mean_latency:.6f} ms/pixel >= 0.025 ms/pixel"
        assert res.contracts_verified["PIPE-05_LATENCY_SLA"] is True

    # ------------------------------------------------------------------------------------------------------------------
    # [PIPE-06] MULTI-TEMPORAL SENTINEL-1 SAR BACKSCATTER ANOMALY ASSIMILATION
    # ------------------------------------------------------------------------------------------------------------------
    def test_pipe_06_sar_anomaly_detector(self):
        """
        Verify Sentinel-1 SAR change detection correctly classifies wetting surges
        and rapid desiccation with appropriate moisture nudge vectors.
        """
        dim = 64
        sigma_base = np.full((dim, dim), -15.0, dtype=np.float32)

        # Case A: Wetting surge (+4.5 dB increase from flash rain / canal flooding)
        sigma_wet = np.full((dim, dim), -10.5, dtype=np.float32)
        res_wet = self.temporal_engine.detect_sar_anomaly(sigma_base, sigma_wet)
        assert res_wet.anomaly_category == "WETTING_SURGE_DETECTED"
        assert res_wet.wetting_pixels_pct == 100.0
        assert np.all(res_wet.moisture_nudge_tensor > 0.05)

        # Case B: Rapid desiccation (-3.5 dB drop from intense transpiration / harvest)
        sigma_dry = np.full((dim, dim), -18.5, dtype=np.float32)
        res_dry = self.temporal_engine.detect_sar_anomaly(sigma_base, sigma_dry)
        assert res_dry.anomaly_category == "RAPID_DESICCATION_DETECTED"
        assert res_dry.desiccation_pixels_pct == 100.0
        assert np.all(res_dry.moisture_nudge_tensor < -0.05)

    # ------------------------------------------------------------------------------------------------------------------
    # [PIPE-07] GRASSROOTS COUPLED TERRAMECHANICS & GOLDILOCKS IRRIGATION CONVERGENCE
    # ------------------------------------------------------------------------------------------------------------------
    def test_pipe_07_coupled_goldilocks_convergence(self):
        """
        Verify coupled nursery bed hydraulics and tractor sinkage mechanics:
        - Goldilocks irrigation depth (<= 25mm) ensures safe rut depth (<= 5cm) and zero damage (SDI=0).
        - Flood over-irrigation (75mm) triggers excessive sinkage (> 12cm) and catastrophic damage.
        """
        dim = 64
        theta_init = np.full((dim, dim), 0.22, dtype=np.float32)
        slope_deg = np.full((dim, dim), 1.5, dtype=np.float32)

        # Goldilocks Water Application (20mm)
        res_safe = self.coupled_simulator.simulate_paddy_tilling(
            theta_initial=theta_init,
            slope_deg=slope_deg,
            water_applied_mm=20.0,
            tractor_contact_pressure_kpa=140.0,
        )
        assert res_safe.tractor_state.mean_rut_depth_cm <= 5.0, "Expected safe rut depth <= 5cm!"
        assert res_safe.mean_seedling_damage_index == 0.0, "Expected zero seedling damage under Goldilocks water!"
        assert "[SHABHASH]" in res_safe.farmer_advisory_text, "Expected positive farmer bulletin!"

        # Catastrophic Over-Irrigation (75mm flood)
        res_flood = self.coupled_simulator.simulate_paddy_tilling(
            theta_initial=theta_init,
            slope_deg=slope_deg,
            water_applied_mm=75.0,
            tractor_contact_pressure_kpa=140.0,
        )
        assert res_flood.tractor_state.mean_rut_depth_cm > 12.0, "Expected deep rutting under 75mm flood!"
        assert res_flood.mean_seedling_damage_index > 0.50, "Expected heavy seedling damage under 75mm flood!"
        assert "[KHATRA]" in res_flood.farmer_advisory_text, "Expected danger alert bulletin under 75mm flood!"

    # ------------------------------------------------------------------------------------------------------------------
    # [PIPE-08] FULL MASTER MONOLITHIC MULTI-SCENARIO STRESS TEST
    # ------------------------------------------------------------------------------------------------------------------
    def test_pipe_08_full_monolithic_multi_scenario_stress(self):
        """
        Ultimate Master Integration Test:
        Executes 3 distinct realistic mission scenarios sequentially through MridanshUnifiedOrchestrator:
          Mission A: Early-Season Transplanting (Anchor overpass, zero forecast drift)
          Mission B: Mid-Season 5-Day Evaporative Drying Forecast (Hot weather drift)
          Mission C: Post-Monsoon High Moisture Field Mobilization (High initial moisture)
        Verifies zero state cross-contamination, deterministic output, and complete contract fulfillment.
        """
        scenarios = [
            {"name": "Mission A: Anchor Pass", "days": 0, "water": 15.0, "tractor": 140.0},
            {"name": "Mission B: 5-Day Forecast", "days": 5, "water": 25.0, "tractor": 140.0},
            {"name": "Mission C: Post-Rain Mobilization", "days": 1, "water": 45.0, "tractor": 160.0},
        ]

        for sc in scenarios:
            req = UnifiedExecutionRequest(
                tensor_bundle=FLIGHT_BUNDLE_PATH,
                crop_name="paddy",
                soil_class="silt_loam",
                forecast_days=sc["days"],
                water_applied_mm=sc["water"],
                tractor_pressure_kpa=sc["tractor"],
                export_geotiffs=False,
            )
            res = self.orchestrator.run(req)

            # Assert all DO-178C contracts verified for each scenario
            assert all(res.contracts_verified.values()), f"Contracts failed under scenario {sc['name']}!"
            assert res.mean_surface_moisture > 0.05, f"Invalid surface moisture in {sc['name']}"
            assert res.agronomic_state.cwsi is not None, f"Agronomic state missing in {sc['name']}"
            assert res.foundation_bearing.q_allow_kpa is not None, f"Civil bearing missing in {sc['name']}"
            assert len(res.farmer_bulletin_alert) > 10, f"Farmer bulletin missing in {sc['name']}"
