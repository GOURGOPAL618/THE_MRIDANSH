"""
MRIDANSH : Cloud-Optimized GeoTIFF (COG) Ingestor & Raster Processor (Day 15)
Handles HTTP/S3 remote raster windowed streaming, resampling to unified grids,
and NoData masking for Earth Observation workflows.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np  

class COGRasterProcessor:
    """ Streams and Processes Remote Cloud-Optimized GeoTIFF (COG) rasters."""

    def __init__(self, target_resolution: float = 10.0):
        """Initializes COG Processor with target pixel resolution (meters).

        Parameters:
            target_resolution: Standard grid pixel size in meters (default 10m for Sentinel-2)
        """

        self.target_resolution = target_resolution

    def window_read_synthetic_raster(
        self,
        cog_url: str,
        bbox: List[float],
        target_shape: Tuple[int, int] = (100, 100),
    ) -> Dict[str, Any]:
        """Simulates windowed spatial streaming from a remote COG asset URL

        over a bounding box without downloading the entire file.

        Parameters:
            cog_url: Remote HTTP/S3 URL for the COG asset
            bbox: [min_lon, min_lat, max_lon, max_lat]
            target_shape: (height, width) array dimensions
        """

        # seed generator based on URL hash for deterministic simulation
        url_seed = abs(hash(cog_url)) % (2 ** 32)
        np.random.seed(url_seed)

        # Generate realistic reflectances (0.0 - 1.0) with some NaN NoData values
        raw_band = np.random.uniform(0.02, 0.85, size = target_shape)

        # Inject Simulated Cloud/NoData Mask (5% Noise)
        mask = np.random.choice(
            [True, False], size = target_shape, p = [0.05, 0.95]
        )
        raw_band[mask] = np.nan

        return {
            "source_url": cog_url,
            "bbox": bbox,
            "crs": "EPSG:4326",
            "resolution": self.target_resolution,
            "shape": target_shape,
            "data": raw_band,
        }

    def align_and_resample(
        self, raster_data: np.ndarray, target_shape: Tuple[int, int]
    ) -> np.ndarray:
        """Resamples a 2D raster array to match a unified target spatial grid.

        Parameters:
            raster_data: 2D numpy array
            target_shape: Desired (rows, cols) dimensions
        """

        if raster_data.shape == target_shape:
            return raster_data

        # Simple Nearest-neighbour grid interpolation for raster alignment
        row_indices = np.linspace(
            0, raster_data.shape[0] - 1, target_shape[0]
        ).astype(int)

        col_indices = np.linspace(
            0, raster_data.shape[1] - 1, target_shape[1]
        ).astype(int)

        resampled = raster_data[np.ix_(row_indices, col_indices)]
        return resampled

    def clean_and_normalize_raster(
        self,
        raster_data: np.ndarray,
        valid_range: Tuple[float, float] = (0.0, 1.0),
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Handles NaN/NoData values via linear interpolation and normalizes values.

        Parameters:
            raster_data: Raw raster array with potential NaNs
            valid_range: Expected range (min, max) for clipping
        """

        data = raster_data.copy()
        nan_mask = np.isnan(data)
        nan_count = int(np.sum(nan_mask))

        # Fill Nans with regional valid median
        if nan_count > 0:
            valid_median = np.nanmedian(data)
            if np.isnan(valid_median):
                valid_median = 0.0
            data[nan_mask] = valid_median

        # Clip Values to valid reflectance range
        cleaned = np.clip(data, valid_range[0], valid_range[1])

        metadata = {
            "total_pixels": data.size,
            "nan_filled_count": nan_count,
            "nan_percentage": float(
                np.round((nan_count / data.size) * 100, 2)
            ),
            "min_val": float(np.round(np.min(cleaned), 4)),
            "max_val": float(np.round(np.max(cleaned), 4)),
            "mean_val": float(np.round(np.mean(cleaned), 4)),
        }

        return cleaned, metadata


# Quick Verification Test
if __name__ == "__main__":
    print("🛰️ Testing Day 15 COG Processor & Raster Ingestor...")
    processor = COGRasterProcessor(target_resolution = 10.0)

    # Bhubaneswar Corriodor Bounding Box
    bhubaneswar_bbox = [85.75, 20.20, 85.90, 20.35]
    sample_cog_url = "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/45/Q/UC/2026/6/S2B_45QUC_20260605_0_L2A/B04.tif"

    print("\n1. Simulating Spatial Window Read from Remote COG...")
    raster_result = processor.window_read_synthetic_raster(
        cog_url = sample_cog_url, bbox = bhubaneswar_bbox, target_shape = (120, 120)
    )

    print(f"   Fetched Band Shape: {raster_result['shape']}")
    print(f"   Target CRS: {raster_result['crs']}")

    print("\n2. Aligning & Resampling to Standard Grid (100x100)...")
    resampled_data = processor.align_and_resample(
        raster_data = raster_result["data"], target_shape = (100, 100)
    )

    print(f"   Resampled Shape: {resampled_data.shape}")

    print("\n3. Cleaning NoData/NaN Mask & Normalizing...")
    cleaned_raster, meta = processor.clean_and_normalize_raster(resampled_data)
    print(f"   Total Pixels: {meta['total_pixels']}")
    print(f"   NaN Pixels Filled: {meta['nan_filled_count']} ({meta['nan_percentage']}%)")
    print(f"   Pixel Value Range: [{meta['min_val']} - {meta['max_val']}]")
    print(f"   Mean Reflectance: {meta['mean_val']}")

    print("\n✅ Day 15 COG & Raster Ingestor Verification Complete!")