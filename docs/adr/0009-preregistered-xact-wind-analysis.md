# ADR 0009: Pre-registered primary analysis: Xact lead readings vs. wind direction

Status: ACCEPTED by the owner 26 Nov 2026, before the analysis was run. Changes after
acceptance apply going forward and are recorded here.

Outcome (26 Nov 2026, data cut c3bca34): run as specified, `konis analyze xact-wind`; see
`docs/results/xact-wind-c3bca34.md`. The primary estimate is **not defined**: all four Xact
stations lie 232-235° from the origin, the wind blew toward 220-230° throughout the event
window, so every matched reading was "downwind" and there was no comparison group. Only the
pre-specified descriptive counts are reported. No substitute comparison was run (K8).

## Why this, not the PM plume comparison
Regulatory PM monitors cannot measure lead (K10) and none lies in the forecast plume direction
(ADR 0007). The EPA Xact monitors measure airborne lead directly at four stations near IAAAP.
The question they can answer is narrow but real.

## Primary question
During the event window, were Xact lead readings above zero more frequent when the station was
downwind of the detonation site than when it was not?

## Definitions (fixed in advance)
- **Data:** `data/curated/xact_lead.csv`, current rows only (not superseded, not removed), as of
  a stated data cut (git commit) recorded with the result.
- **Origin:** the midpoint between the two ECMs as given in the QAPP (UTM 646,000 E,
  4,519,000 N, zone 15N), converted to latitude/longitude once and stored in `config.py`.
  (IAAAP's nominal coordinate in the project brief is not the detonation point.)
- **Detonation time T0:** from a T1 source (Army or EPA) if published; otherwise the
  seismic/infrasound estimate of ADR 0011 (15:00:32 UTC ± 10 s). The source of T0 is stated
  with every result.
- **Event window:** T0 to T0 + 8 h. Pre-event window: readings before T0 on the same day.
- **Wind:** KBRL ASOS observations (IEM archive; the same station EPA used in QAPP Worksheet 17).
  Each Xact reading is matched to the latest KBRL observation at or before its timestamp,
  within 60 minutes; otherwise it is unmatched and excluded (reported, not imputed).
- **Downwind:** the bearing from the origin to the station is within ±45° of the direction the
  wind blows toward (meteorological direction + 180°), using `konis.geo.angular_difference`.
  Calm (< 1 m/s) or variable winds are a separate "calm/variable" group.
- **Outcome:** reading above zero (`reported_zero` is false). Because EPA has not published a
  detection limit, "above zero" means "reported as non-zero", not "detected"; results are
  stated in those words.

## Analysis
1. Counts and proportions of non-zero readings by group (downwind, not downwind,
   calm/variable) and by station, for the event window and the pre-event window.
2. Primary estimate: difference in the proportion non-zero, downwind minus not downwind, in the
   event window, with a 95% confidence interval from a station-cluster bootstrap (resampling
   stations; 4 clusters, so the interval is reported as approximate).
3. No hypothesis test is the primary result. With four stations and one event, the result is
   descriptive; it cannot show that lead did or did not leave the site.

## Sensitivity analyses (pre-specified)
- Cone width ±30° and ±60°.
- Wind from the EPA on-site weather station if EPA publishes it, instead of KBRL.
- Event window T0 to T0 + 4 h and T0 to T0 + 24 h.
- Restricting to readings above a detection limit once EPA publishes one (replaces the primary
  outcome definition, going forward).

## Reporting rules
- Report every analysis above, including null or contrary results.
- State the network limits: four stations, all near the site; no measurement in the forecast
  far-field (ADR 0007).
- Do not compare individual readings with the lead NAAQS (3-month average). Context only: the
  DOE PAC-1 short-term level cited on EPA's viewer, 32 µg/m³.
