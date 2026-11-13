.. _subsystem_06_dashboard_assets:

========================================================================================
Subsystem 06: Mission Cockpit Design System & Visual Evidence (6_dashboard/assets)
========================================================================================

:Engine: AETHER-MRID1607X
:Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
:Lead Architect: Gourgopal Mohapatra
:Status: FROZEN_OPERATIONAL_RELEASE_v1.0

Overview and Subsystem Mandate
==============================

The ``6_dashboard/assets/`` repository encapsulates the visual identity, design tokens, stylesheet architecture,
and authoritative visual telemetry evidence suite for the **AETHER-MRID1607X** Mission Cockpit (``6_dashboard/cockpit/app.py``).
This subsystem encompasses two complementary architectural assets:

1. **Aerospace Glassmorphic Design System (style.css)**: An 842-line stylesheet (22.5 KB) defining high-contrast dark-mode command center tokens, dual-tier typography (``Plus Jakarta Sans`` for interface controls and ``JetBrains Mono`` for telemetry values), Streamlit 4.85rem top-bar layout compensation, and custom Folium Leaflet.draw skinning.
2. **Operational Cockpit Visual Telemetry Evidence Suite (cockpit_screenshots/)**: A gallery of 5 Full HD (1080p, 1917x1078) 32-bit RGBA screenshots and accompanying manifest (``SCREENSHOTS_MANIFEST.md``), providing mathematically verified visual proof of live spaceborne telemetry, cadastre farm boundary extraction, interactive satellite map rendering, and Kisan War Room advisory bulletins.

Asset Inventory & Architecture
==============================

.. code-block:: text

       +-------------------------------------------------------------------------+
       |             SUBSYSTEM 06 DESIGN SYSTEM & VISUAL ASSETS                  |
       |                      (6_dashboard/assets/)                              |
       +------------------------------------+------------------------------------+
                                            |
         +----------------------------------+----------------------------------+
         |                                                                     |
         v                                                                     v
+---------------------------------------+             +---------------------------------------+
|  AEROSPACE STYLESHEET (style.css)     |             |  VISUAL EVIDENCE SUITE                |
|  * Deep Obsidian Canvas (#070a11)     |             |  (cockpit_screenshots/)               |
|  * Electric Cyan Accent (#00f0ff)     |             |  * SCREEN-01: Header & Flight Scene   |
|  * Plus Jakarta Sans / JetBrains Mono |             |  * SCREEN-02: Step 2 Telemetry HUD    |
|  * Streamlit Menu/Footer Suppression  |             |  * SCREEN-03: Zonal Cadastre Deficit  |
|  * Glassmorphic KPI Cards & Hover Glow|             |  * SCREEN-04: Google Hybrid GIS Map   |
|  * Leaflet.draw Drawing Toolbar Skin  |             |  * SCREEN-05: Kisan War Room Advisory |
+---------------------------------------+             +---------------------------------------+

Design Tokens & Color Palette
=============================

The stylesheet defines centralized CSS custom properties in the ``:root`` selector:

.. list-table:: Core Design Tokens & Palette
   :widths: 26 18 36 20
   :header-rows: 1

   * - Token Identifier
     - Hex Code
     - Semantic Role
     - Contrast Ratio
   * - ``--mrid-bg-deep``
     - ``#070a11``
     - Deep obsidian background
     - Canvas Base
   * - ``--mrid-bg-surface``
     - ``#0e1524``
     - Elevated control sidebars
     - Surface 1
   * - ``--mrid-bg-card``
     - ``#131c2e``
     - Glassmorphic telemetry cards
     - Surface 2
   * - ``--mrid-border``
     - ``#1e293b``
     - Structural container border
     - Structural
   * - ``--mrid-border-active``
     - ``#00f0ff``
     - Active tabs and focused tools
     - Accent
   * - ``--mrid-text-primary``
     - ``#f8fafc``
     - Primary telemetry readings
     - 16.2:1
   * - ``--mrid-status-live``
     - ``#00ff88``
     - Operational nominal [SHABHASH]
     - 14.8:1
   * - ``--mrid-status-warn``
     - ``#f59e0b``
     - High uncertainty advisory
     - 9.1:1
   * - ``--mrid-status-error``
     - ``#ef4444``
     - Critical bogging [KHATRA]
     - 5.8:1

Visual Evidence Suite (cockpit_screenshots/)
============================================

.. list-table:: Full HD 1080p Cockpit Screenshot Gallery
   :widths: 15 35 20 30
   :header-rows: 1

   * - Asset ID
     - File Name
     - Resolution
     - Telemetry & Operational Role
   * - **SCREEN-01**
     - ``01_cockpit_top_header_and_scene_selector.png``
     - 1917 x 1078
     - Aerospace header, JCC insignias, Sentinel-1/2 status, Step 1 Scene BBox.
   * - **SCREEN-02**
     - ``02_step2_telemetry_hud_metrics.png``
     - 1917 x 1076
     - Step 2 HUD moments (:math:`\mu=29.5\%`, :math:`\sigma`, :math:`P_{10}`, :math:`P_{90}`).
   * - **SCREEN-03**
     - ``03_farm_boundary_and_water_prescription.png``
     - 1917 x 1078
     - Step 3 & 4 Cadastre extraction, farm acreage, water deficit (L/field).
   * - **SCREEN-04**
     - ``04_interactive_google_maps_satellite_viewport.png``
     - 1917 x 1078
     - Google Maps Hybrid basemap over Kendrapara delta with cyan vector overlay.
   * - **SCREEN-05**
     - ``05_kisan_war_room_advisory_bulletin.png``
     - 1917 x 1078
     - Farmer advisory bulletin [SHABHASH], Bekker rut depth :math:`z_{\text{rut}}`, SHA-256.

Brutally Honest Engineering Disclosures ("Ek Ek Dhappa")
========================================================

1. **Streamlit Top-Bar DOM Injection**: ``style.css`` forcibly overrides ``.block-container { padding-top: 4.85rem !important; }`` and hides ``header[data-testid="stHeader"]``. Future Streamlit selector updates could break this override.
2. **Fixed Resolution Reference (1917 x 1078)**: Screenshots were captured at standard Full HD on a specific browser viewport; high-DPI (4K) scaling causes minor text reflow.
3. **External Font Fallbacks**: Google Fonts (``Plus Jakarta Sans``, ``JetBrains Mono``) rely on CDN availability; tactical offline field stations fall back to system fonts.
4. **Leaflet Toolbar CSS Specificity Hacks**: Skinning Leaflet.draw toolbar buttons requires ultra-high specificity CSS selectors to defeat Leaflet's default styles.
5. **Lossless PNG Storage Overhead**: Storing 3.7 MB of uncompressed 32-bit RGBA PNGs inside the Git repository was chosen over lossy WebP to guarantee pixel-for-pixel mathematical auditability.

Traceable Functional Requirements
=================================

.. list-table::
   :widths: 20 20 25 35
   :header-rows: 1

   * - Requirement ID
     - Verification Type
     - Target Module
     - Technical Specification
   * - **REQ-DASH-ASSET-01**
     - Visual Inspection
     - ``assets/style.css``
     - Enforces dual-tier typography with antialiased font smoothing.
   * - **REQ-DASH-ASSET-02**
     - Layout Test
     - ``assets/style.css``
     - Compensates for top-bar clipping with 4.85rem padding and suppresses default chrome.
   * - **REQ-DASH-ASSET-03**
     - Contrast Audit
     - ``assets/style.css``
     - Design tokens guarantee WCAG AA contrast ratio (:math:`>4.5:1`).
   * - **REQ-DASH-ASSET-04**
     - Component Test
     - ``assets/style.css``
     - Skins Leaflet.draw toolbar with obsidian background and active cyan borders.
   * - **REQ-DASH-ASSET-05**
     - Fidelity Audit
     - ``cockpit_screenshots/``
     - Screenshots maintain Full HD 1080p resolution and 32-bit RGBA color profile.
   * - **REQ-DASH-ASSET-06**
     - Provenance Test
     - ``cockpit_screenshots/``
     - ``SCREENSHOTS_MANIFEST.md`` accurately indexes each asset with its SHA-256 digest.
   * - **REQ-DASH-ASSET-07**
     - Telemetry Audit
     - ``cockpit_screenshots/``
     - Captures display verifiable field telemetry (:math:`\mu=29.5\%`, :math:`z_{\text{rut}}`) matching engine states.
   * - **REQ-DASH-ASSET-08**
     - Evidence Trace
     - ``cockpit_screenshots/``
     - Assets integrate cleanly as publication figures in the 30+ page Master Monograph.
