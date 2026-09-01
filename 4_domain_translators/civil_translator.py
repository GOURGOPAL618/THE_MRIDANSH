# THE MRIDANSH - CIVIL TRANSLATOR

import logging
from typing import Any

import numpy as np

from .base import BaseDomainTranslator

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class CivilLoadTranslator(BaseDomainTranslator):
    """Translates Soil States into soil mechanical bearing capacity and civil engineering stability vectors."""

    def translate(
        self, soil_moisture: np.ndarray, dry_density_g_cm3: float = 1.6
    ) -> dict[str, Any]:
        logging.info(
            "🏗️ Translating Soil State to Civil Bearing Capacity & Shear Strength..."
        )

        # 1. Soil Cohesion & shear strength reduction with saturation
        saturation_ratio = np.clip(soil_moisture / 0.45, 0.0, 1.0)
        baseline_cohesion_kpa = 35.0  # Baseline dry cohesion (kPa)

        # Effective cohension reduces as moisture increases
        effective_cohesion = baseline_cohesion_kpa * (1.0 - 0.6 * saturation_ratio)

        #  2. Allowable Bearing Capacity (Terzaghi - like Simplification) (kPa)
        bearing_capacity_kpa = effective_cohesion * 5.7 + (
            dry_density_g_cm3 * 9.81 * 1.5
        )

        # 3. Heavy Machinery Trafficability Classification
        mean_bearing = float(np.mean(bearing_capacity_kpa))
        if mean_bearing > 180.0:
            trafficability = "HEAVY_RIG_PERMITTED"
        elif mean_bearing > 120.0:
            trafficability = "LIGHT_VEHICLE_ONLY"
        else:
            trafficability = "HAZARDOUS_UNSTABLE_SOIL"

        logging.info(
            f"✅ Civil Engineering Translation Complete!\n"
            f"   -> Mean Bearing Capacity: {mean_bearing:.2f} kPa\n"
            f"   -> Shear Cohesion: {float(np.mean(effective_cohesion)):.2f} kPa\n"
            f"   -> Site Trafficability Grade: {trafficability}"
        )

        return {
            "bearing_capacity_matrix_kPa": bearing_capacity_kpa.astype(np.float32),
            "effective_cohesion_kPa": effective_cohesion.astype(np.float32),
            "site_trafficability": trafficability,
            "mean_bearing_kPa": mean_bearing,
        }


# Self-Test Execution Module
if __name__ == "__main__":
    print("\n--- Testing Civil Load Translator Module ---")
    translator = CivilLoadTranslator()

    mock_moisture = np.random.uniform(0.15, 0.40, size=(120, 120)).astype(np.float32)
    res = translator.translate(mock_moisture)

    assert "bearing_capacity_matrix_kPa" in res and res[
        "bearing_capacity_matrix_kPa"
    ].shape == (120, 120)
    print("\n[SUCCESS] Civil Translator: PASSED OPERATIONAL CHECKS!\n")
