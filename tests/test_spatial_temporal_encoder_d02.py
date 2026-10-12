import os
import sys
import unittest
import torch

# Ensure package context
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '3_core_engine')))

from models.spatial_temporal_encoder import SpatialTemporalEncoderBackbone

class TestNNBackboneD02(unittest.TestCase):
    def setUp(self):
        # 5 channels is the strictly defined requirement without DEM.
        self.model = SpatialTemporalEncoderBackbone(in_channels=5, feature_dim=64)
        torch.manual_seed(42)

    def test_tnn_01_snapshot_support(self):
        print("\\n--- T-NN-01: Snapshot representation support (T=1) ---")
        # 5 channels from fusion output, T=1 snapshot
        x = torch.randn(2, 1, 5, 64, 64) # B=2, T=1, C=5, H=64, W=64
        out = self.model(x)
        self.assertIn("latent_representation", out)
        print("[PASS] T-NN-01: Successfully executed 5-channel snapshot with T=1.")

    def test_tnn_02_output_shape(self):
        print("\\n--- T-NN-02: Configurable shape propagation ---")
        # Ensure independence from hardcoded 120x120
        x = torch.randn(3, 4, 5, 20, 30) # B=3, T=4, C=5, H=20, W=30
        out = self.model(x)["latent_representation"]
        self.assertEqual(out.shape, (3, 64, 20, 30))
        print("[PASS] T-NN-02: Output tensor matches exact (B, feature_dim, H, W) specification.")

    def test_tnn_03_finite_outputs(self):
        print("\\n--- T-NN-03: Finite Forward Pass ---")
        x = torch.randn(1, 2, 5, 10, 10)
        out = self.model(x)["latent_representation"]
        self.assertTrue(torch.isfinite(out).all())
        print("[PASS] T-NN-03: Model preserves finite numerics through GRU and CNN blocks.")

    def test_tnn_04_gradients(self):
        print("\\n--- T-NN-04: Autograd Backpropagation ---")
        x = torch.randn(2, 2, 5, 16, 16)
        out = self.model(x)["latent_representation"]
        
        loss = out.mean()
        loss.backward()
        
        # Verify gradients populated for CNN parameters
        param = next(self.model.spatial_encoder.parameters())
        self.assertIsNotNone(param.grad)
        self.assertTrue(torch.isfinite(param.grad).all())
        self.assertTrue(param.grad.abs().sum().item() > 0)
        
        # Verify gradients populated for GRU parameters
        gru_param = next(self.model.temporal_encoder.parameters())
        self.assertIsNotNone(gru_param.grad)
        self.assertTrue(torch.isfinite(gru_param.grad).all())
        self.assertTrue(gru_param.grad.abs().sum().item() > 0)
        
        print("[PASS] T-NN-04: Confirmed nonzero finite gradients mapped to CNN and GRU parameters.")

    def test_tnn_05_invalid_shapes(self):
        print("\\n--- T-NN-05: Strict Data Contract Execution ---")
        x_wrong_rank = torch.randn(2, 5, 10, 10) # 4D
        with self.assertRaisesRegex(ValueError, "Expected 5D input"):
            self.model(x_wrong_rank)
            
        x_wrong_channels = torch.randn(1, 1, 8, 10, 10) # 8 channels mismatch
        with self.assertRaisesRegex(ValueError, "Expected 5 channels"):
            self.model(x_wrong_channels)
            
        print("[PASS] T-NN-05: Strict dimensionality traps properly enforce (B, T, C, H, W) geometry.")

    def test_tnn_06_deterministic(self):
        print("\\n--- T-NN-06: Deterministic execution constraints ---")
        torch.manual_seed(99)
        model1 = SpatialTemporalEncoderBackbone(in_channels=5, feature_dim=16)
        x = torch.randn(1, 1, 5, 8, 8)
        out1 = model1(x)["latent_representation"]
        
        torch.manual_seed(99)
        model2 = SpatialTemporalEncoderBackbone(in_channels=5, feature_dim=16)
        out2 = model2(x)["latent_representation"]
        
        self.assertTrue(torch.allclose(out1, out2))
        print("[PASS] T-NN-06: Deterministic execution verified across bounded seeds.")

if __name__ == '__main__':
    unittest.main()
