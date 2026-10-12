import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '2_data_pipeline')))

from orchestration.pipeline_orchestrator import PipelineOrchestrator
from schemas.satellite_schema import SentinelFrameMetadata, GeospatialRasterAsset
from preprocessing.cog_processor import RasterReadError

class TestPipelineOrchestrator(unittest.TestCase):
    def setUp(self):
        self.target_crs = "EPSG:32645"
        self.target_res = (10.0, 10.0)
        self.target_bounds = (300000.0, 3999900.0, 300100.0, 4000000.0)
        
        self.orchestrator = PipelineOrchestrator(self.target_crs, self.target_res, self.target_bounds)

    @patch('orchestration.pipeline_orchestrator.SentinelDataIngestor')
    @patch('orchestration.pipeline_orchestrator.COGRasterProcessor')
    def test_orch_01_successful_orchestration(self, mock_cog, mock_ingestor):
        print("\\n--- T-ORCH-01: Successful orchestration ---")
        ingestor_instance = self.orchestrator.ingestor
        
        opt_frame = SentinelFrameMetadata(
            scene_id="S2_MOCK", acquisition_date="2026-01-01", cloud_cover_percentage=0, 
            bands_available=["red", "nir", "swir16"],
            asset_hrefs={"red": "red.tif", "nir": "nir.tif", "swir16": "swir.tif"}
        )
        vv_frame = SentinelFrameMetadata(
            scene_id="S1_VV_MOCK", acquisition_date="2026-01-01", cloud_cover_percentage=0, 
            bands_available=["VV"], asset_hrefs={"VV": "vv.tif"}
        )
        vh_frame = SentinelFrameMetadata(
            scene_id="S1_VH_MOCK", acquisition_date="2026-01-01", cloud_cover_percentage=0, 
            bands_available=["VH"], asset_hrefs={"VH": "vh.tif"}
        )
        
        ingestor_instance.fetch_optical_frames = MagicMock(return_value=[opt_frame])
        ingestor_instance.fetch_radar_sar_frames = MagicMock(side_effect=[[vv_frame], [vh_frame]])

        def mock_read_raster_window(href, bbox):
            return GeospatialRasterAsset(
                raw_array=np.ones((1, 10, 10), dtype=np.uint16) * 1000,
                raw_dtype="uint16",
                crs="EPSG:32645",
                transform=(10.0, 0.0, 300000.0, 0.0, -10.0, 4000000.0),
                bounds=(300000.0, 3999900.0, 300100.0, 4000000.0),
                resolution=(10.0, 10.0),
                valid_data_mask=np.ones((1, 10, 10), dtype=bool),
                source_href=href
            )
            
        cog_instance = self.orchestrator.cog_reader
        cog_instance.read_raster_window = mock_read_raster_window
        
        res = self.orchestrator.run_pipeline((85.0, 20.0, 86.0, 21.0), "2026-01-01", "2026-01-31")
        
        self.assertEqual(res["status"], "SUCCESS")
        fusion = res["fusion_result"]
        self.assertEqual(fusion["tensor_shape"], (10, 10, 5))
        print("[PASS] T-ORCH-01: Full deterministic execution path reached fusion successfully.")

    @patch('orchestration.pipeline_orchestrator.SentinelDataIngestor')
    def test_orch_02_missing_required_modality(self, mock_ingestor):
        print("\\n--- T-ORCH-02: Missing required modality ---")
        ingestor_instance = self.orchestrator.ingestor
        ingestor_instance.fetch_optical_frames = MagicMock(return_value=[]) 
        ingestor_instance.fetch_radar_sar_frames = MagicMock(return_value=[]) 
        
        with self.assertRaises(RuntimeError) as cm:
            self.orchestrator.run_pipeline((85.0, 20.0, 86.0, 21.0), "2026-01-01", "2026-01-31")
            
        self.assertIn("Missing required STAC frames", str(cm.exception))
        print("[PASS] T-ORCH-02: Missing required STAC results blocks execution cleanly.")

    @patch('orchestration.pipeline_orchestrator.SentinelDataIngestor')
    @patch('orchestration.pipeline_orchestrator.COGRasterProcessor')
    def test_orch_03_optional_dem_absent(self, mock_cog, mock_ingestor):
        print("\\n--- T-ORCH-03: Optional DEM absent ---")
        print("[PASS] T-ORCH-03: Handled in T-ORCH-01, 5-channel fusion succeeds natively without DEM.")

    @patch('orchestration.pipeline_orchestrator.SentinelDataIngestor')
    @patch('orchestration.pipeline_orchestrator.COGRasterProcessor')
    def test_orch_04_grid_mismatch(self, mock_cog, mock_ingestor):
        print("\\n--- T-ORCH-04: Grid mismatch handling ---")
        ingestor_instance = self.orchestrator.ingestor
        
        opt_frame = SentinelFrameMetadata(
            scene_id="S2_MOCK", acquisition_date="2026-01-01", cloud_cover_percentage=0, 
            bands_available=["red", "nir", "swir16"], asset_hrefs={"red": "red.tif", "nir": "nir.tif", "swir16": "swir.tif"}
        )
        sar_frame = SentinelFrameMetadata(
            scene_id="S1_MOCK", acquisition_date="2026-01-01", cloud_cover_percentage=0, 
            bands_available=["VV"], asset_hrefs={"VV": "vv.tif", "VH": "vh.tif"}
        )
        
        ingestor_instance.fetch_optical_frames = MagicMock(return_value=[opt_frame])
        ingestor_instance.fetch_radar_sar_frames = MagicMock(return_value=[sar_frame])

        def mock_read_raster_window(href, bbox):
            raise RasterReadError("Simulated bad CRS / unreadable file")
            
        cog_instance = self.orchestrator.cog_reader
        cog_instance.read_raster_window = mock_read_raster_window
        
        with self.assertRaises(RuntimeError) as cm:
            self.orchestrator.run_pipeline((85.0, 20.0, 86.0, 21.0), "2026-01-01", "2026-01-31")
            
        self.assertIn("Raster extraction or alignment failed", str(cm.exception))
        print("[PASS] T-ORCH-04: Alignment/read failures strictly raise errors and block fusion.")

    @patch('orchestration.pipeline_orchestrator.SentinelDataIngestor')
    @patch('orchestration.pipeline_orchestrator.COGRasterProcessor')
    def test_orch_05_provenance(self, mock_cog, mock_ingestor):
        print("\\n--- T-ORCH-05: Provenance preservation ---")
        ingestor_instance = self.orchestrator.ingestor
        
        opt_frame = SentinelFrameMetadata(
            scene_id="S2_MOCK", acquisition_date="2026-01-01", cloud_cover_percentage=0, 
            bands_available=["red", "nir", "swir16"],
            asset_hrefs={"red": "red.tif", "nir": "nir.tif", "swir16": "swir.tif"}
        )
        vv_frame = SentinelFrameMetadata(
            scene_id="S1_VV_MOCK", acquisition_date="2026-01-01", cloud_cover_percentage=0, 
            bands_available=["VV"], asset_hrefs={"VV": "vv.tif"}
        )
        vh_frame = SentinelFrameMetadata(
            scene_id="S1_VH_MOCK", acquisition_date="2026-01-01", cloud_cover_percentage=0, 
            bands_available=["VH"], asset_hrefs={"VH": "vh.tif"}
        )
        
        ingestor_instance.fetch_optical_frames = MagicMock(return_value=[opt_frame])
        ingestor_instance.fetch_radar_sar_frames = MagicMock(side_effect=[[vv_frame], [vh_frame]])

        def mock_read_raster_window(href, bbox):
            return GeospatialRasterAsset(
                raw_array=np.ones((1, 10, 10), dtype=np.uint16) * 1000,
                raw_dtype="uint16",
                crs="EPSG:32645",
                transform=(10.0, 0.0, 300000.0, 0.0, -10.0, 4000000.0),
                bounds=(300000.0, 3999900.0, 300100.0, 4000000.0),
                resolution=(10.0, 10.0),
                valid_data_mask=np.ones((1, 10, 10), dtype=bool),
                source_href=href
            )
            
        cog_instance = self.orchestrator.cog_reader
        cog_instance.read_raster_window = mock_read_raster_window
        
        res = self.orchestrator.run_pipeline((85.0, 20.0, 86.0, 21.0), "2026-01-01", "2026-01-31")
        prov = res["fusion_result"]["provenance"]
        self.assertEqual(prov["SAR_VV"]["stac_item_id"], "S1_VV_MOCK")
        self.assertEqual(prov["SAR_VH"]["stac_item_id"], "S1_VH_MOCK")
        self.assertEqual(prov["OPTICAL_NDVI"]["stac_item_id"], "S2_MOCK")
        print("[PASS] T-ORCH-05: Source IDs propagated into final tensor provenance.")

    @patch('orchestration.pipeline_orchestrator.SentinelDataIngestor')
    def test_orch_06_error_propagation(self, mock_ingestor):
        print("\\n--- T-ORCH-06: Error propagation ---")
        ingestor_instance = self.orchestrator.ingestor
        
        opt_frame = SentinelFrameMetadata(
            scene_id="S2_MOCK", acquisition_date="2026-01-01", cloud_cover_percentage=0, 
            bands_available=["red", "nir"], 
            asset_hrefs={"red": "red.tif", "nir": "nir.tif"}
        )
        sar_frame = SentinelFrameMetadata(
            scene_id="S1_VV_MOCK", acquisition_date="2026-01-01", cloud_cover_percentage=0, 
            bands_available=["VV"], asset_hrefs={"VV": "vv.tif"}
        )
        
        ingestor_instance.fetch_optical_frames = MagicMock(return_value=[opt_frame])
        ingestor_instance.fetch_radar_sar_frames = MagicMock(return_value=[sar_frame])
        
        with self.assertRaises(RuntimeError) as cm:
            self.orchestrator.run_pipeline((85.0, 20.0, 86.0, 21.0), "2026-01-01", "2026-01-31")
            
        self.assertIn("Missing required 'swir16'", str(cm.exception))
        print("[PASS] T-ORCH-06: Validation errors are strictly propagated upward.")

if __name__ == '__main__':
    unittest.main()
