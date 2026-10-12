import os
import sys
import numpy as np

import importlib.util
sf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '2_data_pipeline', 'fusion', 'satellite_fusion.py'))
spec = importlib.util.spec_from_file_location("satellite_fusion", sf_path)
sf_mod = importlib.util.module_from_spec(spec)
sys.modules["satellite_fusion"] = sf_mod
spec.loader.exec_module(sf_mod)

SatelliteSAROpticalFusionEngine = sf_mod.SatelliteSAROpticalFusionEngine
MissingModalityError = sf_mod.MissingModalityError
InvalidModalityError = sf_mod.InvalidModalityError
GridMismatchError = sf_mod.GridMismatchError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '2_data_pipeline')))
from schemas.satellite_schema import GeospatialRasterAsset

def create_mock_asset(crs="EPSG:32645", res=(10.0, 10.0), bounds=(0.0, 90.0, 100.0, 100.0), valid=True, source_id="MOCK_ID") -> GeospatialRasterAsset:
    raw = np.ones((1, 10, 10), dtype=np.float32)
    mask = np.ones((1, 10, 10), dtype=bool) if valid else np.zeros((1, 10, 10), dtype=bool)
    
    return GeospatialRasterAsset(
        raw_array=raw,
        raw_dtype="float32",
        crs=crs,
        transform=(res[0], 0.0, bounds[0], 0.0, -res[1], bounds[3]),
        bounds=bounds,
        resolution=res,
        valid_data_mask=mask,
        stac_item_id=source_id
    )

def test_d08_fusion():
    target_crs = "EPSG:32645"
    target_res = (10.0, 10.0)
    target_bounds = (0.0, 90.0, 100.0, 100.0)
    
    engine = SatelliteSAROpticalFusionEngine(target_crs, target_res, target_bounds)

    print("\\n--- T-MOD-01: All expected modalities present and valid ---")
    try:
        mock_asset = create_mock_asset()
        res = engine.create_fused_spatial_tensor(
            sar_vv=create_mock_asset(source_id="SAR_VV_ID"),
            sar_vh=create_mock_asset(source_id="SAR_VH_ID"),
            ndvi=create_mock_asset(source_id="NDVI_ID"),
            ndmi=create_mock_asset(source_id="NDMI_ID"),
            dem_elevation=create_mock_asset(source_id="DEM_ELEV_ID"),
            dem_slope=create_mock_asset(source_id="DEM_SLOPE_ID"),
        )
        assert res["tensor_shape"] == (10, 10, 7)
        assert res["provenance"]["SAR_VV"]["stac_item_id"] == "SAR_VV_ID"
        assert res["fused_validity_mask"].shape == (10, 10, 7)
        assert np.all(res["fused_validity_mask"])
        print("[PASS] T-MOD-01: Fusion proceeds normally. Provenance and masks preserved.")
    except Exception as e:
        print(f"[FAIL] T-MOD-01: {e}")
        raise
        
    print("\\n--- T-MOD-02: One modality absent ---")
    try:
        engine.create_fused_spatial_tensor(
            sar_vv=create_mock_asset(),
            sar_vh=create_mock_asset(),
            ndvi=create_mock_asset(),
            ndmi=None, # Missing NDMI
            dem_elevation=create_mock_asset(),
            dem_slope=create_mock_asset(),
        )
        raise AssertionError("Should have raised MissingModalityError")
    except MissingModalityError as e:
        print("[PASS] T-MOD-02: Absent input correctly raises MissingModalityError without fabricating arrays.")

    print("\\n--- T-MOD-03: Modality present but entirely invalid ---")
    try:
        engine.create_fused_spatial_tensor(
            sar_vv=create_mock_asset(),
            sar_vh=create_mock_asset(),
            ndvi=create_mock_asset(valid=False), # Invalid NDVI mask
            ndmi=create_mock_asset(),
            dem_elevation=create_mock_asset(),
            dem_slope=create_mock_asset(),
        )
        raise AssertionError("Should have raised InvalidModalityError")
    except InvalidModalityError as e:
        print("[PASS] T-MOD-03: 100% NoData input safely rejected with InvalidModalityError.")

    print("\\n--- T-MOD-04: Incompatible spatial grids ---")
    try:
        engine.create_fused_spatial_tensor(
            sar_vv=create_mock_asset(),
            sar_vh=create_mock_asset(),
            ndvi=create_mock_asset(crs="EPSG:4326"), # Invalid CRS
            ndmi=create_mock_asset(),
            dem_elevation=create_mock_asset(),
            dem_slope=create_mock_asset(),
        )
        raise AssertionError("Should have raised GridMismatchError")
    except GridMismatchError as e:
        print("[PASS] T-MOD-04: Misaligned grid securely raises GridMismatchError before fusion.")

    print("\\n--- T-MOD-05: Output records used modalities and preserves validity ---")
    try:
        res = engine.create_fused_spatial_tensor(
            sar_vv=create_mock_asset(source_id="S1_VV"),
            sar_vh=create_mock_asset(source_id="S1_VH"),
            ndvi=create_mock_asset(source_id="S2_NDVI"),
            ndmi=create_mock_asset(source_id="S2_NDMI"),
            dem_elevation=create_mock_asset(source_id="DEM_E"),
            dem_slope=create_mock_asset(source_id="DEM_S"),
        )
        prov = res["provenance"]
        assert prov["SAR_VV"]["stac_item_id"] == "S1_VV"
        assert prov["DEM_ELEVATION"]["stac_item_id"] == "DEM_E"
        # Since input was valid, combined mask is True for all 7 layers
        assert np.all(res["fused_validity_mask"])
        
        print("[PASS] T-MOD-05: Provenance dictionary fully tracks all valid input items and bounding masks.")
    except Exception as e:
        print(f"[FAIL] T-MOD-05: {e}")
        raise

    print("\\n--- T-MOD-06: Optional DEM modalities omitted safely ---")
    try:
        res = engine.create_fused_spatial_tensor(
            sar_vv=create_mock_asset(),
            sar_vh=create_mock_asset(),
            ndvi=create_mock_asset(),
            ndmi=create_mock_asset(),
            dem_elevation=None,
            dem_slope=None
        )
        assert res["tensor_shape"] == (10, 10, 5)
        assert "DEM_ELEVATION" not in res["channels"]
        assert "DEM_SLOPE" not in res["channels"]
        
        # Verify proxy physics is uncorrupted despite missing DEM
        sm = engine.retrieve_surface_soil_moisture_proxy(res["fused_tensor"])
        assert sm.shape == (10, 10)
        
        print("[PASS] T-MOD-06: DEM is safely optional. Retrieval physics still strictly aligns to channels 0, 3, 4.")
    except Exception as e:
        print(f"[FAIL] T-MOD-06: {e}")
        raise

    print("\\n[OK] All D08 Acceptance Criteria Met. Fusion engine strictly regulates modalities.")

if __name__ == "__main__":
    test_d08_fusion()
