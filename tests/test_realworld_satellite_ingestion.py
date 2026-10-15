"""
THE MRIDANSH : DAY 07 AUTOMATED TEST SUITE (SOC-01 TO SOC-05)
================================================================================
Mission: Spaceborne Operational Campaign (SOC-AETHER-2026) | Day 07
Subsystem: tests/test_realworld_satellite_ingestion.py
Standards: DO-178C Level-A Verification & CEOS-WGCV Ingestion Protocol
================================================================================
"""

import sys
from pathlib import Path
import pytest
import torch

_CURRENT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _CURRENT_DIR.parent
_CAMPAIGN_ROOT = _REPO_ROOT / "9_spaceborne_operational_campaign"
_EXEC_ENGINE = _CAMPAIGN_ROOT / "4_execution_engine"
_CORE_ENGINE = _REPO_ROOT / "3_core_engine"

for p in [str(_REPO_ROOT), str(_CAMPAIGN_ROOT), str(_EXEC_ENGINE), str(_CORE_ENGINE)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from sar_radiometric_calibrator import SarRadiometricCalibrator, MIN_SIGMA0_DB, MAX_SIGMA0_DB
from optical_cloud_preprocessor import OpticalCloudPreprocessor
from realworld_satellite_ingestor import RealWorldSatelliteIngestor
from aether_engine import AETHER_MRID1607X_Engine, IngestedTensorBundle, UnifiedSoilState
from run_day07_field_telemetry import generate_field_telemetry_scene


class TestSpaceborneOperationalIngestion:
    """Formal verification test suite for Day 07 spaceborne ingestion."""

    @pytest.fixture(autouse=True)
    def setup_suite(self):
        self.device = torch.device("cpu")
        self.ingestor = RealWorldSatelliteIngestor(target_resolution_m=10.0, patch_size=64, device=self.device)
        self.scene = generate_field_telemetry_scene(height=128, width=128, cloud_pct=20.0, seed=123)

    def test_soc_01_sar_radiometric_calibration_bounds(self):
        """
        [SOC-01] Verifies Sentinel-1 SAR DN to sigma-nought calibration and strict physical bounding.
        Contract: Output sigma-nought dB must reside strictly in [-35.0 dB, +5.0 dB].
        """
        calibrator = SarRadiometricCalibrator(filter_window=5, nominal_enl=4.9)
        results = calibrator.process_dual_pol_sar(self.scene["raw_s1_vv"], self.scene["raw_s1_vh"])

        sar_db = results["sar_db"]
        assert sar_db.dim() == 4, f"Expected 4D tensor, got {sar_db.dim()}D"
        assert sar_db.shape[1] == 2, f"Expected 2 polarization channels (VV, VH), got {sar_db.shape[1]}"
        assert not torch.isnan(sar_db).any(), "NaN values detected in calibrated SAR tensor!"
        assert not torch.isinf(sar_db).any(), "Inf values detected in calibrated SAR tensor!"

        assert torch.all(sar_db >= MIN_SIGMA0_DB), f"SAR dB dropped below physical floor {MIN_SIGMA0_DB} dB"
        assert torch.all(sar_db <= MAX_SIGMA0_DB), f"SAR dB exceeded physical ceiling {MAX_SIGMA0_DB} dB"

    def test_soc_02_speckle_noise_suppression_enl(self):
        """
        [SOC-02] Verifies Adaptive Refined Lee 5x5 speckle filtering improves Equivalent Number of Looks (ENL).
        Contract: Despeckled ENL must exceed raw ENL (ENL improvement ratio > 1.25x).
        """
        calibrator = SarRadiometricCalibrator(filter_window=5, nominal_enl=4.9)
        results = calibrator.process_dual_pol_sar(self.scene["raw_s1_vv"], self.scene["raw_s1_vh"])

        raw_enl = results["raw_enl"]
        filt_enl = results["filtered_enl"]
        ratio = results["enl_improvement_ratio"]

        assert filt_enl > raw_enl, f"Speckle filter failed to improve ENL: {filt_enl:.2f} <= {raw_enl:.2f}"
        assert ratio >= 1.25, f"ENL gain ratio {ratio:.2f}x below minimum contract 1.25x"

    def test_soc_03_optical_boa_scl_cloud_masking(self):
        """
        [SOC-03] Verifies Sentinel-2 BOA reflectance scaling and SCL cloud mask decoding.
        Contract: Surface reflectance in [0.0, 1.0], clear_mask binary in {0.0, 1.0}, NDVI bounded in [-1.0, 1.0].
        """
        preprocessor = OpticalCloudPreprocessor()
        results = preprocessor.process_optical_bundle(
            raw_b2_blue=self.scene["raw_s2_b2"],
            raw_b3_green=self.scene["raw_s2_b3"],
            raw_b4_red=self.scene["raw_s2_b4"],
            raw_b8_nir=self.scene["raw_s2_b8"],
            raw_scl=self.scene["raw_s2_scl"]
        )

        optical = results["optical"]
        clear_mask = results["clear_mask"]
        ndvi = results["ndvi"]

        assert optical.shape[1] == 4, f"Expected 4 optical channels (B2, B3, B4, B8), got {optical.shape[1]}"
        assert torch.all(optical >= 0.0) and torch.all(optical <= 1.0), "Optical BOA reflectance outside [0.0, 1.0]!"
        assert torch.all((clear_mask == 0.0) | (clear_mask == 1.0)), "Clear sky mask is not strictly binary {0.0, 1.0}!"
        assert torch.all(ndvi >= -1.0) and torch.all(ndvi <= 1.0), "NDVI index outside physical bounds [-1.0, 1.0]!"
        assert results["cloud_fraction_pct"] > 0.0, "Expected non-zero cloud detection on cloudy scene!"

    def test_soc_04_spatial_grid_homogeneity_and_patching(self):
        """
        [SOC-04] Verifies 10m grid co-registration and strict IngestedTensorBundle validation.
        Contract: All modalities aligned to exactly 64x64 patch shape, bundle.validate() passes.
        """
        harmonized = self.ingestor.harmonize_rasters(
            raw_s1_vv=self.scene["raw_s1_vv"],
            raw_s1_vh=self.scene["raw_s1_vh"],
            raw_s2_b2=self.scene["raw_s2_b2"],
            raw_s2_b3=self.scene["raw_s2_b3"],
            raw_s2_b4=self.scene["raw_s2_b4"],
            raw_s2_b8=self.scene["raw_s2_b8"],
            raw_s2_scl=self.scene["raw_s2_scl"],
            raw_dem=self.scene["raw_dem"]
        )

        bundle: IngestedTensorBundle = harmonized["bundle"]
        bundle.validate()  # Strict contract check

        assert bundle.sar.shape == (1, 2, 64, 64), f"Unexpected SAR shape: {bundle.sar.shape}"
        assert bundle.optical.shape == (1, 4, 64, 64), f"Unexpected Optical shape: {bundle.optical.shape}"
        assert bundle.topography.shape == (1, 3, 64, 64), f"Unexpected Topography shape: {bundle.topography.shape}"
        assert bundle.cloud_mask.shape == (1, 1, 64, 64), f"Unexpected Cloud Mask shape: {bundle.cloud_mask.shape}"

        # Verify serialization on disk
        pt_path = self.ingestor.serialize_harmonized_bundle(harmonized)
        assert pt_path.is_file(), f"Serialized tensor bundle not found at {pt_path}"
        assert pt_path.stat().st_size > 10000, "Serialized bundle is suspiciously small"

    def test_soc_05_aether_engine_realworld_inference_handshake(self):
        """
        [SOC-05] Verifies forward execution of real spaceborne tensors through AETHER-MRID1607X.
        Contract: Output UnifiedSoilState verified with zero NaNs, zero Infs, and latency < 0.05 ms/pixel.
        """
        harmonized = self.ingestor.harmonize_rasters(
            raw_s1_vv=self.scene["raw_s1_vv"],
            raw_s1_vh=self.scene["raw_s1_vh"],
            raw_s2_b2=self.scene["raw_s2_b2"],
            raw_s2_b3=self.scene["raw_s2_b3"],
            raw_s2_b4=self.scene["raw_s2_b4"],
            raw_s2_b8=self.scene["raw_s2_b8"],
            raw_s2_scl=self.scene["raw_s2_scl"],
            raw_dem=self.scene["raw_dem"]
        )

        bundle: IngestedTensorBundle = harmonized["bundle"]
        engine = AETHER_MRID1607X_Engine(device=self.device)
        exec_results = self.ingestor.execute_engine_forward_pass(bundle, engine=engine)

        assert exec_results["zero_nan_verified"] is True
        assert exec_results["latency_per_pixel_ms"] < 0.05, f"Latency {exec_results['latency_per_pixel_ms']:.6f} ms/px exceeds SLA limit 0.05 ms/px"
        assert 0.05 <= exec_results["mean_volumetric_moisture"] <= 0.50, f"Unphysical volumetric moisture: {exec_results['mean_volumetric_moisture']}"
        assert exec_results["mean_conformal_sigma"] > 0.0, "Conformal uncertainty must be strictly positive"
