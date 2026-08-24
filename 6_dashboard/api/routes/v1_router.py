"""
THE MRIDANSH : API Router Scaffolding - v1 Endpoints (Day 23)
Modular router container for prediction, GIS raster delivery, and pipeline triggers.
"""

from typing import Any, Dict
from fastapi import APIRouter

api_v1_router = APIRouter(prefix = "/api/v1", tags = ["v1_endpoints"])

@api_v1_router.get("/status", summary = "V1 API Subsystem Status")
async def get_v1_status() -> Dict[str, Any]:
    """Returns status metrics of the v1 API routes."""

    return {
        "subsystem": "THE MRIDANSH v1 CORE API",
        "status": "ONLINE",
        "active_endpoints": ["/api/v1/status"],
    }
