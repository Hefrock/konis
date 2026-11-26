# ADR 0008: Harvest documents linked from official pages

Status: accepted (26 Nov 2026).

Problem: laboratory results, sampling plans and permits are published as PDFs and spreadsheets
linked from the pages konis captures. Saving the page keeps the link, not the document; if an
agency replaces a file at the same URL, the earlier version is lost.

Decision
- After page sources are captured, `konis.capture.harvest` reads the latest stored copy of
  each page source, collects links ending in .pdf .xlsx .xls .csv .docx .doc .zip .pptx, and
  follows only official hosts (`*.gov`, `*.mil`, the Illinois EPA document CDN). Depth 1:
  documents are never crawled further. The EPA OSC document list page is a page source so
  its links are harvested too.
- Each document is source `linked_docs`, keyed by host, file name and a hash of the URL. The
  manifest records the parent page (`parent_source_id`, `parent_url`, `parent_raw_sha256`).
- New links are fetched in the run that finds them; known documents are re-checked every 6 h
  with conditional GET (ETag / Last-Modified), so unchanged files are not downloaded again.
  At most 60 documents are fetched per run. A link that ends in .pdf but serves HTML fails as
  `empty`; a 404 fails as `error` (document moved or withdrawn) and alerts.
- Documents over 9 MB are kept out of git. Their bytes go to `data/_external_staging/`
  (gitignored) and the workflow uploads them as assets of the GitHub release `docs-archive`
  before committing. The asset name starts with the first 16 hex digits of the sha256; the
  committed manifest carries `external.release_tag` and `external.asset_name`. If an upload
  fails, the job stops before the commit, so no manifest points to a missing asset.
- Credential redaction (ADR 0004) applies to documents too; any redaction is in the manifest.

First run (26 Nov): 18 documents found on 3 official domains; 3 over 9 MB (EPA QAPP, 78 MB;
permit application, 191 MB; Illinois children's lead booklet, 12 MB).

Note: EPA marks pages of the posted, redacted permit documents "CUI". They are archived
because EPA published them on its public response site; konis does not alter them.
