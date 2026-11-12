.. _subsystem_05_registry:

========================================================================================
Subsystem 05: Uncertainty Quantification Registry Specification
========================================================================================

:Engine: AETHER-MRID1607X
:Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
:Lead Architect: Gourgopal Mohapatra
:Status: FROZEN_OPERATIONAL_RELEASE_v1.0

Overview and Subsystem Mandate
==============================

The ``5_storage/registry/`` repository serves as the centralized empirical calibration repository
and uncertainty quantification vault for the **AETHER-MRID1607X** earth observation platform.
Formulated during Stage 07 (``1_notebooks_sandbox/07-uncertainty-analysis.ipynb``), this subsystem
archives the parameters governing orthogonal 4-component variance decomposition, empirical Gaussian
coverage calibration tables, and automated fail-soft triggers.

Primary objectives:

1. **Distribution-Free Uncertainty Bounds:** Equip downstream agronomy, civil geotechnics, and
   terramechanics translators with mathematically certified confidence intervals.
2. **Orthogonal Variance Partitioning:** Explicitly separate aleatoric data errors (SAR speckle, cloud
   obscuration) from epistemic model deficits (ensemble spread, temporal latency gap).
3. **Rigorous Empirical Calibration:** Validate that nominal :math:`1\sigma, 2\sigma, 3\sigma`
   prediction intervals match real-world empirical error coverage within strict tolerances (:math:`< 2.0\%`).

Registry Artifact Inventory & Signatures
========================================

.. list-table:: Registry Physical File Inventory
   :widths: 28 10 38 24
   :header-rows: 1

   * - Filename
     - Size (Bytes)
     - SHA-256 Hash
     - Subsystem Role
   * - ``uncertainty_registry.pt``
     - 40,379
     - ``452c9da84a61d1d136e17ef47ebe2159b15a246c81b99aa53dcd0ad1e2efaeef``
     - Binary spatial uncertainty tensors & calibration dictionaries.
   * - ``UNCERTAINTY_REGISTRY_MANIFEST.md``
     - 1,661
     - ``1ff98eb62507850257e8020a59124403328eb9ae8e3c153bca51ef4075191ecb``
     - Human-readable specification manifest and reliability proofs.

Mathematical Formulation & Variance Budget
==========================================

The platform employs an **Orthogonal 4-Component Variance Decomposition Model**:

.. math::

   \sigma_{\text{total}} = \sqrt{\sigma_{\text{ens}}^2 + \sigma_{\text{sensor}}^2 + \sigma_{\text{gap}}^2 + \sigma_{\text{model}}^2}

Component Breakdown:

.. list-table:: Uncertainty Variance Budget
   :widths: 26 26 18 16 14
   :header-rows: 1

   * - Component
     - Physical Origin
     - Classification
     - Mean (m³/m³)
     - Variance Share
   * - **Ensemble Spread** (:math:`\sigma_{\text{ens}}`)
     - 50-member EnKF state dispersion
     - Epistemic / State
     - **0.0310**
     - **51.97%**
   * - **SAR Speckle** (:math:`\sigma_{\text{sar}}`)
     - C-band radar speckle
     - Aleatoric / Sensor
     - 0.0130
     - 9.14%
   * - **Cloud Noise** (:math:`\sigma_{\text{cloud}}`)
     - Optical reflectance contamination
     - Aleatoric / Sensor
     - 0.0100
     - 5.41%
   * - **Net Sensor Noise** (:math:`\sigma_{\text{sensor}}`)
     - :math:`\sqrt{\sigma_{\text{sar}}^2 + \sigma_{\text{cloud}}^2}`
     - Aleatoric / Combined
     - **0.0187**
     - **18.88%**
   * - **Temporal Gap** (:math:`\sigma_{\text{gap}}`)
     - Revisit latency drying drift (:math:`0 - 120\text{ h}`)
     - Epistemic / Latency
     - **0.0123**
     - **8.18%**
   * - **Model Disagreement** (:math:`\sigma_{\text{model}}`)
     - ConvLSTM vs. PINN divergence
     - Epistemic / Model
     - **0.0179**
     - **17.33%**
   * - **Composite Total** (:math:`\sigma_{\text{total}}`)
     - Root-sum-squares combination
     - Total Uncertainty
     - **0.0430**
     - **100.00%**

Confidence Score Mapping
------------------------

Operational confidence index :math:`\mathcal{C} \in [0, 100\%]` is derived via inverse linear scaling:

.. math::

   \mathcal{C} = 100 \times \left(1 - \frac{\sigma_{\text{total}} - \sigma_{\min}}{\sigma_{\max} - \sigma_{\min}}\right)

* Mean Confidence: **52.63%** (:math:`\sigma_{\min} = 0.0302\ \text{m}^3/\text{m}^3`, :math:`\sigma_{\max} = 0.0559\ \text{m}^3/\text{m}^3`).

Empirical Reliability & Calibration Proofs
==========================================

Coverage Calibration
--------------------

.. list-table:: Empirical Reliability Verification
   :widths: 25 25 25 25
   :header-rows: 1

   * - Confidence Interval
     - Theoretical Nominal
     - Empirical Observed
     - Discrepancy Error
   * - :math:`1\sigma` Interval (:math:`\pm 1.00\sigma`)
     - 68.27%
     - **67.32%**
     - **0.95%**
   * - :math:`2\sigma` Interval (:math:`\pm 2.00\sigma`)
     - 95.45%
     - **95.32%**
     - **0.13%**
   * - :math:`3\sigma` Interval (:math:`\pm 3.00\sigma`)
     - 99.73%
     - **99.76%**
     - **0.03%**

Error Monotonicity Across Confidence Tiers
-----------------------------------------

* **Decile Rank Correlation:** :math:`r = -0.9208` (Demonstrates strict inverse relationship with error).
* High Confidence Tier MAE: :math:`0.0297\ \text{m}^3/\text{m}^3`.
* Medium Confidence Tier MAE: :math:`0.0351\ \text{m}^3/\text{m}^3`.
* Low Confidence Tier MAE: :math:`0.0497\ \text{m}^3/\text{m}^3`.

Pre-Computed Stress Outage Benchmarks
------------------------------------

* **Cloud Outage:** :math:`\sigma` rises to :math:`0.0607\ \text{m}^3/\text{m}^3` (:math:`\mathcal{C} = 40.32\%`).
* **Sensor Blackout:** :math:`\sigma` rises to :math:`0.0888\ \text{m}^3/\text{m}^3` (:math:`\mathcal{C} = 26.41\%`, triggers fail-soft mode).

Brutally Honest Disclosures & Caveats
=====================================

1. **PyTorch 2.6 WeightsUnpickler Compatibility:**
   ``uncertainty_registry.pt`` embeds NumPy array primitives. Standard loading with
   ``weights_only=True`` will raise an unpickler security error. Automated ingestion routines
   must configure ``weights_only=False``.
2. **Zero-Covariance Orthogonality Simplification:**
   The composite formula treats sensor noise and model disagreement as strictly independent.
   Under extreme meteorological overcast, sensor degradation and hydrological model divergence
   exhibit positive cross-covariance, causing slight variance underestimation (:math:`3 - 5\%`).
3. **Spatial Benchmark Resolution Scaling:**
   Raw arrays in ``uncertainty_registry.pt`` are stored on a :math:`20 \times 20` test grid and are
   interpolated to :math:`64 \times 64` during production flight pipeline execution.
4. **Physical Boundary Interval Clamping:**
   Gaussian :math:`\pm 2\sigma` intervals can mathematically project outside physically admissible
   limits :math:`[\theta_r, \theta_s]`. Downstream modules must clamp intervals to soil boundaries.

Traceable Requirements Matrix
=============================

.. list-table:: Subsystem 05 Uncertainty Registry Requirements
   :widths: 20 20 40 20
   :header-rows: 1

   * - Requirement ID
     - Method
     - Specification Bound
     - Compliance Status
   * - **REQ-STOR-REG-01**
     - Cryptography
     - Must match SHA-256 signature in master audit checkpoint.
     - **PASSED**
   * - **REQ-STOR-REG-02**
     - Statistical
     - :math:`1\sigma` empirical coverage discrepancy :math:`< 2.0\%`.
     - **PASSED** (0.95%)
   * - **REQ-STOR-REG-03**
     - Statistical
     - :math:`2\sigma` empirical coverage discrepancy :math:`< 1.0\%`.
     - **PASSED** (0.13%)
   * - **REQ-STOR-REG-04**
     - Statistical
     - :math:`3\sigma` empirical coverage discrepancy :math:`< 0.5\%`.
     - **PASSED** (0.03%)
   * - **REQ-STOR-REG-05**
     - Correlation
     - Decile rank correlation between confidence and error :math:`\le -0.85`.
     - **PASSED** (-0.9208)
   * - **REQ-STOR-REG-06**
     - Monotonicity
     - Strict ordering :math:`\text{MAE}_{\text{high}} < \text{MAE}_{\text{med}} < \text{MAE}_{\text{low}}`.
     - **PASSED**
   * - **REQ-STOR-REG-07**
     - Stress Audit
     - Blackout stress scenario drops confidence below :math:`30\%`.
     - **PASSED** (26.41%)
   * - **REQ-STOR-REG-08**
     - Parity
     - Manifest metrics strictly match binary serialized data.
     - **PASSED**
