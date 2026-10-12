"""
THE MRIDANSH : Notebook 04 Temporal Modeling Verification Suite
==============================================================
Strict verification of Notebook 04 structural compliance, cell execution,
scientific honesty, 5D tensor contracts, ConvLSTM recurrent optimization,
temporal lookback ablation, and autoregressive rollout stability.
"""

import os
import json
import unittest
import numpy as np
import torch


class TestNotebook04Verification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.nb_path = os.path.join(cls.repo_root, "1_notebooks_sandbox", "04-temporal-modeling.ipynb")
        cls.storage_dir = os.path.join(cls.repo_root, "5_storage", "notebook_results", "notebook_04_temporal_modeling")
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
        self.assertEqual(len(code_cells), 14)

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

        # Check summary milestones & handoff to Notebook 05
        self.assertIn("EXECUTIVE SUMMARY", pen_source)
        self.assertIn("Kya Mila", pen_source)
        self.assertIn("Kya Nahi Hua", pen_source)
        self.assertIn("Notebook 05", pen_source)

        # Check copyright notice
        self.assertIn("INTELLECTUAL PROPERTY & COPYRIGHT NOTICE", ult_source)
        self.assertIn("Gourgopal Mohapatra", ult_source)
        self.assertIn("JCC HEADQUARTER", ult_source)
        self.assertIn("RS-SDA Division", ult_source)

    def test_05_storage_artifacts_and_plots_persisted(self):
        """Rule: All aerospace plots and data lake exports must exist in 5_storage/notebook_results/notebook_04_temporal_modeling/."""
        expected_plots = [
            "plot_01_spatiotemporal_tensor_slices.png",
            "plot_02_loss_convergence_and_spatial_prediction.png",
            "plot_03_temporal_lookback_ablation.png",
            "plot_04_autoregressive_rollout_recession.png",
            "plot_05_recurrent_hidden_state_activations.png",
        ]
        for plot_file in expected_plots:
            plot_path = os.path.join(self.storage_dir, plot_file)
            self.assertTrue(os.path.exists(plot_path), f"Missing plot artifact: {plot_path}")
            self.assertGreater(os.path.getsize(plot_path), 50000, f"Plot artifact too small: {plot_path}")

        # Check model weights and latent states in storage
        model_storage = os.path.join(self.storage_dir, "convlstm_model_init.pt")
        latent_storage = os.path.join(self.storage_dir, "temporal_latent_states.pt")
        self.assertTrue(os.path.exists(model_storage))
        self.assertTrue(os.path.exists(latent_storage))

        # Check dual persistence in data/processed
        model_proc = os.path.join(self.data_proc_dir, "convlstm_model_init.pt")
        latent_proc = os.path.join(self.data_proc_dir, "temporal_latent_states.pt")
        self.assertTrue(os.path.exists(model_proc))
        self.assertTrue(os.path.exists(latent_proc))

    def test_06_model_checkpoint_and_latent_contracts(self):
        """Rule: Model checkpoint and recurrent latent states must conform to architectural contracts."""
        model_path = os.path.join(self.storage_dir, "convlstm_model_init.pt")
        bundle = torch.load(model_path, weights_only=False)

        required_keys = [
            'model_state_dict', 'in_channels', 'hidden_channels', 'out_channels',
            'sequence_length', 'grid_dim', 'train_losses', 'test_losses', 'loss_reduction_pct'
        ]
        for k in required_keys:
            self.assertIn(k, bundle)

        self.assertEqual(bundle['in_channels'], 2)
        self.assertEqual(bundle['hidden_channels'], 16)
        self.assertEqual(bundle['out_channels'], 2)
        self.assertEqual(bundle['sequence_length'], 5)
        self.assertEqual(bundle['grid_dim'], (20, 20))
        self.assertGreater(bundle['loss_reduction_pct'], 10.0)

        # Inspect recurrent latent states
        latent_path = os.path.join(self.storage_dir, "temporal_latent_states.pt")
        latent_bundle = torch.load(latent_path, weights_only=False)

        self.assertIn('h_final_test', latent_bundle)
        self.assertIn('rollout_predictions', latent_bundle)

        h_final = latent_bundle['h_final_test']
        self.assertEqual(len(h_final.shape), 4)  # (B_test, 16, 20, 20)
        self.assertEqual(h_final.shape[1:], (16, 20, 20))
        self.assertFalse(torch.isnan(h_final).any())
        self.assertFalse(torch.isinf(h_final).any())

        rollout = latent_bundle['rollout_predictions']
        self.assertEqual(rollout.shape, (1, 5, 2, 20, 20))
        self.assertFalse(torch.isnan(rollout).any())
        self.assertFalse(torch.isinf(rollout).any())

    def test_07_temporal_ablation_and_loss_convergence(self):
        """Rule: Sequence ablation must quantify lookback horizons and prove finite error reduction."""
        ablation_path = os.path.join(self.storage_dir, "temporal_sequence_ablation.json")
        self.assertTrue(os.path.exists(ablation_path))

        with open(ablation_path, 'r', encoding='utf-8') as f:
            ablation_data = json.load(f)

        for h in [3, 5, 7, 10]:
            key = f"horizon_{h}"
            self.assertIn(key, ablation_data)
            self.assertIn("val_mse", ablation_data[key])
            self.assertIn("sar_mae", ablation_data[key])
            self.assertIn("ndvi_mae", ablation_data[key])
            self.assertGreater(ablation_data[key]["val_mse"], 0.0)

        # Compare short horizon (T=3) vs long horizon (T=10)
        mse_h3 = ablation_data["horizon_3"]["val_mse"]
        mse_h10 = ablation_data["horizon_10"]["val_mse"]
        self.assertLess(mse_h10, mse_h3, "Extended lookback horizon must improve long-term temporal fitting")


if __name__ == "__main__":
    unittest.main()
