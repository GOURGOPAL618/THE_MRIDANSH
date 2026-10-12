# THE MRIDANSH (AETHER-MRID1607X)
## Notebook 01 — Data Ingestion: Requirements, Design, Verification and Control Document

---

## 1. Document Control

| Field | Value |
|---|---|
| Document ID | MRID-NB01-REQ |
| Title | Notebook 01 Data Ingestion — Requirements Specification |
| Item under documentation | `01-data-ingestion.ipynb` |
| Companion file | `01_data_ingestion.rst` (technical description) |
| Project | THE MRIDANSH — Unified Soil State Estimation System |
| Engine | AETHER-MRID1607X |
| Owner / Author | Gourgopal Mohapatra |
| Organisation | JCC Headquarter, JCC Campus 2, RS-SDA Division |
| Version | 0.2 |
| Date | 2026-10-06 |
| Status | Draft — under review |
| Reviewer | *(to be assigned — must be someone other than author)* |
| Approver | *(to be assigned)* |

### 1.1 Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-10-05 | G. Mohapatra | Initial draft |
| 0.2 | 2026-10-06 | G. Mohapatra | Restructured as a standalone requirements document; removed external-standard framing |

### 1.2 Conventions

* **shall** = mandatory, verifiable. **should** = recommended. **may** = optional.
* Requirement IDs are permanent. A removed requirement is marked *WITHDRAWN*, never reused.
* Status values: **MET** (verified), **PARTIAL** (some aspect missing), **NOT MET** (absent), **WAIVED** (formally accepted, rationale recorded).
* Verification methods: **T** Test, **A** Analysis, **I** Inspection, **D** Demonstration.

---

## 2. Purpose and Scope

### 2.1 Purpose
Define what Notebook 01 shall do, how each statement is verified, and how the work is controlled, so that the ingestion stage of THE MRIDANSH can be reviewed and reproduced objectively.

### 2.2 System context
THE MRIDANSH fuses optical imagery, SAR, DEM, weather and temporal history into a **Unified Soil State Vector** (hydro-physical, biogeochemical, terrain state) with confidence and uncertainty, via data assimilation (EnKF) and physics-guided learning. Domain translators (agriculture, civil engineering, external systems such as MARGAVEDHA) consume that vector.

### 2.3 In scope (Notebook 01)
Area-of-interest definition, temporal window, multi-sensor ingestion, integrity audit, spectral index derivation, DEM-to-grid alignment, STAC metadata, export to `data/raw/`.

### 2.4 Out of scope
Preprocessing (speckle filtering, atmospheric correction), state estimation, EnKF, PINN training, domain translation.

### 2.5 Current-state declaration (mandatory disclosure)
**All data in the current notebook is synthetic** (NumPy generators, seeds 42 and 101). No satellite catalogue, DEM service or weather feed is queried. Any numeric result (for example "45.7 % cloudy days") describes the random generator, not the study area, and shall not be cited as a scientific finding.

---

## 3. Definitions

| Term | Meaning |
|---|---|
| AOI | Area of interest: bounding box around (21.1378 N, 86.6874 E) |
| SAR VV / VH | Sentinel-1 C-band co- and cross-polarised backscatter, dB |
| MSI | Sentinel-2 multispectral instrument |
| DEM | Digital elevation model |
| NDVI | (NIR − RED)/(NIR + RED) = (B08 − B04)/(B08 + B04) |
| NDWI | (GREEN − NIR)/(GREEN + NIR) = (B03 − B08)/(B03 + B08) |
| STAC | SpatioTemporal Asset Catalog, version 1.0.0 |
| Frame | One acquisition record (one table row) |
| Raw data lake | Directory `data/raw/` |

---

## 4. Requirements

### 4.1 Functional — Area and time

| ID | Requirement | Rationale | Method | Acceptance criterion | Status |
|---|---|---|---|---|---|
| FR-001 | The software shall compute a bounding box [W, S, E, N] in EPSG:4326 from a centre latitude, longitude and a buffer in degrees. | Fixed, reproducible AOI. | T | For (21.1378, 86.6874, 0.05) result equals [86.6374, 21.0878, 86.7374, 21.1878] (4 d.p.). | MET |
| FR-002 | The software shall hold the analysis start and end dates as named, editable parameters. | Reproducible temporal window. | I | Parameters `START_DATE`, `END_DATE` present and used. | MET |
| FR-003 | The software shall generate or retrieve exactly N frames evenly spaced between start and end dates. | Defined sampling. | T | N = 35 rows; first timestamp = start; last = end. | MET |

### 4.2 Functional — Ingestion

| ID | Requirement | Rationale | Method | Acceptance criterion | Status |
|---|---|---|---|---|---|
| FR-010 | The software shall retrieve Sentinel-1 VV and VH backscatter (dB) for the AOI and window from a documented catalogue. | Primary soil-moisture signal, cloud-independent. | D | Real scenes retrieved; scene IDs recorded. | NOT MET (simulated) |
| FR-011 | The software shall retrieve Sentinel-2 L2A bands B03, B04, B08 and the scene classification/cloud information. | Vegetation/water indices and cloud masking. | D | Real scenes retrieved; SCL or cloud mask retained. | NOT MET (simulated) |
| FR-012 | The software shall retrieve a DEM covering the AOI and record its source and native resolution. | Terrain input. | D | DEM source and resolution in metadata. | NOT MET (random array) |
| FR-013 | The software shall retrieve precipitation and air temperature for the AOI and window from a documented source. | Hydrological forcing. | D | Source named; units documented. | NOT MET (simulated) |
| FR-014 | The software shall label every dataset as `real` or `synthetic` in the output metadata and file name. | Prevent misuse of simulated data. | I | Label present in CSV file name and STAC properties. | NOT MET |

### 4.3 Functional — Processing

| ID | Requirement | Rationale | Method | Acceptance criterion | Status |
|---|---|---|---|---|---|
| FR-020 | The software shall compute NDVI and NDWI per the formulas in Section 3. | Standard indices. | T | Hand-computed test values reproduced to 1e-9. | PARTIAL (no known-value test) |
| FR-021 | The software shall apply optical quality/cloud masking before computing indices. | Cloud contamination biases indices. | T | Masked pixels yield NaN, not a number. | NOT MET |
| FR-022 | The software shall resample the DEM to the target grid by bilinear interpolation. | Common grid for fusion. | T | Output shape equals target grid shape. | MET |
| FR-023 | The software shall handle zero denominators in index computation explicitly. | Avoid inf/NaN silently. | T | Input with B08 + B04 = 0 gives NaN and a logged warning. | NOT MET |

### 4.4 Functional — Output

| ID | Requirement | Rationale | Method | Acceptance criterion | Status |
|---|---|---|---|---|---|
| FR-030 | The software shall write the telemetry table to `data/raw/` as CSV with a documented schema (Section 6). | Downstream input. | T | File exists; columns and dtypes match schema. | MET (name has typo) |
| FR-031 | The software shall build a STAC 1.0.0 Item containing `id`, `type`, `geometry`, `bbox`, `properties.datetime`, `assets`, `links`. | Standard provenance. | T | Passes a STAC JSON-schema validator. | PARTIAL (key `assert` used instead of `assets`; `links` missing) |
| FR-032 | The software shall write each raster referenced by the STAC Item as a georeferenced GeoTIFF/COG. | Referenced assets must exist. | T | Every `assets.*.href` file exists and carries CRS and transform. | NOT MET |
| FR-033 | The software shall record per-frame provenance: source scene ID, acquisition time, processing version. | Traceability of every value. | I | Columns present and non-empty. | NOT MET |
| FR-034 | The software shall record a SHA-256 checksum of each exported file. | Detect corruption or change. | T | Checksum file generated and verified on re-read. | NOT MET |

### 4.5 Data-integrity requirements

| ID | Requirement | Method | Acceptance criterion | Status |
|---|---|---|---|---|
| DI-001 | All frames shall use a single CRS (EPSG:4326); otherwise execution shall halt. | T | Mixed-CRS input raises an error. | MET |
| DI-002 | The table shall contain no null values, or nulls shall be explicitly flagged per column. | T | Injected NaN is detected and reported. | PARTIAL (check exists; trivially true on synthetic data) |
| DI-003 | NDVI and NDWI shall lie in [−1, 1]; violation shall halt execution. | T | Injected 1.5 raises an error. | MET |
| DI-004 | Each variable shall satisfy its physical range (Section 6). | T | Out-of-range injection is rejected. | NOT MET |
| DI-005 | Timestamps shall be unique and strictly increasing. | T | Duplicate or unsorted input is rejected. | NOT MET |
| DI-006 | The resampled DEM shape shall equal the target raster shape. | T | Assert passes for (100, 100). | MET |
| DI-007 | The cloud-cover ratio reported shall be computed from real data only. | I | Report suppressed or labelled `synthetic` otherwise. | NOT MET |

### 4.6 Uncertainty and quality requirements

| ID | Requirement | Method | Acceptance criterion | Status |
|---|---|---|---|---|
| UQ-001 | Every observed variable shall carry, or reference, a quality or uncertainty indicator usable as observation error in the EnKF. | I | Indicator column or documented fixed value per variable. | NOT MET |
| UQ-002 | The software shall not substitute fabricated values when expected data or columns are missing; it shall raise an error. | T | Missing column causes failure, no fallback. | NOT MET (Plot 4 silently substitutes random temperature) |

### 4.7 Non-functional requirements

| ID | Requirement | Method | Acceptance criterion | Status |
|---|---|---|---|---|
| NF-001 | When simulation is used, random seeds shall be fixed and documented. | T | Two runs give byte-identical CSV. | MET (not yet tested) |
| NF-002 | The software environment shall be pinned (exact package versions) in a lock file. | I | `environment.yml` or lock file committed. | NOT MET |
| NF-003 | The notebook shall run top-to-bottom without manual steps. | D | Clean kernel “Run All” completes with no error. | MET |
| NF-004 | Output paths shall be relative to the repository and created if absent. | T | Run from clean tree succeeds. | MET |
| NF-005 | Identifiers and file names shall be spelled consistently with this document. | I | No occurrence of `weayher`, `telementary`, `lebel`. | NOT MET |
| NF-006 | Unused imports and unused function parameters shall not be present. | I | Linter clean. | NOT MET |
| NF-007 | Plot styling values shall be valid (e.g. colour codes with `#`). | I | No invalid colour strings. | NOT MET |
| NF-008 | The copyright notice shall be present in the notebook and documents. | I | Notice present. | MET |

### 4.8 Interface requirements

| ID | Requirement | Method | Status |
|---|---|---|---|
| IF-001 | The output CSV shall contain a schema-version field or companion schema file. | I | NOT MET |
| IF-002 | The STAC Item shall be readable by standard STAC libraries. | T | PARTIAL |
| IF-003 | Downstream notebooks shall read only from `data/raw/`, never from in-memory state of this notebook. | I | MET |

---

## 5. Design Description

### 5.1 Structure (current)
Single notebook, sequential cells: setup → AOI constants → `fetch_aerospace_stac_telementary()` (to be renamed) → integrity audit → six plots → raster generation and DEM resampling → STAC dictionary → export.

### 5.2 Data structures
pandas DataFrame (35 × 15); NumPy arrays 100 × 100 (RED, NIR, SAR VV, NDVI, aligned DEM); 33 × 33 native DEM; Python dict for the STAC item.

### 5.3 Algorithms
Normalised-difference indices; `scipy.ndimage.zoom(order=1)` bilinear resampling; zoom factors = target size / native size.

### 5.4 Design constants (derived requirements, subject to review)
Buffer 0.05°; sample count 35; grid 100 × 100 at nominal 10 m; native DEM 33 × 33 at nominal 30 m; cloud threshold 50 %; seeds 42 and 101.

### 5.5 Target design (to satisfy Section 4)
Separate modules: `catalog` (STAC queries), `validate` (integrity checks), `raster_io` (COG writing), `stac_item` (metadata), `config` (AOI and constants). The notebook becomes a thin driver that calls them and prints results.

---

## 6. Data Dictionary — `data/raw/stac_telemetry_raw.csv` (target name)

| Column | Type | Unit | Valid range | Null allowed |
|---|---|---|---|---|
| timestamp | datetime64[ns] | UTC | within window; unique; increasing | No |
| crs | string | — | `EPSG:4326` | No |
| lat | float64 | deg | AOI bounds | No |
| lon | float64 | deg | AOI bounds | No |
| s1_vv_db | float64 | dB | −30 … 5 | Flagged |
| s1_vh_db | float64 | dB | −35 … 0 | Flagged |
| s2_cloud_cover_pct | float64 | % | 0 … 100 | Flagged |
| s2_b03_green | float64 | reflectance | 0 … 1 | Flagged |
| s2_b04_red | float64 | reflectance | 0 … 1 | Flagged |
| s2_b08_nir | float64 | reflectance | 0 … 1 | Flagged |
| dem_elevation_m | float64 | m MSL | site-specific, documented | No |
| weather_temp_c | float64 | °C | −10 … 50 | Flagged |
| weather_precip_mm | float64 | mm | ≥ 0 | Flagged |
| ndvi | float64 | — | −1 … 1 | Flagged |
| ndwi | float64 | — | −1 … 1 | Flagged |
| data_origin | string | — | `real` or `synthetic` | No |
| source_id | string | — | catalogue scene ID | No (real data) |

*(Current notebook writes `weayher_temp_c` and lacks `data_origin`, `source_id`; see defects.)*

---

## 7. Verification Procedures

Each procedure is executed from a clean kernel; results are recorded in Section 7.2.

### 7.1 Procedures

| Proc. | Verifies | Steps | Pass criterion |
|---|---|---|---|
| VP-01 | FR-001 | Call bbox function with (21.1378, 86.6874, 0.05). | Equals [86.6374, 21.0878, 86.7374, 21.1878]. |
| VP-02 | FR-003 | Generate table; read first/last timestamp and row count. | 35 rows; start and end equal parameters. |
| VP-03 | FR-020, DI-003 | Feed B04 = 0.1, B08 = 0.3 → NDVI 0.5; B03 = 0.2, B08 = 0.3 → NDWI −0.2. | Within 1e-9. |
| VP-04 | FR-023 | Feed B04 = B08 = 0. | NaN returned; warning logged. |
| VP-05 | FR-022, DI-006 | Resample 33 × 33 DEM. | Shape (100, 100); min/max within native min/max. |
| VP-06 | FR-030 | Run export; read CSV. | Columns and dtypes match Section 6. |
| VP-07 | FR-031 | Validate JSON with STAC schema validator. | Zero errors. |
| VP-08 | FR-032 | Check each asset href exists; open with rasterio. | CRS and transform present. |
| VP-09 | DI-001 | Insert row with a different CRS. | Execution halts with error. |
| VP-10 | DI-002 | Insert NaN. | Detected and reported. |
| VP-11 | DI-004 | Insert VV = 50 dB. | Rejected. |
| VP-12 | DI-005 | Duplicate a timestamp. | Rejected. |
| VP-13 | UQ-002 | Delete a required column before plotting. | Error raised; no random substitute. |
| VP-14 | NF-001 | Run twice; compare SHA-256. | Identical. |
| VP-15 | NF-003 | Kernel restart, Run All. | No error. |
| VP-16 | NF-005, NF-006, NF-007 | Search source and run linter. | No misspelt identifiers, unused imports or invalid colours. |
| VP-17 | FR-010 … FR-013 | Run ingestion against live catalogue for one date. | Real scene IDs returned and stored. |
| VP-18 | FR-034 | Re-read exported files and compare checksums. | Match. |

### 7.2 Verification Record (to be completed at each baseline)

| Proc. | Date | Executed by | Result (Pass/Fail) | Evidence reference | Reviewer |
|---|---|---|---|---|---|
| VP-01 … VP-18 | *(pending)* | | | | |

---

## 8. Traceability Matrix

| Project objective | Requirement(s) | Design item | Verification |
|---|---|---|---|
| Reproducible AOI and window | FR-001, FR-002, FR-003 | §5.1, §5.4 | VP-01, VP-02 |
| Real multi-sensor inputs | FR-010 … FR-014 | §5.5 `catalog` | VP-17 |
| Correct derived indices | FR-020, FR-021, FR-023 | §5.3 | VP-03, VP-04 |
| Common grid | FR-022, DI-006 | §5.3 | VP-05 |
| Auditable outputs | FR-030 … FR-034, IF-001/002 | §5.5 `stac_item`, `raster_io` | VP-06, VP-07, VP-08, VP-18 |
| Data trust | DI-001 … DI-007 | §5.5 `validate` | VP-09 … VP-12 |
| EnKF-ready quality information | UQ-001, UQ-002 | §6 | VP-13 |
| Reproducibility and hygiene | NF-001 … NF-008 | §5, §9 | VP-14, VP-15, VP-16 |

Every requirement above maps to at least one verification procedure; any requirement without one is an error in this document.

---

## 9. Configuration and Change Control

| Item | Rule |
|---|---|
| Repository | All files under Git; one tag per baseline (e.g. `NB01-BL-01`). |
| Controlled items | Notebook, `.rst`, this document, environment lock file, STAC schema, tests. |
| Notebook outputs | Stripped before commit (nbstripout or Jupytext); figures regenerated by Run All. |
| Environment | Exact package versions recorded; Python version recorded. |
| Data | `data/raw/` write-once per baseline; SHA-256 recorded. |
| Change process | Change request (ID, reason, affected requirement IDs) → impact analysis → review → implement → re-run affected VPs → update Section 7.2 and Section 1.1. |
| Document rule | A requirement change shall update Sections 4, 7 and 8 together. |

## 10. Review and Approval

| Review | Checks | Record |
|---|---|---|
| Requirements review | Each requirement is singular, testable, uniquely identified | *(pending)* |
| Code review | Code satisfies requirements; no silent fallbacks; naming consistent | *(pending)* |
| Verification review | VP results complete and match acceptance criteria | *(pending)* |

| Role | Name | Signature | Date |
|---|---|---|---|
| Author | Gourgopal Mohapatra | | |
| Reviewer | | | |
| Approver | | | |

---

## 11. Open Defects

| ID | Defect | Requirement | Fix |
|---|---|---|---|
| D1 | Data is simulated, not ingested | FR-010 … 014 | Implement catalogue queries (e.g. pystac-client) |
| D2 | Typos: `weayher_temp_c`, `telementary`, `processing_lebel`; Plot 4 falls back to random temperature because of the misspelt column | NF-005, UQ-002 | Rename; remove fallback |
| D3 | STAC key `assert` instead of `assets`; `links` missing; validation checks wrong key | FR-031 | Correct key; use schema validator |
| D4 | Colour `"00FFCC"` lacks `#` | NF-007 | Use `"#00FFCC"` |
| D5 | Summary cell file name differs from written file name | NF-005 | Align names |
| D6 | `geopandas`, `sys` unused; function ignores `bbox` argument and uses globals | NF-006 | Remove / pass parameters |
| D7 | AOI ≈ 11 km box vs ≈ 1 km raster grid | FR-001, FR-022 | One AOI definition; derive grid with affine transform |
| D8 | Rasters not georeferenced and not written, though STAC lists them | FR-032 | Write COGs with rasterio |
| D9 | No cloud/quality masking; no zero-denominator handling | FR-021, FR-023 | Implement |
| D10 | SAR preprocessing not defined (speckle, incidence angle, orbit) | scope for NB02 | Specify in NB02 requirements |
| D11 | No provenance, checksums, uncertainty indicators | FR-033, FR-034, UQ-001 | Add columns and checksum file |

## 12. Risks

| ID | Risk | Consequence | Mitigation |
|---|---|---|---|
| R1 | Synthetic data taken as real | Invalid science and engineering outputs | FR-014, DI-007 |
| R2 | Silent fabricated substitutes | Hidden false data in figures | UQ-002 |
| R3 | Invalid STAC / missing assets | Provenance lost | FR-031, FR-032 |
| R4 | No observation uncertainty | EnKF cannot be configured correctly | UQ-001 |
| R5 | Unpinned environment | Non-reproducible results | NF-002 |
| R6 | AOI mismatch | Spatial misregistration | D7 |

## 13. Baseline Release Criteria (NB01-BL-01)

1. Every requirement in Section 4 is **MET** or **WAIVED** with written rationale.
2. VP-01 … VP-18 executed and recorded as Pass in Section 7.2.
3. Defects D1–D11 closed or dispositioned.
4. Real-data ingestion demonstrated for at least one date per sensor.
5. Review and approval table (Section 10) signed by a reviewer other than the author.
6. Environment lock file, checksums and tag committed.

## 14. Intellectual Property Notice

© 2026 Gourgopal Mohapatra. Proprietary and confidential. The notebook, this document, and the associated architecture (PINN, EnKF, multi-modal data fusion) may not be copied, redistributed, reverse-engineered or used commercially, in whole or in part, without prior written authorisation from the lead researcher and JCC RS-SDA.
