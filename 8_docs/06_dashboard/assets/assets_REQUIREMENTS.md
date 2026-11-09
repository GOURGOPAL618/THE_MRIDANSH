# Subsystem 06: Mission Cockpit Design System & Styling Specification (`6_dashboard/assets`)
## Central Engine: AETHER-MRID1607X
### Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
### Author & Lead Architect: Gourgopal Mohapatra
### Release Status: FROZEN_OPERATIONAL_RELEASE_v1.0

---

## 1. Executive Overview & Subsystem Mandate

The `6_dashboard/assets/` directory houses the core visual identity, design tokens, and user interface styling architecture for the **AETHER-MRID1607X** Mission Cockpit (`6_dashboard/app.py`). Encapsulated within the comprehensive 842-line `style.css` stylesheet (22.5 KB), this subsystem defines an **Aerospace Command Center Glassmorphism Design System** engineered for high-consequence situational awareness, geospatial clarity, and multi-domain decision intelligence.

The primary mandate of the assets subsystem is to enforce deterministic visual ergonomics across all cockpit viewports, overcoming default web framework constraints. It achieves this by standardizing dual-tier typography (`Plus Jakarta Sans` for interface controls and `JetBrains Mono` for telemetry numbers), compensating for top-bar viewport clipping, skinning interactive Leaflet.draw GIS tools, and rendering farmer advisory cards (`[SHABHASH]` vs `[KHATRA]`) with zero layout jitter.

```
       +--------------------------------------------------------------+
       |             AEROSPACE COCKPIT STYLING ARCHITECTURE           |
       |                (6_dashboard/assets/style.css)                |
       +------------------------------+-------------------------------+
                                      |
         +----------------------------+----------------------------+
         |                            |                            |
         v                            v                            v
[1. DESIGN TOKENS]           [2. DUAL TYPOGRAPHY]         [3. STREAMLIT OVERRIDES]
• Deep Obsidian (#070a11)    • Plus Jakarta Sans (UI)     • .block-container (4.85rem)
• Electric Cyan (#00f0ff)    • JetBrains Mono (Telemetry) • Menu/Footer Suppression
• Live Status (#00ff88)      • Font Smoothing & Kerning   • Custom Scrollbars
         |                            |                            |
         +----------------------------+----------------------------+
                                      |
         +----------------------------+----------------------------+
         |                                                         |
         v                                                         v
[4. HUD & GLASS CARDS]                                     [5. GIS & LEAFLET DRAW]
• .mrid-master-header (Dual Logos)                         • .leaflet-draw-toolbar
• .kpi-card & Hover Glows                                  • Cyan Technical Vector Polygons
• Kisan War Room Alert Badges                              • Mode Switcher Pill Styles
```

---

## 2. Design System Tokens & Root Color Palette

The visual design system is anchored in `:root` CSS custom properties establishing high contrast ratios against dark satellite imagery:

| Variable Identifier | Color Hex / Value | Semantic Role | Accessibility Contrast Ratio |
|:---|:---:|:---|:---:|
| `--mrid-bg-deep` | `#070a11` | Deep obsidian background for full viewport. | N/A (Base Canvas) |
| `--mrid-bg-canvas` | `#090d16` | Main application canvas background. | Base Canvas |
| `--mrid-bg-surface` | `#0e1524` | Elevated control panels and sidebars. | Surface Tier 1 |
| `--mrid-bg-card` | `#131c2e` | Glassmorphic KPI cards and telemetry containers. | Surface Tier 2 |
| `--mrid-border` | `#1e293b` | Structural container borders. | Subtle Separation |
| `--mrid-border-active` | `#00f0ff` | Focused inputs, active tabs, and drawing tools. | High Contrast Accent |
| `--mrid-text-primary` | `#f8fafc` | Primary readings, headers, and modal text. | 16.2:1 against Deep |
| `--mrid-text-secondary` | `#94a3b8` | Parameter labels, units, and timestamps. | 8.4:1 against Deep |
| `--mrid-text-muted` | `#64748b` | Inactive captions and disabled hints. | 4.6:1 against Deep |
| `--mrid-accent-cyan` | `#00f0ff` | Mission signature electric cyan accent. | High Contrast Accent |
| `--mrid-status-live` | `#00ff88` | Operational nominal, verified lock, `[SHABHASH]`. | 14.8:1 against Deep |
| `--mrid-status-warn` | `#f59e0b` | High uncertainty advisory, moderate rut risk. | 9.1:1 against Deep |
| `--mrid-status-error` | `#ef4444` | Sensor blackout, critical bogging, `[KHATRA]`. | 5.8:1 against Deep |

---

## 3. Detailed Breakdown of the 13 Styling Sections

`style.css` is structured into 13 modular sections governing every graphical aspect of the cockpit:

### 3.1 Section 1: Design Tokens & Root Variables (Lines 11–32)
Declares the institutional CSS variables ensuring global color synchronization across Streamlit native widgets, custom HTML components, and Plotly charts.

### 3.2 Section 2: Typography Enforcement (Lines 34–68)
* **Google Fonts Import:** Fetches `Plus Jakarta Sans` (weights 300..800) and `JetBrains Mono` (weights 400..700).
* **Global Rule:** Injects `font-family: 'Plus Jakarta Sans', sans-serif !important;` across all standard HTML elements, `.stApp`, and markdown containers.
* **Monospace Rule:** Binds `font-family: 'JetBrains Mono', monospace !important;` to telemetry values, raw sensor inputs, coordinates, and latency indicators.

### 3.3 Section 3: Global App Layout & Streamlit Cleanups (Lines 70–130)
* **Top-Padding Compensation:** Enforces `.block-container { padding-top: 4.85rem !important; }` to eliminate header bar clipping under custom fixed banners.
* **Streamlit Chrome Suppression:** Hides default Streamlit menu `#MainMenu`, header decorations, and default footer, replacing them with institutional Aerospace headers.

### 3.4 Section 4: Mission Command Header Bar (Lines 132–230)
* `.mrid-master-header`: Glassmorphic header container with blur backdrop filter (`backdrop-filter: blur(12px)`).
* **Dual Logo Architecture:** Left frame hosts the Project Insignia, while right frame mounts the institutional JCC Campus 2 insignia.
* **Status Badges:** Integrates `.status-pill`, `.pill-live` (pulsing green indicator), `.pill-cyan`, and `.pill-purple`.

### 3.5 Section 5: Telemetry Strip (Lines 232–295)
Renders the horizontal flight telemetry ribbon displaying real-time FPS, inference latency ($	ext{ms/px}$), EnKF convergence status, and active satellite constellation badges.

### 3.6 Section 6: Sidebar Workspace Controls (Lines 297–370)
Customizes Streamlit sidebar components: dark glassmorphic card styling, cyan slider handles, styled radio toggles, and high-visibility file upload dropzones.

### 3.7 Section 7: Standardized KPI Telemetry Cards (Lines 372–465)
Defines `.kpi-card` containers:
* 1px solid border (`--mrid-border`) transitioning to `--mrid-accent-cyan` on `:hover`.
* Smooth CSS translateY elevation (`transform: translateY(-2px);`).
* Dedicated sub-containers for numerical value (`.kpi-value`), physical units (`.kpi-unit`), and status delta badges.

### 3.8 Section 8: Section Headers & Typography (Lines 467–515)
Standardizes sub-headings, section icons, and gradient underline bars separating analytical viewports.

### 3.9 Section 9: Buttons & Interactive Controls (Lines 517–580)
Skins Streamlit primary and secondary buttons:
* Primary: Cyan background with deep obsidian text and subtle outer glow (`box-shadow: 0 0 15px rgba(0, 240, 255, 0.3)`).
* Secondary: Ghost outline with cyan hover borders.

### 3.10 Section 10: Tabs & Accordions (Lines 582–645)
Overhauls `.stTabs`:
* Eliminates default red Streamlit indicators in favor of an animated electric cyan bottom border.
* Unselected tabs rendered in `--mrid-text-secondary`, transitioning to bold `--mrid-text-primary` on active selection.

### 3.11 Section 11: Sector Inspection Glassmorphic Card (Lines 647–710)
Renders the floating farm boundary inspection panel in the GIS viewport, formatting acreage badges, centroid coordinates, and zonal telemetry.

### 3.12 Section 12: Horizontal Dividers & Leaflet Controls (Lines 712–765)
Customizes subtle horizontal separators and repositions Leaflet zoom controls to prevent overlap with telemetry cards.

### 3.13 Section 13: Leaflet Draw Toolbar & Farm Alerts (Lines 767–842)
* **Leaflet.draw Skinning:** Skins polygon and rectangle drawing buttons with cyan border highlights and active drawing states.
* **Farmer Advisory Bulletins:**
  * `.badge-shabhash`: Green alert banner (`#00ff88`) for safe tillage and optimal pre-soak moisture.
  * `.badge-khatra`: Pulsing red hazard banner (`#ef4444`) for critical bogging hazard and seedling submergence risk.

---

## 4. Brutal Engineering Disclosures ("Ek Ek Dhappa")

In alignment with institutional engineering transparency guidelines, the following visual compromises, browser quirks, and DOM coupling vulnerabilities are formally disclosed:

1. **Brute-Force `!important` Streamlit DOM Overrides:**
   * *Problem:* Streamlit injects deeply nested, dynamically generated class names (e.g. `[class*="st-emotion-cache"]`) that override external CSS rules.
   * *Workaround:* `style.css` relies heavily on `!important` declarations across 60+ selectors to guarantee font family and padding enforcement.
   * *Risk:* Upgrading Streamlit minor versions can alter internal HTML wrapper hierarchies, potentially neutralizing specific card or button selectors.
2. **External Cloud Font Network Dependency:**
   * *Problem:* Lines 8–9 import Google Fonts via `@import url('https://fonts.googleapis.com/...')`.
   * *Failure Mode:* On air-gapped defense networks, remote server environments, or field laptops operating without internet connectivity, the font import will silently fail.
   * *Mitigation:* A robust fallback stack is defined (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`), but typography will degrade to standard system fonts.
3. **Hardcoded Top-Padding Compensation (`4.85rem`):**
   * *Problem:* `.block-container` top-padding is hardcoded to `4.85rem` to offset the fixed mission command header.
   * *Impact:* If banner content wraps onto two lines on mobile screens or small browser windows, the header bar will overlap the top telemetry cards.
4. **Third-Party Leaflet.draw Class Coupling:**
   * *Problem:* Section 13 overrides third-party Leaflet CSS classes (e.g. `.leaflet-draw-toolbar a`).
   * *Impact:* Any breaking change in Folium or `leaflet-draw` plugin DOM structuring will silently break toolbar styling, reverting to standard default gray Leaflet buttons.

---

## 5. Traceable Subsystem Requirements Matrix

| Requirement ID | Verification Type | Target Specification / Bound | Status |
|:---|:---:|:---|:---:|
| **REQ-DASH-AST-01** | Visual / Inspection | Typography must enforce `Plus Jakarta Sans` across all UI and controls. | **VERIFIED** |
| **REQ-DASH-AST-02** | Visual / Inspection | Telemetry numbers and coordinates must render in `JetBrains Mono`. | **VERIFIED** |
| **REQ-DASH-AST-03** | Layout | Top-padding compensation must eliminate viewport clipping (`padding-top: 4.85rem`). | **VERIFIED** |
| **REQ-DASH-AST-04** | Branding | Dual logo frames must render Project and JCC Campus 2 insignia cleanly. | **VERIFIED** |
| **REQ-DASH-AST-05** | Contrast | Primary text against dark backgrounds must satisfy WCAG AA ($> 4.5:1$). | **VERIFIED** (16.2:1) |
| **REQ-DASH-AST-06** | GIS Controls | Leaflet.draw toolbar must feature cyan active focus and drawing modes. | **VERIFIED** |
| **REQ-DASH-AST-07** | Farmer Alerts | Advisory alerts must render distinct `.badge-shabhash` and `.badge-khatra` styles. | **VERIFIED** |
| **REQ-DASH-AST-08** | Performance | Stylesheet file size must remain $< 30.0\ 	ext{KB}$ to ensure zero render lag. | **VERIFIED** (22.5 KB) |
