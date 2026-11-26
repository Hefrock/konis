"""Raw store: content is written exactly as received, with a hash, before anything else.

Layout
  data/raw/<source_id>/<YYYY-MM-DD>/<key>__<YYYYMMDDTHHMMSSZ>__<sha12>.<ext>
  data/raw/<source_id>/<YYYY-MM-DD>/<same stem>.manifest.json
  data/raw/<source_id>/_latest.json          last stored sha256 per key
  data/capture_log/<YYYY-MM-DD>/<run_id>.jsonl  every fetch outcome, changed or not

Raw files are never edited or deleted (append-only; enforced by `konis guard`).
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from konis import config


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# Credential-shaped strings embedded in public pages (e.g. a site's own Mapbox map token).
# They are redacted before storage so the public repo never carries them (ADR 0004).
REDACT = [
    ("mapbox_token", re.compile(rb"\b(?:pk|sk|tk)\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")),
    ("google_api_key", re.compile(rb"\bAIza[0-9A-Za-z_-]{35}")),
    ("aws_access_key", re.compile(rb"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("github_token", re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{36,}")),
    ("slack_token", re.compile(rb"\bxox[abposr]-[A-Za-z0-9-]{10,}")),
    ("arcgis_token", re.compile(rb"([?&]token=)[A-Za-z0-9._-]{20,}")),
]


def redact(content: bytes) -> tuple[bytes, list[dict]]:
    found = []
    for name, rx in REDACT:
        def sub(m, name=name, rx=rx):
            found.append({"kind": name, "sha256": sha256(m.group(0))})
            prefix = m.group(1) if rx.groups else b""
            return prefix + b"[REDACTED:" + name.encode() + b"]"
        content = rx.sub(sub, content)
    return content, found


def _safe(key: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", key).strip("-") or "default"


@dataclass
class Outcome:
    run_id: str
    source_id: str
    key: str
    url: str
    fetched_at_utc: str
    status: str  # stored | unchanged | empty | error | blocked
    http_status: int | None = None
    bytes: int = 0
    sha256: str | None = None
    path: str | None = None
    detail: str = ""
    tier: str = "T1"


EXTERNAL_RELEASE_TAG = "docs-archive"


class RawStore:
    def __init__(self, root: Path = config.DATA_DIR):
        self.raw = root / "raw"
        self.logs = root / "capture_log"

    def _latest_file(self, source_id: str) -> Path:
        return self.raw / source_id / "_latest.json"

    def latest(self, source_id: str) -> dict:
        p = self._latest_file(source_id)
        return json.loads(p.read_text()) if p.exists() else {}

    def save(self, *, source_id: str, key: str, ext: str, content: bytes,
             fetched_at: datetime, manifest: dict,
             change_bytes: bytes | None = None,
             state: dict | None = None,
             external_dir: Path | None = None) -> tuple[bool, str, Path | None]:
        """Store content if it changed since the last stored version for this key.

        Change is judged on `change_bytes` (a normalized form with volatile tokens removed)
        when given; the bytes written are always the exact `content` received.
        Returns (stored, sha256, path).
        """
        original_sha = sha256(content)
        content, redactions = redact(content)
        if change_bytes is not None:
            change_bytes, _ = redact(change_bytes)
        digest = sha256(content)
        change = sha256(change_bytes) if change_bytes is not None else digest
        latest = self.latest(source_id)
        prev = latest.get(_safe(key), {})
        if prev.get("change_sha256", prev.get("sha256")) == change:
            if state is not None and prev.get("state") != state:
                prev["state"] = state  # e.g. a new UTC day: keep incremental state current
                self._latest_file(source_id).write_text(
                    json.dumps(latest, indent=2, sort_keys=True) + "\n")
            return False, digest, None
        day = fetched_at.strftime("%Y-%m-%d")
        stamp = fetched_at.strftime("%Y%m%dT%H%M%SZ")
        d = self.raw / source_id / day
        d.mkdir(parents=True, exist_ok=True)
        stem = f"{_safe(key)}__{stamp}__{digest[:12]}"
        path = d / f"{stem}.{ext}"
        if path.exists():  # never overwrite raw
            raise FileExistsError(path)
        if external_dir is not None:
            # Too large for git: bytes go to a staging dir for upload as a release asset;
            # only the manifest is committed (ADR 0008).
            external_dir.mkdir(parents=True, exist_ok=True)
            asset = f"{digest[:16]}__{path.name}"
            (external_dir / asset).write_bytes(content)
            manifest = {**manifest, "external": {"release_tag": EXTERNAL_RELEASE_TAG,
                                                 "asset_name": asset}}
        else:
            path.write_bytes(content)
        man = {"source_id": source_id, "key": key, "sha256": digest, "bytes": len(content),
               "change_sha256": change, "fetched_at_utc": fetched_at.isoformat(),
               "file": path.name, **manifest}
        if redactions:
            man["upstream_sha256_before_redaction"] = original_sha
            man["redactions"] = redactions
        (d / f"{stem}.manifest.json").write_text(json.dumps(man, indent=2, sort_keys=True) + "\n")
        latest[_safe(key)] = {"sha256": digest, "change_sha256": change,
                              "file": str(path.relative_to(self.raw)),
                              "fetched_at_utc": fetched_at.isoformat()}
        if state is not None:
            man["state"] = state
            latest[_safe(key)]["state"] = state
            (d / f"{stem}.manifest.json").write_text(
                json.dumps(man, indent=2, sort_keys=True) + "\n")
        self._latest_file(source_id).write_text(
            json.dumps(latest, indent=2, sort_keys=True) + "\n")
        return True, digest, path

    def touch_state(self, source_id: str, key: str, state: dict) -> None:
        """Record state for a key without storing content (e.g. a document too large to keep)."""
        latest = self.latest(source_id)
        entry = latest.setdefault(_safe(key), {})
        if entry.get("state") == state:
            return
        entry["state"] = state
        self._latest_file(source_id).parent.mkdir(parents=True, exist_ok=True)
        self._latest_file(source_id).write_text(
            json.dumps(latest, indent=2, sort_keys=True) + "\n")

    def log(self, outcome: Outcome) -> Path:
        day = outcome.fetched_at_utc[:10]
        d = self.logs / day
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{outcome.run_id}.jsonl"
        with p.open("a") as f:
            f.write(json.dumps(asdict(outcome), sort_keys=True) + "\n")
        return p
