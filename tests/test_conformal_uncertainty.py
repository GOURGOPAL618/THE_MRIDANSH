"""
THE MRIDANSH — AETHER-MRID1607X CENTRAL ENGINE
Test Suite: tests/test_conformal_uncertainty.py
Role: Unit Verification for Sprint 5.4 — Conformal Uncertainty Engine & Variance Partitioning

Validates:
  1. Certified Uncertainty Registry Ingestion (uncertainty_registry.pt)
  2. Epistemic vs Aleatoric Variance Conservation: sigma_tot^2 = sigma_aleatoric^2 + sigma_epistemic^2
  3. Pillar 5 Conformal Prediction Coverage Audit: Coverage >= 88.0% (Target: 90.5%, s_width = 0.0162)
  4. Decile Monotonicity Law: r <= -0.90 (High Confidence ==> Lower Error)
  5. Physical Vadose Clamping of Conformal Intervals [0.05, 0.45] m3/m3
"""

import sys
import os
import math
import numpy as np
import torch

# Ensure repository root and 3_core_engine are on path
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_CORE_ENGINE = os.path.join(_REPO_ROOT, "3_core_engine")
if _CORE_ENGINE not in sys.path:
    sys.path.insert(0, _CORE_ENGINE)

from state_estimation.conformal_uncertainty import (
    ConformalUncertaintyEngine,
    UncertaintyComponents,
    ConformalCalibrationResult
)


def run_conformal_uncertainty_verification():
    print("=" * 80)
    print("      AETHER-MRID1607X : SPRINT 5.4 CONFORMAL UNCERTAINTY VERIFICATION")
    print("=" * 80)

    engine = ConformalUncertaintyEngine(
        default_alpha=0.10,
        gamma_confidence=15.0,
        min_moisture_bound=0.05,
        max_moisture_bound=0.45
    )

    # -------------------------------------------------------------
    # CHECK 1: Certified Uncertainty Registry Ingestion
    # -------------------------------------------------------------
    print("\n[CHECK 1] Ingesting Certified Uncertainty Registry Artifact...")
    reg_path = os.path.join(_REPO_ROOT, "5_storage", "registry", "uncertainty_registry.pt")
    assert os.path.exists(reg_path), f"Registry missing at {reg_path}"

    reg = engine.load_certified_registry(reg_path)
    required_keys = ['sigma_ens', 'sigma_sensor', 'sigma_model', 'sigma_gap', 'sigma_total', 'confidence_score', 'calibration']
    for k in required_keys:
        assert k in reg, f"Key {k} missing in registry!"

    print(f"  -> Registry File Loaded:  {reg_path}")
    print(f"  -> Grid Dimensions:       {reg['grid_dimensions']}")
    print(f"  -> Sigma Total Range:     [{reg['sigma_total'].min():.4f}, {reg['sigma_total'].max():.4f}] m3/m3")
    print(f"  -> Confidence Range:      [{reg['confidence_score'].min():.4f}, {reg['confidence_score'].max():.4f}]")
    print(">>> [PASS] CHECK 1 : Certified Registry Ingestion Verified")

    # -------------------------------------------------------------
    # CHECK 2: Epistemic vs Aleatoric Variance Conservation
    # -------------------------------------------------------------
    print("\n[CHECK 2] Auditing Epistemic vs Aleatoric Variance Partitioning...")
    decomp = engine.decompose_variance(
        sigma_ens=reg['sigma_ens'],
        sigma_sensor=reg['sigma_sensor'],
        sigma_model=reg['sigma_model'],
        sigma_gap=reg['sigma_gap']
    )

    # Mathematical identity: var_total = var_aleatoric + var_epistemic
    var_sum = np.square(decomp.sigma_aleatoric) + np.square(decomp.sigma_epistemic)
    var_tot = np.square(decomp.sigma_total)
    max_discrepancy = np.max(np.abs(var_sum - var_tot))

    assert max_discrepancy < 1e-10, f"Variance partition non-conservative! Discrepancy: {max_discrepancy}"
    print(f"  -> Mean Aleatoric Variance Ratio: {decomp.pct_aleatoric.mean():.1f}%")
    print(f"  -> Mean Epistemic Variance Ratio: {decomp.pct_epistemic.mean():.1f}%")
    print(f"  -> Max Variance Conservation Error: {max_discrepancy:.2e} (Threshold: < 1.00e-10)")
    print(">>> [PASS] CHECK 2 : Exact Epistemic & Aleatoric Variance Conservation Verified")

    # -------------------------------------------------------------
    # CHECK 3: Pillar 5 Conformal Calibration Coverage Audit
    # -------------------------------------------------------------
    print("\n[CHECK 3] Auditing Pillar 5 Conformal Calibration Coverage (Nominal 90%)...")
    # Generate evaluation distribution matching Notebook 07 Cell 12
    n_samples = 2500
    rng = np.random.default_rng(202)
    y_true = np.linspace(0.18, 0.36, n_samples)
    sigma_flat = np.tile(reg['sigma_total'].flatten(), int(math.ceil(n_samples / 400)))[:n_samples]
    residuals = rng.normal(0, sigma_flat, size=n_samples)
    y_pred = y_true + residuals

    cal_res = engine.calibrate(y_true, y_pred, sigma_flat, alpha=0.10)

    # Audited Contract Benchmark from Notebook 12 / Table 04:
    # Contract: Coverage >= 88.0% at 90% Nominal (Achieved: 90.5%, s_width = 0.0162)
    contract_coverage = 88.0
    print(f"  -> Calibration Sample Count:   {cal_res.num_calibration_samples}")
    print(f"  -> Nominal Target Coverage:    {cal_res.nominal_coverage:.1f}%")
    print(f"  -> Empirical Achieved Coverage: {cal_res.empirical_coverage:.2f}% (Contract Target: >= {contract_coverage:.1f}%)")
    print(f"  -> Calibrated Quantile q_hat:  {cal_res.calibrated_quantile:.4f}")
    print(f"  -> Mean Interval Width s_width: {cal_res.mean_interval_width:.4f} m3/m3")

    assert cal_res.empirical_coverage >= contract_coverage, f"Coverage failed! {cal_res.empirical_coverage}% < {contract_coverage}%"
    print(">>> [PASS] CHECK 3 : Pillar 5 Conformal Coverage Benchmark Verified (>= 88.0%)")

    # -------------------------------------------------------------
    # CHECK 4: Decile Monotonicity Law (Spread vs Skill)
    # -------------------------------------------------------------
    print("\n[CHECK 4] Verifying Decile Monotonicity (High Confidence ==> Lower Error)...")
    confidences = engine.compute_confidence_score(sigma_flat)
    r_corr, tier_mae = engine.verify_spread_skill_monotonicity(y_true, y_pred, confidences, num_deciles=10)

    contract_corr = -0.90
    print(f"  -> Decile Error Correlation r: {r_corr:.4f} (Benchmark Contract <= {contract_corr:.2f})")
    print(f"  -> High Confidence MAE:        {tier_mae['mae_high']:.4f} m3/m3")
    print(f"  -> Medium Confidence MAE:      {tier_mae['mae_med']:.4f} m3/m3")
    print(f"  -> Low Confidence MAE:         {tier_mae['mae_low']:.4f} m3/m3")

    assert r_corr <= contract_corr, f"Decile correlation failed contract! {r_corr} > {contract_corr}"
    assert tier_mae['mae_high'] < tier_mae['mae_low'], "High confidence must have lower error than low confidence!"
    print(">>> [PASS] CHECK 4 : Decile Monotonicity Strictly Confirmed (r <= -0.90)")

    # -------------------------------------------------------------
    # CHECK 5: Physical Vadose Clamping of Conformal Intervals
    # -------------------------------------------------------------
    print("\n[CHECK 5] Testing Physical Clamping on Conformal Interval Predictions...")
    # Test boundary scenarios (near saturation and near bone-dry)
    y_test_pred = np.array([0.060, 0.250, 0.440])
    y_test_sigma = np.array([0.050, 0.020, 0.050])

    low_bound, up_bound = engine.predict_interval(y_test_pred, y_test_sigma, quantile=2.0)

    assert np.all(low_bound >= 0.05), "Underflow below residual limit!"
    assert np.all(up_bound <= 0.45), "Overflow above porosity limit!"
    assert np.all(low_bound <= up_bound), "Lower bound cannot exceed upper bound!"

    print(f"  -> Point Estimates: {y_test_pred.tolist()}")
    print(f"  -> Lower Intervals: {low_bound.tolist()} (Clamped min: >= 0.05)")
    print(f"  -> Upper Intervals: {up_bound.tolist()} (Clamped max: <= 0.45)")
    print(">>> [PASS] CHECK 5 : Physical Clamping Strictly Enforced on All Intervals")

    print("\n" + "=" * 80)
    print("    ALL 5 / 5 CHECKS PASSED : SPRINT 5.4 (CONFORMAL UNCERTAINTY) IS SEALED!   ")
    print("=" * 80)


if __name__ == "__main__":
    run_conformal_uncertainty_verification()
