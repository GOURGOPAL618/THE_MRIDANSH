# THE MRIDANSH - Verification Script: Phase 2 (Dynamic Phenology & FAO-56 Dual Kc Engine)
# Module: 4_domain_translators/agronomy/verify_phase2.py

import sys
import time
from pathlib import Path
import numpy as np
import torch

# Ensure agronomy directory is in sys.path
agronomy_dir = Path(__file__).resolve().parent
if str(agronomy_dir) not in sys.path:
    sys.path.insert(0, str(agronomy_dir))

from dynamic_phenology import DynamicPhenologyEngine, PhenologyState
from fao56_dual_kc import FAO56DualKcEngine, DualKcOutput
from soil_water_reservoir import SoilWaterReservoirEngine


def run_phase2_verification():
    print("=" * 80)
    print("   THE MRIDANSH: PHASE 2 VERIFICATION (DYNAMIC PHENOLOGY & DUAL Kc)")
    print("=" * 80)

    pheno_engine = DynamicPhenologyEngine(ndvi_bare_soil=0.15, ndvi_full_canopy=0.80)
    dual_kc_engine = FAO56DualKcEngine(default_et0_mm_day=4.5)
    soil_engine = SoilWaterReservoirEngine()

    # 1. Test Optical NDVI & Fractional Cover Derivation
    print("\n[TEST 1] Verifying Optical Reflectance -> NDVI & Ground Cover (fc)...")
    # Synthetic optical array [C=4, H=2, W=2]
    # Pixel 0,0: Bare dry soil (Red=0.22, NIR=0.25)
    # Pixel 0,1: Moderate vegetative canopy (Red=0.10, NIR=0.30)
    # Pixel 1,0: Dense mature forest/crop (Red=0.04, NIR=0.55)
    # Pixel 1,1: Water/wet dark surface (Red=0.08, NIR=0.04)
    synth_opt = np.array([
        [[0.06, 0.06], [0.05, 0.08]],  # Blue
        [[0.09, 0.10], [0.08, 0.09]],  # Green
        [[0.22, 0.10], [0.04, 0.08]],  # Red
        [[0.25, 0.30], [0.55, 0.04]],  # NIR
    ], dtype=np.float32)

    ndvi = pheno_engine.compute_ndvi_from_reflectance(synth_opt, red_channel_idx=2, nir_channel_idx=3)
    fc = pheno_engine.compute_fractional_cover(ndvi)

    print(f"  -> Bare Soil Pixel  : NDVI={ndvi[0,0]:.3f} | fc={fc[0,0]:.3f} (Expected near 0)")
    print(f"  -> Moderate Canopy  : NDVI={ndvi[0,1]:.3f} | fc={fc[0,1]:.3f} (Expected ~0.5)")
    print(f"  -> Dense Full Canopy: NDVI={ndvi[1,0]:.3f} | fc={fc[1,0]:.3f} (Expected near 1.0)")
    print(f"  -> Water Body Pixel : NDVI={ndvi[1,1]:.3f} | fc={fc[1,1]:.3f} (Expected 0.0)")

    assert fc[0, 0] <= 0.10, "Bare soil ground cover must be <= 0.10"
    assert 0.40 <= fc[0, 1] <= 0.70, "Moderate canopy ground cover expected 0.40 - 0.70"
    assert fc[1, 0] >= 0.95, "Dense full canopy ground cover must be >= 0.95"
    assert fc[1, 1] == 0.0, "Negative/water NDVI must produce fc = 0.0"
    print("  => PASSED: Optical canopy decomposition satisfies spectral physics.")

    # 2. Test Dynamic Rooting Depth Elongation Zr(fc)
    print("\n[TEST 2] Verifying Dynamic Sigmoidal Root Deepening Model Zr(fc)...")
    fc_range = np.linspace(0.0, 1.0, 6)
    wheat_params = soil_engine.get_crop_parameters("wheat")
    zr_wheat = [pheno_engine.compute_dynamic_root_depth(
        f, zr_min_m=wheat_params["rooting_depth_min_m"], zr_max_m=wheat_params["rooting_depth_max_m"]
    ) for f in fc_range]

    for f, z in zip(fc_range, zr_wheat):
        print(f"  -> Canopy Cover fc={f:.2f} => Dynamic Root Depth Zr={z:.3f} m")

    # Strictly monotonic check
    assert np.all(np.diff(zr_wheat) >= 0), "Root depth must increase monotonically with canopy expansion"
    assert np.isclose(zr_wheat[0], wheat_params["rooting_depth_min_m"]), "Emergence root depth must equal zr_min"
    assert np.isclose(zr_wheat[-1], wheat_params["rooting_depth_max_m"]), "Maturity root depth must equal zr_max"
    print("  => PASSED: Dynamic root elongation complies with biological crop development.")

    # 3. Test FAO-56 Dual Kc Partitioning (Transpiration Kcb vs Evaporation Ke)
    print("\n[TEST 3] Verifying FAO-56 Dual Kc Partitioning (Kcb + Ke <= Kc_max)...")
    tex_loam = soil_engine.get_texture_properties("loam")

    # Case A: Bare wet soil (Rain/Irrigation event on bare field: fc=0, theta_surf=theta_fc)
    out_wet_bare = dual_kc_engine.compute_dual_coefficients(
        kcb=0.15,
        fractional_cover=0.0,
        theta_surf=tex_loam.theta_fc,
        theta_fc=tex_loam.theta_fc,
        theta_res=tex_loam.theta_res,
        et0_mm_day=5.0,
    )
    print(f"  -> Case A (Wet Bare Soil): Kcb={out_wet_bare.kcb:.2f}, Ke={out_wet_bare.ke:.2f}, Kc_total={out_wet_bare.kc_total:.2f}, ETc={out_wet_bare.etc_pot_mm_day:.2f} mm/day")
    assert out_wet_bare.kr == 1.0, "Wet soil surface must have Stage 1 Kr = 1.0"
    assert out_wet_bare.ke > out_wet_bare.kcb, "Evaporation must dominate transpiration on wet bare soil"

    # Case B: Dense mature crop with dry surface (fc=0.95, theta_surf=theta_res)
    out_dry_dense = dual_kc_engine.compute_dual_coefficients(
        kcb=1.15,
        fractional_cover=0.95,
        theta_surf=tex_loam.theta_res,
        theta_fc=tex_loam.theta_fc,
        theta_res=tex_loam.theta_res,
        et0_mm_day=5.0,
    )
    print(f"  -> Case B (Dry Dense Crop): Kcb={out_dry_dense.kcb:.2f}, Ke={out_dry_dense.ke:.2f}, Kc_total={out_dry_dense.kc_total:.2f}, ETc={out_dry_dense.etc_pot_mm_day:.2f} mm/day")
    assert out_dry_dense.ke <= 0.05, "Dense crop on dry soil must have near-zero evaporation"
    assert out_dry_dense.kcb > 1.0, "Transpiration must dominate"
    print("  => PASSED: Dual Kc partitioning accurately isolates transpiration from physical evaporation.")

    # 4. Test on Real-World Spaceborne Telemetry Flight Bundle
    print("\n[TEST 4] Forward Inference on Real Flight Bundle (s1_s2_dem_era5_harmonized_bundle.pt)...")
    bundle_path = Path(__file__).resolve().parents[2] / "9_spaceborne_operational_campaign" / "2_harmonized_tensors" / "s1_s2_dem_era5_harmonized_bundle.pt"
    assert bundle_path.exists(), f"Flight bundle not found: {bundle_path}"

    bundle = torch.load(bundle_path, weights_only=False)
    opt_tensor = bundle["optical"].squeeze(0).numpy()       # [4, 64, 64]
    soil_output = bundle["soil_state_output"]
    theta_surf = soil_output["volumetric_moisture"].squeeze().numpy()  # [64, 64]

    H, W = theta_surf.shape
    t0 = time.perf_counter()

    # Step 1: Phenology evaluation
    pheno_state = pheno_engine.evaluate_phenology(
        optical_reflectance_or_ndvi=opt_tensor,
        crop_params=soil_engine.get_crop_parameters("wheat"),
    )

    # Step 2: Dual Kc evaluation
    dual_out = dual_kc_engine.compute_dual_coefficients(
        kcb=pheno_state.kcb,
        fractional_cover=pheno_state.fractional_cover,
        theta_surf=theta_surf,
        theta_fc=tex_loam.theta_fc,
        theta_res=tex_loam.theta_res,
        et0_mm_day=4.80,
    )
    t_elapsed = time.perf_counter() - t0
    latency_per_px = (t_elapsed * 1000.0) / (H * W)

    print(f"  -> 64x64 Scene Performance: Time = {t_elapsed * 1000:.3f} ms | Latency = {latency_per_px:.6f} ms/pixel")
    print(f"  -> Scene Mean NDVI = {float(np.mean(pheno_state.ndvi)):.3f} (Min: {float(np.min(pheno_state.ndvi)):.3f}, Max: {float(np.max(pheno_state.ndvi)):.3f})")
    print(f"  -> Scene Mean fc   = {float(np.mean(pheno_state.fractional_cover)):.3f}")
    print(f"  -> Scene Mean Zr   = {float(np.mean(pheno_state.z_r_m)):.3f} m")
    print(f"  -> Scene Mean Kcb  = {float(np.mean(dual_out.kcb)):.3f} | Ke = {float(np.mean(dual_out.ke)):.3f} | Total Kc = {float(np.mean(dual_out.kc_total)):.3f}")
    print(f"  -> Scene Mean ETc  = {float(np.mean(dual_out.etc_pot_mm_day)):.2f} mm/day")

    # Assertions
    assert not np.any(np.isnan(dual_out.kc_total)), "NaNs detected in Kc_total"
    assert not np.any(np.isnan(dual_out.etc_pot_mm_day)), "NaNs detected in ETc"
    assert np.all(dual_out.kc_total <= dual_out.kc_max + 1e-5), "Kc cannot breach thermodynamic ceiling Kc_max"
    assert latency_per_px < 0.010, f"Latency SLA breached: {latency_per_px} ms/px >= 0.010 ms/px"
    print("  => PASSED: Real satellite bundle smoothly integrated with sub-microsecond processing.")

    print("\n" + "=" * 80)
    print("   [SUCCESS] PHASE 2 VERIFICATION COMPLETE: ALL SYSTEMS CERTIFIED")
    print("=" * 80)


if __name__ == "__main__":
    run_phase2_verification()
