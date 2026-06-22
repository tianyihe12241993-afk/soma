#!/usr/bin/env python3
"""Pivot data/processed/miner_task_scores.jsonl into a per-task matrix.

Writes:
  data/processed/task_matrix.jsonl   one row per task_id: {task_id, task_name, category,
                                      is_screener, miners:{miner_id:{pass,ratio,score,broke,
                                      neg,baseline_pass,tokens_in,tokens_out}}}
  data/latest/task_matrix.json       same, plus a small index of miner_ids covered.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import PROCESSED, LATEST, utc_now  # noqa: E402

SRC = PROCESSED / "miner_task_scores.jsonl"
OUT = PROCESSED / "task_matrix.jsonl"


def main() -> int:
    if not SRC.exists():
        print(f"{SRC} missing — run import_platform_results.py first.", file=sys.stderr)
        return 1
    rows = [json.loads(l) for l in SRC.read_text(encoding="utf-8").splitlines() if l.strip()]
    matrix = {}
    miner_ids = set()
    for r in rows:
        tid = r["task_id"]
        miner_ids.add(r["miner_id"])
        m = matrix.setdefault(tid, {
            "task_id": tid, "task_name": r.get("task_name"),
            "category": r.get("category"),
            "is_screener": r.get("category") == "screener",
            "miners": {},
        })
        if m["category"] in (None, "screener") and r.get("category") not in (None, "screener"):
            m["category"] = r["category"]            # prefer a real E/M/H label if any source has it
        m["miners"][r["miner_id"]] = {
            "pass": r.get("miner_pass"), "ratio": r.get("compression_ratio"),
            "score": r.get("score"), "broke": r.get("broke_baseline"),
            "neg": r.get("negative_score"), "baseline_pass": r.get("baseline_pass"),
            "tokens_in": r.get("baseline_tokens"), "tokens_out": r.get("miner_tokens"),
        }
    out = sorted(matrix.values(), key=lambda m: m["task_id"])

    PROCESSED.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for m in out:
            f.write(json.dumps(m) + "\n")
    LATEST.mkdir(parents=True, exist_ok=True)
    (LATEST / "task_matrix.json").write_text(json.dumps(
        {"computed_at": utc_now(), "miner_ids": sorted(miner_ids),
         "task_count": len(out), "tasks": out}, indent=2), encoding="utf-8")
    n_cat = sum(1 for m in out if m["category"] not in (None, "screener"))
    print(f"wrote {OUT} and {LATEST/'task_matrix.json'} "
          f"({len(out)} tasks, {len(miner_ids)} miners, {n_cat} with E/M/H category)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
