# 🛰️ THE MRIDANSH // CENTRAL ENGINE: AETHER-MRID1607X
## UNCERTAINTY QUANTIFICATION REGISTRY MANIFEST
**Storage Directory:** `5_storage/registry/`  
**Checkpoint File:** `uncertainty_registry.pt`  
**Architecture:** Orthogonal 4-Component Variance Decomposition (Ens + Sensor + Gap + Model)  
**Calibration Standard:** Nominal Gaussian Empirical Reliability (<2.0% Discrepancy)  

### Component Uncertainty Standard Deviations:
- Ensemble Spread Mean (Sigma_ens)   : 0.0310 m3/m3
- SAR Speckle Noise Mean (Sigma_sar) : 0.0130 m3/m3
- Cloud Contamination (Sigma_cloud)  : 0.0100 m3/m3
- Net Sensor Noise Mean (Sigma_sensor): 0.0187 m3/m3
- Temporal Latency Gap (Sigma_gap)   : 0.0123 m3/m3
- Input Availability (Sigma_avail)   : 0.0008 m3/m3
- Model Disagree Mean (Sigma_model)  : 0.0179 m3/m3
- Composite Total Mean (Sigma_total) : 0.0430 m3/m3
- Mapped Confidence Index Mean       : 52.63%

### Calibration & Reliability Proofs:
- High vs Low Confidence Error Monotonicity: CERTIFIED (Decile r = -0.9208)
- High Conf Tier MAE (0.0297) < Med (0.0351) < Low (0.0497)
- 1-Sigma Empirical Coverage: 67.32% (Nominal: 68.27% | Discrepancy: 0.95%)
- 2-Sigma Empirical Coverage: 95.32% (Nominal: 95.45% | Discrepancy: 0.13%)
- 3-Sigma Empirical Coverage: 99.76% (Nominal: 99.73% | Discrepancy: 0.03%)

### Downstream Ingestion Contract (Handoff to Notebook 08):
- Consumer Module: `1_notebooks_sandbox/08-robustness-and-failure-analysis.ipynb`
- Primary Checkpoint: `5_storage/registry/uncertainty_registry.pt`
- Downstream Role: Stress-testing edge cases, sensor dropouts, saturated boundary physics, and automated fail-soft triggers.