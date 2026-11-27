# konis (*κόνις*, "fine dust")

An independent public archive of the official information and environmental data published
about the controlled detonation of degraded lead azide at the Iowa Army Ammunition Plant
(Middletown, Iowa) on 25 November 2026.

> **Unofficial and independent.** This is not public health or medical advice, and it is not
> affiliated with or endorsed by the EPA, the U.S. Army, or any state agency. For official
> information and guidance, go to:
> [EPA response site](https://response.epa.gov/site/site_profile.aspx?site_id=17211) ·
> [U.S. Army (ASC)](https://www.army.mil/asc) ·
> [Iowa HSEMD](https://homelandsecurity.iowa.gov/iowa-army-munitions-disposition-resources) ·
> [Iowa HHS](https://hhs.iowa.gov/health-prevention/environmental-health/lead-exposure-surveillance) ·
> [Illinois EPA](https://epa.illinois.gov/iowa-plant-updates.html) ·
> [Missouri DNR](https://dnr.mo.gov/iowa-lead-azide-detonation)

## Why this exists

Agencies publish updates about an event like this on web pages and maps that show only the
latest version. When a page changes, the earlier version is usually gone. konis keeps every
version, so anyone can later check what was known, and when.

## What it collects

About once an hour, konis saves a copy of:

- **Official pages and documents** from the EPA, the U.S. Army, and state agencies in Iowa,
  Illinois and Missouri, including the PDFs they link to (sampling plans, permits, advisories,
  the Army's Environmental Assessment).
- **EPA's real-time airborne lead readings** from four "Xact" monitors placed south-west of the
  plant, the direction the wind was forecast to carry dust.
- **Regulatory air-quality monitors** (AirNow) and **airport weather** (Burlington and nearby).

Each saved copy is stored exactly as received, with a fingerprint (a SHA-256 hash) that shows
it has not been altered since. Nothing is filled in or smoothed: a gap stays a gap.

## What it has found so far (as of 27 November 2026)

- **Detonation time.** About 9:00 a.m. CST on 25 November (15:00 UTC), as the Army states. A
  public seismometer and microphone 37 km away recorded ground motion at 15:00:38 UTC and the
  air-pressure wave 104 seconds later, consistent with that time. Earlier Army advisories had
  announced the detonation for 20 November at noon.
- **Airborne lead (EPA Xact monitors).** Most readings are reported as 0. A few are small
  positive values; the highest so far is about 0.01 µg/m³. For comparison, the short-term
  screening level cited on EPA's map is 32 µg/m³. Two cautions:
  - EPA's public map rounds to one decimal place, so these small values appear there as "0.0".
  - EPA has not published the detection limit for these monitors, so a reported 0 cannot be
    read as "no lead", and a small positive value is not a confirmed detection.
- **Army deposition model.** Before the detonation, the Army modelled lead settling on surfaces
  above EPA's floor-dust level (5 µg/ft²) over about 148 square miles, and above the
  window-sill level (100 µg/ft²) over about 27 square miles, in a band running south-west. This
  is a model, not a measurement. EPA's soil and surface sampling results are what will show
  what actually settled; konis is watching for them.
- **What these monitors cannot tell us.** All four lead monitors sit on one line in the
  direction the wind blew that day, so there is no "not downwind" monitor to compare against.
  The regular particle monitors in the region measure dust, not lead, and none is in the
  direction the plume was expected to travel.

Full write-ups: [`docs/results/`](docs/results/). What went wrong and what it taught:
[`docs/lessons.md`](docs/lessons.md).

## Using the data

Everything is in this repository:

- [`data/raw/`](data/raw/): every captured page, file and data layer, as received.
- [`data/curated/`](data/curated/): tidy tables rebuilt from the raw files (lead readings,
  air quality, weather, capture health). Every row says which raw file it came from.
- [`data/seed/`](data/seed/): the few figures copied by hand from documents (for example the
  Army model areas), each citing its source file and page.
- **Weekly releases** (`data-YYYY-MM-DD`, on the
  [releases page](https://github.com/Hefrock/konis/releases)) are fixed snapshots to cite: each
  has the tables as a zip and a list of every archived file with its fingerprint.
- Documents too large for the repository (the EPA sampling plan and permit application) are
  attached to the [`docs-archive`](https://github.com/Hefrock/konis/releases/tag/docs-archive)
  release.

## What konis does not do

- It does not measure anything itself, and it does not estimate anyone's exposure or risk.
- It does not replace official results. EPA and state laboratory results for air filters,
  soil, dust wipes and water are the evidence that matters; konis archives them when published.

## License

Code: [MIT](LICENSE). konis's own tables, notes and reports: [CC BY 4.0](LICENSE-DATA.md).
The archived pages, documents and data files are copies of other organizations' publications
and stay under their publishers' terms; see [LICENSE-DATA.md](LICENSE-DATA.md).

## For developers

How the pipeline works, how to run it, and the rules it follows are in
[`CLAUDE.md`](CLAUDE.md). Design decisions are recorded in [`docs/adr/`](docs/adr/), sources in
[`docs/sources.md`](docs/sources.md), and progress in [`docs/PROGRESS.md`](docs/PROGRESS.md).
