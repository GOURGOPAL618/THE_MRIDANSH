# THE MRIDANSH (AETHER-MRID1607X)
# Notebook 06 — Sequential Soil-State Estimation (EnKF Assimilation)
# Requirements, Verification and Configuration Control

---

## 1. Document Control

### 1.1 Identification

| Field | Value |
|:---|:---|
| **Document ID** | MRID-NB06-DOC-001 |
| **Notebook ID** | `06-state-estimation.ipynb` |
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
| 0.1 | 2026-10-08 | Gourgopal Mohapatra | Structural reverse-engineering of `06-state-estimation.ipynb`, covariance matrices, Kalman gains, and assimilation trajectories. |
| 1.0 | 2026-10-08 | Gourgopal Mohapatra | Baseline requirements specification: atomic filtering requirements, empirical verification cases, discrepancy audit, and bidirectional traceability matrix. |

### 1.3 Document Conventions

- **SHALL** indicates a mandatory, verifiable, and binding engineering requirement.
- **SHOULD** indicates a recommended design practice or optimization target.
- **MAY** indicates an optional or alternative implementation path.
- **Requirement Status Definitions**:
  - `MET`: Requirement verified by execution against empirical output evidence.
  - `PARTIAL`: Implementation exists but carries software defects, narrative discrepancies, or unhandled edge cases.
  - `NOT MET`: Requirement is absent, failing verification, or contradicted by runtime evidence.
  - `WAIVED`: Formal departure accepted with recorded technical rationale.
- **Verification Methods**:
  - `T` (Test): Quantitative execution with test assertions and numerical threshold validation.
  - `A` (Analysis): Theoretical evaluation of covariance positive-definiteness, matrix rank, and Kalman gain stability.
  - `I` (Inspection): Manual examination of source code, configuration constants, and layer declarations.
  - `D` (Demonstration): Observation of operational execution, histogram distributions, and trajectory plots.
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

This document defines the formal software requirements, mathematical formulations, verification procedures, empirical execution results, bidirectional traceability, configuration management, and technical discrepancy logs for Jupyter notebook `06-state-estimation.ipynb` within the **THE MRIDANSH** system.

### 2.2 System Context

**THE MRIDANSH** (*AETHER-MRID1607X*) generates depth-resolved soil moisture and geotechnical shear strength by fusing spaceborne Earth Observation (EO) data with physical governing laws.

Within this macro-architecture:
- **Notebooks 03 & 04** generate spatial graph representations and temporal ConvLSTM sequence forecasts.
- **Notebook 05** enforces Richards PDE conservation and van Genuchten soil water retention physics.
- **Notebook 06 (Item Under Documentation)** acts as the sequential data assimilation engine. It integrates forward prior model predictions with noisy satellite observations using an Ensemble Kalman Filter (EnKF) to compute optimal posterior soil states, error covariance matrices ($\mathbf{P}^a$), and cross-variable state updates across root-zone moisture, bulk density, saturated hydraulic conductivity, and soil organic carbon.
- **Downstream Consumers (Notebooks 07–11)** utilize these assimilated posterior distributions to conduct uncertainty quantification, failure risk analysis, and generalization evaluations.

### 2.3 Notebook Objective

Notebook 06 executes Sprint Days 1–2 of the Scientific Audit & Validation Mission:
1. **Day 1 Objective**: Define target soil state vectors and physical clipping bounds, generate synthetically cross-correlated prior ensembles ($N=50$), implement the Monte Carlo EnKF update equations (mean, anomalies, forecast covariance $\mathbf{P}^f$, innovation covariance $\mathbf{S}$, Kalman gain $\mathbf{K}$, perturbed observations $\mathbf{Y}$, and posterior covariance $\mathbf{P}^a$), and execute single-step assimilation.
2. **Day 2 Objective**: Execute multi-timestep sequential assimilation over a 14-step temporal horizon, benchmark EnKF against unconstrained forward model drift, conduct an observation noise sensitivity sweep across $R \in [10^{-4}, 10^{-1}]$, and compile the final deliverable state uncertainty reduction profile.

### 2.4 In Scope

- All 20 cells of `06-state-estimation.ipynb` (9 code cells, 11 markdown cells).
- Definition of target state vector parameters (`theta_root`, `bulk_density`, `K_sat`, `SOC`).
- Construction of cross-variable prior correlation matrix ($4 \times 4$) and multivariate normal sampling ($N=50$ members).
- Mathematical implementation of the stochastic perturbed-observation Ensemble Kalman Filter algorithm.
- Formulation of observation operator matrix $\mathbf{H} = [1, 0, 0, 0]$ and observation error covariance $\mathbf{R} = [[0.0009]]$.
- 14-timestep sequential trajectory tracking comparing pure model prediction against EnKF assimilation.
- Observation noise variance sensitivity sweep across $R \in [10^{-4}, 10^{-1}]$ (10 logarithmic points).
- Compilation of the deliverable summary DataFrame logging prior/posterior means, standard deviations, and percentage uncertainty reductions.
- Rendering of 3 diagnostic aerospace visual figures.

### 2.5 Out of Scope

- Spatially distributed 2D/3D EnKF assimilation (the filter evaluates a lumped 4-variable column state vector).
- Localized Kalman Filtering or covariance inflation techniques.
- Live satellite ingestion from Sentinel-1 STAC feeds (evaluates synthetic observations).
- Geotechnical slope stability factor of safety evaluation (deferred to downstream modules).

### 2.6 Current-State Declaration (Mandatory Engineering Disclosure)

> [!WARNING]
> **MANDATORY CURRENT-STATE DECLARATION: SYNTHETIC ENSEMBLE AND LUMPED STATE SPACE**
> 
> Notebook 06 operates purely on a lumped 4-dimensional state vector $\mathbf{x} = [\theta_{\text{root}}, \rho_b, K_{\text{sat}}, \text{SOC}]^T$ representing a 0-dimensional point column, completely decoupled from the $20 \times 20$ spatial grid of Notebook 03 and the 5D sequence tensors of Notebook 04. 
> 
> Prior ensembles ($N=50$) and observation timelines (14 steps) are generated in-memory using pseudorandom multivariate distributions under seed 1607. Consequently, the filter demonstrates **mathematical EnKF mechanics, Kalman gain dynamics, and covariance contraction**, but does **not** ingest live Earth Observation data.

---

## 3. Definitions and Abbreviations

| Term / Abbreviation | Definition |
|:---|:---|
| **EnKF** | Ensemble Kalman Filter (Monte Carlo implementation of the Kalman filter for high-dimensional non-linear systems). |
| **$\mathbf{x}$** | State vector: $[\theta_{\text{root}}, \text{bulk\_density}, K_{\text{sat}}, \text{SOC}]^T \in \mathbb{R}^4$. |
| **$N$** | Number of ensemble members ($N = 50$). |
| **$\mathbf{X}^f$** | Prior / Forecast state ensemble matrix $\in \mathbb{R}^{4 \times 50}$. |
| **$\mathbf{X}^a$** | Posterior / Analysis state ensemble matrix $\in \mathbb{R}^{4 \times 50}$. |
| **$\mathbf{P}^f$** | Prior sample error covariance matrix $\in \mathbb{R}^{4 \times 4}$. |
| **$\mathbf{P}^a$** | Posterior sample error covariance matrix $\in \mathbb{R}^{4 \times 4}$. |
| **$\mathbf{H}$** | Observation forward operator mapping state space to measurement space $\in \mathbb{R}^{1 \times 4}$. |
| **$\mathbf{R}$** | Observation error covariance matrix $\in \mathbb{R}^{1 \times 1}$. |
| **$\mathbf{K}$** | Kalman Gain matrix $\in \mathbb{R}^{4 \times 1}$. |
| **$\mathbf{S}$** | Innovation covariance matrix: $\mathbf{S} = \mathbf{H} \mathbf{P}^f \mathbf{H}^T + \mathbf{R}$. |
| **JCC RS-SDA** | Jagannath Command Center — Remote Sensing & Spatial Data Analytics Division. |

---

## 4. Requirements

### 4.1 Functional Requirements

- **FR-001**: The software shall define a 4-dimensional target soil state vector declaring nominal mean, standard deviation, physical minimum, physical maximum, and units for:
  - `theta_root`: Root-Zone Volumetric Moisture ($0.28 \pm 0.04\text{ m}^3/\text{m}^3$, range $[0.05, 0.45]$)
  - `bulk_density`: Dry Soil Bulk Density ($1.35 \pm 0.08\text{ g/cm}^3$, range $[1.00, 1.80]$)
  - `K_sat`: Saturated Hydraulic Conductivity ($2.50 \pm 0.60\text{ cm/hr}$, range $[0.01, 10.0]$)
  - `SOC`: Soil Organic Carbon ($1.20 \pm 0.25\%$, range $[0.10, 4.00]$)
- **FR-002**: The software shall construct a $4 \times 4$ cross-variable correlation matrix $\mathbf{R}_{\text{corr}}$ reflecting documented physical soil relationships:
  - $\operatorname{corr}(\theta, \rho_b) = -0.30$
  - $\operatorname{corr}(\theta, K_{\text{sat}}) = 0.40$
  - $\operatorname{corr}(\theta, \text{SOC}) = 0.20$
  - $\operatorname{corr}(\rho_b, K_{\text{sat}}) = -0.50$
  - $\operatorname{corr}(\rho_b, \text{SOC}) = -0.65$
  - $\operatorname{corr}(K_{\text{sat}}, \text{SOC}) = 0.35$
- **FR-003**: The software shall generate prior ensemble matrix $\mathbf{X}^f \in \mathbb{R}^{4 \times 50}$ by sampling from $\mathcal{N}(\boldsymbol{\mu}, \mathbf{\Sigma})$ where $\mathbf{\Sigma} = \mathbf{D} \mathbf{R}_{\text{corr}} \mathbf{D}$ and $\mathbf{D} = \operatorname{diag}(\boldsymbol{\sigma})$, followed by element-wise clipping to $[\min_i, \max_i]$.
- **FR-004**: The software shall implement the stochastic perturbed-observation EnKF update algorithm (`run_enkf_update`):
  1. Ensemble mean: $\bar{\mathbf{x}} = \frac{1}{N} \sum_{i=1}^N \mathbf{x}_i$
  2. Ensemble anomalies: $\mathbf{A} = \mathbf{X} - \bar{\mathbf{x}}\mathbf{1}^T$
  3. Prior sample covariance: $\mathbf{P}^f = \frac{1}{N-1}\mathbf{A}\mathbf{A}^T$
  4. Innovation covariance: $\mathbf{S} = \mathbf{H}\mathbf{P}^f\mathbf{H}^T + \mathbf{R}$
  5. Kalman gain: $\mathbf{K} = \mathbf{P}^f\mathbf{H}^T \mathbf{S}^{-1}$
  6. Perturbed measurements: $\mathbf{y}_i = \mathbf{y} + \boldsymbol{\epsilon}_i, \boldsymbol{\epsilon}_i \sim \mathcal{N}(\mathbf{0}, \mathbf{R})$
  7. Analysis update: $\mathbf{X}^a = \mathbf{X}^f + \mathbf{K}(\mathbf{Y}_{\text{pert}} - \mathbf{H}\mathbf{X}^f)$
  8. Posterior sample covariance: $\mathbf{P}^a = \frac{1}{N-1}\mathbf{A}^a (\mathbf{A}^a)^T$
- **FR-005**: The software shall execute a single-step assimilation update with observation $y = 0.34\text{ m}^3/\text{m}^3$, variance $R = 0.0009$, and operator $\mathbf{H} = [1.0, 0.0, 0.0, 0.0]$, logging prior mean, posterior mean, and Kalman gains.
- **FR-006**: The software shall render Aerospace Plot 1 displaying prior vs posterior ensemble probability density histograms across all 4 state variables.
- **FR-007**: The software shall execute a 14-timestep sequential assimilation trajectory comparing:
  - Pure unconstrained forward prediction subject to model drift: $\mathbf{x}_{t+1} = \mathbf{x}_t + \mathbf{d} + \mathcal{N}(\mathbf{0}, \mathbf{Q})$
  - Sequential EnKF assimilation tracking noisy observation sequence $y_t$.
- **FR-008**: The software shall calculate Root Mean Squared Error (RMSE) against true reference state $x_{\text{true}} = 0.50\text{ m}^3/\text{m}^3$ for both pure prediction and EnKF assimilation, computing percentage error reduction.
- **FR-009**: The software shall render Aerospace Plot 2 showing dynamic trajectories of model prediction, observations, EnKF posterior estimates, and posterior uncertainty bands.
- **FR-010**: The software shall execute an observation noise sensitivity sweep across 10 logarithmic points $R \in [10^{-4}, 10^{-1}]$ and render Aerospace Plot 3 showing posterior absolute error as a function of observation noise variance.
- **FR-011**: The software shall assemble and format a deliverable summary table reporting prior mean $\pm$ std, posterior mean $\pm$ std, and percentage uncertainty reduction across all 4 state variables.

### 4.2 Data Integrity Requirements

- **DI-001**: Prior error covariance $\mathbf{P}^f$ and posterior error covariance $\mathbf{P}^a$ shall be strictly symmetric ($\mathbf{P} = \mathbf{P}^T$) and positive semi-definite ($\lambda_i \ge 0$).
- **DI-002**: Filter Variance Contraction: Posterior variance shall be strictly less than or equal to prior variance for directly observed states ($\mathbf{P}^a_{00} \le \mathbf{P}^f_{00}$).
- **DI-003**: Cross-Variable State Update: The Kalman gain on unobserved variables shall be non-zero when cross-covariances are non-zero ($K_i \ne 0$ for $\operatorname{cov}(x_0, x_i) \ne 0$).
- **DI-004**: Physical Bounds Enforcement: All initial prior ensemble members shall strictly lie within the physical boundaries declared in `STATE_VARIABLES`.
- **DI-005**: Matrix Invertibility: The innovation covariance matrix $\mathbf{S}$ shall have full rank ($\det(\mathbf{S}) \ne 0$) to guarantee numeric invertibility.

### 4.3 Interface Requirements

- **IF-001**: Function `run_enkf_update` shall accept inputs `(X_prior, obs_vector, obs_cov, H_operator)` and return tuple `(X_posterior, P_f, P_a, K, innovation)`.
- **IF-002**: State ensemble matrices shall maintain shape $(4, 50)$ across all filtering iterations.
- **IF-003**: Output deliverable table shall export a formatted pandas DataFrame containing columns: `'State Variable'`, `'Unit'`, `'Prior Mean ± Std'`, `'Posterior Mean ± Std'`, and `'Uncertainty Reduction (%)'`.

### 4.4 Uncertainty / Quality Requirements

- **UQ-001**: Measurement perturbation sampling shall use the exact observation error covariance $\mathbf{R}$ to prevent underestimation of posterior ensemble spread.
- **UQ-002**: Unbiased sample covariance normalization shall divide by $N - 1$ ($49$ for $N = 50$) rather than $N$.
- **UQ-003**: In-graph telemetry boxes shall display empirical RMSE values and percentage error reduction to at least 4 decimal places.

### 4.5 Non-Functional Requirements

- **NF-001**: Deterministic seeds shall be fixed for NumPy (`np.random.seed(1607)`) and PyTorch (`torch.manual_seed(1607)`).
- **NF-002**: The notebook shall execute unattended from Cell 00 to Cell 19 without manual intervention.
- **NF-003**: All diagnostic figures shall apply the project dark telemetry theme (`#00FFCC` borders, `#1A3344` grids, monospace fonts).
- **NF-004**: Execution memory footprint shall not exceed 150 MB RAM.

---

## 5. Requirements Attributes

| ID | Requirement Statement | Rationale | Method | Acceptance Criterion | Status |
|:---|:---|:---|:---:|:---|:---:|
| **FR-001** | Define 4D target state vector parameters. | Soil state space parameterization. | I | Dictionary declared with 4 state variables. | **MET** |
| **FR-002** | Define $4 \times 4$ cross-variable correlation matrix. | Physically coupled state dependencies. | I | Correlation matrix defined; symmetric, unit diagonal. | **MET** |
| **FR-003** | Generate prior ensemble matrix $\mathbf{X}^f \in \mathbb{R}^{4 \times 50}$. | Monte Carlo state distribution representation. | T | Ensemble shape $(4, 50)$; bounds respected. | **MET** |
| **FR-004** | Implement perturbed-observation EnKF algorithm. | Core data assimilation algorithm. | T | `run_enkf_update` returns analysis states and gains. | **MET** |
| **FR-005** | Single-step assimilation with $y = 0.34$. | Single-observation benchmark update. | T | Posterior theta equals **0.3231**, gain equals **0.6885**. | **MET** |
| **FR-006** | Render Plot 1 prior vs posterior distributions. | Statistical distribution auditing. | D | 4-panel histogram figure rendered. | **MET** |
| **FR-007** | 14-timestep sequential assimilation trajectory. | Dynamic temporal filtering validation. | T | 14 timesteps evaluated for prediction and EnKF. | **MET** |
| **FR-008** | Compute prediction vs EnKF RMSE and reduction. | Quantify assimilation accuracy gain. | T | Pred RMSE: **0.0608**, EnKF RMSE: **0.0211**, Reduction: **65.35%**. | **MET** |
| **FR-009** | Render Plot 2 dynamic state trajectories. | Visual temporal trajectory tracking. | D | Plot rendered showing forecast vs observations. | **PARTIAL\*** |
| **FR-010** | Observation noise sensitivity sweep ($10^{-4}$ to $10^{-1}$). | Filter stability analysis across sensor noise. | T | 10 variance points evaluated; Plot 3 rendered. | **MET** |
| **FR-011** | Format deliverable uncertainty reduction DataFrame. | Downstream state deliverable table. | T | Table printed logging uncertainty reductions. | **MET** |
| **DI-001** | Error covariances symmetric positive semi-definite. | Mathematical covariance matrix validity. | A/T | $\mathbf{P} = \mathbf{P}^T$, eigenvalues non-negative. | **MET** |
| **DI-002** | Posterior variance contraction ($\mathbf{P}^a_{00} \le \mathbf{P}^f_{00}$). | Information gain from observation update. | T | Prior std: $0.0441 \to$ Posterior std: $0.0239$. | **MET** |
| **DI-003** | Non-zero cross-variable Kalman updates. | Indirect cross-variable state assimilation. | T | Bulk density gain equals **-0.5142** (non-zero). | **MET** |
| **DI-004** | Prior ensemble clipping within physical limits. | Prevent physically impossible states. | T | Zero ensemble values violate min/max bounds. | **MET** |
| **DI-005** | Full rank innovation matrix $\det(\mathbf{S}) \ne 0$. | Avoid numerical singularity during matrix inversion. | A/T | $\mathbf{S} > 0$ strictly positive scalar. | **MET** |
| **IF-001** | `run_enkf_update` parameter signature and returns. | Filter interface contract. | I/T | Function accepts 4 args, returns 5 items. | **MET** |
| **IF-002** | State ensemble matrix dimension $(4, 50)$. | Consistent matrix dimension contract. | T | Shapes strictly preserved across all operations. | **MET** |
| **IF-003** | Deliverable DataFrame column schema. | Output report standardization. | T | Columns match specification exactly. | **MET** |
| **UQ-001** | Perturbed observation noise covariance matching $\mathbf{R}$. | Monte Carlo ensemble spread consistency. | T | Perturbations drawn from $\mathcal{N}(\mathbf{0}, \mathbf{R})$. | **MET** |
| **UQ-002** | Unbiased covariance denominator ($N - 1$). | Sample statistics accuracy. | I | Division by `num_members - 1` in code. | **MET** |
| **UQ-003** | Precision telemetry displays in figures. | Accuracy reporting transparency. | D | Telemetry box shows RMSE to 4 decimal places. | **MET** |
| **NF-001** | Deterministic seed initialization (1607). | Exact numerical reproducibility. | I/T | Seeds declared in Cell 02. | **MET** |
| **NF-002** | Unattended headless execution. | Batch pipeline compatibility. | D | All 20 cells execute sequentially without error. | **MET** |
| **NF-003** | Uniform dark telemetry plot styling parameters. | Enterprise visual consistency across division. | I | Theme parameters conform to standard. | **MET** |
| **NF-004** | Lightweight memory footprint (< 150 MB). | Resource compliance in container runtimes. | A | Minimal tensor footprint (< 100 KB). | **MET** |

*\*Note: FR-009 marked PARTIAL due to software defect D-001 (collapsed uncertainty ribbon in Plot 2).*

---

## 6. Verification Procedures

### VP-001: Target State Vector Definition and Parameter Inspection
- **Verifies**: FR-001
- **Setup**: Python 3.10+ kernel with NumPy.
- **Procedure**:
  1. Inspect `STATE_VARIABLES` dictionary.
  2. Verify 4 state variables: `theta_root`, `bulk_density`, `K_sat`, `SOC`.
  3. Validate nominal means, stds, and physical bounds.
- **Expected Result**: All 4 state variables defined with realistic agronomic/geotechnical limits.
- **Pass Criterion**: Zero missing keys; parameters match specification.

### VP-002: Cross-Variable Correlation Matrix Formulation
- **Verifies**: FR-002, DI-001
- **Setup**: Correlation matrix `corr_matrix` in Cell 06.
- **Procedure**:
  1. Check matrix dimensions ($4 \times 4$).
  2. Assert symmetry: $\mathbf{R}_{\text{corr}} = \mathbf{R}_{\text{corr}}^T$.
  3. Verify unit diagonal and physical cross-correlations (e.g. $\operatorname{corr}(\rho_b, \text{SOC}) = -0.65$).
- **Expected Result**: Matrix is symmetric with diagonal 1.0; off-diagonals match physical expectations.
- **Pass Criterion**: Symmetric, positive definite matrix.

### VP-003: Correlated Prior Ensemble Generation and Clipping
- **Verifies**: FR-003, DI-004
- **Setup**: Function `generate_prior_ensemble(num_members=50)` under seed 1607.
- **Procedure**:
  1. Generate ensemble matrix $\mathbf{X}^f$.
  2. Compute ensemble mean and std for `theta_root`.
  3. Assert all members satisfy $\min_i \le x_{ij} \le \max_i$.
- **Expected Result**: Matrix shape $(4, 50)$; Mean $\theta = \mathbf{0.2829}\text{ m}^3/\text{m}^3$, Std $\theta = \mathbf{0.0441}\text{ m}^3/\text{m}^3$. Zero boundary violations.
- **Pass Criterion**: Exact shape $(4, 50)$, logged statistics match baseline.

### VP-004: EnKF Update Operator Mechanics and Gain Validation
- **Verifies**: FR-004, FR-005, DI-002, DI-003, DI-005, IF-001
- **Setup**: Prior ensemble $\mathbf{X}^f$, observation $y = [0.34]$, $R = [[0.0009]]$, $\mathbf{H} = [[1.0, 0.0, 0.0, 0.0]]$.
- **Procedure**:
  1. Execute `run_enkf_update(X_prior, obs_val, R_obs, H_mat)`.
  2. Validate Kalman gain $\mathbf{K}$ on moisture ($K_0$) and bulk density ($K_1$).
  3. Inspect posterior mean and standard deviation.
- **Expected Result**:
  - Prior Theta: $0.2829 \pm 0.0441$
  - Posterior Theta: **0.3231** $\pm$ **0.0239**
  - Kalman Gain on Theta: **0.6885**
  - Kalman Gain on Bulk Density: **-0.5142**
- **Pass Criterion**: Moisture standard deviation contracts from $0.0441 \to 0.0239$; negative bulk density gain verified.

### VP-005: Aerospace Plot 1 Prior vs Posterior Histograms
- **Verifies**: FR-006, NF-003, D
- **Setup**: Prior ensemble $\mathbf{X}^f$ and posterior ensemble $\mathbf{X}^a$.
- **Procedure**:
  1. Render $2 \times 2$ histogram grid comparing prior (orange) and posterior (cyan) distributions.
  2. Verify mean vertical lines and observation reference line on Subplot 0.
- **Expected Result**: 4 subplots rendered with density histograms and legends.
- **Pass Criterion**: Figure displayed successfully without layout clipping.

### VP-006: 14-Step Sequential Trajectory Tracking
- **Verifies**: FR-007, FR-008
- **Setup**: True state $x_{\text{true}} = [0.5, 1.30, 2.80, 1.45]$, 14 timesteps, model drift $\mathbf{d} = [0.002, -0.001, 0.01, 0.005]^T$.
- **Procedure**:
  1. Execute 14-step loop tracking pure prediction vs sequential EnKF updates.
  2. Compute RMSE for pure prediction and EnKF posterior against true state $0.5000$.
- **Expected Result**:
  - True State: **0.5000 m$^3$/m$^3$**
  - Pure Prediction RMSE: **0.0608 m$^3$/m$^3$**
  - EnKF Assimilation RMSE: **0.0211 m$^3$/m$^3$**
  - Error Reduction: **65.35%**
- **Pass Criterion**: Empirical values match logged run outputs under seed 1607.

### VP-007: Aerospace Plot 2 Dynamic Trajectory Rendering
- **Verifies**: FR-009, NF-003, D
- **Setup**: Trajectory arrays `traj_pure_pred`, `traj_enkf_post`, `traj_enkf_std`.
- **Procedure**:
  1. Render time-series plot comparing predictions, observations, and EnKF estimates.
  2. Inspect posterior uncertainty band fill.
- **Expected Result**: Trajectories plotted; in-graph telemetry box displayed.
- **Pass Criterion**: Audit records defect D-001 (collapsed uncertainty band due to duplicate argument and mean instead of std).

### VP-008: Observation Noise Sensitivity Sweep
- **Verifies**: FR-010
- **Setup**: 10 observation error variances $R \in [10^{-4}, 10^{-1}]$ (log-spaced).
- **Procedure**:
  1. Execute EnKF update for each variance and record posterior absolute error.
  2. Render semi-log sensitivity curve.
- **Expected Result**: Posterior error increases monotonically as observation noise variance $R$ increases.
- **Pass Criterion**: Monotonic error trajectory verified; Plot 3 displayed.

### VP-009: Deliverable Uncertainty Reduction Profile Table
- **Verifies**: FR-011, IF-003
- **Setup**: Format final summary deliverable DataFrame.
- **Procedure**:
  1. Compute prior and posterior mean $\pm$ std for all 4 state variables.
  2. Compute percentage uncertainty reduction: $\frac{\sigma_{\text{prior}} - \sigma_{\text{post}}}{\sigma_{\text{prior}}} \times 100\%$.
- **Expected Result**:
  - Root-Zone Moisture: $0.2829 \pm 0.0441 \to 0.3231 \pm 0.0239$ (**45.9% reduction**)
  - Bulk Density: $1.3656 \pm 0.0937 \to 1.3356 \pm 0.0899$ (**4.0% reduction**)
  - Hydraulic Conductivity: $2.4070 \pm 0.6501 \to 2.6507 \pm 0.5855$ (**9.9% reduction**)
  - Soil Organic Carbon: $1.2015 \pm 0.2358 \to 1.2657 \pm 0.2275$ (**3.5% reduction**)
- **Pass Criterion**: Values match printed terminal table exactly.

### VP-010: Error Covariance Matrix Properties
- **Verifies**: DI-001, DI-005
- **Setup**: Prior covariance $\mathbf{P}^f$ and posterior covariance $\mathbf{P}^a$.
- **Procedure**:
  1. Assert symmetry: $\mathbf{P} = \mathbf{P}^T$.
  2. Calculate eigenvalues of $\mathbf{P}^f$ and $\mathbf{P}^a$.
- **Expected Result**: Both matrices symmetric; all eigenvalues strictly positive.
- **Pass Criterion**: Symmetric, positive definite covariance matrices.

### VP-011: Cross-Variable Kalman Gain Validation
- **Verifies**: DI-003
- **Setup**: Kalman gain matrix $\mathbf{K} \in \mathbb{R}^{4 \times 1}$.
- **Procedure**:
  1. Verify sign of Kalman gain on Bulk Density: $K_1 = -0.5142$.
  2. Explain negative sign: negative cross-correlation $\operatorname{corr}(\theta, \rho_b) = -0.30$.
- **Expected Result**: Gain on bulk density is negative; wetter observed soil decreases estimated bulk density.
- **Pass Criterion**: Physical cross-variable coupling verified.

### VP-012: Deterministic Reproducibility
- **Verifies**: NF-001, NF-002
- **Setup**: Clean environment under seed 1607.
- **Procedure**:
  1. Re-run notebook cells sequentially.
  2. Verify identical Kalman gains, posterior means, and RMSE metrics.
- **Expected Result**: Bit-identical output values.
- **Pass Criterion**: Numerical metrics reproduce exactly.

---

## 7. Verification Results

Evidence tags:
- **`[NB]`**: Directly extracted from cell execution outputs in `06-state-estimation.ipynb`.
- **`[AN]`**: Independently re-calculated numerical verification.
- **`[INS]`**: Source code and parameter inspection.

| VP ID | Verification Target | Execution Date | Executor | Result | Empirical Evidence & Numerical Values | Reviewer |
|:---|:---|:---:|:---:|:---:|:---|:---:|
| **VP-001** | State Vector Parameters | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 04: Target parameters declared for all 4 states (`theta_root`, `bulk_density`, `K_sat`, `SOC`). | *Pending* |
| **VP-002** | Correlation Matrix | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[INS]` Cell 06: Symmetric $4 \times 4$ matrix with physical cross-correlations. | *Pending* |
| **VP-003** | Prior Ensemble Sampling | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 06: Shape $(4, 50)$, Mean $\theta = \mathbf{0.2829}$, Std $\theta = \mathbf{0.0441}$. | *Pending* |
| **VP-004** | EnKF Update Operator | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 08: Post Mean $\theta = \mathbf{0.3231}$ (Std: **0.0239**), Gain on $\theta = \mathbf{0.6885}$, Gain on $\rho_b = \mathbf{-0.5142}$. | *Pending* |
| **VP-005** | Plot 1 Distribution Histograms | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 10: PNG rendered (length: 154,100 bytes). Prior vs posterior densities displayed. | *Pending* |
| **VP-006** | 14-Step Assimilation Tracking | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 12: True Theta: **0.5000**, Pred RMSE: **0.0608**, EnKF RMSE: **0.0211**, Error Reduction: **65.35%**. | *Pending* |
| **VP-007** | Plot 2 Trajectory Rendering | 2026-10-08 | Automated / G. Mohapatra | **FAIL\*** | `[NB]` Cell 14: PNG rendered (83,320 bytes). \*Defect D-001: Uncertainty ribbon collapsed due to code bug. | *Pending* |
| **VP-008** | Observation Noise Sensitivity | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 16: Sweep completed across 10 points; PNG rendered (58,576 bytes). | *Pending* |
| **VP-009** | Uncertainty Reduction Profile | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 18: Moisture reduction: **45.9%**, Density: **4.0%**, Conductivity: **9.9%**, SOC: **3.5%**. | *Pending* |
| **VP-010** | Error Covariance Validity | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[AN]` $\mathbf{P}^f$ and $\mathbf{P}^a$ are symmetric positive definite. | *Pending* |
| **VP-011** | Cross-Variable Kalman Gain | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 08: Gain on Density = **-0.5142**, correctly reflecting negative cross-correlation. | *Pending* |
| **VP-012** | Deterministic Reproducibility | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Bit-identical outputs verified across runs under seed 1607. | *Pending* |

---

## 8. Requirements Traceability Matrix

```
Requirement (Section 4)
       │
       ▼
Software Design & Code Cell (Notebook Implementation)
       │
       ▼
Verification Procedure (Section 6)
       │
       ▼
Verification Result & Empirical Evidence (Section 7)
```

| Requirement ID | Design Implementation Element | Code Cell | Verification Procedure | Verification Result |
|:---|:---|:---:|:---:|:---:|
| **FR-001** | State vector parameter dictionary definition | Cell 04 | VP-001 | **PASS** |
| **FR-002** | Cross-variable correlation matrix formulation | Cell 06 | VP-002 | **PASS** |
| **FR-003** | Multivariate normal prior ensemble generation | Cell 06 | VP-003 | **PASS** |
| **FR-004** | Stochastic perturbed-observation EnKF algorithm | Cell 08 | VP-004 | **PASS** |
| **FR-005** | Single-step assimilation with $y=0.34$ | Cell 08 | VP-004 | **PASS** |
| **FR-006** | Aerospace Plot 1 ensemble distribution rendering | Cell 10 | VP-005 | **PASS** |
| **FR-007** | 14-timestep sequential trajectory tracking | Cell 12 | VP-006 | **PASS** |
| **FR-008** | Prediction vs EnKF RMSE and reduction calculation | Cell 12 | VP-006 | **PASS** |
| **FR-009** | Aerospace Plot 2 dynamic trajectory rendering | Cell 14 | VP-007 | **PARTIAL\*** |
| **FR-010** | Observation noise variance sensitivity sweep | Cell 16 | VP-008 | **PASS** |
| **FR-011** | Deliverable summary table compilation | Cell 18 | VP-009 | **PASS** |
| **DI-001** | Prior/posterior covariance positive-definiteness | Cell 08 | VP-010 | **PASS** |
| **DI-002** | Observation update variance contraction | Cell 08 | VP-004 | **PASS** |
| **DI-003** | Non-zero cross-variable Kalman gain update | Cell 08 | VP-011 | **PASS** |
| **DI-004** | Physical state boundary clipping | Cell 06 | VP-003 | **PASS** |
| **DI-005** | Invertible innovation covariance matrix $\mathbf{S}$ | Cell 08 | VP-010 | **PASS** |
| **IF-001** | `run_enkf_update` argument and return contract | Cell 08 | VP-004 | **PASS** |
| **IF-002** | Ensemble matrix dimension contract $(4, 50)$ | Cells 06, 08 | VP-003, VP-004 | **PASS** |
| **IF-003** | Deliverable DataFrame column structure | Cell 18 | VP-009 | **PASS** |
| **UQ-001** | Observation noise covariance matching $\mathbf{R}$ | Cell 08 | VP-004 | **PASS** |
| **UQ-002** | Unbiased sample covariance normalization ($N-1$) | Cell 08 | VP-010 | **PASS** |
| **UQ-003** | High-precision metric reporting in figures | Cells 12, 14 | VP-006, VP-007 | **PASS** |
| **NF-001** | Deterministic seed initialization (1607) | Cell 02 | VP-012 | **PASS** |
| **NF-002** | Unattended headless execution | All cells | Execution Audit | **PASS** |
| **NF-003** | Dark telemetry UI styling on generated figures | Cells 02, 10, 14, 16 | VP-005, VP-007, VP-008 | **PASS** |
| **NF-004** | Lightweight memory footprint (< 150 MB) | All cells | Analysis | **PASS** |

---

## 9. Configuration and Change Control

### 9.1 Controlled Items

The following items constitute the controlled configuration baseline for Notebook 06:
1. **Source Notebook**: `1_notebooks_sandbox/06-state-estimation.ipynb` (SHA-256 baseline hash required).
2. **Requirements & Verification Document (This Document)**: `8_docs/01_Notebooks/06. state estimation/06_state_estimation_REQUIREMENTS.md`.
3. **Companion Technical Description (Pending User Call)**: `8_docs/01_Notebooks/06. state estimation/06_state_estimation.rst`.
4. **Execution Environment**: Pinned Python environment with NumPy, Pandas, Matplotlib, PyTorch.

### 9.2 Baseline Identification

- **Current Working Baseline**: `NB06-BL-01-DRAFT`
- **Target Release Baseline**: `NB06-BL-01`
- **Upstream Baseline**: `NB05-BL-01` (Physics Validation / Richards Diffusion)
- **Downstream Target Baseline**: `NB07-BL-01` (`07-uncertainty-analysis.ipynb`)

### 9.3 Change Procedure

Any modification to state variables, correlation matrices, observation operators, or EnKF formulas shall follow this control lifecycle:

```
[Change Request (CR)] 
        │
        ▼
[Impact Analysis on State Covariances & Downstream Risk Analysis] 
        │
        ▼
[Technical Review & Approval by Lead Authority] 
        │
        ▼
[Code / Documentation Modification] 
        │
        ▼
[Execution of Verification Procedures VP-001 to VP-012] 
        │
        ▼
[Traceability Matrix & Document Control Update] 
        │
        ▼
[Baseline Tag Update]
```

### 9.4 Version Control Rules

1. **Cell Integrity**: Cell outputs shall be committed matching the baseline hash or cleanly stripped before formal release.
2. **Deterministic Tensors**: Clean-kernel re-runs under seed 1607 shall produce identical posterior means ($0.3231$) and gains ($0.6885$).
3. **Requirement Atomicity**: Modifying a requirement mandates updating Sections 4, 5, 6, 7, and 8 concurrently.
4. **Deprecation**: Deprecated requirements shall be tagged `WITHDRAWN` and numerical IDs permanently reserved.

---

## 10. Open Defects and Discrepancies

| ID | Description | Affected Requirement | Severity | Status | Corrective Action |
|:---|:---|:---:|:---:|:---:|:---|
| **D-001** | **Plot 2 Collapsed Uncertainty Ribbon Bug**: In Cell 12 line 296, the script executes `traj_enkf_std.append(X_curr[0, :].mean())` (appending the mean instead of `.std()`). Then in Cell 14 lines 345–346, `fill_between` passes `traj_enkf_post - 2*traj_enkf_std` for **both** lower and upper bounds, completely collapsing the $\pm 2\sigma$ uncertainty band to a single invisible line. | FR-009, NF-003 | **CRITICAL** | **OPEN** | In Cell 12, change line 296 to `.std()`. In Cell 14, change line 346 to `traj_enkf_post + 2*traj_enkf_std`. |
| **D-002** | **Narrative Metric Discrepancy**: Cell 17 narrative summary claims "reduced background prediction drift RMSE from 0.0384 to 0.0091 (>75% reduction)", but actual Cell 12 printed execution output shows: Prediction RMSE = **0.0608**, EnKF RMSE = **0.0211**, **Error Reduction = 65.35%**. | FR-008, UQ-003 | **HIGH** | **OPEN** | Update Cell 17 narrative text to reflect the actual logged run metrics ($0.0608 \to 0.0211$, 65.35% reduction). |
| **D-003** | **Absence of State and Covariance Artifact Export**: Notebook 06 prints the deliverable DataFrame to stdout but does not save `df_deliverable.csv` or posterior covariance matrix `P_a.npy` to `/data_processed/`, preventing downstream ingestion. | IF-003 | **MEDIUM** | **OPEN** | Add explicit CSV and NumPy serialization cells exporting posterior deliverables to disk. |
| **D-004** | **Decoupled 0D Point Column State Space**: Notebook 06 runs on a lumped 4-variable state vector, completely disconnected from the $20 \times 20$ spatial grid of Notebook 03 and the 5D sequence tensors of Notebook 04. | FR-001 | **HIGH** | **OPEN** | Extend EnKF to a spatially distributed grid where state vector incorporates all spatial vertices ($N = 400 \times 4$). |
| **D-005** | **Synthetic True State Value Discrepancy**: Cell 12 defines true state root moisture $x_{\text{true}}[0] = 0.50\text{ m}^3/\text{m}^3$, which exceeds the physical maximum of sandy loam saturation ($\theta_s = 0.41$) and exceeds the declared physical limit in `STATE_VARIABLES` ($0.45$). | FR-001, DI-004 | **MEDIUM** | **OPEN** | Set $x_{\text{true}}[0] \le 0.41$ to ensure physical consistency with soil saturation limits. |

---

## 11. Risks and Assumptions

### 11.1 Technical Risks

| Risk ID | Risk Description | Severity | Likelihood | Consequence | Mitigation Strategy |
|:---|:---|:---:|:---:|:---|:---|
| **R-001** | **Filter Divergence Under Model Bias** | High | Medium | Persistent unmodeled systematic drift causes the EnKF to reject observations and diverge. | Incorporate covariance inflation or adaptive state noise estimation. |
| **R-002** | **Spurious Cross-Variable Correlations** | Moderate | High | Small ensemble size ($N=50$) induces spurious cross-covariances, corrupting unobserved variables (e.g. SOC). | Implement distance-based covariance localization or Schur product tapering. |
| **R-003** | **Ensemble Collapse / Degeneracy** | Moderate | Medium | Repeated assimilation updates with small observation variance $R$ shrink ensemble spread to near zero. | Monitor ensemble spread and inject multiplicative covariance inflation. |
| **R-004** | **Lack of Downstream Persistence** | Moderate | High | Downstream notebooks cannot load assimilated posterior states without re-running the entire notebook. | Export posterior state and covariance files to disk. |

### 11.2 Architectural Assumptions

| Assumption ID | Statement of Assumption | Rationale |
|:---|:---|:---|
| **A-001** | **Linear Gaussian Measurement Model** | Observation errors are zero-mean Gaussian distributed, and the observation operator $\mathbf{H}$ is linear. |
| **A-002** | **Zero Spatial Covariance Coupling** | The state estimation problem can be decoupled into independent local columns without horizontal cross-covariance modeling. |
| **A-003** | **Stationary Cross-Variable Covariances** | The physical correlation structure between moisture, bulk density, hydraulic conductivity, and SOC remains time-invariant. |
| **A-004** | **Uncorrelated Observation Errors** | Measurement errors between separate observation timesteps are mutually independent. |
| **A-005** | **Asymptotic Normality of State Ensembles** | A 50-member ensemble provides an adequate Monte Carlo approximation of the true non-linear error distribution. |

---

## 12. Release and Baseline Acceptance Criteria

Notebook `06-state-estimation.ipynb` shall achieve formal release baseline `NB06-BL-01` only upon meeting all of the following criteria:

1. **Requirements Verification**: All Functional (FR), Data Integrity (DI), and Interface (IF) requirements verified as **MET**.
2. **Defect Remediation**: Resolution of Defect **D-001** (Plot 2 uncertainty ribbon bug) and reconciliation of Defect **D-002** (narrative discrepancy).
3. **Artifact Persistence**: Implementation of file export saving deliverable CSV and covariance matrices to disk (satisfying Defect **D-003**).
4. **Physical State Consistency**: Correction of $x_{\text{true}}$ within soil saturation limits (Defect **D-005**).
5. **Procedure Pass Rate**: 100% of Verification Procedures executed with **PASS** status.
6. **Full Bidirectional Traceability**: 100% bidirectional traceability maintained between requirements, code cells, and verification results.
7. **Independent Technical Review**: Formal review sign-off completed by an authorized independent authority.

---

## 13. Review and Approval

| Role | Designee / Authority | Division & Facility | Signature | Date |
|:---|:---|:---|:---:|:---:|
| **Author / Developer** | Gourgopal Mohapatra | RS-SDA Division, JCC Campus 2 | *Gourgopal Mohapatra* | 2026-10-08 |
| **Independent Technical Reviewer** | *(Assigned Reviewer)* | JCC Systems Engineering | ___________________ | ___________ |
| **Lead Systems Approver** | *(Approving Authority)* | JCC Command & Control | ___________________ | ___________ |

---

## 14. Limitations and Scientific Boundaries

> [!CAUTION]
> **SEPARATION OF MONTE CARLO FILTER CONVERGENCE AND IN-SITU OBSERVATION ACCURACY**
> 
> Successful execution of the EnKF assimilation routine proves:
> 1. The stochastic ensemble Kalman gain update equations execute with numerical stability.
> 2. Posterior variance contracts appropriately (moisture uncertainty reduced by **45.9%**).
> 3. Dynamic sequential assimilation reduces tracking RMSE from **0.0608** to **0.0211 m$^3/\text{m}^3$** (a **65.35% error reduction**).
> 
> **THIS DOES NOT CONSTITUTE FIELD ACCURACY OF GROUND OBSERVATIONS.**
> 
> Because:
> - True state $x_{\text{true}}$ and synthetic observations are artificially generated.
> - The state space is a 0D point column rather than a spatially distributed 2D/3D soil grid.
> - Direct satellite radiometer brightness temperatures (SMAP / Sentinel-1 backscatter) have not been directly inverted via radiative transfer models.
> - Operational deployment requires ingesting true Sentinel-1 $\sigma^0$ observations and calibrating observation error covariance $\mathbf{R}$ against in-situ soil moisture stations.

---

## 15. Intellectual Property and Controlled Distribution

```
========================================================================================
                      JAGANNATH COMMAND CENTER (JCC HEADQUARTER)
             JCC CAMPUS 2 — REMOTE SENSING & SPATIAL DATA ANALYTICS (RS-SDA)
                           PROJECT: THE MRIDANSH (AETHER-MRID1607X)
========================================================================================
```

**Copyright © 2026 Gourgopal Mohapatra. All Rights Reserved.**

This document, the underlying software architecture, mathematical formulations, Ensemble Kalman Filter assimilation algorithms, and associated telemetry data structures constitute **proprietary intellectual property** developed under the auspices of JCC RS-SDA Division.

Unauthorized copying, distribution, decompilation, reverse engineering, dissemination, or commercial utilization—in whole or in part, in any format or medium—is strictly prohibited without prior express written authorization from the author and JCC Command Authority.

```
========================================================================================
                      CLASSIFICATION: STRICTLY PROPRIETARY & CONTROLLED
========================================================================================
```
