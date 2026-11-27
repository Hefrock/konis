"""Static public status page (ADR 0016): `konis site build --out site`.

Reads only curated tables, seed files and raw manifests (K3); writes one self-contained HTML
file. No interpretation beyond what the README and ADRs already state.
"""

from __future__ import annotations

import csv
import html
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

REPO = "https://github.com/Hefrock/konis"
BLOB = f"{REPO}/blob/main"
HOST_LABELS = {"d34w7g4gy10iej.cloudfront.net": "Illinois EPA document server",
               "response.epa.gov": "EPA response site", "www.gsa.gov": "GSA"}


def _rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s)


def _e(s) -> str:
    return html.escape(str(s))


# ----------------------------------------------------------------------------- data

def xact(curated: Path) -> dict[str, list[dict]]:
    from konis.geo import haversine_km
    origin = (40.80903, -91.26903)
    out: dict[str, list[dict]] = {}
    for r in _rows(curated / "xact_lead.csv"):
        if r["superseded_at_utc"] or r["removed_at_utc"]:
            continue
        out.setdefault(r["station_id"], []).append({
            "t": _ts(r["observed_at_utc"]), "v": float(r["value_reported"]),
            "zero": r["reported_zero"] == "true",
            "km": haversine_km(*origin, float(r["latitude"]), float(r["longitude"]))})
    for v in out.values():
        v.sort(key=lambda r: r["t"])
    return dict(sorted(out.items(), key=lambda kv: kv[1][0]["km"]))


def health(curated: Path) -> tuple[str | None, list[dict]]:
    rows = _rows(curated / "ingestion_health.csv")
    if not rows:
        return None, []
    last_day = max(r["date_utc"] for r in rows)
    today = [r for r in rows if r["date_utc"] == last_day]
    return last_day, sorted(today, key=lambda r: (int(r["runs_failed"]) == 0, r["source_id"]))


def latest_capture(raw: Path) -> str | None:
    best = None
    for f in raw.glob("*/_latest.json"):
        for v in json.loads(f.read_text()).values():
            t = v.get("fetched_at_utc") or (v.get("state") or {}).get("last_checked_utc")
            if t and (best is None or t > best):
                best = t
    return best


def documents(raw: Path) -> list[dict]:
    docs: dict[str, dict] = {}
    for m in (raw / "linked_docs").glob("*/*.manifest.json"):
        man = json.loads(m.read_text())
        url = man.get("url", "")
        prev = docs.get(url)
        if prev is None or man["fetched_at_utc"] > prev["fetched_at_utc"]:
            ext = (man.get("external") or {}).get("asset_name")
            archived = (f"{REPO}/releases/download/docs-archive/{ext}" if ext else
                        f"{BLOB}/{m.parent.relative_to(raw.parent.parent)}/{man['file']}")
            docs[url] = {"url": url, "fetched_at_utc": man["fetched_at_utc"],
                         "publisher": HOST_LABELS.get(urlparse(url).hostname or "", urlparse(url).hostname or ""), "archived": archived,
                         "name": unquote(url.rsplit("/", 1)[-1]).replace("_", " ")}
    return sorted(docs.values(), key=lambda d: d["fetched_at_utc"], reverse=True)


# ----------------------------------------------------------------------------- chart

def panel(station: str, km: float, pts: list[dict], t0: datetime, t1: datetime,
          vmax: float) -> str:
    """One small multiple: stems from the zero baseline, a dot per reading."""
    w, h, pl, pr, pt, pb = 320, 150, 44, 10, 26, 26
    span = (t1 - t0).total_seconds() or 1

    def x(t):
        return pl + (t - t0).total_seconds() / span * (w - pl - pr)

    def y(v):
        return h - pb - v / vmax * (h - pt - pb)

    nz = sum(1 for p in pts if not p["zero"])
    el = [(f'<figure class="panel"><svg viewBox="0 0 {w} {h}" role="img" '
          f'aria-label="{_e(station)}: {len(pts)} readings, {nz} reported above zero">'),
          f'<text x="{pl}" y="16" class="ptitle">{_e(station)} · {km:.0f} km</text>',
          f'<line x1="{pl}" y1="{y(0)}" x2="{w - pr}" y2="{y(0)}" class="axis"/>']
    for frac in (0.5, 1.0):
        v = vmax * frac
        el.append(f'<line x1="{pl}" y1="{y(v):.1f}" x2="{w - pr}" y2="{y(v):.1f}" class="grid"/>'
                  f'<text x="{pl - 4}" y="{y(v) + 3:.1f}" class="tick" text-anchor="end">'
                  f'{v:.3f}</text>')
    el.append(f'<text x="{pl - 4}" y="{y(0) + 3:.1f}" class="tick" text-anchor="end">0</text>')
    for p in pts:
        cx, cy = x(p["t"]), y(p["v"])
        tip = (f'{p["t"].strftime("%d %b %H:%M")} UTC: '
               + ("reported 0" if p["zero"] else f'{p["v"]:.4f} µg/m³'))
        if p["zero"]:
            el.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="1.6" class="zero">'
                      f'<title>{_e(tip)}</title></circle>')
        else:
            el.append(f'<line x1="{cx:.1f}" y1="{y(0):.1f}" x2="{cx:.1f}" y2="{cy:.1f}" '
                      f'class="stem"/><circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" class="dot">'
                      f'<title>{_e(tip)}</title></circle>')
    el.append(f'<text x="{pl}" y="{h - 6}" class="tick">{t0:%d %b}</text>'
              f'<text x="{w - pr}" y="{h - 6}" class="tick" text-anchor="end">{t1:%d %b}</text>')
    el.append("</svg>")
    el.append(f'<figcaption>{len(pts)} readings · {nz} above zero · max '
              f'{max(p["v"] for p in pts):.4f} µg/m³</figcaption></figure>')
    return "".join(el)


# ----------------------------------------------------------------------------- page

CSS = """
:root{--bg:#ffffff;--text:#191919;--muted:#666666;--rule:#e2e2e2;--series:#257de0;
--zero:#b0b0b0;--card:#f7f7f7;--warn:#9a5b00}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#191919;--text:#efefef;
--muted:#9c9c9c;--rule:#383838;--series:#338ced;--zero:#5c5c5c;--card:#222222;--warn:#fbb315}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);
font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:980px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:1.7rem;margin:0 0 4px}h2{font-size:1.2rem;margin:36px 0 8px;
border-top:1px solid var(--rule);padding-top:20px}
.muted{color:var(--muted)}.note{background:var(--card);border-left:3px solid var(--muted);
padding:10px 14px;margin:14px 0;border-radius:4px}
a{color:var(--series)}.grid4{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));
gap:12px}.panel{margin:0;background:var(--card);border-radius:6px;padding:6px}
.panel svg{width:100%;height:auto;display:block}.panel figcaption{font-size:.82rem;
color:var(--muted);padding:0 6px 4px}
.ptitle{font-size:12px;fill:var(--text);font-weight:600}.tick{font-size:10px;fill:var(--muted)}
.axis{stroke:var(--muted);stroke-width:1}.grid{stroke:var(--rule);stroke-width:1}
.dot{fill:var(--series);stroke:var(--card);stroke-width:2}.stem{stroke:var(--series);stroke-width:2}
.zero{fill:var(--zero)}
table{border-collapse:collapse;width:100%;font-size:.9rem}td,th{text-align:left;
padding:5px 8px;border-bottom:1px solid var(--rule);vertical-align:top;overflow-wrap:anywhere}
details summary{cursor:pointer;color:var(--series);margin:8px 0}
.tablewrap{overflow-x:auto}.fail{color:var(--warn);font-weight:600}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.fact{background:var(--card);border-radius:6px;padding:12px}.fact b{display:block;font-size:1.25rem}
"""


def build(out: Path, root: Path = Path(".")) -> Path:
    curated, raw = root / "data/curated", root / "data/raw"
    xs = xact(curated)
    allp = [p for v in xs.values() for p in v]
    vmax = max([0.005] + [p["v"] for p in allp]) * 1.1
    t0 = min((p["t"] for p in allp), default=datetime.now(UTC))
    t1 = max((p["t"] for p in allp), default=datetime.now(UTC))
    day, hrows = health(curated)
    latest = latest_capture(raw)
    docs = documents(raw)
    seed = _rows(root / "data/seed/army_model_20261124.csv")
    area = {r["quantity"]: r["value"] for r in seed}
    built = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    panels = "".join(panel(s, v[0]["km"], v, t0, t1, vmax) for s, v in xs.items())
    failing = [r for r in hrows if int(r["runs_failed"]) > 0]
    hlist = "".join(
        f'<tr><td>{_e(r["source_id"])}</td><td>{r["runs_ok"]}/{r["runs"]}</td>'
        f'<td class="{"fail" if int(r["runs_failed"]) else ""}">'
        f'{_e(r["last_failure_detail"] or "")}</td></tr>' for r in hrows)
    flist = ("" if not failing else
             '<div class="tablewrap"><table><tr><th>Source</th><th>Runs ok</th>'
             '<th>Last failure</th></tr>' + "".join(
                 f'<tr><td>{_e(r["source_id"])}</td><td>{r["runs_ok"]}/{r["runs"]}</td>'
                 f'<td class="fail">{_e(r["last_failure_detail"])}</td></tr>' for r in failing)
             + "</table></div>")
    dlist = "".join(
        f'<tr><td><a href="{_e(d["url"])}">{_e(d["name"])}</a></td>'
        f'<td>{_e(d["publisher"])}</td><td>{_e(d["fetched_at_utc"][:16].replace("T", " "))}</td>'
        f'<td><a href="{_e(d["archived"])}">archived copy</a></td></tr>' for d in docs)

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>konis status</title><style>{CSS}</style></head><body><main>
<h1>konis: archive status</h1>
<p class="muted">Independent archive of public data on the 25 November 2026 lead azide
detonation at the Iowa Army Ammunition Plant. Page built {built}.</p>
<div class="note"><b>Unofficial and independent.</b> Not public health or medical advice; not
affiliated with the EPA, the U.S. Army or any state agency. Official information:
<a href="https://response.epa.gov/site/site_profile.aspx?site_id=17211">EPA</a> ·
<a href="https://www.army.mil/asc">U.S. Army</a> ·
<a href="https://homelandsecurity.iowa.gov/iowa-army-munitions-disposition-resources">Iowa HSEMD</a> ·
<a href="https://hhs.iowa.gov/health-prevention/environmental-health/lead-exposure-surveillance">Iowa HHS</a> ·
<a href="https://epa.illinois.gov/iowa-plant-updates.html">Illinois EPA</a> ·
<a href="https://dnr.mo.gov/iowa-lead-azide-detonation">Missouri DNR</a></div>

<div class="facts">
<div class="fact"><span class="muted">Detonation</span><b>25 Nov, ~9:00 a.m. CST</b>
<span class="muted">Army statement; seismic record agrees</span></div>
<div class="fact"><span class="muted">Latest capture</span><b>{_e((latest or "none")[:16].replace("T", " "))} UTC</b>
<span class="muted">about hourly</span></div>
<div class="fact"><span class="muted">Army model, ≥ 5 µg/ft² (floors)</span>
<b>{_e(area.get("surface_deposition_area_ge_5_ug_ft2", "?"))} sq mi</b>
<span class="muted">modelled before the event, not measured</span></div>
<div class="fact"><span class="muted">Army model, ≥ 100 µg/ft² (window sills)</span>
<b>{_e(area.get("surface_deposition_area_ge_100_ug_ft2", "?"))} sq mi</b>
<span class="muted">same model</span></div>
</div>

<h2>Airborne lead, EPA Xact monitors</h2>
<p>Each panel is one monitor, nearest the plant first; all four lie south-west of it.
Grey points are readings EPA reported as 0; blue stems are readings reported above 0
(hover for the value). For scale, the short-term screening level cited on EPA's map is
32 µg/m³, thousands of times higher than the top of these axes.</p>
<div class="grid4">{panels}</div>
<p class="muted">EPA has not published these monitors' detection limit, so a reported 0 is not
"no lead" and a small positive value is not a confirmed detection. EPA's own map rounds to one
decimal place and shows these values as 0.0. Data table:
<a href="{BLOB}/data/curated/xact_lead.csv">xact_lead.csv</a>.</p>

<h2>Capture health{f", {day}" if day else ""}</h2>
<p>{"All sources captured in every run so far today." if not failing else
f"{len(failing)} source(s) had at least one failed run today; a single failure is usually a "
"temporary website error and is retried next run."}</p>
{flist}
<details><summary>All {len(hrows)} sources</summary><div class="tablewrap"><table>
<tr><th>Source</th><th>Runs ok</th><th>Last failure</th></tr>{hlist}</table></div></details>

<h2>Archived official documents</h2>
<p>Newest first. Each links to the publisher's copy and to konis's archived copy, which stays
available if the publisher's link changes.</p>
<div class="tablewrap"><table><tr><th>Document</th><th>Publisher</th><th>Latest version archived (UTC)</th>
<th></th></tr>{dlist}</table></div>

<h2>More</h2>
<p><a href="{REPO}">Repository and README</a> ·
<a href="{REPO}/releases">Weekly data releases</a> ·
<a href="{BLOB}/docs/lessons.md">Lessons</a> ·
<a href="{REPO}/tree/main/docs/results">Analysis reports</a> ·
<a href="{BLOB}/LICENSE-DATA.md">Data license</a></p>
</main></body></html>
"""
    out.mkdir(parents=True, exist_ok=True)
    p = out / "index.html"
    p.write_text(page)
    return p
