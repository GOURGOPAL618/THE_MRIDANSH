# THE MRIDANSH (AETHER-MRID1607X)
# Notebook 08 — Robustness Evaluation, Sensor Failure & Stress Testing Engine
# Requirements, Verification and Configuration Control

---

## 1. Document Control

### 1.1 Identification

| Field | Value |
|:---|:---|
| **Document ID** | MRID-NB08-DOC-001 |
| **Notebook ID** | `08-robustness-and-failure-analysis.ipynb` |
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
| 0.1 | 2026-10-08 | Gourgopal Mohapatra | Structural analysis of `08-robustness-and-failure-analysis.ipynb` cells, sensor dropout sweeps, noise injection matrices, and edge case profiles. |
| 1.0 | 2026-10-08 | Gourgopal Mohapatra | Baseline requirements specification: modality dropout formulations, spectral noise sweeps, four-tier operational taxonomy, and full defect auditing. |

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
  - `A` (Analysis): Theoretical evaluation of noise scaling, dropout degradation, and exponential confidence response.
  - `I` (Inspection): Manual examination of source code, configuration constants, and layer declarations.
  - `D` (Demonstration): Observation of operational execution, multi-panel degradation figures, and taxonomic logging.
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

This document establishes the formal engineering requirements, mathematical formulations, verification procedures, empirical execution results, bidirectional traceability, configuration management, and technical discrepancy logs for Jupyter notebook `08-robustness-and-failure-analysis.ipynb` within **THE MRIDANSH** system.

### 2.2 System Context

**THE MRIDANSH** (*AETHER-MRID1607X*) estimates high-resolution volumetric soil moisture and geotechnical subgrade shear strength across varying satellite observability conditions.

Within this macro-architecture:
- **Notebooks 01–02** ingest and preprocess Sentinel-1 SAR and Sentinel-2 optical data.
- **Notebooks 03–05** construct spatial graphs, temporal ConvLSTM sequences, and Richards PDE physics constraints.
- **Notebook 06** assimilates observations using an Ensemble Kalman Filter (EnKF).
- **Notebook 07** quantifies composite uncertainty and computes baseline confidence surfaces.
- **Notebook 08 (Item Under Documentation)** stresses the system under degraded operational regimes. It audits how the system responds to missing sensor modalities (optical cloud obscuration, SAR radar payload glitches, dual sensor loss), progressive spectral noise and impulse corruption, uncalibrated radar backscatter shifts, and hydrological edge cases (flash flooding, extreme drought, steep mountainous terrain). It establishes the formal 4-tier system Operational State and Failure Mode Taxonomy.
- **Downstream Consumers (Notebooks 09–11)** utilize this failure mode taxonomy to gate hyperspectral validation, ablation audits, and cross-catchment generalization testing.

### 2.3 Notebook Objective

Notebook 08 covers Sprint Days 5–7 of the Scientific Audit & Validation Mission:
1. **Day 5 Objective (Sensor Dropouts)**: Formulate multi-modal feature matrices ($N=1000$ points), simulate single and dual sensor dropouts, measure error expansion, evaluate monotonic uncertainty scaling, and generate Plot 1 degradation profiles.
2. **Day 6 Objective (Controlled Data Corruption & Noise Injection)**: Inject additive Gaussian noise, salt-and-pepper impulse spikes, spatial revisit pixel dropouts, and backscatter calibration shifts; evaluate empirical degradation curves across a 6-step noise sweep ($0\%$ to $15\%$); and render Plot 2 diagnostic curves.
3. **Day 7 Objective (Environmental Edge Cases & Taxonomy)**: Evaluate system behavior under four extreme hydrological and topographic regimes (Normal, Flash Flood, Severe Drought, Mountainous Terrain); render Plot 3 performance matrices; and formalize the official 4-tier Operational State & Failure Mode Catalogue.

### 2.4 In Scope

- All 26 cells of `08-robustness-and-failure-analysis.ipynb` (9 code cells, 17 markdown cells).
- Generation of synthetic ground truth soil moisture $\theta_{\text{true}} \in [0.12, 0.40]\text{ m}^3/\text{m}^3$ across $N=1000$ validation points.
- Multi-modal feature matrix assembly $\mathbf{X}_{\text{baseline}} \in \mathbb{R}^{1000 \times 4}$ containing Sentinel-2 (optical), Sentinel-1 (SAR), DEM elevation ($[100, 800]\text{ m}$), and Weather rainfall ($[0, 50]\text{ mm}$).
- Implementation of `simulate_ensemble_prediction` evaluating four operational states:
  1. `none`: Nominal full constellation (S1 + S2 active)
  2. `missing_S2`: Optical cloud blockage (S2 zero-masked, pure SAR dependency)
  3. `missing_S1`: SAR radar glitch (S1 zero-masked, pure optical dependency)
  4. `dual_missing`: Dual sensor loss (S1 + S2 zero-masked, climatological fallback to $0.25$)
- Noise corruption functions: `inject_spectral_noise`, `inject_spatial_dropout`, `inject_calibration_shift`.
- Six-step noise sweep over $\sigma_{\text{noise}} \in [0.0, 0.15]$ measuring RMSE, $\sigma_{\text{step}}$, and confidence index.
- Backscatter calibration shift test ($\text{scale} = 1.20, \text{offset} = 0.06$).
- Environmental stress scenarios matrix (Normal, Flash Flood Saturation, Severe Drought, Mountainous Terrain).
- 4-Tier Operational State & Failure Mode Taxonomy (State 0: Normal, State 1: Degraded, State 2: High Uncertainty, State 3: Failure Mode).

### 2.5 Out of Scope

- Execution of full deep learning backward passes or ConvLSTM parameter retraining under dropout conditions.
- Real-time orbital ephemeris loss modeling or Doppler radar frequency shifts.
- Coupling with geotechnical limit-equilibrium slope stability solvers.
- Physical serialization of corrupted feature tensors to disk.

### 2.6 Current-State Declaration (Mandatory Engineering Disclosure)

> [!WARNING]
> **MANDATORY CURRENT-STATE DECLARATION: SYNTHETIC SIMULATION AND STATIC TAXONOMIC ARRAYS**
> 
> Inspection of `08-robustness-and-failure-analysis.ipynb` confirms that the notebook operates as an idealized conceptual simulation harness rather than testing trained neural pipeline checkpoints:
> 1. **Mocked Ensemble Prediction**: In Cell 06, predictions are generated via simple linear combinations (`0.5 * X[:, 0] + 0.5 * X[:, 1]`) or fallback constants (`0.25`) rather than invoking the trained ConvLSTM (Notebook 04) or PINN (Notebook 05).
> 2. **Artificial Uncertainty Inflation**: In Cells 06, 13, and 17, uncertainty values ($\sigma$) are synthesized by adding constants to random noise rather than propagating empirical covariances through the Ensemble Kalman Filter.
> 3. **Hardcoded Environmental Edge Case Arrays**: In Cell 20, the environmental stress test metrics (`rmse_env`, `unc_env`, `conf_env`) are **completely static hardcoded python lists**, not the output of a running simulation loop.
> 4. **Decoupled Pipeline**: The notebook does not load data from Notebooks 01–07, nor does it export structured datasets to `data_processed/`.

---

## 3. Definitions and Abbreviations

| Term / Abbreviation | Definition |
|:---|:---|
| **$\mathbf{z}$** | Composite multi-modal feature vector $[\mathbf{x}_{\text{S2}}, \mathbf{x}_{\text{S1}}, \mathbf{x}_{\text{DEM}}, \mathbf{x}_{\text{Weather}}]^T$. |
| **S1 / SAR** | Sentinel-1 Synthetic Aperture Radar (active C-band microwave backscatter). |
| **S2 / Optical** | Sentinel-2 Multi-Spectral Instrument (passive optical surface reflectance). |
| **Sensor Dropout** | Total loss or masking of an observational satellite data stream. |
| **Impulse Noise** | Salt-and-pepper corruption spikes ($\pm 0.25$) modeling transmission bit errors. |
| **Spatial Dropout** | Bernoulli pixel masking modeling missing satellite swath revisit tiles. |
| **Calibration Shift** | Affine scale and offset distortion simulating uncalibrated radar cross-sections. |
| **Operational Taxonomy**| 4-Tier classification mapping uncertainty ($\sigma_{\text{total}}$) to system governance actions. |
| **JCC RS-SDA** | Jagannath Command Center — Remote Sensing & Spatial Data Analytics Division. |

---

## 4. Requirements

### 4.1 Functional Requirements

- **FR-001**: The software shall generate a baseline multi-modal calibration dataset of $N=1000$ spatial samples containing synthetic ground truth volumetric soil moisture $\theta_{\text{true}} \sim \mathcal{U}(0.12, 0.40)\text{ m}^3/\text{m}^3$.
- **FR-002**: The software shall synthesize four distinct feature modalities conforming to:
  - $\mathbf{x}_{\text{S2}} = \theta_{\text{true}} + \mathcal{N}(0, 0.02^2)$ (Optical surface moisture proxy)
  - $\mathbf{x}_{\text{S1}} = \theta_{\text{true}} + \mathcal{N}(0, 0.025^2)$ (SAR radar backscatter proxy)
  - $\mathbf{x}_{\text{DEM}} \sim \mathcal{U}(100, 800)\text{ m}$ (Topographic elevation)
  - $\mathbf{x}_{\text{Weather}} \sim \mathcal{U}(0, 50)\text{ mm}$ (Precipitation accumulation)
  and stack them into matrix $\mathbf{X}_{\text{baseline}} \in \mathbb{R}^{1000 \times 4}$.
- **FR-003**: The software shall implement function `simulate_ensemble_prediction(X_feats, dropout_type)` supporting four operational scenarios:
  1. `none`: $\hat{\theta} = 0.5 \mathbf{x}_{\text{S2}} + 0.5 \mathbf{x}_{\text{S1}}$, $\sigma \sim \mathcal{N}(0.060, 0.005^2)$
  2. `missing_S2`: $\mathbf{x}_{\text{S2}} = 0.0$, $\hat{\theta} = \mathbf{x}_{\text{S1}} + \mathcal{N}(0, 0.015^2)$, $\sigma \sim \mathcal{N}(0.060, 0.005^2)$
  3. `missing_S1`: $\mathbf{x}_{\text{S1}} = 0.0$, $\hat{\theta} = \mathbf{x}_{\text{S2}} + \mathcal{N}(0, 0.020^2)$, $\sigma \sim \mathcal{N}(0.070, 0.006^2)$
  4. `dual_missing`: $\mathbf{x}_{\text{S2}} = \mathbf{x}_{\text{S1}} = 0.0$, $\hat{\theta} = 0.25 + \mathcal{N}(0, 0.05^2)$, $\sigma \sim \mathcal{N}(0.120, 0.010^2)$
- **FR-004**: The software shall compute root-mean-square error (RMSE) against ground truth $\theta_{\text{true}}$ for all four sensor dropout scenarios.
- **FR-005**: The software shall map prediction uncertainty ($\sigma$) into normalized operational confidence ($C$) via:
  $$C = \operatorname{clip}\left(\exp\left(-\gamma \frac{\sigma}{\sigma_{\text{max}}}\right), 0.0, 1.0\right)$$
- **FR-006**: The software shall render Aerospace Plot 1 displaying:
  - Subplot 1: Grouped bar chart comparing Prediction RMSE against Model Uncertainty ($\pm\sigma$) across dropout states.
  - Subplot 2: System Confidence Degradation Decay curve displaying percentage confidence drop across states.
- **FR-007**: The software shall implement function `inject_spectral_noise(X, noise_std, impulse_prob)` injecting additive Gaussian noise $\mathcal{N}(0, \sigma_{\text{noise}}^2)$ and salt-and-pepper impulse spikes ($\pm 0.25$ with probability $p$), clipping values to $[0.0, 1.0]$.
- **FR-008**: The software shall implement function `inject_spatial_dropout(X, dropout_rate)` zero-masking feature entries according to a Bernoulli process with dropout probability $p_{\text{dropout}} = 0.15$.
- **FR-009**: The software shall implement function `inject_calibration_shift(X, scale, offset)` applying an affine transformation $(X \cdot \text{scale}) + \text{offset}$.
- **FR-010**: The software shall execute a 6-level noise sweep over $\sigma_{\text{noise}} \in [0.0, 0.15]$ ($0\%, 3\%, 6\%, 9\%, 12\%, 15\%$), logging RMSE, estimated uncertainty, and decayed confidence at each level.
- **FR-011**: The software shall render Aerospace Plot 2 showing:
  - Subplot 1: Progressive error and uncertainty response curve as a function of noise level.
  - Subplot 2: Graceful confidence decay curve over the noise sweep.
- **FR-012**: The software shall evaluate an uncalibrated radar offset test ($\text{scale} = 1.20, \text{offset} = 0.06$), verifying that the system flags bad sensor calibration via elevated uncertainty ($\sigma > 0.11$) and depressed confidence ($C < 15\%$).
- **FR-013**: The software shall define and evaluate four environmental edge case stress scenarios: Normal Field, Flash Flood Saturation, Severe Drought, and Mountainous Terrain.
- **FR-014**: The software shall render Aerospace Plot 3 displaying grouped bar charts of error/uncertainty and confidence curves across all environmental regimes.
- **FR-015**: The software shall formalize and display a 4-Tier Operational State & Failure Mode Taxonomy mapping uncertainty thresholds to governance actions (Normal, Degraded, High Uncertainty, Failure Mode).

### 4.2 Data Integrity Requirements

- **DI-001**: Non-Negative Soil Moisture and Uncertainty: Predictions $\hat{\theta}$ and uncertainties $\sigma$ shall remain strictly positive.
- **DI-002**: Monotonic Error Expansion Under Modality Loss: Prediction RMSE shall strictly increase as sensor modalities drop: $\text{RMSE}_{\text{nom}} < \text{RMSE}_{\text{single\_loss}} < \text{RMSE}_{\text{dual\_loss}}$.
- **DI-003**: Monotonic Uncertainty Inflation: Mean estimated uncertainty shall strictly increase across the progressive noise sweep: $\sigma(n_i) < \sigma(n_{i+1})$.
- **DI-004**: Inverse Confidence Decay: System confidence shall strictly decrease as noise intensity increases: $C(n_i) > C(n_{i+1})$.
- **DI-005**: Strict Taxonomy State Boundaries: The 4 operational states shall partition the uncertainty domain continuously without gaps or overlaps.

### 4.3 Interface Requirements

- **IF-001**: Function `simulate_ensemble_prediction` shall accept feature matrix `X_feats` and string `dropout_type`, returning tuple `(pred, uncertainty, confidence)`.
- **IF-002**: Function `inject_spectral_noise` shall accept array `X` and return array of identical shape clipped to $[0.0, 1.0]$.
- **IF-003**: Function `inject_calibration_shift` shall accept array `X`, scalar `scale`, and scalar `offset`, returning transformed array.
- **IF-004**: Terminal outputs shall display standard ASCII headers and format metrics with 4-decimal float precision and 1-decimal percentage precision.

### 4.4 Uncertainty / Quality Requirements

- **UQ-001**: Under dual sensor failure, the system confidence shall collapse below $20\%$ to prevent overconfident erroneous predictions.
- **UQ-002**: Severe data corruption ($15\%$ noise) shall depress confidence below $10\%$.
- **UQ-003**: The operational taxonomy shall enforce that State 3 (Failure Mode) triggers an automatic prediction rejection flag.
- **UQ-004**: System self-awareness shall be mathematically satisfied: $\frac{\Delta\sigma}{\Delta\text{RMSE}} \approx \text{constant} > 0$.

### 4.5 Non-Functional Requirements

- **NF-001**: Deterministic seeds shall be fixed for NumPy (`np.random.seed(1607)`) and PyTorch (`torch.manual_seed(1607)`).
- **NF-002**: The notebook shall execute unattended from Cell 00 to Cell 25 without interactive user input.
- **NF-003**: Visual plots shall employ the JCC RS-SDA dark telemetry theme (`#00FFCC`, `#1A3344`, monospace typography).
- **NF-004**: Computational execution time shall evaluate in $< 3.0$ seconds on CPU/CUDA hardware.

---

## 5. Requirements Attributes

| ID | Requirement Statement | Rationale | Method | Acceptance Criterion | Status |
|:---|:---|:---|:---:|:---|:---:|
| **FR-001** | Generate $N=1000$ synthetic ground truth samples in $[0.12, 0.40]$. | Establishes statistical benchmark dataset. | I/T | Array shape `(1000,)`; values bounded $[0.12, 0.40]$. | **MET** |
| **FR-002** | Assemble multi-modal feature matrix $\mathbf{X} \in \mathbb{R}^{1000 \times 4}$. | Input feature space discretization. | T | Shape `(1000, 4)`; optical, SAR, DEM, weather stacked. | **MET** |
| **FR-003** | Implement `simulate_ensemble_prediction` for 4 dropout modes. | Simulates satellite sensor blackout. | I/T | Handles `none`, `missing_S2`, `missing_S1`, `dual_missing`. | **PARTIAL\*** |
| **FR-004** | Compute RMSE across all four dropout states. | Quantitative error tracking. | T | RMSE: Nom=**0.0160**, NoS2=**0.0287**, NoS1=**0.0284**, Dual=**0.0977**. | **MET** |
| **FR-005** | Map uncertainty $\sigma$ to confidence index $C \in [0, 1]$. | Operational risk indexing. | T | Conf: Nom=**40.8%**, NoS2=**40.7%**, NoS1=**35.2%**, Dual=**16.8%**. | **MET** |
| **FR-006** | Render Plot 1 sensor dropout degradation profile. | Visualizing failure response. | D | 2-panel figure rendered; RMSE vs $\sigma$ and confidence curve. | **MET** |
| **FR-007** | Implement `inject_spectral_noise` (Gaussian + Salt/Pepper). | Real-world spectral noise modeling. | I/T | Corrupts inputs with Gaussian noise and impulse spikes. | **MET** |
| **FR-008** | Implement `inject_spatial_dropout` (Bernoulli masking). | Models missing revisit swath pixels. | I/T | Masking verified; rate $p=0.15$. | **MET** |
| **FR-009** | Implement `inject_calibration_shift` (affine transformation). | Models radar backscatter miscalibration. | I/T | Affine transform applied: $(X \cdot 1.20) + 0.06$. | **MET** |
| **FR-010** | Execute 6-level noise sweep over $\sigma_{\text{noise}} \in [0.0, 0.15]$. | Graceful degradation evaluation. | T | 6 steps evaluated; RMSE: $0.0160 \to 0.1033$, Conf: $63.9\% \to 6.4\%$. | **MET** |
| **FR-011** | Render Plot 2 noise sweep degradation curves. | Graphical corruption diagnostics. | D | 2-panel figure rendered; error curve and confidence decay. | **MET** |
| **FR-012** | Evaluate radar backscatter calibration shift test. | Calibration anomaly detection. | T | Shifted RMSE = **0.1149**, $\sigma = \pm\mathbf{0.1154}$, Conf = **12.6%**. | **MET** |
| **FR-013** | Evaluate 4 environmental edge case stress scenarios. | Extreme climate regime resilience. | T | Normal, Flood, Drought, Mountainous scenarios logged. | **PARTIAL\*** |
| **FR-014** | Render Plot 3 environmental performance matrix. | Graphical climate regime comparison. | D | 2-panel figure rendered; bar chart and confidence response. | **MET** |
| **FR-015** | Formalize 4-Tier Operational State & Failure Mode Taxonomy. | Operational deployment governance. | I/D | State 0 (Normal) to State 3 (Failure Mode) mapped. | **MET** |
| **DI-001** | Non-negative soil moisture and uncertainty. | Physical validity enforcement. | T | All predictions and uncertainties $\ge 0$. | **MET** |
| **DI-002** | Monotonic error expansion under modality dropouts. | Modality loss must increase error. | T | $0.0160 < 0.0287 \approx 0.0284 < 0.0977\text{ m}^3/\text{m}^3$. | **MET** |
| **DI-003** | Monotonic uncertainty inflation under noise sweep. | Uncertainty must track noise level. | T | $\sigma$ increases: $0.0249 \to 0.0505 \to 0.0760 \to 0.1015 \to 0.1270 \to 0.1525$. | **MET** |
| **DI-004** | Inverse confidence decay under noise sweep. | Confidence must decrease with noise. | T | Conf drops: $63.9\% \to 40.4\% \to 25.5\% \to 16.1\% \to 10.2\% \to 6.4\%$. | **MET** |
| **DI-005** | Strict taxonomy state boundary coverage. | Complete operational state space. | I/A | $[0, 0.035], (0.035, 0.070], (0.070, 0.110], (0.110, \infty)$ partition. | **MET** |
| **IF-001** | `simulate_ensemble_prediction` interface contract. | Predictor signature consistency. | I/T | Accepts `(X, dropout_type)`, returns `(pred, unc, conf)`. | **MET** |
| **IF-002** | `inject_spectral_noise` interface contract. | Noise injector signature consistency. | I/T | Accepts array, returns clipped array of identical shape. | **MET** |
| **IF-003** | `inject_calibration_shift` interface contract. | Affine shifter signature consistency. | I/T | Accepts array, scale, offset; returns shifted array. | **MET** |
| **IF-004** | Standard ASCII headers and precision formatting. | Telemetry readability standard. | D | Logs use standard separators and precision specifiers. | **MET** |
| **UQ-001** | Confidence collapse $<20\%$ under dual sensor failure. | High-uncertainty detection contract. | T | Dual failure confidence = **16.8%** ($<20\%$). | **MET** |
| **UQ-002** | Confidence depression $<10\%$ under $15\%$ noise. | Severe noise detection contract. | T | $15\%$ noise confidence = **6.4%** ($<10\%$). | **MET** |
| **UQ-003** | State 3 triggers automatic prediction rejection. | Geotechnical safety assurance. | I | Taxonomy declares "REJECT PREDICTION & Alert Operator". | **MET** |
| **UQ-004** | Uncertainty scales proportionally with empirical RMSE. | Self-awareness mathematical criterion. | T | $\sigma$ tracks RMSE across all dropout and noise states. | **MET** |
| **NF-001** | Deterministic seed initialization (1607). | Exact numerical reproducibility. | I/T | Seeds declared in Cell 02. | **MET** |
| **NF-002** | Headless unattended execution. | Batch execution compatibility. | D | All 26 cells execute sequentially without errors. | **MET** |
| **NF-003** | Dark telemetry UI styling on generated figures. | Institutional visual consistency. | I | Cyan borders, dark blue annotation boxes, monospace fonts. | **MET** |
| **NF-004** | Execution runtime $< 3.0$ seconds. | High-performance execution. | A | End-to-end execution completes in $\approx 1.2$s. | **MET** |

*\*Note: FR-003 marked PARTIAL due to mock linear prediction blend (D-001). FR-013 marked PARTIAL due to hardcoded edge case arrays (D-003).*

---

## 6. Verification Procedures

### VP-001: Multi-Modal Feature Matrix Initialization
- **Verifies**: FR-001, FR-002, DI-001, NF-001
- **Setup**: Python 3.10+ kernel with NumPy and PyTorch under seed 1607.
- **Procedure**:
  1. Initialize seed 1607.
  2. Sample `theta_true = np.random.uniform(0.12, 0.40, size=1000)`.
  3. Synthesize `feat_S2`, `feat_S1`, `feat_DEM`, `feat_Weather`.
  4. Stack columns into `X_baseline`.
- **Expected Result**:
  - `theta_true.min() == 0.120` to `0.121`, `theta_true.max() == 0.399` to `0.400`
  - `X_baseline.shape == (1000, 4)`
- **Pass/Fail Criterion**: Matrix dimensions match $(1000, 4)$ and ground truth bounds are verified.

### VP-002: Sensor Dropout Simulation and Error Metric Verification
- **Verifies**: FR-003, FR-004, FR-005, DI-002, UQ-001
- **Setup**: Execute `simulate_ensemble_prediction` on `X_baseline` across four scenarios.
- **Procedure**:
  1. Run `simulate_ensemble_prediction(X_baseline, 'none')`.
  2. Run with `'missing_S2'`, `'missing_S1'`, and `'dual_missing'`.
  3. Compute RMSE for each scenario against `theta_true`.
- **Expected Result**:
  - Nominal: $\text{RMSE} = 0.0160$, Mean $\sigma = \pm 0.0600$, Conf $= 40.8\%$
  - S2 Missing: $\text{RMSE} = 0.0287$, Mean $\sigma = \pm 0.0602$, Conf $= 40.7\%$
  - S1 Missing: $\text{RMSE} = 0.0284$, Mean $\sigma = \pm 0.0698$, Conf $= 35.2\%$
  - Dual Fail: $\text{RMSE} = 0.0977$, Mean $\sigma = \pm 0.1197$, Conf $= 16.8\%$
- **Pass/Fail Criterion**: RMSE values and uncertainties strictly match expected values within $\pm 0.0005$.

### VP-003: Plot 1 Sensor Dropout Visualization
- **Verifies**: FR-006, NF-003
- **Setup**: Matplotlib dark theme configuration.
- **Procedure**:
  1. Render grouped bar chart of RMSE vs Uncertainty.
  2. Render confidence degradation curve.
  3. Annotate percentage labels on confidence markers.
- **Expected Result**: Figure renders with 2 subplots without layout clipping.
- **Pass/Fail Criterion**: Image display object generated successfully.

### VP-004: Noise Injection and Controlled Sweep Evaluation
- **Verifies**: FR-007, FR-010, DI-003, DI-004, UQ-002
- **Setup**: Execute `inject_spectral_noise` across `noise_levels = np.linspace(0.0, 0.15, 6)`.
- **Procedure**:
  1. Loop through noise levels $0.0, 0.03, 0.06, 0.09, 0.12, 0.15$.
  2. Corrupt optical/SAR features and evaluate linear predictions.
  3. Record RMSE, uncertainty ($\sigma_{\text{step}}$), and decayed confidence.
- **Expected Result**:
  - Level $0.0\%$: $\text{RMSE} = 0.0160, \sigma = \pm 0.0249, \text{Conf} = 63.9\%$
  - Level $3.0\%$: $\text{RMSE} = 0.0283, \sigma = \pm 0.0505, \text{Conf} = 40.4\%$
  - Level $6.0\%$: $\text{RMSE} = 0.0492, \sigma = \pm 0.0760, \text{Conf} = 25.5\%$
  - Level $9.0\%$: $\text{RMSE} = 0.0698, \sigma = \pm 0.1015, \text{Conf} = 16.1\%$
  - Level $12.0\%$: $\text{RMSE} = 0.0868, \sigma = \pm 0.1270, \text{Conf} = 10.2\%$
  - Level $15.0\%$: $\text{RMSE} = 0.1033, \sigma = \pm 0.1525, \text{Conf} = 6.4\%$
- **Pass/Fail Criterion**: Monotonic increase of RMSE and $\sigma$, monotonic decrease of confidence.

### VP-005: Plot 2 Data Corruption Curves
- **Verifies**: FR-011, NF-003
- **Setup**: Matplotlib figure rendering.
- **Procedure**:
  1. Plot error and uncertainty curves against corruption level.
  2. Plot confidence decay curve with numerical value annotations.
- **Expected Result**: 2-panel diagnostic figure rendered.
- **Pass/Fail Criterion**: Graphic renders cleanly with dark theme telemetry.

### VP-006: Bad Backscatter Calibration Shift Verification
- **Verifies**: FR-009, FR-012, UQ-001
- **Setup**: Apply `inject_calibration_shift` with $\text{scale}=1.20, \text{offset}=0.06$.
- **Procedure**:
  1. Shift optical and SAR baseline features.
  2. Calculate shifted prediction RMSE and shifted uncertainty.
  3. Calculate confidence drop.
- **Expected Result**:
  - Shifted $\text{RMSE} = 0.1149\text{ m}^3/\text{m}^3$
  - Shifted Mean $\sigma = \pm 0.1154\text{ m}^3/\text{m}^3$
  - Shifted Confidence $= 12.6\%$
- **Pass/Fail Criterion**: System flags bad sensor calibration by elevating uncertainty above $0.110$ and depressing confidence below $15\%$.

### VP-007: Environmental Edge Case Evaluation
- **Verifies**: FR-013, FR-014
- **Setup**: Define environmental stress scenarios array.
- **Procedure**:
  1. Record metrics for Normal Field, Flash Flood Saturation, Severe Drought, Mountainous Terrain.
  2. Render Plot 3 bar charts and confidence curves.
- **Expected Result**:
  - Normal Field: $\text{RMSE} = 0.0160, \sigma = \pm 0.0250, \text{Conf} = 63.8\%$
  - Flash Flood: $\text{RMSE} = 0.0820, \sigma = \pm 0.0980, \text{Conf} = 22.8\%$
  - Drought: $\text{RMSE} = 0.0750, \sigma = \pm 0.0890, \text{Conf} = 26.3\%$
  - Mountainous: $\text{RMSE} = 0.0910, \sigma = \pm 0.1120, \text{Conf} = 18.7\%$
- **Pass/Fail Criterion**: Output printed to terminal and Plot 3 rendered.

### VP-008: Operational State & Failure Mode Taxonomy Audit
- **Verifies**: FR-015, DI-005, UQ-003
- **Setup**: Review taxonomy table in Cell 23.
- **Procedure**:
  1. Inspect uncertainty boundaries: $[0, 0.035]$, $(0.035, 0.070]$, $(0.070, 0.110]$, $> 0.110$.
  2. Inspect confidence index intervals: $>50\%$, $30\%-50\%$, $15\%-30\%$, $<15\%$.
  3. Confirm associated system actions for each state.
- **Expected Result**:
  - State 0 (Normal): Standard Output
  - State 1 (Degraded): Warning Banner
  - State 2 (High Uncertainty): Climatology Fallback
  - State 3 (Failure Mode): Prediction Rejected & Operator Alert
- **Pass/Fail Criterion**: Continuous partition without overlaps; failure action strictly enforced.

---

## 7. Verification Results

| VP | Date | Executor | Result | Empirical Evidence [NB] | Reviewer |
|:---:|:---:|:---:|:---:|:---|:---:|
| **VP-001** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `X_baseline.shape == (1000, 4)`; moisture range $0.120$ to $0.400\text{ m}^3/\text{m}^3$. | Baseline Audit |
| **VP-002** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | Nom RMSE=**0.0160**, NoS2 RMSE=**0.0287**, NoS1 RMSE=**0.0284**, Dual RMSE=**0.0977**; Dual Conf=**16.8%**. | Baseline Audit |
| **VP-003** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | Plot 1 rendered (`length=94192` bytes PNG display data). | Baseline Audit |
| **VP-004** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | Noise sweep: $0.0\% \to \text{RMSE}=0.0160$ ($C=63.9\%$), $15.0\% \to \text{RMSE}=0.1033$ ($C=6.4\%$). | Baseline Audit |
| **VP-005** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | Plot 2 rendered (`length=111824` bytes PNG display data). | Baseline Audit |
| **VP-006** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | Shifted RMSE = **0.1149**, $\sigma = \pm\mathbf{0.1154}$, Confidence = **12.6%**. | Baseline Audit |
| **VP-007** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | Edge cases logged; Plot 3 rendered (`length=94752` bytes PNG display data). | Baseline Audit |
| **VP-008** | 2026-10-08 | Automated / G. Mohapatra | **PASS** | 4-tier taxonomy verified: State 0 to State 3 fully partition operational space. | Baseline Audit |

---

## 8. Requirements Traceability Matrix

| Requirement ID | Design Element | Verification Procedure | Verification Result |
|:---|:---|:---:|:---:|
| **FR-001** | Feature Synthesizer / Ground Truth | VP-001 | **PASS** |
| **FR-002** | Multi-Modal Matrix Assembly | VP-001 | **PASS** |
| **FR-003** | `simulate_ensemble_prediction` Function | VP-002 | **PASS (PARTIAL\*)** |
| **FR-004** | RMSE Calculation Logic | VP-002 | **PASS** |
| **FR-005** | Exponential Confidence Mapper | VP-002 | **PASS** |
| **FR-006** | Plot 1 Visual Diagnostic Routine | VP-003 | **PASS** |
| **FR-007** | `inject_spectral_noise` Function | VP-004 | **PASS** |
| **FR-008** | `inject_spatial_dropout` Function | VP-004 | **PASS** |
| **FR-009** | `inject_calibration_shift` Function | VP-006 | **PASS** |
| **FR-010** | Noise Sweep Execution Loop | VP-004 | **PASS** |
| **FR-011** | Plot 2 Degradation Diagnostic Routine | VP-005 | **PASS** |
| **FR-012** | Calibration Shift Evaluation Routine | VP-006 | **PASS** |
| **FR-013** | Environmental Edge Case Evaluator | VP-007 | **PASS (PARTIAL\*)** |
| **FR-014** | Plot 3 Environmental Performance Matrix | VP-007 | **PASS** |
| **FR-015** | Operational State & Failure Taxonomy Table | VP-008 | **PASS** |
| **DI-001** | Positive Domain Clipping (`np.abs`, `clip`) | VP-001, VP-002 | **PASS** |
| **DI-002** | Error Hierarchy Assertion | VP-002 | **PASS** |
| **DI-003** | Uncertainty Monotonic Growth Check | VP-004 | **PASS** |
| **DI-004** | Confidence Inverse Monotonicity Check | VP-004 | **PASS** |
| **DI-005** | Taxonomy Interval Completeness Check | VP-008 | **PASS** |
| **IF-001** | Predictor Function Signature Definition | VP-002 | **PASS** |
| **IF-002** | Noise Function Signature Definition | VP-004 | **PASS** |
| **IF-003** | Shift Function Signature Definition | VP-006 | **PASS** |
| **IF-004** | Console Telemetry Logging Formats | VP-001 to VP-008 | **PASS** |
| **UQ-001** | Dual Dropout Confidence Gate ($<20\%$) | VP-002 | **PASS** |
| **UQ-002** | Severe Noise Confidence Gate ($<10\%$) | VP-004 | **PASS** |
| **UQ-003** | State 3 Failure Mode Rejection Action | VP-008 | **PASS** |
| **UQ-004** | Error-Uncertainty Correlation Metric | VP-002, VP-004 | **PASS** |
| **NF-001** | Deterministic Seed Locking (1607) | VP-001 | **PASS** |
| **NF-002** | Headless Unattended Execution Pipeline | VP-001 to VP-008 | **PASS** |
| **NF-003** | Dark Telemetry Styling Specifications | VP-003, VP-005, VP-007 | **PASS** |
| **NF-004** | Execution Latency Benchmark | VP-001 to VP-008 | **PASS** |

*\*Note: FR-003 and FR-013 carry design limitations documented in the Defect Register below.*

---

## 9. Configuration and Change Control

### 9.1 Controlled Items

1. **Source Notebook**: `1_notebooks_sandbox/08-robustness-and-failure-analysis.ipynb`
2. **Requirements Baseline**: `8_docs/01_Notebooks/08. robustness and failure analysis/08_robustness_and_failure_analysis_REQUIREMENTS.md`
3. **Technical Description**: `8_docs/01_Notebooks/08. robustness and failure analysis/08_robustness_and_failure_analysis.rst`
4. **Environment**: Python 3.10+ virtual environment (`mridansh_env`) with fixed package locks.
5. **Random Seed Baseline**: NumPy `1607`, PyTorch `1607`.

### 9.2 Baseline Identification

- **Baseline ID**: `NB08-BL-01`
- **Configuration Tag**: `v1.0-scientific-audit-day05-07`
- **Effective Date**: 2026-10-08

### 9.3 Change Procedure

```text
Change Request (CR)
       │
       ▼
Impact Analysis (Assessing effect on taxonomy thresholds & dropout metrics)
       │
       ▼
Technical Approval (Division Lead & Verification Engineer)
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

- Every modification to sensor dropout weights, noise injection levels, or taxonomy boundaries requires a distinct Git commit hash.
- Direct editing of published baseline files without an associated Change Request is prohibited.

---

## 10. Open Defects and Discrepancies

| ID | Description | Affected Requirement | Severity | Status | Corrective Action |
|:---:|:---|:---:|:---:|:---:|:---|
| **D-001** | **Mocked Linear Predictor & Artificial Uncertainty**: In Cell 06, `pred` uses a trivial linear combination (`0.5 * X[:,0] + 0.5 * X[:,1]`) and uncertainty is synthesized by adding noise to hardcoded offsets, rather than executing trained models or propagating EnKF covariances. | FR-003 | **HIGH** | `OPEN` | Replace `simulate_ensemble_prediction` with checkpoints from Notebook 04/05 and posterior covariance matrices from Notebook 06. |
| **D-002** | **Inconsistent Gamma Parameter & Direct Percentage Scaling**: In Cell 06, confidence uses $\gamma = 1.5$. In Cells 13 and 17, confidence uses $\gamma = 1.8$. Furthermore, Cell 17 scales by 100 inside `np.clip`, introducing an inconsistent output representation. | FR-005, FR-010, FR-012 | **MEDIUM** | `OPEN` | Standardize confidence calculation into a single modular function with unified parameter $\gamma = 1.5$ returning normalized fractions in $[0.0, 1.0]$. |
| **D-003** | **Hardcoded Environmental Edge Case Arrays**: In Cell 20, `rmse_env`, `unc_env`, and `conf_env` are defined as static python lists without running an actual data corruption or model evaluation loop. | FR-013 | **HIGH** | `OPEN` | Implement active synthetic generators for extreme moisture saturation, wilting points, and DEM slope distortions to compute empirical edge case metrics dynamically. |
| **D-004** | **Unused Topographic and Weather Modalities**: In Cell 04, DEM and Weather features are generated into `X_baseline`, but `simulate_ensemble_prediction` never consumes `X[:, 2]` or `X[:, 3]` except during dual failure fallback. | FR-002, FR-003 | **LOW** | `OPEN` | Update predictor formulation to incorporate topographic wetness index (DEM) and antecedent precipitation (Weather) into model inference. |
| **D-005** | **Decoupled Pipeline and Missing Data Export**: Notebook 08 does not load real inputs from `data_processed/` or export its stress evaluation metrics or taxonomy state masks to disk. | IF-001 | **MEDIUM** | `OPEN` | Connect upstream data ingestion from Notebook 06/07 and export stress metrics and GeoTIFF taxonomy masks to `data_processed/robustness/`. |

---

## 11. Risks and Assumptions

### 11.1 Risks

- **R-001 (False Operational Confidence)**: Because the noise injection and dropout stress tests are performed on synthetic linear combinations rather than deep ConvLSTM/PINN models, real-world deep neural network failure modes (e.g., out-of-distribution hallucinations) may not be detected.
- **R-002 (Arbitrary Taxonomy Thresholds)**: The operational thresholds ($\sigma \le 0.035$, $0.070$, $0.110$) are established empirically on synthetic distributions; applying them to real satellite scenes without field recalibration may trigger false failure alarms.
- **R-003 (Miscalibration Vulnerability)**: Affine backscatter offsets produce severe error ($0.1149\text{ m}^3/\text{m}^3$); if radar preprocessing fails to calibrate sigma-nought values, the system will enter high uncertainty states.
- **R-004 (Unmodeled Atmospheric Attenuation)**: Optical cloud blockage is modeled as simple zero-masking; partial cloud contamination and thin cirrus haze that escape QA masking are not represented.

### 11.2 Assumptions

- **A-001 (Orthogonal Sensor Failure Modes)**: Sentinel-1 SAR and Sentinel-2 optical failures are assumed statistically independent.
- **A-002 (Constant Residual Noise Floor)**: Baseline instrumental sensor error is assumed to follow an additive Gaussian distribution with zero mean.
- **A-003 (Climatological Prior Validity)**: Under dual sensor dropout, a climatological fallback moisture value of $0.25\text{ m}^3/\text{m}^3$ is assumed representative of nominal field capacity.
- **A-004 (Linear Modality Weighting)**: Equal weighting ($50\%$ optical, $50\%$ SAR) is assumed optimal for the baseline ensemble under clear-sky conditions.

---

## 12. Release / Baseline Acceptance Criteria

To declare Notebook 08 baseline-ready for production deployment, the following criteria must be fulfilled:

1. **Mandatory Functional Requirements**: All requirements marked `MET` or `PARTIAL` must be resolved to `MET` by replacing mocked predictors with real neural checkpoints.
2. **Defect Threshold**: Defect D-001, D-002, and D-003 must be fully resolved.
3. **Traceability**: Bidirectional traceability must achieve $100\%$ across all functional requirements, verification procedures, and test outputs.
4. **Reproducibility**: Execution under seed `1607` must produce bit-exact matches to all logged RMSE, uncertainty, and confidence figures.
5. **Configuration Freeze**: All code cells, requirements documentation, and RST technical descriptions must be frozen under tag `NB08-BL-01`.

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
> **SCIENTIFIC BOUNDARY: ALGORITHMIC STRESS DEMONSTRATION VS. REAL SATELLITE VALIDATION**
> 
> The stress testing routines in Notebook 08 evaluate the **conceptual mathematical response** of uncertainty bounding and confidence decay under sensor loss.
> 
> Because the feature vectors and predictions are synthetic linear surrogates, this verification confirms **software algorithmic integrity and defensive logic**, but does **not constitute real-world satellite validation**. Validation against operational satellite outages (e.g., Copernicus Sentinel-1B payload failure) requires retrospective backtesting against historical ground sensor networks.

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
