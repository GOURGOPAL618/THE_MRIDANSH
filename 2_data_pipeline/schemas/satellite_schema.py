# THE MRIDANSH - DATA PIPELINE - RS-SDA DIVISION


from pydantic import BaseModel, Field, field_validator
import numpy as np
from typing import Optional, Any
from pydantic import ConfigDict, model_validator


class SpatialBoundingBox(BaseModel):
    """Enforces geographic bounding box limits [min_lon, min_lat, max_lon, max_lat]"""

    bbox: tuple[float, float, float, float]

    @field_validator("bbox")
    def validate_coordinates(cls, v):
        min_lon, min_lat, max_lon, max_lat = v
        if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
            raise ValueError("Longitude must be between -180 and 180 degrees.")
        if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
            raise ValueError("Latitude must be between -90 and 90 degrees.")
        if min_lon >= max_lon or min_lat >= max_lat:
            raise ValueError(
                "Invalid bounding box: min coordinates must be strictly less than max coordinates."
            )
        return v


class SentinelFrameMetadata(BaseModel):
    """Validates incoming Sentinel Satellite Frame metadata"""

    scene_id: str = Field(
        ..., min_length=5, description="Unique Satellite Scene Identifier"
    )
    acquisition_date: str = Field(
        ..., description="ISO Format acquisition date (YYYY-MM-DD)"
    )
    cloud_cover_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Cloud Cover percentage filter"
    )

    bands_available: list[str]
    asset_hrefs: dict[str, str] = Field(default_factory=dict)
    spatial_resolution_m: float = Field(default=30.0, gt=0.0)


# Self-test validation block


class ConversionError(Exception):
    """Raised when an attempt to convert to physical units fails due to unresolved parameters."""
    pass

class GeospatialRasterAsset(BaseModel):
    """Canonical Raster Contract for THE MRIDANSH."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Raster Values
    raw_array: np.ndarray = Field(..., description="Source array in native dtype")
    raw_dtype: str = Field(..., description="Original data type of the source raster")
    scale_factor: Optional[float] = Field(None, description="Physical scale factor")
    add_offset: Optional[float] = Field(None, description="Physical add offset")
    
    # Geospatial Metadata
    crs: str = Field(..., description="Coordinate Reference System (e.g., EPSG:32645)")
    transform: tuple[float, float, float, float, float, float] = Field(..., description="6-element Affine transform")
    bounds: tuple[float, float, float, float] = Field(..., description="(min_x, min_y, max_x, max_y)")
    resolution: tuple[float, float] = Field(..., description="(x_res, y_res)")
    
    # Validity and Provenance
    valid_data_mask: np.ndarray = Field(..., description="Boolean validity mask, shape (1, height, width)")
    nodata_value: Optional[float] = Field(None, description="Source nodata metadata")
    
    stac_item_id: Optional[str] = None
    asset_key: Optional[str] = None
    source_href: Optional[str] = None
    acquisition_datetime: Optional[str] = None

    @field_validator("raw_array")
    def validate_array_layout(cls, v):
        if not isinstance(v, np.ndarray):
            raise ValueError("raw_array must be a numpy array")
        if v.ndim != 3:
            raise ValueError(f"Array layout must be (bands, height, width). Got {v.ndim} dimensions.")
        return v

    @field_validator("valid_data_mask")
    def validate_mask_layout(cls, v):
        if not isinstance(v, np.ndarray):
            raise ValueError("valid_data_mask must be a numpy array")
        if v.ndim != 3 or v.shape[0] != 1:
            raise ValueError(f"valid_data_mask must have shape (1, height, width). Got shape {v.shape}.")
        return v

    @model_validator(mode='after')
    def check_mask_dimensions(self):
        if self.valid_data_mask.shape[1:] != self.raw_array.shape[1:]:
            raise ValueError(f"Mask dimensions {self.valid_data_mask.shape[1:]} do not match array dimensions {self.raw_array.shape[1:]}.")
        return self

    def to_physical(self) -> np.ndarray:
        """Converts raw array to physical float32 values."""
        if self.scale_factor is None or self.add_offset is None:
            raise ConversionError("Cannot convert to physical values: scale_factor or add_offset is unresolved.")
        return (self.raw_array.astype(np.float32) * self.scale_factor) + self.add_offset

if __name__ == "__main__":
    sample_bbox = SpatialBoundingBox(bbox=(77.0, 28.0, 78.0, 29.0))
    sample_meta = SentinelFrameMetadata(
        scene_id="S2A_MSIL2A_20260721",
        acquisition_date="2026-07-21",
        cloud_cover_percentage=12.4,
        bands_available=["VV", "VH", "B02", "B03", "B04", "B08"],
    )

    print("[OK] Satellite Validation Schema Operating Normally!")
    print(
        f"Validated Scene: {sample_meta.scene_id} | Cloud Cover: {sample_meta.cloud_cover_percentage}%"
    )

    print("\n--- Testing GeospatialRasterAsset Contract ---")
    
    # 1. Native dtype array and layout retained
    raw = np.ones((1, 10, 10), dtype=np.uint16) * 1000
    mask = np.ones((1, 10, 10), dtype=bool)
    asset = GeospatialRasterAsset(
        raw_array=raw,
        raw_dtype="uint16",
        scale_factor=0.0001,
        add_offset=0.0,
        crs="EPSG:32645",
        transform=(10.0, 0.0, 300000.0, 0.0, -10.0, 4000000.0),
        bounds=(300000.0, 3999900.0, 300100.0, 4000000.0),
        resolution=(10.0, 10.0),
        valid_data_mask=mask,
        stac_item_id="mock_stac_id"
    )
    
    assert asset.raw_array.dtype == np.uint16
    assert asset.raw_array.shape == (1, 10, 10)
    print("1. Native array dtype and shape (bands, height, width) successfully retained.")
    
    # 2. Verified scale/offset produce float32 physical values
    phys = asset.to_physical()
    assert phys.dtype == np.float32
    assert np.allclose(phys, 0.1)
    print("2. Verified scale/offset produced float32 physical values correctly.")
    
    # 3. Unresolved scale/offset raises ConversionError
    unresolved_asset = asset.model_copy(update={"scale_factor": None})
    try:
        unresolved_asset.to_physical()
        raise AssertionError("Should have raised ConversionError")
    except ConversionError:
        print("3. Unresolved parameters correctly raised ConversionError.")
        
    # 4. Invalid dimensions or mismatched mask shape are rejected
    try:
        invalid_mask = np.ones((1, 5, 5), dtype=bool)
        GeospatialRasterAsset(
            raw_array=raw, raw_dtype="uint16", scale_factor=1.0, add_offset=0.0,
            crs="EPSG:4326", transform=(1,0,0,0,-1,0), bounds=(0,0,1,1), resolution=(1,1),
            valid_data_mask=invalid_mask
        )
        raise AssertionError("Should have rejected mismatched mask shape")
    except ValueError as e:
        print("4. Mismatched mask dimensions successfully rejected.")
        
    # 5. Geospatial metadata preservation
    assert asset.crs == "EPSG:32645"
    assert asset.transform == (10.0, 0.0, 300000.0, 0.0, -10.0, 4000000.0)
    assert asset.stac_item_id == "mock_stac_id"
    print("5. Geospatial and provenance metadata securely preserved.")
    
    print("\n[SUCCESS] RASTER CONTRACT IMPLEMENTED AND VERIFIED.")
