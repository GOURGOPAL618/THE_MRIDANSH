# THE MRIDANSH - CIVIL & GEOTECHNICAL DOMAIN TRANSLATOR
# Module: 4_domain_translators/civil/conformal_geotechnical_risk.py
# Subsystem 05 of AETHER-MRID1607X Core Engine
# Architecture: Conformal 2-Sigma Epistemic Decision-Risk Dispatcher
# Standards: Eurocode 7 (EN 1997-1) / IS 1904:2021 / DO-178C Level-A Rigor

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional, Tuple, Union

import numpy as np

try:
    from .ground_stability_engine import GroundStabilityEngine, FoundationBearingResult
    from .slope_stability_engine import SlopeStabilityEngine, SlopeStabilityResult
    from .soil_mechanics_core import GeotechnicalParameters, SoilMechanicsCoreEngine
except ImportError:
    from ground_stability_engine import GroundStabilityEngine, FoundationBearingResult
    from slope_stability_engine import SlopeStabilityEngine, SlopeStabilityResult
    from soil_mechanics_core import GeotechnicalParameters, SoilMechanicsCoreEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


@dataclass(frozen=True)
class ConformalGeotechnicalRiskDispatch:
    """
    Risk-bounded geotechnical dispatch envelope under AETHER 2-sigma conformal uncertainty.
    Eurocode 7 / IS 1904 design invariant: design is strictly governed by conservative lower bounds (q_min, FS_min).
    """
    q_min_kpa: np.ndarray                      # Conservative Lower Bound on Allowable Bearing (wettest 2-sigma bound)
    q_nominal_kpa: np.ndarray                  # Nominal Expected Allowable Bearing
    q_max_kpa: np.ndarray                      # Upper Bound on Allowable Bearing (driest 2-sigma bound)
    q_design_kpa: np.ndarray                   # Eurocode 7 Design Bearing Capacity (strictly equal to q_min)
    fs_min: np.ndarray                         # Conservative Lower Bound on Slope Factor of Safety
    fs_nominal: np.ndarray                     # Nominal Slope Factor of Safety
    fs_max: np.ndarray                         # Upper Bound on Slope Factor of Safety
    fs_design: np.ndarray                      # Eurocode 7 Design Slope Factor of Safety (strictly equal to fs_min)
    bearing_risk_envelope_kpa: np.ndarray      # Half-width uncertainty spread: (q_max - q_min) / 2
    bearing_uncertainty_spread_kpa: np.ndarray # Full uncertainty spread: q_max - q_min
    mean_design_bearing_kpa: float
    mean_design_fs: float
    execution_time_ms: float
    latency_ms_per_pixel: float


class ConformalGeotechnicalRiskDispatcher:
    """
    Propagates AETHER calibrated 2-sigma epistemic uncertainty through non-linear
    unsaturated soil mechanics (van Genuchten matric suction & Fredlund shear degradation).
    
    Theorem (Geotechnical Inverse Monotonicity):
    Because suction and apparent cohesion degrade monotonically with increasing moisture:
    theta_max (wettest bound) yields the lowest suction and cohesion, producing q_min and FS_min.
    theta_min (driest bound) yields the highest suction and cohesion, producing q_max and FS_max.
    Therefore, the ordering invariant q_min <= q_nominal <= q_max holds everywhere.
    """

    def __init__(
        self,
        soil_engine: Optional[SoilMechanicsCoreEngine] = None,
        stability_engine: Optional[GroundStabilityEngine] = None,
        slope_engine: Optional[SlopeStabilityEngine] = None,
    ):
        self.soil_engine = soil_engine or SoilMechanicsCoreEngine()
        self.stability_engine = stability_engine or GroundStabilityEngine(self.soil_engine)
        self.slope_engine = slope_engine or SlopeStabilityEngine(self.soil_engine)

    def dispatch_geotechnical_risk(
        self,
        theta_nominal: np.ndarray,
        sigma_theta_2sigma: np.ndarray,
        slope_deg: np.ndarray,
        soil_class: str = "silt_loam",
    ) -> ConformalGeotechnicalRiskDispatch:
        """
        Computes deterministic 2-sigma risk envelopes for bearing capacity and slope stability:
        - theta_min = max(theta_nominal - 2*sigma, theta_res + 1e-4)
        - theta_max = min(theta_nominal + 2*sigma, theta_sat - 1e-4)
        - q_min = q_allow(theta_max), q_max = q_allow(theta_min)
        - FS_min = FS_slope(theta_max), FS_max = FS_slope(theta_min)
        - Invariant: q_min <= q_nominal <= q_max everywhere.
        """
        t0 = time.perf_counter()
        theta_nom = np.asarray(theta_nominal, dtype=np.float64)
        sigma_2s = np.asarray(sigma_theta_2sigma, dtype=np.float64)
        slope = np.asarray(slope_deg, dtype=np.float64)
        params = self.soil_engine.get_parameters(soil_class)

        # 1. Conformal lower and upper moisture bounds
        theta_min = np.clip(theta_nom - sigma_2s, params.theta_res + 1e-4, params.theta_sat - 1e-4)
        theta_max = np.clip(theta_nom + sigma_2s, params.theta_res + 1e-4, params.theta_sat - 1e-4)

        # 2. Forward bearing evaluations
        res_nom = self.stability_engine.compute_bearing_capacity(theta_nom, soil_class)
        res_wet = self.stability_engine.compute_bearing_capacity(theta_max, soil_class)  # Yields lowest capacity q_min
        res_dry = self.stability_engine.compute_bearing_capacity(theta_min, soil_class)  # Yields highest capacity q_max

        q_nom = res_nom.q_allow_kpa
        q_min = np.minimum(res_wet.q_allow_kpa, q_nom)
        q_max = np.maximum(res_dry.q_allow_kpa, q_nom)

        # 3. Forward slope stability evaluations
        slope_nom = self.slope_engine.compute_slope_stability(slope, theta_nom, soil_class)
        slope_wet = self.slope_engine.compute_slope_stability(slope, theta_max, soil_class)
        slope_dry = self.slope_engine.compute_slope_stability(slope, theta_min, soil_class)

        fs_nom = slope_nom.factor_of_safety
        fs_min = np.minimum(slope_wet.factor_of_safety, fs_nom)
        fs_max = np.maximum(slope_dry.factor_of_safety, fs_nom)

        # 4. Eurocode 7 / IS 1904 Design Invariants
        # Civil design MUST be conservative: governed by lower bound
        q_design = q_min.copy()
        fs_design = fs_min.copy()

        # 5. Risk spread and half-width
        spread_kpa = q_max - q_min
        envelope_kpa = spread_kpa / 2.0

        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000.0
        total_px = float(theta_nom.size)

        return ConformalGeotechnicalRiskDispatch(
            q_min_kpa=q_min.astype(np.float32),
            q_nominal_kpa=q_nom.astype(np.float32),
            q_max_kpa=q_max.astype(np.float32),
            q_design_kpa=q_design.astype(np.float32),
            fs_min=fs_min.astype(np.float32),
            fs_nominal=fs_nom.astype(np.float32),
            fs_max=fs_max.astype(np.float32),
            fs_design=fs_design.astype(np.float32),
            bearing_risk_envelope_kpa=envelope_kpa.astype(np.float32),
            bearing_uncertainty_spread_kpa=spread_kpa.astype(np.float32),
            mean_design_bearing_kpa=float(np.mean(q_design)),
            mean_design_fs=float(np.mean(fs_design)),
            execution_time_ms=elapsed_ms,
            latency_ms_per_pixel=elapsed_ms / total_px,
        )
