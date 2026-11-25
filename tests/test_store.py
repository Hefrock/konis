import json
from datetime import UTC, datetime

import pytest

from konis.capture.engine import (
    CaptureError,
    canonical_json,
    fetch_arcgis_layer,
    fetch_page,
    normalize_page,
    run_capture,
    summarize,
)
from konis.capture.sources import Source
from konis.capture.store import RawStore

T = datetime(2026, 11, 25, 16, 0, tzinfo=UTC)


def test_unchanged_content_is_not_stored_twice(tmp_path):
    st = RawStore(tmp_path)
    a = st.save(source_id="s", key="k", ext="txt", content=b"x", fetched_at=T, manifest={})
    b = st.save(source_id="s", key="k", ext="txt", content=b"x", fetched_at=T, manifest={})
    assert a[0] and not b[0]
    assert len(list((tmp_path / "raw" / "s").rglob("*.txt"))) == 1


def test_change_bytes_drive_dedupe_but_raw_is_exact(tmp_path):
    st = RawStore(tmp_path)
    st.save(source_id="s", key="k", ext="html", content=b"A1", fetched_at=T, manifest={},
            change_bytes=b"A")
    stored, _, _ = st.save(source_id="s", key="k", ext="html", content=b"A2",
                           fetched_at=T.replace(minute=30), manifest={}, change_bytes=b"A")
    assert not stored
    (f,) = (tmp_path / "raw" / "s").rglob("*.html")
    assert f.read_bytes() == b"A1"


def test_manifest_has_provenance(tmp_path):
    st = RawStore(tmp_path)
    _, digest, path = st.save(source_id="s", key="k", ext="json", content=b"{}",
                              fetched_at=T, manifest={"url": "u", "tier": "T1"})
    man = json.loads(path.with_name(path.name.replace(".json", ".manifest.json")).read_text())
    assert man["sha256"] == digest and man["url"] == "u" and man["fetched_at_utc"]


def test_normalize_strips_aspnet_tokens():
    a = b'<input name="__VIEWSTATE" value="abc"><link href="s.css?dt=123">'
    b = b'<input name="__VIEWSTATE" value="xyz"><link href="s.css?dt=999">'
    assert normalize_page(a) == normalize_page(b)
    assert normalize_page(b"<p>lead 1</p>") != normalize_page(b"<p>lead 2</p>")


def test_canonical_json_is_order_independent():
    assert canonical_json({"a": 1, "b": 2}) == canonical_json({"b": 2, "a": 1})


class FakeResp:
    def __init__(self, content=b"", js=None, url="u"):
        self.content, self._js, self.url, self.headers = content, js, url, {}
        self.status_code = 200

    def json(self):
        return self._js


class FakeHttp:
    def __init__(self, responses):
        self.responses = responses

    def get(self, url, params=None, allow_404=False):
        key = (url, (params or {}).get("resultOffset"), (params or {}).get("returnCountOnly"))
        return self.responses[key] if key in self.responses else self.responses[url]


def test_placeholder_page_counts_as_empty():
    src = Source("x", "page", "u", must_contain=("lead",), min_bytes=1)
    with pytest.raises(CaptureError) as e:
        fetch_page(FakeHttp({"u": FakeResp(b"<p>Content not available</p>")}), src, T)
    assert e.value.status == "empty"


def test_arcgis_count_mismatch_is_error():
    u = "L"
    meta = {"fields": [{"name": "objectid", "type": "esriFieldTypeOID"}], "maxRecordCount": 2}
    http = FakeHttp({
        (u, None, None): FakeResp(js=meta),
        (f"{u}/query", None, "true"): FakeResp(js={"count": 3}),
        (f"{u}/query", 0, None): FakeResp(js={"features": [{}, {}],
                                              "exceededTransferLimit": False}),
    })
    with pytest.raises(CaptureError):
        fetch_arcgis_layer(http, Source("x", "arcgis_layer", u), T)


def test_arcgis_pages_until_done():
    u = "L"
    meta = {"fields": [{"name": "objectid", "type": "esriFieldTypeOID"}], "maxRecordCount": 2}
    http = FakeHttp({
        (u, None, None): FakeResp(js=meta),
        (f"{u}/query", None, "true"): FakeResp(js={"count": 3}),
        (f"{u}/query", 0, None): FakeResp(js={"features": [{}, {}],
                                              "exceededTransferLimit": True}),
        (f"{u}/query", 2, None): FakeResp(js={"features": [{}]}),
    })
    ((_, _body, extra),) = fetch_arcgis_layer(http, Source("x", "arcgis_layer", u), T)
    assert extra["feature_count_total"] == 3


def test_failures_are_logged_and_summarized(tmp_path, monkeypatch):
    from konis.capture import engine

    def boom(http, src, now):
        raise CaptureError("blocked", "HTTP 403", 403)

    monkeypatch.setattr(engine, "all_sources", lambda: (Source("x", "page", "u"),))
    monkeypatch.setitem(engine.FETCHERS, "page", boom)
    out = run_capture("r1", RawStore(tmp_path), http=object(), now=T)
    s = summarize(out)
    assert s["x"]["ok"] is False and s["x"]["failures"][0]["status"] == "blocked"
    assert list((tmp_path / "capture_log").rglob("r1.jsonl"))


def test_tokens_redacted_before_storage(tmp_path):
    tok = b"pk.eyJ1IjoiZXhhbXBsZSJ9.abcDEF123_-x"
    st = RawStore(tmp_path)
    _, _, path = st.save(source_id="s", key="k", ext="html", content=b"<a>" + tok + b"</a>",
                         fetched_at=T, manifest={})
    body = path.read_bytes()
    assert tok not in body and b"[REDACTED:mapbox_token]" in body
    man = json.loads(path.with_name(path.name.replace(".html", ".manifest.json")).read_text())
    assert man["redactions"][0]["kind"] == "mapbox_token"
    assert "upstream_sha256_before_redaction" in man


def _layer_http(features, edit_ms=1):
    u = "L"
    meta = {"fields": [{"name": "objectid", "type": "esriFieldTypeOID"}],
            "maxRecordCount": 1000, "editingInfo": {"dataLastEditDate": edit_ms}}
    return FakeHttp({
        (u, None, None): FakeResp(js=meta),
        (f"{u}/query", None, "true"): FakeResp(js={"count": len(features)}),
        (f"{u}/query", 0, None): FakeResp(js={"features": features}),
    })


def _feats(*oids, v=0):
    return [{"attributes": {"objectid": o, "v": v}} for o in oids]


def _save_all(st, items, t):
    for key, body, extra in items:
        state = extra.pop("_state", None)
        st.save(source_id="x", key=key, ext="json", content=body, fetched_at=t,
                manifest=extra, state=state)


def test_arcgis_full_then_delta_then_full_on_edit_and_new_day(tmp_path):
    st, src = RawStore(tmp_path), Source("x", "arcgis_layer", "L")
    items = fetch_arcgis_layer(_layer_http(_feats(1, 2), 1), src, T, store=st)
    assert items[0][0] == "full"
    _save_all(st, items, T)

    items = fetch_arcgis_layer(_layer_http(_feats(1, 2, 3), 2), src, T, store=st)
    assert items[0][0] == "delta" and json.loads(items[0][1])["features"] == _feats(3)
    _save_all(st, items, T.replace(minute=30))

    # edited in place (no new rows, edit time moved): full snapshot
    items = fetch_arcgis_layer(_layer_http(_feats(1, 2, 3, v=9), 3), src, T, store=st)
    assert items[0][0] == "full"
    _save_all(st, items, T.replace(minute=45))

    # a row disappeared: full snapshot
    items = fetch_arcgis_layer(_layer_http(_feats(1, 3), 3), src, T, store=st)
    assert items[0][0] == "full"

    # next UTC day with no change: full requested, content identical so not stored again
    t2 = T.replace(day=26)
    items = fetch_arcgis_layer(_layer_http(_feats(1, 2, 3, v=9), 3), src, t2, store=st)
    assert items[0][0] == "full"
