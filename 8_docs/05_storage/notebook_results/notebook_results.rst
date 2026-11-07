.. _subsystem_05_notebook_results:

========================================================================================
Subsystem 05: Scientific Research & Audit Evidence Repository (notebook_results)
========================================================================================

:Engine: AETHER-MRID1607X
:Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
:Lead Architect: Gourgopal Mohapatra
:Status: FROZEN_OPERATIONAL_RELEASE_v1.0

Overview and Subsystem Mandate
==============================

The ``5_storage/notebook_results/`` directory serves as the centralized empirical evidence repository
and scientific audit archive for the **AETHER-MRID1607X** platform. Encompassing the entire 12-stage
experimental research and operational validation pipeline, this subsystem permanently preserves
diagnostic visualizations, intermediate model checkpoints, evaluation metrics, and ablation matrices.

Primary objectives:

1. **Empirical Reproducibility:** Ensure every scientific figure, performance table, and algorithmic
   claim in certification manuscripts can be deterministically re-generated from stored artifacts.
2. **Sequential Traceability:** Maintain an unbroken provenance chain connecting raw satellite ingestion
   (Stage 01) through physics integration (Stage 05) to final operational release certification (Stage 12).
3. **Decisive Architectural Evidence:** Archive the quantitative benchmarks supporting critical system
   decisions, including sensor tiering, latency budgets, and fail-soft fallback policies.

Master 12-Stage Repository Directory Catalog
============================================

.. list-table:: 12-Stage Research & Audit Directory Summary
   :widths: 24 10 36 30
   :header-rows: 1

   * - Directory Name
     - Files
     - Research Focus
     - Primary Persisted Artifacts
   * - ``notebook_01_ingestion/``
     - 8
     - STAC Spaceborne Multi-Sensor Ingestion
     - ``stac_catalog_item.json``, ``stac_telemetry_raw.csv``, 6 Plots
   * - ``notebook_02_preprocessing/``
     - 6
     - Lee Speckle Filtering & MinMax Scaling
     - ``scaler_manifest.json``, ``preprocessed_telemetry.csv``, 4 Plots
   * - ``notebook_03_spatial_modeling/``
     - 10
     - Topographic KNN Graphs & GCN Embeddings
     - ``spatial_gcn_embeddings.pt``, ``spatial_graph_mesh.npz``, 6 Plots
   * - ``notebook_04_temporal_modeling/``
     - 8
     - Spatio-Temporal ConvLSTM Dynamics
     - ``convlstm_model_init.pt``, ``temporal_latent_states.pt``, 5 Plots
   * - ``notebook_05_physics_validation/``
     - 7
     - Continuous Richards PINN Verification
     - ``pinn_richards_model.pt``, ``pinn_physics_metrics.json``, 5 Plots
   * - ``notebook_06_state_estimation/``
     - 7
     - Stochastic Ensemble Kalman Filter
     - ``enkf_state_database.pt``, ``enkf_state_estimation_metrics.json``, 5 Plots
   * - ``notebook_07_uncertainty_analysis/``
     - 7
     - Split-Conformal Uncertainty Calibration
     - ``uncertainty_registry.pt``, ``uncertainty_analysis_metrics.json``, 5 Plots
   * - ``notebook_08_robustness_and_failure/``
     - 7
     - Sensor Dropout Stress & Self-Healing
     - ``robustness_stress_logs.pt``, ``robustness_analysis_metrics.json``, 5 Plots
   * - ``notebook_09_hyperspectral_experiment/``
     - 9
     - 200-Band Hyperspectral PRISMA Module
     - ``hsi_experiment_checkpoint.pt``, ``hsi_experiment_metrics.json``, 7 Plots
   * - ``notebook_10_ablation_study/``
     - 5
     - 8-Config Marginal Utility Decomposition
     - Plots 01--05 (Pareto, Waterfall, Decision Matrix)
   * - ``notebook_11_generalization/``
     - 5
     - 5-Regime Out-of-Distribution Stress
     - Plots 01--05 (Radar, Residuals, Noise Response)
   * - ``notebook_12_final_audit/``
     - 5
     - Grand Operational Release Certification
     - Audit Figures 1--5 (Master Octagon, Waterfall)

Granular Technical Analysis Across Research Milestones
======================================================

Stages 01--04: Sensing, Graph Geometry & Temporal Hysteresis
------------------------------------------------------------

* **Stage 01 (Ingestion):** Ingests collocated Sentinel-1 SAR, Sentinel-2 MSI, Copernicus 30m DEM,
  and ERA5 weather across Kendrapara/Bhadrak (:math:`86.64^\circ\text{E} - 86.74^\circ\text{E}`,
  :math:`21.09^\circ\text{N} - 21.19^\circ\text{N}`). Evaluates radar penetration during optical cloud cover.
* **Stage 02 (Preprocessing):** Applies a :math:`7 \times 7` Enhanced Lee speckle filter and establishes
  deterministic scaling boundaries (:math:`\text{SAR}_{VV} \in [-18.52, -6.14]\ \text{dB}`).
* **Stage 03 (Spatial Graphs):** Implements an 8-nearest neighbor topographic graph. Demonstrates that
  severing graph edges increases embedding variance from :math:`0.0236` to :math:`0.0353` (:math:`\Delta_F = 4.155`).
* **Stage 04 (Temporal Dynamics):** Establishes ConvLSTM lookback horizon of :math:`L=5` as the Pareto
  optimum (:math:`\text{MSE} = 37.74`), avoiding short-horizon underfitting and long-horizon monsoon overfitting.

Stages 05--08: Physical Conservation, State Assimilation & Failure Recovery
---------------------------------------------------------------------------

* **Stage 05 (Physics Validation):** Solves the 1D mixed-form Richards equation with van Genuchten parameters
  for Loam soils. Reduces PDE residual loss to :math:`1.916 \times 10^{-7}`, achieving a **72.30%** error
  reduction relative to unconstrained neural baselines.
* **Stage 06 (State Estimation):** Deploys a 50-member Ensemble Kalman Filter estimating
  :math:`\mathbf{x} = [\theta_{\text{root}}, \rho_b, K_{\text{sat}}, \text{SOC}]^T`. EnKF assimilation
  contracts prediction RMSE from :math:`0.06535` to :math:`0.01466\ \text{m}^3/\text{m}^3` (**-77.57%**).
* **Stage 07 (Uncertainty Analysis):** Validates split-conformal prediction intervals. Confirms strong
  monotonic residual correlation (:math:`-0.9208`), with high-confidence patch MAE of :math:`0.0028\ \text{m}^3/\text{m}^3`.
* **Stage 08 (Robustness):** Benchmarks sensor dropout resilience. Under complete optical blackout (S2 missing),
  radar-physics coupling bounds RMSE to :math:`0.07046\ \text{m}^3/\text{m}^3`.

Stages 09--12: Hyperspectral Tradeoffs, Ablation Tiering & Final Audit
----------------------------------------------------------------------

* **Stage 09 (Hyperspectral):** Tests 200 science bands with 10 PCA orthogonal features. While achieving
  :math:`-89.67\%` RMSE improvement, its :math:`2.71\times` latency penalty directs its designation as
  Tier 3 on-demand rather than core backbone.
* **Stage 10 (Ablation Study):** Analyzes marginal utility across 8 configurations (Configs A--H).
  Freezes **Config G** (S1+S2+DEM+ERA5+ConvLSTM+PINN+EnKF) as the operational flight backbone (:math:`0.80\ \text{ms}`).
* **Stage 11 (Generalization):** Evaluates 5 out-of-distribution regimes. Certifies spatial holdout
  generalization gap at :math:`0.00129\ \text{m}^3/\text{m}^3` (well below :math:`0.0030` contract threshold).
* **Stage 12 (Final Audit):** Executes master system audit, verifying all 7 persistent storage artifacts
  under SHA-256 model lock and achieving sub-millisecond execution throughput (:math:`0.0116\ \text{ms/pixel}`).

Brutally Honest Disclosures & Research Limitations
==================================================

1. **Temporal Auto-Correlation Leakage in Prototyping:**
   Initial experiments in Stages 01--02 utilized chronological temporal splits, introducing minor
   generalization bias due to persistent soil moisture memory. Fully resolved in Stage 11 via LOCO
   spatial holdout partitions.
2. **1D Vertical Column Assumption in PINN:**
   Stage 05 formulates Richards equation strictly along the 1D vertical dimension :math:`z \in [0, 200\ \text{cm}]`.
   Lateral subsurface flow is approximated via 2D GCN topographic embeddings rather than a fully coupled 3D PDE.
3. **Finite Ensemble Size Approximations:**
   The 50-member EnKF requires covariance inflation (:math:`\lambda = 1.05`) to prevent filter inbreeding
   and covariance collapse over extended assimilation cycles.
4. **Synthetic vs. Real-World Cloud Persistence:**
   Dropout evaluation in Stage 08 utilized randomized synthetic masking. Extended monsoon periods with
   10+ consecutive days of overcast conditions require prolonged reliance on radar-only propagation.

Traceable Requirements Matrix
=============================

.. list-table:: Subsystem 05 Research Milestone Requirements
   :widths: 20 18 42 20
   :header-rows: 1

   * - Requirement ID
     - Stage
     - Specification Contract
     - Compliance Status
   * - **REQ-STOR-NBR-01**
     - Stage 01
     - STAC catalog spans Sentinel-1, Sentinel-2, DEM, and ERA5.
     - **PASSED**
   * - **REQ-STOR-NBR-02**
     - Stage 02
     - Lee filter suppresses speckle while preserving sharp edges.
     - **PASSED**
   * - **REQ-STOR-NBR-03**
     - Stage 03
     - GCN graph representation achieves lower variance than baseline.
     - **PASSED** (0.0236 vs 0.0353)
   * - **REQ-STOR-NBR-04**
     - Stage 04
     - ConvLSTM validation :math:`\text{MSE} \le 40.0` on optimal lookback.
     - **PASSED** (37.74)
   * - **REQ-STOR-NBR-05**
     - Stage 05
     - PINN Richards PDE residual error reduced by :math:`> 70\%`.
     - **PASSED** (72.30%)
   * - **REQ-STOR-NBR-06**
     - Stage 06
     - EnKF assimilation reduces root moisture error by :math:`> 70\%`.
     - **PASSED** (77.57%)
   * - **REQ-STOR-NBR-07**
     - Stage 07
     - Conformal calibration achieves decile correlation :math:`\le -0.85`.
     - **PASSED** (-0.9208)
   * - **REQ-STOR-NBR-08**
     - Stage 08
     - Autonomous self-healing recovery under dual optical/SAR loss.
     - **PASSED**
   * - **REQ-STOR-NBR-09**
     - Stage 09
     - HSI augmentation preserves zero-failure fallback to Config G.
     - **PASSED**
   * - **REQ-STOR-NBR-10**
     - Stage 10
     - Freezes Config G as optimal Pareto production backbone.
     - **PASSED**
   * - **REQ-STOR-NBR-11**
     - Stage 11
     - Spatial generalization gap bounded :math:`\Delta \le 0.0030\ \text{m}^3/\text{m}^3`.
     - **PASSED** (0.00129)
   * - **REQ-STOR-NBR-12**
     - Stage 12
     - 100% zero-defect release verified under master model lock.
     - **PASSED**
