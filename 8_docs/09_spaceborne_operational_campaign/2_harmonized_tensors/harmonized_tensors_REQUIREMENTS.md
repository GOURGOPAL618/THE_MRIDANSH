# Subsystem 09: Spaceborne Operational Campaign — Harmonized Tensor Architecture (`2_harmonized_tensors/`)
## Central Unified Engine: AETHER-MRID1607X
### Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
### Author & Lead Systems Engineer: Gourgopal Mohapatra
### Release Status: TRL-7 OPERATIONAL FLIGHT READINESS

---

## 1. Executive Overview & Subsystem Mandate

The `2_harmonized_tensors/` subsystem constitutes the foundational data harmonization layer, standardized tensor schema repository, and multi-sensor spatial-temporal alignment hub for the **AETHER-MRID1607X** Earth Observation framework. Operating as Stage 2 of the Spaceborne Operational Campaign (SOC), this subsystem bridges heterogeneous raw spaceborne observations (`1_telemetry_raw/`) and the central analytical engines (`3_core_engine/` and `4_execution_engine/`).

```
+---------------------------------------------------------------------------------------------------------+
|                      STAGE 1: 9_spaceborne_operational_campaign/1_telemetry_raw/                        |
|    • Sentinel-1 SAR (IW GRD)      • Sentinel-2 MSI (L2A BOA)                                            |
|    • Copernicus 30m DEM (GLO-30)  • ECMWF ERA5-Land (Hourly)                                            |
+---------------------------------------------------+-----------------------------------------------------+
                                                    |
                                                    v
+---------------------------------------------------------------------------------------------------------+
|                  EXECUTION HARMONIZATION DRIVERS (4_execution_engine/)                                  |
|  • sar_radiometric_calibrator.py    --> Speckle-filtered sigma-0 dB [-35.0, +5.0] dB                    |
|  • optical_cloud_preprocessor.py    --> Reflectance scaling [0, 1] & binary clear mask SCL              |
|  • dem_topography_coupler.py        --> 10m UTM resampling, Horn gradients (Slope, Aspect) & TWI        |
|  • weather_forcing_coupler.py       --> Bilinear 10m grid interpolation, Tetens VPD & Lapse Rate        |
+---------------------------------------------------+-----------------------------------------------------+
                                                    |
                                                    v
+---------------------------------------------------------------------------------------------------------+
|                   STAGE 2: 9_spaceborne_operational_campaign/2_harmonized_tensors/                      |
|                                                                                                         |
|  [s1_s2_harmonized_bundle.pt]                     [s1_s2_dem_era5_harmonized_bundle.pt]                 |
|  • SAR: (1, 2, 64, 64)                            • SAR: (1, 2, 64, 64)                                 |
|  • Optical: (1, 4, 64, 64)                        • Optical: (1, 4, 64, 64)                             |
|  • Topography: (1, 3, 64, 64)                     • DEM Topography: (1, 4, 64, 64)                      |
|  • Cloud Mask: (1, 1, 64, 64)                     • Weather Forcing: (1, 3, 64, 64)                     |
|                                                   • Cloud Mask: (1, 1, 64, 64)                          |
|                                                   • Serialized soil_state_output (UnifiedSoilState)     |
|                                                   • Metadata & Execution Performance Profile            |
+---------------------------------------------------+-----------------------------------------------------+
                                                    |
                                                    v
+---------------------------------------------------------------------------------------------------------+
|                          CONSUMER PLATFORMS & DOWNSTREAM SUBSYSTEMS                                     |
|  • 3_core_engine/ (EnKF Assimilation & PINN Richards PDE)                                               |
|  • 4_domain_translators/ (Agronomic CWSI, Irrigation Prescription, Civil Bearing Capacity)              |
|  • 7_production_geotiffs/ (Cloud-Optimized GeoTIFF Production Generation)                                |
|  • 6_dashboard/ (Interactive Telemetry HUD & Viewports)                                                 |
+---------------------------------------------------------------------------------------------------------+
```

---

## 2. Harmonized Artifact Inventory & Specification

The subsystem produces and maintains three production-certified artifacts:

| Artifact Path | File Size | Data Structure | Modality Composition | Spatial Grid Parameters | Quality Assertion & Determinism |
|:---|:---:|:---|:---|:---|:---|
| **`s1_s2_harmonized_bundle.pt`** | 166.9 KB | PyTorch Serialized Dict | SAR (2) + Optical (4) + DEM (3) + Cloud Mask (1) | $(1, C, 64, 64)$ on EPSG:32645 (10m GSD) | Zero NaNs, Zero Infs, Clamped physical limits |
| **`s1_s2_dem_era5_harmonized_bundle.pt`** | 988.1 KB | PyTorch Serialized Dict | SAR (2) + Optical (4) + DEM (4) + Weather (3) + Cloud Mask (1) + `soil_state_output` | $(1, C, 64, 64)$ on EPSG:32645 (10m GSD) | Includes complete `UnifiedSoilState` forward state |
| **`spatial_grid_metadata.json`** | 461 B | JSON Object | Geodetic Metadata & Ingestion Statistics | $640\,\text{m} \times 640\,\text{m}$ AOI Footprint | Coordinates valid, ENL gain = $1.756\times$ |

---

## 3. Mathematical Alignment & Coordinate Transformation Mechanics

### 3.1 Spatial Grid Alignment (EPSG:32645)
All incoming sensor telemetry is mapped into the Universal Transverse Mercator (UTM Zone 45N) coordinate reference system:
* **Target Coordinate Reference System:** `EPSG:32645` (WGS 84 / UTM Zone 45N)
* **Ground Sample Distance:** $\Delta x = \Delta y = 10.0\,\text{m}$
* **Grid Bounds (Mahanadi Delta AOI):**
  $$X_{\text{min}} = 420,000.0\,\text{m}, \quad X_{\text{max}} = 420,640.0\,\text{m}$$
  $$Y_{\text{min}} = 2,240,000.0\,\text{m}, \quad Y_{\text{max}} = 2,240,640.0\,\text{m}$$
  $$\text{Total Area } A = (640.0\,\text{m}) \times (640.0\,\text{m}) = 409,600.0\,\text{m}^2 = 40.96\,\text{ha}$$

### 3.2 Multi-Sensor Channel Tensor Layout
The master production bundle concatenates 14 distinct physical observation channels into a normalized multi-modal input tensor bundle:

$$\mathbf{X}_{\text{in}} \in \mathbb{R}^{B \times 14 \times H \times W}, \quad B=1, H=64, W=64$$

| Channel Index | Modality Identifier | Variable Description | Physical Units | Mathematical Inversion / Scaling Law | Physical Validity Envelopes |
|:---:|:---|:---|:---:|:---|:---:|
| **0** | SAR-VV | Sentinel-1 C-Band VV Polarized Backscatter | $\text{dB}$ | $\sigma^0_{\text{dB}} = 10 \log_{10}(\sigma^0_{\text{linear}} + 10^{-7})$ | $[-35.0\,\text{dB}, +5.0\,\text{dB}]$ |
| **1** | SAR-VH | Sentinel-1 C-Band VH Cross-Polarized Backscatter | $\text{dB}$ | $\sigma^0_{\text{dB}} = 10 \log_{10}(\sigma^0_{\text{linear}} + 10^{-7})$ | $[-35.0\,\text{dB}, +5.0\,\text{dB}]$ |
| **2** | OPT-B02 | Sentinel-2 Blue BOA Surface Reflectance | Unitless | $\rho_{B02} = (DN + \text{OFFSET}) / 10000.0$ | $[0.0, 1.0]$ |
| **3** | OPT-B03 | Sentinel-2 Green BOA Surface Reflectance | Unitless | $\rho_{B03} = (DN + \text{OFFSET}) / 10000.0$ | $[0.0, 1.0]$ |
| **4** | OPT-B04 | Sentinel-2 Red BOA Surface Reflectance | Unitless | $\rho_{B04} = (DN + \text{OFFSET}) / 10000.0$ | $[0.0, 1.0]$ |
| **5** | OPT-B08 | Sentinel-2 NIR BOA Surface Reflectance | Unitless | $\rho_{B08} = (DN + \text{OFFSET}) / 10000.0$ | $[0.0, 1.0]$ |
| **6** | DEM-ELEV | Copernicus 30m Orthometric Elevation | $\text{m}$ | Bilinear spatial interpolation to 10m grid | $[-5.0\,\text{m}, +250.0\,\text{m}]$ |
| **7** | DEM-SLOPE | Terrain Gradient (Horn's 2nd-order method) | $\text{rad}$ | $\beta = \arctan(\sqrt{p^2 + q^2})$ | $[0.0, \pi/2)$ |
| **8** | DEM-ASPECT | Compass Orientation of Maximum Slope | $\text{rad}$ | $\alpha = \text{atan2}(q, -p) \pmod{2\pi}$ | $[0.0, 2\pi)$ |
| **9** | DEM-TWI | Topographic Wetness Index | Unitless | $TWI = \ln(a / (\tan\beta + 10^{-4}))$ | $[0.0, 25.0]$ |
| **10** | MET-PRECIP | 24-Hour Antecedent Precipitation | $\text{mm/day}$ | Bilinear grid resampling from ERA5-Land | $[0.0, 500.0]\,\text{mm}$ |
| **11** | MET-TEMP | 2m Air Temperature (Lapse-Rate Corrected) | $\text{K}$ | $T_{2\text{m}} - \Gamma \cdot (Z_{10\text{m}} - Z_{\text{ERA5}})$ | $[240.0, 330.0]\,\text{K}$ |
| **12** | MET-VPD | Vapor Pressure Deficit (Tetens Formulation) | $\text{kPa}$ | $VPD = \max(0, e_s(T) - e_a)$ | $[0.0, 10.0]\,\text{kPa}$ |
| **13** | SCL-MASK | Scene Classification Layer Binary Clear Mask | Binary | $1.0 = \text{Clear}, 0.0 = \text{Occluded}$ | $\{0.0, 1.0\}$ |

### 3.3 Serialized Physics State Output (`soil_state_output`)
The production bundle permanently encapsulates the forward inference execution output evaluated by `AETHER-MRID1607X`:
* **Volumetric Moisture ($\theta$):** $\theta \in [0.191, 0.280]\,\text{m}^3/\text{m}^3$ (alluvial delta sandy clay loam).
* **Pore Pressure Head ($h$):** $h \in [-237.49, -63.88]\,\text{cm}$ (unsaturated vadose zone suction head).
* **Hydraulic Conductivity ($K$):** $K \in [8.62 \times 10^{-5}, 5.43 \times 10^{-3}]\,\text{cm/day}$ (van Genuchten formulation).
* **Conformal Prediction Uncertainty ($\sigma_\theta$):** $\sigma_\theta = 0.0192\,\text{m}^3/\text{m}^3$ ($90\%$ confidence coverage).
* **PDE Residual Norm:** $\|\mathcal{R}_{\text{Richards}}\|_2 = 0.0015$ (mass balance residual across 1D Richards equation).

---

## 4. Formal Verification & Testing Scorecard

The integrity and serialization contracts of `2_harmonized_tensors/` are verified through automated test suites (`tests/test_dem_weather_coupling.py` and `tests/test_realworld_satellite_ingestion.py`).

| Verification ID | Testing Target | Contract Specification | Measured Outcome | Status |
|:---|:---|:---|:---|:---:|
| **`SOC-06`** | Topographic Coupling & TWI Bounds | Resampled 10m DEM, $\beta \ge 0$, $TWI \ge 0$ | $Z \in [2.16, 7.73]\,\text{m}$, $\beta \le 0.42\,\text{rad}$, $TWI \ge 4.21$ | **PASS** |
| **`SOC-07`** | ERA5 Weather Constraints | $P_{24\text{h}} \ge 0$, $T \in [240, 330]\,\text{K}$, $VPD \ge 0$ | $P=12.4\,\text{mm}$, $T=301.2\,\text{K}$, $VPD=1.84\,\text{kPa}$ | **PASS** |
| **`SOC-08`** | 4-Source Spatial Alignment | Exact $(1, C, 64, 64)$ grid alignment on EPSG:32645 | All 14 channels aligned to exact 10m UTM 45N grid | **PASS** |
| **`SOC-09`** | Central Engine Forward Handshake | Full forward inference latency $\le 1.0\,\text{ms/px}$ | **$0.003117\,\text{ms/px}$** ($320.8\times$ faster than SLA) | **PASS** |
| **`SOC-10`** | Serialized Persistence Integrity | `torch.load` reload test, zero NaNs, schema valid | $988.1\,\text{KB}$ bundle reloaded with 100% fidelity | **PASS** |

---

## 5. "Ek Ek Dhappa" — Brutally Honest Engineering Disclosures & Limitations

1. **Fixed Spatial Windowing Footprint ($640\,\text{m} \times 640\,\text{m}$):**
   - *Dhappa:* The harmonized tensor bundles are strictly formatted into $64 \times 64$ pixel spatial windows.
   - *Compromise:* Larger regional watershed campaigns requiring $1024 \times 1024$ or $2048 \times 2048$ grids cannot load these bundles directly without iterative sliding-window tile tiling. For regional analytics, the pipeline orchestrator must re-assemble tiled patches into a mosaic.

2. **Temporal Asynchrony Between Modalities:**
   - *Dhappa:* Sentinel-1 SAR and Sentinel-2 Optical sensors fly on different orbits and do not acquire imagery simultaneously.
   - *Compromise:* In the harmonized bundle, Sentinel-1 SAR (Day 07) and Sentinel-2 Optical (Day 07) have a typical temporal delta of $\Delta t \approx 12\text{ to }36\,\text{hours}$. While ERA5-Land weather forcing is hourly matched to the SAR overpass timestamp, rapid antecedent rain events occurring between the optical and SAR acquisitions can lead to transient soil moisture mismatches.

3. **Float32 Precision Storage Footprint:**
   - *Dhappa:* All tensor arrays are serialized as standard 32-bit floating point numbers (`torch.float32`).
   - *Compromise:* A single $64 \times 64$ tile with 14 channels requires only $\sim 988\,\text{KB}$, but scaling to full-state provincial monitoring (e.g. 100,000 tiles) would produce $\sim 98.8\,\text{GB}$ of tensor cache. Quantization to `bfloat16` or `int16` scaled integers was deferred to preserve Richards PDE numerical gradients.

---

## 6. Cross-Subsystem Traceability Matrix

| Ingested Component | Source Module | Serialized Location in `2_harmonized_tensors/` | Downstream Consumer |
|:---|:---|:---|:---|
| Calibrated SAR ($\sigma^0$) | `sar_radiometric_calibrator.py` | `s1_s2_dem_era5_harmonized_bundle.pt['sar']` | `3_core_engine/` & `7_production_geotiffs/` |
| Normalized BOA ($ho$) | `optical_cloud_preprocessor.py` | `s1_s2_dem_era5_harmonized_bundle.pt['optical']` | `4_domain_translators/agronomy/` |
| Resampled DEM & TWI | `dem_topography_coupler.py` | `s1_s2_dem_era5_harmonized_bundle.pt['dem']` | `4_domain_translators/civil/` |
| Downscaled Weather | `weather_forcing_coupler.py` | `s1_s2_dem_era5_harmonized_bundle.pt['weather']` | `3_core_engine/physics/richards_1d_pinn.py` |
| `soil_state_output` | `aether_engine.py` | `s1_s2_dem_era5_harmonized_bundle.pt['soil_state_output']` | `6_dashboard/` & Master Monograph |
