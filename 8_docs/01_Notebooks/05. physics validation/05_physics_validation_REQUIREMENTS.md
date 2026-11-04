# 🛰️ THE MRIDANSH: PHYSICS-INFORMED VALIDATION & RICHARDS' PDE ENGINE
## Engineering Requirements, Verification Procedures & Scientific Traceability Specification
### Module ID: `MRIDANSH-MOD-PHYSICS-05` | Notebook: `05-physics-validation.ipynb`

---

## 1. System Context & Operational Architecture

Module 05 implements the differentiable physical validation engine of **THE MRIDANSH**. Operating downstream of temporal sequence modeling (`04-temporal-modeling`), it constrains neural hydrological predictions to obey fundamental soil-water mass conservation and Darcy-Buckingham unsaturated fluid mechanics. Utilizing the van Genuchten-Mualem constitutive relationships and continuous automatic differentiation (PyTorch autograd), this module trains a Physics-Informed Neural Network (PINN) to solve the 1D mixed-form Richards partial differential equation (PDE) across a 2-meter soil vertical profile ($z \in [0, 200\text{ cm}]$) over a 7-day post-storm infiltration window ($t \in [0, 168\text{ hrs}]$).

```
+----------------------------------------------------------------------------------------------------+
|                                    UPSTREAM ARTIFACT INGESTION                                     |
|  - Telemetry: 5_storage/notebook_results/notebook_02_preprocessing/preprocessed_telemetry.csv       |
|  - Temporal Latent: 5_storage/notebook_results/notebook_04_temporal_modeling/convlstm_model_init.pt|
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 1. Constitutive Soil-Water Relations: van Genuchten (1980) & Mualem (1976)                         |
|    - Active Profile: Regional Odisha Loam (theta_r=0.078, theta_s=0.430, alpha=0.036, n=1.56)     |
|    - Soil Water Retention Curve (SWRC): theta(psi) and Hydraulic Conductivity K(theta)             |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 2. Continuous Space-Time Domain Collocation:                                                       |
|    - Depth domain: z in [0, 200 cm] | Time domain: t in [0, 168 hrs] (1500 interior points)        |
|    - Top Boundary (z=0): Ingested telemetry moisture proxy                                         |
|    - Bottom Boundary (z=200 cm): Deep asymptotic gravity drainage                                 |
|    - Initial Condition (t=0): Equilibrium hydrostatic capillary moisture profile                   |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 3. Physics-Informed Neural Network (PINN) Core:                                                    |
|    - MLP Architecture: 4 hidden layers x 64 units, Tanh activations                                |
|    - Bounded Output: theta_hat = theta_r + (theta_s - theta_r) * Sigmoid(z_net)                    |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 4. PyTorch Autograd Richards PDE Residual Evaluation:                                              |
|    - Mass Conservation: dtheta/dt + dq/dz = 0                                                      |
|    - Darcian Flux with Gravity Head: q = -K(theta) * (dtheta/dz + 1.0)                             |
|    - Loss: L_total = L_pde + lambda_top * L_top + lambda_bot * L_bot + lambda_ic * L_ic            |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 5. Benchmark Physical Consistency Audit:                                                           |
|    - PINN vs Purely Data-Driven Unconstrained Baseline                                             |
|    - Requirement: Physical PDE residual reduction >= 70.0%                                         |
|    - Invariant: pinn_mean_err < 0.001 cm3/cm3/hr                                                   |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 6. Multi-Tier Checkpointing & Manifest Export:                                                     |
|    - 5_storage/checkpoints/pinn_richards_model.pt & PINN_RICHARDS_MODEL_MANIFEST.md                |
|    - 5_storage/notebook_results/notebook_05_physics_validation/pinn_physics_metrics.json           |
|    - Mirrors in data/processed/ (Ready for EnKF assimilation in Notebook 06)                       |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Functional Requirements (FR)

### FR-PHYSICS-001: Soil-Water Constitutive Parameter Definition
The system **SHALL** maintain standard USDA soil hydraulic parameter sets and activate the regional Odisha catchment profile:
- Active Soil: `loam`
- Residual moisture: $\theta_r = 0.078\text{ cm}^3/\text{cm}^3$
- Saturated moisture: $\theta_s = 0.430\text{ cm}^3/\text{cm}^3$
- Air-entry scale parameter: $\alpha = 0.036\text{ cm}^{-1}$
- Pore-size distribution index: $n = 1.56$
- Mualem parameter: $m = 1.0 - \frac{1.0}{n} = 0.3590$
- Saturated hydraulic conductivity: $K_s = 1.04\text{ cm/hr}$
- Tortuosity parameter: $l = 0.5$

### FR-PHYSICS-002: Analytical SWRC & Hydraulic Conductivity Evaluation
The system **SHALL** implement analytical forward solvers for soil water retention:
$$\Theta(h) = \left[ 1 + (\alpha |h|)^n \right]^{-m}$$
$$\theta(h) = \theta_r + (\theta_s - \theta_r) \cdot \Theta(h)$$
and relative hydraulic conductivity:
$$K(\Theta) = K_s \cdot \Theta^l \cdot \left[ 1 - (1 - \Theta^{1/m})^m \right]^2$$
evaluated across matric suction $h \in [0.1, 10000]\text{ cm}$.

### FR-PHYSICS-003: Differentiable PyTorch Soil Physics Operators
The system **SHALL** implement PyTorch tensor-compatible functions `torch_van_genuchten_theta` and `torch_van_genuchten_k` with numerical epsilon clamping ($S_e \in [10^{-6}, 1.0 - 10^{-6}]$) to prevent gradient divergence during backpropagation.

### FR-PHYSICS-004: Continuous Space-Time PINN Surrogate Architecture
The system **SHALL** construct a deep multi-layer perceptron (`PhysicsInformedNN`):
- Input: $(z, t) \in \mathbb{R}^{N \times 2}$ (depth in cm, time in hours).
- Hidden layers: 4 dense layers, 64 neurons per layer, $\tanh$ activation functions.
- Output activation: Sigmoid mapping ensuring strict adherence to physical moisture boundaries:
  $$\hat{\theta}(z, t) = \theta_r + (\theta_s - \theta_r) \cdot \sigma\left(W_{\text{out}} h^{(4)} + b_{\text{out}}\right)$$

### FR-PHYSICS-005: Autograd Richards' PDE Residual Formulation
The system **SHALL** compute exact first-order and second-order space-time partial derivatives via automatic differentiation with graph retention (`create_graph=True`):
1. Temporal derivative: $\frac{\partial \theta}{\partial t} = \operatorname{autograd}(\hat{\theta}, t)$
2. Spatial moisture gradient: $\frac{\partial \theta}{\partial z} = \operatorname{autograd}(\hat{\theta}, z)$
3. Unsaturated Darcian flux with gravitational head:
   $$q = -K(\hat{\theta}) \cdot \left( \frac{\partial \theta}{\partial z} + 1.0 \right)$$
4. Flux divergence: $\frac{\partial q}{\partial z} = \operatorname{autograd}(q, z)$
5. Continuity mass conservation residual:
   $$\mathcal{R}_{\text{PDE}} = \frac{\partial \theta}{\partial t} + \frac{\partial q}{\partial z}$$

### FR-PHYSICS-006: Space-Time Boundary Ingestion & Collocation
The system **SHALL** establish:
- Interior collocation: $N_{\text{colloc}} = 1500$ points uniformly distributed over $z \in [0, 200\text{ cm}]$, $t \in [0, 168\text{ hrs}]$.
- Top boundary ($z=0\text{ cm}$): Ingests preprocessed telemetry moisture proxy from Notebook 02.
- Bottom boundary ($z=200\text{ cm}$): Deep asymptotic drainage target ($\theta \approx \theta_r + 0.05$).
- Initial condition ($t=0\text{ hr}$): Hydrostatic capillary equilibrium.

### FR-PHYSICS-007: Composite Loss Optimization & Gradient Stability
The system **SHALL** train the PINN using composite multi-objective loss:
$$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{PDE}} + \lambda_{\text{top}} \mathcal{L}_{\text{top}} + \lambda_{\text{bot}} \mathcal{L}_{\text{bot}} + \lambda_{\text{IC}} \mathcal{L}_{\text{IC}}$$
over 100 epochs using Adam ($\text{lr} = 10^{-3}$) with gradient norm clipping ($\text{max\_norm} = 1.0$).

### FR-PHYSICS-008: Physical Consistency Benchmark Against Unconstrained Baseline
The system **SHALL** instantiate and train a purely data-driven unconstrained baseline network (lacking PDE loss) and compare PDE residual errors on unseen test collocation points:
- Invariant: PINN physical residual reduction rate **SHALL** exceed $70.0\%$:
  $$\frac{\text{MSE}_{\text{unconstrained}} - \text{MSE}_{\text{PINN}}}{\text{MSE}_{\text{unconstrained}}} \times 100\% \ge 70.0\%$$
- Invariant: Mean absolute PINN PDE residual **SHALL** be strictly $< 0.001\text{ cm}^3/\text{cm}^3/\text{hr}$.

### FR-PHYSICS-009: Multi-Tier Checkpointing & Production Manifest Export
The system **SHALL** export:
1. Production checkpoint `pinn_richards_model.pt` to `5_storage/checkpoints/` (mirrored in `5_storage/notebook_results/notebook_05_physics_validation/` and `data/processed/`).
2. Model manifest markdown `PINN_RICHARDS_MODEL_MANIFEST.md` to `5_storage/checkpoints/`.
3. Metrics summary `pinn_physics_metrics.json` to `5_storage/notebook_results/notebook_05_physics_validation/`.

---

## 3. Data Integrity & Physical Bounding Requirements (DI)

- **DI-PHYSICS-001 (Physical Volumetric Moisture Bounds)**: Predicted moisture strictly bounded: $\hat{\theta} \in [\theta_r - 0.05, \theta_s + 0.05]$.
- **DI-PHYSICS-002 (Collocation Spatial Bounds)**: Depth domain $z \in [0.0, 200.0\text{ cm}]$.
- **DI-PHYSICS-003 (Collocation Temporal Horizon)**: Temporal simulation domain $t \in [0.0, 168.0\text{ hrs}]$.
- **DI-PHYSICS-004 (Continuous Grid Resolution)**: Evaluated 2D moisture profile matrix $\Theta \in \mathbb{R}^{100 \times 100}$.
- **DI-PHYSICS-005 (Model Weight Finiteness)**: All checkpointed parameter tensors must contain 0 NaNs and 0 Infs.

---

## 4. Verification Procedures (VP) & Acceptance Test Suite

The verification suite `tests/test_notebook_05_verification.py` executes 7 strict automated tests:

| Test ID | Procedure Description | Acceptance Criteria | Verified Result |
| :--- | :--- | :--- | :--- |
| **VP-PHYSICS-01** | `test_01_no_python_scripts_in_notebook_dir` | Directory `1_notebooks_sandbox/` contains 0 `.py` scripts | **PASSED** |
| **VP-PHYSICS-02** | `test_02_notebook_cell_structure_and_markdown_rules` | Notebook length $\ge 30$ cells; every code cell preceded by markdown | **PASSED** (36 cells) |
| **VP-PHYSICS-03** | `test_03_all_code_cells_executed_with_zero_errors` | Exactly 16 code cells; all executed; zero error outputs | **PASSED** (16/16 executed) |
| **VP-PHYSICS-04** | `test_04_penultimate_and_ultimate_markdown_cells` | Penultimate contains Executive Summary; Ultimate contains IP notice | **PASSED** |
| **VP-PHYSICS-05** | `test_05_storage_artifacts_and_plots_persisted` | 5 plots (>50KB) and metrics JSON exist in storage | **PASSED** |
| **VP-PHYSICS-06** | `test_06_checkpoint_and_manifest_compliance` | Checkpoint and manifest exist in `5_storage/checkpoints/` with dual persistence; `soil_class == "loam"`; `pde_reduction_pct >= 70%` | **PASSED** |
| **VP-PHYSICS-07** | `test_07_richards_physics_consistency_and_mass_conservation` | PINN error $< 0.001$, reduction $\ge 70\%$, moisture strictly bounded in $[\theta_r - 0.05, \theta_s + 0.05]$ | **PASSED** |

---

## 5. Aerospace Artifact Inventory

The following files are permanently stored in `5_storage/notebook_results/notebook_05_physics_validation/` and `5_storage/checkpoints/`:

| Artifact Name | Storage Path | Type | Size | Description |
| :--- | :--- | :--- | :--- | :--- |
| `plot_01_van_genuchten_swrc_conductivity.png` | `notebook_05_physics_validation/` | PNG (120 DPI) | ~115 KB | Logarithmic suction curves for SWRC $\theta(\psi)$ and unsaturated conductivity $K(\theta)$. |
| `plot_02_pinn_space_time_collocation_mesh.png` | `notebook_05_physics_validation/` | PNG (120 DPI) | ~197 KB | Space-time $(z, t)$ scatter mesh with telemetry-derived Dirichlet boundary conditions. |
| `plot_03_pinn_loss_convergence_trajectory.png` | `notebook_05_physics_validation/` | PNG (120 DPI) | ~86 KB | Semi-log convergence plot of total composite, PDE residual, and boundary condition losses. |
| `plot_04_pinn_vs_unconstrained_pde_residuals.png` | `notebook_05_physics_validation/` | PNG (120 DPI) | ~108 KB | Comparative residual error histograms confirming $>70\%$ violation reduction over unconstrained model. |
| `plot_05_continuous_soil_diffusion_profile.png` | `notebook_05_physics_validation/` | PNG (120 DPI) | ~100 KB | Continuous 2D vertical moisture infiltration diffusion contour map ($100 \times 100$ grid). |
| `pinn_richards_model.pt` | `checkpoints/` & dual mirrors | PyTorch | ~56 KB | Production PINN model checkpoint bundle (architecture, state dict, soil parameters). |
| `PINN_RICHARDS_MODEL_MANIFEST.md` | `checkpoints/` | Markdown | ~1.2 KB | Human- and agent-readable model manifest defining coordinates, governing equations, and lineage. |
| `pinn_physics_metrics.json` | `notebook_05_physics_validation/` | JSON | 591 Bytes | Quantitative validation metrics (errors, reduction rate, physical moisture limits). |

---

## 6. Traceability Matrix

| Requirement | Notebook 05 Code Cell | Verification Test | Storage Artifact |
| :--- | :--- | :--- | :--- |
| **FR-PHYSICS-001** | Cell 5 | `test_06_checkpoint_and_manifest_compliance` | `pinn_richards_model.pt` (`soil_params`) |
| **FR-PHYSICS-002** | Cell 7, 9 | `test_05_storage_artifacts_and_plots_persisted` | `plot_01_van_genuchten_swrc_conductivity.png` |
| **FR-PHYSICS-003** | Cell 11 | `test_03_all_code_cells_executed_with_zero_errors` | Notebook runtime kernel |
| **FR-PHYSICS-004** | Cell 13 | `test_06_checkpoint_and_manifest_compliance` | `pinn_richards_model.pt` |
| **FR-PHYSICS-005** | Cell 15 | `test_07_richards_physics_consistency_and_mass_conservation` | `pinn_physics_metrics.json` |
| **FR-PHYSICS-006** | Cell 17, 19 | `test_05_storage_artifacts_and_plots_persisted` | `plot_02_pinn_space_time_collocation_mesh.png` |
| **FR-PHYSICS-007** | Cell 21, 23 | `test_05_storage_artifacts_and_plots_persisted` | `plot_03_pinn_loss_convergence_trajectory.png` |
| **FR-PHYSICS-008** | Cell 25, 27 | `test_07_richards_physics_consistency_and_mass_conservation` | `plot_04_pinn_vs_unconstrained_pde_residuals.png` |
| **FR-PHYSICS-009** | Cell 29, 31, 33 | `test_06_checkpoint_and_manifest_compliance` | `plot_05_continuous_soil_diffusion_profile.png`, `PINN_RICHARDS_MODEL_MANIFEST.md` |

---

## 7. Brutally Unfiltered Defect Log & Engineering Limitations

| Defect ID | Severity | Subsystem | Description & Root Cause | Impact & Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| `D-NB05-001` | **HIGH** | Richards Operator | **Simplified Darcian Flux Formulation**: The PDE residual engine models flux as $q = -K(\theta)(\frac{\partial \theta}{\partial z} + 1)$ rather than evaluating the matric potential gradient $q = -K(\theta)(\frac{\partial \psi}{\partial z} + 1) = -D(\theta)\frac{\partial \theta}{\partial z} - K(\theta)$ with soil water diffusivity $D(\theta) = K(\theta) \frac{d\psi}{d\theta}$. | Matric capillary suction is linearized directly across moisture space, which slightly overestimates hydraulic flux in dry soil regimes ($\psi > 1000\text{ cm}$). Mitigation: Implement full $D(\theta)$ autograd chain in production kernel. |
| `D-NB05-002` | **HIGH** | Hydraulic Subgrade | **Homogeneous Loam Subgrade Idealization**: The model assumes a single homogeneous loam layer across the entire $2\text{ m}$ soil depth profile, neglecting vertical stratigraphy, clay accumulation horizons ($B_t$ horizon), and root zone macropores. | Rapid preferential fissure flow during heavy monsoon downpours is not captured by matrix flow equations alone. Mitigation: Model multi-layer soil stratigraphy with dual-permeability macropore mechanics. |
| `D-NB05-003` | **MEDIUM** | Spatial Domain | **1D Vertical Infiltration vs 2D Catchment Interflow**: The PINN evaluates infiltration as an isolated 1D vertical column ($z, t$), omitting lateral downslope interflow and subsurface saturation excess runoff. | Subsurface water movement between adjacent grid cells on steep slopes is neglected in this stage. Mitigation: Hand off 1D vertical profile to Notebook 06 where Ensemble Kalman Filtering couples 2D GCN representations with 1D vertical physics. |
| `D-NB05-004` | **LOW** | Boundary Linkage | **Telemetry Surface Moisture Proxy**: Top surface boundary moisture $\theta_{\text{top}}(t)$ is mapped from optical/SAR telemetry using an uncalibrated linear proxy rather than verified in-situ TDR sensor measurements. | Surface boundary values carry unquantified systematic offset relative to ground truth. Mitigation: Assimilate ground truth station observations via kalman update steps in Module 06. |

---

## 8. Configuration Control & Environment Lineage

- **Parent Repository**: `THE_MRIDANSH`
- **Execution Python**: Python 3.12.10 (virtual environment `mridansh_env`, PyTorch 2.14.0+cpu, SciPy 1.15.2)
- **Primary Inputs**: `5_storage/notebook_results/notebook_02_preprocessing/preprocessed_telemetry.csv`, `5_storage/notebook_results/notebook_04_temporal_modeling/convlstm_model_init.pt`
- **Primary Checkpoint**: `5_storage/checkpoints/pinn_richards_model.pt`
- **Manifest Target**: `5_storage/checkpoints/PINN_RICHARDS_MODEL_MANIFEST.md`
- **Verification Command**: `pytest tests/test_notebook_05_verification.py -v`
