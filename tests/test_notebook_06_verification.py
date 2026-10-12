"""
THE MRIDANSH : Notebook 06 State Estimation & EnKF Verification Suite
=====================================================================
Strict verification of Notebook 06 structural compliance, cell execution,
scientific honesty, EnKF sequential data assimilation, pedological cross-covariances,
filter stability, state database checkpointing, manifest generation,
and statistical proof answering: 'Does assimilation actually improve the estimated soil state?'
"""

import os
import json
import unittest
import numpy as np
import torch


class TestNotebook06Verification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.nb_path = os.path.join(cls.repo_root, "1_notebooks_sandbox", "06-state-estimation.ipynb")
        cls.storage_dir = os.path.join(cls.repo_root, "5_storage", "notebook_results", "notebook_06_state_estimation")
        cls.state_db_dir = os.path.join(cls.repo_root, "5_storage", "state_database")
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
        self.assertGreaterEqual(len(cells), 30)

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
        self.assertEqual(len(code_cells), 15)

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

        # Check summary milestones & handoff to Notebook 07
        self.assertIn("EXECUTIVE SUMMARY", pen_source)
        self.assertIn("Kya Mila", pen_source)
        self.assertIn("Kya Nahi Hua", pen_source)
        self.assertIn("Notebook 07", pen_source)

        # Check copyright notice
        self.assertIn("INTELLECTUAL PROPERTY & COPYRIGHT NOTICE", ult_source)
        self.assertIn("Gourgopal Mohapatra", ult_source)
        self.assertIn("JCC HEADQUARTER", ult_source)
        self.assertIn("RS-SDA Division", ult_source)

    def test_05_storage_artifacts_and_plots_persisted(self):
        """Rule: All 5 aerospace plots must exist in 5_storage/notebook_results/notebook_06_state_estimation/."""
        expected_plots = [
            "plot_01_prior_vs_posterior_distributions.png",
            "plot_02_kalman_gain_cross_covariance.png",
            "plot_03_dynamic_trajectory_convergence.png",
            "plot_04_noise_sensitivity_sweep.png",
            "plot_05_spatial_grid_enkf_assimilation.png",
        ]
        for plot_file in expected_plots:
            plot_path = os.path.join(self.storage_dir, plot_file)
            self.assertTrue(os.path.exists(plot_path), f"Missing plot artifact: {plot_path}")
            self.assertGreater(os.path.getsize(plot_path), 50000, f"Plot artifact too small: {plot_path}")

        # Metrics JSON
        metrics_path = os.path.join(self.storage_dir, "enkf_state_estimation_metrics.json")
        self.assertTrue(os.path.exists(metrics_path))

    def test_06_checkpoint_and_manifest_compliance(self):
        """Rule: State database and manifest must exist in 5_storage/state_database/ with dual persistence."""
        db_path = os.path.join(self.state_db_dir, "enkf_state_database.pt")
        manifest_path = os.path.join(self.state_db_dir, "ENKF_STATE_ESTIMATION_MANIFEST.md")
        storage_db = os.path.join(self.storage_dir, "enkf_state_database.pt")
        proc_bundle = os.path.join(self.data_proc_dir, "enkf_assimilation_bundle.pt")

        self.assertTrue(os.path.exists(db_path), f"Missing state database: {db_path}")
        self.assertTrue(os.path.exists(manifest_path), f"Missing manifest: {manifest_path}")
        self.assertTrue(os.path.exists(storage_db), f"Missing storage database: {storage_db}")
        self.assertTrue(os.path.exists(proc_bundle), f"Missing data/processed bundle: {proc_bundle}")

        # Validate Manifest text content
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_content = f.read()

        self.assertIn("ENKF STATE ESTIMATION DATABASE MANIFEST", manifest_content)
        self.assertIn("AETHER-MRID1607X", manifest_content)
        self.assertIn("enkf_state_database.pt", manifest_content)
        self.assertIn("Notebook 07", manifest_content)

        # Validate State Database Bundle
        bundle = torch.load(db_path, weights_only=False)
        self.assertIn("state_names", bundle)
        self.assertIn("prior_ensemble", bundle)
        self.assertIn("posterior_ensemble", bundle)
        self.assertIn("kalman_gain_matrix", bundle)
        self.assertIn("dynamic_trajectory", bundle)
        self.assertIn("spatial_assimilation", bundle)

        self.assertEqual(len(bundle["state_names"]), 4)
        self.assertEqual(bundle["prior_ensemble"].shape, (4, 50))
        self.assertEqual(bundle["posterior_ensemble"].shape, (4, 50))
        self.assertTrue(np.all(np.isfinite(bundle["posterior_ensemble"])))
        self.assertTrue(np.all(np.isfinite(bundle["kalman_gain_matrix"])))

    def test_07_assimilation_validation_and_error_reduction(self):
        """Rule: EnKF must reduce dynamic prediction drift RMSE by >70% and shrink uncertainty."""
        metrics_path = os.path.join(self.storage_dir, "enkf_state_estimation_metrics.json")
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics = json.load(f)

        self.assertEqual(metrics["num_state_variables"], 4)
        self.assertGreater(metrics["prediction_rmse"], metrics["enkf_posterior_rmse"])
        self.assertGreaterEqual(metrics["error_reduction_pct"], 70.0)
        self.assertLess(metrics["enkf_posterior_rmse"], 0.025)
        self.assertGreaterEqual(metrics["root_moisture_uncertainty_reduction_pct"], 35.0)
        self.assertGreaterEqual(metrics["spatial_mean_variance_reduction_pct"], 50.0)
        self.assertEqual(metrics["filter_stability_status"], "CONVERGED_STABLE")


if __name__ == "__main__":
    unittest.main()
