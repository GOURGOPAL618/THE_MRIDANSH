# 🛰️ THE MRIDANSH: SEQUENTIAL STATE ESTIMATION & ENSEMBLE KALMAN FILTER
## Engineering Requirements, Verification Procedures & Scientific Traceability Specification
### Module ID: `MRIDANSH-MOD-STATE-06` | Notebook: `06-state-estimation.ipynb`

---

## 1. System Context & Operational Architecture

Module 06 establishes the data assimilation and sequential state estimation core of **THE MRIDANSH**. Ingesting upstream telemetry from `02-preprocessing`, temporal ConvLSTM rollout dynamics from `04-temporal-modeling`, and van Genuchten hydraulic constraints from `05-physics-validation`, this engine executes a stochastic Ensemble Kalman Filter (EnKF, Burgers et al. 1998; Evensen 2003) across a 4-dimensional physical soil-state space ($\theta_{\text{root}}$, bulk density $\rho_b$, hydraulic conductivity $K_{\text{sat}}$, and Soil Organic Carbon $\text{SOC}$). It bridges 1D point assimilation with 2D spatial grid updates ($20 \times 20$ nodes), proving that satellite data assimilation reduces forecasting error by $>70\%$ and contracts state uncertainty.

```
+----------------------------------------------------------------------------------------------------+
|                                    UPSTREAM ARTIFACT INGESTION                                     |
|  - Telemetry: 5_storage/notebook_results/notebook_02_preprocessing/preprocessed_telemetry.csv       |
|  - Temporal Latent: 5_storage/notebook_results/notebook_04_temporal_modeling/temporal_latent_states.pt|
|  - Physics Checkpoint: 5_storage/checkpoints/pinn_richards_model.pt (Loam subgrade Ks, theta_s/r)   |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 1. 4D Target State Vector Space & Pedological Cross-Correlations:                                  |
|    - States: theta_root (m3/m3), bulk_density (g/cm3), K_sat (cm/hr), SOC (%)                      |
|    - Physically bounded Cholesky-correlated prior ensemble (N_e = 50 stochastic members)           |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 2. Stochastic Ensemble Kalman Filter (EnKF) Mechanics:                                             |
|    - Prior Ensemble Matrix: X^f in R^(4 x 50), Perturbed Observations d_j ~ N(y, R)                |
|    - Innovation Covariance: S = H P^f H^T + R                                                      |
|    - Cross-Covariance Kalman Gain: K = P^f H^T S^(-1)                                              |
|    - Analysis Update: X^a = X^f + K (D - H X^f)                                                    |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 3. Dynamic Sequential Infiltration Trajectory:                                                     |
|    - 14-timestep recursive filtering tracking wetting and recession phases                         |
|    - Benchmark: Unconstrained prediction drift RMSE vs EnKF posterior RMSE (Error reduction > 70%) |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 4. 2D Catchment Spatial Grid Assimilation:                                                         |
|    - 20 x 20 node grid state updating using spatial observation masks                              |
|    - Invariant: Mean spatial variance reduction >= 50.0%                                           |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 5. Multi-Tier State Database & Manifest Export:                                                    |
|    - 5_storage/state_database/enkf_state_database.pt & ENKF_STATE_ESTIMATION_MANIFEST.md           |
|    - 5_storage/notebook_results/notebook_06_state_estimation/enkf_state_estimation_metrics.json    |
|    - Mirrors in data/processed/enkf_assimilation_bundle.pt                                         |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Functional Requirements (FR)

### FR-STATE-001: Upstream Ingestion & Calibrated Anchoring
The system **SHALL** locate and ingest:
1. `preprocessed_telemetry.csv` from Notebook 02.
2. `temporal_latent_states.pt` from Notebook 04.
3. `pinn_richards_model.pt` from `5_storage/checkpoints/` (Notebook 05).
- Calibrate nominal moisture baseline: $\theta_{\text{root}} = 0.22 + 0.12 \times \frac{\sigma^0_{VV} - \min(\sigma^0_{VV})}{\max(\sigma^0_{VV}) - \min(\sigma^0_{VV})}$.
- Anchor soil porosity limits to PINN Loam constants ($\theta_r = 0.078, \theta_s = 0.430\text{ m}^3/\text{m}^3, K_s = 1.04\text{ cm/hr}$).

### FR-STATE-002: 4D Soil-State Vector Definition & Boundary Contracts
The system **SHALL** define the 4-dimensional state vector $\mathbf{x} = [\theta_{\text{root}}, \rho_b, K_{\text{sat}}, \text{SOC}]^T$:
- `theta_root`: Volumetric root-zone moisture, bounds $[0.078, 0.430]\text{ m}^3/\text{m}^3$.
- `bulk_density`: Dry bulk density $\rho_b$, bounds $[1.00, 1.80]\text{ g/cm}^3$.
- `K_sat`: Saturated hydraulic conductivity, bounds $[0.01, 10.0]\text{ cm/hr}$.
- `SOC`: Soil Organic Carbon percentage, bounds $[0.10, 4.00]\%$.

### FR-STATE-003: Pedological Cross-Correlation & Ensemble Generation
The system **SHALL** instantiate a 50-member stochastic ensemble ($N_e = 50$) sampled from a multivariate Gaussian distribution with prescribed pedological correlation structure:
$$\mathbf{C} = \begin{bmatrix} 1.00 & -0.45 & +0.50 & +0.30 \\ -0.45 & 1.00 & -0.40 & -0.65 \\ +0.50 & -0.40 & 1.00 & +0.25 \\ +0.30 & -0.65 & +0.25 & 1.00 \end{bmatrix}$$
$$\mathbf{X}^f = \bar{\mathbf{x}} + \mathbf{L} \mathbf{Z}, \quad \mathbf{L}\mathbf{L}^T = \mathbf{\Sigma} = \operatorname{diag}(\boldsymbol{\sigma}) \mathbf{C} \operatorname{diag}(\boldsymbol{\sigma}), \quad \mathbf{Z} \sim \mathcal{N}(\mathbf{0}, \mathbf{I})$$
All ensemble members **SHALL** be clamped to physical state boundaries.

### FR-STATE-004: Stochastic Ensemble Kalman Filter Mechanics
The system **SHALL** implement the perturbed-observation EnKF algorithm:
1. Prior Ensemble Mean and Anomaly:
   $$\bar{\mathbf{x}}^f = \frac{1}{N_e} \sum_{j=1}^{N_e} \mathbf{x}_j^f, \quad \mathbf{A}^f = \mathbf{X}^f - \bar{\mathbf{x}}^f \mathbf{1}^T$$
2. Prior Error Covariance:
   $$\mathbf{P}^f = \frac{1}{N_e - 1} \mathbf{A}^f (\mathbf{A}^f)^T$$
3. Perturbed Observation Ensemble:
   $$\mathbf{d}_j = \mathbf{y} + \boldsymbol{\epsilon}_j, \quad \boldsymbol{\epsilon}_j \sim \mathcal{N}(\mathbf{0}, \mathbf{R})$$
4. Innovation Covariance & Kalman Gain:
   $$\mathbf{S} = \mathbf{H} \mathbf{P}^f \mathbf{H}^T + \mathbf{R}, \quad \mathbf{K} = \mathbf{P}^f \mathbf{H}^T \mathbf{S}^{-1}$$
5. Analysis Update:
   $$\mathbf{x}_j^a = \mathbf{x}_j^f + \mathbf{K} \left( \mathbf{d}_j - \mathbf{H} \mathbf{x}_j^f \right)$$

### FR-STATE-005: Cross-Variable State Updating
Because $\mathbf{P}^f$ maintains non-zero cross-covariances between moisture and unobserved variables ($\rho_b, K_{\text{sat}}, \text{SOC}$), the Kalman gain $\mathbf{K}$ **SHALL** produce physically meaningful updates for all 4 states from surface moisture observations alone:
- Moisture update: $K_{\theta} > 0.0$
- Bulk density update: $K_{\rho_b} < 0.0$ (reflecting negative pedological correlation).

### FR-STATE-006: Dynamic Sequential Trajectory Filtering
The system **SHALL** execute a 14-timestep sequential assimilation experiment tracking non-stationary storm wetting and drydown:
- Invariant 1: $\text{RMSE}_{\text{EnKF}} < 0.025\text{ m}^3/\text{m}^3$.
- Invariant 2: Error reduction rate relative to pure prediction **SHALL** exceed $70.0\%$:
  $$\frac{\text{RMSE}_{\text{pred}} - \text{RMSE}_{\text{EnKF}}}{\text{RMSE}_{\text{pred}}} \times 100\% \ge 70.0\%$$
- Invariant 3: Root-zone moisture uncertainty reduction **SHALL** exceed $35.0\%$:
  $$\frac{\sigma_{\text{prior}} - \sigma_{\text{post}}}{\sigma_{\text{prior}}} \times 100\% \ge 35.0\%$$

### FR-STATE-007: 2D Catchment Spatial Grid Assimilation
The system **SHALL** assimilate 2D spatial moisture grids on the $20 \times 20$ node mesh ($N = 400$):
- Invariant: Mean spatial variance reduction across the grid **SHALL** exceed $50.0\%$.

### FR-STATE-008: Observation Noise Sensitivity Sweep
The system **SHALL** evaluate filter convergence across 10 observation noise variances $R \in [10^{-4}, 10^{-1}]$:
- Invariant: Kalman gain trace $\operatorname{Tr}(\mathbf{K})$ must monotonically decrease as sensor noise $R \to \infty$.

### FR-STATE-009: Multi-Tier State Database & Manifest Export
The system **SHALL** export:
1. Production state database `enkf_state_database.pt` to `5_storage/state_database/` (mirrored in `5_storage/notebook_results/notebook_06_state_estimation/` and `data/processed/enkf_assimilation_bundle.pt`).
2. Production manifest `ENKF_STATE_ESTIMATION_MANIFEST.md` to `5_storage/state_database/`.
3. Metrics summary `enkf_state_estimation_metrics.json` to `5_storage/notebook_results/notebook_06_state_estimation/`.

---

## 3. Data Integrity & Contract Requirements (DI)

- **DI-STATE-001 (Ensemble Dimensions)**: Prior $\mathbf{X}^f$ and posterior $\mathbf{X}^a$ matrices strictly conform to shape $(4, 50)$.
- **DI-STATE-002 (Covariance Symmetry)**: $\mathbf{P}^f = (\mathbf{P}^f)^T$ and $\mathbf{P}^a = (\mathbf{P}^a)^T$; all eigenvalues non-negative.
- **DI-STATE-003 (Variance Contraction)**: Posterior variance strictly less than prior variance: $\mathbf{P}^a_{ii} < \mathbf{P}^f_{ii}$ for all states $i$.
- **DI-STATE-004 (Physical Bounds Guarantee)**: 100% of posterior ensemble members satisfy state bounds $[\min_i, \max_i]$.
- **DI-STATE-005 (Finiteness Invariant)**: Zero NaNs, zero Infs in state database, gain matrix, and metrics.

---

## 4. Verification Procedures (VP) & Acceptance Test Suite

The verification suite `tests/test_notebook_06_verification.py` executes 7 strict automated tests:

| Test ID | Procedure Description | Acceptance Criteria | Verified Result |
| :--- | :--- | :--- | :--- |
| **VP-STATE-01** | `test_01_no_python_scripts_in_notebook_dir` | Directory `1_notebooks_sandbox/` contains 0 `.py` scripts | **PASSED** |
| **VP-STATE-02** | `test_02_notebook_cell_structure_and_markdown_rules` | Notebook length $\ge 30$ cells; every code cell preceded by markdown | **PASSED** (32 cells) |
| **VP-STATE-03** | `test_03_all_code_cells_executed_with_zero_errors` | Exactly 15 code cells; all executed; zero error outputs | **PASSED** (15/15 executed) |
| **VP-STATE-04** | `test_04_penultimate_and_ultimate_markdown_cells` | Penultimate contains Executive Summary; Ultimate contains IP notice | **PASSED** |
| **VP-STATE-05** | `test_05_storage_artifacts_and_plots_persisted` | 5 plots (>50KB) and metrics JSON exist in storage | **PASSED** |
| **VP-STATE-06** | `test_06_checkpoint_and_manifest_compliance` | State DB & manifest exist in `5_storage/state_database/` with dual persistence; shape $(4, 50)$; all finite | **PASSED** |
| **VP-STATE-07** | `test_07_assimilation_validation_and_error_reduction` | Error reduction $\ge 70\%$, posterior RMSE $< 0.025$, moisture uncertainty reduction $\ge 35\%$, spatial variance reduction $\ge 50\%$, filter status `CONVERGED_STABLE` | **PASSED** |

---

## 5. Aerospace Artifact Inventory

The following files are permanently stored in `5_storage/notebook_results/notebook_06_state_estimation/` and `5_storage/state_database/`:

| Artifact Name | Storage Path | Type | Size | Description |
| :--- | :--- | :--- | :--- | :--- |
| `plot_01_prior_vs_posterior_distributions.png` | `notebook_06_state_estimation/` | PNG (120 DPI) | ~198 KB | 4-panel histogram comparing prior vs posterior distributions across all 4 state variables. |
| `plot_02_kalman_gain_cross_covariance.png` | `notebook_06_state_estimation/` | PNG (120 DPI) | ~98 KB | Heatmap of prior covariance $\mathbf{P}^f$, posterior $\mathbf{P}^a$, and Kalman gain vector $\mathbf{K}$. |
| `plot_03_dynamic_trajectory_convergence.png` | `notebook_06_state_estimation/` | PNG (120 DPI) | ~153 KB | 14-timestep tracking graph: Ground Truth vs Pure Prediction vs EnKF Posterior with $\pm 1\sigma$ envelope. |
| `plot_04_noise_sensitivity_sweep.png` | `notebook_06_state_estimation/` | PNG (120 DPI) | ~126 KB | Semi-log curves illustrating Kalman weight adaptation across observation noise variance $R \in [10^{-4}, 10^{-1}]$. |
| `plot_05_spatial_grid_enkf_assimilation.png` | `notebook_06_state_estimation/` | PNG (120 DPI) | ~86 KB | 4-panel $20 \times 20$ spatial grid maps: Prior Mean, Observation, Posterior Mean, and Variance Reduction. |
| `enkf_state_database.pt` | `state_database/` & mirrors | PyTorch | ~16 KB | Serialized state database bundle (state names, ensembles, gains, trajectories, spatial grids). |
| `ENKF_STATE_ESTIMATION_MANIFEST.md` | `state_database/` | Markdown | ~1.1 KB | Formal manifest recording filter type, state definitions, RMSE improvements, and storage paths. |
| `enkf_state_estimation_metrics.json` | `notebook_06_state_estimation/` | JSON | 570 Bytes | Quantitative summary of errors, reduction rates, Kalman gain trace, and stability flag. |

---

## 6. Traceability Matrix

| Requirement | Notebook 06 Code Cell | Verification Test | Storage Artifact |
| :--- | :--- | :--- | :--- |
| **FR-STATE-001** | Cell 2 | `test_03_all_code_cells_executed_with_zero_errors` | `preprocessed_telemetry.csv`, `pinn_richards_model.pt` |
| **FR-STATE-002** | Cell 4 | `test_06_checkpoint_and_manifest_compliance` | `enkf_state_database.pt` (`state_variables`) |
| **FR-STATE-003** | Cell 6, 8 | `test_06_checkpoint_and_manifest_compliance` | `enkf_state_database.pt` (`prior_ensemble`) |
| **FR-STATE-004** | Cell 10 | `test_06_checkpoint_and_manifest_compliance` | `enkf_state_database.pt` (`kalman_gain_matrix`) |
| **FR-STATE-005** | Cell 12, 14 | `test_05_storage_artifacts_and_plots_persisted` | `plot_01_prior_vs_posterior_distributions.png`, `plot_02_kalman_gain_cross_covariance.png` |
| **FR-STATE-006** | Cell 16, 18 | `test_07_assimilation_validation_and_error_reduction` | `plot_03_dynamic_trajectory_convergence.png`, `enkf_state_estimation_metrics.json` |
| **FR-STATE-007** | Cell 20, 22 | `test_07_assimilation_validation_and_error_reduction` | `plot_05_spatial_grid_enkf_assimilation.png` |
| **FR-STATE-008** | Cell 24, 26 | `test_05_storage_artifacts_and_plots_persisted` | `plot_04_noise_sensitivity_sweep.png` |
| **FR-STATE-009** | Cell 28, 30 | `test_06_checkpoint_and_manifest_compliance` | `enkf_state_database.pt`, `ENKF_STATE_ESTIMATION_MANIFEST.md` |

---

## 7. Brutally Unfiltered Defect Log & Engineering Limitations

| Defect ID | Severity | Subsystem | Description & Root Cause | Impact & Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| `D-NB06-001` | **HIGH** | Observation Perturbation | **Gaussian Noise Assumption for SAR Backscatter**: Observation perturbations $\boldsymbol{\epsilon}_j \sim \mathcal{N}(0, R)$ assume symmetric Gaussian errors. Real Sentinel-1 SAR observations exhibit multiplicative Gamma speckle noise and skewed atmospheric moisture attenuation distributions. | Under extreme rainfall events, Gaussian perturbation underestimates positive tail outliers, slightly over-constraining the analysis spread. Mitigation: Ingest calibrated log-normal or Gamma noise distributions for SAR channels. |
| `D-NB06-002` | **HIGH** | Observation Operator | **Direct Identity Mapping ($H = [1, 0, 0, 0]$)**: The observation operator directly equates surface satellite moisture with volumetric root-zone moisture without solving vertical 1D Richards' equation infiltration within the observation step. | Assumes immediate equilibrium coupling between skin depth ($0-5\text{ cm}$) and root zone ($0-100\text{ cm}$), causing time-lag errors during early storm onset. Mitigation: Implement a non-linear observation operator $h(\mathbf{x})$ driven by the Notebook 05 PINN surrogate. |
| `D-NB06-003` | **MEDIUM** | Covariance Inflation | **Fixed Multiplicative Inflation Omission**: Classical EnKF systems apply covariance inflation ($P^f \leftarrow \rho P^f$, $\rho > 1$) or additive model noise to prevent ensemble filter collapse during long non-storm drydown periods. Notebook 06 omits dynamic inflation. | During multi-week drought drydown, ensemble variance contracts asymptotically, risking filter divergence if a sudden storm occurs. Mitigation: Implement adaptive relaxation-to-prior-spread (RTPS) inflation. |
| `D-NB06-004` | **LOW** | Spatial Localization | **Unlocalized Spatial Grid Covariance**: The 2D spatial assimilation step updates all grid cells without distance-based covariance localization (e.g. Gaspari-Cohn tapering function). | Spurious long-range correlations between distant catchment corners could theoretically introduce unphysical cross-cell updates in larger catchments ($>10\text{ km}$). Mitigation: Apply Schur-product Gaspari-Cohn distance tapering. |

---

## 8. Configuration Control & Environment Lineage

- **Parent Repository**: `THE_MRIDANSH`
- **Execution Python**: Python 3.12.10 (virtual environment `mridansh_env`, PyTorch 2.14.0+cpu, SciPy 1.15.2)
- **Primary Inputs**: `5_storage/notebook_results/notebook_02_preprocessing/preprocessed_telemetry.csv`, `5_storage/checkpoints/pinn_richards_model.pt`
- **Primary State DB**: `5_storage/state_database/enkf_state_database.pt`
- **Manifest Target**: `5_storage/state_database/ENKF_STATE_ESTIMATION_MANIFEST.md`
- **Verification Command**: `pytest tests/test_notebook_06_verification.py -v`
