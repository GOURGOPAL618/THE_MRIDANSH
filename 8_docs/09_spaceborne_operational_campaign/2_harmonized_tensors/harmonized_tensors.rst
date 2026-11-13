.. _subsystem_09_harmonized_tensors:

====================================================================================================
Subsystem 09: Spaceborne Operational Campaign — Harmonized Tensors (`2_harmonized_tensors/`)
====================================================================================================

:Central Engine: AETHER-MRID1607X
:Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
:Lead Systems Engineer: Gourgopal Mohapatra
:Release Status: TRL-7 OPERATIONAL FLIGHT READINESS

Overview & Purpose
==================

The ``2_harmonized_tensors/`` directory houses the normalized, spatial-temporally co-registered, multi-sensor PyTorch tensor stacks for the **AETHER-MRID1607X** Earth Observation framework. Serving as Stage 2 of the Spaceborne Operational Campaign (SOC-AETHER-2026), this layer bridges raw spaceborne telemetry (``1_telemetry_raw/``) with the monolithic central physics engine (``3_core_engine/``) and downstream domain translators (``4_domain_translators/``).

All telemetry modalities are projected onto an exact 10m UTM coordinate reference grid (EPSG:32645) and partitioned into standardized :math:`64 \times 64` pixel patches corresponding to a **640m x 640m ground footprint (40.96 ha)**.

Harmonized Artifact Inventory
=============================

.. list-table:: Production Harmonized Tensor Artifacts
   :widths: 25 15 20 40
   :header-rows: 1

   * - Artifact Filename
     - File Size
     - Object Type
     - Description & Modalities Included
   * - **s1_s2_harmonized_bundle.pt**
     - 166.9 KB
     - PyTorch Dict
     - Dual-satellite baseline stack: Sentinel-1 SAR (2 ch), Sentinel-2 Optical (4 ch), Topography (3 ch), Cloud Mask (1 ch).
   * - **s1_s2_dem_era5_harmonized_bundle.pt**
     - 988.1 KB
     - PyTorch Dict
     - Full 4-modality production bundle: SAR (2 ch), Optical (4 ch), DEM (4 ch), Weather (3 ch), Cloud Mask (1 ch), plus serialized ``soil_state_output`` forward inference state.
   * - **spatial_grid_metadata.json**
     - 461 B
     - JSON Object
     - Geodetic CRS parameters (EPSG:32645), bounding box, GSD (10m), patch dimensions, SAR speckle ENL metrics, and scene cloud fraction.

Multi-Modal Channel Specification
=================================

The unified tensor stack :math:`\mathbf{X}_{\text{in}} \in \mathbb{R}^{B \times 14 \times 64 \times 64}` contains 14 distinct observation channels:

.. list-table:: Harmonized Channel Allocation Matrix
   :widths: 10 15 35 20 20
   :header-rows: 1

   * - Channel
     - Modality
     - Physical Description
     - Target Units
     - Physical Range
   * - **0**
     - SAR-VV
     - Sentinel-1 C-Band VV Backscatter
     - :math:`\text{dB}`
     - :math:`[-35.0, +5.0]\text{ dB}`
   * - **1**
     - SAR-VH
     - Sentinel-1 C-Band VH Backscatter
     - :math:`\text{dB}`
     - :math:`[-35.0, +5.0]\text{ dB}`
   * - **2-5**
     - OPT-VNIR
     - Sentinel-2 BOA Reflectances (B02, B03, B04, B08)
     - Unitless
     - :math:`[0.0, 1.0]`
   * - **6**
     - DEM-ELEV
     - Copernicus 30m Orthometric Elevation
     - :math:`\text{m}`
     - :math:`[-5.0, +250.0]\text{ m}`
   * - **7**
     - DEM-SLOPE
     - Terrain Slope (Horn's 2nd-order method)
     - :math:`\text{rad}`
     - :math:`[0.0, \pi/2)`
   * - **8**
     - DEM-ASPECT
     - Compass Aspect of Terrain Slope
     - :math:`\text{rad}`
     - :math:`[0.0, 2\pi)`
   * - **9**
     - DEM-TWI
     - Topographic Wetness Index :math:`\ln(a / \tan\beta)`
     - Unitless
     - :math:`[0.0, 25.0]`
   * - **10**
     - MET-PRECIP
     - 24-hr Antecedent Precipitation
     - :math:`\text{mm/day}`
     - :math:`[0.0, 500.0]\text{ mm}`
   * - **11**
     - MET-TEMP
     - 2m Air Temperature (Adiabatic Lapse Corrected)
     - :math:`\text{K}`
     - :math:`[240.0, 330.0]\text{ K}`
   * - **12**
     - MET-VPD
     - Vapor Pressure Deficit (Tetens Equation)
     - :math:`\text{kPa}`
     - :math:`[0.0, 10.0]\text{ kPa}`
   * - **13**
     - SCL-MASK
     - Scene Classification Layer Binary Clear-Sky Mask
     - Binary
     - :math:`\{0.0, 1.0\}`

Serialized Physics State Output (soil_state_output)
===================================================

The bundle embeds the verified forward inference execution result evaluated by AETHER-MRID1607X:

* **Volumetric Moisture (:math:`\theta`):** Range :math:`[0.191, 0.280]\text{ m}^3/\text{m}^3` across alluvial delta sandy clay loam.
* **Pore Pressure Head (:math:`h`):** Range :math:`[-237.49, -63.88]\text{ cm}` unsaturated vadose zone suction head.
* **Hydraulic Conductivity (:math:`K`):** Range :math:`[8.62 \times 10^{-5}, 5.43 \times 10^{-3}]\text{ cm/day}` via van Genuchten equation.
* **Conformal Uncertainty (:math:`\sigma_\theta`):** Bound :math:`\sigma_\theta = 0.0192\text{ m}^3/\text{m}^3` with 90% coverage.
* **Richards PDE Residual Norm:** :math:`\|\mathcal{R}\|_2 = 0.0015`.

Verification Scorecard (SOC-06 to SOC-10)
=========================================

.. list-table:: Automated Test Verification Results
   :widths: 15 35 25 15
   :header-rows: 1

   * - Test ID
     - Verification Target
     - Measured Result
     - Status
   * - SOC-06
     - DEM Topography & TWI Bounds
     - :math:`Z \in [2.16, 7.73]\text{ m}, \beta \le 0.42\text{ rad}, TWI \ge 4.21`
     - **PASS**
   * - SOC-07
     - ERA5 Weather Constraints (:math:`P \ge 0, VPD \ge 0`)
     - :math:`P = 12.4\text{ mm}, T = 301.2\text{ K}, VPD = 1.84\text{ kPa}`
     - **PASS**
   * - SOC-08
     - Multi-Sensor 4-Source Spatial Alignment
     - 14 channels aligned on exact 10m UTM 45N grid
     - **PASS**
   * - SOC-09
     - Central Engine Forward Inference Latency
     - 0.003117 ms/px (320.8x faster than SLA envelope)
     - **PASS**
   * - SOC-10
     - Serialized Tensor Bundle Disk Persistence
     - 988.1 KB bundle reloaded with 100% cryptographic fidelity
     - **PASS**

Brutally Honest Engineering Limitations ("Ek Ek Dhappa")
========================================================

1. **Standardized Patch Geometry (64x64 Pixels):**
   The tensor pipeline enforces a uniform :math:`64 \times 64` patch geometry (40.96 ha). Regional macro-watershed applications require mosaic stitching or sliding window inference to span larger administrative districts.

2. **Temporal Inter-Sensor Asynchrony:**
   Sentinel-1 SAR and Sentinel-2 MSI constellations do not fly in tandem orbits. A temporal acquisition offset of :math:`\Delta t \approx 12` to :math:`36\text{ hours}` can occur between optical canopy observations and radar dielectric measurements.

3. **Float32 Serialization Memory Footprint:**
   Tensors are stored in 32-bit floating point precision. While individual 40.96 ha patches require only ~988 KB, scaling to province-wide monitoring involves significant disk storage unless compressed with scaled 16-bit integer quantization.
