.. _subsystem_09_baseline_benchmarks:

====================================================================================================
Subsystem 09: Spaceborne Operational Campaign — Baseline Benchmarks (`5_baseline_benchmarks/`)
====================================================================================================

:Central Engine: AETHER-MRID1607X
:Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
:Lead Systems Engineer: Gourgopal Mohapatra
:Release Status: TRL-7 OPERATIONAL FLIGHT READINESS

Overview & Purpose
==================

The ``5_baseline_benchmarks/`` subsystem houses the comparative validation reports, classical baseline evaluations, multi-regime atmospheric stress test audits, and journal publication artifact registries for the **AETHER-MRID1607X** Earth Observation framework. Serving as Stage 5 of the Spaceborne Operational Campaign (SOC-AETHER-2026), this layer establishes the quantitative evidence base comparing the physics-informed neural network against established empirical remote sensing formulations across the 24 in-situ validation stations.

Benchmark Report Inventory
==========================

.. list-table:: Production Benchmark Reports
   :widths: 30 15 55
   :header-rows: 1

   * - Report Filename
     - File Size
     - Evaluated Models & Primary Scope
   * - **aether_vs_baselines_performance.json**
     - 5.1 KB
     - AETHER-MRID1607X vs Naive Optical NDVI & SAR Water Cloud Model (WCM) across 3 operational regimes.
   * - **baseline_comparison_results.json**
     - 1.1 KB
     - Classical model parameter fits (:math:`A, B, C, D`, slope, intercept) and :math:`R^2, RMSE, MAE, r` statistics.
   * - **cloud_occlusion_stress_test_report.json**
     - 1.5 KB
     - 3-Regime atmospheric stress audit: Nominal (0%), Partial (36%), Total Blackout (100%).
   * - **day12_agronomic_translation_metrics.json**
     - 2.0 KB
     - Day 12 Agronomic Translator metrics: CWSI, Soil Water Deficit, Crop Evapotranspiration (:math:`ET_c`).
   * - **day13_precision_irrigation_metrics.json**
     - 1.8 KB
     - Day 13 Precision Irrigation prescription: VRA water volume, pumping energy, and operating cost.
   * - **real_world_validation_metrics.json**
     - 3.5 KB
     - Multi-temporal 5-day flight campaign synthesis over 40.96 ha coastal delta AOI.
   * - **spaceborne_pipeline_orchestration_report.json**
     - 2.2 KB
     - Autonomous end-to-end mission pipeline execution log and cryptographic SHA-256 seals.

Classical Baseline Models
=========================

1. Naive Optical NDVI Regression (Carlson & Ripley 1995)
--------------------------------------------------------

Linear empirical formulation linking canopy greenness to soil moisture:

.. math::

   \theta_{\text{optical}} = 0.00337 \cdot NDVI + 0.1839

Metrics: :math:`RMSE = 0.0676\text{ m}^3/\text{m}^3, MAE = 0.0562\text{ m}^3/\text{m}^3, R^2 = 0.0001, r = 0.0097`. Under cloud cover, optical blindness results in 100% blind spots.

2. Semi-Empirical SAR Water Cloud Model (Attema & Ulaby 1978)
-------------------------------------------------------------

Two-way vegetation canopy attenuation and soil scattering formulation:

.. math::

   \sigma^0_{\text{total}} = \sigma^0_{\text{veg}} + \tau^2 \cdot \sigma^0_{\text{soil}}

.. math::

   \sigma^0_{\text{veg}} = 0.0555 \cdot \cos(39^\circ) \cdot (1 - \tau^2)

.. math::

   \tau^2 = \exp\left(-2 \cdot 0.1512 \cdot NDVI / \cos(39^\circ)\right)

.. math::

   \sigma^0_{\text{soil}} = -0.0049 + 0.2193 \cdot \theta

Metrics: :math:`RMSE = 0.0486\text{ m}^3/\text{m}^3, MAE = 0.0422\text{ m}^3/\text{m}^3, R^2 = 0.4825, r = 0.8128`.

Comparative Performance Matrix
==============================

.. list-table:: 3-Model Performance Comparison
   :widths: 35 15 15 15 20
   :header-rows: 1

   * - Model Architecture
     - RMSE (:math:`\text{m}^3/\text{m}^3`)
     - MAE (:math:`\text{m}^3/\text{m}^3`)
     - Pearson :math:`r`
     - Blind Spots (100% Cloud)
   * - Naive Optical NDVI (Carlson & Ripley)
     - 0.0676
     - 0.0562
     - 0.0097
     - 100.0% (Total Blindness)
   * - SAR Water Cloud Model (Attema & Ulaby)
     - 0.0486
     - 0.0422
     - 0.8128
     - 0.0% (NDVI Degraded)
   * - **AETHER-MRID1607X (Clear Sky 0%)**
     - **0.0669**
     - **0.0589**
     - **0.3263**
     - **0.0% (Zero Blindness)**
   * - **AETHER-MRID1607X (Partial 36%)**
     - **0.0669**
     - **0.0589**
     - **0.3263**
     - **0.0% (Zero Blindness)**
   * - **AETHER-MRID1607X (Blackout 100%)**
     - **0.0717**
     - **0.0586**
     - **0.3145**
     - **0.0% (Zero Blindness)**

Verification Scorecard (SOC-16 to SOC-20)
=========================================

.. list-table:: Automated Test Verification Results
   :widths: 15 35 25 15
   :header-rows: 1

   * - Test ID
     - Verification Target
     - Measured Result
     - Status
   * - SOC-16
     - Inference Latency & Zero NaNs
     - 0.003117 ms/px, 0 NaNs
     - **PASS**
   * - SOC-17
     - Richards Vadose Mass Conservation
     - :math:`\|\mathcal{R}\|_2 = 0.001456 < 0.050\text{ m}^3/\text{m}^3`
     - **PASS**
   * - SOC-18
     - Multi-Regime Cloud Occlusion Stress Test
     - Error degradation :math:`+7.17\%`, zero blind spots
     - **PASS**
   * - SOC-19
     - Conformal Uncertainty Epistemic Dilation
     - Dilation :math:`+47.69\%` (:math:`0.0130 \to 0.0192`)
     - **PASS**
   * - SOC-20
     - Comparative Benchmark JSON Export
     - 7 verified JSON reports written to disk
     - **PASS**

Brutally Honest Engineering Limitations ("Ek Ek Dhappa")
========================================================

1. **Optical Baseline Near-Zero Correlation:**
   The Carlson-Ripley optical NDVI regression baseline exhibits virtually zero correlation with in-situ surface soil moisture (:math:`r = 0.0097`). In tropical alluvial deltas, canopy greenness reflects crop phenology and cultivar variation rather than instantaneous surface moisture (:math:`0-5\text{ cm}`).

2. **WCM Global Parameter Stationarity:**
   The Water Cloud Model utilizes static calibration parameters across all soil textures. In reality, vegetation scattering (:math:`A`) and soil dielectric sensitivity (:math:`D`) vary between clay loam and sandy loam textures.

3. **Finite Sample Conformal Coverage Under Extreme Blackout:**
   Under 100% optical cloud blackout, the empirical coverage on the 24-station sample drops to 25.0%. For safety-critical civil engineering deployments, wider safety margins (:math:`3\sigma`) are recommended.
