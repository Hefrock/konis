import json
from datetime import UTC, datetime, timedelta

from konis.capture import harvest
from konis.capture.store import RawStore

T = datetime(2026, 11, 26, 3, 0, tzinfo=UTC)


def test_official_and_document_filters():
    assert harvest.is_official("https://response.epa.gov/sites/1/files/a.pdf")
    assert harvest.is_official("https://www.army.mil/x.pdf")
    assert harvest.is_official("https://d34w7g4gy10iej.cloudfront.net/pubs/pdf_1.pdf")
    assert not harvest.is_official("https://naohp-kits.b-cdn.net/kit.pdf")
    assert not harvest.is_official("https://evilgov.com/a.pdf")
    assert harvest.is_document("https://x.gov/files/A%20B_Redacted.PDF")
    assert not harvest.is_document("https://x.gov/page.html")


def test_extract_links_resolves_and_unescapes():
    body = b'<a href="/files/a.pdf?x=1&amp;y=2">a</a><a href="mailto:x@y">m</a>' \
           b"<a href='b.xlsx'>b</a><a href=\"#top\">t</a>"
    links = harvest.extract_links(body, "https://response.epa.gov/site/p.aspx")
    assert links == ["https://response.epa.gov/files/a.pdf?x=1&y=2",
                     "https://response.epa.gov/site/b.xlsx"]


def test_doc_key_is_stable_and_unique():
    a = harvest.doc_key("https://response.epa.gov/sites/1/files/Report%20v1.pdf")
    b = harvest.doc_key("https://response.epa.gov/sites/2/files/Report%20v1.pdf")
    assert a == harvest.doc_key("https://response.epa.gov/sites/1/files/Report%20v1.pdf")
    assert a != b and " " not in a


class R:
    def __init__(self, status, body=b"", headers=None, url="u"):
        self.status_code, self.content, self.headers, self.url = status, body, headers or {}, url


class H:
    def __init__(self, resp):
        self.resp, self.calls = resp, []

    def get(self, url, params=None, allow_404=False, headers=None):
        self.calls.append(headers)
        return self.resp(url)


def _page(store, html):
    store.save(source_id="epa_osc_site", key="page", ext="html", content=html, fetched_at=T,
               manifest={"final_url": "https://response.epa.gov/site/x.aspx"})


def test_harvest_stores_new_doc_then_conditional_recheck(tmp_path, monkeypatch):
    st = RawStore(tmp_path)
    _page(st, b'<a href="/files/plan.pdf">p</a><a href="https://other.com/z.pdf">z</a>')
    h = H(lambda u: R(200, b"%PDF-1.7 data", {"ETag": '"abc"'}, u))
    out = harvest.run_harvest(h, st, "r1", T)
    assert [o.status for o in out] == ["stored"]          # non-official link ignored
    man = next((tmp_path / "raw" / "linked_docs").rglob("*.manifest.json"))
    m = json.loads(man.read_text())
    assert m["parent_source_id"] == "epa_osc_site" and m["url"].endswith("/files/plan.pdf")

    # within RECHECK_HOURS: not fetched again
    assert harvest.run_harvest(h, st, "r2", T + timedelta(hours=1)) == []
    # after: conditional GET with the stored ETag; 304 means unchanged
    h2 = H(lambda u: R(304))
    out = harvest.run_harvest(h2, st, "r3", T + timedelta(hours=7))
    assert out[0].status == "unchanged" and h2.calls[0] == {"If-None-Match": '"abc"'}


def test_large_doc_is_staged_not_committed(tmp_path, monkeypatch):
    st = RawStore(tmp_path)
    monkeypatch.setattr(harvest, "MAX_BYTES", 10)
    monkeypatch.setattr(harvest, "EXTERNAL_STAGING", tmp_path / "staging")
    _page(st, b'<a href="/files/big.pdf">b</a>')
    out = harvest.run_harvest(H(lambda u: R(200, b"%PDF" + b"x" * 50)), st, "r1", T)
    assert out[0].status == "stored"
    assert not list((tmp_path / "raw" / "linked_docs").rglob("*.pdf"))
    (asset,) = (tmp_path / "staging").iterdir()
    man = json.loads(next((tmp_path / "raw" / "linked_docs").rglob("*.manifest.json")).read_text())
    assert man["external"]["asset_name"] == asset.name and asset.name.startswith(man["sha256"][:16])


def test_html_served_for_pdf_link_is_empty(tmp_path):
    st = RawStore(tmp_path)
    _page(st, b'<a href="/files/gone.pdf">g</a>')
    out = harvest.run_harvest(H(lambda u: R(200, b"<html>Not found</html>")), st, "r1", T)
    assert out[0].status == "empty"
