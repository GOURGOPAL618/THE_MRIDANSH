"""
THE MRIDANSH : GRAND INTEGRATION TEST SUITE (PHASES 1 & 2 + FULL ENGINE)
========================================================================
Comprehensive, end-to-end unbroken scientific verification uniting:
- Phase 1 (Notebooks 01–04): STAC Ingestion, Preprocessing, Spatial GCN, ConvLSTM.
- Production Engine & Dashboard: GIS Viewports (Days 18-22), Agronomy/Civil Translators, FastAPI.
- Phase 2 (Notebooks 05–08): PINN Richards Physics, EnKF State Estimation,
                             Uncertainty Quantification, Robustness & Fail-Soft Self-Healing.
- The 4 Storage Directories: checkpoints/, state_database/, registry/, telemetry_logs/.
- Complete Mathematical Traceability: Raw telemetry -> Assimilated state -> Uncertainty -> Domain risk.
"""

import os
import sys
import json
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
import torch

ROOT_DIR = Path(__file__).resolve().parent.parent
PIPELINE_DIR = ROOT_DIR / "2_data_pipeline"
CORE_DIR = ROOT_DIR / "3_core_engine"
TRANSLATORS_DIR = ROOT_DIR / "4_domain_translators"
DASHBOARD_DIR = ROOT_DIR / "6_dashboard"
API_DIR = DASHBOARD_DIR / "api"

for p in [ROOT_DIR, PIPELINE_DIR, CORE_DIR, TRANSLATORS_DIR, DASHBOARD_DIR, API_DIR]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Production Core Engine Imports
from preprocessing.grid_tiler import GeospatialGridTiler
from models.spatial_temporal_encoder import SpatialTemporalEncoderBackbone
from physics.richards_engine import RichardsSoilPhysicsEngine
from state_estimation.enkf_filter import EnsembleKalmanFilterEngine

# Production Domain Translators
from base import DomainInput, DomainOutput
from agronomy_translator import AgronomyHealthTranslator
from civil_translator import CivilLoadTranslator
from domain_integrator import DomainIntegrationRouter

# Production Dashboard & FastAPI Ingress
from fastapi.testclient import TestClient
from main import app


class GrandPhase1AndPhase2IntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = ROOT_DIR
        cls.sandbox_dir = cls.repo_root / "1_notebooks_sandbox"
        cls.storage_dir = cls.repo_root / "5_storage"
        cls.results_dir = cls.storage_dir / "notebook_results"
        cls.testing_results_dir = cls.repo_root / "TESTING RESULTS"
        cls.data_proc_dir = cls.repo_root / "data" / "processed"

        cls.client = TestClient(app)

    def test_01_all_eight_notebooks_exist_and_zero_python_scripts_in_sandbox(self):
        """Rule: 1_notebooks_sandbox must strictly contain only Notebooks 01-08 (.ipynb only, zero .py)."""
        py_files = [f for f in os.listdir(self.sandbox_dir) if f.endswith(".py")]
        self.assertEqual(py_files, [], f"Forbidden .py files found in sandbox: {py_files}")

        expected_notebooks = [
            "01-data-ingestion.ipynb",
            "02-preprocessing.ipynb",
            "03-spatial-modeling.ipynb",
            "04-temporal-modeling.ipynb",
            "05-physics-validation.ipynb",
            "06-state-estimation.ipynb",
            "07-uncertainty-analysis.ipynb",
            "08-robustness-and-failure-analysis.ipynb"
        ]
        for nb_name in expected_notebooks:
            nb_path = self.sandbox_dir / nb_name
            self.assertTrue(nb_path.exists(), f"Missing core notebook: {nb_name}")
            self.assertGreater(nb_path.stat().st_size, 5000, f"Notebook file too small: {nb_name}")

    def test_02_all_eight_notebooks_strictly_interleaved_and_executed_cleanly(self):
        """Rule: All 8 notebooks must have every code cell preceded by markdown, and all code executed with 0 errors."""
        for nb_idx in range(1, 9):
            nb_files = [f for f in os.listdir(self.sandbox_dir) if f.startswith(f"{nb_idx:02d}-") and f.endswith(".ipynb")]
            self.assertEqual(len(nb_files), 1, f"Expected exactly one notebook for index {nb_idx}")
            nb_path = self.sandbox_dir / nb_files[0]

            with open(nb_path, "r", encoding="utf-8") as f:
                nb = json.load(f)

            cells = nb.get("cells", [])
            self.assertGreaterEqual(len(cells), 20, f"Notebook {nb_files[0]} has fewer than 20 cells")

            # Check alternating rule
            for i, c in enumerate(cells):
                if c.get("cell_type") == "code":
                    self.assertGreater(i, 0, f"First cell in {nb_files[0]} cannot be code")
                    prev_type = cells[i - 1].get("cell_type")
                    self.assertEqual(prev_type, "markdown", f"Code cell at index {i} in {nb_files[0]} not preceded by markdown")

                    # Check execution count and zero error
                    exec_count = c.get("execution_count")
                    self.assertIsNotNone(exec_count, f"Cell {i} in {nb_files[0]} was not executed")
                    self.assertGreater(exec_count, 0)

                    for out in c.get("outputs", []):
                        self.assertNotEqual(out.get("output_type"), "error", f"Error in {nb_files[0]} cell {i}")

            # Check penultimate & ultimate cells
            penult_src = "".join(cells[-2].get("source", []))
            ult_src = "".join(cells[-1].get("source", []))

            self.assertIn("EXECUTIVE SUMMARY", penult_src, f"Penultimate summary missing in {nb_files[0]}")
            self.assertIn("INTELLECTUAL PROPERTY & COPYRIGHT NOTICE", ult_src, f"IP notice missing in {nb_files[0]}")
            self.assertIn("Gourgopal Mohapatra", ult_src)
            self.assertIn("JCC HEADQUARTER", ult_src)

    def test_03_phase1_data_to_spatial_temporal_pipeline(self):
        """Rule: Phase 1 pipeline (NB01 to NB04) must provide verified multi-sensor matrices and latents."""
        # 1. Telemetry Ingestion (NB02)
        telemetry_path = self.results_dir / "notebook_02_preprocessing" / "preprocessed_telemetry.csv"
        self.assertTrue(telemetry_path.exists())
        df = pd.read_csv(telemetry_path)
        self.assertGreater(len(df), 20)
        self.assertIn("s2_cloud_cover_pct", df.columns)
        self.assertIn("s1_vh_db", df.columns)

        # 2. Spatial Graph (NB03)
        gcn_path = self.results_dir / "notebook_03_spatial_modeling" / "spatial_gcn_embeddings.pt"
        mesh_path = self.results_dir / "notebook_03_spatial_modeling" / "spatial_graph_mesh.npz"
        self.assertTrue(gcn_path.exists())
        self.assertTrue(mesh_path.exists())
        gcn_emb = torch.load(gcn_path, weights_only=False)
        self.assertIn("spatial_embeddings_nodes", gcn_emb)
        self.assertIsInstance(gcn_emb["spatial_embeddings_nodes"], torch.Tensor)

        # 3. Temporal ConvLSTM States (NB04)
        temporal_path = self.results_dir / "notebook_04_temporal_modeling" / "temporal_latent_states.pt"
        self.assertTrue(temporal_path.exists())
        latent_bundle = torch.load(temporal_path, weights_only=False)
        self.assertIn("h_final_test", latent_bundle)
        self.assertIn("rollout_predictions", latent_bundle)

    def test_04_yesterday_night_interactive_gis_and_dashboard_artifacts(self):
        """Rule: Production interactive GIS viewports, GeoJSON files, and FastAPI ingress must be valid."""
        # Check GIS Map Artifacts generated in TESTING RESULTS
        gis_files = [
            "test_map_day18.html",
            "test_aoi_draw_day19.html",
            "test_raster_overlay_day20.html",
            "test_surface_3d_day21.html",
            "test_spatial_grid_day22.geojson"
        ]
        for gf in gis_files:
            gp = self.testing_results_dir / gf
            self.assertTrue(gp.exists(), f"Missing GIS artifact: {gf}")
            self.assertGreater(gp.stat().st_size, 100, f"GIS file too small: {gf}")

        # Check GeoJSON Validity
        with open(self.testing_results_dir / "test_spatial_grid_day22.geojson", "r", encoding="utf-8") as f:
            geojson_data = json.load(f)
        self.assertEqual(geojson_data.get("type"), "FeatureCollection")
        self.assertGreater(len(geojson_data.get("features", [])), 0)

        # Check Domain Translators
        router = DomainIntegrationRouter()
        enkf_payload = {
            "posterior_soil_state": np.full((20, 20), 0.285),
            "uncertainty_variance": 0.0009
        }
        res = router.integrate_enkf_state(enkf_payload, domain="both")
        self.assertEqual(res.status, "SUCCESS")
        self.assertIn("agriculture", res.domain_output)
        self.assertIn("civil", res.domain_output)

        # Check FastAPI API Ingress
        resp_health = self.client.get("/health")
        self.assertEqual(resp_health.status_code, 200)
        self.assertEqual(resp_health.json().get("status"), "HEALTHY")

    def test_05_phase2_notebook_05_physics_pinn_richards_engine(self):
        """Rule: Notebook 05 PINN model and SWRC parameters must be certified in checkpoints/."""
        model_path = self.storage_dir / "checkpoints" / "pinn_richards_model.pt"
        manifest_path = self.storage_dir / "checkpoints" / "PINN_RICHARDS_MODEL_MANIFEST.md"
        self.assertTrue(model_path.exists())
        self.assertTrue(manifest_path.exists())

        pinn_bundle = torch.load(model_path, weights_only=False)
        self.assertIn("model_state_dict", pinn_bundle)
        self.assertIn("soil_params", pinn_bundle)
        self.assertIn("pde_reduction_pct", pinn_bundle)

        # Richards Loam parameters validation
        soil_p = pinn_bundle["soil_params"]
        self.assertAlmostEqual(soil_p["theta_s"], 0.43, places=2)
        self.assertAlmostEqual(soil_p["theta_r"], 0.078, places=3)
        self.assertGreater(pinn_bundle["pde_reduction_pct"], 60.0)

    def test_06_phase2_notebook_06_state_estimation_enkf_database(self):
        """Rule: Notebook 06 EnKF state database must be certified in state_database/."""
        db_path = self.storage_dir / "state_database" / "enkf_state_database.pt"
        manifest_path = self.storage_dir / "state_database" / "ENKF_STATE_ESTIMATION_MANIFEST.md"
        self.assertTrue(db_path.exists())
        self.assertTrue(manifest_path.exists())

        enkf_bundle = torch.load(db_path, weights_only=False)
        self.assertIn("state_variables", enkf_bundle)
        self.assertIn("spatial_assimilation", enkf_bundle)
        self.assertIn("mean_var_reduction_pct", enkf_bundle["spatial_assimilation"])
        self.assertGreater(enkf_bundle["spatial_assimilation"]["mean_var_reduction_pct"], 70.0)

        # Check state variables in state_variables dict
        state_vars = enkf_bundle["state_variables"]
        for v in ["theta_root", "bulk_density", "K_sat", "SOC"]:
            self.assertIn(v, state_vars)

    def test_07_phase2_notebook_07_uncertainty_quantification_calibration(self):
        """Rule: Notebook 07 Uncertainty Registry must be certified in registry/ with Gaussian reliability."""
        reg_path = self.storage_dir / "registry" / "uncertainty_registry.pt"
        manifest_path = self.storage_dir / "registry" / "UNCERTAINTY_REGISTRY_MANIFEST.md"
        self.assertTrue(reg_path.exists())
        self.assertTrue(manifest_path.exists())

        unc_bundle = torch.load(reg_path, weights_only=False)
        self.assertIn("sigma_total", unc_bundle)
        self.assertIn("calibration", unc_bundle)

        cal = unc_bundle["calibration"]
        self.assertLess(cal["err_1sig"], 2.0, "1-sigma calibration error must be < 2.0%")
        self.assertLess(cal["err_2sig"], 2.0, "2-sigma calibration error must be < 2.0%")
        self.assertLess(cal["decile_corr"], -0.85, "High Confidence must correlate with lower error (r < -0.85)")
        self.assertLess(cal["mae_high"], cal["mae_med"], "High Conf MAE < Med Conf MAE")
        self.assertLess(cal["mae_med"], cal["mae_low"], "Med Conf MAE < Low Conf MAE")

    def test_08_phase2_notebook_08_robustness_failure_and_self_healing(self):
        """Rule: Notebook 08 telemetry logs and manifest must be certified in telemetry_logs/."""
        log_path = self.storage_dir / "telemetry_logs" / "robustness_stress_logs.pt"
        manifest_path = self.storage_dir / "telemetry_logs" / "ROBUSTNESS_STRESS_MANIFEST.md"
        self.assertTrue(log_path.exists())
        self.assertTrue(manifest_path.exists())

        stress_bundle = torch.load(log_path, weights_only=False)
        self.assertIn("dropout_scenarios", stress_bundle)
        self.assertIn("corruption_sweeps", stress_bundle)
        self.assertIn("health_classification", stress_bundle)
        self.assertIn("self_healing", stress_bundle)

        # Monotonicity correlation
        corr = stress_bundle["corruption_sweeps"]["monotonicity_corr"]
        self.assertGreater(corr, 0.95)

        # Self-healing recovery
        sh = stress_bundle["self_healing"]
        peak_sigma = sh["uncertainties"][7]
        recovered_sigma = sh["uncertainties"][10]
        self.assertGreater(peak_sigma, recovered_sigma)
        self.assertLess(recovered_sigma, 0.040)

    def test_09_all_four_storage_blank_folders_and_manifests_certified(self):
        """Rule: All 4 originally blank folders in 5_storage must have checkpoints and .md manifests."""
        folder_matrix = [
            ("checkpoints", "pinn_richards_model.pt", "PINN_RICHARDS_MODEL_MANIFEST.md"),
            ("state_database", "enkf_state_database.pt", "ENKF_STATE_ESTIMATION_MANIFEST.md"),
            ("registry", "uncertainty_registry.pt", "UNCERTAINTY_REGISTRY_MANIFEST.md"),
            ("telemetry_logs", "robustness_stress_logs.pt", "ROBUSTNESS_STRESS_MANIFEST.md"),
        ]
        for folder_name, checkpoint_file, manifest_file in folder_matrix:
            folder_path = self.storage_dir / folder_name
            cp_path = folder_path / checkpoint_file
            mf_path = folder_path / manifest_file

            self.assertTrue(folder_path.exists(), f"Storage folder {folder_name} missing")
            self.assertTrue(cp_path.exists(), f"Checkpoint {checkpoint_file} missing in {folder_name}")
            self.assertTrue(mf_path.exists(), f"Manifest {manifest_file} missing in {folder_name}")
            self.assertGreater(cp_path.stat().st_size, 5000)
            self.assertGreater(mf_path.stat().st_size, 500)

    def test_10_grand_unbroken_provenance_trace_nb01_to_dashboard(self):
        """Rule: Mathematical contract must trace continuously from STAC ingestion to Dashboard translation."""
        # 1. Start with preprocessed telemetry from NB02
        df_tel = pd.read_csv(self.results_dir / "notebook_02_preprocessing" / "preprocessed_telemetry.csv")
        s2_cloud = float(df_tel["s2_cloud_cover_pct"].mean())
        s1_vh = float(df_tel["s1_vh_db"].mean())

        # 2. Pass through PINN physics bounds from NB05
        pinn = torch.load(self.storage_dir / "checkpoints" / "pinn_richards_model.pt", weights_only=False)
        theta_s = pinn["soil_params"]["theta_s"]
        theta_r = pinn["soil_params"]["theta_r"]

        # 3. Ingest EnKF posterior state from NB06
        enkf = torch.load(self.storage_dir / "state_database" / "enkf_state_database.pt", weights_only=False)
        post_grid = enkf["spatial_assimilation"]["posterior_grid"]
        sample_moisture = float(post_grid[10, 10])

        # Verify physics bounds hold
        self.assertGreaterEqual(sample_moisture, theta_r)
        self.assertLessEqual(sample_moisture, theta_s)

        # 4. Ingest Uncertainty & Confidence from NB07
        unc = torch.load(self.storage_dir / "registry" / "uncertainty_registry.pt", weights_only=False)
        sample_sigma = float(unc["sigma_total"][10, 10])
        sample_conf = float(unc["confidence_score"][10, 10] * 100.0)

        # 5. Ingest Stress Health Classification from NB08
        stress = torch.load(self.storage_dir / "telemetry_logs" / "robustness_stress_logs.pt", weights_only=False)
        sample_state = int(stress["health_classification"]["state_grid"][10, 10])
        self.assertIn(sample_state, [0, 1, 2, 3])

        # 6. Translate to Agronomy & Civil Geotechnical Decision Vectors
        router = DomainIntegrationRouter()
        enkf_payload = {
            "posterior_soil_state": post_grid,
            "uncertainty_variance": float(sample_sigma**2)
        }
        out = router.integrate_enkf_state(enkf_payload, domain="both")
        self.assertEqual(out.status, "SUCCESS")
        self.assertIn("civil", out.domain_output)
        self.assertIn("agriculture", out.domain_output)

        # 7. Verify REST API Endpoint
        resp_status = self.client.get("/api/v1/status")
        self.assertEqual(resp_status.status_code, 200)
        self.assertEqual(resp_status.json().get("status"), "ONLINE")

    def test_11_grand_century_ablation_generalization_multi_regime_stress(self):
        """Rule (Century Test 1/2): Verify Notebooks 09-11 multi-sensor synthesis, ablation LOCO, and 5-regime stress holdout."""
        # 1. Verify Hyperspectral Experiment Checkpoint (Notebook 09)
        hsi_ckpt_path = self.storage_dir / "checkpoints" / "hsi_experiment_checkpoint.pt"
        self.assertTrue(hsi_ckpt_path.exists())
        hsi_ckpt = torch.load(hsi_ckpt_path, weights_only=False)
        self.assertIn("verdict", hsi_ckpt)
        self.assertIn("recommendation", hsi_ckpt)
        self.assertIn("TARGETED OPTIONAL AUGMENTATION", hsi_ckpt["verdict"])
        self.assertIn("Lean Production Backbone", hsi_ckpt["recommendation"])

        # 2. Verify Ablation Study Checkpoint & LOCO Analysis (Notebook 10)
        ablation_ckpt_path = self.storage_dir / "checkpoints" / "ablation_study_checkpoint.pt"
        self.assertTrue(ablation_ckpt_path.exists())
        ablation_ckpt = torch.load(ablation_ckpt_path, weights_only=False)
        self.assertEqual(ablation_ckpt["best_baseline_config"], "Config G")
        self.assertAlmostEqual(ablation_ckpt["best_baseline_rmse"], 0.00485, places=4)
        self.assertGreater(ablation_ckpt["best_baseline_r2"], 0.90)
        self.assertIn("Tier 1 (Mission-Critical Core)", ablation_ckpt["essentiality_tiers"])

        # 3. Verify Generalization Evaluation Checkpoint (Notebook 11)
        gen_ckpt_path = self.storage_dir / "checkpoints" / "generalization_evaluation_checkpoint.pt"
        self.assertTrue(gen_ckpt_path.exists())
        gen_ckpt = torch.load(gen_ckpt_path, weights_only=False)
        self.assertIn("spatial_generalization_gap", gen_ckpt)
        self.assertLessEqual(gen_ckpt["spatial_generalization_gap"], 0.0030)
        self.assertEqual(len(gen_ckpt["regimes_evaluated"]), 5)

    def test_12_grand_century_system_closure_model_lock_certification(self):
        """Rule (Century Test 2/2): Verify Notebook 12 Final Scientific Audit, all 12 sandbox notebooks, and Model-Lock Candidate v1.0."""
        # 1. Verify all 12 Canonical Notebooks in 1_notebooks_sandbox/
        expected_notebooks = [
            "01-data-ingestion.ipynb",
            "02-preprocessing.ipynb",
            "03-spatial-modeling.ipynb",
            "04-temporal-modeling.ipynb",
            "05-physics-validation.ipynb",
            "06-state-estimation.ipynb",
            "07-uncertainty-analysis.ipynb",
            "08-robustness-and-failure-analysis.ipynb",
            "09-hyperspectral-experiment.ipynb",
            "10-ablation-study.ipynb",
            "11-generalization-baseline-evaluation.ipynb",
            "12-final-scientific-audit.ipynb"
        ]
        sandbox_files = [f.name for f in self.sandbox_dir.glob("*.ipynb")]
        self.assertEqual(len(sandbox_files), 12, f"Expected exactly 12 notebooks in sandbox, found {len(sandbox_files)}")
        for nb_name in expected_notebooks:
            self.assertIn(nb_name, sandbox_files, f"Canonical notebook {nb_name} missing from sandbox!")

        # 2. Verify Final Scientific Audit Checkpoint & Manifest (Notebook 12)
        audit_ckpt_path = self.storage_dir / "checkpoints" / "final_scientific_audit_checkpoint.pt"
        audit_mf_path = self.storage_dir / "checkpoints" / "FINAL_SCIENTIFIC_AUDIT_MANIFEST.md"
        self.assertTrue(audit_ckpt_path.exists())
        self.assertTrue(audit_mf_path.exists())

        audit_ckpt = torch.load(audit_ckpt_path, weights_only=False)
        self.assertEqual(audit_ckpt["engine"], "AETHER-MRID1607X")
        self.assertEqual(audit_ckpt["version"], "v1.0")
        self.assertEqual(audit_ckpt["status"], "LOCKED_OPERATIONAL_RELEASE")
        self.assertEqual(audit_ckpt["lead_architect"], "Gourgopal Mohapatra")
        self.assertEqual(audit_ckpt["facility"], "JCC CAMPUS 2 (RS-SDA DIVISION)")

        # 3. Verify Tier Lock Contracts
        tiers = audit_ckpt["model_lock_tiers"]
        self.assertEqual(tiers["tier_1_backbone"], "FROZEN")
        self.assertEqual(tiers["tier_2_uncertainty"], "CALIBRATED")
        self.assertEqual(tiers["tier_3_hyperspectral"], "PROVISIONAL_ON_DEMAND")

        # 4. Verify 5 Diagnostic Figures for Notebook 12
        nb12_fig_dir = self.results_dir / "notebook_12_final_audit"
        self.assertTrue(nb12_fig_dir.exists())
        for fig_name in [
            "audit_fig1_performance_radar_octagon.png",
            "audit_fig2_agronomic_decision_space.png",
            "audit_fig3_geotechnical_stability_curves.png",
            "audit_fig4_master_evidence_verification_matrix.png",
            "audit_fig5_model_lock_telemetry_waterfall.png"
        ]:
            fig_path = nb12_fig_dir / fig_name
            self.assertTrue(fig_path.exists(), f"Figure {fig_name} missing from {nb12_fig_dir}")
            self.assertGreater(fig_path.stat().st_size, 50000)


if __name__ == "__main__":
    unittest.main()
