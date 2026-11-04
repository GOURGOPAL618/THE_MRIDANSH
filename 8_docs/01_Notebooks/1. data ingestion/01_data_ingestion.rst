========================================================================================
THE MRIDANSH (AETHER-MRID1607X) - Notebook 01: Multi-Source Telemetry Data Ingestion
========================================================================================

:Project: THE MRIDANSH - Unified Soil State Estimation System
:Engine: AETHER-MRID1607X (Multi-Domain Soil Intelligence Engine)
:Notebook: ``1_notebooks_sandbox/01-data-ingestion.ipynb``
:Sprint Phase: Phase 1 (Data Ingestion & Baseline Structure Establishment)
:Division: RS-SDA (Remote Sensing & Spatial Data Analytics), JCC Campus 2 / Headquarter
:Author / Maintainer: Gourgopal Mohapatra
:Copyright: (c) 2026 Gourgopal Mohapatra. All Rights Reserved.
:Document Type: Technical Description and Software Design Specification
:Document ID: MRID-NB01-SPEC-001
:Document Status: Approved — Unfiltered Engineering Audit
:Classification: Proprietary & Controlled Research Artifact

.. contents:: Table of Contents
   :depth: 3
   :local:


1. Technical Overview
=====================

1.1 Objective
-------------
The primary engineering objective of ``01-data-ingestion.ipynb`` is to establish the observational intake
architecture for **THE MRIDANSH** (*AETHER-MRID1607X*). The notebook formalizes the spatial bounding
box parameterization, generates synchronized multi-sensor time-series telemetry (Sentinel-1 SAR backscatter,
Sentinel-2 multispectral surface reflectance, meteorological forcing, and digital elevation models), performs
spatial sub-grid resampling, constructs a SpatioTemporal Asset Catalog (STAC 1.0.0) GeoJSON metadata manifest,
and persists all observational artifacts into standardized project storage lakes.

1.2 System Context
------------------
Within the **THE MRIDANSH** macro-architecture:

* **Spatial Anchor**: Targets the Bhadrak Catchment, Odisha, India (:math:`21.1378^\circ\,\text{N}, 86.6874^\circ\,\text{E}`).
* **Temporal Domain**: Monsoon monitoring window spanning 35 epochs from ``2026-08-01`` to ``2026-09-07``.
* **Sensor Modalities**:
  - **Copernicus Sentinel-1 C-Band SAR**: Microwave backscatter :math:`\sigma^0_{\text{VV}} \in [-18, -8]\,\text{dB}`,
    :math:`\sigma^0_{\text{VH}} \in [-25, -14]\,\text{dB}`, and polarization ratio :math:`\text{VH}/\text{VV}`.
  - **Copernicus Sentinel-2 MSI**: Optical surface reflectance bands :math:`B03` (Green), :math:`B04` (Red),
    and :math:`B08` (NIR) with dynamic cloud cover percentage :math:`[0, 90]\%`.
  - **Digital Elevation Model (DEM)**: Low-resolution native :math:`33 \times 33` grid at :math:`30\,\text{m}` GSD.
  - **Atmospheric Forcing**: Monsoonal precipitation (:math:`\text{mm/day}`) and surface air temperature (:math:`^\circ\text{C}`).
* **Downstream Integration**: Emits ``stac_telemetry_raw.csv`` and ``stac_catalog_item.json`` to
  ``5_storage/notebook_results/notebook_01_ingestion/`` and ``data/raw/``, feeding directly into Notebook 02
  (``02-preprocessing.ipynb``).

1.3 Design Boundary
-------------------
* **In Boundary**:
  - Bounding box calculation with angular buffer :math:`\Delta = 0.05^\circ`.
  - Synthetic multi-sensor telemetry simulation conforming to real physical sensor bounds.
  - Derivation of normalized difference spectral vegetation and water indices (NDVI, NDWI).
  - Spatial 2D sub-grid generation (:math:`100 \times 100` pixels) and bilinear DEM upsampling.
  - Construction and validation of STAC 1.0.0 GeoJSON Feature dictionary.
  - Export of 6 high-contrast publication aerospace telemetry plots.
* **Out of Boundary**:
  - Direct live network queries against ESA Copernicus Open Access Hub or CDSE (simulated locally).
  - SAR speckle Lee filtering (delegated to Notebook 02).
  - Soil moisture state estimation or Kalman filter assimilation (delegated to Notebooks 05 & 06).


2. Architecture
===============

2.1 Notebook Pipeline Architecture
----------------------------------
The ingestion pipeline is organized into seven sequential computational stages:

.. code-block:: text

   +--------------------------------------------------------------------------------------------------+
   |                        STAGE 1: GEODETIC SPATIAL BOUNDING PARAMETERIZATION                       |
   |   Centroid: (21.1378 N, 86.6874 E) | Buffer: 0.05 deg -> BBOX [86.6374, 21.0878, 86.7374, 21.1878] |
   +--------------------------------------------------------------------------------------------------+
                                                    |
                                                    v
   +--------------------------------------------------------------------------------------------------+
   |                        STAGE 2: MULTI-SENSOR SYNTHETIC TELEMETRY ENGINE                          |
   |   - Sentinel-1 SAR: VV in [-18, -8] dB, VH in [-25, -14] dB                                      |
   |   - Sentinel-2 MSI: B03 [0.05, 0.22], B04 [0.02, 0.18], B08 [0.20, 0.52], Cloud in [0, 90]%      |
   |   - Weather: Temp in [25, 36] C, Monsoonal Precip Choice [0, 1.2, 8.5, 32, 75] mm                |
   |   - In-line Indices: NDVI = (NIR - Red)/(NIR + Red), NDWI = (Green - NIR)/(Green + NIR)          |
   +--------------------------------------------------------------------------------------------------+
                                                    |
                                                    v
   +--------------------------------------------------------------------------------------------------+
   |                        STAGE 3: DATA INTEGRITY & STATISTICAL AUDIT                               |
   |   - Assert EPSG:4326 CRS Uniformity                                                              |
   |   - Assert Zero Nulls / Missing Frames                                                           |
   |   - Analyze Cloud Coverage (>50% Days) to justify SAR necessity                                  |
   |   - Assert Spectral Indices strictly in [-1.0, 1.0]                                              |
   |   - Tag provenance: "SYNTHETIC_SIMULATION"                                                       |
   +--------------------------------------------------------------------------------------------------+
                                                    |
                                                    v
   +--------------------------------------------------------------------------------------------------+
   |                        STAGE 4 & 5: 2D SPATIAL RASTER SUB-GRID & RESAMPLING                      |
   |   - High-Res Sentinel Grid: 100 x 100 pixels (~10m GSD -> 1km x 1km sub-grid)                    |
   |   - Native Low-Res DEM: 33 x 33 pixels (~30m GSD)                                                |
   |   - Resampling: scipy.ndimage.zoom(dem, (100/33, 100/33), order=1) -> 100 x 100 Aligned Grid     |
   +--------------------------------------------------------------------------------------------------+
                                                    |
                                                    v
   +--------------------------------------------------------------------------------------------------+
   |                        STAGE 6: STAC 1.0.0 METADATA MANIFEST ASSEMBLY                            |
   |   - Standard GeoJSON Feature dictionary with explicit Polygon geometry                           |
   |   - Correct 'assets' dictionary (B04_RED, B08_NIR, B03_GREEN, SAR_VV, SAR_VH, DEM_ALIGNED)      |
   +--------------------------------------------------------------------------------------------------+
                                                    |
                                                    v
   +--------------------------------------------------------------------------------------------------+
   |                        STAGE 7: PERSISTENCE & DATA LAKE EXPORT                                   |
   |   - 6 High-Contrast Aerospace Plots -> 5_storage/notebook_01_ingestion/                          |
   |   - stac_telemetry_raw.csv & stac_catalog_item.json -> 5_storage/ & data/raw/                    |
   +--------------------------------------------------------------------------------------------------+


3. Mathematical Foundations & Algorithms
========================================

3.1 Geodetic Spatial Parameterization
-------------------------------------
The spatial bounding box is formulated as a 2D axis-aligned bounding box (AABB) in the WGS84 coordinate
system (EPSG:4326):

.. math::

   \lambda_{\text{min}} = \lambda_0 - \Delta, \quad \lambda_{\text{max}} = \lambda_0 + \Delta

.. math::

   \varphi_{\text{min}} = \varphi_0 - \Delta, \quad \varphi_{\text{max}} = \varphi_0 + \Delta

where :math:`\lambda_0 = 86.6874^\circ\,\text{E}`, :math:`\varphi_0 = 21.1378^\circ\,\text{N}`, and
:math:`\Delta = 0.05^\circ \approx 5.55\,\text{km}`.

3.2 Optical Spectral Indices
----------------------------
The Normalized Difference Vegetation Index (NDVI) and Normalized Difference Water Index (NDWI) evaluate
relative vegetative vigor and surface moisture:

.. math::

   \text{NDVI} = \frac{\rho_{\text{NIR}} - \rho_{\text{Red}}}{\rho_{\text{NIR}} + \rho_{\text{Red}}} = \frac{B08 - B04}{B08 + B04}

.. math::

   \text{NDWI} = \frac{\rho_{\text{Green}} - \rho_{\text{NIR}}}{\rho_{\text{Green}} + \rho_{\text{NIR}}} = \frac{B03 - B08}{B03 + B08}

3.3 Multi-Resolution Spatial Resampling
---------------------------------------
The native digital elevation model grid :math:`\mathbf{D}_{\text{native}} \in \mathbb{R}^{33 \times 33}`
(representing :math:`30\,\text{m}` spatial sampling) is upscaled to align with the optical/SAR spatial matrix
:math:`\mathbf{R} \in \mathbb{R}^{100 \times 100}` (:math:`10\,\text{m}` spatial sampling) via 2D bilinear
spline interpolation:

.. math::

   s_y = \frac{H_{\text{target}}}{H_{\text{source}}} = \frac{100}{33} \approx 3.0303, \quad
   s_x = \frac{W_{\text{target}}}{W_{\text{source}}} = \frac{100}{33} \approx 3.0303

.. math::

   \mathbf{D}_{\text{aligned}} = \text{zoom}\left(\mathbf{D}_{\text{native}}, (s_y, s_x), \text{order}=1\right)


4. Component & Data Structure Design
====================================

4.1 Telemetry DataFrame Schema
------------------------------
The output CSV dataset ``stac_telemetry_raw.csv`` adheres to the following structural schema:

.. list-table:: Ingested Telemetry Data Schema
   :widths: 25 20 55
   :header-rows: 1

   * - Column Name
     - Data Type
     - Description
   * - ``timestamp``
     - ``datetime64[ns]``
     - Observation epoch timestamp (ISO format)
   * - ``crs``
     - ``string``
     - Fixed Coordinate Reference System (``"EPSG:4326"``)
   * - ``lat``
     - ``float64``
     - Center latitude (:math:`21.1378^\circ\,\text{N}`)
   * - ``lon``
     - ``float64``
     - Center longitude (:math:`86.6874^\circ\,\text{E}`)
   * - ``s1_sar_vv_db``
     - ``float64``
     - Sentinel-1 C-Band VV backscatter (:math:`[-18, -8]\,\text{dB}`)
   * - ``s1_sar_vh_db``
     - ``float64``
     - Sentinel-1 C-Band VH backscatter (:math:`[-25, -14]\,\text{dB}`)
   * - ``sar_cross_ratio``
     - ``float64``
     - Cross-polarization ratio (:math:`\text{VH} / \text{VV}`)
   * - ``s2_cloud_cover_pct``
     - ``float64``
     - Sentinel-2 scene cloud cover percentage (:math:`[0, 90]\%`)
   * - ``s2_b03_green``
     - ``float64``
     - Sentinel-2 Band 3 Green surface reflectance (:math:`[0.05, 0.22]`)
   * - ``s2_b04_red``
     - ``float64``
     - Sentinel-2 Band 4 Red surface reflectance (:math:`[0.02, 0.18]`)
   * - ``s2_b08_nir``
     - ``float64``
     - Sentinel-2 Band 8 NIR surface reflectance (:math:`[0.20, 0.52]`)
   * - ``weather_temp_c``
     - ``float64``
     - Surface air temperature (:math:`[25, 36]^\circ\text{C}`)
   * - ``weather_precip_mm``
     - ``float64``
     - Daily monsoonal precipitation accumulation (:math:`\text{mm}`)
   * - ``dem_elevation_m``
     - ``float64``
     - Topographic elevation above sea level (:math:`18.5\,\text{m}`)
   * - ``ndvi``
     - ``float64``
     - Normalized Difference Vegetation Index (:math:`[-1.0, 1.0]`)
   * - ``ndwi``
     - ``float64``
     - Normalized Difference Water Index (:math:`[-1.0, 1.0]`)
   * - ``provenance``
     - ``string``
     - Simulation audit tag (``"SYNTHETIC_SIMULATION"``)

4.2 STAC 1.0.0 Asset Manifest Specification
-------------------------------------------
The serialized ``stac_catalog_item.json`` complies with the STAC v1.0.0 specification:

.. code-block:: json

   {
     "stac_version": "1.0.0",
     "id": "AETHER_S2_S1_COMBINED_20260815_BHADRAK",
     "type": "Feature",
     "geometry": {
       "type": "Polygon",
       "coordinates": [[[86.6374, 21.0878], [86.7374, 21.0878], [86.7374, 21.1878], [86.6374, 21.1878], [86.6374, 21.0878]]]
     },
     "bbox": [86.6374, 21.0878, 86.7374, 21.1878],
     "properties": {
       "datetime": "2026-08-15T05:30:00Z",
       "platform": "sentinel-2b / sentinel-1a",
       "proj:epsg": 4326,
       "eo:cloud_cover": 12.4,
       "aether:processing_level": "L2A_INFRARED_STAC_V1",
       "aether:provenance": "SYNTHETIC_SIMULATION"
     },
     "assets": {
       "s1_vv": { "href": "https://aether-storage/s1_20260815_vv.tif", "type": "image/tiff; application=geotiff; profile=cloud-optimized", "roles": ["data", "radar"] },
       "s1_vh": { "href": "https://aether-storage/s1_20260815_vh.tif", "type": "image/tiff; application=geotiff; profile=cloud-optimized", "roles": ["data", "radar"] },
       "s2_b04_red": { "href": "https://aether-storage/s2_20260815_b04.tif", "type": "image/tiff; application=geotiff; profile=cloud-optimized", "roles": ["data", "visual"] },
       "s2_b08_nir": { "href": "https://aether-storage/s2_20260815_b08.tif", "type": "image/tiff; application=geotiff; profile=cloud-optimized", "roles": ["data", "nir"] },
       "dem_aligned": { "href": "https://aether-storage/dem_bhadrak_10m.tif", "type": "image/tiff; application=geotiff; profile=cloud-optimized", "roles": ["data", "elevation"] }
     }
   }


5. Storage Artifacts & Visualization Telemetry
==============================================

The notebook executes a dedicated visualization pipeline producing 6 high-contrast publication figures
persisted in ``5_storage/notebook_results/notebook_01_ingestion/``:

1. **Plot 1 (`plot_01_s1_sar_dynamics.png`)**: Temporal dynamics of C-Band SAR backscatter (:math:`\sigma^0_{\text{VV}}` and :math:`\sigma^0_{\text{VH}}`) tracking surface dielectric variations under monsoon moisture changes.
2. **Plot 2 (`plot_02_s2_spectral_indices.png`)**: Time-series trajectory comparing photosynthetic biomass (:math:`\text{NDVI}`) against surface water saturation (:math:`\text{NDWI}`).
3. **Plot 3 (`plot_03_cloud_masking_sar_fallback.png`)**: Dual-axis plot demonstrating optical occlusion during monsoonal cloud events (>50%) and corresponding all-weather SAR penetration continuity.
4. **Plot 4 (`plot_04_atmospheric_forcing_precip_temp.png`)**: Meteorological forcing plots correlating precipitation pulse events with ambient temperature fluctuations.
5. **Plot 5 (`plot_05_spatial_rasters_ndvi_sar.png`)**: Side-by-side 2D spatial sub-grid heatmaps (:math:`100 \times 100` pixels) showing spatial distribution of NDVI and SAR VV backscatter.
6. **Plot 6 (`plot_06_resampled_dem_profile.png`)**: 2D topographic elevation heatmap and 1D cross-sectional terrain profile demonstrating smooth bilinear interpolation.


6. Verification & Test Architecture
====================================

The subsystem integrity is formally validated via ``tests/test_notebook_01_verification.py``, executing 6
rigorous test cases:
- ``test_01_no_python_scripts_in_notebook_dir``: Enforces sandbox hygiene; verifies zero forbidden `.py` scripts exist in `1_notebooks_sandbox/`.
- ``test_02_notebook_cell_structure_and_markdown_rules``: Enforces interleaving; verifies every code cell is immediately preceded by markdown.
- ``test_03_all_code_cells_executed_with_zero_errors``: Verifies execution count > 0 and zero execution exceptions across all 14 code cells.
- ``test_04_penultimate_and_ultimate_markdown_cells``: Asserts presence of Executive Summary and Intellectual Property copyright notice.
- ``test_05_storage_artifacts_and_plots_persisted``: Asserts existence and non-zero byte size of all 6 plot PNGs, `stac_telemetry_raw.csv`, and `stac_catalog_item.json` in both `5_storage/` and `data/raw/`.
- ``test_06_data_and_schema_integrity``: Asserts standard column names, spectral index bounds in :math:`[-1.0, 1.0]`, provenance tag, and STAC 1.0.0 compliance.

All 6 test cases passed successfully in 0.45 seconds under `mridansh_env`.


7. Unfiltered Technical Debt & Defect Register
===============================================

.. list-table:: Notebook 01 Defect Register
   :widths: 15 20 35 30
   :header-rows: 1

   * - Defect ID
     - Location
     - Description & Root Cause
     - Remediation Status
   * - **D-NB01-001**
     - Cell 7
     - Absence of epsilon regularization (:math:`\varepsilon = 10^{-8}`) in NDVI/NDWI denominators.
     - Documented; mitigated in production pipeline (`spectral_indices.py`).
   * - **D-NB01-002**
     - Cell 21
     - Hardcoded zoom ratio :math:`100/33` ignores true geographic geotransform origin shifts.
     - Documented; routed through GDAL `RasterDataProcessor` in production pipeline.
   * - **D-NB01-003**
     - Cell 27
     - STAC asset HREFs point to synthetic placeholder URLs rather than live object storage.
     - Bounded under synthetic simulation disclosure.
