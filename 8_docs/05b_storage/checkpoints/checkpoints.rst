.. _subsystem_05_checkpoints:

========================================================================================
Subsystem 05: Checkpoints Storage Specification & Cryptographic Vault
========================================================================================

:Engine: AETHER-MRID1607X
:Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
:Lead Architect: Gourgopal Mohapatra
:Status: FROZEN_OPERATIONAL_RELEASE_v1.0

Overview and Subsystem Mandate
==============================

The ``5_storage/checkpoints/`` repository constitutes the primary high-assurance persistence vault
and cryptographic model registry for the **AETHER-MRID1607X** earth observation and precision soil
intelligence platform. In the sequential 11-stage project architecture, ``5_storage`` serves as the
deterministic operational bridge linking experimental scientific notebooks (``1_notebooks_sandbox``)
and core engine computational modules (``3_core_engine``) with production execution orchestrators
(``5_pipelines``) and the mission cockpit (``6_dashboard``).

The primary objectives of the checkpoints subsystem are:

1. **Deterministic Reproducibility:** Ensure bit-level identical evaluation of neural network weights,
   empirical scaling parameters, and Bayesian filter states across distributed flight campaigns.
2. **Cryptographic Integrity:** Bind every physical checkpoint to an immutable SHA-256 signature
   verified by the master model lock protocol at system initialization.
3. **Architectural Tiering:** Formally isolate mission-critical operational spines (Tier 1) from
   distribution-free uncertainty layers (Tier 2) and targeted on-demand sensors (Tier 3).

Checkpoints Inventory & Provenance Catalog
==========================================

The checkpoint vault maintains 5 primary binary serialization archives (``.pt``) paired with
dedicated Markdown specification manifests:

.. list-table:: Physical Checkpoint Inventory & SHA-256 Signatures
   :widths: 22 10 38 30
   :header-rows: 1

   * - Filename
     - Size (Bytes)
     - SHA-256 Hash
     - Subsystem Role
   * - ``pinn_richards_model.pt``
     - 55,877
     - ``de1cd19c9993f0b35b4612c89d6b92a0553f95d5adaab695264d1be92b697e42``
     - Continuous 1D Richards PDE PINN solver enforcing mass conservation.
   * - ``ablation_study_checkpoint.pt``
     - 4,121
     - ``45e470be31073762525123ebde042a9b70f624b13259298bd23abd772f1c413b``
     - Marginal utility ladder and modular tiering decomposition (Configs A--H).
   * - ``generalization_evaluation_checkpoint.pt``
     - 5,467
     - ``5942df96df28caa108dfaafc5f46ed273284bf3dc82f5d178e1a37ae859c4fd9``
     - Multi-regime stress test metrics across 5 out-of-distribution regimes.
   * - ``hsi_experiment_checkpoint.pt``
     - 28,121
     - ``a50411e72cb882bb5cf05b3b416bb33f09e1fb6cfe92d50fd66c6a4a45538a3b``
     - 200 science channels + 10 PCA orthogonal feature projection weights.
   * - ``final_scientific_audit_checkpoint.pt``
     - 2,889
     - ``c3afec5540c17405b621b3926aba48394c543de26f669f3bbb7bc27afbceb4e7``
     - Master release certification and cross-subsystem hash verification matrix.

Deep Technical Specification
============================

Continuous Physics-Informed Neural Network (PINN) Checkpoint
------------------------------------------------------------

The ``pinn_richards_model.pt`` artifact encapsulates the parameters of a fully connected neural
network trained to satisfy the 1D mixed-form Richards equation with vertical gravitational potential:

.. math::

   \frac{\partial \theta}{\partial t} = \frac{\partial}{\partial z}\left( K(\theta) \left( \frac{\partial \psi}{\partial z} + 1 \right) \right)

Hydraulic conductivity :math:`K(\theta)` and matric potential :math:`\psi` are governed by the
van Genuchten constitutive model:

.. math::

   S_e = \left[ 1 + (\alpha |\psi|)^n \right]^{-m}, \quad K(\theta) = K_s S_e^l \left[ 1 - (1 - S_e^{1/m})^m \right]^2

Certified Loam soil parameters stored within the checkpoint:

* Residual volumetric water content :math:`\theta_r = 0.078\ \text{m}^3/\text{m}^3`
* Saturated volumetric water content :math:`\theta_s = 0.430\ \text{m}^3/\text{m}^3`
* van Genuchten inverse air-entry suction :math:`\alpha = 0.036\ \text{cm}^{-1}`
* Pore size index :math:`n = 1.56` (:math:`m = 1 - 1/n = 0.35897`)
* Saturated hydraulic conductivity :math:`K_s = 1.04\ \text{cm}/\text{hr}`

Empirical Verification Metrics:

* Final Total Loss: :math:`3.796 \times 10^{-3}`
* Final PDE Residual Loss: :math:`1.916 \times 10^{-7}`
* Relative PDE Residual Reduction: **72.30%** relative to unconstrained neural baselines.

Modular Tiering & Ablation Progression
--------------------------------------

The ``ablation_study_checkpoint.pt`` records empirical metrics across 8 cumulative configurations:

.. list-table:: 8-Configuration Incremental Ladder
   :widths: 12 28 14 14 14 18
   :header-rows: 1

   * - Config
     - Ingested Features
     - RMSE (m³/m³)
     - R² Score
     - Latency (ms)
     - Marginal ΔRMSE
   * - **Config A**
     - S2 Optical Alone (B2, B3, B4, B8)
     - 0.03557
     - -3.3130
     - 0.10 ms
     - Baseline
   * - **Config B**
     - + Sentinel-1 SAR (VV, VH)
     - 0.01961
     - -0.3115
     - 0.17 ms
     - -44.86%
   * - **Config C**
     - + Copernicus DEM (Slope, Elev)
     - 0.01496
     - +0.2370
     - 0.24 ms
     - -23.73%
   * - **Config D**
     - + ERA5 Weather (Precip, Temp)
     - 0.01074
     - +0.6070
     - 0.31 ms
     - -28.23%
   * - **Config E**
     - + ConvLSTM Temporal Hysteresis
     - 0.00887
     - +0.7315
     - 0.44 ms
     - -17.35%
   * - **Config F**
     - + Physics PINN (Richards PDE)
     - 0.00679
     - +0.8430
     - 0.57 ms
     - -23.53%
   * - **Config G**
     - + Stochastic EnKF (Bayesian)
     - **0.00485**
     - **+0.9199**
     - **0.80 ms**
     - **-28.57%**
   * - **Config H**
     - + Hyperspectral PRISMA (200 Bands)
     - 0.00338
     - +0.9612
     - 2.44 ms
     - -30.37%

**Operational Directive:** Config G is frozen as the operational flight backbone. Tier 3 (Config H) is
designated for on-demand scientific deployment due to its 3.05x latency penalty.

Master System Release Certification
-----------------------------------

The ``final_scientific_audit_checkpoint.pt`` encapsulates the master cryptographic release verification
executed during the grand scientific audit. Key certification parameters:

* **Richards Mass Conservation Error:** :math:`1.20 \times 10^{-4}`
* **EnKF Variance Contraction:** :math:`-69.47\%`
* **Conformal Empirical Coverage:** :math:`90.5\%` (Nominal target: :math:`90.0\%`)
* **Spatial Holdout Generalization Gap:** :math:`0.001286\ \text{m}^3/\text{m}^3` (Contract bound: :math:`\le 0.0030`)
* **Sub-Millisecond Execution Latency:** :math:`0.0116\ \text{ms/pixel}`

Brutally Honest Disclosures & Storage Caveats
=============================================

1. **PyTorch 2.6 WeightsUnpickler Compatibility Failure:**
   The ``hsi_experiment_checkpoint.pt`` artifact contains pickled NumPy array instances. Under PyTorch 2.6,
   calling ``torch.load(..., weights_only=True)`` fails with an unpickler security exception. Deserialization
   routines must supply ``weights_only=False`` or configure safe globals.
2. **Filesystem Duplication Hazard:**
   ``pinn_richards_model.pt`` is mirrored in ``5_storage/notebook_results/`` and ``data/processed/``.
   To prevent asynchronous state divergence, production pipelines must exclusively resolve weights
   against ``5_storage/checkpoints/pinn_richards_model.pt``.
3. **Non-Dimensional Coordinate Inversion:**
   The neural network operates over normalized coordinates :math:`\tilde{z} = z/200` and :math:`\tilde{t} = t/168`.
   Inference consumers must rescale input physical dimensions prior to tensor forwarding to prevent
   catastrophic saturation collapse.
4. **Homogeneous Lithology Constraint:**
   The frozen PINN weights enforce Loam constitutive parameters. Application to non-loam soil profiles
   introduces structural bias unless domain-specific adaptation heads are activated.

Traceable Requirements Matrix
=============================

.. list-table:: Subsystem 05 Traceable Requirements
   :widths: 20 20 40 20
   :header-rows: 1

   * - Requirement ID
     - Method
     - Specification Bound
     - Compliance Status
   * - **REQ-STOR-CKPT-01**
     - Inspection
     - Checkpoint SHA-256 hashes must strictly match the audit registry.
     - **PASSED**
   * - **REQ-STOR-CKPT-02**
     - Test
     - PINN residual loss must remain :math:`< 1.0 \times 10^{-6}` on Loam grids.
     - **PASSED**
   * - **REQ-STOR-CKPT-03**
     - Benchmark
     - Config G inference latency must not exceed :math:`1.0\ \text{ms}` per patch.
     - **PASSED** (0.80 ms)
   * - **REQ-STOR-CKPT-04**
     - Stress Audit
     - Spatial generalization gap must remain bounded :math:`\Delta \le 0.0030\ \text{m}^3/\text{m}^3`.
     - **PASSED** (0.00129)
   * - **REQ-STOR-CKPT-05**
     - Verification
     - Checkpoints must support CPU and CUDA device remapping.
     - **PASSED**
   * - **REQ-STOR-CKPT-06**
     - Inspection
     - 100% of binary checkpoints must possess corresponding Markdown manifests.
     - **PASSED**
   * - **REQ-STOR-CKPT-07**
     - Test
     - Autonomous fallback from Tier 3 to Tier 1 upon missing HSI data.
     - **PASSED**
   * - **REQ-STOR-CKPT-08**
     - Cryptography
     - Initialization must verify 7/7 persistent artifacts via SHA-256.
     - **PASSED**
