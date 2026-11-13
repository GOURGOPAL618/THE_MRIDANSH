.. _subsystem_11_figures:

====================================================================================================
Subsystem 11: Simulation Test Campaign — Figures Specification (`11_simulation_test_campaign/figures/`)
====================================================================================================

:Central Engine: AETHER-MRID1607X
:Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
:Lead Systems Architect: Gourgopal Mohapatra
:Release Status: TRL-7 OPERATIONAL FLIGHT READINESS

Overview & Purpose
==================

The ``11_simulation_test_campaign/figures/`` subsystem archives the publication-grade scientific graphics, probability distributions, state-space uncertainty confidence ellipsoids, and hydrodynamic trajectory envelopes generated from the 1,000-trial Planetary Monte Carlo Stress Campaign (``PMC-1000-AETHER-MRID1607X``).

All figures are compiled in dual 600 DPI Adobe PDF (vector) and high-resolution PNG formats.

Figure Catalog & Scientific Evidence
====================================

.. list-table:: Scientific Figure Catalog
   :widths: 20 25 55
   :header-rows: 1

   * - Figure ID
     - Filename
     - Scientific Description & Invariant Validated
   * - **Figure 1**
     - ``figure_1_enkf_covariance_stability``
     - EnKF covariance confidence ellipsoids and empirical CDF of condition number :math:`\kappa(\mathbf{P}) \le 1709.03 \ll 10^6` (safety margin :math:`585.1\times`).
   * - **Figure 2**
     - ``figure_2_vadose_trajectory_fancharts``
     - Vadose zone moisture fan charts: Q1 drought monotonic desiccation vs Q2 deluge saturation ceiling :math:`\theta_{\text{sat}} = 0.450`.
   * - **Figure 3**
     - ``figure_3_terramechanics_disaster_envelopes``
     - Terramechanic disaster envelopes: Eurocode 7 slope stability FoS vs Bekker wheel sinkage under 45 kN tractor loads.

Brutally Honest Engineering Limitations ("Ek Ek Dhappa")
========================================================

1. **2D Ellipsoid Projection Simplification:**
   State uncertainty is depicted on a 2D plane (:math:`\theta_{\text{skin}}` vs :math:`\theta_{\text{root}}`), omitting higher-order cross-covariances with matric suction head for visual clarity.

2. **Headless Static Rendering:**
   Figures are compiled via non-interactive Matplotlib ``Agg`` backends. Dynamic exploration requires loading the raw ``.npy`` trajectory files.
