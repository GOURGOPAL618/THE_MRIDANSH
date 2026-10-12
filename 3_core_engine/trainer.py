# THE MRIDANSH - Multi-Task Trainer
# AETHER-MRID1607X Core Engine

import logging
from typing import Any, Dict, Optional, Tuple, Union
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

try:
    from .models.spatial_temporal_encoder import SpatialTemporalEncoderBackbone
    from .physics.richards_engine import RichardsSoilPhysicsEngine
    from .state_estimation.enkf_filter import EnsembleKalmanFilterEngine, assimilate_spatial_grid
except ImportError:
    from models.spatial_temporal_encoder import SpatialTemporalEncoderBackbone
    from physics.richards_engine import RichardsSoilPhysicsEngine
    from state_estimation.enkf_filter import EnsembleKalmanFilterEngine, assimilate_spatial_grid

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class MultiTaskTrainingOrchestrator:
    """
    Multi-Task Training Loop Orchestrator for AETHER-MRID1607X Core Engine.

    Manages:
      1. Forward propagation through SpatialTemporalEncoderBackbone.
      2. Representation loss computation against reference/target feature tensors.
      3. Physics-informed constraint loss evaluation when a valid physical moisture grid is provided.
      4. Backward gradient computation via PyTorch autograd.
      5. Parameter updates via PyTorch Optimizer (torch.optim.Adam by default).

    Scientific & Architectural Boundaries:
    --------------------------------------
    1. Latent Representations != Physical Soil State:
       SpatialTemporalEncoderBackbone outputs an abstract latent feature map (B, feature_dim, H, W).
       No calibrated projection heads exist to map these latent features to volumetric soil moisture [m³/m³]
       or civil soil bearing capacity [kPa].
    2. Supervised Agro/Civil Multitask Status:
       Genuine in-situ agricultural soil moisture and civil geotechnical ground-truth labels are
       currently unavailable in the data pipeline. Supervised multitask training on physical soil
       properties is formally marked as BLOCKED. Targets used in software testing are strictly test fixtures.
    3. Richards Physics Constraint Boundary:
       RichardsSoilPhysicsEngine evaluates 2D lateral gradient flux divergence on physical volumetric
       water content (0.05 <= theta <= 0.45 m³/m³). Latent feature representations are strictly rejected
       if passed to the physics engine.
    4. Ensemble Kalman Filter (EnKF) Boundary:
       EnsembleKalmanFilterEngine is a pure NumPy numerical state estimation filter (H = I).
       It is NOT differentiable via PyTorch autograd. Gradients do not flow through EnKF assimilation.
    """

    def __init__(
        self,
        in_channels: int = 5,
        feature_dim: int = 64,
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-4,
        w_representation: float = 1.0,
        w_physics: float = 0.5,
        w_agro: float = 1.0,
        w_civil: float = 0.8,
        optimizer_cls: type[optim.Optimizer] = optim.Adam,
    ):
        self.in_channels = in_channels
        self.feature_dim = feature_dim
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.w_representation = w_representation
        self.w_physics = w_physics
        self.w_agro = w_agro
        self.w_civil = w_civil

        # Initialize Neural Backbone & Physics Engine
        self.encoder = SpatialTemporalEncoderBackbone(
            in_channels=in_channels, feature_dim=feature_dim
        )
        self.physics_engine = RichardsSoilPhysicsEngine()

        # Initialize PyTorch Optimizer
        self.optimizer = optimizer_cls(
            self.encoder.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay,
        )

        logging.info(
            f"🔄 MultiTaskTrainingOrchestrator Initialized | Channels: {in_channels} | "
            f"Latent Dim: {feature_dim} | LR: {learning_rate} | "
            f"Weights -> Repr: {w_representation}, Physics: {w_physics}"
        )

    def validate_input_tensor(
        self, datacube_batch: Union[torch.Tensor, np.ndarray]
    ) -> torch.Tensor:
        """
        Validates input datacube batch geometry and numeric sanity.
        Expected shape: (B, T, C, H, W) matching canonical backbone contract.
        """
        if isinstance(datacube_batch, np.ndarray):
            datacube_batch = torch.from_numpy(datacube_batch).float()

        if not isinstance(datacube_batch, torch.Tensor):
            raise TypeError(
                f"datacube_batch must be a torch.Tensor or np.ndarray, got {type(datacube_batch).__name__}."
            )

        if datacube_batch.dim() != 5:
            raise ValueError(
                f"Expected 5-D datacube tensor (B, T, C, H, W), got {datacube_batch.dim()}-D tensor "
                f"with shape {tuple(datacube_batch.shape)}."
            )

        b, t, c, h, w = datacube_batch.shape
        if c != self.in_channels:
            raise ValueError(
                f"Expected {self.in_channels} input channels, got {c} in shape {tuple(datacube_batch.shape)}."
            )

        if not torch.isfinite(datacube_batch).all():
            raise ValueError("datacube_batch contains non-finite values (NaN or Inf).")

        return datacube_batch

    def compute_physics_loss(
        self, physical_moisture_grid: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        Evaluates the Richards physics constraint loss on a physical volumetric soil moisture grid.

        Boundary Guards:
          - The input must be a torch.Tensor representing volumetric water content [m³/m³].
          - Latent feature maps (shape (B, feature_dim, H, W) or 4-D matching feature_dim) are strictly rejected.
          - Values outside physical bounds [0.0, 1.0] are strictly rejected.
          - No arbitrary latent-to-moisture projection is performed.
        """
        if not isinstance(physical_moisture_grid, torch.Tensor):
            raise TypeError(
                f"physical_moisture_grid must be a torch.Tensor, got {type(physical_moisture_grid).__name__}."
            )

        # Boundary rejection: latent feature maps cannot be fed into the physics engine
        if physical_moisture_grid.dim() == 4 and physical_moisture_grid.shape[1] == self.feature_dim:
            raise ValueError(
                f"Boundary rejection: Tensor of shape {tuple(physical_moisture_grid.shape)} matches "
                f"backbone latent dimensions (feature_dim={self.feature_dim}). Latent embeddings cannot "
                f"be passed directly to RichardsSoilPhysicsEngine as volumetric soil moisture. "
                f"No verified latent-to-physical mapping currently exists."
            )

        if physical_moisture_grid.dim() < 2:
            raise ValueError(
                f"physical_moisture_grid must have at least 2 spatial dimensions, got {physical_moisture_grid.dim()}-D."
            )

        if not torch.isfinite(physical_moisture_grid).all():
            raise ValueError("physical_moisture_grid contains non-finite values (NaN or Inf).")

        if (physical_moisture_grid < 0.0).any() or (physical_moisture_grid > 1.0).any():
            raise ValueError(
                "Boundary rejection: physical_moisture_grid values outside physical bounds [0.0, 1.0] "
                "for volumetric water content."
            )

        return self.physics_engine.compute_richards_flux(physical_moisture_grid)

    def compute_composite_loss(
        self,
        latent_representation: torch.Tensor,
        target_representation: Optional[torch.Tensor] = None,
        physical_moisture_grid: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        Computes the composite loss for backbone training.

        Terms:
          - Representation Loss: MSE(latent_representation, target_representation)
            Units: dimensionless squared feature difference.
            Weight: self.w_representation (default 1.0)
          - Physics Constraint Loss: Richards lateral flux divergence penalty
            Evaluated ONLY when an independent physical moisture grid is provided.
            Units: (cm/day)^2 flux penalty.
            Weight: self.w_physics (default 0.5)
        """
        if target_representation is None:
            raise ValueError(
                "target_representation must be provided to compute representation loss. "
                "Supervised physical soil targets are unavailable."
            )

        if not isinstance(target_representation, torch.Tensor):
            raise TypeError("target_representation must be a torch.Tensor.")

        if latent_representation.shape != target_representation.shape:
            raise ValueError(
                f"Shape mismatch: latent_representation shape {tuple(latent_representation.shape)} "
                f"!= target_representation shape {tuple(target_representation.shape)}."
            )

        if not torch.isfinite(target_representation).all():
            raise ValueError("target_representation contains non-finite values (NaN or Inf).")

        loss_repr = nn.functional.mse_loss(latent_representation, target_representation)
        total_loss = self.w_representation * loss_repr
        loss_dict: Dict[str, torch.Tensor] = {
            "total_loss": total_loss,
            "loss_representation": loss_repr,
        }

        if physical_moisture_grid is not None:
            phys_out = self.compute_physics_loss(physical_moisture_grid)
            loss_physics = phys_out["physics_constraint_loss"]
            total_loss = total_loss + self.w_physics * loss_physics
            loss_dict["total_loss"] = total_loss
            loss_dict["loss_physics"] = loss_physics

        if not torch.isfinite(total_loss):
            raise FloatingPointError("Computed total_loss is non-finite (NaN or Inf).")

        return loss_dict

    def train_step(
        self,
        datacube_batch: Union[torch.Tensor, np.ndarray],
        target_representation: Union[torch.Tensor, np.ndarray],
        physical_moisture_grid: Optional[torch.Tensor] = None,
    ) -> Dict[str, Any]:
        """
        Executes a single end-to-end PyTorch training step:
        Forward -> Loss -> backward() -> optimizer.step()

        Returns:
          Dictionary of float loss metrics and execution metadata.
        """
        self.encoder.train()
        self.optimizer.zero_grad()

        # Validate inputs
        device = next(self.encoder.parameters()).device
        datacube = self.validate_input_tensor(datacube_batch).to(device)

        if isinstance(target_representation, np.ndarray):
            target_repr = torch.from_numpy(target_representation).float()
        else:
            target_repr = target_representation
        target_repr = target_repr.to(device)

        if physical_moisture_grid is not None:
            physical_moisture_grid = physical_moisture_grid.to(device)

        # 1. Forward Pass
        out = self.encoder(datacube)
        latent = out["latent_representation"]

        # 2. Loss Computation
        loss_dict = self.compute_composite_loss(
            latent,
            target_representation=target_repr,
            physical_moisture_grid=physical_moisture_grid,
        )
        total_loss = loss_dict["total_loss"]

        # 3. Backward Pass
        total_loss.backward()

        # 4. Optimizer Step
        self.optimizer.step()

        metrics: Dict[str, Any] = {
            "total_loss": float(total_loss.item()),
            "loss_representation": float(loss_dict["loss_representation"].item()),
            "latent_shape": tuple(latent.shape),
        }
        if "loss_physics" in loss_dict:
            metrics["loss_physics"] = float(loss_dict["loss_physics"].item())

        logging.info(
            f"✅ Train Step Completed | Total Loss: {metrics['total_loss']:.6f} | "
            f"Repr Loss: {metrics['loss_representation']:.6f}"
        )
        return metrics

    def train_epoch(
        self,
        datacube_batch: Union[torch.Tensor, np.ndarray],
        target_representation: Optional[Union[torch.Tensor, np.ndarray]] = None,
        target_agro: Optional[Union[torch.Tensor, np.ndarray]] = None,
        target_civil: Optional[Union[torch.Tensor, np.ndarray]] = None,
        physical_moisture_grid: Optional[torch.Tensor] = None,
    ) -> Dict[str, Any]:
        """
        Executes an epoch pass over the datacube tensor.

        Notice on Agro & Civil Targets:
          Providing target_agro or target_civil raises NotImplementedError because
          SpatialTemporalEncoderBackbone does not possess calibrated projection heads
          for physical soil moisture or civil bearing capacity.
        """
        if target_agro is not None or target_civil is not None:
            raise NotImplementedError(
                "Supervised agriculture/civil multitask training is BLOCKED: "
                "SpatialTemporalEncoderBackbone outputs an abstract latent embedding (B, feature_dim, H, W) "
                "without calibrated agricultural/civil projection heads. Genuine in-situ soil moisture "
                "and civil geotechnical ground-truth are unavailable in the data pipeline. "
                "Use target_representation for valid backbone representation training."
            )

        if target_representation is None:
            raise ValueError(
                "target_representation must be provided for train_epoch. "
                "Supervised physical soil targets are unavailable."
            )

        return self.train_step(
            datacube_batch=datacube_batch,
            target_representation=target_representation,
            physical_moisture_grid=physical_moisture_grid,
        )


if __name__ == "__main__":
    print("\n--- Self-Test: AETHER-MRID1607X Multi-Task Training Orchestrator ---")
    torch.manual_seed(42)

    # In-channels: 5 (SAR_VV, SAR_VH, SAR_POL_RATIO, OPTICAL_NDVI, OPTICAL_NDMI)
    # Shape: (B=2, T=3, C=5, H=16, W=16)
    mock_datacube = torch.randn(2, 3, 5, 16, 16)
    mock_target_repr = torch.randn(2, 64, 16, 16)

    trainer = MultiTaskTrainingOrchestrator(in_channels=5, feature_dim=64, learning_rate=1e-3)
    metrics = trainer.train_epoch(mock_datacube, target_representation=mock_target_repr)

    assert "total_loss" in metrics and "loss_representation" in metrics
    assert metrics["total_loss"] > 0
    print(f"[SUCCESS] MultiTaskTrainingOrchestrator: PASSED OPERATIONAL CHECKS! Total Loss: {metrics['total_loss']:.6f}\n")
