# 🛰️ Harmonized Multi-Sensor Tensor Stacks Manifest & Data Contracts
## Mission: Spaceborne Operational Campaign (SOC-AETHER-2026) | Subsystem 09
### Repository Location: `9_spaceborne_operational_campaign/2_harmonized_tensors/`
### Operational Status: CERTIFIED PRODUCTION TENSOR ARTIFACTS

---

## 1. Subsystem Mandate & Tensor Persistence Contract

The `2_harmonized_tensors/` directory houses the multi-modal, spatial-temporally co-registered, and radiometrically normalized PyTorch tensor bundles feeding the **AETHER-MRID1607X** central processing engine.

These artifacts represent Stage 2 of the Spaceborne Operational Campaign. Raw satellite granules and meteorological rasters from `1_telemetry_raw/` are ingested, filtered, projected to the target UTM coordinate reference system (EPSG:32645), and serialized into deterministic 64x64 spatial patches corresponding to a **640m x 640m ground footprint (40.96 ha)** at 10m native ground sample distance (GSD).

---

## 2. Harmonized Artifact Inventory

| Artifact Filename | File Size | PyTorch Object Structure | Channel Count | Spatial Grid Shape | Primary Role & Included Modalities |
|:---|:---:|:---|:---:|:---:|:---|
| **`s1_s2_harmonized_bundle.pt`** | 166.9 KB | `Dict[str, Any]` | 10 Channels | $(1, C, 64, 64)$ | Dual-satellite baseline stack: Sentinel-1 SAR (2 ch), Sentinel-2 Optical (4 ch), Topography (3 ch), Cloud Mask (1 ch), plus spatial metadata. |
| **`s1_s2_dem_era5_harmonized_bundle.pt`** | 988.1 KB | `Dict[str, Any]` | 14 Channels + Output | $(1, C, 64, 64)$ | Full 4-modality production bundle: SAR (2 ch), Optical (4 ch), DEM (4 ch), Weather (3 ch), Cloud Mask (1 ch), plus serialized `UnifiedSoilState` forward inference state. |
| **`spatial_grid_metadata.json`** | 461 B | JSON Object | N/A | Coordinate Metadata | CRS (EPSG:32645), bounding box, GSD (10m), patch dimensions, SAR speckle ENL metrics, and scene cloud fraction. |

---

## 3. Tensor Schema & Channel Indexing

### 3.1 `s1_s2_dem_era5_harmonized_bundle.pt` Modality Specifications:

```python
{
    # 1. Sentinel-1 SAR Dual-Pol (Calibrated Decibels)
    "sar": torch.Tensor(shape=(1, 2, 64, 64), dtype=torch.float32),
    # Channel 0: VV Backscatter [dB] -> Range: [-25.43 dB, -10.99 dB]
    # Channel 1: VH Backscatter [dB] -> Range: [-29.80 dB, -16.40 dB]

    # 2. Sentinel-2 MSI Optical (BOA Surface Reflectance)
    "optical": torch.Tensor(shape=(1, 4, 64, 64), dtype=torch.float32),
    # Channel 0: Band 02 (Blue, 490 nm)    -> Range: [0.043, 0.465]
    # Channel 1: Band 03 (Green, 560 nm)   -> Range: [0.043, 0.465]
    # Channel 2: Band 04 (Red, 665 nm)     -> Range: [0.043, 0.465]
    # Channel 3: Band 08 (NIR, 842 nm)     -> Range: [0.043, 0.465]

    # 3. Copernicus 30m Global DEM (Resampled Topography)
    "dem": torch.Tensor(shape=(1, 4, 64, 64), dtype=torch.float32),
    # Channel 0: Orthometric Elevation Z [m]           -> Range: [2.16 m, 7.73 m]
    # Channel 1: Surface Slope beta [rad]              -> Range: [0.00 rad, 0.42 rad]
    # Channel 2: Surface Aspect alpha [rad]            -> Range: [0.00 rad, 6.28 rad)
    # Channel 3: Topographic Wetness Index TWI [unitless] -> Range: [4.21, 12.85]

    # 4. ECMWF ERA5-Land Atmospheric Forcing (Downscaled)
    "weather": torch.Tensor(shape=(1, 3, 64, 64), dtype=torch.float32),
    # Channel 0: 24-hr Antecedent Precipitation P [mm/day] -> Range: [0.00 mm, 12.40 mm]
    # Channel 1: 2m Air Temperature T_2m [K / normalised]  -> Range: [298.15 K, 304.50 K]
    # Channel 2: Vapor Pressure Deficit VPD [kPa]          -> Range: [0.12 kPa, 2.15 kPa]

    # 5. Scene Classification Layer Binary Clear-Sky Mask
    "cloud_mask": torch.Tensor(shape=(1, 1, 64, 64), dtype=torch.float32),
    # 1.0 = Valid Clear-Sky / Surface Pixel, 0.0 = Cloud / Shadow Occluded

    # 6. Serialized AETHER-MRID1607X Forward Physics State
    "soil_state_output": {
        "volumetric_moisture": torch.Tensor(shape=(1, 1, 64, 64)),   # theta in [0.191, 0.280] m3/m3
        "pore_pressure_head": torch.Tensor(shape=(1, 1, 64, 64)),    # h in [-237.49, -63.88] cm
        "hydraulic_conductivity": torch.Tensor(shape=(1, 1, 64, 64)),# K in [8.62e-5, 5.43e-3] cm/day
        "conformal_uncertainty": torch.Tensor(shape=(1, 1, 64, 64)), # sigma_theta = 0.0192 m3/m3
        "pde_residual_norm": torch.Tensor(0.0015)                   # Richards PDE Residual Norm
    }
}
```

---

## 4. Geometric & Coordinate Reference System Parameters

* **Projection:** Universal Transverse Mercator (UTM Zone 45N)
* **EPSG Identifier:** `EPSG:32645`
* **Geodetic Datum:** WGS 84
* **Native Ground Sample Distance (GSD):** $10.0\,\text{m} \times 10.0\,\text{m}$
* **Patch Size:** $64 \times 64$ pixels
* **Ground Footprint Area:** $640.0\,\text{m} \times 640.0\,\text{m} = 409,600.0\,\text{m}^2 = 40.96\,\text{ha}$
* **Bounding Box Extents (UTM):**
  - Easting ($X$): $[420,000.0\,\text{m}, 420,640.0\,\text{m}]$
  - Northing ($Y$): $[2,240,000.0\,\text{m}, 2,240,640.0\,\text{m}]$
