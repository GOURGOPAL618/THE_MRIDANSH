.. _subsystem_05_master_cogs:

========================================================================================
Subsystem 05: Master Cloud-Optimized GeoTIFF (COG) Storage Specification
========================================================================================

:Engine: AETHER-MRID1607X
:Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
:Lead Architect: Gourgopal Mohapatra
:Status: FROZEN_OPERATIONAL_RELEASE_v1.0

Overview and Subsystem Mandate
==============================

The ``5_storage/master_cogs/`` repository functions as the primary spaceborne production raster export
and persistence repository for the **AETHER-MRID1607X** earth observation platform. Generated directly
by the monolithic pipeline orchestrator (``5_pipelines/mridansh_unified_orchestrator.py``), these
Cloud-Optimized GeoTIFFs (COGs) represent the multi-domain operational output of the system across a
contiguous 10-meter spatial mesh in **UTM Zone 45N (EPSG:32645)**.

Key operational objectives:

1. **Deterministic Spatial Registration:** Enforce sub-pixel spatial coherence across soil physics,
   agronomy irrigation prescriptions, and civil geotechnical engineering layers.
2. **Cloud-Optimized Streaming:** Implement internal block tiling (:math:`32 \times 32`) and LZW
   compression to facilitate rapid HTTP range querying for Web GIS viewports (``6_dashboard``).
3. **Cryptographic Provenance:** Validate bit-level raster integrity through SHA-256 digital signatures
   recorded in ``unified_execution_manifest.json``.

Master Raster Inventory & Grid Parameters
=========================================

Spatial Mesh Configuration:

* **Coordinate System:** WGS 84 / UTM Zone 45N (``EPSG:32645``)
* **Pixel Resolution:** :math:`10.0\ \text{m} \times 10.0\ \text{m}`
* **Spatial Dimensions:** :math:`64 \times 64` pixels (:math:`40.96\ \text{ha}`)
* **Bounding Box (Meters):** :math:`X \in [420000.0, 420640.0]`, :math:`Y \in [2240000.0, 2240640.0]`
* **Compression & Tiling:** LZW compression, :math:`32 \times 32` internal tiling, pixel interleaving
* **NoData Value:** ``-9999.0`` (Float32)

.. list-table:: Master Production COG Inventory
   :widths: 25 8 10 37 20
   :header-rows: 1

   * - Filename
     - Bands
     - Size (Bytes)
     - SHA-256 Hash
     - Domain Role
   * - ``master_unified_soil_state.tif``
     - 3
     - 51,771
     - ``a23b5414cc9fa5e0fab8511b05e51d3d373a80f552073c41bcc87a3fdd3369cf``
     - Vadose stratigraphy (:math:`\theta(z)`)
   * - ``master_agronomy_vri.tif``
     - 4
     - 71,882
     - ``adafc22089a54b424072ef5d1881371716b3fc88837f75395ba0a151627c3ed9``
     - Precision VRI & water deficit
   * - ``master_civil_geotech.tif``
     - 4
     - 37,729
     - ``9d4d6385b1cc50220b8b5bd137f49c18d770e8af10523947c93dbd8f9f2f2505``
     - Bearing capacity & rut depth
   * - ``unified_execution_manifest.json``
     - N/A
     - 1,038
     - ``d2220cff1d519cd545569c4ae0581a9ecee04f2b536773ba3d10c21217de1bcf``
     - Cryptographic provenance seal

Band Allocations and Physical Statistics
========================================

Master Unified Soil State (3 Bands)
-----------------------------------

.. list-table:: Vadose Zone Moisture Stratigraphy
   :widths: 8 26 16 16 16 18
   :header-rows: 1

   * - Band
     - Channel Description
     - Depth Horizon
     - Min (m³/m³)
     - Max (m³/m³)
     - Mean (m³/m³)
   * - 1
     - ``Theta_Surface_0_5cm``
     - :math:`0 - 5\ \text{cm}`
     - 0.1657
     - 0.2474
     - 0.2105
   * - 2
     - ``Theta_Rootzone_5_30cm``
     - :math:`5 - 30\ \text{cm}`
     - 0.1907
     - 0.2724
     - 0.2355
   * - 3
     - ``Theta_Deep_30_100cm``
     - :math:`30 - 100\ \text{cm}`
     - 0.2107
     - 0.2924
     - 0.2555

Master Agronomy VRI (4 Bands)
-----------------------------

.. list-table:: Precision Agriculture & Irrigation Prescriptions
   :widths: 8 28 18 14 14 18
   :header-rows: 1

   * - Band
     - Channel Description
     - Physical Units
     - Min
     - Max
     - Mean
   * - 1
     - ``NDVI``
     - Dimensionless
     - 0.2052
     - 0.7782
     - 0.4781
   * - 2
     - ``CWSI``
     - Index :math:`[0, 1]`
     - 0.1101
     - 0.6204
     - 0.3404
   * - 3
     - ``Root_Depletion_Dr_mm``
     - Millimeters (:math:`\text{mm}`)
     - 7.0641
     - 57.0070
     - 26.6600
   * - 4
     - ``Transpiration_Deficit_mm_day``
     - :math:`\text{mm}/\text{day}`
     - 0.5254
     - 3.0675
     - 1.6856

Master Civil Geotechnical (4 Bands)
-----------------------------------

.. list-table:: Soil Mechanics & Ground Stability
   :widths: 8 30 16 14 14 18
   :header-rows: 1

   * - Band
     - Channel Description
     - Physical Units
     - Min
     - Max
     - Mean
   * - 1
     - ``Apparent_Cohesion_kPa``
     - :math:`\text{kPa}`
     - 18.4542
     - 28.7478
     - 21.3713
   * - 2
     - ``Allowable_Bearing_q_allow_kPa``
     - :math:`\text{kPa}`
     - 360.5430
     - 544.2364
     - 412.5997
   * - 3
     - ``Factor_of_Safety_Slope``
     - Ratio :math:`[-]`
     - 10.0000
     - 10.0000
     - 10.0000
   * - 4
     - ``Tractor_Rut_Depth_cm``
     - Centimeters (:math:`\text{cm}`)
     - 1.5000
     - 1.5000
     - 1.5000

Brutally Honest Disclosures & Limitations
=========================================

1. **Flat Terrain Slope Stability Singularity Clamp:**
   The Taylor-Duncan infinite slope equation exhibits an asymptotic singularity as slope angle
   :math:`\beta \to 0^\circ`. Across the flat Kendrapara flight scene, the factor of safety is
   uniformly clamped to :math:`FS = 10.0`, masking micro-topographic stability gradients.
2. **Spatially Invariant Terramechanics Parameters:**
   Tractor rut sinkage is uniformly calculated as :math:`1.5000\ \text{cm}` because Bekker parameters
   (:math:`k_c, k_\phi, n`) are assigned homogeneously across the entire 40.96-ha domain.
3. **Internal Tile Overhead on Micro-Rasters:**
   Configuring :math:`32 \times 32` tile blocks on a compact :math:`64 \times 64` raster yields
   marginal streaming benefits while increasing GeoTIFF directory overhead.
4. **Client-Side CRS Reprojection Burden:**
   Direct ingestion into Web Mercator (``EPSG:3857``) viewports requires client-side reprojection,
   inducing minor sub-pixel resampling artifacts in real-time dashboards.

Traceable Requirements Matrix
=============================

.. list-table:: Subsystem 05 COG Requirements
   :widths: 20 20 40 20
   :header-rows: 1

   * - Requirement ID
     - Method
     - Specification Bound
     - Compliance Status
   * - **REQ-STOR-COG-01**
     - Geometry
     - Rasters must strictly align to UTM Zone 45N (``EPSG:32645``) at :math:`10.0\text{m}`.
     - **PASSED**
   * - **REQ-STOR-COG-02**
     - Inspection
     - Manifest must record bit-level SHA-256 signatures for all rasters.
     - **PASSED**
   * - **REQ-STOR-COG-03**
     - Inspection
     - Tiles must be :math:`32 \times 32` with LZW compression and ``-9999.0`` nodata.
     - **PASSED**
   * - **REQ-STOR-COG-04**
     - Range Test
     - Soil moisture values must satisfy physical bounds :math:`\theta \in [\theta_r, \theta_s]`.
     - **PASSED**
   * - **REQ-STOR-COG-05**
     - Integrity
     - Zero ``NaN`` or ``Inf`` values permitted in civil and agronomy bands.
     - **PASSED**
   * - **REQ-STOR-COG-06**
     - Metadata
     - All 11 raster bands must possess explicit descriptive ASCII identifiers.
     - **PASSED**
   * - **REQ-STOR-COG-07**
     - Benchmark
     - Monolithic production raster export latency must be :math:`< 100\ \text{ms}`.
     - **PASSED** (25.99 ms)
