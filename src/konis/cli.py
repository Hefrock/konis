"""konis command line: `konis capture`, `konis guard`, `konis status`."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime

from konis.capture.engine import run_capture, summarize
from konis.capture.store import RawStore


def _run_id() -> str:
    gh = os.environ.get("GITHUB_RUN_ID")
    if gh:
        return f"gh-{gh}-{os.environ.get('GITHUB_RUN_ATTEMPT', '1')}"
    return "local-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def cmd_capture(a) -> int:
    run_id = a.run_id or _run_id()
    outcomes = run_capture(run_id, RawStore(), only=a.only)
    summary = summarize(outcomes)
    for sid, info in sorted(summary.items()):
        flag = "ok  " if info["ok"] else "FAIL"
        print(f"{flag} {sid:28s} stored={info['stored']} unchanged={info['unchanged']}"
              + "".join(f"\n       {f['status']}: {f['detail']}" for f in info["failures"]))
    if a.summary_out:
        with open(a.summary_out, "w") as f:
            json.dump({"run_id": run_id, "sources": summary}, f, indent=2)
    if a.alerts:
        from konis.alerts import raise_alerts
        url = (f"{os.environ.get('GITHUB_SERVER_URL', '')}/{os.environ.get('GITHUB_REPOSITORY', '')}"
               f"/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}")
        for act in raise_alerts(summary, run_id, url, dry_run=a.dry_run_alerts):
            print("alert:", act)
    # Exit 0 even with source failures: raw that was captured must still be committed.
    return 0


def cmd_guard(a) -> int:
    from konis import guards
    problems = guards.check_append_only(a.base) + guards.check_sizes()
    if a.bot:
        problems += [f"bot touched non-data path {p}" for p in guards.check_bot_paths(a.base)]
    for p in problems:
        print("GUARD:", p)
    return 1 if problems else 0


def cmd_parse(a) -> int:
    """Rebuild every curated table from raw and logs (K3)."""
    from konis.parse import airnow, health, weather, xact
    x = xact.build()
    print("wrote", xact.write(x), len(x), "rows")
    print(xact.summary(x))
    n = airnow.build()
    print("wrote", airnow.write(n), len(n), "rows")
    w = weather.build()
    print("wrote", weather.write(w), len(w), "rows")
    h = health.build()
    print("wrote", health.write(h), len(h), "rows")
    if a.check:  # determinism: a second rebuild must be identical
        if not (xact.build().equals(x) and airnow.build().equals(n) and weather.build().equals(w)
                and health.build().equals(h)):
            print("REBUILD NOT DETERMINISTIC")
            return 1
        print("rebuild deterministic")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="konis")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("capture", help="fetch all sources and archive changed content")
    c.add_argument("--only", nargs="*")
    c.add_argument("--run-id")
    c.add_argument("--summary-out")
    c.add_argument("--alerts", action="store_true", help="open/close GitHub issues")
    c.add_argument("--dry-run-alerts", action="store_true")
    c.set_defaults(fn=cmd_capture)
    g = sub.add_parser("guard", help="append-only, path and size checks before push")
    g.add_argument("--base", required=True)
    g.add_argument("--bot", action="store_true")
    g.set_defaults(fn=cmd_guard)
    pa = sub.add_parser("parse", help="rebuild curated tables from raw")
    pa.add_argument("--check", action="store_true", help="rebuild twice and compare")
    pa.set_defaults(fn=cmd_parse)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
