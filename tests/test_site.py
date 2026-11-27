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
