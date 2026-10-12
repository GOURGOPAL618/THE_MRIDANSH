"""
THE MRIDANSH : Dashboard Metric Presentation Contract & Agriculture Adapter (Task 03)
Enforces typed metrics with explicit semantics, units, provenance, and data states.
"""

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import numpy as np
from runtime_cache import DataState


@dataclass(frozen=True)
class DashboardMetric:
    """Standardized Presentation Contract for Dashboard Scientific Metrics.

    Guarantees that every metric displayed in the dashboard carries explicit units,
    provenance, and data state without guessing or numeric fallback placeholders.
    """

    metric_id: str
    label: str
    value: Optional[Any]  # None indicates explicit absence / unavailable
    unit: str
    data_state: DataState
    provenance: str
    timestamp: Optional[str] = None
    is_valid: bool = True
    uncertainty: Optional[Any] = None
    uncertainty_type: Optional[str] = None
    note: Optional[str] = None

    def __post_init__(self) -> None:
        # Enforce that LIVE cannot be assigned to demo or unknown provenance
        if self.data_state == DataState.LIVE:
            if "demo" in self.provenance.lower() or "synthetic" in self.provenance.lower():
                raise ValueError(
                    f"Metric '{self.metric_id}' has data_state=LIVE but demo/synthetic provenance: '{self.provenance}'"
                )

        # Enforce that numeric placeholders (0, -1, 0.5) must not masquerade as unavailable
        if self.data_state == DataState.UNAVAILABLE and self.value is not None:
            raise ValueError(
                f"Metric '{self.metric_id}' has data_state=UNAVAILABLE but non-None value: {self.value}"
            )

    @property
    def is_available(self) -> bool:
        """True only if value is present and data_state is LIVE or DEMO with valid status."""
        return (
            self.value is not None
            and self.is_valid
            and self.data_state not in (DataState.UNAVAILABLE, DataState.ERROR)
        )

    @property
    def is_demo(self) -> bool:
        """True if the metric is explicit demonstration scaffolding."""
        return self.data_state == DataState.DEMO

    @property
    def display_value(self) -> str:
        """Returns human-readable formatted string or explicit 'Unavailable' / 'Invalid'."""
        if not self.is_available:
            if not self.is_valid or self.data_state == DataState.ERROR:
                return "Invalid Data"
            return "Unavailable"

        if isinstance(self.value, float):
            if not math.isfinite(self.value):
                return "Invalid (NaN/Inf)"

            if self.unit in ("m3/m3", "m³/m³"):
                return f"{self.value * 100:.1f}% ({self.value:.3f} m³/m³)"
            if self.unit == "%":
                return f"{self.value:.2f}%"
            if self.unit == "L/ha":
                return f"{self.value:,.0f} L/ha"
            if self.unit == "score [0.0 - 1.0]":
                return f"{self.value:.2f}"
            if self.unit == "index [0.0 - 1.0]":
                return f"{self.value * 100:.1f}% ({self.value:.2f})"
            if self.unit in ("g/cm3", "g/cm³"):
                return f"{self.value:.2f} g/cm³"
            if self.unit in ("kg/m3", "kg/m³"):
                return f"{self.value:.1f} kg/m³"
            if self.unit == "kPa":
                return f"{self.value:.1f} kPa"
            return f"{self.value:.3f} {self.unit}".strip()

        if isinstance(self.value, (int, str)):
            return f"{self.value} {self.unit}".strip() if self.unit else str(self.value)

        return "Array / Complex Object"


def build_agronomy_metrics(soil_state: Any = None, agronomy_output: Any = None) -> Dict[str, DashboardMetric]:
    """Extracts and normalizes Agriculture metrics into typed DashboardMetric objects.

    Accepts:
      - DomainOutput instances from 4_domain_translators
      - Dictionary containers from runtime_cache or API
      - None / empty inputs for disconnected state verification
    """
    metrics_map: Dict[str, DashboardMetric] = {}

    # Determine general data state and provenance from output container
    is_demo_mode = False
    base_state = DataState.UNAVAILABLE
    base_provenance = "No source connected"

    output_metrics: Dict[str, Any] = {}
    output_metadata: Dict[str, Any] = {}
    output_uncertainty: Optional[Dict[str, Any]] = None

    if agronomy_output is not None:
        if hasattr(agronomy_output, "metrics"):
            # DomainOutput instance
            output_metrics = getattr(agronomy_output, "metrics", {}) or {}
            output_metadata = getattr(agronomy_output, "metadata", {}) or {}
            output_uncertainty = getattr(agronomy_output, "uncertainty", None)
            base_provenance = output_metadata.get("provenance", "Domain Translator Pipeline")
            base_state = DataState.LIVE
        elif isinstance(agronomy_output, dict):
            output_metrics = agronomy_output
            is_demo_mode = agronomy_output.get("is_demo", False) or agronomy_output.get("data_state") == DataState.DEMO
            if "data_state" in agronomy_output:
                base_state = agronomy_output["data_state"]
            elif is_demo_mode:
                base_state = DataState.DEMO
            elif any(k in agronomy_output for k in ["root_zone_moisture", "mean_soil_moisture", "mean_moisture_m3m3", "mean_health_score", "irrigation_required_l_ha"]):
                base_state = DataState.LIVE
            else:
                base_state = DataState.UNAVAILABLE
            base_provenance = agronomy_output.get(
                "provenance", "Synthetic Demonstration Scaffolding" if is_demo_mode else "Dictionary Container"
            )

    # 1. Root-Zone Soil Moisture (Volumetric Fraction m3/m3)
    raw_moisture = (
        output_metrics.get("root_zone_moisture")
        or output_metrics.get("mean_soil_moisture")
        or output_metrics.get("mean_moisture_m3m3")
    )
    if raw_moisture is not None:
        try:
            m_val = float(raw_moisture)
            if math.isfinite(m_val) and 0.0 <= m_val <= 1.0:
                metrics_map["root_zone_moisture"] = DashboardMetric(
                    metric_id="root_zone_moisture",
                    label="Root-Zone Volumetric Moisture",
                    value=m_val,
                    unit="m³/m³",
                    data_state=base_state,
                    provenance=base_provenance,
                    note="Volumetric water fraction theta. Physical state variable.",
                )
            else:
                metrics_map["root_zone_moisture"] = DashboardMetric(
                    metric_id="root_zone_moisture",
                    label="Root-Zone Volumetric Moisture",
                    value=None,
                    unit="m³/m³",
                    data_state=DataState.ERROR,
                    provenance=base_provenance,
                    is_valid=False,
                    note="Moisture value is non-finite or outside physical [0, 1] range.",
                )
        except (ValueError, TypeError):
            metrics_map["root_zone_moisture"] = DashboardMetric(
                metric_id="root_zone_moisture",
                label="Root-Zone Volumetric Moisture",
                value=None,
                unit="m³/m³",
                data_state=DataState.ERROR,
                provenance=base_provenance,
                is_valid=False,
                note="Non-numeric soil moisture input encountered.",
            )
    else:
        metrics_map["root_zone_moisture"] = DashboardMetric(
            metric_id="root_zone_moisture",
            label="Root-Zone Volumetric Moisture",
            value=None,
            unit="m³/m³",
            data_state=DataState.UNAVAILABLE,
            provenance="Physical inference pipeline disconnected",
            note="Soil-moisture estimate unavailable — no verified physical prediction source is connected.",
        )

    # 2. Optical Surface Canopy Reflectance (NDVI)
    raw_ndvi = output_metrics.get("ndvi")
    if raw_ndvi is not None:
        try:
            ndvi_val = float(raw_ndvi) if not isinstance(raw_ndvi, np.ndarray) else float(np.nanmean(raw_ndvi))
            if math.isfinite(ndvi_val) and -1.0 <= ndvi_val <= 1.0:
                metrics_map["ndvi"] = DashboardMetric(
                    metric_id="ndvi",
                    label="Canopy Vegetation Index (NDVI)",
                    value=ndvi_val,
                    unit="dimensionless [-1, 1]",
                    data_state=base_state,
                    provenance=base_provenance,
                    note="Optical spectral band ratio (NIR - Red) / (NIR + Red).",
                )
            else:
                metrics_map["ndvi"] = DashboardMetric(
                    metric_id="ndvi",
                    label="Canopy Vegetation Index (NDVI)",
                    value=None,
                    unit="dimensionless [-1, 1]",
                    data_state=DataState.ERROR,
                    provenance=base_provenance,
                    is_valid=False,
                    note="NDVI out of valid [-1, 1] range or non-finite.",
                )
        except Exception:
            metrics_map["ndvi"] = DashboardMetric(
                metric_id="ndvi",
                label="Canopy Vegetation Index (NDVI)",
                value=None,
                unit="dimensionless [-1, 1]",
                data_state=DataState.ERROR,
                provenance=base_provenance,
                is_valid=False,
                note="Invalid NDVI input array/value.",
            )
    else:
        metrics_map["ndvi"] = DashboardMetric(
            metric_id="ndvi",
            label="Canopy Vegetation Index (NDVI)",
            value=None,
            unit="dimensionless [-1, 1]",
            data_state=DataState.UNAVAILABLE,
            provenance="Optical satellite ingestion disconnected",
            note="Optical canopy reflectance (NDVI) is not connected.",
        )

    # 3. Agronomic Crop Health Score (Requires paired Moisture + NDVI)
    raw_health = output_metrics.get("mean_health_score")
    if raw_health is not None and metrics_map["ndvi"].is_available:
        try:
            h_val = float(raw_health)
            if math.isfinite(h_val) and 0.0 <= h_val <= 1.0:
                metrics_map["crop_health_score"] = DashboardMetric(
                    metric_id="crop_health_score",
                    label="Agronomic Crop Health Index",
                    value=h_val,
                    unit="score [0.0 - 1.0]",
                    data_state=base_state,
                    provenance=base_provenance,
                    note="Heuristic index combining soil moisture and canopy greenness.",
                )
            else:
                metrics_map["crop_health_score"] = DashboardMetric(
                    metric_id="crop_health_score",
                    label="Agronomic Crop Health Index",
                    value=None,
                    unit="score [0.0 - 1.0]",
                    data_state=DataState.ERROR,
                    provenance=base_provenance,
                    is_valid=False,
                    note="Crop health score outside [0, 1] range or non-finite.",
                )
        except Exception:
            metrics_map["crop_health_score"] = DashboardMetric(
                metric_id="crop_health_score",
                label="Agronomic Crop Health Index",
                value=None,
                unit="score [0.0 - 1.0]",
                data_state=DataState.ERROR,
                provenance=base_provenance,
                is_valid=False,
                note="Invalid crop health score input.",
            )
    else:
        metrics_map["crop_health_score"] = DashboardMetric(
            metric_id="crop_health_score",
            label="Agronomic Crop Health Index",
            value=None,
            unit="score [0.0 - 1.0]",
            data_state=DataState.UNAVAILABLE,
            provenance="Agronomic heuristic evaluation",
            note="Crop health indicator unavailable — requires paired moisture and optical NDVI inputs.",
        )

    # 4. Theoretical Irrigation Deficit (L/ha)
    raw_irrig = output_metrics.get("irrigation_required_l_ha")
    if raw_irrig is not None and metrics_map["root_zone_moisture"].is_available:
        try:
            irrig_val = float(raw_irrig) if not isinstance(raw_irrig, np.ndarray) else float(np.nanmean(raw_irrig))
            if math.isfinite(irrig_val) and irrig_val >= 0.0:
                metrics_map["irrigation_required_l_ha"] = DashboardMetric(
                    metric_id="irrigation_required_l_ha",
                    label="Theoretical Irrigation Deficit",
                    value=irrig_val,
                    unit="L/ha",
                    data_state=base_state,
                    provenance=base_provenance,
                    note=(
                        "Theoretical water volume to reach target field capacity (0.35 m3/m3) "
                        "over assumed 10 cm root zone. Not an official field prescription."
                    ),
                )
            else:
                metrics_map["irrigation_required_l_ha"] = DashboardMetric(
                    metric_id="irrigation_required_l_ha",
                    label="Theoretical Irrigation Deficit",
                    value=None,
                    unit="L/ha",
                    data_state=DataState.ERROR,
                    provenance=base_provenance,
                    is_valid=False,
                    note="Irrigation deficit calculation yielded non-finite or negative value.",
                )
        except Exception:
            metrics_map["irrigation_required_l_ha"] = DashboardMetric(
                metric_id="irrigation_required_l_ha",
                label="Theoretical Irrigation Deficit",
                value=None,
                unit="L/ha",
                data_state=DataState.ERROR,
                provenance=base_provenance,
                is_valid=False,
                note="Invalid irrigation calculation input.",
            )
    else:
        metrics_map["irrigation_required_l_ha"] = DashboardMetric(
            metric_id="irrigation_required_l_ha",
            label="Theoretical Irrigation Deficit",
            value=None,
            unit="L/ha",
            data_state=DataState.UNAVAILABLE,
            provenance="Deficit calculation disconnected",
            note="Irrigation deficit unavailable — physical soil moisture input is disconnected.",
        )

    # 5. Regional Drought Risk Status
    raw_drought = output_metrics.get("drought_risk_status")
    if raw_drought is not None and metrics_map["root_zone_moisture"].is_available:
        metrics_map["drought_risk_status"] = DashboardMetric(
            metric_id="drought_risk_status",
            label="Drought Risk Classification",
            value=str(raw_drought),
            unit="category",
            data_state=base_state,
            provenance=base_provenance,
            note="Threshold classification derived from volumetric moisture.",
        )
    else:
        metrics_map["drought_risk_status"] = DashboardMetric(
            metric_id="drought_risk_status",
            label="Drought Risk Classification",
            value=None,
            unit="category",
            data_state=DataState.UNAVAILABLE,
            provenance="Drought assessment disconnected",
            note="Drought risk category unavailable.",
        )

    # 6. Biogeochemical Soil Nutrients (NPK) & Organic Carbon — Genuinely Unavailable
    for nut_id, nut_label in [
        ("nitrogen_level", "Available Soil Nitrogen (N)"),
        ("phosphorus_level", "Available Soil Phosphorus (P)"),
        ("potassium_level", "Available Soil Potassium (K)"),
    ]:
        metrics_map[nut_id] = DashboardMetric(
            metric_id=nut_id,
            label=nut_label,
            value=None,
            unit="kg/ha",
            data_state=DataState.UNAVAILABLE,
            provenance="Chemical soil spectroscopy disconnected",
            note="Chemical nutrient sensing is unavailable. The AETHER engine models soil hydrology, not biochemical soil nutrients.",
        )

    metrics_map["organic_carbon"] = DashboardMetric(
        metric_id="organic_carbon",
        label="Soil Organic Carbon Content",
        value=None,
        unit="%",
        data_state=DataState.UNAVAILABLE,
        provenance="Laboratory soil testing disconnected",
        note="Soil organic carbon measurements are disconnected.",
    )

    return metrics_map


# ---------------------------------------------------------------------------
# Civil & Geotechnical Presentation Adapters & Dimensional Conversions (Task 04)
# ---------------------------------------------------------------------------

SUPPORTED_DENSITY_UNITS = {"g/cm3", "g/cm³", "kg/m3", "kg/m³", "mg/m3", "mg/m³"}


def convert_soil_bulk_density(value: float, from_unit: str, to_unit: str) -> float:
    """Dimensionally verified conversion of soil bulk density.

    Supported units:
      - 'g/cm³' / 'g/cm3' (grams per cubic centimeter)
      - 'kg/m³' / 'kg/m3' (kilograms per cubic meter)
      - 'Mg/m³' / 'Mg/m3' (megagrams per cubic meter, 1 Mg/m³ == 1 g/cm³)

    Dimensional derivation:
      1 g/cm³ = 1000 kg/m³
      1 kg/m³ = 0.001 g/cm³
      1 Mg/m³ = 1000 kg/m³ = 1 g/cm³

    Raises:
      ValueError: If from_unit or to_unit is unsupported/unknown,
                  or if value is non-finite or negative.
    """
    if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0.0:
        raise ValueError(f"Soil bulk density value must be a non-negative finite number, got: {value}")

    norm_from = from_unit.strip().lower()
    norm_to = to_unit.strip().lower()

    if norm_from not in SUPPORTED_DENSITY_UNITS:
        raise ValueError(
            f"Unsupported or unverified source density unit '{from_unit}'. "
            f"Cannot perform conversion without explicit unit evidence. "
            f"Supported units: {sorted(SUPPORTED_DENSITY_UNITS)}"
        )
    if norm_to not in SUPPORTED_DENSITY_UNITS:
        raise ValueError(
            f"Unsupported or unverified target density unit '{to_unit}'. "
            f"Supported units: {sorted(SUPPORTED_DENSITY_UNITS)}"
        )

    # Normalize source to g/cm³
    if norm_from in ("g/cm3", "g/cm³", "mg/m3", "mg/m³"):
        val_g_cm3 = float(value)
    elif norm_from in ("kg/m3", "kg/m³"):
        val_g_cm3 = float(value) / 1000.0
    else:
        raise ValueError(f"Unmapped source density unit: '{from_unit}'")

    # Convert from g/cm³ to target
    if norm_to in ("g/cm3", "g/cm³", "mg/m3", "mg/m³"):
        return val_g_cm3
    elif norm_to in ("kg/m3", "kg/m³"):
        return val_g_cm3 * 1000.0
    else:
        raise ValueError(f"Unmapped target density unit: '{to_unit}'")


def build_civil_metrics(
    soil_state: Any = None,
    civil_output: Any = None,
    density_unit: str = "g/cm³",
) -> Dict[str, DashboardMetric]:
    """Extracts, normalizes, and packages Geotechnical/Civil metrics into typed DashboardMetric objects.

    Enforces explicit semantics, units, provenance, and data states:
      - dry_bulk_density (g/cm³ or kg/m³)
      - pore_water_pressure_kPa (kPa)
      - ground_stability_index (index [0.0 - 1.0])
      - bearing_capacity_kPa (kPa)
      - effective_cohesion_kPa (kPa)
      - factor_of_safety (dimensionless — strictly UNAVAILABLE)
      - california_bearing_ratio (% — strictly UNAVAILABLE)
      - foundation_suitability (classification — strictly UNAVAILABLE)
      - site_trafficability (classification)
      - observation_freshness_hrs (hours)

    Accepts:
      - DomainOutput instances from 4_domain_translators/civil_translator.py
      - Dict containers from runtime_cache or REST API
      - None / empty containers for disconnected state testing
    """
    metrics_map: Dict[str, DashboardMetric] = {}

    # Validate requested density unit
    norm_density_unit = density_unit.strip().lower()
    if norm_density_unit not in SUPPORTED_DENSITY_UNITS:
        raise ValueError(
            f"Unsupported density unit '{density_unit}'. "
            f"Supported density units: {sorted(SUPPORTED_DENSITY_UNITS)}"
        )

    # Determine general data state and provenance
    is_demo_mode = False
    base_state = DataState.UNAVAILABLE
    base_provenance = "Civil inference pipeline disconnected"

    output_metrics: Dict[str, Any] = {}
    output_metadata: Dict[str, Any] = {}
    output_uncertainty: Optional[Dict[str, Any]] = None

    if civil_output is not None:
        if hasattr(civil_output, "metrics"):
            # DomainOutput instance from 4_domain_translators
            output_metrics = getattr(civil_output, "metrics", {}) or {}
            output_metadata = getattr(civil_output, "metadata", {}) or {}
            output_uncertainty = getattr(civil_output, "uncertainty", None)
            base_provenance = output_metadata.get("provenance", "Civil Domain Translator Pipeline")
            base_state = DataState.LIVE
        elif isinstance(civil_output, dict):
            output_metrics = civil_output
            is_demo_mode = civil_output.get("is_demo", False) or civil_output.get("data_state") == DataState.DEMO
            if "data_state" in civil_output:
                base_state = civil_output["data_state"]
            elif is_demo_mode:
                base_state = DataState.DEMO
            elif any(
                k in civil_output
                for k in [
                    "ground_stability_index",
                    "pore_water_pressure_kPa",
                    "mean_bearing_kPa",
                    "bearing_capacity_est_kPa",
                    "dry_density_g_cm3",
                    "bulk_density",
                ]
            ):
                base_state = DataState.LIVE
            else:
                base_state = DataState.UNAVAILABLE
            base_provenance = civil_output.get(
                "provenance",
                "Synthetic Demonstration Scaffolding" if is_demo_mode else "Dictionary Container",
            )
    elif soil_state is not None:
        is_demo_mode = getattr(soil_state, "is_demo", False) or getattr(soil_state, "data_state", None) == DataState.DEMO
        if getattr(soil_state, "data_state", None) is not None:
            base_state = getattr(soil_state, "data_state")
        elif is_demo_mode:
            base_state = DataState.DEMO
        base_provenance = getattr(
            soil_state, "provenance", "Synthetic Demonstration Scaffolding" if is_demo_mode else "Soil State Container"
        )

    # 1. Soil Dry Bulk Density
    raw_density = None
    if output_metrics:
        raw_density = output_metrics.get("dry_density_g_cm3") or output_metrics.get("bulk_density")
    if raw_density is None and soil_state is not None:
        raw_density = getattr(getattr(soil_state, "hydro", None), "bulk_density", None)

    if raw_density is not None:
        try:
            d_val = float(raw_density)
            if math.isfinite(d_val) and d_val > 0.0:
                # Infer source unit: if > 100, source is kg/m3; otherwise g/cm3
                src_unit = "kg/m³" if d_val > 100.0 else "g/cm³"
                converted_val = convert_soil_bulk_density(d_val, src_unit, density_unit)
                # Check realistic soil density bounds in g/cm3 (0.5 to 3.0)
                g_cm3_equiv = converted_val if density_unit in ("g/cm3", "g/cm³", "mg/m3", "mg/m³") else converted_val / 1000.0
                if 0.5 <= g_cm3_equiv <= 3.0:
                    metrics_map["dry_bulk_density"] = DashboardMetric(
                        metric_id="dry_bulk_density",
                        label="Dry Bulk Soil Density",
                        value=converted_val,
                        unit=density_unit,
                        data_state=base_state,
                        provenance=base_provenance,
                        note="Dry bulk density (rho_d). Assumed baseline parameter; not an in-situ field core measurement.",
                    )
                else:
                    metrics_map["dry_bulk_density"] = DashboardMetric(
                        metric_id="dry_bulk_density",
                        label="Dry Bulk Soil Density",
                        value=None,
                        unit=density_unit,
                        data_state=DataState.ERROR,
                        provenance=base_provenance,
                        is_valid=False,
                        note=f"Bulk density value ({converted_val} {density_unit}) is outside realistic soil density bounds [0.5, 3.0] g/cm³.",
                    )
            else:
                metrics_map["dry_bulk_density"] = DashboardMetric(
                    metric_id="dry_bulk_density",
                    label="Dry Bulk Soil Density",
                    value=None,
                    unit=density_unit,
                    data_state=DataState.ERROR,
                    provenance=base_provenance,
                    is_valid=False,
                    note="Bulk density input is non-positive or non-finite.",
                )
        except (ValueError, TypeError):
            metrics_map["dry_bulk_density"] = DashboardMetric(
                metric_id="dry_bulk_density",
                label="Dry Bulk Soil Density",
                value=None,
                unit=density_unit,
                data_state=DataState.ERROR,
                provenance=base_provenance,
                is_valid=False,
                note="Non-numeric bulk density input encountered.",
            )
    else:
        metrics_map["dry_bulk_density"] = DashboardMetric(
            metric_id="dry_bulk_density",
            label="Dry Bulk Soil Density",
            value=None,
            unit=density_unit,
            data_state=DataState.UNAVAILABLE,
            provenance="Laboratory soil core testing disconnected",
            note="Bulk density unavailable — laboratory soil core testing and borehole logs are disconnected.",
        )

    # 2. Pore Water Pressure (kPa)
    raw_pressure = output_metrics.get("pore_water_pressure_kPa")
    if raw_pressure is not None:
        try:
            p_val = float(raw_pressure)
            if math.isfinite(p_val):
                metrics_map["pore_water_pressure_kPa"] = DashboardMetric(
                    metric_id="pore_water_pressure_kPa",
                    label="Pore Water Pressure",
                    value=p_val,
                    unit="kPa",
                    data_state=base_state,
                    provenance=base_provenance,
                    note="Pore water pressure (u). Uncalibrated demonstration parameter; in-situ piezometers/transducers are disconnected.",
                )
            else:
                metrics_map["pore_water_pressure_kPa"] = DashboardMetric(
                    metric_id="pore_water_pressure_kPa",
                    label="Pore Water Pressure",
                    value=None,
                    unit="kPa",
                    data_state=DataState.ERROR,
                    provenance=base_provenance,
                    is_valid=False,
                    note="Pore water pressure value is non-finite.",
                )
        except (ValueError, TypeError):
            metrics_map["pore_water_pressure_kPa"] = DashboardMetric(
                metric_id="pore_water_pressure_kPa",
                label="Pore Water Pressure",
                value=None,
                unit="kPa",
                data_state=DataState.ERROR,
                provenance=base_provenance,
                is_valid=False,
                note="Non-numeric pore water pressure input encountered.",
            )
    else:
        metrics_map["pore_water_pressure_kPa"] = DashboardMetric(
            metric_id="pore_water_pressure_kPa",
            label="Pore Water Pressure",
            value=None,
            unit="kPa",
            data_state=DataState.UNAVAILABLE,
            provenance="In-situ piezometer sensing disconnected",
            note="Pore-water pressure unavailable — in-situ piezometers and hydraulic groundwater models are disconnected.",
        )

    # 3. Ground Stability Index (index [0.0 - 1.0])
    raw_stability = output_metrics.get("ground_stability_index")
    if raw_stability is not None:
        try:
            s_val = float(raw_stability)
            if math.isfinite(s_val) and 0.0 <= s_val <= 1.0:
                metrics_map["ground_stability_index"] = DashboardMetric(
                    metric_id="ground_stability_index",
                    label="Ground Stability Index",
                    value=s_val,
                    unit="index [0.0 - 1.0]",
                    data_state=base_state,
                    provenance=base_provenance,
                    note="Uncalibrated demonstration index. NOT a certified factor of safety, foundation stability, or slope stability measure.",
                )
            else:
                metrics_map["ground_stability_index"] = DashboardMetric(
                    metric_id="ground_stability_index",
                    label="Ground Stability Index",
                    value=None,
                    unit="index [0.0 - 1.0]",
                    data_state=DataState.ERROR,
                    provenance=base_provenance,
                    is_valid=False,
                    note="Ground stability index is non-finite or outside valid [0, 1] bounds.",
                )
        except (ValueError, TypeError):
            metrics_map["ground_stability_index"] = DashboardMetric(
                metric_id="ground_stability_index",
                label="Ground Stability Index",
                value=None,
                unit="index [0.0 - 1.0]",
                data_state=DataState.ERROR,
                provenance=base_provenance,
                is_valid=False,
                note="Non-numeric ground stability index encountered.",
            )
    else:
        metrics_map["ground_stability_index"] = DashboardMetric(
            metric_id="ground_stability_index",
            label="Ground Stability Index",
            value=None,
            unit="index [0.0 - 1.0]",
            data_state=DataState.UNAVAILABLE,
            provenance="Geotechnical stability engine disconnected",
            note="Ground stability index unavailable — geotechnical assessment model disconnected.",
        )

    # 4. Nominal Ultimate Bearing Capacity (kPa)
    raw_bearing = output_metrics.get("mean_bearing_kPa") or output_metrics.get("bearing_capacity_est_kPa")
    if raw_bearing is not None:
        try:
            b_val = float(raw_bearing) if not isinstance(raw_bearing, np.ndarray) else float(np.nanmean(raw_bearing))
            if math.isfinite(b_val) and b_val >= 0.0:
                metrics_map["bearing_capacity_kPa"] = DashboardMetric(
                    metric_id="bearing_capacity_kPa",
                    label="Nominal Ultimate Bearing Capacity",
                    value=b_val,
                    unit="kPa",
                    data_state=base_state,
                    provenance=base_provenance,
                    note=(
                        "Nominal ultimate bearing capacity (q_ult) from undrained Terzaghi heuristic "
                        "(phi=0, Nc=5.7). Reported WITHOUT Factor of Safety (FS). "
                        "Not allowable bearing capacity; NOT for foundation design or construction permitting."
                    ),
                )
            else:
                metrics_map["bearing_capacity_kPa"] = DashboardMetric(
                    metric_id="bearing_capacity_kPa",
                    label="Nominal Ultimate Bearing Capacity",
                    value=None,
                    unit="kPa",
                    data_state=DataState.ERROR,
                    provenance=base_provenance,
                    is_valid=False,
                    note="Bearing capacity estimate is negative or non-finite.",
                )
        except (ValueError, TypeError):
            metrics_map["bearing_capacity_kPa"] = DashboardMetric(
                metric_id="bearing_capacity_kPa",
                label="Nominal Ultimate Bearing Capacity",
                value=None,
                unit="kPa",
                data_state=DataState.ERROR,
                provenance=base_provenance,
                is_valid=False,
                note="Invalid bearing capacity value encountered.",
            )
    else:
        metrics_map["bearing_capacity_kPa"] = DashboardMetric(
            metric_id="bearing_capacity_kPa",
            label="Nominal Ultimate Bearing Capacity",
            value=None,
            unit="kPa",
            data_state=DataState.UNAVAILABLE,
            provenance="Geotechnical site investigation disconnected",
            note="Bearing capacity estimate unavailable — site-specific geotechnical borehole investigation not connected.",
        )

    # 5. Effective Shear Cohesion (kPa)
    raw_cohesion = output_metrics.get("mean_effective_cohesion_kPa") or output_metrics.get("effective_cohesion_kPa")
    if raw_cohesion is not None:
        try:
            c_val = float(raw_cohesion) if not isinstance(raw_cohesion, np.ndarray) else float(np.nanmean(raw_cohesion))
            if math.isfinite(c_val) and c_val >= 0.0:
                metrics_map["effective_cohesion_kPa"] = DashboardMetric(
                    metric_id="effective_cohesion_kPa",
                    label="Effective Shear Cohesion",
                    value=c_val,
                    unit="kPa",
                    data_state=base_state,
                    provenance=base_provenance,
                    note="Empirical apparent cohesion based on fine-grained moisture degradation (c0=35 kPa). Invalid for granular soils.",
                )
            else:
                metrics_map["effective_cohesion_kPa"] = DashboardMetric(
                    metric_id="effective_cohesion_kPa",
                    label="Effective Shear Cohesion",
                    value=None,
                    unit="kPa",
                    data_state=DataState.ERROR,
                    provenance=base_provenance,
                    is_valid=False,
                    note="Shear cohesion is negative or non-finite.",
                )
        except (ValueError, TypeError):
            metrics_map["effective_cohesion_kPa"] = DashboardMetric(
                metric_id="effective_cohesion_kPa",
                label="Effective Shear Cohesion",
                value=None,
                unit="kPa",
                data_state=DataState.ERROR,
                provenance=base_provenance,
                is_valid=False,
                note="Invalid shear cohesion input.",
            )
    else:
        metrics_map["effective_cohesion_kPa"] = DashboardMetric(
            metric_id="effective_cohesion_kPa",
            label="Effective Shear Cohesion",
            value=None,
            unit="kPa",
            data_state=DataState.UNAVAILABLE,
            provenance="Triaxial laboratory shear testing disconnected",
            note="Shear cohesion unavailable — in-situ shear vane and triaxial laboratory testing disconnected.",
        )

    # 6. Factor of Safety (FS) — Strictly UNAVAILABLE
    metrics_map["factor_of_safety"] = DashboardMetric(
        metric_id="factor_of_safety",
        label="Factor of Safety (FS)",
        value=None,
        unit="dimensionless",
        data_state=DataState.UNAVAILABLE,
        provenance="Geotechnical design calculation disconnected",
        note=(
            "Factor of Safety (FS) has NOT been calculated. "
            "Standard geotechnical foundation engineering requires FS >= 3.0 based on certified borehole logs."
        ),
    )

    # 7. California Bearing Ratio (CBR) — Strictly UNAVAILABLE
    metrics_map["california_bearing_ratio"] = DashboardMetric(
        metric_id="california_bearing_ratio",
        label="California Bearing Ratio (CBR)",
        value=None,
        unit="%",
        data_state=DataState.UNAVAILABLE,
        provenance="Pavement laboratory testing disconnected",
        note="California Bearing Ratio (CBR) unavailable — ASTM D1883 / AASHTO T193 laboratory penetration testing is disconnected.",
    )

    # 8. Foundation Suitability — Strictly UNAVAILABLE
    metrics_map["foundation_suitability"] = DashboardMetric(
        metric_id="foundation_suitability",
        label="Foundation Suitability Classification",
        value=None,
        unit="classification",
        data_state=DataState.UNAVAILABLE,
        provenance="Structural engineering site certification disconnected",
        note="Foundation suitability assessment unavailable — site-specific geotechnical borehole investigation is disconnected.",
    )

    # 9. Site Trafficability Grade (classification)
    raw_traffic = output_metrics.get("site_trafficability")
    if raw_traffic is not None:
        metrics_map["site_trafficability"] = DashboardMetric(
            metric_id="site_trafficability",
            label="Site Trafficability Grade",
            value=str(raw_traffic),
            unit="classification",
            data_state=base_state,
            provenance=base_provenance,
            note="Empirical trafficability grade based on spatial mean bearing capacity; not calibrated to vehicle axle loads or NATO cone index.",
        )
    else:
        metrics_map["site_trafficability"] = DashboardMetric(
            metric_id="site_trafficability",
            label="Site Trafficability Grade",
            value=None,
            unit="classification",
            data_state=DataState.UNAVAILABLE,
            provenance="Trafficability heuristic disconnected",
            note="Site trafficability grade unavailable.",
        )

    # 10. Observation Freshness (hours)
    raw_freshness = None
    if soil_state is not None:
        raw_freshness = getattr(getattr(soil_state, "reliability", None), "observation_freshness_hrs", None)

    if raw_freshness is not None:
        try:
            f_val = float(raw_freshness)
            if math.isfinite(f_val) and f_val >= 0.0:
                metrics_map["observation_freshness_hrs"] = DashboardMetric(
                    metric_id="observation_freshness_hrs",
                    label="Observation Freshness",
                    value=f_val,
                    unit="hours",
                    data_state=base_state,
                    provenance=base_provenance,
                    note="Elapsed hours since last validated satellite observation.",
                )
            else:
                metrics_map["observation_freshness_hrs"] = DashboardMetric(
                    metric_id="observation_freshness_hrs",
                    label="Observation Freshness",
                    value=None,
                    unit="hours",
                    data_state=DataState.ERROR,
                    provenance=base_provenance,
                    is_valid=False,
                    note="Observation freshness value is negative or non-finite.",
                )
        except (ValueError, TypeError):
            metrics_map["observation_freshness_hrs"] = DashboardMetric(
                metric_id="observation_freshness_hrs",
                label="Observation Freshness",
                value=None,
                unit="hours",
                data_state=DataState.ERROR,
                provenance=base_provenance,
                is_valid=False,
                note="Non-numeric observation freshness encountered.",
            )
    else:
        metrics_map["observation_freshness_hrs"] = DashboardMetric(
            metric_id="observation_freshness_hrs",
            label="Observation Freshness",
            value=None,
            unit="hours",
            data_state=DataState.UNAVAILABLE,
            provenance="Live telemetry feed disconnected",
            note="Observation freshness unavailable — live satellite telemetry feed is disconnected.",
        )

    return metrics_map


# ---------------------------------------------------------------------------
# GIS Spatial Layer Metadata Contract (Task 05)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SpatialLayerMetadata:
    """Standardized Presentation Contract for GIS Spatial Layers & Heatmaps.

    Guarantees that every spatial layer explicitly declares its geometry type,
    CRS, bounding extent, resolution, metric semantics, units, provenance, and data state.
    """

    layer_id: str
    layer_type: str  # 'spatial_grid_mesh', 'aoi_boundary', 'soil_moisture_raster'
    crs: str  # e.g. 'EPSG:4326'
    extent_bbox: List[float]  # [min_lon, min_lat, max_lon, max_lat]
    data_state: DataState
    provenance: str
    spatial_resolution_m: Optional[float] = None
    grid_dimensions: Optional[Tuple[int, int]] = None
    metric_id: Optional[str] = None
    unit: Optional[str] = None
    timestamp: Optional[str] = None
    has_measurements: bool = False
    nodata_value: Optional[float] = None
    uncertainty: Optional[Any] = None
    uncertainty_type: Optional[str] = None
    note: str = ""

    def __post_init__(self) -> None:
        # CRS must be explicit, not guessed
        if not self.crs or not str(self.crs).strip():
            raise ValueError(
                f"Spatial layer '{self.layer_id}' has empty CRS. Unknown CRS must not be guessed."
            )

        # Enforce that LIVE cannot be assigned to demo provenance
        if self.data_state == DataState.LIVE:
            if "demo" in self.provenance.lower() or "synthetic" in self.provenance.lower():
                raise ValueError(
                    f"Spatial layer '{self.layer_id}' has data_state=LIVE but demo/synthetic provenance: '{self.provenance}'"
                )

        # Enforce bbox validation [min_lon, min_lat, max_lon, max_lat]
        if len(self.extent_bbox) != 4:
            raise ValueError(
                f"extent_bbox must have 4 elements [min_lon, min_lat, max_lon, max_lat], got: {self.extent_bbox}"
            )
        if self.extent_bbox[0] > self.extent_bbox[2] or self.extent_bbox[1] > self.extent_bbox[3]:
            raise ValueError(
                f"Inverted bbox coordinates: min cannot exceed max: {self.extent_bbox}"
            )


def build_spatial_layer_metadata(
    layer_dict: Dict[str, Any],
    layer_type: str = "spatial_grid_mesh",
) -> SpatialLayerMetadata:
    """Extracts and validates spatial metadata from GeoJSON or GIS layer response.

    Enforces explicit CRS, spatial bounds, provenance, and distinction between
    geometry-only subgrids vs verified physical measurements.
    """
    if not isinstance(layer_dict, dict):
        raise ValueError(f"Expected dict for spatial layer, got: {type(layer_dict)}")

    # Extract or validate CRS
    crs = layer_dict.get("crs")
    if not crs or not str(crs).strip():
        # Check if geojson top-level CRS is present
        geojson = layer_dict.get("geojson_data", layer_dict)
        crs = geojson.get("crs", {}).get("properties", {}).get("name") if isinstance(geojson.get("crs"), dict) else "EPSG:4326"
    if not crs:
        raise ValueError("Spatial layer missing CRS. Unknown CRS must not be silently guessed.")

    # Extract or validate extent bbox
    bbox = layer_dict.get("extent_bbox")
    if not bbox:
        geojson = layer_dict.get("geojson_data", layer_dict)
        bbox = geojson.get("bbox", [85.75, 20.20, 85.90, 20.35])

    # Check features for physical measurements
    geojson_payload = layer_dict.get("geojson_data", layer_dict)
    props = layer_dict.get("properties") if isinstance(layer_dict.get("properties"), dict) else {}
    features = geojson_payload.get("features", []) if isinstance(geojson_payload, dict) else []

    has_real_moisture = False
    for f in features:
        f_props = f.get("properties", {}) if isinstance(f, dict) else {}
        if f_props.get("moisture_m3m3") is not None:
            has_real_moisture = True
            break

    # Determine data state & provenance
    is_demo = layer_dict.get("is_demo", False) or props.get("is_demo", False)
    raw_data_state = layer_dict.get("data_state") or props.get("data_state")
    if isinstance(raw_data_state, str):
        try:
            data_state = DataState(raw_data_state)
        except ValueError:
            data_state = None
    elif isinstance(raw_data_state, DataState):
        data_state = raw_data_state
    else:
        data_state = None

    if data_state is None:
        if layer_dict.get("status") == "UNAVAILABLE" or props.get("status") == "UNAVAILABLE":
            data_state = DataState.UNAVAILABLE
        elif has_real_moisture:
            data_state = DataState.DEMO if is_demo else DataState.LIVE
        else:
            data_state = DataState.DEMO

    default_prov = (
        "Unavailable Spatial Layer"
        if data_state == DataState.UNAVAILABLE
        else ("Synthetic Demonstration Grid Tiler" if (is_demo or not has_real_moisture) else "Satellite Radar Inversion Pipeline")
    )
    provenance = layer_dict.get("provenance") or props.get("provenance") or default_prov

    metric_id = "volumetric_soil_moisture" if has_real_moisture else None
    unit = "m³/m³" if has_real_moisture else None

    # Handle requested units validation
    req_unit = layer_dict.get("unit") or props.get("raster_units") or props.get("unit")
    if req_unit is not None:
        if req_unit not in ("m3/m3", "m³/m³", "%", "fraction", "dimensionless"):
            raise ValueError(f"Unknown or unsupported unit '{req_unit}' for spatial soil moisture layer.")
        unit = req_unit

    note = (
        "Volumetric soil moisture spatial field."
        if has_real_moisture
        else (
            "No validated spatial observations are available for this layer."
            if data_state == DataState.UNAVAILABLE
            else "Computational subgrid tiles represent spatial geometry only. No physical sensor observations are attached."
        )
    )

    return SpatialLayerMetadata(
        layer_id=layer_dict.get("layer_id", f"{layer_type}_{crs}"),
        layer_type=layer_type,
        crs=str(crs),
        extent_bbox=[float(x) for x in bbox],
        data_state=data_state,
        provenance=provenance,
        spatial_resolution_m=layer_dict.get("resolution_m"),
        grid_dimensions=layer_dict.get("grid_dimensions"),
        metric_id=metric_id,
        unit=unit,
        timestamp=layer_dict.get("timestamp"),
        has_measurements=has_real_moisture,
        nodata_value=layer_dict.get("nodata_value"),
        uncertainty=layer_dict.get("uncertainty"),
        uncertainty_type=layer_dict.get("uncertainty_type"),
        note=note,
    )
