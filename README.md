# `konis` (*κόνις*)

**Multi-modal environmental telemetry and epidemiological surveillance for the November 2026 Iowa Army Ammunition Plant (IAAAP) detonation.**

Named after the Ancient Greek word for *fine dust, powder, or ash*, `konis` tracks airborne particulate proxies, wind trajectories, and seismic waveforms across Southeast Iowa, Northern Missouri, and Western Illinois following the November 25, 2026 controlled detonation of degraded lead azide ($\text{Pb(N}_3)_2$) in Middletown, Iowa.

> **Unofficial independent project.** Not public health or medical guidance, and not affiliated
> with or endorsed by EPA, the U.S. Army, or any state agency. For official information see
> [EPA's response site](https://response.epa.gov/site/site_profile.aspx?site_id=17211),
> [Iowa HSEMD](https://homelandsecurity.iowa.gov/iowa-army-munitions-disposition-resources),
> [Iowa HHS](https://hhs.iowa.gov/health-prevention/environmental-health/lead-exposure-surveillance)
> and [Illinois EPA](https://epa.illinois.gov/iowa-plant-updates.html).

## Status

**Stage 0 (capture) is running.** Every 30 minutes the pipeline archives official pages, EPA's
public Xact metals layer, AirNow regulatory monitors in the study box, and METAR/ASOS
weather, saving each change exactly as received with a SHA-256 hash. Parsing, modelling and
the dashboard described below are planned (Stages 1-3) and not yet built. See
[`docs/PROGRESS.md`](docs/PROGRESS.md), [`docs/adr/`](docs/adr/) and
[`docs/lessons.md`](docs/lessons.md).

---

## Why This Exists

When large-scale munitions or hazardous materials are neutralized in place—even behind sand berms, ballistic gels, and water walls—initial "all clear" air readings only tell part of the story. From an environmental epidemiology perspective, two questions matter over the days that follow:

1. **Spatial Exposure:** Did particulate levels rise in the downwind plume cone compared to upwind control communities?
2. **Secondary Resuspension:** Once water-misted soil dries out and regional winds pick up, does settled dust re-enter the air?

`konis` automates data collection from public environmental and geophysical networks, pairs them with epidemiological cohort comparisons, and explicitly audits where low-cost sensors fall short.

---

## What It Tracks

* **Air Quality Proxies (`AirNow` & `PurpleAir`):** Bounding-box $\text{PM}_{2.5}$ and $\text{PM}_{10}$ concentrations across a 150-mile radius around Middletown, IA (`40.7906° N, 91.2447° W`).
* **Meteorology (`AviationWeather METAR` & `NOAA HRRR`):** Real-time wind vectors, gusts, humidity, and soil moisture from nearby Burlington (`KBRL`) and open NOAA AWS buckets.
* **Blast Verification (`EarthScope` & `Raspberry Shake`):** Regional seismic and infrasound waveforms confirming exact detonation timestamps and ground/air wave propagation.
* **Official Advisories (`EPA Region 7`, `U.S. Army`, & State Portals):** Automated snapshots of official dispersion contours and lab sampling updates so revisions are preserved in Git history.

---

## Key Analytical Features

* **Upwind vs. Downwind Cohort Analysis:** Dynamically classifies sensors by active wind bearing into a *Primary Plume Cone* ($\pm 25^\circ$) and an *Unexposed Control Group* ($> 90^\circ$), using Difference-in-Differences ($\Delta\text{DiD}$) against a 7-day baseline to separate plume anomalies from normal regional weather.
* **72-Hour Resuspension Risk Index:** Tracks post-detonation drying conditions (low humidity, zero precipitation, rising wind gusts) that could re-suspend settled surface dust.
* **Failure Mode & Blind-Spot Auditor:** Flags optical sensor artifacts—such as water-wall misting humidity spikes, coarse particle settling below $\text{PM}_{2.5}$ size cuts, and sensor dropouts—rather than treating raw numbers at face value.

---

## Important Scientific Caveats

* **Optical Sensors Do Not Measure Lead:** Consumer laser particle counters (`PurpleAir`) and standard regulatory $\text{PM}_{2.5}$ monitors measure total aerosol mass—including fog, misting droplets, and agricultural dust. They **cannot** identify elemental lead ($\text{Pb}$). Confirmed lead concentrations require laboratory filter assays (XRF/ICP-MS) from the EPA and state agencies.
* **Aggregated Public Data:** In compliance with PurpleAir's Terms of Service, raw individual sensor dumps are not committed to this repository; stored datasets contain spatially aggregated cohort metrics and Z-scores.

---

## Quick Start

```bash
# 1. Clone and install in editable mode
git clone [https://github.com/Hefrock/konis.git](https://github.com/Hefrock/konis.git)
cd konis
pip install -e .

# 2. Set API keys for local runs (optional for METAR/FDSN)
export AIRNOW_API_KEY="your_airnow_key"
export PURPLEAIR_API_KEY="your_purpleair_key"

# 3. Launch the interactive dashboard
streamlit run src/konis/app.py
