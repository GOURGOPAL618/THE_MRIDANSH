.. _module_09_hyperspectral_experiment:

========================================================================
🛰️ Module 09: Hyperspectral Augmentation & Spectral Information Audit
========================================================================

:Author: JCC Headquarter (RS-SDA Division) / Gourgopal Mohapatra
:Engine: AETHER-MRID1607X
:Module ID: MRIDANSH-MOD-HSI-09
:Notebook Source: ``1_notebooks_sandbox/09-hyperspectral-experiment.ipynb``
:Verification Suite: ``tests/test_notebook_09_verification.py``
:Last Verification: Verified (8/8 Test Cases Passed)

.. contents:: Table of Contents
   :depth: 3
   :local:

Overview & Scientific Purpose
=============================

Module 09 executes the rigorous hypothesis-driven hyperspectral imaging (HSI) augmentation experiment of **THE MRIDANSH**. The study investigates whether augmenting multi-sensor earth observations (Sentinel-1 SAR, Sentinel-2 Multispectral, Copernicus DEM, and ECMWF Weather) with continuous 224-channel hyperspectral signatures (400 nm to 2500 nm) delivers statistically significant error and uncertainty reductions that justify the operational penalties in data bandwidth, processing latency, and cloud sensitivity.

The module provides an end-to-end scientific assessment:
1. **Atmospheric Telluric Filtering**: Automatic excision of 24 water vapor absorption channels ($1350-1420\text{ nm}$ and $1800-1950\text{ nm}$), retaining 200 science-grade bands.
2. **Pure Mathematical SVD/PCA Compression**: Singular Value Decomposition compressing 200 spectral dimensions into 10 orthogonal principal components with zero external library dependencies.
3. **Controlled A/B Evaluation on Identical Splits**: Direct comparison of CONFIG-A (Frozen Baseline Stack) vs CONFIG-B (HSI-Augmented Stack).
4. **Predictive Uncertainty & Fail-Soft Resilience**: Proving uncertainty variance reduction and confirming that 100% HSI dropout reverts seamlessly to the baseline.
5. **Architectural Trade-Off Directive**: Formal certification of the system directive: ``CASE 2: MODERATE/CONDITIONAL IMPROVEMENT -> TARGETED OPTIONAL AUGMENTATION``.

Spectroscopic Principles & Preprocessing
========================================

Spectral Domain & Absorption Features
-------------------------------------

The continuous spectrum spans 400 nm to 2500 nm with a nominal bandwidth of 10 nm across 224 contiguous bands. Liquid water and hydroxyl ion ($OH^-$) vibrational absorption overtone bands dominate soil reflectance:
- Fundamental :math:`H_2O` stretching/bending overtones at 970 nm, 1200 nm, 1450 nm, and 1940 nm.
- Strong atmospheric telluric absorption bands obscuring ground signals:
  - Band 1: :math:`1350 - 1420\text{ nm}` (1200 - 1450 nm region)
  - Band 2: :math:`1800 - 1950\text{ nm}` (1800 - 1980 nm region)

Atmospheric Quality Control Invariant:
- Total input channels: :math:`224`
- Excised telluric channels: :math:`24`
- Retained scientific channels: :math:`200`

SVD / PCA Dimensionality Reduction
----------------------------------

To overcome high multi-collinearity and the curse of dimensionality, Principal Component Analysis is executed via pure SVD on centered reflectance matrices:

.. math::

   \mathbf{X}_{\text{centered}} = \mathbf{X} - \bar{\mathbf{x}}

.. math::

   \mathbf{X}_{\text{centered}} = \mathbf{U} \mathbf{\Sigma} \mathbf{V}^T

The top :math:`k = 10` right singular vectors :math:`\mathbf{V}_{[:10]}^T` form the orthogonal projection basis. The explained variance ratio is:

.. math::

   \lambda_i = \frac{\Sigma_i^2}{\sum_{j=1}^{200} \Sigma_j^2}

Verified invariant: The top 10 principal components account for **99.2%** of cumulative spectral variance (:math:`\ge 99.0\%` requirement verified).

Controlled A/B Testing & Empirical Performance
==============================================

Model Configurations
--------------------

Both models are trained on identical 80/20 data partitions using analytical ridge regression with closed-form solver:

.. math::

   \mathbf{w} = \left( \mathbf{X}_{\text{aug}}^T \mathbf{X}_{\text{aug}} + \alpha \mathbf{I}^* \right)^{-1} \mathbf{X}_{\text{aug}}^T \mathbf{y}

- **CONFIG-A (Frozen Baseline Stack)**:
  - Features: Sentinel-2 (4 bands), Sentinel-1 SAR (2 bands), DEM (2 bands), Weather (2 bands), ConvLSTM / PINN state priors (2 states).
  - Total input dimension: :math:`12`.
- **CONFIG-B (HSI-Augmented Stack)**:
  - Features: CONFIG-A features concatenated with top 10 HSI principal components.
  - Total input dimension: :math:`22`.

Empirical Benchmark Results
---------------------------

.. list-table:: Controlled A/B Experimental Scorecard
   :widths: 25 25 25 25
   :header-rows: 1

   * - Metric
     - CONFIG-A (Baseline)
     - CONFIG-B (With HSI)
     - Marginal Delta
   * - Root Mean Squared Error (RMSE)
     - :math:`0.0455\text{ m}^3/\text{m}^3`
     - :math:`0.0047\text{ m}^3/\text{m}^3`
     - :math:`-89.67\%`
   * - Mean Absolute Error (MAE)
     - :math:`0.0384\text{ m}^3/\text{m}^3`
     - :math:`0.0038\text{ m}^3/\text{m}^3`
     - :math:`-90.10\%`
   * - Coefficient of Determination (:math:`R^2`)
     - :math:`0.7182`
     - :math:`0.9968`
     - :math:`+0.2786`
   * - Mean Predictive Uncertainty (:math:`\sigma`)
     - :math:`0.0345\text{ m}^3/\text{m}^3`
     - :math:`0.0038\text{ m}^3/\text{m}^3`
     - :math:`-89.01\%`
   * - Inference Latency
     - :math:`1.02\text{ ms}`
     - :math:`2.45\text{ ms}`
     - :math:`+140.2\%` (:math:`2.4\times`)
   * - Data Telemetry Volume
     - :math:`1.2\text{ MB/tile}`
     - :math:`18.4\text{ MB/tile}`
     - :math:`+1433\%` (:math:`15.3\times`)

Fail-Soft Sensor Dropout Resilience
-----------------------------------

When HSI channels are subject to complete ($100\%$) hardware dropout, zero-padding the HSI feature slots causes the model to gracefully revert to the CONFIG-A baseline error level without system exceptions, satisfying fail-soft fault tolerance.

Decision Architecture & Formal Verdict
======================================

Multi-Criteria Decision Evaluation
----------------------------------

While HSI achieves remarkable accuracy gains on cloud-free tiles, spaceborne HSI introduces severe operational constraints:
- Inability to penetrate monsoon cloud cover (optical limitation).
- 15-fold increase in raw telemetry downlink bandwidth.
- Coarser revisit frequency (15-30 days for PRISMA/EnMAP vs 5 days for Sentinel-2).

Formal System Directive: CASE 2
-------------------------------

The architectural outcome is officially classified as:

   **CASE 2 : MODERATE/CONDITIONAL IMPROVEMENT -> TARGETED OPTIONAL AUGMENTATION**

   *Deployment Directive*:
   Retain **CONFIG-A** (Sentinel-1 + Sentinel-2 + DEM + Weather + PINN Physics + EnKF) as the lean, unencumbered 24/7 continuous production backbone. Deploy **CONFIG-B** (HSI-Augmented) strictly as an on-demand, high-precision targeted modality for critical infrastructure risk assessments during cloud-free periods, with autonomous fail-soft reversion to CONFIG-A.

Generated Artifacts & Visualizations
====================================

The module generates 7 aerospace plots and 3 persistent data artifacts in ``5_storage/notebook_results/notebook_09_hyperspectral_experiment/`` and ``5_storage/checkpoints/``:

1. **Spectral Signatures & Atmospheric Masks (plot_01_soil_spectral_signatures_and_atmospheric_masks.png)**: 224-band reflectance curves across moisture regimes with telluric drop bands shaded.
2. **Multispectral vs Hyperspectral Entropy (plot_02_sentinel2_vs_hyperspectral_bandwidth_entropy.png)**: Bandwidth and entropy comparison between 13 discrete MSI bands and 200 contiguous HSI channels.
3. **PCA Scree & Cumulative Variance (plot_03_pca_scree_and_cumulative_variance.png)**: Eigenvalue decay curve demonstrating :math:`>99.0\%` variance in top 10 principal components.
4. **Controlled A/B Predictions & Residuals (plot_04_controlled_ab_predictions_and_residuals.png)**: Scatter regression and residual histograms comparing CONFIG-A vs CONFIG-B.
5. **Predictive Uncertainty Distributions (plot_05_predictive_uncertainty_distributions.png)**: Uncertainty standard deviation contraction under HSI augmentation.
6. **Sensor Dropout & Fallback Profile (plot_06_sensor_dropout_and_fallback_profile.png)**: Stepwise degradation curve during partial HSI dropout.
7. **Master Trade-Off Decision Scorecard (plot_07_master_decision_tradeoff_scorecard.png)**: Multi-criteria comparison highlighting accuracy vs computational cost.

Data Files:
- ``5_storage/checkpoints/hsi_experiment_checkpoint.pt``: Serialized checkpoint containing PCA components, explained variance, projection weights, and verdict.
- ``5_storage/checkpoints/HSI_EXPERIMENT_MANIFEST.md``: Production markdown manifest documenting scientific findings, operational constraints, and deployment directives.
- ``5_storage/notebook_results/notebook_09_hyperspectral_experiment/hsi_experiment_metrics.json``: Machine-readable summary of validation metrics.

Verification & Test Coverage
============================

The verification suite ``tests/test_notebook_09_verification.py`` enforces 8 automated tests:

* ``test_01_notebook_09_structure_and_interleaving``: Confirms exactly 36 cells with strictly alternating markdown/code and zero errors.
* ``test_02_hsi_sensor_and_atmospheric_qc``: Verifies 224 input channels, 24 telluric dropped, and 200 science bands retained.
* ``test_03_pca_dimensionality_reduction_kaiser``: Audits top 10 PCs explaining :math:`\ge 99.0\%` cumulative variance.
* ``test_04_controlled_ab_testing_identical_splits``: Confirms evaluation of CONFIG-A vs CONFIG-B on identical splits.
* ``test_05_uncertainty_quantification_and_variance_reduction``: Asserts predictive variance reduction (:math:`\Delta \sigma < 0`).
* ``test_06_sensor_dropout_and_failsoft_resilience``: Verifies autonomous fallback to CONFIG-A under 100% HSI dropout.
* ``test_07_computational_tradeoff_and_case2_verdict``: Confirms formal classification as Case 2 with recorded latency penalties.
* ``test_08_checkpoint_and_manifest_certified``: Validates checkpoint presence in ``5_storage/checkpoints/``.

Known Defects & Engineering Limitations
========================================

* **D-NB09-001 (Synthetic Spectral Signatures)**: Continuous 224-band reflectance was mathematically synthesized using Gaussian absorption profiles rather than sliced from spaceborne PRISMA/EnMAP L2D image cubes.
* **D-NB09-002 (Linear Estimator Simplification)**: A/B testing employed an analytical linear ridge regressor rather than a deep non-linear Graph Neural Network.
* **D-NB09-003 (Coarse Spaceborne Spatial Resolution)**: The 10m spatial resolution matching Sentinel-2 does not reflect the native 30m resolution of real spaceborne HSI sensors.
* **D-NB09-004 (Static Atmospheric Absorption Masking)**: Telluric absorption bands are eliminated via hardcoded wavelength cutoffs without dynamic radiative transfer modeling.
