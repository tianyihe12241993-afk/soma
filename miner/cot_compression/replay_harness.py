#!/usr/bin/env python3
"""Replay real captured trajectories through the miner — no Docker, no LLM.

Data source: the connector's io logs archived from e2e runs
(`plugin-logs-host/io/*.input-trajectory.json`). Two passes:

1. Sweep: every captured input trajectory, fresh state — coverage of real
   shapes/sizes. Checks protocol + safety invariants, reports mode/savings.
2. Session replay: trajectories grouped by session, fed chronologically with
   shared state — validates incremental behavior and prefix stability on
   real growth patterns.

Usage:
    python3 replay_harness.py [--miner improved_miner.py] [--root /path/to/e2e]
"""

from __future__ import annotations

import argparse
import json
import statistics
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

from test_improved_miner import call_miner, est_tokens, text_of, tool_ids

HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = Path("/Users/user/SOMA-benchmark/outputs/e2e")


def load_io_files(root: Path) -> list[dict]:
    files = sorted(root.glob("*/*/plugin-logs-host/io/*.input-trajectory.json"))
    entries = []
    for f in files:
        try:
            payload = json.loads(f.read_text())
        except Exception:
            continue
        traj = payload.get("trajectory")
        if isinstance(traj, list) and traj:
            entries.append({
                "file": f,
                "session": payload.get("sessionId") or f.name.split("-")[6],
                "ts": payload.get("timestamp") or f.name[:24],
                "messages": traj,
            })
    return entries


def check_invariants(inp: list, out: list, mode: str) -> list[str]:
    problems = []
    if not out:
        return ["empty output"]
    out_text = "\n".join(text_of(m.get("content")) for m in out)
    for m in inp:
        if m.get("role") == "user":
            snip = text_of(m.get("content"))[:60]
            if snip and snip not in out_text:
                problems.append("user message lost")
                break
    in_rc, in_cc = tool_ids(inp)
    out_rc, out_cc = tool_ids(out)
    if not (out_rc - out_cc) <= (in_rc - in_cc):
        problems.append("orphan toolResult introduced")
    if not (out_cc - out_rc) <= (in_cc - in_rc):
        problems.append("orphan toolCall introduced")
    if mode == "gentle" and len(out) != len(inp):
        problems.append(f"gentle dropped messages ({len(inp)}->{len(out)})")
    return problems


def common_prefix(a: list, b: list) -> int:
    n = 0
    for x, y in zip(a, b):
        if json.dumps(x, sort_keys=True) == json.dumps(y, sort_keys=True):
            n += 1
        else:
            break
    return n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--miner", default=str(HERE / "improved_miner.py"))
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--max", type=int, default=0, help="cap sweep size (0 = all)")
    args = ap.parse_args()
    miner = Path(args.miner)
    entries = load_io_files(Path(args.root))
    if args.max:
        entries = entries[: args.max]
    print(f"loaded {len(entries)} captured trajectories from {args.root}")

    # ---- Pass 1: sweep -----------------------------------------------------
    modes = Counter()
    savings_by_mode = defaultdict(list)
    times = []
    failures = []
    for e in entries:
        with tempfile.TemporaryDirectory() as tmp:
            t0 = time.monotonic()
            resp, _ = call_miner(miner, Path(tmp), e["messages"], "replay-sweep")
            times.append(time.monotonic() - t0)
        if not resp.get("ok"):
            failures.append((e["file"].name, f"ok=false {resp.get('error')}"))
            continue
        meta = resp["result"]["baseMiner"]
        out = resp["result"]["messages"]
        mode = meta.get("mode", "?")
        modes[mode] += 1
        it, ot = est_tokens(e["messages"]), est_tokens(out)
        if it:
            savings_by_mode[mode].append(1 - ot / it)
        for p in check_invariants(e["messages"], out, mode):
            failures.append((e["file"].name, p))

    print("\n--- sweep ---")
    for mode, n in modes.most_common():
        sv = savings_by_mode[mode]
        print(f"  {mode:<12} n={n:<4} savings mean={statistics.mean(sv):6.1%} "
              f"min={min(sv):6.1%} max={max(sv):6.1%}" if sv else f"  {mode:<12} n={n}")
    print(f"  latency: mean={statistics.mean(times)*1000:.0f}ms p95={sorted(times)[int(0.95*len(times))-1]*1000:.0f}ms max={max(times)*1000:.0f}ms")
    print(f"  invariant failures: {len(failures)}")
    for name, p in failures[:10]:
        print(f"    {name}: {p}")

    # ---- Pass 2: session replay -------------------------------------------
    sessions = defaultdict(list)
    for e in entries:
        sessions[e["session"]].append(e)
    print(f"\n--- session replay ({len(sessions)} sessions) ---")
    unstable = 0
    for sid, rounds in sessions.items():
        rounds.sort(key=lambda e: e["ts"])
        if len(rounds) < 2:
            continue
        with tempfile.TemporaryDirectory() as tmp:
            prev_out = None
            stable_min = 1.0
            last_mode = "?"
            for e in rounds:
                resp, _ = call_miner(miner, Path(tmp), e["messages"], f"replay-{sid[:24]}")
                if not resp.get("ok"):
                    failures.append((sid, "session replay ok=false"))
                    break
                out = resp["result"]["messages"]
                meta = resp["result"]["baseMiner"]
                last_mode = meta.get("mode", "?")
                if prev_out is not None and not meta.get("pruned"):
                    frac = common_prefix(prev_out, out) / max(1, len(prev_out))
                    stable_min = min(stable_min, frac)
                prev_out = out
        flag = "OK" if stable_min >= 0.8 else "UNSTABLE"
        unstable += int(stable_min < 0.8)
        print(f"  {sid[:40]:<42} rounds={len(rounds):<3} end_mode={last_mode:<7} "
              f"min_stable_prefix={stable_min:5.0%} [{flag}]")
    print(f"\nsummary: {len(entries)} trajectories, {len(failures)} failures, {unstable} unstable sessions")


if __name__ == "__main__":
    main()
