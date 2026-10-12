
import logging
from typing import Any, Optional
import numpy as np

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from schemas.satellite_schema import GeospatialRasterAsset

class MissingModalityError(Exception):
    """Raised when a required satellite or DEM modality is absent."""
    pass

class InvalidModalityError(Exception):
    """Raised when a modality exists but contains no valid data (e.g. 100% cloud cover or NoData)."""
    pass

class GridMismatchError(Exception):
    """Raised when input modalities do not perfectly align to the target geospatial grid."""
    pass

class SatelliteSAROpticalFusionEngine:
    """Fuses multi-modal Earth Observation data (SAR, Optical, DEM) into aligned matrices."""

    def __init__(
        self,
        target_crs: str,
        target_resolution: tuple[float, float],
        target_bounds: tuple[float, float, float, float]
    ):
        """Initializes Fusion Engine with explicit target grid definition for geographic alignment."""
        self.target_crs = target_crs
        self.target_resolution = target_resolution
        self.target_bounds = target_bounds

    def _verify_alignment(self, asset: GeospatialRasterAsset, name: str) -> None:
        if asset.crs != self.target_crs:
            raise GridMismatchError(f"{name} CRS mismatch: expected {self.target_crs}, got {asset.crs}")
        if not np.allclose(asset.resolution, self.target_resolution, atol=1e-6):
            raise GridMismatchError(f"{name} Resolution mismatch: expected {self.target_resolution}, got {asset.resolution}")
        if not np.allclose(asset.bounds, self.target_bounds, atol=1e-6):
            raise GridMismatchError(f"{name} Bounds mismatch: expected {self.target_bounds}, got {asset.bounds}")
        if asset.raw_array.ndim != 3 or asset.raw_array.shape[0] != 1:
            raise GridMismatchError(f"{name} Dimensionality error: Expected (1, H, W) single-band raster.")

    def _process_modality(self, asset: Optional[GeospatialRasterAsset], name: str, required: bool = True) -> Optional[tuple[np.ndarray, np.ndarray, dict]]:
        if asset is None:
            if required:
                raise MissingModalityError(f"Required modality '{name}' is completely absent. Zero-filling fallback is prohibited.")
            return None
            
        self._verify_alignment(asset, name)
        
        if not np.any(asset.valid_data_mask):
            raise InvalidModalityError(f"Modality '{name}' is present but contains 100% invalid pixels (NoData or Clouds).")

        provenance = {
            "stac_item_id": asset.stac_item_id,
            "asset_key": asset.asset_key,
            "source_href": asset.source_href
        }
        
        arr = asset.raw_array[0].astype(np.float32)
        mask = asset.valid_data_mask[0]
        
        return arr, mask, provenance

    def create_fused_spatial_tensor(
        self,
        sar_vv: Optional[GeospatialRasterAsset],
        sar_vh: Optional[GeospatialRasterAsset],
        ndvi: Optional[GeospatialRasterAsset],
        ndmi: Optional[GeospatialRasterAsset],
        dem_elevation: Optional[GeospatialRasterAsset] = None,
        dem_slope: Optional[GeospatialRasterAsset] = None,
    ) -> dict[str, Any]:
        """
        Fuses explicitly provided SAR, Optical, and optionally DEM assets into a stacked multi-channel spatial tensor.
        Enforces strict grid alignment and missing modality policies.
        """

        vv_aligned, vv_mask, vv_prov = self._process_modality(sar_vv, "SAR_VV", required=True)
        vh_aligned, vh_mask, vh_prov = self._process_modality(sar_vh, "SAR_VH", required=True)
        ndvi_aligned, ndvi_mask, ndvi_prov = self._process_modality(ndvi, "OPTICAL_NDVI", required=True)
        ndmi_aligned, ndmi_mask, ndmi_prov = self._process_modality(ndmi, "OPTICAL_NDMI", required=True)
        
        ele_out = self._process_modality(dem_elevation, "DEM_ELEVATION", required=False)
        slope_out = self._process_modality(dem_slope, "DEM_SLOPE", required=False)

        # Compute SAR Cross-Polarization Ratio
        eps = 1e-6
        pol_ratio = vh_aligned / (vv_aligned + eps)
        pol_ratio_mask = vv_mask & vh_mask

        # Dynamic channel stacking preserving base indices 0-4
        stack_arrays = [vv_aligned, vh_aligned, pol_ratio, ndvi_aligned, ndmi_aligned]
        stack_masks = [vv_mask, vh_mask, pol_ratio_mask, ndvi_mask, ndmi_mask]
        channel_names = ["SAR_VV", "SAR_VH", "SAR_POL_RATIO", "OPTICAL_NDVI", "OPTICAL_NDMI"]
        prov_dict = {
            "SAR_VV": vv_prov,
            "SAR_VH": vh_prov,
            "OPTICAL_NDVI": ndvi_prov,
            "OPTICAL_NDMI": ndmi_prov
        }
        
        if ele_out is not None:
            stack_arrays.append(ele_out[0])
            stack_masks.append(ele_out[1])
            channel_names.append("DEM_ELEVATION")
            prov_dict["DEM_ELEVATION"] = ele_out[2]
            
        if slope_out is not None:
            stack_arrays.append(slope_out[0])
            stack_masks.append(slope_out[1])
            channel_names.append("DEM_SLOPE")
            prov_dict["DEM_SLOPE"] = slope_out[2]

        fused_tensor = np.stack(stack_arrays, axis=-1)
        combined_mask = np.stack(stack_masks, axis=-1)

        return {
            "tensor_shape": fused_tensor.shape,
            "channels": channel_names,
            "fused_tensor": fused_tensor,
            "fused_validity_mask": combined_mask,
            "provenance": prov_dict
        }

    def retrieve_surface_soil_moisture_proxy(self, fused_tensor: np.ndarray) -> np.ndarray:
        """Retrieves empirical Surface Soil Moisture Proxy."""
        vv = fused_tensor[:, :, 0]
        ndvi = fused_tensor[:, :, 3]
        ndmi = fused_tensor[:, :, 4]

        # Normalize SAR dB [-25, -5] -> [0.0, 1.0] proxy for soil dielectric constant
        sar_dielectric = np.clip((vv + 25.0) / 20.0, 0.0, 1.0)

        # Empirical retrieval combination
        soil_moisture_proxy = 0.50 * sar_dielectric + 0.35 * ndmi - 0.15 * ndvi

        # Volumetric Moisture Range Clipping (0.05 to 0.45 m3/m3 typical for topsoil)
        soil_moisture_volumetric = np.clip(soil_moisture_proxy, 0.05, 0.45)
        return np.round(soil_moisture_volumetric, 4)

if __name__ == "__main__":
    print("\n--- Testing D08 Modality policies moved to tests/test_satellite_fusion_d08.py ---")
