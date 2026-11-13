.. _subsystem_09_ground_truth:

====================================================================================================
Subsystem 09: Spaceborne Operational Campaign — In-Situ Ground Truth (`3_ground_truth/`)
====================================================================================================

:Central Engine: AETHER-MRID1607X
:Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
:Lead Systems Engineer: Gourgopal Mohapatra
:Release Status: TRL-7 OPERATIONAL FLIGHT READINESS

Overview & Purpose
==================

The ``3_ground_truth/`` subsystem defines the physical truth baseline, in-situ sensor data contracts, and spatial-temporal collocation pipeline for the **AETHER-MRID1607X** Earth Observation framework. Serving as Stage 3 of the Spaceborne Operational Campaign (SOC-AETHER-2026), this layer establishes the experimental foundation for calibration, validation, and comparative benchmark evaluation against classical baseline algorithms.

The network adheres to the **CEOS-WGCV Match-Up Protocol**, **ISMN Quality Taxonomy**, and **NASA SMAP Core Cal/Val** standards.

In-Situ Station Network Architecture
====================================

The network comprises 24 physical in-situ stations distributed across a :math:`1.28\text{ km} \times 1.28\text{ km}` coastal delta domain (:math:`20.25^\circ\text{N}, 86.40^\circ\text{E}`) in Odisha, India:

* **Dual-Depth Hydrological Sensing:** Surface (:math:`0-5\text{ cm}`) and Root-zone (:math:`5-30\text{ cm}`) volumetric soil moisture.
* **Instrumentation:** Campbell CS616 Time-Domain Reflectometers (TDR) and Stevens HydraProbe (50 MHz) coaxial impedance dielectric sensors.
* **Textural Regimes:** 4 USDA classes (Loam, Silt Loam, Clay Loam, Sandy Loam).
* **Soil Matrix Variables:** Dry Bulk Density (:math:`\rho_b \in [1.237, 1.570]\text{ g/cm}^3`) and Soil Organic Carbon (:math:`SOC \in [0.80, 2.69]\%`).

Dataset Artifact Inventory
==========================

.. list-table:: In-Situ Ground Truth Artifacts
   :widths: 25 15 15 45
   :header-rows: 1

   * - Artifact Filename
     - File Size
     - Dimensions
     - Description & Role
   * - **insitu_soil_stations.csv**
     - 4.2 KB
     - 24 × 16
     - Master physical station coordinates, sensor probe types, surface/rootzone moisture, temperature, and ISMN QC flags.
   * - **collocated_insitu_matrix.csv**
     - 5.7 KB
     - 24 × 29
     - Collocated feature matrix: exact pixel coordinates :math:`(i, j)` on 10m UTM 45N grid, extracted SAR, Optical, Topographic, and Weather variables.
   * - **aether_collocated_predictions.csv**
     - 6.9 KB
     - 24 × 36
     - Comparative benchmark matrix: binds ground truth with AETHER-MRID1607X physical predictions, suction head, hydraulic conductivity, and conformal uncertainty bounds.

Geodetic Mapping & 29-Feature Collocation
=========================================

For each station :math:`k` with geodetic UTM coordinates :math:`(E_k, N_k)`, the exact pixel index :math:`(i_k, j_k)` on the 10m grid is mapped:

.. math::

   j_k = \text{clamp}\left(\left\lfloor \frac{E_k - X_{\text{min}}}{\Delta x} \right\rfloor, 0, W - 1\right)

.. math::

   i_k = \text{clamp}\left(\left\lfloor \frac{Y_{\text{max}} - N_k}{\Delta y} \right\rfloor, 0, H - 1\right)

The collocator extracts a 29-dimensional synchronized state vector uniting:
- **SAR Observables:** :math:`\sigma^0_{\text{VV}}, \sigma^0_{\text{VH}}` in dB and Polarization Ratio :math:`PR = \sigma^0_{\text{VV}} - \sigma^0_{\text{VH}}`.
- **Optical VNIR:** BOA reflectances :math:`\rho_{B02}, \rho_{B03}, \rho_{B04}, \rho_{B08}, NDVI, NDWI`, clear sky mask.
- **Topography:** Elevation :math:`Z\text{ [m]}`, Slope :math:`\beta\text{ [deg]}`, Aspect :math:`\alpha\text{ [deg]}`, and :math:`TWI`.
- **Meteorology:** :math:`P_{24\text{h}}\text{ [mm]}, T_{2\text{m}}\text{ [}^\circ\text{C]}, VPD\text{ [kPa]}`.
- **In-Situ Truth:** :math:`\theta_{\text{surf}}, \theta_{\text{root}}, \rho_b`, and USDA texture.

Verification Scorecard (SOC-11 to SOC-15)
=========================================

.. list-table:: Automated Test Verification Results
   :widths: 15 35 25 15
   :header-rows: 1

   * - Test ID
     - Verification Target
     - Measured Result
     - Status
   * - SOC-11
     - In-Situ Ground Truth Ingestion Bounds
     - 24 stations, :math:`\bar{\theta} = 0.1855\text{ m}^3/\text{m}^3`, :math:`\bar{\rho}_b = 1.3784\text{ g/cm}^3`
     - **PASS**
   * - SOC-12
     - Spatial-Temporal Collocation Grid Accuracy
     - 100% stations mapped into :math:`64 \times 64` 10m grid
     - **PASS**
   * - SOC-13
     - Physical Sensor Correlation Integrity
     - Pearson :math:`r(\sigma^0_{\text{VV}}, \theta_{\text{surf}}) = +0.584`
     - **PASS**
   * - SOC-14
     - Naive Optical Regression Baseline (NDVI)
     - :math:`R^2 = 0.182, RMSE = 0.0612\text{ m}^3/\text{m}^3`
     - **PASS**
   * - SOC-15
     - SAR Water Cloud Model (WCM) Baseline
     - :math:`R^2 = 0.441, RMSE = 0.0487\text{ m}^3/\text{m}^3`
     - **PASS**

Brutally Honest Engineering Limitations ("Ek Ek Dhappa")
========================================================

1. **Point-to-Pixel Spatial Representativeness Scale Gap:**
   An in-situ probe measures soil permittivity in a localized volume of :math:`\sim 100\text{ cm}^3`, whereas a 10m satellite pixel represents a footprint of :math:`100\text{ m}^2` (:math:`10^6\times` volume disparity). Micro-scale soil heterogeneities within the pixel introduce unavoidable spatial representativeness uncertainty.

2. **Probe Electronics Calibration Discrepancy:**
   The network utilizes both Campbell CS616 TDR (175 MHz) and Stevens HydraProbe (50 MHz) sensors. Operating at high tropical soil temperatures (:math:`>29^\circ\text{C}`), differences in dielectric frequency response introduce an empirical offset of :math:`\Delta \theta \approx 0.012\text{ m}^3/\text{m}^3` between sensor models in clay loam regimes.

3. **Sparse Station Density (24 Stations over 164 ha):**
   While conforming to NASA SMAP Core Cal/Val requirements for regional verification, fine-scale spatial variograms across the 40.96 ha AOI depend in part on geostatistical covariance models.
