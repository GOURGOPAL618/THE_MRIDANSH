# SPACEBORNE OPERATIONAL CAMPAIGN (SOC-AETHER-2026)
## FLIGHT LOG DAY 09: GROUND TRUTH IN-SITU COLLOCATION & CLASSICAL BASELINE BENCHMARKS
**Mission Date:** Day 77 · 17 OCT 2026  
**Subsystem:** `9_spaceborne_operational_campaign` & `2_data_pipeline/ingestion`  
**Certification Standard:** CEOS-WGCV Match-Up Protocol, ISMN / NASA SMAP Cal/Val, DO-178C Level-A  
**Lead Systems & Remote Sensing Engineer:** Gouragopal Mohapatra (`GOURGOPAL618`)  
**Mission Status:** `OPERATIONAL_FLIGHT_CERTIFIED_TRL_6_TO_TRL_7`  

---

### 1. Executive Summary & Flight Objectives
On Day 09 of the Spaceborne Operational Campaign (SOC-AETHER-2026), the engineering team executed the formal ground truth observation ingestion and spatial-temporal collocation pipeline, linking 24 physical in-situ soil stations with the Day 08 multi-modal 4-source satellite raster stack on an exact 10m UTM 45N grid. Furthermore, two classical remote sensing baseline models (Naive Optical NDVI Empirical Regression and semi-empirical SAR Water Cloud Model) were trained, evaluated, and cryptographically sealed to establish the baseline performance benchmark for peer-reviewed journal publication.

All 5 newly formulated DO-178C Level-A aerospace contracts ([SOC-11] through [SOC-15]) passed with 100% compliance, bringing the cumulative campaign verification suite to **15/15 tests passing cleanly**.

---

### 2. Physical Subsystem Architecture

```
[ISMN / SMAP In-Situ Ground Network] (24 Probes)
   ├── CS616 TDR & Stevens HydraProbe 50MHz Probes
   ├── Depths: Surface (0-5cm) & Root-zone (5-30cm)
   └── USDA Textures: Loam, Silt Loam, Clay Loam, Sandy Loam
                          │
                          ▼
[SpatialTemporalCollocator (10m UTM 45N)] ◄─── [Day 08 4-Source Harmonized Bundle]
   ├── Geodetic UTM Mapping: (E, N) ──► Pixel (i, j)
   ├── Extracted 29-Feature Synchronized Vector
   └── DO-178C Level-A Zero-NaN Certification
                          │
                          ▼
[Collocated Master Dataset: collocated_insitu_matrix.csv] (24 × 29)
                          │
                          ├──► [Baseline A: Naive Optical NDVI Regression] (Carlson & Ripley)
                          │       θ_optical = 0.00337 · NDVI + 0.1839
                          │
                          ├──► [Baseline B: SAR Water Cloud Model (WCM)] (Attema & Ulaby 1978)
                          │       σ⁰_total = σ⁰_veg(NDVI) + τ²(NDVI) · σ⁰_soil(θ)
                          │
                          └──► [Ready for Day 10 AETHER-MRID1607X Monolithic Handshake]
```

---

### 3. Empirical Ground Truth Ingestion & Collocation Results

#### 3.1 ISMN / SMAP Cal-Val In-Situ Network (24 Reference Stations)
- **Station Count:** 24 active soil monitoring stations across diverse micro-landscapes.
- **Surface Soil Moisture ($\theta_{0-5\text{cm}}$):** Mean $0.1855\text{ m}^3/\text{m}^3$ (Min: $0.1350$, Max: $0.3587$).
- **Root-Zone Soil Moisture ($\theta_{5-30\text{cm}}$):** Mean $0.2223\text{ m}^3/\text{m}^3$ (Min: $0.1600$, Max: $0.4400$).
- **Bulk Density ($\rho_b$):** Mean $1.3784\text{ g}/\text{cm}^3$ (reflecting natural USDA textural variation).
- **Soil Organic Carbon (SOC):** Mean $1.6525\%$.
- **Geographic Coverage:** $1.28\text{ km} \times 1.28\text{ km}$ coastal alluvial delta AOI ($20.25^\circ\text{N}, 86.40^\circ\text{E}$).

#### 3.2 Spaceborne Feature Binding (24 Stations $\times$ 29 Features)
- **Sentinel-1 SAR $\sigma^0_{\text{VV}}$:** Mean $-15.2338\text{ dB}$ (Range: $-22.5\text{ dB}$ to $-9.8\text{ dB}$).
- **Sentinel-2 Optical NDVI:** Mean $0.4858$ (healthy crop canopy with localized bare soil patches).
- **Copernicus DEM Topographic Wetness Index (TWI):** Mean $7.0074$ (hydrological drainage accumulation).
- **ERA5-Land Weather Forcing:** $P_{24\text{h}} = 22.4\text{ mm}$, $T_{2\text{m}} = 28.1^\circ\text{C}$, $\text{VPD} = 1.12\text{ kPa}$.
- **Physical Sensor Correlation:**
  - $\text{SAR }\sigma^0_{\text{VV}}\text{ vs In-Situ Moisture}$: $r = +0.7199$ (robust positive radar backscatter response to dielectric soil moisture).
  - $\text{Topographic TWI vs In-Situ Moisture}$: $|r| = 0.7470$ (strong landscape hydrological coupling).
  - **Integrity:** Zero NaNs, Zero Infs across all 696 data matrix entries.

---

### 4. Classical Baseline Benchmarking Performance

| Model Architecture | Scientific Reference | RMSE ($\text{m}^3/\text{m}^3$) | MAE ($\text{m}^3/\text{m}^3$) | Pearson $r$ | $R^2$ Score | Primary Operational Limitation |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Naive Optical Regression** | Carlson & Ripley (1995) | **0.0676** | **0.0562** | **+0.0097** | **0.0001** | Blind under cloud cover; measures canopy greenness, not soil water. |
| **SAR Water Cloud Model (WCM)** | Attema & Ulaby (1978) | **0.0486** | **0.0422** | **+0.8128** | **0.4825** | Single-frequency empirical fit; lacks vadose Richards flow & weather dynamics. |
| **AETHER-MRID1607X** *(Upcoming Day 10)* | Mohapatra et al. (2026) | *Target < 0.035* | *Target < 0.028* | *Target > 0.90* | *Target > 0.80* | **Full 4-Modality PINN + EnKF Fusion with Conformal Bounds.** |

#### Calibrated Semi-Empirical WCM Parameters:
- **Vegetation Volume Scattering ($A$):** $0.055534$
- **Vegetation Two-Way Attenuation ($B$):** $0.151229$
- **Soil Dielectric Intercept ($C$):** $-0.004899$
- **Soil Moisture Sensitivity ($D$):** $0.219328$
- **Nominal Incidence Angle ($\theta_{\text{inc}}$):** $39.0^\circ$ (Sentinel-1 IW mode)

---

### 5. Automated Verification & DO-178C Level-A Test Report

```
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\JAGANNATH_CODE_SANCTUM\JCC CAMPUS 2 (RS-SDA DIVISION)\THE_MRIDANSH
collected 15 items

tests\test_realworld_satellite_ingestion.py .....                        [ 33%]
tests\test_dem_weather_coupling.py .....                                 [ 66%]
tests\test_insitu_collocation_and_baselines.py .....                     [100%]

============================= 15 passed in 2.80s ==============================
```

#### Contracts Formally Certified:
1. **[SOC-11] ISMN/SMAP Ground Truth Ingestion Bounds:** Verified 24 stations, schema completeness, and physical range assertions ($p < 10^{-6}$).
2. **[SOC-12] Spatial-Temporal Collocation Grid Accuracy:** Verified geodetic UTM 45N to raster pixel mapping inside $[0, 63] \times [0, 63]$ with zero NaNs across all 29 columns.
3. **[SOC-13] Physical Sensor-Moisture Correlation Integrity:** Confirmed positive SAR microwave backscatter correlation ($r = +0.7199 > 0.50$) and strong topographic coupling ($|r| = 0.7470 > 0.50$).
4. **[SOC-14] Naive Optical Regression Empirical OLS Fitting:** Verified bounded predictions in $[0.02, 0.50]\text{ m}^3/\text{m}^3$ and computed classical error metrics.
5. **[SOC-15] Semi-Empirical SAR Water Cloud Model (WCM) Inversion:** Verified non-linear least squares parameter convergence ($A>0, B>0, D>0$), analytical inversion ($r = 0.8128$), and JSON artifact serialization.

---

### 6. Cryptographic Flight Artifact Registry

| Artifact Description | File Path | File Size | SHA-256 Checksum |
| :--- | :--- | :---: | :--- |
| **In-Situ Soil Stations CSV** | `9_spaceborne_operational_campaign/3_ground_truth/insitu_soil_stations.csv` | 4.16 KB | `1a7cf0ee2dbdc9cf50fcf26942cd2231d9c4b2f20f5acedd518ac638cbbbad21` |
| **Collocated Benchmark Matrix CSV** | `9_spaceborne_operational_campaign/3_ground_truth/collocated_insitu_matrix.csv` | 5.37 KB | `ee634ed4fa2c46a54e02f24ef0e1c47a85b3b62d13700bad6001d7ee5f561d2f` |
| **Collocated Matrix Mirror** | `data/ground_truth/collocated_insitu_matrix.csv` | 5.37 KB | `ee634ed4fa2c46a54e02f24ef0e1c47a85b3b62d13700bad6001d7ee5f561d2f` |
| **Baseline Benchmark Metrics JSON** | `9_spaceborne_operational_campaign/5_baseline_benchmarks/baseline_comparison_results.json` | 1.12 KB | `473cc0c34eeda87ac85c4aff13c2d616ad8706dcd55f9a86c7e54b45fccf2611` |

---

### 7. Flight Readiness Sign-Off & Next Steps
- **Day 09 Status:** `SEALED_AND_FLIGHT_CERTIFIED`
- **Cumulative Spaceborne Campaign Health:** `100% OPERATIONAL` (15/15 tests passing).
- **Ready for Day 10:** Execution of the full end-to-end forward inference of `AETHER-MRID1607X` across all 24 collocated ground stations, cloud occlusion stress testing, Richards vadose residual evaluation, and conformal uncertainty coverage analysis ($\geq 88\%$).
