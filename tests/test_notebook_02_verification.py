"""
THE MRIDANSH : Notebook 02 Preprocessing Verification Suite
============================================================
Strict verification of Notebook 02 structural compliance, cell execution,
scientific honesty, zero-leakage invariant, and storage persistence.
"""

import os
import json
import unittest
import pandas as pd


class TestNotebook02Verification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.nb_path = os.path.join(cls.repo_root, "1_notebooks_sandbox", "02-preprocessing.ipynb")
        cls.storage_dir = os.path.join(cls.repo_root, "5_storage", "notebook_results", "notebook_02_preprocessing")
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
        self.assertGreater(len(cells), 20)

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
        self.assertEqual(len(code_cells), 12)

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

        # Check summary milestones & handoff to Notebook 03
        self.assertIn("EXECUTIVE SUMMARY", pen_source)
        self.assertIn("Kya Mila", pen_source)
        self.assertIn("Kya Nahi Hua", pen_source)
        self.assertIn("Notebook 03", pen_source)

        # Check copyright notice
        self.assertIn("INTELLECTUAL PROPERTY & COPYRIGHT NOTICE", ult_source)
        self.assertIn("Gourgopal Mohapatra", ult_source)
        self.assertIn("JCC HEADQUARTER", ult_source)
        self.assertIn("RS-SDA Division", ult_source)

    def test_05_storage_artifacts_and_plots_persisted(self):
        """Rule: All 4 aerospace plots and data lake exports must exist in 5_storage/notebook_results/notebook_02_preprocessing/."""
        expected_plots = [
            "plot_01_cloud_qc_masking.png",
            "plot_02_sar_speckle_lee_filter.png",
            "plot_03_feature_scaling_distributions.png",
            "plot_04_preprocessed_telemetry_series.png",
        ]
        for plot_file in expected_plots:
            plot_path = os.path.join(self.storage_dir, plot_file)
            self.assertTrue(os.path.exists(plot_path), f"Missing plot artifact: {plot_path}")
            self.assertGreater(os.path.getsize(plot_path), 50000, f"Plot artifact too small: {plot_path}")

        # Check exported CSV and Scaler Manifest in 5_storage
        csv_storage = os.path.join(self.storage_dir, "preprocessed_telemetry.csv")
        json_storage = os.path.join(self.storage_dir, "scaler_manifest.json")
        self.assertTrue(os.path.exists(csv_storage))
        self.assertTrue(os.path.exists(json_storage))

        # Check exported CSV and Scaler Manifest in data/processed
        csv_proc = os.path.join(self.data_proc_dir, "preprocessed_telemetry.csv")
        json_proc = os.path.join(self.data_proc_dir, "scaler_manifest.json")
        self.assertTrue(os.path.exists(csv_proc))
        self.assertTrue(os.path.exists(json_proc))

    def test_06_data_cleaning_masks_and_zero_leakage_invariants(self):
        """Rule: Masks must be preserved, and zero-leakage normalization verified."""
        csv_path = os.path.join(self.storage_dir, "preprocessed_telemetry.csv")
        df = pd.read_csv(csv_path)

        # 1. Mask verification
        self.assertIn("optical_qc_pass", df.columns)
        self.assertIn("ndvi_masked", df.columns)
        self.assertIn("s1_vv_lee", df.columns)
        self.assertIn("s1_vv_lee_zscore", df.columns)
        self.assertIn("ndvi_minmax", df.columns)

        # Cloudy timestamps must have NaN in ndvi_masked and ndvi_minmax
        cloudy_indices = df[~df["optical_qc_pass"]].index
        self.assertTrue(df.loc[cloudy_indices, "ndvi_masked"].isnull().all())
        self.assertTrue(df.loc[cloudy_indices, "ndvi_minmax"].isnull().all())

        # 2. Zero-leakage training slice invariants (split index 28)
        split_idx = int(len(df) * 0.8)
        train_z_vv = df.iloc[:split_idx]["s1_vv_lee_zscore"]
        self.assertAlmostEqual(train_z_vv.mean(), 0.0, places=4)
        self.assertAlmostEqual(train_z_vv.std(), 1.0, places=3)

        # 3. Scaler manifest schema
        json_path = os.path.join(self.storage_dir, "scaler_manifest.json")
        with open(json_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest["project"], "THE MRIDANSH")
        self.assertEqual(manifest["temporal_split_index"], split_idx)
        self.assertEqual(manifest["train_sample_count"], split_idx)
        self.assertIn("scaler_bounds", manifest)
        self.assertIn("s1_vv_lee", manifest["scaler_bounds"])
        self.assertEqual(manifest["scaler_bounds"]["s1_vv_lee"]["scaling_method"], "z_score")


if __name__ == "__main__":
    unittest.main()
