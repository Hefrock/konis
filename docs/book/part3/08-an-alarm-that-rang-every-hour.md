# An alarm that rang every hour

!!! info "Edition"
    As of: 2026-11-27 · Pinned to: `99ef1e0` · Status: outline

## What we believed

TODO: that one failure should open one alert and one success should close it.

## What we found

One Army page flickered between found and not found. It opened and closed three issues in a day with a comment on every run. Alerts now need two failures in a row to open and two successes to close; every failure is still logged.

## What it taught

A person learns to ignore an alarm like that and then misses the real one. TODO: link forward to chapter 11, where the guard itself depends on an unreliable trigger.

## Sources

- docs/lessons.md #12
- ADR 0014
- `src/konis/alerts.py` (`decide`)
- closed issues #7, #9, #11, #13
