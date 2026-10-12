# THE MRIDANSH (AETHER-MRID1607X)
# Notebook 07 — Comprehensive Uncertainty Analysis & Calibration
# Requirements, Verification and Configuration Control

---

## 1. Document Control

### 1.1 Identification

| Field | Value |
|:---|:---|
| **Document ID** | MRID-NB07-DOC-001 |
| **Notebook ID** | `07-uncertainty-analysis.ipynb` |
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
| 0.1 | 2026-10-08 | Gourgopal Mohapatra | Structural analysis of `07-uncertainty-analysis.ipynb` cells, variance decomposition arrays, coverage metrics, and stress profiles. |
| 1.0 | 2026-10-08 | Gourgopal Mohapatra | Baseline requirements specification: orthogonal variance formulations, empirical coverage procedures, stress test verification, and full discrepancy auditing. |

### 1.3 Document Conventions

- **SHALL** indicates a mandatory, verifiable, and contractually binding engineering requirement.
- **SHOULD** indicates a recommended design practice or optimization target.
- **MAY** indicates an optional or alternative implementation path.
- **Requirement Status Definitions**:
  - `MET`: Requirement verified by execution against empirical output evidence.
  - `PARTIAL`: Implementation exists but carries software defects, circular validations, or documentation discrepancies.
  - `NOT MET`: Requirement is absent, failing verification, or contradicted by runtime evidence.
  - `WAIVED`: Formal departure accepted with recorded technical rationale.
- **Verification Methods**:
  - `T` (Test): Quantitative execution with test assertions and numerical threshold validation.
  - `A` (Analysis): Theoretical evaluation of variance additivity, Gaussian probability bounds, and exponent mapping.
  - `I` (Inspection): Manual examination of source code, configuration constants, and layer declarations.
  - `D` (Demonstration): Observation of operational execution, multi-panel heatmaps, and calibration curves.
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

This document establishes the formal engineering requirements, mathematical formulations, verification procedures, empirical execution results, bidirectional traceability, configuration management, and technical discrepancy logs for Jupyter notebook `07-uncertainty-analysis.ipynb` within the **THE MRIDANSH** system.

### 2.2 System Context

**THE MRIDANSH** (*AETHER-MRID1607X*) estimates high-resolution soil moisture and subgrade shear strength while strictly bounding predictions with rigorous, calibrated confidence metrics.

Within this macro-architecture:
- **Notebook 03** constructs spatial graph topologies.
- **Notebook 04 & 05** generate temporal ConvLSTM forecasts and Richards PDE physics constraints.
- **Notebook 06** assimilates observations using an Ensemble Kalman Filter (EnKF) to compute posterior state covariances ($\mathbf{P}^a$).
- **Notebook 07 (Item Under Documentation)** decomposes net prediction uncertainty into four orthogonal physical variance sources (ensemble spread, sensor quality, temporal revisit gaps, model physics disagreement), computes normalized spatial confidence profiles ($C \in [0, 1]$), performs Gaussian reliability coverage calibration, and conducts 14-day persistent cloud outage stress tests.
- **Downstream Consumers (Notebooks 08–11)** utilize these calibrated uncertainty bounds ($\hat{\theta} \pm \sigma_{\text{total}}$) to perform geotechnical landslide slope failure risk modeling and generalization audits.

### 2.3 Notebook Objective

Notebook 07 covers Sprint Days 3–4 of the Scientific Audit & Validation Mission:
1. **Day 3 Objective**: Generate a $50 \times 50$ spatial lattice of multi-source variance contributors ($\sigma_{\text{ens}}, \sigma_{\text{sensor}}, \sigma_{\text{gap}}, \sigma_{\text{model}}$), formulate composite quadratic variance addition, map total uncertainty into normalized confidence indices via exponential scaling, and render 6-panel decomposition heatmaps.
2. **Day 4 Objective**: Audit statistical coverage reliability against Gaussian $1\sigma / 2\sigma / 3\sigma$ theoretical confidence intervals, construct spread-skill diagrams and reliability curves, execute an extreme 14-day cloud outage sensor failure stress test, and evaluate system confidence degradation.

### 2.4 In Scope

- All 18 cells of `07-uncertainty-analysis.ipynb` (8 code cells, 10 markdown cells).
- Definition and generation of $50 \times 50$ spatial grids for four independent variance sources:
  1. Ensemble spread variance $\sigma_{\text{ens}} \in [0.01, 0.04]$
  2. Sensor noise and cloud mask variance $\sigma_{\text{sensor}}$ (incorporating a 25% binomial cloud mask and Gaussian speckle)
  3. Temporal gap penalty $\sigma_{\text{gap}} = 0.005 \cdot \exp(\Delta t / 4.0)$ over revisit delay $\Delta t \in [0, 10\text{ days}]$
  4. Model physics disagreement $\sigma_{\text{model}} \sim |\mathcal{N}(0.015, 0.008)|$
- Composite standard deviation evaluation: $\sigma_{\text{total}} = \sqrt{\sum \sigma_i^2}$.
- Exponential confidence score transformation: $C = \operatorname{clip}\left(\exp\left(-\gamma \frac{\sigma_{\text{total}}}{\sigma_{\text{max}}}\right), 0, 1\right)$ with $\gamma = 1.5, \sigma_{\text{max}} = 0.10$.
- Single-pixel diagnostic evaluation at coordinate $(x=25, y=25)$.
- Reliability coverage evaluation ($N=2500$ points) across $1\sigma$, $2\sigma$, and $3\sigma$ confidence bands.
- Spread-skill scatter plot and reliability curve rendering.
- 14-day cloud outage stress test evaluation ($\Delta t = 14\text{ days}, \sigma_{\text{sensor}} = 0.08$).

### 2.5 Out of Scope

- Epistemic deep ensemble weight uncertainty via Monte Carlo Dropout (variance is treated at the state/system level).
- Real-time cloud cover mask ingestion from live Sentinel-2 Scene Classification Layers (SCL).
- Spatially coupled error covariance matrices between adjacent pixels (operates on independent grid cells).

### 2.6 Current-State Declaration (Mandatory Engineering Disclosure)

> [!WARNING]
> **MANDATORY CURRENT-STATE DECLARATION: SYNTHETIC VARIANCE FIELDS AND CIRCULAR CALIBRATION**
> 
> Notebook 07 operates completely decoupled from preceding pipeline outputs. The ensemble variance $\sigma_{\text{ens}}$, sensor noise, temporal gaps, and model disagreements **are generated in-memory via synthetic pseudorandom distributions** (`numpy.random` seed 1607) over an unreferenced $50 \times 50$ grid, rather than ingesting $\mathbf{P}^a$ from Notebook 06 or model residuals from Notebooks 04 and 05.
> 
> Crucially, the empirical coverage validation in Step 2 evaluates mock residuals generated directly from `np.random.normal(0, predicted_sigma)`. Because the evaluation errors are artificially drawn from the exact normal distribution defined by the predicted uncertainty, the coverage metrics ($67.04\%, 95.52\%, 99.72\%$) match theoretical Gaussian percentages **by mathematical construction rather than empirical sensor validation**.

---

## 3. Definitions and Abbreviations

| Term / Abbreviation | Definition |
|:---|:---|
| **$\sigma_{\text{total}}$** | Total composite standard deviation (root-sum-squared error, units: $\text{m}^3/\text{m}^3$). |
| **$\sigma_{\text{ens}}$** | Ensemble spread standard deviation reflecting state assimilation dispersion. |
| **$\sigma_{\text{sensor}}$** | Observational sensor uncertainty comprising cloud attenuation and SAR speckle. |
| **$\sigma_{\text{gap}}$** | Temporal revisit penalty modeling exponential uncertainty growth over elapsed time $\Delta t$. |
| **$\sigma_{\text{model}}$** | Epistemic model structural disagreement between ConvLSTM sequence forecasts and PINN physics states. |
| **Confidence Score ($C$)** | Dimensionless normalized reliability index $C \in [0, 1]$ mapped via exponential decay. |
| **Spread-Skill** | Diagnostic relationship comparing predicted uncertainty spread against actual absolute residual errors. |
| **Reliability Curve** | Calibration diagram plotting theoretical nominal confidence levels against observed empirical coverage frequencies. |
| **JCC RS-SDA** | Jagannath Command Center — Remote Sensing & Spatial Data Analytics Division. |

---

## 4. Requirements

### 4.1 Functional Requirements

- **FR-001**: The software shall instantiate a 2D spatial evaluation grid of dimension $50 \times 50$ pixels ($N = 2500$ spatial samples).
- **FR-002**: The software shall generate an ensemble spread standard deviation field $\sigma_{\text{ens}}$ uniformly distributed within $[0.01, 0.04]\text{ m}^3/\text{m}^3$.
- **FR-003**: The software shall generate a sensor quality uncertainty field $\sigma_{\text{sensor}}$ incorporating:
  - Base instrumental uncertainty: $0.01\text{ m}^3/\text{m}^3$
  - Cloud cover penalty: $0.035 \times \operatorname{Bernoulli}(p = 0.25)$ (25% cloud contamination)
  - SAR speckle noise penalty: $|\mathcal{N}(0, 0.015)|$
- **FR-004**: The software shall generate a temporal revisit gap penalty field $\sigma_{\text{gap}}$ modeling latency $\Delta t \sim \mathcal{U}(0, 10\text{ days})$ via exponential growth:
  $$\sigma_{\text{gap}}(\Delta t) = 0.005 \cdot \exp\left(\frac{\Delta t}{4.0}\right)$$
- **FR-005**: The software shall generate a model physics disagreement field $\sigma_{\text{model}}$ sampled from folded normal distribution $|\mathcal{N}(0.015, 0.008)|$.
- **FR-006**: The software shall compute total composite standard deviation via quadratic variance addition:
  $$\sigma_{\text{total}} = \sqrt{\sigma_{\text{ens}}^2 + \sigma_{\text{sensor}}^2 + \sigma_{\text{gap}}^2 + \sigma_{\text{model}}^2}$$
- **FR-007**: The software shall map total composite uncertainty into a normalized Confidence Score $C \in [0.0, 1.0]$ via:
  $$C = \operatorname{clip}\left(\exp\left(-\gamma \cdot \frac{\sigma_{\text{total}}}{\sigma_{\text{max}}}\right), 0.0, 1.0\right)$$
  with decay sensitivity $\gamma = 1.5$ and physical normalization bound $\sigma_{\text{max}} = 0.10\text{ m}^3/\text{m}^3$.
- **FR-008**: The software shall log summary spatial statistics across all four variance components, composite uncertainty, and confidence scores.
- **FR-009**: The software shall render Aerospace Plot 1 displaying a $2 \times 3$ panel figure visualizing all four component fields, total composite uncertainty, and the final confidence index map.
- **FR-010**: The software shall extract and print a sample pixel deliverable profile at coordinate $(x=25, y=25)$ reporting estimated soil moisture, total uncertainty ($\pm\sigma$), and percentage confidence.
- **FR-011**: The software shall perform an empirical coverage reliability audit comparing absolute prediction residuals against $1\sigma$, $2\sigma$, and $3\sigma$ predicted uncertainty thresholds across $N=2500$ samples.
- **FR-012**: The software shall render Aerospace Plot 2 showing:
  - Subplot 1: Spread-skill scatter diagram comparing absolute residuals against predicted $\sigma_{\text{total}}$ with a 1:1 sharpness line.
  - Subplot 2: Reliability calibration curve plotting theoretical confidence levels ($10\%$ to $99\%$) against empirical coverage rates.
- **FR-013**: The software shall execute an extreme 14-day persistent cloud outage stress test scenario configuring:
  - Elevated gap penalty: $\sigma_{\text{gap}} = 0.005 \cdot \exp(14.0 / 4.0)$
  - Severe sensor noise: $\sigma_{\text{sensor}} = 0.08\text{ m}^3/\text{m}^3$ across all grid pixels
- **FR-014**: The software shall compare baseline uncertainty and confidence metrics against outage stress metrics, logging mean degradation percentages.

### 4.2 Data Integrity Requirements

- **DI-001**: Non-Negative Variance: All individual standard deviations ($\sigma_{\text{ens}}, \sigma_{\text{sensor}}, \sigma_{\text{gap}}, \sigma_{\text{model}}$) shall be strictly non-negative ($\sigma_i \ge 0$).
- **DI-002**: Monotonic Variance Addition: Total uncertainty $\sigma_{\text{total}}$ shall strictly exceed or equal any individual variance contributor ($\sigma_{\text{total}} \ge \max(\sigma_i)$).
- **DI-003**: Normalized Confidence Bounds: All confidence scores shall lie strictly within the closed interval $[0.0, 1.0]$.
- **DI-004**: Inverse Monotonicity: The confidence score shall be strictly monotonically decreasing with respect to total uncertainty ($\frac{\partial C}{\partial \sigma_{\text{total}}} < 0$).
- **DI-005**: Coverage Interval Hierarchy: Empirical coverage percentages shall strictly satisfy: $\operatorname{Cov}_{1\sigma} \le \operatorname{Cov}_{2\sigma} \le \operatorname{Cov}_{3\sigma}$.

### 4.3 Interface Requirements

- **IF-001**: Function `compute_composite_uncertainty` shall accept arguments `(sigma_ens, sigma_sensor, sigma_gap, sigma_model, gamma=1.5)` and return tuple `(sigma_total, confidence_score)`.
- **IF-002**: All generated spatial arrays shall maintain consistent 2D shape $(50, 50)$ across all pipeline operations.
- **IF-003**: In-graph telemetry overlays and terminal outputs shall format uncertainty as `±σ` and confidence as percentages.

### 4.4 Uncertainty / Quality Requirements

- **UQ-001**: Theoretical Gaussian coverage targets ($68.27\%, 95.45\%, 99.73\%$) shall be displayed alongside empirical coverage metrics.
- **UQ-002**: The physical maximum uncertainty bound $\sigma_{\text{max}} = 0.10\text{ m}^3/\text{m}^3$ shall reflect upper-limit volumetric soil moisture errors under sensor loss.
- **UQ-003**: Stress test evaluations shall demonstrate substantial confidence reduction ($C_{\text{outage}} \ll C_{\text{baseline}}$) to verify sensor loss detection.

### 4.5 Non-Functional Requirements

- **NF-001**: Deterministic seeds shall be fixed for NumPy (`np.random.seed(1607)`) and PyTorch (`torch.manual_seed(1607)`).
- **NF-002**: The notebook shall execute unattended from Cell 00 to Cell 17 without interactive prompts.
- **NF-003**: Visual plots shall employ the project dark telemetry theme (`#00FFCC` borders, `#1A3344` grids, monospace fonts).
- **NF-004**: Computational execution time shall evaluate in $< 3.0$ seconds on standard CPU hardware.

---

## 5. Requirements Attributes

| ID | Requirement Statement | Rationale | Method | Acceptance Criterion | Status |
|:---|:---|:---|:---:|:---|:---:|
| **FR-001** | Instantiate $50 \times 50$ spatial evaluation grid. | Spatial domain discretization for uncertainty mapping. | I | `GRID_SIZE = (50, 50)` declared. | **MET** |
| **FR-002** | Generate ensemble spread field $\sigma_{\text{ens}} \in [0.01, 0.04]$. | Assimilation dispersion modeling. | T | Values in $[0.01, 0.04]$; Mean = **0.0248**. | **MET** |
| **FR-003** | Generate sensor noise field $\sigma_{\text{sensor}}$ (25% cloud mask). | Remote sensing signal quality modeling. | T | Base $0.01$ + cloud + speckle; Mean = **0.0307**. | **MET** |
| **FR-004** | Generate temporal gap penalty field $\sigma_{\text{gap}}(\Delta t)$. | Satellite revisit latency error modeling. | T | Exponential growth verified; Mean = **0.0222**. | **MET** |
| **FR-005** | Generate model disagreement field $\sigma_{\text{model}}$. | Epistemic structural discrepancy modeling. | T | Folded normal samples; Mean = **0.0151**. | **MET** |
| **FR-006** | Compute composite standard deviation $\sigma_{\text{total}}$. | Quadratic variance addition law. | T | Min = **0.0197**, Max = **0.1063 m$^3/\text{m}^3$**. | **MET** |
| **FR-007** | Map $\sigma_{\text{total}}$ to Confidence Score $C \in [0, 1]$. | Standardized operational decision metric. | T | Mean = **0.4699** (Range: $[0.20, 0.74]$). | **MET** |
| **FR-008** | Log summary statistics to stdout. | Pipeline telemetry verification. | D | Terminal banner printed with exact values. | **MET** |
| **FR-009** | Render Plot 1 6-panel decomposition heatmaps. | Visual multi-source uncertainty auditing. | D | 6-panel figure rendered with colorbars. | **MET** |
| **FR-010** | Extract and print sample pixel profile at $(25, 25)$. | Point deliverable format verification. | T | Output: $0.2971 \pm 0.0731\text{ m}^3/\text{m}^3$ ($C = 33.40\%$). | **MET** |
| **FR-011** | Empirical coverage reliability audit ($1\sigma, 2\sigma, 3\sigma$). | Statistical calibration validation. | T | Cov: $1\sigma = \mathbf{67.04\%}, 2\sigma = \mathbf{95.52\%}, 3\sigma = \mathbf{99.72\%}$. | **PARTIAL\*** |
| **FR-012** | Render Plot 2 spread-skill and reliability curves. | Graphical calibration evaluation. | D | 2-panel figure rendered successfully. | **MET** |
| **FR-013** | Execute 14-day persistent cloud outage stress test. | Resilience evaluation under sensor loss. | T | Outage $\sigma_{\text{total}} = \mathbf{0.1865}$, Confidence = **6.10%**. | **MET** |
| **FR-014** | Log stress scenario comparisons. | Failure mode validation. | D | Outage degradation metrics printed to stdout. | **MET** |
| **DI-001** | Non-negative individual standard deviations. | Physical variance definition. | T | $\min(\sigma_i) \ge 0.0$ across all fields. | **MET** |
| **DI-002** | Composite standard deviation strictly dominates components. | Additivity of orthogonal variances. | T | $\sigma_{\text{total}} \ge \sigma_i$ at all pixels. | **MET** |
| **DI-003** | Confidence score strictly bounded $[0, 1]$. | Normalized probability/confidence contract. | T | $0.0 \le C \le 1.0$ strictly satisfied. | **MET** |
| **DI-004** | Inverse monotonicity of confidence score. | High uncertainty must yield low confidence. | A/T | $\frac{\partial C}{\partial \sigma} = -\frac{\gamma}{\sigma_{\text{max}}} C < 0$. | **MET** |
| **DI-005** | Strict coverage interval ordering. | Monotonic probability accumulation. | T | $67.04\% \le 95.52\% \le 99.72\%$. | **MET** |
| **IF-001** | `compute_composite_uncertainty` signature and returns. | Function interface contract. | I/T | Function accepts 5 args, returns 2 arrays. | **MET** |
| **IF-002** | Spatial array dimension consistency $(50, 50)$. | Consistent matrix interface contract. | T | All 6 spatial arrays have shape $(50, 50)$. | **MET** |
| **IF-003** | In-graph telemetry format (`±σ`, confidence %). | Reporting format standard. | D | In-graph boxes display standard notation. | **MET** |
| **UQ-001** | Theoretical vs empirical Gaussian coverage tracking. | Calibration transparency. | D | Logged: $68.27\% \to 67.04\%$, $95.45\% \to 95.52\%$. | **MET** |
| **UQ-002** | Realistic physical maximum bound $\sigma_{\text{max}} = 0.10$. | Scale normalization realism. | I | Constant declared and used in formula. | **MET** |
| **UQ-003** | Severe confidence reduction under sensor failure. | Outage detection sensitivity. | T | Confidence drops from $46.99\% \to 6.10\%$. | **MET** |
| **NF-001** | Deterministic seed initialization (1607). | Exact numerical reproducibility. | I/T | Seeds declared in Cell 02. | **MET** |
| **NF-002** | Headless unattended execution. | Automated batch pipeline compatibility. | D | All 18 cells run sequentially without error. | **MET** |
| **NF-003** | Dark telemetry UI styling on generated figures. | Enterprise visual consistency across division. | I | Cyan borders, dark blue annotation boxes. | **MET** |
| **NF-004** | Execution runtime $< 3.0$ seconds. | High-performance computational efficiency. | A | End-to-end execution completes in $\approx 1.5$s. | **MET** |

*\*Note: FR-011 marked PARTIAL due to circular validation (mock errors drawn directly from predicted sigma).*

---

## 6. Verification Procedures

### VP-001: Spatial Grid Dimension and Variance Field Initialization
- **Verifies**: FR-001, FR-002, FR-003, FR-004, FR-005, DI-001, NF-001
- **Setup**: Python 3.10+ kernel with NumPy under seed 1607.
- **Procedure**:
  1. Set `GRID_SIZE = (50, 50)`.
  2. Generate $\sigma_{\text{ens}}$, $\sigma_{\text{sensor}}$, $\sigma_{\text{gap}}$, $\sigma_{\text{model}}$.
  3. Validate mean values and non-negativity.
- **Expected Result**:
  - `sigma_ens.mean() == 0.0248`
  - `sigma_sensor.mean() == 0.0307`
  - `sigma_gap.mean() == 0.0222`
  - `sigma_model.mean() == 0.0151`
- **Pass Criterion**: Zero negative values; mean statistics match baseline under seed 1607.

### VP-002: Composite Uncertainty & Confidence Index Evaluation
- **Verifies**: FR-006, FR-007, DI-002, DI-003, DI-004, IF-001
- **Setup**: `compute_composite_uncertainty` function with $\gamma = 1.5, \sigma_{\text{max}} = 0.10$.
- **Procedure**:
  1. Compute $\sigma_{\text{total}} = \sqrt{\sum \sigma_i^2}$.
  2. Compute $C = \operatorname{clip}(\exp(-\gamma \sigma_{\text{total}} / \sigma_{\text{max}}), 0, 1)$.
  3. Validate extrema and monotonicity.
- **Expected Result**:
  - $\min(\sigma_{\text{total}}) = \mathbf{0.0197\text{ m}^3/\text{m}^3}$, $\max(\sigma_{\text{total}}) = \mathbf{0.1063\text{ m}^3/\text{m}^3}$.
  - Mean Confidence Score: **0.4699** (Range: **0.20** to **0.74**).
- **Pass Criterion**: $\sigma_{\text{total}} \ge \max(\sigma_i)$ at all pixels; $0.0 \le C \le 1.0$.

### VP-003: Aerospace Plot 1 Decomposition Heatmap Verification
- **Verifies**: FR-009, NF-003, D
- **Setup**: 6 spatial arrays of shape $(50, 50)$.
- **Procedure**:
  1. Render $2 \times 3$ subplot grid with `inferno`, `magma`, and `YlGnBu` colormaps.
  2. Verify individual colorbars and panel titles.
- **Expected Result**: 6 panels rendered without axis ticks or layout overlap.
- **Pass Criterion**: Render completes cleanly; PNG image generated (length: 195,104 bytes).

### VP-004: Point Pixel Deliverable Verification
- **Verifies**: FR-010, IF-003
- **Setup**: Pixel coordinate $(x=25, y=25)$.
- **Procedure**:
  1. Extract predicted moisture, total uncertainty, and confidence score at index $(25, 25)$.
  2. Format into deliverable string: $\hat{\theta} \pm \sigma_{\text{total}}\text{ [Confidence: } C\text{]}$.
- **Expected Result**:
  - Moisture: **0.2971 m$^3$/m$^3$**
  - Uncertainty: $\pm$**0.0731 m$^3$/m$^3$**
  - Confidence: **33.40%** ($0.33$)
- **Pass Criterion**: Values match printed baseline banner exactly.

### VP-005: Empirical Coverage Reliability Audit
- **Verifies**: FR-011, DI-005, UQ-001
- **Setup**: $N = 2500$ points, `predicted_sigma = sigma_total.flatten()`.
- **Procedure**:
  1. Draw synthetic errors `true_errors = np.random.normal(0, predicted_sigma)`.
  2. Evaluate percentage of absolute residuals $\le 1\sigma, 2\sigma, 3\sigma$.
- **Expected Result**:
  - $1\sigma$ Coverage: **67.04%** (Theoretical: $68.27\%$)
  - $2\sigma$ Coverage: **95.52%** (Theoretical: $95.45\%$)
  - $3\sigma$ Coverage: **99.72%** (Theoretical: $99.73\%$)
- **Pass Criterion**: Coverage ordering satisfied; discloses circular validation defect D-001.

### VP-006: Aerospace Plot 2 Reliability Curve Diagnostics
- **Verifies**: FR-012, NF-003, D
- **Setup**: Subplot 1 (Spread-Skill scatter) and Subplot 2 (Reliability Curve across 20 confidence thresholds).
- **Procedure**:
  1. Render scatter plot with 1:1 sharpness dashed line.
  2. Plot empirical coverage against theoretical nominal confidence ($10\%$ to $99\%$).
- **Expected Result**: 2 subplots displayed; empirical profile aligns tightly with diagonal calibration line.
- **Pass Criterion**: Figure rendered successfully (length: 199,500 bytes).

### VP-007: 14-Day Persistent Cloud Outage Stress Scenario
- **Verifies**: FR-013, FR-014, UQ-003
- **Setup**: Outage parameters: $\Delta t = 14\text{ days} \implies \sigma_{\text{gap}} = 0.005 \cdot \exp(14.0/4.0)$, $\sigma_{\text{sensor}} = 0.08$.
- **Procedure**:
  1. Evaluate `compute_composite_uncertainty` under outage inputs.
  2. Compare mean uncertainty and confidence against baseline.
- **Expected Result**:
  - Mean Uncertainty: $\pm\mathbf{0.0521} \to \pm\mathbf{0.1865\text{ m}^3/\text{m}^3}$
  - Mean Confidence: $\mathbf{46.99\%} \to \mathbf{6.10\%}$
- **Pass Criterion**: Uncertainty surges by $>3.5\times$; confidence collapses to $<7\%$.

### VP-008: Deterministic Reproducibility
- **Verifies**: NF-001, NF-002, NF-004
- **Setup**: Clean environment under seed 1607.
- **Procedure**:
  1. Execute notebook top-to-bottom twice.
  2. Verify identical sample pixel values, coverage percentages, and outage metrics.
- **Expected Result**: Bit-identical output values; execution runtime $< 3.0$ seconds.
- **Pass Criterion**: 100% numerical match.

---

## 7. Verification Results

Evidence tags:
- **`[NB]`**: Directly extracted from cell execution outputs in `07-uncertainty-analysis.ipynb`.
- **`[AN]`**: Independently re-calculated numerical verification.
- **`[INS]`**: Source code and parameter inspection.

| VP ID | Verification Target | Execution Date | Executor | Result | Empirical Evidence & Numerical Values | Reviewer |
|:---|:---|:---:|:---:|:---:|:---|:---:|
| **VP-001** | Multi-Source Variance Fields | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 04: $\sigma_{\text{ens}} = \mathbf{0.0248}$, $\sigma_{\text{sensor}} = \mathbf{0.0307}$, $\sigma_{\text{gap}} = \mathbf{0.0222}$, $\sigma_{\text{model}} = \mathbf{0.0151}$. | *Pending* |
| **VP-002** | Composite Uncertainty & Score | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 06: $\sigma_{\text{total}} \in [\mathbf{0.0197}, \mathbf{0.1063}]$, Mean Confidence $= \mathbf{0.4699}$ (Range: $[0.20, 0.74]$). | *Pending* |
| **VP-003** | Plot 1 6-Panel Heatmaps | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 08: PNG rendered (length: 195,104 bytes). 6 subplots displayed. | *Pending* |
| **VP-004** | Pixel (25, 25) Deliverable Profile | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 09: Moisture: **0.2971**, Uncertainty: $\pm$**0.0731**, Confidence: **33.40%** ($0.33$). | *Pending* |
| **VP-005** | Reliability Coverage Audit | 2026-10-08 | Automated / G. Mohapatra | **PASS\*** | `[NB]` Cell 11: $1\sigma = \mathbf{67.04\%}$ ($68.27\%$), $2\sigma = \mathbf{95.52\%}$ ($95.45\%$), $3\sigma = \mathbf{99.72\%}$ ($99.73\%$). \*Defect D-001 noted. | *Pending* |
| **VP-006** | Plot 2 Calibration Diagnostics | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 13: PNG rendered (length: 199,500 bytes). Spread-skill and reliability curve displayed. | *Pending* |
| **VP-007** | 14-Day Cloud Outage Stress Test | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 15: Uncertainty $\pm\mathbf{0.0521} \to \pm\mathbf{0.1865}$, Confidence $\mathbf{46.99\%} \to \mathbf{6.10\%}$. | *Pending* |
| **VP-008** | Deterministic Reproducibility | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Bit-identical execution under seed 1607; runtime $< 2.0$s. | *Pending* |

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
| **FR-001** | Evaluation grid setup (`GRID_SIZE = (50, 50)`) | Cell 04 | VP-001 | **PASS** |
| **FR-002** | Ensemble spread field generation ($\sigma_{\text{ens}}$) | Cell 04 | VP-001 | **PASS** |
| **FR-003** | Sensor quality and 25% cloud mask field ($\sigma_{\text{sensor}}$) | Cell 04 | VP-001 | **PASS** |
| **FR-004** | Exponential temporal revisit latency penalty ($\sigma_{\text{gap}}$) | Cell 04 | VP-001 | **PASS** |
| **FR-005** | Model physics structural disagreement field ($\sigma_{\text{model}}$) | Cell 04 | VP-001 | **PASS** |
| **FR-006** | Quadratic variance addition formula ($\sigma_{\text{total}}$) | Cell 06 | VP-002 | **PASS** |
| **FR-007** | Exponential confidence score transformation ($C$) | Cell 06 | VP-002 | **PASS** |
| **FR-008** | Summary spatial statistics reporting | Cells 04, 06 | VP-001, VP-002 | **PASS** |
| **FR-009** | Aerospace Plot 1 6-panel decomposition heatmaps | Cell 08 | VP-003 | **PASS** |
| **FR-010** | Pixel $(25, 25)$ deliverable profile formatting | Cell 09 | VP-004 | **PASS** |
| **FR-011** | Empirical coverage reliability audit ($1\sigma, 2\sigma, 3\sigma$) | Cell 11 | VP-005 | **PARTIAL\*** |
| **FR-012** | Aerospace Plot 2 spread-skill & reliability curve rendering | Cell 13 | VP-006 | **PASS** |
| **FR-013** | 14-day persistent cloud outage stress scenario | Cell 15 | VP-007 | **PASS** |
| **FR-014** | Stress scenario degradation metric logging | Cell 15 | VP-007 | **PASS** |
| **DI-001** | Non-negative standard deviation fields | Cell 04 | VP-001 | **PASS** |
| **DI-002** | Composite standard deviation variance dominance | Cell 06 | VP-002 | **PASS** |
| **DI-003** | Bounded confidence interval $[0.0, 1.0]$ | Cell 06 | VP-002 | **PASS** |
| **DI-004** | Inverse monotonicity of confidence score | Cell 06 | VP-002 | **PASS** |
| **DI-005** | Hierarchical coverage ordering ($\operatorname{Cov}_{1\sigma} \le \operatorname{Cov}_{2\sigma} \le \operatorname{Cov}_{3\sigma}$) | Cell 11 | VP-005 | **PASS** |
| **IF-001** | `compute_composite_uncertainty` signature and returns | Cell 06 | VP-002 | **PASS** |
| **IF-002** | Matrix dimension consistency $(50, 50)$ | Cells 04, 06 | VP-001, VP-002 | **PASS** |
| **IF-003** | In-graph telemetry format (`±σ`, confidence %) | Cells 09, 15 | VP-004, VP-007 | **PASS** |
| **UQ-001** | Theoretical vs empirical Gaussian coverage display | Cell 11 | VP-005 | **PASS** |
| **UQ-002** | Realism of maximum uncertainty bound ($\sigma_{\text{max}} = 0.10$) | Cell 06 | VP-002 | **PASS** |
| **UQ-003** | Severe confidence reduction under sensor failure ($46.99\% \to 6.10\%$) | Cell 15 | VP-007 | **PASS** |
| **NF-001** | Deterministic seed initialization (1607) | Cell 02 | VP-008 | **PASS** |
| **NF-002** | Unattended headless execution | All cells | Execution Audit | **PASS** |
| **NF-003** | Dark telemetry UI styling on generated figures | Cells 02, 08, 13 | VP-003, VP-006 | **PASS** |
| **NF-004** | Computational execution runtime $< 3.0$ seconds | All cells | Execution Audit | **PASS** |

---

## 9. Configuration and Change Control

### 9.1 Controlled Items

The following items constitute the controlled configuration baseline for Notebook 07:
1. **Source Notebook**: `1_notebooks_sandbox/07-uncertainty-analysis.ipynb` (SHA-256 baseline hash required).
2. **Requirements & Verification Document (This Document)**: `8_docs/01_Notebooks/07. uncertainty analysis/07_uncertainty_analysis_REQUIREMENTS.md`.
3. **Companion Technical Description (Pending User Call)**: `8_docs/01_Notebooks/07. uncertainty analysis/07_uncertainty_analysis.rst`.
4. **Execution Environment**: Pinned Python environment with NumPy, Pandas, Matplotlib, PyTorch.

### 9.2 Baseline Identification

- **Current Working Baseline**: `NB07-BL-01-DRAFT`
- **Target Release Baseline**: `NB07-BL-01`
- **Upstream Baseline**: `NB06-BL-01` (EnKF State Estimation)
- **Downstream Target Baseline**: `NB08-BL-01` (`08-robustness-and-failure-analysis.ipynb`)

### 9.3 Change Procedure

Any modification to variance formulations, confidence decay multipliers, calibration targets, or stress scenarios shall adhere to the following control lifecycle:

```
[Change Request (CR)] 
        │
        ▼
[Impact Analysis on Confidence Calibration & Failure Risk Analysis] 
        │
        ▼
[Technical Review & Approval by Lead Authority] 
        │
        ▼
[Code / Documentation Modification] 
        │
        ▼
[Execution of Verification Procedures VP-001 to VP-008] 
        │
        ▼
[Traceability Matrix & Document Control Update] 
        │
        ▼
[Baseline Tag Update]
```

### 9.4 Version Control Rules

1. **Cell Integrity**: Cell outputs shall be committed matching the baseline hash or cleanly stripped before formal release.
2. **Deterministic Outputs**: Clean-kernel re-runs under seed 1607 shall reproduce identical coverage metrics ($67.04\%, 95.52\%, 99.72\%$) and pixel deliverable values ($0.2971 \pm 0.0731$).
3. **Requirement Atomicity**: Modifying a requirement mandates updating Sections 4, 5, 6, 7, and 8 concurrently.
4. **Deprecation**: Deprecated requirements shall be tagged `WITHDRAWN` and numerical IDs permanently reserved.

---

## 10. Open Defects and Discrepancies

| ID | Description | Affected Requirement | Severity | Status | Corrective Action |
|:---|:---|:---:|:---:|:---:|:---|
| **D-001** | **Circular Empirical Coverage Validation**: In Cell 11 line 244, `true_errors` is generated *from* `np.random.normal(0, predicted_sigma)`. Because evaluation errors are artificially drawn from the exact normal distribution parameterized by predicted uncertainty, the coverage metrics ($67.04\%, 95.52\%$) match theoretical Gaussian bounds by circular construction rather than testing empirical model residuals. | FR-011, UQ-001 | **CRITICAL** | **OPEN** | Evaluate coverage against actual ground-truth sensor residuals or holdout validation errors from Notebooks 04/05/06 rather than synthetic random normals. |
| **D-002** | **Decoupled Variance Ingestion**: Notebook 07 generates all four variance fields ($\sigma_{\text{ens}}, \sigma_{\text{sensor}}, \sigma_{\text{gap}}, \sigma_{\text{model}}$) using synthetic random generators, completely ignoring the posterior covariance $\mathbf{P}^a$ computed in Notebook 06 and the ConvLSTM/PINN residual fields from Notebooks 04 and 05. | FR-002, FR-005 | **HIGH** | **OPEN** | Ingest $\mathbf{P}^a$ diagonal from Notebook 06 for $\sigma_{\text{ens}}$ and compute true ConvLSTM-PINN residual differences for $\sigma_{\text{model}}$. |
| **D-003** | **Grid Dimension Inconsistency**: Notebook 07 operates on a $50 \times 50$ spatial grid, creating a dimension mismatch with Notebook 03 ($20 \times 20$), Notebook 04 ($10 \times 10$), and Notebook 05 ($100 \times 100$). | FR-001, IF-002 | **MEDIUM** | **OPEN** | Standardize a unified spatial raster grid footprint (e.g. $100 \times 100$) across all validation notebooks. |
| **D-004** | **Absence of Calibrated Field Export**: Spatial uncertainty arrays ($\sigma_{\text{total}}$) and confidence maps ($C$) are rendered visually but are not serialized to disk (`/data_processed/`), preventing ingestion by Notebook 08. | IF-002 | **MEDIUM** | **OPEN** | Add explicit `np.savez_compressed('calibrated_uncertainty_field.npz', sigma_total=sigma_total, confidence=confidence_score)` export cell. |

---

## 11. Risks and Assumptions

### 11.1 Technical Risks

| Risk ID | Risk Description | Severity | Likelihood | Consequence | Mitigation Strategy |
|:---|:---|:---:|:---|:---|
| **R-001** | **False Calibration Confidence** | Critical | High | Relying on circular synthetic coverage gives misleading assurance of sensor reliability under non-Gaussian real-world errors. | Validate coverage against true in-situ soil moisture sensor residuals across diverse weather conditions. |
| **R-002** | **Uncorrelated Variance Assumption Failure** | Moderate | Medium | Assuming sensor noise and model disagreement are strictly orthogonal may underestimate total error if both are biased by cloud cover. | Formulate full error cross-covariance matrices rather than simple quadratic summation. |
| **R-003** | **Exponential Sensitivity Tuning Drift** | Low | Low | An uncalibrated decay parameter $\gamma = 1.5$ may penalize mild uncertainty excessively, depressing operational confidence scores. | Calibrate $\gamma$ against stakeholder risk tolerance and ROC decision curves. |
| **R-004** | **Lack of Downstream Persistence** | Moderate | High | Unsaved spatial confidence fields force re-computation in subsequent risk modeling scripts. | Add persistent file serialization. |

### 11.2 Architectural Assumptions

| Assumption ID | Statement of Assumption | Rationale |
|:---|:---|:---|
| **A-001** | **Orthogonality of Variance Sources** | Ensemble spread, sensor noise, revisit latency, and model structural errors are mutually independent random processes. |
| **A-002** | **Exponential Uncertainty Growth Over Time** | Subsurface moisture prediction skill decays exponentially with time elapsed since the last satellite pass. |
| **A-003** | **Gaussian Residual Distribution** | Prediction residuals at each pixel are asymptotically normal, validating $1\sigma / 2\sigma / 3\sigma$ confidence interval interpretation. |
| **A-004** | **Spatial Pixel Independence** | Pixel-wise uncertainty can be computed point-by-point without spatial correlation tapering across neighboring pixels. |
| **A-005** | **Uniform Sensor Failure Profile** | During extreme cloud outages, sensor noise degrades uniformly across the entire subgrade domain. |

---

## 12. Release and Baseline Acceptance Criteria

Notebook `07-uncertainty-analysis.ipynb` shall achieve formal release baseline `NB07-BL-01` only upon meeting all of the following criteria:

1. **Requirements Verification**: All Functional (FR), Data Integrity (DI), and Interface (IF) requirements verified as **MET**.
2. **Defect Remediation**: Resolution of Defect **D-001** (replacement of circular synthetic error generator with actual model residuals).
3. **Pipeline Ingestion**: Ingestion of real EnKF covariance from Notebook 06 and ConvLSTM/PINN states from Notebooks 04/05 (Defect **D-002**).
4. **Grid Footprint Harmonization**: Resolution of grid size mismatch (Defect **D-003**).
5. **Artifact Persistence**: Implementation of file export saving calibrated uncertainty and confidence fields to disk (Defect **D-004**).
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
> **SEPARATION OF SYNTHETIC CALIBRATION AND EMPIRICAL SENSOR CONFIDENCE**
> 
> Successful completion of the calibration routines in Notebook 07 proves:
> 1. The software correctly implements quadratic variance decomposition ($\sigma_{\text{total}} = \sqrt{\sum \sigma_i^2}$) and exponential confidence score mapping ($C \in [0, 1]$).
> 2. The statistical coverage evaluation logic functions correctly when provided with known Gaussian random errors ($67.04\%$ for $1\sigma$, $95.52\%$ for $2\sigma$).
> 3. Under a simulated 14-day cloud outage stress test, the confidence score drops appropriately from $46.99\%$ to $6.10\%$, demonstrating responsive failure detection.
> 
> **THIS DOES NOT CONSTITUTE PROOF OF SATELLITE SYSTEM CALIBRATION.**
> 
> Because:
> - The coverage test used synthetic errors drawn from the predicted distribution rather than real validation residuals.
> - The variance fields are synthetic random arrays rather than empirical measurement uncertainties.
> - True calibration requires evaluating against real in-situ soil moisture probe arrays (e.g., ISRO / IMD ground networks) across diverse seasonal conditions in Odisha.

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

This document, the underlying software architecture, mathematical formulations, uncertainty decomposition engines, and associated telemetry data structures constitute **proprietary intellectual property** developed under the auspices of JCC RS-SDA Division.

Unauthorized copying, distribution, decompilation, reverse engineering, dissemination, or commercial utilization—in whole or in part, in any format or medium—is strictly prohibited without prior express written authorization from the author and JCC Command Authority.

```
========================================================================================
                      CLASSIFICATION: STRICTLY PROPRIETARY & CONTROLLED
========================================================================================
```
