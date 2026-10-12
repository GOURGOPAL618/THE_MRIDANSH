"""
THE MRIDANSH — AETHER-MRID1607X
Test Suite: tests/test_day4_latent_fusion.py
Role: Automated Verification Suite for Sprint 4.1 Latent Fusion Module
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


def run_test_suite():
    print("=" * 80)
    print("      AETHER-MRID1607X : SPRINT 4.1 MULTI-MODAL LATENT FUSION VERIFICATION")
    print("=" * 80)

    # Initialize model
    model = MultiModalLatentFusion(
        sar_channels=3,
        optical_channels=2,
        dem_channels=2,
        latent_dim=64
    )
    model.eval()

    # -------------------------------------------------------------
    # TEST 4.1.1: Tensor Shape Integrity
    # -------------------------------------------------------------
    print("\n[TEST 4.1.1] Verifying Tensor Shape Integrity...")
    sar_1 = torch.randn(1, 3, 64, 64)
    opt_1 = torch.randn(1, 2, 64, 64)
    dem_1 = torch.randn(1, 2, 64, 64)

    out_1, meta_1 = model(sar_1, opt_1, dem_1)
    assert out_1.shape == (1, 64, 64, 64), f"Expected (1, 64, 64, 64), got {out_1.shape}"
    assert meta_1["optical_active"] is True
    print(f"  -> Single scene (1, 64, 64, 64): PASS | Latent Channels: {out_1.shape[1]}")

    # Batched scene
    sar_b = torch.randn(4, 3, 32, 32)
    opt_b = torch.randn(4, 2, 32, 32)
    dem_b = torch.randn(4, 2, 32, 32)
    out_b, _ = model(sar_b, opt_b, dem_b)
    assert out_b.shape == (4, 64, 32, 32), f"Expected (4, 64, 32, 32), got {out_b.shape}"
    print(f"  -> Batched scenes (4, 64, 32, 32): PASS")
    print(">>> [PASS] TEST 4.1.1 : Shape Integrity Verified (Zero Dimensional Collapse)")

    # -------------------------------------------------------------
    # TEST 4.1.2: Gradient Flow & Differentiability
    # -------------------------------------------------------------
    print("\n[TEST 4.1.2] Verifying End-to-End Gradient Flow...")
    model.train()
    sar_grad = torch.randn(2, 3, 32, 32, requires_grad=True)
    opt_grad = torch.randn(2, 2, 32, 32, requires_grad=True)
    dem_grad = torch.randn(2, 2, 32, 32, requires_grad=True)

    out_grad, _ = model(sar_grad, opt_grad, dem_grad)
    loss = out_grad.mean()
    loss.backward()

    assert sar_grad.grad is not None and not torch.isnan(sar_grad.grad).any(), "SAR gradient failed"
    assert opt_grad.grad is not None and not torch.isnan(opt_grad.grad).any(), "Optical gradient failed"
    assert dem_grad.grad is not None and not torch.isnan(dem_grad.grad).any(), "DEM gradient failed"
    print(">>> [PASS] TEST 4.1.2 : Gradient Flow & Differentiability Verified")

    # -------------------------------------------------------------
    # TEST 4.1.3: 100% Optical Cloud Dropout Resilience
    # -------------------------------------------------------------
    print("\n[TEST 4.1.3] Verifying 100% Optical Cloud Occlusion Fallback...")
    model.eval()
    with torch.no_grad():
        sar_drop = torch.randn(2, 3, 64, 64)
        # Even if optical input contains invalid/zeros, dropout handler takes over
        opt_drop = torch.zeros(2, 2, 64, 64)
        dem_drop = torch.randn(2, 2, 64, 64)

        out_drop, meta_drop = model(sar_drop, opt_drop, dem_drop, optical_dropout=True)

        assert out_drop.shape == (2, 64, 64, 64), f"Expected (2, 64, 64, 64), got {out_drop.shape}"
        assert not torch.isnan(out_drop).any(), "NaN detected in cloud occlusion output!"
        assert not torch.isinf(out_drop).any(), "Inf detected in cloud occlusion output!"
        assert meta_drop["optical_active"] is False, "Optical active flag should be False"
        assert meta_drop["optical_dropout_enforced"] is True
        print(f"  -> SAR Boost Factor Active: {meta_drop['sar_boost_factor']:.2f}x")
        print(">>> [PASS] TEST 4.1.3 : 100% Cloud Occlusion Resilience Verified (Zero Blind Spots)")

    # -------------------------------------------------------------
    # TEST 4.1.4: Bit-for-Bit Numerical Determinism
    # -------------------------------------------------------------
    print("\n[TEST 4.1.4] Verifying Numerical Determinism...")
    torch.manual_seed(42)
    s_in = torch.randn(1, 3, 64, 64)
    o_in = torch.randn(1, 2, 64, 64)
    d_in = torch.randn(1, 2, 64, 64)

    with torch.no_grad():
        run_1, _ = model(s_in, o_in, d_in)
        run_2, _ = model(s_in, o_in, d_in)

    max_diff = torch.max(torch.abs(run_1 - run_2)).item()
    assert max_diff == 0.0, f"Determinism violation: max diff = {max_diff}"
    print(f"  -> Maximum discrepancy between identical runs: {max_diff:.8f}")
    print(">>> [PASS] TEST 4.1.4 : Numerical Determinism Verified (Zero Drift)")

    # -------------------------------------------------------------
    # TEST 4.1.5: Forward Pass Latency Benchmark
    # -------------------------------------------------------------
    print("\n[TEST 4.1.5] Benchmarking Forward Pass Execution Latency...")
    # Warmup
    for _ in range(10):
        _ = model(sar_1, opt_1, dem_1)

    timings = []
    iterations = 50
    for _ in range(iterations):
        t0 = time.perf_counter()
        _ = model(sar_1, opt_1, dem_1)
        t1 = time.perf_counter()
        timings.append((t1 - t0) * 1000.0)  # ms

    mean_ms = np.mean(timings)
    std_ms = np.std(timings)
    per_pixel_ms = mean_ms / (64 * 64)

    print(f"  -> Scene Latency (64x64): {mean_ms:.3f} ms ± {std_ms:.3f} ms")
    print(f"  -> Per-Pixel Latency: {per_pixel_ms:.6f} ms / pixel")
    print(f"  -> Throughput: {1.0 / (per_pixel_ms / 1000.0):,.0f} pixels / second")
    assert mean_ms < 20.0, f"Latency budget exceeded: {mean_ms:.3f} ms"
    print(">>> [PASS] TEST 4.1.5 : Execution Latency Benchmark Passed")

    print("\n" + "=" * 80)
    print("   ALL 5 / 5 OPERATIONAL TESTS PASSED FOR SPRINT 4.1 (LATENT FUSION MANIFOLD)  ")
    print("=" * 80)


if __name__ == "__main__":
    run_test_suite()
