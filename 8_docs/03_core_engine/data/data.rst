.. _core_engine_data:

========================================================================================
Core Engine Data Adapter (Pipeline Snapshot Adapter)
========================================================================================

:Document ID: DOC-MRID-03-DATA-001
:Module: ``3_core_engine/data/``
:Author: Gourgopal Mohapatra
:Status: RELEASED / PRODUCTION AUDITED
:Date: 2026-11-05

.. contents:: Table of Contents
   :depth: 2
   :local:

Subsystem Overview
==================
The ``3_core_engine/data`` package bridges upstream Earth observation data pipelines with downstream deep learning models. Specifically, ``PipelineSnapshotAdapter`` maps heterogeneous NumPy dictionary snapshots from ``2_data_pipeline`` into standardized PyTorch tensors of shape :math:`(B, T, C, H, W)`.

Architectural Disclosures & Code Audit
======================================

.. warning::
   **ENGINEERING AUDIT DISCLOSURES**:

   1. **DataLoader Dimension Conflict (D-ENG-DAT-001)**:
      ``__getitem__`` embeds a synthetic batch dimension (:math:`B=1`) and time dimension (:math:`T=1`). When fed into a standard PyTorch ``DataLoader(batch_size > 1)``, an extra batch dimension is prepended, yielding an unhandled 6-dimensional tensor :math:`(B_{\text{loader}}, 1, 1, C, H, W)`.
   2. **Fixed Channel Dimension Invariant (D-ENG-DAT-002)**:
      Defaults to ``in_channels=5``. Contemporary flight campaigns employ 4 separate sensor bundles with varying channel counts, requiring explicit manual override during instantiation.
   3. **Terminal Encoding Sensitivity (D-ENG-DAT-004)**:
      Contains UTF-8 emoji strings in ``logging.info``, presenting a crash hazard on non-UTF-8 Windows console environments.

Technical Specification
=======================

PipelineSnapshotAdapter Class
-----------------------------
.. code-block:: python

   class PipelineSnapshotAdapter(torch.utils.data.Dataset):
       def __init__(self, snapshots: List[Dict[str, Any]], in_channels: int = 5):
           ...

Validation Rules:
- Array dimensionality: :math:`\text{rank}(fused\_tensor) = 3` with shape :math:`(H, W, C)`.
- Shape congruence: :math:`\text{shape}(fused\_validity\_mask) = \text{shape}(fused\_tensor)`.
- Channel count: :math:`C = in\_channels`.
- Numerical finiteness: :math:`\forall x \in fused\_tensor, \, x \notin \{\text{NaN}, \pm\infty\}`.

Layout Transformation
---------------------
Permutes NumPy channel-last layout :math:`(H, W, C)` to PyTorch tensor format:

.. math::

   (H, W, C) \xrightarrow{\text{transpose}(2, 0, 1)} (C, H, W) \xrightarrow{\text{unsqueeze}} (1, 1, C, H, W)

Helper Function
---------------
``snapshot_to_tensor(snapshot, in_channels=5)`` provides direct, zero-overhead conversion of individual snapshot dictionaries without manual dataset instantiation.

Verification & Test Evidence
============================
Validated via ``tests/test_core_integration_d05.py`` and ``tests/test_core_trainer_d06.py``:
- Verified valid tensor shape extraction :math:`(1, 1, 5, H, W)`.
- Verified immediate exception on missing dictionary keys.
- Verified NaN and infinite value detection.

Defect & Technical Debt Register
================================
.. list-table::
   :widths: 15 45 15 25
   :header-rows: 1

   * - Defect ID
     - Description
     - Severity
     - Remediation Plan
   * - D-ENG-DAT-001
     - Premature batch dimension injection inside ``__getitem__``.
     - HIGH
     - Return 4D tensor :math:`(T, C, H, W)` from dataset.
   * - D-ENG-DAT-002
     - Static default channel count of 5.
     - MEDIUM
     - Dynamically inspect length of ``channels`` list.
   * - D-ENG-DAT-003
     - Incomplete validity mask validation.
     - LOW
     - Validate boolean or binary integer mask values.
   * - D-ENG-DAT-004
     - Emojis in production logging statements.
     - LOW
     - Remove Unicode emojis from logging strings.
