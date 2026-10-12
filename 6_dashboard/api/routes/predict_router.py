"""
THE MRIDANSH : Soil State & Physics Prediction Endpoint (Hardened Day 24)
Exposes physical prediction routing and explicit demonstration scaffolding.
"""

import time
from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

predict_router = APIRouter(prefix="/predict", tags=["Physics & Soil Inference Engine"])


# Request Schema Definition
class SoilPredictionRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, json_schema_extra={"example": 20.2961})
    longitude: float = Field(..., ge=-180.0, le=180.0, json_schema_extra={"example": 85.8245})
    depth_profile_cm: list[float] = Field(default=[5.0, 15.0, 30.0, 60.0, 100.0])
    simulation_days: int = Field(default=7, ge=1, le=30)
    include_enkf_assimilation: bool = Field(default=False)
    allow_demo: bool = Field(
        default=False,
        description="Explicitly enable synthetic demonstration data for UI scaffolding",
    )


# Response Schema Definition
class SoilPredictionResponse(BaseModel):
    status: str
    data_state: str
    message: str
    location: dict[str, float]
    depths_cm: list[float]
    predicted_moisture_m3m3: list[float] | None = None
    uncertainty_bounds: list[float] | None = None
    execution_time_sec: float
    model_metadata: dict[str, Any]


@predict_router.post(
    "",
    response_model=SoilPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Soil Moisture & Richards Physical Simulation",
)
async def predict_soil_state(payload: SoilPredictionRequest) -> dict[str, Any]:
    """Runs physical soil state prediction or explicit UI demonstration scaffolding.

    If live inference engines are disconnected and allow_demo is False, raises HTTP 503.
    """
    start_time = time.time()

    if not payload.allow_demo:
        # Prevent fabricated values from being returned as live predictions
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "UNAVAILABLE",
                "data_state": "UNAVAILABLE",
                "message": (
                    "Live physical prediction engine is not connected. The AETHER "
                    "core engine is disconnected pending pipeline wiring. Pass "
                    "'allow_demo=true' in request body to inspect UI scaffolding."
                ),
                "model_metadata": {
                    "engine": "Disconnected",
                    "assimilated_satellite": "None",
                    "data_state": "UNAVAILABLE",
                },
            },
        )

    try:
        depths = payload.depth_profile_cm
        num_depths = len(depths)

        # Synthetic Scaffolding Profile Generation (explicitly isolated as DEMO)
        base_moisture = 0.25 + 0.05 * np.sin(np.radians(payload.latitude))

        predicted_moisture_vals = [
            round(float(base_moisture * np.exp(-d / 120.0) + 0.05), 4) for d in depths
        ]

        uncertainty_vals = [
            round(float(0.02 + 0.005 * (i + 1)), 4) for i in range(num_depths)
        ]

        exec_duration = round(time.time() - start_time, 4)

        return {
            "status": "DEMO",
            "data_state": "DEMO",
            "message": "DEMO DATA — NOT FOR SCIENTIFIC OR FIELD USE. Synthetic demonstration profile.",
            "location": {"lat": payload.latitude, "lon": payload.longitude},
            "depths_cm": depths,
            "predicted_moisture_m3m3": predicted_moisture_vals,
            "uncertainty_bounds": uncertainty_vals,
            "execution_time_sec": exec_duration,
            "model_metadata": {
                "engine": "Synthetic Scaffolding Generator (DEMO ONLY)",
                "assimilated_satellite": "None (Demonstration Mode)",
                "days_simulated": payload.simulation_days,
                "data_state": "DEMO",
                "disclaimer": "DEMO DATA — NOT FOR SCIENTIFIC USE",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Soil state prediction pipeline error: {e!s}",
        )
