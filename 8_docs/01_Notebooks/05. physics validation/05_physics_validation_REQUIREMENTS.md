# THE MRIDANSH (AETHER-MRID1607X)
# Notebook 05 — Physics-Informed Validation (PINN & Richards/Darcy Mechanics)
# Requirements, Verification and Configuration Control

---

## 1. Document Control

### 1.1 Identification

| Field | Value |
|:---|:---|
| **Document ID** | MRID-NB05-DOC-001 |
| **Notebook ID** | `05-physics-validation.ipynb` |
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
| 0.1 | 2026-10-08 | Gourgopal Mohapatra | Initial structural extraction of `05-physics-validation.ipynb` cells, autograd computational graphs, and loss telemetry. |
| 1.0 | 2026-10-08 | Gourgopal Mohapatra | Baseline requirements specification: atomic physics conservation criteria, automatic differentiation procedures, empirical loss logs, discrepancy analysis, and verification matrix. |

### 1.3 Document Conventions

- **SHALL** indicates a mandatory, verifiable, and binding engineering requirement.
- **SHOULD** indicates a recommended design practice or optimization target.
- **MAY** indicates an optional or alternative implementation path.
- **Requirement Status Definitions**:
  - `MET`: Requirement verified by execution against empirical output evidence.
  - `PARTIAL`: Implementation exists but carries unverified branches, narrative discrepancies, or edge-case limitations.
  - `NOT MET`: Requirement is absent, failing verification, or contradicted by runtime evidence.
  - `WAIVED`: Formal departure accepted with recorded technical rationale.
- **Verification Methods**:
  - `T` (Test): Quantitative execution with test assertions and numerical threshold validation.
  - `A` (Analysis): Theoretical evaluation of mathematical PDE conservation, dimensional units, and autograd graphs.
  - `I` (Inspection): Manual examination of source code, equations, layer parameters, and configuration dictionaries.
  - `D` (Demonstration): Observation of operational execution, convergence curves, and diffusion profiles.
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

This document establishes the formal engineering requirements, mathematical formulations, verification procedures, empirical execution results, bidirectional traceability, configuration management, and technical discrepancy logs for Jupyter notebook `05-physics-validation.ipynb` within the **THE MRIDANSH** system.

### 2.2 System Context

**THE MRIDANSH** (*AETHER-MRID1607X*) couples spaceborne remote sensing with geoscientific conservation laws to predict depth-resolved soil moisture and geotechnical shear strength.

Within this macro-architecture:
- **Notebook 03** extracts spatial terrain slope/aspect gradients and constructs topological graph meshes.
- **Notebook 04** executes temporal sliding-window sequence forecasting via recurrent ConvLSTM networks.
- **Notebook 05 (Item Under Documentation)** enforces 1D unsaturated soil water transport mechanics by embedding the mixed-form Richards Partial Differential Equation (PDE) and van Genuchten analytical Soil Water Retention Curves (SWRC) into a Physics-Informed Neural Network (PINN). It computes exact autograd space-time derivatives and optimizes continuous moisture fields $\hat{\theta}(z, t)$ subject to physical boundary constraints.
- **Downstream Consumers (Notebooks 06–08)** consume these physically bounded moisture profiles to evaluate slope stability, landslide thresholds, and Ensemble Kalman Filter (EnKF) assimilation state transitions.

### 2.3 Notebook Objective

Notebook 05 covers Sprint Days 9–11 of the 18-Day Scientific Validation Sprint:
1. **Day 9 Objective**: Formalize 1D Richards' equation, configure USDA soil hydraulic parameter sets (`sandy_loam`, `silty_clay`), implement closed-form van Genuchten analytical solvers, verify SWRC and conductivity curves, and construct PyTorch differentiable operators.
2. **Day 10 Objective**: Formulate the 4-layer MLP PINN architecture with physical Sigmoid bounding, implement autograd space-time partial derivatives, configure surface infiltration and deep aquifer boundary conditions, and execute a 100-epoch composite loss optimization loop ($\mathcal{L}_{\text{total}} = 0.1\mathcal{L}_{\text{PDE}} + 0.5\mathcal{L}_{\text{BC}}$).
3. **Day 11 Objective**: Benchmark PINN physical consistency against an unconstrained data model, construct a $100 \times 100$ continuous moisture diffusion grid across depth-time space ($z \in [0, 200\text{ cm}]$, $t \in [0, 168\text{ hrs}]$), and render aerospace diagnostic profiles.

### 2.4 In Scope

- All 36 cells of `05-physics-validation.ipynb` (15 code cells, 21 markdown cells).
- van Genuchten parameter dictionary definition (`theta_r`, `theta_s`, `alpha`, `n`, `m`, `Ks`, `l`).
- Analytical forward solvers for retention $\theta(\psi)$ and conductivity $K(\theta)$.
- Differentiable PyTorch operators using `torch.autograd.grad`.
- MLP PINN architecture with bounded output scaling: $\theta \in [\theta_r, \theta_s]$.
- Richards PDE residual evaluation: $\mathcal{R}_{\text{PDE}} = \frac{\partial \hat{\theta}}{\partial t} + \frac{\partial q}{\partial z}$.
- Uniform space-time collocation point generation ($z \in [0, 200\text{ cm}]$, $t \in [0, 168\text{ hrs}]$).
- Dirichlet boundary condition formulation at $z = 0\text{ cm}$ ($\theta = 0.35$) and $z = 200\text{ cm}$ ($\theta = 0.15$).
- 100-epoch Adam optimization with gradient norm clipping ($\text{max\_norm} = 1.0$).
- Benchmark evaluation comparing PINN PDE residuals with unconstrained neural baselines.
- Continuous 2D moisture diffusion grid generation and rendering across depth-time space.
- Rendering of 4 aerospace diagnostic figures.

### 2.5 Out of Scope

- 2D/3D lateral overland flow and Richards equation in multiple spatial dimensions (restricted strictly to 1D vertical infiltration).
- Dynamic meteorological rainfall forcing coupling (surface infiltration is held at a constant Dirichlet boundary $\theta = 0.35$).
- In-situ soil sensor telemetry assimilation (EnKF assimilation is deferred to Notebook 06).
- Hysteresis in soil water retention curves (wetting vs drying branch disparities).

### 2.6 Current-State Declaration (Mandatory Engineering Disclosure)

> [!WARNING]
> **MANDATORY CURRENT-STATE DECLARATION: SYNTHETIC COLLOCATION AND BOUNDARY BENCHMARK**
> 
> Notebook 05 operates over an idealized continuous space-time domain where collocation coordinates $(z, t)$ are drawn uniformly at random ($z \sim \mathcal{U}(0, 200\text{ cm})$, $t \sim \mathcal{U}(0, 168\text{ hrs})$) and boundary conditions are fixed constant scalars ($\theta_{\text{top}} = 0.35, \theta_{\text{bottom}} = 0.15$). 
> 
> Furthermore, the benchmark comparison against the unconstrained baseline in Step 10 evaluates mock random targets ($\theta_{\text{obs}} \sim \mathcal{U}(\theta_r, \theta_s)$), yielding a measured PDE residual reduction of **-1.81%** (slight degradation), which directly contradicts the narrative summary claim of a ">95% error reduction". Consequently, this notebook verifies **computational autograd differential mechanics and boundary enforcement**, but does **not** represent a validated field model for site-specific hydrological forecasts.

---

## 3. Definitions and Abbreviations

| Term / Abbreviation | Definition |
|:---|:---|
| **PINN** | Physics-Informed Neural Network (Neural network trained with PDE residuals embedded into its loss function). |
| **Richards PDE** | Non-linear partial differential equation governing water movement in unsaturated soils. |
| **SWRC** | Soil Water Retention Curve (Relationship between matric potential $\psi$ and volumetric soil moisture $\theta$). |
| **van Genuchten** | Closed-form parametric model (van Genuchten, 1980) relating $\theta$, $\psi$, and unsaturated hydraulic conductivity $K$. |
| **$\psi$** | Matric potential head (negative suction pressure, units: cm). |
| **$\theta$** | Volumetric soil water content (dimensionless: $\text{m}^3/\text{m}^3$ or $\text{cm}^3/\text{cm}^3$). |
| **$K(\theta)$** | Unsaturated hydraulic conductivity (units: cm/hr). |
| **$K_s$** | Saturated hydraulic conductivity at full saturation ($\theta = \theta_s$). |
| **Darcy Flux ($q$)** | Total volumetric water flux density under matric and gravitational potential gradients: $q = -K(\theta) \left(\frac{\partial \psi}{\partial z} + 1\right)$. |
| **Collocation Points** | Discrete space-time coordinates $(z_i, t_i)$ where the PDE differential residual is minimized. |
| **Autograd** | PyTorch reverse-mode automatic differentiation engine evaluating exact analytical gradients. |
| **JCC RS-SDA** | Jagannath Command Center — Remote Sensing & Spatial Data Analytics Division. |

---

## 4. Requirements

### 4.1 Functional Requirements

- **FR-001**: The software shall define standard van Genuchten soil hydraulic parameter dictionaries for at least two standard USDA soil classes (`sandy_loam` and `silty_clay`), declaring:
  - $\theta_r$ (residual water content)
  - $\theta_s$ (saturated water content)
  - $\alpha$ (inverse air-entry suction, $\text{cm}^{-1}$)
  - $n$ (pore-size distribution parameter)
  - $m = 1 - 1/n$
  - $K_s$ (saturated hydraulic conductivity, cm/hr)
  - $l$ (pore connectivity parameter, default $0.5$)
- **FR-002**: The software shall select `sandy_loam` as the active operational soil profile and log all 7 hydraulic parameters.
- **FR-003**: The software shall implement closed-form NumPy forward solvers:
  - Effective saturation: $\Theta(\psi) = \left[1 + (\alpha |\psi|)^n\right]^{-m}$
  - Moisture retention: $\theta(\psi) = \theta_r + (\theta_s - \theta_r) \cdot \Theta(\psi)$
  - Hydraulic conductivity: $K(\theta) = K_s \cdot S_e^l \left[1 - \left(1 - S_e^{1/m}\right)^m\right]^2$ where $S_e = \operatorname{clip}\left(\frac{\theta - \theta_r}{\theta_s - \theta_r}, 10^{-6}, 1.0\right)$.
- **FR-004**: The software shall evaluate analytical SWRC and conductivity curves across a logarithmic matric potential range $\psi \in [0.1, 10000.0]\text{ cm}$ (200 sample points).
- **FR-005**: The software shall implement PyTorch-differentiable counterparts for retention and hydraulic conductivity supporting backpropagation via `torch.autograd`.
- **FR-006**: The software shall instantiate a 4-layer Multi-Layer Perceptron (MLP) `PhysicsInformedNN` satisfying:
  - Input layer mapping $(z, t) \in \mathbb{R}^2 \to 64$ hidden units.
  - 3 hidden layers with 64 units and $\operatorname{Tanh}$ non-linear activation functions.
  - Linear output projection to scalar $\theta_{\text{raw}}$.
  - Xavier normal weight initialization and zero bias initialization.
  - Strict physical range enforcement via Sigmoid scaling:
    $$\hat{\theta}(z, t) = \theta_r + (\theta_s - \theta_r) \cdot \sigma(\theta_{\text{raw}})$$
- **FR-007**: The software shall compute exact space-time partial derivatives using `torch.autograd.grad`:
  - Temporal rate: $\frac{\partial \hat{\theta}}{\partial t}$
  - Spatial gradient: $\frac{\partial \hat{\theta}}{\partial z}$
  - Gravitational Darcy flux: $q = -K(\hat{\theta}) \left(\frac{\partial \hat{\theta}}{\partial z} + 1.0\right)$
  - Spatial flux divergence: $\frac{\partial q}{\partial z}$
  - Richards PDE residual: $\mathcal{R}_{\text{PDE}} = \frac{\partial \hat{\theta}}{\partial t} + \frac{\partial q}{\partial z}$
- **FR-008**: The software shall generate space-time collocation points uniformly sampling depth $z \in [0, 200\text{ cm}]$ and time $t \in [0, 168\text{ hrs}]$.
- **FR-009**: The software shall evaluate the untrained PINN model over 1,500 collocation points and log initial moisture range, mean residual, and maximum residual error.
- **FR-010**: The software shall formulate top ($z = 0\text{ cm}, \theta_{\text{top}} = 0.35$) and bottom ($z = 200\text{ cm}, \theta_{\text{bottom}} = 0.15$) Dirichlet boundary condition tensors over 300 temporal sample points.
- **FR-011**: The software shall compute composite multi-objective loss:
  $$\mathcal{L}_{\text{total}} = w_{\text{pde}} \mathcal{L}_{\text{PDE}} + w_{\text{bc}} (\mathcal{L}_{\text{bc\_top}} + \mathcal{L}_{\text{bc\_bottom}})$$
  with default weights $w_{\text{pde}} = 0.1$ and $w_{\text{bc}} = 0.5$.
- **FR-012**: The software shall execute a 100-epoch Adam optimization loop ($lr = 10^{-3}$) with dynamic collocation resampling (1,000 points/epoch) and gradient norm clipping ($\text{max\_norm} = 1.0$).
- **FR-013**: The software shall evaluate and display convergence telemetry (total loss, PDE loss, boundary loss) on a logarithmic scale.
- **FR-014**: The software shall benchmark PDE residuals on an unseen test domain (1,200 points) comparing the trained PINN against an unconstrained neural network baseline.
- **FR-015**: The software shall construct a continuous $100 \times 100$ moisture diffusion mesh over depth $z \in [0, 200\text{ cm}]$ and time $t \in [0, 168\text{ hrs}]$ and render the resulting field.

### 4.2 Data Integrity Requirements

- **DI-001**: Output moisture $\hat{\theta}(z, t)$ shall be strictly bounded within the physical soil range $[\theta_r, \theta_s]$ everywhere in the space-time domain.
- **DI-002**: Normalized saturation $S_e$ shall be clamped to prevent negative arguments or division by zero in $K(\theta)$ evaluation.
- **DI-003**: Autograd graphs shall set `create_graph=True` and `retain_graph=True` to support second-order derivatives $\frac{\partial q}{\partial z}$.
- **DI-004**: Collocation depth coordinates $z$ shall strictly satisfy $0 \le z \le 200\text{ cm}$.
- **DI-005**: Collocation time coordinates $t$ shall strictly satisfy $0 \le t \le 168\text{ hrs}$ (7 days).
- **DI-006**: Boundary loss tensors shall be non-negative ($\mathcal{L}_{\text{bc}} \ge 0$).

### 4.3 Interface Requirements

- **IF-001**: Forward input to `PhysicsInformedNN` shall accept two column vectors $z, t \in \mathbb{R}^{N \times 1}$ and return $\hat{\theta} \in \mathbb{R}^{N \times 1}$.
- **IF-002**: Function `compute_richards_pde_residual` shall return a tuple of `(pde_residual, theta_pred)` where both tensors have shape $(N, 1)$.
- **IF-003**: Function `compute_composite_pinn_loss` shall accept weighting tuple `(w_data, w_pde, w_bc)` and return total loss along with itemized PDE and BC loss scalars.
- **IF-004**: The moisture diffusion matrix shall format into a NumPy 2D array of shape $(100, 100)$ suitable for `matplotlib.pyplot.imshow`.

### 4.4 Uncertainty / Quality Requirements

- **UQ-001**: Gradient norm clipping shall be applied at threshold $\text{max\_norm} = 1.0$ to stabilize second-order autograd backpropagation.
- **UQ-002**: Collocation points shall be dynamically resampled every epoch to mitigate overfitting to discrete spatial coordinates.
- **UQ-003**: Physical consistency metrics (mean absolute PDE residual) shall be logged and displayed with numerical precision to at least 6 decimal places.

### 4.5 Non-Functional Requirements

- **NF-001**: Deterministic seeds shall be fixed for PyTorch (`torch.manual_seed(42)`) and NumPy (`np.random.seed(42)`).
- **NF-002**: The notebook shall execute unattended from Cell 00 to Cell 35 without interactive prompts.
- **NF-003**: Visual plots shall employ the project dark telemetry theme (`#00FFCC` borders, `#1A3344` grids, monospace fonts).
- **NF-004**: The execution device shall dynamically select CUDA GPU if available or fallback cleanly to CPU.

---

## 5. Requirements Attributes

| ID | Requirement Statement | Rationale | Method | Acceptance Criterion | Status |
|:---|:---|:---|:---:|:---|:---:|
| **FR-001** | Define van Genuchten soil parameter sets. | Soil physics parameter baseline. | I | Parameter dictionaries present with 7 constants. | **MET** |
| **FR-002** | Select and log `sandy_loam` profile. | Operational soil class definition. | T | Active profile logged with matching values. | **MET** |
| **FR-003** | Implement analytical SWRC and $K(\theta)$ solvers. | Forward analytical reference curves. | T | Retention and conductivity evaluate cleanly. | **MET** |
| **FR-004** | Evaluate curves over $\psi \in [0.1, 10000]\text{ cm}$. | Validate full tension range across 200 points. | T | Moisture in $[0.066, 0.410]$, $K$ in $[10^{-13}, 4.31]$. | **MET** |
| **FR-005** | Implement PyTorch differentiable hydraulic operators. | PDE loss gradient computation. | I/T | Functions evaluate with PyTorch tensors. | **PARTIAL\*** |
| **FR-006** | Instantiate 4-layer MLP PINN with Sigmoid bounds. | Continuous space-time surrogate model. | I/T | Model architecture printed; output bounded. | **MET** |
| **FR-007** | Compute autograd space-time PDE residual. | Richards equation residual enforcement. | T | Residual tensor emitted; shape $(N, 1)$. | **MET** |
| **FR-008** | Generate space-time collocation points ($z \in [0, 200], t \in [0, 168]$). | Domain discretization for PDE minimization. | T | Points generated; shapes $(1500, 1)$. | **MET** |
| **FR-009** | Untrained PINN PDE residual baseline evaluation. | Pre-training physical error benchmark. | T | Mean error logged ($0.001347$), max ($0.008327$). | **MET** |
| **FR-010** | Formulate Dirichlet boundary tensors (top $0.35$, bottom $0.15$). | Hydrological boundary enforcement. | T | Top and bottom target tensors verified. | **MET** |
| **FR-011** | Composite loss formulation ($\mathcal{L}_{\text{total}}$). | Multi-objective PDE + BC optimization. | T | Total loss computes correctly with weights. | **MET** |
| **FR-012** | 100-epoch Adam optimization with gradient clipping. | Physical parameter convergence. | T | 100 epochs complete; total loss drops $< 10^{-4}$. | **MET** |
| **FR-013** | Log and render convergence telemetry. | Optimization auditing on log scale. | D | Telemetry plot rendered; metrics displayed. | **MET** |
| **FR-014** | Benchmark PINN vs unconstrained baseline. | Physical consistency verification. | T | Residuals compared on unseen test domain. | **FAIL\*** |
| **FR-015** | Construct $100 \times 100$ moisture diffusion grid. | Continuous vertical infiltration visualization. | T | Grid matrix assembled; shape $(100, 100)$. | **MET** |
| **DI-001** | Output moisture bounded in $[\theta_r, \theta_s]$. | Physical mass conservation boundary. | T | All predicted values strictly within $[0.065, 0.410]$. | **MET** |
| **DI-002** | Clamped normalized saturation ($S_e$). | Prevent division by zero and negative powers. | I/T | Clamp verified in `torch_van_genuchten_k`. | **MET** |
| **DI-003** | Second-order autograd graph retention. | Support $\frac{\partial q}{\partial z}$ derivatives. | I/T | `create_graph=True` verified in code. | **MET** |
| **DI-004** | Collocation depth bounds $z \in [0, 200\text{ cm}]$. | Spatial physical domain validity. | T | $\min(z) \ge 0, \max(z) \le 200$. | **MET** |
| **DI-005** | Collocation time bounds $t \in [0, 168\text{ hrs}]$. | Temporal simulation horizon validity. | T | $\min(t) \ge 0, \max(t) \le 168$. | **MET** |
| **DI-006** | Non-negative boundary losses ($\mathcal{L}_{\text{bc}} \ge 0$). | Squared error mathematical integrity. | T | Squared differences $\ge 0$. | **MET** |
| **IF-001** | Inputs $z, t \in \mathbb{R}^{N \times 1}$, output $\hat{\theta} \in \mathbb{R}^{N \times 1}$. | Tensor dimension contract. | T | Shapes verified across all forward passes. | **MET** |
| **IF-002** | `compute_richards_pde_residual` return contract. | Operator interface contract. | T | Tuple of shape $((N, 1), (N, 1))$ returned. | **MET** |
| **IF-003** | `compute_composite_pinn_loss` return contract. | Multi-loss evaluator interface. | T | Tuple `(total_loss, pde_val, bc_val)` returned. | **MET** |
| **IF-004** | Moisture diffusion grid shape $(100, 100)$. | Visualization array dimension contract. | T | Array shape $(100, 100)$ verified. | **MET** |
| **UQ-001** | Gradient norm clipping at threshold $1.0$. | Prevent autograd derivative explosion. | I/T | `clip_grad_norm_` active in loop. | **MET** |
| **UQ-002** | Dynamic collocation resampling per epoch. | Spatially uniform generalization. | I/T | Resampling active in training loop. | **MET** |
| **UQ-003** | High-precision metric logging (6 decimal places). | Precision reporting of PDE residuals. | D | Outputs formatted with `:.6f`. | **MET** |
| **NF-001** | Deterministic random seeds (PyTorch 42, NumPy 42). | Bit-for-bit numerical reproducibility. | I/T | Seeds declared in Cell 02. | **MET** |
| **NF-002** | Headless non-interactive execution. | Unattended pipeline capability. | D | All 36 cells execute sequentially without error. | **MET** |
| **NF-003** | Dark telemetry UI styling on generated plots. | Visual consistency across division. | I | Themes and colorbars conform to standard. | **MET** |
| **NF-004** | Dynamic device selection (CUDA or CPU). | Hardware flexibility. | I/T | Device detected as CPU and logged. | **MET** |

*\*Note: FR-005 carries partial defect D-001 (`tirch` typo in unused function). FR-014 marked FAIL due to negative residual reduction (-1.81%) contradicting narrative claims.*

---

## 6. Verification Procedures

### VP-001: Soil Hydraulic Parameter Dictionary Inspection
- **Verifies**: FR-001, FR-002
- **Setup**: Python 3.10+ kernel with NumPy.
- **Procedure**:
  1. Inspect `SOIL_HYDRAULIC_PARAMS` dictionary.
  2. Select `ACTIVE_SOIL = SOIL_HYDRAULIC_PARAMS['sandy_loam']`.
  3. Validate parameters: $\theta_r = 0.065$, $\theta_s = 0.410$, $\alpha = 0.075$, $n = 1.89$, $m = 0.4709$, $K_s = 4.42$, $l = 0.5$.
- **Expected Result**: All 7 parameters match exact USDA sandy loam specifications.
- **Pass Criterion**: Zero missing keys; numerical values match expected constants.

### VP-002: Analytical SWRC and Hydraulic Conductivity Solvers
- **Verifies**: FR-003, FR-004, DI-002
- **Setup**: `van_genuchten_retention` and `van_genuchten_conductivity` functions; $\psi \in [0.1, 10000.0]\text{ cm}$.
- **Procedure**:
  1. Evaluate `theta_curve = van_genuchten_retention(psi_range, ACTIVE_SOIL)`.
  2. Evaluate `k_curve = van_genuchten_conductivity(theta_curve, ACTIVE_SOIL)`.
  3. Check min and max ranges.
- **Expected Result**:
  - $\psi$ range: $0.1$ to $10000.0\text{ cm}$.
  - $\theta$ range: $0.0660$ to $0.4100\text{ m}^3/\text{m}^3$.
  - $K$ range: $6.98 \times 10^{-13}$ to $4.31\text{ cm/hr}$.
- **Pass Criterion**: Values monotonic and bounded within physical limits.

### VP-003: Aerospace Plot 1 Retention Curve Diagnostics
- **Verifies**: NF-003, D
- **Setup**: Generated $\psi$, $\theta$, and $K$ curves.
- **Procedure**:
  1. Render 2-panel figure showing SWRC (semi-log x-axis) and unsaturated conductivity.
  2. Inspect embedded diagnostic text box.
- **Expected Result**: Plot displays successfully with `#00FFCC` and `#FF9900` curves.
- **Pass Criterion**: Image rendered without clipping or backend warnings.

### VP-004: Differentiable PyTorch Operator Inspection
- **Verifies**: FR-005, DI-002
- **Setup**: Functions `torch_van_genuchten_theta` and `torch_van_genuchten_k`.
- **Procedure**:
  1. Inspect source code for syntax and correctness.
  2. Test `torch_van_genuchten_k` with tensor input.
- **Expected Result**: `torch_van_genuchten_k` evaluates smoothly with clamp $[10^{-5}, 1.0]$.
- **Pass Criterion**: Disclose defect D-001 (`tirch` typo on line 249 of `torch_van_genuchten_theta`).

### VP-005: PINN Architecture Instantiation and Bounded Forward Pass
- **Verifies**: FR-006, DI-001, IF-001
- **Setup**: `PhysicsInformedNN(in_dim=2, hidden_dim=64, num_layers=4)`.
- **Procedure**:
  1. Instantiate model and inspect sequential layers (4 Linear, 4 Tanh, 1 Linear).
  2. Pass random input tensors $z, t \in \mathbb{R}^{10 \times 1}$.
  3. Verify output tensor $\hat{\theta} \in [\theta_r, \theta_s]$.
- **Expected Result**: Network instantiates cleanly; all outputs lie strictly within $[0.065, 0.410]$.
- **Pass Criterion**: Zero out-of-bound predictions.

### VP-006: Autograd Space-Time PDE Residual Evaluation
- **Verifies**: FR-007, DI-003, IF-002
- **Setup**: `compute_richards_pde_residual` function.
- **Procedure**:
  1. Pass collocation coordinates $z, t$ with `requires_grad=True`.
  2. Evaluate autograd derivatives: $\frac{\partial \hat{\theta}}{\partial t}, \frac{\partial \hat{\theta}}{\partial z}, q, \frac{\partial q}{\partial z}$.
  3. Form $\mathcal{R}_{\text{PDE}} = \frac{\partial \hat{\theta}}{\partial t} + \frac{\partial q}{\partial z}$.
- **Expected Result**: Tuple `(pde_residual, theta_pred)` returned with matching shapes $(N, 1)$.
- **Pass Criterion**: Autograd graph retains second-order gradients without error.

### VP-007: Space-Time Collocation Sampling and Untrained Benchmark
- **Verifies**: FR-008, FR-009, DI-004, DI-005
- **Setup**: 1,500 collocation points generated via `generate_collocation_points(1500)`.
- **Procedure**:
  1. Evaluate untrained `pinn_model` on $z \in [0, 200\text{ cm}], t \in [0, 168\text{ hrs}]$.
  2. Calculate mean and max absolute PDE residuals.
- **Expected Result**:
  - Predicted moisture range: $0.2084$ to $0.3008\text{ m}^3/\text{m}^3$.
  - Mean PDE residual error: **0.001347**.
  - Max PDE residual error: **0.008327**.
- **Pass Criterion**: Metrics match logged execution baseline under seed 42.

### VP-008: Dirichlet Boundary Condition Tensor Formulation
- **Verifies**: FR-010, DI-006
- **Setup**: Function `generate_boundary_conditions(num_points=300)`.
- **Procedure**:
  1. Generate top boundary: $z_{\text{top}} = 0\text{ cm}$, $\theta_{\text{top}} = 0.35$.
  2. Generate bottom boundary: $z_{\text{bottom}} = 200\text{ cm}$, $\theta_{\text{bottom}} = 0.15$.
  3. Inspect tensor shapes and values.
- **Expected Result**: Tensors have shape $(300, 1)$; target values equal $0.35$ and $0.15$.
- **Pass Criterion**: Boundary parameters conform to specification.

### VP-009: Composite Multi-Objective Loss Evaluation
- **Verifies**: FR-011, IF-003
- **Setup**: `compute_composite_pinn_loss` function.
- **Procedure**:
  1. Evaluate composite loss with weights $(1.0, 0.1, 0.5)$.
  2. Assert total loss equals $0.1 \times \mathcal{L}_{\text{pde}} + 0.5 \times \mathcal{L}_{\text{bc}}$.
- **Expected Result**: Scalar losses emitted; values strictly non-negative.
- **Pass Criterion**: Loss components evaluate without NaN or infinite values.

### VP-010: 100-Epoch Optimization Loop & Loss Convergence
- **Verifies**: FR-012, FR-013, UQ-001, UQ-002
- **Setup**: Re-instantiated `PhysicsInformedNN`, Adam optimizer ($lr=1e-3$), 100 epochs.
- **Procedure**:
  1. Execute training loop with dynamic resampling (1,000 points) and `clip_grad_norm_`.
  2. Record loss trajectory at Epochs 1, 20, 40, 60, 80, 100.
- **Expected Result**:
  - Epoch 001: Total: **0.030035** | PDE: **0.000029** | BC: **0.060065**
  - Epoch 020: Total: **0.001248** | PDE: **0.000273** | BC: **0.002441**
  - Epoch 040: Total: **0.000052** | PDE: **0.000087** | BC: **0.000087**
  - Epoch 060: Total: **0.000046** | PDE: **0.000077** | BC: **0.000076**
  - Epoch 080: Total: **0.000019** | PDE: **0.000061** | BC: **0.000027**
  - Epoch 100: Total: **0.000027** | PDE: **0.000185** | BC: **0.000018**
- **Pass Criterion**: Total loss decreases from $0.0300$ to $< 0.0001$.

### VP-011: Physical Consistency Benchmark Evaluation
- **Verifies**: FR-014
- **Setup**: Unconstrained baseline model vs trained PINN evaluated on 1,200 unseen points.
- **Procedure**:
  1. Train unconstrained model on random targets for 100 epochs.
  2. Evaluate PDE residuals on unseen domain $z_{\text{eval}}, t_{\text{eval}}$.
  3. Compare mean absolute PDE residuals.
- **Expected Result**:
  - Unconstrained Baseline PDE Error: **0.003953**.
  - PINN (Richards-Constrained) Error: **0.004024**.
  - Residual Reduction: **-1.81%**.
- **Pass Criterion**: Audit records failure of narrative claim (>95% reduction) due to empirical result of -1.81%.

### VP-012: Continuous Moisture Diffusion Field Mesh & Plot 4
- **Verifies**: FR-015, IF-004, NF-003
- **Setup**: Regular meshgrid: $z \in [0, 200\text{ cm}]$ (100 steps), $t \in [0, 168\text{ hrs}]$ (100 steps).
- **Procedure**:
  1. Flatten meshgrid and evaluate `pinn_model`.
  2. Reshape predictions into $100 \times 100$ matrix.
  3. Render 2D space-time heatmap with inverted depth axis.
- **Expected Result**: Matrix shape $(100, 100)$; Min $\theta = 0.1456$, Max $\theta = 0.3510$. Surface mean $\approx 0.350$, Bottom mean $\approx 0.150$.
- **Pass Criterion**: Figure renders successfully; boundary targets satisfied.

---

## 7. Verification Results

Evidence tags:
- **`[NB]`**: Directly extracted from cell execution outputs in `05-physics-validation.ipynb`.
- **`[AN]`**: Independently re-calculated analytical verification.
- **`[INS]`**: Source code and parameter inspection.

| VP ID | Verification Target | Execution Date | Executor | Result | Empirical Evidence & Numerical Values | Reviewer |
|:---|:---|:---:|:---:|:---:|:---|:---:|
| **VP-001** | Hydraulic Parameters | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 04: $\theta_r=0.0650, \theta_s=0.4100, \alpha=0.0750, n=1.8900, m=0.4709, K_s=4.4200, l=0.5000$. | *Pending* |
| **VP-002** | Analytical Retention & Conductivity | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 06: $\psi \in [0.1, 10000.0]\text{ cm}$, $\theta \in [0.0660, 0.4100]\text{ m}^3/\text{m}^3$, $K \in [6.98 \times 10^{-13}, 4.31]\text{ cm/hr}$. | *Pending* |
| **VP-003** | Plot 1 Retention & Conductivity | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 08: PNG rendered (length: 137,428 bytes). Diagnostic overlay displayed. | *Pending* |
| **VP-004** | Differentiable PyTorch Operators | 2026-10-08 | Automated / G. Mohapatra | **PASS\*** | `[INS]` Cell 10: `torch_van_genuchten_k` operational. \*Defect D-001 noted (`tirch` typo in unused function). | *Pending* |
| **VP-005** | PINN Bounded Architecture | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 12: 4-layer MLP instantiated. Output bounded by Sigmoid scaling. | *Pending* |
| **VP-006** | Autograd PDE Residual Engine | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 14: *"Autograd PDE Residual Engine Compiled!"*. Second-order gradients verified. | *Pending* |
| **VP-007** | Untrained Residual Benchmark | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 18: Mean PDE Residual: **0.001347**, Max PDE Residual: **0.008327**. 1500 points. | *Pending* |
| **VP-008** | Dirichlet Boundary Tensors | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 20: Top ($z=0$ cm) Target: **0.35**, Bottom ($z=200$ cm) Target: **0.15**. | *Pending* |
| **VP-009** | Composite Loss Formulation | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 22: *"Composite Multi-Objective Physics Loss Function Initialized!"*. | *Pending* |
| **VP-010** | 100-Epoch Optimization Loop | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 24: Epoch 001 (**0.030035**) $\to$ Epoch 100 (**0.000027**). Total loss dropped by 3 orders of magnitude. | *Pending* |
| **VP-011** | Physical Consistency Benchmark | 2026-10-08 | Automated / G. Mohapatra | **FAIL\*** | `[NB]` Cell 29: Unconstrained: **0.003953**, PINN: **0.004024**, Reduction: **-1.81%**. Contradicts Cell 34 text (>95%). | *Pending* |
| **VP-012** | Continuous Diffusion Profile | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 31/33: Shape $(100, 100)$, $\theta \in [0.1456, 0.3510]$. PNG rendered (92,484 bytes). | *Pending* |

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
| **FR-001** | van Genuchten soil parameter dictionaries | Cell 04 | VP-001 | **PASS** |
| **FR-002** | Selection of active `sandy_loam` profile | Cell 04 | VP-001 | **PASS** |
| **FR-003** | NumPy closed-form SWRC & conductivity solvers | Cell 06 | VP-002 | **PASS** |
| **FR-004** | Continuous curve sampling across $\psi \in [0.1, 10000]\text{ cm}$ | Cell 06 | VP-002 | **PASS** |
| **FR-005** | Differentiable PyTorch hydraulic operators | Cell 10 | VP-004 | **PASS\*** |
| **FR-006** | 4-layer MLP `PhysicsInformedNN` with Sigmoid bounds | Cell 12 | VP-005 | **PASS** |
| **FR-007** | Autograd space-time PDE residual evaluator | Cell 14 | VP-006 | **PASS** |
| **FR-008** | Collocation domain point generator ($z \in [0, 200], t \in [0, 168]$) | Cell 16 | VP-007 | **PASS** |
| **FR-009** | Untrained forward pass PDE residual benchmark | Cell 18 | VP-007 | **PASS** |
| **FR-010** | Surface infiltration & deep drainage boundary tensors | Cell 20 | VP-008 | **PASS** |
| **FR-011** | Composite loss formulation ($\mathcal{L}_{\text{total}}$) | Cell 22 | VP-009 | **PASS** |
| **FR-012** | 100-epoch Adam optimization with gradient clipping | Cell 24 | VP-010 | **PASS** |
| **FR-013** | Log-scale convergence telemetry visualization | Cell 26 | VP-010 | **PASS** |
| **FR-014** | Benchmark against unconstrained neural baseline | Cell 29 | VP-011 | **FAIL\*** |
| **FR-015** | $100 \times 100$ continuous moisture diffusion mesh | Cells 31, 33 | VP-012 | **PASS** |
| **DI-001** | Output moisture bounded in $[\theta_r, \theta_s]$ | Cell 12 | VP-005 | **PASS** |
| **DI-002** | Clamped normalized saturation ($S_e$) in conductivity | Cells 06, 10 | VP-002, VP-004 | **PASS** |
| **DI-003** | Higher-order autograd graph retention | Cell 14 | VP-006 | **PASS** |
| **DI-004** | Collocation depth boundaries ($0 \le z \le 200\text{ cm}$) | Cell 16 | VP-007 | **PASS** |
| **DI-005** | Collocation temporal boundaries ($0 \le t \le 168\text{ hrs}$) | Cell 16 | VP-007 | **PASS** |
| **DI-006** | Non-negative boundary condition squared errors | Cell 22 | VP-009 | **PASS** |
| **IF-001** | PINN vector input-output dimension contract | Cell 12 | VP-005 | **PASS** |
| **IF-002** | PDE residual tuple return contract | Cell 14 | VP-006 | **PASS** |
| **IF-003** | Composite loss evaluator return contract | Cell 22 | VP-009 | **PASS** |
| **IF-004** | Moisture diffusion grid shape $(100, 100)$ | Cell 31 | VP-012 | **PASS** |
| **UQ-001** | Gradient norm clipping at threshold $1.0$ | Cell 24 | VP-010 | **PASS** |
| **UQ-002** | Dynamic collocation resampling per epoch | Cell 24 | VP-010 | **PASS** |
| **UQ-003** | High-precision metric reporting (6 decimal places) | Cells 18, 24, 29 | VP-007, VP-010, VP-011 | **PASS** |
| **NF-001** | Deterministic seed initialization (Torch 42, NumPy 42) | Cell 02 | VP-001 | **PASS** |
| **NF-002** | Unattended headless execution | All cells | Execution Audit | **PASS** |
| **NF-003** | Dark telemetry UI styling on generated figures | Cells 02, 08, 26, 33 | VP-003, VP-010, VP-012 | **PASS** |
| **NF-004** | Dynamic device selection (CUDA or CPU) | Cell 02 | VP-001 | **PASS** |

---

## 9. Configuration and Change Control

### 9.1 Controlled Items

The following items constitute the controlled configuration baseline for Notebook 05:
1. **Source Notebook**: `1_notebooks_sandbox/05-physics-validation.ipynb` (SHA-256 baseline hash required).
2. **Requirements & Verification Document (This Document)**: `8_docs/01_Notebooks/05. physics validation/05_physics_validation_REQUIREMENTS.md`.
3. **Companion Technical Description (Pending User Call)**: `8_docs/01_Notebooks/05. physics validation/05_physics_validation.rst`.
4. **Execution Environment**: Pinned Python environment with PyTorch 2.0+, SciPy, NumPy, Matplotlib.

### 9.2 Baseline Identification

- **Current Working Baseline**: `NB05-BL-01-DRAFT`
- **Target Release Baseline**: `NB05-BL-01`
- **Upstream Baseline**: `NB04-BL-01` (`convlstm_model_init.pt`)
- **Downstream Target Baseline**: `NB06-BL-01` (`06-state-estimation.ipynb` / EnKF assimilation)

### 9.3 Change Procedure

Any modification to hydraulic parameters, PDE residual formulations, autograd graphs, or loss weights shall adhere to the following control lifecycle:

```
[Change Request (CR)] 
        │
        ▼
[Impact Analysis on Hydraulic Consistency & EnKF Assimilation] 
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

1. **Cell Execution Integrity**: Cell execution counters and outputs shall be preserved matching the baseline hash or cleanly stripped before release.
2. **Deterministic Tensors**: Clean-kernel re-runs under seeds 42 shall produce identical training loss ($0.000027$ at Epoch 100).
3. **Requirement Atomicity**: Modifying a requirement mandates updating Sections 4, 5, 6, 7, and 8 concurrently.
4. **Deprecation**: Deprecated requirements shall be tagged `WITHDRAWN` and numerical IDs permanently reserved.

---

## 10. Open Defects and Discrepancies

| ID | Description | Affected Requirement | Severity | Status | Corrective Action |
|:---|:---|:---:|:---:|:---:|:---|
| **D-001** | **Typo in `torch_van_genuchten_theta` Function**: Line 249 contains `psi_abs = tirch.abs(psi) + 1e-6` (misspelling `tirch` instead of `torch`). The error was masked during notebook execution because this function is never called downstream. | FR-005 | **MEDIUM** | **OPEN** | Correct `tirch.abs` to `torch.abs` on line 249 of Cell 10. |
| **D-002** | **Narrative Benchmark Discrepancy**: Cell 34 text claims "Reduced physical residual error by >95% relative to unconstrained baseline models", but actual Cell 29 execution output shows: Baseline Error = 0.003953, PINN Error = 0.004024, **Reduction = -1.81%** (slight performance degradation). | FR-014, UQ-003 | **CRITICAL** | **OPEN** | Re-tune benchmark training or correct summary narrative to accurately state empirical findings. |
| **D-003** | **Simplified Darcy Flux Derivative Form**: In Cell 14, Darcy flux is formulated as $q = -K(\hat{\theta}) (\frac{\partial \hat{\theta}}{\partial z} + 1.0)$, substituting moisture gradient $\frac{\partial \theta}{\partial z}$ directly for matric potential gradient $\frac{\partial \psi}{\partial z}$, omitting the chain rule factor $\frac{\partial \psi}{\partial \theta} = \frac{1}{C(\psi)}$. | FR-007 | **HIGH** | **OPEN** | Implement the full hydraulic pressure head gradient $q = -K(\theta) (\frac{\partial \psi}{\partial z} + 1)$ via analytical differential capacity $C(\psi)$. |
| **D-004** | **Absence of Model Artifact Export**: Unlike Notebooks 01–04, Notebook 05 does not serialize its trained PINN weights (`pinn_model.state_dict()`) to `/data_processed/`, preventing offline loading by Notebook 06. | IF-003 | **MEDIUM** | **OPEN** | Add explicit `torch.save(pinn_model.state_dict(), 'pinn_richards_model.pt')` cell before completion. |
| **D-005** | **Decoupled Telemetry Ingestion**: Notebook 05 runs purely on synthetic space-time coordinates without ingesting `preprocessed_telemetry.csv` or ConvLSTM outputs from Notebook 04. | FR-008 | **HIGH** | **OPEN** | Couple surface boundary condition $\theta_{\text{top}}(t)$ directly to ingested Sentinel-1 SAR and rainfall time-series. |
| **D-006** | **Constant Boundary Conditions**: Surface infiltration ($0.35$) and deep drainage ($0.15$) are held static across all 168 hours, omitting dynamic monsoon precipitation wetting fronts. | FR-010 | **MEDIUM** | **OPEN** | Formulate time-varying Dirichlet boundary $\theta_{\text{top}}(t) = f(\text{Precipitation}_t)$. |

---

## 11. Risks and Assumptions

### 11.1 Technical Risks

| Risk ID | Risk Description | Severity | Likelihood | Consequence | Mitigation Strategy |
|:---|:---|:---:|:---:|:---|:---|
| **R-001** | **Misleading Physical Validation Claims** | Critical | High | Stating >95% error reduction when actual benchmark shows -1.81% undermines scientific credibility. | Enforce strict verification reporting matching empirical logged results; retrain baseline with proper regularization. |
| **R-002** | **Simplified Flux Approximation Error** | High | High | Omitting soil water capacity $C(\psi)$ in flux calculation distorts physical flow rates during dry conditions. | Implement full 1D mixed-form Richards PDE with analytical differential capacity. |
| **R-003** | **Vanishing Gradients in Higher-Order Autograd** | Moderate | Medium | Repeated `torch.autograd.grad` through $\operatorname{Tanh}$ and power functions can induce gradient decay or explosion. | Enforce gradient norm clipping and Xavier parameter initialization. |
| **R-004** | **Static Boundary Condition Artifacts** | Moderate | High | Constant surface moisture assumption prevents modeling rapid rainfall infiltration events. | Feed dynamic satellite weather telemetry into boundary condition tensors. |
| **R-005** | **Lack of Downstream Persistence** | Moderate | High | Unsaved neural weights mandate re-running 100-epoch training in all downstream notebooks. | Add persistent model serialization step. |

### 11.2 Architectural Assumptions

| Assumption ID | Statement of Assumption | Rationale |
|:---|:---|:---|
| **A-001** | **Vertical 1D Dominance** | Subsurface moisture flow in the vadose zone is dominated by vertical gravity and matric suction gradients, rendering lateral flux negligible. |
| **A-002** | **Isothermal Soil Column** | Soil temperature variations do not significantly alter hydraulic conductivity or matric suction over the 7-day window. |
| **A-003** | **Non-Hysterectic Soil Water Retention** | The wetting and drying branches of the SWRC are modeled by a single non-hysteretic van Genuchten curve. |
| **A-004** | **Homogeneous Soil Stratigraphy** | Soil hydraulic properties (`sandy_loam`) are uniform throughout the entire 200 cm vertical column without clay lenses or layering. |
| **A-005** | **Continuous Differentiability** | Soil moisture distribution $\theta(z, t)$ is continuously differentiable in space and time, satisfying requirements for autograd evaluation. |

---

## 12. Release and Baseline Acceptance Criteria

Notebook `05-physics-validation.ipynb` shall achieve formal release baseline `NB05-BL-01` only upon meeting all of the following criteria:

1. **Requirements Verification**: All Functional (FR), Data Integrity (DI), and Interface (IF) requirements verified as **MET** or formally **WAIVED**.
2. **Defect Remediation**: Resolution of Defect **D-001** (`tirch` typo) and reconciliation of Defect **D-002** (narrative benchmark discrepancy).
3. **Model Artifact Export**: Implementation of model checkpoint export (`pinn_richards_model.pt`) satisfying Defect **D-004**.
4. **Procedure Pass Rate**: 100% of Verification Procedures executed with **PASS** status.
5. **Full Traceability**: Complete bidirectional traceability maintained between requirements, code cells, and verification evidence.
6. **Independent Technical Review**: Formal review sign-off completed by an authorized independent authority.

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
> **SEPARATION OF PDE RESIDUAL MINIMIZATION AND IN-SITU HYDROLOGICAL ACCURACY**
> 
> Successful convergence of the PINN composite loss confirms that:
> 1. The neural network has learned a continuous surrogate function $\hat{\theta}(z, t)$ that satisfies the mathematical 1D Richards PDE residual to within $0.000185$ mean squared error.
> 2. Surface and bottom boundary targets ($\theta = 0.35$ and $\theta = 0.15$) are smoothly satisfied.
> 3. Space-time automatic differentiation executes without gradient explosions.
> 
> **THIS DOES NOT CONSTITUTE VALIDATION AGAINST REAL-WORLD GROUND TRUTH SOIL SENSORS.**
> 
> Because:
> - Soil hydraulic parameters represent USDA generic values rather than calibrated in-situ soil core retention curves from Bhadrak/Balasore.
> - Surface infiltration is modeled as a constant boundary rather than dynamic precipitation-driven flux.
> - Subsurface soil stratigraphy is assumed homogeneous, ignoring stratified clay-sand layering common in coastal Odisha.
> - Operational deployment requires calibration against in-situ capacitive soil moisture probes and meteorological rain gauges.

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

This document, the underlying software architecture, mathematical formalisms, physics-informed neural network implementations, and associated telemetry data structures constitute **proprietary intellectual property** developed under the auspices of JCC RS-SDA Division.

Unauthorized copying, distribution, decompilation, reverse engineering, dissemination, or commercial utilization—in whole or in part, in any format or medium—is strictly prohibited without prior express written authorization from the author and JCC Command Authority.

```
========================================================================================
                      CLASSIFICATION: STRICTLY PROPRIETARY & CONTROLLED
========================================================================================
```
