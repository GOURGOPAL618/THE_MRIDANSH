
import logging
from schemas.satellite_schema import SpatialBoundingBox, SentinelFrameMetadata
from .stac_client import SatelliteSTACClient

class SentinelDataIngestor:
    """High-level orchestrator for Sentinel-1/2 data discovery."""

    def __init__(self, stac_client: SatelliteSTACClient | None = None):
        self.supported_constellations = ["SENTINEL-1", "SENTINEL-2"]
        self.stac_client = stac_client or SatelliteSTACClient()

    def fetch_optical_frames(
        self,
        bbox: SpatialBoundingBox,
        start_date: str,
        end_date: str,
        max_cloud_cover: float = 20.0,
    ) -> list[SentinelFrameMetadata]:
        """Triggers Sentinel-2 Optical Multi-Spectral Ingestion Pipeline via STAC"""
        logging.info(f"🚀 Requesting Sentinel-2 Optical Bands for BBox: {bbox.bbox} | Range: {start_date} to {end_date}")

        raw_results = self.stac_client.search_sentinel2_optical(
            bbox=list(bbox.bbox),
            start_date=start_date,
            end_date=end_date,
            max_cloud_cover=max_cloud_cover,
            limit=5
        )

        frames = []
        for res in raw_results:
            assets = res.get("assets", {})
            valid_assets = {k: v for k, v in assets.items() if v is not None}
            if not valid_assets:
                continue

            frame = SentinelFrameMetadata(
                scene_id=res["scene_id"],
                acquisition_date=res.get("datetime", start_date)[:10] if res.get("datetime") else start_date,
                cloud_cover_percentage=res.get("cloud_cover", 0.0),
                bands_available=list(valid_assets.keys()),
                asset_hrefs=valid_assets,
                spatial_resolution_m=10.0,
            )
            frames.append(frame)
            logging.info(f"✅ Sentinel-2 Frame Found: {frame.scene_id}")

        if not frames:
            logging.warning("⚠️ No Sentinel-2 optical scenes found for the given criteria.")
        
        return frames

    def fetch_radar_sar_frames(
        self,
        bbox: SpatialBoundingBox,
        start_date: str,
        end_date: str,
        polarization: str = "VV+VH",
    ) -> list[SentinelFrameMetadata]:
        """Triggers Sentinel-1 SAR Ingestion Pipeline via STAC"""
        logging.info(f"📡 Requesting Sentinel-1 SAR Radar Arrays ({polarization}) for BBox: {bbox.bbox}")

        # The basic STAC client currently supports fetching one polarization asset explicitly via search parameter.
        # Defaulting to VV if mixed or unknown is requested, as the stac client uses basic substring matching.
        target_pol = "VV" if "VV" in polarization else "VH"

        raw_results = self.stac_client.search_sentinel1_sar(
            bbox=list(bbox.bbox),
            start_date=start_date,
            end_date=end_date,
            polarization=target_pol,
            limit=5
        )

        frames = []
        for res in raw_results:
            href = res.get("sar_href")
            if not href:
                continue

            frame = SentinelFrameMetadata(
                scene_id=res["scene_id"],
                acquisition_date=res.get("datetime", start_date)[:10] if res.get("datetime") else start_date,
                cloud_cover_percentage=0.0,
                bands_available=[target_pol],
                asset_hrefs={target_pol: href},
                spatial_resolution_m=10.0,
            )
            frames.append(frame)
            logging.info(f"✅ Sentinel-1 Frame Found: {frame.scene_id}")

        if not frames:
            logging.warning("⚠️ No Sentinel-1 SAR scenes found for the given criteria.")
            
        return frames

# Self-Test Execution Module
if __name__ == "__main__":
    print("\n--- Sentinel Ingestor & STAC Integration tests moved to tests/test_sentinel_ingestor_d03.py ---")
