# Subsystem 11: Simulation Test Campaign — Scripts Specification (`11_simulation_test_campaign/scripts/`)
## Central Unified Engine: AETHER-MRID1607X
### Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
### Author & Lead Systems Architect: Gourgopal Mohapatra
### Release Status: TRL-7 OPERATIONAL FLIGHT READINESS

---

## 1. Executive Overview & Subsystem Mandate

The `11_simulation_test_campaign/scripts/` subsystem defines the high-performance in-memory execution engines, coupled scenario drivers, and automated figure rendering pipelines for the **AETHER-MRID1607X** Planetary Monte Carlo Stress Campaign (`PMC-1000-AETHER-MRID1607X`).

---

## 2. Module Specifications & Call Signatures

### 2.1 `planetary_monte_carlo_engine.py` (Master In-Memory Vectorized Engine)
* **Class:** `PlanetaryMonteCarloEngine(output_dir: Optional[Path] = None)`
* **Key Execution Methods:**
  - `execute_phase_1_drought(n_trials=250, seed=16071) -> Dict[str, Any]`
  - `execute_phase_2_deluge(n_trials=250, seed=16072) -> Dict[str, Any]`
  - `execute_phase_3_noise(n_trials=250, seed=16073) -> Dict[str, Any]`
  - `execute_phase_4_liquefaction(n_trials=250, seed=16074) -> Dict[str, Any]`
  - `aggregate_full_campaign() -> Dict[str, Any]`
* **Computational SLA:** Total wall-clock execution time for 1,000 trials $\le 10.0\,	ext{seconds}$ ($10.0\,	ext{ms/trial}$). Measured: **$6.53\,	ext{seconds}$ ($6.53\,	ext{ms/trial}$)**.

### 2.2 `generate_monte_carlo_artifacts.py` (Publication Graphics Generator)
* **Function:** `main()`
* **Inputs:** `simulation_data/Q1_drought/`, `Q2_deluge/`, `Q3_noise/`, `Q4_liquefaction/`, and `master_campaign/` `.json` and `.npy` arrays.
* **Outputs:** 3 dual-format figures (`figures/figure_1_...`, `figure_2_...`, `figure_3_...`) + LaTeX captions snippet.

### 2.3 `run_simulation.py` (Coupled Agro-Civil Field Scenario Driver)
* **Function:** `main()`
* **Operational Telemetry:** Evaluates 5 physical tillage scenarios across the 40.96 ha field bounds and executes a 50-trial precursor Monte Carlo test in $533.76\,	ext{ms}$.

---

## 3. "Ek Ek Dhappa" — Brutally Honest Engineering Disclosures

1. **Memory Allocation During 1,000-Trial Array Serialization:**
   - *Dhappa:* Storing 1,000 multi-layer temporal trajectories as raw NumPy arrays requires $\sim 58\,	ext{KB}$ per quadrant.
   - *Compromise:* While trivial for 1,000 trials, scaling to 1,000,000 trials in regional grid simulations would require streaming trajectories to HDF5 or Zarr memory-mapped stores to prevent Out-Of-Memory (OOM) faults.

2. **Single-Threaded Matplotlib Rendering:**
   - *Dhappa:* Figure generation takes $\sim 10.5\,	ext{seconds}$ due to sequential Matplotlib drawing calls.
   - *Compromise:* Rendering runs strictly on CPU with non-interactive `Agg` backend. Multiprocessing was not implemented since figure rendering is an offline publication step.
