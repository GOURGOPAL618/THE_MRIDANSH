# THE MRIDANSH (AETHER-MRID1607X)
# Notebook 01: Multi-Source Satellite Telemetry Data Ingestion
# Requirements, Verification and Configuration Control

---

## 1. Document Control

### 1.1 Identification

| Field | Value |
|:---|:---|
| **Document ID** | MRID-NB01-REQ-001 |
| **Notebook Path** | `1_notebooks_sandbox/01-data-ingestion.ipynb` |
| **Companion Technical Document** | `01_data_ingestion.rst` |
| **Project** | THE MRIDANSH — Unified Soil State Estimation System |
| **Central Engine** | AETHER-MRID1607X (Multi-Domain Soil Intelligence Engine) |
| **Division** | RS-SDA (Remote Sensing & Spatial Data Analytics), JCC Campus 2 / Headquarter |
| **Author / Maintainer** | Gourgopal Mohapatra |
| **Version** | 1.0 (Post-Audit Synchronized Baseline) |
| **Status** | Approved — Unfiltered Engineering Audit |
| **Classification** | Proprietary & Controlled Research Artifact |

### 1.2 Revision History

| Version | Date | Author | Description of Change |
|:---|:---|:---|:---|
| 0.1 | 2026-10-05 | G. Mohapatra | Initial requirements stub. |
| 0.2 | 2026-10-06 | G. Mohapatra | Restructured as standalone requirements document. |
| 1.0 | 2026-11-04 | G. Mohapatra | Complete unfiltered baseline synchronized with updated `01-data-ingestion.ipynb`: full aerospace telemetry ingestion, 6 storage plots, STAC 1.0.0 asset tree, bilinear DEM resampling, and empirical test verification (`test_notebook_01_verification.py`). |

### 1.3 Document Conventions

- **SHALL** indicates a mandatory, verifiable engineering requirement.
- **SHOULD** indicates a recommended design practice.
- **MAY** indicates an optional design path.
- **Requirement Status Definitions**:
  - `MET`: Requirement verified by passing test suite or empirical execution evidence.
  - `PARTIAL`: Implementation exists but exhibits code bugs or incomplete validation.
  - `NOT MET`: Requirement is completely absent or failing execution.
- **Verification Methods**:
  - `T` (Test): Automated execution of unit test suites (`pytest`, `unittest`).
  - `A` (Analysis): Theoretical code inspection, dimensional analysis, and geodetic math verification.
  - `I` (Inspection): Static line-by-line manual examination of source code and AST syntax.
  - `D` (Demonstration): Operational spatial execution against sample rasters and CSV outputs.

---

## 2. Purpose and Scope

### 2.1 Purpose

This document establishes the formal engineering requirements, verification procedures, empirical test results, bidirectional traceability, and an **unfiltered, brutally transparent technical debt and defect register** for `1_notebooks_sandbox/01-data-ingestion.ipynb` within **THE MRIDANSH** (*AETHER-MRID1607X*).

### 2.2 System Context

Notebook 01 establishes the foundational observational intake for the entire AETHER engine:
- **Spatial Area of Interest (AOI)**: Bhadrak Catchment, Odisha, India ($\text{Lat } 21.1378^\circ\,\text{N}, \text{Lon } 86.6874^\circ\,\text{E}$), defined via bounding box $[\text{min\_lon}=86.6374, \text{min\_lat}=21.0878, \text{max\_lon}=86.7374, \text{max\_lat}=21.1878]$ with buffer $\Delta = 0.05^\circ$.
- **Temporal Window**: Monsoon baseline from `2026-08-01` to `2026-09-07` (35 observation epochs).
- **Multi-Sensor Modalities**:
  1. Copernicus Sentinel-1 C-Band SAR ($5.405\,\text{GHz}$): Co-polarization (VV), Cross-polarization (VH), and Polarization Ratio ($\text{VH}/\text{VV}$).
  2. Copernicus Sentinel-2 Multi-Spectral Instrument (MSI): Band 3 (Green, $560\,\text{nm}$), Band 4 (Red, $665\,\text{nm}$), Band 8 (NIR, $842\,\text{nm}$), and Scene Cloud Cover percentage.
  3. Digital Elevation Model (DEM): Copernicus GLO-30 / SRTM topographic elevation ($33 \times 33$ grid at $30\,\text{m}$ resolution).
  4. Atmospheric Forcing Telemetry: Surface air temperature ($^\circ\text{C}$) and monsoonal precipitation ($\text{mm/day}$).
- **Downstream Consumers**: Serializes standardized raw data lake products consumed directly by Notebook 02 (`02-preprocessing.ipynb`).

### 2.3 Current-State Declaration (Mandatory Unfiltered Engineering Disclosure)

> [!CAUTION]
> **MANDATORY UNFILTERED AUDIT DECLARATION: INGESTION SANDBOX REALITIES**
> 
> 1. **Synthetic Telemetry Simulation Boundary**:
>    While the notebook models realistic physical ranges, the current notebook run uses deterministic random distributions (`provenance: "SYNTHETIC_SIMULATION"`, seeds 42 and 101) to simulate multi-sensor observations rather than direct live HTTP STAC streaming. This is explicitly verified by test `test_06_data_and_schema_integrity`.
> 2. **Fixed Constant Resolution Assumption**:
>    Bilinear resampling of the DEM grid uses a fixed ratio of $100/33 \approx 3.0303\times$, assuming ground sampling distance scales exactly from $30\,\text{m}$ to $10\,\text{m}$.
> 3. **Regularization Absent in Notebook Index Calculation**:
>    In Cell 7:
>    ```python
>    df['ndvi'] = (df['s2_b08_nir'] - df['s2_b04_red']) / (df['s2_b08_nir'] + df['s2_b04_red'])
>    df['ndwi'] = (df['s2_b03_green'] - df['s2_b08_nir']) / (df['s2_b03_green'] + df['s2_b08_nir'])
>    ```
>    Zero epsilon regularization ($\varepsilon = 10^{-8}$) is added in the denominator. If a pixel has zero reflectance in both bands, IEEE 754 division yields `NaN` or `Inf`. (This defect was later remedied in the production pipeline `multisource_ingestor.py` and `spectral_indices.py`).

---

## 3. Requirements Catalog

### 3.1 Functional Requirements

#### FR-NB01-001: Geographic Bounding Box Formulation
- **Description**: The notebook SHALL parameterize the target spatial region using a central centroid ($\text{Lat } 21.1378^\circ\,\text{N}, \text{Lon } 86.6874^\circ\,\text{E}$) and a half-width buffer ($\Delta = 0.05^\circ$), producing a closed 4-coordinate bounding box $[\text{min\_lon}, \text{min\_lat}, \text{max\_lon}, \text{max\_lat}]$.
- **Verification Method**: `T` (Test via `tests/test_notebook_01_verification.py`)
- **Status**: `MET`

#### FR-NB01-002: Multi-Sensor Telemetry Synthesizer
- **Description**: The notebook SHALL synthesize a 35-sample longitudinal observation sequence covering Sentinel-1 (VV in $[-18, -8]\,\text{dB}$, VH in $[-25, -14]\,\text{dB}$), Sentinel-2 (Green in $[0.05, 0.22]$, Red in $[0.02, 0.18]$, NIR in $[0.20, 0.52]$, Cloud Cover in $[0, 90]\%$), and Atmospheric Forcing (Temperature in $[25, 36]^\circ\text{C}$, Precipitation discrete distribution).
- **Verification Method**: `T` (Test via `test_06_data_and_schema_integrity`)
- **Status**: `MET`

#### FR-NB01-003: Spectral Index Calculation (NDVI and NDWI)
- **Description**: The notebook SHALL compute Normalized Difference Vegetation Index (NDVI) and Normalized Difference Water Index (NDWI) from optical telemetry, verifying that all output values are strictly bounded within $[-1.0, 1.0]$.
- **Verification Method**: `T` (Test via `test_06_data_and_schema_integrity`)
- **Status**: `MET`

#### FR-NB01-004: Multi-Resolution Spatial DEM Grid Resampling
- **Description**: The notebook SHALL align native $30\,\text{m}$ digital elevation data ($33 \times 33$ grid) onto the $10\,\text{m}$ Sentinel spatial grid ($100 \times 100$ pixels) using Bilinear interpolation (`scipy.ndimage.zoom`, order=1).
- **Verification Method**: `T` (Test via `test_05_storage_artifacts_and_plots_persisted`)
- **Status**: `MET`

#### FR-NB01-005: STAC 1.0.0 Asset Tree Construction
- **Description**: The notebook SHALL construct an official SpatioTemporal Asset Catalog (STAC) v1.0.0 GeoJSON Feature dictionary specifying properties, datetime, bounding coordinates, and typed asset links (`B04_RED`, `B08_NIR`, `B03_GREEN`, `SAR_VV`, `SAR_VH`, `DEM_ALIGNED`).
- **Verification Method**: `T` (Test via `test_06_data_and_schema_integrity`)
- **Status**: `MET`

#### FR-NB01-006: High-Contrast Aerospace Plots Export
- **Description**: The notebook SHALL generate and persist 6 high-contrast publication-grade aerospace plots into `5_storage/notebook_results/notebook_01_ingestion/`:
  1. `plot_01_s1_sar_dynamics.png`
  2. `plot_02_s2_spectral_indices.png`
  3. `plot_03_cloud_masking_sar_fallback.png`
  4. `plot_04_atmospheric_forcing_precip_temp.png`
  5. `plot_05_spatial_rasters_ndvi_sar.png`
  6. `plot_06_resampled_dem_profile.png`
- **Verification Method**: `T` (Test via `test_05_storage_artifacts_and_plots_persisted`)
- **Status**: `MET`

#### FR-NB01-007: Dual Data Lake Persistence
- **Description**: The notebook SHALL serialize the raw telemetry DataFrame (`stac_telemetry_raw.csv`) and STAC metadata (`stac_catalog_item.json`) into both `5_storage/notebook_results/notebook_01_ingestion/` and `data/raw/`.
- **Verification Method**: `T` (Test via `test_05_storage_artifacts_and_plots_persisted`)
- **Status**: `MET`

---

### 3.2 Data Integrity Requirements

#### DI-NB01-001: Standardized Column Nomenclature
- **Description**: Telemetry DataFrames SHALL use standardized column identifiers without typos (specifically verifying `weather_temp_c` instead of `weayher_temp_c`).
- **Verification Method**: `T` (Test via `test_06_data_and_schema_integrity`)
- **Status**: `MET`

#### DI-NB01-002: Provenance Tag Invariant
- **Description**: The telemetry DataFrame SHALL include an explicit `provenance` column with value `"SYNTHETIC_SIMULATION"` to prevent uncalibrated synthetic data from being mistaken for live satellite feeds.
- **Verification Method**: `T` (Test via `test_06_data_and_schema_integrity`)
- **Status**: `MET`

#### DI-NB01-003: STAC 1.0.0 Assets Key Compliance
- **Description**: The STAC metadata dictionary SHALL use key `"assets"`, strictly prohibiting deprecated or misspelled keys such as `"assert"`.
- **Verification Method**: `T` (Test via `test_06_data_and_schema_integrity`)
- **Status**: `MET`

---

## 4. Verification Procedures & Test Results

### 4.1 Verification Procedures

| Procedure ID | Target Requirement | Description | Expected Result |
|:---|:---|:---|:---|
| **VP-NB01-01** | Architecture Rules | Verify no `.py` scripts exist in `1_notebooks_sandbox/`. | Zero Python scripts found. |
| **VP-NB01-02** | Cell Rules | Verify every code cell is immediately preceded by a markdown cell. | 14 code cells each preceded by markdown. |
| **VP-NB01-03** | Execution Rules | Verify all code cells have non-null execution counts and 0 errors. | Execution counts $>0$, 0 errors. |
| **VP-NB01-04** | Closure Rules | Verify penultimate cell is Executive Summary and ultimate is Copyright. | Proper summary milestones and copyright notice. |
| **VP-NB01-05** | Artifact Rules | Verify 6 aerospace plots and 2 data lake files exist in `5_storage/notebook_01_ingestion/`. | All 8 artifacts exist and exceed minimum size thresholds. |
| **VP-NB01-06** | Schema Rules | Verify column spelling, index bounds, and STAC 1.0.0 compliance. | All assertions pass without exceptions. |

### 4.2 Empirical Execution Evidence

Executed under `mridansh_env` (Python 3.14.7 / PyTorch 2.14.0):

```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\JAGANNATH_CODE_SANCTUM\JCC CAMPUS 2 (RS-SDA DIVISION)\THE_MRIDANSH
configfile: pyproject.toml
collected 6 items

tests\test_notebook_01_verification.py ......                            [100%]

============================== 6 passed in 0.45s ==============================
```

---

## 5. Traceability Matrix

| Requirement ID | Notebook Section / Cell | Test Function | Status |
|:---|:---|:---|:---:|
| `FR-NB01-001` | Step 1 (Cell 5) | `test_06_data_and_schema_integrity` | `MET` |
| `FR-NB01-002` | Step 2 (Cell 7) | `test_06_data_and_schema_integrity` | `MET` |
| `FR-NB01-003` | Step 2 (Cell 7) | `test_06_data_and_schema_integrity` | `MET` |
| `FR-NB01-004` | Step 5 (Cell 21) | `test_05_storage_artifacts_and_plots_persisted` | `MET` |
| `FR-NB01-005` | Step 6 (Cell 27) | `test_06_data_and_schema_integrity` | `MET` |
| `FR-NB01-006` | Plots 1–6 (Cells 11, 13, 15, 17, 23, 25) | `test_05_storage_artifacts_and_plots_persisted` | `MET` |
| `FR-NB01-007` | Step 7 (Cell 29) | `test_05_storage_artifacts_and_plots_persisted` | `MET` |
| `DI-NB01-001` | Step 2 (Cell 7) | `test_06_data_and_schema_integrity` | `MET` |
| `DI-NB01-002` | Step 2 (Cell 7) | `test_06_data_and_schema_integrity` | `MET` |
| `DI-NB01-003` | Step 6 (Cell 27) | `test_06_data_and_schema_integrity` | `MET` |

---

## 6. Defect Log & Technical Debt Register

### D-NB01-001: Absence of Epsilon Regularization in Spectral Index Calculations
- **Location**: `01-data-ingestion.ipynb:Cell 7`
- **Severity**: LOW
- **Description**: Formula calculates `(nir - red) / (nir + red)` without adding $\varepsilon = 10^{-8}$. If both bands are zero, division results in `NaN`.
- **Remediation**: Add $10^{-8}$ in denominator (applied in production pipeline).

### D-NB01-002: Hardcoded DEM Zoom Ratio
- **Location**: `01-data-ingestion.ipynb:Cell 21`
- **Severity**: LOW
- **Description**: Uses `zoom_y = GRID_HEIGHT / dem_low_res.shape[0] = 100 / 33`. Ignores geotransform coordinate offsets between raster centers.
- **Remediation**: In production, route resampling through GDAL/Rasterio reprojection (`RasterDataProcessor`).

---

## 7. Configuration Control

### 7.1 Software Environment

- Python: `>= 3.10` (Tested on `Python 3.14.7` / `Python 3.12.0`)
- Key Libraries: `numpy >= 1.24.0`, `pandas >= 2.0.0`, `scipy >= 1.10.0`, `matplotlib >= 3.7.0`
- Seed Invariants: Global seed 42 for temporal telemetry, seed 101 for spatial raster sub-grids.
