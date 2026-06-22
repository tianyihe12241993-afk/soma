#!/usr/bin/env python3
"""Import per-task results into data/processed/miner_task_scores.jsonl.

Sources (in priority order):
  1. --import <file.csv|json>   manual/pasted platform export (schema = the template)
  2. (default) all immutable detail scrapes data/raw/dashboard/*/*_miner_detail.json
     (source=platform). Deduped by (hotkey, task_id), newest observed_at wins.

Row schema (one JSON object per line):
  miner_id, hotkey, version, task_id, task_name, category,
  baseline_pass, miner_pass, baseline_tokens, miner_tokens, compression_ratio,
  score, broke_baseline, negative_score, source, observed_at

NOTE ON MISSING DATA — per-task CATEGORY (Easy/Medium/Hard) is NOT exposed by the
dashboard per task. Screener tasks are tagged category="screener". All other tasks
get category=null unless config/task_categories.csv (task_id,task_name,category)
is present. If category is missing this script writes
data/raw/platform_results/IMPORT_TEMPLATE.csv and warns; Medium/Hard task-level
attribution stays BLOCKED until that map is imported. Scores are never invented.
"""
from __future__ import annotations
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (RAW, PROCESSED, CONFIG, utc_now, read_text,  # noqa: E402
                     load_miners_rich, load_top_miners, load_miners)

OUT = PROCESSED / "miner_task_scores.jsonl"
TEMPLATE = RAW.parent / "platform_results" / "IMPORT_TEMPLATE.csv"
CAT_MAP = CONFIG / "task_categories.csv"
FIELDS = ["miner_id", "hotkey", "version", "task_id", "task_name", "category",
          "baseline_pass", "miner_pass", "baseline_tokens", "miner_tokens",
          "compression_ratio", "score", "broke_baseline", "negative_score",
          "source", "observed_at"]


def _hotkey_index() -> dict:
    """hotkey -> (miner_id, version). Ours from miners.yaml, rivals from top_miners.yaml."""
    idx = {}
    for mid, d in load_miners_rich().items():
        idx[d["hotkey"]] = (d.get("label", mid), d.get("version", ""))
    for mid, d in load_miners().items():                  # legacy: also catches m1/m2/m3/m5/m6/m12
        idx.setdefault(d["hotkey"], (mid, d.get("version", "")))
    for tid, d in load_top_miners().items():
        idx.setdefault(d["hotkey"], (tid, d.get("role", "top")))
    return idx


def _categories() -> dict:
    if not CAT_MAP.exists():
        return {}
    out = {}
    for r in csv.DictReader(CAT_MAP.open(encoding="utf-8")):
        if r.get("task_id"):
            out[int(r["task_id"])] = (r.get("category") or "").strip() or None
    return out


def _ratio(a, b):
    return round(a / b, 4) if (a and b) else None


def rows_from_detail_snaps(idx: dict, cats: dict) -> list:
    """Build rows from every detail snapshot, newest (hotkey,task_id) wins.
    Sources: RSC scrapes (data/raw/dashboard/*_miner_detail.json) AND the JSON-API
    fetch (data/raw/platform_results/*_swe_api.json, which also carries per-run 'runs')."""
    best = {}
    snaps = (sorted(RAW.glob("*/*_miner_detail.json"))
             + sorted((RAW.parent / "platform_results").glob("*/*_swe_api.json")))
    for snap in snaps:
        obj = json.loads(snap.read_text(encoding="utf-8"))
        observed = obj.get("observed_at", "")
        for m in obj.get("miners", []):
            hk = m["hotkey"]
            mid, ver = idx.get(hk, (hk[:8], ""))
            for t in m.get("tasks", []):
                key = (hk, t["task_id"])
                if key in best and best[key]["observed_at"] >= observed:
                    continue
                bt, mt = t.get("tokens_without_compression"), t.get("tokens_with_compression")
                bp, mp = t.get("pass_without_compression"), t.get("pass_with_compression")
                sc = t.get("platform_score")
                cat = "screener" if t.get("is_screener") else cats.get(t["task_id"])
                best[key] = {
                    "miner_id": mid, "hotkey": hk, "version": ver,
                    "task_id": t["task_id"], "task_name": t.get("task_name"),
                    "category": cat, "baseline_pass": bp, "miner_pass": mp,
                    "baseline_tokens": bt, "miner_tokens": mt,
                    "compression_ratio": _ratio(bt, mt), "score": sc,
                    "broke_baseline": bool(bp and not mp),
                    "negative_score": bool(sc is not None and sc < 0),
                    "source": "platform", "observed_at": observed,
                }
    return list(best.values())


def rows_from_file(path: Path) -> list:
    raw = path.read_text(encoding="utf-8")
    if raw.lstrip().startswith(("{", "[")):
        obj = json.loads(raw)
        return obj.get("rows", obj) if isinstance(obj, dict) else obj
    out = []
    for r in csv.DictReader(path.open(encoding="utf-8")):
        for k in ("task_id", "baseline_tokens", "miner_tokens"):
            if r.get(k) not in (None, ""):
                try:
                    r[k] = int(float(r[k]))
                except ValueError:
                    pass
        for k in ("compression_ratio", "score"):
            if r.get(k) not in (None, ""):
                try:
                    r[k] = float(r[k])
                except ValueError:
                    pass
        for k in ("baseline_pass", "miner_pass", "broke_baseline", "negative_score"):
            if isinstance(r.get(k), str):
                r[k] = r[k].strip().lower() in ("true", "1", "yes")
        r.setdefault("source", "manual")
        r.setdefault("observed_at", utc_now())
        out.append(r)
    return out


def write_template():
    TEMPLATE.parent.mkdir(parents=True, exist_ok=True)
    with TEMPLATE.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(FIELDS)
        w.writerow(["m7", "5Gs...", "v11.1", 217, "django__django-10880", "Medium",
                    "true", "true", 1126760, 450595, 2.5, 1.42, "false", "false",
                    "platform", "2026-06-17T00:00:00Z"])
    # also a minimal task->category map template (the actually-missing piece)
    cat_t = TEMPLATE.parent / "TASK_CATEGORIES_TEMPLATE.csv"
    with cat_t.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["task_id", "task_name", "category"])
        w.writerow([217, "django__django-10880", "Medium"])
    return cat_t


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--import", dest="imp", help="manual CSV/JSON export")
    args = ap.parse_args()
    idx, cats = _hotkey_index(), _categories()

    rows = rows_from_file(Path(args.imp)) if args.imp else rows_from_detail_snaps(idx, cats)
    if not rows:
        cat_t = write_template()
        print(f"No per-task data found. Wrote {TEMPLATE} and {cat_t}. "
              f"Fill one and re-run with --import, or collect a detail scrape first.",
              file=sys.stderr)
        return 1

    PROCESSED.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    n_no_cat = sum(1 for r in rows if r.get("category") is None)
    miners = sorted({r["miner_id"] for r in rows})
    print(f"wrote {OUT}  ({len(rows)} rows, {len(miners)} miners: {', '.join(miners)})")
    if n_no_cat:
        cat_t = write_template()
        print(f"  ⚠ {n_no_cat} rows have NO category (Easy/Medium/Hard). Medium/Hard "
              f"task-level attribution is BLOCKED. Fill {CAT_MAP} (template: {cat_t}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
