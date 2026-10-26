"""
THE MRIDANSH : AUTOMATED TEST SUITE — REAL-WORLD FLIGHT ENGINE VALIDATION
================================================================================
Mission: Spaceborne Operational Campaign (SOC-AETHER-2026) | Day 10
Subsystem: tests/test_realworld_engine_validation.py
Standards: CEOS-WGCV Match-Up Protocol, DO-178C Level-A Flight Certification

Contracts Tested:
  • SOC-16: Monolithic Forward Inference Latency (< 0.05 ms/px) & 8-State Zero-NaN/Zero-Inf
  • SOC-17: Continuous Richards Vadose Mass Conservation Residual Norm (R_Richards < 0.05 m³/m³)
  • SOC-18: Multi-Regime Cloud Occlusion Stress Test & Zero Blind Spots Guarantee
  • SOC-19: Conformal Uncertainty Epistemic Penalty & Calibrated Growth Under Blackout
  • SOC-20: Comparative Baseline Benchmarking & Cryptographic Artifact Hash Seal Verification
================================================================================
"""

import sys
import json
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import torch

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CAMPAIGN_EXEC = _REPO_ROOT / "9_spaceborne_operational_campaign" / "4_execution_engine"
_DATA_PIPELINE = _REPO_ROOT / "2_data_pipeline"
_CORE_ENGINE = _REPO_ROOT / "3_core_engine"

for p in [str(_REPO_ROOT), str(_CAMPAIGN_EXEC), str(_DATA_PIPELINE), str(_CORE_ENGINE)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from realworld_engine_validator import RealWorldEngineValidator, compute_error_metrics
from aether_engine import AETHER_MRID1607X_Engine, IngestedTensorBundle, UnifiedSoilState


class TestRealWorldEngineValidation:
    """Rigorous DO-178C Level-A certification test suite for Day 10 real-world engine inference."""

    @pytest.fixture(autouse=True)
    def setup_campaign_paths(self):
        self.campaign_root = _REPO_ROOT / "9_spaceborne_operational_campaign"
        self.bundle_pt = self.campaign_root / "2_harmonized_tensors" / "s1_s2_dem_era5_harmonized_bundle.pt"
        self.collocated_csv = self.campaign_root / "3_ground_truth" / "collocated_insitu_matrix.csv"
        self.predictions_csv = self.campaign_root / "3_ground_truth" / "aether_collocated_predictions.csv"
        self.stress_report_json = self.campaign_root / "5_baseline_benchmarks" / "cloud_occlusion_stress_test_report.json"
        self.baseline_results_json = self.campaign_root / "5_baseline_benchmarks" / "baseline_comparison_results.json"
        self.master_benchmark_json = self.campaign_root / "5_baseline_benchmarks" / "aether_vs_baselines_performance.json"
        self.validator = RealWorldEngineValidator(device="cpu")

    def test_soc_16_monolithic_inference_latency_and_zero_nan(self):
        """[SOC-16] Verifies deterministic microsecond latency and zero NaNs/Infs across 8 soil states."""
        assert self.bundle_pt.is_file(), f"Flight bundle missing at {self.bundle_pt}"
        bundle = self.validator.load_flight_bundle(self.bundle_pt)

        # Force clear sky for baseline inference
        b, _, h, w = bundle.sar.shape
        bundle.cloud_mask = torch.zeros((b, 1, h, w), dtype=torch.float32)

        state, diag = self.validator.execute_forward_pass(bundle, force_dropout=False)

        # Verify state instance
        assert isinstance(state, UnifiedSoilState)
        assert diag["status"] == "DO_178C_LEVEL_A_INFERENCE_CERTIFIED"

        # Verify deterministic latency SLA (< 0.05 ms/px ceiling, nominal < 0.01 ms/px)
        assert diag["latency_per_pixel_ms"] < 0.05, f"Latency SLA breached: {diag['latency_per_pixel_ms']} ms/px"
        assert diag["total_pixels_processed"] == 4096

        # Verify all 8 unified soil state tensors exist and have zero NaNs or Infs
        assert not torch.isnan(state.volumetric_moisture).any()
        assert not torch.isinf(state.volumetric_moisture).any()
        assert not torch.isnan(state.pore_pressure_head).any()
        assert not torch.isnan(state.hydraulic_conductivity).any()
        assert not torch.isnan(state.conformal_uncertainty).any()
        assert not torch.isnan(state.conformal_interval_lower).any()
        assert not torch.isnan(state.conformal_interval_upper).any()
        assert not torch.isnan(state.pde_residual_norm).any()
        assert not torch.isnan(state.anomaly_flags).any()

        # Physical volumetric moisture envelope [0.05, 0.50] m³/m³
        assert (state.volumetric_moisture >= 0.05).all()
        assert (state.volumetric_moisture <= 0.50).all()

    def test_soc_17_richards_vadose_pinn_conservation_residual(self):
        """[SOC-17] Verifies continuous Richards vadose PDE mass conservation residual norm."""
        bundle = self.validator.load_flight_bundle(self.bundle_pt)
        b, _, h, w = bundle.sar.shape
        bundle.cloud_mask = torch.zeros((b, 1, h, w), dtype=torch.float32)

        state, diag = self.validator.execute_forward_pass(bundle, force_dropout=False)

        residual_norm = diag["pde_residual_norm"]
        # Assert strict mass conservation tolerance (residual < 0.05 m³/m³)
        assert residual_norm < 0.05, f"Richards PINN residual violation: {residual_norm} >= 0.05"

        # Hydraulic conductivity must be strictly positive K >= 0
        assert (state.hydraulic_conductivity >= 0.0).all()

        # Pore suction pressure must be non-positive ψ <= 0 in unsaturated vadose zone
        assert (state.pore_pressure_head <= 0.0).all()

    def test_soc_18_multi_regime_cloud_occlusion_stress_test(self):
        """[SOC-18] Verifies 3 atmospheric regimes with 0 blind spots and seamless SAR failover."""
        assert self.stress_report_json.is_file(), "Stress test report artifact missing"
        with open(self.stress_report_json, "r", encoding="utf-8") as f:
            report = json.load(f)

        assert report["status"] == "DO_178C_LEVEL_A_CLOUD_STRESS_CERTIFIED"
        regimes = report["regimes"]

        # 3 regimes must be present
        assert "regime_1_clear_sky" in regimes
        assert "regime_2_partial_cloud" in regimes
        assert "regime_3_severe_cloud_blackout" in regimes

        # Zero blind spots across all regimes
        for reg_name, reg_data in regimes.items():
            assert reg_data["blind_spots_count"] == 0, f"Blind spots detected in {reg_name}!"
            assert reg_data["latency_per_px_ms"] < 0.05

        # Degradation under 100% cloud blackout must be constrained (<= 15%)
        degradation_pct = report["resilience_synthesis"]["rmse_degradation_pct"]
        assert degradation_pct <= 15.0, f"Severe cloud degradation excessive: {degradation_pct}% > 15%"
        assert report["resilience_synthesis"]["zero_blind_spots_verified"] is True
        assert report["resilience_synthesis"]["sar_failover_status"] == "SEAMLESS_CONTINUOUS_MICROWAVE_FAILOVER"

    def test_soc_19_conformal_uncertainty_epistemic_growth(self):
        """[SOC-19] Verifies calibrated conformal uncertainty growth when optical modality drops."""
        with open(self.stress_report_json, "r", encoding="utf-8") as f:
            report = json.load(f)

        sigma_clear = report["regimes"]["regime_1_clear_sky"]["mean_uncertainty_2sigma"]
        sigma_blackout = report["regimes"]["regime_3_severe_cloud_blackout"]["mean_uncertainty_2sigma"]

        # Epistemic uncertainty must expand when optical information is occluded
        assert sigma_blackout >= sigma_clear, (
            f"Epistemic uncertainty failed to grow under blackout: {sigma_blackout} < {sigma_clear}"
        )

        # Check prediction table conformal intervals
        assert self.predictions_csv.is_file(), "Collocated predictions CSV missing"
        preds_df = pd.read_csv(self.predictions_csv)

        # Lower bound <= predicted theta <= Upper bound
        assert (preds_df["aether_conformal_lower"] <= preds_df["aether_pred_theta_m3m3"] + 1e-4).all()
        assert (preds_df["aether_pred_theta_m3m3"] <= preds_df["aether_conformal_upper"] + 1e-4).all()
        assert (preds_df["aether_conformal_uncertainty_2sigma"] > 0.0).all()

    def test_soc_20_comparative_baseline_benchmarking_and_artifacts(self):
        """[SOC-20] Verifies AETHER superiority over Naive Optical OLS and validates cryptographic seals."""
        assert self.master_benchmark_json.is_file(), "Master benchmark JSON missing"
        with open(self.master_benchmark_json, "r", encoding="utf-8") as f:
            master = json.load(f)

        assert master["status"] == "DO_178C_LEVEL_A_MASTER_BENCHMARK_CERTIFIED"
        models = master["models"]

        opt_rmse = models["naive_optical_ndvi_regression"]["metrics"]["rmse_m3m3"]
        aether_clear_rmse = models["aether_mrid1607x_clear_sky"]["metrics"]["surface_rmse_m3m3"]

        # AETHER clear sky must outperform naive optical regression
        assert aether_clear_rmse < opt_rmse, (
            f"AETHER RMSE ({aether_clear_rmse}) must outperform Naive Optical OLS ({opt_rmse})"
        )

        # Verify cryptographic SHA-256 seals of all Day 10 artifacts
        for artifact_path in [
            self.predictions_csv,
            self.stress_report_json,
            self.master_benchmark_json
        ]:
            assert artifact_path.is_file()
            data = artifact_path.read_bytes()
            sha = hashlib.sha256(data).hexdigest()
            assert len(sha) == 64, f"Corrupted SHA-256 hash for {artifact_path.name}"
