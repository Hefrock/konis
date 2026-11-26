"""Pre-registered primary analysis (ADR 0009): Xact lead readings vs. KBRL wind direction.

Every definition here is fixed by ADR 0009 (accepted 26 Nov 2026). Do not change a constant
without amending the ADR first (K8).
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

import polars as pl

from konis.geo import angular_difference, bearing_deg

ANALYSIS_VERSION = "xact_wind/1"
ORIGIN = (40.80903, -91.26903)          # QAPP ECM midpoint (ADR 0009, ADR 0011)
T0 = datetime(2026, 11, 25, 15, 0, 32, tzinfo=UTC)
T0_SOURCE = "seismic/infrasound estimate, ADR 0011 (15:00:32 UTC +/- 10 s)"
WIND_STATION, WIND_SOURCE = "KBRL", "iem_asos"
MATCH_MAX = timedelta(minutes=60)
CALM_MS = 1.0
PRIMARY_CONE, PRIMARY_HOURS = 45.0, 8
SENS_CONES, SENS_HOURS = (30.0, 60.0), (4, 24)
BOOT_REPS, BOOT_SEED = 10_000, 20261125


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s)


def load(curated: Path = Path("data/curated")) -> tuple[pl.DataFrame, pl.DataFrame]:
    x = pl.read_csv(curated / "xact_lead.csv", infer_schema_length=None).filter(
        pl.col("superseded_at_utc").is_null() & pl.col("removed_at_utc").is_null())
    w = pl.read_csv(curated / "weather_obs.csv", infer_schema_length=None).filter(
        (pl.col("station") == WIND_STATION) & (pl.col("source_id") == WIND_SOURCE)
        & pl.col("superseded_at_utc").is_null()).sort("obs_time_utc")
    return x, w


def match_wind(x: pl.DataFrame, w: pl.DataFrame) -> list[dict]:
    """Latest KBRL observation at or before each reading, within 60 minutes (else unmatched)."""
    obs = [(_ts(r["obs_time_utc"]), r) for r in w.iter_rows(named=True)]
    out = []
    for r in x.iter_rows(named=True):
        t = _ts(r["observed_at_utc"])
        prior = [o for o in obs if o[0] <= t]
        m = prior[-1] if prior and t - prior[-1][0] <= MATCH_MAX else None
        b = bearing_deg(ORIGIN[0], ORIGIN[1], r["latitude"], r["longitude"])
        rec = {**r, "t": t, "station_bearing_deg": round(b, 1), "wind_obs_utc": None,
               "wind_toward_deg": None, "wind_speed_ms": None, "calm_or_variable": None}
        if m is not None:
            o = m[1]
            cv = bool(o["calm"]) or bool(o["variable"]) or o["wind_toward_deg"] is None or (
                o["wind_speed_ms"] is not None and o["wind_speed_ms"] < CALM_MS)
            rec.update(wind_obs_utc=o["obs_time_utc"], wind_toward_deg=o["wind_toward_deg"],
                       wind_speed_ms=o["wind_speed_ms"], calm_or_variable=cv)
        out.append(rec)
    return out


def group(rec: dict, cone: float) -> str:
    if rec["wind_obs_utc"] is None:
        return "unmatched"
    if rec["calm_or_variable"]:
        return "calm/variable"
    diff = angular_difference(rec["station_bearing_deg"], rec["wind_toward_deg"])
    return "downwind" if diff <= cone else "not downwind"


def window(recs: list[dict], hours: int | None) -> list[dict]:
    if hours is None:  # pre-event: same UTC day, before T0
        return [r for r in recs if r["t"] < T0 and r["t"].date() == T0.date()]
    return [r for r in recs if T0 <= r["t"] < T0 + timedelta(hours=hours)]


def proportions(recs: list[dict], cone: float) -> dict[str, tuple[int, int]]:
    out: dict[str, tuple[int, int]] = {}
    for r in recs:
        g = group(r, cone)
        n, k = out.get(g, (0, 0))
        out[g] = (n + 1, k + (0 if r["reported_zero"] else 1))
    return out


def _diff(recs: list[dict], cone: float) -> float | None:
    p = proportions(recs, cone)
    (nd, kd), (nn, kn) = p.get("downwind", (0, 0)), p.get("not downwind", (0, 0))
    if nd == 0 or nn == 0:
        return None
    return kd / nd - kn / nn


def bootstrap_ci(recs: list[dict], cone: float, reps: int = BOOT_REPS,
                 seed: int = BOOT_SEED) -> tuple[float | None, float | None, int]:
    """Station-cluster bootstrap; replicates with an empty group are dropped and counted."""
    by_station: dict[str, list[dict]] = {}
    for r in recs:
        by_station.setdefault(r["station_id"], []).append(r)
    stations = sorted(by_station)
    rng = random.Random(seed)
    vals = []
    for _ in range(reps):
        sample = [r for s in (rng.choice(stations) for _ in stations) for r in by_station[s]]
        d = _diff(sample, cone)
        if d is not None:
            vals.append(d)
    if not vals:
        return None, None, reps
    vals.sort()
    lo, hi = vals[int(0.025 * len(vals))], vals[min(len(vals) - 1, int(0.975 * len(vals)))]
    return lo, hi, reps - len(vals)


def run(curated: Path = Path("data/curated")) -> dict:
    x, w = load(curated)
    recs = match_wind(x, w)
    res = {"analysis_version": ANALYSIS_VERSION, "t0_utc": T0.isoformat(), "t0_source": T0_SOURCE,
           "n_readings": len(recs),
           "readings_span_utc": (min(r["observed_at_utc"] for r in recs),
                                 max(r["observed_at_utc"] for r in recs)),
           "wind_span_utc": (w["obs_time_utc"].min(), w["obs_time_utc"].max()),
           "stations": sorted({(r["station_id"], r["station_bearing_deg"]) for r in recs}),
           "runs": []}
    specs = [("primary", PRIMARY_CONE, PRIMARY_HOURS)]
    specs += [(f"cone ±{c:.0f}°", c, PRIMARY_HOURS) for c in SENS_CONES]
    specs += [(f"window {h} h", PRIMARY_CONE, h) for h in SENS_HOURS]
    for label, cone, hours in specs:
        ev = window(recs, hours)
        lo, hi, dropped = bootstrap_ci(ev, cone)
        res["runs"].append({
            "label": label, "cone": cone, "hours": hours,
            "event": proportions(ev, cone), "diff": _diff(ev, cone), "ci95": (lo, hi),
            "boot_dropped": dropped,
            "pre_event": proportions(window(recs, None), cone),
            "by_station": {s: proportions([r for r in ev if r["station_id"] == s], cone)
                           for s, _ in res["stations"]},
        })
    res["records"] = recs
    return res


def _fmt(p: dict[str, tuple[int, int]]) -> str:
    order = ["downwind", "not downwind", "calm/variable", "unmatched"]
    parts = [f"{g} {k}/{n} ({100 * k / n:.1f}%)" for g in order if g in p
             for n, k in [p[g]]]
    return "; ".join(parts) or "none"


def report(res: dict, data_commit: str) -> str:
    from konis.geo import haversine_km

    st = {}
    for r in res["records"]:
        st.setdefault(r["station_id"], (r["station_bearing_deg"],
                                        haversine_km(*ORIGIN, r["latitude"], r["longitude"])))
    prim = res["runs"][0]
    lines = [
        "# Result: Xact lead readings vs. KBRL wind (ADR 0009, primary analysis)", "",
        f"- Analysis version `{res['analysis_version']}`; data cut: git commit `{data_commit}`.",
        f"- T0 = {res['t0_utc']} ({res['t0_source']}).",
        (f"- Xact readings (current rows): {res['n_readings']}, "
        f"{res['readings_span_utc'][0]} to {res['readings_span_utc'][1]}."),
        (f"- Wind: {WIND_STATION} from `{WIND_SOURCE}`, {res['wind_span_utc'][0]} to "
        f"{res['wind_span_utc'][1]}."), "",
        "## Station geometry (from the QAPP ECM midpoint)", "",
        "| station | bearing | distance |", "|---|---|---|",
        *[f"| {s} | {b:.1f}° | {d:.1f} km |" for s, (b, d) in sorted(st.items())], "",
        "## Primary estimate", "",
        (f"Event window T0 to T0 + {PRIMARY_HOURS} h, cone ±{PRIMARY_CONE:.0f}°: "
        f"{_fmt(prim['event'])}."), "",
    ]
    if prim["diff"] is None:
        lines += [
            ("**The primary estimate is not defined.** Every matched reading in the event window "
            "falls in the same group, so there is no comparison group. All four stations lie on a "
            "line south-west of the site, and the wind blew toward that line throughout."), ""]
    else:
        lo, hi = prim["ci95"]
        lines += [(f"Difference in proportion non-zero (downwind − not downwind): "
                  f"{prim['diff']:+.3f}, approximate 95% CI {lo:+.3f} to {hi:+.3f} "
                  f"(station-cluster bootstrap, {BOOT_REPS} replicates, seed {BOOT_SEED})."), ""]
    lines += ["## Pre-specified descriptive counts", "",
              ("Outcome: reading reported as non-zero (not \"detected\": EPA has published no "
              "detection limit for these monitors)."), "",
              "| analysis | event window | pre-event (same day, before T0) |", "|---|---|---|",
              *[f"| {r['label']} | {_fmt(r['event'])} | {_fmt(r['pre_event'])} |"
                for r in res["runs"]], "",
              "By station, primary window:", "",
              "| station | event window |", "|---|---|",
              *[f"| {s} | {_fmt(p)} |" for s, p in prim["by_station"].items()], "",
              "## What this does and does not show", "",
              ("- The design question (downwind vs. not downwind) cannot be answered with these "
              "monitors on this day: there were no readings outside the plume direction."),
              ("- Counts are descriptive. Four stations and one event cannot show that lead did or "
              "did not leave the site, and a non-zero reading is not a confirmed detection."),
              ("- Individual readings must not be compared with the lead NAAQS (a 3-month average). "
              "For context only, the EPA viewer cites the DOE PAC-1 short-term level, 32 µg/m³."),
              ("- Any further analysis (for example, by distance along the transect) is a new "
              "question and needs its own pre-registration before it is run (K8)."), ""]
    return "\n".join(lines)
