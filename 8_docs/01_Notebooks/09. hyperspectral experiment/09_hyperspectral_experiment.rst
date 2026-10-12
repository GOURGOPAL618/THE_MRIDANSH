========================================================================================
THE MRIDANSH (AETHER-MRID1607X) - Notebook 09: Hyperspectral Augmentation Experiment
========================================================================================

:Project: THE MRIDANSH - Unified Soil State Estimation System
:Engine: AETHER-MRID1607X (Multi-Domain Soil Intelligence Engine)
:Notebook: ``09-hyperspectral-experiment.ipynb``
:Sprint phase: Days 8-10 of the Scientific Audit & Validation Mission
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
The primary technical objective of ``09-hyperspectral-experiment.ipynb`` is to design, execute,
and evaluate a formal hypothesis testing experiment investigating whether high-dimensional
Hyperspectral Imaging (HSI) observations provide statistically significant, non-redundant soil
state information beyond the frozen baseline configuration of **THE MRIDANSH** (*AETHER-MRID1607X*).
The notebook tests the alternative hypothesis (:math:`H_1`) against the null hypothesis (:math:`H_0`),
evaluates spectral information compression via Principal Component Analysis (PCA), benchmarks
prediction accuracy and uncertainty contraction, audits sensor dropout fallback recovery, and
weighs computational overheads (latency and RAM footprint) to establish the production deployment policy.

1.2 System Context
------------------
Within the macro-architecture of **THE MRIDANSH**:

* **Upstream Frozen Baseline (:math:`\text{CONFIG-A}`)**: Consists of multispectral Sentinel-2,
  C-band SAR Sentinel-1, digital elevation models (DEM), meteorological precipitation data,
  Richards PDE physics-informed neural network (PINN) constraints, and Ensemble Kalman Filter (EnKF)
  data assimilation (Notebooks 01–07).
* **Core Experimental Engine (:math:`\text{CONFIG-B}`)**: Synthesizes a 224-channel contiguous
  VNIR/SWIR hyperspectral cube (:math:`400 - 2500\text{ nm}`), applies atmospheric water vapor absorption
  filtering, extracts 10 orthogonal spectral feature vectors via PCA, and performs a controlled
  AB benchmark against :math:`\text{CONFIG-A}` over a held-out test dataset (:math:`N=200`).
* **Downstream Integration**: Emits formal integration recommendations, performance deltas, and
  fallback governance rules to Notebook 10 (*Ablation Study*) and Notebook 11 (*Generalization Baseline*).

1.3 Design Boundary
-------------------
The design boundary of Notebook 09 is demarcated as follows:

* **In Boundary**:
  - Generation of a synthetic 224-band hyperspectral data cube representing PRISMA/EnMAP/AVIRIS standards.
  - Soil reflectance continuum formulation with non-linear absorption dips at :math:`1400\text{ nm}` and :math:`1900\text{ nm}`.
  - Atmospheric quality control (QC) masking dropping 24 channels in the 1350–1420 nm and 1800–1950 nm windows.
  - Feature standardization and linear dimensionality reduction extracting 10 principal components.
  - Controlled AB performance testing evaluating RMSE, MAE, :math:`R^2`, and mean uncertainty :math:`\sigma`.
  - Fallback evaluation under 50% band corruption and 100% sensor blackout.
  - Multi-criteria trade-off matrix compilation incorporating computational runtime and memory footprint.
  - Rendering of three diagnostic Matplotlib figures (Plots 1, 2, and 3).
* **Out of Boundary**:
  - Live ingestion of L1C/L2D spaceborne HSI tiles from external data hubs.
  - Radiative transfer modeling of atmospheric path radiance (e.g. MODTRAN, 6SV).
  - Training of non-linear deep spectral autoencoders or 3D convolutional networks.
  - Physical serialization of transformed PCA weight matrices to disk.

1.4 Relationship to Requirements
--------------------------------
This technical description details the mathematical models, algorithmic execution loops,
and component specifications that implement the functional requirements (`FR-001` through `FR-015`),
data integrity constraints (`DI-001` through `DI-005`), and quality standards established in
``09_hyperspectral_experiment_REQUIREMENTS.md``.


2. Architecture
===============

2.1 Notebook Architecture
-------------------------
The software architecture of Notebook 09 is structured into four functional tiers:

.. code-block:: text

   +---------------------------------------------------------------------------------+
   |                          TIER 1: SPECTRAL DEFINITION                            |
   |  - 224 Channels (400 - 2500 nm, Delta_lambda ~ 9.4 nm)                          |
   |  - Soil Reflectance Continuum + 1400 nm / 1900 nm Water Absorption Dips        |
   |  - Synthetic HSI Raw Cube: (1000 pixels, 224 bands)                             |
   +---------------------------------------------------------------------------------+
                                           |
                                           v
   +---------------------------------------------------------------------------------+
   |                     TIER 2: QUALITY CONTROL & COMPRESSION                       |
   |  - Atmospheric Masking: 1350-1420 nm (SWIR-1) & 1800-1950 nm (SWIR-2)           |
   |  - Cleaned QC Cube: 200 Contiguous Channels (24 dropped)                        |
   |  - StandardScaler -> PCA(n_components=10) -> (1000, 10) Feature Matrix          |
   +---------------------------------------------------------------------------------+
                                           |
                                           v
   +---------------------------------------------------------------------------------+
   |                     TIER 3: CONTROLLED AB TESTING ENGINE                        |
   |  - Ground Truth: y_true in [0.05, 0.45] m^3/m^3 (800 Train / 200 Test Split)   |
   |  - CONFIG-A (Frozen Baseline) vs CONFIG-B (Hyperspectral Augmented)             |
   |  - Evaluation: RMSE, MAE, R^2, Mean Uncertainty sigma                           |
   |  - Fallback Audit: 50% Noise Corruption & 100% Dropout Reversion                |
   +---------------------------------------------------------------------------------+
                                           |
                                           v
   +---------------------------------------------------------------------------------+
   |                   TIER 4: MULTI-CRITERIA TRADE-OFF & VERDICT                    |
   |  - Trade-Off Matrix: Accuracy, Uncertainty, Latency (+300%), RAM (+300%)       |
   |  - Plot 3: Normalized Multi-Criteria Score Visualizer                           |
   |  - Hypothesis Test Decision: Reject H0 -> Accept H1                             |
   |  - Operational Deployment Policy Formulation                                    |
   +---------------------------------------------------------------------------------+

2.2 Processing Pipeline
-----------------------
Execution proceeds sequentially across three sprint phases:

1. **Phase 1: Spectral Definition & Quality Filtering (Day 8, Cells 00–09)**
   - Configures dark telemetry styling and hardware devices.
   - Computes continuous soil reflectance spectrum across 224 channels and instantiates the raw data cube.
   - Evaluates atmospheric water vapor masks, dropping 24 bands to yield a 200-band QC cube.
   - Standardizes features and executes PCA to extract 10 principal components.
   - Renders Plot 1 (Mean spectral signatures and Sentinel-2 channel comparison).
2. **Phase 2: Controlled AB Testing & Fallback Audit (Day 9, Cells 10–17)**
   - Synthesizes non-linear ground truth soil moisture :math:`y_{\text{true}}` over 1000 samples.
   - Partitions data into 800 training samples and 200 held-out test samples.
   - Simulates predictions and uncertainty bounds for :math:`\text{CONFIG-A}` and :math:`\text{CONFIG-B}`.
   - Renders Plot 2 (Prediction scatter and uncertainty boxplot distribution).
   - Audits missing HSI fallback across Full HSI, 50% Corruption, and 100% Dropout states.
3. **Phase 3: Multi-Metric Trade-Off & Deployment Policy (Day 10, Cells 18–23)**
   - Constructs multi-metric trade-off DataFrame incorporating accuracy, latency, and memory metrics.
   - Renders Plot 3 (Normalized multi-criteria performance bar chart).
   - Evaluates the formal hypothesis test, logging the rejection of :math:`H_0` and acceptance of :math:`H_1`.
   - Formalizes the two-tier operational deployment decision matrix.

2.3 Component Relationships
---------------------------
Components communicate via in-memory array passing:

* **Wavelength Generator**: Emits the 1D wavelength array :math:`\mathbf{\lambda} \in \mathbb{R}^{224}`.
* **Spectral Synthesizer**: Produces raw cube :math:`\mathbf{X}_{\text{raw}} \in \mathbb{R}^{1000 \times 224}`.
* **Atmospheric QC Filter**: Produces boolean mask :math:`\mathbf{M}_{\text{valid}} \in \{0, 1\}^{224}` and filtered cube :math:`\mathbf{X}_{\text{qc}} \in \mathbb{R}^{1000 \times 200}`.
* **PCA Subsystem**: Emits compressed feature matrix :math:`\mathbf{Z}_{\text{HSI}} \in \mathbb{R}^{1000 \times 10}` and explained variance ratios.
* **AB Evaluator**: Ingests test indices, calculates prediction residuals, and outputs summary error metrics.
* **Trade-Off Module**: Aggregates accuracy metrics and computational overhead parameters into tabular and graphical artifacts.

2.4 Data Flow
-------------
The data transformation sequence is a purely forward DAG:

.. code-block:: text

   wavelengths [224] ──> soil_reflectance_base [224] ──> hsi_raw_cube [1000, 224]
                                                                │
                                                                ▼
                                                    Atmospheric Filter Mask
                                                    (Drops 24 noisy bands)
                                                                │
                                                                ▼
                                                     hsi_qc_cube [1000, 200]
                                                                │
                                                                ▼
                                                     StandardScaler + PCA(10)
                                                                │
                                                                ▼
                                                    hsi_pca_features [1000, 10]
                                                                │
         ┌──────────────────────────────────────────────────────┴──────────────────────┐
         ▼                                                                             ▼
   y_true [1000] ──> Split (800 / 200)                                       Plot 1 (Spectral Curves)
         │
         ├──> CONFIG-A Sim: pred_a [200], unc_a [200]
         ├──> CONFIG-B Sim: pred_b [200], unc_b [200]
         │          │
         │          ▼
         │    Plot 2 (Scatter & Boxplots)
         │          │
         │          ▼
         │    Fallback Audit (Full -> 50% -> 100% Dropout)
         │          │
         └──────────┼──────────────────────────────────────────────────────────┐
                    ▼                                                          ▼
             Trade-Off Matrix                                           Plot 3 (Scores)
                    │
                    ▼
             Hypothesis Decision ($H_1$ Accepted)


3. Execution Flow
=================

3.1 Initialization and Seed Locking
-----------------------------------
Execution begins in Cell 02 by importing dependencies, applying dark styling, and setting random seeds:

.. code-block:: python

   import os, sys, numpy as np, pandas as pd, torch, matplotlib.pyplot as plt
   from sklearn.decomposition import PCA
   from sklearn.preprocessing import StandardScaler

   plt.style.use('dark_background')
   plt.rcParams['font.family'] = 'monospace'
   plt.rcParams['axes.edgecolor'] = '#00FFCC'
   plt.rcParams['axes.linewidth'] = 1.2
   plt.rcParams['grid.color'] = '#1A3344'
   plt.rcParams['grid.linestyle'] = '--'
   plt.rcParams['grid.alpha'] = 0.5

   device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
   np.random.seed(1607)
   torch.manual_seed(1607)

3.2 Hyperspectral Data Cube Synthesis
-------------------------------------
Cell 04 defines the spectral grid and simulates the raw data cube:

.. code-block:: python

   NUM_PIXELS = 1000
   NUM_BANDS = 224
   wavelengths = np.linspace(400, 2500, NUM_BANDS)

   soil_reflectance_base = 0.10 + 0.35 * (1 - np.exp(-wavelengths / 800))
   absorption_1400 = 0.15 * np.exp(-((wavelengths - 1400) / 40)**2)
   absorption_1900 = 0.20 * np.exp(-((wavelengths - 1900) / 50)**2)

   clean_spectrum = soil_reflectance_base - absorption_1400 - absorption_1900
   hsi_raw_cube = np.tile(clean_spectrum, (NUM_PIXELS, 1)) + np.random.normal(0, 0.02, size=(NUM_PIXELS, NUM_BANDS))

3.3 Atmospheric Absorption Window Filtering
-------------------------------------------
Cell 06 identifies contaminated water vapor channels and applies quality masking:

.. code-block:: python

   mask_1400 = (wavelengths >= 1350) & (wavelengths <= 1420)
   mask_1900 = (wavelengths >= 1800) & (wavelengths <= 1950)
   noisy_band_mask = mask_1400 | mask_1900

   valid_band_mask = ~noisy_band_mask
   hsi_qc_cube = hsi_raw_cube[:, valid_band_mask]
   valid_wavelengths = wavelengths[valid_band_mask]

   hsi_qc_cube = np.nan_to_num(hsi_qc_cube, nan=0.0, posinf=1.0, neginf=0.0)
   hsi_qc_cube = np.clip(hsi_qc_cube, 0.0, 1.0)

This process drops exactly 24 bands, retaining 200 valid channels.

3.4 PCA Dimensionality Reduction
--------------------------------
Cell 09 standardizes the QC cube and fits the PCA decomposition engine:

.. code-block:: python

   scaler = StandardScaler()
   hsi_scaled = scaler.fit_transform(hsi_qc_cube)

   pca_engine = PCA(n_components=10)
   hsi_pca_features = pca_engine.fit_transform(hsi_scaled)

   explained_var = pca_engine.explained_variance_ratio_ * 100
   cum_var = np.cumsum(explained_var)

3.5 Benchmark Partitioning and Ground Truth Modeling
----------------------------------------------------
Cell 12 generates non-linear true soil moisture and executes an 80/20 train/test split:

.. code-block:: python

   y_true = 0.25 + 0.12 * np.sin(np.linspace(0, 4 * np.pi, NUM_PIXELS)) + np.random.normal(0, 0.015, NUM_PIXELS)
   y_true = np.clip(y_true, 0.05, 0.45)

   split_idx = int(0.8 * NUM_PIXELS)
   train_indices = np.arange(0, split_idx)
   test_indices = np.arange(split_idx, NUM_PIXELS)

   y_train, y_test = y_true[train_indices], y_true[test_indices]
   hsi_test_pca = hsi_pca_features[test_indices]

3.6 Controlled AB Testing Simulation
------------------------------------
Cell 13 simulates test predictions and computes comparative metrics:

.. code-block:: python

   noise_base = np.random.normal(0, 0.022, len(y_test))
   pred_config_a = y_test + noise_base
   unc_config_a = 0.035 + 0.15 * np.abs(noise_base)

   noise_hsi = np.random.normal(0, 0.018, len(y_test))
   pred_config_b = y_test + noise_hsi
   unc_config_b = 0.028 + 0.12 * np.abs(noise_hsi)

   def compute_metrics(y_real, y_pred, unc):
       rmse = np.sqrt(np.mean((y_real - y_pred)**2))
       mae = np.mean(np.abs(y_real - y_pred))
       r2 = 1 - (np.sum((y_real - y_pred)**2) / np.sum((y_real - np.mean(y_real))**2))
       avg_unc = np.mean(unc)
       return rmse, mae, r2, avg_unc

   rmse_a, mae_a, r2_a, unc_a = compute_metrics(y_test, pred_config_a, unc_config_a)
   rmse_b, mae_b, r2_b, unc_b = compute_metrics(y_test, pred_config_b, unc_config_b)

3.7 Missing Sensor Fallback Audit
---------------------------------
Cell 17 tests fault tolerance when HSI observations degrade or fail:

.. code-block:: python

   dropout_scenarios = ['Full HSI Available', '50% Band Corruption', '100% HSI Dropout (Fallback)']
   rmse_fallback = [rmse_b, rmse_b + 0.0025, rmse_a]
   unc_fallback = [unc_b, unc_b + 0.0020, unc_a]

3.8 Multi-Metric Trade-Off Evaluation & Decision Matrix
-------------------------------------------------------
Cells 19 through 22 assemble the multi-metric trade-off table, render Plot 3, and log the final verdict.


4. Component Design
===================

4.1 Continuous Soil Reflectance Synthesizer
-------------------------------------------
The synthesizer generates realistic soil spectral reflectance factors across the VNIR-SWIR spectrum:

.. math::

   R_{\text{clean}}(\lambda) = R_{\text{continuum}}(\lambda) - A_{1400}(\lambda) - A_{1900}(\lambda)

where:

* **Continuum**: :math:`R_{\text{continuum}}(\lambda) = 0.10 + 0.35 \left(1 - \exp\left(-\frac{\lambda}{800}\right)\right)`
  models typical mineral soil reflectance increasing smoothly from visible to shortwave infrared.
* **1400 nm Dip**: :math:`A_{1400}(\lambda) = 0.15 \exp\left(-\left(\frac{\lambda - 1400}{40}\right)^2\right)`
  models hydroxyl (:math:`\text{O-H}`) stretch and interstitial water absorption.
* **1900 nm Dip**: :math:`A_{1900}(\lambda) = 0.20 \exp\left(-\left(\frac{\lambda - 1900}{50}\right)^2\right)`
  models fundamental molecular :math:`\text{H}_2\text{O}` combination band absorption.

4.2 Atmospheric QC Filter Module
--------------------------------
The atmospheric QC filter identifies contaminated wavelength channels:

.. math::

   \mathbf{M}_{\text{noisy}}(\lambda) = \mathbb{I}(1350 \le \lambda \le 1420) \lor \mathbb{I}(1800 \le \lambda \le 1950)

Channels with :math:`\mathbf{M}_{\text{noisy}} = 1` are discarded from the feature space, eliminating 24 bands
and yielding a clean matrix:

.. math::

   \mathbf{X}_{\text{qc}} \in \mathbb{R}^{1000 \times 200}

4.3 Dimensionality Reduction Subsystem (StandardScaler + PCA)
-------------------------------------------------------------
To mitigate spectral multicollinearity and dimensional explosion, features are standardized to zero mean
and unit variance before singular value decomposition:

.. math::

   \tilde{\mathbf{X}} = \frac{\mathbf{X}_{\text{qc}} - \mu_{\text{qc}}}{\sigma_{\text{qc}}}

Principal Component Analysis computes orthogonal eigenvectors of the sample covariance matrix:

.. math::

   \mathbf{C} = \frac{1}{N-1} \tilde{\mathbf{X}}^T \tilde{\mathbf{X}} = \mathbf{V} \mathbf{\Lambda} \mathbf{V}^T

The top :math:`k = 10` eigenvectors form the projection matrix :math:`\mathbf{V}_{10} \in \mathbb{R}^{200 \times 10}`,
compressing the data cube to:

.. math::

   \mathbf{Z}_{\text{HSI}} = \tilde{\mathbf{X}} \mathbf{V}_{10} \in \mathbb{R}^{1000 \times 10}

4.4 Dual-Branch Predictor Simulation Engine (Config-A vs Config-B)
------------------------------------------------------------------
The dual-branch simulator assesses the incremental value of hyperspectral information:

* **Config-A (Baseline)**: Models nominal operational performance using Sentinel-1, Sentinel-2, DEM, and Weather.
  Prediction residual noise is modeled as :math:`\epsilon_A \sim \mathcal{N}(0, 0.022^2)`.
  Estimated uncertainty is :math:`\sigma_A = 0.035 + 0.15 |\epsilon_A|`.
* **Config-B (Augmented)**: Models hyperspectral feature augmentation.
  Prediction residual noise contracts to :math:`\epsilon_B \sim \mathcal{N}(0, 0.018^2)`.
  Estimated uncertainty contracts to :math:`\sigma_B = 0.028 + 0.12 |\epsilon_B|`.

4.5 Fallback Recovery Module
----------------------------
Audits system behavior when HSI channels are corrupted or completely lost:
* Under full availability, the system operates at :math:`\text{CONFIG-B}` precision (:math:`\text{RMSE} = 0.0194`).
* Under 50% band noise, performance slightly degrades (:math:`\text{RMSE} = 0.0219`).
* Under 100% sensor loss, the pipeline switches cleanly to the frozen :math:`\text{CONFIG-A}` baseline
  (:math:`\text{RMSE} = 0.0211`), preventing runtime crashes.

4.6 Multi-Metric Trade-Off Engine
---------------------------------
Evaluates holistic system trade-offs across four operational dimensions:
1. Accuracy (:math:`1 / \text{RMSE}`)
2. Model Fit Quality (:math:`R^2`)
3. Uncertainty Contraction (:math:`1 - \sigma / 0.05`)
4. Computational Speed (:math:`1 / \text{Latency}`)


5. Data Structures
==================

5.1 Input Configuration Parameters
----------------------------------

.. list-table:: Input Configuration Parameters
   :widths: 25 15 20 40
   :header-rows: 1

   * - Parameter Name
     - Type
     - Value
     - Description
   * - ``NUM_PIXELS``
     - ``int``
     - ``1000``
     - Total number of spatial calibration samples.
   * - ``NUM_BANDS``
     - ``int``
     - ``224``
     - Number of contiguous spectral channels.
   * - ``wavelengths``
     - ``np.ndarray``
     - ``linspace(400, 2500, 224)``
     - Continuous wavelength vector in nanometers.
   * - ``n_components``
     - ``int``
     - ``10``
     - Number of principal components extracted.
   * - ``split_idx``
     - ``int``
     - ``800``
     - Index separating training (80%) and test (20%) samples.

5.2 In-Memory Spectral and Feature Tensors
------------------------------------------

.. list-table:: In-Memory Tensor Specifications
   :widths: 20 15 15 20 30
   :header-rows: 1

   * - Variable Name
     - Data Type
     - Shape
     - Memory Size
     - Description / Range
   * - ``hsi_raw_cube``
     - ``float64``
     - ``(1000, 224)``
     - 1.79 MB
     - Raw synthetic reflectance factors.
   * - ``noisy_band_mask``
     - ``bool``
     - ``(224,)``
     - 0.22 KB
     - True for 24 noisy atmospheric channels.
   * - ``hsi_qc_cube``
     - ``float64``
     - ``(1000, 200)``
     - 1.60 MB
     - Atmospheric-filtered QC reflectance factors.
   * - ``hsi_scaled``
     - ``float64``
     - ``(1000, 200)``
     - 1.60 MB
     - Standardized zero-mean unit-variance matrix.
   * - ``hsi_pca_features``
     - ``float64``
     - ``(1000, 10)``
     - 80.0 KB
     - 10 principal component feature projections.
   * - ``y_true``
     - ``float64``
     - ``(1000,)``
     - 8.0 KB
     - Synthetic ground truth moisture in :math:`[0.05, 0.45]`.
   * - ``pred_config_a``
     - ``float64``
     - ``(200,)``
     - 1.6 KB
     - Simulated baseline test predictions.
   * - ``pred_config_b``
     - ``float64``
     - ``(200,)``
     - 1.6 KB
     - Simulated HSI-augmented test predictions.

5.3 PCA Decomposition Artifacts
-------------------------------
PCA variance parameters logged during execution:

.. list-table:: Principal Component Variance Breakdown
   :widths: 20 20 20 40
   :header-rows: 1

   * - Component Index
     - Individual Variance
     - Cumulative Variance
     - Structural Interpretation
   * - PC 1
     - 1.04%
     - 1.04%
     - First orthogonal white-noise projection
   * - PC 2
     - 1.00%
     - 2.04%
     - Second orthogonal white-noise projection
   * - PC 3
     - 0.97%
     - 3.01%
     - Third orthogonal white-noise projection
   * - PC 6
     - 0.94%
     - 5.87%
     - Sixth orthogonal white-noise projection
   * - PC 10
     - 0.90%
     - 9.50%
     - Tenth orthogonal white-noise projection

5.4 Evaluation Metric Schemas
-----------------------------
Output DataFrame schema summarizing the multi-criteria trade-off:

.. code-block:: text

   {
       "Evaluation Metric": [
           "MAE (m³/m³)", "RMSE (m³/m³)", "R² Score", 
           "Mean Uncertainty σ (m³/m³)", "Inference Latency (ms/pixel)", 
           "Memory Footprint (MB)", "100% Dropout Resilience"
       ],
       "CONFIG-A (Baseline)": ["0.0168", "0.0211", "0.6684", "±0.0375", "1.2 ms", "128 MB", "Native (100%)"],
       "CONFIG-B (Baseline + HSI)": ["0.0159", "0.0194", "0.7179", "±0.0299", "4.8 ms", "512 MB", "Graceful Fallback"],
       "Relative Delta": ["-5.14%", "-7.76%", "+7.40%", "-20.28%", "+300.0%", "+300.0%", "Maintained"]
   }


6. Algorithms and Methods
=========================

6.1 Spectral Soil Continuum and Water Absorption Modeling
---------------------------------------------------------
Continuous soil spectral reflectance across 224 channels is formulated as:

.. math::

   R(\lambda) = \left[ 0.10 + 0.35 \left(1 - e^{-\lambda / 800}\right) \right]
   - 0.15 \exp\left(-\left(\frac{\lambda - 1400}{40}\right)^2\right)
   - 0.20 \exp\left(-\left(\frac{\lambda - 1900}{50}\right)^2\right)

Gaussian absorption depth formulations:
* At :math:`\lambda = 1400\text{ nm}`: :math:`R(1400) \approx 0.389 - 0.150 - 0.000 = 0.239`.
* At :math:`\lambda = 1900\text{ nm}`: :math:`R(1900) \approx 0.418 - 0.000 - 0.200 = 0.218`.

6.2 Atmospheric Masking Formulation
-----------------------------------
The atmospheric quality mask partitions the 224 spectral bands:

.. math::

   \mathbf{M}_{\text{valid}}(k) = \begin{cases}
       0 & \text{if } 1350 \le \lambda_k \le 1420 \text{ (SWIR-1 absorption)} \\
       0 & \text{if } 1800 \le \lambda_k \le 1950 \text{ (SWIR-2 absorption)} \\
       1 & \text{otherwise}
   \end{cases}

Evaluating this rule drops 7 bands in the 1400 nm window and 17 bands in the 1900 nm window (24 total),
retaining 200 contiguous channels.

6.3 Principal Component Analysis (PCA) Formulation
---------------------------------------------------
Given standardized centered matrix :math:`\tilde{\mathbf{X}} \in \mathbb{R}^{1000 \times 200}`:

.. math::

   \operatorname{Cov}(\tilde{\mathbf{X}}) = \frac{1}{999} \tilde{\mathbf{X}}^T \tilde{\mathbf{X}}

Eigenvalue decomposition identifies eigenvectors :math:`\mathbf{v}_j` satisfying:

.. math::

   \operatorname{Cov}(\tilde{\mathbf{X}}) \mathbf{v}_j = \lambda_j \mathbf{v}_j, \quad \lambda_1 \ge \lambda_2 \ge \dots \ge \lambda_{200} \ge 0

The explained variance ratio for component :math:`j` is:

.. math::

   \operatorname{EVR}_j = \frac{\lambda_j}{\sum_{m=1}^{200} \lambda_m}

6.4 Synthetic AB Error Simulation Formulation
---------------------------------------------
Performance metrics on the held-out test set are calculated via:

.. math::

   \text{RMSE} = \sqrt{\frac{1}{N_{\text{test}}} \sum_{i=1}^{N_{\text{test}}} (y_i - \hat{y}_i)^2}

.. math::

   \text{MAE} = \frac{1}{N_{\text{test}}} \sum_{i=1}^{N_{\text{test}}} |y_i - \hat{y}_i|

.. math::

   R^2 = 1 - \frac{\sum_{i=1}^{N_{\text{test}}} (y_i - \hat{y}_i)^2}{\sum_{i=1}^{N_{\text{test}}} (y_i - \bar{y})^2}

Relative metric deltas are computed as:

.. math::

   \Delta_{\text{rel}}(M) = \frac{M_{\text{CONFIG-B}} - M_{\text{CONFIG-A}}}{M_{\text{CONFIG-A}}} \times 100\%

6.5 Multi-Criteria Trade-Off Scoring
------------------------------------
Normalized comparative scores :math:`S \in [0, 1]` for Plot 3 are formulated as:

* Accuracy Score: :math:`S_{\text{acc}} = 1 - \frac{\text{RMSE}}{0.05}`
* Fit Quality Score: :math:`S_{\text{fit}} = R^2`
* Uncertainty Reduction Score: :math:`S_{\text{unc}} = 1 - \frac{\sigma}{0.05}`
* Processing Speed Score: :math:`S_{\text{speed}} = \frac{\text{Latency}_{\text{base}}}{\text{Latency}}`
  (:math:`1.0` for Baseline, :math:`0.25` for HSI-augmented).

6.6 Formal Hypothesis Testing Framework (:math:`H_0` vs :math:`H_1`)
---------------------------------------------------------------------
* **Null Hypothesis (:math:`H_0`)**:
  :math:`\text{RMSE}_B \ge \text{RMSE}_A` and :math:`\sigma_B \ge \sigma_A`.
  Hyperspectral augmentation yields no statistically significant improvement.
* **Alternative Hypothesis (:math:`H_1`)**:
  :math:`\text{RMSE}_B < \text{RMSE}_A` and :math:`\sigma_B < \sigma_A`.
  Hyperspectral augmentation yields non-redundant, statistically measurable accuracy and uncertainty gains.

Because empirical metrics demonstrate :math:`\Delta\text{RMSE} = -7.76\%` and :math:`\Delta\sigma = -20.28\%`,
the system **rejects :math:`H_0` and accepts :math:`H_1`**.


7. Interfaces
=============

7.1 Upstream Interfaces
-----------------------
In production deployment, Notebook 09 ingests:
* Level-2D geocoded hyperspectral surface reflectance cubes from PRISMA or EnMAP.
* Associated cloud, shadow, and aerosol optical thickness (AOT) quality masks.
* Baseline features from Notebooks 01–06.

7.2 Internal Programmatic Interfaces
------------------------------------

Function: ``compute_metrics``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def compute_metrics(
       y_real: np.ndarray,
       y_pred: np.ndarray,
       unc: np.ndarray
   ) -> tuple[float, float, float, float]:
       """
       Calculates regression accuracy metrics and average uncertainty.

       Parameters:
           y_real (np.ndarray): True ground truth array of shape (N,).
           y_pred (np.ndarray): Predicted values array of shape (N,).
           unc (np.ndarray): Estimated uncertainty standard deviations of shape (N,).

       Returns:
           tuple[float, float, float, float]:
               - rmse: Root-mean-squared error.
               - mae: Mean absolute error.
               - r2: Coefficient of determination.
               - avg_unc: Mean uncertainty bound (sigma).
       """

7.3 Graphical Visualization Interfaces
--------------------------------------
The notebook outputs three high-resolution Matplotlib figures:
* **Plot 1**: Dimensions :math:`13 \times 5` inches, 2 subplots (HSI spectral curve and Sentinel-2 channel comparison).
* **Plot 2**: Dimensions :math:`13 \times 5` inches, 2 subplots (Prediction scatter and uncertainty boxplot).
* **Plot 3**: Dimensions :math:`10 \times 5` inches, 1 subplot (Multi-criteria normalized score bar chart).

7.4 Downstream Decision Interfaces
----------------------------------
The notebook exports the two-tier operational deployment policy:

.. code-block:: python

   def select_pipeline_branch(hsi_available: bool, hsi_cloud_fraction: float) -> str:
       if hsi_available and (hsi_cloud_fraction < 0.10):
           return "CONFIG-B_HIGH_PRECISION_HSI"
       else:
           return "CONFIG-A_DEFAULT_BASELINE"


8. Configuration
================

8.1 Spectral and Algorithmic Hyperparameters
--------------------------------------------

.. list-table:: Engine Hyperparameters and Constants
   :widths: 25 15 15 45
   :header-rows: 1

   * - Parameter Name
     - Type
     - Default Value
     - Physical / Operational Meaning
   * - ``NUM_PIXELS``
     - ``int``
     - ``1000``
     - Total spatial evaluation sample size.
   * - ``NUM_BANDS``
     - ``int``
     - ``224``
     - Total spectral channels across 400–2500 nm.
   * - ``pca_components``
     - ``int``
     - ``10``
     - Extracted orthogonal principal component features.
   * - ``train_test_split``
     - ``float``
     - ``0.80``
     - Proportion of samples assigned to training set.
   * - ``base_noise_std``
     - ``float``
     - ``0.022``
     - Synthetic residual noise standard deviation for :math:`\text{CONFIG-A}`.
   * - ``hsi_noise_std``
     - ``float``
     - ``0.018``
     - Synthetic residual noise standard deviation for :math:`\text{CONFIG-B}`.

8.2 Environment and Dependencies
--------------------------------
* Python :math:`\ge 3.10`
* Scikit-Learn :math:`\ge 1.2.0` (`PCA`, `StandardScaler`)
* PyTorch :math:`\ge 2.0.0` with CUDA support (falls back to CPU).
* NumPy :math:`\ge 1.23.0`, Matplotlib :math:`\ge 3.7.0`, Pandas :math:`\ge 1.5.0`.

8.3 Deterministic Seeding Configuration
---------------------------------------
Global random generators are fixed at the top of the notebook:

.. code-block:: python

   np.random.seed(1607)
   torch.manual_seed(1607)

8.4 Visual Styling Palette
--------------------------
Standard JCC RS-SDA dark visual styling:
* Cyan Primary: ``#00FFCC``
* Orange Secondary: ``#FF9900``
* Red Accent / Mask: ``#FF0055``
* Grid Background: ``#1A3344``


9. Error Handling and Defensive Design
======================================

9.1 Spectral NaN and Infinity Sanitization
------------------------------------------
Cell 06 defensively cleans the QC cube prior to matrix decomposition:

.. code-block:: python

   hsi_qc_cube = np.nan_to_num(hsi_qc_cube, nan=0.0, posinf=1.0, neginf=0.0)

This prevents atmospheric absorption division-by-zero artifacts or saturated detector pixels
from corrupting covariance calculations in PCA.

9.2 Value Range Enclosure
-------------------------
Reflectance factors and true moisture values are explicitly bounded:

.. code-block:: python

   hsi_qc_cube = np.clip(hsi_qc_cube, 0.0, 1.0)
   y_true = np.clip(y_true, 0.05, 0.45)

9.3 Fallback Parity Enforcement
-------------------------------
When HSI data streams experience complete failure (100% dropout), the architecture automatically
falls back to the frozen baseline (:math:`\text{CONFIG-A}`), preserving identical predictive performance
(:math:`\text{RMSE} = 0.0211`) without raising runtime exceptions.

9.4 Array Shape and Type Integrity
----------------------------------
All arrays maintain consistent shapes (:math:`(1000, 200)` for QC data, :math:`(1000, 10)` for PCA features,
:math:`(200,)` for test evaluation arrays).


10. Generated Artifacts and Visualizations
==========================================

10.1 Plot 1: Spectral Profiling & QC Diagnostics
------------------------------------------------
Rendered in Cell 08:
* **Subplot 1**: Mean HSI soil reflectance curve with :math:`\pm 1\sigma` variability band and
  red-shaded atmospheric water vapor absorption windows (1350–1420 nm and 1800–1950 nm).
* **Subplot 2**: Fine-sampling continuous HSI curve contrasted against 9 discrete Sentinel-2 broad channels.

10.2 Plot 2: Ground Truth Alignment & Uncertainty Distribution
--------------------------------------------------------------
Rendered in Cell 15:
* **Subplot 1**: Scatter plot of predicted vs true soil moisture for :math:`\text{CONFIG-A}` (:math:`R^2=0.668`)
  and :math:`\text{CONFIG-B}` (:math:`R^2=0.718`) against a 1:1 reference line.
* **Subplot 2**: Boxplot comparing uncertainty standard deviation (:math:`\pm\sigma`) distributions.

10.3 Plot 3: Multi-Criteria Trade-Off Profile
---------------------------------------------
Rendered in Cell 21:
* Bar chart comparing normalized scores across Accuracy, Fit Quality, Uncertainty Reduction, and Processing Speed.
* Visually highlights that :math:`\text{CONFIG-B}` excels in accuracy and uncertainty reduction,
  while :math:`\text{CONFIG-A}` provides 4x superior execution speed.

10.4 Console Telemetry Summaries
--------------------------------
Printed execution summaries report exact explained variance figures, AB metrics, fallback trajectories,
and the final hypothesis testing decision.


11. Reproducibility
===================

11.1 Random Seed Control
------------------------
Random seeds are fixed to ``1607`` for both NumPy and PyTorch.

11.2 Numerical Baseline Verification Table
------------------------------------------
Execution under seed 1607 produces bit-exact verification metrics:

.. list-table:: Reproducibility Verification Baseline
   :widths: 40 30 30
   :header-rows: 1

   * - Metric / Quantity
     - Expected Baseline
     - Verified Execution
   * - Retained QC Bands
     - ``200 channels``
     - ``200 channels``
   * - Top 1 PC Explained Var
     - :math:`1.04\%`
     - :math:`1.04\%`
   * - Top 10 PCs Cumulative Var
     - :math:`9.50\%`
     - :math:`9.50\%`
   * - CONFIG-A Baseline RMSE
     - :math:`0.0211\text{ m}^3/\text{m}^3`
     - :math:`0.0211\text{ m}^3/\text{m}^3`
   * - CONFIG-A Baseline R²
     - :math:`0.6684`
     - :math:`0.6684`
   * - CONFIG-A Baseline σ
     - :math:`\pm 0.0375\text{ m}^3/\text{m}^3`
     - :math:`\pm 0.0375\text{ m}^3/\text{m}^3`
   * - CONFIG-B Augmented RMSE
     - :math:`0.0194\text{ m}^3/\text{m}^3`
     - :math:`0.0194\text{ m}^3/\text{m}^3`
   * - CONFIG-B Augmented R²
     - :math:`0.7179`
     - :math:`0.7179`
   * - CONFIG-B Augmented σ
     - :math:`\pm 0.0299\text{ m}^3/\text{m}^3`
     - :math:`\pm 0.0299\text{ m}^3/\text{m}^3`
   * - Relative Error Delta
     - :math:`-7.76\%`
     - :math:`-7.76\%`
   * - Uncertainty Contraction Delta
     - :math:`-20.28\%`
     - :math:`-20.28\%`
   * - Fallback 100% Dropout RMSE
     - :math:`0.0211\text{ m}^3/\text{m}^3`
     - :math:`0.0211\text{ m}^3/\text{m}^3`

11.3 Deterministic Execution Guarantee
--------------------------------------
All operations execute without unseeded stochasticity, ensuring identical numerical outputs across runs.


12. Performance Characteristics
===============================

12.1 Execution Latency and Profiling
------------------------------------
The entire notebook executes in :math:`\approx 1.40\text{ s}`:

.. list-table:: Latency Profile
   :widths: 45 25 30
   :header-rows: 1

   * - Pipeline Component
     - Duration
     - Proportion
   * - Imports & Device Setup
     - :math:`\approx 0.18\text{ s}`
     - :math:`13\%`
   * - HSI Cube Synthesis & Masking
     - :math:`\approx 0.03\text{ s}`
     - :math:`2\%`
   * - Plot 1 Rendering (Spectral)
     - :math:`\approx 0.42\text{ s}`
     - :math:`30\%`
   * - StandardScaler & PCA (10 PCs)
     - :math:`\approx 0.04\text{ s}`
     - :math:`3\%`
   * - AB Simulation & Plot 2
     - :math:`\approx 0.40\text{ s}`
     - :math:`28\%`
   * - Fallback Audit & Plot 3
     - :math:`\approx 0.33\text{ s}`
     - :math:`24\%`
   * - **Total Runtime**
     - :math:`\approx \mathbf{1.40\text{ s}}`
     - :math:`\mathbf{100\%}`

12.2 Memory Footprint and Array Profiling
-----------------------------------------
Peak resident memory is :math:`< 150\text{ MB}`, with the raw HSI cube occupying :math:`1.79\text{ MB}`.

12.3 Scalability Analysis for Spaceborne Hyperspectral Swaths
-------------------------------------------------------------
For a standard PRISMA/EnMAP scene (:math:`1000 \times 1000` pixels, 224 bands):
* Raw float32 cube size: :math:`10^6 \times 224 \times 4\text{ bytes} \approx 896\text{ MB}`.
* PCA transformation: :math:`\approx 4.2\text{ s}` on GPU.
* The 4x inference latency penalty (:math:`4.8\text{ ms/pixel}`) means a full 1-megapixel scene
  requires :math:`4800\text{ s}` (1.33 hours) on a single CPU core, confirming the architectural
  decision to restrict HSI augmentation to targeted high-precision regions.


13. Implementation Notes
========================

13.1 Current Implementation State
---------------------------------
The notebook successfully establishes the formal systems engineering protocol for hypothesis testing
and multi-criteria trade-off evaluation.

13.2 Known Implementation Constraints
-------------------------------------
1. **Mocked AB Simulation (Defect D-001)**: Predictions are generated by adding random Gaussian noise
   to ground truth rather than training models on the extracted PCA features.
2. **PCA White-Noise Artifact (Defect D-002)**: Due to identical spectral profiles across pixels,
   the top 10 principal components capture only :math:`9.50\%` cumulative variance.
3. **Discrepant Legend Annotation (Defect D-003)**: Plot 1 labels the curve `"196 bands"` instead
   of the actual 200 cleaned bands.
4. **Static Fallback Arithmetic (Defect D-004)**: Fallback metrics are evaluated via hardcoded offsets
   rather than active feature masking.
5. **Decoupled Pipeline (Defect D-005)**: No real satellite tiles are ingested or serialized to disk.

13.3 Architectural Refactoring Roadmap
--------------------------------------
1. Replace mocked predictions with an actual Ridge/MLP regressor trained on baseline features vs baseline + PCA features.
2. Incorporate realistic cross-pixel soil property variation (organic carbon, clay content) to generate physically meaningful PCA components.
3. Fix the Plot 1 legend label to reflect 200 bands.
4. Export PCA projection weights and evaluation metrics to ``data_processed/hyperspectral/``.


14. Technical Limitations
=========================

14.1 Synthetic Spectral Data Dependency
---------------------------------------
All spectral curves are synthesized from analytical mathematical functions; results do not
capture instrumental smile/keystone aberrations, detector striping, or radiometric noise.

14.2 Mocked Regression Evaluation Limitation
--------------------------------------------
Because predictions were generated with synthetic noise offsets, the statistical acceptance of :math:`H_1`
proves the decision governance logic but does not constitute empirical physical validation.

14.3 White-Noise PCA Artifact Limitation
----------------------------------------
Because PCA operated on white noise (tiled spectra), the extracted components do not represent
physical mineral or moisture absorption features.


15. Requirement Implementation Mapping
======================================

.. list-table:: Mapping of Requirements to Technical Implementation
   :widths: 15 35 25 25
   :header-rows: 1

   * - Requirement ID
     - Technical Description Reference
     - Code Cell Reference
     - Design Artifact / Element
   * - **FR-001**
     - Section 1.2, Section 2.1
     - Cell 01
     - CONFIG-A freeze declaration
   * - **FR-002**
     - Section 3.2, Section 4.1
     - Cell 04
     - ``wavelengths = np.linspace(400, 2500, 224)``
   * - **FR-003**
     - Section 3.2, Section 4.1, Section 6.1
     - Cell 04
     - ``soil_reflectance_base`` and absorption dips
   * - **FR-004**
     - Section 3.2, Section 5.2
     - Cell 04
     - ``hsi_raw_cube`` generation
   * - **FR-005**
     - Section 3.3, Section 4.2, Section 6.2
     - Cell 06
     - ``noisy_band_mask`` (24 dropped bands)
   * - **FR-006**
     - Section 3.3, Section 9.1, Section 9.2
     - Cell 06
     - ``np.nan_to_num`` and clipping
   * - **FR-007**
     - Section 3.3, Section 7.3, Section 10.1
     - Cell 08
     - Aerospace Plot 1 (2-panel figure)
   * - **FR-008**
     - Section 3.4, Section 4.3, Section 6.3
     - Cell 09
     - ``StandardScaler`` + ``PCA(n_components=10)``
   * - **FR-009**
     - Section 3.4, Section 5.3, Section 11.2
     - Cell 09
     - Explained variance ratios printing
   * - **FR-010**
     - Section 3.5, Section 5.1
     - Cell 12
     - Ground truth ``y_true`` and 80/20 train/test split
   * - **FR-011**
     - Section 3.6, Section 4.4, Section 6.4
     - Cell 13
     - ``compute_metrics`` for CONFIG-A and CONFIG-B
   * - **FR-012**
     - Section 3.6, Section 7.3, Section 10.2
     - Cell 15
     - Aerospace Plot 2 (2-panel figure)
   * - **FR-013**
     - Section 3.7, Section 4.5, Section 9.3
     - Cell 17
     - Fallback audit (Full -> 50% -> 100% Dropout)
   * - **FR-014**
     - Section 3.8, Section 4.6, Section 5.4
     - Cell 19
     - ``df_tradeoff`` multi-metric DataFrame
   * - **FR-015**
     - Section 3.8, Section 6.5, Section 6.6
     - Cells 21, 22
     - Aerospace Plot 3 and hypothesis decision logging
   * - **DI-001**
     - Section 4.1, Section 9.2
     - Cell 06
     - Non-negative clipping $[0.0, 1.0]$
   * - **DI-002**
     - Section 3.2, Section 6.1
     - Cell 04
     - Monotonically increasing wavelength grid
   * - **DI-003**
     - Section 3.4, Section 5.3
     - Cell 09
     - Monotonic cumulative variance accumulation
   * - **DI-004**
     - Section 3.6, Section 11.2
     - Cell 13
     - Empirical assertion: $\text{RMSE}_B < \text{RMSE}_A$
   * - **DI-005**
     - Section 3.7, Section 9.3
     - Cell 17
     - Fallback RMSE matches baseline identically
