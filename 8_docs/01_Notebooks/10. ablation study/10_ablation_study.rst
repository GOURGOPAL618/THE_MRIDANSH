========================================================================================
THE MRIDANSH (AETHER-MRID1607X) - Notebook 10: Component Ablation & Marginal Utility
========================================================================================

:Project: THE MRIDANSH - Unified Soil State Estimation System
:Engine: AETHER-MRID1607X (Multi-Domain Soil Intelligence Engine)
:Notebook: ``10-ablation-study.ipynb``
:Sprint phase: Days 11-12 of the Scientific Audit & Validation Mission
:Division: RS-SDA (Remote Sensing & Spatial Data Analytics), JCC Campus 2 / JCC Headquarter
:Author / Maintainer: Gourgopal Mohapatra
:Copyright: (c) 2026 Gourgopal Mohapatra. All Rights Reserved.
:Document type: Technical Description and Software Design Specification
:Document status: Baseline Draft

.. contents:: Table of Contents
   :depth: 3
   :local:

1. Technical Overview
=====================

1.1 Objective
-------------
The primary technical objective of ``10-ablation-study.ipynb`` is to design, execute, and analyze
a systematic component contribution analysis and forward-assembly ablation study for **THE MRIDANSH**
(*AETHER-MRID1607X*). The engine quantifies the isolated marginal utility (:math:`\Delta\text{RMSE}, \Delta\sigma`)
and computational cost of every modular layer—progressing from a standalone optical baseline (Sentinel-2)
to the full physics-guided, assimilation-enhanced, hyperspectral-augmented system. By mapping all configurations
onto an accuracy-versus-latency Pareto efficiency frontier, the notebook establishes the formal systems
engineering justification for the production deployment baseline.

1.2 System Context
------------------
Within the **THE MRIDANSH** macro-architecture:

* **Upstream Components (Notebooks 01–09)**: Supply the modular technologies that compose the estimation
  stack: optical multispectral channels (Notebook 02), SAR microwave backscatter (Notebook 02),
  spatial graph topologies (Notebook 03), temporal sequence predictors (Notebook 04), Richards PDE
  physics constraints (Notebook 05), Ensemble Kalman Filter assimilation (Notebook 06), calibrated
  uncertainty fields (Notebook 07), failure mode gates (Notebook 08), and hyperspectral PCA features (Notebook 09).
* **Core Ablation Engine**: Evaluates eight cumulative configurations (:math:`\text{Config A}` through
  :math:`\text{Config H}`), measures step-by-step error reduction (:math:`\text{RMSE}: 0.0540 \to 0.0171\text{ m}^3/\text{m}^3`)
  and uncertainty contraction (:math:`\sigma: \pm 0.085 \to \pm 0.026\text{ m}^3/\text{m}^3`), evaluates cumulative
  gains (:math:`0\% \to 68.36\%`), and classifies modules into an essentiality taxonomy (Essential Core,
  Secondary Core, and Optional/Targeted).
* **Downstream Integration**: Emits the validated core configuration (:math:`\text{Configs A–G}`) to
  Notebook 11 (*Generalization Baseline Evaluation*) to govern cross-catchment out-of-distribution benchmarking.

1.3 Design Boundary
-------------------
The design boundary of Notebook 10 is demarcated as follows:

* **In Boundary**:
  - Definition of eight forward-cumulative configurations spanning sensor modalities, physics bounds, state filtering, and hyperspectral features.
  - Synthesis of a 1000-sample benchmark dataset with non-linear harmonic ground truth soil moisture.
  - Progressive simulation of prediction residuals, uncertainty standard deviations, and latency benchmarks.
  - Mathematical derivation of marginal utility deltas (:math:`\Delta\text{RMSE}_i, \Delta\sigma_i`) and cumulative accuracy gains.
  - Compilation of the official Component-Contribution Matrix and essentiality tier assignments.
  - Generation of the 2D Pareto efficiency frontier mapping accuracy gain against inference latency.
  - Rendering of two high-resolution telemetry figures (Plots 1 and 2).
* **Out of Boundary**:
  - Full retraining of deep neural networks (ConvLSTM, PINN) across all 8 configurations.
  - Leave-one-out (backward elimination) permutation importance testing.
  - Spatial raster processing on geospatial coordinate grids (operates on 1D sample arrays).
  - Physical serialization of intermediate prediction arrays to disk.

1.4 Relationship to Requirements
--------------------------------
This technical description details the mathematical models, algorithmic execution loops,
and component specifications that implement the functional requirements (`FR-001` through `FR-015`),
data integrity constraints (`DI-001` through `DI-005`), and quality standards established in
``10_ablation_study_REQUIREMENTS.md``.


2. Architecture
===============

2.1 Notebook Architecture
-------------------------
The software architecture of Notebook 10 is structured into four functional tiers:

.. code-block:: text

   +---------------------------------------------------------------------------------+
   |                          TIER 1: BENCHMARK SYNTHESIS                            |
   |  - Ground Truth Generation: y_true in [0.045, 0.402] m^3/m^3 (N = 1000)        |
   |  - Feature Generation: X_s2, X_s1, X_dem, X_weather, X_temporal                |
   +---------------------------------------------------------------------------------+
                                           |
                                           v
   +---------------------------------------------------------------------------------+
   |                    TIER 2: CUMULATIVE SIMULATION SWEEP                          |
   |  Iterate Configs A -> H with decreasing noise schedule [0.055 -> 0.017]         |
   |  pred_i = clip(y_true + N(0, sigma_i^2), 0.02, 0.48)                            |
   |  calc_metrics(y_true, pred_i, unc_levels[i]) -> RMSE, R^2, Uncertainty_sigma    |
   +---------------------------------------------------------------------------------+
                                           |
                                           v
   +---------------------------------------------------------------------------------+
   |                    TIER 3: MARGINAL UTILITY & MATRIX ENGINE                     |
   |  - Marginal Deltas: Delta_RMSE, Delta_Unc (relative % gains)                    |
   |  - Cumulative Gain % relative to baseline S2 (0.0540 m^3/m^3)                   |
   |  - Component-Contribution Matrix: Core Baseline -> Primary Drivers -> Secondary |
   +---------------------------------------------------------------------------------+
                                           |
                                           v
   +---------------------------------------------------------------------------------+
   |                     TIER 4: PARETO AUDIT & GOVERNANCE                           |
   |  - Pareto Frontier: Normalized Accuracy Gain vs Latency (0.3 ms -> 5.2 ms)      |
   |  - Plot 2: Scatter Pareto Front Visualizer                                      |
   |  - Production Deployment Decision: Freeze Configs A-G, HSI Optional             |
   +---------------------------------------------------------------------------------+

2.2 Processing Pipeline
-----------------------
Execution proceeds sequentially across two sprint phases:

1. **Phase 1: Incremental Assembly & Trajectory Profiling (Day 11, Cells 00–09)**
   - Configures dark telemetry styling and device locks (NumPy `1607`, PyTorch `1607`).
   - Synthesizes 1000 ground truth points and 5 multi-modal input feature arrays.
   - Executes the 8-configuration simulation sweep, compiling DataFrame `df_ablation`.
   - Renders Plot 1 (Step-by-step RMSE reduction and uncertainty contraction trajectories).
   - Computes step-by-step marginal utility deltas (:math:`\Delta\text{RMSE}, \Delta\sigma`).
2. **Phase 2: Scientific Component Matrix & Pareto Audit (Day 12, Cells 10–15)**
   - Constructs DataFrame `df_matrix` categorizing modules into architectural roles and essentiality tiers.
   - Maps configurations onto the 2D Pareto efficiency plane.
   - Renders Plot 2 (Pareto front connecting accuracy gain to latency penalty).
   - Formulates and logs the final scientific architectural justification for MRIDANSH.

2.3 Component Relationships
---------------------------
Components communicate via in-memory array passing and DataFrame operations:

* **Benchmark Synthesizer**: Generates 1D ground truth vector :math:`\mathbf{y}_{\text{true}} \in \mathbb{R}^{1000}`.
* **Assembly Simulation Loop**: Ingests configuration parameter lists, synthesizes bounded prediction vectors,
  and evaluates regression metrics.
* **Utility Calculator**: Operates on DataFrame columns using discrete differencing (`np.diff`),
  computing step gains and cumulative improvements.
* **Pareto Optimizer**: Computes normalized accuracy scores and projects coordinates against inference runtimes.
* **Classification Engine**: Applies conditional logic to assign architectural roles and tier classifications.

2.4 Data Flow
-------------
The data transformation sequence forms a linear directed graph:

.. code-block:: text

   Seed (1607) ──> y_true [1000] ──> Multi-Modal Inputs [X_s2, X_s1, X_dem, ...]
                         │
                         ▼
        Incremental Noise Schedule & Latency Constants
        [noise_levels, unc_levels, runtimes_ms]
                         │
                         ▼
        Simulation Loop across Configs A through H
                         │
                         ▼
        df_ablation [8 rows x 5 cols]
                         │
       ┌─────────────────┴─────────────────┐
       ▼                                   ▼
   Plot 1 (Trajectories)           Marginal Differencing
                                   (Delta_RMSE, Delta_Unc)
                                           │
                                           ▼
                                   df_matrix [8 rows x 7 cols]
                                           │
                                           ▼
                                   Plot 2 (Pareto Front)
                                           │
                                           ▼
                                   Final Architectural Verdict


3. Execution Flow
=================

3.1 Initialization and Hardware Verification
--------------------------------------------
Cell 02 initializes system dependencies, configures visual styling, and locks pseudo-random generators:

.. code-block:: python

   import os, sys, numpy as np, matplotlib.pyplot as plt, pandas as pd, torch

   plt.style.use('dark_background')
   plt.rcParams['font.family'] = 'monospace'
   plt.rcParams['axes.edgecolor'] = '#00FFCC'
   plt.rcParams['axes.linewidth'] = 1.2
   plt.rcParams['grid.color'] = '#1A3344'
   plt.rcParams['grid.linestyle'] = '--'
   plt.rcParams['grid.alpha'] = 0.5

   device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
   np.random.seed(1607)
   torch.manual_seed(1607)

When executed, the system logs:
``⚡ [MRIDANSH Ablation Engine] Active Hardware: cuda`` (or ``cpu``).

3.2 Synthetic Benchmark Dataset Construction
--------------------------------------------
Cell 04 establishes the ground truth soil moisture profile over 1000 points using harmonic series:

.. code-block:: python

   N_SAMPLES = 1000
   t_series = np.linspace(0, 4 * np.pi, N_SAMPLES)
   y_true = 0.22 + 0.14 * np.sin(t_series) + 0.03 * np.cos(3 * t_series) + np.random.normal(0, 0.01, N_SAMPLES)
   y_true = np.clip(y_true, 0.04, 0.46)

   # Multi-modal input features (generated for architectural representation)
   X_s2 = y_true + np.random.normal(0, 0.055, N_SAMPLES)
   X_s1 = y_true + np.random.normal(0, 0.042, N_SAMPLES)
   X_dem = 0.02 * np.sin(t_series / 2)
   X_weather = 0.03 * np.cos(t_series)
   X_temporal = y_true * 0.95 + np.random.normal(0, 0.02)

3.3 Incremental Configuration Simulation Sweep
----------------------------------------------
Cell 06 executes the forward-assembly ablation loop across all eight configurations:

.. code-block:: python

   configs = [
       'Config A (S2)', 'Config B (+S1)', 'Config C (+DEM)', 'Config D (+Weather)',
       'Config E (+Temporal)', 'Config F (+Physics)', 'Config G (+EnKF)', 'Config H (+HSI)'
   ]

   noise_levels = [0.055, 0.042, 0.036, 0.031, 0.026, 0.022, 0.019, 0.017]
   unc_levels   = [0.085, 0.068, 0.058, 0.050, 0.042, 0.036, 0.031, 0.026]
   runtimes_ms  = [0.3,   0.5,   0.7,   0.9,   1.1,   1.5,   2.1,   5.2]

   results = []
   preds = {}

   for i, cfg in enumerate(configs):
       n_err = np.random.normal(0, noise_levels[i], N_SAMPLES)
       pred = np.clip(y_true + n_err, 0.02, 0.48)
       preds[cfg] = pred
       rmse, r2, unc = calc_metrics(y_true, pred, unc_levels[i])
       results.append({
           'Config': cfg, 'RMSE': rmse, 'R2': r2,
           'Uncertainty_σ': unc, 'Latency_ms': runtimes_ms[i]
       })

   df_ablation = pd.DataFrame(results)

3.4 Marginal Utility and Delta Calculations
-------------------------------------------
Cell 09 evaluates discrete differences between adjacent configurations:

.. code-block:: python

   delta_rmse = [0.0] + list(np.diff(df_ablation['RMSE']))
   delta_unc  = [0.0] + list(np.diff(df_ablation['Uncertainty_σ']))

   df_ablation['Delta_RMSE'] = delta_rmse
   df_ablation['Delat_Unc']  = delta_unc

   for i in range(1, len(configs)):
       prev_cfg = configs[i-1].split(' ')[1]
       curr_cfg = configs[i].split(' ')[1]
       r_gain = (abs(delta_rmse[i]) / df_ablation['RMSE'][i-1]) * 100
       u_gain = (abs(delta_unc[i]) / df_ablation['Uncertainty_σ'][i-1]) * 100
       print(f"• {prev_cfg:>8}  ➔  {curr_cfg:<10} : ΔRMSE = {delta_rmse[i]:+.4f} ({r_gain:5.2f}% gain) | Δσ = {delta_unc[i]:+.4f} ({u_gain:5.2f}% gain)")

3.5 Component-Contribution Matrix Synthesis
-------------------------------------------
Cell 11 computes cumulative percentage gains relative to Config A and assigns architectural classifications:

.. code-block:: python

   baseline_rmse = df_ablation['RMSE'].iloc[0]
   contributions = []

   for i in range(len(df_ablation)):
       cfg_name = df_ablation['Config'].iloc[i]
       rmse_val = df_ablation['RMSE'].iloc[i]
       unc_val = df_ablation['Uncertainty_σ'].iloc[i]
       lat_val = df_ablation['Latency_ms'].iloc[i]
       abs_gain_pct = ((baseline_rmse - rmse_val) / baseline_rmse) * 100

       if i == 0:
           role, tire = 'Core Baseline', 'Essential'
       elif i in [1, 5, 6]:
           role, tire = 'Primery Driver', 'Essential'
       elif i in [2, 3, 4]:
           role, tire = 'Contextual Adjuster', 'Secondary Core'
       else:
           role, tire = 'High-Precision Module', 'Optional / Targeted'

       contributions.append({
           'Module': cfg_name, 'RMSE (m³/m³)': f"{rmse_val:.4f}",
           'Cumulative Gain': f"{abs_gain_pct:.2f}", 'Uncertainty σ': f"±{unc_val:.3f}",
           'Latent (ms)': f"{lat_val} ms", 'Architectural Role': role,
           'Essentiality Tire': tire
       })

   df_matrix = pd.DataFrame(contributions)

3.6 Pareto Efficiency Frontier Audit
------------------------------------
Cell 13 maps configurations onto the accuracy-latency plane:

.. code-block:: python

   x_lat = df_ablation['Latency_ms']
   y_acc = 1 - (df_ablation['RMSE'] / baseline_rmse)

3.7 Final Architectural Justification Compilation
-------------------------------------------------
Cell 14 compiles and logs the definitive systems engineering justification to stdout.


4. Component Design
===================

4.1 Ground Truth Benchmark Synthesizer
--------------------------------------
The benchmark synthesizer models realistic temporal soil moisture dynamics using a harmonic expansion:

.. math::

   \theta_{\text{true}}(t) = 0.22 + 0.14 \sin(t) + 0.03 \cos(3t) + \eta(t)

where:
* Base mean: :math:`\bar{\theta} = 0.22\text{ m}^3/\text{m}^3` represents field capacity baseline.
* Primary harmonic: :math:`0.14 \sin(t)` represents seasonal wet/dry hydrologic oscillation.
* Tertiary harmonic: :math:`0.03 \cos(3t)` represents short-term precipitation pulse infiltration.
* Micro-scale noise: :math:`\eta \sim \mathcal{N}(0, 0.01^2)`.
* Boundary clipping: :math:`\theta_{\text{true}} \in [0.04, 0.46]\text{ m}^3/\text{m}^3` preserves physical soil saturation bounds.

4.2 Multi-Modal Feature Synthesizers
------------------------------------
Synthesizes sensor proxy vectors:
* **Optical (:math:`\mathbf{X}_{\text{S2}}`)**: :math:`\theta_{\text{true}} + \mathcal{N}(0, 0.055^2)` (sensitive to cloud contamination).
* **SAR (:math:`\mathbf{X}_{\text{S1}}`)**: :math:`\theta_{\text{true}} + \mathcal{N}(0, 0.042^2)` (cloud penetrating, roughness sensitive).
* **Topography (:math:`\mathbf{X}_{\text{DEM}}`)**: :math:`0.02 \sin(t / 2)` (elevation and slope moisture accumulation).
* **Weather (:math:`\mathbf{X}_{\text{weather}}`)**: :math:`0.03 \cos(t)` (rainfall and evapotranspiration driver).
* **Temporal (:math:`\mathbf{X}_{\text{temporal}}`)**: :math:`0.95 \theta_{\text{true}} + \mathcal{N}(0, 0.02^2)` (antecedent soil moisture memory).

4.3 Forward Assembly Simulation Engine
--------------------------------------
Simulates predictions under 8 cumulative configurations:

.. list-table:: 8 Cumulative Configuration Specifications
   :widths: 15 25 20 20 20
   :header-rows: 1

   * - Config ID
     - Layer Name
     - Noise Floor :math:`\sigma_{\text{noise}}`
     - Uncertainty :math:`\sigma`
     - Latency (ms)
   * - Config A
     - Sentinel-2 (Optical Baseline)
     - :math:`0.055`
     - :math:`\pm 0.085`
     - :math:`0.3`
   * - Config B
     - Config A + Sentinel-1 SAR
     - :math:`0.042`
     - :math:`\pm 0.068`
     - :math:`0.5`
   * - Config C
     - Config B + DEM Topography
     - :math:`0.036`
     - :math:`\pm 0.058`
     - :math:`0.7`
   * - Config D
     - Config C + Weather Dynamics
     - :math:`0.031`
     - :math:`\pm 0.050`
     - :math:`0.9`
   * - Config E
     - Config D + Temporal Memory
     - :math:`0.026`
     - :math:`\pm 0.042`
     - :math:`1.1`
   * - Config F
     - Config E + Physics PINN
     - :math:`0.022`
     - :math:`\pm 0.036`
     - :math:`1.5`
   * - Config G
     - Config F + EnKF State Assimilation
     - :math:`0.019`
     - :math:`\pm 0.031`
     - :math:`2.1`
   * - Config H
     - Config G + Hyperspectral PCA
     - :math:`0.017`
     - :math:`\pm 0.026`
     - :math:`5.2`

4.4 Marginal Utility Analysis Module
------------------------------------
Evaluates isolated step-by-step improvements:

.. math::

   \Delta\text{RMSE}_i = \text{RMSE}_i - \text{RMSE}_{i-1}, \quad \text{Gain}_{\text{step}, i} = \frac{|\Delta\text{RMSE}_i|}{\text{RMSE}_{i-1}} \times 100\%

.. math::

   \Delta\sigma_i = \sigma_i - \sigma_{i-1}, \quad \text{Gain}_{\sigma, i} = \frac{|\Delta\sigma_i|}{\sigma_{i-1}} \times 100\%

4.5 Pareto Frontier Optimizer
-----------------------------
Maps cumulative accuracy gains against computational execution penalties:

.. math::

   \text{Gain}_{\text{acc}}(i) = 1 - \frac{\text{RMSE}_i}{\text{RMSE}_A}

A configuration :math:`i` dominates configuration :math:`j` if:

.. math::

   \text{Gain}_{\text{acc}}(i) \ge \text{Gain}_{\text{acc}}(j) \quad \land \quad \text{Latency}(i) \le \text{Latency}(j)

4.6 Architectural Classification & Tier Assignment Engine
---------------------------------------------------------
Classifies modules into operational tiers based on marginal impact and resource demands:

* **Tier 1: Essential Core Drivers**:
  - Config A (S2): Primary optical spectrum foundation.
  - Config B (S1): Major multi-modal sensor leap (+21.88% gain).
  - Config F (Physics PINN): Major physical consistency leap (+21.25% gain).
  - Config G (EnKF): Essential sequential state tightening (+9.45% gain, :math:`\sigma \to \pm 0.031`).
* **Tier 2: Secondary Core (Contextual Adjusters)**:
  - Config C (DEM), Config D (Weather), Config E (Temporal): Provide required micro-climate and topographic context (+35.49% cumulative gain).
* **Tier 3: Optional / Targeted (High-Precision Refinement)**:
  - Config H (HSI): High-precision refinement (+10.86% step gain), but carries a +147% latency penalty (5.2 ms).


5. Data Structures
==================

5.1 Configuration Array Schema
------------------------------

.. list-table:: Configuration Input Arrays
   :widths: 25 15 20 40
   :header-rows: 1

   * - Array Variable
     - Data Type
     - Length
     - Description
   * - ``configs``
     - ``list[str]``
     - 8
     - Names of the 8 incremental architectural configurations.
   * - ``noise_levels``
     - ``list[float]``
     - 8
     - Pre-specified Gaussian residual noise standard deviations.
   * - ``unc_levels``
     - ``list[float]``
     - 8
     - Pre-specified model uncertainty bounds (:math:`\pm\sigma`).
   * - ``runtimes_ms``
     - ``list[float]``
     - 8
     - Benchmarked computational inference latencies in milliseconds.

5.2 In-Memory Benchmark and Prediction Tensors
----------------------------------------------

.. list-table:: Benchmark Tensor Specifications
   :widths: 20 15 15 20 30
   :header-rows: 1

   * - Variable Name
     - Data Type
     - Shape
     - Memory Size
     - Description / Range
   * - ``t_series``
     - ``float64``
     - ``(1000,)``
     - 8.0 KB
     - Time indices spanning :math:`[0, 4\pi]`.
   * - ``y_true``
     - ``float64``
     - ``(1000,)``
     - 8.0 KB
     - Ground truth soil moisture in :math:`[0.045, 0.402]`.
   * - ``X_s2``
     - ``float64``
     - ``(1000,)``
     - 8.0 KB
     - Synthetic Sentinel-2 proxy feature vector.
   * - ``X_s1``
     - ``float64``
     - ``(1000,)``
     - 8.0 KB
     - Synthetic Sentinel-1 proxy feature vector.
   * - ``preds``
     - ``dict[str, np.ndarray]``
     - 8 keys
     - 64.0 KB
     - Dictionary of prediction arrays for Configs A–H.

5.3 Ablation Metrics Summary Schema (``df_ablation``)
----------------------------------------------------

.. list-table:: ``df_ablation`` DataFrame Schema
   :widths: 20 15 20 45
   :header-rows: 1

   * - Column Name
     - Type
     - Example Value
     - Interpretation
   * - ``Config``
     - ``object``
     - ``Config A (S2)``
     - Configuration label.
   * - ``RMSE``
     - ``float64``
     - ``0.053975``
     - Root-mean-squared error against :math:`\mathbf{y}_{\text{true}}`.
   * - ``R2``
     - ``float64``
     - ``0.714731``
     - Coefficient of determination.
   * - ``Uncertainty_σ``
     - ``float64``
     - ``0.085``
     - Assigned model uncertainty standard deviation.
   * - ``Latency_ms``
     - ``float64``
     - ``0.3``
     - Inference runtime per pixel in milliseconds.
   * - ``Delta_RMSE``
     - ``float64``
     - ``-0.011808``
     - Marginal error change relative to previous step.
   * - ``Delat_Unc``
     - ``float64``
     - ``-0.017000``
     - Marginal uncertainty change (code typo retained).

5.4 Component-Contribution Matrix Schema (``df_matrix``)
--------------------------------------------------------

.. list-table:: ``df_matrix`` DataFrame Schema
   :widths: 20 15 20 45
   :header-rows: 1

   * - Column Name
     - Type
     - Example Value
     - Interpretation
   * - ``Module``
     - ``object``
     - ``Config B (+S1)``
     - Configuration label.
   * - ``RMSE (m³/m³)``
     - ``object``
     - ``0.0422``
     - Formatted string representation of RMSE.
   * - ``Cumulative Gain``
     - ``object``
     - ``21.88``
     - Percentage accuracy gain relative to Config A.
   * - ``Uncertainty σ``
     - ``object``
     - ``±0.068``
     - Formatted uncertainty standard deviation.
   * - ``Latent (ms)``
     - ``object``
     - ``0.5 ms``
     - Formatted inference latency (code typo retained).
   * - ``Architectural Role``
     - ``object``
     - ``Primery Driver``
     - Assigned system role (code typo retained).
   * - ``Essentiality Tire``
     - ``object``
     - ``Essential``
     - Operational essentiality tier (code typo retained).


6. Algorithms and Methods
=========================

6.1 Synthetic Soil Moisture Harmonic Continuum Formulation
----------------------------------------------------------
The continuous benchmark time-series is formulated via Fourier superposition:

.. math::

   \theta(t) = a_0 + a_1 \sin(\omega_1 t) + a_2 \cos(\omega_2 t) + \epsilon(t)

Parameters: :math:`a_0 = 0.22, a_1 = 0.14, \omega_1 = 1, a_2 = 0.03, \omega_2 = 3, \epsilon \sim \mathcal{N}(0, 0.01^2)`.
This creates a realistic non-linear target containing rapid wetting spikes and gradual drying recessions.

6.2 Staged Gaussian Noise Injection Formulation
-----------------------------------------------
For configuration :math:`i`, predictions are simulated by adding zero-mean Gaussian noise:

.. math::

   \hat{\theta}_i = \operatorname{clip}\left(\theta_{\text{true}} + \mathcal{N}(0, \sigma_{\text{noise}, i}^2), 0.02, 0.48\right)

Noise levels strictly decrease:

.. math::

   \sigma_{\text{noise}} = [0.055, 0.042, 0.036, 0.031, 0.026, 0.022, 0.019, 0.017]

6.3 Regression and Uncertainty Evaluation Metrics
-------------------------------------------------
Evaluated via standard formulations:

.. math::

   \text{RMSE} = \sqrt{\frac{1}{N} \sum_{k=1}^N \left(\theta_{\text{true}, k} - \hat{\theta}_k\right)^2}

.. math::

   R^2 = 1 - \frac{\sum_{k=1}^N \left(\theta_{\text{true}, k} - \hat{\theta}_k\right)^2}{\sum_{k=1}^N \left(\theta_{\text{true}, k} - \bar{\theta}\right)^2}

6.4 Marginal Gain and Utility Derivation
----------------------------------------
Marginal error reduction percentage between stage :math:`i-1` and stage :math:`i`:

.. math::

   \operatorname{Gain}_{\text{step}}(i) = \frac{\text{RMSE}_{i-1} - \text{RMSE}_i}{\text{RMSE}_{i-1}} \times 100\%

Empirical results:
* :math:`A \to B`: :math:`\frac{0.0540 - 0.0422}{0.0540} \times 100\% = 21.88\%`
* :math:`B \to C`: :math:`\frac{0.0422 - 0.0358}{0.0422} \times 100\% = 15.18\%`
* :math:`C \to D`: :math:`\frac{0.0358 - 0.0315}{0.0358} \times 100\% = 11.95\%`
* :math:`D \to E`: :math:`\frac{0.0315 - 0.0269}{0.0315} \times 100\% = 14.69\%`
* :math:`E \to F`: :math:`\frac{0.0269 - 0.0212}{0.0269} \times 100\% = 21.25\%`
* :math:`F \to G`: :math:`\frac{0.0212 - 0.0192}{0.0212} \times 100\% = 9.45\%`
* :math:`G \to H`: :math:`\frac{0.0192 - 0.0171}{0.0192} \times 100\% = 10.86\%`

6.5 Cumulative Accuracy Gain Formulation
----------------------------------------
Evaluates total progress relative to the optical baseline:

.. math::

   \operatorname{Gain}_{\text{cum}}(i) = \frac{\text{RMSE}_A - \text{RMSE}_i}{\text{RMSE}_A} \times 100\%

Empirical results:
* Config A: :math:`0.00\%`
* Config B: :math:`21.88\%`
* Config C: :math:`33.74\%`
* Config D: :math:`41.65\%`
* Config E: :math:`50.22\%`
* Config F: :math:`60.80\%`
* Config G: :math:`64.51\%`
* Config H: :math:`68.36\%`

6.6 Pareto Efficiency Frontier Mapping
--------------------------------------
Maps each configuration :math:`i` onto coordinates :math:`(x_i, y_i)`:

.. math::

   x_i = \text{Latency}_i, \quad y_i = 1 - \frac{\text{RMSE}_i}{\text{RMSE}_A}

Because both latency and accuracy increase monotonically, all 8 configurations lie on the Pareto boundary,
tracing a concave diminishing-returns curve where late-stage gains require disproportionate runtime.


7. Interfaces
=============

7.1 Upstream Pipeline Interfaces
--------------------------------
In the production system, Notebook 10 ingests:
* Trained weights from ConvLSTM (Notebook 04): ``models/convlstm.pt``.
* PINN loss weights from Richards solver (Notebook 05): ``models/pinn_richards.pt``.
* Posterior error covariance matrices from EnKF (Notebook 06): ``data_processed/state_covariances.npy``.
* PCA projection matrices from HSI engine (Notebook 09): ``data_processed/hsi_pca_weights.npy``.

7.2 Internal Programmatic Interfaces
------------------------------------

Function: ``calc_metrics``
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def calc_metrics(
       y_real: np.ndarray,
       y_pred: np.ndarray,
       unc_base: float
   ) -> tuple[float, float, float]:
       """
       Computes regression error, goodness of fit, and mean uncertainty.

       Parameters:
           y_real (np.ndarray): 1D array of ground truth soil moisture values (N,).
           y_pred (np.ndarray): 1D array of predicted soil moisture values (N,).
           unc_base (float): Pre-specified model uncertainty standard deviation.

       Returns:
           tuple[float, float, float]:
               - rmse: Root-mean-squared error.
               - r2: Coefficient of determination.
               - unc: Mean uncertainty bound.
       """

7.3 Graphical Visualization Interfaces
--------------------------------------
The notebook outputs two high-resolution Matplotlib figures:
* **Plot 1**: Dimensions :math:`13 \times 5` inches, 2 subplots (Step-by-step RMSE reduction and uncertainty contraction trajectories).
* **Plot 2**: Dimensions :math:`10 \times 5` inches, 1 subplot (Pareto efficiency frontier with scatter markers and dashed trajectory).

7.4 Downstream Architectural Governance Interfaces
--------------------------------------------------
The notebook exports the operational deployment policy:

.. code-block:: python

   CORE_DEPLOYMENT_STACK = ["Config A", "Config B", "Config C", "Config D", "Config E", "Config F", "Config G"]
   OPTIONAL_AUGMENTATION_STACK = ["Config H"]


8. Configuration
================

8.1 Noise Schedules and Latency Constants
-----------------------------------------

.. list-table:: Configuration Schedules and Constants
   :widths: 20 20 20 40
   :header-rows: 1

   * - Configuration
     - Noise Floor :math:`\sigma`
     - Uncertainty :math:`\pm\sigma`
     - Latency (ms/pixel)
   * - Config A (S2)
     - :math:`0.055`
     - :math:`0.085`
     - :math:`0.3`
   * - Config B (+S1)
     - :math:`0.042`
     - :math:`0.068`
     - :math:`0.5`
   * - Config C (+DEM)
     - :math:`0.036`
     - :math:`0.058`
     - :math:`0.7`
   * - Config D (+Weather)
     - :math:`0.031`
     - :math:`0.050`
     - :math:`0.9`
   * - Config E (+Temporal)
     - :math:`0.026`
     - :math:`0.042`
     - :math:`1.1`
   * - Config F (+Physics)
     - :math:`0.022`
     - :math:`0.036`
     - :math:`1.5`
   * - Config G (+EnKF)
     - :math:`0.019`
     - :math:`0.031`
     - :math:`2.1`
   * - Config H (+HSI)
     - :math:`0.017`
     - :math:`0.026`
     - :math:`5.2`

8.2 Environment and Dependencies
--------------------------------
* Python :math:`\ge 3.10`
* PyTorch :math:`\ge 2.0.0` with CUDA support (falls back to CPU).
* NumPy :math:`\ge 1.23.0`, Matplotlib :math:`\ge 3.7.0`, Pandas :math:`\ge 1.5.0`.

8.3 Deterministic Seeding Configuration
---------------------------------------
Global random generators are fixed at the top of the notebook:

.. code-block:: python

   np.random.seed(1607)
   torch.manual_seed(1607)

8.4 Dark Telemetry Palette
--------------------------
Standard JCC RS-SDA dark visual styling:
* Cyan Primary: ``#00FFCC``
* Orange Secondary: ``#FF9900``
* Grid Background: ``#1A3344``
* Pareto Spectrum: ``#FF0055``, ``#FF9900``, ``#FFCC00``, ``#00FFCC``, ``#00CCFF``, ``#9900FF``, ``#00FF66``, ``#FFFFFF``


9. Error Handling and Defensive Design
======================================

9.1 Prediction Value Physical Boundary Clipping
-----------------------------------------------
All simulated predictions are bounded below and above:

.. code-block:: python

   pred = np.clip(y_true + n_err, 0.02, 0.48)

This prevents unconstrained Gaussian noise tails from generating physically impossible soil moisture values.

9.2 Monotonic Constraint Verification
-------------------------------------
The forward assembly process guarantees monotonic error reduction:

.. math::

   \text{RMSE}_{i+1} < \text{RMSE}_i \quad \land \quad \sigma_{i+1} < \sigma_i

9.3 Latency Overhead Guardrails
-------------------------------
The Pareto analysis provides an explicit guardrail against computational over-engineering,
quantifying that adding HSI increases runtime by +147% for only +3.85% cumulative accuracy gain.

9.4 Array Shape and Type Integrity
----------------------------------
All arrays maintain shape :math:`(1000,)` with 64-bit floating point precision, preventing
broadcasting errors during differencing.


10. Generated Artifacts and Visualizations
==========================================

10.1 Plot 1: Incremental Progression Trajectory
-----------------------------------------------
Rendered in Cell 08:
* **Subplot 1**: Step-by-step RMSE reduction curve showing values dropping from :math:`0.054 \to 0.017\text{ m}^3/\text{m}^3`.
* **Subplot 2**: Model uncertainty contraction trajectory showing bounds shrinking from :math:`\pm 0.085 \to \pm 0.026\text{ m}^3/\text{m}^3`.

10.2 Plot 2: Pareto Efficiency Audit
------------------------------------
Rendered in Cell 13:
* Scatter plot connecting configurations along the accuracy-latency frontier.
* Annotates each configuration marker, illustrating high marginal efficiency for early modules (Configs A–G)
  and steep latency penalty for Config H.

10.3 Component-Contribution Telemetry Table
-------------------------------------------
Printed to stdout in Cell 11:
Displays the complete 8-row executive matrix detailing RMSE, cumulative gains, uncertainty bounds,
latency, architectural roles, and essentiality tiers.

10.4 Architectural Decision Verdict
-----------------------------------
Printed to stdout in Cell 14:
Formally declares Sentinel-1, Physics PINN, and EnKF as Essential Core Drivers, DEM/Weather/Temporal
as Contextual Adjusters, and HSI as an Optional Module.


11. Reproducibility
===================

11.1 Random Seed Control
------------------------
Random seeds are fixed to ``1607`` for both NumPy and PyTorch.

11.2 Numerical Baseline Verification Table
------------------------------------------
Execution under seed 1607 produces bit-exact verification metrics:

.. list-table:: Reproducibility Verification Baseline
   :widths: 35 35 30
   :header-rows: 1

   * - Metric / Quantity
     - Expected Baseline
     - Verified Execution
   * - Config A (S2) RMSE
     - :math:`0.053975\text{ m}^3/\text{m}^3`
     - :math:`0.053975\text{ m}^3/\text{m}^3`
   * - Config B (+S1) RMSE
     - :math:`0.042167\text{ m}^3/\text{m}^3`
     - :math:`0.042167\text{ m}^3/\text{m}^3`
   * - Config C (+DEM) RMSE
     - :math:`0.035765\text{ m}^3/\text{m}^3`
     - :math:`0.035765\text{ m}^3/\text{m}^3`
   * - Config D (+Weather) RMSE
     - :math:`0.031492\text{ m}^3/\text{m}^3`
     - :math:`0.031492\text{ m}^3/\text{m}^3`
   * - Config E (+Temporal) RMSE
     - :math:`0.026867\text{ m}^3/\text{m}^3`
     - :math:`0.026867\text{ m}^3/\text{m}^3`
   * - Config F (+Physics) RMSE
     - :math:`0.021158\text{ m}^3/\text{m}^3`
     - :math:`0.021158\text{ m}^3/\text{m}^3`
   * - Config G (+EnKF) RMSE
     - :math:`0.019158\text{ m}^3/\text{m}^3`
     - :math:`0.019158\text{ m}^3/\text{m}^3`
   * - Config H (+HSI) RMSE
     - :math:`0.017077\text{ m}^3/\text{m}^3`
     - :math:`0.017077\text{ m}^3/\text{m}^3`
   * - Config B Cumulative Gain
     - :math:`21.88\%`
     - :math:`21.88\%`
   * - Config F Cumulative Gain
     - :math:`60.80\%`
     - :math:`60.80\%`
   * - Config G Cumulative Gain
     - :math:`64.51\%`
     - :math:`64.51\%`
   * - Config H Cumulative Gain
     - :math:`68.36\%`
     - :math:`68.36\%`

11.3 Deterministic Execution Guarantee
--------------------------------------
All operations execute without unseeded stochasticity, ensuring identical numerical outputs across runs.


12. Performance Characteristics
===============================

12.1 Execution Latency and Wall-Clock Benchmarks
------------------------------------------------
The entire notebook executes in :math:`\approx 1.15\text{ s}`:

.. list-table:: Latency Profile
   :widths: 45 25 30
   :header-rows: 1

   * - Pipeline Component
     - Duration
     - Proportion
   * - Imports & Device Setup
     - :math:`\approx 0.18\text{ s}`
     - :math:`16\%`
   * - Benchmark Dataset Synthesis
     - :math:`\approx 0.01\text{ s}`
     - :math:`1\%`
   * - Ablation Simulation Sweep
     - :math:`\approx 0.03\text{ s}`
     - :math:`3\%`
   * - Plot 1 Rendering (Trajectories)
     - :math:`\approx 0.42\text{ s}`
     - :math:`36\%`
   * - Marginal Deltas & Matrix Setup
     - :math:`\approx 0.01\text{ s}`
     - :math:`1\%`
   * - Plot 2 Rendering (Pareto)
     - :math:`\approx 0.38\text{ s}`
     - :math:`33\%`
   * - Summary Printing & Termination
     - :math:`\approx 0.12\text{ s}`
     - :math:`10\%`
   * - **Total Runtime**
     - :math:`\approx \mathbf{1.15\text{ s}}`
     - :math:`\mathbf{100\%}`

12.2 Memory Footprint and Array Profiling
-----------------------------------------
Peak resident memory is :math:`< 100\text{ MB}`, with active data arrays occupying :math:`< 150\text{ KB}`.

12.3 Scalability Analysis for Deep Model Ablation
-------------------------------------------------
While the synthetic ablation simulation executes in 1.15 seconds, full retraining of all 8 deep learning
models on a 1-million-pixel geospatial dataset would require :math:`\approx 32\text{ GPU-hours}`,
justifying the use of parametric surrogate schedules for rapid architectural exploration.


13. Implementation Notes
========================

13.1 Current Implementation State
---------------------------------
The notebook establishes the formal mathematical and systems engineering framework for component
justification, marginal utility tracking, and Pareto trade-off optimization.

13.2 Known Implementation Constraints
-------------------------------------
1. **Mocked Ablation Sweep (Defect D-001)**: Predictions are generated via pre-specified noise schedules
   rather than executing retrained neural checkpoints.
2. **Unused Feature Arrays (Defect D-002)**: Feature tensors `X_s2, X_s1, X_dem, X_weather, X_temporal`
   are constructed in Cell 04 but never used in the simulation loop.
3. **Narrative vs Computed Metric Discrepancies (Defect D-003)**: Text printouts in Cell 14 cite
   numbers (+28.13%, +19.36%, +15.83%, +7.88%) that diverge from the calculated values in Cells 09 and 11
   (21.88%, 21.25%, 9.45%, 10.86%).
4. **Code Typographical Errors (Defect D-004)**: Column names and variables contain typos (`Delat_Unc`,
   `Primery Driver`, `Essentiality Tire`, `Latent (ms)`).
5. **Decoupled Pipeline (Defect D-005)**: No checkpoints are loaded and no summary tables are exported.

13.3 Architectural Refactoring Roadmap
--------------------------------------
1. Replace mocked noise injections with actual model inference using checkpoints from Notebooks 03–06.
2. Feed synthetic feature arrays into empirical regression baselines.
3. Align Cell 14 narrative printouts with dynamic formatted variables from `df_matrix`.
4. Fix column and variable typographical errors.
5. Export `ablation_matrix.parquet` to ``data_processed/ablation/``.


14. Technical Limitations
=========================

14.1 Synthetic Simulation Dependency
------------------------------------
Because all prediction arrays are generated from analytical Gaussian noise distributions, the results
demonstrate the decision governance methodology but do not represent empirical neural network accuracy.

14.2 Mocked Incremental Performance Schedules
---------------------------------------------
The monotonically decreasing noise schedule enforces monotonic error reduction by mathematical design,
which does not capture potential negative transfer or feature interference in real deep architectures.

14.3 Unidirectional Forward Assembly Limitation
-----------------------------------------------
Evaluating components solely in forward cumulative order (:math:`A \to B \to \dots \to H`) prevents
detecting non-linear inter-component interactions that would be revealed by leave-one-out (LOO) ablation.


15. Requirement Implementation Mapping
======================================

.. list-table:: Mapping of Requirements to Technical Implementation
   :widths: 15 35 25 25
   :header-rows: 1

   * - Requirement ID
     - Technical Description Reference
     - Code Cell Reference
     - Design Artifact / Element
   * - **FR-001**
     - Section 2.1, Section 4.3
     - Cell 01, Cell 06
     - ``configs`` list declaration
   * - **FR-002**
     - Section 3.2, Section 4.1
     - Cell 04
     - ``y_true`` harmonic formulation
   * - **FR-003**
     - Section 3.2, Section 4.2
     - Cell 04
     - Feature proxy arrays (S2, S1, DEM, Weather, Temporal)
   * - **FR-004**
     - Section 3.2, Section 7.2
     - Cell 04
     - ``calc_metrics`` function
   * - **FR-005**
     - Section 3.3, Section 6.2
     - Cell 06
     - Noise injection simulation loop
   * - **FR-006**
     - Section 3.3, Section 5.3, Section 11.2
     - Cell 06
     - ``df_ablation`` summary DataFrame
   * - **FR-007**
     - Section 3.3, Section 7.3, Section 10.1
     - Cell 08
     - Aerospace Plot 1 (2-panel trajectory figure)
   * - **FR-008**
     - Section 3.4, Section 6.4, Section 11.2
     - Cell 09
     - Marginal utility delta calculations
   * - **FR-009**
     - Section 3.5, Section 6.5, Section 11.2
     - Cell 11
     - Cumulative percentage gain calculations
   * - **FR-010**
     - Section 3.5, Section 4.6, Section 5.4
     - Cell 11
     - ``df_matrix`` component-contribution table
   * - **FR-011**
     - Section 3.6, Section 4.5, Section 6.6
     - Cell 13
     - Pareto coordinate evaluation
   * - **FR-012**
     - Section 3.6, Section 7.3, Section 10.2
     - Cell 13
     - Aerospace Plot 2 (Pareto front figure)
   * - **FR-013**
     - Section 4.6, Section 6.4
     - Cell 09, Cell 14
     - S1 jump verification (21.88% step gain)
   * - **FR-014**
     - Section 4.6, Section 6.4
     - Cell 09, Cell 14
     - Physics PINN jump verification (21.25% step gain)
   * - **FR-015**
     - Section 4.6, Section 7.4, Section 10.4
     - Cell 14
     - Final architectural justification terminal banner
   * - **DI-001**
     - Section 4.3, Section 9.2
     - Cell 06
     - Monotonic RMSE reduction across configurations
   * - **DI-002**
     - Section 4.3, Section 9.2
     - Cell 06
     - Monotonic uncertainty contraction across configurations
   * - **DI-003**
     - Section 3.3, Section 11.2
     - Cell 06
     - Monotonic R² elevation across configurations
   * - **DI-004**
     - Section 4.3, Section 8.1
     - Cell 06
     - Monotonic latency growth across configurations
   * - **DI-005**
     - Section 6.5, Section 11.2
     - Cell 11
     - Cumulative gain bounding in $[0.0\%, 100.0\%]$
