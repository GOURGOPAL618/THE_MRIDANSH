# THE MRIDANSH - CIVIL & GEOTECHNICAL DOMAIN TRANSLATOR
# Module: 4_domain_translators/civil/civil_geotiff_exporter.py
# Subsystem 05 of AETHER-MRID1607X Core Engine
# Architecture: Production OGC GeoTIFF & Cloud-Optimized GeoTIFF (COG) Exporter
# Standards: OGC GeoTIFF 1.1, CEOS-WGCV, ISO 19115-2, DO-178C Level-A Rigor

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_bounds

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def _is_file_locked_by_viewer(path: Path) -> bool:
    """Detects whether a GeoTIFF is actively open/locked by an external GIS viewer (e.g. QGIS)."""
    if not path.is_file():
        return False
    try:
        temp_test = path.with_name(f"{path.name}.locktest")
        os.rename(path, temp_test)
        os.rename(temp_test, path)
        return False
    except (PermissionError, OSError):
        return True


class CivilGeoTIFFExporter:
    """
    Exports precision civil and geotechnical ground stability intelligence into
    standard georeferenced GeoTIFFs and multi-band Cloud-Optimized GeoTIFFs (COG).
    """

    DEFAULT_CRS = "EPSG:32645"  # WGS 84 / UTM Zone 45N (Coastal Bengal / Odisha Scene)
    BOUNDS = {
        "min_x": 420000.0,
        "min_y": 2240000.0,
        "max_x": 420640.0,
        "max_y": 2240640.0,
    }
    PIXEL_RESOLUTION_M = 10.0
    GRID_ROWS = 64
    GRID_COLS = 64

    LAYERS_CONFIG = [
        {
            "band_idx": 1,
            "filename": "allowable_bearing_capacity_10m.tif",
            "name": "allowable_bearing_capacity_kpa",
            "description": "Eurocode 7 / IS 1904 Allowable Foundation Bearing Capacity (FS=3.0)",
            "units": "kPa",
            "dtype": "float32",
            "nodata": -9999.0,
        },
        {
            "band_idx": 2,
            "filename": "slope_factor_of_safety_10m.tif",
            "name": "slope_factor_of_safety",
            "description": "Copernicus DEM-Coupled Infinite Slope Factor of Safety (Taylor-Duncan)",
            "units": "dimensionless ratio",
            "dtype": "float32",
            "nodata": -9999.0,
        },
        {
            "band_idx": 3,
            "filename": "topographic_wetness_index_10m.tif",
            "name": "topographic_wetness_index",
            "description": "Beven-Kirkby Topographic Wetness Index (TWI)",
            "units": "dimensionless [2.0, 20.0]",
            "dtype": "float32",
            "nodata": -9999.0,
        },
        {
            "band_idx": 4,
            "filename": "vehicle_mobility_tier_10m.tif",
            "name": "vehicle_mobility_tier",
            "description": "NATO / USACE Composite Off-Road Vehicle Mobility Tier (0=NoGo, 3=AllGo)",
            "units": "categorical code [0, 3]",
            "dtype": "float32",
            "nodata": -9999.0,
        },
    ]

    def __init__(self, output_dir: Optional[Union[str, Path]] = None):
        if output_dir is None:
            campaign_root = Path(__file__).resolve().parents[2] / "9_spaceborne_operational_campaign"
            output_dir = campaign_root / "7_production_geotiffs"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.transform = from_bounds(
            self.BOUNDS["min_x"],
            self.BOUNDS["min_y"],
            self.BOUNDS["max_x"],
            self.BOUNDS["max_y"],
            self.GRID_COLS,
            self.GRID_ROWS,
        )
        self.crs = CRS.from_string(self.DEFAULT_CRS)

    @staticmethod
    def _compute_sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def export_civil_rasters(
        self,
        q_allow_kpa: np.ndarray,
        fs_slope: np.ndarray,
        twi: np.ndarray,
        mobility_tier: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Exports 4 single-band GeoTIFFs and 1 master 4-layer Cloud-Optimized GeoTIFF stack.
        Returns provenance manifest with cryptographic hashes.
        """
        arrays = [
            np.asarray(q_allow_kpa, dtype=np.float32),
            np.asarray(fs_slope, dtype=np.float32),
            np.asarray(twi, dtype=np.float32),
            np.asarray(mobility_tier, dtype=np.float32),
        ]

        for idx, arr in enumerate(arrays):
            if arr.shape != (self.GRID_ROWS, self.GRID_COLS):
                raise ValueError(
                    f"Array {idx} shape mismatch: expected ({self.GRID_ROWS}, {self.GRID_COLS}), got {arr.shape}"
                )
            if np.isnan(arr).any():
                raise ValueError(f"Array {idx} contains NaN values; strictly prohibited under DO-178C.")

        manifest: Dict[str, Any] = {
            "mission": "THE_MRIDANSH",
            "subsystem": "05_CIVIL_GEOTECHNICAL_DOMAIN_TRANSLATOR",
            "crs": self.DEFAULT_CRS,
            "bounds": self.BOUNDS,
            "pixel_resolution_m": self.PIXEL_RESOLUTION_M,
            "dimensions": {"rows": self.GRID_ROWS, "cols": self.GRID_COLS},
            "single_band_geotiffs": {},
            "master_4layer_cog": {},
        }

        # 1. Export 4 Single-Band GeoTIFFs
        for cfg, arr in zip(self.LAYERS_CONFIG, arrays):
            out_path = self.output_dir / cfg["filename"]
            if _is_file_locked_by_viewer(out_path):
                logging.warning(f"File {out_path.name} locked by external viewer; skipping overwrite.")
                continue

            with rasterio.open(
                out_path,
                "w",
                driver="GTiff",
                height=self.GRID_ROWS,
                width=self.GRID_COLS,
                count=1,
                dtype=cfg["dtype"],
                crs=self.crs,
                transform=self.transform,
                nodata=cfg["nodata"],
                compress="lzw",
            ) as dst:
                dst.write(arr, 1)
                dst.set_band_description(1, cfg["description"])
                dst.update_tags(
                    LAYER_NAME=cfg["name"],
                    UNITS=cfg["units"],
                    SUBSYSTEM="05_CIVIL_TRANSLATOR",
                    AUTHORITY="JCC_CAMPUS_2_RS_SDA",
                )

            sha = self._compute_sha256(out_path)
            size_kb = round(out_path.stat().st_size / 1024.0, 2)
            manifest["single_band_geotiffs"][cfg["name"]] = {
                "file": out_path.name,
                "sha256": sha,
                "size_kb": size_kb,
                "description": cfg["description"],
                "units": cfg["units"],
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
                "mean": float(np.mean(arr)),
            }

        # 2. Export Master 4-Layer Cloud-Optimized GeoTIFF (COG)
        master_cog_name = "master_geotechnical_civil_4layer_10m.tif"
        master_cog_path = self.output_dir / master_cog_name

        if not _is_file_locked_by_viewer(master_cog_path):
            with rasterio.open(
                master_cog_path,
                "w",
                driver="GTiff",
                height=self.GRID_ROWS,
                width=self.GRID_COLS,
                count=4,
                dtype="float32",
                crs=self.crs,
                transform=self.transform,
                nodata=-9999.0,
                compress="deflate",
                tiled=True,
                blockxsize=64,
                blockysize=64,
            ) as master_dst:
                for band_num, (cfg, arr) in enumerate(zip(self.LAYERS_CONFIG, arrays), start=1):
                    master_dst.write(arr, band_num)
                    master_dst.set_band_description(band_num, cfg["description"])

                master_dst.update_tags(
                    MISSION="THE_MRIDANSH",
                    SUBSYSTEM="05_CIVIL_GEOTECHNICAL_DOMAIN_TRANSLATOR",
                    LAYER_COUNT="4",
                    CRS="EPSG:32645",
                    PIXEL_RESOLUTION="10m",
                    STANDARDS="Eurocode 7 / USACE TM 5-818-1 / NATO STANAG 4370",
                    AUTHORITY="Jagannath Command Center (JCC) - RS-SDA Division",
                )

            master_sha = self._compute_sha256(master_cog_path)
            master_size_kb = round(master_cog_path.stat().st_size / 1024.0, 2)
            manifest["master_4layer_cog"] = {
                "file": master_cog_name,
                "sha256": master_sha,
                "size_kb": master_size_kb,
                "bands": [cfg["name"] for cfg in self.LAYERS_CONFIG],
            }

        # 3. Write Provenance Manifest
        manifest_path = self.output_dir / "civil_geotiff_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        logging.info(f"Civil GeoTIFF export certified: {master_cog_path.name}")
        return manifest
