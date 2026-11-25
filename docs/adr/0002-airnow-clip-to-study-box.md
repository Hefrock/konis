# ADR 0002: AirNow hourly files are clipped to the study box

Status: accepted (25 Nov 2026).

AirNow publishes national hourly files (~0.7 MB each, ~17 MB/day) with no API key at
files.airnowtech.org. Committing them whole would add ~0.5 GB/month to the repo.

Decision: store only rows whose AQSID is in `Monitoring_Site_Locations_V2.dat` inside
`config.BBOX`, plus the clipped site file. This departs from "raw exactly as received", so each
manifest records the full upstream file's sha256 and size and the clip rule, and the clip is
deterministic and re-runnable. The last four hours are re-fetched each run because files are
revised after posting; each revision is stored as a new version.

Known limit: the box holds 16 PM2.5 and 2 PM10 regulatory monitors (25 Nov site file), which
is too few for a powered plume-vs-control comparison on its own.
