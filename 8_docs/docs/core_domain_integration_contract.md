# Core Engine / Pipeline to Domain Translators Integration Contract

**THE MRIDANSH · AETHER-MRID1607X**  
**Module:** `4_domain_translators`  
**Task:** 05 of 06 — Verified 2026-10-09  
**Status:** Hardened, Semantically Gated & Operationally Verified  

---

## 1. Executive Summary & Purpose

This contract establishes the formal integration boundary between upstream core-engine outputs (`3_core_engine`), data-pipeline products (`2_data_pipeline`), and downstream domain translators (`4_domain_translators`).

The integration layer is implemented by [`DomainIntegrationRouter`](file:///d:/JAGANNATH_CODE_SANCTUM/JCC%20CAMPUS%202%20%28RS-SDA%20DIVISION%29/THE_MRIDANSH/4_domain_translators/domain_integrator.py) in `4_domain_translators/domain_integrator.py`. It guarantees:
1. **Semantic Gating:** Abstract neural latent embeddings and physics flux divergence rates are strictly prevented from masquerading as physical soil moisture content ($\theta$ in $\text{m}^3/\text{m}^3$).
2. **Contract Compliance:** Data routed to [`AgronomyHealthTranslator`](file:///d:/JAGANNATH_CODE_SANCTUM/JCC%20CAMPUS%202%20%28RS-SDA%20DIVISION%29/THE_MRIDANSH/4_domain_translators/agronomy_translator.py) and [`CivilLoadTranslator`](file:///d:/JAGANNATH_CODE_SANCTUM/JCC%20CAMPUS%202%20%28RS-SDA%20DIVISION%29/THE_MRIDANSH/4_domain_translators/civil_translator.py) must strictly satisfy the [`DomainInput`](file:///d:/JAGANNATH_CODE_SANCTUM/JCC%20CAMPUS%202%20%28RS-SDA%20DIVISION%29/THE_MRIDANSH/4_domain_translators/base.py) specification.
3. **Validity Mask & Metadata Preservation:** Upstream invalid observation masks, CRS, affine transforms, bounding boxes, resolution, acquisition timestamps, and STAC provenance flow through without fabrication.
4. **Honest Uncertainty Accounting:** EnKF ensemble variance is preserved as a scalar variance; it is never converted to standard deviation or expanded into a synthetic per-pixel raster.

---

## 2. Source-to-Destination Interface Map

| Source Module | Source Function / Output | Destination Function | Route Status | Reason & Required Evidence |
| :--- | :--- | :--- | :---: | :--- |
| `3_core_engine/state_estimation/enkf_filter.py` | `assimilate_spatial_grid` / `posterior_soil_state` (H, W) | `DomainIntegrationRouter.integrate_enkf_state` $\to$ `AgronomyHealthTranslator` / `CivilLoadTranslator` | **EXECUTABLE** | Satisfies declared physical state contract when soil moisture prior & obs in $\text{m}^3/\text{m}^3$ are assimilated. |
| `3_core_engine/models/spatial_temporal_encoder.py` | `forward` / `latent_representation` (B, D, H, W) | `DomainIntegrationRouter.integrate_backbone_latent` | **BLOCKED** | Latent neural features ($D=64/128$) are dimensionless and uncalibrated. Unblocking requires a trained physical projection head with in-situ validation. |
| `3_core_engine/physics/richards_engine.py` | `compute_richards_flux` / `water_flux` (H, W) | `DomainIntegrationRouter.integrate_physics_output` | **BLOCKED** | Water flux is in $\text{cm/day}$ (flux divergence), not volumetric water content ($\text{m}^3/\text{m}^3$). Unblocking requires a time-stepping solver integrating $\partial\theta/\partial t$. |
| `2_data_pipeline/fusion/satellite_fusion.py` | Snapshot dictionary (`channels`, `fused_tensor`, `fused_validity_mask`) | `DomainIntegrationRouter.extract_pipeline_context` $\to$ `DomainInput` auxiliary | **EXECUTABLE** | Extracts genuine contextual spectral index (`OPTICAL_NDVI`), per-pixel validity mask, and STAC scene provenance. |
| External / Verified In-Situ Sensor | Physical soil moisture raster $(H, W)$ | `DomainIntegrationRouter.integrate_direct_state` | **EXECUTABLE** | Validated physical arrays with declared unit $\text{m}^3/\text{m}^3$ are ingested directly. |

---

## 3. Verified Tensor Shapes & Variable Semantics

### 3.1 Neural Backbone (`SpatialTemporalEncoderBackbone`)
- **Input Tensor Layout:** $(B, T, C, H, W)$ where $C=5$ (`SAR_VV`, `SAR_VH`, `SAR_POL_RATIO`, `OPTICAL_NDVI`, `OPTICAL_NDMI`).
- **Output Tensor Layout:** $(B, \text{feature\_dim}, H, W)$ where $\text{feature\_dim} \in \{64, 128\}$.
- **Semantics:** Abstract latent activations. **No physical soil moisture state exists.**

### 3.2 Richards Physics Engine (`RichardsSoilPhysicsEngine`)
- **Input Tensor Layout:** $(H, W)$ or $(\dots, H, W)$ physical moisture grid ($0.05 \le \theta \le 0.45\text{ m}^3/\text{m}^3$).
- **Output Dictionary:**
  - `hydraulic_conductivity`: $K(\theta)$ in $\text{cm/day}$.
  - `water_flux`: Darcy-Richards flux $\mathbf{Q} = -K \nabla \theta$ in $\text{cm/day}$.
  - `physics_constraint_loss`: Scalar flux violation penalty $(\text{cm/day})^2$.
- **Semantics:** Transport rates and gradient divergence. **Not a state variable.**

### 3.3 State Estimation (`EnsembleKalmanFilterEngine`)
- **Input Grids:** Prior state grid $(H, W)$, observation grid $(H, W)$.
- **Internal State Dimension:** $N_{\text{state}} = H \times W$. Ensemble size $N_{\text{ens}} = 20$.
- **Output Dictionary:**
  - `posterior_soil_state`: $(H, W)$ posterior ensemble mean.
  - `uncertainty_variance`: Scalar float (sample variance across ensemble).
  - `kalman_gain`: $(N_{\text{state}}, N_{\text{state}})$ Kalman gain matrix.
- **Semantics:** Assimilated state in the same physical units as the input prior/observation.

---

## 4. Integration Routing Architecture

### 4.1 EnKF Execution Route
```
EnKF Output Dict
   ├── posterior_soil_state (H, W) ─────────┐
   └── uncertainty_variance (scalar float) ─┼──> DomainInput(soil_state, uncertainty, ...)
                                            │          │
Optional Pipeline Context                  │          ├──> AgronomyHealthTranslator -> DomainOutput
   ├── OPTICAL_NDVI (H, W) ─────────────────┤          └──> CivilLoadTranslator      -> DomainOutput
   ├── valid_data_mask (H, W) ──────────────┤
   └── provenance dict ─────────────────────┘
```

### 4.2 Semantic Gate Blocking Logic
```python
if source_type == "backbone":
    # Abstract latent tensor (B, D, H, W) -> No projection head exists
    return IntegrationResult(
        status="BLOCKED",
        blocked_reason="SpatialTemporalEncoderBackbone outputs an abstract latent feature tensor...",
        required_evidence="Requires an architecturally defined and calibrated physical projection head..."
    )

if source_type == "physics":
    # Flux divergence (cm/day) -> Not volumetric moisture
    return IntegrationResult(
        status="BLOCKED",
        blocked_reason="RichardsSoilPhysicsEngine produces water_flux (cm/day)...",
        required_evidence="Requires a coupled temporal state-integration solver..."
    )
```

---

## 5. Mask and Geospatial Metadata Handling

1. **Mask Preservation:**
   - Upstream boolean `valid_data_mask` must have shape matching `soil_state`.
   - Invalid pixels (`False`) are propagated without replacement.
   - Downstream translators fill invalid locations with `np.nan` in metric rasters.
   - Aggregate statistics (`mean_moisture_m3m3`, `mean_bearing_kPa`) are calculated strictly over valid pixels.
   - 100% invalid masks raise `IntegrationValidationError` / `ValueError` ("0 valid pixels").
2. **Geospatial Integrity:**
   - Upstream `crs`, `transform`, `bounds`, `resolution`, `acquisition_datetime`, and `provenance` are passed through untouched.
   - Missing fields remain `None`. Defaults like `EPSG:4326` or zero-bounding boxes are **never** fabricated.

---

## 6. Uncertainty Type & Propagation Audit

1. **Upstream Quantity:** EnKF computes sample variance across ensemble members:
   $$\sigma^2 = \frac{1}{N_{\text{state}} \cdot N_{\text{ens}}} \sum_{i, j} (X_{a, i, j} - \bar{x}_a)^2$$
   - Units: $(\text{m}^3/\text{m}^3)^2$.
   - Dimension: Scalar float.
2. **Safeguards Enforced:**
   - **No Variance $\to$ Std Conversion:** Variance is not square-rooted without explicit caller declaration.
   - **No Spatial Expansion:** Scalar variance is not broadcast into a synthetic 2D raster.
   - **No Metric Mislabelling:** The uncertainty is recorded under `input_soil_state_uncertainty` with `propagation_status: "unpropagated"`. It is explicitly NOT labeled as crop health uncertainty, irrigation uncertainty, or bearing capacity uncertainty.
   - **Uncalibrated Status:** The output explicitly notes that no analytical error propagation model is implemented for downstream heuristic indicators.

---

## 7. Verification Evidence

The integration suite in [`tests/test_domain_integration_d05.py`](file:///d:/JAGANNATH_CODE_SANCTUM/JCC%20CAMPUS%202%20%28RS-SDA%20DIVISION%29/tests/test_domain_integration_d05.py) validates all 18 requirements:
- **18/18 Tests PASSED in 0.28s**.
- Full domain suite: **61/61 PASSED in 0.28s**.
- Core engine regression: **107 PASSED** (zero regressions).
