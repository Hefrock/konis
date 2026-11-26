"""Ingestion health: capture logs -> daily per-source outcome counts.

Rebuilt from data/capture_log/ only. A run counts as ok for a source when every outcome
for that source in the run was `stored` or `unchanged`.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

PARSER_VERSION = "health/1"

SCHEMA = {"date_utc": pl.Utf8, "source_id": pl.Utf8, "runs": pl.Int64, "runs_ok": pl.Int64,
          "runs_failed": pl.Int64, "stored": pl.Int64, "unchanged": pl.Int64,
          "empty": pl.Int64, "error": pl.Int64, "blocked": pl.Int64,
          "last_failure_detail": pl.Utf8, "parser_version": pl.Utf8}


def build(log_root: Path = Path("data/capture_log")) -> pl.DataFrame:
    recs = []
    for f in sorted(log_root.glob("*/*.jsonl")):
        for line in f.read_text().splitlines():
            if line.strip():
                recs.append(json.loads(line))
    if not recs:
        return pl.DataFrame(schema=SCHEMA)
    df = pl.DataFrame(recs).with_columns(pl.col("fetched_at_utc").str.slice(0, 10)
                                         .alias("date_utc"))
    per_run = (df.group_by(["date_utc", "source_id", "run_id"])
               .agg(pl.col("status").is_in(["stored", "unchanged"]).all().alias("ok")))
    runs = (per_run.group_by(["date_utc", "source_id"])
            .agg(pl.len().alias("runs"), pl.col("ok").sum().alias("runs_ok")))
    counts = df.group_by(["date_utc", "source_id"]).agg(
        *[(pl.col("status") == s).sum().alias(s)
          for s in ("stored", "unchanged", "empty", "error", "blocked")],
        pl.col("detail").filter(~pl.col("status").is_in(["stored", "unchanged"]))
        .sort_by(pl.col("fetched_at_utc").filter(
            ~pl.col("status").is_in(["stored", "unchanged"]))).last()
        .alias("last_failure_detail"))
    out = (runs.join(counts, on=["date_utc", "source_id"])
           .with_columns((pl.col("runs") - pl.col("runs_ok")).alias("runs_failed"),
                         pl.lit(PARSER_VERSION).alias("parser_version")))
    return out.select(list(SCHEMA)).cast(SCHEMA).sort(["date_utc", "source_id"])


def write(df: pl.DataFrame, out: Path = Path("data/curated/ingestion_health.csv")) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(out)
    return out
