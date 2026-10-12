import logging
import numpy as np
from pystac_client import Client

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from schemas.satellite_schema import SpatialBoundingBox, GeospatialRasterAsset
from preprocessing.cog_processor import COGRasterProcessor, RasterReadError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class DEMTerrainEngine:
    """Digital Elevation Model (DEM) Engine for Terrain & Slope Derivation."""

    def __init__(self, stac_url: str = "https://earth-search.aws.element84.com/v1"):
        self.stac_url = stac_url
        self.cog_processor = COGRasterProcessor()

    def fetch_dem_asset(self, bbox: SpatialBoundingBox) -> GeospatialRasterAsset:
        """Acquires actual DEM data (Copernicus GLO-30) from Element84 STAC."""
        logging.info(f"🏔️ Querying COP-DEM-GLO-30 for BBox: {bbox.bbox}")
        
        try:
            client = Client.open(self.stac_url)
            search = client.search(
                collections=['cop-dem-glo-30'],
                bbox=list(bbox.bbox),
                limit=1
            )
            items = list(search.items())
        except Exception as e:
            raise RuntimeError(f"DEM Source Access Error: Failed to query STAC catalog: {e}")
            
        if not items:
            raise RuntimeError(f"DEM Coverage Error: No Copernicus DEM data found for bbox {bbox.bbox}")
            
        item = items[0]
        if "data" not in item.assets:
            raise RuntimeError(f"DEM Asset Error: 'data' asset missing from item {item.id}")
            
        href = item.assets["data"].href
        if href.startswith("s3://"):
            href = href.replace("s3://", "https://s3.eu-central-1.amazonaws.com/")
        
        import rasterio
        try:
            logging.info(f"📥 Downloading DEM COG: {href}")
            with rasterio.Env(AWS_NO_SIGN_REQUEST='YES'):
                dem_asset = self.cog_processor.read_raster_window(href, bbox=list(bbox.bbox))
        except RasterReadError as e:
            raise RuntimeError(f"DEM Extraction Error: Failed to read DEM raster: {e}")
            
        dem_asset.stac_item_id = item.id
        return dem_asset

    def calculate_slope(self, elevation_asset: GeospatialRasterAsset) -> GeospatialRasterAsset:
        """Derives slope (degrees) from elevation using numpy gradient geometry."""
        logging.info("📐 Computing Terrain Slope Matrix...")
        
        # Check units validity (mixing degrees and meters produces invalid slope)
        if "4326" in elevation_asset.crs.lower() or "degree" in elevation_asset.crs.lower():
            logging.warning("⚠️ Slope derivation on a geographic CRS (degrees) produces invalid units. Reproject to UTM/metric first.")
            
        elev = elevation_asset.raw_array[0].astype(np.float32)
        res_x = abs(elevation_asset.resolution[0])
        res_y = abs(elevation_asset.resolution[1])
        
        dy, dx = np.gradient(elev, res_y, res_x)
        
        slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
        slope_deg = np.degrees(slope_rad).astype(np.float32)
        
        return GeospatialRasterAsset(
            raw_array=np.expand_dims(slope_deg, axis=0),
            raw_dtype="float32",
            scale_factor=1.0,
            add_offset=0.0,
            crs=elevation_asset.crs,
            transform=elevation_asset.transform,
            bounds=elevation_asset.bounds,
            resolution=elevation_asset.resolution,
            valid_data_mask=elevation_asset.valid_data_mask.copy(),
            nodata_value=elevation_asset.nodata_value,
            stac_item_id=elevation_asset.stac_item_id,
            asset_key="derived_slope",
            source_href=elevation_asset.source_href,
            acquisition_datetime=elevation_asset.acquisition_datetime
        )
