# 🛰️ THE MRIDANSH: TEMPORAL SEQUENCE MODELING & CONVLSTM ENGINE
## Engineering Requirements, Verification Procedures & Scientific Traceability Specification
### Module ID: `MRIDANSH-MOD-TEMPORAL-04` | Notebook: `04-temporal-modeling.ipynb`

---

## 1. System Context & Operational Architecture

Module 04 implements the spatio-temporal dynamics engine of **THE MRIDANSH**. Ingesting preprocessed multi-sensor telemetry from `02-preprocessing` and topographical graph parameters from `03-spatial-modeling`, this engine constructs 5D spatio-temporal data cubes $(B, T, C, H, W)$, trains a 2D Spatial-Temporal Convolutional LSTM (`SpatialTemporalConvLSTM`), benchmarks temporal lookback horizon sensitivity ($T \in \{3, 5, 7, 10\}$), and validates multi-step autoregressive rollout stability over hydrological recession windows.

```
+----------------------------------------------------------------------------------------------------+
|                                    UPSTREAM ARTIFACT INGESTION                                     |
|  - Telemetry: 5_storage/notebook_results/notebook_02_preprocessing/preprocessed_telemetry.csv       |
|  - Spatial Mesh: 5_storage/notebook_results/notebook_03_spatial_modeling/spatial_graph_mesh.npz    |
|  - Spatial Embeddings: 5_storage/.../notebook_03_spatial_modeling/spatial_gcn_embeddings.pt        |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 1. 5D Spatio-Temporal Tensor Construction:                                                          |
|    - Sliding window (seq_len T=5, target_lead=1) over 35 temporal epochs                           |
|    - 2D Topographic modulation: DEM elevation & slope applied to 1D telemetry vectors               |
|    - Dimensions: X in R^(30 x 5 x 2 x 20 x 20), Y in R^(30 x 1 x 2 x 20 x 20)                       |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 2. Chronological Train-Test Split (80/20):                                                         |
|    - Training Batch: B_train = 24 sequences (t in [0, 23])                                         |
|    - Test Batch: B_test = 6 sequences (t in [24, 29])                                              |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 3. ConvLSTM Recurrent Architecture:                                                                |
|    - ConvLSTMCell: Cin=2, Chidden=16, 3x3 kernel, circular/reflect padding                         |
|    - Unified 4-gate convolution: Conv2d(in=18, out=64, kernel=3, padding=1)                        |
|    - Output Head: Conv2d(16, 8, 3) -> ReLU -> Conv2d(8, 2, 1)                                      |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 4. Optimization & Convergence (25 Epochs):                                                         |
|    - Loss: Mean Squared Error (MSE) on predicted next-frame spatial field                           |
|    - Optimizer: Adam (lr=1e-3), Gradient Clipping (max_norm=1.0)                                   |
|    - Loss Reduction > 10.0% verified across training window                                        |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 5. Temporal Lookback Ablation & Autoregressive Rollout:                                            |
|    - Horizon Sweep: T in {3, 5, 7, 10}; confirms long-term memory benefit                           |
|    - 5-step recursive closed-loop autoregressive rollout for hydrological recession                 |
|    - Recurrent hidden state extraction: h_final in R^(6 x 16 x 20 x 20)                            |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 6. Dual Storage Export:                                                                            |
|    - 5_storage/notebook_results/notebook_04_temporal_modeling/convlstm_model_init.pt               |
|    - 5_storage/notebook_results/notebook_04_temporal_modeling/temporal_latent_states.pt             |
|    - 5_storage/notebook_results/notebook_04_temporal_modeling/temporal_sequence_ablation.json      |
|    - Mirrors in data/processed/                                                                    |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Functional Requirements (FR)

### FR-TEMPORAL-001: Upstream Ingestion Integrity
The system **SHALL** locate and ingest:
1. `preprocessed_telemetry.csv` from Notebook 02 (35 epochs).
2. `spatial_gcn_embeddings.pt` from Notebook 03 (spatial latent tensor $(20, 20, 8)$).
3. `spatial_graph_mesh.npz` from Notebook 03 (`dem_grid` and `slope_deg` shape $(20, 20)$).

### FR-TEMPORAL-002: 5D Spatio-Temporal Tensor Assembly
The system **SHALL** construct 5D spatiotemporal tensors using a sliding temporal window of length $T=5$ and forward prediction horizon $\tau=1$:
$$N_{\text{samples}} = N_{\text{frames}} - T - \tau + 1 = 35 - 5 - 1 + 1 = 30$$
- Input tensor $X \in \mathbb{R}^{30 \times 5 \times 2 \times 20 \times 20}$.
- Target tensor $Y \in \mathbb{R}^{30 \times 1 \times 2 \times 20 \times 20}$.
- Channel 0: Sentinel-1 $\sigma^0_{VV}$ backscatter modulated by normalized slope gradient.
- Channel 1: Sentinel-2 NDVI modulated by normalized DEM elevation.
- Any missing cloud-masked optical values **SHALL** be sanitized via linear temporal interpolation with backward and forward fill.

### FR-TEMPORAL-003: Chronological Train-Test Split
The system **SHALL** split the 30 sequence samples chronologically at ratio $\rho=0.80$:
- Training split: $B_{\text{train}} = \lfloor 30 \times 0.80 \rfloor = 24$ sequences.
- Test split: $B_{\text{test}} = 30 - 24 = 6$ sequences.
- Random shuffling is strictly prohibited to preserve temporal causality.

### FR-TEMPORAL-004: Custom ConvLSTM Recurrent Cell Architecture
The system **SHALL** implement a PyTorch `ConvLSTMCell` with:
- $C_{\text{in}} = 2$ (SAR VV, NDVI), $C_{\text{hidden}} = 16$, $k = 3$, padding $= 1$.
- Unified 2D convolution for input ($i$), forget ($f$), candidate ($c$), and output ($o$) gates:
  $$\begin{bmatrix} \mathbf{i}_t \\ \mathbf{f}_t \\ \tilde{\mathbf{c}}_t \\ \mathbf{o}_t \end{bmatrix} = \begin{bmatrix} \sigma \\ \sigma \\ \tanh \\ \sigma \end{bmatrix} \left( \mathbf{W} * [\mathbf{x}_t, \mathbf{h}_{t-1}] + \mathbf{b} \right), \quad \mathbf{W} \in \mathbb{R}^{64 \times 18 \times 3 \times 3}$$
  $$\mathbf{c}_t = \mathbf{f}_t \odot \mathbf{c}_{t-1} + \mathbf{i}_t \odot \tilde{\mathbf{c}}_t$$
  $$\mathbf{h}_t = \mathbf{o}_t \odot \tanh(\mathbf{c}_t)$$
- All hidden states **SHALL** be zero-initialized: $\mathbf{h}_0 = \mathbf{0}, \mathbf{c}_0 = \mathbf{0}$.

### FR-TEMPORAL-005: Spatial-Temporal Network Forecasting Head
The system **SHALL** wrap the recurrent cell in `SpatialTemporalConvLSTM` with a multi-scale convolutional output head:
$$\mathbf{y}_{\text{pred}} = \operatorname{Conv2D}_{1 \times 1}\left(\operatorname{ReLU}\left(\operatorname{Conv2D}_{3 \times 3}(\mathbf{h}_T)\right)\right)$$
- Output shape: $(B, 1, 2, 20, 20)$.

### FR-TEMPORAL-006: Optimization & Convergence Verification
The system **SHALL** optimize model weights for 25 epochs using Adam ($\text{lr} = 10^{-3}$) and MSE loss with gradient norm clipping ($\text{max\_norm} = 1.0$):
$$\mathcal{L}_{\text{MSE}} = \frac{1}{B \cdot C \cdot H \cdot W} \sum_{b,c,i,j} \left(Y_{b,1,c,i,j} - \hat{Y}_{b,1,c,i,j}\right)^2$$
- Invariant: Percentage loss reduction over 25 epochs **SHALL** exceed $10.0\%$.

### FR-TEMPORAL-007: Temporal Lookback Horizon Ablation
The system **SHALL** evaluate validation MSE and channel MAE across sequence lookback horizons $T \in \{3, 5, 7, 10\}$:
- Invariant: Extended lookback horizon ($T=10$) **SHALL** achieve lower validation MSE than short lookback horizon ($T=3$).

### FR-TEMPORAL-008: Autoregressive Hydrological Rollout
The system **SHALL** compute a 5-step recursive closed-loop autoregressive forecast:
$$\hat{\mathbf{x}}_{t+1} = \mathcal{M}\left([\mathbf{x}_{t-T+1}, \dots, \mathbf{x}_t]\right)$$
$$\hat{\mathbf{x}}_{t+2} = \mathcal{M}\left([\mathbf{x}_{t-T+2}, \dots, \mathbf{x}_t, \hat{\mathbf{x}}_{t+1}]\right)$$
- Invariant: All rollout predictions must remain finite, free of NaNs, and physically bounded ($|\sigma^0_{VV}| < 50.0\text{ dB}$).

### FR-TEMPORAL-009: Dual-Target Persistence & Checkpoint Schema
The system **SHALL** export:
1. `convlstm_model_init.pt` (weights, dimensions, losses, reduction %).
2. `temporal_latent_states.pt` (final recurrent state $h_{\text{final}} \in \mathbb{R}^{6 \times 16 \times 20 \times 20}$, 5-step rollout tensor $(1, 5, 2, 20, 20)$).
3. `temporal_sequence_ablation.json` (metrics for horizons 3, 5, 7, 10).
Persisted to `5_storage/notebook_results/notebook_04_temporal_modeling/` and mirrored in `data/processed/`.

---

## 3. Data Integrity & Tensor Contract Requirements (DI)

- **DI-TEMPORAL-001 (5D Sequence Shape)**: Input tensor $X$ strictly conforms to shape $(30, 5, 2, 20, 20)$.
- **DI-TEMPORAL-002 (Target Dimension Contract)**: Target tensor $Y$ strictly conforms to shape $(30, 1, 2, 20, 20)$.
- **DI-TEMPORAL-003 (Batch Split Conservation)**: $B_{\text{train}} + B_{\text{test}} = 24 + 6 = 30$.
- **DI-TEMPORAL-004 (Hidden State Dimension)**: Final recurrent hidden state shape equals $(6, 16, 20, 20)$.
- **DI-TEMPORAL-005 (Rollout Tensor Shape)**: Autoregressive tensor shape equals $(1, 5, 2, 20, 20)$.
- **DI-TEMPORAL-006 (Zero Non-Finite Elements)**: All exported tensors must have zero NaNs and zero Infs.

---

## 4. Verification Procedures (VP) & Acceptance Test Suite

The verification suite `tests/test_notebook_04_verification.py` executes 7 strict automated tests:

| Test ID | Procedure Description | Acceptance Criteria | Verified Result |
| :--- | :--- | :--- | :--- |
| **VP-TEMPORAL-01** | `test_01_no_python_scripts_in_notebook_dir` | Directory `1_notebooks_sandbox/` contains 0 `.py` scripts | **PASSED** |
| **VP-TEMPORAL-02** | `test_02_notebook_cell_structure_and_markdown_rules` | Notebook length $\ge 30$ cells; every code cell preceded by markdown | **PASSED** (32 cells) |
| **VP-TEMPORAL-03** | `test_03_all_code_cells_executed_with_zero_errors` | Exactly 14 code cells; all executed; zero error outputs | **PASSED** (14/14 executed) |
| **VP-TEMPORAL-04** | `test_04_penultimate_and_ultimate_markdown_cells` | Penultimate contains Executive Summary; Ultimate contains IP notice | **PASSED** |
| **VP-TEMPORAL-05** | `test_05_storage_artifacts_and_plots_persisted` | 5 plots (>50KB) and 2 data artifacts exist in dual storage | **PASSED** |
| **VP-TEMPORAL-06** | `test_06_model_checkpoint_and_latent_contracts` | Checkpoint contracts ($C_{\text{in}}=2, C_h=16, C_o=2, T=5$), loss reduction $>10\%$, $h_{\text{final}} \in \mathbb{R}^{6 \times 16 \times 20 \times 20}$ | **PASSED** |
| **VP-TEMPORAL-07** | `test_07_temporal_ablation_and_loss_convergence` | JSON exists; horizons 3, 5, 7, 10 present; $\text{MSE}_{T=10} < \text{MSE}_{T=3}$ | **PASSED** |

---

## 5. Aerospace Artifact Inventory

The following files are permanently stored in `5_storage/notebook_results/notebook_04_temporal_modeling/`:

| Artifact Name | Type | Size | Description |
| :--- | :--- | :--- | :--- |
| `plot_01_spatiotemporal_tensor_slices.png` | PNG (120 DPI) | ~50 KB | 2-row $\times$ 6-column spatial maps showing sequential temporal evolution of SAR and NDVI channels. |
| `plot_02_loss_convergence_and_spatial_prediction.png` | PNG (120 DPI) | ~101 KB | Dual-panel visualization of 25-epoch train/test MSE loss curves and spatial prediction vs ground truth. |
| `plot_03_temporal_lookback_ablation.png` | PNG (120 DPI) | ~82 KB | Multi-bar chart illustrating validation MSE, SAR MAE, and NDVI MAE across lookback horizons. |
| `plot_04_autoregressive_rollout_recession.png` | PNG (120 DPI) | ~78 KB | Spatial rollout sequence maps and line trajectory graphs over 5 consecutive forecast steps. |
| `plot_05_recurrent_hidden_state_activations.png` | PNG (120 DPI) | ~84 KB | 8-panel activation map grid displaying internal recurrent feature representations. |
| `convlstm_model_init.pt` | PyTorch | ~50 KB | Model state dictionary, layer parameters, training loss curves, and metadata. |
| `temporal_latent_states.pt` | PyTorch | ~172 KB | Serialized recurrent states $h_{\text{final}}$ and autoregressive rollout tensor. |
| `temporal_sequence_ablation.json` | JSON | 735 Bytes | Numerical metrics across lookback horizons $T \in \{3, 5, 7, 10\}$. |

---

## 6. Traceability Matrix

| Requirement | Notebook 04 Code Cell | Verification Test | Storage Artifact |
| :--- | :--- | :--- | :--- |
| **FR-TEMPORAL-001** | Cell 5 | `test_03_all_code_cells_executed_with_zero_errors` | `preprocessed_telemetry.csv`, `spatial_gcn_embeddings.pt` |
| **FR-TEMPORAL-002** | Cell 7, 9 | `test_06_model_checkpoint_and_latent_contracts` | `plot_01_spatiotemporal_tensor_slices.png` |
| **FR-TEMPORAL-003** | Cell 7 | `test_06_model_checkpoint_and_latent_contracts` | `convlstm_model_init.pt` |
| **FR-TEMPORAL-004** | Cell 11 | `test_06_model_checkpoint_and_latent_contracts` | `convlstm_model_init.pt` |
| **FR-TEMPORAL-005** | Cell 11, 13 | `test_06_model_checkpoint_and_latent_contracts` | `convlstm_model_init.pt` |
| **FR-TEMPORAL-006** | Cell 15, 17 | `test_06_model_checkpoint_and_latent_contracts` | `plot_02_loss_convergence_and_spatial_prediction.png` |
| **FR-TEMPORAL-007** | Cell 19, 21 | `test_07_temporal_ablation_and_loss_convergence` | `plot_03_temporal_lookback_ablation.png`, `temporal_sequence_ablation.json` |
| **FR-TEMPORAL-008** | Cell 23, 25 | `test_06_model_checkpoint_and_latent_contracts` | `plot_04_autoregressive_rollout_recession.png`, `temporal_latent_states.pt` |
| **FR-TEMPORAL-009** | Cell 27, 29 | `test_05_storage_artifacts_and_plots_persisted` | `plot_05_recurrent_hidden_state_activations.png`, `convlstm_model_init.pt` |

---

## 7. Brutally Unfiltered Defect Log & Engineering Limitations

| Defect ID | Severity | Subsystem | Description & Root Cause | Impact & Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| `D-NB04-001` | **HIGH** | Data Cube Builder | **Synthetic Spatial Texture Modulation**: Because the upstream telemetry is a single-vector 1D temporal series, 2D spatial frames are synthesized by modulating scalar telemetry values with static DEM elevation and slope rasters. | The spatial texture reflects static topography modulated by time, rather than genuine high-resolution satellite imagery pixels that exhibit non-uniform vegetative greening or localized ponding. Mitigation: Ingest native multi-temporal Sentinel-1/2 GeoTIFF stacks. |
| `D-NB04-002` | **HIGH** | ConvLSTM Training | **Small-Sample Overfitting Regime**: The training partition contains only 24 sequence samples ($B_{\text{train}} = 24$), whereas `SpatialTemporalConvLSTM` contains $>11,000$ trainable parameters. | Risk of empirical memorization of specific rainfall cycles. Without physical constraints (e.g. mass balance, Richards PDE), the neural net could output unphysical moisture states during extreme weather anomalies. (Addressed in Notebook 05). |
| `D-NB04-003` | **MEDIUM** | Rollout Forecaster | **Compounding Autoregressive Error & Variance Damping**: In 5-step recursive closed-loop forecasting, errors in step $k$ feed into step $k+1$. Over multiple steps, predictions exhibit variance dampening (regression toward the spatial mean). | High-frequency storm peaks are smoothed out during multi-day rollouts. Mitigation: Couple with Ensemble Kalman Filter (EnKF) or nudging data assimilation in Notebook 06. |
| `D-NB04-004` | **LOW** | Pre-processing | **Linear Temporal Interpolation on Cloud-Masked Optical Frames**: Cloudy days where NDVI was masked are filled using 1D linear interpolation before constructing the 5D tensor. | Sharp post-cyclone soil greening or flood submergence drops that occurred during peak cloud cover are replaced by smooth linear gradients. Mitigation: Use SAR backscatter to predict missing optical indices during cloudy periods. |

---

## 8. Configuration Control & Environment Lineage

- **Parent Repository**: `THE_MRIDANSH`
- **Execution Python**: Python 3.12.10 (virtual environment `mridansh_env`, PyTorch 2.14.0+cpu, SciPy 1.15.2)
- **Primary Inputs**: `5_storage/notebook_results/notebook_02_preprocessing/preprocessed_telemetry.csv`, `5_storage/notebook_results/notebook_03_spatial_modeling/spatial_graph_mesh.npz`
- **Storage Target**: `5_storage/notebook_results/notebook_04_temporal_modeling/`
- **Secondary Target**: `data/processed/`
- **Verification Command**: `pytest tests/test_notebook_04_verification.py -v`
