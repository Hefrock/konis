# The gap nobody saw

!!! info "Edition"
    As of: 2026-11-27 · Pinned to: `99ef1e0` · Status: needs evidence

## What we believed

The watchdog (scheduled at :52, alerts after 75 minutes of silence) would catch a stopped capture.

## What we found

On 27 Nov the capture commits run 00:04, 01:04, 01:26, then 06:06 UTC: about 4.6 hours with nothing, and no `capture stale` issue has ever opened. The watchdog is a GitHub schedule and CLAUDE.md says that scheduler has fired only a few times a day. The real backup is an hourly task on the owner's account, outside the repo.

## What it taught

A guard that depends on the thing it guards is not independent. **Do not write this chapter until these are checked:** (1) which sources lost data between 02:00 and 06:00 UTC and whether METAR and IEM back-fill covered it; (2) whether the capture log or the Actions run list shows runs that failed or never started; (3) what the owner-side backup task did in that window; (4) what, if anything, was fixed afterwards.

## Sources

- `git log` of capture commits for 2026-11-27
- docs/adr/0003-capture-schedule.md, `.github/workflows/watchdog.yml`
- CLAUDE.md (Operations)
- vault `Projects/konis.md` (finding 2)
