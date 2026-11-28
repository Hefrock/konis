# The guard that depended on what it guarded

!!! info "Edition"
    As of: 2026-11-28 · Pinned to: `99ef1e0` · Status: outline

## What we believed

That the capture pipeline ran on its own schedule (`ingest-live` at :07 and :37), and that if
it stopped, the watchdog (scheduled at :52, alerting after 75 minutes of silence) would notice
and start it again.

## What we found

Counted from the Actions run list and the capture logs (25 to 28 Nov, UTC):

- Of 51 `ingest-live` runs, **6 came from GitHub's scheduler and 45 were dispatched by hand
  or by a task on the owner's own account** (CLAUDE.md, Operations). The scheduler should have
  fired about 100 times in that period.
- The `watchdog` ran **6 times** against about 53 expected. It is a GitHub schedule too, so it
  was unreliable in the same way as the thing it watches.
- Before the backup task existed, the largest gaps between captures were 104 to 128 minutes
  (five of them on 26 Nov, 01:05 to 11:02 UTC). Since then the gaps are 80, 82 and 97 minutes.
- No `capture stale` issue has ever opened. That is consistent with the watchdog's own rule
  (75 minutes, checked at :52), not evidence it works.

CLAUDE.md already says this: the scheduler "has fired only a few times a day" and a backup
task covers it. The finding is how much the archive now depends on that one task.

## What it taught

A guard that depends on the thing it guards is not independent. The archive's reliability is
the reliability of one scheduled task on one machine, and nothing in the repository can
detect it stopping.

Also a lesson about the audit itself. The first version of this chapter described a 4.6 hour
gap on 27 Nov. It was not real: commit times had been listed without an end date and sorted by
time of day, which mixed two days and manufactured a hole. The capture logs and the run list
showed no such gap. Say what the primary record says, in UTC, with explicit bounds, before
telling a story about it. (Compare chapter 10.)

## Still to check before this chapter is `draft`

1. Which sources lost data in the 104 to 128 minute gaps on 26 Nov. Pages that changed twice
   between captures lose the intermediate version; the Xact layer, AirNow files and METAR or
   IEM back-fill are less exposed.
2. What the owner-side backup task is, where it runs and what happens when that machine is
   off. Only the owner can say.
3. Whether the scheduler has recovered since the planned reset (PROGRESS item 3), and what
   was changed.

## Sources

- Actions run lists for `ingest_live.yml` and `watchdog.yml` (event type, 25 to 28 Nov)
- `data/capture_log/` fetch times, 55 runs
- ADR 0003, `.github/workflows/watchdog.yml`
- CLAUDE.md (Operations)
- docs/PROGRESS.md (planned improvement 3)
