#!/usr/bin/env python3
"""Ingest dashboard leaderboard data into data/processed/leaderboard_snapshots.jsonl.

Thin wrapper over the existing collectors so the research Makefile has one entry point:
  --import <file>   first write an immutable raw snapshot from a saved leaderboard
                    (html/json/csv) via collect_dashboard.py, then normalize.
  (default)         normalize every raw leaderboard snapshot not yet processed.

Raw snapshots are never overwritten; normalization is idempotent per (observed_at,hotkey).
"""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import normalize_leaderboard  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--import", dest="imp", help="saved leaderboard (html/json/csv) -> new raw snapshot")
    args = ap.parse_args()
    if args.imp:
        rc = subprocess.run([sys.executable, str(HERE / "collect_dashboard.py"),
                             "--import", args.imp]).returncode
        if rc != 0:
            return rc
    return normalize_leaderboard.main()


if __name__ == "__main__":
    raise SystemExit(main())
