# ADR 0010: Curated surface weather table

Status: accepted (26 Nov 2026).

`data/curated/weather_obs.csv`, rebuilt from `data/raw/metar_awc/` and `data/raw/iem_asos/`.
One row per station x observation time x source x revision.

- **Two sources, side by side.** NOAA AWC METAR (live, 3-hour window per capture) and the Iowa
  Environmental Mesonet ASOS archive (completed UTC days). They are not merged: a downstream
  analysis chooses a source explicitly. The archive fills the gaps that late or missed capture
  runs leave in the live feed.
- **Agreement check (first build):** 29 observations appear in both; wind direction and speed
  match in all 29.
- **Units:** speeds converted from knots (`wind_speed_kt` kept), temperatures from °F for IEM,
  precipitation from inches (`precip_in` kept). IEM `p01i` is reported as published; at
  non-hourly specials it is accumulation since the last hourly report, so it is not summed.
  "T" (trace) is `precip_trace` = true with no numeric value.
- **Wind:** `wind_from_deg` is the reported direction; `wind_toward_deg` = from + 180 mod 360.
  Calm (0 at 0 kt) and variable ("VRB") have no direction and are flagged (`calm`,
  `variable`). Missing ("M") stays missing.
- **Revisions:** an observation that changes between captures (a corrected report) becomes a
  new row; the old row gets `superseded_at_utc`.

ADR 0009 (proposed) uses KBRL from `iem_asos` as the primary wind source, the station EPA used
in QAPP Worksheet 17.
