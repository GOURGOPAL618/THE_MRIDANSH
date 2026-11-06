# Subsystem 05: Master Cloud-Optimized GeoTIFF (COG) Storage Specification
## Central Engine: AETHER-MRID1607X
### Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
### Author & Lead Architect: Gourgopal Mohapatra
### Release Status: FROZEN_OPERATIONAL_RELEASE_v1.0

---

## 1. Executive Overview & Subsystem Mandate

The `5_storage/master_cogs/` repository serves as the definitive spaceborne raster delivery and production persistence hub for the **AETHER-MRID1607X** earth observation platform. Operating as the terminal serialization sink of the unified monolithic orchestrator (`5_pipelines/mridansh_unified_orchestrator.py`), this subsystem converts contiguous in-memory tensor representations into standards-compliant Cloud-Optimized GeoTIFFs (COGs).

The primary architectural mandate is to export multi-domain spatial intelligence across a standardized 10-meter spatial mesh in **UTM Zone 45N (`EPSG:32645`)** covering the 40.96-hectare Kendrapara flight campaign footprint, enabling:
1. **Low-Latency Streaming:** Sub-block HTTP range querying for Web GIS and Mission Cockpit viewports (`6_dashboard`).
2. **Multi-Domain Data Coherence:** Zero-divergence spatial registration across physical soil moisture stratigraphy, precision agronomy VRI, and geotechnical foundation stability.
3. **Cryptographic Flight Provenance:** Bit-level validation governed by `unified_execution_manifest.json` under immutable SHA-256 digital signatures.

```
       +-------------------------------------------------------------+
       |         UNIFIED PIPELINE IN-MEMORY TENSOR OUTPUTS           |
       |             (5_pipelines/mridansh_unified_orchestrator.py)  |
       +------------------------------+------------------------------+
                                      |
                      [Production GeoTIFF Exporter Engine]
                                      |
         +----------------------------+----------------------------+
         |                            |                            |
         v                            v                            v
+-----------------------+   +-----------------------+   +-----------------------+
| master_unified_       |   | master_agronomy_      |   | master_civil_         |
| soil_state.tif        |   | vri.tif               |   | geotech.tif           |
| (3-Band Vadose Stack) |   | (4-Band Precision VRI)|   | (4-Band Geotechnical) |
+-----------+-----------+   +-----------+-----------+   +-----------+-----------+
            |                           |                           |
            +---------------------------+---------------------------+
                                        |
                                        v
                    +---------------------------------------+
                    |    unified_execution_manifest.json    |
                    |    (Spatial Metadata & SHA-256 Lock)  |
                    +---------------------------------------+
```

---

## 2. Master Raster Inventory & Geographic Grid Parameters

All rasters in `5_storage/master_cogs/` share an identical spatial reference system, geographic bounding box, and pixel grid geometry:

* **Coordinate Reference System (CRS):** Universal Transverse Mercator (UTM) Zone 45N (`EPSG:32645`), WGS 84 Datum.
* **Spatial Resolution:** $10.0\ \text{m} \times 10.0\ \text{m}$ per pixel.
* **Grid Dimensions:** $64 \times 64$ pixels ($40.96\ \text{hectares} / 0.4096\ \text{km}^2$).
* **Spatial Bounding Box (UTM Meters):**
  * West ($X_{\min}$): $420000.00\ \text{m}$
  * East ($X_{\max}$): $420640.00\ \text{m}$
  * South ($Y_{\min}$): $2240000.00\ \text{m}$
  * North ($Y_{\max}$): $2240640.00\ \text{m}$
* **Affine Transform Matrix:**
  $$\begin{bmatrix} X \\ Y \\ 1 \end{bmatrix} = \begin{bmatrix} 10.0 & 0.0 & 420000.0 \\ 0.0 & -10.0 & 2240640.0 \\ 0.0 & 0.0 & 1.0 \end{bmatrix} \begin{bmatrix} \text{col} \\ \text{row} \\ 1 \end{bmatrix}$$
* **Compression & Tiling:** LZW lossless compression, $32 \times 32$ internal block tiling (`tiled=True`), pixel interleaved.
* **NoData Value:** `-9999.0` (32-bit floating point).

### Inventory Table:

| Raster Filename | Bands | Size (Bytes) | SHA-256 Cryptographic Hash | Primary Analytical Domain |
|:---|:---:|:---:|:---|:---|
| **`master_unified_soil_state.tif`** | 3 | 51,771 | `a23b5414cc9fa5e0fab8511b05e51d3d373a80f552073c41bcc87a3fdd3369cf` | Physics & Richards Vadose Stratigraphy |
| **`master_agronomy_vri.tif`** | 4 | 71,882 | `adafc22089a54b424072ef5d1881371716b3fc88837f75395ba0a151627c3ed9` | Precision Agriculture & Irrigation Deficit |
| **`master_civil_geotech.tif`** | 4 | 37,729 | `9d4d6385b1cc50220b8b5bd137f49c18d770e8af10523947c93dbd8f9f2f2505` | Geotechnical Foundation & Terramechanics |
| **`unified_execution_manifest.json`** | N/A | 1,038 | `d2220cff1d519cd545569c4ae0581a9ecee04f2b536773ba3d10c21217de1bcf` | Master Provenance & Cross-Layer Metadata |

---

## 3. Band Allocations, Physical Units & Empirical Statistics

### 3.1 `master_unified_soil_state.tif` (3-Layer Vadose Stratigraphy)
Stores continuous volumetric soil moisture content $\theta(z)$ across three depth horizons calibrated against Richards PDE solutions and EnKF state assimilation:

| Band | Channel Identifier | Depth Horizon | Physical Units | Min | Max | Mean | Physical Interpretation |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **1** | `Theta_Surface_0_5cm` | $0 - 5\ \text{cm}$ | $\text{m}^3/\text{m}^3$ | 0.1657 | 0.2474 | 0.2105 | Optical/SAR skin coupling layer; highly responsive to diurnality and evaporative flux. |
| **2** | `Theta_Rootzone_5_30cm` | $5 - 30\ \text{cm}$ | $\text{m}^3/\text{m}^3$ | 0.1907 | 0.2724 | 0.2355 | Active root-zone reservoir; governs crop transpiration and root water extraction. |
| **3** | `Theta_Deep_30_100cm` | $30 - 100\ \text{cm}$ | $\text{m}^3/\text{m}^3$ | 0.2107 | 0.2924 | 0.2555 | Deep subbase percolation horizon; buffered drainage boundary. |

### 3.2 `master_agronomy_vri.tif` (4-Band Precision Agronomy)
Translates surface-root moisture states and optical multispectral telemetry into variable rate irrigation (VRI) prescriptions:

| Band | Channel Identifier | Physical Units | Min | Max | Mean | Analytical Formulation |
|:---:|:---|:---:|:---:|:---:|:---:|:---|
| **1** | `NDVI` | Dimensionless $[-1, 1]$ | 0.2052 | 0.7782 | 0.4781 | $\text{NDVI} = \frac{B_8 - B_4}{B_8 + B_4}$ (Canopy density proxy) |
| **2** | `CWSI` | Index $[0, 1]$ | 0.1101 | 0.6204 | 0.3404 | Crop Water Stress Index; $CWSI = 1 - \frac{ET_a}{ET_c}$ |
| **3** | `Root_Depletion_Dr_mm` | Millimeters ($\text{mm}$) | 7.0641 | 57.0070 | 26.6600 | Volumetric root-zone moisture deficit relative to field capacity ($FC$). |
| **4** | `Transpiration_Deficit_mm_day` | $\text{mm}/\text{day}$ | 0.5254 | 3.0675 | 1.6856 | Daily evapotranspirative loss requiring irrigation replacement. |

### 3.3 `master_civil_geotech.tif` (4-Band Civil Geotechnical & Terramechanics)
Translates soil saturation into unsaturated soil mechanics and off-road tractor trafficability metrics:

| Band | Channel Identifier | Physical Units | Min | Max | Mean | Engineering Formulation |
|:---:|:---|:---:|:---:|:---:|:---:|:---|
| **1** | `Apparent_Cohesion_kPa` | Kilopascals ($\text{kPa}$) | 18.4542 | 28.7478 | 21.3713 | Fredlund unsaturated shear strength enhancement: $c(\theta) = c' + (u_a - u_w) \tan \phi^b$. |
| **2** | `Allowable_Bearing_q_allow_kPa` | Kilopascals ($\text{kPa}$) | 360.5430 | 544.2364 | 412.5997 | Meyerhof general bearing capacity with mandatory safety factor $FS=3.0$: $q_{\text{allow}} = q_{\text{ult}} / 3.0$. |
| **3** | `Factor_of_Safety_Slope` | Ratio $[-]$ | 10.0000 | 10.0000 | 10.0000 | Taylor-Duncan infinite slope factor of safety (clamped to 10.0 on flat alluvial plains). |
| **4** | `Tractor_Rut_Depth_cm` | Centimeters ($\text{cm}$) | 1.5000 | 1.5000 | 1.5000 | Bekker terramechanics mud sinkage: $z_{\text{rut}} = \left(\frac{W / A}{k_c/b + k_\phi}\right)^{1/n}$. |

---

## 4. Brutal Engineering Disclosures & Implementation Flaws

In alignment with institutional engineering transparency guidelines, the following architectural shortcuts, raster constraints, and physical caveats are formally disclosed:

1. **Flat-Ground Slope Stability Singularity Clamp:**
   * *Observation:* Band 3 (`Factor_of_Safety_Slope`) has an identical value ($FS = 10.0000$) across all 4,096 pixels.
   * *Root Cause:* The Kendrapara flight scene consists of flat coastal plain alluvium with slope angle $\beta \approx 0.0^{\circ}$. In infinite slope equations, $\sin \beta \to 0$ in the denominator induces a mathematical divide-by-zero singularity. The engine clamps flat pixels to a hardcoded ceiling of $FS = 10.0$.
   * *Impact:* Slope risk maps cannot differentiate stability variations in terrain flatter than $1.0^{\circ}$.
2. **Uniform Terramechanics Soil Lithology:**
   * *Observation:* Band 4 (`Tractor_Rut_Depth_cm`) reports a constant $1.5000\ \text{cm}$ across the entire scene.
   * *Root Cause:* Bekker soil parameters ($k_c, k_\phi, n$) were held spatially homogeneous assuming uniform Loam clay-silt matrix across the 40.96-ha zone. Real-world localized soil heterogeneity (e.g., bund sand pockets) is not yet spatially modeled.
3. **Internal Tile Size vs. Scene Dimension Mismatch:**
   * *Observation:* Internal blocks are configured as $32 \times 32$ pixels, resulting in exactly $2 \times 2 = 4$ tiles per band.
   * *Limitation:* For a compact $64 \times 64$ raster (51 KB), Cloud-Optimized GeoTIFF HTTP byte-range querying provides negligible performance benefits over flat GeoTIFFs, introducing 4–8 KB of unnecessary TIFF directory and header overhead. However, it preserves architectural consistency for regional scaling.
4. **Projected CRS vs. Web Mercator Reprojection Latency:**
   * *Observation:* Rasters are natively projected in UTM Zone 45N (`EPSG:32645`).
   * *Client Impact:* Leaflet and Folium dashboard renderers operating in Spherical Mercator (`EPSG:3857`) must reproject raster tiles on the fly or warp them during ingestion, which introduces minor client-side sub-pixel antialiasing artifacts.

---

## 5. Traceable Requirements Matrix

| Requirement ID | Verification Type | Specification Bound / Success Metric | Compliance Status |
|:---|:---:|:---|:---:|
| **REQ-STOR-COG-01** | Geometry | All rasters must strictly align to UTM Zone 45N (`EPSG:32645`) with $10.0\text{m}$ cell size. | **VERIFIED** |
| **REQ-STOR-COG-02** | Metadata | `unified_execution_manifest.json` must record verified SHA-256 signatures for all exported rasters. | **VERIFIED** |
| **REQ-STOR-COG-03** | Format | GeoTIFFs must feature internal tiling ($32 \times 32$), LZW compression, and floating-point nodata. | **VERIFIED** |
| **REQ-STOR-COG-04** | Bounds Check | Moisture values in `master_unified_soil_state.tif` must remain physically bounded $\theta \in [\theta_r, \theta_s]$. | **VERIFIED** |
| **REQ-STOR-COG-05** | Integrity | Singularity protection must prevent `NaN` or `Inf` in geotechnical bearing and slope safety layers. | **VERIFIED** |
| **REQ-STOR-COG-06** | Channel Naming | Every raster band must possess an explicit ASCII descriptive tag (e.g. `Theta_Surface_0_5cm`). | **VERIFIED** (11/11 bands) |
| **REQ-STOR-COG-07** | Pipeline Latency | Monolithic production raster export must complete in $< 100\ \text{ms}$ total execution time. | **VERIFIED** (25.99 ms) |
