.. _module_11_generalization:

========================================================================
🛰️ Module 11: Multi-Regime Generalization & Extreme Stress Testing
========================================================================

:Author: JCC Headquarter (RS-SDA Division) / Gourgopal Mohapatra
:Engine: AETHER-MRID1607X
:Module ID: MRIDANSH-MOD-GEN-11
:Notebook Source: ``1_notebooks_sandbox/11-generalization-baseline-evaluation.ipynb``
:Verification Suite: ``tests/test_notebook_11_verification.py``
:Last Verification: Verified (8/8 Test Cases Passed)

.. contents:: Table of Contents
   :depth: 3
   :local:

Overview & Scientific Purpose
=============================

Module 11 provides the out-of-distribution (OOD) operational certification for **THE MRIDANSH**. In operational aerospace deployments, estimating soil states under benign, identically distributed (IID) conditions is insufficient. Systems must maintain bounded errors when deployed across unseen catchments, under extreme weather events, or in high-noise environments.

This module subjects the unified multi-modal neural physics architecture (AETHER-MRID1607X) to five stress-testing regimes:
1. **Regime 1 (IID Reference)**: Nominal in-domain Bhadrak catchment baseline.
2. **Regime 2 (Spatial Holdout)**: Contiguous unseen catchment with completely disjoint coordinates.
3. **Regime 3 (Topographic Extremes)**: Rugged high-relief terrain (:math:`\theta_{\text{slope}} > 25^\circ`, high elevation).
4. **Regime 4 (Temporal Climate Shift)**: Extreme monsoonal deluge and multi-week drought drydown.
5. **Regime 5 (Sensor Noise Stress)**: Heavy synthetic aperture radar speckle and optical cloud occlusion.

The module computes the spatial generalization gap, executes Leave-One-Component-Out (LOCO) sensitivity ablations, and performs two-sample Kolmogorov-Smirnov (KS) statistical drift testing.

Multi-Regime Experimental Matrix & Empirical Metrics
====================================================

The empirical performance across the 5 regimes is summarized below:

.. list-table:: Multi-Regime Generalization Scorecard
   :widths: 25 25 25 25
   :header-rows: 1

   * - Generalization Regime
     - Unconstrained Naive RMSE
     - MRIDANSH System RMSE
     - Error Reduction Rate
   * - **Regime 1: IID Reference**
     - :math:`0.0230\text{ m}^3/\text{m}^3`
     - :math:`0.00447\text{ m}^3/\text{m}^3`
     - :math:`80.58\%`
   * - **Regime 2: Spatial Holdout**
     - :math:`0.0211\text{ m}^3/\text{m}^3`
     - :math:`0.00448\text{ m}^3/\text{m}^3`
     - :math:`78.79\%`
   * - **Regime 3: Topographic Extremes**
     - :math:`0.0245\text{ m}^3/\text{m}^3`
     - :math:`0.00628\text{ m}^3/\text{m}^3`
     - :math:`74.34\%`
   * - **Regime 4: Climate Shift**
     - :math:`0.0281\text{ m}^3/\text{m}^3`
     - :math:`0.00770\text{ m}^3/\text{m}^3`
     - :math:`72.59\%`
   * - **Regime 5: Sensor Noise Stress**
     - :math:`0.0468\text{ m}^3/\text{m}^3`
     - :math:`0.00455\text{ m}^3/\text{m}^3`
     - :math:`90.27\%`

Spatial Generalization Gap Contract
-----------------------------------

The spatial generalization gap :math:`\Delta_{\text{spatial}}` is defined as:

.. math::

   \Delta_{\text{spatial}} = \text{RMSE}_{\text{Regime 2}} - \text{RMSE}_{\text{Regime 1}}

Verified contract results:
- :math:`\Delta_{\text{spatial}} = 0.00448 - 0.00447 = 0.00001\text{ m}^3/\text{m}^3 \le 0.0030\text{ m}^3/\text{m}^3` (Contract met).
- Spatial holdout :math:`R^2 = 0.924` (:math:`> 0.90` requirement met).

Leave-One-Component-Out (LOCO) Sensitivity
==========================================

To evaluate component criticality under out-of-distribution stress, individual components were removed one at a time:
- **Drop EnKF Filter**: Triggers severe error accumulation during non-stationary rainfall surges (:math:`\Delta\text{RMSE} = +42.1\%`).
- **Drop Physics PINN**: Results in unphysical capillary head gradients and negative volumetric moisture values (:math:`\Delta\text{RMSE} = +35.8\%`).
- **Drop Sentinel-1 SAR**: Causes complete loss of predictive capability during persistent overcast monsoon conditions (:math:`\Delta\text{RMSE} = +78.4\%`).

Conclusion: LOCO sensitivity proves that Sentinel-1 SAR, Richards PINN, and the EnKF filter form the indispensable **Tier 1 core** of the system.

Statistical Drift Detection & Uncertainty Calibration
=====================================================

Two-Sample Kolmogorov-Smirnov Test
----------------------------------

To verify autonomous detection of distribution shift, the two-sample Kolmogorov-Smirnov statistic was evaluated between reference and stressed residual distributions:

.. math::

   D = \sup_x |F_{\text{ref}}(x) - F_{\text{shift}}(x)|

The test yielded :math:`p < 0.001`, confirming statistically significant shift detection. Under shift conditions, predictive uncertainty envelopes expand dynamically, ensuring the model never issues overconfident predictions when operating out-of-domain.

Generated Artifacts & Visualizations
====================================

The module generates 5 high-resolution diagnostic plots and 2 persistent checkpoint files in ``5_storage/notebook_results/notebook_11_generalization/`` and ``5_storage/checkpoints/``:

1. **Multi-Regime Error Radar (plot_01_multi_regime_generalization_error_radar.png)**: Spider chart illustrating error metrics across all 5 evaluation regimes.
2. **Spatial Holdout Residuals (plot_02_spatial_holdout_residual_distribution.png)**: Residual error distributions comparing in-domain training vs unseen geographical holdouts.
3. **Topographic Elevation vs Moisture Stability (plot_03_topographic_elevation_vs_moisture_stability.png)**: Contour and scatter plots mapping model stability across steep slopes.
4. **Temporal Monsoon/Drought Stress Response (plot_04_temporal_monsoon_drought_stress_response.png)**: Dynamic tracking under simulated monsoonal flooding and arid drydowns.
5. **Sensor Noise Robustness Curve (plot_05_sensor_noise_degradation_robustness_curve.png)**: Degradation response curve as observation noise variance escalates to 100%.

Data Files:
- ``5_storage/checkpoints/generalization_evaluation_checkpoint.pt``: Serialized checkpoint containing regime metrics, LOCO scores, and operational flags.
- ``5_storage/checkpoints/GENERALIZATION_EVALUATION_MANIFEST.md``: Production markdown manifest certifying generalization bounds.

Verification & Test Coverage
============================

The verification suite ``tests/test_notebook_11_verification.py`` enforces 8 automated tests:

* ``test_01_notebook_11_structure_and_interleaving``: Confirms exactly 36 cells with strictly alternating markdown/code, executive summary, and IP notice.
* ``test_02_spatial_block_holdout_zero_data_leakage``: Verifies 5 generalization regimes partitioned with isolated holdouts.
* ``test_03_multi_regime_generalization_evaluation``: Audits all 5 regimes maintaining :math:`>70\%` error reduction vs naive baseline.
* ``test_04_spatial_generalization_gap_tolerance``: Asserts spatial generalization gap :math:`\le 0.0030\text{ m}^3/\text{m}^3` and :math:`R^2 > 0.90`.
* ``test_05_loco_ablation_tier1_anchors``: Confirms LOCO ablation proves Tier 1 anchors (SAR, PINN, EnKF) are essential.
* ``test_06_uncertainty_calibration_and_ks_shift``: Audits uncertainty expansion and two-sample KS test shift significance.
* ``test_07_embedded_and_standalone_visual_plots``: Audits physical presence of all 5 plots on disk (>50KB) and confirms base64 image embedding.
* ``test_08_checkpoint_and_manifest_certification``: Confirms presence of certified checkpoint and manifest in ``5_storage/checkpoints/``.

Known Defects & Engineering Limitations
========================================

* **D-NB11-001 (Synthetic Spatial Holdout Coordinates)**: The held-out catchment is synthesized via coordinate shifts rather than sourced from genuine field telemetry in a distinct geological basin.
* **D-NB11-002 (Simulated Temporal Climate Extremes)**: Monsoon deluges and droughts are generated via mathematical scaling multipliers rather than multi-decadal historical climate reanalysis.
* **D-NB11-003 (Synthesized High-Relief Topography)**: Steep slopes are generated synthetically without modeling physical radar layover/foreshortening or mountain shadow effects.
* **D-NB11-004 (Residual-Only KS Statistical Drift)**: The KS drift test evaluates scalar residuals rather than monitoring high-dimensional latent space representations for covariate shift.
