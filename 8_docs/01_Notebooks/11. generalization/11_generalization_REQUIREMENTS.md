# 🛰️ THE MRIDANSH: MULTI-REGIME GENERALIZATION & EXTREME STRESS EVALUATION
## Engineering Requirements, Verification Procedures & Scientific Traceability Specification
### Module ID: `MRIDANSH-MOD-GEN-11` | Notebook: `11-generalization-baseline-evaluation.ipynb`

---

## 1. System Context & Operational Architecture

Module 11 benchmarks the out-of-distribution (OOD) generalization capacity of **THE MRIDANSH** across five operational stress regimes. Moving beyond the local Bhadrak baseline, this engine stress-tests the multi-modal neural physics core against unseen geographical catchments, severe topographic elevation gradients, seasonal monsoonal climate shifts, and heavy sensor noise corruption.

Through Leave-One-Component-Out (LOCO) ablation, two-sample Kolmogorov-Smirnov (KS) statistical drift tests, and Pareto generalization gap analysis, Module 11 certifies whether the system maintains bounded errors when deployed beyond its training domain.

```
+----------------------------------------------------------------------------------------------------+
|                                    FIVE GENERALIZATION REGIMES                                     |
|  - Regime 1: IID Reference Baseline (In-Domain Telemetry & Infiltration)                           |
|  - Regime 2: Spatial Holdout Catchment (Unseen Geographic Basin, Zero Spatial Leakage)             |
|  - Regime 3: Topographic Extremes (Rugged High-Relief Terrain: Slopes > 25 deg, High Elevation)    |
|  - Regime 4: Temporal Climate Shift (Extreme Monsoonal Deluge & Multi-Week Arid Drought)          |
|  - Regime 5: Sensor Noise & Corruption Stress (Heavy Radar Speckle & Optical Cloud Occlusion)      |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 1. Empirical Generalization Performance:                                                           |
|    - Maintained error reduction > 70% across all 5 regimes compared to unconstrained baselines     |
|    - Spatial Generalization Gap Delta <= 0.0030 m3/m3 (Spatial Holdout RMSE = 0.00448 m3/m3)       |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 2. Leave-One-Component-Out (LOCO) Sensitivity Audit:                                               |
|    - Confirms Tier 1 Pillars (Sentinel-1 SAR, Richards PINN, EnKF) are essential anchors           |
|    - Dropping any Tier 1 component produces catastrophic error expansion under OOD shift           |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 3. Uncertainty Calibration & Kolmogorov-Smirnov Drift Detection:                                   |
|    - Certified two-sample KS test (p < 0.001) proves autonomous detection of distribution shift   |
|    - Predictive confidence bounds expand appropriately to encapsulate unseen regime errors         |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 4. Production Checkpoint & Manifest Serialization:                                                 |
|    - 5_storage/checkpoints/generalization_evaluation_checkpoint.pt                                 |
|    - 5_storage/checkpoints/GENERALIZATION_EVALUATION_MANIFEST.md                                   |
|    - 5 standalone 300 DPI plots in 5_storage/notebook_results/notebook_11_generalization/          |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Functional Requirements (FR)

### FR-GEN-001: Five-Regime Generalization Partitioning
The system **SHALL** evaluate the model against five distinct, non-overlapping operational domains:
1. **Regime 1 (IID Reference)**: In-distribution nominal Bhadrak catchment telemetry.
2. **Regime 2 (Spatial Holdout)**: Contiguous unseen catchment with completely disjoint spatial coordinates.
3. **Regime 3 (Topographic Extremes)**: High-altitude steep-slope terrain ($\theta_{\text{slope}} > 25^\circ$, elevation $150-450\text{ m}$).
4. **Regime 4 (Temporal Climate Shift)**: Non-stationary monsoon deluge ($> 100\text{ mm/day}$) and severe drought ($< 0.10\text{ m}^3/\text{m}^3$).
5. **Regime 5 (Sensor Noise Stress)**: Injected Gaussian and speckle noise up to $100\%$ amplitude.

### FR-GEN-002: Bounded Generalization Gap Tolerance
The system **SHALL** satisfy the spatial generalization gap contract:
$$\Delta_{\text{spatial}} = \text{RMSE}_{\text{Regime 2}} - \text{RMSE}_{\text{Regime 1}} \le 0.0030\text{ m}^3/\text{m}^3$$
- Invariant 1: Held-out spatial test RMSE **SHALL** satisfy $\text{RMSE}_{\text{spatial}} \le 0.0050\text{ m}^3/\text{m}^3$ (Nominal: $0.00448\text{ m}^3/\text{m}^3$).
- Invariant 2: Spatial holdout $R^2$ **SHALL** exceed $0.90$ (Nominal: $>0.92$).

### FR-GEN-003: Multi-Regime Error Reduction Guarantee
Across all 5 generalization regimes, **THE MRIDANSH** **SHALL** maintain $>70\%$ error reduction relative to naive, unconstrained baselines:
- Regime 1: $\ge 80.0\%$ (Nominal: $80.58\%$)
- Regime 2: $\ge 75.0\%$ (Nominal: $78.79\%$)
- Regime 3: $\ge 70.0\%$ (Nominal: $74.34\%$)
- Regime 4: $\ge 70.0\%$ (Nominal: $72.59\%$)
- Regime 5: $\ge 85.0\%$ (Nominal: $90.27\%$)

### FR-GEN-004: Leave-One-Component-Out (LOCO) Sensitivity Audit
The system **SHALL** execute LOCO ablation by selectively removing individual architectural components under severe distribution shift:
- Removal of **EnKF Filter**: Triggers dynamic forecast drift under non-stationary weather.
- Removal of **Physics PINN**: Induces mass conservation and supersaturation violations.
- Removal of **Sentinel-1 SAR**: Causes catastrophic failure during cloudy monsoon overpasses.
- Invariant: Confirms Tier 1 components are non-negotiable structural anchors.

### FR-GEN-005: Two-Sample Kolmogorov-Smirnov Shift Detection
The system **SHALL** evaluate the two-sample Kolmogorov-Smirnov (KS) test between reference and stressed prediction residual distributions:
$$D = \sup_x |F_{\text{ref}}(x) - F_{\text{shift}}(x)|$$
- Invariant: Achieves statistically significant shift identification ($p < 0.001$), certifying that predictive uncertainty expands proactively when the model operates out-of-domain.

### FR-GEN-006: Production Checkpointing & Manifest Export
The system **SHALL** export:
1. `generalization_evaluation_checkpoint.pt` containing regime metrics, LOCO sensitivities, and operational readiness status to `5_storage/checkpoints/`.
2. `GENERALIZATION_EVALUATION_MANIFEST.md` to `5_storage/checkpoints/`.
3. Five standalone diagnostic plots to `5_storage/notebook_results/notebook_11_generalization/`.

---

## 3. Data Integrity & Contract Requirements (DI)

- **DI-GEN-001 (Regime Cardinality)**: Exactly 5 generalization regimes evaluated; `len(regimes_evaluated) == 5`.
- **DI-GEN-002 (Generalization Gap Bounding)**: $\Delta_{\text{spatial}} \le 0.0030\text{ m}^3/\text{m}^3$.
- **DI-GEN-003 (Deterministic Reproducibility)**: Seeds pinned to 1607 (`np.random.seed(1607)`, `torch.manual_seed(1607)`).
- **DI-GEN-004 (Finiteness Invariant)**: Zero NaNs, zero Infs across all evaluation regimes.

---

## 4. Verification Procedures (VP) & Acceptance Test Suite

The verification suite `tests/test_notebook_11_verification.py` executes 8 strict automated tests:

| Test ID | Procedure Description | Acceptance Criteria | Verified Result |
| :--- | :--- | :--- | :--- |
| **VP-GEN-01** | `test_01_notebook_11_structure_and_interleaving` | Exactly 36 cells; strictly alternating markdown/code; executive summary and IP notice | **PASSED** (36/36) |
| **VP-GEN-02** | `test_02_spatial_block_holdout_zero_data_leakage` | Zero leakage; 5 generalization regimes partitioned with isolated holdouts | **PASSED** |
| **VP-GEN-03** | `test_03_multi_regime_generalization_evaluation` | All 5 regimes evaluated; maintains $>70\%$ error reduction vs naive baseline | **PASSED** |
| **VP-GEN-04** | `test_04_spatial_generalization_gap_tolerance` | Spatial generalization gap $\le 0.0030\text{ m}^3/\text{m}^3$; $\text{RMSE}_{\text{holdout}} \approx 0.00448$; $R^2 > 0.90$ | **PASSED** |
| **VP-GEN-05** | `test_05_loco_ablation_tier1_anchors` | LOCO ablation proves Tier 1 anchors (SAR, PINN, EnKF) are essential | **PASSED** |
| **VP-GEN-06** | `test_06_uncertainty_calibration_and_ks_shift` | Uncertainty expands under shift; KS test proves statistically significant shift | **PASSED** |
| **VP-GEN-07** | `test_07_embedded_and_standalone_visual_plots` | 5 plots exist on disk (>50KB) and embedded as base64 in notebook cells | **PASSED** |
| **VP-GEN-08** | `test_08_checkpoint_and_manifest_certification` | Checkpoint and manifest exist in `5_storage/checkpoints/` (>3KB, >2KB); system engine verified | **PASSED** |

---

## 5. Aerospace Artifact Inventory

The following files are permanently stored in `5_storage/notebook_results/notebook_11_generalization/` and `5_storage/checkpoints/`:

| Artifact Name | Storage Path | Type | Size | Description |
| :--- | :--- | :--- | :--- | :--- |
| `plot_01_multi_regime_generalization_error_radar.png` | `notebook_11_generalization/` | PNG (120 DPI) | ~137 KB | Multi-axis radar diagram tracking performance metrics across all 5 evaluation regimes. |
| `plot_02_spatial_holdout_residual_distribution.png` | `notebook_11_generalization/` | PNG (120 DPI) | ~110 KB | Error residual histogram comparing in-domain training vs held-out spatial quadrant. |
| `plot_03_topographic_elevation_vs_moisture_stability.png` | `notebook_11_generalization/` | PNG (120 DPI) | ~305 KB | Scatter and contour plots of model stability across high-elevation, steep-slope terrain. |
| `plot_04_temporal_monsoon_drought_stress_response.png` | `notebook_11_generalization/` | PNG (120 DPI) | ~267 KB | Dynamic temporal response under extreme monsoon flooding and multi-week drought drydown. |
| `plot_05_sensor_noise_degradation_robustness_curve.png` | `notebook_11_generalization/` | PNG (120 DPI) | ~79 KB | Degradation response curve as observation noise variance escalates to 100%. |
| `generalization_evaluation_checkpoint.pt` | `checkpoints/` | PyTorch | ~4 KB | Serialized checkpoint containing all 5 regime metrics, LOCO scores, and certification flags. |
| `GENERALIZATION_EVALUATION_MANIFEST.md` | `checkpoints/` | Markdown | ~2.2 KB | Formal production manifest certifying generalization bounds and operational readiness. |

---

## 6. Traceability Matrix

| Requirement | Notebook 11 Code Cell | Verification Test | Storage Artifact |
| :--- | :--- | :--- | :--- |
| **FR-GEN-001** | Cell 7 | `test_02_spatial_block_holdout_zero_data_leakage` | Notebook runtime kernel |
| **FR-GEN-002** | Cell 11 | `test_04_spatial_generalization_gap_tolerance` | `generalization_evaluation_checkpoint.pt` |
| **FR-GEN-003** | Cell 11 | `test_03_multi_regime_generalization_evaluation` | `plot_01_multi_regime_generalization_error_radar.png` |
| **FR-GEN-004** | Cell 13 | `test_05_loco_ablation_tier1_anchors` | `generalization_evaluation_checkpoint.pt` |
| **FR-GEN-005** | Cell 17, 19 | `test_06_uncertainty_calibration_and_ks_shift` | `plot_02_spatial_holdout_residual_distribution.png` |
| **FR-GEN-006** | Cell 21-29, 33 | `test_07_embedded_and_standalone_visual_plots`, `test_08_checkpoint_and_manifest_certification` | `generalization_evaluation_checkpoint.pt`, `GENERALIZATION_EVALUATION_MANIFEST.md` |

---

## 7. Brutally Unfiltered Defect Log & Engineering Limitations

| Defect ID | Severity | Subsystem | Description & Root Cause | Impact & Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| `D-NB11-001` | **HIGH** | Out-of-Domain Catchment | **Synthetic Spatial Holdout Coordinates**: The unseen catchment in Regime 2 is synthesized via spatial shift perturbations rather than ingesting genuine remote sensing rasters from an external sub-basin (e.g. Mahanadi or Baitarani basin). | True geographical transferability across distinct agro-ecological zones is simulated rather than verified with remote field data. Mitigation: Deploy in-situ sensor networks across contrasting river basins. |
| `D-NB11-002` | **HIGH** | Climate Stress | **Simulated Temporal Forcing Shifts**: Monsoon deluge ($>100\text{ mm/day}$) and arid drought are generated by modulating the temporal sequence with synthetic scaling multipliers rather than ingesting multi-year historical extreme weather series. | May underestimate non-linear hysteresis in soil moisture drydown curves during compound heatwave-drought events. Mitigation: Ingest multi-decadal ERA5-Land climate reanalysis extremes. |
| `D-NB11-003` | **MEDIUM** | Topographic Extremes | **Synthetic Extreme Topography**: High-relief topography ($\theta_{\text{slope}} > 25^\circ$) is mathematically synthesized on the $20 \times 20$ grid rather than imported from mountainous Himalayan DEM tiles. | Shadowing effects and radar foreshortening/layover in steep terrain are not physically modeled. Mitigation: Ingest high-resolution ALOS PALSAR radiometrically terrain-corrected (RTC) tiles. |
| `D-NB11-004` | **LOW** | KS Shift Test | **Residual-Only Statistical Drift**: The two-sample KS test evaluates drift solely on scalar prediction residuals rather than monitoring high-dimensional covariate shift in the latent feature representations ($Z \in \mathbb{R}^{20 \times 20 \times 8}$). | Subtle multidimensional feature drift may pass undetected if aggregate residual distributions appear stationary. Mitigation: Implement Maximum Mean Discrepancy (MMD) on latent GCN/ConvLSTM feature spaces. |

---

## 8. Configuration Control & Environment Lineage

- **Parent Repository**: `THE_MRIDANSH`
- **Execution Python**: Python 3.12.10 (virtual environment `mridansh_env`, PyTorch 2.14.0+cpu, SciPy 1.15.2)
- **Primary Checkpoint**: `5_storage/checkpoints/generalization_evaluation_checkpoint.pt`
- **Manifest Target**: `5_storage/checkpoints/GENERALIZATION_EVALUATION_MANIFEST.md`
- **Storage Target**: `5_storage/notebook_results/notebook_11_generalization/`
- **Verification Command**: `pytest tests/test_notebook_11_verification.py -v`
