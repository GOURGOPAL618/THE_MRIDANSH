"""
THE MRIDANSH : AUTOMATED TEST SUITE — DAY 12 AGRICULTURE DOMAIN TRANSLATOR
================================================================================
Mission: Phase 4 (Domain Translators & Downstream Intelligence) | Day 12
Subsystem: tests/test_day12_agronomy_translator.py
Standards: United Nations FAO-56, USDA-NRCS Pedotransfer, DO-178C Level-A Avionics Rigor

Contracts Tested:
  • AGRI-01: Mathematical Boundedness (0 <= Ks <= 1.0, 0 <= CWSI <= 1.0, Ks + CWSI == 1.0)
  • AGRI-02: Hydraulic Invariants & Mass Balance (RAW <= TAW, Dr >= 0, ETc_act <= ETc_pot)
  • AGRI-03: Real Spaceborne Telemetry Numerical Integrity (0 NaNs, 0 Infs across 4,096 pixels)
  • AGRI-04: Dynamic Phenology & Biological Monotonic Root Deepening (Zr_min <= Zr <= Zr_max)
  • AGRI-05: Real-Time Operational Latency SLA (< 0.010000 ms/pixel for 64x64 scene)
================================================================================
"""

import sys
import time
from pathlib import Path
import numpy as np
import pytest
import torch

_REPO_ROOT = Path(__file__).resolve().parent.parent
_AGRONOMY_DIR = _REPO_ROOT / "4_domain_translators" / "agronomy"

for p in [str(_REPO_ROOT), str(_AGRONOMY_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from soil_water_reservoir import SoilWaterReservoirEngine, USDA_TEXTURE_PROPERTIES
from dynamic_phenology import DynamicPhenologyEngine
from fao56_dual_kc import FAO56DualKcEngine
from crop_water_stress import CropWaterStressEngine
from agronomy_domain_engine import AgronomyDomainEngine, AgronomicStateVector


class TestDay12AgronomyTranslator:
    """Rigorous verification suite for Day 12 FAO-56 crop hydraulics and water stress."""

    @pytest.fixture(autouse=True)
    def setup_agronomy_system(self):
        self.crop_taxonomy_path = _AGRONOMY_DIR / "crop_taxonomy.json"
        self.engine = AgronomyDomainEngine(crop_taxonomy_path=self.crop_taxonomy_path)
        self.reservoir = SoilWaterReservoirEngine(crop_taxonomy_path=self.crop_taxonomy_path)
        self.pheno = DynamicPhenologyEngine()
        self.dual_kc = FAO56DualKcEngine()
        self.stress = CropWaterStressEngine()

        self.bundle_pt = (
            _REPO_ROOT
            / "9_spaceborne_operational_campaign"
            / "2_harmonized_tensors"
            / "s1_s2_dem_era5_harmonized_bundle.pt"
        )

    def test_agri_01_mathematical_boundedness(self):
        """
        [CONTRACT AGRI-01] Validates that Ks and CWSI strictly conform to [0.0, 1.0]
        and satisfy the complementary relation Ks + CWSI == 1.0 across all stress regimes.
        """
        # Test synthetic array spanning zero depletion to extreme over-depletion
        taw = 100.0  # mm
        raw = 40.0   # mm
        depletions = np.array([-10.0, 0.0, 20.0, 40.0, 70.0, 100.0, 150.0], dtype=np.float32)

        ks_vals = [self.stress.compute_water_stress_coefficient(d, raw, taw) for d in depletions]
        cwsi_vals = [self.stress.compute_crop_water_stress_index(k) for k in ks_vals]

        for d, ks, cwsi in zip(depletions, ks_vals, cwsi_vals):
            # Assert boundaries
            assert 0.0 <= ks <= 1.0, f"Ks out of bounds [0, 1]: {ks} for Dr={d}"
            assert 0.0 <= cwsi <= 1.0, f"CWSI out of bounds [0, 1]: {cwsi} for Dr={d}"
            assert np.isclose(ks + cwsi, 1.0, atol=1e-5), f"Complementarity breached: {ks} + {cwsi} != 1.0"

        # Specific regimes checks
        assert ks_vals[1] == 1.0 and cwsi_vals[1] == 0.0, "Dr=0 must yield Ks=1.0, CWSI=0.0 (No stress)"
        assert ks_vals[3] == 1.0 and cwsi_vals[3] == 0.0, "Dr=RAW must yield Ks=1.0, CWSI=0.0 (Threshold of stress)"
        assert ks_vals[5] == 0.0 and cwsi_vals[5] == 1.0, "Dr=TAW must yield Ks=0.0, CWSI=1.0 (Full wilting)"
        assert ks_vals[6] == 0.0 and cwsi_vals[6] == 1.0, "Dr > TAW must clamp to Ks=0.0, CWSI=1.0"

    def test_agri_02_hydraulic_invariants_and_mass_balance(self):
        """
        [CONTRACT AGRI-02] Verifies conservation of mass and hydraulic reservoir ordering:
        RAW <= TAW, Dr >= 0, ETc_act <= ETc_pot, and USDA hydraulic ordering.
        """
        # 1. USDA 12 textures hydraulic ordering
        for name, prop in USDA_TEXTURE_PROPERTIES.items():
            assert 0.0 <= prop.theta_res < prop.theta_wp < prop.theta_fc < prop.theta_sat <= 1.0, (
                f"USDA texture {name} violates hydraulic ordering"
            )

        # 2. RAW <= TAW invariant across all crops
        crops = ["rice_paddy", "wheat", "maize", "sugarcane", "cotton", "potato"]
        for c in crops:
            res = self.reservoir.compute_available_water(
                theta_fc=0.32, theta_wp=0.18, z_r_m=0.80, crop_type_or_p=c
            )
            assert res.raw_mm <= res.taw_mm, f"RAW > TAW for crop {c}"
            assert res.taw_mm > 0.0, f"TAW non-positive for crop {c}"

        # 3. ETc_act <= ETc_pot invariant
        out = self.stress.evaluate_stress(
            theta_rz=0.22,
            theta_fc=0.32,
            z_r_m=0.60,
            raw_mm=30.0,
            taw_mm=80.0,
            kcb=1.10,
            ke=0.10,
            et0_mm_day=5.0,
        )
        assert out.dr_mm >= 0.0, "Depletion must be non-negative"
        etc_pot = (1.10 + 0.10) * 5.0
        assert out.etc_act_mm_day <= etc_pot + 1e-5, "Actual ET cannot exceed potential ET"
        assert out.et_deficit_mm_day >= 0.0, "Transpiration deficit must be non-negative"

    def test_agri_03_spaceborne_telemetry_numerical_integrity(self):
        """
        [CONTRACT AGRI-03] Executes end-to-end forward translation across the certified
        Spaceborne Flight Bundle (Sentinel-1 SAR + Sentinel-2 optical + ERA5 weather),
        verifying 0 NaNs and 0 Infs across all 4,096 spatial pixels.
        """
        assert self.bundle_pt.exists(), f"Flight bundle missing: {self.bundle_pt}"
        bundle = torch.load(self.bundle_pt, weights_only=False)

        opt_tensor = bundle["optical"].squeeze(0).numpy()       # [4, 64, 64]
        soil_output = bundle["soil_state_output"]
        theta_surf = soil_output["volumetric_moisture"].squeeze().numpy()  # [64, 64]
        
        # Approximate root-zone moisture via physical attenuation for test
        theta_rz = np.clip(theta_surf * 0.95 + 0.01, 0.05, 0.45)

        state = self.engine.forward(
            optical_reflectance_or_ndvi=opt_tensor,
            theta_surf=theta_surf,
            theta_rz=theta_rz,
            soil_texture="silt_loam",
            crop_name="wheat",
            et0_mm_day=4.80,
        )

        assert isinstance(state, AgronomicStateVector)
        H, W = theta_surf.shape

        # Verify array dimensions
        for field_name in [
            "ndvi", "fractional_cover", "root_depth_m", "taw_mm", "raw_mm",
            "kcb", "ke", "kc_potential", "root_depletion_dr_mm", "water_stress_ks",
            "cwsi", "etc_actual_mm_day", "transpiration_deficit_mm_day",
        ]:
            arr = getattr(state, field_name)
            assert arr.shape == (H, W), f"Shape mismatch for {field_name}: {arr.shape} != {(H, W)}"
            assert not np.any(np.isnan(arr)), f"DO-178C Violation: NaN encountered in {field_name}"
            assert not np.any(np.isinf(arr)), f"DO-178C Violation: Inf encountered in {field_name}"

        # Physics bounds checks
        assert np.all(state.water_stress_ks >= 0.0) and np.all(state.water_stress_ks <= 1.0)
        assert np.all(state.cwsi >= 0.0) and np.all(state.cwsi <= 1.0)
        assert np.all(state.raw_mm <= state.taw_mm)

    def test_agri_04_dynamic_phenology_monotonic_root_deepening(self):
        """
        [CONTRACT AGRI-04] Asserts that dynamic rooting depth Zr and basal coefficient Kcb
        monotonically scale within biological constraints [Zr_min, Zr_max] as NDVI increases.
        """
        ndvi_spectrum = np.linspace(-0.2, 0.9, 100)
        fc_spectrum = self.pheno.compute_fractional_cover(ndvi_spectrum)

        # 1. Fractional cover monotonicity
        assert np.all(np.diff(fc_spectrum) >= 0.0), "fc must be non-decreasing with NDVI"
        assert np.min(fc_spectrum) == 0.0 and np.max(fc_spectrum) == 1.0

        # 2. Dynamic root elongation for maize (Zr: 0.15m to 1.20m)
        maize_params = self.reservoir.get_crop_parameters("maize")
        zr_maize = self.pheno.compute_dynamic_root_depth(
            fc_spectrum,
            zr_min_m=maize_params["rooting_depth_min_m"],
            zr_max_m=maize_params["rooting_depth_max_m"],
        )
        assert np.all(np.diff(zr_maize) >= 0.0), "Root depth must increase monotonically with fc"
        assert np.isclose(zr_maize[0], maize_params["rooting_depth_min_m"])
        assert np.isclose(zr_maize[-1], maize_params["rooting_depth_max_m"])

        # 3. Kcb monotonicity
        kcb_maize = self.pheno.compute_basal_crop_coefficient(
            fc_spectrum,
            kcb_ini=maize_params["kcb_initial"],
            kcb_mid=maize_params["kcb_mid"],
        )
        assert np.all(np.diff(kcb_maize) >= 0.0), "Kcb must increase monotonically with fc"

    def test_agri_05_realtime_latency_sla(self):
        """
        [CONTRACT AGRI-05] Enforces strict DO-178C Level-A real-time processing SLA:
        Full forward agronomic decomposition of a 64x64 scene must execute in < 0.010 ms/pixel.
        """
        H, W = 64, 64
        synth_ndvi = np.full((H, W), 0.55, dtype=np.float32)
        theta_surf = np.full((H, W), 0.24, dtype=np.float32)
        theta_rz = np.full((H, W), 0.22, dtype=np.float32)

        # Warm-up pass
        _ = self.engine.forward(
            optical_reflectance_or_ndvi=synth_ndvi,
            theta_surf=theta_surf,
            theta_rz=theta_rz,
            soil_texture="loam",
            crop_name="rice_paddy",
        )

        # Timed benchmark pass
        t0 = time.perf_counter()
        state = self.engine.forward(
            optical_reflectance_or_ndvi=synth_ndvi,
            theta_surf=theta_surf,
            theta_rz=theta_rz,
            soil_texture="loam",
            crop_name="rice_paddy",
        )
        elapsed = time.perf_counter() - t0
        latency_px = (elapsed * 1000.0) / (H * W)

        sla_limit = 0.010000  # ms/pixel SLA
        assert latency_px < sla_limit, f"Latency SLA breached: {latency_px:.6f} ms/px >= {sla_limit} ms/px"
        assert state.latency_ms_per_pixel < sla_limit
