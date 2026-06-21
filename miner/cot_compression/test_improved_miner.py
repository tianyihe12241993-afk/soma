#!/usr/bin/env python3
"""Harness: run the improved miner and the reference baseline through the exact
compression-service subprocess protocol on the SOMA sample trajectories.

Checks, per trajectory and per miner:
- protocol: ok=true, non-empty messages, changed/pruned flags
- safety:   task statement retained, every user message retained, newest tool
            result intact, no toolCall/toolResult orphans introduced
- savings:  output vs input estimated tokens (chars/4, the connector's metric)
- state:    incremental second call reuses session state

Usage: python3 test_improved_miner.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMPROVED = HERE / "improved_miner.py"
BASELINE = HERE / "reference_base_miner.py"
SAMPLES = HERE.parent / "plain_text_compression" / "sample_tasks" / "cot_compression_tasks.jsonl"

TAG = re.compile(
    r'<message role="(?P<role>user|assistant)">(?P<body>.*?)</message>'
    r'|<tool_result tool="(?P<tool>[^"]*)" tool_call_id="(?P<rid>[^"]*)">(?P<rbody>.*?)</tool_result>',
    re.DOTALL,
)
INNER = re.compile(
    r"<thinking>(?P<thinking>.*?)</thinking>"
    r'|<tool_call name="(?P<name>[^"]*)" id="(?P<cid>[^"]*)">(?P<args>.*?)</tool_call>'
    r"|<text>(?P<text>.*?)</text>",
    re.DOTALL,
)


def parse_transcript(source_text: str) -> list[dict]:
    messages: list[dict] = []
    for match in TAG.finditer(source_text):
        if match.group("role") == "user":
            inner = INNER.search(match.group("body"))
            text = inner.group("text") if inner and inner.group("text") else match.group("body")
            messages.append({"role": "user", "content": [{"type": "text", "text": text.strip()}]})
        elif match.group("role") == "assistant":
            blocks = []
            for inner in INNER.finditer(match.group("body")):
                if inner.group("thinking") is not None:
                    blocks.append({"type": "thinking", "text": inner.group("thinking").strip()})
                elif inner.group("cid") is not None:
                    blocks.append(
                        {
                            "type": "toolCall",
                            "id": inner.group("cid"),
                            "name": inner.group("name"),
                            "arguments": inner.group("args").strip(),
                        }
                    )
                elif inner.group("text") is not None:
                    blocks.append({"type": "text", "text": inner.group("text").strip()})
            if blocks:
                messages.append({"role": "assistant", "content": blocks})
        else:
            messages.append(
                {
                    "role": "toolResult",
                    "toolCallId": match.group("rid"),
                    "toolName": match.group("tool"),
                    "content": [{"type": "text", "text": match.group("rbody").strip()}],
                }
            )
    return messages


def synth_long_trajectory(base: list[dict], repeats: int = 12) -> list[dict]:
    """Inflate a real trajectory: repeat its tool interactions with unique ids
    (every 4th repeat keeps identical result text to exercise dedupe)."""
    out = [base[0]]
    middle = base[1:-2] if len(base) > 4 else base[1:]
    for repeat in range(repeats):
        for message in middle:
            clone = json.loads(json.dumps(message))
            if clone.get("role") == "assistant":
                for block in clone.get("content", []):
                    if isinstance(block, dict) and block.get("type") == "toolCall":
                        block["id"] = f"{block['id']}_r{repeat}"
            elif clone.get("role") == "toolResult":
                clone["toolCallId"] = f"{clone['toolCallId']}_r{repeat}"
                if repeat % 4 != 0:
                    for block in clone.get("content", []):
                        if isinstance(block, dict) and "text" in block:
                            block["text"] += f"\n[variant {repeat}]" + ("x" * 600)
            out.append(clone)
    out.extend(base[-2:] if len(base) > 4 else [])
    return out


def call_miner(miner: Path, plugin_dir: Path, messages: list[dict], session_id: str) -> tuple[dict, float]:
    payload = {
        "pluginId": "soma-miner",
        "pluginName": "SOMA Miner",
        "pluginDir": str(plugin_dir),
        "params": {
            "messages": messages,
            "sessionId": session_id,
            "sessionKey": None,
            "currentTokenCount": est_tokens(messages),
        },
        "sourceHook": "assemble",
    }
    start = time.monotonic()
    proc = subprocess.run(
        [sys.executable, str(miner), "assemble"],
        input=json.dumps(payload, ensure_ascii=False),
        capture_output=True,
        text=True,
        timeout=120,
    )
    elapsed = time.monotonic() - start
    if proc.returncode != 0:
        raise RuntimeError(f"{miner.name} exited {proc.returncode}: {proc.stderr[:400]}")
    return json.loads(proc.stdout), elapsed


def text_of(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(text_of(v) for v in value)
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            return value["text"]
        if isinstance(value.get("content"), str):
            return value["content"]
        return "\n".join(text_of(v) for v in value.values())
    return str(value)


def est_tokens(messages: list[dict]) -> int:
    return sum(len(text_of(m.get("content"))) for m in messages) // 4


def tool_ids(messages: list[dict]) -> tuple[set, set]:
    calls, results = set(), set()
    for m in messages:
        if m.get("role") == "assistant":
            for b in m.get("content", []) if isinstance(m.get("content"), list) else []:
                if isinstance(b, dict) and b.get("type") == "toolCall" and b.get("id"):
                    calls.add(b["id"])
            for f in ("toolCalls", "tool_calls"):
                for tc in m.get(f) or []:
                    if isinstance(tc, dict) and tc.get("id"):
                        calls.add(tc["id"])
        elif str(m.get("role", "")).lower().replace("_", "") == "toolresult":
            for f in ("toolCallId", "toolUseId", "id"):
                if isinstance(m.get(f), str):
                    results.add(m[f])
    return calls, results


def validate(name: str, inp: list[dict], resp: dict) -> list[str]:
    problems = []
    if not resp.get("ok"):
        return [f"ok=false: {resp.get('error')}"]
    out = resp["result"]["messages"]
    if not out:
        return ["empty output messages"]
    out_text = "\n".join(text_of(m.get("content")) for m in out)

    task_snip = text_of(inp[0].get("content"))[:80]
    if task_snip and task_snip not in out_text:
        problems.append("task statement lost")
    for m in inp:
        if m.get("role") == "user":
            snip = text_of(m.get("content"))[:60]
            if snip and snip not in out_text:
                problems.append("a user message was dropped")
                break
    last_result = next((m for m in reversed(inp) if str(m.get("role", "")).lower().startswith("tool")), None)
    if last_result:
        snip = text_of(last_result.get("content"))[:120]
        if snip and snip not in out_text:
            problems.append("newest tool result lost/modified")

    in_calls, in_results = tool_ids(inp)
    out_calls, out_results = tool_ids(out)
    if not (out_results - out_calls) <= (in_results - in_calls):
        problems.append("introduced orphan toolResult")
    if not (out_calls - out_results) <= (in_calls - in_results):
        problems.append("introduced orphan toolCall")
    return problems


def run_case(label: str, messages: list[dict]) -> None:
    in_tok = est_tokens(messages)
    print(f"\n=== {label}: {len(messages)} msgs, ~{in_tok} tokens ===")
    for miner in (IMPROVED, BASELINE):
        with tempfile.TemporaryDirectory() as tmp:
            resp, elapsed = call_miner(miner, Path(tmp), messages, f"sess-{label}")
            if not resp.get("ok"):
                print(f"  {miner.stem:<16} ERROR: {resp.get('error')}")
                continue
            out = resp["result"]["messages"]
            out_tok = est_tokens(out)
            meta = resp["result"].get("baseMiner", {})
            problems = validate(label, messages, resp)
            savings = 100 * (1 - out_tok / in_tok) if in_tok else 0
            print(
                f"  {miner.stem:<16} {len(out):>3} msgs  ~{out_tok:>6} tok  "
                f"savings {savings:5.1f}%  changed={meta.get('changed')} "
                f"pruned={meta.get('pruned')} reason={meta.get('reason')}  {elapsed*1000:.0f}ms"
            )
            print(f"  {'':<16} issues: {problems or 'none'}")


def run_incremental(messages: list[dict]) -> None:
    print("\n=== incremental state (improved miner, 2 calls, same session) ===")
    with tempfile.TemporaryDirectory() as tmp:
        cut = int(len(messages) * 0.7)
        first, _ = call_miner(IMPROVED, Path(tmp), messages[:cut], "sess-incr")
        second, _ = call_miner(IMPROVED, Path(tmp), messages, "sess-incr")
        m1 = first["result"]["baseMiner"]
        m2 = second["result"]["baseMiner"]
        print(f"  call1: loaded={m1.get('stateLoaded')} saved={m1.get('stateSaved')} out={m1.get('messageCount')}")
        print(
            f"  call2: loaded={m2.get('stateLoaded')} matched={m2.get('stateMatchedPrefix')} "
            f"new={m2.get('newMessageCount')} out={m2.get('messageCount')}"
        )
        assert m2.get("stateLoaded") is True, "state was not reused on second call"
        print("  state reuse OK")


def run_cache_stability(base: list[dict]) -> None:
    """Simulate a realistic run: the trajectory grows by one interaction per
    assemble call. Track the compressed prefix across calls. On a call that
    triggers no new prune, the prefix the connector sends the provider must be
    byte-identical to the previous call (prompt-cache hit). This is the
    property that makes compression cheap rather than cache-thrashing."""
    print("\n=== cache/prefix stability (improved miner, incremental growth) ===")
    # One synthetic interaction (~500 tokens) appended per call.
    def grow(n: int) -> list[dict]:
        msgs = list(base)
        for i in range(n):
            msgs.append({"role": "assistant", "content": [
                {"type": "text", "text": f"Step {i}: inspecting another module."},
                {"type": "toolCall", "id": f"call_g{i}", "name": "exec",
                 "arguments": json.dumps({"command": f"sed -n '1,40p' mod_{i}.py"})}]})
            msgs.append({"role": "toolResult", "toolCallId": f"call_g{i}",
                         "content": [{"type": "text", "text": f"# mod_{i}.py\n" + ("line of code\n" * 120)}]})
        return msgs

    with tempfile.TemporaryDirectory() as tmp:
        plugin_dir = Path(tmp)
        prev_out, prune_calls, append_calls, stable_appends = None, 0, 0, 0
        for n in range(0, 22):
            resp, _ = call_miner(IMPROVED, plugin_dir, grow(n), "sess-cache")
            out = resp["result"]["messages"]
            meta = resp["result"]["baseMiner"]
            pruned = bool(meta.get("pruned"))
            if prev_out is not None:
                # longest common byte-identical prefix vs previous call
                stable = 0
                for a, b in zip(prev_out, out):
                    if json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True):
                        stable += 1
                    else:
                        break
                if pruned:
                    prune_calls += 1
                else:
                    append_calls += 1
                    # No prune → prev compressed prefix must survive intact.
                    # Allow tail churn: in gentle mode one result ages out of
                    # the protected window (last KEEP_RECENT_FULL interactions
                    # ≈ 12 messages) per new interaction.
                    need = max(0, len(prev_out) - 14)
                    ok = stable >= need
                    stable_appends += int(ok)
                    flag = "OK" if ok else "BROKEN"
                    print(f"  n={n:>2} out={len(out):>3} mode={meta.get('mode')} stable_prefix={stable}/{len(prev_out)} [{flag}]")
                    assert ok, f"prefix not stable on append round n={n}: {stable}<{need}"
            prev_out = out
        print(f"  prune calls={prune_calls}, append calls={append_calls}, all appends cache-stable={append_calls==stable_appends}")
        assert append_calls > 0, "test never exercised an append-only round"
        print("  incremental cache stability OK")


def run_gentle_mode(messages: list[dict]) -> None:
    """Harvest mode (3k-25k): truncation-only. No message may be dropped,
    user/assistant content byte-identical, error-bearing results keep bigger
    budgets than plain ones. The two bulky results sit early so newer
    interactions push them out of the recent-keep window (only then truncated)."""
    print("\n=== gentle/harvest mode (mid-size trajectory) ===")
    def interaction(cid, text):
        return [
            {"role": "assistant", "content": [
                {"type": "toolCall", "id": cid, "name": "exec", "arguments": "{}"}]},
            {"role": "toolResult", "toolCallId": cid, "content": [{"type": "text", "text": text}]},
        ]
    big_plain = "x = compute()\n" * 1500
    big_error = "Traceback (most recent call last):\n  AssertionError: boom\n" + ("ctx line\n" * 1500)
    msgs = [{"role": "user", "content": [{"type": "text", "text": "Fix the bug in module foo."}]}]
    msgs += interaction("call_g_p", big_plain)
    msgs += interaction("call_g_e", big_error)
    for i in range(6):  # newer interactions age the big ones out of the recent window
        msgs += interaction(f"call_s{i}", f"small result {i}\n" * 5)
    with tempfile.TemporaryDirectory() as tmp:
        resp, _ = call_miner(IMPROVED, Path(tmp), msgs, "sess-gentle")
    meta = resp["result"]["baseMiner"]
    out = resp["result"]["messages"]
    assert meta.get("mode") in ("harvest", "steady"), f"expected harvest/steady, got {meta.get('mode')}"
    assert len(out) == len(msgs), f"truncation mode dropped messages: {len(msgs)} -> {len(out)}"
    in_assist = [text_of(m.get("content")) for m in msgs if m.get("role") == "assistant"]
    out_assist = [text_of(m.get("content")) for m in out if m.get("role") == "assistant"]
    assert in_assist == out_assist, "gentle mode modified assistant content"
    def result_len(ms, cid):
        return next(len(text_of(m.get("content"))) for m in ms
                    if m.get("role") == "toolResult" and m.get("toolCallId") == cid)
    plain_out, err_out = result_len(out, "call_g_p"), result_len(out, "call_g_e")
    assert plain_out < len(big_plain), "plain bulky result was not truncated"
    assert err_out > plain_out, f"error result ({err_out}) not protected vs plain ({plain_out})"
    savings = 1 - est_tokens(out) / est_tokens(msgs)
    print(f"  mode=gentle msgs {len(msgs)}=={len(out)}, assistant untouched, "
          f"plain {len(big_plain)}->{plain_out}, error {len(big_error)}->{err_out}, savings {savings:.0%}")
    print("  gentle mode OK")


def run_mode_escalation(base: list[dict]) -> None:
    """Modes must escalate passthrough -> harvest -> steady -> tight, never revert."""
    print("\n=== mode escalation ===")
    # Tiny seed (~0.5k tokens) so n=0 is below the 3k pass-through floor.
    seed = [{"role": "user", "content": [{"type": "text", "text": "Fix the bug. " * 150}]}]
    filler = "line of code here\n" * 220  # ~1.2k tokens per interaction
    def grown(n):
        msgs = list(seed)
        for i in range(n):
            msgs.append({"role": "assistant", "content": [
                {"type": "toolCall", "id": f"call_m{i}", "name": "exec", "arguments": "{}"}]})
            msgs.append({"role": "toolResult", "toolCallId": f"call_m{i}",
                         "content": [{"type": "text", "text": filler}]})
        return msgs
    with tempfile.TemporaryDirectory() as tmp:
        seen = []
        for n in (0, 8, 16, 30, 34, 36):
            resp, _ = call_miner(IMPROVED, Path(tmp), grown(n), "sess-mode")
            seen.append(resp["result"]["baseMiner"].get("mode"))
        print("  modes:", " -> ".join(seen))
        order = {"passthrough": 0, "harvest": 1, "steady": 2, "tight": 3}
        ranks = [order[m] for m in seen]
        assert ranks == sorted(ranks), "mode reverted"
        assert seen[0] == "passthrough" and seen[-1] == "tight", seen
        assert ("harvest" in seen or "steady" in seen), f"never hit a truncation band: {seen}"
        print("  escalation OK (monotonic; passthrough -> harvest/steady -> tight)")


def run_coach(base: list[dict]) -> None:
    """Tight mode appends exactly one coach message (always last, never
    duplicated), with dynamic failing-test status and the governor line on
    long sessions; gentle/passthrough never inject it."""
    print("\n=== coach injection (tight mode, dynamic) ===")
    big = synth_long_trajectory(base, repeats=30)  # >150k tokens → tight + governor
    test_fail = {
        "role": "toolResult", "toolCallId": "call_tst",
        "content": [{"type": "text", "text":
            "============ FAILED tests/utils_tests/test_html.py::test_urlize_trailing - "
            "AssertionError: 'lt!' != '!'\n1 failed, 12 passed in 4.2s"}],
    }
    test_call = {"role": "assistant", "content": [
        {"type": "toolCall", "id": "call_tst", "name": "exec", "arguments": '{"command":"pytest"}'}]}
    big_with_tests = big[:-1] + [test_call, test_fail, big[-1]]
    with tempfile.TemporaryDirectory() as tmp:
        r1, _ = call_miner(IMPROVED, Path(tmp), big_with_tests, "sess-coach")
        out1 = r1["result"]["messages"]
        extra = [{"role": "assistant", "content": [{"type": "text", "text": "Continuing."}]}]
        r2, _ = call_miner(IMPROVED, Path(tmp), big_with_tests + extra, "sess-coach")
        out2 = r2["result"]["messages"]
    MARKER = "[SOMA CONTEXT NOTE]"
    def coach_count(ms):
        return sum(1 for m in ms if MARKER in text_of(m.get("content")))
    for tag, out in (("r1", out1), ("r2", out2)):
        assert coach_count(out) == 1, f"{tag}: coach count {coach_count(out)} != 1"
        coach = text_of(out[-1].get("content"))
        assert MARKER in coach, f"{tag}: coach not last"
        assert "test_urlize_trailing" in coach, f"{tag}: dynamic test status missing"
        assert "STOP NOW" in coach, f"{tag}: governor stop line missing on 200k session"
        # compliance: no generic behavioral directives
        assert "edit the real" not in coach.lower(), f"{tag}: disallowed directive present"
        assert "delete" not in coach.lower(), f"{tag}: disallowed directive present"
    # v5.1: issue re-injection — the coach must restate the task text
    issue_snip = text_of(base[0].get("content"))[:60]
    coach1 = text_of(out1[-1].get("content"))
    assert issue_snip in coach1, "issue text not re-injected into coach"
    assert "[SOMA COMPRESSED HISTORY" not in coach1, "digest leaked into coach"
    # v5.1: loop breaker — 3 identical call+result pairs trigger the note,
    # healthy repeats (same cmd, different results) do not
    def looped(msgs):
        with tempfile.TemporaryDirectory() as tmp:
            r, _ = call_miner(IMPROVED, Path(tmp), msgs, "sess-loop")
        return "Loop detected" in text_of(r["result"]["messages"][-1].get("content"))
    def rep(i, result_text):
        return [
            {"role": "assistant", "content": [
                {"type": "toolCall", "id": f"call_rep{i}", "name": "exec",
                 "arguments": '{"command":"pytest tests/x.py"}'}]},
            {"role": "toolResult", "toolCallId": f"call_rep{i}",
             "content": [{"type": "text", "text": result_text}]},
        ]
    stuck = big[:-1]
    for i in range(3):
        stuck += rep(i, "1 failed: AssertionError boom")
    stuck += [big[-1]]
    healthy = big[:-1]
    for i in range(3):
        healthy += rep(i, f"1 failed: AssertionError boom (variant {i})")
    healthy += [big[-1]]
    assert looped(stuck), "loop breaker did not fire on identical repeats"
    assert not looped(healthy), "loop breaker false-positive on healthy edit-test loop"
    # gentle/passthrough must not inject
    with tempfile.TemporaryDirectory() as tmp:
        r3, _ = call_miner(IMPROVED, Path(tmp), base, "sess-nocoach")
    assert coach_count(r3["result"]["messages"]) == 0, "coach leaked outside tight mode"
    print("  tight: compliant coach (summary + stop-condition + loop detect + governor), no directives; loop fires/abstains correctly; others: none")
    print("  coach OK")


def run_robustness() -> None:
    print("\n=== robustness ===")
    for label, stdin in (
        ("empty object", "{}"),
        ("garbage", "{not json"),
        ("null messages", json.dumps({"params": {"messages": None}})),
    ):
        proc = subprocess.run(
            [sys.executable, str(IMPROVED), "assemble"],
            input=stdin, capture_output=True, text=True, timeout=60,
        )
        try:
            resp = json.loads(proc.stdout)
            print(f"  {label:<14} exit={proc.returncode} ok={resp.get('ok')} (valid JSON out)")
        except json.JSONDecodeError:
            print(f"  {label:<14} INVALID JSON OUTPUT: {proc.stdout[:120]}")


def main() -> None:
    tasks = [json.loads(line) for line in SAMPLES.read_text().splitlines() if line.strip()]
    parsed = [parse_transcript(t["source_text"]) for t in tasks]
    for i, messages in enumerate(parsed, 1):
        run_case(f"sample-{i}", messages)
    long_traj = synth_long_trajectory(max(parsed, key=est_tokens))
    run_case("synthetic-long", long_traj)
    run_incremental(long_traj)
    run_cache_stability(parsed[0])
    run_gentle_mode(parsed[3])
    run_mode_escalation(parsed[0])
    run_coach(parsed[0])
    run_robustness()


if __name__ == "__main__":
    main()
