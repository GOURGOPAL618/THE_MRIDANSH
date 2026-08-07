# THE MRIDANSH - AGRONOMY TRANSLATOR

import logging
import numpy as np
from typing import Dict, Any
from .base import BaseDomainTranslator

logging.basicConfig(level = logging.INFO, format = "%(asctime)s - %(levelname)s - %(message)s")

class AgronomyHealthTranslator(BaseDomainTranslator):
    """Translates soil atate and spectral indices into agronomic decision vectors."""

    def translate(self, soil_moisture: np.ndarray, ndvi: np.ndarray = None) -> Dict[str, Any]:
        logging.info("🌾 Translating Soil State to Agronomy Health & Irrigation Vectors...")

        if ndvi is None:
            ndvi = np.full_like(soil_moisture, 0.65)   # Default average NDVI


        # 1. Crop Health Index Scorre (0-100%)
        health_score = np.clip((soil_moisture * 0.5 + ndvi * 0.5) * 100, 0, 100)

        # 2. Irrigation Deficit (Target Optimal Moisture = 0.35)
        optimal_moisture = 0.35
        moisture_deficit = np.maximum(0, optimal_moisture - soil_moisture)
        irrigation_liters_per_ha = moisture_deficit * 10000 * 10 # Liters per hectare estimation

        # 3. Drought Risk Level Classification
        mean_moisture = float(np.mean(soil_moisture))
        if mean_moisture < 0.15:
            drought_risk = "CRITICAL_DROUGHT"
        elif mean_moisture < 0.25:
            drought_risk = "MODERATE_STRESS"
        else:
            drought_risk = "OPTIMAL_HYDRATION"

        logging.info(
            f"✅ Agronomy Translation Complete!\n"
            f"   -> Mean Crop Health Score: {float(np.mean(health_score)):.2f}%\n"
            f"   -> Irrigation Needed: {float(np.mean(irrigation_liters_per_ha)):.2f} L/ha\n"
            f"   -> Regional Drought Risk: {drought_risk}"
        )

        return {
            "crop_health_matrix": health_score.astype(np.float32),
            "irrigation_required_l_ha": irrigation_liters_per_ha.astype(np.float32),
            "drought_risk_status": drought_risk,
            "mean_health_score": float(np.mean(health_score))
        }


# Self-Test Execution Module
if __name__ == "__main__":
    print("\n--- Testing Agronomy Health Translator Module ---")
    translator = AgronomyHealthTranslator()

    mock_moisture = np.random.uniform(0.12, 0.38, size = (120, 120)).astype(np.float32)
    mock_ndvi =  np.random.uniform(0.30, 0.85, size = (120, 120)).astype(np.float32)

    res = translator.translate(mock_moisture, mock_ndvi)
    assert "crop_health_matrix" in res and res["crop_health_matrix"].shape == (120, 120)
    print("\n[SUCCESS] Agronomy Translator: PASSED OPERATIONAL CHECKS!\n")