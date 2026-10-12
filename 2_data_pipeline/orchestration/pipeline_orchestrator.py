import logging
from typing import Any
import numpy as np

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from ingestion.sentinel_ingestor import SentinelDataIngestor
from preprocessing.cog_processor import COGRasterProcessor, RasterReadError
from preprocessing.raster_processor import RasterDataProcessor, GridAlignmentError
from fusion.satellite_fusion import SatelliteSAROpticalFusionEngine, MissingModalityError, GridMismatchError
from schemas.satellite_schema import SpatialBoundingBox, GeospatialRasterAsset

class PipelineOrchestrator:
    """End-to-End Execution Pipeline for AETHER-MRIDANSH."""

    def __init__(self, target_crs: str, target_resolution: tuple[float, float], target_bounds: tuple[float, float, float, float]):
        self.target_crs = target_crs
        self.target_resolution = target_resolution
        self.target_bounds = target_bounds
        
        self.ingestor = SentinelDataIngestor()
        self.cog_reader = COGRasterProcessor()
        self.aligner = RasterDataProcessor(target_resolution_m=target_resolution[0])
        self.fusion_engine = SatelliteSAROpticalFusionEngine(target_crs, target_resolution, target_bounds)

    def _read_and_align(self, href: str) -> GeospatialRasterAsset:
        # Read the full COG. The raster processor will clip it geographically using the target_bounds in the target_crs.
        asset = self.cog_reader.read_raster_window(href, bbox=None)
        aligned = self.aligner.reproject_asset(
            asset=asset,
            target_crs=self.target_crs,
            target_resolution=self.target_resolution,
            target_bounds=self.target_bounds,
            is_categorical=False
        )
        return aligned

    def _compute_index(self, nir_band: GeospatialRasterAsset, other_band: GeospatialRasterAsset, name: str) -> GeospatialRasterAsset:
        """Computes normalized difference indices like NDVI or NDMI."""
        nir_arr = nir_band.raw_array.astype(np.float32)
        other_arr = other_band.raw_array.astype(np.float32)
        
        denom = nir_arr + other_arr + 1e-8
        index_arr = (nir_arr - other_arr) / denom
        index_arr = np.clip(index_arr, -1.0, 1.0)
        
        valid_mask = nir_band.valid_data_mask & other_band.valid_data_mask
        
        return GeospatialRasterAsset(
            raw_array=index_arr,
            raw_dtype="float32",
            scale_factor=1.0,
            add_offset=0.0,
            crs=nir_band.crs,
            transform=nir_band.transform,
            bounds=nir_band.bounds,
            resolution=nir_band.resolution,
            valid_data_mask=valid_mask,
            nodata_value=nir_band.nodata_value,
            stac_item_id=nir_band.stac_item_id,
            asset_key=name,
            source_href=f"derived_{name}",
            acquisition_datetime=nir_band.acquisition_datetime
        )

    def run_pipeline(
        self,
        bbox_coords: tuple[float, float, float, float],
        start_date: str,
        end_date: str,
        include_dem: bool = False
    ) -> dict[str, Any]:
        logging.info("🚀 Starting End-to-End Orchestration...")
        bbox = SpatialBoundingBox(bbox=bbox_coords)
        
        # 1. Discover STAC assets
        opt_frames = self.ingestor.fetch_optical_frames(bbox, start_date, end_date, max_cloud_cover=20.0)
        sar_vv_frames = self.ingestor.fetch_radar_sar_frames(bbox, start_date, end_date, polarization="VV")
        sar_vh_frames = self.ingestor.fetch_radar_sar_frames(bbox, start_date, end_date, polarization="VH")
        
        if not opt_frames or not sar_vv_frames or not sar_vh_frames:
            raise RuntimeError("Pipeline Failure: Missing required STAC frames for SAR or Optical. Pipeline aborted.")
            
        opt_frame = opt_frames[0]
        vv_frame = sar_vv_frames[0]
        vh_frame = sar_vh_frames[0]
        
        # 2 & 3. Read and Align
        req_opt = ["red", "nir", "swir16"]
        for ro in req_opt:
            if ro not in opt_frame.asset_hrefs:
                raise RuntimeError(f"Pipeline Failure: Missing required '{ro}' asset in Optical Frame {opt_frame.scene_id}.")
                
        try:
            logging.info("📥 Reading and aligning assets via D06 Reprojection engine...")
            red_asset = self._read_and_align(opt_frame.asset_hrefs["red"])
            nir_asset = self._read_and_align(opt_frame.asset_hrefs["nir"])
            swir_asset = self._read_and_align(opt_frame.asset_hrefs["swir16"])
            
            vv_href = vv_frame.asset_hrefs.get("VV") or vv_frame.asset_hrefs.get("sar_href")
            vh_href = vh_frame.asset_hrefs.get("VH") or vh_frame.asset_hrefs.get("sar_href")
            
            vv_asset = self._read_and_align(vv_href)
            vh_asset = self._read_and_align(vh_href)
        except (RasterReadError, GridAlignmentError) as e:
            raise RuntimeError(f"Pipeline Failure: Raster extraction or alignment failed: {e}")
            
        # Retain provenance
        vv_asset.stac_item_id = vv_frame.scene_id
        vh_asset.stac_item_id = vh_frame.scene_id
        red_asset.stac_item_id = opt_frame.scene_id
        nir_asset.stac_item_id = opt_frame.scene_id
        swir_asset.stac_item_id = opt_frame.scene_id
        
        # 4. Compute NDVI & NDMI
        logging.info("🧮 Computing NDVI and NDMI indices from aligned surface reflectances...")
        ndvi_asset = self._compute_index(nir_asset, red_asset, "OPTICAL_NDVI")
        ndmi_asset = self._compute_index(nir_asset, swir_asset, "OPTICAL_NDMI")
        
        # Optional DEM
        ele_aligned = None
        slope_aligned = None
        if include_dem:
            from preprocessing.dem_processor import DEMTerrainEngine
            dem_engine = DEMTerrainEngine()
            try:
                ele_asset = dem_engine.fetch_dem_asset(bbox)
                ele_aligned = self.aligner.reproject_asset(
                    asset=ele_asset,
                    target_crs=self.target_crs,
                    target_resolution=self.target_resolution,
                    target_bounds=self.target_bounds,
                    is_categorical=False
                )
                slope_aligned = dem_engine.calculate_slope(ele_aligned)
            except Exception as e:
                raise RuntimeError(f"Pipeline Failure: Optional DEM acquisition requested but failed: {e}")

        # 5. Invoke Fusion
        try:
            logging.info("🔗 Triggering D08 strict fusion engine...")
            fusion_result = self.fusion_engine.create_fused_spatial_tensor(
                sar_vv=vv_asset,
                sar_vh=vh_asset,
                ndvi=ndvi_asset,
                ndmi=ndmi_asset,
                dem_elevation=ele_aligned,
                dem_slope=slope_aligned
            )
        except (MissingModalityError, GridMismatchError) as e:
            raise RuntimeError(f"Pipeline Failure: Fusion engine rejected inputs: {e}")
            
        logging.info("✅ End-to-End Orchestration complete.")
        return {
            "status": "SUCCESS",
            "target_grid": {
                "crs": self.target_crs,
                "resolution": self.target_resolution,
                "bounds": self.target_bounds
            },
            "fusion_result": fusion_result
        }
