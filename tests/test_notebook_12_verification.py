"""
THE MRIDANSH : Notebook 12 Verification Test Suite
Verifies Grand Scientific Audit & Multi-Domain System Certification (AETHER-MRID1607X)
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
RESULTS_DIR = STORAGE_DIR / "notebook_results" / "notebook_12_final_audit"
CHECKPOINTS_DIR = STORAGE_DIR / "checkpoints"


class TestNotebook12Verification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nb_path = SANDBOX_DIR / "12-final-scientific-audit.ipynb"
        cls.ckpt_path = CHECKPOINTS_DIR / "final_scientific_audit_checkpoint.pt"
        cls.manifest_path = CHECKPOINTS_DIR / "FINAL_SCIENTIFIC_AUDIT_MANIFEST.md"

        with open(cls.nb_path, "r", encoding="utf-8") as f:
            cls.nb = json.load(f)
        cls.cells = cls.nb.get("cells", [])

    def test_01_notebook_12_structure_and_interleaving(self):
        """Rule: Notebook 12 must have strictly alternating markdown/code, zero errors, penultimate summary, ultimate IP."""
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
        self.assertIn("EXECUTIVE SUMMARY & SCIENTIFIC MILESTONES (NOTEBOOK 12)", penult_src)
        self.assertIn("Master Scientific Audit Scorecard", penult_src)

        # Ultimate cell: JCC IP & Copyright Notice
        ult_src = "".join(self.cells[-1].get("source", []))
        self.assertIn("INTELLECTUAL PROPERTY & COPYRIGHT NOTICE", ult_src)
        self.assertIn("Gourgopal Mohapatra", ult_src)
        self.assertIn("JAGANNATH COMMAND CENTER", ult_src)
        self.assertIn("JCC HEADQUARTER", ult_src)
        self.assertIn("RS-SDA Division", ult_src)

    def test_02_directive_1_physical_provenance_audit(self):
        """Rule: Directive 1 must verify 7 core artifacts on disk with valid SHA-256 checksums."""
        cell_03_out = "".join([line for out in self.cells[3].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("TABLE 1: PHYSICAL ARTIFACT CRYPTOGRAPHIC PROVENANCE AUDIT", cell_03_out)
        self.assertIn("ALL 7 CRITICAL ARTIFACTS MATERIALIZED & CERTIFIED", cell_03_out)
        self.assertIn("pinn_richards_model.pt", cell_03_out)
        self.assertIn("enkf_state_database.pt", cell_03_out)
        self.assertIn("uncertainty_registry.pt", cell_03_out)
        self.assertIn("robustness_stress_logs.pt", cell_03_out)
        self.assertIn("hsi_experiment_checkpoint.pt", cell_03_out)
        self.assertIn("ablation_study_checkpoint.pt", cell_03_out)
        self.assertIn("generalization_evaluation_checkpoint.pt", cell_03_out)

    def test_03_directive_2_dimensional_and_physical_consistency(self):
        """Rule: Directive 2 must verify 10 pipeline stages shape lineage and dimensional homogeneity."""
        cell_07_out = "".join([line for out in self.cells[7].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("TABLE 3: SYSTEM-WIDE TENSOR SHAPE & DIMENSIONAL LINEAGE CONTRACT", cell_07_out)
        self.assertIn("All 10 pipeline stages verified for strict shape and dimensional compliance", cell_07_out)

        cell_09_out = "".join([line for out in self.cells[9].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("TABLE 4: PHYSICAL GOVERNING EQUATIONS & DIMENSIONAL HOMOGENEITY AUDIT", cell_09_out)
        self.assertIn("100% of physical governing equations certified as dimensionally homogeneous", cell_09_out)

    def test_04_directive_3_results_scientific_audit(self):
        """Rule: Directive 3 must empirically verify Richards mass balance, EnKF squashing, and conformal coverage."""
        cell_11_out = "".join([line for out in self.cells[11].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("AUDIT RESULT: PHYSICS PINN & ENKF FILTER CORE STATE", cell_11_out)
        self.assertIn("Contract <= 1.0e-4: PASS", cell_11_out)
        self.assertIn("Contract <= -60%: PASS", cell_11_out)

        cell_13_out = "".join([line for out in self.cells[13].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("AUDIT RESULT: UNCERTAINTY QUANTIFICATION & SENSOR ROBUSTNESS", cell_13_out)
        self.assertIn("Within +/-2.5% tolerance: PASS", cell_13_out)

    def test_05_domain_translation_live_execution(self):
        """Rule: Agronomy and Civil domain translators execute successfully and produce physically valid metrics."""
        cell_19_out = "".join([line for out in self.cells[19].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("AGRONOMIC DOMAIN TRANSLATION AUDIT", cell_19_out)
        self.assertIn("Domain Name                  : agriculture", cell_19_out)
        self.assertIn("Estimated Water Savings      : 28.4%", cell_19_out)

        cell_21_out = "".join([line for out in self.cells[21].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("CIVIL / GEOTECHNICAL DOMAIN TRANSLATION AUDIT", cell_21_out)
        self.assertIn("Domain Name                   : civil", cell_21_out)
        self.assertIn("Mean Effective Bearing (q_ult):", cell_21_out)
        self.assertIn("Site Trafficability Grade     :", cell_21_out)

    def test_06_directive_4_failure_register_and_boundaries(self):
        """Rule: Directive 4 must log all historical defects with resolutions and verify 0 open critical defects."""
        cell_23_out = "".join([line for out in self.cells[23].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("TABLE 7: SYSTEM FAILURE REGISTER & SCIENTIFIC RESOLUTION AUDIT", cell_23_out)
        self.assertIn("0 UNRESOLVED DEFECTS", cell_23_out)

        cell_25_out = "".join([line for out in self.cells[25].get("outputs", []) for line in out.get("text", [])])
        self.assertIn("TABLE 8: MASTER SCIENTIFIC CLAIMS MATRIX & EMPIRICAL ADJUDICATION", cell_25_out)
        self.assertIn("8/8 CORE SCIENTIFIC CLAIMS EMPIRICALLY CERTIFIED", cell_25_out)

    def test_07_diagnostic_visualization_plots(self):
        """Rule: All 5 publication-grade audit figures must exist in 5_storage/notebook_results/notebook_12_final_audit/."""
        expected_plots = [
            "audit_fig1_performance_radar_octagon.png",
            "audit_fig2_agronomic_decision_space.png",
            "audit_fig3_geotechnical_stability_curves.png",
            "audit_fig4_master_evidence_verification_matrix.png",
            "audit_fig5_model_lock_telemetry_waterfall.png"
        ]

        for plot_name in expected_plots:
            plot_path = RESULTS_DIR / plot_name
            self.assertTrue(plot_path.exists(), f"Diagnostic figure missing: {plot_name}")
            self.assertGreater(plot_path.stat().st_size, 50000, f"Diagnostic figure too small: {plot_name}")

    def test_08_directive_5_model_lock_checkpoint_and_manifest(self):
        """Rule: Directive 5 must serialize final release checkpoint and manifest declaring Model-Lock Candidate v1.0."""
        self.assertTrue(self.ckpt_path.exists())
        self.assertTrue(self.manifest_path.exists())
        self.assertGreater(self.ckpt_path.stat().st_size, 2000)
        self.assertGreater(self.manifest_path.stat().st_size, 2000)

        # Inspect final checkpoint contents
        ckpt = torch.load(self.ckpt_path, weights_only=False)
        self.assertEqual(ckpt["engine"], "AETHER-MRID1607X")
        self.assertEqual(ckpt["version"], "v1.0")
        self.assertEqual(ckpt["status"], "LOCKED_OPERATIONAL_RELEASE")
        self.assertEqual(ckpt["lead_architect"], "Gourgopal Mohapatra")
        self.assertEqual(ckpt["facility"], "JCC CAMPUS 2 (RS-SDA DIVISION)")
        self.assertIn("audit_metrics", ckpt)
        self.assertIn("model_lock_tiers", ckpt)
        self.assertEqual(ckpt["model_lock_tiers"]["tier_1_backbone"], "FROZEN")
        self.assertEqual(ckpt["model_lock_tiers"]["tier_2_uncertainty"], "CALIBRATED")
        self.assertEqual(ckpt["model_lock_tiers"]["tier_3_hyperspectral"], "PROVISIONAL_ON_DEMAND")


if __name__ == "__main__":
    unittest.main()
