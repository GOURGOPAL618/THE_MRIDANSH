# THE MRIDANSH - Agriculture Domain Translator
# Module: 4_domain_translators/agronomy/crop_water_stress.py
# Standard: United Nations FAO-56 Water Stress Mechanics (Allen et al., 1998, Chapter 8)
# DO-178C Level-A Avionics & Remote Sensing Rigor

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger("MRIDANSH.AgriTranslator.CropStress")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@dataclass
class WaterStressOutput:
    """
    Evaluated soil water depletion, transpiration reduction, and stress classification.

    Fields:
      dr_mm: Root zone soil water depletion (mm)
      ks: Transpiration reduction factor [0.0, 1.0] (1.0 = no stress, 0.0 = wilting)
      cwsi: Crop Water Stress Index [0.0, 1.0] (0.0 = healthy, 1.0 = severe drought)
      etc_act_mm_day: Actual crop evapotranspiration (mm/day)
      et_deficit_mm_day: Transpiration deficit (mm/day)
      stress_fraction: Fraction of root-zone capacity depleted
    """
    dr_mm: Union[float, np.ndarray]
    ks: Union[float, np.ndarray]
    cwsi: Union[float, np.ndarray]
    etc_act_mm_day: Union[float, np.ndarray]
    et_deficit_mm_day: Union[float, np.ndarray]
    stress_fraction: Union[float, np.ndarray]


class CropWaterStressEngine:
    """
    Computes root-zone depletion (Dr), transpiration reduction (Ks),
    Crop Water Stress Index (CWSI), and actual crop evapotranspiration (ETc_act)
    under non-standard and drought conditions.
    """

    def __init__(self, wilting_buffer_fraction: float = 0.01):
        self.wilting_buffer = float(wilting_buffer_fraction)

    @staticmethod
    def compute_root_zone_depletion(
        theta_rz: Union[float, np.ndarray],
        theta_fc: Union[float, np.ndarray],
        z_r_m: Union[float, np.ndarray],
    ) -> Union[float, np.ndarray]:
        """
        Calculates Root-Zone Soil Water Depletion Dr (FAO-56 Eq. 83):
            Dr = 1000 * (theta_fc - theta_rz) * z_r_m   [mm]

        If theta_rz >= theta_fc, depletion Dr = 0.0 (soil is at or above field capacity).
        """
        trz = np.asarray(theta_rz, dtype=np.float32)
        tfc = np.asarray(theta_fc, dtype=np.float32)
        zr = np.asarray(z_r_m, dtype=np.float32)

        # Depletion in mm
        dr = 1000.0 * (tfc - trz) * zr
        dr = np.maximum(dr, 0.0)

        if np.isscalar(theta_rz) and np.isscalar(theta_fc) and np.isscalar(z_r_m):
            return float(dr)
        return dr

    @staticmethod
    def compute_water_stress_coefficient(
        dr_mm: Union[float, np.ndarray],
        raw_mm: Union[float, np.ndarray],
        taw_mm: Union[float, np.ndarray],
    ) -> Union[float, np.ndarray]:
        """
        Derives the FAO-56 transpiration reduction factor Ks (FAO-56 Eq. 84):
          - If Dr <= RAW: Ks = 1.0 (No water stress, stomata remain open)
          - If Dr > RAW: Ks = (TAW - Dr) / (TAW - RAW) (Stomata partially close)
          - If Dr >= TAW: Ks = 0.0 (Severe stress, permanent wilting point reached)
        """
        dr = np.asarray(dr_mm, dtype=np.float32)
        raw = np.asarray(raw_mm, dtype=np.float32)
        taw = np.asarray(taw_mm, dtype=np.float32)

        # Denominator: extractable reserve between RAW and TAW
        den = np.maximum(taw - raw, 1.0)  # Avoid division by zero
        ks_stressed = (taw - dr) / den
        ks_stressed = np.clip(ks_stressed, 0.0, 1.0)

        # Piecewise selection
        ks = np.where(dr <= raw, 1.0, ks_stressed)
        ks = np.where(dr >= taw, 0.0, ks)
        ks = np.clip(ks, 0.0, 1.0)

        if np.isscalar(dr_mm) and np.isscalar(raw_mm) and np.isscalar(taw_mm):
            return float(ks)
        return ks

    @staticmethod
    def compute_crop_water_stress_index(
        ks: Union[float, np.ndarray],
    ) -> Union[float, np.ndarray]:
        """
        Calculates the Crop Water Stress Index (CWSI):
            CWSI = 1.0 - Ks
        Ranges continuously from 0.0 (No stress / Optimal) to 1.0 (Extreme Drought / Wilting).
        """
        ks_arr = np.asarray(ks, dtype=np.float32)
        cwsi = 1.0 - ks_arr
        cwsi = np.clip(cwsi, 0.0, 1.0)

        if np.isscalar(ks):
            return float(cwsi)
        return cwsi

    def evaluate_stress(
        self,
        theta_rz: Union[float, np.ndarray],
        theta_fc: Union[float, np.ndarray],
        z_r_m: Union[float, np.ndarray],
        raw_mm: Union[float, np.ndarray],
        taw_mm: Union[float, np.ndarray],
        kcb: Union[float, np.ndarray],
        ke: Union[float, np.ndarray],
        et0_mm_day: Union[float, np.ndarray] = 4.5,
    ) -> WaterStressOutput:
        """
        Evaluates full water stress and actual crop evapotranspiration fluxes:
            ETc_act = (Ks * Kcb + Ke) * ET0
            ET_deficit = (1 - Ks) * Kcb * ET0 = CWSI * Kcb * ET0
        """
        # 1. Root zone depletion
        dr = self.compute_root_zone_depletion(
            theta_rz=theta_rz,
            theta_fc=theta_fc,
            z_r_m=z_r_m,
        )

        # 2. Water stress coefficient Ks
        ks = self.compute_water_stress_coefficient(
            dr_mm=dr,
            raw_mm=raw_mm,
            taw_mm=taw_mm,
        )

        # 3. Crop Water Stress Index
        cwsi = self.compute_crop_water_stress_index(ks)

        # 4. Actual ET and Deficit
        kcb_arr = np.asarray(kcb, dtype=np.float32)
        ke_arr = np.asarray(ke, dtype=np.float32)
        et0_arr = np.asarray(et0_mm_day, dtype=np.float32)

        etc_act = (ks * kcb_arr + ke_arr) * et0_arr
        et_deficit = cwsi * kcb_arr * et0_arr

        # Fraction of TAW capacity depleted
        taw_arr = np.asarray(taw_mm, dtype=np.float32)
        stress_frac = np.clip(dr / np.maximum(taw_arr, 1.0), 0.0, 2.0)

        # DO-178C Safety assertions
        if np.any(np.isnan(ks)) or np.any(np.isinf(ks)):
            raise AssertionError("DO-178C Violation: NaN or Inf in Ks calculation")
        if np.any(np.isnan(cwsi)) or np.any(np.isinf(cwsi)):
            raise AssertionError("DO-178C Violation: NaN or Inf in CWSI calculation")
        if np.any(np.isnan(etc_act)) or np.any(np.isinf(etc_act)):
            raise AssertionError("DO-178C Violation: NaN or Inf in ETc_act calculation")

        if np.isscalar(theta_rz):
            return WaterStressOutput(
                dr_mm=float(dr),
                ks=float(ks),
                cwsi=float(cwsi),
                etc_act_mm_day=float(etc_act),
                et_deficit_mm_day=float(et_deficit),
                stress_fraction=float(stress_frac),
            )

        return WaterStressOutput(
            dr_mm=dr,
            ks=ks,
            cwsi=cwsi,
            etc_act_mm_day=etc_act,
            et_deficit_mm_day=et_deficit,
            stress_fraction=stress_frac,
        )
