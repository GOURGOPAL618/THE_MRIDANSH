=====================================================================
THE MRIDANSH (AETHER-MRID1607X) - Notebook 01: Data Ingestion
=====================================================================

:Project: THE MRIDANSH - Unified Soil State Estimation System
:Engine: AETHER-MRID1607X
:Notebook: ``01-data-ingestion.ipynb``
:Sprint phase: Day 1-2 of the 18-Day Scientific Validation Sprint
:Division: RS-SDA (Remote Sensing & Spatial Data Analytics), JCC Campus 2 / JCC Headquarter
:Author / Maintainer: Gourgopal Mohapatra
:Copyright: (c) 2026 Gourgopal Mohapatra. All Rights Reserved.
:Document status: Draft for review

.. contents:: Table of Contents
   :depth: 3
   :local:

1. Purpose and Scope
====================

1.1 Project context
-------------------

THE MRIDANSH is a physics-guided, AI-driven Unified Soil State Estimation
System. It fuses optical imagery, Synthetic Aperture Radar (SAR), Digital
Elevation Models (DEM), weather observations and temporal history into one
framework, and produces a **Unified Soil State Vector** with associated
confidence and uncertainty. Downstream domain translators (agriculture,
civil engineering, and external systems such as MARGAVEDHA) consume that
vector. The core is intentionally application-agnostic.

1.2 Role of this notebook
-------------------------

Notebook 01 is the first stage of the data pipeline. It is responsible for:

* defining the study area and temporal window;
* ingesting (currently *simulating*) multi-sensor telemetry;
* auditing the data for integrity (CRS, nulls, spectral bounds, cloud cover);
* visualising temporal and spatial behaviour of the inputs;
* aligning a coarse DEM to the fine optical/SAR grid;
* building a STAC 1.0.0 style metadata item;
* exporting results to ``data/raw/``.

It does **not** perform state estimation, EnKF assimilation, or PINN training.
Those belong to later notebooks.

2. Study Area and Parameters
============================

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Parameter
     - Value
     - Notes
   * - Target latitude
     - 21.1378 N
     - ``TARGET_LAT``
   * - Target longitude
     - 86.6874 E
     - ``TARGET_LON``
   * - Buffer
     - 0.05 degrees
     - Roughly 5 km each side, giving about an 11 km wide box
   * - Bounding box [W, S, E, N]
     - [86.6374, 21.0878, 86.7374, 21.1878]
     - CRS EPSG:4326
   * - Temporal window
     - 2026-08-01 to 2026-09-07
     - Monsoon period, 35 samples
   * - Spatial sub-grid
     - 100 x 100 pixels
     - Described as 10 m pixels (about 1 km x 1 km)

.. note::
   The bounding box (about 11 km) and the raster sub-grid (about 1 km) are
   different extents. The notebook text refers to both as the area of
   interest; this should be reconciled (see Section 9).

3. Mathematical Foundations
===========================

SAR backscatter conversion::

    sigma0_dB = 10 * log10(sigma0_linear)

Normalized Difference Vegetation Index::

    NDVI = (NIR - RED) / (NIR + RED) = (B08 - B04) / (B08 + B04)

Normalized Difference Water Index::

    NDWI = (GREEN - NIR) / (GREEN + NIR) = (B03 - B08) / (B03 + B08)

Spatial resampling (bilinear)::

    I_resampled(x, y) = sum_i sum_j w_ij * I_raw(x_i, y_j)

4. Notebook Structure
=====================

.. list-table::
   :header-rows: 1
   :widths: 10 35 55

   * - Step
     - Title
     - Description
   * - 0
     - Environment setup
     - Imports (numpy, pandas, geopandas, matplotlib), dark telemetry theme.
   * - 1
     - Bounding box and window
     - Computes ``BBOX`` from lat/lon and buffer; sets start/end dates.
   * - 2
     - Multi-sensor ingestion
     - ``fetch_aerospace_stac_telementary()`` builds a DataFrame of 35 frames
       (S1 VV/VH, S2 B03/B04/B08, cloud cover, DEM, temperature, precipitation)
       and derives NDVI and NDWI.
   * - 3
     - Integrity audit
     - Assertions for CRS uniformity, zero nulls, spectral bounds; reports the
       fraction of days with cloud cover above 50 %.
   * - Plot 1
     - SAR dual-pol dynamics
     - VV and VH time series.
   * - Plot 2
     - Spectral indices
     - NDVI and NDWI time series with zero baseline.
   * - Plot 3
     - Cloud mask vs SAR
     - Cloud-cover bars with 50 % threshold overlaid with SAR VV.
   * - Plot 4
     - Atmospheric forcing
     - Precipitation (bars) and temperature (line).
   * - 4
     - Raster generation and resampling
     - 100x100 RED/NIR/SAR rasters, NDVI raster, 33x33 DEM upsampled to
       100x100 using ``scipy.ndimage.zoom(order=1)``.
   * - Plot 5
     - Spatial heatmaps
     - NDVI and SAR VV sub-grid images.
   * - Plot 6
     - Resampled DEM
     - Terrain colour map of the aligned DEM.
   * - 5
     - STAC metadata
     - Builds a STAC 1.0.0 style Feature dictionary and checks mandatory keys.
   * - 6
     - Data lake export
     - Writes ``stac_telementary_raw.csv`` and ``stac_catalog_item.json`` to
       ``../data/raw/``.

5. Data Products
================

5.1 Telemetry table
-------------------

Columns: ``timestamp``, ``crs``, ``lat``, ``lon``, ``s1_vv_db``, ``s1_vh_db``,
``s2_cloud_cover_pct``, ``s2_b03_green``, ``s2_b04_red``, ``s2_b08_nir``,
``dem_elevation_m``, ``weayher_temp_c`` (sic), ``weather_precip_mm``,
``ndvi``, ``ndwi``.

5.2 Output files
----------------

* ``data/raw/stac_telementary_raw.csv`` - the telemetry table above.
* ``data/raw/stac_catalog_item.json`` - STAC style item metadata.

.. warning::
   The metadata references GeoTIFF assets (``s1_vv_20260815.tif``,
   ``s2_ndvi_20260815.tif``, ``dem_aligned_20260815.tif``) that the notebook
   does **not** actually write. Raster arrays exist only in memory.

6. Data Provenance - Important Limitation
=========================================

All data in this notebook is **synthetic**. ``fetch_aerospace_stac_telementary``
draws values from ``numpy.random`` with seed 42, and the spatial rasters use
seed 101. No STAC API, Sentinel archive, DEM service or weather feed is
queried. Consequently:

* the "45.7 % cloudy days" result is a property of the random generator
  (uniform 0-90 % cloud cover), not evidence about the Odisha monsoon;
* the zero-null and spectral-bound checks pass by construction;
* any scientific conclusion drawn from this notebook's numbers is invalid
  until real data replaces the simulator.

7. Verification Performed in the Notebook
=========================================

.. list-table::
   :header-rows: 1
   :widths: 5 40 25 30

   * - ID
     - Check
     - Method
     - Result in notebook
   * - V1
     - Single CRS EPSG:4326
     - ``assert``
     - Pass
   * - V2
     - No null values
     - ``assert``
     - Pass
   * - V3
     - NDVI and NDWI within [-1, 1]
     - ``assert``
     - Pass
   * - V4
     - Cloud-cover ratio reported
     - Print
     - 45.7 %
   * - V5
     - Resampled DEM shape equals (100, 100)
     - ``assert``
     - Pass
   * - V6
     - STAC mandatory keys present
     - ``assert``
     - Pass (note defect D3)

8. Reproducibility
==================

* Python 3 with numpy, pandas, geopandas, matplotlib, scipy.
* Fixed seeds: 42 (telemetry), 101 (rasters).
* Output path is relative: ``../data/raw/``.
* Pinned library versions are **not** recorded; they should be added.

9. Known Defects and Recommended Corrections
============================================

.. list-table::
   :header-rows: 1
   :widths: 6 44 50

   * - ID
     - Defect
     - Recommended fix
   * - D1
     - Data is simulated, not ingested from STAC.
     - Implement real queries (e.g. pystac-client with Sentinel-1 RTC,
       Sentinel-2 L2A, Copernicus DEM, a weather reanalysis).
   * - D2
     - Typos in identifiers: ``weayher_temp_c``, ``telementary``,
       ``processing_lebel``, "Telementary" in comments.
     - Rename; Plot 4 currently falls back to *random* temperature because it
       looks for ``weather_temp_c`` and does not find the misspelt column.
   * - D3
     - STAC item uses key ``"assert"`` instead of ``"assets"``; the validation
       assert therefore checks the wrong key.
     - Use ``assets``; validate with the ``pystac`` or ``stac-validator``
       library.
   * - D4
     - Matplotlib ``axes.edgecolor`` is set to ``"00FFCC"`` without ``#``.
     - Use ``"#00FFCC"``.
   * - D5
     - Summary cell names ``stac_telemetry_raw.csv`` but the code writes
       ``stac_telementary_raw.csv``.
     - Make names consistent.
   * - D6
     - ``geopandas``, ``sys`` imported but unused; ``fetch_*`` ignores its
       ``bbox`` argument and uses globals.
     - Remove or use; pass parameters explicitly.
   * - D7
     - AOI size inconsistency (about 11 km box vs 1 km grid).
     - Define one AOI and derive the raster grid from it with an affine
       transform.
   * - D8
     - Rasters have no georeferencing; STAC assets are not written.
     - Write Cloud Optimized GeoTIFFs with ``rasterio`` and an affine
       transform.
   * - D9
     - Raw S2 reflectances can make NDVI = 0/0 only in degenerate cases but
       no cloud-mask or SCL-based masking is applied to optical bands.
     - Apply SCL/QA masks before computing indices.
   * - D10
     - No SAR preprocessing described (speckle filtering, incidence-angle
       normalisation, orbit/pass handling).
     - Document and implement in Notebook 02.

10. Interfaces to Downstream Notebooks
======================================

* Input contract for Notebook 02 (preprocessing): CSV in ``data/raw/`` with
  the schema in Section 5.1 (after typo fixes) and a valid STAC item.
* The Unified Soil State Vector is **not** produced here.

11. Licensing and Notice
========================

This notebook and its documentation are proprietary intellectual property of
Gourgopal Mohapatra (JCC Headquarter / JCC Campus 2, RS-SDA Division).
Unauthorised copying, redistribution or commercial use in whole or in part is
prohibited without prior written authorisation.
