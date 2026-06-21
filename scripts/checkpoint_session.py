#!/usr/bin/env python3
"""Write a timestamped session checkpoint (source of truth survives compaction).

  sessions/YYYY-MM-DD_HHMMSS_<reason>.md   -- human-readable summary
  sessions/index.jsonl                      -- one appended JSONL row per checkpoint
  state/latest.md                           -- refreshed compact "where we are now" pointer

Usage: checkpoint_session.py [--reason precompact|manual|...] [--note "free text"]
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (ROOT, STATE, SESSIONS, LATEST, REPORTS, utc_now, utc_stamp,  # noqa: E402
                     read_text, git_info, load_miners, latest_processed_rows)


def _tail(path: Path, n: int) -> list:
    lines = [l for l in read_text(path).splitlines() if l.strip()
             and not l.lstrip().startswith("#")]
    return lines[-n:] if n else lines


def _scoreboard() -> tuple:
    rows = {r["hotkey"]: r for r in latest_processed_rows()}
    miners = load_miners()
    live, pending = [], []
    for name, info in miners.items():
        r = rows.get(info["hotkey"])
        if r and isinstance(r.get("overall"), (int, float)):
            live.append((name, info["version"], r["overall"], r.get("easy"), r.get("medium"), r.get("hard")))
        else:
            pending.append((name, info["version"]))
    live.sort(key=lambda x: -x[2])
    return live, pending


def _reward_winners() -> dict:
    p = LATEST / "category_winners.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text())
    return {"elements": {k: [w["name"] or w["hotkey"][:8] for w in v["winners"]]
                         for k, v in d.get("elements", {}).items()},
            "our_wins": d.get("our_element_wins", [])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reason", default="manual")
    ap.add_argument("--note", default="")
    args = ap.parse_args()

    ts = utc_now()
    g = git_info(ROOT)
    live, pending = _scoreboard()
    rw = _reward_winners()
    decisions = _tail(STATE / "DECISIONS.md", 6)
    next_actions = _tail(STATE / "NEXT_ACTIONS.md", 8)

    # ---- session markdown ----
    md = [f"# Session checkpoint — {ts}", f"**reason:** {args.reason}"]
    if args.note:
        md.append(f"**NOTE:** {args.note}")
    md += ["", f"**git:** branch `{g['branch']}`, {'dirty' if g['dirty'] else 'clean'}"]
    if g["changed"]:
        md.append("recent changes: " + ", ".join(g["changed"][:12]))
    md += ["", "## Live miners (scored)"]
    if live:
        md.append("| slot | ver | overall | E | M | H |")
        md.append("|------|-----|---------|---|---|---|")
        for n, v, o, e, m, h in live:
            md.append(f"| {n} | {v} | {o:.3f} | {e:.3f} | {m:.3f} | {h:.3f} |")
    else:
        md.append("_(no scored rows — run `make collect` then `make reward`)_")
    md += ["", "## Pending / unevaluated miners"]
    md.append(", ".join(f"{n}({v})" for n, v in pending) or "_(none)_")
    md += ["", "## Reward element winners"]
    if rw:
        for el, w in rw["elements"].items():
            md.append(f"- {el}: {', '.join(w)}")
        md.append(f"- **our element wins:** {rw['our_wins'] or 'none'}")
    else:
        md.append("_(run `make reward`)_")
    md += ["", "## Latest decisions"]
    md += [f"- {d}" for d in decisions] or ["_(none)_"]
    md += ["", "## Next actions"]
    md += [f"- {a}" for a in next_actions] or ["_(none)_"]

    SESSIONS.mkdir(parents=True, exist_ok=True)
    safe_reason = "".join(c if c.isalnum() else "-" for c in args.reason)[:24]
    sess_path = SESSIONS / f"{utc_stamp()}_{safe_reason}.md"
    sess_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    # ---- index.jsonl ----
    idx = {"ts": ts, "reason": args.reason, "note": args.note, "branch": g["branch"],
           "dirty": g["dirty"], "file": str(sess_path.relative_to(ROOT)),
           "live_best": (f"{live[0][0]}={live[0][2]:.3f}" if live else None),
           "live_count": len(live), "pending": [n for n, _ in pending],
           "our_element_wins": rw.get("our_wins", [])}
    with (SESSIONS / "index.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(idx) + "\n")

    # ---- refresh state/latest.md (compact pointer) ----
    latest = [f"# LATEST — {ts}", f"_auto-written by checkpoint ({args.reason})_", ""]
    if args.note:
        latest.append(f"**Note:** {args.note}\n")
    latest.append(f"**Best live miner:** {idx['live_best'] or 'n/a'} | "
                  f"pending: {', '.join(idx['pending']) or 'none'}")
    latest.append(f"**Our reward-element wins:** {rw.get('our_wins') or 'none'}")
    latest += ["", "**Top of NEXT_ACTIONS:**"] + [f"- {a}" for a in next_actions[:4]]
    latest += ["", f"_Full checkpoint: {sess_path.relative_to(ROOT)}_"]
    (STATE / "latest.md").write_text("\n".join(latest) + "\n", encoding="utf-8")

    print(f"checkpoint -> {sess_path.relative_to(ROOT)}  (reason={args.reason})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
