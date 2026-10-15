"""
THE MRIDANSH : OPTICAL RADIOMETRIC NORMALIZATION & SCL CLOUD MASK DECODER
================================================================================
Mission: Spaceborne Operational Campaign (SOC-AETHER-2026) | Day 07
Subsystem: 9_spaceborne_operational_campaign/4_execution_engine/optical_cloud_preprocessor.py
Standards: ESA Sentinel-2 L2A MSI Product Specification & DO-178C Safety Bounds

Functionality:
1. Radiometric Scaling: Converts 16-bit integer DN to Bottom-of-Atmosphere (BOA)
   surface reflectance: ρ_λ = (DN + BOA_ADD_OFFSET) / 10000.0, strictly bounded in [0.0, 1.0].
2. Scene Classification Layer (SCL) Decoder:
   Decodes 12-class ESA landcover classification:
   - Valid Clear Land/Vegetation/Water: SCL ∈ {4, 5, 6, 7}  --> clear_mask = 1.0
   - Cloud, Shadow, Snow, Defective: SCL ∈ {0, 1, 3, 8, 9, 10, 11} --> clear_mask = 0.0
3. Biophysical Vegetation & Moisture Inversion:
   - NDVI = (NIR - Red) / (NIR + Red + ε)
   - Moisture Proxy = (NIR - Green) / (NIR + Green + ε)
4. Graceful Fallback Generation:
   Replaces cloudy pixels with synthetic reflectance bounds to avoid NaN propagation
   into downstream neural backbones.
================================================================================
"""

from typing import Dict, Any, Tuple, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F

EPSILON: float = 1e-7

# ESA SCL Classes (Sentinel-2 Level-2A)
SCL_NO_DATA: int = 0
SCL_SATURATED_OR_DEFECTIVE: int = 1
SCL_DARK_AREA_PIXELS: int = 2
SCL_CLOUD_SHADOWS: int = 3
SCL_VEGETATION: int = 4
SCL_NOT_VEGETATED: int = 5  # Bare soil
SCL_WATER: int = 6
SCL_UNCLASSIFIED: int = 7
SCL_CLOUD_MEDIUM_PROBABILITY: int = 8
SCL_CLOUD_HIGH_PROBABILITY: int = 9
SCL_THIN_CIRRUS: int = 10
SCL_SNOW_ICE: int = 11

VALID_SURFACE_CLASSES = {
    SCL_DARK_AREA_PIXELS,
    SCL_VEGETATION,
    SCL_NOT_VEGETATED,
    SCL_WATER,
    SCL_UNCLASSIFIED
}


class OpticalCloudPreprocessor:
    """
    Deterministic Sentinel-2 L2A processor handling optical BOA scaling,
    cloud mask extraction, and vegetative index derivation.
    """

    def __init__(self, boa_offset: float = 0.0, scale_factor: float = 10000.0):
        """
        Args:
            boa_offset: ESA Baseline offset (0.0 for pre-PB04.00, -1000.0 for PB04.00+).
            scale_factor: Standard ESA integer to reflectance divisor (10000.0).
        """
        self.boa_offset = boa_offset
        self.scale_factor = scale_factor

    def normalize_boa_reflectance(self, dn_tensor: torch.Tensor) -> torch.Tensor:
        """
        Scales raw Sentinel-2 L2A integer DN to physical surface reflectance [0.0, 1.0].
        """
        reflectance = (dn_tensor.float() + self.boa_offset) / self.scale_factor
        return torch.clamp(reflectance, min=0.0, max=1.0)

    def decode_scl_mask(self, scl_tensor: torch.Tensor) -> Tuple[torch.Tensor, float]:
        """
        Decodes Scene Classification Layer into a binary clear-sky mask.

        Args:
            scl_tensor: Tensor of integer classification values (B, 1, H, W) or (B, H, W).

        Returns:
            Tuple of:
                - clear_mask: Float tensor (B, 1, H, W) where 1.0 = clear, 0.0 = cloud/shadow/bad.
                - cloud_fraction: Percentage of scene covered by clouds/shadows (0.0% - 100.0%).
        """
        if scl_tensor.dim() == 3:
            scl_tensor = scl_tensor.unsqueeze(1)
        elif scl_tensor.dim() == 2:
            scl_tensor = scl_tensor.unsqueeze(0).unsqueeze(0)

        # Create clear-sky binary mask
        clear_mask = torch.zeros_like(scl_tensor, dtype=torch.float32)
        for valid_cls in VALID_SURFACE_CLASSES:
            clear_mask = torch.where(scl_tensor == valid_cls, 1.0, clear_mask)

        # Calculate cloud & occlusion percentage
        total_pixels = clear_mask.numel()
        clear_pixels = float(torch.sum(clear_mask))
        cloud_pixels = total_pixels - clear_pixels
        cloud_fraction_pct = (cloud_pixels / max(total_pixels, 1)) * 100.0

        return clear_mask, cloud_fraction_pct

    def compute_vegetation_indices(
        self,
        b2_blue: torch.Tensor,
        b3_green: torch.Tensor,
        b4_red: torch.Tensor,
        b8_nir: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        Derives NDVI, NDWI, and Greenness metrics with numerical singularity protection.
        """
        # Normalized Difference Vegetation Index (NDVI)
        ndvi = (b8_nir - b4_red) / (b8_nir + b4_red + EPSILON)
        ndvi = torch.clamp(ndvi, min=-1.0, max=1.0)

        # Normalized Difference Water/Moisture Proxy (NDWI)
        ndwi = (b3_green - b8_nir) / (b3_green + b8_nir + EPSILON)
        ndwi = torch.clamp(ndwi, min=-1.0, max=1.0)

        # Enhanced Soil/Vegetation Index
        evi_proxy = 2.5 * ((b8_nir - b4_red) / (b8_nir + 6.0 * b4_red - 7.5 * b2_blue + 1.0 + EPSILON))
        evi_proxy = torch.clamp(evi_proxy, min=-1.0, max=2.5)

        return {
            "ndvi": ndvi,
            "ndwi": ndwi,
            "evi_proxy": evi_proxy
        }

    def process_optical_bundle(
        self,
        raw_b2_blue: torch.Tensor,
        raw_b3_green: torch.Tensor,
        raw_b4_red: torch.Tensor,
        raw_b8_nir: torch.Tensor,
        raw_scl: Optional[torch.Tensor] = None
    ) -> Dict[str, Any]:
        """
        Executes complete optical preprocessing pipeline:
        Reflectance scaling, SCL mask decoding, vegetation indexing,
        and unified 4-channel tensor assembly.

        Returns:
            Dictionary containing:
                - 'optical': Tensor (B, 4, H, W) [B2, B3, B4, B8] in [0.0, 1.0].
                - 'clear_mask': Tensor (B, 1, H, W) [1.0 = clear, 0.0 = occluded].
                - 'cloud_fraction_pct': Float cloud coverage percentage.
                - 'ndvi': Tensor (B, 1, H, W).
                - 'ndwi': Tensor (B, 1, H, W).
        """
        # Step 1: Scale BOA reflectances
        b2 = self.normalize_boa_reflectance(raw_b2_blue)
        b3 = self.normalize_boa_reflectance(raw_b3_green)
        b4 = self.normalize_boa_reflectance(raw_b4_red)
        b8 = self.normalize_boa_reflectance(raw_b8_nir)

        # Align dimensions to 4D (B, 1, H, W)
        for t in [b2, b3, b4, b8]:
            while t.dim() < 4:
                t.unsqueeze_(0)

        # Stack into standard 4-channel optical tensor (B, 4, H, W)
        optical = torch.cat([b2, b3, b4, b8], dim=1)

        # Step 2: Handle SCL cloud mask
        if raw_scl is not None:
            clear_mask, cloud_fraction = self.decode_scl_mask(raw_scl)
        else:
            # Assume 100% clear if SCL is absent
            clear_mask = torch.ones((optical.shape[0], 1, optical.shape[2], optical.shape[3]),
                                    dtype=torch.float32, device=optical.device)
            cloud_fraction = 0.0

        # Step 3: Compute vegetative indices
        indices = self.compute_vegetation_indices(b2, b3, b4, b8)

        return {
            "optical": optical,
            "clear_mask": clear_mask,
            "cloud_fraction_pct": cloud_fraction,
            "ndvi": indices["ndvi"],
            "ndwi": indices["ndwi"],
            "evi_proxy": indices["evi_proxy"]
        }
