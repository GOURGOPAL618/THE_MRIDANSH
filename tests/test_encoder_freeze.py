"""
THE MRIDANSH — AETHER-MRID1607X CENTRAL ENGINE
Test Suite: tests/test_encoder_freeze.py
Role: Day 4 Master Unit Verification Suite — Neural Encoder Freeze & Dimensionality Audit

Integrates all 3 Day 4 modules:
  1. MultiModalLatentFusion (Sprint 4.1)
  2. SpatiotemporalBackbone (Sprint 4.2)
  3. DynamicDropoutHandler (Sprint 4.3)

Strictly validates:
- Zero-dimensional collapse: Input (B, T, C_raw, H, W) -> Output strict (B, 64, H, W).
- Full channel rank conservation: No dead or zeroed latent channels across 64 dimensions.
- End-to-end 100% optical cloud occlusion fallback resilience.
- End-to-end forward latency benchmark.
"""

import sys
import os
import time
import torch
import numpy as np

# Ensure repository root and 3_core_engine are on Python path
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_CORE_ENGINE = os.path.join(_REPO_ROOT, "3_core_engine")
if _CORE_ENGINE not in sys.path:
    sys.path.insert(0, _CORE_ENGINE)

from models.latent_fusion import MultiModalLatentFusion
from models.spatiotemporal_backbone import SpatiotemporalBackbone
from models.dropout_handler import DynamicDropoutHandler


class Day4IntegratedEncoder(torch.nn.Module):
    """Integrated Day 4 Neural Front-End Pipeline for verification."""

    def __init__(self):
        super(Day4IntegratedEncoder, self).__init__()
        self.fusion = MultiModalLatentFusion(
            sar_channels=3,
            optical_channels=2,
            dem_channels=2,
            latent_dim=64
        )
        self.dropout_handler = DynamicDropoutHandler(latent_fusion_module=self.fusion)
        self.temporal_backbone = SpatiotemporalBackbone(
            in_channels=64,
            hidden_channels=64,
            num_layers=1,
            kernel_size=3
        )

    def forward(
        self,
        sar_seq: torch.Tensor,
        opt_seq: torch.Tensor,
        dem: torch.Tensor,
        cloud_masks: torch.Tensor = None,
        force_dropout: bool = False
    ):
        b, t, _, h, w = sar_seq.shape
        fused_frames = []

        for timestep in range(t):
            c_mask = cloud_masks[:, timestep] if cloud_masks is not None else None
            frame_latent, _ = self.dropout_handler(
                sar=sar_seq[:, timestep],
                optical=opt_seq[:, timestep],
                dem=dem,
                cloud_mask=c_mask,
                force_dropout=force_dropout
            )
            fused_frames.append(frame_latent)

        # Spatiotemporal sequence: (B, T, 64, H, W)
        latent_sequence = torch.stack(fused_frames, dim=1)

        # Process through ConvLSTM Temporal Backbone
        integrated_state, meta = self.temporal_backbone(latent_sequence)
        return integrated_state, meta


def run_encoder_freeze_verification():
    print("=" * 80)
    print("      AETHER-MRID1607X : DAY 4 MASTER NEURAL ENCODER FREEZE VERIFICATION")
    print("=" * 80)

    encoder = Day4IntegratedEncoder()
    encoder.eval()

    # -------------------------------------------------------------
    # VERIFICATION 1: Zero-Dimensional Collapse Check (B x 64 x 64 x 64)
    # -------------------------------------------------------------
    print("\n[VERIFICATION 1] Verifying Zero-Dimensional Collapse on Single Scene...")
    b, t, h, w = 1, 5, 64, 64
    sar_seq = torch.randn(b, t, 3, h, w)
    opt_seq = torch.randn(b, t, 2, h, w)
    dem = torch.randn(b, 2, h, w)

    with torch.no_grad():
        out_state, meta = encoder(sar_seq, opt_seq, dem)

    expected_shape = (b, 64, h, w)
    assert out_state.shape == expected_shape, f"Dimensional Collapse! Expected {expected_shape}, got {out_state.shape}"
    assert out_state.dim() == 4, f"Rank Collapse! Tensor must be 4D (B, C, H, W), got {out_state.dim()}D"
    assert out_state.shape[1] == 64, f"Channel Collapse! Expected 64 channels, got {out_state.shape[1]}"
    print(f"  -> Input Datacube: (B={b}, T={t}, Channels=[3 SAR, 2 Opt, 2 DEM], H={h}, W={w})")
    print(f"  -> Integrated State Output: {out_state.shape}")
    print(">>> [PASS] VERIFICATION 1 : Zero-Dimensional Collapse Strictly Verified (Exact B x 64 x 64 x 64)")

    # -------------------------------------------------------------
    # VERIFICATION 2: Multi-Batch Spatial Scaling Invariance
    # -------------------------------------------------------------
    print("\n[VERIFICATION 2] Verifying Multi-Batch Spatial Scaling Invariance (B=4, H=64, W=64)...")
    b_multi = 4
    sar_multi = torch.randn(b_multi, t, 3, h, w)
    opt_multi = torch.randn(b_multi, t, 2, h, w)
    dem_multi = torch.randn(b_multi, 2, h, w)

    with torch.no_grad():
        out_multi, _ = encoder(sar_multi, opt_multi, dem_multi)

    expected_multi = (b_multi, 64, h, w)
    assert out_multi.shape == expected_multi, f"Batch scaling failed! Expected {expected_multi}, got {out_multi.shape}"
    print(f"  -> Batched Scenes Output: {out_multi.shape}")
    print(">>> [PASS] VERIFICATION 2 : Multi-Batch Scaling Verified (4 x 64 x 64 x 64)")

    # -------------------------------------------------------------
    # VERIFICATION 3: Full Channel Rank Conservation (No Dead Channels)
    # -------------------------------------------------------------
    print("\n[VERIFICATION 3] Verifying Latent Channel Rank & Diversity (No Dead Channels)...")
    # Compute variance across spatial dimensions for each of the 64 channels
    channel_variances = torch.var(out_state[0], dim=(1, 2))  # (64,)
    dead_channels = (channel_variances < 1e-6).sum().item()
    min_var = channel_variances.min().item()
    max_var = channel_variances.max().item()

    assert dead_channels == 0, f"Channel collapse detected: {dead_channels} dead channels!"
    print(f"  -> Total Active Latent Channels: 64 / 64")
    print(f"  -> Dead Channels: {dead_channels}")
    print(f"  -> Channel Variance Range: [{min_var:.6f}, {max_var:.6f}]")
    print(">>> [PASS] VERIFICATION 3 : Full Channel Rank Conservation Verified (64/64 Active)")

    # -------------------------------------------------------------
    # VERIFICATION 4: End-to-End 100% Optical Cloud Occlusion Fallback
    # -------------------------------------------------------------
    print("\n[VERIFICATION 4] Verifying End-to-End 100% Optical Cloud Occlusion Fallback...")
    opt_corrupted = torch.full((b, t, 2, h, w), float('nan'))  # 100% Cloud Blackout with corrupted optical

    with torch.no_grad():
        out_cloud, _ = encoder(sar_seq, opt_corrupted, dem, force_dropout=True)

    assert out_cloud.shape == expected_shape, f"Shape error in cloud fallback: {out_cloud.shape}"
    assert not torch.isnan(out_cloud).any(), "NaN detected in cloud fallback output!"
    assert not torch.isinf(out_cloud).any(), "Inf detected in cloud fallback output!"
    print(f"  -> Corrupted Optical Feed Ingested across all 5 timesteps.")
    print(f"  -> Output Output NaNs = 0 | Shape: {out_cloud.shape} [100% Preserved]")
    print(">>> [PASS] VERIFICATION 4 : 100% Cloud Occlusion Fallback Verified (Zero Blind Spots)")

    # -------------------------------------------------------------
    # VERIFICATION 5: End-to-End Pipeline Latency Benchmark
    # -------------------------------------------------------------
    print("\n[VERIFICATION 5] Benchmarking End-to-End Day 4 Pipeline Latency...")
    # Warmup
    for _ in range(5):
        _ = encoder(sar_seq, opt_seq, dem)

    timings = []
    for _ in range(25):
        t0 = time.perf_counter()
        _ = encoder(sar_seq, opt_seq, dem)
        t1 = time.perf_counter()
        timings.append((t1 - t0) * 1000.0)

    mean_ms = np.mean(timings)
    std_ms = np.std(timings)
    per_pixel_ms = mean_ms / (h * w)

    print(f"  -> End-to-End Full Pipeline Latency (T=5, 64x64): {mean_ms:.3f} ms ± {std_ms:.3f} ms")
    print(f"  -> Per-Pixel Latency: {per_pixel_ms:.6f} ms / pixel")
    print(f"  -> Pipeline Throughput: {1.0 / (per_pixel_ms / 1000.0):,.0f} pixels / second")
    assert mean_ms < 150.0, f"Latency budget exceeded: {mean_ms:.3f} ms"
    print(">>> [PASS] VERIFICATION 5 : Pipeline Latency Benchmark Passed")

    print("\n" + "=" * 80)
    print("    ALL 5 / 5 OPERATIONAL VERIFICATIONS PASSED : DAY 4 ENCODER IS SEALED!   ")
    print("=" * 80)


if __name__ == "__main__":
    run_encoder_freeze_verification()
