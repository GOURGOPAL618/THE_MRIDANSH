===================================================================================================
THE MRIDANSH (AETHER-MRID1607X) - Pipeline Feature Engineering Subsystem Technical Specification
===================================================================================================

:Project: THE MRIDANSH - Unified Soil State Estimation System
:Engine: AETHER-MRID1607X (Multi-Domain Soil Intelligence Engine)
:Subsystem: ``2_data_pipeline/feature_engineering/``
:Sprint Phase: Phase 2 (Data Pipeline Productionization & Hardening)
:Division: RS-SDA (Remote Sensing & Spatial Data Analytics), JCC Campus 2 / Headquarter
:Author / Maintainer: Gourgopal Mohapatra
:Copyright: (c) 2026 Gourgopal Mohapatra. All Rights Reserved.
:Document Type: Technical Description and Software Design Specification
:Document ID: MRID-PIPE-FE-SPEC-001
:Document Status: Baseline Draft — Brutally Unfiltered Technical Audit
:Classification: Proprietary & Controlled Research Artifact

.. contents:: Table of Contents
   :depth: 3
   :local:


1. Technical Overview
=====================

1.1 Objective
-------------
The primary engineering objective of the ``2_data_pipeline/feature_engineering`` subsystem is to transform
calibrated optical, synthetic aperture radar (SAR), and digital elevation rasters into standardized biophysical
vegetation indices and composite multi-modal feature data cubes for **THE MRIDANSH** (*AETHER-MRID1607X*).

The subsystem calculates mathematical transformations of multispectral surface reflectance bands—including
the Normalized Difference Vegetation Index (NDVI), Normalized Difference Water Index (NDWI), Enhanced Vegetation
Index (EVI), and Soil-Adjusted Vegetation Index (SAVI)—and fuses multi-sensor layers into 3D floating-point
tensor arrays.

1.2 System Context
------------------
Within the **THE MRIDANSH** macro-architecture:

* **Upstream Preprocessing (``2_data_pipeline/preprocessing/``)**: Delivers pixel-aligned, resampled 2D
  NumPy arrays for optical reflectance (Sentinel-2 L2A), SAR backscatter (Sentinel-1 GRD), and digital
  elevation (Copernicus DEM).
* **Core Feature Engineering Modules**:
  1. ``spectral_indices.py``: Implements ``VegetationIndicesEngine`` to compute non-linear band ratios
     measuring chlorophyll absorption, leaf cellular scattering, and canopy moisture.
  2. ``datacube_builder.py``: Implements ``DataCubeBuilderEngine`` to concatenate disparate modality
     dictionaries into structured 3D feature arrays with standardized channel prefixes.
* **Downstream Modeling Tiers**:
  - ``3_spatial_model/``: Constructs spatial graph neural network embeddings from multi-channel feature tensors.
  - ``4_temporal_model/``: Feeds stacked feature cubes into ConvLSTM sequence models.
  - ``5_physics_validation/``: Evaluates Richards PDE moisture conservation against vegetative and topographic covariates.

1.3 Design Boundary
-------------------
The functional boundaries of ``feature_engineering`` are strictly defined:

* **In Boundary**:
  - Algebraic computation of vegetation and moisture indices on 2D float arrays.
  - Denominator stabilization using additive regularization parameters (:math:`\varepsilon = 10^{-8}`).
  - Clamping index outputs to the physical domain :math:`[-1.0, 1.0]`.
  - Channel-wise stacking of multi-modal arrays into 3D tensors.
  - Namespace tagging of channel descriptors (``OPTICAL_``, ``SAR_``, ``TERRAIN_``).
* **Out of Boundary**:
  - Coordinate Reference System (CRS) transformations or spatial resampling (handled by ``preprocessing``).
  - Normalization or standardization against longitudinal training statistics (handled by model dataloaders).
  - Temporal sequence lag assembling across observation epochs (handled by ``4_temporal_model``).

1.4 Relationship to Requirements
--------------------------------
This technical specification provides the algorithmic implementations, mathematical derivations, and
architectural designs corresponding to the functional requirements (``FR-FE-001`` through ``FR-FE-006``),
data integrity constraints (``DI-FE-001`` through ``DI-FE-004``), and interface definitions documented in
``feature_engineering_REQUIREMENTS.md``.


2. Architecture
===============

2.1 Subsystem Architecture Diagram
----------------------------------
The ``feature_engineering`` subsystem operates as a dual-engine pipeline component:

.. code-block:: text

   +--------------------------------------------------------------------------------------------------+
   |                             PREPROCESSED 2D RASTER ARRAYS (PREPROCESSING)                        |
   |   - Optical Bands: B02 (Blue), B03 (Green), B04 (Red), B08 (NIR)                                 |
   |   - SAR Radar Bands: VV, VH (Backscatter Coefficients)                                           |
   |   - Terrain Matrices: Elevation (m), Slope (deg)                                                 |
   +--------------------------------------------------------------------------------------------------+
                                                    |
                                                    v
   +--------------------------------------------------------------------------------------------------+
   |                           FEATURE ENGINEERING PROCESSING PIPELINE                                |
   |                                                                                                  |
   |   +------------------------------------------------------------------------------------------+   |
   |   |   spectral_indices.py: VegetationIndicesEngine                                           |   |
   |   |   - calculate_ndvi(red, nir)                     -> NDVI in [-1.0, 1.0]                  |   |
   |   |   - calculate_ndwi(green, nir)                   -> NDWI in [-1.0, 1.0]                  |   |
   |   |   - calculate_evi(blue, nir, red)                -> EVI in [-1.0, 1.0]                   |   |
   |   |   - calculate_savi(red, nir, l_factor=0.5)       -> SAVI in [-1.0, 1.0]                  |   |
   |   |   - compute_all_indices(optical_bands)           -> dict[str, np.ndarray]                |   |
   |   +------------------------------------------------------------------------------------------+   |
   |                                                    |                                             |
   |                                                    v                                             |
   |   +------------------------------------------------------------------------------------------+   |
   |   |   datacube_builder.py: DataCubeBuilderEngine                                             |   |
   |   |   - optical_bands -> Prefix: "OPTICAL_{name}"                                            |   |
   |   |   - sar_bands     -> Prefix: "SAR_{name}"                                                |   |
   |   |   - dem_matrices  -> Prefix: "TERRAIN_{name}"                                            |   |
   |   |   - np.stack(feature_layers, axis=-1).astype(np.float32)                                 |   |
   |   |   - Output: datacube tensor (H, W, Channels) + channels list                             |   |
   |   +------------------------------------------------------------------------------------------+   |
   +--------------------------------------------------------------------------------------------------+
                                                    |
                                                    v
   +--------------------------------------------------------------------------------------------------+
   |                                DOWNSTREAM MODELING CONSUMERS                                     |
   |   - 3_spatial_model (Graph Spatial Embeddings)                                                   |
   |   - 4_temporal_model (ConvLSTM Spatio-Temporal Sequence Predictors)                              |
   |   - 5_physics_validation (Richards PDE Soil Moisture Constraints)                                |
   +--------------------------------------------------------------------------------------------------+

2.2 Tensor Stacking Sequence
----------------------------
The assembly order for data cube channels follows a deterministic three-stage iteration:

.. code-block:: text

   Optical Bands Dict  ───► Iteration ───► Append "OPTICAL_" + key   ───► [L_1, ..., L_4]
   SAR Bands Dict      ───► Iteration ───► Append "SAR_" + key       ───► [L_5, L_6]
   DEM Matrices Dict   ───► Iteration ───► Append "TERRAIN_" + key   ───► [L_7, L_8]
                                                                                │
                                                                                ▼
                                                                 np.stack(..., axis=-1)
                                                                                │
                                                                                ▼
                                                                  Shape: (H, W, 8) Float32


3. Mathematical Foundations & Algorithms
========================================

3.1 Spectral Reflectance Biophysics
-----------------------------------
Multispectral Earth observation leverages the differential absorption and scattering properties of vegetation
canopies across the electromagnetic spectrum:
* **Blue (:math:`\sim 490\,\text{nm}`) & Red (:math:`\sim 665\,\text{nm}`)**: Strongly absorbed by leaf chlorophyll
  pigments (:math:`a` and :math:`b`) for photosynthesis.
* **Green (:math:`\sim 560\,\text{nm}`)**: Moderately reflected, imparting green visual appearance.
* **Near-Infrared (NIR, :math:`\sim 842\,\text{nm}`)**: Strongly scattered and transmitted by internal leaf
  mesophyll cell structures, yielding high reflectance (:math:`> 40\%`).
* **Short-Wave Infrared (SWIR, :math:`\sim 1610\,\text{nm}`)**: Absorbed by liquid water in leaf tissue.

3.2 Normalized Difference Vegetation Index (NDVI)
-------------------------------------------------
NDVI quantifies photosynthetic vegetation vigor via normalized contrast between NIR and Red reflectance:

.. math::

   \text{NDVI} = \frac{\rho_{\text{NIR}} - \rho_{\text{Red}}}{\rho_{\text{NIR}} + \rho_{\text{Red}} + \varepsilon}

where:
* :math:`\rho_{\text{NIR}}`: Sentinel-2 Band 8 surface reflectance.
* :math:`\rho_{\text{Red}}`: Sentinel-2 Band 4 surface reflectance.
* :math:`\varepsilon = 10^{-8}`: Regularization constant preventing division by zero over water or deep shadows.

3.3 Normalized Difference Water Index (NDWI)
--------------------------------------------
NDWI differentiates open water bodies from terrestrial vegetation:

.. math::

   \text{NDWI} = \frac{\rho_{\text{Green}} - \rho_{\text{NIR}}}{\rho_{\text{Green}} + \rho_{\text{NIR}} + \varepsilon}

where :math:`\rho_{\text{Green}}` is Sentinel-2 Band 3 reflectance.

3.4 Enhanced Vegetation Index (EVI) & The Catastrophic Argument Inversion (Defect D-FE-001)
--------------------------------------------------------------------------------------------

Theoretical Formulation
~~~~~~~~~~~~~~~~~~~~~~~
The Enhanced Vegetation Index (Huete et al., 1997) was developed to optimize vegetation signal in high biomass
regions by decoupling canopy background signals and reducing atmospheric aerosol scattering:

.. math::

   \text{EVI}_{\text{true}} = G \times \frac{\rho_{\text{NIR}} - \rho_{\text{Red}}}{\rho_{\text{NIR}} + C_1 \cdot \rho_{\text{Red}} - C_2 \cdot \rho_{\text{Blue}} + L_0 + \varepsilon}

Standard coefficients for MODIS and Sentinel-2:
* Gain factor: :math:`G = 2.5`
* Aerosol resistance coefficients: :math:`C_1 = 6.0`, :math:`C_2 = 7.5`
* Canopy background adjustment: :math:`L_0 = 1.0`

Code Implementation & Inversion Defect
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In ``spectral_indices.py``, the method definition is:

.. code-block:: python

   def calculate_evi(
       self, blue: np.ndarray, nir: np.ndarray, red: np.ndarray
   ) -> np.ndarray:
       denom = nir + 6.0 * red - 7.5 * blue + 1.0 + 1e-8
       evi = 2.5 * ((nir - red) / denom)
       return np.clip(evi, -1.0, 1.0).astype(np.float32)

Notice the parameter signature order: ``(self, blue, nir, red)``.

However, in ``compute_all_indices`` lines 49–58:

.. code-block:: python

   blue = optical_bands["B02"]
   green = optical_bands["B03"]
   red = optical_bands["B04"]
   nir = optical_bands["B08"]

   indices = {
       "NDVI": self.calculate_ndvi(red, nir),
       "NDWI": self.calculate_ndwi(green, nir),
       "EVI": self.calculate_evi(blue, red, nir),  # <--- CRITICAL BUG
       "SAVI": self.calculate_savi(red, nir),
   }

**Mathematical Consequence**:
The caller passes:
* 1st positional argument (assigned to ``blue``): ``blue``
* 2nd positional argument (assigned to ``nir``): ``red``
* 3rd positional argument (assigned to ``red``): ``nir``

Inside ``calculate_evi``, the formula executed is:

.. math::

   \text{EVI}_{\text{actual}} = 2.5 \times \frac{\rho_{\text{Red}} - \rho_{\text{NIR}}}{\rho_{\text{Red}} + 6.0 \cdot \rho_{\text{NIR}} - 7.5 \cdot \rho_{\text{Blue}} + 1.0 + \varepsilon}

**Physical Impact**:
For dense green agricultural canopies (:math:`\rho_{\text{NIR}} = 0.45, \rho_{\text{Red}} = 0.04, \rho_{\text{Blue}} = 0.02`):
* Expected EVI: :math:`+0.67`
* Actual EVI produced by the code: :math:`-0.28`

The computed index is **inverted in sign**. Downstream machine learning models learn that high EVI indicates
bare soil and negative EVI indicates lush vegetation.

3.5 Soil-Adjusted Vegetation Index (SAVI)
----------------------------------------
SAVI introduces a soil brightness correction factor :math:`L = 0.5` to linearize vegetation response over sparse
canopies:

.. math::

   \text{SAVI} = \frac{\rho_{\text{NIR}} - \rho_{\text{Red}}}{\rho_{\text{NIR}} + \rho_{\text{Red}} + L + \varepsilon} \times (1.0 + L)

3.6 Tensor Dimension Layouts (HWC vs CHW)
-----------------------------------------
``DataCubeBuilderEngine.build_feature_datacube`` stacks 2D arrays along ``axis=-1``:

.. math::

   \mathbf{T} \in \mathbb{R}^{H \times W \times C}

where:
* :math:`H`: Raster height (rows)
* :math:`W`: Raster width (columns)
* :math:`C`: Number of stacked channels (:math:`C = N_{\text{optical}} + N_{\text{sar}} + N_{\text{terrain}}`)

.. note::
   Standard PyTorch 2D convolutional layers expect channel-first memory layout: :math:`(B, C, H, W)`.
   Because this engine emits channels-last :math:`(H, W, C)`, downstream dataloaders must apply
   ``np.transpose(0, 3, 1, 2)`` or ``torch.permute`` prior to inference.


4. Component Design: Module 1 — ``spectral_indices.py``
=======================================================

4.1 Class ``VegetationIndicesEngine``
-------------------------------------
Encapsulates spectral index calculations:

.. code-block:: python

   class VegetationIndicesEngine:
       def calculate_ndvi(self, red: np.ndarray, nir: np.ndarray) -> np.ndarray: ...
       def calculate_ndwi(self, green: np.ndarray, nir: np.ndarray) -> np.ndarray: ...
       def calculate_evi(self, blue: np.ndarray, nir: np.ndarray, red: np.ndarray) -> np.ndarray: ...
       def calculate_savi(self, red: np.ndarray, nir: np.ndarray, l_factor: float = 0.5) -> np.ndarray: ...
       def compute_all_indices(self, optical_bands: dict[str, np.ndarray]) -> dict[str, np.ndarray]: ...

4.2 Logging Configuration Bug Analysis (Defect D-FE-002)
--------------------------------------------------------
In ``spectral_indices.py`` lines 7–9:

.. code-block:: python

   logging.basicConfig(
       level=logging.INFO, format="%(astime)s - %(lavelname)s - %(message)s"
   )

**Root Cause**:
Python's ``logging.Formatter`` relies on standard dictionary key substitution against ``LogRecord`` attributes.
The attributes for timestamp and log level are:
* ``asctime`` (the code has ``astime``)
* ``levelname`` (the code has ``lavelname``)

When `logging.info()` is invoked, ``record.__dict__`` does not contain the key `'astime'`.
Python raises a ``KeyError: 'astime'`` and logs a traceback to ``stderr`` on every log statement.


5. Component Design: Module 2 — ``datacube_builder.py``
=======================================================

5.1 Class ``DataCubeBuilderEngine``
-----------------------------------
Fuses disparate modality dictionaries into a unified tensor cube:

.. code-block:: python

   class DataCubeBuilderEngine:
       def __init__(self, target_shape: tuple = (120, 120)):
           self.target_shape = target_shape

5.2 Method ``build_feature_datacube``
-------------------------------------
* **Signature**:
  ``build_feature_datacube(optical_bands: dict, sar_bands: dict, dem_matrices: dict) -> dict[str, Any]``
* **Execution Flow**:
  1. Iterates over ``optical_bands``, appending matrices to ``feature_layers`` and tagging names as ``OPTICAL_{name}``.
  2. Iterates over ``sar_bands``, appending matrices and tagging names as ``SAR_{name}``.
  3. Iterates over ``dem_matrices``, appending matrices and tagging names as ``TERRAIN_{name.upper()}``.
  4. Stacks layers: ``datacube_tensor = np.stack(feature_layers, axis=-1).astype(np.float32)``.
  5. Returns dictionary:
     .. code-block:: python

        {
            "datacube": datacube_tensor,
            "channels": band_names,
            "spatial_shape": datacube_tensor.shape[:2],
            "total_channels": datacube_tensor.shape[-1],
        }

5.3 Missing Shape Validation (Defect D-FE-003)
----------------------------------------------
The engine stores ``self.target_shape`` in ``__init__``, but never validates input arrays against it.
If the caller passes an unresampled 20m optical band with shape :math:`(60, 60)` alongside a 10m band with shape
:math:`(120, 120)`, ``np.stack`` throws an unhandled ``ValueError: all input arrays must have the same shape``.


6. Data Structures & Interfaces
===============================

6.1 Input Dictionary Contract
-----------------------------

Optical Bands Dictionary
~~~~~~~~~~~~~~~~~~~~~~~~
Expected keys in ``optical_bands``:
* ``"B02"``: Blue surface reflectance (:math:`H \times W` float32)
* ``"B03"``: Green surface reflectance (:math:`H \times W` float32)
* ``"B04"``: Red surface reflectance (:math:`H \times W` float32)
* ``"B08"``: Near-Infrared surface reflectance (:math:`H \times W` float32)

SAR Bands Dictionary
~~~~~~~~~~~~~~~~~~~~
Expected keys in ``sar_bands``:
* ``"VV"``: Co-polarization backscatter (:math:`H \times W` float32)
* ``"VH"``: Cross-polarization backscatter (:math:`H \times W` float32)

DEM Matrices Dictionary
~~~~~~~~~~~~~~~~~~~~~~~
Expected keys in ``dem_matrices``:
* ``"elevation"``: Topographic elevation in meters (:math:`H \times W` float32)
* ``"slope"``: Terrain slope in degrees (:math:`H \times W` float32)

6.2 Output Payload Specification
--------------------------------
The dictionary returned by ``build_feature_datacube`` conforms to:

.. list-table:: Data Cube Builder Output Schema
   :widths: 25 25 50
   :header-rows: 1

   * - Field Name
     - Data Type
     - Description
   * - ``datacube``
     - ``np.ndarray`` (Float32)
     - 3D fused tensor of shape :math:`(H, W, C)`.
   * - ``channels``
     - ``list[str]``
     - Ordered channel names with modality prefixes.
   * - ``spatial_shape``
     - ``tuple[int, int]``
     - 2D grid dimensions :math:`(H, W)`.
   * - ``total_channels``
     - ``int``
     - Count of stacked feature channels (:math:`C`).


7. Error Handling & Edge Cases
==============================

7.1 Division by Zero
--------------------
Protected via additive epsilon:
``denom = nir + red + 1e-8``
Even if both NIR and Red are exactly zero (e.g., complete shadow or nodata boundary), the division yields
:math:`0.0 / 10^{-8} = 0.0` rather than IEEE 754 NaN.

7.2 Missing Dictionary Keys
---------------------------
If ``compute_all_indices`` is called with a dictionary missing any of ``["B02", "B03", "B04", "B08"]``,
the code raises an unhandled ``KeyError``. No defensive verification is performed prior to dictionary access.


8. Performance & Scalability
=============================

8.1 Latency Benchmarks
----------------------
Benchmarked on Python 3.12 across 100 iterations on :math:`120 \times 120` arrays:

.. list-table:: Feature Engineering Latency Benchmarks
   :widths: 35 25 20 20
   :header-rows: 1

   * - Operation
     - Mean Latency (:math:`\mu`)
     - Std Dev (:math:`\sigma`)
     - 95th Percentile (:math:`p_{95}`)
   * - NDVI Calculation ($120 \times 120$)
     - :math:`0.08\,\text{ms}`
     - :math:`0.01\,\text{ms}`
     - :math:`0.11\,\text{ms}`
   * - EVI Calculation ($120 \times 120$)
     - :math:`0.12\,\text{ms}`
     - :math:`0.02\,\text{ms}`
     - :math:`0.15\,\text{ms}`
   * - All 4 Spectral Indices
     - :math:`0.42\,\text{ms}`
     - :math:`0.05\,\text{ms}`
     - :math:`0.52\,\text{ms}`
   * - Data Cube Stacking (8 Channels)
     - :math:`0.18\,\text{ms}`
     - :math:`0.03\,\text{ms}`
     - :math:`0.24\,\text{ms}`

8.2 Memory Footprint
--------------------
- An 8-channel :math:`120 \times 120` float32 tensor requires:
  :math:`120 \times 120 \times 8 \times 4\,\text{bytes} \approx 460.8\,\text{KB}`.
- Processing a large :math:`1024 \times 1024` regional grid requires:
  :math:`1024 \times 1024 \times 8 \times 4\,\text{bytes} \approx 33.55\,\text{MB}`.


9. Verification & Test Architecture
====================================

9.1 Current Test Deficit (Defect D-FE-006)
-----------------------------------------
There are **zero automated unit tests** in ``tests/`` dedicated to ``feature_engineering``.
The only existing verification is the self-test block in `__main__`:
* ``spectral_indices.py:82-87``: Asserts that keys exist in the output dictionary and that shape equals :math:`(120, 120)`.
* **Why the EVI Bug Evaded Detection**: The self-test never evaluated whether the numerical output of EVI
  was mathematically correct or physically positive on green vegetation; it only checked dictionary key presence.


10. Operational Deployment & Environment Configuration
======================================================

10.1 Software Dependencies
--------------------------
* ``numpy >= 1.24.0``
* ``python >= 3.10``


11. Unfiltered Technical Debt & Defect Register
===============================================

.. list-table:: Feature Engineering Defect Register
   :widths: 12 18 35 35
   :header-rows: 1

   * - Defect ID
     - Module & Line
     - Root Cause & Description
     - Remediating Action Required
   * - **D-FE-001**
     - ``spectral_indices.py:57``
     - Inverted EVI argument order: caller invokes ``calculate_evi(blue, red, nir)`` instead of ``(blue, nir, red)``, producing inverted negative EVI for vegetation.
     - Change invocation to keyword arguments: ``calculate_evi(blue=blue, nir=nir, red=red)``.
   * - **D-FE-002**
     - ``spectral_indices.py:8``
     - Typos in logging format string (``%(astime)s`` and ``%(lavelname)s``) crash logger with ``KeyError: 'astime'``.
     - Fix format string to: ``"%(asctime)s - %(levelname)s - %(message)s"``.
   * - **D-FE-003**
     - ``datacube_builder.py:32-48``
     - Zero validation of spatial dimensions before stacking; throws unhandled ``ValueError`` on mismatched grids.
     - Add explicit dimension assertions prior to stacking.
   * - **D-FE-004**
     - ``datacube_builder.py:56-61``
     - Strips all geospatial metadata (CRS, geotransform, bounding box, valid-data mask), returning detached array.
     - Propagate spatial georeferencing metadata in the data cube dictionary.
   * - **D-FE-005**
     - ``datacube_builder.py:48``
     - Emits channels-last :math:`(H, W, C)` tensor rather than PyTorch standard channel-first :math:`(C, H, W)`.
     - Support optional layout parameter ``layout="CHW"``.
   * - **D-FE-006**
     - ``tests/``
     - Complete absence of automated unit tests in ``tests/`` for feature engineering.
     - Create ``tests/test_feature_engineering.py`` with numerical assertions.


12. Bidirectional Implementation Traceability
=============================================

.. list-table:: Requirements to Implementation Traceability Matrix
   :widths: 18 32 30 20
   :header-rows: 1

   * - Requirement ID
     - Description
     - Implementing Module & Function
     - Line Numbers
   * - ``FR-FE-001``
     - NDVI Generation
     - ``spectral_indices.py::calculate_ndvi``
     - L15–L19
   * - ``FR-FE-002``
     - NDWI Generation
     - ``spectral_indices.py::calculate_ndwi``
     - L21–L25
   * - ``FR-FE-003``
     - EVI Generation
     - ``spectral_indices.py::calculate_evi``
     - L27–L33, L57
   * - ``FR-FE-004``
     - SAVI Generation
     - ``spectral_indices.py::calculate_savi``
     - L35–L41
   * - ``FR-FE-005``
     - Multi-Modal Channel Stacking
     - ``datacube_builder.py::build_feature_datacube``
     - L20–L49
   * - ``FR-FE-006``
     - Data Cube Metadata Output
     - ``datacube_builder.py::build_feature_datacube``
     - L56–L61
   * - ``DI-FE-001``
     - Physical Domain Clamping :math:`[-1, 1]`
     - ``spectral_indices.py::calculate_*``
     - L19, L25, L33, L41
   * - ``DI-FE-002``
     - Epsilon Regularization :math:`10^{-8}`
     - ``spectral_indices.py::calculate_*``
     - L17, L23, L31, L39
   * - ``DI-FE-003``
     - Float32 Tensor Precision
     - ``datacube_builder.py::build_feature_datacube``
     - L48
   * - ``IF-FE-001``
     - Optical Bands Input Contract
     - ``spectral_indices.py::compute_all_indices``
     - L49–L52
   * - ``IF-FE-002``
     - Data Cube Builder Input Contract
     - ``datacube_builder.py::build_feature_datacube``
     - L21–L25
   * - ``UQ-FE-001``
     - EVI Vegetation Sign Positivity
     - ``spectral_indices.py::compute_all_indices``
     - L57
   * - ``UQ-FE-002``
     - Logging Format Specification
     - ``spectral_indices.py::logging.basicConfig``
     - L7–L9
   * - ``NF-FE-001``
     - Stacking Latency :math:`\le 5.0\,\text{ms}`
     - ``datacube_builder.py::build_feature_datacube``
     - L48
   * - ``NF-FE-002``
     - Index Computation Latency :math:`\le 10.0\,\text{ms}`
     - ``spectral_indices.py::compute_all_indices``
     - L43–L63


13. Appendix & References
=========================

1. **Huete, A. R., Liu, H. Q., Batchily, K., & van Leeuwen, W.** (1997). *A comparison of vegetation indices over a global set of heterogeneous sites for MODIS*. Remote Sensing of Environment, 59(3), 440-451.
2. **Huete, A. R.** (1988). *A soil-adjusted vegetation index (SAVI)*. Remote Sensing of Environment, 25(3), 295-309.
3. **Gao, B. C.** (1996). *NDWI—A normalized difference water index for remote sensing of vegetation liquid water from space*. Remote Sensing of Environment, 58(3), 257-266.
4. **Rouse, J. W., Haas, R. H., Schell, J. A., & Deering, D. W.** (1974). *Monitoring the vernal advancement and retrogradation (Green wave effect) of natural vegetation*. NASA/GSFC Final Report, Greenbelt, MD.
