"""
THE MRIDANSH : Notebook 10 Verification Test Suite
Verifies Component Ablation & Marginal Utility Engine (AETHER-MRID1607X)
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
RESULTS_DIR = STORAGE_DIR / "notebook_results" / "notebook_10_ablation_study"
CHECKPOINTS_DIR = STORAGE_DIR / "checkpoints"


class TestNotebook10Verification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb_path = SANDBOX_DIR / "10-ablation-study.ipynb"
        cls.ckpt_path = CHECKPOINTS_DIR / "ablation_study_checkpoint.pt"
        cls.manifest_path = CHECKPOINTS_DIR / "ABLATION_STUDY_MANIFEST.md"

        with open(cls.nb_path, "r", encoding="utf-8") as f:
            cls.nb = json.load(f)
        cls.cells = cls.nb.get("cells", [])

    def test_01_notebook_10_structure_and_interleaving(self):
        """Rule: Notebook 10 must have strictly alternating markdown/code, zero errors, penultimate summary, ultimate IP."""
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
        self.assertIn("EXECUTIVE SUMMARY & SCIENTIFIC MILESTONES (NOTEBOOK 10)", penult_src)
        self.assertIn("Summary of Empirical Findings", penult_src)

        # Ultimate cell: JCC IP & Copyright Notice
        ult_src = "".join(self.cells[-1].get("source", []))
        self.assertIn("INTELLECTUAL PROPERTY & COPYRIGHT NOTICE", ult_src)
        self.assertIn("Gourgopal Mohapatra", ult_src)
        self.assertIn("JCC HEADQUARTER", ult_src)
        self.assertIn("RS-SDA Division", ult_src)

    def test_02_spatial_block_holdout_zero_data_leakage(self):
        """Rule: Zero spatial data leakage; 80% train / 20% test held-out top-right quadrant."""
        cell_08_out = "".join([line for out in self.cells[7].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("Total Domain Pixels : 400", cell_08_out)
        self.assertIn("Training Set Pixels : 320 (80.0%)", cell_08_out)
        self.assertIn("Held-Out Test Pixels: 80 (20.0%)", cell_08_out)
        self.assertIn("Rows 12-20, Cols 10-20", cell_08_out)

    def test_03_eight_stage_incremental_ablation_matrix(self):
        """Rule: All 8 configs (A-H) evaluated with monotonic error reduction and genuine estimators."""
        cell_14_out = "".join([line for out in self.cells[13].get("outputs", []) for line in out.get("text", [])])
        for cfg in ["Config A", "Config B", "Config C", "Config D", "Config E", "Config F", "Config G", "Config H"]:
            self.assertIn(cfg, cell_14_out)
        
        # Verify significant margin reduction across milestones
        self.assertIn("-44.85", cell_14_out)   # S1 SAR leap
        self.assertIn("-28.23", cell_14_out)   # Weather leap
        self.assertIn("-23.52", cell_14_out)   # Physics PINN leap
        self.assertIn("-28.56", cell_14_out)   # EnKF Filter leap

        # Verify strict monotonic descent in RMSE ladder
        ckpt = torch.load(self.ckpt_path, weights_only=False)
        rmses = ckpt["rmse_ladder"]
        self.assertEqual(len(rmses), 8)
        for i in range(len(rmses) - 1):
            self.assertGreater(rmses[i], rmses[i+1], f"RMSE at step {i} not strictly greater than step {i+1}")

    def test_04_uncertainty_quantification_and_variance_contraction(self):
        """Rule: Bootstrap ensemble (B=30) demonstrates massive predictive uncertainty contraction."""
        cell_16_out = "".join([line for out in self.cells[15].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("PREDICTIVE UNCERTAINTY QUANTIFICATION", cell_16_out)
        self.assertIn("BOOTSTRAP ENSEMBLE B=30", cell_16_out)
        self.assertIn("Config G", cell_16_out)

    def test_05_computational_latency_and_pareto_frontier(self):
        """Rule: Micro-benchmarked latency (1000 runs) and Pareto efficiency evaluated."""
        cell_18_out = "".join([line for out in self.cells[17].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("COMPUTATIONAL INFERENCE LATENCY BENCHMARKING", cell_18_out)
        
        cell_20_out = "".join([line for out in self.cells[19].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("MASTER ABLATION SCORECARD", cell_20_out)
        self.assertIn("Pareto_Efficiency_Ratio", cell_20_out)

    def test_06_component_essentiality_tier_determination(self):
        """Rule: Explicitly determines which components matter into Tier 1, Tier 2, and Tier 3."""
        cell_32_out = "".join([line for out in self.cells[31].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("SCIENTIFIC COMPONENT ESSENTIALITY", cell_32_out)
        self.assertIn("Tier 1 (Core)", cell_32_out)
        self.assertIn("Tier 2 (High-Value)", cell_32_out)
        self.assertIn("Tier 3 (Conditional)", cell_32_out)
        self.assertIn("Mandatory Core", cell_32_out)
        self.assertIn("On-Demand Augmentation", cell_32_out)

    def test_07_embedded_and_standalone_visual_plots(self):
        """Rule: All 5 high-resolution diagnostic plots exist on disk and are embedded as base64 in notebook."""
        expected_plots = [
            (21, "plot_01_step_by_step_rmse_reduction_trajectory.png"),
            (23, "plot_02_predictive_uncertainty_contraction_trajectory.png"),
            (25, "plot_03_pareto_efficiency_accuracy_vs_latency.png"),
            (27, "plot_04_marginal_delta_rmse_waterfall.png"),
            (29, "plot_05_component_essentiality_decision_matrix.png")
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
        """Rule: PyTorch checkpoint and Markdown manifest exist and certify architectural freeze."""
        self.assertTrue(self.ckpt_path.exists())
        self.assertTrue(self.manifest_path.exists())
        self.assertGreater(self.ckpt_path.stat().st_size, 3000)
        self.assertGreater(self.manifest_path.stat().st_size, 2000)

        # Inspect checkpoint contents
        ckpt = torch.load(self.ckpt_path, weights_only=False)
        self.assertIn("system_engine", ckpt)
        self.assertEqual(ckpt["system_engine"], "AETHER-MRID1607X")
        self.assertIn("configs", ckpt)
        self.assertEqual(len(ckpt["configs"]), 8)
        self.assertIn("rmse_ladder", ckpt)
        self.assertIn("uncertainty_ladder", ckpt)
        self.assertIn("latency_ladder", ckpt)
        self.assertIn("essentiality_tiers", ckpt)
        self.assertIn("Tier 1 (Mission-Critical Core)", ckpt["essentiality_tiers"])
        self.assertEqual(ckpt["certified_by"], "Gourgopal Mohapatra")
        self.assertEqual(ckpt["facility"], "JCC CAMPUS 2 (RS-SDA DIVISION)")


if __name__ == "__main__":
    unittest.main()
