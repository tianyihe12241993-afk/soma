#!/usr/bin/env python3
"""Passive comp-status watcher (launchd `com.soma.compwatch`, every 30 min).

Rebuilt 2026-07-07 for comp-110 + the RSC-flight dashboard (the comp-108 original was never
committed — scripts/ was gitignored). Read-only + notify-only: NEVER decides strategy or uploads.

Each run:
  1. Fetch the active comp board (RSC flight, same mechanism as collect_dashboard.py).
  2. Diff per-hotkey status vs the previous run (data/latest/.comp_watch_state.json, git-ignored).
  3. Re-check the live README allowed set (rules gate, cheap).
  4. On ANY change: append an ALERT block to state/comp_watch.md (tracked = handoff) and fire a
     macOS notification. No change -> just update the "last checked" heartbeat line.

Events tracked: new submission on the board · any status transition (in queue -> screening ->
scored / failed review) · miner disappearing · README allowed-set change · comp state/window change.
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import RAW, utc_now  # noqa: E402
from collect_runs import extract_flight, balanced  # noqa: E402
from check_readme_current import fetch_readme, extract_allowed, BASELINE  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STATE_JSON = ROOT / "data" / "latest" / ".comp_watch_state.json"      # git-ignored machine state
WATCH_MD = ROOT / "state" / "comp_watch.md"                            # tracked handoff
DASH_URL = "https://thesoma.ai/dashboard"


def fetch_board() -> tuple[dict | None, dict[str, str]]:
    req = urllib.request.Request(DASH_URL, headers={"User-Agent": "soma-ops-collector/1.0"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
    flight = extract_flight(html)
    comps = balanced(flight, "competitions") or []
    active = next((c for c in comps if c.get("is_active")), None)
    rows = balanced(flight, "sweMiners") or balanced(flight, "miners") or []
    statuses = {}
    for r in rows:
        hk = r.get("hotkey") or ""
        if re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{48}", hk):
            score = r.get("total_score") if r.get("total_score") is not None else r.get("score")
            statuses[hk] = f"{r.get('status') or '?'}" + (f" @ {score:.4f}" if isinstance(score, (int, float)) else "")
    return active, statuses


def notify(title: str, msg: str) -> None:
    try:
        subprocess.run(["osascript", "-e",
                        f'display notification {json.dumps(msg)} with title {json.dumps(title)} sound name "Glass"'],
                       timeout=10, capture_output=True)
    except Exception:
        pass  # notification is best-effort; the .md alert is the record


def main() -> int:
    prev = {}
    if STATE_JSON.exists():
        try:
            prev = json.loads(STATE_JSON.read_text())
        except json.JSONDecodeError:
            prev = {}

    alerts: list[str] = []

    # --- board ---
    try:
        active, statuses = fetch_board()
    except Exception as e:
        alerts.append(f"- ⚠️ board fetch FAILED: {e}")
        active, statuses = None, dict(prev.get("statuses") or {})
    else:
        old = prev.get("statuses") or {}
        for hk, st in sorted(statuses.items()):
            if hk not in old:
                alerts.append(f"- 🆕 NEW submission: `{hk[:12]}…` → {st}")
            elif old[hk] != st:
                alerts.append(f"- 🔔 STATUS CHANGE: `{hk[:12]}…` {old[hk]} → **{st}**")
        for hk in sorted(set(old) - set(statuses)):
            alerts.append(f"- ❌ DROPPED from board: `{hk[:12]}…` (was {old[hk]})")
        comp_sig = {k: (active or {}).get(k) for k in ("competition_id", "competition_name", "state")}
        if prev.get("comp") and prev["comp"] != comp_sig:
            alerts.append(f"- 🏁 COMP CHANGE: {prev['comp']} → {comp_sig}")

    # --- rules gate ---
    readme_state = prev.get("readme", "baseline")
    try:
        live = extract_allowed(fetch_readme())
        removed, added = BASELINE - live, live - BASELINE
        cur = "baseline" if not (removed or added) else f"removed={sorted(removed)} added={sorted(added)}"
        if cur != readme_state:
            sev = "🚫 BLOCK" if removed else "👀 REVIEW"
            alerts.append(f"- {sev} README allowed-set changed: {cur}")
        readme_state = cur
    except Exception as e:
        alerts.append(f"- ⚠️ README fetch failed (gate unknown): {e}")

    # --- persist + report ---
    STATE_JSON.parent.mkdir(parents=True, exist_ok=True)
    STATE_JSON.write_text(json.dumps(
        {"checked_at": utc_now(),
         "comp": {k: (active or {}).get(k) for k in ("competition_id", "competition_name", "state")},
         "statuses": statuses, "readme": readme_state}, indent=1))

    header = f"# comp watch — active: {(active or {}).get('competition_name', '?')} " \
             f"(id {(active or {}).get('competition_id', '?')}, state {(active or {}).get('state', '?')})\n"
    heartbeat = f"_last checked {utc_now()} — {len(statuses)} on board, {len(alerts)} alert(s)_\n"
    old_body = WATCH_MD.read_text() if WATCH_MD.exists() else ""
    old_alerts = old_body.split("\n## ALERTS\n", 1)[1] if "\n## ALERTS\n" in old_body else ""
    new_alerts = (f"### {utc_now()}\n" + "\n".join(alerts) + "\n\n" + old_alerts) if alerts else old_alerts
    WATCH_MD.write_text(header + heartbeat + "\n## ALERTS\n" + (new_alerts or "_none yet_\n"))

    if alerts:
        notify("SOMA comp watch", f"{len(alerts)} change(s) — see state/comp_watch.md")
        print("\n".join(alerts))
    else:
        print(f"no changes ({len(statuses)} on board)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
