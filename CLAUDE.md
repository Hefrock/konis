# konis: technical notes for contributors and Claude Code

Unofficial, independent, provenance-first archive of public data about the 25 Nov 2026 IAAAP
lead azide detonation. The README is for the public; this file is the technical reference.
Read `docs/PROGRESS.md` first each session, then the ADRs relevant to the task.

## Invariants (adapted from hefrock/ilara; ADR 0001)

- K1 Raw first and immutable. Every fetch outcome is logged in `data/capture_log/`. Changed
  content is written to `data/raw/` with a manifest (sha256, url, fetched_at_utc, publisher,
  tier) before anything else. Never edit or delete raw. Parsing failure never blocks saving.
  Documented exceptions: AirNow files clipped to the study box (ADR 0002); credential-shaped
  strings redacted (ADR 0004); files > 9 MB stored as release assets (ADR 0008).
- K2 Check content, not job success. A placeholder page, an empty layer, a count mismatch or a
  non-PDF behind a .pdf link is a failure.
- K3 Curated is regenerable from raw (`konis parse --check`). Never hand-edit curated files.
  Hand-transcribed figures go in `data/seed/`, citing file, sha256 and page; never edited.
- K4 Provenance on every curated row: source_id, tier, raw_sha256/raw_file, fetched time,
  observed time, parser_version.
- K5 Tiers. T1 official (EPA, Army, state agencies, NOAA/NWS, FAA ASOS, EarthScope). T2
  peer-reviewed. T3 news / third-party: locating sources only, never merged with T1.
- K6 No fabrication. No interpolation or forward-fill. A gap stays a gap. A reported 0 is not
  "no lead" and not "not reported"; "non-zero" is not "detected".
- K7 Polite access: descriptive UA naming the repo, >= 5 s between requests per host.
  Blocked or challenged: record `blocked`, alert, do not work around.
- K8 Pre-registration. Analysis definitions are fixed in an accepted ADR before results are
  computed; later changes apply going forward and are recorded.
- K9 Public repo: never commit secrets or personal data. The capture bot commits only under
  `data/` (`konis guard --bot`).
- K10 Optical PM is not lead. Never compare PM2.5/PM10 with lead thresholds, and never compare
  single readings with the lead NAAQS (3-month average).

## Commands

```
uv sync [--extra seismic]          # install (seismic extra: obspy, pyproj)
uv run pytest -q                   # offline tests (network tests are marked and skipped)
uv run ruff check src tests
uv run konis capture [--only ID ...] [--summary-out F] [--alerts]
uv run konis parse [--check]       # rebuild data/curated/ from raw; --check = rebuild twice
uv run konis guard --base <sha> [--bot]
uv run konis analyze xact-wind|transect-a|transect-b [--new-out F]
uv run konis seismic fetch|analyze
uv run konis release build --out DIR --tag data-YYYY-MM-DD --commit SHA
uv run konis site build [--out site]   # static status page (ADR 0016)
uv run konis verify [--assets-json F]  # re-hash raw files vs manifests (+ docs-archive assets)
```

## Layout

| Path | What |
|---|---|
| `src/konis/capture/` | `sources.py` registry, `engine.py` fetchers and checks, `store.py` raw store and redaction, `harvest.py` linked-document harvester |
| `src/konis/parse/` | curated builders: `xact`, `airnow`, `weather`, `health` |
| `src/konis/analysis/` | `xact_wind` (ADR 0009), `transect` (ADR 0012) |
| `src/konis/seismic.py` | detonation-time check (ADR 0011) |
| `src/konis/alerts.py` | GitHub Issue alerts, two-in-a-row rule (ADR 0014) |
| `src/konis/guards.py`, `geo.py`, `config.py` | push guards; great-circle math; fixed constants |
| `data/raw/<source_id>/<date>/` | raw files + `.manifest.json`; `_latest.json` per source |
| `data/curated/` | `xact_lead`, `airnow_hourly`, `weather_obs`, `ingestion_health`, `seismic_triggers` (CSV); `transect_partB.md` |
| `data/seed/`, `data/reference/` | hand-transcribed figures; one-off reference checks |
| `docs/results/` | analysis reports (named with the data-cut commit) |
| `.github/workflows/` | `ingest_live` (capture, parse, Part B, alerts), `watchdog`, `release_weekly` (ADR 0015), `site` (Pages, ADR 0016), `ci` |
| `src/konis/release.py`, `CITATION.cff` | weekly release builder; citation metadata |

## Operations

- **Schedule.** `ingest-live` is scheduled at :07 and :37 and `watchdog` at :52, but GitHub's
  scheduler has fired only a few times a day since 25 Nov. A backup scheduled task on the
  owner's account ("konis capture backup", hourly at :01) dispatches `ingest-live` when the
  last `data: capture` commit is > 45 min old. Remove it once GitHub's schedule is reliable.
- **Alerts.** `capture-failure` issues open after two consecutive failed runs and close after
  two consecutive successes. `resuspension-episode` issues open when an ADR 0012 Part B episode
  completes. `capture stale` comes from the watchdog.
- **Large files.** `data/_external_staging/` (gitignored) -> release `docs-archive`, uploaded
  before the commit; the manifest records the asset name.
- **Secrets.** None required. `AIRNOW_API_KEY` / `PURPLEAIR_API_KEY` are read by the workflow
  but unused; PurpleAir and OpenAQ were checked and not adopted (docs/sources.md).

## Decisions (docs/adr/)

0001 adopt ilara practices · 0002 AirNow clipped to box · 0003 schedule and stopping rule ·
0004 redact credential strings · 0005 incremental ArcGIS, growth budget · 0006 curated Xact,
CSV format · 0007 AirNow curated, network limits · 0008 linked-document harvester ·
0009 Xact x wind (run: undefined, no comparison group) · 0010 curated weather ·
0011 seismic detonation time · 0012 transect by distance (Part A done; Part B live) ·
0013 Missouri and Army ASC sources, T0 confirmed · 0014 two-in-a-row alerts, Army model seed ·
0015 weekly data releases · 0016 status page.

## Conventions

- Commit prefixes: `data:` (bot only), `ingest:`, `project:`, `docs:`, `ci:`, `style:`.
  Never force-push or rewrite history on `main`. Work on a branch; PR to `main`.
- Tests are offline; write golden tests from real captures for parsers.
- Times: store UTC (ISO 8601); give Central time alongside where a person reads it.
- Keep the README plain-language and claim only what the code and data support; put detail
  here or in an ADR. Re-audit README claims after substantive changes (repo-pincer method).

## Stop and ask the owner when

A source blocks access; anything needs secrets or repository settings (log it in
`docs/BLOCKERS.md`); an action is irreversible or could expose data; a pre-registered
definition would change.
