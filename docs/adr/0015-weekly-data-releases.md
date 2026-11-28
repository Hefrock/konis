# ADR 0015: Weekly tagged data releases

Status: accepted (27 Nov 2026).

A git history is not a citable, fixed snapshot. Each week (Mondays 06:23 UTC, or by hand) the
`release-weekly` workflow tags `main` as `data-YYYY-MM-DD` and publishes a GitHub release with:

- `konis-<tag>.zip`: `data/curated`, `data/seed`, `data/reference`, `docs/results`,
  `LICENSE-DATA.md` and `MANIFEST.csv` (built deterministically: same content, same bytes);
- `MANIFEST.csv`: every raw capture with path, sha256, bytes, source, URL, publisher, tier,
  fetch time, and the `docs-archive` asset name for files kept outside git;
- release notes with counts and freshness only, no interpretation.

The raw files are in the source archive GitHub attaches to every release; they are not
duplicated as an asset (repository growth, ADR 0005). The workflow is idempotent (skips an
existing tag) and shares the `ingest-live` concurrency group so it never tags mid-commit.

Citation and DOI: `CITATION.cff` describes the dataset. If the owner enables the repository in
Zenodo's GitHub integration, each published release is archived there with a DOI. That is an
owner action (Zenodo account), not automated here.

Known limit: GitHub's scheduler has been unreliable for this repository (CLAUDE.md,
Operations). A missed Monday is recovered by running the workflow by hand; the date in the tag
is the day it actually ran.

## Amendment (28 Nov 2026)

Before building, the release job runs `konis verify` against the `docs-archive` asset
listing. Any raw file or asset that does not match its manifest stops the release.
