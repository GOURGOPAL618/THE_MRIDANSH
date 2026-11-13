.. _simulation_data_specification:

========================================================================
Subsystem 11: Simulation Data Store & Telemetry Architecture Specification
========================================================================

:Author: JAGANNATH COMMAND CENTER (JCC) - RS-SDA DIVISION
:System: Planetary Hydrology & Terramechanics Verification Campaign
:Classification: Spaceborne Ground-Truth Verification & Data Vault
:Revision: v2.4 (Sanitized Planetary Certification Baseline)

Overview & Directory Organization
=================================

The ``simulation_data/`` vault stores empirical simulation trajectories, stress-testing telemetry, and scenario validation records for the 1,000-trial planetary verification campaign.

Directory Hierarchy
-------------------

.. code-block:: text

   11_simulation_test_campaign/simulation_data/
   ├── master_campaign/
   │   ├── monte_carlo_1000_metrics.json          # Master 1,000-trial statistical metrics
   │   └── simulation_telemetry_results.json       # Operational pre-soak scenario results
   ├── Q1_drought/
   │   ├── Q1_drought_250_metrics.json             # 250-trial Hyper-Arid Drought metrics
   │   └── Q1_drought_250_trajectories.npy         # (250, 16) float32 trajectory tensor
   ├── Q2_deluge/
   │   ├── Q2_deluge_250_metrics.json             # 250-trial Monsoon Deluge metrics
   │   └── Q2_deluge_250_trajectories.npy         # (250, 8) float32 trajectory tensor
   ├── Q3_noise/
   │   ├── Q3_noise_250_metrics.json              # 250-trial Sensor Speckle metrics
   │   └── Q3_noise_250_trajectories.npy          # (250, 10) float32 trajectory tensor
   └── Q4_liquefaction/
       ├── Q4_liquefaction_250_metrics.json       # 250-trial Terramechanic Rutting metrics
       └── Q4_liquefaction_250_trajectories.npy   # (250, 8) float32 trajectory tensor

Data Matrix Specifications
==========================

Trajectory Tensor Layouts
-------------------------

All ``.npy`` artifacts are persisted in uncompressed IEEE 754 32-bit single-precision floating point (``float32``):

.. list-table:: Trajectory Binary Specifications
   :header-rows: 1
   :widths: 20 20 20 40

   * - Quadrant
     - File Name
     - Tensor Shape
     - Physical Significance
   * - **Q1: Drought**
     - ``Q1_drought_250_trajectories.npy``
     - ``(250, 16)``
     - 16-day severe drying curve under solar irradiance :math:`R_s \in [20, 32]\,\text{MJ/m}^2`.
   * - **Q2: Deluge**
     - ``Q2_deluge_250_trajectories.npy``
     - ``(250, 8)``
     - 8-day extreme monsoon saturation under precipitation :math:`P \in [40, 180]\,\text{mm/day}`.
   * - **Q3: Sensor Noise**
     - ``Q3_noise_250_trajectories.npy``
     - ``(250, 10)``
     - 10-day dual-satellite assimilation under :math:`\pm 4.5\,\text{dB}` SAR speckle noise.
   * - **Q4: Liquefaction**
     - ``Q4_liquefaction_250_trajectories.npy``
     - ``(250, 8)``
     - 8-day mud liquefaction under tractor axle loads :math:`W_{\text{axle}} \in [35, 55]\,\text{kN}`.

Statistical Ledger Schema
-------------------------

The master ledger (``monte_carlo_1000_metrics.json``) provides aggregate moments:

* **Total Trials Executed:** 1,000
* **Passed Trials:** 1,000 (100.0% qualification rate)
* **Mean Wall Time per Trial:** 6.53 ms
* **Condition Number Margin:** :math:`585.1\times` (:math:`\kappa_{\max} = 1709.03 \ll 10^6`)
* **Numerical Drift:** :math:`0.000000\,\text{m}^3/\text{m}^3`

Engineering Limitations & Boundary Disclosures ("Ek Ek Dhappa")
================================================================

1. **Dimensional Decoupling:**
   Trajectory matrices store column-averaged vadose water contents. Spatial variations within horizontal grid cells are neglected.
2. **Immobilization Rutting Cap:**
   Tractor sinkage depth is limited to 35.0 cm, representing chassis ground-out. Beyond this limit, mechanical drawbar pull collapses completely.
3. **Clamping Conservation:**
   Mass conservation drift of :math:`0.0` is achieved via post-update numerical projection back onto the valid convex simplex :math:`[\theta_r, \theta_s]`.
