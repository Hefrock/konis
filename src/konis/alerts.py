"""GitHub Issue alerts for capture failures (ilara lessons 1-2).

One open issue per failing source, labelled `capture-failure` (ADR 0014):
- an issue opens only when a source has failed in this run AND in its previous run;
- while it is open, further failures add nothing (no comment per run);
- it closes only after two consecutive successful runs.
A single failed run is recorded in the capture log and the ingestion-health table only.
Uses the `gh` CLI, present on GitHub-hosted runners (GITHUB_TOKEN with issues: write).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

LABEL = "capture-failure"


def _gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def _open_issues() -> dict[str, int]:
    out = _gh("issue", "list", "--label", LABEL, "--state", "open", "--limit", "200",
              "--json", "number,title")
    return {i["title"]: i["number"] for i in json.loads(out or "[]")}


def previous_status(source_id: str, run_id: str,
                    log_root: Path = Path("data/capture_log")) -> bool | None:
    """Was the source ok in the most recent earlier run that captured it? None if unknown."""
    runs: dict[str, tuple[str, bool]] = {}
    for f in log_root.glob("*/*.jsonl"):
        if f.stem == run_id:
            continue
        for line in f.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("source_id") != source_id:
                continue
            ok = r.get("status") in ("stored", "unchanged")
            t, prev_ok = runs.get(f.stem, (r["fetched_at_utc"], True))
            runs[f.stem] = (max(t, r["fetched_at_utc"]), prev_ok and ok)
    if not runs:
        return None
    return max(runs.values())[1]


def decide(ok: bool, prev_ok: bool | None, has_issue: bool) -> str:
    """'open', 'close' or 'none' (two-in-a-row rule)."""
    if not ok and not has_issue and prev_ok is False:
        return "open"
    if ok and has_issue and prev_ok is True:
        return "close"
    return "none"


def title_for(source_id: str) -> str:
    return f"capture failure: {source_id}"


def failure_body(source_id: str, info: dict, run_id: str, run_url: str) -> str:
    lines = [f"Source `{source_id}` did not produce a valid capture in run `{run_id}`.", ""]
    for f in info["failures"]:
        lines.append(f"- **{f['status']}** (HTTP {f['http_status']}): {f['detail']} — {f['url']}")
    lines += ["", f"Run: {run_url}",
              "", ("A blocked source is not worked around (I7). An `empty` status means the "
              "page loaded but lacked expected content: check whether the source moved.")]
    return "\n".join(lines)


def raise_alerts(summary: dict[str, dict], run_id: str, run_url: str,
                 dry_run: bool = False) -> list[str]:
    actions: list[str] = []
    try:
        _gh("label", "create", LABEL, "--color", "B60205", "--force",
            "--description", "Automated capture failure") if not dry_run else None
        existing = {} if dry_run else _open_issues()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"alerts: gh unavailable ({e}); printing instead")
        dry_run, existing = True, {}
    for sid, info in sorted(summary.items()):
        title = title_for(sid)
        action = decide(info["ok"], previous_status(sid, run_id), title in existing)
        if action == "open":
            body = failure_body(sid, info, run_id, run_url) + (
                "\n\nOpened because this source also failed in its previous run (ADR 0014).")
            if dry_run:
                actions.append(f"WOULD OPEN {title}\n{body}")
            else:
                _gh("issue", "create", "--title", title, "--label", LABEL, "--body", body)
                actions.append(f"opened {title}")
        elif action == "close" and not dry_run:
            _gh("issue", "close", str(existing[title]), "--comment",
                f"Recovered: `{sid}` captured successfully in two consecutive runs "
                f"(latest `{run_id}`). {run_url}")
            actions.append(f"closed #{existing[title]}")
        elif not info["ok"]:
            actions.append(f"noted failure of {sid} (no issue change)")
    stale = existing.get("capture stale")
    if stale and not dry_run and any(i["ok"] for i in summary.values()):
        _gh("issue", "close", str(stale), "--comment", f"Captures resumed with run `{run_id}`.")
        actions.append(f"closed #{stale}")
    return actions
