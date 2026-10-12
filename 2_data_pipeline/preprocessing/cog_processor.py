import sys
import os
import rasterio
from rasterio.windows import from_bounds
from rasterio.errors import RasterioIOError
import numpy as np

# Add parent directory to path so we can import schemas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from schemas.satellite_schema import GeospatialRasterAsset

class RasterReadError(Exception):
    pass

class InvalidWindowError(Exception):
    pass

class COGRasterProcessor:
    """Streams and Processes Remote Cloud-Optimized GeoTIFF (COG) rasters."""

    def __init__(self, target_resolution: float = 10.0):
        self.target_resolution = target_resolution

    def read_raster_window(
        self,
        cog_url: str,
        bbox: list[float] | None = None,
    ) -> GeospatialRasterAsset:
        """Reads a real raster or window using rasterio."""
        try:
            with rasterio.open(cog_url) as src:
                if src.crs is None or src.transform is None:
                    raise RasterReadError("Source raster lacks required CRS or Transform metadata.")
                
                scale = src.scales[0] if src.scales and src.scales[0] is not None else None
                offset = src.offsets[0] if src.offsets and src.offsets[0] is not None else None
                
                if bbox:
                    # rasterio from_bounds expects (left, bottom, right, top)
                    min_x, min_y, max_x, max_y = bbox
                    window = from_bounds(min_x, min_y, max_x, max_y, src.transform)
                    
                    # Round window to integer pixels to avoid fractional reads
                    window = window.round_lengths().round_offsets()
                    
                    # Check if window intersects with raster
                    try:
                        window = window.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
                    except rasterio.errors.WindowError:
                        raise InvalidWindowError("Requested bounding box does not intersect the raster.")
                    
                    if window.width <= 0 or window.height <= 0:
                        raise InvalidWindowError("Requested bounding box does not intersect the raster or produces empty window.")
                    
                    
                    raw_array = src.read(window=window)
                    transform = src.window_transform(window)
                    bounds = rasterio.windows.bounds(window, src.transform)
                    valid_mask = src.read_masks(window=window)
                else:
                    raw_array = src.read()
                    transform = src.transform
                    bounds = src.bounds
                    valid_mask = src.read_masks()

                raw_dtype = str(raw_array.dtype)
                
                if valid_mask.ndim == 2:
                    bool_mask = (valid_mask != 0)[np.newaxis, :, :]
                else:
                    # Collapse (bands, height, width) to (1, height, width)
                    bool_mask = np.all(valid_mask != 0, axis=0, keepdims=True)

                return GeospatialRasterAsset(
                    raw_array=raw_array,
                    raw_dtype=raw_dtype,
                    scale_factor=scale,
                    add_offset=offset,
                    crs=src.crs.to_string(),
                    transform=tuple(transform)[:6],
                    bounds=tuple(bounds),
                    resolution=(src.res[0], src.res[1]),
                    valid_data_mask=bool_mask,
                    nodata_value=src.nodata,
                    source_href=cog_url
                )
        except RasterioIOError as e:
            raise RasterReadError(f"Failed to read raster source: {str(e)}")

    def align_and_resample(self, raster_data: np.ndarray, target_shape: tuple[int, int]) -> np.ndarray:
        # Legacy method kept for compatibility for now.
        if raster_data.shape == target_shape:
            return raster_data
        row_indices = np.linspace(0, raster_data.shape[0] - 1, target_shape[0]).astype(int)
        col_indices = np.linspace(0, raster_data.shape[1] - 1, target_shape[1]).astype(int)
        resampled = raster_data[np.ix_(row_indices, col_indices)]
        return resampled

    def clean_and_normalize_raster(self, raster_data: np.ndarray, valid_range: tuple[float, float] = (0.0, 1.0)):
        # Legacy method kept for compatibility.
        data = raster_data.copy()
        nan_mask = np.isnan(data)
        nan_count = int(np.sum(nan_mask))
        if nan_count > 0:
            valid_median = np.nanmedian(data)
            if np.isnan(valid_median):
                valid_median = 0.0
            data[nan_mask] = valid_median
        cleaned = np.clip(data, valid_range[0], valid_range[1])
        metadata = {
            "total_pixels": data.size,
            "nan_filled_count": nan_count,
            "nan_percentage": float(np.round((nan_count / data.size) * 100, 2)),
            "min_val": float(np.round(np.min(cleaned), 4)),
            "max_val": float(np.round(np.max(cleaned), 4)),
            "mean_val": float(np.round(np.mean(cleaned), 4)),
        }
        return cleaned, metadata
