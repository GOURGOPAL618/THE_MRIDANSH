# THE MRIDANSH - CIVIL & GEOTECHNICAL DOMAIN TRANSLATOR
# Module: 4_domain_translators/civil/slope_stability_engine.py
# Subsystem 05 of AETHER-MRID1607X Core Engine
# Architecture: Terzaghi-Taylor-Duncan Infinite Slope Stability / Copernicus 30m DEM Coupled

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

try:
    from .soil_mechanics_core import GeotechnicalParameters, SoilMechanicsCoreEngine
except ImportError:
    from soil_mechanics_core import GeotechnicalParameters, SoilMechanicsCoreEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

MAX_FS_CLAMP: float = 10.0  # Certified numerical ceiling for flat topography (beta -> 0)
MIN_FS_CLAMP: float = 0.10  # Numerical floor for extreme shear liquefaction


@dataclass(frozen=True)
class SlopeStabilityResult:
    """Result of DEM-coupled infinite slope stability and landslide hazard analysis."""
    factor_of_safety: np.ndarray
    hazard_class_raster: np.ndarray  # 0: Stable, 1: Marginally Stable, 2: Landslide Hazard
    resisting_stress_kpa: np.ndarray
    driving_stress_kpa: np.ndarray
    pore_water_pressure_kpa: np.ndarray
    slope_angle_deg: np.ndarray
    mean_factor_of_safety: float
    hazard_summary: dict


class SlopeStabilityEngine:
    """
    Evaluates 2D/3D slope stability and landslide susceptibility by coupling
    Copernicus 30m DEM terrain slope (beta) with spaceborne vadose pore pressure (u)
    and unsaturated shear strength via the Taylor-Duncan Infinite Slope formulation.
    """

    def __init__(
        self,
        soil_engine: Optional[SoilMechanicsCoreEngine] = None,
        slip_surface_depth_m: float = 2.0,
    ):
        self.soil_engine = soil_engine or SoilMechanicsCoreEngine()
        self.z_slip = float(slip_surface_depth_m)
        if self.z_slip <= 0.0:
            raise ValueError(f"Slip surface depth must be positive, got {self.z_slip}")

    def compute_slope_stability(
        self,
        slope_deg: np.ndarray,
        theta_rz: np.ndarray,
        soil_class: str = "silt_loam",
    ) -> SlopeStabilityResult:
        """
        Calculates the Factor of Safety (FS) against planar slope failure:
        FS = [c' + (gamma_sat * z * cos^2(beta) - u_w) * tan(phi')] / [gamma_sat * z * sin(beta) * cos(beta)]
        """
        params = self.soil_engine.get_parameters(soil_class)
        slope_arr = np.asarray(slope_deg, dtype=np.float32)
        theta_arr = np.asarray(theta_rz, dtype=np.float32)

        # 1. Suction & Pore Water Pressure from vadose moisture
        se = self.soil_engine.compute_effective_saturation(theta_arr, params.theta_res, params.theta_sat)
        psi = self.soil_engine.compute_matric_suction(se, params.van_genuchten_alpha_1_cm, params.van_genuchten_n)
        u_w = self.soil_engine.compute_pore_water_pressure(psi)  # In unsaturated zone, u_w = -psi <= 0

        # 2. Angle conversions and flat-ground singularity management
        # Effective slope bounded to [0.1 deg, 85.0 deg]
        beta_clamped = np.clip(slope_arr, 0.1, 85.0)
        beta_rad = np.radians(beta_clamped)

        cos_beta = np.cos(beta_rad)
        sin_beta = np.sin(beta_rad)
        cos2_beta = cos_beta ** 2

        # 3. Normal total stress along slip surface
        # sigma_n = gamma_sat * z * cos^2(beta)
        gamma_sat = params.saturated_unit_weight_kn_m3
        total_normal_stress = gamma_sat * self.z_slip * cos2_beta

        # 4. Effective normal stress: sigma' = sigma_n - u_w = sigma_n + psi
        effective_normal_stress = np.maximum(0.0, total_normal_stress - u_w)

        # 5. Resisting Shear Strength (Numerator)
        # tau_res = c' + sigma' * tan(phi')
        tan_phi = np.tan(params.friction_angle_rad)
        resisting_shear = params.cohesion_kpa + effective_normal_stress * tan_phi

        # 6. Driving Gravitational Shear Stress (Denominator)
        # tau_drive = gamma_sat * z * sin(beta) * cos(beta)
        driving_shear = gamma_sat * self.z_slip * sin_beta * cos_beta

        # 7. Factor of Safety Calculation
        # Guard against division by near-zero on flat terrain
        fs_raw = resisting_shear / np.maximum(1e-3, driving_shear)

        # If native slope < 0.5 degrees, terrain is effectively flat -> clamp to MAX_FS_CLAMP
        flat_mask = slope_arr < 0.5
        fs = np.where(flat_mask, MAX_FS_CLAMP, np.clip(fs_raw, MIN_FS_CLAMP, MAX_FS_CLAMP))

        # 8. Hazard Classification
        # 0: STABLE (FS >= 1.5)
        # 1: MARGINALLY_STABLE (1.0 <= FS < 1.5)
        # 2: LANDSLIDE_HAZARD (FS < 1.0)
        hazard_raster = np.zeros_like(fs, dtype=np.int32)
        hazard_raster[(fs >= 1.0) & (fs < 1.5)] = 1
        hazard_raster[fs < 1.0] = 2

        # Summary statistics
        total_px = int(fs.size)
        n_stable = int(np.sum(hazard_raster == 0))
        n_marginal = int(np.sum(hazard_raster == 1))
        n_hazard = int(np.sum(hazard_raster == 2))

        summary = {
            "total_pixels": total_px,
            "stable_pixels": n_stable,
            "stable_pct": float((n_stable / total_px) * 100.0),
            "marginal_pixels": n_marginal,
            "marginal_pct": float((n_marginal / total_px) * 100.0),
            "hazard_pixels": n_hazard,
            "hazard_pct": float((n_hazard / total_px) * 100.0),
            "mean_fs": float(np.mean(fs)),
            "min_fs": float(np.min(fs)),
            "max_fs": float(np.max(fs)),
        }

        self.assert_invariants(fs, hazard_raster)

        return SlopeStabilityResult(
            factor_of_safety=fs.astype(np.float32),
            hazard_class_raster=hazard_raster,
            resisting_stress_kpa=resisting_shear.astype(np.float32),
            driving_stress_kpa=driving_shear.astype(np.float32),
            pore_water_pressure_kpa=u_w.astype(np.float32),
            slope_angle_deg=slope_arr,
            mean_factor_of_safety=float(np.mean(fs)),
            hazard_summary=summary,
        )

    @staticmethod
    def assert_invariants(fs: np.ndarray, hazard_class: np.ndarray) -> None:
        """
        DO-178C Level-A Invariants:
        1. Non-negativity: FS > 0 everywhere
        2. Boundedness: FS in [MIN_FS_CLAMP, MAX_FS_CLAMP]
        3. Hazard class values strictly in {0, 1, 2}
        4. Zero NaNs and Zero Infs
        """
        if np.any(fs <= 0.0):
            raise AssertionError("Factor of Safety contains non-positive values!")
        if np.any(fs < (MIN_FS_CLAMP - 1e-4)) or np.any(fs > (MAX_FS_CLAMP + 1e-4)):
            raise AssertionError("Factor of Safety exceeds physical clipping limits!")
        if not np.all(np.isin(hazard_class, [0, 1, 2])):
            raise AssertionError("Hazard class contains invalid enum integers!")
        if np.any(np.isnan(fs)) or np.any(np.isinf(fs)):
            raise AssertionError("NaNs or Infs detected in Factor of Safety raster!")
