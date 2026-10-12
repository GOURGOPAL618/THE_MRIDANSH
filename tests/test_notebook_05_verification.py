"""
THE MRIDANSH : Notebook 05 Physics Validation & PINN Verification Suite
======================================================================
Strict verification of Notebook 05 structural compliance, cell execution,
scientific honesty, Richards PDE differential formulation, van Genuchten SWRC,
PINN continuous space-time solver, checkpointing in 5_storage/checkpoints/,
manifest generation, and physical mass conservation benchmark superiority.
"""

import os
import json
import unittest
import numpy as np
import torch


class TestNotebook05Verification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.nb_path = os.path.join(cls.repo_root, "1_notebooks_sandbox", "05-physics-validation.ipynb")
        cls.storage_dir = os.path.join(cls.repo_root, "5_storage", "notebook_results", "notebook_05_physics_validation")
        cls.checkpoint_dir = os.path.join(cls.repo_root, "5_storage", "checkpoints")
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
        self.assertEqual(len(code_cells), 16)

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

        # Check summary milestones & handoff to Notebook 06
        self.assertIn("EXECUTIVE SUMMARY", pen_source)
        self.assertIn("Kya Mila", pen_source)
        self.assertIn("Kya Nahi Hua", pen_source)
        self.assertIn("Notebook 06", pen_source)

        # Check copyright notice
        self.assertIn("INTELLECTUAL PROPERTY & COPYRIGHT NOTICE", ult_source)
        self.assertIn("Gourgopal Mohapatra", ult_source)
        self.assertIn("JCC HEADQUARTER", ult_source)
        self.assertIn("RS-SDA Division", ult_source)

    def test_05_storage_artifacts_and_plots_persisted(self):
        """Rule: All 5 aerospace plots must exist in 5_storage/notebook_results/notebook_05_physics_validation/."""
        expected_plots = [
            "plot_01_van_genuchten_swrc_conductivity.png",
            "plot_02_pinn_space_time_collocation_mesh.png",
            "plot_03_pinn_loss_convergence_trajectory.png",
            "plot_04_pinn_vs_unconstrained_pde_residuals.png",
            "plot_05_continuous_soil_diffusion_profile.png",
        ]
        for plot_file in expected_plots:
            plot_path = os.path.join(self.storage_dir, plot_file)
            self.assertTrue(os.path.exists(plot_path), f"Missing plot artifact: {plot_path}")
            self.assertGreater(os.path.getsize(plot_path), 50000, f"Plot artifact too small: {plot_path}")

        # Metrics JSON
        metrics_path = os.path.join(self.storage_dir, "pinn_physics_metrics.json")
        self.assertTrue(os.path.exists(metrics_path))

    def test_06_checkpoint_and_manifest_compliance(self):
        """Rule: Model checkpoint and manifest must exist in 5_storage/checkpoints/ with dual persistence."""
        ckpt_path = os.path.join(self.checkpoint_dir, "pinn_richards_model.pt")
        manifest_path = os.path.join(self.checkpoint_dir, "PINN_RICHARDS_MODEL_MANIFEST.md")
        storage_ckpt = os.path.join(self.storage_dir, "pinn_richards_model.pt")
        proc_ckpt = os.path.join(self.data_proc_dir, "pinn_richards_model.pt")

        self.assertTrue(os.path.exists(ckpt_path), f"Missing checkpoint: {ckpt_path}")
        self.assertTrue(os.path.exists(manifest_path), f"Missing manifest: {manifest_path}")
        self.assertTrue(os.path.exists(storage_ckpt), f"Missing storage checkpoint: {storage_ckpt}")
        self.assertTrue(os.path.exists(proc_ckpt), f"Missing data/processed checkpoint: {proc_ckpt}")

        # Validate Manifest text content
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_content = f.read()

        self.assertIn("PINN RICHARDS PDE MODEL CHECKPOINT MANIFEST", manifest_content)
        self.assertIn("AETHER-MRID1607X", manifest_content)
        self.assertIn("pinn_richards_model.pt", manifest_content)
        self.assertIn("LOAM", manifest_content)
        self.assertIn("Richards Equation", manifest_content)
        self.assertIn("Notebook 06", manifest_content)

        # Validate Checkpoint dictionary
        bundle = torch.load(ckpt_path, weights_only=False)
        self.assertIn("model_state_dict", bundle)
        self.assertIn("soil_class", bundle)
        self.assertIn("soil_params", bundle)
        self.assertIn("pde_reduction_pct", bundle)
        self.assertEqual(bundle["soil_class"], "loam")
        self.assertGreaterEqual(bundle["pde_reduction_pct"], 70.0)

        for param_tensor in bundle["model_state_dict"].values():
            self.assertTrue(torch.isfinite(param_tensor).all(), "Non-finite weights found in PINN model!")

    def test_07_richards_physics_consistency_and_mass_conservation(self):
        """Rule: PINN must reduce physical PDE residual by >70% and satisfy moisture bounds."""
        metrics_path = os.path.join(self.storage_dir, "pinn_physics_metrics.json")
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics = json.load(f)

        self.assertEqual(metrics["soil_type"], "loam")
        self.assertGreater(metrics["unconstrained_baseline_error"], metrics["pinn_physics_error"])
        self.assertGreaterEqual(metrics["mass_conservation_improvement_pct"], 70.0)
        self.assertLess(metrics["pinn_physics_error"], 0.001)

        # Volumetric Moisture bounded between residual and saturation limits
        theta_r = metrics["soil_parameters"]["theta_r"]
        theta_s = metrics["soil_parameters"]["theta_s"]
        self.assertGreaterEqual(metrics["min_moisture_bounded"], theta_r - 0.05)
        self.assertLessEqual(metrics["max_moisture_bounded"], theta_s + 0.05)


if __name__ == "__main__":
    unittest.main()
