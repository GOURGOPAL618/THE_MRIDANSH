import os
import sys
import unittest
import torch

# Ensure package context
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '3_core_engine')))

from physics.richards_engine import RichardsSoilPhysicsEngine

class TestRichardsEngineD03(unittest.TestCase):
    def setUp(self):
        self.engine = RichardsSoilPhysicsEngine()
        torch.manual_seed(42)

    def test_trp_01_valid_inputs(self):
        print("\\n--- T-RP-01: Valid inputs produce documented shapes ---")
        moisture = torch.empty(2, 64, 64).uniform_(0.15, 0.35)
        out = self.engine.compute_richards_flux(moisture, depth_interval_m=0.1)
        self.assertEqual(out["hydraulic_conductivity"].shape, (2, 64, 64))
        self.assertEqual(out["water_flux"].shape, (2, 64, 64))
        self.assertEqual(out["physics_constraint_loss"].shape, ())
        print("[PASS] T-RP-01: Correctly maintained exact structural topology.")

    def test_trp_02_invalid_dimensions(self):
        print("\\n--- T-RP-02: Invalid dimensions fail explicitly ---")
        moisture_1d = torch.empty(10).uniform_(0.1, 0.3)
        with self.assertRaisesRegex(ValueError, "must have at least 2 spatial dimensions"):
            self.engine.compute_richards_flux(moisture_1d)
        print("[PASS] T-RP-02: Explicitly trapped rank-1 tensors unable to form a spatial gradient.")

    def test_trp_03_finite_results(self):
        print("\\n--- T-RP-03: CPU execution produces finite results ---")
        # Extremely low moisture
        moisture = torch.full((10, 10), 0.05)
        out = self.engine.compute_richards_flux(moisture)
        self.assertTrue(torch.isfinite(out["hydraulic_conductivity"]).all())
        self.assertTrue(torch.isfinite(out["water_flux"]).all())
        self.assertTrue(torch.isfinite(out["physics_constraint_loss"]).all())
        print("[PASS] T-RP-03: Handled boundary saturation values with stable numerics.")

    def test_trp_04_autograd(self):
        print("\\n--- T-RP-04: Autograd produces finite, nonzero gradients ---")
        moisture = torch.empty(10, 10).uniform_(0.15, 0.35)
        moisture.requires_grad_(True)
        
        out = self.engine.compute_richards_flux(moisture)
        
        # We explicitly trigger a backward pass using the computed physics constraint loss.
        # Due to the mathematical formulation of the prototype (which ignores gravity),
        # water flux is strictly non-positive, so the constraint loss acts strictly
        # as a non-zero L2 spatial smoothing penalty.
        loss = out["physics_constraint_loss"]
        loss.backward()
        
        self.assertIsNotNone(moisture.grad)
        self.assertTrue(torch.isfinite(moisture.grad).all())
        self.assertTrue(moisture.grad.abs().sum() > 0)
        
        # Test differentiation with respect to model parameters
        self.assertIsNotNone(self.engine.ks_sat.grad)
        self.assertTrue(torch.isfinite(self.engine.ks_sat.grad).all())
        self.assertTrue(self.engine.ks_sat.grad.abs().item() > 0)
        
        print("[PASS] T-RP-04: Confirmed physical model maintains a mathematically valid backward autograd graph.")

    def test_trp_05_physical_invariant(self):
        print("\\n--- T-RP-05: Simple physical behavior / invariant ---")
        # A perfectly uniform moisture field has 0 spatial gradient. 
        # Therefore, lateral flux = 0 under the engine's original Darcian formulation.
        moisture_flat = torch.full((20, 20), 0.25)
        out = self.engine.compute_richards_flux(moisture_flat)
        flux = out["water_flux"]
        self.assertTrue(torch.allclose(flux, torch.zeros_like(flux), atol=1e-5))
        print("[PASS] T-RP-05: Verified invariant: uniform moisture gradient yields zero Darcian flux.")

    def test_trp_06_api_compatibility(self):
        print("\\n--- T-RP-06: API compatibility ---")
        # Existing callers expected a single output dict with specific keys 
        moisture = torch.empty(5, 5).uniform_(0.2, 0.3)
        out = self.engine.compute_richards_flux(moisture)
        self.assertIn("hydraulic_conductivity", out)
        self.assertIn("water_flux", out)
        self.assertIn("physics_constraint_loss", out)
        print("[PASS] T-RP-06: Verified 100% dictionary key contract compatibility.")

if __name__ == '__main__':
    unittest.main()
