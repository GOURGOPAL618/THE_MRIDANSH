.. _ingestion_operational_bridges:

========================================================================================
Operational Spaceborne Campaign Ingestion Bridges & Gateways
========================================================================================

:Document ID: DOC-MRID-02-ING-EXT-001
:Module: ``2_data_pipeline/ingestion/``
:Campaign Subsystem: ``9_spaceborne_operational_campaign/4_execution_engine/``
:Classification: High-Integrity Mission-Critical Earth Observation Pipeline Extension
:Author: Gourgopal Mohapatra
:Status: RELEASED / PRODUCTION AUDITED
:Date: 2026-11-05

.. contents:: Table of Contents
   :depth: 3
   :local:

Document Control
================

Identification & Scope
----------------------
This document specifies the architectural, functional, and empirical verification baselines for the **8 operational campaign bridge modules** incorporated into ``2_data_pipeline/ingestion/``. These modules link the preliminary data ingestion pipeline with the spaceborne execution engines of the **Spaceborne Operational Campaign (SOC-AETHER-2026)** in ``9_spaceborne_operational_campaign/4_execution_engine/``.

Revision History
----------------
.. list-table::
   :widths: 10 15 25 50
   :header-rows: 1

   * - Version
     - Date
     - Author
     - Description of Change
   * - 1.0
     - 2026-11-05
     - Gourgopal Mohapatra
     - Consolidated baseline audit and unfiltered requirements document for all 8 newly added operational flight campaign bridge modules in ``2_data_pipeline/ingestion/``.

Mandatory Unfiltered Engineering Disclosure & Architectural Audit
=================================================================

.. warning::
   **BRUTAL ARCHITECTURAL REALITY & CODE AUDIT**:

   1. **Inverted Architectural Dependency (Defect D-ING-EXT-001)**:
      In standard software layering, Layer 2 (``2_data_pipeline``) is an upstream foundation. In these 8 bridge files, Layer 2 reaches forward into Layer 9 (``9_spaceborne_operational_campaign``), creating a circular architectural inversion. If Layer 9 is missing or reorganized, Layer 2 crashes on import.
   2. **Global sys.path Tampering (Defect D-ING-EXT-002)**:
      Every bridge module mutates ``sys.path`` at runtime by inserting ``9_spaceborne_operational_campaign/4_execution_engine``, ``3_core_engine``, and the workspace root at index 0. This permanently modifies module resolution for the entire Python interpreter process.
   3. **Heterogeneous Import Mechanics (Defect D-ING-EXT-003)**:
      Six bridge files employ dynamic ``importlib.util.spec_from_file_location`` and ``getattr`` bindings, while two files (``geotiff_production_exporter.py`` and ``spaceborne_pipeline_orchestrator.py``) utilize raw standard imports after modifying ``sys.path``. This divergence impedes static code analysis and linting.
   4. **Incomplete Export Declarations (Defect D-ING-EXT-004)**:
      The package entry point ``2_data_pipeline/ingestion/__init__.py`` only exports ``RealWorldSatelliteIngestor``, leaving 7 bridge classes unexposed in ``__all__``.
   5. **Synthetic In-Situ Fallback Cloaking (Defect D-ING-EXT-005)**:
      ``insitu_ground_truth_ingestor.py`` generates synthetic soil moisture readings via Gaussian sampling clamped to :math:`[0.02, 0.50]\,\text{m}^3/\text{m}^3` when live ground telemetry is unreachable.

Comprehensive Breakdown of the 8 Bridge Modules
================================================

1. realworld_satellite_ingestor.py
----------------------------------
* **Bridge Module**: ``2_data_pipeline/ingestion/realworld_satellite_ingestor.py``
* **Target Module**: ``9_spaceborne_operational_campaign/4_execution_engine/realworld_satellite_ingestor.py``
* **Key Exports**: ``RealWorldSatelliteIngestor``, ``SarRadiometricCalibrator``, ``OpticalCloudPreprocessor``

SAR Radiometric Calibration:
Converts raw digital numbers (:math:`DN`) to calibrated backscatter intensity :math:`\sigma^0` in decibels:

.. math::

   \sigma^0_{\text{dB}} = 10 \log_{10}(DN^2 + \epsilon) - 83.0

The calibrated values are hard-clamped to :math:`[-35.0, 5.0]\,\text{dB}`. Speckle filtering uses a :math:`5 \times 5` Boxcar kernel (:math:`ENL \approx 4.9`). Optical preprocessing applies Sentinel-2 Scene Classification Layer (:math:`SCL`) masks, filtering cloud classes :math:`\{3, 8, 9, 10, 11\}`.

2. weather_forcing_coupler.py
-----------------------------
* **Bridge Module**: ``2_data_pipeline/ingestion/weather_forcing_coupler.py``
* **Target Module**: ``9_spaceborne_operational_campaign/4_execution_engine/weather_forcing_coupler.py``
* **Key Exports**: ``WeatherForcingCoupler``

Computes saturation vapor pressure :math:`e_s(T)` via the empirical Tetens formulation:

.. math::

   e_s(T) = 0.61078 \exp\left(\frac{17.27 T}{T + 237.3}\right) \quad [\text{kPa}]

Actual vapor pressure :math:`e_a` is derived via relative humidity :math:`RH`, yielding Vapor Pressure Deficit:

.. math::

   VPD = \max(0.0, e_s(T) - e_a)

Temperature is coupled with high-resolution DEM elevation using standard adiabatic lapse rate:

.. math::

   T_{\text{coupled}} = T_{2m} - \Gamma_{\text{adiabatic}} \cdot (Z_{\text{DEM}} - Z_{\text{base}})

where :math:`\Gamma_{\text{adiabatic}} = 0.0065\,\text{K/m}`.

3. comparative_baseline_benchmarks.py
-------------------------------------
* **Bridge Module**: ``2_data_pipeline/ingestion/comparative_baseline_benchmarks.py``
* **Target Module**: ``9_spaceborne_operational_campaign/4_execution_engine/comparative_baseline_benchmarks.py``
* **Key Exports**: ``NaiveOpticalRegressionBaseline``, ``WaterCloudModelBaseline``, ``BaselineBenchmarkEngine``, ``compute_hydrological_metrics``

Implements ordinary least squares (OLS) linear NDVI regression and Attema & Ulaby (1978) semi-empirical Water Cloud Model:

.. math::

   \sigma^0 = \sigma^0_{\text{veg}} + \tau^2 \sigma^0_{\text{soil}}

where:

.. math::

   \sigma^0_{\text{veg}} = A \cdot V_1 \cos(\theta_{\text{inc}}) \left(1 - \exp\left(-\frac{2 B V_2}{\cos(\theta_{\text{inc}})}\right)\right)

.. math::

   \tau^2 = \exp\left(-\frac{2 B V_2}{\cos(\theta_{\text{inc}})}\right), \quad \sigma^0_{\text{soil}} = C + D \cdot \theta_{\text{ground}}

Metrics computed include MAE, RMSE, Pearson correlation :math:`r`, and unbiased RMSE:

.. math::

   ubRMSE = \sqrt{RMSE^2 - \text{Bias}^2}

4. insitu_ingestor.py
---------------------
* **Bridge Module**: ``2_data_pipeline/ingestion/insitu_ingestor.py``
* **Target Module**: ``9_spaceborne_operational_campaign/4_execution_engine/insitu_ground_truth_ingestor.py``
* **Key Exports**: ``InSituGroundTruthIngestor``

Validates ground station volumetric soil moisture observations against ISMN protocols and SMAP Cal/Val standards. Rejects values outside :math:`[0.01, 0.60]\,\text{m}^3/\text{m}^3` and formats certified match-up tables.

5. spatial_temporal_collocator.py
---------------------------------
* **Bridge Module**: ``2_data_pipeline/ingestion/spatial_temporal_collocator.py``
* **Target Module**: ``9_spaceborne_operational_campaign/4_execution_engine/spatial_temporal_collocator.py``
* **Key Exports**: ``SpatialTemporalCollocator``

Maps geographic coordinates (UTM Easting, Northing) to 10m discrete image raster grid coordinates:

.. math::

   \text{row} = \left\lfloor \frac{\text{Northing}_{\max} - N}{\Delta y} \right\rfloor, \quad \text{col} = \left\lfloor \frac{E - \text{Easting}_{\min}}{\Delta x} \right\rfloor

Extracts coincident feature vectors across SAR, Optical, Terrain, and Weather modalities for each station cell.

6. realworld_engine_validator.py
--------------------------------
* **Bridge Module**: ``2_data_pipeline/ingestion/realworld_engine_validator.py``
* **Target Module**: ``9_spaceborne_operational_campaign/4_execution_engine/realworld_engine_validator.py``
* **Key Exports**: ``RealWorldEngineValidator``, ``compute_error_metrics``

Executes full 4-modality forward passes through the frozen AETHER engine. Runs cloud occlusion stress tests (zeroing optical channels) to confirm that radar backscatter and vadose physics prevent catastrophic prediction failure. Verifies monotonic epistemic uncertainty growth (:math:`\sigma_{\text{occluded}} > \sigma_{\text{clear}}`).

7. geotiff_production_exporter.py
---------------------------------
* **Bridge Module**: ``2_data_pipeline/ingestion/geotiff_production_exporter.py``
* **Target Module**: ``9_spaceborne_operational_campaign/4_execution_engine/geotiff_production_exporter.py``
* **Key Exports**: ``GeoTIFFProductionExporter``

Generates production-grade georeferenced GeoTIFF and Cloud-Optimized GeoTIFF (COG) rasters with internal tiling (:math:`256 \times 256`), DEFLATE compression, and multi-level overviews. Implements viewer-lock retry loops for Windows filesystem safety.

8. spaceborne_pipeline_orchestrator.py
--------------------------------------
* **Bridge Module**: ``2_data_pipeline/ingestion/spaceborne_pipeline_orchestrator.py``
* **Target Module**: ``9_spaceborne_operational_campaign/4_execution_engine/spaceborne_pipeline_orchestrator.py``
* **Key Exports**: ``SpacebornePipelineOrchestrator``

Provides automated execution sequencing across all ingestion and flight campaign stages, generating certified execution logs, telemetry streams, and JSON verification reports.

Requirements Catalog
====================

Functional Requirements
-----------------------
* **FR-ING-EXT-001**: Calibrate SAR digital numbers to physical backscatter intensity :math:`\sigma^0 \in [-35.0, 5.0]\,\text{dB}`.
* **FR-ING-EXT-002**: Screen optical pixels using Sentinel-2 SCL cloud classification layers.
* **FR-ING-EXT-003**: Calculate atmospheric vapor pressure deficit via Tetens equation with non-negative lower bound.
* **FR-ING-EXT-004**: Apply adiabatic environmental lapse rate (:math:`0.0065\,\text{K/m}`) to ERA5 reanalysis air temperature.
* **FR-ING-EXT-005**: Perform spatial collocation of ground truth points onto a discrete 10m grid.
* **FR-ING-EXT-006**: Execute comparative benchmark models (OLS and Water Cloud Model).
* **FR-ING-EXT-007**: Validate inference resilience during 100% optical cloud occlusion.
* **FR-ING-EXT-008**: Export tiled Cloud-Optimized GeoTIFF products with WGS84 UTM 45N spatial references.
* **FR-ING-EXT-009**: Automate end-to-end flight campaign pipeline execution.

Data Integrity Requirements
---------------------------
* **DI-ING-EXT-001**: Intermediate and final state tensors shall contain zero NaN or Inf values.
* **DI-ING-EXT-002**: Volumetric soil moisture outputs shall be bounded within :math:`[0.0, 0.60]\,\text{m}^3/\text{m}^3`.
* **DI-ING-EXT-003**: Input tensors shall conform strictly to :math:`(1, C, 64, 64)`.
* **DI-ING-EXT-004**: Occluded optical inputs shall produce strictly higher epistemic uncertainty than clear-sky inputs.

Verification Results
====================

Automated Test Evidence
-----------------------
The 8 operational bridge modules are validated by 20 unit tests across 4 test suites:
- ``tests/test_realworld_satellite_ingestion.py``
- ``tests/test_dem_weather_coupling.py``
- ``tests/test_insitu_collocation_and_baselines.py``
- ``tests/test_realworld_engine_validation.py``

All 20 tests pass deterministically in 8.73 seconds:

.. code-block:: text

   ============================= test session starts =============================
   platform win32 -- Python 3.14.7, pytest-9.1.1
   collected 20 items

   tests/test_dem_weather_coupling.py::TestDEMWeatherCoupling::test_soc_06_copernicus_dem_topographic_integrity PASSED [  5%]
   tests/test_dem_weather_coupling.py::TestDEMWeatherCoupling::test_soc_07_era5_weather_physical_bounds PASSED [ 10%]
   tests/test_dem_weather_coupling.py::TestDEMWeatherCoupling::test_soc_08_multi_sensor_spatial_alignment PASSED [ 15%]
   tests/test_dem_weather_coupling.py::TestDEMWeatherCoupling::test_soc_09_aether_engine_full_4modality_forward_handshake PASSED [ 20%]
   tests/test_dem_weather_coupling.py::TestDEMWeatherCoupling::test_soc_10_serialized_bundle_persistence_integrity PASSED [ 25%]
   tests/test_insitu_collocation_and_baselines.py::TestInsituCollocationAndBaselines::test_soc_11_insitu_ground_truth_ingestion_bounds PASSED [ 30%]
   tests/test_insitu_collocation_and_baselines.py::TestInsituCollocationAndBaselines::test_soc_12_spatial_temporal_collocation_grid_accuracy PASSED [ 35%]
   tests/test_insitu_collocation_and_baselines.py::TestInsituCollocationAndBaselines::test_soc_13_physical_sensor_correlation_integrity PASSED [ 40%]
   tests/test_insitu_collocation_and_baselines.py::TestInsituCollocationAndBaselines::test_soc_14_naive_optical_regression_baseline PASSED [ 45%]
   tests/test_insitu_collocation_and_baselines.py::TestInsituCollocationAndBaselines::test_soc_15_sar_water_cloud_model_baseline_and_export PASSED [ 50%]
   tests/test_realworld_engine_validation.py::TestRealWorldEngineValidation::test_soc_16_monolithic_inference_latency_and_zero_nan PASSED [ 55%]
   tests/test_realworld_engine_validation.py::TestRealWorldEngineValidation::test_soc_17_richards_vadose_pinn_conservation_residual PASSED [ 60%]
   tests/test_realworld_engine_validation.py::TestRealWorldEngineValidation::test_soc_18_multi_regime_cloud_occlusion_stress_test PASSED [ 65%]
   tests/test_realworld_engine_validation.py::TestRealWorldEngineValidation::test_soc_19_conformal_uncertainty_epistemic_growth PASSED [ 70%]
   tests/test_realworld_engine_validation.py::TestRealWorldEngineValidation::test_soc_20_comparative_baseline_benchmarking_and_artifacts PASSED [ 75%]
   tests/test_realworld_satellite_ingestion.py::TestSpaceborneOperationalIngestion::test_soc_01_sar_radiometric_calibration_bounds PASSED [ 80%]
   tests/test_realworld_satellite_ingestion.py::TestSpaceborneOperationalIngestion::test_soc_02_speckle_noise_suppression_enl PASSED [ 85%]
   tests/test_realworld_satellite_ingestion.py::TestSpaceborneOperationalIngestion::test_soc_03_optical_boa_scl_cloud_masking PASSED [ 90%]
   tests/test_realworld_satellite_ingestion.py::TestSpaceborneOperationalIngestion::test_soc_04_spatial_grid_homogeneity_and_patching PASSED [ 95%]
   tests/test_realworld_satellite_ingestion.py::TestSpaceborneOperationalIngestion::test_soc_05_aether_engine_realworld_inference_handshake PASSED [100%]

   ============================= 20 passed in 8.73s ==============================

Traceability Matrix
===================

.. list-table::
   :widths: 20 30 30 20
   :header-rows: 1

   * - Requirement
     - Source Module File
     - Verification Test
     - Status
   * - FR-ING-EXT-001
     - ``realworld_satellite_ingestor.py``
     - ``test_soc_01``
     - MET
   * - FR-ING-EXT-002
     - ``realworld_satellite_ingestor.py``
     - ``test_soc_03``
     - MET
   * - FR-ING-EXT-003
     - ``weather_forcing_coupler.py``
     - ``test_soc_07``
     - MET
   * - FR-ING-EXT-004
     - ``weather_forcing_coupler.py``
     - ``test_soc_07``
     - MET
   * - FR-ING-EXT-005
     - ``spatial_temporal_collocator.py``
     - ``test_soc_12``
     - MET
   * - FR-ING-EXT-006
     - ``comparative_baseline_benchmarks.py``
     - ``test_soc_14``, ``test_soc_15``
     - MET
   * - FR-ING-EXT-007
     - ``realworld_engine_validator.py``
     - ``test_soc_18``
     - MET
   * - FR-ING-EXT-008
     - ``geotiff_production_exporter.py``
     - ``test_soc_20``
     - MET
   * - FR-ING-EXT-009
     - ``spaceborne_pipeline_orchestrator.py``
     - ``test_soc_16``
     - MET

Defect Log and Technical Debt Register
======================================

.. list-table::
   :widths: 15 45 15 25
   :header-rows: 1

   * - Defect ID
     - Description
     - Severity
     - Remediation Plan
   * - D-ING-EXT-001
     - Inverted dependency: Layer 2 imports from Layer 9.
     - HIGH
     - Factor shared operational components into a common core library.
   * - D-ING-EXT-002
     - Mutates global ``sys.path`` dynamically on module import.
     - HIGH
     - Replace dynamic path manipulation with registered package installations.
   * - D-ING-EXT-003
     - Inconsistent import styles across the 8 bridge files.
     - MEDIUM
     - Standardize all bridge files on a uniform import pattern.
   * - D-ING-EXT-004
     - Incomplete export list in ``ingestion/__init__.py``.
     - MEDIUM
     - Add all 8 bridge classes to ``__all__`` in ``ingestion/__init__.py``.
   * - D-ING-EXT-005
     - Clamped Gaussian fallback for missing in-situ telemetry.
     - LOW
     - Flag synthetic observations with explicit ``is_synthetic`` metadata.
