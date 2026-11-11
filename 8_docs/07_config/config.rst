.. _subsystem_07_config:

================================================================================
Subsystem 07: Global Configuration Matrix Specification (7_config)
================================================================================

:Central Engine: AETHER-MRID1607X
:Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
:Lead Architect: Gourgopal Mohapatra
:Release Status: FROZEN_OPERATIONAL_RELEASE_v1.0

Executive Overview & Subsystem Mandate
======================================

The ``7_config/`` repository houses the central declarative configuration matrix for the
**AETHER-MRID1607X** earth observation and multi-domain soil intelligence platform. Enclosed within
``global_config.yaml`` (664 bytes, 21 lines), this subsystem establishes immutable global system boundaries,
default geospatial coordinate reference systems (CRS), multi-sensor satellite band definitions, and baseline
physical constants for Richards' equation hydrological modeling.

The primary mandate of ``7_config/`` is to serve as the single source of truth across all upstream ingestion
pipelines (``2_data_pipeline/``), core physics engines (``3_core_engine/``), domain translators (``4_domain_translators/``),
and operational command interfaces (``6_dashboard/``). Parsed at application bootstrap by ``ConfigLoader``
(``3_core_engine/utils.py``), this configuration matrix prevents cross-subsystem parameter divergence.

Configuration Architecture & Distribution Pipeline
===================================================

.. code-block:: text

       +-------------------------------------------------------------------------+
       |             GLOBAL CONFIGURATION MATRIX (7_config/global_config.yaml)  |
       +------------------------------------+------------------------------------+
                                            |
                                            v
       +-------------------------------------------------------------------------+
       |                 CENTRAL PARSER & VALIDATION LOADER                      |
       |                   (3_core_engine/utils.py: ConfigLoader)                |
       |  * YAML Safe Load Matrix                                                |
       |  * Dot-Notation Parameter Querying (get_param("spatial_bounds.crs"))    |
       +------------------------------------+------------------------------------+
                                            |
         +----------------------------------+----------------------------------+
         |                                  |                                  |
         v                                  v                                  v
+-----------------------+        +-----------------------+        +-----------------------+
|  SPATIAL BOUNDS       |        |  SATELLITE CHANNELS   |        |  HYDROLOGY PHYSICS    |
| * CRS: EPSG:4326      |        | * S1: VV, VH (SAR)    |        | * Porosity Max: 0.45  |
| * Res: 30.0 meters    |        | * S2: B02, B03, B04,  |        | * K_sat Baseline:     |
| * Default Bounding    |        |       B08, B11, B12   |        |   0.001 cm/s          |
|   Box Coordinates     |        | * DEM: COP30 GLO-30   |        | * Gravity (g): 9.81   |
+-----------------------+        +-----------------------+        +-----------------------+

Configuration Parameter Inventory & Semantics
=============================================

.. list-table::
   :widths: 25 20 20 35
   :header-rows: 1

   * - Parameter Key
     - Configured Value
     - Unit / Format
     - Architectural Role
   * - ``project_name``
     - ``"THE_MRIDANSH"``
     - UTF-8 String
     - Canonical workspace project name.
   * - ``engine_version``
     - ``"AETHER-MRID1607X"``
     - Semantic Tag
     - Frozen physical-neural hybrid engine release tag.
   * - ``spatial_bounds.crs``
     - ``"EPSG:4326"``
     - EPSG Code
     - Standard geographic latitude/longitude coordinate frame.
   * - ``spatial_bounds.resolution_meters``
     - ``30.0``
     - Meters (:math:`\text{m}`)
     - Default spatial resampling grid cell size.
   * - ``spatial_bounds.default_bbox``
     - ``[77.0, 28.0, 78.0, 29.0]``
     - Vector
     - Reference testing domain (Delhi NCR / Yamuna basin).
   * - ``satellite_channels.sentinel_1``
     - ``["VV", "VH"]``
     - Polarization
     - C-band SAR backscatter input polarizations.
   * - ``satellite_channels.sentinel_2``
     - 6 Optical Bands
     - Wavelengths
     - B02 (Blue), B03 (Green), B04 (Red), B08 (NIR), B11 (SWIR1), B12 (SWIR2).
   * - ``satellite_channels.dem_source``
     - ``"COP30"``
     - DEM Dataset
     - Copernicus 30m Global DEM terrain elevation grid.
   * - ``hydrology_physics.porosity_max``
     - ``0.45``
     - :math:`\text{m}^3/\text{m}^3`
     - Maximum saturated volumetric moisture fraction (:math:`\theta_{\text{sat}}`).
   * - ``hydrology_physics.hydraulic_conductivity_baseline``
     - ``0.001``
     - :math:`\text{cm/s}`
     - Baseline saturated hydraulic conductivity (:math:`K_{\text{sat}}`).
   * - ``hydrology_physics.gravity_constant``
     - ``9.81``
     - :math:`\text{m/s}^2`
     - Gravitational acceleration constant (:math:`g`).

Brutally Honest Engineering Disclosures ("Ek Ek Dhappa")
========================================================

1. **Relative Path Hardcoding**: ``ConfigLoader`` defaults to ``7_config/global_config.yaml``. Running from subdirectories without setting root CWD triggers immediate ``FileNotFoundError``.
2. **Absence of Strict Schema Validation**: Ingestion uses raw ``yaml.safe_load()`` without Pydantic or Cerberus runtime type enforcement. Key typos fail late during execution.
3. **Disjoint Testing vs Operational Bounding Box**: Default BBox covers Delhi NCR (:math:`28^\circ\text{N}`), while operational campaign tensors reside in Kendrapara, Odisha (:math:`20.5^\circ\text{N}`).
4. **Static Single-Layer Soil Physics**: Porosity (0.45) and conductivity (0.001) are static global scalars, ignoring stratified van Genuchten soil water retention parameters (:math:`\alpha, n`).

Traceable Functional Requirements
=================================

.. list-table::
   :widths: 20 20 25 35
   :header-rows: 1

   * - Requirement ID
     - Verification Type
     - Target Module
     - Technical Specification
   * - **REQ-CONF-01**
     - Parsing Test
     - ``global_config.yaml``
     - YAML matrix parses cleanly under PyYAML safe_load without external tags.
   * - **REQ-CONF-02**
     - Schema Test
     - ``global_config.yaml``
     - Spatial bounds define EPSG:4326, 30m resolution, and valid 4-element BBox.
   * - **REQ-CONF-03**
     - Interface Test
     - ``global_config.yaml``
     - Satellite channels define VV/VH SAR, 6 MSI optical bands, and COP30 DEM.
   * - **REQ-CONF-04**
     - Physics Test
     - ``global_config.yaml``
     - Hydrology parameters declare positive physical bounds (:math:`0 < \phi \le 0.45`, :math:`g = 9.81`).
   * - **REQ-CONF-05**
     - Integration Test
     - ``3_core_engine/utils.py``
     - ``ConfigLoader.get_param`` resolves nested dot-notation paths across the YAML tree.
