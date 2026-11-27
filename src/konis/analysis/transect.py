"""ADR 0012: Xact readings by distance along the south-west transect.

Part A (exploratory, 25 Nov): per-station description; no slope, test or interval.
Part B (confirmatory, prospective): resuspension episodes after the acceptance time.

Definitions are fixed by ADR 0012 (accepted 2026-11-26T13:20Z). Clarifications recorded in
the ADR: (1) "no measurable precipitation" means no KBRL report with precip_in > 0 (a trace is
not measurable), and a UTC day counts only if it has at least MIN_OBS_PER_DAY reports;
(2) the dry streak is the three complete UTC days before the gust's day plus the gust's day up
to the gust; (3) Part B baselines also use only readings after acceptance.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import polars as pl

from konis.analysis.xact_wind import ORIGIN, T0, load
from konis.geo import angular_difference, bearing_deg, haversine_km

ANALYSIS_VERSION = "transect/1"
ACCEPTED = datetime(2026, 11, 26, 13, 20, tzinfo=UTC)
EVENT_HOURS = 8
DRY_DAYS, GUST_MS, EPISODE_HOURS, BASELINE_DAYS = 3, 6.7, 12, 7
MIN_OBS_PER_DAY = 20
TRANSECT_BEARING, TRANSECT_CONE = 233.0, 45.0


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s)


def stations(x: pl.DataFrame) -> list[dict]:
    out = []
    for sid, lat, lon in (x.group_by("station_id")
                          .agg(pl.col("latitude").first(), pl.col("longitude").first())
                          .sort("station_id").iter_rows()):
        out.append({"station_id": sid, "distance_km": haversine_km(*ORIGIN, lat, lon),
                    "bearing_deg": bearing_deg(*ORIGIN, lat, lon)})
    return sorted(out, key=lambda s: s["distance_km"])


def _summ(rows: list[dict]) -> dict:
    n = len(rows)
    k = sum(1 for r in rows if not r["reported_zero"])
    vals = [r["value_reported"] for r in rows if r["value_reported"] is not None]
    return {"n": n, "nonzero": k, "prop": (k / n) if n else None,
            "max": max(vals) if vals else None}


# ----------------------------------------------------------------------------- Part A

def part_a(curated: Path = Path("data/curated")) -> list[dict]:
    x, _ = load(curated)
    rows = list(x.iter_rows(named=True))
    out = []
    for s in stations(x):
        mine = [r for r in rows if r["station_id"] == s["station_id"]]
        pre = [r for r in mine if _ts(r["observed_at_utc"]) < T0
               and _ts(r["observed_at_utc"]).date() == T0.date()]
        ev = [r for r in mine if T0 <= _ts(r["observed_at_utc"]) < T0 + timedelta(hours=EVENT_HOURS)]
        a, b = _summ(pre), _summ(ev)
        out.append({**s, "pre": a, "event": b,
                    "change": None if a["prop"] is None or b["prop"] is None
                    else b["prop"] - a["prop"]})
    return out


def svg_plot(rows: list[dict]) -> str:
    """Proportion non-zero vs distance, pre-event (open) and event window (filled)."""
    w, h, left, bottom, top = 520, 300, 60, 250, 30
    xmax = 50.0
    ymax = max([0.2] + [r[k]["prop"] or 0 for r in rows for k in ("pre", "event")])

    def px(d):
        return left + d / xmax * (w - left - 20)

    def py(p):
        return bottom - p / ymax * (bottom - top)

    el = [(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
          f'font-family="sans-serif" font-size="12">'),
          '<rect width="100%" height="100%" fill="white"/>',
          f'<line x1="{left}" y1="{bottom}" x2="{w - 20}" y2="{bottom}" stroke="#333"/>',
          f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#333"/>',
          (f'<text x="{(w + left) / 2}" y="{h - 12}" text-anchor="middle">distance from origin '
          f'along the transect (km)</text>'),
          (f'<text x="14" y="{(top + bottom) / 2}" transform="rotate(-90 14 {(top + bottom) / 2})" '
          'text-anchor="middle">proportion of readings non-zero</text>'),
          (f'<text x="{left}" y="18">25 Nov, exploratory (ADR 0012 Part A): open = before T0, '
          f'filled = T0 to T0+{EVENT_HOURS} h</text>')]
    for d in (0, 10, 20, 30, 40, 50):
        el.append(f'<text x="{px(d)}" y="{bottom + 16}" text-anchor="middle">{d}</text>')
    for i in range(5):
        p = ymax * i / 4
        el.append(f'<text x="{left - 6}" y="{py(p) + 4}" text-anchor="end">{p:.2f}</text>')
    for r in rows:
        x0 = px(r["distance_km"])
        if r["pre"]["prop"] is not None:
            el.append(f'<circle cx="{x0 - 4}" cy="{py(r["pre"]["prop"])}" r="5" fill="none" '
                      'stroke="#1f5fa8" stroke-width="2"/>')
        if r["event"]["prop"] is not None:
            el.append(f'<circle cx="{x0 + 4}" cy="{py(r["event"]["prop"])}" r="5" '
                      'fill="#c0392b"/>')
        el.append(f'<text x="{x0}" y="{top + 12}" text-anchor="middle" fill="#555">'
                  f'{r["station_id"]}</text>')
    el.append("</svg>")
    return "\n".join(el)


def _chg(c: float | None) -> str:
    return "—" if c is None else f"{c:+.3f}"


def report_a(rows: list[dict], data_commit: str) -> str:
    def p(s):
        return "—" if s["prop"] is None else f"{s['nonzero']}/{s['n']} ({100 * s['prop']:.1f}%)"

    def mx(s):
        return "—" if s["max"] is None else f"{s['max']:.4f}"

    lines = [
        "# ADR 0012 Part A: Xact readings by distance, 25 Nov (EXPLORATORY)", "",
        (f"Analysis `{ANALYSIS_VERSION}`; data cut git `{data_commit}`; T0 {T0.isoformat()} "
        "(ADR 0011)."), "",
        ("**Exploratory.** The question was chosen after these by-station counts had been seen "
        "(ADR 0009 report). No slope, test or interval is given, by design."), "",
        ("| station | distance | pre-event non-zero | event non-zero | change | pre max | "
        "event max (µg/m³) |"), "|---|---|---|---|---|---|---|",
        *[f"| {r['station_id']} | {r['distance_km']:.1f} km | {p(r['pre'])} | {p(r['event'])} | "
          f"{_chg(r['change'])} | "
          f"{mx(r['pre'])} | {mx(r['event'])} |" for r in rows], "",
        "![Proportion non-zero by distance](transect-partA.svg)", "",
        ("Limits: EPA has published no detection limit, so \"non-zero\" is not \"detected\"; the "
        "pre-event window is only 1.5-2 hours per station; four stations, one event. Do not "
        "compare individual readings with the lead NAAQS (3-month average)."), ""]
    return "\n".join(lines)


# ----------------------------------------------------------------------------- Part B

def _kbrl(w: pl.DataFrame) -> list[dict]:
    return [{**r, "t": _ts(r["obs_time_utc"])} for r in w.iter_rows(named=True)]


def _day_status(obs: list[dict]) -> dict:
    """UTC date -> 'dry' | 'wet' | 'incomplete'."""
    by: dict = {}
    for o in obs:
        by.setdefault(o["t"].date(), []).append(o)
    out = {}
    for d, rows in by.items():
        if any((o["precip_in"] or 0) > 0 for o in rows):
            out[d] = "wet"
        elif len(rows) < MIN_OBS_PER_DAY:
            out[d] = "incomplete"
        else:
            out[d] = "dry"
    return out


def episodes(obs: list[dict], after: datetime = ACCEPTED) -> list[dict]:
    status = _day_status(obs)
    eps: list[dict] = []
    end = None
    for o in sorted(obs, key=lambda o: o["t"]):
        if o["t"] <= after or (end and o["t"] < end):
            continue
        g = o["wind_gust_ms"]
        if g is None or g <= GUST_MS:
            continue
        day = o["t"].date()
        prior = [day - timedelta(days=i) for i in range(1, DRY_DAYS + 1)]
        if not all(status.get(d) == "dry" for d in prior):
            continue
        same_day = [p for p in obs if p["t"].date() == day and p["t"] <= o["t"]]
        if any((p["precip_in"] or 0) > 0 for p in same_day):
            continue
        start = o["t"]
        end = start + timedelta(hours=EPISODE_HOURS)
        eps.append({"episode_id": start.strftime("EP%Y%m%dT%H%MZ"), "start": start, "end": end,
                    "trigger_gust_ms": g})
    return eps


def _spearman(xs: list[float], ys: list[float]) -> float | None:
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    if len(xs) < 3:
        return None
    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry, strict=True))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return None if den == 0 else num / den


def evaluate(ep: dict, eps: list[dict], xrows: list[dict], obs: list[dict],
             st: list[dict]) -> dict:
    def in_any(t):
        return any(e["start"] <= t < e["end"] for e in eps)

    rows = [{**r, "t": _ts(r["observed_at_utc"])} for r in xrows]
    rows = [r for r in rows if r["t"] > ACCEPTED]
    per = []
    for s in st:
        mine = [r for r in rows if r["station_id"] == s["station_id"]]
        epi = [r for r in mine if ep["start"] <= r["t"] < ep["end"]]
        base = [r for r in mine if ep["start"] - timedelta(days=BASELINE_DAYS) <= r["t"]
                < ep["start"] and not in_any(r["t"])]
        a, b = _summ(base), _summ(epi)
        per.append({**s, "baseline": a, "episode": b,
                    "change": None if a["prop"] is None or b["prop"] is None
                    else b["prop"] - a["prop"]})
    usable = [p for p in per if p["change"] is not None]
    rho = _spearman([p["distance_km"] for p in usable], [p["change"] for p in usable])
    win = [o for o in obs if ep["start"] <= o["t"] < ep["end"] and o["wind_toward_deg"] is not None
           and not o["calm"] and not o["variable"]]
    toward = sum(1 for o in win
                 if angular_difference(o["wind_toward_deg"], TRANSECT_BEARING) <= TRANSECT_CONE)
    return {**ep, "stations": per, "spearman": rho, "n_stations_used": len(usable),
            "wind_obs": len(win), "wind_toward_transect": toward,
            "wind_class": ("toward transect" if win and toward / len(win) > 0.5
                           else "not toward transect" if win else "no wind data")}


def part_b(curated: Path = Path("data/curated"), now: datetime | None = None) -> dict:
    x, w = load(curated)
    obs = _kbrl(w)
    st = stations(x)
    eps = episodes(obs)
    latest_wind = max((o["t"] for o in obs), default=None)
    latest_xact = max((_ts(t) for t in x["observed_at_utc"]), default=None)
    done = [e for e in eps if latest_wind and latest_xact
            and e["end"] <= latest_wind and e["end"] <= latest_xact]
    pending = [e for e in eps if e not in done]
    xrows = list(x.iter_rows(named=True))
    return {"completed": [evaluate(e, eps, xrows, obs, st) for e in done],
            "pending": pending, "latest_wind": latest_wind, "latest_xact": latest_xact,
            "day_status": dict(sorted(_day_status(obs).items()))}


def report_b(res: dict, data_commit: str) -> str:
    def p(s):
        return "—" if s["prop"] is None else f"{s['nonzero']}/{s['n']} ({100 * s['prop']:.1f}%)"

    lines = ["# ADR 0012 Part B: resuspension episodes (confirmatory, prospective)", "",
             (f"Analysis `{ANALYSIS_VERSION}`; data cut git `{data_commit}`. Uses only Xact readings "
             f"after {ACCEPTED.isoformat()} (ADR 0012 acceptance)."), "",
             (f"Episode: {DRY_DAYS} complete dry UTC days at KBRL, then a gust > {GUST_MS} m/s; "
             f"{EPISODE_HOURS} h from the gust. Baseline: each station's readings in the prior "
             f"{BASELINE_DAYS} days outside any episode."), "",
             (f"- Latest KBRL observation: {res['latest_wind']}; latest Xact reading: "
             f"{res['latest_xact']}."),
             "- KBRL day status: " + ", ".join(f"{d} {s}" for d, s in res["day_status"].items()),
             (f"- Episodes not yet complete (awaiting data): "
             f"{', '.join(e['episode_id'] for e in res['pending']) or 'none'}."), ""]
    if not res["completed"]:
        lines += ["**No completed episode yet.** Nothing to report.", ""]
    for e in res["completed"]:
        rho = "—" if e["spearman"] is None else f"{e['spearman']:+.2f}"
        lines += [f"## {e['episode_id']}", "",
                  (f"{e['start'].isoformat()} to {e['end'].isoformat()}; trigger gust "
                  f"{e['trigger_gust_ms']:.1f} m/s; wind {e['wind_class']} "
                  f"({e['wind_toward_transect']}/{e['wind_obs']} KBRL reports within ±"
                  f"{TRANSECT_CONE:.0f}° of {TRANSECT_BEARING:.0f}°)."), "",
                  "| station | distance | baseline non-zero | episode non-zero | change |",
                  "|---|---|---|---|---|",
                  *[f"| {s['station_id']} | {s['distance_km']:.1f} km | {p(s['baseline'])} | "
                    f"{p(s['episode'])} | "
                    f"{'—' if s['change'] is None else format(s['change'], '+.3f')} |"
                    for s in e["stations"]], "",
                  (f"Spearman correlation of change with distance: {rho} "
                  f"({e['n_stations_used']} stations; descriptive, no p-value). Hypothesis "
                  "(ADR 0012): change largest at AS01 and not increasing with distance."), ""]
    lines += ["\"Non-zero\" is not \"detected\": EPA has published no detection limit.", ""]
    return "\n".join(lines)
