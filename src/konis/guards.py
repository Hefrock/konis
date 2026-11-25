"""Pre-push guards for bot commits (adapted from ilara)."""

from __future__ import annotations

import subprocess
from pathlib import Path

MAX_FILE_BYTES = 10 * 1024 * 1024
MUTABLE = ("_latest.json",)


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def check_append_only(base: str, head: str = "HEAD") -> list[str]:
    """Raw files and capture logs may only be added, never modified or deleted."""
    bad = []
    for line in _git("diff", "--name-status", "--no-renames", base, head).splitlines():
        status, path = line.split("\t", 1)
        protected = path.startswith(("data/raw/", "data/capture_log/"))
        if protected and status != "A" and not path.endswith(MUTABLE):
            bad.append(f"{status} {path}")
    return bad


def check_bot_paths(base: str, head: str = "HEAD") -> list[str]:
    """The capture bot commits only under data/."""
    return [p for p in _git("diff", "--name-only", base, head).splitlines()
            if not p.startswith("data/")]


def check_sizes(root: Path = Path("data")) -> list[str]:
    return [f"{p} is {p.stat().st_size} bytes" for p in root.rglob("*")
            if p.is_file() and p.stat().st_size > MAX_FILE_BYTES]
