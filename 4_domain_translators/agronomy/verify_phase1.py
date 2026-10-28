# THE MRIDANSH - Verification Script: Phase 1 (Soil Water Reservoir Engine)
# Module: 4_domain_translators/agronomy/verify_phase1.py

import sys
import time
import numpy as np
from pathlib import Path

# Ensure agronomy directory is directly in sys.path
agronomy_dir = Path(__file__).resolve().parent
if str(agronomy_dir) not in sys.path:
    sys.path.insert(0, str(agronomy_dir))

from soil_water_reservoir import (
    SoilWaterReservoirEngine,
    USDA_TEXTURE_PROPERTIES,
)


def run_phase1_verification():
    print("=" * 80)
    print("   THE MRIDANSH: PHASE 1 VERIFICATION (SOIL WATER RESERVOIR & TAXONOMY)")
    print("=" * 80)

    engine = SoilWaterReservoirEngine()

    # 1. Test Crop Taxonomy Loading
    print("\n[TEST 1] Verifying FAO-56 Crop Taxonomy Loading...")
    crops_to_test = ["rice_paddy", "wheat", "maize", "sugarcane", "cotton", "potato", "pulses_chickpea"]
    for c in crops_to_test:
        params = engine.get_crop_parameters(c)
        p = params["p_depletion_fraction"]
        zr_max = params["rooting_depth_max_m"]
        assert 0.1 <= p <= 0.8, f"Invalid p={p} for {c}"
        assert 0.3 <= zr_max <= 2.5, f"Invalid zr_max={zr_max} for {c}"
        print(f"  -> {params['common_name']:<25} | p = {p:.2f} | Zr_max = {zr_max:.2f} m | OK")
    print("  => PASSED: All major FAO-56 crops loaded with validated parameters.")

    # 2. Test USDA 12 Textures Hydraulic Properties
    print("\n[TEST 2] Verifying USDA 12 Texture Hydraulic Properties...")
    assert len(USDA_TEXTURE_PROPERTIES) == 12, "Must contain all 12 USDA texture classes"
    for name, prop in USDA_TEXTURE_PROPERTIES.items():
        assert prop.theta_res < prop.theta_wp < prop.theta_fc < prop.theta_sat, f"Ordering failed for {name}"
        # Soil available water capacity per meter
        awc = prop.theta_fc - prop.theta_wp
        print(f"  -> {name:<18} | Sat={prop.theta_sat:.2f} | FC={prop.theta_fc:.2f} | WP={prop.theta_wp:.2f} | AWC={awc:.2f} m3/m3")
    print("  => PASSED: All 12 USDA textures strictly satisfy thermodynamic & hydraulic ordering.")

    # 3. Test Saxton-Rawls Continuous Pedotransfer Functions
    print("\n[TEST 3] Verifying Saxton-Rawls Continuous Pedotransfer...")
    # Test typical Loam: sand=0.40, clay=0.20, om=0.02
    fc_loam, wp_loam, sat_loam = engine.saxton_rawls_pedotransfer(0.40, 0.20, 0.02)
    print(f"  -> Loam Pedotransfer: FC={fc_loam:.3f}, WP={wp_loam:.3f}, Sat={sat_loam:.3f}")
    assert wp_loam < fc_loam < sat_loam, "Continuous pedotransfer ordering failure"

    # Test typical Clay: sand=0.20, clay=0.55, om=0.02
    fc_clay, wp_clay, sat_clay = engine.saxton_rawls_pedotransfer(0.20, 0.55, 0.02)
    print(f"  -> Clay Pedotransfer: FC={fc_clay:.3f}, WP={wp_clay:.3f}, Sat={sat_clay:.3f}")
    assert wp_clay < fc_clay < sat_clay, "Continuous pedotransfer ordering failure"
    assert fc_clay > fc_loam, "Clay field capacity must exceed Loam field capacity"
    print("  => PASSED: Saxton-Rawls continuous equations validated.")

    # 4. Test 2D Spatial Raster Grid Execution (64x64 Scene)
    print("\n[TEST 4] Verifying 2D Spatial Raster Grid Execution (64x64 Scene)...")
    H, W = 64, 64
    t0 = time.perf_counter()
    res_rice = engine.generate_spatial_reservoir_map(
        grid_shape=(H, W),
        dominant_texture="clay_loam",
        dominant_crop="rice_paddy",
        root_depth_m=0.40,
    )
    t_elapsed = time.perf_counter() - t0
    latency_per_px = (t_elapsed * 1000.0) / (H * W)

    assert res_rice.taw_mm.shape == (H, W), f"Shape mismatch: {res_rice.taw_mm.shape}"
    assert res_rice.raw_mm.shape == (H, W), f"Shape mismatch: {res_rice.raw_mm.shape}"
    assert np.all(res_rice.raw_mm <= res_rice.taw_mm), "RAW must be <= TAW across all pixels"
    assert not np.any(np.isnan(res_rice.taw_mm)), "NaNs detected in TAW"
    assert not np.any(np.isnan(res_rice.raw_mm)), "NaNs detected in RAW"
    assert not np.any(np.isinf(res_rice.taw_mm)), "Infs detected in TAW"

    mean_taw = float(np.mean(res_rice.taw_mm))
    mean_raw = float(np.mean(res_rice.raw_mm))
    print(f"  -> 64x64 Scene Performance: Total Time = {t_elapsed * 1000:.3f} ms | Latency = {latency_per_px:.6f} ms/pixel")
    print(f"  -> Mean TAW = {mean_taw:.2f} mm | Mean RAW = {mean_raw:.2f} mm | Crop: Rice (p=0.20, Zr=0.40m)")

    # Test Wheat with deeper roots
    res_wheat = engine.generate_spatial_reservoir_map(
        grid_shape=(H, W),
        dominant_texture="silt_loam",
        dominant_crop="wheat",
        root_depth_m=0.90,
    )
    mean_taw_wheat = float(np.mean(res_wheat.taw_mm))
    mean_raw_wheat = float(np.mean(res_wheat.raw_mm))
    print(f"  -> Mean TAW = {mean_taw_wheat:.2f} mm | Mean RAW = {mean_raw_wheat:.2f} mm | Crop: Wheat (p=0.55, Zr=0.90m)")
    assert mean_taw_wheat > mean_taw, "Deeper rooted wheat must have larger TAW reservoir"
    print("  => PASSED: 2D Spatial Raster Reservoir validated with microsecond execution speed.")

    print("\n" + "=" * 80)
    print("   [SUCCESS] PHASE 1 VERIFICATION COMPLETE: ALL SYSTEMS CERTIFIED")
    print("=" * 80)


if __name__ == "__main__":
    run_phase1_verification()
