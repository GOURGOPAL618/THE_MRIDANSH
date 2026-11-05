.. _core_engine_models:

========================================================================================
Core Engine Deep Learning Neural Backbones & Latent Fusion
========================================================================================

:Document ID: DOC-MRID-03-MOD-001
:Module: ``3_core_engine/models/``
:Author: Gourgopal Mohapatra
:Status: RELEASED / PRODUCTION AUDITED
:Date: 2026-11-05

.. contents:: Table of Contents
   :depth: 2
   :local:

Subsystem Overview
==================
The ``3_core_engine/models`` subsystem houses the deep neural backbones of AETHER-MRID1607X. It encompasses 2D ConvLSTM spatiotemporal temporal sequence tracking, multi-modal cross-sensor latent fusion, and rule-based dynamic sensor dropout under severe optical cloud occlusion.

Architectural Disclosures & Code Audit
======================================

.. warning::
   **ENGINEERING AUDIT DISCLOSURES**:

   1. **Single-Sample BatchNorm Risk (D-ENG-MOD-001)**:
      ``ResidualConvBlock`` in ``latent_fusion.py`` uses standard ``nn.BatchNorm2d``. Running in ``.train()`` mode with batch size :math:`B=1` during operational flight sweeps results in invalid batch running statistics or division-by-zero crashes. The production pipeline must unconditionally set ``.eval()``.
   2. **GroupNorm Divisibility Invariant (D-ENG-MOD-002)**:
      ``ConvLSTMCell`` sets ``nn.GroupNorm(num_groups=4, num_channels=hidden_dim)``. Reconfiguring ``hidden_dim`` to values not divisible by 4 causes initialization exceptions.
   3. **Legacy Prototype Clutter (D-ENG-MOD-003)**:
      ``spatial_temporal_encoder.py`` is an obsolete prototype replaced by ``spatiotemporal_backbone.py`` and ``latent_fusion.py``, yet it remains in the codebase as dormant technical debt.
   4. **Empirical Exponent in Cloud Attenuation (D-ENG-MOD-004)**:
      The optical attenuation factor :math:`w_{\text{optical}} = (1 - \phi)^{1.5}` aggressively suppresses cirrus clouds, occasionally discarding usable ground reflectance.

Technical Formulations
=======================

Spatiotemporal ConvLSTM Backbone
--------------------------------
Maintains 2D spatial image coordinates while performing recurrent state transitions:

.. math::

   i_t = \sigma(W_{xi} * X_t + W_{hi} * H_{t-1} + b_i)

.. math::

   f_t = \sigma(W_{xf} * X_t + W_{hf} * H_{t-1} + b_f)

.. math::

   \tilde{c}_t = \tanh(W_{xc} * X_t + W_{hc} * H_{t-1} + b_c)

.. math::

   c_t = f_t \odot c_{t-1} + i_t \odot \tilde{c}_t

.. math::

   o_t = \sigma(W_{xo} * X_t + W_{ho} * H_{t-1} + b_o)

.. math::

   H_t = o_t \odot \tanh(c_t)

Gate activations are normalized across channels via ``GroupNorm(4, hidden_dim)`` prior to non-linear mapping.

Multi-Modal Latent Fusion Manifold
----------------------------------
Extracts dedicated spatial representations across 4 sensor families:
- Sentinel-1 SAR: :math:`2 \to 32` channels
- Sentinel-2 Optical: :math:`4 \to 32` channels
- Weather Covariates: :math:`3 \to 16` channels
- Copernicus DEM: :math:`4 \to 16` channels

Channels are concatenated (:math:`32 + 32 + 16 + 16 = 96`) and projected into a 64-channel residual latent manifold:

.. math::

   Z_{\text{latent}} = \text{Conv2D}_{96 \to 64}([Z_{\text{SAR}}, w_{\text{opt}} \cdot Z_{\text{Opt}}, Z_{\text{Weather}}, Z_{\text{DEM}}])

Dynamic Cloud Dropout Policy
----------------------------
Monitors cloud fraction :math:`\phi \in [0.0, 1.0]`:

.. math::

   w_{\text{optical}} = \max(0.0, 1.0 - \phi)^{1.5}, \quad w_{\text{sar}} = 1.0 + 0.5 \cdot \phi

When :math:`\phi > 0.80` (TOTAL_SAR_BACKBONE), :math:`w_{\text{optical}} = 0.0` and the model executes purely on microwave radar and vadose PINN dynamics, preserving :math:`RMSE \le 0.00712\,\text{m}^3/\text{m}^3`.

Verification Results
====================
Validated via unit tests in ``tests/test_day4_temporal_backbone.py``, ``tests/test_day4_latent_fusion.py``, and ``tests/test_day4_dropout_handler.py``:
- Verified ConvLSTM spatial grid preservation across sequence lengths :math:`T \in [1, 12]`.
- Verified GroupNorm gradient stability without NaN or exploding tensors.
- Verified 64-channel latent projection and bounded activation.
- Verified zero-leakage radar fallback under 100% simulated cloud occlusion.

Defect & Technical Debt Register
================================
.. list-table::
   :widths: 15 45 15 25
   :header-rows: 1

   * - Defect ID
     - Description
     - Severity
     - Remediation Plan
   * - D-ENG-MOD-001
     - Single-sample BatchNorm crash risk in ``ResidualConvBlock``.
     - HIGH
     - Replace with GroupNorm or enforce strict model ``.eval()`` mode.
   * - D-ENG-MOD-002
     - GroupNorm channel count must be divisible by 4.
     - MEDIUM
     - Calculate dynamic group count based on channel divisibility.
   * - D-ENG-MOD-003
     - Orphan legacy file ``spatial_temporal_encoder.py``.
     - LOW
     - Archive or deprecate the legacy encoder module.
   * - D-ENG-MOD-004
     - Optical cloud attenuation exponent tuned empirically.
     - LOW
     - Calibrate exponent against spectral transmissivity measurements.
