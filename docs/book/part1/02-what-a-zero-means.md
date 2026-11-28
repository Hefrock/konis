# What a zero means

!!! info "Edition"
    As of: 2026-11-25 · Pinned to: `99ef1e0` · Status: outline

## What we believed

TODO: that "zero detected" means no lead, and that the public map shows the data.

## What we found

EPA's Xact layer holds results per station and time; most are 0 and a few are small positive. The map rounds to one decimal, so 0.004 and 0.0 look the same. EPA has not published the detection limit. TODO: update the numbers from `data/curated/xact_lead.csv` at the pinned commit (at 99ef1e0: 415 rows, 4 stations, 391 zeros, 24 positive, maximum 0.0102 µg/m³).

## What it taught

A zero is a statement about an instrument. konis stores the published value and the displayed value side by side. TODO: the unsent detection-limit request as a worked example of a blocker.

## Sources

- docs/lessons.md #2, #4
- ADR 0006
- docs/requests/epa-xact-detection-limit.md
- docs/BLOCKERS.md
