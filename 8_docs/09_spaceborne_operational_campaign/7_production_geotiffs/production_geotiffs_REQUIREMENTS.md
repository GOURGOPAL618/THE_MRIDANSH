# Subsystem 09: Spaceborne Operational Campaign — Production GeoTIFF Architecture (`7_production_geotiffs/`)
## Central Unified Engine: AETHER-MRID1607X
### Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
### Author & Lead Systems Engineer: Gourgopal Mohapatra
### Release Status: TRL-7 OPERATIONAL FLIGHT READINESS

---

## 1. Executive Overview & Subsystem Mandate

The `7_production_geotiffs/` subsystem constitutes the official production GIS export interface, multi-band Cloud-Optimized GeoTIFF (COG) generation pipeline, and spatial raster repository for the **AETHER-MRID1607X** Earth Observation platform. Operating as Stage 7 of the Spaceborne Operational Campaign (SOC-AETHER-2026), this layer translates numerical PyTorch tensor bundles into industry-standard, georeferenced, cloud-streamable raster files conforming to **OGC GeoTIFF 1.1** and **Cloud-Optimized GeoTIFF** specifications.

```
+---------------------------------------------------------------------------------------------------------+
|                                    INTERNAL ANALYTICAL TENSORS                                          |
|  • UnifiedSoilState (Core Physics)  • Agronomic VRI Tensors  • Geotechnical Bearing Capacity Tensors    |
+---------------------------------------------------+-----------------------------------------------------+
                                                    |
                                                    v
+---------------------------------------------------------------------------------------------------------+
|                  PRODUCTION RASTER EXPORTER (4_execution_engine/geotiff_production_exporter.py)         |
|  • Geodetic Affine Mapping: Transform [10.0, 0.0, 420000.0, 0.0, -10.0, 2240640.0]                      |
|  • LZW Lossless Predictor Compression (Horizontal Differencing)                                         |
|  • Cloud-Optimized GeoTIFF (COG) Architecture: Internal Tile Blocks (64x64) & Power-of-2 Overviews     |
|  • Active Desktop GIS Lock Detection (_is_file_locked_by_viewer) with Timestamped Fallbacks             |
+---------------------------------------------------+-----------------------------------------------------+
                                                    |
                                                    v
+---------------------------------------------------------------------------------------------------------+
|                      STAGE 7: 9_spaceborne_operational_campaign/7_production_geotiffs/                  |
|                                                                                                         |
|  [Master Multi-Band COG Stacks]                   [Single-Band Decision Layers]                         |
|  • master_unified_soil_state_7layer.tif (7 Bands) • theta_surface_10m.tif & theta_rootzone_10m.tif      |
|  • master_agronomic_vri_4layer_10m.tif  (4 Bands) • pore_pressure_head_10m.tif & hydraulic_cond.tif     |
|  • master_geotechnical_civil_4layer_10m.tif(4 B)  • crop_water_stress_index_10m.tif & rootzone_dep.tif  |
|                                                   • precision_irrigation_prescription_10m.tif           |
|  [Spatial Manifests]                              • allowable_bearing_capacity_10m.tif (FS >= 3.0)      |
|  • geotiff_manifest.json                          • slope_factor_of_safety_10m.tif                      |
|  • agronomic_geotiff_manifest.json                • vehicle_mobility_tier_10m.tif                       |
|  • civil_geotiff_manifest.json                    • topographic_wetness_index_10m.tif                   |
+---------------------------------------------------+-----------------------------------------------------+
                                                    |
                                                    v
+---------------------------------------------------------------------------------------------------------+
|                              DOWNSTREAM CONSUMERS & FIELD TERMINALS                                     |
|  • 6_dashboard/ (Interactive Leaflet Map Viewports & Zonal Extractor)                                   |
|  • Mobile Field Terminals (Kisan Advisory Mobile Webapp)                                                |
|  • Precision Tractor Machinery (ISOBUS Task Controller XML / Shapefile Export)                          |
|  • Desktop GIS Suites (QGIS 3.x, ArcGIS Pro, Google Earth Engine)                                        |
+---------------------------------------------------------------------------------------------------------+
```

---

## 2. Geodetic Projection & Raster Georeferencing Contracts

All exported GeoTIFF rasters adhere strictly to standard spatial parameters:
* **Coordinate Reference System:** Universal Transverse Mercator Zone 45N (`EPSG:32645`)
* **Horizontal Geodetic Datum:** WGS 84
* **Ground Sample Distance (GSD):** $\Delta x = 10.0\,	ext{m}, \Delta y = -10.0\,	ext{m}$ (pixel-is-area convention).
* **Grid Spatial Bounds (Mahanadi Delta AOI):**
  - Easting ($X$): $[420,000.0\,	ext{m}, 420,640.0\,	ext{m}]$
  - Northing ($Y$): $[2,240,000.0\,	ext{m}, 2,240,640.0\,	ext{m}]$
* **GDAL Affine Transform Matrix:**
  $$egin{bmatrix} X_{	ext{geo}} \ Y_{	ext{geo}} \end{bmatrix} = egin{bmatrix} 420000.0 & 10.0 & 0.0 \ 2240640.0 & 0.0 & -10.0 \end{bmatrix} egin{bmatrix} 1 \ j \ i \end{bmatrix}$$
* **NoData Value:** `-9999.0` (IEEE 754 32-bit floating point).
* **Compression Profile:** `COMPRESS=LZW`, `PREDICTOR=2` (Floating Point Horizontal Differencing).

---

## 3. Master Multi-Band Cloud-Optimized GeoTIFF (COG) Specifications

### 3.1 `master_unified_soil_state_7layer.tif` (Central Soil Physics Stack)
This 7-band COG encapsulates the complete physical soil state predicted by the frozen `AETHER-MRID1607X` engine:
* **Band 1 — $	heta_{0-5	ext{cm}}$:** Volumetric moisture layer 1 ($0-5\,	ext{cm}$ surface) in $	ext{m}^3/	ext{m}^3$. Range: $[0.191, 0.280]$.
* **Band 2 — $	heta_{5-15	ext{cm}}$:** Volumetric moisture layer 2 ($5-15\,	ext{cm}$) in $	ext{m}^3/	ext{m}^3$. Range: $[0.191, 0.280]$.
* **Band 3 — $	heta_{15-30	ext{cm}}$:** Volumetric moisture layer 3 ($15-30\,	ext{cm}$) in $	ext{m}^3/	ext{m}^3$. Range: $[0.191, 0.280]$.
* **Band 4 — $	heta_{30-60	ext{cm}}$:** Volumetric moisture layer 4 ($30-60\,	ext{cm}$ deep vadose) in $	ext{m}^3/	ext{m}^3$. Range: $[0.191, 0.280]$.
* **Band 5 — $h$:** Matric suction pressure head in $	ext{cm}$. Range: $[-237.49, -63.88]$.
* **Band 6 — $K$:** Unsaturated hydraulic conductivity in $	ext{cm/day}$. Range: $[8.62 	imes 10^{-5}, 5.43 	imes 10^{-3}]$.
* **Band 7 — $2\sigma_	heta$:** Conformal prediction uncertainty ($2\sigma$) in $	ext{m}^3/	ext{m}^3$. Bound: $0.0192$.

### 3.2 `master_agronomic_vri_4layer_10m.tif` (Precision Irrigation Stack)
* **Band 1 — CWSI:** FAO-56 Crop Water Stress Index ($[0.0, 1.0]$). Mean: $0.0063$, Max: $0.4260$.
* **Band 2 — $D_r$:** Root-zone water depletion below field capacity in $	ext{mm}$. Range: $[9.27, 128.79]\,	ext{mm}$.
* **Band 3 — VRI Prescription:** Variable-Rate Irrigation application rate in $	ext{Liters/Hectare}$. Range: $[0.0, 1,431,035.0]\,	ext{L/ha}$.
* **Band 4 — Conformal Risk Margin:** $2\sigma$ half-width uncertainty envelope in $	ext{Liters/Hectare}$. Mean: $219,606.9\,	ext{L/ha}$.

### 3.3 `master_geotechnical_civil_4layer_10m.tif` (Civil Geotechnical Stack)
* **Band 1 — $q_{	ext{allow}}$:** Allowable foundation bearing capacity in $	ext{kPa}$ with structural safety factor $FS \ge 3.0$. Range: $[553.9, 806.0]\,	ext{kPa}$.
* **Band 2 — Slope FS:** Infinite slope stability factor of safety (Taylor-Duncan method). Nominal value: $10.0$ across flat delta terrain.
* **Band 3 — TWI:** Beven-Kirkby Topographic Wetness Index. Range: $[8.74, 10.20]$.
* **Band 4 — Mobility Tier:** NATO/USACE off-road ground trafficability rating (Categorical Tier 3 = AllGo).

---

## 4. Formal Verification & Testing Scorecard (SOC-21 to SOC-22)

The production GeoTIFF generation is validated via automated Pytest assertions (`tests/test_day11_operational_orchestration.py`).

| Test Identifier | Verification Target | Target Envelope | Measured Outcome | Pass/Fail |
|:---|:---|:---|:---|:---:|
| **`SOC-21`** | GeoTIFF Georeference & Affine Transform | EPSG:32645, 10m pixel size, non-inverted grid | Valid EPSG:32645 CRS, exact affine transform | **PASS** |
| **`SOC-22`** | 7-Layer COG Band Semantics & Zero NaNs | 7 distinct bands, zero NaNs, LZW compression | All 7 bands validated, 0 NaN pixels out of 4,096 | **PASS** |

---

## 5. "Ek Ek Dhappa" — Brutally Honest Engineering Disclosures & Limitations

1. **Windows OS Concurrent File Locking (`PermissionError [Errno 13]`):**
   - *Dhappa:* Desktop GIS software (such as QGIS 3.x or ArcGIS Pro) and Windows Explorer thumbnail renderers place exclusive file-lock handles on open `.tif` files. If a user has `master_unified_soil_state_7layer.tif` open in QGIS, running an automated re-export pipeline immediately crashes with `PermissionError: [Errno 13] Permission denied`.
   - *Compromise:* `GeoTIFFProductionExporter` implements an active `_is_file_locked_by_viewer()` probe. If a lock is detected, the exporter preserves the locked file and writes the new raster to a timestamped fallback path (`_fallback_YYYYMMDD_HHMMSS.tif`), logging a clear warning rather than failing the mission.

2. **Float32 Uncompressed Storage Overhead:**
   - *Dhappa:* Each 10m single-band float32 GeoTIFF requires $\sim 16.5\,	ext{KB}$, and the 7-layer master COG requires $\sim 54.2\,	ext{KB}$ for a single $64 	imes 64$ patch.
   - *Compromise:* While trivial for a 40.96 ha field, scaling to a state-wide mission (e.g. 500,000 tiles) would produce over $27.1\,	ext{GB}$ of raster storage. While LZW compression reduces disk footprint by $\sim 65\%$, converting floating-point moisture into 16-bit scaled unsigned integers (`uint16` with scale factor $0.0001$) was deferred to Phase 7 to prevent truncation of small hydraulic conductivity gradients.

3. **Web Mercator Reprojection Resampling Blur:**
   - *Dhappa:* Production GeoTIFFs are generated natively in UTM Zone 45N (`EPSG:32645`). Leaflet web map viewers require Web Mercator (`EPSG:3857`).
   - *Compromise:* Dynamic on-the-fly browser re-projection from UTM to Web Mercator causes subtle edge-blurring and sub-pixel antialiasing resampling artifacts along sharp agricultural boundary edges.

---

## 6. Cross-Subsystem Traceability Matrix

| Production GeoTIFF File | Generating Module | Mathematical Contract | Downstream Consumer Subsystem |
|:---|:---|:---|:---|
| `master_unified_soil_state_7layer.tif` | `geotiff_production_exporter.py` | 7-Layer Soil State | `6_dashboard/` & Web Viewports |
| `master_agronomic_vri_4layer_10m.tif` | `geotiff_production_exporter.py` | FAO-56 CWSI & VRI | Kisan Advisory Bulletin |
| `master_geotechnical_civil_4layer_10m.tif`| `geotiff_production_exporter.py` | Eurocode 7 $FS \ge 3.0$ | Civil Engineering Infrastructure |
| `geotiff_manifest.json` | `geotiff_production_exporter.py` | SHA-256 Checksums | Root Flight Certification |
