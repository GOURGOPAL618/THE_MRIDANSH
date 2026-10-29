# THE MRIDANSH - Agriculture Domain Translator
# Module: 4_domain_translators/agronomy/irrigation_prescription.py
# Standard: United Nations FAO-56 & Precision Variable-Rate Irrigation (VRI) Mechanics
# DO-178C Level-A Avionics & Remote Sensing Rigor

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger("MRIDANSH.AgriTranslator.IrrigationPrescription")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Dimensional Constants
LITERS_PER_HA_PER_MM: float = 10000.0       # 1 mm over 1 ha (10,000 m2) = 10 m3 = 10,000 Liters
LITERS_PER_10M_PIXEL_PER_MM: float = 100.0  # 1 mm over 10m x 10m (100 m2) = 0.1 m3 = 100 Liters
DEFAULT_PIXEL_AREA_M2: float = 100.0        # 10m ground resolution


class IrrigationStrategy(str, Enum):
    """Irrigation management operational strategies."""
    STRESS_AVOIDANCE = "STRESS_AVOIDANCE"  # Refills only the deficit exceeding RAW (max water conservation)
    FULL_RECHARGE = "FULL_RECHARGE"        # Restores entire depleted root zone to Field Capacity if Dr > RAW
    MAINTENANCE = "MAINTENANCE"            # Replaces daily actual evapotranspiration loss


class IrrigationSystemType(str, Enum):
    """Irrigation hardware application efficiencies (ASABE & FAO-56 Standards)."""
    DRIP_MICRO = "DRIP_MICRO"          # Typical efficiency eta = 0.90
    CENTER_PIVOT = "CENTER_PIVOT"      # Typical efficiency eta = 0.80
    SURFACE_FLOOD = "SURFACE_FLOOD"    # Typical efficiency eta = 0.60


SYSTEM_EFFICIENCY_MAP: Dict[str, float] = {
    IrrigationSystemType.DRIP_MICRO.value: 0.90,
    IrrigationSystemType.CENTER_PIVOT.value: 0.80,
    IrrigationSystemType.SURFACE_FLOOD.value: 0.60,
}


@dataclass
class IrrigationPrescriptionMap:
    """
    Spatial prescription map for Variable-Rate Irrigation (VRI) equipment.
    
    Fields:
      net_irrigation_mm: Net water depth requirement (mm)
      gross_irrigation_mm: Gross water depth accounting for application efficiency (mm)
      liters_per_hectare: Volume of water per hectare (L/ha)
      liters_per_pixel: Volume of water per 10m pixel (L/pixel)
      priority_mask: Boolean spatial mask where True indicates immediate irrigation trigger
      trigger_fraction: Spatial percentage of scene requiring irrigation (%)
      mean_prescription_l_ha: Mean water volume across irrigable pixels (L/ha)
      execution_time_ms: Computation runtime in milliseconds
      latency_ms_per_pixel: Computation speed per spatial pixel
    """
    net_irrigation_mm: np.ndarray
    gross_irrigation_mm: np.ndarray
    liters_per_hectare: np.ndarray
    liters_per_pixel: np.ndarray
    priority_mask: np.ndarray
    trigger_fraction_pct: float
    mean_prescription_l_ha: float
    execution_time_ms: float
    latency_ms_per_pixel: float


class PrecisionIrrigationEngine:
    """
    Precision Variable-Rate Irrigation (VRI) Engine.
    Transforms root-zone depletion (Dr) and Readily Available Water (RAW)
    into farm-scale prescription maps (L/ha and L/pixel).
    """

    def __init__(
        self,
        default_strategy: IrrigationStrategy = IrrigationStrategy.FULL_RECHARGE,
        default_system: IrrigationSystemType = IrrigationSystemType.DRIP_MICRO,
        pixel_resolution_m: float = 10.0,
    ):
        self.default_strategy = default_strategy
        self.default_system = default_system
        self.pixel_res = float(pixel_resolution_m)
        self.pixel_area_m2 = self.pixel_res * self.pixel_res

    def compute_prescription(
        self,
        dr_mm: Union[float, np.ndarray],
        raw_mm: Union[float, np.ndarray],
        taw_mm: Optional[Union[float, np.ndarray]] = None,
        etc_act_mm_day: Optional[Union[float, np.ndarray]] = None,
        strategy: Optional[Union[str, IrrigationStrategy]] = None,
        system_type: Optional[Union[str, IrrigationSystemType]] = None,
        application_efficiency: Optional[float] = None,
    ) -> IrrigationPrescriptionMap:
        """
        Derives pixel-by-pixel Variable-Rate Irrigation requirements.

        Parameters:
            dr_mm: Root-zone soil water depletion in millimeters (mm)
            raw_mm: Readily Available Water threshold in millimeters (mm)
            taw_mm: Total Available Water capacity in millimeters (mm, optional)
            etc_act_mm_day: Daily actual evapotranspiration (mm/day, optional for MAINTENANCE mode)
            strategy: Operational dispatch strategy
            system_type: Irrigation hardware type (determines efficiency eta)
            application_efficiency: Explicit override for application efficiency (0.3 <= eta <= 1.0)

        Returns:
            IrrigationPrescriptionMap with spatial volumetric grids
        """
        t0 = time.perf_counter()

        # 1. Resolve strategy and efficiency
        strat = IrrigationStrategy(strategy) if strategy is not None else self.default_strategy
        
        if application_efficiency is not None:
            eta = float(np.clip(application_efficiency, 0.30, 1.00))
        elif system_type is not None:
            sys_key = system_type.value if isinstance(system_type, IrrigationSystemType) else str(system_type)
            eta = SYSTEM_EFFICIENCY_MAP.get(sys_key, 0.85)
        else:
            eta = SYSTEM_EFFICIENCY_MAP[self.default_system.value]

        # 2. Vectorize inputs
        dr = np.asarray(dr_mm, dtype=np.float32)
        raw = np.asarray(raw_mm, dtype=np.float32)

        # 3. Derive Net Irrigation Requirement I_net (mm)
        if strat == IrrigationStrategy.STRESS_AVOIDANCE:
            # Only refill the deficit that exceeds RAW (brings back to stress threshold)
            i_net = np.maximum(0.0, dr - raw)
        elif strat == IrrigationStrategy.FULL_RECHARGE:
            # If stress is triggered (Dr > RAW), restore the entire root zone to Field Capacity (Dr)
            i_net = np.where(dr > raw, dr, 0.0)
        elif strat == IrrigationStrategy.MAINTENANCE:
            # Daily ETc replacement if available, otherwise fallback to Dr - RAW
            if etc_act_mm_day is not None:
                etc_arr = np.asarray(etc_act_mm_day, dtype=np.float32)
                i_net = np.maximum(0.0, etc_arr)
            else:
                i_net = np.maximum(0.0, dr - raw)
        else:
            raise ValueError(f"Unsupported irrigation strategy: {strat}")

        # Ensure non-negativity and cap at TAW if provided
        i_net = np.maximum(i_net, 0.0)
        if taw_mm is not None:
            taw = np.asarray(taw_mm, dtype=np.float32)
            i_net = np.minimum(i_net, taw)

        # 4. Gross Irrigation Requirement accounting for efficiency
        i_gross = i_net / eta

        # 5. Volumetric Conversion to Farm Scale (L/ha) and Pixel Scale (L/pixel)
        # Formula: 1 mm depth * 10,000 m2/ha * 10^-3 m/mm * 1000 L/m3 = 10,000 L/ha per mm
        liters_per_ha = i_gross * LITERS_PER_HA_PER_MM

        # Formula: Area of pixel (m2) * depth (m) * 1000 L/m3 = area * 10^-3 * 1000 = area * depth_mm
        # For 10m x 10m: 100 m2 * 1 mm = 100 Liters / pixel per mm
        liters_per_pixel = i_gross * (self.pixel_area_m2 / 1000.0) * 1000.0  # i_gross * 100.0

        # 6. Priority Trigger Mask
        priority_mask = i_net > 0.0
        total_pixels = i_net.size
        trigger_count = int(np.sum(priority_mask))
        trigger_pct = (trigger_count / max(total_pixels, 1)) * 100.0

        mean_presc = float(np.mean(liters_per_ha[priority_mask])) if trigger_count > 0 else 0.0

        t_elapsed = time.perf_counter() - t0
        latency_px = (t_elapsed * 1000.0) / max(total_pixels, 1)

        # DO-178C Safety Assertions
        if np.any(np.isnan(i_net)) or np.any(np.isinf(i_net)):
            raise AssertionError("DO-178C Violation: NaN or Inf in net irrigation derivation")
        if np.any(np.isnan(liters_per_ha)) or np.any(np.isinf(liters_per_ha)):
            raise AssertionError("DO-178C Violation: NaN or Inf in volumetric L/ha derivation")
        if np.any(i_net < 0.0):
            raise AssertionError("Physics Violation: Negative irrigation depth encountered")

        return IrrigationPrescriptionMap(
            net_irrigation_mm=i_net,
            gross_irrigation_mm=i_gross,
            liters_per_hectare=liters_per_ha,
            liters_per_pixel=liters_per_pixel,
            priority_mask=priority_mask,
            trigger_fraction_pct=round(trigger_pct, 2),
            mean_prescription_l_ha=round(mean_presc, 2),
            execution_time_ms=round(t_elapsed * 1000.0, 3),
            latency_ms_per_pixel=round(latency_px, 6),
        )
