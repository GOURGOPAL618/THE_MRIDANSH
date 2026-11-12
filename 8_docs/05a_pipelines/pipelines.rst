.. _subsystem_05_pipelines:

================================================================================
Subsystem 05: Unified Production Orchestration Pipeline (5_pipelines)
================================================================================

:Central Engine: AETHER-MRID1607X
:Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
:Lead Architect: Gourgopal Mohapatra
:Release Status: FROZEN_OPERATIONAL_RELEASE_v1.0

Executive Overview & Subsystem Mandate
======================================

The ``5_pipelines/`` subsystem constitutes the master end-to-end execution orchestrator for the **AETHER-MRID1607X**
spaceborne earth observation and precision soil intelligence platform. Encapsulated within ``mridansh_unified_orchestrator.py``
(25.4 KB, 554 lines), this module serves as the unified operational conduit bridging raw spaceborne tensor bundles
(``9_spaceborne_operational_campaign/``), multi-day temporal hydrodynamics (``4_domain_translators/temporal_hydrodynamics.py``),
dual-domain physics translators (``agronomy/`` and ``civil/``), coupled agro-geotechnical simulations, and cryptographic
Cloud-Optimized GeoTIFF (COG) production manifests (``5_storage/master_cogs/``).

Pipeline Architecture & Execution Stages
========================================

.. code-block:: text

       +-------------------------------------------------------------------------+
       |        HARMONIZED SPACEBORNE TENSOR BUNDLE (.pt PyTorch Dictionary)     |
       |  * Sentinel-1 SAR (VV, VH), Sentinel-2 Optical (B4 Red, B8 NIR), DEM    |
       |  * Core Engine Soil State Predictions (theta_surf, theta_root, theta_deep)|
       +------------------------------------+------------------------------------+
                                            |
                                            v
       +-------------------------------------------------------------------------+
       |              MRIDANSH UNIFIED ORCHESTRATOR (mridansh_unified_orchestrator.py)
       |  [Stage 1] Input Integrity Validation & Tensor Unpacking                |
       |  [Stage 2] SAR Anomaly Check & Multi-Day Temporal Hydrodynamic Forecast |
       |  [Stage 3] Dual-Domain Translation (Agronomy FAO-56 & Civil Mechanics)  |
       |  [Stage 4] Coupled Agro-Civil Simulation (Tractor Sinkage & Goldilocks) |
       |  [Stage 5] Triple-COG GeoTIFF Export + SHA-256 Manifest Generation      |
       |  [Stage 6] Aerospace Contract Verification (PIPE-01 through PIPE-05)    |
       +------------------------------------+------------------------------------+
                                            |
         +----------------------------------+----------------------------------+
         |                                  |                                  |
         v                                  v                                  v
+-----------------------+        +-----------------------+        +-----------------------+
|  UNIFIED SOIL STATE   |        |  AGRONOMY VRI COG     |        |  CIVIL GEOTECH COG    |
| * master_unified_     |        | * master_agronomy_    |        | * master_civil_       |
|   soil_state.tif      |        |   vri.tif             |        |   geotech.tif         |
| * 3-Layer Moisture    |        | * CWSI, Deficit, VRI  |        | * q_allow, FS, Rut    |
+-----------------------+        +-----------------------+        +-----------------------+

Verification Contracts (PIPE-01 through PIPE-05)
================================================

.. list-table::
   :widths: 28 42 30
   :header-rows: 1

   * - Contract ID
     - Verification Criterion
     - Enforcement Threshold
   * - **PIPE-01_TEMPORAL_MONOTONICITY**
     - Monotonic drying dynamics under zero-rain forecasts.
     - ``monotonicity_verified == True``
   * - **PIPE-02_MASS_CONSERVATION_BOUNDS**
     - Surface and root moisture bounded within physical vadose limits.
     - :math:`0.049 \le \theta \le 0.481`
   * - **PIPE-03_UNIFIED_FINITE_EXECUTION**
     - Zero-NaN, finite state validation across all output domains.
     - ``np.all(np.isfinite(...)) == True``
   * - **PIPE-04_TRIPLE_COG_ALIGNMENT**
     - All exported Triple-COG GeoTIFFs exist physically on disk.
     - ``Path(r_path).exists() == True``
   * - **PIPE-05_LATENCY_SLA**
     - End-to-end real-time per-pixel execution throughput budget.
     - :math:`\text{latency} < 0.025\text{ ms/pixel}`

Brutally Honest Engineering Disclosures ("Ek Ek Dhappa")
========================================================

1. **Self-Referential SAR Anomaly Check (Line 235)**: ``detect_sar_anomaly(vv_anchor, vv_anchor)`` passes the identical tensor for both passes when a second temporal image is omitted, yielding :math:`\Delta\sigma^0 = 0.0\text{ dB}`.
2. **Linear Moisture Offset Extrapolation (Lines 249-250)**: Multi-day forecasts advance ``theta_surf_arr`` via the 1D bucket model, then compute ``theta_root_arr`` and ``theta_deep_arr`` using fixed linear offsets (``+0.025``, ``+0.020``) rather than solving multi-layer Richards diffusion.
3. **Dynamic importlib Workarounds**: Because directory names start with digits (``4_domain_translators``), the orchestrator imports modules dynamically via ``importlib.import_module()``, bypassing static type checking.
4. **Default Dry-Down Schedule**: Omitting ``weather_schedule`` falls back to a synthetic 5-day dry-down (:math:`ET_0 = 4.5\text{ mm/day}`, :math:`P = 0.0\text{ mm}`).

Traceable Functional Requirements
=================================

.. list-table::
   :widths: 20 20 25 35
   :header-rows: 1

   * - Requirement ID
     - Verification Type
     - Target Module
     - Technical Specification
   * - **REQ-PIPE-01**
     - Integration Test
     - ``mridansh_unified_orchestrator.py``
     - Loads tensor bundles and validates required keys without unhandled exceptions.
   * - **REQ-PIPE-02**
     - Physics Test
     - ``mridansh_unified_orchestrator.py``
     - Satisfies ``PIPE-01`` monotonicity and ``PIPE-02`` mass conservation bounds.
   * - **REQ-PIPE-03**
     - Integrity Test
     - ``mridansh_unified_orchestrator.py``
     - ``PIPE-03`` enforces 100% finite outputs across hydrology, agronomy, and civil domains.
   * - **REQ-PIPE-04**
     - Export Test
     - ``mridansh_unified_orchestrator.py``
     - Writes Triple-COG GeoTIFFs and ``unified_execution_manifest.json`` with SHA-256 digests.
   * - **REQ-PIPE-05**
     - Performance Test
     - ``mridansh_unified_orchestrator.py``
     - Meets ``PIPE-05`` real-time latency SLA (:math:`< 0.025\text{ ms/pixel}`).
