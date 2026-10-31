# THE MRIDANSH - CIVIL & GEOTECHNICAL DOMAIN TRANSLATOR
# Module: 4_domain_translators/civil/drainage_intelligence.py
# Subsystem 05 of AETHER-MRID1607X Core Engine
# Architecture: Hydrological Routing, Topographic Wetness Index (TWI) & Runoff Conduit Engine
# Standards: Beven-Kirkby (1979) / Moore et al. (1991) Terrain Hydrology

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Tuple, Union

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

EPSILON_SLOPE: float = 1e-4  # Singularity guard for flat plateaus
DEFAULT_PIXEL_SPACING_M: float = 10.0  # 10m Sentinel/Copernicus raster grid


@dataclass(frozen=True)
class DrainageIntelligenceResult:
    """Telemetry result of topographic drainage routing and runoff analysis."""
    flow_direction_azimuth_deg: np.ndarray    # Compass flow direction (0°-360°)
    topographic_wetness_index: np.ndarray     # Continuous TWI = ln(a / tan(beta))
    runoff_flow_paths_mask: np.ndarray        # High-energy channel conduits
    water_accumulation_zones_mask: np.ndarray # Sinks, flat basins & pooling zones
    waterlogging_hazard_mask: np.ndarray      # Accumulation zones coupled with high moisture
    slope_angle_deg: np.ndarray               # Surface slope beta
    mean_twi: float
    accumulation_area_pct: float
    channel_density_pct: float
    waterlogging_hazard_pct: float


class DrainageIntelligenceEngine:
    """
    Evaluates topographic runoff dynamics, drainage flow conduits, and water accumulation
    basins by coupling digital elevation models (DEM) with hydrological transport physics.
    """

    def __init__(
        self,
        cell_size_m: float = DEFAULT_PIXEL_SPACING_M,
        flat_slope_threshold_deg: float = 1.5,
        twi_accumulation_percentile: float = 75.0,
    ):
        self.cell_size_m = float(cell_size_m)
        self.flat_slope_deg = float(flat_slope_threshold_deg)
        self.twi_percentile = float(twi_accumulation_percentile)
        if self.cell_size_m <= 0.0:
            raise ValueError(f"Cell size must be positive, got {self.cell_size_m}")

    def compute_terrain_gradients(self, dem: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculates 2D central spatial gradients dz/dx, dz/dy and surface slope angle beta.
        Uses Horn-style spatial difference convolution.
        Supports 2D (H, W) or multi-channel 3D (C, H, W) where Channel 0 is elevation.
        """
        z = np.asarray(dem, dtype=np.float64)
        if z.ndim == 3:
            z = z[0]  # Extract elevation band from multi-channel raster
        elif z.ndim != 2:
            raise ValueError(f"DEM must be 2D (H, W) or 3D (C, H, W), got shape {z.shape}")

        # Compute gradient dz/dx (columns, East-West) and dz/dy (rows, North-South)
        dz_dy, dz_dx = np.gradient(z, self.cell_size_m, self.cell_size_m)

        # Slope gradient: tan(beta) = sqrt( (dz/dx)^2 + (dz/dy)^2 )
        tan_beta = np.sqrt(dz_dx**2 + dz_dy**2)
        slope_rad = np.arctan(tan_beta)
        slope_deg = np.degrees(slope_rad)

        return dz_dx, dz_dy, slope_deg

    def compute_runoff_flow_direction(
        self, dz_dx: np.ndarray, dz_dy: np.ndarray
    ) -> np.ndarray:
        """
        Derives downhill runoff flow direction azimuth in compass degrees [0°, 360°):
        0° = North, 90° = East, 180° = South, 270° = West.
        Water flows in the direction of steepest descent (-dz/dx, -dz/dy).
        """
        # Downhill gradient components
        down_x = -dz_dx
        down_y = -dz_dy

        # Mathematical angle from positive X (East) counterclockwise
        # In grid coordinates: down_y > 0 means flowing South (increasing row index)
        # down_x > 0 means flowing East (increasing col index)
        # Compass azimuth: 0° North (down_y < 0, down_x = 0), 90° East (down_y = 0, down_x > 0)
        azimuth_rad = np.arctan2(down_x, -down_y)
        azimuth_deg = np.degrees(azimuth_rad)

        # Normalize to [0, 360)
        azimuth_deg = np.mod(azimuth_deg + 360.0, 360.0)

        # Zero gradient clamp: flat zones default to 0.0°
        flat_mask = np.sqrt(dz_dx**2 + dz_dy**2) < 1e-6
        azimuth_deg[flat_mask] = 0.0

        return azimuth_deg

    def compute_specific_catchment_area(
        self, dz_dx: np.ndarray, dz_dy: np.ndarray
    ) -> np.ndarray:
        """
        Estimates specific contributing catchment area 'a' (m^2 / m = m).
        Uses convergent flow routing proxy where flow accumulates downhill along local curvature.
        """
        h, w = dz_dx.shape
        gradient_mag = np.sqrt(dz_dx**2 + dz_dy**2)

        # Divergence of gradient (Laplacian of elevation: nabla^2 z)
        # Negative Laplacian means valley/concave hollow (convergent flow accumulating water)
        # Positive Laplacian means ridge/convex peak (divergent flow shedding water)
        d2z_dy2, _ = np.gradient(dz_dy, self.cell_size_m, self.cell_size_m)
        _, d2z_dx2 = np.gradient(dz_dx, self.cell_size_m, self.cell_size_m)
        laplacian = d2z_dx2 + d2z_dy2

        # Concavity proxy: concave zones have higher catchment convergence
        concavity = np.maximum(0.0, -laplacian) * (self.cell_size_m ** 2)
        
        # Base contributing area: each cell contributes its own width (cell_size_m)
        # Valleys receive convergent accumulation
        specific_area = self.cell_size_m * (1.0 + np.log1p(concavity / 10.0))

        return np.maximum(self.cell_size_m, specific_area)

    def analyze_drainage(
        self,
        dem: np.ndarray,
        theta_soil: Optional[np.ndarray] = None,
    ) -> DrainageIntelligenceResult:
        """
        Executes end-to-end drainage intelligence pipeline:
        1. Terrain slope & spatial gradients
        2. Runoff flow direction azimuth (0°-360°)
        3. Beven-Kirkby Topographic Wetness Index (TWI)
        4. Primary flow conduit paths
        5. Water accumulation & ponding depression zones
        6. Subgrade waterlogging hazard mapping
        """
        z = np.asarray(dem, dtype=np.float64)
        dz_dx, dz_dy, slope_deg = self.compute_terrain_gradients(z)
        flow_azimuth = self.compute_runoff_flow_direction(dz_dx, dz_dy)

        # Topographic Wetness Index (TWI): TWI = ln(a / tan(beta))
        tan_beta = np.tan(np.radians(slope_deg))
        safe_tan_beta = np.maximum(tan_beta, EPSILON_SLOPE)
        catchment_area = self.compute_specific_catchment_area(dz_dx, dz_dy)
        
        twi = np.log(catchment_area / safe_tan_beta)
        # Numerical guard: clamp TWI to realistic natural bounds [2.0, 20.0]
        twi = np.clip(twi, 2.0, 20.0)

        # Water accumulation zones: flat terrain (slope <= flat_slope_deg) AND high TWI
        twi_thresh = float(np.percentile(twi, self.twi_percentile))
        accumulation_mask = np.logical_and(slope_deg <= self.flat_slope_deg, twi >= twi_thresh)

        # Runoff flow conduits: high stream power proxy (catchment_area * tan(beta))
        stream_power = catchment_area * tan_beta
        conduit_thresh = float(np.percentile(stream_power, 85.0))
        flow_paths_mask = stream_power >= conduit_thresh

        # Waterlogging hazard: accumulation zone coupled with high spaceborne soil moisture
        if theta_soil is not None:
            theta_arr = np.asarray(theta_soil, dtype=np.float64)
            waterlogging_mask = np.logical_and(accumulation_mask, theta_arr >= 0.35)
        else:
            waterlogging_mask = accumulation_mask.copy()

        total_px = float(z.size)
        pct_accum = float(np.sum(accumulation_mask) / total_px * 100.0)
        pct_channel = float(np.sum(flow_paths_mask) / total_px * 100.0)
        pct_waterlogging = float(np.sum(waterlogging_mask) / total_px * 100.0)

        return DrainageIntelligenceResult(
            flow_direction_azimuth_deg=flow_azimuth.astype(np.float32),
            topographic_wetness_index=twi.astype(np.float32),
            runoff_flow_paths_mask=flow_paths_mask,
            water_accumulation_zones_mask=accumulation_mask,
            waterlogging_hazard_mask=waterlogging_mask,
            slope_angle_deg=slope_deg.astype(np.float32),
            mean_twi=float(np.mean(twi)),
            accumulation_area_pct=pct_accum,
            channel_density_pct=pct_channel,
            waterlogging_hazard_pct=pct_waterlogging,
        )
