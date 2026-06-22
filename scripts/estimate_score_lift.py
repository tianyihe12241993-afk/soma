#!/usr/bin/env python3
"""Estimate m7's safe score-lift from deeper pass-safe compression, and write the gap
analysis. Reads data/processed/shared_pass_tasks.jsonl (proven_max_ratio per task) and
data/processed/fragile_tasks.jsonl. Writes reports/m7_gap_analysis.md.

MANUAL INTERPRETATION: per-task score ~ 1 + 0.5*ln(ratio) on shared-pass tasks (fits
the observed data closely). "Safe headroom" = a top miner PASSED the same task at a
higher ratio, so it is a proven-achievable UPPER BOUND — not a guarantee m7's mechanism
hits it without breaking the pass. Fragile tasks are excluded from the push list.
"""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import PROCESSED, REPORTS, utc_now, load_miners_rich  # noqa: E402

SHARED = PROCESSED / "shared_pass_tasks.jsonl"
GAP = PROCESSED / "compression_gap_tasks.jsonl"
FRAGILE = PROCESSED / "fragile_tasks.jsonl"


def _load(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def main() -> int:
    shared = _load(SHARED)
    if not shared:
        print(f"{SHARED} missing — run find_shared_pass_gaps.py first.", file=sys.stderr)
        return 1
    fragile = {f["task_name"] for f in _load(FRAGILE)}
    barely = _load(GAP)
    m7 = load_miners_rich().get("m7", {})

    # safe headroom = passes, has proven higher ratio, NOT fragile
    rows = []
    for s in shared:
        if s["task_name"] in fragile:
            continue
        if s["proven_max_ratio"] and s["proven_max_ratio"] > s["m7_ratio"]:
            gain = 0.5 * math.log(s["proven_max_ratio"] / s["m7_ratio"])
            rows.append({**s, "est_gain": round(gain, 4)})
    rows.sort(key=lambda x: -x["est_gain"])
    tot = sum(x["est_gain"] for x in rows)
    base = m7.get("total", 0) or 0
    lift_per45 = tot / 45

    L = [f"# m7 gap analysis — safe compression headroom",
         f"_computed {utc_now()} from data/processed/shared_pass_tasks.jsonl. "
         f"Model: score ~ 1 + 0.5·ln(ratio) (manual interpretation). Proven upper bound._", "",
         f"**{len(rows)} SAFE headroom tasks** (m7 passes, a top miner proved a higher ratio, not fragile). "
         f"Est. total per-task gain **{tot:+.2f}** → avg over 45 tasks **{lift_per45:+.3f}** "
         f"(rough lift {base:.3f} → ~{base+lift_per45:.2f} if fully captured).", "",
         "## Ranked safe headroom (push these first)",
         "| task | m7 ratio | proven | by | ×more | ~gain | m7 score | actual gap | ratio-expl |",
         "|------|----------|--------|----|-------|-------|----------|-----------|-----------|"]
    for x in rows:
        L.append(f"| {x['task_name']} | {x['m7_ratio']:.2f}× | {x['proven_max_ratio']:.2f}× | "
                 f"{x['proven_by']} | {x['safe_headroom_x']:.2f}× | {x['est_gain']:+.3f} | "
                 f"{(x['m7_score'] or 0):.3f} | {x['actual_score_gap']:+.3f} | {x['ratio_explained_gap']:+.3f} |")

    L += ["", f"## Barely-compressed (m7 ratio < 2×) — {len(barely)} tasks, biggest raw headroom",
          "| task | m7 ratio | m7 score |", "|------|----------|----------|"]
    for b in barely:
        L.append(f"| {b['task_name']} | {b['m7_ratio']:.2f}× | {(b['m7_score'] or 0):.3f} |")

    L += ["", f"## Fragile tasks EXCLUDED from the push list ({len(fragile)})",
          ("- " + ", ".join(sorted(fragile))) if fragile else "- none"]
    L += ["", "## Caveats",
          "- Upper bound: assumes m7 can match the proven ratio **without losing the pass**. "
          "Validate each push locally; a broken pass costs ~−4 (catastrophic).",
          "- Score model is manual interpretation; observed `actual_score_gap` is carried for truth.",
          "- Medium/Hard attribution needs the task→category map (currently missing)."]
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "m7_gap_analysis.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {REPORTS/'m7_gap_analysis.md'} — {len(rows)} safe headroom tasks, "
          f"est +{lift_per45:.3f}/task (toward ~{base+lift_per45:.2f} from {base:.3f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
