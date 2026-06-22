#!/usr/bin/env python3
"""Find where the compression-ratio gap lives, task by task (m7 vs top miners).

Reads data/processed/task_matrix.jsonl. Baseline = m7. Reference = top_miners.yaml
primary_reference (default overall leader), plus 'proven max ratio' across ALL top
miners that also pass a task (an evidence-based safe-headroom ceiling).

Writes:
  data/processed/shared_pass_tasks.jsonl      tasks m7 & reference BOTH pass, with the
        score gap decomposed: ratio_explained (0.5*ln(ref/m7)) vs residual.
  data/processed/compression_gap_tasks.jsonl  tasks m7 passes with ratio < 2x
        (barely-compressed; largest raw headroom).

The 0.5*ln(ratio) term is a MANUAL-INTERPRETATION model (empirically fits shared-pass
tasks: score ~ 1 + 0.5*ln(ratio)). Observed scores are carried alongside, untouched.
"""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import PROCESSED, CONFIG, read_text, load_top_miners  # noqa: E402
import re

MATRIX = PROCESSED / "task_matrix.jsonl"
SHARED = PROCESSED / "shared_pass_tasks.jsonl"
GAP = PROCESSED / "compression_gap_tasks.jsonl"
BARELY = 2.0


def _primary_ref_id(tops: dict) -> str | None:
    txt = read_text(CONFIG / "top_miners.yaml")
    m = re.search(r'primary_reference:\s*(\S+)', txt)
    if not m:
        return None
    hk = m.group(1)
    for tid, d in tops.items():
        if d["hotkey"] == hk:
            return tid
    return None


def main() -> int:
    if not MATRIX.exists():
        print(f"{MATRIX} missing — run normalize_task_scores.py first.", file=sys.stderr)
        return 1
    tasks = [json.loads(l) for l in MATRIX.read_text(encoding="utf-8").splitlines() if l.strip()]
    tops = load_top_miners()
    top_ids = set(tops)
    ref = _primary_ref_id(tops)
    if not ref:
        print("no primary_reference resolved from top_miners.yaml", file=sys.stderr)
        return 1

    shared, gaps = [], []
    for t in tasks:
        if t.get("is_screener"):
            continue
        ms = t["miners"]
        m7 = ms.get("m7")
        if not m7 or not m7.get("pass") or not m7.get("ratio"):
            continue
        # barely-compressed: m7 passes, ratio < 2x
        if m7["ratio"] < BARELY:
            gaps.append({"task_id": t["task_id"], "task_name": t["task_name"],
                         "category": t.get("category"), "m7_ratio": m7["ratio"],
                         "m7_score": m7.get("score"),
                         "baseline_pass": m7.get("baseline_pass")})
        # proven max ratio among top miners that pass this task
        best_r, best_who = 0.0, None
        for tid in top_ids:
            x = ms.get(tid)
            if x and x.get("pass") and x.get("ratio") and x["ratio"] > best_r:
                best_r, best_who = x["ratio"], tid
        r = ms.get(ref)
        if r and r.get("pass") and r.get("ratio"):
            actual_gap = (r.get("score") or 0) - (m7.get("score") or 0)
            ratio_expl = 0.5 * math.log(r["ratio"] / m7["ratio"]) if r["ratio"] > 0 else 0
            shared.append({
                "task_id": t["task_id"], "task_name": t["task_name"],
                "category": t.get("category"),
                "m7_ratio": m7["ratio"], "m7_score": m7.get("score"),
                "ref_id": ref, "ref_ratio": r["ratio"], "ref_score": r.get("score"),
                "actual_score_gap": round(actual_gap, 4),
                "ratio_explained_gap": round(ratio_expl, 4),
                "residual_gap": round(actual_gap - ratio_expl, 4),
                "proven_max_ratio": round(best_r, 4), "proven_by": best_who,
                "safe_headroom_x": round(best_r / m7["ratio"], 3) if best_r > m7["ratio"] else 1.0,
            })

    PROCESSED.mkdir(parents=True, exist_ok=True)
    with SHARED.open("w", encoding="utf-8") as f:
        for r in sorted(shared, key=lambda x: -x["actual_score_gap"]):
            f.write(json.dumps(r) + "\n")
    with GAP.open("w", encoding="utf-8") as f:
        for r in sorted(gaps, key=lambda x: x["m7_ratio"]):
            f.write(json.dumps(r) + "\n")

    print(f"wrote {SHARED} ({len(shared)} shared-pass) and {GAP} ({len(gaps)} barely-compressed)")
    if shared:
        n = len(shared)
        mean_actual = sum(x["actual_score_gap"] for x in shared) / n
        mean_ratio = sum(x["ratio_explained_gap"] for x in shared) / n
        print(f"  shared-pass mean gap {mean_actual:+.3f}/task; ratio-model explains "
              f"{mean_ratio:+.3f}/task (residual {mean_actual-mean_ratio:+.3f}) "
              f"→ the gap is compression depth, not solving")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
