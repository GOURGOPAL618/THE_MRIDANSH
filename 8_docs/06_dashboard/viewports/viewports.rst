.. _subsystem_06_dashboard_viewports:

================================================================================
Subsystem 06: Domain Command Viewports Specification (6_dashboard/viewports)
================================================================================

:Central Engine: AETHER-MRID1607X
:Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
:Lead Architect: Gourgopal Mohapatra
:Release Status: FROZEN_OPERATIONAL_RELEASE_v1.0

Executive Overview & Subsystem Mandate
======================================

The ``6_dashboard/viewports/`` subsystem houses the specialized domain decision viewports for the
**AETHER-MRID1607X** spaceborne earth observation and precision soil intelligence platform. Operating as the
mission-specific graphical user interfaces embedded within the Streamlit Mission Cockpit (``6_dashboard/cockpit/app.py``),
this subsystem translates raw physical soil state predictions into domain-tailored operational workspaces:

1. **Agronomy Command & Soil Health Viewport (agronomy_view.py)**: Renders vadose-zone moisture depth stratigraphy (:math:`0-100\text{ cm}`), theoretical irrigation water deficits, Crop Water Stress Index (CWSI), soil macronutrient status, and interactive rainfall scenario simulations.
2. **Civil & Ground Stability Command Viewport (civil_view.py)**: Renders geotechnical ground stability scores, pore water pressure estimations, dry bulk density, 3D subsurface stratification meshes, and heavy equipment trafficability advisories.

The primary mandate of the viewports subsystem is to enforce **strict scientific integrity, defensive error handling, and transparent operational boundaries**. Rather than masking data pipeline disconnections with synthetic mockups, the viewports render explicit, typed data states (``LIVE_ESTIMATE``, ``DEMO_FALLBACK``, ``UNAVAILABLE``) and display prominent safety banners to prevent dangerous real-world misapplications.

Viewport Module Architecture & Responsibilities
===============================================

.. code-block:: text

       +-------------------------------------------------------------------------+
       |             PHYSICAL TENSOR PREDICTIONS & UNIFIED SOIL STATE            |
       |                   (AETHER-MRID1607X Core Engine Output)                 |
       +------------------------------------+------------------------------------+
                                            |
                                            v
       +-------------------------------------------------------------------------+
       |                    SUBSYSTEM 06 VIEWPORTS ENGINE                        |
       |                     (6_dashboard/viewports/)                            |
       +------------------------------------+------------------------------------+
                                            |
                    +-----------------------+-----------------------+
                    |                                               |
                    v                                               v
+---------------------------------------+       +---------------------------------------+
|      AGRONOMY COMMAND VIEWPORT        |       |       CIVIL COMMAND VIEWPORT          |
|         (agronomy_view.py)            |       |          (civil_view.py)              |
+---------------------------------------+       +---------------------------------------+
| * Root-Zone Moisture (m³/m³)          |       | * Ground Stability Index (0-100%)     |
| * Crop Health & Irrigation Deficit    |       | * Pore Water Pressure (kPa)           |
| * 5-Node Moisture Depth Curve (0-1m)  |       | * Dry Bulk Density (g/cm³)            |
| * Biogeochemical NPK Disclaimers      |       | * 3D Subsurface Stratification Mesh   |
| * What-If Rainfall Scenario Simulator |       | * Heavy Equipment Traffic Advisory    |
+---------------------------------------+       +---------------------------------------+
                    |                                               |
                    +-----------------------+-----------------------+
                                            |
                                            v
       +-------------------------------------------------------------------------+
       |                  DEFENSIVE DATA INTEGRITY GUARDS                        |
       |  * Typed DashboardMetric Contract Validation                            |
       |  * Mandatory "NOT FOR FIELD / ENGINEERING USE" Safety Banners           |
       |  * Uncalibrated Fallback Watermarks & Explicit "Unavailable" Badges     |
       +-------------------------------------------------------------------------+

Mathematical Formulations & Heuristic Models
============================================

Agronomic What-If Infiltration Heuristic
----------------------------------------

To provide an educational preview of topsoil moisture response to precipitation, ``agronomy_view.py`` implements
a depth-attenuated empirical infiltration heuristic:

.. math::

   \theta_{\text{sim}}(z) = \text{clip}\left(\theta_{\text{raw}}(z) + \frac{P_{\text{rain}} \cdot \beta_{\text{inf}}}{\frac{z}{10}}, \; \theta_{\text{res}}, \; \theta_{\text{sat}}\right)

Where:
* :math:`P_{\text{rain}}`: Simulated rainfall depth (:math:`0 \le P_{\text{rain}} \le 100\text{ mm}`).
* :math:`\beta_{\text{inf}} = 0.0025\text{ m}^{-1}`: Empirical infiltration scaling coefficient.
* :math:`z`: Soil depth node in centimeters (:math:`z \in \{5, 15, 30, 60, 100\}\text{ cm}`).
* :math:`\theta_{\text{res}} = 0.05\text{ m}^3/\text{m}^3` and :math:`\theta_{\text{sat}} = 0.48\text{ m}^3/\text{m}^3`.

Theoretical Irrigation Deficit (L/ha)
-------------------------------------

The volumetric irrigation volume required to restore the top :math:`40\text{ cm}` root zone to target field capacity
(:math:`\theta_{\text{target}} = 0.35\text{ m}^3/\text{m}^3`) is calculated as:

.. math::

   V_{\text{irrig}} = \max\left(0.0, \; (\theta_{\text{target}} - \theta_{\text{measured}}) \cdot z_{\text{root}} \cdot 10{,}000{,}000\right) \quad [\text{L/ha}]

Geotechnical Factor of Safety (FS) Benchmark
--------------------------------------------

``civil_view.py`` mandates standard geotechnical safety margins:

.. math::

   FS = \frac{q_{\text{ult}}}{q_{\text{allow}}} \ge 3.0

Brutally Honest Engineering Disclosures ("Ek Ek Dhappa")
========================================================

1. **Heuristic Rainfall Infiltration vs Richards PDE**: The rainfall simulator uses a simplified depth-attenuated linear formula. It does **not** solve the non-linear 1D Richards PDE and ignores hysteretic suction transitions.
2. **Absence of In-Situ NPK Chemical Sensors**: Satellites cannot measure biochemical macronutrients (N, P, K). Automated commercial fertilizer application guidance is completely suppressed.
3. **Geotechnical Surface Extrapolation Limits**: Spaceborne sensors penetrate only :math:`5-10\text{ cm}`. Extrapolating foundation bearing capacity or deep slope stability without rotary boreholes is physically invalid.
4. **Transparent Disconnected States**: When the core inference pipeline is offline, viewports render explicit ``Unavailable`` and ``DISCONNECTED`` badges rather than hallucinating plausible values.
5. **Fixed 5-Node Depth Discretization**: Depth profiles hardcode nodes :math:`z \in \{5, 15, 30, 60, 100\}\text{ cm}`, which cannot resolve localized hardpan compaction layers at intermediate depths (:math:`18-25\text{ cm}`).

Traceable Functional Requirements
=================================

.. list-table::
   :widths: 20 20 25 35
   :header-rows: 1

   * - Requirement ID
     - Verification Type
     - Target Module
     - Technical Specification
   * - **REQ-DASH-VIEW-01**
     - Functional Test
     - ``agronomy_view.py``
     - Agronomy viewport shall consume typed ``DashboardMetric`` contracts and render 4 KPI cards.
   * - **REQ-DASH-VIEW-02**
     - Integration Test
     - ``agronomy_view.py``
     - Viewport shall render 5-node vadose depth curve and horizon breakdowns when tensors connect.
   * - **REQ-DASH-VIEW-03**
     - Safety Audit
     - ``agronomy_view.py``
     - Viewport shall display NPK disconnection notices and suppress commercial fertilizer guidance.
   * - **REQ-DASH-VIEW-04**
     - Interactive Test
     - ``agronomy_view.py``
     - What-If slider (:math:`0-100\text{ mm}`) shall recompute simulated infiltration curves.
   * - **REQ-DASH-VIEW-05**
     - Functional Test
     - ``civil_view.py``
     - Civil viewport shall render 4 geotechnical KPI cards with explicit data states.
   * - **REQ-DASH-VIEW-06**
     - Integration Test
     - ``civil_view.py``
     - Viewport shall render 3D subsurface mesh and angular ground stability gauge without error.
   * - **REQ-DASH-VIEW-07**
     - Safety Audit
     - ``civil_view.py``
     - Viewport shall enforce heavy equipment advisories mandating :math:`FS \ge 3.0` and borehole logs.
   * - **REQ-DASH-VIEW-08**
     - Integrity Test
     - ``viewports/*.py``
     - Both viewports shall mount persistent safety banners whenever ``is_demo=True``.
