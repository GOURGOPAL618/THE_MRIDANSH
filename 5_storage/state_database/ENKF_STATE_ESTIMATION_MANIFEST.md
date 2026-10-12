# 🛰️ ENKF STATE ESTIMATION DATABASE MANIFEST
## Central Engine: AETHER-MRID1607X
* **Database File:** `enkf_state_database.pt`
* **Filter Type:** Stochastic Ensemble Kalman Filter (EnKF, Burgers et al. 1998)
* **State Dimension:** 4 Physical States (Root Moisture, Bulk Density, Hydraulic Conductivity, SOC)
* **Ensemble Size:** 50 Stochastic Members
* **Upstream Ingestion:** Notebook 02 (SAR Telemetry), Notebook 04 (ConvLSTM), Notebook 05 (PINN Loam Physics)
* **Prediction RMSE:** 0.0653 m3/m3
* **EnKF Posterior RMSE:** 0.0147 m3/m3
* **Error Reduction Rate:** 77.57% improvement over unconstrained prediction
* **Root Moisture Uncertainty Reduction:** 42.32%
* **Storage Location:** `d:\JAGANNATH_CODE_SANCTUM\JCC CAMPUS 2 (RS-SDA DIVISION)\THE_MRIDANSH\5_storage\state_database\enkf_state_database.pt`
* **Dual Persistence:** `d:\JAGANNATH_CODE_SANCTUM\JCC CAMPUS 2 (RS-SDA DIVISION)\THE_MRIDANSH\5_storage\notebook_results\notebook_06_state_estimation\enkf_state_database.pt` & `d:\JAGANNATH_CODE_SANCTUM\JCC CAMPUS 2 (RS-SDA DIVISION)\THE_MRIDANSH\data\processed\enkf_assimilation_bundle.pt`
* **Downstream Integration:** Consumed by Notebook 07 (Uncertainty Analysis & Monte Carlo Sensitivity)
