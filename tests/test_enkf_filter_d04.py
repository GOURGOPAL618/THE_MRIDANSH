import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '3_core_engine')))

from state_estimation.enkf_filter import EnsembleKalmanFilterEngine, assimilate_spatial_grid


class TestEnKFFilterD04(unittest.TestCase):

    def _make_engine(self, n_ens=10, obs_std=0.05):
        return EnsembleKalmanFilterEngine(num_ensembles=n_ens, obs_noise_std=obs_std)

    def _make_rng(self, seed=42):
        return np.random.default_rng(seed)

    # ── T-EKF-01 ──────────────────────────────────────────────────────────────
    def test_tekf_01_valid_shapes(self):
        print("\\n--- T-EKF-01: Valid ensemble + observation produce correctly shaped outputs ---")
        engine = self._make_engine(n_ens=10)
        rng    = self._make_rng(1)
        n_state = 6 * 6   # 36

        prior_ens = rng.uniform(0.20, 0.35, size=(n_state, 10)).astype(np.float32)
        obs       = rng.uniform(0.22, 0.38, size=(n_state,)).astype(np.float32)

        out = engine.assimilate_observations(prior_ens, obs, rng=rng)

        self.assertEqual(out["posterior_soil_state"].shape,  (n_state,))
        self.assertEqual(out["kalman_gain"].shape,           (n_state, n_state))
        self.assertEqual(out["posterior_ensemble"].shape,    (n_state, 10))
        self.assertIsInstance(out["uncertainty_variance"],   np.floating)
        print("[PASS] T-EKF-01: Correct shapes produced for (N_state=36, N_ens=10).")

    # ── T-EKF-02 ──────────────────────────────────────────────────────────────
    def test_tekf_02_variable_grid_sizes(self):
        print("\\n--- T-EKF-02: Different state sizes work without fixed-dim assumptions ---")
        for h, w in [(4, 4), (8, 12), (1, 20)]:
            n_state = h * w
            engine  = self._make_engine(n_ens=6)
            rng     = self._make_rng(2)
            prior_ens = rng.uniform(0.1, 0.4, size=(n_state, 6)).astype(np.float32)
            obs       = rng.uniform(0.1, 0.4, size=(n_state,)).astype(np.float32)
            out = engine.assimilate_observations(prior_ens, obs, rng=rng)
            self.assertEqual(out["posterior_soil_state"].shape, (n_state,))
        print("[PASS] T-EKF-02: Engine handles arbitrary grid sizes without hardcoded 120×120.")

    # ── T-EKF-03 ──────────────────────────────────────────────────────────────
    def test_tekf_03_invalid_dimensions(self):
        print("\\n--- T-EKF-03: Invalid shapes fail explicitly ---")
        engine = self._make_engine(n_ens=5)
        rng    = self._make_rng(3)

        # Wrong rank for prior_ensemble (3-D not allowed)
        with self.assertRaises(ValueError):
            engine.assimilate_observations(
                np.ones((10, 5, 2), dtype=np.float32),
                np.ones(10, dtype=np.float32),
                rng=rng,
            )

        # Wrong member count vs engine config
        with self.assertRaises(ValueError):
            engine.assimilate_observations(
                np.ones((10, 8), dtype=np.float32),   # 8 ≠ 5
                np.ones(10, dtype=np.float32),
                rng=rng,
            )

        # Observation dim mismatch
        with self.assertRaises(ValueError):
            engine.assimilate_observations(
                np.ones((10, 5), dtype=np.float32),
                np.ones(7, dtype=np.float32),          # 7 ≠ 10
                rng=rng,
            )

        # Observation not 1-D
        with self.assertRaises(ValueError):
            engine.assimilate_observations(
                np.ones((10, 5), dtype=np.float32),
                np.ones((10, 2), dtype=np.float32),   # 2-D obs
                rng=rng,
            )

        print("[PASS] T-EKF-03: All invalid dimension cases raise ValueError explicitly.")

    # ── T-EKF-04 ──────────────────────────────────────────────────────────────
    def test_tekf_04_non_finite_inputs(self):
        print("\\n--- T-EKF-04: Non-finite inputs fail explicitly ---")
        engine = self._make_engine(n_ens=4)
        rng    = self._make_rng(4)

        nan_prior = np.full((6, 4), np.nan, dtype=np.float32)
        obs       = np.ones(6, dtype=np.float32) * 0.3
        with self.assertRaises(ValueError):
            engine.assimilate_observations(nan_prior, obs, rng=rng)

        inf_obs = np.full(6, np.inf, dtype=np.float32)
        good_prior = np.ones((6, 4), dtype=np.float32) * 0.3
        with self.assertRaises(ValueError):
            engine.assimilate_observations(good_prior, inf_obs, rng=rng)

        print("[PASS] T-EKF-04: NaN and Inf inputs are caught before matrix ops.")

    # ── T-EKF-05 ──────────────────────────────────────────────────────────────
    def test_tekf_05_deterministic_update(self):
        """
        Analytical check: when the prior ensemble is a perfect constant field and
        the observation equals that constant, the posterior should be unchanged.
        More precisely: if x_f = obs (zero innovation), posterior mean = x_f.
        """
        print("\\n--- T-EKF-05: Zero-innovation case: posterior == prior mean ---")
        n_state, n_ens = 9, 6
        value  = 0.30
        engine = self._make_engine(n_ens=n_ens, obs_std=0.001)
        rng    = np.random.default_rng(99)

        # All members identical → prior mean = value, innovation Y_p − X ≈ obs − value
        prior_ens = np.full((n_state, n_ens), value, dtype=np.float64)
        obs       = np.full((n_state,),       value, dtype=np.float64)

        out = engine.assimilate_observations(prior_ens, obs, rng=rng)
        post_mean = out["posterior_soil_state"].astype(np.float64)

        # With obs = prior, posterior mean should stay near value despite noise
        # Tolerance is generous to accommodate stochastic perturbation residuals
        self.assertTrue(
            np.allclose(post_mean, value, atol=0.02),
            f"Posterior mean {post_mean.mean():.4f} drifted from prior {value} "
            "under zero innovation — update equation likely wrong."
        )
        print(f"[PASS] T-EKF-05: Posterior mean {post_mean.mean():.4f} ~= prior {value} under zero innovation.")

    # ── T-EKF-06 ──────────────────────────────────────────────────────────────
    def test_tekf_06_deterministic_with_rng(self):
        print("\\n--- T-EKF-06: Same RNG seed yields identical results ---")
        engine = self._make_engine(n_ens=8)
        n_state = 16

        rng_a = np.random.default_rng(7)
        prior_ens = np.random.default_rng(5).uniform(0.2, 0.35, size=(n_state, 8)).astype(np.float32)
        obs       = np.random.default_rng(6).uniform(0.2, 0.35, size=(n_state,)).astype(np.float32)
        out_a = engine.assimilate_observations(prior_ens, obs, rng=rng_a)

        rng_b = np.random.default_rng(7)   # same seed
        out_b = engine.assimilate_observations(prior_ens, obs, rng=rng_b)

        np.testing.assert_array_equal(
            out_a["posterior_soil_state"],
            out_b["posterior_soil_state"],
        )
        print("[PASS] T-EKF-06: Seeded RNG produces byte-identical posterior means.")

    # ── T-EKF-07 ──────────────────────────────────────────────────────────────
    def test_tekf_07_api_compatibility_spatial_wrapper(self):
        print("\\n--- T-EKF-07: Legacy spatial-grid API preserved ---")
        engine = self._make_engine(n_ens=10)
        rng    = self._make_rng(8)

        prior_grid = rng.uniform(0.20, 0.35, size=(8, 8)).astype(np.float32)
        obs_grid   = rng.uniform(0.22, 0.38, size=(8, 8)).astype(np.float32)

        result = assimilate_spatial_grid(engine, prior_grid, obs_grid, rng=rng)

        self.assertEqual(result["posterior_soil_state"].shape, (8, 8))
        self.assertIn("kalman_gain",          result)
        self.assertIn("uncertainty_variance", result)
        self.assertIn("posterior_ensemble",   result)
        print("[PASS] T-EKF-07: assimilate_spatial_grid returns (H, W) posterior, all keys present.")

    # ── Extra: constructor validation ─────────────────────────────────────────
    def test_constructor_rejects_bad_params(self):
        with self.assertRaises(ValueError):
            EnsembleKalmanFilterEngine(num_ensembles=1)
        with self.assertRaises(ValueError):
            EnsembleKalmanFilterEngine(obs_noise_std=-0.1)
        with self.assertRaises(ValueError):
            EnsembleKalmanFilterEngine(tikhonov_reg=0.0)


if __name__ == '__main__':
    unittest.main()
