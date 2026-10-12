"""
THE MRIDANSH : Notebook 03 Spatial Modeling Verification Suite
=============================================================
Strict verification of Notebook 03 structural compliance, cell execution,
scientific honesty, graph topology, GCN spatial representation,
spatial ablation, and unseen-area inductive generalization.
"""

import os
import json
import unittest
import numpy as np
import torch


class TestNotebook03Verification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.nb_path = os.path.join(cls.repo_root, "1_notebooks_sandbox", "03-spatial-modeling.ipynb")
        cls.storage_dir = os.path.join(cls.repo_root, "5_storage", "notebook_results", "notebook_03_spatial_modeling")
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

        # Check summary milestones & handoff to Notebook 04
        self.assertIn("EXECUTIVE SUMMARY", pen_source)
        self.assertIn("Kya Mila", pen_source)
        self.assertIn("Kya Nahi Hua", pen_source)
        self.assertIn("Notebook 04", pen_source)

        # Check copyright notice
        self.assertIn("INTELLECTUAL PROPERTY & COPYRIGHT NOTICE", ult_source)
        self.assertIn("Gourgopal Mohapatra", ult_source)
        self.assertIn("JCC HEADQUARTER", ult_source)
        self.assertIn("RS-SDA Division", ult_source)

    def test_05_storage_artifacts_and_plots_persisted(self):
        """Rule: All aerospace plots and data lake exports must exist in 5_storage/notebook_results/notebook_03_spatial_modeling/."""
        expected_plots = [
            "plot_01_topographic_slope_elevation.png",
            "plot_02_knn_spatial_graph_adjacency.png",
            "plot_03_gcn_latent_feature_embeddings.png",
            "plot_04_spatial_ablation_analysis.png",
            "plot_05_unseen_area_generalization.png",
        ]
        for plot_file in expected_plots:
            plot_path = os.path.join(self.storage_dir, plot_file)
            self.assertTrue(os.path.exists(plot_path), f"Missing plot artifact: {plot_path}")
            self.assertGreater(os.path.getsize(plot_path), 50000, f"Plot artifact too small: {plot_path}")

        # Check graph mesh and tensor embeddings in 5_storage
        mesh_storage = os.path.join(self.storage_dir, "spatial_graph_mesh.npz")
        pt_storage = os.path.join(self.storage_dir, "spatial_gcn_embeddings.pt")
        self.assertTrue(os.path.exists(mesh_storage))
        self.assertTrue(os.path.exists(pt_storage))

        # Check dual persistence in data/processed
        mesh_proc = os.path.join(self.data_proc_dir, "spatial_graph_mesh.npz")
        pt_proc = os.path.join(self.data_proc_dir, "spatial_gcn_embeddings.pt")
        self.assertTrue(os.path.exists(mesh_proc))
        self.assertTrue(os.path.exists(pt_proc))

    def test_06_graph_and_embedding_tensor_contracts(self):
        """Rule: Adjacency, Laplacian, and 3D spatial tensor embeddings must satisfy physical shape contracts."""
        mesh_path = os.path.join(self.storage_dir, "spatial_graph_mesh.npz")
        mesh_data = np.load(mesh_path)

        for key in ["adj_matrix", "node_coords", "dem_grid", "slope_deg", "aspect_deg"]:
            self.assertIn(key, mesh_data)

        adj = mesh_data["adj_matrix"]
        self.assertEqual(adj.shape, (400, 400))

        # Check spatial embeddings dictionary
        pt_path = os.path.join(self.storage_dir, "spatial_gcn_embeddings.pt")
        emb_bundle = torch.load(pt_path, weights_only=False)
        self.assertIn("spatial_embeddings_tensor_2d", emb_bundle)
        self.assertIn("spatial_embeddings_nodes", emb_bundle)
        self.assertIn("A_hat", emb_bundle)

        emb_2d = emb_bundle["spatial_embeddings_tensor_2d"]
        self.assertEqual(emb_2d.shape, (20, 20, 8))
        self.assertFalse(torch.isnan(emb_2d).any())
        self.assertFalse(torch.isinf(emb_2d).any())

        # Check Kipf-Welling normalized Laplacian
        A_hat = emb_bundle["A_hat"]
        self.assertEqual(A_hat.shape, (400, 400))
        self.assertTrue(torch.all(torch.diag(A_hat) > 0))

    def test_07_spatial_ablation_and_unseen_generalization_validations(self):
        """Rule: Spatial ablation and unseen-area generalization outputs must be documented and mathematically valid."""
        ablation_json = os.path.join(self.storage_dir, "spatial_ablation_results.json")
        self.assertTrue(os.path.exists(ablation_json))

        with open(ablation_json, "r", encoding="utf-8") as f:
            res = json.load(f)

        self.assertIn("full_model", res)
        self.assertIn("no_graph_ablation", res)
        self.assertIn("no_terrain_ablation", res)

        # Confirm non-trivial divergence between full graph message passing and ablations
        self.assertGreater(res["no_graph_ablation"]["frobenius_divergence"], 0.5)
        self.assertGreater(res["no_terrain_ablation"]["frobenius_divergence"], 0.5)

        # Check unseen-area generalization embeddings
        unseen_pt = os.path.join(self.storage_dir, "unseen_area_embeddings.pt")
        self.assertTrue(os.path.exists(unseen_pt))
        unseen_bundle = torch.load(unseen_pt, weights_only=False)
        self.assertIn("unseen_latent_2d", unseen_bundle)
        unseen_emb = unseen_bundle["unseen_latent_2d"]
        self.assertEqual(unseen_emb.shape, (20, 20, 8))
        self.assertFalse(torch.isnan(unseen_emb).any())
        self.assertFalse(torch.isinf(unseen_emb).any())


if __name__ == "__main__":
    unittest.main()
