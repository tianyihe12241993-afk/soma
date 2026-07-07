#!/usr/bin/env python3
"""LOCAL explore-quality scorer for comp-110 (swe_explorer_explore).

WHY: during the upload window the eval tasks are HIDDEN, so we test on PUBLIC SWE-Explore-Bench
instances. The platform's hit_file_rate / noise_file_rate are computed VALIDATOR-side (no local
scorer ships), but the ground truth IS resolvable locally (SWE-Explore-Bench/SWE-Explore-Bench).
This reconstructs the FILE-LEVEL quality the explore gate uses so we can compare candidates locally.

Run under the benchmark env (it needs `soma_bench` to resolve ground truth):
  cd ~/joshua-work/SOMA-benchmark && uv run python \
    /Users/eric.xiao/joshua-work/soma/scripts/score_explore_local.py \
    --instance-id django__django-14017 \
    --regions /path/to/explore-result.json        # or --output-dir <benchmark-solve output dir>
  [--baseline-quality 0.42]                        # optional: also print the explore gate·tau

METRICS (file-level, matching the metric NAMES; the validator's exact formula is hidden — this is a
faithful reconstruction from ground_truth.read_core_files, documented, for RELATIVE local comparison):
  reported = set of file paths in the agent's regions (─/workspace/ prefix)
  core     = set(ground_truth.read_core_files)
  hit_file_rate   = |reported ∩ core| / |core|                 (recall over core files)
  noise_file_rate = |reported − core| / |reported|             (false-positive rate; 0 if none reported)
  quality = hit_file_rate − noise_file_rate   (what compute_explore_task_score gates on)
  + precision / recall / f1 for context.
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import sys

_WORKSPACE = "/workspace/"


def _strip(p: str) -> str:
    p = str(p or "").strip()
    if p.startswith(_WORKSPACE):
        p = p[len(_WORKSPACE):]
    return p.lstrip("./")


def _regions_from(regions_arg: str | None, output_dir: str | None) -> list[dict]:
    text = None
    if regions_arg:
        text = open(regions_arg, encoding="utf-8", errors="ignore").read()
    elif output_dir:
        # explore mode packs regions as the "patch"; also try a literal explore-result.json
        for pat in ("explore-result*.json", "**/explore-result*.json", "output.jsonl", "**/*trajectory*.jsonl"):
            for f in glob.glob(os.path.join(output_dir, pat), recursive=True):
                try:
                    raw = open(f, encoding="utf-8", errors="ignore").read()
                except Exception:
                    continue
                # find a JSON array of {path,...}
                import re
                m = re.search(r'\[\s*\{[^\[]*?"path"[^\]]*\]', raw, re.S)
                if m:
                    text = m.group(0)
                    break
            if text:
                break
    if not text:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _resolve_core_files(instance_id: str) -> list[str]:
    from soma_bench.benchmark.solve import _SWE_EXPLORER_BENCHMARK_NAME, resolve_benchmark_runtime_setup
    _, _, entry = resolve_benchmark_runtime_setup(
        benchmark_name=_SWE_EXPLORER_BENCHMARK_NAME, selection_id=instance_id)
    gt = (entry.get("hidden_eval") or {}).get("ground_truth") or {}
    return list(gt.get("read_core_files") or [])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance-id", required=True)
    ap.add_argument("--regions", help="path to a regions JSON array (explore-result.json)")
    ap.add_argument("--output-dir", help="benchmark-solve output dir to auto-find regions in")
    ap.add_argument("--baseline-quality", type=float, default=None)
    ap.add_argument("--miner-weighted", type=float, default=None, help="miner weighted tokens (for tau)")
    ap.add_argument("--baseline-weighted", type=float, default=None)
    args = ap.parse_args()

    core = {_strip(f) for f in _resolve_core_files(args.instance_id)}
    if not core:
        print(f"NO GROUND TRUTH for {args.instance_id} (dataset resolve failed).", file=sys.stderr)
        return 2
    regions = _regions_from(args.regions, args.output_dir)
    reported = {_strip(r.get("path")) for r in regions if isinstance(r, dict) and r.get("path")}

    hit = len(reported & core) / len(core)
    noise = (len(reported - core) / len(reported)) if reported else 0.0
    quality = hit - noise
    precision = (len(reported & core) / len(reported)) if reported else 0.0
    recall = hit
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    print(f"instance: {args.instance_id}")
    print(f"core files ({len(core)}): {sorted(core)}")
    print(f"reported files ({len(reported)}): {sorted(reported)}")
    print(f"  hit_file_rate   = {hit:.4f}")
    print(f"  noise_file_rate = {noise:.4f}")
    print(f"  QUALITY (hit-noise) = {quality:.4f}")
    print(f"  precision={precision:.3f} recall={recall:.3f} f1={f1:.3f}")

    if args.baseline_quality is not None:
        from math import log2
        delta = 0.20
        margin = quality - args.baseline_quality
        if margin <= -delta:
            print(f"  explore per-task score = FLOOR -2.0 (quality margin {margin:+.3f} <= -{delta})")
        elif args.miner_weighted and args.baseline_weighted:
            r = max(0.0, min(1.0, (margin + delta) / (2 * delta)))
            gate = 3 * r**2 - 2 * r**3
            tau = max(-2.0, min(2.0, 2 * log2(args.baseline_weighted / args.miner_weighted)))
            print(f"  margin {margin:+.3f} → gate {gate:.3f}; tau {tau:.3f}; explore task score = {gate*tau:.3f}")
        else:
            print(f"  quality margin vs baseline = {margin:+.3f} (pass --miner-weighted/--baseline-weighted for tau)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
