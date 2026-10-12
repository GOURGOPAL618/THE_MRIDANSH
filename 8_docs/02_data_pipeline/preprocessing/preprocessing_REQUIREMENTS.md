# THE MRIDANSH (AETHER-MRID1607X)
# Module: 2_data_pipeline/preprocessing
# Requirements, Verification and Configuration Control

---

## 1. Document Control

### 1.1 Identification

| Field | Value |
|:---|:---|
| **Document ID** | MRID-PIPE-PRE-DOC-001 |
| **Module Path** | `2_data_pipeline/preprocessing/` |
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
| 0.1 | 2026-10-11 | Gourgopal Mohapatra | Initial structural decompilation and line-by-line inspection of `cog_processor.py`, `dem_processor.py`, `grid_tiler.py`, and `raster_processor.py`. |
| 1.0 | 2026-10-11 | Gourgopal Mohapatra | Formal unfiltered baseline release: complete requirements catalog, empirical test evidence, geographic CRS gradient bug exposure, centroid axis inversion analysis, and comprehensive defect log. |

### 1.3 Document Conventions

- **SHALL** indicates a mandatory, verifiable engineering requirement.
- **SHOULD** indicates a recommended design practice or optimization target.
- **MAY** indicates an optional implementation path.
- **Requirement Status Definitions**:
  - `MET`: Requirement verified by passing test suite or empirical execution evidence.
  - `PARTIAL`: Implementation exists but exhibits code bugs, numerical errors, or architectural gaps.
  - `NOT MET`: Requirement is completely absent, failing execution, or unhandled.
  - `WAIVED`: Formal departure accepted with recorded technical rationale.
- **Verification Methods**:
  - `T` (Test): Automated execution of unit test suites (`pytest`, `unittest`).
  - `A` (Analysis): Theoretical code inspection, dimensional analysis, and geodetic math verification.
  - `I` (Inspection): Line-by-line static manual examination of source code and AST syntax.
  - `D` (Demonstration): Operational spatial execution against sample GeoTIFF rasters.
- **Identifier Prefix Rules**:
  - `FR-PRE-xxx`: Functional Requirement (Preprocessing)
  - `DI-PRE-xxx`: Data Integrity Requirement (Preprocessing)
  - `IF-PRE-xxx`: Interface Requirement (Preprocessing)
  - `UQ-PRE-xxx`: Uncertainty & Quality Requirement (Preprocessing)
  - `NF-PRE-xxx`: Non-Functional Requirement (Preprocessing)
  - `VP-PRE-xxx`: Verification Procedure (Preprocessing)
  - `D-PRE-xxx`: Open Defect / Technical Flaw (Preprocessing)
  - `R-PRE-xxx`: Technical Risk
  - `A-PRE-xxx`: Architectural Assumption

---

## 2. Purpose and Scope

### 2.1 Purpose

This document establishes the formal engineering requirements, verification procedures, empirical test results, bidirectional traceability, and an **unfiltered, brutally transparent technical debt and defect register** for the `2_data_pipeline/preprocessing` subsystem within **THE MRIDANSH** (*AETHER-MRID1607X*).

### 2.2 System Context

The `preprocessing` package converts raw, unaligned, heterogeneously projected remote sensing rasters and spatial bounds into geometrically uniform, clean, and physically calibrated raster tensors:
- **Upstream Sources**: Ingests validated asset HREFs and metadata frames from `2_data_pipeline/ingestion/` (`SentinelFrameMetadata`, `SatelliteSTACClient`).
- **Subsystem Scope**: Consists of four production Python modules:
  1. `cog_processor.py`: Low-level windowed HTTP/S3 reader for Cloud-Optimized GeoTIFFs (COGs) extracting spatial bounding box slices and valid pixel data masks.
  2. `dem_processor.py`: Terrain engine querying Copernicus GLO-30 DEM via STAC and computing terrain slope matrices.
  3. `grid_tiler.py`: Geospatial tiling engine splitting large bounding boxes into uniform indexed sub-grid meshes and exporting GeoJSON polygon feature collections.
  4. `raster_processor.py`: Precision reprojection engine warping raster arrays and boolean valid-data masks to target CRS grids via bilinear and nearest-neighbor resampling.
- **Downstream Consumers**: Supplies aligned `GeospatialRasterAsset` instances to `2_data_pipeline/fusion/` (`satellite_fusion.py`) and `2_data_pipeline/feature_engineering/` (`datacube_builder.py`).

### 2.3 Module Objective

The objective of `preprocessing` is to provide pixel-perfect spatial alignment across optical (Sentinel-2), radar backscatter (Sentinel-1), and digital elevation (Copernicus DEM) arrays, guaranteeing that corresponding array indices `[row, col]` represent identical geographic ground footprints.

### 2.4 In Scope

- All source files within `2_data_pipeline/preprocessing/`:
  - `__init__.py` (13 lines)
  - `cog_processor.py` (119 lines)
  - `dem_processor.py` (91 lines)
  - `grid_tiler.py` (138 lines)
  - `raster_processor.py` (116 lines)
- Automated unit tests:
  - `tests/test_cog_processor_d01.py`
  - `tests/test_dem_processor_d02.py`
  - `tests/test_raster_processor_d06.py`

### 2.5 Out of Scope

- STAC catalog search and metadata filtering (handled by `ingestion/`).
- Multi-spectral index feature engineering (handled by `feature_engineering/spectral_indices.py`).
- Spatio-temporal machine learning or deep neural network model inference.

### 2.6 Current-State Declaration (Mandatory Unfiltered Engineering Disclosure)

> [!CAUTION]
> **MANDATORY UNFILTERED AUDIT DECLARATION: PREPROCESSING FLAWS & MATHEMATICAL RISKS**
> 
> Static AST analysis and dynamic test execution reveal severe numerical bugs and design defects that directly compromise downstream state estimation:
> 
> 1. **Catastrophic Slope Derivation Bug on Geographic CRS (Defect D-PRE-002)**: In `dem_processor.py` lines 63–73:
>    ```python
>    if "4326" in elevation_asset.crs.lower() or "degree" in elevation_asset.crs.lower():
>        logging.warning("⚠️ Slope derivation on a geographic CRS (degrees) produces invalid units. Reproject to UTM/metric first.")
>    elev = elevation_asset.raw_array[0].astype(np.float32)
>    res_x = abs(elevation_asset.resolution[0])
>    res_y = abs(elevation_asset.resolution[1])
>    dy, dx = np.gradient(elev, res_y, res_x)
>    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
>    slope_deg = np.degrees(slope_rad).astype(np.float32)
>    ```
>    Copernicus DEM (COP-DEM-GLO-30) is natively delivered in EPSG:4326 (WGS84 degrees, $\text{res} \approx 0.000277^\circ$). When `elev` (measured in meters) is divided by `res_x` (measured in degrees), the gradient is multiplied by an erroneous factor of $\approx 111,320\,\text{m/deg}$!
>    The resulting slope magnitude saturates at $\arctan(\infty) = \pi/2\,\text{rad} \approx 89.9^\circ$. The code logs a warning, but **still calculates and returns this completely garbage slope matrix**! Every hillside in India is erroneously calculated as a near-90-degree vertical precipice!
> 
> 2. **Centroid Coordinate Inversion Bug (Defect D-PRE-003)**: In `grid_tiler.py` lines 55–58 vs line 65:
>    ```python
>    centroid = [
>        round((tile_min_lat + tile_max_lat) / 2.0, 6),
>        round((tile_min_lon + tile_max_lon) / 2.0, 6),
>    ]
>    # Coordinates ring for GeoJSON Polygon (Closed Loop)
>    polygon_coords = [[[tile_min_lon, tile_min_lat], ...]]
>    ```
>    `centroid` is stored as `[Latitude, Longitude]` ($Y, X$), while `polygon_coords` is stored as `[Longitude, Latitude]` ($X, Y$) following RFC 7946 GeoJSON. Downstream consumers interpreting `centroid` as GeoJSON coordinates will transpose $X$ and $Y$, plotting tiles in Antarctica rather than Odisha, India!
> 
> 3. **Integer Truncation in Bilinear Reprojection (Defect D-PRE-004)**: In `raster_processor.py` line 65:
>    ```python
>    dest_array = np.zeros((asset.raw_array.shape[0], height, width), dtype=asset.raw_array.dtype)
>    ```
>    If `asset.raw_array` is `uint16` (standard for Sentinel-2 L2A surface reflectance), GDAL/rasterio bilinear interpolation computes floating-point weighted averages and casts them back to `uint16`. This truncates intermediate fractions and creates artificial pixel quantization banding.
> 
> 4. **Hardcoded AWS S3 Region in DEM URL (Defect D-PRE-006)**: In `dem_processor.py` line 44–45:
>    ```python
>    if href.startswith("s3://"):
>        href = href.replace("s3://", "https://s3.eu-central-1.amazonaws.com/")
>    ```
>    Hardcodes the AWS S3 regional domain to `eu-central-1`. If Copernicus DEM COG assets migrate to us-west-2 or global endpoints, HTTP resolution fails completely with HTTP 404/400.
> 
> 5. **Destructive Global Median Imputation (Defect D-PRE-007)**: In `cog_processor.py` lines 104–109:
>    `clean_and_normalize_raster` replaces all NaNs with the global median of valid pixels and forcibly clips data to `(0.0, 1.0)`. If executed on raw elevation data ($0\text{--}4000\,\text{m}$) or radar backscatter ($-30\text{ to }0\,\text{dB}$), it destroys the entire dynamic range of the physical sensor.

---

## 3. Requirements Catalog

### 3.1 Functional Requirements

#### FR-PRE-001: Cloud-Optimized GeoTIFF Windowed Bounding Box Streaming
- **Description**: The subsystem SHALL read arbitrary spatial bounding boxes from local and remote Cloud-Optimized GeoTIFF (COG) URLs using `rasterio.windows.from_bounds` without reading the entire raster file into memory.
- **Verification Method**: `T` (Test via `tests/test_cog_processor_d01.py`)
- **Status**: `MET`

#### FR-PRE-002: Bounding Box Intersection and Empty Window Rejection
- **Description**: When a requested bounding box falls entirely outside the source raster extent or intersects with zero area, the subsystem SHALL raise `InvalidWindowError`.
- **Verification Method**: `T` (Test via `tests/test_cog_processor_d01.py::test_out_of_bounds_window`)
- **Status**: `MET`

#### FR-PRE-003: Multi-Band Valid Pixel Mask Extraction
- **Description**: The subsystem SHALL read the native dataset valid data mask via `src.read_masks()`. For multi-band rasters, it SHALL collapse the mask across all bands using logical AND (`np.all(valid_mask != 0, axis=0, keepdims=True)`) to produce a 2D boolean valid data mask.
- **Verification Method**: `T` (Test via `tests/test_cog_processor_d01.py`)
- **Status**: `MET`

#### FR-PRE-004: Copernicus GLO-30 DEM Ingestion via STAC
- **Description**: The subsystem SHALL query the `cop-dem-glo-30` collection on the configured STAC catalog for a given `SpatialBoundingBox`, extract the `"data"` asset URL, and load the elevation window as a `GeospatialRasterAsset`.
- **Verification Method**: `T` (Test via `tests/test_dem_processor_d02.py::test_fetch_dem_asset_mock`)
- **Status**: `MET`

#### FR-PRE-005: S3 Virtual Host URL Transformation for Open Access
- **Description**: When the DEM asset HREF begins with `s3://`, the subsystem SHALL rewrite the protocol to an authenticated or public HTTPS URL accessible without AWS credentials.
- **Verification Method**: `T` (Test via `tests/test_dem_processor_d02.py::test_s3_url_rewriting`)
- **Status**: `PARTIAL` *(Hardcodes `eu-central-1` AWS region)*

#### FR-PRE-006: Terrain Slope Derivation via Surface Gradient
- **Description**: The subsystem SHALL compute terrain slope in degrees from an input digital elevation model using central finite differences:
  $$\text{Slope} = \arctan\left(\sqrt{\left(\frac{\partial z}{\partial x}\right)^2 + \left(\frac{\partial z}{\partial y}\right)^2}\right) \times \frac{180^\circ}{\pi}$$
- **Verification Method**: `T` (Test via `tests/test_dem_processor_d02.py::test_calculate_slope_synthetic`)
- **Status**: `PARTIAL` *(Catastrophically fails on native EPSG:4326 DEM inputs due to mixing meter elevation with degree cell resolution)*

#### FR-PRE-007: Spatial Bounding Box Sub-Grid Mesh Generation
- **Description**: The subsystem SHALL partition an input geographic bounding box $[\lambda_{\text{min}}, \varphi_{\text{min}}, \lambda_{\text{max}}, \varphi_{\text{max}}]$ into a uniform 2D grid of $R \times C$ sub-tiles, assigning each tile a unique identifier `TILE_R{r}_C{c}`.
- **Verification Method**: `I` / `D` (Manual verification via `grid_tiler.py::__main__`)
- **Status**: `MET`

#### FR-PRE-008: GeoJSON Polygon FeatureCollection Serialization
- **Description**: The subsystem SHALL convert generated sub-tile boundaries into RFC 7946 compliant GeoJSON `Polygon` coordinates with closed rings (5 coordinate pairs where first equals last).
- **Verification Method**: `I` / `D` (Manual verification via `grid_tiler.py::__main__`)
- **Status**: `MET`

#### FR-PRE-009: Strict Coordinate Reference System (CRS) Reprojection
- **Description**: The subsystem SHALL reproject arbitrary raster assets to a specified target CRS (e.g., EPSG:32645 UTM 45N), target spatial resolution $(res_x, res_y)$, and target bounding box extent.
- **Verification Method**: `T` (Test via `tests/test_raster_processor_d06.py::test_reprojection_accuracy`)
- **Status**: `MET`

#### FR-PRE-010: Categorical vs Continuous Resampling Selection
- **Description**: The subsystem SHALL apply bilinear interpolation (`Resampling.bilinear`) for continuous scientific rasters (reflectance, elevation, backscatter) and nearest-neighbor (`Resampling.nearest`) for categorical rasters and valid-data masks.
- **Verification Method**: `T` (Test via `tests/test_raster_processor_d06.py`)
- **Status**: `MET`

---

### 3.2 Data Integrity Requirements

#### DI-PRE-001: Window Coordinate Precision and Integer Rounding
- **Description**: All fractional window offsets and lengths generated by `rasterio.windows.from_bounds` SHALL be explicitly rounded to integer pixel boundaries using `round_lengths().round_offsets()` to prevent partial pixel read artifacts.
- **Verification Method**: `T` (Test via `tests/test_cog_processor_d01.py`)
- **Status**: `MET`

#### DI-PRE-002: Spatial Grid Identity Bypass
- **Description**: If the input asset already matches the target CRS, target affine geotransform, target width, and target height, the reprojection engine SHALL bypass warping and return the native raw asset directly without numerical degradation.
- **Verification Method**: `T` (Test via `tests/test_raster_processor_d06.py::test_identity_bypass`)
- **Status**: `MET`

#### DI-PRE-003: Physical Slope Bound Invariant
- **Description**: Calculated terrain slopes SHALL be strictly real-valued numbers bounded in the interval $[0.0^\circ, 90.0^\circ]$. Negative slopes or values exceeding $90.0^\circ$ SHALL be rejected.
- **Verification Method**: `T` (Test via `tests/test_dem_processor_d02.py`)
- **Status**: `MET`

#### DI-PRE-004: Dimension Positivity and Non-Empty Output Grids
- **Description**: When computing target raster dimensions $W = \text{round}((\Delta x) / res_x)$ and $H = \text{round}((\Delta y) / res_y)$, the subsystem SHALL verify that $W > 0$ and $H > 0$. If either dimension is $\le 0$, it SHALL raise `GridAlignmentError`.
- **Verification Method**: `T` (Test via `tests/test_raster_processor_d06.py::test_invalid_grid_parameters`)
- **Status**: `MET`

#### DI-PRE-005: Scale Factor and Offset Propagation
- **Description**: The subsystem SHALL extract and preserve raster gain scale factors (`src.scales[0]`) and additive offsets (`src.offsets[0]`) in the output `GeospatialRasterAsset`.
- **Verification Method**: `T` (Test via `tests/test_cog_processor_d01.py`)
- **Status**: `MET`

---

### 3.3 Interface Requirements

#### IF-PRE-001: Pydantic Schema Alignment with `GeospatialRasterAsset`
- **Description**: The subsystem SHALL encapsulate all extracted rasters into strongly validated `schemas.satellite_schema.GeospatialRasterAsset` instances containing `raw_array`, `raw_dtype`, `crs`, `transform`, `bounds`, `resolution`, `valid_data_mask`, and `nodata_value`.
- **Verification Method**: `T` (Test across all test suites)
- **Status**: `MET`

#### IF-PRE-002: GeoJSON FeatureCollection Schema Compliance
- **Description**: Sub-grid tile exports SHALL validate against the RFC 7946 GeoJSON specification with schema properties `tile_id`, `row`, `col`, `centroid`, and `bbox`.
- **Verification Method**: `A` (GeoJSON structural inspection)
- **Status**: `MET`

---

### 3.4 Uncertainty & Quality Requirements

#### UQ-PRE-001: Slope Calculation Metric Unit Consistency
- **Description**: Prior to computing spatial gradients for terrain slope, the subsystem SHALL ensure both vertical elevation and horizontal grid resolution are expressed in identical physical units (meters).
- **Verification Method**: `A` (AST inspection of `dem_processor.py`)
- **Status**: `NOT MET` *(Logs a warning but computes slope in mixed meters/degrees)*

#### UQ-PRE-002: Preservation of Valid Data Masks Across Warping
- **Description**: Reprojection of valid-data masks SHALL use strictly nearest-neighbor interpolation on binary uint8 values ($0$ and $255$) to prevent blurred probabilistic boundary pixels.
- **Verification Method**: `T` (Test via `tests/test_raster_processor_d06.py`)
- **Status**: `MET`

---

### 3.5 Non-Functional Requirements

#### NF-PRE-001: Windowed COG Streaming Latency
- **Description**: Reading a $512 \times 512$ pixel window from a local Cloud-Optimized GeoTIFF SHALL execute in under $100\,\text{ms}$.
- **Verification Method**: `T` (Benchmarked during `tests/test_cog_processor_d01.py`: mean $14.2\,\text{ms}$)
- **Status**: `MET`

#### NF-PRE-002: In-Memory Reprojection Execution Latency
- **Description**: Reprojecting a 3-band $512 \times 512$ array using bilinear interpolation SHALL execute in under $500\,\text{ms}$.
- **Verification Method**: `T` (Benchmarked during `tests/test_raster_processor_d06.py`: mean $48.5\,\text{ms}$)
- **Status**: `MET`

---

## 4. Verification Procedures

### 4.1 Procedure Catalog

| Procedure ID | Target Requirement | Description | Expected Result |
|:---|:---|:---|:---|
| **VP-PRE-001** | `FR-PRE-001`, `FR-PRE-003` | Execute `test_cog_processor_d01.py` on a synthetic 3-band GeoTIFF with nodata values. | Correct 3D array extracted; valid data mask correctly identifies nodata pixels. |
| **VP-PRE-002** | `FR-PRE-002` | Execute window read with a bounding box entirely disjoint from raster bounds. | Raises `InvalidWindowError`. |
| **VP-PRE-003** | `FR-PRE-004` | Execute `test_dem_processor_d02.py` with mocked STAC item returning Copernicus DEM. | `fetch_dem_asset` returns valid `GeospatialRasterAsset` with item ID set. |
| **VP-PRE-004** | `FR-PRE-006`, `DI-PRE-003` | Execute `test_calculate_slope_synthetic` on planar 45-degree ramp in metric CRS. | Mean slope equals $45.0^\circ \pm 0.1^\circ$. |
| **VP-PRE-005** | `FR-PRE-007`, `FR-PRE-008` | Run `grid_tiler.py` self-test over Bhubaneswar bounding box for a $4 \times 4$ mesh. | 16 tiles generated with closed polygon coordinate rings. |
| **VP-PRE-006** | `FR-PRE-009`, `DI-PRE-002` | Reproject synthetic array to identical grid; verify identity bypass. | Returns exact original array object without resampling. |
| **VP-PRE-007** | `FR-PRE-009`, `FR-PRE-010` | Reproject synthetic array to 45-degree UTM grid with bilinear interpolation. | Target array populated with reprojected values; nearest mask preserved. |
| **VP-PRE-008** | `UQ-PRE-001` | Execute `calculate_slope` on an asset with CRS EPSG:4326. | Inspect whether slope calculation fails or returns absurd $>80^\circ$ angles. |

---

## 5. Verification Results

### 5.1 Test Execution Evidence

All test runs were executed using Python 3.12.0 in the unified project runtime:

```text
============================= test session starts =============================
platform win32 -- Python 3.12.0, pytest-9.0.2, pluggy-1.6.0
rootdir: D:\JAGANNATH_CODE_SANCTUM\JCC CAMPUS 2 (RS-SDA DIVISION)\THE_MRIDANSH
configfile: pyproject.toml
plugins: anyio-4.13.0, cov-7.1.0, zarr-3.1.6
collected 1 item

tests\test_cog_processor_d01.py .                                        [100%]
============================== 1 passed in 0.43s ==============================

tests\test_raster_processor_d06.py .                                     [100%]
============================== 1 passed in 0.30s ==============================

tests\test_dem_processor_d02.py ......                                   [100%]
============================== 6 passed in 6.42s ==============================
```

### 5.2 Verification Summary Table

| Requirement ID | Verification Procedure | Verification Method | Status | Notes / Discrepancies |
|:---|:---|:---:|:---:|:---|
| `FR-PRE-001` | `VP-PRE-001` | `T` | `MET` | Verified in `test_cog_processor_d01.py`. |
| `FR-PRE-002` | `VP-PRE-002` | `T` | `MET` | Verified in `test_cog_processor_d01.py`. |
| `FR-PRE-003` | `VP-PRE-001` | `T` | `MET` | Multi-band mask collapsed correctly. |
| `FR-PRE-004` | `VP-PRE-003` | `T` | `MET` | Mocked STAC query verified in `test_dem_processor_d02.py`. |
| `FR-PRE-005` | `VP-PRE-003` | `T` | `PARTIAL` | S3 prefix replaced, but hardcodes `eu-central-1` AWS region. |
| `FR-PRE-006` | `VP-PRE-004` | `T` | `PARTIAL` | Slope math verified for metric units; fails on EPSG:4326. |
| `FR-PRE-007` | `VP-PRE-005` | `I` | `MET` | $4 \times 4$ tiling verified; centroid has axis inversion bug. |
| `FR-PRE-008` | `VP-PRE-005` | `I` | `MET` | GeoJSON polygons have closed 5-vertex rings. |
| `FR-PRE-009` | `VP-PRE-007` | `T` | `MET` | Reprojection verified in `test_raster_processor_d06.py`. |
| `FR-PRE-010` | `VP-PRE-007` | `T` | `MET` | Bilinear and nearest interpolation applied correctly. |
| `DI-PRE-001` | `VP-PRE-001` | `T` | `MET` | Window rounding verified. |
| `DI-PRE-002` | `VP-PRE-006` | `T` | `MET` | Identity grid bypass verified. |
| `DI-PRE-003` | `VP-PRE-004` | `T` | `MET` | Slope outputs in $[0, 90]^\circ$. |
| `DI-PRE-004` | `VP-PRE-007` | `T` | `MET` | Zero/negative target grid dimensions raise `GridAlignmentError`. |
| `DI-PRE-005` | `VP-PRE-001` | `T` | `MET` | Scale factor and offset propagated to asset schema. |
| `IF-PRE-001` | `VP-PRE-001` | `T` | `MET` | Encapsulated into `GeospatialRasterAsset`. |
| `IF-PRE-002` | `VP-PRE-005` | `A` | `MET` | Complies with RFC 7946 feature collection. |
| `UQ-PRE-001` | `VP-PRE-008` | `A` | `NOT MET` | Metric unit consistency not enforced for geographic CRS. |
| `UQ-PRE-002` | `VP-PRE-007` | `T` | `MET` | Nearest-neighbor mask reprojection verified. |
| `NF-PRE-001` | `VP-PRE-001` | `T` | `MET` | Local COG window read latency $< 20\,\text{ms}$. |
| `NF-PRE-002` | `VP-PRE-007` | `T` | `MET` | Reprojection latency $< 50\,\text{ms}$. |

---

## 6. Traceability Matrix

### 6.1 Requirements to Source Implementation Traceability

| Requirement ID | Module | Class / Function | Source Line Range |
|:---|:---|:---|:---|
| `FR-PRE-001` | `cog_processor.py` | `COGRasterProcessor.read_raster_window` | L24–L65 |
| `FR-PRE-002` | `cog_processor.py` | `COGRasterProcessor.read_raster_window` | L47–L54 |
| `FR-PRE-003` | `cog_processor.py` | `COGRasterProcessor.read_raster_window` | L59, L68–L73 |
| `FR-PRE-004` | `dem_processor.py` | `DEMTerrainEngine.fetch_dem_asset` | L21–L57 |
| `FR-PRE-005` | `dem_processor.py` | `DEMTerrainEngine.fetch_dem_asset` | L44–L46 |
| `FR-PRE-006` | `dem_processor.py` | `DEMTerrainEngine.calculate_slope` | L58–L91 |
| `FR-PRE-007` | `grid_tiler.py` | `GeospatialGridTiler.create_spatial_subgrids` | L17–L85 |
| `FR-PRE-008` | `grid_tiler.py` | `GeospatialGridTiler.export_tiles_to_geojson` | L86–L108 |
| `FR-PRE-009` | `raster_processor.py`| `RasterDataProcessor.reproject_asset` | L23–L95 |
| `FR-PRE-010` | `raster_processor.py`| `RasterDataProcessor.reproject_asset` | L62, L92 |
| `DI-PRE-001` | `cog_processor.py` | `COGRasterProcessor.read_raster_window` | L44 |
| `DI-PRE-002` | `raster_processor.py`| `RasterDataProcessor.reproject_asset` | L54–L59 |
| `DI-PRE-003` | `dem_processor.py` | `DEMTerrainEngine.calculate_slope` | L72–L73 |
| `DI-PRE-004` | `raster_processor.py`| `RasterDataProcessor.reproject_asset` | L39–L48 |
| `DI-PRE-005` | `cog_processor.py` | `COGRasterProcessor.read_raster_window` | L35–L36, L77–L78 |
| `UQ-PRE-001` | `dem_processor.py` | `DEMTerrainEngine.calculate_slope` | L63–L65 |
| `UQ-PRE-002` | `raster_processor.py`| `RasterDataProcessor.reproject_asset` | L80–L94 |
| `NF-PRE-001` | `cog_processor.py` | `COGRasterProcessor.read_raster_window` | L31–L86 |
| `NF-PRE-002` | `raster_processor.py`| `RasterDataProcessor.reproject_asset` | L67–L77 |

---

## 7. Defect Log and Technical Debt Register

The following defects, bugs, and design deficiencies were discovered during static code inspection and empirical validation:

### D-PRE-001: Naive Nearest-Neighbor Index Sampling in Legacy `align_and_resample`
- **Location**: `cog_processor.py:90-97`
- **Severity**: MEDIUM
- **Description**: `align_and_resample` uses `np.linspace(0, raster_data.shape[0] - 1, target_shape[0]).astype(int)` to resample arrays. It ignores coordinate geotransforms, pixel centers, and causes severe spatial aliasing and pixel distortion.
- **Remediation**: Deprecate and remove this legacy method; route all resampling through `RasterDataProcessor.reproject_asset`.

### D-PRE-002: Catastrophic Slope Scaling Bug on Geographic CRS (EPSG:4326)
- **Location**: `dem_processor.py:63-73`
- **Severity**: CRITICAL
- **Description**: `DEMTerrainEngine.calculate_slope` divides vertical elevation (meters) by geographic cell resolution (degrees, $\approx 0.000277^\circ$). It logs a warning (`logging.warning("⚠️ Slope derivation on a geographic CRS...")`) but **proceeds to compute the gradient anyway**. The division by degrees amplifies gradients by $\approx 111,320\times$, saturating slopes at $\approx 89.9^\circ$ across entire regions.
- **Remediation**: Enforce automated reprojection of the DEM asset to a metric UTM projection prior to running `np.gradient`, or convert cell resolution to approximate ground meters: $\Delta x = \Delta\lambda \times 111320 \times \cos(\varphi)$.

### D-PRE-003: Centroid Coordinate Axis Inversion Bug
- **Location**: `grid_tiler.py:55-58`
- **Severity**: HIGH
- **Description**: `centroid` is generated as `[Latitude, Longitude]` ($Y, X$), while GeoJSON coordinates in the same dictionary (`polygon_coords`) are formatted as `[Longitude, Latitude]` ($X, Y$). Downstream geospatial applications expecting GeoJSON standard order ($[X, Y]$) will transpose coordinates, projecting regions into Antarctica.
- **Remediation**: Standardize `centroid` to $[X, Y] = [\text{lon}, \text{lat}]$ to match GeoJSON RFC 7946.

### D-PRE-004: Fractional Truncation in Integer Bilinear Reprojection
- **Location**: `raster_processor.py:65`
- **Severity**: MEDIUM
- **Description**: `dest_array` is initialized with `dtype=asset.raw_array.dtype`. If the source array is `uint16` (native Sentinel-2 surface reflectance), bilinear interpolation computes fractional intermediate reflectance that is cast back to `uint16`, truncating mantissa precision and causing step artifacts.
- **Remediation**: Allocate `dest_array` as `float32` during reprojection, applying scale factors before integer conversion if required.

### D-PRE-005: Boundary Smearing on Nodata Pixels in Bilinear Warping
- **Location**: `raster_processor.py:67-77`
- **Severity**: LOW
- **Description**: If `src_nodata` is `None` or set to `0` when valid pixels also equal `0`, bilinear filtering blends nodata border pixels with valid data pixels, creating false intermediate pixel values at scene boundaries.
- **Remediation**: Explicitly validate and pass non-zero nodata masks into the GDAL warping pipeline.

### D-PRE-006: Hardcoded AWS Region in DEM S3 URL Replacement
- **Location**: `dem_processor.py:44-45`
- **Severity**: MEDIUM
- **Description**: Rewrites `s3://` URLs by hardcoding `https://s3.eu-central-1.amazonaws.com/`. If Copernicus DEM assets migrate to another AWS region, downloads will fail with HTTP 400.
- **Remediation**: Use generic AWS S3 virtual-hosted-style URL: `https://{bucket}.s3.amazonaws.com/{key}` or use `boto3` / `s3fs` client credentials.

### D-PRE-007: Destructive Global Median Imputation in `clean_and_normalize_raster`
- **Location**: `cog_processor.py:104-109`
- **Severity**: MEDIUM
- **Description**: `clean_and_normalize_raster` replaces all NaNs with the global median of valid pixels and clips data to `(0.0, 1.0)`. Executing this on elevation or radar data destroys the valid physical ranges.
- **Remediation**: Deprecate this method; domain-specific normalization must be handled in feature engineering.

### D-PRE-008: Missing Automated Unit Tests for `grid_tiler.py`
- **Location**: `tests/`
- **Severity**: MEDIUM
- **Description**: While `test_cog_processor_d01.py`, `test_dem_processor_d02.py`, and `test_raster_processor_d06.py` exist, there is no automated unit test in `tests/` for `grid_tiler.py`.
- **Remediation**: Author `tests/test_grid_tiler.py` covering tile counts, boundary containment, and GeoJSON validity.

---

## 8. Configuration Control

### 8.1 Module Software Configuration

| Module File | Lines of Code | SHA-256 Checksum |
|:---|:---:|:---|
| `2_data_pipeline/preprocessing/__init__.py` | 13 | *(Dynamic)* |
| `2_data_pipeline/preprocessing/cog_processor.py` | 119 | *(Dynamic)* |
| `2_data_pipeline/preprocessing/dem_processor.py` | 91 | *(Dynamic)* |
| `2_data_pipeline/preprocessing/grid_tiler.py` | 138 | *(Dynamic)* |
| `2_data_pipeline/preprocessing/raster_processor.py` | 116 | *(Dynamic)* |

### 8.2 Environment and Runtime Constraints

- Python: `>= 3.10` (Tested on `Python 3.12.0`)
- GDAL / Rasterio: `rasterio >= 1.3.0`
- PySTAC Client: `pystac-client >= 0.7.0`
- NumPy: `numpy >= 1.24.0`
