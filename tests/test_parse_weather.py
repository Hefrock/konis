import json

import pytest

from konis.parse import weather


def _w(root, sid, name, stamp, body):
    d = root / sid / "2026-11-26"
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(body)
    (d / (name.rsplit(".", 1)[0] + ".manifest.json")).write_text(json.dumps(
        {"fetched_at_utc": f"2026-11-26T{stamp}:00+00:00", "file": name, "sha256": stamp}))


def ob(wdir=200, wspd=10, wgst=None, t=1795661700, temp=1.7):
    return {"icaoId": "KBRL", "obsTime": t, "wdir": wdir, "wspd": wspd, "wgst": wgst,
            "temp": temp, "dewp": -3.3, "rawOb": "METAR KBRL ...", "lat": 40.78, "lon": -91.12}


def test_metar_units_toward_and_dedupe(tmp_path):
    _w(tmp_path, "metar_awc", "a.json", "03:00", json.dumps([ob(wgst=20)]))
    _w(tmp_path, "metar_awc", "b.json", "03:30", json.dumps([ob(wgst=20)]))  # same ob again
    df = weather.build(tmp_path)
    assert len(df) == 1
    r = df.row(0, named=True)
    assert r["wind_from_deg"] == 200 and r["wind_toward_deg"] == 20
    assert r["wind_speed_ms"] == pytest.approx(5.144, abs=1e-3)
    assert r["wind_gust_ms"] == pytest.approx(10.289, abs=1e-3)
    assert r["obs_time_utc"].endswith("+00:00")


def test_calm_variable_and_revision(tmp_path):
    _w(tmp_path, "metar_awc", "a.json", "03:00",
       json.dumps([ob(wdir=0, wspd=0, t=1), ob(wdir="VRB", wspd=3, t=2), ob(t=3)]))
    _w(tmp_path, "metar_awc", "b.json", "03:30", json.dumps([ob(t=3, temp=2.0)]))  # corrected
    df = weather.build(tmp_path).sort("obs_time_utc", "revision")
    calm, vrb, a, b = df.rows(named=True)
    assert calm["calm"] and calm["wind_from_deg"] is None and calm["wind_toward_deg"] is None
    assert vrb["variable"] and vrb["wind_from_deg"] is None and not vrb["calm"]
    assert (a["revision"], b["revision"]) == (0, 1) and a["superseded_at_utc"] is not None


def test_iem_csv_conversion_trace_and_missing(tmp_path):
    csv = ("station,valid,lon,lat,tmpf,dwpf,relh,drct,sknt,p01i,vsby,gust,metar\n"
           "BRL,2026-11-24 15:53,-91.12,40.78,32.0,23.0,69.0,270.0,12.0,T,10.0,,KBRL x\n"
           "BRL,2026-11-24 16:53,-91.12,40.78,M,M,M,M,M,0.02,10.0,22.0,KBRL y\n")
    _w(tmp_path, "iem_asos", "d.csv", "03:00", csv)
    a, b = weather.build(tmp_path).rows(named=True)
    assert a["station"] == "KBRL" and a["temp_c"] == 0.0 and a["precip_trace"]
    assert a["precip_in"] is None and a["wind_toward_deg"] == 90.0
    assert b["temp_c"] is None and b["wind_from_deg"] is None and not b["calm"]
    assert b["precip_mm"] == pytest.approx(0.51) and b["wind_gust_ms"] == pytest.approx(11.318)


def test_sources_kept_side_by_side(tmp_path):
    _w(tmp_path, "metar_awc", "a.json", "03:00", json.dumps([ob(t=1795651980)]))
    csv = ("station,valid,lon,lat,tmpf,dwpf,relh,drct,sknt,p01i,vsby,gust,metar\n"
           "BRL,2026-11-26 00:13,-91.12,40.78,35,27,72,210,10,0.00,10,,KBRL z\n")
    _w(tmp_path, "iem_asos", "d.csv", "03:00", csv)
    df = weather.build(tmp_path)
    assert sorted(df["source_id"].to_list()) == ["iem_asos", "metar_awc"]
