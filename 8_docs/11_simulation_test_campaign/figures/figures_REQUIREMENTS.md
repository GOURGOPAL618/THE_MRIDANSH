# Subsystem 11: Simulation Test Campaign — Figures Specification (`11_simulation_test_campaign/figures/`)
## Central Unified Engine: AETHER-MRID1607X
### Mission Facility: JCC CAMPUS 2 (RS-SDA DIVISION)
### Author & Lead Systems Architect: Gourgopal Mohapatra
### Release Status: TRL-7 OPERATIONAL FLIGHT READINESS

---

## 1. Executive Overview & Visual Evidence Mandate

The `11_simulation_test_campaign/figures/` subsystem archives the publication-grade scientific visualizations, probability density distributions, state-space uncertainty ellipses, and hydrodynamic trajectory envelopes generated from the 1,000-trial Planetary Monte Carlo Stress Campaign (`PMC-1000-AETHER-MRID1607X`).

These artifacts serve as the empirical visual evidence for peer-reviewed journal publication in IEEE TGRS and provide visual proofs for the Master Monograph.

---

## 2. Multi-Figure Scientific Specification

### 2.1 Figure 1: EnKF Covariance Stability & Radiometric Noise Resilience
* **Panel A (State-Space Confidence Ellipsoids):** Evaluates Ensemble Kalman Filter covariance matrices across 250 trials in Quadrant 3. Under heavy synthetic Sentinel-1 SAR speckle injection ($\Delta \sigma^0 \in [-4.5, +4.5]\,\text{dB}$) and $50\%$ optical cloud blackout, state uncertainty is tightly bounded within the $95\%$ confidence ellipse.
* **Panel B (Condition Number Empirical CDF):**
  $$\kappa(\mathbf{P}) = \frac{\lambda_{\max}(\mathbf{P})}{\lambda_{\min}(\mathbf{P})}$$
  Maximum condition number $\kappa_{\max} = 1709.03$, maintaining an operating safety margin of **$585.1\times$** below the numerical matrix collapse threshold ($\kappa = 10^6$). Minimum eigenvalue $\lambda_{\min} = 9.7 \times 10^{-5} \gg 10^{-9}$.

### 2.2 Figure 2: Planetary Vadose Hydrodynamic Trajectories
* **Panel A (Hyper-Arid Drought Desiccation — Q1):** 14-day desiccation envelope ($ET_0 = 8-14\,\text{mm/d}$, $P = 0\,\text{mm/d}$). Shows strictly monotonic moisture decay ($\frac{\partial \theta}{\partial t} \le 0$), asymptoting safely at the residual moisture floor $\theta_{\text{res}} = 0.120\,\text{m}^3/\text{m}^3$ with zero Richards mass balance drift.
* **Panel B (Monsoon Deluge Inundation — Q2):** 7-day cyclonic cloudburst envelope ($P = 50-150\,\text{mm/d}$). Illustrates rapid pore filling with $80\%$ of trials reaching the exact physical porosity ceiling $\theta_{\text{sat}} = 0.450\,\text{m}^3/\text{m}^3$, with zero unphysical volume overflow.

### 2.3 Figure 3: Cross-Domain Terramechanics & Disaster Envelopes
* **Panel A (Eurocode 7 Slope Stability):** Factor of safety ($FoS$) as a function of soil saturation ratio ($S_r$). Accurately isolates 6 planar shear slip hazards ($FoS \in [0.87, 0.98] < 1.0$) on steep slopes ($\beta \ge 35^\circ$).
* **Panel B (Bekker Tractor Rutting & Sinkage):** Semi-empirical tyre sinkage depth ($z_{\text{rut}}$) under $45\,\text{kN}$ tractor axle loads on saturated alluvial clay. $100\%$ of trials reach the chassis grounding limit ($35.0\,\text{cm}$), accurately modeling vehicle immobilization during disaster-grade monsoon soil liquefaction.

---

## 3. "Ek Ek Dhappa" — Brutally Honest Visual Artifact Disclosures

1. **2D Ellipsoid State Projection Simplification:**
   - *Dhappa:* Figure 1 projects the multi-state EnKF covariance matrix onto a 2D plane (surface moisture $\theta_{\text{skin}}$ vs root-zone $\theta_{\text{root}}$).
   - *Compromise:* Higher-order cross-covariances with vadose suction head $h$ and hydraulic conductivity $K$ are suppressed in the 2D projection for visual clarity.
2. **Matplotlib Non-Interactive Agg Backend:**
   - *Dhappa:* Figures are generated headlessly using the `Agg` raster backend.
   - *Compromise:* Interactive zooming or 3D rotation of the point clouds requires opening the underlying raw trajectory `.npy` arrays directly in Python.
