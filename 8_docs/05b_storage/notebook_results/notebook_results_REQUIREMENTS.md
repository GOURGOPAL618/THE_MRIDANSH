# Subsystem 05: Scientific Research & Audit Evidence Repository (`notebook_results`)
## Central Engine: AETHER-MRID1607X
### Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
### Author & Lead Architect: Gourgopal Mohapatra
### Release Status: FROZEN_OPERATIONAL_RELEASE_v1.0

---

## 1. Executive Overview & Subsystem Mandate

The `5_storage/notebook_results/` repository represents the definitive empirical evidence vault and scientific audit trial of the **AETHER-MRID1607X** earth observation platform. Spanning the entire 12-stage research and operational certification campaign, this subsystem archives high-resolution diagnostic plots, intermediate model weights, quantitative evaluation metrics, and ablation matrices.

The primary architectural mandate of `notebook_results` is to establish an immutable, verifiable chain of custody from raw multi-sensor spaceborne ingestion to final grand scientific audit. Every empirical claim made in peer-reviewed dossiers and institutional certification sign-offs is anchored directly to reproducible artifacts stored within this 12-stage directory structure.

```
       +-------------------------------------------------------------+
       |           12-STAGE SCIENTIFIC RESEARCH & AUDIT TRAIL        |
       |               (5_storage/notebook_results/)                 |
       +------------------------------+------------------------------+
                                      |
         +----------------------------+----------------------------+
         |                            |                            |
         v                            v                            v
[STAGE 01-04: SENSING & GRAPHS] [STAGE 05-08: PHYSICS & ENKF] [STAGE 09-12: ABLATION & AUDIT]
• 01_ingestion (STAC / SAR)     • 05_physics_validation (PINN)• 09_hyperspectral (HSI)
• 02_preprocessing (Lee / Scale)• 06_state_estimation (EnKF)  • 10_ablation_study (Pareto)
• 03_spatial_modeling (GCN)     • 07_uncertainty (Conformal)   • 11_generalization (Stress)
• 04_temporal_modeling (LSTM)   • 08_robustness_failure (Heal) • 12_final_audit (Model Lock)
```

---

## 2. Master 12-Stage Repository Directory Catalog

The vault comprises 12 sequential stage directories containing 85+ primary scientific artifacts:

| Stage Directory | Artifact Count | Core Analytical Domain | Key Persisted Artifacts |
|:---|:---:|:---|:---|
| **`notebook_01_ingestion/`** | 8 | Multi-Modal Ingestion & STAC Telemetry | `stac_catalog_item.json`, `stac_telemetry_raw.csv`, 6 Diagnostic Plots |
| **`notebook_02_preprocessing/`** | 6 | Speckle Filtering & Feature Normalization | `scaler_manifest.json`, `preprocessed_telemetry.csv`, 4 Diagnostic Plots |
| **`notebook_03_spatial_modeling/`** | 10 | Spatial Topography & Graph Convolution | `spatial_gcn_embeddings.pt`, `spatial_graph_mesh.npz`, 6 Diagnostic Plots |
| **`notebook_04_temporal_modeling/`** | 8 | Spatio-Temporal ConvLSTM Dynamics | `convlstm_model_init.pt`, `temporal_latent_states.pt`, 5 Diagnostic Plots |
| **`notebook_05_physics_validation/`**| 7 | Continuous Richards PINN Verification | `pinn_richards_model.pt`, `pinn_physics_metrics.json`, 5 Diagnostic Plots |
| **`notebook_06_state_estimation/`** | 7 | Stochastic Ensemble Kalman Filter (EnKF) | `enkf_state_database.pt`, `enkf_state_estimation_metrics.json`, 5 Plots |
| **`notebook_07_uncertainty_analysis/`| 7 | Split-Conformal Uncertainty Calibration | `uncertainty_registry.pt`, `uncertainty_analysis_metrics.json`, 5 Plots |
| **`notebook_08_robustness_and_failure/`| 7 | Sensor Dropout & Self-Healing Stress | `robustness_stress_logs.pt`, `robustness_analysis_metrics.json`, 5 Plots |
| **`notebook_09_hyperspectral_experiment/`| 9 | 200-Band Hyperspectral PRISMA Module | `hsi_experiment_checkpoint.pt`, `hsi_experiment_metrics.json`, 7 Plots |
| **`notebook_10_ablation_study/`** | 5 | 8-Config Marginal Utility Decomposition | `plot_01`..`plot_05` (Pareto, Waterfall, Decision Matrix) |
| **`notebook_11_generalization/`** | 5 | 5-Regime Out-of-Distribution Stress | `plot_01`..`plot_05` (Radar, Holdout Residuals, Noise Response) |
| **`notebook_12_final_audit/`** | 5 | Grand Operational Certification | `audit_fig1`..`audit_fig5` (Master Octagon, Decision Space, Waterfall) |

---

## 3. Granular Stage-by-Stage Technical Analysis

### 3.1 Stage 01: Multi-Modal Ingestion (`notebook_01_ingestion/`)
* **Objective:** Autonomous ingestion of spatio-temporally collocated Sentinel-1 C-band SAR ($VV, VH$), Sentinel-2 MSI multispectral surface reflectance ($B_2, B_3, B_4, B_8$), Copernicus 30m DEM elevation, and ERA5-Land reanalysis weather forcing.
* **Spatial Extent:** Centered over Bhadrak/Kendrapara coastal agro-ecosystems (Bounding box: $86.6374^\circ	ext{E}$ to $86.7374^\circ	ext{E}$, $21.0878^\circ	ext{N}$ to $21.1878^\circ	ext{N}$).
* **Key Artifacts:**
  * `stac_catalog_item.json`: Spatio-Temporal Asset Catalog specification linking raw scene metadata.
  * `stac_telemetry_raw.csv`: Raw time-series records across 35 temporal acquisition timestamps.
  * `plot_01_s1_sar_dynamics.png`: Radar cross-section backscatter dynamics ($\sigma^0_{VV}, \sigma^0_{VH}$).
  * `plot_03_cloud_masking_sar_fallback.png`: Demonstrates optical cloud obscuration mitigation via all-weather radar fallback.

### 3.2 Stage 02: Preprocessing & Scaling (`notebook_02_preprocessing/`)
* **Objective:** Radiometric speckle suppression and deterministic train/test temporal feature scaling.
* **Algorithmic Core:**
  * Enhanced Lee Filter applied to SAR backscatter with a $7 	imes 7$ moving window, reducing speckle variance while preserving sharp field boundary edges.
  * Cloud QC masking via Scene Classification Layer (SCL) filtering.
  * Temporal split at sample index 28 (`2026-08-31 11:17:38 UTC`), yielding 28 training timesteps and 7 evaluation timesteps.
* **Key Artifacts:**
  * `scaler_manifest.json`: Exact MinMax scaling bounds: $	ext{SAR}_{VV} \in [-18.52, -6.14]\ 	ext{dB}$, $	ext{NDVI} \in [0.184, 0.792]$.
  * `plot_02_sar_speckle_lee_filter.png`: Pre/post filtering spatial contrast profiles.

### 3.3 Stage 03: Spatial Modeling & Graph Representation (`notebook_03_spatial_modeling/`)
* **Objective:** Capturing non-Euclidean topographic connectivity via 2-layer Graph Convolutional Networks (GCN).
* **Graph Topology:** $K$-Nearest Neighbor ($K=8$) spatial adjacency matrix parameterized by geodesic distance and elevation hydraulic gradient $
abla z$.
* **Key Metrics:**
  * Full GCN model spatial variance: $0.02364$.
  * Graph ablation (severing edges): Variance surges to $0.03530$ with Frobenius divergence $\Delta_F = 4.155$.
* **Key Artifacts:**
  * `spatial_gcn_embeddings.pt`: 670 KB serialized latent node feature vectors.
  * `spatial_graph_mesh.npz`: Sparse adjacency and node coordinate tensors.

### 3.4 Stage 04: Spatio-Temporal Dynamics (`notebook_04_temporal_modeling/`)
* **Objective:** Modeling soil moisture drying hysteresis and memory via recurrent ConvLSTM units.
* **Ablation Horizon Results (`temporal_sequence_ablation.json`):**
  * Horizon $L=3$: Validation $	ext{MSE} = 42.69$, SAR $	ext{MAE} = 8.96\ 	ext{dB}$.
  * Horizon $L=5$: Validation $	ext{MSE} = 37.74$, SAR $	ext{MAE} = 8.58\ 	ext{dB}$ (Optimal balance).
  * Horizon $L=7$: Validation $	ext{MSE} = 40.12$ (Overfitting on short monsoon intervals).
* **Key Artifacts:**
  * `convlstm_model_init.pt` (50.4 KB): Initialized ConvLSTM convolutional recurrent weights.
  * `temporal_latent_states.pt` (171.7 KB): Hidden state trajectories ($H_t, C_t$).

### 3.5 Stage 05: Physics Validation & PINN Richards (`notebook_05_physics_validation/`)
* **Objective:** Continuous 1D Richards PDE solution enforcing mass conservation and hydraulic consistency.
* **Key Metrics (`pinn_physics_metrics.json`):**
  * Final Total Composite Loss: $3.796 	imes 10^{-3}$.
  * Final PDE Residual Loss: $1.916 	imes 10^{-7}$.
  * Boundary Condition Loss: $2.838 	imes 10^{-3}$.
  * PDE residual error reduction: **72.30%** over unconstrained neural networks.
* **Key Artifacts:**
  * `pinn_richards_model.pt` (55.9 KB): Trained continuous neural network weights.
  * `plot_01_van_genuchten_swrc_conductivity.png`: Certified retention and conductivity curves.

### 3.6 Stage 06: EnKF State Estimation (`notebook_06_state_estimation/`)
* **Objective:** Stochastic 50-member Ensemble Kalman Filter assimilating sparse ground-truth observations.
* **Estimated State Vector:** $\mathbf{x} = [	heta_{	ext{root}}, ho_b, K_{	ext{sat}}, 	ext{SOC}]^T$.
* **Key Metrics (`enkf_state_estimation_metrics.json`):**
  * Prior Model Prediction RMSE: $0.06535\ 	ext{m}^3/	ext{m}^3$.
  * EnKF Posterior Assimilated RMSE: $0.01466\ 	ext{m}^3/	ext{m}^3$.
  * Error Reduction: **-77.57%**.
  * Root-Zone Uncertainty Contraction: **-69.47%**.
* **Key Artifacts:**
  * `enkf_state_database.pt` (16.2 KB): Persisted ensemble state trajectories.
  * `plot_02_kalman_gain_cross_covariance.png`: Cross-covariance coupling matrices.

### 3.7 Stage 07: Uncertainty Quantification (`notebook_07_uncertainty_analysis/`)
* **Objective:** Split-conformal prediction separating aleatoric (data noise) and epistemic (model ignorance) uncertainty.
* **Key Metrics (`uncertainty_analysis_metrics.json`):**
  * Mean Composite Uncertainty $\sigma$: $0.04301\ 	ext{m}^3/	ext{m}^3$ (Range: $[0.03017, 0.05591]$).
  * Decile Rank Correlation with True Residuals: $-0.9208$ (Strong monotonic calibration).
  * High-Confidence Patch MAE: $0.0028\ 	ext{m}^3/	ext{m}^3$ vs Low-Confidence: $0.0142\ 	ext{m}^3/	ext{m}^3$.
* **Key Artifacts:**
  * `uncertainty_registry.pt` (40.4 KB): Conformal quantile calibration lookup tables.

### 3.8 Stage 08: Robustness & Sensor Failure (`notebook_08_robustness_and_failure/`)
* **Objective:** Torture-testing multi-sensor dropout and evaluating self-healing dynamic fallback.
* **Stress Evaluation Matrix (`robustness_analysis_metrics.json`):**
  * Nominal All-Sensor RMSE: $0.04369\ 	ext{m}^3/	ext{m}^3$.
  * S2 Optical Dropout (Cloud Blindness): $	ext{RMSE} = 0.07046\ 	ext{m}^3/	ext{m}^3$ (+61.3% error).
  * S1 Radar Dropout: $	ext{RMSE} = 0.08060\ 	ext{m}^3/	ext{m}^3$ (+84.5% error).
  * Dual Dropout (S1 + S2 Blindness): $	ext{RMSE} = 0.10483\ 	ext{m}^3/	ext{m}^3$ (Fallback to ERA5+PINN).
  * Spatial Failure Classification: 12 Normal, 323 Degraded, 65 Critical recovery pixels.
* **Key Artifacts:**
  * `robustness_stress_logs.pt` (9.0 KB): Telemetry dropout response logs.

### 3.9 Stage 09: Hyperspectral Experimentation (`notebook_09_hyperspectral_experiment/`)
* **Objective:** Assessing 224-band HSI (PRISMA/EnMAP) augmentation against the lean multi-sensor baseline.
* **Key Metrics (`hsi_experiment_metrics.json`):**
  * Config A (Baseline) RMSE: $0.04462\ 	ext{m}^3/	ext{m}^3$ vs Config B (With HSI): $0.00461\ 	ext{m}^3/	ext{m}^3$ (**-89.67% error**).
  * Uncertainty $\sigma$: $0.00900 	o 0.00099$ (**-89.01%**).
  * Inference Latency Penalty: $2.71	imes$ slowdown ($0.0046	ext{ ms} 	o 0.0125	ext{ ms}$).
  * Storage Payload Penalty: $19.7	imes$ data expansion.
* **Architectural Verdict:** CASE 2: Targeted Optional Augmentation (Retain Config G as primary; deploy HSI on-demand).

### 3.10 Stage 10: Component Ablation Study (`notebook_10_ablation_study/`)
* **Objective:** Full 8-configuration Pareto optimization isolating the marginal contribution of every single component.
* **Essentiality Classification:**
  * **Tier 1 (Mission-Critical):** Sentinel-1 SAR (-44.86% $\Delta	ext{RMSE}$), Physics PINN (-23.53%), EnKF Filter (-28.57%), S2 Optical.
  * **Tier 2 (Contextual Enhancers):** DEM Topography (-23.73%), Meteorology (-28.23%), ConvLSTM (-17.35%).
  * **Tier 3 (On-Demand):** Hyperspectral HSI (-30.37% marginal gain, but 3.05x latency penalty).

### 3.11 Stage 11: Generalization & Stress Testing (`notebook_11_generalization/`)
* **Objective:** Validating operational robustness across 5 extreme out-of-distribution regimes.
* **Certified Operational Limits:**
  * Spatial Holdout RMSE: $0.00448\ 	ext{m}^3/	ext{m}^3$ ($R^2 = +0.9534$).
  * Spatial Generalization Gap: $\Delta = +0.00129\ 	ext{m}^3/	ext{m}^3$ (Well below $0.0030$ threshold).
  * Severe Radiometric Noise Immunity: $+90.3\%$ error reduction over unconstrained models under $+2.0	ext{ dB}$ radar speckle.

### 3.12 Stage 12: Grand Scientific Audit (`notebook_12_final_audit/`)
* **Objective:** Master system closure, multi-attribute performance radar, and cryptographic model lock.
* **Key Verifications:**
  * 12/12 Research Milestones Certified.
  * 7/7 Persistent Storage Checkpoints SHA-256 Validated.
  * Sub-millisecond compute throughput: $0.0116	ext{ ms/pixel}$.
  * Operational Status: `LOCKED_OPERATIONAL_RELEASE_v1.0`.

---

## 4. Brutal Engineering Disclosures ("Ek Ek Dhappa")

In accordance with institutional integrity standards, the following historical research compromises, approximations, and technical limitations are formally cataloged:

1. **Temporal Split Leakage in Early Prototyping:**
   * *Disclosure:* In Stages 01 and 02, temporal splitting was executed sequentially on continuous time-series. In presence of long-term soil moisture auto-correlation, adjacent timesteps induce subtle information leakage across train and validation folds.
   * *Resolution:* Fully mitigated in Stage 11 via true Leave-One-Cluster-Out (LOCO) spatial block holdout and climate shift evaluations.
2. **1D Vertical Column Simplification in PINN:**
   * *Disclosure:* Stage 05 implements a 1D vertical Richards equation column $	heta(z, t)$ rather than full 3D subsurface flow. Lateral hydrodynamic fluxes driven by micro-topography are not solved in the neural PDE head, relying instead on 2D ConvLSTM and GCN inductive biases.
3. **Ensemble Size vs. Computational Budget Tradeoff:**
   * *Disclosure:* Stage 06 utilizes $N=50$ ensemble members. While sufficient for 4 state variables, covariance inflation ($\lambda = 1.05$) is required to prevent filter divergence and ensemble collapse in long-duration rollouts.
4. **Synthetic Cloud Dropout Masking:**
   * *Disclosure:* Stage 08 evaluated sensor failure using Bernoulli synthetic masking. Real-world monsoon overcast exhibits spatial-temporal clustering where cloud obscuration persists continuously for 10–14 days, straining optical interpolation bounds.

---

## 5. Traceable Subsystem Requirements

| Requirement ID | Verification Stage | Target Specification / Bound | Status |
|:---|:---:|:---|:---:|
| **REQ-STOR-NBR-01** | Stage 01 | Multi-modal STAC catalog must span Sentinel-1, Sentinel-2, DEM, and ERA5. | **VERIFIED** |
| **REQ-STOR-NBR-02** | Stage 02 | Lee filter must suppress speckle variance while maintaining edge gradients. | **VERIFIED** |
| **REQ-STOR-NBR-03** | Stage 03 | GCN graph representation must demonstrate lower variance than disconnected nodes. | **VERIFIED** (0.0236 vs 0.0353) |
| **REQ-STOR-NBR-04** | Stage 04 | ConvLSTM temporal memory must achieve validation $	ext{MSE} \le 40.0$ on optimal lookback. | **VERIFIED** (37.74) |
| **REQ-STOR-NBR-05** | Stage 05 | PINN Richards PDE residual error must be reduced by $> 70\%$ over baseline. | **VERIFIED** (72.30%) |
| **REQ-STOR-NBR-06** | Stage 06 | EnKF state assimilation must reduce root moisture error by $> 70\%$. | **VERIFIED** (77.57%) |
| **REQ-STOR-NBR-07** | Stage 07 | Conformal uncertainty calibration must achieve monotonic decile correlation $\le -0.85$. | **VERIFIED** (-0.9208) |
| **REQ-STOR-NBR-08** | Stage 08 | System must dynamically recover from dual sensor blackout via fallback physics. | **VERIFIED** |
| **REQ-STOR-NBR-09** | Stage 09 | HSI augmentation must improve accuracy without corrupting fallback pipelines. | **VERIFIED** (-89.67%) |
| **REQ-STOR-NBR-10** | Stage 10 | Config G must be validated as optimal Pareto backbone ($0.80	ext{ ms}, R^2=0.9199$). | **VERIFIED** |
| **REQ-STOR-NBR-11** | Stage 11 | Spatial holdout generalization gap must remain bounded $\Delta \le 0.0030\ 	ext{m}^3/	ext{m}^3$. | **VERIFIED** (0.00129) |
| **REQ-STOR-NBR-12** | Stage 12 | Final scientific audit must certify 100% zero-defect release under model lock. | **VERIFIED** |
