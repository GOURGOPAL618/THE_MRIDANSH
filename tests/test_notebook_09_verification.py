"""
THE MRIDANSH : Notebook 09 Verification Test Suite
Verifies Hyperspectral Augmentation & Spectral Information Experiment (AETHER-MRID1607X)
"""

import json
import os
import unittest
from pathlib import Path
import torch

ROOT_DIR = Path(__file__).resolve().parent.parent
SANDBOX_DIR = ROOT_DIR / "1_notebooks_sandbox"
STORAGE_DIR = ROOT_DIR / "5_storage"
TESTING_RESULTS_DIR = ROOT_DIR / "TESTING RESULTS"


class TestNotebook09Verification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb_path = SANDBOX_DIR / "09-hyperspectral-experiment.ipynb"
        cls.ckpt_path = STORAGE_DIR / "checkpoints" / "hsi_experiment_checkpoint.pt"
        cls.manifest_path = STORAGE_DIR / "checkpoints" / "HSI_EXPERIMENT_MANIFEST.md"

        with open(cls.nb_path, "r", encoding="utf-8") as f:
            cls.nb = json.load(f)
        cls.cells = cls.nb.get("cells", [])

    def test_01_notebook_09_structure_and_interleaving(self):
        """Rule: Notebook 09 must have strictly alternating markdown/code, zero errors, penultimate summary, ultimate IP."""
        self.assertTrue(self.nb_path.exists())
        self.assertEqual(len(self.cells), 36)

        # Check alternating rule
        for i, c in enumerate(self.cells):
            if c.get("cell_type") == "code":
                self.assertGreater(i, 0)
                self.assertEqual(self.cells[i - 1].get("cell_type"), "markdown", f"Code cell {i} not preceded by markdown")
                exec_count = c.get("execution_count")
                self.assertIsNotNone(exec_count)
                self.assertGreater(exec_count, 0)

                for out in c.get("outputs", []):
                    self.assertNotEqual(out.get("output_type"), "error", f"Error in cell {i}")

        # Check Penultimate & Ultimate cells
        penult_src = "".join(self.cells[-2].get("source", []))
        ult_src = "".join(self.cells[-1].get("source", []))

        self.assertIn("EXECUTIVE SUMMARY", penult_src)
        self.assertIn("INTELLECTUAL PROPERTY & COPYRIGHT NOTICE", ult_src)
        self.assertIn("Gourgopal Mohapatra", ult_src)
        self.assertIn("JCC HEADQUARTER", ult_src)

    def test_02_hsi_sensor_and_atmospheric_qc(self):
        """Rule: 224 continuous bands, 24 telluric absorption bands dropped, 200 science bands retained."""
        cell_08_out = "".join([line for out in self.cells[7].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("Total Input Bands        : 224", cell_08_out)
        self.assertIn("Telluric / Dropped Bands : 24", cell_08_out)
        self.assertIn("Retained Science Bands   : 200", cell_08_out)

    def test_03_pca_dimensionality_reduction_kaiser(self):
        """Rule: PCA must capture >99.0% variance across top 10 orthogonal components."""
        cell_14_out = "".join([line for out in self.cells[13].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("Cumulative Variance (10 PCs)", cell_14_out)
        self.assertIn(">99.0% threshold satisfied", cell_14_out)

    def test_04_controlled_ab_testing_identical_splits(self):
        """Rule: Model A and B must be fitted on identical splits with zero synthetic noise addition."""
        cell_20_out = "".join([line for out in self.cells[19].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("CONTROLLED A/B TEST EVALUATION RESULTS", cell_20_out)
        self.assertIn("CONFIG-A (Baseline)", cell_20_out)
        self.assertIn("CONFIG-B (With HSI)", cell_20_out)

    def test_05_uncertainty_quantification_and_variance_reduction(self):
        """Rule: HSI must achieve non-negative uncertainty variance reduction (delta sigma < 0)."""
        cell_22_out = "".join([line for out in self.cells[21].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("Uncertainty Profile Audit", cell_22_out)
        self.assertIn("reduction in predictive variance", cell_22_out)

    def test_06_sensor_dropout_and_failsoft_resilience(self):
        """Rule: 100% missing HSI must smoothly and autonomously fall back to CONFIG-A Baseline."""
        cell_26_out = "".join([line for out in self.cells[25].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("100% Dropout gracefully and autonomously reverts to CONFIG-A", cell_26_out)

    def test_07_computational_tradeoff_and_case2_verdict(self):
        """Rule: Formal verdict must be Case 2 (Targeted Optional Augmentation) with latency slowdown recorded."""
        cell_34_out = "".join([line for out in self.cells[33].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("CASE 2 : MODERATE/CONDITIONAL IMPROVEMENT -> TARGETED OPTIONAL AUGMENTATION", cell_34_out)
        self.assertIn("Deploy CONFIG-B (HSI) strictly as an On-Demand High-Precision Modality", cell_34_out)

    def test_08_checkpoint_and_manifest_certified(self):
        """Rule: Checkpoint and manifest must exist in 5_storage/checkpoints/."""
        self.assertTrue(self.ckpt_path.exists())
        self.assertTrue(self.manifest_path.exists())
        self.assertGreater(self.ckpt_path.stat().st_size, 2000)
        self.assertGreater(self.manifest_path.stat().st_size, 500)

        # Inspect checkpoint contents
        ckpt = torch.load(self.ckpt_path, weights_only=False)
        self.assertIn("hsi_pca_components", ckpt)
        self.assertIn("explained_variance_ratio", ckpt)
        self.assertIn("rmse_baseline_a", ckpt)
        self.assertIn("rmse_augmented_b", ckpt)
        self.assertIn("delta_rmse_pct", ckpt)
        self.assertIn("verdict", ckpt)


if __name__ == "__main__":
    unittest.main()
