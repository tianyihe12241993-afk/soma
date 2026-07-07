#!/usr/bin/env python3
"""Passive comp-status watcher (launchd `com.soma.compwatch`, every 30 min).

Rebuilt 2026-07-07 for comp-110 + the RSC-flight dashboard (the comp-108 original was never
committed — scripts/ was gitignored). Read-only + notify-only: NEVER decides strategy or uploads.

Each run:
  1. Fetch the active comp board (RSC flight, same mechanism as collect_dashboard.py).
  2. Diff per-hotkey status vs the previous run (data/latest/.comp_watch_state.json, git-ignored).
  3. Re-check the live README allowed set (rules gate, cheap).
  4. UPSTREAM SCORING WATCH (added 2026-07-07): fetch the raw upstream scoring/contract files and
     alert on any change — whole-file SHA (never miss) + targeted extraction of the load-bearing
     constants (so the alert names exactly what moved). Watches: config.py, scoring.py,
     swebench_orchestrator.py, incentive_calculator.py, README_prompting.md (+ SOMA-benchmark
     compression service = the miner contract). Flags: screener savings gate; input/cached/output
     token weights; compute_weighted_tokens; explore tau; quality gate/floor; screener qualification;
     incentive layer weights; miner contract; allowed markers. WHY: the SOMA team said the score
     formula is actively changing (DISCOVERIES 2026-07-07) — do NOT build/tune until it lands.
  5. On ANY change: append an ALERT block to state/comp_watch.md (tracked = handoff) and fire a
     macOS notification. No change -> just update the "last checked" heartbeat line.

Events tracked: board submissions/status transitions · comp state/window change · README allowed-set
change · upstream scoring-constant / formula / contract changes.
"""
from __future__ import annotations
import hashlib
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

_RAW_SOMA = "https://raw.githubusercontent.com/DendriteHQ/SOMA/main/"
_RAW_BENCH = "https://raw.githubusercontent.com/DendriteHQ/SOMA-benchmark/main/"


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())


def _field(name: str) -> tuple[str, int]:
    # a pydantic `<name>: float|int = Field(default=<value>,` (value may span the newline)
    return (rf"{name}\s*:\s*(?:float|int)\s*=\s*Field\(\s*default\s*=\s*([0-9.\s/]+?)\s*[,)]", re.S)


# label -> (raw_url, {signal_name: (regex, flags)}); whole-file SHA is always tracked too.
_UPSTREAM: dict[str, tuple[str, dict[str, tuple[str, int]]]] = {
    "config.py": (_RAW_SOMA + "mcp_platform/app/core/config.py", {
        "screener_savings_gate": _field("swebench_screening_min_weighted_token_saving_ratio"),
        "screener_pass_ratio": _field("swebench_screening_pass_ratio"),
        "input_token_weight": _field("swebench_screening_input_tokens_weight"),
        "cached_token_weight": _field("swebench_screening_cached_input_tokens_weight"),
        "output_token_weight": _field("swebench_screening_output_tokens_weight"),
        "screener_task_count": _field("swebench_dynamic_screener_task_count"),
        "screener_min_passed_tasks": _field("swebench_screening_min_passed_tasks"),
    }),
    "scoring.py": (_RAW_SOMA + "mcp_platform/app/api/routes/scoring.py", {
        "explore_quality_delta": (r"EXPLORE_QUALITY_DELTA\s*=\s*([\-0-9.]+)", 0),
        "explore_score_floor": (r"EXPLORE_SCORE_FLOOR\s*=\s*([\-0-9.]+)", 0),
        "explore_tau_line": (r"(tau\s*=\s*max\(.*?log2.*?\)\s*\))", re.S),
        "explore_gate_line": (r"(gate\s*=\s*[^\n]+)", 0),
        "explore_total_blend": (r"s_ratio\s*\+\s*([0-9.]+)\)\s*/\s*([0-9.]+)", re.S),
        "weighted_tokens_return": (r"(input_weight \* float\(input_tokens\).*?output_weight \* float\(output_tokens\)\))", re.S),
        "swe_savings_multiplier_norm": (r"savings_ratio\s*\+\s*([0-9.]+)\)\s*/\s*([0-9.]+)", 0),
        "base_swe_scores": (r"(if baseline_pass and compressed_pass:.*?return 0\.0, 0\.1)", re.S),
    }),
    "swebench_orchestrator.py": (_RAW_SOMA + "mcp_platform/app/services/swebench_orchestrator.py", {
        "screener_benchmark_types": (r"for benchmark_type in \(([^)]*)\):", 0),
        "qualification_return": (r"(return True, weighted_savings_ratio >= [^\n]+)", 0),
        "required_ratio_fn": (r"def _required_screening_weighted_token_saving_ratio.*?return (.+?)\n", re.S),
    }),
    "incentive_calculator.py": (_RAW_SOMA + "mcp_platform/app/services/incentive_calculator.py", {
        "layer_weight_formula": (r"layer_weight\s*=\s*(.+?)\n", 0),
        "element_weight_formula": (r"element_weight\s*=\s*(.+?)\n", 0),
    }),
    "README_prompting.md": (_RAW_SOMA + "miner/README_prompting.md", {}),   # allowed-set via the rules gate; SHA catches prose
    "contract(bench)": (_RAW_BENCH + "src/compression_service/app/main.py", {
        "compressor_candidate_names": (r"COMPRESSOR_CANDIDATE_NAMES\s*=\s*\(([^)]*)\)", re.S),
        "transform_endpoint": (r'@app\.post\(\s*"(/[^"]+)"', 0),
    }),
}


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "soma-ops-collector/1.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")


def check_upstream_code(prev: dict) -> tuple[list[str], dict]:
    """Fetch each monitored upstream file; alert on SHA change (catch-all) + named-signal changes."""
    prev_up = prev.get("upstream") or {}
    alerts: list[str] = []
    new_up: dict = {}
    for label, (url, sigs) in _UPSTREAM.items():
        try:
            txt = _fetch(url)
        except Exception as e:
            alerts.append(f"- ⚠️ upstream fetch FAILED [{label}]: {e}")
            new_up[label] = prev_up.get(label) or {}       # keep old baseline; don't lose it
            continue
        sha = hashlib.sha256(txt.encode("utf-8", "replace")).hexdigest()[:16]
        vals: dict[str, str] = {}
        for name, (pat, flags) in sigs.items():
            m = re.search(pat, txt, flags)
            vals[name] = _norm(m.group(0) if m and m.lastindex is None else (m.group(1) if m else "")) if m else "<NOT-FOUND>"
            if m and m.lastindex and m.lastindex > 1:       # multi-group (e.g. two constants)
                vals[name] = _norm(" / ".join(m.group(i) for i in range(1, m.lastindex + 1)))
        cur = {"sha": sha, "signals": vals}
        old = prev_up.get(label)
        if old:
            file_flagged = False
            for name, v in vals.items():
                ov = (old.get("signals") or {}).get(name)
                if ov is not None and ov != v:
                    alerts.append(f"- 🎯 SCORING/CONTRACT CHANGE [{label}] {name}: `{ov}` → `{v}`")
                    file_flagged = True
            if old.get("sha") and old["sha"] != sha and not file_flagged:
                alerts.append(f"- 👀 [{label}] changed (sha {old['sha']} → {sha}) — no tracked constant moved; REVIEW the diff")
        new_up[label] = cur
    return alerts, new_up


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

    # --- upstream scoring / contract watch ---
    try:
        up_alerts, upstream_state = check_upstream_code(prev)
        alerts.extend(up_alerts)
    except Exception as e:
        alerts.append(f"- ⚠️ upstream scoring watch failed: {e}")
        upstream_state = prev.get("upstream") or {}

    # --- persist + report ---
    STATE_JSON.parent.mkdir(parents=True, exist_ok=True)
    STATE_JSON.write_text(json.dumps(
        {"checked_at": utc_now(),
         "comp": {k: (active or {}).get(k) for k in ("competition_id", "competition_name", "state")},
         "statuses": statuses, "readme": readme_state, "upstream": upstream_state}, indent=1))

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
