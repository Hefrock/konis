# ADR 0012: Xact readings by distance along the south-west transect

Status: PROPOSED (draft 26 Nov 2026), for owner review. Nothing in this ADR has been run.

## Why, and what has already been seen
ADR 0009's downwind comparison was undefined: the four EPA Xact stations lie on one line
south-west of the origin (AS01 5.8 km, AS02 18.9 km, AS03 30.7 km, AS04 44.0 km; bearings
232-235°), the direction the wind blew on 25 Nov. The geometry supports a different question:
how do readings change with distance along that line?

**This question was chosen after seeing the data.** ADR 0009's report already shows non-zero
readings by station in the event window (AS01 2/60, AS02 2/61, AS03 4/60, AS04 9/59). Any
analysis of 25 Nov by distance is therefore **exploratory** and is labelled so wherever it
appears. A confirmatory analysis can only use data collected after this ADR is accepted.

## Part A: exploratory description of 25 Nov (no inference)
- Data: `data/curated/xact_lead.csv`, current rows; T0 and origin as in ADR 0009; the same data
  cut as `docs/results/xact-wind-c3bca34.md` plus any later EPA revisions, stated with the result.
- Per station: proportion non-zero before T0 (same UTC day) and in T0 to T0 + 8 h; the change
  (event minus pre-event); and the maximum reported value in each window.
- Shown as a table and a plot against distance. No slope, test or interval: with four stations,
  one event and a pattern already seen, any such number would overstate what is known.
- Reported together with the limits: no detection limit published; "non-zero" is not
  "detected"; the pre-event baseline is 1.5-2 hours at each station.

## Part B: confirmatory, prospective (resuspension episodes)
Applies only to Xact data observed after this ADR's acceptance date, and only if EPA keeps
publishing Xact results (the layer's latest reading at drafting was 02:40 UTC 26 Nov).

- **Episode:** a period meeting ADR 0003's resuspension conditions, measured at KBRL from
  `iem_asos`: at least 3 consecutive UTC days with no measurable precipitation, then any hour
  with a gust > 6.7 m/s. The episode runs from the first such hour for 12 h.
- **Baseline:** for each station, all its readings in the 7 days before the episode that fall
  outside any episode.
- **Outcome:** per station, proportion non-zero in the episode minus proportion non-zero in its
  baseline (once EPA publishes a detection limit, "above the detection limit" replaces
  "non-zero", going forward).
- **Hypothesis (direction fixed in advance):** if deposited lead is being resuspended near the
  site, the change is largest at the station nearest the origin (AS01) and does not increase
  with distance.
- **Estimate:** the change at each station, and the Spearman correlation between change and
  distance across stations, reported with all four values. With four stations, a correlation
  can only be -1, -0.8, ... 1; it is descriptive, and no p-value is the primary result.
- **Wind check:** each episode is also classified by KBRL wind toward the transect (±45° of
  233°) or not; results are reported for both, not pooled.
- Every episode that meets the definition is reported, including ones with no change.

## Not covered
- Regulatory PM monitors (ADR 0007) and PurpleAir: optical PM is not lead (K10).
- Soil, wipe and filter results: analysed when EPA publishes them, under their own ADR.
