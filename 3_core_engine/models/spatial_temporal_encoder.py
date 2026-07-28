# THE MRIDANSH - 3. Core Engine | Model Architecture |Spatial Temporal Encoder

import logging
import numpy as np
from typing import Dict, Any, Tuple

logging.basicConfig(level = logging.INFO, format = "%(asctime)s - %(levelname)s - %(message)s")

class SpatialTemporalEncoderBackbone:
    """Neural Network Spatial-Temporal Backbone Architecture for Multi-Modal Satellite Cubes."""

    def __init__(self, in_channels: int = 8, feature_dim: int = 128, sequence_length: int = 5):
        self.in_channels = in_channels
        self.feature_dim = feature_dim
        self.sequence_length = sequence_length
        logging.info(f"🧠 Initializing Neural Backbone | Channels: {in_channels} | Latent Dim: {feature_dim}")

    def extract_spatial_features(self, inputr_tensor: np.ndarray) -> np.ndarray:
        """Simulates Spatial Convolutional Features (2D CNN Layer processing on H x W x C)."""
        batch_size, h, w, c = inputr_tensor.shape

        # Simulated Spatial Feature Map Extraction via weights dot Product & ReLU
        weights = np.random.randn(c, self.feature_dim) * 0.01
        spatial_map = np.maximum(0, np.dot(inputr_tensor, weights))

        return spatial_map   # Shape: (Batch, H, W, Latent_Dim)

    def extract_temporal_sequence(self, sequence_tensor: np.ndarray) -> np.ndarray:
        """Simulates Recurrent Sequence Encoding (GRU / LSTM processing over time-steps)."""
        logging.info(f"⏳ Processing Temporal Sequence Stream: {sequence_tensor.shape} (Batch x Time x H x W x C)...")

        batch, time_steps, h, w, c = sequence_tensor.shape
        time_outputs = []

        for t in range(time_steps):
            frame_spatial = self.extract_spatial_features(sequence_tensor[:, t, :, :, :])
            time_outputs.append(frame_spatial)

        # Temporal Pooling / Hidden State Accumulation Across Time axis
        temporal_latent_representation = np.mean(np.stack(time_outputs, axis=1), axis=1)
        return temporal_latent_representation

    def forward(self, datacube_sequence: np.ndarray) -> Dict[str, Any]:
        """Forward pass through full Spatial-Temporal Neural Encoder Backbone."""
        logging.info("🚀 Executing Spatial-Temporal Neural Network Forward Pass...")

        # latent_spatial_temporal_map = self.extract_temporal_sequence(datacube_sequence)

        latent_spatial_temporal_map = self.extract_temporal_sequence(datacube_sequence)

        logging.info(
            f"✅ Neural Backbone Encoding Completed!\n"
            f"   -> Input Sequence: {datacube_sequence.shape}\n"
            f"   -> Output Latent Map: {latent_spatial_temporal_map.shape} (Batch x H x W x Latent_Dim)"
        )

        return {
            "latent_representation": latent_spatial_temporal_map,
            "latent_shape": latent_spatial_temporal_map.shape,
            "feature_dim": self.feature_dim
        }


# Self-Test Execution Module
if __name__ == "__main__":
    print("\n--- Testing Day 8 Neural Network Backbone (Spatial-Temporal Encoders) ---")

    # Batch size=2, Time sequence=5 steps, Spatial=120x120, Channels=8 (Optical + SAR + Terrain)
    mock_sequence = np.random.uniform(0.0, 1.0, size = (2, 5, 120, 120, 8)).astype(np.float32)
    
    backbone = SpatialTemporalEncoderBackbone(in_channels = 8, feature_dim = 128, sequence_length = 5)
    result = backbone.forward(mock_sequence)

    assert result["latent_representation"].shape == (2, 120, 120, 128)
    print("\n[SUCCESS] Day 8 Neural Network Backbone Engine: PASSED OPERATIONAL CHECKS!\n")