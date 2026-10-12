import os
import sys
import numpy as np
import rasterio
from rasterio.transform import from_origin

import importlib.util
cog_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '2_data_pipeline', 'preprocessing', 'cog_processor.py'))
spec = importlib.util.spec_from_file_location("cog_processor", cog_path)
cog_processor_mod = importlib.util.module_from_spec(spec)
sys.modules["cog_processor"] = cog_processor_mod
spec.loader.exec_module(cog_processor_mod)
COGRasterProcessor = cog_processor_mod.COGRasterProcessor
RasterReadError = cog_processor_mod.RasterReadError
InvalidWindowError = cog_processor_mod.InvalidWindowError

def create_deterministic_fixture(filepath: str):
    """Creates a small 3-band uint16 GeoTIFF for testing."""
    # 3 bands, 100x100
    data = np.zeros((3, 100, 100), dtype=np.uint16)
    data[0, :, :] = 1000 # Band 1
    data[1, :, :] = 2000 # Band 2
    data[2, :, :] = 3000 # Band 3
    
    # Add a nodata section (top left 10x10)
    data[:, 0:10, 0:10] = 0
    
    # Transform: Origin at 300000, 4000000, 10m resolution
    transform = from_origin(300000.0, 4000000.0, 10.0, 10.0)
    
    with rasterio.open(
        filepath,
        'w',
        driver='GTiff',
        height=100,
        width=100,
        count=3,
        dtype=str(data.dtype),
        crs='EPSG:32645',
        transform=transform,
        nodata=0
    ) as dst:
        dst.write(data)
        # We can also set scales/offsets if we want, but let's test defaults (None)
        
def test_cog_processor():
    fixture_path = "test_fixture.tif"
    create_deterministic_fixture(fixture_path)
    
    processor = COGRasterProcessor()
    
    print("--- Running T-FIX-01: Real pixel reading ---")
    try:
        asset = processor.read_raster_window(fixture_path)
        assert asset.raw_dtype == "uint16"
        assert asset.raw_array.shape == (3, 100, 100)
        assert asset.raw_array[0, 50, 50] == 1000
        assert asset.raw_array[1, 50, 50] == 2000
        assert asset.crs == "EPSG:32645"
        assert asset.nodata_value == 0
        
        # Check nodata mask
        assert asset.valid_data_mask[0, 5, 5] == False  # In the 0-10 nodata wedge
        assert asset.valid_data_mask[0, 50, 50] == True # Outside the nodata wedge
        print("[PASS] T-FIX-01: Real pixels successfully read. Metadata preserved. No synthetic data generated.")
    except Exception as e:
        print(f"[FAIL] T-FIX-01: {e}")
        raise
        
    print("\\n--- Running T-WIN-01: BBox/window behaviour ---")
    try:
        # BBox: [min_x, min_y, max_x, max_y]
        # Full raster bounds: (300000.0, 3999000.0, 301000.0, 4000000.0)
        # Let's request a 20x20 window inside
        bbox = [300500.0, 3999500.0, 300700.0, 3999700.0]
        
        asset_window = processor.read_raster_window(fixture_path, bbox=bbox)
        assert asset_window.raw_array.shape == (3, 20, 20)
        # Transform origin should now be Top-Left of the window: (300500.0, 3999700.0)
        assert asset_window.transform[2] == 300500.0
        assert asset_window.transform[5] == 3999700.0
        print("[PASS] T-WIN-01: Windowed read returned exact subset and updated affine transform.")
    except Exception as e:
        print(f"[FAIL] T-WIN-01: {e}")
        raise
        
    print("\\n--- Running T-ERR-01: Read failure ---")
    try:
        # Invalid bbox totally outside the raster
        invalid_bbox = [0.0, 0.0, 10.0, 10.0]
        try:
            processor.read_raster_window(fixture_path, bbox=invalid_bbox)
            raise AssertionError("Should have failed with InvalidWindowError")
        except InvalidWindowError:
            print("[PASS] T-ERR-01: Invalid window strictly rejected.")
            
        # Invalid file
        try:
            processor.read_raster_window("does_not_exist.tif")
            raise AssertionError("Should have failed with RasterReadError")
        except RasterReadError:
            print("[PASS] T-ERR-01: Unreadable source strictly rejected.")
            
    except Exception as e:
        print(f"[FAIL] T-ERR-01: {e}")
        raise

    # Cleanup
    if os.path.exists(fixture_path):
        os.remove(fixture_path)
        
    print("\\n✅ All acceptance criteria met. D01 is closed.")

if __name__ == "__main__":
    test_cog_processor()
