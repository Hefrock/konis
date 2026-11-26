# Progress

## Stage 0: capture (25 Nov 2026)
Status: running on main (:07/:37, watchdog :52). First GitHub run 23:07 UTC: 17/17 ok.

## Stage 1: curated tables (started 25 Nov 2026)
Done: uv + polars with uv.lock; `konis parse` builds `data/curated/xact_lead.csv` (ADR 0006)
and `data/curated/ingestion_health.csv`; deterministic rebuild checked in CI; runs after each
capture. Illinois EPA PDFs added as sources.
Evidence: 36 offline tests; 326 Xact rows from 4 stations at first build.
Open: detonation time (BLOCKERS); EPA detection limit (draft request).
Done 26 Nov: AirNow curated table (ADR 0007), great-circle geometry with tests; capture check
for full-size files with no study-box rows.
Done 26 Nov: linked-document harvester with release-asset storage for large files (ADR 0008);
ADR 0009 pre-registered Xact x wind analysis drafted (PROPOSED).
Next: METAR/ASOS parsers, 7-day baseline, then HRRR and seismic.
