# THE MRIDANSH - Agriculture Domain Translator
# Module: 4_domain_translators/agronomy/soil_water_reservoir.py
# Standard: United Nations FAO-56 & USDA Soil Hydraulic Pedotransfer Mechanics
# DO-178C Level-A Avionics & Remote Sensing Rigor

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger("MRIDANSH.AgriTranslator.SoilReservoir")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@dataclass(frozen=True)
class SoilHydraulicProperties:
    """
    Physical soil hydraulic boundary constants for a specific texture.
    Units: Volumetric fraction (m3/m3).
    """
    texture_name: str
    theta_sat: float  # Saturation moisture / porosity (0 kPa)
    theta_fc: float   # Field capacity (-33 kPa matric suction)
    theta_wp: float   # Permanent wilting point (-1500 kPa matric suction)
    theta_res: float  # Residual moisture content

    def __post_init__(self):
        if not (0.0 <= self.theta_res <= self.theta_wp < self.theta_fc < self.theta_sat <= 1.0):
            raise ValueError(
                f"Violated physical hydraulic boundary ordering for {self.texture_name}: "
                f"res={self.theta_res}, wp={self.theta_wp}, fc={self.theta_fc}, sat={self.theta_sat}"
            )


# USDA Standard 12 Texture Classes (USDA-NRCS & FAO-56 Standard Calibrated Parameters)
USDA_TEXTURE_PROPERTIES: Dict[str, SoilHydraulicProperties] = {
    "sand": SoilHydraulicProperties("sand", theta_sat=0.43, theta_fc=0.10, theta_wp=0.05, theta_res=0.02),
    "loamy_sand": SoilHydraulicProperties("loamy_sand", theta_sat=0.41, theta_fc=0.12, theta_wp=0.05, theta_res=0.03),
    "sandy_loam": SoilHydraulicProperties("sandy_loam", theta_sat=0.41, theta_fc=0.18, theta_wp=0.08, theta_res=0.04),
    "loam": SoilHydraulicProperties("loam", theta_sat=0.43, theta_fc=0.27, theta_wp=0.12, theta_res=0.05),
    "silt_loam": SoilHydraulicProperties("silt_loam", theta_sat=0.45, theta_fc=0.33, theta_wp=0.13, theta_res=0.04),
    "silt": SoilHydraulicProperties("silt", theta_sat=0.46, theta_fc=0.30, theta_wp=0.09, theta_res=0.03),
    "sandy_clay_loam": SoilHydraulicProperties("sandy_clay_loam", theta_sat=0.39, theta_fc=0.27, theta_wp=0.17, theta_res=0.07),
    "clay_loam": SoilHydraulicProperties("clay_loam", theta_sat=0.41, theta_fc=0.32, theta_wp=0.20, theta_res=0.08),
    "silty_clay_loam": SoilHydraulicProperties("silty_clay_loam", theta_sat=0.43, theta_fc=0.37, theta_wp=0.21, theta_res=0.07),
    "sandy_clay": SoilHydraulicProperties("sandy_clay", theta_sat=0.38, theta_fc=0.32, theta_wp=0.24, theta_res=0.10),
    "silty_clay": SoilHydraulicProperties("silty_clay", theta_sat=0.41, theta_fc=0.39, theta_wp=0.25, theta_res=0.07),
    "clay": SoilHydraulicProperties("clay", theta_sat=0.43, theta_fc=0.40, theta_wp=0.27, theta_res=0.10),
}


@dataclass
class AvailableWaterReservoir:
    """
    Vectorized representation of the root-zone soil water reservoir.
    Units:
      taw_mm: Total Available Water (mm)
      raw_mm: Readily Available Water before water stress onset (mm)
      theta_fc: Field Capacity array (m3/m3)
      theta_wp: Wilting Point array (m3/m3)
      z_r_m: Rooting depth used in calculation (m)
      p_fraction: Soil water depletion fraction (dimensionless)
    """
    taw_mm: Union[float, np.ndarray]
    raw_mm: Union[float, np.ndarray]
    theta_fc: Union[float, np.ndarray]
    theta_wp: Union[float, np.ndarray]
    z_r_m: Union[float, np.ndarray]
    p_fraction: Union[float, np.ndarray]


class SoilWaterReservoirEngine:
    """
    High-Precision Soil Water Reservoir Engine complying with FAO-56 Irrigation
    Guidelines and USDA Soil Conservation Service mechanics.
    """

    def __init__(self, crop_taxonomy_path: Optional[Union[str, Path]] = None):
        if crop_taxonomy_path is None:
            crop_taxonomy_path = Path(__file__).parent / "crop_taxonomy.json"
        
        self.crop_taxonomy_path = Path(crop_taxonomy_path)
        self.crop_catalog = self._load_crop_taxonomy()

    def _load_crop_taxonomy(self) -> Dict[str, dict]:
        """Loads and verifies the FAO-56 crop database."""
        if not self.crop_taxonomy_path.exists():
            logger.warning(
                "Crop taxonomy file %s not found. Initializing with default fallback crops.",
                self.crop_taxonomy_path
            )
            return {
                "default_generic_crop": {
                    "p_depletion_fraction": 0.50,
                    "rooting_depth_min_m": 0.15,
                    "rooting_depth_max_m": 1.00,
                }
            }

        with open(self.crop_taxonomy_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        crops = data.get("crops", {})
        logger.info("Loaded %d certified FAO-56 crops from taxonomy.", len(crops))
        return crops

    def get_crop_parameters(self, crop_name: str) -> dict:
        """Retrieves parameters for a given crop name, with case-insensitive matching."""
        key = crop_name.strip().lower()
        if key in self.crop_catalog:
            return self.crop_catalog[key]
        
        # Partial match lookup
        for k, v in self.crop_catalog.items():
            if key in k or key in v.get("common_name", "").lower():
                return v

        logger.warning(
            "Crop '%s' not recognized in taxonomy. Falling back to 'default_generic_crop'.",
            crop_name
        )
        return self.crop_catalog.get("default_generic_crop", {
            "p_depletion_fraction": 0.50,
            "rooting_depth_min_m": 0.15,
            "rooting_depth_max_m": 1.00,
        })

    @staticmethod
    def get_texture_properties(texture_name: str) -> SoilHydraulicProperties:
        """Retrieves calibrated USDA hydraulic properties by texture name."""
        key = texture_name.strip().lower().replace(" ", "_")
        if key in USDA_TEXTURE_PROPERTIES:
            return USDA_TEXTURE_PROPERTIES[key]
        
        logger.warning(
            "Texture '%s' not found in standard USDA classes. Falling back to reference 'loam'.",
            texture_name
        )
        return USDA_TEXTURE_PROPERTIES["loam"]

    @staticmethod
    def saxton_rawls_pedotransfer(
        sand_fraction: Union[float, np.ndarray],
        clay_fraction: Union[float, np.ndarray],
        organic_matter_fraction: Union[float, np.ndarray] = 0.015,
    ) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray], Union[float, np.ndarray]]:
        """
        Calculates continuous Field Capacity (theta_fc), Wilting Point (theta_wp),
        and Saturation (theta_sat) using the empirical Saxton & Rawls (2006) equations.

        Parameters:
            sand_fraction: Mass fraction of sand (0.0 to 1.0)
            clay_fraction: Mass fraction of clay (0.0 to 1.0)
            organic_matter_fraction: Organic matter fraction (default: 0.015 = 1.5%)

        Returns:
            (theta_fc, theta_wp, theta_sat) in m3/m3
        """
        S = np.asarray(sand_fraction, dtype=np.float32)
        C = np.asarray(clay_fraction, dtype=np.float32)
        OM = np.asarray(organic_matter_fraction, dtype=np.float32)

        # 1. Permanent Wilting Point (1500 kPa suction)
        theta_1500t = (
            -0.024 * S
            + 0.487 * C
            + 0.006 * OM
            + 0.005 * (S * OM)
            - 0.013 * (C * OM)
            + 0.068 * (S * C)
            + 0.031
        )
        theta_wp = theta_1500t + (0.14 * theta_1500t - 0.02)

        # 2. Field Capacity (33 kPa suction)
        theta_33t = (
            -0.251 * S
            + 0.195 * C
            + 0.011 * OM
            + 0.006 * (S * OM)
            - 0.027 * (C * OM)
            + 0.452 * (S * C)
            + 0.299
        )
        theta_fc = theta_33t + (1.283 * (theta_33t**2) - 0.374 * theta_33t - 0.015)

        # 3. Saturation (0 kPa suction)
        theta_s33t = (
            0.278 * S
            + 0.034 * C
            + 0.022 * OM
            - 0.018 * (S * OM)
            - 0.027 * (C * OM)
            - 0.584 * (S * C)
            + 0.078
        )
        theta_s33 = theta_s33t + (0.636 * theta_s33t - 0.107)
        theta_sat = theta_fc + theta_s33 - 0.097 * S + 0.043

        # Strict physical boundaries enforcement
        theta_wp = np.clip(theta_wp, 0.03, 0.35)
        theta_fc = np.clip(theta_fc, theta_wp + 0.03, 0.48)
        theta_sat = np.clip(theta_sat, theta_fc + 0.03, 0.55)

        if np.isscalar(sand_fraction):
            return float(theta_fc), float(theta_wp), float(theta_sat)

        return theta_fc, theta_wp, theta_sat

    def compute_available_water(
        self,
        theta_fc: Union[float, np.ndarray],
        theta_wp: Union[float, np.ndarray],
        z_r_m: Union[float, np.ndarray],
        crop_type_or_p: Union[str, float] = "wheat",
    ) -> AvailableWaterReservoir:
        """
        Evaluates the Total Available Water (TAW) and Readily Available Water (RAW)
        following the FAO-56 dual crop water balance methodology.

        Formulations:
            TAW = 1000 * (theta_fc - theta_wp) * z_r_m   [mm]
            RAW = p_fraction * TAW                       [mm]

        Parameters:
            theta_fc: Field Capacity (m3/m3)
            theta_wp: Permanent Wilting Point (m3/m3)
            z_r_m: Effective rooting depth in meters (m)
            crop_type_or_p: Crop identifier from taxonomy, or explicit depletion fraction p (0 < p <= 1)

        Returns:
            AvailableWaterReservoir containing TAW (mm) and RAW (mm)
        """
        # Resolve soil water depletion fraction p
        if isinstance(crop_type_or_p, (int, float)):
            p_val = float(crop_type_or_p)
            if not (0.05 <= p_val <= 0.95):
                raise ValueError(f"Depletion fraction p={p_val} outside physical bounds [0.05, 0.95]")
        else:
            crop_params = self.get_crop_parameters(str(crop_type_or_p))
            p_val = float(crop_params.get("p_depletion_fraction", 0.50))

        # Vectorized array casting
        fc = np.asarray(theta_fc, dtype=np.float32)
        wp = np.asarray(theta_wp, dtype=np.float32)
        zr = np.asarray(z_r_m, dtype=np.float32)

        # Integrity check: Ensure field capacity strictly exceeds wilting point
        if np.any(fc <= wp):
            logger.warning(
                "Detected non-physical moisture thresholds where theta_fc <= theta_wp. Enforcing minimum 0.02 margin."
            )
            fc = np.maximum(fc, wp + 0.02)

        # Root depth sanity check: non-negative and non-zero
        zr = np.clip(zr, 0.05, 3.0)

        # Total Available Water (TAW) in mm
        # Formula: 1000 * (theta_fc - theta_wp) * z_r
        taw_mm = 1000.0 * (fc - wp) * zr
        taw_mm = np.maximum(taw_mm, 0.0)

        # Readily Available Water (RAW) in mm
        # Formula: p * TAW
        raw_mm = p_val * taw_mm
        raw_mm = np.maximum(raw_mm, 0.0)

        # DO-178C Level-A Assertions: Zero NaNs, Zero Infs
        if np.any(np.isnan(taw_mm)) or np.any(np.isinf(taw_mm)):
            raise AssertionError("DO-178C Violation: NaN or Inf encountered in TAW calculation")
        if np.any(np.isnan(raw_mm)) or np.any(np.isinf(raw_mm)):
            raise AssertionError("DO-178C Violation: NaN or Inf encountered in RAW calculation")
        if np.any(raw_mm > taw_mm):
            raise AssertionError("Physics Violation: Readily Available Water (RAW) exceeds Total Available Water (TAW)")

        # Return scalar if inputs were scalars
        if np.isscalar(theta_fc) and np.isscalar(theta_wp) and np.isscalar(z_r_m):
            return AvailableWaterReservoir(
                taw_mm=float(taw_mm),
                raw_mm=float(raw_mm),
                theta_fc=float(fc),
                theta_wp=float(wp),
                z_r_m=float(zr),
                p_fraction=p_val,
            )

        return AvailableWaterReservoir(
            taw_mm=taw_mm,
            raw_mm=raw_mm,
            theta_fc=fc,
            theta_wp=wp,
            z_r_m=zr,
            p_fraction=p_val,
        )

    def generate_spatial_reservoir_map(
        self,
        grid_shape: Tuple[int, int],
        dominant_texture: str = "clay_loam",
        dominant_crop: str = "rice_paddy",
        root_depth_m: float = 0.40,
    ) -> AvailableWaterReservoir:
        """
        Creates a full 2D spatial raster grid of TAW and RAW for satellite tile orchestration.
        """
        H, W = grid_shape
        tex_prop = self.get_texture_properties(dominant_texture)
        
        fc_grid = np.full((H, W), tex_prop.theta_fc, dtype=np.float32)
        wp_grid = np.full((H, W), tex_prop.theta_wp, dtype=np.float32)
        zr_grid = np.full((H, W), root_depth_m, dtype=np.float32)

        return self.compute_available_water(
            theta_fc=fc_grid,
            theta_wp=wp_grid,
            z_r_m=zr_grid,
            crop_type_or_p=dominant_crop,
        )
