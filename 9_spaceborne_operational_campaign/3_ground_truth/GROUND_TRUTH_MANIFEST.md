# 🛰️ In-Situ Ground Truth Soil Observation Network & Collocation Manifest
## Mission: Spaceborne Operational Campaign (SOC-AETHER-2026) | Subsystem 09
### Repository Location: `9_spaceborne_operational_campaign/3_ground_truth/`
### Operational Status: CALIBRATION & VALIDATION (CAL/VAL) REFERENCE BENCHMARK

---

## 1. Subsystem Mandate & Cal/Val Protocol

The `3_ground_truth/` directory stores the empirical in-situ soil moisture observations, spatial-temporal collocation matrices, and model comparison records for the **AETHER-MRID1607X** Earth Observation framework.

Serving as Stage 3 of the Spaceborne Operational Campaign, this subsystem establishes the physical truth baseline against which spaceborne SAR, Optical, Topographic, and Meteorological estimates are calibrated and validated. The network architecture adheres strictly to:
* **CEOS-WGCV Match-Up Protocol:** Committee on Earth Observation Satellites Working Group on Calibration and Validation guidelines for land surface variables.
* **ISMN Quality Assurance:** International Soil Moisture Network quality control flag taxonomy (`G` = Good, `M` = Dubious, `B` = Bad).
* **NASA SMAP Cal/Val Standards:** Core validation site spatial sampling criteria and dual-depth probe installation protocols.

---

## 2. In-Situ Station Network Inventory

The network comprises 24 high-precision in-situ soil hydrological stations deployed across a $1.28\,\text{km} \times 1.28\,\text{km}$ coastal alluvial delta domain ($20.2505^\circ\text{N} - 20.2610^\circ\text{N}, 86.4006^\circ\text{E} - 86.4117^\circ\text{E}$) in Odisha, India:

| Station ID | Latitude ($^\circ$) | Longitude ($^\circ$) | UTM Easting ($m$) | UTM Northing ($m$) | Elevation ($m$) | USDA Texture | Probe Type | Surface Moisture ($\text{m}^3/\text{m}^3$) | Rootzone Moisture ($\text{m}^3/\text{m}^3$) | Bulk Density ($\text{g/cm}^3$) | SOC (\%) |
|:---|:---:|:---:|:---:|:---:|:---:|:---|:---|:---:|:---:|:---:|:---:|
| `ISMN_DLT_001` | 20.250742 | 86.400978 | 437102.16 | 2239082.57 | 26.18 | Loam | Campbell CS616 TDR | 0.1350 | 0.1724 | 1.384 | 1.90 |
| `ISMN_DLT_002` | 20.250916 | 86.403497 | 437365.24 | 2239101.94 | 29.81 | Silt Loam | Stevens HydraProbe 50MHz | 0.1350 | 0.1600 | 1.322 | 1.60 |
| `ISMN_DLT_003` | 20.250554 | 86.406117 | 437638.86 | 2239061.68 | 30.64 | Clay Loam | Campbell CS616 TDR | 0.1350 | 0.1615 | 1.314 | 2.39 |
| `ISMN_DLT_004` | 20.250780 | 86.408716 | 437910.29 | 2239086.83 | 32.77 | Sandy Loam | Stevens HydraProbe 50MHz | 0.1350 | 0.1673 | 1.503 | 0.91 |
| `ISMN_DLT_005` | 20.250594 | 86.411441 | 438194.93 | 2239066.17 | 32.92 | Loam | Campbell CS616 TDR | 0.1350 | 0.1783 | 1.378 | 1.96 |
| `ISMN_DLT_006` | 20.253305 | 86.400712 | 437074.38 | 2239367.89 | 25.65 | Silt Loam | Stevens HydraProbe 50MHz | 0.1368 | 0.1822 | 1.329 | 1.21 |
| `ISMN_DLT_007` | 20.253247 | 86.403494 | 437364.90 | 2239361.48 | 37.85 | Clay Loam | Campbell CS616 TDR | 0.1350 | 0.1600 | 1.252 | 2.69 |
| `ISMN_DLT_008` | 20.253221 | 86.406197 | 437647.17 | 2239358.56 | 43.36 | Sandy Loam | Stevens HydraProbe 50MHz | 0.1350 | 0.1619 | 1.520 | 0.80 |
| `ISMN_DLT_009` | 20.253354 | 86.408992 | 437939.11 | 2239373.36 | 41.10 | Loam | Campbell CS616 TDR | 0.1350 | 0.1726 | 1.360 | 1.92 |
| `ISMN_DLT_010` | 20.253281 | 86.411581 | 438209.52 | 2239365.20 | 32.59 | Silt Loam | Stevens HydraProbe 50MHz | 0.1350 | 0.1600 | 1.414 | 1.22 |
| `ISMN_DLT_011` | 20.255580 | 86.400843 | 437088.09 | 2239621.21 | 26.82 | Clay Loam | Campbell CS616 TDR | 0.1575 | 0.2045 | 1.311 | 2.62 |
| `ISMN_DLT_012` | 20.255682 | 86.403683 | 437384.70 | 2239632.49 | 46.31 | Sandy Loam | Stevens HydraProbe 50MHz | 0.1551 | 0.2014 | 1.500 | 0.93 |
| `ISMN_DLT_013` | 20.255733 | 86.406191 | 437646.60 | 2239638.22 | 53.80 | Loam | Campbell CS616 TDR | 0.1645 | 0.2058 | 1.355 | 1.69 |
| `ISMN_DLT_014` | 20.255897 | 86.409016 | 437941.60 | 2239656.43 | 48.19 | Silt Loam | Stevens HydraProbe 50MHz | 0.1575 | 0.1934 | 1.387 | 1.50 |
| `ISMN_DLT_015` | 20.255538 | 86.411677 | 438219.49 | 2239616.44 | 31.98 | Clay Loam | Campbell CS616 TDR | 0.1577 | 0.2075 | 1.271 | 2.56 |
| `ISMN_DLT_016` | 20.258461 | 86.400620 | 437064.80 | 2239941.85 | 25.10 | Sandy Loam | Stevens HydraProbe 50MHz | 0.1696 | 0.2196 | 1.473 | 1.20 |
| `ISMN_DLT_017` | 20.258097 | 86.403613 | 437377.36 | 2239901.40 | 51.55 | Loam | Campbell CS616 TDR | 0.2627 | 0.3047 | 1.419 | 1.32 |
| `ISMN_DLT_018` | 20.258240 | 86.406071 | 437634.01 | 2239917.22 | 61.21 | Silt Loam | Stevens HydraProbe 50MHz | 0.2786 | 0.3163 | 1.314 | 1.92 |
| `ISMN_DLT_019` | 20.258367 | 86.408908 | 437930.39 | 2239931.37 | 53.80 | Clay Loam | Campbell CS616 TDR | 0.2629 | 0.2997 | 1.237 | 2.35 |
| `ISMN_DLT_020` | 20.258040 | 86.411719 | 438223.94 | 2239895.05 | 31.53 | Sandy Loam | Stevens HydraProbe 50MHz | 0.1649 | 0.1874 | 1.504 | 1.04 |
| `ISMN_DLT_021` | 20.260592 | 86.400878 | 437091.69 | 2240179.15 | 28.06 | Loam | Campbell CS616 TDR | 0.1992 | 0.2205 | 1.377 | 1.32 |
| `ISMN_DLT_022` | 20.260948 | 86.403327 | 437347.52 | 2240218.71 | 52.41 | Silt Loam | Stevens HydraProbe 50MHz | 0.3145 | 0.3448 | 1.344 | 1.29 |
| `ISMN_DLT_023` | 20.260967 | 86.406352 | 437663.35 | 2240220.82 | 64.97 | Clay Loam | Campbell CS616 TDR | 0.3587 | 0.4063 | 1.244 | 2.24 |
| `ISMN_DLT_024` | 20.260604 | 86.408870 | 437926.34 | 2240180.46 | 56.32 | Sandy Loam | Stevens HydraProbe 50MHz | 0.2977 | 0.3471 | 1.570 | 1.08 |

---

## 3. Dataset Artifact Inventory

| Artifact Filename | File Size | Format | Row Count | Column Count | Primary Role |
|:---|:---:|:---:|:---:|:---:|:---|
| **`insitu_soil_stations.csv`** | 4.2 KB | CSV | 24 | 16 | Raw in-situ soil hydrological observations: geodetic coordinates, dual-depth moisture ($0-5\,\text{cm}$, $5-30\,\text{cm}$), temperature, bulk density, organic carbon, and ISMN QC flags. |
| **`collocated_insitu_matrix.csv`** | 5.7 KB | CSV | 24 | 29 | Collocated feature matrix: exact $(i, j)$ pixel mapping on 10m UTM 45N grid, extracted SAR ($VV, VH$), Optical ($B_2-B_8, NDVI, NDWI$), Topography ($Z, \beta, \alpha, TWI$), and Weather ($P, T, VPD$). |
| **`aether_collocated_predictions.csv`** | 6.9 KB | CSV | 24 | 36 | Model benchmarking matrix: binds ground truth with `AETHER-MRID1607X` physical predictions ($\theta$, suction head $h$, conductivity $K$, conformal uncertainty $\sigma_\theta$, and upper/lower intervals). |
