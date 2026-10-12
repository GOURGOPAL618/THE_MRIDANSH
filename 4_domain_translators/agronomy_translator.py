# THE MRIDANSH - AGRONOMY TRANSLATOR
# Module: 4_domain_translators/agronomy_translator.py
# AETHER-MRID1607X Core Engine

import logging
from typing import Any, Dict, List, Optional, Set, Union

import numpy as np

try:
    from .base import BaseDomainTranslator, DomainInput, DomainOutput
except ImportError:
    from base import BaseDomainTranslator, DomainInput, DomainOutput

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Supported physical state variables for the Agriculture domain
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

# Agronomic Heuristic Constants
DEFAULT_TARGET_MOISTURE_M3M3: float = 0.35
ASSUMED_ROOT_ZONE_DEPTH_M: float = 0.10  # Assumed generic 10 cm root zone

# Dimensional Derivation for Irrigation Multiplier:
#   Area: 1 hectare = 10,000 m2
#   Depth: assumed root zone = 0.10 m (10 cm)
#   Soil Volume: 10,000 m2 * 0.10 m = 1,000 m3 soil / ha
#   Unit Deficit: 1.0 m3 water / m3 soil
#   Water Volume: 1,000 m3 water / ha
#   Conversion to Liters: 1 m3 water = 1,000 Liters
#   Total Conversion Factor: 1,000 m3 * 1,000 L/m3 = 1,000,000 L/ha per unit deficit
LITERS_PER_HA_PER_UNIT_DEFICIT: float = 10000.0 * ASSUMED_ROOT_ZONE_DEPTH_M * 1000.0  # 1,000,000.0 L/ha


class AgronomyHealthTranslator(BaseDomainTranslator):
    """
    Translates volumetric soil moisture and optical spectral indices
    into agronomic health vectors, irrigation deficit indicators, and
    regional drought classifications.

    Scientific Caveat & Integrity Statement:
    ----------------------------------------
    1. Heuristic Nature: Crop Health Index is an uncalibrated linear blend
       of soil moisture and NDVI. It does not represent a field-validated
       measurement of plant physiological stress or crop yield potential.
    2. Irrigation Deficit: Evaluated as an uncalibrated theoretical water
       volume relative to a fixed target of 0.35 m3/m3 over an assumed 0.10 m
       root zone (1,000,000 L/ha per unit volumetric deficit). It is not a
       validated agronomic irrigation prescription.
    3. Missing NDVI: When NDVI is absent, crop health indices are explicitly
       omitted (set to None) rather than computing on fabricated values.
    4. Validity Masks: Computations and regional averages strictly exclude
       masked invalid pixels (clouds, shadow, NoData).
    5. Broad Sanity Bounds: Input soil moisture is validated against [0.0, 1.0] m3/m3
       as a broad numerical sanity check. This does not validate against actual
       soil-specific porosity or field capacity, which require soil texture data.
    """

    def translate(
        self,
        soil_input: Union[DomainInput, np.ndarray, None] = None,
        ndvi: Optional[np.ndarray] = None,
        soil_moisture: Optional[np.ndarray] = None,
        **kwargs: Any,
    ) -> DomainOutput:
        """
        Translates soil state into agricultural health and irrigation metrics.

        Supported Calling Conventions:
          1. Standardized: translate(soil_input=DomainInput(...))
          2. Legacy Positional: translate(soil_moisture, ndvi)
          3. Legacy Keyword: translate(soil_moisture=..., ndvi=...)
        """
        logging.info("🌾 Translating Soil State to Agronomy Health & Irrigation Vectors...")

        # 1. Resolve Input Disambiguation
        if soil_input is None and soil_moisture is not None:
            soil_input = soil_moisture
        elif isinstance(soil_input, DomainInput) and soil_moisture is not None:
            raise ValueError(
                "Conflicting arguments: cannot provide both DomainInput as soil_input and soil_moisture."
            )
        elif soil_input is None:
            raise ValueError("No soil input provided to AgronomyHealthTranslator.translate.")

        # 2. Normalize to DomainInput
        if isinstance(soil_input, DomainInput):
            # If ndvi was also passed as keyword, check for conflict with soil_input.ndvi
            if ndvi is not None and soil_input.ndvi is not None:
                if not np.array_equal(ndvi, soil_input.ndvi):
                    raise ValueError("Conflicting NDVI passed: both in DomainInput and as keyword argument.")
            elif ndvi is not None and soil_input.ndvi is None:
                soil_input.ndvi = ndvi
            inp = soil_input
        else:
            inp = self.normalize_input(soil_input, ndvi=ndvi, **kwargs)

        # 3. Validate Physical Variable and Units
        norm_var = inp.state_variable.strip().lower()
        if norm_var not in SUPPORTED_STATE_VARIABLES:
            raise ValueError(
                f"Unsupported state variable '{inp.state_variable}' for AgronomyHealthTranslator. "
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

        # 4. Handle and Validate Mask
        if inp.valid_data_mask is not None:
            valid_mask = inp.valid_data_mask
            if not np.any(valid_mask):
                raise ValueError("valid_data_mask contains 0 valid pixels. Translation rejected.")
        else:
            valid_mask = np.ones(soil_arr.shape, dtype=bool)

        valid_moisture = soil_arr[valid_mask]

        # 5. Broad Physical Sanity Bounds Check on Valid Soil Moisture
        # Note: [0.0, 1.0] m3/m3 enforces numerical sanity (volume fraction cannot be negative
        # or exceed total bulk volume). This does NOT validate against actual soil-specific porosity.
        if valid_moisture.min() < 0.0 or valid_moisture.max() > 1.0:
            raise ValueError(
                f"Soil moisture values [{valid_moisture.min():.4f}, {valid_moisture.max():.4f}] "
                f"fall outside broad physical sanity bounds [0.0, 1.0] m3/m3 for volumetric water content. "
                f"Note: This check enforces numerical plausibility only; soil-specific porosity is not validated."
            )

        warnings: List[str] = []

        # 6. Validate and Process NDVI
        ndvi_arr = inp.ndvi
        has_ndvi = ndvi_arr is not None

        if has_ndvi:
            if not isinstance(ndvi_arr, np.ndarray):
                raise TypeError(f"ndvi must be a numpy.ndarray, got {type(ndvi_arr).__name__}.")
            if ndvi_arr.shape != soil_arr.shape:
                raise ValueError(
                    f"ndvi shape {ndvi_arr.shape} does not match soil_state shape {soil_arr.shape}."
                )
            valid_ndvi = ndvi_arr[valid_mask]
            if not np.isfinite(valid_ndvi).all():
                raise ValueError("ndvi contains non-finite values (NaN or Inf) on valid pixels.")
            if valid_ndvi.min() < -1.0 or valid_ndvi.max() > 1.0:
                raise ValueError(
                    f"ndvi values [{valid_ndvi.min():.4f}, {valid_ndvi.max():.4f}] "
                    f"are outside valid physical range [-1.0, 1.0]."
                )

            # Heuristic Crop Health Index Score (0 - 100%)
            health_score_raster = np.full(soil_arr.shape, np.nan, dtype=np.float32)
            computed_health = np.clip(
                (valid_moisture * 0.5 + valid_ndvi * 0.5) * 100.0, 0.0, 100.0
            )
            health_score_raster[valid_mask] = computed_health.astype(np.float32)
            mean_health_score: Optional[float] = float(np.mean(computed_health))
            warnings.append(
                "Heuristic notice: Crop health index is an uncalibrated 50/50 linear blend of soil moisture "
                "and NDVI; not a validated physiological plant stress measurement."
            )
        else:
            health_score_raster = None
            mean_health_score = None
            warnings.append(
                "Input notice: NDVI was not supplied; crop_health_matrix and mean_health_score are omitted "
                "(no fabricated default NDVI was applied)."
            )

        # 7. Mask-Aware Irrigation Deficit (Target Optimal Moisture = 0.35)
        optimal_moisture = DEFAULT_TARGET_MOISTURE_M3M3
        irrigation_raster = np.full(soil_arr.shape, np.nan, dtype=np.float32)
        deficit = np.maximum(0.0, optimal_moisture - valid_moisture)
        # 10,000 m2/ha * 0.10 m root depth * 1,000 L/m3 = 1,000,000 L/ha per unit deficit
        computed_irrigation = deficit * LITERS_PER_HA_PER_UNIT_DEFICIT
        irrigation_raster[valid_mask] = computed_irrigation.astype(np.float32)
        mean_irrigation = float(np.mean(computed_irrigation))
        warnings.append(
            f"Heuristic notice: Irrigation required is an uncalibrated theoretical estimate relative to "
            f"fixed {optimal_moisture:.2f} m3/m3 target over assumed {ASSUMED_ROOT_ZONE_DEPTH_M:.2f} m root zone "
            f"({LITERS_PER_HA_PER_UNIT_DEFICIT:,.0f} L/ha per unit deficit); not a validated agronomic prescription."
        )

        # 8. Mask-Aware Regional Drought Risk Classification
        mean_moisture = float(np.mean(valid_moisture))
        if mean_moisture < 0.15:
            drought_risk = "CRITICAL_DROUGHT"
        elif mean_moisture < 0.25:
            drought_risk = "MODERATE_STRESS"
        else:
            drought_risk = "OPTIMAL_HYDRATION"

        warnings.append(
            "Heuristic notice: Drought risk status is based on an unweighted regional mean moisture; "
            "does not account for localized drought pockets or soil-specific wilting points."
        )

        logging.info(
            f"✅ Agronomy Translation Complete!\n"
            f"   -> Regional Mean Moisture: {mean_moisture:.4f} m3/m3\n"
            f"   -> Mean Irrigation Needed: {mean_irrigation:.2f} L/ha\n"
            f"   -> Regional Drought Risk: {drought_risk}"
        )

        # 9. Format Domain Output Metrics
        metrics: Dict[str, Any] = {
            "irrigation_required_l_ha": irrigation_raster,
            "drought_risk_status": drought_risk,
            "mean_moisture_m3m3": mean_moisture,
            "mean_irrigation_l_ha": mean_irrigation,
        }
        if health_score_raster is not None:
            metrics["crop_health_matrix"] = health_score_raster
        else:
            metrics["crop_health_matrix"] = None

        if mean_health_score is not None:
            metrics["mean_health_score"] = mean_health_score
        else:
            metrics["mean_health_score"] = None

        # 10. Metadata and Uncertainty Propagation
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

        uncertainty_dict: Optional[Dict[str, Any]] = None
        if inp.uncertainty is not None:
            uncertainty_dict = {
                "input_soil_state_uncertainty": inp.uncertainty,
                "input_uncertainty_type": inp.uncertainty_type if inp.uncertainty_type is not None else "unspecified",
                "propagation_status": "unpropagated",
                "note": (
                    "Input state uncertainty is preserved directly from upstream state estimation. "
                    "Downstream crop health and irrigation outputs do NOT have calibrated propagated "
                    "uncertainty; no error propagation model is implemented for agricultural heuristics."
                ),
            }
            if inp.uncertainty_type is None:
                warnings.append(
                    "Uncertainty notice: Input uncertainty provided without declared uncertainty_type; "
                    "statistical units and interpretation remain unspecified."
                )

        return DomainOutput(
            domain="agriculture",
            metrics=metrics,
            valid_data_mask=inp.valid_data_mask,
            metadata=metadata,
            uncertainty=uncertainty_dict,
            warnings=warnings,
        )


# Self-Test Execution Module
if __name__ == "__main__":
    print("\n--- Testing Hardened Agronomy Health Translator Module ---")
    translator = AgronomyHealthTranslator()

    mock_moisture = np.random.uniform(0.15, 0.38, size=(64, 64)).astype(np.float32)
    mock_ndvi = np.random.uniform(0.30, 0.85, size=(64, 64)).astype(np.float32)

    # 1. Test DomainInput Path
    inp_obj = DomainInput(
        soil_state=mock_moisture,
        ndvi=mock_ndvi,
        crs="EPSG:32645",
        uncertainty=0.03,
        uncertainty_type="ensemble_variance",
    )
    res_modern = translator.translate(inp_obj)
    assert res_modern.domain == "agriculture"
    assert res_modern["crop_health_matrix"] is not None
    assert res_modern["crop_health_matrix"].shape == (64, 64)
    assert res_modern.metadata.get("crs") == "EPSG:32645"
    assert res_modern.uncertainty["input_soil_state_uncertainty"] == 0.03
    print("  [OK] Modern DomainInput call passed.")

    # 2. Test Legacy Call Path
    res_legacy = translator.translate(mock_moisture, mock_ndvi)
    assert res_legacy["crop_health_matrix"] is not None
    assert "drought_risk_status" in res_legacy
    print("  [OK] Legacy call compatibility passed.")

    # 3. Test Missing NDVI Call Path (No fabricated defaults)
    res_no_ndvi = translator.translate(mock_moisture)
    assert res_no_ndvi["crop_health_matrix"] is None
    assert res_no_ndvi["irrigation_required_l_ha"] is not None
    print("  [OK] Missing NDVI omitted gracefully without fabricated defaults.")

    print("\n[SUCCESS] Agronomy Translator: ALL HARDENED OPERATIONAL CHECKS PASSED!\n")
