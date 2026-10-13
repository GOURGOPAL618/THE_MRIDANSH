"""
THE MRIDANSH — AETHER-MRID1607X CENTRAL ENGINE
Test Suite: tests/test_van_genuchten.py
Role: Unit Verification for Sprint 5.1 — van Genuchten SWRC Soil Physics Engine

Validates:
  1. Asymptotic Physical Limits (theta -> theta_s as psi -> 0; theta -> theta_r as psi -> inf)
  2. Monotonicity (increasing suction strictly reduces water content)
  3. Round-Trip Inverter Consistency (psi -> theta -> psi_rec with relative error < 1e-4)
  4. PyTorch Differentiability & Autograd Gradients (d_theta/d_psi non-zero, finite, zero NaNs)
  5. Multi-Texture Pedological Profiling across all 5 USDA Soil Types
  6. Ariane-5 Extreme Float Edge Case Protection (psi = 0, 1e-12, 1e8)
"""

import sys
import os
import numpy as np
import torch

# Ensure repository root and 3_core_engine are on path
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_CORE_ENGINE = os.path.join(_REPO_ROOT, "3_core_engine")
if _CORE_ENGINE not in sys.path:
    sys.path.insert(0, _CORE_ENGINE)

from physics.van_genuchten import (
    VanGenuchtenEngine,
    SoilHydraulicParams,
    USDA_SOIL_CATALOG,
    EPSILON
)


def run_van_genuchten_verification():
    print("=" * 80)
    print("      AETHER-MRID1607X : SPRINT 5.1 VAN GENUCHTEN SWRC VERIFICATION")
    print("=" * 80)

    engine = VanGenuchtenEngine('sandy_loam')
    p = engine.params
    print(f"Active Soil Engine: {engine}")

    # -------------------------------------------------------------
    # CHECK 1: Asymptotic Physical Limits
    # -------------------------------------------------------------
    print("\n[CHECK 1] Verifying Asymptotic Physical Limits...")
    # At psi near zero (saturation limit)
    theta_sat = engine.retention(0.0)
    assert abs(theta_sat - p.theta_s) < 1e-4, f"Saturation limit failed: got {theta_sat}, expected {p.theta_s}"

    # At extreme suction (residual limit)
    theta_dry = engine.retention(1e8)
    assert abs(theta_dry - p.theta_r) < 1e-4, f"Dry residual limit failed: got {theta_dry}, expected {p.theta_r}"

    print(f"  -> Saturated limit theta(psi=0):   {theta_sat:.6f} m3/m3 (Target: {p.theta_s:.6f})")
    print(f"  -> Bone-dry limit theta(psi=1e8): {theta_dry:.6f} m3/m3 (Target: {p.theta_r:.6f})")
    print(">>> [PASS] CHECK 1 : Asymptotic Physical Boundaries Verified")

    # -------------------------------------------------------------
    # CHECK 2: Monotonicity Constraint
    # -------------------------------------------------------------
    print("\n[CHECK 2] Verifying Physical Monotonicity (Suction vs Water Content)...")
    suction_heads = np.logspace(-1, 5, 200)
    theta_values = engine.retention(suction_heads)

    # Differential should be strictly non-positive (moisture decreases as suction increases)
    d_theta = np.diff(theta_values)
    violations = np.sum(d_theta > 1e-7)
    assert violations == 0, f"Monotonicity violated at {violations} points!"
    print(f"  -> Tested 200 suction increments across [0.1 cm, 100,000 cm]")
    print(f"  -> Monotonicity Violations: {violations}")
    print(">>> [PASS] CHECK 2 : Monotonicity Strictly Conserved")

    # -------------------------------------------------------------
    # CHECK 3: Round-Trip Inverter Consistency
    # -------------------------------------------------------------
    print("\n[CHECK 3] Verifying Round-Trip Inverter Precision (psi -> theta -> psi_rec)...")
    test_psi = np.array([1.0, 10.0, 50.0, 100.0, 500.0, 1000.0, 5000.0])
    calc_theta = engine.retention(test_psi)
    rec_psi = engine.suction_head(calc_theta)

    rel_error = np.abs(rec_psi - test_psi) / test_psi
    max_rel_err = np.max(rel_error)
    assert max_rel_err < 1e-4, f"Round-trip error exceeded budget: max rel error = {max_rel_err:.2e}"
    print(f"  -> Tested 7 suction points: {test_psi.tolist()}")
    print(f"  -> Reconstructed Suction:   {[round(x, 2) for x in rec_psi.tolist()]}")
    print(f"  -> Max Relative Inverter Error: {max_rel_err:.2e} (Threshold: <= 1.00e-04)")
    print(">>> [PASS] CHECK 3 : Round-Trip Inverter Conservation Verified")

    # -------------------------------------------------------------
    # CHECK 4: PyTorch Autograd Differentiability
    # -------------------------------------------------------------
    print("\n[CHECK 4] Verifying PyTorch Differentiability & Autograd Gradients...")
    psi_t = torch.tensor([5.0, 25.0, 100.0, 400.0], dtype=torch.float32, requires_grad=True)
    theta_t = engine.retention(psi_t)
    loss = theta_t.sum()
    loss.backward()

    grad = psi_t.grad
    assert grad is not None, "Gradient graph disconnected!"
    assert torch.isfinite(grad).all(), "NaN or Inf detected in autograd gradients!"
    assert (grad < 0.0).all(), "d_theta/d_psi must be strictly negative for soil retention!"

    # Validate against analytical capacity C(psi)
    c_analytical = engine.capacity(psi_t.detach())
    capacity_diff = torch.abs(torch.abs(grad) - c_analytical).max().item()
    print(f"  -> Autograd Gradients d_theta/d_psi: {grad.tolist()}")
    print(f"  -> Analytical Capacity C(psi):        {c_analytical.tolist()}")
    print(f"  -> Max Difference (|grad| vs C(psi)): {capacity_diff:.2e}")
    assert capacity_diff < 1e-4, f"Gradient does not match analytical derivative! Diff: {capacity_diff}"
    print(">>> [PASS] CHECK 4 : PyTorch Differentiability & Autograd Verified")

    # -------------------------------------------------------------
    # CHECK 5: Multi-Texture USDA Soil Catalog Profiling
    # -------------------------------------------------------------
    print("\n[CHECK 5] Profiling All 5 USDA Soil Catalog Textures...")
    for soil_name in USDA_SOIL_CATALOG.keys():
        s_eng = VanGenuchtenEngine(soil_name)
        mid_psi = 100.0  # 100 cm matric suction head
        th = s_eng.retention(mid_psi)
        k = s_eng.conductivity(th)
        assert s_eng.params.theta_r <= th <= s_eng.params.theta_s
        assert 0.0 <= k <= s_eng.params.Ks
        print(f"  -> [{soil_name.upper():<10}] theta(100cm) = {th:.4f} m3/m3 | K(theta) = {k:.6f} cm/hr (Ks={s_eng.params.Ks})")
    print(">>> [PASS] CHECK 5 : Multi-Texture Physical Catalog Verified")

    # -------------------------------------------------------------
    # CHECK 6: Ariane-5 Extreme Float Robustness Guardrails
    # -------------------------------------------------------------
    print("\n[CHECK 6] Testing Ariane-5 Extreme Float Singularity Protection...")
    extreme_psi = np.array([0.0, 1e-15, 1e-9, 1e9, 1e12])
    extreme_th = engine.retention(extreme_psi)
    assert np.isfinite(extreme_th).all(), "Extreme psi produced non-finite values!"

    extreme_k = engine.conductivity(extreme_th)
    assert np.isfinite(extreme_k).all(), "Extreme conductivity produced non-finite values!"

    print(f"  -> Ingested Extreme Suctions: {extreme_psi.tolist()}")
    print(f"  -> Resulting Moistures:       {[round(x, 4) for x in extreme_th.tolist()]}")
    print(f"  -> Resulting Conductivities:  {[round(x, 6) for x in extreme_k.tolist()]}")
    print(f"  -> Non-finite elements (NaN/Inf): 0")
    print(">>> [PASS] CHECK 6 : Ariane-5 Extreme Float Guardrails Verified")

    print("\n" + "=" * 80)
    print("    ALL 6 / 6 CHECKS PASSED : SPRINT 5.1 (VAN GENUCHTEN) IS SEALED!   ")
    print("=" * 80)


if __name__ == "__main__":
    run_van_genuchten_verification()
