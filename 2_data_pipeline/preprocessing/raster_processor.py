import logging
import numpy as np
from rasterio.warp import reproject, Resampling
from rasterio.transform import Affine

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from schemas.satellite_schema import GeospatialRasterAsset

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class GridAlignmentError(Exception):
    """Raised when the target grid is physically or mathematically invalid."""
    pass

class RasterDataProcessor:
    """Processor for Satellite Raster Resampling, Cloud Masking & Grid Alignment."""

    def __init__(self, target_resolution_m: float = 10.0):
        self.target_resolution = target_resolution_m

    def reproject_asset(
        self,
        asset: GeospatialRasterAsset,
        target_crs: str,
        target_resolution: tuple[float, float],
        target_bounds: tuple[float, float, float, float],
        is_categorical: bool = False
    ) -> GeospatialRasterAsset:
        """
        Geospatially aligns a raster asset to a strict target grid via physical reprojection.
        """
        logging.info(f"🌐 Aligning Raster to CRS {target_crs} | Res: {target_resolution} | Bounds: {target_bounds}")

        min_x, min_y, max_x, max_y = target_bounds
        res_x, res_y = target_resolution

        if res_x <= 0 or res_y <= 0:
            raise GridAlignmentError(f"Invalid target grid: resolution must be positive. Got {target_resolution}")
        if min_x >= max_x or min_y >= max_y:
            raise GridAlignmentError(f"Invalid target grid: minimum bounds must be less than maximum. Got {target_bounds}")

        width = int(round((max_x - min_x) / res_x))
        height = int(round((max_y - min_y) / res_y))

        if width <= 0 or height <= 0:
            raise GridAlignmentError(f"Invalid target grid: calculated dimensions (W:{width}, H:{height}) are empty.")

        target_transform = Affine.translation(min_x, max_y) * Affine.scale(res_x, -res_y)
        src_transform = Affine(*asset.transform)

        # Skip resampling if the grids are mathematically identical
        if (asset.crs == target_crs and 
            target_transform == src_transform and 
            width == asset.raw_array.shape[2] and 
            height == asset.raw_array.shape[1]):
            logging.info("✅ Grids identical. Returning raw native asset.")
            return asset

        # Define Resampling Method
        resampling = Resampling.nearest if is_categorical else Resampling.bilinear

        # Execute Raw Data Reprojection
        dest_array = np.zeros((asset.raw_array.shape[0], height, width), dtype=asset.raw_array.dtype)
        
        reproject(
            source=asset.raw_array,
            destination=dest_array,
            src_transform=src_transform,
            src_crs=asset.crs,
            dst_transform=target_transform,
            dst_crs=target_crs,
            src_nodata=asset.nodata_value,
            dst_nodata=asset.nodata_value,
            resampling=resampling
        )

        # Execute Mask Reprojection Strictly using Nearest
        dest_mask = np.zeros((1, height, width), dtype=np.uint8)
        source_mask_uint8 = asset.valid_data_mask.astype(np.uint8) * 255
        
        reproject(
            source=source_mask_uint8,
            destination=dest_mask,
            src_transform=src_transform,
            src_crs=asset.crs,
            dst_transform=target_transform,
            dst_crs=target_crs,
            src_nodata=0,
            dst_nodata=0,
            resampling=Resampling.nearest
        )
        out_mask = dest_mask.astype(bool)

        return GeospatialRasterAsset(
            raw_array=dest_array,
            raw_dtype=asset.raw_dtype,
            scale_factor=asset.scale_factor,
            add_offset=asset.add_offset,
            crs=target_crs,
            transform=tuple(target_transform)[:6],
            bounds=target_bounds,
            resolution=target_resolution,
            valid_data_mask=out_mask,
            nodata_value=asset.nodata_value,
            stac_item_id=asset.stac_item_id,
            asset_key=asset.asset_key,
            source_href=asset.source_href,
            acquisition_datetime=asset.acquisition_datetime
        )

# Self-Test Execution Module
if __name__ == "__main__":
    print("\n--- Testing D06 Reprojection & Grid Alignment moved to tests/test_raster_processor_d06.py ---")
