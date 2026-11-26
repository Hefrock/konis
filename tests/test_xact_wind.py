from datetime import timedelta

from konis.analysis import xact_wind as xw


def rec(station="S1", bearing=230.0, toward=230.0, zero=True, cv=False, matched=True,
        minutes=60):
    return {"station_id": station, "station_bearing_deg": bearing, "wind_toward_deg": toward,
            "reported_zero": zero, "calm_or_variable": cv,
            "wind_obs_utc": "x" if matched else None, "t": xw.T0 + timedelta(minutes=minutes)}


def test_groups_and_wraparound():
    assert xw.group(rec(bearing=359, toward=1), 45) == "downwind"
    assert xw.group(rec(bearing=100, toward=230), 45) == "not downwind"
    assert xw.group(rec(bearing=275, toward=230), 45) == "downwind"   # exactly 45
    assert xw.group(rec(cv=True), 45) == "calm/variable"
    assert xw.group(rec(matched=False), 45) == "unmatched"


def test_diff_undefined_without_comparison_group():
    recs = [rec(zero=False), rec()]
    assert xw._diff(recs, 45) is None
    assert xw.bootstrap_ci(recs, 45, reps=50) == (None, None, 50)


def test_diff_and_bootstrap_are_deterministic():
    recs = [rec("A", zero=False), rec("A"), rec("B", bearing=50), rec("B", bearing=50, zero=False),
            rec("C", bearing=50), rec("D")]
    assert xw._diff(recs, 45) == 1 / 3 - 1 / 3
    assert xw.bootstrap_ci(recs, 45, reps=200) == xw.bootstrap_ci(recs, 45, reps=200)


def test_windows():
    recs = [rec(minutes=-10), rec(minutes=0), rec(minutes=8 * 60 - 1), rec(minutes=8 * 60)]
    assert len(xw.window(recs, 8)) == 2 and len(xw.window(recs, None)) == 1


def test_match_wind_respects_60_minute_limit():
    import polars as pl
    x = pl.DataFrame({"observed_at_utc": ["2026-11-25T16:00:00+00:00",
                                          "2026-11-25T18:00:00+00:00"],
                      "latitude": [40.77, 40.77], "longitude": [-91.32, -91.32],
                      "reported_zero": [True, True], "station_id": ["AS01", "AS01"]})
    w = pl.DataFrame({"obs_time_utc": ["2026-11-25T15:53:00+00:00"], "calm": [False],
                      "variable": [False], "wind_toward_deg": [230.0], "wind_speed_ms": [6.7]})
    a, b = xw.match_wind(x, w)
    assert a["wind_obs_utc"] == "2026-11-25T15:53:00+00:00" and b["wind_obs_utc"] is None
