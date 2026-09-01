"""
THE MRIDANSH : GIS Vector & Satellite Raster Delivery Endpoint (Day 25)
Exposes vector boundaries, grid mesh geometries, and raster layer metadata via REST API.
"""

import importlib.util
import os
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

# Direct file-level import of GeospatialGridTiler — bypasses preprocessing/__init__.py
# which has a broken `from ..schemas` relative import chain (2_data_pipeline has no __init__.py).
# grid_tiler.py itself has no relative imports, so this is safe.
_GRID_TILER_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "2_data_pipeline",
        "preprocessing",
        "grid_tiler.py",
    )
)
_spec = importlib.util.spec_from_file_location("grid_tiler", _GRID_TILER_PATH)
_grid_tiler_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_grid_tiler_module)
GeospatialGridTiler = _grid_tiler_module.GeospatialGridTiler

gis_router = APIRouter(prefix="/gis", tags=["GIS & Satellite Spatial Data Engine"])

tiler_engine = GeospatialGridTiler()


class LayerMetadataResponse(BaseModel):
    status: str
    layer_type: str
    crs: str
    extent_bbox: list[float]
    geojson_data: dict[str, Any]
    execution_time_sec: float


@gis_router.get(
    "/layer",
    response_model=LayerMetadataResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch GIS Vector & Computational Grid Mesh Layers",
)
async def get_gis_layer(
    layer_type: str = Query(
        "spatial_grid_mesh",
        description="Type Of Layer: 'aoi_boundary', 'spatial_grid_mesh', 'soil_moisture_raster'",
    ),
    min_lon: float = Query(85.75, description="Minimum Longitude"),
    min_lat: float = Query(20.20, description="Minimum Latitude"),
    max_lon: float = Query(85.90, description="Maximum Longitude"),
    max_lat: float = Query(20.35, description="Maximum Latitude"),
    grid_rows: int = Query(4, ge=1, le=10, description="Grid Rows for tiling"),
    grid_cols: int = Query(4, ge=1, le=10, description="Grid Cols for tiling"),
) -> dict[str, Any]:
    """Generates and serves vector boundaries, computational sub-grids, or raster overlay specs."""
    start_time = time.time()
    bbox = [min_lon, min_lat, max_lon, max_lat]

    try:
        if layer_type == "spatial_grid_mesh":
            # Generates Sub-Grid Mesh via day 22 Grid Tiler
            tiles = tiler_engine.create_spatial_subgrids(
                bbox, rows=grid_rows, cols=grid_cols
            )
            geojson_payload = tiler_engine.export_tiles_to_geojson(tiles)

        elif layer_type == "aoi_boundary":
            # Generates Single AOI Polygon
            geojson_payload = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"name": "User Target AOI Boundary"},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [min_lon, min_lat],
                                    [max_lon, min_lat],
                                    [max_lon, max_lat],
                                    [min_lon, max_lat],
                                    [min_lon, min_lat],
                                ]
                            ],
                        },
                    }
                ],
            }

        elif layer_type == "soil_moisture_raster":
            # Mock Satellite Soil Moisture Surface Layer Metadata
            geojson_payload = {
                "type": "FeatureCollection",
                "properties": {
                    "raster_units": "m3/m3",
                    "resolution_m": 10.0,
                    "satellite_source": "Sentinel - 1 C-Band SAR Assimilation",
                    "colormap": "Spectral_r",
                    "min_val": 0.05,
                    "max_val": 0.45,
                },
                "features": [],
            }

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported layer_type: '{layer_type}'. Use 'spatial_grid_mesh', 'aoi_boundary', or 'soil_moisture_raster'.",
            )

        exec_duration = round(time.time() - start_time, 4)

        return {
            "status": "SUCCESS",
            "layer_type": layer_type,
            "crs": "EPSG:4326",
            "extent_bbox": bbox,
            "geojson_data": geojson_payload,
            "execution_time_sec": exec_duration,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GIS Layer Generation Pipeline Error: {e!s}",
        )
