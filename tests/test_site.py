import json

from konis import site


def test_build_page(tmp_path):
    c = tmp_path / "data/curated"
    c.mkdir(parents=True)
    hdr = ("station_id,observed_at_utc,value_reported,reported_zero,latitude,longitude,"
           "superseded_at_utc,removed_at_utc\n")
    (c / "xact_lead.csv").write_text(
        hdr + "AS01,2026-11-25T15:00:00+00:00,0.0,true,40.77,-91.32,,\n"
        "AS01,2026-11-25T16:00:00+00:00,0.002,false,40.77,-91.32,,\n"
        "AS01,2026-11-25T17:00:00+00:00,9.9,false,40.77,-91.32,2026-11-26,\n")  # superseded
    (c / "ingestion_health.csv").write_text(
        "date_utc,source_id,runs,runs_ok,runs_failed,last_failure_detail\n"
        "2026-11-27,a,3,2,1,HTTP 404\n2026-11-27,b,3,3,0,\n")
    d = tmp_path / "data/raw/linked_docs/2026-11-27"
    d.mkdir(parents=True)
    (d / "x.manifest.json").write_text(json.dumps({
        "file": "x.pdf", "url": "https://response.epa.gov/files/My%20Plan.pdf",
        "fetched_at_utc": "2026-11-27T10:00:00+00:00", "external": {"asset_name": "abc__x.pdf"}}))
    (tmp_path / "data/raw/linked_docs/_latest.json").write_text(json.dumps(
        {"k": {"fetched_at_utc": "2026-11-27T10:00:00+00:00"}}))
    html = site.build(tmp_path / "site", tmp_path).read_text()
    assert "AS01" in html and "2 readings" in html and "1 above zero" in html  # superseded dropped
    assert "My Plan.pdf" in html and "releases/download/docs-archive/abc__x.pdf" in html
    assert "HTTP 404" in html and "Unofficial and independent" in html
    assert "<script" not in html


def test_xact_notice_only_when_layer_checked_but_stale():
    from datetime import UTC, datetime

    obs = datetime(2026, 11, 27, 13, 21, tzinfo=UTC)
    stale = site.xact_notice(obs, "2026-11-28T03:49:17+00:00")
    assert "No new readings from EPA since 27 Nov 13:21 UTC" in stale
    assert "7:21 AM CST" in stale and "14 hours" in stale
    assert site.xact_notice(obs, "2026-11-27T15:00:00+00:00") == ""   # under 6 h
    assert site.xact_notice(obs, None) == ""                          # never checked
    assert site.xact_notice(None, "2026-11-28T03:49:17+00:00") == ""


def test_last_ok_check_ignores_failures(tmp_path):
    d = tmp_path / "2026-11-28"
    d.mkdir()
    (d / "r.jsonl").write_text(
        json.dumps({"source_id": "epa_xact_metals", "status": "unchanged",
                    "fetched_at_utc": "2026-11-28T01:00:00+00:00"}) + "\n" +
        json.dumps({"source_id": "epa_xact_metals", "status": "error",
                    "fetched_at_utc": "2026-11-28T02:00:00+00:00"}) + "\n")
    assert site.last_ok_check(tmp_path, "epa_xact_metals") == "2026-11-28T01:00:00+00:00"
