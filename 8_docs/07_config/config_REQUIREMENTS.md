# Subsystem 07: Global Configuration Matrix Specification (`7_config`)
## Central Engine: AETHER-MRID1607X
### Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
### Author & Lead Architect: Gourgopal Mohapatra
### Release Status: FROZEN_OPERATIONAL_RELEASE_v1.0

---

## 1. Executive Overview & Subsystem Mandate

The `7_config/` repository houses the central declarative configuration matrix for the **AETHER-MRID1607X** earth observation and multi-domain soil intelligence platform. Enclosed within `global_config.yaml` (664 bytes, 21 lines), this subsystem establishes immutable global system boundaries, default geospatial coordinate reference systems (CRS), multi-sensor satellite band definitions, and baseline physical constants for Richards' equation hydrological modeling.

The primary mandate of `7_config/` is to serve as the single source of truth across all upstream ingestion pipelines (`2_data_pipeline/`), core physics engines (`3_core_engine/`), domain translators (`4_domain_translators/`), and operational command interfaces (`6_dashboard/`). Parsed at application bootstrap by `ConfigLoader` (`3_core_engine/utils.py`), this configuration matrix prevents cross-subsystem parameter divergence.

```
       +-------------------------------------------------------------------------+
       |             GLOBAL CONFIGURATION MATRIX (7_config/global_config.yaml)  |
       +------------------------------------+------------------------------------+
                                            |
                                            v
       +-------------------------------------------------------------------------+
       |                 CENTRAL PARSER & VALIDATION LOADER                      |
       |                   (3_core_engine/utils.py: ConfigLoader)                |
       |  • YAML Safe Load Matrix                                                |
       |  • Dot-Notation Parameter Querying (`get_param("spatial_bounds.crs")`)  |
       +------------------------------------+------------------------------------+
                                            |
         +----------------------------------+----------------------------------+
         |                                  |                                  |
         v                                  v                                  v
+-----------------------+        +-----------------------+        +-----------------------+
|  SPATIAL BOUNDS       |        |  SATELLITE CHANNELS   |        |  HYDROLOGY PHYSICS    |
| • CRS: EPSG:4326      |        | • S1: VV, VH (SAR)    |        | • Porosity Max: 0.45  |
| • Res: 30.0 meters    |        | • S2: B02, B03, B04,  |        | • K_sat Baseline:     |
| • Default Bounding    |        |       B08, B11, B12   |        |   0.001 cm/s          |
|   Box Coordinates     |        | • DEM: COP30 GLO-30   |        | • Gravity (g): 9.81   |
+-----------------------+        +-----------------------+        +-----------------------+
```

---

## 2. Configuration Matrix Inventory & Full Manifest

The subsystem encapsulates all system-wide parameters within `7_config/global_config.yaml`:

```yaml
# THE MRIDANSH - Global Configuration Matrix
project_name: "THE_MRIDANSH"
engine_version: "AETHER-MRID1607X"

# Spatial-Temporal Limits (Default Testing Domain)
spatial_bounds:
  crs: "EPSG:4326"
  resolution_meters: 30.0
  default_bbox: [77.0, 28.0, 78.0, 29.0] # [min_lon, min_lat, max_lon, max_lat]

# Data Pipeline Channels
satellite_channels:
  sentinel_1: ["VV", "VH"]
  sentinel_2: ["B02", "B03", "B04", "B08", "B11", "B12"] # RGB, NIR, SWIR1, SWIR2
  dem_source: "COP30"

# Physics informed parameters (Richards Boundary defaults)
hydrology_physics:
  porosity_max: 0.45
  hydraulic_conductivity_baseline: 0.001
  gravity_constant: 9.81
```

---

## 3. Parameter Schema & Architectural Semantics

| Parameter Key | Configured Value | Unit / Format | Target Subsystem | Architectural Mandate |
|:---|:---:|:---:|:---|:---|
| `project_name` | `"THE_MRIDANSH"` | UTF-8 String | Workspace-wide | Canonical project workspace identification string. |
| `engine_version` | `"AETHER-MRID1607X"` | Semantic Tag | Core Engine | Designates the frozen physical-neural hybrid estimation architecture. |
| `spatial_bounds.crs` | `"EPSG:4326"` | EPSG Authority Code | `2_data_pipeline` | WGS84 standard geographic coordinate system [lat/lon]. |
| `spatial_bounds.resolution_meters` | `30.0` | Meters ($	ext{m}$) | `2_data_pipeline` | Default raster resampling resolution for testing domains. |
| `spatial_bounds.default_bbox` | `[77.0, 28.0, 78.0, 29.0]` | BBox Vector | `1_notebooks_sandbox` | Reference testing bounding box covering Delhi NCR / Yamuna basin. |
| `satellite_channels.sentinel_1` | `["VV", "VH"]` | C-band Polarization | `2_data_pipeline` | Dual-polarization Level-1 GRD SAR backscatter channels. |
| `satellite_channels.sentinel_2` | `["B02", "B03", "B04", "B08", "B11", "B12"]` | MSI Band Identifiers | `2_data_pipeline` | Blue, Green, Red, NIR, SWIR1, and SWIR2 reflectance bands for moisture indices. |
| `satellite_channels.dem_source` | `"COP30"` | STAC Collection | `2_data_pipeline` | Copernicus 30m Global DEM (GLO-30) surface elevation. |
| `hydrology_physics.porosity_max` | `0.45` | $	ext{m}^3/	ext{m}^3$ | `3_core_engine` | Saturated volumetric moisture ceiling ($	heta_{	ext{sat}}$) for Richards PDE. |
| `hydrology_physics.hydraulic_conductivity_baseline`| `0.001` | $	ext{cm/s}$ | `3_core_engine` | Baseline saturated hydraulic conductivity ($K_{	ext{sat}}$) for alluvial soils. |
| `hydrology_physics.gravity_constant` | `9.81` | $	ext{m/s}^2$ | `3_core_engine` | Gravitational acceleration constant ($g$) for hydraulic gradient calculations. |

---

## 4. Brutally Honest Engineering Disclosures ("Ek Ek Dhappa")

In strict adherence to aerospace software engineering transparency, the following technical compromises, debt points, and operational assumptions in `7_config/` are disclosed:

### Dhappa 1: Relative Path Coupling in `ConfigLoader`
* **Compromise:** In `3_core_engine/utils.py`, `ConfigLoader` defaults to relative path `config_path="7_config/global_config.yaml"`.
* **Failure Mode:** If a script or test is executed from a working directory other than the project root (e.g. running from inside `2_data_pipeline/`), Python evaluates `os.path.exists()` against the subfolder, raising `FileNotFoundError: Critical System Failure: 7_config/global_config.yaml not found`.
* **Mitigation:** The path should be dynamically resolved relative to `Path(__file__).resolve().parent.parent`.

### Dhappa 2: Absence of Schema Validation (Pydantic / Cerberus)
* **Compromise:** The configuration file is ingested via raw `yaml.safe_load()`. There is no schema validation layer (no Pydantic model or JSONSchema check) verifying value types or range bounds.
* **Risk:** A typographical error in a key name (e.g. `gravty_constant`) passes loading silently and only raises a runtime `NoneType` error deep inside physics PDE solver execution.

### Dhappa 3: Geographically Disjoint Default Testing BBox
* **Compromise:** The default bounding box `[77.0, 28.0, 78.0, 29.0]` corresponds to Delhi NCR / Haryana, whereas the operational flight campaign (`9_spaceborne_operational_campaign`) and mission cockpit (`6_dashboard/cockpit/app.py`) operate over Kendrapara, coastal Odisha `[86.40, 20.45, 86.50, 20.55]`.
* **Discrepancy:** Developers running default ingestion without overriding `default_bbox` pull northern alluvial plain scenes instead of the coastal operational campaign AOI.

### Dhappa 4: Simplified Static Soil Physics Constants
* **Compromise:** Richards PDE boundary defaults (`porosity_max: 0.45`, `hydraulic_conductivity_baseline: 0.001`) are single global scalar constants.
* **Limitation:** In real multi-horizon soil columns, porosity and conductivity vary by orders of magnitude across depth ($0-100	ext{ cm}$) and soil texture classes (clay vs loam). Full van Genuchten retention curves ($lpha, n, 	heta_r$) cannot be captured by these 3 scalar values alone.

---

## 5. Traceable Functional Requirements

| Requirement ID | Verification Type | Target Module | Technical Specification |
|:---|:---:|:---:|:---|
| **`REQ-CONF-01`** | Parsing Test | `global_config.yaml` | The configuration file shall parse cleanly under PyYAML `safe_load` without syntax errors or external tag dependencies. |
| **`REQ-CONF-02`** | Schema Test | `global_config.yaml` | `spatial_bounds` shall define WGS84 CRS (`EPSG:4326`), 30m resolution, and a valid 4-element coordinate bounding box. |
| **`REQ-CONF-03`** | Interface Test | `global_config.yaml` | `satellite_channels` shall define VV/VH SAR polarizations, 6 Sentinel-2 optical bands, and COP30 DEM source. |
| **`REQ-CONF-04`** | Physics Test | `global_config.yaml` | `hydrology_physics` shall define positive physical constants ($0.0 < \phi_{\max} < 1.0$, $K_{	ext{sat}} > 0$, $g = 9.81	ext{ m/s}^2$). |
| **`REQ-CONF-05`** | Integration Test | `3_core_engine/utils.py` | `ConfigLoader.get_param()` shall support nested dot-notation access across all declared dictionary hierarchies. |

---

## 6. Safety, Verification & Operational Guidelines

1. **Aerospace Software Integrity Norms**: Configuration parameters must remain read-only at runtime. In-memory modification of the configuration dictionary is strictly prohibited to maintain deterministic repeatability.
2. **Defensive Fallback Defaults**: Upstream modules consuming configuration values must specify defensive fallback arguments when calling `ConfigLoader.get_param(key, default=...)` to guard against missing keys.
