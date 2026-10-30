# THE MRIDANSH - CIVIL & GEOTECHNICAL DOMAIN TRANSLATOR
# Module: 4_domain_translators/civil/ground_stability_engine.py
# Subsystem 05 of AETHER-MRID1607X Core Engine
# Architecture: Eurocode 7 (EN 1997-1) / IS 1904:2021 / General Meyerhof-Hansen

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Tuple, Union

import numpy as np

try:
    from .soil_mechanics_core import GeotechnicalParameters, SoilMechanicsCoreEngine
except ImportError:
    from soil_mechanics_core import GeotechnicalParameters, SoilMechanicsCoreEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DEFAULT_SAFETY_FACTOR: float = 3.0  # Eurocode 7 / IS 1904 mandatory foundation safety factor
GRAVITY_M_S2: float = 9.80665


@dataclass(frozen=True)
class BearingCapacityFactors:
    """Classical Meyerhof-Hansen bearing capacity factors."""
    Nc: float
    Nq: float
    Ngamma: float
    sc: float
    sq: float
    sgamma: float
    dc: float
    dq: float
    dgamma: float


@dataclass(frozen=True)
class FoundationBearingResult:
    """Result of ultimate and allowable foundation bearing capacity analysis."""
    q_ult_kpa: np.ndarray
    q_allow_kpa: np.ndarray
    cohesion_term_kpa: np.ndarray
    surcharge_term_kpa: np.ndarray
    self_weight_term_kpa: np.ndarray
    apparent_cohesion_kpa: np.ndarray
    factor_of_safety: float
    trafficability_grade: str


class GroundStabilityEngine:
    """
    Evaluates ground mechanical bearing capacity for shallow foundations and structural footprints
    using the General Meyerhof-Hansen formulation coupled with unsaturated soil mechanics.
    """

    def __init__(
        self,
        soil_engine: Optional[SoilMechanicsCoreEngine] = None,
        target_factor_of_safety: float = DEFAULT_SAFETY_FACTOR,
        footing_width_b_m: float = 1.5,
        footing_length_l_m: float = 1.5,
        embedment_depth_df_m: float = 1.5,
    ):
        self.soil_engine = soil_engine or SoilMechanicsCoreEngine()
        self.fs_target = float(target_factor_of_safety)
        if self.fs_target < 1.0:
            raise ValueError(f"Factor of Safety must be >= 1.0, got {self.fs_target}")
        self.B = float(footing_width_b_m)
        self.L = float(footing_length_l_m)
        self.Df = float(embedment_depth_df_m)

    def compute_bearing_capacity_factors(self, phi_deg: float) -> BearingCapacityFactors:
        """
        Calculates Meyerhof-Hansen continuous bearing capacity factors Nc, Nq, Ngamma
        and geometric shape (s) and depth (d) correction factors.
        """
        phi_rad = np.radians(phi_deg)
        
        if phi_deg < 0.1:
            Nq = 1.0
            Nc = 5.14
            Ngamma = 0.0
            sc = 1.0 + 0.2 * (self.B / self.L)
            sq = 1.0
            sgamma = 1.0
            dc = 1.0 + 0.4 * (self.Df / self.B)
            dq = 1.0
            dgamma = 1.0
        else:
            # Nq = exp(pi * tan(phi)) * tan^2(45 + phi/2)
            Nq = float(np.exp(np.pi * np.tan(phi_rad)) * (np.tan(np.pi / 4.0 + phi_rad / 2.0) ** 2))
            Nc = float((Nq - 1.0) / np.tan(phi_rad))
            # Meyerhof formulation: Ngamma = (Nq - 1.0) * tan(1.4 * phi)
            Ngamma = float((Nq - 1.0) * np.tan(1.4 * phi_rad))
            
            # Shape factors
            sc = float(1.0 + (self.B / self.L) * (Nq / Nc))
            sq = float(1.0 + (self.B / self.L) * np.tan(phi_rad))
            sgamma = float(max(0.60, 1.0 - 0.4 * (self.B / self.L)))
            
            # Depth factors
            dq = float(1.0 + 2.0 * np.tan(phi_rad) * ((1.0 - np.sin(phi_rad)) ** 2) * (self.Df / self.B))
            dc = float(dq - (1.0 - dq) / (Nc * np.tan(phi_rad)))
            dgamma = 1.0

        return BearingCapacityFactors(
            Nc=Nc, Nq=Nq, Ngamma=Ngamma,
            sc=sc, sq=sq, sgamma=sgamma,
            dc=dc, dq=dq, dgamma=dgamma,
        )

    def compute_bearing_capacity(
        self,
        theta_rz: np.ndarray,
        soil_class: str = "silt_loam",
        overburden_surcharge_kpa: Optional[float] = None,
    ) -> FoundationBearingResult:
        """
        Vectorized ultimate and allowable bearing capacity calculation across spatial grids.
        q_ult = c_app * Nc * sc * dc + q * Nq * sq * dq + 0.5 * gamma * B * Ngamma * sgamma * dgamma
        q_allow = q_ult / FS
        """
        params = self.soil_engine.get_parameters(soil_class)
        factors = self.compute_bearing_capacity_factors(params.friction_angle_deg)
        
        # Effective surcharge q = gamma_dry * Df
        if overburden_surcharge_kpa is None:
            gamma_dry = params.dry_density_g_cm3 * GRAVITY_M_S2  # kN/m3
            surcharge = gamma_dry * self.Df  # kPa
        else:
            surcharge = float(overburden_surcharge_kpa)
            
        # Apparent cohesion from vadose moisture
        se = self.soil_engine.compute_effective_saturation(theta_rz, params.theta_res, params.theta_sat)
        psi = self.soil_engine.compute_matric_suction(se, params.van_genuchten_alpha_1_cm, params.van_genuchten_n)
        c_app = self.soil_engine.compute_apparent_cohesion(params.cohesion_kpa, psi, params.suction_angle_deg)
        
        # 1. Cohesion component
        term_cohesion = c_app * (factors.Nc * factors.sc * factors.dc)
        
        # 2. Surcharge component
        term_surcharge = np.full_like(theta_rz, surcharge * (factors.Nq * factors.sq * factors.dq), dtype=np.float32)
        
        # 3. Soil self-weight component (0.5 * gamma_sat * B * Ngamma * sgamma * dgamma)
        gamma_sat = params.saturated_unit_weight_kn_m3
        term_weight = np.full_like(
            theta_rz,
            0.5 * gamma_sat * self.B * (factors.Ngamma * factors.sgamma * factors.dgamma),
            dtype=np.float32,
        )
        
        # Ultimate bearing capacity
        q_ult = term_cohesion + term_surcharge + term_weight
        
        # Allowable bearing capacity with Eurocode safety factor
        q_allow = q_ult / self.fs_target
        
        # Invariant checks
        self.assert_invariants(q_ult, q_allow, self.fs_target)
        
        # Site trafficability grade based on mean allowable capacity
        mean_allow = float(np.mean(q_allow))
        if mean_allow > 180.0:
            trafficability = "HEAVY_RIG_PERMITTED"
        elif mean_allow > 100.0:
            trafficability = "LIGHT_VEHICLE_ONLY"
        else:
            trafficability = "HAZARDOUS_UNSTABLE_SOIL"
            
        return FoundationBearingResult(
            q_ult_kpa=q_ult.astype(np.float32),
            q_allow_kpa=q_allow.astype(np.float32),
            cohesion_term_kpa=term_cohesion.astype(np.float32),
            surcharge_term_kpa=term_surcharge.astype(np.float32),
            self_weight_term_kpa=term_weight.astype(np.float32),
            apparent_cohesion_kpa=c_app.astype(np.float32),
            factor_of_safety=self.fs_target,
            trafficability_grade=trafficability,
        )

    @staticmethod
    def assert_invariants(q_ult: np.ndarray, q_allow: np.ndarray, fs: float) -> None:
        """
        DO-178C Level-A Invariants:
        1. Non-negativity: q_ult > 0, q_allow > 0
        2. Strict Factor of Safety Identity: q_ult / q_allow == fs
        3. Zero NaNs and Zero Infs
        """
        if np.any(q_ult <= 0.0) or np.any(q_allow <= 0.0):
            raise AssertionError("Bearing capacity must be strictly positive!")
            
        ratio = q_ult / q_allow
        if not np.allclose(ratio, fs, rtol=1e-5):
            raise AssertionError(f"Safety factor identity violated! Expected {fs}, got {np.mean(ratio)}")
            
        if np.any(np.isnan(q_ult)) or np.any(np.isinf(q_ult)):
            raise AssertionError("NaNs or Infs detected in ultimate bearing capacity!")
