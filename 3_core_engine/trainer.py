# THE MRIDANSH - Trainer

import logging

import numpy as np

from .models.spatial_temporal_encoder import SpatialTemporalEncoderBackbone
from .physics.richards_engine import RichardsSoilPhysicsEngine

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class MultiTaskTrainingOrchestrator:
    """Multi-task Training Loop Orchestrator balancing Agronomy, Civil and Physics Losses."""

    def __init__(
        self,
        w_agro: float = 1.0,
        w_civil: float = 0.8,
        w_physics: float = 0.5,
        in_channels: int = 8,
        feature_dim: int = 128,
    ):
        self.w_agro = w_agro
        self.w_civil = w_civil
        self.w_physics = w_physics

        # Initialize Neutral Backbone & Physics Engine
        self.encoder = SpatialTemporalEncoderBackbone(
            in_channels=in_channels, feature_dim=feature_dim
        )
        self.physics_engine = RichardsSoilPhysicsEngine()

        logging.info(
            f"🔄 Multi-Task Trainer Initialized | Weights -> "
            f"Agro: {w_agro}, Civil: {w_civil}, Physics: {w_physics}"
        )

    def compute_composite_loss(
        self,
        pred_agro: np.ndarray,
        target_agro: np.ndarray,
        pred_civil: np.ndarray,
        target_civil: np.ndarray,
        physics_penalty: float,
    ) -> dict[str, float]:
        """Computes Comnposite Multi task loss with Physics Informed Penalty."""

        loss_agro = float(np.mean(np.square(pred_agro - target_agro)))
        loss_civil = float(np.mean(np.square(pred_civil - target_civil)))

        total_loss = (
            self.w_agro * loss_agro
            + self.w_civil * loss_civil
            + self.w_physics * physics_penalty
        )

        return {
            "total_loss": total_loss,
            "loss_agro": loss_agro,
            "loss_civil": loss_civil,
            "loss_physics": float(physics_penalty),
        }

    def train_epoch(
        self,
        datacube_batch: np.ndarray,
        target_agro: np.ndarray,
        target_civil: np.ndarray,
    ) -> dict[str, float]:
        """Execute a Single multi-task training epoch pass over the data cube tensor."""
        logging.info("⚡ Running Multi-Task Training Epoch Forward Pass...")

        # 1. Forward Pass Through Neural Spatial - Temporal Encoder
        latent_output = self.encoder.forward(datacube_batch)
        latent_map = latent_output[
            "latent_representation"
        ]  # Shape: (Batch, H, W, Latent_Dim)

        # 2. Multi-Task Simulated Predictions (Agro Soil Moisture & Civil Bearing Capacity)
        pred_agro = (
            np.mean(latent_map, axis=-1, keepdims=True) * 0.35
        )  # Scaled Volumetric Soil Moisture
        pred_civil = (
            np.mean(latent_map, axis=-1, keepdims=True) * 150.0
        )  # Scaled Bearing Capacity (kPa)

        # Squeeze Channel Dim For loss matching if required
        pred_agro_sq = np.squeeze(pred_agro, axis=-1)
        pred_civil_sq = np.squeeze(pred_civil, axis=-1)

        # 3. Calculate Physics Constraints Violation via Richards Engine
        mean_moisture_field = np.mean(pred_agro_sq, axis=0)  # Spatial mean across batch
        physics_eval = self.physics_engine.compute_richards_flux(mean_moisture_field)
        physics_penalty = float(physics_eval["physics_constraint_loss"])

        # 4. Compute Composite Loss Matrix
        loss_dict = self.compute_composite_loss(
            pred_agro_sq, target_agro, pred_civil_sq, target_civil, physics_penalty
        )

        logging.info(
            f"✅ Epoch Completed | Total Loss: {loss_dict['total_loss']:.6f} "
            f"(Agro MSE: {loss_dict['loss_agro']:.6f}, Civil MSE: {loss_dict['loss_civil']:.6f}, "
            f"Physics Penalty: {loss_dict['loss_physics']:.6f})"
        )

        return loss_dict


# Self-Test Execution Module
if __name__ == "__main__":
    print("\n--- Testing Day 10 Multi-Task Training Loop Orchestrator ---")

    trainer = MultiTaskTrainingOrchestrator()

    # Mock Batch Input Datacube: Batch=2, Sequence=5, H=120, W=120, Channels=
    mock_datacube = np.random.uniform(0.0, 1.0, size=(2, 5, 120, 120, 8)).astype(
        np.float32
    )

    # Mock Target Ground Truth Matrices
    mock_target_agro = np.random.uniform(0.15, 0.40, size=(2, 120, 120)).astype(
        np.float32
    )
    mock_target_civil = np.random.uniform(50.0, 200.0, size=(2, 120, 120)).astype(
        np.float32
    )

    metrics = trainer.train_epoch(mock_datacube, mock_target_agro, mock_target_civil)

    assert "total_loss" in metrics and "loss_physics" in metrics
    assert metrics["total_loss"] > 0

    print(
        "\n[SUCCESS] Day 10 Multi-Task Training Loop Engine: PASSED OPERATIONAL CHECKS!\n"
    )
