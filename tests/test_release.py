import json
import zipfile

from konis import release


def _setup(root):
    d = root / "data/raw/src_a/2026-11-27"
    d.mkdir(parents=True)
    (d / "page__x.html").write_text("<p>hi</p>")
    (d / "page__x.manifest.json").write_text(json.dumps({
        "file": "page__x.html", "sha256": "abc", "bytes": 9, "source_id": "src_a",
        "url": "https://x.gov/p", "publisher": "X", "tier": "T1",
        "fetched_at_utc": "2026-11-27T10:00:00+00:00"}))
    big = root / "data/raw/linked_docs/2026-11-27"
    big.mkdir(parents=True)
    (big / "doc.manifest.json").write_text(json.dumps({
        "file": "doc.pdf", "sha256": "def", "bytes": 10**8, "source_id": "linked_docs",
        "url": "https://x.gov/d.pdf", "external": {"asset_name": "def__doc.pdf"},
        "fetched_at_utc": "2026-11-27T11:00:00+00:00"}))
    (root / "data/curated").mkdir(parents=True)
    (root / "data/curated/t.csv").write_text("a,b\n1,2\n3,4\n")
    (root / "LICENSE-DATA.md").write_text("cc-by")


def test_build_contents_and_determinism(tmp_path):
    _setup(tmp_path)
    out = tmp_path / "out"
    z, man, notes = release.build(out, "data-2026-11-30", "deadbeef", tmp_path)
    names = zipfile.ZipFile(z).namelist()
    assert {"data/curated/t.csv", "LICENSE-DATA.md", "MANIFEST.csv"} <= set(names)
    rows = man.read_text().splitlines()
    assert len(rows) == 3 and "def__doc.pdf" in rows[1] + rows[2]
    text = notes.read_text()
    assert "2 files from 2 sources" in text and "`t.csv`: 2" in text and "deadbeef" in text
    first = z.read_bytes()
    release.build(out, "data-2026-11-30", "deadbeef", tmp_path)
    assert z.read_bytes() == first   # same inputs -> identical zip
