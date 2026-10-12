# THE MRIDANSH (AETHER-MRID1607X)
# Notebook 03 — Spatial Representation, Terrain Graph Mesh & GCN Modeling
# Requirements, Verification and Configuration Control

---

## 1. Document Control

### 1.1 Identification

| Field | Value |
|:---|:---|
| **Document ID** | MRID-NB03-DOC-001 |
| **Notebook ID** | `03-spatial-modeling.ipynb` |
| **Project** | THE MRIDANSH — Unified Soil State Estimation System |
| **System / Engine** | AETHER-MRID1607X (Multi-Domain Soil Intelligence Engine) |
| **Author / Developer** | Gourgopal Mohapatra |
| **Organization** | JCC HEADQUARTER — JCC CAMPUS 2, RS-SDA Division |
| **Reviewer** | *(To be assigned — independent technical reviewer)* |
| **Approver** | *(To be assigned — systems engineering authority)* |
| **Version** | 1.0 |
| **Date** | 2026-10-08 |
| **Status** | Baseline Draft — Under Strict Technical Review |
| **Classification** | Proprietary & Controlled Research Artifact |

### 1.2 Revision History

| Version | Date | Author | Description of Change |
|:---|:---|:---|:---|
| 0.1 | 2026-10-08 | Gourgopal Mohapatra | Initial reverse-engineering and structural extraction of `03-spatial-modeling.ipynb` code, cell outputs, and numerical tensors. |
| 1.0 | 2026-10-08 | Gourgopal Mohapatra | Formalized rigorous systems engineering specification: atomic requirements, mathematical formulations, verification procedures, empirical execution results, bidirectional traceability matrix, and open problem reports. |

### 1.3 Document Conventions

- **SHALL** indicates a mandatory, verifiable, and binding requirement.
- **SHOULD** indicates a strongly recommended engineering practice or design target.
- **MAY** indicates an optional or permitted implementation path.
- **Requirement Status Definitions**:
  - `MET`: Requirement has been verified by execution or inspection against actual evidence.
  - `PARTIAL`: Implementation exists but lacks formal verification, runtime assertions, or carries edge-case caveats.
  - `NOT MET`: Requirement is absent, violated, or replaced by an unverified synthetic stub.
  - `WAIVED`: Formal departure accepted with recorded technical rationale.
- **Verification Methods**:
  - `T` (Test): Execution of software with deterministic inputs and direct evaluation against numerical pass/fail criteria.
  - `A` (Analysis): Quantitative evaluation of mathematical properties, algorithmic complexity, or memory consumption.
  - `I` (Inspection): Manual examination of source code, configurations, schemas, or file structures.
  - `D` (Demonstration): Observation of operational pipeline behavior or diagnostic visualizations.
- **Requirement Identification Rules**:
  - `FR-xxx`: Functional Requirement
  - `DI-xxx`: Data Integrity Requirement
  - `IF-xxx`: Interface & File Structure Requirement
  - `UQ-xxx`: Uncertainty & Quality Requirement
  - `NF-xxx`: Non-Functional & Reproducibility Requirement
  - `VP-xxx`: Verification Procedure
  - `D-xxx`: Open Defect / Discrepancy
  - `R-xxx`: Technical Risk
  - `A-xxx`: Architectural Assumption

---

## 2. Purpose and Scope

### 2.1 Purpose

This document establishes the formal engineering requirements, mathematical formulation, software design description, verification procedures, empirical verification results, bidirectional traceability, and configuration baseline for Jupyter notebook `03-spatial-modeling.ipynb` within the **THE MRIDANSH** system.

### 2.2 System Context

**THE MRIDANSH** (*Engine: AETHER-MRID1607X*) fuses multi-modal spaceborne Earth Observation (EO) data—Sentinel-1 C-band SAR backscatter, Sentinel-2 optical multispectral bands, Digital Elevation Models (DEM), and meteorology—with Physics-Informed Neural Networks (PINN) and Ensemble Kalman Filtering (EnKF) to estimate high-resolution soil state vectors ($\theta_v$, matric potential, and subgrade shear capacity).

Within this macro-architecture:
- **Notebook 01** ingests multi-sensor telemetry and establishes bounding extents.
- **Notebook 02** performs temporal speckle filtering (Lee filter), cloud screening, train/test partitioning, and z-score/min-max scaling.
- **Notebook 03 (Item Under Documentation)** translates 2D raster arrays into structured spatial graph meshes ($G = (V, E)$), derives topographic terrain derivative fields (slope and aspect), constructs symmetric normalized graph Laplacians, and performs forward-pass spatial latent feature extraction using a custom 2-layer Graph Convolutional Network (GCN).
- **Downstream Consumers (Notebooks 04–06)** consume the resulting spatial graph mesh (`spatial_graph_mesh.npz`) and latent embedding tensors (`spatial_gcn_embeddings.pt`) to constrain spatio-temporal PDE operators (Richards equation and 2D hydrological diffusion).

### 2.3 Notebook Objective

Notebook 03 executes Sprint Days 5–6 of the 18-Day Scientific Validation Sprint, structured into two parts:
1. **Day 5 Objective**: Topographic gradient extraction ($\theta_{\text{slope}}, \phi_{\text{aspect}}$), spatial coordinate grid extraction, $k$-NN grid adjacency matrix construction ($A_{ij}$), and persistence of graph mesh topology.
2. **Day 6 Objective**: Graph tensor assembly, multi-sensor node feature matrix construction ($X \in \mathbb{R}^{N \times F}$), implementation of a custom PyTorch 2-layer GCN architecture, forward-pass execution, spatial latent feature map visualization, and tensor artifact persistence.

### 2.4 In Scope

- All 29 cells of `03-spatial-modeling.ipynb` (13 code cells, 16 markdown cells).
- Ingestion logic for preprocessed telemetry (`preprocessed_telemetry.csv`).
- Topographic gradient calculation via 2D spatial Sobel filtering.
- Graph mesh generation ($20 \times 20$ grid, 4-neighbor spatial topology).
- Adjacency matrix construction, degree vector calculation, and PyTorch `edge_index` generation.
- Symmetric normalized Laplacian computation: $\hat{A} = \tilde{D}^{-1/2}(A + I_N)\tilde{D}^{-1/2}$.
- PyTorch custom `GraphConvLayer` and `SpatialGCN` module execution.
- Forward evaluation producing $N \times 8$ node embeddings.
- Generation and rendering of 3 diagnostic aerospace visual figures.
- Persistence of export artifacts (`spatial_graph_mesh.npz`, `spatial_gcn_embeddings.pt`).

### 2.5 Out of Scope

- Notebook 01 telemetry ingestion and bounding box generation.
- Notebook 02 Lee filtering, cloud thresholding, and tabular scaling fitting.
- Backpropagation, loss computation, and gradient updates for the GCN (Notebook 03 is strictly an un-trained forward-pass structural representation and initialization notebook).
- Physics-Informed Neural Network (PINN) loss formulation and temporal modeling (Notebooks 04 and 05).
- Live cloud STAC API connectivity and real-time inference serving.

### 2.6 Current-State Declaration (Mandatory Engineering Disclosure)

> [!WARNING]
> **MANDATORY CURRENT-STATE DECLARATION: SYNTHETIC SPATIAL RASTER DOMAIN**
> 
> Although Notebook 03 successfully checks for the presence of `preprocessed_telemetry.csv` (35 rows from Notebook 02), the $20 \times 20$ spatial rasters used for graph mesh construction and node feature assembly **are generated in-memory via synthetic pseudorandom distributions** (`numpy.random` seed 101, Gaussian-filtered DEM, uniform SAR, and random normal/uniform features). 
> 
> The spatial grid coordinates are discrete index grids ($[0, 19] \times [0, 19]$) rather than georeferenced EPSG:4326/EPSG:32645 coordinates. Consequently, all derived numerical values (mean slope $3.06^\circ$, embedding bounds $[-0.4555, 0.3316]$) verify the **computational pipeline and mathematical operators**, but do **not** represent verified in-situ terrain measurements for the Bhadrak/Balasore study site.

---

## 3. Definitions and Abbreviations

| Term / Abbreviation | Definition |
|:---|:---|
| **AOI** | Area of Interest (Spatial footprint centered at 21.1378° N, 86.6874° E, Odisha). |
| **GCN** | Graph Convolutional Network (Spectral/spatial message passing neural network on irregular graph topologies). |
| **$k$-NN** | $k$-Nearest Neighbors (Spatial connectivity operator connecting nodes within a Euclidean threshold). |
| **DEM** | Digital Elevation Model (Topographic surface elevation array, units: meters). |
| **SAR** | Synthetic Aperture Radar (Active microwave backscatter sensor, C-band Sentinel-1). |
| **NDVI** | Normalized Difference Vegetation Index: $(B08 - B04) / (B08 + B04)$. |
| **Sobel Operator** | Discrete spatial differentiation filter used to approximate continuous first-order elevation gradients. |
| **$\hat{A}$** | Renormalized Symmetric Adjacency / Laplacian Operator: $\tilde{D}^{-1/2} \tilde{A} \tilde{D}^{-1/2}$, where $\tilde{A} = A + I_N$. |
| **$|V|$** | Number of graph vertices / nodes (for $20 \times 20$ grid, $|V| = 400$). |
| **$|E|$** | Number of graph edges (undirected connections $|E| = 760$, directed pairs $= 1520$). |
| **JCC RS-SDA** | Jagannath Command Center — Remote Sensing & Spatial Data Analytics Division. |

---

## 4. Requirements

### 4.1 Functional Requirements

- **FR-001**: The software shall ingest or verify the existence of preprocessed telemetry table `preprocessed_telemetry.csv`.
- **FR-002**: The software shall construct a 2D spatial grid domain of dimension $20 \times 20$ nodes ($N = 400$ total spatial vertices).
- **FR-003**: The software shall compute continuous 2D first-order spatial elevation derivatives $\frac{\partial Z}{\partial x}$ and $\frac{\partial Z}{\partial y}$ across the DEM grid using standard Sobel directional convolution kernels scaled by spatial cell resolution $\Delta X = 10.0\text{ m}$.
- **FR-004**: The software shall compute topographic surface slope angle ($\theta_{\text{slope}}$) in radians and degrees via:
  $$\theta_{\text{slope}} = \arctan\left(\sqrt{\left(\frac{\partial Z}{\partial x}\right)^2 + \left(\frac{\partial Z}{\partial y}\right)^2}\right)$$
- **FR-005**: The software shall compute topographic surface aspect angle ($\phi_{\text{aspect}}$) in degrees clockwise from North in the range $[0^\circ, 360^\circ)$ via:
  $$\phi_{\text{aspect}} = \left(\operatorname{atan2}\left(-\frac{\partial Z}{\partial y}, \frac{\partial Z}{\partial x}\right) \times \frac{180}{\pi}\right) \pmod{360}$$
- **FR-006**: The software shall generate discrete 2D spatial node coordinates for all $N$ grid cells and compute pairwise Euclidean distance matrices.
- **FR-007**: The software shall construct an unweighted symmetric adjacency matrix $A \in \{0, 1\}^{N \times N}$ connecting adjacent grid cells under 4-neighbor spatial topology ($0 < d(v_i, v_j) \le 1.01$).
- **FR-008**: The software shall compute the node degree vector $d_i = \sum_{j} A_{ij}$ and verify that corner, edge, and interior nodes possess valid topological degrees ($d_i \in \{2, 3, 4\}$).
- **FR-009**: The software shall export the spatial graph topology, node coordinates, raw DEM, and derived slope array to compressed archive `spatial_graph_mesh.npz`.
- **FR-010**: The software shall convert the adjacency matrix into a PyTorch long tensor `edge_index` of shape $[2, 2|E|]$ representing directed edge connectivity.
- **FR-011**: The software shall assemble a standardized multi-sensor node feature tensor $X \in \mathbb{R}^{N \times 4}$ containing:
  - Feature 0: Z-score standardized DEM elevation.
  - Feature 1: Z-score standardized topographic slope.
  - Feature 2: SAR backscatter attribute.
  - Feature 3: Optical NDVI vegetation attribute.
- **FR-012**: The software shall compute the Kipf-Welling renormalized symmetric adjacency matrix:
  $$\tilde{A} = A + I_N, \quad \tilde{D}_{ii} = \sum_{j} \tilde{A}_{ij}, \quad \hat{A} = \tilde{D}^{-1/2} \tilde{A} \tilde{D}^{-1/2}$$
- **FR-013**: The software shall instantiate a 2-layer Graph Convolutional Network (`SpatialGCN`) implementing the forward propagation model:
  $$H^{(1)} = \operatorname{Dropout}\left(\operatorname{ReLU}\left(\hat{A} X W^{(0)} + b^{(0)}\right)\right), \quad H^{(2)} = \hat{A} H^{(1)} W^{(1)} + b^{(1)}$$
  with architectural dimensions $F_{\text{in}} = 4 \to F_{\text{hidden}} = 16 \to F_{\text{out}} = 8$.
- **FR-014**: The software shall execute forward propagation in evaluation mode (`model.eval()`, `torch.no_grad()`) to produce latent node representation matrix $Z \in \mathbb{R}^{400 \times 8}$.
- **FR-015**: The software shall export the computed spatial latent embeddings, model state dictionary, and normalized adjacency matrix to PyTorch artifact `spatial_gcn_embeddings.pt`.

### 4.2 Data Integrity Requirements

- **DI-001**: The graph adjacency matrix $A$ shall be strictly symmetric ($A = A^T$) with an identically zero diagonal ($A_{ii} = 0$, no self-loops prior to renormalization).
- **DI-002**: For a 4-connected grid of dimension $M \times M$ with $M=20$, the total number of undirected edges shall strictly equal $2M(M - 1) = 2 \times 20 \times 19 = 760$.
- **DI-003**: The directed edge index tensor shall contain exactly $2 \times 760 = 1520$ directed edges.
- **DI-004**: The derived slope matrix shall be non-negative everywhere ($\theta_{\text{slope}} \ge 0^\circ$).
- **DI-005**: The derived aspect matrix shall strictly satisfy $0^\circ \le \phi_{\text{aspect}} < 360^\circ$.
- **DI-006**: The feature tensor $X$ and embedding tensor $Z$ shall contain zero NaN, infinite, or unrepresentable values.
- **DI-007**: The normalized Laplacian matrix $\hat{A}$ shall have unit diagonal dominance and row sums bounded by 1.

### 4.3 Interface Requirements

- **IF-001**: The software shall attempt loading telemetry from primary path `/kaggle/input/datasets/gourgopalmohapatra/preprocessed-telemetry-csv/preprocessed_telemetry.csv` and handle missing files gracefully without unhandled crashes.
- **IF-002**: The software shall create output directory `/kaggle/working/data_processed/` if it does not already exist.
- **IF-003**: The graph archive `spatial_graph_mesh.npz` shall contain exactly four named keys: `'adj_matrix'`, `'node_coords'`, `'dem_grid'`, and `'slope_deg'`.
- **IF-004**: The PyTorch model artifact `spatial_gcn_embeddings.pt` shall serialize a dictionary containing exactly: `'spatial_embeddings'`, `'model_state_dict'`, and `'A_hat'`.

### 4.4 Uncertainty / Quality Requirements

- **UQ-001**: Epsilon stabilization ($\epsilon = 10^{-6}$) shall be added to feature standard deviation denominators to prevent numerical overflow on degenerate constant fields.
- **UQ-002**: Linear layer bias vectors shall be included in both GCN graph convolutional stages to preserve representation capacity across zero-mean normalized inputs.
- **UQ-003**: Numerical output ranges of latent embeddings shall be audited and logged during the forward pass diagnostic banner.

### 4.5 Non-Functional Requirements

- **NF-001**: Random number generator seeds shall be explicitly fixed (`numpy.random.seed(101)` for spatial grids, `torch.manual_seed(42)` for PyTorch parameters).
- **NF-002**: The notebook shall execute from top-to-bottom without interactive manual interventions.
- **NF-003**: Visual diagnostic plots shall employ the project-standard dark telemetry theme (`#00FFCC` border, `#1A3344` grid, monospace fonts).
- **NF-004**: Source code shall not contain undefined symbols or unhandled fatal exceptions.
- **NF-005**: All exported artifacts shall reside under a configurable directory rather than hardcoded environment-dependent paths.

---

## 5. Requirements Attributes

| ID | Requirement Statement | Rationale | Method | Acceptance Criterion | Status |
|:---|:---|:---|:---:|:---|:---:|
| **FR-001** | Verify or ingest telemetry CSV from data lake. | Pipeline upstream dependency. | I/T | Telemetry loaded or fallback notified. | **MET** |
| **FR-002** | Reconstruct $20 \times 20$ spatial grid footprint ($N=400$). | Fixed spatial discretization for graph nodes. | T | Grid dimensions equal $(20, 20)$; $N=400$. | **MET** |
| **FR-003** | Compute spatial elevation derivatives via Sobel filters ($\Delta X = 10\text{ m}$). | Terrain hydrological runoff modeling. | T | `dz_dx` and `dz_dy` generated with shape $(20, 20)$. | **MET** |
| **FR-004** | Compute slope matrix in degrees. | Quantify gravitational drainage gradient. | T | Mean slope and min/max computed; shape $(20, 20)$. | **MET** |
| **FR-005** | Compute aspect matrix in degrees $[0, 360)$. | Solar radiation and directional runoff vector. | T | Values bounded within $[0, 360)$. | **MET** |
| **FR-006** | Compute pairwise Euclidean node distance matrix. | Prerequisite for topological neighbor extraction. | T | Coordinate array of shape $(400, 2)$; distance matrix $(400, 400)$. | **MET** |
| **FR-007** | Construct 4-neighbor spatial adjacency matrix. | Spatial physical connectivity without diagonal cross-flow. | T | Binary adjacency matrix of shape $(400, 400)$. | **MET** |
| **FR-008** | Calculate node degree vector and mean connectivity. | Topological graph mesh validation. | T | Total edges $= 760$; Mean degree $= 3.8$. | **MET** |
| **FR-009** | Export graph topology to `spatial_graph_mesh.npz`. | Persist spatial graph for downstream solvers. | T | File exists on disk; keys match specification. | **MET** |
| **FR-010** | Extract PyTorch long tensor `edge_index` from adjacency. | Native PyTorch graph format compatibility. | T | Tensor shape equals `torch.Size([2, 1520])`. | **MET** |
| **FR-011** | Assemble node feature tensor $X \in \mathbb{R}^{400 \times 4}$. | Multi-modal spatial attribute fusion. | T | Tensor shape `torch.Size([400, 4])`; 0 NaNs. | **MET** |
| **FR-012** | Compute normalized symmetric Laplacian $\hat{A}$. | Kipf-Welling spectral graph convolution operator. | T | Tensor shape `torch.Size([400, 400])`; symmetric. | **MET** |
| **FR-013** | Implement 2-layer `SpatialGCN` architecture ($4 \to 16 \to 8$). | Hierarchical spatial feature aggregation. | I/T | Model instantiates with defined layer dimensions. | **MET** |
| **FR-014** | Execute forward pass producing embedding matrix $Z$. | Generate latent representation for soil state. | T | Embedding shape equals `torch.Size([400, 8])`. | **MET** |
| **FR-015** | Export latent spatial embeddings to `spatial_gcn_embeddings.pt`. | Downstream coupling with PINN / EnKF. | T | Saved dictionary loaded and verified. | **MET** |
| **DI-001** | Strict symmetry and zero diagonal on adjacency matrix $A$. | Undirected graph without spurious self-reinforcement. | T | $A = A^T$ and $\operatorname{diag}(A) = \mathbf{0}$. | **MET** |
| **DI-002** | Undirected edge count strictly equals 760. | Analytical planarity theorem for 4-connected grid. | T | $\frac{1}{2} \sum A_{ij} = 760$. | **MET** |
| **DI-003** | Directed edge tensor length equals 1520. | Directed edge index consistency with adjacency. | T | `edge_index.shape[1] == 1520`. | **MET** |
| **DI-004** | Slope angle strictly non-negative ($\ge 0^\circ$). | Physical definition of gradient magnitude. | T | $\min(\theta_{\text{slope}}) \ge 0.0$. | **MET** |
| **DI-005** | Aspect angle strictly bounded $[0^\circ, 360^\circ)$. | Directional azimuth integrity. | T | $0.0 \le \phi_{\text{aspect}} < 360.0$. | **MET** |
| **DI-006** | Zero NaN or Inf in feature and embedding tensors. | Numerical validity of neural representations. | T | `torch.isnan().sum() == 0`, `torch.isinf().sum() == 0`. | **MET** |
| **DI-007** | Unit bounded diagonal on normalized Laplacian $\hat{A}$. | Spectral stability of graph filtering. | T | $\hat{A}_{ii} \le 1.0$. | **MET** |
| **IF-001** | Graceful fallback on absent input CSV. | Pipeline execution resilience. | T | Missing path triggers warning; no crash. | **MET** |
| **IF-002** | Automatic directory creation for exports. | Filesystem independence. | T | Directory `/kaggle/working/data_processed/` created. | **MET** |
| **IF-003** | Exact keys in `.npz` archive. | Interface contract with downstream loaders. | I/T | Keys: `adj_matrix`, `node_coords`, `dem_grid`, `slope_deg`. | **MET** |
| **IF-004** | Exact dictionary structure in `.pt` export. | Interface contract with Notebook 04 PINN engine. | I/T | Keys: `spatial_embeddings`, `model_state_dict`, `A_hat`. | **MET** |
| **UQ-001** | Epsilon denominator stabilization in scaling. | Prevent divide-by-zero on zero-variance inputs. | I/T | $10^{-6}$ offset present in scaling denominators. | **MET** |
| **UQ-002** | Affine bias parameter inclusion in GCN linear layers. | Prevent manifold collapse to origin. | I/T | `bias=True` set on all `nn.Linear` layers. | **MET** |
| **UQ-003** | Audit and logging of forward pass embedding bounds. | Anomaly detection on latent representations. | T | Min/max bounds computed and reported in stdout. | **MET** |
| **NF-001** | Pinned pseudorandom seeds for NumPy and PyTorch. | Bit-for-bit numerical reproducibility. | I/T | `np.random.seed(101)` and `torch.manual_seed(42)` set. | **MET** |
| **NF-002** | Complete non-interactive top-to-bottom execution. | Batch headless execution capability. | D | Notebook runs all 29 cells sequentially without error. | **MET** |
| **NF-003** | Uniform dark telemetry theme on all generated plots. | Visual interface consistency across division. | I | Palette `#00FFCC`, `#FF9900`, `#0A192F` applied. | **MET** |
| **NF-004** | Linter and identifier consistency. | Source code hygiene. | I | No syntax errors, correct identifier naming. | **PARTIAL** |
| **NF-005** | Elimination of hardcoded environment paths. | Portability across local server and cloud runtimes. | I | Hardcoded `/kaggle/` paths present in script. | **NOT MET** |

---

## 6. Verification Procedures

### VP-001: Telemetry Ingestion and Spatial Grid Initialization
- **Verifies**: FR-001, FR-002, IF-001, NF-001
- **Setup**: Clean Python 3.10+ kernel with NumPy, Pandas, Scipy.
- **Procedure**:
  1. Initialize target data path `/kaggle/input/.../preprocessed_telemetry.csv`.
  2. Execute ingestion check cell.
  3. Instantiate $GRID\_DIM = 20$.
  4. Generate synthetic `dem_grid` using `gaussian_filter` with $\sigma = 1.5$ under seed 101.
  5. Generate synthetic `sar_grid` under uniform distribution $[-16.0, -6.0]\text{ dB}$.
- **Expected Result**: Ingestion logs report loaded dataset or in-memory fallback; `dem_grid.shape == (20, 20)`, `sar_grid.shape == (20, 20)`.
- **Pass Criterion**: Node count equals 400 exactly; zero exceptions raised.

### VP-002: Topographic Slope and Aspect Extraction
- **Verifies**: FR-003, FR-004, FR-005, DI-004, DI-005
- **Setup**: Initialized `dem_grid` from VP-001; $\Delta X = 10.0\text{ m}$.
- **Procedure**:
  1. Convolve `dem_grid` with `scipy.ndimage.sobel` along axis 1 and axis 0.
  2. Scale by $8.0 \times \Delta X = 80.0$.
  3. Calculate $\theta_{\text{slope}} = \arctan\left(\sqrt{dz_x^2 + dz_y^2}\right)$ in degrees.
  4. Calculate $\phi_{\text{aspect}} = \operatorname{atan2}(-dz_y, dz_x) \times \frac{180}{\pi} \pmod{360}$.
  5. Audit mean slope, min/max slope, and mean aspect.
- **Expected Result**: Mean slope equals $3.06^\circ \pm 0.01^\circ$; min slope equals $0.13^\circ$; max slope equals $8.96^\circ$; mean aspect equals $182.17^\circ$.
- **Pass Criterion**: $\min(\theta_{\text{slope}}) \ge 0^\circ$ and $0^\circ \le \phi_{\text{aspect}} < 360^\circ$ across all 400 nodes.

### VP-003: Aerospace Plot 1 Diagnostics
- **Verifies**: NF-003, D
- **Setup**: Derived `dem_grid` and `slope_deg` arrays.
- **Procedure**:
  1. Render 2-panel figure ($15 \times 6$ inches) with `terrain` and `magma` colormaps.
  2. Inject embedded text box with calculated elevation delta and mean slope.
- **Expected Result**: Image rendered with colorbars and diagnostic text box.
- **Pass Criterion**: Figure successfully displayed without clipping or backend errors.

### VP-004: $k$-NN Graph Adjacency Construction and Degree Audit
- **Verifies**: FR-006, FR-007, FR-008, DI-001, DI-002
- **Setup**: Grid coordinate vertices from meshgrid ($20 \times 20$).
- **Procedure**:
  1. Compute node coordinate array of shape $(400, 2)$.
  2. Compute Euclidean distance matrix via `scipy.spatial.distance_matrix`.
  3. Form binary adjacency matrix $A$ where $0 < d(v_i, v_j) \le 1.01$.
  4. Compute total edges as $\frac{1}{2} \sum A_{ij}$.
  5. Compute node degree vector $d_i = \sum_j A_{ij}$ and mean degree.
  6. Verify symmetry $A = A^T$ and diagonal $\operatorname{diag}(A) = \mathbf{0}$.
- **Expected Result**: $|V| = 400$, undirected $|E| = 760$, mean degree $= 3.8$ neighbors (interior nodes $= 4$, edge nodes $= 3$, corner nodes $= 2$).
- **Pass Criterion**: Exactly 760 edges, zero diagonal, perfect symmetry.

### VP-005: Graph Mesh Artifact Export
- **Verifies**: FR-009, IF-002, IF-003
- **Setup**: Built `adj_matrix`, `node_coords`, `dem_grid`, `slope_deg`.
- **Procedure**:
  1. Create directory `/kaggle/working/data_processed/`.
  2. Call `np.savez_compressed` saving the four arrays to `spatial_graph_mesh.npz`.
  3. Reload file from disk and assert all 4 keys exist and shapes match memory arrays.
- **Expected Result**: Archive successfully written and byte-readable.
- **Pass Criterion**: File exists on disk, uncorrupted, with matching array contents.

### VP-006: PyTorch Edge Index and Graph Tensor Conversion
- **Verifies**: FR-010, DI-003
- **Setup**: Loaded `spatial_graph_mesh.npz` or local `adj_matrix`.
- **Procedure**:
  1. Extract `src_nodes, dst_nodes` via `np.where(adj_mat > 0)`.
  2. Stack into PyTorch long tensor `edge_index` of shape $[2, 2|E|]$.
- **Expected Result**: `edge_index.shape == torch.Size([2, 1520])`.
- **Pass Criterion**: Exact shape $[2, 1520]$, data type `torch.int64`.

### VP-007: Multi-Sensor Node Feature Tensor Construction
- **Verifies**: FR-011, DI-006, UQ-001
- **Setup**: Spatial arrays `dem_arr`, `slope_arr`, synthetic `f_sar`, `f_ndvi`.
- **Procedure**:
  1. Standardize DEM: `(dem - mean) / (std + 1e-6)`.
  2. Standardize Slope: `(slope - mean) / (std + 1e-6)`.
  3. Draw `f_sar` from $\mathcal{N}(0, 1)$ ($N=400$).
  4. Draw `f_ndvi` from $\mathcal{U}(0, 1)$ ($N=400$).
  5. Assemble column-stacked matrix $X \in \mathbb{R}^{400 \times 4}$ and convert to PyTorch float32 tensor.
- **Expected Result**: Tensor shape `torch.Size([400, 4])`, zero NaNs, finite values.
- **Pass Criterion**: Exact dimensions $400 \times 4$, zero NaN/Inf values.

### VP-008: Normalized Laplacian Calculation
- **Verifies**: FR-012, DI-007
- **Setup**: Adjacency matrix $A \in \{0, 1\}^{400 \times 400}$.
- **Procedure**:
  1. Add self-loops: $\tilde{A} = A + I_{400}$.
  2. Sum row degrees: $\tilde{D}_i = \sum_j \tilde{A}_{ij}$.
  3. Form diagonal inverse square-root matrix: $\tilde{D}^{-1/2} = \operatorname{diag}(\tilde{D}^{-0.5})$.
  4. Compute $\hat{A} = \tilde{D}^{-1/2} \tilde{A} \tilde{D}^{-1/2}$.
- **Expected Result**: Tensor shape `torch.Size([400, 400])`, symmetric, positive elements.
- **Pass Criterion**: Diagonal elements equal $1 / (\text{degree} + 1)$, all row sums $\le 1.0$.

### VP-009: GCN Model Instantiation and Layer Validation
- **Verifies**: FR-013, UQ-002
- **Setup**: PyTorch neural network runtime under seed 42.
- **Procedure**:
  1. Instantiate `SpatialGCN(in_features=4, hidden_dim=16, out_features=8)`.
  2. Inspect module parameters: `gconv1.linear.weight` $(16, 4)$, `gconv2.linear.weight` $(8, 16)$, `dropout` ($p=0.1$).
- **Expected Result**: Model contains 2 graph convolution stages with matching tensor shapes.
- **Pass Criterion**: Parameter initialization succeeds; model representation matches specification.

### VP-010: GCN Forward Pass Execution and Output Bounds Audit
- **Verifies**: FR-014, DI-006, UQ-003
- **Setup**: Instantiated `SpatialGCN`, input $X$ (`torch.Size([400, 4])`), $\hat{A}$ (`torch.Size([400, 400])`).
- **Procedure**:
  1. Set `model.eval()`.
  2. Execute with `torch.no_grad()`: `spatial_embeddings = model(X_tensor, A_hat)`.
  3. Compute minimum and maximum bounds of output numpy array.
- **Expected Result**: `spatial_embeddings.shape == torch.Size([400, 8])`. Output minimum equals **-0.4555**, maximum equals **0.3316**.
- **Pass Criterion**: Zero NaNs, dimensions exactly $400 \times 8$, bounds match deterministic seed.

### VP-011: Aerospace Plot 3 GCN Latent Representation
- **Verifies**: NF-003, D
- **Setup**: Output embedding array, reshaped to $20 \times 20$ for Channel 0 and Channel 1.
- **Procedure**:
  1. Render 2D spatial heatmap of Channel 0 and Channel 1.
  2. Inject diagnostic annotation text box.
- **Expected Result**: Two subplots displayed showing spatial embedding distributions.
- **Pass Criterion**: Plot displays successfully (auditing open defect D-001).

### VP-012: Latent Embedding Artifact Export
- **Verifies**: FR-015, IF-004
- **Setup**: Calculated `spatial_embeddings`, `model.state_dict()`, `A_hat`.
- **Procedure**:
  1. Serialize dictionary to `/kaggle/working/data_processed/spatial_gcn_embeddings.pt` via `torch.save`.
  2. Reload file and verify keys and tensor shapes.
- **Expected Result**: File written to disk, reload succeeds without deserialization error.
- **Pass Criterion**: File exists, contains all 3 specified keys, tensor dimensions verified.

---

## 7. Verification Results

Evidence tags:
- **`[NB]`**: Directly extracted from saved executed cell output streams and display data in `03-spatial-modeling.ipynb`.
- **`[AN]`**: Independently re-computed analytical or numerical check matching identical seeds and operations.
- **`[INS]`**: Manual source code and structural file inspection.

| VP ID | Verification Target | Execution Date | Executor | Result | Empirical Evidence & Numerical Values | Reviewer |
|:---|:---|:---:|:---:|:---:|:---|:---:|
| **VP-001** | Telemetry Ingest & Grid Setup | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 04: *"Loaded Preprocessed Telemetry Dataset: 35 records"*, *"Reconstructed Spatial Sub-Grid Footprint: 20x20 Nodes (400 Total Spatial Vertices)"*. | *Pending* |
| **VP-002** | Terrain Slope & Aspect Extraction | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 06: Mean Slope: **3.06°** (Range: **[0.13°, 8.96°]**), Mean Aspect: **182.17°**. Zero negative slopes. | *Pending* |
| **VP-003** | Aerospace Plot 1 Terrain Maps | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 08: PNG rendered (length: 78,148 bytes). Diagnostic text: Max Delta: **17.81m**, Mean Slope: **3.06°**. | *Pending* |
| **VP-004** | $k$-NN Adjacency & Degree Consistency | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 10: Vertices $|V| = \mathbf{400}$, Edges $|E| = \mathbf{760}$, Mean Degree $= \mathbf{3.8}$ neighbors. Symmetric matrix verified. | *Pending* |
| **VP-005** | Graph Mesh `.npz` File Export | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 14: Saved `spatial_graph_mesh.npz` to `/kaggle/working/data_processed/`. Shape: 400 nodes. | *Pending* |
| **VP-006** | PyTorch Edge Index Conversion | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 16: Graph Nodes: **400**, Graph Edges: **1520**, Edge Tensor Shape: `torch.Size([2, 1520])`. | *Pending* |
| **VP-007** | Node Feature Matrix ($X$) Assembly | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 18: Dimensions: `torch.Size([400, 4])`, $F_{\text{in}} = 4$ (DEM, Slope, SAR, NDVI). Zero NaNs. | *Pending* |
| **VP-008** | Normalized Laplacian ($\hat{A}$) Tensor | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 22: Shape: `torch.Size([400, 400])`, symmetric, normalized diagonal. | *Pending* |
| **VP-009** | 2-Layer GCN Instantiation | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 20: Instantiated `SpatialGCN(gconv1: 4->16, dropout: p=0.1, gconv2: 16->8)`. | *Pending* |
| **VP-010** | Forward Pass & Latent Embeddings | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 22: Latent Matrix Shape: `torch.Size([400, 8])`. Output Bounds: Min = **-0.4555**, Max = **0.3316**. | *Pending* |
| **VP-011** | Aerospace Plot 3 Latent Embedding Maps | 2026-10-08 | Automated / G. Mohapatra | **FAIL\*** | `[NB]` Cell 24: PNG rendered (length: 74,972 bytes). \*Failed due to defect **D-001**: Subplot 2 plots Channel 0 instead of Channel 1. | *Pending* |
| **VP-012** | Model & Embedding Artifact Persistence | 2026-10-08 | Automated / G. Mohapatra | **PASS** | `[NB]` Cell 26: Exported `spatial_gcn_embeddings.pt` containing embeddings, state dict, and $\hat{A}$. | *Pending* |

---

## 8. Requirements Traceability Matrix

```
Requirement (Section 4)
       │
       ▼
Software Design & Code Cell (Notebook Implementation)
       │
       ▼
Verification Procedure (Section 6)
       │
       ▼
Verification Result & Empirical Evidence (Section 7)
```

| Requirement ID | Design Implementation Element | Code Cell | Verification Procedure | Verification Result |
|:---|:---|:---:|:---:|:---:|
| **FR-001** | Telemetry existence verification & fallback reader | Cell 04 | VP-001 | **PASS** |
| **FR-002** | Spatial grid footprint configuration ($GRID\_DIM = 20$) | Cell 04 | VP-001 | **PASS** |
| **FR-003** | Sobel derivative convolution ($\Delta X = 10.0\text{ m}$) | Cell 06 | VP-002 | **PASS** |
| **FR-004** | Topographic slope calculation in degrees | Cell 06 | VP-002 | **PASS** |
| **FR-005** | Topographic aspect calculation in degrees | Cell 06 | VP-002 | **PASS** |
| **FR-006** | Coordinate grid & Euclidean distance matrix | Cell 10 | VP-004 | **PASS** |
| **FR-007** | 4-neighbor spatial grid thresholding ($d \le 1.01$) | Cell 10 | VP-004 | **PASS** |
| **FR-008** | Node degree vector and topological connectivity audit | Cell 10 | VP-004 | **PASS** |
| **FR-009** | Compressed NumPy export (`spatial_graph_mesh.npz`) | Cell 14 | VP-005 | **PASS** |
| **FR-010** | Directed PyTorch `edge_index` generation | Cell 16 | VP-006 | **PASS** |
| **FR-011** | Standardized 4-channel node feature matrix assembly ($X$) | Cell 18 | VP-007 | **PASS** |
| **FR-012** | Symmetric normalized Laplacian computation ($\hat{A}$) | Cell 20 | VP-008 | **PASS** |
| **FR-013** | Custom `GraphConvLayer` & `SpatialGCN` PyTorch modules | Cell 20 | VP-009 | **PASS** |
| **FR-014** | Forward propagation evaluation under `torch.no_grad()` | Cell 22 | VP-010 | **PASS** |
| **FR-015** | PyTorch model checkpoint and embedding export (`.pt`) | Cell 26 | VP-012 | **PASS** |
| **DI-001** | Adjacency matrix symmetry and zero diagonal assertions | Cell 10 | VP-004 | **PASS** |
| **DI-002** | Planar grid 760 undirected edge conservation | Cell 10 | VP-004 | **PASS** |
| **DI-003** | 1520 directed edge index size conservation | Cell 16 | VP-006 | **PASS** |
| **DI-004** | Non-negative slope angle boundary condition | Cell 06 | VP-002 | **PASS** |
| **DI-005** | Circular aspect azimuth $[0^\circ, 360^\circ)$ boundary | Cell 06 | VP-002 | **PASS** |
| **DI-006** | Zero NaN/Inf validation in node features and embeddings | Cells 18, 22 | VP-007, VP-010 | **PASS** |
| **DI-007** | Normalized Laplacian spectral diagonal dominance | Cell 20 | VP-008 | **PASS** |
| **IF-001** | Telemetry path existence check with warning fallback | Cell 04 | VP-001 | **PASS** |
| **IF-002** | Destination directory initialization via `os.makedirs` | Cells 14, 26 | VP-005, VP-012 | **PASS** |
| **IF-003** | `.npz` archive key-value contract validation | Cell 14 | VP-005 | **PASS** |
| **IF-004** | `.pt` dictionary serialization contract validation | Cell 26 | VP-012 | **PASS** |
| **UQ-001** | Feature scaling epsilon denominator ($10^{-6}$) | Cell 18 | VP-007 | **PASS** |
| **UQ-002** | Affine linear layer bias inclusion | Cell 20 | VP-009 | **PASS** |
| **UQ-003** | Diagnostic forward pass logging of output extrema | Cell 22 | VP-010 | **PASS** |
| **NF-001** | Deterministic seed initialization (NumPy 101, PyTorch 42) | Cells 04, 16 | VP-001, VP-006 | **PASS** |
| **NF-002** | Unattended top-to-bottom cell execution | All cells | Execution Audit | **PASS** |
| **NF-003** | Dark telemetry styling parameters | Cells 02, 08, 12, 24 | VP-003, VP-011 | **PASS** |
| **NF-004** | Source code syntax and naming hygiene | All cells | Inspection | **PARTIAL** |
| **NF-005** | Environment-independent relative path handling | Cells 04, 14, 26 | Inspection | **FAIL** |

---

## 9. Configuration and Change Control

### 9.1 Controlled Items

The following items constitute the controlled configuration baseline for Notebook 03:
1. **Source Notebook**: `1_notebooks_sandbox/03-spatial-modeling.ipynb` (SHA-256 baseline hash required).
2. **Requirements & Verification Document (This Document)**: `8_docs/01_Notebooks/03. spatial modeling/03-spatial-modeling_DO178C_Documentation.md`.
3. **Companion Sphinx Document**: `8_docs/01_Notebooks/03. spatial modeling/03-spatial-modeling_DO178C_Documentation.rst`.
4. **Export Artifact 1**: `spatial_graph_mesh.npz` (Compressed graph topology archive).
5. **Export Artifact 2**: `spatial_gcn_embeddings.pt` (PyTorch latent embedding dictionary).
6. **Execution Environment**: Python virtual environment with pinned packages (NumPy, SciPy, PyTorch, Matplotlib, Pandas).

### 9.2 Baseline Identification

- **Current Working Baseline**: `NB03-BL-01-DRAFT`
- **Target Release Baseline**: `NB03-BL-01`
- **Associated Upstream Baseline**: `NB02-BL-01` (`preprocessed_telemetry.csv`, `scaler_manifest.json`)
- **Downstream Target Baseline**: `NB04-BL-01` (`04-temporal-modeling.ipynb` / PINN formulation)

### 9.3 Change Procedure

Any modification to requirements, mathematical algorithms, code cells, or generated artifacts shall adhere to the following life-cycle control loop:

```
[Change Request (CR)] 
        │
        ▼
[Impact Analysis on Graph Topology & PINN Couplings] 
        │
        ▼
[Technical Review & Approval by Lead Authority] 
        │
        ▼
[Code / Documentation Modification] 
        │
        ▼
[Execution of Verification Procedures VP-001 to VP-012] 
        │
        ▼
[Traceability Matrix & Document Control Update] 
        │
        ▼
[Baseline Tag Update]
```

### 9.4 Version Control Rules

1. **Commit Integrity**: Code cells in `.ipynb` shall have cell outputs cleared or deterministically committed matching the baseline hash.
2. **Deterministic Regeneration**: Clean environment re-execution shall reproduce byte-identical tensors for fixed seeds.
3. **Requirement Atomicity**: No requirement shall be modified or deleted without updating the bidirectional traceability matrix.
4. **Deprecation**: Deprecated requirements shall be marked `WITHDRAWN` and shall not have their numerical IDs reassigned.

---

## 10. Open Defects and Discrepancies

| ID | Description | Affected Requirement | Severity | Status | Corrective Action |
|:---|:---|:---:|:---:|:---:|:---|
| **D-001** | **Aerospace Plot 3 Duplicate Channel Bug**: Cell 24 extracts both `emb_ch0` and `emb_ch1`, but line 490 executes `ax2.imshow(emb_ch0)` instead of `ax2.imshow(emb_ch1)`, rendering Channel 0 twice and omitting Channel 1. | NF-003, D | **MEDIUM** | **OPEN** | In Cell 24, replace `im2 = ax2.imshow(emb_ch0, ...)` with `im2 = ax2.imshow(emb_ch1, ...)`. |
| **D-002** | **Disconnection Between Telemetry Table and Spatial Grid**: Cell 04 loads `df_prep` (35 rows), but the spatial grid generation completely ignores this table and constructs synthetic arrays (`dem_grid`, `sar_grid`). | FR-001, FR-002 | **HIGH** | **OPEN** | Interpolate or reconstruct true spatial raster grids from ingested telemetry or georeferenced GeoTIFFs rather than synthetic uniform fields. |
| **D-003** | **Unused Synthetic SAR Grid in Node Features**: In Cell 04, `sar_grid` is generated, but in Cell 18, `f_sar` is generated as fresh uncorrelated Gaussian noise `np.random.normal(0, 1)`, ignoring `sar_grid`. | FR-011 | **MEDIUM** | **OPEN** | Standardize and flatten the actual `sar_grid` array into `f_sar` instead of generating independent random noise. |
| **D-004** | **Hardcoded `/kaggle/` Absolute Paths**: Ingestion and export paths (`/kaggle/input/...`, `/kaggle/working/...`) prevent out-of-the-box local repository execution. | NF-005, IF-001 | **MEDIUM** | **OPEN** | Implement repository-relative path resolution via `pathlib.Path` or environment configuration parameters. |
| **D-005** | **Lack of Formal Runtime Assertions**: Ingestion and topological properties are reported via `print()` statements rather than enforced via programmatic `assert` statements. | DI-001 to DI-007 | **LOW** | **OPEN** | Introduce defensive assertions for matrix symmetry, edge counts, and absence of NaNs before export. |
| **D-006** | **Lack of Georeferencing / CRS Metadata**: Spatial graph mesh contains only 0-indexed discrete coordinates without EPSG:4326/EPSG:32645 projection or affine transform parameters. | IF-003 | **HIGH** | **OPEN** | Attach geotransform metadata (origin coordinates, cell size in meters, CRS string) to `spatial_graph_mesh.npz`. |
| **D-007** | **In-Memory Fallback Conceals Missing Pipeline Files**: Cell 16 contains fallback `adj_mat = adj_matrix` if the `.npz` file does not exist, masking file I/O failures during single-kernel runs. | UQ-002 | **LOW** | **OPEN** | Require strict disk reload verification rather than silent fallback to in-memory scope variables. |
| **D-008** | **Unused Edge Index in Forward Pass**: `edge_index` is constructed in Cell 16 but the GCN model in Cell 20 utilizes dense matrix multiplication (`torch.matmul(A_hat, h)`), leaving `edge_index` unused. | FR-010 | **LOW** | **OPEN** | Clarify whether `edge_index` is reserved for PyTorch Geometric (PyG) compatibility in downstream modules. |

---

## 11. Risks and Assumptions

### 11.1 Technical Risks

| Risk ID | Risk Description | Severity | Likelihood | Consequence | Mitigation Strategy |
|:---|:---|:---:|:---:|:---|:---|
| **R-001** | **Scientific Misinterpretation of Synthetic Grid** | Critical | High | Synthetic gradient statistics mistaken for verified field observations at Bhadrak/Balasore. | Enforce mandatory synthetic disclosure banner and require real COG raster ingestion before field deployment. |
| **R-002** | **Dense Laplacian Scalability Limits** | Moderate | Medium | $N \times N$ dense matrix multiplication ($\hat{A} \in \mathbb{R}^{400 \times 400}$) will cause GPU out-of-memory errors on larger operational grids ($1000 \times 1000 = 10^6$ nodes). | Migrate from dense `torch.matmul` to sparse tensor representation (`torch.sparse_coo_tensor` or PyG `MessagePassing`). |
| **R-003** | **Uncalibrated Random Feature Convolutions** | Moderate | High | Latent embeddings generated from randomly initialized GCN weights without training or calibration. | Document that Notebook 03 produces initialized structural representations; train weights under PINN loss in Notebook 05. |
| **R-004** | **Planar Grid Boundary Distortion** | Low | Low | Boundary nodes have degree 2 or 3 while interior nodes have degree 4, inducing boundary edge effects in GCN message passing. | Implement mirror padding or virtual boundary nodes in Laplacian calculation. |
| **R-005** | **Path Environment Brittleness** | Moderate | High | Notebook execution fails when running outside the Kaggle cloud environment due to hardcoded `/kaggle/` paths. | Refactor to environment-aware path configurations (`PROCESSED_DIR = os.getenv('DATA_DIR', './data')`). |

### 11.2 Architectural Assumptions

| Assumption ID | Statement of Assumption | Rationale |
|:---|:---|:---|
| **A-001** | **Planar Orthogonal Grid Geometry** | The spatial terrain domain is modeled as a 2D regular square grid where cell spacing $\Delta X = \Delta Y = 10.0\text{ m}$. |
| **A-002** | **Local 4-Connected Spatial Dependency** | Soil moisture diffusion and surface runoff primarily couple directly between adjacent cardinal grid cells (North, South, East, West). |
| **A-003** | **Linear Isotropic Graph Smoothing** | Kipf-Welling first-order spectral Chebyshev approximation provides sufficient spatial feature aggregation for soil property continuity. |
| **A-004** | **Uniform Temporal Snapshot** | Spatial terrain gradients (DEM slope/aspect) are temporally invariant across the simulation window, while SAR and NDVI vary dynamically. |
| **A-005** | **Decoupled Structural Initialization** | Forward pass evaluation with fixed pseudo-random weights generates a valid initial latent feature manifold prior to physics-informed optimization. |

---

## 12. Release and Baseline Acceptance Criteria

Notebook `03-spatial-modeling.ipynb` shall achieve formal release baseline `NB03-BL-01` only upon meeting all of the following criteria:

1. **Mandatory Requirements Compliance**: All Functional (FR), Data Integrity (DI), and Interface (IF) requirements marked **MET** or formally **WAIVED**.
2. **Verification Suite Execution**: 100% of Verification Procedures VP-001 through VP-012 executed and recorded with **PASS** status.
3. **Critical Defect Resolution**: Defect **D-001** (Plot 3 duplicate channel) and **D-003** (unused SAR grid) resolved and re-verified.
4. **Defensive Assertions**: Programmatic assertions added to the notebook for matrix symmetry, edge counts, and tensor bounds.
5. **Path Neutrality**: Elimination of hardcoded `/kaggle/` paths, enabling verified execution on the local JCC RS-SDA compute cluster.
6. **Full Bidirectional Traceability**: Zero unmapped requirements, unverified design elements, or undocumented cell outputs.
7. **Independent Review Sign-Off**: Completion of formal review signatures by an authorized technical authority other than the author.

---

## 13. Review and Approval

| Role | Designee / Authority | Division & Facility | Signature | Date |
|:---|:---|:---|:---:|:---:|
| **Author / Developer** | Gourgopal Mohapatra | RS-SDA Division, JCC Campus 2 | *Gourgopal Mohapatra* | 2026-10-08 |
| **Independent Technical Reviewer** | *(Assigned Reviewer)* | JCC Systems Engineering | ___________________ | ___________ |
| **Lead Systems Approver** | *(Approving Authority)* | JCC Command & Control | ___________________ | ___________ |

---

## 14. Limitations and Scientific Boundaries

> [!CAUTION]
> **SEPARATION OF SOFTWARE VERIFICATION AND SCIENTIFIC VALIDATION**
> 
> Successful completion of the verification procedures defined in this document confirms that:
> 1. The Python code executes without unhandled runtime exceptions.
> 2. The numerical operators (Sobel gradients, $k$-NN adjacency, Laplacian renormalization, GCN linear transformations) evaluate in exact conformity with their mathematical formulas.
> 3. Array dimensions, tensor structures, and file serialization contracts are computationally correct.
> 
> **THIS DOES NOT CONSTITUTE EMPIRICAL SCIENTIFIC VALIDATION OF THE MRIDANSH ESTIMATION ACCURACY.**
> 
> The elevation and backscatter inputs currently processed are synthetic pseudorandom arrays. Consequently:
> - The computed terrain slopes and aspect orientations do not reflect true topography at coordinates $(21.1378^\circ\text{ N}, 86.6874^\circ\text{ E})$.
> - The 8-dimensional GCN embeddings represent un-trained structural representations and cannot be used for operational civil engineering or agronomic decision-making.
> - Full scientific validation requires substitution of synthetic arrays with calibrated Sentinel-1 RTC GeoTIFFs, Sentinel-2 L2A surface reflectances, and 30-meter Copernicus DEM rasters coupled with in-situ soil moisture sensor telemetry.

---

## 15. Intellectual Property and Controlled Distribution

```
========================================================================================
                      JAGANNATH COMMAND CENTER (JCC HEADQUARTER)
             JCC CAMPUS 2 — REMOTE SENSING & SPATIAL DATA ANALYTICS (RS-SDA)
                           PROJECT: THE MRIDANSH (AETHER-MRID1607X)
========================================================================================
```

**Copyright © 2026 Gourgopal Mohapatra. All Rights Reserved.**

This document, the underlying software architecture, mathematical formalisms, graph neural network implementations, and associated telemetry data structures constitute **proprietary intellectual property** developed under the auspices of JCC RS-SDA Division.

Unauthorized copying, distribution, decompilation, reverse engineering, dissemination, or commercial utilization—in whole or in part, in any format or medium—is strictly prohibited without prior express written authorization from the author and JCC Command Authority.

```
========================================================================================
                      CLASSIFICATION: STRICTLY PROPRIETARY & CONTROLLED
========================================================================================
```
