"""Fixed event facts, study area and reference constants.

Values here are definitions. Changing one after post-event data have been seen must be
recorded in an ADR and applied going forward only (see docs/adr/0001).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

REPO_URL = "https://github.com/hefrock/konis"
USER_AGENT = f"konis-capture/0.1 (+{REPO_URL})"

# Event
IAAAP_LAT = 40.7906
IAAAP_LON = -91.2447
DETONATION_UTC = datetime(2026, 11, 25, 15, 0, tzinfo=UTC)

# Study area: SE Iowa, NE Missouri, W Illinois (lon_min, lat_min, lon_max, lat_max)
BBOX = (-93.5, 39.5, -89.0, 42.0)

METAR_STATIONS = ("KBRL", "KMLI", "KOTM", "KIRK", "KUIN")
# Iowa Environmental Mesonet ASOS ids (no K prefix), archive back-fill source
IEM_ASOS_STATIONS = ("BRL", "MLI", "OTM", "IRK", "UIN")

# Reference constants (context only; PM monitors cannot be compared against the Pb NAAQS)
PB_NAAQS_UG_M3_3MO = 0.15
DEPOSITION_LOW_UG_FT2 = 5.0
DEPOSITION_ELEVATED_UG_FT2 = 100.0
CDC_BLRV_UG_DL = 3.5  # no safe blood lead level has been identified

# Polite access (ilara I7): minimum seconds between requests to one host
MIN_SECONDS_PER_HOST = 5.0
HTTP_TIMEOUT = 60

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
LOG_DIR = DATA_DIR / "capture_log"
