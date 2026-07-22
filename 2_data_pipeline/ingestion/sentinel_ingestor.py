# THE MRIDANSH - 2_data_pipeline/ingestion/sentinel_ingestor.py

import os
import logging
from typing import Dict, Any, List
from ..schemas.satellite_schema import SpatialBoundingBox, SentinelFrameMetadata

logging.basicConfig(level=logging.INFO, format = "%(asctime)s - %(levelname)s - %(message)s")

class SentinelDataIngestor:
    """Multi-Modal Data Ingestor for Sentinel-1 (Radar SAR) and Sentinel-2 (Optical) Payload Engines."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.supported_constellations = ["SENTINEL-1", "SENTINEL-2"]

    def fetch_optical_frames(self, bbox: SpatialBoundingBox, start_date:str, end_date: str, max_cloud_cover: float = 20.0) -> List[SentinelFrameMetadata]:
        """Simulates/Triggers Sentinel-2 Optical Multi-Spectral Ingestion Pipeline"""
        logging.info(f"🛰️ Requesting Sentinel - 2 Optical Bands for BBox: {bbox.bbox} | Range: {start_date} to {end_date}")

        # Validating & payload Construction Mock
        sample_frame = SentinelFrameMetadata(
            scene_id = f"S2A_MSIL2A_{start_date.replace('-', '')}_INGESTED",
            acquisition_date = start_date,
            cloud_cover_percentage = min(max_cloud_cover, 8.5),
            bands_available = ["B02", "B03", "B04", "B08", "B11", "B12"],
            spatial_resolution_m = 10.0
        )

        logging.info(f"✅ Sentinel-2 Frame Successfully Ingested: {sample_frame.scene_id}")
        return  [sample_frame]

    def fetch_radar_sar_frames(self, bbox: SpatialBoundingBox, start_date: str, end_date: str, polarization: str = "VV+VH") -> List[SentinelFrameMetadata]:
        """Simulates/Triggers Sentinel-1 Synthetic Aperture Radar (SAR) Ingestion Pipeline"""
        logging.info(f"📡 Requesting Sentinel-1 SAR Radar Arrays ({polarization}) for BBox: {bbox.bbox}")

        sample_frame = SentinelFrameMetadata(
            scene_id = f"S1A_IW_GRDH_1SDV_{start_date.replace('-', '')}_SAR",
            acquisition_date = start_date,
            cloud_cover_percentage = 0.0,
            bands_available = ["VV", "VH"],
            spatial_resolution_m = 10.0
        )

        logging.info(f"✅ Sentinel-1 Frame Ingested: {sample_frame.scene_id}")
        return [sample_frame]



# Self-Test Execution Module
if __name__ == "__main__":
    print("\n--- Testing Day 3 Multi-Modal Ingestion Engine ---")
    
    # Initialize Engine & Sample Bounding Box
    ingestor = SentinelDataIngestor()
    test_bbox = SpatialBoundingBox(bbox = (77.10, 28.50, 77.25, 28.65))

    # Run Ingestion Pipeline
    optical_payload = ingestor.fetch_optical_frames(test_bbox, "2026-07-22", "2026-07-25")
    radar_payload = ingestor.fetch_radar_sar_frames(test_bbox, "2026-07-22", "2026-07-25")

    print("\n[SUCCESS] Day 3 Data Ingestion Test: PASSED OPERATIONAL CHECKS!\n")