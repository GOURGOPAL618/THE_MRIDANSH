# THE MRIDANSH - DATA PIPELINE - RS-SDA DIVISION

from pydantic import BaseModel, Field, field_validator
from typing import List, Tuple

class SpatialBoundingBox(BaseModel):
    """Enforces geographic bounding box limits [min_lon, min_lat, max_lon, max_lat]"""
    bbox: Tuple[float, float, float, float]

    @field_validator('bbox')
    def validate_coordinates(cls, v):
        min_lon, min_lat, max_lon, max_lat = v
        if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
            raise ValueError("Longitude must be between -180 and 180 degrees.")
        if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
            raise ValueError("Latitude must be between -90 and 90 degrees.")
        if min_lon >= max_lon or min_lat >= max_lat:
            raise ValueError("Invalid bounding box: min coordinates must be strictly less than max coordinates.")
        return v

class SentinelFrameMetadata(BaseModel):
    """Validates incoming Sentinel Satellite Frame metadata"""
    scene_id: str = Field(..., min_length = 5, description = "Unique Satellite Scene Identifier")
    acquisition_date: str = Field(..., description = "ISO Format acquisition date (YYYY-MM-DD)")
    cloud_cover_percentage: float = Field(..., ge = 0.0, le = 100.0, description = "Cloud Cover percentage filter")

    bands_available: List[str]
    spatial_resolution_m: float = Field(default = 30.0, gt = 0.0)
    
# Self-test validation block
if __name__ == "__main__":
    sample_bbox = SpatialBoundingBox(bbox=(77.0, 28.0, 78.0, 29.0))
    sample_meta = SentinelFrameMetadata(
        scene_id="S2A_MSIL2A_20260721",
        acquisition_date="2026-07-21",
        cloud_cover_percentage=12.4,
        bands_available=["VV", "VH", "B02", "B03", "B04", "B08"]
    )

    print("✅ Satellite Validation Schema Operating Normally!")
    print(f"Validated Scene: {sample_meta.scene_id} | Cloud Cover: {sample_meta.cloud_cover_percentage}%")