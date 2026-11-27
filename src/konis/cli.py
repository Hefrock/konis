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


def cmd_seismic(a) -> int:
    from konis import seismic
    if a.action == "fetch":
        print("stored" if seismic.fetch() else "unchanged")
        return 0
    df = seismic.triggers()
    out = "data/curated/seismic_triggers.csv"
    df.write_csv(out)
    print("wrote", out, len(df), "rows")
    for line in seismic.summarize(df):
        print(line)
    return 0


def cmd_analyze(a) -> int:
    import subprocess
    from pathlib import Path

    from konis.analysis import xact_wind
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], check=False, capture_output=True,
                            text=True).stdout.strip() or "unknown"
    if a.name == "xact-wind":
        text = xact_wind.report(xact_wind.run(), commit)
        out = Path("docs/results") / f"xact-wind-{commit}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
        print(text)
        print("wrote", out)
        return 0
    from konis.analysis import transect
    if a.name == "transect-a":
        rows = transect.part_a()
        d = Path("docs/results")
        d.mkdir(parents=True, exist_ok=True)
        (d / "transect-partA.svg").write_text(transect.svg_plot(rows))
        (d / f"transect-partA-{commit}.md").write_text(transect.report_a(rows, commit))
        print(transect.report_a(rows, commit))
        return 0
    # transect-b: bot-safe outputs under data/ (K9); list newly completed episodes for alerts
    import json
    res = transect.part_b()
    out = Path("data/curated/transect_episodes.json")
    seen = set(json.loads(out.read_text())["completed_ids"]) if out.exists() else set()
    ids = [e["episode_id"] for e in res["completed"]]
    out.write_text(json.dumps({"completed_ids": ids,
                               "pending_ids": [e["episode_id"] for e in res["pending"]]},
                              indent=2) + "\n")
    Path("data/curated/transect_partB.md").write_text(transect.report_b(res, commit))
    new = [i for i in ids if i not in seen]
    if a.new_out:
        Path(a.new_out).write_text("\n".join(new))
    print(transect.report_b(res, commit))
    print("newly completed episodes:", new or "none")
    return 0


def cmd_release(a) -> int:
    from pathlib import Path

    from konis import release
    for f in release.build(Path(a.out), a.tag, a.commit):
        print("wrote", f)
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
    se = sub.add_parser("seismic", help="detonation-time check (needs the seismic extra)")
    se.add_argument("action", choices=["fetch", "analyze"])
    se.set_defaults(fn=cmd_seismic)
    an = sub.add_parser("analyze", help="pre-registered analyses (ADR 0009)")
    an.add_argument("name", choices=["xact-wind", "transect-a", "transect-b"])
    an.add_argument("--new-out", help="transect-b: write newly completed episode ids here")
    an.set_defaults(fn=cmd_analyze)
    rl = sub.add_parser("release", help="build weekly data release assets (ADR 0015)")
    rl.add_argument("action", choices=["build"])
    rl.add_argument("--out", required=True)
    rl.add_argument("--tag", required=True)
    rl.add_argument("--commit", required=True)
    rl.set_defaults(fn=cmd_release)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
