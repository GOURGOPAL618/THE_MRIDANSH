.. _module_04_temporal_modeling:

========================================================================
🛰️ Module 04: Temporal Sequence Modeling & Spatio-Temporal ConvLSTM
========================================================================

:Author: JCC Headquarter (RS-SDA Division) / Gourgopal Mohapatra
:Engine: AETHER-MRID1607X
:Module ID: MRIDANSH-MOD-TEMPORAL-04
:Notebook Source: ``1_notebooks_sandbox/04-temporal-modeling.ipynb``
:Verification Suite: ``tests/test_notebook_04_verification.py``
:Last Verification: Verified (7/7 Test Cases Passed)

.. contents:: Table of Contents
   :depth: 3
   :local:

Overview & Scientific Purpose
=============================

Module 04 executes the recurrent spatio-temporal dynamics engine of **THE MRIDANSH**. Operating downstream of data cleaning (Module 02) and spatial topographical meshing (Module 03), it structures telemetry observations into 5D spatio-temporal data cubes :math:`(B, T, C, H, W)` and implements a 2D Convolutional Long Short-Term Memory network (``SpatialTemporalConvLSTM``) capable of capturing simultaneous temporal lags and localized spatial diffusion patterns.

Key scientific features:
1. **5D Spatio-Temporal Tensor Generation**: Sliding window formulation over 35 temporal epochs producing :math:`30` sequence samples of shape :math:`(30, 5, 2, 20, 20)`.
2. **Topographic Feature Modulation**: 2D spatial texture synthesized by modulating SAR backscatter and NDVI signals with local DEM elevation and slope gradients.
3. **2D ConvLSTM Recurrent Architecture**: Internal convolutional gating (:math:`3 \times 3` kernel, :math:`16` hidden channels) enabling localized spatial state tracking across time.
4. **Temporal Horizon Sensitivity Ablation**: Systematic lookback horizon sweep (:math:`T \in \{3, 5, 7, 10\}`) proving the necessity of extended hydrological memory.
5. **Autoregressive Multi-Step Rollout**: 5-step recursive closed-loop forecasting for post-storm hydrological recession simulation.

Mathematical Formulations & Tensor Contracts
=============================================

5D Spatio-Temporal Tensor Assembly
----------------------------------

Given a sequence length :math:`T = 5` and a one-step-ahead prediction target lead :math:`\tau = 1`, sliding sequence windows are extracted across :math:`N = 35` temporal records:

.. math::

   B = N - T - \tau + 1 = 35 - 5 - 1 + 1 = 30 \text{ samples}

Spatial grid frames of dimensions :math:`H = 20, W = 20` are synthesized by modulating normalized telemetry with topographical gradients:

.. math::

   X_{b, t, 0, :, :} = \sigma^0_{VV}(t) + 0.10 \cdot \frac{\theta_{\text{slope}} - \bar{\theta}}{\sigma_\theta}

.. math::

   X_{b, t, 1, :, :} = \text{NDVI}(t) + 0.15 \cdot \frac{Z_{\text{DEM}} - \bar{Z}}{\sigma_Z}

where :math:`X \in \mathbb{R}^{30 \times 5 \times 2 \times 20 \times 20}` and target tensor :math:`Y \in \mathbb{R}^{30 \times 1 \times 2 \times 20 \times 20}`.

Chronological Partitioning
--------------------------

To strictly prevent temporal lookahead leakage, the 30 sequence batches are partitioned chronologically at ratio :math:`\rho = 0.80`:

.. math::

   B_{\text{train}} = \lfloor 30 \times 0.80 \rfloor = 24 \text{ samples}, \quad B_{\text{test}} = 6 \text{ samples}

ConvLSTM Cell Dynamics
----------------------

The recurrent cell replaces standard matrix multiplication with 2D spatial convolutions:

.. math::

   \mathbf{i}_t = \sigma\left(\mathbf{W}_{xi} * \mathbf{x}_t + \mathbf{W}_{hi} * \mathbf{h}_{t-1} + \mathbf{b}_i\right)

.. math::

   \mathbf{f}_t = \sigma\left(\mathbf{W}_{xf} * \mathbf{x}_t + \mathbf{W}_{hf} * \mathbf{h}_{t-1} + \mathbf{b}_f\right)

.. math::

   \tilde{\mathbf{c}}_t = \tanh\left(\mathbf{W}_{xc} * \mathbf{x}_t + \mathbf{W}_{hc} * \mathbf{h}_{t-1} + \mathbf{b}_c\right)

.. math::

   \mathbf{c}_t = \mathbf{f}_t \odot \mathbf{c}_{t-1} + \mathbf{i}_t \odot \tilde{\mathbf{c}}_t

.. math::

   \mathbf{o}_t = \sigma\left(\mathbf{W}_{xo} * \mathbf{x}_t + \mathbf{W}_{ho} * \mathbf{h}_{t-1} + \mathbf{b}_o\right)

.. math::

   \mathbf{h}_t = \mathbf{o}_t \odot \tanh(\mathbf{c}_t)

where :math:`*` represents 2D spatial convolution with reflection padding, and :math:`\odot` denotes Hadamard element-wise multiplication. In the unified implementation:
- Input channels: :math:`C_{\text{in}} + C_{\text{hidden}} = 2 + 16 = 18`
- Output channels: :math:`4 \times 16 = 64`
- Kernel: :math:`3 \times 3`, padding :math:`1`
- Cell parameter count: :math:`(18 \times 64 \times 9) + 64 = 10,432` weights.

Forecasting Head & Optimization
-------------------------------

The final hidden state :math:`\mathbf{h}_T \in \mathbb{R}^{B \times 16 \times 20 \times 20}` is mapped to the output spatial prediction :math:`\hat{\mathbf{y}}` via:

.. math::

   \hat{\mathbf{y}} = \operatorname{Conv2D}_{1 \times 1}\left(\operatorname{ReLU}\left(\operatorname{Conv2D}_{3 \times 3}(\mathbf{h}_T)\right)\right)

Optimization is conducted over 25 epochs with Adam (:math:`\text{lr}=10^{-3}`), gradient norm clipping (:math:`\text{max\_norm}=1.0`), and Mean Squared Error loss:

.. math::

   \mathcal{L} = \frac{1}{B \cdot C \cdot H \cdot W} \sum_{b=1}^B \sum_{c=1}^C \sum_{i=1}^H \sum_{j=1}^W \left( Y_{b,1,c,i,j} - \hat{Y}_{b,1,c,i,j} \right)^2

Loss reduction across 25 epochs is verified to exceed 10.0%.

Ablation Studies & Autoregressive Rollouts
==========================================

Lookback Horizon Sweep
----------------------

The sensitivity of temporal sequence modeling was audited across 4 sequence lookback horizons :math:`T \in \{3, 5, 7, 10\}`:

.. list-table:: Temporal Horizon Lookback Sensitivity
   :widths: 15 15 25 25 20
   :header-rows: 1

   * - Lookback Horizon (:math:`T`)
     - Usable Samples
     - Validation MSE
     - SAR MAE (:math:`\text{dB}`)
     - NDVI MAE
   * - :math:`T=3`
     - 32
     - 0.084120
     - 0.2412
     - 0.0381
   * - :math:`T=5`
     - 30
     - 0.061290
     - 0.1985
     - 0.0294
   * - :math:`T=7`
     - 28
     - 0.049810
     - 0.1742
     - 0.0251
   * - :math:`T=10`
     - 25
     - 0.038450
     - 0.1491
     - 0.0210

Extended lookback horizons (:math:`T=10`) systematically reduce validation error by :math:`54.3\%` compared to :math:`T=3`, demonstrating strong long-term hydrological autoregressive persistence.

Recursive Autoregressive Rollout
--------------------------------

A 5-step closed-loop autoregressive forecast was evaluated by iteratively feeding model predictions back into the input sequence buffer:

.. math::

   \hat{\mathbf{x}}_{t+k} = \mathcal{M}\left([\mathbf{x}_{t-T+k}, \dots, \hat{\mathbf{x}}_{t+k-1}]\right)

Verification confirmed zero NaN generation and physical boundary compliance (:math:`|\sigma^0_{VV}| < 50.0\text{ dB}`).

Generated Artifacts & Visualizations
====================================

The module generates 5 diagnostic plots and 3 persistent data artifacts in ``5_storage/notebook_results/notebook_04_temporal_modeling/``:

1. **Spatio-Temporal Sequence Slices (plot_01_spatiotemporal_tensor_slices.png)**: 2-row :math:`\times` 6-column spatial maps illustrating temporal progression of SAR and optical features.
2. **Loss Convergence & Spatial Prediction (plot_02_loss_convergence_and_spatial_prediction.png)**: Dual-panel plot of training/validation loss curves and predicted vs actual spatial fields.
3. **Temporal Horizon Ablation (plot_03_temporal_lookback_ablation.png)**: Sensitivity metrics across lookback lengths :math:`T \in \{3, 5, 7, 10\}`.
4. **Autoregressive Rollout Recession (plot_04_autoregressive_rollout_recession.png)**: Multi-step predicted spatial maps and mean trajectory tracking.
5. **Recurrent Hidden Activations (plot_05_recurrent_hidden_state_activations.png)**: 8-channel activation map grid from internal ConvLSTM hidden states.

Storage Files:
- ``convlstm_model_init.pt``: Model checkpoint containing trained weights, loss trajectories, and hyperparameters.
- ``temporal_latent_states.pt``: Serialized final recurrent states :math:`h_{\text{final}} \in \mathbb{R}^{6 \times 16 \times 20 \times 20}` and 5-step rollout tensor.
- ``temporal_sequence_ablation.json``: Machine-readable summary of lookback horizon metrics.

Verification & Test Coverage
============================

The verification suite ``tests/test_notebook_04_verification.py`` enforces 7 automated tests:

* ``test_01_no_python_scripts_in_notebook_dir``: Confirms zero Python scripts in sandbox directory.
* ``test_02_notebook_cell_structure_and_markdown_rules``: Validates alternating markdown/code layout (:math:`\ge 30` cells).
* ``test_03_all_code_cells_executed_with_zero_errors``: Audits all 14 code cells executed with 0 runtime errors.
* ``test_04_penultimate_and_ultimate_markdown_cells``: Audits presence of Executive Summary and Intellectual Property notices.
* ``test_05_storage_artifacts_and_plots_persisted``: Validates file presence and size thresholds (>50KB) for all 5 plots and model weights.
* ``test_06_model_checkpoint_and_latent_contracts``: Audits channel contracts (:math:`C_{\text{in}}=2, C_h=16, C_o=2`), loss reduction >10%, and valid hidden state shapes.
* ``test_07_temporal_ablation_and_loss_convergence``: Confirms ablation JSON schema and verifies :math:`\text{MSE}_{T=10} < \text{MSE}_{T=3}`.

Known Defects & Engineering Limitations
========================================

* **D-NB04-001 (Synthetic Spatial Texture Modulation)**: Due to 1D telemetry aggregation, 2D spatial frames are generated by modulating scalar time series with static DEM and slope maps rather than processing multi-temporal satellite imagery rasters.
* **D-NB04-002 (Small-Sample Overfitting Risk)**: The training dataset comprises only 24 sequences (:math:`B_{\text{train}}=24`) for a model with over 11,000 parameters, creating susceptibility to empirical overfitting without physical regularization.
* **D-NB04-003 (Compounding Autoregressive Rollout Errors)**: Recursive 5-step forecasting exhibits slight variance dampening over extended horizons due to unconstrained error accumulation.
* **D-NB04-004 (Linear Interpolation of Optical NaNs)**: Cloud-masked NDVI values are linearly interpolated in time, potentially smoothing over rapid vegetative or moisture responses.
