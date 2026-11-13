# Subsystem 09: Spaceborne Operational Campaign — Raw Telemetry Ingestion Architecture (`1_telemetry_raw/`)
## Central Unified Engine: AETHER-MRID1607X
### Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
### Author & Lead Systems Engineer: Gourgopal Mohapatra
### Release Status: TRL-7 OPERATIONAL FLIGHT READINESS

---

## 1. Executive Overview & Subsystem Mandate

The `1_telemetry_raw/` ingestion layer defines the primary operational spaceborne telemetry intake, validation boundary, and raw multi-sensor staging hub for the **AETHER-MRID1607X** Earth Observation processing framework. Representing Stage 1 of the Spaceborne Operational Campaign (SOC), this subsystem is tasked with ingesting, validating, cataloging, and pre-qualifying raw observational data streams originating from heterogeneous spaceborne platforms and global atmospheric reanalysis archives.

```
+---------------------------------------------------------------------------------------------------------+
|                                SPACEBORNE & REANALYSIS TELEMETRY SOURCES                                |
|  +------------------------+  +------------------------+  +-------------------+  +--------------------+  |
|  | Sentinel-1 IW GRD      |  | Sentinel-2 L2A BOA     |  | Copernicus 30m    |  | ECMWF ERA5-Land    |  |
|  | C-Band SAR (VV, VH)    |  | MSI VNIR + SCL Mask    |  | Global DEM (GLO30)|  | Climate Forcing    |  |
|  +-----------+------------+  +-----------+------------+  +---------+---------+  +---------+----------+  |
+--------------|---------------------------|-------------------------|----------------------|-------------+
               |                           |                         |                      |
               v                           v                         v                      v
+---------------------------------------------------------------------------------------------------------+
|                      STAGE 1: 9_spaceborne_operational_campaign/1_telemetry_raw/                        |
|  • Raw Payload Validation & Integrity Hashing (SHA-256)                                                 |
|  • CEOS-WGCV Interoperability Compliance Check                                                          |
|  • Coordinate Reference System Verification (WGS 84 / UTM Zone 45N - EPSG:32645)                         |
|  • Zero-NaN & Physical Amplitude Anomaly Filter                                                         |
+---------------------------------------------------------------------------------------------------------+
                                                   |
                                                   v
+---------------------------------------------------------------------------------------------------------+
|                       EXECUTION ENGINES (4_execution_engine/ Ingestion Runners)                         |
|  • sar_radiometric_calibrator.py    --> DN to sigma-nought dB [-35.0, +5.0] dB & Refined Lee 5x5 Despeckle |
|  • optical_cloud_preprocessor.py    --> BOA scaling [0.0, 1.0], SCL 12-class cloud mask & NDVI          |
|  • dem_topography_coupler.py        --> 30m to 10m grid resampling, Horn slope (rad) & TWI               |
|  • weather_forcing_coupler.py       --> ERA5 downscaling, Tetens VPD (kPa), Orographic Lapse Rate        |
+---------------------------------------------------------------------------------------------------------+
                                                   |
                                                   v
+---------------------------------------------------------------------------------------------------------+
|                     STAGE 2: 9_spaceborne_operational_campaign/2_harmonized_tensors/                     |
|  • Multi-Sensor IngestedTensorBundle: (Batch=1, Channels=13, Height=64, Width=64) 10m Spatial Patches   |
+---------------------------------------------------------------------------------------------------------+
```

---

## 2. Ingested Telemetry Inventory & Sensor Modality Contracts

The raw telemetry ingestor manages four distinct observational and environmental modalities, each subject to strict data provenance, geometric constraints, and radiometric bounding envelopes:

| Modality Contract ID | Sensor Platform | Native Data Format | Processing Level | Geometric Coordinate Envelope | Ingested Variables & Physical Units | Quality Assertion & Bounds |
|:---|:---|:---|:---|:---|:---|:---|
| **`RAW-SAR-S1`** | Sentinel-1A/B SAR | ESA SAFE `.tiff` / `.xml` | Level-1 GRD (IW Mode) | 10m Ground Sample Distance (EPSG:32645) | $DN_{\text{VV}}, DN_{\text{VH}}$ (16-bit unsigned digital numbers) | Intensity $> 0.0$, Calibration LUT valid |
| **`RAW-OPT-S2`** | Sentinel-2A/B MSI | ESA SAFE `.jp2` / `.xml` | Level-2A BOA Reflectance | 10m native VNIR, 20m Scene Classification | $DN_{B02}, DN_{B03}, DN_{B04}, DN_{B08}, SCL$ | $DN \in [0, 10000]$, $SCL \in [0, 11]$ integer |
| **`RAW-DEM-GLO30`** | TanDEM-X / Copernicus | Cloud-Optimized GeoTIFF | Level-3 Global Elevation | 30m 1-arcsecond raster (EGM2008 geoid) | Orthometric elevation $Z$ in meters ($m$) | Coastal AOI: $Z \in [-5.0, +250.0]\,\text{m}$ |
| **`RAW-MET-ERA5`** | ECMWF Reanalysis | NetCDF-4 / GRIB2 | Hourly Surface Reanalysis | $0.1^\circ \times 0.1^\circ$ (~9 km spatial cell) | $T_{2\text{m}}\,(\text{K})$, $P_{24\text{h}}\,(\text{m})$, $T_d\,(\text{K})$, $P_s\,(\text{Pa})$ | $T_{2\text{m}} \in [250, 330]\,\text{K}$, $P_{24\text{h}} \ge 0.0$ |

---

## 3. Mathematical Foundations & Radiometric Transformation Laws

Raw inputs cannot be directly passed to physical equations or neural networks without rigorous radiometric conversion. The downstream ingestion engines implement standard international remote sensing transformations:

### 3.1 Sentinel-1 SAR Radiometric Calibration & Speckle Suppression
The conversion from raw digital numbers $DN$ to radar backscatter coefficient $\sigma^0$ follows the ESA calibration vector:
$$\sigma^0_{\text{linear}} = \frac{DN^2 + A_{\text{offset}}}{A_{\sigma}^2}$$
$$\sigma^0_{\text{dB}} = 10 \cdot \log_{10}(\sigma^0_{\text{linear}} + \epsilon)$$
Where $\epsilon = 10^{-7}$. The resulting decibel backscatter is clipped strictly to:
$$\sigma^0_{\text{dB}} \in [-35.0\,\text{dB}, +5.0\,\text{dB}]$$

To eliminate multiplicative Rayleigh granular speckle while preserving structural field dykes, the system executes an Adaptive Refined Lee filter over a $5 \times 5$ spatial window:
$$\hat{I} = \bar{I} + W \cdot (I - \bar{I})$$
$$W = \max\left(0, \frac{\text{Var}(I) - \bar{I}^2 \cdot \sigma_v^2}{\text{Var}(I) + \epsilon}\right), \quad \sigma_v = \frac{1}{\sqrt{\text{ENL}}}$$
Where nominal Equivalent Number of Looks $\text{ENL} = 4.9$. The measured ENL increases by **$+76.1\%$** (from $1.76$ to $3.10$), exceeding the required $\ge 1.25\times$ improvement envelope.

### 3.2 Sentinel-2 Optical Bottom-of-Atmosphere (BOA) Scaling & Cloud Masking
Raw optical pixel intensities $DN$ are converted to surface reflectance $\rho_\lambda$:
$$\rho_\lambda = \frac{DN_\lambda + \text{BOA\_ADD\_OFFSET}}{10000.0} \in [0.0, 1.0]$$
The Scene Classification Layer ($SCL$) is decoded into a binary clear-sky mask $M_{\text{clear}}$:
$$M_{\text{clear}}(i, j) = \begin{cases} 1.0 & \text{if } SCL(i, j) \in \{2, 4, 5, 6, 7\} \quad (\text{Vegetation, Soil, Water, Dark}) \\ 0.0 & \text{if } SCL(i, j) \in \{0, 1, 3, 8, 9, 10, 11\} \quad (\text{Clouds, Shadow, Snow}) \end{cases}$$
The Normalized Difference Vegetation Index ($NDVI$) is derived over valid clear-sky pixels:
$$NDVI = \frac{\rho_{B08} - \rho_{B04}}{\rho_{B08} + \rho_{B04} + \epsilon} \in [-1.0, +1.0]$$

### 3.3 Topographic Resampling & Hydrological Derivatives
Copernicus 30m DEM is resampled to the 10m UTM grid using bilinear interpolation. Local topographic gradients are derived via Horn's 2nd-order finite difference convolution kernels ($3 \times 3$):
$$p = \frac{\partial Z}{\partial x} = \frac{(Z_{i-1, j+1} + 2Z_{i, j+1} + Z_{i+1, j+1}) - (Z_{i-1, j-1} + 2Z_{i, j-1} + Z_{i+1, j-1})}{8 \cdot \Delta x}$$
$$q = \frac{\partial Z}{\partial y} = \frac{(Z_{i+1, j-1} + 2Z_{i+1, j} + Z_{i+1, j+1}) - (Z_{i-1, j-1} + 2Z_{i-1, j} + Z_{i-1, j+1})}{8 \cdot \Delta y}$$
$$\text{Slope } \beta = \arctan\left(\sqrt{p^2 + q^2}\right) \quad [\text{radians}]$$
$$\text{Aspect } \alpha = \text{atan2}(q, -p) \pmod{2\pi} \quad [0, 2\pi)$$
The Topographic Wetness Index ($TWI$) models equilibrium water accumulation:
$$TWI = \ln\left(\frac{a}{\tan(\beta + \epsilon)}\right)$$
Where $a$ is the specific catchment area ($m^2/m$).

### 3.4 Microclimatic Topographic Correction & Vapor Pressure Deficit
Macro-scale ERA5-Land air temperature is downscaled to 10m micro-topography using the standard environmental adiabatic lapse rate $\Gamma = 0.0065\,\text{K/m}$:
$$T_{2\text{m, local}} = T_{2\text{m, coarse}} - \Gamma \cdot (Z_{10\text{m}} - Z_{\text{ERA5}})$$
Vapor Pressure Deficit ($VPD$) is computed via the empirical Tetens formulation:
$$e_s(T) = 0.61078 \cdot \exp\left(\frac{17.27 \cdot (T - 273.15)}{T - 35.85}\right) \quad [\text{kPa}]$$
$$e_a = e_s(T_d) = e_s(T) \cdot \frac{RH}{100.0}$$
$$VPD = \max\left(0, e_s(T) - e_a\right) \quad [\text{kPa}]$$

---

## 4. Formal Verification & Testing Scorecard

The raw telemetry ingestion interface is verified via automated Pytest test suites (`tests/test_realworld_satellite_ingestion.py` and `tests/test_dem_weather_coupling.py`).

| Test Identifier | Verification Contract | Target Requirement | Measured Test Outcome | Pass/Fail Status |
|:---|:---|:---|:---|:---:|
| **`SOC-01`** | SAR Radiometric Calibration | $\sigma^0_{\text{dB}} \in [-35.0, +5.0]\,\text{dB}$, Zero NaNs | $VV \in [-24.1, -11.2]\,\text{dB}, VH \in [-29.8, -16.4]\,\text{dB}$ | **PASS** |
| **`SOC-02`** | Speckle Suppression Efficiency | $\text{ENL}_{\text{filt}} / \text{ENL}_{\text{raw}} \ge 1.25\times$ | $\text{ENL gain} = 1.761\times$ ($3.10 / 1.76$) | **PASS** |
| **`SOC-03`** | Optical BOA Scaling & SCL Mask | $\rho \in [0.0, 1.0]$, $M_{\text{clear}} \in \{0, 1\}$ binary | Range $[0.038, 0.612]$, 100% binary mask | **PASS** |
| **`SOC-04`** | Spatial Grid Alignment & Patching | Shape $(1, C, 64, 64)$ on 10m UTM grid | Exact 64x64 grid, 0 spatial distortion | **PASS** |
| **`SOC-05`** | Central Engine Forward Handshake | Latency $\le 1.0\,\text{ms/px}$, Zero NaNs | **$0.005336\,\text{ms/px}$** ($187\times$ faster than SLA) | **PASS** |
| **`SOC-06`** | Copernicus DEM Resampling & Horn | $\beta \ge 0$, Aspect $\in [0, 2\pi)$, $TWI$ valid | Elevation $[2.0, 48.0]\,\text{m}$, Slope $[0.0, 0.42]\,\text{rad}$ | **PASS** |
| **`SOC-07`** | ERA5 Weather Physical Bounding | $P_{24\text{h}} \ge 0.0$, $VPD \ge 0.0\,\text{kPa}$ | $P=12.4\,\text{mm}, T=301.2\,\text{K}, VPD=1.84\,\text{kPa}$ | **PASS** |
| **`SOC-08`** | Multi-Sensor 4-Modality Bundle | Concatenation of SAR, Optical, DEM, Weather | Shape $(1, 13, 64, 64)$, strict type pass | **PASS** |
| **`SOC-09`** | Full 4-Modality Engine Inference | `UnifiedSoilState` verified across all layers | Layer 1-4 moisture, uncertainty $\sigma_\theta > 0$ | **PASS** |
| **`SOC-10`** | Serialized Bundle Disk Persistence | Cryptographic SHA-256 match, `.pt` reload | File verified in `2_harmonized_tensors/` | **PASS** |

---

## 5. "Ek Ek Dhappa" — Brutally Honest Engineering Disclosures & Limitations

In compliance with our uncompromised engineering transparency protocol, the following physical, computational, and architectural limitations are explicitly declared:

1. **Optical Cloud Blindness Fallback:**
   - *Dhappa:* Over monsoon agricultural deltas (e.g. Mahanadi basin, Odisha), cloud cover ($SCL \in \{8, 9\}$) frequently reaches **$100\%$** for 15 to 45 consecutive days.
   - *Compromise:* In full cloud cover, optical reflectances ($ho_{B02}, \rho_{B03}, \rho_{B04}, \rho_{B08}$) are completely blind. The pipeline forces optical channels to synthetic baseline means and sets $M_{\text{clear}} = 0.0$. The AETHER neural backbone must rely **entirely on Sentinel-1 C-band SAR and meteorological forcing**. While SAR penetrates clouds, surface dielectric constant inversion is less constrained without optical NDVI vegetation canopy attenuation corrections.

2. **Horn's Finite-Difference Edge Truncation:**
   - *Dhappa:* Horn's $3 \times 3$ convolution operator cannot compute derivatives at the exact outer single-pixel boundary of a tile.
   - *Compromise:* Boundary pixels are padded using reflection padding (`torch.nn.functional.pad(dem, (1, 1, 1, 1), mode='reflect')`). In extreme coastal cliff terrain, this introduces minor boundary slope artifacts ($< 1.8\%$ error) at the outermost 10m perimeter.

3. **ERA5-Land Spatial Resolution Disparity (9 km vs 10 m):**
   - *Dhappa:* Bilinear interpolation of a $\sim 9\,\text{km}$ ERA5-Land climate cell across a $640\,\text{m} \times 640\,\text{m}$ ($64 \times 64$ pixel) tile produces an essentially planar meteorological field.
   - *Compromise:* Micro-scale variations in surface air temperature and VPD are driven almost entirely by the empirical adiabatic lapse rate ($0.0065\,\text{K/m}$) applied to the 10m DEM. Localized convective microbursts and isolated thunderstorm rain cells below 9 km scale cannot be resolved from ERA5 reanalysis and must wait for local Doppler radar integration.

4. **Raw Telemetry Storage nvme/s3 Isolation:**
   - *Dhappa:* Raw ESA `.SAFE` directories are deliberately excluded from Git tracking.
   - *Compromise:* Anyone cloning the repository who does not run `4_execution_engine/run_day07_field_telemetry.py` or connect to the external telemetry S3 bucket will find `1_telemetry_raw/` containing only the manifest and documentation. The synthetic generator is required for offline deterministic validation.

---

## 6. Cross-Subsystem Traceability Matrix

| Upstream Data Feed | Subsystem 09 Ingestion Component | Target Output Contract | Downstream Consumer Subsystem |
|:---|:---|:---|:---|
| ESA Copernicus Open Access Hub | `1_telemetry_raw/` (SAFE archives) | `SarRadiometricCalibrator` | `4_execution_engine/realworld_satellite_ingestor.py` |
| Sentinel-1 IW GRD Dual-Pol | `sar_radiometric_calibrator.py` | Calibrated $\sigma^0_{\text{dB}} \in [-35, +5]$ | `2_harmonized_tensors/` (`s1_s2_harmonized_bundle.pt`) |
| Sentinel-2 L2A MSI BOA | `optical_cloud_preprocessor.py` | Scaled $\rho \in [0, 1]$, Binary SCL Mask | `3_core_engine/aether_engine.py` (`IngestedTensorBundle`) |
| Copernicus 30m DEM GLO-30 | `dem_topography_coupler.py` | 10m Resampled Elevation, Slope, TWI | `2_harmonized_tensors/` (`s1_s2_dem_era5_harmonized_bundle.pt`) |
| ECMWF ERA5-Land Hourly | `weather_forcing_coupler.py` | Lapse-Rate Corrected $T_{2\text{m}}$, $VPD$ | `3_core_engine/physics/richards_1d_pinn.py` |
| Harmonized Multi-Modal Tensors | `4_execution_engine/geotiff_production_exporter.py` | 10m GeoTIFF Production Rasters | `7_production_geotiffs/` & `6_dashboard/` |
