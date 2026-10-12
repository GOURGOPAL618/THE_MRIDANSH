"""
Task 06 — Multitask Trainer Integration & Core Engine Verification
==================================================================
Tests the minimal PyTorch training pathway:
  Input -> Backbone -> Supported Loss -> backward() -> Optimizer Step

Also verifies:
  - Parameter gradient updates on CNN and GRU modules.
  - Absence of accidental computational graph detachment.
  - Clear boundaries against feeding latent features into physics engine.
  - Strict NumPy-only boundary for Ensemble Kalman Filter (EnKF).
  - Integration with the verified 2_data_pipeline adapter snapshot.

Note:
  Target tensors used in these tests are SOFTWARE-TEST FIXTURES to verify
  computational execution and differentiability. They are NOT in-situ soil measurements
  or scientifically validated ground-truth labels.
"""

import math
import os
import sys
import unittest
import numpy as np
import torch
import torch.nn as nn

# Establish repository package roots
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_CORE_ENGINE = os.path.join(_REPO_ROOT, "3_core_engine")
_DATA_PIPELINE = os.path.join(_REPO_ROOT, "2_data_pipeline")

for _p in (_CORE_ENGINE, _DATA_PIPELINE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from trainer import MultiTaskTrainingOrchestrator
from data.pipeline_adapter import snapshot_to_tensor
from fusion.satellite_fusion import SatelliteSAROpticalFusionEngine
from schemas.satellite_schema import GeospatialRasterAsset
from state_estimation.enkf_filter import EnsembleKalmanFilterEngine, assimilate_spatial_grid


def _make_raster_asset(
    value: float,
    band_name: str,
    crs: str = "EPSG:32645",
    resolution: tuple = (10.0, 10.0),
    bounds: tuple = (0.0, 0.0, 100.0, 100.0),
    transform: tuple = (10.0, 0.0, 0.0, 0.0, -10.0, 100.0),
    height: int = 10,
    width: int = 10,
) -> GeospatialRasterAsset:
    raw = np.full((1, height, width), value, dtype=np.float32)
    mask = np.ones((1, height, width), dtype=bool)
    return GeospatialRasterAsset(
        raw_array=raw,
        raw_dtype="float32",
        scale_factor=1.0,
        add_offset=0.0,
        crs=crs,
        transform=transform,
        bounds=bounds,
        resolution=resolution,
        valid_data_mask=mask,
        stac_item_id=f"mock_{band_name}",
        asset_key=band_name,
        source_href=f"s3://mock/{band_name}.tif",
    )


class TestCoreTrainerD06(unittest.TestCase):

    def setUp(self):
        torch.manual_seed(42)
        np.random.seed(42)
        self.in_channels = 5
        self.feature_dim = 64
        self.trainer = MultiTaskTrainingOrchestrator(
            in_channels=self.in_channels,
            feature_dim=self.feature_dim,
            learning_rate=1e-3,
        )

    # ─── T-TR-01: Valid inputs execute forward and loss pathway ──────────────
    def test_ttr_01_valid_inputs_execute_training_step(self):
        """
        Valid 5-D tensor (B, T, C, H, W) and 4-D target fixture (B, feature_dim, H, W)
        execute the documented forward, loss, backward, and optimizer step cycle.
        """
        b, t, c, h, w = 2, 3, self.in_channels, 16, 16
        mock_input = torch.randn(b, t, c, h, w)
        # Software test fixture representing desired latent target
        mock_target = torch.randn(b, self.feature_dim, h, w)

        metrics = self.trainer.train_step(mock_input, mock_target)

        self.assertIn("total_loss", metrics)
        self.assertIn("loss_representation", metrics)
        self.assertIn("latent_shape", metrics)
        self.assertEqual(metrics["latent_shape"], (b, self.feature_dim, h, w))
        self.assertIsInstance(metrics["total_loss"], float)
        self.assertTrue(metrics["total_loss"] > 0)

    # ─── T-TR-02: Invalid dimensions and incompatible inputs fail explicitly ─
    def test_ttr_02_invalid_inputs_fail_explicitly(self):
        """
        Confirms strict validation on input rank, channel count, target shape,
        non-finite values, and blocked agro/civil parameters.
        """
        # 1. 4-D input tensor (missing time dimension T)
        with self.assertRaises(ValueError):
            self.trainer.train_step(
                torch.randn(2, self.in_channels, 16, 16),
                torch.randn(2, self.feature_dim, 16, 16),
            )

        # 2. Channel mismatch (e.g., C=3 instead of 5)
        with self.assertRaises(ValueError):
            self.trainer.train_step(
                torch.randn(2, 1, 3, 16, 16),
                torch.randn(2, self.feature_dim, 16, 16),
            )

        # 3. Non-finite values in input
        nan_input = torch.randn(2, 1, self.in_channels, 16, 16)
        nan_input[0, 0, 0, 0, 0] = float("nan")
        with self.assertRaises(ValueError):
            self.trainer.train_step(nan_input, torch.randn(2, self.feature_dim, 16, 16))

        # 4. Target shape mismatch
        with self.assertRaises(ValueError):
            self.trainer.train_step(
                torch.randn(2, 1, self.in_channels, 16, 16),
                torch.randn(2, self.feature_dim, 8, 8),  # spatial mismatch
            )

        # 5. Non-tensor input
        with self.assertRaises(TypeError):
            self.trainer.train_step("invalid_tensor", torch.randn(2, self.feature_dim, 16, 16))

        # 6. Attempting to supply target_agro or target_civil raises NotImplementedError
        with self.assertRaises(NotImplementedError):
            self.trainer.train_epoch(
                torch.randn(2, 1, self.in_channels, 16, 16),
                target_agro=torch.randn(2, 16, 16),
            )

    # ─── T-TR-03: The selected loss is finite ─────────────────────────────────
    def test_ttr_03_loss_is_finite(self):
        """
        Verifies that computed losses are numerically finite and positive.
        """
        mock_input = torch.randn(2, 2, self.in_channels, 12, 12)
        mock_target = torch.randn(2, self.feature_dim, 12, 12)

        metrics = self.trainer.train_step(mock_input, mock_target)

        self.assertTrue(math.isfinite(metrics["total_loss"]))
        self.assertTrue(math.isfinite(metrics["loss_representation"]))
        self.assertFalse(math.isnan(metrics["total_loss"]))

    # ─── T-TR-04: backward() produces finite, nonzero gradients ──────────────
    def test_ttr_04_backward_produces_finite_nonzero_gradients(self):
        """
        Verifies that backward() produces nonzero, finite gradients on both
        spatial CNN and temporal GRU trainable parameters.
        """
        mock_input = torch.randn(2, 2, self.in_channels, 16, 16)
        mock_target = torch.randn(2, self.feature_dim, 16, 16)

        # Clear any prior gradients
        self.trainer.optimizer.zero_grad()

        # Step
        self.trainer.train_step(mock_input, mock_target)

        # Check CNN parameters
        cnn_conv0_grad = self.trainer.encoder.spatial_encoder[0].weight.grad
        self.assertIsNotNone(cnn_conv0_grad)
        self.assertTrue(torch.isfinite(cnn_conv0_grad).all())
        self.assertTrue(cnn_conv0_grad.abs().sum().item() > 0)

        # Check GRU parameters
        gru_weight_grad = self.trainer.encoder.temporal_encoder.weight_ih_l0.grad
        self.assertIsNotNone(gru_weight_grad)
        self.assertTrue(torch.isfinite(gru_weight_grad).all())
        self.assertTrue(gru_weight_grad.abs().sum().item() > 0)

    # ─── T-TR-05: Optimizer step changes trainable parameters ────────────────
    def test_ttr_05_optimizer_step_changes_parameters(self):
        """
        Demonstrates that at least one intended trainable parameter changes
        after an optimizer step under a valid, nonzero training signal.
        """
        mock_input = torch.randn(2, 2, self.in_channels, 16, 16)
        mock_target = torch.randn(2, self.feature_dim, 16, 16)

        # Record parameter weights before step
        conv0_weight_before = (
            self.trainer.encoder.spatial_encoder[0].weight.detach().clone()
        )
        gru_weight_before = (
            self.trainer.encoder.temporal_encoder.weight_ih_l0.detach().clone()
        )

        # Execute training step
        self.trainer.train_step(mock_input, mock_target)

        # Record updated parameter weights
        conv0_weight_after = (
            self.trainer.encoder.spatial_encoder[0].weight.detach().clone()
        )
        gru_weight_after = (
            self.trainer.encoder.temporal_encoder.weight_ih_l0.detach().clone()
        )

        # Assert parameters changed
        delta_cnn = (conv0_weight_after - conv0_weight_before).abs().max().item()
        delta_gru = (gru_weight_after - gru_weight_before).abs().max().item()

        self.assertTrue(delta_cnn > 0, "CNN weights did not change after optimizer step.")
        self.assertTrue(delta_gru > 0, "GRU weights did not change after optimizer step.")

    # ─── T-TR-06: Repeated steps clear gradients correctly ───────────────────
    def test_ttr_06_repeated_steps_clear_gradients(self):
        """
        Verifies that optimizer.zero_grad() clears gradients correctly between steps
        and does not unintentionally accumulate stale gradients.
        """
        mock_input = torch.randn(2, 1, self.in_channels, 12, 12)
        mock_target = torch.randn(2, self.feature_dim, 12, 12)

        # Step 1
        self.trainer.train_step(mock_input, mock_target)
        grad_step1 = (
            self.trainer.encoder.spatial_encoder[0].weight.grad.detach().clone()
        )

        # Reset optimizer explicitly
        self.trainer.optimizer.zero_grad()
        grad_zeroed = self.trainer.encoder.spatial_encoder[0].weight.grad
        # PyTorch zero_grad either sets to None or zero tensor
        if grad_zeroed is not None:
            self.assertEqual(grad_zeroed.abs().sum().item(), 0.0)

        # Step 2 with exact same input
        self.trainer.train_step(mock_input, mock_target)
        grad_step2 = (
            self.trainer.encoder.spatial_encoder[0].weight.grad.detach().clone()
        )

        # If gradients were accumulating, grad_step2 would be 2 * grad_step1
        # Because we clear grads before each backward, grad_step2 should be close to grad_step1
        # (slight difference due to parameter update from step 1, but order of magnitude identical)
        self.assertTrue(
            torch.isfinite(grad_step2).all(), "Step 2 gradients must be finite."
        )
        self.assertFalse(
            torch.allclose(grad_step2, 2.0 * grad_step1, rtol=1e-2),
            "Gradients accumulated across steps without clearing!",
        )

    # ─── T-TR-07: Physics-loss boundary rejection ─────────────────────────────
    def test_ttr_07_physics_loss_boundary_rejection_and_acceptance(self):
        """
        Verifies that:
          1. Feeding a latent feature map (4-D with channel == feature_dim) into
             compute_physics_loss is explicitly REJECTED with ValueError.
          2. Values outside physical volumetric water content [0.0, 1.0] are REJECTED.
          3. A valid physical moisture grid [0.15, 0.35] is ACCEPTED and produces a finite loss.
        """
        # 1. Latent tensor rejection
        latent_tensor = torch.randn(2, self.feature_dim, 16, 16)
        with self.assertRaises(ValueError) as ctx:
            self.trainer.compute_physics_loss(latent_tensor)
        self.assertIn("Boundary rejection", str(ctx.exception))

        # 2. Negative moisture rejection
        negative_moisture = torch.tensor([[-0.05, 0.20], [0.30, 0.25]], dtype=torch.float32)
        with self.assertRaises(ValueError):
            self.trainer.compute_physics_loss(negative_moisture)

        # 3. Super-saturated moisture rejection
        super_moisture = torch.tensor([[1.20, 0.20], [0.30, 0.25]], dtype=torch.float32)
        with self.assertRaises(ValueError):
            self.trainer.compute_physics_loss(super_moisture)

        # 4. Valid physical moisture grid acceptance
        valid_moisture = torch.empty(16, 16, dtype=torch.float32).uniform_(0.15, 0.35)
        phys_out = self.trainer.compute_physics_loss(valid_moisture)
        self.assertIn("physics_constraint_loss", phys_out)
        self.assertTrue(torch.isfinite(phys_out["physics_constraint_loss"]))

        # 5. Combined training step with valid physical moisture grid
        mock_input = torch.randn(2, 1, self.in_channels, 16, 16)
        mock_target = torch.randn(2, self.feature_dim, 16, 16)
        metrics = self.trainer.train_step(
            mock_input, mock_target, physical_moisture_grid=valid_moisture
        )
        self.assertIn("loss_physics", metrics)
        self.assertTrue(metrics["loss_physics"] >= 0)

    # ─── T-TR-08: NumPy EnKF gradient detachment verification ─────────────────
    def test_ttr_08_enkf_does_not_propagate_gradients(self):
        """
        Verifies that:
          1. The EnKF filter operates strictly on NumPy arrays.
          2. Passing PyTorch tensors to assimilate_spatial_grid fails.
          3. EnKF outputs have no autograd graph attached (detached boundary).
        """
        enkf = EnsembleKalmanFilterEngine(num_ensembles=5)

        # PyTorch tensor with requires_grad
        prior_torch = torch.rand(4, 4, requires_grad=True)
        obs_torch = torch.rand(4, 4)

        with self.assertRaises((AttributeError, TypeError)):
            assimilate_spatial_grid(enkf, prior_torch, obs_torch)

        # Pure NumPy execution
        prior_np = np.full((4, 4), 0.25, dtype=np.float32)
        obs_np = np.full((4, 4), 0.30, dtype=np.float32)
        result = assimilate_spatial_grid(enkf, prior_np, obs_np)

        self.assertIsInstance(result["posterior_soil_state"], np.ndarray)
        self.assertFalse(hasattr(result["posterior_soil_state"], "grad_fn"))

    # ─── T-TR-09: End-to-end integration with pipeline adapter snapshot ───────
    def test_ttr_09_end_to_end_pipeline_adapter_to_trainer(self):
        """
        Verifies full wiring from 2_data_pipeline fusion snapshot -> adapter -> trainer.
        """
        engine = SatelliteSAROpticalFusionEngine(
            target_crs="EPSG:32645",
            target_resolution=(10.0, 10.0),
            target_bounds=(0.0, 0.0, 100.0, 100.0),
        )

        vv = _make_raster_asset(0.2, "SAR_VV")
        vh = _make_raster_asset(0.1, "SAR_VH")
        ndvi = _make_raster_asset(0.5, "OPTICAL_NDVI")
        ndmi = _make_raster_asset(0.3, "OPTICAL_NDMI")

        # Fusion snapshot from pipeline
        snapshot = engine.create_fused_spatial_tensor(vv, vh, ndvi, ndmi)

        # Adapter converts to (1, 1, 5, 10, 10) tensor
        datacube = snapshot_to_tensor(snapshot, in_channels=self.in_channels)
        self.assertEqual(datacube.shape, (1, 1, 5, 10, 10))

        # Software test fixture target
        target = torch.randn(1, self.feature_dim, 10, 10)

        # Execute train step
        metrics = self.trainer.train_step(datacube, target)
        self.assertIn("total_loss", metrics)
        self.assertTrue(metrics["total_loss"] > 0)
        self.assertEqual(metrics["latent_shape"], (1, self.feature_dim, 10, 10))


if __name__ == "__main__":
    unittest.main()
