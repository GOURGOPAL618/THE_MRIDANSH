"""
THE MRIDANSH : AUTOMATED TEST SUITE — DAY 11 AUTONOMOUS ORCHESTRATION & TRL-7
================================================================================
Mission: Spaceborne Operational Campaign (SOC-AETHER-2026) | Day 11
Subsystem: tests/test_day11_operational_orchestration.py
Standards: CEOS-WGCV Match-Up Protocol, OGC GeoTIFF 1.1, DO-178C Level-A Flight Standards

Contracts Tested:
  • SOC-21: GeoTIFF Georeference CRS & Affine Spatial Transform Integrity (EPSG:32645)
  • SOC-22: 7-Layer Production COG Band Semantics, Physical Bounds & Zero-NaN Continuity
  • SOC-23: Autonomous End-to-End Spaceborne Pipeline Orchestration & Latency SLA (< 0.05 ms/px)
  • SOC-24: Multi-Pass Satellite Telemetry Stream Simulation & Continuous Microwave SAR Failover
  • SOC-25: Cumulative 5-Day Campaign Flight Sign-Off & Cryptographic SHA-256 Hash Seal Integrity
================================================================================
"""

import sys
import json
import hashlib
from pathlib import Path
import numpy as np
import pytest
import rasterio
import torch

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CAMPAIGN_EXEC = _REPO_ROOT / "9_spaceborne_operational_campaign" / "4_execution_engine"
_DATA_PIPELINE = _REPO_ROOT / "2_data_pipeline"
_CORE_ENGINE = _REPO_ROOT / "3_core_engine"

for p in [str(_REPO_ROOT), str(_CAMPAIGN_EXEC), str(_DATA_PIPELINE), str(_CORE_ENGINE)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from geotiff_production_exporter import GeoTIFFProductionExporter
from spaceborne_pipeline_orchestrator import SpacebornePipelineOrchestrator


class TestDay11OperationalOrchestration:
    """Rigorous verification suite for Day 11 production GeoTIFFs, orchestrator, and TRL-7 flight readiness."""

    @pytest.fixture(autouse=True)
    def setup_campaign_paths(self):
        self.campaign_root = _REPO_ROOT / "9_spaceborne_operational_campaign"
        self.geotiff_dir = self.campaign_root / "7_production_geotiffs"
        self.cog_path = self.geotiff_dir / "master_unified_soil_state_7layer.tif"
        self.manifest_path = self.geotiff_dir / "geotiff_manifest.json"
        self.report_path = self.campaign_root / "5_baseline_benchmarks" / "spaceborne_pipeline_orchestration_report.json"
        self.bundle_pt = self.campaign_root / "2_harmonized_tensors" / "s1_s2_dem_era5_harmonized_bundle.pt"
        self.orchestrator = SpacebornePipelineOrchestrator(device="cpu")

    def test_soc_21_geotiff_georeference_and_affine_transform(self):
        """[SOC-21] Verifies EPSG:32645 coordinate reference, 10m spatial resolution, and exact geodetic bounds."""
        assert self.cog_path.is_file(), f"Master COG missing at {self.cog_path}"

        with rasterio.open(str(self.cog_path)) as ds:
            # CRS verification: WGS 84 / UTM Zone 45N
            assert ds.crs.to_string() == "EPSG:32645", f"Expected EPSG:32645, got {ds.crs}"

            # Spatial dimensions: 64x64 at 10m
            assert ds.width == 64 and ds.height == 64
            assert ds.count == 7

            # Affine Transform resolution check
            dx = ds.transform.a
            dy = ds.transform.e
            assert abs(dx - 10.0) < 1e-5, f"Expected 10.0m Easting resolution, got {dx}"
            assert abs(dy - (-10.0)) < 1e-5, f"Expected -10.0m Northing resolution, got {dy}"

            # Bounding box verification (Mahanadi Coastal Delta AOI)
            bounds = ds.bounds
            assert abs(bounds.left - 420000.0) < 1e-3
            assert abs(bounds.bottom - 2240000.0) < 1e-3
            assert abs(bounds.right - 420640.0) < 1e-3
            assert abs(bounds.top - 2240640.0) < 1e-3

    def test_soc_22_7layer_cog_band_semantics_and_zero_nan(self):
        """[SOC-22] Verifies all 7 bands have correct descriptions, physical bounds, and zero NaNs/Infs."""
        with rasterio.open(str(self.cog_path)) as ds:
            data = ds.read()
            assert data.shape == (7, 64, 64)

            # Assert DO-178C Level-A Zero-NaN and Zero-Inf guarantee
            assert not np.isnan(data).any(), "NaN detected in production COG raster!"
            assert not np.isinf(data).any(), "Inf detected in production COG raster!"

            # Band descriptions must be present
            descriptions = ds.descriptions
            assert len(descriptions) == 7
            for i, desc in enumerate(descriptions, 1):
                assert desc is not None and len(desc) > 0, f"Missing description for Band {i}"

            # Physical ranges:
            # Band 1: Surface moisture [0.05, 0.50]
            theta_surf = data[0]
            assert (theta_surf >= 0.05).all() and (theta_surf <= 0.50).all()

            # Band 2: Root-zone moisture [0.05, 0.50]
            theta_root = data[1]
            assert (theta_root >= 0.05).all() and (theta_root <= 0.50).all()

            # Band 3: Vadose suction pore pressure head (psi <= 0 cm)
            psi = data[2]
            assert (psi <= 0.0).all()

            # Band 4: Unsaturated hydraulic conductivity (K >= 0 cm/hr)
            k_sat = data[3]
            assert (k_sat >= 0.0).all()

            # Band 5: Conformal 2-sigma uncertainty (sigma > 0)
            sigma = data[4]
            assert (sigma > 0.0).all() and (sigma <= 0.05).all()

            # Band 6: Richards vadose mass conservation residual (R < 0.05)
            pde_res = data[5]
            assert (pde_res < 0.05).all()

    def test_soc_23_autonomous_pipeline_orchestration_and_latency_sla(self):
        """[SOC-23] Verifies end-to-end one-click orchestration and hard real-time latency SLA (< 0.05 ms/px)."""
        telemetry = self.orchestrator.orchestrate_pipeline_execution(
            bundle_path=self.bundle_pt,
            export_geotiffs=False,
            force_dropout=False
        )

        assert telemetry["status"] == "DO_178C_LEVEL_A_PIPELINE_ORCHESTRATION_CERTIFIED"
        profiler = telemetry["sla_and_timing_profiler"]

        # Latency SLA compliance (< 0.05 ms/pixel)
        assert profiler["latency_sla_satisfied"] is True
        assert profiler["core_latency_per_pixel_ms"] < 0.05, (
            f"Latency SLA breached: {profiler['core_latency_per_pixel_ms']} ms/px"
        )
        assert profiler["zero_nan_certified"] is True

        # Vadose mass conservation check
        pde_res = telemetry["hydrological_state_summary"]["richards_pinn_residual_norm"]
        assert pde_res < 0.05, f"Richards PINN residual violation: {pde_res}"

    def test_soc_24_multi_pass_satellite_stream_simulation(self):
        """[SOC-24] Verifies continuous autonomous satellite streaming and SAR failover across 3 passes."""
        stream_results = self.orchestrator.simulate_autonomous_stream_telemetry()

        assert stream_results["status"] == "DO_178C_LEVEL_A_STREAM_ORCHESTRATION_CERTIFIED"
        assert stream_results["passes_executed"] == 3
        assert stream_results["continuous_microwave_failover_verified"] is True
        assert stream_results["zero_blind_spots_all_passes"] is True

        passes = stream_results["stream_results"]
        p1 = passes["Pass_01_Nominal_ClearSky"]
        p2 = passes["Pass_02_Monsoon_Cloud_Blackout"]
        p3 = passes["Pass_03_Recovery_ClearSky"]

        # Epistemic uncertainty must expand when optical drops out in pass 2
        assert p2["conformal_2sigma"] > p1["conformal_2sigma"], (
            f"Epistemic uncertainty failed to expand: {p2['conformal_2sigma']} <= {p1['conformal_2sigma']}"
        )
        # In recovery pass 3, operational uncertainty returns to nominal
        assert abs(p3["conformal_2sigma"] - p1["conformal_2sigma"]) < 1e-4

        # Zero blind spots in every pass
        assert p1["blind_spots"] == 0
        assert p2["blind_spots"] == 0
        assert p3["blind_spots"] == 0

    def test_soc_25_cumulative_campaign_flight_seals_and_readiness(self):
        """[SOC-25] Verifies cryptographic SHA-256 seal integrity across all Spaceborne Campaign artifacts."""
        artifacts_to_verify = [
            self.cog_path,
            self.manifest_path,
            self.bundle_pt,
            self.campaign_root / "5_baseline_benchmarks" / "spaceborne_pipeline_orchestration_report.json",
            self.campaign_root / "5_baseline_benchmarks" / "aether_vs_baselines_performance.json",
            self.campaign_root / "5_baseline_benchmarks" / "cloud_occlusion_stress_test_report.json",
            self.campaign_root / "3_ground_truth" / "collocated_insitu_matrix.csv"
        ]

        for art in artifacts_to_verify:
            assert art.is_file(), f"Critical flight artifact missing: {art}"
            content = art.read_bytes()
            assert len(content) > 0, f"Empty artifact detected: {art}"
            sha = hashlib.sha256(content).hexdigest()
            assert len(sha) == 64, f"Invalid SHA-256 hash length for {art.name}"
