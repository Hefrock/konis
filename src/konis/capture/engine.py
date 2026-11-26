"""Capture engine: fetch, check what was captured, save raw, log every outcome.

Lessons carried from ilara:
- a fetch that "works" but holds nothing is a failure (content checks per source);
- a blocked or challenged request is recorded as `blocked` and never worked around;
- every outcome is logged, including unchanged content.
"""

from __future__ import annotations

import io
import json
import re
import time
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse

import requests

from konis import config
from konis.capture.sources import SOURCES, Source, iem_asos_url
from konis.capture.store import Outcome, RawStore

BLOCK_MARKERS = (b"captcha", b"access denied", b"cf-challenge", b"request blocked")


class CaptureError(Exception):
    def __init__(self, status: str, detail: str, http_status: int | None = None):
        super().__init__(detail)
        self.status, self.detail, self.http_status = status, detail, http_status


class Http:
    """requests session with a descriptive UA, per-host spacing and bounded retries."""

    def __init__(self, min_gap: float = config.MIN_SECONDS_PER_HOST):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = config.USER_AGENT
        self.min_gap = min_gap
        self._last: dict[str, float] = {}

    def get(self, url: str, params: dict | None = None, allow_404: bool = False,
            headers: dict | None = None):
        host = urlparse(url).netloc
        for attempt in range(3):
            wait = self.min_gap - (time.monotonic() - self._last.get(host, -1e9))
            if wait > 0:
                time.sleep(wait)
            self._last[host] = time.monotonic()
            try:
                r = self.s.get(url, params=params, headers=headers,
                               timeout=config.HTTP_TIMEOUT)
            except requests.RequestException as e:
                if attempt == 2:
                    raise CaptureError("error", f"{type(e).__name__}: {e}") from e
                time.sleep(10 * (attempt + 1))
                continue
            if (r.status_code == 404 and allow_404) or (r.status_code == 304 and headers):
                return r
            if r.status_code in (401, 403, 451):
                raise CaptureError("blocked", f"HTTP {r.status_code}", r.status_code)
            if r.status_code == 429 or r.status_code >= 500:
                if attempt == 2:
                    raise CaptureError("error", f"HTTP {r.status_code}", r.status_code)
                time.sleep(float(r.headers.get("Retry-After", 15 * (attempt + 1))))
                continue
            if r.status_code != 200:
                raise CaptureError("error", f"HTTP {r.status_code}", r.status_code)
            head = r.content[:4000].lower()
            if any(m in head for m in BLOCK_MARKERS) and len(r.content) < 20000:
                raise CaptureError("blocked", "challenge or block page", r.status_code)
            return r
        raise CaptureError("error", "retries exhausted")


def canonical_json(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            + "\n").encode()


# ---------------------------------------------------------------- per-kind fetchers
# Each returns a list of (key, content_bytes, extra_manifest)


_VOLATILE = [
    re.compile(rb'(<input[^>]+name="__(?:VIEWSTATE|VIEWSTATEGENERATOR|EVENTVALIDATION|'
               rb'REQUESTDIGEST)"[^>]*value=")[^"]*'),
    re.compile(rb'([?&](?:dt|v|ver|_|cb|itok)=)[A-Za-z0-9._-]+'),
    re.compile(rb'(nonce=")[^"]*'),
    re.compile(rb'(KeepAliveSession\.aspx\?q=)\d+'),
    re.compile(rb'(name="csrf[-_]?token" content=")[^"]*', re.IGNORECASE),
]


def normalize_page(body: bytes) -> bytes:
    """Remove per-request tokens so change detection reflects content changes only."""
    for rx in _VOLATILE:
        body = rx.sub(rb"\1~", body)
    return body


def fetch_page(http: Http, src: Source, now: datetime):
    r = http.get(src.url)
    body = r.content
    if len(body) < src.min_bytes:
        raise CaptureError("empty", f"only {len(body)} bytes", 200)
    low = body.lower()
    if src.must_contain and not any(k.encode() in low for k in src.must_contain):
        raise CaptureError("empty", f"none of {src.must_contain} found (placeholder page?)", 200)
    return [("page", body, {"_change_bytes": normalize_page(body),
                            "content_type": r.headers.get("Content-Type", ""),
                            "final_url": r.url})]


def fetch_file(http: Http, src: Source, now: datetime):
    r = http.get(src.url)
    body = r.content
    if len(body) < src.min_bytes:
        raise CaptureError("empty", f"only {len(body)} bytes", 200)
    if src.ext == "pdf" and not body.startswith(b"%PDF"):
        raise CaptureError("empty", "not a PDF (moved or replaced by an HTML page?)", 200)
    return [("file", body, {"content_type": r.headers.get("Content-Type", ""),
                            "final_url": r.url})]


def _arcgis_json(http: Http, url: str, params: dict) -> dict:
    d = http.get(url, params={**params, "f": "json"}).json()
    if isinstance(d, dict) and "error" in d:
        raise CaptureError("error", f"ArcGIS error: {d['error']}", 200)
    return d


def fetch_arcgis_layer(http: Http, src: Source, now: datetime, store: RawStore | None = None):
    """Full snapshot once per UTC day; between them, only features with a new object id.

    A full snapshot is also taken whenever the layer was edited without adding rows, or lost
    rows, so in-place revisions and deletions are never missed (ADR 0005).
    """
    meta = _arcgis_json(http, src.url, {})
    fields = [f["name"] for f in meta.get("fields", [])]
    if not fields:
        raise CaptureError("empty", "layer metadata has no fields (schema change?)", 200)
    oid = meta.get("objectIdField") or next(
        (f["name"] for f in meta["fields"] if f["type"] == "esriFieldTypeOID"), fields[0])
    count = _arcgis_json(http, f"{src.url}/query",
                         {"where": "1=1", "returnCountOnly": "true"}).get("count")
    page = int(meta.get("maxRecordCount") or 1000)
    feats: list = []
    while True:
        d = _arcgis_json(http, f"{src.url}/query", {
            "where": "1=1", "outFields": "*", "returnGeometry": "true", "outSR": "4326",
            "orderByFields": oid, "resultOffset": len(feats), "resultRecordCount": page})
        batch = d.get("features", [])
        feats.extend(batch)
        if not batch or not d.get("exceededTransferLimit"):
            break
    if count is not None and len(feats) != count:
        raise CaptureError("error", f"paged {len(feats)} features but count says {count}", 200)
    edit_ms = (meta.get("editingInfo") or {}).get("dataLastEditDate")
    oids = [f.get("attributes", {}).get(oid) for f in feats]
    max_oid = max((o for o in oids if isinstance(o, int)), default=None)
    state = {"max_oid": max_oid, "count": len(feats), "data_last_edit_ms": edit_ms,
             "day": now.strftime("%Y-%m-%d")}
    base = {"feature_count_total": len(feats), "fields": fields, "data_last_edit_ms": edit_ms,
            "_state": state}

    latest = store.latest(src.source_id) if store else {}
    prev = max((latest.get(k, {}).get("state") or {} for k in ("full", "delta")),
               key=lambda st: st.get("max_oid") or -1, default={})
    full_day = (latest.get("full", {}).get("state") or {}).get("day")
    prev_max, prev_count = prev.get("max_oid"), prev.get("count")
    new = [f for f, o in zip(feats, oids, strict=True)
           if isinstance(o, int) and prev_max is not None and o > prev_max]
    need_full = (
        full_day != state["day"] or prev_max is None or prev_count is None
        or len(feats) != prev_count + len(new)          # rows removed or re-keyed
        or (not new and edit_ms != prev.get("data_last_edit_ms"))  # edited in place
    )
    if need_full:
        doc = {"layer_url": src.url, "mode": "full", "count": count,
               "fields": meta.get("fields"), "editingInfo": meta.get("editingInfo"),
               "features": feats}
        return [("full", canonical_json(doc), {**base, "mode": "full"})]
    doc = {"layer_url": src.url, "mode": "delta", "after_oid": prev_max, "count": count,
           "editingInfo": meta.get("editingInfo"), "features": new}
    return [("delta", canonical_json(doc),
             {**base, "mode": "delta", "after_oid": prev_max, "feature_count": len(new)})]


def fetch_arcgis_item(http: Http, src: Source, now: datetime):
    item = _arcgis_json(http, src.url, {})
    data = _arcgis_json(http, f"{src.url}/data", {})
    for volatile in ("numViews", "numComments", "numRatings", "avgRating", "lastViewed"):
        item.pop(volatile, None)
    return [("item", canonical_json({"item": item, "data": data}),
             {"title": item.get("title"), "owner": item.get("owner"),
              "modified_ms": item.get("modified")})]


def fetch_json(http: Http, src: Source, now: datetime):
    r = http.get(src.url, params=src.params)
    d = r.json()
    if not d:
        raise CaptureError("empty", "empty JSON", 200)
    return [("latest", canonical_json(d), {"records": len(d) if isinstance(d, list) else None,
                                           "params": src.params})]


def fetch_iem_asos(http: Http, src: Source, now: datetime):
    out = []
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # Completed UTC days only (yesterday and the day before, for late reports); live
    # weather comes from METAR. Re-storing today's growing file every run would bloat git.
    for day in (today - timedelta(days=2), today - timedelta(days=1)):
        url, params = iem_asos_url(day)
        body = http.get(url, params=params).content
        lines = body.decode("utf-8", "replace").strip().splitlines()
        if not lines or not lines[0].startswith("station"):
            raise CaptureError("empty", "IEM response lacks CSV header", 200)
        if len(lines) < 2:
            raise CaptureError("empty", f"no observations for {day:%Y-%m-%d}", 200)
        out.append((day.strftime("%Y-%m-%d"), body, {"rows": len(lines) - 1, "params": params}))
    return out


def _airnow_bbox_sites(http: Http, base: str, now: datetime) -> tuple[set[str], bytes, str]:
    url = f"{base}/{now:%Y}/{now:%Y%m%d}/Monitoring_Site_Locations_V2.dat"
    r = http.get(url, allow_404=True)
    if r.status_code == 404:  # new day's file not posted yet
        prev = now - timedelta(days=1)
        url = f"{base}/{prev:%Y}/{prev:%Y%m%d}/Monitoring_Site_Locations_V2.dat"
        r = http.get(url)
    lon0, lat0, lon1, lat1 = config.BBOX
    lines = r.content.decode("utf-8", "replace").splitlines()
    keep = [lines[0]]
    ids: set[str] = set()
    for ln in lines[1:]:
        p = ln.split("|")
        try:
            lat, lon = float(p[11]), float(p[12])
        except (IndexError, ValueError):
            continue
        if lat0 <= lat <= lat1 and lon0 <= lon <= lon1:
            keep.append(ln)
            ids.add(p[1])
    if not ids:
        raise CaptureError("empty", "no AirNow sites inside BBOX", 200)
    return ids, ("\n".join(keep) + "\n").encode(), url


def fetch_airnow_hourly(http: Http, src: Source, now: datetime):
    """Clip hourly national files to the study box (ADR 0002: full-file hash kept)."""
    import hashlib

    ids, sites_body, sites_url = _airnow_bbox_sites(http, src.url, now)
    out = [("sites", sites_body, {"upstream_url": sites_url, "clip": "BBOX by lat/lon",
                                  "bbox": config.BBOX})]
    got = 0
    top = now.replace(minute=0, second=0, microsecond=0)
    for h in range(1, 5):  # last four completed hours (files are revised after posting)
        t = top - timedelta(hours=h)
        url = f"{src.url}/{t:%Y}/{t:%Y%m%d}/HourlyData_{t:%Y%m%d%H}.dat"
        r = http.get(url, allow_404=True)
        if r.status_code == 404:
            continue
        full = r.content
        rows = [ln for ln in io.StringIO(full.decode("utf-8", "replace"))
                if len(ln.split("|")) > 2 and ln.split("|")[2] in ids]
        got += 1
        out.append((f"{t:%Y%m%d%H}", "".join(rows).encode(), {
            "upstream_url": url, "upstream_sha256": hashlib.sha256(full).hexdigest(),
            "upstream_bytes": len(full), "clip": "rows whose AQSID is in sites file in BBOX",
            "rows": len(rows), "valid_hour_utc": t.isoformat()}))
    if got == 0:
        raise CaptureError("empty", "none of the last 4 hourly files were available", 404)
    # Files are posted in stages, so an early version can hold no study-box rows. But a
    # full-size national file with zero study-box rows means the format or site ids changed.
    hourly = [e for _, _, e in out if "valid_hour_utc" in e]
    if all(e["rows"] == 0 for e in hourly) and any(e["upstream_bytes"] > 300_000
                                                   for e in hourly):
        raise CaptureError("empty", "full-size hourly files but no study-box rows "
                           "(format or site-id change?)", 200)
    return out


FETCHERS = {
    "page": fetch_page,
    "file": fetch_file,
    "arcgis_layer": fetch_arcgis_layer,
    "arcgis_item": fetch_arcgis_item,
    "json": fetch_json,
    "iem_asos": fetch_iem_asos,
    "airnow_hourly": fetch_airnow_hourly,
}

IEM_SOURCE = Source("iem_asos", "iem_asos", "https://mesonet.agron.iastate.edu",
                    publisher="Iowa Environmental Mesonet (FAA/NWS ASOS)", ext="csv")


def all_sources() -> tuple[Source, ...]:
    return (*SOURCES, IEM_SOURCE)


def run_capture(run_id: str, store: RawStore | None = None, only: list[str] | None = None,
                http: Http | None = None, now: datetime | None = None) -> list[Outcome]:
    store = store or RawStore()
    http = http or Http()
    outcomes: list[Outcome] = []
    for src in all_sources():
        if only and src.source_id not in only:
            continue
        t = now or datetime.now(UTC)
        stamp = t.isoformat()
        try:
            fn = FETCHERS[src.kind]
            items = (fn(http, src, t, store=store) if src.kind == "arcgis_layer"
                     else fn(http, src, t))
        except CaptureError as e:
            o = Outcome(run_id, src.source_id, "*", src.url, stamp, e.status, e.http_status,
                        detail=e.detail, tier=src.tier)
            store.log(o)
            outcomes.append(o)
            continue
        except Exception as e:  # noqa: BLE001 - parsing surprises must not stop other sources
            o = Outcome(run_id, src.source_id, "*", src.url, stamp, "error",
                        detail=f"{type(e).__name__}: {e}", tier=src.tier)
            store.log(o)
            outcomes.append(o)
            continue
        for key, body, extra in items:
            change_bytes = extra.pop("_change_bytes", None)
            state = extra.pop("_state", None)
            man = {"url": src.url, "publisher": src.publisher, "tier": src.tier,
                   "kind": src.kind, "run_id": run_id, **extra}
            stored, digest, path = store.save(source_id=src.source_id, key=key, ext=src.ext,
                                              content=body, fetched_at=t, manifest=man,
                                              change_bytes=change_bytes, state=state)
            o = Outcome(run_id, src.source_id, key, extra.get("upstream_url", src.url), stamp,
                        "stored" if stored else "unchanged", 200, len(body), digest,
                        str(path) if path else None, tier=src.tier)
            store.log(o)
            outcomes.append(o)
    if not only or "linked_docs" in only:
        from konis.capture.harvest import run_harvest
        try:
            outcomes += run_harvest(http, store, run_id, now or datetime.now(UTC))
        except Exception as e:  # noqa: BLE001 - harvester must not lose the page captures
            o = Outcome(run_id, "linked_docs", "*", "", datetime.now(UTC).isoformat(),
                        "error", detail=f"{type(e).__name__}: {e}")
            store.log(o)
            outcomes.append(o)
    return outcomes


def summarize(outcomes: list[Outcome]) -> dict[str, dict]:
    """Per-source status: ok if every outcome for the source is stored/unchanged."""
    agg: dict[str, dict] = defaultdict(lambda: {"ok": True, "stored": 0, "unchanged": 0,
                                                "failures": []})
    for o in outcomes:
        a = agg[o.source_id]
        if o.status in ("stored", "unchanged"):
            a[o.status] += 1
        else:
            a["ok"] = False
            a["failures"].append({"status": o.status, "detail": o.detail, "url": o.url,
                                  "http_status": o.http_status})
    return dict(agg)
