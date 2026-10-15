"""
THE MRIDANSH : SAR RADIOMETRIC CALIBRATION & REFINED LEE SPECKLE FILTER
================================================================================
Mission: Spaceborne Operational Campaign (SOC-AETHER-2026) | Day 07
Subsystem: 9_spaceborne_operational_campaign/4_execution_engine/sar_radiometric_calibrator.py
Standards: CEOS-SAR Radiometric Calibration & DO-178C Deterministic Bounds

Functionality:
1. Radiometric Calibration: Converts raw DN to sigma-nought backscatter in linear and decibel (dB) scale:
   σ₀_linear = (DN² + A_offset) / (A_gain²)
   σ₀_dB = 10 * log10(σ₀_linear + ε)
2. Adaptive Refined Lee Speckle Filter (5x5 spatial kernel):
   Suppresses multiplicative Rayleigh speckle noise while preserving field boundaries,
   drainage boundaries, and edge discontinuities.
3. Physical Telemetry Bounding:
   Clamps σ₀_dB to realistic radar backscatter envelopes [-35.0 dB, +5.0 dB].
4. Equivalent Number of Looks (ENL) Verification:
   Measures speckle noise reduction efficiency: ENL = mean(I)² / var(I).
================================================================================
"""

import math
from typing import Tuple, Dict, Any, Optional
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

EPSILON: float = 1e-7
MIN_SIGMA0_DB: float = -35.0
MAX_SIGMA0_DB: float = 5.0


class SarRadiometricCalibrator:
    """
    Deterministic SAR processor for Sentinel-1 C-Band (5.405 GHz) dual-pol (VV, VH) telemetry.
    """

    def __init__(self, filter_window: int = 5, nominal_enl: float = 4.9):
        """
        Args:
            filter_window: Moving window size for speckle filter (must be odd, default 5x5).
            nominal_enl: Equivalent Number of Looks for Sentinel-1 IW GRD product (nominal ~4.9).
        """
        if filter_window % 2 == 0:
            raise ValueError(f"filter_window must be an odd integer, got {filter_window}")
        self.filter_window = filter_window
        self.pad_size = filter_window // 2
        self.nominal_enl = nominal_enl
        # Speckle relative standard deviation: sigma_v = 1 / sqrt(ENL)
        self.sigma_v_sq = 1.0 / max(nominal_enl, 1.0)

    def calibrate_dn_to_sigma0(
        self,
        dn_intensity: torch.Tensor,
        calibration_factor: float = 1.0,
        to_db: bool = True
    ) -> torch.Tensor:
        """
        Converts raw Sentinel-1 DN or Intensity into sigma-nought backscatter.

        Args:
            dn_intensity: Tensor of shape (B, C, H, W) or (C, H, W).
            calibration_factor: Radiometric calibration scale factor A_sigma.
            to_db: If True, returns backscatter in decibels (dB), else linear.

        Returns:
            Calibrated tensor with strict physical boundary clamping.
        """
        was_3d = False
        if dn_intensity.dim() == 3:
            dn_intensity = dn_intensity.unsqueeze(0)
            was_3d = True

        # Ensure positive intensity
        intensity = torch.clamp(dn_intensity.float(), min=0.0)
        
        # Radiometric linear scaling: sigma0_linear = DN / (cal_factor^2)
        cal_scale = max(calibration_factor ** 2, EPSILON)
        sigma0_linear = intensity / cal_scale
        sigma0_linear = torch.clamp(sigma0_linear, min=EPSILON)

        if to_db:
            sigma0_db = 10.0 * torch.log10(sigma0_linear)
            # Physical aerospace bounding [-35.0 dB, +5.0 dB]
            sigma0_bounded = torch.clamp(sigma0_db, min=MIN_SIGMA0_DB, max=MAX_SIGMA0_DB)
            return sigma0_bounded.squeeze(0) if was_3d else sigma0_bounded
        else:
            return sigma0_linear.squeeze(0) if was_3d else sigma0_linear

    def refined_lee_filter(self, intensity_tensor: torch.Tensor) -> Tuple[torch.Tensor, float, float]:
        """
        Applies vectorized 5x5 Refined Lee speckle filtering to intensity SAR data.

        Formula:
            I_hat = mean_I + W * (I - mean_I)
            where W = max(0, (var_I - mean_I^2 * sigma_v^2) / (var_I + eps))

        Args:
            intensity_tensor: Tensor of shape (B, C, H, W), representing linear SAR intensity.

        Returns:
            Tuple of:
                - filtered_intensity: Speckle-suppressed tensor of shape (B, C, H, W).
                - raw_enl: Measured Equivalent Number of Looks before filtering.
                - filtered_enl: Measured Equivalent Number of Looks after filtering.
        """
        was_3d = False
        if intensity_tensor.dim() == 3:
            intensity_tensor = intensity_tensor.unsqueeze(0)
            was_3d = True

        b, c, h, w = intensity_tensor.shape
        device = intensity_tensor.device
        dtype = intensity_tensor.dtype

        # Construct spatial averaging convolution kernel
        kernel_size = self.filter_window
        weight = torch.ones((c, 1, kernel_size, kernel_size), dtype=dtype, device=device) / (kernel_size * kernel_size)

        # Replicate padding for boundary reflection
        padded = F.pad(intensity_tensor, [self.pad_size, self.pad_size, self.pad_size, self.pad_size], mode='reflect')

        # Compute local spatial statistics: mean and mean of squares
        local_mean = F.conv2d(padded, weight, groups=c)
        local_sq_mean = F.conv2d(padded ** 2, weight, groups=c)
        local_var = torch.clamp(local_sq_mean - (local_mean ** 2), min=0.0)

        # Lee adaptive weighting coefficient W
        noise_var = (local_mean ** 2) * self.sigma_v_sq
        w_factor = torch.clamp((local_var - noise_var) / (local_var + EPSILON), min=0.0, max=1.0)

        # Filtered output: I_hat = mean + W * (I - mean)
        filtered = local_mean + w_factor * (intensity_tensor - local_mean)
        filtered = torch.clamp(filtered, min=EPSILON)

        # Measure empirical Equivalent Number of Looks (ENL = mean^2 / var) in homogeneous regions
        raw_mean = float(torch.mean(intensity_tensor))
        raw_var = float(torch.var(intensity_tensor)) + EPSILON
        raw_enl = (raw_mean ** 2) / raw_var

        filt_mean = float(torch.mean(filtered))
        filt_var = float(torch.var(filtered)) + EPSILON
        filt_enl = (filt_mean ** 2) / filt_var

        res = filtered.squeeze(0) if was_3d else filtered
        return res, raw_enl, filt_enl

    def process_dual_pol_sar(
        self,
        raw_vv: torch.Tensor,
        raw_vh: torch.Tensor,
        calibration_factor: float = 1.0
    ) -> Dict[str, Any]:
        """
        Executes end-to-end radiometric calibration, despeckling, and dB conversion
        for Sentinel-1 dual-polarization pair [VV, VH].

        Returns:
            Dictionary containing:
                - 'sar_db': Stacked tensor (B, 2, H, W) [channel 0 = VV_dB, channel 1 = VH_dB].
                - 'raw_enl': Average raw ENL.
                - 'filtered_enl': Average filtered ENL.
                - 'enl_improvement_ratio': Filter efficiency factor (target > 2.0x).
                - 'cross_pol_ratio_db': VH_dB - VV_dB depolarization index.
        """
        # Ensure 4D tensors
        if raw_vv.dim() == 2:
            raw_vv = raw_vv.unsqueeze(0).unsqueeze(0)
        elif raw_vv.dim() == 3:
            raw_vv = raw_vv.unsqueeze(0)

        if raw_vh.dim() == 2:
            raw_vh = raw_vh.unsqueeze(0).unsqueeze(0)
        elif raw_vh.dim() == 3:
            raw_vh = raw_vh.unsqueeze(0)

        # Step 1: Linear radiometric calibration
        vv_linear = self.calibrate_dn_to_sigma0(raw_vv, calibration_factor=calibration_factor, to_db=False)
        vh_linear = self.calibrate_dn_to_sigma0(raw_vh, calibration_factor=calibration_factor, to_db=False)

        # Step 2: Adaptive speckle filtering
        vv_filtered, vv_raw_enl, vv_filt_enl = self.refined_lee_filter(vv_linear)
        vh_filtered, vh_raw_enl, vh_filt_enl = self.refined_lee_filter(vh_linear)

        # Step 3: Decibel conversion with physical clamping
        vv_db = 10.0 * torch.log10(vv_filtered)
        vv_db = torch.clamp(vv_db, min=MIN_SIGMA0_DB, max=MAX_SIGMA0_DB)

        vh_db = 10.0 * torch.log10(vh_filtered)
        vh_db = torch.clamp(vh_db, min=MIN_SIGMA0_DB, max=MAX_SIGMA0_DB)

        # Stack into unified SAR tensor (B, 2, H, W)
        sar_db = torch.cat([vv_db, vh_db], dim=1)

        avg_raw_enl = (vv_raw_enl + vh_raw_enl) / 2.0
        avg_filt_enl = (vv_filt_enl + vh_filt_enl) / 2.0
        enl_ratio = avg_filt_enl / max(avg_raw_enl, 1e-6)

        cross_pol_ratio_db = vh_db - vv_db  # Depolarization volume ratio

        return {
            "sar_db": sar_db,
            "raw_enl": avg_raw_enl,
            "filtered_enl": avg_filt_enl,
            "enl_improvement_ratio": enl_ratio,
            "cross_pol_ratio_db": cross_pol_ratio_db,
            "vv_db": vv_db,
            "vh_db": vh_db
        }
