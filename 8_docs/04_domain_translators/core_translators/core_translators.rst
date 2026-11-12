.. _subsystem_04_core_translators:

================================================================================
Subsystem 04: Domain Translators Core Architecture (4_domain_translators/)
================================================================================

:Central Engine: AETHER-MRID1607X
:Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
:Lead Architect: Gourgopal Mohapatra
:Release Status: FROZEN_OPERATIONAL_RELEASE_v1.0

Executive Overview & Subsystem Mandate
======================================

The root layer of ``4_domain_translators/`` constitutes the architectural contract bridge, multi-domain
integration router, coupled agro-geotechnical simulator, temporal hydrodynamic forecaster, and spatial
zonal extractor for the **AETHER-MRID1607X** earth observation platform. Operating downstream of
``3_core_engine/`` (PINN Richards Physics, EnKF Assimilation) and upstream of ``6_dashboard/``, this
layer enforces strict physical data validation, prevents blind neural latent hallucination, and translates
volumetric soil moisture tensors into actionable agricultural and civil engineering telemetry.

Core Architecture & Module Inventory
====================================

.. code-block:: text

       +-------------------------------------------------------------------------+
       |                CORE ENGINE OUTPUTS (3_core_engine/)                     |
       |    * EnKF Posterior State (theta, variance)                             |
       |    * PINN Richards Physics Predictions                                  |
       |    * Multi-Modal Backbone Latent Features (Blocked without Head)        |
       +------------------------------------+------------------------------------+
                                            |
                                            v
       +-------------------------------------------------------------------------+
       |                DOMAIN INTEGRATION ROUTER (domain_integrator.py)         |
       |  * Validates 2D Spatial Tensors & Enforces [0.0, 1.0] Bounds            |
       |  * Anti-Hallucination Gate (IntegrationBlockedError on Raw Latents)     |
       |  * Packages Unified DomainInput Contracts (base.py)                     |
       +------------------------------------+------------------------------------+
                                            |
         +----------------------------------+----------------------------------+
         |                                  |                                  |
         v                                  v                                  v
+-----------------------+        +-----------------------+        +-----------------------+
|  TRANSLATOR WRAPPERS  |        |  COUPLED SIMULATOR    |        |  TEMPORAL & ZONAL     |
| * agronomy_translator |        | (coupled_agro_civil_  |        | * temporal_           |
|   (Crop Health & CWSI)|        |  simulator.py)        |        |   hydrodynamics.py    |
| * civil_translator    |        | * Bekker Tyre Sinkage |        |   (1D Richards Bucket |
|   (Bearing & FS>=3.0) |        | * Seedling Damage     |        |    & SAR Delta Nudge) |
|                       |        | * Goldilocks Water    |        | * zonal_field_        |
|                       |        | * Monte Carlo Trials  |        |   extractor.py        |
+-----------------------+        +-----------------------+        +-----------------------+

Mathematical Formulations & Physical Equations
==============================================

1D Richards-Bucket Mass Conservation
------------------------------------

Across daily weather forcing steps (:math:`P_t` precipitation, :math:`ET_{0,t}` reference evapotranspiration),
volumetric moisture evolves according to constrained mass conservation in ``temporal_hydrodynamics.py``:

.. math::

   \theta_{t+1} = \text{clip}\left(\theta_t + \frac{P_t - K_s(\theta_t) \cdot ET_{0,t} - D(\theta_t)}{z_{\text{root}} \cdot 1000}, \; \theta_{\text{wilt}}, \; \theta_{\text{sat}}\right)

SAR Backscatter Anomaly Nudging
-------------------------------

Between consecutive Sentinel-1 C-band passes (:math:`\sigma^0_{\text{anchor}}, \sigma^0_{\text{curr}}` in dB):

.. math::

   \Delta \sigma^0 = \sigma^0_{\text{curr}} - \sigma^0_{\text{anchor}} \quad [\text{dB}]

Metric Shoelace Geodesic Area
-----------------------------

For arbitrary closed farm boundary vertices :math:`(x_i, y_i)` projected onto local metric coordinates (meters),
``zonal_field_extractor.py`` calculates exact enclosed surface area via the Shoelace theorem:

.. math::

   A_{\text{poly}} = \frac{1}{2} \left| \sum_{i=0}^{N-1} (x_i y_{i+1} - x_{i+1} y_i) \right| \quad [\text{m}^2]

Brutally Honest Engineering Disclosures ("Ek Ek Dhappa")
========================================================

1. **Intentional Blocking of Raw Backbone Latents**: ``domain_integrator.py`` explicitly raises ``IntegrationBlockedError`` if raw neural embeddings lack a validated physical projection head.
2. **1D Bucket vs Full 3D Richards**: ``temporal_hydrodynamics.py`` propagates columns vertically in 1D, neglecting lateral surface runoff between adjacent DEM slopes.
3. **SAR Backscatter Canopy Interference**: ``detect_sar_anomaly`` attributes :math:`\Delta \sigma^0` shifts to soil moisture, though rapid crop canopy growth can produce false wetting surge signals.
4. **Pure-Python Ray-Casting Loop**: ``rasterize_polygon_mask`` runs a Python loop per pixel, which is fast for :math:`64 \times 64` grids but becomes a bottleneck on large regional rasters.
5. **Heuristic Root Wrappers**: Root translators perform broad sanity bounds and preliminary advisories; deep physical models live in the ``agronomy/`` and ``civil/`` submodules.

Traceable Functional Requirements
=================================

.. list-table::
   :widths: 20 20 25 35
   :header-rows: 1

   * - Requirement ID
     - Verification Type
     - Target Module
     - Technical Specification
   * - **REQ-TRNS-CORE-01**
     - Unit Test
     - ``base.py``
     - ``DomainInput`` rejects non-2D arrays, NaNs, and values outside :math:`[0.0, 1.0]`.
   * - **REQ-TRNS-CORE-02**
     - Integration Test
     - ``domain_integrator.py``
     - Router raises ``IntegrationBlockedError`` on unmapped raw neural latent tensors.
   * - **REQ-TRNS-CORE-03**
     - Safety Audit
     - ``civil_translator.py``
     - Civil wrapper enforces explicit :math:`FS \ge 3.0` structural safety disclaimers.
   * - **REQ-TRNS-CORE-04**
     - Unit Test
     - ``coupled_agro_civil_simulator.py``
     - Tractor sinkage and seedling damage models compute monotonic damage bounded in :math:`[0.0, 1.0]`.
   * - **REQ-TRNS-CORE-05**
     - Simulation Test
     - ``coupled_agro_civil_simulator.py``
     - Vectorized Monte Carlo stress test generates mean and variance distributions.
   * - **REQ-TRNS-CORE-06**
     - Physics Test
     - ``temporal_hydrodynamics.py``
     - ``propagate_step`` conserves mass within :math:`[\theta_{\text{wilt}}, \theta_{\text{sat}}]` bounds.
   * - **REQ-TRNS-CORE-07**
     - Signal Test
     - ``temporal_hydrodynamics.py``
     - ``detect_sar_anomaly`` classifies backscatter deltas into ``{-1, 0, +1}`` masks.
   * - **REQ-TRNS-CORE-08**
     - Geometry Test
     - ``zonal_field_extractor.py``
     - Extractor computes Shoelace area, ray-cast masks, and sub-10m centroid fallbacks.
