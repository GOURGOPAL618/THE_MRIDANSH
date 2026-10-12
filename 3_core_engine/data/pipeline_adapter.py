import torch
from torch.utils.data import Dataset
import numpy as np
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class PipelineSnapshotAdapter(Dataset):
    """Adapter converting a pipeline snapshot (numpy) into a tensor suitable for the
    SpatialTemporalEncoderBackbone.

    Expected snapshot dict keys (as emitted by ``SatelliteSAROpticalFusionEngine``):
        - "fused_tensor": np.ndarray of shape (H, W, C)
        - "fused_validity_mask": np.ndarray of same shape (H, W, C)
        - "channels": List[str]  ordered channel names
        - optional metadata (e.g., "provenance")

    The adapter validates:
        * rank == 3
        * matching spatial dimensions between tensor and mask
        * channel count matches the expected backbone ``in_channels`` (default 5)
        * data are finite (no NaN/Inf)
    It returns a dict with:
        - "input_tensor": torch.Tensor of shape (B, T, C, H, W)
        - "metadata": original snapshot metadata (preserved unchanged)
    ``B`` is the dataset batch index (always 1 for a single item), ``T`` is 1
    for a single observation date.
    """

    def __init__(self, snapshots: List[Dict[str, Any]], in_channels: int = 5):
        if not isinstance(snapshots, list) or len(snapshots) == 0:
            raise ValueError("snapshots must be a non‑empty list of snapshot dicts.")
        self.snapshots = snapshots
        self.in_channels = in_channels
        logging.info(f"📦 PipelineSnapshotAdapter initialised with {len(snapshots)} snapshot(s).")

    # ---------------------------------------------------------------------
    def __len__(self) -> int:
        return len(self.snapshots)

    # ---------------------------------------------------------------------
    def __getitem__(self, idx: int) -> dict:
        snap = self.snapshots[idx]
        # -----------------------------------------------------------------
        # Validation of required fields
        # -----------------------------------------------------------------
        required_keys = {"fused_tensor", "fused_validity_mask", "channels"}
        missing = required_keys - snap.keys()
        if missing:
            raise KeyError(f"Snapshot missing required keys: {missing}")

        tensor_np: np.ndarray = snap["fused_tensor"]
        mask_np: np.ndarray = snap["fused_validity_mask"]
        channels: List[str] = snap["channels"]

        if tensor_np.ndim != 3:
            raise ValueError(
                f"fused_tensor must be 3‑D (H, W, C), got shape {tensor_np.shape}."
            )
        if mask_np.shape != tensor_np.shape:
            raise ValueError(
                "fused_validity_mask shape must match fused_tensor shape.")
        if len(channels) != tensor_np.shape[2]:
            raise ValueError(
                f"Channel list length {len(channels)} does not match tensor channel dimension {tensor_np.shape[2]}."
            )
        if tensor_np.shape[2] != self.in_channels:
            raise ValueError(
                f"Expected {self.in_channels} channels for the backbone, got {tensor_np.shape[2]}."
            )
        if not np.isfinite(tensor_np).all():
            raise ValueError("fused_tensor contains NaN or Inf values.")

        # -----------------------------------------------------------------
        # Convert to torch tensor with required layout (B, T, C, H, W)
        # -----------------------------------------------------------------
        # numpy layout is (H, W, C) -> transpose to (C, H, W)
        tensor_chw = np.transpose(tensor_np, (2, 0, 1))  # (C, H, W)
        # add batch and time dimensions (both =1)
        tensor_btchw = tensor_chw[np.newaxis, np.newaxis, ...]  # (1, 1, C, H, W)
        tensor_torch = torch.from_numpy(tensor_btchw).float()

        # Preserve any additional metadata (e.g., provenance, acquisition datetime)
        metadata = {k: v for k, v in snap.items() if k not in required_keys}

        return {"input_tensor": tensor_torch, "metadata": metadata}

# Helper function for a single snapshot (convenient for quick use)
def snapshot_to_tensor(snapshot: Dict[str, Any], in_channels: int = 5) -> torch.Tensor:
    """Convert a single pipeline snapshot dict to a torch tensor of shape (1, 1, C, H, W).
    Performs the same validation as the Dataset class.
    """
    adapter = PipelineSnapshotAdapter([snapshot], in_channels=in_channels)
    return adapter[0]["input_tensor"]
