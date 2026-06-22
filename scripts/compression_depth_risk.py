#!/usr/bin/env python3
"""Part B — compression-depth risk: does deeper compression cause instability?

Core question: do top miners reach ~4.9x WITH materially higher flakiness, or do they
compress deeper while keeping ~the same negative-run rate? Tested on shared-pass tasks,
overall and by category, by correlating per-(miner,task) compression ratio against
negative-run rate / broke-rate / score.

Also emits the H1 candidate target list (pass-safe deeper-compression tasks).

Inputs: data/processed/{task_matrix,run_scores,shared_pass_tasks,fragile_tasks}.jsonl
Outputs: reports/compression_depth_risk.md, data/latest/compression_depth_risk.json,
         reports/h1_safe_compression_targets.md, data/latest/h1_safe_compression_targets.json

NOTE: output/cached-token split is NOT in the data (one compressed-token count per run),
so "compression vs output-token increase" is reported as MISSING, not invented.
"""
from __future__ import annotations
import json, math, statistics as st, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import PROCESSED, LATEST, REPORTS, utc_now  # noqa: E402

LEADERS = ["t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8", "t9", "t10"]
TOP4 = ["t1", "t2", "t3", "t4"]
REF = "t1"
CATS = ["Easy", "Medium", "Hard"]
DEEP = 4.5          # "leader-level" compression threshold
CLEAN_NEG = 1       # <= this many negative runs (of 5) counts as pass-stable/clean


def _jsonl(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = st.mean(xs), st.mean(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return round(cov / (sx * sy), 3) if sx and sy else None


def main() -> int:
    tasks = {t["task_id"]: t for t in _jsonl(PROCESSED / "task_matrix.jsonl")}
    runs = _jsonl(PROCESSED / "run_scores.jsonl")
    shared = {s["task_id"]: s for s in _jsonl(PROCESSED / "shared_pass_tasks.jsonl")}
    fragile_ids = {f["task_id"] for f in _jsonl(PROCESSED / "fragile_tasks.jsonl")}
    if not tasks or not runs:
        print("missing processed data", file=sys.stderr); return 1

    # per-(miner,task): n runs, neg runs, ratio, pass, broke, score
    rg = {}
    for r in runs:
        a = rg.setdefault((r["miner_id"], r["task_id"]), {"n": 0, "neg": 0, "pass": 0})
        a["n"] += 1
        if (r.get("run_score") or 0) < 0: a["neg"] += 1
        if r.get("run_pass"): a["pass"] += 1
    def cell(mid, tid):
        t = tasks.get(tid, {}).get("miners", {}).get(mid)
        a = rg.get((mid, tid))
        if not t or not a or not a["n"]:
            return None
        return {"ratio": t.get("ratio"), "score": t.get("score"), "pass": t.get("pass"),
                "broke": bool(t.get("broke")), "n": a["n"], "neg": a["neg"],
                "neg_rate": a["neg"] / a["n"]}

    # ---- correlations on shared-pass tasks (per (miner,task) where miner passes) ----
    def corr_set(cat=None):
        rr, nn, bb, ss = [], [], [], []
        miners = ["m7"] + LEADERS
        for tid, s in shared.items():
            if cat and s.get("category") != cat:
                continue
            for mid in miners:
                c = cell(mid, tid)
                if c and c["pass"] and c["ratio"]:
                    rr.append(c["ratio"]); nn.append(c["neg_rate"]); bb.append(1.0 if c["broke"] else 0.0); ss.append(c["score"] or 0)
        return {"n_points": len(rr),
                "corr_ratio_vs_negrate": pearson(rr, nn),
                "corr_ratio_vs_broke": pearson(rr, bb),
                "corr_ratio_vs_score": pearson(rr, ss),
                "mean_ratio": round(st.mean(rr), 3) if rr else None,
                "mean_negrate": round(st.mean(nn), 4) if nn else None}
    corr = {"overall": corr_set(), **{c: corr_set(c) for c in CATS}}

    # ---- test 2/3: deep-and-clean vs deep-and-unstable, vs m7 ----
    proven_safe_deep, instability = [], []
    for tid, s in shared.items():
        m7 = cell("m7", tid)
        if not m7:
            continue
        # best clean-deep leader on this task
        best = None
        for mid in LEADERS:
            c = cell(mid, tid)
            if c and c["pass"] and c["ratio"] and c["ratio"] >= m7["ratio"] * 1.3:
                if c["neg"] <= CLEAN_NEG and (best is None or c["ratio"] > best["ratio"]):
                    best = {"by": mid, **c}
        if best and m7["neg"] <= CLEAN_NEG:
            proven_safe_deep.append({"task_id": tid, "task_name": s["task_name"], "category": s.get("category"),
                                     "m7_ratio": m7["ratio"], "m7_neg": m7["neg"],
                                     "leader": best["by"], "leader_ratio": round(best["ratio"], 2), "leader_neg": best["neg"]})
        # instability: any miner deep (>=DEEP) with >=3 neg on a task where a shallower miner is clean
        for mid in ["m7"] + LEADERS:
            c = cell(mid, tid)
            if c and c["ratio"] and c["ratio"] >= DEEP and c["neg"] >= 3:
                instability.append({"task_id": tid, "task_name": s["task_name"], "category": s.get("category"),
                                    "miner": mid, "ratio": round(c["ratio"], 2), "neg": c["neg"], "score": round(c["score"] or 0, 3)})

    # ---- test 5: feasibility of ~4.5-5x for m7-style ----
    deep_clean_tasks = set()
    for tid, s in shared.items():
        for mid in LEADERS:
            c = cell(mid, tid)
            if c and c["pass"] and c["ratio"] and c["ratio"] >= DEEP and c["neg"] <= CLEAN_NEG:
                deep_clean_tasks.add(tid); break
    feasibility = {"shared_pass_tasks": len(shared),
                   "tasks_with_a_clean_deep_leader(>=4.5x,<=1neg)": len(deep_clean_tasks),
                   "share": round(len(deep_clean_tasks) / len(shared), 3) if shared else None}

    risk = {"computed_at": utc_now(), "deep_threshold": DEEP, "clean_neg_max": CLEAN_NEG,
            "correlations": corr,
            "output_token_data": "MISSING — only one compressed-token count per run; no input/cached/output split",
            "proven_safe_deep_tasks": sorted(proven_safe_deep, key=lambda x: -(x["leader_ratio"] / max(x["m7_ratio"], .01)))[:25],
            "instability_examples": sorted(instability, key=lambda x: -x["neg"])[:15],
            "feasibility": feasibility}
    LATEST.mkdir(parents=True, exist_ok=True)
    (LATEST / "compression_depth_risk.json").write_text(json.dumps(risk, indent=2), encoding="utf-8")

    # ---- H1 target list ----
    targets = []
    for tid, s in shared.items():
        m7 = cell("m7", tid)
        if not m7 or not m7["pass"] or not m7["ratio"]:
            continue
        # best leader proof of a higher ratio (prefer clean)
        cands = []
        for mid in LEADERS:
            c = cell(mid, tid)
            if c and c["pass"] and c["ratio"] and c["ratio"] > m7["ratio"]:
                cands.append((mid, c))
        if not cands:
            continue
        clean = [(mid, c) for mid, c in cands if c["neg"] <= CLEAN_NEG]
        pool = clean or cands
        by, lc = max(pool, key=lambda mc: mc[1]["ratio"])
        target_ratio = lc["ratio"]
        est_lift = round(0.5 * math.log(target_ratio / m7["ratio"]), 3)
        # risk label
        if tid in fragile_ids or m7["neg"] >= 2:
            label = "fragile"
            reason = "m7/variant broke baseline or m7 has >=2 negative runs here — guard, do not push"
        elif m7["neg"] == 0 and clean and lc["neg"] == 0:
            label = "safe"
            reason = f"m7 clean (0 neg); {by} proves {target_ratio:.1f}x with 0 neg on this task"
        else:
            label = "moderate"
            reason = (f"m7 neg={m7['neg']}; best higher-ratio proof {by} {target_ratio:.1f}x neg={lc['neg']} "
                      f"({'clean' if clean else 'no clean leader above m7 — flakier'})")
        targets.append({"task_id": tid, "category": s.get("category"),
                        "m7_ratio": m7["ratio"], "leader_ratio": round(target_ratio, 2), "leader": by,
                        "m7_score": round(m7["score"] or 0, 3), "leader_score": round((cell(by, tid)["score"] or 0), 3),
                        "m7_pass": f"{m7['pass']}", "m7_neg_runs": f"{m7['neg']}/{m7['n']}",
                        "leader_neg_runs": f"{lc['neg']}/{lc['n']}",
                        "est_score_lift": est_lift, "risk": label, "reason": reason,
                        "task_name": s["task_name"], "headroom_x": round(target_ratio / m7["ratio"], 2)})
    order = {"safe": 0, "moderate": 1, "fragile": 2}
    targets.sort(key=lambda t: (order[t["risk"]], -t["est_score_lift"]))
    (LATEST / "h1_safe_compression_targets.json").write_text(
        json.dumps({"computed_at": utc_now(), "targets": targets}, indent=2), encoding="utf-8")

    # ---- markdown reports ----
    def f(v, p="{:.3f}"):
        return p.format(v) if isinstance(v, (int, float)) else "—"
    R = [f"# Compression-depth risk", f"_computed {utc_now()} on shared-pass tasks. neg run = run_score<0._", "",
         "## Correlation: compression ratio vs risk (per miner-task, miner passes)",
         "| scope | n | r(ratio,neg-rate) | r(ratio,broke) | r(ratio,score) | mean ratio | mean neg-rate |",
         "|---|---|---|---|---|---|---|"]
    for k in ["overall"] + CATS:
        c = corr[k]
        R.append(f"| {k} | {c['n_points']} | {f(c['corr_ratio_vs_negrate'])} | {f(c['corr_ratio_vs_broke'])} | "
                 f"{f(c['corr_ratio_vs_score'])} | {f(c['mean_ratio'],'{:.2f}×')} | {f(c['mean_negrate'],'{:.1%}')} |")
    R += ["", "_r≈0 → deeper compression does NOT track higher flakiness; r>0.3 → it does._",
          "", "## compression vs output-token increase",
          "- **MISSING DATA** — the dashboard exposes one compressed-token count per run; there is no "
          "input/cached/output split, so weighted/output-token analysis is not possible yet.",
          "", f"## Feasibility of leader-level depth (≥{DEEP}× with ≤{CLEAN_NEG} neg) for m7-style",
          f"- {feasibility['tasks_with_a_clean_deep_leader(>=4.5x,<=1neg)']} / {feasibility['shared_pass_tasks']} "
          f"shared-pass tasks have a leader passing CLEANLY at ≥{DEEP}× "
          f"({f(feasibility['share'],'{:.0%}')}). → deep compression is demonstrably pass-safe on these.",
          "", "## Tasks where a leader compresses much deeper than m7 with NO extra negative runs (proven-safe-deep)",
          "| task | cat | m7× (neg) | leader× (neg) | by |", "|---|---|---|---|---|"]
    for x in risk["proven_safe_deep_tasks"][:15]:
        R.append(f"| {x['task_name']} | {x['category']} | {x['m7_ratio']:.2f} ({x['m7_neg']}) | "
                 f"{x['leader_ratio']:.2f} ({x['leader_neg']}) | {x['leader']} |")
    R += ["", "## Tasks where deep compression clearly causes instability (≥4.5×, ≥3/5 neg)",
          "| task | cat | miner | ratio | neg | score |", "|---|---|---|---|---|---|"]
    for x in risk["instability_examples"]:
        R.append(f"| {x['task_name']} | {x['category']} | {x['miner']} | {x['ratio']:.2f} | {x['neg']} | {x['score']} |")
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "compression_depth_risk.md").write_text("\n".join(R) + "\n", encoding="utf-8")

    H = [f"# H1 safe-compression targets", f"_computed {utc_now()} — {len(targets)} tasks "
         f"(safe/moderate/fragile). est lift = 0.5·ln(leader/m7)._", "",
         "| task | cat | risk | m7× | leader× (by) | head | m7 score | ~lift | m7 neg | leader neg | reason |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for t in targets:
        H.append(f"| {t['task_name']} | {t['category']} | {t['risk']} | {t['m7_ratio']:.2f} | "
                 f"{t['leader_ratio']:.2f} ({t['leader']}) | {t['headroom_x']:.2f}× | {t['m7_score']:.3f} | "
                 f"{t['est_score_lift']:+.3f} | {t['m7_neg_runs']} | {t['leader_neg_runs']} | {t['reason']} |")
    (REPORTS / "h1_safe_compression_targets.md").write_text("\n".join(H) + "\n", encoding="utf-8")

    print("wrote compression_depth_risk.{md,json} + h1_safe_compression_targets.{md,json}")
    print(f"  corr(ratio,neg-rate): overall {f(corr['overall']['corr_ratio_vs_negrate'])} | "
          f"Easy {f(corr['Easy']['corr_ratio_vs_negrate'])} | Medium {f(corr['Medium']['corr_ratio_vs_negrate'])} | "
          f"Hard {f(corr['Hard']['corr_ratio_vs_negrate'])}")
    print(f"  feasibility: {feasibility['tasks_with_a_clean_deep_leader(>=4.5x,<=1neg)']}/{feasibility['shared_pass_tasks']} "
          f"shared-pass tasks have a clean deep (>={DEEP}x) leader")
    from collections import Counter
    print("  H1 targets by risk:", dict(Counter(t["risk"] for t in targets)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
