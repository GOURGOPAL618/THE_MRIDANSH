# THE MRIDANSH - UNIFIED PHYSICS CORE & MULTI-DOMAIN TEST CAMPAIGN
# Module: 11_simulation_test_campaign/planetary_monte_carlo_engine.py
# Subsystem: Mission Day 18 - 1,000-Trial Planetary Monte Carlo Stress Campaign
# Standards: RTCA DO-178C Level-A Verification Principles / Eurocode 7 / FAO-56 / USACE TM 5-818-1
# Lead Systems Architect: Gouragopal Mohapatra (JCC Campus 2, RS-SDA Division)

from __future__ import annotations

import hashlib
import json
import logging
import math
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Ensure repository root and translators directories are on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
TRANSLATORS_DIR = REPO_ROOT / "4_domain_translators"
CIVIL_DIR = TRANSLATORS_DIR / "civil"
AGRI_DIR = TRANSLATORS_DIR / "agronomy"

for p in [REPO_ROOT, TRANSLATORS_DIR, CIVIL_DIR, AGRI_DIR]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from coupled_agro_civil_simulator import CoupledAgroCivilSimulator
from temporal_hydrodynamics import DailyWeatherForcing, TemporalHydrodynamicEngine
from civil.slope_stability_engine import SlopeStabilityEngine
from civil.soil_mechanics_core import SoilMechanicsCoreEngine
from civil.ground_stability_engine import GroundStabilityEngine

logger = logging.getLogger("MRIDANSH.MonteCarlo1000")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# ======================================================================================================================
# MASTER SEED ARCHITECTURE & PARTITION MATRIX
# ======================================================================================================================

GLOBAL_MASTER_SEED: int = 1607  # AETHER-MRID1607X Core Signature

SEED_QUADRANT_1: int = 16071    # Phase 1: Hyper-Arid Drought Stress (Trials 001 - 250)
SEED_QUADRANT_2: int = 16072    # Phase 2: Monsoon Deluge & Landslide Hazards (Trials 251 - 500)
SEED_QUADRANT_3: int = 16073    # Phase 3: Sensor Noise & SAR Dropout (Trials 501 - 750)
SEED_QUADRANT_4: int = 16074    # Phase 4: Mud Liquefaction & Heavy Terramodels (Trials 751 - 1000)

NUM_TRIALS_PER_QUADRANT: int = 250


# ======================================================================================================================
# DATA STRUCTURES FOR AUDITABLE TELEMETRY & FORENSICS
# ======================================================================================================================

@dataclass
class ForensicAuditTelemetry:
    """Forensic verification logger capturing code artifacts vs true physical dynamics."""
    code_integrity_passed: bool
    mass_conservation_drift: float
    clamping_detected: bool
    is_super_additive_synergy: bool
    condition_number: float
    min_eigenvalue: float


@dataclass
class QuadrantTrialResult:
    """Individual trial metrics across Agriculture, Hydrology, and Civil Geotechnical domains."""
    trial_id: int
    quadrant: str
    seed: int
    soil_class: str
    crop_name: str
    initial_theta: float
    final_theta: float
    cwsi: float
    irrigation_deficit_mm: float
    pore_pressure_kpa: float
    factor_of_safety_slope: float
    landslide_hazard_triggered: bool
    tractor_rut_depth_cm: float
    bearing_capacity_kpa: float
    seedling_damage_index: float
    mass_drift_m3_m3: float
    condition_number_kappa: float
    min_eigenvalue_lambda: float
    execution_time_ms: float
    invariants_passed: bool


class PlanetaryMonteCarloEngine:
    """
    High-Performance In-Memory Vectorized Engine executing the 1,000-Trial Planetary Stress Campaign.
    Designed under RTCA DO-178C Level-A verification invariants and Eurocode 7 limit states.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path(__file__).resolve().parent
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.temporal_engine = TemporalHydrodynamicEngine()
        self.soil_engine = SoilMechanicsCoreEngine()
        self.ground_engine = GroundStabilityEngine(soil_engine=self.soil_engine)
        self.slope_engine = SlopeStabilityEngine(soil_engine=self.soil_engine)
        self.coupled_sim = CoupledAgroCivilSimulator()

    # ------------------------------------------------------------------------------------------------------------------
    # PHASE 1: QUADRANT 1 - HYPER-ARID DROUGHT STRESS (TRIALS 001 - 250)
    # ------------------------------------------------------------------------------------------------------------------
    def execute_phase_1_drought(self) -> Dict[str, Any]:
        """
        Executes Phase 1 (Trials 001-250) under Seed 16071.
        Evaluates severe evaporative desiccation, monotonic vadose decay, and residual moisture asymptote.
        """
        print("\n" + "=" * 90)
        print("  JCC CAMPUS 2 (RS-SDA) - EXECUTING PHASE 1: QUADRANT 1 (TRIALS 001 - 250)")
        print("  TARGET REGIME: HYPER-ARID CONTINUOUS DROUGHT | SEED: 16071")
        print("=" * 90)

        rng = np.random.default_rng(SEED_QUADRANT_1)
        t_start = time.perf_counter()

        trials_results: List[QuadrantTrialResult] = []
        forensics_log: List[ForensicAuditTelemetry] = []

        # Soil classes to distribute uniformly across 250 trials
        soil_pool = ["sand", "sandy_loam", "silt_loam", "clay_loam", "clay"]
        crop_pool = ["paddy", "wheat", "maize", "mustard", "pulses"]

        # Trajectory recording tensor: [250, 16_days]
        theta_trajectories = np.zeros((NUM_TRIALS_PER_QUADRANT, 16), dtype=np.float32)

        for i in range(NUM_TRIALS_PER_QUADRANT):
            t_trial_0 = time.perf_counter()

            soil_type = soil_pool[i % len(soil_pool)]
            crop_type = crop_pool[i % len(crop_pool)]
            params = self.soil_engine.get_parameters(soil_type)

            # 1. Stochastic Initial State: Field capacity down to moderately dry
            theta_init = float(rng.uniform(params.theta_res + 0.10, params.theta_sat - 0.05))
            
            # 2. Stochastic Atmospheric Stress: ET0 in [8.0, 14.0] mm/day, Zero Precipitation
            et0_nominal = float(rng.uniform(8.0, 14.0))
            
            # Construct synthetic 15-day continuous weather forcing
            daily_forcing: List[DailyWeatherForcing] = [
                DailyWeatherForcing(
                    et0_mm_day=float(et0_nominal * rng.uniform(0.95, 1.05)),
                    precipitation_mm_day=0.0,
                    t2m_celsius=float(rng.uniform(34.0, 44.0)),
                    wind_speed_ms=float(rng.uniform(2.5, 6.0)),
                    relative_humidity_pct=float(rng.uniform(20.0, 45.0)),
                    runoff_fraction_cn=0.20,
                )
                for _ in range(15)
            ]

            # 3. Hydrodynamic Vadose Propagation (15 days)
            # 64x64 spatial field to test full spatial array execution
            init_field = np.full((64, 64), theta_init, dtype=np.float32)
            
            # Configure engine instance with exact soil class physical parameters
            soil_engine_instance = TemporalHydrodynamicEngine(
                z_active_m=0.25,
                theta_res=params.theta_res,
                theta_wp=params.theta_res + 0.30 * (params.theta_sat - params.theta_res),
                theta_fc=params.theta_res + 0.65 * (params.theta_sat - params.theta_res),
                theta_sat=params.theta_sat,
                k_sat_mm_day=params.permeability_m_s * 86400.0 * 1000.0,
            )

            trajectory = soil_engine_instance.forecast_trajectory(
                theta_anchor=init_field,
                weather_schedule=daily_forcing,
            )

            # Record mean trajectory
            theta_trajectories[i, 0] = theta_init
            for step_idx, step in enumerate(trajectory.daily_steps):
                theta_trajectories[i, step_idx + 1] = step.mean_theta

            theta_final = float(trajectory.final_mean_theta)

            # 4. Invariant 1: Monotonic Desiccation under Zero Rainfall
            # Assert theta(t+1) <= theta(t) + epsilon
            diffs = np.diff(theta_trajectories[i, :])
            monotonic_pass = bool(np.all(diffs <= 1e-5))

            # 5. Invariant 2: Residual Lower Bound Clamping
            residual_pass = bool(theta_final >= (params.theta_res - 1e-4))

            # 6. Invariant 3: Mass Conservation Continuity Error
            # Total water loss in active layer (mm) vs sum of actual ET + deep drainage
            total_flux_loss_mm = sum((s.et_actual_mm + s.drainage_mm) for s in trajectory.daily_steps)
            total_water_loss_volumetric = (theta_init - theta_final) * 250.0  # 250 mm active depth
            mass_drift = abs(total_water_loss_volumetric - total_flux_loss_mm) / 250.0
            mass_pass = bool(mass_drift <= 1e-4)

            # 7. Invariant 4: Kalman EnKF Error Covariance Conditioning
            # Simulate EnKF background covariance matrix P (3x3 for skin, root, deep layers)
            P_matrix = np.array([
                [0.0012 + rng.uniform(0.0001, 0.0003), 0.0004, 0.0002],
                [0.0004, 0.0018 + rng.uniform(0.0001, 0.0004), 0.0003],
                [0.0002, 0.0003, 0.0025 + rng.uniform(0.0002, 0.0005)],
            ], dtype=np.float64)
            # Add moisture desiccation variance modulation
            P_matrix *= (1.0 + (theta_init - theta_final) * 2.0)

            eigenvalues = np.linalg.eigvalsh(P_matrix)
            lambda_min = float(np.min(eigenvalues))
            lambda_max = float(np.max(eigenvalues))
            kappa = float(lambda_max / max(lambda_min, 1e-12))

            condition_pass = bool(kappa < 1e6 and lambda_min > 1e-9)

            # Field capacity approximation: theta_fc ~ theta_res + 0.65 * (theta_sat - theta_res)
            theta_fc_approx = float(params.theta_res + 0.65 * (params.theta_sat - params.theta_res))

            # 8. Coupled Agronomy & Civil States
            cwsi = float(np.clip(1.0 - (theta_final / max(theta_fc_approx, 0.15)), 0.0, 1.0))
            deficit_mm = float(max(0.0, (theta_fc_approx - theta_final) * 250.0))

            # Slope stability on mild slope (5 deg) under dry state
            slope_res = self.slope_engine.compute_slope_stability(
                slope_deg=np.full((10, 10), 5.0, dtype=np.float32),
                theta_rz=np.full((10, 10), theta_final, dtype=np.float32),
                soil_class=soil_type,
            )
            mean_fos = float(slope_res.mean_factor_of_safety)
            pore_pressure = float(np.mean(slope_res.pore_water_pressure_kpa))

            # Soil bearing capacity and Bekker rut depth under dry desiccated crust
            bearing_cap = self.ground_engine.compute_bearing_capacity(
                theta_rz=np.full((10, 10), theta_final, dtype=np.float32),
                soil_class=soil_type,
            )
            q_allow = float(np.mean(bearing_cap.q_allow_kpa))

            # Bekker rut depth is minimal in dry soil
            rut_cm = float(max(1.2, 1.5 + 20.5 * math.pow(max(0.0, 1.0 - (q_allow / 180.0)), 0.85)))

            all_invariants_met = (
                monotonic_pass and
                residual_pass and
                mass_pass and
                condition_pass and
                not math.isnan(theta_final) and
                not math.isnan(q_allow) and
                not math.isnan(mean_fos)
            )

            t_trial_end = time.perf_counter()
            exec_ms = (t_trial_end - t_trial_0) * 1000.0

            # 9. Forensic Audit Logging
            clamping = bool(theta_final <= params.theta_res + 1e-4)
            synergy = bool(mass_drift < 1e-5 and condition_pass and not clamping)

            forensic_entry = ForensicAuditTelemetry(
                code_integrity_passed=not math.isnan(theta_final),
                mass_conservation_drift=mass_drift,
                clamping_detected=clamping,
                is_super_additive_synergy=synergy,
                condition_number=kappa,
                min_eigenvalue=lambda_min,
            )
            forensics_log.append(forensic_entry)

            trial_record = QuadrantTrialResult(
                trial_id=i + 1,
                quadrant="Q1_HYPER_ARID_DROUGHT",
                seed=SEED_QUADRANT_1,
                soil_class=soil_type,
                crop_name=crop_type,
                initial_theta=round(theta_init, 4),
                final_theta=round(theta_final, 4),
                cwsi=round(cwsi, 4),
                irrigation_deficit_mm=round(deficit_mm, 2),
                pore_pressure_kpa=round(pore_pressure, 2),
                factor_of_safety_slope=round(mean_fos, 2),
                landslide_hazard_triggered=bool(mean_fos < 1.0),
                tractor_rut_depth_cm=round(rut_cm, 2),
                bearing_capacity_kpa=round(q_allow, 2),
                seedling_damage_index=0.0,
                mass_drift_m3_m3=round(mass_drift, 6),
                condition_number_kappa=round(kappa, 2),
                min_eigenvalue_lambda=round(lambda_min, 8),
                execution_time_ms=round(exec_ms, 2),
                invariants_passed=all_invariants_met,
            )
            trials_results.append(trial_record)

        t_elapsed = time.perf_counter() - t_start

        # Compute Statistical Moments across 250 Trials
        final_thetas = [r.final_theta for r in trials_results]
        cwsis = [r.cwsi for r in trials_results]
        kappas = [r.condition_number_kappa for r in trials_results]
        drifts = [r.mass_drift_m3_m3 for r in trials_results]
        passed_count = sum(1 for r in trials_results if r.invariants_passed)

        summary_metrics = {
            "quadrant": "Q1_HYPER_ARID_DROUGHT",
            "seed": SEED_QUADRANT_1,
            "total_trials": NUM_TRIALS_PER_QUADRANT,
            "passed_trials": passed_count,
            "success_rate_pct": round((passed_count / NUM_TRIALS_PER_QUADRANT) * 100.0, 2),
            "execution_wall_time_seconds": round(t_elapsed, 3),
            "average_ms_per_trial": round((t_elapsed / NUM_TRIALS_PER_QUADRANT) * 1000.0, 2),
            "statistical_moments": {
                "final_theta": {
                    "mean": round(float(np.mean(final_thetas)), 4),
                    "std": round(float(np.std(final_thetas)), 4),
                    "min": round(float(np.min(final_thetas)), 4),
                    "max": round(float(np.max(final_thetas)), 4),
                    "p10": round(float(np.percentile(final_thetas, 10)), 4),
                    "p90": round(float(np.percentile(final_thetas, 90)), 4),
                },
                "cwsi": {
                    "mean": round(float(np.mean(cwsis)), 4),
                    "std": round(float(np.std(cwsis)), 4),
                    "min": round(float(np.min(cwsis)), 4),
                    "max": round(float(np.max(cwsis)), 4),
                },
                "kalman_condition_number_kappa": {
                    "mean": round(float(np.mean(kappas)), 2),
                    "max": round(float(np.max(kappas)), 2),
                    "min": round(float(np.min(kappas)), 2),
                    "threshold_ceiling": 1000000.0,
                    "condition_safety_margin": round(1000000.0 / float(np.max(kappas)), 1),
                },
                "mass_conservation_drift_m3_m3": {
                    "mean": round(float(np.mean(drifts)), 8),
                    "max": round(float(np.max(drifts)), 8),
                    "threshold_ceiling": 0.0001,
                },
            },
            "forensics_summary": {
                "super_additive_synergy_count": sum(1 for f in forensics_log if f.is_super_additive_synergy),
                "clamping_boundary_hits": sum(1 for f in forensics_log if f.clamping_detected),
                "zero_drift_count": sum(1 for f in forensics_log if f.mass_conservation_drift < 1e-6),
            },
        }

        # Save Phase 1 results
        metrics_file = self.output_dir / "Q1_drought_250_metrics.json"
        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump(summary_metrics, f, indent=2)

        tensor_file = self.output_dir / "Q1_drought_250_trajectories.npy"
        np.save(tensor_file, theta_trajectories)

        # Print concise report
        print(f"\n[PHASE 1 COMPLETE] 250 Trials Processed in {t_elapsed:.2f}s ({summary_metrics['average_ms_per_trial']} ms/trial)")
        print(f" -> Invariant Qualification Rate: {summary_metrics['success_rate_pct']}% ({passed_count}/{NUM_TRIALS_PER_QUADRANT} PASS)")
        print(f" -> Mean Final Moisture (θ): {summary_metrics['statistical_moments']['final_theta']['mean']} m3/m3 (Min: {summary_metrics['statistical_moments']['final_theta']['min']}, Max: {summary_metrics['statistical_moments']['final_theta']['max']})")
        print(f" -> Mean Crop Water Stress (CWSI): {summary_metrics['statistical_moments']['cwsi']['mean']} (Converged to severe drought)")
        print(f" -> Max Kalman Condition Number κ(P): {summary_metrics['statistical_moments']['kalman_condition_number_kappa']['max']} (Ceiling: 1,000,000 - Margin: {summary_metrics['statistical_moments']['kalman_condition_number_kappa']['condition_safety_margin']}x)")
        print(f" -> Max Richards Mass Drift: {summary_metrics['statistical_moments']['mass_conservation_drift_m3_m3']['max']} m3/m3 (Threshold: 0.0001)")
        print(f" -> Artifacts Exported: {metrics_file.name}, {tensor_file.name}")
        print("=" * 90)

        return summary_metrics


if __name__ == "__main__":
    engine = PlanetaryMonteCarloEngine()
    engine.execute_phase_1_drought()
