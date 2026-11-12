# Subsystem 05: Uncertainty Quantification Registry Specification
## Central Engine: AETHER-MRID1607X
### Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
### Author & Lead Architect: Gourgopal Mohapatra
### Release Status: FROZEN_OPERATIONAL_RELEASE_v1.0

---

## 1. Executive Overview & Subsystem Mandate

The `5_storage/registry/` repository serves as the centralized empirical calibration store and uncertainty quantification registry for the **AETHER-MRID1607X** earth observation platform. Originating from the rigorous statistical validation executed in Stage 07 (`1_notebooks_sandbox/07-uncertainty-analysis.ipynb`), this subsystem encapsulates the parameters governing orthogonal 4-component variance decomposition, empirical coverage calibration tables, and automated fail-soft triggers.

The primary mandate of the uncertainty registry is to provide downstream domain translators (agronomy irrigation, civil geotechnical bearing, and tractor trafficability) with distribution-free, mathematically bounded confidence metrics. Rather than outputting point predictions of soil moisture $\theta$, every pixel is accompanied by an empirically calibrated composite standard deviation $\sigma_{\text{total}}$ and a mapped confidence score $\mathcal{C} \in [0, 100\%]$.

```
       +--------------------------------------------------------------+
       |         MULTI-SOURCE UNCERTAINTY INGESTION & COVARIANCE      |
       |           (Ensemble + Sensors + Temporal Gap + Model)        |
       +------------------------------+-------------------------------+
                                      |
                      [Orthogonal Variance Decomposer]
                                      |
         +----------------------------+----------------------------+
         |                            |                            |
         v                            v                            v
+------------------+         +------------------+         +------------------+
| Ensemble Spread  |         | Net Sensor Noise |         | Latency Gap &    |
| (Sigma_ens:      |         | (Sigma_sensor:   |         | Model Disagree   |
|  0.0310 m3/m3)   |         |  0.0187 m3/m3)   |         | (0.0123, 0.0179) |
+--------+---------+         +--------+---------+         +--------+---------+
         |                            |                            |
         +----------------------------+----------------------------+
                                      |
                                      v
                 +------------------------------------------+
                 | Composite Standard Deviation: Sigma_total|
                 | (Root-Sum-Squares: 0.0430 m3/m3)         |
                 +--------------------+---------------------+
                                      |
         +----------------------------+----------------------------+
         |                                                         |
         v                                                         v
+------------------------------------+    +------------------------------------+
|  UNCERTAINTY_REGISTRY_MANIFEST.md  |    |     uncertainty_registry.pt        |
|  (Human-Readable Specification)    |    |     (Binary Serialization Vault)   |
+------------------------------------+    +------------------------------------+
```

---

## 2. Registry Artifact Inventory & Cryptographic Signatures

The uncertainty registry vault maintains two synchronized artifacts ensuring human-readable traceability and high-performance in-memory deserialization:

| Artifact Filename | Size (Bytes) | SHA-256 Cryptographic Hash | Storage Category | Primary Role |
|:---|:---:|:---|:---|:---|
| **`uncertainty_registry.pt`** | 40,379 | `452c9da84a61d1d136e17ef47ebe2159b15a246c81b99aa53dcd0ad1e2efaeef` | PyTorch Binary Archive | Persisted 2D spatial uncertainty arrays, calibration tables, and stress benchmarks. |
| **`UNCERTAINTY_REGISTRY_MANIFEST.md`** | 1,661 | `1ff98eb62507850257e8020a59124403328eb9ae8e3c153bca51ef4075191ecb` | Specification Manifest | Authoritative metadata, variance budgets, reliability proofs, and downstream contract. |

---

## 3. Mathematical Formulation of Uncertainty Decomposition

The system implements an **Orthogonal 4-Component Variance Decomposition Model** that partitions total predictive uncertainty into physically interpretable aleatoric and epistemic constituents:

$$\sigma_{\text{total}}^2 = \sigma_{\text{ens}}^2 + \sigma_{\text{sensor}}^2 + \sigma_{\text{gap}}^2 + \sigma_{\text{model}}^2$$

$$\sigma_{\text{total}} = \sqrt{\sigma_{\text{ens}}^2 + \sigma_{\text{sensor}}^2 + \sigma_{\text{gap}}^2 + \sigma_{\text{model}}^2}$$

### 3.1 Component Variance Budget

| Uncertainty Component | Physical Source | Statistical Nature | Mean Value (m³/m³) | Contribution to Total Variance (%) |
|:---|:---|:---|:---:|:---:|
| **Ensemble Spread ($\sigma_{\text{ens}}$)** | 50-member EnKF posterior state dispersion | Epistemic / State | **0.0310** | **51.97%** |
| **SAR Speckle ($\sigma_{\text{sar}}$)** | Residual radar backscatter speckle variance | Aleatoric / Sensor | 0.0130 | 9.14% |
| **Cloud Noise ($\sigma_{\text{cloud}}$)** | Multispectral atmospheric contamination | Aleatoric / Sensor | 0.0100 | 5.41% |
| **Net Sensor Noise ($\sigma_{\text{sensor}}$)** | $\sqrt{\sigma_{\text{sar}}^2 + \sigma_{\text{cloud}}^2}$ | Aleatoric / Sensor | **0.0187** | **18.88%** |
| **Temporal Latency Gap ($\sigma_{\text{gap}}$)** | Satellite revisit gap drying drift ($0 - 120\text{ hrs}$) | Epistemic / Latency | **0.0123** | **8.18%** |
| **Input Availability ($\sigma_{\text{avail}}$)** | Missing modality indicator penalty | Epistemic / Flux | 0.0008 | 0.03% |
| **Model Disagreement ($\sigma_{\text{model}}$)** | Divergence between ConvLSTM and PINN heads | Epistemic / Model | **0.0179** | **17.33%** |
| **Composite Total ($\sigma_{\text{total}}$)** | Root-sum-square combination | Total Combined | **0.0430** | **100.00%** |

### 3.2 Confidence Score Mapping Function
The continuous composite uncertainty $\sigma_{\text{total}}$ is non-linearly mapped into an operational confidence index $\mathcal{C} \in [0, 100\%]$:

$$\mathcal{C} = 100 \times \left(1 - \frac{\sigma_{\text{total}} - \sigma_{\min}}{\sigma_{\max} - \sigma_{\min}}\right)$$

* Mean Confidence Score: **$52.63\%$**
* Min Standard Deviation: $\sigma_{\min} = 0.0302\ \text{m}^3/\text{m}^3$ (Yields $\mathcal{C} = 100\%$)
* Max Standard Deviation: $\sigma_{\max} = 0.0559\ \text{m}^3/\text{m}^3$ (Yields $\mathcal{C} = 0\%$)

---

## 4. Empirical Reliability & Calibration Proofs

The stored calibration metrics prove that the predicted error bars match true Gaussian empirical error distributions within strict margins:

### 4.1 Gaussian Interval Coverage Calibration

| Interval | Theoretical Nominal Coverage | Empirical Observed Coverage | Discrepancy (Error Bound) | Certification Status |
|:---:|:---:|:---:|:---:|:---:|
| **$1\sigma$ Interval ($[-\sigma, +\sigma]$)** | $68.27\%$ | **$67.32\%$** | **$0.95\%$** ($< 2.0\%$ target) | **CERTIFIED** |
| **$2\sigma$ Interval ($[-2\sigma, +2\sigma]$)** | $95.45\%$ | **$95.32\%$** | **$0.13\%$** ($< 1.0\%$ target) | **CERTIFIED** |
| **$3\sigma$ Interval ($[-3\sigma, +3\sigma]$)** | $99.73\%$ | **$99.76\%$** | **$0.03\%$** ($< 0.5\%$ target) | **CERTIFIED** |

### 4.2 Error Monotonicity & Confidence Tiering
The registry confirms strict negative rank correlation between mapped confidence and true prediction error:
* **Decile Rank Correlation:** $r = -0.9208$ (Proves higher confidence monotonically indicates smaller error).
* **Tier 1 (High Confidence):** $\text{MAE} = 0.0297\ \text{m}^3/\text{m}^3$.
* **Tier 2 (Medium Confidence):** $\text{MAE} = 0.0351\ \text{m}^3/\text{m}^3$.
* **Tier 3 (Low Confidence):** $\text{MAE} = 0.0497\ \text{m}^3/\text{m}^3$.
* Strictly adheres to monotonic order: $\text{MAE}_{\text{high}} < \text{MAE}_{\text{med}} < \text{MAE}_{\text{low}}$.

### 4.3 Pre-computed Stress Outage Benchmarks
* **Simulated Cloud Outage Scenario:** Composite $\sigma$ surges to **$0.0607\ \text{m}^3/\text{m}^3$**, depressing mean confidence to **$40.32\%$**.
* **Simulated Full Sensor Blackout:** Composite $\sigma$ explodes to **$0.0888\ \text{m}^3/\text{m}^3$**, dropping confidence to **$26.41\%$** and automatically triggering fail-soft physics-only fallback.

---

## 5. Brutal Technical Disclosures & Known Limitations

In accordance with institutional engineering integrity standards, the following assumptions, storage caveats, and mathematical compromises are formally disclosed:

1. **PyTorch 2.6 Serialization Caveat:**
   * *Observation:* `uncertainty_registry.pt` serializes nested NumPy arrays and dictionaries.
   * *Impact:* Loading with `torch.load(..., weights_only=True)` raises security exceptions in PyTorch 2.6 environments. Downstream services must load using `weights_only=False`.
2. **Orthogonality Assumption under Severe Overcast:**
   * *Approximation:* The composite variance calculation assumes zero covariance between sensor noise ($\sigma_{\text{sensor}}$) and model disagreement ($\sigma_{\text{model}}$).
   * *Caveat:* In persistent monsoon conditions, thick cloud cover simultaneously degrades optical surface reflectance while causing model physics divergence, introducing non-zero positive cross-covariance that can slightly underestimate total variance by $3 - 5\%$.
3. **Spatial Grid Resolution Scaling:**
   * *Observation:* The raw arrays inside `uncertainty_registry.pt` are structured over a $20 \times 20$ spatial grid representing the initial OSSE validation benchmark.
   * *Production Translation:* When ingested by the $64 \times 64$ ($10\text{m}$) production flight engine, bilinear spatial resampling is applied, smoothing localized sub-pixel uncertainty spikes.
4. **Gaussian Symmetry vs. Physical Saturation Bounds:**
   * *Limitation:* The symmetric $\pm k\sigma$ interval can mathematically extend below residual water content $\theta_r$ or above saturation $\theta_s$ in extreme wet/dry conditions. Production downstream filters must explicitly clamp conformal confidence intervals to physical bounds $[	heta_r, \theta_s]$.

---

## 6. Traceable Subsystem Requirements Matrix

| Requirement ID | Verification Type | Contract Specification / Bound | Compliance Status |
|:---|:---:|:---|:---:|
| **REQ-STOR-REG-01** | Cryptography | `uncertainty_registry.pt` must match SHA-256 signature in `final_scientific_audit_checkpoint.pt`. | **VERIFIED** |
| **REQ-STOR-REG-02** | Calibration | $1\sigma$ empirical coverage discrepancy must remain strictly $< 2.0\%$ from nominal ($68.27\%$). | **VERIFIED** (0.95%) |
| **REQ-STOR-REG-03** | Calibration | $2\sigma$ empirical coverage discrepancy must remain strictly $< 1.0\%$ from nominal ($95.45\%$). | **VERIFIED** (0.13%) |
| **REQ-STOR-REG-04** | Calibration | $3\sigma$ empirical coverage discrepancy must remain strictly $< 0.5\%$ from nominal ($99.73\%$). | **VERIFIED** (0.03%) |
| **REQ-STOR-REG-05** | Monotonicity | Decile rank correlation between confidence and true residual must be $\le -0.85$. | **VERIFIED** (-0.9208) |
| **REQ-STOR-REG-06** | Tier Order | Error across confidence tiers must strictly satisfy $\text{MAE}_{\text{high}} < \text{MAE}_{\text{med}} < \text{MAE}_{\text{low}}$. | **VERIFIED** |
| **REQ-STOR-REG-07** | Fail-Soft Trigger | Sensor blackout stress scenario must detect confidence drop below $30\%$ threshold. | **VERIFIED** (26.41%) |
| **REQ-STOR-REG-08** | Manifest Sync | `UNCERTAINTY_REGISTRY_MANIFEST.md` metrics must match binary data with zero discrepancy. | **VERIFIED** |
