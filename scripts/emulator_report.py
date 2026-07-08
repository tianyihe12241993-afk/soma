#!/usr/bin/env python3
"""comp-110 LOCAL SCREENER EMULATOR — detailed scoring report.

Scores candidate variants against the FIXED seeded baseline exactly the platform's way:
  Gate A: per task, majority of runs RESOLVED (graded via grade_patch_local.py reports); pass >=50% of tasks.
  Gate B: aggregate weighted savings (ratio-of-sums over all runs) >= 20%;
          weighted = 1*input + 0.1*cache_read + 3*output; baseline reference = MEAN of that task's seeds.
Also reports: raw savings, token splits, steps, output/step, per-task pass+savings, break runs,
sidecar in/out char ratio (from messages in/out captures), marker compliance of emitted content.

Usage: cd ~/joshua-work/SOMA-benchmark && python3 <this> [--variants f1kt,deep380] [--runs 2]
"""
from __future__ import annotations
import argparse, glob, json, os, re, statistics as st

TASKS = ["django-15103", "django-13964", "django-11551", "django-15375", "django-13516"]
MARK = re.compile(r"\[\[CMP\]\] source line \d+( ~ source line \d+ Omitted)? \[\[/CMP\]\]")
BAD = re.compile(r"\[\[(?!CMP\]\]|/CMP\]\])")   # any [[X other than the approved wrapper


def load(outdir):
    fp = os.path.join(outdir, "output.jsonl")
    if not os.path.exists(fp):
        return None
    try:
        d = json.load(open(fp))
    except Exception:
        return None
    m = d.get("metadata", {}) or {}; t = m.get("token_usage", {}) or {}
    i, c, o = t.get("input_tokens", 0), t.get("cache_read_tokens", 0), t.get("output_tokens", 0)
    rep = sorted(glob.glob(os.path.join(outdir, "localgrade.*.json")), key=os.path.getmtime)
    resolved = None
    if rep:
        rj = json.load(open(rep[-1]))          # latest grade wins (re-grades supersede flaky first grades)
        resolved = bool(rj.get("resolved_ids"))
    # sidecar ratio + marker compliance from message captures (miner runs)
    ratio = None; bad_markers = 0; n_mark = 0
    mi, mo = m.get("messages_in_path"), m.get("messages_out_path")
    def chars(p):
        tot = 0
        for line in open(p, errors="ignore"):
            line = line.strip()
            if not line: continue
            try: obj = json.loads(line)
            except: continue
            ms = obj.get("messages") if isinstance(obj, dict) else obj
            if not isinstance(ms, list): continue
            for msg in ms:
                cc = msg.get("content") if isinstance(msg, dict) else None
                if isinstance(cc, str): tot += len(cc)
                elif isinstance(cc, list):
                    for part in cc:
                        if isinstance(part, dict) and isinstance(part.get("text"), str): tot += len(part["text"])
        return tot
    try:
        if mi and mo and os.path.exists(mi) and os.path.exists(mo):
            ci, co = chars(mi), chars(mo)
            ratio = co / ci if ci else None
            txt = open(mo, errors="ignore").read()
            n_mark = len(MARK.findall(txt))
            bad_markers = len([x for x in re.findall(r"\[\[[^\]]{0,40}\]\]", txt)
                               if not (x.startswith("[[CMP]]") or x == "[[/CMP]]" or MARK.search(x))])
    except Exception:
        pass
    return {"resolved": resolved, "input": i, "cache": c, "output": o,
            "weighted": 1.0 * i + 0.1 * c + 3.0 * o, "raw": i + c + o,
            "steps": m.get("agent_steps") or 0, "sidecar_ratio": ratio,
            "markers": n_mark, "bad_markers": bad_markers}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", default="f1kt,deep380")
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--seed-runs", type=int, default=3)
    ap.add_argument("--seed-prefix", default="baseline_seed_")
    ap.add_argument("--cand-prefix", default="cand_")
    args = ap.parse_args()

    # fixed baseline: mean weighted/raw per task over seeds + pass record
    base = {}
    for t in TASKS:
        rows = [load(f"outputs/{args.seed_prefix}{t}_r{r}") for r in range(1, args.seed_runs + 1)]
        rows = [r for r in rows if r]
        base[t] = {"weighted": st.mean(x["weighted"] for x in rows) if rows else None,
                   "raw": st.mean(x["raw"] for x in rows) if rows else None,
                   "steps": [x["steps"] for x in rows],
                   "resolved": [x["resolved"] for x in rows], "n": len(rows)}
    print("=== FIXED BASELINE (seeds) ===")
    for t in TASKS:
        b = base[t]
        print(f"  {t:16s} n={b['n']} wt_mean={b['weighted']:.0f} raw_mean={b['raw']:.0f} steps={b['steps']} resolved={b['resolved']}")

    for V in args.variants.split(","):
        print(f"\n================ VARIANT {V} ================")
        MW = BW = MR = BR = 0.0
        task_pass = 0; all_rows = []; est_scores = []
        import math
        print(f"{'task':16s} {'run':3s} {'ok':5s} {'wt':>9s} {'sav%':>6s} {'raw%':>6s} {'in':>6s} {'cache':>8s} {'out':>6s} {'stp':>4s} {'o/s':>4s} {'mk':>5s} {'mk/kstp':>7s} {'cls':>5s} {'estS':>6s}")
        for t in TASKS:
            per = []
            for r in range(1, args.runs + 1):
                x = load(f"outputs/{args.cand_prefix}{V}_{t}_r{r}")
                if not x: print(f"  {t:16s} r{r} MISSING"); continue
                if x["raw"] == 0:   # zero-token dead run: platform = missing row = fatal; never 'savings'
                    print(f"{t:16s} r{r:<2d} DEAD-RUN (0 tokens, no patch) -> Gate A fail contribution, excluded from savings; ON PLATFORM THIS ALONE = NOT QUALIFIED")
                    per.append(x); continue
                bw, br = base[t]["weighted"], base[t]["raw"]
                MW += x["weighted"]; BW += bw; MR += x["raw"]; BR += br
                sav = (1 - x["weighted"] / bw) * 100; rsav = (1 - x["raw"] / br) * 100
                ops = x["output"] / x["steps"] if x["steps"] else 0
                per.append(x); all_rows.append((t, x, sav))
                # pp/break/flip/ff vs graded baseline (all seeds RESOLVED on these tasks → base pass=True)
                cls = "pp" if x["resolved"] else "BRK"
                base_v, lam = (1.0, 0.5) if x["resolved"] else (-4.0, 0.0)
                trim = max(-2.0, min(2.0, math.log(br / x["raw"]))) if x["raw"] else 0.0
                est = base_v + lam * trim
                est_scores.append(est)
                mden = x["markers"] / x["steps"] if x["steps"] else 0
                print(f"{t:16s} r{r:<2d} {str(x['resolved']):5s} {x['weighted']:9.0f} {sav:5.1f}% {rsav:5.1f}% {x['input']:6d} {x['cache']:8d} {x['output']:6d} "
                      f"{x['steps']:4d} {ops:4.0f} {x['markers']:5d} {mden:7.1f} {cls:>5s} {est:6.2f}"
                      + ("  ⚠BAD-MARKERS" if x["bad_markers"] else ""))
            res = [p["resolved"] for p in per if p["resolved"] is not None]
            if res and sum(res) > len(res) // 2:
                task_pass += 1
        n_tasks = len(TASKS)
        agg = (1 - MW / BW) * 100 if BW else 0
        ragg = (1 - MR / BR) * 100 if BR else 0
        gateA = task_pass >= (n_tasks + 1) // 2
        gateB = agg >= 20.0
        run_pass = [1 for (_, x, _) in all_rows if x["resolved"]]
        print(f"--- {V}: tasks majority-passed {task_pass}/{n_tasks} (Gate A {'PASS' if gateA else 'FAIL'}) | "
              f"runs resolved {len(run_pass)}/{len(all_rows)}")
        print(f"--- {V}: AGG WEIGHTED SAVINGS {agg:.1f}% (Gate B {'PASS' if gateB else 'FAIL'}, gate 20%) | raw {ragg:.1f}%")
        print(f"--- {V}: est platform-style score mean {st.mean(est_scores):.3f} (pp=+1+0.5·trim, BRK=−4; category-avg proxy)" if est_scores else "")
        print(f"--- {V}: VERDICT {'✅ QUALIFIES (emulator)' if gateA and gateB else '❌ not qualifying'}")
        if gateA and gateB:
            rec = "UPLOAD-CANDIDATE: run Codex audit + readiness"
        elif gateA and agg >= 15:
            rec = "TIGHTEN slightly or add runs to confirm margin"
        elif gateA:
            rec = "HOLD (Gate-A-clean but savings below gate; per stop-rule do not spend a hotkey)"
        else:
            rec = "LOOSEN (correctness regressed)"
        print(f"--- {V}: RECOMMENDATION → {rec}")


if __name__ == "__main__":
    main()
