# Lessons

What went wrong or surprised us, written for students of environmental epidemiology.

### 1. A page that changes on every visit (25 Nov 2026)
EPA's response site embeds per-request tokens (ASP.NET view state, cache-busting
parameters, a keep-alive id). Hashing the raw bytes would store a "new version" every 30
minutes. Change is now judged on a normalized copy with those tokens removed, while the exact
bytes are still what gets saved. Lesson: decide what "changed" means before trusting a hash.

### 2. "Zero detected" is a statement about an instrument
EPA reported zero airborne lead detections in the first hours. Its public Xact layer holds
results per station and time; most are 0 and a few are small positive values. What 0 means
(below detection, blank-corrected, rounded) is not stated in the layer. Until EPA documents
the detection limit, konis records values as published and does not call 0 "no lead" (K6).

### 3. A public page that was "a secret" (25 Nov 2026)
The first push was rejected because a captured state page contained a map access token that
the state itself publishes. Archiving the web means archiving whatever it embeds. Tokens are
now redacted before storage and the original hash is kept (ADR 0004).
