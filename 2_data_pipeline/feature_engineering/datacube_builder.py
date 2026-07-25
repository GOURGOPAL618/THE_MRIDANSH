# THE MRIDANSH - DATA CUBE BUILDER
# Multi-Modal Feature Stacking & Data Cube Generation Engine

import logging
import numpy as np
from typing import Dict, Any, List

logging.basicConfig(level = logging.INFO, format = "%(asctime)s - %(levelname)s - %(message)s")

class DataCubeBuilderEngine:
    """Engine For Merging Multi-Spectral Satellite, SAR Radar, and DEM Terrain Matrices into a Unified Data Cube Tensor."""


    def __init__(self, target_shape: tuple = (120, 120)):
        self.target_shape = target_shape

    def build_feature_datacube(
        self,
        optical_bands: Dict[str, np.ndarray],
        sar_bands: Dict[str, np.ndarray],
        dem_matrices: Dict[str, np.ndarray]
    ) -> Dict[str, Any]:

        """Fuses Multi-model geospatial layers into a unified feature tensor block."""
        logging.info("🧊 Initialize Multi-model Data Cube Fusion Sequence...")

        feature_layers = []
        band_names = []

        # 1. Stack Optical Multi-Spectral Bands (e.g., B0, B03, B04, B08)
        for name, matrix in optical_bands.items():
            feature_layers.append(matrix)
            band_names.append(f"OPTICAL_{name}")

        # 2. Stack Synthetic Aperture RADAR (SAR) Bands (eg., VV, VH)
        for name, matrix in sar_bands.items():
            feature_layers.append(matrix)
            band_names.append(f"SAR_{name}")

        # 3. Stack Elevation & Slope Terrain Matrices
        for name, matrix in dem_matrices.items():
            feature_layers.append(matrix)
            band_names.append(f"TERRAIN_{name.upper()}")

        # 4. Concatenate along channel axis -> Shape: (HEIGHT, WIDTH, CHANNELS)
        datacube_tensor = np.stack(feature_layers, axis = -1).astype(np.float32)

        logging.info(
            f"✅ Multi-Model Data Cube Generated Successfully!\n"
            f"   -> Tensor Shape: {datacube_tensor.shape} (H * W * Channels)\n"
            f"   -> Enclosed Channels: {band_names}"
        )

        return {
            "datacube": datacube_tensor,
            "channels": band_names,
            "spatial_shape": datacube_tensor.shape[:2],
            "total_channels": datacube_tensor.shape[-1]
        }


# Self-Test Execution Module
if __name__ == "__main__":
    print("\n--- Testing Day 6 Multi-Modal Data Cube Fusion Engine ---")

    shape = (120, 120)
    builder = DataCubeBuilderEngine(target_shape = shape)

    #  Mock Input Matrices (day 3 + day 4 + day 5 Outputs)
    mock_optical = {
        "B02": np.random.rand(*shape),
        "B03": np.random.rand(*shape),
        "B04": np.random.rand(*shape),
        "B08": np.random.rand(*shape)
    }

    mock_sar = {
        "VV": np.random.rand(*shape),
        "VH": np.random.rand(*shape)
    }

    mock_dem = {
        "elevation": np.random.rand(*shape),
        "slope": np.random.rand(*shape)
    }

    # Execute Data Cube Construction
    result = builder.build_feature_datacube(mock_optical, mock_sar, mock_dem)

    assert result["datacube"].shape == (120, 120, 8)    # 4 Optical + 2 SAR + 2 Terrain = 8 Channels
    print("\n[SUCCESS] Day 6 Multi-Modal Data Cube Engine: PASSED OPERATIONAL CHECKS!\n")