#!/usr/bin/env python3
"""Per-run head-to-head m12 vs m12_1b for the run-stability regression.
Reads resolved (evaluation-summary.json) + tokens/calls (output.jsonl token_usage.total)
for every solve, groups by (profile, task) over the 5 runs, and reports: 5-run resolved
consistency (break-rate / flip consistency), Medium tok/call, per-task head-to-head."""
import json, sys, statistics as st
from pathlib import Path
from collections import defaultdict

RD = Path(sys.argv[1]) if len(sys.argv) > 1 else sorted(
    Path("/Users/user/SOMA").glob("experiments/runs/*_H1M_*batch"), key=lambda p: p.stat().st_mtime)[-1]
cat = {}
if (RD / "tasks.tsv").exists():
    for line in (RD / "tasks.tsv").read_text().splitlines():
        if "\t" in line:
            inst, c = line.split("\t", 1); cat[inst] = c.strip()

def solve_metrics(d):
    pe = json.loads((d / "evaluation-summary.json").read_text()).get("patch_evaluation", {})
    resolved = int(pe.get("resolved_count", 0))
    tu = (json.loads((d / "output.jsonl").read_text().splitlines()[0]).get("metadata", {}) or {}).get("token_usage", {}) or {}
    tot = tu.get("total", {}) or {}
    calls = tu.get("model_calls_count") or 0
    return {"resolved": resolved, "calls": calls,
            "total": tot.get("total_tokens") or 0, "input": tot.get("input_tokens") or 0,
            "output": tot.get("output_tokens") or 0, "cache": tot.get("cache_read_tokens") or 0}

# group: (prof, inst) -> list of per-run metrics
runs = defaultdict(list)
for d in sorted(RD.glob("*__r*")):
    if not (d / "evaluation-summary.json").exists():
        continue
    name = d.name; prof = name.split("__", 1)[0]; rest = name.split("__", 1)[1]
    inst = rest.rsplit("__", 1)[0]
    try:
        runs[(prof, inst)].append(solve_metrics(d))
    except Exception as e:
        print(f"  WARN parse {name}: {e}")

profs = sorted({p for p, _ in runs})
insts = sorted({i for _, i in runs})
def tokpercall(ms):
    cs = [m["calls"] for m in ms if m["calls"]]
    ts = [m["total"] for m in ms if m["calls"]]
    return (sum(ts) / sum(cs)) if cs else 0
def ipc(ms):  # (input+output) per call — the non-cached working tokens / call
    cs = [m["calls"] for m in ms if m["calls"]]
    io = [m["input"] + m["output"] for m in ms if m["calls"]]
    return (sum(io) / sum(cs)) if cs else 0

print(f"# Run-variance head-to-head — {RD.name}\n")
print(f"profiles: {profs}   tasks: {len(insts)}   runs/task: "
      f"{ {p: (len(runs[(p, insts[0])]) if (p, insts[0]) in runs else 0) for p in profs} }\n")

# ---- per-task head-to-head: resolved/5 ----
print("## Per-task resolved/5 (consistency) — m12 vs m12_1b")
print(f"{'task':<26}{'cat':<12}" + "".join(f"{p+' res/5':<14}" for p in profs) + "tok/call (m12 -> m12_1b)")
cat_resolved = defaultdict(lambda: defaultdict(int))   # cat -> prof -> resolved sum
cat_runs = defaultdict(lambda: defaultdict(int))
cat_tpc = defaultdict(lambda: defaultdict(list))
for inst in insts:
    c = cat.get(inst, "?")
    row = f"{inst.split('__')[-1]:<26}{c:<12}"
    tpc = {}
    for p in profs:
        ms = runs.get((p, inst), [])
        r = sum(m["resolved"] for m in ms); n = len(ms)
        row += f"{f'{r}/{n}':<14}"
        cat_resolved[c][p] += r; cat_runs[c][p] += n
        tpc[p] = tokpercall(ms); cat_tpc[c][p] += ms
    if "m12" in profs and "m12_1b" in profs:
        row += f"{tpc.get('m12',0):>9.0f} -> {tpc.get('m12_1b',0):<9.0f}"
    print(row)

# ---- per-category aggregate ----
print("\n## Per-category aggregate")
print(f"{'cat':<14}{'profile':<10}{'resolved':<12}{'tok/call':<11}{'(in+out)/call':<14}{'mean_total':<12}{'mean_calls':<10}")
for c in sorted(cat_resolved):
    for p in profs:
        ms = cat_tpc[c][p]
        mt = st.mean([m["total"] for m in ms]) if ms else 0
        mc = st.mean([m["calls"] for m in ms]) if ms else 0
        print(f"{c:<14}{p:<10}{f'{cat_resolved[c][p]}/{cat_runs[c][p]}':<12}"
              f"{tokpercall(ms):<11.0f}{ipc(ms):<14.0f}{mt:<12.0f}{mc:<10.1f}")

# ---- overall + the spec's deltas ----
print("\n## Overall + acceptance deltas")
for p in profs:
    allms = [m for (pp, _), lst in runs.items() if pp == p for m in lst]
    tot_res = sum(m["resolved"] for m in allms); tot_n = len(allms)
    print(f"  {p:<8} total resolved {tot_res}/{tot_n}   tok/call {tokpercall(allms):.0f}   (in+out)/call {ipc(allms):.0f}")

# Medium tok/call delta (the key gate)
def cat_tpc_val(c, p): return tokpercall(cat_tpc[c][p])
if "m12" in profs and "m12_1b" in profs:
    for c in ("Medium", "HardFragile", "Hard", "Easy"):
        if c in cat_resolved:
            a, b = cat_tpc_val(c, "m12"), cat_tpc_val(c, "m12_1b")
            d = 100 * (b - a) / a if a else 0
            print(f"  {c:<12} tok/call  m12={a:.0f}  m12_1b={b:.0f}  Δ={d:+.1f}%")
