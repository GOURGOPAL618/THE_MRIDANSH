# THE_MRIDANSH/3_core_engine/physics/__init__.py
from .richards_engine import RichardsSoilPhysicsEngine
from .van_genuchten import VanGenuchtenEngine, SoilHydraulicParams, USDA_SOIL_CATALOG
from .pinn_richards import (
    PhysicsInformedNN,
    RichardsPINN,
    RichardsResidualEvaluator,
    RichardsPhysicsLoss,
    clamp_vadose_moisture,
)
