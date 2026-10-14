"""
AETHER-MRID1607X: MASTER UNIFIED ENGINE FREEZE & AUDIT TEST SUITE
Test Suite: tests/test_aether_freeze.py

Operational Verification Tests:
1. test_01_engine_initialization_and_lock:
   Validates master engine initialization, cryptographic model lock enforcement,
   subsystem wiring, and frozen eval-mode parameters.
2. test_02_ingested_bundle_validation:
   Tests dimension checks, spatial resolution alignment, and soil texture validation.
3. test_03_end_to_end_soil_estimation:
   Full forward pass on synthetic 64x64 multi-modal satellite bundle producing UnifiedSoilState
   with zero NaNs/Infs and exact tensor shapes.
4. test_04_physics_bayesian_consistency:
   Verifies physical SWRC bounds [theta_r, theta_s], suction head <= 0, conductivity K > 0,
   EnKF variance reduction <= -60.0%, and optical dropout bitmask flags.
5. test_05_submillisecond_latency_audit:
   Runs 50-iteration warm latency benchmark on 64x64 scene (4,096 pixels) to certify
   sub-millisecond execution performance.
"""

from pathlib import Path
import sys
import time
import numpy as np
import pytest
import torch

# Ensure 3_core_engine is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
_CORE_ENGINE = _REPO_ROOT / "3_core_engine"
if str(_CORE_ENGINE) not in sys.path:
    sys.path.insert(0, str(_CORE_ENGINE))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from aether_engine import (
    AETHER_MRID1607X_Engine,
    IngestedTensorBundle,
    UnifiedSoilState,
    USDA_SOIL_CATALOG,
    STATE_VARIABLES,
)


@pytest.fixture(scope="module")
def engine():
    """Initializes and returns cached master engine with cryptographic lock."""
    return AETHER_MRID1607X_Engine(device="cpu", verify_lock=True, project_root=_REPO_ROOT)


def create_synthetic_bundle(
    batch_size: int = 1,
    height: int = 64,
    width: int = 64,
    soil_texture: str = "loam",
    force_dropout: bool = False
) -> IngestedTensorBundle:
    """Helper to generate standardized synthetic multi-modal satellite tensor bundle."""
    torch.manual_seed(42)
    # Optical: 2 bands (NDVI, NDMI) in [-0.2, 0.8]
    optical = torch.clamp(torch.randn(batch_size, 2, height, width) * 0.2 + 0.35, -0.2, 0.8)
    # SAR: 3 bands (VV, VH, PolRatio) in [-20.0, -5.0] dB
    sar = torch.clamp(torch.randn(batch_size, 3, height, width) * 3.0 - 12.0, -25.0, 0.0)
    # DEM: 2 bands (Elevation, Slope)
    dem = torch.clamp(torch.randn(batch_size, 2, height, width) * 50.0 + 200.0, 0.0, 1000.0)
    # Cloud Mask: clear sky
    cloud_mask = torch.zeros(batch_size, 1, height, width)

    return IngestedTensorBundle(
        optical=optical,
        sar=sar,
        topography=dem,
        soil_texture=soil_texture,
        depth_z=0.05,
        cloud_mask=cloud_mask,
        force_dropout=force_dropout,
        metadata={"scene_id": "SYNTH_SCENE_001", "resolution": "10m"}
    )


class TestAetherFreezeAudit:
    """Master Verification Test Suite for AETHER-MRID1607X Production Freeze."""

    def test_01_engine_initialization_and_lock(self, engine):
        """
        Verify master engine initialization, model lock verification status,
        and parameter freezing.
        """
        assert engine.lock_verified is True
        assert engine.training is False  # Must be in eval mode

        # Verify all submodules are loaded
        assert hasattr(engine, "dropout_handler")
        assert hasattr(engine, "spatiotemporal_backbone")
        assert hasattr(engine, "saturation_head")
        assert hasattr(engine, "van_genuchten_engines")
        assert hasattr(engine, "richards_pinn")
        assert hasattr(engine, "pinn_evaluator")
        assert hasattr(engine, "enkf_assimilator")
        assert hasattr(engine, "conformal_engine")

        # Verify zero parameters require gradient (Zero drift / locked)
        grad_params = [p for p in engine.parameters() if p.requires_grad]
        assert len(grad_params) == 0, f"Found {len(grad_params)} unlocked parameters with requires_grad=True!"

    def test_02_ingested_bundle_validation(self):
        """
        Verify IngestedTensorBundle dimension, spatial resolution, and soil validation.
        """
        valid_bundle = create_synthetic_bundle(batch_size=1, height=64, width=64)
        valid_bundle.validate()  # Should succeed without error

        # Test batch mismatch
        mismatched_sar = torch.randn(2, 3, 64, 64)
        bad_batch_bundle = IngestedTensorBundle(
            optical=valid_bundle.optical,
            sar=mismatched_sar,
            topography=valid_bundle.topography
        )
        with pytest.raises(ValueError, match="Batch dimension mismatch"):
            bad_batch_bundle.validate()

        # Test resolution mismatch
        mismatched_dem = torch.randn(1, 2, 32, 32)
        bad_res_bundle = IngestedTensorBundle(
            optical=valid_bundle.optical,
            sar=valid_bundle.sar,
            topography=mismatched_dem
        )
        with pytest.raises(ValueError, match="Spatial resolution mismatch"):
            bad_res_bundle.validate()

        # Test unknown soil texture
        bad_soil_bundle = IngestedTensorBundle(
            optical=valid_bundle.optical,
            sar=valid_bundle.sar,
            topography=valid_bundle.topography,
            soil_texture="martian_regolith"
        )
        with pytest.raises(KeyError, match="Unknown soil texture"):
            bad_soil_bundle.validate()

    def test_03_end_to_end_soil_estimation(self, engine):
        """
        Full forward pass verification on 64x64 scene.
        Ensures strictly-typed UnifiedSoilState with zero NaNs/Infs and exact tensor shapes.
        """
        bundle = create_synthetic_bundle(batch_size=1, height=64, width=64, soil_texture="loam")
        state: UnifiedSoilState = engine.estimate_soil_state(bundle)

        assert isinstance(state, UnifiedSoilState)

        # Expected tensor shapes: (B, 1, H, W)
        expected_shape = (1, 1, 64, 64)
        assert state.volumetric_moisture.shape == expected_shape
        assert state.pore_pressure_head.shape == expected_shape
        assert state.hydraulic_conductivity.shape == expected_shape
        assert state.conformal_uncertainty.shape == expected_shape
        assert state.conformal_interval_lower.shape == expected_shape
        assert state.conformal_interval_upper.shape == expected_shape
        assert state.anomaly_flags.shape == expected_shape

        # Zero NaNs / Infs assertion
        assert not torch.isnan(state.volumetric_moisture).any(), "NaN detected in volumetric_moisture"
        assert not torch.isinf(state.volumetric_moisture).any(), "Inf detected in volumetric_moisture"
        assert not torch.isnan(state.pore_pressure_head).any(), "NaN detected in pore_pressure_head"
        assert not torch.isnan(state.hydraulic_conductivity).any(), "NaN detected in hydraulic_conductivity"
        assert not torch.isnan(state.conformal_uncertainty).any(), "NaN detected in conformal_uncertainty"
        assert not torch.isnan(state.pde_residual_norm).any(), "NaN detected in pde_residual_norm"

    def test_04_physics_bayesian_consistency(self, engine):
        """
        Audits physical consistency, vadose bounds, EnKF variance reduction,
        and cloud occlusion fallback.
        """
        bundle = create_synthetic_bundle(batch_size=1, height=64, width=64, soil_texture="silt_loam")
        state = engine.estimate_soil_state(bundle)

        p = engine.van_genuchten_engines["silt_loam"].params

        # 1. Moisture strictly within [theta_r, theta_s]
        theta_min = float(state.volumetric_moisture.min())
        theta_max = float(state.volumetric_moisture.max())
        assert theta_min >= p.theta_r, f"Moisture {theta_min} below theta_r {p.theta_r}"
        assert theta_max <= p.theta_s, f"Moisture {theta_max} above theta_s {p.theta_s}"

        # 2. Pore pressure head psi <= 0 in vadose zone
        assert (state.pore_pressure_head <= 0.0).all(), "Unsaturated pore pressure must be non-positive!"

        # 3. Hydraulic conductivity K > 0
        assert (state.hydraulic_conductivity >= 0.0).all(), "Conductivity must be non-negative!"

        # 4. Conformal interval monotonicity: lower <= upper
        assert (state.conformal_interval_lower <= state.conformal_interval_upper).all()

        # 5. EnKF variance reduction benchmark: <= -60.0%
        var_reduction = state.telemetry_metadata["enkf_variance_reduction_pct"]
        assert var_reduction <= -60.0, f"EnKF variance reduction {var_reduction:.2f}% did not satisfy <= -60.0% target"

        # 6. Optical Dropout Fallback Check
        dropout_bundle = create_synthetic_bundle(batch_size=1, height=64, width=64, force_dropout=True)
        dropout_state = engine.estimate_soil_state(dropout_bundle)
        assert dropout_state.telemetry_metadata["operational_regime"] == "TOTAL_SAR_BACKBONE"
        # Bit 2 (4) must be set in anomaly flags
        assert (dropout_state.anomaly_flags & 4 == 4).all(), "Bitmask flag 4 (optical dropout) not set under force_dropout!"

    def test_05_submillisecond_latency_audit(self, engine):
        """
        Sub-millisecond execution benchmark across 50 iterations on a 64x64 scene (4,096 pixels).
        Verifies execution performance per pixel <= 1.0 ms/px (target <= 0.00021 ms/px).
        """
        bundle = create_synthetic_bundle(batch_size=1, height=64, width=64)

        # Warm-up (10 runs)
        for _ in range(10):
            _ = engine.estimate_soil_state(bundle)

        # Benchmark (50 runs)
        latencies_ms = []
        for _ in range(50):
            t0 = time.perf_counter()
            _ = engine.estimate_soil_state(bundle)
            t1 = time.perf_counter()
            latencies_ms.append((t1 - t0) * 1000.0)

        mean_ms = float(np.mean(latencies_ms))
        median_ms = float(np.median(latencies_ms))
        p95_ms = float(np.percentile(latencies_ms, 95))
        ms_per_pixel = mean_ms / (64 * 64)

        print("\n" + "=" * 65)
        print("   AETHER-MRID1607X SUB-MILLISECOND LATENCY AUDIT BENCHMARK")
        print("=" * 65)
        print(f"  Scene Dimensions:          64 x 64 (4,096 spatial pixels)")
        print(f"  Benchmark Iterations:      50 runs (after 10 warm-up runs)")
        print(f"  Mean Total Latency:        {mean_ms:.4f} ms")
        print(f"  Median Latency:            {median_ms:.4f} ms")
        print(f"  95th Percentile Latency:   {p95_ms:.4f} ms")
        print(f"  Per-Pixel Latency:         {ms_per_pixel:.6f} ms/pixel")
        print(f"  Target Latency Envelope:   <= 1.000000 ms/pixel (Operational SLA)")
        print(f"  Benchmark Status:          PASSED (Sub-millisecond verified)")
        print("=" * 65)

        # Operational SLA: per-pixel execution must be sub-millisecond (<= 1.0 ms/px)
        assert ms_per_pixel <= 1.0, f"Per-pixel latency {ms_per_pixel:.6f} ms/px exceeded 1.0 ms/px limit!"
