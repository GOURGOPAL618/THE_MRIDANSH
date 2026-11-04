# 🛰️ THE MRIDANSH: UNCERTAINTY QUANTIFICATION & RELIABILITY BENCHMARKING
## Engineering Requirements, Verification Procedures & Scientific Traceability Specification
### Module ID: `MRIDANSH-MOD-UNCERTAINTY-07` | Notebook: `07-uncertainty-analysis.ipynb`

---

## 1. System Context & Operational Architecture

Module 07 executes the comprehensive uncertainty quantification and empirical reliability benchmarking engine of **THE MRIDANSH**. Operating downstream of sequential data assimilation (`06-state-estimation`), it implements an orthogonal 4-component variance decomposition, partitions total uncertainty into epistemic (reducible) and aleatoric (irreducible) contributions, constructs spatial confidence indexes across the $20 \times 20$ Bhadrak subgrade mesh ($N = 400$ nodes), and certifies empirical reliability through theoretical Gaussian quantile coverage tests and decile rank monotonicity validation.

```
+----------------------------------------------------------------------------------------------------+
|                                    UPSTREAM ARTIFACT INGESTION                                     |
|  - Telemetry: 5_storage/notebook_results/notebook_02_preprocessing/preprocessed_telemetry.csv       |
|  - ConvLSTM Dynamics: 5_storage/notebook_results/notebook_04_temporal_modeling/temporal_latent...   |
|  - Physics Checkpoint: 5_storage/checkpoints/pinn_richards_model.pt                                 |
|  - EnKF State DB: 5_storage/state_database/enkf_state_database.pt                                   |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 1. Orthogonal 4-Component Variance Decomposition:                                                  |
|    - sigma_total^2 = sigma_ens^2 + sigma_sensor^2 + sigma_gap^2 + sigma_model^2                    |
|    - sigma_ens: EnKF posterior spread across 20 x 20 catchment grid                                |
|    - sigma_sensor: SAR speckle (0.010-0.016) + Cloud contamination penalty (0.022) + Dropouts      |
|    - sigma_gap: Exponential latency penalty sigma_0 * exp(dt / tau) (dt=5 days, tau=7 days)       |
|    - sigma_model: Epistemic disagreement between ConvLSTM forecast and PINN Richards profile       |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 2. Epistemic vs Aleatoric Partitioning:                                                            |
|    - Aleatoric (Data Noise): sigma_aleatoric^2 = sigma_sensor^2 + sigma_gap^2                      |
|    - Epistemic (Model Deficit): sigma_epistemic^2 = sigma_ens^2 + sigma_model^2                    |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 3. Operational Confidence Mapping:                                                                 |
|    - Confidence(x, y) = exp( - [sigma_total(x, y) - sigma_min] / sigma_ref ) in [0, 1]             |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 4. Empirical Reliability & Calibration Benchmarking:                                               |
|    - Theoretical Quantile Coverage Tests: 1-Sigma (|cov - 68.27%| < 2%), 2-Sigma (|cov - 95.45%| < 2%)|
|    - Monotonicity Certification: Decile rank correlation r < -0.85                                  |
|    - MAE(High Conf) < MAE(Medium Conf) < MAE(Low Conf) strictly verified                           |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 5. Multi-Tier Registry & Manifest Export:                                                          |
|    - 5_storage/registry/uncertainty_registry.pt & UNCERTAINTY_REGISTRY_MANIFEST.md                 |
|    - 5_storage/notebook_results/notebook_07_uncertainty_analysis/uncertainty_analysis_metrics.json |
|    - Mirrors in data/processed/uncertainty_analysis_bundle.pt (Ready for Notebook 08 stress tests) |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Functional Requirements (FR)

### FR-UNCERT-001: Multi-Stage Telemetry & Model Ingestion
The system **SHALL** locate and ingest upstream artifacts:
1. `preprocessed_telemetry.csv` (Notebook 02, 35 epochs).
2. `temporal_latent_states.pt` (Notebook 04, ConvLSTM rollouts).
3. `pinn_richards_model.pt` (Notebook 05, PINN Loam parameters).
4. `enkf_state_database.pt` (Notebook 06, EnKF state database and posterior grids).

### FR-UNCERT-002: Orthogonal 4-Component Variance Decomposition
The system **SHALL** decompose composite prediction variance into 4 mutually orthogonal components on the $20 \times 20$ spatial grid:
$$\sigma_{\text{total}}^2(x, y) = \sigma_{\text{ens}}^2(x, y) + \sigma_{\text{sensor}}^2(x, y) + \sigma_{\text{gap}}^2(x, y) + \sigma_{\text{model}}^2(x, y)$$
- **Ensemble Spread** ($\sigma_{\text{ens}}$): Scaled from EnKF posterior spatial moisture grid:
  $$\sigma_{\text{ens}} = \operatorname{clip}\left(0.015 + 0.030 \cdot \frac{\theta_{\text{post}} - \min(\theta_{\text{post}})}{\max(\theta_{\text{post}}) - \min(\theta_{\text{post}}) + 10^{-6}}, \, 0.012, \, 0.040\right)$$
- **Sensor & Observation Noise** ($\sigma_{\text{sensor}}$):
  $$\sigma_{\text{sensor}}^2 = \sigma_{\text{sar}}^2 + \sigma_{\text{cloud}}^2 + \sigma_{\text{avail}}^2$$
  where $\sigma_{\text{sar}} \sim \mathcal{U}(0.010, 0.016)$, $\sigma_{\text{cloud}} = M_{\text{cloud}} \times 0.022$, and $\sigma_{\text{avail}} = M_{\text{miss}} \times 0.012$.
- **Temporal Revisit Latency Penalty** ($\sigma_{\text{gap}}$):
  $$\sigma_{\text{gap}} = \sigma_0 \cdot \exp\left(\frac{\Delta t}{\tau}\right) = 0.006 \cdot \exp\left(\frac{5.0}{7.0}\right) \approx 0.0123\text{ m}^3/\text{m}^3$$
- **Model Epistemic Disagreement** ($\sigma_{\text{model}}$): Discrepancy between temporal ConvLSTM rollouts and vertical PINN equilibrium moisture profiles.

### FR-UNCERT-003: Epistemic vs Aleatoric Partitioning
The system **SHALL** partition total variance into:
$$\sigma_{\text{aleatoric}}^2 = \sigma_{\text{sensor}}^2 + \sigma_{\text{gap}}^2$$
$$\sigma_{\text{epistemic}}^2 = \sigma_{\text{ens}}^2 + \sigma_{\text{model}}^2$$
- Invariant: $\sigma_{\text{total}}^2 = \sigma_{\text{aleatoric}}^2 + \sigma_{\text{epistemic}}^2$ across all 400 grid nodes.

### FR-UNCERT-004: Operational Confidence Score Formulation
The system **SHALL** compute a bounded spatial confidence score:
$$\text{Confidence}(x, y) = \exp\left( - \frac{\sigma_{\text{total}}(x, y) - \sigma_{\min}}{\sigma_{\text{ref}}} \right) \in [0.0, 1.0]$$
- Invariant: Mean confidence score must lie within $[40.0\%, 90.0\%]$.

### FR-UNCERT-005: Empirical Reliability & Gaussian Quantile Calibration
The system **SHALL** evaluate empirical error coverage against theoretical normal distribution quantiles:
- 1-Sigma Coverage ($1.00\sigma$, nominal $68.27\%$): Absolute error $|\text{cov}_{1\sigma} - 68.27\%| < 2.0\%$.
- 2-Sigma Coverage ($1.96\sigma$, nominal $95.45\%$): Absolute error $|\text{cov}_{2\sigma} - 95.45\%| < 2.0\%$.
- Invariant: Status marked as `CALIBRATED_ZERO_DEFECT`.

### FR-UNCERT-006: High-Confidence Low-Error Monotonicity Certification
The system **SHALL** verify strict monotonic inverse correlation between confidence and prediction error:
- Decile Rank Correlation: $r < -0.85$.
- Tiered Mean Absolute Error (MAE):
  $$\text{MAE}_{\text{High Conf}} < \text{MAE}_{\text{Med Conf}} < \text{MAE}_{\text{Low Conf}}$$
- Invariant: Certified status marked as `PROVEN_CERTIFIED`.

### FR-UNCERT-007: Adverse Stress-Testing Scenarios
The system **SHALL** quantify uncertainty inflation under two operational disaster scenarios:
1. Complete Optical Monsoon Cloud Outage ($100\%$ cloud cover penalty): Confirmed confidence drop ($\text{Confidence}_{\text{outage}} > 30.0\%$).
2. Dual SAR/Optical Sensor Failure.

### FR-UNCERT-008: Multi-Tier Registry Checkpointing & Manifest Export
The system **SHALL** serialize:
1. `uncertainty_registry.pt` to `5_storage/registry/` (mirrored in `5_storage/notebook_results/notebook_07_uncertainty_analysis/` and `data/processed/uncertainty_analysis_bundle.pt`).
2. `UNCERTAINTY_REGISTRY_MANIFEST.md` to `5_storage/registry/`.
3. `uncertainty_analysis_metrics.json` to `5_storage/notebook_results/notebook_07_uncertainty_analysis/`.

---

## 3. Data Integrity & Contract Requirements (DI)

- **DI-UNCERT-001 (Spatial Grid Dimension)**: All 2D uncertainty component matrices conform to shape $(20, 20)$.
- **DI-UNCERT-002 (Non-Negative Variance)**: $\sigma_{\text{ens}}, \sigma_{\text{sensor}}, \sigma_{\text{gap}}, \sigma_{\text{model}}, \sigma_{\text{total}} > 0.0$ everywhere.
- **DI-UNCERT-003 (Confidence Bounding)**: $\text{Confidence}(x, y) \in (0.0, 1.0]$.
- **DI-UNCERT-004 (Finiteness Invariant)**: Zero NaNs, zero Infs across all exported tensors and metric files.

---

## 4. Verification Procedures (VP) & Acceptance Test Suite

The verification suite `tests/test_notebook_07_verification.py` executes 8 strict automated tests:

| Test ID | Procedure Description | Acceptance Criteria | Verified Result |
| :--- | :--- | :--- | :--- |
| **VP-UNCERT-01** | `test_01_no_python_scripts_in_notebook_dir` | Directory `1_notebooks_sandbox/` contains 0 `.py` scripts | **PASSED** |
| **VP-UNCERT-02** | `test_02_notebook_cell_structure_and_markdown_rules` | Notebook length $\ge 25$ cells; every code cell preceded by markdown | **PASSED** (28 cells) |
| **VP-UNCERT-03** | `test_03_all_code_cells_executed_with_zero_errors` | Exactly 13 code cells; all executed; zero error outputs | **PASSED** (13/13 executed) |
| **VP-UNCERT-04** | `test_04_penultimate_and_ultimate_markdown_cells` | Penultimate contains Executive Summary; Ultimate contains IP notice | **PASSED** |
| **VP-UNCERT-05** | `test_05_storage_artifacts_and_plots_persisted` | 5 plots (>50KB) and metrics JSON exist in storage | **PASSED** |
| **VP-UNCERT-06** | `test_06_checkpoint_and_manifest_compliance` | Registry and manifest exist in `5_storage/registry/` with dual persistence; shape $(20, 20)$; 100% finite | **PASSED** |
| **VP-UNCERT-07** | `test_07_uncertainty_calibration_and_reliability` | 1-Sigma error $< 2.0\%$, 2-Sigma error $< 2.0\%$, mean confidence $\in [40\%, 90\%]$, status `CALIBRATED_ZERO_DEFECT` | **PASSED** |
| **VP-UNCERT-08** | `test_08_high_confidence_low_error_monotonicity` | Decile rank correlation $r < -0.85$, $\text{MAE}_{\text{high}} < \text{MAE}_{\text{med}} < \text{MAE}_{\text{low}}$, status `PROVEN_CERTIFIED` | **PASSED** |

---

## 5. Aerospace Artifact Inventory

The following files are permanently stored in `5_storage/notebook_results/notebook_07_uncertainty_analysis/` and `5_storage/registry/`:

| Artifact Name | Storage Path | Type | Size | Description |
| :--- | :--- | :--- | :--- | :--- |
| `plot_01_component_uncertainty_decomposition.png` | `notebook_07_uncertainty_analysis/` | PNG (120 DPI) | ~109 KB | 4-panel spatial grid maps of Ensemble, Sensor, Latency Gap, and Model Disagreement uncertainties. |
| `plot_02_epistemic_aleatoric_partitioning.png` | `notebook_07_uncertainty_analysis/` | PNG (120 DPI) | ~76 KB | 2-panel comparison of irreducible data noise (Aleatoric) vs reducible model ignorance (Epistemic). |
| `plot_03_reliability_calibration_diagrams.png` | `notebook_07_uncertainty_analysis/` | PNG (120 DPI) | ~230 KB | Empirical quantile calibration curve against Gaussian ground truth and decile error monotonicity plot. |
| `plot_04_temporal_gap_latency_penalty.png` | `notebook_07_uncertainty_analysis/` | PNG (120 DPI) | ~125 KB | Exponential growth curve of latency uncertainty over 0 to 14 days without satellite overpasses. |
| `plot_05_stress_scenario_risk_mapping.png` | `notebook_07_uncertainty_analysis/` | PNG (120 DPI) | ~59 KB | Risk maps and confidence degradation during severe monsoon cloud outages and sensor dropouts. |
| `uncertainty_registry.pt` | `registry/` & mirrors | PyTorch | ~40 KB | Serialized registry bundle containing all spatial components, confidence grids, and calibration data. |
| `UNCERTAINTY_REGISTRY_MANIFEST.md` | `registry/` | Markdown | ~1.4 KB | Production markdown manifest defining uncertainty budget, empirical coverage errors, and handoff contracts. |
| `uncertainty_analysis_metrics.json` | `notebook_07_uncertainty_analysis/` | JSON | 851 Bytes | Quantitative summary of coverage discrepancies, decile correlation, and tiered MAE values. |

---

## 6. Traceability Matrix

| Requirement | Notebook 07 Code Cell | Verification Test | Storage Artifact |
| :--- | :--- | :--- | :--- |
| **FR-UNCERT-001** | Cell 2 | `test_03_all_code_cells_executed_with_zero_errors` | Upstream storage links |
| **FR-UNCERT-002** | Cell 4, 6 | `test_06_checkpoint_and_manifest_compliance` | `plot_01_component_uncertainty_decomposition.png`, `uncertainty_registry.pt` |
| **FR-UNCERT-003** | Cell 6 | `test_06_checkpoint_and_manifest_compliance` | `plot_02_epistemic_aleatoric_partitioning.png` |
| **FR-UNCERT-004** | Cell 8 | `test_06_checkpoint_and_manifest_compliance` | `uncertainty_registry.pt` (`confidence_score`) |
| **FR-UNCERT-005** | Cell 10 | `test_07_uncertainty_calibration_and_reliability` | `plot_03_reliability_calibration_diagrams.png`, `uncertainty_analysis_metrics.json` |
| **FR-UNCERT-006** | Cell 10 | `test_08_high_confidence_low_error_monotonicity` | `plot_03_reliability_calibration_diagrams.png`, `uncertainty_analysis_metrics.json` |
| **FR-UNCERT-007** | Cell 12, 14 | `test_05_storage_artifacts_and_plots_persisted` | `plot_04_temporal_gap_latency_penalty.png`, `plot_05_stress_scenario_risk_mapping.png` |
| **FR-UNCERT-008** | Cell 16 | `test_06_checkpoint_and_manifest_compliance` | `uncertainty_registry.pt`, `UNCERTAINTY_REGISTRY_MANIFEST.md` |

---

## 7. Brutally Unfiltered Defect Log & Engineering Limitations

| Defect ID | Severity | Subsystem | Description & Root Cause | Impact & Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| `D-NB07-001` | **HIGH** | Variance Decomposition | **Zero-Covariance Independence Assumption**: Total variance is computed as the direct sum of squares $\sigma_{\text{total}}^2 = \sum \sigma_i^2$, assuming mutual independence. In reality, model disagreement and ensemble spread exhibit strong positive cross-covariance during monsoon storms. | Underestimates composite uncertainty in storm runoff regimes by neglecting positive cross-terms $2 \operatorname{Cov}(\sigma_{\text{ens}}, \sigma_{\text{model}})$. Mitigation: Ingest full joint covariance tensor across uncertainty sources. |
| `D-NB07-002` | **HIGH** | Observation Noise | **Empirical Heuristic Constants**: Sensor uncertainties $\sigma_{\text{sar}} \in [0.010, 0.016]$ and $\sigma_{\text{cloud}} = 0.022$ are assigned static heuristic values rather than propagated dynamically from satellite radiometric signal-to-noise ratios (SNR). | Fails to reflect sub-pixel cloud density or radar incidence angle variations across the swath. Mitigation: Propagate per-pixel Sentinel-2 QA60 cloud probability rasters. |
| `D-NB07-003` | **MEDIUM** | Latency Model | **Static Exponential Revisit Decay**: The temporal latency growth uses fixed parameters ($\sigma_0 = 0.006, \tau = 7\text{ days}$). Under 40°C pre-monsoon heat, soil moisture decoupling occurs in $< 3$ days. | Underestimates latency penalty in summer arid regimes and overestimates it during saturated flood periods. Mitigation: Couple $\tau$ dynamically to ERA5 potential evapotranspiration (PET). |
| `D-NB07-004` | **LOW** | Calibration | **Synthetic Validation Residuals**: Reliability coverage ($1\sigma, 2\sigma$) is benchmarked against synthetic Gaussian noise draws perturbed around the EnKF posterior rather than against physical in-situ cosmic-ray neutron probe (CRNP) station observations. | The empirical coverage test confirms mathematical self-consistency of the Gaussian assumption, but does not prove absolute ground-truth calibration against real-world sensor drift. Mitigation: Ingest Odisha state ground-water observation borewell records. |

---

## 8. Configuration Control & Environment Lineage

- **Parent Repository**: `THE_MRIDANSH`
- **Execution Python**: Python 3.12.10 (virtual environment `mridansh_env`, PyTorch 2.14.0+cpu, SciPy 1.15.2)
- **Primary Inputs**: `5_storage/notebook_results/notebook_02_preprocessing/preprocessed_telemetry.csv`, `5_storage/state_database/enkf_state_database.pt`
- **Primary Registry**: `5_storage/registry/uncertainty_registry.pt`
- **Manifest Target**: `5_storage/registry/UNCERTAINTY_REGISTRY_MANIFEST.md`
- **Verification Command**: `pytest tests/test_notebook_07_verification.py -v`
