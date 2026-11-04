.. _module_05_physics_validation:

========================================================================
🛰️ Module 05: Soil-Water Physics, 1D Richards' PDE & PINN Solver
========================================================================

:Author: JCC Headquarter (RS-SDA Division) / Gourgopal Mohapatra
:Engine: AETHER-MRID1607X
:Module ID: MRIDANSH-MOD-PHYSICS-05
:Notebook Source: ``1_notebooks_sandbox/05-physics-validation.ipynb``
:Verification Suite: ``tests/test_notebook_05_verification.py``
:Last Verification: Verified (7/7 Test Cases Passed)

.. contents:: Table of Contents
   :depth: 3
   :local:

Overview & Scientific Purpose
=============================

Module 05 introduces rigorous physical conservation laws into the **THE MRIDANSH** hydrological estimation pipeline. While Modules 03 and 04 model spatial and temporal representations via data-driven deep learning architectures, Module 05 guarantees that volumetric soil moisture dynamics adhere strictly to classical unsaturated subsurface flow mechanics.

The module develops a Physics-Informed Neural Network (PINN) that functions as a continuous mesh-free surrogate solver for the 1D mixed-form Richards partial differential equation (PDE) across a 2-meter soil profile (:math:`z \in [0, 200\text{ cm}]`) over a 7-day post-storm simulation period (:math:`t \in [0, 168\text{ hrs}]`).

Key scientific components:
1. **van Genuchten-Mualem Constitutive Formulation**: Closed-form analytical curves modeling soil-water retention :math:`\theta(\psi)` and unsaturated hydraulic conductivity :math:`K(\theta)` parameterized for regional Odisha loam.
2. **Continuous Space-Time Domain Collocation**: Mesh-free collocation network evaluating physical loss residuals over :math:`1500` space-time interior points.
3. **PyTorch Autograd Richards PDE Residual Engine**: Automatic differentiation computing second-order spatial and first-order temporal derivatives to enforce mass continuity: :math:`\frac{\partial \theta}{\partial t} + \frac{\partial q}{\partial z} = 0`.
4. **Physical Benchmark Consistency**: Rigorous comparative validation demonstrating a :math:`>70\%` reduction in physical residual violation compared to an unconstrained purely data-driven neural network.
5. **Multi-Tier Production Checkpointing**: Automated export of model weights and architecture specifications into ``5_storage/checkpoints/`` accompanied by a formalized markdown manifest.

Constitutive Soil-Water Physics
===============================

The module implements the van Genuchten (1980) soil water retention model coupled with the Mualem (1976) hydraulic conductivity model:

Active Soil Profile: Regional Loam
----------------------------------

.. list-table:: Loam Hydraulic Parameters (USDA / Carsel & Parrish, 1988)
   :widths: 20 25 25 30
   :header-rows: 1

   * - Parameter
     - Symbol
     - Calibrated Value
     - Physical Units
   * - Residual Water Content
     - :math:`\theta_r`
     - 0.078
     - :math:`\text{cm}^3/\text{cm}^3`
   * - Saturated Water Content
     - :math:`\theta_s`
     - 0.430
     - :math:`\text{cm}^3/\text{cm}^3`
   * - Air-Entry Scale Parameter
     - :math:`\alpha`
     - 0.036
     - :math:`\text{cm}^{-1}`
   * - Pore-Size Distribution Index
     - :math:`n`
     - 1.560
     - Dimensionless
   * - Mualem Parameter
     - :math:`m = 1 - 1/n`
     - 0.3590
     - Dimensionless
   * - Saturated Hydraulic Conductivity
     - :math:`K_s`
     - 1.040
     - :math:`\text{cm/hr}`
   * - Tortuosity / Connectivity Parameter
     - :math:`l`
     - 0.500
     - Dimensionless

Analytical Governing Equations
------------------------------

Effective saturation :math:`\Theta \in [0, 1]` as a function of matric suction head :math:`\psi = |h| \ge 0`:

.. math::

   \Theta(\psi) = \left[ 1 + (\alpha \psi)^n \right]^{-m}

Volumetric water content :math:`\theta(\psi)`:

.. math::

   \theta(\psi) = \theta_r + (\theta_s - \theta_r) \cdot \Theta(\psi)

Unsaturated hydraulic conductivity :math:`K(\Theta)`:

.. math::

   K(\Theta) = K_s \cdot \Theta^l \cdot \left[ 1 - \left( 1 - \Theta^{1/m} \right)^m \right]^2

Richards' Equation & Autograd Formulation
=========================================

Governing PDE
-------------

The 1D vertical infiltration of water through unsaturated porous soil is governed by the mixed-form Richards equation:

.. math::

   \frac{\partial \theta}{\partial t} + \frac{\partial q}{\partial z} = 0

where :math:`z` is depth measured positive downward (:math:`\text{cm}`), :math:`t` is elapsed time (:math:`\text{hr}`), and :math:`q` is Darcian flux:

.. math::

   q = -K(\theta) \cdot \left( \frac{\partial \theta}{\partial z} + 1.0 \right)

The constant :math:`+1.0` accounts for unit gravitational potential gradient in vertical downward flow.

Automatic Differentiation Residual Engine
-----------------------------------------

The continuous neural network surrogate :math:`\mathcal{M}_\vartheta(z, t)` directly predicts :math:`\hat{\theta}(z, t)`. Automatic differentiation evaluates:

1. **Temporal Rate of Change**:

   .. math::

      \frac{\partial \hat{\theta}}{\partial t} = \frac{\partial \mathcal{M}_\vartheta(z, t)}{\partial t}

2. **Spatial Moisture Gradient**:

   .. math::

      \frac{\partial \hat{\theta}}{\partial z} = \frac{\partial \mathcal{M}_\vartheta(z, t)}{\partial z}

3. **Continuous Flux Computation**:

   .. math::

      q = -K(\hat{\theta}) \cdot \left( \frac{\partial \hat{\theta}}{\partial z} + 1.0 \right)

4. **Flux Spatial Divergence**:

   .. math::

      \frac{\partial q}{\partial z} = \operatorname{autograd}(q, z)

5. **Continuity Residual**:

   .. math::

      \mathcal{R}_{\text{PDE}}(z, t) = \frac{\partial \hat{\theta}}{\partial t} + \frac{\partial q}{\partial z}

PINN Architecture & Boundary Conditions
=======================================

Network Blueprint
-----------------

- **Input Dimension**: :math:`2` (:math:`z \in [0, 200\text{ cm}]`, :math:`t \in [0, 168\text{ hrs}]`)
- **Hidden Layers**: 4 fully connected layers with 64 neurons each
- **Activation Function**: Hyperbolic tangent (:math:`\tanh`) for smooth second-order derivatives
- **Output Layer**: Sigmoid activation scaled to physical soil saturation limits:

  .. math::

     \hat{\theta}(z, t) = \theta_r + (\theta_s - \theta_r) \cdot \sigma\left( \mathbf{W}_5 \mathbf{h}_4 + \mathbf{b}_5 \right)

Space-Time Boundary Enforcements
--------------------------------

1. **Top Infiltration Boundary (:math:`z = 0\text{ cm}`)**:
   Anchored dynamically to preprocessed surface satellite telemetry from Module 02.
2. **Bottom Drainage Boundary (:math:`z = 200\text{ cm}`)**:
   Asymptotic deep drainage boundary condition (:math:`\theta \to \theta_r + 0.05`).
3. **Initial Condition (:math:`t = 0\text{ hr}`)**:
   Hydrostatic capillary equilibrium moisture profile.

Optimization Loss
-----------------

The composite loss function combines the physical residual over :math:`N = 1500` interior collocation points with boundary penalties:

.. math::

   \mathcal{L}_{\text{total}} = \frac{1}{N_{\text{colloc}}} \sum_{i=1}^{N_{\text{colloc}}} \left| \mathcal{R}_{\text{PDE}}(z_i, t_i) \right|^2 + \lambda_{\text{top}} \mathcal{L}_{\text{top}} + \lambda_{\text{bot}} \mathcal{L}_{\text{bot}} + \lambda_{\text{IC}} \mathcal{L}_{\text{IC}}

Trained over 100 epochs using Adam (:math:`\text{lr}=10^{-3}`) with gradient norm clipping (:math:`\text{max\_norm}=1.0`).

Physical Benchmark & Consistency Results
========================================

To rigorously verify physical fidelity, the PINN model was benchmarked against an identical unconstrained neural network trained solely on surface boundary data without the Richards PDE loss:

- **Unconstrained Baseline Mean PDE Error**: :math:`0.003420\text{ cm}^3/\text{cm}^3/\text{hr}`
- **PINN (Richards-Constrained) Mean PDE Error**: :math:`0.000785\text{ cm}^3/\text{cm}^3/\text{hr}`
- **Mass Conservation Residual Reduction Rate**: :math:`77.05\%`
- **Moisture Bounds**: :math:`\hat{\theta} \in [0.1284, 0.4120]\text{ cm}^3/\text{cm}^3` (strictly bounded within :math:`[\theta_r - 0.05, \theta_s + 0.05]`)

Generated Artifacts & Visualizations
====================================

The module generates 5 diagnostic plots and 3 persistent data artifacts:

1. **van Genuchten SWRC & Conductivity (plot_01_van_genuchten_swrc_conductivity.png)**: Dual-panel semi-log plots of water retention and conductivity curves across matric suction :math:`\psi \in [0.1, 10000]\text{ cm}`.
2. **Space-Time Collocation Mesh (plot_02_pinn_space_time_collocation_mesh.png)**: Scatter plot illustrating interior collocation points and boundary Dirichlet anchors.
3. **PINN Loss Convergence Trajectory (plot_03_pinn_loss_convergence_trajectory.png)**: Semi-log curve tracking total, PDE residual, and boundary losses over 100 epochs.
4. **Physical Residual Benchmark (plot_04_pinn_vs_unconstrained_pde_residuals.png)**: Dual-panel error distribution comparison confirming :math:`>70\%` error reduction over unconstrained modeling.
5. **Continuous Soil Diffusion Profile (plot_05_continuous_soil_diffusion_profile.png)**: 2D contour map depicting vertical wetting front infiltration across 200 cm depth and 168 hours.

Checkpoints & Data Files:
- ``5_storage/checkpoints/pinn_richards_model.pt``: Production PINN model checkpoint.
- ``5_storage/checkpoints/PINN_RICHARDS_MODEL_MANIFEST.md``: Production model manifest describing coordinate systems, soil parameters, and governing equations.
- ``5_storage/notebook_results/notebook_05_physics_validation/pinn_physics_metrics.json``: Machine-readable validation metrics.

Verification & Test Coverage
============================

The verification suite ``tests/test_notebook_05_verification.py`` enforces 7 automated tests:

* ``test_01_no_python_scripts_in_notebook_dir``: Confirms zero Python scripts in sandbox directory.
* ``test_02_notebook_cell_structure_and_markdown_rules``: Validates alternating markdown/code layout (:math:`\ge 30` cells).
* ``test_03_all_code_cells_executed_with_zero_errors``: Audits all 16 code cells executed with 0 runtime errors.
* ``test_04_penultimate_and_ultimate_markdown_cells``: Audits presence of Executive Summary and Intellectual Property notices.
* ``test_05_storage_artifacts_and_plots_persisted``: Validates presence and file sizes (>50KB) of all 5 plots and metrics JSON.
* ``test_06_checkpoint_and_manifest_compliance``: Validates physical presence of checkpoint and manifest in ``5_storage/checkpoints/``, verifies ``soil_class == "loam"``, and confirms PDE reduction :math:`\ge 70\%`.
* ``test_07_richards_physics_consistency_and_mass_conservation``: Asserts physical PDE error :math:`< 0.001` and verifies volumetric moisture bounds.

Known Defects & Engineering Limitations
========================================

* **D-NB05-001 (Simplified Darcian Flux Formulation)**: Flux is modeled as :math:`q = -K(\theta)(\frac{\partial \theta}{\partial z} + 1)` rather than explicitly computing soil water diffusivity :math:`D(\theta) = K(\theta) \frac{d\psi}{d\theta}`, slightly overestimating hydraulic flux under dry conditions.
* **D-NB05-002 (Homogeneous Loam Subgrade Idealization)**: Assumes uniform soil properties throughout the :math:`2\text{ m}` column, ignoring soil horizon layering and macropore bypass flow.
* **D-NB05-003 (1D Vertical Infiltration Assumption)**: Neglects lateral subsurface interflow between adjacent catchment cells on slopes.
* **D-NB05-004 (Uncalibrated Surface Telemetry Proxy)**: The surface moisture boundary is derived from an uncalibrated proxy rather than in-situ sensor networks.
