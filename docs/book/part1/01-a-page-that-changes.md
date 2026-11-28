# A page that changes on every visit

!!! info "Edition"
    As of: 2026-11-25 · Pinned to: `99ef1e0` · Status: outline

## What we believed

TODO: that hashing a page tells you whether it changed.

## What we found

EPA's response site embeds per-request tokens, so hashing the raw bytes would record a new version every 30 minutes. Change is judged on a normalized copy; the exact bytes are still what is saved. TODO: show one real before/after pair from `data/raw/epa_osc_site/`.

## What it taught

Decide what "changed" means before trusting a hash. TODO: tie to K1 (raw first, immutable).

## Sources

- docs/lessons.md #1
- ADR 0001, ADR 0005
- `src/konis/capture/engine.py` (normalization; read before writing)
