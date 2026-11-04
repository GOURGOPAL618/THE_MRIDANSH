.. _module_10_ablation_study:

========================================================================
🛰️ Module 10: Component Ablation & Marginal Utility System Audit
========================================================================

:Author: JCC Headquarter (RS-SDA Division) / Gourgopal Mohapatra
:Engine: AETHER-MRID1607X
:Module ID: MRIDANSH-MOD-ABLATION-10
:Notebook Source: ``1_notebooks_sandbox/10-ablation-study.ipynb``
:Verification Suite: ``tests/test_notebook_10_verification.py``
:Last Verification: Verified (8/8 Test Cases Passed)

.. contents:: Table of Contents
   :depth: 3
   :local:

Overview & Scientific Purpose
=============================

Module 10 provides the definitive architectural synthesis and marginal utility assessment for **THE MRIDANSH**. Across Modules 01 through 09, multiple independent modalities and physical modeling paradigms were introduced—optical radiometry, synthetic aperture radar, digital elevation models, meteorological reanalyses, spatiotemporal ConvLSTMs, physics-informed neural Richards equations, Ensemble Kalman Filters, and hyperspectral imaging.

Module 10 rigorously answers the vital systems engineering question:
   *"Which components are truly essential to the mission, and which are dispensable?"*

To prevent optimistic spatial cross-talk, all evaluations are conducted on an isolated spatial block holdout partition (80% training / 20% contiguous held-out test quadrant). The module tracks the sequential descent in Root Mean Squared Error (RMSE) across an 8-stage configuration ladder, benchmarks inference latencies, computes Pareto efficiencies, and formally categorizes each technology into three operational governance tiers.

Spatial Block Partitioning & Zero-Leakage Protocol
==================================================

The spatial catchment mesh comprises :math:`N = 400` units on a :math:`20 \times 20` grid. Rather than random pixel splitting (which allows spatial autocorrelation to leak information into adjacent test pixels), the domain is partitioned geographically:
- **Training Partition**: 320 contiguous spatial pixels (:math:`80.0\%`).
- **Held-Out Test Quadrant**: 80 contiguous spatial pixels (:math:`20.0\%`), strictly bounded by Rows 12–20 and Columns 10–20.

All feature normalizations and model parameters are fitted strictly on the training partition and evaluated out-of-sample on the held-out quadrant.

The 8-Stage Incremental Model Ladder
====================================

The system evaluates eight progressive architectural configurations:

.. list-table:: Eight-Stage Incremental Configuration Ladder
   :widths: 15 35 25 25
   :header-rows: 1

   * - Configuration
     - Integrated Modalities & Layers
     - Test RMSE (:math:`\text{m}^3/\text{m}^3`)
     - Marginal Delta (:math:`\Delta\text{RMSE}`)
   * - **Config A**
     - Sentinel-2 Optical (Blue, Green, Red, NIR)
     - :math:`0.0914`
     - Baseline Reference
   * - **Config B**
     - Config A + Sentinel-1 SAR Backscatter (VV, VH)
     - :math:`0.0504`
     - :math:`-44.85\%` (Leap 1: SAR Cloud Penetration)
   * - **Config C**
     - Config B + Copernicus Topography (DEM, Slope)
     - :math:`0.0468`
     - :math:`-7.14\%`
   * - **Config D**
     - Config C + ECMWF Weather (Temperature, Precip)
     - :math:`0.0336`
     - :math:`-28.23\%` (Leap 2: Meteorological Forcing)
   * - **Config E**
     - Config D + ConvLSTM Spatiotemporal Dynamics
     - :math:`0.0302`
     - :math:`-10.12\%`
   * - **Config F**
     - Config E + PINN Richards PDE Moisture Prior
     - :math:`0.0231`
     - :math:`-23.52\%` (Leap 3: Mass Conservation)
   * - **Config G**
     - Config F + EnKF Sequential Data Assimilation
     - :math:`0.0165`
     - :math:`-28.56\%` (Leap 4: Real-time Assimilation)
   * - **Config H**
     - Config G + Hyperspectral (Top 10 HSI PCs)
     - :math:`0.0047`
     - :math:`-71.51\%` (Targeted On-Demand Modality)

Strict Monotonic Descent Invariant:

.. math::

   \text{RMSE}_A > \text{RMSE}_B > \text{RMSE}_C > \text{RMSE}_D > \text{RMSE}_E > \text{RMSE}_F > \text{RMSE}_G > \text{RMSE}_H

Uncertainty Contraction & Computational Efficiency
==================================================

Predictive Uncertainty Contraction
----------------------------------

Predictive uncertainty variance was audited using a 30-member bootstrap ensemble (:math:`B=30`). Integrating physical constraints (PINN) and EnKF sequential filtering systematically contracted the error envelope from :math:`\pm 0.082\text{ m}^3/\text{m}^3` in Config A down to :math:`\pm 0.014\text{ m}^3/\text{m}^3` in Config G.

Inference Latency & Pareto Efficiency
-------------------------------------

Inference latency was profiled across 1000 Monte Carlo iterations on host hardware:
- **Config A**: :math:`0.24\text{ ms}`
- **Config D**: :math:`0.48\text{ ms}`
- **Config G (Full Production Stack)**: :math:`1.12\text{ ms}` (Sweet spot: Real-time capable at :math:`> 850\text{ Hz}`)
- **Config H (With HSI)**: :math:`2.68\text{ ms}` (:math:`2.4\times` slowdown over Config G)

Pareto analysis confirms that **Config G** achieves the optimal trade-off between estimation accuracy and real-time computational throughput.

Component Essentiality Governance Tiers
=======================================

Based on the empirical marginal utility and sensitivity audits, pipeline components are formally designated into three operational governance tiers:

1. **Tier 1 (Mission-Critical Core)**:
   - *Components*: Sentinel-1 SAR Backscatter, Richards PINN Physics, Ensemble Kalman Filter (EnKF).
   - *Governance*: Mandatory. The system cannot operate safely or meet aerospace error thresholds without these three core pillars.

2. **Tier 2 (High-Value Enhancements)**:
   - *Components*: Sentinel-2 Optical MSI, ECMWF ERA5 Weather Telemetry, Copernicus DEM.
   - *Governance*: Standard Operational Stack. Provide essential contextual and meteorological forcing data.

3. **Tier 3 (Conditional / On-Demand Augmentation)**:
   - *Components*: Continuous Hyperspectral Imaging (HSI).
   - *Governance*: On-Demand Targeted Deployments. Deployed exclusively for high-risk critical infrastructure sites during cloud-free windows.

Generated Artifacts & Visualizations
====================================

The module generates 5 high-resolution diagnostic plots and 2 persistent checkpoint files in ``5_storage/notebook_results/notebook_10_ablation_study/`` and ``5_storage/checkpoints/``:

1. **Step-by-Step RMSE Reduction Trajectory (plot_01_step_by_step_rmse_reduction_trajectory.png)**: Staircase descent plot illustrating the 8-stage error contraction with percentage leaps annotated.
2. **Predictive Uncertainty Contraction (plot_02_predictive_uncertainty_contraction_trajectory.png)**: Bootstrap variance envelopes contracting across the 8 configurations.
3. **Pareto Efficiency: Accuracy vs Latency (plot_03_pareto_efficiency_accuracy_vs_latency.png)**: Pareto frontier mapping estimation precision against inference latency.
4. **Marginal Delta RMSE Waterfall (plot_04_marginal_delta_rmse_waterfall.png)**: Waterfall chart isolating the individual marginal accuracy contribution of each layer.
5. **Component Essentiality Decision Matrix (plot_05_component_essentiality_decision_matrix.png)**: Strategic bubble chart mapping Technical Essentiality against Operational Readiness.

Data Files:
- ``5_storage/checkpoints/ablation_study_checkpoint.pt``: Serialized checkpoint containing configuration arrays, RMSE ladders, and tier mappings.
- ``5_storage/checkpoints/ABLATION_STUDY_MANIFEST.md``: Production markdown manifest certifying the architectural freeze.

Verification & Test Coverage
============================

The verification suite ``tests/test_notebook_10_verification.py`` enforces 8 automated tests:

* ``test_01_notebook_10_structure_and_interleaving``: Confirms exactly 36 cells with strictly alternating markdown/code, executive summary, and IP notice.
* ``test_02_spatial_block_holdout_zero_data_leakage``: Validates zero spatial leakage with 320 train pixels and 80 test block pixels (Rows 12-20, Cols 10-20).
* ``test_03_eight_stage_incremental_ablation_matrix``: Verifies strict monotonic error descent across all 8 configs and confirms major drops (-44.85%, -28.23%, -23.52%, -28.56%).
* ``test_04_uncertainty_quantification_and_variance_contraction``: Confirms bootstrap ensemble (:math:`B=30`) uncertainty contraction.
* ``test_05_computational_latency_and_pareto_frontier``: Audits 1000-run latency micro-benchmarks and Pareto efficiency.
* ``test_06_component_essentiality_tier_determination``: Confirms formal categorization into Tier 1, Tier 2, and Tier 3.
* ``test_07_embedded_and_standalone_visual_plots``: Audits physical presence of all 5 plots on disk (>50KB) and confirms base64 image embedding in notebook cells.
* ``test_08_checkpoint_and_manifest_certification``: Confirms presence of certified checkpoint and manifest in ``5_storage/checkpoints/``.

Known Defects & Engineering Limitations
========================================

* **D-NB10-001 (Arbitrary Test Quadrant Selection)**: The spatial holdout block is fixed to the top-right quadrant (Rows 12-20, Cols 10-20), which may carry localized topographical bias compared to a k-fold spatial checkerboard cross-validation.
* **D-NB10-002 (Harmonized Ridge Regression Proxy)**: The 8-stage ablation evaluates linear ridge regression models across feature combinations rather than re-training complete deep GCN/ConvLSTM networks from scratch for each subset.
* **D-NB10-003 (Host CPU Latency Profiling)**: Inference latencies were micro-benchmarked on a general-purpose host CPU rather than a specialized flight-grade embedded accelerator (e.g. NVIDIA Jetson Orin).
* **D-NB10-004 (Linear Bootstrap Uncertainty Approximation)**: Bootstrap predictive variance reflects sample variation of the linear estimator rather than full Bayesian neural network weight posterior sampling.
