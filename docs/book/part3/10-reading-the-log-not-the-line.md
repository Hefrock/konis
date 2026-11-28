# Reading the log, not the line

!!! info "Edition"
    As of: 2026-11-27 · Pinned to: `99ef1e0` · Status: outline

## What we believed

One error line on issue #14 (HTTP 404 on an Army page) looked like a page that had moved and should be retired.

## What we found

The capture log shows the page alternating between 200 and 404 (for example 404 at 20:02, 21:03 and 22:03 UTC on 27 Nov, then 200 at 23:02). It is a flaky source, not a dead one, and ADR 0014 already handled it.

## What it taught

Read the pattern before recommending a cause. This chapter is told from the audit's own mistake, on purpose.

## Sources

- Issue #14 and closed issues #7, #9, #11, #13
- `data/capture_log/2026-11-27/`
- ADR 0014
