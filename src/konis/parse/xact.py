"""EPA Xact lead results: raw ArcGIS captures -> curated table with provenance.

Rebuilt from data/raw/epa_xact_metals/ only (K3). Captures are replayed in fetch order and
each one is judged against what was known when it was fetched (ilara lesson 5):

- a feature seen for the first time becomes revision 0;
- a feature whose published attributes later change gets a new revision row, and the
  previous row records `superseded_at_utc` (revisions are new rows, never overwrites);
- a feature missing from a later *full* snapshot gets `removed_at_utc` (deltas only add).

Values are kept exactly as published. A reported 0 is not "no lead": EPA has not published
a detection limit for this layer (K6). The EPA viewer shows one decimal place, so
`viewer_display_1dp` records what a member of the public saw on the map.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl

PARSER_VERSION = "xact/1"
SOURCE_ID = "epa_xact_metals"
CENTRAL = ZoneInfo("America/Chicago")
ANALYTE_NOTE = "EPA viewer field label 'Lead Concentration (µg/m3)'"

SCHEMA = {
    "station_id": pl.Utf8, "observed_at_utc": pl.Utf8, "observed_at_central": pl.Utf8,
    "value_reported": pl.Float64, "units": pl.Utf8, "analyte": pl.Utf8,
    "reported_zero": pl.Boolean, "viewer_display_1dp": pl.Utf8,
    "latitude": pl.Float64, "longitude": pl.Float64,
    "globalid": pl.Utf8, "objectid": pl.Int64, "revision": pl.Int64,
    "first_seen_fetched_at_utc": pl.Utf8, "superseded_at_utc": pl.Utf8,
    "removed_at_utc": pl.Utf8, "observed_after_fetch": pl.Boolean,
    "source_id": pl.Utf8, "tier": pl.Utf8, "raw_sha256": pl.Utf8, "raw_file": pl.Utf8,
    "parser_version": pl.Utf8,
}


def _iso(ms: int | None, tz=UTC) -> str | None:
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=UTC).astimezone(tz).isoformat()


def _captures(raw_root: Path):
    """Yield (manifest, doc) for every stored capture, in fetch order."""
    mans = []
    for m in (raw_root / SOURCE_ID).glob("*/*.manifest.json"):
        man = json.loads(m.read_text())
        mans.append((man["fetched_at_utc"], man["file"], m, man))
    for _, _, m, man in sorted(mans, key=lambda t: (t[0], t[1])):
        doc = json.loads((m.parent / man["file"]).read_text())
        # Stage 0 first captures used key "layer": those are full snapshots.
        mode = doc.get("mode") or ("full" if man.get("key") == "layer" else man.get("mode"))
        yield man, mode, doc, (m.parent / man["file"])


def _attr_hash(a: dict, geom: dict | None) -> str:
    return hashlib.sha256(json.dumps([a, geom], sort_keys=True).encode()).hexdigest()


def build(raw_root: Path = Path("data/raw")) -> pl.DataFrame:
    rows: list[dict] = []
    current: dict[str, tuple[str, int]] = {}  # globalid -> (attr hash, index into rows)
    revisions: dict[str, int] = {}
    for man, mode, doc, path in _captures(raw_root):
        fetched = man["fetched_at_utc"]
        fetched_dt = datetime.fromisoformat(fetched)
        seen: set[str] = set()
        for f in doc.get("features", []):
            a, g = f.get("attributes", {}), f.get("geometry")
            gid = a.get("globalid") or f"oid:{a.get('objectid')}"
            seen.add(gid)
            h = _attr_hash(a, g)
            if gid in current and current[gid][0] == h:
                continue
            if gid in current:
                rows[current[gid][1]]["superseded_at_utc"] = fetched
            rev = revisions.get(gid, -1) + 1
            revisions[gid] = rev
            ms, v = a.get("Mon_Date_Time"), a.get("Mon_Results")
            obs_utc = _iso(ms)
            rows.append({
                "station_id": a.get("Air_Station_ID"),
                "observed_at_utc": obs_utc,
                "observed_at_central": _iso(ms, CENTRAL),
                "value_reported": v,
                "units": a.get("Mon_Units"),
                "analyte": "Pb",
                "reported_zero": (v == 0) if v is not None else None,
                "viewer_display_1dp": None if v is None else f"{v:.1f}",
                "latitude": a.get("Latitude"),
                "longitude": a.get("Longitude"),
                "globalid": gid,
                "objectid": a.get("objectid"),
                "revision": rev,
                "first_seen_fetched_at_utc": fetched,
                "superseded_at_utc": None,
                "removed_at_utc": None,
                "observed_after_fetch": (obs_utc is not None
                                         and datetime.fromisoformat(obs_utc) > fetched_dt),
                "source_id": SOURCE_ID,
                "tier": man.get("tier", "T1"),
                "raw_sha256": man["sha256"],
                "raw_file": str(path.relative_to(raw_root)),
                "parser_version": PARSER_VERSION,
            })
            current[gid] = (h, len(rows) - 1)
        if mode == "full":
            for gid in [g for g in current if g not in seen]:
                rows[current[gid][1]]["removed_at_utc"] = fetched
                del current[gid]
    df = pl.DataFrame(rows, schema=SCHEMA) if rows else pl.DataFrame(schema=SCHEMA)
    return df.sort(["observed_at_utc", "station_id", "globalid", "revision"], nulls_last=True)


def write(df: pl.DataFrame, out: Path = Path("data/curated/xact_lead.csv")) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(out)
    return out


def summary(df: pl.DataFrame) -> pl.DataFrame:
    """Current (not superseded, not removed) readings per station."""
    cur = df.filter(pl.col("superseded_at_utc").is_null() & pl.col("removed_at_utc").is_null())
    return (cur.group_by("station_id")
            .agg(pl.len().alias("n"),
                 pl.col("reported_zero").sum().alias("n_reported_zero"),
                 pl.col("value_reported").max().alias("max_reported"),
                 pl.col("observed_at_utc").min().alias("first_obs_utc"),
                 pl.col("observed_at_utc").max().alias("last_obs_utc"))
            .sort("station_id"))


