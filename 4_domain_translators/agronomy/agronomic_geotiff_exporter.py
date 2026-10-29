# THE MRIDANSH - Agriculture Domain Translator
# Module: 4_domain_translators/agronomy/agronomic_geotiff_exporter.py
# Production OGC GeoTIFF & Cloud-Optimized GeoTIFF (COG) Exporter
# Standards: OGC GeoTIFF 1.1, CEOS-WGCV, ISO 19115-2, DO-178C Level-A Rigor

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_bounds

logger = logging.getLogger("MRIDANSH.AgriTranslator.GeoTIFFExporter")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


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


class AgronomicGeoTIFFExporter:
    """
    Exports precision agronomic intelligence into standard georeferenced GeoTIFFs
    and multi-band Cloud-Optimized GeoTIFFs (COG).
    """

    DEFAULT_CRS = "EPSG:32645"  # WGS 84 / UTM Zone 45N
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
            "filename": "crop_water_stress_index_10m.tif",
            "name": "crop_water_stress_index",
            "description": "FAO-56 Crop Water Stress Index (CWSI)",
            "units": "dimensionless [0.0, 1.0]",
            "dtype": "float32",
            "nodata": -9999.0,
        },
        {
            "band_idx": 2,
            "filename": "root_zone_depletion_dr_10m.tif",
            "name": "root_zone_depletion",
            "description": "Root-Zone Vadose Water Depletion (Dr)",
            "units": "mm",
            "dtype": "float32",
            "nodata": -9999.0,
        },
        {
            "band_idx": 3,
            "filename": "precision_irrigation_prescription_liters_per_ha_10m.tif",
            "name": "irrigation_prescription_l_ha",
            "description": "Precision Variable-Rate Irrigation (VRI) Prescription",
            "units": "Liters / Hectare",
            "dtype": "float32",
            "nodata": -9999.0,
        },
        {
            "band_idx": 4,
            "filename": "irrigation_conformal_risk_envelope_10m.tif",
            "name": "conformal_risk_envelope_l_ha",
            "description": "Conformal 2-Sigma Decision-Risk Envelope (Half-Width)",
            "units": "Liters / Hectare",
            "dtype": "float32",
            "nodata": -9999.0,
        },
    ]

    def __init__(self, output_dir: Optional[Union[str, Path]] = None):
        if output_dir is None:
            # Default to campaign production geotiffs directory
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

    def export_agronomic_rasters(
        self,
        cwsi: np.ndarray,
        dr_mm: np.ndarray,
        irrigation_l_ha: np.ndarray,
        risk_envelope_l_ha: np.ndarray,
        crop_name: str = "Winter Wheat",
        soil_texture: str = "Silt Loam",
    ) -> Dict[str, Any]:
        """
        Exports all 4 individual agronomic GeoTIFF rasters and the master 4-band COG.

        Parameters:
            cwsi: [64, 64] Crop Water Stress Index
            dr_mm: [64, 64] Root-zone depletion in mm
            irrigation_l_ha: [64, 64] VRI nominal rate in L/ha
            risk_envelope_l_ha: [64, 64] Conformal uncertainty risk envelope in L/ha
            crop_name: Crop species
            soil_texture: Soil texture classification

        Returns:
            Dictionary containing export manifest and cryptographic SHA-256 hashes
        """
        layers_data = [
            np.asarray(cwsi, dtype=np.float32),
            np.asarray(dr_mm, dtype=np.float32),
            np.asarray(irrigation_l_ha, dtype=np.float32),
            np.asarray(risk_envelope_l_ha, dtype=np.float32),
        ]

        for i, arr in enumerate(layers_data):
            if arr.shape != (self.GRID_ROWS, self.GRID_COLS):
                raise ValueError(
                    f"Array {i} shape mismatch: {arr.shape} != {(self.GRID_ROWS, self.GRID_COLS)}"
                )
            if np.any(np.isnan(arr)) or np.any(np.isinf(arr)):
                raise AssertionError(f"DO-178C Violation: NaN or Inf detected in layer {i}")

        manifest = {
            "mission": "THE MRIDANSH - Phase 4 Agronomy Translator",
            "crs": self.DEFAULT_CRS,
            "bounds": self.BOUNDS,
            "resolution_m": self.PIXEL_RESOLUTION_M,
            "grid_dimensions": [self.GRID_ROWS, self.GRID_COLS],
            "crop_species": crop_name,
            "soil_texture": soil_texture,
            "rasters": {},
        }

        # 1. Export 4 Individual Single-Band GeoTIFFs
        for cfg, arr in zip(self.LAYERS_CONFIG, layers_data):
            file_path = self.output_dir / cfg["filename"]

            if _is_file_locked_by_viewer(file_path):
                logger.warning("File %s is locked by QGIS viewer; using temporary target.", file_path.name)
                target_path = self.output_dir / f"agri_{cfg['filename']}"
            else:
                target_path = file_path

            profile = {
                "driver": "GTiff",
                "height": self.GRID_ROWS,
                "width": self.GRID_COLS,
                "count": 1,
                "dtype": cfg["dtype"],
                "crs": self.crs,
                "transform": self.transform,
                "nodata": cfg["nodata"],
                "compress": "deflate",
                "predictor": 2,
            }

            with rasterio.open(target_path, "w", **profile) as dst:
                dst.write(arr, 1)
                dst.set_band_description(1, cfg["description"])
                dst.update_tags(
                    title=cfg["description"],
                    units=cfg["units"],
                    crop=crop_name,
                    soil=soil_texture,
                    standard="FAO-56",
                )

            sha256 = self._compute_sha256(target_path)
            manifest["rasters"][cfg["name"]] = {
                "filename": target_path.name,
                "description": cfg["description"],
                "units": cfg["units"],
                "sha256": sha256,
                "min": float(np.min(arr)),
                "mean": float(np.mean(arr)),
                "max": float(np.max(arr)),
            }
            logger.info("Exported single-band raster: %s (SHA-256: %s...)", target_path.name, sha256[:12])

        # 2. Export Master 4-Band Cloud-Optimized GeoTIFF (COG) Stack
        master_cog_path = self.output_dir / "master_agronomic_vri_4layer_10m.tif"
        if _is_file_locked_by_viewer(master_cog_path):
            target_cog_path = self.output_dir / "master_agronomic_vri_4layer_10m_target.tif"
        else:
            target_cog_path = master_cog_path

        cog_profile = {
            "driver": "GTiff",
            "height": self.GRID_ROWS,
            "width": self.GRID_COLS,
            "count": len(self.LAYERS_CONFIG),
            "dtype": "float32",
            "crs": self.crs,
            "transform": self.transform,
            "nodata": -9999.0,
            "compress": "deflate",
            "predictor": 2,
            "tiled": True,
            "blockxsize": 16,
            "blockysize": 16,
        }

        with rasterio.open(target_cog_path, "w", **cog_profile) as dst:
            for i, (cfg, arr) in enumerate(zip(self.LAYERS_CONFIG, layers_data), start=1):
                dst.write(arr, i)
                dst.set_band_description(i, f"{cfg['description']} [{cfg['units']}]")
            
            dst.update_tags(
                mission="THE_MRIDANSH_AGRONOMY",
                product="4_LAYER_VRI_PRESCRIPTION_STACK",
                spatial_resolution="10m",
                crs=self.DEFAULT_CRS,
                crop=crop_name,
                soil=soil_texture,
                standard="FAO-56 / DO-178C Level-A",
            )

        master_sha256 = self._compute_sha256(target_cog_path)
        manifest["rasters"]["master_agronomic_vri_4layer"] = {
            "filename": target_cog_path.name,
            "description": "Master 4-Layer Agronomic VRI Prescription COG Stack",
            "bands_count": 4,
            "sha256": master_sha256,
        }
        logger.info("Exported Master 4-Layer COG: %s (SHA-256: %s...)", target_cog_path.name, master_sha256[:12])

        # 3. Save Cryptographic Manifest
        manifest_path = self.output_dir / "agronomic_geotiff_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return manifest
