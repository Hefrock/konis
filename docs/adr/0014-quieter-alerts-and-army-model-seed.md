# ADR 0014: Two-in-a-row alerts; Army model figures as a seed file

Status: accepted (27 Nov 2026).

## Alerts
Problem: army.mil intermittently returned 404 for the Army's first advisory (article 297039),
so the one-failure-opens / one-success-closes rule opened and closed three issues in 24 h
(#7, #9, #11) and commented on every run. Alerts that fire on noise stop being read.

Decision (`konis.alerts.decide`):
- open an issue only when a source fails in this run **and** in its previous run;
- while open, add nothing per run;
- close only after **two** consecutive successful runs.
Every failure is still logged in `data/capture_log/` and counted in
`data/curated/ingestion_health.csv`; only the GitHub notification changes. The `capture stale`
watchdog issue and the `resuspension-episode` issues are unchanged.

## Army deposition model
The Army's 24 Nov public advisory (pdf_78382, archived by the harvester) is the only source of
the modelled deposition footprint. The map is a raster image in the PDF; there is no GIS layer.
Its figures are transcribed by hand into `data/seed/army_model_20261124.csv`, each row citing
the archived file, its sha256 and page. Seed files are hand-entered by definition, so they live
in `data/seed/`, not `data/curated/` (K3), and are never edited after commit; a correction is a
new row or a new file.

Transcribed: 27 mi² at >= 100 µg/ft², 148 mi² at >= 5 µg/ft² ("Mitigated 0.26" scenario,
model as of 24 Nov 08:48), planned DTG 25 Nov 09:00 CST, and an "air sampling method detection
limit" of 0.18 µg/m³ from the dispersion-map legend. That last value names no method and must
not be read as the Xact detection limit (the EPA request still stands).
