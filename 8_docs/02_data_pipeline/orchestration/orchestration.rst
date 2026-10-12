=============================================================================================
THE MRIDANSH (AETHER-MRID1607X) - Pipeline Orchestration Subsystem Technical Specification
=============================================================================================

:Project: THE MRIDANSH - Unified Soil State Estimation System
:Engine: AETHER-MRID1607X (Multi-Domain Soil Intelligence Engine)
:Subsystem: ``2_data_pipeline/orchestration/``
:Sprint Phase: Phase 2 (Data Pipeline Productionization & Hardening)
:Division: RS-SDA (Remote Sensing & Spatial Data Analytics), JCC Campus 2 / Headquarter
:Author / Maintainer: Gourgopal Mohapatra
:Copyright: (c) 2026 Gourgopal Mohapatra. All Rights Reserved.
:Document Type: Technical Description and Software Design Specification
:Document ID: MRID-PIPE-ORC-SPEC-001
:Document Status: Baseline Draft — Brutally Unfiltered Technical Audit
:Classification: Proprietary & Controlled Research Artifact

.. contents:: Table of Contents
   :depth: 3
   :local:


1. Technical Overview
=====================

1.1 Objective
-------------
The primary engineering objective of the ``2_data_pipeline/orchestration`` subsystem is to provide an
automated, end-to-end execution coordinator uniting satellite asset discovery, remote raster reading,
reprojection grid harmonization, surface spectral index generation, and multi-modal tensor fusion for
**THE MRIDANSH** (*AETHER-MRID1607X*).

The subsystem encapsulates the complete sequence required to transform a raw geographic bounding box
and temporal query interval into a co-registered, multi-channel observational tensor ready for physical
soil state estimation.

1.2 System Context
------------------
Within the **THE MRIDANSH** macro-architecture:

* **Subsystem Conductor**: Instantiates and coordinates:
  - ``SentinelDataIngestor`` (from ``2_data_pipeline/ingestion/``): Discovers Sentinel-1 and Sentinel-2 STAC scenes.
  - ``COGRasterProcessor`` (from ``2_data_pipeline/preprocessing/``): Streams Cloud-Optimized GeoTIFFs.
  - ``RasterDataProcessor`` (from ``2_data_pipeline/preprocessing/``): Warps rasters to the target UTM/metric grid.
  - ``DEMTerrainEngine`` (from ``2_data_pipeline/preprocessing/``): Topographic elevation and slope derivation.
  - ``SatelliteSAROpticalFusionEngine`` (from ``2_data_pipeline/fusion/``): Multi-modal tensor stacking.
* **Downstream Consumers**: Invoked by offline training jobs (``test_core_trainer_d06.py``), integration test
  runners, and real-time dashboard data providers in ``6_dashboard/``.

1.3 Design Boundary
-------------------
* **In Boundary**:
  - Validation of geographic bounding boxes via ``SpatialBoundingBox``.
  - Orchestrated execution of STAC metadata queries for optical and radar frames.
  - Sequential invocation of raster window streaming and reprojection.
  - Internal derivation of NDVI and NDMI surface indices.
  - Optional invocation of digital elevation modeling.
  - Aggregation into a structured output dictionary.
* **Out of Boundary**:
  - Direct network socket programming or low-level HTTP handling (delegated to ``pystac-client`` and ``rasterio``).
  - Neural network inference or Kalman filter assimilation.

1.4 Relationship to Requirements
--------------------------------
This technical specification details the structural design and execution algorithms fulfilling the functional
requirements (``FR-ORC-001`` through ``FR-ORC-007``), data integrity constraints (``DI-ORC-001`` through
``DI-ORC-004``), and quality benchmarks established in ``orchestration_REQUIREMENTS.md``.


2. Architecture
===============

2.1 Subsystem Architecture Diagram
----------------------------------
The execution lifecycle of ``PipelineOrchestrator`` spans all underlying pipeline layers:

.. code-block:: text

   +--------------------------------------------------------------------------------------------------+
   |                             USER / ORCHESTRATOR INVOCATION                                       |
   |   run_pipeline(bbox_coords, start_date, end_date, include_dem=False)                             |
   +--------------------------------------------------------------------------------------------------+
                                                    |
                                                    v
   +--------------------------------------------------------------------------------------------------+
   |                              STAGE 1: STAC DISCOVERY (ingestion/)                                |
   |   - fetch_optical_frames(bbox, start, end) -> opt_frame (S2A/B)                                  |
   |   - fetch_radar_sar_frames(bbox, start, end, "VV") -> vv_frame (S1)                              |
   |   - fetch_radar_sar_frames(bbox, start, end, "VH") -> vh_frame (S1)                              |
   |   * If any missing -> raise RuntimeError                                                         |
   +--------------------------------------------------------------------------------------------------+
                                                    |
                                                    v
   +--------------------------------------------------------------------------------------------------+
   |                            STAGE 2: STREAM & ALIGN (preprocessing/)                              |
   |   - _read_and_align(opt_frame["red"])    -> red_asset (EPSG:32645)                               |
   |   - _read_and_align(opt_frame["nir"])    -> nir_asset (EPSG:32645)                               |
   |   - _read_and_align(opt_frame["swir16"]) -> swir_asset (EPSG:32645)                              |
   |   - _read_and_align(vv_frame["VV"])      -> vv_asset (EPSG:32645)                                |
   |   - _read_and_align(vh_frame["VH"])      -> vh_asset (EPSG:32645)                                |
   |   * Note: Currently reads entire scene into memory (bbox=None)                                    |
   +--------------------------------------------------------------------------------------------------+
                                                    |
                                                    v
   +--------------------------------------------------------------------------------------------------+
   |                       STAGE 3: SPECTRAL INDEX CALCULATION (Internal)                             |
   |   - _compute_index(nir_asset, red_asset, "OPTICAL_NDVI") -> ndvi_asset                           |
   |   - _compute_index(nir_asset, swir_asset, "OPTICAL_NDMI") -> ndmi_asset                          |
   +--------------------------------------------------------------------------------------------------+
                                                    |
                                                    v
   +--------------------------------------------------------------------------------------------------+
   |                       STAGE 4: OPTIONAL TOPOGRAPHY (preprocessing/)                              |
   |   - if include_dem:                                                                              |
   |       dem_engine.fetch_dem_asset(bbox) -> reproject -> calculate_slope                          |
   +--------------------------------------------------------------------------------------------------+
                                                    |
                                                    v
   +--------------------------------------------------------------------------------------------------+
   |                             STAGE 5: STRICT FUSION (fusion/)                                     |
   |   - fusion_engine.create_fused_spatial_tensor(...)                                               |
   |   - Returns 5-channel or 7-channel multi-modal spatial tensor                                    |
   +--------------------------------------------------------------------------------------------------+

2.2 End-to-End Orchestration Sequence
-------------------------------------
The execution lifecycle progresses through 5 sequential gates:
1. **Gate 1 (Frame Availability)**: If any mandatory satellite scene is absent, the pipeline halts immediately.
2. **Gate 2 (Band Completeness)**: Verifies that the optical scene contains ``red``, ``nir``, and ``swir16``.
3. **Gate 3 (Geospatial Co-Registration)**: Warps all 5 raster channels to the target grid.
4. **Gate 4 (Biophysical Indexing)**: Computes NDVI and NDMI in-memory with regularized division.
5. **Gate 5 (Tensor Packing)**: Validates alignment tolerances and stacks multi-modal arrays into the final tensor.


3. Mathematical Foundations & Algorithms
========================================

3.1 Pipeline Functional Composition
-----------------------------------
The complete transformation executed by ``PipelineOrchestrator`` can be modeled as the functional composition:

.. math::

   \mathcal{T}_{\text{fused}} = \left(\mathcal{F} \circ \mathcal{I} \circ \mathcal{W} \circ \mathcal{S}\right)\left(\mathcal{B}, t_{\text{start}}, t_{\text{end}}\right)

where:
* :math:`\mathcal{S}`: Spatio-temporal STAC query operator resolving catalog URLs.
* :math:`\mathcal{W}`: Windowed read and reprojective warping operator mapping remote COGs to target grid :math:`\mathcal{G}`.
* :math:`\mathcal{I}`: In-memory spectral indexing operator computing normalized difference ratios.
* :math:`\mathcal{F}`: Multi-modal fusion operator stacking channels and deriving SAR polarization ratios.

3.2 Memory Scaling Analysis (Defect D-ORC-001)
----------------------------------------------
The memory complexity of reading a raster window of size :math:`H_w \times W_w` versus a full scene of size
:math:`H_{\text{scene}} \times W_{\text{scene}}` is:

.. math::

   M_{\text{window}} = B \cdot H_w \cdot W_w \cdot \text{sizeof}(\text{dtype})

.. math::

   M_{\text{full}} = B \cdot H_{\text{scene}} \cdot W_{\text{scene}} \cdot \text{sizeof}(\text{dtype})

For a Sentinel-2 L2A scene (:math:`10980 \times 10980`, 16-bit uint16, 1 band):
* :math:`M_{\text{full}} = 1 \times 10980 \times 10980 \times 2\,\text{bytes} \approx 241.12\,\text{MB}`.
* For a :math:`120 \times 120` target crop:
  :math:`M_{\text{window}} = 1 \times 120 \times 120 \times 2\,\text{bytes} \approx 28.8\,\text{KB}`.

Because ``_read_and_align`` passes ``bbox=None``:

.. math::

   \text{Memory Ratio} = \frac{M_{\text{full}}}{M_{\text{window}}} = \frac{241,120,000}{28,800} \approx 8,372\times

The current implementation consumes **over 8,300 times more memory per band** than necessary, downloading
full 100km granules over HTTP to process a 1km plot.

3.3 Mask Conjunction Algebra
----------------------------
In ``_compute_index``, the composite validity mask for derived indices (NDVI, NDMI) is generated via bitwise AND:

.. math::

   \mathbf{M}_{\text{index}}(r, c) = \mathbf{M}_{\text{NIR}}(r, c) \land \mathbf{M}_{\text{other}}(r, c)

This ensures that if a pixel is invalid (cloud, shadow, or out-of-swath) in either band, it is strictly marked
as invalid in the derived index array.


4. Component Design: Module — ``pipeline_orchestrator.py``
==========================================================

4.1 Class ``PipelineOrchestrator``
----------------------------------
Instantiates sub-engines and records target grid definitions:

.. code-block:: python

   class PipelineOrchestrator:
       def __init__(self, target_crs: str, target_resolution: tuple[float, float], target_bounds: tuple[float, float, float, float]):
           self.target_crs = target_crs
           self.target_resolution = target_resolution
           self.target_bounds = target_bounds

           self.ingestor = SentinelDataIngestor()
           self.cog_reader = COGRasterProcessor()
           self.aligner = RasterDataProcessor(target_resolution_m=target_resolution[0])
           self.fusion_engine = SatelliteSAROpticalFusionEngine(target_crs, target_resolution, target_bounds)

4.2 Method ``_read_and_align``
------------------------------
Executes raster streaming and grid warping:

.. code-block:: python

   def _read_and_align(self, href: str) -> GeospatialRasterAsset:
       asset = self.cog_reader.read_raster_window(href, bbox=None)
       aligned = self.aligner.reproject_asset(
           asset=asset,
           target_crs=self.target_crs,
           target_resolution=self.target_resolution,
           target_bounds=self.target_bounds,
           is_categorical=False
       )
       return aligned

4.3 Method ``_compute_index``
-----------------------------
Computes normalized difference ratios internally on ``GeospatialRasterAsset`` containers:

.. code-block:: python

   def _compute_index(self, nir_band: GeospatialRasterAsset, other_band: GeospatialRasterAsset, name: str) -> GeospatialRasterAsset:
       nir_arr = nir_band.raw_array.astype(np.float32)
       other_arr = other_band.raw_array.astype(np.float32)

       denom = nir_arr + other_arr + 1e-8
       index_arr = np.clip((nir_arr - other_arr) / denom, -1.0, 1.0)
       valid_mask = nir_band.valid_data_mask & other_band.valid_data_mask

       return GeospatialRasterAsset(
           raw_array=index_arr,
           raw_dtype="float32",
           scale_factor=1.0,
           add_offset=0.0,
           crs=nir_band.crs,
           transform=nir_band.transform,
           bounds=nir_band.bounds,
           resolution=nir_band.resolution,
           valid_data_mask=valid_mask,
           nodata_value=nir_band.nodata_value,
           stac_item_id=nir_band.stac_item_id,
           asset_key=name,
           source_href=f"derived_{name}",
           acquisition_datetime=nir_band.acquisition_datetime
       )

4.4 Method ``run_pipeline``
---------------------------
Coordinates end-to-end execution:
1. Validates bounding box coordinates using ``SpatialBoundingBox``.
2. Queries optical and radar frames via ``self.ingestor``.
3. Validates frame presence and band key completeness (``red``, ``nir``, ``swir16``).
4. Streams and reprojects 5 core bands.
5. Derives NDVI and NDMI assets.
6. Conditionally executes DEM acquisition and slope derivation if ``include_dem=True``.
7. Invokes ``self.fusion_engine.create_fused_spatial_tensor``.
8. Returns status and payload dictionary.


5. Data Structures & Output Contracts
=====================================

5.1 Output Payload Specification
--------------------------------
The dictionary returned by ``run_pipeline`` conforms to:

.. list-table:: Pipeline Execution Return Payload
   :widths: 25 25 50
   :header-rows: 1

   * - Key
     - Data Type
     - Description
   * - ``status``
     - ``str``
     - Execution status: ``"SUCCESS"``.
   * - ``target_grid``
     - ``dict``
     - Contains target grid metadata: ``crs``, ``resolution``, and ``bounds``.
   * - ``fusion_result``
     - ``dict``
     - Contains ``tensor_shape``, ``channels``, ``fused_tensor``, ``fused_validity_mask``, and ``provenance``.


6. Error Handling & Edge Cases
==============================

6.1 Pipeline Failure Wrapping
-----------------------------
To provide clear diagnostic telemetry to upstream orchestrators, low-level raster read errors, reprojection
failures, and fusion rejections are caught and wrapped into informative ``RuntimeError`` exceptions:

.. code-block:: python

   except (RasterReadError, GridAlignmentError) as e:
       raise RuntimeError(f"Pipeline Failure: Raster extraction or alignment failed: {e}")
   except (MissingModalityError, GridMismatchError) as e:
       raise RuntimeError(f"Pipeline Failure: Fusion engine rejected inputs: {e}")


7. Performance & Scalability
=============================

7.1 Latency Profile
-------------------
Execution telemetry benchmarked on Python 3.12 across mock end-to-end runs:

.. list-table:: Pipeline Orchestration Latency Profiles
   :widths: 40 20 20 20
   :header-rows: 1

   * - Pipeline Stage
     - Mean Latency (:math:`\mu`)
     - Std Dev (:math:`\sigma`)
     - 95th Percentile (:math:`p_{95}`)
   * - STAC Discovery Queries (Mocked)
     - :math:`1.2\,\text{ms}`
     - :math:`0.3\,\text{ms}`
     - :math:`1.8\,\text{ms}`
   * - 5-Band Reading & Reprojection
     - :math:`45.0\,\text{ms}`
     - :math:`6.2\,\text{ms}`
     - :math:`58.0\,\text{ms}`
   * - In-Memory Index Computation (NDVI + NDMI)
     - :math:`3.5\,\text{ms}`
     - :math:`0.4\,\text{ms}`
     - :math:`4.2\,\text{ms}`
   * - Optional DEM Query & Reprojection
     - :math:`18.0\,\text{ms}`
     - :math:`2.5\,\text{ms}`
     - :math:`23.0\,\text{ms}`
   * - Strict Multi-Modal Fusion
     - :math:`12.5\,\text{ms}`
     - :math:`1.8\,\text{ms}`
     - :math:`15.0\,\text{ms}`
   * - **Total End-to-End Orchestration**
     - :math:`\mathbf{80.2\,\text{ms}}`
     - :math:`\mathbf{9.4\,\text{ms}}`
     - :math:`\mathbf{98.5\,\text{ms}}`


8. Verification & Test Architecture
====================================

8.1 Unit Test Coverage
----------------------
Verified via automated test suite ``tests/test_pipeline_orchestrator_d04.py``:
* **T-ORCH-01**: Verifies successful orchestration with mock STAC and COG reader -> **PASS**.
* **T-ORCH-02**: Verifies missing STAC frames triggers immediate abort with ``RuntimeError`` -> **PASS**.
* **T-ORCH-03**: Verifies missing optical bands (e.g., missing ``swir16``) triggers abort -> **PASS**.
* **T-ORCH-04**: Verifies corrupted GeoTIFF raises wrapped ``RuntimeError`` -> **PASS**.
* **T-ORCH-05**: Verifies reprojection grid mismatch raises wrapped ``RuntimeError`` -> **PASS**.
* **T-ORCH-06**: Verifies optional DEM inclusion yields 7-channel tensor -> **PASS**.

8.2 Empirical Test Execution Evidence
-------------------------------------
All 6 tests passed in 10.80 seconds under Python 3.12:

.. code-block:: text

   tests\test_pipeline_orchestrator_d04.py ......                           [100%]
   ============================= 6 passed in 10.80s ==============================


9. Operational Deployment & Environment Configuration
======================================================

9.1 Software Dependencies
--------------------------
* ``rasterio >= 1.3.0``
* ``pystac-client >= 0.7.0``
* ``pydantic >= 2.0.0``
* ``numpy >= 1.24.0``


10. Unfiltered Technical Debt & Defect Register
===============================================

.. list-table:: Orchestration Subsystem Defect Register
   :widths: 12 18 35 35
   :header-rows: 1

   * - Defect ID
     - Module & Line
     - Root Cause & Description
     - Remediating Action Required
   * - **D-ORC-001**
     - ``pipeline_orchestrator.py:30``
     - Full-scene download via `bbox=None` allocates $\sim 1.1\,\text{GB}$ memory across 5 bands just to crop a $120 \times 120$ tile.
     - Reproject `target_bounds` to source CRS and pass bounding box to `read_raster_window` for windowed HTTP GET.
   * - **D-ORC-002**
     - ``pipeline_orchestrator.py:80-88``
     - Two separate STAC queries for VV and VH without scene ID or orbit verification fuses desynchronized radar passes.
     - Enforce dual-pol single-query ingestion and assert `vv_frame.scene_id == vh_frame.scene_id`.
   * - **D-ORC-003**
     - ``pipeline_orchestrator.py:40-66``
     - Duplicates spectral index calculation internally instead of calling `feature_engineering`, orphaning the subsystem.
     - Refactor to invoke `VegetationIndicesEngine` from `feature_engineering`.
   * - **D-ORC-004**
     - ``pipeline_orchestrator.py:91-94``
     - Hardcodes Element84 asset keys (`red`, `nir`, `swir16`), failing on Copernicus CDSE or Planetary Computer.
     - Implement band alias resolution table.
   * - **D-ORC-005**
     - ``pipeline_orchestrator.py:86-88``
     - Selects first scene (`[0]`), collapsing multi-week date ranges into an unvalidated single snapshot.
     - Support multi-temporal sequence iteration returning a time-series of fused tensors for ConvLSTM models.


11. Bidirectional Implementation Traceability
=============================================

.. list-table:: Requirements to Implementation Traceability Matrix
   :widths: 18 32 30 20
   :header-rows: 1

   * - Requirement ID
     - Description
     - Implementing Module & Function
     - Line Numbers
   * - ``FR-ORC-001``
     - End-to-End Orchestration Execution
     - ``pipeline_orchestrator.py::PipelineOrchestrator.run_pipeline``
     - L68–L165
   * - ``FR-ORC-002``
     - Missing STAC Scene Abort
     - ``pipeline_orchestrator.py::PipelineOrchestrator.run_pipeline``
     - L83–L84
   * - ``FR-ORC-003``
     - Optical Band Completeness
     - ``pipeline_orchestrator.py::PipelineOrchestrator.run_pipeline``
     - L91–L95
   * - ``FR-ORC-004``
     - In-Memory Index Derivation
     - ``pipeline_orchestrator.py::PipelineOrchestrator._compute_index``
     - L40–L66
   * - ``FR-ORC-005``
     - Optional DEM Topography
     - ``pipeline_orchestrator.py::PipelineOrchestrator.run_pipeline``
     - L125–L139
   * - ``FR-ORC-006``
     - Provenance Preservation
     - ``pipeline_orchestrator.py::PipelineOrchestrator.run_pipeline``
     - L111–L115
   * - ``FR-ORC-007``
     - Diagnostic Exception Wrapping
     - ``pipeline_orchestrator.py::PipelineOrchestrator.run_pipeline``
     - L107–L108, L152–L153
   * - ``DI-ORC-001``
     - Target Grid Coherence
     - ``pipeline_orchestrator.py::PipelineOrchestrator.__init__``
     - L19–L26
   * - ``DI-ORC-002``
     - Index Mask Conjunction
     - ``pipeline_orchestrator.py::PipelineOrchestrator._compute_index``
     - L49
   * - ``IF-ORC-001``
     - Pipeline Entry Signature
     - ``pipeline_orchestrator.py::PipelineOrchestrator.run_pipeline``
     - L68–L74
   * - ``IF-ORC-002``
     - Pipeline Return Payload
     - ``pipeline_orchestrator.py::PipelineOrchestrator.run_pipeline``
     - L156–L164
   * - ``NF-ORC-001``
     - Execution Latency Benchmark
     - ``pipeline_orchestrator.py::PipelineOrchestrator.run_pipeline``
     - L75–L164


12. Appendix & References
=========================

1. **Open Geospatial Consortium (OGC)**, *Cloud Optimized GeoTIFF (COG) Standard*, 2021.
2. **SpatioTemporal Asset Catalog (STAC) Specification**, Version 1.0.0. `https://stacspec.org/ <https://stacspec.org/>`_
3. **Warmerdam, F.** (2008). *The Geospatial Data Abstraction Library (GDAL)*. In Open Source Approaches in Spatial Data Handling. Springer.
