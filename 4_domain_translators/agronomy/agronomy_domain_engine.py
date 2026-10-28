# THE MRIDANSH - Agriculture Domain Translator
# Module: 4_domain_translators/agronomy/agronomy_domain_engine.py
# Unified Monolithic Agronomic Downstream Intelligence Engine
# Standards: United Nations FAO-56 & DO-178C Level-A Avionics Rigor

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np

try:
    from .soil_water_reservoir import SoilWaterReservoirEngine, AvailableWaterReservoir
    from .dynamic_phenology import DynamicPhenologyEngine, PhenologyState
    from .fao56_dual_kc import FAO56DualKcEngine, DualKcOutput
    from .crop_water_stress import CropWaterStressEngine, WaterStressOutput
except (ImportError, ValueError):
    from soil_water_reservoir import SoilWaterReservoirEngine, AvailableWaterReservoir
    from dynamic_phenology import DynamicPhenologyEngine, PhenologyState
    from fao56_dual_kc import FAO56DualKcEngine, DualKcOutput
    from crop_water_stress import CropWaterStressEngine, WaterStressOutput

logger = logging.getLogger("MRIDANSH.AgriTranslator.DomainEngine")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@dataclass
class AgronomicStateVector:
    """
    Unified spaceborne agronomic state output packet.
    All spatial arrays share identical spatial resolution (e.g. 10m UTM).
    """
    ndvi: np.ndarray
    fractional_cover: np.ndarray
    root_depth_m: np.ndarray
    taw_mm: np.ndarray
    raw_mm: np.ndarray
    kcb: np.ndarray
    ke: np.ndarray
    kc_potential: np.ndarray
    root_depletion_dr_mm: np.ndarray
    water_stress_ks: np.ndarray
    cwsi: np.ndarray
    etc_actual_mm_day: np.ndarray
    transpiration_deficit_mm_day: np.ndarray
    execution_time_ms: float
    latency_ms_per_pixel: float
    provenance: Dict[str, Any]


class AgronomyDomainEngine:
    """
    Production-grade Monolithic Agronomy Translator.
    Transforms multi-modal satellite observations and AETHER soil state outputs
    into certified United Nations FAO-56 crop water balance intelligence.
    """

    def __init__(
        self,
        crop_taxonomy_path: Optional[Union[str, Path]] = None,
        default_et0_mm_day: float = 4.80,
    ):
        self.reservoir_engine = SoilWaterReservoirEngine(crop_taxonomy_path=crop_taxonomy_path)
        self.pheno_engine = DynamicPhenologyEngine(ndvi_bare_soil=0.15, ndvi_full_canopy=0.80)
        self.dual_kc_engine = FAO56DualKcEngine(default_et0_mm_day=default_et0_mm_day)
        self.stress_engine = CropWaterStressEngine()
        self.default_et0 = float(default_et0_mm_day)

    def forward(
        self,
        optical_reflectance_or_ndvi: np.ndarray,
        theta_surf: np.ndarray,
        theta_rz: np.ndarray,
        soil_texture: str = "clay_loam",
        crop_name: str = "wheat",
        et0_mm_day: Optional[Union[float, np.ndarray]] = None,
    ) -> AgronomicStateVector:
        """
        Executes end-to-end forward agronomic translation across a 2D spatial raster grid.

        Parameters:
            optical_reflectance_or_ndvi: [C, H, W] Sentinel-2 BOA reflectance or [H, W] NDVI
            theta_surf: [H, W] Surface volumetric soil moisture (0-5 cm) from AETHER Band 1
            theta_rz: [H, W] Root-zone volumetric soil moisture (5-30 cm) from AETHER Band 2
            soil_texture: Soil texture class name from USDA 12 catalog
            crop_name: Crop species identifier from FAO-56 taxonomy
            et0_mm_day: Daily reference evapotranspiration (mm/day)

        Returns:
            AgronomicStateVector with fully decomposed crop water balance
        """
        t0 = time.perf_counter()

        # 1. Clean and shape spatial arrays
        ts = np.squeeze(np.asarray(theta_surf, dtype=np.float32))
        trz = np.squeeze(np.asarray(theta_rz, dtype=np.float32))
        if ts.ndim != 2 or trz.ndim != 2:
            raise ValueError(f"Expected 2D spatial grids for moisture, got ts={ts.shape}, trz={trz.shape}")

        H, W = ts.shape

        # 2. Extract Soil Hydraulic Boundary Thresholds
        tex_props = self.reservoir_engine.get_texture_properties(soil_texture)
        theta_fc = tex_props.theta_fc
        theta_wp = tex_props.theta_wp
        theta_res = tex_props.theta_res

        # 3. Dynamic Optical Phenology & Root Elongation
        crop_params = self.reservoir_engine.get_crop_parameters(crop_name)
        pheno = self.pheno_engine.evaluate_phenology(
            optical_reflectance_or_ndvi=optical_reflectance_or_ndvi,
            crop_params=crop_params,
        )

        # 4. Available Water Capacity Reservoir (TAW & RAW)
        p_depletion = float(crop_params.get("p_depletion_fraction", 0.50))
        reservoir = self.reservoir_engine.compute_available_water(
            theta_fc=theta_fc,
            theta_wp=theta_wp,
            z_r_m=pheno.z_r_m,
            crop_type_or_p=p_depletion,
        )

        # 5. FAO-56 Dual Kc Partitioning (Kcb + Ke)
        dual_kc = self.dual_kc_engine.compute_dual_coefficients(
            kcb=pheno.kcb,
            fractional_cover=pheno.fractional_cover,
            theta_surf=ts,
            theta_fc=theta_fc,
            theta_res=theta_res,
            et0_mm_day=et0_mm_day if et0_mm_day is not None else self.default_et0,
        )

        # 6. Vadose Depletion, Transpiration Stress & CWSI
        stress = self.stress_engine.evaluate_stress(
            theta_rz=trz,
            theta_fc=theta_fc,
            z_r_m=pheno.z_r_m,
            raw_mm=reservoir.raw_mm,
            taw_mm=reservoir.taw_mm,
            kcb=pheno.kcb,
            ke=dual_kc.ke,
            et0_mm_day=dual_kc.et0_mm_day,
        )

        t_elapsed = time.perf_counter() - t0
        latency_px = (t_elapsed * 1000.0) / (H * W)

        provenance = {
            "engine": "AgronomyDomainEngine-v1.0",
            "standards": ["FAO-56", "DO-178C-Level-A"],
            "crop_species": crop_params.get("common_name", crop_name),
            "soil_texture": tex_props.texture_name,
            "soil_fc_m3m3": theta_fc,
            "soil_wp_m3m3": theta_wp,
            "grid_dimensions": [H, W],
            "total_pixels": H * W,
        }

        return AgronomicStateVector(
            ndvi=pheno.ndvi,
            fractional_cover=pheno.fractional_cover,
            root_depth_m=pheno.z_r_m,
            taw_mm=reservoir.taw_mm,
            raw_mm=reservoir.raw_mm,
            kcb=dual_kc.kcb,
            ke=dual_kc.ke,
            kc_potential=dual_kc.kc_total,
            root_depletion_dr_mm=stress.dr_mm,
            water_stress_ks=stress.ks,
            cwsi=stress.cwsi,
            etc_actual_mm_day=stress.etc_act_mm_day,
            transpiration_deficit_mm_day=stress.et_deficit_mm_day,
            execution_time_ms=t_elapsed * 1000.0,
            latency_ms_per_pixel=latency_px,
            provenance=provenance,
        )
