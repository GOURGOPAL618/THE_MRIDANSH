.. _subsystem_04_agronomy:

================================================================================
Subsystem 04: Precision Agronomy & FAO-56 Engine (4_domain_translators/agronomy)
================================================================================

:Central Engine: AETHER-MRID1607X
:Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
:Lead Architect: Gourgopal Mohapatra
:Release Status: FROZEN_OPERATIONAL_RELEASE_v1.0

Executive Overview & Subsystem Mandate
======================================

The ``4_domain_translators/agronomy/`` subsystem is the physics-grounded agricultural intelligence engine of the
**AETHER-MRID1607X** platform. Operating downstream of the core soil hydrology tensors (``3_core_engine/``), this
module implements the complete **FAO-56 Dual Crop Coefficient** evapotranspiration framework (Allen et al., 1998),
coupled with **Saxton & Rawls (2006) Pedotransfer Functions**, **Gutman & Ignatov (1998) Dynamic Phenology**, and
**Conformal Uncertainty-Bounded Variable Rate Irrigation (VRI)** prescription synthesis.

Architecture & Module Pipeline
==============================

.. code-block:: text

       +-------------------------------------------------------------------------+
       |              UNIFIED SOIL STATE & OPTICAL REFLECTANCE INPUTS            |
       |  * Root-Zone Moisture (theta_rz), Surface Moisture (theta_surf)         |
       |  * Conformal Uncertainty (±2sigma), Optical NDVI / NIR-Red Reflectance  |
       +------------------------------------+------------------------------------+
                                            |
                                            v
       +-------------------------------------------------------------------------+
       |                    AGRONOMY DOMAIN ENGINE PIPELINE                      |
       |                     (agronomy_domain_engine.py)                         |
       +------------------------------------+------------------------------------+
                                            |
         +----------------------------------+----------------------------------+
         |                                  |                                  |
         v                                  v                                  v
+-----------------------+        +-----------------------+        +-----------------------+
|  SOIL RESERVOIR       |        |  DYNAMIC PHENOLOGY    |        |  FAO-56 DUAL Kc       |
| (soil_water_          |        | (dynamic_phenology.py)|        | (fao56_dual_kc.py)    |
|  reservoir.py)        |        | * Gutman-Ignatov fc   |        | * Stage 1/2 Soil Evap |
| * Saxton-Rawls PTF    |        | * Dynamic Root Depth  |        |   Reduction (Kr)      |
| * TAW & RAW [mm]      |        |   Zr(fc) Deepening    |        | * Kc = Kcb + Ke       |
+-----------+-----------+        +-----------+-----------+        +-----------+-----------+
            |                                |                                |
            +--------------------------------+--------------------------------+
                                             |
                                             v
       +-------------------------------------------------------------------------+
       |           WATER STRESS & CONFORMAL VRI PRESCRIPTION DISPATCH            |
       |  * CropWaterStressEngine: Depletion (Dr), Ks, CWSI = 1 - Ks             |
       |  * PrecisionIrrigationEngine: Net/Gross Irrigation (mm & L/ha)          |
       |  * ConformalRiskDispatcher: [I_min, I_nom, I_max] Risk Bounds           |
       +-------------------------------------------------------------------------+

Mathematical Formulations & Agronomic Physics
=============================================

Soil Water Reservoir (TAW & RAW)
--------------------------------

Given soil hydraulic bounds (:math:`\theta_{\text{fc}}, \theta_{\text{wp}}`) from Saxton-Rawls pedotransfer functions or
12 USDA texture presets:

.. math::

   TAW = 1000 \cdot (\theta_{\text{fc}} - \theta_{\text{wp}}) \cdot Z_r \quad [\text{mm}], \qquad RAW = p \cdot TAW \quad [\text{mm}]

Dynamic Phenology & FAO-56 Dual Crop Coefficient
------------------------------------------------

Fractional canopy cover :math:`f_c` and dynamic rooting depth :math:`Z_r` are computed from NDVI:

.. math::

   f_c = \text{clip}\left(\frac{\text{NDVI} - \text{NDVI}_{\text{bare}}}{\text{NDVI}_{\text{full}} - \text{NDVI}_{\text{bare}}}, \; 0.0, \; 1.0\right), \quad Z_r(f_c) = Z_{r,\min} + (Z_{r,\max} - Z_{r,\min}) \cdot f_c^\gamma

.. math::

   K_e = \min\left(K_r \cdot (K_{c,\max} - K_{cb}), \; (1 - f_c) \cdot K_{c,\max}\right), \quad ET_c = (K_{cb} + K_e) \cdot ET_0

Crop Water Stress Index (CWSI)
------------------------------

.. math::

   D_r = 1000 \cdot (\theta_{\text{fc}} - \theta_{\text{rz}}) \cdot Z_r, \quad K_s = \text{clip}\left(\frac{TAW - D_r}{TAW - RAW}, \; 0.0, \; 1.0\right), \quad \text{CWSI} = 1.0 - K_s

Brutally Honest Engineering Disclosures ("Ek Ek Dhappa")
========================================================

1. **Saxton-Rawls Non-Saline Mineral Soil Assumption**: Empirical PTF regressions lose accuracy in coastal Odisha saline-alkali soils where osmotic potential restricts water uptake.
2. **Uniform Texture Grid Fallbacks**: When continuous sand/clay maps are absent, ``generate_spatial_reservoir_map`` broadcasts a uniform texture preset, flattening micro-topographical sand/clay heterogeneity.
3. **Optical NDVI Saturation & Cloud Artifacts**: Gutman-Ignatov :math:`f_c` saturates at :math:`\text{NDVI} \ge 0.80` in dense paddy canopies and underestimates transpiration under cloud haze.
4. **Single-Layer Bucket Root-Zone Depletion**: Aggregates :math:`[0, Z_r]` into one bulk bucket :math:`D_r`, ignoring preferential upper-root-zone extraction profiles.
5. **Symmetric Conformal Uncertainty Bounds**: Applies symmetric :math:`\theta_{\text{rz}} \pm 2\sigma` bounds, neglecting error distribution skewness near wilting or saturation boundaries.

Traceable Functional Requirements
=================================

.. list-table::
   :widths: 20 20 25 35
   :header-rows: 1

   * - Requirement ID
     - Verification Type
     - Target Module
     - Technical Specification
   * - **REQ-AGRO-01**
     - Physics Test
     - ``soil_water_reservoir.py``
     - Strictly enforces :math:`0 \le \theta_{\text{res}} \le \theta_{\text{wp}} < \theta_{\text{fc}} < \theta_{\text{sat}} \le 1` and :math:`RAW \le TAW`.
   * - **REQ-AGRO-02**
     - Unit Test
     - ``dynamic_phenology.py``
     - Computes bounded :math:`f_c \in [0, 1]` and :math:`Z_r \in [Z_{r,\min}, Z_{r,\max}]` without NaNs.
   * - **REQ-AGRO-03**
     - Physics Test
     - ``fao56_dual_kc.py``
     - Bounds :math:`K_e \le (1 - f_c) K_{c,\max}` and satisfies :math:`K_c = K_{cb} + K_e`.
   * - **REQ-AGRO-04**
     - Unit Test
     - ``crop_water_stress.py``
     - Computes :math:`K_s \in [0, 1]` and :math:`\text{CWSI} = 1 - K_s` with zero-division protection.
   * - **REQ-AGRO-05**
     - Integration Test
     - ``irrigation_prescription.py``
     - Computes non-negative net and gross irrigation accounting for application efficiency.
   * - **REQ-AGRO-06**
     - Risk Audit
     - ``conformal_risk_dispatcher.py``
     - Monotonically satisfies :math:`I_{\min} \le I_{\text{nom}} \le I_{\max}` across all valid pixels.
   * - **REQ-AGRO-07**
     - Export Test
     - ``agronomic_geotiff_exporter.py``
     - Exports 4-band COG stacks with SHA-256 provenance and Windows lock safety.
   * - **REQ-AGRO-08**
     - Regression Test
     - ``verify_phase*.py``
     - All 4 phase verification suites pass deterministic physics and boundary checks.
