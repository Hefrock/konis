# ADR 0006: Curated Xact lead table, and curated tables as CSV

Status: accepted (25 Nov 2026).

## Curated format
Curated tables are committed as CSV in `data/curated/`, not Parquet. They are rebuilt every
run; git stores text revisions as small deltas but re-stores a changed Parquet file almost
whole. Parquet can be produced locally from the CSV when needed. `konis parse --check` (run in
CI) rebuilds twice and fails if the results differ.

## `xact_lead.csv`
Source: EPA Region 7 layer `IAAAP_Xact_Data_Public_Viewer` (captures in
`data/raw/epa_xact_metals/`). One row per published reading per revision.

- `analyte` = `Pb`, from EPA's own viewer field label "Lead Concentration (µg/m3)". The layer
  itself names no analyte.
- `observed_at_utc` is `Mon_Date_Time` read as UTC epoch milliseconds. Check: no reading is
  later than the capture that first contained it (`observed_after_fetch` is false for all rows
  at first build). `observed_at_central` is the same instant in America/Chicago.
- `value_reported` is exactly as published. `reported_zero` marks a published 0; it is not
  read as "no lead" because EPA has published no detection limit (K6; request drafted in
  `docs/requests/`).
- `viewer_display_1dp` is what EPA's map showed: the viewer formats this field to one decimal
  place, so every reading so far (maximum 0.0102 µg/m³) displayed as "0.0".
- Revisions become new rows (`revision`, `superseded_at_utc`); rows missing from a later full
  snapshot get `removed_at_utc`. Each capture is judged by what was known when it was fetched.
- Provenance: `source_id`, `tier`, `raw_sha256`, `raw_file`, `first_seen_fetched_at_utc`,
  `parser_version`.

Reference context only (no averaging-time match is implied): EPA's viewer cites the DOE
PAC-1 short-term screening level for lead, 32 µg/m³. The lead NAAQS (0.15 µg/m³) is a rolling
3-month average and cannot be compared with individual readings.
