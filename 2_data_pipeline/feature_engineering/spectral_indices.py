# THE MRIDANSH - spectral_indices.py

import logging
import numpy as np
from typing import Dict

logging.basicConfig(level = logging.INFO, format = "%(astime)s - %(lavelname)s - %(message)s")

class VegetationIndicesEngine:
    """Calculate Spectral Vegetation & Water Indices (NDVI, NDWI, EVI, SAVI) From Sentinel-2 Optical Bands."""

    def calculate_ndvi(self, red: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """Normalized Difference Vegetation Index: (NIR - Red) / (NIR + Red)"""
        denom = nir + red + 1e-8
        ndvi = (nir - red) / denom
        return np.clip(ndvi, -1.0, 1.0).astype(np.float32)

    def calculate_ndwi(self, green: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """Normalized Difference Water Index: (Green - NIR) / (Green + NIR)"""
        denom = green + nir + 1e-8
        ndwi = (green - nir) / denom
        return np.clip(ndwi, -1.0, 1.0).astype(np.float32)

    def calculate_evi(self, blue: np.ndarray, nir: np.ndarray, red: np.ndarray) -> np.ndarray:
        """Enhanced Vegetation Index: 2.5 * ((NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1))"""
        denom = nir + 6.0 * red - 7.5 * blue + 1.0 + 1e-8
        evi = 2.5 * ((nir - red) / denom)
        return np.clip(evi, -1.0, 1.0).astype(np.float32)

    def calculate_savi(self, red: np.ndarray, nir: np.ndarray, l_factor: float = 0.5) -> np.ndarray:
        """Soil-Adjusted Vegetation Index: ((NIR - Red) / (NIR + Red + L)) * (1 + L)"""
        denom = nir + red + l_factor + 1e-8
        savi = ((nir - red) / denom) * (1.0 + l_factor)
        return np.clip(savi, -1.0, 1.0).astype(np.float32)

    def compute_all_indices(self, optical_bands: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Calculates all spectral indices using B02 (Blue), B03 (Green), B04 (Red), B08 (NIR)."""
        logging.info("🌿 Computing Spectral Indices (NDVI, NDWI, EVI, SAVI)...")

        blue = optical_bands["B02"]
        green = optical_bands["B03"]
        red = optical_bands["B04"]
        nir = optical_bands["B08"]

        indices = {
            "NDVI": self.calculate_ndvi(red, nir),
            "NDWI": self.calculate_ndwi(green, nir),
            "EVI": self.calculate_evi(blue, red, nir),
            "SAVI": self.calculate_savi(red, nir)
        }

        logging.info("✅ All 4 Spectral Indices Calculated Successfully!")
        return indices


# Self-Test Execution Module
if __name__ == "__main__":
    print("\n--- Testing Spectral Vegetation Indices Engine ---")

    engine = VegetationIndicesEngine()
    shape = (120, 120)

    mock_optical = {
        "B02": np.random.uniform(0.01, 0.15, size = shape),
        "B03": np.random.uniform(0.02, 0.20, size = shape),
        "B04": np.random.uniform(0.02, 0.25, size = shape),
        "B08": np.random.uniform(0.15, 0.50, size = shape)
    }

    results = engine.compute_all_indices(mock_optical)

    assert "NDVI" in results and "NDWI" in results and "EVI" in results and "SAVI" in results
    assert results["NDVI"].shape == (120, 120)

    print("\n[SUCCESS] Spectral Indices Engine: PASSED OPERATIONAL CHECKS!\n")