# ADR 0001: What konis adopts from ilara

Status: proposed (25 Nov 2026), awaiting owner decision on items marked "decide".

ilara archives disease-report dashboards; konis archives sensor telemetry and agency pages.
Practices are adopted where the failure mode is about *collection*, adapted where it depends
on the data type, and not adopted where it is specific to case reporting.

| ilara practice | konis | Why |
|---|---|---|
| Raw saved first, hashed, immutable (I1) | adopt (K1) | Agency pages and the EPA Xact layer show only current state |
| Content checks; "success" that held nothing is failure (lesson 2) | adopt (K2) | Same risk: moved pages, emptied ArcGIS layers |
| Backup trigger for late/missed cron (lessons 1, 6) | adopt (watchdog.yml) | Same scheduler |
| Alerts as GitHub issues, auto-close on recovery | adopt | Owner requested |
| Append-only guard, bot paths, size guard | adopt (`konis guard`) | Same repo-growth risk |
| Provenance on every row (I3) | adapt (K4) | Add observed_at vs fetched_at; sensor time zones vary |
| Source tiers (I4) | adapt (K5) | No "T3-derived" case counts; news used only to find sources |
| No fabrication (I5) | adopt (K6) | Plus: non-detect is not zero |
| Pre-registration; rules change only going forward (lesson 12) | adopt (K8) | DiD and cone widths are easy to tune after the fact |
| Self-inconsistent snapshot (lesson 4) | adapt | Check ArcGIS count vs paged features; check layer schema |
| Re-judge captures by what was known then (lesson 5) | adopt in Stage 1 | AirNow data are preliminary and later revised |
| Report-date / right truncation (lesson 8) | adapt | Analogue: lab results lag 24-72 h; AirNow revisions |
| Downward count revisions (lesson 9) | adapt | Analogue: revised or withdrawn readings kept as new rows |
| Forecast withheld until validated (G4) | decide | Applies to the resuspension index, which is a heuristic |
| SEIR model, seeding, ABC calibration (lessons 10-11) | not adopted | No transmission process here |
| Case-level / line-list safeguards | not adopted | No case data; replaced by PurpleAir ToS rule (K9) |
| uv + polars + duckdb + pydantic stack | decide | Stage 0 uses pip + requests only, to start capture today |
