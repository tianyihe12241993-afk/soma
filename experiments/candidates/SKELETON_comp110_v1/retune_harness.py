#!/usr/bin/env python3
"""Parameterized RE-TUNE harness for the SKELETON candidate (comp-110). Stdlib only, offline, no credits.

Purpose: the score formula is in flux (DISCOVERIES 2026-07-07). The moment the watcher flags a change,
plug the NEW weights + gate in here and instantly see which knob settings (budget / head / tail) clear
the gate on real captured traffic — and how much file-path (explore) signal each preserves. No re-arch.

Inputs (defaults = CURRENT upstream constants, cached 1/10, gate 0.20):
  --input-weight --cached-weight --output-weight --gate
  --payloads   (default: scratchpad feas_payloads.jsonl — the 29 real captured requests)
  --dilution   (my_captured_context / live_context; default auto from a stored value; real≈opt×dilution)
Method + caveats: fixed-trajectory replay. Measures CONTEXT (input+cached) savings a compressor can
directly achieve; CANNOT measure trajectory/output changes (output held at the live constant). So the
number is the path-independent context-savings component — an upper bound on the compressor's own effect.

Usage examples:
  python3 retune_harness.py                              # current constants
  python3 retune_harness.py --cached-weight 0.333 --gate 0.10   # e.g. if they revert cached to 1/3, gate to 10%
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MINER = ROOT / "miner" / "cot_compression" / "upload_miner_skeleton_v2.py"
DEFAULT_PAYLOADS = "/private/tmp/claude-502/-Users-eric-xiao-joshua-work-soma/1bfdbf36-7583-4f8f-bf10-e3f3ddef4000/scratchpad/feas_payloads.jsonl"
LIVE_OUTPUT_TOKENS = 10722          # from the captured no-compression run (weight = output_weight)
LIVE_CACHED_TOKENS = 508160         # for the dilution/validation vs live
LIVE_INPUT_TOKENS = 16878

_PATH = re.compile(r"[\w\-./]+\.py\b")
_TERM = re.compile(r"(\r\n|\r|\n)$")


def _load_miner(min_c, head, tail, budget, recency=True):
    os.environ["SOMA_SKEL_RECENCY"] = "1" if recency else "0"
    sys.modules.pop("sk", None)
    spec = importlib.util.spec_from_file_location("sk", MINER)
    m = importlib.util.module_from_spec(spec); sys.modules["sk"] = m; spec.loader.exec_module(m)
    m.MIN_COMPRESS, m.HEAD_LINES, m.TAIL_LINES, m.BUDGET = min_c, head, tail, budget
    m.MIN_LINES = head + tail + 2
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-weight", type=float, default=1.0)
    ap.add_argument("--cached-weight", type=float, default=1.0 / 10.0)
    ap.add_argument("--output-weight", type=float, default=3.0)
    ap.add_argument("--gate", type=float, default=0.20)
    ap.add_argument("--payloads", default=DEFAULT_PAYLOADS)
    ap.add_argument("--dilution", type=float, default=None, help="my_ctx/live_ctx; if omitted, computed")
    args = ap.parse_args()

    reqs = [json.loads(l)["messages"] for l in open(args.payloads) if l.strip()]
    IW, CW, OW = args.input_weight, args.cached_weight, args.output_weight
    OUT_W = LIVE_OUTPUT_TOKENS * OW

    def chars(m, sl=slice(None)):
        return sum(len(x.get("content")) for x in m[sl] if isinstance(x.get("content"), str))

    def ctxw(m):   # per-request weighted context: prefix cached, last message = fresh input; tokens=chars/4
        return chars(m, slice(0, -1)) / 4 * CW + chars(m, slice(-1, None)) / 4 * IW if m else 0.0

    base = sum(ctxw(m) for m in reqs) + OUT_W
    # dilution vs live (context only) so real≈opt×dilution (hidden uncompressible schemas/framing)
    my_ctx = sum(ctxw(m) for m in reqs)
    live_ctx = LIVE_INPUT_TOKENS * IW + LIVE_CACHED_TOKENS * CW
    dil = args.dilution if args.dilution is not None else (my_ctx / live_ctx if live_ctx else 1.0)

    print(f"weights: input×{IW} cached×{CW:.4g} output×{OW} | gate {args.gate*100:.0f}% | dilution ×{dil:.2f} "
          f"| {len(reqs)} captured requests")
    print(f"{'profile/knobs':>22} {'opt%':>6} {'real~%':>7} {'.py paths kept':>15} {'clears gate':>11}")
    grid = [("safe", 700, 5, 2, 900), ("target", 500, 3, 1, 550), ("deep", 400, 2, 1, 380),
            ("aggr-1", 400, 2, 1, 300), ("aggr-2", 300, 1, 1, 220), ("ceiling", 150, 0, 0, 120)]
    for name, minc, h, t, bud in grid:
        m = _load_miner(minc, h, t, bud)
        var = 0.0; paths_in = set(); paths_kept = set()
        for msgs in reqs:
            comp = m.compress_messages([dict(x) for x in msgs]); var += ctxw(comp)
            for a, b in zip(msgs, comp):
                if isinstance(a.get("content"), str):
                    paths_in |= set(_PATH.findall(a["content"]))
                if isinstance(b.get("content"), str):
                    paths_kept |= set(_PATH.findall(b["content"]))
        s = 1 - (var + OUT_W) / base
        real = s * dil
        pk = len(paths_in & paths_kept) / max(len(paths_in), 1) * 100
        print(f"{name+' '+str((minc,h,t,bud)):>22} {s*100:6.1f} {real*100:7.1f} {pk:14.0f}% "
              f"{'YES' if real >= args.gate else 'no':>11}")
    print("\nNOTE: real% = context-savings component only (fixed trajectory). Confirm with a live multi-run "
          "eval before trusting; output/turn effects are not captured. Re-run after any formula change.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
