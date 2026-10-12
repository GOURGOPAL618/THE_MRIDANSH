import logging
import torch
import torch.nn as nn
from typing import Dict

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

class RichardsSoilPhysicsEngine(nn.Module):
    """
    1D Unsaturated Soil water Dynamics Using Van Genuchten & Richards Equation Principle.
    
    NOTE: The current numerical formulation computes a 2D lateral spatial gradient 
    across the geographical grid (grad_x, grad_y) rather than a true vertical 1D depth profile,
    and it computes purely gradient-driven diffusion while omitting the gravity head (z).
    As required by the scope, this formulation is preserved exactly as a prototype solver.
    """

    def __init__(
        self, alpha: float = 0.035, n_param: float = 1.48, ks_sat: float = 10.5
    ):
        super().__init__()
        # Van Genuchten Mualem soil hydraulic parameters (Default: Loam soil)
        self.alpha = nn.Parameter(torch.tensor(alpha, dtype=torch.float32))
        self.n = nn.Parameter(torch.tensor(n_param, dtype=torch.float32))
        self.ks_sat = nn.Parameter(torch.tensor(ks_sat, dtype=torch.float32))

    def calculate_relative_hydraulic_conductivity(
        self,
        volumetric_water_content: torch.Tensor,
        theta_res: float = 0.078,
        theta_sat: float = 0.43,
    ) -> torch.Tensor:
        """Computes Relative hydraulic conductivity K(Theta) Based on Effective Saturation."""
        logging.info("💧 Calculating Soil Relative Hydraulic Conductivity Matrix (PyTorch)....")

        # Dynamic m parameter based on n
        m = 1.0 - (1.0 / self.n)

        # Effective Saturation (Se)
        se = (volumetric_water_content - theta_res) / (theta_sat - theta_res)
        
        # Clamp to avoid numerical instability (negative saturation or > 1)
        # Using a small eps > 0 to avoid derivative singularities at exactly 0.0
        se = torch.clamp(se, min=1e-5, max=1.0)

        # Mualem's Relative Hydraulic Conductivity Model
        # K_rel = Se^0.5 * (1 - (1 - Se^(1/m))^m)^2
        # To avoid NaN gradients, ensure the inner term (1 - Se^(1/m)) is clamped > 0
        inner_pow = torch.pow(se, 1.0 / m)
        inner_term = torch.clamp(1.0 - inner_pow, min=1e-7)
        k_relative = torch.sqrt(se) * torch.square(1.0 - torch.pow(inner_term, m))
        
        return k_relative

    def compute_richards_flux(
        self, moisture_grid: torch.Tensor, depth_interval_m: float = 0.1
    ) -> dict[str, torch.Tensor]:
        """Calculates 1D Richards equation hydraulic head gradient & water flux divergence."""
        logging.info(
            "📐 Executing 1D Unsaturated Soil Richards Equation Flux Computation (Differentiable)..."
        )
        
        # Relative Conductivity
        k_rel = self.calculate_relative_hydraulic_conductivity(moisture_grid)
        k_actual = self.ks_sat * k_rel

        # Spatial Moisture Gradient (dtheta / dz)
        # Evaluated along the last two spatial dimensions (y, x) 
        if moisture_grid.dim() < 2:
            raise ValueError(f"moisture_grid must have at least 2 spatial dimensions, got shape {moisture_grid.shape}")
            
        grad_y, grad_x = torch.gradient(moisture_grid, spacing=depth_interval_m, dim=(-2, -1))
        
        # Add epsilon to prevent NaN gradients in torch.sqrt when gradient is exactly zero
        eps = 1e-12
        total_gradient = torch.sqrt(torch.square(grad_x) + torch.square(grad_y) + eps)

        # Flux (Q) = -k * grad(H) 
        water_flux = -k_actual * total_gradient

        # Mass Conservation Balance / Constraint Violation Penalty
        # Penalty for negative fluxes (as implemented in original)
        physics_loss = torch.mean(torch.square(torch.clamp(-water_flux, min=0.0)))

        logging.info(
            f"✅ Physics Engine Processed; Mean Water Flux: {torch.mean(water_flux).item():.4f} cm/day | Loss Penalty = {physics_loss.item():.6f}"
        )

        return {
            "hydraulic_conductivity": k_actual,
            "water_flux": water_flux,
            "physics_constraint_loss": physics_loss,
        }

# Self-Test Execution Module
if __name__ == "__main__":
    print("\n--- Testing Monday (Day 7) Soil Richards Physics Constraints Engine ---")

    physics_engine = RichardsSoilPhysicsEngine()

    # Mock Soil Moisture Matrix (120 * 120 Spatial Field, values between residual 0.10 and saturated 0.40)
    mock_moisture = torch.empty(120, 120, dtype=torch.float32).uniform_(0.12, 0.38)
    mock_moisture.requires_grad_(True)

    physics_results = physics_engine.compute_richards_flux(
        mock_moisture, depth_interval_m=0.1
    )

    assert (
        "hydraulic_conductivity" in physics_results
        and "physics_constraint_loss" in physics_results
    )
    assert physics_results["hydraulic_conductivity"].shape == (120, 120)

    # Test Autograd Backward
    loss = physics_results["physics_constraint_loss"]
    loss.backward()
    assert mock_moisture.grad is not None

    print(
        "\n[SUCCESS] Monday (Day 7) Soil Richards Physics Engine: PASSED OPERATIONAL CHECKS!\n"
    )
