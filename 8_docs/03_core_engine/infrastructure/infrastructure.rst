.. _core_engine_infrastructure:

========================================================================================
Core Engine Infrastructure, Cryptographic Model Lock & Multi-Task Trainer
========================================================================================

:Document ID: DOC-MRID-03-INF-001
:Module: ``3_core_engine/`` (Infrastructure & Governance Modules)
:Author: Gourgopal Mohapatra
:Status: RELEASED / PRODUCTION AUDITED
:Date: 2026-11-05

.. contents:: Table of Contents
   :depth: 2
   :local:

Subsystem Overview
==================
The ``3_core_engine`` infrastructure modules govern runtime execution integrity, multi-task model optimization, and configuration parsing. This includes SHA256 cryptographic verification of model weights and frozen checkpoints (``model_lock.py``), multi-task training orchestration across spatiotemporal, physics, and uncertainty losses (``trainer.py``), and centralized YAML variable loading (``utils.py``). As mandated, the primary central engine entrypoint (``aether_engine.py``) is excluded from this document and governed by its master freeze specification.

Architectural Disclosures & Code Audit
======================================

.. warning::
   **ENGINEERING AUDIT DISCLOSURES**:

   1. **Cold-Start Verification Latency (D-ENG-INF-001)**:
      ``model_lock.py`` computes SHA256 digests over all model weights synchronously during initialization. On mechanical hard drives or throttled storage, this introduces a 2-second startup latency before flight inference can begin.
   2. **Static Loss Weighting Gradient Conflict (D-ENG-INF-002)**:
      ``trainer.py`` uses fixed scalar coefficients (:math:`\lambda_{\text{task}}, \lambda_{\text{physics}}, \lambda_{\text{uncertainty}}`). In early training epochs, large gradients from physical Richards residuals can destabilize the feature representations of the spatiotemporal ConvLSTM backbone.
   3. **Working Directory Dependency in Configuration (D-ENG-INF-003)**:
      ``ConfigLoader`` in ``utils.py`` relies on a relative path (``7_config/global_config.yaml``). Running scripts from subdirectories without setting ``cwd`` triggers immediate ``FileNotFoundError``.

Technical Specification & Formulations
======================================

Cryptographic Model Lock & Drift Prevention
-------------------------------------------
Ensures that all weights, calibration databases, and PINN models match their certified cryptographic signatures:

.. math::

   \text{Digest} = \text{SHA256}(\text{Binary Checkpoint Stream})

If computed digest differs from ``AETHER_MRID1607X_FREEZE_MANIFEST.json``, execution halts immediately with ``ModelIntegrityDriftError``.

Multi-Task Objective Function
-----------------------------
Simultaneously optimizes observation prediction accuracy, vadose zone physics, and uncertainty calibration:

.. math::

   \mathcal{L}_{\text{total}} = \mathcal{L}_{\text{MSE}}(\hat{\theta}, \theta_{\text{true}}) + \lambda_{\text{phys}} \mathcal{L}_{\text{Richards}}(\mathcal{R}) + \lambda_{\text{unc}} \mathcal{L}_{\text{NLL}}(\hat{\theta}, \sigma, \theta_{\text{true}})

Gradients are bounded using :math:`L_2` norm clipping:

.. math::

   \|\mathbf{g}\|_2 \le 1.0

Global System Configuration Loader
----------------------------------
``ConfigLoader`` parses and validates system execution parameters from ``7_config/global_config.yaml``, populating device contexts and deterministic random seeds.

Verification Results
====================
Validated via unit tests in ``tests/test_model_lock.py`` and ``tests/test_core_trainer_d06.py``:
- Verified deterministic SHA256 checksum calculation across binary artifacts.
- Verified instant exception triggering when weight files are tampered with.
- Verified multi-task loss backward pass and gradient clipping bound :math:`\le 1.0`.

Defect & Technical Debt Register
================================
.. list-table::
   :widths: 15 45 15 25
   :header-rows: 1

   * - Defect ID
     - Description
     - Severity
     - Remediation Plan
   * - D-ENG-INF-001
     - Synchronous SHA256 startup latency.
     - MEDIUM
     - Implement in-memory flag caching after initial successful boot.
   * - D-ENG-INF-002
     - Static multi-task loss weighting induces gradient interference.
     - MEDIUM
     - Integrate dynamic gradient projection (PCGrad / GradNorm).
   * - D-ENG-INF-003
     - Relative config file path sensitive to working directory.
     - LOW
     - Anchor file path to repo root via ``Path(__file__).resolve()``.
