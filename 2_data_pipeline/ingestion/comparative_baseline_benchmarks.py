"""
THE MRIDANSH : COMPARATIVE BASELINE BENCHMARKS GATEWAY & BRIDGE
================================================================================
Mission: Spaceborne Operational Campaign (SOC-AETHER-2026) | Day 09
Subsystem: 2_data_pipeline/ingestion/comparative_baseline_benchmarks.py
Architecture: Ingestion Layer Bridge to Operational Flight Execution Engine

Provides a unified pipeline import interface to:
  9_spaceborne_operational_campaign/4_execution_engine/comparative_baseline_benchmarks.py
================================================================================
"""

import importlib.util
import sys
from pathlib import Path

# Resolve repo root and campaign execution engine paths
_CURRENT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _CURRENT_DIR.parent.parent
_CAMPAIGN_EXEC_ENGINE = _REPO_ROOT / "9_spaceborne_operational_campaign" / "4_execution_engine"
_TARGET_FILE = _CAMPAIGN_EXEC_ENGINE / "comparative_baseline_benchmarks.py"

if not _TARGET_FILE.exists():
    raise FileNotFoundError(f"Operational campaign baseline benchmarks missing at {_TARGET_FILE}")

# Ensure execution engine, core engine, and repo root are in sys.path
for _p in [str(_CAMPAIGN_EXEC_ENGINE), str(_REPO_ROOT / "3_core_engine"), str(_REPO_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

_spec = importlib.util.spec_from_file_location("operational_campaign.comparative_baseline_benchmarks", str(_TARGET_FILE))
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

NaiveOpticalRegressionBaseline = getattr(_module, "NaiveOpticalRegressionBaseline")
WaterCloudModelBaseline = getattr(_module, "WaterCloudModelBaseline")
BaselineBenchmarkEngine = getattr(_module, "BaselineBenchmarkEngine")
compute_hydrological_metrics = getattr(_module, "compute_hydrological_metrics")

__all__ = [
    "NaiveOpticalRegressionBaseline",
    "WaterCloudModelBaseline",
    "BaselineBenchmarkEngine",
    "compute_hydrological_metrics",
]
