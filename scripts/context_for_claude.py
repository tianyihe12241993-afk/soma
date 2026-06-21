#!/usr/bin/env python3
"""Print a compact context block for Claude Code to read at startup/resume/compact.

Concatenates (concise, injection-safe):
  - state/latest.md
  - state/NEXT_ACTIONS.md
  - reports/reward_projection.md
  - last 3 session checkpoint summaries (from sessions/index.jsonl)

Designed to be the FIRST thing Claude reads so chat history is never the source of truth.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ROOT, STATE, REPORTS, SESSIONS, read_text  # noqa: E402

MAX = 1800  # per-section char cap to keep the block small


def _clip(text: str, n: int = MAX) -> str:
    text = text.strip()
    return text if len(text) <= n else text[:n] + "\n…[truncated]…"


def main() -> int:
    out = ["==================== SOMA-ops CONTEXT (read this first; files are the source of truth, not chat) ===================="]

    out += ["", "### state/latest.md", _clip(read_text(STATE / "latest.md", "(empty)"))]
    out += ["", "### state/NEXT_ACTIONS.md", _clip(read_text(STATE / "NEXT_ACTIONS.md", "(empty)"))]
    out += ["", "### reports/reward_projection.md", _clip(read_text(REPORTS / "reward_projection.md", "(run `make reward`)"))]

    out += ["", "### last 3 session checkpoints"]
    idx_path = SESSIONS / "index.jsonl"
    if idx_path.exists():
        rows = [json.loads(l) for l in idx_path.read_text().splitlines() if l.strip()][-3:]
        for r in reversed(rows):
            out.append(f"- [{r['ts']}] reason={r['reason']} best={r.get('live_best')} "
                       f"pending={','.join(r.get('pending', [])) or '-'} "
                       f"our_wins={r.get('our_element_wins') or 'none'}"
                       + (f" note={r['note']}" if r.get('note') else ""))
    else:
        out.append("- (no checkpoints yet — run `make checkpoint NOTE=\"...\"`)")

    out += ["", "### operating reminder",
            "Read state/CURRENT.md, NEXT_ACTIONS.md, DECISIONS.md, SCOREBOARD.md before acting.",
            "Update state/latest.md + run `make checkpoint` after important results.",
            "Never submit/modify miner code unless explicitly told. Never overwrite raw snapshots or write secrets.",
            "=" * 110]
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
