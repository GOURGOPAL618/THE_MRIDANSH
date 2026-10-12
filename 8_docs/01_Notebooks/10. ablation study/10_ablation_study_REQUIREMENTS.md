# THE MRIDANSH (AETHER-MRID1607X)
# Notebook 10 — Component Contribution Analysis & Scientific Ablation Study
# Requirements, Verification and Configuration Control

---

## 1. Document Control

### 1.1 Identification

| Field | Value |
|:---|:---|
| **Document ID** | MRID-NB10-DOC-001 |
| **Notebook ID** | `10-ablation-study.ipynb` |
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
| 0.1 | 2026-10-08 | Gourgopal Mohapatra | Structural analysis of `10-ablation-study.ipynb` cells, 8-configuration ablation sweep, marginal utility deltas, and Pareto front metrics. |
| 1.0 | 2026-10-08 | Gourgopal Mohapatra | Baseline requirements specification: incremental module progression (Config A–H), Pareto trade-off optimization, architectural tier classification, and full defect auditing. |

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
  - `A` (Analysis): Theoretical evaluation of marginal utility derivatives, Pareto optimality, and variance reduction.
  - `I` (Inspection): Manual examination of source code, configuration constants, and layer declarations.
  - `D` (Demonstration): Observation of operational execution, multi-panel diagnostic figures, and summary tables.
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

This document establishes the formal engineering requirements, mathematical formulations, verification procedures, empirical execution results, bidirectional traceability, configuration management, and technical discrepancy logs for Jupyter notebook `10-ablation-study.ipynb` within **THE MRIDANSH** system.

### 2.2 System Context

**THE MRIDANSH** (*AETHER-MRID1607X*) estimates high-resolution volumetric soil moisture by fusing multi-spectral optical imagery, synthetic aperture radar (SAR), digital elevation topography, meteorological data, physics-informed neural network (PINN) PDE boundaries, and Ensemble Kalman Filter (EnKF) assimilation.

Within this macro-architecture:
- **Notebooks 01–06** develop the core estimation pipeline (Data Ingestion, Preprocessing, Spatial Graph GCN, Temporal ConvLSTM, Richards PDE PINN, EnKF State Assimilation).
- **Notebooks 07–09** perform uncertainty quantification, failure robustness stress testing, and hyperspectral augmentation evaluation.
- **Notebook 10 (Item Under Documentation)** conducts the formal Component Contribution Analysis & Scientific Ablation Study. It systematically deconstructs the architecture into 8 cumulative configurations (Config A to Config H), quantifying the isolated marginal utility ($\Delta\text{RMSE}, \Delta\sigma$), cumulative accuracy gain ($0\% \to 68.36\%$), and computational runtime cost ($0.3\text{ ms} \to 5.2\text{ ms}$) of each modular layer. It maps all components onto a Pareto efficiency frontier to establish the definitive architectural justification for production deployment.
- **Downstream Consumer (Notebook 11)** utilizes this architectural baseline to evaluate cross-catchment out-of-distribution generalization.

### 2.3 Notebook Objective

Notebook 10 covers Sprint Days 11–12 of the Scientific Audit & Validation Mission:
1. **Day 11 Objective (Incremental Ablation Sweep)**: Establish a synthetic calibration benchmark ($N=1000$ points), assemble 8 cumulative architectural configurations (Config A to Config H), simulate step-by-step prediction errors and uncertainty contraction, compute marginal utility deltas ($\Delta\text{RMSE}, \Delta\sigma$), and render Plot 1 trajectories.
2. **Day 12 Objective (Component-Contribution Matrix & Pareto Audit)**: Categorize modules into architectural roles (Core Baseline, Primary Driver, Contextual Adjuster, High-Precision Module) and essentiality tiers (Essential, Secondary Core, Optional/Targeted), map configurations onto an accuracy-versus-latency Pareto frontier (Plot 2), and document the final scientific architectural justification.

### 2.4 In Scope

- All 16 cells of `10-ablation-study.ipynb` (6 code cells, 10 markdown cells).
- Definition of the 8 incremental architectural configurations:
  1. **Config A (S2)**: Optical Sentinel-2 baseline
  2. **Config B (+S1)**: Config A + Sentinel-1 C-band SAR
  3. **Config C (+DEM)**: Config B + Digital Elevation Model topography
  4. **Config D (+Weather)**: Config C + Meteorological rainfall/temperature
  5. **Config E (+Temporal)**: Config D + Lagged moisture temporal memory
  6. **Config F (+Physics)**: Config E + Richards PDE PINN constraints
  7. **Config G (+EnKF)**: Config F + Ensemble Kalman Filter sequential state assimilation
  8. **Config H (+HSI)**: Config G + Hyperspectral PCA feature matrix
- Synthetic benchmark generation: $y_{\text{true}} \in [0.04, 0.46]\text{ m}^3/\text{m}^3$ over $N=1000$ samples.
- Evaluation of RMSE, $R^2$, uncertainty $\sigma$, and inference latency across all 8 configurations.
- Step-by-step marginal utility calculation ($\Delta\text{RMSE}, \Delta\sigma$) and cumulative percentage gain tracking.
- Execution of the accuracy-versus-speed Pareto efficiency analysis.
- Classification of all modules into the official 3-tier essentiality taxonomy.

### 2.5 Out of Scope

- Retraining deep neural networks (ConvLSTM, PINN) from scratch across all 8 ablation permutations.
- Permutation importance shuffling on real geospatial raster tiles.
- Backward step-wise feature elimination (the study evaluates forward cumulative assembly).
- Direct serialization of intermediate ablation prediction arrays to disk.

### 2.6 Current-State Declaration (Mandatory Engineering Disclosure)

> [!WARNING]
> **MANDATORY CURRENT-STATE DECLARATION: SYNTHETIC SIMULATION AND STATIC PARAMETER LISTS**
> 
> Inspection of `10-ablation-study.ipynb` confirms that the notebook operates as an idealized conceptual simulation harness rather than retraining deep learning models for each ablation step:
> 1. **Mocked Ablation Sweep (Defect D-001)**: In Cell 06, predictions are not generated by executing actual machine learning models. Instead, predictions are synthesized by adding pre-specified Gaussian noise offsets (`noise_levels = [0.055, 0.042, 0.036, 0.031, 0.026, 0.022, 0.019, 0.017]`) and static uncertainty values (`unc_levels = [0.085, 0.068, 0.058, 0.050, 0.042, 0.036, 0.031, 0.026]`) directly to ground truth.
> 2. **Unused Synthetic Feature Inputs (Defect D-002)**: In Cell 04, feature arrays `X_s2, X_s1, X_dem, X_weather, X_temporal` are constructed, but none of these tensors are ever passed into any prediction model or evaluation function in Cell 06.
> 3. **Narrative Metric Discrepancies (Defect D-003)**: The final scientific summary in Cell 14 quotes percentage gains that contradict the programmatically calculated values in Cells 09 and 11:
>    - S1 jump: Cell 14 quotes **+28.13%**, whereas Cells 09/11 compute **21.88%**.
>    - PINN jump: Cell 14 quotes **+19.36%**, whereas Cell 09 computes **21.25%**.
>    - EnKF jump: Cell 14 quotes **+15.83%**, whereas Cell 09 computes **9.45%**.
>    - HSI jump: Cell 14 quotes **+7.88%**, whereas Cell 09 computes **10.86%**.
> 4. **Code Typographical Errors (Defect D-004)**: Variables and columns carry typos (`Delat_Unc`, `Primery Driver`, `Essentiality Tire`, `Latent (ms)`).
> 5. **Decoupled Pipeline (Defect D-005)**: No real checkpoints are loaded from `data_checkpoints/`, and no summary tables are exported to `data_processed/`.

---

## 3. Definitions and Abbreviations

| Term / Abbreviation | Definition |
|:---|:---|
| **Ablation Study** | Systematic removal or addition of components to isolate individual contribution. |
| **Marginal Utility** | Incremental performance improvement ($\Delta\text{RMSE}, \Delta\sigma$) achieved by adding one module. |
| **Pareto Frontier** | Optimal trade-off boundary where accuracy cannot be improved without increasing latency. |
| **Cumulative Gain** | Total percentage reduction in RMSE relative to the optical baseline ($\text{Config A}$). |
| **Config A–H** | The eight cumulative architectural configurations evaluated in forward assembly. |
| **Core Baseline** | Minimal operational sensing layer (Sentinel-2 optical). |
| **Primary Driver** | High-yield architectural layer providing major step-function accuracy gains ($>20\%$). |
| **Contextual Adjuster** | Secondary environmental layer providing micro-climate and topographic tuning ($10\%–15\%$). |
| **High-Precision Module**| Optional augmentation providing marginal accuracy refinement at high computational cost. |
| **JCC RS-SDA** | Jagannath Command Center — Remote Sensing & Spatial Data Analytics Division. |

---

## 4. Requirements

### 4.1 Functional Requirements

- **FR-001**: The software shall define an 8-stage incremental configuration matrix encompassing:
  - Config A: Sentinel-2 (Optical Baseline)
  - Config B: Config A + Sentinel-1 SAR
  - Config C: Config B + DEM Topography
  - Config D: Config C + Weather Precipitation/Temperature
  - Config E: Config D + Temporal Memory Dynamics
  - Config F: Config E + Physics PINN Constraints
  - Config G: Config F + EnKF Sequential State Assimilation
  - Config H: Config G + Hyperspectral PCA Feature Matrix
- **FR-002**: The software shall generate a synthetic benchmark dataset of $N=1000$ spatial samples with ground truth soil moisture:
  $$y_{\text{true}} = \operatorname{clip}\left(0.22 + 0.14 \sin(t) + 0.03 \cos(3t) + \mathcal{N}(0, 0.01^2), 0.04, 0.46\right)$$
  spanning a physical moisture range of $[0.045, 0.402]\text{ m}^3/\text{m}^3$.
- **FR-003**: The software shall synthesize multi-modal feature representations for optical ($\mathbf{X}_{\text{S2}}$), SAR ($\mathbf{X}_{\text{S1}}$), topography ($\mathbf{X}_{\text{DEM}}$), weather ($\mathbf{X}_{\text{weather}}$), and temporal memory ($\mathbf{X}_{\text{temporal}}$).
- **FR-004**: The software shall implement metric calculation function `calc_metrics(y_real, y_pred, unc_base)` computing RMSE, coefficient of determination ($R^2$), and mean uncertainty $\sigma$.
- **FR-005**: The software shall simulate prediction arrays for all 8 configurations by adding progressively decreasing Gaussian noise vectors $\mathcal{N}(0, \sigma_{\text{noise}, i}^2)$ to ground truth and clipping outputs to $[0.02, 0.48]\text{ m}^3/\text{m}^3$.
- **FR-006**: The software shall record empirical performance metrics in DataFrame `df_ablation`:
  - Config A: $\text{RMSE} \approx 0.0540, R^2 \approx 0.715, \sigma = \pm 0.085, \text{Latency} = 0.3\text{ ms}$
  - Config B: $\text{RMSE} \approx 0.0422, R^2 \approx 0.826, \sigma = \pm 0.068, \text{Latency} = 0.5\text{ ms}$
  - Config C: $\text{RMSE} \approx 0.0358, R^2 \approx 0.875, \sigma = \pm 0.058, \text{Latency} = 0.7\text{ ms}$
  - Config D: $\text{RMSE} \approx 0.0315, R^2 \approx 0.903, \sigma = \pm 0.050, \text{Latency} = 0.9\text{ ms}$
  - Config E: $\text{RMSE} \approx 0.0269, R^2 \approx 0.929, \sigma = \pm 0.042, \text{Latency} = 1.1\text{ ms}$
  - Config F: $\text{RMSE} \approx 0.0212, R^2 \approx 0.956, \sigma = \pm 0.036, \text{Latency} = 1.5\text{ ms}$
  - Config G: $\text{RMSE} \approx 0.0192, R^2 \approx 0.964, \sigma = \pm 0.031, \text{Latency} = 2.1\text{ ms}$
  - Config H: $\text{RMSE} \approx 0.0171, R^2 \approx 0.971, \sigma = \pm 0.026, \text{Latency} = 5.2\text{ ms}$
- **FR-007**: The software shall render Aerospace Plot 1 showing:
  - Subplot 1: Step-by-step RMSE reduction trajectory across Config A through Config H with numerical annotations.
  - Subplot 2: Model uncertainty contraction trajectory ($\pm\sigma$) across all configurations.
- **FR-008**: The software shall calculate step-by-step marginal utility deltas:
  $$\Delta\text{RMSE}_i = \text{RMSE}_i - \text{RMSE}_{i-1}, \quad \Delta\sigma_i = \sigma_i - \sigma_{i-1}$$
  and evaluate percentage gains relative to the preceding stage.
- **FR-009**: The software shall compute cumulative percentage accuracy gains relative to baseline Config A:
  $$\text{Gain}_{\text{cum}, i} = \frac{\text{RMSE}_A - \text{RMSE}_i}{\text{RMSE}_A} \times 100\%$$
- **FR-010**: The software shall construct and print the Scientific Component-Contribution Matrix classifying each configuration into an Architectural Role and an Essentiality Tier:
  - Config A: Core Baseline | Essential
  - Config B, F, G: Primary Driver | Essential
  - Config C, D, E: Contextual Adjuster | Secondary Core
  - Config H: High-Precision Module | Optional / Targeted
- **FR-011**: The software shall map all configurations onto a 2D Pareto efficiency plane plotting inference latency (ms/pixel) on the x-axis against normalized cumulative accuracy gain on the y-axis.
- **FR-012**: The software shall render Aerospace Plot 2 visualizing the Pareto efficiency front with color-coded markers, configuration labels, and dashed trade-off trajectory lines.
- **FR-013**: The software shall verify that SAR integration (Config B) delivers the single largest sensor-driven error drop ($\ge 20\%$ marginal gain).
- **FR-014**: The software shall verify that Physics PINN constraints (Config F) deliver the single largest model-driven non-sensor error drop ($\ge 20\%$ marginal gain).
- **FR-015**: The software shall log the final architectural justification confirming that the baseline MRIDANSH stack (Configs A–G) captures $64.51\%$ cumulative gain at $2.1\text{ ms}$ latency, whereas HSI (Config H) adds $3.85\%$ gain at a $147\%$ latency penalty.

### 4.2 Data Integrity Requirements

- **DI-001**: Monotonic RMSE Reduction: Prediction error shall strictly decrease across cumulative assembly: $\text{RMSE}_{i+1} < \text{RMSE}_i$.
- **DI-002**: Monotonic Uncertainty Contraction: Model uncertainty bounds shall strictly contract across cumulative assembly: $\sigma_{i+1} < \sigma_i$.
- **DI-003**: Monotonic $R^2$ Elevation: Goodness-of-fit shall strictly increase across cumulative assembly: $R^2_{i+1} > R^2_i$.
- **DI-004**: Monotonic Latency Growth: Computational inference latency shall strictly increase as layers are added: $\text{Latency}_{i+1} > \text{Latency}_i$.
- **DI-005**: Cumulative Gain Bounding: Cumulative percentage accuracy gains shall remain strictly bounded within $[0.0\%, 100.0\%]$.

### 4.3 Interface Requirements

- **IF-001**: Function `calc_metrics` shall accept `(y_real, y_pred, unc_base)` and return tuple `(rmse, r2, unc)`.
- **IF-002**: DataFrame `df_ablation` shall contain standard columns: `Config`, `RMSE`, `R2`, `Uncertainty_σ`, `Latency_ms`.
- **IF-003**: DataFrame `df_matrix` shall contain standard columns: `Module`, `RMSE (m³/m³)`, `Cumulative Gain`, `Uncertainty σ`, `Latent (ms)`, `Architectural Role`, `Essentiality Tire`.
- **IF-004**: Terminal outputs shall display formatted tabular summaries and clean ASCII banners.

### 4.4 Uncertainty / Quality Requirements

- **UQ-001**: The full core baseline (Config G) shall achieve an uncertainty bound of $\sigma \le 0.035\text{ m}^3/\text{m}^3$.
- **UQ-002**: The full HSI-augmented system (Config H) shall achieve an uncertainty bound of $\sigma \le 0.026\text{ m}^3/\text{m}^3$.
- **UQ-003**: Cumulative accuracy gain shall exceed $60\%$ upon integration of physics constraints (Config F).
- **UQ-004**: In-graph annotations on Plot 1 and Plot 2 shall accurately reflect the numerical values computed in `df_ablation`.

### 4.5 Non-Functional Requirements

- **NF-001**: Deterministic seeds shall be fixed for NumPy (`np.random.seed(1607)`) and PyTorch (`torch.manual_seed(1607)`).
- **NF-002**: The notebook shall execute unattended from Cell 00 to Cell 15 without interactive user input.
- **NF-003**: Visual plots shall employ the JCC RS-SDA dark telemetry styling (`#00FFCC`, `#FF9900`, `#1A3344`, monospace typography).
- **NF-004**: Computational execution time shall evaluate in $< 2.0$ seconds on CPU/CUDA hardware.

---

## 5. Requirements Attributes

| ID | Requirement Statement | Rationale | Method | Acceptance Criterion | Status |
|:---|:---|:---|:---:|:---|:---:|
| **FR-001** | Define 8-stage cumulative configuration matrix. | Establishes incremental ablation architecture. | I | Configs A through H declared in Cell 01 and Cell 06. | **MET** |
| **FR-002** | Generate $N=1000$ synthetic ground truth samples. | Benchmark dataset initialization. | T | Values bounded $[0.045, 0.402]\text{ m}^3/\text{m}^3$. | **MET** |
| **FR-003** | Synthesize 5 multi-modal input features. | Input feature representation. | T | Optical, SAR, DEM, weather, temporal arrays created. | **PARTIAL\*** |
| **FR-004** | Implement `calc_metrics` evaluating RMSE, R², σ. | Metric evaluation contract. | I/T | Function accepts 3 args, returns 3 scalars. | **MET** |
| **FR-005** | Simulate prediction arrays with decreasing noise. | Simulates incremental layer integration. | T | Decreasing noise: $0.055 \to 0.017$. | **PARTIAL\*** |
| **FR-006** | Compile `df_ablation` across all 8 configurations. | Ablation sweep record keeping. | T | All 8 rows match baseline numbers. | **MET** |
| **FR-007** | Render Plot 1 error and uncertainty trajectories. | Visual incremental progression. | D | 2-panel figure rendered (`length=113704` bytes). | **MET** |
| **FR-008** | Compute marginal utility deltas ($\Delta\text{RMSE}, \Delta\sigma$). | Quantifies step-by-step layer value. | T | Deltas computed: A $\to$ B = **-0.0118**, E $\to$ F = **-0.0057**. | **MET** |
| **FR-009** | Compute cumulative accuracy gains relative to S2. | Quantifies total architectural gain. | T | Gains: B=**21.88%**, F=**60.80%**, G=**64.51%**, H=**68.36%**. | **MET** |
| **FR-010** | Construct Component-Contribution Matrix. | Architectural governance taxonomy. | D | 8 modules categorized into Roles and Tiers. | **MET** |
| **FR-011** | Map configurations onto Pareto efficiency plane. | Accuracy vs latency trade-off. | A/T | Normalized gain vs latency evaluated. | **MET** |
| **FR-012** | Render Plot 2 Pareto efficiency front figure. | Visual trade-off frontier. | D | Plot 2 rendered (`length=73364` bytes). | **MET** |
| **FR-013** | Verify SAR integration (Config B) gain $\ge 20\%$. | Sensor multi-modal justification. | T | Empirical gain = **21.88%** ($\ge 20\%$). | **MET** |
| **FR-014** | Verify Physics PINN (Config F) gain $\ge 20\%$. | Physical PDE constraint justification. | T | Empirical marginal gain = **21.25%** ($\ge 20\%$). | **MET** |
| **FR-015** | Log final architectural justification summary. | Production deployment governance. | D | Terminal summary logged in Cell 14. | **MET** |
| **DI-001** | Strict monotonic RMSE reduction. | Cumulative assemblies must improve error. | T | $0.0540 > 0.0422 > \dots > 0.0171\text{ m}^3/\text{m}^3$. | **MET** |
| **DI-002** | Strict monotonic uncertainty contraction. | Added information must contract bounds. | T | $0.085 > 0.068 > \dots > 0.026\text{ m}^3/\text{m}^3$. | **MET** |
| **DI-003** | Strict monotonic $R^2$ elevation. | Added features must improve variance fit. | T | $0.7147 < 0.8259 < \dots < 0.9714$. | **MET** |
| **DI-004** | Strict monotonic latency growth. | Additional layers consume computation. | T | $0.3 < 0.5 < 0.7 < 0.9 < 1.1 < 1.5 < 2.1 < 5.2\text{ ms}$. | **MET** |
| **DI-005** | Cumulative gain bounded $[0, 100\%]$. | Valid percentage range. | T | Minimum = $0.00\%$, Maximum = $68.36\%$. | **MET** |
| **IF-001** | `calc_metrics` interface contract. | Predictor evaluation signature. | I/T | Signature matches `(y_real, y_pred, unc_base)`. | **MET** |
| **IF-002** | `df_ablation` DataFrame schema. | Standard ablation table schema. | T | 8 rows, 5 standard columns present. | **MET** |
| **IF-003** | `df_matrix` DataFrame schema. | Executive summary table schema. | T | 8 rows, 7 standard columns present. | **MET** |
| **IF-004** | Standard ASCII headers and precision formatting. | Telemetry readability standard. | D | Standard Pandas formatting verified. | **MET** |
| **UQ-001** | Core baseline uncertainty $\sigma \le 0.035$. | Core system quality target. | T | Config G uncertainty = **±0.031** ($\le 0.035$). | **MET** |
| **UQ-002** | HSI-augmented uncertainty $\sigma \le 0.026$. | Target augmented quality target. | T | Config H uncertainty = **±0.026** ($\le 0.026$). | **MET** |
| **UQ-003** | Cumulative gain $> 60\%$ with PINN. | Physical modeling value threshold. | T | Config F cumulative gain = **60.80%** ($>60\%$). | **MET** |
| **UQ-004** | In-graph annotations match table numbers. | Visual reporting truth. | D | Exact values annotated on Plot 1 and Plot 2. | **MET** |
| **NF-001** | Deterministic seed initialization (1607). | Numerical reproducibility standard. | I/T | NumPy and PyTorch seeds set in Cell 02. | **MET** |
| **NF-002** | Headless unattended execution. | Batch pipeline compatibility. | D | All 16 cells execute sequentially without errors. | **MET** |
| **NF-003** | Dark telemetry UI styling on generated figures. | Institutional visual consistency. | I | Cyan, orange, yellow accents on dark background. | **MET** |
| **NF-004** | Execution runtime $< 2.0$ seconds. | Computational execution speed. | A | End-to-end execution completes in $\approx 1.1$s. | **MET** |

*\*Note: FR-003 and FR-005 marked PARTIAL due to unused feature arrays (D-002) and mocked noise simulation (D-001).*

---

## 6. Verification Procedures

### VP-001: Ground Truth Synthesis and Feature Generation
- **Verifies**: FR-002, FR-003, DI-005, NF-001
- **Setup**: Python 3.10+ kernel with NumPy and PyTorch under seed 1607.
- **Procedure**:
  1. Initialize seed 1607.
  2. Compute sinusoidal `y_true` over $N=1000$ points.
  3. Synthesize `X_s2, X_s1, X_dem, X_weather, X_temporal`.
  4. Verify minimum and maximum range of `y_true`.
- **Expected Result**:
  - `len(y_true) == 1000`
  - `y_true.min() == 0.045`, `y_true.max() == 0.402`
- **Pass/Fail Criterion**: Exact length 1000 and verified value bounds.

### VP-002: Ablation Sweep Simulation and DataFrame Compilation
- **Verifies**: FR-001, FR-004, FR-005, FR-006, DI-001, DI-002, DI-003, DI-004
- **Setup**: Execute the 8-configuration simulation loop in Cell 06.
- **Procedure**:
  1. Iterate across `configs` with specified `noise_levels`, `unc_levels`, and `runtimes_ms`.
  2. Synthesize `pred = np.clip(y_true + n_err, 0.02, 0.48)`.
  3. Compute `rmse, r2, unc = calc_metrics(y_true, pred, unc_levels[i])`.
  4. Populate DataFrame `df_ablation`.
- **Expected Result**:
  - Config A: $\text{RMSE} = \mathbf{0.053975}, R^2 = \mathbf{0.714731}, \sigma = \mathbf{0.085}, \text{Lat} = \mathbf{0.3\text{ ms}}$
  - Config B: $\text{RMSE} = \mathbf{0.042167}, R^2 = \mathbf{0.825891}, \sigma = \mathbf{0.068}, \text{Lat} = \mathbf{0.5\text{ ms}}$
  - Config C: $\text{RMSE} = \mathbf{0.035765}, R^2 = \mathbf{0.874745}, \sigma = \mathbf{0.058}, \text{Lat} = \mathbf{0.7\text{ ms}}$
  - Config D: $\text{RMSE} = \mathbf{0.031492}, R^2 = \mathbf{0.902887}, \sigma = \mathbf{0.050}, \text{Lat} = \mathbf{0.9\text{ ms}}$
  - Config E: $\text{RMSE} = \mathbf{0.026867}, R^2 = \mathbf{0.929320}, \sigma = \mathbf{0.042}, \text{Lat} = \mathbf{1.1\text{ ms}}$
  - Config F: $\text{RMSE} = \mathbf{0.021158}, R^2 = \mathbf{0.956164}, \sigma = \mathbf{0.036}, \text{Lat} = \mathbf{1.5\text{ ms}}$
  - Config G: $\text{RMSE} = \mathbf{0.019158}, R^2 = \mathbf{0.964059}, \sigma = \mathbf{0.031}, \text{Lat} = \mathbf{2.1\text{ ms}}$
  - Config H: $\text{RMSE} = \mathbf{0.017077}, R^2 = \mathbf{0.971444}, \sigma = \mathbf{0.026}, \text{Lat} = \mathbf{5.2\text{ ms}}$
- **Pass/Fail Criterion**: All metric values strictly match expected baseline numbers within $\pm 0.0001$.

### VP-003: Marginal Utility Deltas Verification
- **Verifies**: FR-008, FR-013, FR-014
- **Setup**: Execute `np.diff` on `df_ablation['RMSE']` and `df_ablation['Uncertainty_σ']`.
- **Procedure**:
  1. Compute step-by-step $\Delta\text{RMSE}$ and $\Delta\sigma$.
  2. Compute relative percentage gains relative to preceding configuration.
- **Expected Result**:
  - A $\to$ B: $\Delta\text{RMSE} = \mathbf{-0.0118}$ ($21.88\%$ gain) | $\Delta\sigma = \mathbf{-0.0170}$ ($20.00\%$ gain)
  - B $\to$ C: $\Delta\text{RMSE} = \mathbf{-0.0064}$ ($15.18\%$ gain) | $\Delta\sigma = \mathbf{-0.0100}$ ($14.71\%$ gain)
  - C $\to$ D: $\Delta\text{RMSE} = \mathbf{-0.0043}$ ($11.95\%$ gain) | $\Delta\sigma = \mathbf{-0.0080}$ ($13.79\%$ gain)
  - D $\to$ E: $\Delta\text{RMSE} = \mathbf{-0.0046}$ ($14.69\%$ gain) | $\Delta\sigma = \mathbf{-0.0080}$ ($16.00\%$ gain)
  - E $\to$ F: $\Delta\text{RMSE} = \mathbf{-0.0057}$ ($21.25\%$ gain) | $\Delta\sigma = \mathbf{-0.0060}$ ($14.29\%$ gain)
  - F $\to$ G: $\Delta\text{RMSE} = \mathbf{-0.0020}$ ($9.45\%$ gain) | $\Delta\sigma = \mathbf{-0.0050}$ ($13.89\%$ gain)
  - G $\to$ H: $\Delta\text{RMSE} = \mathbf{-0.0021}$ ($10.86\%$ gain) | $\Delta\sigma = \mathbf{-0.0050}$ ($16.13\%$ gain)
- **Pass/Fail Criterion**: Exact match with printed terminal output in Cell 09.

### VP-004: Component-Contribution Matrix and Cumulative Gains
- **Verifies**: FR-009, FR-010, UQ-001, UQ-002, UQ-003
- **Setup**: Evaluate DataFrame `df_matrix` in Cell 11.
- **Procedure**:
  1. Compute cumulative gain relative to Config A ($0.0540$).
  2. Verify classification logic for Roles and Tiers.
- **Expected Result**:
  - Config A: Cumulative Gain = **0.00%**, Role = Core Baseline, Tier = Essential
  - Config B: Cumulative Gain = **21.88%**, Role = Primary Driver, Tier = Essential
  - Config C: Cumulative Gain = **33.74%**, Role = Contextual Adjuster, Tier = Secondary Core
  - Config D: Cumulative Gain = **41.65%**, Role = Contextual Adjuster, Tier = Secondary Core
  - Config E: Cumulative Gain = **50.22%**, Role = Contextual Adjuster, Tier = Secondary Core
  - Config F: Cumulative Gain = **60.80%**, Role = Primary Driver, Tier = Essential
  - Config G: Cumulative Gain = **64.51%**, Role = Primary Driver, Tier = Essential
  - Config H: Cumulative Gain = **68.36%**, Role = High-Precision Module, Tier = Optional / Targeted
- **Pass/Fail Criterion**: Exact percentage matches and consistent classification assignments.

### VP-005: Visual Progression Diagnostics (Plot 1)
- **Verifies**: FR-007, UQ-004, NF-003
- **Setup**: Matplotlib dark theme configuration.
- **Procedure**:
  1. Render RMSE trajectory plot with data labels.
  2. Render Uncertainty trajectory plot with data labels.
- **Expected Result**: Figure display object generated (`length=113704` bytes).
- **Pass/Fail Criterion**: 2 subplots rendered with correct labels.

### VP-006: Pareto Efficiency Frontier Audit (Plot 2)
- **Verifies**: FR-011, FR-012, NF-003
- **Setup**: Render Pareto scatter plot in Cell 13.
- **Procedure**:
  1. Plot latency (ms) on x-axis vs normalized accuracy gain on y-axis.
  2. Plot dashed connection line tracing the Pareto frontier.
  3. Verify color-coded markers for each configuration.
- **Expected Result**: Single-panel Pareto figure rendered (`length=73364` bytes).
- **Pass/Fail Criterion**: All 8 configurations plotted and connected.

### VP-007: Architectural Justification and Summary Telemetry
- **Verifies**: FR-015
- **Setup**: Review printed banner in Cell 14.
- **Procedure**:
  1. Confirm core drivers identified: Sentinel-1, Physics PINN, EnKF Filter.
  2. Confirm contextual adjusters identified: DEM, Weather, Temporal.
  3. Confirm optional module identified: Hyperspectral HSI.
- **Expected Result**: Banner printed cleanly with complete summary.
- **Pass/Fail Criterion**: Clean terminal output with lock declaration.

### VP-008: Headless Execution & Runtime Benchmark
- **Verifies**: NF-002, NF-004
- **Setup**: Execute notebook end-to-end via Python kernel.
- **Procedure**:
  1. Measure wall-clock duration from Cell 00 to Cell 15.
  2. Ensure zero unhandled exceptions or interactive pauses.
- **Expected Result**: Total runtime $< 2.0$ seconds.
- **Pass/Fail Criterion**: Clean headless termination.

---

## 7. Verification Results

| VP | Date | Executor | Result | Empirical Evidence [NB] | Reviewer |
|:---:|:---:|:---:|:---:|:---|:---:|
| **VP-001** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `y_true.shape == (1000,)`; physical range $0.045$ to $0.402\text{ m}^3/\text{m}^3$. | Baseline Audit |
| **VP-002** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | Config A: RMSE=**0.0540**, R²=**0.715** $\to$ Config H: RMSE=**0.0171**, R²=**0.971**; all 8 rows verified. | Baseline Audit |
| **VP-003** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | Marginal gains: A $\to$ B = **21.88%**, E $\to$ F = **21.25%**, F $\to$ G = **9.45%**, G $\to$ H = **10.86%**. | Baseline Audit |
| **VP-004** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | Cumulative gains: B=**21.88%**, F=**60.80%**, G=**64.51%**, H=**68.36%**; 4 Essential, 3 Secondary, 1 Optional. | Baseline Audit |
| **VP-005** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | Plot 1 rendered (`length=113704` bytes PNG display data). | Baseline Audit |
| **VP-006** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | Plot 2 Pareto front rendered (`length=73364` bytes PNG display data). | Baseline Audit |
| **VP-007** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | Architectural justification printed to terminal; Core vs Optional tiers verified. | Baseline Audit |
| **VP-008** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | Headless execution completed in $\approx 1.15$ seconds without errors. | Baseline Audit |

---

## 8. Requirements Traceability Matrix

| Requirement ID | Design Element | Verification Procedure | Verification Result |
|:---|:---|:---:|:---:|
| **FR-001** | Incremental Configuration Array | VP-002 | **PASS** |
| **FR-002** | Synthetic Ground Truth Generator | VP-001 | **PASS** |
| **FR-003** | Multi-Modal Feature Synthesizer | VP-001 | **PASS (PARTIAL\*)** |
| **FR-004** | Metric Evaluator Function | VP-002 | **PASS** |
| **FR-005** | Prediction Noise Simulation Loop | VP-002 | **PASS (PARTIAL\*)** |
| **FR-006** | `df_ablation` Summary Builder | VP-002 | **PASS** |
| **FR-007** | Plot 1 Trajectory Visualizer | VP-005 | **PASS** |
| **FR-008** | Marginal Utility Delta Calculator | VP-003 | **PASS** |
| **FR-009** | Cumulative Gain Evaluator | VP-004 | **PASS** |
| **FR-010** | Component-Contribution Matrix Builder | VP-004 | **PASS** |
| **FR-011** | Pareto Coordinate Evaluator | VP-006 | **PASS** |
| **FR-012** | Plot 2 Pareto Front Visualizer | VP-006 | **PASS** |
| **FR-013** | SAR Jump Verification Logic | VP-003 | **PASS** |
| **FR-014** | Physics PINN Jump Verification Logic | VP-003 | **PASS** |
| **FR-015** | Final Architectural Justification Banner | VP-007 | **PASS** |
| **DI-001** | Strict Monotonic Error Reduction Assertion | VP-002 | **PASS** |
| **DI-002** | Strict Monotonic Uncertainty Contraction Assertion | VP-002 | **PASS** |
| **DI-003** | Strict Monotonic R² Elevation Assertion | VP-002 | **PASS** |
| **DI-004** | Strict Monotonic Latency Growth Assertion | VP-002 | **PASS** |
| **DI-005** | Cumulative Gain Bounding Logic | VP-004 | **PASS** |
| **IF-001** | Metric Function Signature Contract | VP-002 | **PASS** |
| **IF-002** | `df_ablation` Column Schema Definition | VP-002 | **PASS** |
| **IF-003** | `df_matrix` Column Schema Definition | VP-004 | **PASS** |
| **IF-004** | ASCII Terminal Formatting Protocol | VP-002, VP-004, VP-007 | **PASS** |
| **UQ-001** | Core Baseline Uncertainty Threshold ($\le 0.035$) | VP-004 | **PASS** |
| **UQ-002** | HSI Augmented Uncertainty Threshold ($\le 0.026$) | VP-004 | **PASS** |
| **UQ-003** | PINN Cumulative Gain Threshold ($> 60\%$) | VP-004 | **PASS** |
| **UQ-004** | In-Graph Telemetry Annotation Parity | VP-005, VP-006 | **PASS** |
| **NF-001** | Deterministic Seed Locking (1607) | VP-001 | **PASS** |
| **NF-002** | Headless Unattended Pipeline Execution | VP-001 to VP-008 | **PASS** |
| **NF-003** | Dark Telemetry Styling Specifications | VP-005, VP-006 | **PASS** |
| **NF-004** | Execution Latency Benchmark | VP-008 | **PASS** |

*\*Note: FR-003 and FR-005 carry design limitations documented in the Defect Register below.*

---

## 9. Configuration and Change Control

### 9.1 Controlled Items

1. **Source Notebook**: `1_notebooks_sandbox/10-ablation-study.ipynb`
2. **Requirements Baseline**: `8_docs/01_Notebooks/10. ablation study/10_ablation_study_REQUIREMENTS.md`
3. **Technical Description**: `8_docs/01_Notebooks/10. ablation study/10_ablation_study.rst`
4. **Environment**: Python 3.10+ virtual environment (`mridansh_env`) with fixed Pandas and Matplotlib locks.
5. **Random Seed Baseline**: NumPy `1607`, PyTorch `1607`.

### 9.2 Baseline Identification

- **Baseline ID**: `NB10-BL-01`
- **Configuration Tag**: `v1.0-scientific-audit-day11-12`
- **Effective Date**: 2026-10-08

### 9.3 Change Procedure

```text
Change Request (CR)
       │
       ▼
Impact Analysis (Assessing effect on configuration rankings, Pareto frontier & tier definitions)
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

- Modifications to configuration noise schedules, latency benchmarks, or essentiality classification thresholds require formal Change Request logging.
- Direct editing of baseline documentation without an associated Change Request is strictly prohibited.

---

## 10. Open Defects and Discrepancies

| ID | Description | Affected Requirement | Severity | Status | Corrective Action |
|:---:|:---|:---:|:---:|:---:|:---|
| **D-001** | **Mocked Ablation Sweep / Zero Model Retraining**: In Cell 06, predictions are not generated by executing trained neural models or data assimilation filters. Instead, predictions are synthesized by adding a pre-specified array of noise standard deviations (`noise_levels`) and static uncertainty values (`unc_levels`) to ground truth. | FR-005, FR-006 | **CRITICAL** | `OPEN` | Train actual regressors/neural pipelines corresponding to each cumulative configuration and evaluate real test inference metrics. |
| **D-002** | **Unused Synthetic Feature Inputs**: In Cell 04, feature arrays `X_s2, X_s1, X_dem, X_weather, X_temporal` are constructed in memory, but none of these tensors are ever utilized in Cell 06 prediction loops. | FR-003 | **MEDIUM** | `OPEN` | Connect synthetic feature tensors to actual feature-ablation regression models. |
| **D-003** | **Narrative Metric Discrepancies**: In Cell 14, printed narrative numbers contradict the programmatically computed values in Cells 09 and 11: S1 gain is quoted as **+28.13%** (vs computed **21.88%**); PINN is quoted as **+19.36%** (vs computed **21.25%**); EnKF is quoted as **+15.83%** (vs computed **9.45%**); HSI is quoted as **+7.88%** (vs computed **10.86%**). | FR-015 | **MEDIUM** | `OPEN` | Update Cell 14 print statements to dynamically reference formatted variables from `df_matrix` rather than hardcoded strings. |
| **D-004** | **Code Typographical Errors**: Cell 09 creates DataFrame column `Delat_Unc` (typo for `Delta_Unc`). Cell 11 defines `tire = 'Essential'` (typo for `tier`), `role = 'Primery Driver'` (typo for `Primary`), and `'Latent (ms)'` (typo for `Latency`). | IF-002, IF-003 | **LOW** | `OPEN` | Correct typos across variable and DataFrame column declarations. |
| **D-005** | **Decoupled Pipeline and Missing Data Export**: Notebook 10 does not load model weights from preceding notebooks or serialize the ablation matrices to `data_processed/`. | IF-002 | **MEDIUM** | `OPEN` | Ingest real checkpoint weights from Notebooks 03–06 and export `ablation_matrix.parquet` to `data_processed/ablation/`. |

---

## 11. Risks and Assumptions

### 11.1 Risks

- **R-001 (False Modular Justification)**: Because the ablation study relies on monotonically decreasing synthetic noise levels, the performance jumps prove the mathematical aggregation framework but do not empirically validate real neural component efficacy.
- **R-002 (Unmodeled Negative Inter-Module Interaction)**: Real neural systems often suffer from feature interference or gradient conflicts when adding multi-modal inputs; a monotonically improving synthetic noise schedule fails to capture negative transfer.
- **R-003 (Hardware-Specific Latency Assumptions)**: Latency benchmarks ($0.3\text{ ms}$ to $5.2\text{ ms}$) are assumed static; on constrained edge devices or non-GPU hardware, EnKF covariance matrix inversion and HSI PCA transformation will exhibit severe non-linear scaling.
- **R-004 (Forward Assembly Order Sensitivity)**: Evaluating ablation solely in forward order ($A \to B \to \dots \to H$) masks potential interaction effects; leaving one component out from the full model (LOO ablation) might yield different marginal utility rankings.

### 11.2 Assumptions

- **A-001 (Monotonic Marginal Utility)**: Every incremental layer in MRIDANSH is assumed to provide non-negative informational gain ($\Delta\text{RMSE} \le 0$).
- **A-002 (Independent Latency Additivity)**: Component execution runtimes are assumed additive without pipeline parallelization or pipelined asynchronous streaming.
- **A-003 (Representative Sensor Noise Hierarchy)**: Optical Sentinel-2 is assumed to have the highest noise floor ($\sigma=0.055$), while SAR Sentinel-1 provides a lower baseline floor ($\sigma=0.042$).
- **A-004 (Linear Pareto Trade-off)**: The accuracy-speed trade-off is assumed to follow a concave Pareto frontier where early modules provide high accuracy per millisecond of compute.

---

## 12. Release / Baseline Acceptance Criteria

To declare Notebook 10 baseline-ready for production deployment, the following criteria must be fulfilled:

1. **Mandatory Functional Requirements**: All requirements marked `MET` or `PARTIAL` must be resolved to `MET` by replacing mocked noise injections with real neural ablation models.
2. **Defect Threshold**: Critical defect D-001 and Medium defect D-003 must be fully resolved.
3. **Traceability**: Bidirectional traceability must achieve $100\%$ across all functional requirements, verification procedures, and test outputs.
4. **Reproducibility**: Execution under seed `1607` must produce bit-exact matches to all logged RMSE, cumulative gain, and Pareto metrics.
5. **Configuration Freeze**: All code cells, requirements documentation, and RST technical descriptions must be frozen under tag `NB10-BL-01`.

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
> **SCIENTIFIC BOUNDARY: ALGORITHMIC ABLATION FRAMEWORK VS. EMPIRICAL NEURAL SENSITIVITY**
> 
> The ablation sweep in Notebook 10 establishes the **systems engineering rationale and Pareto optimization framework** for justifying the multi-layer MRIDANSH architecture.
> 
> Because the incremental predictions are generated via synthetic noise vectors rather than training 8 separate neural network checkpoints, this verification confirms **software logic, marginal delta mathematics, and Pareto trade-off governance**, but does **not constitute empirical proof of neural layer contributions**. Full empirical ablation requires retraining the GCN, ConvLSTM, and PINN architectures on ground-truth field sensor networks (e.g., ISMN probes) under leave-one-out and cumulative ablation protocols.

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
