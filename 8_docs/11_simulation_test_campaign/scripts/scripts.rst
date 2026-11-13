.. _subsystem_11_scripts:

====================================================================================================
Subsystem 11: Simulation Test Campaign — Scripts Specification (`11_simulation_test_campaign/scripts/`)
====================================================================================================

:Central Engine: AETHER-MRID1607X
:Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
:Lead Systems Architect: Gourgopal Mohapatra
:Release Status: TRL-7 OPERATIONAL FLIGHT READINESS

Overview & Purpose
==================

The ``11_simulation_test_campaign/scripts/`` subsystem contains the high-performance in-memory simulation engines, scenario drivers, and automated artifact rendering tools for the **AETHER-MRID1607X** 1,000-Trial Planetary Monte Carlo Stress Campaign.

Scripts Inventory & Interface Contracts
=======================================

.. list-table:: Scripts Inventory
   :widths: 30 20 50
   :header-rows: 1

   * - Script Filename
     - File Size
     - Core Functionality
   * - **planetary_monte_carlo_engine.py**
     - 66.5 KB
     - Master vectorized engine executing 1,000 trials across 4 quadrants in 6.53s total (6.53 ms/trial).
   * - **generate_monte_carlo_artifacts.py**
     - 18.5 KB
     - Publication graphics compiler generating 600 DPI PNG and vector PDF figures.
   * - **run_simulation.py**
     - 6.1 KB
     - Coupled agro-civil scenario runner evaluating 5 tillage moisture regimes.

Brutally Honest Engineering Limitations ("Ek Ek Dhappa")
========================================================

1. **In-Memory Trajectory Caching:**
   Trajectories are stored in memory before disk serialization. Scaling beyond 10,000 trials requires HDF5/Zarr memory-mapped stores.

2. **Sequential Figure Compilation:**
   Matplotlib rendering executes sequentially on CPU (:math:`\sim 10.5\text{ s}`), which is acceptable for offline publication workflows.
