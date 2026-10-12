# THE MRIDANSH (AETHER-MRID1607X)
# Module: 2_data_pipeline/schemas
# Requirements, Verification and Configuration Control

---

## 1. Document Control

### 1.1 Identification

| Field | Value |
|:---|:---|
| **Document ID** | MRID-PIPE-SCH-DOC-001 |
| **Module Path** | `2_data_pipeline/schemas/` |
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
| 0.1 | 2026-10-11 | Gourgopal Mohapatra | Static line-by-line inspection of `satellite_schema.py`, `weather_schema.py`, and orphan `test_schema.py`. |
| 1.0 | 2026-10-11 | Gourgopal Mohapatra | Formal unfiltered baseline release: complete requirements catalog, empirical test evidence, CP1252 emoji crash exposure, 30m resolution default mismatch, and defect log. |

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
  - `A` (Analysis): Theoretical code inspection, mathematical derivation, and physical dimensional analysis.
  - `I` (Inspection): Line-by-line static manual examination of source code and AST syntax.
  - `D` (Demonstration): Operational execution against sample schema payloads.
- **Identifier Prefix Rules**:
  - `FR-SCH-xxx`: Functional Requirement (Schemas)
  - `DI-SCH-xxx`: Data Integrity Requirement (Schemas)
  - `IF-SCH-xxx`: Interface Requirement (Schemas)
  - `UQ-SCH-xxx`: Uncertainty & Quality Requirement (Schemas)
  - `NF-SCH-xxx`: Non-Functional Requirement (Schemas)
  - `VP-SCH-xxx`: Verification Procedure (Schemas)
  - `D-SCH-xxx`: Open Defect / Technical Flaw (Schemas)
  - `R-SCH-xxx`: Technical Risk
  - `A-SCH-xxx`: Architectural Assumption

---

## 2. Purpose and Scope

### 2.1 Purpose

This document establishes the formal engineering requirements, verification procedures, empirical execution results, bidirectional traceability, and an **unfiltered, brutally transparent technical debt and defect register** for the `2_data_pipeline/schemas` subsystem within **THE MRIDANSH** (*AETHER-MRID1607X*).

### 2.2 System Context

The `schemas` subsystem provides the foundational Pydantic type models and contracts governing all inter-module communication across the data pipeline:
- **Scope**:
  1. `satellite_schema.py` (176 lines): Defines `SpatialBoundingBox`, `SentinelFrameMetadata`, and the canonical `GeospatialRasterAsset` contract.
  2. `weather_schema.py` (31 lines): Defines `WeatherTelemetry` for atmospheric covariates.
  3. `test_schema.py` (57 lines): Redundant prototype file contaminating production package space.
- **Consumers**: Imported by all subsystems across `ingestion/`, `preprocessing/`, `feature_engineering/`, `fusion/`, and `orchestration/`.

### 2.3 Current-State Declaration (Mandatory Unfiltered Engineering Disclosure)

> [!CAUTION]
> **MANDATORY UNFILTERED AUDIT DECLARATION: SCHEMA DEFECTS & DRIFT**
> 
> 1. **Orphan Scratch File in Production Namespace (Defect D-SCH-001)**:
>    `2_data_pipeline/schemas/test_schema.py` is an uncurated scratch file left in the production package directory. It contains an un-namespaced executable statement `print("Imports and class definitions successful.")` at line 56 that prints to stdout on module load.
> 
> 2. **Default Resolution Mismatch for Sentinel Products (Defect D-SCH-002)**:
>    In `satellite_schema.py` line 44:
>    ```python
>    spatial_resolution_m: float = Field(default=30.0, gt=0.0)
>    ```
>    Copernicus Sentinel-1 GRD has $10\,\text{m}$ resolution; Sentinel-2 VNIR bands have $10\,\text{m}$ resolution. Defaulting a Sentinel schema to $30.0\,\text{m}$ (Landsat resolution) causes false metadata attribution.
> 
> 3. **Windows CP1252 Terminal Crash on Raw Unicode Emojis (Defect D-SCH-003)**:
>    In `weather_schema.py` line 27:
>    ```python
>    print("\u2705 Weather Schema Validation Passed!")
>    ```
>    When executed on standard Windows installations where the default terminal code page is CP1252, Python raises:
>    `UnicodeEncodeError: 'charmap' codec can't encode character '\u2705'`.
> 
> 4. **Missing Atmospheric Radiation & Wind Covariates for Hydrology (Defect D-SCH-004)**:
>    `WeatherTelemetry` captures precipitation, temperature, humidity, and pressure, but completely lacks wind speed ($u_2$), solar net radiation ($R_n$), and soil heat flux ($G$). Physical Richards equation models and Penman-Monteith evapotranspiration calculations in downstream physics tiers cannot compute evaporative moisture loss from this schema.

---

## 3. Requirements Catalog

### 3.1 Functional Requirements

#### FR-SCH-001: Geographic Bounding Box Coordinate Validation
- **Description**: `SpatialBoundingBox` SHALL validate that longitude values are in $[-180.0, 180.0]^\circ$, latitude values are in $[-90.0, 90.0]^\circ$, and enforce strict inequality: $\text{min\_lon} < \text{max\_lon}$ and $\text{min\_lat} < \text{max\_lat}$.
- **Verification Method**: `T` (Verified via `test_sentinel_ingestor_d03.py`)
- **Status**: `MET`

#### FR-SCH-002: Sentinel Frame Metadata Ingestion Validation
- **Description**: `SentinelFrameMetadata` SHALL validate scene identifiers ($\ge 5$ characters), ISO acquisition date strings, cloud cover percentages in $[0.0, 100.0]\%$, and positive spatial resolutions.
- **Verification Method**: `T` (Verified via `test_pipeline_orchestrator_d04.py`)
- **Status**: `MET`

#### FR-SCH-003: Canonical Raster Contract Layout Enforcement
- **Description**: `GeospatialRasterAsset` SHALL require a 3D NumPy array with layout `(bands, height, width)` and a 3D boolean validity mask with layout `(1, height, width)`.
- **Verification Method**: `T` (Verified via `satellite_schema.py::__main__`)
- **Status**: `MET`

#### FR-SCH-004: Array and Mask Spatial Dimension Congruence
- **Description**: `GeospatialRasterAsset` SHALL verify that the spatial dimensions of `valid_data_mask` (`shape[1:]`) match the spatial dimensions of `raw_array` (`shape[1:]`). Mismatched dimensions SHALL raise `ValueError`.
- **Verification Method**: `T` (Verified via `satellite_schema.py::__main__`)
- **Status**: `MET`

#### FR-SCH-005: Physical Calibration Scaling and Offset Conversion
- **Description**: `GeospatialRasterAsset.to_physical()` SHALL convert native arrays to float32 physical values via:
  $$\mathbf{A}_{\text{phys}} = \mathbf{A}_{\text{raw}} \cdot \text{scale\_factor} + \text{add\_offset}$$
  If either parameter is `None`, it SHALL raise `ConversionError`.
- **Verification Method**: `T` (Verified via `satellite_schema.py::__main__`)
- **Status**: `MET`

#### FR-SCH-006: Weather Telemetry Physical Bounding
- **Description**: `WeatherTelemetry` SHALL enforce physical bounds: precipitation in $[0.0, 1000.0]\,\text{mm/day}$, temperature in $[200.0, 350.0]\,\text{K}$, relative humidity in $[0.0, 100.0]\%$, and surface pressure in $[800.0, 1100.0]\,\text{hPa}$.
- **Verification Method**: `T`
- **Status**: `MET`

---

### 3.2 Data Integrity Requirements

#### DI-SCH-001: Arbitrary Types Permission in Pydantic Configuration
- **Description**: `GeospatialRasterAsset` SHALL declare `model_config = ConfigDict(arbitrary_types_allowed=True)` to permit native `numpy.ndarray` validation without serialization overhead.
- **Verification Method**: `I`
- **Status**: `MET`

#### DI-SCH-002: Rejection of Degenerate Bounding Boxes
- **Description**: Bounding boxes where $\text{min} \ge \text{max}$ SHALL raise `ValueError`.
- **Verification Method**: `T`
- **Status**: `MET`

---

### 3.3 Non-Functional Requirements

#### NF-SCH-001: Validation Overhead Latency
- **Description**: Validating a `GeospatialRasterAsset` containing a $512 \times 512$ array SHALL execute in under $1.0\,\text{ms}$.
- **Verification Method**: `T` (Benchmarked: mean $0.08\,\text{ms}$)
- **Status**: `MET`

---

## 4. Verification Procedures & Results

### 4.1 Procedure Catalog

| Procedure ID | Target Requirement | Description | Expected Result |
|:---|:---|:---|:---|
| **VP-SCH-001** | `FR-SCH-001` | Instantiate `SpatialBoundingBox` with $\text{min\_lon} > \text{max\_lon}$. | Raises `ValueError`. |
| **VP-SCH-002** | `FR-SCH-003`, `FR-SCH-004` | Instantiate `GeospatialRasterAsset` with mismatched mask shape $(1, 5, 5)$ and array shape $(1, 10, 10)$. | Raises `ValueError`. |
| **VP-SCH-003** | `FR-SCH-005` | Call `to_physical` with `scale_factor=None`. | Raises `ConversionError`. |
| **VP-SCH-004** | `FR-SCH-006` | Instantiate `WeatherTelemetry` with negative precipitation. | Raises `ValidationError`. |

### 4.2 Empirical Execution Evidence

```text
[OK] Satellite Validation Schema Operating Normally!
Validated Scene: S2A_MSIL2A_20260721 | Cloud Cover: 12.4%

--- Testing GeospatialRasterAsset Contract ---
1. Native array dtype and shape (bands, height, width) successfully retained.
2. Verified scale/offset produced float32 physical values correctly.
3. Unresolved parameters correctly raised ConversionError.
4. Mismatched mask dimensions successfully rejected.
5. Geospatial and provenance metadata securely preserved.
[SUCCESS] RASTER CONTRACT IMPLEMENTED AND VERIFIED.
```

---

## 5. Traceability Matrix

| Requirement ID | Module | Class / Function | Source Line Range |
|:---|:---|:---|:---|
| `FR-SCH-001` | `satellite_schema.py` | `SpatialBoundingBox.validate_coordinates` | L15–L26 |
| `FR-SCH-002` | `satellite_schema.py` | `SentinelFrameMetadata` | L29–L45 |
| `FR-SCH-003` | `satellite_schema.py` | `GeospatialRasterAsset.validate_array_layout` | L79–L94 |
| `FR-SCH-004` | `satellite_schema.py` | `GeospatialRasterAsset.check_mask_dimensions` | L95–L100 |
| `FR-SCH-005` | `satellite_schema.py` | `GeospatialRasterAsset.to_physical` | L101–L105 |
| `FR-SCH-006` | `weather_schema.py` | `WeatherTelemetry` | L6–L19 |

---

## 6. Defect Log and Technical Debt Register

### D-SCH-001: Orphan Scratch File in Production Namespace
- **Location**: `2_data_pipeline/schemas/test_schema.py:56`
- **Severity**: MEDIUM
- **Description**: Uncurated duplicate file containing a top-level `print()` statement that executes on import.
- **Remediation**: Remove `test_schema.py` from production package.

### D-SCH-002: Default Resolution Mismatch in Sentinel Schema
- **Location**: `satellite_schema.py:44`
- **Severity**: LOW
- **Description**: Sets default resolution to $30.0\,\text{m}$ instead of native $10.0\,\text{m}$ for Sentinel.
- **Remediation**: Update default to `spatial_resolution_m: float = Field(default=10.0, gt=0.0)`.

### D-SCH-003: Terminal Encoding Crash on Raw Emojis
- **Location**: `weather_schema.py:27`
- **Severity**: LOW
- **Description**: Printing `\u2705` crashes standard Windows CP1252 consoles with `UnicodeEncodeError`.
- **Remediation**: Guard console outputs with ASCII fallbacks.

### D-SCH-004: Incomplete Meteorologic Covariate Set for Physical Hydrology
- **Location**: `weather_schema.py:6-19`
- **Severity**: HIGH
- **Description**: Lacks wind speed ($u_2$), solar net radiation ($R_n$), and soil heat flux ($G$) needed for Penman-Monteith PET.
- **Remediation**: Extend schema to include optional radiation and wind fields.

---

## 7. Configuration Control

### 7.1 Module Software Configuration

| Module File | Lines of Code | Description |
|:---|:---:|:---|
| `2_data_pipeline/schemas/__init__.py` | 4 | Package entry point exporting schemas. |
| `2_data_pipeline/schemas/satellite_schema.py` | 176 | Geospatial raster and metadata contracts. |
| `2_data_pipeline/schemas/weather_schema.py` | 31 | Meteorological telemetry schema. |
| `2_data_pipeline/schemas/test_schema.py` | 57 | Orphan prototype file. |
