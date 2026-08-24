"""
THE MRIDANSH : FastAPI Core Application Server (Day 23)
Asynchronous REST API Engine providing CORS middleware, health telemetry,
and API routing structure for satellite processing pipelines.
"""

import time
from typing import Dict, Any
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from routes.v1_router import api_v1_router

def create_application() -> FastAPI:
    """FastAPI Application Factory."""
    app = FastAPI(
        title = "THE MRIDANSH - GEOSPATIAL AGRICULTURE ENGINE API",
        description = "Async REST API backend powering satellite soil moisture assimilation, GIS overlays, and Richards+EnKF physics engine.",
        version="1.0.0",
        docs_url = "/docs",
        redoc_url = "/redoc",
    )

    # Enable CORS for Streamlit / Web UI Communication
    app.add_middleware(
        CORSMiddleware,
        allow_origins = ["*"],
        allow_credentials = True,
        allow_methods = ["*"],
        allow_headers = ["*"],
    )

    # Middleware for request timing telementary
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time-Sec"] = f"{process_time:.4f}"
        return response

    # Mount V1 Router
    app.include_router(api_v1_router)

    # Telementry / Health Check Endpoint
    @app.get("/health", tags = ["Telementry"], summary = "System Health Check")
    async def health_check() -> Dict[str, Any]:
        """Provides backend engine health status and operational parameters."""
        return {
            "status": "HEALTHY",
            "service": "THE MRIDANSH Async REST Backend",
            "version": "1.0.0",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "modules": {
                "gis_engine": "ACTIVE",
                "grid_tiler": "ACTIVE",
                "api_v1": "ACTIVE",
            },
        }

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn
    print("⚡ Starting Day 23 FastAPI REST Engine Server on http://127.0.0.1:8000 ...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)