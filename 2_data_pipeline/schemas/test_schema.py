import numpy as np
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator

class ConversionError(Exception):
    pass

class GeospatialRasterAsset(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    raw_array: np.ndarray
    raw_dtype: str
    scale_factor: Optional[float] = None
    add_offset: Optional[float] = None
    
    crs: str
    transform: tuple[float, float, float, float, float, float]
    bounds: tuple[float, float, float, float]
    resolution: tuple[float, float]
    
    valid_data_mask: np.ndarray
    nodata_value: Optional[float] = None
    
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
        if self.scale_factor is None or self.add_offset is None:
            raise ConversionError("Cannot convert to physical values: scale_factor or add_offset is unresolved.")
        return (self.raw_array.astype(np.float32) * self.scale_factor) + self.add_offset

print("Imports and class definitions successful.")
