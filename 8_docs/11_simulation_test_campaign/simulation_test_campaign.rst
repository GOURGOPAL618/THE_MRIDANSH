.. _subsystem_11_simulation_test_campaign:

====================================================================================================
Subsystem 11: Simulation Test Campaign — 1,000-Trial Planetary Monte Carlo (`11_simulation_test_campaign/`)
====================================================================================================

:Central Engine: AETHER-MRID1607X
:Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
:Lead Systems Architect: Gourgopal Mohapatra
:Release Status: TRL-7 OPERATIONAL FLIGHT READINESS

Overview & Purpose
==================

The ``11_simulation_test_campaign/`` subsystem defines the high-performance in-memory vectorized Monte Carlo stress-testing harness, cross-domain agro-civil simulation pipeline, and flight-invariant qualification framework for the **AETHER-MRID1607X** Earth Observation platform. Executed on **Mission Day 18 (11 Nov 2026)**, this campaign subjects the central physics core and domain translators to extreme planetary boundary regimes across 1,000 continuous trials.

All 1,000 trials achieved a **100.0% Invariant Qualification Rate** with zero numerical singularities, zero NaNs/Infs, and zero Richards PDE mass conservation drift.

4-Quadrant Planetary Stress Architecture
=========================================

.. list-table:: 1,000-Trial Quadrant Partition Matrix
   :widths: 20 25 35 20
   :header-rows: 1

   * - Quadrant & Seed
     - Target Stress Regime
     - Physical Forcing Boundary
     - Compliance Rate
   * - **Q1 (Seed 16071)**
     - Hyper-Arid Sustained Drought
     - 14-day desiccation, :math:`P = 0.0\text{ mm/d}, ET_0 = 8-14\text{ mm/d}`
     - **250 / 250 PASS (100%)**
   * - **Q2 (Seed 16072)**
     - Monsoon Deluge & Landslides
     - 7-day deluge, :math:`P = 50-150\text{ mm/d}`, Eurocode 7 Slope FoS < 1.0
     - **250 / 250 PASS (100%)**
   * - **Q3 (Seed 16073)**
     - Sensor Noise & Cloud Dropout
     - 80-100% cloud cover, SAR speckle :math:`\Delta\sigma^0 \in [-4.5, +4.5]\text{ dB}`
     - **250 / 250 PASS (100%)**
   * - **Q4 (Seed 16074)**
     - Coastal Mud Liquefaction
     - 45 kN tractor axle loading, Bekker sinkage :math:`z_{\text{rut}} \le 35\text{ cm}`
     - **250 / 250 PASS (100%)**

Flight-Grade Invariant Verification Matrix
==========================================

.. list-table:: Invariant Verification Performance
   :widths: 15 30 35 20
   :header-rows: 1

   * - Invariant ID
     - Name
     - Mathematical Rule
     - Result
   * - **INV-HYDRO-01**
     - Porosity Saturation Ceiling
     - :math:`\theta(z, t) \le \theta_{\text{sat}} = 0.450\text{ m}^3/\text{m}^3`
     - **1000/1000 PASS**
   * - **INV-HYDRO-02**
     - Residual Clamping
     - :math:`\theta(z, t) \ge \theta_{\text{res}} = 0.120\text{ m}^3/\text{m}^3, \frac{d\theta}{dt} \le 0`
     - **1000/1000 PASS**
   * - **INV-HYDRO-03**
     - Richards Mass Conservation Drift
     - :math:`|\text{Drift}| \le 1.0 \times 10^{-4}\text{ m}^3/\text{m}^3`
     - **1000/1000 PASS** (0.000000)
   * - **INV-KALMAN-04**
     - Covariance Conditioning Bound
     - :math:`\kappa(\mathbf{P}) < 1.0 \times 10^6, \lambda_{\min} > 10^{-9}`
     - **1000/1000 PASS** (:math:`\kappa_{\max} = 1709.03`)
   * - **INV-GEOTECH-05**
     - Bearing Capacity & Rut Bounds
     - :math:`q_{\text{ult}} > 0, 0 \le z_{\text{rut}} \le 35.0\text{ cm}`
     - **1000/1000 PASS**

Publication Figures & Visual Assets
===================================

The campaign generates three 600 DPI publication-grade figures in ``11_simulation_test_campaign/figures/``:

1. **Figure 1 (figure_1_enkf_covariance_stability):** Ensemble Kalman Filter covariance conditioning number (:math:`\kappa(P) < 1709.03 \ll 10^6`, safety margin :math:`585.1\times`) and eigenvalue spectrum.
2. **Figure 2 (figure_2_vadose_trajectory_fancharts):** Vadose zone moisture trajectory fan charts across 14-day desiccation and 7-day deluge stress cycles.
3. **Figure 3 (figure_3_terramechanics_disaster_envelopes):** Terramechanical disaster envelopes linking Bekker wheel sinkage, seedling damage, and Eurocode 7 slope stability.

Brutally Honest Engineering Limitations ("Ek Ek Dhappa")
========================================================

1. **Synthetic Forcing Parameterization:**
   Weather forcing in Q1 and Q2 utilizes parameterized mathematical bounds rather than raw multidecadal atmospheric reanalysis series. Synoptic multi-week climate teleconnections are not simulated.

2. **Chassis Grounding Hard Cutoff:**
   In Quadrant 4, rut sinkage is clamped at :math:`35.0\text{ cm}` when tractor differential clearance is exceeded. This captures vehicle immobilization accurately for advisory routing, but does not compute 3D soil flow around the chassis.

3. **1D Hydrodynamic Column Simplification:**
   Vadose flow is modeled vertically via 1D Richards equations, with lateral groundwater movement approximated via the Topographic Wetness Index rather than a 3D finite-element mesh.
