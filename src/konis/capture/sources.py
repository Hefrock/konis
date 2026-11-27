"""Registry of Stage 0 capture sources.

Tiers (adapted from ilara I4):
  T1  official primary: EPA, U.S. Army, state agencies, NOAA/NWS, FAA ASOS archives
  T2  peer-reviewed literature
  T3  news / third-party maps: for locating sources and sanity checks only
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from konis import config

EPA_ARCGIS = "https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services"


@dataclass(frozen=True)
class Source:
    source_id: str
    kind: str  # page | file | arcgis_layer | arcgis_item | json | csv | airnow_hourly
    url: str
    tier: str = "T1"
    publisher: str = ""
    ext: str = "html"
    min_bytes: int = 500
    # page: at least one of these (case-insensitive) must appear, else the capture is "empty"
    must_contain: tuple[str, ...] = ()
    note: str = ""
    params: dict = field(default_factory=dict)


SOURCES: tuple[Source, ...] = (
    # --- Official GIS (EPA Region 7 response viewer; owner org "U.S. EPA") ---
    Source("epa_xact_metals", "arcgis_layer",
           f"{EPA_ARCGIS}/IAAAP_Xact_Data_Public_Viewer/FeatureServer/0",
           publisher="EPA Region 7", ext="json",
           note="Xact XRF real-time metals monitor results (elemental, not optical PM)"),
    Source("epa_air_stations", "arcgis_layer",
           f"{EPA_ARCGIS}/Air_Sampling_and_Monitoring_Location/FeatureServer/0",
           publisher="EPA Region 7", ext="json",
           note="Air sampling / monitoring station locations and instrument types"),
    Source("epa_viewer_webmap", "arcgis_item",
           "https://www.arcgis.com/sharing/rest/content/items/55521a18cb4849089d04c8575b5f8ccb",
           publisher="EPA Region 7", ext="json",
           note="Web map behind the public viewer; watched for added/removed layers"),
    Source("epa_viewer_experience", "arcgis_item",
           "https://www.arcgis.com/sharing/rest/content/items/1ddcf8b9d8314971b00dac8893ae9cd6",
           publisher="EPA Region 7", ext="json",
           note="IAAAP Response Data Viewer (ArcGIS Experience) config"),
    # --- Official pages ---
    Source("epa_osc_site", "page",
           "https://response.epa.gov/site/site_profile.aspx?site_id=17211",
           publisher="EPA On-Scene Coordinator", must_contain=("iowa", "ammunition")),
    Source("epa_osc_documents", "page",
           "https://response.epa.gov/site/doc_list.aspx?site_id=17211",
           publisher="EPA On-Scene Coordinator", must_contain=("document",),
           note="Document list for the IAAAP response; links harvested (ADR 0008)"),
    Source("epa_news_initial_air", "page",
           "https://www.epa.gov/newsreleases/initial-air-monitoring-shows-zero-detection-"
           "airborne-lead-following-controlled",
           publisher="EPA", must_contain=("lead",)),
    Source("iepa_updates", "page", "https://epa.illinois.gov/iowa-plant-updates.html",
           publisher="Illinois EPA", must_contain=("lead",)),
    Source("iowa_hsemd_resources", "page",
           "https://homelandsecurity.iowa.gov/iowa-army-munitions-disposition-resources",
           publisher="Iowa HSEMD", must_contain=("lead", "army")),
    Source("iowa_hhs_lead", "page",
           "https://hhs.iowa.gov/health-prevention/environmental-health/lead-exposure-surveillance",
           publisher="Iowa HHS", must_contain=("lead",)),
    *(
        Source(f"army_article_{n}", "page", f"https://www.army.mil/article/{n}",
               publisher="U.S. Army", must_contain=("lead", "ammunition"))
        for n in (297039, 297076, 297078, 297079, 297080)
    ),
    *(
        Source(f"iepa_pdf_{n}", "file", f"https://d34w7g4gy10iej.cloudfront.net/pubs/pdf_{n}.pdf",
               publisher="Illinois EPA", ext="pdf", min_bytes=1000,
               note="PDF linked from the Illinois EPA updates page")
        for n in (77827, 78382)
    ),
    # --- U.S. Army Sustainment Command: update page (maps, advisories, EA; ADR 0013) ---
    Source("army_asc_updates", "page", "https://www.army.mil/asc", publisher="U.S. Army ASC",
           must_contain=("lead azide",),
           note="Army update page; links the advisories, Environmental Assessment and maps"),
    # --- Missouri (plume forecast to drift south-west into Missouri; ADR 0013) ---
    Source("mo_dnr_detonation", "page", "https://dnr.mo.gov/iowa-lead-azide-detonation",
           publisher="Missouri DNR", must_contain=("lead",)),
    *(
        Source(f"mo_governor_{sid}", "page",
               f"https://governor.mo.gov/press-releases/archive/{slug}",
               publisher="Missouri Governor's Office", must_contain=("lead", "army"))
        for sid, slug in (
            ("post_detonation", "governor-kehoes-statement-following-detonation-iowa-army-"
             "ammunition-plant"),
            ("new_details", "state-missouri-shares-new-details-planned-detonation-iowa-army-"
             "ammunition"),
            ("public_animal_health", "state-missouri-acting-ensure-public-and-animal-health-"
             "preparation-us-armys"),
            ("seoc_activation", "governor-kehoe-activates-state-emergency-operation-center-"
             "preparation"),
        )
    ),
    # --- Meteorology ---
    Source("metar_awc", "json",
           "https://aviationweather.gov/api/data/metar",
           publisher="NOAA Aviation Weather Center", ext="json", min_bytes=50,
           params={"ids": ",".join(config.METAR_STATIONS), "format": "json", "hours": "3"}),
    # --- Air quality: regulatory monitors, no API key (files product) ---
    Source("airnow_hourly", "airnow_hourly",
           "https://files.airnowtech.org/airnow",
           publisher="EPA AirNow (preliminary, unvalidated)", ext="dat", min_bytes=0,
           note="Hourly files clipped to BBOX; see ADR 0002"),
)


def iem_asos_url(day: datetime) -> tuple[str, dict]:
    """IEM ASOS archive request for one UTC day across all study stations."""
    nxt = day + timedelta(days=1)
    params = {
        "station": list(config.IEM_ASOS_STATIONS),
        "data": "all",
        "year1": day.year, "month1": day.month, "day1": day.day,
        "year2": nxt.year, "month2": nxt.month, "day2": nxt.day,
        "tz": "Etc/UTC", "format": "onlycomma", "latlon": "yes", "elev": "yes",
        "missing": "empty", "trace": "T", "direct": "no", "report_type": ["3", "4"],
    }
    return "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py", params


def by_id(source_id: str) -> Source:
    for s in SOURCES:
        if s.source_id == source_id:
            return s
    raise KeyError(source_id)
