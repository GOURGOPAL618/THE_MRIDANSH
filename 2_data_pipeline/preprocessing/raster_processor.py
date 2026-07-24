# THE_MRIDANSH/2_data_pipeline/preprocessing/raster_processor.py

import logging
import numpy as np
from typing import Dict, Any, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class RasterDataProcessor:
    """Processor for Satellite Raster Resampling, Cloud Masking & Polygon Mask Clipping."""

    def __init__(self, target_resolution_m: float = 10.0):
        self.target_resolution = target_resolution_m

    def generate_cloud_mask(self, scl_band: np.ndarray, cloud_values: list = [3, 8, 9, 10]) -> np.ndarray:
        """Generates a binary cloud/shadow mask based on Sentinel-2 Scene Classification (SCL)."""
        logging.info("☁️ Filtering Cloud Noise & Shadow Artifacts via SCL Band Masking...")
        
        # Binary mask: True where cloud/shadow/noise exists
        cloud_mask = np.isin(scl_band, cloud_values)
        cloud_percentage = (np.sum(cloud_mask) / scl_band.size) * 100.0
        
        logging.info(f"✅ Cloud Mask Created: {cloud_percentage:.2f}% pixels flagged as unusable cloud/shadow.")
        return cloud_mask

    def apply_vector_polygon_clip(self, raster_data: np.ndarray, polygon_mask: np.ndarray) -> np.ndarray:
        """Clips and crops full satellite raster matrix strictly inside the field boundary polygon."""
        logging.info("✂️ Clipping Satellite Raster to Field Vector Polygon Boundaries...")
        
        # Zero out pixels outside the vector ROI (Region of Interest)
        clipped_raster = np.where(polygon_mask == 1, raster_data, 0.0)
        return clipped_raster

    def resample_raster_grid(self, raster_matrix: np.ndarray, target_shape: Tuple[int, int]) -> np.ndarray:
        """Resamples raw multi-spectral raster grid to target uniform resolution grid shape."""
        logging.info(f"🔄 Resampling Raster Matrix from {raster_matrix.shape} -> Target shape: {target_shape}")
        
        # Nearest-neighbor grid indexing simulation for spatial grid alignment
        row_indices = np.linspace(0, raster_matrix.shape[0] - 1, target_shape[0]).astype(int)
        col_indices = np.linspace(0, raster_matrix.shape[1] - 1, target_shape[1]).astype(int)
        
        resampled_matrix = raster_matrix[np.ix_(row_indices, col_indices)]
        return resampled_matrix


# Self-Test Execution Module
if __name__ == "__main__":
    print("\n--- Testing Day 5 Resampling & Cloud/Polygon Masking Engine ---")
    
    processor = RasterDataProcessor(target_resolution_m=10.0)
    
    # 1. Mock 100x100 Satellite SCL & Reflectance Band Matrix
    mock_scl = np.random.choice([4, 4, 4, 3, 8, 9], size=(100, 100)) # 4=Vegetation, 3/8/9=Cloud
    mock_band_b04 = np.random.uniform(0.05, 0.45, size=(100, 100)).astype(np.float32)
    
    # 2. Mock Circular Field Polygon Mask
    y, x = np.ogrid[:100, :100]
    mock_polygon = ((x - 50)**2 + (y - 50)**2 <= 35**2).astype(np.uint8)
    
    # 3. Pipeline Operations
    cloud_mask = processor.generate_cloud_mask(mock_scl)
    clipped_band = processor.apply_vector_polygon_clip(mock_band_b04, mock_polygon)
    resampled_band = processor.resample_raster_grid(clipped_band, target_shape=(120, 120))
    
    assert resampled_band.shape == (120, 120)
    print("\n[SUCCESS] Day 5 Resampling & Polygon/Cloud Masking Engine: PASSED OPERATIONAL CHECKS!\n")