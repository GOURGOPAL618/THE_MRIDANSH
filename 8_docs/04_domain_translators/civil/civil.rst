.. _subsystem_04_civil:

================================================================================
Subsystem 04: Civil Geotechnics & Soil Mechanics (4_domain_translators/civil)
================================================================================

:Central Engine: AETHER-MRID1607X
:Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
:Lead Architect: Gourgopal Mohapatra
:Release Status: FROZEN_OPERATIONAL_RELEASE_v1.0

Executive Overview & Subsystem Mandate
======================================

The ``4_domain_translators/civil/`` subsystem constitutes the unsaturated soil mechanics, foundation bearing
capacity, slope stability, drainage intelligence, and dynamic disaster simulation engine for the **AETHER-MRID1607X**
platform. Operating downstream of ``3_core_engine/`` volumetric moisture and uncertainty tensors, this subsystem
applies unsaturated geotechnical engineering laws—specifically **van Genuchten (1980)** matric suction,
**Fredlund & Morgenstern** extended shear strength, **Meyerhof-Hansen** bearing capacity, **Infinite Slope**
stability, and **Beven-Kirkby Topographic Wetness Index (TWI)**—to evaluate infrastructure trafficability and structural risk.

Architecture & Geotechnical Pipeline
====================================

.. code-block:: text

       +-------------------------------------------------------------------------+
       |              UNIFIED SOIL STATE & DEM TOPOGRAPHY INPUTS                 |
       |  * Volumetric Moisture (theta_surf, theta_rz), Conformal Uncertainty ±2σ|
       |  * Copernicus 30m / 10m Resampled DEM Elevation Grid                    |
       +------------------------------------+------------------------------------+
                                            |
                                            v
       +-------------------------------------------------------------------------+
       |                 SOIL MECHANICS CORE (soil_mechanics_core.py)            |
       |  * van Genuchten Analytical Matric Suction Inversion (psi <= 10 MPa)    |
       |  * Bishop Effective Stress & Fredlund Apparent Cohesion                 |
       |  * 3-Horizon Stratification (Skin, Subbase, Foundation)                 |
       +------------------------------------+------------------------------------+
                                            |
         +----------------------------------+----------------------------------+
         |                                  |                                  |
         v                                  v                                  v
+-----------------------+        +-----------------------+        +-----------------------+
|  GROUND STABILITY     |        |  SLOPE STABILITY      |        |  DRAINAGE & TWI       |
| (ground_stability_    |        | (slope_stability_     |        | (drainage_            |
|  engine.py)           |        |  engine.py)           |        |  intelligence.py)     |
| * Meyerhof-Hansen     |        | * Infinite Slope FS   |        | * D8 Runoff Direction |
|   Nc, Nq, Ngamma      |        | * Flat Guard (0.5 deg)|        | * Specific Catchment  |
| * q_ult & q_allow     |        | * Landslide Hazard    |        | * TWI = ln(a/tan B)   |
+-----------------------+        +-----------------------+        +-----------------------+

Mathematical Formulations & Geotechnical Physics
================================================

Unsaturated Matric Suction & Fredlund Shear Strength
----------------------------------------------------

Using effective saturation :math:`S_e`, matric suction :math:`\psi` (kPa) and apparent cohesion :math:`c_{\text{app}}` are derived:

.. math::

   \psi(S_e) = \frac{1}{\alpha} \left( S_e^{-1/m} - 1 \right)^{1/n} \cdot 0.0980665, \quad c_{\text{app}} = c' + \psi \cdot \tan(\phi^b)

Meyerhof-Hansen Bearing Capacity
--------------------------------

.. math::

   q_{\text{ult}} = c_{\text{app}} N_c s_c d_c + q N_q s_q d_q + 0.5 \gamma_{\text{sat}} B N_\gamma s_\gamma d_\gamma, \qquad q_{\text{allow}} = \frac{q_{\text{ult}}}{FS}

Infinite Slope Factor of Safety
-------------------------------

.. math::

   FS = \frac{c' + (\gamma_{\text{sat}} z \cos^2\beta - u_w)\tan(\phi')}{\gamma_{\text{sat}} z \sin(\beta)\cos(\beta)}, \quad u_w = -\psi

Topographic Wetness Index (TWI)
-------------------------------

.. math::

   \text{TWI} = \text{clip}\left(\ln\left(\frac{a}{\tan\beta}\right), \; 2.0, \; 20.0\right)

Brutally Honest Engineering Disclosures ("Ek Ek Dhappa")
========================================================

1. **Field Assignment Quirk in scenario_simulator.py (Line 154)**: ``simulate_heavy_rainfall`` populates ``matric_suction_simulated_kpa`` using ``post_bearing.apparent_cohesion_kpa`` rather than raw matric suction.
2. **1D Planar Slide vs Circular Slip**: ``SlopeStabilityEngine`` uses a 1D infinite planar equation, neglecting circular rotational failures (Bishop/Spencer slices) in cohesive clays.
3. **Flat-Terrain Singularity Clamp**: When :math:`\beta < 0.5^\circ`, dividing by :math:`\sin(\beta)` diverges; the engine clamps flat zones to ``MAX_FS_CLAMP = 10.0``.
4. **van Genuchten Asymptotic Clipping**: Suction is capped at ``MAX_SUCTION_KPA = 10000.0`` (10 MPa) to prevent divergence near residual moisture.
5. **No In-Situ Boreholes or Seismic PGA**: Bearing capacities extrapolate from surface moisture and static presets; real foundation design requires physical SPT/CPT borehole logs.

Traceable Functional Requirements
=================================

.. list-table::
   :widths: 20 20 25 35
   :header-rows: 1

   * - Requirement ID
     - Verification Type
     - Target Module
     - Technical Specification
   * - **REQ-CIV-01**
     - Physics Test
     - ``soil_mechanics_core.py``
     - Matric suction remains non-negative and bounded within :math:`[0.0, 10000.0]\text{ kPa}`.
   * - **REQ-CIV-02**
     - Invariant Test
     - ``ground_stability_engine.py``
     - Enforces :math:`q_{\text{ult}} > 0`, :math:`q_{\text{allow}} > 0`, and :math:`q_{\text{ult}} / q_{\text{allow}} = FS`.
   * - **REQ-CIV-03**
     - Boundary Test
     - ``slope_stability_engine.py``
     - Clamps Factor of Safety within :math:`[0.10, 10.0]` and guards flat slopes (:math:`< 0.5^\circ`).
   * - **REQ-CIV-04**
     - Terrain Test
     - ``drainage_intelligence.py``
     - Clamps Topographic Wetness Index within :math:`[2.0, 20.0]` without division-by-zero.
   * - **REQ-CIV-05**
     - Simulation Test
     - ``scenario_simulator.py``
     - Heavy rainfall simulation decreases bearing capacity monotonically with rising saturation.
   * - **REQ-CIV-06**
     - Mobility Test
     - ``scenario_simulator.py``
     - Classifies terrain into Passable, Marginal, and Quagmire zones via contact pressures.
   * - **REQ-CIV-07**
     - Risk Audit
     - ``conformal_geotechnical_risk.py``
     - Propagates :math:`\pm 2\sigma` uncertainty into conservative bearing capacity bounds.
   * - **REQ-CIV-08**
     - Export Test
     - ``civil_geotiff_exporter.py``
     - Writes 4-band COG GeoTIFF stacks with SHA-256 checksums and Windows lock safety.
