# ADR 0013: Missouri sources, the Army ASC update page, and the agency detonation time

Status: accepted (27 Nov 2026).

## Why
The Army forecast the plume to drift south-west into northern Missouri, but konis archived no
Missouri source. The Army's Sustainment Command page (army.mil/asc) is where the Army posts its
advisories, deposition maps and the Environmental Assessment.

## Added page sources (T1)
- `army_asc_updates`: https://www.army.mil/asc
- `mo_dnr_detonation`: https://dnr.mo.gov/iowa-lead-azide-detonation
- `mo_governor_post_detonation`, `mo_governor_new_details`, `mo_governor_public_animal_health`,
  `mo_governor_seoc_activation`: Missouri Governor's Office press releases.

The linked-document harvester (ADR 0008) follows their document links. On 27 Nov the ASC page
linked four Illinois-EPA-CDN PDFs not yet archived: two pre-event advisories (pdf_78347,
pdf_78366), the Army Environmental Assessment IAAAP-EA-2026-01 (pdf_78364, 41 pages), and Army
claims information (pdf_78387).

Not added: two ArcGIS Experiences linked from the Missouri DNR page are general MoDNR viewers
(solid waste; park status), not event data. A MoDNR web map linked there is not public.

## Detonation time from a T1 source
The ASC page states: "Detonation at IAAAP on Wednesday, Nov. 25, 2026, approximately 9:00 a.m.
CST". The Missouri DNR page gives "about 9 a.m." This agrees with the seismic/infrasound estimate
of ADR 0011 (15:00:32 UTC). The working T0 stays 15:00:32 UTC ± 10 s, now supported by an agency
statement at minute precision and the seismic estimate at second precision.

## Note on revisions
The pre-event advisories archived from the ASC page give the planned detonation as "Nov. 20 at
approximately noon". The event happened on 25 Nov at about 09:00 CST. Both versions are kept.
