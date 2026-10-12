# Trainer Integration & Core-Engine Training Contract

**THE MRIDANSH · AETHER-MRID1607X**  
Task 06 — Verified 2026-10-09

This document records the **verified** computational training contract of `3_core_engine/trainer.py`,
the loss definitions, mathematical formulations, optimizer mechanics, and explicit scientific boundaries.

---

## 1. Supported Computational Pathway

The implemented and verified training execution path is:

$$\text{Datacube Input } (B, T, C, H, W) \longrightarrow \text{Backbone} \longrightarrow \text{Latent Map } (B, D, H, W) \longrightarrow \text{Loss} \longrightarrow \text{backward}() \longrightarrow \text{optimizer.step}()$$

### 1.1 Input Contract
- **Shape**: $(B, T, C, H, W)$ where:
  - $B$: Dynamic batch size
  - $T$: Sequence length ($T \ge 1$; dynamic pixel-wise GRU)
  - $C$: Must equal `in_channels` (default 5 matching fusion contract: `SAR_VV`, `SAR_VH`, `SAR_POL_RATIO`, `OPTICAL_NDVI`, `OPTICAL_NDMI`)
  - $H, W$: Dynamic spatial height and width
- **Type**: `torch.float32` (or `np.float32` which is converted)
- **Numeric Validation**: Must be finite; NaN or Inf raises `ValueError`.

### 1.2 Output Contract
- `SpatialTemporalEncoderBackbone` produces `latent_representation` of shape $(B, D, H, W)$ where $D = \text{feature\_dim}$ (default 64 or 128).
- **Physical Interpretation**: Abstract latent feature representation. It is **NOT** a physical soil moisture grid.

---

## 2. Loss Definitions, Units, and Mathematical Formulation

### 2.1 Representation Loss ($\mathcal{L}_{\text{repr}}$)
- **Formulation**: Mean Squared Error across all elements:
  $$\mathcal{L}_{\text{repr}} = \frac{1}{B \cdot D \cdot H \cdot W} \sum_{b, d, h, w} \left(\mathbf{z}_{b, d, h, w} - \mathbf{y}_{b, d, h, w}\right)^2$$
- **Inputs**:
  - $\mathbf{z}$: Predicted latent feature map $(B, D, H, W)$
  - $\mathbf{y}$: Reference target feature tensor $(B, D, H, W)$
- **Units**: Dimensionless squared latent feature difference.
- **Weight**: $w_{\text{repr}} = 1.0$ (configurable via `w_representation`).

### 2.2 Physics Constraint Loss ($\mathcal{L}_{\text{physics}}$)
- **Formulation**: Richards lateral flux divergence penalty:
  $$\mathbf{K}_{\text{rel}}(\theta) = S_e^{0.5} \left(1 - \left(1 - S_e^{1/m}\right)^m\right)^2, \quad S_e = \text{clamp}\left(\frac{\theta - \theta_r}{\theta_s - \theta_r}, 10^{-5}, 1.0\right)$$
  $$\mathbf{Q} = -K_s \mathbf{K}_{\text{rel}} \nabla_{xy} \theta$$
  $$\mathcal{L}_{\text{physics}} = \frac{1}{|\Omega|} \sum \left(\max(0, -\mathbf{Q})\right)^2$$
- **Inputs**: Independent physical volumetric soil moisture grid $\theta$ ($0.05 \le \theta \le 0.45 \text{ m}^3/\text{m}^3$).
- **Units**: $(\text{cm/day})^2$ flux violation penalty.
- **Weight**: $w_{\text{phys}} = 0.5$ (configurable via `w_physics`).
- **Boundary Guard**: Evaluated **ONLY** when a semantically valid physical moisture grid is explicitly passed. Latent embeddings fed as moisture grids are strictly rejected.

### 2.3 Composite Loss ($\mathcal{L}_{\text{total}}$)
$$\mathcal{L}_{\text{total}} = w_{\text{repr}} \mathcal{L}_{\text{repr}} + w_{\text{phys}} \mathcal{L}_{\text{physics}}$$

---

## 3. Optimizer Configuration & Parameter Updates

- **Optimizer**: `torch.optim.Adam` (configurable)
- **Default Learning Rate**: $10^{-3}$
- **Weight Decay**: $10^{-4}$
- **Gradient Management**: `self.optimizer.zero_grad()` is explicitly called prior to `backward()` on every step, preventing stale gradient accumulation (verified by T-TR-06).
- **Trainable Parameters**:
  - Spatial CNN: 3 2D-convolution layers (`spatial_encoder.0.weight`, `spatial_encoder.2.weight`, `spatial_encoder.4.weight`).
  - Temporal GRU: 1 recurrent layer (`temporal_encoder.weight_ih_l0`, `temporal_encoder.weight_hh_l0`, biases).
- **Verified Behavior**: Confirmed non-zero, finite gradients on both CNN and GRU weights (T-TR-04) and confirmed parameter modification after optimizer step (T-TR-05).

---

## 4. Architectural Boundaries and Limitations

| Boundary | Architectural Reality | Scientific Status |
|----------|----------------------|-------------------|
| **Backbone $\rightarrow$ Physical Soil Moisture** | Outputs $(B, D, H, W)$ latent features. No calibrated projection head exists. | **BLOCKED** — Cannot directly predict physical $\theta$ without calibrated head and in-situ labels. |
| **Backbone $\rightarrow$ Civil Bearing Capacity** | No projection head or geotechnical model exists. | **BLOCKED** — Uncalibrated heuristic scalers in legacy code are removed. |
| **Physics Loss Integration** | Operates on 2D spatial grid $\theta \in [0, 1]$. Omitted gravity head. | **PARTIAL** — Differentiable 2D lateral diffusion penalty only; requires external physical moisture grid. |
| **EnKF Assimilation** | NumPy-based, $H = I$. Operates outside PyTorch autograd. | **NOT DIFFERENTIABLE** — Autograd stops at EnKF boundary. Separate numerical update only. |
| **Ground-Truth Supervision** | In-situ probe data (ISMN, TDR) and geotechnical measurements are absent. | **BLOCKED** — Supervised training on ground-truth soil state is blocked by data availability. |

---

*Generated as part of Task 06 verification. Confirmed by 9 passing tests in `tests/test_core_trainer_d06.py` and 62 passing named tests repository-wide.*
