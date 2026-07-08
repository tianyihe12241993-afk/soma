#!/usr/bin/env python3
"""LOCAL correctness grading for comp-110 candidates (the piece the copilot backend lacks).

The copilot backend only CAPTURES the patch (capture_repo_patch); the SWE-rebench grading step is
implemented only for the openclaw backend. This grades a captured patch directly with the standard
swebench harness: builds predictions.jsonl from a benchmark-solve output dir and runs
swebench.harness.run_evaluation (prebuilt x86 images; runs under emulation on Apple Silicon).

Usage (from the SOMA-benchmark repo, its uv env has swebench):
  cd ~/joshua-work/SOMA-benchmark && uv run python \
    /Users/eric.xiao/joshua-work/soma/scripts/grade_patch_local.py \
    --output-dir outputs/baseline_seed_11551_r1 [--run-id grade1] [--timeout 1800]
Prints RESOLVED / NOT-RESOLVED and the report path. Exit 0 = resolved, 2 = not resolved, 1 = error.
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--run-id", default="localgrade")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--max-workers", type=int, default=1)
    args = ap.parse_args()

    out = Path(args.output_dir)
    d = json.load(open(out / "output.jsonl"))
    inst = d["instance_id"]
    pc = (d.get("metadata", {}) or {}).get("patch_capture") or {}
    patch_path = pc.get("patch_path")
    if not (patch_path and Path(patch_path).is_file()):
        print(f"ERROR: no captured patch for {inst} (patch_path={patch_path})", file=sys.stderr)
        return 1
    patch = Path(patch_path).read_text(encoding="utf-8", errors="ignore")
    if not patch.strip():
        print(f"NOT-RESOLVED {inst} (empty patch)")
        return 2

    preds = out / "predictions_localgrade.jsonl"
    preds.write_text(json.dumps({
        "instance_id": inst, "model_name_or_path": "localgrade", "model_patch": patch}) + "\n")

    cmd = [sys.executable, "-m", "swebench.harness.run_evaluation",
           "--dataset_name", "SWE-bench/SWE-bench_Verified", "--split", "test",
           "--predictions_path", str(preds.resolve()), "--instance_ids", inst,
           "--run_id", args.run_id, "--max_workers", str(args.max_workers),
           "--timeout", str(args.timeout), "--cache_level", "env"]
    print("+", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=str(out))  # harness writes logs/ + report under cwd
    # report: <model_name>.<run_id>.json in cwd
    rep = None
    for cand in out.glob(f"localgrade.{args.run_id}.json"):
        rep = cand
    if rep is None:
        print(f"ERROR: harness exited {r.returncode}, no report found", file=sys.stderr)
        return 1
    rj = json.loads(rep.read_text())
    resolved = inst in (rj.get("resolved_ids") or [])
    print(f"{'RESOLVED' if resolved else 'NOT-RESOLVED'} {inst}  (report: {rep})")
    return 0 if resolved else 2


if __name__ == "__main__":
    raise SystemExit(main())
