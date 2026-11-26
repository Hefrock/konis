"""Surface weather: METAR (NOAA AWC) and ASOS archive (IEM) -> one curated table.

Rebuilt from data/raw/metar_awc/ and data/raw/iem_asos/ (K3). See ADR 0010.

- One row per station x observation time x source. The two sources are kept side by side,
  never merged, so a disagreement between them stays visible.
- Repeated captures of the same observation are de-duplicated; a changed observation (e.g. a
  corrected report) becomes a new revision row.
- Units are converted to SI from the published values; the published values are kept too
  (`wind_speed_kt`, `precip_in`).
- Calm (direction 0 and speed 0) and variable ("VRB") winds have no direction and are flagged.
- `wind_toward_deg` = direction the wind blows toward = (from + 180) mod 360.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

PARSER_VERSION = "weather/1"
KT_TO_MS = 0.514444

SCHEMA = {
    "station": pl.Utf8, "obs_time_utc": pl.Utf8, "source_id": pl.Utf8,
    "wind_from_deg": pl.Float64, "wind_toward_deg": pl.Float64, "wind_speed_kt": pl.Float64,
    "wind_speed_ms": pl.Float64, "wind_gust_ms": pl.Float64, "calm": pl.Boolean,
    "variable": pl.Boolean, "temp_c": pl.Float64, "dewpoint_c": pl.Float64,
    "rh_pct": pl.Float64, "precip_in": pl.Float64, "precip_mm": pl.Float64,
    "precip_trace": pl.Boolean, "visibility_mi": pl.Utf8, "raw_metar": pl.Utf8,
    "latitude": pl.Float64, "longitude": pl.Float64,
    "revision": pl.Int64, "first_seen_fetched_at_utc": pl.Utf8, "superseded_at_utc": pl.Utf8,
    "tier": pl.Utf8, "raw_sha256": pl.Utf8, "raw_file": pl.Utf8, "parser_version": pl.Utf8,
}


def _f(v):
    if v is None or v == "" or v == "M":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _wind(direction, speed_kt, gust_kt):
    variable = isinstance(direction, str) and direction.upper().startswith("VRB")
    d = None if variable else _f(direction)
    s = _f(speed_kt)
    calm = s == 0 and (d in (None, 0.0))
    if calm:
        d = None
    return {
        "wind_from_deg": d,
        "wind_toward_deg": None if d is None else (d + 180.0) % 360.0,
        "wind_speed_kt": s,
        "wind_speed_ms": None if s is None else round(s * KT_TO_MS, 3),
        "wind_gust_ms": None if _f(gust_kt) is None else round(_f(gust_kt) * KT_TO_MS, 3),
        "calm": calm, "variable": variable,
    }


def _precip(v):
    if isinstance(v, str) and v.strip().upper() == "T":
        return {"precip_in": None, "precip_mm": None, "precip_trace": True}
    x = _f(v)
    return {"precip_in": x, "precip_mm": None if x is None else round(x * 25.4, 2),
            "precip_trace": False}


def _manifests(raw_root: Path, source_id: str):
    out = []
    for m in (raw_root / source_id).glob("*/*.manifest.json"):
        man = json.loads(m.read_text())
        out.append((man, m.parent / man["file"]))
    return sorted(out, key=lambda t: (t[0]["fetched_at_utc"], t[0]["file"]))


def _metar_records(raw_root: Path):
    for man, path in _manifests(raw_root, "metar_awc"):
        for ob in json.loads(path.read_text()):
            t = ob.get("obsTime")
            if t is None:
                continue
            yield man, path, "metar_awc", {
                "station": ob.get("icaoId"),
                "obs_time_utc": datetime.fromtimestamp(t, UTC).isoformat(),
                **_wind(ob.get("wdir"), ob.get("wspd"), ob.get("wgst")),
                "temp_c": _f(ob.get("temp")), "dewpoint_c": _f(ob.get("dewp")),
                "rh_pct": None, **_precip(ob.get("precip")),
                "visibility_mi": None if ob.get("visib") is None else str(ob.get("visib")),
                "raw_metar": ob.get("rawOb"), "latitude": _f(ob.get("lat")),
                "longitude": _f(ob.get("lon")),
            }


def _iem_records(raw_root: Path):
    for man, path in _manifests(raw_root, "iem_asos"):
        for r in csv.DictReader(io.StringIO(path.read_text(errors="replace"))):
            try:
                t = datetime.strptime(r["valid"], "%Y-%m-%d %H:%M").replace(tzinfo=UTC)
            except (KeyError, ValueError):
                continue
            tf, df_ = _f(r.get("tmpf")), _f(r.get("dwpf"))
            st = r.get("station", "")
            yield man, path, "iem_asos", {
                "station": st if len(st) == 4 else f"K{st}",
                "obs_time_utc": t.isoformat(),
                **_wind(r.get("drct"), r.get("sknt"), r.get("gust")),
                "temp_c": None if tf is None else round((tf - 32) * 5 / 9, 2),
                "dewpoint_c": None if df_ is None else round((df_ - 32) * 5 / 9, 2),
                "rh_pct": _f(r.get("relh")), **_precip(r.get("p01i")),
                "visibility_mi": r.get("vsby") or None, "raw_metar": r.get("metar") or None,
                "latitude": _f(r.get("lat")), "longitude": _f(r.get("lon")),
            }


def build(raw_root: Path = Path("data/raw")) -> pl.DataFrame:
    rows: list[dict] = []
    current: dict[tuple, tuple[tuple, int]] = {}
    revs: dict[tuple, int] = {}
    for gen in (_metar_records(raw_root), _iem_records(raw_root)):
        for man, path, sid, rec in gen:
            k = (rec["station"], rec["obs_time_utc"], sid)
            sig = tuple(sorted(rec.items()))
            if k in current and current[k][0] == sig:
                continue
            fetched = man["fetched_at_utc"]
            if k in current:
                rows[current[k][1]]["superseded_at_utc"] = fetched
            rev = revs.get(k, -1) + 1
            revs[k] = rev
            rows.append({**rec, "source_id": sid, "revision": rev,
                         "first_seen_fetched_at_utc": fetched, "superseded_at_utc": None,
                         "tier": man.get("tier", "T1"), "raw_sha256": man["sha256"],
                         "raw_file": str(path.relative_to(raw_root)),
                         "parser_version": PARSER_VERSION})
            current[k] = (sig, len(rows) - 1)
    df = pl.DataFrame(rows, schema=SCHEMA) if rows else pl.DataFrame(schema=SCHEMA)
    return df.sort(["station", "obs_time_utc", "source_id", "revision"])


def write(df: pl.DataFrame, out: Path = Path("data/curated/weather_obs.csv")) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(out)
    return out
