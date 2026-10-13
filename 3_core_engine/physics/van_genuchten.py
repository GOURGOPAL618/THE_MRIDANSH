"""
THE MRIDANSH — AETHER-MRID1607X CENTRAL ENGINE
Module: 3_core_engine/physics/van_genuchten.py
Role: Analytical Soil-Water Retention Curve (SWRC) & Unsaturated Conductivity Engine

Scientific Formulations:
  - van Genuchten (1980): Soil Water Retention Curve (SWRC)
  - Mualem (1976): Pore-size distribution and unsaturated hydraulic conductivity
  - USDA / Carsel & Parrish (1988): Standard pedotransfer hydraulic parameters

Operational Contracts:
  - Differentiable PyTorch operators for PINN vadose solver autograd.
  - Vector-accelerated NumPy operators for high-throughput spatial GIS raster calculation.
  - Strict float32/float64 numerical stability bounds (Ariane-5 overflow/underflow protection).
"""

from dataclasses import dataclass
from typing import Dict, Union, Optional
import numpy as np
import torch


# Constant EPSILON for numerical singularities (zero suction / zero conductivity)
EPSILON: float = 1e-7


@dataclass(frozen=True)
class SoilHydraulicParams:
    """
    Physical Soil Hydraulic Parameter Set for van Genuchten - Mualem model.
    Units:
      - theta_r: [m3/m3] Residual volumetric water content
      - theta_s: [m3/m3] Saturated volumetric water content (porosity limit)
      - alpha:   [1/cm]  Inverse of air-entry suction head (alpha > 0)
      - n:       [-]     Pore-size distribution parameter (n > 1)
      - Ks:      [cm/hr] Saturated hydraulic conductivity
      - l:       [-]     Tortuosity / connectivity coefficient (standard = 0.5)
      - m:       [-]     Derived van Genuchten parameter m = 1 - 1/n
    """
    theta_r: float
    theta_s: float
    alpha: float
    n: float
    Ks: float
    l: float = 0.5
    m: float = None

    def __post_init__(self):
        # Strict Physical Validations
        if self.theta_r < 0.0:
            raise ValueError(f"Residual water content theta_r must be non-negative: {self.theta_r}")
        if self.theta_s <= self.theta_r:
            raise ValueError(f"Saturated water content theta_s ({self.theta_s}) must exceed theta_r ({self.theta_r})")
        if self.alpha <= 0.0:
            raise ValueError(f"Air-entry parameter alpha must be strictly positive: {self.alpha}")
        if self.n <= 1.0:
            raise ValueError(f"Pore-size distribution parameter n must be strictly > 1.0: {self.n}")
        if self.Ks <= 0.0:
            raise ValueError(f"Saturated hydraulic conductivity Ks must be strictly positive: {self.Ks}")

        # Compute and assign derived m parameter if not explicitly set
        if self.m is None:
            object.__setattr__(self, 'm', 1.0 - (1.0 / self.n))


# Certified USDA / Carsel & Parrish (1988) Soil Hydraulic Catalog
USDA_SOIL_CATALOG: Dict[str, SoilHydraulicParams] = {
    'sandy_loam': SoilHydraulicParams(
        theta_r=0.065,
        theta_s=0.410,
        alpha=0.075,
        n=1.89,
        Ks=4.42,
        l=0.5
    ),
    'loam': SoilHydraulicParams(
        theta_r=0.078,
        theta_s=0.430,
        alpha=0.036,
        n=1.56,
        Ks=1.04,
        l=0.5
    ),
    'silt_loam': SoilHydraulicParams(
        theta_r=0.067,
        theta_s=0.450,
        alpha=0.020,
        n=1.41,
        Ks=0.45,
        l=0.5
    ),
    'clay': SoilHydraulicParams(
        theta_r=0.068,
        theta_s=0.380,
        alpha=0.008,
        n=1.09,
        Ks=0.20,
        l=0.5
    ),
    'sand': SoilHydraulicParams(
        theta_r=0.045,
        theta_s=0.430,
        alpha=0.145,
        n=2.68,
        Ks=29.70,
        l=0.5
    )
}


class VanGenuchtenEngine:
    """
    Production-grade Analytical Soil Physics Engine implementing the van Genuchten - Mualem model.
    Provides mathematically synchronized NumPy and PyTorch execution paths with zero NaN leakage.
    """

    def __init__(self, params: Union[SoilHydraulicParams, str] = 'sandy_loam'):
        if isinstance(params, str):
            soil_key = params.lower().replace(" ", "_")
            if soil_key not in USDA_SOIL_CATALOG:
                raise KeyError(f"Unknown soil texture '{params}'. Available: {list(USDA_SOIL_CATALOG.keys())}")
            self.params = USDA_SOIL_CATALOG[soil_key]
            self.soil_name = soil_key
        elif isinstance(params, SoilHydraulicParams):
            self.params = params
            self.soil_name = "custom"
        else:
            raise TypeError(f"params must be SoilHydraulicParams or str, got {type(params)}")

    # =========================================================================
    # NUMPY VECTORIZED PIPELINE (GIS Rasters, CPU Processing)
    # =========================================================================

    def retention_numpy(self, psi: np.ndarray) -> np.ndarray:
        """
        Calculates Volumetric Soil Water Content theta(psi) [m3/m3] from Matric Suction Head psi [cm].
        Equation: theta = theta_r + (theta_s - theta_r) * [1 + (alpha * |psi|)^n]^(-m)
        """
        psi_arr = np.asarray(psi, dtype=np.float64)
        psi_abs = np.abs(psi_arr) + EPSILON

        # Effective Saturation Se in (0, 1]
        denom = 1.0 + (self.params.alpha * psi_abs) ** self.params.n
        eff_sat = denom ** (-self.params.m)
        eff_sat = np.clip(eff_sat, EPSILON, 1.0)

        theta = self.params.theta_r + (self.params.theta_s - self.params.theta_r) * eff_sat
        return np.clip(theta, self.params.theta_r, self.params.theta_s)

    def conductivity_numpy(self, theta: np.ndarray) -> np.ndarray:
        """
        Calculates Unsaturated Hydraulic Conductivity K(theta) [cm/hr] via Mualem-van Genuchten.
        Equation: K(Se) = Ks * Se^l * [1 - (1 - Se^(1/m))^m]^2
        """
        theta_arr = np.asarray(theta, dtype=np.float64)
        # Compute Effective Saturation Se
        delta_theta = self.params.theta_s - self.params.theta_r
        eff_sat = (theta_arr - self.params.theta_r) / max(delta_theta, EPSILON)
        eff_sat = np.clip(eff_sat, EPSILON, 1.0 - EPSILON)

        # Mualem integral solution
        term = 1.0 - (eff_sat ** (1.0 / self.params.m))
        term = np.clip(term, EPSILON, 1.0)
        bracket = 1.0 - (term ** self.params.m)
        bracket = np.clip(bracket, 0.0, 1.0)

        k_val = self.params.Ks * (eff_sat ** self.params.l) * (bracket ** 2.0)
        return np.clip(k_val, 0.0, self.params.Ks)

    def suction_head_numpy(self, theta: np.ndarray) -> np.ndarray:
        """
        Calculates Inverse Matric Suction Head |psi|(theta) [cm] from Volumetric Water Content.
        Equation: |psi| = (1 / alpha) * [Se^(-1/m) - 1]^(1/n)
        """
        theta_arr = np.asarray(theta, dtype=np.float64)
        delta_theta = self.params.theta_s - self.params.theta_r
        eff_sat = (theta_arr - self.params.theta_r) / max(delta_theta, EPSILON)
        eff_sat = np.clip(eff_sat, EPSILON, 1.0 - EPSILON)

        inner = (eff_sat ** (-1.0 / self.params.m)) - 1.0
        inner = np.clip(inner, 0.0, None)
        psi = (1.0 / self.params.alpha) * (inner ** (1.0 / self.params.n))
        return psi

    def capacity_numpy(self, psi: np.ndarray) -> np.ndarray:
        """
        Calculates Specific Moisture Capacity C(psi) = d(theta)/d(psi) [1/cm].
        Equation: C(psi) = alpha * m * n * (theta_s - theta_r) * (alpha * |psi|)^(n-1) * [1 + (alpha * |psi|)^n]^(-(m+1))
        """
        psi_arr = np.asarray(psi, dtype=np.float64)
        psi_abs = np.abs(psi_arr) + EPSILON

        p = self.params
        delta_theta = p.theta_s - p.theta_r
        a_psi = p.alpha * psi_abs

        numer = p.alpha * p.m * p.n * delta_theta * (a_psi ** (p.n - 1.0))
        denom = (1.0 + (a_psi ** p.n)) ** (p.m + 1.0)
        c_val = numer / np.maximum(denom, EPSILON)
        return np.clip(c_val, 0.0, None)

    # =========================================================================
    # PYTORCH DIFFERENTIABLE PIPELINE (PINN Loss Backprop, GPU/CPU Tensors)
    # =========================================================================

    def retention_torch(self, psi: torch.Tensor) -> torch.Tensor:
        """
        Differentiable PyTorch Soil Water Retention Function theta(psi) [m3/m3].
        Preserves backward computation graph for PINN physics loss residuals.
        """
        p = self.params
        psi_abs = torch.abs(psi) + EPSILON

        alpha_t = torch.tensor(p.alpha, dtype=psi.dtype, device=psi.device)
        n_t = torch.tensor(p.n, dtype=psi.dtype, device=psi.device)
        m_t = torch.tensor(p.m, dtype=psi.dtype, device=psi.device)
        theta_r_t = torch.tensor(p.theta_r, dtype=psi.dtype, device=psi.device)
        theta_s_t = torch.tensor(p.theta_s, dtype=psi.dtype, device=psi.device)

        denom = 1.0 + (alpha_t * psi_abs).pow(n_t)
        eff_sat = denom.pow(-m_t)
        eff_sat = torch.clamp(eff_sat, min=EPSILON, max=1.0)

        theta = theta_r_t + (theta_s_t - theta_r_t) * eff_sat
        return torch.clamp(theta, min=p.theta_r, max=p.theta_s)

    def conductivity_torch(self, theta: torch.Tensor) -> torch.Tensor:
        """
        Differentiable PyTorch Unsaturated Hydraulic Conductivity K(theta) [cm/hr].
        """
        p = self.params
        m_inv = 1.0 / p.m
        delta_theta = p.theta_s - p.theta_r

        eff_sat = (theta - p.theta_r) / max(delta_theta, EPSILON)
        eff_sat = torch.clamp(eff_sat, min=EPSILON, max=1.0 - EPSILON)

        term = 1.0 - eff_sat.pow(m_inv)
        term = torch.clamp(term, min=EPSILON, max=1.0)
        bracket = 1.0 - term.pow(p.m)
        bracket = torch.clamp(bracket, min=0.0, max=1.0)

        k_val = p.Ks * eff_sat.pow(p.l) * bracket.pow(2.0)
        return torch.clamp(k_val, min=0.0, max=p.Ks)

    def suction_head_torch(self, theta: torch.Tensor) -> torch.Tensor:
        """
        Differentiable PyTorch Inverse Matric Suction Head |psi|(theta) [cm].
        """
        p = self.params
        delta_theta = p.theta_s - p.theta_r

        eff_sat = (theta - p.theta_r) / max(delta_theta, EPSILON)
        eff_sat = torch.clamp(eff_sat, min=EPSILON, max=1.0 - EPSILON)

        inner = eff_sat.pow(-1.0 / p.m) - 1.0
        inner = torch.clamp(inner, min=0.0)
        psi = (1.0 / p.alpha) * inner.pow(1.0 / p.n)
        return psi

    def capacity_torch(self, psi: torch.Tensor) -> torch.Tensor:
        """
        Differentiable PyTorch Specific Moisture Capacity C(psi) = d(theta)/d(psi) [1/cm].
        """
        p = self.params
        psi_abs = torch.abs(psi) + EPSILON

        delta_theta = p.theta_s - p.theta_r
        a_psi = p.alpha * psi_abs

        numer = p.alpha * p.m * p.n * delta_theta * a_psi.pow(p.n - 1.0)
        denom = (1.0 + a_psi.pow(p.n)).pow(p.m + 1.0)
        c_val = numer / torch.clamp(denom, min=EPSILON)
        return torch.clamp(c_val, min=0.0)

    # =========================================================================
    # POLYMORPHIC ADAPTER METHODS (Auto-Dispatch by Type)
    # =========================================================================

    def retention(self, psi: Union[np.ndarray, torch.Tensor, float]) -> Union[np.ndarray, torch.Tensor, float]:
        """Polymorphic dispatcher for Soil Water Retention theta(psi)."""
        if isinstance(psi, torch.Tensor):
            return self.retention_torch(psi)
        elif isinstance(psi, np.ndarray):
            return self.retention_numpy(psi)
        elif isinstance(psi, (int, float)):
            return float(self.retention_numpy(np.array([psi]))[0])
        else:
            raise TypeError(f"Unsupported input type {type(psi)}")

    def conductivity(self, theta: Union[np.ndarray, torch.Tensor, float]) -> Union[np.ndarray, torch.Tensor, float]:
        """Polymorphic dispatcher for Unsaturated Hydraulic Conductivity K(theta)."""
        if isinstance(theta, torch.Tensor):
            return self.conductivity_torch(theta)
        elif isinstance(theta, np.ndarray):
            return self.conductivity_numpy(theta)
        elif isinstance(theta, (int, float)):
            return float(self.conductivity_numpy(np.array([theta]))[0])
        else:
            raise TypeError(f"Unsupported input type {type(theta)}")

    def suction_head(self, theta: Union[np.ndarray, torch.Tensor, float]) -> Union[np.ndarray, torch.Tensor, float]:
        """Polymorphic dispatcher for Inverse Matric Suction Head |psi|(theta)."""
        if isinstance(theta, torch.Tensor):
            return self.suction_head_torch(theta)
        elif isinstance(theta, np.ndarray):
            return self.suction_head_numpy(theta)
        elif isinstance(theta, (int, float)):
            return float(self.suction_head_numpy(np.array([theta]))[0])
        else:
            raise TypeError(f"Unsupported input type {type(theta)}")

    def capacity(self, psi: Union[np.ndarray, torch.Tensor, float]) -> Union[np.ndarray, torch.Tensor, float]:
        """Polymorphic dispatcher for Specific Moisture Capacity C(psi)."""
        if isinstance(psi, torch.Tensor):
            return self.capacity_torch(psi)
        elif isinstance(psi, np.ndarray):
            return self.capacity_numpy(psi)
        elif isinstance(psi, (int, float)):
            return float(self.capacity_numpy(np.array([psi]))[0])
        else:
            raise TypeError(f"Unsupported input type {type(psi)}")

    def __repr__(self) -> str:
        return (f"VanGenuchtenEngine(soil='{self.soil_name}', theta_r={self.params.theta_r:.3f}, "
                f"theta_s={self.params.theta_s:.3f}, alpha={self.params.alpha:.3f}, "
                f"n={self.params.n:.2f}, m={self.params.m:.4f}, Ks={self.params.Ks:.2f} cm/hr)")
