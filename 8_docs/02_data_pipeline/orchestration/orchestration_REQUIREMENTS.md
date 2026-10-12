# THE MRIDANSH (AETHER-MRID1607X)
# Module: 2_data_pipeline/orchestration
# Requirements, Verification and Configuration Control

---

## 1. Document Control

### 1.1 Identification

| Field | Value |
|:---|:---|
| **Document ID** | MRID-PIPE-ORC-DOC-001 |
| **Module Path** | `2_data_pipeline/orchestration/` |
| **Project** | THE MRIDANSH — Unified Soil State Estimation System |
| **System / Engine** | AETHER-MRID1607X (Multi-Domain Soil Intelligence Engine) |
| **Author / Developer** | Gourgopal Mohapatra |
| **Organization** | JCC HEADQUARTER — JCC CAMPUS 2, RS-SDA Division |
| **Reviewer** | *(To be assigned — independent technical reviewer)* |
| **Approver** | *(To be assigned — systems engineering authority)* |
| **Version** | 1.0 |
| **Date** | 2026-10-11 |
| **Status** | Baseline Draft — Unfiltered Technical Audit |
| **Classification** | Proprietary & Controlled Research Artifact |

### 1.2 Revision History

| Version | Date | Author | Description of Change |
|:---|:---|:---|:---|
| 0.1 | 2026-10-11 | Gourgopal Mohapatra | Static inspection of `pipeline_orchestrator.py` and test execution of `test_pipeline_orchestrator_d04.py`. |
| 1.0 | 2026-10-11 | Gourgopal Mohapatra | Formal unfiltered baseline release: complete requirements catalog, empirical test evidence, unwindowed full COG read defect expose, desynchronized dual-pol query flaw, and technical defect register. |

### 1.3 Document Conventions

- **SHALL** indicates a mandatory, verifiable engineering requirement.
- **SHOULD** indicates a recommended design practice or optimization target.
- **MAY** indicates an optional implementation path.
- **Requirement Status Definitions**:
  - `MET`: Requirement verified by passing test suite or empirical execution evidence.
  - `PARTIAL`: Implementation exists but exhibits severe code bugs, swallowed exceptions, or missing validations.
  - `NOT MET`: Requirement is completely absent, failing execution, or unhandled.
  - `WAIVED`: Formal departure accepted with recorded technical rationale.
- **Verification Methods**:
  - `T` (Test): Automated execution of unit test suites (`pytest`, `unittest`).
  - `A` (Analysis): Theoretical code inspection, architecture flow evaluation, and performance analysis.
  - `I` (Inspection): Line-by-line static manual examination of source code and AST syntax.
  - `D` (Demonstration): Operational execution against mock or live satellite frames.
- **Identifier Prefix Rules**:
  - `FR-ORC-xxx`: Functional Requirement (Orchestration)
  - `DI-ORC-xxx`: Data Integrity Requirement (Orchestration)
  - `IF-ORC-xxx`: Interface Requirement (Orchestration)
  - `UQ-ORC-xxx`: Uncertainty & Quality Requirement (Orchestration)
  - `NF-ORC-xxx`: Non-Functional Requirement (Orchestration)
  - `VP-ORC-xxx`: Verification Procedure (Orchestration)
  - `D-ORC-xxx`: Open Defect / Technical Flaw (Orchestration)
  - `R-ORC-xxx`: Technical Risk
  - `A-ORC-xxx`: Architectural Assumption

---

## 2. Purpose and Scope

### 2.1 Purpose

This document establishes the formal engineering requirements, verification procedures, empirical test results, bidirectional traceability, and an **unfiltered, brutally transparent technical debt and defect register** for the `2_data_pipeline/orchestration` subsystem within **THE MRIDANSH** (*AETHER-MRID1607X*).

### 2.2 System Context

The `orchestration` package serves as the end-to-end conductor uniting all modular stages of the data pipeline:
- **Upstream Modules Integrated**:
  1. `2_data_pipeline/ingestion/sentinel_ingestor.py` (`SentinelDataIngestor`): STAC metadata queries.
  2. `2_data_pipeline/preprocessing/cog_processor.py` (`COGRasterProcessor`): Remote raster streaming.
  3. `2_data_pipeline/preprocessing/raster_processor.py` (`RasterDataProcessor`): Reprojection and resampling.
  4. `2_data_pipeline/preprocessing/dem_processor.py` (`DEMTerrainEngine`): Elevation and slope extraction.
  5. `2_data_pipeline/fusion/satellite_fusion.py` (`SatelliteSAROpticalFusionEngine`): Multi-modal tensor stacking.
- **Downstream Consumers**: Invoked by high-level training pipelines (`test_core_trainer_d06.py`), domain integration scripts (`test_domain_integration_d05.py`), and operational dashboard workers (`6_dashboard/`).

### 2.3 Current-State Declaration (Mandatory Unfiltered Engineering Disclosure)

> [!CAUTION]
> **MANDATORY UNFILTERED AUDIT DECLARATION: ORCHESTRATION FLAWS & MEMORY EXPLOSION RISKS**
> 
> Critical code analysis reveals severe memory inefficiencies, architectural bypasses, and multi-sensor desynchronization vulnerabilities:
> 
> 1. **Unbounded Full-Scene Ingestion via `bbox=None` (Defect D-ORC-001)**:
>    In `pipeline_orchestrator.py` lines 28–30:
>    ```python
>    def _read_and_align(self, href: str) -> GeospatialRasterAsset:
>        # Read the full COG. The raster processor will clip it geographically using the target_bounds in the target_crs.
>        asset = self.cog_reader.read_raster_window(href, bbox=None)
>    ```
>    Passing `bbox=None` commands `rasterio` to **download and decompress the entire full-granule satellite image** into memory!
>    A single Sentinel-2 full granule is $10980 \times 10980$ pixels ($\approx 241\,\text{MB}$ per band).
>    The orchestrator reads `red`, `nir`, `swir16`, `vv`, and `vh` in full—allocating **over 1.1 GIGABYTES of unwindowed pixel data** in RAM—merely to extract a tiny $120 \times 120$ tile ($28\,\text{KB}$) in `reproject_asset`!
>    This completely defeats the purpose of Cloud-Optimized GeoTIFFs (COGs), which exist to support HTTP range window GETs.
> 
> 2. **Desynchronized Dual-Polarization SAR Queries (Defect D-ORC-002)**:
>    In lines 80–81:
>    ```python
>    sar_vv_frames = self.ingestor.fetch_radar_sar_frames(bbox, start_date, end_date, polarization="VV")
>    sar_vh_frames = self.ingestor.fetch_radar_sar_frames(bbox, start_date, end_date, polarization="VH")
>    vv_frame = sar_vv_frames[0]
>    vh_frame = sar_vh_frames[0]
>    ```
>    Because `sentinel_ingestor.py` cannot return dual-pol simultaneously (Defect `D-ING-002`), the orchestrator issues two independent STAC searches.
>    It takes `sar_vv_frames[0]` and `sar_vh_frames[0]` **without checking whether they share the same scene ID, orbit direction, or acquisition date**!
>    `vv_frame` could be from an ascending pass on January 5th, while `vh_frame` could be from a descending pass on January 29th! Fusing them together produces invalid, geometrically corrupted cross-polarization ratios.
> 
> 3. **Architectural Bypass of `feature_engineering` Subsystem (Defect D-ORC-003)**:
>    Instead of importing and utilizing `VegetationIndicesEngine` from `2_data_pipeline/feature_engineering/spectral_indices.py`, the orchestrator re-implements index calculation internally in lines 40–66 (`_compute_index`). The entire `feature_engineering` package is left as orphaned dead code in the production execution path.
> 
> 4. **Hardcoded Element84 Asset Keys (Defect D-ORC-004)**:
>    Lines 91–94 enforce:
>    ```python
>    req_opt = ["red", "nir", "swir16"]
>    for ro in req_opt:
>        if ro not in opt_frame.asset_hrefs:
>            raise RuntimeError(f"Pipeline Failure: Missing required '{ro}' asset in Optical Frame {opt_frame.scene_id}.")
>    ```
>    Queries against Copernicus CDSE (which uses `B04`, `B08`, `B11`) unconditionally fail and abort the pipeline with a `RuntimeError`.

---

## 3. Requirements Catalog

### 3.1 Functional Requirements

#### FR-ORC-001: End-to-End Orchestration Workflow Execution
- **Description**: The subsystem SHALL orchestrate the sequential discovery, streaming, reprojection, index computation, and fusion of Sentinel-1, Sentinel-2, and optional DEM rasters for a specified bounding box, returning a unified output payload.
- **Verification Method**: `T` (Test via `tests/test_pipeline_orchestrator_d04.py::test_orch_01_successful_orchestration`)
- **Status**: `MET`

#### FR-ORC-002: Missing STAC Scene Detection and Abort
- **Description**: If STAC searches return zero frames for any mandatory constellation (Optical, SAR VV, SAR VH), the orchestrator SHALL immediately raise `RuntimeError` and halt execution.
- **Verification Method**: `T` (Test via `tests/test_pipeline_orchestrator_d04.py::test_orch_02_missing_stac_frames`)
- **Status**: `MET`

#### FR-ORC-003: Optical Spectral Band Completeness Verification
- **Description**: The orchestrator SHALL verify that the optical scene contains all required spectral channels (`red`, `nir`, `swir16`). If any required asset is missing from `asset_hrefs`, it SHALL raise `RuntimeError`.
- **Verification Method**: `T` (Test via `tests/test_pipeline_orchestrator_d04.py::test_orch_03_missing_optical_bands`)
- **Status**: `MET`

#### FR-ORC-004: In-Memory Spectral Index Derivation
- **Description**: The orchestrator SHALL compute normalized difference indices (NDVI and NDMI) from reprojected surface reflectance assets, preserving CRS, affine geotransform, bounds, and aggregated boolean validity masks.
- **Verification Method**: `T` (Test via `tests/test_pipeline_orchestrator_d04.py`)
- **Status**: `MET`

#### FR-ORC-005: Optional DEM Terrain Modeling Integration
- **Description**: When `include_dem=True`, the orchestrator SHALL query Copernicus GLO-30 DEM, reproject elevation to the target grid, compute terrain slope, and pass both layers to the fusion engine.
- **Verification Method**: `T` (Test via `tests/test_pipeline_orchestrator_d04.py::test_orch_06_optional_dem_handling`)
- **Status**: `MET`

#### FR-ORC-006: Data Provenance Preservation Across Pipeline Tiers
- **Description**: The orchestrator SHALL attach the original upstream STAC scene identifiers (`stac_item_id`) to all reprojected raster assets prior to invoking fusion.
- **Verification Method**: `T` (Test via `tests/test_pipeline_orchestrator_d04.py`)
- **Status**: `MET`

#### FR-ORC-007: Exception Wrapping and Diagnostic Error Messages
- **Description**: The orchestrator SHALL catch low-level `RasterReadError`, `GridAlignmentError`, `MissingModalityError`, and `GridMismatchError` exceptions and wrap them into informative `RuntimeError` messages prefixed with `"Pipeline Failure: "`.
- **Verification Method**: `T` (Test via `tests/test_pipeline_orchestrator_d04.py::test_orch_04_rasterio_read_error`)
- **Status**: `MET`

---

### 3.2 Data Integrity Requirements

#### DI-ORC-001: Target Grid Parameter Coherence
- **Description**: The target grid definition (`target_crs`, `target_resolution`, `target_bounds`) configured in `PipelineOrchestrator.__init__` SHALL be passed identically to both the reprojection aligner and the fusion engine.
- **Verification Method**: `I`
- **Status**: `MET`

#### DI-ORC-002: Spatial Mask Aggregation Invariant
- **Description**: Derived index masks (NDVI, NDMI) SHALL be computed via bitwise AND: $\mathbf{M}_{\text{index}} = \mathbf{M}_{\text{NIR}} \land \mathbf{M}_{\text{other}}$, ensuring invalid pixels in either band propagate to the index mask.
- **Verification Method**: `T`
- **Status**: `MET`

---

### 3.3 Interface Requirements

#### IF-ORC-001: Public Pipeline Execution Signature
- **Description**: The primary entry point SHALL be `run_pipeline(bbox_coords, start_date, end_date, include_dem=False) -> dict[str, Any]`.
- **Verification Method**: `T`
- **Status**: `MET`

#### IF-ORC-002: Pipeline Execution Return Schema
- **Description**: Upon success, `run_pipeline` SHALL return a dictionary containing keys `"status"`, `"target_grid"`, and `"fusion_result"`.
- **Verification Method**: `T`
- **Status**: `MET`

---

### 3.4 Uncertainty & Quality Requirements

#### UQ-ORC-001: Multi-Sensor Temporal Coherence Threshold
- **Description**: The orchestrator SHALL enforce that the optical and SAR acquisitions selected for fusion do not exceed a maximum temporal delta $\Delta t_{\text{max}} \le 7\,\text{days}$.
- **Verification Method**: `A`
- **Status**: `NOT MET` *(Zero temporal check; selects first scene blindly)*

#### UQ-ORC-002: Dual-Polarization Scene ID Identity
- **Description**: The orchestrator SHALL assert that the VV and VH radar frames selected originate from the identical STAC scene: `assert vv_frame.scene_id == vh_frame.scene_id`.
- **Verification Method**: `A`
- **Status**: `NOT MET` *(Zero scene ID comparison)*

---

### 3.5 Non-Functional Requirements

#### NF-ORC-001: End-to-End Orchestration Execution Latency
- **Description**: Mock end-to-end pipeline orchestration SHALL execute in under $15.0\,\text{seconds}$.
- **Verification Method**: `T` (Benchmarked: 6 tests executed in $10.80\,\text{s}$)
- **Status**: `MET`

---

## 4. Verification Procedures & Results

### 4.1 Procedure Catalog

| Procedure ID | Target Requirement | Description | Expected Result |
|:---|:---|:---|:---|
| **VP-ORC-001** | `FR-ORC-001` | Execute `test_orch_01_successful_orchestration` with mock optical and SAR frames. | Returns `status="SUCCESS"` with 5-channel fused tensor. |
| **VP-ORC-002** | `FR-ORC-002` | Execute `test_orch_02_missing_stac_frames` with empty optical search results. | Raises `RuntimeError("Missing required STAC frames...")`. |
| **VP-ORC-003** | `FR-ORC-003` | Execute `test_orch_03_missing_optical_bands` with missing `swir16` asset. | Raises `RuntimeError("Missing required 'swir16' asset...")`. |
| **VP-ORC-004** | `FR-ORC-007` | Execute `test_orch_04_rasterio_read_error` simulating corrupted GeoTIFF. | Raises wrapped `RuntimeError("Raster extraction or alignment failed...")`. |
| **VP-ORC-005** | `FR-ORC-005` | Execute `test_orch_06_optional_dem_handling` with `include_dem=True`. | Output fusion contains `DEM_ELEVATION` and `DEM_SLOPE` (7 channels). |

### 4.2 Empirical Execution Evidence

Executed under Python 3.12.0:

```text
============================= test session starts =============================
platform win32 -- Python 3.12.0, pytest-9.0.2, pluggy-1.6.0
rootdir: D:\JAGANNATH_CODE_SANCTUM\JCC CAMPUS 2 (RS-SDA DIVISION)\THE_MRIDANSH
configfile: pyproject.toml
plugins: anyio-4.13.0, cov-7.1.0, zarr-3.1.6
collected 6 items

tests\test_pipeline_orchestrator_d04.py ......                           [100%]
============================= 6 passed in 10.80s ==============================
```

Detailed test outputs:
- `T-ORCH-01`: Successful orchestration with mock STAC and COG reader -> **PASS**
- `T-ORCH-02`: Missing STAC frames triggers immediate abort -> **PASS**
- `T-ORCH-03`: Missing required optical bands triggers abort -> **PASS**
- `T-ORCH-04`: RasterIO read failure caught and wrapped -> **PASS**
- `T-ORCH-05`: Reprojection grid mismatch caught and wrapped -> **PASS**
- `T-ORCH-06`: Optional DEM inclusion verified -> **PASS**

---

## 5. Traceability Matrix

| Requirement ID | Module | Class / Function | Source Line Range |
|:---|:---|:---|:---|
| `FR-ORC-001` | `pipeline_orchestrator.py` | `PipelineOrchestrator.run_pipeline` | L68–L165 |
| `FR-ORC-002` | `pipeline_orchestrator.py` | `PipelineOrchestrator.run_pipeline` | L83–L84 |
| `FR-ORC-003` | `pipeline_orchestrator.py` | `PipelineOrchestrator.run_pipeline` | L91–L95 |
| `FR-ORC-004` | `pipeline_orchestrator.py` | `PipelineOrchestrator._compute_index` | L40–L66 |
| `FR-ORC-005` | `pipeline_orchestrator.py` | `PipelineOrchestrator.run_pipeline` | L125–L139 |
| `FR-ORC-006` | `pipeline_orchestrator.py` | `PipelineOrchestrator.run_pipeline` | L111–L115 |
| `FR-ORC-007` | `pipeline_orchestrator.py` | `PipelineOrchestrator.run_pipeline` | L107–L108, L152–L153 |
| `DI-ORC-001` | `pipeline_orchestrator.py` | `PipelineOrchestrator.__init__` | L19–L26 |
| `DI-ORC-002` | `pipeline_orchestrator.py` | `PipelineOrchestrator._compute_index` | L49 |
| `IF-ORC-001` | `pipeline_orchestrator.py` | `PipelineOrchestrator.run_pipeline` | L68–L74 |
| `IF-ORC-002` | `pipeline_orchestrator.py` | `PipelineOrchestrator.run_pipeline` | L156–L164 |

---

## 6. Defect Log and Technical Debt Register

### D-ORC-001: Unbounded Full-Scene Ingestion via `bbox=None`
- **Location**: `pipeline_orchestrator.py:30`
- **Severity**: CRITICAL
- **Description**: Calls `self.cog_reader.read_raster_window(href, bbox=None)`. Downloads and decompresses the entire $10980 \times 10980$ pixel scene ($\approx 241\,\text{MB}$ per band) across 5 bands ($\approx 1.1\,\text{GB}$) just to crop a $120 \times 120$ tile in `reproject_asset`.
- **Remediation**: Transform `target_bounds` from `target_crs` to source raster CRS and pass bounding box to `read_raster_window` for windowed HTTP GET.

### D-ORC-002: Desynchronized Dual-Polarization SAR Queries
- **Location**: `pipeline_orchestrator.py:80-88`
- **Severity**: HIGH
- **Description**: Issues separate STAC searches for VV and VH, selecting `sar_vv_frames[0]` and `sar_vh_frames[0]` without verifying that they belong to the same scene ID or orbit.
- **Remediation**: Query dual-polarization items as a single STAC search and assert scene ID equality.

### D-ORC-003: Subsystem Bypass & Duplicate Index Code
- **Location**: `pipeline_orchestrator.py:40-66`
- **Severity**: MEDIUM
- **Description**: Duplicates index calculation internally instead of calling `2_data_pipeline/feature_engineering/`, creating unmanaged code duplication.
- **Remediation**: Route index computation through `feature_engineering` engine.

### D-ORC-004: Hardcoded Element84 Asset Key Names
- **Location**: `pipeline_orchestrator.py:91-94`
- **Severity**: HIGH
- **Description**: Requires `["red", "nir", "swir16"]`, failing unconditionally on standard Copernicus CDSE or Planetary Computer catalogs.
- **Remediation**: Use band alias resolution mapping logical names to catalog-specific band keys.

### D-ORC-005: Absence of Multi-Temporal Epoch Iteration
- **Location**: `pipeline_orchestrator.py:86-88`
- **Severity**: MEDIUM
- **Description**: Selects index 0 (`[0]`), collapsing a temporal date range into a single unvalidated snapshot.
- **Remediation**: Support temporal sequence iteration returning a list of timestamped fused tensors for ConvLSTM models.

---

## 7. Configuration Control

### 7.1 Module Software Configuration

| Module File | Lines of Code | Description |
|:---|:---:|:---|
| `2_data_pipeline/orchestration/pipeline_orchestrator.py` | 165 | End-to-end execution pipeline uniting ingestion, preprocessing, and fusion. |

### 7.2 Environment and Runtime Constraints

- Python: `>= 3.10` (Tested on `Python 3.12.0`)
- Rasterio: `>= 1.3.0`
- NumPy: `>= 1.24.0`
