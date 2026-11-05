.. _core_engine_physics:

========================================================================================
Core Engine Vadose Zone Soil Physics & PINN Solver
========================================================================================

:Document ID: DOC-MRID-03-PHY-001
:Module: ``3_core_engine/physics/``
:Author: Gourgopal Mohapatra
:Status: RELEASED / PRODUCTION AUDITED
:Date: 2026-11-05

.. contents:: Table of Contents
   :depth: 2
   :local:

Subsystem Overview
==================
The ``3_core_engine/physics`` package integrates deterministic hydrodynamic soil physics with neural representations. It incorporates analytical van Genuchten retention curves, Mualem unsaturated hydraulic conductivity functions, and a continuous space-time Physics-Informed Neural Network (PINN) enforcing Richards equation mass conservation.

Architectural Disclosures & Code Audit
======================================

.. warning::
   **ENGINEERING AUDIT DISCLOSURES**:

   1. **Prototype Lateral Diffusion Shortcut (D-ENG-PHY-001)**:
      ``richards_engine.py`` implements a simplified 2D spatial diffusion solver using Sobel image convolutions rather than vertical 1D soil columns. It completely omits the gravitational elevation gradient :math:`+\frac{\partial K}{\partial z}`. The production system utilizes ``pinn_richards.py`` for true physical conservation.
   2. **Autograd Memory Footprint (D-ENG-PHY-002)**:
      Evaluating continuous PDE residuals :math:`\mathcal{R}_{\text{Richards}}` requires 2nd-order autograd graph creation (``torch.autograd.grad(create_graph=True)``), which demands substantial temporary VRAM allocations.
   3. **Static USDA Pedotransfer Parameters (D-ENG-PHY-003)**:
      Pedotransfer parameters (:math:`\theta_r, \theta_s, \alpha, n, K_s`) are hardcoded for 12 discrete USDA soil classes (Carsel & Parrish 1988), lacking sub-grid organic matter gradations.

Scientific Formulations
=======================

Van Genuchten Soil Water Retention Curve (SWRC)
-----------------------------------------------
Relates soil suction head :math:`h` to volumetric soil moisture :math:`\theta`:

.. math::

   S_e(h) = \left[1 + |\alpha h|^n\right]^{-m}, \quad m = 1 - \frac{1}{n} \quad (n > 1)

.. math::

   \theta(h) = \theta_r + (\theta_s - \theta_r) \cdot S_e(h)

Inverse relation for suction head:

.. math::

   h(\theta) = -\frac{1}{\alpha} \left[S_e^{-1/m} - 1\right]^{1/n}

Mualem Unsaturated Hydraulic Conductivity
-----------------------------------------
Computes hydraulic conductivity :math:`K(S_e)` as a non-linear function of effective saturation:

.. math::

   K(S_e) = K_s \cdot S_e^{0.5} \left[1 - \left(1 - S_e^{1/m}\right)^m\right]^2

Richards Vadose Mass Conservation PDE
-------------------------------------
1D vertical unsaturated water transport is governed by Richards equation:

.. math::

   \frac{\partial \theta}{\partial t} = \frac{\partial}{\partial z} \left[K(\theta) \left(\frac{\partial \psi}{\partial z} - 1\right)\right]

Continuity flux and mass balance residual:

.. math::

   q(z, t) = -K(\theta) \left(\frac{\partial \theta}{\partial z} + 1.0\right)

.. math::

   \mathcal{R}_{\text{Richards}}(z, t) = \frac{\partial \theta}{\partial t} + \frac{\partial q}{\partial z}

Production Conservation Threshold:

.. math::

   \mathcal{R}_{\text{Richards}} \le 1.20 \times 10^{-4}\,\text{m}^3/\text{m}^3

Verification Results
====================
Validated via unit tests in ``tests/test_pinn_richards.py``, ``tests/test_richards_engine_d03.py``, and ``tests/test_physics_enkf_freeze.py``:
- Verified analytical van Genuchten curve inversion between suction and moisture.
- Verified unsaturated conductivity across 12 standard USDA soil classes.
- Verified PINN mass conservation residual satisfies :math:`\le 1.20 \times 10^{-4}\,\text{m}^3/\text{m}^3`.
- Verified physical range clamping to :math:`[\theta_r, \theta_s]`.

Defect & Technical Debt Register
================================
.. list-table::
   :widths: 15 45 15 25
   :header-rows: 1

   * - Defect ID
     - Description
     - Severity
     - Remediation Plan
   * - D-ENG-PHY-001
     - Prototype 2D lateral diffusion without gravity head.
     - HIGH
     - Replace prototype solver with true vertical 1D finite volume scheme.
   * - D-ENG-PHY-002
     - 2nd-order autograd graph memory consumption on large rasters.
     - MEDIUM
     - Apply spatial tiling during PINN residual inference.
   * - D-ENG-PHY-003
     - Discrete 12-class USDA parameter table.
     - LOW
     - Introduce continuous neural pedotransfer functions.
   * - D-ENG-PHY-004
     - Numerical singularity at saturation (:math:`S_e \to 1.0`).
     - LOW
     - Maintain epsilon stabilization guards on suction head.
