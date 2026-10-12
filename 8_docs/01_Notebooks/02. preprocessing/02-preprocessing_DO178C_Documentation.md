# AETHER-MRID1607X — Notebook 02: Satellite Data Preprocessing

## Software Requirements, Design, Verification and Traceability Document (DO-178C-style)

---

## 0. Document Control

| Field | Value |
|:------|:------|
| **Document ID** | AETHER-MRID1607X-NB02-DOC-001 |
| **Document Title** | Software Requirements Data, Design Description, Verification Cases/Results and Trace Data for `02-preprocessing.ipynb` |
| **Project** | THE MRIDANSH |
| **Central Engine** | AETHER : MRID1607X (Multi-Domain Soil Intelligence Engine) |
| **Item Documented** | Jupyter notebook `02-preprocessing.ipynb` (Notebook 02, Sprint Days 3–4) |
| **Document Version** | 1.0 (Draft for Owner Review) |
| **Document Date** | 2026-10-06 |
| **Owner / Developer** | Gourgopal Mohapatra |
| **Organization** | JCC HEADQUARTER — JCC CAMPUS 2, RS-SDA Division |
| **Document Status** | Baseline-ready, pending owner review and approval |
| **Reviewer / Approver** | *(to be completed by owner)* |
| **Classification** | Confidential & Proprietary (see Appendix C) |

### 0.1 Revision History

| Version | Date | Author | Description |
|:--------|:-----|:-------|:------------|
| 0.1 | 2026-10-06 | Documentation pass | Reverse-engineered from notebook source, cell outputs and metadata |
| 1.0 | 2026-10-06 | Documentation pass | Requirements, design, verification, traceability and problem reports consolidated |

### 0.2 Important Notice on Certification Claims

This document is **structured after the life-cycle data items of RTCA DO-178C / EUROCAE ED-12C** (Software Requirements Data, Design Description, Verification Cases and Procedures, Verification Results, Configuration Index, Problem Reports, Trace Data). It is written to give the notebook the same *rigor of traceability and evidence*.

It is **not** a certification artifact. No Design Assurance Level (DAL) has been assigned by any certification authority, and no claim of DO-178C compliance is made. The notebook is research software for a remote-sensing / geotechnical data pipeline, not airborne software.

### 0.3 How Evidence Is Labeled in This Document

| Tag | Meaning |
|:----|:--------|
| **[NB]** | Evidence taken directly from the saved notebook (source code, saved cell outputs, metadata) |
| **[AN]** | Evidence obtained by re-executing the notebook logic offline during this documentation pass (same seed, same code). All offline re-execution results for the values printed by the notebook matched the notebook's printed values exactly |
| **[INS]** | Evidence from manual inspection of source text |

---

## 1. Introduction

### 1.1 Purpose

This document defines, for `02-preprocessing.ipynb`:

1. what the software is required to do (high-level, low-level and derived requirements),
2. how it is designed to do it (architecture, algorithms, data structures, parameters),
3. how each requirement is verified and what the verification evidence shows,
4. the complete bidirectional traceability between requirements, design, code cells and verification cases,
5. every discrepancy, defect and limitation found between *what the notebook claims* and *what the notebook does* (Section 12).

### 1.2 Scope

In scope: every one of the 29 cells of the notebook (13 code cells, 16 markdown cells), all 4 figures, all printed audit reports, and both exported artifacts.

Out of scope: Notebook 01 (data ingestion), Notebook 03 (GCN spatial modeling), PINN/EnKF components, and the Kaggle platform itself.

### 1.3 Notebook Purpose (Summary)

Notebook 02 takes a 35-record Sentinel-1 (SAR) / Sentinel-2 (optical) / DEM telemetry table and performs:

- NDVI derivation,
- Sentinel-2 cloud quality control (threshold ≤ 50 % cloud cover),
- Sentinel-1 VV 1-D temporal Lee speckle filtering,
- 80/20 chronological train/test partition,
- Z-score scaling (SAR VV-Lee, SAR VH, DEM) and Min-Max scaling (NDVI) fitted on the training partition,
- integrity assertions,
- export of `preprocessed_telemetry.csv` and `scaler_manifest.json`.

### 1.4 Intended Audience

Project owner, algorithm developers (Notebook 03 / PINN / GCN), reviewers, and anyone auditing data-leakage claims.

### 1.5 Document Conventions

- **shall** = mandatory requirement; **should** = recommended; **may** = permitted.
- Cell references use the **0-based cell index** `C00`…`C28` (Section 4.3).
- Requirement IDs: `HLR-nn` (high-level), `LLR-nn` (low-level), `DR-nn` (derived), `NFR-nn` (non-functional / constraint), `IF-nn` (interface), `VC-nn` (verification case), `PR-nn` (problem report).
- Verification methods: **T** = Test (execution), **I** = Inspection, **A** = Analysis, **D** = Demonstration.

---

## 2. Reference Documents

| Ref | Document |
|:----|:---------|
| [R1] | RTCA DO-178C / EUROCAE ED-12C, *Software Considerations in Airborne Systems and Equipment Certification* (structure used as a model only) |
| [R2] | `02-preprocessing.ipynb`, 642,415 bytes, nbformat 4.4 (item under documentation) |
| [R3] | Notebook 01 (data ingestion; artifact `stac_telemetry_raw.csv` referenced by Step 1 markdown; **not provided**) |
| [R4] | Notebook 03 (Spatial Modeling & GCN; downstream consumer; **not provided**) |
| [R5] | J.-S. Lee, "Digital image enhancement and noise filtering by use of local statistics," IEEE TPAMI, 1980 (algorithm family of the Lee filter) |
| [R6] | ESA Sentinel-2 Level-2A Scene Classification Layer (SCL) specification (cited by the notebook narrative only) |

---

## 3. Definitions and Acronyms

| Term | Definition |
|:-----|:-----------|
| AETHER-MRID1607X | Central engine of project THE MRIDANSH |
| DEM | Digital Elevation Model |
| DAL | Design Assurance Level (DO-178C A–E) |
| EnKF | Ensemble Kalman Filter |
| GCN | Graph Convolutional Network |
| HLR / LLR / DR | High-Level / Low-Level / Derived Requirement |
| NDVI | Normalized Difference Vegetation Index, (NIR − Red) / (NIR + Red) |
| PINN | Physics-Informed Neural Network |
| QC | Quality Control |
| SAR | Synthetic Aperture Radar |
| SCL | Sentinel-2 Scene Classification Layer |
| S1 / S2 | Sentinel-1 / Sentinel-2 |
| VV / VH | SAR polarization channels (vertical-vertical / vertical-horizontal) |
| STAC | SpatioTemporal Asset Catalog |
| θv | Volumetric soil moisture (project target quantity) |
| Train / Test | First 80 % / last 20 % of the chronologically ordered records |
| Leakage | Any dependence of training-side computation on test-period data |

---

## 4. Notebook Identification and Configuration Index

### 4.1 Item Identification

| Attribute | Value | Source |
|:----------|:------|:-------|
| File name | `02-preprocessing.ipynb` | upload |
| Internal self-name (manifest) | `02_preprocessing.ipynb` (underscore; see PR-12) | [NB] C26 |
| File size | 642,415 bytes | [AN] |
| Notebook format | nbformat 4, minor 4 | [NB] |
| Kernel | `python3` ("Python 3") | [NB] |
| Language / version | Python 3.12.13 | [NB] |
| Platform metadata | Kaggle notebook (`sourceType: notebook`) | [NB] |
| Accelerator | none (`isGpuEnabled: false`) | [NB] |
| Internet | disabled (`isInternetEnabled: false`) | [NB] |
| Attached data sources | none (`dataSources: []`) | [NB] |
| Docker image version id | 28755 | [NB] |
| Execution counts | 30 → 42, strictly increasing in cell order (13 code cells) | [NB] |
| Execution errors in saved outputs | none (no `error` outputs) | [NB] |
| Embedded figures | 4 PNG (`display_data`) in C08, C12, C20, C22 | [NB] |

### 4.2 Library Baseline

Exact library versions are **not recorded** in the notebook (see PR-15). The following is inferred.

| Library | Used for | Version evidence |
|:--------|:---------|:-----------------|
| Python | runtime | 3.12.13 [NB] |
| NumPy | arrays, RNG, `where`, `maximum` | ≥ 2.0 inferred, because printed dictionary shows `np.float64(...)` reprs [NB] |
| pandas | DataFrame, `date_range`, CSV I/O | not recorded |
| SciPy (`scipy.ndimage`) | `uniform_filter` (used); `variance` (imported, **unused**) | not recorded |
| Matplotlib | plotting, dark theme | not recorded |
| json, os, sys | stdlib (`sys` imported, **unused**) | stdlib |

Offline reproduction used NumPy 2.4.4, pandas 3.0.2, SciPy 1.17.1, Matplotlib 3.10.8 [AN] and reproduced every printed number.

### 4.3 Cell Inventory (Complete)

| Cell | Type | Exec # | Title / Role | Section in this document |
|:----:|:----:|:------:|:-------------|:-------------------------|
| C00 | MD | — | Project banner, engine, division, framework, operational target | 1, 5 |
| C01 | MD | — | Notebook 02 header, sprint objective, Lee and Min-Max math | 8.2, 8.3 |
| C02 | Code | 30 | Imports and Matplotlib dark-theme configuration | 8.1 |
| C03 | MD | — | Step 1 description (claims load from Notebook 01) | 8.2 |
| C04 | Code | 31 | In-memory telemetry generator, NDVI, write raw CSV | 8.2 |
| C05 | MD | — | Step 2 description (cloud QC, 50 % threshold) | 8.3 |
| C06 | Code | 32 | Cloud-QC flag and NDVI masking, counts report | 8.3 |
| C07 | MD | — | Plot 1 description | 13 |
| C08 | Code | 33 | Plot 1: raw vs masked NDVI | 13 |
| C09 | MD | — | Step 3 description (Lee filter) | 8.4 |
| C10 | Code | 34 | `apply_lee_filter_1d`, apply to VV, variance report | 8.4 |
| C11 | MD | — | Plot 2 description | 13 |
| C12 | Code | 35 | Plot 2: raw vs Lee-filtered VV | 13 |
| C13 | MD | — | Step 4 description (leakage invariant) | 8.5 |
| C14 | Code | 36 | Split index, train stats, `s1_vv_normalized`, audit report (Day 3) | 8.5 |
| C15 | MD | — | Part 2 header (Day 4), Z-score and Min-Max math | 8.6 |
| C16 | Code | 37 | Feature list, `df_proc`, split bounds report | 8.6 |
| C17 | MD | — | Step 5 description | 8.7 |
| C18 | Code | 38 | Z-score (3 columns) + NDVI Min-Max, `train_stats` | 8.7 |
| C19 | MD | — | Plot 3 description | 13 |
| C20 | Code | 39 | Plot 3: distributions, raw vs Z-score | 13 |
| C21 | MD | — | Plot 4 description | 13 |
| C22 | Code | 40 | Plot 4: scaled multi-sensor series + split boundary | 13 |
| C23 | MD | — | Step 6 description (integrity audit) | 8.8 |
| C24 | Code | 41 | Assertions and final audit report | 8.8 |
| C25 | MD | — | Step 7 description (export) | 8.9 |
| C26 | Code | 42 | Export CSV and scaler manifest JSON | 8.9 |
| C27 | MD | — | Executive summary and milestones claims | 12, App. B |
| C28 | MD | — | IP and copyright notice | App. C |

---

## 5. System Context and Software Overview

### 5.1 Position in the Pipeline

```
  Notebook 01                    Notebook 02 (this item)                  Notebook 03
 (ingestion, STAC)   --------->  Preprocessing / QC / Despeckle / Scale  ---------> (GCN spatial
 stac_telemetry_raw.csv         preprocessed_telemetry.csv                         modeling)
 [not provided]                 scaler_manifest.json
```

> **Note [NB]:** In the delivered notebook, the raw table is *not* read from Notebook 01. It is regenerated in memory (C04) from a seeded random generator and then written to `data_raw/`. See PR-01.

### 5.2 Internal Data Flow

```
 C04  df_raw (8 cols, 35 rows)
        |
        v
 C06  df_qc  = df_raw + optical_qc_pass + ndvi_masked
        |
        v
 C10  df_qc  += s1_vv_lee                           (Lee filter on FULL series)
        |
        v
 C14  df_qc  += s1_vv_normalized                    (train mean/std, split_idx = 28)
        |
        v
 C16  df_proc = df_qc.copy();  train_df = [0:28];  test_df = [28:35]
        |
        v
 C18  scaled_df = df_proc + 3 z-score cols + ndvi_minmax;   train_stats{}
        |
        v
 C24  assertions (nulls, train z-mean/std, row count)
        |
        v
 C26  preprocessed_telemetry.csv  +  scaler_manifest.json
```

### 5.3 Software Characteristics

| Characteristic | Value |
|:---------------|:------|
| Execution model | Sequential, single-process, top-to-bottom cell execution; no concurrency |
| Data volume | N = 35 records; ≈ 16 columns; negligible compute and memory |
| External inputs at run time | none (all data synthetic, in-memory) |
| Outputs | 2 files, 4 figures, console reports |
| Persistent state | shared kernel namespace between cells (cells depend on earlier cells' variables) |
| Randomness | `numpy.random.seed(42)` once, in C04 |
| Safety-/hazard relevance | Indirect: output feeds downstream subgrade-stability (shear-strength) estimation; faulty preprocessing may bias downstream estimates |

### 5.4 Assumed Assurance Level (Informative)

No DAL is formally assigned. Because the downstream product concerns geotechnical stability, a failure of this stage is judged to yield *degraded accuracy* (not direct hazard) of an advisory estimate. For documentation rigor the *structure* of DAL D/C-type objectives (requirements, trace, verification, problem reporting) is applied. This is an informative assumption only and should be confirmed by the owner.

---

## 6. Software Life-Cycle Environment

| Item | Description |
|:-----|:------------|
| Development environment | Kaggle hosted Jupyter notebook, CPU only, internet disabled |
| Execution order requirement | C02 → C04 → C06 → C08 → C10 → C12 → C14 → C16 → C18 → C20 → C22 → C24 → C26 (as executed, counts 30–42) |
| Hard-coded paths | `/kaggle/working/data_raw`, `/kaggle/working/data_processed` |
| Plot theme | `plt.style.use('dark_background')`; monospace font; edge color `#00FFCC`; line width 1.2; grid `#1A3344`, dashed, alpha 0.5 |
| Magic commands | `%matplotlib inline` |
| Version control | none recorded (no commit hash / tag in notebook) |
| Build / compile | none (interpreted) |

---

## 7. Software Requirements Data

### 7.1 High-Level Requirements (HLR)

Status legend: **Met**, **Met with deviation**, **Partially met**, **Not met**.

| ID | Requirement (shall statement) | Rationale | Method | Status |
|:---|:------------------------------|:----------|:------:|:-------|
| **HLR-01** | The software **shall** provide a raw telemetry table `df_raw` of 35 chronologically ordered records with fields `timestamp`, `s1_vv_db`, `s1_vh_db`, `s2_cloud_cover_pct`, `s2_b04_red`, `s2_b08_nir`, `dem_elevation_m`. | Common input contract for all later steps | T, I | **Met with deviation** (data synthetic, not read from Notebook 01; PR-01) |
| **HLR-02** | The software **shall** compute NDVI = (NIR − Red) / (NIR + Red) for every record. | Vegetation proxy for moisture modeling | T | **Met** |
| **HLR-03** | The software **shall** persist the raw table as CSV to `/kaggle/working/data_raw/stac_telemetry_raw.csv`, creating the directory if absent. | Reproducible raw data lake artifact | T | **Met** |
| **HLR-04** | The software **shall** classify each record as optical-QC-pass when `s2_cloud_cover_pct` ≤ 50.0 and **shall** set NDVI to NaN for records that fail, without deleting rows. | Prevent cloud-corrupted indices entering models | T | **Met with deviation** (percentage threshold; SCL bitmask not used; PR-02) |
| **HLR-05** | The software **shall** report the number and percentage of QC-passed and QC-masked records. | Visibility of data loss | T | **Met** |
| **HLR-06** | The software **shall** produce a speckle-reduced Sentinel-1 VV series `s1_vv_lee` using an adaptive Lee filter, `Î = Ī + W·(I − Ī)`, `W = Var(I)/(Var(I)+σn²)`. | Noise reduction of SAR backscatter | T, A | **Met with deviation** (1-D temporal, dB domain, global σn² estimate; PR-11) |
| **HLR-07** | The software **shall** partition the records chronologically (no shuffling) into a training set of the first `floor(0.8·N)` records and a test set of the remaining records. | Temporal hold-out validation | T | **Met** |
| **HLR-08** | The software **shall** derive Z-score parameters (mean, standard deviation) for `s1_vv_lee`, `s1_vh_db`, `dem_elevation_m` and Min-Max parameters (min, max) for `ndvi_masked` **exclusively from the training partition**, and apply them to all records. | Leakage-constrained scaling | T, A | **Met** (for scaler parameters) |
| **HLR-09** | The software **shall** ensure that no training-side value, statistic or parameter depends on any test-period sample (zero-future-leakage invariant). | Scientific validity of hold-out evaluation | A | **Partially met** — violated in the SAR despeckling stage (PR-03) |
| **HLR-10** | The software **shall** verify, with run-halting assertions, (a) zero nulls in the three Z-score columns, (b) training Z-score mean < 1e-4 in magnitude and standard deviation within 1e-2 of 1.0, (c) train + test row count equals total row count. | Detect preprocessing corruption before persistence | T | **Met** (limited coverage; PR-05, PR-07) |
| **HLR-11** | The software **shall** export the preprocessed table as `/kaggle/working/data_processed/preprocessed_telemetry.csv`, creating the directory if absent. | Hand-off to Notebook 03 | T | **Met** |
| **HLR-12** | The software **shall** export a scaler manifest `/kaggle/working/data_processed/scaler_manifest.json` containing project, engine, notebook name, split index, train/test counts and all scaler parameters. | Reproducible inverse/forward scaling downstream | T | **Met** |
| **HLR-13** | The software **shall** render four diagnostic figures (NDVI QC, SAR despeckling, scaling distributions, multi-sensor series) with embedded textual diagnostics. | Human-verifiable evidence | D | **Met** (annotation defects; PR-09, PR-10) |
| **HLR-14** | The software **shall** print a status/audit report for every processing stage. | Execution traceability | T | **Met** |
| **HLR-15** | The software **shall** be deterministic: re-execution in the same environment shall yield identical numerical outputs. | Reproducibility | T, A | **Met** (seeded; versions unpinned, PR-15) |

### 7.2 Low-Level Requirements (LLR)

| ID | Low-level requirement | Cell | Parent HLR |
|:---|:----------------------|:----:|:-----------|
| **LLR-01** | Import `sys, os, numpy as np, pandas as pd, json, scipy.ndimage.uniform_filter, scipy.ndimage.variance, matplotlib.pyplot as plt`. | C02 | HLR-15 |
| **LLR-02** | Select inline Matplotlib backend and set theme: `dark_background`, monospace font, axes edge `#00FFCC`, axes line width 1.2, grid `#1A3344`, linestyle `--`, alpha 0.5. | C02 | HLR-13 |
| **LLR-03** | Print initialization banner `⚡ [AETHER-SYSTEMS] Preprocessing Environment & Aerospace Theme Initialized!`. | C02 | HLR-14 |
| **LLR-04** | Call `np.random.seed(42)` before any random draw. | C04 | HLR-15 |
| **LLR-05** | Create `timestamp = pd.date_range("2026-08-01","2026-09-07", periods=35)` (inclusive endpoints, constant step 1 d 02 h 07 min 03.53 s). | C04 | HLR-01 |
| **LLR-06** | Draw, in this exact order, 35 samples each from uniform distributions: `s1_vv_db` U(−18, −8); `s1_vh_db` U(−25, −14); `s2_cloud_cover_pct` U(0, 90); `s2_b04_red` U(0.02, 0.18); `s2_b08_nir` U(0.20, 0.52). | C04 | HLR-01, HLR-15 |
| **LLR-07** | Set `dem_elevation_m` to constant 18.5 for all records. | C04 | HLR-01 |
| **LLR-08** | Compute `ndvi = (s2_b08_nir − s2_b04_red) / (s2_b08_nir + s2_b04_red)`. | C04 | HLR-02 |
| **LLR-09** | Create `/kaggle/working/data_raw` (`exist_ok=True`) and write `df_raw` to `stac_telemetry_raw.csv` with `index=False`. | C04 | HLR-03 |
| **LLR-10** | Print record count and output path; display first 3 rows (`head(3)`). | C04 | HLR-14 |
| **LLR-11** | Copy `df_raw` to `df_qc`; set `optical_qc_pass = (s2_cloud_cover_pct <= 50.0)` (threshold inclusive). | C06 | HLR-04 |
| **LLR-12** | Set `ndvi_masked = where(optical_qc_pass, ndvi, NaN)`. | C06 | HLR-04 |
| **LLR-13** | Compute `valid_count = sum(optical_qc_pass)`, `corrupted_count = N − valid_count`; print totals and percentages to 1 decimal. | C06 | HLR-05 |
| **LLR-14** | Plot 1 per Section 13.1 (raw NDVI, masked NDVI, red vertical lines at each masked timestamp, legend, diagnostics box). | C08 | HLR-13 |
| **LLR-15** | Define `apply_lee_filter_1d(series, window_size=3)` per Section 8.4 (local mean, local mean of squares, variance clamped ≥ 0, `noise_var = mean(var) + 1e-6`, weight, filtered output). | C10 | HLR-06 |
| **LLR-16** | Apply it to `df_qc['s1_vv_db']` with `window_size=3`, store as `s1_vv_lee`; print raw and filtered sample variance (4 decimals). | C10 | HLR-06, HLR-14 |
| **LLR-17** | Plot 2 per Section 13.2 (raw VV, Lee VV, diagnostics box with variance values and percentage reduction). | C12 | HLR-13 |
| **LLR-18** | Compute `split_idx = int(len(df_qc)*0.8)`; `train_slice = iloc[:split_idx]`, `test_slice = iloc[split_idx:]`. | C14 | HLR-07 |
| **LLR-19** | Compute `train_mean`, `train_std` (pandas, ddof = 1) of `s1_vv_lee` on `train_slice`; set `s1_vv_normalized = (s1_vv_lee − train_mean)/train_std` for all rows. | C14 | HLR-08 |
| **LLR-20** | Print the "Data Leakage Audit Report (Day 3)" (split index, train/test frame counts, normalization statistics, status line). | C14 | HLR-14 |
| **LLR-21** | Define `feature_cols`; copy `df_qc` to `df_proc`; set `SPLIT_RATIO = 0.8`; `split_index = int(len(df_proc)*SPLIT_RATIO)`; `train_df = df_proc.iloc[:split_index]`; `test_df = df_proc.iloc[split_index:]`. | C16 | HLR-07 |
| **LLR-22** | Print temporal split bounds with first/last dates (`%Y-%m-%d`) of each window. | C16 | HLR-14 |
| **LLR-23** | For each of `s1_vv_lee, s1_vh_db, dem_elevation_m`: `mean_val = train_df[col].mean()`; `std_val = train_df[col].std() + 1e-6`; store in `train_stats`; add `<col>_zscore = (df_proc[col] − mean_val)/std_val` to `scaled_df`. | C18 | HLR-08 |
| **LLR-24** | Compute `ndvi_min`, `ndvi_max` over non-NaN `ndvi_masked` in `train_df`; store in `train_stats['ndvi_masked']`; add `ndvi_minmax = (ndvi_masked − ndvi_min)/(ndvi_max − ndvi_min + 1e-6)` to `scaled_df`. NaNs propagate. | C18 | HLR-08 |
| **LLR-25** | Print scaler bounds dictionary. | C18 | HLR-14 |
| **LLR-26** | Plot 3 per Section 13.3 (two histograms, Z-score diagnostics box, suptitle). | C20 | HLR-13 |
| **LLR-27** | Plot 4 per Section 13.4 (scaled VV, scaled NDVI, dashed train/test boundary at `df_proc.iloc[split_index]['timestamp']`). | C22 | HLR-13 |
| **LLR-28** | Assert `scaled_df[['s1_vv_lee_zscore','s1_vh_db_zscore','dem_elevation_m_zscore']].isnull().sum().sum() == 0`. | C24 | HLR-10 |
| **LLR-29** | Assert `abs(train_z.mean()) < 1e-4` and `abs(train_z.std() − 1.0) < 1e-2` for `s1_vv_lee_zscore` over the training rows. | C24 | HLR-10 |
| **LLR-30** | Assert `len(train_df) + len(test_df) == len(scaled_df)`. | C24 | HLR-10 |
| **LLR-31** | Print the "Preprocessing Final Audit Report" with three PASSED lines (printed only if assertions pass). | C24 | HLR-14, HLR-10 |
| **LLR-32** | Create `/kaggle/working/data_processed` (`exist_ok=True`); write `scaled_df` to `preprocessed_telemetry.csv` (`index=False`). | C26 | HLR-11 |
| **LLR-33** | Build manifest dict with keys `Project`, `engine`, `notebook`, `temporal_split_index`, `train_sample_count`, `test_sample_count`, `feature_scaler_parameters`; write JSON (`indent=2`) to `scaler_manifest.json`. | C26 | HLR-12 |
| **LLR-34** | Print completion banner with the two output paths and the "Ready for Notebook 03" line. | C26 | HLR-14 |

### 7.3 Derived Requirements (DR)

Derived requirements are behaviors present in the code that are **not directly traceable** to an HLR text. In DO-178C practice they must be reviewed for impact on the system-level assessment.

| ID | Derived requirement (as implemented) | Cell | Impact assessment |
|:---|:-------------------------------------|:----:|:------------------|
| **DR-01** | `uniform_filter` operates with its default boundary mode `reflect`; edge samples therefore use mirrored neighbors. | C10 | Edge values (index 0 and 34) are smoothed using a duplicated sample. Low |
| **DR-02** | Local variance is clamped to ≥ 0 with `np.maximum` to remove negative round-off. | C10 | Numerical safety. None |
| **DR-03** | Lee noise variance σn² is estimated as `mean(local variance) + 1e-6` over the **entire** series (35 samples, both partitions). | C10 | Introduces cross-partition dependence (PR-03). **High** |
| **DR-04** | A 1e-6 epsilon is added to every Z-score standard deviation and to the Min-Max denominator. | C18 | Prevents division by zero; yields Z-std marginally < 1.0 and a constant-feature Z-score of exactly 0 (PR-06). Low |
| **DR-05** | Cloud-masked NDVI values remain NaN in `ndvi_minmax`; they are neither dropped nor interpolated. | C18 | 16 NaN in the exported file (PR-05). Medium |
| **DR-06** | `s1_vv_normalized` (C14) is an additional exported column, near-duplicate of `s1_vv_lee_zscore`. | C14, C26 | Redundant column in exported artifact (PR-08). Low |
| **DR-07** | `s1_vh_db` is **not** despeckled; Z-score is applied to raw VH. | C18 | Asymmetric treatment of polarizations (PR-11). Medium |
| **DR-08** | `s2_cloud_cover_pct` and `s2_b04_red`, `s2_b08_nir`, `ndvi` (unmasked), `s1_vv_db` are passed through unscaled to the export. | C26 | Downstream must select the correct columns. Low |
| **DR-09** | Timestamps are timezone-naive although axes are labeled UTC. | C04, C08 | Labeling ambiguity (PR-10). Low |
| **DR-10** | The split index is computed twice independently (`split_idx` in C14, `split_index` in C16) with the same formula. | C14, C16 | Duplication; consistency holds only while both formulas stay identical (PR-08). Low |

### 7.4 Non-Functional Requirements and Constraints

| ID | Requirement / constraint | Status |
|:---|:-------------------------|:-------|
| **NFR-01** | The notebook shall run with no internet access and no attached datasets. | Met [NB] |
| **NFR-02** | The notebook shall run on CPU only. | Met [NB] |
| **NFR-03** | The notebook shall execute without raised exceptions in a fresh kernel when cells are run in order. | Met in saved run (no error outputs) [NB]; fresh-kernel run not independently executed on Kaggle |
| **NFR-04** | Output paths shall be writable under `/kaggle/working`. | Met on Kaggle; **not portable** to other hosts (PR-12) |
| **NFR-05** | Runtime shall be negligible (N = 35; vectorized NumPy/pandas). | Met (no timing recorded) |
| **NFR-06** | Cells shall be executed strictly in order (state shared via kernel namespace). | Constraint |
| **NFR-07** | Visual style shall use the project "Aerospace" dark theme. | Met |

### 7.5 Interface Requirements

#### IF-01 — Input data contract (`df_raw`)

| Column | dtype | Unit | Generator / range | Notes |
|:-------|:------|:-----|:------------------|:------|
| `timestamp` | datetime64 | (naive, labeled UTC) | 35 points 2026-08-01 → 2026-09-07 inclusive | step ≈ 26 h 07 min 03.5 s |
| `s1_vv_db` | float64 | dB | U(−18.0, −8.0) | Sentinel-1 VV backscatter |
| `s1_vh_db` | float64 | dB | U(−25.0, −14.0) | Sentinel-1 VH backscatter |
| `s2_cloud_cover_pct` | float64 | % | U(0.0, 90.0) | Sentinel-2 cloud cover |
| `s2_b04_red` | float64 | reflectance | U(0.02, 0.18) | Band 4 |
| `s2_b08_nir` | float64 | reflectance | U(0.20, 0.52) | Band 8 |
| `dem_elevation_m` | float64 | m | constant 18.5 | elevation |
| `ndvi` | float64 | – | derived | range [−1, 1]; with these draws always positive |

#### IF-02 — Output data contract (`preprocessed_telemetry.csv`, 16 columns, 35 rows, in this order)

| # | Column | Origin cell | Meaning | NaN possible |
|:-:|:-------|:-----------:|:--------|:------------:|
| 1 | `timestamp` | C04 | acquisition time | no |
| 2 | `s1_vv_db` | C04 | raw VV (dB) | no |
| 3 | `s1_vh_db` | C04 | raw VH (dB) | no |
| 4 | `s2_cloud_cover_pct` | C04 | cloud cover (%) | no |
| 5 | `s2_b04_red` | C04 | red reflectance | no |
| 6 | `s2_b08_nir` | C04 | NIR reflectance | no |
| 7 | `dem_elevation_m` | C04 | elevation (m) | no |
| 8 | `ndvi` | C04 | unmasked NDVI | no |
| 9 | `optical_qc_pass` | C06 | boolean QC flag | no |
| 10 | `ndvi_masked` | C06 | NDVI, NaN where QC failed | **yes (16)** |
| 11 | `s1_vv_lee` | C10 | Lee-filtered VV (dB) | no |
| 12 | `s1_vv_normalized` | C14 | VV-Lee Z-score using ddof=1 std, no epsilon | no |
| 13 | `s1_vv_lee_zscore` | C18 | VV-Lee Z-score, std + 1e-6 | no |
| 14 | `s1_vh_db_zscore` | C18 | VH Z-score | no |
| 15 | `dem_elevation_m_zscore` | C18 | DEM Z-score (all 0.0) | no |
| 16 | `ndvi_minmax` | C18 | NDVI Min-Max (train bounds) | **yes (16)** |

#### IF-03 — Scaler manifest (`scaler_manifest.json`)

```json
{
  "Project": "THE MRIDANSH",
  "engine": "AETHER-MRID1607X",
  "notebook": "02_preprocessing.ipynb",
  "temporal_split_index": 28,
  "train_sample_count": 28,
  "test_sample_count": 7,
  "feature_scaler_parameters": {
    "s1_vv_lee":       {"mean": -13.510027922701811, "std": 2.197309599467909},
    "s1_vh_db":        {"mean": -19.648007479125024, "std": 3.4012699200375653},
    "dem_elevation_m": {"mean": 18.5,                "std": 1e-06},
    "ndvi_masked":     {"min": 0.18364952752897318,  "max": 0.7692757597519014}
  }
}
```

Values from the saved C18 output [NB]. Note that `std` already includes the +1e-6 epsilon (DR-04) and that `ndvi_masked` bounds are computed over the 14 QC-passed training frames [AN].

#### IF-04 — Intermediate raw artifact

`/kaggle/working/data_raw/stac_telemetry_raw.csv`: the 8 columns of IF-01, 35 rows, no index column.

---

## 8. Software Design Description

### 8.1 Initialization (C02)

- Imports (LLR-01) and theme (LLR-02).
- `%matplotlib inline` makes figures render in the output area.
- Unused imports: `sys`, `scipy.ndimage.variance` (PR-08). `json` is imported again in C26 (harmless).

### 8.2 Step 1 — Telemetry Provisioning (C03, C04)

**Narrative claim [NB C03]:** loads `stac_telemetry_raw.csv` from Notebook 01.
**Actual implementation [NB C04]:** a seeded in-memory generator, with the comment *"Bypasses File Path Issues"*.

Algorithm:

1. `np.random.seed(42)`.
2. Build timestamp vector (35 evenly spaced instants).
3. Draw five uniform vectors in the fixed order of LLR-06. **The order is part of the design**: changing it changes every downstream number.
4. Set DEM constant.
5. Compute NDVI.
6. Create directory, write CSV.
7. Print counts and `head(3)`.

Reference output (first 3 rows) [NB]:

| idx | timestamp | s1_vv_db | s1_vh_db | cloud % | b04 | b08 | dem | ndvi |
|:---:|:----------|---------:|---------:|--------:|----:|----:|----:|-----:|
| 0 | 2026-08-01 00:00:00 | −14.254599 | −16.107629 | 69.502029 | 0.059887 | 0.507983 | 18.5 | 0.789083 |
| 1 | 2026-08-02 02:07:03.53 | −8.492857 | −21.649249 | 17.884411 | 0.085661 | 0.280570 | 18.5 | 0.532202 |
| 2 | 2026-08-03 04:14:07.06 | −10.680061 | −23.925607 | 0.496991 | 0.140888 | 0.359120 | 18.5 | 0.436456 |

### 8.3 Step 2 — Sentinel-2 Cloud Quality Control (C05, C06)

$$\text{QC}_i = \begin{cases}\text{True} & c_i \le 50.0\\ \text{False} & c_i > 50.0\end{cases}\qquad
\text{NDVI}^{\text{masked}}_i = \begin{cases}\text{NDVI}_i & \text{QC}_i\\ \text{NaN} & \text{otherwise}\end{cases}$$

where `c_i` is `s2_cloud_cover_pct`. The mask removes information **by value**, not by row: all 35 rows persist.

Observed result [NB]: **19 / 35 pass (54.3 %)**, **16 / 35 masked (45.7 %)**.

Design remark: the markdown calls this "SCL Bitmasking" (C01, C27), but no SCL band is read; the mask is a scalar threshold on a pre-aggregated cloud-percentage (PR-02).

### 8.4 Step 3 — Sentinel-1 VV Lee Speckle Filter (C09, C10)

Specified formula (C01):

$$\hat{I} = \bar{I} + W\,(I-\bar{I}),\qquad W=\frac{\operatorname{Var}(I)}{\operatorname{Var}(I)+\sigma_n^2}$$

Implemented algorithm `apply_lee_filter_1d(series, window_size=3)`:

| Step | Operation | Code |
|:----:|:----------|:-----|
| 1 | Cast to float64 NumPy | `series.to_numpy(dtype=float)` |
| 2 | Local mean `Ī` | `uniform_filter(x, size=3)` |
| 3 | Local mean of squares | `uniform_filter(x**2, size=3)` |
| 4 | Local variance | `var = mean_sq − mean**2` |
| 5 | Clamp | `var = np.maximum(var, 0)` |
| 6 | Noise variance | `noise_var = np.mean(var) + 1e-6` |
| 7 | Weight | `W = var / (var + noise_var)` |
| 8 | Output | `mean + W * (x − mean)` |

Properties:

- 1-D **temporal** window of 3 samples (centered, boundary mode `reflect`), not a 2-D spatial window.
- Applied in **dB (logarithmic) domain** to VV only.
- σn² is a single scalar for the whole series (≈ 5.8118 dB² [AN]); it is *not* derived from the number of looks (ENL).
- Because the window is centered, the output at index *k* uses samples *k−1, k, k+1*.

Observed result [NB]: raw variance **9.0643** → filtered variance **5.7011**. Relative variance reduction = (9.0643 − 5.7011)/9.0643 = **37.1 %** [AN, matches the figure annotation formula].

### 8.5 Step 4 — Day-3 Leakage Invariant Check (C13, C14)

1. `split_idx = int(35 × 0.8) = 28`.
2. `train_slice = rows 0–27`, `test_slice = rows 28–34`.
3. `train_mean = −13.51`, `train_std = 2.20` (of `s1_vv_lee`, train rows only).
4. `s1_vv_normalized` computed for all 35 rows.
5. Report printed. Line 5 is a **hard-coded string** `PASSED (Zero Future Leakage)` and is not computed from any check (PR-03, PR-07).

### 8.6 Part 2 — Temporal Split Definition (C15, C16)

`split_index = 28`; train = 28 frames (2026-08-01 → 2026-08-30); test = 7 frames (2026-08-31 → 2026-09-07) [NB].

The printed labels `t <= 28` (train) and `t > 28` (test) are **off by one** relative to the Python slicing used: train covers indices 0…27 (`t < 28`), test covers 28…34 (`t ≥ 28`) (PR-04).

`feature_cols = ['s1_vv_lee','s1_vh_db','ndvi_masked','s2_cloud_cover_pct','dem_elevation_m']` is defined but never used (PR-08).

### 8.7 Step 5 — Zero-Leakage Feature Normalization (C17, C18)

Z-score for `col ∈ {s1_vv_lee, s1_vh_db, dem_elevation_m}`:

$$z = \frac{x-\mu_{\text{train}}}{\sigma_{\text{train}}+10^{-6}}$$

Min-Max for NDVI:

$$\text{ndvi\_minmax}=\frac{\text{ndvi\_masked}-\min_{\text{train}}}{\max_{\text{train}}-\min_{\text{train}}+10^{-6}}$$

with `min`/`max` over non-NaN training values (14 values [AN]).

Observed parameters [NB]:

| Feature | Parameter 1 | Parameter 2 |
|:--------|:------------|:------------|
| `s1_vv_lee` | mean = −13.510028 | std = 2.197310 |
| `s1_vh_db` | mean = −19.648007 | std = 3.401270 |
| `dem_elevation_m` | mean = 18.5 | std = 1e-06 (constant feature) |
| `ndvi_masked` | min = 0.183650 | max = 0.769276 |

Behavioral notes:

- Test-period NDVI is **not clipped**; it can fall outside [0, 1] for other data. With the present draws, test `ndvi_minmax` lies in [0.3519, 0.8927] [AN].
- NaN positions of `ndvi_masked` carry through to `ndvi_minmax` (14 train + 2 test = 16) [AN].
- `dem_elevation_m_zscore` is identically 0 because the feature is constant (PR-06).

### 8.8 Step 6 — Integrity Audit (C23, C24)

| Check | Assertion | Observed |
|:------|:----------|:---------|
| 1 | nulls in 3 Z-score columns == 0 | PASSED |
| 2a | `abs(train_z.mean()) < 1e-4` | PASSED |
| 2b | `abs(train_z.std() − 1.0) < 1e-2` | PASSED |
| 3 | `len(train_df)+len(test_df) == len(scaled_df)` | PASSED (28 + 7) |

Failure behavior: `AssertionError` with message, halting cell execution; the "PASSED" lines after each assertion are not reached.

Coverage limits of this audit:

- `ndvi_minmax` (which contains NaN) is not checked.
- Check 2 recomputes a property that is true by construction of Z-scoring on the same rows; it does **not** prove that the scaler was fitted without test data (PR-07).

### 8.9 Step 7 — Export (C25, C26)

1. Create directory `/kaggle/working/data_processed`.
2. `scaled_df.to_csv(..., index=False)`.
3. Build and `json.dump` the manifest (NumPy `float64` values serialize because `np.float64` subclasses Python `float`).
4. Print completion banner.

No post-write existence/size/readback check is performed.

### 8.10 Design Parameters (Complete Constant Table)

| Parameter | Value | Cell | Used by |
|:----------|:------|:----:|:--------|
| Random seed | 42 | C04 | HLR-15 |
| Record count | 35 | C04 | HLR-01 |
| Date range | 2026-08-01 … 2026-09-07 | C04 | HLR-01 |
| DEM constant | 18.5 m | C04 | HLR-01 |
| VV range | U(−18, −8) dB | C04 | HLR-01 |
| VH range | U(−25, −14) dB | C04 | HLR-01 |
| Cloud range | U(0, 90) % | C04 | HLR-01 |
| Red range | U(0.02, 0.18) | C04 | HLR-01 |
| NIR range | U(0.20, 0.52) | C04 | HLR-01 |
| Cloud threshold | 50.0 % (inclusive pass) | C06 | HLR-04 |
| Lee window | 3 samples | C10 | HLR-06 |
| Lee ε (noise variance) | 1e-6 | C10 | DR-03 |
| Split ratio | 0.8 | C14, C16 | HLR-07 |
| Scaling ε | 1e-6 | C18 | DR-04 |
| Mean tolerance | 1e-4 | C24 | HLR-10 |
| Std tolerance | 1e-2 | C24 | HLR-10 |
| Raw dir | `/kaggle/working/data_raw` | C04 | HLR-03 |
| Processed dir | `/kaggle/working/data_processed` | C26 | HLR-11 |

---

## 9. Software Verification

### 9.1 Verification Strategy

- **Requirements-based testing** by executing the notebook and comparing saved outputs against requirement statements (method T).
- **Inspection** of source text for requirements that cannot be tested by output alone (method I).
- **Analysis** for properties such as leakage (method A).
- **Demonstration** for figures (method D).
- Because the notebook contains **no test cell** other than three `assert` statements, additional offline analyses were performed [AN] and are clearly labeled.

### 9.2 Verification Cases and Results

| ID | Verification case | Method | Expected | Observed | Result | Tag |
|:---|:------------------|:------:|:---------|:---------|:------:|:---:|
| **VC-01** | Environment initializes without error | T | Banner printed, no error | Banner printed | **PASS** | NB |
| **VC-02** | Raw record count | T | 35 | "35 temporal records" | **PASS** | NB |
| **VC-03** | Determinism of first rows | T/A | Fixed values for seed 42 | Row 0: VV −14.254599, cloud 69.502029, NDVI 0.789083 (reproduced offline) | **PASS** | NB, AN |
| **VC-04** | QC pass/mask counts | T | pass + masked = 35 | 19 (54.3 %) + 16 (45.7 %) = 35 | **PASS** | NB |
| **VC-05** | Masked NDVI NaN count equals QC failures | A | 16 | 16 NaN in `ndvi_masked` | **PASS** | AN |
| **VC-06** | Lee filter reduces variance | T | filtered var < raw var | 9.0643 → 5.7011 (−37.1 %) | **PASS** | NB, AN |
| **VC-07** | Partition sizes and chronology | T | 28 / 7, train dates precede test dates | 28 / 7; 08-01→08-30 and 08-31→09-07 | **PASS** | NB |
| **VC-08** | Step-4 and Step-5 train stats consistent | A | same mean/std | −13.51 / 2.20 vs −13.510028 / 2.197310 | **PASS** | NB |
| **VC-09** | Train Z-mean ≈ 0, Z-std ≈ 1 | T | tolerances 1e-4 / 1e-2 | assertions passed | **PASS** | NB |
| **VC-10** | No nulls in Z-score columns | T | 0 | assertion passed | **PASS** | NB |
| **VC-11** | Partition row conservation | T | 35 | assertion passed (28+7) | **PASS** | NB |
| **VC-12** | Artifacts written | T | two files, paths printed | paths printed (no existence check) | **PASS (weak)** | NB |
| **VC-13** | Four figures rendered | D | 4 figures | 4 `image/png` outputs present | **PASS** | NB |
| **VC-14** | Statistic offline reproduction | A | printed values reproduce | variances, counts, scaler bounds reproduce exactly | **PASS** | AN |
| **VC-15** | **Leakage independence** of SAR stage: changing a *test* sample must not alter any *train* feature | A | no change | Raising raw VV at test index 28 by +5 dB changes train feature `s1_vv_lee[27]` by **+0.8188 dB**; also σn² uses all 35 samples | **FAIL** | AN |
| **VC-16** | Completeness of exported NaN-free features | A | 0 NaN in exported model features | `ndvi_minmax` has 16 NaN (not covered by audit) | **FAIL / informational** | AN |

### 9.3 Requirements-Based Coverage

All 15 HLR and 34 LLR have at least one verification case or inspection (Section 10.3). Two HLR (HLR-09 and, with limits, HLR-10) carry verification findings.

### 9.4 Structural Coverage

| Measure | Result |
|:--------|:-------|
| Code cells executed | 13 / 13 (execution counts 30–42) [NB] |
| Function coverage | 1 / 1 function (`apply_lee_filter_1d`) executed |
| Statement coverage | not instrumented; code is essentially straight-line and all code cells ran |
| Branch / MC/DC coverage | not measured. The only data-dependent selection is `np.where` (both outcomes exercised: 19 True / 16 False). Assertion failure paths (3) were **not** exercised |
| Dead code | unused: `sys`, `variance`, `feature_cols`, `s1_vv_normalized` (as a model input) |

### 9.5 Recommended Additional Verification (Not Yet Executed)

| ID | Proposed test | Targets |
|:---|:--------------|:--------|
| **VP-01** | Boundary test of `cloud == 50.0` and `50.0001` | LLR-11 |
| **VP-02** | Negative tests forcing each of the 3 assertions to fail | LLR-28..30 |
| **VP-03** | Leakage test: perturb test rows, assert train features and scaler params bit-identical | HLR-09 |
| **VP-04** | `ndvi_masked` all-NaN training set → graceful error | LLR-24 |
| **VP-05** | Constant-column test (`dem_elevation_m`) → documented behavior | DR-04 |
| **VP-06** | Lee filter reference test on a known synthetic signal (constant → unchanged; step edge → preserved) | LLR-15 |
| **VP-07** | File existence, row/column count and `read_csv` round-trip of both artifacts | HLR-11, HLR-12 |
| **VP-08** | Manifest schema validation and JSON-reload scaling reproduces `scaled_df` | HLR-12 |
| **VP-09** | Fresh-kernel "Restart & Run All" regression with pinned library versions | NFR-03, HLR-15 |
| **VP-10** | Assert 16 columns and exact column order in the export | IF-02 |

---

## 10. Traceability

### 10.1 HLR → LLR → Cell → Verification

| HLR | LLR | Cells | Verification |
|:----|:----|:------|:-------------|
| HLR-01 | LLR-05, 06, 07 | C04 | VC-02, VC-03 |
| HLR-02 | LLR-08 | C04 | VC-03 (NDVI value), VC-14 |
| HLR-03 | LLR-09 | C04 | VC-02 (path printed) |
| HLR-04 | LLR-11, 12 | C06 | VC-04, VC-05 |
| HLR-05 | LLR-13 | C06 | VC-04 |
| HLR-06 | LLR-15, 16 | C10 | VC-06, VC-14 |
| HLR-07 | LLR-18, 21 | C14, C16 | VC-07 |
| HLR-08 | LLR-19, 23, 24 | C14, C18 | VC-08, VC-09 |
| HLR-09 | LLR-15, 19, 23, 24 (and DR-03) | C10, C14, C18 | VC-15 (**FAIL**) |
| HLR-10 | LLR-28, 29, 30, 31 | C24 | VC-09, VC-10, VC-11, VC-16 |
| HLR-11 | LLR-32 | C26 | VC-12 |
| HLR-12 | LLR-33 | C26 | VC-12 |
| HLR-13 | LLR-02, 14, 17, 26, 27 | C02, C08, C12, C20, C22 | VC-13 |
| HLR-14 | LLR-03, 10, 13, 16, 20, 22, 25, 31, 34 | C02–C26 | VC-01 … VC-12 |
| HLR-15 | LLR-01, 04, 06 | C02, C04 | VC-03, VC-14 |

### 10.2 Derived Requirement → Cell → Problem Report

| DR | Cell | Problem Report |
|:---|:----:|:---------------|
| DR-01 | C10 | — (informational) |
| DR-02 | C10 | — |
| DR-03 | C10 | PR-03 |
| DR-04 | C18 | PR-06 |
| DR-05 | C18 | PR-05 |
| DR-06 | C14, C26 | PR-08 |
| DR-07 | C18 | PR-11 |
| DR-08 | C26 | — |
| DR-09 | C04, C08 | PR-10 |
| DR-10 | C14, C16 | PR-08 |

### 10.3 Reverse Trace: Cell → Requirements

| Cell | LLR | DR |
|:----:|:----|:---|
| C02 | LLR-01, 02, 03 | — |
| C04 | LLR-04 … 10 | DR-09 |
| C06 | LLR-11, 12, 13 | — |
| C08 | LLR-14 | DR-09 |
| C10 | LLR-15, 16 | DR-01, 02, 03 |
| C12 | LLR-17 | — |
| C14 | LLR-18, 19, 20 | DR-06, 10 |
| C16 | LLR-21, 22 | DR-10 |
| C18 | LLR-23, 24, 25 | DR-04, 05, 07 |
| C20 | LLR-26 | — |
| C22 | LLR-27 | — |
| C24 | LLR-28 … 31 | — |
| C26 | LLR-32, 33, 34 | DR-06, 08 |

*Markdown cells C00, C01, C03, C05, C07, C09, C11, C13, C15, C17, C19, C21, C23, C25, C27, C28 carry documentation only and trace to no executable requirement; their claims are audited in Section 12 and Appendix B.*

### 10.4 Trace Completeness Check

- Every HLR has ≥ 1 LLR: **yes**.
- Every LLR has a parent HLR: **yes**.
- Every code cell maps to ≥ 1 LLR: **yes** (13/13).
- Every DR is documented: **yes** (10).
- Every HLR has ≥ 1 verification case: **yes**.

---

## 11. Requirements Compliance Summary

| Status | Count | HLR IDs |
|:-------|:-----:|:--------|
| Met | 11 | HLR-02, 03, 05, 07, 08, 10, 11, 12, 13, 14, 15 |
| Met with deviation | 3 | HLR-01, 04, 06 |
| Partially met | 1 | HLR-09 |
| Not met | 0 | none |
| **Total** | **15** | |

*Notes:* "Met" for HLR-10 and HLR-13 carries documented limitations (PR-05, PR-07, PR-09, PR-10); HLR-08 and HLR-15 are Met for the scaler parameters and for seeded determinism respectively (PR-03, PR-15 apply to related aspects). The authoritative per-requirement status is Section 7.1.

**Overall conclusion:** the notebook executes as designed and meets its functional intent on synthetic data. It **does not** satisfy its own strongest claim ("Zero Future Leakage", HLR-09) because the Lee filtering stage precedes and ignores the temporal split.

---

## 12. Problem Reports and Open Issues

Severity: **High** = invalidates a stated scientific/safety claim; **Medium** = affects data quality or maintainability; **Low** = cosmetic / hygiene.

| ID | Sev. | Cell | Finding | Evidence | Recommended corrective action |
|:---|:----:|:----:|:--------|:---------|:------------------------------|
| **PR-01** | High | C03, C04 | Narrative says raw data is loaded from Notebook 01 (`stac_telemetry_raw.csv`), but the code generates **synthetic uniform random** data (seed 42). Results are not real satellite observations. | C04 comment "Bypasses File Path Issues"; `np.random.uniform` calls | Label data as synthetic in the title; add a switch `USE_REAL_DATA` that reads the Notebook 01 CSV; keep the generator as a test fixture |
| **PR-02** | Medium | C01, C05, C06, C27 | "SCL Bitmasking" is claimed, but no SCL band is read; filtering is a scalar `cloud_pct <= 50` rule. | Code C06 | Rename to "cloud-percentage threshold QC", or implement SCL class masking (e.g. classes 3, 8, 9, 10) |
| **PR-03** | **High** | C10, C14 | The Lee filter runs on the **entire** series before the split. (a) The centered 3-sample window mixes test sample 28 into train feature 27. (b) σn² = mean local variance of all 35 samples. The "Zero Future Leakage" statements (C08 figure text, C14 printout, C27) are therefore not strictly true. | VC-15: +5 dB perturbation at index 28 changes `s1_vv_lee[27]` by 0.8188 dB | Split first; filter each partition separately (or use a causal / trailing window); estimate σn² from the training partition only; compute the leakage status from a test (VP-03), not a literal string |
| **PR-04** | Low | C16 | Printed bounds `t <= 28` / `t > 28` are off by one relative to slicing (`[:28]`, `[28:]`). | Output C16 | Print `t < 28` and `t >= 28` |
| **PR-05** | Medium | C18, C22, C24 | NaNs are neither dropped nor interpolated, yet Plot 4 states "Optical QC Interpolation: Cloud NaNs Handled". `ndvi_minmax` has 16 NaN (14 train, 2 test) and is outside the Step-6 audit. | AN | Either interpolate using training-only information or document NaN as intentional; extend audit to `ndvi_minmax`; correct the annotation |
| **PR-06** | Low | C18 | `dem_elevation_m` is constant (18.5). Std = 0 → stored as 1e-06; Z-score ≡ 0. Meaningless feature, and the stored `std` is the epsilon, not a real deviation. | Manifest values | Exclude constant features from scaling or flag them in manifest |
| **PR-07** | Medium | C14, C24 | The "audit" is partly tautological. Train Z-mean = 0 and Z-std ≈ 1 hold by construction and cannot detect test-data leakage. The "PASSED (Zero Future Leakage)" line is a hard-coded `print`. | Source | Replace by a perturbation-based leakage test (VP-03); compare scaler parameters with those recomputed from `train_df` only |
| **PR-08** | Low | C02, C14, C16 | Hygiene: unused imports (`sys`, `variance`), unused `feature_cols`, duplicate `json` import, split index computed twice (`split_idx`, `split_index`), redundant `s1_vv_normalized` vs `s1_vv_lee_zscore` exported. | Source | Remove or use; single source of truth for split index; drop redundant column |
| **PR-09** | Medium | C01, C15, C21, C22, C27 | Claims with no corresponding code/evidence: "Precipitation forcing" (Plot 4 text), "SAR-Optical channels aligned to common spatial grid", Bhadrak/Balasore grid coordinates (21.1378° N, 86.6874° E), "preserving hydrological ground boundaries", "100 % verified, scientifically audited", Step 4 text citing (μ, σ) while top math cites Min-Max. | Source search | Delete or substantiate each claim (Appendix B) |
| **PR-10** | Low | C08, C12, C20, C22 | Label/typo defects: `'TIMESTAMPS (UTC'` (missing `)`), legend `'… (Granular Speckle'`, `'TIMESTAMMP (UTC)'`, `'Scaled NDVI (Min-Max [0, 1'`, `'TRain Scaled'`; axes labeled "UTC" but timestamps are tz-naive; Plot 3 left panel titled "RAW SAR VV" but plots Lee-filtered `s1_vv_lee`. | Source | Fix strings; use `tz='UTC'` in `date_range`; retitle panel "LEE-FILTERED VV" |
| **PR-11** | Medium | C10, C18 | Lee filter simplifications: 1-D temporal, dB domain (Lee theory assumes linear intensity/multiplicative noise), global σn² without ENL, VH not filtered, default reflect boundary. Title text says "adaptive Lee filter preserving structural hydrological boundaries". | Source | Convert dB→linear, filter, convert back; derive σn² from ENL; apply to VH or justify; or rename to "temporal adaptive smoothing" |
| **PR-12** | Low | C04, C26 | Hard-coded Kaggle paths; manifest field `notebook` = `02_preprocessing.ipynb` while the file is `02-preprocessing.ipynb`. | Source | Use a `BASE_DIR` config; derive/standardize notebook name |
| **PR-13** | Low | C26 | No readback / existence verification of exported files. | Source | Add VP-07 checks |
| **PR-14** | Low | C04 | Timestamps are evenly spaced at ≈ 26 h 07 min, not actual Sentinel acquisition times (S1/S2 revisits are irregular and sensor-specific). | AN | Use actual acquisition datetimes per sensor and an explicit temporal alignment step |
| **PR-15** | Low | all | No pinned library versions, no commit/tag, no `requirements` listing. | Metadata | Record `pip freeze` / environment lock in the notebook header |

---

## 13. Figure Specifications

All figures: Matplotlib, dark theme, Aerospace palette, rendered inline.

### 13.1 Figure 1 — Optical QC (C08) — LLR-14

| Property | Value |
|:---------|:------|
| Size | 14 × 5 in |
| Series | Raw NDVI (`#556677`, dotted, `x` markers, α 0.7); QC-passed NDVI (`#00FF66`, circles, lw 2.0) |
| Overlay | Dashed vertical lines (`#FF3355`, α 0.3) at each masked timestamp (16) |
| Title | `AETHER PREPROCESSING // SENTINEL-2 CLOUD QC & OPTICAL MASKING` |
| Diagnostics box (axes coords 0.02, 0.15) | threshold text; "Retained Clean Frames: 19/35 (54.3%)"; the sentence "Zero Cloud Noise Leakage Guaranteed into Downstream Array" |
| Defects | Label typos (PR-10) |

### 13.2 Figure 2 — SAR Despeckling (C12) — LLR-17

| Property | Value |
|:---------|:------|
| Size | 14 × 5 in |
| Series | Raw VV (`#FF3355`, dashed, squares, α 0.6); Lee VV (`#00FFCC`, circles, lw 2.0) |
| Diagnostics | raw variance 9.064 dB²; filtered 5.701 dB²; "Speckle Noise Suppression: 37.1 % Variance Smoothness" (computed) |
| Defects | Typos (PR-10); the quantity "variance reduction" is called "speckle suppression" although part of the reduction is genuine signal smoothing |

### 13.3 Figure 3 — Raw vs Scaled Distributions (C20) — LLR-26

| Property | Value |
|:---------|:------|
| Size | 15 × 5 in, two panels |
| Left | Histograms of `s1_vv_lee` for train (12 bins, `#FF3355`) and test (8 bins, `#FFCC00`); titled "RAW SAR VV" (mislabel, PR-10) |
| Right | Histograms of train/test Z-score; diagnostics box at (0.03, 0.65): Train Z-Mean (~0.0), Train Z-Std (~1.0), "Zero Future Leakage Confirmed" (unsupported, PR-03/07) |
| Suptitle | `AETHER PREPROCESSING // ZERO-LEAKAGE FEATURE SCALING COMPARISON` (y = 1.02) |

### 13.4 Figure 4 — Scaled Multi-Sensor Series (C22) — LLR-27

| Property | Value |
|:---------|:------|
| Size | 14 × 5 in |
| Series | Z-score VV (`#00FFCC`, circles); NDVI Min-Max (`#00FF66`, triangles); NaN gaps appear as breaks |
| Boundary | Red dashed vertical line at 2026-08-31 (first test timestamp) |
| Diagnostics | split date; "Cloud NaNs Handled" (inaccurate, PR-05); "Aligned to Common Spatial Grid" (unsupported, PR-09) |

---

## 14. Execution and Reproduction Procedure

1. Open `02-preprocessing.ipynb` in a Kaggle (or compatible) Python 3.12 environment, NumPy ≥ 2, pandas, SciPy, Matplotlib installed.
2. Ensure `/kaggle/working` is writable (or change the paths; PR-12).
3. Restart the kernel and **Run All**; cells must run in order C02 → C26.
4. Verify console output against Section 9.2 (expected numbers: 35 records; 19/16 QC; variances 9.0643 → 5.7011; split 28/7; mean −13.51, std 2.20).
5. Confirm both artifacts exist under `/kaggle/working/data_processed/` and that the CSV has 16 columns × 35 rows (IF-02).
6. Archive: notebook file, both artifacts, environment lock (PR-15).

---

## 15. Open Actions for Owner (Prioritized)

| Priority | Action | Closes |
|:--------:|:-------|:-------|
| 1 | Move Lee filtering after the split, or make it causal and train-only; add a perturbation leakage test | PR-03, PR-07, HLR-09 |
| 2 | State clearly that data is synthetic or connect real Notebook 01 output | PR-01, PR-14 |
| 3 | Align notebook claims with the implementation (SCL, spatial grid, interpolation, coordinates, precipitation, "100 % verified") | PR-02, PR-05, PR-09 |
| 4 | Extend integrity audit to all exported model features including `ndvi_minmax` | PR-05, HLR-10 |
| 5 | Pin environment and parametrize paths | PR-12, PR-15 |
| 6 | Clean-up pass for typos, unused code, redundant columns | PR-04, PR-06, PR-08, PR-10, PR-13 |

---

## Appendix A — Mapping to DO-178C Life-Cycle Data Items

| DO-178C data item (Section 11) | Where addressed in this document | Remark |
|:-------------------------------|:---------------------------------|:-------|
| PSAC / SDP / SVP / SCMP / SQAP | Sections 0.2, 5.4, 6, 9.1 (condensed) | Planning data not produced as separate documents |
| Software Requirements Data (11.9) | Section 7 | HLR, LLR, DR, NFR, interfaces |
| Design Description (11.10) | Section 8 | Architecture, algorithms, parameters |
| Source Code (11.11) | Notebook cells C02–C26 | Reference [R2] |
| Executable Object Code (11.12) | not applicable | interpreted |
| Verification Cases and Procedures (11.13) | Sections 9.1, 9.2, 9.5, 14 | |
| Verification Results (11.14) | Section 9.2, 9.4 | |
| Life Cycle Environment Config. Index (11.15) | Sections 4.2, 6 | versions incomplete |
| Software Configuration Index (11.16) | Section 4 | no version control |
| Problem Reports (11.17) | Section 12 | 15 reports |
| Trace Data (11.21) | Section 10 | bidirectional |
| Software Accomplishment Summary (11.20) | Section 11 | informal |

---

## Appendix B — Notebook Claims vs. Verified Evidence (C27 Executive Summary)

| Claim in notebook | Verdict | Evidence / comment |
|:------------------|:-------:|:-------------------|
| "Sentinel-2 SCL Cloud Quality Control filtering out observations with > 50 % cloud mask" | Partially true | Threshold on cloud %, not SCL (PR-02) |
| "Isolated corrupted optical spectral index frames" | True | 16 NDVI values masked |
| "Applied adaptive 1D Lee Filtering on backscatter σ⁰VV" | True | C10 |
| "preserving hydrological ground boundaries" | Unsupported | No spatial data or boundary metric |
| "Enforced strict 80/20 temporal split" | True | 28 / 7, chronological |
| "Fitted Z-Score and Min-Max scalers exclusively on training frames" | True | C18 |
| "preventing future data contamination into downstream models" | **Not fully true** | Lee stage leaks across split (PR-03) |
| "Embedded real-time mathematical diagnostic annotations" | True | 4 figures |
| "Persisted preprocessed_telemetry.csv and scaler_manifest.json" | True | C26 (printed; not read back) |
| "Target domain: Bhadrak/Balasore Spatial Grid (21.1378° N, 86.6874° E)" | Unsupported | No coordinates or spatial grid in code |
| "100 % verified, scientifically audited" | Overstated | Three assertions; two High/Medium findings (Section 12) |
| "SAR-Optical channels aligned to common spatial grid" | Unsupported | Single-point time series |
| "Zero Cloud Noise Leakage Guaranteed" | Conditionally true | NDVI is masked; but the cloud-percentage column itself remains in the export |

---

## Appendix C — Intellectual Property and Copyright Notice (carried from C28)

**PROJECT — THE MRIDANSH · CENTRAL ENGINE — AETHER-MRID1607X**
*Multi-Domain Soil Intelligence & Geotechnical Stability Engine*

| | |
|:--|:--|
| **Copyright** | © 2026 Gourgopal Mohapatra. All Rights Reserved. |
| **Developed & Maintained by** | Gourgopal Mohapatra |
| **Lead Organization** | JCC HEADQUARTER |
| **Facility** | JCC CAMPUS 2 — RS-SDA Division (Remote Sensing & Spatial Data Analytics) |

This codebase, together with its neural architecture specifications (PINN / GCN), numerical formulations and associated telemetry pipelines, constitutes proprietary intellectual property. Unauthorized copying, redistribution, reverse engineering or commercial execution of this software package, in whole or in part, via any medium, is strictly prohibited without prior written authorization from the lead researcher and JCC RS-SDA.

*This documentation inherits the same classification and notice.*

---

*End of Document AETHER-MRID1607X-NB02-DOC-001, Version 1.0*
