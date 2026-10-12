=====================================================================
THE MRIDANSH (AETHER-MRID1607X) - Notebook 03: Spatial Modeling
=====================================================================

:Project: THE MRIDANSH - Unified Soil State Estimation System
:Engine: AETHER-MRID1607X (Multi-Domain Soil Intelligence Engine)
:Notebook: ``03-spatial-modeling.ipynb``
:Sprint phase: Days 5-6 of the 18-Day Scientific Validation Sprint
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
The primary technical objective of ``03-spatial-modeling.ipynb`` is to translate
two-dimensional spatial Earth Observation (EO) rasters into topologically connected
spatial graph representations :math:`G = (V, E)`, derive continuous terrain
derivatives (topographic slope and aspect) from Digital Elevation Models (DEM), and
implement a spectral Graph Convolutional Network (GCN) architecture to perform
spatial representation learning across irregular terrain nodes.

1.2 System Context
------------------
Within the **THE MRIDANSH** (*AETHER-MRID1607X*) architecture, raw satellite telemetry
is acquired during Notebook 01, screened, filtered, and scaled in Notebook 02.
Notebook 03 serves as the foundational spatial discretization layer. It bridges the
gap between traditional raster grids and graph-based physics engines:

* Upstream: Consumes preprocessed telemetry tables and spatial domain boundaries.
* Core Engine: Discretizes terrain into a 4-neighbor spatial lattice, derives surface
  hydraulic slope angles, and executes spatial message-passing convolutions.
* Downstream: Emits compressed graph topologies (``spatial_graph_mesh.npz``) and
  spatial latent embedding tensors (``spatial_gcn_embeddings.pt``) to initialize
  spatio-temporal Physics-Informed Neural Network (PINN) PDE operators in Notebooks 04
  and 05.

1.3 Design Boundary
-------------------
The design of Notebook 03 is bounded as follows:

* **In Boundary**: Spatial raster discretization, Sobel elevation gradient filtering,
  topographic slope and aspect derivation, Euclidean distance matrix evaluation,
  4-connected graph adjacency matrix construction, degree distribution calculation,
  PyTorch graph tensor conversion, multi-modal node feature normalization, Kipf-Welling
  renormalized graph Laplacian evaluation, 2-layer GCN forward evaluation, and artifact
  serialization.
* **Out of Boundary**: GCN backpropagation and weight optimization (the forward pass
  evaluates structural initialization), time-series recurrence (handled in Notebook 04),
  hydrological PDE loss terms (handled in Notebook 05), and interactive cloud UI rendering.

1.4 Relationship to Requirements
--------------------------------
This technical description details the software architecture, internal mechanisms,
algorithms, data flows, and concrete implementations that realize the requirements
stipulated in ``03_spatial_modeling_REQUIREMENTS.md``. Every mathematical model and
code construct described herein directly fulfills one or more formal requirement
statements (see Section 15 for complete requirement-to-design mapping).

2. Architecture
===============

2.1 Notebook Architecture
-------------------------
The notebook is structured into two sequential phases across 29 notebook cells:

* **Phase 1: Terrain Derivatives and Spatial Graph Mesh (Sprint Day 5)**:
  Handles telemetry ingestion, spatial grid initialization, discrete Sobel terrain
  differentiation, topographic metric extraction, spatial adjacency calculation,
  diagnostic rendering, and topological archive export.
* **Phase 2: Graph Convolutional Network and Latent Feature Extraction (Sprint Day 6)**:
  Handles PyTorch graph tensor conversion, multi-sensor node feature vector assembly,
  spectral Laplacian renormalization, 2-layer GCN module instantiation, forward-pass
  execution under evaluation mode, embedding map visualization, and tensor persistence.

2.2 Processing Pipeline
-----------------------
The operational pipeline executes along the following linear flow:

.. code-block:: text

   [preprocessed_telemetry.csv]
               │
               ▼
   [20x20 Spatial Sub-Grid Footprint] ────► [Sobel Elevation Filtering]
               │                                      │
               ├──────────────────────────────► [Slope & Aspect Extraction]
               │                                      │
               ▼                                      ▼
   [Euclidean Distance Matrix]            [Multi-Sensor Node Matrix X]
               │                                (DEM, Slope, SAR, NDVI)
               ▼                                      │
   [4-Neighbor Adjacency A]                           │
               │                                      │
               ├──────────────────────────────► [spatial_graph_mesh.npz]
               │
               ▼
   [Renormalized Laplacian Â] ────────────────────────┐
                                                      ▼
                                       [2-Layer Spatial GCN Architecture]
                                                      │
                                                      ▼
                                       [Forward Pass Latent Matrix Z]
                                                      │
                                                      ▼
                                       [spatial_gcn_embeddings.pt]

2.3 Component Relationships
---------------------------
The software components interact through explicit functional boundaries:

1. **Topographic Engine**: Operates directly on the 2D elevation grid using SciPy image
   processing filters to compute directional surface gradients.
2. **Graph Mesh Engine**: Translates regular 2D grid coordinates into an abstract graph
   topology :math:`(V, E)` using SciPy spatial distance operators.
3. **Feature Assembler**: Normalizes heterogeneous physical quantities (elevation,
   angular slope, radar backscatter, optical reflectance) into a unified zero-mean
   unit-variance node feature tensor.
4. **PyTorch GCN Core**: Performs spectral neighborhood message passing using dense
   tensor contractions against the renormalized Laplacian matrix.

2.4 Data Flow
-------------
The data flow transitions through three distinct operational spaces:

1. **2D Raster Space**: Arrays of shape :math:`(20, 20)` representing spatial surface
   quantities across a :math:`10\text{ m}` grid cell lattice.
2. **Topological Graph Space**: Node coordinates :math:`(400, 2)`, adjacency matrix
   :math:`A \in \{0, 1\}^{400 \times 400}`, and directed edge index tensor of shape
   :math:`(2, 1520)`.
3. **Latent Manifold Space**: Input feature tensor :math:`X \in \mathbb{R}^{400 \times 4}`
   projected into latent feature embeddings :math:`Z \in \mathbb{R}^{400 \times 8}`.

3. Execution Flow
=================

3.1 Initialization
------------------
* Imports system dependencies (``sys``, ``os``, ``json``, ``numpy``, ``pandas``,
  ``scipy.ndimage``, ``scipy.spatial``, ``matplotlib.pyplot``).
* Configures inline rendering and sets the project dark telemetry theme:
  background ``#000000``, axis borders ``#00FFCC`` (width 1.2), grid lines ``#1A3344``
  (dashed, alpha 0.5), and monospace font family.
* Emits initialization status banner.

3.2 Ingestion & Spatial Footprint Setup
---------------------------------------
* Verifies presence of upstream dataset at
  ``/kaggle/input/datasets/gourgopalmohapatra/preprocessed-telemetry-csv/preprocessed_telemetry.csv``.
* Ingests 35 records of tabular telemetry.
* Sets spatial grid dimension constant ``GRID_DIM = 20`` (:math:`N = 400` vertices).
* Generates continuous synthetic DEM surface array via Gaussian smoothing filter
  (``sigma = 1.5``) over uniform elevation bounds :math:`[10.0, 30.0]\text{ m}` under
  random seed 101.
* Generates synthetic SAR backscatter surface array over uniform bounds
  :math:`[-16.0, -6.0]\text{ dB}`.

3.3 Topographic Gradient Extraction
-----------------------------------
* Sets spatial resolution parameter ``DX = 10.0`` meters.
* Applies 2D Sobel edge operators along axis 1 (horizontal, :math:`x`) and axis 0
  (vertical, :math:`y`), normalized by the kernel denominator :math:`8 \times \Delta X`.
* Computes surface slope in radians and converts to degrees.
* Computes surface aspect angle in degrees using four-quadrant arctangent, oriented
  clockwise from North.
* Logs mean slope, slope range, and mean aspect to stdout.

3.4 Spatial k-NN Graph Mesh Construction
----------------------------------------
* Constructs 2D meshgrid coordinates across the :math:`20 \times 20` lattice and flattens
  into a coordinate vertex array of shape :math:`(400, 2)`.
* Computes the complete Euclidean distance matrix :math:`D \in \mathbb{R}^{400 \times 400}`.
* Filters distances with condition :math:`0 < d(v_i, v_j) \le 1.01` to isolate strictly
  adjacent 4-grid neighbors, yielding a binary unweighted adjacency matrix :math:`A`.
* Computes node degree vector :math:`\mathbf{d} = A \mathbf{1}` and logs graph topological
  statistics (vertices, edges, mean degree).

3.5 Graph Mesh Export
---------------------
* Ensures directory ``/kaggle/working/data_processed/`` exists.
* Serializes ``adj_matrix``, ``node_coords``, ``dem_grid``, and ``slope_deg`` into
  compressed NumPy archive ``spatial_graph_mesh.npz``.
* Outputs Day 5 completion milestone banner.

3.6 Graph Tensor Initialization
-------------------------------
* Sets PyTorch deterministic seed ``torch.manual_seed(42)``.
* Loads ``spatial_graph_mesh.npz`` from disk (falling back to memory variables if missing).
* Extracts source and target non-zero indices from the adjacency matrix.
* Assembles PyTorch directed edge tensor ``edge_index`` of shape :math:`(2, 1520)`.

3.7 Multi-Sensor Node Feature Assembly
--------------------------------------
* Flattens 2D arrays ``dem_grid`` and ``slope_deg`` into 1D node arrays.
* Applies z-score standardization to elevation and slope with :math:`10^{-6}` numerical
  epsilon stabilization.
* Draws synthetic SAR attribute from :math:`\mathcal{N}(0, 1)` and synthetic NDVI
  attribute from :math:`\mathcal{U}(0, 1)`.
* Horizontally stacks features into node matrix :math:`X \in \mathbb{R}^{400 \times 4}`
  and converts to a 32-bit floating point PyTorch tensor.

3.8 Normalized Laplacian Operator Computation
---------------------------------------------
* Adds identity matrix self-loops: :math:`\tilde{A} = A + I_{400}`.
* Sums row degrees :math:`\tilde{D}_i = \sum_j \tilde{A}_{ij}`.
* Forms diagonal inverse square-root matrix :math:`\tilde{D}^{-1/2} = \operatorname{diag}(\tilde{D}^{-0.5})`.
* Evaluates symmetric normalized Laplacian: :math:`\hat{A} = \tilde{D}^{-1/2} \tilde{A} \tilde{D}^{-1/2}`.

3.9 GCN Architecture Definition
-------------------------------
* Instantiates custom ``GraphConvLayer`` modules wrapping linear projections with dense
  normalized adjacency message passing.
* Constructs composite ``SpatialGCN`` module chaining two convolution layers with
  intermediate ReLU activation and dropout regularization (:math:`p = 0.1`).
* Parameter dimensions: Input features :math:`4`, Hidden dimension :math:`16`, Output
  latent channels :math:`8`.

3.10 Forward Propagation & Embedding Extraction
-----------------------------------------------
* Sets model to evaluation mode (``model.eval()``).
* Disables gradient tracking (``torch.no_grad()``).
* Executes forward propagation: :math:`Z = \text{SpatialGCN}(X, \hat{A})`.
* Converts latent tensor to NumPy array and audits output extrema.

3.11 Diagnostic Visualizations
------------------------------
* Generates three aerospace-standard telemetry figures:
  1. *Aerospace Plot 1*: 2-panel elevation map (terrain colormap) and derived slope map
     (magma colormap) with embedded derivative statistics overlay.
  2. *Aerospace Plot 2*: Sub-matrix heatmap of the first 50 nodes of spatial adjacency
     matrix :math:`A_{ij}` with mesh specifications overlay.
  3. *Aerospace Plot 3*: 2-panel spatial sub-grid visualization of GCN latent channels 0
     and 1 with network diagnostic overlays.

3.12 Embedding Persistence
--------------------------
* Serializes a dictionary containing ``spatial_embeddings``, ``model_state_dict``, and
  ``A_hat`` into ``/kaggle/working/data_processed/spatial_gcn_embeddings.pt``.
* Emits Day 6 completion diagnostic report.

4. Component Design
===================

4.1 Telemetry Ingestion & Spatial Footprint Generator
-----------------------------------------------------
* **Function**: Loads upstream tabular data and initializes the spatial domain.
* **Mechanism**: Ingests ``preprocessed_telemetry.csv`` via pandas. To simulate spatial
  variability across the study domain, a 2D Gaussian filter (:math:`\sigma = 1.5`) is
  convolved with a uniform random field :math:`[10.0, 30.0]\text{ m}` to construct a
  spatially continuous elevation surface mimicking natural topography.
* **Outputs**: ``dem_grid`` :math:`(20, 20)`, ``sar_grid`` :math:`(20, 20)`.

4.2 Topographic Derivative Engine
---------------------------------
* **Function**: Evaluates continuous physical terrain metrics from elevation rasters.
* **Mechanism**: Employs discrete Sobel horizontal and vertical convolutional kernels:

  .. code-block:: text

     Sobel_x = [[-1,  0,  1],      Sobel_y = [[-1, -2, -1],
                [-2,  0,  2],                 [ 0,  0,  0],
                [-1,  0,  1]]                 [ 1,  2,  1]]

  Normalized by the kernel scale factor :math:`8 \cdot \Delta X`. Evaluates magnitude
  and azimuth of the steepest descent vector.
* **Outputs**: ``slope_deg`` :math:`(20, 20)`, ``aspect_deg`` :math:`(20, 20)`.

4.3 Spatial Graph Mesh Builder
------------------------------
* **Function**: Generates topological graph meshes from grid cell coordinates.
* **Mechanism**:
  1. Generates grid indices :math:`(x, y) \in \{0, \dots, 19\} \times \{0, \dots, 19\}`.
  2. Computes pairwise Euclidean distances between all 400 coordinate tuples.
  3. Applies bilateral distance thresholding :math:`0 < d_{ij} \le 1.01` to extract
     orthogonal grid neighbors while excluding diagonal connections and self-loops.
* **Outputs**: ``adj_matrix`` :math:`(400, 400)`, ``node_coords`` :math:`(400, 2)`.

4.4 Graph Neural Network Core: GraphConvLayer & SpatialGCN
----------------------------------------------------------
* **Function**: Executes spatial neighborhood message passing.
* **Mechanism**:
  - ``GraphConvLayer``: Implements the mathematical operation:

    .. math::

       H_{\text{out}} = \hat{A} \cdot (H_{\text{in}} W + b)

    where :math:`W` is a learnable weight matrix and :math:`b` is a learnable bias vector.
  - ``SpatialGCN``: Encapsulates two convolution stages:

    .. math::

       H^{(1)} = \operatorname{ReLU}(\operatorname{GConv}_1(X, \hat{A}))

    .. math::

       H^{(1)}_{\text{drop}} = \operatorname{Dropout}(H^{(1)}, p = 0.1)

    .. math::

       Z = \operatorname{GConv}_2(H^{(1)}_{\text{drop}}, \hat{A})

4.5 Persistence & Artifact Serializer
-------------------------------------
* **Function**: Guarantees filesystem integrity and persists model artifacts.
* **Mechanism**: Utilizes ``numpy.savez_compressed`` for array topologies and
  ``torch.save`` for PyTorch neural network tensors and weights.

5. Data Structures
==================

5.1 Input Schema
----------------
Table ``preprocessed_telemetry.csv`` schema (loaded in Step 1):

.. list-table::
   :header-rows: 1
   :widths: 25 20 20 35

   * - Column
     - Type
     - Unit
     - Description
   * - ``timestamp``
     - string
     - UTC ISO
     - Observation acquisition timestamp
   * - ``s1_vv_lee_zscore``
     - float64
     - standard units
     - Lee-filtered, z-score standardized SAR VV
   * - ``s2_cloud_cover_pct``
     - float64
     - percent
     - Scene cloud cover percentage
   * - ``dem_elevation_m``
     - float64
     - meters
     - In-situ or pixel DEM elevation

5.2 Intermediate Data Structures
--------------------------------
1. **DEM Array** (``dem_grid``): NumPy float64 array of shape :math:`(20, 20)`.
2. **Topographic Gradient Arrays** (``dz_dx``, ``dz_dy``): NumPy float64 arrays of shape
   :math:`(20, 20)`.
3. **Slope Matrix** (``slope_deg``): NumPy float64 array of shape :math:`(20, 20)`.
4. **Aspect Matrix** (``aspect_deg``): NumPy float64 array of shape :math:`(20, 20)`.
5. **Node Coordinates** (``node_coords``): NumPy int64 array of shape :math:`(400, 2)`.
6. **Distance Matrix** (``dist_mat``): NumPy float64 array of shape :math:`(400, 400)`.
7. **Graph Adjacency Matrix** (``adj_matrix``): NumPy float64 binary array of shape
   :math:`(400, 400)`.
8. **Normalized Laplacian Tensor** (``A_hat``): PyTorch float32 tensor of shape
   :math:`(400, 400)`.
9. **Node Feature Tensor** (``X_tensor``): PyTorch float32 tensor of shape
   :math:`(400, 4)`.

5.3 Output Schema
-----------------
1. **Latent Node Embedding Tensor** (``spatial_embeddings``): PyTorch float32 tensor of
   shape :math:`(400, 8)` representing 8 continuous spatial latent channels per grid node.

5.4 Graph Mesh & Tensor Schema
------------------------------
Archive ``spatial_graph_mesh.npz`` keys:

* ``adj_matrix``: float64 array of shape :math:`(400, 400)`.
* ``node_coords``: int64 array of shape :math:`(400, 2)`.
* ``dem_grid``: float64 array of shape :math:`(20, 20)`.
* ``slope_deg``: float64 array of shape :math:`(20, 20)`.

Archive ``spatial_gcn_embeddings.pt`` serialized dictionary keys:

* ``spatial_embeddings``: PyTorch tensor :math:`(400, 8)`.
* ``model_state_dict``: PyTorch state dictionary containing weights and biases:
  - ``gconv1.linear.weight``: :math:`(16, 4)`
  - ``gconv1.linear.bias``: :math:`(16,)`
  - ``gconv2.linear.weight``: :math:`(8, 16)`
  - ``gconv2.linear.bias``: :math:`(8,)`
* ``A_hat``: PyTorch tensor :math:`(400, 400)`.

6. Algorithms and Methods
=========================

6.1 Discrete Topographic Gradient via Sobel Kernels
---------------------------------------------------
Spatial elevation gradients are computed using discrete Sobel directional convolutions:

.. math::

   \frac{\partial Z}{\partial x} = \frac{1}{8 \cdot \Delta X} \cdot (\operatorname{Sobel}_x * Z)

.. math::

   \frac{\partial Z}{\partial y} = \frac{1}{8 \cdot \Delta X} \cdot (\operatorname{Sobel}_y * Z)

Where :math:`\Delta X = 10.0\text{ m}` is the nominal pixel resolution. The factor of 8
accounts for the weighted averaging of neighboring finite difference baselines across
the :math:`3 \times 3` spatial window.

6.2 Slope & Aspect Mathematical Formulations
--------------------------------------------
Surface slope angle :math:`\theta_{\text{slope}}` quantifies the magnitude of the terrain
gradient vector:

.. math::

   \theta_{\text{slope}} = \arctan\left(\sqrt{\left(\frac{\partial Z}{\partial x}\right)^2 + \left(\frac{\partial Z}{\partial y}\right)^2}\right) \times \frac{180}{\pi}

Surface aspect :math:`\phi_{\text{aspect}}` quantifies the directional azimuth of steepest
gravitational descent:

.. math::

   \phi_{\text{aspect}} = \left(\operatorname{atan2}\left(-\frac{\partial Z}{\partial y}, \frac{\partial Z}{\partial x}\right) \times \frac{180}{\pi}\right) \pmod{360}

The negation of :math:`\frac{\partial Z}{\partial y}` correctly aligns the Cartesian
derivative with top-to-bottom raster image coordinates.

6.3 Spatial k-NN Adjacency Matrix Construction
----------------------------------------------
For node coordinates :math:`v_i = (x_i, y_i)` on a 2D integer lattice, pairwise Euclidean
distance is given by:

.. math::

   d(v_i, v_j) = \sqrt{(x_i - x_j)^2 + (y_i - y_j)^2}

The binary adjacency operator is defined by:

.. math::

   A_{ij} = \begin{cases}
   1, & \text{if } 0 < d(v_i, v_j) \le 1.01 \\
   0, & \text{otherwise}
   \end{cases}

Because diagonal neighbors have Euclidean distance :math:`\sqrt{2} \approx 1.414 > 1.01`,
this strictly extracts 4-connected cardinal neighbors (North, South, East, West).

6.4 Kipf-Welling Renormalized Laplacian Operator
-----------------------------------------------
Direct application of raw adjacency :math:`A` leads to numerical instability and scale
explosion during multi-layer neural message passing. The software computes the Kipf &
Welling (2017) first-order spectral Chebyshev approximation:

1. Add self-loops to allow each node to preserve its own feature representation:

   .. math::

      \tilde{A} = A + I_N

2. Compute the modified degree matrix:

   .. math::

      \tilde{D}_{ii} = \sum_{j=1}^{N} \tilde{A}_{ij}, \quad \tilde{D}_{ij} = 0 \text{ for } i \ne j

3. Perform symmetric inverse square-root normalization:

   .. math::

      \hat{A} = \tilde{D}^{-\frac{1}{2}} \tilde{A} \tilde{D}^{-\frac{1}{2}}

For any two connected nodes :math:`i` and :math:`j`, the normalized edge weight is:

.. math::

   \hat{A}_{ij} = \frac{1}{\sqrt{\tilde{D}_{ii} \tilde{D}_{jj}}}

6.5 Graph Convolutional Forward Pass Mechanics
----------------------------------------------
The layer-wise message passing propagation rule is evaluated as:

.. math::

   H^{(l+1)} = \sigma\left(\hat{A} H^{(l)} W^{(l)} + b^{(l)}\right)

Where:
* :math:`H^{(0)} = X \in \mathbb{R}^{400 \times 4}` is the multi-sensor node feature matrix.
* :math:`W^{(0)} \in \mathbb{R}^{4 \times 16}` and :math:`b^{(0)} \in \mathbb{R}^{16}`
  represent layer 1 linear transformations.
* :math:`\sigma` is the element-wise Rectified Linear Unit (:math:`\operatorname{ReLU}`).
* :math:`\hat{A} \cdot H` computes the normalized spatial neighborhood average.

6.6 Multi-Sensor Feature Z-Score Standardization
------------------------------------------------
To ensure equal gradient contribution across disparate physical units, terrain features
are standardized prior to GCN input:

.. math::

   x_{\text{norm}} = \frac{x - \mu_x}{\sigma_x + 10^{-6}}

Where :math:`\mu_x` and :math:`\sigma_x` are the empirical mean and standard deviation of
the raster array, and :math:`10^{-6}` guarantees numerical division stability.

7. Interfaces
-------------

7.1 Input Interfaces
--------------------
* **Primary Path**: ``/kaggle/input/datasets/gourgopalmohapatra/preprocessed-telemetry-csv/preprocessed_telemetry.csv``.
* **Format**: Comma-Separated Values (CSV), UTF-8 encoded.
* **Behavior on Failure**: Emits warning message and continues execution using in-memory
  spatial raster generators.

7.2 Output Interfaces
---------------------
* **Primary Path**: ``/kaggle/working/data_processed/``.
* **Format**: Binary NumPy compressed archive (``.npz``) and PyTorch serialized state
  dictionary (``.pt``).

7.3 File Interfaces
-------------------
* ``spatial_graph_mesh.npz``:
  - File size: ~10.8 KB.
  - Serialization engine: ``numpy.savez_compressed``.
* ``spatial_gcn_embeddings.pt``:
  - File size: ~657 KB (uncompressed PyTorch tensor archive).
  - Serialization engine: ``torch.save``.

7.4 Downstream Consumer Interfaces
----------------------------------
* **Consumer**: Notebook 04 (``04-temporal-modeling.ipynb``) and Notebook 05 (``05-physics-validation.ipynb``).
* **Contract**: Downstream notebooks deserialize ``spatial_gcn_embeddings.pt`` to extract
  the spatial embedding matrix :math:`Z \in \mathbb{R}^{400 \times 8}` and integrate it as
  a spatial conditioning tensor into temporal ConvLSTM / PINN state estimators.

8. Configuration
----------------

8.1 Constants
-------------
* ``GRID_DIM = 20``: Grid dimension along each axis (total nodes :math:`N = 400`).
* ``DX = 10.0``: Spatial cell resolution in meters.
* ``K_NEIGHBORS = 4``: Target neighborhood degree for orthogonal grid connectivity.
* ``EUC_DIST_MAX = 1.01``: Maximum Euclidean threshold for 4-neighbor adjacency.
* ``F_IN = 4``: Number of input node features.
* ``HIDDEN_DIM = 16``: Latent channel dimension of GCN layer 1.
* ``F_OUT = 8``: Latent channel dimension of GCN layer 2.
* ``DROPOUT_P = 0.1``: Dropout probability during training mode.

8.2 Environment
---------------
* Python 3.10+ execution runtime.
* Linux x86_64 container environment (Kaggle kernel instance).
* Backend: PyTorch CPU / CUDA runtime.

8.3 Runtime Configuration
-------------------------
* ``%matplotlib inline``: Interactive graphics backend.
* Matplotlib stylesheet: ``dark_background``.
* Plotting theme parameters:
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
* ``scipy >= 1.10.0``
* ``torch >= 2.0.0``
* ``matplotlib >= 3.7.0``

9. Error Handling
-----------------

9.1 Absent Input File
---------------------
When ``preprocessed_telemetry.csv`` is not found at the hardcoded path, the script
traverses an ``else`` branch, emitting:

.. code-block:: text

   ⚠️ Preprocessed path not found. Initialized In-Memory Stream for Notebook 03.

Execution proceeds without raising an unhandled exception.

9.2 Zero Standard Deviation Handling
------------------------------------
In Cell 18, standard deviation scaling denominators include an explicit epsilon term:

.. code-block:: python

   f_dem = (dem_arr.flatten() - dem_arr.mean()) / (dem_arr.std() + 1e-6)

Preventing ``ZeroDivisionError`` or ``NaN`` propagation when processing completely flat
elevation plates.

9.3 Boundary Node Degree Disparity
----------------------------------
Nodes located along grid boundaries inherently possess fewer neighbors than interior nodes
(corners: 2 neighbors, edges: 3 neighbors, interior: 4 neighbors). The normalized Laplacian
formulation mathematically accounts for this disparity by normalizing each edge by
:math:`\frac{1}{\sqrt{\tilde{D}_{ii} \tilde{D}_{jj}}}`, ensuring boundary nodes do not suffer
numerical gradient explosion or artificial attenuation.

9.4 Missing Pre-computation Fallback
------------------------------------
Cell 16 checks for the physical presence of ``spatial_graph_mesh.npz``. If absent, it
falls back to local kernel memory variables (``adj_mat = adj_matrix``), preventing script
termination during interactive sequential runs.

10. Generated Artifacts
=======================

10.1 spatial_graph_mesh.npz
---------------------------
* **Location**: ``/kaggle/working/data_processed/spatial_graph_mesh.npz``
* **Content**: 4 arrays:
  - ``adj_matrix``: Sparse-equivalent dense binary adjacency (:math:`400 \times 400`).
  - ``node_coords``: Coordinate indices of each node (:math:`400 \times 2`).
  - ``dem_grid``: Elevation raster array (:math:`20 \times 20`).
  - ``slope_deg``: Topographic surface slope raster (:math:`20 \times 20`).

10.2 spatial_gcn_embeddings.pt
------------------------------
* **Location**: ``/kaggle/working/data_processed/spatial_gcn_embeddings.pt``
* **Content**: PyTorch dictionary:
  - ``spatial_embeddings``: Latent tensor (:math:`400 \times 8`).
  - ``model_state_dict``: Weight tensors for ``gconv1`` and ``gconv2``.
  - ``A_hat``: Renormalized symmetric Laplacian matrix (:math:`400 \times 400`).

10.3 Diagnostic Figures
-----------------------
* **Aerospace Plot 1**: Subplot 1 (DEM surface elevation, meters) and Subplot 2
  (Derived topographic slope, degrees).
* **Aerospace Plot 2**: Visual representation of the first :math:`50 \times 50` block of
  graph adjacency matrix :math:`A_{ij}`.
* **Aerospace Plot 3**: Subplot 1 (GCN latent embedding Channel 0) and Subplot 2
  (GCN latent embedding Channel 1).

11. Reproducibility
===================

11.1 Random Seeds
-----------------
The notebook enforces deterministic reproducibility across two key pseudorandom number
generators:

1. **NumPy Generator**: Seed ``101`` is fixed prior to spatial grid generation in Cell 04:

   .. code-block:: python

      np.random.seed(101)

2. **PyTorch Generator**: Seed ``42`` is fixed prior to tensor allocation and neural
   network weight initialization in Cell 16:

   .. code-block:: python

      torch.manual_seed(42)

11.2 Environment
----------------
Execution is fully deterministic across identical hardware and package versions. Clean
kernel re-execution reproduces bit-identical outputs across all numerical arrays and
model parameter tensors.

11.3 Deterministic Numerical Invariants
---------------------------------------
Under seeds 101 and 42, the following exact numerical invariants are guaranteed:

* Grid Vertices: Exactly :math:`400`.
* Undirected Graph Edges: Exactly :math:`760`.
* Directed Edge Index Entries: Exactly :math:`1520`.
* Mean Topographic Slope: Exactly :math:`3.06^\circ`.
* Minimum Topographic Slope: Exactly :math:`0.13^\circ`.
* Maximum Topographic Slope: Exactly :math:`8.96^\circ`.
* Mean Topographic Aspect: Exactly :math:`182.17^\circ`.
* Mean Graph Node Degree: Exactly :math:`3.8` neighbors.
* Forward Pass Latent Embedding Minimum: Exactly :math:`-0.4555`.
* Forward Pass Latent Embedding Maximum: Exactly :math:`0.3316`.

12. Performance Characteristics
===============================

12.1 Execution Time Profile
---------------------------
Across standard x86_64 CPU hardware (Intel Xeon / AMD EPYC 2.2 GHz):

* Initialization & Imports (Cell 02): :math:`< 0.5\text{ s}`
* Spatial Grid & Elevation Differentiation (Cells 04, 06): :math:`< 0.1\text{ s}`
* Euclidean Distance Matrix Evaluation (Cell 10): :math:`< 0.05\text{ s}`
* PyTorch Model Instantiation & Laplacian Calculation (Cell 20): :math:`< 0.05\text{ s}`
* GCN Forward Pass Execution (Cell 22): :math:`< 0.01\text{ s}`
* Diagnostic Plot Rendering (Cells 08, 12, 24): :math:`\approx 1.2\text{ s}`
* File Serialization I/O (Cells 14, 26): :math:`< 0.2\text{ s}`
* **Total Execution Time**: :math:`< 2.5\text{ s}` (fully headless).

12.2 Memory Footprint
---------------------
* Peak RAM Utilization: :math:`< 180\text{ MB}` above baseline Python runtime.
* In-Memory Tensor Footprint:
  - Distance Matrix: :math:`400 \times 400 \times 8\text{ bytes} \approx 1.28\text{ MB}`.
  - Adjacency Matrix: :math:`400 \times 400 \times 8\text{ bytes} \approx 1.28\text{ MB}`.
  - Laplacian Matrix (:math:`\hat{A}`): :math:`400 \times 400 \times 4\text{ bytes} \approx 0.64\text{ MB}`.
  - Node Features (:math:`X`): :math:`400 \times 4 \times 4\text{ bytes} \approx 6.4\text{ KB}`.
  - Latent Embeddings (:math:`Z`): :math:`400 \times 8 \times 4\text{ bytes} \approx 12.8\text{ KB}`.

12.3 Data Volume
----------------
* Input Telemetry CSV: :math:`\approx 9.3\text{ KB}`.
* Output Graph Mesh Archive (``spatial_graph_mesh.npz``): :math:`\approx 10.9\text{ KB}`.
* Output PyTorch Checkpoint (``spatial_gcn_embeddings.pt``): :math:`\approx 657\text{ KB}`.

13. Implementation Notes
========================

13.1 Current Implementation State
---------------------------------
The notebook represents an operational, fully executing research baseline. All numerical
operations, mathematical transformations, neural network modules, and artifact writers
execute without exceptions.

13.2 Known Implementation Constraints
-------------------------------------
1. **Plot 3 Channel Duplication**: In Cell 24, both ``emb_ch0`` and ``emb_ch1`` are
   extracted, but line 490 invokes ``im2 = ax2.imshow(emb_ch0)`` instead of
   ``ax2.imshow(emb_ch1)``, causing Channel 0 to be rendered in both subplots.
2. **Decoupled Grid Telemetry**: Step 1 ingests ``df_prep``, but Step 1 grid generation
   does not interpolate values from this table; it generates synthetic random fields.
3. **SAR Grid Feature Disconnection**: Cell 04 computes ``sar_grid``, but Cell 18
   generates ``f_sar`` as an independent random normal variable rather than flattening
   ``sar_grid``.
4. **Hardcoded Kaggle Paths**: Script relies on ``/kaggle/input/`` and ``/kaggle/working/``
   prefixes, requiring manual path overrides for non-Kaggle environments.
5. **Dense Matrix Multiplications**: The GCN forward pass executes dense matrix multiplication
   against a :math:`(400, 400)` Laplacian rather than utilizing sparse message passing.

13.3 Forward Path to Production
-------------------------------
* Rectify Plot 3 Channel 1 rendering call.
* Replace synthetic raster generation with true georeferenced GeoTIFF ingestion.
* Refactor paths to use environment variables (``DATA_DIR``, ``OUTPUT_DIR``).
* Transition GCN layers to PyTorch Geometric (PyG) ``MessagePassing`` to support large-scale
  sparse spatial graphs.

14. Technical Limitations
=========================

14.1 Current Limitations
------------------------
* **Non-Georeferenced Grids**: Node coordinates are discrete grid index pairs :math:`(x, y)`
  and lack explicit geospatial coordinates (EPSG:4326 / EPSG:32645).
* **Un-trained Neural Weights**: GCN weights are pseudorandomly initialized; spatial
  embeddings reflect structural neighborhood smoothing rather than trained feature
  representations.
* **Regular Lattice Assumption**: The graph generation logic assumes a regular square
  grid and does not currently support unstructured triangular or Voronoi meshes.

14.2 Synthetic Data Boundary
----------------------------
As emphasized in the system requirements, the elevation and microwave backscatter arrays
processed in this notebook are synthetic pseudorandom fields. While the computational
algorithms (Sobel filters, graph convolutions, Laplacian normalizations) are mathematically
sound and verified, **the generated latent embeddings do not represent real-world physical
measurements of the Bhadrak/Balasore study area**.

14.3 External Dependencies
--------------------------
The architecture requires PyTorch and SciPy. Execution within restricted embedded runtimes
requires export of the mathematical operators to ONNX or C++ TensorRT engines.

15. Requirement Implementation Mapping
======================================

The implementation described across this technical document directly fulfills the
formal software requirements established in ``03_spatial_modeling_REQUIREMENTS.md``:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Requirement ID
     - Requirement Description
     - Implementing Design Section
   * - **FR-001**
     - Telemetry CSV verification and fallback
     - Section 3.2, Section 4.1, Section 7.1
   * - **FR-002**
     - 20x20 spatial grid footprint setup
     - Section 3.2, Section 8.1
   * - **FR-003**
     - Sobel elevation derivatives (:math:`\Delta X = 10\text{ m}`)
     - Section 3.3, Section 4.2, Section 6.1
   * - **FR-004**
     - Topographic surface slope angle calculation
     - Section 3.3, Section 4.2, Section 6.2
   * - **FR-005**
     - Topographic surface aspect angle calculation
     - Section 3.3, Section 4.2, Section 6.2
   * - **FR-006**
     - Coordinate vertex grid & Euclidean distance matrix
     - Section 3.4, Section 4.3, Section 6.3
   * - **FR-007**
     - 4-neighbor spatial adjacency matrix construction
     - Section 3.4, Section 4.3, Section 6.3
   * - **FR-008**
     - Node degree vector and topological connectivity audit
     - Section 3.4, Section 6.3, Section 11.3
   * - **FR-009**
     - Graph topology export to ``spatial_graph_mesh.npz``
     - Section 3.5, Section 4.5, Section 10.1
   * - **FR-010**
     - Directed PyTorch ``edge_index`` tensor generation
     - Section 3.6, Section 5.2, Section 11.3
   * - **FR-011**
     - Standardized 4-channel node feature matrix (:math:`X`)
     - Section 3.7, Section 5.2, Section 6.6
   * - **FR-012**
     - Kipf-Welling normalized symmetric Laplacian (:math:`\hat{A}`)
     - Section 3.8, Section 4.4, Section 6.4
   * - **FR-013**
     - 2-layer ``SpatialGCN`` architecture (:math:`4 \to 16 \to 8`)
     - Section 3.9, Section 4.4, Section 6.5
   * - **FR-014**
     - Forward pass evaluation under ``torch.no_grad()``
     - Section 3.10, Section 6.5, Section 11.3
   * - **FR-015**
     - Latent spatial embedding export to ``.pt`` archive
     - Section 3.12, Section 4.5, Section 10.2
   * - **DI-001**
     - Adjacency matrix symmetry and zero diagonal
     - Section 3.4, Section 6.3
   * - **DI-002**
     - Undirected edge count conservation (:math:`|E| = 760`)
     - Section 3.4, Section 11.3
   * - **DI-003**
     - Directed edge index size conservation (:math:`2|E| = 1520`)
     - Section 3.6, Section 11.3
   * - **DI-004**
     - Non-negative slope boundary condition
     - Section 3.3, Section 6.2
   * - **DI-005**
     - Circular aspect azimuth bounds :math:`[0^\circ, 360^\circ)`
     - Section 3.3, Section 6.2
   * - **DI-006**
     - Zero NaN/Inf validation in feature and embedding tensors
     - Section 3.7, Section 3.10, Section 9.2
   * - **DI-007**
     - Unit bounded diagonal on normalized Laplacian
     - Section 3.8, Section 6.4
   * - **IF-001**
     - Telemetry path existence check with warning fallback
     - Section 3.2, Section 7.1, Section 9.1
   * - **IF-002**
     - Destination directory initialization
     - Section 3.5, Section 7.2
   * - **IF-003**
     - Key-value contract for ``spatial_graph_mesh.npz``
     - Section 5.4, Section 10.1
   * - **IF-004**
     - Dictionary serialization contract for ``.pt`` archive
     - Section 5.4, Section 10.2
   * - **UQ-001**
     - Feature scaling epsilon stabilization (:math:`10^{-6}`)
     - Section 3.7, Section 6.6, Section 9.2
   * - **UQ-002**
     - Affine linear layer bias inclusion in GCN
     - Section 3.9, Section 4.4, Section 6.5
   * - **UQ-003**
     - Diagnostic forward pass logging of output extrema
     - Section 3.10, Section 11.3
   * - **NF-001**
     - Deterministic random seed initialization (NumPy 101, Torch 42)
     - Section 3.2, Section 3.6, Section 11.1
   * - **NF-002**
     - Non-interactive top-to-bottom cell execution
     - Section 2.1, Section 12.1
   * - **NF-003**
     - Uniform dark telemetry styling on all generated figures
     - Section 3.1, Section 8.3, Section 10.3
   * - **NF-004**
     - Source code syntax and naming hygiene
     - Section 2.1, Section 8.4
   * - **NF-005**
     - Portability across local server and cloud runtimes
     - Section 7.1, Section 13.2, Section 13.3
