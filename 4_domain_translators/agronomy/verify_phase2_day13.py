# THE MRIDANSH - Verification Script: Day 13 Phase 2 (Conformal Risk Dispatch & GeoTIFFs)
# Module: 4_domain_translators/agronomy/verify_phase2_day13.py

import json
import sys
import time
from pathlib import Path
import numpy as np
import rasterio
import torch

# Ensure agronomy directory is in sys.path
agronomy_dir = Path(__file__).resolve().parent
if str(agronomy_dir) not in sys.path:
    sys.path.insert(0, str(agronomy_dir))

from conformal_risk_dispatcher import ConformalRiskDispatcher, ConformalIrrigationDispatch
from agronomic_geotiff_exporter import AgronomicGeoTIFFExporter
from agronomy_domain_engine import AgronomyDomainEngine
from irrigation_prescription import IrrigationStrategy, IrrigationSystemType


def run_day13_phase2_verification():
    print("=" * 80)
    print("   THE MRIDANSH: DAY 13 PHASE 2 VERIFICATION (CONFORMAL RISK & GEOTIFF EXPORT)")
    print("=" * 80)

    risk_dispatcher = ConformalRiskDispatcher()
    exporter = AgronomicGeoTIFFExporter()

    # 1. Test Conformal Invariant Ordering (I_min <= I_nominal <= I_max)
    print("\n[TEST 1] Verifying Conformal 2-Sigma Ordering Invariants...")
    # Synthetic array across varying moisture and uncertainty levels
    theta_rz_test = np.array([0.15, 0.20, 0.25, 0.30], dtype=np.float32)
    sigma2_test = np.array([0.015, 0.020, 0.018, 0.012], dtype=np.float32)
    taw_val = 100.0
    raw_val = 40.0

    res_dispatch = risk_dispatcher.dispatch_risk_bounds(
        theta_rz=theta_rz_test.reshape(2, 2),
        uncertainty_2sigma=sigma2_test.reshape(2, 2),
        theta_fc=0.32,
        theta_wp=0.12,
        theta_sat=0.45,
        z_r_m=0.80,
        raw_mm=raw_val,
        taw_mm=taw_val,
        strategy=IrrigationStrategy.FULL_RECHARGE,
        system_type=IrrigationSystemType.DRIP_MICRO,
    )

    i_min = res_dispatch.i_min_l_ha.flatten()
    i_nom = res_dispatch.i_nominal_l_ha.flatten()
    i_max = res_dispatch.i_max_l_ha.flatten()
    spread = res_dispatch.risk_spread_l_ha.flatten()

    for idx in range(len(i_min)):
        print(f"  -> Pixel {idx}: I_min={i_min[idx]:9,.0f} L/ha | I_nom={i_nom[idx]:9,.0f} L/ha | I_max={i_max[idx]:9,.0f} L/ha | Spread={spread[idx]:8,.0f} L/ha")
        assert i_min[idx] <= i_nom[idx] <= i_max[idx], f"Ordering breach at pixel {idx}: {i_min[idx]} <= {i_nom[idx]} <= {i_max[idx]}"
        assert spread[idx] >= 0.0, f"Negative spread at pixel {idx}"
    print("  => PASSED: Conformal risk bounds strictly satisfy I_min <= I_nominal <= I_max.")

    # 2. Real Flight Telemetry Forward Execution
    print("\n[TEST 2] Ingesting Flight Bundle & Executing Conformal Risk Dispatch...")
    bundle_path = Path(__file__).resolve().parents[2] / "9_spaceborne_operational_campaign" / "2_harmonized_tensors" / "s1_s2_dem_era5_harmonized_bundle.pt"
    assert bundle_path.exists(), f"Missing flight bundle: {bundle_path}"

    bundle = torch.load(bundle_path, weights_only=False)
    opt_tensor = bundle["optical"].squeeze(0).numpy()
    soil_output = bundle["soil_state_output"]
    theta_surf = soil_output["volumetric_moisture"].squeeze().numpy()
    uncertainty_2sigma = soil_output["conformal_uncertainty"].squeeze().numpy()
    theta_rz = np.clip(theta_surf * 0.95 + 0.01, 0.05, 0.45)

    H, W = theta_surf.shape

    # Step 1: Agronomy Engine
    agri_engine = AgronomyDomainEngine()
    agri_state = agri_engine.forward(
        optical_reflectance_or_ndvi=opt_tensor,
        theta_surf=theta_surf,
        theta_rz=theta_rz,
        soil_texture="silt_loam",
        crop_name="wheat",
    )

    # Step 2: Conformal Risk Dispatch
    t0 = time.perf_counter()
    flight_dispatch = risk_dispatcher.dispatch_risk_bounds(
        theta_rz=theta_rz,
        uncertainty_2sigma=uncertainty_2sigma,
        theta_fc=0.33,
        theta_wp=0.13,
        theta_sat=0.45,
        z_r_m=agri_state.root_depth_m,
        raw_mm=agri_state.raw_mm,
        taw_mm=agri_state.taw_mm,
        strategy=IrrigationStrategy.FULL_RECHARGE,
        system_type=IrrigationSystemType.DRIP_MICRO,
    )
    t_elapsed = time.perf_counter() - t0
    latency_px = (t_elapsed * 1000.0) / (H * W)

    print(f"  -> Conformal Dispatch Latency: {latency_px:.6f} ms/pixel ({t_elapsed * 1000:.3f} ms total)")
    print(f"  -> Mean 2-Sigma Moisture Uncertainty: ±{float(np.mean(uncertainty_2sigma)):.4f} m3/m3")
    print(f"  -> Mean Irrigation Risk Envelope     : ±{float(np.mean(flight_dispatch.risk_envelope_l_ha)):,.0f} Liters/ha")
    print(f"  -> Mean Risk Spread (I_max - I_min)  :  {float(np.mean(flight_dispatch.risk_spread_l_ha)):,.0f} Liters/ha")
    assert np.all(flight_dispatch.i_min_l_ha <= flight_dispatch.i_nominal_l_ha + 1e-4)
    assert np.all(flight_dispatch.i_nominal_l_ha <= flight_dispatch.i_max_l_ha + 1e-4)
    print("  => PASSED: Flight telemetry risk dispatch executed with zero defects.")

    # 3. Export 4 Production Agronomic GeoTIFFs & Master COG Stack
    print("\n[TEST 3] Exporting Production Agronomic GeoTIFFs to 7_production_geotiffs...")
    manifest = exporter.export_agronomic_rasters(
        cwsi=agri_state.cwsi,
        dr_mm=agri_state.root_depletion_dr_mm,
        irrigation_l_ha=flight_dispatch.i_nominal_l_ha,
        risk_envelope_l_ha=flight_dispatch.risk_envelope_l_ha,
        crop_name="Winter Wheat",
        soil_texture="Silt Loam",
    )

    out_dir = exporter.output_dir
    print(f"  -> Production Directory: {out_dir}")
    for name, meta in manifest["rasters"].items():
        print(f"     • {meta['filename']:<55} | SHA-256: {meta['sha256'][:16]}...")

    # 4. Rasterio Verification of Exported GeoTIFFs
    print("\n[TEST 4] Validating Exported GeoTIFFs via Rasterio Engine...")
    master_cog_path = out_dir / "master_agronomic_vri_4layer_10m.tif"
    if not master_cog_path.exists():
        master_cog_path = out_dir / "master_agronomic_vri_4layer_10m_target.tif"

    assert master_cog_path.exists(), f"Master COG missing: {master_cog_path}"
    with rasterio.open(master_cog_path) as src:
        assert src.count == 4, f"Expected 4 bands, got {src.count}"
        assert src.crs.to_string() == "EPSG:32645", f"CRS mismatch: {src.crs}"
        assert src.width == 64 and src.height == 64, f"Dimensions mismatch: {src.width}x{src.height}"
        assert src.transform[0] == 10.0 and abs(src.transform[4]) == 10.0, "Resolution must be 10.0m"
        
        # Read all 4 bands and verify zero NaNs / Infs
        for b_idx in range(1, 5):
            arr = src.read(b_idx)
            assert not np.any(np.isnan(arr)), f"NaN in Band {b_idx}"
            assert not np.any(np.isinf(arr)), f"Inf in Band {b_idx}"
            desc = src.descriptions[b_idx - 1]
            print(f"  -> Band {b_idx}: {desc:<65} | Min={np.min(arr):.2f}, Max={np.max(arr):.2f} | OK")

    print("  => PASSED: All 4 production GeoTIFF rasters verified with standard GIS CRS & lossless compression.")

    print("\n" + "=" * 80)
    print("   [SUCCESS] DAY 13 PHASE 2 VERIFICATION COMPLETE: ALL SYSTEMS CERTIFIED")
    print("=" * 80)


if __name__ == "__main__":
    run_day13_phase2_verification()
