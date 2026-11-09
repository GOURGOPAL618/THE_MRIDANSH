.. _subsystem_06_dashboard_assets:

========================================================================================
Subsystem 06: Mission Cockpit Design System & Styling Specification (6_dashboard/assets)
========================================================================================

:Engine: AETHER-MRID1607X
:Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
:Lead Architect: Gourgopal Mohapatra
:Status: FROZEN_OPERATIONAL_RELEASE_v1.0

Overview and Subsystem Mandate
==============================

The ``6_dashboard/assets/`` repository encapsulates the visual identity, design tokens, and user
interface styling architecture for the **AETHER-MRID1607X** Mission Cockpit (``6_dashboard/app.py``).
Defined in the 842-line stylesheet ``style.css`` (22.5 KB), this subsystem delivers an **Aerospace
Command Center Glassmorphism Design System** optimized for situational awareness and multi-domain decision-making.

Key objectives:

1. **Dual Typography Standardization:** Enforces ``Plus Jakarta Sans`` for interface controls and
   ``JetBrains Mono`` for high-precision telemetry numbers and geospatial coordinates.
2. **Viewport Optimization:** Compensates for framework layout anomalies, eliminating header bar clipping
   and suppressing default web chrome.
3. **Specialized GIS & Agronomic Components:** Skins interactive Folium/Leaflet.draw GIS tools and renders
   farmer advisory bulletins (``[SHABHASH]`` vs ``[KHATRA]``) with clear visual hierarchy.

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
     - Glassmorphic KPI cards
     - Surface 2
   * - ``--mrid-accent-cyan``
     - ``#00f0ff``
     - Mission signature electric cyan
     - Accent
   * - ``--mrid-text-primary``
     - ``#f8fafc``
     - Primary telemetry readings
     - 16.2:1 (High)
   * - ``--mrid-text-secondary``
     - ``#94a3b8``
     - Control labels and units
     - 8.4:1
   * - ``--mrid-status-live``
     - ``#00ff88``
     - Operational nominal & ``[SHABHASH]``
     - 14.8:1
   * - ``--mrid-status-error``
     - ``#ef4444``
     - Sensor failure & ``[KHATRA]``
     - 5.8:1

13 Modular Styling Sections Breakdown
=====================================

1. **Design Tokens & Root Variables:** Centralized theme variables.
2. **Typography Enforcement:** Global injection of ``Plus Jakarta Sans`` and ``JetBrains Mono``.
3. **Global App Layout:** Top-padding compensation (``padding-top: 4.85rem``) and header bar un-clipping.
4. **Mission Command Header:** Dual-logo frame layout (Project insignia left, JCC Campus 2 right) with glass blur.
5. **Telemetry Strip:** Horizontal operational HUD displaying live FPS, latency, and model lock status.
6. **Sidebar Controls:** Dark glassmorphic workspace controls, sliders, and upload dropzones.
7. **KPI Telemetry Cards:** Standardized ``.kpi-card`` with cyan hover elevation.
8. **Section Headers:** Clean visual dividing rules with glowing accent underlines.
9. **Buttons & Controls:** Electric cyan glow buttons with active click transitions.
10. **Tabs & Accordions:** Custom animated cyan tab indicators replacing default framework themes.
11. **Sector Inspection Card:** Floating farm boundary analytics panel.
12. **Dividers & Leaflet Controls:** Repositioned map zoom controls.
13. **Leaflet Draw & Alerts:** Styled GIS polygon drawing tools and farmer advisory alert badges.

Brutally Honest Disclosures & Caveats
=====================================

1. **Excessive `!important` Declarations:**
   Streamlit's internal CSS architecture necessitates heavy reliance on ``!important`` declarations,
   introducing fragility during minor framework upgrades.
2. **Cloud Font CDN Dependency:**
   ``@import url('https://fonts.googleapis.com/...')`` requires active internet access. In air-gapped
   defense deployments, typography silently falls back to standard system sans-serif fonts.
3. **Rigid Viewport Padding:**
   The ``4.85rem`` top-padding is calibrated for standard desktop displays; extreme mobile viewport
   wrapping can induce minor header overlaps.
4. **Leaflet.draw Class Coupling:**
   Custom styles directly target third-party ``.leaflet-draw-toolbar`` classes; library updates could
   alter DOM class names.

Traceable Requirements Matrix
=============================

.. list-table:: Subsystem 06 Design Assets Requirements
   :widths: 20 20 40 20
   :header-rows: 1

   * - Requirement ID
     - Method
     - Specification Contract
     - Compliance Status
   * - **REQ-DASH-AST-01**
     - Inspection
     - Enforces ``Plus Jakarta Sans`` across all UI controls.
     - **PASSED**
   * - **REQ-DASH-AST-02**
     - Inspection
     - Enforces ``JetBrains Mono`` on telemetry numbers and coordinates.
     - **PASSED**
   * - **REQ-DASH-AST-03**
     - Layout
     - Compensates for top header clipping via ``4.85rem`` padding.
     - **PASSED**
   * - **REQ-DASH-AST-04**
     - Branding
     - Dual logo frames cleanly render Project and JCC insignia.
     - **PASSED**
   * - **REQ-DASH-AST-05**
     - Accessibility
     - Primary text contrast exceeds WCAG AA standards (:math:`> 4.5:1`).
     - **PASSED** (16.2:1)
   * - **REQ-DASH-AST-06**
     - GIS Controls
     - Leaflet.draw toolbar features cyan active focus styling.
     - **PASSED**
   * - **REQ-DASH-AST-07**
     - Alerts
     - Distinct ``.badge-shabhash`` and ``.badge-khatra`` styles rendered.
     - **PASSED**
   * - **REQ-DASH-AST-08**
     - Size
     - Stylesheet byte size remains strictly :math:`< 30.0\ \text{KB}`.
     - **PASSED** (22.5 KB)
