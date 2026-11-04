.. _module_06_state_estimation:

========================================================================
🛰️ Module 06: Sequential Soil-State Estimation & Ensemble Kalman Filter
========================================================================

:Author: JCC Headquarter (RS-SDA Division) / Gourgopal Mohapatra
:Engine: AETHER-MRID1607X
:Module ID: MRIDANSH-MOD-STATE-06
:Notebook Source: ``1_notebooks_sandbox/06-state-estimation.ipynb``
:Verification Suite: ``tests/test_notebook_06_verification.py``
:Last Verification: Verified (7/7 Test Cases Passed)

.. contents:: Table of Contents
   :depth: 3
   :local:

Overview & Scientific Purpose
=============================

Module 06 constitutes the real-time data assimilation engine of **THE MRIDANSH**. Operating downstream of data cleaning (Module 02), ConvLSTM autoregressive forecasting (Module 04), and physics-informed Richards equation neural networks (Module 05), this module synthesizes observational data with theoretical physical projections using the stochastic Ensemble Kalman Filter (EnKF, Burgers et al. 1998; Evensen 2003).

The engine addresses a fundamental operational question:
   *"Does assimilating noisy satellite telemetry observations actually reduce prediction drift and provide superior state estimates compared to unconstrained neural forecasting?"*

The quantitative results demonstrate that sequential EnKF assimilation achieves a **>70% reduction in RMSE** relative to open-loop predictions while contracting posterior state uncertainty across all pedological variables.

Target State Space & Pedological Cross-Covariances
==================================================

The state space models four coupled physical properties of the Bhadrak subgrade:

.. list-table:: Target Soil State Variables
   :widths: 20 15 20 20 25
   :header-rows: 1

   * - State Variable
     - Symbol
     - Physical Units
     - Physical Bounds
     - Pedological Coupling
   * - Root-Zone Moisture
     - :math:`\theta_{\text{root}}`
     - :math:`\text{m}^3/\text{m}^3`
     - :math:`[0.078, 0.430]`
     - Primary observed state
   * - Dry Bulk Density
     - :math:`\rho_b`
     - :math:`\text{g/cm}^3`
     - :math:`[1.00, 1.80]`
     - Negatively correlated with moisture and organic matter
   * - Saturated Conductivity
     - :math:`K_{\text{sat}}`
     - :math:`\text{cm/hr}`
     - :math:`[0.01, 10.0]`
     - Positively correlated with macro-porosity
   * - Soil Organic Carbon
     - :math:`\text{SOC}`
     - :math:`\%`
     - :math:`[0.10, 4.00]`
     - Modulates aggregate stability and retention

Correlated Prior Ensemble Sampling
----------------------------------

A 50-member Monte Carlo prior ensemble :math:`\mathbf{X}^f \in \mathbb{R}^{4 \times 50}` is initialized via Cholesky decomposition of a prescribed pedological correlation matrix :math:`\mathbf{C}`:

.. math::

   \mathbf{C} = \begin{bmatrix}
   1.00 & -0.45 & +0.50 & +0.30 \\
   -0.45 & 1.00 & -0.40 & -0.65 \\
   +0.50 & -0.40 & 1.00 & +0.25 \\
   +0.30 & -0.65 & +0.25 & 1.00
   \end{bmatrix}

.. math::

   \mathbf{\Sigma} = \operatorname{diag}(\boldsymbol{\sigma}) \cdot \mathbf{C} \cdot \operatorname{diag}(\boldsymbol{\sigma}) = \mathbf{L} \mathbf{L}^T

.. math::

   \mathbf{X}^f = \bar{\mathbf{x}} + \mathbf{L} \mathbf{Z}, \quad \mathbf{Z} \sim \mathcal{N}(\mathbf{0}, \mathbf{I}_{4 \times 50})

Ensemble Kalman Filter Mathematical Framework
=============================================

Prior Error Covariance
----------------------

Given prior ensemble matrix :math:`\mathbf{X}^f \in \mathbb{R}^{4 \times N_e}` (:math:`N_e = 50`), the ensemble mean :math:`\bar{\mathbf{x}}^f` and anomaly matrix :math:`\mathbf{A}^f` are defined as:

.. math::

   \bar{\mathbf{x}}^f = \frac{1}{N_e} \sum_{j=1}^{N_e} \mathbf{x}_j^f, \quad \mathbf{A}^f = \mathbf{X}^f - \bar{\mathbf{x}}^f \mathbf{1}^T

The sample prior covariance :math:`\mathbf{P}^f` is computed without explicit matrix storage:

.. math::

   \mathbf{P}^f = \frac{1}{N_e - 1} \mathbf{A}^f (\mathbf{A}^f)^T

Stochastic Observation Update
-----------------------------

To prevent filter inbreeding and variance collapse, observations :math:`\mathbf{y}` are perturbed with Gaussian noise matching the measurement error covariance :math:`\mathbf{R}`:

.. math::

   \mathbf{d}_j = \mathbf{y} + \boldsymbol{\epsilon}_j, \quad \boldsymbol{\epsilon}_j \sim \mathcal{N}(\mathbf{0}, \mathbf{R})

The Kalman Gain :math:`\mathbf{K} \in \mathbb{R}^{4 \times 1}` is evaluated using the innovation covariance :math:`\mathbf{S}`:

.. math::

   \mathbf{S} = \mathbf{H} \mathbf{P}^f \mathbf{H}^T + \mathbf{R}

.. math::

   \mathbf{K} = \mathbf{P}^f \mathbf{H}^T \mathbf{S}^{-1}

The analysis update step updates all state variables simultaneously:

.. math::

   \mathbf{x}_j^a = \mathbf{x}_j^f + \mathbf{K} \left( \mathbf{d}_j - \mathbf{H} \mathbf{x}_j^f \right)

Indirect Cross-Variable Assimilation
------------------------------------

Because :math:`\mathbf{P}^f` contains non-zero off-diagonal terms, observing only surface moisture updates unobserved physical variables:
- Moisture update: :math:`K_{\theta} > 0.0` (direct correction)
- Bulk density update: :math:`K_{\rho_b} < 0.0` (indirect pedological correction)
- Hydraulic conductivity update: :math:`K_{K_s} > 0.0`
- Organic carbon update: :math:`K_{\text{SOC}} > 0.0`

Dynamic Sequential Filtering & Empirical Findings
=================================================

Dynamic Trajectory Tracking
---------------------------

The filter was evaluated across a 14-timestep non-stationary wetting and recession cycle:
- **Pure Prediction RMSE**: :math:`0.0630\text{ m}^3/\text{m}^3`
- **EnKF Posterior RMSE**: :math:`0.0142\text{ m}^3/\text{m}^3`
- **Error Reduction Rate**: :math:`77.46\%`
- **Root Moisture Uncertainty Reduction**: :math:`42.3\%`
- **Bulk Density Uncertainty Reduction**: :math:`18.7\%`
- **Filter Stability Status**: ``CONVERGED_STABLE``

Spatial Catchment Assimilation
------------------------------

The algorithm scales to 2D spatial meshes (:math:`20 \times 20` nodes, :math:`N = 400`):
- Mean prior spatial variance across the basin: :math:`0.0018`
- Mean posterior spatial variance after assimilation: :math:`0.0008`
- Mean spatial uncertainty reduction rate: :math:`55.6\%` (:math:`> 50.0\%` requirement verified).

Observation Noise Sensitivity
-----------------------------

A logarithmic sweep across sensor variance :math:`R \in [10^{-4}, 10^{-1}]` verified that the filter gracefully transitions between measurement trust (:math:`R \to 0, K \to 1`) and physical model trust (:math:`R \to \infty, K \to 0`).

Generated Artifacts & Visualizations
====================================

The module generates 5 diagnostic plots and 3 persistent data artifacts in ``5_storage/notebook_results/notebook_06_state_estimation/`` and ``5_storage/state_database/``:

1. **Prior vs Posterior Distributions (plot_01_prior_vs_posterior_distributions.png)**: 4-panel histogram confirming significant uncertainty contraction across all 4 state variables.
2. **Kalman Gain & Covariance Matrices (plot_02_kalman_gain_cross_covariance.png)**: Heatmaps of :math:`\mathbf{P}^f`, :math:`\mathbf{P}^a`, and the cross-variable gain vector :math:`\mathbf{K}`.
3. **Dynamic Trajectory Convergence (plot_03_dynamic_trajectory_convergence.png)**: 14-timestep sequential trajectory tracking comparing ground truth, unconstrained forecast, and EnKF analysis.
4. **Noise Sensitivity Sweep (plot_04_noise_sensitivity_sweep.png)**: Logarithmic curve showing Kalman weight decay as observation error increases.
5. **Spatial Grid EnKF Assimilation (plot_05_spatial_grid_enkf_assimilation.png)**: 4-panel spatial map illustrating 2D moisture updating and variance contraction.

Data Archives:
- ``5_storage/state_database/enkf_state_database.pt``: Complete state database bundle containing ensemble states, covariance matrices, Kalman gains, and trajectories.
- ``5_storage/state_database/ENKF_STATE_ESTIMATION_MANIFEST.md``: Production markdown manifest documenting filter parameters and error reductions.
- ``5_storage/notebook_results/notebook_06_state_estimation/enkf_state_estimation_metrics.json``: Machine-readable summary of validation metrics.

Verification & Test Coverage
============================

The verification suite ``tests/test_notebook_06_verification.py`` enforces 7 automated tests:

* ``test_01_no_python_scripts_in_notebook_dir``: Confirms zero Python scripts in sandbox directory.
* ``test_02_notebook_cell_structure_and_markdown_rules``: Validates alternating markdown/code layout (:math:`\ge 30` cells).
* ``test_03_all_code_cells_executed_with_zero_errors``: Audits all 15 code cells executed with 0 runtime errors.
* ``test_04_penultimate_and_ultimate_markdown_cells``: Audits presence of Executive Summary and Intellectual Property notices.
* ``test_05_storage_artifacts_and_plots_persisted``: Validates file presence and size thresholds (>50KB) for all 5 plots and metrics JSON.
* ``test_06_checkpoint_and_manifest_compliance``: Validates physical presence of state database and manifest in ``5_storage/state_database/``, asserts shape :math:`(4, 50)`, and confirms finite values.
* ``test_07_assimilation_validation_and_error_reduction``: Asserts error reduction :math:`\ge 70\%`, posterior RMSE :math:`< 0.025`, moisture uncertainty reduction :math:`\ge 35\%`, and spatial variance reduction :math:`\ge 50\%`.

Known Defects & Engineering Limitations
========================================

* **D-NB06-001 (Gaussian Perturbation for SAR Radar Noise)**: Observations are perturbed via Gaussian noise :math:`\mathcal{N}(0, R)` rather than skewed Gamma speckle distributions, slightly underestimating heavy-tailed flood observation errors.
* **D-NB06-002 (Identity Observation Operator)**: :math:`\mathbf{H} = [1, 0, 0, 0]` equates surface satellite penetration depth (:math:`0-5\text{ cm}`) directly with the root-zone moisture (:math:`0-100\text{ cm}`), ignoring infiltration lag during storm inception.
* **D-NB06-003 (Static Multiplicative Inflation Omission)**: The filter lacks adaptive covariance inflation, risking ensemble spread collapse during prolonged drydown periods.
* **D-NB06-004 (Unlocalized Spatial Covariance)**: 2D spatial grid assimilation updates all cells without distance-based Gaspari-Cohn tapering, which could theoretically allow spurious long-distance updates in larger basins.
