.. _module_03_spatial_modeling:

========================================================================
🛰️ Module 03: Spatial Representation, Terrain Graph Mesh & GCN Modeling
========================================================================

:Author: JCC Headquarter (RS-SDA Division) / Gourgopal Mohapatra
:Engine: AETHER-MRID1607X
:Module ID: MRIDANSH-MOD-SPATIAL-03
:Notebook Source: ``1_notebooks_sandbox/03-spatial-modeling.ipynb``
:Verification Suite: ``tests/test_notebook_03_verification.py``
:Last Verification: Verified (7/7 Test Cases Passed)

.. contents:: Table of Contents
   :depth: 3
   :local:

Overview & Scientific Purpose
=============================

Module 03 models the 2D spatial domain of the Bhadrak hydrological catchment basin. It reconstructs a :math:`20 \times 20` spatial vertex grid (:math:`N=400` nodes) at :math:`10\text{ m}` Ground Sampling Distance (:math:`200\text{ m} \times 200\text{ m}` localized catchment), derives first-order topographic gradients (slope and aspect), constructs a planar 4-nearest neighbor graph topology, and implements a spectral Graph Convolutional Network (GCN) that computes latent spatial representations :math:`Z \in \mathbb{R}^{20 \times 20 \times 8}`.

Key scientific capabilities:
1. **Topographic Gradient Extraction**: Sobel spatial operator filtering on digital elevation matrices to quantify gravitational drainage inclination and solar aspect angles.
2. **Topological Graph Mesh**: Planar :math:`k`-NN undirected graph network with 4-connectivity (:math:`|V|=400`, :math:`|E|=760`, mean degree :math:`\bar{d}=3.8`).
3. **Spectral Graph Convolution**: Kipf-Welling symmetric normalized Laplacian smoothing (:math:`\hat{A} = \tilde{D}^{-1/2} \tilde{A} \tilde{D}^{-1/2}`) applied across 4 standardized channels (Elevation, Slope, SAR Backscatter, and NDVI).
4. **Dirichlet Energy Ablation**: Quantitative analysis of graph message-passing efficacy against an unconstrained identity baseline (:math:`A = I_N`) and terrain ablation.
5. **Inductive Out-of-Distribution Generalization**: Testing frozen GCN spatial encodings against rugged unseen terrain (mean elevation :math:`45\text{ m}`, mean slope :math:`\approx 15^\circ`).

Spatial Domain & Topographic Formulations
=========================================

Topographic Grid Discretization
-------------------------------

The spatial mesh comprises :math:`N = 400` nodes arranged on a uniform :math:`20 \times 20` grid with spatial resolution :math:`\Delta X = 10.0\text{ m}`. The elevation surface :math:`Z_{\text{DEM}}` is initialized using baseline elevation telemetry from Module 02 combined with Gaussian spatial smoothing (:math:`\sigma=1.8`):

.. math::

   Z_{\text{DEM}} = \mathcal{G}_{\sigma=1.8}\left(\mu_{\text{DEM}} + \epsilon_{\text{noise}}\right), \quad \epsilon_{\text{noise}} \sim \mathcal{U}(-4.5, +5.5)

Slope & Aspect Calculations
---------------------------

Spatial elevation gradients are derived via horizontal and vertical Sobel kernel operators:

.. math::

   \frac{\partial z}{\partial x} = \frac{\operatorname{Sobel}_x(Z_{\text{DEM}})}{8 \cdot \Delta X}, \quad \frac{\partial z}{\partial y} = \frac{\operatorname{Sobel}_y(Z_{\text{DEM}})}{8 \cdot \Delta X}

Gravitational slope angle :math:`\theta_{\text{slope}}` in degrees:

.. math::

   \theta_{\text{slope}} = \arctan\left(\sqrt{\left(\frac{\partial z}{\partial x}\right)^2 + \left(\frac{\partial z}{\partial y}\right)^2}\right) \times \frac{180^\circ}{\pi}

Directional aspect azimuth :math:`\phi_{\text{aspect}}` in degrees :math:`[0^\circ, 360^\circ)`:

.. math::

   \phi_{\text{aspect}} = \operatorname{atan2}\left(-\frac{\partial z}{\partial y}, \, \frac{\partial z}{\partial x}\right) \times \frac{180^\circ}{\pi} \pmod{360^\circ}

Graph Topology & Graph Convolutional Networks
=============================================

Planar 4-NN Adjacency Matrix
----------------------------

For vertex coordinates :math:`\mathbf{x}_i, \mathbf{x}_j \in \mathbb{R}^2`, the undirected adjacency matrix :math:`A \in \{0, 1\}^{400 \times 400}` is constructed via distance thresholding:

.. math::

   A_{ij} = \begin{cases} 1 & \text{if } 0 < \|\mathbf{x}_i - \mathbf{x}_j\|_2 \le 1.01 \\ 0 & \text{otherwise} \end{cases}

Structural graph metrics:
- Vertices :math:`|V| = 400`
- Undirected edges :math:`|E| = \frac{1}{2} \sum_{i,j} A_{ij} = 760`
- Directed edge index length: :math:`2|E| = 1520`
- Degree distribution: 4 (interior nodes), 3 (boundary nodes), 2 (corner nodes)
- Mean node degree: :math:`\bar{d} = 3.80`

Symmetric Normalized Laplacian
------------------------------

To enable spectral graph convolution with numerical stability, self-loops are added and the Kipf-Welling renormalization trick is applied:

.. math::

   \tilde{A} = A + I_N, \quad \tilde{D}_{ii} = \sum_{j=1}^N \tilde{A}_{ij}

.. math::

   \hat{A} = \tilde{D}^{-1/2} \tilde{A} \tilde{D}^{-1/2}

Properties:
- :math:`\hat{A}_{ii} \in (0, 1]` for all :math:`i`
- :math:`\hat{A} = \hat{A}^T` (symmetric)

GCN Architecture
----------------

The two-layer graph neural network maps 4 input node features to an 8-channel latent spatial representation:

.. math::

   H^{(1)} = \operatorname{LeakyReLU}\left(\hat{A} X W^{(0)} + \mathbf{b}^{(0)}, \, \alpha=0.1\right), \quad W^{(0)} \in \mathbb{R}^{4 \times 16}

.. math::

   Z = \hat{A} H^{(1)} W^{(1)} + \mathbf{b}^{(1)}, \quad W^{(1)} \in \mathbb{R}^{16 \times 8}

The node embedding matrix :math:`Z \in \mathbb{R}^{400 \times 8}` is reshaped into a continuous 3D spatial tensor of dimensions :math:`(20, 20, 8)` to serve as spatial conditioning for downstream ConvLSTM modeling.

Spatial Ablation & Dirichlet Energy
===================================

The effectiveness of graph message-passing is audited using Dirichlet Energy (spatial roughness) on the combinatorial graph Laplacian :math:`L = D - A`:

.. math::

   \mathcal{E}_D(H) = \frac{\operatorname{Tr}\left(H^T L H\right)}{N \cdot C}

Ablation benchmark results:
- **Full Spatial GCN**: Latent Variance = :math:`0.2841`, Spatial Roughness = :math:`0.1412`
- **No-Graph Baseline (:math:`A = I_N`)**: Latent Variance = :math:`0.3920`, Spatial Roughness = :math:`0.4891`
- **No-Terrain Ablation (DEM, Slope zeroed)**: Latent Variance = :math:`0.1624`, Spatial Roughness = :math:`0.2105`

Scientific finding: Spatial graph message-passing dampens high-frequency numerical roughness by :math:`71.13\%` compared to independent node projections, while preserving macro-scale hydrological elevation gradients.

Generated Artifacts & Visualizations
====================================

The module produces 5 high-resolution (300 DPI) plots and 4 data files in ``5_storage/notebook_results/notebook_03_spatial_modeling/``:

1. **Topographic Slope & Elevation (plot_01_topographic_slope_elevation.png)**: Dual-panel map of digital elevation and derived Sobel slope gradients.
2. **$k$-NN Adjacency Heatmap (plot_02_knn_spatial_graph_adjacency.png)**: Heatmap displaying the tri-diagonal band structure of the 400-node graph.
3. **GCN Feature Embeddings (plot_03_gcn_latent_feature_embeddings.png)**: 2D spatial contour plots of latent channels 0 and 1.
4. **Spatial Ablation Comparative Analytics (plot_04_spatial_ablation_analysis.png)**: Quantitative bar charts of representation variance and Dirichlet roughness.
5. **Unseen-Area Generalization (plot_05_unseen_area_generalization.png)**: Generalization test of frozen GCN on rugged out-of-distribution terrain.

Data Archives:
- ``spatial_graph_mesh.npz``: Graph topology, adjacency matrix, and topographic grids.
- ``spatial_gcn_embeddings.pt``: Serialized PyTorch dictionary containing the :math:`(20, 20, 8)` spatial tensor, model parameters, and :math:`\hat{A}`.
- ``spatial_ablation_results.json``: Quantitative metrics across ablation conditions.
- ``unseen_area_embeddings.pt``: Out-of-distribution evaluation embeddings.

Verification & Test Coverage
============================

The verification suite ``tests/test_notebook_03_verification.py`` enforces 7 automated tests:

* ``test_01_no_python_scripts_in_notebook_dir``: Confirms zero Python scripts in sandbox directory.
* ``test_02_notebook_cell_structure_and_markdown_rules``: Validates alternating markdown/code structure (:math:`\ge 30` cells).
* ``test_03_all_code_cells_executed_with_zero_errors``: Verifies all 15 code cells executed with 0 runtime errors.
* ``test_04_penultimate_and_ultimate_markdown_cells``: Audits presence of Executive Summary and Intellectual Property notices.
* ``test_05_storage_artifacts_and_plots_persisted``: Validates file existence and size thresholds (>50KB) for all 5 plots and data files.
* ``test_06_graph_and_embedding_tensor_contracts``: Audits shape contracts of :math:`A` (:math:`400 \times 400`), :math:`Z` (:math:`20 \times 20 \times 8`), and Laplacian :math:`\hat{A}`.
* ``test_07_spatial_ablation_and_unseen_generalization_validations``: Audits ablation divergence (>0.5) and ensures unseen-area embeddings are 100% finite.

Known Defects & Engineering Limitations
========================================

* **D-NB03-001 (Synthetic 2D DEM Sub-Grid Perturbation)**: The :math:`20 \times 20` elevation grid is synthesized via Gaussian perturbation around the mean telemetry elevation rather than sliced directly from native high-resolution Copernicus DEM raster tiles.
* **D-NB03-002 (Untrained Random Projection GCN)**: The 2-layer `SpatialGCN` operates as a fixed random spectral filter without backpropagation against ground-truth soil moisture measurements.
* **D-NB03-003 (Boundary Node Connectivity Asymmetry)**: Edge nodes (degree 3) and corner nodes (degree 2) receive fewer messages than interior nodes (degree 4), creating minor edge damping in Dirichlet energy.
* **D-NB03-004 (Isotropic Graph Adjacency)**: Graph edges are undirected and isotropic (:math:`A_{ij} = A_{ji}`), which does not account for gravitational slope direction or hydrologic flow paths.
