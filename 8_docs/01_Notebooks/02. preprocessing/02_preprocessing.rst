.. _module_02_preprocessing:

========================================================================
🛰️ Module 02: Satellite Data Preprocessing & Signal Standardization
========================================================================

:Author: JCC Headquarter (RS-SDA Division) / Gourgopal Mohapatra
:Engine: AETHER-MRID1607X
:Module ID: MRIDANSH-MOD-PREPROC-02
:Notebook Source: ``1_notebooks_sandbox/02-preprocessing.ipynb``
:Verification Suite: ``tests/test_notebook_02_verification.py``
:Last Verification: Verified (6/6 Test Cases Passed)

.. contents:: Table of Contents
   :depth: 3
   :local:

Overview & Scientific Purpose
=============================

Module 02 provides rigorous, zero-leakage preprocessing, speckle noise reduction, and signal conditioning for multi-sensor satellite telemetry collected over the Bhadrak catchment region. It serves as the primary bridge between raw heterogeneous geospatial raster ingestions (Sentinel-1 SAR, Sentinel-2 Optical, Copernicus DEM, and ECMWF Weather) and downstream neural representation architectures (Graph Convolutional Networks and Spatial-Temporal ConvLSTMs).

The module enforces strict operational discipline:
1. **Cloud Quality Control**: Optical Sentinel-2 measurements are filtered against a 50% cloud fraction threshold to prevent atmospheric haze and cloud shadow contamination.
2. **Adaptive Lee Speckle Filtering**: Multiplicative SAR speckle noise in Sentinel-1 :math:`\sigma^0_{VV}` backscatter is mitigated using a 1D adaptive variance filter.
3. **Zero-Leakage Temporal Splitting**: The dataset is strictly partitioned into an 80% training window (:math:`t \in [0, 27]`) and a 20% test holdout (:math:`t \in [28, 34]`).
4. **Isolated Feature Normalization**: Normalization parameters (mean, standard deviation, min, max) are estimated exclusively on the training partition and frozen before transformation.
5. **Dual-Tier Artifact Serialization**: Processed datasets and parameter manifests are mirrored simultaneously into dedicated execution storage and repository data lakes.

Input Telemetry Invariants
==========================

The module consumes the primary output of ``01-data-ingestion``:

* **Primary Path**: ``5_storage/notebook_results/notebook_01_ingestion/stac_telemetry_raw.csv``
* **Fallback Path**: ``data/raw/stac_telemetry_raw.csv``
* **Dimension**: Exactly 35 observations (:math:`N=35`) spanning August 1, 2026 to September 7, 2026.
* **Coordinate Reference System**: EPSG:4326 (WGS 84).

Mandatory feature columns validated at ingestion:

.. list-table:: Ingested Telemetry Features
   :widths: 25 15 20 40
   :header-rows: 1

   * - Field Name
     - Sensor Origin
     - Physical Units
     - Description
   * - ``timestamp``
     - Telemetry System
     - ISO 8601 UTC
     - Temporal observation epoch
   * - ``s1_vv_db``
     - Sentinel-1 SAR
     - Decibels (:math:`\text{dB}`)
     - Co-polarized vertical backscatter intensity
   * - ``s1_vh_db``
     - Sentinel-1 SAR
     - Decibels (:math:`\text{dB}`)
     - Cross-polarized vertical-horizontal intensity
   * - ``s2_cloud_cover_pct``
     - Sentinel-2 Optical
     - Percentage (:math:`\%`)
     - Catchment mean cloud cover fraction
   * - ``dem_elevation_m``
     - Copernicus DEM
     - Metres (:math:`\text{m}`)
     - Catchment topographic mean elevation
   * - ``weather_temp_c``
     - ECMWF ERA5
     - Celsius (:math:`^\circ\text{C}`)
     - 2m surface ambient temperature
   * - ``weather_precip_mm``
     - ECMWF ERA5
     - Millimetres (:math:`\text{mm}`)
     - Daily accumulated precipitation depth
   * - ``ndvi``
     - Sentinel-2 MSI
     - Dimensionless
     - Normalized Difference Vegetation Index
   * - ``ndwi``
     - Sentinel-2 MSI
     - Dimensionless
     - Normalized Difference Water Index

Mathematical Formulations
=========================

Optical Quality Control & Corruption Masking
--------------------------------------------

Sentinel-2 optical observations are severely degraded by convective monsoon cloud systems. The quality control flag :math:`M_{\text{QC}}(t) \in \{0, 1\}` is evaluated as:

.. math::

   M_{\text{QC}}(t) = 
   \begin{cases}
   1 & \text{if } C(t) \le C_{\text{thresh}} \\
   0 & \text{if } C(t) > C_{\text{thresh}}
   \end{cases}

where :math:`C(t)` is ``s2_cloud_cover_pct`` and :math:`C_{\text{thresh}} = 50.0\%`. Corrupted vegetation indices are masked to IEEE 754 ``NaN``:

.. math::

   \text{NDVI}_{\text{masked}}(t) = 
   \begin{cases}
   \text{NDVI}(t) & \text{if } M_{\text{QC}}(t) = 1 \\
   \text{NaN} & \text{if } M_{\text{QC}}(t) = 0
   \end{cases}

In the operational test run, 19 frames (54.29%) passed QC, while 16 frames (45.71%) were corrupted and masked.

Adaptive 1D Lee Speckle Filtering
---------------------------------

Synthetic Aperture Radar (SAR) signals suffer from multiplicative speckle noise arising from coherent interference of backscattered electromagnetic waves. The 1D adaptive Lee filter operates on the backscatter series :math:`I(t) = s1\_vv\_db(t)` over a moving temporal window of size :math:`N=3`:

1. **Local Moving Mean**:

   .. math::

      \bar{I}(t) = \frac{1}{N} \sum_{k \in W(t)} I(k)

2. **Local Moving Mean of Squares**:

   .. math::

      \overline{I^2}(t) = \frac{1}{N} \sum_{k \in W(t)} I^2(k)

3. **Local Signal Variance**:

   .. math::

      \sigma_I^2(t) = \max\left(\overline{I^2}(t) - \bar{I}^2(t), \, 0\right)

4. **Global Noise Variance Floor**:

   .. math::

      \sigma_{\text{noise}}^2 = \frac{1}{T} \sum_{t=1}^T \sigma_I^2(t) + 10^{-6}

5. **Adaptive Weighting Coefficient**:

   .. math::

      W(t) = \frac{\sigma_I^2(t)}{\sigma_I^2(t) + \sigma_{\text{noise}}^2}, \quad W(t) \in [0, 1]

6. **Filter Output Estimation**:

   .. math::

      \hat{I}(t) = \bar{I}(t) + W(t) \cdot \left[ I(t) - \bar{I}(t) \right]

When local variance :math:`\sigma_I^2(t)` is high (e.g. sharp hydrological edge or flood wetting event), :math:`W(t) \to 1` and the raw measurement is preserved. In homogeneous regions where variance is low, :math:`W(t) \to 0` and the output reverts to the local mean :math:`\bar{I}(t)`.

Empirical filtering results:
- Raw backscatter variance: :math:`3.6848 \text{ dB}^2`
- Lee-filtered variance: :math:`2.2618 \text{ dB}^2`
- Speckle noise variance reduction: :math:`38.62\%`

Zero-Leakage Chronological Partitioning & Normalization
-------------------------------------------------------

To eliminate data leakage, the time series is split strictly chronologically:

.. math::

   K_{\text{split}} = \lfloor N \times 0.80 \rfloor = 28

The training set comprises :math:`t \in [0, 27]` (August 1 to August 31, 2026), and the test set comprises :math:`t \in [28, 34]` (September 1 to September 7, 2026).

**Z-Score Standardization**:
Parameters :math:`\mu` and :math:`\sigma` are fitted strictly on the training partition:

.. math::

   \mu_{\text{train}} = \frac{1}{28} \sum_{t=0}^{27} x(t), \quad \sigma_{\text{train}} = \sqrt{\frac{1}{27} \sum_{t=0}^{27} (x(t) - \mu_{\text{train}})^2} + 10^{-6}

.. math::

   z(t) = \frac{x(t) - \mu_{\text{train}}}{\sigma_{\text{train}}}

Verified properties:
- :math:`\mathbb{E}[z_{\text{train}}] = 0.0 \pm 10^{-5}`
- :math:`\text{Std}[z_{\text{train}}] = 1.0 \pm 10^{-4}`

**Min-Max Scaling**:
Applied to valid, cloud-free NDVI observations on the training slice:

.. math::

   x_{\text{min}} = \min_{t \in \text{train}, M_{\text{QC}}=1} \text{NDVI}(t), \quad x_{\text{max}} = \max_{t \in \text{train}, M_{\text{QC}}=1} \text{NDVI}(t)

.. math::

   \text{NDVI}_{\text{minmax}}(t) = \frac{\text{NDVI}_{\text{masked}}(t) - x_{\text{min}}}{x_{\text{max}} - x_{\text{min}} + 10^{-6}}

Cloud-masked indices retain ``NaN`` across all scaling operations.

Generated Artifacts & Visualizations
====================================

The module automatically generates and persists high-resolution (300 DPI) aerospace plots in ``5_storage/notebook_results/notebook_02_preprocessing/``:

1. **Optical QC Masking (plot_01_cloud_qc_masking.png)**
   Illustrates temporal cloud cover fluctuations relative to the 50% operational threshold, showing raw vs masked NDVI samples.
2. **SAR Lee Speckle Filtering (plot_02_sar_speckle_lee_filter.png)**
   Compares raw Sentinel-1 :math:`\sigma^0_{VV}` backscatter with the adaptive Lee-filtered signal, detailing local variance suppression.
3. **Feature Scaling Distributions (plot_03_feature_scaling_distributions.png)**
   Displays kernel density distributions of raw features alongside standardized zero-mean, unit-variance distributions.
4. **Preprocessed Telemetry Series (plot_04_preprocessed_telemetry_series.png)**
   Displays the synchronized multi-sensor standardized telemetry stream across the entire 35-epoch observation window, demarcating the train-test boundary.

Stored Data Files:
- ``preprocessed_telemetry.csv``: Cleaned and normalized feature dataset (35 rows :math:`\times` 18 columns).
- ``scaler_manifest.json``: Machine-readable JSON manifest recording all frozen scaling parameters (:math:`\mu, \sigma, \min, \max`), split index, and provenance.

Verification & Test Coverage
============================

The verification suite ``tests/test_notebook_02_verification.py`` enforces 6 rigorous automated tests:

* ``test_01_no_python_scripts_in_notebook_dir``: Confirms absence of forbidden scripts in sandbox.
* ``test_02_notebook_cell_structure_and_markdown_rules``: Validates that all 12 code cells are preceded by explanatory markdown documentation.
* ``test_03_all_code_cells_executed_with_zero_errors``: Verifies execution counts and zero runtime exceptions.
* ``test_04_penultimate_and_ultimate_markdown_cells``: Audits presence of Executive Summary and Intellectual Property notices.
* ``test_05_storage_artifacts_and_plots_persisted``: Validates physical persistence and file sizes (>50KB) of all 4 plots and dual data targets.
* ``test_06_data_cleaning_masks_and_zero_leakage_invariants``: Audits zero-leakage training statistics and NaN mask preservation.

Known Defects & Engineering Limitations
========================================

The following engineering limitations and design approximations are cataloged in the defect register:

* **D-NB02-001 (Heuristic 1D Temporal Noise Variance)**: Standard Lee filters operate on 2D spatial radar grids where noise variance is physically bounded by the equivalent number of looks (:math:`\sigma_v^2 \approx 1/L`). Estimating noise variance as the global average of a 1D temporal moving window (:math:`\langle \sigma_t^2 \rangle`) can inadvertently dampen rapid hydrological transitions.
* **D-NB02-002 (Unclipped Min-Max Test Extrapolation)**: Min-Max scaling for NDVI does not enforce ``np.clip(..., 0.0, 1.0)``. If test observations exhibit vegetation density outside the training min/max bounds, normalized values will stray outside :math:`[0, 1]`.
* **D-NB02-003 (Coarse Scene Cloud QC)**: The 50% cloud threshold functions at the scene level rather than the sub-pixel level. Clear sub-regions within a 51% cloudy scene are discarded, while cloud-contaminated sub-pixels within a 49% scene pass through.
* **D-NB02-004 (Uniform Kernel on Irregular Temporal Cadence)**: Sentinel-1 satellite passes occur on irregular 2-to-5 day cycles. The 1D uniform filter treats time steps as equidistant, slightly distorting temporal weighting.
