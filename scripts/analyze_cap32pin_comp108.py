#!/usr/bin/env python3
"""cap32+pin comp-108 postmortem: decompose WHERE the champion's score came from.

Input:  data/raw/platform_results/2026-07-07/045717_swe_runs.json (13 miners x 50 tasks x 5 runs)
Output: reports/comp108_cap32pin_postmortem.md (numbers; narrative added on top, marked)
        data/latest/cap32pin_postmortem.json (machine)

Method notes (truth-levels):
- All scores/pass flags/tokens = source:platform (scraped archive). Savings ratios computed from
  RAW token totals (the platform used WEIGHTED for the savings term; baseline token splits are not
  exposed, so ratios here are an APPROXIMATION — labeled `raw_ln_ratio`).
- Task categories are INFERRED (Hard = baseline-fail; Easy/Medium = token-threshold split fitted to
  the published per-category board scores) and VALIDATED against every miner's board numbers below.
"""
from __future__ import annotations
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAP = ROOT / "data" / "raw" / "platform_results" / "2026-07-07" / "045717_swe_runs.json"
OUT_MD = ROOT / "reports" / "comp108_cap32pin_postmortem_data.md"   # data section only; narrative lives in comp108_cap32pin_postmortem.md
OUT_JSON = ROOT / "data" / "latest" / "cap32pin_postmortem.json"

LABELS = {
    "5DAbJik": "cap32+pin", "5FLUziw": "np2+pin", "5E4Y4jz": "np3+pin",
    "5CPbtf": "np2", "5F9ZRe": "np3", "5FXAR4": "nocap",
    "5DMC61SU": "M-winner", "5F4g41c5": "H-winner", "5D22vwFM": "E-winner",
    "5DCnA57": "old-leader", "5EeUAVZ": "king-DQ1", "5GpLcd": "king-DQ2", "5DkJeMq": "xtra-win",
}
BOARD = {  # published board category scores (source:platform, archive snapshot 034045)
    "cap32+pin": (1.0443597, 0.8616654, 0.2812331),
    "np2+pin": None, "np3+pin": None, "np2": None, "np3": None, "nocap": None,
    "M-winner": None, "H-winner": None, "E-winner": None, "old-leader": None,
    "king-DQ1": None, "king-DQ2": None, "xtra-win": None,
}


def label(hk: str) -> str:
    for p, l in LABELS.items():
        if hk.startswith(p):
            return l
    return hk[:8]


def load():
    snap = json.loads(SNAP.read_text())
    miners = {}
    for m in snap["miners"]:
        miners[label(m["hotkey"])] = m
    board = {label(r["hotkey"]): r for r in snap.get("leaderboard", []) if label(r["hotkey"]) in
             set(LABELS.values())}
    return snap, miners


def task_key(t) -> str:
    return t.get("task_name") or str(t.get("task_id"))


def load_solved_categories() -> tuple[dict, str]:
    """Category map SOLVED by hill-climbing the 39 published board-score constraints
    (13 miners x E/M/H means) over the 50-task assignment; fit RMS ~0.02/cell.
    Persisted at data/latest/comp108_task_categories.json. Sizes: E17/M16/H17."""
    p = ROOT / "data" / "latest" / "comp108_task_categories.json"
    cats = json.loads(p.read_text())
    return cats, "solved-from-board-constraints (RMS ~0.02/cell, E17/M16/H17)"


def infer_categories(miners: dict) -> tuple[dict, float, list]:
    """(legacy heuristic, superseded by load_solved_categories) Hard = baseline-fail; E/M = token split."""
    base_pass, base_tokens = {}, defaultdict(list)
    for m in miners.values():
        for t in m["tasks"]:
            if t.get("is_screener"):
                continue
            k = task_key(t)
            bp = t.get("pass_without_compression")
            if bp is not None:
                base_pass.setdefault(k, bp)
            tw = t.get("tokens_without_compression")
            if tw:
                base_tokens[k].append(tw)
    avg_tokens = {k: sum(v) / len(v) for k, v in base_tokens.items() if v}
    hard = {k for k, bp in base_pass.items() if bp is False}
    passk = [k for k in base_pass if k not in hard and k in avg_tokens]

    # reference categories from cap32+pin's published board scores
    ref = miners["cap32+pin"]
    ref_scores = {task_key(t): t.get("platform_score") for t in ref["tasks"] if not t.get("is_screener")}
    want_e, want_m, want_h = BOARD["cap32+pin"]

    def cat_means(thresh):
        e = [ref_scores[k] for k in passk if avg_tokens[k] <= thresh and ref_scores.get(k) is not None]
        mm = [ref_scores[k] for k in passk if avg_tokens[k] > thresh and ref_scores.get(k) is not None]
        h = [ref_scores[k] for k in hard if ref_scores.get(k) is not None]
        f = lambda xs: sum(xs) / len(xs) if xs else float("nan")
        return f(e), f(mm), f(h)

    best, best_err = None, 1e9
    for thresh in sorted({avg_tokens[k] for k in passk}):
        e, mm, h = cat_means(thresh)
        if math.isnan(e) or math.isnan(mm):
            continue
        err = (e - want_e) ** 2 + (mm - want_m) ** 2
        if err < best_err:
            best_err, best = err, thresh
    cats = {}
    for k in base_pass:
        if k in hard:
            cats[k] = "H"
        elif k in avg_tokens:
            cats[k] = "E" if avg_tokens[k] <= best else "M"
    e, mm, h = cat_means(best)
    fit_report = [f"threshold = {best:,.0f} baseline tokens; cap32+pin fit: "
                  f"E {e:.4f} (board {want_e:.4f}) M {mm:.4f} (board {want_m:.4f}) H {h:.4f} (board {want_h:.4f})"]
    return cats, best, fit_report


def miner_stats(m: dict, cats: dict) -> dict:
    per_cat = defaultdict(list)
    n_runs = n_break = n_flip = n_unres = 0
    tot_in = tot_cached = 0
    ln_ratios, task_std = [], []
    per_task = {}
    for t in m["tasks"]:                     # ALL 50 tasks — screeners are Easy in the solved map
        k = task_key(t)
        cat = cats.get(k, "?")
        s = t.get("platform_score")
        if s is not None:
            per_cat[cat].append(s)
            per_task[k] = {"cat": cat, "score": s, "base_pass": t.get("pass_without_compression"),
                           "pass": t.get("pass_with_compression"),
                           "tok_wo": t.get("tokens_without_compression"), "tok_w": t.get("tokens_with_compression")}
        if t.get("tokens_without_compression") and t.get("tokens_with_compression"):
            ln_ratios.append(math.log(t["tokens_without_compression"] / t["tokens_with_compression"]))
        runs = t.get("runs") or []
        rs = [r.get("platform_score") for r in runs if r.get("platform_score") is not None]
        if len(rs) > 1:
            mu = sum(rs) / len(rs)
            task_std.append(math.sqrt(sum((x - mu) ** 2 for x in rs) / (len(rs) - 1)))
        for r in runs:
            n_runs += 1
            tot_in += r.get("input_tokens_with_compression") or 0
            tot_cached += r.get("cached_input_tokens_with_compression") or 0
            rp = r.get("pass_with_compression")
            if rp is None:
                n_unres += 1
            elif t.get("pass_without_compression") is True and rp is False:
                n_break += 1
            elif t.get("pass_without_compression") is False and rp is True:
                n_flip += 1
    f = lambda xs: sum(xs) / len(xs) if xs else float("nan")
    # per-run-slice pseudo-draws: total recomputed using only attempt k
    slice_totals = []
    for k_at in range(1, 6):
        vals = []
        for t in m["tasks"]:
            rs = [r.get("platform_score") for r in (t.get("runs") or [])
                  if r.get("attempt_no") == k_at and r.get("platform_score") is not None]
            if rs:
                vals.append(rs[0])
        if vals:
            slice_totals.append(sum(vals) / len(vals))
    return {
        "total_runs": n_runs, "break_runs": n_break, "flip_runs": n_flip, "unresolved": n_unres,
        "break_rate": n_break / n_runs if n_runs else None,
        "flip_rate": n_flip / n_runs if n_runs else None,
        "cache_share": tot_cached / (tot_in + tot_cached) if (tot_in + tot_cached) else None,
        "E": f(per_cat["E"]), "M": f(per_cat["M"]), "H": f(per_cat["H"]),
        "overall_mean_cat": f([f(per_cat["E"]), f(per_cat["M"]), f(per_cat["H"])]),
        "raw_ln_ratio": f(ln_ratios), "keep_x": math.exp(f(ln_ratios)) if ln_ratios else None,
        "task_score_std": f(task_std),
        "slice_totals": [round(x, 4) for x in slice_totals],
        "per_task": per_task,
    }


def pair_diff(a: dict, b: dict, cats: dict):
    """per-task score diff a-b on shared tasks, grouped by category."""
    diffs = defaultdict(list)
    movers = []
    for k, ta in a["per_task"].items():
        tb = b["per_task"].get(k)
        if tb is None:
            continue
        d = ta["score"] - tb["score"]
        diffs[ta["cat"]].append(d)
        movers.append((d, k, ta["cat"], ta["score"], tb["score"]))
    movers.sort()
    f = lambda xs: sum(xs) / len(xs) if xs else float("nan")
    return {c: (f(v), len(v)) for c, v in diffs.items()}, movers


def main() -> int:
    snap, miners = load()
    cats, method = load_solved_categories()
    n_by_cat = defaultdict(int)
    for v in cats.values():
        n_by_cat[v] += 1

    stats = {name: miner_stats(m, cats) for name, m in miners.items()}

    L = ["# comp-108 cap32+pin postmortem — data section (generated by scripts/analyze_cap32pin_comp108.py)",
         f"_snapshot: {SNAP.name} (source:platform, archive). Categories: {method}; "
         f"E={n_by_cat['E']} M={n_by_cat['M']} H={n_by_cat['H']} (incl. the 5 screeners, which land in Easy)._", ""]

    # validation vs board for every miner with board scores
    L.append("## Category-inference validation (computed vs published board)")
    L.append("| miner | E calc | M calc | H calc | board E/M/H |")
    L.append("|---|---|---|---|---|")
    board_rows = {label(r["hotkey"]): r for r in snap.get("leaderboard", [])}
    for name in ["cap32+pin", "np2", "np3", "np2+pin", "np3+pin", "nocap", "M-winner", "H-winner",
                 "E-winner", "old-leader", "king-DQ1", "king-DQ2", "xtra-win"]:
        s = stats[name]
        m = miners[name].get("summary") or {}
        cs = m.get("category_scores") or {}
        L.append(f"| {name} | {s['E']:.3f} | {s['M']:.3f} | {s['H']:.3f} | "
                 f"{cs.get('Easy', float('nan')):.3f}/{cs.get('Medium', float('nan')):.3f}/{cs.get('Hard', float('nan')):.3f} |")
    L.append("")

    L.append("## Core table (all 50 tasks x 5 runs)")
    L.append("| miner | total | E | M | H | break-runs | flip-runs | cache | keep (x less tokens) | task-score std | per-attempt totals (5 pseudo-draws) |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for name in ["cap32+pin", "np2+pin", "np3+pin", "np2", "np3", "nocap", "M-winner", "H-winner",
                 "E-winner", "old-leader", "xtra-win", "king-DQ1", "king-DQ2"]:
        s = stats[name]
        tot = (miners[name].get("summary") or {}).get("total_score")
        L.append(f"| {name} | {tot:.4f} | {s['E']:.3f} | {s['M']:.3f} | {s['H']:.3f} "
                 f"| {s['break_runs']} ({s['break_rate']:.1%}) | {s['flip_runs']} ({s['flip_rate']:.1%}) "
                 f"| {s['cache_share']:.1%} | {s['keep_x']:.2f}x | {s['task_score_std']:.3f} "
                 f"| {min(s['slice_totals']):.3f}–{max(s['slice_totals']):.3f} |")
    L.append("")

    # pin isolation
    L.append("## PIN isolation (same cap, +pin vs base) — per-task score diff (pin − base)")
    for a, b in [("np2+pin", "np2"), ("np3+pin", "np3")]:
        by_cat, movers = pair_diff(stats[a], stats[b], cats)
        L.append(f"### {a} − {b}")
        L.append("| cat | mean Δscore | n |")
        L.append("|---|---|---|")
        for c in "EMH":
            if c in by_cat:
                L.append(f"| {c} | {by_cat[c][0]:+.3f} | {by_cat[c][1]} |")
        worst = [f"`{k}`({c}) {d:+.2f}" for d, k, c, _, _ in movers[:5]]
        best = [f"`{k}`({c}) {d:+.2f}" for d, k, c, _, _ in movers[-5:][::-1]]
        L.append(f"- worst movers: {', '.join(worst)}")
        L.append(f"- best movers: {', '.join(best)}")
        L.append("")

    # cap isolation
    L.append("## CAP isolation (same pin, different cap) — per-task score diff")
    for a, b in [("cap32+pin", "np2+pin"), ("cap32+pin", "np3+pin"), ("cap32+pin", "np2"), ("cap32+pin", "np3")]:
        by_cat, movers = pair_diff(stats[a], stats[b], cats)
        cells = " ".join(f"{c}:{by_cat[c][0]:+.3f}" for c in "EMH" if c in by_cat)
        worst = ", ".join(f"`{k}`({c}) {d:+.2f}" for d, k, c, _, _ in movers[:3])
        best = ", ".join(f"`{k}`({c}) {d:+.2f}" for d, k, c, _, _ in movers[-3:][::-1])
        L.append(f"- **{a} − {b}**: {cells}  | worst: {worst} | best: {best}")
    L.append("")

    # gaps to winners
    L.append("## Gap decomposition vs the corner winners")
    for rival, cat in [("M-winner", "M"), ("H-winner", "H"), ("E-winner", "E")]:
        by_cat, movers = pair_diff(stats["cap32+pin"], stats[rival], cats)
        d, n = by_cat.get(cat, (float("nan"), 0))
        in_cat = [(dd, k) for dd, k, c, _, _ in movers if c == cat]
        worst = ", ".join(f"`{k}` {dd:+.2f}" for dd, k in in_cat[:6])
        s_r, s_o = stats[rival], stats["cap32+pin"]
        L.append(f"- **vs {rival}** on {cat}: mean Δ {d:+.3f} over {n} tasks. Rival: break {s_r['break_rate']:.1%} "
                 f"/ flip {s_r['flip_rate']:.1%} / keep {s_r['keep_x']:.2f}x / cache {s_r['cache_share']:.1%} "
                 f"(ours: {s_o['break_rate']:.1%} / {s_o['flip_rate']:.1%} / {s_o['keep_x']:.2f}x / {s_o['cache_share']:.1%}). "
                 f"Biggest per-task losses: {worst}")
    L.append("")

    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    OUT_JSON.write_text(json.dumps(
        {"generated_from": SNAP.name, "categories": cats, "category_method": method,
         "stats": {k: {kk: vv for kk, vv in v.items() if kk != "per_task"} for k, v in stats.items()}},
        indent=1), encoding="utf-8")
    print(f"wrote {OUT_MD}")
    print(f"wrote {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
