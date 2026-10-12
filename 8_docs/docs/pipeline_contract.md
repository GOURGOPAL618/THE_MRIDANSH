# Pipeline–Core Engine Integration Contract

**THE MRIDANSH · AETHER-MRID1607X**  
Task 05 — Verified 2026-10-09

This document records the **verified** interface between the `2_data_pipeline` output
and the `3_core_engine` components.  Only properties confirmed by reading actual code
and by passing tests are stated as facts.  Unknown properties are explicitly marked.

---

## 1. Pipeline Snapshot Schema

The canonical snapshot is the return value of
[`SatelliteSAROpticalFusionEngine.create_fused_spatial_tensor`](../2_data_pipeline/fusion/satellite_fusion.py).

### 1.1 Snapshot dict keys

| Key | Type | Description | Verified |
|-----|------|-------------|---------|
| `fused_tensor` | `np.ndarray` | Fused multi-channel array | ✅ |
| `fused_validity_mask` | `np.ndarray` | Per-pixel per-channel validity | ✅ |
| `channels` | `List[str]` | Ordered channel names | ✅ |
| `tensor_shape` | `tuple` | Shape redundantly stored as `(H, W, C)` | ✅ |
| `provenance` | `dict[str, dict]` | Per-channel STAC provenance | ✅ |

### 1.2 `fused_tensor` layout

```
Shape:  (H, W, C)    — height × width × channels
Dtype:  np.float32   — cast explicitly in _process_modality (line 64)
```

The array is constructed by `np.stack(stack_arrays, axis=-1)`.  The per-pixel float values
are the `raw_array[0]` values cast to `float32` **without** applying `scale_factor` or
`add_offset`.  The `to_physical()` method on `GeospatialRasterAsset` is **never called**
inside the fusion engine.

> **UNKNOWN**: the physical meaning of raw values for SAR channels (linear power, dB, or
> DN) is not established by the fusion code.  The `retrieve_surface_soil_moisture_proxy`
> method normalises SAR VV assuming a dB range of [−25, −5], but this is not enforced
> during fusion.

### 1.3 Channel order (verified, immutable for 5-channel mode)

| Index | Name | Derivation |
|-------|------|------------|
| 0 | `SAR_VV` | `raw_array[0].astype(float32)` of sar_vv asset |
| 1 | `SAR_VH` | `raw_array[0].astype(float32)` of sar_vh asset |
| 2 | `SAR_POL_RATIO` | `SAR_VH / (SAR_VV + 1e-6)` — derived, no provenance entry |
| 3 | `OPTICAL_NDVI` | `raw_array[0].astype(float32)` of ndvi asset |
| 4 | `OPTICAL_NDMI` | `raw_array[0].astype(float32)` of ndmi asset |

Channels 5 and 6 (`DEM_ELEVATION`, `DEM_SLOPE`) are appended conditionally if the
optional DEM assets are provided.  The backbone is configured with `in_channels=5`;
DEM channels require a separately configured backbone.

### 1.4 `fused_validity_mask` semantics (verified)

```
Shape:  (H, W, C)    — same as fused_tensor
Dtype:  bool
```

Each entry is `True` if the pixel is valid, `False` if invalid (cloud/NoData).

The mask is constructed by `np.stack(stack_masks, axis=-1)` where:
- Each per-channel mask comes from `asset.valid_data_mask[0]` (shape `(H, W)`)
- The SAR_POL_RATIO mask is `vv_mask & vh_mask`

**Critical verified behavior — mask is NOT applied to `fused_tensor` values.**  
The fusion engine stores the mask separately.  A pixel whose mask entry is `False`
still carries its original float32 value in `fused_tensor`.  There is no NaN-fill,
zero-fill, or replacement.  Invalid numeric values **can only be detected** if the
source asset happened to contain NaN or Inf at the invalid locations.

---

## 2. Adapter Contract (`3_core_engine/data/pipeline_adapter.py`)

### 2.1 Input

A single snapshot dict as described in §1.

### 2.2 Output

```
"input_tensor"  : torch.Tensor, shape (1, 1, C, H, W), dtype torch.float32
"metadata"      : dict — all snapshot keys except fused_tensor, fused_validity_mask, channels
```

The adapter:
1. Validates required keys exist.
2. Validates `fused_tensor.ndim == 3`.
3. Validates `fused_validity_mask.shape == fused_tensor.shape`.
4. Validates `len(channels) == fused_tensor.shape[2]`.
5. Validates `fused_tensor.shape[2] == in_channels` (default 5).
6. Validates `np.isfinite(fused_tensor).all()` — raises `ValueError` on NaN or Inf.
7. Transposes `(H, W, C) → (C, H, W)` and adds B=1, T=1 dimensions.
8. **Does NOT apply the validity mask** to the tensor values.
9. **Does NOT warn** when mask contains False entries.  
   (See §3 for documented risk and justification for not filling.)

### 2.3 Import path

```python
# tests must add 3_core_engine to sys.path first:
sys.path.insert(0, os.path.join(repo_root, "3_core_engine"))
from data.pipeline_adapter import PipelineSnapshotAdapter, snapshot_to_tensor
```

The `data` sub-package has an `__init__.py`; the import is valid.

---

## 3. Validity Mask — Verified Behavior and Documented Risk

### What was found

The fusion engine guarantees:
- At least one valid pixel per modality (`np.any(valid_data_mask)` — line 55 of satellite_fusion.py).
- Modalities with **zero** valid pixels raise `InvalidModalityError`.
- Modalities with **partial** valid pixels are accepted without warning.

The adapter guarantees:
- If the fused_tensor values at invalid pixels are NaN or Inf, the adapter raises `ValueError`.
- If the fused_tensor values at invalid pixels are finite numbers (e.g., 0.0, sensor nodata),
  the adapter silently passes them through to the backbone.

### Why no replacement was introduced

- Task scope explicitly forbids inventing replacement values for missing observations.
- Zero-fill would misrepresent radar backscatter or optical reflectance.
- NaN-fill is blocked because the adapter raises ValueError on non-finite inputs, which
  would make partial-coverage scenes unusable rather than partially usable.
- The correct masking policy must be defined at the ingestion/preprocessing boundary,
  not at the adapter level.

### Documented risk (T-CI-09)

Invalid pixels whose raw values are finite pass through the adapter into the backbone
as ordinary observations.  This is the verified behavior.  T-CI-09 asserts this
explicitly.

**Resolution path** (outside Task 05 scope): The raster processor or fusion engine
should zero out or NaN-out invalid pixels at read time, or the backbone training loop
must apply the mask tensor as a loss mask before computing gradients.

---

## 4. Backbone Boundary

### Input contract

```
torch.Tensor, shape (B, T, C, H, W), dtype torch.float32
  B — batch size (1 per snapshot from the adapter)
  T — number of time steps (1 for a single snapshot)
  C — channel count matching backbone in_channels (default 5)
  H, W — spatial dimensions (dynamic, any size)
```

### Output contract

```python
{
    "latent_representation": torch.Tensor,  # shape (B, feature_dim, H, W)
    "latent_shape": torch.Size,
    "feature_dim": int,
}
```

### What the latent representation is NOT

The backbone latent tensor `(B, feature_dim, H, W)` is a learned feature map.  It is:
- **Not** a volumetric water content grid `[m³/m³]`.
- **Not** in physical units.
- **Not** directly usable as input to `RichardsSoilPhysicsEngine`.
- **Not** directly usable as input to `EnsembleKalmanFilterEngine`.

A conversion mapping latent features → physical moisture state has **not been defined**
in this codebase.  This is an open research question, not a software defect.

---

## 5. Physics Engine Boundary (`3_core_engine/physics/richards_engine.py`)

### Input contract

```
RichardsSoilPhysicsEngine.compute_richards_flux(
    moisture_grid: torch.Tensor,  # shape >= 2D, e.g. (H, W), physical units m³/m³
    depth_interval_m: float = 0.1,
)
```

### Verified limitations (stated in module docstring)

1. The formulation computes a **2D lateral spatial gradient** (∂θ/∂x, ∂θ/∂y), not a true
   vertical 1D depth profile as the class docstring implies.
2. The **gravity head is omitted**.  This is explicitly noted as a prototype limitation.
3. Parameters `alpha`, `n`, `ks_sat` are learnable `nn.Parameter` values.  Defaults
   correspond to loam soil (Van Genuchten/Mualem model); they are **not calibrated**.
4. The engine accepts any tensor with `ndim >= 2`, including latent tensors fed
   accidentally.  **There is no explicit type or shape guard** against misuse.
   Test T-CI-07a documents this silent mis-use risk.

### Output contract

```python
{
    "hydraulic_conductivity": torch.Tensor,  # same shape as moisture_grid
    "water_flux": torch.Tensor,              # same shape as moisture_grid
    "physics_constraint_loss": torch.Tensor, # scalar
}
```

---

## 6. EnKF Boundary (`3_core_engine/state_estimation/enkf_filter.py`)

### Input contract

```
assimilate_observations(
    prior_ensemble: np.ndarray,  # shape (N_state, N_ens), float32 or float64
    observation:    np.ndarray,  # shape (N_state,), same dtype as prior_ensemble
) -> dict
```

Or via the spatial wrapper:

```
assimilate_spatial_grid(
    engine:           EnsembleKalmanFilterEngine,
    prior_state_grid: np.ndarray,  # shape (H, W), float32
    observation_grid: np.ndarray,  # shape (H, W), same dtype
) -> dict
```

### Verified constraints

| Constraint | Evidence |
|-----------|---------|
| Observation operator H = I | Lines 24–25 of enkf_filter.py; `M = N = N_state` enforced at line 197 |
| Inputs must be `np.ndarray` | `.astype()` on torch.Tensor raises `AttributeError` (verified in T-CI-07b) |
| Not differentiable | Operates on NumPy; no PyTorch autograd graph is formed |
| Gradient flow stops at EnKF | Any torch.Tensor must be `.detach().numpy()` before passing to EnKF |
| No temporal propagation | The caller must supply the model-propagated prior ensemble |

### Output contract

```python
{
    "posterior_soil_state":  np.ndarray,  # shape (N_state,) or (H, W) via wrapper
    "kalman_gain":           np.ndarray,  # shape (N_state, N_state)
    "uncertainty_variance":  np.float32,  # scalar posterior ensemble variance
    "posterior_ensemble":    np.ndarray,  # shape (N_state, N_ens)
}
```

---

## 7. Component Boundary Diagram

```
2_data_pipeline                           3_core_engine
───────────────────────────────────────────────────────────────────────────
GeospatialRasterAsset (per modality)
        │
        ▼
SatelliteSAROpticalFusionEngine
        │   fused_tensor (H, W, 5) float32 [raw, not physical]
        │   fused_validity_mask (H, W, 5) bool [NOT applied to tensor]
        ▼
PipelineSnapshotAdapter                   [Task 05 boundary]
        │   validates: shape, channel count, finiteness
        │   does NOT apply mask
        │   input_tensor: torch.Tensor (1, 1, 5, H, W)
        ▼
SpatialTemporalEncoderBackbone
        │   latent_representation: torch.Tensor (1, feature_dim, H, W)
        │   ≠ moisture grid
        │   ≠ physical units
        ▼
  [UNDEFINED CONVERSION]
        │   no mapping from latent features → moisture state exists
        ▼
RichardsSoilPhysicsEngine                 [separate, not wired to backbone]
        │   input: moisture_grid (H, W) torch.float32, physical units m³/m³
        │   prototype: 2D lateral diffusion, no gravity term
        ▼
  [UNDEFINED CONVERSION / DETACH]
        │   must detach from autograd; convert to numpy float32
        ▼
EnsembleKalmanFilterEngine                [not differentiable]
        │   input: np.ndarray (N_state, N_ens)
        │   H = I (identity observation operator only)
        ▼
  posterior_soil_state: np.ndarray (H, W)
```

---

## 8. What Remains Undefined (Open Items)

1. **Physical units of SAR/optical raw values** — not established by fusion code.
2. **Mapping from backbone latent features to soil moisture state** — not implemented.
3. **Mask application policy** — no replacement value strategy defined.
4. **Temporal multi-date cube assembly** — no API exists; `create_multi_date_tensor`
   would raise `AttributeError`.
5. **End-to-end gradient flow** — blocked at the NumPy EnKF boundary; differentiable
   assimilation not implemented.

---

*Generated from verified code inspection and passing tests (14 tests T-CI-01 through T-CI-09).*  
*Do not update this document without re-running `tests/test_core_integration_d05.py`.*
