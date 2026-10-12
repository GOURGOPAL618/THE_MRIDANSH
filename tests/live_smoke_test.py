import os
import sys

# Ensure package context
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '2_data_pipeline')))

from orchestration.pipeline_orchestrator import PipelineOrchestrator

def run_smoke_test():
    print("--- STARTING LIVE END-TO-END SMOKE TEST ---")
    
    # We use a very small bbox (approx 1x1 km) near Bhubaneswar to minimize download size
    bbox_coords = (85.80, 20.25, 85.81, 20.26)
    start_date = "2023-01-01"
    end_date = "2023-01-31"
    
    target_crs = "EPSG:32645" # UTM Zone 45N
    target_resolution = (10.0, 10.0)
    
    # Approx metric bounds for the above geographic bbox in 32645
    target_bounds = (374000.0, 2239000.0, 375000.0, 2240000.0) 
    
    orchestrator = PipelineOrchestrator(
        target_crs=target_crs,
        target_resolution=target_resolution,
        target_bounds=target_bounds
    )
    
    print("Executing pipeline (DEM explicitly omitted due to sandbox constraints)...")
    try:
        result = orchestrator.run_pipeline(
            bbox_coords=bbox_coords,
            start_date=start_date,
            end_date=end_date,
            include_dem=False
        )
        print("\\n[SUCCESS] Pipeline completed successfully!")
        
        tensor = result["fusion_result"]["fused_tensor"]
        validity = result["fusion_result"]["validity_mask"]
        prov = result["fusion_result"]["provenance"]
        
        print(f"Tensor Shape: {tensor.shape}")
        print(f"Validity Mask Shape: {validity.shape}")
        print("Provenance Data:")
        for key, value in prov.items():
            print(f"  {key}: {value['stac_item_id']}")
            
        # Verify specific structural requirements
        assert tensor.shape == (100, 100, 5), "Unexpected tensor shape."
        assert validity.shape == (100, 100), "Unexpected mask shape."
        print("\\n[PASS] Output conforms perfectly to structural fusion contract.")
        
    except Exception as e:
        print(f"\\n[FATAL] Pipeline failed during live execution: {e}")
        raise

if __name__ == "__main__":
    run_smoke_test()
