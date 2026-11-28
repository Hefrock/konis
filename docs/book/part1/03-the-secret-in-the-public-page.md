# The secret in the public page

!!! info "Edition"
    As of: 2026-11-25 · Pinned to: `99ef1e0` · Status: outline

## What we believed

TODO: that a public page is safe to archive as-is.

## What we found

The first push was rejected: a captured state page contained a map access token the state itself publishes. Archiving the web archives whatever it embeds. Tokens are redacted before storage and the original hash is kept.

## What it taught

TODO: what redaction does to "raw is immutable" (the documented exceptions in K1), and why pattern-based redaction is best effort, not a guarantee.

## Sources

- docs/lessons.md #3
- ADR 0004
- `src/konis/capture/store.py` (REDACT patterns)
