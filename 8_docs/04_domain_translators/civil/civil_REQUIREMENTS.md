# Subsystem 04: Civil Geotechnics & Soil Mechanics Engine (`4_domain_translators/civil`)
## Central Engine: AETHER-MRID1607X
### Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
### Author & Lead Architect: Gourgopal Mohapatra
### Release Status: FROZEN_OPERATIONAL_RELEASE_v1.0

---

## 1. Executive Overview & Subsystem Mandate

The `4_domain_translators/civil/` subsystem constitutes the unsaturated soil mechanics, foundation bearing capacity, slope stability, drainage intelligence, and dynamic disaster simulation engine for the **AETHER-MRID1607X** platform. Operating downstream of `3_core_engine/` volumetric moisture and uncertainty tensors, this subsystem applies classical and unsaturated geotechnical engineering laws—specifically **van Genuchten (1980)** matric suction, **Fredlund & Morgenstern** extended Mohr-Coulomb shear strength, **Meyerhof-Hansen** bearing capacity, **Infinite Slope** stability, and **Beven-Kirkby Topographic Wetness Index (TWI)**—to evaluate infrastructure trafficability and structural risk.

```
       +-------------------------------------------------------------------------+
       |              UNIFIED SOIL STATE & DEM TOPOGRAPHY INPUTS                 |
       |  • Volumetric Moisture (theta_surf, theta_rz), Conformal Uncertainty ±2σ|
       |  • Copernicus 30m / 10m Resampled DEM Elevation Grid                    |
       +------------------------------------+------------------------------------+
                                            |
                                            v
       +-------------------------------------------------------------------------+
       |                 SOIL MECHANICS CORE (soil_mechanics_core.py)            |
       |  • van Genuchten Analytical Matric Suction Inversion (psi <= 10 MPa)    |
       |  • Bishop Effective Stress & Fredlund Apparent Cohesion                 |
       |  • 3-Horizon Stratification (Skin, Subbase, Foundation)                 |
       +------------------------------------+------------------------------------+
                                            |
         +----------------------------------+----------------------------------+
         |                                  |                                  |
         v                                  v                                  v
+-----------------------+        +-----------------------+        +-----------------------+
|  GROUND STABILITY     |        |  SLOPE STABILITY      |        |  DRAINAGE & TWI       |
| (ground_stability_    |        | (slope_stability_     |        | (drainage_            |
|  engine.py)           |        |  engine.py)           |        |  intelligence.py)     |
| • Meyerhof-Hansen     |        | • Infinite Slope FS   |        | • D8 Runoff Direction |
|   Nc, Nq, Ngamma      |        | • Flat Guard (0.5 deg)|        | • Specific Catchment  |
| • q_ult & q_allow     |        | • Landslide Hazard    |        | • TWI = ln(a/tan B)   |
+-----------+-----------+        +-----------+-----------+        +-----------+-----------+
            |                                |                                |
            +--------------------------------+--------------------------------+
                                             |
                                             v
       +-------------------------------------------------------------------------+
       |           DYNAMIC SCENARIO & CONFORMAL RISK ENGINE                      |
       |  • DynamicScenarioSimulator: Heavy Rainfall Surge, Vehicle Mobility,    |
       |    and Flood Liquefaction (Quicksand LSI >= 0.70)                       |
       |  • ConformalGeotechnicalRiskDispatcher: ±2σ Risk Envelope               |
       |  • CivilGeoTIFFExporter: 4-Band COG Stack + SHA-256 Audit Digest        |
       +-------------------------------------------------------------------------+
```

---

## 2. Module Inventory & Architectural Responsibilities

The `civil/` package comprises 9 files providing soil mechanics, stability grading, disaster simulation, and COG export:

| File Path | File Size | Module Classification | Key Architectural Responsibilities |
|:---|:---:|:---|:---|
| **`soil_mechanics_core.py`** | 12.2 KB | Unsaturated Physics | `SoilMechanicsCoreEngine`: van Genuchten matric suction inversion, Bishop effective stress, Fredlund apparent cohesion, and 3-horizon stratification. |
| **`ground_stability_engine.py`** | 7.9 KB | Foundation Bearing | `GroundStabilityEngine`: Meyerhof-Hansen factors ($N_c, N_q, N_\gamma$), shape/depth factors, ultimate $q_{\text{ult}}$, and allowable $q_{\text{allow}} = q_{\text{ult}}/FS$. |
| **`slope_stability_engine.py`** | 7.0 KB | Landslide Analytics | `SlopeStabilityEngine`: Infinite slope planar safety factor $FS$, flat-terrain singularity clamp ($eta < 0.5^\circ$), and 3-tier hazard grading. |
| **`drainage_intelligence.py`** | 8.4 KB | Runoff & TWI | `DrainageIntelligenceEngine`: Terrain gradients, steepest-descent flow direction, catchment area, and Beven-Kirkby TWI bounded in $[2.0, 20.0]$. |
| **`scenario_simulator.py`** | 14.9 KB | Stress Testing | `DynamicScenarioSimulator`: Heavy rainfall suction collapse, heavy vehicle mobility grading, and flood liquefaction / quicksand susceptibility. |
| **`conformal_geotechnical_risk.py`**| 7.1 KB | Conformal Risk | `ConformalGeotechnicalRiskDispatcher`: Propagates AETHER $\pm 2\sigma$ moisture bounds into conservative bearing capacity envelopes. |
| **`civil_geotiff_exporter.py`** | 9.2 KB | COG Exporter | `CivilGeoTIFFExporter`: Writes 4-band geotechnical GeoTIFFs with SHA-256 provenance and Windows file-lock safety. |
| **`geotechnical_taxonomy.json`** | 6.3 KB | Parameter Registry | Reference geotechnical constants ($c', \phi', \phi^b, \alpha, n, \gamma_{\text{sat}}$) across 13 soil classes (`sand` to `clay` + `default_generic`). |
| **`__init__.py`** | 1.6 KB | Package Init | Exposes public civil engineering engines and structured result dataclasses. |

---

## 3. Mathematical Formulations & Geotechnical Physics

### 3.1 Unsaturated Matric Suction & Fredlund Shear Strength (`soil_mechanics_core.py`)

Using effective saturation $S_e = \frac{\theta - \theta_r}{\theta_s - \theta_r}$ clipped away from singularities, matric suction $\psi$ (kPa) is inverted analytically via the van Genuchten (1980) water retention curve:

$$\psi(S_e) = \frac{1}{\alpha} \left( S_e^{-1/m} - 1 \right)^{1/n} \cdot 0.0980665 \quad [\text{kPa}], \quad m = 1 - \frac{1}{n}$$

Fredlund extended Mohr-Coulomb apparent cohesion and Bishop effective shear strength are then evaluated as:

$$c_{\text{app}} = c' + \psi \cdot \tan(\phi^b), \qquad \sigma' = \sigma + S_e \cdot \psi, \qquad \tau_f = c_{\text{app}} + \sigma' \tan(\phi')$$

### 3.2 Meyerhof-Hansen Bearing Capacity (`ground_stability_engine.py`)

For continuous or rectangular footings of width $B$ and length $L$:

$$N_q = e^{\pi \tan\phi'} \tan^2\left(45^\circ + \frac{\phi'}{2}\right), \quad N_c = \frac{N_q - 1}{\tan\phi'}, \quad N_\gamma = (N_q - 1)\tan(1.4\phi')$$

$$q_{\text{ult}} = c_{\text{app}} N_c s_c d_c + q N_q s_q d_q + 0.5 \gamma_{\text{sat}} B N_\gamma s_\gamma d_\gamma, \qquad q_{\text{allow}} = \frac{q_{\text{ult}}}{FS}$$

### 3.3 Infinite Slope Planar Factor of Safety (`slope_stability_engine.py`)

For terrain slope angle $\beta$ and failure plane depth $z$:

$$FS = \frac{c' + (\gamma_{\text{sat}} z \cos^2\beta - u_w)\tan(\phi')}{\gamma_{\text{sat}} z \sin(\beta)\cos(\beta)}, \quad u_w = -\psi$$

With hazard thresholds: `STABLE` ($FS \ge 1.5$), `MARGINALLY_STABLE` ($1.0 \le FS < 1.5$), and `LANDSLIDE_HAZARD` ($FS < 1.0$).

### 3.4 Topographic Wetness Index & Liquefaction Index (`drainage_intelligence.py`, `scenario_simulator.py`)

$$\text{TWI} = \text{clip}\left(\ln\left(\frac{a}{\tan\beta}\right), \; 2.0, \; 20.0\right)$$

Under flooded inundation ($\psi \to 0$, submerged unit weight $\gamma' = \gamma_{\text{sat}} - \gamma_w$), Liquefaction Susceptibility Index ($	ext{LSI}$) flags quicksand hazards wherever $\text{LSI} \ge 0.70$.

---

## 4. Brutally Honest Engineering Disclosures ("Ek Ek Dhappa")

In strict accordance with aerospace transparent disclosure norms, the following code quirks, physical approximations, and engineering gaps in `4_domain_translators/civil/` are explicitly disclosed:

### Dhappa 1: Field Assignment Quirk in `scenario_simulator.py` (Line 154)
* **Code Reality:** Inside `simulate_heavy_rainfall()`, the returned `HeavyRainfallSimulationResult` assigns `matric_suction_simulated_kpa = post_bearing.apparent_cohesion_kpa.astype(np.float32)`.
* **Impact:** That field actually stores *apparent cohesion* ($c_{\text{app}}$) post-rainfall rather than raw matric suction ($\psi$). Downstream consumers inspecting `matric_suction_simulated_kpa` must account for this internal mapping.

### Dhappa 2: 1D Infinite Planar Slide vs Circular Rotational Slip
* **Compromise:** `SlopeStabilityEngine` relies on a 1D infinite planar translational slide equation.
* **Limitation:** In deep cohesive clay embankments or cut slopes, real failures frequently occur along circular rotational arcs (Bishop Simplified / Spencer method of slices) rather than shallow infinite planes.

### Dhappa 3: Flat-Terrain Slope Singularity Clamp ($\beta < 0.5^\circ$)
* **Compromise:** In `FS = ... / (gamma * z * sin(beta) * cos(beta))`, as $\beta \to 0$, the denominator approaches zero and $FS \to \infty$.
* **Workaround:** `slope_stability_engine.py` detects `slope_deg < 0.5` and forcibly clamps output to `MAX_FS_CLAMP = 10.0`.

### Dhappa 4: van Genuchten Asymptotic Clipping at Boundaries
* **Compromise:** The analytical van Genuchten curve diverges to $\psi \to \infty$ as $S_e \to 0$.
* **Safeguard:** `soil_mechanics_core.py` clamps effective saturation away from $0$ and $1$ and imposes a hard ceiling of `MAX_SUCTION_KPA = 10,000.0 kPa` (10 MPa).

### Dhappa 5: Zero In-Situ Borehole, Water Table, or Seismic PGA Coupling
* **Engineering Reality:** All bearing capacity, slope safety, and liquefaction metrics extrapolate from spaceborne surface moisture ($0-10\text{ cm}$) and static USDA soil presets (`geotechnical_taxonomy.json`).
* **Mandate:** Outputs are situational awareness intelligence only; structural foundation engineering requires physical SPT/CPT rotary boreholes and triaxial laboratory shear testing.

---

## 5. Traceable Functional Requirements

| Requirement ID | Verification Type | Target Module | Technical Specification |
|:---|:---:|:---:|:---|
| **`REQ-CIV-01`** | Physics Test | `soil_mechanics_core.py` | Matric suction shall remain non-negative and bounded within $[0.0, 10000.0]\text{ kPa}$ across all valid saturations. |
| **`REQ-CIV-02`** | Invariant Test | `ground_stability_engine.py` | `assert_invariants` shall enforce $q_{\text{ult}} > 0$, $q_{\text{allow}} > 0$, and exact identity $q_{\text{ult}} / q_{\text{allow}} = FS$. |
| **`REQ-CIV-03`** | Boundary Test | `slope_stability_engine.py` | Factor of Safety shall remain finite and strictly bounded within $[0.10, 10.0]$, safely clamping flat slopes ($\beta < 0.5^\circ$). |
| **`REQ-CIV-04`** | Terrain Test | `drainage_intelligence.py` | Topographic Wetness Index shall be clamped to $[2.0, 20.0]$ without log-of-zero or division-by-zero errors. |
| **`REQ-CIV-05`** | Simulation Test | `scenario_simulator.py` | Heavy rainfall simulation shall monotonically decrease bearing capacity ($\Delta q_{\text{allow}} \ge 0$) as saturation rises. |
| **`REQ-CIV-06`** | Mobility Test | `scenario_simulator.py` | `simulate_vehicle_mobility` shall classify terrain into Passable, Marginal Risk, or Quagmire masks using vehicle contact pressures. |
| **`REQ-CIV-07`** | Risk Audit | `conformal_geotechnical_risk.py`| `dispatch_geotechnical_risk` shall propagate $\pm 2\sigma$ uncertainty into conservative lower-bound bearing capacities. |
| **`REQ-CIV-08`** | Export Test | `civil_geotiff_exporter.py` | Exporter shall output 4-band geotechnical GeoTIFF stacks with SHA-256 digests and Windows lock safety. |

---

## 6. Safety, Verification & Operational Guidelines

1. **Aerospace Software Integrity Norms**: Every geotechnical solver executes `assert_invariants()` post-computation, blocking NaN, Inf, or physically inverted results.
2. **Mandatory Engineering Disclaimer**: All outputs carry explicit engineering boundaries stating that spaceborne surface estimations do not substitute certified geotechnical borehole investigations.
