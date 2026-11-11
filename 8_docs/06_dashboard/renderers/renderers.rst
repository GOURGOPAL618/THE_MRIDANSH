.. _subsystem_06_dashboard_renderers:

================================================================================
Subsystem 06: Spatial Layer & Scientific Chart Renderers (6_dashboard/renderers)
================================================================================

:Central Engine: AETHER-MRID1607X
:Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
:Lead Architect: Gourgopal Mohapatra
:Release Status: FROZEN_OPERATIONAL_RELEASE_v1.0

Executive Overview & Subsystem Mandate
======================================

The ``6_dashboard/renderers/`` subsystem constitutes the multi-dimensional cartographic, spatial raster,
and scientific chart rendering engine for the **AETHER-MRID1607X** earth observation and precision soil
intelligence platform. Operating as the visual abstraction and geospatial graphics backend for the Streamlit
Mission Cockpit (``6_dashboard/cockpit/app.py``), this subsystem transforms multi-spectral tensor predictions,
Digital Elevation Models (DEM), and geotechnical telemetry into interactive, publication-grade Web GIS layers
and Plotly visualizations.

The mandate of the renderers subsystem is to provide deterministic, zero-hallucination visualization primitives:

* **Interactive 2D Web GIS**: High-resolution Folium/Leaflet mapping with satellite hybrid basemaps, georeferenced raster overlays, and vector AOI selection.
* **3D Topographic Terrain Meshes**: Dynamic WebGL surface contouring mapping predicted soil properties across 10m DEM elevation grids with configurable relief exaggeration.
* **Scientific Depth & Geotechnical Instrumentation**: Calibrated 2D vadose-zone depth curves, macronutrient concentration profiles, and ground stability angular gauges with explicit empty-state safeguards.

Renderer Module Inventory & Architecture
=========================================

.. code-block:: text

       +-------------------------------------------------------------------------+
       |             PHYSICAL TENSOR PREDICTIONS & SPATIAL DATA                  |
       |             (AETHER-MRID1607X Output, DEM 10m, Soil Telemetry)          |
       +------------------------------------+------------------------------------+
                                            |
                                            v
       +-------------------------------------------------------------------------+
       |                    SUBSYSTEM 06 RENDERERS ENGINE                        |
       |                     (6_dashboard/renderers/)                            |
       +------------------------------------+------------------------------------+
                                            |
         +----------------------------------+----------------------------------+
         |                                  |                                  |
         v                                  v                                  v
+-----------------------+        +-----------------------+        +-----------------------+
|  2D WEB GIS ENGINE    |        |  3D TERRAIN MESHES    |        |  SCIENTIFIC CHARTS    |
| (map_renderers.py)    |        | (surface_3d.py)       |        | (chart_renderers.py)  |
| * Permanent Google    |        | * Plotly go.Surface   |        | * Moisture vs Depth   |
|   Maps Hybrid Tiles   |        | * DEM 10m Elevation   |        | * N-P-K Concentration |
| * Layer Controls      |        | * Configurable Relief |        | * Ground Stability    |
| * Fullscreen & Scale  |        |   Exaggeration (1.5x) |        |   Angular Gauge       |
+-----------+-----------+        +-----------------------+        +-----------+-----------+
            |                                                                 |
            v                                                                 v
+-----------------------+                                         +-----------------------+
|  RASTER & AOI TOOLS   |                                         |  DEFENSIVE WATERMARK  |
| (raster_overlays.py)  |                                         | * Honest Empty-States |
| * Georeferenced PNG   |                                         | * (DEMO DATA) Notices |
|   ImageOverlay Arrays |                                         | * Zero-Data Fallbacks |
| (aoi_selector.py)     |                                         +-----------------------+
| * Leaflet.draw Vector |
| * GeoJSON Extraction  |
+-----------------------+

Mathematical Formulations & Spatial Algorithms
================================================

Equirectangular Surface Area Approximation
------------------------------------------

For fast, zero-dependency area computation of user-drawn polygons, ``aoi_selector.py`` implements an
equirectangular flat-earth approximation tailored for the Kendrapara/Odisha latitude band (:math:`\phi \approx 20.3^\circ \text{N}`):

.. math::

   \Delta y = (\text{lat}_{\max} - \text{lat}_{\min}) \cdot 111{,}000 \quad [\text{m}]

.. math::

   \Delta x = (\text{lon}_{\max} - \text{lon}_{\min}) \cdot 111{,}000 \cdot \cos(\phi_0) \quad [\text{m}], \quad \cos(20^\circ) \approx 0.939

.. math::

   A_{\text{sqm}} = |\Delta y \cdot \Delta x| \quad [\text{m}^2], \qquad A_{\text{hectares}} = \frac{A_{\text{sqm}}}{10{,}000}

Dynamic Colormap Normalization
------------------------------

When converting floating-point soil state matrices :math:`\mathbf{X} \in \mathbb{R}^{H \times W}` into georeferenced RGBA raster overlays,
``raster_overlays.py`` applies continuous linear scaling across the valid scalar domain:

.. math::

   \tilde{x}_{i,j} = \frac{x_{i,j} - x_{\min}}{\max(x_{\max} - x_{\min}, \; \epsilon)}, \quad \epsilon = 10^{-6}

.. math::

   \mathbf{C}_{i,j} = \mathcal{F}_{\text{colormap}}(\tilde{x}_{i,j}) \in [0, 255]^4 \quad (\text{RGBA})

3D Topographic Mesh Coordinates
-------------------------------

Terrain surfaces are computed over discrete integer indices :math:`(i, j)` corresponding to tensor dimensions :math:`H \times W`:

.. math::

   X_{i, j} = j \cdot \Delta s, \quad Y_{i, j} = (H - 1 - i) \cdot \Delta s, \quad Z_{\text{display}}(i, j) = Z_{\text{DEM}}(i, j) \cdot \alpha_{\text{exag}}

Where :math:`\Delta s = 10.0\text{ m}` and :math:`\alpha_{\text{exag}} = 1.5` (default vertical exaggeration factor).

Brutally Honest Engineering Disclosures ("Ek Ek Dhappa")
========================================================

1. **WebGL Context Memory Leaks**: Plotly WebGL contexts (``surface_3d.py``) are not actively garbage-collected on Streamlit script re-runs. 40–50 consecutive re-runs can crash client browser tabs with WebGL context exhaustion errors.
2. **Equirectangular Flat-Earth Distortion**: ``aoi_selector.py`` uses a fixed :math:`\cos(20^\circ) \approx 0.939` scalar. While accurate within :math:`\pm 1.2\%` in Kendrapara, distortion scales significantly at higher latitudes.
3. **CPU-Bound RGBA Pixel Loops**: ``raster_overlays.py`` iterates nested Python loops to map colormaps. While negligible for :math:`64 \times 64` grids (:math:`12\text{ ms}`), scaling to :math:`512 \times 512` blocks the UI thread for :math:`>750\text{ ms}`.
4. **Hardcoded Google Maps Tile URIs**: ``map_renderers.py`` relies on live Google Maps tile endpoints. Field deployments without internet connectivity experience gray tile blackouts without an offline MBTiles cache.
5. **Defensive Demo Watermarking**: ``chart_renderers.py`` explicitly watermarks uncalibrated data as ``(DEMO DATA — NOT CALIBRATED)``, preventing field commanders from confusing simulations with flight telemetry.

Traceable Functional Requirements
=================================

.. list-table::
   :widths: 20 20 25 35
   :header-rows: 1

   * - Requirement ID
     - Verification Type
     - Target Module
     - Technical Specification
   * - **REQ-DASH-REND-01**
     - Functional Test
     - ``map_renderers.py``
     - GIS map renderer shall initialize Folium map anchored at Kendrapara with Google Maps Hybrid base.
   * - **REQ-DASH-REND-02**
     - Integration Test
     - ``aoi_selector.py``
     - AOI selector shall embed Leaflet.draw toolbar with polygon intersection error prevention.
   * - **REQ-DASH-REND-03**
     - Unit Test
     - ``aoi_selector.py``
     - GeoJSON parser shall extract bounding box and equirectangular area in hectares.
   * - **REQ-DASH-REND-04**
     - Unit Test
     - ``raster_overlays.py``
     - Raster overlay engine shall convert 2D NumPy arrays to georeferenced RGBA PNG overlays.
   * - **REQ-DASH-REND-05**
     - Mathematical Test
     - ``raster_overlays.py``
     - Engine shall prevent division-by-zero crashes when matrix dynamic range is near zero.
   * - **REQ-DASH-REND-06**
     - Performance Test
     - ``surface_3d.py``
     - 3D renderer shall generate Plotly terrain surface decoupling DEM geometry from soil colors.
   * - **REQ-DASH-REND-07**
     - Integration Test
     - ``chart_renderers.py``
     - Moisture profile chart shall render depth curves with explicit empty-state fallbacks.
   * - **REQ-DASH-REND-08**
     - Safety Audit
     - ``chart_renderers.py``
     - Stability gauge and NPK charts shall stamp ``(DEMO DATA)`` when uncalibrated flags are active.
