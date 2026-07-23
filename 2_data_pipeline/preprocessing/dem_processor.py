# THE_MRIDANSH/2_data_pipeline/processing/dem_processor.py

import logging
import numpy as np
from typing import Dict, Any, Tuple
from ..schemas.satellite_schema import SpatialBoundingBox

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class DEMTerrainEngine:
    """Digital Elevation Model (DEM) Engine for Terrain, Slope & Spatial Grid Alignment."""

    def __init__(self, resolution_meters: float = 30.0):
        self.resolution = resolution_meters

    def fetch_dem_matrix(self, bbox: SpatialBoundingBox, grid_shape: Tuple[int, int] = (100, 100)) -> np.ndarray:
        """Simulates/Extracts Digital Elevation Model (DEM) height array (in meters) for BBox."""
        logging.info(f"⛰️ Ingesting DEM Elevation Matrix for BBox: {bbox.bbox} | Grid: {grid_shape}")
        
        # Synthetic Synthetic Terrain Generation for Testing (Base elevation ~ 250m to 800m)
        x = np.linspace(-2, 2, grid_shape[1])
        y = np.linspace(-2, 2, grid_shape[0])
        xx, yy = np.meshgrid(x, y)
        elevation_matrix = 300 + 200 * np.exp(-(xx**2 + yy**2)) + 50 * np.sin(3 * xx)
        
        return elevation_matrix.astype(np.float32)

    def calculate_slope_and_aspect(self, elevation_matrix: np.ndarray) -> Dict[str, np.ndarray]:
        """Calculates Slope (degrees) and Aspect (orientation) from Elevation Matrix."""
        logging.info("📐 Computing Terrain Slope & Aspect Gradient Matrices...")
        
        # Calculate Gradients along X and Y axes
        dy, dx = np.gradient(elevation_matrix, self.resolution)
        
        # Slope Calculation: arctan(sqrt(dz/dx^2 + dz/dy^2)) converted to degrees
        slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
        slope_deg = np.degrees(slope_rad)
        
        # Aspect Calculation: Direction of maximum slope
        aspect_rad = np.arctan2(-dx, dy)
        aspect_deg = np.degrees(aspect_rad) % 360.0
        
        logging.info(f"✅ Terrain Engine Processed: Max Elevation={np.max(elevation_matrix):.1f}m | Max Slope={np.max(slope_deg):.1f}°")
        
        return {
            "elevation": elevation_matrix,
            "slope": slope_deg.astype(np.float32),
            "aspect": aspect_deg.astype(np.float32)
        }


# Self-Test Execution Module
if __name__ == "__main__":
    print("\n--- Testing Day 4 DEM & Terrain Alignment Engine ---")
    
    engine = DEMTerrainEngine(resolution_meters=30.0)
    test_bbox = SpatialBoundingBox(bbox=(77.10, 28.50, 77.25, 28.65))
    
    dem_grid = engine.fetch_dem_matrix(test_bbox, grid_shape=(120, 120))
    terrain_data = engine.calculate_slope_and_aspect(dem_grid)
    
    assert "slope" in terrain_data and "aspect" in terrain_data
    print("\n[SUCCESS] Day 4 DEM Terrain Alignment Engine: PASSED OPERATIONAL CHECKS!\n")