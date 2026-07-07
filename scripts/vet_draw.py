#!/usr/bin/env python3
"""Vet a scored draw: CLEAN vs BAD-DRAW vs BAD-ACCOUNT (run BEFORE trusting any scored result).

Rebuilt 2026-07-07 (the comp-108 original was never committed — scripts/ was gitignored).
Thresholds are the comp-108-proven ones (they caught the m33/np2b/np2d1 confounds):
  CLEAN       cache >= 88%  AND  break-run rate <= 13%  AND  unresolved runs < 4
  BAD-ACCOUNT cache < 88%             -> routing/provider problem: fix routing, score is confounded
  BAD-DRAW    cache OK, breaks > 13%  -> unlucky draw: discard the score, redraw the same account

Category-agnostic (works with comp-110's task-type layers — categories are read verbatim).

Usage:
  python3 scripts/vet_draw.py --hotkey HK [--comp N]     # comp defaults to config/dashboard.yaml
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_runs import parse_miner  # noqa: E402

CFG = (Path(__file__).resolve().parent.parent / "config" / "dashboard.yaml").read_text()
DEFAULT_COMP = int((re.search(r"competition_id:\s*(\d+)", CFG) or [None, "110"])[1])

CACHE_MIN = 0.88          # weighted-token regime: below this the account's routing is broken
BREAK_MAX = 0.13          # share of runs that break a baseline-pass task
UNRESOLVED_MAX = 4        # runs with no pass/fail outcome (timeouts / infra)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hotkey", required=True)
    ap.add_argument("--comp", type=int, default=DEFAULT_COMP)
    args = ap.parse_args()

    info = parse_miner(args.comp, args.hotkey)
    tasks, runs_by_task = info["tasks"], info["runs_by_task"]
    if not tasks:
        print(f"NO DATA — no tasks on the miner page (comp {args.comp}, {args.hotkey[:12]}…). "
              "Not scored yet, or the page format changed.")
        return 2

    tot_in = tot_cached = 0
    n_runs = n_break = n_flip = n_unresolved = 0
    for t in tasks:
        base_pass = t.get("pass_without_compression")
        for r in (runs_by_task.get(str(t.get("task_id"))) or runs_by_task.get(t.get("task_id")) or []):
            n_runs += 1
            tot_in += r.get("input_tokens_with_compression") or 0
            tot_cached += r.get("cached_input_tokens_with_compression") or 0
            rp = r.get("pass_with_compression")
            if rp is None:
                n_unresolved += 1
            elif base_pass is True and rp is False:
                n_break += 1
            elif base_pass is False and rp is True:
                n_flip += 1

    cache = tot_cached / (tot_in + tot_cached) if (tot_in + tot_cached) else 0.0
    break_rate = n_break / n_runs if n_runs else 0.0
    flip_rate = n_flip / n_runs if n_runs else 0.0

    summary = info["summary"] or {}
    print(f"comp {args.comp}  {args.hotkey[:16]}…  total={summary.get('total_score')}  "
          f"categories={summary.get('category_scores')}")
    print(f"runs={n_runs}  cache={cache:.1%} (min {CACHE_MIN:.0%})  "
          f"break-runs={n_break} ({break_rate:.1%}, max {BREAK_MAX:.0%})  "
          f"flip-runs={n_flip} ({flip_rate:.1%})  unresolved={n_unresolved} (max <{UNRESOLVED_MAX})")

    if cache < CACHE_MIN:
        print("VERDICT: BAD-ACCOUNT — cache below floor: routing/provider confound. "
              "Fix routing; do NOT read this score as algo signal.")
        return 1
    if break_rate > BREAK_MAX or n_unresolved >= UNRESOLVED_MAX:
        print("VERDICT: BAD-DRAW — account clean but the draw rolled dirty. "
              "Discard the score; redraw on the same account.")
        return 1
    print("VERDICT: CLEAN — trustworthy draw.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
