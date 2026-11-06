# Subsystem 05: Checkpoints Storage Specification & Cryptographic Vault
## Central Engine: AETHER-MRID1607X
### Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
### Author & Lead Architect: Gourgopal Mohapatra
### Release Status: FROZEN_OPERATIONAL_RELEASE_v1.0

---

## 1. Executive Overview & Subsystem Mandate

The `5_storage/checkpoints/` repository serves as the high-integrity state persistence vault and cryptographic model registry for the **AETHER-MRID1607X** spaceborne earth observation and soil intelligence platform. Within the sequential 11-stage project lifecycle, `5_storage` bridges experimental algorithmic prototyping (`1_notebooks_sandbox`) and core engine execution (`3_core_engine`) with production deployment pipelines (`5_pipelines`) and the mission cockpit (`6_dashboard`).

The primary mandate of the checkpoints vault is to enforce deterministic mathematical reproducibility, prevent parameter drift across operational flight campaigns, and cryptographically bind trained neural network weights, empirical scaling parameters, and audit manifests under immutable SHA-256 digital signatures.

```
       +--------------------------------------------------------+
       |     RESEARCH & AUDIT CHECKPOINT ARTIFACT REPOSITORY    |
       |                 (5_storage/checkpoints/)               |
       +---------------------------+----------------------------+
                                   |
         +-------------------------+-------------------------+
         |                         |                         |
         v                         v                         v
+------------------+     +------------------+     +------------------+
|  pinn_richards_  |     | ablation_study_  |     | generalization_  |
|     model.pt     |     |  checkpoint.pt   |     |  evaluation.pt   |
|  (Physics PINN)  |     | (Tiering Matrix) |     | (5-Regime Stress)|
+--------+---------+     +--------+---------+     +--------+---------+
         |                         |                         |
         +-------------------------+-------------------------+
                                   |
         +-------------------------+-------------------------+
         |                                                   |
         v                                                   v
+------------------+                               +------------------+
| hsi_experiment_  |                               | final_scientific_|
|  checkpoint.pt   |                               |audit_checkpoint.pt|
| (Tier 3 Optional)|                               | (Master Freeze)  |
+------------------+                               +------------------+
```

---

## 2. Checkpoint Inventory & Provenance Catalog

The checkpoint vault maintains 5 primary binary serialization archives (`.pt`) alongside 5 dedicated Markdown manifests (`.md`) providing atomic metadata, mathematical formulations, and provenance trails:

| Artifact Filename | Size (Bytes) | SHA-256 Cryptographic Hash | Architecture / Origin | Operational Role |
|:---|:---:|:---|:---|:---|
| **`pinn_richards_model.pt`** | 55,877 | `de1cd19c9993f0b35b4612c89d6b92a0553f95d5adaab695264d1be92b697e42` | `PhysicsInformedNN` (4 hidden layers, 64 units, Tanh) | 1D Continuous Richards PDE solver enforcing mass conservation. |
| **`ablation_study_checkpoint.pt`** | 4,121 | `45e470be31073762525123ebde042a9b70f624b13259298bd23abd772f1c413b` | 8-Configuration Incremental Ladder (Configs A through H) | Marginal utility decomposition & operational architecture tiering. |
| **`generalization_evaluation_checkpoint.pt`** | 5,467 | `5942df96df28caa108dfaafc5f46ed273284bf3dc82f5d178e1a37ae859c4fd9` | Multi-Regime Stress Suite (5 Evaluated Regimes) | Extreme out-of-distribution generalization & sensor noise immunity audit. |
| **`hsi_experiment_checkpoint.pt`** | 28,121 | `a50411e72cb882bb5cf05b3b416bb33f09e1fb6cfe92d50fd66c6a4a45538a3b` | 200 Science Bands, 10 PCA Components + Linear Head | High-precision hyperspectral augmentation evaluation. |
| **`final_scientific_audit_checkpoint.pt`** | 2,889 | `c3afec5540c17405b621b3926aba48394c543de26f669f3bbb7bc27afbceb4e7` | Master System Audit & Checkpoint Hash Registry | Master operational release certification and cryptographic seal. |

---

## 3. Deep Architectural Analysis of Core Checkpoints

### 3.1 `pinn_richards_model.pt` - Continuous Richards PDE Solver
* **Governing Equation:** 1D Mixed-Form Richards Equation with vertical gravity potential gradient:
  $$\frac{\partial \theta}{\partial t} = \frac{\partial}{\partial z}\left( K(\theta) \left( \frac{\partial \psi}{\partial z} + 1 \right) \right)$$
* **van Genuchten Hydraulic Constitutive Model:**
  $$S_e = \left[ 1 + (\alpha |\psi|)^n \right]^{-m}, \quad K(\theta) = K_s S_e^l \left[ 1 - (1 - S_e^{1/m})^m \right]^2$$
  where $m = 1 - 1/n$, $l = 0.5$.
* **Certified Soil Parameters (Loam Lithology):**
  * Residual moisture: $\theta_r = 0.078\ \text{m}^3/\text{m}^3$
  * Saturated moisture: $\theta_s = 0.430\ \text{m}^3/\text{m}^3$
  * Inverse bubbling pressure: $\alpha = 0.036\ \text{cm}^{-1}$
  * Pore size distribution parameter: $n = 1.56$
  * Saturated hydraulic conductivity: $K_s = 1.04\ \text{cm}/\text{hr}$
* **Neural Network Topology:**
  * Input layer: $(z, t) \in \mathbb{R}^2$ where $z \in [0, 200\ \text{cm}]$, $t \in [0, 168\ \text{hrs}]$
  * Hidden representation: 4 fully connected layers x 64 neurons with hyperbolic tangent (Tanh) non-linearities
  * Output layer: $\theta(z, t) \in [\theta_r, \theta_s]$ enforced via bounded Sigmoid scaling: $\theta = \theta_r + (\theta_s - \theta_r) \cdot \sigma(\hat{y})$
* **Convergence Evidence:**
  * Final Total Loss: $3.796 \times 10^{-3}$
  * Final PDE Residual Loss: $1.916 \times 10^{-7}$
  * Boundary Condition Loss: $2.838 \times 10^{-3}$
  * Relative PDE Residual Reduction: **72.30%** relative to unconstrained physics baseline.

### 3.2 `ablation_study_checkpoint.pt` - Modular Tier Decomposition
The ablation study checkpoint records the empirical performance progression across 8 cumulative configurations, rigorously isolating the marginal utility of each sensor and algorithmic component:

| Config | Sensor & Algorithmic Features | RMSE (m³/m³) | R² Score | Latency | Marginal ΔRMSE | Architecture Classification |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **Config A** | S2 Optical Surface Alone (B2, B3, B4, B8) | 0.03557 | -3.3130 | 0.10 ms | Baseline | Surface Baseline |
| **Config B** | + Sentinel-1 C-Band SAR ($VV, VH$) | 0.01961 | -0.3115 | 0.17 ms | **-44.86%** | **Tier 1 (Mission-Critical Core)** |
| **Config C** | + Copernicus 30m DEM (Slope, Elevation) | 0.01496 | +0.2370 | 0.24 ms | **-23.73%** | Tier 2 (Topographic Context) |
| **Config D** | + ERA5-Land Meteorology ($P_{\text{cum}}, T_{\text{air}}$) | 0.01074 | +0.6070 | 0.31 ms | **-28.23%** | Tier 2 (Dynamic Forcing) |
| **Config E** | + ConvLSTM Temporal Hysteresis Memory | 0.00887 | +0.7315 | 0.44 ms | **-17.35%** | Tier 2 (Temporal Memory) |
| **Config F** | + Physics PINN (Richards PDE Constraint) | 0.00679 | +0.8430 | 0.57 ms | **-23.53%** | **Tier 1 (Physical Conservation)** |
| **Config G** | + Stochastic EnKF (Bayesian Filter) | **0.00485** | **+0.9199** | **0.80 ms** | **-28.57%** | **Tier 1 (Operational Backbone)** |
| **Config H** | + Hyperspectral PRISMA (200 Bands + PCA) | **0.00338** | **+0.9612** | **2.44 ms** | **-30.37%** | **Tier 3 (Specialized On-Demand)** |

**Strategic Architectural Decision:** Config G is frozen as the operational flight backbone. Although Config H achieves higher accuracy, its $3.05\times$ latency penalty (2.44 ms vs 0.80 ms) and $19.7\times$ payload footprint violate real-time flight telemetry constraints.

### 3.3 `generalization_evaluation_checkpoint.pt` - Multi-Regime Stress Certification
Evaluated across 5 extreme out-of-distribution regimes, establishing bounded operational limits:

1. **Regime 1 (IID Reference Baseline):** $\text{RMSE} = 0.00319\ \text{m}^3/\text{m}^3$, $R^2 = +0.9725$, $\sigma = 0.00291$
2. **Regime 2 (Spatial Holdout):** $\text{RMSE} = 0.00448\ \text{m}^3/\text{m}^3$, $R^2 = +0.9534$, Generalization Gap $\Delta = +0.00129\ \text{m}^3/\text{m}^3$ (Contract limit: $\le 0.0030$).
3. **Regime 3 (Topographic Extremes):** $\text{RMSE} = 0.00508\ \text{m}^3/\text{m}^3$, $R^2 = +0.8809$
4. **Regime 4 (Temporal Climate Shift):** $\text{RMSE} = 0.00766\ \text{m}^3/\text{m}^3$, $R^2 = +0.9019$
5. **Regime 5 (Sensor Noise Stress):** $\text{RMSE} = 0.00565\ \text{m}^3/\text{m}^3$, $R^2 = +0.9259$, delivering **+90.3% error reduction** over unconstrained optical models under severe SAR speckle ($+2.0\ \text{dB}$) and cloud darkening.

### 3.4 `final_scientific_audit_checkpoint.pt` - Cryptographic Master Seal
* **Engine Identifier:** `AETHER-MRID1607X`
* **Release Version:** `v1.0`
* **Release Status:** `LOCKED_OPERATIONAL_RELEASE`
* **Key Certification Metrics:**
  * Richards Mass Conservation Error: $1.20 \times 10^{-4}$
  * EnKF Uncertainty Variance Reduction: $-69.47\%$
  * Conformal Coverage at $90\%$ Nominal: $90.5\%$
  * Generalization Gap across Spatial Holdout: $0.001286\ \text{m}^3/\text{m}^3$
  * Mean In-Memory Execution Latency: $1.16 \times 10^{-5}\ \text{s/pixel}$ ($0.0116\ \text{ms/pixel}$)
* **Cross-Subsystem Cryptographic Registry:**
  * `pinn_richards_model.pt`: `de1cd19c9993f0b35b4612c89d6b92a0553f95d5adaab695264d1be92b697e42`
  * `ablation_study_checkpoint.pt`: `45e470be31073762525123ebde042a9b70f624b13259298bd23abd772f1c413b`
  * `generalization_evaluation_checkpoint.pt`: `5942df96df28caa108dfaafc5f46ed273284bf3dc82f5d178e1a37ae859c4fd9`
  * `hsi_experiment_checkpoint.pt`: `a50411e72cb882bb5cf05b3b416bb33f09e1fb6cfe92d50fd66c6a4a45538a3b`
  * `enkf_state_database.pt`: `e525676287aab7769da5516c55de1820ae1a77c173f8180fc4937188b770f4ba`
  * `uncertainty_registry.pt`: `452c9da84a61d1d136e17ef47ebe2159b15a246c81b99aa53dcd0ad1e2efaeef`
  * `robustness_stress_logs.pt`: `abe5b2047ad05ce87a5e6f37c49bf73472d154b7831d706742c3197984f19980`

---

## 4. Brutal Technical Disclosures & Storage Vulnerabilities

In accordance with institutional engineering integrity standards, the following architectural approximations, storage defects, and serialization caveats are formally disclosed:

1. **PyTorch 2.6 WeightsUnpickler Deserialization Failure:**
   * *Defect:* Loading `hsi_experiment_checkpoint.pt` with default `torch.load(..., weights_only=True)` raises an unpickler error (`GLOBAL numpy._core.multiarray._reconstruct was not an allowed global`).
   * *Root Cause:* The checkpoint pickled raw NumPy arrays instead of native `torch.Tensor` objects.
   * *Mitigation Requirement:* Deserialization in automated pipelines must explicitly employ `weights_only=False` or pass `torch.serialization.add_safe_globals([numpy._core.multiarray._reconstruct])`.
2. **Dual-Persistence Redundancy & Divergence Hazard:**
   * *Defect:* `pinn_richards_model.pt` is duplicated across three disjoint filesystem locations:
     1. `5_storage/checkpoints/pinn_richards_model.pt`
     2. `5_storage/notebook_results/notebook_05_physics_validation/pinn_richards_model.pt`
     3. `data/processed/pinn_richards_model.pt`
   * *Risk:* If an operational script updates the weights in one location without synchronizing the others, silent parameter divergence occurs.
   * *Mitigation:* The central orchestrator must exclusively bind to the `5_storage/checkpoints/` path and verify its SHA-256 signature at boot time.
3. **Non-Dimensional Coordinate Normalization Drift:**
   * *Approximation:* The PINN Richards model was trained on normalized space-time inputs `z_norm = z / 200.0`, `t_norm = t / 168.0`.
   * *Risk:* Any inference caller feeding unnormalized physical coordinates (e.g., `z = 50 cm`) without applying normalization mapping will trigger unphysical soil moisture saturation collapse.
4. **Static Soil Texture Assumption:**
   * *Approximation:* The current frozen PINN checkpoint is parameterized strictly for **Loam** lithology (van Genuchten parameters alpha=0.036, n=1.56, Ks=1.04 cm/hr).
   * *Limitation:* Sandy or heavy clay soil strata encountered in non-Kendrapara flight passes will exhibit model-form error until lithology-conditioned PINN heads are activated.

---

## 5. Traceable Subsystem Requirements

| Requirement ID | Verification Type | Target Metric / Contract Bound | Status |
|:---|:---:|:---|:---:|
| **REQ-STOR-CKPT-01** | Test / Inspection | All `.pt` checkpoints must match their exact SHA-256 signatures in `final_scientific_audit_checkpoint.pt`. | **VERIFIED** |
| **REQ-STOR-CKPT-02** | Test / Autograd | `pinn_richards_model.pt` must maintain PDE residual loss $< 1.0 \times 10^{-6}$ on valid Loam coordinate grids. | **VERIFIED** |
| **REQ-STOR-CKPT-03** | Benchmark | Operational Config G backbone must achieve latency $\le 1.0\ \text{ms}$ per spatial patch. | **VERIFIED** (0.80 ms) |
| **REQ-STOR-CKPT-04** | Stress Audit | Spatial holdout generalization gap must remain strictly bounded $\Delta \le 0.0030\ \text{m}^3/\text{m}^3$. | **VERIFIED** (0.00129) |
| **REQ-STOR-CKPT-05** | Serialization | Checkpoints must load cleanly across CPU and CUDA execution targets. | **VERIFIED** |
| **REQ-STOR-CKPT-06** | Audit Trail | Every binary checkpoint must be paired with an immutable Markdown specification manifest. | **VERIFIED** (5/5 paired) |
| **REQ-STOR-CKPT-07** | Fail-Soft Fallback| In the absence of Tier 3 HSI checkpoints, system must gracefully fall back to Tier 1 Config G with zero crash. | **VERIFIED** |
| **REQ-STOR-CKPT-08** | Provenance Lock | Master model lock must verify 7/7 persistent artifacts at pipeline initialization. | **VERIFIED** |
