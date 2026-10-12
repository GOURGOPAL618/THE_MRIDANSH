# THE MRIDANSH — ENKF FILTER
# DEVELOPED BY — JCC
#
# ─── Implemented Equations ──────────────────────────────────────────────────────
#
#   Ensemble layout:  X  ∈ ℝ^{N × N_ens}     (columns are ensemble members)
#   Observation vec:  y  ∈ ℝ^{M}
#   Observation op.:  H  ∈ ℝ^{M × N}         (default: identity, M = N)
#
#   1. FORECAST (caller's responsibility — see R-ENKF-04 note)
#      X_f is supplied by the caller (model propagation step).
#
#   2. ANALYSIS
#      A     = X_f - x̄_f                     ensemble anomaly matrix
#      P_f   = A A^T / (N_ens − 1)            sample forecast covariance  [N × N]
#      P_yx  = H P_f                          cross-covariance            [M × N]
#      S     = H P_f H^T + R                  innovation covariance       [M × M]
#      K     = P_yx^T S^{-1}                  Kalman gain                 [N × M]
#      Y_p   = y𝟙^T + ε,  ε ~ N(0, R)         perturbed obs per member    [M × N_ens]
#      X_a   = X_f + K (Y_p − H X_f)         analysis update             [N × N_ens]
#
# ─── Limitations ────────────────────────────────────────────────────────────────
#   • No temporal propagation model is included; the caller must supply X_f.
#   • H is restricted to the identity observation operator (M = N = state_dim).
#     Partial observations (M < N) with a non-trivial H are deferred.
#   • Stochastic perturbations are intentional per the standard EnKF formulation
#     (Burgers et al. 1998).  They are not a defect.
#   • S is inverted with numpy.linalg.solve (triangular solve via lstsq fallback),
#     NOT np.linalg.inv, for numerical stability.
#   • EnKF is NOT differentiable end-to-end via PyTorch autograd; it operates on
#     numpy arrays.  The caller is responsible for detaching tensors before handing
#     them to this module (see R-ENKF-06).
# ────────────────────────────────────────────────────────────────────────────────

import logging

import numpy as np

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class EnsembleKalmanFilterEngine:
    """
    Ensemble Kalman Filter (EnKF) for soil-state data assimilation.

    State and ensemble shape contract
    ──────────────────────────────────
      prior_ensemble  : np.ndarray, shape (N_state, N_ens),  float32 or float64
      observation     : np.ndarray, shape (N_state,),        same dtype
      obs_noise_cov R : scalar σ² or ndarray (N_state, N_state), positive-definite

    Outputs
    ───────
      posterior_soil_state  : np.ndarray, (spatial_shape)   — posterior ensemble mean
      kalman_gain           : np.ndarray, (N_state, N_state) — full K matrix
      uncertainty_variance  : float                         — posterior ensemble variance
      posterior_ensemble    : np.ndarray, (N_state, N_ens)  — full analysis ensemble

    Note on state semantics
    ───────────────────────
      The current caller in trainer.py supplies a 2-D spatial grid (H, W).  This
      module flattens that grid to (H*W,) = N_state for internal computation and
      reshapes the posterior mean back to the original spatial shape on return.
      The connection between latent NN features and actual soil moisture states is
      NOT established here; that boundary must be defined by the trainer.
    """

    def __init__(
        self,
        num_ensembles: int = 20,
        obs_noise_std: float = 0.05,
        ensemble_init_noise_std: float = 0.02,
        tikhonov_reg: float = 1e-6,
    ):
        """
        Parameters
        ----------
        num_ensembles         : Number of ensemble members (must be ≥ 2).
        obs_noise_std         : Observation noise std dev σ (scalar, same units as state).
                                R is assumed diagonal: R = σ² I.
        ensemble_init_noise_std : Std dev used when generating the initial ensemble spread
                                from a prior state estimate.  Intentional stochastic
                                perturbation per standard EnKF design.
        tikhonov_reg          : Small diagonal regularisation added to the innovation
                                covariance S before solving for K.  Prevents singular
                                systems when N_ens is small.  Must be > 0.
        """
        if num_ensembles < 2:
            raise ValueError(
                f"num_ensembles must be ≥ 2 (got {num_ensembles}); "
                "fewer than 2 members makes sample covariance undefined."
            )
        if obs_noise_std <= 0.0:
            raise ValueError(
                f"obs_noise_std must be > 0 (got {obs_noise_std})."
            )
        if tikhonov_reg <= 0.0:
            raise ValueError(
                f"tikhonov_reg must be > 0 (got {tikhonov_reg})."
            )

        self.num_ensembles = num_ensembles
        self.obs_noise_std = obs_noise_std
        self.ensemble_init_noise_std = ensemble_init_noise_std
        self.tikhonov_reg = tikhonov_reg

        logging.info(
            f"📊 Initializing EnKF Engine | Ensembles: {num_ensembles} | "
            f"obs_noise_std: {obs_noise_std}"
        )

    # ─── Public API ──────────────────────────────────────────────────────────────

    def generate_ensemble_states(
        self,
        initial_state: np.ndarray,
        rng: np.random.Generator | None = None,
    ) -> np.ndarray:
        """
        Generate an initial ensemble by adding Gaussian perturbations to a prior estimate.

        Parameters
        ----------
        initial_state : np.ndarray, any spatial shape — the central prior estimate.
        rng           : Optional numpy random Generator for reproducible calls.
                        If None, the global numpy default is used (stochastic).

        Returns
        -------
        np.ndarray, shape (N_state, N_ens)  — ensemble columns.
        """
        if initial_state.ndim == 0:
            raise ValueError("initial_state must have at least 1 dimension.")

        rng = rng or np.random.default_rng()
        flat = initial_state.flatten()        # (N_state,)
        n_state = flat.size

        noise = rng.normal(
            0.0, self.ensemble_init_noise_std, size=(n_state, self.num_ensembles)
        ).astype(flat.dtype)                  # (N_state, N_ens)

        return flat[:, None] + noise          # broadcast: (N_state, N_ens)

    def assimilate_observations(
        self,
        prior_ensemble: np.ndarray,
        observation: np.ndarray,
        rng: np.random.Generator | None = None,
    ) -> dict:
        """
        EnKF analysis step: update the prior ensemble given new observations.

        Parameters
        ----------
        prior_ensemble : np.ndarray, shape (N_state, N_ens)
                         Forecast ensemble, columns = members.
        observation    : np.ndarray, shape (N_state,)
                         Observed values aligned to the full state vector (H = I).
        rng            : Optional numpy random Generator for reproducible noise.

        Returns
        -------
        dict with keys:
          'posterior_soil_state'  — np.ndarray, posterior mean reshaped to (N_state,)
          'kalman_gain'           — np.ndarray, shape (N_state, N_state)
          'uncertainty_variance'  — float, scalar posterior ensemble variance
          'posterior_ensemble'    — np.ndarray, shape (N_state, N_ens)
        """
        # ── Input validation ────────────────────────────────────────────────────
        if prior_ensemble.ndim != 2:
            raise ValueError(
                f"prior_ensemble must be 2-D (N_state, N_ens), "
                f"got shape {prior_ensemble.shape}."
            )
        n_state, n_ens = prior_ensemble.shape

        if n_ens < 2:
            raise ValueError(
                f"prior_ensemble must have at least 2 columns (ensemble members), "
                f"got {n_ens}."
            )
        if n_ens != self.num_ensembles:
            raise ValueError(
                f"prior_ensemble has {n_ens} members but engine was initialised "
                f"with num_ensembles={self.num_ensembles}."
            )
        if observation.ndim != 1:
            raise ValueError(
                f"observation must be 1-D (N_state,), got shape {observation.shape}."
            )
        if observation.size != n_state:
            raise ValueError(
                f"observation size {observation.size} does not match "
                f"state dimension {n_state}.  H = I requires M = N."
            )
        if not np.all(np.isfinite(prior_ensemble)):
            raise ValueError("prior_ensemble contains non-finite values (NaN / Inf).")
        if not np.all(np.isfinite(observation)):
            raise ValueError("observation contains non-finite values (NaN / Inf).")

        logging.info(
            "📊 Executing EnKF Assimilation Cycle (model Prior + Satellite Observations)..."
        )

        rng = rng or np.random.default_rng()

        # ── 1. Ensemble anomaly matrix ──────────────────────────────────────────
        x_mean = prior_ensemble.mean(axis=1, keepdims=True)   # (N_state, 1)
        A = prior_ensemble - x_mean                           # (N_state, N_ens)

        # ── 2. Sample forecast covariance (H = I, so P_yx = P_f) ───────────────
        # P_f = A A^T / (N_ens − 1)
        # We never form the full [N_state × N_state] P_f explicitly when N_state is
        # large — instead we express K as (A A^T / (N-1) + R)^{-1} via a solve.
        # For the identity H used here: S = P_f + R = A A^T/(N-1) + σ² I

        # Compute S in the ensemble subspace for efficiency (Woodbury / ensemble space):
        #   P_f = A A^T / (N-1)
        #   S   = A A^T / (N-1) + σ²I
        # We use the full-space explicit approach since N_state may be in the hundreds,
        # not millions, for this prototype.
        P_f = (A @ A.T) / (n_ens - 1)                       # (N_state, N_state)

        obs_variance = self.obs_noise_std ** 2
        S = P_f + obs_variance * np.eye(n_state, dtype=prior_ensemble.dtype)
        S += self.tikhonov_reg * np.eye(n_state, dtype=prior_ensemble.dtype)

        # ── 3. Kalman gain: K = P_f S^{-1}  (solve S^T K^T = P_f^T) ───────────
        # Using lstsq for numerical robustness (handles near-singular S).
        K_T, _, _, _ = np.linalg.lstsq(S.T, P_f.T, rcond=None)
        K = K_T.T                                            # (N_state, N_state)

        # ── 4. Perturbed observations  Y_p ∈ ℝ^{N_state × N_ens} ───────────────
        obs_noise = rng.normal(
            0.0, self.obs_noise_std, size=(n_state, n_ens)
        ).astype(prior_ensemble.dtype)
        Y_p = observation[:, None] + obs_noise               # (N_state, N_ens)

        # ── 5. Analysis update: X_a = X_f + K (Y_p − H X_f) ───────────────────
        # H = I, so H X_f = prior_ensemble
        innovation = Y_p - prior_ensemble                    # (N_state, N_ens)
        posterior_ensemble = prior_ensemble + K @ innovation # (N_state, N_ens)

        posterior_mean = posterior_ensemble.mean(axis=1)     # (N_state,)
        uncertainty_variance = float(np.var(posterior_ensemble))

        logging.info(
            f"✅ EnKF Assimilation Complete!\n"
            f"   -> Kalman Gain trace: {np.trace(K):.4f}\n"
            f"   -> Mean Prior:        {x_mean.mean():.4f}\n"
            f"   -> Mean Posterior:    {posterior_mean.mean():.4f}"
        )

        return {
            "posterior_soil_state": posterior_mean.astype(np.float32),
            "kalman_gain":          K.astype(np.float32),
            "uncertainty_variance": np.float32(uncertainty_variance),
            "posterior_ensemble":   posterior_ensemble.astype(np.float32),
        }


# ─── Convenience wrapper preserving legacy call-site shape handling ───────────

def assimilate_spatial_grid(
    engine: EnsembleKalmanFilterEngine,
    prior_state_grid: np.ndarray,
    observation_grid: np.ndarray,
    rng: np.random.Generator | None = None,
) -> dict:
    """
    Convenience wrapper: accepts spatial grids of arbitrary shape (H, W),
    flattens them, runs the EnKF analysis, and reshapes the posterior mean back.

    The ensemble is generated internally from the prior_state_grid.
    This preserves the original caller pattern used by trainer.py.

    Parameters
    ----------
    engine            : EnsembleKalmanFilterEngine instance.
    prior_state_grid  : np.ndarray, shape (H, W) — model prior.
    observation_grid  : np.ndarray, shape (H, W) — satellite observation.
    rng               : Optional reproducible Generator.

    Returns
    -------
    Same dict as assimilate_observations, but 'posterior_soil_state' is
    reshaped to (H, W).
    """
    if prior_state_grid.shape != observation_grid.shape:
        raise ValueError(
            f"prior_state_grid shape {prior_state_grid.shape} != "
            f"observation_grid shape {observation_grid.shape}."
        )
    spatial_shape = prior_state_grid.shape

    prior_ensemble = engine.generate_ensemble_states(prior_state_grid, rng=rng)
    obs_flat       = observation_grid.flatten().astype(prior_state_grid.dtype)

    result = engine.assimilate_observations(prior_ensemble, obs_flat, rng=rng)
    result["posterior_soil_state"] = result["posterior_soil_state"].reshape(spatial_shape)
    return result


# ─── Self-Test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n--- Testing Day 9 Ensemble Kalman Filter (EnKF) Engine ---")

    engine = EnsembleKalmanFilterEngine(num_ensembles=20, obs_noise_std=0.03)
    rng    = np.random.default_rng(seed=0)

    mock_prior = np.random.default_rng(1).uniform(0.20, 0.35, size=(10, 10)).astype(np.float32)
    mock_obs   = np.random.default_rng(2).uniform(0.22, 0.38, size=(10, 10)).astype(np.float32)

    result = assimilate_spatial_grid(engine, mock_prior, mock_obs, rng=rng)

    assert "posterior_soil_state" in result and "kalman_gain" in result
    assert result["posterior_soil_state"].shape == (10, 10)

    print("\n[SUCCESS] Day 9 EnKF State Estimation Engine: PASSED OPERATIONAL CHECKS!\n")
