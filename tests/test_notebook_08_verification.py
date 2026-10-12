"""
THE MRIDANSH : Notebook 08 Robustness & Failure Analysis Verification Suite
===========================================================================
Strict verification of Notebook 08 structural compliance, cell execution,
sensor modality failure ablation, controlled data corruption sweeps,
environmental edge cases, 4-tier operational health state classification,
dynamic Bayesian self-healing recovery, 4th blank storage folder compliance,
and mathematical certification answering: 'When MRIDANSH doesn't know, does it know that it doesn't know?'
"""

import os
import json
import unittest
import numpy as np
import torch


class TestNotebook08Verification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.nb_path = os.path.join(cls.repo_root, "1_notebooks_sandbox", "08-robustness-and-failure-analysis.ipynb")
        cls.storage_dir = os.path.join(cls.repo_root, "5_storage", "notebook_results", "notebook_08_robustness_and_failure")
        cls.logs_dir = os.path.join(cls.repo_root, "5_storage", "telemetry_logs")
        cls.data_proc_dir = os.path.join(cls.repo_root, "data", "processed")

        with open(cls.nb_path, "r", encoding="utf-8") as f:
            cls.nb = json.load(f)

    def test_01_no_python_scripts_in_notebook_dir(self):
        """Rule: 1_notebooks_sandbox must strictly contain only .ipynb files."""
        nb_dir = os.path.join(self.repo_root, "1_notebooks_sandbox")
        py_files = [f for f in os.listdir(nb_dir) if f.endswith(".py")]
        self.assertEqual(py_files, [], f"Found forbidden .py files in sandbox: {py_files}")

    def test_02_notebook_cell_structure_and_markdown_rules(self):
        """Rule: Every code cell must be immediately preceded by a dedicated markdown cell."""
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

        # Check summary milestones & handoff
        self.assertIn("EXECUTIVE SUMMARY", pen_source)
        self.assertIn("Kya Mila", pen_source)
        self.assertIn("Kya Nahi Hua", pen_source)
        self.assertIn("Phase 3", pen_source)

        # Check copyright notice
        self.assertIn("INTELLECTUAL PROPERTY & COPYRIGHT NOTICE", ult_source)
        self.assertIn("Gourgopal Mohapatra", ult_source)
        self.assertIn("JCC HEADQUARTER", ult_source)
        self.assertIn("RS-SDA Division", ult_source)

    def test_05_storage_artifacts_and_plots_persisted(self):
        """Rule: All 5 aerospace plots must exist in 5_storage/notebook_results/notebook_08_robustness_and_failure/."""
        expected_plots = [
            "plot_01_sensor_modality_dropout_matrix.png",
            "plot_02_progressive_data_corruption_response.png",
            "plot_03_environmental_edge_cases_evaluation.png",
            "plot_04_spatial_failure_mode_classification_map.png",
            "plot_05_dynamic_self_healing_recovery_trajectory.png",
        ]
        for plot_file in expected_plots:
            plot_path = os.path.join(self.storage_dir, plot_file)
            self.assertTrue(os.path.exists(plot_path), f"Missing plot artifact: {plot_path}")
            self.assertGreater(os.path.getsize(plot_path), 50000, f"Plot artifact too small: {plot_path}")

        # Metrics JSON
        metrics_path = os.path.join(self.storage_dir, "robustness_analysis_metrics.json")
        self.assertTrue(os.path.exists(metrics_path))

    def test_06_checkpoint_and_manifest_in_blank_folder(self):
        """Rule: Robustness stress logs and manifest must exist in 5_storage/telemetry_logs/ (4th blank folder)."""
        log_path = os.path.join(self.logs_dir, "robustness_stress_logs.pt")
        manifest_path = os.path.join(self.logs_dir, "ROBUSTNESS_STRESS_MANIFEST.md")
        storage_log = os.path.join(self.storage_dir, "robustness_stress_logs.pt")
        proc_bundle = os.path.join(self.data_proc_dir, "robustness_stress_bundle.pt")

        self.assertTrue(os.path.exists(log_path), f"Missing log checkpoint in 4th blank folder: {log_path}")
        self.assertTrue(os.path.exists(manifest_path), f"Missing manifest in 4th blank folder: {manifest_path}")
        self.assertTrue(os.path.exists(storage_log), f"Missing storage log: {storage_log}")
        self.assertTrue(os.path.exists(proc_bundle), f"Missing data/processed bundle: {proc_bundle}")

        # Validate Manifest text content
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_content = f.read()

        self.assertIn("ROBUSTNESS EVALUATION & FAILURE TELEMETRY MANIFEST", manifest_content)
        self.assertIn("AETHER-MRID1607X", manifest_content)
        self.assertIn("5_storage/telemetry_logs/", manifest_content)
        self.assertIn("robustness_stress_logs.pt", manifest_content)
        self.assertIn("Phase 3", manifest_content)

        # Validate Stress Bundle
        bundle = torch.load(log_path, weights_only=False)
        self.assertIn("grid_dim", bundle)
        self.assertIn("dropout_scenarios", bundle)
        self.assertIn("corruption_sweeps", bundle)
        self.assertIn("environmental_edges", bundle)
        self.assertIn("health_classification", bundle)
        self.assertIn("self_healing", bundle)
        self.assertIn("failure_catalogue", bundle)

        self.assertEqual(bundle["grid_dim"], (20, 20))

    def test_07_sensor_dropout_monotonic_degradation(self):
        """Rule: System RMSE must expand predictably as sensor modalities are removed."""
        metrics_path = os.path.join(self.storage_dir, "robustness_analysis_metrics.json")
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics = json.load(f)

        nom_rmse = metrics["nominal_rmse"]
        s2_rmse = metrics["s2_missing_rmse"]
        s1_rmse = metrics["s1_missing_rmse"]
        dual_rmse = metrics["dual_missing_rmse"]

        self.assertLess(nom_rmse, s2_rmse, "Optical dropout must increase error above nominal")
        self.assertLess(s2_rmse, s1_rmse, "SAR dropout must produce higher error than optical dropout")
        self.assertLess(s1_rmse, dual_rmse, "Dual satellite blackout must produce highest error")

    def test_08_noise_monotonicity_and_self_healing(self):
        """Rule: Noise vs Uncertainty correlation must be > 0.95, and self-healing must recover nominal bounds."""
        metrics_path = os.path.join(self.storage_dir, "robustness_analysis_metrics.json")
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics = json.load(f)

        self.assertGreater(metrics["noise_monotonicity_correlation"], 0.95)
        self.assertGreater(metrics["self_healing_peak_sigma"], metrics["self_healing_recovered_sigma"])
        self.assertLess(metrics["self_healing_recovered_sigma"], 0.040)
        self.assertEqual(metrics["robustness_status"], "CERTIFIED_FAIL_SOFT_ZERO_DEFECT")


if __name__ == "__main__":
    unittest.main()
