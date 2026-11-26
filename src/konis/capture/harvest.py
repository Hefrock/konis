"""Linked-document harvester (ADR 0008).

After the page sources are captured, read the latest stored copy of each official page,
collect links to documents (PDF, spreadsheet, CSV, Word, zip) on official domains, and
archive each document as source `linked_docs`, with the parent page recorded.

- New links are fetched in the run that finds them. Known documents are re-checked every
  RECHECK_HOURS, so a replaced file is caught without re-downloading everything each run.
- Only official domains are followed (.gov, .mil, and listed agency CDNs); a document
  is never followed further (depth 1).
- Files over MAX_BYTES are kept out of git: the bytes are staged and the workflow uploads them
  as GitHub release assets (tag `docs-archive`) before the commit; the manifest, with the
  sha256 and asset name, is committed as usual.
- Re-checks use conditional GET (ETag / Last-Modified) so unchanged documents are not
  downloaded again.
"""

from __future__ import annotations

import hashlib
import html
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

from konis.capture.sources import SOURCES, Source
from konis.capture.store import Outcome, RawStore

SOURCE = Source("linked_docs", "harvest", "", publisher="(see parent page)", ext="bin",
                note="Documents linked from official pages")
DOC_EXT = re.compile(r"\.(pdf|xlsx|xls|csv|docx|doc|zip|pptx)$", re.IGNORECASE)
OFFICIAL_SUFFIXES = (".gov", ".mil")
OFFICIAL_HOSTS = {"d34w7g4gy10iej.cloudfront.net"}  # Illinois EPA document CDN
MAX_BYTES = 9 * 1024 * 1024  # larger files go to a GitHub release asset (ADR 0008)
EXTERNAL_STAGING = Path("data/_external_staging")
RECHECK_HOURS = 6
MAX_FETCH_PER_RUN = 60
HREF = re.compile(rb"""href\s*=\s*["']([^"'#>]+)""", re.IGNORECASE)


def is_official(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in OFFICIAL_HOSTS or host.endswith(OFFICIAL_SUFFIXES)


def is_document(url: str) -> bool:
    return bool(DOC_EXT.search(unquote(urlparse(url).path)))


def doc_key(url: str) -> str:
    """Stable, filesystem-safe key: readable host/name plus a hash of the full URL."""
    u = urlparse(url)
    name = unquote(u.path.rsplit("/", 1)[-1])
    readable = re.sub(r"[^A-Za-z0-9._-]+", "-", f"{u.hostname}_{name}").strip("-")[:100]
    return f"{readable}_{hashlib.sha256(url.encode()).hexdigest()[:10]}"


def extract_links(body: bytes, base_url: str) -> list[str]:
    out = []
    for m in HREF.finditer(body):
        raw = html.unescape(m.group(1).decode("utf-8", "replace")).strip()
        if raw.lower().startswith(("mailto:", "javascript:", "tel:")):
            continue
        out.append(urljoin(base_url, raw))
    return sorted(set(out))


def discover(store: RawStore) -> dict[str, dict]:
    """url -> parent info, from the latest stored copy of every page source."""
    found: dict[str, dict] = {}
    for src in SOURCES:
        if src.kind != "page":
            continue
        latest = store.latest(src.source_id).get("page")
        if not latest:
            continue
        path = store.raw / latest["file"]
        man_path = path.with_name(path.name.rsplit(".", 1)[0] + ".manifest.json")
        base = src.url
        if man_path.exists():
            import json
            base = json.loads(man_path.read_text()).get("final_url") or src.url
        for url in extract_links(path.read_bytes(), base):
            if is_document(url) and is_official(url):
                found.setdefault(url, {"parent_source_id": src.source_id, "parent_url": base,
                                       "parent_raw_sha256": latest["sha256"]})
    return found


def run_harvest(http, store: RawStore, run_id: str, now: datetime) -> list[Outcome]:
    from konis.capture.engine import CaptureError

    outcomes: list[Outcome] = []
    latest = store.latest(SOURCE.source_id)
    found = discover(store)
    due = []
    for url, parent in found.items():
        st = latest.get(doc_key(url), {}).get("state") or {}
        last = st.get("last_checked_utc")
        if last is None or now - datetime.fromisoformat(last) >= timedelta(hours=RECHECK_HOURS):
            due.append((last is not None, url, parent))  # new links first
    for _, url, parent in sorted(due)[:MAX_FETCH_PER_RUN]:
        key, stamp = doc_key(url), now.isoformat()
        st = latest.get(key, {}).get("state") or {}
        cond = {}
        if st.get("etag"):
            cond["If-None-Match"] = st["etag"]
        if st.get("last_modified"):
            cond["If-Modified-Since"] = st["last_modified"]
        try:
            r = http.get(url, allow_404=True, headers=cond or None)
            if r.status_code == 404:
                store.touch_state(SOURCE.source_id, key,
                                  {**st, "last_checked_utc": stamp, "url": url,
                                   "last_status": 404})
                raise CaptureError("error", "HTTP 404 (document removed or moved?)", 404)
            if r.status_code == 304:  # server says unchanged since our copy
                store.touch_state(SOURCE.source_id, key, {**st, "last_checked_utc": stamp})
                o = Outcome(run_id, SOURCE.source_id, key, url, stamp, "unchanged", 304,
                            sha256=st.get("sha256"), detail="not modified (conditional GET)")
                store.log(o)
                outcomes.append(o)
                continue
            body = r.content
            if url.lower().endswith(".pdf") and not body.startswith(b"%PDF"):
                raise CaptureError("empty", "link ends in .pdf but content is not a PDF", 200)
        except CaptureError as e:
            o = Outcome(run_id, SOURCE.source_id, key, url, stamp, e.status, e.http_status,
                        detail=e.detail)
            store.log(o)
            outcomes.append(o)
            continue
        ext = DOC_EXT.search(unquote(urlparse(url).path)).group(1).lower()
        large = len(body) > MAX_BYTES
        man = {"url": url, "final_url": r.url, "publisher": urlparse(url).hostname,
               "tier": "T1", "kind": "linked_doc", "run_id": run_id,
               "content_type": r.headers.get("Content-Type", ""), **parent}
        new_state = {"last_checked_utc": stamp, "url": url,
                     "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body),
                     "etag": r.headers.get("ETag"), "last_modified": r.headers.get("Last-Modified")}
        stored, digest, path = store.save(
            source_id=SOURCE.source_id, key=key, ext=ext, content=body, fetched_at=now,
            manifest=man, state=new_state,
            external_dir=EXTERNAL_STAGING if large else None)
        o = Outcome(run_id, SOURCE.source_id, key, url, stamp,
                    "stored" if stored else "unchanged", 200, len(body), digest,
                    str(path) if path else None,
                    detail="large: staged for release asset upload" if (large and stored) else "")
        store.log(o)
        outcomes.append(o)
    return outcomes
