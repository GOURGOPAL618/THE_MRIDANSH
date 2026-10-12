import os
import sys
import numpy as np

import importlib.util
rp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '2_data_pipeline', 'preprocessing', 'raster_processor.py'))
spec = importlib.util.spec_from_file_location("raster_processor", rp_path)
rp_mod = importlib.util.module_from_spec(spec)
sys.modules["raster_processor"] = rp_mod
spec.loader.exec_module(rp_mod)
RasterDataProcessor = rp_mod.RasterDataProcessor
GridAlignmentError = rp_mod.GridAlignmentError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '2_data_pipeline')))
from schemas.satellite_schema import GeospatialRasterAsset
from schemas.satellite_schema import GeospatialRasterAsset
from rasterio.transform import Affine

def test_raster_processor_d06():
    processor = RasterDataProcessor()

    # 1. Generate Mock GeospatialRasterAsset (EPSG:32645)
    # 10x10 array at 10m resolution
    raw = np.ones((1, 10, 10), dtype=np.uint16) * 1000
    raw[0, 5, 5] = 5000  # distinct value for testing bilinear/nearest
    mask = np.ones((1, 10, 10), dtype=bool)
    mask[0, 0:2, 0:2] = False # NoData region (top-left 2x2)

    src_transform = Affine.translation(300000.0, 4000000.0) * Affine.scale(10.0, -10.0)

    asset = GeospatialRasterAsset(
        raw_array=raw,
        raw_dtype="uint16",
        scale_factor=1.0,
        add_offset=0.0,
        crs="EPSG:32645",
        transform=tuple(src_transform)[:6],
        bounds=(300000.0, 3999900.0, 300100.0, 4000000.0),
        resolution=(10.0, 10.0),
        valid_data_mask=mask,
        nodata_value=0.0
    )

    print("\\n--- Running T-FIX-02: Deterministic Reprojection ---")
    try:
        # Reproject to exactly same CRS but shifted bounds and 20m res
        # Bounds exactly cover 40x40m -> 2x2 of 20m pixels.
        target_bounds = (300000.0, 3999960.0, 300040.0, 4000000.0)
        target_res = (20.0, 20.0)
        
        reprojected = processor.reproject_asset(
            asset,
            target_crs="EPSG:32645",
            target_resolution=target_res,
            target_bounds=target_bounds,
            is_categorical=False # Bilinear
        )
        
        assert reprojected.crs == "EPSG:32645"
        assert reprojected.raw_array.shape == (1, 2, 2)
        assert reprojected.transform[0] == 20.0
        assert reprojected.transform[4] == -20.0
        assert reprojected.transform[2] == 300000.0
        assert reprojected.transform[5] == 4000000.0
        
        # Test exact value match. Bilinear of all 1000s is 1000.
        assert reprojected.raw_array[0, 1, 1] == 1000
        
        print("[PASS] T-FIX-02: CRS, dimensions, transform aligned correctly. Continuous resampling (Bilinear) worked.")
    except Exception as e:
        print(f"[FAIL] T-FIX-02: {e}")
        raise

    print("\\n--- Running T-MASK-01: Mask and nodata propagation ---")
    try:
        # Reproject a categorical mask asset using Nearest
        reprojected_mask = processor.reproject_asset(
            asset,
            target_crs="EPSG:32645",
            target_resolution=(10.0, 10.0), # Same res
            target_bounds=(300000.0, 3999980.0, 300020.0, 4000000.0), # Top-Left 2x2 pixels
            is_categorical=True # Nearest
        )
        
        # Original mask has False at [0:2, 0:2]. 
        # BBox (300000.0, 3999980.0, 300020.0, 4000000.0) isolating exactly top-left 2x2 pixels.
        assert np.all(reprojected_mask.valid_data_mask == False)
        print("[PASS] T-MASK-01: Invalid pixels correctly masked using Nearest resampling.")
    except Exception as e:
        print(f"[FAIL] T-MASK-01: {e}")
        raise

    print("\\n--- Running T-ERR-01: Invalid target grid ---")
    try:
        try:
            processor.reproject_asset(
                asset,
                target_crs="EPSG:32645",
                target_resolution=(-10.0, 10.0), # Invalid res
                target_bounds=(300000.0, 3999960.0, 300040.0, 4000000.0)
            )
            raise AssertionError("Should fail on negative resolution")
        except GridAlignmentError:
            pass

        try:
            processor.reproject_asset(
                asset,
                target_crs="EPSG:32645",
                target_resolution=(10.0, 10.0),
                target_bounds=(300040.0, 4000000.0, 300000.0, 3999960.0) # Invalid bounds min > max
            )
            raise AssertionError("Should fail on invalid bounds")
        except GridAlignmentError:
            pass
            
        print("[PASS] T-ERR-01: Invalid grids safely raise GridAlignmentError with no fabricated data.")
    except Exception as e:
        print(f"[FAIL] T-ERR-01: {e}")
        raise

    print("\\n[OK] All D06 Acceptance criteria met. Raster reprojection is operational.")

if __name__ == "__main__":
    test_raster_processor_d06()
