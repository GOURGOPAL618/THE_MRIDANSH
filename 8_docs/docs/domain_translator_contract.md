# Domain Translators Contract & Architecture Specification

**THE MRIDANSH · AETHER-MRID1607X**  
**Module:** `4_domain_translators`  
**Task:** 02 of 06 — Verified 2026-10-09

---

## 1. Objective & Scope

This specification formalizes the shared contracts and abstract interface for the `4_domain_translators` module.
It establishes:
1. A structured input contract (`DomainInput`) carrying physical soil state rasters, validity masks, uncertainty metrics, and geospatial metadata.
2. A structured output contract (`DomainOutput`) carrying domain-specific metrics, valid masks, propagated metadata, and scientific caveats.
3. An abstract base interface (`BaseDomainTranslator`) providing consistent input normalization and calling conventions.
4. Documented import mechanisms compliant with Python's numeric directory naming constraints.

---

## 2. Shared Input Contract (`DomainInput`)

The `DomainInput` dataclass encapsulates all upstream information required for domain translation.

### 2.1 Specification Table

| Field Name | Type | Requirement | Default | Description / Units |
| :--- | :--- | :---: | :--- | :--- |
| `soil_state` | `np.ndarray` | **Required** | — | Physical soil state array (e.g. Volumetric Soil Moisture $\theta$). Must have $\ge 2$ spatial dimensions $(H, W)$. Must be finite unless masked. |
| `state_variable` | `str` | Optional | `"volumetric_soil_moisture"` | Explicit physical quantity name. |
| `unit` | `str` | Optional | `"m3/m3"` | Physical unit of measurement. |
| `valid_data_mask`| `Optional[np.ndarray]`| Optional | `None` | Boolean array where `True` = valid, `False` = invalid/cloud/NoData. Shape must match `soil_state.shape`. |
| `uncertainty` | `Optional[Union[float, np.ndarray]]` | Optional | `None` | State estimation uncertainty (e.g. EnKF posterior ensemble variance). Must be finite and $\ge 0.0$. |
| `uncertainty_type` | `Optional[str]` | Optional | `None` | Specification of uncertainty representation: `'variance'`, `'std'`, `'ensemble_spread'`, etc. |
| `crs` | `Optional[str]` | Optional | `None` | Coordinate Reference System identifier (e.g. `'EPSG:32645'`). None if unprojected. |
| `transform` | `Optional[Tuple[float, ...]]` | Optional | `None` | 6-element GDAL/Affine geotransform tuple. |
| `bounds` | `Optional[Tuple[float, float, float, float]]` | Optional | `None` | Geospatial bounding box `(min_x, min_y, max_x, max_y)`. Must satisfy `min < max`. |
| `resolution` | `Optional[Tuple[float, float]]` | Optional | `None` | Spatial resolution tuple `(res_x, res_y)` in CRS units. Must be positive finite floats. |
| `acquisition_datetime` | `Optional[str]` | Optional | `None` | ISO 8601 acquisition timestamp string. |
| `provenance` | `Optional[Dict[str, Any]]` | Optional | `None` | STAC scene identifiers, satellite platform, and processing lineage. |
| `ndvi` | `Optional[np.ndarray]` | Optional | `None` | Optical vegetation index array. If supplied, shape must match `soil_state.shape`. |
| `dry_density_g_cm3` | `Optional[float]` | Optional | `None` | Geotechnical dry bulk density in $\text{g/cm}^3$. Must be finite and $> 0.0$. |
| `extra_parameters` | `Dict[str, Any]` | Optional | `{}` | Extensible bag for caller-supplied domain parameters. |

### 2.2 Validation Rules
- **Array Rank:** `soil_state.ndim >= 2` enforced at instantiation. Rank-1 or 0-D tensors raise `ValueError`.
- **Numeric Integrity:** If `valid_data_mask` is omitted, `soil_state` must be 100% finite (no NaN or Inf). If a mask is provided, only unmasked valid pixels must be finite.
- **Uncertainty Bounds:** Non-negative constraint ($u \ge 0.0$) enforced. Negative uncertainty values raise `ValueError`.
- **No Fabricated Metadata:** If geospatial metadata (CRS, bounds, transform) is absent upstream, fields remain `None`. Defaults like `EPSG:4326` or `(0,0,0,0)` are **never** synthesized.

---

## 3. Shared Output Contract (`DomainOutput`)

The `DomainOutput` dataclass standardizes translation results across Agriculture and Civil modules.

### 3.1 Specification Table

| Field Name | Type | Requirement | Description |
| :--- | :--- | :---: | :--- |
| `domain` | `str` | **Required** | Domain identifier: `'agriculture'` or `'civil'`. Non-empty string. |
| `metrics` | `Dict[str, Any]` | **Required** | Primary dictionary containing calculated matrices, summary KPI floats, and qualitative risk classifications. |
| `valid_data_mask` | `Optional[np.ndarray]` | Optional | Boolean mask matching output spatial rasters. |
| `metadata` | `Dict[str, Any]` | Optional | Preserved geospatial context, CRS, resolution, and timestamps. |
| `uncertainty` | `Optional[Dict[str, Any]]` | Optional | Explicit translated domain uncertainty measures (e.g. Trafficability confidence bounds). |
| `warnings` | `List[str]` | Optional | Audit notices, heuristic caveats, out-of-distribution flags, or uncalibrated model warnings. |

### 3.2 Backward Compatibility & Dictionary Emulation
To ensure drop-in compatibility with legacy callers and dashboard viewports expecting Python dictionaries:
- `output[key]` retrieves from `metrics` first, then attributes.
- `key in output` checks both `metrics` and attributes.
- `output.get(key, default)` performs safe dictionary lookups.
- `output.to_dict()` produces a complete dictionary containing metadata, metrics, and flat metric keys.

---

## 4. Abstract Base Translator (`BaseDomainTranslator`)

```python
class BaseDomainTranslator(ABC):
    @abstractmethod
    def translate(
        self,
        soil_input: Union[DomainInput, np.ndarray],
        **kwargs: Any,
    ) -> Union[DomainOutput, Dict[str, Any]]:
        """Translates raw/estimated soil state into domain-specific metrics."""
        pass

    @staticmethod
    def normalize_input(
        soil_input: Union[DomainInput, np.ndarray],
        **kwargs: Any,
    ) -> DomainInput:
        """Converts raw arrays or DomainInput objects into validated DomainInput."""
        ...
```

The static method `normalize_input` bridges legacy call sites (passing loose arrays and kwargs) into modern validated `DomainInput` structures without breaking existing call patterns.

---

## 5. Supported Import Mechanisms

Because `4_domain_translators` begins with a digit, standard Python syntax `import 4_domain_translators` causes a `SyntaxError: invalid decimal literal`.

### Supported Import Patterns:

1. **Dynamic Import (Recommended across packages):**
   ```python
   import importlib
   translators = importlib.import_module("4_domain_translators")
   BaseDomainTranslator = translators.BaseDomainTranslator
   DomainInput = translators.DomainInput
   DomainOutput = translators.DomainOutput
   ```

2. **Package Path Insertion (Recommended for test suites):**
   ```python
   import os, sys
   sys.path.insert(0, os.path.join(repo_root, "4_domain_translators"))
   from base import BaseDomainTranslator, DomainInput, DomainOutput
   ```

3. **Submodule CLI Execution:**
   ```powershell
   python -m 4_domain_translators.agronomy_translator
   python -m 4_domain_translators.civil_translator
   ```

---

## 6. Scientific Limitations & Demarcation of Future Tasks

- **Task 02 Scope:** Defined and verified data contracts, base interface, input validation, and import mechanics.
- **Tasks 03 & 04 (Future):** Refactor `agronomy_translator.py` and `civil_translator.py` to consume `DomainInput`, enforce mask filtering, and produce `DomainOutput`.
- **Task 05 (Future):** Build integration adapter from `3_core_engine` EnKF state output to `DomainInput`.
- **Task 06 (Future):** Test suite expansion and downstream dashboard contract alignment.
