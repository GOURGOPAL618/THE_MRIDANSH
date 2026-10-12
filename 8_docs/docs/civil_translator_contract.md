# Civil Load Translator Specification & Geotechnical Parameter Audit

**THE MRIDANSH · AETHER-MRID1607X**  
**Module:** `4_domain_translators/civil_translator.py`  
**Task:** 04 of 06 — Verified 2026-10-09  
**Status:** Hardened & Operationally Verified  

---

## 1. Executive Summary

This document specifies the software contract, dimensional derivations, geotechnical assumptions, and scientific boundaries of `CivilLoadTranslator` in `4_domain_translators/civil_translator.py`.

The Civil Translator converts satellite-estimated volumetric soil moisture ($\theta$ in $\text{m}^3/\text{m}^3$) and optional soil dry bulk density ($\rho_d$ in $\text{g/cm}^3$) into nominal soil mechanical bearing capacity rasters, shear cohesion matrices, and broad heavy machinery trafficability ratings.

> [!CAUTION]
> **Geotechnical Safety Disclaimer**
> 
> The calculations performed by this translator are **uncalibrated heuristics**. The nominal bearing capacity represents an idealized, unreduced ultimate capacity ($q_{\text{ult}}$) without an engineering **Factor of Safety (FS)**. In standard civil engineering practice, allowable bearing capacity requires $FS \ge 3.0$ ($q_{\text{all}} = q_{\text{ult}} / FS$). 
> 
> **Outputs from this module MUST NOT be used for foundation design, roadbed engineering, embankment stability verification, or structural permitting.**

---

## 2. Input and Output Contracts

### 2.1 Standardized Input (`DomainInput`)

`CivilLoadTranslator.translate()` accepts the standardized `DomainInput` dataclass:

| Field | Type | Unit | Requirement | Description |
| :--- | :--- | :--- | :---: | :--- |
| `soil_state` | `np.ndarray` | $\text{m}^3/\text{m}^3$ | **Required** | Volumetric soil moisture array ($\ge 2\text{D}$). Plausibility bounds $[0.0, 1.0]$. |
| `state_variable` | `str` | — | Optional | Must be in `{'volumetric_soil_moisture', 'soil_moisture', 'surface_soil_moisture', 'root_zone_moisture', 'soil_water_content'}`. |
| `unit` | `str` | — | Optional | Must be in `{'m3/m3', 'm^3/m^3', 'm3 m-3', 'fraction', 'dimensionless', 'm3/m3 (volumetric)', 'm3 / m3'}`. |
| `valid_data_mask` | `Optional[np.ndarray]` | bool | Optional | Boolean mask where `True` indicates valid pixels. Must match `soil_state.shape`. |
| `dry_density_g_cm3` | `Optional[float]` | $\text{g/cm}^3$ | Optional | Dry bulk density. Default $1.60\text{ g/cm}^3$. Must be finite and $> 0.0$. |
| `uncertainty` | `Optional[Union[float, np.ndarray]]` | — | Optional | Upstream state estimation uncertainty (e.g. EnKF posterior variance). Preserved without false downstream claims. |
| `uncertainty_type` | `Optional[str]` | — | Optional | Declared representation (e.g. `'ensemble_variance'`). |
| `metadata` | geospatial | — | Optional | `crs`, `transform`, `bounds`, `resolution`, `acquisition_datetime`, `provenance`. |

### 2.2 Standardized Output (`DomainOutput`)

| Field | Type | Description |
| :--- | :--- | :--- |
| `domain` | `str` | Constant `"civil"`. |
| `metrics["bearing_capacity_matrix_kPa"]` | `np.ndarray` (float32) | Nominal ultimate bearing capacity raster in $\text{kPa}$. Invalid pixels contain `np.nan`. |
| `metrics["effective_cohesion_kPa"]` | `np.ndarray` (float32) | Effective shear cohesion raster in $\text{kPa}$. Invalid pixels contain `np.nan`. |
| `metrics["site_trafficability"]` | `str` | Qualitative site trafficability rating string. |
| `metrics["mean_bearing_kPa"]` | `float` | Spatial mean nominal bearing capacity over valid pixels only ($\text{kPa}$). |
| `metrics["mean_effective_cohesion_kPa"]`| `float` | Spatial mean shear cohesion over valid pixels only ($\text{kPa}$). |
| `metrics["surcharge_kPa"]` | `float` | Evaluated foundation surcharge stress ($\text{kPa}$). |
| `metrics["dry_density_g_cm3"]` | `float` | Applied dry bulk density ($\text{g/cm}^3$). |
| `valid_data_mask` | `Optional[np.ndarray]` | Preserved boolean valid pixel mask. |
| `metadata` | `Dict[str, Any]` | Geospatial metadata and STAC lineage preserved intact. |
| `uncertainty` | `Optional[Dict[str, Any]]` | Preserved upstream uncertainty marked `propagation_status: "unpropagated"`. |
| `warnings` | `List[str]` | Explicit engineering caveats and uncalibrated model notices. |

---

## 3. Geotechnical Parameterization & Dimensional Analysis

### 3.1 Model Constants

The translator parameterizes classical soil mechanics relationships with the following default constants:

| Constant | Value | Units | Physical Interpretation & Assumptions |
| :--- | :--- | :--- | :--- |
| $\theta_{\text{sat}}$ | $0.45$ | $\text{m}^3/\text{m}^3$ | Reference saturation moisture content; assumes nominal pore volume fraction (porosity $n = 0.45$). |
| $c_0$ | $35.0$ | $\text{kPa}$ | Baseline dry apparent cohesion for fine-grained cohesive soil. |
| $r_c$ | $0.60$ | dimensionless | Cohesion degradation coefficient at $100\%$ saturation ($60\%$ loss of dry cohesion). |
| $N_c$ | $5.7$ | dimensionless | Prandtl / Terzaghi undrained bearing capacity factor for frictionless rough continuous strip footing ($\phi = 0^\circ$). |
| $D_f$ | $1.5$ | $\text{m}$ | Assumed nominal foundation embedment depth. |
| $g$ | $9.81$ | $\text{m/s}^2$ | Standard gravitational acceleration. |
| $\rho_{d,\text{default}}$ | $1.60$ | $\text{g/cm}^3$ | Default dry bulk density for typical mineral soils. |

### 3.2 Dimensional Derivation of Surcharge Term

In geotechnical engineering, vertical surcharge stress $q$ at depth $D_f$ is defined as:
$$q = \gamma_{\text{dry}} \cdot D_f$$

Where:
- $\rho_d$ is dry bulk density in $\text{g/cm}^3 = 1000\text{ kg/m}^3$.
- $g = 9.81\text{ m/s}^2$.
- Soil dry unit weight $\gamma_{\text{dry}}$ in $\text{N/m}^3$:
  $$\gamma_{\text{dry}} = \rho_d \left[\frac{\text{g}}{\text{cm}^3}\right] \times 1000 \left[\frac{\text{kg/m}^3}{\text{g/cm}^3}\right] \times 9.81 \left[\frac{\text{m}}{\text{s}^2}\right] = 9810 \cdot \rho_d \left[\frac{\text{N}}{\text{m}^3}\right]$$
- Converting $\text{N/m}^3$ to $\text{kN/m}^3$ ($\text{kPa/m}$):
  $$\gamma_{\text{dry}} \left[\frac{\text{kN}}{\text{m}^3}\right] = \frac{9810 \cdot \rho_d}{1000} = 9.81 \cdot \rho_d \left[\frac{\text{kN}}{\text{m}^3}\right] = 9.81 \cdot \rho_d \left[\frac{\text{kPa}}{\text{m}}\right]$$
- Surcharge stress $q$ at $D_f = 1.5\text{ m}$:
  $$q \left[\text{kPa}\right] = \gamma_{\text{dry}} \left[\frac{\text{kPa}}{\text{m}}\right] \times 1.5\left[\text{m}\right] = \rho_d \times 9.81 \times 1.5 \left[\text{kPa}\right]$$

For default $\rho_d = 1.60\text{ g/cm}^3$:
$$q = 1.60 \times 9.81 \times 1.5 = 23.544\text{ kPa}$$

The legacy code formulation `dry_density_g_cm3 * 9.81 * 1.5` evaluates directly to $\text{kPa}$ because the conversion factor $1000\text{ kg/m}^3\text{ per g/cm}^3$ and $1/1000\text{ kN/N}$ exactly cancel out.

### 3.3 Comparison with Classical Terzaghi Theory

Terzaghi's classical general bearing capacity equation for a continuous strip footing is:
$$q_{\text{ult}} = c \cdot N_c + q \cdot N_q + \frac{1}{2} \gamma B N_\gamma$$

In `CivilLoadTranslator`:
1. **Cohesion Term ($c \cdot N_c$):** Evaluated with $N_c = 5.7$ and $c = c(\theta) = c_0 \cdot (1 - 0.6 \cdot S_r)$. $N_c = 5.7$ corresponds to Terzaghi's rough base undrained condition ($\phi = 0^\circ$).
2. **Surcharge Term ($q \cdot N_q$):** Evaluated with $N_q = 1.0$ (which corresponds strictly to $\phi = 0^\circ$).
3. **Footing Width Term ($\frac{1}{2} \gamma B N_\gamma$):** Completely omitted ($N_\gamma = 0$ for $\phi = 0^\circ$).

#### Geotechnical Limitations of this Formulation:
- **Cohesionless Soils (Sands & Gravels):** For granular soils, true cohesion $c = 0$, and bearing capacity is derived entirely from friction angle $\phi > 0$ via $N_q$ and $N_\gamma$. Applying this formula to sand produces invalid results.
- **Undrained vs Drained Behavior:** In saturated clays, undrained shear strength $s_u$ is determined from consolidation stress and liquidity index, not simple dry cohesion scaling.
- **Factor of Safety:** The formula computes nominal ultimate bearing capacity $q_{\text{ult}}$. An allowable bearing capacity $q_{\text{all}} = q_{\text{ult}} / FS$ is **not** computed.

---

## 4. Trafficability Classification

Site trafficability grades are assigned based on the spatial mean nominal bearing capacity computed strictly over valid pixels:

| Mean Nominal Bearing Capacity | Trafficability Grade | Operational Heuristic |
| :--- | :--- | :--- |
| $> 180.0\text{ kPa}$ | `HEAVY_RIG_PERMITTED` | Firm soil conditions; sufficient nominal strength for heavy tracked rigs. |
| $> 120.0\text{ kPa}$ and $\le 180.0\text{ kPa}$ | `LIGHT_VEHICLE_ONLY` | Marginal support; heavy equipment risks rutting or immobilization. |
| $\le 120.0\text{ kPa}$ | `HAZARDOUS_UNSTABLE_SOIL` | Saturated or low-strength soil; severe vehicle sinkage hazard. |

> [!NOTE]
> These thresholds are empirical rule-of-thumb heuristics. They are not calibrated against vehicle gross weights, tire inflation pressures, contact patch areas, or NATO Rating Cone Index (RCI) mobility models.

---

## 5. Verification & Regression Coverage

The hardened implementation is tested in `tests/test_civil_translator_d04.py` (18 focused tests):

1. `test_t01_valid_domain_input_accepted`: Verifies execution under standardized `DomainInput`.
2. `test_t02_legacy_array_call_compatible`: Verifies positional and keyword calling conventions.
3. `test_t03_unsupported_state_variable_or_unit_rejected`: Verifies rejection of non-moisture variables and invalid units.
4. `test_t04_dry_density_validation`: Validates rejection of non-numeric, $\le 0$, and non-finite density inputs.
5. `test_t05_broad_sanity_bounds_enforced`: Rejects out-of-bounds soil moisture $(< 0.0$ or $> 1.0\text{ m}^3/\text{m}^3$).
6. `test_t06_mask_dtype_and_shape_validation`: Validates mask dimensions and boolean dtype.
7. `test_t07_masked_nans_do_not_contaminate_calculations`: Verifies NaN isolation on invalid pixels.
8. `test_t08_all_invalid_mask_rejected`: Rejects masks with zero valid pixels.
9. `test_t09_invalid_pixels_do_not_affect_aggregates_or_trafficability`: Verifies statistical immunity of aggregates to masked invalid data.
10. `test_t10_valid_pixel_outputs_are_finite`: Confirms all valid-pixel calculations are finite floats.
11. `test_t11_geospatial_metadata_and_provenance_preserved`: Validates propagation of CRS, transform, bounds, resolution, and STAC lineage.
12. `test_t12_warnings_document_geotechnical_limitations`: Confirms presence of mandatory engineering caveats.
13. `test_t13_uncertainty_semantics_and_no_false_labeling`: Verifies honest propagation of input uncertainty without false claims on bearing capacity.
14. `test_t14_domain_output_preserves_legacy_dict_access`: Confirms backward compatibility for dictionary indexing and `.get()`.
15. `test_t15_dimensional_consistency_of_surcharge_and_cohesion`: Analytical verification against theoretical values at dry and saturated conditions.
16. `test_t16_absent_density_uses_documented_default_and_warns_atypical`: Validates default density assignment and range warnings.
17. `test_t17_conflicting_arguments_rejected`: Traps conflicting positional, keyword, or object arguments.
18. `test_t18_trafficability_threshold_classification`: Validates boundary transitions between the three trafficability grades.
