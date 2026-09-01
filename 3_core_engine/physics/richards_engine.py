# THE MRIDANSH - RICHARDS ENGINE (RIC_ED)
# DEVELOPED BY - JCC

import logging

import numpy as np

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class RichardsSoilPhysicsEngine:
    """1D Unsaturated Soil water Dynamics Using Van Genuchten & Richards Equation Principle."""

    def __init__(
        self, alpha: float = 0.035, n_param: float = 1.48, ks_sat: float = 10.5
    ):
        # Van Genuctten Mualem soil hydraulic parameters (Default: Loam soil)
        self.alpha = alpha  # Inverse Of Air-entry suction (1 / cm)
        self.n = n_param  # Pore-size distribution index
        self.m = 1.0 - (1.0 / self.n)
        self.ks_sat = ks_sat  # Saturated Hydraulic conductivity (cm/day)

    def calculate_relative_hydraulic_conductivity(
        self,
        volumetric_water_content: np.ndarray,
        theta_res: float = 0.078,
        theta_sat: float = 0.43,
    ) -> np.ndarray:
        """Computes Relative hydraulic conductivity K(Theta) Based on Effective Saturation."""
        logging.info("💧 Calculating Soil Relative Hydraulic Coductivity Matrix....")

        # Effective Saturation (Se)
        se = (volumetric_water_content - theta_res) / (theta_sat - theta_res)
        se = np.clip(se, 1e-5, 1.0)

        # Mualem`s Relative Hydraulic Conductivity Model
        k_relative = (se**0.5) * (1.0 - (1.0 - (se ** (1.0 / self.m))) ** self.m) ** 2
        return k_relative.astype(np.float32)

    def compute_richards_flux(
        self, moisture_grid: np.ndarray, depth_interval_m: float = 0.1
    ) -> dict[str, np.ndarray]:
        """Calculates 1D Richards equation hydraulic head gradient & water flus divergence."""
        logging.info(
            "📐 Executing 1D Unsaturated Soil Richards Equation Flux Computation..."
        )

        # Relative Conductivity
        k_rel = self.calculate_relative_hydraulic_conductivity(moisture_grid)
        k_actual = self.ks_sat * k_rel

        # Spatial Moisture Gradient (dtheta / dz)
        grad_y, grad_x = np.gradient(moisture_grid, depth_interval_m)
        total_gradient = np.sqrt(grad_x**2 + grad_y**2)

        # Flux (Q) = -k * grad(H)
        water_flux = -k_actual * total_gradient

        # Mass Conservation Balance / Constraint Violation Penalty
        physics_loss = np.mean(np.square(np.maximum(0, -water_flux)))

        logging.info(
            f"✅ Physics Engine Processed; Mean Water Flux: {np.mean(water_flux):.4f} cm/day | Loss Penalty = {physics_loss:.6f}"
        )

        return {
            "hydraulic_conductivity": k_actual,
            "water_flux": water_flux,
            "physics_constraint_loss": np.array(physics_loss, dtype=np.float32),
        }


# Self-Test Execution Module
if __name__ == "__main__":
    print("\n--- Testing Monday (Day 7) Soil Richards Physics Constraints Engine ---")

    physics_engine = RichardsSoilPhysicsEngine()

    # Mock Soil Moisture Matrix (120 * 120 Spatial Field, values between residual 0.10 and saturated 0.40)
    mock_moisture = np.random.uniform(0.12, 0.38, size=(120, 120)).astype(np.float32)

    physics_results = physics_engine.compute_richards_flux(
        mock_moisture, depth_interval_m=0.1
    )

    assert (
        "hydraulic_conductivity" in physics_results
        and "physics_constraint_loss" in physics_results
    )
    assert physics_results["hydraulic_conductivity"].shape == (120, 120)

    print(
        "\n[SUCCESS] Monday (Day 7) Soil Richards Physics Engine: PASSED OPERATIONAL CHECKS!\n"
    )
