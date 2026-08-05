# THE MRIDANSH - ENKF FILTER

import logging
import numpy as np
from typing import Dict, Tuple

logging.basicConfig(level = logging.INFO, format = "%(asctime)s - %(levelname)s - %(message)s")

class EnsembleKalmanFilterEngine:
    """Ensemble Kalman Filter (EnKF) for data assimilation & Optical Soil State Estimation."""

    def __init__(self, num_ensembles: int = 20, state_dim: int = 120 * 120, obs_noise_std: float = 0.05):
        self.num_ensembles = num_ensembles
        self.state_dim = state_dim
        self.obs_noise_std = obs_noise_std
        logging.info(f"📊 Initializing EnKF Engine | Ensembles: {num_ensembles} | State Dimension: {state_dim}")


    def generate_ensemble_states(self, initial_state: np.ndarray) -> np.ndarray:
        """Generates Perturbed ensemble states around initial model prediction."""
        flat_state = initial_state.flatten()
        noise = np.random.normal(0, 0.02, size = (self.num_ensembles, self.state_dim))
        ensemble = flat_state + noise
        return ensemble

    def assimilate_observations(self, prior_state: np.ndarray, observation: np.ndarray) -> Dict[str, np.ndarray]:
        """Performes EnKF State Estimation (Analysis Step) merging Model Prior and Satellite Observations."""
        logging.info("📊 Executing EnKF Assimilation Cycle (model Prior + Satellite Observations)...")

        shape = prior_state.shape
        flat_prior = prior_state.flatten()
        flat_obs = observation.flatten()

        # 1. Ensemble Forecast
        X = self.generate_ensemble_states(prior_state)  # Shape: (Ensembles, State_Dim)

        # Mean Prior State
        x_mean = np.mean(X, axis = 0)

        # Ensembles Perturbations Matrix
        A = X - x_mean

        # 2. Observation Pertubations
        obs_noise = np.random.normal(0, self.obs_noise_std, size = (self.num_ensembles, self.state_dim))
        Y = flat_obs + obs_noise

        # 3. Kalman Gain Computation (Scalar / Diagonal Approximation for Spatial Grids)
        prior_variance = np.var(flat_prior) + 1e-6
        obs_variance = (self.obs_noise_std ** 2) + 1e-6
        kalman_gain = prior_variance / (prior_variance + obs_variance)

        # 4. Analysis Step (Posterior State Estimation)
        posterior_ensemble = X + kalman_gain * (Y - X)
        posterior_mean = np.mean(posterior_ensemble, axis = 0).reshape(shape)

        logging.info(
            f"✅ EnKF Assimilation Complete!\n"
            f"   -> Calculated Kalman Gain (K): {kalman_gain:.4f}\n"
            f"   -> Mean Prior Soil Moisture: {np.mean(prior_state):.4f}\n"
            f"   -> Mean Assimilated Soil State: {np.mean(posterior_mean):.4f}"
        )

        return {
            "posterior_soil_state": posterior_mean.astype(np.float32),
            "kalman_gain": np.array(kalman_gain, dtype = np.float32),
            "uncertainty_variance": np.array(np.var(posterior_ensemble), dtype = np.float32)
        }


# Self-Test Execution Module
if __name__ == "__main__":
    print("\n--- Testing Day 9 Ensemble Kalman Filter (EnKF) Engine ---")

    enkf = EnsembleKalmanFilterEngine(num_ensembles = 20, obs_noise_std = 0.03)

    #  Stimulated 120*120 Soil Moisture Matrix
    mock_model_prior = np.random.uniform(0.20, 0.35, size = (120, 120)).astype(np.float32)
    mock_satellite_obs = np.random.uniform(0.22, 0.38, size = (120, 120)).astype(np.float32)
    
    result = enkf.assimilate_observations(mock_model_prior, mock_satellite_obs)

    assert "posterior_soil_state" in result and "kalman_gain" in result
    assert result["posterior_soil_state"].shape == (120, 120)

    print("\n[SUCCESS] Day 9 EnKF State Estimation Engine: PASSED OPERATIONAL CHECKS!\n")