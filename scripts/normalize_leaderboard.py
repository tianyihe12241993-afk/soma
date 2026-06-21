#!/usr/bin/env python3
"""Normalize immutable raw snapshots -> data/processed/leaderboard_snapshots.jsonl

Each row: observed_at, hotkey, display_name, rank, overall, easy, medium, hard,
          review_status, eval_status

Idempotent per (observed_at, hotkey): re-running won't duplicate rows already present.
Processes all raw snapshots not yet normalized.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import RAW, PROCESSED, hotkey_to_name  # noqa: E402

OUT = PROCESSED / "leaderboard_snapshots.jsonl"


def main() -> int:
    names = hotkey_to_name()
    existing = set()
    if OUT.exists():
        for line in OUT.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                existing.add((r["observed_at"], r["hotkey"]))

    new_rows = []
    for snap_path in sorted(RAW.glob("*/*_leaderboard.json")):
        snap = json.loads(snap_path.read_text())
        observed_at = snap.get("observed_at", "")
        miners = snap.get("miners", [])
        # rank by overall (desc), among rows that have a number
        ranked = sorted([m for m in miners if m.get("total") is not None],
                        key=lambda m: -m["total"])
        rank_of = {m["hotkey"]: i + 1 for i, m in enumerate(ranked)}
        for m in miners:
            hk = m.get("hotkey")
            key = (observed_at, hk)
            if key in existing:
                continue
            existing.add(key)
            new_rows.append({
                "observed_at": observed_at,
                "hotkey": hk,
                "display_name": names.get(hk, ""),          # our slot name (m7, ...) or ""
                "rank": rank_of.get(hk),
                "overall": m.get("total"),
                "easy": m.get("easy"),
                "medium": m.get("medium"),
                "hard": m.get("hard"),
                "review_status": m.get("review_status", ""),
                "eval_status": m.get("eval_status", ""),
            })

    PROCESSED.mkdir(parents=True, exist_ok=True)
    with OUT.open("a", encoding="utf-8") as f:
        for r in new_rows:
            f.write(json.dumps(r) + "\n")
    print(f"normalized {len(new_rows)} new rows -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
