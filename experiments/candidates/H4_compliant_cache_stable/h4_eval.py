#!/usr/bin/env python3
"""Offline evaluation harness for H4_compliant_cache_stable (stdlib only).

Runs the H4 miner through the exact compression-service subprocess protocol on a
fixture set and asserts the round's compliance + safety properties, then compares
H4 against H3 on the SAME fixtures (compression ratio, prefix/cache-stability,
protection regression). Prints a PASS/FAIL table and EXITS NONZERO on any fail.

WHAT THIS MEASURES (offline, real): compression ratio, structural safety
(load-bearing preservation + tool-call/result pairing), in-place tool-result body
masking, marker-set compliance, loop-reason compliance, absence of force-stop /
behavior-steering language (via scripts/check_prompt_compliance.py), and
prefix/cache-stability across appended turns.

WHAT THIS CANNOT MEASURE offline: real platform pass/fail. Structural-safety
(protected content survives) is a pass-safety PROXY, not a guarantee.

Tests (each row PASS/FAIL):
  1  task instruction preserved byte-identical
  2  failing-test names preserved
  3  assertion lines preserved
  4  traceback tail preserved
  5  file paths preserved
  6  active patch/diff preserved
  7  tool-call/tool-result pairing integrity (no new orphans)
  8  tool-result bodies masked in place (message + tool_call_id kept, body changed)
  9  ONLY allowed markers appear in output
  10 ONLY allowed loop-reason strings appear in output
  11 NO force-stop/behavior-steering language in output or source (calls the scanner)
  12 prefix/cache-stability across appended turns >= H3 on the same growing trajectory

Outputs: ../../../data/latest/h4_compliance_results.json + a console table.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent                       # repo root
MINER_DIR = ROOT / "miner" / "cot_compression"
sys.path.insert(0, str(MINER_DIR))
from test_improved_miner import parse_transcript, est_tokens, text_of, tool_ids  # noqa: E402

H4 = HERE / "h4_miner.py"
H3 = ROOT / "experiments" / "candidates" / "H3_cache_stable_depth_v1" / "h3_miner.py"
SCANNER = ROOT / "scripts" / "check_prompt_compliance.py"
SAMPLES = ROOT / "miner" / "plain_text_compression" / "sample_tasks" / "cot_compression_tasks.jsonl"

# Allowed marker/loop-reason sets (mirrors README §5 and the scanner).
ALLOWED_MARKER_TOKENS = {"[[CMP]]", "[[/CMP]]"}
ALLOWED_BLOCK_OPEN = re.compile(r"^\[\[BLOCK \d+\]\]$")
ALLOWED_BLOCK_CLOSE = re.compile(r"^\[\[/BLOCK \d+\]\]$")
ALLOWED_LOOP_REASONS = {
    "loop_detected: repeated assistant response",
    "loop_detected: repeated tool call signature",
}
_BRACKET_TOKEN = re.compile(r"\[\[[^\[\]]*\]\]")
_LOOP_REASON = re.compile(r"loop_detected:[^\"'\\\n]*")
FORBIDDEN_OUTPUT = [
    "STOP NOW", "stop and return", "do not explore", "change your approach",
    "solution is complete", "tests pass, stop", "[SOMA", "CONTEXT NOTE",
    "COMPRESSED HISTORY", "[soma", "old output elided", "old file view elided",
]

# Protected sentinels embedded in the synthetic fixtures (preservation = pass-safety).
MARK_TASK = "SOMA-H4-TASK-INSTRUCTION-KEEPME"
MARK_TEST = "test_h4_protected_signal"
MARK_ASSERT = "AssertionError: h4 sentinel 42 != 7"
MARK_TRACE = "h4_module/core.py"
MARK_DIFF_PATH = "django/utils/html.py"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def synth_harvest_clean(rounds: int = 30) -> list[dict]:
    """SHALLOW, LARGE, CLEAN/RESOLVING trajectory (no recent errors) → stays in HARVEST
    for both H3 and H4 → exercises the CMP body-mask + superseded-view dedup path.
    Embeds protected markers (task instruction, file path, test name) and a current
    diff so protection can be measured."""
    file_read = ("def escape(s):\n    return s.replace('<','&lt;')\n"
                 f"# module: {MARK_DIFF_PATH} implementation notes\n" * 26)
    parts = [f'<message role="user"><text>{MARK_TASK}: make escape() handle None in '
             f'{MARK_DIFF_PATH}. Output a unified diff. Do not modify the tests.</text></message>']
    for k in range(1, rounds + 1):
        parts.append(f'<message role="assistant"><thinking>step {k} review</thinking>'
                     f'<tool_call name="read_file" id="c{k}">{{"path":"{MARK_DIFF_PATH}"}}'
                     f'</tool_call></message>')
        parts.append(f'<tool_result tool="read_file" tool_call_id="c{k}">{file_read}</tool_result>')
    # a current patch/diff the agent is holding (must survive)
    parts.append('<message role="assistant"><thinking>apply the fix</thinking>'
                 '<tool_call name="apply_patch" id="cdiff">{"patch":"see diff"}</tool_call></message>')
    parts.append(f'<tool_result tool="apply_patch" tool_call_id="cdiff">'
                 f'diff --git a/{MARK_DIFF_PATH} b/{MARK_DIFF_PATH}\n'
                 f'--- a/{MARK_DIFF_PATH}\n+++ b/{MARK_DIFF_PATH}\n'
                 f'@@ -1,2 +1,3 @@\n+    if s is None:\n+        return ""\n     return s.replace("<","&lt;")\n'
                 f'</tool_result>')
    # clean final round (PASSED) so the recent window has no errors -> harvest
    parts.append('<message role="assistant"><thinking>run tests</thinking>'
                 '<tool_call name="run_tests" id="cok">{"k":"html"}</tool_call></message>')
    parts.append(f'<tool_result tool="run_tests" tool_call_id="cok">Ran 1 test in 0.2s OK\n'
                 f'utils/test_html.py::{MARK_TEST} PASSED\nfile: {MARK_TRACE}</tool_result>')
    return parse_transcript("\n".join(parts))


def synth_errdense(rounds: int = 30) -> list[dict]:
    """SHALLOW, LARGE, error-bearing trajectory → routes to RICH (fragile guard) for both.
    Exercises the gentle/RICH dedup path and protected-content preservation under the
    most safety-critical regime. Embeds task instruction, failing test, assertion,
    traceback tail, file paths."""
    big_log = ("running: pytest tests/test_core.py\n" + "noise output line\n" * 40 +
               f"FAILED tests/test_core.py::{MARK_TEST}\n{MARK_ASSERT}\n"
               f'Traceback (most recent call last):\n  File "{MARK_TRACE}", line 88, in run\n'
               "    raise ValueError(x)\n")
    parts = [f'<message role="user"><text>{MARK_TASK}: fix the failing test in {MARK_TRACE}. '
             f'Problem: run() raises on None.</text></message>']
    for k in range(1, rounds + 1):
        body = big_log.replace("line 88", f"line {80 + k}")
        parts.append(f'<message role="assistant"><thinking>step {k}: inspect and edit</thinking>'
                     f'<tool_call name="run_tests" id="c{k}">{{"k":"core"}}</tool_call></message>')
        parts.append(f'<tool_result tool="run_tests" tool_call_id="c{k}">{body}</tool_result>')
    # most-recent round carries the live ground truth that MUST survive intact
    parts.append('<message role="assistant"><thinking>final run</thinking>'
                 '<tool_call name="run_tests" id="cfinal">{"k":"core"}</tool_call></message>')
    parts.append(f'<tool_result tool="run_tests" tool_call_id="cfinal">'
                 f'FAILED tests/test_core.py::{MARK_TEST}\n{MARK_ASSERT}\n'
                 f'Traceback (most recent call last):\n  File "{MARK_TRACE}", line 88, in run\n'
                 f'    return go(s)\n</tool_result>')
    return parse_transcript("\n".join(parts))


def synth_loop(rounds: int = 16) -> list[dict]:
    """A no-progress LOOP: the same tool call with identical args repeated many times
    (and identical assistant responses). Exercises the compliant loop guard. CLEAN
    (no errors) and large enough to clear the passthrough threshold so the guard path
    actually runs (loop detection only fires once compression is active)."""
    # Each round carries a sizeable but identical, error-free body so the trajectory
    # clears PASS_THROUGH_TOKENS (-> harvest) yet never trips the fragile/rich guard.
    body = ("def escape(s):\n    return s\n"
            f"# inspecting {MARK_DIFF_PATH} (no change this pass)\n" * 30)
    parts = [f'<message role="user"><text>{MARK_TASK}: investigate {MARK_DIFF_PATH}.</text></message>']
    for k in range(1, rounds + 1):
        parts.append('<message role="assistant"><text>Let me look again.</text>'
                     f'<tool_call name="read_file" id="c{k}">{{"path":"{MARK_DIFF_PATH}"}}</tool_call></message>')
        parts.append(f'<tool_result tool="read_file" tool_call_id="c{k}">{body}</tool_result>')
    return parse_transcript("\n".join(parts))


# ---------------------------------------------------------------------------
# Subprocess driver
# ---------------------------------------------------------------------------

def call(miner: Path, messages: list[dict], plugin_dir: str, session_id: str = "h4-eval") -> dict:
    """Single-shot call. Each fixture passes a UNIQUE session_id so per-session state
    (the sticky passthrough->harvest->rich mode ratchet) never leaks between fixtures;
    a fixture is judged on a clean session, exactly as the platform runs one task."""
    payload = {"pluginId": "soma-miner", "pluginName": "SOMA", "pluginDir": plugin_dir,
               "params": {"messages": messages, "sessionId": session_id,
                          "sessionKey": None, "currentTokenCount": est_tokens(messages)},
               "sourceHook": "assemble"}
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        proc = subprocess.run([sys.executable, str(miner), "assemble"],
                              input=json.dumps(payload, ensure_ascii=False),
                              capture_output=True, text=True, encoding="utf-8",
                              timeout=120, env=env)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}
    if proc.returncode != 0:
        return {"ok": False, "error": (proc.stderr or "")[-400:]}
    if not proc.stdout:
        return {"ok": False, "error": "empty stdout; stderr=" + (proc.stderr or "")[-300:]}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return {"ok": False, "error": f"bad json: {e}; head={proc.stdout[:200]!r}"}


def out_text(messages: list[dict]) -> str:
    return "\n".join(text_of(m.get("content")) for m in messages if isinstance(m, dict))


def first_user_text(messages: list[dict]) -> str:
    for m in messages:
        if isinstance(m, dict) and str(m.get("role", "")).lower() == "user":
            return text_of(m.get("content"))
    return ""


def first_user_byte_identical(inp: list[dict], out: list[dict]) -> bool:
    """The original task statement (first user message) must be preserved byte-identical
    — neither path compresses the frozen head, so the exact text must reappear verbatim
    somewhere in the output (the connector may re-wrap blocks, so compare on text)."""
    fu = first_user_text(inp).strip()
    if not fu:
        return True
    return fu in out_text(out)


def body_masked_in_place(inp: list[dict], out: list[dict]) -> bool:
    """At least one tool-result kept its envelope + tool_call_id but had its body
    text changed (the in-place mask), and NO tool-result lost its tool_call_id."""
    def by_id(msgs):
        d = {}
        for m in msgs:
            if not isinstance(m, dict) or str(m.get("role", "")).lower().replace("_", "") != "toolresult":
                continue
            rid = m.get("toolCallId") or m.get("toolUseId") or m.get("id")
            if rid:
                d[rid] = text_of(m.get("content"))
        return d
    bin_, bout = by_id(inp), by_id(out)
    # every kept tool-result retains its id (no envelope lost for surviving ids)
    ids_preserved = all(rid in bout for rid in bin_ if rid in {
        (m.get("toolCallId") or m.get("toolUseId") or m.get("id"))
        for m in out if isinstance(m, dict)
        and str(m.get("role", "")).lower().replace("_", "") == "toolresult"})
    changed = any(rid in bout and bout[rid] != bin_[rid] for rid in bin_)
    return changed and ids_preserved


def markers_ok(text: str) -> tuple[bool, list[str]]:
    bad = []
    for tok in set(_BRACKET_TOKEN.findall(text)):
        if tok in ALLOWED_MARKER_TOKENS:
            continue
        if ALLOWED_BLOCK_OPEN.match(tok) or ALLOWED_BLOCK_CLOSE.match(tok):
            continue
        bad.append(tok)
    return (not bad), sorted(bad)


def loop_reasons_ok(text: str) -> tuple[bool, list[str]]:
    bad = [r.strip() for r in _LOOP_REASON.findall(text) if r.strip() not in ALLOWED_LOOP_REASONS]
    return (not bad), sorted(set(bad))


def forbidden_in(text: str) -> list[str]:
    return [s for s in FORBIDDEN_OUTPUT if s in text]


# ---------------------------------------------------------------------------
# Prefix / cache-stability across appended turns (test 12 + comparison)
# ---------------------------------------------------------------------------

def growing_trajectory(rounds: int = 26) -> list[list[dict]]:
    """Return a list of cumulative trajectories t1..tN where each t_{k+1} is t_k with one
    more (assistant tool-call + clean tool-result) round appended — the real connector
    growth pattern. Clean so it stays in harvest (cache-stable regime)."""
    base = synth_harvest_clean(rounds)
    # snapshots after each tool-result boundary (a "turn"), starting once there is
    # enough history that compression can engage
    snaps = []
    for end in range(6, len(base) + 1):
        snaps.append(base[:end])
    return snaps


def stable_prefix_turns(miner: Path, snaps: list[list[dict]], plugin_dir: str, session_id: str) -> dict:
    """For a sequence of growing trajectories, run the miner on each and hash the emitted
    CACHE-STABLE PREFIX (everything before the recent-intact tail boundary). Count how
    many consecutive turn-to-turn transitions kept a STABLE shared prefix — i.e. the
    earlier turn's prefix bytes are a prefix of the later turn's emitted messages. More
    stable transitions = fewer cache invalidations = better cache reuse. All snapshots
    share ONE session id so the miner's incremental state carries across turns (the real
    growth pattern)."""
    # Import the miner module to use its own prefix_boundary (head + masked old region).
    import importlib.util
    spec = importlib.util.spec_from_file_location(f"_m_{miner.stem}", miner)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    prev_prefix_blob = None
    stable = 0
    total = 0
    boundaries = []
    for snap in snaps:
        r = call(miner, snap, plugin_dir, session_id=session_id)
        if not r.get("ok"):
            return {"ok": False, "error": r.get("error")}
        out = r["result"]["messages"]
        boundary = mod.prefix_boundary(out)
        boundaries.append(boundary)
        # canonical bytes of the cache-stable prefix region
        prefix_blob = mod.canonical_json(out[:boundary])
        if prev_prefix_blob is not None:
            total += 1
            # stable transition := previous prefix region is a byte-prefix of the new
            # one (the new turn only appended; the old cached region was not rewritten)
            if prefix_blob.startswith(prev_prefix_blob):
                stable += 1
        prev_prefix_blob = prefix_blob
    return {"ok": True, "stable_transitions": stable, "total_transitions": total,
            "stable_ratio": round(stable / total, 4) if total else None,
            "mean_boundary": round(sum(boundaries) / len(boundaries), 2) if boundaries else None}


# ---------------------------------------------------------------------------
# Per-fixture compliance + safety checks (tests 1-11)
# ---------------------------------------------------------------------------

def check_fixture(name: str, miner: Path, msgs: list[dict], plugin_dir: str) -> dict:
    in_text = out_text(msgs)
    r = call(miner, msgs, plugin_dir, session_id=f"h4-fix-{name}")
    if not r.get("ok"):
        return {"case": name, "ok": False, "error": r.get("error")}
    res = r["result"]
    out = res["messages"]
    o_text = out_text(out)
    meta = res.get("baseMiner", {})

    in_res, in_call = tool_ids(msgs)
    out_res, out_call = tool_ids(out)

    # only require preservation for markers that were actually IN the input
    prot = {m: (m in o_text) for m in (MARK_TASK, MARK_TEST, MARK_ASSERT, MARK_TRACE, MARK_DIFF_PATH) if m in in_text}

    mk_ok, bad_mk = markers_ok(o_text)
    lr_ok, bad_lr = loop_reasons_ok(o_text)
    forb = forbidden_in(o_text)

    return {
        "case": name, "ok": True, "mode": meta.get("mode"),
        "tokens_in": est_tokens(msgs), "tokens_out": est_tokens(out),
        "ratio": round(est_tokens(msgs) / est_tokens(out), 3) if est_tokens(out) else None,
        # test 1: task instruction byte-identical. The synthetic fixtures embed
        # MARK_TASK; for real sample transcripts (no sentinel) we instead require the
        # first user message to survive byte-identical in the output.
        "task_preserved": (MARK_TASK in o_text) if MARK_TASK in in_text
                          else first_user_byte_identical(msgs, out),
        # tests 2-6: protected content present (only those present in input)
        "failing_test_preserved": prot.get(MARK_TEST, True),
        "assertion_preserved": prot.get(MARK_ASSERT, True),
        "traceback_preserved": prot.get(MARK_TRACE, True),
        "paths_preserved": prot.get(MARK_DIFF_PATH, True),
        "diff_preserved": ("diff --git" in o_text) if "diff --git" in in_text else True,
        # test 7: no NEW orphans
        "pairing_ok": out_res <= in_res and out_call <= in_call,
        # test 8: in-place body mask (only meaningful when something was masked)
        "masked_in_place": body_masked_in_place(msgs, out) if (
            meta.get("maskedToolResults") or meta.get("duplicateResultCount")
            or meta.get("nearDuplicateResultCount") or meta.get("elidedFileViews")) else True,
        # test 9 / 10 / 11
        "markers_ok": mk_ok, "bad_markers": bad_mk,
        "loop_reasons_ok": lr_ok, "bad_loop_reasons": bad_lr,
        "no_forbidden_output": not forb, "forbidden_found": forb,
        "loopGuardFired": meta.get("loopGuardFired"),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_scanner(target: Path) -> dict:
    proc = subprocess.run([sys.executable, str(SCANNER), str(target)],
                          capture_output=True, text=True)
    return {"target": str(target), "exit": proc.returncode,
            "pass": proc.returncode == 0, "report": proc.stdout.strip()}


def main() -> int:
    samples = []
    if SAMPLES.exists():
        samples = [parse_transcript(json.loads(l)["source_text"])
                   for l in SAMPLES.read_text(encoding="utf-8").splitlines() if l.strip()]
    fixtures = [(f"sample-{i}", m) for i, m in enumerate(samples, 1)]
    fixtures += [
        ("synth-harvest-clean", synth_harvest_clean(30)),
        ("synth-harvest-big", synth_harvest_clean(40)),
        ("synth-errdense-rich", synth_errdense(30)),
        ("synth-loop", synth_loop(8)),
    ]

    results = {
        "computed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": "Offline compliance + structural-safety + cache-stability for "
                "H4_compliant_cache_stable vs H3. Platform pass/fail = PENDING_EVAL "
                "(needs SOMA SWE-bench). Structural-safety is a pass-safety PROXY.",
    }

    with tempfile.TemporaryDirectory() as d4, tempfile.TemporaryDirectory() as d3:
        # --- Scanner verdicts (test 11 source-side; sanity on H3) ---
        results["scanner"] = {
            "h4": run_scanner(H4),
            "h3_sanity_should_fail": run_scanner(H3),
        }

        # --- Per-fixture checks on H4 (tests 1-11) ---
        rows = [check_fixture(name, H4, msgs, d4) for name, msgs in fixtures]
        results["h4_fixture_checks"] = rows

        # --- H3 vs H4 compression ratio on the SAME fixtures ---
        comp = []
        for name, msgs in fixtures:
            r4 = call(H4, msgs, d4, session_id=f"cmp4-{name}")
            r3 = call(H3, msgs, d3, session_id=f"cmp3-{name}")
            if not (r4.get("ok") and r3.get("ok")):
                comp.append({"case": name, "ok": False,
                             "h4_err": r4.get("error"), "h3_err": r3.get("error")})
                continue
            o4, o3 = r4["result"]["messages"], r3["result"]["messages"]
            t_in = est_tokens(msgs)
            t4, t3 = est_tokens(o4), est_tokens(o3)
            ratio4 = t_in / t4 if t4 else None
            ratio3 = t_in / t3 if t3 else None
            # protection regression: any sentinel H3 kept that H4 dropped?
            in_text = out_text(msgs)
            txt4, txt3 = out_text(o4), out_text(o3)
            regress = [s for s in (MARK_TASK, MARK_TEST, MARK_ASSERT, MARK_TRACE, MARK_DIFF_PATH)
                       if s in in_text and s in txt3 and s not in txt4]
            comp.append({
                "case": name, "ok": True,
                "mode_h4": r4["result"]["baseMiner"].get("mode"),
                "mode_h3": r3["result"]["baseMiner"].get("mode"),
                "tokens_in": t_in, "tokens_out_h4": t4, "tokens_out_h3": t3,
                "ratio_h4": round(ratio4, 3) if ratio4 else None,
                "ratio_h3": round(ratio3, 3) if ratio3 else None,
                "ratio_delta_pct": round((ratio4 / ratio3 - 1) * 100, 2) if (ratio4 and ratio3) else None,
                "protection_regression": regress,
            })
        results["h3_vs_h4_compression"] = comp

        # --- Prefix / cache-stability across appended turns (test 12 + comparison) ---
        snaps = growing_trajectory(26)
        stab4 = stable_prefix_turns(H4, snaps, d4, session_id="stab4")
        stab3 = stable_prefix_turns(H3, snaps, d3, session_id="stab3")
        results["prefix_stability"] = {"h4": stab4, "h3": stab3,
            "h4_at_least_as_good": (
                stab4.get("ok") and stab3.get("ok")
                and (stab4.get("stable_ratio") or 0) >= (stab3.get("stable_ratio") or 0))}

    # ---- Build the PASS/FAIL test table (12 tests) ----
    rows = results["h4_fixture_checks"]
    ok_rows = [r for r in rows if r.get("ok")]
    masked_cases = [r for r in ok_rows if r["mode"] == "harvest"]
    loop_cases = [r for r in ok_rows if r["loopGuardFired"]]

    def allrows(key, default=True):
        return all(r.get(key, default) for r in ok_rows)

    stab = results["prefix_stability"]
    table = [
        ("1  task instruction preserved byte-identical", allrows("task_preserved")),
        ("2  failing-test names preserved", allrows("failing_test_preserved")),
        ("3  assertion lines preserved", allrows("assertion_preserved")),
        ("4  traceback tail preserved", allrows("traceback_preserved")),
        ("5  file paths preserved", allrows("paths_preserved")),
        ("6  active patch/diff preserved", allrows("diff_preserved")),
        ("7  tool-call/tool-result pairing integrity", allrows("pairing_ok")),
        ("8  tool-result bodies masked in place", allrows("masked_in_place")
            and any(r["mode"] == "harvest" for r in ok_rows)),
        ("9  ONLY allowed markers in output", allrows("markers_ok")),
        ("10 ONLY allowed loop-reason strings in output", allrows("loop_reasons_ok")),
        ("11 NO force-stop/steering (output + source scan)",
            allrows("no_forbidden_output") and results["scanner"]["h4"]["pass"]),
        ("12 prefix/cache-stability >= H3", bool(stab.get("h4_at_least_as_good"))),
        ("--  sanity: scanner FAILS on H3 (coach present)",
            not results["scanner"]["h3_sanity_should_fail"]["pass"]),
        ("--  all fixtures ran ok", len(ok_rows) == len(rows) and len(rows) > 0),
        ("--  loop guard fired on synth-loop with an allowed reason",
            any(r["case"] == "synth-loop" and r["loopGuardFired"] in ALLOWED_LOOP_REASONS
                for r in ok_rows)),
    ]
    results["test_table"] = [{"test": t, "pass": bool(p)} for t, p in table]

    res_path = ROOT / "data" / "latest" / "h4_compliance_results.json"
    res_path.parent.mkdir(parents=True, exist_ok=True)
    res_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # ---- Console report ----
    print("=" * 72)
    print("H4_compliant_cache_stable — offline compliance + safety eval")
    print("=" * 72)
    print(f"scanner H4: {'PASS' if results['scanner']['h4']['pass'] else 'FAIL'}  "
          f"(exit {results['scanner']['h4']['exit']})")
    print(f"scanner H3 (sanity, expect FAIL): "
          f"{'FAIL' if not results['scanner']['h3_sanity_should_fail']['pass'] else 'PASS(!)'}"
          f"  (exit {results['scanner']['h3_sanity_should_fail']['exit']})")
    print()
    print(f"{'test':<52} {'result'}")
    print("-" * 64)
    all_pass = True
    for t, p in table:
        all_pass = all_pass and bool(p)
        print(f"{t:<52} {'PASS' if p else 'FAIL'}")
    print()

    print("H3 vs H4 compression (ratio = tokens_in / tokens_out; higher = more compression):")
    print(f"{'case':<24} {'mode_h4':>8} {'ratio_h3':>9} {'ratio_h4':>9} {'Δ% ':>7} {'regress':>8}")
    deltas = []
    for c in results["h3_vs_h4_compression"]:
        if not c.get("ok"):
            print(f"{c['case']:<24} ERROR {c.get('h4_err') or c.get('h3_err')}")
            continue
        d = c["ratio_delta_pct"]
        if d is not None:
            deltas.append(d)
        print(f"{c['case']:<24} {str(c['mode_h4']):>8} {str(c['ratio_h3']):>9} "
              f"{str(c['ratio_h4']):>9} {(f'{d:+.1f}' if d is not None else '—'):>7} "
              f"{str(len(c['protection_regression'])):>8}")
    if deltas:
        print(f"\nmean compression-ratio delta H4 vs H3: {sum(deltas)/len(deltas):+.2f}%")
    print()
    print("Prefix / cache-stability across appended turns (stable_ratio higher = better):")
    print(f"  H3: {stab['h3']}")
    print(f"  H4: {stab['h4']}")
    print(f"  H4 at least as good as H3: {stab.get('h4_at_least_as_good')}")
    print()
    print(f"wrote {res_path}")
    print("\nOVERALL:", "PASS" if all_pass else "FAIL")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
