#!/usr/bin/env python3
"""Find FRAGILE tasks: where compression broke a passing baseline (✓→✗), for ANY of
our miners. These are the catastrophic-penalty cases the next round must guard against.

Reads data/processed/task_matrix.jsonl. Writes data/processed/fragile_tasks.jsonl:
  {task_id, task_name, category, broke_by:[miner_ids], m7_broke, detail:{miner:{ratio,score}},
   severity}  — severity = most-negative score among breakers (lower = worse).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import PROCESSED, load_miners_rich  # noqa: E402

MATRIX = PROCESSED / "task_matrix.jsonl"
OUT = PROCESSED / "fragile_tasks.jsonl"


def main() -> int:
    if not MATRIX.exists():
        print(f"{MATRIX} missing — run normalize_task_scores.py first.", file=sys.stderr)
        return 1
    ours = set(load_miners_rich())                       # m7..m11
    tasks = [json.loads(l) for l in MATRIX.read_text(encoding="utf-8").splitlines() if l.strip()]
    out = []
    for t in tasks:
        if t.get("is_screener"):
            continue
        breakers, detail, worst = [], {}, None
        for mid, d in t["miners"].items():
            if mid not in ours:
                continue
            if d.get("broke"):                            # baseline passed, miner failed
                breakers.append(mid)
                detail[mid] = {"ratio": d.get("ratio"), "score": d.get("score")}
                s = d.get("score")
                if s is not None and (worst is None or s < worst):
                    worst = s
        if breakers:
            out.append({"task_id": t["task_id"], "task_name": t["task_name"],
                        "category": t.get("category"), "broke_by": sorted(breakers),
                        "m7_broke": "m7" in breakers, "detail": detail,
                        "severity": worst})
    PROCESSED.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for r in sorted(out, key=lambda x: (not x["m7_broke"], x["severity"] if x["severity"] is not None else 0)):
            f.write(json.dumps(r) + "\n")
    m7f = [r["task_name"] for r in out if r["m7_broke"]]
    print(f"wrote {OUT} ({len(out)} fragile tasks; m7 breaks {len(m7f)}: {', '.join(m7f) or 'none'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
