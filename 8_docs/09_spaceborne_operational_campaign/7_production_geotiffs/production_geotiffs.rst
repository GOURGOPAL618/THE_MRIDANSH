.. _subsystem_09_production_geotiffs:

====================================================================================================
Subsystem 09: Spaceborne Operational Campaign — Production GeoTIFFs (`7_production_geotiffs/`)
====================================================================================================

:Central Engine: AETHER-MRID1607X
:Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
:Lead Systems Engineer: Gourgopal Mohapatra
:Release Status: TRL-7 OPERATIONAL FLIGHT READINESS

Overview & Purpose
==================

The ``7_production_geotiffs/`` subsystem houses the official geospatial raster deliverables, multi-band Cloud-Optimized GeoTIFF (COG) stacks, and spatial manifests for the **AETHER-MRID1607X** Earth Observation framework. Serving as Stage 7 of the Spaceborne Operational Campaign (SOC-AETHER-2026), this layer translates analytical PyTorch tensor bundles into georeferenced, cloud-streamable raster files conforming to **OGC GeoTIFF 1.1** and **Cloud-Optimized GeoTIFF (COG)** standards.

Geodetic Projection & Raster Parameters
=======================================

* **Coordinate Reference System:** Universal Transverse Mercator Zone 45N (``EPSG:32645``)
* **Horizontal Datum:** WGS 84
* **Ground Sample Distance (GSD):** :math:`10.0\text{ m} \times 10.0\text{ m}`
* **Spatial Bounds (Mahanadi Delta AOI):** Easting :math:`[420000.0, 420640.0]\text{ m}`, Northing :math:`[2240000.0, 2240640.0]\text{ m}`
* **Affine Transform Matrix:** :math:`[10.0, 0.0, 420000.0, 0.0, -10.0, 2240640.0]`
* **Compression Profile:** ``COMPRESS=LZW``, ``PREDICTOR=2``, NoData = ``-9999.0``

Master Multi-Band COG Stacks
============================

.. list-table:: Production Master COG Stacks
   :widths: 35 15 15 35
   :header-rows: 1

   * - Master COG Filename
     - File Size
     - Bands
     - Included Layers & Semantics
   * - **master_unified_soil_state_7layer.tif**
     - 54.2 KB
     - 7 Bands
     - Layers 1-4 Moisture (:math:`\theta`), Suction Head (:math:`h`), Conductivity (:math:`K`), Uncertainty (:math:`2\sigma_\theta`).
   * - **master_agronomic_vri_4layer_10m.tif**
     - 31.5 KB
     - 4 Bands
     - CWSI, Root-Zone Depletion (:math:`D_r`), VRI Prescription (L/ha), Conformal Risk Envelope (L/ha).
   * - **master_geotechnical_civil_4layer_10m.tif**
     - 29.7 KB
     - 4 Bands
     - Bearing Capacity (:math:`q_{\text{allow}}, FS \ge 3.0`), Slope Stability FS, TWI, Vehicle Mobility Tier.

Single-Band GeoTIFF Rasters
===========================

.. list-table:: Single-Band Production Rasters
   :widths: 35 20 20 25
   :header-rows: 1

   * - Raster Filename
     - Property
     - Units
     - Physical Range
   * - ``theta_surface_10m.tif``
     - Volumetric Soil Moisture (0-5cm)
     - :math:`\text{m}^3/\text{m}^3`
     - :math:`[0.191, 0.280]`
   * - ``theta_rootzone_10m.tif``
     - Volumetric Soil Moisture (5-30cm)
     - :math:`\text{m}^3/\text{m}^3`
     - :math:`[0.191, 0.280]`
   * - ``pore_pressure_head_10m.tif``
     - Matric Suction Head (:math:`h`)
     - :math:`\text{cm}`
     - :math:`[-237.49, -63.88]`
   * - ``hydraulic_conductivity_10m.tif``
     - Unsaturated Conductivity (:math:`K`)
     - :math:`\text{cm/day}`
     - :math:`[8.62 \times 10^{-5}, 5.43 \times 10^{-3}]`
   * - ``crop_water_stress_index_10m.tif``
     - CWSI Index
     - Unitless
     - :math:`[0.000, 0.426]`
   * - ``root_zone_depletion_dr_10m.tif``
     - Depletion Depth (:math:`D_r`)
     - :math:`\text{mm}`
     - :math:`[9.27, 128.79]`
   * - ``precision_irrigation_prescription_10m.tif``
     - VRI Irrigation Rate
     - :math:`\text{L/ha}`
     - :math:`[0.0, 1431035.0]`
   * - ``allowable_bearing_capacity_10m.tif``
     - Safe Bearing Capacity (:math:`q_{\text{allow}}`)
     - :math:`\text{kPa}`
     - :math:`[553.9, 806.0]`
   * - ``topographic_wetness_index_10m.tif``
     - Topographic Wetness Index
     - Unitless
     - :math:`[8.74, 10.20]`

Verification Scorecard (SOC-21 to SOC-22)
=========================================

.. list-table:: Automated Test Verification Results
   :widths: 15 35 25 15
   :header-rows: 1

   * - Test ID
     - Verification Target
     - Measured Result
     - Status
   * - SOC-21
     - GeoTIFF Georeference & Affine Transform
     - Valid EPSG:32645 CRS, exact affine transform
     - **PASS**
   * - SOC-22
     - 7-Layer COG Band Semantics & Zero NaNs
     - 7 distinct bands validated, 0 NaN pixels out of 4,096
     - **PASS**

Brutally Honest Engineering Limitations ("Ek Ek Dhappa")
========================================================

1. **Windows OS Concurrent File Locking:**
   External GIS tools (QGIS/ArcGIS) locking open GeoTIFF files on Windows trigger ``PermissionError [Errno 13]``. The exporter implements an active ``_is_file_locked_by_viewer()`` probe and timestamped fallback file naming.

2. **Float32 Uncompressed Storage Overhead:**
   Each single-band GeoTIFF requires ~16.5 KB and the 7-layer COG requires ~54.2 KB for a single 40.96 ha patch. Large provincial monitoring campaigns require scaled integer quantization (``uint16``) to optimize disk usage.

3. **Web Mercator Reprojection Resampling Blur:**
   Exported rasters are projected natively in UTM Zone 45N (``EPSG:32645``). Dynamic client-side re-projection to Web Mercator (``EPSG:3857``) in Leaflet viewports introduces subtle antialiasing blur along sharp agricultural field parcel boundaries.
