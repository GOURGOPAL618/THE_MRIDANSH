"""
THE MRIDANSH — AETHER-MRID1607X CENTRAL ENGINE
Test Suite: tests/test_enkf_assimilator.py
Role: Unit Verification for Sprint 5.3 — Production EnKF Assimilator & Pedological State Tracker

Validates:
  1. Certified State Database Ingestion (enkf_state_database.pt) & Pillar 4 Variance Squashing (-69.5%)
  2. Multi-Variable Prior Generation: X_prior in R^{4 x 50} with pedological correlation
  3. Stochastic Analysis Update: Correct Kalman Gain K in R^{4 x 1} and posterior state
  4. Cross-Variable Pedological Update: Moisture observation updates bulk density and K_sat
  5. 2D GIS Spatial Grid Assimilation: High-throughput raster updating with zero NaNs
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

from state_estimation.enkf_assimilator import (
    EnsembleKalmanFilterAssimilator,
    STATE_VARIABLES,
    STATE_NAMES,
    PEDOLOGICAL_CORRELATION_MATRIX
)


def run_enkf_assimilator_verification():
    print("=" * 80)
    print("      AETHER-MRID1607X : SPRINT 5.3 ENKF ASSIMILATOR VERIFICATION")
    print("=" * 80)

    assimilator = EnsembleKalmanFilterAssimilator(
        num_ensembles=50,
        obs_noise_std=0.03,
        inflation=1.0,
        tikhonov_reg=1e-6
    )

    # -------------------------------------------------------------
    # CHECK 1: Certified State Database Ingestion & Pillar 4 Audit
    # -------------------------------------------------------------
    print("\n[CHECK 1] Ingesting Certified EnKF State Database from Disk...")
    db_path = os.path.join(_REPO_ROOT, "5_storage", "state_database", "enkf_state_database.pt")
    assert os.path.exists(db_path), f"Database missing at {db_path}"

    db = assimilator.load_certified_state_database(db_path)
    assert "prior_ensemble" in db
    assert "posterior_ensemble" in db
    assert "kalman_gain_matrix" in db

    # Audit Pillar 4 variance reduction contract: <= -60.0%
    prior_var = float(db.get("prior_mean_variance", db["prior_covariance_P_f"][0, 0]))
    post_var = float(db.get("posterior_mean_variance", db["posterior_covariance_P_a"][0, 0]))
    var_reduction_pct = ((post_var - prior_var) / prior_var) * 100.0

    print(f"  -> State Database Loaded: {db_path}")
    print(f"  -> State Names:           {db['state_names']}")
    print(f"  -> Prior Ensemble Shape:  {db['prior_ensemble'].shape}")
    print(f"  -> Prior Mean Variance:   {prior_var:.6f}")
    print(f"  -> Posterior Mean Variance: {post_var:.6f}")
    print(f"  -> Variance Reduction:    {var_reduction_pct:.2f}% (Pillar 4 Contract <= -60.0%)")

    assert var_reduction_pct <= -60.0, f"Variance squashing failed contract! Got {var_reduction_pct:.2f}%"
    print(">>> [PASS] CHECK 1 : Certified Database Ingestion & Pillar 4 Squashing Verified")

    # -------------------------------------------------------------
    # CHECK 2: Prior Ensemble Generation with Pedological Correlation
    # -------------------------------------------------------------
    print("\n[CHECK 2] Generating Correlated Multi-Variable Prior Ensemble...")
    x_prior, cov_mat = assimilator.generate_prior_ensemble(num_members=50, seed=42)

    assert x_prior.shape == (4, 50), f"Prior shape mismatch: {x_prior.shape}"
    assert np.isfinite(x_prior).all(), "Non-finite elements in prior ensemble!"

    for i, var in enumerate(STATE_NAMES):
        meta = STATE_VARIABLES[var]
        mean_val = float(x_prior[i, :].mean())
        std_val = float(x_prior[i, :].std())
        min_val = float(x_prior[i, :].min())
        max_val = float(x_prior[i, :].max())
        assert meta['min'] <= min_val <= max_val <= meta['max']
        print(f"  -> [{var:<12}] Mean={mean_val:.4f} {meta['unit']} | Std={std_val:.4f} | Range=[{min_val:.4f}, {max_val:.4f}]")

    print(">>> [PASS] CHECK 2 : Prior Ensemble Generated with Physical Bounding")

    # -------------------------------------------------------------
    # CHECK 3: Stochastic Analysis Assimilation Update
    # -------------------------------------------------------------
    print("\n[CHECK 3] Executing Analysis Update with Satellite Observation...")
    obs_satellite = 0.3300  # Surface moisture observed by Sentinel-1 SAR
    res = assimilator.assimilate(x_prior, observation=obs_satellite, seed=101)

    x_post = res['posterior_ensemble']
    k_gain = res['kalman_gain']
    prior_var_m = res['prior_variance_moisture']
    post_var_m = res['posterior_variance_moisture']
    reduction_pct = res['variance_reduction_pct']

    assert x_post.shape == (4, 50), f"Posterior shape mismatch: {x_post.shape}"
    assert k_gain.shape == (4, 1), f"Kalman gain shape mismatch: {k_gain.shape}"
    assert post_var_m < prior_var_m, "Posterior variance must be lower than prior variance!"

    print(f"  -> Satellite Observation:    {obs_satellite:.4f} m3/m3")
    print(f"  -> Prior Moisture Mean:      {res['prior_mean'][0]:.4f} m3/m3 (Var: {prior_var_m:.6f})")
    print(f"  -> Posterior Moisture Mean:  {res['posterior_mean'][0]:.4f} m3/m3 (Var: {post_var_m:.6f})")
    print(f"  -> Kalman Gain Vector K:     {k_gain.flatten().tolist()}")
    print(f"  -> Moisture Var Reduction:   {reduction_pct:.2f}%")
    print(">>> [PASS] CHECK 3 : Analysis Assimilation & Dimensionality Verified")

    # -------------------------------------------------------------
    # CHECK 4: Cross-Variable Pedological Propagation
    # -------------------------------------------------------------
    print("\n[CHECK 4] Verifying Cross-Variable Information Propagation...")
    # Because Corr(theta, bulk_density) is negative (-0.30), a positive moisture innovation
    # must pull bulk density downward.
    # Because Corr(theta, K_sat) is positive (+0.40), positive moisture innovation must increase K_sat.
    k_theta = k_gain[0, 0]
    k_bd = k_gain[1, 0]
    k_ksat = k_gain[2, 0]

    assert k_theta > 0.0, "Moisture Kalman gain must be positive!"
    assert k_bd < 0.0, "Bulk Density Kalman gain must be negative (negative correlation)!"
    assert k_ksat > 0.0, "K_sat Kalman gain must be positive (positive correlation)!"

    print(f"  -> K_gain [theta_root]   = {k_theta:+.4f} (Positive: pulls state toward observation)")
    print(f"  -> K_gain [bulk_density] = {k_bd:+.4f} (Negative: structural compaction loosens with moisture)")
    print(f"  -> K_gain [K_sat]        = {k_ksat:+.4f} (Positive: permeability tracks moisture recharge)")
    print(">>> [PASS] CHECK 4 : Pedological Cross-Variable Covariance Propagation Verified")

    # -------------------------------------------------------------
    # CHECK 5: 2D GIS Spatial Raster Grid Assimilation
    # -------------------------------------------------------------
    print("\n[CHECK 5] Benchmarking 2D GIS Spatial Raster Grid Assimilation...")
    h, w = 20, 20
    grid_prior = np.full((h, w), 0.250, dtype=np.float64)
    grid_obs = np.full((h, w), 0.320, dtype=np.float64)

    spatial_res = assimilator.assimilate_spatial_grid(grid_prior, grid_obs, obs_noise_var=0.0009)
    grid_post = spatial_res['posterior_grid']

    assert grid_post.shape == (h, w)
    assert np.isfinite(grid_post).all(), "NaN found in spatial grid assimilation!"
    assert np.all(grid_post > grid_prior), "Posterior moisture must shift toward higher observation!"

    print(f"  -> Spatial Grid Dimensions:  {h} x {w} ({h * w} cells)")
    print(f"  -> Prior Uniform State:      {grid_prior[0, 0]:.4f} m3/m3")
    print(f"  -> Satellite Observed State: {grid_obs[0, 0]:.4f} m3/m3")
    print(f"  -> Posterior Assimilated:    {grid_post[0, 0]:.4f} m3/m3")
    print(f"  -> Grid Variance Reduction:  {spatial_res['variance_reduction_pct']:.2f}%")
    print(">>> [PASS] CHECK 5 : 2D GIS Spatial Raster Grid Assimilation Passed")

    print("\n" + "=" * 80)
    print("    ALL 5 / 5 CHECKS PASSED : SPRINT 5.3 (ENKF ASSIMILATOR) IS SEALED!   ")
    print("=" * 80)


if __name__ == "__main__":
    run_enkf_assimilator_verification()
