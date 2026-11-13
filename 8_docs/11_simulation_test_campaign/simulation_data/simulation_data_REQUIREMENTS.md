# SUBSYSTEM 11: SIMULATION DATA STORE & TELEMETRY REQUIREMENTS SPECIFICATION
**Document Identifier:** `JCC-REQ-SIMDATA-11-2026`  
**System Classification:** Spaceborne Ground-Truth Verification & Planetary Data Vault  
**Author:** JAGANNATH COMMAND CENTER (JCC) - RS-SDA DIVISION  
**Revision:** v2.4 (Sanitized Planetary Certification Baseline)

---

## 1. Scope & Functional Purpose

This Requirements Specification governs the architectural design, serialization formats, validation rules, and schema definitions for the simulation data artifacts maintained under `11_simulation_test_campaign/simulation_data/`.

The data vault provides immutable evidentiary verification records for spaceborne Earth observation algorithms, vadose hydrology solvers, and terramechanics mobility modules under extreme terrestrial stress conditions.

---

## 2. Functional Requirements (FR-DATA)

### FR-DATA-01: Deterministic Binary Serialization
* The simulation engine **SHALL** export trial trajectory matrices in uncompressed IEEE 754 32-bit single-precision floating point (`float32`) binary format (`.npy`).
* Row index **SHALL** map strictly to trial identifier ($0 \le \text{trial\_id} < 250$).
* Column index **SHALL** map monotonically to simulation day ($t \in [0, N_{\text{days}}-1]$).

### FR-DATA-02: Structured JSON Telemetry Ledger
* Every quadrant directory and the master campaign directory **SHALL** contain an accompanying `.json` metadata ledger.
* Ledgers **SHALL** record execution wall-clock time, mean execution time per trial, statistical moments (mean, std, min, max, p10, p90), failure hazard rates, and condition numbers.

### FR-DATA-03: Cryptographic Integrity Validation
* The master ledger (`monte_carlo_1000_metrics.json`) **SHALL** record an overall SHA256 checksum summarizing the campaign state to guarantee tamper-evident qualification records.

---

## 3. Data Schema & Memory Layout Specifications

```
+-----------------------------------------------------------------------------------------+
|                  1,000-TRIAL MONTE CARLO SERIALIZED TELEMETRY VAULT                     |
+-----------------------------------------------------------------------------------------+
|                                                                                         |
|  [Q1_drought]            [Q2_deluge]            [Q3_noise]            [Q4_liquefaction] |
|  - (250, 16) float32     - (250, 8) float32     - (250, 10) float32   - (250, 8) float32|
|  - Drought Desiccation   - Monsoon Flooding     - Speckle & Clouds    - Rutting Sinkage |
|                                                                                         |
|  +-----------------------------------------------------------------------------------+  |
|  |                           MASTER CAMPAIGN CONSOLIDATION                           |  |
|  |  - monte_carlo_1000_metrics.json    : 1000-trial aggregate moments & qualification|  |
|  |  - simulation_telemetry_results.json: 5 Field scenarios & advisory bulletins      |  |
|  +-----------------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------------+
```

### Detailed Field Schema for Quadrant Metrics

```json
{
  "quadrant": "STRING: Identifier (e.g. Q1_HYPER_ARID_DROUGHT)",
  "seed": "INTEGER: PRNG seed value (e.g. 16071)",
  "total_trials": "INTEGER: 250",
  "passed_trials": "INTEGER: 250",
  "success_rate_pct": "FLOAT: 100.0",
  "execution_wall_time_seconds": "FLOAT: Measured wall clock execution time",
  "average_ms_per_trial": "FLOAT: Wall time / total_trials * 1000",
  "statistical_moments": {
    "final_theta": {
      "mean": "FLOAT: Mean volumetric water content [m^3/m^3]",
      "std": "FLOAT: Standard deviation",
      "min": "FLOAT: Minimum observed value",
      "max": "FLOAT: Maximum observed value",
      "p10": "FLOAT: 10th percentile",
      "p90": "FLOAT: 90th percentile"
    },
    "kalman_condition_number_kappa": {
      "mean": "FLOAT: Mean condition number",
      "max": "FLOAT: Peak condition number",
      "threshold_ceiling": "FLOAT: 1000000.0",
      "condition_safety_margin": "FLOAT: threshold / max"
    },
    "mass_conservation_drift_m3_m3": {
      "mean": "FLOAT: Maximum drift residual",
      "threshold_ceiling": "FLOAT: 0.0001"
    }
  }
}
```

---

## 4. Verification & Validation Invariants

1. **Non-Negativity Constraint:** Every scalar in `.npy` arrays must satisfy $\theta \ge 0.0$.
2. **Physical Porosity Bound:** Moisture must satisfy $\theta \le \theta_s = 0.450\,\text{m}^3/\text{m}^3$.
3. **Zero Numerical Anomalies:** All JSON and NPY files must contain **zero NaNs, Infs, or subnormal numbers**.
4. **Execution Performance SLA:** Processing time per trial across all quadrants must remain strictly below $10.0\,\text{ms/trial}$.

---

## 5. Engineering Disclosures & Limit States ("Ek Ek Dhappa")

* **Disk Storage Minimization:** Trajectories are written as flat dense matrices without temporal chunking or index headers. Reading scripts must rely on hardcoded dimensions $(N_{\text{trials}}, N_{\text{days}})$.
* **Absence of Uncertainty Propagation Covariance:** Individual trial arrays store state trajectory means. Cross-covariance matrices $\mathbf{P}_t \in \mathbb{R}^{2 \times 2}$ are processed in memory during Kalman updates but only scalar condition numbers $\kappa(\mathbf{P})$ are preserved in JSON metrics to prevent megabyte-scale file inflation.
* **Deterministic Pseudo-Randomness:** PRNG sequences use NumPy standard MT19937 seeded generators. Rerunning with identical seeds guarantees bit-for-bit identical telemetry.
