"""
THE MRIDANSH — AETHER-MRID1607X CENTRAL ENGINE
Module: 3_core_engine/physics/pinn_richards.py
Role: Continuous Space-Time Richards PDE PINN Solver & Mass Conservation Evaluator

Scientific Formulations:
  - 1D Richards Vadose Hydrology Mass Conservation Equation:
      d(theta)/dt = d/dz [ K(theta) * (d(psi)/dz - 1) ]
  - Continuity Flux Form:
      q(z, t) = -K(theta) * (d(theta)/dz + 1.0)
      R_Richards(z, t) = d(theta)/dt + dq/dz
  - Certified Benchmark (Notebook 12 Pillar 3):
      R_Richards <= 1.20e-4 m3/m3 (Operational Conservation Threshold)

Operational Contracts:
  - PyTorch 2nd-order autograd derivative engine for continuous space-time evaluation.
  - Zero-defect state loading from certified checkpoint (pinn_richards_model.pt).
  - Physical boundary clamping & unphysical state penalization [theta_r, theta_s].
"""

import os
from typing import Dict, Tuple, Union, Optional
import torch
import torch.nn as nn

from .van_genuchten import VanGenuchtenEngine, SoilHydraulicParams, USDA_SOIL_CATALOG, EPSILON


class PhysicsInformedNN(nn.Module):
    """
    Continuous Space-Time Neural Solver for 1D Richards PDE.
    Maps Coordinate (z, t) -> Volumetric Moisture theta(z, t).
    Preserves exact layer naming for zero-defect checkpoint compatibility.
    """

    def __init__(
        self,
        in_dim: int = 2,
        hidden_dim: int = 64,
        num_layers: int = 4,
        out_dim: int = 1
    ):
        super(PhysicsInformedNN, self).__init__()
        self.in_dim = in_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.out_dim = out_dim

        layers = [nn.Linear(in_dim, hidden_dim), nn.Tanh()]
        for _ in range(num_layers - 1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.Tanh())
        layers.append(nn.Linear(hidden_dim, out_dim))
        self.network = nn.Sequential(*layers)

    def forward(
        self,
        z: torch.Tensor,
        t: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward evaluation mapping spatio-temporal coordinates to volumetric moisture.
        Supports both (z, t) separate inputs or a single concatenated (zt) input tensor.
        """
        if t is not None:
            if z.dim() == 1:
                z = z.unsqueeze(-1)
            if t.dim() == 1:
                t = t.unsqueeze(-1)
            zt = torch.cat([z, t], dim=-1)
        else:
            zt = z

        return self.network(zt)

    @classmethod
    def from_pretrained(
        cls,
        checkpoint_path: str = "5_storage/checkpoints/pinn_richards_model.pt",
        map_location: str = "cpu"
    ) -> "PhysicsInformedNN":
        """
        Loads pre-trained certified PINN weights from disk with strict verification.
        """
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"Checkpoint not found at: {checkpoint_path}")

        ckpt = torch.load(checkpoint_path, map_location=map_location, weights_only=False)
        in_dim = ckpt.get("in_dim", 2)
        hidden_dim = ckpt.get("hidden_dim", 64)
        num_layers = ckpt.get("num_layers", 4)
        out_dim = ckpt.get("out_dim", 1)

        model = cls(in_dim=in_dim, hidden_dim=hidden_dim, num_layers=num_layers, out_dim=out_dim)
        state_dict = ckpt.get("model_state_dict", ckpt)
        model.load_state_dict(state_dict, strict=True)
        model.eval()
        return model


# Production Alias
RichardsPINN = PhysicsInformedNN


class RichardsResidualEvaluator:
    """
    High-order Autograd Evaluator for continuous 1D Richards PDE Mass Conservation Residual.
    Computes exact temporal and spatial derivatives to verify conservation of mass:
      R_Richards(z, t) = d(theta)/dt + dq/dz
    """

    def __init__(
        self,
        model: nn.Module,
        soil_engine: Optional[VanGenuchtenEngine] = None
    ):
        self.model = model
        self.soil_engine = soil_engine if soil_engine is not None else VanGenuchtenEngine('loam')

    def evaluate_residual(
        self,
        z: torch.Tensor,
        t: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Computes continuous PDE residual, predicted moisture, and downward Darcy flux.

        Args:
          z: Depth coordinate tensor [cm], shape (N, 1) or (N,)
          t: Time coordinate tensor [hours], shape (N, 1) or (N,)

        Returns:
          pde_residual: Mass conservation residual (N, 1) [cm3/cm3 per hr]
          theta_pred: Predicted volumetric soil moisture (N, 1) [cm3/cm3]
          flux_q: Downward Darcian unsaturated moisture flux (N, 1) [cm/hr]
        """
        if z.dim() == 1:
            z = z.unsqueeze(-1)
        if t.dim() == 1:
            t = t.unsqueeze(-1)

        # Clone and enable autograd on coordinate tensors
        z_col = z.clone().detach().requires_grad_(True)
        t_col = t.clone().detach().requires_grad_(True)

        # 1. Forward model prediction theta(z, t)
        theta_pred = self.model(z_col, t_col)

        # 2. Temporal Derivative: d(theta)/dt [cm3/cm3 per hr]
        dtheta_dt = torch.autograd.grad(
            outputs=theta_pred,
            inputs=t_col,
            grad_outputs=torch.ones_like(theta_pred),
            create_graph=True,
            retain_graph=True
        )[0]

        # 3. Spatial Gradient: d(theta)/dz [1/cm]
        dtheta_dz = torch.autograd.grad(
            outputs=theta_pred,
            inputs=z_col,
            grad_outputs=torch.ones_like(theta_pred),
            create_graph=True,
            retain_graph=True
        )[0]

        # 4. Unsaturated Hydraulic Conductivity K(theta) [cm/hr]
        k_val = self.soil_engine.conductivity_torch(theta_pred)

        # 5. Unsaturated Darcian Flux with Gravity Head: q = -K * (d(theta)/dz + 1.0)
        flux_q = -k_val * (dtheta_dz + 1.0)

        # 6. Spatial Divergence of Flux: dq/dz
        dq_dz = torch.autograd.grad(
            outputs=flux_q,
            inputs=z_col,
            grad_outputs=torch.ones_like(flux_q),
            create_graph=True,
            retain_graph=True
        )[0]

        # 7. Mass Conservation Continuity Residual: R = d(theta)/dt + dq/dz
        pde_residual = dtheta_dt + dq_dz

        return pde_residual, theta_pred, flux_q


class RichardsPhysicsLoss(nn.Module):
    """
    Multi-objective Physics-Informed Loss Function penalizing non-conservation,
    boundary condition divergence, and unphysical state bounds.
    """

    def __init__(
        self,
        evaluator: RichardsResidualEvaluator,
        w_pde: float = 1.0,
        w_data: float = 1.0,
        w_bc: float = 0.5,
        w_penalty: float = 5.0
    ):
        super(RichardsPhysicsLoss, self).__init__()
        self.evaluator = evaluator
        self.w_pde = w_pde
        self.w_data = w_data
        self.w_bc = w_bc
        self.w_penalty = w_penalty
        self.mse = nn.MSELoss()

    def forward(
        self,
        z_col: torch.Tensor,
        t_col: torch.Tensor,
        z_data: Optional[torch.Tensor] = None,
        t_data: Optional[torch.Tensor] = None,
        theta_obs: Optional[torch.Tensor] = None,
        z_bc: Optional[torch.Tensor] = None,
        t_bc: Optional[torch.Tensor] = None,
        theta_bc: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Computes composite multi-task physics loss dictionary.
        """
        # 1. PDE Mass Conservation Residual
        pde_res, theta_pred_col, _ = self.evaluator.evaluate_residual(z_col, t_col)
        loss_pde = torch.mean(pde_res.pow(2.0))

        # 2. Data Fitting Loss (if observations available)
        loss_data = torch.tensor(0.0, device=z_col.device)
        if z_data is not None and t_data is not None and theta_obs is not None:
            theta_pred_data = self.evaluator.model(z_data, t_data)
            loss_data = self.mse(theta_pred_data, theta_obs)

        # 3. Boundary Condition Loss
        loss_bc = torch.tensor(0.0, device=z_col.device)
        if z_bc is not None and t_bc is not None and theta_bc is not None:
            theta_pred_bc = self.evaluator.model(z_bc, t_bc)
            loss_bc = self.mse(theta_pred_bc, theta_bc)

        # 4. Unphysical Bound Penalty: penalize theta outside [theta_r, theta_s]
        p = self.evaluator.soil_engine.params
        lower_viol = torch.relu(p.theta_r - theta_pred_col)
        upper_viol = torch.relu(theta_pred_col - p.theta_s)
        loss_penalty = torch.mean(lower_viol.pow(2.0) + upper_viol.pow(2.0))

        total_loss = (
            self.w_pde * loss_pde +
            self.w_data * loss_data +
            self.w_bc * loss_bc +
            self.w_penalty * loss_penalty
        )

        return {
            "total_loss": total_loss,
            "loss_pde": loss_pde,
            "loss_data": loss_data,
            "loss_bc": loss_bc,
            "loss_penalty": loss_penalty,
            "max_residual": torch.max(torch.abs(pde_res))
        }


def clamp_vadose_moisture(
    theta: torch.Tensor,
    theta_r: float = 0.05,
    theta_s: float = 0.45
) -> torch.Tensor:
    """
    Enforces physical hard-clamping to prevent unphysical moisture states.
    """
    return torch.clamp(theta, min=theta_r, max=theta_s)
