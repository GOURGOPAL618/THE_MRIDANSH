# THE MRIDANSH - Agriculture Domain Translators
# Module: 4_domain_translators/agronomy/__init__.py
# AETHER-MRID1607X Operational Downstream Intelligence

from .soil_water_reservoir import (
    SoilHydraulicProperties,
    AvailableWaterReservoir,
    SoilWaterReservoirEngine,
    USDA_TEXTURE_PROPERTIES,
)
from .dynamic_phenology import (
    PhenologyState,
    DynamicPhenologyEngine,
)
from .fao56_dual_kc import (
    DualKcOutput,
    FAO56DualKcEngine,
)
from .crop_water_stress import (
    WaterStressOutput,
    CropWaterStressEngine,
)
from .agronomy_domain_engine import (
    AgronomicStateVector,
    AgronomyDomainEngine,
)
from .irrigation_prescription import (
    IrrigationStrategy,
    IrrigationSystemType,
    IrrigationPrescriptionMap,
    PrecisionIrrigationEngine,
    LITERS_PER_HA_PER_MM,
    LITERS_PER_10M_PIXEL_PER_MM,
)

__all__ = [
    # Phase 1: Soil Hydraulics & Reservoir
    "SoilHydraulicProperties",
    "AvailableWaterReservoir",
    "SoilWaterReservoirEngine",
    "USDA_TEXTURE_PROPERTIES",

    # Phase 2: Dynamic Phenology & Dual Kc
    "PhenologyState",
    "DynamicPhenologyEngine",
    "DualKcOutput",
    "FAO56DualKcEngine",

    # Phase 3: Stress Mechanics & Monolithic Engine
    "WaterStressOutput",
    "CropWaterStressEngine",
    "AgronomicStateVector",
    "AgronomyDomainEngine",
    
    # Day 13 Phase 1: Precision Variable-Rate Irrigation
    "IrrigationStrategy",
    "IrrigationSystemType",
    "IrrigationPrescriptionMap",
    "PrecisionIrrigationEngine",
    "LITERS_PER_HA_PER_MM",
    "LITERS_PER_10M_PIXEL_PER_MM",
]
