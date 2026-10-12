# THE MRIDANSH (AETHER-MRID1607X)
# Module: 2_data_pipeline/ingestion
# Requirements, Verification and Configuration Control

---

## 1. Document Control

### 1.1 Identification

| Field | Value |
|:---|:---|
| **Document ID** | MRID-PIPE-ING-DOC-001 |
| **Module Path** | `2_data_pipeline/ingestion/` |
| **Project** | THE MRIDANSH — Unified Soil State Estimation System |
| **System / Engine** | AETHER-MRID1607X (Multi-Domain Soil Intelligence Engine) |
| **Author / Developer** | Gourgopal Mohapatra |
| **Organization** | JCC HEADQUARTER — JCC CAMPUS 2, RS-SDA Division |
| **Reviewer** | *(To be assigned — independent technical reviewer)* |
| **Approver** | *(To be assigned — systems engineering authority)* |
| **Version** | 1.0 |
| **Date** | 2026-10-10 |
| **Status** | Baseline Draft — Unfiltered Technical Audit |
| **Classification** | Proprietary & Controlled Research Artifact |

### 1.2 Revision History

| Version | Date | Author | Description of Change |
|:---|:---|:---|:---|
| 0.1 | 2026-10-10 | Gourgopal Mohapatra | Initial structural decompilation and line-by-line inspection of `stac_client.py`, `sentinel_ingestor.py`, `multisource_ingestor.py`, and `caching_and_resilience.py`. |
| 1.0 | 2026-10-10 | Gourgopal Mohapatra | Formal unfiltered baseline release: complete requirements catalog, empirical test evidence, STAC property bug expose, and comprehensive technical debt register. |

### 1.3 Document Conventions

- **SHALL** indicates a mandatory, verifiable engineering requirement.
- **SHOULD** indicates a recommended design practice or optimization target.
- **MAY** indicates an optional implementation path.
- **Requirement Status Definitions**:
  - `MET`: Requirement verified by passing test suite or empirical execution evidence.
  - `PARTIAL`: Implementation exists but exhibits severe code bugs, swallowed exceptions, architectural mismatches, or missing validations.
  - `NOT MET`: Requirement is completely absent, failing execution, or unhandled.
  - `WAIVED`: Formal departure accepted with recorded technical rationale.
- **Verification Methods**:
  - `T` (Test): Automated execution of unit test suites (`pytest`, `unittest`).
  - `A` (Analysis): Theoretical code inspection, API protocol evaluation, and cryptographic hashing analysis.
  - `I` (Inspection): Line-by-line static manual examination of source code and AST syntax.
  - `D` (Demonstration): Operational network query execution against live endpoints.
- **Identifier Prefix Rules**:
  - `FR-ING-xxx`: Functional Requirement (Ingestion)
  - `DI-ING-xxx`: Data Integrity Requirement (Ingestion)
  - `IF-ING-xxx`: Interface Requirement (Ingestion)
  - `UQ-ING-xxx`: Uncertainty & Quality Requirement (Ingestion)
  - `NF-ING-xxx`: Non-Functional Requirement (Ingestion)
  - `VP-ING-xxx`: Verification Procedure (Ingestion)
  - `D-ING-xxx`: Open Defect / Technical Flaw (Ingestion)
  - `R-ING-xxx`: Technical Risk
  - `A-ING-xxx`: Architectural Assumption

---

## 2. Purpose and Scope

### 2.1 Purpose

This document establishes the formal engineering requirements, verification procedures, test results, bidirectional traceability, and an **unfiltered, brutally transparent technical debt and defect register** for the `2_data_pipeline/ingestion` subsystem within **THE MRIDANSH** (*AETHER-MRID1607X*).

### 2.2 System Context

The `ingestion` package serves as the primary external gateway for acquiring raw Earth Observation (EO) satellite and GIS data:
- **Upstream Sources**: External SpatioTemporal Asset Catalog (STAC) API endpoints (Element84 AWS, Microsoft Planetary Computer), Copernicus Data Space Ecosystem (CDSE), USGS Landsat STAC, and ISRO Bhuvan OGC Web Map Services (WMS).
- **Subsystem Scope**: Consists of four production Python modules:
  1. `stac_client.py`: Low-level wrapper around `pystac_client.Client` querying Sentinel-1 (SAR) and Sentinel-2 (Optical) STAC items.
  2. `sentinel_ingestor.py`: High-level domain service converting raw STAC dictionaries into Pydantic-validated `SentinelFrameMetadata` instances.
  3. `multisource_ingestor.py`: Multi-catalog aggregator querying Landsat-8/9 Collection 2, generating ISRO Bhuvan WMS endpoint strings, and calculating static surface moisture indices (NDVI, NDMI, NDWI).
  4. `caching_and_resilience.py`: Defensive middleware providing SHA256 deterministic response caching, exponential backoff retries, and offline fallback generators.
- **Downstream Consumers**: Feeds validated asset URLs and metadata into `2_data_pipeline/preprocessing/` (`cog_processor.py`, `raster_processor.py`) and `2_data_pipeline/fusion/` (`satellite_fusion.py`).

### 2.3 Module Objective

The objective of `ingestion` is to reliably discover, validate, cache, and index multi-sensor raster assets across space and time for any user-defined bounding box (`SpatialBoundingBox`) without data loss, blocking exceptions, or unhandled rate limits.

### 2.4 In Scope

- All source files within `2_data_pipeline/ingestion/`:
  - `__init__.py` (13 lines)
  - `stac_client.py` (170 lines)
  - `sentinel_ingestor.py` (101 lines)
  - `multisource_ingestor.py` (192 lines)
  - `caching_and_resilience.py` (153 lines)
- Test suite: `tests/test_sentinel_ingestor_d03.py` (4 tests).
- Local disk cache management under directory `.cache/satellite_data/`.

### 2.5 Out of Scope

- Cloud-Optimized GeoTIFF (COG) byte-range HTTP window reading (delegated to `preprocessing/cog_processor.py`).
- Coordinate Reference System (CRS) reprojective warping (delegated to `preprocessing/raster_processor.py`).
- Model inference or temporal Kalman filtering.

### 2.6 Current-State Declaration (Mandatory Unfiltered Engineering Disclosure)

> [!CAUTION]
> **MANDATORY UNFILTERED AUDIT DECLARATION: CRITICAL FLAWS & ARCHITECTURAL GAPS**
> 
> A ruthless inspection of the `ingestion` codebase reveals severe implementation defects, silent failure patterns, and architectural inconsistencies that must be transparently exposed:
> 
> 1. **STAC Property Typo Bug (Defect D-ING-001)**: In `stac_client.py` line 123–125:
>    ```python
>    "orbit_direction": item.properties.get("sat.orbit_state", "descending")
>    ```
>    The official STAC specification defines orbit state as `"sat:orbit_state"` (with a colon) or `"orbit_direction"`. Because the code queries `"sat.orbit_state"` with a **period/dot**, `item.properties.get()` **always fails to find the key** and silently falls back to `"descending"`. Every Sentinel-1 scene is erroneously reported as "descending", even ascending passes!
> 
> 2. **Inability to Ingest Dual-Polarization (Defect D-ING-002)**: In `sentinel_ingestor.py` lines 66–67:
>    ```python
>    target_pol = "VV" if "VV" in polarization else "VH"
>    ```
>    When the user requests `"VV+VH"`, the code collapses the request to a single polarization (`VV`) and extracts exactly one asset HREF. Consequently, it is **physically impossible** for `sentinel_ingestor.py` to deliver both VV and VH channels in a single frame, directly breaking the contract required by `satellite_fusion.py` to compute `SAR_POL_RATIO = SAR_VH / (SAR_VV + 1e-6)`.
> 
> 3. **Hardcoded Asset Keys Breaking Non-AWS Catalogs (Defect D-ING-003)**: In `stac_client.py` lines 61–73, asset extraction hardcodes keys `red`, `nir`, `swir16`, `visual`. These key names are unique to Element84 Earth Search v1. Standard ESA Copernicus CDSE or Planetary Computer catalogs use band identifiers (`B04`, `B08`, `B11`, `TCI`). If any user configures a different STAC catalog URL, `stac_client.py` returns all asset HREFs as `None`, silently rendering the query useless.
> 
> 4. **Swallowed Exceptions in Landsat STAC Search (Defect D-ING-004)**: In `multisource_ingestor.py` lines 41–54:
>    ```python
>    try:
>        search = self.stac_client.search(collections=["landsat-c2-l2"], ...)
>        items = list(search.items())
>    except Exception:
>        items = []
>    ```
>    The code defaults `stac_client` to `ELEMENT84_STAC_URL`, which does **not host Landsat Collection 2**. When the query fails, it catches all `Exception` instances blindly without logging, swallowing the error and silently returning `[]`.
> 
> 5. **Unauthenticated Planetary & S3 Asset URLs (Defect D-ING-005)**: The asset HREFs extracted by `multisource_ingestor.py` from Planetary Computer or AWS requesters require SAS token signing (`planetary_computer.sign()`) or AWS credentials. The ingestor does not perform token signing; any downstream attempt to read these raw HREFs results in immediate `HTTP 403 Forbidden`.
> 
> 6. **Bhuvan WMS is a Dummy String Generator (Defect D-ING-006)**: Method `get_bhuvan_wms_layer_config` in `multisource_ingestor.py` executes **no network request**. It merely performs string concatenation to format a WMS GetMap URL. It does not parse capabilities, does not validate layer existence, and does not download imagery.
> 
> 7. **Destructive Precision Truncation in Spectral Indices (Defect D-ING-007)**: In `multisource_ingestor.py` lines 139–141, the indices are rounded via `np.round(..., 4)`. Truncating float32 satellite bands to 4 decimal places prematurely destroys numerical gradient precision required for deep neural backpropagation in `3_core_engine`.
> 
> 8. **Cache Key Serialization Crash on Pydantic Types (Defect D-ING-008)**: In `caching_and_resilience.py` line 26:
>    ```python
>    json.dumps({"endpoint": endpoint_name, "params": params}, sort_keys=True)
>    ```
>    `json.dumps()` crashes with `TypeError` if `params` contains any non-primitive object (such as `SpatialBoundingBox`, `Path`, `datetime`, or `numpy.ndarray`).
> 
> 9. **Zero Test Coverage for Resilience and MultiSource (Defect D-ING-009)**: In the test directory `tests/`, only `test_sentinel_ingestor_d03.py` exists (testing mocked `SentinelDataIngestor`). There are **zero unit tests** for `multisource_ingestor.py` and **zero unit tests** for `caching_and_resilience.py`.

---

## 3. Definitions and Abbreviations

| Term / Abbreviation | Definition |
|:---|:---|
| **STAC** | SpatioTemporal Asset Catalog specification (JSON metadata for geospatial assets). |
| **Element84** | Public AWS STAC catalog endpoint hosting Sentinel-2 L2A and Sentinel-1 GRD. |
| **CDSE** | Copernicus Data Space Ecosystem (official ESA satellite distribution portal). |
| **GRD** | Ground Range Detected SAR radar product (amplitude backscatter). |
| **L2A** | Level-2A Bottom-Of-Atmosphere (BOA) surface reflectance optical product. |
| **WMS** | OGC Web Map Service standard for rendering geographic map images. |
| **Bhuvan** | Indian Space Research Organisation (ISRO) geospatial geoportal. |
| **NDVI** | Normalized Difference Vegetation Index: $(\text{NIR} - \text{Red}) / (\text{NIR} + \text{Red})$. |
| **NDMI** | Normalized Difference Moisture Index: $(\text{NIR} - \text{SWIR}) / (\text{NIR} + \text{SWIR})$. |
| **NDWI** | Normalized Difference Water Index: $(\text{Green} - \text{NIR}) / (\text{Green} + \text{NIR})$. |
| **Backoff** | Exponential wait time multiplier between consecutive retry attempts. |
| **JCC RS-SDA** | Jagannath Command Center — Remote Sensing & Spatial Data Analytics Division. |

---

## 4. Requirements

### 4.1 Functional Requirements

- **FR-ING-001**: The software shall implement `SatelliteSTACClient` interfacing with STAC catalogs, defaulting to `https://earth-search.aws.element84.com/v1`.
- **FR-ING-002**: The software shall query Sentinel-2 L2A optical scenes filtering by bounding box `bbox`, date range `datetime_range`, and cloud cover threshold `max_cloud_cover` via STAC collection `sentinel-2-l2a`.
- **FR-ING-003**: The software shall extract optical band asset HREFs for `red`, `nir`, `swir16`, and `visual`.
- **FR-ING-004**: The software shall query Sentinel-1 GRD radar scenes filtering by bounding box `bbox` and date range `datetime_range` via STAC collection `sentinel-1-grd`.
- **FR-ING-005**: The software shall extract SAR radar asset HREFs matching requested polarization substrings (`VV` or `VH`).
- **FR-ING-006**: The software shall implement `SentinelDataIngestor` orchestrating high-level optical and radar frame discovery.
- **FR-ING-007**: The software shall wrap extracted STAC metadata into Pydantic-validated `SentinelFrameMetadata` schema objects.
- **FR-ING-008**: The software shall silently drop invalid or `None` asset HREFs, returning only frames with at least one active asset.
- **FR-ING-009**: The software shall implement `MultiSourceIngestor` supporting secondary satellite catalogs (Landsat 8/9 C2 and ISRO Bhuvan WMS).
- **FR-ING-010**: The software shall query Landsat Collection 2 Level-2 scenes via STAC collection `landsat-c2-l2` extracting `red`, `nir08`, `swir16`, and `lwir11` assets.
- **FR-ING-011**: The software shall construct ISRO Bhuvan OGC WMS GetMap URLs formatting layer names, EPSG:4326 bounding boxes, and $512 \times 512$ PNG image dimensions.
- **FR-ING-012**: The software shall implement static method `compute_spectral_indices(red, nir, swir, green)` computing NDVI, NDMI, and NDWI.
- **FR-ING-013**: The software shall prevent zero-division in spectral indices using an epsilon stabilizer $\epsilon = 10^{-8}$ and clip results to $[-1.0, 1.0]$.
- **FR-ING-014**: The software shall implement `ResilientSatelliteIngestor` managing disk caching, retries, and offline fallbacks.
- **FR-ING-015**: The software shall generate a deterministic SHA256 cache key from endpoint names and sorted query parameter dictionaries.
- **FR-ING-016**: The software shall implement exponential backoff retries doubling delay intervals ($1.0\text{ s}, 2.0\text{ s}, 4.0\text{ s}$) up to `max_retries` attempts before triggering fallback generators.

### 4.2 Data Integrity Requirements

- **DI-ING-001**: Geographic Coordinate Enclosure: All bounding boxes shall conform to valid WGS84 limits: $-180 \le \text{lon} \le 180$ and $-90 \le \text{lat} \le 90$ with $\text{min} < \text{max}$.
- **DI-ING-002**: Index Value Bounding: All computed spectral indices (NDVI, NDMI, NDWI) shall strictly lie within the closed domain $[-1.0, 1.0]$.
- **DI-ING-003**: Deterministic Cache Keys: Repeated serialization of identical query parameters shall produce bit-exact identical SHA256 hashes.
- **DI-ING-004**: Source Origin Provenance: All responses returned by `ResilientSatelliteIngestor` shall be stamped with a `_source` origin tag (`LOCAL_DISK_CACHE`, `LIVE_API_NETWORK`, or `OFFLINE FALLBACK_ENGINE`).
- **DI-ING-005**: Resolution Integrity: `SentinelFrameMetadata` shall enforce positive spatial resolutions (`spatial_resolution_m > 0.0`).
- **DI-ING-006**: Cloud Cover Boundaries: Cloud cover percentages shall be strictly validated within $[0.0, 100.0]\%$.

### 4.3 Interface Requirements

- **IF-ING-001**: `SatelliteSTACClient.search_sentinel2_optical` signature: `(bbox: list[float], start_date: str, end_date: str, max_cloud_cover: float = 20.0, limit: int = 5) -> list[dict[str, Any]]`.
- **IF-ING-002**: `SatelliteSTACClient.search_sentinel1_sar` signature: `(bbox: list[float], start_date: str, end_date: str, polarization: str = "VV", limit: int = 5) -> list[dict[str, Any]]`.
- **IF-ING-003**: `SentinelDataIngestor.fetch_optical_frames` signature: `(bbox: SpatialBoundingBox, start_date: str, end_date: str, max_cloud_cover: float = 20.0) -> list[SentinelFrameMetadata]`.
- **IF-ING-004**: `SentinelDataIngestor.fetch_radar_sar_frames` signature: `(bbox: SpatialBoundingBox, start_date: str, end_date: str, polarization: str = "VV+VH") -> list[SentinelFrameMetadata]`.
- **IF-ING-005**: `MultiSourceIngestor.compute_spectral_indices` signature: `(red: np.ndarray, nir: np.ndarray, swir: np.ndarray, green: np.ndarray | None = None) -> dict[str, np.ndarray]`.

### 4.4 Uncertainty / Quality Requirements

- **UQ-ING-001**: Optical scene ingestion shall explicitly extract the cloud cover metadata attribute to enable downstream atmospheric uncertainty estimation.
- **UQ-ING-002**: When green band reflectance is unavailable (`green is None`), `compute_spectral_indices` shall return a zero-array for NDWI rather than unhandled exceptions.
- **UQ-ING-003**: Radar scene ingestion shall report `cloud_cover_percentage = 0.0` reflecting C-band radar cloud penetration.
- **UQ-ING-004**: Failure resilience shall execute a minimum of 3 retry attempts before declaring network timeout.

### 4.5 Non-Functional Requirements

- **NF-ING-001**: Directory Auto-Creation: The cache manager shall automatically create directory trees if `.cache/satellite_data` does not exist.
- **NF-ING-002**: Zero Live Network Dependency in Unit Tests: Unit tests in `tests/test_sentinel_ingestor_d03.py` shall utilize `unittest.mock.MagicMock` to ensure deterministic execution offline.
- **NF-ING-003**: Pure Python Execution: Ingestion routines shall execute without GPU dependencies across Linux and Windows environments.
- **NF-ING-004**: Execution Latency: Mocked frame ingestion shall evaluate in $< 50\text{ ms}$.

---

## 5. Requirements Attributes

| ID | Requirement Statement | Rationale | Method | Acceptance Criterion | Status |
|:---|:---|:---|:---:|:---|:---:|
| **FR-ING-001** | STAC Client wrapper initialization. | Standardizes STAC endpoint connectivity. | I/T | Connects to Element84 URL. | **MET** |
| **FR-ING-002** | Search Sentinel-2 L2A optical scenes. | Optical satellite discovery. | T | Query filters bbox, date, cloud cover. | **MET** |
| **FR-ING-003** | Extract optical band asset HREFs. | Data asset link extraction. | T | Maps `red`, `nir`, `swir16`, `visual`. | **PARTIAL (D-ING-003)** |
| **FR-ING-004** | Search Sentinel-1 GRD SAR scenes. | Radar satellite discovery. | T | Query filters bbox, date, collection. | **MET** |
| **FR-ING-005** | Extract SAR asset HREFs by polarization. | Polarimetric data asset extraction. | T | Finds matching polarization substring. | **PARTIAL (D-ING-001, 002)** |
| **FR-ING-006** | Orchestrate high-level Sentinel ingestion. | Bridges STAC to typed schemas. | T | `SentinelDataIngestor` initialized. | **MET** |
| **FR-ING-007** | Populate `SentinelFrameMetadata` schema. | Pydantic validation enforcement. | T | Returns valid `SentinelFrameMetadata` list. | **MET** |
| **FR-ING-008** | Drop None/invalid asset HREFs. | Prevents broken downstream downloads. | T | Verified by `test_stac_03_empty_handling`. | **MET** |
| **FR-ING-009** | MultiSourceIngestor multi-catalog engine. | Extensibility across non-ESA sources. | I | Class instantiated with catalog URLs. | **MET** |
| **FR-ING-010** | Search Landsat Collection 2 via STAC. | Landsat 8/9 data discovery. | I | Queries `landsat-c2-l2`. | **PARTIAL (D-ING-004, 005)** |
| **FR-ING-011** | Construct ISRO Bhuvan WMS GetMap URLs. | Regional Indian soil/GIS overlays. | I/T | Generates valid GetMap string. | **PARTIAL (D-ING-006)** |
| **FR-ING-012** | Compute NDVI, NDMI, NDWI spectral indices. | EO surface feature derivation. | T | Returns dictionary with 3 index arrays. | **PARTIAL (D-ING-007)** |
| **FR-ING-013** | Epsilon stabilizer $\epsilon=10^{-8}$ and clipping. | Numerical stability assurance. | T | Values clipped $[-1.0, 1.0]$. | **MET** |
| **FR-ING-014** | ResilientSatelliteIngestor caching & retries. | Network resilience & offline survival. | I | Wrapper class implemented. | **PARTIAL (D-ING-008, 009)** |
| **FR-ING-015** | Deterministic SHA256 cache key generation. | Collision-free cache lookup. | I/A | Key generated via `hashlib.sha256`. | **PARTIAL (D-ING-008)** |
| **FR-ING-016** | Exponential backoff retry loop ($1\text{s}, 2\text{s}, 4\text{s}$). | Prevents server rate-limit bans. | I | `time.sleep(backoff_delay)` implemented. | **MET** |
| **DI-ING-001** | WGS84 bounding box validation. | Geographic validity contract. | T | Verified by `SpatialBoundingBox`. | **MET** |
| **DI-ING-002** | Spectral index values bounded $[-1, 1]$. | Physical mathematical bound. | T | `np.clip(..., -1.0, 1.0)` verified. | **MET** |
| **DI-ING-003** | Deterministic SHA256 cache key hashes. | Repeatable offline retrieval. | A | Sorted JSON parameter hashing. | **MET** |
| **DI-ING-004** | Response provenance tagging (`_source`). | Traceability of payload origin. | I | `result["_source"]` assigned. | **MET** |
| **DI-ING-005** | Positive spatial resolution validation. | Physical scale integrity. | T | Schema rejects resolution $\le 0$. | **MET** |
| **DI-ING-006** | Cloud cover bounded in $[0, 100]\%$. | Statistical percentage integrity. | T | Schema rejects out-of-range clouds. | **MET** |
| **IF-ING-001** | `search_sentinel2_optical` signature. | API interface contract. | I/T | Signature matches specification. | **MET** |
| **IF-ING-002** | `search_sentinel1_sar` signature. | API interface contract. | I/T | Signature matches specification. | **MET** |
| **IF-ING-003** | `fetch_optical_frames` signature. | Domain service interface contract. | T | Verified by `test_stac_01`. | **MET** |
| **IF-ING-004** | `fetch_radar_sar_frames` signature. | Domain service interface contract. | T | Verified by `test_stac_02`. | **MET** |
| **IF-ING-005** | `compute_spectral_indices` signature. | Index generator interface contract. | T | Verified via test arrays. | **MET** |
| **UQ-ING-001** | Optical cloud cover metadata retention. | Atmospheric UQ input tracking. | T | Stored in `cloud_cover_percentage`. | **MET** |
| **UQ-ING-002** | NDWI fallback to zeros when green missing. | Graceful degradation under missing band. | T | Returns `zeros_like` when `green is None`. | **MET** |
| **UQ-ING-003** | Radar cloud cover set to 0.0. | Physical radar penetration assumption. | I/T | Hardcoded `0.0` in SAR frames. | **MET** |
| **UQ-ING-004** | Minimum 3 retry attempts before failure. | Network resilience policy. | I | Default `max_retries = 3`. | **MET** |
| **NF-ING-001** | Cache directory auto-creation on init. | Filesystem resilience. | I/T | `Path.mkdir(parents=True, exist_ok=True)`. | **MET** |
| **NF-ING-002** | Mocked unit test isolation. | CI/CD offline reproducibility. | T | `unittest.mock.MagicMock` in test suite. | **MET** |
| **NF-ING-003** | Pure CPU Python execution. | Edge and server portability. | I/T | Runs without CUDA acceleration. | **MET** |
| **NF-ING-004** | Mocked execution latency $< 50\text{ ms}$. | High-throughput ingestion. | T | Unit tests execute in $< 0.05\text{ s}$. | **MET** |

---

## 6. Verification Procedures

### VP-ING-001: Mocked Optical STAC Response Parsing & Schema Mapping
- **Verifies**: FR-ING-002, FR-ING-003, FR-ING-006, FR-ING-007, FR-ING-008, IF-ING-003, UQ-ING-001
- **Setup**: Python 3.10+ with `unittest` using `tests/test_sentinel_ingestor_d03.py::test_stac_01_mocked_response`.
- **Procedure**:
  1. Mock `SatelliteSTACClient.search_sentinel2_optical` returning a synthetic scene with `red`, `nir`, and `swir16: None`.
  2. Invoke `SentinelDataIngestor.fetch_optical_frames`.
  3. Validate that `scene_id == "MOCK_SCENE_1"`, `acquisition_date == "2026-01-15"`, `red` asset is retained, and `swir16` is dropped.
- **Expected Result**: Single `SentinelFrameMetadata` instance returned with 2 valid bands and valid HREFs.
- **Pass/Fail Criterion**: PASS if `len(results) == 1` and `"swir16" not in frame.asset_hrefs`.

### VP-ING-002: Bounding Box and Date Parameter Passing Integrity
- **Verifies**: FR-ING-004, FR-ING-005, IF-ING-004, DI-ING-001
- **Setup**: `tests/test_sentinel_ingestor_d03.py::test_stac_02_parameter_passing`.
- **Procedure**:
  1. Mock `SatelliteSTACClient.search_sentinel1_sar`.
  2. Invoke `SentinelDataIngestor.fetch_radar_sar_frames` with `SpatialBoundingBox(bbox=(85.75, 20.20, 85.90, 20.35))`.
  3. Assert `search_sentinel1_sar.assert_called_once_with` receives exact bounding box list and date strings.
- **Expected Result**: Parameter conversion from Pydantic tuple to list without mutation.
- **Pass/Fail Criterion**: PASS if arguments match exactly.

### VP-ING-003: Empty Search Handling and Zero-Asset Pruning
- **Verifies**: FR-ING-008, UQ-ING-002
- **Setup**: `tests/test_sentinel_ingestor_d03.py::test_stac_03_empty_handling`.
- **Procedure**:
  1. Return empty list `[]` from mock STAC search.
  2. Assert `fetch_optical_frames` returns `[]`.
  3. Return item with `{"assets": {"red": None}}`.
  4. Assert `fetch_optical_frames` returns `[]` (prunes frames with zero active assets).
- **Expected Result**: Graceful empty list return without unhandled exceptions.
- **Pass/Fail Criterion**: PASS if both calls return empty lists.

### VP-ING-004: Live STAC Endpoint Smoke Query
- **Verifies**: FR-ING-001, FR-ING-002, NF-ING-003
- **Setup**: `tests/test_sentinel_ingestor_d03.py::test_stac_04_live_smoke`.
- **Procedure**:
  1. Instantiate real `SatelliteSTACClient()` connecting to Element84 Earth Search v1.
  2. Execute query over Bhubaneswar bounding box for dates `2023-01-01` to `2023-01-31`.
- **Expected Result**: Connection succeeds over HTTPS; returns real STAC items or gracefully handles network unavailability.
- **Pass/Fail Criterion**: PASS if HTTP query executes without unhandled JSON deserialization crashes.

### VP-ING-005: Orbit State Property Typo Bug Verification (Exposing D-ING-001)
- **Verifies**: D-ING-001
- **Setup**: Manual code inspection and AST evaluation of `stac_client.py` line 123.
- **Procedure**:
  1. Inspect `item.properties.get("sat.orbit_state", "descending")`.
  2. Contrast against official STAC Sat Extension spec (`sat:orbit_state`).
- **Expected Result**: Query with period (`.`) fails to match colon (`:`) key in STAC properties dictionary, always returning default `"descending"`.
- **Pass/Fail Criterion**: Confirmed defect logged.

### VP-ING-006: Dual-Polarization SAR Collapse Bug Verification (Exposing D-ING-002)
- **Verifies**: D-ING-002
- **Setup**: Inspect lines 66–67 of `sentinel_ingestor.py`.
- **Procedure**:
  1. Evaluate `target_pol = "VV" if "VV" in polarization else "VH"` with `polarization = "VV+VH"`.
  2. Check resulting `bands_available` and `asset_hrefs`.
- **Expected Result**: Only `VV` is fetched; `VH` is dropped, rendering polarimetric ratio calculation impossible.
- **Pass/Fail Criterion**: Confirmed defect logged.

### VP-ING-007: Spectral Indices Calculation and Decimal Precision Audit
- **Verifies**: FR-ING-012, FR-ING-013, DI-ING-002, D-ING-007
- **Setup**: Execute `MultiSourceIngestor.compute_spectral_indices` on mock arrays.
- **Procedure**:
  1. Input `red`, `nir`, `swir`, `green` random arrays in $[0.05, 0.70]$.
  2. Compute NDVI, NDMI, NDWI.
  3. Validate range $[-1.0, 1.0]$.
  4. Inspect decimal precision of output arrays.
- **Expected Result**: Indices computed within $[-1.0, 1.0]$, but truncated to 4 decimal places via `np.round(..., 4)`.
- **Pass/Fail Criterion**: Precision truncation defect documented.

### VP-ING-008: Cache Resilience SHA256 Key Collision & Serialization Audit
- **Verifies**: FR-ING-014, FR-ING-015, DI-ING-003, D-ING-008
- **Setup**: Execute `ResilientSatelliteIngestor._generate_cache_key`.
- **Procedure**:
  1. Test primitive dictionary params: verify deterministic 64-character hex hash.
  2. Test non-primitive params (e.g. `SpatialBoundingBox`): verify `TypeError` crash.
- **Expected Result**: Crashes when non-JSON primitives are passed to `_generate_cache_key`.
- **Pass/Fail Criterion**: Serialization vulnerability confirmed and logged.

---

## 7. Verification Results

| VP | Date | Executor | Result | Empirical Evidence | Reviewer |
|:---:|:---:|:---:|:---:|:---|:---:|
| **VP-ING-001** | 2026-10-10 | Automated / PyTest | **PASS** | `test_stac_01_mocked_response`: `len(results)==1`, `frame.scene_id=='MOCK_SCENE_1'`, `swir16` dropped. | Pipeline Audit |
| **VP-ING-002** | 2026-10-10 | Automated / PyTest | **PASS** | `test_stac_02_parameter_passing`: `search_sentinel1_sar` called with `[85.75, 20.2, 85.9, 20.35]`, `limit=5`. | Pipeline Audit |
| **VP-ING-003** | 2026-10-10 | Automated / PyTest | **PASS** | `test_stac_03_empty_handling`: Both empty searches and frames with `None` assets return `[]`. | Pipeline Audit |
| **VP-ING-004** | 2026-10-10 | Automated / PyTest | **PASS** | `test_stac_04_live_smoke`: Live Element84 query executed without uncaught network exceptions. | Pipeline Audit |
| **VP-ING-005** | 2026-10-10 | Manual Inspection | **FAIL (DEFECT)** | `stac_client.py:123` queries `"sat.orbit_state"` (dot) instead of `"sat:orbit_state"` (colon). | Code Review |
| **VP-ING-006** | 2026-10-10 | Manual Inspection | **FAIL (DEFECT)** | `sentinel_ingestor.py:66` collapses `"VV+VH"` to `"VV"`, dropping VH asset entirely. | Code Review |
| **VP-ING-007** | 2026-10-10 | Script Execution | **PASS (PARTIAL)** | Indices bounded in $[-1, 1]$, but `np.round(..., 4)` truncates downstream neural float32 precision. | Pipeline Audit |
| **VP-ING-008** | 2026-10-10 | Script Execution | **FAIL (DEFECT)** | `_generate_cache_key` crashes with `TypeError` when `SpatialBoundingBox` is passed. | Code Review |

---

## 8. Requirements Traceability Matrix

| Requirement ID | Source File & Function | Verification Procedure | Verification Result |
|:---|:---|:---:|:---:|
| **FR-ING-001** | `stac_client.py::SatelliteSTACClient.__init__` | VP-ING-004 | **PASS** |
| **FR-ING-002** | `stac_client.py::search_sentinel2_optical` | VP-ING-001, VP-ING-004 | **PASS** |
| **FR-ING-003** | `stac_client.py::search_sentinel2_optical` | VP-ING-001 | **PARTIAL (D-ING-003)** |
| **FR-ING-004** | `stac_client.py::search_sentinel1_sar` | VP-ING-002, VP-ING-004 | **PASS** |
| **FR-ING-005** | `stac_client.py::search_sentinel1_sar` | VP-ING-002, VP-ING-005 | **PARTIAL (D-ING-001, 002)** |
| **FR-ING-006** | `sentinel_ingestor.py::SentinelDataIngestor` | VP-ING-001, VP-ING-002 | **PASS** |
| **FR-ING-007** | `sentinel_ingestor.py::fetch_optical_frames` | VP-ING-001 | **PASS** |
| **FR-ING-008** | `sentinel_ingestor.py::fetch_optical_frames` | VP-ING-003 | **PASS** |
| **FR-ING-009** | `multisource_ingestor.py::MultiSourceIngestor` | VP-ING-007 | **PASS** |
| **FR-ING-010** | `multisource_ingestor.py::search_landsat_multispectral` | Code Inspection | **PARTIAL (D-ING-004, 005)** |
| **FR-ING-011** | `multisource_ingestor.py::get_bhuvan_wms_layer_config` | Code Inspection | **PARTIAL (D-ING-006)** |
| **FR-ING-012** | `multisource_ingestor.py::compute_spectral_indices` | VP-ING-007 | **PARTIAL (D-ING-007)** |
| **FR-ING-013** | `multisource_ingestor.py::compute_spectral_indices` | VP-ING-007 | **PASS** |
| **FR-ING-014** | `caching_and_resilience.py::ResilientSatelliteIngestor` | VP-ING-008 | **PARTIAL (D-ING-008, 009)** |
| **FR-ING-015** | `caching_and_resilience.py::_generate_cache_key` | VP-ING-008 | **PARTIAL (D-ING-008)** |
| **FR-ING-016** | `caching_and_resilience.py::execute_with_resilience` | Code Inspection | **PASS** |
| **DI-ING-001** | `schemas/satellite_schema.py::SpatialBoundingBox` | VP-ING-002 | **PASS** |
| **DI-ING-002** | `multisource_ingestor.py::compute_spectral_indices` | VP-ING-007 | **PASS** |
| **DI-ING-003** | `caching_and_resilience.py::_generate_cache_key` | VP-ING-008 | **PASS** |
| **DI-ING-004** | `caching_and_resilience.py::execute_with_resilience` | Code Inspection | **PASS** |
| **DI-ING-005** | `schemas/satellite_schema.py::SentinelFrameMetadata` | VP-ING-001 | **PASS** |
| **DI-ING-006** | `schemas/satellite_schema.py::SentinelFrameMetadata` | VP-ING-001 | **PASS** |
| **IF-ING-001** | `stac_client.py::search_sentinel2_optical` | VP-ING-001 | **PASS** |
| **IF-ING-002** | `stac_client.py::search_sentinel1_sar` | VP-ING-002 | **PASS** |
| **IF-ING-003** | `sentinel_ingestor.py::fetch_optical_frames` | VP-ING-001 | **PASS** |
| **IF-ING-004** | `sentinel_ingestor.py::fetch_radar_sar_frames` | VP-ING-002 | **PASS** |
| **IF-ING-005** | `multisource_ingestor.py::compute_spectral_indices` | VP-ING-007 | **PASS** |
| **UQ-ING-001** | `sentinel_ingestor.py::fetch_optical_frames` | VP-ING-001 | **PASS** |
| **UQ-ING-002** | `multisource_ingestor.py::compute_spectral_indices` | VP-ING-007 | **PASS** |
| **UQ-ING-003** | `sentinel_ingestor.py::fetch_radar_sar_frames` | Code Inspection | **PASS** |
| **UQ-ING-004** | `caching_and_resilience.py::ResilientSatelliteIngestor` | Code Inspection | **PASS** |
| **NF-ING-001** | `caching_and_resilience.py::__init__` | Code Inspection | **PASS** |
| **NF-ING-002** | `tests/test_sentinel_ingestor_d03.py` | VP-ING-001 to 003 | **PASS** |
| **NF-ING-003** | Ingestion module scripts | System Execution | **PASS** |
| **NF-ING-004** | `tests/test_sentinel_ingestor_d03.py` | Automated Execution | **PASS** |

---

## 9. Configuration and Change Control

### 9.1 Controlled Items

1. **Source Code**:
   - `2_data_pipeline/ingestion/__init__.py`
   - `2_data_pipeline/ingestion/stac_client.py`
   - `2_data_pipeline/ingestion/sentinel_ingestor.py`
   - `2_data_pipeline/ingestion/multisource_ingestor.py`
   - `2_data_pipeline/ingestion/caching_and_resilience.py`
2. **Requirements Baseline**: `8_docs/02_data_pipeline/ingestion/ingestion_REQUIREMENTS.md`
3. **Technical Description**: `8_docs/02_data_pipeline/ingestion/ingestion.rst`
4. **Unit Tests**: `tests/test_sentinel_ingestor_d03.py`

### 9.2 Baseline Identification

- **Baseline ID**: `PIPE-ING-BL-01`
- **Configuration Tag**: `v1.0-data-pipeline-ingestion`
- **Effective Date**: 2026-10-10

### 9.3 Change Procedure

```text
Change Request (CR)
       │
       ▼
Impact Analysis (Assessing effect on STAC schemas, polarization, caching & fusion)
       │
       ▼
Technical Approval (Division Lead & Chief Systems Engineer)
       │
       ▼
Implementation (Code update in 2_data_pipeline/ingestion/)
       │
       ▼
Re-verification (Full execution of VP-ING-001 through VP-ING-008 & pytest)
       │
       ▼
Baseline Update (Version bump in MD, RST, and Git history)
```

---

## 10. Open Defects and Technical Debt Register

| ID | Description | Affected Requirement | Severity | Status | Corrective Action Required |
|:---:|:---|:---:|:---:|:---:|:---|
| **D-ING-001** | **STAC Orbit State Property Typo Bug**: In `stac_client.py` line 123, code queries `item.properties.get("sat.orbit_state", "descending")`. In STAC specification, the key is `"sat:orbit_state"` (colon). The query always fails and defaults to `"descending"`, corrupting orbit metadata. | FR-ING-005 | **HIGH** | `OPEN` | Change key to `"sat:orbit_state"` and support fallback to `"orbit_direction"`. |
| **D-ING-002** | **Dual-Polarization (VV+VH) Collapse**: In `sentinel_ingestor.py` line 66, when `"VV+VH"` is requested, `target_pol` collapses to `"VV"`, fetching only one channel. Downstream `satellite_fusion.py` requires both VV and VH to compute `SAR_POL_RATIO`. | FR-ING-005, IF-ING-004 | **CRITICAL** | `OPEN` | Refactor `search_sentinel1_sar` and `fetch_radar_sar_frames` to discover and return both VV and VH asset HREFs simultaneously. |
| **D-ING-003** | **Hardcoded Element84 STAC Asset Names**: In `stac_client.py` lines 61–73, assets are hardcoded as `red`, `nir`, `swir16`, `visual`. Other STAC endpoints (CDSE, Planetary Computer) use `B04`, `B08`, `B11`, `TCI`. Non-AWS endpoints return `None` for all bands. | FR-ING-003 | **HIGH** | `OPEN` | Implement asset aliasing dictionary mapping common band names (`B04` $\to$ `red`, `B08` $\to$ `nir`). |
| **D-ING-004** | **Blind Exception Swallowing in Landsat Search**: In `multisource_ingestor.py` line 51, `except Exception:` catches all errors without logging and returns `[]`. Querying Element84 for `landsat-c2-l2` fails silently. | FR-ING-010 | **HIGH** | `OPEN` | Route Landsat queries exclusively to Microsoft Planetary Computer STAC and log explicit warning messages on failures. |
| **D-ING-005** | **Unauthenticated / Unsigned Asset HREFs**: Planetary Computer and AWS Requester Pays require SAS token signing (`planetary_computer.sign()`) or AWS SigV4. Ingestor returns raw unsigned URLs that return HTTP 403 when downloaded. | FR-ING-010 | **CRITICAL** | `OPEN` | Integrate URL signing middleware prior to returning asset dictionaries. |
| **D-ING-006** | **Bhuvan WMS is a Non-Functional String Generator**: Method `get_bhuvan_wms_layer_config` merely formats a URL string; it never performs network GET or image downloading. | FR-ING-011 | **MEDIUM** | `OPEN` | Implement actual WMS raster download and GeoTIFF conversion via `OWSLib.wms`. |
| **D-ING-007** | **Destructive 4-Decimal Rounding in Spectral Indices**: `compute_spectral_indices` applies `np.round(..., 4)`, truncating float32 precision and harming downstream neural gradient propagation. | FR-ING-012 | **MEDIUM** | `OPEN` | Remove `np.round` and retain native `float32` precision. |
| **D-ING-008** | **Cache Key Serialization Crash on Non-Primitives**: `_generate_cache_key` calls `json.dumps` on raw `params`. If `params` contains `SpatialBoundingBox`, `Path`, or `numpy` objects, it crashes with `TypeError`. | FR-ING-015 | **HIGH** | `OPEN` | Add custom JSON encoder handling Pydantic models, tuples, and datetime objects. |
| **D-ING-009** | **Zero Unit Test Coverage for MultiSource & Resilience**: `multisource_ingestor.py` and `caching_and_resilience.py` have zero unit test files in `tests/`. | NF-ING-002 | **HIGH** | `OPEN` | Author `test_multisource_ingestor.py` and `test_caching_and_resilience.py`. |

---

## 11. Risks and Assumptions

### 11.1 Risks

- **R-ING-001 (Single Point of Catalog Failure)**: Reliance on AWS Element84 (`earth-search.aws.element84.com`) means any AWS outage or API schema deprecation breaks all ingestion.
- **R-ING-002 (Downstream Fusion Starvation)**: Due to defect D-ING-002, `sentinel_ingestor.py` cannot supply dual-pol radar arrays, forcing `satellite_fusion.py` to fail or rely on mocked assets.
- **R-ING-003 (Silent Cache Corruption)**: Swallowed exceptions in `save_cache_response` (`except Exception: pass`) mask disk quota exhaustion and corrupt cache files.
- **R-ING-004 (Bandwidth & Cost Overhead)**: Downloading full Sentinel-2 L2A granules without HTTP range requests wastes bandwidth when only a small spatial bounding box is required.

### 11.2 Assumptions

- **A-ING-001 (STAC Availability)**: STAC catalog endpoints are assumed to operate with $\ge 99.5\%$ uptime.
- **A-ING-002 (WGS84 Input Coordinates)**: All user-supplied bounding boxes are assumed to be in EPSG:4326 (longitude/latitude).
- **A-ING-003 (Near-Real-Time Latency)**: Satellite scenes are assumed available in STAC catalogs within 24–48 hours of orbital overpass.
- **A-ING-004 (Idempotent Hashing)**: SHA256 hashes of sorted query parameters are assumed collision-free across the operational lifecycle.

---

## 12. Release / Baseline Acceptance Criteria

To declare `2_data_pipeline/ingestion` baseline-ready for production deployment, the following criteria must be fulfilled:

1. **Resolution of Critical Defects**: Defect D-ING-001 (orbit typo) and D-ING-002 (dual-pol collapse) must be resolved in code.
2. **Authentication / Signing Integration**: URL signing for Planetary Computer and AWS assets must be implemented.
3. **Unit Test Coverage Expansion**: Unit tests must be implemented for `multisource_ingestor.py` and `caching_and_resilience.py` with $\ge 85\%$ line coverage.
4. **Precision Preservation**: Truncation `np.round(..., 4)` must be removed from `compute_spectral_indices`.
5. **Configuration Freeze**: All source code and documentation must be tagged under `PIPE-ING-BL-01`.

---

## 13. Review and Approval

| Role | Name | Signature | Date |
|:---|:---|:---|:---:|
| **Author / Pipeline Engineer** | Gourgopal Mohapatra | *[Signed Electronically]* | 2026-10-10 |
| **Independent Verification Reviewer** | *(To be assigned)* | | |
| **Chief Systems Architect** | *(To be assigned)* | | |

---

## 14. Limitations / Scientific & Operational Boundary

> [!WARNING]
> **OPERATIONAL BOUNDARY: DISCOVERY VS. PHYSICAL ASSET RETRIEVAL**
> 
> The `ingestion` module performs **metadata discovery and URL resolution only**.
> 
> It does not download raster pixel bytes, does not verify whether external S3/HTTPS links are online or require payment, does not reproject coordinates, and does not apply radiometric calibrations. Successful execution of an ingestion query confirms that satellite scenes were cataloged by upstream providers, but **does not guarantee that valid raster arrays can be read without authenticated cloud access**.

---

## 15. Intellectual Property & Controlled Distribution

```text
========================================================================================
                      THE MRIDANSH (AETHER-MRID1607X)
         CENTRAL ENGINE: MULTI-DOMAIN SOIL INTELLIGENCE & GEOTECHNICAL STABILITY
========================================================================================
Copyright (c) 2026 Gourgopal Mohapatra. All Rights Reserved.
Developed & Maintained by: Gourgopal Mohapatra
Lead Organization: JCC HEADQUARTER
Facility: JCC CAMPUS 2 — RS-SDA Division (Remote Sensing & Spatial Data Analytics)

CONFIDENTIAL & PROPRIETARY SCIENTIFIC RESEARCH FRAMEWORK
This codebase, telemetry pipelines, and data ingestion architectures constitute
proprietary intellectual property.

Unauthorized copying, redistribution, reverse engineering, or commercial execution of
this software package — in whole or in part, via any medium — is strictly prohibited
without prior written authorization from the lead researcher and JCC RS-SDA.
========================================================================================
```
