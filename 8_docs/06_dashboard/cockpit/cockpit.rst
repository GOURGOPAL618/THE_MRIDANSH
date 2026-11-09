.. _subsystem_06_dashboard_cockpit:

================================================================================
Subsystem 06: Streamlit Mission Cockpit Specification (6_dashboard/cockpit)
================================================================================

:Central Engine: AETHER-MRID1607X
:Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
:Lead Architect: Gourgopal Mohapatra
:Release Status: FROZEN_OPERATIONAL_RELEASE_v1.0

Executive Overview & Subsystem Mandate
======================================

The ``6_dashboard/cockpit/`` subsystem constitutes the operational command bridge, telemetry visualization hub,
and interactive decision workstation for the **AETHER-MRID1607X** spaceborne earth observation and precision soil
intelligence platform. Operating as the primary graphical interface for field commanders, agronomists, and geotechnical
engineers at the **Jagannath Command Center (JCC Campus 2)**, this module synthesizes multi-modal spaceborne tensor predictions
into deterministic, real-time situational awareness.

Following the project architecture standardization, all cockpit execution modules are consolidated in ``6_dashboard/cockpit/``:

* **app.py** (54.7 KB, 1,024 lines): Master Streamlit cockpit orchestrator, viewport navigator, interactive Leaflet/Folium drawing interface, and Step 2 Telemetry HUD coupling engine.
* **metrics.py** (47.1 KB, 1,073 lines): Typed scientific telemetry and mathematical presentation engine computing agro-hydrological deficits, Crop Water Stress Index (CWSI), and Bekker wheel sinkage dynamics.
* **runtime_cache.py** (16.4 KB, 411 lines): In-memory cache singleton, tensor bridge, and asynchronous REST API fallback manager ensuring zero-mock production parity.
* **__init__.py** (55 B): Package initializer providing seamless workspace symbol resolution.

Cockpit Architecture & Telemetry Pipeline
=========================================

.. code-block:: text

       +-------------------------------------------------------------------------+
       |             SPACEBORNE TENSOR INGESTION & HARMONIZED DATA               |
       |  (9_spaceborne_operational_campaign/.../s1_s2_dem_era5_harmonized_bundle) |
       +------------------------------------+------------------------------------+
                                            |
                                            v
       +-------------------------------------------------------------------------+
       |                      RUNTIME CACHE & ENGINE BRIDGE                      |
       |                      (6_dashboard/cockpit/runtime_cache.py)             |
       |  * Singleton In-Memory Orchestrator (@st.cache_resource)                |
       |  * Decoupled Tensor Extraction & Fast GeoJSON Generator                |
       |  * Asynchronous FastAPI Client Fallback (Port 8000 Polling)             |
       +------------------------------------+------------------------------------+
                                            |
                                            v
       +-------------------------------------------------------------------------+
       |                     STREAMLIT OPERATIONAL COCKPIT                       |
       |                       (6_dashboard/cockpit/app.py)                      |
       |  * Sidebar Navigation & Mission Mode Selection (Live / Campaign / API)  |
       |  * Interactive Folium Dual-Layer Heatmap with Leaflet.draw Bounding Box |
       |  * Step 2: AETHER-MRID1607X Physical State Telemetry HUD                |
       +------------------------------------+------------------------------------+
                                            |
                        +-------------------+-------------------+
                        |                                       |
                        v                                       v
       +---------------------------------+   +---------------------------------+
       |      KISAN WAR ROOM VIEWPORT    |   |    CIVIL GEOTECHNICS VIEWPORT   |
       |  * Volumetric Water Deficit (mm)|   |  * Ultimate Bearing Cap (kPa)   |
       |  * CWSI Crop Water Stress Index |   |  * Bekker Wheel Rut Depth (cm)  |
       |  * Tala Gachha Tree Protection  |   |  * Heavy Machinery Traffic Risk |
       |  * Odia/English Tactical Alerts |   |  * Foundation Stability Grade   |
       +---------------------------------+   +---------------------------------+

Mathematical Formulations & Geotechnical Physics
================================================

Volumetric Soil Water Deficit
-----------------------------

To advise smallholder farmers on precise irrigation requirements without over-saturating the root zone,
``metrics.py`` calculates the volumetric water deficit:

.. math::

   \Delta V_{\text{water}} = \max\left(0.0, \; (\theta_{\text{field\_capacity}} - \theta_{\text{measured}}) \cdot z_{\text{root}} \cdot 1000\right) \quad [\text{mm}]

Where:
* :math:`\theta_{\text{measured}}`: Root-zone moisture fraction (:math:`\text{m}^3/\text{m}^3`) estimated by AETHER-MRID1607X.
* :math:`\theta_{\text{field\_capacity}}`: Soil-texture-dependent field capacity threshold (default :math:`0.32\text{ m}^3/\text{m}^3`).
* :math:`z_{\text{root}}`: Active rooting depth (default :math:`0.40\text{ m}`).

Crop Water Stress Index (CWSI)
------------------------------

The Crop Water Stress Index represents transpiration deficit normalized between 0.0 and 1.0:

.. math::

   \text{CWSI} = \max\left(0.0, \; \min\left(1.0, \; 1.0 - \frac{\theta_{\text{measured}} - \theta_{\text{wilt}}}{\theta_{\text{field\_capacity}} - \theta_{\text{wilt}}}\right)\right)

Bekker-Wong Soil Sinkage & Wheel Rut Depth
------------------------------------------

For heavy agricultural tractors and construction vehicles operating on soft alluvial terrain, ``metrics.py`` implements
the Bekker-Wong semi-empirical pressure-sinkage formulation:

.. math::

   p = \left(\frac{k_c}{b} + k_\phi\right) z^n \implies z_{\text{rut}} = \left(\frac{p}{\frac{k_c}{b} + k_\phi}\right)^{\frac{1}{n}} \cdot 100 \quad [\text{cm}]

Non-Parametric Quantile Slicing
-------------------------------

Spatial layer statistics are calculated across valid unmasked pixels :math:`\mathcal{M}`:

.. math::

   p_{10} = \mathcal{Q}(0.10, \mathbf{X}_\mathcal{M}), \quad p_{50} = \text{median}(\mathbf{X}_\mathcal{M}), \quad p_{90} = \mathcal{Q}(0.90, \mathbf{X}_\mathcal{M})

Brutally Honest Engineering Disclosures ("Ek Ek Dhappa")
========================================================

1. **Streamlit Reactive Lifecycle**: Every widget interaction re-executes ``app.py`` top-to-bottom. While ``@st.cache_resource`` protects neural weights, DOM reconciliation incurs :math:`200\text{ ms} - 450\text{ ms}` latency per cycle.
2. **Numeric Directory Import Workarounds**: Because Python disallows module identifiers starting with numbers, ``app.py`` relies on ``importlib.util.spec_from_file_location`` inside ``get_zonal_extractor()``.
3. **Leaflet.draw Iframe Reset**: Switching layers in the sidebar causes an iframe reload in ``streamlit-folium``, resetting uncommitted polygon drawings.
4. **Homogeneous Bekker Moduli**: The sinkage formulation assumes uniform soil moduli across the field, neglecting localized micro-topographical softening in coastal Odisha alluvial soils.
5. **Surrogate CWSI**: Moisture-derived CWSI exhibits a 2-4 hour response lag compared to real-time infrared canopy thermal differentials during midday heat waves.

Traceable Functional Requirements
=================================

.. list-table::
   :widths: 20 20 25 35
   :header-rows: 1

   * - Requirement ID
     - Verification Type
     - Target Module
     - Technical Specification
   * - **REQ-DASH-COCK-01**
     - Functional Test
     - ``cockpit/app.py``
     - Cockpit initializes in wide layout, loads ``assets/style.css``, and renders aerospace header.
   * - **REQ-DASH-COCK-02**
     - Integration Test
     - ``cockpit/app.py``
     - Interactive Folium Leaflet canvas displays 10m GSD heatmaps with layer controls.
   * - **REQ-DASH-COCK-03**
     - Unit Test
     - ``cockpit/metrics.py``
     - ``build_agronomy_metrics`` computes water deficit and CWSI bounded in :math:`[0.0, 1.0]`.
   * - **REQ-DASH-COCK-04**
     - Unit Test
     - ``cockpit/metrics.py``
     - ``build_civil_metrics`` computes bearing capacity and Bekker sinkage rut depth.
   * - **REQ-DASH-COCK-05**
     - Integration Test
     - ``cockpit/runtime_cache.py``
     - Master orchestrator loads and caches ``s1_s2_dem_era5_harmonized_bundle.pt`` without mock data.
   * - **REQ-DASH-COCK-06**
     - Performance Test
     - ``cockpit/runtime_cache.py``
     - ``FastAPIClient`` polls ``/health`` with max 2.0s timeout and falls back to in-memory execution.
   * - **REQ-DASH-COCK-07**
     - Mathematical Test
     - ``cockpit/metrics.py``
     - Layer summaries compute exact non-parametric :math:`p_{10}, p_{50}, p_{90}` quantiles.
   * - **REQ-DASH-COCK-08**
     - Geometry Test
     - ``cockpit/app.py``
     - Leaflet.draw polygon coordinates convert to pixel masks via ``get_zonal_extractor()``.
