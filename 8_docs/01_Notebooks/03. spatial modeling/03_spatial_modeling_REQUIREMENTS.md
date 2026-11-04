# 🛰️ THE MRIDANSH: SPATIAL REPRESENTATION & GRAPH CONVOLUTIONAL MODELING
## Engineering Requirements, Verification Procedures & Scientific Traceability Specification
### Module ID: `MRIDANSH-MOD-SPATIAL-03` | Notebook: `03-spatial-modeling.ipynb`

---

## 1. System Context & Operational Architecture

Module 03 forms the spatial representation engine of **THE MRIDANSH**. Operating downstream of `02-preprocessing`, it transforms 1D point-aggregate preprocessed telemetry into a 2D topographical catchment mesh ($20 \times 20$ vertices, $200\text{ m} \times 200\text{ m}$ domain at $10\text{ m}$ Ground Sampling Distance), constructs a topological 4-nearest neighbors graph network, derives physical slope/aspect directional vectors, and applies spectral Graph Convolutional Networks (GCN) to produce latent 8-channel spatial embeddings.

```
+----------------------------------------------------------------------------------------------------+
|                                  UPSTREAM PREPROCESSED TELEMETRY                                   |
|  Source: 5_storage/notebook_results/notebook_02_preprocessing/preprocessed_telemetry.csv           |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 1. Topographic Sub-Grid Initialization:                                                            |
|    - 20 x 20 Spatial Grid (N=400 vertices, GSD = 10m)                                              |
|    - DEM elevation field synthesized via Gaussian perturbation (sigma=1.8) around baseline mean    |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 2. Differential Topographic Analysis: Sobel Gradient Filters (Delta X = 10m)                       |
|    - Slope (deg): theta = arctan(sqrt(dz_x^2 + dz_y^2)) in [0, 90]                                  |
|    - Aspect (deg): phi = atan2(-dz_y, dz_x) * 180 / pi (mod 360) in [0, 360)                       |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 3. Topological k-NN Graph Mesh Construction:                                                       |
|    - 4-connected Cartesian grid (Euclidean distance threshold d <= 1.01)                           |
|    - |V| = 400 nodes, |E| = 760 undirected edges (1520 directed edges), mean degree = 3.8          |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 4. Multi-Modal Node Feature Matrix Assembly:                                                       |
|    - X in R^(400 x 4) [DEM, Slope, SAR VV, Optical NDVI]                                           |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 5. Spectral Graph Convolutional Network (GCN):                                                      |
|    - Symmetric Normalized Laplacian: A_hat = D_tilde^(-1/2) * A_tilde * D_tilde^(-1/2)             |
|    - Layer 1: R^4 -> R^16 (LeakyReLU alpha=0.1)                                                    |
|    - Layer 2: R^16 -> R^8 (Linear Embedding)                                                       |
|    - Latent Representation: Z in R^(400 x 8) -> Reshaped to (20, 20, 8) 2D Spatial Tensor          |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 6. Spatial Ablation & Unseen-Area Generalization Testing:                                           |
|    - Full Model vs No-Graph Baseline (A=I) vs No-Terrain Ablation (Dirichlet Roughness Audit)      |
|    - Unseen Rugged Catchment (Mean 45m, slope ~15 deg) out-of-distribution evaluation              |
+----------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+----------------------------------------------------------------------------------------------------+
| 7. Dual Storage Export:                                                                            |
|    - 5_storage/notebook_results/notebook_03_spatial_modeling/spatial_graph_mesh.npz                |
|    - 5_storage/notebook_results/notebook_03_spatial_modeling/spatial_gcn_embeddings.pt             |
|    - Mirrors in data/processed/                                                                    |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Functional Requirements (FR)

### FR-SPATIAL-001: Upstream Telemetry Ingestion
The system **SHALL** locate and ingest `preprocessed_telemetry.csv` from `5_storage/notebook_results/notebook_02_preprocessing/` (fallback to `data/processed/preprocessed_telemetry.csv`).
- Extract calibrated spatial baselines: `baseline_dem_mean`, `baseline_sar_vv_mean`, and `baseline_ndvi_mean`.

### FR-SPATIAL-002: Spatial Sub-Grid Discretization
The system **SHALL** instantiate a $20 \times 20$ planar sub-grid ($N = 400$ nodes) with Ground Sampling Distance $\Delta X = 10.0\text{ m}$:
- The digital elevation field $Z_{\text{DEM}} \in \mathbb{R}^{20 \times 20}$ **SHALL** be generated via Gaussian spatial smoothing ($\sigma = 1.8$) centered around the ingested baseline DEM mean.

### FR-SPATIAL-003: Topographic Gradient Extraction
The system **SHALL** compute spatial partial derivatives of the elevation surface using horizontal and vertical Sobel kernel operators with a spatial denominator of $8 \times \Delta X = 80.0\text{ m}$:
$$\frac{\partial z}{\partial x} = \frac{\operatorname{Sobel}_x(Z_{\text{DEM}})}{8 \cdot \Delta X}, \quad \frac{\partial z}{\partial y} = \frac{\operatorname{Sobel}_y(Z_{\text{DEM}})}{8 \cdot \Delta X}$$
- **Slope Angle Requirement**:
  $$\theta_{\text{slope}} = \arctan\left(\sqrt{\left(\frac{\partial z}{\partial x}\right)^2 + \left(\frac{\partial z}{\partial y}\right)^2}\right) \times \frac{180^\circ}{\pi}, \quad \theta \ge 0^\circ$$
- **Aspect Azimuth Requirement**:
  $$\phi_{\text{aspect}} = \operatorname{atan2}\left(-\frac{\partial z}{\partial y}, \, \frac{\partial z}{\partial x}\right) \times \frac{180^\circ}{\pi} \pmod{360^\circ}, \quad \phi \in [0^\circ, 360^\circ)$$

### FR-SPATIAL-004: $k$-NN Graph Mesh & Adjacency Construction
The system **SHALL** construct a 4-nearest neighbor spatial adjacency matrix $A \in \{0, 1\}^{400 \times 400}$ based on Euclidean vertex coordinates:
$$A_{ij} = \begin{cases} 1 & \text{if } 0 < \|\mathbf{x}_i - \mathbf{x}_j\|_2 \le 1.01 \\ 0 & \text{otherwise} \end{cases}$$
- Graph invariants:
  - Undirected edge count: $\frac{1}{2} \sum_{i,j} A_{ij} = 760$.
  - Self-loop diagonal: $\operatorname{diag}(A) = \mathbf{0}$.
  - Symmetry: $A = A^T$.
  - Mean node degree: $\bar{d} = \frac{2 \times 760}{400} = 3.80$.

### FR-SPATIAL-005: Multi-Modal Feature Tensor Assembly
The system **SHALL** construct node feature tensor $X \in \mathbb{R}^{400 \times 4}$ containing standardized channels:
$$X = \begin{bmatrix} \tilde{\mathbf{z}}_{\text{DEM}} & \tilde{\boldsymbol{\theta}}_{\text{slope}} & \tilde{\boldsymbol{\sigma}}^0_{\text{SAR}} & \tilde{\mathbf{v}}_{\text{NDVI}} \end{bmatrix}$$
where each column is independently standardized to zero mean and unit variance.

### FR-SPATIAL-006: Graph Convolutional Network Architecture
The system **SHALL** compute the Kipf-Welling symmetric normalized Laplacian with self-loops:
$$\tilde{A} = A + I_{400}, \quad \tilde{D}_{ii} = \sum_{j=1}^{400} \tilde{A}_{ij}, \quad \hat{A} = \tilde{D}^{-1/2} \tilde{A} \tilde{D}^{-1/2}$$
The two-layer forward propagation **SHALL** follow:
$$H^{(1)} = \operatorname{LeakyReLU}\left(\hat{A} X W^{(0)} + \mathbf{b}^{(0)}, \, \alpha=0.1\right), \quad W^{(0)} \in \mathbb{R}^{4 \times 16}$$
$$Z = \hat{A} H^{(1)} W^{(1)} + \mathbf{b}^{(1)}, \quad W^{(1)} \in \mathbb{R}^{16 \times 8}$$
- The output embedding $Z \in \mathbb{R}^{400 \times 8}$ **SHALL** be reshaped into a 2D spatial feature cube $(20, 20, 8)$.

### FR-SPATIAL-007: Spatial Ablation & Dirichlet Energy Quantification
The system **SHALL** execute and compare three spatial modeling conditions:
1. Full Spatial GCN ($\hat{A}$, $X$)
2. No-Graph Baseline ($\hat{A} = I_{400}$)
3. No-Terrain Ablation ($X_{[:, :2]} = \mathbf{0}$)
- The system **SHALL** quantify spatial roughness via Dirichlet Energy on the graph Laplacian $L = D - A$:
$$\mathcal{E}_D(H) = \frac{\operatorname{Tr}(H^T L H)}{N \cdot C}$$
- Invariant: Graph convolution must demonstrate reduced Dirichlet roughness compared to unconstrained feature projection.

### FR-SPATIAL-008: Unseen-Area Out-of-Distribution Generalization
The system **SHALL** evaluate the frozen GCN weights on an unseen geographical catchment with steep rugged topography (mean DEM $\sim 45\text{ m}$, range $20-70\text{ m}$, mean slope $\approx 15^\circ$):
- Invariant: Output embeddings for unseen terrain must be 100% finite (zero NaNs, zero Infs).

### FR-SPATIAL-009: Dual-Target Storage Export
The system **SHALL** serialize:
1. `spatial_graph_mesh.npz` (containing `adj_matrix`, `node_coords`, `dem_grid`, `slope_deg`, `aspect_deg`).
2. `spatial_gcn_embeddings.pt` (containing `spatial_embeddings_tensor_2d`, `spatial_embeddings_nodes`, `model_state_dict`, `A_hat`, `ablation_results`, `grid_dim`).
Both files **SHALL** be written to:
- `5_storage/notebook_results/notebook_03_spatial_modeling/`
- `data/processed/`

---

## 3. Data Integrity & Tensor Shape Contracts (DI)

- **DI-SPATIAL-001 (Planar Grid Count)**: Sub-grid node count strictly equals $20 \times 20 = 400$.
- **DI-SPATIAL-002 (Adjacency Matrix Dimensions)**: `adj_matrix.shape == (400, 400)`.
- **DI-SPATIAL-003 (Symmetric Non-Negative Slope)**: $\min(\theta_{\text{slope}}) \ge 0.0^\circ$.
- **DI-SPATIAL-004 (Laplacian Unit Bound)**: Diagonal elements $\hat{A}_{ii} \in (0, 1]$.
- **DI-SPATIAL-005 (Embedding Tensor Shape)**: `spatial_embeddings_tensor_2d.shape == (20, 20, 8)`.
- **DI-SPATIAL-006 (Zero Non-Finite Elements)**: `torch.isnan(Z).sum() == 0` and `torch.isinf(Z).sum() == 0`.

---

## 4. Verification Procedures (VP) & Acceptance Test Suite

The verification suite `tests/test_notebook_03_verification.py` executes 7 strict automated tests:

| Test ID | Procedure Description | Acceptance Criteria | Verified Result |
| :--- | :--- | :--- | :--- |
| **VP-SPATIAL-01** | `test_01_no_python_scripts_in_notebook_dir` | Directory `1_notebooks_sandbox/` contains 0 `.py` scripts | **PASSED** |
| **VP-SPATIAL-02** | `test_02_notebook_cell_structure_and_markdown_rules` | Notebook length $\ge 30$ cells; every code cell preceded by markdown | **PASSED** (34 cells) |
| **VP-SPATIAL-03** | `test_03_all_code_cells_executed_with_zero_errors` | Exactly 15 code cells; all executed; zero error outputs | **PASSED** (15/15 executed) |
| **VP-SPATIAL-04** | `test_04_penultimate_and_ultimate_markdown_cells` | Penultimate contains Executive Summary; Ultimate contains IP notice | **PASSED** |
| **VP-SPATIAL-05** | `test_05_storage_artifacts_and_plots_persisted` | 5 plots (>50KB) and 2 data artifacts exist in dual storage | **PASSED** |
| **VP-SPATIAL-06** | `test_06_graph_and_embedding_tensor_contracts` | Adjacency $(400, 400)$, 2D embedding $(20, 20, 8)$, diagonal positive $\hat{A}$ | **PASSED** |
| **VP-SPATIAL-07** | `test_07_spatial_ablation_and_unseen_generalization_validations` | Ablation JSON exists with Frobenius divergence $>0.5$; unseen embeddings $(20, 20, 8)$ finite | **PASSED** |

---

## 5. Aerospace Artifact Inventory

The following files are permanently stored in `5_storage/notebook_results/notebook_03_spatial_modeling/`:

| Artifact Name | Type | Size | Description |
| :--- | :--- | :--- | :--- |
| `plot_01_topographic_slope_elevation.png` | PNG (300 DPI) | ~196 KB | 2-panel spatial map of synthesized elevation field and Sobel slope magnitude. |
| `plot_02_knn_spatial_graph_adjacency.png` | PNG (300 DPI) | ~77 KB | Sparse binary adjacency heatmap depicting 4-connected band structure ($N=400$). |
| `plot_03_gcn_latent_feature_embeddings.png` | PNG (300 DPI) | ~161 KB | 2-panel spatial projection of learned GCN latent embedding channels 0 and 1. |
| `plot_04_spatial_ablation_analysis.png` | PNG (300 DPI) | ~160 KB | Quantitative bar chart comparing variance and Dirichlet roughness across ablation conditions. |
| `plot_05_unseen_area_generalization.png` | PNG (300 DPI) | ~163 KB | Topography and latent embedding projection on steep out-of-distribution terrain. |
| `spatial_graph_mesh.npz` | NPZ | ~14 KB | Compressed archive storing `adj_matrix`, `node_coords`, `dem_grid`, `slope_deg`, `aspect_deg`. |
| `spatial_gcn_embeddings.pt` | PyTorch | ~670 KB | Serialized dictionary with `spatial_embeddings_tensor_2d` $(20, 20, 8)$, model weights, and $\hat{A}$. |
| `spatial_ablation_results.json` | JSON | 336 Bytes | Metrics summary for full model, no-graph, and no-terrain ablations. |
| `unseen_area_embeddings.pt` | PyTorch | ~15 KB | Latent embeddings evaluated on unseen out-of-distribution terrain. |

---

## 6. Traceability Matrix

| Requirement | Notebook 03 Code Cell | Verification Test | Storage Artifact |
| :--- | :--- | :--- | :--- |
| **FR-SPATIAL-001** | Cell 5 | `test_03_all_code_cells_executed_with_zero_errors` | `preprocessed_telemetry.csv` (input) |
| **FR-SPATIAL-002** | Cell 5 | `test_06_graph_and_embedding_tensor_contracts` | `spatial_graph_mesh.npz` (`dem_grid`) |
| **FR-SPATIAL-003** | Cell 7, 9 | `test_06_graph_and_embedding_tensor_contracts` | `plot_01_topographic_slope_elevation.png` |
| **FR-SPATIAL-004** | Cell 11, 13 | `test_06_graph_and_embedding_tensor_contracts` | `plot_02_knn_spatial_graph_adjacency.png` |
| **FR-SPATIAL-005** | Cell 15 | `test_06_graph_and_embedding_tensor_contracts` | `spatial_gcn_embeddings.pt` |
| **FR-SPATIAL-006** | Cell 17, 19, 21 | `test_06_graph_and_embedding_tensor_contracts` | `plot_03_gcn_latent_feature_embeddings.png` |
| **FR-SPATIAL-007** | Cell 23, 25 | `test_07_spatial_ablation_and_unseen_generalization_validations` | `plot_04_spatial_ablation_analysis.png`, `spatial_ablation_results.json` |
| **FR-SPATIAL-008** | Cell 27, 29 | `test_07_spatial_ablation_and_unseen_generalization_validations` | `plot_05_unseen_area_generalization.png`, `unseen_area_embeddings.pt` |
| **FR-SPATIAL-009** | Cell 31 | `test_05_storage_artifacts_and_plots_persisted` | `spatial_graph_mesh.npz`, `spatial_gcn_embeddings.pt` |

---

## 7. Brutally Unfiltered Defect Log & Engineering Limitations

| Defect ID | Severity | Subsystem | Description & Root Cause | Impact & Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| `D-NB03-001` | **HIGH** | Grid Synthesizer | **Synthetic 2D DEM Sub-Grid Perturbation**: The $20 \times 20$ sub-grid DEM is generated by adding Gaussian noise ($\sigma=1.8$) to the scalar mean elevation from Notebook 02, rather than slicing real 2D Copernicus DEM raster tiles. | The local topographic gradients, while mathematically smooth, are synthetic micro-relief representations rather than true physical contours of the Bhadrak sub-basin. Mitigation: In production, crop and project native Copernicus DEM geotiffs directly to UTM coordinates. |
| `D-NB03-002` | **HIGH** | GCN Encoder | **Untrained Random Projection Baseline**: The 2-layer `SpatialGCN` weights ($W^{(0)}, W^{(1)}$) are randomly initialized via PyTorch defaults and executed without backpropagation against ground-truth soil moisture targets. | The GCN functions strictly as a randomized spectral graph filter and smoothing manifold, rather than a supervised or self-supervised hydrological representation. Mitigation: Pre-train GCN weights using masked spatial reconstruction autoencoders or supervised in-situ stations. |
| `D-NB03-003` | **MEDIUM** | Graph Mesh | **Boundary Node Connectivity Asymmetry**: In the $20 \times 20$ 4-connected grid, interior nodes possess degree 4, boundary nodes degree 3, and four corner nodes degree 2. | Boundary nodes experience reduced message aggregation and smaller self-loop weights in $\hat{A}$, producing edge artifacts in Dirichlet energy calculations. Mitigation: Implement boundary padding or periodic toroidal boundary conditions. |
| `D-NB03-004` | **MEDIUM** | Hydrology | **Isotropic Graph Adjacency vs Directional Gravity**: The adjacency matrix $A$ treats spatial connections as undirected and isotropic ($A_{ij} = A_{ji}$), ignoring gravity and hydraulic head direction. | Overland flow and subsurface runoff are strictly directional (downslope). An undirected graph allows bidirectional diffusion of soil water states contrary to gravity. Mitigation: Weight graph edges directedly using topographic wetness index (TWI) and D8 flow direction algorithms. |

---

## 8. Configuration Control & Environment Lineage

- **Parent Repository**: `THE_MRIDANSH`
- **Execution Python**: Python 3.12.10 (virtual environment `mridansh_env`, PyTorch 2.14.0+cpu, SciPy 1.15.2)
- **Primary Input**: `5_storage/notebook_results/notebook_02_preprocessing/preprocessed_telemetry.csv`
- **Storage Target**: `5_storage/notebook_results/notebook_03_spatial_modeling/`
- **Secondary Target**: `data/processed/`
- **Verification Command**: `pytest tests/test_notebook_03_verification.py -v`
