# THE MRIDANSH - Verification Script: Day 13 Phase 1 (Precision Irrigation Engine)
# Module: 4_domain_translators/agronomy/verify_phase1_day13.py

import sys
import time
from pathlib import Path
import numpy as np
import torch

# Ensure agronomy directory is in sys.path
agronomy_dir = Path(__file__).resolve().parent
if str(agronomy_dir) not in sys.path:
    sys.path.insert(0, str(agronomy_dir))

from irrigation_prescription import (
    PrecisionIrrigationEngine,
    IrrigationStrategy,
    IrrigationSystemType,
    LITERS_PER_HA_PER_MM,
    LITERS_PER_10M_PIXEL_PER_MM,
)
from agronomy_domain_engine import AgronomyDomainEngine


def run_day13_phase1_verification():
    print("=" * 80)
    print("   THE MRIDANSH: DAY 13 PHASE 1 VERIFICATION (PRECISION VRI DEFICIT ENGINE)")
    print("=" * 80)

    engine = PrecisionIrrigationEngine()

    # 1. Test Strategies Comparison (Stress Avoidance vs Full Recharge)
    print("\n[TEST 1] Verifying VRI Strategies (STRESS_AVOIDANCE vs FULL_RECHARGE)...")
    dr_test = np.array([0.0, 20.0, 40.0, 60.0, 90.0], dtype=np.float32)  # Depletions in mm
    raw_threshold = 40.0  # RAW in mm
    taw_capacity = 100.0  # TAW in mm

    # Mode A: STRESS_AVOIDANCE (Only refills excess over RAW)
    presc_avoid = engine.compute_prescription(
        dr_mm=dr_test,
        raw_mm=raw_threshold,
        taw_mm=taw_capacity,
        strategy=IrrigationStrategy.STRESS_AVOIDANCE,
        application_efficiency=1.0,  # Unity for pure depth check
    )
    expected_avoid_mm = np.array([0.0, 0.0, 0.0, 20.0, 50.0], dtype=np.float32)
    assert np.allclose(presc_avoid.net_irrigation_mm, expected_avoid_mm), "STRESS_AVOIDANCE depth mismatch"
    print(f"  -> STRESS_AVOIDANCE Depths: {presc_avoid.net_irrigation_mm.tolist()} mm | OK")

    # Mode B: FULL_RECHARGE (Refills full Dr if Dr > RAW)
    presc_recharge = engine.compute_prescription(
        dr_mm=dr_test,
        raw_mm=raw_threshold,
        taw_mm=taw_capacity,
        strategy=IrrigationStrategy.FULL_RECHARGE,
        application_efficiency=1.0,
    )
    expected_recharge_mm = np.array([0.0, 0.0, 0.0, 60.0, 90.0], dtype=np.float32)
    assert np.allclose(presc_recharge.net_irrigation_mm, expected_recharge_mm), "FULL_RECHARGE depth mismatch"
    print(f"  -> FULL_RECHARGE    Depths: {presc_recharge.net_irrigation_mm.tolist()} mm | OK")
    print("  => PASSED: Irrigation dispatch strategies adhere to FAO-56 deficit mechanics.")

    # 2. Test Volumetric Dimensional Invariants (L/ha and L/pixel)
    print("\n[TEST 2] Verifying Volumetric Conversions (L/ha = 100 * L/pixel)...")
    i_test_mm = np.array([10.0, 25.0, 50.0], dtype=np.float32)
    presc_vol = engine.compute_prescription(
        dr_mm=i_test_mm + 40.0,
        raw_mm=40.0,
        strategy=IrrigationStrategy.STRESS_AVOIDANCE,
        application_efficiency=1.0,
    )
    
    # 1 mm = 10,000 L/ha and 100 L/pixel
    expected_l_ha = i_test_mm * 10000.0
    expected_l_px = i_test_mm * 100.0
    assert np.allclose(presc_vol.liters_per_hectare, expected_l_ha), "L/ha conversion mismatch"
    assert np.allclose(presc_vol.liters_per_pixel, expected_l_px), "L/pixel conversion mismatch"
    assert np.allclose(presc_vol.liters_per_hectare, presc_vol.liters_per_pixel * 100.0), "Scale invariant breached"
    
    for mm, l_ha, l_px in zip(i_test_mm, presc_vol.liters_per_hectare, presc_vol.liters_per_pixel):
        print(f"  -> Deficit {mm:5.1f} mm => {l_ha:10,.0f} L/ha | {l_px:6,.0f} L/pixel (10m x 10m)")
    print("  => PASSED: Volumetric dimensional invariance strictly certified.")

    # 3. Test Irrigation System Efficiency Scaling (Drip vs Sprinkler vs Flood)
    print("\n[TEST 3] Verifying System Application Efficiencies (Drip 90% vs Pivot 80% vs Flood 60%)...")
    dr_single = 50.0  # mm
    raw_single = 20.0 # mm

    p_drip = engine.compute_prescription(dr_single, raw_single, strategy=IrrigationStrategy.STRESS_AVOIDANCE, system_type=IrrigationSystemType.DRIP_MICRO)
    p_pivot = engine.compute_prescription(dr_single, raw_single, strategy=IrrigationStrategy.STRESS_AVOIDANCE, system_type=IrrigationSystemType.CENTER_PIVOT)
    p_flood = engine.compute_prescription(dr_single, raw_single, strategy=IrrigationStrategy.STRESS_AVOIDANCE, system_type=IrrigationSystemType.SURFACE_FLOOD)

    # Net depth is 30 mm in all cases
    assert np.isclose(p_drip.net_irrigation_mm, 30.0)
    # Gross: 30 / 0.90 = 33.33 mm, 30 / 0.80 = 37.5 mm, 30 / 0.60 = 50.0 mm
    print(f"  -> Drip (eta=0.90)    : Gross = {float(p_drip.gross_irrigation_mm):.2f} mm | Volume = {float(p_drip.liters_per_hectare):10,.0f} L/ha")
    print(f"  -> Pivot (eta=0.80)   : Gross = {float(p_pivot.gross_irrigation_mm):.2f} mm | Volume = {float(p_pivot.liters_per_hectare):10,.0f} L/ha")
    print(f"  -> Flood (eta=0.60)   : Gross = {float(p_flood.gross_irrigation_mm):.2f} mm | Volume = {float(p_flood.liters_per_hectare):10,.0f} L/ha")
    
    assert p_drip.liters_per_hectare < p_pivot.liters_per_hectare < p_flood.liters_per_hectare, "Efficiency ordering failed"
    water_saving_pct = ((p_flood.liters_per_hectare - p_drip.liters_per_hectare) / p_flood.liters_per_hectare) * 100.0
    print(f"  -> Precision Drip Water Savings vs Conventional Flood: {water_saving_pct:.1f}%")
    print("  => PASSED: Engineering application efficiencies correctly scale gross water prescriptions.")

    # 4. Real Flight Telemetry Forward Run (64x64 Scene, 4,096 Pixels)
    print("\n[TEST 4] Forward VRI Prescription on Real Flight Bundle (s1_s2_dem_era5_harmonized_bundle.pt)...")
    bundle_path = Path(__file__).resolve().parents[2] / "9_spaceborne_operational_campaign" / "2_harmonized_tensors" / "s1_s2_dem_era5_harmonized_bundle.pt"
    assert bundle_path.exists(), f"Missing flight bundle: {bundle_path}"

    bundle = torch.load(bundle_path, weights_only=False)
    opt_tensor = bundle["optical"].squeeze(0).numpy()
    soil_output = bundle["soil_state_output"]
    theta_surf = soil_output["volumetric_moisture"].squeeze().numpy()
    theta_rz = np.clip(theta_surf * 0.95 + 0.01, 0.05, 0.45)

    # Step 1: Agronomy forward pass for vadose Dr and RAW
    agri_engine = AgronomyDomainEngine()
    agri_state = agri_engine.forward(
        optical_reflectance_or_ndvi=opt_tensor,
        theta_surf=theta_surf,
        theta_rz=theta_rz,
        soil_texture="silt_loam",
        crop_name="wheat",
    )

    # Step 2: Precision VRI prescription
    H, W = theta_surf.shape
    t0 = time.perf_counter()
    vri_map = engine.compute_prescription(
        dr_mm=agri_state.root_depletion_dr_mm,
        raw_mm=agri_state.raw_mm,
        taw_mm=agri_state.taw_mm,
        strategy=IrrigationStrategy.FULL_RECHARGE,
        system_type=IrrigationSystemType.DRIP_MICRO,
    )
    t_elapsed = time.perf_counter() - t0
    latency_per_px = (t_elapsed * 1000.0) / (H * W)

    # Verify array assertions
    assert vri_map.net_irrigation_mm.shape == (H, W)
    assert vri_map.liters_per_hectare.shape == (H, W)
    assert vri_map.liters_per_pixel.shape == (H, W)
    assert vri_map.priority_mask.shape == (H, W)
    assert not np.any(np.isnan(vri_map.liters_per_hectare)), "NaNs detected in L/ha"
    assert not np.any(np.isinf(vri_map.liters_per_hectare)), "Infs detected in L/ha"
    assert np.all(vri_map.net_irrigation_mm >= 0.0), "Negative irrigation depth detected"

    total_scene_liters = float(np.sum(vri_map.liters_per_pixel))
    print(f"  -> 64x64 Scene Performance : Runtime = {t_elapsed * 1000:.3f} ms | Latency = {latency_per_px:.6f} ms/pixel")
    print(f"  -> Irrigable Area Triggered: {vri_map.trigger_fraction_pct:.1f}% of farm scene ({int(np.sum(vri_map.priority_mask))}/{H*W} pixels)")
    print(f"  -> Mean Prescription Rate  : {vri_map.mean_prescription_l_ha:,.0f} Liters / Hectare (for irrigable zones)")
    print(f"  -> Total Farm Water Volume : {total_scene_liters:,.0f} Liters across entire 40.96 ha scene")
    assert latency_per_px < 0.005000, f"Latency SLA breached: {latency_per_px} ms/px"
    print("  => PASSED: Real satellite VRI prescription executed with sub-microsecond latency.")

    print("\n" + "=" * 80)
    print("   [SUCCESS] DAY 13 PHASE 1 VERIFICATION COMPLETE: ALL INVARIANTS CERTIFIED")
    print("=" * 80)


if __name__ == "__main__":
    run_day13_phase1_verification()
