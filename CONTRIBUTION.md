# JAGANNATH COMMAND CENTER (JCC) — SOVEREIGN CONTRIBUTOR & ENGINEERING GUIDEBOOK (JCC-CONTRIB-v1.0)

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:000000,15:050814,35:0a1128,55:1c0a35,75:002b49,90:050814,100:000000&height=220&section=header&text=CONTRIBUTOR%20GUIDEBOOK&fontSize=55&fontColor=00f2fe&animation=fadeIn&fontAlignY=38&desc=JCC%20CAMPUS%202%20%E2%80%A2%20AEROSPACE%20FLIGHT%20STANDARDS%20%E2%80%A2%20DO-178C%20LEVEL-A&descAlignY=62&descSize=14&descColor=4facfe" width="100%"/>

<br/>

[![Mission Authority](https://img.shields.io/badge/MISSION%20AUTHORITY-COMMANDER%20GOURAGOPAL%20MOHAPATRA%20(GOURGOPAL618)-00f2fe?style=for-the-badge&logo=spacex&logoColor=00f2fe&labelColor=050814)](#-1-sovereign-mission--engineering-ethos)
[![Command Sanctum](https://img.shields.io/badge/COMMAND%20SANCTUM-JCC%20CAMPUS%202%20(RS--SDA%20DIVISION)-7f00ff?style=for-the-badge&logo=nasa&logoColor=7f00ff&labelColor=050814)](#-1-sovereign-mission--engineering-ethos)
[![Test Mandate](https://img.shields.io/badge/CI%20REQUIREMENT-63%2F63%20TEST%20SUITES%20PASSED%20(100%25)-00ffab?style=for-the-badge&logo=pytest&logoColor=00ffab&labelColor=050814)](#-5-the-century-verification-mandate-63-test-suites)
[![Target Flight Lock](https://img.shields.io/badge/OPERATIONAL%20RELEASE-14%20NOV%202026%20%40%2018%3A18%20IST-ff0055?style=for-the-badge&logo=clockify&logoColor=ff0055&labelColor=050814)](#-8-sovereign-consecration--review-board)

<br/>

> **Dedicated with profound reverence to the Lotus Feet of Mahaprabhu Shri Jagannath.**  
> *Sovereign Sanctum: Balasore / Bhadrak Border Sanctum, Odisha, Bharat.*

</div>

---

## 🛰️ 1. SOVEREIGN MISSION & ENGINEERING ETHOS

Thank you for your interest in contributing to **THE MRIDANSH** and the **AETHER-MRID1607X** physics-guided digital twin.

This engine is engineered to serve two paramount objectives:
1. **Grassroots Kisan Welfare:** Protecting smallholder farmers against drought, flash floods, and machine sinkage through precise, physics-informed Earth observation.
2. **Aerospace Determinism (DO-178C Level-A):** Enforcing strict mathematical conservation laws, zero numerical hallucination, and rigorous test coverage.

Every line of code submitted to this repository must meet mission-critical aerospace standards. Before submitting a pull request, please review [LICENSE.md](LICENSE.md) (`JSTIRPL-v1.0`) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

## ⚖️ 2. LEGAL & INTELLECTUAL PROPERTY COVENANT

By contributing code, documentation, mathematical formulations, or test cases:
1. You certify that your contribution is your original creation or licensed under compatible terms.
2. You agree that your contribution is bound by the **Jagannath Sovereign Technological Integrity & Restricted Public License (JSTIRPL-v1.0)**.
3. You agree that your contribution will **never** be used for commercial SaaS wrapping, paid monetization against farmers, model distillation, or kinetic weaponization.
4. Ultimate architectural authority rests with **Commander Gouragopal Mohapatra (`GOURGOPAL618`)**, Jagannath Command Center (Campus 2).

---

## 🛠️ 3. LOCAL ENVIRONMENT SETUP

### 3.1 Prerequisites
- **Operating System:** Windows 10/11 (PowerShell 7+ recommended), Ubuntu 22.04+ LTS, or macOS.
- **Python:** Python 3.10, 3.11, 3.12, or 3.14 (with `uv` or `pip`).
- **Geospatial Binaries:** GDAL 3.6+, PROJ 9+, GEOS.

### 3.2 Workspace Initialization
Clone the repository and activate the dedicated virtual environment:

```powershell
# Clone the sovereign repository
git clone https://github.com/GOURGOPAL618/THE_MRIDANSH.git
cd THE_MRIDANSH

# Activate virtual environment (Windows PowerShell)
.\mridansh_env\Scripts\activate

# Or create a fresh virtual environment using uv
uv venv mridansh_env --python 3.12
.\mridansh_env\Scripts\activate
uv pip install -r requirements.txt
```

Verify that all dependencies and geospatial bindings load cleanly:
```powershell
python -c "import torch, rasterio, numpy, fastapi, streamlit; print('>> JCC Environment Online')"
```

---

## 🌿 4. GIT WORKFLOW & COMMIT CONVENTIONS

### 4.1 Branching Strategy
Never commit directly to the `main` branch. Create a feature or bugfix branch with clear subsystem categorization:

| Branch Type | Syntax Example | Purpose |
| :--- | :--- | :--- |
| **Feature** | `feat/agronomy-vri-scheduler` | New functional capability in domain translators or core engine. |
| **Bugfix** | `fix/richards-mass-drift` | Numerical bugfix or boundary condition correction. |
| **Telemetry / Test** | `test/monte-carlo-q5` | Verification suite enhancement or test coverage expansion. |
| **Documentation** | `docs/mathematical-monograph` | LaTeX manuscript, whitepaper, or architectural updates. |

### 4.2 Conventional Commit Standard
All commit messages must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification with strict subsystem scopes:

```text
<type>(<scope>): <concise descriptive summary in present tense>

[optional detailed architectural body]

[optional footer: Signed-off-by: Contributor Name <email>]
```

**Permitted Scopes:**
- `core_engine` (PINN, Richards PDE, EnKF, Van Genuchten)
- `domain_translators` (Agronomy VRI, Civil Terramechanics)
- `data_pipeline` (Sentinel-1 SAR, Sentinel-2 MSI, DEM, COG)
- `dashboard` (Streamlit Cockpit, Mapbox/Folium GIS renderers)
- `simulation` (Monte Carlo planetary campaign)
- `audit` / `test` (Harnesses, verification dossiers)
- `docs` (Monographs, flight logs, LaTeX packages)

**Example:**
```text
feat(domain_translators): enforce complementary stress identity Ks + CWSI == 1.0

Validated zero-drift tolerance (<1e-6) across 10,000 synthetic moisture states.
Ensures compliance with DO-178C Level-A deterministic invariants.

Signed-off-by: Gouragopal Mohapatra <ggmohapatra.info.2007@gmail.com>
```

---

## 🔬 5. THE CENTURY VERIFICATION MANDATE (63 TEST SUITES)

**This is the single most critical rule of THE MRIDANSH engineering.**

Before submitting any Pull Request, you **MUST** run the Master Full-Project Audit Harness:

```powershell
python run_full_system_test_audit.py
```

### 🛑 Zero-Tolerance Pass Criteria:
- **Test File Compliance:** Exactly **63 / 63 test suites** must report `PASSED`.
- **Individual Contracts:** Exactly **426 / 426 formal contracts** must report `PASSED`.
- **Pass Rate:** **100.0%** (Zero failures, Zero timeouts, Zero skipped).
- **Execution Budget:** Suite execution must complete within $\approx 180$ seconds.
- **Numerical Purity:** Zero `NaN`, zero `Inf`, and zero unhandled covariance divergences ($\kappa(P) \ll 10^6$).

If even **one** test fails or times out, your Pull Request will be automatically rejected.

---

## 📐 6. SUBSYSTEM CODING STANDARDS

### 6.1 Core Physics Engine (`3_core_engine/`)
- **Richards PDE Residuals:** Finite difference and PINN solvers must preserve mass conservation residuals $< 10^{-6}\ \text{m}^3/\text{m}^3$.
- **Van Genuchten Constraints:** Parameter limits ($\alpha > 0$, $n > 1$, $\theta_r < \theta_s$) must be mathematically clamped. Never permit non-physical soil water content.
- **EnKF Filter Conditioning:** Ensemble covariance matrix conditioning must satisfy $\kappa(P) < 10^6$. Maintain the empirical safety margin ($\kappa \approx 1709 \ll 10^6$).

### 6.2 Agronomy Translator (`4_domain_translators/agronomy/`)
- **Complementary Stress Identity:** The Crop Water Stress Index ($\text{CWSI}$) and Transpiration Reduction Factor ($K_s$) must strictly satisfy:
  $$K_s + \text{CWSI} \equiv 1.000000 \pm 10^{-6}$$
- **VRI Bounds:** Variable Rate Irrigation advisories must never recommend over-irrigation that induces root hypoxia or under-irrigation that exceeds permanent wilting point ($\text{PWP}$).

### 6.3 Civil & Terramechanics Translator (`4_domain_translators/civil/`)
- **Safety Factor Standards:** Meyerhof ultimate bearing capacity ($q_{ult}$) and Bekker trafficability must enforce:
  $$\text{FS} = \frac{q_{ult}}{\sigma_{applied}} \ge 1.30$$
- Any soil condition with $\text{FS} < 1.30$ or slope liquefaction probability $> 60\%$ must trigger an immediate `IMMOBILIZATION_ALERT` and `HAZARD` flag.

### 6.4 GIS, Dashboard & API (`6_dashboard/`, `2_data_pipeline/`)
- **Coordinate Reference System:** All spatial geometries must be normalized to WGS84 (`EPSG:4326`) with explicit reprojection to UTM zones for distance/area computations.
- **FastAPI Determinism:** API response payloads must be strictly validated using Pydantic v2 schemas.
- **Map Renderers:** Renderers must handle empty bounding boxes, cloudy Sentinel-2 passes, and missing SAR polarizations gracefully without crashing.

---

## 📋 7. PULL REQUEST SUBMISSION CHECKLIST

Before opening a PR, ensure all items in this checklist are satisfied:

- [ ] Branch branched off current `main` branch.
- [ ] Code formatted using standard PEP 8 conventions.
- [ ] Type annotations included on all public function signatures.
- [ ] Docstrings provided with parameter descriptions and physical units (e.g., $\text{m}^3/\text{m}^3$, $\text{kPa}$, $\text{m}/\text{s}$).
- [ ] New unit tests added to `tests/` covering new features or bug fixes.
- [ ] Executed `python run_full_system_test_audit.py` with **63/63 files PASSED (100.0%)**.
- [ ] No temporary debug artifacts, uncompressed video recordings, or cache files committed.
- [ ] Commit messages follow Conventional Commits format.

---

## 🏛️ 8. SOVEREIGN CONSECRATION & REVIEW BOARD

All pull requests are reviewed by the **Jagannath Command Center Supreme Review Board** under the personal direction of **Commander Gouragopal Mohapatra (`GOURGOPAL618`)**.

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║                 JCC CONTRIBUTOR CHARTER & ENGINEERING COVENANT                       ║
║                                                                                      ║
║                 COMMANDER GOURAGOPAL MOHAPATRA (GOURGOPAL618)                        ║
║            Lead Systems Architect & Remote Sensing Mission Engineer                  ║
║           JAGANNATH COMMAND CENTER (JCC) - CAMPUS 2 (RS-SDA DIVISION)                ║
║                                                                                      ║
║             Sovereign Sanctum: Balasore / Bhadrak Border Sanctum,                    ║
║                               Odisha, Bharat                                         ║
║                                                                                      ║
║         Target Flight Release Lock: 14 November 2026 @ 18:18:00 IST                  ║
║                                                                                      ║
║           DEDICATED TO THE LOTUS FEET OF MAHAPRABHU SHRI JAGANNATH                   ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```

<div align="center">

[![JCC Contributor Seal](https://img.shields.io/badge/AUTHENTICATED%20BY-JAGANNATH%20COMMAND%20CENTER%20(JCC)-00f2fe?style=for-the-badge&logo=shield&logoColor=00f2fe&labelColor=050814)](#-1-sovereign-mission--engineering-ethos)
[![TRL-7 Certified](https://img.shields.io/badge/FLIGHT%20CERTIFICATION-TRL--7%20OPERATIONAL-00ffab?style=for-the-badge&logo=nasa&logoColor=00ffab&labelColor=050814)](#-5-the-century-verification-mandate-63-test-suites)

</div>
