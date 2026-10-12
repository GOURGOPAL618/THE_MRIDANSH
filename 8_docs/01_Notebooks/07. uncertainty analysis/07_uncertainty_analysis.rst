=================================================================================
THE MRIDANSH (AETHER-MRID1607X) - Notebook 07: Uncertainty Analysis & Calibration
=================================================================================

:Project: THE MRIDANSH - Unified Soil State Estimation System
:Engine: AETHER-MRID1607X (Multi-Domain Soil Intelligence Engine)
:Notebook: ``07-uncertainty-analysis.ipynb``
:Sprint phase: Days 3-4 of the Scientific Audit & Validation Mission
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
The primary technical objective of ``07-uncertainty-analysis.ipynb`` is to design, implement,
and rigorously validate a multi-source uncertainty quantification (UQ) and statistical confidence
calibration engine. The engine decomposes volumetric soil moisture prediction errors into four
orthogonal physical variance sources, synthesizes total composite uncertainty via quadratic
variance addition, transforms absolute spread into normalized operational confidence scores,
and audits statistical coverage reliability against Gaussian confidence intervals.

1.2 System Context
------------------
Within the **THE MRIDANSH** (*AETHER-MRID1607X*) computational framework, uncertainty analysis
acts as the formal statistical gating interface between geophysical estimation and operational
geotechnical decision-making:

* **Upstream Data Ingestion**: Conceptually receives prior state covariances (:math:`\mathbf{P}^f`)
  from ConvLSTM temporal models (Notebook 04), physics disagreement residuals from Richards PDE
  PINNs (Notebook 05), and assimilated posterior error covariances (:math:`\mathbf{P}^a`) from the
  Ensemble Kalman Filter (Notebook 06).
* **Core Execution**: Synthesizes a :math:`50 \times 50` spatial lattice, generates individual
  variance components (:math:`\sigma_{\text{ens}}, \sigma_{\text{sensor}}, \sigma_{\text{gap}}, \sigma_{\text{model}}`),
  computes root-sum-square total standard deviation (:math:`\sigma_{\text{total}}`), projects uncertainty
  into bounded confidence indices (:math:`C \in [0.0, 1.0]`), evaluates :math:`1\sigma / 2\sigma / 3\sigma`
  empirical coverage over :math:`N = 2500` spatial samples, and executes a 14-day persistent sensor
  blackout stress test.
* **Downstream Integration**: Emits spatial confidence fields and total uncertainty bounds
  (:math:`\hat{\theta} \pm \sigma_{\text{total}}`) to Notebook 08 (*Robustness & Failure Analysis*)
  and Notebook 10 (*Ablation Study*) to govern threshold gating in landslide slope safety
  factor calculations.

1.3 Design Boundary
-------------------
The architectural boundary of Notebook 07 is demarcated as follows:

* **In Boundary**:
  - Generation of four independent variance contributor fields on a :math:`50 \times 50` grid.
  - Quadratic variance addition: :math:`\sigma_{\text{total}} = \sqrt{\sum \sigma_i^2}`.
  - Exponential confidence transformation with tuneable decay rate (:math:`\gamma = 1.5`) and
    physical saturation threshold (:math:`\sigma_{\text{max}} = 0.10\text{ m}^3/\text{m}^3`).
  - Empirical reliability coverage auditing across nominal Gaussian intervals (:math:`68.27\%, 95.45\%, 99.73\%`).
  - Generation of spread-skill scatter diagrams and reliability calibration curves.
  - Stress testing under simulated severe cloud obstruction and observation revisit delay.
* **Out of Boundary**:
  - Spatially correlated non-diagonal error covariance modeling (Markov Random Fields or spatial kriging).
  - Bayesian neural network Monte Carlo dropout sampling during inference.
  - Real-time ingestion of live satellite Scene Classification Layers (SCL).
  - Geotechnical slope stability limit-equilibrium equations (deferred to Notebook 08).

1.4 Relationship to Requirements
--------------------------------
This technical description specifies the mathematical foundations, software architecture, data structures,
and execution workflows implementing the functional requirements (`FR-001` through `FR-014`), data integrity
rules (`DI-001` through `DI-005`), and quality standards defined in the companion Requirements and
Verification baseline (``07_uncertainty_analysis_REQUIREMENTS.md``).


2. Architecture
===============

2.1 Notebook Architecture
-------------------------
The software architecture of Notebook 07 follows a modular 4-tier pipeline designed for vectorised
array processing in NumPy and PyTorch:

.. code-block:: text

   +---------------------------------------------------------------------------------+
   |                                TIER 1: GENERATION                               |
   |  Spatial Grid Setup (50x50)  -->  Synthetic Variance Synthesizers               |
   |  [sigma_ens (U)]   [sigma_sensor (Cloud/Noise)]   [sigma_gap (Exp)]   [sigma_model] |
   +---------------------------------------------------------------------------------+
                                           |
                                           v
   +---------------------------------------------------------------------------------+
   |                                 TIER 2: FUSION                                  |
   |  compute_composite_uncertainty(sigma_ens, sigma_sensor, sigma_gap, sigma_model)  |
   |             sigma_total = sqrt(sum(sigma_i^2))                                   |
   |             C = clip(exp(-gamma * sigma_total / sigma_max), 0, 1)                |
   +---------------------------------------------------------------------------------+
                                           |
                                           v
   +---------------------------------------------------------------------------------+
   |                              TIER 3: CALIBRATION                                |
   |  Coverage Verification (1-sigma, 2-sigma, 3-sigma)                              |
   |  Spread-Skill Diagnostics  -->  Reliability Curves (10% - 99%)                  |
   +---------------------------------------------------------------------------------+
                                           |
                                           v
   +---------------------------------------------------------------------------------+
   |                            TIER 4: STRESS AUDITING                              |
   |  14-Day Cloud Outage Simulation (Delta_t = 14, sigma_sensor = 0.08)              |
   |  Degradation Telemetry  -->  Aerospace Figure Rendering                         |
   +---------------------------------------------------------------------------------+

2.2 Processing Pipeline
-----------------------
Execution proceeds strictly through sequential pipeline stages:

1. **Deterministic Seeding**: Sets global random seeds for NumPy and PyTorch to ``1607``.
2. **Spatial Grid Discretization**: Defines a 2D evaluation lattice of shape :math:`(50, 50)`.
3. **Component Synthesization**: Computes individual variance tensors representing physical error mechanisms.
4. **Quadratic Variance Fusion**: Evaluates the composite error field and exponential confidence surface.
5. **Point Telemetry Inspection**: Extracts diagnostic predictions and uncertainty bounds at pixel :math:`(25, 25)`.
6. **Aerospace Plot 1 Generation**: Renders a 6-panel visual decomposition of the uncertainty surface.
7. **Statistical Coverage Verification**: Assesses the frequency of residual containment within error bounds.
8. **Aerospace Plot 2 Generation**: Produces spread-skill scatter and calibration curve plots.
9. **Outage Scenario Stress Test**: Injects persistent revisit latency and high sensor noise to assess failure resilience.

2.3 Component Relationships
---------------------------
The components interact through direct array passing without intermediate disk serialization:

* **Grid Domain Controller**: Provides the spatial shape tuple ``GRID_SIZE = (50, 50)`` to all generators.
* **Variance Synthesizers**: Populate four distinct 2D float arrays conforming to the grid shape.
* **Fusion Function**: Ingests all four arrays and scalar hyperparameters, returning fused uncertainty and confidence.
* **Diagnostic Plotters**: Ingest the generated arrays and render high-resolution Matplotlib figures.
* **Stress Harness**: Overwrites sensor and gap arrays with extreme values and re-evaluates the fusion function.

2.4 Data Flow
-------------
The data flow represents a purely forward directed acyclic graph (DAG):

.. code-block:: text

   Seed (1607) ---> GRID_SIZE (50, 50)
                           |
       +-------------------+-------------------+
       |                   |                   |                   |
       v                   v                   v                   v
   sigma_ens          sigma_sensor         sigma_gap          sigma_model
   [50, 50]             [50, 50]            [50, 50]            [50, 50]
       |                   |                   |                   |
       +-------------------+-------------------+-------------------+
                               |
                               v
               compute_composite_uncertainty()
                               |
                     +---------+---------+
                     |                   |
                     v                   v
                sigma_total          confidence
                  [50, 50]            [50, 50]
                     |                   |
                     +---------+---------+
                               |
             +-----------------+-----------------+
             |                                   |
             v                                   v
   Aerospace Plot 1 (6-Panel)        Coverage & Reliability (Plot 2)
                                                 |
                                                 v
                                     Stress Test (14-Day Outage)


3. Execution Flow
=================

3.1 Initialization and Seed Locking
-----------------------------------
Execution begins in Cell 00 and Cell 01 by importing scientific dependencies and establishing
numerical reproducibility:

.. code-block:: python

   import numpy as np
   import matplotlib.pyplot as plt
   import matplotlib.gridspec as gridspec
   import scipy.stats as stats
   import torch

   np.random.seed(1607)
   torch.manual_seed(1607)

3.2 Spatial Grid Instantiation
------------------------------
Cell 02 establishes the spatial domain dimension:

.. code-block:: python

   GRID_SIZE = (50, 50)

This creates a 2D discrete manifold of :math:`N = 2500` independent pixels.

3.3 Multi-Source Variance Generation
------------------------------------
Cell 03 instantiates the four orthogonal uncertainty fields:

1. **Ensemble Spread (:math:`\sigma_{\text{ens}}`)**:
   Models the dispersion among ensemble members resulting from the EnKF assimilation update:
   
   .. code-block:: python

      sigma_ens = np.random.uniform(0.01, 0.04, GRID_SIZE)

2. **Sensor Quality & Cloud Mask (:math:`\sigma_{\text{sensor}}`)**:
   Models baseline radiometer noise, cloud contamination (25% probability), and SAR speckle:
   
   .. code-block:: python

      cloud_mask = np.random.binomial(1, 0.25, GRID_SIZE)
      sigma_sensor = 0.01 + 0.035 * cloud_mask + np.abs(np.random.normal(0, 0.015, GRID_SIZE))

3. **Temporal Gap Penalty (:math:`\sigma_{\text{gap}}`)**:
   Models satellite revisit latency :math:`\Delta t \in [0, 10]` days with exponential uncertainty growth:
   
   .. code-block:: python

      time_since_obs = np.random.uniform(0, 10, GRID_SIZE)
      sigma_gap = 0.005 * np.exp(time_since_obs / 4.0)

4. **Model Physics Disagreement (:math:`\sigma_{\text{model}}`)**:
   Models epistemic structural divergence between the neural ConvLSTM and the Richards PDE:
   
   .. code-block:: python

      sigma_model = np.abs(np.random.normal(0.015, 0.008, GRID_SIZE))

3.4 Composite Uncertainty Evaluation
------------------------------------
Cell 04 declares the composite uncertainty calculation engine, and Cell 05 executes it:

.. code-block:: python

   def compute_composite_uncertainty(sigma_ens, sigma_sensor, sigma_gap, sigma_model, gamma=1.5):
       sigma_total = np.sqrt(sigma_ens**2 + sigma_sensor**2 + sigma_gap**2 + sigma_model**2)
       sigma_max = 0.10
       confidence_score = np.exp(-gamma * (sigma_total / sigma_max))
       confidence_score = np.clip(confidence_score, 0.0, 1.0)
       return sigma_total, confidence_score

   sigma_total, confidence_score = compute_composite_uncertainty(
       sigma_ens, sigma_sensor, sigma_gap, sigma_model
   )

3.5 Confidence Score Transformation
-----------------------------------
The confidence score maps unbounded root-sum-square errors into an operational unit interval :math:`[0.0, 1.0]`.
With :math:`\gamma = 1.5` and :math:`\sigma_{\text{max}} = 0.10`:
* Zero uncertainty yields :math:`C = 1.0` (100% confidence).
* An uncertainty of :math:`\sigma_{\text{total}} = 0.0462` yields :math:`C = 0.50` (50% confidence).
* An uncertainty of :math:`\sigma_{\text{total}} = \sigma_{\text{max}} = 0.10` yields :math:`C = \exp(-1.5) \approx 0.2231` (22.3% confidence).

3.6 Spatial Telemetry Rendering (Plot 1)
----------------------------------------
Cell 07 constructs a :math:`2 \times 3` multi-panel figure displaying spatial fields in
distinct colormaps (``Blues``, ``Reds``, ``YlOrBr``, ``Purples``, ``magma``, and ``viridis``).
Colorbars and axis titles present exact physical units (:math:`\text{m}^3/\text{m}^3`).

3.7 Reliability and Empirical Coverage Audit
--------------------------------------------
Cells 09 through 14 flatten the 2D arrays, synthesize evaluation residuals, compute coverage percentages
across :math:`1\sigma, 2\sigma, 3\sigma` confidence intervals, and plot reliability curves:

.. code-block:: python

   predicted_sigma = sigma_total.flatten()
   true_errors = np.random.normal(0, predicted_sigma)

   cov_1sigma = np.mean(np.abs(true_errors) <= 1.0 * predicted_sigma) * 100
   cov_2sigma = np.mean(np.abs(true_errors) <= 2.0 * predicted_sigma) * 100
   cov_3sigma = np.mean(np.abs(true_errors) <= 3.0 * predicted_sigma) * 100

3.8 Sensor Outage Stress Scenario
---------------------------------
Cells 15 through 17 execute an extreme operational failure scenario where satellite revisit is delayed
by 14 days and heavy persistent cloud cover elevates sensor noise to :math:`0.08\text{ m}^3/\text{m}^3`:

.. code-block:: python

   stress_gap = 0.005 * np.exp(14.0 / 4.0)
   stress_sensor = np.full(GRID_SIZE, 0.08)
   stress_sigma_total, stress_confidence = compute_composite_uncertainty(
       sigma_ens, stress_sensor, stress_gap, sigma_model
   )


4. Component Design
===================

4.1 Grid Domain Controller
--------------------------
The grid domain controller manages spatial discretization.
In the current implementation, it consists of the constant definition:

.. code-block:: python

   GRID_SIZE = (50, 50)

This establishes a uniform Cartesian grid of 2500 pixels.
*Design Note*: This represents a local grid domain that is not georeferenced to the real-world
EPSG:32644 CRS established in Notebooks 01 and 02.

4.2 Variance Field Synthesizers
-------------------------------
The synthesizers generate stochastic fields representing orthogonal physical error sources:

.. list-table:: Variance Field Synthesizer Specifications
   :widths: 20 25 25 30
   :header-rows: 1

   * - Contributor
     - Mathematical Distribution
     - Implementation Parameters
     - Physical Phenomenon Represented
   * - :math:`\sigma_{\text{ens}}`
     - :math:`\mathcal{U}(a, b)`
     - :math:`a=0.01, b=0.04`
     - EnKF ensemble spread across state trajectories
   * - :math:`\sigma_{\text{sensor}}`
     - :math:`\sigma_0 + \Delta\sigma \cdot \mathcal{B}(p) + |\mathcal{N}(0, s)|`
     - :math:`\sigma_0=0.01, \Delta\sigma=0.035, p=0.25, s=0.015`
     - Optical cloud occlusion and SAR radar speckle
   * - :math:`\sigma_{\text{gap}}`
     - :math:`\sigma_{\text{base}} \exp(\Delta t / \tau)`
     - :math:`\sigma_{\text{base}}=0.005, \tau=4.0\text{ d}, \Delta t \in [0, 10]`
     - Epistemic uncertainty growth during orbit revisit gaps
   * - :math:`\sigma_{\text{model}}`
     - :math:`|\mathcal{N}(\mu, \sigma)|` (Folded Normal)
     - :math:`\mu=0.015, \sigma=0.008`
     - Divergence between ConvLSTM neural model and PDE physics

4.3 Composite Uncertainty Engine
--------------------------------
The composite uncertainty engine combines the variance fields under the assumption of mutual orthogonality:

.. math::

   \sigma_{\text{total}}(\mathbf{x}) = \sqrt{
       \sigma_{\text{ens}}^2(\mathbf{x}) +
       \sigma_{\text{sensor}}^2(\mathbf{x}) +
       \sigma_{\text{gap}}^2(\mathbf{x}) +
       \sigma_{\text{model}}^2(\mathbf{x})
   }

Because covariances between distinct error sources are assumed zero (:math:`\operatorname{Cov}(\sigma_i, \sigma_j) = 0`),
quadratic addition preserves variance additivity without cross-coupling terms.

4.4 Exponential Confidence Mapper
---------------------------------
The confidence mapper translates the dimensional standard deviation into a dimensionless confidence metric:

.. math::

   C(\mathbf{x}) = \min\left(1.0, \max\left(0.0, \exp\left(-\gamma \frac{\sigma_{\text{total}}(\mathbf{x})}{\sigma_{\text{max}}}\right)\right)\right)

Parameters:
* :math:`\gamma = 1.5`: Non-linear steepness parameter controlling the rate of confidence decay.
* :math:`\sigma_{\text{max}} = 0.10\text{ m}^3/\text{m}^3`: Benchmark maximum allowable volumetric moisture error.

4.5 Empirical Coverage and Reliability Auditor
----------------------------------------------
The auditor evaluates calibration quality by comparing empirical containment rates against Gaussian theory:

.. math::

   \operatorname{Coverage}(k) = \frac{1}{N} \sum_{i=1}^N \mathbb{I}\left( |e_i| \le k \cdot \sigma_i \right)

For standard Gaussian error distributions, theoretical coverage targets are:
* :math:`1\sigma` (:math:`k=1.0`): :math:`68.27\%`
* :math:`2\sigma` (:math:`k=2.0`): :math:`95.45\%`
* :math:`3\sigma` (:math:`k=3.0`): :math:`99.73\%`

4.6 Sensor Failure Stress Testing Harness
-----------------------------------------
The stress harness simulates extreme degraded operating conditions:
* :math:`\Delta t = 14.0\text{ days}` (cloud cover lasting two full orbital cycles):
  :math:`\sigma_{\text{gap}} = 0.005 \cdot \exp(14.0 / 4.0) = 0.005 \cdot \exp(3.5) \approx 0.1656\text{ m}^3/\text{m}^3`.
* Sensor noise clamped to a severe uniform value: :math:`\sigma_{\text{sensor}} = 0.08\text{ m}^3/\text{m}^3`.
* Total uncertainty spikes to :math:`\sigma_{\text{total}} \approx 0.1865\text{ m}^3/\text{m}^3`.
* Confidence score collapses to :math:`C \approx 0.0610` (6.10%).


5. Data Structures
==================

5.1 Input Data Structures
-------------------------
In the standalone sandbox execution, input parameters are defined in-memory:

.. list-table:: Input Configuration Data Structures
   :widths: 25 15 20 40
   :header-rows: 1

   * - Parameter
     - Type
     - Dimensions
     - Value / Description
   * - ``GRID_SIZE``
     - ``tuple``
     - ``(2,)``
     - ``(50, 50)`` (2500 discrete spatial cells)
   * - ``gamma``
     - ``float``
     - Scalar
     - ``1.5`` (Confidence decay sensitivity)
   * - ``sigma_max``
     - ``float``
     - Scalar
     - ``0.10`` (Maximum uncertainty normalization bound)
   * - ``seed``
     - ``int``
     - Scalar
     - ``1607`` (NumPy and PyTorch deterministic seed)

5.2 In-Memory Variance and State Tensors
---------------------------------------
All intermediate uncertainty fields exist as 2D NumPy float arrays:

.. list-table:: In-Memory Array Tensors
   :widths: 20 15 15 20 30
   :header-rows: 1

   * - Variable Name
     - Data Type
     - Shape
     - Memory Size
     - Empirical Mean (Seed 1607)
   * - ``sigma_ens``
     - ``float64``
     - ``(50, 50)``
     - 20.0 KB
     - :math:`0.0248\text{ m}^3/\text{m}^3`
   * - ``cloud_mask``
     - ``int32``
     - ``(50, 50)``
     - 10.0 KB
     - 24.32% cloud fraction
   * - ``sigma_sensor``
     - ``float64``
     - ``(50, 50)``
     - 20.0 KB
     - :math:`0.0307\text{ m}^3/\text{m}^3`
   * - ``time_since_obs``
     - ``float64``
     - ``(50, 50)``
     - 20.0 KB
     - :math:`5.03\text{ days}`
   * - ``sigma_gap``
     - ``float64``
     - ``(50, 50)``
     - 20.0 KB
     - :math:`0.0222\text{ m}^3/\text{m}^3`
   * - ``sigma_model``
     - ``float64``
     - ``(50, 50)``
     - 20.0 KB
     - :math:`0.0151\text{ m}^3/\text{m}^3`
   * - ``sigma_total``
     - ``float64``
     - ``(50, 50)``
     - 20.0 KB
     - :math:`0.0521\text{ m}^3/\text{m}^3`
   * - ``confidence_score``
     - ``float64``
     - ``(50, 50)``
     - 20.0 KB
     - :math:`0.4699` (46.99%)

5.3 Evaluation and Metric Records
---------------------------------
Evaluation vectors used during reliability coverage and calibration assessment:

.. list-table:: Evaluation Metrics Data Structures
   :widths: 20 15 15 50
   :header-rows: 1

   * - Variable
     - Type
     - Shape
     - Description
   * - ``predicted_sigma``
     - ``float64``
     - ``(2500,)``
     - Flattened 1D array of total standard deviations.
   * - ``true_errors``
     - ``float64``
     - ``(2500,)``
     - Synthetic residual errors drawn from :math:`\mathcal{N}(0, \sigma_{\text{predicted}})`.
   * - ``nom_levels``
     - ``float64``
     - ``(15,)``
     - Nominal coverage levels from :math:`0.10` to :math:`0.99`.
   * - ``cov_rates``
     - ``float64``
     - ``(15,)``
     - Empirical coverage fractions evaluated across nominal levels.

5.4 Output Deliverable Interfaces
---------------------------------
The primary single-pixel output deliverable structure formatted for terminal display:

.. code-block:: text

   ======================================================================
   AETHER-MRID1607X: UNIFIED DELIVERABLE (Pixel [25, 25])
   ======================================================================
   Estimated Volumetric Soil Moisture : 0.2971 m^3/m^3
   Total Combined Uncertainty (±1σ)   : ±0.0731 m^3/m^3
   Calibrated Operational Confidence  : 33.40%
   Integrity Status                   : PASS (Within Physical Limits)
   ======================================================================


6. Algorithms and Methods
=========================

6.1 Orthogonal Variance Summation
---------------------------------
Let :math:`\mathbf{x} = (u, v)` denote spatial pixel coordinates.
Assuming the error contributors are mutually independent, the composite error variance
equals the sum of individual variances:

.. math::

   \operatorname{Var}_{\text{total}}(\mathbf{x}) =
   \operatorname{Var}_{\text{ens}}(\mathbf{x}) +
   \operatorname{Var}_{\text{sensor}}(\mathbf{x}) +
   \operatorname{Var}_{\text{gap}}(\mathbf{x}) +
   \operatorname{Var}_{\text{model}}(\mathbf{x})

Taking the square root yields the composite standard deviation:

.. math::

   \sigma_{\text{total}}(\mathbf{x}) = \sqrt{\sum_{k=1}^4 \sigma_k^2(\mathbf{x})}

Because each :math:`\sigma_k \ge 0`, the function is strictly monotonic:

.. math::

   \frac{\partial \sigma_{\text{total}}}{\partial \sigma_k} = \frac{\sigma_k}{\sigma_{\text{total}}} \ge 0

6.2 Exponential Confidence Decay Scaling
----------------------------------------
To convert dimensional physical uncertainty (:math:`\text{m}^3/\text{m}^3`) into an operational
reliability metric, an exponential transformation is applied:

.. math::

   C(\mathbf{x}) = \operatorname{clip}\left(\exp\left(-\gamma \frac{\sigma_{\text{total}}(\mathbf{x})}{\sigma_{\text{max}}}\right), 0.0, 1.0\right)

Properties of the exponential mapper:
1. **Upper Bound**: :math:`\lim_{\sigma_{\text{total}} \to 0} C = 1.0`.
2. **Strict Monotonicity**: :math:`\frac{dC}{d\sigma_{\text{total}}} = -\frac{\gamma}{\sigma_{\text{max}}} \exp\left(-\gamma \frac{\sigma_{\text{total}}}{\sigma_{\text{max}}}\right) < 0`.
3. **Decay Half-Life**: The half-confidence uncertainty (:math:`C = 0.5`) occurs at:

   .. math::

      \sigma_{1/2} = \frac{\ln(2)}{\gamma} \sigma_{\text{max}} = \frac{0.6931}{1.5} \times 0.10 \approx 0.0462\text{ m}^3/\text{m}^3

6.3 Empirical Interval Coverage Evaluation
------------------------------------------
Given standard deviations :math:`\sigma_i` and error residuals :math:`e_i`, empirical coverage is evaluated as:

.. math::

   \operatorname{Cov}_k = \frac{1}{N} \sum_{i=1}^N \mathbb{I}\left( \frac{|e_i|}{\sigma_i} \le k \right) \times 100\%

For a calibrated normal distribution:
* :math:`k = 1.0`: :math:`\operatorname{erf}(1 / \sqrt{2}) \approx 68.27\%` (Notebook result: **67.04%**)
* :math:`k = 2.0`: :math:`\operatorname{erf}(2 / \sqrt{2}) \approx 95.45\%` (Notebook result: **95.52%**)
* :math:`k = 3.0`: :math:`\operatorname{erf}(3 / \sqrt{2}) \approx 99.73\%` (Notebook result: **99.72%**)

6.4 Spread-Skill Diagnostic Formulation
---------------------------------------
The spread-skill relationship evaluates whether predicted uncertainty corresponds to actual error magnitude.
Under perfect calibration:

.. math::

   \mathbb{E}\left[ |e_i| \;\middle|\; \sigma_i \right] = \sigma_i \sqrt{\frac{2}{\pi}} \approx 0.7979 \cdot \sigma_i

The notebook renders a scatter plot of :math:`\sigma_i` versus :math:`|e_i|` along with a 1:1 reference line
to diagnose under-confidence or over-confidence.

6.5 Outage Latency Propagation Model
------------------------------------
During satellite communication loss or persistent cloud obstruction, the temporal revisit gap :math:`\Delta t`
increases linearly with time.
The resulting epistemic uncertainty grows exponentially:

.. math::

   \sigma_{\text{gap}}(\Delta t) = \sigma_{\text{base}} \exp\left(\frac{\Delta t}{\tau}\right)

With :math:`\sigma_{\text{base}} = 0.005` and relaxation time :math:`\tau = 4.0\text{ days}`:
* :math:`\Delta t = 0\text{ d} \implies \sigma_{\text{gap}} = 0.0050`
* :math:`\Delta t = 4\text{ d} \implies \sigma_{\text{gap}} = 0.0136`
* :math:`\Delta t = 8\text{ d} \implies \sigma_{\text{gap}} = 0.0369`
* :math:`\Delta t = 14\text{ d} \implies \sigma_{\text{gap}} = 0.1656`

This exponential penalty ensures that forecasts rapidly degrade in operational confidence when
observational data assimilation ceases.


7. Interfaces
=============

7.1 Upstream Pipeline Interfaces
--------------------------------
In the integrated production pipeline, Notebook 07 expects the following interfaces:

* **From Notebook 06 (State Estimation)**:
  Assimilated posterior error covariance matrix :math:`\mathbf{P}^a` containing diagonal state variances
  :math:`\sigma_{\text{ens}}^2 = \mathbf{P}^a_{0,0}`.
* **From Notebook 04 (Temporal Modeling)**:
  Temporal forecast variance and elapsed observation timestamp difference :math:`\Delta t`.
* **From Notebook 05 (Physics Validation)**:
  Residual physics disagreement :math:`|R_{\text{Richards}}|` mapped to :math:`\sigma_{\text{model}}`.
* **From Notebook 01/02 (Data Ingestion/Preprocessing)**:
  Satellite QA masks and Scene Classification Layers (SCL) defining :math:`\sigma_{\text{sensor}}`.

7.2 Internal Programmatic Interfaces
------------------------------------

Function: ``compute_composite_uncertainty``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def compute_composite_uncertainty(
       sigma_ens: np.ndarray,
       sigma_sensor: np.ndarray,
       sigma_gap: np.ndarray,
       sigma_model: np.ndarray,
       gamma: float = 1.5
   ) -> tuple[np.ndarray, np.ndarray]:
       """
       Computes the total composite standard deviation and exponential confidence score.

       Parameters:
           sigma_ens (np.ndarray): 2D array of ensemble spread standard deviations.
           sigma_sensor (np.ndarray): 2D array of sensor quality and cloud uncertainty.
           sigma_gap (np.ndarray): 2D array of temporal revisit latency penalties.
           sigma_model (np.ndarray): 2D array of physics model disagreement standard deviations.
           gamma (float, optional): Exponential decay sensitivity factor (default 1.5).

       Returns:
           tuple[np.ndarray, np.ndarray]:
               - sigma_total: Root-sum-squared composite standard deviation array.
               - confidence_score: Normalized confidence score array bounded in [0.0, 1.0].
       """

7.3 Graphical Visualization Interfaces
--------------------------------------
The notebook renders two high-resolution Matplotlib figures:

1. **Aerospace Plot 1 (Multi-Panel Variance Decomposition)**:
   - Size: :math:`16 \times 9` inches, DPI 150.
   - Grid: :math:`2 \times 3` subplots.
   - Colormaps: Individual component maps use specialized palettes; composite uncertainty uses ``magma``;
     confidence index uses ``viridis``.
2. **Aerospace Plot 2 (Calibration Diagnostics & Reliability)**:
   - Size: :math:`14 \times 6` inches, DPI 150.
   - Left Panel: Spread-skill scatter plot with 1:1 diagonal reference line.
   - Right Panel: Theoretical vs. empirical reliability calibration curve with highlighted :math:`1\sigma, 2\sigma, 3\sigma` points.

7.4 Downstream Consumer Interfaces
----------------------------------
Downstream modules (Notebook 08 *Failure Analysis* and operational hazard mapping) consume:

* ``sigma_total``: 2D array of standard deviations in :math:`\text{m}^3/\text{m}^3`.
* ``confidence_score``: 2D array of confidence indices in :math:`[0.0, 1.0]`.
* Boolean gating mask: :math:`\mathcal{M}_{\text{valid}} = (\text{confidence\_score} \ge C_{\text{threshold}})`.


8. Configuration
================

8.1 Hyperparameters and Physical Constants
------------------------------------------
The quantitative behavior of the uncertainty engine is governed by five primary constants:

.. list-table:: Configuration Constants
   :widths: 25 15 15 45
   :header-rows: 1

   * - Parameter Name
     - Type
     - Default Value
     - Physical / Algorithmic Meaning
   * - ``GRID_SIZE``
     - ``tuple``
     - ``(50, 50)``
     - Spatial dimensions of the evaluation lattice.
   * - ``gamma``
     - ``float``
     - ``1.5``
     - Exponential confidence decay steepness.
   * - ``sigma_max``
     - ``float``
     - ``0.10``
     - Upper threshold for volumetric soil moisture uncertainty (:math:`\text{m}^3/\text{m}^3`).
   * - ``tau_gap``
     - ``float``
     - ``4.0``
     - Exponential time constant for revisit latency growth (days).
   * - ``cloud_probability``
     - ``float``
     - ``0.25``
     - Prior Bernoulli probability of cloud obstruction.

8.2 Environment and Hardware Dependencies
-----------------------------------------
The execution environment requires the following software libraries:

* Python :math:`\ge 3.10`
* NumPy :math:`\ge 1.23.0`
* Matplotlib :math:`\ge 3.7.0`
* SciPy :math:`\ge 1.10.0`
* PyTorch :math:`\ge 2.0.0` (used for deterministic seed initialization)

8.3 Deterministic Seeding Configuration
---------------------------------------
Global random generators are fixed at the top of the notebook:

.. code-block:: python

   np.random.seed(1607)
   torch.manual_seed(1607)

This guarantees bit-exact replication of all synthetic variance distributions, pixel metrics,
and graphical plots across different runs.

8.4 Visual Styling Palette
--------------------------
Plot formatting adheres to the JCC RS-SDA dark telemetry design specification:

* Figure Background: ``#0B1528`` (Deep Navy)
* Axes Background: ``#0F1B2B``
* Grid Lines: ``#1A3344``, alpha 0.4, linestyle ``--``
* Border Accents: ``#00FFCC`` (Cyan)
* Font Family: Monospace (Consolas / DejaVu Sans Mono)


9. Error Handling and Defensive Design
======================================

9.1 Non-Negative Variance Safeguards
------------------------------------
All variance sources are bounded below by zero.
The model disagreement uses the folded normal distribution (:math:`|\mathcal{N}(\mu, \sigma)|`) to ensure
that random draws never yield negative standard deviations.

9.2 Zero-Division and Overflow Mitigation
-----------------------------------------
In the temporal revisit formulation:

.. math::

   \sigma_{\text{gap}} = 0.005 \cdot \exp\left(\frac{\Delta t}{4.0}\right)

Since :math:`\Delta t \ge 0`, the exponent is always non-negative.
For operational inputs :math:`\Delta t \le 30\text{ days}`, :math:`\exp(7.5) \approx 1808`, preventing
floating-point overflow in 64-bit IEEE arithmetic.

9.3 Confidence Bounding Enforcement
-----------------------------------
The confidence mapper explicitly clips outputs to the unit interval:

.. code-block:: python

   confidence_score = np.clip(confidence_score, 0.0, 1.0)

This prevents numerical anomalies where small negative values or numbers slightly exceeding 1.0
could propagate into downstream classification logic.

9.4 Array Shape and Type Integrity
----------------------------------
All arrays are created with identical shape ``(50, 50)`` and floating-point precision ``float64``,
preventing broadcasting errors during quadratic summation.


10. Generated Artifacts and Visualizations
==========================================

10.1 Multi-Panel Variance Heatmap (Plot 1)
------------------------------------------
Rendered in Cell 07, this :math:`2 \times 3` panel visualization details the spatial breakdown of uncertainty:

* **Panel (0,0)**: *Ensemble Spread (:math:`\sigma_{\text{ens}}`)* - Uniform variation in :math:`[0.01, 0.04]`.
* **Panel (0,1)**: *Sensor Quality (:math:`\sigma_{\text{sensor}}`)* - Spatial clusters displaying cloud mask contamination.
* **Panel (0,2)**: *Revisit Gap Penalty (:math:`\sigma_{\text{gap}}`)* - Exponential latency surface.
* **Panel (1,0)**: *Model Disagreement (:math:`\sigma_{\text{model}}`)* - Folded normal epistemic error.
* **Panel (1,1)**: *Total Composite Uncertainty (:math:`\sigma_{\text{total}}`)* - Root-sum-squared composite error.
* **Panel (1,2)**: *Confidence Score Map (:math:`C`)* - Normalized reliability index in :math:`[0, 1]`.

10.2 Reliability Curve and Spread-Skill Diagnostic (Plot 2)
-----------------------------------------------------------
Rendered in Cell 14, this 2-panel figure provides statistical validation:

* **Left Panel**: Scatter plot of predicted uncertainty vs. actual residual errors, annotated with
  coverage metrics (:math:`1\sigma = 67.04\%, 2\sigma = 95.52\%, 3\sigma = 99.72\%`).
* **Right Panel**: Reliability curve comparing theoretical confidence levels against empirical coverage,
  verifying alignment along the diagonal line.

10.3 Single-Pixel Diagnostic Telemetry
--------------------------------------
Logged to terminal output in Cell 08 for reference pixel :math:`(25, 25)`:

.. code-block:: text

   Location Coordinates: (x=25, y=25)
   Soil Moisture (theta): 0.2971 m^3/m^3
   Total Uncertainty (±1σ): ±0.0731 m^3/m^3
   Confidence Index: 33.40%

10.4 Outage Degradation Audit Log
---------------------------------
Logged to terminal output in Cell 17 for the 14-day persistent cloud outage stress test:

.. code-block:: text

   ======================================================================
   STRESS TEST: 14-DAY PERSISTENT SENSOR OUTAGE
   ======================================================================
   Baseline Mean Uncertainty : ±0.0521 m^3/m^3
   Outage Mean Uncertainty   : ±0.1865 m^3/m^3 (+257.97% increase)
   Baseline Mean Confidence  : 46.99%
   Outage Mean Confidence    : 6.10% (-87.02% reduction)
   Status                    : RESILIENCE VERIFIED (Catastrophic Degradation Safely Detected)
   ======================================================================


11. Reproducibility
===================

11.1 Random Seed Control
------------------------
Full numerical reproducibility is enforced by fixing pseudo-random number generator states:

.. code-block:: python

   np.random.seed(1607)
   torch.manual_seed(1607)

11.2 Mathematical Determinism
-----------------------------
Because all calculations involve elementary closed-form arithmetic (:math:`\sqrt{\cdot}`, :math:`\exp(\cdot)`, :math:`\operatorname{clip}`),
the execution is mathematically deterministic across all platforms implementing IEEE 754 floating-point standards.

11.3 Execution Traceability
---------------------------
When executed from a clean Python kernel under seed 1607, the notebook reproduces the exact summary statistics:

.. list-table:: Verified Empirical Numerical Baseline
   :widths: 40 30 30
   :header-rows: 1

   * - Metric / Quantity
     - Expected Baseline
     - Verified Execution
   * - Mean :math:`\sigma_{\text{ens}}`
     - :math:`0.0248`
     - :math:`0.0248`
   * - Mean :math:`\sigma_{\text{sensor}}`
     - :math:`0.0307`
     - :math:`0.0307`
   * - Mean :math:`\sigma_{\text{gap}}`
     - :math:`0.0222`
     - :math:`0.0222`
   * - Mean :math:`\sigma_{\text{model}}`
     - :math:`0.0151`
     - :math:`0.0151`
   * - Mean :math:`\sigma_{\text{total}}`
     - :math:`0.0521`
     - :math:`0.0521`
   * - Mean Confidence Score (:math:`C`)
     - :math:`0.4699` (46.99%)
     - :math:`0.4699` (46.99%)
   * - Empirical Coverage (:math:`1\sigma`)
     - :math:`67.04\%`
     - :math:`67.04\%`
   * - Empirical Coverage (:math:`2\sigma`)
     - :math:`95.52\%`
     - :math:`95.52\%`
   * - Empirical Coverage (:math:`3\sigma`)
     - :math:`99.72\%`
     - :math:`99.72\%`
   * - Outage Uncertainty (:math:`\sigma_{\text{total}}`)
     - :math:`0.1865`
     - :math:`0.1865`
   * - Outage Confidence Score (:math:`C`)
     - :math:`0.0610` (6.10%)
     - :math:`0.0610` (6.10%)


12. Performance Characteristics
===============================

12.1 Execution Latency and Wall-Clock Benchmarks
------------------------------------------------
The computational latency of Notebook 07 is dominated by Matplotlib rendering rather than array math:

.. list-table:: Execution Time Profile
   :widths: 40 30 30
   :header-rows: 1

   * - Pipeline Stage
     - Wall-Clock Duration
     - Percentage of Runtime
   * - Imports & Seed Locking
     - :math:`\approx 0.15\text{ s}`
     - :math:`10\%`
   * - Synthetic Field Generation
     - :math:`\approx 0.01\text{ s}`
     - :math:`< 1\%`
   * - Composite Uncertainty Fusion
     - :math:`\approx 0.002\text{ s}`
     - :math:`< 1\%`
   * - Plot 1 Rendering (6-Panel)
     - :math:`\approx 0.65\text{ s}`
     - :math:`45\%`
   * - Coverage & Reliability Audit
     - :math:`\approx 0.05\text{ s}`
     - :math:`3\%`
   * - Plot 2 Rendering (Calibration)
     - :math:`\approx 0.55\text{ s}`
     - :math:`38\%`
   * - Stress Test Evaluation
     - :math:`\approx 0.01\text{ s}`
     - :math:`< 1\%`
   * - **Total End-to-End Latency**
     - :math:`\approx \mathbf{1.42\text{ s}}`
     - :math:`\mathbf{100\%}`

12.2 Memory Footprint and Array Profiling
-----------------------------------------
The maximum memory footprint during execution is extremely lightweight:
* 6 arrays of shape :math:`(50, 50)` at 8 bytes per element: :math:`6 \times 2500 \times 8 = 120\text{ KB}`.
* Matplotlib figure buffers: :math:`\approx 25\text{ MB}` peak memory in RAM.
* Total process working set: :math:`< 150\text{ MB}`.

12.3 Scalability Analysis for Continental Grids
-----------------------------------------------
Vectorized NumPy array operations scale linearly with pixel count :math:`O(N)`:
* Grid :math:`50 \times 50` (:math:`2.5 \times 10^3` pixels): :math:`0.002\text{ s}`.
* Regional Grid :math:`1000 \times 1000` (:math:`1.0 \times 10^6` pixels): :math:`\approx 0.045\text{ s}`.
* Continental Grid :math:`10000 \times 10000` (:math:`1.0 \times 10^8` pixels): :math:`\approx 4.8\text{ s}` (requiring :math:`\approx 4.8\text{ GB}` RAM).


13. Implementation Notes
========================

13.1 Current Implementation State
---------------------------------
The implementation in ``07-uncertainty-analysis.ipynb`` serves as an interactive prototype
and algorithmic demonstrator. It successfully proves the mathematical formulation of quadratic
variance fusion, exponential confidence transformation, and reliability coverage calculation.

13.2 Known Implementation Constraints
-------------------------------------
Three critical technical constraints exist in the current codebase:

1. **Circular Reliability Verification (Defect D-001)**:
   In Cell 11, line 244:
   
   .. code-block:: python

      true_errors = np.random.normal(0, predicted_sigma)

   The evaluation residuals are drawn directly from the predicted Gaussian uncertainty.
   Consequently, the empirical coverage figures (:math:`67.04\%, 95.52\%, 99.72\%`) match Gaussian theory
   by synthetic mathematical construction rather than true empirical sensor validation.

2. **Pipeline Decoupling (Defect D-002)**:
   The notebook does not ingest output arrays from preceding pipeline stages:
   - Does not load :math:`\mathbf{P}^a` from Notebook 06.
   - Does not load Richards PDE residuals from Notebook 05.
   - Does not load ConvLSTM predictions from Notebook 04.
   All variance components are synthesized from independent random number generators.

3. **Grid Inconsistency (Defect D-003)**:
   The spatial lattice dimension is :math:`(50, 50)`, whereas Notebook 03 uses :math:`(20, 20)`,
   Notebook 04 uses :math:`(10, 10)`, and Notebook 05 uses :math:`(100, 100)`.

13.3 Architectural Refactoring Roadmap
--------------------------------------
The planned production refactoring targets:
1. Replacing random generators with actual array loaders ingesting ``data_processed/state_estimation_results.npz``.
2. Implementing true residual calculation against in-situ sensor ground truth (e.g., ISMN soil moisture probes).
3. Standardizing all pipeline stages on a unified EPSG:32644 spatial raster grid.
4. Exporting uncertainty products to GeoTIFF and NetCDF formats with complete STAC metadata.


14. Technical Limitations
=========================

14.1 Synthetic Variance Dependency
----------------------------------
Because variance components are generated from synthetic random distributions, the numerical
results demonstrate algorithmic capability but do not constitute real-world satellite validation.

14.2 Circular Coverage Evaluation Limitation
--------------------------------------------
The reliability curves and spread-skill diagrams validate that the numerical coverage evaluator
operates correctly on Gaussian inputs, but they cannot detect model overconfidence or
unmodeled epistemic sensor bias until tested against real ground measurements.

14.3 Spatial Covariance Independence Limitation
-----------------------------------------------
The current quadratic addition model assumes zero spatial correlation between adjacent pixels:

.. math::

   \operatorname{Cov}(\sigma(\mathbf{x}_i), \sigma(\mathbf{x}_j)) = 0 \quad (\forall i \ne j)

In real satellite remote sensing, atmospheric water vapor, cloud shadows, and soil texture heterogeneity
induce spatial auto-correlation. Modeling this requires full 2D spatial error covariance matrices.


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
     - Section 3.2, Section 4.1
     - Cell 02
     - ``GRID_SIZE = (50, 50)``
   * - **FR-002**
     - Section 3.3, Section 4.2
     - Cell 03
     - ``sigma_ens = np.random.uniform(0.01, 0.04, GRID_SIZE)``
   * - **FR-003**
     - Section 3.3, Section 4.2
     - Cell 03
     - ``sigma_sensor = 0.01 + 0.035 * cloud_mask + ...``
   * - **FR-004**
     - Section 3.3, Section 4.2
     - Cell 03
     - ``sigma_gap = 0.005 * np.exp(time_since_obs / 4.0)``
   * - **FR-005**
     - Section 3.3, Section 4.2
     - Cell 03
     - ``sigma_model = np.abs(np.random.normal(0.015, 0.008, GRID_SIZE))``
   * - **FR-006**
     - Section 3.4, Section 4.3, Section 6.1
     - Cell 04, Cell 05
     - ``sigma_total = np.sqrt(sum(sigma_i**2))``
   * - **FR-007**
     - Section 3.5, Section 4.4, Section 6.2
     - Cell 04, Cell 05
     - ``confidence_score = np.clip(np.exp(-gamma * ...), 0, 1)``
   * - **FR-008**
     - Section 3.4, Section 11.3
     - Cell 06
     - Terminal logging of mean uncertainty and confidence.
   * - **FR-009**
     - Section 3.6, Section 7.3, Section 10.1
     - Cell 07
     - Aerospace Plot 1 (:math:`2 \times 3` panel figure).
   * - **FR-010**
     - Section 3.4, Section 5.4, Section 10.3
     - Cell 08
     - Deliverable printout at pixel :math:`(25, 25)`.
   * - **FR-011**
     - Section 3.7, Section 4.5, Section 6.3
     - Cell 09-11
     - Empirical coverage computation (:math:`1\sigma, 2\sigma, 3\sigma`).
   * - **FR-012**
     - Section 3.7, Section 7.3, Section 10.2
     - Cell 12-14
     - Aerospace Plot 2 (Spread-skill and reliability curves).
   * - **FR-013**
     - Section 3.8, Section 4.6, Section 6.5
     - Cell 15, Cell 16
     - Outage stress test (:math:`\Delta t = 14\text{ d}`, :math:`\sigma_{\text{sensor}} = 0.08`).
   * - **FR-014**
     - Section 3.8, Section 10.4
     - Cell 17
     - Degradation telemetry comparison printout.
   * - **DI-001**
     - Section 4.2, Section 9.1
     - Cell 03
     - Non-negative array generation.
   * - **DI-002**
     - Section 4.3, Section 6.1
     - Cell 04
     - Monotonic quadratic addition.
   * - **DI-003**
     - Section 4.4, Section 9.3
     - Cell 04
     - Output clipping to :math:`[0.0, 1.0]`.
   * - **DI-004**
     - Section 4.4, Section 6.2
     - Cell 04
     - Strict inverse monotonic decay of exponential mapper.
   * - **DI-005**
     - Section 4.5, Section 6.3
     - Cell 11
     - Monotonic coverage hierarchy (:math:`\operatorname{Cov}_{1\sigma} \le \operatorname{Cov}_{2\sigma} \le \operatorname{Cov}_{3\sigma}`).
