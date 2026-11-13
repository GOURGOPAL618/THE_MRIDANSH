# 🛰️ Execution Engine Architecture & Module Manifest
## Mission: Spaceborne Operational Campaign (SOC-AETHER-2026) | Subsystem 09
### Repository Location: `9_spaceborne_operational_campaign/4_execution_engine/`
### Operational Status: ACTIVE PRODUCTION FLIGHT DRIVERS (TRL-7)

---

## 1. Subsystem Mandate & Engineering Tiers

The `4_execution_engine/` directory constitutes the primary algorithmic computation, ingestion, calibration, collocation, validation, and raster serialization engine for the **AETHER-MRID1607X** Earth Observation framework.

The 13 operational Python modules are architecturally organized into four sequential functional tiers:
* **Tier 1 — Radiometric & Environmental Preprocessing:** Physics-based radiometric calibration, speckle filtering, optical reflectance scaling, cloud masking, and micro-topographic downscaling.
* **Tier 2 — Spaceborne Ingestion & Field Drivers:** Spatial-temporal patch tiling, multi-sensor `IngestedTensorBundle` assembly, and daily telemetry test runners.
* **Tier 3 — In-Situ Collocation & Benchmark Modeling:** Ground truth soil station validation, 29-feature pixel collocation, and classical remote sensing comparative baselines (NDVI regression and SAR Water Cloud Model).
* **Tier 4 — Operational Validation & Production GIS Export:** Monolithic inference latency enforcement (<0.05 ms/px SLA), Richards PDE conservation verification, multi-regime cloud occlusion stress testing, and production Cloud-Optimized GeoTIFF (COG) generation.

---

## 2. 13-Module Inventory & Technical Signatures

| Module Filename | File Size | Functional Tier | Primary Classes / Functions | Key Algorithmic Responsibilities |
|:---|:---:|:---:|:---|:---|
| **`sar_radiometric_calibrator.py`** | 8.8 KB | Tier 1 | `SarRadiometricCalibrator` | Sentinel-1 C-Band ($VV, VH$) calibration to $\sigma^0_{\text{dB}} \in [-35.0, +5.0]\,\text{dB}$; Adaptive Refined Lee $5\times 5$ speckle filter (ENL gain $\ge 1.25\times$). |
| **`optical_cloud_preprocessor.py`** | 7.2 KB | Tier 1 | `OpticalCloudPreprocessor` | Sentinel-2 L2A BOA reflectance scaling ($DN \to [0, 1]$); SCL 12-class cloud mask extraction ($M_{\text{clear}} \in \{0, 1\}$); NDVI and moisture index inversion. |
| **`dem_topography_coupler.py`** | 8.3 KB | Tier 1 | `DEMTopographyCoupler` | Bilinear resampling of Copernicus 30m DEM to 10m UTM 45N grid; Horn's 2nd-order convolution kernels for Slope $\beta$, Aspect $\alpha$, and Topographic Wetness Index ($TWI$). |
| **`weather_forcing_coupler.py`** | 7.9 KB | Tier 1 | `WeatherForcingCoupler` | ERA5-Land climate forcing downscaling; Tetens formulation for Vapor Pressure Deficit ($VPD$ in kPa); environmental adiabatic lapse rate ($\Gamma = 0.0065\,\text{K/m}$). |
| **`realworld_satellite_ingestor.py`** | 11.2 KB | Tier 2 | `RealWorldSatelliteIngestor` | Multi-sensor spatial harmonization; $64\times 64$ patch windowing; assembly of certified `IngestedTensorBundle` for AETHER-MRID1607X. |
| **`run_day07_field_telemetry.py`** | 8.9 KB | Tier 2 | `generate_field_telemetry_scene`, `execute_day07_campaign` | Day 07 mission runner: end-to-end ingestion and forward handshake on dual-pol SAR and 4-band optical scene. |
| **`run_day08_dem_weather_telemetry.py`** | 12.9 KB | Tier 2 | `generate_day08_spaceborne_scene`, `execute_day08_telemetry_handshake` | Day 08 mission runner: couples 4 modalities (SAR + Optical + DEM + ERA5) and serializes the 14-channel production bundle. |
| **`insitu_ground_truth_ingestor.py`** | 11.0 KB | Tier 3 | `InSituGroundTruthIngestor` | ISMN / NASA SMAP Cal-Val network validator; captures dual-depth soil moisture ($0-5\,\text{cm}, 5-30\,\text{cm}$), bulk density, and USDA texture classes. |
| **`spatial_temporal_collocator.py`** | 10.7 KB | Tier 3 | `SpatialTemporalCollocator` | Geodetic coordinate transformation ($(E, N) \to (i, j)$); extracts 29-feature synchronized state vectors across all 4 spaceborne sources. |
| **`comparative_baseline_benchmarks.py`** | 11.9 KB | Tier 3 | `NaiveOpticalRegressionBaseline`, `WaterCloudModelBaseline`, `BaselineBenchmarkEngine` | Classical remote sensing models: Carlson-Ripley optical NDVI regression and Attema-Ulaby SAR Water Cloud Model (WCM); computes $R^2, RMSE, ubRMSE, MAE, r$. |
| **`realworld_engine_validator.py`** | 20.5 KB | Tier 4 | `RealWorldEngineValidator`, `compute_error_metrics` | Latency profiling ($<0.05\,\text{ms/px}$); multi-regime cloud occlusion stress testing ($0\% \to 100\%$); Richards PINN PDE residual check ($\|\mathcal{R}\|_2 < 0.05$); conformal uncertainty auditing. |
| **`geotiff_production_exporter.py`** | 20.1 KB | Tier 4 | `GeoTIFFProductionExporter`, `_is_file_locked_by_viewer` | Production GIS exporter: generates 10m single-band GeoTIFFs and 7-layer Master Cloud-Optimized GeoTIFF (COG) with GDAL overviews and LZW compression. |
| **`spaceborne_pipeline_orchestrator.py`** | 17.4 KB | Tier 4 | `SpacebornePipelineOrchestrator` | Master autonomous flight pipeline orchestrator: executes end-to-end mission workflow from raw telemetry to GIS export with cryptographic SHA-256 flight registries. |
