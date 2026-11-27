# Progress

## Stage 0: capture (25 Nov 2026)
Status: running on main (:07/:37, watchdog :52). First GitHub run 23:07 UTC: 17/17 ok.

## Stage 1: curated tables (started 25 Nov 2026)
Done: uv + polars with uv.lock; `konis parse` builds `data/curated/xact_lead.csv` (ADR 0006)
and `data/curated/ingestion_health.csv`; deterministic rebuild checked in CI; runs after each
capture. Illinois EPA PDFs added as sources.
Evidence: 55 offline tests; 326 Xact rows from 4 stations at first build.
Open: detonation time (BLOCKERS); EPA detection limit (draft request).
Done 26 Nov: AirNow curated table (ADR 0007), great-circle geometry with tests; capture check
for full-size files with no study-box rows.
Done 26 Nov: linked-document harvester with release-asset storage for large files (ADR 0008);
ADR 0009 pre-registered Xact x wind analysis drafted (PROPOSED).
Done 26 Nov: weather_obs curated table from METAR + IEM ASOS (ADR 0010).
Done 26 Nov: seismic/infrasound detonation-time check (ADR 0011): ~15:00:32 UTC, preliminary.
Done 26 Nov: ADR 0009 accepted and run; primary estimate undefined (no non-downwind station),
descriptive counts in docs/results/xact-wind-c3bca34.md.
ADR 0012 accepted 26 Nov 13:20Z (Part A exploratory; Part B prospective, data after 13:20Z).
Done 26 Nov: ADR 0012 Part A report (docs/results/transect-partA-da11702.md) and Part B
episode detector in ingest-live (no episode yet; 25 Nov was wet at KBRL).
Next: owner sends EPA request; PurpleAir key; dashboard, 7-day baseline, then HRRR and seismic.

Done 27 Nov: Missouri and Army ASC sources (ADR 0013); detonation time confirmed by the Army.
OpenAQ checked: no coverage within 50 km; low-cost sensors out of scope.
Done 27 Nov: two-in-a-row alerts (ADR 0014); Army 24 Nov model figures transcribed to data/seed/.

## Planned improvements (agreed 27 Nov 2026, in order)
1. DONE 27 Nov (repo-pincer audit: 6/22 claims confirmed; 4 High findings fixed). README rewrite: plain-language, human-readable account of what konis collects, what it
   found and its limits; drop handoff features that were not built (plume DiD on PM monitors,
   PurpleAir, resuspension gauge). Technical detail moves to CLAUDE.md / docs/, not the README.
   Fact-check every claim against docs/adr, docs/sources.md and the data.
2. DONE 27 Nov (ADR 0015; Zenodo link is an owner action). Tagged data releases (weekly), optionally archived to Zenodo for a DOI (owner links Zenodo).
3. Reduce backup-trigger cost once GitHub's scheduler is reliable (owner: disable/re-enable
   ingest-live and watchdog in Actions), then remove or slow the hourly backup.
4. DONE 27 Nov (ADR 0016; owner enables Pages). Simple public status page (GitHub Pages) instead of the full Streamlit dashboard.
Not planned: more sensor sources or analyses (diminishing returns; EPA lab results are the
key pending evidence, watched by the harvester).
Licenses added 27 Nov: MIT for code; CC BY 4.0 for konis-created data/docs; third-party captures keep publishers' terms.
