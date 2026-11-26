"""AirNow hourly regulatory-monitor data: raw clipped files -> curated table.

Rebuilt from data/raw/airnow_hourly/ only (K3). See ADR 0007.

File facts (observed 25-26 Nov 2026):
- `HourlyData_YYYYMMDDHH.dat` rows: date|time|AQSID|site|gmt_offset|parameter|units|value|agency.
  Every row's date/time equals the UTC hour in the file name, so times are read as UTC; any
  row that disagrees is kept and flagged `time_mismatch`.
- AirNow posts a file in stages: an early version may hold a fraction of the sites. A row
  absent from an early version is therefore *not yet published*, never "removed".
- A later version with a different value for the same site/parameter/hour is a revision:
  a new row with `revision` + 1; the previous row gets `superseded_at_utc`.
- Values are preliminary and unvalidated (EPA AQS holds the validated data, months later).
  Negative values are kept as published and flagged.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from konis.geo import bearing_deg, haversine_km

PARSER_VERSION = "airnow/1"
SOURCE_ID = "airnow_hourly"

SCHEMA = {
    "aqsid": pl.Utf8, "site_name": pl.Utf8, "parameter": pl.Utf8, "units": pl.Utf8,
    "valid_hour_utc": pl.Utf8, "value_reported": pl.Float64, "negative_value": pl.Boolean,
    "agency": pl.Utf8, "latitude": pl.Float64, "longitude": pl.Float64, "state": pl.Utf8,
    "county": pl.Utf8, "distance_km": pl.Float64, "bearing_from_iaaap_deg": pl.Float64,
    "revision": pl.Int64, "first_seen_fetched_at_utc": pl.Utf8, "superseded_at_utc": pl.Utf8,
    "time_mismatch": pl.Boolean, "upstream_file_bytes": pl.Int64,
    "source_id": pl.Utf8, "tier": pl.Utf8, "raw_sha256": pl.Utf8, "raw_file": pl.Utf8,
    "parser_version": pl.Utf8,
}

SITE_COLS = ["StationID", "AQSID", "FullAQSID", "Parameter", "MonitorType", "SiteCode",
             "SiteName", "Status", "AgencyID", "AgencyName", "EPARegion", "Latitude",
             "Longitude", "Elevation", "GMTOffset", "CountryFIPS", "CBSA_ID", "CBSA_Name",
             "StateAQSCode", "StateAbbreviation", "CountyAQSCode", "CountyName"]


def _manifests(raw_root: Path) -> list[tuple[dict, Path]]:
    out = []
    for m in (raw_root / SOURCE_ID).glob("*/*.manifest.json"):
        man = json.loads(m.read_text())
        out.append((man, m.parent / man["file"]))
    return sorted(out, key=lambda t: (t[0]["fetched_at_utc"], t[0]["file"]))


def _site_index(raw_root: Path) -> dict[str, dict]:
    """Latest known location metadata per AQSID (sites files replayed in fetch order)."""
    idx: dict[str, dict] = {}
    for man, path in _manifests(raw_root):
        if man.get("key") != "sites":
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for ln in lines[1:]:
            p = ln.split("|")
            if len(p) < len(SITE_COLS):
                continue
            r = dict(zip(SITE_COLS, p, strict=False))
            try:
                lat, lon = float(r["Latitude"]), float(r["Longitude"])
            except ValueError:
                continue
            idx[r["AQSID"]] = {"latitude": lat, "longitude": lon,
                               "state": r["StateAbbreviation"] or None,
                               "county": r["CountyName"] or None}
    return idx


def _parse_line(ln: str):
    p = ln.rstrip("\n").split("|")
    if len(p) < 9:
        return None
    try:
        when = datetime.strptime(f"{p[0]} {p[1]}", "%m/%d/%y %H:%M").replace(
            tzinfo=UTC)
        value = float(p[7])
    except ValueError:
        return None
    return {"when": when, "aqsid": p[2], "site_name": p[3], "parameter": p[5],
            "units": p[6], "value": value, "agency": p[8]}


def build(raw_root: Path = Path("data/raw")) -> pl.DataFrame:
    from konis import config

    sites = _site_index(raw_root)
    rows: list[dict] = []
    current: dict[tuple, tuple[float, int]] = {}
    revs: dict[tuple, int] = {}
    for man, path in _manifests(raw_root):
        key = man.get("key", "")
        if key == "sites" or not key.isdigit():
            continue
        file_hour = datetime.strptime(key, "%Y%m%d%H").replace(tzinfo=UTC)
        fetched = man["fetched_at_utc"]
        for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
            r = _parse_line(ln)
            if r is None:
                continue
            k = (r["aqsid"], r["parameter"], r["when"])
            if k in current and current[k][0] == r["value"]:
                continue
            if k in current:
                rows[current[k][1]]["superseded_at_utc"] = fetched
            rev = revs.get(k, -1) + 1
            revs[k] = rev
            s = sites.get(r["aqsid"], {})
            lat, lon = s.get("latitude"), s.get("longitude")
            rows.append({
                "aqsid": r["aqsid"], "site_name": r["site_name"], "parameter": r["parameter"],
                "units": r["units"], "valid_hour_utc": r["when"].isoformat(),
                "value_reported": r["value"], "negative_value": r["value"] < 0,
                "agency": r["agency"], "latitude": lat, "longitude": lon,
                "state": s.get("state"), "county": s.get("county"),
                "distance_km": (None if lat is None else
                                round(haversine_km(config.IAAAP_LAT, config.IAAAP_LON, lat, lon), 3)),
                "bearing_from_iaaap_deg": (None if lat is None else
                                           round(bearing_deg(config.IAAAP_LAT, config.IAAAP_LON,
                                                             lat, lon), 2)),
                "revision": rev, "first_seen_fetched_at_utc": fetched,
                "superseded_at_utc": None, "time_mismatch": r["when"] != file_hour,
                "upstream_file_bytes": man.get("upstream_bytes"),
                "source_id": SOURCE_ID, "tier": man.get("tier", "T1"),
                "raw_sha256": man["sha256"], "raw_file": str(path.relative_to(raw_root)),
                "parser_version": PARSER_VERSION,
            })
            current[k] = (r["value"], len(rows) - 1)
    df = pl.DataFrame(rows, schema=SCHEMA) if rows else pl.DataFrame(schema=SCHEMA)
    return df.sort(["valid_hour_utc", "parameter", "aqsid", "revision"])


def write(df: pl.DataFrame, out: Path = Path("data/curated/airnow_hourly.csv")) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(out)
    return out
