# THE MRIDANSH - Agriculture Domain Translator
# Module: 4_domain_translators/agronomy/dynamic_phenology.py
# Standard: United Nations FAO-56 & Remote Sensing Optical Canopy Mechanics
# DO-178C Level-A Avionics & Remote Sensing Rigor

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger("MRIDANSH.AgriTranslator.Phenology")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@dataclass
class PhenologyState:
    """
    Continuous pixel-level vegetation canopy and phenological state.
    
    Fields:
      ndvi: Normalized Difference Vegetation Index [-1.0, 1.0]
      fractional_cover: Fractional canopy ground cover fc [0.0, 1.0]
      z_r_m: Dynamic effective rooting depth (meters)
      kcb: Basal crop transpiration coefficient (dimensionless)
    """
    ndvi: Union[float, np.ndarray]
    fractional_cover: Union[float, np.ndarray]
    z_r_m: Union[float, np.ndarray]
    kcb: Union[float, np.ndarray]


class DynamicPhenologyEngine:
    """
    Extracts dynamic vegetation phenology, fractional ground cover,
    dynamic sigmoidal root deepening, and basal crop coefficient (Kcb)
    from optical reflectance and FAO-56 species databases.
    """

    def __init__(
        self,
        ndvi_bare_soil: float = 0.15,
        ndvi_full_canopy: float = 0.80,
    ):
        """
        Parameters:
            ndvi_bare_soil: Threshold NDVI corresponding to dry bare soil (FAO-56 default: 0.15)
            ndvi_full_canopy: Threshold NDVI corresponding to dense 100% ground cover (default: 0.80)
        """
        if not (0.0 <= ndvi_bare_soil < ndvi_full_canopy <= 1.0):
            raise ValueError(
                f"Invalid NDVI calibration thresholds: bare={ndvi_bare_soil}, full={ndvi_full_canopy}"
            )
        self.ndvi_bare = float(ndvi_bare_soil)
        self.ndvi_full = float(ndvi_full_canopy)

    def compute_ndvi_from_reflectance(
        self,
        optical_bands: np.ndarray,
        red_channel_idx: int = 2,
        nir_channel_idx: int = 3,
        epsilon: float = 1e-6,
    ) -> np.ndarray:
        """
        Derives NDVI from multi-spectral BOA surface reflectance.
        Expected optical_bands shape: [C, H, W] or [B, C, H, W], where C >= 4
        Standard Sentinel-2 BOA layout: Band 0=Blue, 1=Green, 2=Red, 3=NIR.
        """
        arr = np.asarray(optical_bands, dtype=np.float32)
        if arr.ndim == 3:
            red = arr[red_channel_idx]
            nir = arr[nir_channel_idx]
        elif arr.ndim == 4:
            red = arr[:, red_channel_idx]
            nir = arr[:, nir_channel_idx]
        else:
            raise ValueError(f"Expected 3D or 4D optical array, got shape {arr.shape}")

        denom = nir + red + epsilon
        ndvi = (nir - red) / denom
        
        # Physical boundary clamp
        ndvi = np.clip(ndvi, -1.0, 1.0)
        
        if np.any(np.isnan(ndvi)) or np.any(np.isinf(ndvi)):
            raise AssertionError("DO-178C Violation: NaN or Inf encountered in NDVI derivation")

        return ndvi

    def compute_fractional_cover(
        self,
        ndvi: Union[float, np.ndarray],
    ) -> Union[float, np.ndarray]:
        """
        Calculates Fractional Vegetation Cover (fc) using Gutman & Ignatov (1998)
        and FAO-56 Eq. 76:
            fc = clip( (NDVI - NDVI_bare) / (NDVI_full - NDVI_bare), 0.0, 1.0 )
        """
        ndvi_arr = np.asarray(ndvi, dtype=np.float32)
        fc = (ndvi_arr - self.ndvi_bare) / (self.ndvi_full - self.ndvi_bare)
        fc = np.clip(fc, 0.0, 1.0)

        if np.isscalar(ndvi):
            return float(fc)
        return fc

    def compute_dynamic_root_depth(
        self,
        fractional_cover: Union[float, np.ndarray],
        zr_min_m: float = 0.15,
        zr_max_m: float = 1.00,
        growth_curvature: float = 1.2,
    ) -> Union[float, np.ndarray]:
        """
        Models biological root elongation as a function of canopy phenology.
        Roots deepen progressively as above-ground biomass expands:
            Zr(fc) = zr_min + (zr_max - zr_min) * (fc ** growth_curvature)

        Guarantees strict monotonic bounds: [zr_min, zr_max].
        """
        if zr_min_m <= 0.0 or zr_max_m <= zr_min_m:
            raise ValueError(f"Invalid root bounds: min={zr_min_m}, max={zr_max_m}")

        fc = np.asarray(fractional_cover, dtype=np.float32)
        # Power expansion curve captures non-linear root development
        expansion = np.power(fc, growth_curvature)
        zr = zr_min_m + (zr_max_m - zr_min_m) * expansion
        zr = np.clip(zr, zr_min_m, zr_max_m)

        if np.isscalar(fractional_cover):
            return float(zr)
        return zr

    def compute_basal_crop_coefficient(
        self,
        fractional_cover: Union[float, np.ndarray],
        kcb_ini: float = 0.15,
        kcb_mid: float = 1.15,
        kcb_end: Optional[float] = None,
    ) -> Union[float, np.ndarray]:
        """
        Calculates basal crop coefficient (Kcb) according to FAO-56 dual crop coefficient approach:
            Kcb = kcb_ini + (kcb_mid - kcb_ini) * fc
        """
        fc = np.asarray(fractional_cover, dtype=np.float32)
        kcb = kcb_ini + (kcb_mid - kcb_ini) * fc
        kcb = np.clip(kcb, min(kcb_ini, 0.10), max(kcb_mid, 1.35))

        if np.isscalar(fractional_cover):
            return float(kcb)
        return kcb

    def evaluate_phenology(
        self,
        optical_reflectance_or_ndvi: Union[float, np.ndarray],
        crop_params: dict,
    ) -> PhenologyState:
        """
        One-stop evaluator: Transforms optical input into comprehensive PhenologyState.
        """
        inp = np.asarray(optical_reflectance_or_ndvi, dtype=np.float32)
        
        # If input has multi-channel reflectance, compute NDVI
        if inp.ndim >= 3:
            ndvi = self.compute_ndvi_from_reflectance(inp)
        else:
            ndvi = np.clip(inp, -1.0, 1.0)

        # 1. Fractional canopy cover fc
        fc = self.compute_fractional_cover(ndvi)

        # 2. Extract crop physiological thresholds
        zr_min = float(crop_params.get("rooting_depth_min_m", 0.15))
        zr_max = float(crop_params.get("rooting_depth_max_m", 1.00))
        kcb_ini = float(crop_params.get("kcb_initial", 0.15))
        kcb_mid = float(crop_params.get("kcb_mid", 1.15))

        # 3. Dynamic root depth
        zr_m = self.compute_dynamic_root_depth(fc, zr_min_m=zr_min, zr_max_m=zr_max)

        # 4. Basal crop coefficient
        kcb = self.compute_basal_crop_coefficient(fc, kcb_ini=kcb_ini, kcb_mid=kcb_mid)

        return PhenologyState(
            ndvi=ndvi,
            fractional_cover=fc,
            z_r_m=zr_m,
            kcb=kcb,
        )
