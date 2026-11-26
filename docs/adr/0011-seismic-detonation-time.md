# ADR 0011: Detonation time from seismic and infrasound data (preliminary)

Status: accepted as a method; result PRELIMINARY (26 Nov 2026). Superseded for analysis by
any T1 agency statement of the exact time, if one is published and agrees.

## Question
The project brief gives 09:00 CST (15:00 UTC); some same-day news said "about 9 a.m. ET"
(14:00 UTC). The answer decides which Xact readings are pre- or post-event (ADR 0009).

## Data
EarthScope FDSN (`service.earthscope.org`; IRIS now redirects there), station N4.N41A,
36.7 km east of the QAPP ECM midpoint (UTM 15N 646000 E 4519000 N = 40.80903 N, 91.26903 W):
HHZ (seismic, 100 Hz) and BDF (infrasound, 40 Hz), 13:50-15:20 UTC 25 Nov. Stored raw in
`data/raw/seismic_fdsn/`. The Raspberry Shake FDSN service returned HTTP 502/504 on 26 Nov.

## Method (`konis seismic analyze`)
Band-pass (HHZ 1-15 Hz, BDF 1-10 Hz), classic STA/LTA (1 s / 30 s), onsets at ratio >= 4.
A blast should produce a seismic onset (~6 km/s, ~6 s travel) followed by an infrasound onset
at the speed of sound (0.30-0.36 km/s window, ~100-120 s later). Strong seismic onsets
(ratio >= 10) are paired with infrasound onsets in that window.

## Result
- 13:55-14:10 UTC (09:00 ET): **no seismic onsets** at any ratio >= 4.
- 14:55-15:10 UTC (09:00 CST): one strong seismic onset that pairs: **15:00:38.5 UTC**
  (STA/LTA 16) -> implied origin **15:00:32 UTC**; infrasound onset 15:02:22.7 UTC, implied
  sound speed **0.333 km/s**. KBRL air temperature at 14:53 UTC was 0.6 °C, for which the
  speed of sound is 0.332 km/s; the cross-path wind (from 50° at 4.1 m/s) changes that by
  about -0.003 km/s.
- Stations 139-203 km away (L40A, N38B, HDIL, L42A, P43A, P40B, SCIA) show no consistent
  arrivals: a buried, mitigated detonation of this size is below the noise at those ranges.

## Interpretation and limits
The data support a detonation at about **15:00:32 UTC (09:00:32 CST)** and give no support to
14:00 UTC. This rests on one station; the background has many onsets (198 in 90 minutes,
mostly wind and cultural noise), and the seismic and infrasound picks are automatic. It is
evidence, not a location. Use 15:00:32 UTC ± 10 s as the working T0 until an agency time is
published; record the source of T0 with any result.
