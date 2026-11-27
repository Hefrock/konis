# ADR 0016: Public status page on GitHub Pages

Status: accepted (27 Nov 2026).

Instead of the Streamlit dashboard in the original brief, konis publishes one static page
(`konis site build`, `src/konis/site.py`), deployed to GitHub Pages by `.github/workflows/site.yml`
after every `ingest-live` run and on demand. No server, no JavaScript, nothing to host.

Content, all from curated tables, seed files and raw manifests (K3), no new interpretation:
- disclaimer and official links (same as the README);
- key facts: detonation time, latest capture, Army model areas (labelled "modelled, not measured");
- EPA Xact readings as four small multiples, one per monitor ordered by distance; reported 0s
  in grey, positive readings as blue stems (dataviz default series blue, light #257de0 / dark
  #338ced; single series per panel, so no legend); value tooltips via SVG <title>; a link to
  the CSV as the table view; caveats on detection limit and EPA map rounding beside the charts;
- capture health for the latest day, failures first, full list collapsed;
- archived official documents, newest first, each with the publisher link and the archived copy.

Checked by screenshot in light and dark schemes and at 390 px width (no horizontal scroll).

One-time owner action: Settings -> Pages -> Source "GitHub Actions". Until then the workflow fails
at the deploy step and the page is not published.
