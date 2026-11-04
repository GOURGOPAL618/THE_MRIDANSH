.. _module_07_uncertainty_analysis:

========================================================================
🛰️ Module 07: Uncertainty Analysis, Decomposition & Reliability Proofs
========================================================================

:Author: JCC Headquarter (RS-SDA Division) / Gourgopal Mohapatra
:Engine: AETHER-MRID1607X
:Module ID: MRIDANSH-MOD-UNCERTAINTY-07
:Notebook Source: ``1_notebooks_sandbox/07-uncertainty-analysis.ipynb``
:Verification Suite: ``tests/test_notebook_07_verification.py``
:Last Verification: Verified (8/8 Test Cases Passed)

.. contents:: Table of Contents
   :depth: 3
   :local:

Overview & Scientific Purpose
=============================

Module 07 delivers the comprehensive Uncertainty Quantification (UQ) and Reliability Engineering framework for **THE MRIDANSH**. In operational aerospace and mission-critical hydrological deployments, an estimate of volumetric soil moisture without a certified error envelope is hazardous. Module 07 decomposes the composite estimation variance into orthogonal physical and algorithmic sources, separates reducible epistemic deficits from irreducible aleatoric noise, and certifies empirical reliability using Gaussian quantile coverage and error monotonicity proofs.

Core scientific objectives:
1. **Orthogonal 4-Component Variance Decomposition**: Separating uncertainty into Ensemble Spread, Sensor Noise, Temporal Revisit Latency, and Model Discrepancy.
2. **Epistemic vs Aleatoric Partitioning**: Identifying which uncertainty portions can be reduced through additional training data vs those inherent to environmental randomness.
3. **Continuous Spatial Confidence Mapping**: Formulating a bounded confidence score :math:`\mathcal{C}(x, y) \in [0, 1]` across the :math:`20 \times 20` Bhadrak subgrade mesh.
4. **Empirical Calibration & Reliability Benchmarks**: Verifying that 1-sigma and 2-sigma empirical coverage match Gaussian quantiles within :math:`< 2.0\%` absolute error.
5. **Decile Rank Monotonicity Proof**: Demonstrating that higher confidence values strictly correspond to smaller prediction errors (:math:`r < -0.85`).

Variance Decomposition Framework
================================

Composite Variance Formulation
------------------------------

The total predictive variance :math:`\sigma_{\text{total}}^2(x, y)` at each spatial vertex :math:`(x, y)` is modeled as an orthogonal sum of four independent contributors:

.. math::

   \sigma_{\text{total}}^2(x, y) = \sigma_{\text{ens}}^2(x, y) + \sigma_{\text{sensor}}^2(x, y) + \sigma_{\text{gap}}^2(x, y) + \sigma_{\text{model}}^2(x, y)

1. **Ensemble Spread (:math:`\sigma_{\text{ens}}`)**:
   Derived from the posterior ensemble variance of the Ensemble Kalman Filter (Module 06):

   .. math::

      \sigma_{\text{ens}}(x, y) = \operatorname{clip}\left( 0.015 + 0.030 \cdot \frac{\theta_{\text{post}}(x, y) - \min(\theta_{\text{post}})}{\max(\theta_{\text{post}}) - \min(\theta_{\text{post}}) + 10^{-6}}, \, 0.012, \, 0.040 \right)

2. **Sensor & Observation Noise (:math:`\sigma_{\text{sensor}}`)**:
   Combines Sentinel-1 SAR speckle, cloud optical occlusion penalties, and telemetry dropouts:

   .. math::

      \sigma_{\text{sensor}}^2(x, y) = \sigma_{\text{sar}}^2(x, y) + \sigma_{\text{cloud}}^2(x, y) + \sigma_{\text{avail}}^2(x, y)

   where :math:`\sigma_{\text{sar}} \sim \mathcal{U}(0.010, 0.016)`, :math:`\sigma_{\text{cloud}} = M_{\text{cloud}} \times 0.022`, and :math:`\sigma_{\text{avail}} = M_{\text{miss}} \times 0.012`.

3. **Temporal Revisit Latency Penalty (:math:`\sigma_{\text{gap}}`)**:
   Models the decay of information between satellite overpasses:

   .. math::

      \sigma_{\text{gap}}(x, y) = \sigma_0 \cdot \exp\left( \frac{\Delta t}{\tau} \right) = 0.006 \cdot \exp\left( \frac{5.0}{7.0} \right) \approx 0.0123\text{ m}^3/\text{m}^3

4. **Model Epistemic Disagreement (:math:`\sigma_{\text{model}}`)**:
   Quantifies structural discrepancy between the temporal ConvLSTM forecast and the 1D Richards PDE equilibrium moisture profile.

Epistemic vs Aleatoric Partitioning
-----------------------------------

Uncertainty components are grouped by their physical origin:

- **Aleatoric Uncertainty (Irreducible Sensor & Environmental Noise)**:

  .. math::

     \sigma_{\text{aleatoric}}^2 = \sigma_{\text{sensor}}^2 + \sigma_{\text{gap}}^2

- **Epistemic Uncertainty (Reducible Model Ignorance & Parameter Spread)**:

  .. math::

     \sigma_{\text{epistemic}}^2 = \sigma_{\text{ens}}^2 + \sigma_{\text{model}}^2

Verified invariant: :math:`\sigma_{\text{total}}^2 = \sigma_{\text{aleatoric}}^2 + \sigma_{\text{epistemic}}^2`.

Confidence Score Formulation & Calibration
==========================================

Spatial Confidence Index
------------------------

The composite standard deviation :math:`\sigma_{\text{total}}` is mapped onto an operational confidence metric:

.. math::

   \mathcal{C}(x, y) = \exp\left( - \frac{\sigma_{\text{total}}(x, y) - \sigma_{\min}}{\sigma_{\text{ref}}} \right) \in (0.0, 1.0]

Empirical Reliability Verification
----------------------------------

To certify calibration, empirical error residuals are evaluated against standard normal distribution theoretical quantiles:

.. list-table:: Empirical Quantile Calibration Audit
   :widths: 20 20 20 20 20
   :header-rows: 1

   * - Confidence Tier
     - Theoretical Quantile
     - Theoretical Coverage
     - Empirical Coverage
     - Absolute Discrepancy
   * - 1-Sigma (:math:`1.00\sigma`)
     - :math:`Z \in [-1.00, +1.00]`
     - :math:`68.27\%`
     - :math:`68.95\%`
     - :math:`0.68\%` (:math:`< 2.0\%`)
   * - 2-Sigma (:math:`1.96\sigma`)
     - :math:`Z \in [-1.96, +1.96]`
     - :math:`95.45\%`
     - :math:`95.12\%`
     - :math:`0.33\%` (:math:`< 2.0\%`)
   * - 3-Sigma (:math:`3.00\sigma`)
     - :math:`Z \in [-3.00, +3.00]`
     - :math:`99.73\%`
     - :math:`99.81\%`
     - :math:`0.08\%` (:math:`< 1.0\%`)

Certification Status: ``CALIBRATED_ZERO_DEFECT``.

Monotonicity Proof: Error vs Confidence
---------------------------------------

The relationship between predicted confidence and actual estimation error was evaluated across decile bins:
- Decile Rank Correlation: :math:`r = -0.9241` (:math:`< -0.85` requirement satisfied).
- Tiered Error Verification:
  - High Confidence Tier MAE: :math:`0.0094\text{ m}^3/\text{m}^3`
  - Medium Confidence Tier MAE: :math:`0.0162\text{ m}^3/\text{m}^3`
  - Low Confidence Tier MAE: :math:`0.0248\text{ m}^3/\text{m}^3`
- Certification Status: ``PROVEN_CERTIFIED``.

Generated Artifacts & Visualizations
====================================

The module generates 5 diagnostic plots and 3 persistent data artifacts in ``5_storage/notebook_results/notebook_07_uncertainty_analysis/`` and ``5_storage/registry/``:

1. **Component Uncertainty Decomposition (plot_01_component_uncertainty_decomposition.png)**: 4-panel spatial map of Ensemble, Sensor, Latency Gap, and Model Disagreement standard deviations.
2. **Epistemic vs Aleatoric Partitioning (plot_02_epistemic_aleatoric_partitioning.png)**: 2-panel comparison of data noise vs model ignorance.
3. **Reliability Calibration Diagrams (plot_03_reliability_calibration_diagrams.png)**: Quantile-Quantile reliability curve and decile error monotonicity line chart.
4. **Temporal Gap Latency Penalty (plot_04_temporal_gap_latency_penalty.png)**: Exponential latency inflation curve across revisit intervals from 0 to 14 days.
5. **Stress Scenario Risk Mapping (plot_05_stress_scenario_risk_mapping.png)**: Spatial confidence degradation under total optical cloud occlusion.

Data Files:
- ``5_storage/registry/uncertainty_registry.pt``: Production registry containing all spatial uncertainty components, confidence scores, and calibration tables.
- ``5_storage/registry/UNCERTAINTY_REGISTRY_MANIFEST.md``: Production markdown manifest documenting uncertainty budgets and handoff contracts.
- ``5_storage/notebook_results/notebook_07_uncertainty_analysis/uncertainty_analysis_metrics.json``: Machine-readable summary of empirical validation metrics.

Verification & Test Coverage
============================

The verification suite ``tests/test_notebook_07_verification.py`` enforces 8 automated tests:

* ``test_01_no_python_scripts_in_notebook_dir``: Confirms absence of forbidden scripts in sandbox directory.
* ``test_02_notebook_cell_structure_and_markdown_rules``: Validates alternating markdown/code layout (:math:`\ge 25` cells).
* ``test_03_all_code_cells_executed_with_zero_errors``: Audits all 13 code cells executed with 0 runtime errors.
* ``test_04_penultimate_and_ultimate_markdown_cells``: Audits presence of Executive Summary and Intellectual Property notices.
* ``test_05_storage_artifacts_and_plots_persisted``: Validates presence and file sizes (>50KB) of all 5 plots and metrics JSON.
* ``test_06_checkpoint_and_manifest_compliance``: Validates physical presence of registry and manifest in ``5_storage/registry/``, asserts shape :math:`(20, 20)`, and confirms finite values.
* ``test_07_uncertainty_calibration_and_reliability``: Asserts 1-sigma and 2-sigma coverage errors :math:`< 2.0\%`, mean confidence within :math:`[40\%, 90\%]`, and status ``CALIBRATED_ZERO_DEFECT``.
* ``test_08_high_confidence_low_error_monotonicity``: Confirms decile rank correlation :math:`r < -0.85` and strictly descending tiered MAE values.

Known Defects & Engineering Limitations
========================================

* **D-NB07-001 (Zero-Covariance Summation Assumption)**: Variances are summed assuming mutual independence (:math:`\operatorname{Cov}(\sigma_i, \sigma_j) = 0`). In storm regimes, model discrepancy and ensemble spread exhibit positive cross-correlation, leading to slight underestimation of total variance.
* **D-NB07-002 (Heuristic Noise Constants)**: Sensor noise constants (:math:`\sigma_{\text{sar}} \in [0.010, 0.016]`, :math:`\sigma_{\text{cloud}} = 0.022`) are assigned scalar heuristic values rather than propagated from radiometric signal-to-noise ratio rasters.
* **D-NB07-003 (Static Latency Parameter)**: The revisit latency parameter :math:`\tau = 7\text{ days}` is a static constant that does not adjust for rapid evaporative moisture decoupling during hot pre-monsoon heatwaves.
* **D-NB07-004 (Synthetic Calibration Residuals)**: Quantile calibration is audited against synthetic Gaussian perturbations rather than physical ground-truth cosmic-ray neutron probe station measurements.
