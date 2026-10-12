# THE MRIDANSH - CIVIL TRANSLATOR
# Module: 4_domain_translators/civil_translator.py
# AETHER-MRID1607X Core Engine

import logging
import math
from typing import Any, Dict, List, Optional, Set, Union

import numpy as np

try:
    from .base import BaseDomainTranslator, DomainInput, DomainOutput
except ImportError:
    from base import BaseDomainTranslator, DomainInput, DomainOutput

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Supported physical state variables for the Civil domain
SUPPORTED_STATE_VARIABLES: Set[str] = {
    "volumetric_soil_moisture",
    "soil_moisture",
    "surface_soil_moisture",
    "root_zone_moisture",
    "soil_water_content",
}

# Supported units for volumetric soil moisture fraction
SUPPORTED_UNITS: Set[str] = {
    "m3/m3",
    "m^3/m^3",
    "m3 m-3",
    "fraction",
    "dimensionless",
    "m3/m3 (volumetric)",
    "m3 / m3",
}

# Geotechnical Model Constants & Default Assumptions
DEFAULT_DRY_DENSITY_G_CM3: float = 1.6  # Default dry bulk density (g/cm3)
TYPICAL_MIN_DRY_DENSITY_G_CM3: float = 0.8
TYPICAL_MAX_DRY_DENSITY_G_CM3: float = 2.4

# Assumed reference moisture at saturation (nominal porosity n ~ 0.45 m3/m3)
REFERENCE_SATURATION_MOISTURE_M3M3: float = 0.45

# Assumed baseline dry apparent cohesion (kPa) for cohesive fine-grained soils
BASELINE_COHESION_KPA: float = 35.0

# Empirical cohesion reduction fraction at full saturation (60% reduction -> c_sat = 14.0 kPa)
COHESION_SATURATION_REDUCTION_FACTOR: float = 0.6

# Classical Prandtl / Terzaghi undrained bearing capacity factor Nc for phi = 0
TERZAGHI_NC: float = 5.7

# Assumed nominal foundation embedment depth D_f (meters)
NOMINAL_FOOTING_DEPTH_M: float = 1.5

# Gravitational acceleration constant (m/s2)
GRAVITY_M_S2: float = 9.81

# Dimensional Surcharge Derivation:
#   Dry density rho_d: g/cm3 = 1000 kg/m3
#   Gravity g: 9.81 m/s2
#   Unit weight gamma: rho_d [g/cm3] * 1000 [kg/m3 per g/cm3] * 9.81 [m/s2] = 9810 * rho_d [N/m3]
#   Unit weight gamma in kN/m3: (9810 * rho_d) / 1000 = 9.81 * rho_d [kN/m3] = 9.81 * rho_d [kPa/m]
#   Surcharge q = gamma * D_f = (9.81 * rho_d [kPa/m]) * 1.5 [m] = rho_d * 9.81 * 1.5 [kPa]
#   Numerically, rho_d [g/cm3] * GRAVITY_M_S2 * NOMINAL_FOOTING_DEPTH_M evaluates directly to kPa.
SURCHARGE_DEPTH_FACTOR: float = GRAVITY_M_S2 * NOMINAL_FOOTING_DEPTH_M  # 9.81 * 1.5 = 14.715 kPa / (g/cm3)

# Trafficability Classification Thresholds (Mean Nominal Bearing Capacity in kPa)
TRAFFICABILITY_HEAVY_RIG_THRESHOLD_KPA: float = 180.0
TRAFFICABILITY_LIGHT_VEHICLE_THRESHOLD_KPA: float = 120.0


class CivilLoadTranslator(BaseDomainTranslator):
    """
    Translates volumetric soil moisture into nominal soil mechanical bearing capacity,
    shear cohesion, and heavy machinery trafficability ratings.

    Geotechnical Caveat & Integrity Statement:
    -------------------------------------------
    1. Heuristic Nature: Bearing capacity is estimated using an uncalibrated Terzaghi-like
       simplification assuming frictionless undrained behavior (phi = 0, Nc = 5.7, Nq = 1.0,
       Ngamma = 0) combined with an empirical cohesion reduction formula. It does NOT represent
       a certified geotechnical site investigation, cone penetrometer test (CPT), or structural
       foundation design.
    2. Factor of Safety (FS): Nominal ultimate bearing capacity (q_ult) is reported WITHOUT
       an engineering Factor of Safety (FS). Standard civil foundation engineering requires
       FS >= 3.0 (q_allowable = q_ult / FS). This output is NOT allowable bearing capacity and
       MUST NOT be used for foundation sizing, roadbed design, or construction permitting.
    3. Soil Lithology & Cohesion: The apparent cohesion formula assumes a fine-grained cohesive
       soil with baseline dry cohesion c0 = 35.0 kPa. It is completely invalid for cohesionless
       granular soils (clean sands and gravels where c = 0).
    4. Surcharge Assumptions: Embedment depth Df = 1.5 m and dry density are applied uniformly;
       variations in moisture with depth and groundwater table elevation are neglected.
    5. Trafficability Grades: Site trafficability ratings (HEAVY_RIG_PERMITTED, LIGHT_VEHICLE_ONLY,
       HAZARDOUS_UNSTABLE_SOIL) are empirical heuristics based on spatial mean bearing capacity;
       they are not calibrated to specific vehicle gross weights, tire pressures, or NATO rating cone indices.
    6. Validity Masks: Computations and spatial mean aggregates strictly exclude masked invalid
       pixels (clouds, shadow, NoData).
    7. Broad Sanity Bounds: Input soil moisture is validated against [0.0, 1.0] m3/m3 as a broad
       numerical sanity check. This does not validate against actual soil-specific porosity.
    """

    def translate(
        self,
        soil_input: Union[DomainInput, np.ndarray, None] = None,
        dry_density_g_cm3: Optional[float] = None,
        soil_moisture: Optional[np.ndarray] = None,
        **kwargs: Any,
    ) -> DomainOutput:
        """
        Translates soil state into civil engineering bearing capacity and trafficability metrics.

        Supported Calling Conventions:
          1. Standardized: translate(soil_input=DomainInput(...))
          2. Legacy Positional: translate(soil_moisture, dry_density_g_cm3=1.6)
          3. Legacy Keyword: translate(soil_moisture=..., dry_density_g_cm3=...)
        """
        logging.info("Translating Soil State to Civil Bearing Capacity & Shear Strength...")

        # 1. Resolve Input Disambiguation
        if "soil_moisture" in kwargs and soil_moisture is None:
            soil_moisture = kwargs.pop("soil_moisture")
        if "dry_density_g_cm3" in kwargs:
            kw_density = kwargs.pop("dry_density_g_cm3")
            if dry_density_g_cm3 is not None and not math.isclose(dry_density_g_cm3, kw_density, rel_tol=1e-5):
                raise ValueError("Conflicting dry_density_g_cm3 passed as positional and keyword argument.")
            dry_density_g_cm3 = kw_density

        if soil_input is None and soil_moisture is not None:
            soil_input = soil_moisture
        elif soil_input is not None and soil_moisture is not None:
            raise ValueError(
                "Conflicting arguments: cannot provide both soil_input and soil_moisture."
            )
        elif soil_input is None:
            raise ValueError("No soil input provided to CivilLoadTranslator.translate.")

        warnings: List[str] = []

        # 2. Normalize to DomainInput
        if isinstance(soil_input, DomainInput):
            if dry_density_g_cm3 is not None:
                if soil_input.dry_density_g_cm3 is not None:
                    if not math.isclose(dry_density_g_cm3, soil_input.dry_density_g_cm3, rel_tol=1e-5):
                        raise ValueError(
                            "Conflicting dry_density_g_cm3 passed: both in DomainInput and as keyword argument."
                        )
                else:
                    soil_input.dry_density_g_cm3 = dry_density_g_cm3
            inp = soil_input
        else:
            inp = self.normalize_input(soil_input, dry_density_g_cm3=dry_density_g_cm3, **kwargs)

        # 3. Resolve and Validate Dry Density
        if inp.dry_density_g_cm3 is None:
            effective_density = DEFAULT_DRY_DENSITY_G_CM3
            warnings.append(
                f"Parameter notice: Default dry density {DEFAULT_DRY_DENSITY_G_CM3:.2f} g/cm3 applied; "
                f"in-situ dry density varies significantly by soil compaction and lithology."
            )
        else:
            effective_density = inp.dry_density_g_cm3
            if not isinstance(effective_density, (int, float)):
                raise TypeError(
                    f"dry_density_g_cm3 must be numeric, got {type(effective_density).__name__}."
                )
            if not math.isfinite(effective_density) or effective_density <= 0.0:
                raise ValueError(
                    f"dry_density_g_cm3 must be positive and finite, got {effective_density}."
                )
            if (
                effective_density < TYPICAL_MIN_DRY_DENSITY_G_CM3
                or effective_density > TYPICAL_MAX_DRY_DENSITY_G_CM3
            ):
                warnings.append(
                    f"Parameter notice: dry_density_g_cm3 ({effective_density:.2f} g/cm3) falls outside "
                    f"typical mineral soil range [{TYPICAL_MIN_DRY_DENSITY_G_CM3:.1f}, {TYPICAL_MAX_DRY_DENSITY_G_CM3:.1f}] g/cm3."
                )

        # 4. Validate Physical Variable and Units
        norm_var = inp.state_variable.strip().lower()
        if norm_var not in SUPPORTED_STATE_VARIABLES:
            raise ValueError(
                f"Unsupported state variable '{inp.state_variable}' for CivilLoadTranslator. "
                f"Supported variables: {sorted(SUPPORTED_STATE_VARIABLES)}."
            )

        norm_unit = inp.unit.strip().lower()
        if norm_unit not in SUPPORTED_UNITS:
            raise ValueError(
                f"Unsupported unit '{inp.unit}' for volumetric soil moisture. "
                f"Expected decimal fraction in m3/m3 (e.g. 0.25, not 25%). "
                f"Supported units: {sorted(SUPPORTED_UNITS)}."
            )

        soil_arr = inp.soil_state

        # 5. Handle and Validate Mask
        if inp.valid_data_mask is not None:
            valid_mask = inp.valid_data_mask
            if not np.any(valid_mask):
                raise ValueError("valid_data_mask contains 0 valid pixels. Translation rejected.")
        else:
            valid_mask = np.ones(soil_arr.shape, dtype=bool)

        valid_moisture = soil_arr[valid_mask]

        # 6. Broad Physical Sanity Bounds Check on Valid Soil Moisture
        # Note: [0.0, 1.0] m3/m3 enforces numerical sanity (volume fraction cannot be negative
        # or exceed total bulk volume). This does NOT validate against actual soil-specific porosity.
        if valid_moisture.min() < 0.0 or valid_moisture.max() > 1.0:
            raise ValueError(
                f"Soil moisture values [{valid_moisture.min():.4f}, {valid_moisture.max():.4f}] "
                f"fall outside broad physical sanity bounds [0.0, 1.0] m3/m3 for volumetric water content. "
                f"Note: This check enforces numerical plausibility only; soil-specific porosity is not validated."
            )

        # 7. Geotechnical Bearing Capacity & Cohesion Calculations (on valid pixels only)
        # Saturation ratio relative to nominal reference porosity (0.45 m3/m3)
        valid_sat_ratio = np.clip(valid_moisture / REFERENCE_SATURATION_MOISTURE_M3M3, 0.0, 1.0)

        # Effective cohesion degradation: c = c0 * (1 - 0.6 * S_r)
        valid_cohesion = BASELINE_COHESION_KPA * (
            1.0 - COHESION_SATURATION_REDUCTION_FACTOR * valid_sat_ratio
        )

        # Surcharge term: q = gamma_dry * D_f = (rho_d [g/cm3] * 9.81 [m/s2]) * 1.5 [m] (in kPa)
        surcharge_kpa = float(effective_density * SURCHARGE_DEPTH_FACTOR)

        # Nominal ultimate bearing capacity: q_ult = c * Nc + q
        valid_bearing = valid_cohesion * TERZAGHI_NC + surcharge_kpa

        # Rasters populated with NaN at masked invalid pixels
        bearing_raster = np.full(soil_arr.shape, np.nan, dtype=np.float32)
        cohesion_raster = np.full(soil_arr.shape, np.nan, dtype=np.float32)

        bearing_raster[valid_mask] = valid_bearing.astype(np.float32)
        cohesion_raster[valid_mask] = valid_cohesion.astype(np.float32)

        # Aggregates computed strictly over valid pixels
        mean_bearing = float(np.mean(valid_bearing))
        mean_cohesion = float(np.mean(valid_cohesion))

        # 8. Site Trafficability Classification (strictly from valid pixels mean bearing)
        if mean_bearing > TRAFFICABILITY_HEAVY_RIG_THRESHOLD_KPA:
            trafficability = "HEAVY_RIG_PERMITTED"
        elif mean_bearing > TRAFFICABILITY_LIGHT_VEHICLE_THRESHOLD_KPA:
            trafficability = "LIGHT_VEHICLE_ONLY"
        else:
            trafficability = "HAZARDOUS_UNSTABLE_SOIL"

        # 9. Geotechnical Limitation Warnings
        warnings.append(
            "Heuristic notice: Bearing capacity is a simplified Terzaghi-like heuristic assuming "
            "phi=0 undrained behavior (Nc=5.7, Nq=1.0, Ngamma=0) with empirical cohesion degradation; "
            "not a validated geotechnical site investigation or structural foundation design."
        )
        warnings.append(
            "Safety notice: Nominal ultimate bearing capacity is reported without a geotechnical Factor of Safety (FS). "
            "Allowable bearing capacity in engineering practice typically requires FS >= 3.0; "
            "this output MUST NOT be used for foundation design, roadbed design, or construction permitting."
        )
        warnings.append(
            "Parameter notice: Effective cohesion formula assumes fine-grained cohesive soil with dry cohesion c0=35 kPa; "
            "completely invalid for cohesionless coarse-grained soils (clean sands/gravels where c=0)."
        )
        warnings.append(
            "Heuristic notice: Site trafficability classification is an uncalibrated heuristic based on "
            "spatial mean bearing capacity; not calibrated to vehicle axle loads, contact pressures, or rating cone indices."
        )

        logging.info(
            f"Civil Engineering Translation Complete:\n"
            f"   -> Mean Nominal Bearing Capacity: {mean_bearing:.2f} kPa\n"
            f"   -> Mean Shear Cohesion: {mean_cohesion:.2f} kPa\n"
            f"   -> Surcharge: {surcharge_kpa:.2f} kPa (dry density {effective_density:.2f} g/cm3)\n"
            f"   -> Site Trafficability Grade: {trafficability}"
        )

        # 10. Format Domain Output Metrics (preserving legacy keys)
        metrics: Dict[str, Any] = {
            "bearing_capacity_matrix_kPa": bearing_raster,
            "effective_cohesion_kPa": cohesion_raster,
            "site_trafficability": trafficability,
            "mean_bearing_kPa": mean_bearing,
            "mean_effective_cohesion_kPa": mean_cohesion,
            "surcharge_kPa": surcharge_kpa,
            "dry_density_g_cm3": effective_density,
        }

        # 11. Metadata Preservation
        metadata: Dict[str, Any] = {}
        if inp.crs is not None:
            metadata["crs"] = inp.crs
        if inp.transform is not None:
            metadata["transform"] = inp.transform
        if inp.bounds is not None:
            metadata["bounds"] = inp.bounds
        if inp.resolution is not None:
            metadata["resolution"] = inp.resolution
        if inp.acquisition_datetime is not None:
            metadata["acquisition_datetime"] = inp.acquisition_datetime
        if inp.provenance is not None:
            metadata["provenance"] = inp.provenance

        # 12. Uncertainty Semantics
        uncertainty_dict: Optional[Dict[str, Any]] = None
        if inp.uncertainty is not None:
            uncertainty_dict = {
                "input_soil_state_uncertainty": inp.uncertainty,
                "input_uncertainty_type": (
                    inp.uncertainty_type if inp.uncertainty_type is not None else "unspecified"
                ),
                "propagation_status": "unpropagated",
                "note": (
                    "Input state uncertainty is preserved directly from upstream state estimation. "
                    "Downstream geotechnical bearing capacity, cohesion, and trafficability outputs do NOT "
                    "have calibrated propagated uncertainty; no error propagation model is implemented for civil heuristics."
                ),
            }
            if inp.uncertainty_type is None:
                warnings.append(
                    "Uncertainty notice: Input uncertainty provided without declared uncertainty_type; "
                    "statistical units and interpretation remain unspecified."
                )

        return DomainOutput(
            domain="civil",
            metrics=metrics,
            valid_data_mask=inp.valid_data_mask,
            metadata=metadata,
            uncertainty=uncertainty_dict,
            warnings=warnings,
        )


# Self-Test Execution Module
if __name__ == "__main__":
    print("\n--- Testing Hardened Civil Load Translator Module ---")
    translator = CivilLoadTranslator()

    mock_moisture = np.random.uniform(0.15, 0.40, size=(120, 120)).astype(np.float32)

    # 1. Test DomainInput path
    inp_obj = DomainInput(
        soil_state=mock_moisture,
        dry_density_g_cm3=1.65,
        crs="EPSG:32645",
        uncertainty=0.02,
        uncertainty_type="ensemble_variance",
    )
    res_modern = translator.translate(inp_obj)
    assert res_modern.domain == "civil"
    assert "bearing_capacity_matrix_kPa" in res_modern
    assert res_modern["bearing_capacity_matrix_kPa"].shape == (120, 120)
    assert res_modern.metadata.get("crs") == "EPSG:32645"
    assert res_modern.uncertainty["input_soil_state_uncertainty"] == 0.02
    print("  [OK] Modern DomainInput call passed.")

    # 2. Test Legacy Positional Call
    res_legacy = translator.translate(mock_moisture, 1.6)
    assert "bearing_capacity_matrix_kPa" in res_legacy
    assert "site_trafficability" in res_legacy
    print("  [OK] Legacy positional call compatibility passed.")

    # 3. Test Legacy Default Density Call
    res_default = translator.translate(mock_moisture)
    assert res_default["dry_density_g_cm3"] == 1.6
    print("  [OK] Default dry density applied cleanly.")

    print("\n[SUCCESS] Civil Translator: ALL HARDENED OPERATIONAL CHECKS PASSED!\n")
