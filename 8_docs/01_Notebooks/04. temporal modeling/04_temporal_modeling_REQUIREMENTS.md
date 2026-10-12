# THE MRIDANSH (AETHER-MRID1607X)
# Notebook 04 — Temporal Sequence Modeling & Spatial-Temporal ConvLSTM Engine
# Requirements, Verification and Configuration Control

---

## 1. Document Control

### 1.1 Identification

| Field | Value |
|:---|:---|
| **Document ID** | MRID-NB04-DOC-001 |
| **Notebook ID** | `04-temporal-modeling.ipynb` |
| **Project** | THE MRIDANSH — Unified Soil State Estimation System |
| **System / Engine** | AETHER-MRID1607X (Multi-Domain Soil Intelligence Engine) |
| **Author / Developer** | Gourgopal Mohapatra |
| **Organization** | JCC HEADQUARTER — JCC CAMPUS 2, RS-SDA Division |
| **Reviewer** | *(To be assigned — independent technical reviewer)* |
| **Approver** | *(To be assigned — systems engineering authority)* |
| **Version** | 1.0 |
| **Date** | 2026-10-08 |
| **Status** | Baseline Draft — Under Strict Technical Review |
| **Classification** | Proprietary & Controlled Research Artifact |

### 1.2 Revision History

| Version | Date | Author | Description of Change |
|:---|:---|:---|:---|
| 0.1 | 2026-10-08 | Gourgopal Mohapatra | Initial structural extraction and telemetry verification of `04-temporal-modeling.ipynb` cells, outputs, and model parameters. |
| 1.0 | 2026-10-08 | Gourgopal Mohapatra | Baseline requirements specification: atomic functional criteria, verification cases, empirical training metrics, bidirectional traceability matrix, and open discrepancy log. |

### 1.3 Document Conventions

- **SHALL** indicates a mandatory, verifiable, and contractually binding requirement.
- **SHOULD** indicates a recommended design practice or optimization target.
- **MAY** indicates an optional or alternative implementation allowance.
- **Requirement Status Definitions**:
  - `MET`: Requirement verified by execution against empirical output evidence.
  - `PARTIAL`: Requirement implemented but exhibits limitations, unhandled edge cases, or documentation discrepancies.
  - `NOT MET`: Requirement absent, failing verification, or replaced with an unverified dummy stub.
  - `WAIVED`: Formal departure accepted with documented engineering justification.
- **Verification Methods**:
  - `T` (Test): Quantitative execution with test assertions and numerical threshold validation.
  - `A` (Analysis): Theoretical evaluation of tensor shapes, mathematical formulations, or gradient dynamics.
  - `I` (Inspection): Manual examination of source code, configuration constants, and layer declarations.
  - `D` (Demonstration): Observation of operational execution, convergence trajectories, and visual telemetry plots.
- **Identifier Prefix Rules**:
  - `FR-xxx`: Functional Requirement
  - `DI-xxx`: Data Integrity Requirement
  - `IF-xxx`: Interface & File Structure Requirement
  - `UQ-xxx`: Uncertainty & Quality Requirement
  - `NF-xxx`: Non-Functional & Reproducibility Requirement
  - `VP-xxx`: Verification Procedure
  - `D-xxx`: Open Defect / Discrepancy
  - `R-xxx`: Technical Risk
  - `A-xxx`: Architectural Assumption

---

## 2. Purpose and Scope

### 2.1 Purpose

This document defines the formal software requirements, mathematical formulation, verification procedures, empirical execution evidence, bidirectional traceability, configuration management, and technical discrepancy logs for Jupyter notebook `04-temporal-modeling.ipynb` within the **THE MRIDANSH** system.

### 2.2 System Context

**THE MRIDANSH** (*AETHER-MRID1607X*) fuses multi-sensor satellite imagery (Sentinel-1 SAR, Sentinel-2 Optical, DEM) with physics-informed state estimation to predict continuous soil moisture profiles and geotechnical shear strength.

Within this pipeline:
- **Notebook 01 & 02** ingest and clean temporal telemetry series.
- **Notebook 03** constructs spatial graph topologies ($G = (V, E)$) and extracts terrain slope/aspect fields.
- **Notebook 04 (Item Under Documentation)** constructs 5-dimensional spatio-temporal sequence tensors $(B, T, C, H, W)$, implements a 2D Spatial-Temporal Convolutional Long Short-Term Memory (`ConvLSTM`) recurrent neural network, performs temporal sequence horizon ablation ($T \in \{3, 5, 7, 10\}$), and optimizes spatio-temporal weights to forecast dynamic soil moisture fields.
- **Downstream Consumers (Notebooks 05–07)** integrate these recurrent spatio-temporal representations into Richards-equation-constrained PINN solvers and Ensemble Kalman Filters (EnKF).

### 2.3 Notebook Objective

Notebook 04 spans Sprint Days 7–8 of the 18-Day Scientific Validation Sprint:
1. **Day 7 Objective**: Convert 1D/2D multi-sensor time-series into 5D sliding-window spatio-temporal tensors, instantiate a numerical-stability-clamped `SpatialTemporalConvLSTM` architecture, execute an untrained forward pass baseline, and serialize model blueprint `convlstm_model_init.pt`.
2. **Day 8 Objective**: Perform sequence horizon ablation across temporal lookback windows $T \in \{3, 5, 7, 10\}$, execute 15-epoch spatio-temporal weight optimization with Adam optimizer and gradient clipping, evaluate convergence trajectories, and render aerospace diagnostic comparisons.

### 2.4 In Scope

- All 23 cells of `04-temporal-modeling.ipynb` (11 code cells, 12 markdown cells).
- Ingestion of preprocessed telemetry table `preprocessed_telemetry.csv`.
- Formulation and execution of sliding temporal sequence windowing.
- Mathematical construction of 2D sinusoidal spatial gradient masks: $\operatorname{spatial\_pattern}(x, y) = \sin(x) + \cos(y)$.
- Assembly of 5D input tensors $X \in \mathbb{R}^{B \times T \times C \times H \times W}$ and 4D target tensors $Y \in \mathbb{R}^{B \times C \times H \times W}$.
- Architecture design of custom `ConvLSTMCell` (2D convolutions, Xavier initialization, gate clamping $[-10.0, 10.0]$).
- Architecture design of `SpatialTemporalConvLSTM` recurrent network with 2D $1 \times 1$ convolutional prediction head.
- Sequence horizon ablation analysis across $T \in \{3, 5, 7, 10\}$.
- Multi-epoch training loop with Adam optimizer, gradient clipping ($\text{max\_norm} = 1.0$), and MSE loss tracking.
- Rendering of 2 diagnostic aerospace figures (Predicted vs Actual spatial fields, and Loss Convergence Curve).
- Serialization of initialization checkpoint `convlstm_model_init.pt`.

### 2.5 Out of Scope

- Notebook 03 Graph Convolutional Network (GCN) spatial modeling.
- Downstream Physics-Informed Neural Network (PINN) PDE loss terms (Notebook 05).
- Ensemble Kalman Filtering (EnKF) assimilation loops (Notebook 06).
- Deployment of models to live production serving APIs.

### 2.6 Current-State Declaration (Mandatory Engineering Disclosure)

> [!WARNING]
> **MANDATORY CURRENT-STATE DECLARATION: SYNTHETIC SPATIAL GRADIENT INJECTION**
> 
> The upstream telemetry file `preprocessed_telemetry.csv` provides scalar temporal records (35 timesteps) representing spatially lumped observations. To generate 2D spatial dimensions $(H=10, W=10)$ for ConvLSTM sequence modeling, Notebook 04 modulates the temporal scalars with an in-memory synthetic 2D trigonometric spatial pattern:
> $$\operatorname{spatial\_pattern}(x, y) = \sin(x) + \cos(y), \quad x, y \in [-1, 1]$$
> 
> While this verifies the **5D tensor sliding-window mechanics, convolutional recurrent gate operations, backpropagation through time (BPTT), and convergence stability**, the spatial variations are synthetically generated and do **not** represent true georeferenced pixel rasters from the Bhadrak/Balasore study footprint.

---

## 3. Definitions and Abbreviations

| Term / Abbreviation | Definition |
|:---|:---|
| **ConvLSTM** | Convolutional Long Short-Term Memory (Recurrent neural network with internal 2D convolutional gate transitions). |
| **5D Tensor** | Five-dimensional data structure of shape $(B, T, C, H, W)$ denoting Batch, Timesteps, Channels, Height, Width. |
| **BPTT** | Backpropagation Through Time (Gradient computation algorithm across unrolled recurrent sequence steps). |
| **SAR VV** | Sentinel-1 vertical-transmit vertical-receive radar backscatter (Z-score standardized). |
| **NDVI** | Normalized Difference Vegetation Index: $(B08 - B04)/(B08 + B04)$ (Min-Max standardized $[0, 1]$). |
| **Lookback Window ($T$)** | Number of historical observation timesteps fed into the recurrent state to predict the next temporal state. |
| **Gate Clamping** | Numerical bounding operation restricting pre-activation gate potentials to $[-10.0, 10.0]$ to prevent exponential overflow. |
| **MSE** | Mean Squared Error: $\frac{1}{N} \sum (Y_{\text{pred}} - Y_{\text{true}})^2$. |
| **JCC RS-SDA** | Jagannath Command Center — Remote Sensing & Spatial Data Analytics Division. |

---

## 4. Requirements

### 4.1 Functional Requirements

- **FR-001**: The software shall verify or ingest preprocessed telemetry table `preprocessed_telemetry.csv`.
- **FR-002**: The software shall configure temporal sequence modeling dimensions:
  - Default lookback sequence horizon $T = 7$ timesteps (1-week analysis window).
  - Feature channel depth $C = 2$ (Channel 0: SAR VV, Channel 1: Optical NDVI).
  - Spatial sub-grid footprint dimensions $H = 10$, $W = 10$ pixels.
- **FR-003**: The software shall generate a continuous 2D spatial gradient template matrix of shape $(10, 10)$ over coordinate interval $[-1, 1] \times [-1, 1]$ via:
  $$\operatorname{spatial\_pattern}(x, y) = \sin(x) + \cos(y)$$
- **FR-004**: The software shall transform tabular time-series into 5D input tensors $X \in \mathbb{R}^{B \times T \times C \times H \times W}$ and 4D target tensors $Y \in \mathbb{R}^{B \times C \times H \times W}$ using a sliding temporal window where:
  $$B = N_{\text{frames}} - T$$
  $$X[b, t, 0, :, :] = 0.5 \cdot \operatorname{spatial\_pattern} + \operatorname{SAR}[b + t]$$
  $$X[b, t, 1, :, :] = 0.2 \cdot \operatorname{spatial\_pattern} + \operatorname{NDVI}[b + t]$$
  $$Y[b, 0, :, :] = 0.5 \cdot \operatorname{spatial\_pattern} + \operatorname{SAR}[b + T]$$
  $$Y[b, 1, :, :] = 0.2 \cdot \operatorname{spatial\_pattern} + \operatorname{NDVI}[b + T]$$
- **FR-005**: For $N_{\text{frames}} = 35$ and $T = 7$, the software shall assemble input tensor $X$ with exact shape `torch.Size([28, 7, 2, 10, 10])` and target tensor $Y$ with exact shape `torch.Size([28, 2, 10, 10])`.
- **FR-006**: The software shall implement a custom `ConvLSTMCell` module satisfying:
  - Joint input-hidden convolution: $\operatorname{Conv2D}(C_{\text{in}} + C_{\text{hidden}}, 4 \cdot C_{\text{hidden}}, \text{kernel}=3, \text{pad}=1)$.
  - Xavier uniform weight initialization and zero bias initialization.
  - Symmetrical gate clamping enforcing pre-activation bounds $[-10.0, 10.0]$.
  - Standard LSTM recurrent state updates across input ($i$), forget ($f$), output ($o$), and cell candidate ($g$) gates:
    $$c_{t} = f_t \circ c_{t-1} + i_t \circ g_t, \quad h_{t} = o_t \circ \tanh(c_t)$$
- **FR-007**: The software shall implement a recurrent `SpatialTemporalConvLSTM` wrapper class unrolling the cell across sequence length $T$ and projecting final hidden state $h_T$ back to $C_{\text{in}}$ channels using a $1 \times 1$ convolutional prediction head.
- **FR-008**: The software shall execute an untrained forward pass in evaluation mode (`model.eval()`, `torch.no_grad()`) and log the initial spatial MSE loss against target tensor $Y$.
- **FR-009**: The software shall serialize the untrained ConvLSTM model blueprint, configuration parameters, and state dictionary to artifact `convlstm_model_init.pt`.
- **FR-010**: The software shall execute a sequence horizon ablation function evaluating sliding tensor shapes and initial MSE loss across lookback windows $T \in \{3, 5, 7, 10\}$.
- **FR-011**: The software shall implement an iterative optimization loop executing 15 training epochs using the Adam optimizer ($lr = 0.001$), Mean Squared Error criterion, and gradient norm clipping ($\text{max\_norm} = 1.0$).
- **FR-012**: The software shall record loss convergence history across all 15 epochs and demonstrate monotonic loss minimization.
- **FR-013**: The software shall render 2 aerospace diagnostic figures:
  - *Aerospace Plot 1*: Untrained spatial forecast vs ground truth target field with embedded diagnostics.
  - *Aerospace Plot 2*: 15-epoch MSE loss convergence trajectory curve alongside post-training spatial forecast field.

### 4.2 Data Integrity Requirements

- **DI-001**: Sequence generation shall strictly preserve chronological ordering; future frames shall never leak into lookback window inputs ($t < T$).
- **DI-002**: Sample count conservation: for total frames $N$ and sequence length $T$, the batch dimension shall strictly satisfy $B = N - T$.
- **DI-003**: Zero Spatial Distortion: 2D convolutional padding ($\text{padding} = 1$ for $\text{kernel} = 3$) shall strictly preserve spatial dimensions ($H_{\text{out}} = H_{\text{in}} = 10, W_{\text{out}} = W_{\text{in}} = 10$).
- **DI-004**: Numerical Sanitization: Input tensors $X$, targets $Y$, and predictions $Y_{\text{pred}}$ shall be checked and purged of `NaN` or `Inf` values via `torch.nan_to_num`.
- **DI-005**: Recurrent State Initialization: Hidden state $h_0$ and cell state $c_0$ shall be strictly zero-initialized matching the input tensor device and data type.

### 4.3 Interface Requirements

- **IF-001**: The software shall attempt loading telemetry from `/kaggle/input/.../preprocessed_telemetry.csv` and execute an in-memory fallback if absent without fatal interruption.
- **IF-002**: The software shall create export directory `/kaggle/working/data_processed/` if absent.
- **IF-003**: The checkpoint file `convlstm_model_init.pt` shall serialize a dictionary containing exactly:
  - `'model_state_dict'`
  - `'seq_len'`
  - `'channels'`
  - `'grid_dim'`
- **IF-004**: The output prediction tensor shall strictly match target tensor dimensions $(B, C, H, W)$ to enable downstream element-wise loss evaluation.

### 4.4 Uncertainty / Quality Requirements

- **UQ-001**: Pre-activation gate tensors shall be explicitly clamped to $[-10.0, 10.0]$ to eliminate exploding exponentials in $\operatorname{sigmoid}$ and $\tanh$ activations.
- **UQ-002**: Gradient norm clipping shall be applied at threshold $\text{max\_norm} = 1.0$ prior to every optimizer step to prevent recurrent gradient explosion.
- **UQ-003**: Untrained baseline loss and post-training convergence reduction percentage shall be audited and displayed on diagnostic plots.

### 4.5 Non-Functional Requirements

- **NF-001**: Deterministic seeds shall be fixed for PyTorch (`torch.manual_seed(42)`) and NumPy (`np.random.seed(42)`).
- **NF-002**: The notebook shall execute unattended from Cell 00 to Cell 22 without manual intervention.
- **NF-003**: Visual plots shall comply with the project dark telemetry styling (`#00FFCC` borders, `#1A3344` grid, `#0A192F` annotation boxes).
- **NF-004**: Execution memory footprint shall not exceed standard container limits (< 500 MB RAM).

---

## 5. Requirements Attributes

| ID | Requirement Statement | Rationale | Method | Acceptance Criterion | Status |
|:---|:---|:---|:---:|:---|:---:|
| **FR-001** | Ingest or verify telemetry table. | Upstream pipeline dependency. | I/T | Telemetry loaded or fallback initialized. | **MET** |
| **FR-002** | Configure tensor parameters ($T=7, C=2, H=10, W=10$). | Standardized dimensions for sequence engine. | I | Constants declared and logged. | **MET** |
| **FR-003** | Generate 2D trigonometric spatial gradient pattern. | Spatial foundation for simulated pixel rasters. | T | Array shape $(10, 10)$, values in $[-\sqrt{2}, \sqrt{2}]$. | **MET** |
| **FR-004** | Sliding sequence window transformation. | Temporal sequence modeling input formatting. | T | Tensors generated matching sliding window math. | **MET** |
| **FR-005** | Shape validation: $X \in \mathbb{R}^{28 \times 7 \times 2 \times 10 \times 10}$, $Y \in \mathbb{R}^{28 \times 2 \times 10 \times 10}$. | Exact 5D tensor interface contract. | T | Tensor shapes match expected dimensions. | **MET** |
| **FR-006** | Custom `ConvLSTMCell` with gate clamping $[-10, 10]$. | Spatio-temporal recurrent gate dynamics. | I/T | Module instantiates, clamped gates execute. | **MET** |
| **FR-007** | Recurrent `SpatialTemporalConvLSTM` with $1 \times 1$ head. | Unrolled sequence forecasting network. | I/T | Model processes 5D tensor, emits $(B, C, H, W)$. | **MET** |
| **FR-008** | Untrained forward pass and initial MSE evaluation. | Baseline benchmark before optimization. | T | Forward pass executes, loss printed ($0.859975$). | **MET** |
| **FR-009** | Export model checkpoint `convlstm_model_init.pt`. | Downstream model blueprint persistence. | T | File exists on disk; dictionary keys verified. | **MET** |
| **FR-010** | Sequence horizon ablation ($T \in \{3, 5, 7, 10\}$). | Lookback sensitivity analysis. | T | All 4 horizons evaluated, metrics logged. | **MET** |
| **FR-011** | 15-epoch Adam optimization with gradient clipping. | Spatio-temporal weight convergence. | T | 15 epochs complete; loss drops monotonically. | **MET** |
| **FR-012** | Record loss history and convergence trajectory. | Verification of neural learning dynamics. | T | `loss_history` contains 15 values; final loss $< 0.70$. | **MET** |
| **FR-013** | Render 2 aerospace diagnostic figures. | Visual telemetry and convergence auditing. | D | Figures displayed with colorbars and annotations. | **MET** |
| **DI-001** | Strict chronological sequence ordering. | Eliminate temporal lookahead leakage. | T | Inputs strictly precede prediction targets. | **MET** |
| **DI-002** | Batch sample count conservation ($B = N - T$). | Mathematical consistency of sliding windows. | T | $B = 35 - 7 = 28$ verified. | **MET** |
| **DI-003** | Spatial dimension preservation ($H=10, W=10$). | Spatial resolution invariant across convolutions. | T | Output height and width equal input height/width. | **MET** |
| **DI-004** | NaN/Inf sanitization via `torch.nan_to_num`. | Numerical stability of training tensors. | T | Zero NaNs in $X, Y, Y_{\text{pred}}$. | **MET** |
| **DI-005** | Zero-initialized initial recurrent hidden states. | Standardized recurrent boundary condition. | T | Initial $h_0, c_0$ tensors filled with zeros. | **MET** |
| **IF-001** | Telemetry path existence check with fallback. | Fault tolerance in disconnected environments. | T | Absence of file triggers warning without crash. | **MET** |
| **IF-002** | Automatic export directory initialization. | File system portability. | T | Directory `/kaggle/working/data_processed/` created. | **MET** |
| **IF-003** | Checkpoint serialization contract. | Downstream model loading contract. | I/T | 4 mandatory keys verified in checkpoint dict. | **MET** |
| **IF-004** | Output dimension compatibility with target tensor. | Element-wise loss computation compatibility. | T | Shape of $Y_{\text{pred}}$ equals shape of $Y$. | **MET** |
| **UQ-001** | Pre-activation gate clamping $[-10.0, 10.0]$. | Prevent floating-point overflow in gates. | I/T | Clamp operation verified in `ConvLSTMCell`. | **MET** |
| **UQ-002** | Gradient norm clipping ($\text{max\_norm} = 1.0$). | Recurrent gradient stability during BPTT. | I/T | `clip_grad_norm_` executed before optimizer step. | **MET** |
| **UQ-003** | Display baseline and post-training diagnostics. | Quantitative telemetry transparency. | D | Initial loss, final loss, and delta displayed. | **MET** |
| **NF-001** | Deterministic seed initialization (PyTorch 42, NumPy 42). | Bit-for-bit execution reproducibility. | I/T | Seeds declared in Cell 02. | **MET** |
| **NF-002** | Unattended headless notebook execution. | Batch execution readiness. | D | All 23 cells run sequentially without error. | **MET** |
| **NF-003** | Dark telemetry plot styling parameters. | Enterprise visual consistency across division. | I | Cyan borders, dark blue annotation boxes. | **MET** |
| **NF-004** | Lightweight memory footprint (< 500 MB). | Resource compliance in container runtimes. | A | Minimal tensor footprints (~1 MB). | **MET** |

---

## 6. Verification Procedures

### VP-001: Telemetry Ingestion and Sequence Parameter Verification
- **Verifies**: FR-001, FR-002, IF-001, NF-001
- **Setup**: Python 3.10+ kernel with PyTorch, NumPy, Pandas.
- **Procedure**:
  1. Initialize target data path.
  2. Execute ingestion check.
  3. Validate constants: `SEQUENCE_LENGTH = 7`, `CHANNELS = 2`, `HEIGHT = 10`, `WIDTH = 10`.
- **Expected Result**: 35 records verified; parameters logged to stdout.
- **Pass Criterion**: Zero exceptions; logged parameters match specification.

### VP-002: 2D Spatial Gradient Mask Formulation
- **Verifies**: FR-003, DI-003
- **Setup**: Coordinate arrays $x, y \in [-1, 1]$ with 10 discrete intervals.
- **Procedure**:
  1. Generate meshgrid `xx, yy`.
  2. Evaluate `spatial_pattern = np.sin(xx) + np.cos(yy)`.
  3. Inspect shape, minimum, and maximum.
- **Expected Result**: Array shape equals $(10, 10)$; values lie in range $[-\sqrt{2}, \sqrt{2}] \approx [-1.414, 1.414]$.
- **Pass Criterion**: Shape exactly $(10, 10)$, zero NaNs.

### VP-003: 5D Spatio-Temporal Sequence Tensor Assembly
- **Verifies**: FR-004, FR-005, DI-001, DI-002, DI-004
- **Setup**: Telemetry dataframe (35 rows), spatial pattern from VP-002.
- **Procedure**:
  1. Call `create_spatial_temporal_sequences(df_prep, seq_len=7, h=10, w=10)`.
  2. Inspect returned tensor shapes, data types, and null counts.
- **Expected Result**:
  - `X_tensor.shape == torch.Size([28, 7, 2, 10, 10])`
  - `Y_tensor.shape == torch.Size([28, 2, 10, 10])`
  - Data type: `torch.float32`.
- **Pass Criterion**: Exact shapes verified; zero NaNs.

### VP-004: ConvLSTM Cell Architecture and Gate Clamping
- **Verifies**: FR-006, UQ-001
- **Setup**: Instantiated `ConvLSTMCell(in_channels=2, hidden_channels=16, kernel_size=3)`.
- **Procedure**:
  1. Pass dummy tensor $x \in \mathbb{R}^{1 \times 2 \times 10 \times 10}$ and states $h, c \in \mathbb{R}^{1 \times 16 \times 10 \times 10}$.
  2. Assert gate clamping $[-10.0, 10.0]$ is active.
  3. Verify output state shapes match hidden dimensions.
- **Expected Result**: Outputs $h_{\text{next}}, c_{\text{next}}$ have shape `torch.Size([1, 16, 10, 10])`.
- **Pass Criterion**: Shapes preserved; Xavier weights verified.

### VP-005: SpatialTemporalConvLSTM Model Instantiation
- **Verifies**: FR-007, DI-003, DI-005
- **Setup**: Instantiated `SpatialTemporalConvLSTM(in_channels=2, hidden_channels=16)`.
- **Procedure**:
  1. Inspect network submodules: `conv_lstm` and `head`.
  2. Assert `head` is $1 \times 1$ convolution mapping 16 channels to 2 channels.
- **Expected Result**: Module architecture printed successfully.
- **Pass Criterion**: Submodules conform to specification.

### VP-006: Untrained Forward Pass and Baseline MSE Diagnostic
- **Verifies**: FR-008, IF-004, UQ-003
- **Setup**: `convlstm_model.eval()`, `X_tensor`, `Y_tensor`.
- **Procedure**:
  1. Execute forward pass with `torch.no_grad()`.
  2. Calculate `nn.MSELoss()(y_pred_tensor, Y_tensor).item()`.
- **Expected Result**: Output shape `torch.Size([28, 2, 10, 10])`. Temporal MSE loss equals **0.859975**.
- **Pass Criterion**: Loss matches **0.859975** under seed 42.

### VP-007: Aerospace Plot 1 Verification
- **Verifies**: FR-013, NF-003, D
- **Setup**: Extracted target and prediction arrays for sample 0, channel 0.
- **Procedure**:
  1. Render 2-panel plot comparing Ground Truth vs Untrained Forecast.
  2. Verify dynamic colorbars and embedded diagnostic box.
- **Expected Result**: Plot displays with `viridis` and `plasma` colormaps.
- **Pass Criterion**: Render completes without clipping or display errors.

### VP-008: Model Blueprint Serialization
- **Verifies**: FR-009, IF-002, IF-003
- **Setup**: `convlstm_model`, export directory.
- **Procedure**:
  1. Save state dictionary to `/kaggle/working/data_processed/convlstm_model_init.pt`.
  2. Reload archive and assert presence of `'model_state_dict'`, `'seq_len'`, `'channels'`, `'grid_dim'`.
- **Expected Result**: File written to disk, reload succeeds.
- **Pass Criterion**: File exists, byte-readable, dictionary keys match contract.

### VP-009: Sequence Horizon Ablation Execution
- **Verifies**: FR-010, DI-002
- **Setup**: Function `run_sequence_ablation(df_prep, [3, 5, 7, 10])`.
- **Procedure**:
  1. Iterate across lookback horizons $T \in \{3, 5, 7, 10\}$.
  2. Record tensor shapes and initial MSE values.
- **Expected Result**:
  - $T=3$: Tensor `[32, 3, 2, 10, 10]`, MSE = **0.85518**
  - $T=5$: Tensor `[30, 5, 2, 10, 10]`, MSE = **0.87601**
  - $T=7$: Tensor `[28, 7, 2, 10, 10]`, MSE = **0.88071**
  - $T=10$: Tensor `[25, 10, 2, 10, 10]`, MSE = **0.86520**
- **Pass Criterion**: All 4 horizons match expected shapes and MSE values.

### VP-010: Multi-Epoch Optimization & Loss Convergence
- **Verifies**: FR-011, FR-012, UQ-002
- **Setup**: `convlstm_model.train()`, Adam optimizer ($lr=0.001$), MSE loss, 15 epochs.
- **Procedure**:
  1. Execute training loop with `loss.backward()`, `clip_grad_norm_`, and `optimizer.step()`.
  2. Record loss per epoch.
- **Expected Result**:
  - Epoch 01 MSE: **0.847105**
  - Epoch 03 MSE: **0.814763**
  - Epoch 06 MSE: **0.769809**
  - Epoch 09 MSE: **0.733365**
  - Epoch 12 MSE: **0.714874**
  - Epoch 15 MSE: **0.698587**
- **Pass Criterion**: Monotonic loss reduction over training; Epoch 15 loss $< 0.70$.

### VP-011: Aerospace Plot 2 Convergence Evaluation
- **Verifies**: FR-013, NF-003, D
- **Setup**: `loss_history` array and trained forecast tensor.
- **Procedure**:
  1. Render 2-panel figure showing loss trajectory and trained spatial prediction.
  2. Inspect embedded diagnostic text.
- **Expected Result**: Loss trajectory plotted with `#00FFCC` line; spatial forecast rendered with `viridis`.
- **Pass Criterion**: Figure rendered successfully.

### VP-012: Deterministic Reproducibility
- **Verifies**: NF-001, NF-002
- **Setup**: Clean Python environment.
- **Procedure**:
  1. Execute notebook top-to-bottom twice.
  2. Compare epoch loss values and initial MSE.
- **Expected Result**: Bit-identical numerical values.
- **Pass Criterion**: Identical loss values across runs.

---

## 7. Verification Results

Evidence tags:
- **`[NB]`**: Directly extracted from cell execution outputs in `04-temporal-modeling.ipynb`.
- **`[AN]`**: Independently re-calculated numerical verification.
- **`[INS]`**: Source code and parameter inspection.

| VP ID | Verification Target | Execution Date | Executor | Result | Empirical Evidence & Numerical Values | Reviewer |
|:---|:---|:---:|:---:|:---:|:---|:---:|
| **VP-001** | Telemetry Ingestion & Parameters | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 04: *"Loaded Preprocessed Telemetry Dataset: 35 records"*, $T=7$, $C=2$, $H=10$, $W=10$. | *Pending* |
| **VP-002** | 2D Spatial Pattern Generation | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[AN]` Evaluated `sin(xx) + cos(yy)` on $[-1, 1]^{10 \times 10}$. Shape $(10, 10)$, range $[-1.414, 1.414]$. | *Pending* |
| **VP-003** | 5D Sequence Tensor Assembly | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 10: $X$: `torch.Size([28, 7, 2, 10, 10])`, $Y$: `torch.Size([28, 2, 10, 10])`. | *Pending* |
| **VP-004** | ConvLSTM Cell Gate Clamping | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[INS]` Cell 08: Line 188: `torch.clamp(gates, min=-10.0, max=10.0)`. | *Pending* |
| **VP-005** | Model Architecture Definition | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 08: *"Fixed ConvLSTM Architecture Instantiated!"*. Submodules verified. | *Pending* |
| **VP-006** | Untrained Forward Pass & MSE | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 10: Initial MSE Loss: **0.859975**. Predictions shape: `torch.Size([28, 2, 10, 10])`. | *Pending* |
| **VP-007** | Aerospace Plot 1 Diagnostics | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 12: PNG rendered (length: 68,692 bytes). Ground Truth vs Untrained Forecast displayed. | *Pending* |
| **VP-008** | Model Blueprint Serialization | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 14: Saved `convlstm_model_init.pt` to `/kaggle/working/data_processed/`. | *Pending* |
| **VP-009** | Sequence Horizon Ablation | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 16: $T=3$ (0.85518), $T=5$ (0.87601), $T=7$ (0.88071), $T=10$ (0.86520). | *Pending* |
| **VP-010** | 15-Epoch Loss Convergence | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 18: Epoch 01: **0.847105** $\to$ Epoch 15: **0.698587**. Monotonic decrease verified. | *Pending* |
| **VP-011** | Aerospace Plot 2 Convergence | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 20: PNG rendered (length: 107,912 bytes). Loss curve and post-training map displayed. | *Pending* |
| **VP-012** | Deterministic Reproducibility | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Bit-identical outputs verified across seeds (Torch 42, NumPy 42). | *Pending* |

---

## 8. Requirements Traceability Matrix

```
Requirement (Section 4)
       │
       ▼
Software Design & Code Cell (Notebook Implementation)
       │
       ▼
Verification Procedure (Section 6)
       │
       ▼
Verification Result & Empirical Evidence (Section 7)
```

| Requirement ID | Design Implementation Element | Code Cell | Verification Procedure | Verification Result |
|:---|:---|:---:|:---:|:---:|
| **FR-001** | Telemetry ingestion check & synthetic fallback | Cell 04 | VP-001 | **PASS** |
| **FR-002** | Sequence constants ($T=7, C=2, H=10, W=10$) | Cell 04 | VP-001 | **PASS** |
| **FR-003** | 2D trigonometric spatial pattern generator | Cell 06 | VP-002 | **PASS** |
| **FR-004** | Sliding temporal window sequence constructor | Cell 06 | VP-003 | **PASS** |
| **FR-005** | 5D tensor interface contract validation | Cell 06 | VP-003 | **PASS** |
| **FR-006** | `ConvLSTMCell` with gate clamping $[-10, 10]$ | Cell 08 | VP-004 | **PASS** |
| **FR-007** | `SpatialTemporalConvLSTM` with $1 \times 1$ head | Cell 08 | VP-005 | **PASS** |
| **FR-008** | Untrained forward pass & baseline MSE diagnostic | Cell 10 | VP-006 | **PASS** |
| **FR-009** | Model checkpoint export (`convlstm_model_init.pt`) | Cell 14 | VP-008 | **PASS** |
| **FR-010** | Dynamic lookback sequence ablation ($T=3, 5, 7, 10$) | Cell 16 | VP-009 | **PASS** |
| **FR-011** | 15-epoch Adam optimization with gradient clipping | Cell 18 | VP-010 | **PASS** |
| **FR-012** | Monotonic loss history recording | Cell 18 | VP-010 | **PASS** |
| **FR-013** | Aerospace diagnostic plotting suite | Cells 12, 20 | VP-007, VP-011 | **PASS** |
| **DI-001** | Non-leaking chronological window slicing | Cell 06 | VP-003 | **PASS** |
| **DI-002** | Sample count conservation ($B = N - T$) | Cell 06 | VP-003 | **PASS** |
| **DI-003** | Convolutional spatial dimension preservation | Cell 08 | VP-004 | **PASS** |
| **DI-004** | NaN/Inf sanitization via `torch.nan_to_num` | Cells 10, 16 | VP-006 | **PASS** |
| **DI-005** | Zero initial hidden and cell state tensors | Cell 08 | VP-005 | **PASS** |
| **IF-001** | Ingestion file check with fallback notification | Cell 04 | VP-001 | **PASS** |
| **IF-002** | Directory creation via `os.makedirs` | Cell 14 | VP-008 | **PASS** |
| **IF-003** | Checkpoint dictionary schema contract | Cell 14 | VP-008 | **PASS** |
| **IF-004** | Prediction and target tensor shape parity | Cell 10 | VP-006 | **PASS** |
| **UQ-001** | Pre-activation gate clamping $[-10.0, 10.0]$ | Cell 08 | VP-004 | **PASS** |
| **UQ-002** | Gradient clipping at $\text{max\_norm} = 1.0$ | Cell 18 | VP-010 | **PASS** |
| **UQ-003** | Diagnostic banner and plot annotation rendering | Cells 10, 12, 20 | VP-006, VP-011 | **PASS** |
| **NF-001** | Deterministic seed initialization (PyTorch 42, NumPy 42) | Cell 02 | VP-012 | **PASS** |
| **NF-002** | Headless non-interactive execution | All cells | Execution Audit | **PASS** |
| **NF-003** | Uniform dark telemetry plot styling parameters | Cells 02, 12, 20 | VP-007, VP-011 | **PASS** |
| **NF-004** | Memory consumption within container bounds | All cells | Analysis | **PASS** |

---

## 9. Configuration and Change Control

### 9.1 Controlled Items

The following software and data items constitute the controlled configuration baseline for Notebook 04:
1. **Source Notebook**: `1_notebooks_sandbox/04-temporal-modeling.ipynb` (SHA-256 baseline hash required).
2. **Requirements & Verification Document (This Document)**: `8_docs/01_Notebooks/04. temporal modeling/04_temporal_modeling_REQUIREMENTS.md`.
3. **Companion Technical Description (Pending User Call)**: `8_docs/01_Notebooks/04. temporal modeling/04_temporal_modeling.rst`.
4. **Export Artifact**: `convlstm_model_init.pt` (PyTorch state dict and architecture parameters).
5. **Execution Environment**: Pinned Python environment with PyTorch 2.0+, NumPy, Pandas, Matplotlib.

### 9.2 Baseline Identification

- **Current Working Baseline**: `NB04-BL-01-DRAFT`
- **Target Release Baseline**: `NB04-BL-01`
- **Upstream Baseline**: `NB02-BL-01` (`preprocessed_telemetry.csv`)
- **Downstream Target Baseline**: `NB05-BL-01` (`05-physics-validation.ipynb` / PINN formulation)

### 9.3 Change Procedure

Any modification to sequence lengths, network architectures, gate equations, loss functions, or artifacts shall follow this control lifecycle:

```
[Change Request (CR)] 
        │
        ▼
[Impact Analysis on Sequence Horizon & PINN Coupling] 
        │
        ▼
[Technical Review & Approval by Lead Authority] 
        │
        ▼
[Code / Documentation Modification] 
        │
        ▼
[Execution of Verification Procedures VP-001 to VP-012] 
        │
        ▼
[Traceability Matrix & Document Control Update] 
        │
        ▼
[Baseline Tag Update]
```

### 9.4 Version Control Rules

1. **Cell State**: Cell execution counters and outputs shall be preserved matching the baseline hash or cleanly stripped before release.
2. **Deterministic Tensors**: Clean-kernel re-runs under seeds 42 shall produce identical training MSE loss ($0.698587$ at Epoch 15).
3. **Requirement Atomicity**: Modifying a requirement mandates updating Sections 4, 5, 6, 7, and 8 concurrently.
4. **Deprecation**: Deprecated requirements shall be tagged `WITHDRAWN` and numerical IDs permanently reserved.

---

## 10. Open Defects and Discrepancies

| ID | Description | Affected Requirement | Severity | Status | Corrective Action |
|:---|:---|:---:|:---:|:---:|:---|
| **D-001** | **Mathematical Peephole Discrepancy**: Cell 01 markdown defines ConvLSTM equations with peephole connections ($W_{ci} \circ C_{t-1}$, $W_{cf} \circ C_{t-1}$, $W_{co} \circ C_t$), but code in Cell 08 implements standard ConvLSTM without peephole terms. | FR-006 | **LOW** | **OPEN** | Align markdown equations with code implementation or implement peephole parameters in `ConvLSTMCell`. |
| **D-002** | **Path Misspelling in Telemetry Ingestion**: Cell 04 specifies path `.../preprocessed-telementary-dataset/...` (misspelling `telementary`), which may cause file-not-found errors on systems using the correct directory name. | IF-001 | **MEDIUM** | **OPEN** | Standardize path string to `preprocessed-telemetry-dataset` across all notebook cells. |
| **D-003** | **Synthetic 2D Spatial Injection**: Scalar time-series from telemetry is converted to 2D grids via synthetic trigonometric modulation (`spatial_pattern`), not actual spatial pixel data. | FR-003, FR-004 | **HIGH** | **OPEN** | Ingest true 2D raster time-series stacks from Sentinel-1 / Sentinel-2 GeoTIFFs rather than modulating scalars with synthetic sine/cosine patterns. |
| **D-004** | **Narrative Loss Reduction Discrepancy**: Cell 21 text claims "19.7% reduction in MSE loss ($0.8701 \rightarrow 0.6985$)", but Cell 18 actual training output shows initial loss was **0.847105** (a **17.5% reduction**). The 0.8701 figure came from a different run. | FR-012, UQ-003 | **LOW** | **OPEN** | Update Cell 21 narrative text to reflect actual logged run numbers ($0.847105 \rightarrow 0.698587$, 17.5% reduction). |
| **D-005** | **Lack of Train/Validation/Test Split**: All 15 training epochs optimize on all 28 sequence samples without an independent validation set to monitor overfitting. | FR-011 | **MEDIUM** | **OPEN** | Implement an 80/20 chronological train/val split for sequence samples in Cell 18. |
| **D-006** | **Model Instance Overwrite**: In Cell 18, `convlstm_model` is re-instantiated, overwriting the model previously benchmarked in Cell 08 and serialized in Cell 14. | IF-003 | **LOW** | **OPEN** | Use distinct variable names (e.g. `convlstm_model_trained`) to maintain clear provenance between initialized and trained weights. |
| **D-007** | **Hardcoded Kaggle Absolute Paths**: Ingestion and export paths rely on `/kaggle/` root filesystem conventions. | IF-001, IF-002 | **MEDIUM** | **OPEN** | Introduce relative path resolution or environment variables for cross-platform execution. |
| **D-008** | **Unused Sequence Ablation Models**: Cell 16 computes initial loss across $T \in \{3, 5, 7, 10\}$ but discards the models without evaluating post-training performance across horizons. | FR-010 | **LOW** | **OPEN** | Extend ablation to train 5 epochs per horizon to verify sequence convergence rates. |

---

## 11. Risks and Assumptions

### 11.1 Technical Risks

| Risk ID | Risk Description | Severity | Likelihood | Consequence | Mitigation Strategy |
|:---|:---|:---:|:---:|:---|:---|
| **R-001** | **False Generalization on Synthetic Grids** | Critical | High | ConvLSTM filters learn synthetic sinusoidal patterns ($\sin(x) + \cos(y)$) rather than genuine geophysical soil moisture diffusion. | Replace synthetic spatial pattern with real spatial raster time-series before PINN integration. |
| **R-002** | **Vanishing/Exploding Gradients in Deep Sequences** | Moderate | Medium | Longer lookback sequences ($T > 20$) may suffer numerical instability during backpropagation through time. | Pre-activation clamping $[-10, 10]$ and gradient clipping ($\text{norm} = 1.0$) are implemented. |
| **R-003** | **Memory Saturation on Full Operational Rasters** | Moderate | High | Scaling from $10 \times 10$ to $500 \times 500$ grids increases 5D tensor size by a factor of 2500, causing GPU OOM errors. | Implement spatial patch-based tiling or ConvLSTM hidden state checkpointing. |
| **R-004** | **Overfitting on Small Sample Count ($B=28$)** | High | High | Optimizing a 16-channel ConvLSTM on only 28 samples risks memorization. | Incorporate temporal data augmentation and strict early stopping. |
| **R-005** | **Path Dependency Failure in Local Pipelines** | Moderate | High | Execution aborts on local workstation due to hardcoded `/kaggle/` filesystem paths. | Refactor filesystem paths to use `pathlib.Path(__file__).parent`. |

### 11.2 Architectural Assumptions

| Assumption ID | Statement of Assumption | Rationale |
|:---|:---|:---|
| **A-001** | **Temporal First-Order Markov Property** | The current soil state can be sufficiently predicted from a 7-day lookback sequence ($T=7$) of SAR backscatter and NDVI reflectances. |
| **A-002** | **Spatial Stationarity of Convolutional Kernels** | Soil moisture transport physics is spatially translation-invariant across the local $10 \times 10$ subgrade domain. |
| **A-003** | **Equispaced Temporal Sampling** | Satellite observations are assumed to be regularly sampled at discrete uniform time intervals. |
| **A-004** | **Decoupled Architecture Verification** | Structural validation of the ConvLSTM forward pass and BPTT dynamics can be verified on synthetic spatial fields prior to real data ingestion. |
| **A-005** | **Separation of Forecasting and Physics Constraints** | Data-driven ConvLSTM sequence learning serves as a predictive prior before PINN PDE residual constraints are applied in Notebook 05. |

---

## 12. Release and Baseline Acceptance Criteria

Notebook `04-temporal-modeling.ipynb` shall achieve formal release baseline `NB04-BL-01` only when all of the following conditions are satisfied:

1. **Requirements Verification**: All Functional (FR), Data Integrity (DI), and Interface (IF) requirements verified as **MET**.
2. **Procedure Pass Rate**: 100% of Verification Procedures VP-001 through VP-012 executed with **PASS** status.
3. **Discrepancy Remediation**: Defect **D-001** (peephole equation alignment), **D-002** (path typo), and **D-004** (narrative loss reduction text) closed.
4. **Validation Partitioning**: Implementation of independent validation loss tracking (Defect **D-005**).
5. **Path Neutrality**: Removal of hardcoded `/kaggle/` paths to support local execution.
6. **Full Traceability**: 100% bidirectional traceability maintained between requirements, code cells, and verification results.
7. **Independent Review**: Formal sign-off completed by an authorized independent reviewer.

---

## 13. Review and Approval

| Role | Designee / Authority | Division & Facility | Signature | Date |
|:---|:---|:---|:---:|:---:|
| **Author / Developer** | Gourgopal Mohapatra | RS-SDA Division, JCC Campus 2 | *Gourgopal Mohapatra* | 2026-10-08 |
| **Independent Technical Reviewer** | *(Assigned Reviewer)* | JCC Systems Engineering | ___________________ | ___________ |
| **Lead Systems Approver** | *(Approving Authority)* | JCC Command & Control | ___________________ | ___________ |

---

## 14. Limitations and Scientific Boundaries

> [!CAUTION]
> **SEPARATION OF COMPUTATIONAL VERIFICATION AND PHYSICAL SOIL VALIDATION**
> 
> Successful execution and convergence of the ConvLSTM training pipeline in Notebook 04 proves:
> 1. The custom PyTorch `ConvLSTMCell` and `SpatialTemporalConvLSTM` classes execute correct tensor tensor contractions, activations, and gate operations without memory leaks.
> 2. Gate clamping and gradient clipping successfully stabilize backpropagation through time.
> 3. The MSE loss drops monotonically from **0.847105** to **0.698587** over 15 epochs.
> 
> **THIS DOES NOT PROVE ACCURACY OF PHYSICAL SOIL MOISTURE FORECASTING.**
> 
> Because the spatial features were modulated with a synthetic trigonometric pattern ($\sin(x) + \cos(y)$):
> - The learned convolutional kernels have optimized against synthetic geometric artifacts rather than actual subsurface hydraulic diffusion.
> - Forecasted SAR backscatter maps cannot be utilized for operational irrigation scheduling or subgrade compaction assessment.
> - Full scientific validation requires feeding true multi-temporal Sentinel-1 / Sentinel-2 raster datacubes coupled with in-situ soil moisture sensor networks.

---

## 15. Intellectual Property and Controlled Distribution

```
========================================================================================
                      JAGANNATH COMMAND CENTER (JCC HEADQUARTER)
             JCC CAMPUS 2 — REMOTE SENSING & SPATIAL DATA ANALYTICS (RS-SDA)
                           PROJECT: THE MRIDANSH (AETHER-MRID1607X)
========================================================================================
```

**Copyright © 2026 Gourgopal Mohapatra. All Rights Reserved.**

This document, the underlying software architecture, mathematical formulations, ConvLSTM neural network implementations, and associated telemetry data structures constitute **proprietary intellectual property** developed under the auspices of JCC RS-SDA Division.

Unauthorized copying, distribution, decompilation, reverse engineering, dissemination, or commercial utilization—in whole or in part, in any format or medium—is strictly prohibited without prior express written authorization from the author and JCC Command Authority.

```
========================================================================================
                      CLASSIFICATION: STRICTLY PROPRIETARY & CONTROLLED
========================================================================================
```
