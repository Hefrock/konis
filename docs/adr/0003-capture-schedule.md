# ADR 0003: Capture schedule and stopping rule

Status: accepted (schedule and stopping rule), 25 Nov 2026.

Schedule: `ingest-live` at :07 and :37 every hour; `watchdog` at :52 dispatches a backup
run and alerts if no capture is logged for 75 minutes. Unchanged content is logged, not stored.

Stopping rule (accepted by the owner 25 Nov 2026; no literature found supporting a fixed 30 days, see
docs/sources.md): keep 30-minute capture until all of
1. a dry spell (>= 3 consecutive days with no measurable precipitation at KBRL) has occurred,
2. followed by a wind event (gusts > 6.7 m/s at KBRL) after that dry spell, and
3. EPA/Army have published post-event soil and air laboratory results,
then drop to daily capture through spring thaw. Fixed before any post-event analysis (K8).
