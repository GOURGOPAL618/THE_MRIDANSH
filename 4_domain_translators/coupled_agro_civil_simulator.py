# THE MRIDANSH - UNIFIED PHYSICS CORE & DOMAIN TRANSLATORS
# Module: 4_domain_translators/coupled_agro_civil_simulator.py
# Subsystem 06: Cross-Domain Agro-Geotechnical Simulation Engine
# Architecture: Coupled Paddy Nursery Bed (Tala Gachha) Hydraulics & Tractor Puddling Mechanics
# Standards: FAO-56 / Bekker-Meyerhof Soil Mechanics / RTCA DO-178C Level-A Monte Carlo

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

# Import Civil & Geotechnical Components
try:
    from .civil.ground_stability_engine import GroundStabilityEngine
    from .civil.slope_stability_engine import SlopeStabilityEngine
    from .civil.soil_mechanics_core import GeotechnicalParameters, SoilMechanicsCoreEngine
except ImportError:
    from civil.ground_stability_engine import GroundStabilityEngine
    from civil.slope_stability_engine import SlopeStabilityEngine
    from civil.soil_mechanics_core import GeotechnicalParameters, SoilMechanicsCoreEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Standard Agricultural Tractor Specs (Mahindra / Swaraj 35-45 HP Class)
DEFAULT_TRACTOR_PRESSURE_KPA: float = 140.0    # Mean rear lug tyre ground contact pressure
TRACTOR_WHEEL_WIDTH_M: float = 0.35            # 13.6-28 rear tyre width (approx 35 cm)
TRACTOR_CONTACT_LENGTH_M: float = 1.00         # Tyre ground contact patch length
MAX_TRACTOR_CHASSIS_SINKAGE_CM: float = 22.0   # Axle clearance bottom-out depth
SAFE_TILLING_DEPTH_CM: float = 5.0             # Safe nursery bed tilling depth (intact roots)
CRITICAL_TILLING_DEPTH_CM: float = 15.0        # Catastrophic rut depth (seed buried & root network torn)

# Paddy Tillage Infiltration Zone (Top 25 cm plough zone)
PADDY_TILLAGE_DEPTH_M: float = 0.25

# Paddy Nursery Bed Hydraulic Thresholds
PADDY_OPTIMAL_THETA_MIN: float = 0.28
PADDY_OPTIMAL_THETA_MAX: float = 0.38


@dataclass(frozen=True)
class PaddyNurseryState:
    """Hydraulic state of the paddy nursery bed (Tala Gachha)."""
    theta_bed: np.ndarray
    water_status_category: str     # DEFICIENT, OPTIMAL, SATURATED_ANOXIA
    anoxia_risk_pct: float
    mean_moisture: float


@dataclass(frozen=True)
class TractorSinkageState:
    """Geotechnical sinkage state of agricultural tractor during field preparation."""
    q_allow_kpa: np.ndarray
    rut_depth_cm: np.ndarray
    mean_rut_depth_cm: float
    max_rut_depth_cm: float
    mobility_status: str           # SMOOTH_TILLAGE, EXCESSIVE_SINKAGE, BOGGED_QUAGMIRE
    bogged_area_pct: float


@dataclass(frozen=True)
class CoupledSimulationResult:
    """Full cross-domain agro-geotechnical simulation outcome."""
    paddy_state: PaddyNurseryState
    tractor_state: TractorSinkageState
    seedling_damage_index: np.ndarray      # Continuous 0.0 (Safe) to 1.0 (Severely Ruptured)
    mean_seedling_damage_index: float
    safe_nursery_area_pct: float
    damaged_nursery_area_pct: float
    water_applied_mm: float
    tractor_contact_pressure_kpa: float
    recommended_optimal_water_mm: float
    farmer_advisory_text: str
    execution_time_ms: float


@dataclass(frozen=True)
class MonteCarloCoupledResult:
    """Precursor Monte Carlo stress-testing benchmark telemetry for Day 18."""
    num_trials: int
    tractor_bogged_probability: float
    seedling_damage_probability: float
    mean_rut_depth_distribution_cm: np.ndarray
    mean_damage_distribution: np.ndarray
    optimal_water_ci_95: Tuple[float, float]
    execution_time_ms: float
    latency_per_trial_ms: float


class CoupledAgroCivilSimulator:
    """
    Simulates real-world dynamic coupling between Agricultural Crop Biology (Paddy Nursery Bed)
    and Civil Soil Mechanics (Tractor Wheel Sinkage & Bearing Capacity).
    """

    def __init__(
        self,
        soil_engine: Optional[SoilMechanicsCoreEngine] = None,
        stability_engine: Optional[GroundStabilityEngine] = None,
        slope_engine: Optional[SlopeStabilityEngine] = None,
    ):
        self.soil_engine = soil_engine or SoilMechanicsCoreEngine()
        # Initialize dedicated tractor surface-wheel footing (B=0.35m, Df=0.0m surface contact, FS=1.5)
        self.stability_engine = stability_engine or GroundStabilityEngine(
            soil_engine=self.soil_engine,
            target_factor_of_safety=1.5,
            footing_width_b_m=TRACTOR_WHEEL_WIDTH_M,
            footing_length_l_m=TRACTOR_CONTACT_LENGTH_M,
            embedment_depth_df_m=0.0,
        )
        self.slope_engine = slope_engine or SlopeStabilityEngine(self.soil_engine)

    def compute_tractor_sinkage(
        self,
        q_allow_kpa: np.ndarray,
        q_contact_kpa: float = DEFAULT_TRACTOR_PRESSURE_KPA,
    ) -> np.ndarray:
        """
        Calculates tractor tyre rut sinkage depth in centimeters using the Bekker-Meyerhof formulation:
        z_rut = z_base + (z_max - z_base) * max(0, 1.0 - q_allow / q_contact)^0.85
        When allowable bearing capacity >= contact pressure, sinkage is minimal (1.5 cm elastic tyre track).
        When allowable bearing drops below contact pressure, sinkage escalates up to z_max (22.0 cm).
        """
        q_allow = np.asarray(q_allow_kpa, dtype=np.float64)
        
        # Relative bearing deficit ratio
        deficit = np.maximum(0.0, 1.0 - (q_allow / float(q_contact_kpa)))
        
        # Non-linear wheel rut depth in centimeters
        rut_depth_cm = 1.5 + (MAX_TRACTOR_CHASSIS_SINKAGE_CM - 1.5) * np.power(deficit, 0.85)
        
        return np.clip(rut_depth_cm, 1.0, MAX_TRACTOR_CHASSIS_SINKAGE_CM)

    def compute_seedling_damage(self, rut_depth_cm: np.ndarray) -> np.ndarray:
        """
        Calculates Seedling Damage Index (SDI) in [0.0, 1.0]:
        - z_rut <= 5.0 cm: SDI = 0.0 (Safe rootbed, seedling intact)
        - 5.0 cm < z_rut < 15.0 cm: SDI linearly ramps from 0.0 to 1.0 (Root tearing & burial)
        - z_rut >= 15.0 cm: SDI = 1.0 (Catastrophic nursery inversion)
        """
        z = np.asarray(rut_depth_cm, dtype=np.float64)
        sdi = np.clip(
            (z - SAFE_TILLING_DEPTH_CM) / (CRITICAL_TILLING_DEPTH_CM - SAFE_TILLING_DEPTH_CM),
            0.0,
            1.0,
        )
        return sdi

    def find_goldilocks_optimal_water(
        self,
        theta_initial: np.ndarray,
        q_contact_kpa: float = DEFAULT_TRACTOR_PRESSURE_KPA,
        soil_class: str = "silt_loam",
    ) -> float:
        """
        Optimizes irrigation depth (mm) to achieve optimal nursery moisture without causing
        tractor sinkage > SAFE_TILLING_DEPTH_CM.
        Scans water increments from 10mm to 80mm.
        """
        params = self.soil_engine.get_parameters(soil_class)
        theta_arr = np.asarray(theta_initial, dtype=np.float64)
        
        best_water_mm = 25.0
        min_penalty = 1e9

        for test_water_mm in np.linspace(10.0, 80.0, 29):
            # Infiltration into 25cm tillage root zone
            d_theta = (test_water_mm * 0.90) / (PADDY_TILLAGE_DEPTH_M * 1000.0)
            theta_sim = np.clip(theta_arr + d_theta, params.theta_res + 1e-4, params.theta_sat - 1e-4)

            # Surface bearing with puddling remolding effect
            bearing = self.stability_engine.compute_bearing_capacity(theta_sim, soil_class, overburden_surcharge_kpa=0.0)
            remold_factor = np.clip(1.0 - np.power(theta_sim / params.theta_sat, 3.0), 0.08, 1.0)
            q_effective = bearing.q_allow_kpa * remold_factor

            rut_cm = self.compute_tractor_sinkage(q_effective, q_contact_kpa)
            mean_rut = float(np.mean(rut_cm))

            # Penalty: deviation from optimal moisture range [0.28, 0.36] + heavy penalty if rut > 5.0 cm
            mean_theta = float(np.mean(theta_sim))
            moisture_penalty = max(0.0, PADDY_OPTIMAL_THETA_MIN - mean_theta) * 100.0 + max(0.0, mean_theta - PADDY_OPTIMAL_THETA_MAX) * 100.0
            rut_penalty = max(0.0, mean_rut - SAFE_TILLING_DEPTH_CM) * 50.0

            total_penalty = moisture_penalty + rut_penalty
            if total_penalty < min_penalty:
                min_penalty = total_penalty
                best_water_mm = float(test_water_mm)

        return best_water_mm

    def simulate_paddy_tilling(
        self,
        theta_initial: np.ndarray,
        slope_deg: np.ndarray,
        water_applied_mm: float = 35.0,
        tractor_contact_pressure_kpa: float = DEFAULT_TRACTOR_PRESSURE_KPA,
        soil_class: str = "silt_loam",
    ) -> CoupledSimulationResult:
        """
        Executes coupled cross-domain simulation:
        1. Infiltration of applied water into 25 cm tillage root zone.
        2. Soil mechanics degradation of allowable bearing capacity + puddling remolding.
        3. Non-linear tractor rut depth sinkage.
        4. Seedling damage and root tearing evaluation.
        5. Optimal water depth recommendation and human farmer advisory bulletin.
        """
        t0 = time.perf_counter()
        theta_arr = np.asarray(theta_initial, dtype=np.float64)
        params = self.soil_engine.get_parameters(soil_class)

        # 1. Paddy Nursery Water Infiltration (Tillage zone Z = 0.25 m)
        d_theta = (water_applied_mm * 0.90) / (PADDY_TILLAGE_DEPTH_M * 1000.0)
        theta_bed = np.clip(theta_arr + d_theta, params.theta_res + 1e-4, params.theta_sat - 1e-4)

        mean_moisture = float(np.mean(theta_bed))
        anoxia_mask = theta_bed >= (params.theta_sat - 0.02)
        anoxia_pct = float(np.sum(anoxia_mask) / theta_bed.size * 100.0)

        if mean_moisture < PADDY_OPTIMAL_THETA_MIN:
            water_status = "DEFICIENT"
        elif mean_moisture > (params.theta_sat - 0.03):
            water_status = "SATURATED_ANOXIA"
        else:
            water_status = "OPTIMAL"

        paddy_state = PaddyNurseryState(
            theta_bed=theta_bed.astype(np.float32),
            water_status_category=water_status,
            anoxia_risk_pct=anoxia_pct,
            mean_moisture=mean_moisture,
        )

        # 2. Civil Ground Bearing & Puddling Slurry Remolding
        bearing = self.stability_engine.compute_bearing_capacity(theta_bed, soil_class, overburden_surcharge_kpa=0.0)
        remold_factor = np.clip(1.0 - np.power(theta_bed / params.theta_sat, 3.0), 0.08, 1.0)
        q_effective = bearing.q_allow_kpa * remold_factor

        rut_cm = self.compute_tractor_sinkage(q_effective, tractor_contact_pressure_kpa)
        
        mean_rut = float(np.mean(rut_cm))
        max_rut = float(np.max(rut_cm))
        bogged_mask = rut_cm >= 10.0
        bogged_pct = float(np.sum(bogged_mask) / rut_cm.size * 100.0)

        if mean_rut <= SAFE_TILLING_DEPTH_CM:
            mobility_status = "SMOOTH_TILLAGE"
        elif mean_rut <= 10.0:
            mobility_status = "EXCESSIVE_SINKAGE"
        else:
            mobility_status = "BOGGED_QUAGMIRE"

        tractor_state = TractorSinkageState(
            q_allow_kpa=q_effective.astype(np.float32),
            rut_depth_cm=rut_cm.astype(np.float32),
            mean_rut_depth_cm=mean_rut,
            max_rut_depth_cm=max_rut,
            mobility_status=mobility_status,
            bogged_area_pct=bogged_pct,
        )

        # 3. Seedling Damage Index
        sdi = self.compute_seedling_damage(rut_cm)
        mean_sdi = float(np.mean(sdi))
        safe_area_pct = float(np.sum(sdi <= 0.10) / sdi.size * 100.0)
        damaged_area_pct = float(np.sum(sdi >= 0.50) / sdi.size * 100.0)

        # 4. Goldilocks Optimal Irrigation Recommendation
        optimal_water_mm = self.find_goldilocks_optimal_water(
            theta_arr, tractor_contact_pressure_kpa, soil_class
        )

        # 5. Natural Language Farmer Advisory Bulletin (Simple, Grassroots Language)
        if mean_rut > SAFE_TILLING_DEPTH_CM:
            warning_msg = (
                f"[KHATRA] {water_applied_mm:.0f}mm paani zyada hai! Mitti kado banne se tractor "
                f"{mean_rut:.1f} cm gehra dhas raha hai (Safe limit <= 5cm), jisse {damaged_area_pct:.1f}% chare ki jadhein toot jayengi! "
                f"SALAHA: Paani kam karke exactly {optimal_water_mm:.0f}mm karein taaki tractor smooth joti kare aur beej 100% surakshit uge."
            )
        else:
            warning_msg = (
                f"[SHABHASH] {water_applied_mm:.0f}mm paani bilkul sahi hai! Tractor sirf {mean_rut:.1f} cm "
                f"dhasega (Safe limit <= 5cm). Nursery bed me 100% tandurast chara ugega aur jadhein safe rahengi."
            )

        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000.0

        return CoupledSimulationResult(
            paddy_state=paddy_state,
            tractor_state=tractor_state,
            seedling_damage_index=sdi.astype(np.float32),
            mean_seedling_damage_index=mean_sdi,
            safe_nursery_area_pct=safe_area_pct,
            damaged_nursery_area_pct=damaged_area_pct,
            water_applied_mm=float(water_applied_mm),
            tractor_contact_pressure_kpa=float(tractor_contact_pressure_kpa),
            recommended_optimal_water_mm=float(optimal_water_mm),
            farmer_advisory_text=warning_msg,
            execution_time_ms=elapsed_ms,
        )

    def run_monte_carlo_stress_test(
        self,
        theta_initial: np.ndarray,
        slope_deg: np.ndarray,
        num_trials: int = 50,
        water_nominal_mm: float = 40.0,
        soil_class: str = "silt_loam",
    ) -> MonteCarloCoupledResult:
        """
        Executes high-speed vectorized Monte Carlo stochastic perturbation trials:
        Precursor to Day 18's 1,000 Monte Carlo campaign.
        Perturbs water applied ~ N(water_nominal, 10mm^2),
        Perturbs tractor contact pressure ~ U(120, 160 kPa),
        Perturbs soil moisture with AETHER uncertainty.
        Computes probabilistic risk of tractor sinkage and seedling damage.
        """
        t0 = time.perf_counter()
        rng = np.random.default_rng(seed=42)

        theta_base = np.asarray(theta_initial, dtype=np.float64)
        
        rut_depths = np.zeros(num_trials, dtype=np.float64)
        damage_indices = np.zeros(num_trials, dtype=np.float64)
        optimal_waters = np.zeros(num_trials, dtype=np.float64)
        bogged_counts = 0
        damage_counts = 0

        for trial in range(num_trials):
            # Stochastic perturbations
            p_water = float(rng.normal(loc=water_nominal_mm, scale=14.0))
            p_water = max(10.0, min(80.0, p_water))
            p_pressure = float(rng.uniform(120.0, 160.0))
            p_theta_noise = rng.normal(0.0, 0.015, size=theta_base.shape)
            trial_theta = np.clip(theta_base + p_theta_noise, 0.08, 0.45)

            # Execute simulation
            res = self.simulate_paddy_tilling(
                theta_initial=trial_theta,
                slope_deg=slope_deg,
                water_applied_mm=p_water,
                tractor_contact_pressure_kpa=p_pressure,
                soil_class=soil_class,
            )

            rut_depths[trial] = res.tractor_state.mean_rut_depth_cm
            damage_indices[trial] = res.mean_seedling_damage_index
            optimal_waters[trial] = res.recommended_optimal_water_mm

            if res.tractor_state.mean_rut_depth_cm >= 8.0:
                bogged_counts += 1
            if res.mean_seedling_damage_index >= 0.30:
                damage_counts += 1

        t1 = time.perf_counter()
        total_time_ms = (t1 - t0) * 1000.0

        p_bogged = float(bogged_counts / num_trials)
        p_damage = float(damage_counts / num_trials)
        ci_lower = float(np.percentile(optimal_waters, 2.5))
        ci_upper = float(np.percentile(optimal_waters, 97.5))

        return MonteCarloCoupledResult(
            num_trials=num_trials,
            tractor_bogged_probability=p_bogged,
            seedling_damage_probability=p_damage,
            mean_rut_depth_distribution_cm=rut_depths.astype(np.float32),
            mean_damage_distribution=damage_indices.astype(np.float32),
            optimal_water_ci_95=(ci_lower, ci_upper),
            execution_time_ms=total_time_ms,
            latency_per_trial_ms=total_time_ms / float(num_trials),
        )
