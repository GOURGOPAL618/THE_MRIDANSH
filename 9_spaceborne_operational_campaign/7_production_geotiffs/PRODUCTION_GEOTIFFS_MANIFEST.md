# 🛰️ Production GeoTIFF & Cloud-Optimized GeoTIFF (COG) Catalog
## Mission: Spaceborne Operational Campaign (SOC-AETHER-2026) | Subsystem 09
### Repository Location: `9_spaceborne_operational_campaign/7_production_geotiffs/`
### Operational Status: CERTIFIED PRODUCTION GIS DELIVERABLES (TRL-7)

---

## 1. Subsystem Mandate & GIS Deliverables Protocol

The `7_production_geotiffs/` directory contains the production-grade geospatial raster deliverables, multi-band Cloud-Optimized GeoTIFF (COG) stacks, and spatial metadata manifests for the **AETHER-MRID1607X** Earth Observation platform.

Serving as Stage 7 of the Spaceborne Operational Campaign, this subsystem exports calibrated 10m physical soil hydrological, agronomic irrigation, and civil geotechnical rasters formatted strictly to **OGC GeoTIFF 1.1** and **Cloud-Optimized GeoTIFF (COG)** standards for seamless integration into web GIS viewers, QGIS, ArcGIS Pro, and automated farm dispatch machinery.

---

## 2. Multi-Band Master COG Stacks

| Master COG Filename | File Size | Band Count | Dimensions & Resolution | CRS | Primary Role & Layer Semantics | SHA-256 Checksum |
|:---|:---:|:---:|:---:|:---:|:---|:---|
| **`master_unified_soil_state_7layer.tif`** | 54.2 KB | 7 Bands | $64 \times 64$ @ 10m | `EPSG:32645` | Master Central Soil State: $\theta_{L1}, \theta_{L2}, \theta_{L3}, \theta_{L4}$, Matric Suction Head ($h$), Hydraulic Conductivity ($K$), Conformal Uncertainty ($2\sigma_\theta$). | `2a71749044d1...` |
| **`master_agronomic_vri_4layer_10m.tif`** | 31.5 KB | 4 Bands | $64 \times 64$ @ 10m | `EPSG:32645` | Precision Agronomy: CWSI, Root-Zone Depletion ($D_r$), VRI Prescription (L/ha), Conformal Risk Envelope (L/ha). | `9204adab2f4f...` |
| **`master_geotechnical_civil_4layer_10m.tif`** | 29.7 KB | 4 Bands | $64 \times 64$ @ 10m | `EPSG:32645` | Geotechnical Civil: Allowable Bearing Capacity ($q_{\text{allow}}$ with $FS \ge 3.0$), Slope Stability FS, Beven-Kirkby TWI, Off-road Mobility Tier. | `b9129a23080b...` |

---

## 3. Single-Band Production GeoTIFF Rasters

| Single-Band Filename | File Size | Physical Property & Units | Physical Range (Min / Mean / Max) | Description |
|:---|:---:|:---|:---:|:---|
| **`theta_surface_10m.tif`** | 16.1 KB | Volumetric Moisture ($\text{m}^3/\text{m}^3$) | $[0.191, 0.235, 0.280]$ | Surface vadose zone ($0-5\,\text{cm}$) volumetric soil water content. |
| **`theta_rootzone_10m.tif`** | 16.1 KB | Volumetric Moisture ($\text{m}^3/\text{m}^3$) | $[0.191, 0.235, 0.280]$ | Root-zone vadose layer ($5-30\,\text{cm}$) volumetric soil water content. |
| **`pore_pressure_head_10m.tif`** | 16.7 KB | Matric Suction Head ($\text{cm}$) | $[-237.49, -112.50, -63.88]$ | Soil matric suction potential head ($h$). |
| **`hydraulic_conductivity_10m.tif`** | 17.1 KB | Unsaturated Conductivity ($\text{cm/day}$) | $[8.62 \times 10^{-5}, 1.65 \times 10^{-3}, 5.43 \times 10^{-3}]$ | van Genuchten unsaturated hydraulic conductivity $K(\theta)$. |
| **`conformal_uncertainty_2sigma_10m.tif`** | 1.9 KB | Conformal Margin ($\text{m}^3/\text{m}^3$) | $[0.0192, 0.0192, 0.0192]$ | $2\sigma_\theta$ epistemic uncertainty half-width (95% confidence). |
| **`pde_residual_norm_10m.tif`** | 1.9 KB | PDE Mass Residual ($\text{m}^3/\text{m}^3$) | $[0.0015, 0.0015, 0.0015]$ | Discrete Richards unsaturated flow conservation residual norm. |
| **`hydrological_anomaly_flags_10m.tif`** | 1.9 KB | Anomaly Code (Categorical) | $[0.0, 0.0, 20.0]$ | Automated hydrological and sensor anomaly classification flags. |
| **`crop_water_stress_index_10m.tif`** | 2.2 KB | CWSI (Unitless $[0, 1]$) | $[0.000, 0.006, 0.426]$ | FAO-56 Crop Water Stress Index for Winter Wheat / Paddy. |
| **`root_zone_depletion_dr_10m.tif`** | 15.2 KB | Depletion Depth ($\text{mm}$) | $[9.27, 53.50, 128.79]$ | Root-zone water depletion below field capacity ($D_r$). |
| **`precision_irrigation_prescription_liters_per_ha_10m.tif`** | 2.2 KB | Irrigation Rate ($\text{L/ha}$) | $[0.0, 29599.4, 1431035.0]$ | Variable-Rate Irrigation (VRI) water application volume. |
| **`irrigation_conformal_risk_envelope_10m.tif`** | 11.3 KB | Conformal Risk Margin ($\text{L/ha}$) | $[0.0, 219606.9, 828766.5]$ | $2\sigma$ uncertainty dispatch margin for precision irrigation. |
| **`allowable_bearing_capacity_10m.tif`** | 17.2 KB | Bearing Capacity ($\text{kPa}$) | $[553.9, 613.8, 806.0]$ | Safe allowable foundation bearing capacity ($FS \ge 3.0$). |
| **`slope_factor_of_safety_10m.tif`** | 1.8 KB | Safety Factor (Ratio) | $[10.0, 10.0, 10.0]$ | Copernicus DEM-coupled infinite slope stability factor of safety. |
| **`topographic_wetness_index_10m.tif`** | 17.0 KB | TWI Index (Unitless) | $[8.74, 9.38, 10.20]$ | Beven-Kirkby Topographic Wetness Index $\ln(a / \tan\beta)$. |
| **`vehicle_mobility_tier_10m.tif`** | 1.8 KB | Mobility Tier (Code $[0, 3]$) | $[3.0, 3.0, 3.0]$ | NATO / USACE off-road ground trafficability rating (Tier 3 = AllGo). |

---

## 4. Metadata Manifest Files

* **`geotiff_manifest.json`** (4.8 KB): Master production manifest registering the 7-layer COG, bounding boxes, affine transform, CRS, and viewer lock status.
* **`agronomic_geotiff_manifest.json`** (2.2 KB): Agronomic VRI raster catalog registering CWSI, $D_r$, prescription volumes, crop parameters, and SHA-256 hashes.
* **`civil_geotiff_manifest.json`** (2.4 KB): Civil geotechnical catalog registering bearing capacity, factor of safety, vehicle mobility, and Eurocode 7 / IS 1904 compliance.
