"""
THE MRIDANSH : SAR/Optical Satellite Fusion Engine for Soil Moisture Retrieval (Day 16)
Combines Sentinel-1 SAR Backscatter (VV, VH) with Sentinel-2/Landsat Optical Indices
(NDVI, NDMI) and DEM Terrain attributes into a unified multi-modal spatial tensor.
"""

from typing import Any

import numpy as np


class SatelliteSAROpticalFusionEngine:
    """Fuses multi-modal Earth Observation data (SAR, Optical, DEM) into aligned matrices

    for physics-guided surface soil moisture retrieval algorithms.
    """

    def __init__(self, spatial_grid_shape: tuple[int, int] - (100, 100)):
        """Initializes Fusion Engine with standard target spatial grid dimensions.

        Parameters:
            spatial_grid_shape: Standard (height, width) matrix size for fused output
        """

        self.grid_shape = spatial_grid_shape

    def align_channel(
        self, channel_data: np.ndarray, target_shape: tuple[int, int]
    ) -> np.ndarray:
        """Resamples and aligns raw channel matrix to target spatial grid."""

        if channel_data.shape == target_shape:
            return channel_data

        rows = np.linspace(0, channel_data.shape[0] - 1, target_shape[0]).astype(int)

        cols = np.linspace(0, channel_data.shape[1] - 1, target_shape[1]).astype(int)
        return channel_data[np.ix_(rows, cols)]

    def create_fused_spatial_tensor(
        self,
        sar_vv: np.ndarray,
        sar_vh: np.ndarray,
        ndvi: np.ndarray,
        ndmi: np.ndarray,
        dem_elevation: np.ndarray,
        dem_slope: np.ndarray,
    ) -> dict[str, Any]:
        """Fuses SAR backscatter, Optical Vegetation/Moisture Indices, and DEM Terrain into

        a stacked 3D multi-channel spatial tensor (H x W x C).

        Channels:
        0: SAR VV Backscatter (dB)
        1: SAR VH Backscatter (dB)
        2: Cross-Polarization Ratio (VH / VV)
        3: NDVI (Vegetation Cover Index)
        4: NDMI (Vegetation/Soil Canopy Moisture)
        5: Elevation (m)
        6: Terrain Slope (deg)
        """

        # Step 1: Align all channels to target spatial grid
        vv_aligned = self.align_channel(sar_vv, self.grid_shape)
        vh_aligned = self.align_channel(sar_vh, self.grid_shape)
        ndvi_aligned = self.align_channel(ndvi, self.grid_shape)
        ndmi_aligned = self.align_channel(ndmi, self.grid_shape)
        ele_aligned = self.align_channel(dem_elevation, self.grid_shape)
        slope_aligned = self.align_channel(dem_slope, self.grid_shape)

        # Step 2: Compute SAR Cross-Polarization Ratio (Pol Ratio = VH - VV in dB domain, or VH / VV in linear)
        eps = 1e-6
        pol_ratio = vh_aligned / (vv_aligned + eps)

        # Step 3: Multi Channel Stacking (Height, Width, Channels)
        fused_tensor = np.stack(
            [
                vv_aligned,
                vh_aligned,
                pol_ratio,
                ndvi_aligned,
                ndmi_aligned,
                ele_aligned,
                slope_aligned,
            ],
            axis=-1,
        )

        return {
            "tensor_shape": fused_tensor.shape,
            "channels": [
                "SAR_VV",
                "SAR_VH",
                "SAR_POL_RATIO",
                "OPTICAL_NDVI",
                "OPTICAL_NDMI",
                "DEM_ELEVATION",
                "DEM_SLOPE",
            ],
            "fused_tensor": fused_tensor,
        }

    def retrieve_surface_soil_moisture_proxy(
        self, fused_tensor: np.ndarray
    ) -> np.ndarray:
        """Retrieves empirical Surface Soil Moisture Proxy (volumetric % m3/m3)

        combining SAR radar dielectric response and Optical canopy moisture.

        Retrieval Physics Proxy Formula:
        Soil_Moisture = w1 * SAR_dielectric_factor + w2 * NDMI_moisture - w3 * NDVI_attenuation
        """

        vv = fused_tensor[:, :, 0]
        vh = fused_tensor[:, :, 1]
        ndvi = fused_tensor[:, :, 3]
        ndmi = fused_tensor[:, :, 4]

        # Normalize SAR dB [-25, -5] -> [0.0, 1.0] proxy for soil dielectric constant
        sar_dielectric = np.clip((vv + 25.0) / 20.0, 0.0, 1.0)

        # Empirical retrieval combination
        soil_moisture_proxy = 0.50 * sar_dielectric + 0.35 * ndmi - 0.15 * ndvi

        # Volumetric Moisture Range Clipping (0.05 to 0.45 m3/m3 typical for topsoil)
        soil_moisture_volumetric = np.clip(soil_moisture_proxy, 0.05, 0.45)

        return np.round(soil_moisture_volumetric, 4)


# Quick Verification Test
if __name__ == "__main__":
    print("🛰️ Testing Day 16 SAR/Optical Fusion Engine & Soil Moisture Retrieval...")
    fusion_engine = SatelliteSAROpticalFusionEngine(spatial_grid_shape=(100, 100))

    # synthetic multi-model inputs (100 * 100 spatial grid)
    np.random.seed(42)
    mock_vv = np.random.uniform(-20.0, -8.0, (100, 100))
    mock_vh = np.random.uniform(-25.0, -12.0, (100, 100))
    mock_ndvi = np.random.uniform(0.2, 0.7, (100, 100))
    mock_ndmi = np.random.uniform(0.1, 0.5, (100, 100))
    mock_elev = np.random.uniform(40.0, 120.0, (100, 100))
    mock_slope = np.random.uniform(1.0, 12.0, (100, 100))

    print("\n1. Fusing SAR, Optical, and DEM Observables into Tensor...")
    result = fusion_engine.create_fused_spatial_tensor(
        sar_vv=mock_vv,
        sar_vh=mock_vh,
        ndvi=mock_ndvi,
        ndmi=mock_ndmi,
        dem_elevation=mock_elev,
        dem_slope=mock_slope,
    )

    print(f"   Fused Tensor Shape (H, W, C): {result['tensor_shape']}")
    print(f"   Fused Channels ({len(result['channels'])}): {result['channels']}")

    print("\n2. Executing Surface Soil Moisture Retrieval Proxy...")
    sm_retrieved = fusion_engine.retrieve_surface_soil_moisture_proxy(
        result["fused_tensor"]
    )

    print(f"   Retrieved Soil Moisture Shape: {sm_retrieved.shape}")
    print(
        f"   Soil Moisture Range: [{sm_retrieved.min():.4f} - {sm_retrieved.max():.4f}] m³/m³"
    )
    print(f"   Mean Surface Moisture: {sm_retrieved.mean():.4f} m³/m³")

    print("\n✅ Day 16 SAR/Optical Fusion Engine Verification Complete!")
