# 11_simulation_test_campaign/run_simulation.py
import sys
import json
import time
from pathlib import Path
import numpy as np
import torch

repo_root = Path(__file__).resolve().parent.parent
translators_dir = repo_root / "4_domain_translators"
civil_dir = translators_dir / "civil"

for p in [repo_root, translators_dir, civil_dir]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from coupled_agro_civil_simulator import CoupledAgroCivilSimulator

def main():
    print("=" * 80)
    print("  JCC CAMPUS 2 (RS-SDA DIVISION) - COUPLED SIMULATION RUNNER")
    print("=" * 80)
    
    sim = CoupledAgroCivilSimulator()
    output_dir = Path(__file__).resolve().parent

    # Load spaceborne flight telemetry
    bundle_path = repo_root / "9_spaceborne_operational_campaign" / "2_harmonized_tensors" / "s1_s2_dem_era5_harmonized_bundle.pt"
    bundle = torch.load(bundle_path, weights_only=False, map_location="cpu")
    
    theta_arr = bundle["soil_state_output"]["volumetric_moisture"].squeeze().numpy()
    if theta_arr.ndim == 3:
        theta_arr = theta_arr[0]
    
    dem = bundle["dem"].squeeze().numpy()
    if dem.ndim == 3:
        dem_slope = dem[1] # slope layer
        dem_elev = dem[0]
    else:
        gy, gx = np.gradient(dem, 10.0, 10.0)
        dem_slope = np.degrees(np.arctan(np.sqrt(gx**2 + gy**2)))
        dem_elev = dem
    
    # 1. Evaluate 5 Specific Scenarios
    scenarios = [
        {"name": "Scenario 1: Bone Dry Baseline", "water_mm": 0.0},
        {"name": "Scenario 2: Insufficient Pre-Soak", "water_mm": 5.0},
        {"name": "Scenario 3: Goldilocks Zone (Optimal)", "water_mm": 12.0},
        {"name": "Scenario 4: Heavy Over-Irrigation", "water_mm": 45.0},
        {"name": "Scenario 5: Typical Uncontrolled Flood", "water_mm": 75.0},
    ]
    
    scenario_results = []
    for sc in scenarios:
        res = sim.simulate_paddy_tilling(
            theta_initial=theta_arr,
            slope_deg=dem_slope,
            water_applied_mm=sc["water_mm"]
        )
        entry = {
            "scenario": sc["name"],
            "water_applied_mm": sc["water_mm"],
            "mean_moisture": round(res.paddy_state.mean_moisture, 4),
            "water_status": res.paddy_state.water_status_category,
            "mean_rut_depth_cm": round(res.tractor_state.mean_rut_depth_cm, 2),
            "max_rut_depth_cm": round(res.tractor_state.max_rut_depth_cm, 2),
            "mobility_status": res.tractor_state.mobility_status,
            "mean_seedling_damage_index": round(res.mean_seedling_damage_index, 4),
            "safe_nursery_area_pct": round(res.safe_nursery_area_pct, 2),
            "damaged_nursery_area_pct": round(res.damaged_nursery_area_pct, 2),
            "recommended_optimal_water_mm": round(res.recommended_optimal_water_mm, 1),
            "advisory_bulletin": res.farmer_advisory_text
        }
        scenario_results.append(entry)
        print(f"[{sc['name']}] Water: {sc['water_mm']}mm -> Rut: {entry['mean_rut_depth_cm']}cm | SDI: {entry['mean_seedling_damage_index']} | {entry['mobility_status']}")

    # 2. Monte Carlo Stress Test Precursor (50 trials)
    t0 = time.perf_counter()
    mc_res = sim.run_monte_carlo_stress_test(
        theta_initial=theta_arr,
        slope_deg=dem_slope,
        num_trials=50,
        water_nominal_mm=40.0
    )
    mc_wall_ms = (time.perf_counter() - t0) * 1000.0
    
    mc_summary = {
        "num_trials": mc_res.num_trials,
        "wall_time_ms": round(mc_res.execution_time_ms, 2),
        "ms_per_trial": round(mc_res.latency_per_trial_ms, 3),
        "projected_1000_trials_seconds": round(mc_res.latency_per_trial_ms * 1000.0 / 1000.0, 2),
        "mean_rut_depth_cm": round(float(np.mean(mc_res.mean_rut_depth_distribution_cm)), 2),
        "p95_rut_depth_cm": round(float(np.percentile(mc_res.mean_rut_depth_distribution_cm, 95)), 2),
        "mean_damage_index": round(float(np.mean(mc_res.mean_damage_distribution)), 4),
        "p95_damage_index": round(float(np.percentile(mc_res.mean_damage_distribution, 95)), 4),
        "bogged_chassis_prob_pct": round(mc_res.tractor_bogged_probability * 100.0, 2),
        "severe_damage_prob_pct": round(mc_res.seedling_damage_probability * 100.0, 2),
        "recommended_safe_water_envelope_mm": [
            round(mc_res.optimal_water_ci_95[0], 1),
            round(mc_res.optimal_water_ci_95[1], 1)
        ]
    }
    print(f"\n[Monte Carlo 50 Trials] Executed in {mc_summary['wall_time_ms']} ms ({mc_summary['ms_per_trial']} ms/trial).")
    print(f"Projected 1,000-Trial Wall Time: {mc_summary['projected_1000_trials_seconds']} seconds!")

    # 3. Spaceborne Scene Telemetry
    telemetry_summary = {
        "scene_name": "Kendrapara Coastal Alluvial Delta",
        "spatial_crs": "EPSG:32645 (WGS 84 / UTM Zone 45N)",
        "total_pixels": int(theta_arr.size),
        "total_hectares": 40.96,
        "baseline_moisture_mean": round(float(np.mean(theta_arr)), 4),
        "elevation_range_m": [round(float(np.min(dem_elev)), 3), round(float(np.max(dem_elev)), 3)],
        "slope_mean_deg": round(float(np.mean(dem_slope)), 2),
        "optimal_prescribed_water_mm": round(scenario_results[2]["recommended_optimal_water_mm"], 1),
        "water_saved_liters_per_hectare": round((75.0 - 12.0) * 10000.0, 0)
    }

    # 4. Serialize to JSON
    full_output = {
        "metadata": {
            "mission": "THE MRIDANSH (AETHER-MRID1607X)",
            "command": "Jagannath Command Center (JCC) - Campus 2 (RS-SDA Division)",
            "commander": "Gouragopal Mohapatra (GOURGOPAL618)",
            "campaign": "Cross-Domain Agro-Civil Simulation Campaign",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        },
        "scenarios": scenario_results,
        "spaceborne_flight_telemetry": telemetry_summary,
        "monte_carlo_precursor": mc_summary
    }
    
    out_json = output_dir / "simulation_telemetry_results.json"
    out_json.write_text(json.dumps(full_output, indent=2), encoding="utf-8")
    print(f"\nSaved telemetry results to: {out_json}")

if __name__ == "__main__":
    main()
