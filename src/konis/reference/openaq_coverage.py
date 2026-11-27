"""One-off check: which OpenAQ locations exist near the IAAAP site? (no data download)

Reads OPENAQ_API_KEY from the environment (a GitHub Actions secret); the key is never
written anywhere. Writes data/reference/openaq_locations.csv: one row per location within
RADIUS_KM of the QAPP origin, with provider, whether it is a monitor or a low-cost sensor,
pollutants, first/last reported times, distance and bearing from the origin.
"""

from __future__ import annotations

import csv
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import requests

from konis import config
from konis.analysis.xact_wind import ORIGIN
from konis.geo import bearing_deg, haversine_km

API = "https://api.openaq.org/v3/locations"
RADIUS_KM = 50.0
# ~0.75 deg lat x 1.0 deg lon box around the origin, filtered to RADIUS_KM afterwards
BBOX = (ORIGIN[1] - 0.7, ORIGIN[0] - 0.5, ORIGIN[1] + 0.7, ORIGIN[0] + 0.5)
OUT = Path("data/reference/openaq_locations.csv")


def fetch(key: str) -> list[dict]:
    s = requests.Session()
    s.headers.update({"X-API-Key": key, "User-Agent": config.USER_AGENT})
    out, page = [], 1
    while True:
        r = s.get(API, params={"bbox": ",".join(f"{v:.4f}" for v in BBOX), "limit": 1000,
                               "page": page}, timeout=60)
        if r.status_code in (401, 403):
            sys.exit(f"OpenAQ refused the key (HTTP {r.status_code})")
        r.raise_for_status()
        res = r.json().get("results", [])
        out += res
        if len(res) < 1000:
            return out
        page += 1
        time.sleep(2)


def rows(locs: list[dict]) -> list[dict]:
    out = []
    for loc in locs:
        c = loc.get("coordinates") or {}
        lat, lon = c.get("latitude"), c.get("longitude")
        if lat is None or lon is None:
            continue
        d = haversine_km(*ORIGIN, lat, lon)
        if d > RADIUS_KM:
            continue
        params = sorted({(s.get("parameter") or {}).get("name", "") for s in loc.get("sensors", [])})
        out.append({
            "openaq_id": loc.get("id"), "name": loc.get("name"),
            "provider": (loc.get("provider") or {}).get("name"),
            "owner": (loc.get("owner") or {}).get("name"),
            "is_monitor": loc.get("isMonitor"), "is_mobile": loc.get("isMobile"),
            "parameters": ";".join(p for p in params if p),
            "first_utc": (loc.get("datetimeFirst") or {}).get("utc"),
            "last_utc": (loc.get("datetimeLast") or {}).get("utc"),
            "latitude": lat, "longitude": lon, "distance_km": round(d, 1),
            "bearing_deg": round(bearing_deg(*ORIGIN, lat, lon), 0),
        })
    return sorted(out, key=lambda r: r["distance_km"])


def main() -> int:
    key = os.environ.get("OPENAQ_API_KEY")
    if not key:
        sys.exit("OPENAQ_API_KEY is not set")
    rs = rows(fetch(key))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = ["openaq_id", "name", "provider", "owner", "is_monitor", "is_mobile", "parameters",
              "first_utc", "last_utc", "latitude", "longitude", "distance_km", "bearing_deg"]
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rs)
    now = datetime.now(UTC).isoformat()
    print(f"{len(rs)} OpenAQ locations within {RADIUS_KM:.0f} km (checked {now})")
    for r in rs:
        print(f"  {r['distance_km']:5.1f} km {r['bearing_deg']:5.0f}°  monitor={r['is_monitor']}"
              f"  {r['provider']}  {r['name']}  [{r['parameters']}]  last {r['last_utc']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
