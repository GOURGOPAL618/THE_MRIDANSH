# 🛰️ Planetary Monte Carlo Execution Scripts Manifest
## Mission: 1,000-Trial Planetary Monte Carlo Campaign (`PMC-1000-AETHER-MRID1607X`)
### Repository Location: `11_simulation_test_campaign/scripts/`
### Operational Status: ACTIVE IN-MEMORY COMPUTATIONAL ENGINES

---

## 1. Subsystem Mandate & Algorithmic Tiers

The `11_simulation_test_campaign/scripts/` directory houses the core algorithmic code, in-memory vectorized simulation engines, scenario runners, and artifact generators for the 1,000-trial Planetary Monte Carlo campaign.

---

## 2. Script Inventory & Interface Signatures

| Script Filename | File Size | Primary Class / Functions | Algorithmic Responsibilities & Execution Envelopes |
|:---|:---:|:---|:---|
| **`planetary_monte_carlo_engine.py`** | 66.5 KB | `PlanetaryMonteCarloEngine` | Master in-memory simulation engine: Vectorized execution across Q1 (drought), Q2 (deluge), Q3 (sensor noise), Q4 (liquefaction). Executes 1,000 trials in 6.53s total (6.53 ms/trial). Enforces 5 flight invariants. |
| **`generate_monte_carlo_artifacts.py`** | 18.5 KB | `main()` | Publication artifact generator: Reads raw `.npy` trajectory arrays and `.json` metrics; generates 3 publication-grade figures (600 DPI PNG & vector PDF); exports `figures_captions_latex.tex`. |
| **`run_simulation.py`** | 6.1 KB | `main()` | Coupled agro-civil field scenario runner: Evaluates 5 field moisture scenarios (Bone Dry to Flooded); runs 50-trial precursor Monte Carlo stress trials; exports `simulation_telemetry_results.json`. |

---

## 3. Dynamic Path Resolution Standard

All scripts implement robust multi-level path resolution:
```python
_SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = _SCRIPTS_DIR.parent.parent if _SCRIPTS_DIR.name == "scripts" else _SCRIPTS_DIR.parent
```
This guarantees zero `ModuleNotFoundError` whether invoked from the repository root, subfolders, or automated test runners.
