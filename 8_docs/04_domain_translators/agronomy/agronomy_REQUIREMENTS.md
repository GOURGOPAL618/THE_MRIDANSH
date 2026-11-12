# Subsystem 04: Precision Agronomy & FAO-56 Irrigation Engine (`4_domain_translators/agronomy`)
## Central Engine: AETHER-MRID1607X
### Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
### Author & Lead Architect: Gourgopal Mohapatra
### Release Status: FROZEN_OPERATIONAL_RELEASE_v1.0

---

## 1. Executive Overview & Subsystem Mandate

The `4_domain_translators/agronomy/` subsystem is the physics-grounded agricultural intelligence engine of the **AETHER-MRID1607X** platform. Operating downstream of the core soil hydrology tensors (`3_core_engine/`), this module implements the complete **FAO-56 Dual Crop Coefficient** evapotranspiration framework (Allen et al., 1998), coupled with **Saxton & Rawls (2006) Pedotransfer Functions**, **Gutman & Ignatov (1998) Dynamic Phenology**, and **Conformal Uncertainty-Bounded Variable Rate Irrigation (VRI)** prescription synthesis.

The primary mandate of this subsystem is to transform raw volumetric soil moisture ($\theta_{\text{surf}}, \theta_{\text{rz}}$), optical NDVI, and conformal uncertainty bounds ($\pm 2\sigma$) into deterministic, auditable irrigation volume recommendations (mm and L/ha) and Cloud-Optimized GeoTIFFs (COGs) across 9 agronomic crop taxonomies.

```
       +-------------------------------------------------------------------------+
       |              UNIFIED SOIL STATE & OPTICAL REFLECTANCE INPUTS            |
       |  • Root-Zone Moisture (theta_rz), Surface Moisture (theta_surf)         |
       |  • Conformal Uncertainty (±2σ), Optical NDVI / NIR-Red Reflectance      |
       +------------------------------------+------------------------------------+
                                            |
                                            v
       +-------------------------------------------------------------------------+
       |                    AGRONOMY DOMAIN ENGINE PIPELINE                      |
       |                     (agronomy_domain_engine.py)                         |
       +------------------------------------+------------------------------------+
                                            |
         +----------------------------------+----------------------------------+
         |                                  |                                  |
         v                                  v                                  v
+-----------------------+        +-----------------------+        +-----------------------+
|  SOIL RESERVOIR       |        |  DYNAMIC PHENOLOGY    |        |  FAO-56 DUAL Kc       |
| (soil_water_          |        | (dynamic_phenology.py)|        | (fao56_dual_kc.py)    |
|  reservoir.py)        |        | • Gutman-Ignatov fc   |        | • Stage 1/2 Soil Evap |
| • Saxton-Rawls PTF    |        | • Dynamic Root Depth  |        |   Reduction (Kr)      |
| • TAW & RAW [mm]      |        |   Zr(fc) Deepening    |        | • Kc = Kcb + Ke       |
+-----------+-----------+        +-----------+-----------+        +-----------+-----------+
            |                                |                                |
            +--------------------------------+--------------------------------+
                                             |
                                             v
       +-------------------------------------------------------------------------+
       |           WATER STRESS & CONFORMAL VRI PRESCRIPTION DISPATCH            |
       |  • CropWaterStressEngine: Depletion (Dr), Ks, CWSI = 1 - Ks             |
       |  • PrecisionIrrigationEngine: Net/Gross Irrigation (mm & L/ha)          |
       |  • ConformalRiskDispatcher: [I_min, I_nom, I_max] Risk Bounds           |
       +------------------------------------+------------------------------------+
                                            |
                                            v
       +-------------------------------------------------------------------------+
       |           GEOSPATIAL EXPORT & SHA-256 INTEGRITY AUDIT                   |
       |  • AgronomicGeoTIFFExporter: 4-Band COG Stack + SHA-256 Digest          |
       +-------------------------------------------------------------------------+
```

---

## 2. Module Inventory & Architectural Responsibilities

The `agronomy/` package comprises 14 files covering physical engines, crop taxonomy lookup tables, geospatial exporters, and phase verification suites:

| File Path | File Size | Module Classification | Key Architectural Responsibilities |
|:---|:---:|:---|:---|
| **`agronomy_domain_engine.py`** | 7.0 KB | Master Engine | `AgronomyDomainEngine`: Orchestrates full end-to-end execution returning typed `AgronomicStateVector` payloads. |
| **`soil_water_reservoir.py`** | 13.1 KB | Hydraulic Reservoir | `SoilWaterReservoirEngine`: Saxton-Rawls pedotransfer equations, 12 USDA soil texture presets, $TAW$ and $RAW$ calculations. |
| **`dynamic_phenology.py`** | 6.8 KB | Canopy Phenology | `DynamicPhenologyEngine`: Computes NDVI, Gutman-Ignatov fractional cover $f_c$, sigmoidal root depth $Z_r(f_c)$, and basal crop coefficient $K_{cb}$. |
| **`fao56_dual_kc.py`** | 7.2 KB | Evapotranspiration | `FAO56DualKcEngine`: Implements Stage 1/2 surface evaporation reduction $K_r$, exposed wetted fraction $f_{ew}$, and total $K_c = K_{cb} + K_e$. |
| **`crop_water_stress.py`** | 6.9 KB | Stress Analytics | `CropWaterStressEngine`: Computes root-zone depletion $D_r$ (mm), transpiration stress factor $K_s$, and Crop Water Stress Index ($	ext{CWSI} = 1 - K_s$). |
| **`irrigation_prescription.py`** | 8.7 KB | VRI Prescriptions | `PrecisionIrrigationEngine`: Translates depletion into net/gross irrigation depth (`STRESS_AVOIDANCE`, `FULL_RECHARGE`, `DAILY_ETC_REPLACEMENT`) and priority masks. |
| **`conformal_risk_dispatcher.py`** | 7.8 KB | Risk Bounds Engine | `ConformalRiskDispatcher`: Propagates AETHER $\pm 2\sigma$ conformal intervals into conservative (`I_min`), nominal (`I_nom`), and protective (`I_max`) irrigation bounds. |
| **`agronomic_geotiff_exporter.py`**| 9.8 KB | COG Raster Exporter | `AgronomicGeoTIFFExporter`: Writes georeferenced 4-band agronomic GeoTIFFs with SHA-256 provenance and Windows viewer file-lock guards. |
| **`crop_taxonomy.json`** | 4.0 KB | Reference Registry | Parameter database covering 9 crops (`rice_paddy`, `wheat`, `maize`, `sugarcane`, `cotton`, `pulses_chickpea`, `mustard_oilseed`, `potato`, `default_generic_crop`). |
| **`verify_phase1*.py` / `verify_phase2*.py`**| ~28 KB | Verification Suites | 4 standalone certification scripts validating physical bounds, mass balance, and Day 13 conformal VRI contracts. |

---

## 3. Mathematical Formulations & Agronomic Physics

### 3.1 Saxton & Rawls (2006) Pedotransfer Functions (`soil_water_reservoir.py`)

Given soil sand ($S$), clay ($C$), and organic matter ($OM$) fractions, continuous field capacity ($\theta_{\text{fc}}$), wilting point ($\theta_{\text{wp}}$), and saturation ($\theta_{\text{sat}}$) are computed and constrained within physical limits ($0 \le \theta_{\text{res}} \le \theta_{\text{wp}} < \theta_{\text{fc}} < \theta_{\text{sat}} \le 1$):

$$TAW = 1000 \cdot (\theta_{\text{fc}} - \theta_{\text{wp}}) \cdot Z_r \quad [\text{mm}]$$

$$RAW = p \cdot TAW \quad [\text{mm}]$$

Where $Z_r$ is active rooting depth (m) and $p$ is the crop-specific depletion fraction for no stress (from `crop_taxonomy.json`).

### 3.2 Gutman & Ignatov (1998) Phenology & Dynamic Rooting (`dynamic_phenology.py`)

Fractional canopy ground cover $f_c \in [0, 1]$ and dynamic rooting depth $Z_r$ are derived from satellite NDVI:

$$f_c = \text{clip}\left(\frac{\text{NDVI} - \text{NDVI}_{\text{bare}}}{\text{NDVI}_{\text{full}} - \text{NDVI}_{\text{bare}}}, \; 0.0, \; 1.0\right)$$

$$Z_r(f_c) = Z_{r,\min} + (Z_{r,\max} - Z_{r,\min}) \cdot f_c^\gamma$$

$$K_{cb}(f_c) = K_{cb,\text{ini}} + (K_{cb,\text{mid}} - K_{cb,\text{ini}}) \cdot f_c$$

### 3.3 FAO-56 Dual Crop Coefficient ($K_c$) (`fao56_dual_kc.py`)

Total potential crop evapotranspiration separates basal plant transpiration ($K_{cb}$) from bare-soil surface evaporation ($K_e$):

$$K_r = \text{clip}\left(\frac{\theta_{\text{surf}} - \theta_{\text{res}}}{\theta_{\text{fc}} - \theta_{\text{res}}}, \; 0.0, \; 1.0\right)$$

$$K_e = \min\left(K_r \cdot (K_{c,\max} - K_{cb}), \; f_{ew} \cdot K_{c,\max}\right), \quad f_{ew} = 1 - f_c$$

$$ET_c = (K_{cb} + K_e) \cdot ET_0$$

### 3.4 Crop Water Stress Index & Conformal Bounds (`crop_water_stress.py`, `conformal_risk_dispatcher.py`)

Root-zone depletion $D_r$ (mm) drives transpiration reduction factor $K_s$ and stress index $\text{CWSI}$:

$$D_r = 1000 \cdot (\theta_{\text{fc}} - \theta_{\text{rz}}) \cdot Z_r, \quad K_s = \text{clip}\left(\frac{TAW - D_r}{TAW - RAW}, \; 0.0, \; 1.0\right), \quad \text{CWSI} = 1.0 - K_s$$

Under conformal uncertainty $\pm 2\sigma$ on root-zone moisture ($\theta_{\text{rz}}^{\min} = \theta_{\text{rz}} - 2\sigma$, $\theta_{\text{rz}}^{\max} = \theta_{\text{rz}} + 2\sigma$), `ConformalRiskDispatcher` generates three operational bounds:
* **`I_min` (Hypoxia / Over-irrigation Guard):** Computed from upper moisture bound $\theta_{\text{rz}}^{\max}$.
* **`I_nom` (Nominal Prescription):** Computed from mean estimate $\theta_{\text{rz}}$.
* **`I_max` (Wilting Protection Guard):** Computed from lower moisture bound $\theta_{\text{rz}}^{\min}$.

---

## 4. Brutally Honest Engineering Disclosures ("Ek Ek Dhappa")

In adherence to strict aerospace engineering transparency, the following domain compromises and physical assumptions in `4_domain_translators/agronomy/` are explicitly disclosed:

### Dhappa 1: Saxton-Rawls Non-Saline Mineral Soil Assumption
* **Compromise:** `saxton_rawls_pedotransfer` fits empirical polynomial regressions calibrated on US temperate mineral soils.
* **Limitation:** Coastal Odisha deltaic soils often exhibit high salinity, sodicity, or organic muck layers. In saline-alkali coastal belts, osmotic potential reduces plant-available water even when matric suction predictions look favorable.

### Dhappa 2: Uniform Texture Grid Fallbacks
* **Compromise:** When spatially continuous sand/clay rasters are unavailable, `generate_spatial_reservoir_map` broadcasts a single scalar USDA soil texture class (e.g., `clay_loam`) across the entire 64x64 grid.
* **Impact:** Real-world micro-topographical sand lenses and clay pockets within a single village block are flattened into uniform $TAW$ and $RAW$ thresholds.

### Dhappa 3: Optical NDVI Saturation & Cloud Artifacts
* **Compromise:** `DynamicPhenologyEngine` derives fractional cover $f_c$ strictly from optical NDVI ($	ext{NDVI}_{\text{bare}}=0.15, \text{NDVI}_{\text{full}}=0.80$).
* **Failure Mode:** During dense vegetative stages (e.g., full-canopy rice paddy), NDVI saturates near 0.80, freezing $K_{cb}$ and $Z_r$ sensitivity. Additionally, residual cloud haze suppresses NDVI, causing under-estimation of crop transpiration demand.

### Dhappa 4: Single-Layer Bucket Root-Zone Depletion
* **Compromise:** `CropWaterStressEngine` aggregates the active root zone $[0, Z_r]$ into a single bulk water reservoir $D_r$.
* **Engineering Reality:** It assumes roots extract water uniformly across depth, whereas real crops extract $>70\%$ of moisture from the upper $50\%$ of the root zone before tapping deeper layers.

### Dhappa 5: Symmetric Conformal Error Intervals
* **Compromise:** `ConformalRiskDispatcher` applies symmetric $\theta_{\text{rz}} \pm 2\sigma$ intervals clipped to $[\theta_{\text{wp}}, \theta_{\text{sat}}]$.
* **Limitation:** Near saturation or wilting boundaries, true physical error distributions become heavily skewed. Symmetric bounds can slightly overestimate `I_max` during extreme dry regimes.

---

## 5. Traceable Functional Requirements

| Requirement ID | Verification Type | Target Module | Technical Specification |
|:---|:---:|:---:|:---|
| **`REQ-AGRO-01`** | Physics Test | `soil_water_reservoir.py` | `SoilHydraulicProperties` shall strictly enforce $0 \le \theta_{\text{res}} \le \theta_{\text{wp}} < \theta_{\text{fc}} < \theta_{\text{sat}} \le 1$ and guarantee $RAW \le TAW$. |
| **`REQ-AGRO-02`** | Unit Test | `dynamic_phenology.py` | `compute_fractional_cover` and `compute_dynamic_root_depth` shall return bounded values $f_c \in [0, 1]$ and $Z_r \in [Z_{r,\min}, Z_{r,\max}]$ without NaNs. |
| **`REQ-AGRO-03`** | Physics Test | `fao56_dual_kc.py` | `compute_dual_coefficients` shall bound soil evaporation $K_e \le f_{ew} \cdot K_{c,\max}$ and satisfy $K_c = K_{cb} + K_e$. |
| **`REQ-AGRO-04`** | Unit Test | `crop_water_stress.py` | `evaluate_stress` shall compute $K_s \in [0, 1]$ and $\text{CWSI} = 1 - K_s$ with zero division-by-zero errors when $TAW = RAW$. |
| **`REQ-AGRO-05`** | Integration Test | `irrigation_prescription.py` | `PrecisionIrrigationEngine` shall compute non-negative net/gross irrigation volumes accounting for system application efficiency. |
| **`REQ-AGRO-06`** | Risk Audit | `conformal_risk_dispatcher.py` | `dispatch_risk_bounds` shall monotonically satisfy $I_{\min} \le I_{\text{nom}} \le I_{\max}$ across all valid pixels. |
| **`REQ-AGRO-07`** | Export Test | `agronomic_geotiff_exporter.py`| Exporter shall write 4-band GeoTIFF stacks with valid EPSG projection, SHA-256 integrity hash, and Windows lock safety. |
| **`REQ-AGRO-08`** | Regression Test | `verify_phase*.py` | All 4 phase verification suites shall pass 100% deterministic physics and numerical boundary checks. |

---

## 6. Safety, Verification & Operational Guidelines

1. **Aerospace Software Integrity Norms**: Every mathematical computation enforces explicit NaN/Inf assertions and physical boundary clamps prior to returning `AgronomicStateVector` outputs.
2. **Conformal Risk Transparency**: Farmers and field engineers receive all three risk-bounded irrigation tiers (`I_min`, `I_nom`, `I_max`) rather than a single over-confident scalar prescription.
