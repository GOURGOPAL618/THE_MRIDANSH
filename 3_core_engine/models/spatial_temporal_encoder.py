import logging
from typing import Any
import torch
import torch.nn as nn

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class SpatialTemporalEncoderBackbone(nn.Module):
    """Neural Network Spatial-Temporal Backbone Architecture for Multi-Modal Satellite Cubes."""

    def __init__(self, in_channels: int = 5, feature_dim: int = 128, sequence_length: int = 5):
        """
        Initializes the PyTorch Neural Backbone.
        sequence_length is kept for interface compatibility but temporal ops handle dynamic T natively.
        """
        super(SpatialTemporalEncoderBackbone, self).__init__()
        self.in_channels = in_channels
        self.feature_dim = feature_dim
        
        logging.info(f"🧠 Initializing PyTorch Neural Backbone | Channels: {in_channels} | Latent Dim: {feature_dim}")
        
        # Spatial Encoder (CNN)
        # Expects per-frame input: (B*T, C, H, W)
        self.spatial_encoder = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, feature_dim, kernel_size=1)
        )
        
        # Temporal Encoder (GRU applied pixel-wise)
        # Input: (B*H*W, T, feature_dim) -> Output: (B*H*W, feature_dim)
        self.temporal_encoder = nn.GRU(
            input_size=feature_dim,
            hidden_size=feature_dim,
            num_layers=1,
            batch_first=True
        )

    def extract_spatial_features(self, input_tensor: torch.Tensor) -> torch.Tensor:
        """Extracts spatial convolutional features. Input: (B*T, C, H, W) -> Output: (B*T, feature_dim, H, W)"""
        return self.spatial_encoder(input_tensor)

    def extract_temporal_sequence(self, sequence_tensor: torch.Tensor) -> torch.Tensor:
        """
        Processes temporal sequence stream.
        Input: (B, T, C, H, W)
        Output: (B, feature_dim, H, W)
        """
        if sequence_tensor.dim() != 5:
            raise ValueError(f"Expected 5D input tensor (B, T, C, H, W), got {sequence_tensor.dim()}D tensor.")
            
        b, t, c, h, w = sequence_tensor.shape
        if c != self.in_channels:
            raise ValueError(f"Expected {self.in_channels} channels, got {c}.")

        # Fold time into batch dimension for spatial encoding
        sequence_tensor = sequence_tensor.view(b * t, c, h, w)
        
        # Pass through spatial CNN
        spatial_features = self.extract_spatial_features(sequence_tensor)
        
        # Unfold time
        spatial_features = spatial_features.view(b, t, self.feature_dim, h, w)
        
        # Permute to isolate pixel-wise time-series: (B, H, W, T, feature_dim)
        spatial_features = spatial_features.permute(0, 3, 4, 1, 2).contiguous()
        
        # Flatten spatial dims into batch dim for GRU: (B*H*W, T, feature_dim)
        gru_input = spatial_features.view(b * h * w, t, self.feature_dim)
        
        # Apply GRU
        gru_out, hidden = self.temporal_encoder(gru_input)
        
        # Take the final hidden state across sequence
        last_hidden = hidden.squeeze(0)  # (B*H*W, feature_dim)
        
        # Reshape back to spatial dimensions: (B, H, W, feature_dim)
        latent_representation = last_hidden.view(b, h, w, self.feature_dim)
        
        # Standard PyTorch channel-first output convention: (B, feature_dim, H, W)
        latent_representation = latent_representation.permute(0, 3, 1, 2).contiguous()
        
        return latent_representation

    def forward(self, datacube_sequence: torch.Tensor) -> dict[str, Any]:
        """Forward pass through full Spatial-Temporal Neural Encoder Backbone."""
        logging.info("🚀 Executing Spatial-Temporal Neural Network Forward Pass...")
        
        latent_map = self.extract_temporal_sequence(datacube_sequence)
        
        logging.info(
            f"✅ Neural Backbone Encoding Completed!\n"
            f"   -> Input Sequence: {datacube_sequence.shape}\n"
            f"   -> Output Latent Map: {latent_map.shape} (Batch x feature_dim x H x W)"
        )
        
        return {
            "latent_representation": latent_map,
            "latent_shape": latent_map.shape,
            "feature_dim": self.feature_dim,
        }

# Self-Test Execution Module
if __name__ == "__main__":
    print("\n--- Testing Day 8 Neural Network Backbone (Spatial-Temporal Encoders) ---")

    # B=2, T=5, C=5, H=120, W=120
    mock_sequence = torch.randn(2, 5, 5, 120, 120)

    backbone = SpatialTemporalEncoderBackbone(in_channels=5, feature_dim=128)
    result = backbone(mock_sequence)

    assert result["latent_representation"].shape == (2, 128, 120, 120)
    print("\n[SUCCESS] Day 8 Neural Network Backbone Engine: PASSED OPERATIONAL CHECKS!\n")
