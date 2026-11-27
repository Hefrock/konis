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

### 4. What the public map showed (25 Nov 2026)
EPA's public viewer formats the Xact lead field to one decimal place. Every reading published
on the first day was below 0.05 µg/m³, so the map showed "0.0" even where the layer held
0.004 or 0.01. The same numbers can read as "zero" or "trace" depending on display precision.
konis keeps both: the value as published and what the map displayed (ADR 0006).

### 5. When did it happen? (25 Nov 2026)
The project brief gives 09:00 CST (15:00 UTC); some same-day news reports say "about 9 a.m.
ET" (08:00 CST). Small positive Xact readings appear at 08:40 and 08:50 CST, which are before
the blast under one time and after it under the other. The event time is now an open question
to confirm from a T1 source (Army or EPA), not a constant to assume.

### 6. No monitor where the plume was forecast to go (26 Nov 2026)
The Army forecast drift to the southwest into Missouri. The regulatory PM monitors reporting in
the study box are all in Iowa and Illinois, the nearest 65 km away, and none lies southwest. A
network can be "working" and still be unable to answer the question being asked. Absence of a
signal at these monitors says nothing about places they do not cover (ADR 0007).

### 7. A file that grows after it is published (26 Nov 2026)
AirNow posts each hourly file in stages; the first copy we saw held no rows for the study box.
Treating that copy as final would have recorded every monitor as missing for that hour. Early
copies are kept, and a later, fuller copy adds rows rather than "revising" them.

### 8. The documents behind the page (26 Nov 2026)
The pages konis archived linked to the sampling plan (QAPP), the permit and its appendices.
Two of the most important were 78 MB and 191 MB: too big for the repository, so a size guard
would have quietly dropped exactly the files that say how lead was to be measured. Large files
now go to release assets with their hash kept in the repository (ADR 0008).

### 9. Timing a blast with a microphone 37 km away (26 Nov 2026)
News reports and the project brief disagreed on the detonation time by an hour. A public
seismometer and infrasound sensor 37 km away settled it without asking anyone: ground motion at
15:00:38 UTC, then an air pressure wave 104 s later, which is the speed of sound at the
temperature the nearest airport reported. One station is weak evidence on its own; the check
that made it convincing was physics, not the pick: the two arrivals had to agree with the speed
of sound, and they did (ADR 0011).

### 10. A comparison the monitors could never make (26 Nov 2026)
The pre-registered question compared lead readings at stations downwind of the site with
stations that were not. When the analysis ran, all four EPA monitors turned out to sit on one
line running south-west from the site, the direction the wind blew all day. EPA had placed them
where the plume was expected, which is sensible for monitoring, but it means every reading was
"downwind" and there was nothing to compare against. The analysis was reported as undefined
rather than replaced by a different comparison chosen after seeing the data. Lesson: check what
contrast the data can support (here, station positions against the forecast wind) before
writing the analysis plan.

### 11. The date that moved (27 Nov 2026)
The Army's earlier public advisories, still linked from its update page, announced the
detonation for 20 November at about noon. It happened on 25 November at about 9 a.m. Anyone
reading only the first advisory would have the wrong day and the wrong hour. An archive that
keeps every version shows that the plan changed, and when, rather than only what finally
happened (ADR 0013).
