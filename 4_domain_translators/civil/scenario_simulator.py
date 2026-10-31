# THE MRIDANSH - CIVIL & GEOTECHNICAL DOMAIN TRANSLATOR
# Module: 4_domain_translators/civil/scenario_simulator.py
# Subsystem 05 of AETHER-MRID1607X Core Engine
# Architecture: Dynamic Multi-Hazard Scenario Simulator (Rainfall Surge, Vehicle Mobility, Flood Liquefaction)
# Standards: Eurocode 7 (EN 1997-1) / USACE TM 5-818-1 / NATO STANAG 4370 Mobility

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Union

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

GRAVITY_M_S2: float = 9.80665
WATER_UNIT_WEIGHT_KN_M3: float = 9.80665

# Standard NATO / USACE Vehicle Class Parameters
VEHICLE_CLASS_1_HEAVY_PRESSURE_KPA: float = 280.0   # Main Battle Tank / Heavy Crane (>30t)
VEHICLE_CLASS_2_MEDIUM_PRESSURE_KPA: float = 180.0  # 6x6 Heavy Logistics / Dump Truck (10-30t)
VEHICLE_CLASS_3_LIGHT_PRESSURE_KPA: float = 85.0    # Light Tactical / Utility 4x4 (<5t)
QUAGMIRE_BEARING_THRESHOLD_KPA: float = 70.0        # Soils below this are impassable bogs/quagmires

# Max slope limits for vehicular negotiation
MAX_SLOPE_CLASS_1_DEG: float = 25.0
MAX_SLOPE_CLASS_2_DEG: float = 20.0
MAX_SLOPE_CLASS_3_DEG: float = 30.0


@dataclass(frozen=True)
class HeavyRainfallSimulationResult:
    """Telemetry result of heavy precipitation surge scenario."""
    theta_simulated: np.ndarray
    moisture_surge: np.ndarray
    matric_suction_simulated_kpa: np.ndarray
    apparent_cohesion_simulated_kpa: np.ndarray
    q_allow_simulated_kpa: np.ndarray
    bearing_capacity_drop_pct: np.ndarray
    fs_slope_simulated: np.ndarray
    slope_safety_factor_drop: np.ndarray
    landslide_destabilized_count: int
    mean_bearing_drop_pct: float
    rainfall_amount_mm: float


@dataclass(frozen=True)
class VehicleMobilitySimulationResult:
    """Telemetry result of NATO/USACE off-road vehicle mobility simulation."""
    class1_heavy_tank_status: np.ndarray   # 0: No-Go, 1: Marginal Risk, 2: Passable
    class2_medium_truck_status: np.ndarray # 0: No-Go, 1: Marginal Risk, 2: Passable
    class3_light_suv_status: np.ndarray    # 0: No-Go, 1: Marginal Risk, 2: Passable
    quagmire_risk_mask: np.ndarray         # True where soil is an impassable mud trap
    composite_mobility_tier: np.ndarray    # 3: All Go, 2: Medium+Light, 1: Light Only, 0: No-Go
    passable_area_pct_class1: float
    passable_area_pct_class2: float
    passable_area_pct_class3: float
    quagmire_area_pct: float


@dataclass(frozen=True)
class FloodLiquefactionSimulationResult:
    """Telemetry result of flood inundation and liquefaction quicksand hazard."""
    effective_stress_residual_kpa: np.ndarray
    pore_water_pressure_flood_kpa: np.ndarray
    critical_hydraulic_gradient: float
    liquefaction_susceptibility_index: np.ndarray  # Continuous 0.0 to 1.0
    quicksand_hazard_mask: np.ndarray              # True in severe liquefaction zones
    bearing_capacity_flooded_kpa: np.ndarray
    mean_liquefaction_index: float
    quicksand_hazard_area_pct: float
    flood_water_depth_m: float


class DynamicScenarioSimulator:
    """
    Executes dynamic multi-hazard civil and geotechnical stress simulations:
    1. Heavy Rainfall Surge: Infiltration surge, suction collapse, bearing drop, slope trigger.
    2. Vehicle Load Mobility: NATO / USACE wheeled and tracked passability classifications.
    3. Flood & Liquefaction: Zero effective stress, quicksand hazard, critical hydraulic gradient.
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

    def simulate_heavy_rainfall(
        self,
        theta_initial: np.ndarray,
        slope_deg: np.ndarray,
        rainfall_amount_mm: float = 50.0,
        soil_class: str = "silt_loam",
        wetting_depth_m: float = 0.50,
        infiltration_efficiency: float = 0.85,
    ) -> HeavyRainfallSimulationResult:
        """
        Simulates sudden heavy monsoon precipitation downpour:
        - Infiltration pushes vadose moisture towards saturation: theta_sim = min(theta + d_theta, theta_sat).
        - Dissipates matric suction (psi -> 0), degrading apparent cohesion c_app.
        - Calculates bearing drop (Delta q_allow) and slope destabilization (Delta FS_slope).
        """
        theta_arr = np.asarray(theta_initial, dtype=np.float64)
        slope_arr = np.asarray(slope_deg, dtype=np.float64)
        params = self.soil_engine.get_parameters(soil_class)

        # Baseline un-simulated states
        base_bearing = self.stability_engine.compute_bearing_capacity(theta_arr, soil_class)
        base_slope = self.slope_engine.compute_slope_stability(slope_arr, theta_arr, soil_class)

        # Volumetric moisture increment: d_theta = (rainfall_mm * efficiency) / (wetting_depth_m * 1000)
        d_theta = (rainfall_amount_mm * infiltration_efficiency) / (wetting_depth_m * 1000.0)
        
        # Saturated ceiling clamp: theta cannot exceed theta_sat - 1e-4 for analytical suction stability
        max_theta = params.theta_sat - 1e-4
        theta_sim = np.clip(theta_arr + d_theta, params.theta_res + 1e-4, max_theta)
        actual_surge = theta_sim - theta_arr

        # Re-evaluate post-rainfall ground stability
        post_bearing = self.stability_engine.compute_bearing_capacity(theta_sim, soil_class)
        post_slope = self.slope_engine.compute_slope_stability(slope_arr, theta_sim, soil_class)

        # Bearing drop: Delta q_allow = q_base - q_sim
        delta_q = np.maximum(0.0, base_bearing.q_allow_kpa - post_bearing.q_allow_kpa)
        bearing_drop_pct = (delta_q / np.maximum(1e-3, base_bearing.q_allow_kpa)) * 100.0

        # Slope safety factor drop: Delta FS = FS_base - FS_sim
        delta_fs = np.maximum(0.0, base_slope.factor_of_safety - post_slope.factor_of_safety)

        # Count newly destabilized slope zones (where base was stable FS >= 1.2, but post-rain is FS < 1.2)
        base_stable = base_slope.factor_of_safety >= 1.2
        post_unstable = post_slope.factor_of_safety < 1.2
        newly_destabilized = np.logical_and(base_stable, post_unstable)
        landslide_destabilized_count = int(np.sum(newly_destabilized))

        return HeavyRainfallSimulationResult(
            theta_simulated=theta_sim.astype(np.float32),
            moisture_surge=actual_surge.astype(np.float32),
            matric_suction_simulated_kpa=post_bearing.apparent_cohesion_kpa.astype(np.float32),
            apparent_cohesion_simulated_kpa=post_bearing.apparent_cohesion_kpa.astype(np.float32),
            q_allow_simulated_kpa=post_bearing.q_allow_kpa.astype(np.float32),
            bearing_capacity_drop_pct=bearing_drop_pct.astype(np.float32),
            fs_slope_simulated=post_slope.factor_of_safety.astype(np.float32),
            slope_safety_factor_drop=delta_fs.astype(np.float32),
            landslide_destabilized_count=landslide_destabilized_count,
            mean_bearing_drop_pct=float(np.mean(bearing_drop_pct)),
            rainfall_amount_mm=float(rainfall_amount_mm),
        )

    def simulate_vehicle_mobility(
        self,
        q_allow_kpa: np.ndarray,
        slope_deg: np.ndarray,
    ) -> VehicleMobilitySimulationResult:
        """
        Evaluates NATO / USACE off-road mobility across 3 standardized vehicle classes:
        - Class 1: Main Battle Tank / Heavy Crane (>30t, 280 kPa)
        - Class 2: Medium Transport Hauler (10-30t, 180 kPa)
        - Class 3: Light Tactical 4x4 (<5t, 85 kPa)
        - Quagmire Flag: Soils with allowable bearing < 70 kPa
        """
        q_allow = np.asarray(q_allow_kpa, dtype=np.float64)
        slope = np.asarray(slope_deg, dtype=np.float64)

        def _evaluate_class(pressure_kpa: float, max_slope: float) -> np.ndarray:
            """
            0: No-Go (insufficient bearing or excessive slope)
            1: Marginal Risk (0.7 * pressure <= q_allow < pressure)
            2: Passable (q_allow >= pressure and slope <= max_slope)
            """
            status = np.zeros_like(q_allow, dtype=np.int32)
            passable = np.logical_and(q_allow >= pressure_kpa, slope <= max_slope)
            marginal = np.logical_and(
                q_allow >= 0.70 * pressure_kpa,
                np.logical_and(q_allow < pressure_kpa, slope <= (max_slope + 2.0))
            )
            status[marginal] = 1
            status[passable] = 2
            return status

        c1_status = _evaluate_class(VEHICLE_CLASS_1_HEAVY_PRESSURE_KPA, MAX_SLOPE_CLASS_1_DEG)
        c2_status = _evaluate_class(VEHICLE_CLASS_2_MEDIUM_PRESSURE_KPA, MAX_SLOPE_CLASS_2_DEG)
        c3_status = _evaluate_class(VEHICLE_CLASS_3_LIGHT_PRESSURE_KPA, MAX_SLOPE_CLASS_3_DEG)

        # Quagmire risk: bearing < 70 kPa (wheel sinkage / bog)
        quagmire_mask = q_allow < QUAGMIRE_BEARING_THRESHOLD_KPA

        # Composite mobility tier:
        # 3: All vehicles passable (C1=2, C2=2, C3=2)
        # 2: Medium & Light passable (C2=2, C3=2, C1<2)
        # 1: Light vehicle only (C3=2, C2<2, C1<2)
        # 0: Complete No-Go / Quagmire
        composite = np.zeros_like(c1_status, dtype=np.int32)
        composite[c3_status >= 1] = 1
        composite[c2_status >= 1] = 2
        composite[c1_status == 2] = 3
        composite[quagmire_mask] = 0

        total_px = float(q_allow.size)
        pct_c1 = float(np.sum(c1_status == 2) / total_px * 100.0)
        pct_c2 = float(np.sum(c2_status == 2) / total_px * 100.0)
        pct_c3 = float(np.sum(c3_status == 2) / total_px * 100.0)
        pct_quag = float(np.sum(quagmire_mask) / total_px * 100.0)

        return VehicleMobilitySimulationResult(
            class1_heavy_tank_status=c1_status,
            class2_medium_truck_status=c2_status,
            class3_light_suv_status=c3_status,
            quagmire_risk_mask=quagmire_mask,
            composite_mobility_tier=composite,
            passable_area_pct_class1=pct_c1,
            passable_area_pct_class2=pct_c2,
            passable_area_pct_class3=pct_c3,
            quagmire_area_pct=pct_quag,
        )

    def simulate_flood_liquefaction(
        self,
        theta_initial: np.ndarray,
        slope_deg: np.ndarray,
        soil_class: str = "silt_loam",
        flood_water_depth_m: float = 0.50,
        upward_seepage_gradient: float = 0.35,
    ) -> FloodLiquefactionSimulationResult:
        """
        Simulates surface flood inundation and upward hydrostatic seepage:
        - Critical hydraulic exit gradient (Terzaghi): i_crit = (Gs - 1) / (1 + e) = gamma' / gamma_w.
        - Loss of effective stress: sigma' = sigma_total - u_w -> 0.
        - Calculates Liquefaction / Quicksand Susceptibility Index (0.0 to 1.0).
        """
        theta_arr = np.asarray(theta_initial, dtype=np.float64)
        slope_arr = np.asarray(slope_deg, dtype=np.float64)
        params = self.soil_engine.get_parameters(soil_class)

        # Critical hydraulic gradient: i_crit = gamma' / gamma_w
        gamma_sat = params.saturated_unit_weight_kn_m3
        gamma_submerged = max(1.0, gamma_sat - WATER_UNIT_WEIGHT_KN_M3)
        i_crit = float(gamma_submerged / WATER_UNIT_WEIGHT_KN_M3)

        # Foundation depth reference (z = 1.0 m)
        z_ref = 1.0
        sigma_total = gamma_sat * z_ref + (WATER_UNIT_WEIGHT_KN_M3 * flood_water_depth_m)
        
        # Pore water pressure under flood with upward seepage: u = gamma_w * (z + h_flood) + (i * gamma_w * z)
        u_flood = (WATER_UNIT_WEIGHT_KN_M3 * (z_ref + flood_water_depth_m)) + (upward_seepage_gradient * WATER_UNIT_WEIGHT_KN_M3 * z_ref)
        
        # Effective vertical stress: sigma' = sigma_total - u_flood
        sigma_prime = np.maximum(0.0, sigma_total - u_flood)
        sigma_prime_raster = np.full_like(theta_arr, sigma_prime, dtype=np.float64)

        # Saturated bearing capacity under flooded state (suction psi = 0, apparent cohesion = drained c')
        # Saturated shear parameters: cohesion c' only
        factors = self.stability_engine.compute_bearing_capacity_factors(params.friction_angle_deg)
        q_flooded_ult = (
            params.cohesion_kpa * factors.Nc * factors.sc * factors.dc
            + (gamma_submerged * z_ref) * factors.Nq * factors.sq * factors.dq
            + 0.5 * gamma_submerged * self.stability_engine.B * factors.Ngamma * factors.sgamma * factors.dgamma
        )
        q_flooded_allow = max(10.0, q_flooded_ult / self.stability_engine.fs_target)
        q_flooded_raster = np.full_like(theta_arr, q_flooded_allow, dtype=np.float64)

        # Liquefaction Susceptibility Index (0.0 to 1.0):
        # Driven by: (1) upward seepage proximity to i_crit, (2) relative saturation, (3) flat topography
        gradient_ratio = np.clip(upward_seepage_gradient / i_crit, 0.0, 1.0)
        rel_saturation = np.clip(theta_arr / params.theta_sat, 0.0, 1.0)
        flatness_factor = np.clip(np.cos(np.radians(slope_arr)), 0.0, 1.0)

        liquefaction_index = np.clip(gradient_ratio * 0.50 + rel_saturation * 0.35 + flatness_factor * 0.15, 0.0, 1.0)

        # Quicksand hazard threshold: index >= 0.70
        quicksand_mask = liquefaction_index >= 0.70

        total_px = float(theta_arr.size)
        pct_quicksand = float(np.sum(quicksand_mask) / total_px * 100.0)

        return FloodLiquefactionSimulationResult(
            effective_stress_residual_kpa=sigma_prime_raster.astype(np.float32),
            pore_water_pressure_flood_kpa=np.full_like(theta_arr, u_flood, dtype=np.float32),
            critical_hydraulic_gradient=i_crit,
            liquefaction_susceptibility_index=liquefaction_index.astype(np.float32),
            quicksand_hazard_mask=quicksand_mask,
            bearing_capacity_flooded_kpa=q_flooded_raster.astype(np.float32),
            mean_liquefaction_index=float(np.mean(liquefaction_index)),
            quicksand_hazard_area_pct=pct_quicksand,
            flood_water_depth_m=float(flood_water_depth_m),
        )
