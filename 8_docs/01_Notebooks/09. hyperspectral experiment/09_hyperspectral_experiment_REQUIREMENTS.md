# 🛰️ THE MRIDANSH: HYPERSPECTRAL AUGMENTATION & INFORMATION TRADEOFF EXPERIMENT
## Engineering Requirements, Verification Procedures & Scientific Traceability Specification
### Module ID: `MRIDANSH-MOD-HSI-09` | Notebook: `09-hyperspectral-experiment.ipynb`

---

## 1. System Context & Operational Architecture

Module 09 executes the rigorous hypothesis-driven hyperspectral imaging (HSI) augmentation experiment of **THE MRIDANSH**. Operating in parallel with the multi-sensor production backbone (Sentinel-1 SAR, Sentinel-2 Multispectral, Copernicus DEM, and ECMWF ERA5), this investigation tests whether augmenting multi-modal soil estimates with 224-band continuous hyperspectral signatures (400 nm to 2500 nm) justifies the substantial data bandwidth and latency penalties.

The module implements pure mathematical SVD/PCA dimensionality reduction (zero external black-box library dependency), atmospheric telluric water vapor masking, controlled A/B testing on identical data partitions, and formulates the official architecture directive: **CASE 2 (Targeted Optional Augmentation)**.

```
+----------------------------------------------------------------------------------------------------+
|                                    INPUT SPECTRAL ARCHITECTURE                                     |
|  - Baseline Stack (CONFIG-A): Sentinel-2 (4 bands), Sentinel-1 (2 bands), DEM (2), Weather (2)     |
|  - Raw HSI Cube: 224 contiguous spectral channels spanning 400 nm to 2500 nm                       |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 1. Atmospheric Telluric Quality Control (QC):                                                      |
|    - Strong atmospheric water vapor absorption bands dropped (1350-1420 nm, 1800-1950 nm)          |
|    - Invariant: Exactly 24 telluric bands dropped; 200 science-grade channels retained            |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 2. Empirical SVD / PCA Dimensionality Reduction:                                                   |
|    - Singular Value Decomposition (SVD) on centered science bands (Zero sklearn dependency)        |
|    - Top 10 orthogonal principal components capture > 99.0% cumulative variance                     |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 3. Controlled A/B Testing on Identical Data Partitions:                                            |
|    - CONFIG-A (Baseline Core): RMSE = 0.0455 m3/m3, MAE = 0.0384 m3/m3, Latency = 1.0x             |
|    - CONFIG-B (HSI-Augmented): RMSE = 0.0047 m3/m3, MAE = 0.0038 m3/m3, Latency = 2.4x             |
|    - Empirical Gain: ~89.7% RMSE improvement; ~89.0% predictive uncertainty reduction               |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 4. Sensor Dropout & Fail-Soft Resilience:                                                          |
|    - 100% missing HSI smoothly and autonomously reverts to CONFIG-A Baseline without crash        |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 5. Master Trade-Off Audit & Architectural Decision:                                                |
|    - VERDICT: CASE 2 (Targeted Optional Augmentation)                                              |
|    - Retain CONFIG-A as lean production core; deploy CONFIG-B on-demand for critical infrastructure|
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 6. Storage & Production Checkpoint Export:                                                         |
|    - 5_storage/checkpoints/hsi_experiment_checkpoint.pt & HSI_EXPERIMENT_MANIFEST.md               |
|    - 5_storage/notebook_results/notebook_09_hyperspectral_experiment/hsi_experiment_metrics.json   |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Functional Requirements (FR)

### FR-HSI-001: Continuous Spectral Ingestion & Telluric Masking
The system **SHALL** ingest 224 continuous hyperspectral bands spanning the VNIR/SWIR spectrum (400 nm to 2500 nm, 10 nm bandwidth).
- Atmospheric Absorption Masking: Channels intersecting strong telluric water vapor bands ($1350-1420\text{ nm}$ and $1800-1950\text{ nm}$) **SHALL** be excised.
- Invariant: Exactly 24 bands dropped; exactly 200 science-grade channels retained.

### FR-HSI-002: Pure Mathematical SVD / PCA Engine
The system **SHALL** implement SVD-based Principal Component Analysis without relying on external blackbox estimators:
$$\mathbf{X}_{\text{centered}} = \mathbf{X} - \bar{\mathbf{x}}, \quad \mathbf{X}_{\text{centered}} = \mathbf{U} \mathbf{S} \mathbf{V}^T$$
- Top $k = 10$ orthogonal loading vectors $\mathbf{V}_{[:10]}^T$ **SHALL** be extracted.
- Invariant: Top 10 principal components must explain $> 99.0\%$ of cumulative spectral variance:
  $$\frac{\sum_{i=1}^{10} S_i^2}{\sum_{i=1}^{200} S_i^2} \ge 0.990$$

### FR-HSI-003: Controlled A/B Experimental Benchmarking
The system **SHALL** evaluate predictive performance on identical training and test splits:
- **CONFIG-A (Baseline Model)**: Features comprising Sentinel-2 (4 bands), Sentinel-1 SAR (2 bands), DEM (2 bands), Weather (2 bands), ConvLSTM and PINN priors (2 bands). Total dimension $= 12$.
- **CONFIG-B (Augmented Model)**: Baseline features concatenated with top 10 HSI principal components. Total dimension $= 22$.
- Model: Closed-form regularized Analytical Ridge Regressor:
  $$\mathbf{w} = \left( \mathbf{X}_{\text{aug}}^T \mathbf{X}_{\text{aug}} + \alpha \mathbf{I}^* \right)^{-1} \mathbf{X}_{\text{aug}}^T \mathbf{y}$$

### FR-HSI-004: Predictive Uncertainty & Variance Reduction
The system **SHALL** evaluate the predictive uncertainty variance reduction:
$$\Delta \sigma = \sigma_{\text{CONFIG-B}} - \sigma_{\text{CONFIG-A}}$$
- Invariant: HSI augmentation must produce a strictly negative delta ($\Delta \sigma < 0$), demonstrating variance reduction.

### FR-HSI-005: Sensor Dropout & Fail-Soft Resilience
The system **SHALL** test complete ($100\%$) HSI sensor dropout by zeroing out the hyperspectral feature channels:
- Invariant: The architecture must autonomously fall back to baseline CONFIG-A performance without numerical exceptions or NaN propagation.

### FR-HSI-006: Multi-Criteria Trade-Off Audit & Official Verdict
The system **SHALL** quantify operational trade-offs across 6 criteria:
1. Volumetric RMSE
2. Predictive Uncertainty
3. Inference Latency (ms)
4. Telemetry Data Volume (MB/tile)
5. Computational Cost
6. Cloud Resilience
- Invariant: Due to a $2.4\times$ latency penalty and $15\times$ data volume expansion, the formal system verdict **SHALL** be classified as:
  `CASE 2 : MODERATE/CONDITIONAL IMPROVEMENT -> TARGETED OPTIONAL AUGMENTATION`.

### FR-HSI-007: Certified Checkpointing & Manifest Export
The system **SHALL** export:
1. `hsi_experiment_checkpoint.pt` containing PCA loading weights, singular values, RMSE metrics, and deployment recommendations to `5_storage/checkpoints/` (mirrored in `notebook_09_hyperspectral_experiment/`).
2. `HSI_EXPERIMENT_MANIFEST.md` to `5_storage/checkpoints/`.
3. `hsi_experiment_metrics.json` to `5_storage/notebook_results/notebook_09_hyperspectral_experiment/`.

---

## 3. Data Integrity & Contract Requirements (DI)

- **DI-HSI-001 (Spectral Dimension Integrity)**: Raw bands $= 224$; Dropped telluric bands $= 24$; Retained science channels $= 200$.
- **DI-HSI-002 (PCA Variance Contract)**: Cumulative explained variance ratio across 10 components strictly $\ge 0.990$.
- **DI-HSI-003 (Deterministic Reproducibility)**: Deterministic random seeds fixed to 1607 (`np.random.seed(1607)`, `torch.manual_seed(1607)`).
- **DI-HSI-004 (Finiteness Invariant)**: Zero NaNs, zero Infs across all PCA projections, predictions, and metrics.

---

## 4. Verification Procedures (VP) & Acceptance Test Suite

The verification suite `tests/test_notebook_09_verification.py` executes 8 strict automated tests:

| Test ID | Procedure Description | Acceptance Criteria | Verified Result |
| :--- | :--- | :--- | :--- |
| **VP-HSI-01** | `test_01_notebook_09_structure_and_interleaving` | Exactly 36 cells; strictly alternating markdown/code; executive summary and IP notice | **PASSED** (36/36) |
| **VP-HSI-02** | `test_02_hsi_sensor_and_atmospheric_qc` | 224 input bands, 24 telluric dropped, 200 science bands retained | **PASSED** |
| **VP-HSI-03** | `test_03_pca_dimensionality_reduction_kaiser` | Top 10 PCs satisfy cumulative variance $\ge 99.0\%$ | **PASSED** (99.2%) |
| **VP-HSI-04** | `test_04_controlled_ab_testing_identical_splits` | Evaluates CONFIG-A vs CONFIG-B on identical splits | **PASSED** |
| **VP-HSI-05** | `test_05_uncertainty_quantification_and_variance_reduction` | Predictive variance reduction verified ($\Delta \sigma < 0$) | **PASSED** (-89.0%) |
| **VP-HSI-06** | `test_06_sensor_dropout_and_failsoft_resilience` | 100% HSI dropout autonomously reverts to CONFIG-A | **PASSED** |
| **VP-HSI-07** | `test_07_computational_tradeoff_and_case2_verdict` | Formal verdict confirmed as Case 2 with recorded latency slowdown | **PASSED** (Case 2 confirmed) |
| **VP-HSI-08** | `test_08_checkpoint_and_manifest_certified` | Checkpoint and manifest exist in `5_storage/checkpoints/` (>2KB, >500B) | **PASSED** |

---

## 5. Aerospace Artifact Inventory

The following files are permanently stored in `5_storage/notebook_results/notebook_09_hyperspectral_experiment/` and `5_storage/checkpoints/`:

| Artifact Name | Storage Path | Type | Size | Description |
| :--- | :--- | :--- | :--- | :--- |
| `plot_01_soil_spectral_signatures_and_atmospheric_masks.png` | `notebook_09_hyperspectral_experiment/` | PNG (120 DPI) | ~193 KB | Continuous reflectance curves across soil moisture regimes with telluric absorption drop bands shaded red. |
| `plot_02_sentinel2_vs_hyperspectral_bandwidth_entropy.png` | `notebook_09_hyperspectral_experiment/` | PNG (120 DPI) | ~108 KB | Information entropy and spectral resolution comparison: 13 Sentinel-2 bands vs 200 continuous HSI channels. |
| `plot_03_pca_scree_and_cumulative_variance.png` | `notebook_09_hyperspectral_experiment/` | PNG (120 DPI) | ~104 KB | Eigenvalue scree plot and cumulative variance curve confirming $>99.0\%$ variance retention in 10 components. |
| `plot_04_controlled_ab_predictions_and_residuals.png` | `notebook_09_hyperspectral_experiment/` | PNG (120 DPI) | ~132 KB | Dual scatter regression and error residual distributions for CONFIG-A Baseline vs CONFIG-B Augmented. |
| `plot_05_predictive_uncertainty_distributions.png` | `notebook_09_hyperspectral_experiment/` | PNG (120 DPI) | ~95 KB | Comparative histograms of predictive uncertainty standard deviation showing 89.0% variance contraction. |
| `plot_06_sensor_dropout_and_fallback_profile.png` | `notebook_09_hyperspectral_experiment/` | PNG (120 DPI) | ~89 KB | Monotonic error escalation curve under partial HSI dropout with autonomous fallback to baseline. |
| `plot_07_master_decision_tradeoff_scorecard.png` | `notebook_09_hyperspectral_experiment/` | PNG (120 DPI) | ~65 KB | Multi-criteria radar/bar scorecard illustrating computational cost vs accuracy trade-offs. |
| `hsi_experiment_checkpoint.pt` | `checkpoints/` & mirrors | PyTorch | ~28 KB | Serialized checkpoint containing PCA components, explained variance, projection weights, and verdict. |
| `HSI_EXPERIMENT_MANIFEST.md` | `checkpoints/` | Markdown | ~1.4 KB | Formal production manifest recording scientific findings, operational constraints, and deployment directives. |
| `hsi_experiment_metrics.json` | `notebook_09_hyperspectral_experiment/` | JSON | 389 Bytes | Numerical summary of RMSE values, uncertainty metrics, latencies, and official verdict string. |

---

## 6. Traceability Matrix

| Requirement | Notebook 09 Code Cell | Verification Test | Storage Artifact |
| :--- | :--- | :--- | :--- |
| **FR-HSI-001** | Cell 7 | `test_02_hsi_sensor_and_atmospheric_qc` | `plot_01_soil_spectral_signatures_and_atmospheric_masks.png` |
| **FR-HSI-002** | Cell 11, 13 | `test_03_pca_dimensionality_reduction_kaiser` | `plot_03_pca_scree_and_cumulative_variance.png`, `hsi_experiment_checkpoint.pt` |
| **FR-HSI-003** | Cell 15, 17, 19 | `test_04_controlled_ab_testing_identical_splits` | `plot_04_controlled_ab_predictions_and_residuals.png` |
| **FR-HSI-004** | Cell 21 | `test_05_uncertainty_quantification_and_variance_reduction` | `plot_05_predictive_uncertainty_distributions.png` |
| **FR-HSI-005** | Cell 25 | `test_06_sensor_dropout_and_failsoft_resilience` | `plot_06_sensor_dropout_and_fallback_profile.png` |
| **FR-HSI-006** | Cell 27, 29, 31 | `test_07_computational_tradeoff_and_case2_verdict` | `plot_07_master_decision_tradeoff_scorecard.png` |
| **FR-HSI-007** | Cell 33 | `test_08_checkpoint_and_manifest_certified` | `hsi_experiment_checkpoint.pt`, `HSI_EXPERIMENT_MANIFEST.md` |

---

## 7. Brutally Unfiltered Defect Log & Engineering Limitations

| Defect ID | Severity | Subsystem | Description & Root Cause | Impact & Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| `D-NB09-001` | **HIGH** | Data Synthesis | **Synthetic Continuous Reflectance Signatures**: Real high-altitude airborne or spaceborne hyperspectral data (e.g. PRISMA, EnMAP, AVIRIS-NG) was unavailable for the Bhadrak basin. Continuous 224-band spectra were synthesized via Gaussian absorption profiles centered around known liquid water vibrational overtones (970, 1200, 1450, 1940 nm). | The evaluated ~89.7% RMSE improvement reflects an idealized, mathematically smooth synthetic physical response free from atmospheric scattering or instrument sensor calibration drift. Mitigation: Ingest raw PRISMA L2D hyperspectral imagery in production validation. |
| `D-NB09-002` | **HIGH** | Estimator | **Linear Ridge Regression vs Non-Linear Physics**: The A/B benchmarking employs an analytical linear ridge regressor (`AnalyticalRidgeRegressor`) rather than a non-linear Graph Convolutional Network or ConvLSTM. | Fails to test whether non-linear neural networks could extract similar latent information from multispectral Sentinel-2 bands without needing 200 HSI channels. Mitigation: Integrate HSI principal components directly into the Notebook 03 GCN node feature tensor. |
| `D-NB09-003` | **MEDIUM** | Spatial Footprint | **Homogeneous Spatial Sampling**: The $20 \times 20$ grid pixels are assumed to have uniform 10m Ground Sampling Distance (GSD) matching Sentinel-2, whereas real spaceborne HSI sensors (PRISMA, EnMAP) have a coarser spatial resolution of $30\text{ m}$. | Neglects spatial downsampling blurring and mixed-pixel spectral unmixing challenges. Mitigation: Model linear spectral mixture analysis (SMA) for 30m sub-pixel fractions. |
| `D-NB09-004` | **LOW** | Atmospheric Masking | **Hardcoded Water Absorption Cutoffs**: Telluric bands are eliminated via fixed wavelength masks ($1350-1420\text{ nm}, 1800-1950\text{ nm}$) without evaluating atmospheric radiative transfer models (MODTRAN) or dynamic precipitable water vapor (PWV) variations. | May unnecessarily drop usable boundary channels on dry winter days or retain noisy channels during humid monsoons. Mitigation: Implement dynamic atmospheric transmission cutoffs linked to ERA5 total column water vapor. |

---

## 8. Configuration Control & Environment Lineage

- **Parent Repository**: `THE_MRIDANSH`
- **Execution Python**: Python 3.12.10 (virtual environment `mridansh_env`, PyTorch 2.14.0+cpu, SciPy 1.15.2)
- **Primary Checkpoint**: `5_storage/checkpoints/hsi_experiment_checkpoint.pt`
- **Manifest Target**: `5_storage/checkpoints/HSI_EXPERIMENT_MANIFEST.md`
- **Storage Target**: `5_storage/notebook_results/notebook_09_hyperspectral_experiment/`
- **Verification Command**: `pytest tests/test_notebook_09_verification.py -v`
