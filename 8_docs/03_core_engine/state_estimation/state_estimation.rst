.. _core_engine_state_estimation:

========================================================================================
Core Engine State Estimation, EnKF & Conformal Uncertainty
========================================================================================

:Document ID: DOC-MRID-03-EST-001
:Module: ``3_core_engine/state_estimation/``
:Author: Gourgopal Mohapatra
:Status: RELEASED / PRODUCTION AUDITED
:Date: 2026-11-05

.. contents:: Table of Contents
   :depth: 2
   :local:

Subsystem Overview
==================
The ``3_core_engine/state_estimation`` package delivers distribution-free conformal uncertainty intervals and ensemble data assimilation. It decomposes predictive uncertainty into orthogonal epistemic and aleatoric variances and implements a Stochastic Ensemble Kalman Filter (EnKF) updating a 4-parameter pedological state vector.

Architectural Disclosures & Code Audit
======================================

.. warning::
   **ENGINEERING AUDIT DISCLOSURES**:

   1. **Matrix Singularity in Unregularized Inversion (D-ENG-EST-001)**:
      ``enkf_filter.py`` uses standard ``np.linalg.inv`` to compute the innovation covariance inverse :math:`(H P_f H^T + R)^{-1}`. If observations are spatially redundant or sensors have zero noise, the matrix becomes singular, triggering an unhandled ``LinAlgError``. The production orchestrator must route calls through ``enkf_assimilator.py`` which enforces Tikhonov ridge conditioning (:math:`\lambda = 10^{-5}`).
   2. **Ensemble Memory Consumption (D-ENG-EST-002)**:
      Maintaining :math:`N=50` spatial ensemble members across large raster grids (:math:`512 \times 512`) consumes significant memory, requiring proactive deallocation of intermediate forecast perturbations.
   3. **Conformal Exchangeability Caveat (D-ENG-EST-003)**:
      The theoretical finite-sample coverage guarantee :math:`\ge 1 - \alpha` assumes exchangeable non-conformity scores. Abrupt monsoon onset events temporarily introduce temporal distribution shifts.
   4. **Linear Kalman Assumption on Non-Linear Hydraulic Conductivity (D-ENG-EST-004)**:
      Assimilating observations directly into :math:`K_{\text{sat}}` assumes linear error propagation, whereas hydraulic conductivity is exponentially distributed. Explicit lower-bound clamping is required to prevent negative conductivities.

Statistical & Scientific Formulations
=====================================

Epistemic & Aleatoric Variance Partitioning
-------------------------------------------
Total predictive variance is partitioned into decoupled sources:

.. math::

   \sigma_{\text{total}}^2 = \sigma_{\text{aleatoric}}^2 + \sigma_{\text{epistemic}}^2

.. math::

   \sigma_{\text{aleatoric}}^2 = \sigma_{\text{ensemble}}^2 + \sigma_{\text{sensor}}^2 \quad (\text{SAR speckle} + \text{cloud fraction})

.. math::

   \sigma_{\text{epistemic}}^2 = \sigma_{\text{backbone}}^2 + \sigma_{\text{gap}}^2

Split Conformal Prediction Intervals
------------------------------------
Calibrates valid finite-sample prediction intervals without distributional assumptions:

1. Non-conformity score:

   .. math::

      s_i = \frac{|y_i - \hat{y}_i|}{\sigma_{\text{total}, i}}

2. Finite-sample quantile at significance level :math:`\alpha`:

   .. math::

      \hat{q} = \text{Quantile}\left(\{s_1, \dots, s_n\}, \frac{\lceil(n+1)(1-\alpha)\rceil}{n}\right)

3. Valid prediction band:

   .. math::

      \mathcal{C}(x) = [\hat{y}(x) - \hat{q} \cdot \sigma_{\text{total}}(x), \; \hat{y}(x) + \hat{q} \cdot \sigma_{\text{total}}(x)]

Production Coverage Benchmark:

.. math::

   \text{Coverage} \ge 88.0\% \quad (\text{at } 90\% \text{ Nominal Confidence}, \text{Achieved: } 90.5\%)

Stochastic Ensemble Kalman Filter (EnKF)
----------------------------------------
Tracks the 4-dimensional pedological state vector:

.. math::

   \mathbf{x} = [\theta_{\text{root}}, \text{bulk\_density}, K_{\text{sat}}, \text{SOC}]^T \in \mathbb{R}^4

Perturbed observations and Tikhonov-regularized Kalman gain:

.. math::

   \mathbf{y}_j = \mathbf{y} + \mathbf{v}_j, \quad \mathbf{v}_j \sim \mathcal{N}(0, R)

.. math::

   K = P_f H^T (H P_f H^T + R + \lambda I)^{-1}

Ensemble member state update:

.. math::

   \mathbf{x}_j^a = \mathbf{x}_j^f + K (\mathbf{y}_j - H \mathbf{x}_j^f)

Production Variance Squashing Benchmark:

.. math::

   \frac{\text{Tr}(P_a) - \text{Tr}(P_f)}{\text{Tr}(P_f)} \le -60.0\% \quad (\text{Achieved: } -69.5\%)

Verification Results
====================
Validated via unit tests in ``tests/test_conformal_uncertainty.py``, ``tests/test_enkf_assimilator.py``, ``tests/test_enkf_filter_d04.py``, and ``tests/test_physics_enkf_freeze.py``:
- Verified variance decomposition into aleatoric and epistemic components.
- Verified conformal empirical coverage exceeds 88.0% threshold.
- Verified EnKF variance reduction exceeds -60.0% benchmark.
- Verified numerical stability under Tikhonov regularization.

Defect & Technical Debt Register
================================
.. list-table::
   :widths: 15 45 15 25
   :header-rows: 1

   * - Defect ID
     - Description
     - Severity
     - Remediation Plan
   * - D-ENG-EST-001
     - Direct matrix inversion in ``enkf_filter.py`` prone to singularity.
     - HIGH
     - Replace with pseudo-inverse or mandatory Tikhonov ridge term.
   * - D-ENG-EST-002
     - Large memory footprint of 50-member Monte Carlo ensemble rasters.
     - MEDIUM
     - Introduce spatial block-streaming during ensemble covariance updates.
   * - D-ENG-EST-003
     - Temporary exchangeability degradation during sudden weather shifts.
     - LOW
     - Implement adaptive rolling-window conformal calibration.
   * - D-ENG-EST-004
     - Linear updates applied to exponential hydraulic parameters.
     - LOW
     - Log-transform conductivity prior to Kalman gain multiplication.
