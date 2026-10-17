"""
THE MRIDANSH : AUTOMATED TEST SUITE — IN-SITU COLLOCATION & BASELINES
================================================================================
Mission: Spaceborne Operational Campaign (SOC-AETHER-2026) | Day 09
Subsystem: tests/test_insitu_collocation_and_baselines.py
Standards: CEOS-WGCV Interoperability, ISMN Protocols, DO-178C Level-A Compliance

Contracts Tested:
  • SOC-11: ISMN/SMAP Ground Truth In-Situ Ingestion Bounds & Schema Verification
  • SOC-12: Spatial-Temporal Coordinate Collocation & 29-Feature Zero-NaN Extraction
  • SOC-13: Physical Sensor-Moisture Correlation Integrity (SAR σ⁰ & Topographic TWI)
  • SOC-14: Classical Naive Optical Regression Empirical OLS Fitting & Bounds
  • SOC-15: Semi-Empirical SAR Water Cloud Model (WCM) Inversion & Benchmark Export
================================================================================
"""

import sys
import json
import pytest
from pathlib import Path
import numpy as np
import pandas as pd
import torch

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CAMPAIGN_EXEC = _REPO_ROOT / "9_spaceborne_operational_campaign" / "4_execution_engine"
_DATA_PIPELINE = _REPO_ROOT / "2_data_pipeline"

for p in [str(_REPO_ROOT), str(_CAMPAIGN_EXEC), str(_DATA_PIPELINE)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from insitu_ground_truth_ingestor import InSituGroundTruthIngestor
from spatial_temporal_collocator import SpatialTemporalCollocator
from comparative_baseline_benchmarks import (
    NaiveOpticalRegressionBaseline,
    WaterCloudModelBaseline,
    BaselineBenchmarkEngine,
    compute_hydrological_metrics
)


class TestInsituCollocationAndBaselines:
    """Rigorous verification suite for Day 09 in-situ collocation and baseline models."""

    @pytest.fixture(autouse=True)
    def setup_paths(self):
        self.campaign_root = _REPO_ROOT / "9_spaceborne_operational_campaign"
        self.stations_csv = self.campaign_root / "3_ground_truth" / "insitu_soil_stations.csv"
        self.bundle_pt = self.campaign_root / "2_harmonized_tensors" / "s1_s2_dem_era5_harmonized_bundle.pt"
        self.matrix_csv = self.campaign_root / "3_ground_truth" / "collocated_insitu_matrix.csv"

    def test_soc_11_insitu_ground_truth_ingestion_bounds(self):
        """[SOC-11] Verifies ISMN/SMAP station generator conforms to physical bounds and schema."""
        ingestor = InSituGroundTruthIngestor(seed=1607)
        df = ingestor.build_ismn_compliant_network(num_stations=24)

        assert len(df) == 24, f"Expected 24 reference stations, got {len(df)}"
        assert not df.isna().any().any(), "NaN detected in in-situ ground truth network!"
        
        # Schema verification
        for col in InSituGroundTruthIngestor.REQUIRED_COLUMNS:
            assert col in df.columns, f"Missing required ISMN column: {col}"

        # Physical range assertions
        assert (df["surface_moisture_m3m3"] >= 0.05).all() and (df["surface_moisture_m3m3"] <= 0.45).all()
        assert (df["rootzone_moisture_m3m3"] >= 0.10).all() and (df["rootzone_moisture_m3m3"] <= 0.50).all()
        assert (df["bulk_density_g_cm3"] >= 1.10).all() and (df["bulk_density_g_cm3"] <= 1.80).all()
        assert (df["soil_organic_carbon_pct"] >= 0.50).all() and (df["soil_organic_carbon_pct"] <= 5.0).all()

    def test_soc_12_spatial_temporal_collocation_grid_accuracy(self):
        """[SOC-12] Verifies 10m UTM coordinate mapping into raster grid and 29-feature integrity."""
        collocator = SpatialTemporalCollocator(pixel_size_m=10.0)
        assert self.stations_csv.exists(), "Stations CSV missing"
        assert self.bundle_pt.exists(), "Harmonized bundle missing"

        df_collocated, stats = collocator.collocate_stations_with_bundle(
            self.stations_csv, self.bundle_pt
        )

        assert len(df_collocated) == 24
        assert len(df_collocated.columns) == 29
        assert not df_collocated.isna().any().any(), "NaN leak detected in collocated matrix!"
        assert not np.isinf(df_collocated.select_dtypes(include=[np.number]).values).any()

        # Grid bounds: 64x64 raster
        assert (df_collocated["pixel_row"] >= 0).all() and (df_collocated["pixel_row"] < 64).all()
        assert (df_collocated["pixel_col"] >= 0).all() and (df_collocated["pixel_col"] < 64).all()

        # Physical spaceborne ranges
        assert (df_collocated["sar_vv_db"] >= -35.0).all() and (df_collocated["sar_vv_db"] <= 5.0).all()
        assert (df_collocated["ndvi"] >= -0.2).all() and (df_collocated["ndvi"] <= 1.0).all()
        assert (df_collocated["twi"] >= 2.0).all() and (df_collocated["twi"] <= 18.0).all()

    def test_soc_13_physical_sensor_correlation_integrity(self):
        """[SOC-13] Verifies physical sensitivity of microwave SAR and hydrological TWI."""
        collocator = SpatialTemporalCollocator()
        df, stats = collocator.collocate_stations_with_bundle(
            self.stations_csv, self.bundle_pt
        )

        corr_sar = df["sar_vv_db"].corr(df["ground_truth_moisture_m3m3"])
        corr_twi = df["twi"].corr(df["ground_truth_moisture_m3m3"])

        # SAR radar backscatter increases with dielectric constant of moist soil (Target r > 0.50)
        assert corr_sar > 0.50, f"SAR backscatter failed positive moisture correlation: r = {corr_sar:.4f}"
        # Topographic Wetness Index couples strongly with landscape hydrology (|r| > 0.50)
        assert abs(corr_twi) > 0.50, f"TWI failed topographic coupling: r = {corr_twi:.4f}"

    def test_soc_14_naive_optical_regression_baseline(self):
        """[SOC-14] Verifies empirical Ordinary Least Squares optical regression baseline."""
        df = pd.read_csv(str(self.matrix_csv))
        ndvi = df["ndvi"].values
        theta = df["ground_truth_moisture_m3m3"].values

        baseline = NaiveOpticalRegressionBaseline()
        baseline.fit(ndvi, theta)

        assert baseline.slope is not None and baseline.intercept is not None
        preds = baseline.predict(ndvi)

        assert len(preds) == len(theta)
        assert not np.isnan(preds).any()
        assert (preds >= 0.02).all() and (preds <= 0.50).all()
        assert "rmse_m3m3" in baseline.metrics
        assert "mae_m3m3" in baseline.metrics
        assert "pearson_r" in baseline.metrics

    def test_soc_15_sar_water_cloud_model_baseline_and_export(self):
        """[SOC-15] Verifies semi-empirical WCM calibration, inversion, and artifact export."""
        engine = BaselineBenchmarkEngine()
        comparison = engine.run_benchmark(self.matrix_csv)

        assert comparison["status"] == "DO_178C_LEVEL_A_BENCHMARKS_CERTIFIED"
        assert comparison["num_ground_stations"] == 24

        wcm_dict = comparison["baselines"]["classical_sar_water_cloud_model"]
        assert wcm_dict["parameters"]["A_veg_scattering"] >= 0.0
        assert wcm_dict["parameters"]["B_veg_attenuation"] >= 0.0
        assert wcm_dict["parameters"]["D_soil_sensitivity"] > 0.0

        # WCM should achieve lower RMSE than optical baseline
        opt_rmse = comparison["baselines"]["naive_optical_ndvi_regression"]["metrics"]["rmse_m3m3"]
        wcm_rmse = wcm_dict["metrics"]["rmse_m3m3"]
        wcm_corr = wcm_dict["metrics"]["pearson_r"]

        assert wcm_rmse < opt_rmse, f"WCM RMSE ({wcm_rmse}) must outperform Optical OLS ({opt_rmse})"
        assert wcm_corr > 0.70, f"WCM Pearson correlation ({wcm_corr}) must exceed 0.70"

        # Verify export and cryptographic hash seal
        json_path, sha256 = engine.export_benchmark_results(comparison)
        assert json_path.exists(), "Benchmark JSON file missing"
        assert len(sha256) == 64, "Invalid SHA-256 hash length"
