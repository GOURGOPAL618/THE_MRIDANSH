# THE MRIDANSH - Agriculture Domain Translator
# Module: 4_domain_translators/agronomy/fao56_dual_kc.py
# Standard: United Nations FAO-56 Dual Crop Coefficient (Allen et al., 1998, Chapter 7)
# DO-178C Level-A Avionics & Remote Sensing Rigor

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger("MRIDANSH.AgriTranslator.DualKc")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@dataclass
class DualKcOutput:
    """
    Partitioned dual crop evapotranspiration coefficients and flux rates.
    
    Fields:
      kc_total: Total potential crop coefficient Kc = Kcb + Ke
      kcb: Basal crop transpiration coefficient
      ke: Soil surface evaporation coefficient
      kr: Evaporation reduction coefficient [0.0, 1.0]
      kc_max: Thermodynamic upper ceiling for dual Kc
      et0_mm_day: Atmospheric reference evapotranspiration (mm/day)
      etc_pot_mm_day: Potential crop evapotranspiration (mm/day)
    """
    kc_total: Union[float, np.ndarray]
    kcb: Union[float, np.ndarray]
    ke: Union[float, np.ndarray]
    kr: Union[float, np.ndarray]
    kc_max: Union[float, np.ndarray]
    et0_mm_day: Union[float, np.ndarray]
    etc_pot_mm_day: Union[float, np.ndarray]


class FAO56DualKcEngine:
    """
    Evaluates the FAO-56 Dual Crop Coefficient:
        ETc = (Kcb + Ke) * ET0

    Separates biological transpiration from physical soil evaporation
    using surface moisture inferred from AETHER-MRID1607X and optical cover.
    """

    def __init__(
        self,
        default_et0_mm_day: float = 4.5,
    ):
        """
        Parameters:
            default_et0_mm_day: Baseline daily reference ET (mm/day) for sub-tropical/tropical climates.
        """
        self.default_et0 = float(default_et0_mm_day)

    @staticmethod
    def compute_evaporation_reduction_coefficient(
        theta_surf: Union[float, np.ndarray],
        theta_fc: Union[float, np.ndarray],
        theta_res: Union[float, np.ndarray] = 0.04,
    ) -> Union[float, np.ndarray]:
        """
        Derives Kr, the dimensionless soil evaporation reduction factor (FAO-56 Eq. 74):
          - Stage 1 (Energy-limiting, theta_surf >= theta_fc): Kr = 1.0
          - Stage 2 (Falling rate diffusion, theta_surf < theta_fc):
              Kr = clip( (theta_surf - theta_res) / (theta_fc - theta_res), 0.0, 1.0 )
        """
        ts = np.asarray(theta_surf, dtype=np.float32)
        fc = np.asarray(theta_fc, dtype=np.float32)
        res = np.asarray(theta_res, dtype=np.float32)

        # Numerator: extractable surface water
        num = ts - res
        den = np.maximum(fc - res, 0.02)  # Avoid division by near-zero

        kr = num / den
        kr = np.clip(kr, 0.0, 1.0)

        # Stage 1 override: if moisture exceeds field capacity, evaporation is 100% energy limited
        kr = np.where(ts >= fc, 1.0, kr)

        if np.isscalar(theta_surf):
            return float(kr)
        return kr

    @staticmethod
    def compute_kc_max(
        kcb: Union[float, np.ndarray],
        rh_min_pct: float = 45.0,
        wind_speed_u2_m_s: float = 2.0,
        plant_height_h_m: float = 0.8,
    ) -> Union[float, np.ndarray]:
        """
        Evaluates the upper physical thermodynamic limit Kc_max (FAO-56 Eq. 72):
            Kc_max = max(1.2 + [0.04*(u2 - 2) - 0.004*(RH_min - 45)] * (h/3)^0.3, Kcb + 0.05)
        """
        kcb_arr = np.asarray(kcb, dtype=np.float32)

        # Climate adjustment factor
        climate_term = (0.04 * (wind_speed_u2_m_s - 2.0) - 0.004 * (rh_min_pct - 45.0)) * ((plant_height_h_m / 3.0) ** 0.3)
        kc_max_base = 1.20 + climate_term

        # Upper limit must be at least Kcb + 0.05
        kc_max = np.maximum(kc_max_base, kcb_arr + 0.05)
        kc_max = np.clip(kc_max, 1.05, 1.50)

        if np.isscalar(kcb):
            return float(kc_max)
        return kc_max

    def compute_dual_coefficients(
        self,
        kcb: Union[float, np.ndarray],
        fractional_cover: Union[float, np.ndarray],
        theta_surf: Union[float, np.ndarray],
        theta_fc: Union[float, np.ndarray],
        theta_res: Union[float, np.ndarray] = 0.04,
        rh_min_pct: float = 45.0,
        wind_speed_u2_m_s: float = 2.0,
        plant_height_h_m: float = 0.8,
        et0_mm_day: Optional[Union[float, np.ndarray]] = None,
    ) -> DualKcOutput:
        """
        Full FAO-56 dual crop coefficient decomposition.

        Formulations:
            Kr = Stage 2 soil reduction factor
            few = (1 - fc) exposed soil fraction
            Ke = Kr * few * (Kc_max - Kcb)
            Kc = Kcb + Ke  (with Kc <= Kc_max constraint)
            ETc_pot = Kc * ET0
        """
        kcb_arr = np.asarray(kcb, dtype=np.float32)
        fc_arr = np.asarray(fractional_cover, dtype=np.float32)
        ts_arr = np.asarray(theta_surf, dtype=np.float32)
        t_fc = np.asarray(theta_fc, dtype=np.float32)

        # 1. Kc_max calculation
        kc_max = self.compute_kc_max(
            kcb=kcb_arr,
            rh_min_pct=rh_min_pct,
            wind_speed_u2_m_s=wind_speed_u2_m_s,
            plant_height_h_m=plant_height_h_m,
        )

        # 2. Soil evaporation reduction coefficient Kr
        kr = self.compute_evaporation_reduction_coefficient(
            theta_surf=ts_arr,
            theta_fc=t_fc,
            theta_res=theta_res,
        )

        # 3. Soil evaporation coefficient Ke (FAO-56 Eq. 71)
        few = np.clip(1.0 - fc_arr, 0.0, 1.0)
        ke = kr * few * (kc_max - kcb_arr)
        ke = np.maximum(ke, 0.0)

        # Physical limit: Ke cannot exceed few * Kc_max
        ke = np.minimum(ke, few * kc_max)

        # 4. Total dual crop coefficient Kc = Kcb + Ke
        kc_total = kcb_arr + ke
        kc_total = np.minimum(kc_total, kc_max)

        # 5. Reference ET0 and Potential ETc
        if et0_mm_day is None:
            et0 = np.full_like(kc_total, self.default_et0) if isinstance(kc_total, np.ndarray) else self.default_et0
        else:
            et0 = np.asarray(et0_mm_day, dtype=np.float32)

        etc_pot = kc_total * et0

        # Safety assertions
        if np.any(np.isnan(kc_total)) or np.any(np.isinf(kc_total)):
            raise AssertionError("DO-178C Violation: NaN or Inf encountered in dual Kc calculation")
        if np.any(np.isnan(etc_pot)) or np.any(np.isinf(etc_pot)):
            raise AssertionError("DO-178C Violation: NaN or Inf encountered in ETc calculation")

        if np.isscalar(kcb) and np.isscalar(fractional_cover) and np.isscalar(theta_surf):
            return DualKcOutput(
                kc_total=float(kc_total),
                kcb=float(kcb_arr),
                ke=float(ke),
                kr=float(kr),
                kc_max=float(kc_max),
                et0_mm_day=float(et0),
                etc_pot_mm_day=float(etc_pot),
            )

        return DualKcOutput(
            kc_total=kc_total,
            kcb=kcb_arr,
            ke=ke,
            kr=kr,
            kc_max=kc_max,
            et0_mm_day=et0,
            etc_pot_mm_day=etc_pot,
        )
