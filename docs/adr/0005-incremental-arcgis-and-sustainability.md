# ADR 0005: Incremental ArcGIS capture and repository growth budget

Status: accepted (25 Nov 2026).

Problem: the EPA Xact layer is an ever-growing table (~4 stations x 2 readings/hour). Storing a
full snapshot whenever it changed would store ~48 growing copies a day, roughly 1 GB within
a month. The IEM ASOS file for the current day also grew and was re-stored every run.

Decision
- ArcGIS layers: one full snapshot per UTC day (skipped if identical to the last one), and
  between them a delta holding only features with an object id above the last one seen. A full
  snapshot is taken immediately if the layer lost rows, or was edited without adding rows, so
  revisions and deletions are always captured. Delta state is kept in `_latest.json`.
- IEM ASOS: only completed UTC days (the two previous days) are captured; live weather is METAR.

Budget (measured on 25 Nov, before git compression; text packs compress several-fold):
~0.3 MB/day METAR, <=1.7 MB/day AirNow clipped hourly files incl. revisions, ~0.5 MB/day
capture logs, <0.1 MB/day IEM, one Xact full per day (86 KB now, growing ~50 KB/day) plus
deltas. Expected total well under 5 MB/day uncompressed, i.e. a few hundred MB per year at
the 30-minute rate, and far less once ADR 0003's stopping rule drops capture to daily.
`konis guard` refuses any single file over 10 MB.

Actions minutes are free for public repositories. Each run takes ~2-3 minutes, mostly
the 5-second per-host politeness spacing.
