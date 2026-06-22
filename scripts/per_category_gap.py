#!/usr/bin/env python3
"""Part A — per-category gap report (m7 vs top miners), from existing processed data.

Inputs (no recollection):
  data/processed/task_matrix.jsonl      per-task per-miner aggregate (ratio/score/pass/broke)
  data/processed/run_scores.jsonl       per-run (run_score/run_pass) -> negative-run rate
  data/processed/shared_pass_tasks.jsonl  m7-vs-reference shared-pass decomposition (+proven ratio)
  data/processed/fragile_tasks.jsonl

Leaders = top-4 by overall (config/top_miners.yaml order t1..t4). "Negative run" = run_score < 0.
Outputs: reports/per_category_gap.md, data/latest/per_category_gap.json
"""
from __future__ import annotations
import json, math, statistics as st, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import PROCESSED, LATEST, REPORTS, utc_now, load_top_miners  # noqa: E402

CATS = ["Easy", "Medium", "Hard"]
LEADERS = ["t1", "t2", "t3", "t4"]          # top-4 by overall
REF = "t1"                                   # primary reference (overall leader)


def _jsonl(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def main() -> int:
    tasks = _jsonl(PROCESSED / "task_matrix.jsonl")
    runs = _jsonl(PROCESSED / "run_scores.jsonl")
    shared = _jsonl(PROCESSED / "shared_pass_tasks.jsonl")
    fragile = _jsonl(PROCESSED / "fragile_tasks.jsonl")
    if not tasks or not runs:
        print("missing task_matrix/run_scores — run import+normalize first", file=sys.stderr)
        return 1

    # per-(miner,task) run aggregates
    rg = {}
    for r in runs:
        a = rg.setdefault((r["miner_id"], r["task_id"]), {"n": 0, "neg": 0, "pass": 0})
        a["n"] += 1
        if (r.get("run_score") or 0) < 0: a["neg"] += 1
        if r.get("run_pass"): a["pass"] += 1

    def neg_rate(miner_ids, cat):
        n = neg = 0
        for r in runs:
            if r["miner_id"] in miner_ids and r.get("category") == cat and r.get("run_score") is not None:
                n += 1
                if r["run_score"] < 0: neg += 1
        return (neg / n) if n else None

    by_cat = {}
    for cat in CATS:
        ct = [t for t in tasks if t.get("category") == cat]
        def avg_score(mid):
            v = [t["miners"][mid]["score"] for t in ct if mid in t["miners"] and t["miners"][mid].get("score") is not None]
            return st.mean(v) if v else None
        def avg_ratio(mid):
            v = [t["miners"][mid]["ratio"] for t in ct if mid in t["miners"] and t["miners"][mid].get("ratio")]
            return st.mean(v) if v else None
        def broke(mid):
            return sum(1 for t in ct if mid in t["miners"] and t["miners"][mid].get("broke"))
        m7_s = avg_score("m7")
        lead_s = st.mean([s for s in (avg_score(m) for m in LEADERS) if s is not None])
        m7_r = avg_ratio("m7")
        lead_r = st.mean([r for r in (avg_ratio(m) for m in LEADERS) if r is not None])
        sp = [s for s in shared if s.get("category") == cat]
        by_cat[cat] = {
            "tasks": len(ct),
            "m7_avg_score": round(m7_s, 4) if m7_s is not None else None,
            "leader_avg_score": round(lead_s, 4),
            "score_gap": round(lead_s - m7_s, 4) if m7_s is not None else None,
            "m7_avg_ratio": round(m7_r, 3) if m7_r else None,
            "leader_avg_ratio": round(lead_r, 3),
            "m7_neg_run_rate": round(neg_rate({"m7"}, cat), 4) if neg_rate({"m7"}, cat) is not None else None,
            "leader_neg_run_rate": round(neg_rate(set(LEADERS), cat), 4) if neg_rate(set(LEADERS), cat) is not None else None,
            "m7_broke": broke("m7"),
            "leader_broke_total": sum(broke(m) for m in LEADERS),
            "shared_pass_tasks": len(sp),
            "shared_pass_mean_gap": round(st.mean([x["actual_score_gap"] for x in sp]), 4) if sp else None,
            "shared_pass_ratio_explained": round(st.mean([x["ratio_explained_gap"] for x in sp]), 4) if sp else None,
            "shared_pass_residual": round(st.mean([x["residual_gap"] for x in sp]), 4) if sp else None,
        }

    # ---- task lists ----
    def pass_stable(mid, tid):
        a = rg.get((mid, tid))
        return bool(a and a["neg"] == 0 and a["pass"] == a["n"] and a["n"] > 0)

    def undercompressed(cat, n=10):
        out = []
        for s in shared:
            if s.get("category") != cat:
                continue
            if not pass_stable("m7", s["task_id"]):     # m7 must be pass-stable to push safely
                continue
            if s["proven_max_ratio"] and s["proven_max_ratio"] > s["m7_ratio"]:
                gain = 0.5 * math.log(s["proven_max_ratio"] / s["m7_ratio"])
                out.append({"task_id": s["task_id"], "task_name": s["task_name"],
                            "m7_ratio": s["m7_ratio"], "proven_ratio": s["proven_max_ratio"],
                            "proven_by": s["proven_by"], "headroom_x": s["safe_headroom_x"],
                            "m7_score": s["m7_score"], "est_gain": round(gain, 3)})
        return sorted(out, key=lambda x: -x["est_gain"])[:n]

    fragile_top = sorted(fragile, key=lambda f: (not f.get("m7_broke"),
                         f.get("severity") if f.get("severity") is not None else 0))[:10]
    # catastrophic Hard-gap: Hard tasks by (leader ref score - m7 score)
    hard_gap = []
    for t in tasks:
        if t.get("category") != "Hard":
            continue
        m7 = t["miners"].get("m7"); ref = t["miners"].get(REF)
        if m7 and ref and m7.get("score") is not None and ref.get("score") is not None:
            hard_gap.append({"task_id": t["task_id"], "task_name": t["task_name"],
                             "m7_score": round(m7["score"], 3), "leader_score": round(ref["score"], 3),
                             "gap": round(ref["score"] - m7["score"], 3),
                             "m7_ratio": m7.get("ratio"), "leader_ratio": ref.get("ratio")})
    hard_gap = sorted(hard_gap, key=lambda x: -x["gap"])[:10]

    out = {"computed_at": utc_now(), "leaders": LEADERS, "reference": REF,
           "by_category": by_cat,
           "under_compressed_medium": undercompressed("Medium"),
           "under_compressed_hard": undercompressed("Hard"),
           "fragile_top": fragile_top, "catastrophic_hard_gap": hard_gap}
    LATEST.mkdir(parents=True, exist_ok=True)
    (LATEST / "per_category_gap.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    # ---- markdown ----
    def f(v, p="{:.3f}"):
        return p.format(v) if isinstance(v, (int, float)) else "—"
    L = [f"# Per-category gap — m7 vs top-4 leaders ({', '.join(LEADERS)})",
         f"_computed {utc_now()} from processed data. Negative run = run_score < 0._", "",
         "| metric | Easy | Medium | Hard |", "|---|---|---|---|"]
    def row(label, key, p="{:.3f}"):
        return f"| {label} | " + " | ".join(f(by_cat[c][key], p) for c in CATS) + " |"
    L += [row("m7 avg score", "m7_avg_score"),
          row("leader avg score", "leader_avg_score"),
          row("**score gap**", "score_gap"),
          row("m7 avg ratio", "m7_avg_ratio", "{:.2f}×") if False else
          "| m7 avg ratio | " + " | ".join(f(by_cat[c]["m7_avg_ratio"], "{:.2f}×") for c in CATS) + " |",
          "| leader avg ratio | " + " | ".join(f(by_cat[c]["leader_avg_ratio"], "{:.2f}×") for c in CATS) + " |",
          "| m7 neg-run rate | " + " | ".join(f(by_cat[c]["m7_neg_run_rate"], "{:.1%}") for c in CATS) + " |",
          "| leader neg-run rate | " + " | ".join(f(by_cat[c]["leader_neg_run_rate"], "{:.1%}") for c in CATS) + " |",
          row("m7 broke-baseline", "m7_broke", "{:d}"),
          row("leader broke (t1-4 sum)", "leader_broke_total", "{:d}"),
          row("shared-pass tasks", "shared_pass_tasks", "{:d}"),
          row("shared-pass mean gap", "shared_pass_mean_gap"),
          row("…ratio-explained", "shared_pass_ratio_explained"),
          row("…residual", "shared_pass_residual")]

    def tasklist(title, rows, cols, fmts):
        out = ["", f"## {title}", "| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
        for r in rows:
            out.append("| " + " | ".join(fmts[i](r) for i in range(len(cols))) + " |")
        return out
    L += tasklist("Top 10 Medium — under-compressed but pass-stable", out["under_compressed_medium"],
                  ["task", "m7×", "proven×", "by", "head", "m7 score", "~gain"],
                  [lambda r: r["task_name"], lambda r: f"{r['m7_ratio']:.2f}", lambda r: f"{r['proven_ratio']:.2f}",
                   lambda r: r["proven_by"], lambda r: f"{r['headroom_x']:.2f}×", lambda r: f"{(r['m7_score'] or 0):.3f}",
                   lambda r: f"{r['est_gain']:+.3f}"])
    L += tasklist("Top 10 Hard — under-compressed but pass-stable", out["under_compressed_hard"],
                  ["task", "m7×", "proven×", "by", "head", "m7 score", "~gain"],
                  [lambda r: r["task_name"], lambda r: f"{r['m7_ratio']:.2f}", lambda r: f"{r['proven_ratio']:.2f}",
                   lambda r: r["proven_by"], lambda r: f"{r['headroom_x']:.2f}×", lambda r: f"{(r['m7_score'] or 0):.3f}",
                   lambda r: f"{r['est_gain']:+.3f}"])
    L += tasklist("Top fragile tasks (m7/variants broke a passing baseline)", fragile_top,
                  ["task", "cat", "broke_by", "m7_broke", "severity"],
                  [lambda r: r["task_name"], lambda r: str(r.get("category")), lambda r: ",".join(r["broke_by"]),
                   lambda r: "yes" if r["m7_broke"] else "", lambda r: f"{(r.get('severity') or 0):.2f}"])
    L += tasklist("Top catastrophic Hard-gap tasks (leader − m7)", hard_gap,
                  ["task", "m7 score", "leader score", "gap", "m7×", "leader×"],
                  [lambda r: r["task_name"], lambda r: f"{r['m7_score']:.3f}", lambda r: f"{r['leader_score']:.3f}",
                   lambda r: f"{r['gap']:+.3f}", lambda r: f"{(r['m7_ratio'] or 0):.2f}", lambda r: f"{(r['leader_ratio'] or 0):.2f}"])
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "per_category_gap.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("wrote reports/per_category_gap.md + data/latest/per_category_gap.json")
    for c in CATS:
        b = by_cat[c]
        print(f"  {c:>6}: gap {f(b['score_gap'])}  m7 {f(b['m7_avg_ratio'],'{:.2f}×')} vs lead "
              f"{f(b['leader_avg_ratio'],'{:.2f}×')}  negrun m7 {f(b['m7_neg_run_rate'],'{:.1%}')} "
              f"lead {f(b['leader_neg_run_rate'],'{:.1%}')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
