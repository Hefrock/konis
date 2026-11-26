# Result: Xact lead readings vs. KBRL wind (ADR 0009, primary analysis)

- Analysis version `xact_wind/1`; data cut: git commit `c3bca34`.
- T0 = 2026-11-25T15:00:32+00:00 (seismic/infrasound estimate, ADR 0011 (15:00:32 UTC +/- 10 s)).
- Xact readings (current rows): 335, 2026-11-25T13:00:00+00:00 to 2026-11-26T02:40:00+00:00.
- Wind: KBRL from `iem_asos`, 2026-11-23T00:53:00+00:00 to 2026-11-25T23:53:00+00:00.

## Station geometry (from the QAPP ECM midpoint)

| station | bearing | distance |
|---|---|---|
| AS01 | 232.0° | 5.8 km |
| AS02 | 233.8° | 18.9 km |
| AS03 | 234.1° | 30.7 km |
| AS04 | 235.4° | 44.0 km |

## Primary estimate

Event window T0 to T0 + 8 h, cone ±45°: downwind 17/240 (7.1%).

**The primary estimate is not defined.** Every matched reading in the event window falls in the same group, so there is no comparison group. All four stations lie on a line south-west of the site, and the wind blew toward that line throughout.

## Pre-specified descriptive counts

Outcome: reading reported as non-zero (not "detected": EPA has published no detection limit for these monitors).

| analysis | event window | pre-event (same day, before T0) |
|---|---|---|
| primary | downwind 17/240 (7.1%) | downwind 3/85 (3.5%) |
| cone ±30° | downwind 17/240 (7.1%) | downwind 3/85 (3.5%) |
| cone ±60° | downwind 17/240 (7.1%) | downwind 3/85 (3.5%) |
| window 4 h | downwind 13/193 (6.7%) | downwind 3/85 (3.5%) |
| window 24 h | downwind 17/244 (7.0%); unmatched 0/6 (0.0%) | downwind 3/85 (3.5%) |

By station, primary window:

| station | event window |
|---|---|
| AS01 | downwind 2/60 (3.3%) |
| AS02 | downwind 2/61 (3.3%) |
| AS03 | downwind 4/60 (6.7%) |
| AS04 | downwind 9/59 (15.3%) |

## What this does and does not show

- The design question (downwind vs. not downwind) cannot be answered with these monitors on this day: there were no readings outside the plume direction.
- Counts are descriptive. Four stations and one event cannot show that lead did or did not leave the site, and a non-zero reading is not a confirmed detection.
- Individual readings must not be compared with the lead NAAQS (a 3-month average). For context only, the EPA viewer cites the DOE PAC-1 short-term level, 32 µg/m³.
- Any further analysis (for example, by distance along the transect) is a new question and needs its own pre-registration before it is run (K8).
