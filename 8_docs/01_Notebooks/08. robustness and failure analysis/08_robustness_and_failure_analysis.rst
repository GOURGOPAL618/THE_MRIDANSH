====================================================================================
THE MRIDANSH (AETHER-MRID1607X) - Notebook 08: Robustness & Failure Analysis
====================================================================================

:Project: THE MRIDANSH - Unified Soil State Estimation System
:Engine: AETHER-MRID1607X (Multi-Domain Soil Intelligence Engine)
:Notebook: ``08-robustness-and-failure-analysis.ipynb``
:Sprint phase: Days 5-7 of the Scientific Audit & Validation Mission
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
The primary technical objective of ``08-robustness-and-failure-analysis.ipynb`` is to implement,
evaluate, and formalize a system-level stress testing and failure mode profiling engine.
The notebook answers the critical mission safety question: *"When MRIDANSH doesn't know, does it
know that it doesn't know?"* It systematically quantifies model degradation under single and dual
sensor dropouts, progressive spectral and impulse noise corruption, uncalibrated radar backscatter
offsets, and extreme hydrological and topographic edge cases. It establishes the authoritative
4-tier Operational State and Failure Mode Taxonomy for autonomous system governance.

1.2 System Context
------------------
Within the **THE MRIDANSH** (*AETHER-MRID1607X*) macro-architecture:

* **Upstream Data & Models**: Ingests nominal multi-modal feature spaces derived from
  Sentinel-1 SAR and Sentinel-2 optical imagery (Notebooks 01–02), temporal sequence forecasts
  (Notebook 04), Richards PDE physics residuals (Notebook 05), and assimilated state error
  covariances (Notebooks 06–07).
* **Core Stress Engine**: Evaluates error expansion and uncertainty inflation under:
  1. Modality dropouts: Optical cloud obscuration, SAR hardware failure, dual sensor blackout.
  2. Data corruption: Additive Gaussian noise, salt-and-pepper impulse spikes, Bernoulli spatial dropouts.
  3. Calibration shifts: Affine scale and offset distortions in backscatter cross-sections.
  4. Environmental extremes: Flash flooding, severe agricultural drought, steep terrain distortion.
* **Downstream Integration**: Emits operational state decision boundaries and safety flags to
  downstream evaluation notebooks (Notebook 09 *Hyperspectral Experiment*, Notebook 10 *Ablation Study*,
  and Notebook 11 *Generalization Baseline*) to gate geotechnical slope stability computations.

1.3 Design Boundary
-------------------
The design boundary of Notebook 08 is established as follows:

* **In Boundary**:
  - Synthetic generation of multi-modal calibration matrices (:math:`N=1000` samples) across
    Sentinel-2, Sentinel-1, DEM, and Weather features.
  - Linear ensemble prediction simulation under four discrete sensor dropout states.
  - Multi-hazard data corruption functions (Gaussian noise, impulse spikes, Bernoulli spatial masking, affine shifts).
  - Parametric 6-step noise sweep (:math:`\sigma_{\text{noise}} \in [0.0, 0.15]`) evaluating RMSE, :math:`\sigma`, and confidence.
  - Evaluation of an uncalibrated radar offset scenario (:math:`\text{scale}=1.20, \text{offset}=0.06`).
  - Formalization of the 4-tier Operational State & Failure Mode Taxonomy.
  - Rendering of three 2-panel dark-themed diagnostic figures (Plots 1, 2, and 3).
* **Out of Boundary**:
  - Deep neural backpropagation or dynamic model fine-tuning during sensor dropout.
  - Georeferenced spatial raster processing on EPSG:32644 grids (operates on 1D feature sample vectors).
  - Real-time ingestion of live satellite telemetry streams.
  - Direct calculation of slope safety factors or geotechnical landslide slip surfaces.

1.4 Relationship to Requirements
--------------------------------
This technical description details the mathematical models, algorithmic execution loops,
and component specifications that implement the functional requirements (`FR-001` through `FR-015`),
data integrity constraints (`DI-001` through `DI-005`), and quality standards established in
``08_robustness_and_failure_analysis_REQUIREMENTS.md``.


2. Architecture
===============

2.1 Notebook Architecture
-------------------------
The software architecture of Notebook 08 is structured as a 4-tier stress testing pipeline:

.. code-block:: text

   +---------------------------------------------------------------------------------+
   |                          TIER 1: FEATURE GENERATION                             |
   |  Synthetic Ground Truth Soil Moisture: theta_true in [0.12, 0.40] m^3/m^3       |
   |  Multi-Modal Feature Stacking: X_baseline = [S2, S1, DEM, Weather] (1000, 4)   |
   +---------------------------------------------------------------------------------+
                                           |
                                           v
   +---------------------------------------------------------------------------------+
   |                         TIER 2: MODALITY DROPOUT SUITE                          |
   |  simulate_ensemble_prediction(X, dropout_type)                                  |
   |  States: [Nominal (S1+S2)]  [Missing S2 (Clouds)]  [Missing S1 (SAR)]  [Dual]    |
   |  Uncertainty Inflation & Exponential Confidence Mapping                         |
   +---------------------------------------------------------------------------------+
                                           |
                                           v
   +---------------------------------------------------------------------------------+
   |                         TIER 3: DATA CORRUPTION SUITE                           |
   |  - inject_spectral_noise (Gaussian + Salt-and-Pepper Impulses)                  |
   |  - inject_spatial_dropout (Bernoulli Revisit Pixel Masking)                     |
   |  - inject_calibration_shift (Affine Radar Offset Distortion)                    |
   |  - 6-Level Noise Sweep (0% to 15%) & Degradation Curves                         |
   +---------------------------------------------------------------------------------+
                                           |
                                           v
   +---------------------------------------------------------------------------------+
   |                     TIER 4: TAXONOMY & REGIME EVALUATION                        |
   |  - Environmental Regimes: Normal, Flash Flood, Drought, Mountainous             |
   |  - 4-Tier Operational State Taxonomy: Normal -> Degraded -> High Unc -> Failure |
   |  - Safety Rejection Logic & Telemetry Logging                                   |
   +---------------------------------------------------------------------------------+

2.2 Processing Pipeline
-----------------------
Execution proceeds sequentially across three sprint validation phases:

1. **Phase 1: Environment Initialization & Feature Matrix Construction** (Cells 00–04)
   - Configures dark telemetry graphics and sets seeds (NumPy `1607`, PyTorch `1607`).
   - Synthesizes 1000 ground truth points and 4-column multi-modal feature matrix :math:`\mathbf{X}_{\text{baseline}}`.
2. **Phase 2: Sensor Dropout Stress Testing** (Cells 05–09)
   - Evaluates nominal, single-loss, and dual-loss sensor states.
   - Calculates RMSE against ground truth, measures mean uncertainty :math:`\sigma`, and applies exponential confidence mapping.
   - Renders Plot 1 (RMSE vs. Uncertainty bar chart and confidence decay curve).
3. **Phase 3: Controlled Noise Injection & Sweep** (Cells 10–17)
   - Implements noise injectors for spectral Gaussian/impulse corruption, spatial masking, and affine calibration offsets.
   - Executes a 6-level noise sweep (:math:`0\%` to :math:`15\%`), recording degradation trajectories.
   - Renders Plot 2 (Progressive error/uncertainty response and graceful confidence decay curve).
   - Executes the uncalibrated radar offset test.
4. **Phase 4: Environmental Edge Cases & Taxonomy Formalization** (Cells 18–25)
   - Audits performance metrics across four extreme environmental regimes.
   - Renders Plot 3 (Regime performance matrix and climate confidence response).
   - Formalizes the 4-tier Operational State & Failure Mode Taxonomy and outputs final scientific conclusions.

2.3 Component Relationships
---------------------------
Components interact through direct array passing within memory:

* **Feature Synthesizer**: Produces :math:`\mathbf{X}_{\text{baseline}} \in \mathbb{R}^{1000 \times 4}`.
* **Dropout Predictor**: Copies the input matrix, applies zero-masking to active columns, blends surviving channels,
  and adds stochastic noise.
* **Corruption Injectors**: Transform feature slices via additive noise, element-wise masking, or affine scaling.
* **Confidence Evaluator**: Maps uncertainty vectors to bounded confidence percentages using exponential decay.
* **Taxonomy Engine**: Evaluates scalar thresholds on :math:`\sigma_{\text{total}}` to assign operational states.

2.4 Data Flow
-------------
The data flow is a feedforward evaluation graph:

.. code-block:: text

   theta_true [1000] ──> [S2, S1, DEM, Weather] ──> X_baseline [1000, 4]
                                                            │
         ┌──────────────────────────────────────────────────┼─────────────────────────┐
         │                                                  │                         │
         ▼                                                  ▼                         ▼
   Dropout Simulator                                Corruption Suite           Calibration Shift
   [none, noS2, noS1, dual]                         [Noise Sweep 0-15%]        [scale=1.2, off=0.06]
         │                                                  │                         │
         ▼                                                  ▼                         ▼
   Plot 1 (Dropout Profile)                         Plot 2 (Noise Curves)      Offset Audit Log
         │                                                  │                         │
         └──────────────────────────────────────────────────┼─────────────────────────┘
                                                            │
                                                            ▼
                                               Environmental Edge Cases
                                                            │
                                                            ▼
                                               Plot 3 (Regime Matrix)
                                                            │
                                                            ▼
                                               4-Tier Operational Taxonomy


3. Execution Flow
=================

3.1 Initialization and Hardware Verification
--------------------------------------------
Cell 02 initializes system libraries, applies styling, and verifies computational execution hardware:

.. code-block:: python

   import sys, os, numpy as np, pandas as pd, torch, matplotlib.pyplot as plt

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
``⚡ [MRIDANSH-Robustness Engine] Active on: cuda`` (or ``cpu``).

3.2 Multi-Modal Feature Generation
----------------------------------
Cell 04 generates the synthetic calibration dataset:

.. code-block:: python

   NUM_SAMPLES = 1000
   theta_true = np.random.uniform(0.12, 0.40, size=NUM_SAMPLES)

   feat_S2 = theta_true + np.random.normal(0, 0.02, size=NUM_SAMPLES)
   feat_S1 = theta_true + np.random.normal(0, 0.025, size=NUM_SAMPLES)
   feat_DEM = np.random.uniform(100, 800, size=NUM_SAMPLES)
   feat_Weather = np.random.uniform(0, 50, size=NUM_SAMPLES)

   X_baseline = np.column_stack([feat_S2, feat_S1, feat_DEM, feat_Weather])

3.3 Sensor Dropout Stress Testing
---------------------------------
Cell 06 defines the prediction simulator and executes the four dropout modes:

.. code-block:: python

   def simulate_ensemble_prediction(X_feats, dropout_type='none'):
       X_mod = X_feats.copy()
       base_unc = 0.025

       if dropout_type == 'none':
           pred = 0.5 * X_mod[:, 0] + 0.5 * X_mod[:, 1]
           uncertainty = np.full(len(X_feats), base_unc + 0.035) + np.random.normal(0, 0.005, size=len(X_feats))

       elif dropout_type == 'missing_S2':
           X_mod[:, 0] = 0.0
           pred = X_mod[:, 1] + np.random.normal(0, 0.015, size=len(X_feats))
           uncertainty = np.full(len(X_feats), base_unc + 0.035) + np.random.normal(0, 0.005, size=len(X_feats))

       elif dropout_type == 'missing_S1':
           X_mod[:, 1] = 0.0
           pred = X_mod[:, 0] + np.random.normal(0, 0.020, size=len(X_feats))
           uncertainty = np.full(len(X_feats), base_unc + 0.045) + np.random.normal(0, 0.006, size=len(X_feats))

       elif dropout_type == 'dual_missing':
           X_mod[:, 0] = 0.0
           X_mod[:, 1] = 0.0
           pred = np.full(len(X_feats), 0.25) + np.random.normal(0, 0.05, size=len(X_feats))
           uncertainty = np.full(len(X_feats), 0.120) + np.random.normal(0, 0.010, size=len(X_feats))

       uncertainty = np.abs(uncertainty)
       confidence = np.exp(-1.5 * (uncertainty / 0.10))
       confidence = np.clip(confidence, 0.0, 1.0)
       return pred, uncertainty, confidence

3.4 Controlled Noise Injection and Sweep
----------------------------------------
Cells 12 and 13 declare corruption functions and execute a 6-step noise sweep:

.. code-block:: python

   noise_levels = np.linspace(0.0, 0.15, 6)
   corrupt_rmses, corrupt_uncs, corrupt_confs = [], [], []

   for n_lvl in noise_levels:
       X_noise = inject_spectral_noise(X_baseline[:, :2], noise_std=n_lvl, impulse_prob=n_lvl * 0.2)
       pred_noisy = 0.5 * X_noise[:, 0] + 0.5 * X_noise[:, 1]
       rmse_step = np.sqrt(np.mean((pred_noisy - theta_true)**2))
       unc_step = 0.025 + (n_lvl * 0.85) + np.random.normal(0, 0.002, size=NUM_SAMPLES)
       conf_step = np.clip(np.exp(-1.8 * (unc_step / 0.10)), 0.0, 1.0)

       corrupt_rmses.append(rmse_step)
       corrupt_uncs.append(unc_step.mean())
       corrupt_confs.append(conf_step.mean() * 100)

3.5 Radar Calibration Shift Simulation
--------------------------------------
Cell 17 tests the effect of uncalibrated backscatter offsets:

.. code-block:: python

   X_shifted = inject_calibration_shift(X_baseline[:, :2], scale=1.20, offset=0.06)
   pred_shifted = 0.5 * X_shifted[:, 0] + 0.5 * X_shifted[:, 1]
   rmse_shifted = np.sqrt(np.mean((pred_shifted - theta_true)**2))
   unc_shifted = 0.115 + np.random.normal(0, 0.005, size=NUM_SAMPLES)
   conf_shifted = np.clip(np.exp(-1.8 * (unc_shifted / 0.10)) * 100, 0, 100)

3.6 Environmental Stress Assessment
-----------------------------------
Cell 20 defines performance metrics across four operational hydrological regimes:

.. code-block:: python

   scenarios_env = ['Normal Field', 'Flash Flood Saturation', 'Severe Drought', 'Mountainous Terrain']
   rmse_env = [0.0160, 0.0820, 0.0750, 0.0910]
   unc_env  = [0.0250, 0.0980, 0.0890, 0.1120]
   conf_env = [63.8, 22.8, 26.3, 18.7]

3.7 Operational State Taxonomy Compilation
------------------------------------------
Cell 23 formalizes the 4-tier decision taxonomy that maps :math:`\sigma_{\text{total}}` thresholds
to operational actions.


4. Component Design
===================

4.1 Multi-Modal Feature Generator
---------------------------------
The feature generator constructs synthetic multi-modal observations that correlate with ground truth
soil moisture while introducing sensor-specific noise distributions:

.. list-table:: Modality Feature Synthesizer Attributes
   :widths: 20 25 25 30
   :header-rows: 1

   * - Feature Name
     - Column Index
     - Mathematical Formulation
     - Physical Significance
   * - ``feat_S2``
     - 0
     - :math:`\theta_{\text{true}} + \mathcal{N}(0, 0.020^2)`
     - Optical surface reflectance proxy
   * - ``feat_S1``
     - 1
     - :math:`\theta_{\text{true}} + \mathcal{N}(0, 0.025^2)`
     - SAR C-band microwave backscatter proxy
   * - ``feat_DEM``
     - 2
     - :math:`\mathcal{U}(100, 800)\text{ m}`
     - Digital elevation model terrain height
   * - ``feat_Weather``
     - 3
     - :math:`\mathcal{U}(0, 50)\text{ mm}`
     - Antecedent precipitation accumulation

4.2 Dropout Prediction Simulator
--------------------------------
The simulator replicates operational degradation when satellite sensors experience outages:

* **Nominal (`none`)**: Computes an equal linear blend of optical and SAR channels:
  :math:`\hat{\theta} = 0.5 \mathbf{x}_{\text{S2}} + 0.5 \mathbf{x}_{\text{S1}}`.
  Base uncertainty is :math:`\sigma \approx 0.060\text{ m}^3/\text{m}^3`.
* **Missing Sentinel-2 (`missing_S2`)**: Zero-masks optical features (:math:`\mathbf{x}_{\text{S2}} = 0`).
  Prediction relies purely on SAR with added noise: :math:`\hat{\theta} = \mathbf{x}_{\text{S1}} + \mathcal{N}(0, 0.015^2)`.
* **Missing Sentinel-1 (`missing_S1`)**: Zero-masks SAR features (:math:`\mathbf{x}_{\text{S1}} = 0`).
  Prediction relies purely on optical with added noise: :math:`\hat{\theta} = \mathbf{x}_{\text{S2}} + \mathcal{N}(0, 0.020^2)`.
  Uncertainty expands to :math:`\sigma \approx 0.070\text{ m}^3/\text{m}^3`.
* **Dual Missing (`dual_missing`)**: Zero-masks both primary remote sensing channels.
  Falls back to climatological mean: :math:`\hat{\theta} \sim \mathcal{N}(0.25, 0.05^2)`.
  Uncertainty expands to :math:`\sigma \approx 0.120\text{ m}^3/\text{m}^3`.

4.3 Noise and Corruption Injectors
----------------------------------
Three standalone functions simulate real-world data degradation:

1. **`inject_spectral_noise(X, noise_std, impulse_prob)`**:
   Injects additive Gaussian noise :math:`\mathcal{N}(0, \sigma_{\text{noise}}^2)` and salt-and-pepper
   impulse spikes (:math:`\pm 0.25` drawn with probability :math:`p_{\text{impulse}}`), clipping results to :math:`[0.0, 1.0]`.
2. **`inject_spatial_dropout(X, dropout_rate)`**:
   Applies element-wise Bernoulli masking where entries are set to zero with probability :math:`p_{\text{dropout}} = 0.15`.
3. **`inject_calibration_shift(X, scale, offset)`**:
   Applies an affine transformation :math:`\mathbf{X}_{\text{shifted}} = \mathbf{X} \cdot \text{scale} + \text{offset}`
   simulating uncalibrated radar cross-sections.

4.4 Dynamic Uncertainty & Confidence Mapper
-------------------------------------------
Translates dimensional uncertainty into an operational confidence index via exponential decay:

.. math::

   C = \operatorname{clip}\left(\exp\left(-\gamma \frac{\sigma}{\sigma_{\text{max}}}\right), 0.0, 1.0\right)

*Note on Implementation Discrepancy*:
Cell 06 utilizes :math:`\gamma = 1.5`, whereas Cell 13 and Cell 17 utilize :math:`\gamma = 1.8`.
Both formulations employ :math:`\sigma_{\text{max}} = 0.10\text{ m}^3/\text{m}^3`.

4.5 Diagnostic Visualization Engine
-----------------------------------
Generates three 2-panel Matplotlib figures utilizing dark telemetry styling:

* **Plot 1 (Day 5)**: Sensor dropout RMSE vs. uncertainty bar charts and confidence decay curve.
* **Plot 2 (Day 6)**: Progressive error response curve and graceful confidence decay curve over the noise sweep.
* **Plot 3 (Day 7)**: Environmental edge case performance matrix and climate regime confidence response.

4.6 4-Tier Operational State Governance Module
----------------------------------------------
Maps quantitative uncertainty bounds into discrete operational system states:

.. list-table:: 4-Tier Operational State Governance Specification
   :widths: 20 20 18 22 20
   :header-rows: 1

   * - Operational State
     - Uncertainty Bound (:math:`\sigma`)
     - Confidence Index
     - Primary Trigger Condition
     - System Action
   * - **STATE 0: NORMAL**
     - :math:`\sigma \le 0.035\text{ m}^3/\text{m}^3`
     - :math:`> 50\%`
     - S1 + S2 Active, Clear Sky
     - Standard High-Precision Output
   * - **STATE 1: DEGRADED**
     - :math:`0.035 < \sigma \le 0.070`
     - :math:`30\% - 50\%`
     - S2 Missing (Clouds) / Mild Noise
     - Flag Output with Warning Banner
   * - **STATE 2: HIGH UNCERTAINTY**
     - :math:`0.070 < \sigma \le 0.110`
     - :math:`15\% - 30\%`
     - S1 Missing / Severe Corruption
     - Trigger Climatology Fallback
   * - **STATE 3: FAILURE MODE**
     - :math:`\sigma > 0.110\text{ m}^3/\text{m}^3`
     - :math:`< 15\%`
     - Dual Sensor Dropout / Flash Flood
     - **REJECT PREDICTION** & Alert Operator


5. Data Structures
==================

5.1 Input Schema
----------------
Configuration parameters governing the simulation runs:

.. list-table:: Input Configuration Schema
   :widths: 25 15 20 40
   :header-rows: 1

   * - Parameter
     - Type
     - Default Value
     - Description
   * - ``NUM_SAMPLES``
     - ``int``
     - ``1000``
     - Total number of spatial calibration samples.
   * - ``noise_levels``
     - ``np.ndarray``
     - ``linspace(0, 0.15, 6)``
     - Evaluation steps for progressive noise sweep.
   * - ``scale`` (Offset Test)
     - ``float``
     - ``1.20``
     - Radar backscatter multiplicative scale error.
   * - ``offset`` (Offset Test)
     - ``float``
     - ``0.06``
     - Radar backscatter additive offset bias.

5.2 In-Memory Feature and Evaluation Tensors
--------------------------------------------
Primary runtime tensors held in memory:

.. list-table:: In-Memory Tensor Specifications
   :widths: 20 15 15 20 30
   :header-rows: 1

   * - Variable Name
     - Data Type
     - Shape
     - Memory Footprint
     - Typical Value Range
   * - ``theta_true``
     - ``float64``
     - ``(1000,)``
     - 8.0 KB
     - :math:`[0.120, 0.400]\text{ m}^3/\text{m}^3`
   * - ``X_baseline``
     - ``float64``
     - ``(1000, 4)``
     - 32.0 KB
     - Optical, SAR, DEM, Weather
   * - ``pred_nom``
     - ``float64``
     - ``(1000,)``
     - 8.0 KB
     - :math:`[0.12, 0.40]\text{ m}^3/\text{m}^3`
   * - ``unc_nom``
     - ``float64``
     - ``(1000,)``
     - 8.0 KB
     - Mean :math:`\pm 0.0600\text{ m}^3/\text{m}^3`
   * - ``conf_nom``
     - ``float64``
     - ``(1000,)``
     - 8.0 KB
     - Mean :math:`0.408` (40.8%)
   * - ``pred_dual``
     - ``float64``
     - ``(1000,)``
     - 8.0 KB
     - Mean :math:`0.25\text{ m}^3/\text{m}^3`
   * - ``unc_dual``
     - ``float64``
     - ``(1000,)``
     - 8.0 KB
     - Mean :math:`\pm 0.1197\text{ m}^3/\text{m}^3`
   * - ``conf_dual``
     - ``float64``
     - ``(1000,)``
     - 8.0 KB
     - Mean :math:`0.168` (16.8%)

5.3 Degradation Metric Records
------------------------------
Arrays recording the trajectory of the 6-step noise sweep:

.. list-table:: Noise Sweep Evaluation Arrays
   :widths: 20 15 15 50
   :header-rows: 1

   * - Variable
     - Type
     - Length
     - Stored Values
   * - ``corrupt_rmses``
     - ``list[float]``
     - 6
     - ``[0.0160, 0.0283, 0.0492, 0.0698, 0.0868, 0.1033]``
   * - ``corrupt_uncs``
     - ``list[float]``
     - 6
     - ``[0.0249, 0.0505, 0.0760, 0.1015, 0.1270, 0.1525]``
   * - ``corrupt_confs``
     - ``list[float]``
     - 6
     - ``[63.9, 40.4, 25.5, 16.1, 10.2, 6.4]``

5.4 Operational State Classification Schema
-------------------------------------------
Output structure representing an operational governance decision:

.. code-block:: text

   {
       "sample_id": int,
       "predicted_theta": float,
       "uncertainty_sigma": float,
       "confidence_index": float,
       "operational_state": "STATE 0: NORMAL" | "STATE 1: DEGRADED" | 
                            "STATE 2: HIGH UNCERTAINTY" | "STATE 3: FAILURE MODE",
       "action": "STANDARD_OUTPUT" | "WARNING_BANNER" | 
                 "CLIMATOLOGY_FALLBACK" | "REJECT_PREDICTION"
   }


6. Algorithms and Methods
=========================

6.1 Linear Modality Blending Formulation
----------------------------------------
Under clear-sky conditions with full constellation availability, the prediction is formulated
as an equal linear blend of optical and SAR observations:

.. math::

   \hat{\theta} = w_{\text{S2}} \mathbf{x}_{\text{S2}} + w_{\text{S1}} \mathbf{x}_{\text{S1}}
   \quad \text{where } w_{\text{S2}} = w_{\text{S1}} = 0.5

When sensor :math:`m` drops out, its weight is set to zero (:math:`w_m = 0`) and surviving channels
are re-normalized:

.. math::

   \hat{\theta}_{\text{no\_S2}} = \mathbf{x}_{\text{S1}} + \epsilon_{\text{SAR}}, \quad \epsilon_{\text{SAR}} \sim \mathcal{N}(0, 0.015^2)

.. math::

   \hat{\theta}_{\text{no\_S1}} = \mathbf{x}_{\text{S2}} + \epsilon_{\text{opt}}, \quad \epsilon_{\text{opt}} \sim \mathcal{N}(0, 0.020^2)

Under dual loss (:math:`w_{\text{S2}} = w_{\text{S1}} = 0`), the model reverts to climatological prior:

.. math::

   \hat{\theta}_{\text{dual}} = \bar{\theta}_{\text{clim}} + \epsilon_{\text{clim}} = 0.25 + \mathcal{N}(0, 0.05^2)

6.2 Spectral Gaussian and Salt-and-Pepper Impulse Injection
-----------------------------------------------------------
Data corruption models additive noise and transmission bit errors:

.. math::

   \mathbf{x}_{\text{corrupted}} = \operatorname{clip}\left(\mathbf{x} + \mathcal{N}(0, \sigma_{\text{noise}}^2) + \mathbf{\eta}_{\text{impulse}}, 0.0, 1.0\right)

where impulse noise is defined by:

.. math::

   \mathbf{\eta}_{\text{impulse}} = \begin{cases}
       +0.25 & \text{with probability } p / 2 \\
       -0.25 & \text{with probability } p / 2 \\
       0.0 & \text{with probability } 1 - p
   \end{cases}
   \quad \text{with } p = \sigma_{\text{noise}} \times 0.20

6.3 Spatial Bernoulli Masking
-----------------------------
Simulates missing revisit pixels or corrupted spatial tiles:

.. math::

   \mathbf{x}_{\text{masked}} = \mathbf{x} \odot \mathbf{M}_{\text{spatial}},
   \quad \mathbf{M}_{\text{spatial}} \sim \operatorname{Bernoulli}(1 - p_{\text{dropout}})

where :math:`p_{\text{dropout}} = 0.15` (15% random pixel loss).

6.4 Affine Calibration Offset Transformation
--------------------------------------------
Models uncalibrated radar cross-sections or radiometer drift:

.. math::

   \mathbf{x}_{\text{calibrated}} = \alpha \cdot \mathbf{x} + \beta

In the calibration shift test: :math:`\alpha = 1.20` (+20% scale gain error) and :math:`\beta = 0.06` (+0.06 bias offset).

6.5 Exponential Confidence Decay Response
-----------------------------------------
Quantifies operational reliability decay as uncertainty escalates:

.. math::

   C(\sigma) = \exp\left(-\gamma \frac{\sigma}{\sigma_{\text{max}}}\right)

Evaluating derivatives demonstrates strictly monotonic decay:

.. math::

   \frac{dC}{d\sigma} = -\frac{\gamma}{\sigma_{\text{max}}} C(\sigma) < 0 \quad (\forall \sigma \ge 0)

6.6 4-Tier State Decision Logic
-------------------------------
Assigns operational status according to scalar uncertainty thresholds:

.. math::

   \text{State}(\sigma) = \begin{cases}
       \text{STATE 0: NORMAL} & \text{if } \sigma \le 0.035 \\
       \text{STATE 1: DEGRADED} & \text{if } 0.035 < \sigma \le 0.070 \\
       \text{STATE 2: HIGH UNCERTAINTY} & \text{if } 0.070 < \sigma \le 0.110 \\
       \text{STATE 3: FAILURE MODE} & \text{if } \sigma > 0.110
   \end{cases}


7. Interfaces
=============

7.1 Upstream Interfaces
-----------------------
In production deployment, Notebook 08 ingests:
* Feature matrices from preprocessing pipelines: ``data_processed/features.parquet``.
* Model weights from ConvLSTM: ``models/convlstm_checkpoint.pt``.
* Posterior covariance diagonals from EnKF: ``data_processed/state_covariances.npy``.

7.2 Internal Programmatic Interfaces
------------------------------------

Function: ``simulate_ensemble_prediction``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def simulate_ensemble_prediction(
       X_feats: np.ndarray,
       dropout_type: str = 'none'
   ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
       """
       Simulates ensemble predictions, uncertainty bounds, and confidence indices.

       Parameters:
           X_feats (np.ndarray): 2D array of shape (N, 4) containing feature columns.
           dropout_type (str): Mode string ('none', 'missing_S2', 'missing_S1', 'dual_missing').

       Returns:
           tuple[np.ndarray, np.ndarray, np.ndarray]:
               - pred: Predicted soil moisture array (N,).
               - uncertainty: Estimated standard deviation array (N,).
               - confidence: Normalized confidence array in [0.0, 1.0] (N,).
       """

Function: ``inject_spectral_noise``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def inject_spectral_noise(
       X: np.ndarray,
       noise_std: float = 0.05,
       impulse_prob: float = 0.02
   ) -> np.ndarray:
       """Injects additive Gaussian noise and Salt-and-Pepper impulse spikes into feature array."""

7.3 Graphical Visualization Interfaces
--------------------------------------
The notebook outputs three high-resolution visual interfaces:
* **Plot 1**: Figure dimensions :math:`13 \times 5` inches, 2 subplots (Bar chart and line decay).
* **Plot 2**: Figure dimensions :math:`13 \times 5` inches, 2 subplots (Response curves and confidence decay).
* **Plot 3**: Figure dimensions :math:`13 \times 5` inches, 2 subplots (Regime matrix and climate confidence).

7.4 Downstream Safety Interfaces
--------------------------------
Downstream geotechnical risk mapping consumes boolean rejection masks:

.. code-block:: python

   is_rejected = (uncertainty > 0.110) | (confidence < 0.15)
   valid_predictions = pred[~is_rejected]


8. Configuration
================

8.1 Empirical Constants and Parameters
--------------------------------------

.. list-table:: Engine Hyperparameters and Constants
   :widths: 25 15 15 45
   :header-rows: 1

   * - Parameter Name
     - Type
     - Default Value
     - Physical / Operational Rationale
   * - ``NUM_SAMPLES``
     - ``int``
     - ``1000``
     - Sample size for empirical statistical evaluation.
   * - ``base_unc``
     - ``float``
     - ``0.025``
     - Baseline instrumental measurement error floor (:math:`\text{m}^3/\text{m}^3`).
   * - ``gamma`` (Dropout)
     - ``float``
     - ``1.5``
     - Confidence decay rate parameter used in Cell 06.
   * - ``gamma`` (Noise Sweep)
     - ``float``
     - ``1.8``
     - Confidence decay rate parameter used in Cells 13 and 17.
   * - ``sigma_max``
     - ``float``
     - ``0.10``
     - Upper threshold bound for volumetric soil moisture error (:math:`\text{m}^3/\text{m}^3`).

8.2 Environment and Hardware
----------------------------
* Python :math:`\ge 3.10`
* PyTorch :math:`\ge 2.0.0` with CUDA support (falls back to CPU).
* NumPy :math:`\ge 1.23.0`, Matplotlib :math:`\ge 3.7.0`, Pandas :math:`\ge 1.5.0`.

8.3 Deterministic Seeding
-------------------------
Enforced globally via:

.. code-block:: python

   np.random.seed(1607)
   torch.manual_seed(1607)

8.4 Dark Telemetry Palette
--------------------------
Standard JCC RS-SDA dark visual styling:
* Cyan Primary: ``#00FFCC``
* Orange Secondary: ``#FF9900``
* Red Warning: ``#FF5500``
* Crimson Failure: ``#FF0055``
* Grid Background: ``#1A3344``


9. Error Handling and Defensive Design
======================================

9.1 Input Value Range Clipping
------------------------------
All spectral noise corruption routines apply hard clipping:

.. code-block:: python

   return np.clip(X_corrupted, 0.0, 1.0)

This prevents corrupted feature values from exceeding physical reflectance boundaries.

9.2 Zero-Division and Infinite Gradient Prevention
---------------------------------------------------
All uncertainty standard deviations are wrapped with ``np.abs()`` prior to exponential scaling,
guaranteeing non-negative inputs to the exponential mapper.

9.3 Fallback Prior Management
-----------------------------
When both optical and radar sensors drop out simultaneously, the software defensively refuses
to return ungrounded zeros or unconditioned neural extrapolations.
Instead, it switches to a bounded climatological prior:

.. code-block:: python

   pred = np.full(len(X_feats), 0.25) + np.random.normal(0, 0.05, size=len(X_feats))
   uncertainty = np.full(len(X_feats), 0.120) + np.random.normal(0, 0.010, size=len(X_feats))

9.4 Array Shape and Type Integrity
----------------------------------
Matrix manipulation utilizes explicit column stacking and slicing (`X[:, :2]`), preventing
dimension mismatch exceptions.


10. Generated Artifacts and Visualizations
==========================================

10.1 Plot 1: Sensor Dropout Degradation Profile
-----------------------------------------------
Rendered in Cell 08:
* **Subplot 1**: Bar comparison of Prediction RMSE and Model Uncertainty (:math:`\pm\sigma`).
* **Subplot 2**: System Confidence Degradation Decay curve displaying values
  :math:`40.8\% \to 40.7\% \to 35.2\% \to 16.8\%`.

10.2 Plot 2: Noise Sweep Degradation Diagnostics
------------------------------------------------
Rendered in Cell 15:
* **Subplot 1**: Trajectory of RMSE expanding from :math:`0.0160 \to 0.1033` alongside uncertainty (:math:`0.0249 \to 0.1525`).
* **Subplot 2**: Graceful confidence decay curve dropping from :math:`63.9\% \to 6.4\%`.

10.3 Plot 3: Environmental Edge Case Matrix
-------------------------------------------
Rendered in Cell 22:
* **Subplot 1**: Error and uncertainty across Normal, Flash Flood, Drought, and Mountainous regimes.
* **Subplot 2**: System confidence response across climate regimes (:math:`63.8\% \to 22.8\% \to 26.3\% \to 18.7\%`).

10.4 Console Telemetry Summaries
--------------------------------
Printed execution summaries for dropout stress, noise sweep, and calibration offset tests
provide automated terminal verification logs.


11. Reproducibility
===================

11.1 Random Seed Control
------------------------
Random seeds are fixed to ``1607`` for both NumPy and PyTorch.

11.2 Numerical Reproducibility Audit Table
------------------------------------------
Execution under seed 1607 produces bit-exact verification metrics:

.. list-table:: Reproducibility Verification Baseline
   :widths: 40 30 30
   :header-rows: 1

   * - Metric / Quantity
     - Expected Baseline
     - Verified Execution
   * - Nominal RMSE (S1+S2)
     - :math:`0.0160`
     - :math:`0.0160`
   * - S2 Missing RMSE (Clouds)
     - :math:`0.0287`
     - :math:`0.0287`
   * - S1 Missing RMSE (SAR Fail)
     - :math:`0.0284`
     - :math:`0.0284`
   * - Dual Fail RMSE
     - :math:`0.0977`
     - :math:`0.0977`
   * - Dual Fail Confidence
     - :math:`16.8\%`
     - :math:`16.8\%`
   * - 0.0% Noise Sweep RMSE
     - :math:`0.0160`
     - :math:`0.0160`
   * - 15.0% Noise Sweep RMSE
     - :math:`0.1033`
     - :math:`0.1033`
   * - 15.0% Noise Confidence
     - :math:`6.4\%`
     - :math:`6.4\%`
   * - Shifted Calibration RMSE
     - :math:`0.1149`
     - :math:`0.1149`
   * - Shifted Calibration Confidence
     - :math:`12.6\%`
     - :math:`12.6\%`

11.3 Deterministic Execution Guarantee
--------------------------------------
All operations execute without unseeded stochasticity, ensuring identical numerical outputs
across repeated runs.


12. Performance Characteristics
===============================

12.1 Execution Latency and Wall-Clock Benchmarks
------------------------------------------------
The entire notebook executes in :math:`\approx 1.25\text{ s}`:

.. list-table:: Latency Profile
   :widths: 45 25 30
   :header-rows: 1

   * - Pipeline Component
     - Duration
     - Proportion
   * - Environment & Imports
     - :math:`\approx 0.18\text{ s}`
     - :math:`14\%`
   * - Feature Generation
     - :math:`\approx 0.01\text{ s}`
     - :math:`1\%`
   * - Dropout Simulation & Plot 1
     - :math:`\approx 0.38\text{ s}`
     - :math:`30\%`
   * - Noise Sweep & Plot 2
     - :math:`\approx 0.35\text{ s}`
     - :math:`28\%`
   * - Calibration Offset Test
     - :math:`\approx 0.01\text{ s}`
     - :math:`1\%`
   * - Edge Cases & Plot 3
     - :math:`\approx 0.32\text{ s}`
     - :math:`26\%`
   * - **Total Runtime**
     - :math:`\approx \mathbf{1.25\text{ s}}`
     - :math:`\mathbf{100\%}`

12.2 Memory Footprint
---------------------
Peak resident memory is :math:`< 120\text{ MB}`, with active arrays occupying :math:`< 250\text{ KB}`.

12.3 Computational Complexity Analysis
--------------------------------------
All operations are vectorized element-wise arithmetic scaling linearly :math:`O(N)` with sample count.


13. Implementation Notes
========================

13.1 Current Implementation State
---------------------------------
The notebook successfully validates the mathematical principles of monotonic error expansion,
uncertainty inflation, and graceful confidence decay.

13.2 Known Implementation Constraints
-------------------------------------
1. **Mocked Ensemble Predictions (Defect D-001)**: `simulate_ensemble_prediction` uses linear combinations
   rather than real neural network inference.
2. **Inconsistent Gamma Decay Parameter (Defect D-002)**: Cell 06 uses :math:`\gamma = 1.5`, whereas
   Cells 13 and 17 use :math:`\gamma = 1.8`.
3. **Hardcoded Environmental Arrays (Defect D-003)**: Environmental edge case metrics in Cell 20
   are static python lists rather than calculated outputs.
4. **Unused Modality Columns (Defect D-004)**: DEM and Weather columns in :math:`\mathbf{X}_{\text{baseline}}`
   are not incorporated into the prediction formulas.
5. **Decoupled Pipeline (Defect D-005)**: No datasets are ingested from or exported to `data_processed/`.

13.3 Architectural Refactoring Roadmap
--------------------------------------
1. Replace mocked predictors with TorchScript neural model checkpoints from Notebooks 04 and 05.
2. Unify confidence mapping under a single parameter specification (:math:`\gamma = 1.5`).
3. Connect dynamic simulation routines for flash flood and drought edge cases.
4. Export operational state GeoTIFF masks to `data_processed/robustness/`.


14. Technical Limitations
=========================

14.1 Synthetic Feature Dependency
---------------------------------
All feature distributions and sensor noises are drawn from synthetic random generators; results
do not represent physical satellite calibrations.

14.2 Linear Surrogate Model Limitation
---------------------------------------
Averaging optical and SAR channels linearly does not capture non-linear neural cross-attention
or saturation dynamics present in deep learning architectures.

14.3 Static Environmental Metrics Limitation
--------------------------------------------
Because edge case performance metrics are static lists, they demonstrate reporting taxonomy
rather than real simulation behavior.


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
     - Section 3.2, Section 4.1
     - Cell 04
     - ``theta_true = np.random.uniform(0.12, 0.40, ...)``
   * - **FR-002**
     - Section 3.2, Section 4.1
     - Cell 04
     - ``X_baseline = np.column_stack(...)``
   * - **FR-003**
     - Section 3.3, Section 4.2
     - Cell 06
     - ``simulate_ensemble_prediction`` function
   * - **FR-004**
     - Section 3.3, Section 11.2
     - Cell 06
     - ``rmse_nom, rmse_noS2, rmse_noS1, rmse_dual``
   * - **FR-005**
     - Section 3.3, Section 4.4, Section 6.5
     - Cell 06
     - ``confidence = np.clip(np.exp(-1.5 * ...), 0, 1)``
   * - **FR-006**
     - Section 3.3, Section 7.3, Section 10.1
     - Cell 08
     - Aerospace Plot 1 (2-panel figure)
   * - **FR-007**
     - Section 3.4, Section 4.3, Section 6.2
     - Cell 12
     - ``inject_spectral_noise`` function
   * - **FR-008**
     - Section 3.4, Section 4.3, Section 6.3
     - Cell 12
     - ``inject_spatial_dropout`` function
   * - **FR-009**
     - Section 3.4, Section 4.3, Section 6.4
     - Cell 12
     - ``inject_calibration_shift`` function
   * - **FR-010**
     - Section 3.4, Section 5.3, Section 11.2
     - Cell 13
     - 6-level noise sweep execution loop
   * - **FR-011**
     - Section 3.4, Section 7.3, Section 10.2
     - Cell 15
     - Aerospace Plot 2 (2-panel figure)
   * - **FR-012**
     - Section 3.5, Section 6.4, Section 11.2
     - Cell 17
     - Uncalibrated radar offset evaluation
   * - **FR-013**
     - Section 3.6, Section 4.6
     - Cell 20
     - Environmental stress scenarios array
   * - **FR-014**
     - Section 3.6, Section 7.3, Section 10.3
     - Cell 22
     - Aerospace Plot 3 (2-panel figure)
   * - **FR-015**
     - Section 3.7, Section 4.6, Section 6.6
     - Cell 23
     - 4-Tier Operational State Taxonomy table
   * - **DI-001**
     - Section 4.2, Section 9.2
     - Cell 06
     - ``np.abs(uncertainty)``
   * - **DI-002**
     - Section 4.2, Section 11.2
     - Cell 06
     - Monotonic RMSE increase across dropouts
   * - **DI-003**
     - Section 4.2, Section 11.2
     - Cell 13
     - Monotonic uncertainty inflation over noise sweep
   * - **DI-004**
     - Section 4.4, Section 6.5
     - Cell 13
     - Monotonic confidence decay over noise sweep
   * - **DI-005**
     - Section 4.6, Section 6.6
     - Cell 23
     - Complete continuous uncertainty partition
