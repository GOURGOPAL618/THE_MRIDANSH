# THE MRIDANSH - UNIFIED PHYSICS CORE & DOMAIN TRANSLATORS
# Module: 4_domain_translators/temporal_hydrodynamics.py
# Subsystem 07: Temporal Hydrodynamic Continuity Engine
# Architecture: Continuous Vadose Evaporative Drying, Hydraulic Drainage & SAR Multi-Temporal Anomaly Fusion
# Standards: FAO-56 / Van Genuchten Vadose Hydraulics / WMO-No. 168 / RTCA DO-178C Level-A
# Lead Systems Architect: Gouragopal Mohapatra (JCC Campus 2, RS-SDA Division)

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger("MRIDANSH.TemporalHydrodynamics")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


# ======================================================================================================================
# CONSTANTS & PHYSICAL COEFFICIENTS
# ======================================================================================================================

# Active Soil Vadose / Root Zone Depth (Default 25 cm = 0.25 m for shallow tillage & seedbed)
DEFAULT_ACTIVE_DEPTH_M: float = 0.25

# Physical Hydraulic Limits for Loam / Clay-Loam (FAO-56 & USDA Standard)
DEFAULT_THETA_RESIDUAL: float = 0.05    # Residual non-extractable moisture (m3/m3)
DEFAULT_THETA_WILTING: float = 0.12     # Permanent wilting point at -1500 kPa (m3/m3)
DEFAULT_THETA_FIELD_CAPACITY: float = 0.33  # Field capacity at -33 kPa (m3/m3)
DEFAULT_THETA_SATURATION: float = 0.48  # Total porosity / saturated limit at 0 kPa (m3/m3)

# Hydraulic Percolation Parameters
DEFAULT_K_SAT_MM_DAY: float = 120.0     # Saturated hydraulic conductivity (mm/day)
DRAINAGE_TIMESCALE_TAU: float = 0.50    # Gravity drainage characteristic relaxation rate (1/day)

# Multi-Temporal SAR Anomaly Detection Thresholds (Sentinel-1 C-band VV, dB)
SAR_WETTING_ANOMALY_THRESHOLD_DB: float = 2.5      # Backscatter rise > +2.5 dB implies unrecorded irrigation/rain
SAR_DESICCATION_ANOMALY_THRESHOLD_DB: float = -2.0  # Backscatter drop < -2.0 dB implies rapid desiccation/harvest
SAR_SENSITIVITY_DB_PER_THETA: float = 35.0         # Empirical d(sigma0)/d(theta) in C-band VV (~35 dB / (m3/m3))


# ======================================================================================================================
# DATA STRUCTURES
# ======================================================================================================================

@dataclass(frozen=True)
class DailyWeatherForcing:
    """
    Atmospheric and hydrological surface forcing parameters for a 24-hour simulation interval.
    
    Fields:
      et0_mm_day: Reference evapotranspiration derived from Penman-Monteith / ERA5 (mm/day)
      precipitation_mm_day: Total daily precipitation depth (mm/day)
      t2m_celsius: Daily mean 2-meter surface air temperature (°C)
      wind_speed_ms: Daily mean 10-meter wind speed (m/s)
      relative_humidity_pct: Daily mean relative humidity (percent, 0-100)
      runoff_fraction_cn: Fraction of precipitation lost to immediate surface runoff [0.0, 1.0]
    """
    et0_mm_day: float = 4.0
    precipitation_mm_day: float = 0.0
    t2m_celsius: float = 28.0
    wind_speed_ms: float = 2.0
    relative_humidity_pct: float = 65.0
    runoff_fraction_cn: float = 0.15

    def __post_init__(self):
        if self.et0_mm_day < 0.0:
            raise ValueError(f"ET0 must be non-negative: {self.et0_mm_day}")
        if self.precipitation_mm_day < 0.0:
            raise ValueError(f"Precipitation must be non-negative: {self.precipitation_mm_day}")
        if not (0.0 <= self.runoff_fraction_cn <= 1.0):
            raise ValueError(f"Runoff fraction must be in [0.0, 1.0]: {self.runoff_fraction_cn}")


@dataclass(frozen=True)
class TemporalStepResult:
    """Telemetry result of a single daily hydrodynamic propagation step."""
    day_index: int
    theta: np.ndarray
    mean_theta: float
    min_theta: float
    max_theta: float
    et_actual_mm: float
    drainage_mm: float
    infiltrated_rain_mm: float
    stress_factor_ks: float
    monotonic_decrease: bool


@dataclass(frozen=True)
class TemporalTrajectory:
    """Full multi-day temporal moisture propagation trajectory bridging satellite revisit intervals."""
    daily_steps: List[TemporalStepResult]
    forecast_days: int
    anchor_mean_theta: float
    final_mean_theta: float
    net_water_loss_mm: float
    monotonicity_verified: bool
    execution_time_ms: float
    contract_verification: Dict[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class SARAnomalyResult:
    """Results of multi-temporal Sentinel-1 SAR change detection."""
    delta_sigma_db: np.ndarray
    anomaly_mask: np.ndarray          # -1 = Rapid Desiccation, 0 = Normal Drift, +1 = Wetting Surge
    anomaly_category: str             # NORMAL_HYDROLOGIC_DRIFT, WETTING_SURGE, RAPID_DESICCATION
    mean_delta_sigma_db: float
    wetting_pixels_pct: float
    desiccation_pixels_pct: float
    moisture_nudge_tensor: np.ndarray # Estimated delta theta (m3/m3) from SAR backscatter shift


# ======================================================================================================================
# CORE TEMPORAL HYDRODYNAMIC ENGINE
# ======================================================================================================================

class TemporalHydrodynamicEngine:
    """
    Subsystem 07: Temporal Hydrodynamic Continuity Engine.
    
    Bridges the 5-6 day satellite revisit gap by propagating vadose soil moisture
    using a continuous 1D Richards-bucket mass conservation model combined with
    multi-temporal SAR anomaly assimilation.
    
    Complies with RTCA DO-178C Level-A safety and real-time execution invariants.
    """

    def __init__(
        self,
        z_active_m: float = DEFAULT_ACTIVE_DEPTH_M,
        theta_res: float = DEFAULT_THETA_RESIDUAL,
        theta_wp: float = DEFAULT_THETA_WILTING,
        theta_fc: float = DEFAULT_THETA_FIELD_CAPACITY,
        theta_sat: float = DEFAULT_THETA_SATURATION,
        k_sat_mm_day: float = DEFAULT_K_SAT_MM_DAY,
        kc_crop: float = 1.05,
    ) -> None:
        """
        Initialize the Temporal Hydrodynamic Engine with physical boundaries.
        
        Args:
            z_active_m: Active vadose layer thickness in meters (default 0.25 m).
            theta_res: Residual non-extractable moisture fraction (m3/m3).
            theta_wp: Permanent wilting point (-1500 kPa).
            theta_fc: Field capacity (-33 kPa).
            theta_sat: Total porosity / saturated limit (0 kPa).
            k_sat_mm_day: Saturated hydraulic conductivity (mm/day).
            kc_crop: Nominal crop transpiration coefficient (default 1.05).
        """
        # Physical boundary ordering invariant
        if not (0.0 <= theta_res <= theta_wp < theta_fc < theta_sat <= 1.0):
            raise ValueError(
                f"Physical ordering violation: theta_res ({theta_res}) <= "
                f"theta_wp ({theta_wp}) < theta_fc ({theta_fc}) < theta_sat ({theta_sat})"
            )
        if z_active_m <= 0.0:
            raise ValueError(f"Active soil layer depth must be positive: {z_active_m}")

        self.z_active_m: float = float(z_active_m)
        self.theta_res: float = float(theta_res)
        self.theta_wp: float = float(theta_wp)
        self.theta_fc: float = float(theta_fc)
        self.theta_sat: float = float(theta_sat)
        self.k_sat_mm_day: float = float(k_sat_mm_day)
        self.kc_crop: float = float(kc_crop)

    def calculate_ks_stress(self, theta: np.ndarray) -> np.ndarray:
        """
        Compute FAO-56 soil water stress coefficient Ks in [0.0, 1.0].
        
        Ks = 1.0 for theta >= theta_fc (Unrestricted transpiration)
        Ks = (theta - theta_wp) / (theta_fc - theta_wp) for theta_wp < theta < theta_fc
        Ks = 0.0 for theta <= theta_wp (Complete stomatal closure / wilting)
        """
        denominator = max(self.theta_fc - self.theta_wp, 1e-6)
        ks = (theta - self.theta_wp) / denominator
        return np.clip(ks, 0.0, 1.0)

    def propagate_step(
        self,
        theta_curr: np.ndarray,
        weather: DailyWeatherForcing,
        dt_days: float = 1.0,
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Propagate soil moisture tensor forward by dt_days under given weather forcing.
        
        Governing Differential Water Balance:
            d(theta)/dt = [ P_inf(t) - (ET_actual(t) + D_deep(t)) ] / (1000 * Z_active)
        
        Args:
            theta_curr: Current volumetric soil moisture tensor (m3/m3).
            weather: Daily atmospheric surface forcing.
            dt_days: Simulation timestep in days (default 1.0 day).
            
        Returns:
            Tuple of (theta_next tensor, step_metrics dict).
        """
        if dt_days <= 0.0:
            raise ValueError(f"Timestep dt_days must be positive: {dt_days}")
        
        # Verify input tensor integrity
        if np.any(np.isnan(theta_curr)) or np.any(np.isinf(theta_curr)):
            raise FloatingPointError("Input soil moisture contains NaN or Infinite values.")

        theta_arr = np.asarray(theta_curr, dtype=np.float32)
        reservoir_depth_mm = self.z_active_m * 1000.0  # e.g., 250 mm for 0.25 m

        # 1. FAO-56 Actual Evapotranspiration Flux (ET_actual in mm/day)
        ks = self.calculate_ks_stress(theta_arr)
        et_actual_rate = ks * self.kc_crop * weather.et0_mm_day  # mm/day
        et_actual_depth = et_actual_rate * dt_days               # mm

        # 2. Gravitational Vadose Percolation (D_deep in mm/day)
        # When moisture exceeds field capacity, gravity drains excess water
        excess_theta = np.maximum(0.0, theta_arr - self.theta_fc)
        drainage_rate = DRAINAGE_TIMESCALE_TAU * excess_theta * reservoir_depth_mm  # mm/day
        drainage_depth = drainage_rate * dt_days                                    # mm

        # 3. Infiltrated Precipitation Flux (P_inf in mm/day)
        # Infiltration accounts for immediate surface runoff fraction (1 - CN)
        p_infiltrated_depth = (weather.precipitation_mm_day * (1.0 - weather.runoff_fraction_cn)) * dt_days

        # Net water depth exchange in mm (+ve = recharge, -ve = depletion)
        net_water_exchange_mm = p_infiltrated_depth - (et_actual_depth + drainage_depth)

        # Convert net water depth (mm) to volumetric moisture increment (m3/m3)
        delta_theta = net_water_exchange_mm / reservoir_depth_mm

        # Update and strictly clamp to physical boundaries (Mass Conservation Invariant)
        theta_next = theta_arr + delta_theta
        theta_next = np.clip(theta_next, self.theta_res, self.theta_sat)

        # DO-178C Invariant: Strict Monotonicity under Dry Weather (P = 0)
        # If precipitation is zero and ET0 > 0, moisture must strictly not increase.
        monotonic_decrease = True
        if weather.precipitation_mm_day == 0.0 and weather.et0_mm_day > 0.0:
            # Floating point tolerance 1e-6
            max_drift = np.max(theta_next - theta_arr)
            if max_drift > 1e-6:
                monotonic_decrease = False

        metrics: Dict[str, float] = {
            "mean_theta": float(np.mean(theta_next)),
            "min_theta": float(np.min(theta_next)),
            "max_theta": float(np.max(theta_next)),
            "et_actual_mm": float(np.mean(et_actual_depth)),
            "drainage_mm": float(np.mean(drainage_depth)),
            "infiltrated_rain_mm": float(p_infiltrated_depth),
            "stress_factor_ks": float(np.mean(ks)),
            "monotonic_decrease": float(1.0 if monotonic_decrease else 0.0),
        }

        return theta_next, metrics

    def forecast_trajectory(
        self,
        theta_anchor: np.ndarray,
        weather_schedule: List[DailyWeatherForcing],
    ) -> TemporalTrajectory:
        """
        Propagate soil moisture across a multi-day forecast sequence.
        
        Args:
            theta_anchor: Spaceborne soil moisture tensor at anchor overpass date.
            weather_schedule: List of DailyWeatherForcing for each day of the forecast.
            
        Returns:
            TemporalTrajectory with daily states, telemetry, and DO-178C audit.
        """
        t_start = time.perf_counter()

        if not weather_schedule:
            raise ValueError("weather_schedule list cannot be empty.")

        theta_current = np.copy(theta_anchor)
        anchor_mean = float(np.mean(theta_current))
        daily_steps: List[TemporalStepResult] = []
        overall_monotonicity = True

        for day_idx, weather in enumerate(weather_schedule, start=1):
            theta_next, metrics = self.propagate_step(theta_current, weather, dt_days=1.0)
            
            step_result = TemporalStepResult(
                day_index=day_idx,
                theta=theta_next,
                mean_theta=metrics["mean_theta"],
                min_theta=metrics["min_theta"],
                max_theta=metrics["max_theta"],
                et_actual_mm=metrics["et_actual_mm"],
                drainage_mm=metrics["drainage_mm"],
                infiltrated_rain_mm=metrics["infiltrated_rain_mm"],
                stress_factor_ks=metrics["stress_factor_ks"],
                monotonic_decrease=bool(metrics["monotonic_decrease"] > 0.5),
            )
            daily_steps.append(step_result)

            if weather.precipitation_mm_day == 0.0 and not step_result.monotonic_decrease:
                overall_monotonicity = False

            theta_current = theta_next

        t_elapsed_ms = (time.perf_counter() - t_start) * 1000.0
        final_mean = float(np.mean(theta_current))
        net_loss_mm = (anchor_mean - final_mean) * self.z_active_m * 1000.0

        # Run DO-178C Contract Checks
        contracts = self._verify_contracts(theta_anchor, daily_steps, weather_schedule, t_elapsed_ms)

        return TemporalTrajectory(
            daily_steps=daily_steps,
            forecast_days=len(weather_schedule),
            anchor_mean_theta=anchor_mean,
            final_mean_theta=final_mean,
            net_water_loss_mm=net_loss_mm,
            monotonicity_verified=overall_monotonicity,
            execution_time_ms=t_elapsed_ms,
            contract_verification=contracts,
        )

    def detect_sar_anomaly(
        self,
        sigma_anchor_db: np.ndarray,
        sigma_current_db: np.ndarray,
    ) -> SARAnomalyResult:
        """
        Multi-temporal Sentinel-1 C-band SAR change detection and anomaly classification.
        
        Compares backscatter at current overpass against the anchor date.
        Flags unmodeled flooding/irrigation surges or catastrophic crop desiccation.
        
        Args:
            sigma_anchor_db: Backscatter array at previous pass (dB).
            sigma_current_db: Backscatter array at current pass (dB).
            
        Returns:
            SARAnomalyResult with delta sigma array, masks, and soil moisture nudge.
        """
        if sigma_anchor_db.shape != sigma_current_db.shape:
            raise ValueError(
                f"Shape mismatch in SAR anomaly detection: anchor {sigma_anchor_db.shape} "
                f"vs current {sigma_current_db.shape}"
            )

        delta_sigma = sigma_current_db - sigma_anchor_db

        # Anomaly Mask: +1 = Wetting surge, -1 = Rapid Desiccation, 0 = Normal drift
        anomaly_mask = np.zeros_like(delta_sigma, dtype=np.int32)
        wetting_mask = delta_sigma > SAR_WETTING_ANOMALY_THRESHOLD_DB
        desiccation_mask = delta_sigma < SAR_DESICCATION_ANOMALY_THRESHOLD_DB

        anomaly_mask[wetting_mask] = 1
        anomaly_mask[desiccation_mask] = -1

        total_pixels = float(delta_sigma.size)
        wetting_pct = (float(np.sum(wetting_mask)) / total_pixels) * 100.0
        desiccation_pct = (float(np.sum(desiccation_mask)) / total_pixels) * 100.0
        mean_delta = float(np.mean(delta_sigma))

        # Overall Category
        if wetting_pct > 15.0:
            category = "WETTING_SURGE_DETECTED"
        elif desiccation_pct > 15.0:
            category = "RAPID_DESICCATION_DETECTED"
        else:
            category = "NORMAL_HYDROLOGIC_DRIFT"

        # Estimated delta moisture nudge from radar sensitivity
        # Delta theta ~ Delta sigma (dB) / (d(sigma)/d(theta))
        moisture_nudge = delta_sigma / SAR_SENSITIVITY_DB_PER_THETA
        moisture_nudge = np.clip(moisture_nudge, -0.15, +0.15)

        return SARAnomalyResult(
            delta_sigma_db=delta_sigma,
            anomaly_mask=anomaly_mask,
            anomaly_category=category,
            mean_delta_sigma_db=mean_delta,
            wetting_pixels_pct=wetting_pct,
            desiccation_pixels_pct=desiccation_pct,
            moisture_nudge_tensor=moisture_nudge,
        )

    def _verify_contracts(
        self,
        theta_anchor: np.ndarray,
        daily_steps: List[TemporalStepResult],
        weather_schedule: List[DailyWeatherForcing],
        execution_time_ms: float,
    ) -> Dict[str, bool]:
        """Verify DO-178C Level-A safety invariants across trajectory."""
        contracts: Dict[str, bool] = {}

        # 1. Finite numbers check (PIPE-03 invariant)
        all_finite = True
        for step in daily_steps:
            if not np.all(np.isfinite(step.theta)):
                all_finite = False
                break
        contracts["PIPE_FINITE_NUMBERS"] = all_finite

        # 2. Vadose Mass Conservation Bounds (PIPE-02 invariant)
        bounds_satisfied = True
        for step in daily_steps:
            if np.any(step.theta < (self.theta_res - 1e-5)) or np.any(step.theta > (self.theta_sat + 1e-5)):
                bounds_satisfied = False
                break
        contracts["PIPE_MASS_CONSERVATION_BOUNDS"] = bounds_satisfied

        # 3. Monotonicity under Dry Days (PIPE-01 invariant)
        monotonic_ok = True
        prev_theta = theta_anchor
        for step, weather in zip(daily_steps, weather_schedule):
            if weather.precipitation_mm_day == 0.0 and weather.et0_mm_day > 0.0:
                if np.any(step.theta > (prev_theta + 1e-6)):
                    monotonic_ok = False
                    break
            prev_theta = step.theta
        contracts["PIPE_MONOTONIC_DRYING"] = monotonic_ok

        # 4. Latency SLA (< 0.010 ms/pixel for standalone propagator)
        pixel_count = theta_anchor.size
        latency_per_pixel_ms = execution_time_ms / max(pixel_count, 1)
        contracts["PIPE_LATENCY_SLA"] = bool(latency_per_pixel_ms < 0.010)

        return contracts
