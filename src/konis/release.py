"""Weekly data release builder (ADR 0015).

`konis release build --out DIR --tag TAG` writes into DIR:
- konis-<TAG>.zip : data/curated, data/seed, data/reference, docs/results,
                         LICENSE-DATA.md and MANIFEST.csv
- MANIFEST.csv         : one row per raw capture (from its manifest): path, sha256, bytes,
                         source_id, url, publisher, tier, fetched_at_utc, external asset name
- NOTES.md             : release notes (counts and freshness, no interpretation)
The raw files themselves are in the source archive GitHub attaches to every release.
"""

from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

INCLUDE = ["data/curated", "data/seed", "data/reference", "docs/results"]
MANIFEST_FIELDS = ["path", "sha256", "bytes", "source_id", "url", "publisher", "tier",
                   "fetched_at_utc", "external_asset"]


def manifest_rows(root: Path = Path(".")) -> list[dict]:
    rows = []
    for m in sorted((root / "data/raw").glob("*/*/*.manifest.json")):
        man = json.loads(m.read_text())
        ext = (man.get("external") or {}).get("asset_name", "")
        rows.append({
            "path": str((m.parent / man["file"]).relative_to(root)),
            "sha256": man.get("sha256"), "bytes": man.get("bytes"),
            "source_id": man.get("source_id"), "url": man.get("final_url") or man.get("url"),
            "publisher": man.get("publisher"), "tier": man.get("tier"),
            "fetched_at_utc": man.get("fetched_at_utc"), "external_asset": ext,
        })
    return rows


def _csv(rows: list[dict], fields: list[str]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def _count_rows(path: Path) -> int:
    with path.open() as f:
        return max(0, sum(1 for _ in f) - 1)


def notes(rows: list[dict], tag: str, commit: str, root: Path = Path(".")) -> str:
    sources = sorted({r["source_id"] for r in rows})
    latest = max((r["fetched_at_utc"] for r in rows), default="none")
    lines = [
        f"# konis data release {tag}",
        "",
        (f"Snapshot of the archive at commit `{commit}`, built "
        f"{datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}."),
        "",
        (f"- Raw captures: {len(rows)} files from {len(sources)} sources; latest capture "
        f"{latest}. Listed with hashes in MANIFEST.csv; the files are in the source archive "
        "below (large documents in the `docs-archive` release)."),
        "- Curated tables (rows):",
    ]
    for p in sorted((root / "data/curated").glob("*.csv")):
        lines.append(f"  - `{p.name}`: {_count_rows(p)}")
    lines += [
        "",
        ("Unofficial and independent; not public health guidance. See the README for official "
        "sources and for what these data can and cannot show."),
        "",
        ("Licenses: konis-created tables and docs CC BY 4.0 (LICENSE-DATA.md); archived "
        "third-party content keeps its publishers' terms; code MIT."),
    ]
    return "\n".join(lines) + "\n"


def build(out: Path, tag: str, commit: str, root: Path = Path(".")) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    rows = manifest_rows(root)
    man_csv = _csv(rows, MANIFEST_FIELDS)
    (out / "MANIFEST.csv").write_text(man_csv)
    z = out / f"konis-{tag}.zip"
    fixed = (2026, 1, 1, 0, 0, 0)  # fixed timestamps: same content -> same zip bytes
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for d in INCLUDE:
            for p in sorted((root / d).rglob("*")):
                if p.is_file():
                    zi = zipfile.ZipInfo(str(p.relative_to(root)), fixed)
                    zi.compress_type = zipfile.ZIP_DEFLATED
                    zf.writestr(zi, p.read_bytes())
        for name, data in (("LICENSE-DATA.md", (root / "LICENSE-DATA.md").read_bytes()),
                           ("MANIFEST.csv", man_csv.encode())):
            zi = zipfile.ZipInfo(name, fixed)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(zi, data)
    (out / "NOTES.md").write_text(notes(rows, tag, commit, root))
    return [z, out / "MANIFEST.csv", out / "NOTES.md"]
