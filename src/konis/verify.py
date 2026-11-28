"""Archive integrity check (K1).

`konis verify` re-hashes every file in data/raw/<source>/<date>/ and compares it with its
manifest (sha256 and bytes). Files stored as release assets (ADR 0008) are checked against
a release asset listing when one is given (`--assets-json`, the JSON from the GitHub
releases API): name present, size equal, and sha256 equal when GitHub reports a digest.
Also reported: raw files with no manifest, and manifests whose file is missing.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(root: Path = Path("."), assets: list[dict] | None = None) -> dict:
    raw = root / "data/raw"
    problems: list[str] = []
    checked = external = assets_ok = 0
    covered: set[Path] = set()
    by_name = {a.get("name"): a for a in (assets or [])}
    for m in sorted(raw.glob("*/*/*.manifest.json")):
        man = json.loads(m.read_text())
        f = m.parent / man["file"]
        covered.add(f)
        rel = f.relative_to(root)
        ext = (man.get("external") or {}).get("asset_name")
        if ext:
            external += 1
            if assets is None:
                continue
            a = by_name.get(ext)
            if a is None:
                problems.append(f"{rel}: release asset {ext} missing")
                continue
            if a.get("size") != man.get("bytes"):
                problems.append(f"{rel}: asset size {a.get('size')} != manifest {man.get('bytes')}")
                continue
            digest = a.get("digest") or ""
            if digest.startswith("sha256:") and digest[7:] != man.get("sha256"):
                problems.append(f"{rel}: asset sha256 differs from manifest")
                continue
            assets_ok += 1
            continue
        if not f.exists():
            problems.append(f"{rel}: file missing")
            continue
        checked += 1
        if f.stat().st_size != man.get("bytes"):
            problems.append(f"{rel}: {f.stat().st_size} bytes, manifest says {man.get('bytes')}")
        elif _sha256(f) != man.get("sha256"):
            problems.append(f"{rel}: sha256 differs from manifest")
    for f in sorted(raw.glob("*/*/*")):
        if f.is_file() and not f.name.endswith(".manifest.json") and f not in covered:
            problems.append(f"{f.relative_to(root)}: no manifest")
    return {"checked": checked, "external": external, "assets_ok": assets_ok,
            "problems": problems}
