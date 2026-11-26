# ADR 0007: Curated AirNow hourly table

Status: accepted (26 Nov 2026).

`data/curated/airnow_hourly.csv`, rebuilt from `data/raw/airnow_hourly/` by `konis parse`.
One row per site x parameter x valid hour x revision.

- Time: each row's date/time equals the UTC hour in the file name, so it is read as UTC.
  Rows that disagree are kept with `time_mismatch` = true (none at first build).
- Staged posting: AirNow posts an hourly file in parts (the 22:00 UTC file on 25 Nov was 82 KB
  at 23:07 and 727 KB at 01:06). A row missing from an early version is "not yet published",
  never "removed". Only a changed value is a revision (`revision`, `superseded_at_utc`).
- Capture check (K2): a run whose hourly files are full size (>300 KB nationally) but contain no
  study-box rows fails as `empty`, since that means a format or site-id change.
- Values are preliminary and unvalidated, kept as published; negative values are flagged.
- `distance_km` and `bearing_from_iaaap_deg` (great circle, `konis.geo`) from IAAAP use the
  latest site file. They are geometry only; exposure strata are not assigned here (K8).

## Network limits (first build, 26 Nov)
Reporting PM monitors in the box: 9 PM2.5 and 1 PM10, all in Iowa and Illinois. The nearest is
65 km from IAAAP (Lake Sugema, bearing 261°). None lies to the southwest, the direction the Army
forecast drift into Missouri, and no Missouri monitor reports into the box. A plume-versus-control
comparison on this network alone would have no monitor where the plume was forecast to go.
