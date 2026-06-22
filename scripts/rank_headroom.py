#!/usr/bin/env python3
"""Rank a miner's SAFE compression headroom, task by task.

"Safe headroom" = a task the target miner already passes (with compression) where
some leader proved a HIGHER compression ratio also passes. The per-task score is
~ 1 + 0.5*ln(ratio) on shared-pass tasks (verified empirically), so the estimated
score gain from matching the leader's ratio is 0.5*ln(leader_ratio / our_ratio).
This is a proven-achievable UPPER BOUND, not a guarantee our approach hits it.

Reads data/latest/miner_detail.json (run collect_miner_detail.py first, including
the target + some leaders). Writes reports/headroom.md.

Usage:  python scripts/rank_headroom.py [TARGET_HOTKEY]   (default: m7 from miners.yaml)
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import LATEST, REPORTS, hotkey_to_name, load_miners  # noqa: E402

def ratio(t):
    a, b = t.get("tokens_without_compression"), t.get("tokens_with_compression")
    return a / b if (a and b) else None

def tasks(m):
    return {t["task_id"]: t for t in m.get("tasks", []) if not t.get("is_screener")}

def main() -> int:
    data = json.loads((LATEST / "miner_detail.json").read_text(encoding="utf-8"))["miners"]
    by = {m["hotkey"]: m for m in data}
    names = hotkey_to_name()
    miners = load_miners()
    target = sys.argv[1] if len(sys.argv) > 1 else miners.get("m7", {}).get("hotkey")
    if target not in by:
        print(f"target {target} not in data/latest/miner_detail.json", file=sys.stderr)
        return 1
    tgt_name = names.get(target, target[:8])
    leaders = {h: m for h, m in by.items() if h != target and h not in names}  # non-ours = rivals
    tg = tasks(by[target])
    lt = {h: tasks(m) for h, m in leaders.items()}

    rows = []
    for tid, t in tg.items():
        if not t.get("pass_with_compression"):
            continue
        r = ratio(t)
        if not r:
            continue
        best_r, who = 0.0, None
        for h, tt in lt.items():
            x = tt.get(tid)
            if x and x.get("pass_with_compression") and ratio(x) and ratio(x) > best_r:
                best_r, who = ratio(x), (names.get(h) or h[:8])
        gain = 0.5 * math.log(best_r / r) if best_r > r else 0.0
        rows.append({"task": t["task_name"],
                     "tier": "SAFE" if t.get("pass_without_compression") else "RECOVERED",
                     "r": r, "best": best_r, "who": who, "head": (best_r / r) if best_r else 0,
                     "gain": gain, "score": t.get("platform_score")})

    safe = sorted([x for x in rows if x["tier"] == "SAFE" and x["gain"] > 0], key=lambda x: -x["gain"])
    rec = sorted([x for x in rows if x["tier"] == "RECOVERED" and x["gain"] > 0], key=lambda x: -x["gain"])
    none = [x for x in rows if x["gain"] <= 0]
    tot = sum(x["gain"] for x in safe)
    base = by[target]["total_score"]

    L = [f"# {tgt_name} — safe compression headroom",
         f"_from data/latest/miner_detail.json; proven-achievable upper bound (leader passed at the higher ratio)._",
         "", f"**{len(safe)} SAFE tasks with headroom.** Est. total per-task score gain **{tot:+.2f}** "
         f"→ avg over 45 tasks **{tot/45:+.3f}** (rough lift {base:.3f} → ~{base + tot/45:.2f} if fully captured).",
         "", "## SAFE — passes baseline AND compressed; a leader proved a higher ratio still passes",
         "| task | our ratio | proven ratio | by | ×more | ~score gain | cur score |",
         "|------|-----------|--------------|----|-------|-------------|-----------|"]
    for x in safe:
        L.append(f"| {x['task']} | {x['r']:.2f}× | {x['best']:.2f}× | {x['who']} | "
                 f"{x['head']:.2f}× | {x['gain']:+.3f} | {x['score']:.3f} |")
    L += ["", "## RECOVERED — we fixed a failing baseline (✗→✓); push cautiously (may lose the recovery)",
          "| task | our ratio | proven ratio | by | ~score gain |",
          "|------|-----------|--------------|----|-------------|"]
    for x in rec:
        L.append(f"| {x['task']} | {x['r']:.2f}× | {x['best']:.2f}× | {x['who']} | {x['gain']:+.3f} |")
    L += ["", f"## No headroom — already ≥ leaders' proven ratio; don't compress more ({len(none)})"]
    for x in sorted(none, key=lambda x: -x["r"]):
        L.append(f"- {x['task']} — {x['r']:.2f}× (best leader {x['best']:.2f}×)")
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "headroom.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {REPORTS/'headroom.md'} — {len(safe)} safe headroom tasks, est +{tot/45:.3f}/task "
          f"(lift toward ~{base + tot/45:.2f} from {base:.3f})")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
