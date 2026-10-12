"""
THE MRIDANSH : Notebook 07 Uncertainty Analysis Verification Suite
==================================================================
Strict verification of Notebook 07 structural compliance, cell execution,
scientific honesty, orthogonal 4-component variance decomposition,
epistemic vs aleatoric uncertainty partitioning, empirical reliability calibration,
registry checkpointing in 5_storage/registry/, manifest generation,
and statistical certification answering: 'How do we quantify and validate composite uncertainty?'
"""

import os
import json
import unittest
import numpy as np
import torch


class TestNotebook07Verification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.nb_path = os.path.join(cls.repo_root, "1_notebooks_sandbox", "07-uncertainty-analysis.ipynb")
        cls.storage_dir = os.path.join(cls.repo_root, "5_storage", "notebook_results", "notebook_07_uncertainty_analysis")
        cls.registry_dir = os.path.join(cls.repo_root, "5_storage", "registry")
        cls.data_proc_dir = os.path.join(cls.repo_root, "data", "processed")

        with open(cls.nb_path, "r", encoding="utf-8") as f:
            cls.nb = json.load(f)

    def test_01_no_python_scripts_in_notebook_dir(self):
        """Rule: 1_notebooks_sandbox must strictly contain only .ipynb files."""
        nb_dir = os.path.join(self.repo_root, "1_notebooks_sandbox")
        py_files = [f for f in os.listdir(nb_dir) if f.endswith(".py")]
        self.assertEqual(py_files, [], f"Found forbidden .py files in sandbox: {py_files}")

    def test_02_notebook_cell_structure_and_markdown_rules(self):
        """Rule: Every code cell must be immediately preceded by a markdown cell."""
        cells = self.nb.get("cells", [])
        self.assertGreaterEqual(len(cells), 25)

        for i, cell in enumerate(cells):
            if cell.get("cell_type") == "code":
                self.assertGreater(i, 0, "First cell cannot be code without preceding markdown")
                prev_cell = cells[i - 1]
                self.assertEqual(
                    prev_cell.get("cell_type"),
                    "markdown",
                    f"Code cell at index {i} is not preceded by a markdown cell (found {prev_cell.get('cell_type')})"
                )

    def test_03_all_code_cells_executed_with_zero_errors(self):
        """Rule: All code cells must be executed and contain zero errors/exceptions."""
        cells = self.nb.get("cells", [])
        code_cells = [c for c in cells if c.get("cell_type") == "code"]
        self.assertEqual(len(code_cells), 13)

        for idx, cell in enumerate(code_cells):
            exec_count = cell.get("execution_count")
            self.assertIsNotNone(exec_count, f"Code cell {idx} has not been executed (execution_count is None)")
            self.assertGreater(exec_count, 0)

            outputs = cell.get("outputs", [])
            for out in outputs:
                out_type = out.get("output_type")
                self.assertNotEqual(
                    out_type,
                    "error",
                    f"Code cell {idx} failed with error: {out.get('ename')}: {out.get('evalue')}"
                )

    def test_04_penultimate_and_ultimate_markdown_cells(self):
        """Rule: Last two cells must be Executive Summary and Intellectual Property notice."""
        cells = self.nb.get("cells", [])
        penultimate = cells[-2]
        ultimate = cells[-1]

        self.assertEqual(penultimate.get("cell_type"), "markdown")
        self.assertEqual(ultimate.get("cell_type"), "markdown")

        pen_source = "".join(penultimate.get("source", []))
        ult_source = "".join(ultimate.get("source", []))

        # Check summary milestones & handoff to Notebook 08
        self.assertIn("EXECUTIVE SUMMARY", pen_source)
        self.assertIn("Kya Mila", pen_source)
        self.assertIn("Kya Nahi Hua", pen_source)
        self.assertIn("Notebook 08", pen_source)

        # Check copyright notice
        self.assertIn("INTELLECTUAL PROPERTY & COPYRIGHT NOTICE", ult_source)
        self.assertIn("Gourgopal Mohapatra", ult_source)
        self.assertIn("JCC HEADQUARTER", ult_source)
        self.assertIn("RS-SDA Division", ult_source)

    def test_05_storage_artifacts_and_plots_persisted(self):
        """Rule: All 5 aerospace plots must exist in 5_storage/notebook_results/notebook_07_uncertainty_analysis/."""
        expected_plots = [
            "plot_01_component_uncertainty_decomposition.png",
            "plot_02_epistemic_aleatoric_partitioning.png",
            "plot_03_reliability_calibration_diagrams.png",
            "plot_04_temporal_gap_latency_penalty.png",
            "plot_05_stress_scenario_risk_mapping.png",
        ]
        for plot_file in expected_plots:
            plot_path = os.path.join(self.storage_dir, plot_file)
            self.assertTrue(os.path.exists(plot_path), f"Missing plot artifact: {plot_path}")
            self.assertGreater(os.path.getsize(plot_path), 50000, f"Plot artifact too small: {plot_path}")

        # Metrics JSON
        metrics_path = os.path.join(self.storage_dir, "uncertainty_analysis_metrics.json")
        self.assertTrue(os.path.exists(metrics_path))

    def test_06_checkpoint_and_manifest_compliance(self):
        """Rule: Uncertainty registry and manifest must exist in 5_storage/registry/ with dual persistence."""
        reg_path = os.path.join(self.registry_dir, "uncertainty_registry.pt")
        manifest_path = os.path.join(self.registry_dir, "UNCERTAINTY_REGISTRY_MANIFEST.md")
        storage_reg = os.path.join(self.storage_dir, "uncertainty_registry.pt")
        proc_bundle = os.path.join(self.data_proc_dir, "uncertainty_analysis_bundle.pt")

        self.assertTrue(os.path.exists(reg_path), f"Missing registry file: {reg_path}")
        self.assertTrue(os.path.exists(manifest_path), f"Missing manifest: {manifest_path}")
        self.assertTrue(os.path.exists(storage_reg), f"Missing storage registry: {storage_reg}")
        self.assertTrue(os.path.exists(proc_bundle), f"Missing data/processed bundle: {proc_bundle}")

        # Validate Manifest text content
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_content = f.read()

        self.assertIn("UNCERTAINTY QUANTIFICATION REGISTRY MANIFEST", manifest_content)
        self.assertIn("AETHER-MRID1607X", manifest_content)
        self.assertIn("uncertainty_registry.pt", manifest_content)
        self.assertIn("Notebook 08", manifest_content)

        # Validate Registry Bundle
        bundle = torch.load(reg_path, weights_only=False)
        self.assertIn("grid_dimensions", bundle)
        self.assertIn("sigma_ens", bundle)
        self.assertIn("sigma_sensor", bundle)
        self.assertIn("sigma_gap", bundle)
        self.assertIn("sigma_model", bundle)
        self.assertIn("sigma_total", bundle)
        self.assertIn("confidence_score", bundle)
        self.assertIn("calibration", bundle)
        self.assertIn("stress_scenarios", bundle)

        self.assertEqual(bundle["grid_dimensions"], (20, 20))
        self.assertTrue(np.all(np.isfinite(bundle["sigma_total"])))
        self.assertTrue(np.all(np.isfinite(bundle["confidence_score"])))

    def test_07_uncertainty_calibration_and_reliability(self):
        """Rule: Calibration errors must be < 2.0% of theoretical Gaussian quantiles."""
        metrics_path = os.path.join(self.storage_dir, "uncertainty_analysis_metrics.json")
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics = json.load(f)

        self.assertLess(metrics["coverage_1sigma_error_pct"], 2.0)
        self.assertLess(metrics["coverage_2sigma_error_pct"], 2.0)
        self.assertGreater(metrics["mean_confidence_score_pct"], 40.0)
        self.assertLess(metrics["mean_confidence_score_pct"], 90.0)
        self.assertGreater(metrics["cloud_outage_confidence_pct"], 30.0)
        self.assertEqual(metrics["calibration_status"], "CALIBRATED_ZERO_DEFECT")

    def test_08_high_confidence_low_error_monotonicity(self):
        """Rule: High Confidence MUST strictly correspond to lower actual error (monotonicity)."""
        metrics_path = os.path.join(self.storage_dir, "uncertainty_analysis_metrics.json")
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics = json.load(f)

        self.assertIn("decile_rank_correlation", metrics)
        self.assertLess(metrics["decile_rank_correlation"], -0.85, "Decile correlation must be strongly negative (< -0.85)")
        self.assertLess(metrics["mae_high_confidence"], metrics["mae_med_confidence"], "High Conf MAE must be less than Med Conf MAE")
        self.assertLess(metrics["mae_med_confidence"], metrics["mae_low_confidence"], "Med Conf MAE must be less than Low Conf MAE")
        self.assertEqual(metrics["confidence_error_monotonicity"], "PROVEN_CERTIFIED")


if __name__ == "__main__":
    unittest.main()

