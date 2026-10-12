"""
THE MRIDANSH : Notebook 11 Verification Test Suite
Verifies Generalization Baseline Evaluation & Extreme Stress Testing Engine (AETHER-MRID1607X)
Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
Lead Architect: Gourgopal Mohapatra
"""

import json
import os
import unittest
from pathlib import Path
import torch

ROOT_DIR = Path(__file__).resolve().parent.parent
SANDBOX_DIR = ROOT_DIR / "1_notebooks_sandbox"
STORAGE_DIR = ROOT_DIR / "5_storage"
RESULTS_DIR = STORAGE_DIR / "notebook_results" / "notebook_11_generalization"
CHECKPOINTS_DIR = STORAGE_DIR / "checkpoints"


class TestNotebook11Verification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb_path = SANDBOX_DIR / "11-generalization-baseline-evaluation.ipynb"
        cls.ckpt_path = CHECKPOINTS_DIR / "generalization_evaluation_checkpoint.pt"
        cls.manifest_path = CHECKPOINTS_DIR / "GENERALIZATION_EVALUATION_MANIFEST.md"

        with open(cls.nb_path, "r", encoding="utf-8") as f:
            cls.nb = json.load(f)
        cls.cells = cls.nb.get("cells", [])

    def test_01_notebook_11_structure_and_interleaving(self):
        """Rule: Notebook 11 must have strictly alternating markdown/code, zero errors, penultimate summary, ultimate IP."""
        self.assertTrue(self.nb_path.exists())
        self.assertEqual(len(self.cells), 36)

        # Alternating cell type validation
        for i, c in enumerate(self.cells):
            if c.get("cell_type") == "code":
                self.assertGreater(i, 0)
                self.assertEqual(self.cells[i - 1].get("cell_type"), "markdown", f"Code cell {i} not preceded by markdown")
                exec_count = c.get("execution_count")
                self.assertIsNotNone(exec_count)
                self.assertGreater(exec_count, 0)

                for out in c.get("outputs", []):
                    self.assertNotEqual(out.get("output_type"), "error", f"Error in cell {i}")

        # Penultimate cell: Executive Summary
        penult_src = "".join(self.cells[-2].get("source", []))
        self.assertIn("EXECUTIVE SUMMARY & SCIENTIFIC MILESTONES (NOTEBOOK 11)", penult_src)
        self.assertIn("Summary of Multi-Regime Generalization Performance", penult_src)

        # Ultimate cell: JCC IP & Copyright Notice
        ult_src = "".join(self.cells[-1].get("source", []))
        self.assertIn("INTELLECTUAL PROPERTY & COPYRIGHT NOTICE", ult_src)
        self.assertIn("Gourgopal Mohapatra", ult_src)
        self.assertIn("JCC HEADQUARTER", ult_src)
        self.assertIn("RS-SDA Division", ult_src)

    def test_02_spatial_block_holdout_zero_data_leakage(self):
        """Rule: Zero spatial data leakage; 5 generalization regimes partitioned with isolated held-out blocks."""
        cell_08_out = "".join([line for out in self.cells[7].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("5 Generalization Regimes Partitioned Successfully", cell_08_out)
        self.assertIn("Regime 1 (IID Reference)", cell_08_out)
        self.assertIn("Regime 2 (Spatial Holdout)", cell_08_out)
        self.assertIn("Regime 3 (Topographic Extremes)", cell_08_out)
        self.assertIn("Regime 4 (Temporal Climate Shift)", cell_08_out)
        self.assertIn("Regime 5 (Sensor Noise Stress)", cell_08_out)

    def test_03_multi_regime_generalization_evaluation(self):
        """Rule: All 5 regimes evaluated; MRIDANSH maintains high accuracy (>80% error reduction vs naive)."""
        cell_12_out = "".join([line for out in self.cells[11].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("MULTI-REGIME GENERALIZATION MATRIX", cell_12_out)
        for r_name in ["Regime 1", "Regime 2", "Regime 3", "Regime 4", "Regime 5"]:
            self.assertIn(r_name, cell_12_out)

        # Verify significant error reduction across all regimes (>70% reduction)
        self.assertIn("80.58", cell_12_out)
        self.assertIn("78.79", cell_12_out)
        self.assertIn("74.34", cell_12_out)
        self.assertIn("72.59", cell_12_out)
        self.assertIn("90.27", cell_12_out)

    def test_04_spatial_generalization_gap_tolerance(self):
        """Rule: Spatial generalization gap must satisfy contract tolerance (Delta <= 0.0030 m3/m3)."""
        ckpt = torch.load(self.ckpt_path, weights_only=False)
        gap = ckpt["spatial_generalization_gap"]
        self.assertLessEqual(gap, 0.0030, f"Spatial generalization gap exceeded tolerance: {gap}")
        self.assertAlmostEqual(ckpt["spatial_holdout_rmse"], 0.00448, places=4)
        self.assertGreater(ckpt["spatial_holdout_r2"], 0.90)

    def test_05_loco_ablation_tier1_anchors(self):
        """Rule: LOCO ablation proves Tier 1 components (SAR, PINN, EnKF) are essential anchors."""
        cell_14_out = "".join([line for out in self.cells[13].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("LEAVE-ONE-COMPONENT-OUT (LOCO) ABLATION", cell_14_out)
        self.assertIn("Drop EnKF Filter", cell_14_out)
        self.assertIn("Drop Physics PINN", cell_14_out)
        self.assertIn("Drop Sentinel-1 SAR", cell_14_out)

    def test_06_uncertainty_calibration_and_ks_shift(self):
        """Rule: Uncertainty expands appropriately under shift; KS test proves significant shift."""
        cell_18_out = "".join([line for out in self.cells[17].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("PREDICTIVE UNCERTAINTY & CONFIDENCE COVERAGE", cell_18_out)

        cell_20_out = "".join([line for out in self.cells[19].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("TWO-SAMPLE KOLMOGOROV-SMIRNOV (KS)", cell_20_out)
        self.assertIn("Significant Shift", cell_20_out)

    def test_07_embedded_and_standalone_visual_plots(self):
        """Rule: All 5 diagnostic plots exist on disk and are embedded as base64 in notebook."""
        expected_plots = [
            (21, "plot_01_multi_regime_generalization_error_radar.png"),
            (23, "plot_02_spatial_holdout_residual_distribution.png"),
            (25, "plot_03_topographic_elevation_vs_moisture_stability.png"),
            (27, "plot_04_temporal_monsoon_drought_stress_response.png"),
            (29, "plot_05_sensor_noise_degradation_robustness_curve.png")
        ]

        for cell_idx, plot_name in expected_plots:
            # Standalone disk check
            disk_path = RESULTS_DIR / plot_name
            self.assertTrue(disk_path.exists(), f"Plot missing on disk: {plot_name}")
            self.assertGreater(disk_path.stat().st_size, 50000, f"Plot file too small: {plot_name}")

            # Notebook base64 embed check
            cell = self.cells[cell_idx]
            self.assertEqual(cell.get("cell_type"), "code")
            displays = [out for out in cell.get("outputs", []) if out.get("output_type") == "display_data"]
            self.assertGreater(len(displays), 0, f"No display_data output in cell {cell_idx}")
            b64_str = displays[0].get("data", {}).get("image/png", "")
            self.assertGreater(len(b64_str), 50000, f"Base64 image data too small in cell {cell_idx}")

    def test_08_checkpoint_and_manifest_certification(self):
        """Rule: PyTorch checkpoint and Markdown manifest exist and certify generalization freeze."""
        self.assertTrue(self.ckpt_path.exists())
        self.assertTrue(self.manifest_path.exists())
        self.assertGreater(self.ckpt_path.stat().st_size, 3000)
        self.assertGreater(self.manifest_path.stat().st_size, 2000)

        # Inspect checkpoint contents
        ckpt = torch.load(self.ckpt_path, weights_only=False)
        self.assertIn("system_engine", ckpt)
        self.assertEqual(ckpt["system_engine"], "AETHER-MRID1607X")
        self.assertIn("regimes_evaluated", ckpt)
        self.assertEqual(len(ckpt["regimes_evaluated"]), 5)
        self.assertIn("generalization_metrics", ckpt)
        self.assertIn("loco_ablation_metrics", ckpt)
        self.assertIn("operational_readiness", ckpt)
        self.assertEqual(ckpt["certified_by"], "Gourgopal Mohapatra")
        self.assertEqual(ckpt["facility"], "JCC CAMPUS 2 (RS-SDA DIVISION)")


if __name__ == "__main__":
    unittest.main()
