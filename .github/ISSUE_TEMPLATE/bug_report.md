---
name: "🐛 Bug Report / Numerical Defect"
about: "Report a reproducible bug, numerical drift, or pipeline defect in THE MRIDANSH"
title: "[BUG]: "
labels: ["bug", "triage"]
assignees: ["GOURGOPAL618"]
---

### 🛰️ Subsystem Affected
- [ ] Core Physics Engine (`3_core_engine/` - PINN, Richards PDE, EnKF, SWRC)
- [ ] Domain Translators (`4_domain_translators/` - Agronomy VRI, Civil Terramechanics)
- [ ] Data Pipeline & Ingestion (`2_data_pipeline/` - Sentinel-1/2, Landsat, COG, DEM)
- [ ] Mission Cockpit & GIS Dashboard (`6_dashboard/` - FastAPI, Streamlit, Mapbox/Folium)
- [ ] Simulation Campaign & Verification Suites (`11_simulation_test_campaign/`, `tests/`)

### 📝 Defect Description
<!-- Clear and concise description of the bug, unexpected behavior, or numerical divergence. -->

### 🔬 Mathematical Invariant Violated
<!-- Which physical law or contract was breached? (e.g., Richards mass drift >= 1e-6, FS < 1.30 without hazard trigger, Ks + CWSI != 1.0, NaN in Kalman covariance). -->

### 🔄 Steps to Reproduce
1. Execute command: `...`
2. Ingest AoI / Tensor: `...`
3. Observe error or exception: `...`

### 💻 Minimal Reproducible Example / Payload
```python
# Minimal Python snippet reproducing the numerical or pipeline error
```

### 📊 Expected vs. Actual Telemetry
- **Expected Behavior:** <!-- e.g., Finite difference solver converges with residual < 1e-6 -->
- **Actual Behavior:** <!-- e.g., Solver raises FloatingPointError: NaN encountered -->

### ⚙️ Operating Environment
- **Operating System:** Windows 10/11 / Ubuntu 22.04 LTS / macOS
- **Python Version:** 3.10 / 3.11 / 3.12 / 3.14
- **GDAL / Rasterio Version:**
- **PyTorch Version:**
- **Commit SHA / Branch:**

### 📎 Telemetry Logs & Screenshots
<!-- Paste terminal stack trace or attach log files if applicable. -->
