"""
THE MRIDANSH — AETHER-MRID1607X CENTRAL ENGINE
Module: 3_core_engine/models/latent_fusion.py
Role: Production-Grade Multi-Modal Satellite Latent Fusion Manifold

Extracts and unifies multi-sensor satellite Earth observation tensors
(Sentinel-1 microwave SAR, Sentinel-2 optical MSI/indices, and SRTM DEM)
into a continuous, strictly-bounded 64-dimensional latent manifold.

Key Features:
- Dedicated per-modality convolutional representation encoders.
- Dynamic fault-tolerant optical occlusion gate (100% cloud cover fallback).
- Bounded 64-channel residual latent projection.
- Pure PyTorch, zero external notebook dependencies, fully deterministic.
"""

from typing import Any, Dict, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F


class ResidualConvBlock(nn.Module):
    """Residual convolutional block with GroupNorm and GELU activations."""

    def __init__(self, channels: int):
        super(ResidualConvBlock, self).__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False)
        self.gn1 = nn.GroupNorm(num_groups=min(8, channels), num_channels=channels)
        self.act1 = nn.GELU()
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False)
        self.gn2 = nn.GroupNorm(num_groups=min(8, channels), num_channels=channels)
        self.act2 = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        out = self.act1(self.gn1(self.conv1(x)))
        out = self.gn2(self.conv2(out))
        return self.act2(out + residual)


class MultiModalLatentFusion(nn.Module):
    """
    Multi-Modal Latent Fusion Manifold (AETHER-MRID1607X).
    
    Fuses:
      1. SAR Microwave backscatter (VV, VH, PolRatio) -> 32 latent channels
      2. Optical reflectances / indices (NDVI, NDMI, etc.) -> 32 latent channels
      3. Topographic DEM (Elevation, Slope) -> 16 latent channels
    
    Projects into unified 64-dimensional spatiotemporal latent manifold.
    Enforces dynamic resilience under 100% optical cloud occlusion dropout.
    """

    def __init__(
        self,
        sar_channels: int = 3,
        optical_channels: int = 2,
        dem_channels: int = 2,
        latent_dim: int = 64,
    ):
        super(MultiModalLatentFusion, self).__init__()
        self.sar_channels = sar_channels
        self.optical_channels = optical_channels
        self.dem_channels = dem_channels
        self.latent_dim = latent_dim

        # 1. SAR Microwave Feature Extractor (3 -> 32)
        self.sar_encoder = nn.Sequential(
            nn.Conv2d(sar_channels, 32, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(num_groups=8, num_channels=32),
            nn.GELU(),
            ResidualConvBlock(32),
        )

        # 2. Optical Feature Extractor (2 -> 32)
        self.optical_encoder = nn.Sequential(
            nn.Conv2d(optical_channels, 32, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(num_groups=8, num_channels=32),
            nn.GELU(),
            ResidualConvBlock(32),
        )

        # 3. Topographic DEM Feature Extractor (2 -> 16)
        self.dem_encoder = nn.Sequential(
            nn.Conv2d(dem_channels, 16, kernel_size=3, padding=1, bias=False),
            nn.GroupNorm(num_groups=4, num_channels=16),
            nn.GELU(),
            ResidualConvBlock(16),
        )

        # 4. Cross-Modal Fusion Bottleneck (32 + 32 + 16 = 80 -> latent_dim)
        total_in_features = 32 + 32 + 16
        self.fusion_projection = nn.Sequential(
            nn.Conv2d(total_in_features, latent_dim, kernel_size=1, bias=False),
            nn.GroupNorm(num_groups=8, num_channels=latent_dim),
            nn.GELU(),
            ResidualConvBlock(latent_dim),
        )

        # Learnable fallback parameters for cloud occlusion
        self.sar_amplification_weight = nn.Parameter(torch.tensor(1.25, dtype=torch.float32))

    def forward(
        self,
        sar: torch.Tensor,
        optical: torch.Tensor,
        dem: torch.Tensor,
        optical_dropout: bool = False,
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Executes multi-modal latent fusion forward pass.

        Parameters:
        -----------
        sar : torch.Tensor
            Microwave SAR tensor of shape (B, sar_channels, H, W).
        optical : torch.Tensor
            Optical reflectances / index tensor of shape (B, optical_channels, H, W).
        dem : torch.Tensor
            Topography elevation and slope tensor of shape (B, dem_channels, H, W).
        optical_dropout : bool
            If True, simulates 100% cloud cover. The optical branch is suppressed,
            and the SAR microwave backbone takes over with zero NaNs.

        Returns:
        --------
        Tuple[torch.Tensor, Dict[str, Any]]:
            - latent_manifold : Tensor of shape (B, latent_dim, H, W)
            - metadata : Diagnostic telemetry dictionary
        """
        # Dimensionality assertions
        if sar.dim() != 4:
            raise ValueError(f"Expected 4D SAR tensor (B, C, H, W), got shape {sar.shape}")
        if optical.dim() != 4:
            raise ValueError(f"Expected 4D Optical tensor (B, C, H, W), got shape {optical.shape}")
        if dem.dim() != 4:
            raise ValueError(f"Expected 4D DEM tensor (B, C, H, W), got shape {dem.shape}")

        b, _, h, w = sar.shape

        # 1. Encode SAR microwave features
        f_sar = self.sar_encoder(sar)

        # 2. Encode Optical features (with dynamic cloud occlusion logic)
        if optical_dropout:
            # 100% Cloud Occlusion: Zero out optical features, amplify SAR backbone
            f_optical = torch.zeros(b, 32, h, w, device=optical.device, dtype=optical.dtype)
            f_sar = f_sar * self.sar_amplification_weight
            active_optical = False
        else:
            f_optical = self.optical_encoder(optical)
            active_optical = True

        # 3. Encode Topography DEM features
        f_dem = self.dem_encoder(dem)

        # 4. Concatenate cross-modal feature representations (80 channels)
        f_concat = torch.cat([f_sar, f_optical, f_dem], dim=1)

        # 5. Project into continuous 64-dimensional latent manifold
        latent_manifold = self.fusion_projection(f_concat)

        metadata = {
            "batch_size": b,
            "spatial_dim": (h, w),
            "latent_dim": self.latent_dim,
            "optical_active": active_optical,
            "optical_dropout_enforced": optical_dropout,
            "sar_boost_factor": float(self.sar_amplification_weight.item()) if optical_dropout else 1.0,
        }

        return latent_manifold, metadata
