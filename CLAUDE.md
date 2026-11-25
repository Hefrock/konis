# konis: instructions for Claude Code

Unofficial, independent, provenance-first archive of public environmental data around the
25 November 2026 IAAAP lead azide detonation. Read `docs/PROGRESS.md` first each session.

## Invariants (adapted from hefrock/ilara; status in docs/adr/0001)

- K1 Raw first and immutable. Every fetch outcome is logged in `data/capture_log/`. Changed
  content is written to `data/raw/` with a manifest (sha256, url, fetched_at_utc, publisher,
  tier) before anything else. Never edit or delete raw. Parsing failure never blocks saving.
- K2 Check content, not job success. A fetch that returns a placeholder, an empty layer, or a
  feature count that disagrees with the server count is a failure and raises an alert.
- K3 Curated is regenerable from raw (Stage 1+). Never hand-edit curated files.
- K4 Provenance on every curated row: source_id, tier, raw_sha256, fetched_at_utc,
  observed_at_utc (the time the source says the value is for), parser_version.
- K5 Tiers. T1 official (EPA, Army, state agencies, NOAA/NWS, FAA ASOS). T2 peer-reviewed.
  T3 news / third-party maps: locating sources and sanity checks only, never merged with T1.
- K6 No fabrication. Never interpolate or forward-fill readings. A dropout stays a gap.
  "Non-detect" is not "zero" and neither is "not reported".
- K7 Polite access. Descriptive UA naming the repo, >=5 s between requests per host, respect
  robots.txt and terms. Blocked or challenged: record `blocked`, alert, do not work around.
- K8 Pre-registration. Plume cone, DiD, resuspension score and stopping rule are fixed in an
  ADR before post-event analysis. Changes apply going forward and say so.
- K9 Publication hygiene. Public repo: never commit secrets, personal data, or raw
  PurpleAir sensor rows (ToS). Bot commits only under `data/`.
- K10 Optical PM is not lead. Never present PM2.5/PM10 against lead thresholds.

## Commands

`pip install -e '.[dev]'`; `pytest -q`; `ruff check src tests`;
`konis capture [--only ID ...]`; `konis guard --base <sha> [--bot]`.
Network tests are marked `@pytest.mark.network` and skipped by default.

## Stop and ask the human when

A source blocks access; anything needs secrets or repo settings (add to docs/BLOCKERS.md);
an action is irreversible or could expose data; a pre-registered definition would change.
