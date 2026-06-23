#!/usr/bin/env python3
"""Analyze the latest H1M smoke run: compare m7 / h1m@medium / h1m@deep on the
real eval artifacts, and emit per-profile gate CSVs (pass from evaluation-summary.json,
NOT output.jsonl metadata.resolved). Weighted tokens = cost-rate input-equivalents."""
import json, csv, re, statistics as st
from pathlib import Path

ROOT = Path("/Users/user/SOMA")
RD = sorted(ROOT.glob("experiments/runs/*_H1M_smoke_real_eval"), key=lambda p: p.stat().st_mtime)[-1]
TASKS = ["django__django-10914", "django__django-15851"]
PROFILES = ["m7", "h1m@medium", "h1m@deep"]
DIR = {"m7": "m7", "h1m@medium": "h1m_medium", "h1m@deep": "h1m_deep"}


def load(prof, task):
    d = RD / f"{DIR[prof]}__{task}"
    es = json.loads((d / "evaluation-summary.json").read_text())
    pe = es.get("patch_evaluation", {})
    oj = json.loads((d / "output.jsonl").read_text().splitlines()[0])
    tu = (oj.get("metadata", {}) or {}).get("token_usage", {}) or {}
    tot = tu.get("total", {}) or {}
    cost, cb = tot.get("cost"), None
    if not isinstance(cost, dict):
        tf = (tu.get("trajectory_fallback", {}) or {}).get("total", {}) or {}
        cost = tf.get("cost")
    if isinstance(cost, dict):
        cb, cost = cost, cost.get("total")
    inp, out, cache = tot.get("input_tokens") or 0, tot.get("output_tokens") or 0, tot.get("cache_read_tokens") or 0
    # weighted tokens: input-equivalents using the solve's own cost rates (output pricier, cache ~free)
    rin = (cb["input"] / inp) if (cb and inp and cb.get("input")) else None
    weighted = round((cost or 0) / rin) if rin else (inp + out + cache)
    return {"prof": prof, "task": task, "resolved": pe.get("resolved_count", 0),
            "f2p": f"{pe.get('fail_to_pass_success')}/{pe.get('fail_to_pass_total')}",
            "p2p": f"{pe.get('pass_to_pass_success')}/{pe.get('pass_to_pass_total')}",
            "calls": tu.get("model_calls_count"), "input": inp, "cache": cache, "output": out,
            "total": tot.get("total_tokens") or (inp + out + cache), "weighted": weighted,
            "cost": round(cost or 0.0, 5)}


R = {(p, t): load(p, t) for p in PROFILES for t in TASKS}

# m7 platform ratio per task (to ground the gate's absolute ratio)
mtx = {}
p = ROOT / "data/processed/task_matrix.jsonl"
if p.exists():
    for line in p.read_text().splitlines():
        if not line.strip():
            continue
        t = json.loads(line)
        num = (re.search(r"(\d+)\s*$", t.get("task_name", "") or "") or [None, None])[1] if t.get("task_name") else None
        if num:
            mtx[num] = (t["miners"].get("m7", {}) or {}).get("ratio")

print(f"# H1M smoke analysis — {RD.name}\n")
hdr = ["profile", "task", "resolved", "F2P", "P2P", "calls", "input", "cache", "output", "total", "wtd_tok", "cost$"]
print("  ".join(f"{h:>10}" for h in hdr))
for t in TASKS:
    for p_ in PROFILES:
        r = R[(p_, t)]
        print("  ".join(f"{str(v):>10}" for v in
              [p_, t.split('-')[-1], r["resolved"], r["f2p"], r["p2p"], r["calls"],
               r["input"], r["cache"], r["output"], r["total"], r["weighted"], r["cost"]]))
    print()

# per-profile averages + reduction vs m7 (same-task), and gate CSVs
print("## Averages over the 2 tasks + reduction vs m7 (same tasks)")
m7avg = {k: st.mean([R[("m7", t)][k] for t in TASKS]) for k in ("total", "weighted", "cost", "calls")}
for p_ in PROFILES:
    a = {k: st.mean([R[(p_, t)][k] for t in TASKS]) for k in ("total", "weighted", "cost", "calls")}
    passes = sum(R[(p_, t)]["resolved"] for t in TASKS)
    red_tot = (m7avg["total"] - a["total"]) / m7avg["total"] * 100
    red_wt = (m7avg["weighted"] - a["weighted"]) / m7avg["weighted"] * 100
    red_cost = (m7avg["cost"] - a["cost"]) / m7avg["cost"] * 100
    print(f"  {p_:>11}: resolved {passes}/2 | avg total {a['total']:.0f} ({red_tot:+.1f}% vs m7) | "
          f"wtd {a['weighted']:.0f} ({red_wt:+.1f}%) | cost ${a['cost']:.4f} ({red_cost:+.1f}%) | calls {a['calls']:.1f}")

# build gate CSVs (one per candidate profile)
for prof in ("h1m@medium", "h1m@deep"):
    rows = []
    for t in TASKS:
        c, m = R[(prof, t)], R[("m7", t)]
        num = t.split("-")[-1]
        m7ratio = mtx.get(num)
        # real-grounded candidate ratio: m7 platform ratio scaled by measured token reduction vs m7
        ratio = round(m7ratio * (m["total"] / c["total"]), 3) if (m7ratio and c["total"]) else ""
        rows.append({"task": t, "pass": str(bool(c["resolved"])).lower(),
                     "neg_runs": 0 if c["resolved"] else 1, "n_runs": 1, "ratio": ratio,
                     "score": "", "broke_baseline": str(bool(m["resolved"] and not c["resolved"])).lower(),
                     "pairing_error": "false", "missing_patch": str(c["total"] == 0).lower(),
                     "category": "Medium"})
    out = RD / f"gate_{DIR[prof]}.csv"
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {out}")
