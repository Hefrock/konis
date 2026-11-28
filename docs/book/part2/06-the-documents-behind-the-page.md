# The documents behind the page

!!! info "Edition"
    As of: 2026-11-26 · Pinned to: `99ef1e0` · Status: outline

## What we believed

TODO: that the web pages were the source material.

## What we found

The pages linked to the sampling plan, the permit and its appendices. Two were 78 MB and 191 MB, so a size guard would have dropped exactly the files that say how lead was to be measured. Large files go to a release asset with their hash kept in the repository. A related lesson: AirNow files grow after they are published, so early copies are kept and later rows are added.

## What it taught

The most important evidence is often one click behind the page you archived, and a safety guard can quietly delete it. TODO: worked example of one manifest pointing at a `docs-archive` asset.

## Sources

- docs/lessons.md #7, #8
- ADR 0002, ADR 0008
- `src/konis/guards.py` (10 MB limit)
