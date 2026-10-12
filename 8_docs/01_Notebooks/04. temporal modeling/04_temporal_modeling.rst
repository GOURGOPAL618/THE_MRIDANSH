=====================================================================
THE MRIDANSH (AETHER-MRID1607X) - Notebook 04: Temporal Modeling
=====================================================================

:Project: THE MRIDANSH - Unified Soil State Estimation System
:Engine: AETHER-MRID1607X (Multi-Domain Soil Intelligence Engine)
:Notebook: ``04-temporal-modeling.ipynb``
:Sprint phase: Days 7-8 of the 18-Day Scientific Validation Sprint
:Division: RS-SDA (Remote Sensing & Spatial Data Analytics), JCC Campus 2 / JCC Headquarter
:Author / Maintainer: Gourgopal Mohapatra
:Copyright: (c) 2026 Gourgopal Mohapatra. All Rights Reserved.
:Document type: Technical Description and Software Design Specification
:Document status: Baseline Draft

.. contents:: Table of Contents
   :depth: 3
   :local:

1. Technical Overview
=====================

1.1 Objective
-------------
The primary technical objective of ``04-temporal-modeling.ipynb`` is to formulate,
construct, and validate a dynamic recurrent spatial-temporal sequence learning engine
using 2D Convolutional Long Short-Term Memory (``ConvLSTM``) networks. The software
transforms multi-modal Earth Observation (EO) time-series into 5-dimensional sliding-window
tensors :math:`(B, T, C, H, W)` and optimizes spatial convolutional recurrent gates to
forecast dynamic volumetric soil moisture distributions across forward temporal horizons.

1.2 System Context
------------------
Within **THE MRIDANSH** (*AETHER-MRID1607X*) architecture, raw telemetry is cleaned and
scaled in Notebook 02, while spatial terrain derivatives and graph Laplacians are
extracted in Notebook 03. Notebook 04 establishes the temporal dynamics core:

* **Upstream**: Ingests preprocessed, standardized multi-sensor telemetry tables
  (``preprocessed_telemetry.csv``) containing Sentinel-1 SAR backscatter and optical NDVI.
* **Core Engine**: Constructs 5D spatio-temporal sequence windows, implements custom
  numerically clamped ``ConvLSTMCell`` operators, conducts lookback horizon ablation
  studies (:math:`T \in \{3, 5, 7, 10\}`), and executes multi-epoch backpropagation through
  time (BPTT).
* **Downstream**: Emits initial and trained model checkpoints (``convlstm_model_init.pt``)
  which serve as recurrent priors for Physics-Informed Neural Network (PINN) PDE loss
  constraints in Notebook 05 and Ensemble Kalman Filter (EnKF) state transitions in Notebook 06.

1.3 Design Boundary
-------------------
The design of Notebook 04 is bounded as follows:

* **In Boundary**: Chronological sliding-window sequence slicing, 2D trigonometric spatial
  pattern synthesis, 5D tensor assembly, custom PyTorch 2D ``ConvLSTMCell`` with gate
  clamping, unrolled ``SpatialTemporalConvLSTM`` recurrent architecture, Xavier uniform
  parameter initialization, untrained forward pass benchmarking, lookback horizon ablation
  modeling, multi-epoch Adam optimization with gradient norm clipping, and artifact serialization.
* **Out of Boundary**: Spatial irregular graph message passing (governed by Notebook 03),
  hydrological PDE loss formulation (Richards equation, governed by Notebook 05),
  radiometric soil moisture inversion, and real-time cloud inference serving.

1.4 Relationship to Requirements
--------------------------------
This technical description details the software architecture, tensor mechanics, numerical
formulations, and component designs implementing the formal requirements specified in
``04_temporal_modeling_REQUIREMENTS.md``. Every mathematical gate transition, training
routine, and tensor shape described herein directly fulfills the verified requirements.
See Section 15 for complete requirement-to-design mapping.

2. Architecture
===============

2.1 Notebook Architecture
-------------------------
The software architecture is partitioned into two chronological research milestones across
23 notebook cells:

* **Milestone 1: 5D Spatio-Temporal Tensor Assembly & ConvLSTM Formulation (Sprint Day 7)**:
  Handles telemetry ingestion, spatial grid parameter configuration, sliding-window sequence
  extraction, custom ``ConvLSTMCell`` definition with pre-activation bounds, untrained
  forward-pass evaluation, baseline MSE logging, and initialization checkpoint export.
* **Milestone 2: Sequence Horizon Ablation & Spatio-Temporal Optimization (Sprint Day 8)**:
  Handles multi-horizon lookback evaluations (:math:`T \in \{3, 5, 7, 10\}`), multi-epoch
  neural network optimization using Adam and gradient norm clipping, loss trajectory logging,
  and comparative diagnostic visual rendering.

2.2 Processing Pipeline
-----------------------
The operational sequence pipeline executes through the following stages:

.. code-block:: text

   [preprocessed_telemetry.csv] (35 records)
               │
               ▼
   [Sliding Sequence Constructor] ◄─── [2D Spatial Pattern: sin(x) + cos(y)]
   (Window T = 7, Step = 1)
               │
               ├────────────────────────────────────────┐
               ▼                                        ▼
   [Input Tensor X: (28, 7, 2, 10, 10)]     [Target Tensor Y: (28, 2, 10, 10)]
               │                                        │
               ▼                                        │
   [ConvLSTMCell Gate Computations]                     │
   (Joint Conv2D, Clamped [-10, 10])                    │
               │                                        │
               ▼                                        │
   [Recurrent Hidden State h_t, c_t]                    │
               │                                        │
               ▼                                        │
   [1x1 Conv Prediction Head]                           │
               │                                        │
               ▼                                        │
   [Predicted Spatial Forecast Y_pred]                  │
               │                                        │
               ├────────────────────────────────────────┘
               ▼
   [Mean Squared Error Criterion: MSE(Y_pred, Y)]
               │
               ├────────────────────────────────────────► [Day 7: convlstm_model_init.pt]
               │
               ▼
   [15-Epoch Adam Optimizer + Gradient Clipping (1.0)]
               │
               ▼
   [Loss Convergence & Aerospace Visual Telemetry Plots]

2.3 Component Relationships
---------------------------
The internal software components interact via explicit object boundaries:

1. **Sequence Window Constructor**: Ingests tabular pandas Series and projects temporal
   scalars onto 2D spatial coordinate lattices, emitting high-dimensional PyTorch tensors.
2. **ConvLSTMCell Submodule**: Encapsulates 2D spatial convolutions across concatenated
   input and hidden channels, enforcing gate stability clamping and state transitions.
3. **SpatialTemporalConvLSTM Module**: Orchestrates the recurrent temporal unrolling loop
   across :math:`T` timesteps and projects the terminal hidden state through an affine
   :math:`1 \times 1` convolutional projection head.
4. **Optimization Loop**: Coordinates gradient backpropagation through time (BPTT),
   enforces gradient norm clipping at :math:`1.0`, and updates convolutional parameters.

2.4 Data Flow
-------------
The data flows across four structural representations:

1. **Tabular Scalar Domain**: Pandas DataFrame of shape :math:`(35, 4)` containing
   chronologically indexed observation records.
2. **5D Input Sequence Tensor**: PyTorch 32-bit floating point tensor of shape
   :math:`(B, T, C, H, W) = (28, 7, 2, 10, 10)`.
3. **4D Recurrent Hidden State**: Tensors :math:`h_t, c_t \in \mathbb{R}^{B \times C_{\text{hidden}} \times H \times W} = \mathbb{R}^{28 \times 16 \times 10 \times 10}`.
4. **4D Forecast Output Tensor**: Prediction tensor :math:`Y_{\text{pred}} \in \mathbb{R}^{B \times C_{\text{in}} \times H \times W} = \mathbb{R}^{28 \times 2 \times 10 \times 10}`.

3. Execution Flow
=================

3.1 Initialization
------------------
* Imports system dependencies (``sys``, ``os``, ``json``, ``numpy``, ``pandas``, ``torch``,
  ``torch.nn``, ``matplotlib.pyplot``).
* Configures inline rendering and project dark telemetry theme:
  background ``#000000``, axis borders ``#00FFCC`` (width 1.2), grid lines ``#1A3344``
  (dashed, alpha 0.5), and monospace font family.
* Sets deterministic random seeds: ``torch.manual_seed(42)`` and ``np.random.seed(42)``.
* Emits initialization confirmation banner.

3.2 Ingestion & Dimension Configuration
---------------------------------------
* Verifies file existence at path
  ``/kaggle/input/datasets/gourgopalmohapatra/preprocessed-telementary-dataset/preprocessed_telemetry.csv``.
* Ingests 35 records of tabular telemetry containing standardized SAR VV, NDVI, and DEM.
* Declares sequence and spatial grid constants:
  - ``SEQUENCE_LENGTH = 7`` (:math:`T = 7` timesteps / 1-week temporal window).
  - ``CHANNELS = 2`` (:math:`C = 2`, SAR VV and Optical NDVI).
  - ``HEIGHT = 10``, ``WIDTH = 10`` (:math:`10 \times 10` spatial sub-grid footprint).
* Emits verified tensor parameters to stdout.

3.3 2D Spatial Pattern Generation
---------------------------------
* Evaluates a continuous 2D spatial gradient template over normalized coordinate space
  :math:`[-1, 1] \times [-1, 1]` via:

  .. code-block:: python

     x = np.linspace(-1, 1, w)
     y = np.linspace(-1, 1, h)
     xx, yy = np.meshgrid(x, y)
     spatial_pattern = np.sin(xx) + np.cos(yy)

* Yields a :math:`10 \times 10` deterministic spatial pattern with values bounded within
  :math:`[-\sqrt{2}, \sqrt{2}]`.

3.4 5D Spatio-Temporal Sequence Sliding Window Assembly
-------------------------------------------------------
* Function ``create_spatial_temporal_sequences`` executes sliding sequence windowing:
  - Total sequence samples: :math:`N_{\text{samples}} = N_{\text{frames}} - T = 35 - 7 = 28`.
  - For each window :math:`i \in \{0, \dots, 27\}`:
    - Extracts :math:`T = 7` lookback rows (inputs) and row :math:`i + 7` (target).
    - Modulates SAR scalar by :math:`0.5 \times \text{spatial\_pattern}`.
    - Modulates NDVI scalar by :math:`0.2 \times \text{spatial\_pattern}`.
    - Stacks channels into :math:`(C, H, W) = (2, 10, 10)`.
    - Stacks timesteps into :math:`(T, C, H, W) = (7, 2, 10, 10)`.
* Emits input tensor :math:`X` of shape :math:`(28, 7, 2, 10, 10)` and target tensor :math:`Y`
  of shape :math:`(28, 2, 10, 10)`.

3.5 ConvLSTMCell & Network Class Definition
-------------------------------------------
* Instantiates custom ``ConvLSTMCell`` with joint input-hidden 2D convolution:
  :math:`\operatorname{Conv2D}(C_{\text{in}} + C_{\text{hidden}} \to 4 \cdot C_{\text{hidden}}, \text{kernel}=3, \text{pad}=1)`.
* Applies Xavier uniform initialization to convolutional weights and constant 0.0 to bias.
* Implements symmetrical gate pre-activation clamping to :math:`[-10.0, 10.0]`.
* Instantiates composite ``SpatialTemporalConvLSTM`` with :math:`C_{\text{hidden}} = 16`
  and a :math:`1 \times 1` convolutional prediction head mapping :math:`16 \to 2` channels.

3.6 Untrained Forward Pass & Diagnostic Baseline
------------------------------------------------
* Sanitizes input and target tensors via ``torch.nan_to_num(..., nan=0.0)``.
* Evaluates model in non-tracking mode (``convlstm_model.eval()``, ``torch.no_grad()``).
* Computes baseline untrained Mean Squared Error (MSE): **0.859975**.
* Emits Day 7 diagnostic banner.

3.7 Model Checkpoint Serialization
----------------------------------
* Ensures output directory ``/kaggle/working/data_processed/`` exists.
* Serializes model state dictionary and architectural hyperparameters into
  ``/kaggle/working/data_processed/convlstm_model_init.pt``.

3.8 Sequence Horizon Ablation Study
-----------------------------------
* Evaluates dynamic temporal lookback horizons :math:`T \in \{3, 5, 7, 10\}` via
  ``run_sequence_ablation()``.
* For each horizon, generates corresponding 5D sequence tensors and records untrained MSE loss:
  - :math:`T = 3 \implies \text{Tensor: } [32, 3, 2, 10, 10]`, Initial MSE: **0.85518**
  - :math:`T = 5 \implies \text{Tensor: } [30, 5, 2, 10, 10]`, Initial MSE: **0.87601**
  - :math:`T = 7 \implies \text{Tensor: } [28, 7, 2, 10, 10]`, Initial MSE: **0.88071**
  - :math:`T = 10 \implies \text{Tensor: } [25, 10, 2, 10, 10]`, Initial MSE: **0.86520**
* Emits Day 8 sequence horizon ablation summary to stdout.

3.9 Multi-Epoch Adam Optimization & Training Loop
-------------------------------------------------
* Re-instantiates ``SpatialTemporalConvLSTM(in_channels=2, hidden_channels=16)``.
* Configures Adam optimizer (learning rate :math:`\eta = 0.001`) and ``nn.MSELoss()``.
* Executes 15 training epochs in training mode (``model.train()``):
  - Clears parameter gradients: ``optimizer.zero_grad()``.
  - Evaluates forward prediction: ``predictions = convlstm_model(X_tensor)``.
  - Computes spatial MSE loss against ground truth target :math:`Y`.
  - Backpropagates error through time: ``loss.backward()``.
  - Clips parameter gradient norms: ``clip_grad_norm_(..., max_norm=1.0)``.
  - Updates weights: ``optimizer.step()``.
  - Records scalar loss history.
* Logs training trajectory: Epoch 01 (0.847105) :math:`\to` Epoch 15 (0.698587).

3.10 Convergence Evaluation & Spatial Prediction Rendering
----------------------------------------------------------
* Switches model to evaluation mode (``model.eval()``) and generates trained forecast tensor.
* Renders Aerospace Plot 2:
  - Subplot 1: 15-epoch loss convergence trajectory curve (cyan line with markers).
  - Subplot 2: Post-training spatial forecast field for SAR Channel 0 (viridis colormap).
  - Embedded diagnostic text box detailing initial loss, final loss, and percentage reduction.

4. Component Design
===================

4.1 Sequence Window Constructor
-------------------------------
* **Function**: Slices continuous time-series into overlapping chronological sequences.
* **Mechanism**:
  Given temporal array :math:`S \in \mathbb{R}^{N}`, spatial template :math:`P \in \mathbb{R}^{H \times W}`,
  and window length :math:`T`, the :math:`b`-th sample at step :math:`t \in \{0, \dots, T-1\}` is:

  .. math::

     F_{b, t}(x, y) = \alpha \cdot P(x, y) + S[b + t]

  Where :math:`\alpha` is a channel-specific scaling weight (:math:`0.5` for SAR, :math:`0.2` for NDVI).
  The prediction target is identically constructed at timestep :math:`b + T`.

4.2 ConvLSTMCell Engine
-----------------------
* **Function**: Implements spatial convolution within LSTM recurrent state transitions.
* **Mechanism**:
  Input tensor :math:`X_t \in \mathbb{R}^{B \times C_{\text{in}} \times H \times W}` and previous hidden state
  :math:`H_{t-1} \in \mathbb{R}^{B \times C_{\text{hidden}} \times H \times W}` are concatenated along the
  channel dimension into :math:`[X_t, H_{t-1}] \in \mathbb{R}^{B \times (C_{\text{in}} + C_{\text{hidden}}) \times H \times W}`.

  A single joint 2D convolution evaluates all four recurrent gates simultaneously:

  .. math::

     \operatorname{Gates} = \operatorname{Conv2D}([X_t, H_{t-1}]) \in \mathbb{R}^{B \times 4C_{\text{hidden}} \times H \times W}

  To eliminate floating-point overflow during recurrent exponentiations, gates are clamped:

  .. math::

     \operatorname{Gates}_{\text{clamped}} = \operatorname{clamp}(\operatorname{Gates}, -10.0, 10.0)

  The clamped tensor is partitioned into four channel chunks of size :math:`C_{\text{hidden}}`:
  Input gate :math:`i`, Forget gate :math:`f`, Output gate :math:`o`, and Candidate state :math:`g`.

  State updates proceed via Hadamard element-wise operations:

  .. math::

     i_t = \sigma(i), \quad f_t = \sigma(f), \quad o_t = \sigma(o), \quad g_t = \tanh(g)

  .. math::

     C_t = f_t \circ C_{t-1} + i_t \circ g_t

  .. math::

     H_t = o_t \circ \tanh(C_t)

4.3 SpatialTemporalConvLSTM Recurrent Network
--------------------------------------------
* **Function**: Unrolls sequence iterations and maps final hidden states to physical channels.
* **Mechanism**:
  Zero-initializes :math:`H_0 = \mathbf{0}` and :math:`C_0 = \mathbf{0}`. Iterates sequentially
  across :math:`t = 0, \dots, T-1`. The terminal hidden state :math:`H_T` is passed through a
  pointwise :math:`1 \times 1` convolutional prediction head:

  .. math::

     Y_{\text{pred}} = \operatorname{Conv2D}_{1 \times 1}(H_T) \in \mathbb{R}^{B \times C_{\text{in}} \times H \times W}

4.4 Optimization & Gradient Clipping Controller
-----------------------------------------------
* **Function**: Minimizes spatial prediction error across temporal sequences.
* **Mechanism**:
  Uses the standard Adam adaptive gradient algorithm with parameter updates governed by:

  .. math::

     \theta_{k+1} = \theta_k - \eta \cdot \frac{\hat{m}_k}{\sqrt{\hat{v}_k} + \epsilon}

  Prior to updating parameters, gradient norm clipping enforces:

  .. math::

     g \leftarrow g \cdot \min\left(1, \frac{\text{max\_norm}}{\|g\|_2}\right) \quad \text{where } \text{max\_norm} = 1.0

4.5 Persistence & Checkpoint Handler
------------------------------------
* **Function**: Serializes model checkpoints and architecture metadata.
* **Mechanism**: Utilizes PyTorch native serialization (``torch.save``) to write binary
  state dictionaries and architectural constants to disk.

5. Data Structures
==================

5.1 Input Schema
----------------
Table ``preprocessed_telemetry.csv`` input columns:

.. list-table::
   :header-rows: 1
   :widths: 25 20 20 35

   * - Column
     - Type
     - Unit
     - Role in Sequence
   * - ``timestamp``
     - string
     - UTC ISO
     - Chronological sorting verification
   * - ``s1_vv_lee_zscore``
     - float64
     - standard units
     - Channel 0 scalar time-series
   * - ``ndvi_minmax``
     - float64
     - [0, 1]
     - Channel 1 scalar time-series
   * - ``dem_elevation_m``
     - float64
     - meters
     - In-situ topographic baseline

5.2 Intermediate Tensors
------------------------
1. **Spatial Pattern Matrix** (``spatial_pattern``): NumPy float64 array of shape :math:`(10, 10)`.
2. **5D Sequence Input Tensor** (``X_tensor``): PyTorch float32 tensor of shape
   :math:`(28, 7, 2, 10, 10)`.
3. **4D Sequence Target Tensor** (``Y_tensor``): PyTorch float32 tensor of shape
   :math:`(28, 2, 10, 10)`.
4. **Recurrent Hidden Tensor** (``h_t``): PyTorch float32 tensor of shape :math:`(28, 16, 10, 10)`.
5. **Recurrent Cell Tensor** (``c_t``): PyTorch float32 tensor of shape :math:`(28, 16, 10, 10)`.
6. **Pre-activation Gate Tensor** (``gates``): PyTorch float32 tensor of shape :math:`(28, 64, 10, 10)`.

5.3 Output Schema
-----------------
1. **Predicted Spatial Forecast** (``y_pred_tensor``): PyTorch float32 tensor of shape
   :math:`(28, 2, 10, 10)` representing 2-channel forecasts across the :math:`10 \times 10` sub-grid.

5.4 Checkpoint Schema
---------------------
Archive ``convlstm_model_init.pt`` serialized dictionary keys:

* ``'model_state_dict'``: PyTorch state dictionary containing:
  - ``conv_lstm.conv.weight``: Shape :math:`(64, 18, 3, 3)`
  - ``conv_lstm.conv.bias``: Shape :math:`(64,)`
  - ``head.weight``: Shape :math:`(2, 16, 1, 1)`
  - ``head.bias``: Shape :math:`(2,)`
* ``'seq_len'``: Integer constant :math:`7`.
* ``'channels'``: Integer constant :math:`2`.
* ``'grid_dim'``: Tuple of integers :math:`(10, 10)`.

6. Algorithms and Methods
=========================

6.1 5D Sliding-Window Tensor Construction
-----------------------------------------
Given scalar sequences :math:`s_1(t)` (SAR) and :math:`s_2(t)` (NDVI) of length :math:`N`,
the sliding window algorithm iterates index :math:`i` from :math:`0` to :math:`N - T - 1`:

.. code-block:: text

   Sample i = 0: Inputs [0, 1, ..., 6]   Target [7]
   Sample i = 1: Inputs [1, 2, ..., 7]   Target [8]
   ...
   Sample i = 27: Inputs [27, 28, ..., 33] Target [34]

Each scalar is converted into a 2D spatial raster by adding a weighted spatial gradient
matrix:

.. math::

   R_{1}(x, y, t) = 0.5 \cdot (\sin(x) + \cos(y)) + s_1(t)

.. math::

   R_{2}(x, y, t) = 0.2 \cdot (\sin(x) + \cos(y)) + s_2(t)

Yielding total sample count :math:`B = 35 - 7 = 28`.

6.2 2D Convolutional Recurrent Gate Mechanics
---------------------------------------------
Standard LSTMs use matrix vector multiplications which destroy spatial neighborhood topologies.
The ``ConvLSTMCell`` replaces fully connected layers with 2D convolutions:

* Convolution Kernel: :math:`3 \times 3` spatial window.
* Spatial Padding: :math:`\text{padding} = 1` ensures output height and width match input height and width:

  .. math::

     H_{\text{out}} = \left\lfloor \frac{H_{\text{in}} + 2 \times 1 - 3}{1} \right\rfloor + 1 = H_{\text{in}}

* Channel Expansion: Input channels :math:`(C_{\text{in}} + C_{\text{hidden}}) = 2 + 16 = 18`
  mapped to :math:`4 \times 16 = 64` gate channels.

6.3 Numerical Stability Clamping
--------------------------------
In deep recurrent networks unrolled across time, pre-activation values in gates can grow
unbounded prior to saturation. Extremely large positive or negative values cause:

* Exponent overflow in :math:`\sigma(x) = \frac{1}{1 + e^{-x}}`.
* Gradient vanishing in saturated regimes of :math:`\tanh(x)`.

The software injects hard numerical clamping:

.. math::

   \text{clamp}(z, -10.0, 10.0) = \max(-10.0, \min(10.0, z))

Ensuring all exponentials evaluate within :math:`[e^{-10}, e^{10}] \approx [4.54 \times 10^{-5}, 22026.4]`,
completely eliminating NaN propagation.

6.4 Backpropagation Through Time (BPTT)
---------------------------------------
Gradients of the spatial MSE loss :math:`\mathcal{L}` are backpropagated through all :math:`T`
temporal cell unrollings:

.. math::

   \frac{\partial \mathcal{L}}{\partial W_{\text{conv}}} = \sum_{t=1}^{T} \frac{\partial \mathcal{L}}{\partial H_t} \cdot \frac{\partial H_t}{\partial W_{\text{conv}}}

Where spatial derivatives preserve 2D convolutional filter topologies.

6.5 Gradient Norm Clipping
--------------------------
To stabilize parameter updates across recurrent unrollings, parameter gradients are scaled
if the global Euclidean norm exceeds :math:`1.0`:

.. math::

   \|g\|_2 = \sqrt{\sum_{p \in \Theta} \|g_p\|_2^2}

.. math::

   g \leftarrow \frac{g}{\max(1.0, \|g\|_2)}

6.6 Sequence Horizon Ablation Methodology
-----------------------------------------
Lookback sensitivity is evaluated by programmatically varying sequence horizon :math:`T \in \{3, 5, 7, 10\}`:
* As :math:`T` increases, the lookback context broadens, but sample size :math:`B = 35 - T` decreases.
* The ablation function instantiates independent model copies, evaluates untrained forward passes,
  and logs the trade-off between tensor volume and initial loss.

7. Interfaces
-------------

7.1 Input Interfaces
--------------------
* **Primary Path**: ``/kaggle/input/datasets/gourgopalmohapatra/preprocessed-telementary-dataset/preprocessed_telemetry.csv``.
* **Format**: Comma-Separated Values (CSV), UTF-8.
* **Failure Mode**: Logs fallback notification and generates synthetic in-memory stream.

7.2 Output Interfaces
---------------------
* **Primary Path**: ``/kaggle/working/data_processed/convlstm_model_init.pt``.
* **Format**: PyTorch binary serialized checkpoint.

7.3 File Interfaces
-------------------
* ``convlstm_model_init.pt``:
  - File size: ~44.6 KB.
  - Serialization engine: ``torch.save``.
  - Deserialization engine: ``torch.load``.

7.4 Downstream PINN/EnKF Interfaces
-----------------------------------
* **Consumer**: Notebook 05 (``05-physics-validation.ipynb``).
* **Interface Contract**: Notebook 05 loads ``convlstm_model_init.pt`` to initialize the
  spatio-temporal neural backbone before attaching Richards equation PDE loss functions.

8. Configuration
----------------

8.1 Constants
-------------
* ``SEQUENCE_LENGTH = 7``: Default sliding window horizon in timesteps.
* ``CHANNELS = 2``: Channel depth (SAR VV, Optical NDVI).
* ``HEIGHT = 10``: Spatial grid height in pixels.
* ``WIDTH = 10``: Spatial grid width in pixels.
* ``HIDDEN_CHANNELS = 16``: Number of convolutional feature channels in ConvLSTM cell.
* ``KERNEL_SIZE = 3``: Spatial convolution kernel diameter.
* ``LEARNING_RATE = 0.001``: Adam optimizer learning rate.
* ``EPOCHS = 15``: Optimization training epoch limit.
* ``GRAD_CLIP_MAX_NORM = 1.0``: Maximum Euclidean threshold for gradient norm clipping.

8.2 Environment
---------------
* Python 3.10+ runtime.
* Linux x86_64 container runtime (Kaggle kernel environment).
* Computation device: PyTorch CPU or CUDA GPU.

8.3 Runtime Configuration
-------------------------
* ``%matplotlib inline``: Inline rendering engine.
* Matplotlib stylesheet: ``dark_background``.
* Plotting theme:
  - ``axes.edgecolor``: ``#00FFCC``
  - ``axes.linewidth``: 1.2
  - ``grid.color``: ``#1A3344``
  - ``grid.linestyle``: ``--``
  - ``grid.alpha``: 0.5
  - ``font.family``: ``monospace``

8.4 Dependencies
----------------
* ``numpy >= 1.24.0``
* ``pandas >= 2.0.0``
* ``torch >= 2.0.0``
* ``matplotlib >= 3.7.0``

9. Error Handling
-----------------

9.1 Absent Input File
---------------------
When ``preprocessed_telemetry.csv`` is not detected on the filesystem, the script executes
an inline synthetic generator:

.. code-block:: python

   dates = pd.date_range(start="2026-08-01", end="2026-09-07", periods=35)
   df_prep = pd.DataFrame({
       "timestamp": dates,
       "s1_vv_lee_zscore": np.random.normal(0, 1, 35),
       "ndvi_minmax": np.random.uniform(0.2, 0.8, 35),
       "dem_elevation_m": 18.5
   })

Preventing unhandled execution crashes.

9.2 Gate Activation Overflow
----------------------------
Unclamped gate activations in recurrent convolutions can generate large exponentials.
The explicit clamp:

.. code-block:: python

   gates = torch.clamp(gates, min=-10.0, max=10.0)

Guarantees floating-point stability across all gate projections.

9.3 Exploding Gradients
-----------------------
During backpropagation through time, recurrent weight updates can destabilize.
The software enforces:

.. code-block:: python

   torch.nn.utils.clip_grad_norm_(convlstm_model.parameters(), max_norm=1.0)

Preventing NaN weights during training.

9.4 NaN Sanitization
--------------------
To prevent upstream data anomalies from propagating into model tensors, inputs are explicitly
purged of missing values:

.. code-block:: python

   X_tensor = torch.nan_to_num(X_tensor, nan=0.0)
   Y_tensor = torch.nan_to_num(Y_tensor, nan=0.0)

10. Generated Artifacts
=======================

10.1 convlstm_model_init.pt
---------------------------
* **Path**: ``/kaggle/working/data_processed/convlstm_model_init.pt``
* **Size**: ~44.6 KB.
* **Content**: PyTorch state dictionary with weights for 2D convolutional recurrent gates
  and :math:`1 \times 1` prediction head, along with structural sequence dimensions.

10.2 Diagnostic Plot Suite
--------------------------
* **Aerospace Plot 1**: Subplot 1 (Target Ground Truth SAR Channel) and Subplot 2
  (ConvLSTM Temporal Forecast Untrained) with embedded telemetry text.
* **Aerospace Plot 2**: Subplot 1 (15-Epoch MSE Loss Convergence Trajectory) and Subplot 2
  (Post-Training Spatial Forecast SAR Map) with quantitative convergence reduction metrics.

11. Reproducibility
===================

11.1 Random Seeds
-----------------
Deterministic execution is enforced across PyTorch and NumPy in Cell 02:

.. code-block:: python

   torch.manual_seed(42)
   np.random.seed(42)

11.2 Environment & Hardware Invariance
--------------------------------------
Under identical package versions and IEEE-754 floating-point operations, re-execution
produces bit-identical tensors and loss convergence histories.

11.3 Deterministic Numerical Invariants
---------------------------------------
Under seeds 42, the following exact numerical invariants are guaranteed:

* Input Tensor Shape: Exactly ``torch.Size([28, 7, 2, 10, 10])``.
* Target Tensor Shape: Exactly ``torch.Size([28, 2, 10, 10])``.
* Untrained Baseline MSE Loss: Exactly **0.859975**.
* Sequence Horizon Initial Losses:
  - :math:`T = 3`: **0.85518**
  - :math:`T = 5`: **0.87601**
  - :math:`T = 7`: **0.88071**
  - :math:`T = 10`: **0.86520**
* Optimization Trajectory Losses:
  - Epoch 01: **0.847105**
  - Epoch 03: **0.814763**
  - Epoch 06: **0.769809**
  - Epoch 09: **0.733365**
  - Epoch 12: **0.714874**
  - Epoch 15: **0.698587**

12. Performance Characteristics
===============================

12.1 Execution Time Profile
---------------------------
Measured on standard 2-core x86_64 CPU runtime:

* Environment Initialization (Cell 02): :math:`< 0.5\text{ s}`
* Sequence Tensor Assembly (Cell 06): :math:`< 0.1\text{ s}`
* Model Instantiation & Initialization (Cell 08): :math:`< 0.05\text{ s}`
* Untrained Forward Pass & Benchmark (Cell 10): :math:`< 0.1\text{ s}`
* Checkpoint Serialization (Cell 14): :math:`< 0.1\text{ s}`
* Sequence Horizon Ablation Study (Cell 16): :math:`\approx 0.8\text{ s}`
* 15-Epoch Optimization Loop (Cell 18): :math:`\approx 2.5\text{ s}`
* Diagnostic Plot Rendering (Cells 12, 20): :math:`\approx 1.0\text{ s}`
* **Total End-to-End Execution**: :math:`< 5.2\text{ s}`.

12.2 Memory Footprint
---------------------
* Peak RAM Consumption: :math:`< 220\text{ MB}` above base Python kernel.
* Tensor Allocations:
  - Input Tensor :math:`X`: :math:`28 \times 7 \times 2 \times 10 \times 10 \times 4\text{ bytes} \approx 156.8\text{ KB}`.
  - Target Tensor :math:`Y`: :math:`28 \times 2 \times 10 \times 10 \times 4\text{ bytes} \approx 22.4\text{ KB}`.
  - Model Parameters: ~10,500 parameters :math:`\times 4\text{ bytes} \approx 42\text{ KB}`.

12.3 Tensor Dimensions and Volumes
----------------------------------
* Input Telemetry File: :math:`\approx 9.3\text{ KB}`.
* Serialized Model Weights: :math:`\approx 44.6\text{ KB}`.

13. Implementation Notes
========================

13.1 Current Implementation State
---------------------------------
The notebook constitutes a verified, operational baseline for spatial-temporal sequence
modeling. All tensor operations, forward passes, convolutional recurrent gate operations,
and optimization iterations execute cleanly without errors.

13.2 Known Implementation Constraints
-------------------------------------
1. **Mathematical Peephole Omission**: Markdown header formulas state peephole connections
   (:math:`W_{ci} \circ C_{t-1}`), but code implements standard ConvLSTM without peephole
   weights.
2. **Dataset Path Typo**: Ingestion specifies ``preprocessed-telementary-dataset``
   (misspelling ``telemetry``).
3. **Synthetic Spatial Injection**: Scalar time-series are modulated with synthetic trigonometric
   patterns (:math:`\sin(x) + \cos(y)`) to form 2D grids rather than reading real 2D rasters.
4. **Narrative Text Loss Discrepancy**: Summary text mentions a 19.7% reduction
   (:math:`0.8701 \to 0.6985`), whereas the logged run achieved a 17.5% reduction
   (:math:`0.8471 \to 0.6986`).
5. **Lack of Validation Split**: Training optimizes all 28 sequence samples without an
   independent validation split.
6. **Hardcoded Kaggle Paths**: Script relies on ``/kaggle/input/`` and ``/kaggle/working/``.

13.3 Forward Path to Production
-------------------------------
* Align markdown formulas with code implementation.
* Ingest true 2D raster time-series stacks from Sentinel-1 / Sentinel-2 GeoTIFFs.
* Incorporate 80/20 train/validation split with early stopping.
* Migrate filesystem paths to configurable environment variables.

14. Technical Limitations
=========================

14.1 Current Limitations
------------------------
* **Small Sample Regime**: Optimization evaluates on 28 sliding sequence samples, limiting
  generalization capacity without regularization.
* **Rigid Spatial Grid**: The convolutional architecture strictly operates on regular
  orthogonal 2D grids and cannot directly ingest irregular graph vertices without rasterization.
* **Fixed Lookback Horizon**: The trained model requires a fixed sequence length of 7
  timesteps during inference.

14.2 Synthetic Spatial Domain Boundary
--------------------------------------
While the ConvLSTM tensor contractions and backpropagation mechanics are verified,
**the learned convolutional features reflect synthetic trigonometric patterns rather than
genuine subsurface hydraulic transport dynamics**.

14.3 Temporal Sequence Horizon Boundary
---------------------------------------
Ablation confirms lookback horizons :math:`T > 10` rapidly decrease available sequence samples
(:math:`B = 35 - T`), indicating that operational multi-month sequence modeling requires
substantially longer satellite observation archives (> 100 timesteps).

15. Requirement Implementation Mapping
======================================

The implementation described across this technical document directly fulfills the
formal software requirements established in ``04_temporal_modeling_REQUIREMENTS.md``:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Requirement ID
     - Requirement Description
     - Implementing Design Section
   * - **FR-001**
     - Telemetry ingestion verification and fallback
     - Section 3.2, Section 7.1, Section 9.1
   * - **FR-002**
     - Sequence constants configuration (:math:`T=7, C=2, H=10, W=10`)
     - Section 3.2, Section 8.1
   * - **FR-003**
     - 2D trigonometric spatial pattern generation
     - Section 3.3, Section 4.1, Section 6.1
   * - **FR-004**
     - Sliding sequence window transformation
     - Section 3.4, Section 4.1, Section 6.1
   * - **FR-005**
     - 5D and 4D tensor shape contracts (:math:`X` and :math:`Y`)
     - Section 3.4, Section 5.2, Section 11.3
   * - **FR-006**
     - Custom ``ConvLSTMCell`` with gate clamping
     - Section 3.5, Section 4.2, Section 6.2, Section 6.3
   * - **FR-007**
     - Recurrent ``SpatialTemporalConvLSTM`` architecture
     - Section 3.5, Section 4.3, Section 6.2
   * - **FR-008**
     - Untrained forward pass & baseline MSE diagnostic
     - Section 3.6, Section 11.3
   * - **FR-009**
     - Model checkpoint serialization
     - Section 3.7, Section 4.5, Section 10.1
   * - **FR-010**
     - Sequence horizon ablation (:math:`T \in \{3, 5, 7, 10\}`)
     - Section 3.8, Section 6.6, Section 11.3
   * - **FR-011**
     - 15-epoch Adam optimization with gradient clipping
     - Section 3.9, Section 4.4, Section 6.5
   * - **FR-012**
     - Monotonic loss history recording
     - Section 3.9, Section 11.3, Section 12.1
   * - **FR-013**
     - Diagnostic plotting suite (Plots 1 and 2)
     - Section 3.10, Section 8.3, Section 10.2
   * - **DI-001**
     - Chronological non-leaking window slicing
     - Section 3.4, Section 6.1
   * - **DI-002**
     - Batch sample count conservation (:math:`B = N - T`)
     - Section 3.4, Section 6.1
   * - **DI-003**
     - Spatial dimension preservation (:math:`H=10, W=10`)
     - Section 3.5, Section 4.2, Section 6.2
   * - **DI-004**
     - NaN/Inf sanitization via ``torch.nan_to_num``
     - Section 3.6, Section 9.4
   * - **DI-005**
     - Zero initial hidden and cell state tensors
     - Section 3.5, Section 4.3
   * - **IF-001**
     - Telemetry path existence check with fallback
     - Section 3.2, Section 7.1, Section 9.1
   * - **IF-002**
     - Automatic export directory initialization
     - Section 3.7, Section 7.2
   * - **IF-003**
     - Checkpoint dictionary schema contract
     - Section 5.4, Section 10.1
   * - **IF-004**
     - Prediction and target tensor shape parity
     - Section 3.6, Section 5.3
   * - **UQ-001**
     - Pre-activation gate clamping :math:`[-10.0, 10.0]`
     - Section 3.5, Section 4.2, Section 6.3, Section 9.2
   * - **UQ-002**
     - Gradient norm clipping at :math:`\text{max\_norm} = 1.0`
     - Section 3.9, Section 4.4, Section 6.5, Section 9.3
   * - **UQ-003**
     - Quantitative diagnostic displays on visual plots
     - Section 3.6, Section 3.10, Section 10.2
   * - **NF-001**
     - Deterministic seeds (PyTorch 42, NumPy 42)
     - Section 3.1, Section 11.1
   * - **NF-002**
     - Unattended headless execution
     - Section 2.1, Section 12.1
   * - **NF-003**
     - Uniform dark telemetry styling on generated figures
     - Section 3.1, Section 8.3, Section 10.2
   * - **NF-004**
     - Lightweight memory footprint (< 500 MB)
     - Section 12.2
