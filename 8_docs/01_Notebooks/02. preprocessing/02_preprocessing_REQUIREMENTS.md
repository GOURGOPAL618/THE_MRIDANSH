# 🛰️ THE MRIDANSH: SATELLITE PREPROCESSING & TELEMETRY STANDARDIZATION
## Engineering Requirements, Verification Procedures & Scientific Traceability Specification
### Module ID: `MRIDANSH-MOD-PREPROC-02` | Notebook: `02-preprocessing.ipynb`

---

## 1. System Context & Operational Architecture

The `02-preprocessing` module forms the mission-critical secondary stage of **THE MRIDANSH** hydrological intelligence pipeline. Operating directly downstream of `01-data-ingestion`, this engine ingests raw multi-sensor telemetry vectors, isolates optical corruption caused by tropical monsoon cloud systems, suppresses radar speckle noise using adaptive filtering, and establishes zero-leakage normalization boundaries before handoff to spatial and temporal neural graph backbones (`03-spatial-modeling` and `04-temporal-modeling`).

```
+----------------------------------------------------------------------------------------------------+
|                                  UPSTREAM TELEMETRY INGESTION                                      |
|  Source: 5_storage/notebook_results/notebook_01_ingestion/stac_telemetry_raw.csv (35 epochs)      |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 1. Optical Quality Control (QC): Cloud Thresholding (s2_cloud_cover_pct <= 50.0%)                  |
|    - Corrupted optical NDVI frames flagged & masked to IEEE NaN                                    |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 2. SAR Speckle Noise Suppression: 1D Adaptive Lee Filter (Window N=3)                              |
|    - s1_vv_db -> s1_vv_lee; Var Reduction > 0.0%                                                   |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 3. Temporal Partitioning: Strict 80/20 Chronological Split (Split Index = 28)                      |
|    - Training Slice: t in [0, 27] (28 frames) | Test Holdout: t in [28, 34] (7 frames)             |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 4. Zero-Leakage Normalization: Fits scalers exclusively on Training Slice                          |
|    - Z-Score: s1_vv_lee, s1_vh_db, dem_elevation_m                                                 |
|    - Min-Max: ndvi_masked (valid clean training observations)                                      |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 5. Dual Storage Export:                                                                            |
|    - 5_storage/notebook_results/notebook_02_preprocessing/preprocessed_telemetry.csv               |
|    - 5_storage/notebook_results/notebook_02_preprocessing/scaler_manifest.json                     |
|    - Dual mirrors in data/processed/                                                               |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Functional Requirements (FR)

### FR-PREPROC-001: Ingestion & Telemetry Invariant Verification
The system **SHALL** locate and ingest the primary raw STAC telemetry artifact `stac_telemetry_raw.csv` from `5_storage/notebook_results/notebook_01_ingestion/` (with automatic fallback to `data/raw/stac_telemetry_raw.csv`).
- **Input Dimensions**: Exactly 35 temporal epochs spanning `2026-08-01 00:00:00` to `2026-09-07 00:00:00`.
- **Mandatory Columns**: `timestamp`, `crs`, `s1_vv_db`, `s1_vh_db`, `s2_cloud_cover_pct`, `dem_elevation_m`, `weather_temp_c`, `weather_precip_mm`, `ndvi`, `ndwi`.
- **CRS Invariant**: All ingested records must have `crs == 'EPSG:4326'`.

### FR-PREPROC-002: Optical Cloud Quality Control & Corruption Masking
The system **SHALL** apply a binary cloud mask using the Sentinel-2 cloud cover percentage:
$$\text{optical\_qc\_pass} = (s2\_cloud\_cover\_pct \le 50.0)$$
- Frames with $s2\_cloud\_cover\_pct > 50.0$ **SHALL** have their `ndvi` masked to IEEE 754 `NaN`.
- Invariant: Exactly 19 frames pass optical QC (54.29%), and 16 frames are masked (45.71%).

### FR-PREPROC-003: Sentinel-1 Adaptive 1D Lee Speckle Filtering
The system **SHALL** apply an adaptive local statistics Lee filter to raw temporal backscatter $I = s1\_vv\_db$ over a moving temporal window of size $N=3$:
$$\bar{I}_t = \frac{1}{N} \sum_{k \in W_t} I_k, \quad \overline{I^2}_t = \frac{1}{N} \sum_{k \in W_t} I_k^2$$
$$\sigma_t^2 = \max\left(\overline{I^2}_t - \bar{I}_t^2, 0\right)$$
$$W_t = \frac{\sigma_t^2}{\sigma_t^2 + \sigma_{\text{noise}}^2}, \quad \text{where } \sigma_{\text{noise}}^2 = \langle \sigma_t^2 \rangle + 10^{-6}$$
$$\hat{I}_t = \bar{I}_t + W_t (I_t - \bar{I}_t)$$
- Filtered series `s1_vv_lee` **SHALL** achieve measurable variance reduction:
$$\text{Var}(\hat{I}) < \text{Var}(I)$$
- Invariant: Raw variance of $3.6848 \text{ dB}^2$ reduced to $2.2618 \text{ dB}^2$ ($38.62\%$ reduction).

### FR-PREPROC-004: Strict Chronological Temporal Train-Test Splitting
The system **SHALL** partition the telemetry chronologically at ratio $\rho = 0.80$:
$$\text{split\_index} = \lfloor 35 \times 0.80 \rfloor = 28$$
- Training slice: Indices $t \in [0, 27]$ (28 epochs, `2026-08-01` to `2026-08-31`).
- Test holdout: Indices $t \in [28, 34]$ (7 epochs, `2026-09-01` to `2026-09-07`).
- Random shuffling is strictly prohibited.

### FR-PREPROC-005: Zero-Leakage Feature Normalization
The system **SHALL** compute normalization scaling statistics exclusively on `train_df`:
- **Z-Score Standardization**:
  $$\mu = \frac{1}{N_{\text{train}}} \sum_{i \in \text{train}} x_i, \quad \sigma = \sqrt{\frac{1}{N_{\text{train}}-1} \sum_{i \in \text{train}} (x_i - \mu)^2} + 10^{-6}$$
  $$z = \frac{x - \mu}{\sigma}$$
  Applied to: `s1_vv_lee`, `s1_vh_db`, `dem_elevation_m`.
- **Min-Max Scaling**:
  $$x_{\text{min}} = \min_{i \in \text{train}, \text{clean}} x_i, \quad x_{\text{max}} = \max_{i \in \text{train}, \text{clean}} x_i$$
  $$x_{\text{norm}} = \frac{x - x_{\text{min}}}{x_{\text{max}} - x_{\text{min}} + 10^{-6}}$$
  Applied to: `ndvi_masked` (computed strictly over non-null valid optical frames in train slice).
- **Zero-Leakage Invariant**:
  $$\mathbb{E}[z_{\text{train}}] = 0.0 \pm 10^{-5}, \quad \text{Std}[z_{\text{train}}] = 1.0 \pm 10^{-3}$$
  Test frames must be transformed using the frozen training $(\mu, \sigma)$ without re-estimation.

### FR-PREPROC-006: Dual-Target Persistence & Manifest Integrity
The system **SHALL** serialize:
1. `preprocessed_telemetry.csv` containing all cleaned, masked, filtered, and scaled features.
2. `scaler_manifest.json` containing exact scaler bounds, split indices, split timestamps, and configuration parameters.
Both files **SHALL** be persisted concurrently to:
- `5_storage/notebook_results/notebook_02_preprocessing/`
- `data/processed/`

---

## 3. Data Integrity & Numerical Requirements (DI)

- **DI-PREPROC-001 (Zero Nulls in Processed Core)**: Standardized features (`s1_vv_lee_zscore`, `s1_vh_db_zscore`, `dem_elevation_m_zscore`) must contain 0 NaN/null values.
- **DI-PREPROC-002 (Mask Preservation)**: The number of NaNs in `ndvi_minmax` must exactly equal the number of corrupted optical frames ($N_{\text{corrupt}} = 16$).
- **DI-PREPROC-003 (Provenence Metadata)**: Every row must retain `provenance == "SYNTHETIC_SIMULATION"`.
- **DI-PREPROC-004 (Weight Bounding)**: Adaptive Lee weights $W_t \in [0.0, 1.0]$ for all epochs.

---

## 4. Verification Procedures (VP) & Acceptance Test Suite

The verification suite `tests/test_notebook_02_verification.py` executes 6 strict automated tests:

| Test ID | Procedure Description | Acceptance Criteria | Verified Result |
| :--- | :--- | :--- | :--- |
| **VP-PREPROC-01** | `test_01_no_python_scripts_in_notebook_dir` | Directory `1_notebooks_sandbox/` contains 0 `.py` scripts | **PASSED** |
| **VP-PREPROC-02** | `test_02_notebook_cell_structure_and_markdown_rules` | Notebook length > 20 cells; every code cell preceded by markdown | **PASSED** (28 cells) |
| **VP-PREPROC-03** | `test_03_all_code_cells_executed_with_zero_errors` | Exactly 12 code cells; all executed; zero error outputs | **PASSED** (12/12 executed) |
| **VP-PREPROC-04** | `test_04_penultimate_and_ultimate_markdown_cells` | Penultimate contains Executive Summary; Ultimate contains IP notice | **PASSED** |
| **VP-PREPROC-05** | `test_05_storage_artifacts_and_plots_persisted` | 4 plots (>50KB) and 2 data artifacts exist in dual storage | **PASSED** |
| **VP-PREPROC-06** | `test_06_data_cleaning_masks_and_zero_leakage_invariants` | Zero-leakage verification ($\mu \approx 0, \sigma \approx 1$ on train slice); mask preservation | **PASSED** |

---

## 5. Aerospace Artifact Inventory

The following files are permanently stored in `5_storage/notebook_results/notebook_02_preprocessing/`:

| Artifact Name | Type | Size | Description |
| :--- | :--- | :--- | :--- |
| `plot_01_cloud_qc_masking.png` | PNG (300 DPI) | ~290 KB | Temporal cloud cover trajectory with 50% threshold line and raw vs masked NDVI flags. |
| `plot_02_sar_speckle_lee_filter.png` | PNG (300 DPI) | ~384 KB | Raw Sentinel-1 $\sigma^0_{VV}$ backscatter vs 1D Lee-filtered signal showing 38.62% variance suppression. |
| `plot_03_feature_scaling_distributions.png` | PNG (300 DPI) | ~162 KB | Dual-panel distribution histograms of raw vs standardized features. |
| `plot_04_preprocessed_telemetry_series.png` | PNG (300 DPI) | ~298 KB | Comprehensive multi-channel preprocessed telemetry time series with temporal split boundary marker. |
| `preprocessed_telemetry.csv` | CSV | 12.3 KB | 35 rows $\times$ 18 columns cleaned and normalized telemetry dataset. |
| `scaler_manifest.json` | JSON | 880 Bytes | Serialized training scaler boundaries ($\mu, \sigma, \min, \max$), split date, and metadata. |

---

## 6. Traceability Matrix

| Requirement | Notebook 02 Code Cell | Verification Test | Storage Artifact |
| :--- | :--- | :--- | :--- |
| **FR-PREPROC-001** | Cell 5 | `test_03_all_code_cells_executed_with_zero_errors` | `stac_telemetry_raw.csv` (input) |
| **FR-PREPROC-002** | Cell 7, 9 | `test_06_data_cleaning_masks_and_zero_leakage_invariants` | `plot_01_cloud_qc_masking.png` |
| **FR-PREPROC-003** | Cell 11, 13 | `test_06_data_cleaning_masks_and_zero_leakage_invariants` | `plot_02_sar_speckle_lee_filter.png` |
| **FR-PREPROC-004** | Cell 15 | `test_06_data_cleaning_masks_and_zero_leakage_invariants` | `scaler_manifest.json` |
| **FR-PREPROC-005** | Cell 17, 19 | `test_06_data_cleaning_masks_and_zero_leakage_invariants` | `plot_03_feature_scaling_distributions.png` |
| **FR-PREPROC-006** | Cell 21, 25 | `test_05_storage_artifacts_and_plots_persisted` | `preprocessed_telemetry.csv`, `scaler_manifest.json` |
| **DI-PREPROC-001..004** | Cell 23 | `test_06_data_cleaning_masks_and_zero_leakage_invariants` | `plot_04_preprocessed_telemetry_series.png` |

---

## 7. Brutally Unfiltered Defect Log & Engineering Limitations

| Defect ID | Severity | Subsystem | Description & Root Cause | Impact & Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| `D-NB02-001` | **HIGH** | Lee Filter | **Heuristic 1D Temporal Noise Variance Fallback**: Standard Lee speckle filtering operates on 2D spatial radar grids where noise variance is physically bounded by the equivalent number of looks ($\sigma_v^2 \approx 1/L$). Notebook 02 estimates $\sigma_{\text{noise}}^2 = \langle \sigma_t^2 \rangle + 10^{-6}$ over a 1D temporal series. | Treats high-frequency hydrological surge events (e.g. flash-flood wetting) as speckle noise and partially dampens legitimate physical transitions. Mitigation: In production, apply 2D spatial Lee filtering prior to catchment aggregation. |
| `D-NB02-002` | **MEDIUM** | Scaler Engine | **Unclipped Min-Max Test Extrapolation**: Min-Max scaling for NDVI computes bounds strictly on the training partition ($[x_{\text{min}}, x_{\text{max}}]$). If future test frames experience extreme greening or browning beyond these limits, $x_{\text{norm}}$ escapes $[0, 1]$ into negative or $>1.0$ domains because `np.clip` was omitted. | Downstream sigmoid activation layers or physics loss penalties in Notebook 05 could experience mild gradient instability on extreme out-of-bounds inputs. Mitigation: Add `np.clip(x_norm, 0.0, 1.0)`. |
| `D-NB02-003` | **MEDIUM** | Optical QC | **All-or-Nothing Scene Cloud Threshold**: A hard threshold of $s2\_cloud\_cover\_pct \le 50.0\%$ drops entire frames if scene cloud cover is 50.1%, while accepting frames with 49.9% cloud cover without pixel-level Scene Classification Layer (SCL) validation. | May retain cloud-contaminated pixels or discard clear catchment sub-regions. Mitigation: Ingest Sentinel-2 SCL raster masks for per-pixel valid-data masking. |
| `D-NB02-004` | **LOW** | Lee Filter | **Uniform Kernel on Non-Uniform Temporal Spacing**: Sentinel-1 overpasses occur on 2-to-5 day irregular cadences. The 1D uniform moving average assumes uniformly spaced time points $\Delta t_k = \text{const}$. | Temporal smoothing weights adjacent days identically regardless of whether the time delta was 1 day or 5 days. Mitigation: Weight moving average by inverse time interval $\Delta t^{-1}$. |

---

## 8. Configuration Control & Environment Lineage

- **Parent Repository**: `THE_MRIDANSH`
- **Execution Python**: Python 3.12.10 (virtual environment `mridansh_env`, PyTorch 2.14.0+cpu, SciPy 1.15.2, Pandas 2.2.3)
- **Primary Input**: `5_storage/notebook_results/notebook_01_ingestion/stac_telemetry_raw.csv`
- **Storage Target**: `5_storage/notebook_results/notebook_02_preprocessing/`
- **Secondary Target**: `data/processed/`
- **Verification Command**: `pytest tests/test_notebook_02_verification.py -v`
