#!/usr/bin/env python3
"""Normalize PER-RUN snapshots -> data/processed/run_scores.jsonl + a variance report.

Reads every per-run snapshot under data/raw/platform_results/ — both the
{miners:[...]} shape (collect_runs.py / *_swe_runs.json) and single-miner files
(vendored extension raw/<hk>.json). One row per (hotkey, task, attempt):
  miner_id, hotkey, task_id, task_name, category, attempt_no, run_id,
  run_pass, run_tokens, run_score, time_taken_seconds, agent_steps,
  baseline_tokens, source, observed_at
Dedup by (hotkey, task_id, attempt_no), newest observed_at wins.

Also writes data/latest/run_variance.json + reports/run_variance.md: per (miner, task)
run-level spread — this is what per-run buys us (a pass/pass task can still score low
because some of the 5 attempts fail or cost far more).
"""
from __future__ import annotations
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (RAW, PROCESSED, LATEST, REPORTS, utc_now, read_text,  # noqa: E402
                     load_miners_rich, load_top_miners, load_miners)
import csv as _csv

PLATFORM = RAW.parent / "platform_results"
OUT = PROCESSED / "run_scores.jsonl"


def _idx():
    idx = {}
    for mid, d in load_miners_rich().items():
        idx[d["hotkey"]] = d.get("label", mid)
    for mid, d in load_miners().items():
        idx.setdefault(d["hotkey"], mid)
    for tid, d in load_top_miners().items():
        idx.setdefault(d["hotkey"], tid)
    return idx


def _task_meta():
    """task_id -> (category, real_task_name) from config/task_categories.csv."""
    from pathlib import Path as _P
    p = _P("config/task_categories.csv")
    if not p.exists():
        return {}, {}
    cats, names = {}, {}
    for r in _csv.DictReader(p.open(encoding="utf-8")):
        if r.get("task_id"):
            tid = int(r["task_id"])
            cats[tid] = (r.get("category") or None)
            if r.get("task_name"):
                names[tid] = r["task_name"]
    return cats, names


def _is_placeholder(name):
    return (not name) or "available after uploads" in str(name).lower()


def _miner_records(obj, observed):
    """Yield (miner_dict, observed_at) for both snapshot shapes."""
    if isinstance(obj, dict) and "miners" in obj:
        for m in obj["miners"]:
            yield m, obj.get("observed_at", observed)
    elif isinstance(obj, dict) and obj.get("hotkey") and "tasks" in obj:
        yield obj, observed


def main() -> int:
    idx = _idx()
    cats, tnames = _task_meta()
    best = {}
    for snap in sorted(PLATFORM.glob("**/*.json")):
        try:
            obj = json.loads(snap.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        # fallback observed_at from the day-dir name for single-miner files
        day = snap.parent.name
        for m, observed in _miner_records(obj, day):
            hk = m.get("hotkey")
            if not hk:
                continue
            mid = idx.get(hk, hk[:8])
            for t in m.get("tasks", []):
                tid = t.get("task_id")
                bt = t.get("tokens_without_compression")
                for r in (t.get("runs") or []):
                    key = (hk, tid, r.get("attempt_no"))
                    if key in best and best[key]["observed_at"] >= (observed or ""):
                        continue
                    nm = t.get("task_name")
                    if _is_placeholder(nm):
                        nm = tnames.get(tid, nm)
                    best[key] = {
                        "miner_id": mid, "hotkey": hk, "task_id": tid,
                        "task_name": nm, "category": cats.get(tid),
                        "attempt_no": r.get("attempt_no"), "run_id": r.get("run_id"),
                        "run_pass": r.get("pass_with_compression"),
                        "run_tokens": r.get("tokens_with_compression"),
                        "run_score": r.get("platform_score"),
                        "time_taken_seconds": r.get("time_taken_seconds"),
                        "agent_steps": r.get("agent_steps"),
                        "baseline_tokens": bt,
                        "source": "platform", "observed_at": observed or "",
                    }
    rows = list(best.values())
    if not rows:
        print("No per-run data yet (run: python scripts/collect_runs.py) — skipping run normalize.")
        return 0
    PROCESSED.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    # ---- per (miner, task) variance ----
    groups = {}
    for r in rows:
        groups.setdefault((r["miner_id"], r["task_id"], r["task_name"], r["category"]), []).append(r)
    var = []
    for (mid, tid, tname, cat), rs in groups.items():
        scores = [x["run_score"] for x in rs if x["run_score"] is not None]
        passes = [x["run_pass"] for x in rs if x["run_pass"] is not None]
        toks = [x["run_tokens"] for x in rs if x["run_tokens"]]
        if not scores:
            continue
        var.append({
            "miner_id": mid, "task_id": tid, "task_name": tname, "category": cat,
            "n_runs": len(rs), "n_pass": sum(1 for p in passes if p),
            "score_min": round(min(scores), 3), "score_max": round(max(scores), 3),
            "score_spread": round(max(scores) - min(scores), 3),
            "score_mean": round(st.mean(scores), 3),
            "tokens_min": min(toks) if toks else None, "tokens_max": max(toks) if toks else None,
            "flaky": len(set(bool(p) for p in passes)) > 1,   # some runs pass, some fail
        })
    LATEST.mkdir(parents=True, exist_ok=True)
    (LATEST / "run_variance.json").write_text(json.dumps(
        {"computed_at": utc_now(), "rows": var}, indent=2), encoding="utf-8")

    ours = set(load_miners_rich())
    flaky = sorted([v for v in var if v["miner_id"] in ours and v["flaky"]],
                   key=lambda v: -v["score_spread"])
    spread = sorted([v for v in var if v["miner_id"] in ours],
                    key=lambda v: -v["score_spread"])[:20]
    L = [f"# Per-run variance (our miners)",
         f"_computed {utc_now()} from data/processed/run_scores.jsonl ({len(rows)} run rows)._", "",
         f"**Flaky tasks** (some of the { '5' } runs pass, some fail) — the hidden cost behind "
         f"'pass/pass' tasks that still score low: **{len(flaky)}**.", "",
         "| miner | task | cat | n_pass/n | score min→max | spread |",
         "|-------|------|-----|----------|---------------|--------|"]
    for v in flaky[:25]:
        L.append(f"| {v['miner_id']} | {v['task_name']} | {v['category']} | "
                 f"{v['n_pass']}/{v['n_runs']} | {v['score_min']}→{v['score_max']} | {v['score_spread']} |")
    L += ["", "## Highest score spread (our miners, top 20)",
          "| miner | task | cat | n_pass/n | mean | spread |",
          "|-------|------|-----|----------|------|--------|"]
    for v in spread:
        L.append(f"| {v['miner_id']} | {v['task_name']} | {v['category']} | "
                 f"{v['n_pass']}/{v['n_runs']} | {v['score_mean']} | {v['score_spread']} |")
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "run_variance.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    print(f"wrote {OUT} ({len(rows)} run rows, {len(groups)} miner-task groups), "
          f"{LATEST/'run_variance.json'}, {REPORTS/'run_variance.md'}")
    print(f"  flaky (mixed pass/fail across runs) for our miners: {len(flaky)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
