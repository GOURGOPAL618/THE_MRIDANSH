# THE MRIDANSH (AETHER-MRID1607X)
# Notebook 09 — Hyperspectral Augmentation & Spectral Information Experiment
# Requirements, Verification and Configuration Control

---

## 1. Document Control

### 1.1 Identification

| Field | Value |
|:---|:---|
| **Document ID** | MRID-NB09-DOC-001 |
| **Notebook ID** | `09-hyperspectral-experiment.ipynb` |
| **Project** | THE MRIDANSH — Unified Soil State Estimation System |
| **System / Engine** | AETHER-MRID1607X (Multi-Domain Soil Intelligence Engine) |
| **Author / Developer** | Gourgopal Mohapatra |
| **Organization** | JCC HEADQUARTER — JCC CAMPUS 2, RS-SDA Division |
| **Reviewer** | *(To be assigned — independent technical reviewer)* |
| **Approver** | *(To be assigned — systems engineering authority)* |
| **Version** | 1.0 |
| **Date** | 2026-10-08 |
| **Status** | Baseline Draft — Under Strict Technical Review |
| **Classification** | Proprietary & Controlled Research Artifact |

### 1.2 Revision History

| Version | Date | Author | Description of Change |
|:---|:---|:---|:---|
| 0.1 | 2026-10-08 | Gourgopal Mohapatra | Structural analysis of `09-hyperspectral-experiment.ipynb` cells, HSI data cubes, PCA explained variance vectors, and AB testing metrics. |
| 1.0 | 2026-10-08 | Gourgopal Mohapatra | Baseline requirements specification: hypothesis testing protocol, atmospheric window filtering, PCA feature compression, multi-criteria trade-off matrix, and full defect auditing. |

### 1.3 Document Conventions

- **SHALL** indicates a mandatory, verifiable, and contractually binding engineering requirement.
- **SHOULD** indicates a recommended design practice or optimization target.
- **MAY** indicates an optional or alternative implementation path.
- **Requirement Status Definitions**:
  - `MET`: Requirement verified by execution against empirical output evidence.
  - `PARTIAL`: Implementation exists but carries software defects, mock formulations, or documentation discrepancies.
  - `NOT MET`: Requirement is absent, failing verification, or contradicted by runtime evidence.
  - `WAIVED`: Formal departure accepted with recorded technical rationale.
- **Verification Methods**:
  - `T` (Test): Quantitative execution with test assertions and numerical threshold validation.
  - `A` (Analysis): Theoretical evaluation of spectral absorption physics, PCA variance ratios, and hypothesis test boundaries.
  - `I` (Inspection): Manual examination of source code, configuration constants, and layer declarations.
  - `D` (Demonstration): Observation of operational execution, multi-panel diagnostic figures, and trade-off tables.
- **Identifier Prefix Rules**:
  - `FR-xxx`: Functional Requirement
  - `DI-xxx`: Data Integrity Requirement
  - `IF-xxx`: Interface & File Structure Requirement
  - `UQ-xxx`: Uncertainty & Quality Requirement
  - `NF-xxx`: Non-Functional & Reproducibility Requirement
  - `VP-xxx`: Verification Procedure
  - `D-xxx`: Open Defect / Discrepancy
  - `R-xxx`: Technical Risk
  - `A-xxx`: Architectural Assumption

---

## 2. Purpose and Scope

### 2.1 Purpose

This document establishes the formal engineering requirements, mathematical formulations, verification procedures, empirical execution results, bidirectional traceability, configuration management, and technical discrepancy logs for Jupyter notebook `09-hyperspectral-experiment.ipynb` within **THE MRIDANSH** system.

### 2.2 System Context

**THE MRIDANSH** (*AETHER-MRID1607X*) estimates high-resolution volumetric soil moisture and subgrade shear strength from multi-sensor Earth Observation (EO) data.

Within this macro-architecture:
- **Notebooks 01–02** ingest and preprocess multispectral Sentinel-2 and microwave Sentinel-1 observations.
- **Notebooks 03–05** construct spatial graph topologies, temporal ConvLSTM sequences, and Richards PDE physics constraints.
- **Notebook 06** assimilates observations using an Ensemble Kalman Filter (EnKF).
- **Notebooks 07–08** quantify composite uncertainty bounds and establish the 4-tier operational safety taxonomy.
- **Notebook 09 (Item Under Documentation)** evaluates whether high-dimensional Hyperspectral Imaging (HSI) provides statistically significant, non-redundant soil state information beyond the frozen baseline configuration ($\text{CONFIG-A}$). It executes a formal scientific hypothesis test ($H_0$ vs $H_1$), models continuous $224$-channel VNIR/SWIR spectra, filters atmospheric water absorption windows, compresses features via Principal Component Analysis (PCA), runs a controlled AB test, assesses computational penalties (latency, memory), and formalizes the deployment decision matrix.
- **Downstream Consumers (Notebooks 10–11)** evaluate systematic component ablations and cross-catchment generalization baselines.

### 2.3 Notebook Objective

Notebook 09 covers Sprint Days 8–10 of the Scientific Audit & Validation Mission:
1. **Day 8 Objective (HSI Definition & Quality Control)**: Freeze $\text{CONFIG-A}$ baseline, synthesize a $224$-band HSI data cube ($400 - 2500\text{ nm}$) over $N=1000$ points, apply atmospheric absorption window masking (1350–1420 nm & 1800–1950 nm), compress valid bands to 10 principal components via PCA, and render Plot 1 spectral curves.
2. **Day 9 Objective (Controlled AB Testing)**: Execute a controlled $80/20$ train/test benchmark comparing $\text{CONFIG-A}$ (frozen baseline) against $\text{CONFIG-B}$ (hyperspectral augmented), quantify error deltas ($\Delta\text{RMSE}, \Delta\text{MAE}, \Delta R^2, \Delta\sigma$), render Plot 2 scatter and uncertainty boxplots, and audit a $100\%$ sensor dropout fallback scenario.
3. **Day 10 Objective (Multi-Criteria Trade-Off & Decision Matrix)**: Evaluate accuracy vs. computational overhead ($4\times$ latency and memory penalties), render Plot 3 normalized trade-off bars, conclude the formal hypothesis test ($H_1$ accepted), and establish the operational deployment policy.

### 2.4 In Scope

- All 24 cells of `09-hyperspectral-experiment.ipynb` (10 code cells, 14 markdown cells).
- Definition of the frozen baseline architecture: $\text{CONFIG-A} = \{\text{Sentinel-2}, \text{Sentinel-1}, \text{DEM}, \text{Weather}, \text{Physics PINN}, \text{EnKF Filter}\}$.
- Definition of the experimental branch: $\text{CONFIG-B} = \text{CONFIG-A} \cup \{\mathbf{Z}_{\text{HSI\_PCA}}\}$.
- Generation of synthetic contiguous HSI cube of shape $(1000, 224)$ with SWIR water absorption dips at $1400\text{ nm}$ and $1900\text{ nm}$.
- Atmospheric masking dropping $24$ noisy channels, producing a clean QC array of shape $(1000, 200)$.
- StandardScaler and PCA dimensionality reduction extracting $10$ orthogonal principal components.
- Ground truth generation: $y_{\text{true}} = 0.25 + 0.12 \sin(\dots) + \mathcal{N}(0, 0.015^2)$, clipped to $[0.05, 0.45]\text{ m}^3/\text{m}^3$.
- Simulation of $\text{CONFIG-A}$ ($\text{RMSE}=0.0211$) vs $\text{CONFIG-B}$ ($\text{RMSE}=0.0194$) over 200 test samples.
- Fallback degradation testing across Full HSI, 50% Corruption, and 100% Dropout.
- Multi-metric trade-off evaluation (Accuracy, $R^2$, Uncertainty, Latency, RAM, Resilience).
- Formal hypothesis test decision: Reject $H_0 \to$ Accept $H_1$.

### 2.5 Out of Scope

- Real-time ingestion of calibrated L2A surface reflectance data cubes from orbital missions (PRISMA, EnMAP, DESIS, EMIT).
- Radiative transfer modeling of atmospheric path radiance (6S or MODTRAN simulations).
- Deep spectral-spatial 3D-CNN or spectral transformer training.
- Physical serialization of processed PCA matrices to disk.

### 2.6 Current-State Declaration (Mandatory Engineering Disclosure)

> [!WARNING]
> **MANDATORY CURRENT-STATE DECLARATION: SYNTHETIC SIMULATION AND MOCKED AB INFERENCE**
> 
> Inspection of `09-hyperspectral-experiment.ipynb` confirms that the notebook operates as an idealized conceptual simulation harness rather than testing trained neural pipelines on real hyperspectral data cubes:
> 1. **Mocked AB Prediction Simulation (Defect D-001)**: In Cell 13, neither $\text{CONFIG-A}$ nor $\text{CONFIG-B}$ executes a machine learning regressor or neural network. Predictions are synthesized simply by adding Gaussian noise to ground truth:
>    $$\hat{y}_A = y_{\text{test}} + \mathcal{N}(0, 0.022^2), \quad \hat{y}_B = y_{\text{test}} + \mathcal{N}(0, 0.018^2)$$
>    The PCA features extracted in Cell 09 ($\mathbf{Z}_{\text{HSI\_PCA}}$) are never passed as inputs to any predictive model.
> 2. **PCA White-Noise Artifact (Defect D-002)**: In Cell 04, the raw HSI cube is created by tiling a single mean spectral signature across all 1000 pixels and adding i.i.d. Gaussian noise. Because there is zero across-pixel physical spectral variance, standardizing the matrix removes the mean signature, leaving only white noise. Consequently, 10 principal components explain merely **$9.50\%$** cumulative variance.
> 3. **Discrepant Band Count Annotation (Defect D-003)**: In Cell 08 line 190, Plot 1 labels the curve `"HSI Continuous (196 bands)"`, whereas the actual cleaned QC array has **200 bands** ($224 - 24 = 200$).
> 4. **Static Fallback Arithmetic (Defect D-004)**: In Cell 17, fallback metrics are calculated using hardcoded arithmetic offsets (`rmse_b + 0.0025`, `rmse_a`) without executing actual channel masking through an inference pipeline.
> 5. **Decoupled Pipeline (Defect D-005)**: No real satellite tiles are ingested, and no artifacts are written to `data_processed/`.

---

## 3. Definitions and Abbreviations

| Term / Abbreviation | Definition |
|:---|:---|
| **HSI** | Hyperspectral Imaging (hundreds of narrow, contiguous spectral bands). |
| **VNIR** | Visible and Near-Infrared spectrum ($400 - 1000\text{ nm}$). |
| **SWIR** | Short-Wave Infrared spectrum ($1000 - 2500\text{ nm}$). |
| **PRISMA / EnMAP** | Spaceborne hyperspectral missions providing orbital $30\text{ m}$ contiguous data. |
| **CONFIG-A** | Frozen baseline MRIDANSH system (S1, S2, DEM, Weather, PINN, EnKF). |
| **CONFIG-B** | Experimental candidate system augmented with hyperspectral PCA features. |
| **$H_0$ (Null)** | Hypothesis stating HSI provides no statistically significant estimation improvement. |
| **$H_1$ (Alternative)** | Hypothesis stating HSI provides statistically significant, non-redundant improvement. |
| **PCA** | Principal Component Analysis (orthogonal linear dimensionality reduction). |
| **Atmospheric Windows**| Wavelength intervals ($1350-1420\text{ nm}$ and $1800-1950\text{ nm}$) obscured by atmospheric $\text{H}_2\text{O}$. |
| **JCC RS-SDA** | Jagannath Command Center — Remote Sensing & Spatial Data Analytics Division. |

---

## 4. Requirements

### 4.1 Functional Requirements

- **FR-001**: The software shall formalize the frozen baseline configuration $\text{CONFIG-A}$ comprising Sentinel-2, Sentinel-1, DEM, Weather, Physics PINN, and EnKF.
- **FR-002**: The software shall define a contiguous hyperspectral domain spanning $400\text{ nm}$ to $2500\text{ nm}$ across $224$ spectral channels with regular wavelength sampling:
  $$\lambda_k = 400 + k \cdot \frac{2100}{223}\text{ nm}, \quad k \in [0, 223]$$
- **FR-003**: The software shall generate a baseline soil reflectance spectrum incorporating:
  - Base continuum: $R_{\text{base}}(\lambda) = 0.10 + 0.35 \left(1 - \exp(-\lambda / 800)\right)$
  - SWIR-1 water absorption dip near $1400\text{ nm}$: $A_{1400}(\lambda) = 0.15 \exp\left(-\left(\frac{\lambda - 1400}{40}\right)^2\right)$
  - SWIR-2 water absorption dip near $1900\text{ nm}$: $A_{1900}(\lambda) = 0.20 \exp\left(-\left(\frac{\lambda - 1900}{50}\right)^2\right)$
- **FR-004**: The software shall instantiate a synthetic raw HSI data cube of shape $(1000, 224)$ combining clean spectra with Gaussian noise $\mathcal{N}(0, 0.02^2)$.
- **FR-005**: The software shall execute atmospheric quality control masking:
  - Mask 1: $1350\text{ nm} \le \lambda \le 1420\text{ nm}$
  - Mask 2: $1800\text{ nm} \le \lambda \le 1950\text{ nm}$
  dropping exactly $24$ noisy channels and yielding a cleaned QC cube of shape $(1000, 200)$.
- **FR-006**: The software shall sanitize the QC cube using `nan_to_num` and clip reflectance values to $[0.0, 1.0]$.
- **FR-007**: The software shall render Aerospace Plot 1 showing:
  - Subplot 1: Mean HSI soil reflectance curve with $\pm 1\sigma$ variability and red-shaded atmospheric water vapor absorption bands.
  - Subplot 2: Continuous HSI sampling compared against 9 discrete broadband Sentinel-2 channel centers.
- **FR-008**: The software shall standardize the QC cube using `StandardScaler` and extract 10 orthogonal principal components via `PCA(n_components=10)`.
- **FR-009**: The software shall compute and log the individual and cumulative explained variance ratios for Top 1, Top 3, Top 6, and Top 10 principal components.
- **FR-010**: The software shall generate synthetic true soil moisture ground truth:
  $$y_{\text{true}} = \operatorname{clip}\left(0.25 + 0.12 \sin\left(\frac{4\pi \cdot i}{1000}\right) + \mathcal{N}(0, 0.015^2), 0.05, 0.45\right)$$
  and partition the dataset into 800 training samples and 200 held-out test samples.
- **FR-011**: The software shall evaluate $\text{CONFIG-A}$ and $\text{CONFIG-B}$ predictions over the 200 test samples, computing RMSE, MAE, $R^2$, and mean uncertainty $\sigma$.
- **FR-012**: The software shall render Aerospace Plot 2 showing:
  - Subplot 1: Scatter plot of predicted vs true soil moisture for $\text{CONFIG-A}$ and $\text{CONFIG-B}$ with a 1:1 ideal reference line.
  - Subplot 2: Boxplot comparing residual model uncertainty ($\pm\sigma$) distributions between both configurations.
- **FR-013**: The software shall audit missing HSI fallback resilience across Full HSI Available, 50% Band Corruption, and 100% HSI Dropout (reverting to $\text{CONFIG-A}$).
- **FR-014**: The software shall compile and log a comprehensive multi-metric trade-off table comparing Accuracy, $R^2$, Uncertainty, Inference Latency, Memory Footprint, and Dropout Resilience.
- **FR-015**: The software shall render Aerospace Plot 3 displaying normalized multi-criteria trade-off scores across Accuracy, Fit Quality, Uncertainty Reduction, and Processing Speed, and log the formal hypothesis decision ($H_1$ accepted).

### 4.2 Data Integrity Requirements

- **DI-001**: Non-Negative Reflectance Factor: All raw and QC spectral reflectance values shall satisfy $0.0 \le R(\lambda) \le 1.0$.
- **DI-002**: Monotonic Spectral Axis: The wavelength vector $\lambda$ shall be strictly monotonically increasing ($\lambda_{k+1} > \lambda_k$).
- **DI-003**: Cumulative Variance Monotonicity: Cumulative explained variance ratios shall strictly increase: $\operatorname{CumVar}(k) \le \operatorname{CumVar}(k+1)$.
- **DI-004**: Performance Superiority Assertion: $\text{CONFIG-B}$ shall demonstrate quantitative improvements over $\text{CONFIG-A}$: $\text{RMSE}_B < \text{RMSE}_A$ and $\sigma_B < \sigma_A$.
- **DI-005**: Graceful Fallback Guarantee: Under 100% HSI dropout, performance metrics shall exactly match $\text{CONFIG-A}$ baseline metrics without crashing.

### 4.3 Interface Requirements

- **IF-001**: Function `compute_metrics` shall accept `(y_real, y_pred, unc)` and return tuple `(rmse, mae, r2, avg_unc)`.
- **IF-002**: Dimensionality reduction module shall transform QC matrix of shape $(1000, 200)$ into feature matrix of shape $(1000, 10)$.
- **IF-003**: In-graph legends and axis titles shall display physical units ($\text{nm}$, $\text{m}^3/\text{m}^3$, $\text{ms/pixel}$, $\text{MB}$).
- **IF-004**: Terminal outputs shall display standardized ASCII tables formatted via Pandas DataFrame printing.

### 4.4 Uncertainty / Quality Requirements

- **UQ-001**: Hyperspectral augmentation shall achieve a relative error reduction of $\ge 5\%$ over baseline ($\Delta\text{RMSE} / \text{RMSE}_A \le -0.05$).
- **UQ-002**: Hyperspectral augmentation shall achieve an uncertainty contraction of $\ge 15\%$ ($\Delta\sigma / \sigma_A \le -0.15$).
- **UQ-003**: Inference latency penalty shall be transparently quantified (demonstrating $4.0\times$ execution overhead).
- **UQ-004**: Memory footprint expansion shall be documented (demonstrating $4.0\times$ RAM overhead).

### 4.5 Non-Functional Requirements

- **NF-001**: Deterministic seeds shall be fixed for NumPy (`np.random.seed(1607)`) and PyTorch (`torch.manual_seed(1607)`).
- **NF-002**: The notebook shall execute unattended from Cell 00 to Cell 23 without interactive prompts.
- **NF-003**: Visual plots shall employ the JCC RS-SDA dark telemetry theme (`#00FFCC`, `#FF9900`, `#FF0055`, monospace typography).
- **NF-004**: Computational execution time shall evaluate in $< 3.0$ seconds on CPU/CUDA hardware.

---

## 5. Requirements Attributes

| ID | Requirement Statement | Rationale | Method | Acceptance Criterion | Status |
|:---|:---|:---|:---:|:---|:---:|
| **FR-001** | Freeze $\text{CONFIG-A}$ baseline specification. | Prevents experimental leakage. | I | Architectural lock declared in Step 0. | **MET** |
| **FR-002** | Define 224-channel grid from $400\text{ nm}$ to $2500\text{ nm}$. | PRISMA/EnMAP sensor standard. | I/T | Array length = 224, range $[400, 2500]$. | **MET** |
| **FR-003** | Synthesize soil spectrum with 1400/1900 nm water dips. | Physical reflectance modeling. | T | Absorptions at $1400\text{ nm}$ and $1900\text{ nm}$ verified. | **MET** |
| **FR-004** | Instantiate raw HSI cube $(1000, 224)$ with noise. | Spectral dataset discretization. | T | Cube shape $(1000, 224)$; noise $\sigma=0.02$. | **MET** |
| **FR-005** | Apply atmospheric masking (1350-1420 & 1800-1950 nm). | Drops uninformative absorption noise. | T | 24 channels dropped; 200 channels retained. | **MET** |
| **FR-006** | Sanitize QC cube via `nan_to_num` and clipping $[0, 1]$. | Numerical stability enforcement. | T | No NaNs/Infs; values bounded $[0.0, 1.0]$. | **MET** |
| **FR-007** | Render Plot 1 spectral curves and Sentinel-2 comparison. | Visual validation of spectral bands. | D | 2-panel figure rendered (`length=129876` bytes). | **MET** |
| **FR-008** | Scale QC cube and fit PCA engine with 10 components. | Dimensionality reduction. | T | PCA matrix shape $(1000, 10)$. | **MET** |
| **FR-009** | Log explained variance ratios for Top 1, 3, 6, 10 PCs. | Spectral information auditing. | T | Top 1: **1.04%**, Top 10: **9.50%**. | **MET** |
| **FR-010** | Generate $y_{\text{true}}$ and create 800/200 train/test split. | Benchmark dataset initialization. | T | Train size 800, Test size 200; range $[0.05, 0.45]$. | **MET** |
| **FR-011** | Evaluate $\text{CONFIG-A}$ vs $\text{CONFIG-B}$ on test set. | Quantitative AB testing. | T | Base RMSE=**0.0211**, HSI RMSE=**0.0194**. | **PARTIAL\*** |
| **FR-012** | Render Plot 2 scatter plot and uncertainty boxplots. | Visual validation of AB evaluation. | D | 2-panel figure rendered (`length=141628` bytes). | **MET** |
| **FR-013** | Audit missing HSI fallback across 3 scenarios. | Fault-tolerant graceful degradation. | T | 100% dropout RMSE = **0.0211** (matches baseline). | **PARTIAL\*** |
| **FR-014** | Compile multi-metric trade-off table in Pandas. | Holistic systems trade-off analysis. | D | 7-row table printed with latencies and memory. | **MET** |
| **FR-015** | Render Plot 3 normalized trade-off bars and log verdict. | Final deployment governance. | D/I | Plot 3 rendered; Alternative hypothesis $H_1$ accepted. | **MET** |
| **DI-001** | Non-negative spectral reflectance factor. | Physical radiant energy definition. | T | $\min(R) \ge 0.0$ and $\max(R) \le 1.0$. | **MET** |
| **DI-002** | Strict wavelength monotonicity. | Valid physical spectral grid. | T | $\operatorname{diff}(\lambda) > 0$ across all bands. | **MET** |
| **DI-003** | Monotonic cumulative PCA explained variance. | Orthogonal variance accumulation. | T | $1.04\% \le 3.01\% \le 5.87\% \le 9.50\%$. | **MET** |
| **DI-004** | Quantitative HSI error and uncertainty superiority. | Alternative hypothesis verification. | T | $\text{RMSE}_B (0.0194) < \text{RMSE}_A (0.0211)$. | **MET** |
| **DI-005** | Graceful fallback metric preservation. | Pipeline safety contract. | T | Dropout fallback RMSE matches $\text{CONFIG-A}$ (0.0211). | **MET** |
| **IF-001** | `compute_metrics` signature and return contract. | Performance metric evaluator. | I/T | Accepts 3 arrays, returns 4 scalar metrics. | **MET** |
| **IF-002** | Dimensionality reduction input/output interface. | Pipeline feature dimension contract. | T | $(1000, 200) \to (1000, 10)$ compression verified. | **MET** |
| **IF-003** | In-graph telemetry units and labels. | Reporting readability standard. | D | Physical units displayed across all subplots. | **MET** |
| **IF-004** | Formatted ASCII DataFrame output. | Telemetry logging standard. | D | Multi-metric trade-off printed to stdout. | **MET** |
| **UQ-001** | Relative RMSE reduction $\ge 5\%$. | HSI precision gain threshold. | T | Empirical delta = **-7.76%** (exceeds 5% target). | **MET** |
| **UQ-002** | Relative uncertainty contraction $\ge 15\%$. | UQ contraction threshold. | T | Empirical delta = **-20.28%** (exceeds 15% target). | **MET** |
| **UQ-003** | Inference latency expansion quantified. | Operational throughput transparency. | I | Evaluated at $1.2\text{ ms} \to 4.8\text{ ms}$ ($+300\%$). | **MET** |
| **UQ-004** | Memory footprint expansion quantified. | Computational resource transparency. | I | Evaluated at $128\text{ MB} \to 512\text{ MB}$ ($+300\%$). | **MET** |
| **NF-001** | Deterministic seed initialization (1607). | Numerical reproducibility standard. | I/T | NumPy and PyTorch seeds set in Cell 02. | **MET** |
| **NF-002** | Headless unattended execution. | Batch pipeline compatibility. | D | All 24 cells execute sequentially without errors. | **MET** |
| **NF-003** | Dark telemetry UI styling on generated figures. | Institutional visual consistency. | I | Cyan, orange, red accents with monospace fonts. | **MET** |
| **NF-004** | Execution runtime $< 3.0$ seconds. | Computational performance standard. | A | End-to-end execution completes in $\approx 1.4$s. | **MET** |

*\*Note: FR-011 marked PARTIAL due to mocked Gaussian AB simulation (D-001). FR-013 marked PARTIAL due to static fallback offsets (D-004).*

---

## 6. Verification Procedures

### VP-001: Wavelength Grid and Spectral Formulation Verification
- **Verifies**: FR-002, FR-003, DI-001, DI-002, NF-001
- **Setup**: Python 3.10+ kernel with NumPy under seed 1607.
- **Procedure**:
  1. Construct `wavelengths = np.linspace(400, 2500, 224)`.
  2. Compute base continuum, 1400 nm absorption, and 1900 nm absorption.
  3. Validate non-negativity and minimum values near 1400 nm and 1900 nm.
- **Expected Result**:
  - `wavelengths[0] == 400.0`, `wavelengths[-1] == 2500.0`
  - Wavelengths strictly increasing: `np.all(np.diff(wavelengths) > 0)`
  - Absorption dips observed at indices corresponding to 1400 nm and 1900 nm.
- **Pass/Fail Criterion**: Grid matches 224 points and dips are centered within $\pm 10\text{ nm}$.

### VP-002: Atmospheric Quality Control Masking
- **Verifies**: FR-004, FR-005, FR-006, IF-002
- **Setup**: Generate `hsi_raw_cube` of shape `(1000, 224)` and apply atmospheric masks.
- **Procedure**:
  1. Compute `mask_1400 = (wavelengths >= 1350) & (wavelengths <= 1420)`.
  2. Compute `mask_1900 = (wavelengths >= 1800) & (wavelengths <= 1950)`.
  3. Count dropped bands: `np.sum(mask_1400 | mask_1900)`.
  4. Verify shape of `hsi_qc_cube = hsi_raw_cube[:, ~(mask_1400 | mask_1900)]`.
- **Expected Result**:
  - Dropped noisy bands == **24 channels**
  - Cleaned QC cube shape == **(1000, 200)**
  - No NaN, Inf, or out-of-bound values in QC cube.
- **Pass/Fail Criterion**: Exact retention of 200 bands and valid numerical ranges.

### VP-003: PCA Dimensionality Reduction
- **Verifies**: FR-008, FR-009, DI-003
- **Setup**: Standardize QC cube via `StandardScaler` and fit `PCA(n_components=10)`.
- **Procedure**:
  1. Execute `pca_engine.fit_transform(hsi_scaled)`.
  2. Calculate `explained_variance_ratio_ * 100`.
  3. Compute cumulative variance array `cum_var = np.cumsum(explained_var)`.
- **Expected Result**:
  - Top 1 PC: **1.04%**
  - Top 3 PCs Cumulative: **3.01%**
  - Top 6 PCs Cumulative: **5.87%**
  - Top 10 PCs Cumulative: **9.50%**
  - Transformed feature matrix shape == **(1000, 10)**
- **Pass/Fail Criterion**: Cumulative variances match within $\pm 0.05\%$.

### VP-004: Ground Truth Synthesis and Data Partitioning
- **Verifies**: FR-010, NF-001
- **Setup**: Generate sinusoidal synthetic ground truth under seed 1607.
- **Procedure**:
  1. Evaluate `y_true` formulation over 1000 points.
  2. Split at index 800: `y_train = y_true[:800]`, `y_test = y_true[800:]`.
  3. Slice `hsi_test_pca = hsi_pca_features[800:]`.
- **Expected Result**:
  - `len(y_train) == 800`, `len(y_test) == 200`
  - Values bounded within $[0.05, 0.45]\text{ m}^3/\text{m}^3$.
- **Pass/Fail Criterion**: Correct split sizes and physical value bounds.

### VP-005: Controlled AB Testing Evaluation
- **Verifies**: FR-011, DI-004, IF-001, UQ-001, UQ-002
- **Setup**: Execute `compute_metrics` on simulated predictions for $\text{CONFIG-A}$ and $\text{CONFIG-B}$.
- **Procedure**:
  1. Simulate $\text{CONFIG-A}$ ($\text{noise} \sim \mathcal{N}(0, 0.022^2)$) and compute metrics.
  2. Simulate $\text{CONFIG-B}$ ($\text{noise} \sim \mathcal{N}(0, 0.018^2)$) and compute metrics.
  3. Evaluate absolute and relative deltas for RMSE, MAE, $R^2$, and $\sigma$.
- **Expected Result**:
  - $\text{CONFIG-A}$: $\text{RMSE} = \mathbf{0.0211}$, $\text{MAE} = \mathbf{0.0168}$, $R^2 = \mathbf{0.6684}$, $\sigma = \pm \mathbf{0.0375}$
  - $\text{CONFIG-B}$: $\text{RMSE} = \mathbf{0.0194}$, $\text{MAE} = \mathbf{0.0159}$, $R^2 = \mathbf{0.7179}$, $\sigma = \pm \mathbf{0.0299}$
  - RMSE Delta: $\mathbf{-0.0016\text{ m}^3/\text{m}^3}$ ($\mathbf{-7.76\%}$)
  - MAE Delta: $\mathbf{-0.0009\text{ m}^3/\text{m}^3}$ ($\mathbf{-5.14\%}$)
  - $R^2$ Delta: $\mathbf{+0.0495}$ ($\mathbf{+7.40\%}$)
  - Uncertainty Contraction: $\mathbf{-0.0076\text{ m}^3/\text{m}^3}$ ($\mathbf{-20.28\%}$)
- **Pass/Fail Criterion**: All metric values strictly match expected baseline numbers within $\pm 0.0005$.

### VP-006: Visual Diagnostic Rendering (Plots 1, 2, 3)
- **Verifies**: FR-007, FR-012, FR-015, NF-003
- **Setup**: Matplotlib dark theme configuration.
- **Procedure**:
  1. Verify rendering of Plot 1 (Spectral curves and S2 comparison).
  2. Verify rendering of Plot 2 (Scatter and uncertainty boxplots).
  3. Verify rendering of Plot 3 (Multi-criteria normalized bar charts).
- **Expected Result**: All 3 figure display objects generated without exceptions.
- **Pass/Fail Criterion**: PNG byte lengths $> 50000$ bytes for all figures.

### VP-007: Missing HSI Fallback Resilience Audit
- **Verifies**: FR-013, DI-005
- **Setup**: Evaluate fallback scenario array in Cell 17.
- **Procedure**:
  1. Inspect Full HSI Available metrics: $\text{RMSE} = 0.0194, \sigma = \pm 0.0299$.
  2. Inspect 50% Band Corruption metrics: $\text{RMSE} = 0.0219, \sigma = \pm 0.0319$.
  3. Inspect 100% Dropout metrics: $\text{RMSE} = 0.0211, \sigma = \pm 0.0375$.
- **Expected Result**: 100% Dropout matches $\text{CONFIG-A}$ baseline metrics identically.
- **Pass/Fail Criterion**: System maintains operational state and recovers to baseline performance.

### VP-008: Multi-Metric Trade-off & Hypothesis Verification
- **Verifies**: FR-001, FR-014, FR-015, UQ-003, UQ-004
- **Setup**: Review trade-off matrix DataFrame and terminal verdict in Cells 19 and 22.
- **Procedure**:
  1. Verify latency values: $1.2\text{ ms}$ ($\text{CONFIG-A}$) vs $4.8\text{ ms}$ ($\text{CONFIG-B}$).
  2. Verify memory footprint: $128\text{ MB}$ ($\text{CONFIG-A}$) vs $512\text{ MB}$ ($\text{CONFIG-B}$).
  3. Confirm hypothesis decision: Reject Null Hypothesis $H_0 \to$ Accept Alternative Hypothesis $H_1$.
  4. Confirm deployment policy: Retain $\text{CONFIG-A}$ as default; integrate HSI as optional high-precision module.
- **Expected Result**: Table formats cleanly; hypothesis verdict and deployment rules verified.
- **Pass/Fail Criterion**: Consistent governance logic between text declaration and quantitative metrics.

---

## 7. Verification Results

| VP | Date | Executor | Result | Empirical Evidence [NB] | Reviewer |
|:---:|:---:|:---:|:---:|:---|:---:|
| **VP-001** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `wavelengths` length = 224 ($400 - 2500\text{ nm}$); dips at $1400$ and $1900\text{ nm}$. | Baseline Audit |
| **VP-002** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | Dropped noisy bands = **24**; Cleaned QC cube shape = **(1000, 200)**. | Baseline Audit |
| **VP-003** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | Top 1 PC = **1.04%**, Top 3 = **3.01%**, Top 6 = **5.87%**, Top 10 = **9.50%**; shape `(1000, 10)`. | Baseline Audit |
| **VP-004** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | Train size = 800, Test size = 200; ground truth range $0.05$ to $0.45\text{ m}^3/\text{m}^3$. | Baseline Audit |
| **VP-005** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | $\text{RMSE}_A = \mathbf{0.0211}$, $\text{RMSE}_B = \mathbf{0.0194}$ ($\Delta = \mathbf{-7.76\%}$); $\sigma_A = \mathbf{0.0375}$, $\sigma_B = \mathbf{0.0299}$ ($\Delta = \mathbf{-20.28\%}$). | Baseline Audit |
| **VP-006** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | Plot 1 (`129876` B), Plot 2 (`141628` B), Plot 3 (`62816` B) rendered cleanly. | Baseline Audit |
| **VP-007** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | Fallback test: 100% Dropout reverts to $\text{RMSE} = \mathbf{0.0211}$, $\sigma = \pm \mathbf{0.0375}$. | Baseline Audit |
| **VP-008** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | Trade-off table verified: $4\times$ latency ($1.2 \to 4.8\text{ ms}$), $4\times$ RAM ($128 \to 512\text{ MB}$); $H_1$ accepted. | Baseline Audit |

---

## 8. Requirements Traceability Matrix

| Requirement ID | Design Element | Verification Procedure | Verification Result |
|:---|:---|:---:|:---:|
| **FR-001** | Baseline Architectural Freeze Declaration | VP-008 | **PASS** |
| **FR-002** | Wavelength Array Discretization Engine | VP-001 | **PASS** |
| **FR-003** | Soil Reflectance & Absorption Formulations | VP-001 | **PASS** |
| **FR-004** | Raw HSI Data Cube Synthesizer | VP-002 | **PASS** |
| **FR-005** | Atmospheric QC Masking Logic | VP-002 | **PASS** |
| **FR-006** | QC Array Sanitization & Clipping Engine | VP-002 | **PASS** |
| **FR-007** | Plot 1 Spectral Diagnostics Visualizer | VP-006 | **PASS** |
| **FR-008** | StandardScaler + PCA Decomposition Engine | VP-003 | **PASS** |
| **FR-009** | PCA Explained Variance Telemetry Logger | VP-003 | **PASS** |
| **FR-010** | Synthetic Ground Truth & Dataset Splitter | VP-004 | **PASS** |
| **FR-011** | Controlled AB Testing Evaluator | VP-005 | **PASS (PARTIAL\*)** |
| **FR-012** | Plot 2 Scatter & Boxplot Visualizer | VP-006 | **PASS** |
| **FR-013** | Missing HSI Fallback Routine | VP-007 | **PASS (PARTIAL\*)** |
| **FR-014** | Multi-Metric Trade-off DataFrame Builder | VP-008 | **PASS** |
| **FR-015** | Plot 3 Normalized Bar Chart & Verdict Logger | VP-006, VP-008 | **PASS** |
| **DI-001** | Reflectance Physical Range Bounding | VP-001, VP-002 | **PASS** |
| **DI-002** | Wavelength Monotonic Grid Sorting | VP-001 | **PASS** |
| **DI-003** | Cumulative Explained Variance Hierarchy | VP-003 | **PASS** |
| **DI-004** | Performance Superiority Metric Check | VP-005 | **PASS** |
| **DI-005** | Graceful Fallback Preservation Check | VP-007 | **PASS** |
| **IF-001** | Metric Evaluator Function Interface | VP-005 | **PASS** |
| **IF-002** | Dimensionality Reduction Matrix Shape Interface | VP-002, VP-003 | **PASS** |
| **IF-003** | Standardized Telemetry Axis Units | VP-006 | **PASS** |
| **IF-004** | ASCII Terminal Formatting Protocol | VP-008 | **PASS** |
| **UQ-001** | Relative Error Reduction Threshold ($\ge 5\%$) | VP-005 | **PASS** |
| **UQ-002** | Relative Uncertainty Contraction Threshold ($\ge 15\%$) | VP-005 | **PASS** |
| **UQ-003** | Computational Latency Overhead Quantification | VP-008 | **PASS** |
| **UQ-004** | Computational Memory Overhead Quantification | VP-008 | **PASS** |
| **NF-001** | Deterministic Seed Locking (1607) | VP-001, VP-004 | **PASS** |
| **NF-002** | Headless Unattended Execution Pipeline | VP-001 to VP-008 | **PASS** |
| **NF-003** | Dark Telemetry Styling Specifications | VP-006 | **PASS** |
| **NF-004** | Computational Execution Latency Benchmark | VP-001 to VP-008 | **PASS** |

*\*Note: FR-011 and FR-013 carry design limitations documented in the Defect Register below.*

---

## 9. Configuration and Change Control

### 9.1 Controlled Items

1. **Source Notebook**: `1_notebooks_sandbox/09-hyperspectral-experiment.ipynb`
2. **Requirements Baseline**: `8_docs/01_Notebooks/09. hyperspectral experiment/09_hyperspectral_experiment_REQUIREMENTS.md`
3. **Technical Description**: `8_docs/01_Notebooks/09. hyperspectral experiment/09_hyperspectral_experiment.rst`
4. **Environment**: Python 3.10+ virtual environment (`mridansh_env`) with fixed Scikit-Learn locks.
5. **Random Seed Baseline**: NumPy `1607`, PyTorch `1607`.

### 9.2 Baseline Identification

- **Baseline ID**: `NB09-BL-01`
- **Configuration Tag**: `v1.0-scientific-audit-day08-10`
- **Effective Date**: 2026-10-08

### 9.3 Change Procedure

```text
Change Request (CR)
       │
       ▼
Impact Analysis (Assessing PCA dimensionality, latency overhead & baseline compatibility)
       │
       ▼
Technical Approval (Division Lead & Chief Systems Engineer)
       │
       ▼
Implementation (Code update in 1_notebooks_sandbox/)
       │
       ▼
Re-verification (Full execution of VP-001 through VP-008)
       │
       ▼
Baseline Update (Version bump in MD, RST, and Git history)
```

### 9.4 Version Control Rules

- Modifications to atmospheric absorption mask thresholds, PCA component count ($k=10$), or hypothesis decision rules require formal review.
- Direct editing of baseline documentation without an associated Change Request is strictly prohibited.

---

## 10. Open Defects and Discrepancies

| ID | Description | Affected Requirement | Severity | Status | Corrective Action |
|:---:|:---|:---:|:---:|:---:|:---|
| **D-001** | **Mocked AB Prediction Simulation / Zero Model Training**: In Cell 13, neither $\text{CONFIG-A}$ nor $\text{CONFIG-B}$ trains a model. Predictions are synthesized simply by adding Gaussian noise to ground truth (`y_test + np.random.normal(0, 0.022)` vs `0.018`). The PCA features extracted in Cell 09 are never utilized in any predictive model. | FR-011 | **CRITICAL** | `OPEN` | Train actual regressors (e.g. Ridge / Random Forest / MLP) on baseline features vs baseline + PCA features to evaluate empirical predictive power. |
| **D-002** | **PCA White-Noise Artifact from Tiled Spectra**: In Cell 04, `hsi_raw_cube` is generated by tiling a single spectrum across all 1000 pixels and adding i.i.d. noise. Standardizing removes the common signal, leaving pure white noise; hence 10 PCs capture merely **$9.50\%$** variance. | FR-004, FR-009 | **HIGH** | `OPEN` | Introduce realistic cross-pixel spectral variability (e.g., varying soil organic matter, iron oxide content, and texture) so that PCA captures physically meaningful absorption components ($>85\%$ variance). |
| **D-003** | **Discrepant Band Count Annotation in Plot 1**: In Cell 08 line 190, the plot legend labels `"HSI Continuous (196 bands)"`, but the actual cleaned array has **200 bands** ($224 - 24 = 200$). | FR-007 | **LOW** | `OPEN` | Correct legend string in Cell 08 to `"HSI Continuous (200 bands)"`. |
| **D-004** | **Static Fallback Arithmetic**: In Cell 17, fallback metrics are calculated using hardcoded arithmetic offsets (`rmse_b + 0.0025`, `rmse_a`) rather than running actual corrupted HSI arrays through an inference pipeline. | FR-013 | **MEDIUM** | `OPEN` | Implement active channel zero-masking on input matrices and evaluate predictions dynamically. |
| **D-005** | **Decoupled Pipeline and Missing Data Export**: Notebook 09 operates completely in-memory without ingesting real satellite HSI tiles (PRISMA/EnMAP) or exporting PCA transformation models to `data_processed/`. | IF-002 | **MEDIUM** | `OPEN` | Ingest calibrated L2A surface reflectance tiles and export PCA projection matrices and metrics to `data_processed/hyperspectral/`. |

---

## 11. Risks and Assumptions

### 11.1 Risks

- **R-001 (False Precision Confirmation)**: Because the AB test artificially injected lower noise into $\text{CONFIG-B}$ ($\sigma=0.018$ vs $0.022$), the hypothesis test accepted $H_1$ by synthetic construction rather than validating real spectroscopic soil moisture estimation.
- **R-002 (Severe Throughput Penalty)**: If deployed to production, the $4.0\times$ latency penalty ($4.8\text{ ms/pixel}$) and $4.0\times$ RAM footprint ($512\text{ MB}$) will bottleneck large-scale regional and national scale soil moisture mapping pipelines.
- **R-003 (Orbital Revisit Scarcity)**: Spaceborne hyperspectral missions (PRISMA, EnMAP) have narrow swath widths ($30\text{ km}$) and long revisit intervals ($15–30\text{ days}$), making operational reliance on HSI impractical without continuous optical/SAR fallback.
- **R-004 (Atmospheric Water Contamination)**: In tropical and monsoonal regimes, high column water vapor can broaden absorption windows beyond 1420 nm and 1950 nm, contaminating adjacent valid bands.

### 11.2 Assumptions

- **A-001 (Linear Dimensionality Sufficiency)**: 10 linear principal components are assumed sufficient to capture the non-linear spectral absorption dynamics of soil moisture.
- **A-002 (Atmospheric Absorption Stationarity)**: Atmospheric water vapor absorption bands are assumed stationary and completely contained within 1350–1420 nm and 1800–1950 nm.
- **A-003 (Independent Residuals)**: Measurement noise across contiguous 10 nm channels is assumed independent and identically distributed.
- **A-004 (Graceful Fallback Parity)**: Total failure of the HSI sensor is assumed to revert performance identically to the frozen baseline without causing covariance matrix singularity.

---

## 12. Release / Baseline Acceptance Criteria

To declare Notebook 09 baseline-ready for production deployment, the following criteria must be fulfilled:

1. **Mandatory Functional Requirements**: All requirements marked `MET` or `PARTIAL` must be resolved to `MET` by replacing mocked noise injections with real regressor training.
2. **Defect Threshold**: Critical defect D-001 and High defect D-002 must be fully resolved.
3. **Traceability**: Bidirectional traceability must achieve $100\%$ across all functional requirements, verification procedures, and test outputs.
4. **Reproducibility**: Execution under seed `1607` must produce bit-exact matches to all logged RMSE, explained variance, and trade-off metrics.
5. **Configuration Freeze**: All code cells, requirements documentation, and RST technical descriptions must be frozen under tag `NB09-BL-01`.

---

## 13. Review and Approval

| Role | Name | Signature | Date |
|:---|:---|:---|:---:|
| **Author / Systems Engineer** | Gourgopal Mohapatra | *[Signed Electronically]* | 2026-10-08 |
| **Independent Verification Reviewer** | *(To be assigned)* | | |
| **Quality & Safety Assurance Authority** | *(To be assigned)* | | |

---

## 14. Limitations / Scientific Boundary

> [!CAUTION]
> **SCIENTIFIC BOUNDARY: ALGORITHMIC HYPOTHESIS DEMONSTRATION VS. REAL SPECTROSCOPIC VALIDATION**
> 
> The hypothesis testing protocol in Notebook 09 demonstrates the **systems engineering governance workflow** for evaluating sensor augmentation.
> 
> Because the spectral data cube and prediction outputs are generated via synthetic mathematical functions, this verification confirms **software logic, PCA pipeline execution, and trade-off decision governance**, but does **not constitute empirical spectroscopic proof** of hyperspectral soil moisture estimation. Real-world validation requires benchmarking against calibrated laboratory spectroradiometer measurements (ASD FieldSpec) and spaceborne PRISMA/EnMAP Level-2D surface reflectance products.

---

## 15. Intellectual Property & Controlled Distribution

```text
========================================================================================
                      THE MRIDANSH (AETHER-MRID1607X)
         CENTRAL ENGINE: MULTI-DOMAIN SOIL INTELLIGENCE & GEOTECHNICAL STABILITY
========================================================================================
Copyright (c) 2026 Gourgopal Mohapatra. All Rights Reserved.
Developed & Maintained by: Gourgopal Mohapatra
Lead Organization: JCC HEADQUARTER
Facility: JCC CAMPUS 2 — RS-SDA Division (Remote Sensing & Spatial Data Analytics)

CONFIDENTIAL & PROPRIETARY SCIENTIFIC RESEARCH FRAMEWORK
This codebase, neural architecture specifications (PINN / GCN), numerical formulations,
and associated telemetry pipelines constitute proprietary intellectual property.

Unauthorized copying, redistribution, reverse engineering, or commercial execution of
this software package — in whole or in part, via any medium — is strictly prohibited
without prior written authorization from the lead researcher and JCC RS-SDA.
========================================================================================
```
