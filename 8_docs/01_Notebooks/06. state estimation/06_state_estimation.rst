=====================================================================
THE MRIDANSH (AETHER-MRID1607X) - Notebook 06: State Estimation
=====================================================================

:Project: THE MRIDANSH - Unified Soil State Estimation System
:Engine: AETHER-MRID1607X (Multi-Domain Soil Intelligence Engine)
:Notebook: ``06-state-estimation.ipynb``
:Sprint phase: Days 1-2 of the Scientific Audit & Validation Mission
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
The primary technical objective of ``06-state-estimation.ipynb`` is to implement,
validate, and benchmark a stochastic Ensemble Kalman Filter (EnKF) data assimilation
engine that sequentially merges physical forward-model state predictions with noisy
Earth Observation (EO) satellite measurements to compute optimal posterior soil states
and dynamic error covariance matrices.

1.2 System Context
------------------
Within **THE MRIDANSH** (*AETHER-MRID1607X*) system, Notebook 04 forecasts temporal
sequences via ConvLSTM and Notebook 05 solves vertical unsaturated moisture diffusion via
Richards PDE PINNs. Notebook 06 executes statistical state assimilation:

* **Upstream**: Ingests nominal soil parameter bounds and forward model prediction trajectories.
* **Core Engine**: Constructs a 50-member Monte Carlo ensemble with realistic physical
  cross-correlations, executes stochastic perturbed-observation EnKF updates, computes
  Kalman gains, propagates forecast error covariances (:math:`\mathbf{P}^f`) to analysis error
  covariances (:math:`\mathbf{P}^a`), and runs multi-timestep sequential filtering against model drift.
* **Downstream**: Emits assimilated posterior state vectors and covariance matrices to
  Notebook 07 (Uncertainty Analysis) and Notebook 08 (Robustness and Failure Analysis) for
  probabilistic geotechnical risk assessment.

1.3 Design Boundary
-------------------
The design of Notebook 06 is bounded as follows:

* **In Boundary**: Target 4D state vector definition (:math:`\theta_{\text{root}}, \rho_b, K_{\text{sat}}, \text{SOC}`),
  multivariate normal prior ensemble generation with cross-variable correlation matrices,
  stochastic perturbed-observation Kalman gain computation, single-step observation updates,
  14-timestep sequential trajectory tracking against synthetic model drift, observation noise
  variance sweeps (:math:`R \in [10^{-4}, 10^{-1}]`), and summary deliverable compilation.
* **Out of Boundary**: Spatially distributed 2D/3D grid filtering (the filter operates on a
  lumped 0D point column vector), spatial covariance localization, non-Gaussian particle
  filtering, and direct radiometer brightness temperature inversion.

1.4 Relationship to Requirements
--------------------------------
This technical description details the mathematical models, algorithmic execution loops,
state transition equations, and software components implementing the formal requirements
specified in ``06_state_estimation_REQUIREMENTS.md``. See Section 15 for the complete
requirement-to-design mapping matrix.

2. Architecture
===============

2.1 Notebook Architecture
-------------------------
The software architecture is structured across two primary operational phases over 20 notebook cells:

* **Phase 1: EnKF Formulation & Single-Step Assimilation (Sprint Day 1)**:
  Defines the 4D target state space, builds the cross-variable correlation matrix,
  generates the 50-member clipped prior ensemble, implements the core EnKF update operator,
  executes a single-step observation assimilation test, and renders 4-variable distribution histograms.
* **Phase 2: Sequential Validation, Trajectory Tracking & Noise Sensitivity (Sprint Day 2)**:
  Simulates a 14-timestep synthetic observation timeline with systematic model drift, tracks
  unconstrained vs assimilated state trajectories, benchmarks RMSE error reductions, conducts
  an observation error variance sweep across 10 logarithmic points, and compiles the final
  uncertainty reduction profile table.

2.2 Processing Pipeline
-----------------------
The sequential assimilation pipeline operates through the following stages:

.. code-block:: text

   [Target State Parameters & Physical Bounds]
   (theta_root, bulk_density, K_sat, SOC)
               │
               ▼
   [Cross-Correlation Matrix R_corr] ──► [Covariance: Σ = D * R_corr * D]
               │
               ▼
   [Prior State Ensemble X^f ∈ R^(4x50)] (Multivariate Normal + Physical Clipping)
               │
               ├────────────────────────────────────────┐
               ▼                                        ▼
   [Observation Vector y = 0.34]            [Prior Anomalies: A = X^f - x_mean]
   [Noise Covariance R = 0.0009]                        │
   [Observation Matrix H = [1,0,0,0]]                   ▼
               │                            [Prior Covariance: P^f = A * A^T / (N-1)]
               │                                        │
               ├────────────────────────────────────────┘
               ▼
   [Innovation Covariance: S = H * P^f * H^T + R]
               │
               ▼
   [Kalman Gain: K = P^f * H^T * inv(S)]
               │
               ├────────────────────────────────────────┐
               ▼                                        ▼
   [Perturbed Obs: Y = y + ε, ε ~ N(0, R)]  [Innovation: Y - H * X^f]
               │                                        │
               ├────────────────────────────────────────┘
               ▼
   [Posterior Analysis Update: X^a = X^f + K * (Y - H * X^f)]
               │
               ├────────────────────────────────────────► [Plot 1: Histograms]
               │
               ▼
   [14-Timestep Sequential Trajectory Engine] ──────────► [Plot 2: State Trajectories]
               │
               ▼
   [Noise Sensitivity Sweep R ∈ [1e-4, 1e-1]] ──────────► [Plot 3: R-Variance Sweep]
               │
               ▼
   [Deliverable Summary DataFrame Compilation]

2.3 Component Relationships
---------------------------
The internal software components interact through explicit functional roles:

1. **Prior Ensemble Generator**: Samples multivariate normal distributions using empirical
   cross-correlation matrices and enforces physical parameter clipping.
2. **EnKF Update Engine**: Implements the stochastic perturbed-observation Kalman equations
   computing prior covariances, innovation inverses, Kalman gain projections, and posterior spreads.
3. **Sequential Trajectory Simulator**: Drives the forward temporal unrolling loop, applying
   systematic linear model drift and injecting sequential observation updates.
4. **Sensitivity Sweeper**: Evaluates filter convergence and stability across varying sensor
   noise variance parameters.

2.4 Data Flow
-------------
The data flow transitions across three mathematical matrix spaces:

1. **Ensemble State Space**: Matrices :math:`\mathbf{X} \in \mathbb{R}^{4 \times 50}` where rows
   represent physical state variables and columns represent Monte Carlo members.
2. **Covariance Space**: Error covariance matrices :math:`\mathbf{P}^f, \mathbf{P}^a \in \mathbb{R}^{4 \times 4}`
   and scalar innovation variance :math:`S \in \mathbb{R}^{1 \times 1}`.
3. **Measurement Space**: Scalar observation :math:`y \in \mathbb{R}^{1}`, noise variance
   :math:`R \in \mathbb{R}^{1 \times 1}`, and perturbed measurement array :math:`\mathbf{Y} \in \mathbb{R}^{1 \times 50}`.

3. Execution Flow
=================

3.1 Initialization
------------------
* Imports dependencies (``sys``, ``os``, ``numpy``, ``pandas``, ``torch``, ``matplotlib.pyplot``).
* Configures inline rendering and dark telemetry stylesheet:
  background ``#000000``, axis borders ``#00FFCC`` (width 1.2), grid lines ``#1A3344``
  (dashed, alpha 0.5), monospace font family.
* Fixes random seeds matching engine codename: ``np.random.seed(1607)`` and ``torch.manual_seed(1607)``.
* Emits initialization status banner.

3.2 Target State Vector Definition
----------------------------------
* Declares dictionary ``STATE_VARIABLES`` with nominal distributions and physical ranges:
  - ``theta_root``: :math:`\mu = 0.28, \sigma = 0.04`, range :math:`[0.05, 0.45]\text{ m}^3/\text{m}^3`.
  - ``bulk_density``: :math:`\mu = 1.35, \sigma = 0.08`, range :math:`[1.00, 1.80]\text{ g/cm}^3`.
  - ``K_sat``: :math:`\mu = 2.50, \sigma = 0.60`, range :math:`[0.01, 10.0]\text{ cm/hr}`.
  - ``SOC``: :math:`\mu = 1.20, \sigma = 0.25`, range :math:`[0.10, 4.00]\%`.
* Logs nominal target profiles to stdout.

3.3 Correlated Prior Ensemble Generation
----------------------------------------
* Constructs :math:`4 \times 4` correlation matrix:

  .. code-block:: python

     corr_matrix = np.array([
         [ 1.00, -0.30,  0.40,  0.20],
         [-0.30,  1.00, -0.50, -0.65],
         [ 0.40, -0.50,  1.00,  0.35],
         [ 0.20, -0.65,  0.35,  1.00]
     ])

* Computes covariance matrix :math:`\mathbf{\Sigma} = \mathbf{D} \mathbf{R}_{\text{corr}} \mathbf{D}`.
* Draws 50 samples via ``np.random.multivariate_normal`` and clips to physical bounds.
* Logs prior statistics: Mean :math:`\theta = 0.2829\text{ m}^3/\text{m}^3`, Std :math:`\theta = 0.0441\text{ m}^3/\text{m}^3`.

3.4 Single-Step EnKF Assimilation
---------------------------------
* Sets observation parameters:
  - Observation: :math:`y = [0.34]\text{ m}^3/\text{m}^3` (direct surface moisture measurement).
  - Measurement error variance: :math:`R = [[0.0009]]` (:math:`\sigma_R = 0.03\text{ m}^3/\text{m}^3`).
  - Observation operator: :math:`\mathbf{H} = [[1.0, 0.0, 0.0, 0.0]]`.
* Executes ``run_enkf_update()``:
  - Prior Theta: :math:`0.2829 \pm 0.0441`.
  - Posterior Theta: :math:`0.3231 \pm 0.0239`.
  - Kalman Gain on Theta: **0.6885**.
  - Kalman Gain on Bulk Density: **-0.5142**.
* Emits Day 1 assimilation summary to stdout.

3.5 Diagnostic Distribution Plotting (Plot 1)
---------------------------------------------
* Renders Aerospace Plot 1: :math:`2 \times 2` histogram grid displaying prior vs posterior
  probability densities, vertical mean lines, and the observation reference line.

3.6 14-Timestep Sequential Trajectory Tracking
----------------------------------------------
* Sets true reference state :math:`\mathbf{x}_{\text{true}} = [0.5, 1.30, 2.80, 1.45]`.
* Generates 14-step sinusoidal observation sequence:

  .. code-block:: python

     obs_timeline = x_true[0] + 0.02 * np.sin(np.linspace(0, 2*np.pi, 14)) + np.random.normal(0, 0.015, 14)

* Propagates forward ensemble with linear drift :math:`\mathbf{d} = [0.002, -0.001, 0.01, 0.005]^T`
  and random noise :math:`\mathcal{N}(0, 0.005)`.
* Sequentially assimilates :math:`y_t` at each step via ``run_enkf_update()``.
* Computes performance metrics:
  - Pure Prediction RMSE: **0.0608 m$^3$/m$^3$**
  - EnKF Assimilation RMSE: **0.0211 m$^3$/m$^3$**
  - Error Reduction: **65.35%**

3.7 Trajectory Diagnostic Rendering (Plot 2)
--------------------------------------------
* Renders Aerospace Plot 2: Displays Pure Prediction trajectory (dashed orange), SAR Observations
  (red markers), and EnKF Posterior Estimate (cyan curve) alongside an in-graph diagnostic text box.

3.8 Observation Noise Sensitivity Sweep (Plot 3)
------------------------------------------------
* Iterates through 10 logarithmic variance points :math:`R \in [10^{-4}, 10^{-1}]`.
* Evaluates posterior absolute error at each variance level.
* Renders Aerospace Plot 3 showing monotonic increase in posterior error as measurement noise increases.

3.9 Deliverable Summary Compilation
-----------------------------------
* Compiles final DataFrame comparing prior and posterior distributions across all 4 variables:
  - Root-Zone Moisture: :math:`0.2829 \pm 0.0441 \to 0.3231 \pm 0.0239` (**45.9% reduction**)
  - Bulk Density: :math:`1.3656 \pm 0.0937 \to 1.3356 \pm 0.0899` (**4.0% reduction**)
  - Hydraulic Conductivity: :math:`2.4070 \pm 0.6501 \to 2.6507 \pm 0.5855` (**9.9% reduction**)
  - Soil Organic Carbon: :math:`1.2015 \pm 0.2358 \to 1.2657 \pm 0.2275` (**3.5% reduction**)
* Prints deliverable profile table to terminal.

4. Component Design
===================

4.1 Prior Ensemble Sampling Module
----------------------------------
* **Function**: Generates physically realistic state ensembles with cross-variable correlations.
* **Mechanism**:
  Given state standard deviations :math:`\boldsymbol{\sigma} = [\sigma_1, \sigma_2, \sigma_3, \sigma_4]^T`
  and empirical correlation matrix :math:`\mathbf{R}_{\text{corr}}`, the full covariance is:

  .. math::

     \mathbf{\Sigma} = \operatorname{diag}(\boldsymbol{\sigma}) \cdot \mathbf{R}_{\text{corr}} \cdot \operatorname{diag}(\boldsymbol{\sigma})

  Ensemble members are sampled from :math:`\mathcal{N}(\boldsymbol{\mu}, \mathbf{\Sigma})` and
  clipped element-wise to satisfy:

  .. math::

     x_{ij} \leftarrow \operatorname{clip}(x_{ij}, \min_i, \max_i)

4.2 EnKF Update Operator (``run_enkf_update``)
----------------------------------------------
* **Function**: Executes the mathematical Kalman analysis step on state ensemble matrices.
* **Mechanism**:
  1. Ensemble Mean:

     .. math::

        \bar{\mathbf{x}} = \frac{1}{N}\sum_{j=1}^N \mathbf{x}_j \in \mathbb{R}^{n \times 1}

  2. Anomaly Matrix:

     .. math::

        \mathbf{A} = \mathbf{X} - \bar{\mathbf{x}}\mathbf{1}^T \in \mathbb{R}^{n \times N}

  3. Sample Prior Error Covariance:

     .. math::

        \mathbf{P}^f = \frac{1}{N-1}\mathbf{A}\mathbf{A}^T \in \mathbb{R}^{n \times n}

  4. Innovation Covariance:

     .. math::

        \mathbf{S} = \mathbf{H}\mathbf{P}^f\mathbf{H}^T + \mathbf{R} \in \mathbb{R}^{m \times m}

  5. Kalman Gain:

     .. math::

        \mathbf{K} = \mathbf{P}^f\mathbf{H}^T \mathbf{S}^{-1} \in \mathbb{R}^{n \times m}

  6. Perturbed Measurements:

     .. math::

        \mathbf{y}_j = \mathbf{y} + \boldsymbol{\epsilon}_j, \quad \boldsymbol{\epsilon}_j \sim \mathcal{N}(\mathbf{0}, \mathbf{R})

  7. Analysis State Update:

     .. math::

        \mathbf{x}_j^a = \mathbf{x}_j^f + \mathbf{K}\left(\mathbf{y}_j - \mathbf{H}\mathbf{x}_j^f\right)

  8. Posterior Error Covariance:

     .. math::

        \mathbf{P}^a = \frac{1}{N-1}\mathbf{A}^a (\mathbf{A}^a)^T \in \mathbb{R}^{n \times n}

4.3 Sequential Trajectory Engine
--------------------------------
* **Function**: Unrolls dynamic time-series assimilation over forward horizons.
* **Mechanism**: Iterates discrete steps :math:`t = 1, \dots, T_{\text{steps}}`. At each step,
  the ensemble is propagated through forward physics with drift:

  .. math::

     \mathbf{X}_{t+1}^f = \mathbf{X}_t^a + \mathbf{d} + \boldsymbol{\omega}_t, \quad \boldsymbol{\omega}_t \sim \mathcal{N}(\mathbf{0}, \mathbf{Q})

  And updated with the arriving measurement :math:`y_t` via ``run_enkf_update``.

5. Data Structures
==================

5.1 State Variable Definition Schema
------------------------------------
Dictionary ``STATE_VARIABLES`` schema:

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 15 15 20

   * - Variable
     - Mean
     - Std
     - Min
     - Max
     - Unit
   * - ``theta_root``
     - 0.28
     - 0.04
     - 0.05
     - 0.45
     - :math:`\text{m}^3/\text{m}^3`
   * - ``bulk_density``
     - 1.35
     - 0.08
     - 1.00
     - 1.80
     - :math:`\text{g/cm}^3`
   * - ``K_sat``
     - 2.50
     - 0.60
     - 0.01
     - 10.0
     - cm/hr
   * - ``SOC``
     - 1.20
     - 0.25
     - 0.10
     - 4.00
     - %

5.2 Intermediate Matrix Structures
----------------------------------
1. **Prior Ensemble Matrix** (``X_prior``): NumPy float64 array of shape :math:`(4, 50)`.
2. **Posterior Ensemble Matrix** (``X_post``): NumPy float64 array of shape :math:`(4, 50)`.
3. **Prior Covariance Matrix** (``P_f``): NumPy float64 array of shape :math:`(4, 4)`.
4. **Posterior Covariance Matrix** (``P_a``): NumPy float64 array of shape :math:`(4, 4)`.
5. **Kalman Gain Matrix** (``K_gain``): NumPy float64 array of shape :math:`(4, 1)`.
6. **Observation Operator Matrix** (``H_mat``): NumPy float64 array of shape :math:`(1, 4)`.
7. **Observation Noise Covariance** (``R_obs``): NumPy float64 array of shape :math:`(1, 1)`.

5.3 Deliverable Output Schema
-----------------------------
Deliverable DataFrame ``df_deliverable`` columns:
* ``State Variable``: string
* ``Unit``: string
* ``Prior Mean ± Std``: string
* ``Posterior Mean ± Std``: string
* ``Uncertainty Reduction (%)``: string

6. Algorithms and Methods
=========================

6.1 Stochastic Perturbed-Observation EnKF
-----------------------------------------
Standard Kalman filters explicitly propagate covariances via :math:`\mathbf{P}^a = (\mathbf{I} - \mathbf{K}\mathbf{H})\mathbf{P}^f`.
In high-dimensional geophysical domains, this causes covariance rank deficiency.
Burgers et al. (1998) proved that to prevent ensemble spread collapse, observations must be
perturbed by random draws matching the measurement error covariance:

.. math::

   \mathbf{y}_j = \mathbf{y} + \boldsymbol{\epsilon}_j, \quad \boldsymbol{\epsilon}_j \sim \mathcal{N}(\mathbf{0}, \mathbf{R})

The resulting sample covariance of the updated ensemble asymptotically converges to the
true Bayesian analysis error covariance.

6.2 Cross-Variable Covariance Updates
-------------------------------------
Because the observation operator :math:`\mathbf{H} = [1, 0, 0, 0]` directly measures only
soil moisture, unobserved variables are updated purely through background cross-covariances.
The Kalman gain for state variable :math:`i` is:

.. math::

   K_i = \frac{P^f_{i, 0}}{P^f_{0, 0} + R}

Since bulk density is negatively correlated with moisture (:math:`P^f_{1, 0} = -0.30 \cdot \sigma_\theta \sigma_{\rho_b} < 0`),
the Kalman gain on bulk density is negative:

.. math::

   K_1 = -0.5142

Consequently, when the satellite observes a wetter-than-expected moisture level
(:math:`y - H\bar{\mathbf{x}} > 0`), the filter automatically decreases estimated bulk density,
accurately mimicking physical soil compaction physics.

6.3 Multi-Timestep Trajectory Assimilation
------------------------------------------
Sequential filtering executes 14 discrete assimilation epochs. Unconstrained predictions
accumulate systematic drift:

.. math::

   \text{RMSE}_{\text{pred}} = \sqrt{\frac{1}{T}\sum_{t=1}^T (\bar{x}_t^{\text{pred}} - x_{\text{true}})^2} = 0.0608\text{ m}^3/\text{m}^3

While EnKF updates bound the trajectory near ground truth:

.. math::

   \text{RMSE}_{\text{enkf}} = \sqrt{\frac{1}{T}\sum_{t=1}^T (\bar{x}_t^{\text{post}} - x_{\text{true}})^2} = 0.0211\text{ m}^3/\text{m}^3

Achieving a **65.35% error reduction**.

7. Interfaces
-------------

7.1 Function Interface: ``run_enkf_update``
-------------------------------------------
* **Signature**: ``run_enkf_update(X_prior, obs_vector, obs_cov, H_operator)``
* **Inputs**:
  - ``X_prior``: :math:`\mathbb{R}^{n \times N}` array.
  - ``obs_vector``: :math:`\mathbb{R}^{m}` array.
  - ``obs_cov``: :math:`\mathbb{R}^{m \times m}` array.
  - ``H_operator``: :math:`\mathbb{R}^{m \times n}` array.
* **Returns**: Tuple of ``(X_posterior, P_f, P_a, K, innovation)``.

7.2 Output Deliverable Interface
--------------------------------
* Terminal formatted table reporting posterior states and uncertainty reductions.

7.3 Downstream Consumer Interfaces
----------------------------------
* **Consumer**: Notebook 07 (Uncertainty Analysis) and Notebook 08 (Robustness Analysis).
* **Contract**: Supplies assimilated posterior state means :math:`\bar{\mathbf{x}}^a` and
  covariance matrix :math:`\mathbf{P}^a` to initialize Monte Carlo slope failure risk simulations.

8. Configuration
----------------

8.1 Constants
-------------
* ``NUM_MEMBERS = 50``: Ensemble member count.
* ``NUM_STATES = 4``: Number of soil state variables.
* ``R_OBS = 0.0009``: Nominal observation variance (:math:`\sigma_R = 0.03\text{ m}^3/\text{m}^3`).
* ``TIMESTEPS = 14``: Sequential assimilation horizon.
* ``PRED_DRIFT = [0.002, -0.001, 0.01, 0.005]``: Systematic model drift vector.

8.2 Environment
---------------
* Python 3.10+ runtime.
* Backend: NumPy / PyTorch CPU or CUDA.

8.3 Runtime Configuration
-------------------------
* Plotting theme: ``dark_background``.
* Plotting styling:
  - ``axes.edgecolor``: ``#00FFCC``
  - ``axes.linewidth``: 1.2
  - ``grid.color``: ``#1A3344``
  - ``grid.linestyle``: ``--``
  - ``grid.alpha``: 0.5
  - ``font.family``: ``monospace``

8.4 Dependencies
----------------
* ``numpy >= 1.24.0``
* ``pandas >= 2.0.0``
* ``torch >= 2.0.0``
* ``matplotlib >= 3.7.0``

9. Error Handling
-----------------

9.1 Physical State Boundary Clipping
------------------------------------
Multivariate normal sampling can draw values violating physical constraints (e.g., negative
hydraulic conductivity). The software enforces post-sampling clipping:

.. code-block:: python

   for i, var in enumerate(STATE_NAMES):
       ensemble[i, :] = np.clip(ensemble[i, :], STATE_VARIABLES[var]['min'], STATE_VARIABLES[var]['max'])

9.2 Positive Semi-Definiteness Maintenance
------------------------------------------
Sample covariance matrices :math:`\mathbf{P} = \frac{1}{N-1}\mathbf{A}\mathbf{A}^T` are
mathematically guaranteed to be symmetric positive semi-definite, avoiding complex eigenvalues.

10. Generated Artifacts
=======================

10.1 Diagnostic Plot Suite
--------------------------
* **Aerospace Plot 1**: :math:`2 \times 2` histogram grid showing prior (orange) and posterior
  (cyan) ensemble distributions across Root-Zone Moisture, Bulk Density, Hydraulic Conductivity,
  and Soil Organic Carbon.
* **Aerospace Plot 2**: Time-series trajectory comparing Model Prediction, SAR Observations,
  and EnKF Posterior Estimates over 14 timesteps.
* **Aerospace Plot 3**: Semi-log Observation Noise Sensitivity Curve plotting posterior absolute
  error as a function of observation noise variance :math:`R \in [10^{-4}, 10^{-1}]`.

11. Reproducibility
===================

11.1 Random Seeds
-----------------
Fixed seeds ensure deterministic reproduction across NumPy and PyTorch:

.. code-block:: python

   np.random.seed(1607)
   torch.manual_seed(1607)

11.2 Deterministic Numerical Invariants
---------------------------------------
Under seed 1607, the following exact numerical invariants are guaranteed:

* Prior Moisture Mean: Exactly **0.2829 m$^3$/m$^3$** (Std: **0.0441**).
* Posterior Moisture Mean: Exactly **0.3231 m$^3$/m$^3$** (Std: **0.0239**).
* Kalman Gain on Moisture: Exactly **0.6885**.
* Kalman Gain on Bulk Density: Exactly **-0.5142**.
* Pure Prediction RMSE: Exactly **0.0608 m$^3$/m$^3$**.
* EnKF Assimilation RMSE: Exactly **0.0211 m$^3$/m$^3$**.
* Trajectory Error Reduction: Exactly **65.35%**.
* Uncertainty Reductions:
  - Root-Zone Moisture: Exactly **45.9%**
  - Bulk Density: Exactly **4.0%**
  - Hydraulic Conductivity: Exactly **9.9%**
  - Soil Organic Carbon: Exactly **3.5%**

12. Performance Characteristics
===============================

12.1 Execution Time Profile
---------------------------
Measured across standard x86_64 CPU hardware:

* Prior Ensemble Sampling (Cell 06): :math:`< 0.05\text{ s}`
* Single-Step EnKF Update (Cell 08): :math:`< 0.01\text{ s}`
* Histogram Plot Rendering (Cell 10): :math:`\approx 0.6\text{ s}`
* 14-Step Sequential Trajectory Loop (Cell 12): :math:`< 0.05\text{ s}`
* Trajectory Plot Rendering (Cell 14): :math:`\approx 0.5\text{ s}`
* Noise Sensitivity Sweep (Cell 16): :math:`\approx 0.4\text{ s}`
* Deliverable Table Formatting (Cell 18): :math:`< 0.01\text{ s}`
* **Total End-to-End Execution**: :math:`< 2.0\text{ s}`.

12.2 Memory Footprint
---------------------
* Peak RAM Utilization: :math:`< 100\text{ MB}`.
* Ensemble Matrix Allocation: :math:`4 \times 50 \times 8\text{ bytes} = 1.6\text{ KB}`.
* Covariance Allocation: :math:`4 \times 4 \times 8\text{ bytes} = 128\text{ bytes}`.

13. Implementation Notes
========================

13.1 Current Implementation State
---------------------------------
The notebook constitutes a verified mathematical baseline for Ensemble Kalman Filtering.
All matrix contractions, gain evaluations, and statistical distributions execute cleanly.

13.2 Known Implementation Constraints
-------------------------------------
1. **Plot 2 Collapsed Uncertainty Ribbon**: In Cell 12 line 296, the script appends ``.mean()``
   instead of ``.std()`` to ``traj_enkf_std``. In Cell 14 lines 345–346, ``fill_between`` passes
   ``post - 2*std`` for both upper and lower bounds, collapsing the uncertainty band.
2. **Narrative Metric Discrepancy**: Summary text in Cell 17 claims "reduced RMSE from 0.0384 to 0.0091
   (>75% reduction)", but the actual logged run recorded an initial RMSE of 0.0608 and final
   RMSE of 0.0211 (65.35% reduction).
3. **Absence of Disk Serialization**: Deliverable tables and covariance matrices are printed to stdout
   but not saved to ``/data_processed/``.
4. **Decoupled Lumped State Space**: State estimation operates on a 0D point column rather than
   the :math:`20 \times 20` spatial grid from preceding notebooks.
5. **Physical Bounds Inconsistency in Truth**: Synthetic true state :math:`x_{\text{true}}[0] = 0.50`
   exceeds sandy loam saturated moisture capacity (:math:`\theta_s = 0.41`).

13.3 Forward Path to Production
-------------------------------
* Correct ``fill_between`` bounds and append standard deviation in Plot 2.
* Reconcile narrative text with logged execution numbers.
* Add disk serialization: ``np.save('posterior_covariance.npy', P_a)`` and ``df_deliverable.to_csv()``.
* Extend EnKF to spatially distributed 2D grids using spatial covariance localization.

14. Technical Limitations
=========================

14.1 Current Limitations
------------------------
* **0D Point Limitation**: Lacks horizontal spatial coupling between neighboring grid cells.
* **Gaussian Error Assumption**: Assumes prior and observation errors are strictly Gaussian,
  which may fail during bounded saturated conditions.
* **Synthetic Observation Series**: Evaluates artificial sinusoidal observation timelines
  rather than real Sentinel-1 backscatter datacubes.

14.2 Synthetic Domain Boundary
------------------------------
The ensemble distributions and observations are synthetic mathematical constructs. **The
computed Kalman gains and uncertainty reductions verify algorithm mechanics, not in-situ soil
conditions at the Bhadrak/Balasore study footprint.**

15. Requirement Implementation Mapping
======================================

The implementation described across this technical document directly fulfills the
formal software requirements established in ``06_state_estimation_REQUIREMENTS.md``:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Requirement ID
     - Requirement Description
     - Implementing Design Section
   * - **FR-001**
     - Target state vector parameterization
     - Section 3.2, Section 5.1
   * - **FR-002**
     - Cross-variable correlation matrix formulation
     - Section 3.3, Section 4.1
   * - **FR-003**
     - Multivariate normal prior ensemble generation
     - Section 3.3, Section 4.1, Section 9.1
   * - **FR-004**
     - Stochastic perturbed-observation EnKF algorithm
     - Section 3.4, Section 4.2, Section 6.1
   * - **FR-005**
     - Single-step assimilation with :math:`y=0.34`
     - Section 3.4, Section 6.2, Section 11.2
   * - **FR-006**
     - Plot 1 prior vs posterior histogram rendering
     - Section 3.5, Section 10.1
   * - **FR-007**
     - 14-timestep sequential trajectory tracking
     - Section 3.6, Section 4.3, Section 6.3
   * - **FR-008**
     - Prediction vs EnKF RMSE error reduction
     - Section 3.6, Section 6.3, Section 11.2
   * - **FR-009**
     - Plot 2 dynamic trajectory rendering
     - Section 3.7, Section 10.1, Section 13.2
   * - **FR-010**
     - Observation noise variance sensitivity sweep
     - Section 3.8, Section 10.1
   * - **FR-011**
     - Deliverable uncertainty reduction table compilation
     - Section 3.9, Section 5.3, Section 11.2
   * - **DI-001**
     - Covariance matrix positive semi-definiteness
     - Section 4.2, Section 9.2
   * - **DI-002**
     - Observation update variance contraction
     - Section 3.4, Section 11.2
   * - **DI-003**
     - Non-zero cross-variable Kalman gain update
     - Section 3.4, Section 6.2, Section 11.2
   * - **DI-004**
     - Prior ensemble physical boundary clipping
     - Section 3.3, Section 4.1, Section 9.1
   * - **DI-005**
     - Invertible innovation covariance matrix
     - Section 4.2
   * - **IF-001**
     - ``run_enkf_update`` signature and return contract
     - Section 4.2, Section 7.1
   * - **IF-002**
     - Ensemble matrix dimension contract :math:`(4, 50)`
     - Section 3.3, Section 5.2
   * - **IF-003**
     - Deliverable DataFrame column schema
     - Section 3.9, Section 5.3, Section 7.2
   * - **UQ-001**
     - Perturbed observation noise covariance matching :math:`\mathbf{R}`
     - Section 4.2, Section 6.1
   * - **UQ-002**
     - Unbiased sample covariance normalization (:math:`N - 1`)
     - Section 4.2
   * - **UQ-003**
     - High-precision metric reporting in figures
     - Section 3.6, Section 3.7, Section 10.1
   * - **NF-001**
     - Deterministic seed initialization (1607)
     - Section 3.1, Section 11.1
   * - **NF-002**
     - Unattended headless execution
     - Section 2.1, Section 12.1
   * - **NF-003**
     - Dark telemetry UI styling on generated figures
     - Section 3.1, Section 8.3, Section 10.1
   * - **NF-004**
     - Lightweight memory footprint (< 100 MB)
     - Section 12.2
