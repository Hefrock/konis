from datetime import UTC, datetime, timedelta

import pytest

from konis.analysis import transect as tr

D0 = datetime(2026, 11, 27, 0, 0, tzinfo=UTC)


def day_obs(day, n=24, precip=0.0, gust=None, gust_hour=12, toward=230.0):
    out = []
    for h in range(n):
        t = day + timedelta(hours=h, minutes=53)
        out.append({"t": t, "obs_time_utc": t.isoformat(), "precip_in": precip if h == 3 else 0.0,
                    "wind_gust_ms": gust if h == gust_hour else None,
                    "wind_toward_deg": toward, "calm": False, "variable": False})
    return out


def test_episode_needs_three_complete_dry_days_then_gust():
    obs = [o for i in range(3) for o in day_obs(D0 + timedelta(days=i))]
    obs += day_obs(D0 + timedelta(days=3), gust=8.0)
    (ep,) = tr.episodes(obs, after=D0 - timedelta(days=1))
    assert ep["start"] == D0 + timedelta(days=3, hours=12, minutes=53)
    assert ep["end"] - ep["start"] == timedelta(hours=12)


def test_wet_or_incomplete_day_breaks_streak():
    wet = day_obs(D0) + day_obs(D0 + timedelta(days=1), precip=0.02) + day_obs(
        D0 + timedelta(days=2)) + day_obs(D0 + timedelta(days=3), gust=9.0)
    assert tr.episodes(wet, after=D0 - timedelta(days=1)) == []
    short = day_obs(D0) + day_obs(D0 + timedelta(days=1), n=10) + day_obs(
        D0 + timedelta(days=2)) + day_obs(D0 + timedelta(days=3), gust=9.0)
    assert tr.episodes(short, after=D0 - timedelta(days=1)) == []


def test_gust_at_threshold_or_before_acceptance_ignored():
    obs = [o for i in range(3) for o in day_obs(D0 + timedelta(days=i))]
    obs += day_obs(D0 + timedelta(days=3), gust=6.7)
    assert tr.episodes(obs, after=D0 - timedelta(days=1)) == []
    obs[-12]["wind_gust_ms"] = 9.0
    assert tr.episodes(obs, after=D0 + timedelta(days=5)) == []


def test_no_overlapping_episodes():
    obs = [o for i in range(3) for o in day_obs(D0 + timedelta(days=i))]
    d3 = day_obs(D0 + timedelta(days=3))
    for h in (2, 5, 20):
        d3[h]["wind_gust_ms"] = 8.0
    eps = tr.episodes(obs + d3, after=D0 - timedelta(days=1))
    assert [e["start"].hour for e in eps] == [2, 20]


@pytest.mark.parametrize("x,y,rho", [([1, 2, 3, 4], [1, 2, 3, 4], 1.0),
                                     ([1, 2, 3, 4], [4, 3, 2, 1], -1.0),
                                     ([1, 2, 3, 4], [1, 1, 1, 1], None)])
def test_spearman(x, y, rho):
    assert tr._spearman(x, y) == rho


def test_evaluate_uses_only_post_acceptance_and_excludes_episodes_from_baseline():
    st = [{"station_id": "AS01", "distance_km": 5.8, "bearing_deg": 232.0}]
    start = tr.ACCEPTED + timedelta(days=4)
    ep = {"episode_id": "E", "start": start, "end": start + timedelta(hours=12),
          "trigger_gust_ms": 8.0}

    def x(t, zero):
        return {"station_id": "AS01", "observed_at_utc": t.isoformat(), "reported_zero": zero,
                "value_reported": 0.0 if zero else 0.01}
    rows = [x(tr.ACCEPTED - timedelta(hours=1), False),            # before acceptance: excluded
            x(start - timedelta(days=1), True), x(start - timedelta(days=2), True),
            x(start + timedelta(hours=1), False), x(start + timedelta(hours=2), True)]
    res = tr.evaluate(ep, [ep], rows, [], st)
    s = res["stations"][0]
    assert s["baseline"]["n"] == 2 and s["episode"]["n"] == 2 and s["change"] == 0.5
    assert res["wind_class"] == "no wind data"
