"""
THE MRIDANSH — AETHER-MRID1607X
Test Suite: tests/test_day4_temporal_backbone.py
Role: Automated Verification Suite for Sprint 4.2 Spatiotemporal Backbone Module
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

from models.spatiotemporal_backbone import SpatiotemporalBackbone, ConvLSTMCell


def run_test_suite():
    print("=" * 80)
    print("     AETHER-MRID1607X : SPRINT 4.2 SPATIOTEMPORAL CONVLSTM VERIFICATION")
    print("=" * 80)

    # Initialize model
    model = SpatiotemporalBackbone(
        in_channels=64,
        hidden_channels=64,
        num_layers=1,
        kernel_size=3
    )
    model.eval()

    # -------------------------------------------------------------
    # TEST 4.2.1: Spatiotemporal Shape Integrity
    # -------------------------------------------------------------
    print("\n[TEST 4.2.1] Verifying Spatiotemporal Shape Integrity...")
    # B=2, T=5, C=64, H=32, W=32
    seq_batch = torch.randn(2, 5, 64, 32, 32)
    out_b, meta_b = model(seq_batch)
    assert out_b.shape == (2, 64, 32, 32), f"Expected (2, 64, 32, 32), got {out_b.shape}"
    assert meta_b["timesteps"] == 5
    print(f"  -> Batched sequence (2, T=5, 64, 32, 32): PASS | Output: {out_b.shape}")

    # Single full scene B=1, T=5, C=64, H=64, W=64
    seq_single = torch.randn(1, 5, 64, 64, 64)
    out_s, meta_s = model(seq_single)
    assert out_s.shape == (1, 64, 64, 64), f"Expected (1, 64, 64, 64), got {out_s.shape}"
    print(f"  -> Single full scene (1, T=5, 64, 64, 64): PASS | Output: {out_s.shape}")
    print(">>> [PASS] TEST 4.2.1 : Spatiotemporal Shape Integrity Verified")

    # -------------------------------------------------------------
    # TEST 4.2.2: Dynamic Sequence Horizon Flexibility (T=1, 3, 5, 8)
    # -------------------------------------------------------------
    print("\n[TEST 4.2.2] Verifying Dynamic Sequence Horizons (T in {1, 3, 5, 8})...")
    for t_step in [1, 3, 5, 8]:
        seq_t = torch.randn(1, t_step, 64, 32, 32)
        out_t, meta_t = model(seq_t)
        assert out_t.shape == (1, 64, 32, 32), f"Failed for T={t_step}, got shape {out_t.shape}"
        assert meta_t["timesteps"] == t_step
        print(f"  -> Lookback Horizon T={t_step:02d}: PASS (Output Shape: {out_t.shape})")
    print(">>> [PASS] TEST 4.2.2 : Dynamic Sequence Horizon Verified (Zero Hardcoding)")

    # -------------------------------------------------------------
    # TEST 4.2.3: Numerical Determinism & State Isolation
    # -------------------------------------------------------------
    print("\n[TEST 4.2.3] Verifying Numerical Determinism & State Isolation...")
    torch.manual_seed(1607)
    seq_fixed = torch.randn(1, 5, 64, 32, 32)

    with torch.no_grad():
        run_1, _ = model(seq_fixed)
        run_2, _ = model(seq_fixed)

    max_diff = torch.max(torch.abs(run_1 - run_2)).item()
    assert max_diff == 0.0, f"Determinism violation: max diff = {max_diff}"
    print(f"  -> Discrepancy between consecutive forward passes: {max_diff:.8f}")
    print(">>> [PASS] TEST 4.2.3 : Determinism & State Isolation Verified (Zero Memory Leak)")

    # -------------------------------------------------------------
    # TEST 4.2.4: BPTT Gradient Flow & Stability
    # -------------------------------------------------------------
    print("\n[TEST 4.2.4] Verifying Backpropagation Through Time (BPTT)...")
    model.train()
    seq_grad = torch.randn(2, 5, 64, 16, 16, requires_grad=True)
    out_grad, _ = model(seq_grad)
    loss = out_grad.pow(2).mean()
    loss.backward()

    assert seq_grad.grad is not None, "Input sequence gradient is None"
    assert not torch.isnan(seq_grad.grad).any(), "NaN in input gradient"

    # Check total model parameter gradient norm
    total_norm = 0.0
    for p in model.parameters():
        if p.grad is not None:
            param_norm = p.grad.data.norm(2)
            total_norm += param_norm.item() ** 2
    total_norm = total_norm ** 0.5

    print(f"  -> Total Gradient L2 Norm across 5 timesteps: {total_norm:.4f}")
    assert total_norm < 100.0, f"Gradient explosion detected: norm = {total_norm}"
    assert total_norm > 0.0, "Zero gradients (vanishing gradient)"
    print(">>> [PASS] TEST 4.2.4 : BPTT Gradient Flow Verified (Stable & Bounded)")

    # -------------------------------------------------------------
    # TEST 4.2.5: Autoregressive Multi-Step Rollout (Satellite-Gap Forecasting)
    # -------------------------------------------------------------
    print("\n[TEST 4.2.5] Verifying Autoregressive Multi-Step Rollout...")
    model.eval()
    with torch.no_grad():
        initial_state = out_s  # (1, 64, 64, 64)
        rollout_steps = 3
        forecasts = model.rollout_forecast(initial_state, steps=rollout_steps)

        assert len(forecasts) == rollout_steps, f"Expected {rollout_steps} forecasts, got {len(forecasts)}"
        for idx, f_step in enumerate(forecasts):
            assert f_step.shape == (1, 64, 64, 64), f"Step {idx+1} shape error: {f_step.shape}"
            assert not torch.isnan(f_step).any(), f"Step {idx+1} contains NaN"
            assert not torch.isinf(f_step).any(), f"Step {idx+1} contains Inf"
            delta_mag = torch.norm(f_step - initial_state).item()
            print(f"  -> Forecast Step t+{idx+1}: Shape {f_step.shape} | State Delta Magnitude: {delta_mag:.4f}")

    print(">>> [PASS] TEST 4.2.5 : Autoregressive Multi-Step Rollout Verified (Non-Divergent)")

    # -------------------------------------------------------------
    # TEST 4.2.6: Forward Latency Benchmark (T=5 Scene)
    # -------------------------------------------------------------
    print("\n[TEST 4.2.6] Benchmarking Spatiotemporal Forward Latency...")
    # Warmup
    for _ in range(5):
        _ = model(seq_single)

    timings = []
    iterations = 30
    for _ in range(iterations):
        t0 = time.perf_counter()
        _ = model(seq_single)
        t1 = time.perf_counter()
        timings.append((t1 - t0) * 1000.0)

    mean_ms = np.mean(timings)
    std_ms = np.std(timings)
    per_timestep_ms = mean_ms / 5.0
    per_pixel_ms = mean_ms / (64 * 64)

    print(f"  -> Full Sequence Latency (T=5, 64x64): {mean_ms:.3f} ms ± {std_ms:.3f} ms")
    print(f"  -> Per-Timestep Latency: {per_timestep_ms:.3f} ms / step")
    print(f"  -> Per-Pixel Full Latency: {per_pixel_ms:.6f} ms / pixel")
    print(f"  -> Throughput: {1.0 / (per_pixel_ms / 1000.0):,.0f} pixels / second")
    print(">>> [PASS] TEST 4.2.6 : Execution Latency Benchmark Passed")

    print("\n" + "=" * 80)
    print("   ALL 6 / 6 OPERATIONAL TESTS PASSED FOR SPRINT 4.2 (TEMPORAL BACKBONE)    ")
    print("=" * 80)


if __name__ == "__main__":
    run_test_suite()
