"""
THE MRIDANSH : Notebook 01 Data Ingestion Verification Suite
=============================================================
Strict verification of Notebook 01 structural compliance, cell-level execution,
scientific honesty, and storage artifact persistence.
"""

import os
import json
import unittest
import pandas as pd


class TestNotebook01Verification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.nb_path = os.path.join(cls.repo_root, "1_notebooks_sandbox", "01-data-ingestion.ipynb")
        cls.storage_dir = os.path.join(cls.repo_root, "5_storage", "notebook_results", "notebook_01_ingestion")
        cls.data_raw_dir = os.path.join(cls.repo_root, "data", "raw")

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

        # Check summary milestones & handoff
        self.assertIn("EXECUTIVE SUMMARY", pen_source)
        self.assertIn("Kya Mila", pen_source)
        self.assertIn("Kya Nahi Hua", pen_source)
        self.assertIn("Notebook 02", pen_source)

        # Check copyright notice
        self.assertIn("INTELLECTUAL PROPERTY & COPYRIGHT NOTICE", ult_source)
        self.assertIn("Gourgopal Mohapatra", ult_source)
        self.assertIn("JCC HEADQUARTER", ult_source)
        self.assertIn("RS-SDA Division", ult_source)

    def test_05_storage_artifacts_and_plots_persisted(self):
        """Rule: All 6 aerospace plots and data lake exports must exist in 5_storage/notebook_01_ingestion/."""
        expected_plots = [
            "plot_01_s1_sar_dynamics.png",
            "plot_02_s2_spectral_indices.png",
            "plot_03_cloud_masking_sar_fallback.png",
            "plot_04_atmospheric_forcing_precip_temp.png",
            "plot_05_spatial_rasters_ndvi_sar.png",
            "plot_06_resampled_dem_profile.png",
        ]
        for plot_file in expected_plots:
            plot_path = os.path.join(self.storage_dir, plot_file)
            self.assertTrue(os.path.exists(plot_path), f"Missing plot artifact: {plot_path}")
            self.assertGreater(os.path.getsize(plot_path), 50000, f"Plot artifact too small: {plot_path}")

        # Check exported CSV and STAC JSON in 5_storage
        csv_storage = os.path.join(self.storage_dir, "stac_telemetry_raw.csv")
        json_storage = os.path.join(self.storage_dir, "stac_catalog_item.json")
        self.assertTrue(os.path.exists(csv_storage))
        self.assertTrue(os.path.exists(json_storage))

        # Check exported CSV and STAC JSON in data/raw
        csv_raw = os.path.join(self.data_raw_dir, "stac_telemetry_raw.csv")
        json_raw = os.path.join(self.data_raw_dir, "stac_catalog_item.json")
        self.assertTrue(os.path.exists(csv_raw))
        self.assertTrue(os.path.exists(json_raw))

    def test_06_data_and_schema_integrity(self):
        """Rule: Typos must be resolved and STAC 1.0.0 assets must strictly validate."""
        csv_path = os.path.join(self.storage_dir, "stac_telemetry_raw.csv")
        df = pd.read_csv(csv_path)

        # 1. Column names must be standard (no weayher typo)
        self.assertIn("weather_temp_c", df.columns)
        self.assertNotIn("weayher_temp_c", df.columns)
        self.assertIn("weather_precip_mm", df.columns)
        self.assertIn("provenance", df.columns)
        self.assertEqual(df["provenance"].iloc[0], "SYNTHETIC_SIMULATION")

        # 2. Spectral indices bounds
        self.assertTrue(df["ndvi"].between(-1.0, 1.0).all())
        self.assertTrue(df["ndwi"].between(-1.0, 1.0).all())

        # 3. STAC item schema
        json_path = os.path.join(self.storage_dir, "stac_catalog_item.json")
        with open(json_path, "r", encoding="utf-8") as f:
            stac_item = json.load(f)

        self.assertEqual(stac_item["stac_version"], "1.0.0")
        self.assertIn("assets", stac_item, "STAC item must use 'assets' key, not 'assert'")
        self.assertNotIn("assert", stac_item)
        self.assertIn("s1_vv", stac_item["assets"])
        self.assertEqual(stac_item["properties"]["aether:processing_level"], "L2A_INFRARED_STAC_V1")


if __name__ == "__main__":
    unittest.main()
