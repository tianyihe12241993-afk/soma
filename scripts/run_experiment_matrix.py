#!/usr/bin/env python3
"""Experiment runner skeleton for next-round candidates (offline).

Creates a fully-structured run directory, records the m7 BASELINE metrics on the
selected task subsets (from data/processed), and — if candidate per-task results are
supplied via --results — computes candidate metrics, the delta vs m7, and the decision
gate verdict. We cannot run platform evals offline, so without --results the candidate
metrics are honestly marked status="needs_data".

Usage:
  python scripts/run_experiment_matrix.py --manifest experiments/manifests/H1_*.yaml
  python scripts/run_experiment_matrix.py --manifest <m> --results <candidate_task_results.csv|json>

Run dir: experiments/runs/YYYY-MM-DD_HHMMSS_<id>/
  manifest.yaml  raw_logs/  metrics.json  task_results.jsonl  report.md
"""
from __future__ import annotations
import argparse
import csv
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import PROCESSED, ROOT, utc_now, utc_stamp, read_text, CONFIG  # noqa: E402
import re

RUNS = ROOT / "experiments" / "runs"
SUBSET_FILES = {
    "shared_pass": PROCESSED / "shared_pass_tasks.jsonl",
    "barely_compressed": PROCESSED / "compression_gap_tasks.jsonl",
    "fragile": PROCESSED / "fragile_tasks.jsonl",
}


def parse_manifest(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        m = re.match(r'^([A-Za-z0-9_]+):\s*(.*)$', line)
        if not m:
            continue
        k, v = m.group(1), m.group(2).strip()
        if v.startswith("[") and v.endswith("]"):
            out[k] = [x.strip().strip('"') for x in v[1:-1].split(",") if x.strip()]
        elif v.lower() in ("null", "", "~"):
            out[k] = None
        else:
            out[k] = v.strip('"')
    return out


def _jsonl(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def resolve_subset_task_ids(subsets) -> set:
    ids = set()
    missing = []
    for s in (subsets or []):
        f = SUBSET_FILES.get(s)
        if not f or not f.exists():
            missing.append(s)
            continue
        for r in _jsonl(f):
            ids.add(r["task_id"])
    return ids, missing


def metrics_from_rows(rows: list) -> dict:
    ratios = [r["ratio"] for r in rows if r.get("ratio")]
    scores = [r["score"] for r in rows if r.get("score") is not None]
    return {
        "n_tasks": len(rows),
        "pass_rate": round(sum(1 for r in rows if r.get("pass")) / len(rows), 4) if rows else None,
        "broke_baseline": sum(1 for r in rows if r.get("broke")),
        "negative_score": sum(1 for r in rows if r.get("neg")),
        "avg_compression_ratio": round(st.mean(ratios), 3) if ratios else None,
        "median_compression_ratio": round(st.median(ratios), 3) if ratios else None,
        "score_estimate": round(st.mean(scores), 4) if scores else None,
        "weighted_token_cost": None,     # needs input/cached/output token split (not yet available)
        "output_token_increase": None,   # needs output-token data (H4)
    }


def baseline_rows(task_ids: set) -> list:
    out = []
    for t in _jsonl(PROCESSED / "task_matrix.jsonl"):
        if t["task_id"] in task_ids and not t.get("is_screener"):
            d = t["miners"].get("m7")
            if d:
                out.append({"task_id": t["task_id"], "task_name": t["task_name"], **d})
    return out


def load_results(path: Path) -> list:
    raw = path.read_text(encoding="utf-8")
    if raw.lstrip().startswith(("{", "[")):
        obj = json.loads(raw)
        rows = obj.get("rows", obj) if isinstance(obj, dict) else obj
    else:
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
    for r in rows:
        for k in ("ratio", "score"):
            if r.get(k) not in (None, ""):
                r[k] = float(r[k])
        for k in ("pass", "broke", "neg"):
            if isinstance(r.get(k), str):
                r[k] = r[k].strip().lower() in ("true", "1", "yes")
    return rows


def gate(cand: dict, base: dict) -> list:
    cfg = read_text(CONFIG / "experiments.yaml")
    def g(name, dflt):
        m = re.search(rf'{name}:\s*([-\d.]+)', cfg)
        return float(m.group(1)) if m else dflt
    verdicts = []
    if cand.get("broke_baseline") is not None:
        if cand["broke_baseline"] - base["broke_baseline"] > g("max_broken_baseline_increase", 0):
            verdicts.append("REJECT: broken baselines increased vs m7")
    if cand.get("avg_compression_ratio") and base.get("avg_compression_ratio"):
        if cand["avg_compression_ratio"] - base["avg_compression_ratio"] < g("min_avg_ratio_improvement", 0.3):
            verdicts.append("REJECT: avg ratio improvement below threshold")
    if cand.get("score_estimate") and base.get("score_estimate"):
        if cand["score_estimate"] < base["score_estimate"]:
            verdicts.append("WARN: score estimate dropped vs m7")
    return verdicts or ["PASS (subset gate; Medium/category gate needs task->category map)"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--results", help="candidate per-task results CSV/JSON from a local replay")
    args = ap.parse_args()
    man = parse_manifest(read_text(Path(args.manifest)))
    exp_id = man.get("id") or Path(args.manifest).stem

    task_ids, missing = resolve_subset_task_ids(man.get("subsets"))
    brows = baseline_rows(task_ids)
    base = metrics_from_rows(brows)

    run_dir = RUNS / f"{utc_stamp()}_{exp_id}"
    (run_dir / "raw_logs").mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.yaml").write_text(read_text(Path(args.manifest)), encoding="utf-8")

    cand = {"status": "needs_data",
            "note": "No candidate results supplied. Run the candidate locally on the subset and "
                    "re-run with --results <file>. weighted_token_cost/output_token_increase need "
                    "input/cached/output token split (H4)."}
    crows = []
    verdicts = ["BASELINE ONLY — no candidate yet"]
    if args.results:
        crows = load_results(Path(args.results))
        cand = metrics_from_rows(crows)
        cand["status"] = "measured"
        verdicts = gate(cand, base)

    changed = []
    if crows:
        bmap = {r["task_id"]: r for r in brows}
        for r in crows:
            tid = int(r.get("task_id")) if str(r.get("task_id", "")).isdigit() else r.get("task_id")
            b = bmap.get(tid)
            if b and (r.get("score") is not None and b.get("score") is not None
                      and abs(r["score"] - b["score"]) > 1e-6):
                changed.append({"task_id": tid, "m7_score": b["score"], "cand_score": r["score"]})

    metrics = {"experiment_id": exp_id, "computed_at": utc_now(),
               "subsets": man.get("subsets"), "missing_subsets": missing,
               "task_ids": sorted(task_ids), "baseline_m7": base, "candidate": cand,
               "changed_vs_m7": changed, "gate": verdicts}
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    with (run_dir / "task_results.jsonl").open("w", encoding="utf-8") as f:
        for r in (crows or brows):
            f.write(json.dumps(r) + "\n")

    R = [f"# Experiment run — {exp_id}", f"_run {utc_now()}_", "",
         f"- Subsets: {man.get('subsets')}  (missing: {missing or 'none'})",
         f"- Tasks in scope: {len(task_ids)}",
         f"- Base m7: pass_rate {base['pass_rate']}, broke {base['broke_baseline']}, "
         f"neg {base['negative_score']}, ratio {base['avg_compression_ratio']}×, "
         f"score~{base['score_estimate']}",
         f"- Candidate: {cand.get('status')}"
         + (f", ratio {cand.get('avg_compression_ratio')}×, broke {cand.get('broke_baseline')}, "
            f"score~{cand.get('score_estimate')}" if cand.get('status') == 'measured' else ""),
         f"- Gate: {'; '.join(verdicts)}",
         "", f"_manifest.yaml, metrics.json, task_results.jsonl in this dir._"]
    (run_dir / "report.md").write_text("\n".join(R) + "\n", encoding="utf-8")
    print(f"run dir: {run_dir}")
    print(f"  baseline m7 on {len(task_ids)} subset tasks: ratio {base['avg_compression_ratio']}×, "
          f"broke {base['broke_baseline']}, score~{base['score_estimate']}")
    print(f"  candidate: {cand.get('status')} | gate: {'; '.join(verdicts)}")
    if missing:
        print(f"  ⚠ missing subsets (need data): {missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
