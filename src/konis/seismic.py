"""Seismic / infrasound check of the detonation time (ADR 0011). Optional extra: `seismic`.

`konis seismic fetch`   pull N4.N41A HHZ (seismic) and BDF (infrasound) from EarthScope FDSN
                        for 13:50-15:20 UTC on 25 Nov 2026 and store it raw (K1).
`konis seismic analyze` STA/LTA triggers on the stored traces, written to
                        data/curated/seismic_triggers.csv, plus a summary of the two
                        candidate windows (14:00 UTC = 09:00 ET; 15:00 UTC = 09:00 CST).

This is a consistency check, not a location: one station cannot locate a source. The test
is whether a seismic onset is followed by an infrasound onset at the delay that a sound
speed consistent with the observed air temperature predicts.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from konis.capture.store import RawStore

PARSER_VERSION = "seismic/1"
FDSN = "https://service.earthscope.org"
NET, STA, CHANS = "N4", "N41A", "HHZ,BDF"
T_START, T_END = "2026-11-25T13:50:00", "2026-11-25T15:20:00"
# QAPP Worksheet 17: midpoint between the two ECMs, UTM 15N 646000 E 4519000 N.
ORIGIN_UTM = (646000.0, 4519000.0)
STA_S, LTA_S, ON, OFF = 1.0, 30.0, 4.0, 1.5
BANDS = {"HHZ": (1.0, 15.0), "BDF": (1.0, 10.0)}


def origin_latlon() -> tuple[float, float]:
    from pyproj import Transformer

    lon, lat = Transformer.from_crs("EPSG:32615", "EPSG:4326", always_xy=True).transform(
        *ORIGIN_UTM)
    return lat, lon


def fetch(store: RawStore | None = None) -> Path | None:
    import io

    from obspy import UTCDateTime
    from obspy.clients.fdsn import Client

    store = store or RawStore()
    st = Client(FDSN).get_waveforms(NET, STA, "*", CHANS, UTCDateTime(T_START),
                                    UTCDateTime(T_END))
    buf = io.BytesIO()
    st.write(buf, format="MSEED")
    stored, _, path = store.save(
        source_id="seismic_fdsn", key=f"{NET}.{STA}", ext="mseed", content=buf.getvalue(),
        fetched_at=datetime.now(UTC),
        manifest={"url": f"{FDSN}/fdsnws/dataselect/1/query", "publisher": "EarthScope FDSN",
                  "tier": "T1", "network": NET, "station": STA, "channels": CHANS,
                  "starttime": T_START, "endtime": T_END,
                  "traces": [str(tr) for tr in st]})
    return path if stored else None


def _latest_mseed(raw_root: Path) -> Path:
    files = sorted((raw_root / "seismic_fdsn").glob("*/*.mseed"))
    if not files:
        raise FileNotFoundError("no stored seismic data; run `konis seismic fetch`")
    return files[-1]


def triggers(raw_root: Path = Path("data/raw")) -> pl.DataFrame:
    import hashlib

    from obspy import read
    from obspy.geodetics import gps2dist_azimuth
    from obspy.signal.trigger import classic_sta_lta, trigger_onset

    path = _latest_mseed(raw_root)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    lat, lon = origin_latlon()
    dist_km = gps2dist_azimuth(lat, lon, 40.708, -90.855)[0] / 1000
    rows = []
    for tr in read(str(path)):
        t = tr.copy()
        t.detrend("demean")
        fmin, fmax = BANDS[t.stats.channel]
        t.filter("bandpass", freqmin=fmin, freqmax=fmax, corners=4, zerophase=True)
        sr = t.stats.sampling_rate
        cft = classic_sta_lta(t.data, int(STA_S * sr), int(LTA_S * sr))
        for a, b in trigger_onset(cft, ON, OFF):
            rows.append({"trace_id": tr.id, "channel": t.stats.channel,
                         "onset_utc": (t.stats.starttime + a / sr).isoformat() + "Z",
                         "peak_sta_lta": round(float(cft[a:b + 1].max()), 2),
                         "distance_km": round(dist_km, 2), "raw_sha256": sha,
                         "raw_file": str(path.relative_to(raw_root)),
                         "parser_version": PARSER_VERSION})
    return pl.DataFrame(rows).sort("onset_utc", "channel")


def summarize(df: pl.DataFrame, sound_speed_range=(0.30, 0.36), p_speed=6.0) -> list[str]:
    """Pairs of strong seismic onsets and infrasound onsets at the predicted delay."""
    def ts(s):
        return datetime.fromisoformat(s.replace("Z", "+00:00").replace("+00:00+00:00", "+00:00"))

    d = df["distance_km"][0]
    out = [f"station N4.N41A, {d:.1f} km from the QAPP ECM midpoint"]
    for label, lo, hi in (("14:00 UTC (09:00 ET)", "13:55", "14:10"),
                          ("15:00 UTC (09:00 CST)", "14:55", "15:10")):
        w = df.filter(pl.col("onset_utc").str.slice(11, 5).is_between(pl.lit(lo), pl.lit(hi), closed="left"))
        seis = w.filter((pl.col("channel") == "HHZ") & (pl.col("peak_sta_lta") >= 10))
        out.append(f"{label}: {len(w.filter(pl.col('channel') == 'HHZ'))} seismic onsets, "
                   f"{len(seis)} strong (STA/LTA >= 10)")
        for r in seis.iter_rows(named=True):
            t0 = ts(r["onset_utc"]).timestamp() - d / p_speed
            for i in df.filter(pl.col("channel") == "BDF").iter_rows(named=True):
                dt = ts(i["onset_utc"]).timestamp() - t0
                if dt > 0 and sound_speed_range[0] <= d / dt <= sound_speed_range[1]:
                    out.append(
                        f"  seismic {r['onset_utc'][11:22]} (r{r['peak_sta_lta']:.0f}) -> "
                        f"implied T0 {datetime.fromtimestamp(t0, UTC).isoformat()[11:19]} UTC; "
                        f"infrasound {i['onset_utc'][11:22]} (r{i['peak_sta_lta']:.0f}), "
                        f"implied sound speed {d / dt:.3f} km/s")
    return out
