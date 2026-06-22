#!/usr/bin/env python3
"""H1M real-task experiment runner (offline-honest).

Builds an experiments/runs/<stamp>_H1M_eval/ run that:
  * computes the REAL m7 baseline on the exact target tasks (pass/ratio/score/neg-run/
    broke) from data/processed/{task_matrix,run_scores}.jsonl  -> source=platform
  * attaches the OFFLINE candidate proxy (compression-ratio + safety deltas measured by
    h1m_eval.py in data/latest/h1m_candidate_results.json) and a per-target ratio/score
    PROJECTION (m7_ratio * (1+offline_pct))  -> source=estimate (manual interpretation)
  * marks candidate real pass-rate/neg-run/broke as PENDING_EVAL (needs SOMA SWE-bench;
    the raw per-call task contexts are not available offline) -- never invented
  * if --results <file> (a real per-task candidate export) is given, ingests it and
    computes full candidate metrics + applies the FULL decision gate.

Usage:
  python h1m_run.py                       # baseline + offline proxy/projection
  python h1m_run.py --results runs.csv    # + real candidate metrics (from an eval)
"""
from __future__ import annotations
import argparse, csv, json, math, statistics as st, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from _common import PROCESSED, LATEST, REPORTS, utc_now, utc_stamp  # noqa: E402

RUNS = ROOT / "experiments" / "runs"
MEDIUM_FIRST = ["15851", "11119", "24539", "14580", "14855", "10914", "11603"]
FRAGILE = ["17139", "16766", "11239", "14493"]
SOLVING_GAP = ["14999", "22714"]
PROFILES = ["h1m@medium", "h1m@deep"]
MIN_RATIO_IMPROVE = 0.08      # gate: >=8%


def _jsonl(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def _num(task_name):
    import re
    m = re.search(r"(\d+)\s*$", task_name or "")
    return m.group(1) if m else None


def _to_bool(v):
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("true", "1", "yes", "y", "t")


def load_candidate_results(path):
    """Parse a REAL per-task candidate export (csv/json) -> normalized rows.
    Columns: task (id/name), pass, neg_runs, n_runs, ratio, score, broke_baseline,
    pairing_error, missing_patch, [category]. This is the ingestion of SOMA-eval output."""
    raw = path.read_text(encoding="utf-8")
    if raw.lstrip().startswith(("{", "[")):
        obj = json.loads(raw)
        rows = obj.get("rows", obj) if isinstance(obj, dict) else obj
    else:
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
    out = []
    for r in rows:
        def g(*keys):
            for k in keys:
                if r.get(k) not in (None, ""):
                    return r[k]
            return None
        task = str(g("task", "task_name", "task_id") or "").strip()
        rv, sv = g("ratio", "compression_ratio"), g("score", "platform_score")
        out.append({
            "task": task, "num": _num(task),
            "pass": _to_bool(g("pass", "miner_pass")),
            "n_runs": int(float(g("n_runs") or 5)),
            "neg_runs": int(float(g("neg_runs") or 0)),
            "ratio": float(rv) if rv is not None else None,
            "score": float(sv) if sv is not None else None,
            "broke_baseline": _to_bool(g("broke_baseline", "broke")),
            "pairing_error": _to_bool(g("pairing_error")),
            "missing_patch": _to_bool(g("missing_patch")),
            "category": g("category"),
        })
    return out


def candidate_rows(group_tasks, cand_by_num):
    """Join candidate results to the m7 baseline, per task in a group."""
    rows = []
    for t in group_tasks:
        c = cand_by_num.get(_num(t.get("task_name")))
        if not c:
            continue
        m7 = t["miners"].get("m7", {})
        rows.append({
            "task_name": t["task_name"], "category": c.get("category") or t.get("category"),
            "m7_ratio": m7.get("ratio"), "m7_score": m7.get("score"), "m7_broke": bool(m7.get("broke")),
            "cand_ratio": c["ratio"], "cand_score": c["score"], "cand_pass": c["pass"],
            "cand_neg_runs": c["neg_runs"], "cand_n_runs": c["n_runs"], "cand_broke": c["broke_baseline"],
            "pairing_error": c["pairing_error"], "missing_patch": c["missing_patch"],
            "score_delta": round(c["score"] - m7["score"], 3) if (c["score"] is not None and m7.get("score") is not None) else None,
            "new_broke": bool(c["broke_baseline"] and not m7.get("broke")),
            "source": "real_candidate",
        })
    return rows


def aggregate_candidate(rows, cat=None):
    rs = [r for r in rows if (cat is None or r["category"] == cat)]
    if not rs:
        return {}
    ratios = [r["cand_ratio"] for r in rs if r["cand_ratio"]]
    scores = [r["cand_score"] for r in rs if r["cand_score"] is not None]
    tot_n = sum(r["cand_n_runs"] for r in rs)
    tot_neg = sum(r["cand_neg_runs"] for r in rs)
    return {
        "n": len(rs), "pass_rate": round(sum(1 for r in rs if r["cand_pass"]) / len(rs), 3),
        "neg_run_rate": round(tot_neg / tot_n, 4) if tot_n else 0.0,
        "broke_baseline_count": sum(1 for r in rs if r["cand_broke"]),
        "new_broke_count": sum(1 for r in rs if r["new_broke"]),
        "negative_score_count": sum(1 for r in rs if (r["cand_score"] or 0) < 0),
        "avg_ratio": round(st.mean(ratios), 3) if ratios else None,
        "median_ratio": round(st.median(ratios), 3) if ratios else None,
        "avg_score": round(st.mean(scores), 3) if scores else None,
        "pairing_errors": sum(1 for r in rs if r["pairing_error"]),
        "missing_patch": sum(1 for r in rs if r["missing_patch"]),
    }


def full_gate(mf_rows, fragile_rows, base_mf, min_ratio=0.08, neg_margin=0.05):
    """The FULL decision gate applied to REAL candidate results vs the m7 baseline."""
    mf = aggregate_candidate(mf_rows)
    med = aggregate_candidate(mf_rows, "Medium")
    checks = []
    new_breaks = mf.get("new_broke_count", 0) + sum(1 for r in fragile_rows if r["new_broke"])
    checks.append(("no_new_broken_baseline_vs_m7", "REJECT" if new_breaks > 0 else "PASS",
                   f"{new_breaks} new break(s)"))
    impr = (mf["avg_ratio"] / base_mf["avg_ratio"] - 1) if (mf.get("avg_ratio") and base_mf.get("avg_ratio")) else None
    checks.append(("compression_improvement>=8%",
                   "PASS" if (impr is not None and impr >= min_ratio) else "REJECT",
                   f"{impr*100:+.1f}%" if impr is not None else "n/a"))
    mnr, base_mnr = med.get("neg_run_rate", 0.0), (base_mf.get("medium_neg_run_rate") or 0.0)
    checks.append(("medium_neg_run_not_up", "REJECT" if (mnr - base_mnr) > neg_margin else "PASS",
                   f"cand {mnr:.1%} vs m7 {base_mnr:.1%}"))
    msc, bsc = med.get("avg_score"), base_mf.get("medium_est_score")
    checks.append(("medium_est_score_no_drop",
                   "REJECT" if (msc is not None and bsc is not None and msc < bsc) else "PASS",
                   f"cand {msc} vs m7 {bsc}"))
    integ = (mf.get("pairing_errors", 0) + mf.get("missing_patch", 0)
             + sum(1 for r in fragile_rows if r["pairing_error"] or r["missing_patch"]))
    checks.append(("no_pairing_or_missing_patch_errors", "REJECT" if integ > 0 else "PASS",
                   f"{integ} integrity error(s)"))
    rejects = [c[0] for c in checks if c[1] == "REJECT"]
    return {"decision": "REJECT" if rejects else "ACCEPT for next-stage evaluation",
            "checks": checks, "rejected_on": rejects,
            "medium_first_metrics": mf, "medium_metrics": med}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", help="real candidate per-task results (csv/json) from a SOMA eval")
    args = ap.parse_args()

    matrix = {t["task_id"]: t for t in _jsonl(PROCESSED / "task_matrix.jsonl")}
    runs = _jsonl(PROCESSED / "run_scores.jsonl")
    offline = json.loads((LATEST / "h1m_candidate_results.json").read_text(encoding="utf-8"))
    pct = {"h1m@medium": offline["summary"]["h1m@medium"]["mean_pct_vs_m7"],
           "h1m@deep": offline["summary"]["h1m@deep"]["mean_pct_vs_m7"]}
    safe = {"h1m@medium": offline["summary"]["h1m@medium"],
            "h1m@deep": offline["summary"]["h1m@deep"]}

    # m7 per-(task) neg-run rate from run_scores
    negrun = {}
    for r in runs:
        if r["miner_id"] == "m7":
            a = negrun.setdefault(r["task_id"], {"n": 0, "neg": 0})
            a["n"] += 1
            if (r.get("run_score") or 0) < 0:
                a["neg"] += 1

    name_by_num = {}
    for tid, t in matrix.items():
        nm = _num(t.get("task_name"))
        if nm:
            name_by_num[nm] = t

    def group_tasks(nums):
        return [name_by_num[n] for n in nums if n in name_by_num]

    def m7_baseline(tasks):
        m7 = [t["miners"].get("m7") for t in tasks if t["miners"].get("m7")]
        ratios = [m["ratio"] for m in m7 if m.get("ratio")]
        scores = [m["score"] for m in m7 if m.get("score") is not None]
        meds = [t for t in tasks if t.get("category") == "Medium"]
        med_r = [t["miners"]["m7"]["ratio"] for t in meds if t["miners"].get("m7", {}).get("ratio")]
        med_s = [t["miners"]["m7"]["score"] for t in meds if t["miners"].get("m7", {}).get("score") is not None]
        tot_n = sum(negrun.get(t["task_id"], {}).get("n", 0) for t in tasks)
        tot_neg = sum(negrun.get(t["task_id"], {}).get("neg", 0) for t in tasks)
        mn = sum(negrun.get(t["task_id"], {}).get("n", 0) for t in meds)
        mneg = sum(negrun.get(t["task_id"], {}).get("neg", 0) for t in meds)
        return {
            "n_tasks": len(tasks),
            "pass_rate": round(sum(1 for m in m7 if m.get("pass")) / len(m7), 3) if m7 else None,
            "neg_run_rate": round(tot_neg / tot_n, 4) if tot_n else None,
            "broke_baseline_count": sum(1 for m in m7 if m.get("broke")),
            "negative_score_count": sum(1 for m in m7 if (m.get("score") or 0) < 0),
            "avg_ratio": round(st.mean(ratios), 3) if ratios else None,
            "median_ratio": round(st.median(ratios), 3) if ratios else None,
            "medium_ratio": round(st.mean(med_r), 3) if med_r else None,
            "medium_est_score": round(st.mean(med_s), 3) if med_s else None,
            "medium_neg_run_rate": round(mneg / mn, 4) if mn else 0.0,
            "avg_score": round(st.mean(scores), 3) if scores else None,
        }

    def projection(base, prof):
        p = pct[prof]
        return {
            "source": "estimate (offline proxy x m7 baseline; NOT a real eval)",
            "offline_ratio_pct_vs_m7": p,
            "proj_avg_ratio": round(base["avg_ratio"] * (1 + p), 3) if base["avg_ratio"] else None,
            "proj_medium_ratio": round(base["medium_ratio"] * (1 + p), 3) if base["medium_ratio"] else None,
            "est_score_delta_per_task": round(0.5 * math.log(1 + p), 3),
            "offline_all_protected": safe[prof]["all_protected"],
            "offline_orphans_ok": safe[prof]["orphans_ok"],
            "real_pass_rate": "PENDING_EVAL", "real_neg_run_rate": "PENDING_EVAL",
            "real_broke_baseline": "PENDING_EVAL", "real_negative_score": "PENDING_EVAL",
        }

    groups = {"medium_first": group_tasks(MEDIUM_FIRST),
              "fragile_guard": group_tasks(FRAGILE),
              "solving_gap_excluded": group_tasks(SOLVING_GAP)}

    metrics = {"computed_at": utc_now(), "candidate": "H1M_m7_deeper_safe_v1",
               "profiles": ["m7"] + PROFILES,
               "data_basis": "REAL m7 baseline (platform scrape) + OFFLINE candidate proxy/projection. "
                             "Candidate real pass/neg-run/broke = PENDING_EVAL (needs SOMA SWE-bench env; "
                             "raw per-call task contexts unavailable offline). No scores invented.",
               "groups": {}}
    for gname, gtasks in groups.items():
        base = m7_baseline(gtasks)
        entry = {"tasks": [t["task_name"] for t in gtasks], "m7_baseline": base}
        if gname != "solving_gap_excluded":
            for prof in PROFILES:
                entry[prof] = projection(base, prof)
                if gname == "fragile_guard":
                    entry[prof]["expected_behavior"] = ("fragile guard -> fall back to m7 (no deepening); "
                                                        "VERIFY on eval. offline: guard fired on error-dense signature")
        metrics["groups"][gname] = entry

    # ---- per-task results (real m7 + projection) ----
    task_rows = []
    for gname in ("medium_first", "fragile_guard"):
        for t in groups[gname]:
            m7 = t["miners"].get("m7", {})
            nr = negrun.get(t["task_id"], {})
            row = {"group": gname, "task_id": t["task_id"], "task_name": t["task_name"],
                   "category": t.get("category"), "m7_pass": m7.get("pass"),
                   "m7_ratio": m7.get("ratio"), "m7_score": m7.get("score"),
                   "m7_broke": bool(m7.get("broke")),
                   "m7_neg_runs": f"{nr.get('neg', 0)}/{nr.get('n', 0)}"}
            for prof in PROFILES:
                p = pct[prof]
                guard = gname == "fragile_guard"
                row[f"{prof}_proj_ratio"] = (round(m7.get("ratio", 0), 3) if guard
                                             else round((m7.get("ratio") or 0) * (1 + p), 3))
                row[f"{prof}_est_score_delta"] = 0.0 if guard else round(0.5 * math.log(1 + p), 3)
                row[f"{prof}_real_pass"] = "PENDING_EVAL"
                row[f"{prof}_real_neg_runs"] = "PENDING_EVAL"
            task_rows.append(row)

    # ---- decision gate (offline-measurable + projection; real parts pending) ----
    def gate(prof):
        p = pct[prof]
        med = metrics["groups"]["medium_first"]["m7_baseline"]
        verdicts = []
        verdicts.append(("compression_improvement>=8%",
                         "PASS" if p >= MIN_RATIO_IMPROVE else "REJECT", f"offline +{p*100:.1f}%"))
        verdicts.append(("fragile_guard_works",
                         "PASS" if safe[prof]["all_protected"] and safe[prof]["fragile_guard_fired_on"] else "CHECK",
                         f"guard fired on {len(safe[prof]['fragile_guard_fired_on'])} case(s), protected={safe[prof]['all_protected']}"))
        verdicts.append(("medium_est_score_no_drop", "PASS (projected)",
                         f"projected +{0.5*math.log(1+p):.3f}/task on Medium (deeper ratio)"))
        verdicts.append(("new_broken_baseline_vs_m7", "PENDING_EVAL",
                         "offline harness: 0 broken; real needs SOMA eval"))
        verdicts.append(("medium_neg_run_increase", "PENDING_EVAL",
                         f"m7 Medium-first targets are pass-stable (neg_run_rate={med['neg_run_rate']}); real needs eval"))
        offline_pass = all(v[1].startswith("PASS") for v in verdicts[:3])
        decision = ("ADVANCE (candidate-only): offline gate PASS; real-task gate PENDING_EVAL"
                    if offline_pass else "HOLD: offline gate failed")
        return {"checks": verdicts, "offline_decision": decision}
    metrics["gate"] = {prof: gate(prof) for prof in PROFILES}

    # ---- ingest REAL candidate results if provided, and apply the FULL gate ----
    if args.results:
        cres = load_candidate_results(Path(args.results))
        cand_by_num = {c["num"]: c for c in cres if c["num"]}
        mf_rows = candidate_rows(groups["medium_first"], cand_by_num)
        fr_rows = candidate_rows(groups["fragile_guard"], cand_by_num)
        base_mf = metrics["groups"]["medium_first"]["m7_baseline"]
        verdict = full_gate(mf_rows, fr_rows, base_mf)
        improved = [r["task_name"] for r in mf_rows
                    if r["score_delta"] is not None and r["score_delta"] > 0]
        regressed = [r["task_name"] for r in mf_rows
                     if r["score_delta"] is not None and r["score_delta"] < 0]
        metrics["real_results_ingested"] = str(Path(args.results))
        metrics["real_candidate"] = {
            "medium_first": verdict["medium_first_metrics"], "medium": verdict["medium_metrics"],
            "fragile_new_breaks": sum(1 for r in fr_rows if r["new_broke"]),
            "tasks_improved_vs_m7": improved, "tasks_regressed_vs_m7": regressed,
        }
        metrics["real_gate"] = {"decision": verdict["decision"], "checks": verdict["checks"],
                                "rejected_on": verdict["rejected_on"]}
        task_rows += mf_rows + fr_rows   # real per-task rows into task_results.jsonl

    # ---- write run dir ----
    run_dir = RUNS / f"{utc_stamp()}_H1M_eval"
    (run_dir / "raw_logs").mkdir(parents=True, exist_ok=True)
    (run_dir / "raw_logs" / "offline_eval.json").write_text(
        json.dumps(offline, indent=2), encoding="utf-8")
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    with (run_dir / "task_results.jsonl").open("w", encoding="utf-8") as f:
        for r in task_rows:
            f.write(json.dumps(r) + "\n")
    man = [f"experiment: H1M_eval", f"candidate: H1M_m7_deeper_safe_v1",
           f"created: {utc_now()}", "profiles: [m7, h1m@medium, h1m@deep]",
           f"medium_first: {MEDIUM_FIRST}", f"fragile_guard: {FRAGILE}",
           f"solving_gap_excluded: {SOLVING_GAP}",
           "basis: real m7 baseline + offline candidate proxy; candidate pass/neg-run PENDING_EVAL",
           "gate: reject if new broken baseline / Medium neg-run up / Medium score down / ratio<8% / guard fails"]
    (run_dir / "manifest.yaml").write_text("\n".join(man) + "\n", encoding="utf-8")

    # ---- report.md ----
    mb = metrics["groups"]["medium_first"]["m7_baseline"]
    L = [f"# H1M_eval run — {run_dir.name}", f"_{utc_now()}_", "",
         metrics["data_basis"], "",
         "## m7 baseline on Medium-first targets (REAL, platform scrape)",
         f"- tasks: {mb['n_tasks']} | pass_rate {mb['pass_rate']} | neg-run rate {mb['neg_run_rate']} | "
         f"broke {mb['broke_baseline_count']} | neg-score {mb['negative_score_count']}",
         f"- avg ratio {mb['avg_ratio']}× | median {mb['median_ratio']}× | Medium ratio {mb['medium_ratio']}× | "
         f"Medium est score {mb['medium_est_score']}", "",
         "## Candidate (offline proxy + projection; real pass/neg-run PENDING_EVAL)",
         "| profile | offline ratio Δ | proj avg ratio | proj Medium ratio | est score Δ/task | protected | guard | real pass/neg |",
         "|---|---|---|---|---|---|---|---|"]
    for prof in PROFILES:
        pr = metrics["groups"]["medium_first"][prof]
        L.append(f"| {prof} | +{pr['offline_ratio_pct_vs_m7']*100:.1f}% | {pr['proj_avg_ratio']}× | "
                 f"{pr['proj_medium_ratio']}× | +{pr['est_score_delta_per_task']} | {pr['offline_all_protected']} | "
                 f"fires (offline) | PENDING_EVAL |")
    L += ["", "## Fragile guard group (m7 baseline; candidate expected to fall back to m7)",
          f"- tasks: {[t['task_name'] for t in groups['fragile_guard']]}",
          f"- m7 broke-baseline here: {metrics['groups']['fragile_guard']['m7_baseline']['broke_baseline_count']} "
          f"| m7 neg-run rate {metrics['groups']['fragile_guard']['m7_baseline']['neg_run_rate']}",
          "- candidate: guard (ERROR_GUARD_MIN_HITS=3) routes still-failing/error-dense to m7 rich path → "
          "no deeper compression; offline harness confirmed the guard fires. Verify on eval.", "",
          "## Decision gate"]
    for prof in PROFILES:
        L.append(f"### {prof}")
        for name, verdict, detail in metrics["gate"][prof]["checks"]:
            L.append(f"- {name}: **{verdict}** — {detail}")
        L.append(f"- → {metrics['gate'][prof]['offline_decision']}")
    L += ["", "## What is needed to finish the gate (the one thing offline can't do)",
          "Run h1m@deep (and h1m@medium) through the SOMA SWE-bench eval on the Medium-first targets, export "
          "per-task results (task_id, pass, neg_runs, ratio, score), then `python h1m_run.py --results <file>`. "
          "Only that yields real pass-rate / neg-run / broke-baseline; until then candidate stays CANDIDATE-ONLY."]
    if metrics.get("real_gate"):
        rc = metrics["real_candidate"]
        mfm, medm = rc["medium_first"], rc["medium"]
        L += ["", "## REAL candidate results — FULL gate (from --results)",
              f"- Medium-first: pass_rate {mfm.get('pass_rate')} | neg-run {mfm.get('neg_run_rate')} | "
              f"broke {mfm.get('broke_baseline_count')} (new {mfm.get('new_broke_count')}) | "
              f"neg-score {mfm.get('negative_score_count')} | avg ratio {mfm.get('avg_ratio')}× | "
              f"median {mfm.get('median_ratio')}×",
              f"- Medium: ratio {medm.get('avg_ratio')}× | est score {medm.get('avg_score')} | "
              f"neg-run {medm.get('neg_run_rate')}",
              f"- fragile new breaks: {rc['fragile_new_breaks']} | improved {len(rc['tasks_improved_vs_m7'])} | "
              f"regressed {len(rc['tasks_regressed_vs_m7'])}",
              "", "| gate check | verdict | detail |", "|---|---|---|"]
        for name, verdict, detail in metrics["real_gate"]["checks"]:
            L.append(f"| {name} | **{verdict}** | {detail} |")
        L.append(f"- → **DECISION: {metrics['real_gate']['decision']}**"
                 + (f" (rejected on: {', '.join(metrics['real_gate']['rejected_on'])})"
                    if metrics['real_gate']['rejected_on'] else ""))
    (run_dir / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    if metrics.get("real_gate"):
        rg = metrics["real_gate"]
        print("REAL gate decision:", rg["decision"],
              ("| rejected_on: " + ", ".join(rg["rejected_on"]) if rg["rejected_on"] else ""))
        for name, verdict, detail in rg["checks"]:
            print(f"  {verdict:>6}  {name}  ({detail})")
    print(f"run dir: {run_dir.name}")
    print(f"m7 Medium-first baseline: pass {mb['pass_rate']} neg-run {mb['neg_run_rate']} broke {mb['broke_baseline_count']} "
          f"avg {mb['avg_ratio']}x Medium {mb['medium_ratio']}x")
    for prof in PROFILES:
        pr = metrics["groups"]["medium_first"][prof]
        print(f"  {prof}: offline +{pr['offline_ratio_pct_vs_m7']*100:.1f}% -> proj Medium {pr['proj_medium_ratio']}x "
              f"est +{pr['est_score_delta_per_task']}/task | real pass/neg = PENDING_EVAL | "
              f"{metrics['gate'][prof]['offline_decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
