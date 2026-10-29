# THE MRIDANSH - Agriculture Domain Translator
# Module: 4_domain_translators/agronomy/conformal_risk_dispatcher.py
# Standard: Conformal Prediction Bounds & Decision-Risk Irrigation Dispatch
# DO-178C Level-A Avionics & Remote Sensing Rigor

import logging
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Union

import numpy as np

try:
    from .irrigation_prescription import (
        IrrigationStrategy,
        IrrigationSystemType,
        PrecisionIrrigationEngine,
        LITERS_PER_HA_PER_MM,
    )
except (ImportError, ValueError):
    from irrigation_prescription import (
        IrrigationStrategy,
        IrrigationSystemType,
        PrecisionIrrigationEngine,
        LITERS_PER_HA_PER_MM,
    )

logger = logging.getLogger("MRIDANSH.AgriTranslator.ConformalRisk")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@dataclass
class ConformalIrrigationDispatch:
    """
    Risk-bounded Variable-Rate Irrigation prescription packet under conformal uncertainty.
    
    Fields:
      i_min_l_ha: Conservative Lower Bound (L/ha) - Over-irrigation & hypoxia protection
      i_nominal_l_ha: Nominal Recommendation (L/ha) - Expected optimal yield target
      i_max_l_ha: Safety Upper Bound (L/ha) - Severe drought & crop wilting emergency buffer
      risk_envelope_l_ha: Uncertainty margin half-width (± L/ha)
      risk_spread_l_ha: Full uncertainty spread ΔI = I_max - I_min (L/ha)
      cwsi_nominal: Nominal Crop Water Stress Index [0.0, 1.0]
      cwsi_max_risk: Worst-case 2-sigma risk Crop Water Stress Index [0.0, 1.0]
      execution_time_ms: Computation runtime in milliseconds
      latency_ms_per_pixel: Computation latency per spatial pixel
    """
    i_min_l_ha: np.ndarray
    i_nominal_l_ha: np.ndarray
    i_max_l_ha: np.ndarray
    risk_envelope_l_ha: np.ndarray
    risk_spread_l_ha: np.ndarray
    cwsi_nominal: np.ndarray
    cwsi_max_risk: np.ndarray
    execution_time_ms: float
    latency_ms_per_pixel: float


class ConformalRiskDispatcher:
    """
    Propagates calibrated 2-sigma epistemic/aleatoric uncertainty envelopes
    from AETHER-MRID1607X into three operational irrigation risk bounds.
    """

    def __init__(self, irrigation_engine: Optional[PrecisionIrrigationEngine] = None):
        self.vri_engine = irrigation_engine or PrecisionIrrigationEngine()

    def dispatch_risk_bounds(
        self,
        theta_rz: np.ndarray,
        uncertainty_2sigma: np.ndarray,
        theta_fc: Union[float, np.ndarray],
        theta_wp: Union[float, np.ndarray],
        theta_sat: Union[float, np.ndarray],
        z_r_m: Union[float, np.ndarray],
        raw_mm: np.ndarray,
        taw_mm: np.ndarray,
        strategy: IrrigationStrategy = IrrigationStrategy.FULL_RECHARGE,
        system_type: IrrigationSystemType = IrrigationSystemType.DRIP_MICRO,
        application_efficiency: Optional[float] = None,
    ) -> ConformalIrrigationDispatch:
        """
        Derives three risk-calibrated irrigation prescriptions (Min, Nominal, Max)
        based on AETHER's conformal ±2σ uncertainty bounds.

        Parameters:
            theta_rz: [H, W] Root-zone volumetric soil moisture (m3/m3)
            uncertainty_2sigma: [H, W] 2-sigma conformal uncertainty (m3/m3)
            theta_fc: Field capacity threshold (m3/m3)
            theta_wp: Wilting point threshold (m3/m3)
            theta_sat: Saturation threshold (m3/m3)
            z_r_m: Dynamic effective rooting depth (m)
            raw_mm: Readily available water (mm)
            taw_mm: Total available water (mm)
            strategy: Operational irrigation strategy
            system_type: Irrigation hardware type
            application_efficiency: System efficiency override

        Returns:
            ConformalIrrigationDispatch containing all 3 risk bounds
        """
        t0 = time.perf_counter()

        # 1. Clean arrays
        trz = np.asarray(theta_rz, dtype=np.float32)
        sigma2 = np.asarray(uncertainty_2sigma, dtype=np.float32)
        tfc = np.asarray(theta_fc, dtype=np.float32)
        twp = np.asarray(theta_wp, dtype=np.float32)
        tsat = np.asarray(theta_sat, dtype=np.float32)
        zr = np.asarray(z_r_m, dtype=np.float32)

        H, W = trz.shape
        total_pixels = H * W

        # 2. Conformal Root-Zone Moisture Bounds [theta_min, theta_max]
        # In worst-case dry scenario, moisture is trz - 2sigma
        theta_rz_min = np.clip(trz - sigma2, twp, tsat)
        # In wet scenario, moisture is trz + 2sigma
        theta_rz_max = np.clip(trz + sigma2, twp, tsat)

        # 3. Conformal Root-Zone Depletions
        # Worst-case dry scenario produces maximum depletion
        dr_max = np.maximum(0.0, 1000.0 * (tfc - theta_rz_min) * zr)
        # Expected nominal scenario produces nominal depletion
        dr_nom = np.maximum(0.0, 1000.0 * (tfc - trz) * zr)
        # Wet scenario produces minimum depletion
        dr_min = np.maximum(0.0, 1000.0 * (tfc - theta_rz_max) * zr)

        # 4. Generate Prescriptions for all three regimes
        presc_min = self.vri_engine.compute_prescription(
            dr_mm=dr_min,
            raw_mm=raw_mm,
            taw_mm=taw_mm,
            strategy=strategy,
            system_type=system_type,
            application_efficiency=application_efficiency,
        )
        presc_nom = self.vri_engine.compute_prescription(
            dr_mm=dr_nom,
            raw_mm=raw_mm,
            taw_mm=taw_mm,
            strategy=strategy,
            system_type=system_type,
            application_efficiency=application_efficiency,
        )
        presc_max = self.vri_engine.compute_prescription(
            dr_mm=dr_max,
            raw_mm=raw_mm,
            taw_mm=taw_mm,
            strategy=strategy,
            system_type=system_type,
            application_efficiency=application_efficiency,
        )

        i_min = presc_min.liters_per_hectare
        i_nom = presc_nom.liters_per_hectare
        i_max = presc_max.liters_per_hectare

        # Enforce strict physical ordering: I_min <= I_nominal <= I_max
        i_nom = np.maximum(i_nom, i_min)
        i_max = np.maximum(i_max, i_nom)

        # 5. Risk Envelope and Spread
        risk_spread = i_max - i_min
        risk_envelope = risk_spread / 2.0

        # 6. Conformal Crop Water Stress Index
        den = np.maximum(taw_mm - raw_mm, 1.0)
        ks_nom = np.clip(np.where(dr_nom <= raw_mm, 1.0, (taw_mm - dr_nom) / den), 0.0, 1.0)
        ks_risk = np.clip(np.where(dr_max <= raw_mm, 1.0, (taw_mm - dr_max) / den), 0.0, 1.0)

        cwsi_nom = 1.0 - ks_nom
        cwsi_risk = 1.0 - ks_risk

        t_elapsed = time.perf_counter() - t0
        latency_px = (t_elapsed * 1000.0) / max(total_pixels, 1)

        # DO-178C Safety Invariant Assertions
        if np.any(np.isnan(i_nom)) or np.any(np.isinf(i_nom)):
            raise AssertionError("DO-178C Violation: NaN or Inf in nominal prescription dispatch")
        if np.any(np.isnan(risk_spread)) or np.any(np.isinf(risk_spread)):
            raise AssertionError("DO-178C Violation: NaN or Inf in risk spread derivation")
        if np.any(i_min > i_nom) or np.any(i_nom > i_max):
            raise AssertionError("Mathematical Invariant Violation: I_min <= I_nominal <= I_max violated")

        return ConformalIrrigationDispatch(
            i_min_l_ha=i_min,
            i_nominal_l_ha=i_nom,
            i_max_l_ha=i_max,
            risk_envelope_l_ha=risk_envelope,
            risk_spread_l_ha=risk_spread,
            cwsi_nominal=cwsi_nom,
            cwsi_max_risk=cwsi_risk,
            execution_time_ms=round(t_elapsed * 1000.0, 3),
            latency_ms_per_pixel=round(latency_px, 6),
        )
