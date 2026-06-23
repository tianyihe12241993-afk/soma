#!/usr/bin/env python3
"""Offline test harness for H3_cache_stable_depth_v1 (stdlib only; no network, no deps).

Builds synthetic + sample-shaped trajectories, runs h3_miner through the exact
compression-service subprocess protocol, and asserts the 10 structural checks the
candidate must satisfy. Prints a clear PASS/FAIL table and exits non-zero on any FAIL.

WHAT THIS MEASURES (offline, real): cache-prefix stability, pairing integrity, frozen-head
preservation, load-bearing-content survival, superseded-view elision, in-place body
masking, patch/diff preservation, profile bake + depth monotonicity, prune minimization,
and compression monotonicity with depth.

WHAT THIS CANNOT MEASURE offline: real platform pass/fail and the −4 penalty rate — those
need the SOMA SWE-bench eval (Docker+agent+OpenRouter). Structural safety is a strong
pass-safety proxy, not a guarantee.
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MINER = os.path.join(HERE, "h3_miner.py")

# Markers we assert survive (preservation = pass-safety proxy).
MARK_TASK = "SOMA-H3-TASK-INSTRUCTION-KEEPME"
MARK_TEST = "test_h3_protected_signal"
MARK_ASSERT = "AssertionError: h3 sentinel 42 != 7"
MARK_TRACE_FILE = "h3_module/core.py"
MARK_PATCH = "@@ -10,7 +10,9 @@"


# ---------------------------------------------------------------------------
# Stdlib helpers (mirror the miner's content extraction / token estimate).
# ---------------------------------------------------------------------------

def text_of(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return "\n".join(text_of(v) for v in value)
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            return value["text"]
        if isinstance(value.get("content"), str):
            return value["content"]
        return "\n".join(text_of(v) for v in value.values())
    return str(value)


def est_tokens(messages) -> int:
    chars = sum(len(text_of(m.get("content"))) for m in messages if isinstance(m, dict))
    return max(1, math.ceil(chars / 4)) if messages else 0


def tool_ids(messages):
    call_ids, result_ids = set(), set()
    for m in messages:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role", "")).lower().replace("_", "").replace("-", "")
        if role == "assistant":
            content = m.get("content")
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "toolCall" and b.get("id"):
                        call_ids.add(str(b["id"]).strip())
            for f in ("toolCalls", "tool_calls"):
                for tc in (m.get(f) or []):
                    if isinstance(tc, dict) and tc.get("id"):
                        call_ids.add(str(tc["id"]).strip())
        elif role == "toolresult":
            for f in ("toolCallId", "toolUseId", "id"):
                if isinstance(m.get(f), str) and m[f].strip():
                    result_ids.add(m[f].strip())
    return result_ids, call_ids


def call(messages, profile, *, token_count=None):
    with tempfile.TemporaryDirectory() as d:
        payload = {
            "pluginId": "soma-miner", "pluginName": "SOMA", "pluginDir": d,
            "params": {
                "messages": messages, "sessionId": "h3-eval", "sessionKey": None,
                "currentTokenCount": token_count if token_count is not None else est_tokens(messages),
            },
            "sourceHook": "assemble",
        }
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["H3_PROFILE"] = profile
        try:
            proc = subprocess.run(
                [sys.executable, MINER, "assemble"],
                input=json.dumps(payload, ensure_ascii=False),
                capture_output=True, text=True, encoding="utf-8", timeout=120, env=env,
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "timeout"}
        if proc.returncode != 0:
            return {"ok": False, "error": (proc.stderr or "")[-400:]}
        if not proc.stdout:
            return {"ok": False, "error": "empty stdout; stderr=" + (proc.stderr or "")[-200:]}
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError as e:
            return {"ok": False, "error": f"bad json: {e}; head={proc.stdout[:160]!r}"}


def out_of(r):
    """(messages, baseMiner) from a successful call, else (None, None)."""
    if not r.get("ok"):
        return None, None
    res = r["result"]
    return res["messages"], res.get("baseMiner", {})


# ---------------------------------------------------------------------------
# Trajectory builders (connector message shape).
# ---------------------------------------------------------------------------

def _asst(step_text, call_id, name, args):
    return {"role": "assistant", "content": [
        {"type": "text", "text": step_text},
        {"type": "toolCall", "id": call_id, "name": name, "arguments": args},
    ]}


def _result(call_id, body):
    return {"role": "toolResult", "toolCallId": call_id,
            "content": [{"type": "text", "text": body}]}


def synth_clean_harvest(rounds=24):
    """SHALLOW, LARGE, redundant, CLEAN/RESOLVING transcript → stays in HARVEST.
    Old reads of the same path are superseded by later reads; the final result is a
    PASS (no recent errors → no fragile-guard). Carries the task marker + a patch."""
    big_file = ("def escape(s):\n    return mark_safe(s)\n"
                "# helper in h3_module/core.py\n" * 60)
    msgs = [
        {"role": "system", "content": "You are an autonomous coding agent. Follow tool protocol."},
        {"role": "user", "content": [{"type": "text", "text":
            f"{MARK_TASK}: make escape() handle None in h3_module/core.py. "
            "The function currently raises on None input."}]},
    ]
    for k in range(1, rounds + 1):
        msgs.append(_asst(f"step {k}: inspect the file",
                          f"c{k}", "read_file", '{"path":"h3_module/core.py"}'))
        msgs.append(_result(f"c{k}", big_file + f"\n# revision marker {k}\n"))
    # an edit/patch interaction (load-bearing diff)
    msgs.append(_asst("apply the fix", "cpatch", "apply_patch",
                      '{"path":"h3_module/core.py"}'))
    msgs.append(_result("cpatch",
                        f"diff --git a/h3_module/core.py b/h3_module/core.py\n{MARK_PATCH}\n"
                        "-    return mark_safe(s)\n+    if s is None:\n+        return ''\n+    return mark_safe(s)\n"))
    # final clean test run (resolving → harvest stays)
    msgs.append(_asst("run the tests", "cok", "run_tests", '{"k":"core"}'))
    msgs.append(_result("cok",
                        f"Ran 1 test in 0.10s\nOK\nh3_module/test_core.py::{MARK_TEST} PASSED"))
    return msgs


def synth_superseded_views(rounds=12):
    """Reads path A several times, then reads it AGAIN at the very end (latest view).
    Earlier large views of A must be elided to a one-line ref; the LATEST kept."""
    view = ("class Widget:\n    def render(self):\n        return self.value\n"
            "# this is module h3_module/widget.py contents\n" * 50)
    latest = ("class Widget:\n    def render(self):\n        return str(self.value)\n"
              "# UPDATED module h3_module/widget.py LATEST contents kept high fidelity\n" * 50)
    msgs = [
        {"role": "system", "content": "You are a coding agent."},
        {"role": "user", "content": [{"type": "text", "text":
            f"{MARK_TASK}: refactor h3_module/widget.py render()."}]},
    ]
    for k in range(1, rounds + 1):
        msgs.append(_asst(f"read widget {k}", f"w{k}", "read_file",
                          '{"path":"h3_module/widget.py"}'))
        msgs.append(_result(f"w{k}", view + f"# round {k}\n"))
    # latest read of the SAME path, in the recent-intact tail
    msgs.append(_asst("re-read widget after edits", "wlast", "read_file",
                      '{"path":"h3_module/widget.py"}'))
    msgs.append(_result("wlast", latest))
    msgs.append(_asst("done", "wok", "run_tests", '{}'))
    msgs.append(_result("wok", "Ran 2 tests OK\nh3_module/test_widget.py::test_render PASSED"))
    return msgs


def synth_masked_bodies(rounds=18):
    """Large stale tool bodies (logs) early; CLEAN at the tail. Old bodies should be
    MASKED in place (message kept, tool_call_id kept, body shrunk + 'old output
    elided' marker) — never dropped. Each body reads a DIFFERENT path so they are not
    superseded views (forces the mask path, not the elide path)."""
    msgs = [
        {"role": "system", "content": "You are a coding agent."},
        {"role": "user", "content": [{"type": "text", "text":
            f"{MARK_TASK}: investigate the slow build in h3_module/."}]},
    ]
    for k in range(1, rounds + 1):
        body = (f"$ build module_{k}\n"
                + ("compiling object file with verbose diagnostic output line\n" * 120)
                + f"build of h3_module/sub_{k}.py finished, exit code 0\n")
        msgs.append(_asst(f"build {k}", f"b{k}", "run_shell",
                          f'{{"cmd":"build module_{k}"}}'))
        msgs.append(_result(f"b{k}", body))
    msgs.append(_asst("final status", "bok", "run_shell", '{"cmd":"status"}'))
    msgs.append(_result("bok", "All modules built. exit code 0\nh3_module/done.py OK"))
    return msgs


def synth_with_errors_protected(rounds=10):
    """Has error/test ground-truth EARLY (so it ages out of the tail) plus task marker.
    Forces token_count low so it can land in harvest for the protection checks; the
    error content (failing test, assertion, traceback) MUST survive even when masked.
    Each error body reads a different path so it is masked (not elided)."""
    msgs = [
        {"role": "system", "content": "You are a coding agent."},
        {"role": "user", "content": [{"type": "text", "text":
            f"{MARK_TASK}: fix {MARK_TRACE_FILE} so escape() handles None."}]},
    ]
    err_body = (
        f"$ pytest h3_module/test_core.py\n"
        + ("running collected test item with a lot of incidental progress noise\n" * 80)
        + f"FAILED h3_module/test_core.py::{MARK_TEST}\n{MARK_ASSERT}\n"
        + "Traceback (most recent call last):\n"
        + f'  File "{MARK_TRACE_FILE}", line 88, in escape\n    return mark_safe(s)\n'
    )
    for k in range(1, rounds + 1):
        msgs.append(_asst(f"run tests {k}", f"e{k}", "run_tests",
                          f'{{"target":"h3_module/path_{k}.py"}}'))
        msgs.append(_result(f"e{k}", err_body.replace("line 88", f"line {88 + k}")))
    # CLEAN recent tail so the fragile guard does NOT trip (we want harvest here)
    for k in range(1, 8):
        msgs.append(_asst(f"clean read {k}", f"r{k}", "read_file",
                          f'{{"path":"h3_module/clean_{k}.py"}}'))
        msgs.append(_result(f"r{k}", "def ok():\n    return True\n" * 40))
    msgs.append(_asst("final run", "ok", "run_tests", '{}'))
    msgs.append(_result("ok", "Ran 5 tests OK\nall passing"))
    return msgs


def synth_big_for_prune(rounds=40):
    """Very large CLEAN transcript that exceeds the hard cap even after masking, with
    DISTINCT paths each round (no superseding) and huge bodies → forces prune. Used to
    check prune>0 here but prune==0 on the small clean case, and depth-monotonicity."""
    msgs = [
        {"role": "system", "content": "You are a coding agent."},
        {"role": "user", "content": [{"type": "text", "text":
            f"{MARK_TASK}: large refactor across many files in h3_module/."}]},
    ]
    for k in range(1, rounds + 1):
        body = (f"$ cat h3_module/file_{k}.py\n"
                + (f"line of source code number with content {k} " * 40 + "\n") * 120)
        msgs.append(_asst(f"read file {k}", f"f{k}", "read_file",
                          f'{{"path":"h3_module/file_{k}.py"}}'))
        msgs.append(_result(f"f{k}", body))
    msgs.append(_asst("final", "fok", "run_tests", '{}'))
    msgs.append(_result("fok", "Ran 10 tests OK\nall green"))
    return msgs


def append_turn(messages):
    """Return messages + one appended (assistant tool_call, tool_result) turn,
    simulating the trajectory growing by one round (T -> T+1)."""
    nxt = max(
        [int(b["id"][1:]) for m in messages if isinstance(m, dict)
         for b in (m.get("content") or []) if isinstance(b, dict)
         and b.get("type") == "toolCall" and isinstance(b.get("id"), str)
         and b["id"][1:].isdigit()] + [0]
    ) + 1
    body = ("def newly_read():\n    return compute()\n"
            "# fresh module h3_module/newfile.py\n" * 40)
    return [
        *messages,
        _asst(f"new step {nxt}", f"z{nxt}", "read_file",
              '{"path":"h3_module/newfile.py"}'),
        _result(f"z{nxt}", body),
    ]


# ---------------------------------------------------------------------------
# Checks. Each returns (ok: bool, detail: str).
# ---------------------------------------------------------------------------

def check_1_profiles_monotonic():
    """Profile bake/selection works; output-token depth is monotonic ultra<=king<=safe.
    Uses a maskable-bodies trajectory that stays in harvest (token_count under the
    rich threshold) so depth is exercised via masking, not routing."""
    msgs = synth_masked_bodies(20)
    sizes = {}
    for prof in ("cache_safe", "cache_king", "cache_ultra"):
        r = call(msgs, prof)
        out, bm = out_of(r)
        if out is None:
            return False, f"{prof} call failed: {r.get('error')}"
        if bm.get("mode") != "harvest":
            return False, f"{prof} not in harvest (mode={bm.get('mode')})"
        sizes[prof] = est_tokens(out)
    mono = sizes["cache_ultra"] <= sizes["cache_king"] <= sizes["cache_safe"]
    return mono, f"tokens safe={sizes['cache_safe']} king={sizes['cache_king']} ultra={sizes['cache_ultra']}"


def check_2_pairing_integrity():
    """No orphan toolCall/toolResult introduced on every test trajectory + profile."""
    trajs = {
        "clean": synth_clean_harvest(24),
        "superseded": synth_superseded_views(12),
        "masked": synth_masked_bodies(18),
        "errors": synth_with_errors_protected(10),
        "big": synth_big_for_prune(40),
    }
    bad = []
    for name, msgs in trajs.items():
        in_res, in_call = tool_ids(msgs)
        for prof in ("cache_safe", "cache_king", "cache_ultra"):
            out, bm = out_of(call(msgs, prof, token_count=400_000 if name == "big" else None))
            if out is None:
                bad.append(f"{name}/{prof}:call_failed")
                continue
            out_res, out_call = tool_ids(out)
            if not (out_res - out_call <= in_res - in_call) or not (out_call - out_res <= in_call - in_res):
                bad.append(f"{name}/{prof}:orphan")
    return (not bad), ("ok all trajectories/profiles" if not bad else "; ".join(bad))


def check_3_first_user_byte_identical():
    """First user message preserved byte-identical in HARVEST output."""
    msgs = synth_clean_harvest(24)
    first_user = next(m for m in msgs if m.get("role") == "user")
    out, bm = out_of(call(msgs, "cache_safe"))
    if out is None or bm.get("mode") != "harvest":
        return False, f"call failed / not harvest (mode={bm.get('mode') if bm else None})"
    out_users = [m for m in out if isinstance(m, dict) and m.get("role") == "user"]
    # the coach message is also role=user and appended last; the FIRST user message
    # must be byte-identical to the input first user message.
    if not out_users:
        return False, "no user message in output"
    identical = json.dumps(out_users[0], sort_keys=True) == json.dumps(first_user, sort_keys=True)
    no_digest = "SOMA COMPRESSED HISTORY" not in text_of(out_users[0].get("content"))
    return (identical and no_digest), f"byte_identical={identical} no_injected_digest={no_digest}"


def check_4_loadbearing_survives():
    """Failing-test names, assertion lines, traceback tails present in input survive."""
    msgs = synth_with_errors_protected(10)
    out, bm = out_of(call(msgs, "cache_safe"))
    if out is None:
        return False, "call failed"
    if bm.get("mode") != "harvest":
        return False, f"expected harvest, got {bm.get('mode')} (fragile guard mis-fired)"
    ot = "\n".join(text_of(m.get("content")) for m in out if isinstance(m, dict))
    kept = {
        "failing_test": MARK_TEST in ot,
        "assertion": MARK_ASSERT in ot,
        "traceback_file": MARK_TRACE_FILE in ot,
    }
    return all(kept.values()), str(kept)


def check_5_superseded_elided_latest_kept():
    """Latest/active view kept; superseded earlier views of the same path elided to ref."""
    msgs = synth_superseded_views(12)
    out, bm = out_of(call(msgs, "cache_safe"))
    if out is None or bm.get("mode") != "harvest":
        return False, f"call failed / not harvest (mode={bm.get('mode') if bm else None})"
    ot = "\n".join(text_of(m.get("content")) for m in out if isinstance(m, dict))
    elided_ref = "old file view elided" in ot and "superseded by later read" in ot
    latest_kept = "UPDATED module" in ot and "LATEST contents kept high fidelity" in ot
    elided_count = bm.get("elidedFileViews", 0) >= 1
    return (elided_ref and latest_kept and elided_count), \
        f"elided_ref={elided_ref} latest_kept={latest_kept} elidedFileViews={bm.get('elidedFileViews')}"


def check_6_bodies_masked_in_place():
    """Old tool-result bodies masked in place: message kept, tool_call_id kept, body
    replaced (never dropped)."""
    msgs = synth_masked_bodies(18)
    in_res, in_call = tool_ids(msgs)
    out, bm = out_of(call(msgs, "cache_safe"))
    if out is None or bm.get("mode") != "harvest":
        return False, f"call failed / not harvest (mode={bm.get('mode') if bm else None})"
    out_res, _ = tool_ids(out)
    # every input toolResult id still present in output (no result dropped)
    ids_kept = in_res <= out_res
    masked = bm.get("maskedToolResults", 0) >= 1
    pruned = bm.get("pruneEvents", 0) == 0
    ot = "\n".join(text_of(m.get("content")) for m in out if isinstance(m, dict))
    marker_present = "old output elided" in ot
    return (ids_kept and masked and pruned and marker_present), \
        f"ids_kept={ids_kept} masked={bm.get('maskedToolResults')} prune={bm.get('pruneEvents')} marker={marker_present}"


def check_7_patch_preserved():
    """Patch/diff context preserved."""
    msgs = synth_clean_harvest(24)
    out, bm = out_of(call(msgs, "cache_king"))  # deeper profile, still must keep diff
    if out is None or bm.get("mode") != "harvest":
        return False, f"call failed / not harvest (mode={bm.get('mode') if bm else None})"
    ot = "\n".join(text_of(m.get("content")) for m in out if isinstance(m, dict))
    return (MARK_PATCH in ot and "diff --git" in ot), f"patch_hunk={MARK_PATCH in ot}"


def check_8_prefix_stability():
    """HEADLINE: across SUCCESSIVE append turns (T, T+1, T+2, T+3) the compressed
    HARVEST outputs share a long byte-identical PREFIX. The frozen head + the
    already-compressed old region must be byte-identical across turns — only the
    boundary message that just crossed the tail + the recent tail may differ. This
    is the cache win (vs H1M, whose per-turn digest rebuild mutates the first user
    message every turn → cache miss every turn)."""
    from_miner = _import_miner()
    if from_miner is None:
        return False, "could not import miner for prefix functions"
    canonical_json, prefix_boundary, compress_cache_stable, normalize_role = from_miner
    msgs = synth_masked_bodies(18)
    prev_out = prev_b = None
    boundaries = []
    for turn in range(4):
        out, _ = compress_cache_stable(msgs)
        b = prefix_boundary(out)
        boundaries.append(b)
        if prev_out is not None:
            # the stable region is everything before the PREVIOUS boundary: T's old
            # region is fully contained in T+1's old region (T+1 only appended).
            for i in range(prev_b):
                if i >= len(out) or canonical_json(prev_out[i]) != canonical_json(out[i]):
                    return False, f"prefix changed at msg {i} on turn {turn} (boundaries={boundaries})"
            if b < prev_b:  # boundary must advance (or hold), never retreat
                return False, f"boundary retreated {prev_b}->{b} on turn {turn}"
        prev_out, prev_b = out, b
        msgs = append_turn(msgs)
    return (boundaries[0] > 4), f"byte-stable prefix across 4 turns; boundaries={boundaries}"


def check_9_prune_minimized():
    """Prune events are 0 on trajectories under the hard cap; minimized otherwise.
    The hard cap is a true safety net at 60k output tokens; an input large enough to
    breach it post-mask would route to RICH. So we exercise the prune machinery
    directly (mode-independent pure function) with a LOW cap to confirm: (a) 0 prunes
    under cap, (b) >0 but MINIMIZED prunes over cap (drops only enough oldest
    interactions to get under), (c) pairing preserved through prune."""
    from_miner = _import_miner_full()
    if from_miner is None:
        return False, "could not import miner"
    m = from_miner
    # (a) under cap, normal call → 0 prunes
    small = synth_clean_harvest(24)
    out_s, bm_s = out_of(call(small, "cache_safe"))
    if out_s is None:
        return False, "small call failed"
    small_zero = bm_s.get("mode") == "harvest" and bm_s.get("pruneEvents", -1) == 0

    # (b)+(c) force prune via the pure function with a deliberately LOW hard cap.
    big = synth_masked_bodies(30)
    in_res, in_call = tool_ids(big)
    # cap small enough that masking alone is insufficient → prune must engage
    out_b, info_b = m.compress_cache_stable(big, hard_cap_tokens=2_000)
    out_res, out_call = tool_ids(out_b)
    pairing_ok = (out_res - out_call <= in_res - in_call) and (out_call - out_res <= in_call - in_res)
    pruned_some = info_b.get("pruneEvents", 0) > 0
    under_cap = est_tokens(out_b) <= 2_000 * 1.5  # minimized: stops near the cap, not 0
    # minimization: we did NOT drop everything droppable — output retains most msgs
    kept_ratio = len(out_b) / max(1, len(big))
    minimized = under_cap and kept_ratio > 0.3
    return (small_zero and pruned_some and pairing_ok and minimized), \
        (f"small_prune={bm_s.get('pruneEvents')} forced_prune={info_b.get('pruneEvents')} "
         f"pairing_ok={pairing_ok} out_tokens={est_tokens(out_b)} kept_ratio={kept_ratio:.2f}")


def check_10_compression_monotonic_depth():
    """Compression monotonic with depth (ultra<=king<=safe output tokens) on a large
    synthetic trajectory (separate from check 1: maskable bodies, not prune-bound)."""
    msgs = synth_masked_bodies(30)
    sizes = {}
    for prof in ("cache_safe", "cache_king", "cache_ultra"):
        out, bm = out_of(call(msgs, prof))
        if out is None or bm.get("mode") != "harvest":
            return False, f"{prof} call failed / not harvest"
        sizes[prof] = est_tokens(out)
    mono = sizes["cache_ultra"] <= sizes["cache_king"] <= sizes["cache_safe"]
    return mono, f"tokens safe={sizes['cache_safe']} king={sizes['cache_king']} ultra={sizes['cache_ultra']}"


# ---------------------------------------------------------------------------
# In-process import of the miner (for the prefix-stability check, which needs the
# pure functions directly). Done in a subprocess-free way by importing the module.
# ---------------------------------------------------------------------------

def _import_miner_full():
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("h3_miner_inproc", MINER)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception as e:
        print(f"  (import error: {e})", file=sys.stderr)
        return None


def _import_miner():
    mod = _import_miner_full()
    if mod is None:
        return None
    return (mod.canonical_json, mod.prefix_boundary, mod.compress_cache_stable,
            mod.normalize_role)


# ---------------------------------------------------------------------------
# Runner.
# ---------------------------------------------------------------------------

CHECKS = [
    ("1. profile bake + depth monotonic", check_1_profiles_monotonic),
    ("2. tool pairing integrity (all trajs)", check_2_pairing_integrity),
    ("3. first user msg byte-identical", check_3_first_user_byte_identical),
    ("4. failing-test/assert/traceback survive", check_4_loadbearing_survives),
    ("5. superseded views elided, latest kept", check_5_superseded_elided_latest_kept),
    ("6. tool bodies masked in place", check_6_bodies_masked_in_place),
    ("7. patch/diff preserved", check_7_patch_preserved),
    ("8. PREFIX STABILITY (headline)", check_8_prefix_stability),
    ("9. prune events minimized", check_9_prune_minimized),
    ("10. compression monotonic w/ depth", check_10_compression_monotonic_depth),
]


def main() -> int:
    print(f"H3 offline eval — miner: {MINER}")
    print(f"profiles: cache_safe (default), cache_king, cache_ultra\n")
    results = []
    for label, fn in CHECKS:
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, f"EXCEPTION: {e!r}"
        results.append((label, ok, detail))

    width = max(len(l) for l, _, _ in results)
    print(f"{'CHECK'.ljust(width)}  RESULT  DETAIL")
    print("-" * (width + 9 + 40))
    n_pass = 0
    for label, ok, detail in results:
        tag = "PASS" if ok else "FAIL"
        n_pass += int(ok)
        print(f"{label.ljust(width)}  {tag:>6}  {detail}")
    print("-" * (width + 9 + 40))
    print(f"\n{n_pass}/{len(results)} checks PASSED")
    print("\nNOTE: platform pass/fail and the -4 penalty rate are PENDING_EVAL "
          "(need SOMA SWE-bench: Docker+agent+OpenRouter). Structural safety here is a "
          "pass-safety proxy, not a guarantee.")
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
