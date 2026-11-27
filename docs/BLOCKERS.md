# Blockers

| date | need | blocks | status |
|---|---|---|---|
| 25 Nov | AirNow API key (free: https://docs.airnowapi.org/account/request/) as repo secret AIRNOW_API_KEY | optional; Stage 0 uses keyless files | open |
| 25 Nov | PurpleAir API key (https://develop.purpleair.com) as PURPLEAIR_API_KEY | Stage 2 PurpleAir cohorts | open |
| 25 Nov | Scheduled workflows run only from the default branch: Stage 0 must be merged to `main` | all scheduled capture | open |
| 25 Nov | Confirm detonation time from a T1 source (brief: 09:00 CST; some news: 9 a.m. ET = 08:00 CST) | pre/post split for Xact | resolved 27 Nov: Army ASC page says ~9:00 a.m. CST, agreeing with ADR 0011 (ADR 0013) |
| 25 Nov | Owner to send EPA the Xact detection-limit request (docs/requests/epa-xact-detection-limit.md) | interpreting reported zeros | open |
| 26 Nov | Owner review of ADR 0009 (pre-registered Xact x wind analysis) | primary analysis | done 26 Nov: accepted and run |
| 26 Nov | Owner review of ADR 0012 (Xact by distance; Part B is prospective) | transect analysis | done 26 Nov 13:20Z: accepted |
| 27 Nov | Owner: choose code and data licenses (pyproject says MIT; no LICENSE file; data unlicensed) | public reuse of the archive | resolved 27 Nov: MIT (LICENSE) + CC BY 4.0 for konis-created data/docs (LICENSE-DATA.md) |
| 27 Nov | Owner: enable GitHub Pages (Settings -> Pages -> Source: GitHub Actions) | public status page | open |
