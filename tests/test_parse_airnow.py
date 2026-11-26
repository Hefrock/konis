import json

from konis.parse import airnow

SITES = ("StationID|AQSID|FullAQSID|Parameter|MonitorType|SiteCode|SiteName|Status|AgencyID|"
         "AgencyName|EPARegion|Latitude|Longitude|Elevation|GMTOffset|CountryFIPS|CBSA_ID|"
         "CBSA_Name|StateAQSCode|StateAbbreviation|CountyAQSCode|CountyName\n"
         "x|190570001|x|PM2.5|Permanent|1|Burlington|Active|IA|Iowa DNR|R7|40.80|-91.12||"
         "-6|US||||IA||Des Moines\n")


def _w(root, key, stamp, body):
    d = root / "airnow_hourly" / "2026-11-25"
    d.mkdir(parents=True, exist_ok=True)
    name = f"{key}__{stamp}__x.dat"
    (d / name).write_text(body)
    (d / name.replace(".dat", ".manifest.json")).write_text(json.dumps(
        {"fetched_at_utc": f"2026-11-25T{stamp}:00+00:00", "file": name, "key": key,
         "sha256": stamp, "upstream_bytes": len(body)}))


ROW = "11/25/26|18:00|190570001|Burlington|-6|PM2.5|UG/M3|{v}|Iowa DNR\n"


def test_partial_then_full_then_revision(tmp_path):
    _w(tmp_path, "sites", "19:00", SITES)
    _w(tmp_path, "2026112518", "19:00", "")                  # early partial: nothing yet
    _w(tmp_path, "2026112518", "20:00", ROW.format(v="6.7"))
    _w(tmp_path, "2026112518", "21:00", ROW.format(v="6.7"))  # unchanged
    _w(tmp_path, "2026112518", "22:00", ROW.format(v="7.1"))  # revised
    df = airnow.build(tmp_path).sort("revision")
    assert df["value_reported"].to_list() == [6.7, 7.1]
    assert df["superseded_at_utc"][0].startswith("2026-11-25T22:00")
    r = df.row(0, named=True)
    assert r["valid_hour_utc"] == "2026-11-25T18:00:00+00:00" and not r["time_mismatch"]
    assert r["state"] == "IA" and 5 < r["distance_km"] < 15
    assert 45 < r["bearing_from_iaaap_deg"] < 135  # Burlington is east of IAAAP


def test_time_mismatch_and_negative_flagged(tmp_path):
    _w(tmp_path, "2026112519", "20:00", ROW.format(v="-1.0"))
    r = airnow.build(tmp_path).row(0, named=True)
    assert r["time_mismatch"] and r["negative_value"] and r["latitude"] is None
