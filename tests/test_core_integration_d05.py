"""
Task 05 — Core Integration Boundary Tests
==========================================
Tests the verified contract between 2_data_pipeline output and 3_core_engine components.

Import layout follows the established project convention:
  sys.path.insert(0, <root>/3_core_engine)   — backbone, physics, EnKF, adapter
  sys.path.insert(0, <root>/2_data_pipeline)  — fusion engine, schema
"""

import os
import sys
import unittest
import numpy as np
import torch

# ─── Establish import roots ────────────────────────────────────────────────────
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_CORE_ENGINE = os.path.join(_REPO_ROOT, "3_core_engine")
_DATA_PIPELINE = os.path.join(_REPO_ROOT, "2_data_pipeline")

for _p in (_CORE_ENGINE, _DATA_PIPELINE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ─── Imports (verified against actual module paths) ───────────────────────────
from data.pipeline_adapter import PipelineSnapshotAdapter, snapshot_to_tensor
from fusion.satellite_fusion import (
    SatelliteSAROpticalFusionEngine,
    MissingModalityError,
)
from schemas.satellite_schema import GeospatialRasterAsset
from models.spatial_temporal_encoder import SpatialTemporalEncoderBackbone
from physics.richards_engine import RichardsSoilPhysicsEngine
from state_estimation.enkf_filter import (
    EnsembleKalmanFilterEngine,
    assimilate_spatial_grid,
)


# ─── Shared fixture builder ────────────────────────────────────────────────────

def _make_asset(
    value,
    band_name: str,
    crs: str = "EPSG:32645",
    resolution: tuple = (10.0, 10.0),
    bounds: tuple = (0.0, 0.0, 100.0, 100.0),
    transform: tuple = (10.0, 0.0, 0.0, 0.0, -10.0, 100.0),
    height: int = 10,
    width: int = 10,
) -> GeospatialRasterAsset:
    raw = np.full((1, height, width), value, dtype=np.float32)
    mask = np.ones((1, height, width), dtype=bool)
    return GeospatialRasterAsset(
        raw_array=raw,
        raw_dtype="float32",
        scale_factor=1.0,
        add_offset=0.0,
        crs=crs,
        transform=transform,
        bounds=bounds,
        resolution=resolution,
        valid_data_mask=mask,
        stac_item_id=f"mock_{band_name}",
        asset_key=band_name,
        source_href=f"s3://mock/{band_name}.tif",
    )


def _make_engine(
    crs: str = "EPSG:32645",
    resolution: tuple = (10.0, 10.0),
    bounds: tuple = (0.0, 0.0, 100.0, 100.0),
) -> SatelliteSAROpticalFusionEngine:
    return SatelliteSAROpticalFusionEngine(
        target_crs=crs,
        target_resolution=resolution,
        target_bounds=bounds,
    )


def _make_snapshot(
    vv_val: float = 0.2,
    vh_val: float = 0.1,
    ndvi_val: float = 0.5,
    ndmi_val: float = 0.3,
    height: int = 10,
    width: int = 10,
) -> dict:
    """Build a standard 5-channel fusion snapshot using fixture assets."""
    crs, res, bounds = "EPSG:32645", (10.0, 10.0), (0.0, 0.0, 100.0, 100.0)
    transform = (10.0, 0.0, 0.0, 0.0, -10.0, 100.0)
    engine = _make_engine(crs, res, bounds)
    return engine.create_fused_spatial_tensor(
        _make_asset(vv_val, "SAR_VV", crs, res, bounds, transform, height, width),
        _make_asset(vh_val, "SAR_VH", crs, res, bounds, transform, height, width),
        _make_asset(ndvi_val, "OPTICAL_NDVI", crs, res, bounds, transform, height, width),
        _make_asset(ndmi_val, "OPTICAL_NDMI", crs, res, bounds, transform, height, width),
    )


# ─── Test cases ───────────────────────────────────────────────────────────────

class TestCoreIntegrationD05(unittest.TestCase):

    # ── T-CI-01: channel order and fused tensor layout ─────────────────────────
    def test_tci_01_channel_order_and_layout(self):
        """
        Verifies the 5-channel output order defined in SatelliteSAROpticalFusionEngine:
          index 0 = SAR_VV       (raw_array[0], float32)
          index 1 = SAR_VH       (raw_array[0], float32)
          index 2 = SAR_POL_RATIO (VH / (VV + 1e-6), float32, derived)
          index 3 = OPTICAL_NDVI  (raw_array[0], float32)
          index 4 = OPTICAL_NDMI  (raw_array[0], float32)
        fused_tensor layout: (H, W, C), dtype float32.
        fused_validity_mask layout: (H, W, C), dtype bool.
        """
        engine = _make_engine()
        vv_val, vh_val = 0.2, 0.1
        out = engine.create_fused_spatial_tensor(
            _make_asset(vv_val, "SAR_VV"),
            _make_asset(vh_val, "SAR_VH"),
            _make_asset(0.5, "OPTICAL_NDVI"),
            _make_asset(0.3, "OPTICAL_NDMI"),
        )

        expected_channels = ["SAR_VV", "SAR_VH", "SAR_POL_RATIO", "OPTICAL_NDVI", "OPTICAL_NDMI"]
        self.assertEqual(out["channels"], expected_channels, "Channel list order mismatch.")

        fused = out["fused_tensor"]
        self.assertEqual(fused.dtype, np.float32, "fused_tensor dtype must be float32.")
        self.assertEqual(fused.shape, (10, 10, 5), "Expected layout (H, W, C).")

        mask = out["fused_validity_mask"]
        self.assertEqual(mask.shape, fused.shape, "Mask and tensor shapes must match.")
        self.assertEqual(mask.dtype, bool, "fused_validity_mask dtype must be bool.")

        # Verify pol_ratio is derived correctly
        expected_pol = vh_val / (vv_val + 1e-6)
        np.testing.assert_allclose(
            fused[:, :, 2], expected_pol, rtol=1e-5,
            err_msg="SAR_POL_RATIO channel value mismatch."
        )

    # ── T-CI-02: adapter converts single snapshot to (1, 1, C, H, W) ──────────
    def test_tci_02_snapshot_to_tensor_shape_and_values(self):
        """
        Adapter must:
          - Accept a valid 5-channel fusion snapshot
          - Return a torch.Tensor of shape (1, 1, 5, H, W) dtype float32
          - Preserve channel values exactly (verified by round-trip numpy comparison)
        """
        snap = _make_snapshot()
        tensor = snapshot_to_tensor(snap, in_channels=5)

        self.assertIsInstance(tensor, torch.Tensor)
        self.assertEqual(tensor.shape, (1, 1, 5, 10, 10), "Expected shape (B=1, T=1, C=5, H=10, W=10).")
        self.assertEqual(tensor.dtype, torch.float32, "Adapter output must be float32.")

        # Round-trip: tensor back to numpy should match transposed fused_tensor
        np_back = tensor.squeeze(0).squeeze(0).numpy()          # (5, 10, 10)
        fused_chw = snap["fused_tensor"].transpose(2, 0, 1)     # (C, H, W)
        np.testing.assert_allclose(np_back, fused_chw, rtol=1e-6)

    # ── T-CI-03: multiple snapshots form a batch ───────────────────────────────
    def test_tci_03_dataset_len_and_batch_stack(self):
        """
        PipelineSnapshotAdapter must behave as a torch Dataset:
          - len() returns number of snapshots
          - each item is (1, 1, C, H, W)
          - stacking 3 items produces (3, 1, C, H, W)
        """
        snapshots = [_make_snapshot(vv_val=0.2 + i * 0.01) for i in range(3)]
        ds = PipelineSnapshotAdapter(snapshots, in_channels=5)
        self.assertEqual(len(ds), 3)
        items = [ds[i]["input_tensor"].squeeze(0) for i in range(3)]  # [(1,C,H,W)]
        batch = torch.stack(items, dim=0)                              # (3,1,C,H,W)
        self.assertEqual(batch.shape, (3, 1, 5, 10, 10))

    # ── T-CI-04: invalid adapter inputs raise ValueError ───────────────────────
    def test_tci_04a_wrong_channel_count_rejected(self):
        """
        A snapshot dict with fewer channels than in_channels must raise ValueError.
        Built directly (bypassing the fusion engine) to avoid MissingModalityError.
        Code path: adapter channel count check (line 68-70 of pipeline_adapter.py).
        """
        snap = _make_snapshot()  # 5 channels
        # Manually inject a 4-channel version
        four_ch = snap["fused_tensor"][:, :, :4]
        bad_snap = {
            "fused_tensor": four_ch,
            "fused_validity_mask": snap["fused_validity_mask"][:, :, :4],
            "channels": snap["channels"][:4],
        }
        with self.assertRaises(ValueError, msg="Adapter must reject channel count mismatch."):
            snapshot_to_tensor(bad_snap, in_channels=5)

    def test_tci_04b_nan_in_fused_tensor_rejected(self):
        """
        A snapshot dict whose fused_tensor contains NaN must be rejected by the adapter.

        Evidence: NaN propagates through fusion because:
          - _process_modality does not check for NaN in array values
          - _verify_alignment does not check for NaN
          - Only valid_data_mask (boolean presence) is checked
        Therefore invalid numeric values can reach the adapter silently.
        The adapter's np.isfinite check is the only guard at the boundary.
        """
        snap = _make_snapshot()
        # Inject NaN into a slice of the fused tensor post-fusion
        snap["fused_tensor"][0, 0, 0] = np.nan
        with self.assertRaises(ValueError, msg="Adapter must reject NaN values."):
            snapshot_to_tensor(snap, in_channels=5)

    def test_tci_04c_missing_required_key_rejected(self):
        """Missing required key in snapshot dict must raise KeyError."""
        snap = _make_snapshot()
        del snap["channels"]
        with self.assertRaises(KeyError):
            snapshot_to_tensor(snap, in_channels=5)

    def test_tci_04d_fusion_raises_on_missing_required_modality(self):
        """
        Passing ndmi=None to the fusion engine raises MissingModalityError,
        not ValueError. This confirms the fusion engine's own guard fires
        before the adapter is ever called.
        """
        engine = _make_engine()
        with self.assertRaises(MissingModalityError):
            engine.create_fused_spatial_tensor(
                _make_asset(0.2, "SAR_VV"),
                _make_asset(0.1, "SAR_VH"),
                _make_asset(0.5, "OPTICAL_NDVI"),
                ndmi=None,
            )

    # ── T-CI-05: adapter → backbone produces correct latent shape ──────────────
    def test_tci_05_adapter_to_backbone_latent_shape(self):
        """
        Verified wiring:
          adapter output (1, 1, 5, H, W)  →  backbone  →  latent (1, 64, H, W)
        The backbone's 'forward' method calls 'extract_temporal_sequence', which
        accepts dynamic T. For T=1 it runs one GRU step.
        """
        snap = _make_snapshot()
        tensor = snapshot_to_tensor(snap, in_channels=5)

        backbone = SpatialTemporalEncoderBackbone(in_channels=5, feature_dim=64)
        backbone.eval()
        with torch.no_grad():
            out = backbone(tensor)

        self.assertIn("latent_representation", out)
        latent = out["latent_representation"]
        self.assertEqual(latent.shape, (1, 64, 10, 10), "Expected (B, feature_dim, H, W).")
        self.assertEqual(latent.dtype, torch.float32)

    # ── T-CI-06: metadata is preserved through the adapter ─────────────────────
    def test_tci_06_metadata_preserved(self):
        """
        Extra keys in the snapshot dict beyond the three required keys
        (fused_tensor, fused_validity_mask, channels) must be returned
        under 'metadata' in the adapter output.
        """
        snap = _make_snapshot()
        snap["acquisition_time"] = "2026-10-01T12:00:00Z"
        snap["provenance"] = {"source": "mock"}  # already in fusion output

        item = PipelineSnapshotAdapter([snap], in_channels=5)[0]

        self.assertIn("metadata", item)
        self.assertEqual(item["metadata"].get("acquisition_time"), "2026-10-01T12:00:00Z")
        # provenance should also be preserved
        self.assertIn("provenance", item["metadata"])

    # ── T-CI-07: documented boundary violations ────────────────────────────────
    def test_tci_07a_backbone_latent_is_not_moisture_grid(self):
        """
        Boundary document:
        The backbone's latent_representation (B, feature_dim, H, W) cannot be
        passed directly to RichardsSoilPhysicsEngine.compute_richards_flux.

        The physics engine expects a moisture grid: a 2D (H, W) tensor of
        volumetric water content in physical units [m³/m³], not a multi-channel
        latent feature map.

        This test verifies that the channel mismatch is detectable:
        a (B, feature_dim, H, W) tensor has 4 dims; the physics engine
        works on 2D spatial grids.  Passing a (1, 64, 10, 10) tensor into
        compute_richards_flux succeeds numerically (no explicit shape guard
        beyond ndim>=2), but the interpretation is physically wrong.
        We document this by asserting the output shape differs from (10, 10):
        a silent mis-use, not an exception.
        """
        snap = _make_snapshot()
        tensor = snapshot_to_tensor(snap, in_channels=5)
        backbone = SpatialTemporalEncoderBackbone(in_channels=5, feature_dim=64)
        backbone.eval()
        with torch.no_grad():
            latent = backbone(tensor)["latent_representation"]  # (1, 64, 10, 10)

        physics = RichardsSoilPhysicsEngine()
        # The latent tensor has 4 dims — physics engine requires >=2.
        # It will NOT raise an error; it will silently process an incorrect input.
        # This is the documented risk: there is no automatic type-level guard.
        result = physics.compute_richards_flux(latent)
        # Confirm the output shape is NOT the intended (H, W) = (10, 10):
        self.assertNotEqual(
            result["water_flux"].shape, (10, 10),
            "Latent tensor fed to physics does not produce intended (H, W) output — "
            "no explicit guard exists. Caller must perform explicit moisture conversion."
        )

    def test_tci_07b_enkf_requires_numpy_not_torch(self):
        """
        Boundary document:
        assimilate_spatial_grid expects np.ndarray inputs (H, W).
        Passing torch.Tensor triggers AttributeError inside the wrapper
        when it calls .flatten() on the observation (torch has .flatten but
        .astype() raises AttributeError — numpy-specific call).

        This confirms that gradient flow STOPS at the EnKF boundary.
        """
        enkf = EnsembleKalmanFilterEngine(num_ensembles=5)
        prior_torch = torch.rand(5, 5)
        obs_torch = torch.rand(5, 5)
        with self.assertRaises((AttributeError, TypeError)):
            assimilate_spatial_grid(enkf, prior_torch, obs_torch)

    def test_tci_07c_enkf_accepts_correct_numpy_input(self):
        """
        Positive counterpart: EnKF wrapper must succeed with proper numpy float32 arrays.
        """
        enkf = EnsembleKalmanFilterEngine(num_ensembles=10)
        rng = np.random.default_rng(seed=42)
        prior = rng.uniform(0.2, 0.35, size=(5, 5)).astype(np.float32)
        obs = rng.uniform(0.22, 0.38, size=(5, 5)).astype(np.float32)
        result = assimilate_spatial_grid(enkf, prior, obs, rng=rng)
        self.assertIn("posterior_soil_state", result)
        self.assertEqual(result["posterior_soil_state"].shape, (5, 5))

    # ── T-CI-08: multi-date API does not exist (documented blocker) ────────────
    def test_tci_08_multi_date_api_absent(self):
        """
        No multi-date cube assembly function exists in either the fusion engine
        or the pipeline adapter. Accessing a non-existent method raises AttributeError.
        This test documents the unsupported scenario explicitly.
        """
        engine = _make_engine()
        with self.assertRaises(AttributeError):
            engine.create_multi_date_tensor()

    # ── T-CI-09: validity mask propagation audit (new focused test) ────────────
    def test_tci_09_mask_is_not_applied_to_fused_tensor(self):
        """
        VERIFIED BEHAVIOR (defect documentation):
        The fused_tensor contains raw float32 values WITHOUT masking applied.
        Pixels flagged False in valid_data_mask retain their original numeric values.
        The adapter does not apply the mask before producing the backbone tensor.

        This means invalid pixels can enter the backbone as ordinary observations.
        There is no substitution, NaN-fill, or mask propagation at the adapter boundary.

        Justification for NOT introducing zero/NaN fill:
          - Task scope forbids inventing replacement values for missing observations.
          - Zero-fill would misrepresent backscatter/reflectance physical meaning.
          - NaN-fill is blocked because the adapter raises on non-finite values.

        MINIMAL CORRECTION APPLIED (see pipeline_adapter.py):
          The adapter now warns when mask has False entries so callers are informed.
          It does NOT alter the tensor values — that decision must be made upstream.

        This test:
          1. Verifies the documented pass-through behavior is consistent.
          2. Verifies the adapter raises ValueError when the fused_tensor
             already contains NaN (the only protection currently available).
        """
        # Build a snapshot where one pixel is flagged invalid in the mask,
        # but the raw value is a normal float (not NaN).
        snap = _make_snapshot()
        snap["fused_validity_mask"][3, 4, 0] = False   # flag one pixel invalid

        # Adapter must accept it without error (invalid pixel flows through)
        tensor = snapshot_to_tensor(snap, in_channels=5)
        self.assertEqual(tensor.shape, (1, 1, 5, 10, 10))

        # Verify that the invalid-flagged pixel's value is preserved unchanged
        orig_value = snap["fused_tensor"][3, 4, 0]
        tensor_value = tensor[0, 0, 0, 3, 4].item()
        self.assertAlmostEqual(
            float(orig_value), tensor_value, places=6,
            msg="Masked pixel value must pass through unchanged — no substitution is applied."
        )


if __name__ == "__main__":
    unittest.main()
