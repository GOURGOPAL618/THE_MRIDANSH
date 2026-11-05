.. _preprocessing_operational_bridges:

========================================================================================
Operational Spaceborne Campaign Preprocessing Bridge (DEM Topography Coupler)
========================================================================================

:Document ID: DOC-MRID-02-PRE-EXT-001
:Module: ``2_data_pipeline/preprocessing/``
:Campaign Subsystem: ``9_spaceborne_operational_campaign/4_execution_engine/dem_topography_coupler.py``
:Classification: High-Integrity Mission-Critical Earth Observation Pipeline Extension
:Author: Gourgopal Mohapatra
:Status: RELEASED / PRODUCTION AUDITED
:Date: 2026-11-05

.. contents:: Table of Contents
   :depth: 3
   :local:

Document Control
================

Identification & Scope
----------------------
This document provides the technical requirements, architectural analysis, and verification baseline for the **operational preprocessing bridge** ``dem_topography_coupler.py`` in ``2_data_pipeline/preprocessing/``. The module bridges the local preprocessing pipeline with the flight-certified DEM terrain coupling engine developed for the **Spaceborne Operational Campaign (SOC-AETHER-2026)** in ``9_spaceborne_operational_campaign/4_execution_engine/``.

Revision History
----------------
.. list-table::
   :widths: 10 15 25 50
   :header-rows: 1

   * - Version
     - Date
     - Author
     - Description of Change
   * - 1.0
     - 2026-11-05
     - Gourgopal Mohapatra
     - Initial engineering baseline and unfiltered architectural audit for ``2_data_pipeline/preprocessing/dem_topography_coupler.py``.

Mandatory Unfiltered Engineering Disclosure & Architectural Audit
=================================================================

.. warning::
   **BRUTAL ARCHITECTURAL REALITY & CODE AUDIT**:

   1. **Inverted Architectural Dependency (Defect D-PRE-EXT-001)**:
      ``dem_topography_coupler.py`` in ``2_data_pipeline/preprocessing/`` inverts classical layering by importing from downstream flight execution code in ``9_spaceborne_operational_campaign/4_execution_engine/``.
   2. **Global sys.path Modification (Defect D-PRE-EXT-002)**:
      Module import dynamically prepends campaign directories to ``sys.path[0]``, causing global namespace pollution across the Python runtime.
   3. **Heuristic TWI Formulation (Defect D-PRE-EXT-003)**:
      The Beven & Kirkby Topographic Wetness Index (:math:`\text{TWI} = \ln(a / \tan \beta)`) requires upslope contributing area :math:`a` computed via hydrological flow routing (such as D8 or D-infinity flow accumulation). Instead of implementing flow routing, ``DEMTopographyCoupler`` employs an inverted relative elevation proxy:

      .. math::

         a_{\text{proxy}} = \Delta x \cdot (1.0 + 15.0 \cdot \text{rel\_depth})

      This shortcut approximates drainage accumulation based solely on relative local depth rather than true hydrological topography.
   4. **Replicate Boundary Padding Artifacts (Defect D-PRE-EXT-004)**:
      Horn's convolution pads outer borders with ``mode='replicate'``, forcing boundary derivatives to zero and dampening calculated slope on the 1-pixel outermost perimeter.
   5. **Missing Package Export (Defect D-PRE-EXT-005)**:
      The bridge class is not exported in ``2_data_pipeline/preprocessing/__init__.py``, preventing clean package-level imports.

Technical Specification & Mathematical Models
=============================================

Resampling to 10m Ground Sampling Distance
------------------------------------------
Input digital elevation models (such as Copernicus GLO-30 at 30m resolution) are resampled to the 10m UTM coordinate grid using bilinear 2D interpolation with corner alignment:

.. code-block:: python

   resampled = F.interpolate(
       dem_4d,
       size=(out_h, out_w),
       mode='bilinear',
       align_corners=True
   )

Horn's 2nd-Order Finite-Difference Gradients
--------------------------------------------
Spatial gradients are estimated using Horn's :math:`3 \times 3` finite-difference convolution kernels:

.. math::

   K_x = \frac{1}{8 \Delta x} \begin{bmatrix} -1 & 0 & 1 \\ -2 & 0 & 2 \\ -1 & 0 & 1 \end{bmatrix}, \quad
   K_y = \frac{1}{8 \Delta y} \begin{bmatrix} -1 & -2 & -1 \\ 0 & 0 & 0 \\ 1 & 2 & 1 \end{bmatrix}

where :math:`\Delta x = \Delta y = 10.0\,\text{m}`.

Slope:
Derives terrain inclination angle :math:`\beta` in radians:

.. math::

   \text{Gradient Norm} = \sqrt{\left(\frac{\partial Z}{\partial x}\right)^2 + \left(\frac{\partial Z}{\partial y}\right)^2 + 10^{-12}}

.. math::

   \beta = \arctan(\text{Gradient Norm}) \quad [\text{radians}, \beta \in [0, \pi/2]]

Aspect:
Derives compass aspect direction :math:`\alpha` in radians clockwise from North:

.. math::

   \alpha_{\text{raw}} = \text{atan2}\left(-\frac{\partial Z}{\partial y}, -\frac{\partial Z}{\partial x}\right)

.. math::

   \alpha = (\alpha_{\text{raw}} + 2\pi) \pmod{2\pi} \quad [\text{radians}, \alpha \in [0, 2\pi)]

Topographic Wetness Index (TWI)
-------------------------------
Computes local hydraulic accumulation potential:

.. math::

   \text{TWI} = \ln\left(\frac{a}{\tan \beta + \epsilon}\right)

with :math:`\epsilon = 10^{-4}` to prevent singularity on horizontal surfaces. Clamped to :math:`[0.0, 25.0]`.

4-Channel Unified Terrain Tensor
--------------------------------
The final output tensor has shape :math:`(1, 4, 64, 64)` of type ``torch.float32``:
- **Channel 0**: Normalized Elevation :math:`Z_{\text{norm}} \in [0.0, 1.0]`
- **Channel 1**: Slope :math:`\beta \in [0.0, \pi/2]`
- **Channel 2**: Aspect :math:`\alpha \in [0.0, 2\pi)`
- **Channel 3**: Topographic Wetness Index :math:`\text{TWI} \in [0.0, 25.0]`

Requirements Catalog
====================

Functional Requirements
-----------------------
* **FR-PRE-EXT-001**: Resample arbitrary elevation grids to target shape using bilinear interpolation.
* **FR-PRE-EXT-002**: Estimate partial surface derivatives via Horn's weighted :math:`3 \times 3` convolution.
* **FR-PRE-EXT-003**: Calculate physical slope :math:`\beta \in [0, \pi/2]` in radians.
* **FR-PRE-EXT-004**: Calculate compass aspect :math:`\alpha \in [0, 2\pi)` in radians.
* **FR-PRE-EXT-005**: Compute stabilized Topographic Wetness Index with division-by-zero protection.
* **FR-PRE-EXT-006**: Output a stacked 4-channel tensor matching :math:`(1, 4, H, W)`.

Data Integrity Requirements
---------------------------
* **DI-PRE-EXT-001**: Output tensors shall contain zero NaN and zero Inf values.
* **DI-PRE-EXT-002**: Normalized elevation shall strictly span :math:`[0.0, 1.0]`.
* **DI-PRE-EXT-003**: TWI shall be strictly non-negative (:math:`\ge 0.0`).

Verification Results
====================

Empirical Test Execution Evidence
---------------------------------
Verified via automated test ``test_soc_06_copernicus_dem_topographic_integrity`` in ``tests/test_dem_weather_coupling.py``:

.. code-block:: text

   ============================= test session starts =============================
   platform win32 -- Python 3.14.7, pytest-9.1.1
   collected 5 items / 4 deselected / 1 selected

   tests/test_dem_weather_coupling.py::TestDEMWeatherCoupling::test_soc_06_copernicus_dem_topographic_integrity PASSED [100%]

   ======================= 1 passed, 4 deselected in 1.48s =======================

Traceability Matrix
===================

.. list-table::
   :widths: 20 30 30 20
   :header-rows: 1

   * - Requirement
     - Implementation Method
     - Verification Procedure
     - Status
   * - FR-PRE-EXT-001
     - ``DEMTopographyCoupler.resample_to_10m``
     - ``test_soc_06``
     - MET
   * - FR-PRE-EXT-002
     - ``DEMTopographyCoupler.compute_slope_and_aspect``
     - ``test_soc_06``
     - MET
   * - FR-PRE-EXT-003
     - ``DEMTopographyCoupler.compute_slope_and_aspect``
     - ``test_soc_06``
     - MET
   * - FR-PRE-EXT-004
     - ``DEMTopographyCoupler.compute_slope_and_aspect``
     - ``test_soc_06``
     - MET
   * - FR-PRE-EXT-005
     - ``DEMTopographyCoupler.compute_topographic_wetness_index``
     - ``test_soc_06``
     - MET
   * - FR-PRE-EXT-006
     - ``DEMTopographyCoupler.process_dem``
     - ``test_soc_06``
     - MET
   * - DI-PRE-EXT-001
     - ``DEMTopographyCoupler.process_dem``
     - ``test_soc_06``
     - MET

Defect Log and Technical Debt Register
======================================

.. list-table::
   :widths: 15 45 15 25
   :header-rows: 1

   * - Defect ID
     - Description
     - Severity
     - Remediation Plan
   * - D-PRE-EXT-001
     - Preprocessing layer imports from downstream campaign execution engine.
     - HIGH
     - Migrate implementation directly into ``2_data_pipeline/preprocessing/``.
   * - D-PRE-EXT-002
     - Dynamic ``sys.path`` mutation on module load.
     - HIGH
     - Use package installation or absolute project roots.
   * - D-PRE-EXT-003
     - Relative elevation heuristic used as proxy for flow accumulation in TWI.
     - MEDIUM
     - Implement genuine D-infinity hydrological flow accumulation.
   * - D-PRE-EXT-004
     - Replicate padding collapses gradient to zero along 1-pixel border.
     - LOW
     - Document boundary exclusion zone or implement extrapolated padding.
   * - D-PRE-EXT-005
     - Class missing from ``preprocessing/__init__.py`` exports.
     - MEDIUM
     - Export ``DEMTopographyCoupler`` in ``preprocessing/__init__.py``.
