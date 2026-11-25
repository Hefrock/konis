"""GitHub Issue alerts for capture failures (ilara lessons 1-2).

One open issue per failing source, labelled `capture-failure`. A repeat failure adds a
comment; the first later success comments and closes the issue. Uses the `gh` CLI, which
is present on GitHub-hosted runners (GITHUB_TOKEN with issues: write).
"""

from __future__ import annotations

import json
import subprocess

LABEL = "capture-failure"


def _gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def _open_issues() -> dict[str, int]:
    out = _gh("issue", "list", "--label", LABEL, "--state", "open", "--limit", "200",
              "--json", "number,title")
    return {i["title"]: i["number"] for i in json.loads(out or "[]")}


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
        if not info["ok"]:
            body = failure_body(sid, info, run_id, run_url)
            if dry_run:
                actions.append(f"WOULD ALERT {title}\n{body}")
            elif title in existing:
                _gh("issue", "comment", str(existing[title]), "--body", body)
                actions.append(f"commented #{existing[title]}")
            else:
                _gh("issue", "create", "--title", title, "--label", LABEL, "--body", body)
                actions.append(f"opened {title}")
        elif title in existing and not dry_run:
            _gh("issue", "close", str(existing[title]), "--comment",
                f"Recovered: run `{run_id}` captured `{sid}` successfully. {run_url}")
            actions.append(f"closed #{existing[title]}")
    stale = existing.get("capture stale")
    if stale and not dry_run and any(i["ok"] for i in summary.values()):
        _gh("issue", "close", str(stale), "--comment", f"Captures resumed with run `{run_id}`.")
        actions.append(f"closed #{stale}")
    return actions
