# Subsystem 09: Spaceborne Operational Campaign — In-Situ Ground Truth Architecture (`3_ground_truth/`)
## Central Unified Engine: AETHER-MRID1607X
### Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
### Author & Lead Systems Engineer: Gourgopal Mohapatra
### Release Status: TRL-7 OPERATIONAL FLIGHT READINESS

---

## 1. Executive Overview & Subsystem Mandate

The `3_ground_truth/` subsystem establishes the empirical soil physical truth baseline, in-situ sensor data contracts, and spatial-temporal collocation pipeline for the **AETHER-MRID1607X** Earth Observation processing framework. Representing Stage 3 of the Spaceborne Operational Campaign (SOC-AETHER-2026), this layer is tasked with capturing, validating, and binding real physical ground measurements with satellite pixels to enable rigorous statistical validation, classical baseline comparison, and peer-reviewed aerospace calibration.

```
+---------------------------------------------------------------------------------------------------------+
|                                     IN-SITU PHYSICAL SOIL NETWORK                                       |
|  • 24 Deployed Soil Monitoring Stations across 1.28 km x 1.28 km Mahanadi Delta AOI                     |
|  • Dual-depth TDR / High-Frequency Capacitance Probes (0-5cm Surface & 5-30cm Root-zone)                |
|  • USDA Textures: Loam, Silt Loam, Clay Loam, Sandy Loam with Bulk Density & Soil Organic Carbon        |
+---------------------------------------------------+-----------------------------------------------------+
                                                    |
                                                    v
+---------------------------------------------------------------------------------------------------------+
|                  INGESTION & SPATIAL-TEMPORAL COLLOCATION (4_execution_engine/)                         |
|  • insitu_ground_truth_ingestor.py  --> ISMN Flagging ('G'), Zero-NaN asserts, Physical [0, 0.6] bounds  |
|  • spatial_temporal_collocator.py   --> (Easting, Northing) -> 10m UTM (Pixel Row i, Col j) Mapping     |
|                                         Synchronized 29-Feature Extraction Across 4 Spaceborne Sources  |
+---------------------------------------------------+-----------------------------------------------------+
                                                    |
                                                    v
+---------------------------------------------------------------------------------------------------------+
|                        STAGE 3: 9_spaceborne_operational_campaign/3_ground_truth/                       |
|  • insitu_soil_stations.csv            ➔ 24 Station Coordinates, Textures, Densities & In-Situ Moisture|
|  • collocated_insitu_matrix.csv        ➔ 24 Rows x 29 Columns (Satellite Features + In-Situ Truth)      |
|  • aether_collocated_predictions.csv   ➔ 24 Rows x 36 Columns (AETHER Physical States + Conformal 2σ)   |
+---------------------------------------------------+-----------------------------------------------------+
                                                    |
                                                    v
+---------------------------------------------------------------------------------------------------------+
|                         DOWNSTREAM BENCHMARKING & JOURNAL CERTIFICATION                                 |
|  • 5_baseline_benchmarks/ (Naive Optical NDVI Linear Baseline & SAR Water Cloud Model WCM)              |
|  • 8_paper_artifacts/ (Peer-reviewed IEEE / MDPI Figures, Taylor Diagrams, LaTeX Benchmark Tables)      |
|  • TRL-7 Operational Flight Readiness Certificate (Root Sign-off)                                       |
+---------------------------------------------------------------------------------------------------------+
```

---

## 2. In-Situ Soil Probe Instrumentation & Standards

All ground truth observations follow internationally recognized soil calibration protocols:

| Standard / Guideline | Governing Organization | Standard Specification | Implementation in MRIDANSH |
|:---|:---|:---|:---|
| **CEOS-WGCV Match-Up Protocol** | CEOS | Spatial-temporal collocation within $\pm 1\,\text{hr}$ and native satellite pixel footprint. | Collocated to exact 10m UTM 45N pixel coordinates $(i, j)$ with time delta $\Delta t \le 30\,\text{min}$. |
| **ISMN Data Quality Taxonomy** | International Soil Moisture Network | Quality flags: `G` (Good), `M` (Dubious), `B` (Bad). | Strict enforcement: Only stations passing `G` flags are ingested into benchmark matrices. |
| **NASA SMAP Core Cal/Val** | NASA JPL / GSFC | Depth-stratified monitoring: Surface ($0-5\,\text{cm}$) vs Root-zone ($5-30\,\text{cm}$). | Dual-sensor probes installed at $z=2.5\,\text{cm}$ and $z=17.5\,\text{cm}$ centroids. |
| **USDA Soil Taxonomy** | USDA NRCS | Hydrological texture classification based on sand/silt/clay fractions. | Classifies all 24 stations into 4 alluvial delta textural classes. |

---

## 3. Mathematical Foundations & Collocation Mechanics

### 3.1 Geodetic Coordinate Mapping to 10m Raster Grid
For each station $k$ with geodetic UTM coordinates $(E_k, N_k)$, the exact raster grid pixel index $(i_k, j_k)$ is evaluated:

$$j_k = \text{clamp}\left(\left\lfloor \frac{E_k - X_{\text{min}}}{\Delta x} \right\rfloor, 0, W - 1\right)$$

$$i_k = \text{clamp}\left(\left\lfloor \frac{Y_{\text{max}} - N_k}{\Delta y} \right\rfloor, 0, H - 1\right)$$

Where $X_{\text{min}} = 420,000.0\,\text{m}$, $Y_{\text{max}} = 2,240,640.0\,\text{m}$, and $\Delta x = \Delta y = 10.0\,\text{m}$.

### 3.2 29-Feature Synchronized Collocation Vector
For each station, the collocator extracts a 29-dimensional synchronized state vector:
$$\mathbf{z}_k = [\mathbf{p}_k, \mathbf{s}_k, \mathbf{o}_k, \mathbf{d}_k, \mathbf{w}_k, \mathbf{g}_k]$$
* **Position ($\mathbf{p}_k$):** $\text{Station ID}, \text{Lat}, \text{Lon}, E, N, i, j$.
* **SAR Radar ($\mathbf{s}_k$):** $\sigma^0_{\text{VV}}\,(\text{dB}), \sigma^0_{\text{VH}}\,(\text{dB}), \text{Polarization Ratio } PR = \sigma^0_{\text{VV}} - \sigma^0_{\text{VH}}\,(\text{dB})$.
* **Optical ($\mathbf{o}_k$):** $\rho_{B02}, \rho_{B03}, \rho_{B04}, \rho_{B08}, NDVI, NDWI, M_{\text{clear}}$.
* **Topography ($\mathbf{d}_k$):** Elevation $Z\,(\text{m})$, Slope $\beta\,(^\circ)$, Aspect $\alpha\,(^\circ)$, $TWI$.
* **Weather ($\mathbf{w}_k$):** $P_{24\text{h}}\,(\text{mm})$, $T_{2\text{m}}\,(^\circ\text{C})$, $VPD\,(\text{kPa})$.
* **Ground Truth ($\mathbf{g}_k$):** $\theta_{\text{surf}}\,(\text{m}^3/\text{m}^3)$, $\theta_{\text{root}}\,(\text{m}^3/\text{m}^3)$, $\rho_b\,(\text{g/cm}^3)$, $\text{Texture}$.

### 3.3 AETHER Physical State Inversion Binding
Downstream forward inference adds 7 operational verification channels:
* Predicted Volumetric Soil Moisture: $\hat{\theta} \in [0.1140, 0.2557]\,\text{m}^3/\text{m}^3$.
* Vadose Zone Pore Pressure Suction Head: $h \in [-5181.17, -86.96]\,\text{cm}$.
* Unsaturated Hydraulic Conductivity: $K(\theta) \in [0.0, 0.0022]\,\text{cm/hr}$.
* Conformal Prediction Uncertainty Bounds ($2\sigma$ coverage at $95\%$ confidence):
  $$\hat{\theta}_{\text{lower}} = \max(0, \hat{\theta} - 2\sigma_\theta), \quad \hat{\theta}_{\text{upper}} = \min(1, \hat{\theta} + 2\sigma_\theta)$$
  Where conformal margin $2\sigma_\theta = 0.0384\,\text{m}^3/\text{m}^3$ (with $\sigma_\theta = 0.0192$).

---

## 4. Formal Verification & Testing Scorecard (SOC-11 to SOC-15)

The ground truth subsystem is validated through automated Pytest test suites (`tests/test_insitu_collocation_and_baselines.py`).

| Verification ID | Verification Rule / Contract | Target Envelope | Measured Test Outcome | Pass/Fail Status |
|:---|:---|:---|:---|:---:|
| **`SOC-11`** | In-Situ Ground Truth Ingestion Bounds | $\theta \in [0.05, 0.55]$, $\rho_b \in [1.0, 1.8]\,\text{g/cm}^3$, Zero NaNs | 24 stations, $\bar{\theta}_{\text{surf}}=0.1855$, $\bar{\rho}_b=1.3784$, 100% valid | **PASS** |
| **`SOC-12`** | Spatial-Temporal Collocation Grid Accuracy | Pixel coordinates $(i, j) \in [0, 63]$, zero out-of-bounds | 100% stations mapped into $64 \times 64$ grid | **PASS** |
| **`SOC-13`** | Physical Sensor Correlation Integrity | Pearson $r(\sigma^0_{\text{VV}}, \theta_{\text{surf}}) > 0.40$ | Measured $r = +0.584$ (strong dielectric coupling) | **PASS** |
| **`SOC-14`** | Naive Optical Regression Baseline | Train Carlson-Ripley empirical baseline | $R^2 = 0.182$, $RMSE = 0.0612\,\text{m}^3/\text{m}^3$ | **PASS** |
| **`SOC-15`** | SAR Water Cloud Model (WCM) Baseline | Attema-Ulaby semi-empirical inversion | $R^2 = 0.441$, $RMSE = 0.0487\,\text{m}^3/\text{m}^3$ | **PASS** |

---

## 5. "Ek Ek Dhappa" — Brutally Honest Engineering Disclosures & Limitations

1. **Point-to-Pixel Spatial Representativeness Scale Gap:**
   - *Dhappa:* An in-situ TDR sensor measures soil permittivity in an immediate electromagnetic sphere of influence of $\sim 100\,\text{cm}^3$. A single Sentinel-1/Sentinel-2 pixel represents a surface footprint of $100\,\text{m}^2$ ($10\,\text{m} \times 10\,\text{m}$), which is a **$1,000,000\times$ volume disparity**.
   - *Compromise:* Sub-pixel soil heterogeneities (e.g., small irrigation furrows, localized micro-depressions, localized cattle compaction) within the 10m pixel cannot be captured by a single station. Validation metrics inevitably reflect a portion of spatial representativeness error rather than pure model inversion error.

2. **Probe Electronic Calibration Discrepancy (Campbell TDR vs Stevens HydraProbe):**
   - *Dhappa:* The network employs two distinct physical probe architectures: Campbell CS616 time-domain reflectometers (175 MHz) and Stevens HydraProbe coaxial impedance dielectric sensors (50 MHz).
   - *Compromise:* At high tropical soil temperatures ($>29^\circ\text{C}$), the temperature sensitivity of the apparent dielectric permittivity differs between 50 MHz and 175 MHz. A systematic offset of $\Delta \theta \approx 0.012\,\text{m}^3/\text{m}^3$ exists between probe types in heavy clay loam soils.

3. **Sparse Station Density (24 Stations over 164 ha):**
   - *Dhappa:* 24 stations over a $1.28\,\text{km} \times 1.28\,\text{km}$ delta area corresponds to an average density of $\sim 1$ station per 6.8 hectares.
   - *Compromise:* While meeting NASA SMAP Core Cal/Val criteria ($\ge 1$ station per $36\,\text{km}^2$ for coarse SMAP grids), fine-scale 10m spatial variograms cannot be fully reconstructed without geostatistical kriging interpolation assumptions.

---

## 6. Cross-Subsystem Traceability Matrix

| In-Situ Component | Originating File | Collocated Intermediate File | Downstream Consumer |
|:---|:---|:---|:---|
| Physical Soil Observations | `insitu_soil_stations.csv` | `collocated_insitu_matrix.csv` | `4_execution_engine/spatial_temporal_collocator.py` |
| 29-Feature Synchronized Matrix | `collocated_insitu_matrix.csv` | `aether_collocated_predictions.csv` | `4_execution_engine/comparative_baseline_benchmarks.py` |
| Benchmarking Predictions | `aether_collocated_predictions.csv` | `5_baseline_benchmarks/` | `8_paper_artifacts/` & Master Monograph |
| In-Situ Cal/Val Metrics | Pytest Suite (`SOC-11`..`15`) | Root Flight Certificate | `TRL7_OPERATIONAL_FLIGHT_READINESS_CERTIFICATE.md` |
