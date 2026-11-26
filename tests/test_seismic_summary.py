import polars as pl

from konis.seismic import summarize


def _df(rows):
    return pl.DataFrame([{"channel": c, "onset_utc": t, "peak_sta_lta": r, "distance_km": 36.7}
                         for c, t, r in rows])


def test_pairs_seismic_with_infrasound_at_sound_speed():
    df = _df([("HHZ", "2026-11-25T15:00:38.520000Z", 16.0),
              ("BDF", "2026-11-25T15:02:22.670000Z", 7.5),   # 0.333 km/s
              ("BDF", "2026-11-25T15:00:50.000000Z", 9.0)])  # far too fast: not paired
    out = summarize(df)
    assert any("implied T0 15:00:32 UTC" in s and "0.333 km/s" in s for s in out)
    assert sum("implied T0" in s for s in out) == 1
    assert any(s.startswith("14:00 UTC") and "0 seismic onsets" in s for s in out)


def test_weak_seismic_onsets_are_not_paired():
    df = _df([("HHZ", "2026-11-25T15:00:38.520000Z", 6.0),
              ("BDF", "2026-11-25T15:02:22.670000Z", 7.5)])
    assert not any("implied T0" in s for s in summarize(df))
