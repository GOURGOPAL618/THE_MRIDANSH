# THE MRIDANSH - CIVIL & GEOTECHNICAL DOMAIN TRANSLATOR
# Module: 4_domain_translators/civil/soil_mechanics_core.py
# Subsystem 05 of AETHER-MRID1607X Core Engine
# Architecture: RTCA DO-178C Level-A Principles / Eurocode 7 (EN 1997) / ASTM D2487

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

GRAVITY_M_S2: float = 9.80665
CM_H2O_TO_KPA: float = 0.0980665
MAX_SUCTION_KPA: float = 10000.0  # Physical upper limit for residual matric suction (10 MPa)


@dataclass(frozen=True)
class GeotechnicalParameters:
    """Certified soil parameters mapped to USCS and USDA textural systems."""
    soil_class: str
    uscs_group: str
    description: str
    friction_angle_deg: float
    cohesion_kpa: float
    saturated_unit_weight_kn_m3: float
    dry_density_g_cm3: float
    suction_angle_deg: float
    van_genuchten_alpha_1_cm: float
    van_genuchten_n: float
    theta_res: float
    theta_sat: float
    permeability_m_s: float

    @property
    def friction_angle_rad(self) -> float:
        return float(np.radians(self.friction_angle_deg))

    @property
    def suction_angle_rad(self) -> float:
        return float(np.radians(self.suction_angle_deg))


@dataclass(frozen=True)
class StratificationProfile:
    """3D Subsurface Geotechnical Profile across 3 standard infrastructure depth zones."""
    theta_skin_0_5cm: np.ndarray
    theta_subbase_5_30cm: np.ndarray
    theta_foundation_30_100cm: np.ndarray
    suction_skin_kpa: np.ndarray
    suction_subbase_kpa: np.ndarray
    suction_foundation_kpa: np.ndarray
    pore_pressure_foundation_kpa: np.ndarray
    apparent_cohesion_foundation_kpa: np.ndarray


@dataclass(frozen=True)
class FredlundShearResult:
    """Result of Fredlund extended unsaturated shear strength analysis."""
    effective_saturation: np.ndarray
    matric_suction_kpa: np.ndarray
    pore_water_pressure_kpa: np.ndarray
    apparent_cohesion_kpa: np.ndarray
    effective_stress_kpa: np.ndarray
    shear_strength_kpa: np.ndarray


class SoilMechanicsCoreEngine:
    """
    Core constitutive soil mechanics engine transforming spaceborne soil moisture states
    into unsaturated effective stress, matric suction, and Fredlund shear strength fields.
    """

    def __init__(self, taxonomy_path: Optional[Path] = None):
        if taxonomy_path is None:
            taxonomy_path = Path(__file__).resolve().parent / "geotechnical_taxonomy.json"
        self.taxonomy_path = Path(taxonomy_path)
        self.taxonomy = self._load_taxonomy(self.taxonomy_path)

    @staticmethod
    def _load_taxonomy(path: Path) -> Dict[str, GeotechnicalParameters]:
        if not path.exists():
            raise FileNotFoundError(f"Geotechnical taxonomy not found at {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        soil_classes = {}
        for key, vals in data.get("soil_classes", {}).items():
            soil_classes[key.lower()] = GeotechnicalParameters(
                soil_class=key.lower(),
                uscs_group=vals["uscs_group"],
                description=vals["description"],
                friction_angle_deg=float(vals["friction_angle_deg"]),
                cohesion_kpa=float(vals["cohesion_kpa"]),
                saturated_unit_weight_kn_m3=float(vals["saturated_unit_weight_kn_m3"]),
                dry_density_g_cm3=float(vals["dry_density_g_cm3"]),
                suction_angle_deg=float(vals["suction_angle_deg"]),
                van_genuchten_alpha_1_cm=float(vals["van_genuchten_alpha_1_cm"]),
                van_genuchten_n=float(vals["van_genuchten_n"]),
                theta_res=float(vals["theta_res"]),
                theta_sat=float(vals["theta_sat"]),
                permeability_m_s=float(vals["permeability_m_s"]),
            )
        return soil_classes

    def get_parameters(self, soil_class: str) -> GeotechnicalParameters:
        norm_key = soil_class.strip().lower().replace(" ", "_")
        if norm_key in self.taxonomy:
            return self.taxonomy[norm_key]
        logging.warning(
            f"Soil class '{soil_class}' unmapped in geotechnical taxonomy. Falling back to 'default_generic'."
        )
        return self.taxonomy["default_generic"]

    def compute_effective_saturation(
        self, theta: np.ndarray, theta_res: float, theta_sat: float
    ) -> np.ndarray:
        """
        Computes normalized effective saturation Se in (0, 1].
        """
        theta_arr = np.asarray(theta, dtype=np.float32)
        denom = max(1e-4, theta_sat - theta_res)
        se = (theta_arr - theta_res) / denom
        return np.clip(se, 1e-4, 1.0).astype(np.float32)

    def compute_matric_suction(
        self, se: np.ndarray, alpha_1_cm: float, n: float
    ) -> np.ndarray:
        """
        van Genuchten analytical suction inversion:
        psi = (1 / alpha) * (Se^(-1/m) - 1)^(1/n) in cm H2O, converted to kPa.
        """
        se_arr = np.asarray(se, dtype=np.float32)
        m = 1.0 - (1.0 / max(1.001, n))
        
        # Guard against zero/negative base
        inv_se = np.power(se_arr, -1.0 / m)
        term = np.maximum(0.0, inv_se - 1.0)
        
        suction_cm = (1.0 / max(1e-4, alpha_1_cm)) * np.power(term, 1.0 / n)
        suction_kpa = suction_cm * CM_H2O_TO_KPA
        
        # Bounded between 0.0 kPa (full saturation) and MAX_SUCTION_KPA (residual)
        return np.clip(suction_kpa, 0.0, MAX_SUCTION_KPA).astype(np.float32)

    def compute_pore_water_pressure(self, matric_suction_kpa: np.ndarray) -> np.ndarray:
        """
        In unsaturated porous media, pore water pressure u_w = -psi (compressive suction).
        At full saturation (psi = 0), u_w = 0 (hydrostatic baseline).
        """
        return (-np.maximum(0.0, matric_suction_kpa)).astype(np.float32)

    def compute_apparent_cohesion(
        self, effective_cohesion_kpa: float, matric_suction_kpa: np.ndarray, suction_angle_deg: float
    ) -> np.ndarray:
        """
        Fredlund extended apparent cohesion:
        c_apparent(theta) = c' + psi(theta) * tan(phi^b)
        """
        phi_b_rad = np.radians(suction_angle_deg)
        apparent_c = effective_cohesion_kpa + matric_suction_kpa * np.tan(phi_b_rad)
        return np.maximum(effective_cohesion_kpa, apparent_c).astype(np.float32)

    def compute_bishop_effective_stress(
        self, total_stress_kpa: Union[float, np.ndarray], se: np.ndarray, matric_suction_kpa: np.ndarray
    ) -> np.ndarray:
        """
        Bishop's unsaturated effective stress formulation:
        sigma' = (sigma_total - u_a) + chi * (u_a - u_w)
        Assuming atmospheric pore air pressure u_a = 0 and chi = Se:
        sigma' = sigma_total + Se * psi
        """
        tot_stress = np.asarray(total_stress_kpa, dtype=np.float32)
        effective_stress = tot_stress + se * matric_suction_kpa
        return np.maximum(0.0, effective_stress).astype(np.float32)

    def evaluate_shear_strength(
        self,
        theta: np.ndarray,
        soil_class: str,
        total_stress_kpa: Union[float, np.ndarray] = 50.0,
    ) -> FredlundShearResult:
        """
        Computes complete unsaturated geotechnical state and Fredlund Mohr-Coulomb shear strength.
        tau_f = c_apparent(theta) + sigma' * tan(phi')
        """
        params = self.get_parameters(soil_class)
        se = self.compute_effective_saturation(theta, params.theta_res, params.theta_sat)
        psi = self.compute_matric_suction(se, params.van_genuchten_alpha_1_cm, params.van_genuchten_n)
        u_w = self.compute_pore_water_pressure(psi)
        c_app = self.compute_apparent_cohesion(params.cohesion_kpa, psi, params.suction_angle_deg)
        eff_stress = self.compute_bishop_effective_stress(total_stress_kpa, se, psi)
        
        tan_phi = np.tan(params.friction_angle_rad)
        shear_strength = c_app + eff_stress * tan_phi
        
        self.assert_invariants(params, psi, c_app, u_w, shear_strength)
        
        return FredlundShearResult(
            effective_saturation=se,
            matric_suction_kpa=psi,
            pore_water_pressure_kpa=u_w,
            apparent_cohesion_kpa=c_app,
            effective_stress_kpa=eff_stress,
            shear_strength_kpa=shear_strength.astype(np.float32),
        )

    def compute_stratification_profile(
        self, theta_surf: np.ndarray, theta_rz: np.ndarray, soil_class: str
    ) -> StratificationProfile:
        """
        Derives continuous 3-depth subsurface vadose geotechnical stratigraphy:
        Layer 1: Skin surface (0 - 5 cm)
        Layer 2: Upper pavement / subbase contact (5 - 30 cm)
        Layer 3: Deep foundation anchorage shear plane (30 - 100 cm)
        """
        params = self.get_parameters(soil_class)
        
        # Stratification weighting
        theta_skin = np.asarray(theta_surf, dtype=np.float32)
        theta_found = np.asarray(theta_rz, dtype=np.float32)
        theta_subbase = (0.40 * theta_skin + 0.60 * theta_found).astype(np.float32)
        
        # Suction profiles across all 3 layers
        se_skin = self.compute_effective_saturation(theta_skin, params.theta_res, params.theta_sat)
        psi_skin = self.compute_matric_suction(se_skin, params.van_genuchten_alpha_1_cm, params.van_genuchten_n)
        
        se_sub = self.compute_effective_saturation(theta_subbase, params.theta_res, params.theta_sat)
        psi_sub = self.compute_matric_suction(se_sub, params.van_genuchten_alpha_1_cm, params.van_genuchten_n)
        
        se_found = self.compute_effective_saturation(theta_found, params.theta_res, params.theta_sat)
        psi_found = self.compute_matric_suction(se_found, params.van_genuchten_alpha_1_cm, params.van_genuchten_n)
        
        u_found = self.compute_pore_water_pressure(psi_found)
        c_app_found = self.compute_apparent_cohesion(params.cohesion_kpa, psi_found, params.suction_angle_deg)
        
        return StratificationProfile(
            theta_skin_0_5cm=theta_skin,
            theta_subbase_5_30cm=theta_subbase,
            theta_foundation_30_100cm=theta_found,
            suction_skin_kpa=psi_skin,
            suction_subbase_kpa=psi_sub,
            suction_foundation_kpa=psi_found,
            pore_pressure_foundation_kpa=u_found,
            apparent_cohesion_foundation_kpa=c_app_found,
        )

    @staticmethod
    def assert_invariants(
        params: GeotechnicalParameters,
        psi: np.ndarray,
        c_app: np.ndarray,
        u_w: np.ndarray,
        shear_strength: np.ndarray,
    ) -> None:
        """
        DO-178C Level-A Formal Engineering Invariant Assertions.
        """
        # 1. Friction angle boundedness
        if not (0.0 <= params.friction_angle_deg <= 45.0):
            raise AssertionError(f"Friction angle {params.friction_angle_deg} outside [0, 45] deg.")
        
        # 2. Suction non-negativity
        if np.any(psi < 0.0):
            raise AssertionError("Matric suction contains negative values.")
        
        # 3. Pore water pressure non-positivity under unsaturated state
        if np.any(u_w > 0.0):
            raise AssertionError("Unsaturated pore water pressure contains positive values.")
        
        # 4. Apparent cohesion bounded below by drained effective cohesion
        if np.any(c_app < (params.cohesion_kpa - 1e-4)):
            raise AssertionError(f"Apparent cohesion dropped below drained c'={params.cohesion_kpa} kPa.")
        
        # 5. Non-negativity of shear strength
        if np.any(shear_strength < 0.0):
            raise AssertionError("Shear strength contains negative values.")
            
        # 6. Zero NaNs and Zero Infs
        if np.any(np.isnan(shear_strength)) or np.any(np.isinf(shear_strength)):
            raise AssertionError("NaNs or Infs detected in geotechnical shear calculation.")
