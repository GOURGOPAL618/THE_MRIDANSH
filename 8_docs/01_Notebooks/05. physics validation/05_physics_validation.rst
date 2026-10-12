=====================================================================
THE MRIDANSH (AETHER-MRID1607X) - Notebook 05: Physics Validation
=====================================================================

:Project: THE MRIDANSH - Unified Soil State Estimation System
:Engine: AETHER-MRID1607X (Multi-Domain Soil Intelligence Engine)
:Notebook: ``05-physics-validation.ipynb``
:Sprint phase: Days 9-11 of the 18-Day Scientific Validation Sprint
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
The primary technical objective of ``05-physics-validation.ipynb`` is to formulate,
differentiate, and optimize a Physics-Informed Neural Network (PINN) that embeds the
governing partial differential equations (PDEs) of unsaturated porous media flow—specifically
the 1D mixed-form Richards equation coupled with van Genuchten (1980) Soil Water Retention
Curves (SWRC)—into a deep learning surrogate to enforce mass conservation and physical
plausibility over space-time moisture dynamics.

1.2 System Context
------------------
Within **THE MRIDANSH** (*AETHER-MRID1607X*) system, Notebook 03 constructs spatial graph
meshes and Notebook 04 forecasts temporal sequence dynamics via ConvLSTM. Notebook 05
acts as the rigorous physical consistency gatekeeper:

* **Upstream**: Consumes physical soil domain parameters and baseline temporal horizons.
* **Core Engine**: Implements van Genuchten closed-form analytical solvers, constructs
  reverse-mode automatic differentiation pipelines (PyTorch Autograd) to evaluate exact
  space-time PDE derivatives, formulates multi-objective composite loss functions
  (:math:`\mathcal{L}_{\text{total}} = 0.1\mathcal{L}_{\text{PDE}} + 0.5\mathcal{L}_{\text{BC}}`),
  and executes 100-epoch neural optimization.
* **Downstream**: Supplies physically validated vertical moisture diffusion fields
  :math:`\hat{\theta}(z, t)` to Notebook 06 for geotechnical slope stability analysis and
  Ensemble Kalman Filter (EnKF) state updating.

1.3 Design Boundary
-------------------
The design of Notebook 05 is bounded as follows:

* **In Boundary**: van Genuchten retention :math:`\theta(\psi)` and conductivity :math:`K(\theta)`
  implementations, PyTorch-differentiable hydraulic operators, 4-layer MLP PINN architecture
  with bounded Sigmoid output scaling, higher-order Autograd computational graph construction,
  continuous space-time collocation sampling, Dirichlet boundary condition enforcement,
  100-epoch Adam optimization with gradient norm clipping, benchmark evaluation against
  unconstrained baselines, and 2D continuous space-time diffusion grid visualization.
* **Out of Boundary**: Multi-dimensional lateral hydraulic routing (governed by 2D/3D shallow
  water equations), empirical soil moisture sensor assimilation (governed by EnKF in Notebook 06),
  dynamic atmospheric evapotranspiration coupling, and soil column stratigraphy layering.

1.4 Relationship to Requirements
--------------------------------
This technical description details the mathematical models, software design, tensor pipelines,
and algorithms implementing the formal software requirements established in
``05_physics_validation_REQUIREMENTS.md``. Every component described herein maps to verified
functional and data integrity requirements. See Section 15 for the full mapping matrix.

2. Architecture
===============

2.1 Notebook Architecture
-------------------------
The software architecture spans three operational milestones across 36 notebook cells:

* **Milestone 1: Soil Physics Parameterization & Analytical Solvers (Sprint Day 9)**:
  Defines USDA soil hydraulic parameter sets, implements NumPy closed-form SWRC and
  conductivity equations, evaluates logarithmic tension sweeps, and instantiates PyTorch
  differentiable operators.
* **Milestone 2: PINN Architecture, Autograd PDE Residual & Composite Loss (Sprint Day 10)**:
  Constructs the 4-layer MLP architecture with Sigmoid saturation scaling, evaluates exact
  autograd space-time derivatives, formulates Dirichlet surface/deep boundary conditions,
  and executes 100-epoch composite loss optimization.
* **Milestone 3: Benchmark Evaluation & Continuous Diffusion Mapping (Sprint Day 11)**:
  Evaluates physical consistency against an unconstrained neural baseline, constructs a
  :math:`100 \times 100` continuous space-time diffusion mesh, and renders aerospace-grade
  diagnostic heatmaps.

2.2 Processing Pipeline
-----------------------
The operational physics pipeline executes through the following sequence:

.. code-block:: text

   [van Genuchten Soil Parameters] (sandy_loam: θr=0.065, θs=0.410, α=0.075, n=1.89, Ks=4.42)
               │
               ▼
   [Analytical Solvers: θ(ψ) & K(θ)] ────► [Aerospace Plot 1: SWRC & K Curves]
               │
               ▼
   [Space-Time Collocation Sampling: z ∈ [0, 200 cm], t ∈ [0, 168 hrs]]
               │
               ├────────────────────────────────────────┐
               ▼                                        ▼
   [PhysicsInformedNN (MLP 2->64->1)]       [Dirichlet Boundary Tensors]
   (Bounded: θ ∈ [θr, θs])                  (Top z=0: 0.35, Bottom z=200: 0.15)
               │                                        │
               ▼                                        │
   [Autograd Derivative Engine]                         │
   (∂θ/∂t, ∂θ/∂z, q = -K(∂θ/∂z+1), ∂q/∂z)               │
               │                                        │
               ▼                                        │
   [Richards PDE Residual: ∂θ/∂t + ∂q/∂z]               │
               │                                        │
               ├────────────────────────────────────────┘
               ▼
   [Composite Loss: 0.1 * L_pde + 0.5 * (L_bc_top + L_bc_bottom)]
               │
               ▼
   [100-Epoch Adam Optimization (lr=1e-3, Clip=1.0)]
               │
               ├────────────────────────────────────────► [Plot 3: Convergence Telemetry]
               │
               ▼
   [Benchmark Evaluation: PINN vs Unconstrained Baseline]
               │
               ▼
   [2D Diffusion Grid Construction (100x100)] ──► [Plot 4: Depth-Time Diffusion Map]

2.3 Component Relationships
---------------------------
The internal software components interact via explicit functional interfaces:

1. **Analytical Hydraulic Engine**: Evaluates closed-form water retention and hydraulic
   conductivity functions for standard USDA soil textures.
2. **Autograd Derivative Engine**: Interrogates the PyTorch computational graph via
   ``torch.autograd.grad`` to extract exact analytical spatial and temporal derivatives.
3. **PINN Model Core**: Evaluates continuous forward moisture predictions while strictly
   constraining values to the interval :math:`[\theta_r, \theta_s]` via Sigmoid activation scaling.
4. **Boundary Condition Engine**: Enforces hydrological constraints at the upper soil
   surface (:math:`z = 0\text{ cm}`) and the bottom deep drainage boundary (:math:`z = 200\text{ cm}`).
5. **Diffusion Visualizer**: Interpolates the continuous neural surrogate over a regular
   :math:`100 \times 100` depth-time mesh for hydrological auditing.

2.4 Data Flow
-------------
The data flow transitions across three mathematical domains:

1. **Hydraulic Parameter Domain**: Soil physical constants (:math:`\alpha, n, m, K_s, \theta_r, \theta_s`).
2. **Space-Time Coordinate Domain**: Collocation tensors :math:`z \in \mathbb{R}^{N \times 1}`
   (depth in cm) and :math:`t \in \mathbb{R}^{N \times 1}` (time in hours).
3. **Continuous Field Domain**: Differentiable moisture field :math:`\hat{\theta}(z, t) \in \mathbb{R}^{N \times 1}`
   and associated physical residual tensors :math:`\mathcal{R}_{\text{PDE}} \in \mathbb{R}^{N \times 1}`.

3. Execution Flow
=================

3.1 Initialization
------------------
* Imports core system dependencies (``sys``, ``os``, ``json``, ``math``, ``numpy``, ``pandas``,
  ``torch``, ``torch.nn``, ``matplotlib.pyplot``).
* Configures inline rendering and dark telemetry stylesheet:
  background ``#000000``, axis borders ``#00FFCC`` (width 1.2), grid lines ``#1A3344``
  (dashed, alpha 0.5), monospace font family.
* Selects computation device (``torch.device('cpu')``) and fixes random seeds:
  ``torch.manual_seed(42)`` and ``np.random.seed(42)``.
* Emits initialization status banner.

3.2 Soil Hydraulic Parameter Definition
---------------------------------------
* Declares dictionary ``SOIL_HYDRAULIC_PARAMS`` containing USDA parameters for:
  - ``sandy_loam``: :math:`\theta_r = 0.065, \theta_s = 0.410, \alpha = 0.075\text{ cm}^{-1}, n = 1.89, m = 0.4709, K_s = 4.42\text{ cm/hr}, l = 0.5`.
  - ``silty_clay``: :math:`\theta_r = 0.070, \theta_s = 0.360, \alpha = 0.005\text{ cm}^{-1}, n = 1.09, m = 0.0826, K_s = 0.02\text{ cm/hr}, l = 0.5`.
* Sets ``ACTIVE_SOIL = SOIL_HYDRAULIC_PARAMS['sandy_loam']`` and prints parameters to stdout.

3.3 Analytical Forward Curve Evaluation
---------------------------------------
* Evaluates NumPy closed-form solvers:
  - ``van_genuchten_retention(psi, params)``: Computes :math:`\theta(\psi)`.
  - ``van_genuchten_conductivity(theta, params)``: Computes :math:`K(\theta)`.
* Sweeps matric suction range :math:`\psi \in [0.1, 10000.0]\text{ cm}` across 200 log-spaced points.
* Emits logged ranges: :math:`\theta \in [0.0660, 0.4100]\text{ m}^3/\text{m}^3`, :math:`K \in [6.98 \times 10^{-13}, 4.31]\text{ cm/hr}`.
* Renders Aerospace Plot 1 showing semi-log SWRC and conductivity curves.

3.4 PyTorch Differentiable Hydraulic Operators
----------------------------------------------
* Instantiates PyTorch-compatible hydraulic functions:
  - ``torch_van_genuchten_theta(psi, params)``: Differentiable retention function.
  - ``torch_van_genuchten_k(theta, params)``: Differentiable unsaturated conductivity
    with normalized saturation clamping :math:`S_e \in [10^{-5}, 1.0]`.

3.5 PINN Architecture Definition
--------------------------------
* Instantiates class ``PhysicsInformedNN``:
  - Input layer: :math:`\operatorname{Linear}(2, 64) \to \operatorname{Tanh}`.
  - Hidden layers: 3 sequential blocks of :math:`\operatorname{Linear}(64, 64) \to \operatorname{Tanh}`.
  - Output projection: :math:`\operatorname{Linear}(64, 1)`.
  - Parameter initialization: Xavier normal on weights, constant 0.0 on biases.
  - Output forward scaling:

    .. math::

       \hat{\theta} = \theta_r + (\theta_s - \theta_r) \cdot \operatorname{sigmoid}(\theta_{\text{raw}})

* Transfers model to active device and logs architecture.

3.6 Autograd PDE Residual Engine
--------------------------------
* Function ``compute_richards_pde_residual`` enforces the Richards differential operator:
  - Flags inputs: ``z.requires_grad_(True)``, ``t.requires_grad_(True)``.
  - Evaluates forward prediction: ``theta_pred = model(z, t)``.
  - Computes temporal rate: :math:`\frac{\partial \hat{\theta}}{\partial t} = \operatorname{autograd.grad}(\hat{\theta}, t)`.
  - Computes spatial gradient: :math:`\frac{\partial \hat{\theta}}{\partial z} = \operatorname{autograd.grad}(\hat{\theta}, z)`.
  - Evaluates unsaturated conductivity: :math:`K = \operatorname{torch\_van\_genuchten\_k}(\hat{\theta})`.
  - Evaluates Darcy flux: :math:`q = -K \cdot \left(\frac{\partial \hat{\theta}}{\partial z} + 1.0\right)`.
  - Computes flux divergence: :math:`\frac{\partial q}{\partial z} = \operatorname{autograd.grad}(q, z)`.
  - Combines into residual: :math:`\mathcal{R}_{\text{PDE}} = \frac{\partial \hat{\theta}}{\partial t} + \frac{\partial q}{\partial z}`.

3.7 Space-Time Collocation Sampling & Baseline Evaluation
---------------------------------------------------------
* Generates 1,500 uniform collocation points via ``generate_collocation_points(1500)``:
  :math:`z \sim \mathcal{U}(0, 200\text{ cm})`, :math:`t \sim \mathcal{U}(0, 168\text{ hrs})`.
* Evaluates untrained model:
  - Predicted moisture range: :math:`[0.2084, 0.3008]\text{ m}^3/\text{m}^3`.
  - Mean PDE residual: **0.001347**.
  - Maximum PDE residual: **0.008327**.

3.8 Boundary Condition Formulation
----------------------------------
* Generates 300 boundary coordinates via ``generate_boundary_conditions()``:
  - Surface top boundary: :math:`z_{\text{top}} = 0\text{ cm}`, target :math:`\theta = 0.35` (wet infiltration).
  - Bottom drainage boundary: :math:`z_{\text{bottom}} = 200\text{ cm}`, target :math:`\theta = 0.15` (deep drainage).
  - Time coordinates: :math:`t_{\text{bc}} \sim \mathcal{U}(0, 168\text{ hrs})`.

3.9 Composite Multi-Objective Loss Formulation
----------------------------------------------
* Function ``compute_composite_pinn_loss`` calculates weighted composite loss:

  .. math::

     \mathcal{L}_{\text{total}} = 0.1 \cdot \mathcal{L}_{\text{PDE}} + 0.5 \cdot (\mathcal{L}_{\text{bc\_top}} + \mathcal{L}_{\text{bc\_bottom}})

  Where :math:`\mathcal{L}_{\text{PDE}} = \frac{1}{M} \sum \mathcal{R}_{\text{PDE}}^2`, and boundary losses are mean squared errors against targets.

3.10 PINN Optimization Loop
---------------------------
* Re-instantiates ``pinn_model`` and configures Adam optimizer (learning rate :math:`10^{-3}`).
* Executes 100 epochs with dynamic resampling (1,000 collocation points per epoch):
  - Clears gradients: ``optimizer.zero_grad()``.
  - Computes composite loss: ``compute_composite_pinn_loss()``.
  - Backpropagates derivatives: ``total_loss.backward()``.
  - Clips gradients: ``torch.nn.utils.clip_grad_norm_(..., max_norm=1.0)``.
  - Steps optimizer: ``optimizer.step()``.
  - Records scalar losses.
* Logs training trajectory: Epoch 001 (0.030035) :math:`\to` Epoch 100 (0.000027).

3.11 Convergence Diagnostics Rendering
--------------------------------------
* Renders Aerospace Plot 3 displaying total composite loss, PDE residual loss, and boundary
  condition loss on a logarithmic y-axis over 100 epochs with embedded diagnostics.

3.12 Physical Consistency Benchmark Evaluation
----------------------------------------------
* Instantiates identical 4-layer MLP unconstrained baseline model trained for 100 epochs purely
  on random mock data without PDE or boundary constraints.
* Evaluates PDE residuals on 1,200 unseen test points:
  - Unconstrained Baseline PDE Error: **0.003953**.
  - PINN (Richards-Constrained) Error: **0.004024**.
  - Physical Residual Reduction: **-1.81%**.

3.13 Continuous Space-Time Diffusion Heatmap
--------------------------------------------
* Constructs a regular :math:`100 \times 100` grid across :math:`z \in [0, 200\text{ cm}]`
  and :math:`t \in [0, 168\text{ hrs}]`.
* Evaluates trained model under ``torch.no_grad()``, reshaping outputs to :math:`(100, 100)`.
* Emits output bounds: Min :math:`\theta = 0.1456`, Max :math:`\theta = 0.3510\text{ m}^3/\text{m}^3`.
* Renders Aerospace Plot 4: Continuous 2D depth-time diffusion field with inverted depth axis.

4. Component Design
===================

4.1 Soil Hydraulic Parameter Engine
-----------------------------------
* **Function**: Maintains physical soil hydraulic parameters.
* **Mechanism**: Python dictionary structure indexing physical constants by soil texture class.
  Provides parameters governing the non-linear relationship between pore suction and liquid content.

4.2 Closed-Form Analytical Solvers
----------------------------------
* **Function**: Evaluates reference soil retention curves.
* **Mechanism**:
  - Retention: Computes effective saturation :math:`\Theta(\psi) = [1 + (\alpha |\psi|)^n]^{-m}`,
    then scales to volumetric moisture :math:`\theta = \theta_r + (\theta_s - \theta_r)\Theta`.
  - Conductivity: Computes Mualem-van Genuchten relative conductivity:

    .. math::

       K(\theta) = K_s S_e^l \left[1 - \left(1 - S_e^{1/m}\right)^m\right]^2

4.3 PhysicsInformedNN Architecture
----------------------------------
* **Function**: Serves as a differentiable surrogate mapping :math:`(z, t) \to \hat{\theta}`.
* **Mechanism**: Deep Multi-Layer Perceptron (MLP) containing 4 dense linear layers with 64 units
  each and hyperbolic tangent (:math:`\operatorname{Tanh}`) activations. Hyperbolic tangents are
  selected over ReLUs because ReLUs have zero second-order derivatives (:math:`\frac{\partial^2}{\partial z^2} = 0`),
  which would extinguish second-order flux divergence terms. Output values are passed through a
  Sigmoid function scaled by :math:`(\theta_s - \theta_r)` and offset by :math:`\theta_r` to guarantee
  physical saturation boundaries.

4.4 Autograd Space-Time Differential Engine
-------------------------------------------
* **Function**: Evaluates partial derivatives and differential PDE residuals.
* **Mechanism**:
  Leverages PyTorch reverse-mode automatic differentiation. Evaluates:

  .. math::

     \frac{\partial \hat{\theta}}{\partial t} = \operatorname{autograd}(\hat{\theta}, t, \mathbf{1})

  .. math::

     \frac{\partial \hat{\theta}}{\partial z} = \operatorname{autograd}(\hat{\theta}, z, \mathbf{1})

  .. math::

     \frac{\partial q}{\partial z} = \operatorname{autograd}\left(-K(\hat{\theta})\left[\frac{\partial \hat{\theta}}{\partial z} + 1\right], z, \mathbf{1}\right)

  Graph retention parameters ``create_graph=True`` and ``retain_graph=True`` enable computing
  gradients of gradients during backward optimization.

4.5 Collocation & Boundary Generator
------------------------------------
* **Function**: Generates sampling grids across the space-time domain.
* **Mechanism**: Generates pseudo-random coordinates via ``torch.rand`` scaled to the domain
  limits (:math:`[0, 200\text{ cm}]` and :math:`[0, 168\text{ hrs}]`). Formulates fixed coordinate
  vectors for surface (:math:`z = 0`) and deep drainage (:math:`z = 200`) boundaries.

5. Data Structures
==================

5.1 Input Parameter Schema
--------------------------
Dictionary ``ACTIVE_SOIL`` keys:

.. list-table::
   :header-rows: 1
   :widths: 20 20 20 40

   * - Parameter
     - Type
     - Value
     - Physical Meaning
   * - ``theta_r``
     - float
     - 0.0650
     - Residual water content (:math:`\text{m}^3/\text{m}^3`)
   * - ``theta_s``
     - float
     - 0.4100
     - Saturated water content (:math:`\text{m}^3/\text{m}^3`)
   * - ``alpha``
     - float
     - 0.0750
     - Inverse air-entry value (:math:`\text{cm}^{-1}`)
   * - ``n``
     - float
     - 1.8900
     - Pore-size distribution index
   * - ``m``
     - float
     - 0.4709
     - Retention exponent (:math:`1 - 1/n`)
   * - ``Ks``
     - float
     - 4.4200
     - Saturated hydraulic conductivity (cm/hr)
   * - ``l``
     - float
     - 0.5000
     - Pore connectivity parameter

5.2 Intermediate Tensors
------------------------
1. **Collocation Coordinate Tensors** (``z_colloc``, ``t_colloc``): PyTorch float32 tensors of shape :math:`(N, 1)`.
2. **Boundary Tensors** (``z_top``, ``z_bottom``, ``t_bc``): PyTorch float32 tensors of shape :math:`(300, 1)`.
3. **Target Boundary Tensors** (``theta_top_target``, ``theta_bottom_target``): PyTorch float32 tensors of shape :math:`(300, 1)`.
4. **Hydraulic Conductivity Tensor** (``K_val``): PyTorch float32 tensor of shape :math:`(N, 1)`.
5. **Darcy Flux Tensor** (``flux_q``): PyTorch float32 tensor of shape :math:`(N, 1)`.
6. **PDE Residual Tensor** (``pde_residual``): PyTorch float32 tensor of shape :math:`(N, 1)`.

5.3 Output Schema
-----------------
1. **Moisture Diffusion Matrix** (``Theta_matrix``): NumPy float32 2D array of shape :math:`(100, 100)`
   representing continuous soil moisture values across 100 discrete depth intervals and 100 time steps.

6. Algorithms and Methods
=========================

6.1 1D Mixed-Form Richards' Equation Mechanics
----------------------------------------------
The mixed-form 1D Richards PDE describes vertical unsaturated water flow in porous media:

.. math::

   \frac{\partial \theta}{\partial t} = \frac{\partial}{\partial z} \left[ K(\psi) \left( \frac{\partial \psi}{\partial z} + 1 \right) \right] - S(z, t)

Where:
* :math:`\theta` is volumetric water content.
* :math:`\psi` is negative matric suction head.
* :math:`K(\psi)` is unsaturated hydraulic conductivity.
* The :math:`+1` term accounts for gravity-driven downward potential gradient.
* In Notebook 05, the sink term :math:`S(z, t) = 0` (no root water uptake).

6.2 Darcy Flux Formulation in Code
----------------------------------
The software implements a simplified gradient formulation for unsaturated Darcy flux:

.. math::

   q = -K(\hat{\theta}) \left[ \frac{\partial \hat{\theta}}{\partial z} + 1.0 \right]

And evaluates flux divergence as:

.. math::

   \operatorname{div}(q) = \frac{\partial q}{\partial z}

Yielding the differential conservation residual:

.. math::

   \mathcal{R}_{\text{PDE}} = \frac{\partial \hat{\theta}}{\partial t} + \frac{\partial q}{\partial z}

6.3 Automatic Differentiation Implementation
--------------------------------------------
PyTorch Autograd computes vector-Jacobian products to extract exact partial derivatives without
finite difference grid discretization:

.. code-block:: python

   dtheta_dt = torch.autograd.grad(
       outputs=theta_pred, inputs=t,
       grad_outputs=torch.ones_like(theta_pred),
       create_graph=True, retain_graph=True
   )[0]

Setting ``create_graph=True`` ensures that :math:`d\theta/dt` itself remains in the computational
graph, allowing its derivative with respect to neural parameters :math:`W` to be computed during
subsequent ``loss.backward()`` operations.

6.4 Composite Loss Optimization
-------------------------------
The composite loss balances physical conservation against boundary constraints:

.. math::

   \mathcal{L}_{\text{total}} = w_{\text{pde}} \cdot \frac{1}{M}\sum_{i=1}^{M} \mathcal{R}_{\text{PDE}}^2(z_i, t_i) + w_{\text{bc}} \cdot \left[ \frac{1}{B}\sum_{j=1}^{B} (\hat{\theta}(0, t_j) - 0.35)^2 + \frac{1}{B}\sum_{j=1}^{B} (\hat{\theta}(200, t_j) - 0.15)^2 \right]

With :math:`w_{\text{pde}} = 0.1` and :math:`w_{\text{bc}} = 0.5`.

6.5 Dynamic Collocation Resampling
----------------------------------
To prevent neural networks from fitting discrete collocation point artifacts, new space-time
coordinates are drawn uniformly at the beginning of each epoch:

.. code-block:: python

   for epoch in range(1, EPOCHS + 1):
       z_c, t_c = generate_collocation_points(num_points=1000)

This acts as continuous stochastic regularization across the space-time domain.

7. Interfaces
-------------

7.1 Input Interfaces
--------------------
* Soil parameters ingested directly via internal configuration dictionaries.
* Model accepts tensor coordinates :math:`z \in \mathbb{R}^{N \times 1}` and :math:`t \in \mathbb{R}^{N \times 1}`.

7.2 Output Interfaces
---------------------
* Model forward method returns continuous moisture predictions :math:`\hat{\theta} \in \mathbb{R}^{N \times 1}`.
* Residual evaluator returns tuple of tensors: ``(pde_residual, theta_pred)``.

7.3 File Interfaces
-------------------
* *Note*: Notebook 05 currently operates entirely in memory and does not write serialized
  model checkpoints to disk (see Open Defect D-004 in the requirements document).

7.4 Downstream Consumer Interfaces
----------------------------------
* **Consumer**: Notebook 06 (Geotechnical slope stability & EnKF).
* **Contract**: Supplies continuous vertical infiltration profile :math:`\hat{\theta}(z, t)` to
  evaluate transient pore water pressure :math:`u = -\psi(\hat{\theta}) \cdot \gamma_w` and
  Bishop effective stress for landslide factor of safety calculations.

8. Configuration
----------------

8.1 Constants
-------------
* ``ACTIVE_SOIL``: ``sandy_loam``.
* ``Z_MAX = 200.0``: Maximum soil column depth in centimeters.
* ``T_MAX = 168.0``: Maximum temporal simulation horizon in hours (7 days).
* ``THETA_TOP = 0.35``: Wet surface infiltration boundary target.
* ``THETA_BOTTOM = 0.15``: Deep drainage equilibrium boundary target.
* ``W_PDE = 0.1``: Weight multiplier for PDE residual loss.
* ``W_BC = 0.5``: Weight multiplier for boundary condition loss.
* ``LR = 0.001``: Adam optimizer learning rate.
* ``EPOCHS = 100``: Training optimization epoch limit.
* ``MAX_NORM = 1.0``: Maximum gradient norm threshold.

8.2 Environment
---------------
* Python 3.10+ execution runtime.
* Backend: PyTorch CPU or CUDA GPU.

8.3 Runtime Configuration
-------------------------
* Plotting theme: ``dark_background``.
* Plotting parameters:
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

9.1 Clamped Saturation Mechanics
--------------------------------
In ``torch_van_genuchten_k``, normalized saturation is smoothly bounded:

.. code-block:: python

   Se = torch.clamp((theta - theta_r) / (theta_s - theta_r + 1e-6), min=1e-5, max=1.0)

This prevents negative values or division by zero when raising saturation to the fractional
power :math:`1/m`, eliminating NaN propagation in the autograd graph.

9.2 Gradient Norm Clipping
--------------------------
Higher-order derivatives in PINN losses can cause exploding gradients.
Enforcing:

.. code-block:: python

   torch.nn.utils.clip_grad_norm_(pinn_model.parameters(), max_norm=1.0)

Safeguards against divergence during backpropagation.

9.3 Physical Value Bounding
---------------------------
Output layer Sigmoid scaling ensures predictions can never violate physical limits:

.. code-block:: python

   theta_bounded = theta_r + (theta_s - theta_r) * torch.sigmoid(theta_raw)

Even if unconstrained neural linear weights diverge, output moisture strictly remains within
:math:`[0.065, 0.410]\text{ m}^3/\text{m}^3`.

10. Generated Artifacts
=======================

10.1 Diagnostic Plot Suite
--------------------------
* **Aerospace Plot 1**: Semi-log Soil Water Retention Curve (SWRC) and unsaturated hydraulic
  conductivity curve :math:`K(\theta)` with hydrological profile overlay.
* **Aerospace Plot 3**: 100-Epoch PINN Optimization Convergence Telemetry displaying Total Composite
  Loss, PDE Residual Loss, and Boundary Condition Loss on a logarithmic scale.
* **Aerospace Plot 4**: Continuous 2D Soil Moisture Diffusion Field :math:`\hat{\theta}(z, t)`
  over depth :math:`z \in [0, 200\text{ cm}]` and time :math:`t \in [0, 168\text{ hrs}]` with
  hydrological mass conservation audit overlay.

11. Reproducibility
===================

11.1 Random Seeds
-----------------
Fixed random seeds ensure identical weight initialization and collocation sampling:

.. code-block:: python

   torch.manual_seed(42)
   np.random.seed(42)

11.2 Deterministic Numerical Invariants
---------------------------------------
Under seeds 42, the following exact numerical invariants are guaranteed:

* Analytical Retention Limits: :math:`\theta \in [0.0660, 0.4100]\text{ m}^3/\text{m}^3`.
* Analytical Conductivity Limits: :math:`K \in [6.98 \times 10^{-13}, 4.31]\text{ cm/hr}`.
* Untrained Initial PDE Residual: Mean = **0.001347**, Max = **0.008327**.
* Optimization Trajectory Losses:
  - Epoch 001: Total: **0.030035** | PDE: **0.000029** | BC: **0.060065**
  - Epoch 020: Total: **0.001248** | PDE: **0.000273** | BC: **0.002441**
  - Epoch 040: Total: **0.000052** | PDE: **0.000087** | BC: **0.000087**
  - Epoch 060: Total: **0.000046** | PDE: **0.000077** | BC: **0.000076**
  - Epoch 080: Total: **0.000019** | PDE: **0.000061** | BC: **0.000027**
  - Epoch 100: Total: **0.000027** | PDE: **0.000185** | BC: **0.000018**
* Benchmark PDE Residuals:
  - Unconstrained Baseline: **0.003953**
  - PINN Model: **0.004024**
  - Measured Reduction: **-1.81%**
* Continuous Diffusion Mesh Output: Min :math:`\theta = 0.1456`, Max :math:`\theta = 0.3510`.

12. Performance Characteristics
===============================

12.1 Execution Time Profile
---------------------------
Measured across standard x86_64 CPU hardware:

* Analytical Curve Generation (Cells 04, 06): :math:`< 0.1\text{ s}`
* Model Instantiation (Cell 12): :math:`< 0.05\text{ s}`
* Untrained Autograd Residual Evaluation (Cell 18): :math:`< 0.15\text{ s}`
* 100-Epoch PINN Optimization Loop (Cell 24): :math:`\approx 8.5\text{ s}`
* Unconstrained Benchmark Evaluation (Cell 29): :math:`\approx 1.2\text{ s}`
* Diffusion Grid Forward Pass (Cell 31): :math:`< 0.1\text{ s}`
* Diagnostic Plot Rendering (Cells 08, 26, 33): :math:`\approx 1.5\text{ s}`
* **Total Execution Time**: :math:`< 12.0\text{ s}` (fully headless).

12.2 Memory Footprint
---------------------
* Peak RAM Consumption: :math:`< 250\text{ MB}` above baseline Python runtime.
* Model Parameter Count: ~8,500 parameters :math:`\times 4\text{ bytes} \approx 34\text{ KB}`.
* Autograd Computational Graph: Retained graph tensors consume :math:`\approx 2.5\text{ MB}`
  during backward derivative evaluation.

13. Implementation Notes
========================

13.1 Current Implementation State
---------------------------------
The notebook constitutes an operational scientific research implementation of 1D Richards PDE
physics-informed neural networks. All autograd graphs, analytical solvers, optimization loops,
and diagnostic plotting functions execute cleanly without exceptions.

13.2 Known Implementation Constraints
-------------------------------------
1. **Typo in Unused Function**: Line 249 of Cell 10 contains `psi_abs = tirch.abs(psi) + 1e-6`
   (misspelling `tirch` instead of `torch`).
2. **Benchmark Narrative Discrepancy**: Cell 34 claims ">95% reduction in physical residual error",
   whereas the empirical logged run in Cell 29 recorded a **-1.81%** reduction.
3. **Simplified Darcy Flux Form**: The Darcy flux equation substitutes moisture gradient
   :math:`\frac{\partial \theta}{\partial z}` directly for matric potential gradient
   :math:`\frac{\partial \psi}{\partial z}`, omitting the differential soil water capacity term.
4. **Lack of Model Serialization**: Trained PINN model weights are not saved to disk,
   preventing direct offline loading by Notebook 06.
5. **Decoupled Telemetry Ingestion**: Notebook 05 operates on synthetic collocation points
   rather than ingesting time-series from Notebook 04.

13.3 Forward Path to Production
-------------------------------
* Correct typo in ``torch_van_genuchten_theta``.
* Re-train baseline and reconcile benchmark narrative claims with empirical results.
* Formulate complete mixed-form Richards PDE with analytical capacity :math:`C(\psi) = \frac{\partial \theta}{\partial \psi}`.
* Add model checkpoint serialization cell: ``torch.save(pinn_model.state_dict(), 'pinn_richards_model.pt')``.
* Dynamically drive surface boundary condition :math:`\theta_{\text{top}}(t)` with ingested
  rainfall telemetry.

14. Technical Limitations
=========================

14.1 Current Limitations
------------------------
* **1D Vertical Assumption**: Does not account for lateral subsurface flow or topography-driven
  surface runoff.
* **Static Surface Boundary**: Fixed surface saturation (:math:`0.35`) does not reflect dynamic
  wetting and drying cycles driven by episodic rainfall.
* **Homogeneous Soil Profile**: Assumes uniform hydraulic properties throughout the 200 cm
  column, ignoring natural soil stratification.

14.2 Synthetic Spatial Domain Boundary
--------------------------------------
The collocation coordinates and boundary conditions are synthetic mathematical constructs.
**The generated moisture diffusion fields verify mathematical PDE constraint satisfaction,
not empirical field observations at the Bhadrak/Balasore study footprint.**

15. Requirement Implementation Mapping
======================================

The implementation described across this technical document directly fulfills the
formal software requirements established in ``05_physics_validation_REQUIREMENTS.md``:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Requirement ID
     - Requirement Description
     - Implementing Design Section
   * - **FR-001**
     - Soil hydraulic parameter dictionary definition
     - Section 3.2, Section 4.1, Section 5.1
   * - **FR-002**
     - Active ``sandy_loam`` profile selection and logging
     - Section 3.2, Section 5.1
   * - **FR-003**
     - NumPy closed-form SWRC & conductivity solvers
     - Section 3.3, Section 4.2
   * - **FR-004**
     - Continuous curve sampling across :math:`\psi \in [0.1, 10000]\text{ cm}`
     - Section 3.3, Section 10.1, Section 11.2
   * - **FR-005**
     - Differentiable PyTorch hydraulic operators
     - Section 3.4, Section 4.2, Section 9.1
   * - **FR-006**
     - 4-layer MLP PINN with Sigmoid range scaling
     - Section 3.5, Section 4.3, Section 9.3
   * - **FR-007**
     - Autograd space-time PDE residual evaluation
     - Section 3.6, Section 4.4, Section 6.2, Section 6.3
   * - **FR-008**
     - Uniform space-time collocation point generation
     - Section 3.7, Section 4.5, Section 6.5
   * - **FR-009**
     - Untrained PINN PDE residual baseline benchmark
     - Section 3.7, Section 11.2
   * - **FR-010**
     - Top (:math:`0.35`) and bottom (:math:`0.15`) boundary condition tensors
     - Section 3.8, Section 4.5, Section 6.4
   * - **FR-011**
     - Composite loss formulation (:math:`\mathcal{L}_{\text{total}}`)
     - Section 3.9, Section 6.4
   * - **FR-012**
     - 100-epoch Adam optimization with gradient clipping
     - Section 3.10, Section 6.4, Section 9.2
   * - **FR-013**
     - Log-scale convergence telemetry visualization
     - Section 3.11, Section 10.1
   * - **FR-014**
     - Benchmark against unconstrained baseline model
     - Section 3.12, Section 11.2, Section 13.2
   * - **FR-015**
     - :math:`100 \times 100` continuous moisture diffusion mesh
     - Section 3.13, Section 5.3, Section 10.1
   * - **DI-001**
     - Strict output bounding within :math:`[\theta_r, \theta_s]`
     - Section 3.5, Section 4.3, Section 9.3
   * - **DI-002**
     - Clamped normalized saturation in conductivity
     - Section 3.4, Section 9.1
   * - **DI-003**
     - Higher-order autograd graph retention
     - Section 3.6, Section 4.4, Section 6.3
   * - **DI-004**
     - Collocation depth boundaries (:math:`0 \le z \le 200\text{ cm}`)
     - Section 3.7, Section 4.5
   * - **DI-005**
     - Collocation time boundaries (:math:`0 \le t \le 168\text{ hrs}`)
     - Section 3.7, Section 4.5
   * - **DI-006**
     - Non-negative boundary condition squared errors
     - Section 3.9, Section 6.4
   * - **IF-001**
     - Input-output tensor dimension contracts
     - Section 4.3, Section 5.2
   * - **IF-002**
     - PDE residual tuple return contract
     - Section 3.6, Section 7.2
   * - **IF-003**
     - Composite loss evaluator return contract
     - Section 3.9, Section 6.4
   * - **IF-004**
     - Diffusion grid shape :math:`(100, 100)`
     - Section 3.13, Section 5.3
   * - **UQ-001**
     - Gradient norm clipping at threshold :math:`1.0`
     - Section 3.10, Section 9.2
   * - **UQ-002**
     - Dynamic collocation resampling per epoch
     - Section 3.10, Section 6.5
   * - **UQ-003**
     - High-precision metric reporting (6 decimal places)
     - Section 3.7, Section 3.10, Section 3.12
   * - **NF-001**
     - Deterministic random seeds (PyTorch 42, NumPy 42)
     - Section 3.1, Section 11.1
   * - **NF-002**
     - Unattended headless execution
     - Section 2.1, Section 12.1
   * - **NF-003**
     - Dark telemetry UI styling on generated figures
     - Section 3.1, Section 8.3, Section 10.1
   * - **NF-004**
     - Dynamic execution device selection (CUDA or CPU)
     - Section 3.1, Section 8.2
