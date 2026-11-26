import json

from konis.parse import xact


def _write(root, stamp, key, mode, feats):
    d = root / "epa_xact_metals" / "2026-11-25"
    d.mkdir(parents=True, exist_ok=True)
    name = f"{key}__{stamp}__x.json"
    (d / name).write_text(json.dumps({"mode": mode, "features": feats}))
    (d / name.replace(".json", ".manifest.json")).write_text(json.dumps({
        "fetched_at_utc": f"2026-11-25T{stamp}:00+00:00", "file": name, "key": key,
        "sha256": stamp, "tier": "T1"}))


def _f(gid, oid, v, ms=1795618800000):
    return {"attributes": {"globalid": gid, "objectid": oid, "Mon_Results": v,
                           "Mon_Units": "µg/m3", "Air_Station_ID": "AS01",
                           "Mon_Date_Time": ms}}


def test_first_seen_revision_and_removal(tmp_path):
    _write(tmp_path, "16:00", "full", "full", [_f("a", 1, 0.0), _f("b", 2, 0.004)])
    _write(tmp_path, "16:30", "delta", "delta", [_f("c", 3, 0.01)])
    _write(tmp_path, "17:00", "full", "full", [_f("a", 1, 0.002), _f("c", 3, 0.01)])
    df = xact.build(tmp_path)
    a = df.filter(df["globalid"] == "a").sort("revision")
    assert a["revision"].to_list() == [0, 1]
    assert a["value_reported"].to_list() == [0.0, 0.002]
    assert a["superseded_at_utc"][0].startswith("2026-11-25T17:00")
    b = df.filter(df["globalid"] == "b")
    assert b["removed_at_utc"][0].startswith("2026-11-25T17:00")
    c = df.filter(df["globalid"] == "c")
    assert len(c) == 1 and c["removed_at_utc"][0] is None


def test_zero_flag_and_viewer_rounding(tmp_path):
    _write(tmp_path, "16:00", "full", "full", [_f("a", 1, 0.0), _f("b", 2, 0.0102)])
    df = xact.build(tmp_path).sort("objectid")
    assert df["reported_zero"].to_list() == [True, False]
    assert df["viewer_display_1dp"].to_list() == ["0.0", "0.0"]  # what the map showed


def test_observed_time_is_utc_with_central_copy(tmp_path):
    _write(tmp_path, "16:00", "full", "full", [_f("a", 1, 0.0)])  # 15:00 UTC
    row = xact.build(tmp_path).row(0, named=True)
    assert row["observed_at_utc"] == "2026-11-25T15:00:00+00:00"
    assert row["observed_at_central"] == "2026-11-25T09:00:00-06:00"
    assert row["observed_after_fetch"] is False


def test_rebuild_is_deterministic(tmp_path):
    _write(tmp_path, "16:00", "full", "full", [_f("b", 2, 0.1), _f("a", 1, 0.0)])
    assert xact.build(tmp_path).equals(xact.build(tmp_path))
