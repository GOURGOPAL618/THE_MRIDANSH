# 🛰️ Raw Spaceborne Telemetry Ingestion Manifest & Data Provenance
## Mission: Spaceborne Operational Campaign (SOC-AETHER-2026) | Subsystem 09
### Repository Location: `9_spaceborne_operational_campaign/1_telemetry_raw/`
### Operational Status: ACTIVE PRODUCTION STAGING

---

## 1. Subsystem Mandate & Storage Isolation Policy

The `1_telemetry_raw/` directory serves as the local staging and ingestion cache for raw, multi-modal earth observation payloads feeding the **AETHER-MRID1607X** central processing engine. 

### Why Raw Granules Are Staged Externally from Git Tracking:
* **Payload Footprint:** A single multi-temporal Copernicus acquisition set (Sentinel-1 SAR IW GRD SAFE archive, Sentinel-2 L2A BOA MSI SAFE directory, Copernicus 30m DEM GeoTIFFs, and ECMWF ERA5-Land NetCDF/GRIB files) exceeds **4.8 GB per orbit pass**.
* **Storage Protocol:** Raw binary archives are permanently cataloged and archived in high-throughput object storage (`s3://jcc-rs-sda-telemetry/soc-aether-2026/raw/`) and mirrored onto high-speed NVMe scratch storage (`D:\JAGANNATH_CODE_SANCTUM\DATA_CACHE\1_telemetry_raw\`).
* **Deterministic Reproducibility:** Downstream pipeline execution engines (`4_execution_engine/run_day07_field_telemetry.py` and `run_day08_dem_weather_telemetry.py`) maintain deterministic synthetic telemetry generators parameterized by empirical SAR backscatter curves, optical BOA spectral profiles, Horn's 2nd-order topographic gradients, and Tetens vapor pressure deficit formulations to enable zero-network, 100% reproducible continuous integration test runs.

---

## 2. Ingested Spaceborne Sensor Modalities

| Modality Identifier | Spaceborne Platform | Sensor Payload | Operational Product Level | Native Resolution | Polarization / Bands / Metrics | Temporal Cadence |
|:---|:---|:---|:---|:---|:---|:---|
| **`TEL-SAR-01`** | Sentinel-1A / 1B | C-Band SAR (5.405 GHz) | Level-1 Ground Range Detected (IW GRD) | 10m Ground Sample Distance | Dual-pol: $VV$, $VH$ intensity & amplitude | 6 to 12 days repeat |
| **`TEL-OPT-02`** | Sentinel-2A / 2B | MultiSpectral Instrument (MSI) | Level-2A Bottom-of-Atmosphere (BOA) | 10m native (VNIR), 20m (SCL) | $B_2$ (Blue), $B_3$ (Green), $B_4$ (Red), $B_8$ (NIR) + SCL (Scene Classification Layer) | 5 days (constellation) |
| **`TEL-DEM-03`** | TanDEM-X / Copernicus GLO-30 | Radar Interferometry (X-band) | 30m Global DEM (GLO-30 Tile) | 30m spatial grid | Orthometric Elevation ($Z$ in meters above EGM2008 geoid) | Static baseline |
| **`TEL-MET-04`** | ECMWF Reanalysis v5 | Atmospheric Circulation Reanalysis | ERA5-Land Hourly Surface Grids | $0.1^\circ \times 0.1^\circ$ (~9 km) | 2m Temp ($T_{2\text{m}}$), 24h Precip ($P_{24\text{h}}$), Dewpoint ($T_d$), Surface Pressure ($P_s$) | Hourly / 24-hr aggregates |

---

## 3. Directory Layout & Local Ingestion Staging

```
9_spaceborne_operational_campaign/1_telemetry_raw/
├── RAW_TELEMETRY_MANIFEST.md        ➔ Master data provenance, sensor parameters & staging guide
├── .gitkeep                         ➔ Preserves folder structure in version control
└── [LOCAL_STAGING_STORAGE]          ➔ Symlinked or copied during operational runs:
    ├── S1A_IW_GRDH_1SDV_20261015T...SAFE/
    │   ├── manifest.safe
    │   ├── measurement/
    │   │   ├── s1a-iw-grd-vv-20261015...tiff
    │   │   └── s1a-iw-grd-vh-20261015...tiff
    │   └── annotation/calibration/
    │       └── calibration-s1a-iw-grd-vv-20261015...xml
    ├── S2A_MSIL2A_20261015T...SAFE/
    │   ├── GRANULE/L2A_.../IMG_DATA/R10m/
    │   │   ├── T45N_20261015..._B02_10m.jp2
    │   │   ├── T45N_20261015..._B03_10m.jp2
    │   │   ├── T45N_20261015..._B04_10m.jp2
    │   │   └── T45N_20261015..._B08_10m.jp2
    │   └── GRANULE/L2A_.../IMG_DATA/R20m/
    │       └── T45N_20261015..._SCL_20m.jp2
    ├── Copernicus_DSM_COG_10_N20_00_E085_00_DEM.tif
    └── ERA5_LAND_HOURLY_20261015_COASTAL_DELTA.nc
```

---

## 4. Radiometric Calibration & Scaling Standards

### 4.1 Sentinel-1 SAR Calibration ($DN \to \sigma^0$):
$$\sigma^0 (\text{linear}) = \frac{DN^2}{A_{\sigma}^2}$$
$$\sigma^0 (\text{dB}) = 10 \cdot \log_{10}(\sigma^0 (\text{linear}) + 10^{-7})$$
* Clamped strictly to physical backscatter boundaries: $[-35.0\,\text{dB}, +5.0\,\text{dB}]$.

### 4.2 Sentinel-2 Optical BOA Normalization ($DN \to \rho$):
$$\rho_\lambda = \frac{DN_\lambda + \text{BOA\_ADD\_OFFSET}}{10000.0} \in [0.0, 1.0]$$
* SCL Cloud Filter: Clear sky valid pixels extracted when $SCL \in \{2, 4, 5, 6, 7\}$.

### 4.3 Copernicus DEM Topographic Resampling:
* Bilinear downsampling from 30m to exact 10m UTM Zone 45N grid matching Sentinel rasters.
* 2nd-order Horn convolution kernels compute local surface slope $\beta$ and aspect $\alpha$.

### 4.4 ERA5-Land Microclimate Lapse-Rate Correction:
$$T_{2\text{m, corrected}} = T_{2\text{m, coarse}} - \Gamma \cdot (Z_{\text{DEM, 10m}} - Z_{\text{ERA5, coarse}})$$
* Environmental adiabatic lapse rate: $\Gamma = 0.0065\,\text{K/m}$.
* Tetens formulation computes saturation vapor pressure and Vapor Pressure Deficit ($VPD$).
