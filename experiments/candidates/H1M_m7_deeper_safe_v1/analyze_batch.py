#!/usr/bin/env python3
"""Aggregate the latest H1M batch across runs-per-task; compare m7 vs h1m@deep by category;
emit the h1m@deep gate CSV. Pass/F2P/P2P from evaluation-summary.json (NOT output.jsonl)."""
import json, csv, re, statistics as st
from pathlib import Path
from collections import defaultdict

ROOT = Path("/Users/user/SOMA")
RD = sorted(ROOT.glob("experiments/runs/*_H1M_batch"), key=lambda p: p.stat().st_mtime)[-1]

cat = {}
if (RD / "tasks.tsv").exists():
    for line in (RD / "tasks.tsv").read_text().splitlines():
        if "\t" in line:
            inst, c = line.split("\t", 1); cat[inst] = c.strip()


def parse(name):
    prof = name.split("__", 1)[0]
    rest = name.split("__", 1)[1]
    return prof, rest.rsplit("__", 1)[0], rest.rsplit("__", 1)[1]


def metrics(d):
    pe = json.loads((d / "evaluation-summary.json").read_text()).get("patch_evaluation", {})
    p2ps, p2pt = pe.get("pass_to_pass_success"), pe.get("pass_to_pass_total")
    oj = json.loads((d / "output.jsonl").read_text().splitlines()[0])
    tu = (oj.get("metadata", {}) or {}).get("token_usage", {}) or {}
    tot = tu.get("total", {}) or {}
    cost = tot.get("cost")
    if not isinstance(cost, (int, float)):
        c = ((tu.get("trajectory_fallback", {}) or {}).get("total", {}) or {}).get("cost")
        cost = c.get("total") if isinstance(c, dict) else None
    return {"resolved": pe.get("resolved_count", 0),
            "broke": (p2ps is not None and p2pt is not None and p2ps < p2pt),
            "calls": tu.get("model_calls_count") or 0, "total": tot.get("total_tokens") or 0,
            "input": tot.get("input_tokens") or 0, "cache": tot.get("cache_read_tokens") or 0,
            "cost": cost or 0.0}


agg = defaultdict(list)
for d in sorted(RD.glob("*__r*")):
    if not (d / "evaluation-summary.json").exists():
        continue
    prof, inst, _ = parse(d.name)
    try:
        agg[(prof, inst)].append(metrics(d))
    except Exception as e:
        print(f"  ! skip {d.name}: {e}")

_ORDER = ["m7", "h1m_light", "h1m_medium", "h1m_deep", "h1m_king", "h1m_ultra",
          "h3_cache_safe", "h3_cache_king", "h3_cache_ultra"]
present = {k[0] for k in agg}
PROFS = [p for p in _ORDER if p in present] + sorted(present - set(_ORDER))
insts = sorted({k[1] for k in agg}, key=lambda i: (cat.get(i, "Z"), i))
by = defaultdict(dict)
print(f"# H1M batch — {RD.name}\n")
print(f"{'task':<24}{'cat':<12}{'prof':<14}{'runs':<5}{'resv':<8}{'broke':<6}{'calls':<7}{'total':<10}{'input':<9}{'cache_rd':<10}{'hit':<6}{'cost':<8}")
for inst in insts:
    for prof in PROFS:
        rs = agg.get((prof, inst))
        if not rs:
            continue
        n = len(rs); res = sum(r["resolved"] for r in rs); broke = sum(1 for r in rs if r["broke"])
        ac = st.mean(r["calls"] for r in rs); at = st.mean(r["total"] for r in rs); co = st.mean(r["cost"] for r in rs)
        ai = st.mean(r["input"] for r in rs); ach = st.mean(r["cache"] for r in rs)
        hit = ach / (ach + ai) if (ach + ai) else 0.0
        by[prof][inst] = {"n": n, "res": res, "broke": broke, "calls": ac, "total": at, "cost": co,
                          "input": ai, "cache": ach, "hit": hit}
        print(f"{inst.split('__')[-1]:<24}{cat.get(inst,'?'):<12}{prof:<14}{n:<5}{f'{res}/{n}':<8}{broke:<6}{ac:<7.1f}{at:<10.0f}{ai:<9.0f}{ach:<10.0f}{hit:<6.2f}{co:<8.4f}")
    print()

print("## Per-category: m7 vs h1m@deep")
for c in sorted(set(cat.values())):
    ci = [i for i in insts if cat.get(i) == c]
    for prof in PROFS:
        n = sum(by[prof].get(i, {}).get("n", 0) for i in ci)
        res = sum(by[prof].get(i, {}).get("res", 0) for i in ci)
        broke = sum(by[prof].get(i, {}).get("broke", 0) for i in ci)
        tot = [by[prof][i]["total"] for i in ci if i in by[prof]]
        inp = [by[prof][i]["input"] for i in ci if i in by[prof]]
        cah = [by[prof][i]["hit"] for i in ci if i in by[prof]]
        print(f"  {c:<12} {prof:<14} resolved {res}/{n}  neg {n-res}  broke {broke}  "
              f"avg_total {st.mean(tot) if tot else 0:.0f}  avg_input {st.mean(inp) if inp else 0:.0f}  "
              f"cache_hit {st.mean(cah) if cah else 0:.2f}")
    print()

# gate CSV for h1m@deep
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
for cand in [p for p in PROFS if p != "m7"]:
    out = RD / f"gate_{cand}_batch.csv"
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task", "pass", "neg_runs", "n_runs", "ratio", "score", "broke_baseline", "pairing_error", "missing_patch", "category"])
        for inst in insts:
            d, m = by[cand].get(inst), by["m7"].get(inst)
            if not d:
                continue
            num = re.search(r"(\d+)$", inst).group(1)
            m7r = mtx.get(num)
            ratio = round(m7r * (m["total"] / d["total"]), 3) if (m7r and m and d["total"]) else ""
            ccat = cat.get(inst, "")
            ccat = "Medium" if ccat == "Medium" else ("Hard" if ccat in ("Hard", "HardFragile") else ccat)
            w.writerow([inst, str(d["res"] >= (d["n"] + 1) // 2).lower(), d["n"] - d["res"], d["n"], ratio, "",
                        str(d["broke"] > 0 and not (m and m["broke"] > 0)).lower(), "false", "false", ccat])
    print(f"wrote {out}")
