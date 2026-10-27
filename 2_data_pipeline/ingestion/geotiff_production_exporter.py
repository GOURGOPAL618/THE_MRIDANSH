"""
THE MRIDANSH : PIPELINE BRIDGE — PRODUCTION GEOTIFF & COG EXPORTER
================================================================================
Mission: Spaceborne Operational Campaign (SOC-AETHER-2026) | Day 11
Subsystem: 2_data_pipeline/ingestion/geotiff_production_exporter.py
"""

from pathlib import Path
import sys

_CAMPAIGN_EXEC = Path(__file__).resolve().parent.parent.parent / "9_spaceborne_operational_campaign" / "4_execution_engine"
if str(_CAMPAIGN_EXEC) not in sys.path:
    sys.path.insert(0, str(_CAMPAIGN_EXEC))

from geotiff_production_exporter import GeoTIFFProductionExporter

__all__ = ["GeoTIFFProductionExporter"]
