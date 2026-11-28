import hashlib
import json

from konis.verify import verify


def _put(root, name, data, **extra):
    d = root / "data/raw/src/2026-11-27"
    d.mkdir(parents=True, exist_ok=True)
    man = {"file": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), **extra}
    if not extra.get("external"):
        (d / name).write_bytes(data)
    (d / f"{name}.manifest.json").write_text(json.dumps(man))
    return d / name


def test_clean_archive_passes(tmp_path):
    _put(tmp_path, "a.json", b"{}")
    r = verify(tmp_path)
    assert r["checked"] == 1 and r["problems"] == []


def test_altered_file_and_orphan_are_reported(tmp_path):
    f = _put(tmp_path, "a.json", b"{}")
    f.write_bytes(b"[]")
    (f.parent / "stray.txt").write_text("x")
    probs = verify(tmp_path)["problems"]
    assert any("sha256 differs" in p for p in probs)
    assert any("stray.txt: no manifest" in p for p in probs)


def test_release_assets_checked_by_size_and_digest(tmp_path):
    data = b"%PDF big"
    _put(tmp_path, "big.pdf", data, external={"asset_name": "x.pdf"})
    good = [{"name": "x.pdf", "size": len(data),
             "digest": "sha256:" + hashlib.sha256(data).hexdigest()}]
    assert verify(tmp_path)["problems"] == []  # not checked without a listing
    assert verify(tmp_path, good)["assets_ok"] == 1
    bad = [{**good[0], "digest": "sha256:" + "0" * 64}]
    assert verify(tmp_path, bad)["problems"]
    assert verify(tmp_path, [])["problems"]
