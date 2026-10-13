"""
THE MRIDANSH — AETHER-MRID1607X CENTRAL ENGINE
Module: 3_core_engine/state_estimation/enkf_assimilator.py
Role: Production Ensemble Kalman Filter (EnKF) Assimilator & Pedological State Tracker

Scientific Formulations:
  - Stochastic Ensemble Kalman Filter (Burgers et al. 1998; Evensen 2003)
  - Multi-variable Pedological State Vector:
      x = [theta_root, bulk_density, K_sat, SOC]^T in R^4
  - Pedological cross-variable empirical correlation matrix.
  - Optimal Kalman Gain with Tikhonov Regularization:
      K = P_f * H^T * (H * P_f * H^T + R + lambda * I)^(-1)
  - Certified Benchmark (Notebook 12 Pillar 4):
      Posterior State Variance Squashing <= -60.0% (Achieved: -69.5%)

Operational Contracts:
  - Direct ingestion of certified database (enkf_state_database.pt).
  - High-throughput 2D spatial grid raster assimilation.
  - Strict physical value clipping & numerical stability guards (Ariane-5 protection).
"""

import os
import math
from typing import Dict, List, Tuple, Union, Optional, Any
import numpy as np
import torch


# Certified Pedological State Variable Definitions
STATE_VARIABLES: Dict[str, Dict[str, Any]] = {
    'theta_root': {
        'name': 'Root-Zone Moisture',
        'unit': 'm3/m3',
        'mean': 0.2753,
        'std': 0.0400,
        'min': 0.0780,
        'max': 0.4300
    },
    'bulk_density': {
        'name': 'Bulk Density',
        'unit': 'g/cm3',
        'mean': 1.3500,
        'std': 0.0800,
        'min': 1.0000,
        'max': 1.8000
    },
    'K_sat': {
        'name': 'Hydraulic Conductivity',
        'unit': 'cm/hr',
        'mean': 1.0400,
        'std': 0.3500,
        'min': 0.0100,
        'max': 10.0000
    },
    'SOC': {
        'name': 'Soil Organic Carbon',
        'unit': '%',
        'mean': 1.2000,
        'std': 0.2500,
        'min': 0.1000,
        'max': 4.0000
    }
}

STATE_NAMES: List[str] = list(STATE_VARIABLES.keys())
NUM_STATES: int = len(STATE_NAMES)

# Empirically Validated Pedological Cross-Variable Correlation Matrix (Notebook 06)
PEDOLOGICAL_CORRELATION_MATRIX: np.ndarray = np.array([
    [ 1.00, -0.30,  0.40,  0.20],   # theta_root
    [-0.30,  1.00, -0.50, -0.65],   # bulk_density
    [ 0.40, -0.50,  1.00,  0.35],   # K_sat
    [ 0.20, -0.65,  0.35,  1.00]    # SOC
], dtype=np.float64)


class EnsembleKalmanFilterAssimilator:
    """
    Production-grade Stochastic Ensemble Kalman Filter Assimilator for pedological soil state estimation.
    Integrates satellite surface moisture observations into deep root-zone multi-variable states.
    """

    def __init__(
        self,
        num_ensembles: int = 50,
        obs_noise_std: float = 0.03,
        inflation: float = 1.0,
        tikhonov_reg: float = 1e-6
    ):
        if num_ensembles < 2:
            raise ValueError(f"num_ensembles must be >= 2, got {num_ensembles}")
        if obs_noise_std <= 0.0:
            raise ValueError(f"obs_noise_std must be positive, got {obs_noise_std}")
        if inflation < 1.0:
            raise ValueError(f"inflation factor must be >= 1.0, got {inflation}")
        if tikhonov_reg < 0.0:
            raise ValueError(f"tikhonov_reg must be non-negative, got {tikhonov_reg}")

        self.num_ensembles = num_ensembles
        self.obs_noise_std = obs_noise_std
        self.inflation = inflation
        self.tikhonov_reg = tikhonov_reg

    def generate_prior_ensemble(
        self,
        num_members: Optional[int] = None,
        seed: int = 42
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generates physically correlated prior state ensemble matrix X_prior in R^{4 x N_ens}.
        """
        n_members = num_members if num_members is not None else self.num_ensembles
        rng = np.random.default_rng(seed)

        means = np.array([STATE_VARIABLES[var]['mean'] for var in STATE_NAMES], dtype=np.float64)
        stds = np.array([STATE_VARIABLES[var]['std'] for var in STATE_NAMES], dtype=np.float64)

        D = np.diag(stds)
        cov_matrix = D @ PEDOLOGICAL_CORRELATION_MATRIX @ D

        # Sample from correlated Multivariate Gaussian
        x_raw = rng.multivariate_normal(means, cov_matrix, size=n_members).T

        # Physical Bounding Clamp
        x_prior = np.zeros_like(x_raw)
        for i, var in enumerate(STATE_NAMES):
            x_prior[i, :] = np.clip(
                x_raw[i, :],
                STATE_VARIABLES[var]['min'],
                STATE_VARIABLES[var]['max']
            )

        return x_prior, cov_matrix

    def assimilate(
        self,
        x_prior: np.ndarray,
        observation: Union[np.ndarray, float],
        obs_cov: Optional[np.ndarray] = None,
        h_operator: Optional[np.ndarray] = None,
        seed: int = 42
    ) -> Dict[str, Any]:
        """
        Executes stochastic EnKF analysis update:
          1. X_f -> Anomaly A_f -> P_f
          2. S = H * P_f * H^T + R + lambda * I
          3. K = P_f * H^T * S^(-1)
          4. Y_p = y + epsilon
          5. X_a = X_f + K * (Y_p - H * X_f)

        Args:
          x_prior: Prior ensemble matrix (N_states, N_ens)
          observation: Observation vector (N_obs,) or scalar float
          obs_cov: Observation error covariance matrix R (N_obs, N_obs)
          h_operator: Observation forward operator H (N_obs, N_states)
          seed: Random seed for reproducible stochastic perturbation

        Returns:
          Dictionary of posterior states, covariances, Kalman Gain, and variance reduction.
        """
        rng = np.random.default_rng(seed)
        num_states, num_members = x_prior.shape

        # Format observation vector y
        if isinstance(observation, (int, float)):
            obs_vec = np.array([float(observation)], dtype=np.float64)
        else:
            obs_vec = np.asarray(observation, dtype=np.float64).flatten()
        num_obs = len(obs_vec)

        # Default Observation Operator: observes first state (theta_root)
        if h_operator is None:
            h_mat = np.zeros((num_obs, num_states), dtype=np.float64)
            h_mat[0, 0] = 1.0
        else:
            h_mat = np.asarray(h_operator, dtype=np.float64)

        # Default Observation Noise Covariance R
        if obs_cov is None:
            r_mat = np.eye(num_obs, dtype=np.float64) * (self.obs_noise_std ** 2.0)
        else:
            r_mat = np.asarray(obs_cov, dtype=np.float64)
            if r_mat.ndim == 1:
                r_mat = np.diag(r_mat)

        # 1. Prior Ensemble Mean and Anomaly Matrix
        x_mean_prior = np.mean(x_prior, axis=1, keepdims=True)
        a_prior = (x_prior - x_mean_prior) * math.sqrt(self.inflation)

        # 2. Sample Prior Covariance Matrix P_f
        p_f = (a_prior @ a_prior.T) / (num_members - 1)

        # 3. Innovation Covariance Matrix S = H P_f H^T + R + lambda * I
        s_mat = h_mat @ p_f @ h_mat.T + r_mat
        if self.tikhonov_reg > 0.0:
            s_mat = s_mat + np.eye(num_obs, dtype=np.float64) * self.tikhonov_reg

        # 4. Optimal Kalman Gain K = P_f H^T S^(-1)
        k_gain = p_f @ h_mat.T @ np.linalg.pinv(s_mat)

        # 5. Stochastic Observation Perturbation (Burgers et al. 1998)
        obs_noise = rng.multivariate_normal(np.zeros(num_obs), r_mat, size=num_members).T
        if obs_noise.ndim == 1:
            obs_noise = obs_noise.reshape(1, -1)
        y_perturbed = obs_vec.reshape(-1, 1) + obs_noise

        # 6. Innovation and Analysis Update
        x_inflated = x_mean_prior + a_prior
        innovation = y_perturbed - (h_mat @ x_inflated)
        x_post_raw = x_inflated + k_gain @ innovation

        # Physical Bounds Enforcement
        x_posterior = np.zeros_like(x_post_raw)
        for i, var in enumerate(STATE_NAMES):
            x_posterior[i, :] = np.clip(
                x_post_raw[i, :],
                STATE_VARIABLES[var]['min'],
                STATE_VARIABLES[var]['max']
            )

        # 7. Posterior Covariance Matrix P_a
        x_mean_post = np.mean(x_posterior, axis=1, keepdims=True)
        a_post = x_posterior - x_mean_post
        p_a = (a_post @ a_post.T) / (num_members - 1)

        # Variance Squashing Metrics
        prior_var_moisture = float(p_f[0, 0])
        post_var_moisture = float(p_a[0, 0])
        var_reduction_pct = ((post_var_moisture - prior_var_moisture) / max(prior_var_moisture, 1e-8)) * 100.0

        return {
            'posterior_ensemble': x_posterior,
            'posterior_mean': x_mean_post.flatten(),
            'prior_mean': x_mean_prior.flatten(),
            'prior_covariance_P_f': p_f,
            'posterior_covariance_P_a': p_a,
            'kalman_gain': k_gain,
            'innovation': innovation,
            'prior_variance_moisture': prior_var_moisture,
            'posterior_variance_moisture': post_var_moisture,
            'variance_reduction_pct': var_reduction_pct
        }

    def assimilate_spatial_grid(
        self,
        prior_grid: np.ndarray,
        obs_grid: np.ndarray,
        obs_noise_var: float = 0.0009
    ) -> Dict[str, Any]:
        """
        Vectorized 2D spatial raster grid assimilation for GIS maps (H, W).
        Computes cell-by-cell scalar Kalman update:
          x_post = x_prior + K * (y_obs - x_prior)
          K = var_prior / (var_prior + var_obs)
        """
        h, w = prior_grid.shape
        var_prior_cell = (STATE_VARIABLES['theta_root']['std']) ** 2.0
        k_scalar = var_prior_cell / (var_prior_cell + obs_noise_var)

        # Innovation and Posterior Map
        innovation_grid = obs_grid - prior_grid
        posterior_grid = prior_grid + k_scalar * innovation_grid
        posterior_grid = np.clip(
            posterior_grid,
            STATE_VARIABLES['theta_root']['min'],
            STATE_VARIABLES['theta_root']['max']
        )

        post_var_cell = (1.0 - k_scalar) * var_prior_cell
        grid_var_reduction = ((post_var_cell - var_prior_cell) / var_prior_cell) * 100.0

        return {
            'posterior_grid': posterior_grid,
            'kalman_gain_scalar': k_scalar,
            'prior_variance': var_prior_cell,
            'posterior_variance': post_var_cell,
            'variance_reduction_pct': grid_var_reduction
        }

    @staticmethod
    def load_certified_state_database(
        path: str = "5_storage/state_database/enkf_state_database.pt"
    ) -> Dict[str, Any]:
        """
        Ingests pre-computed state database bundle certified in Notebook 06 and Notebook 12.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"EnKF state database missing: {path}")
        return torch.load(path, map_location="cpu", weights_only=False)
