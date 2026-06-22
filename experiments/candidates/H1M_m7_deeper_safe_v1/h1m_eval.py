#!/usr/bin/env python3
"""Offline evaluation: H1M_m7_deeper_safe_v1 vs m7/v11.1.

WHAT THIS MEASURES (offline, real): compression RATIO and STRUCTURAL SAFETY of each
profile vs m7, by running both miners through the exact compression-service subprocess
protocol on (a) the SOMA sample transcripts and (b) synthetic shallow-large redundant
trajectories that exercise the HARVEST regime (where Medium/Easy pass-stable tasks live).

WHAT THIS CANNOT MEASURE offline: real platform pass/fail, negative-run rate, broke-
baseline — those require the SOMA SWE-bench eval (Docker+agent+OpenRouter). They are
reported as PENDING_EVAL, never invented. Structural-safety (protected content survives)
is a strong pass-safety proxy, not a guarantee.

Outputs: ../../../data/latest/h1m_candidate_results.json and a console summary.
"""
from __future__ import annotations
import json, math, os, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent                       # repo root
MINER_DIR = ROOT / "miner" / "cot_compression"
sys.path.insert(0, str(MINER_DIR))
from test_improved_miner import parse_transcript, est_tokens, text_of, tool_ids  # noqa: E402

M7 = MINER_DIR / "upload_miner_v11_m7.py"
H1M = HERE / "h1m_miner.py"
SAMPLES = ROOT / "miner" / "plain_text_compression" / "sample_tasks" / "cot_compression_tasks.jsonl"

# protected markers we will assert survive compression (preservation = pass-safety proxy)
MARK_TASK = "SOMA-H1M-TASK-INSTRUCTION-KEEPME"
MARK_TEST = "test_h1m_protected_signal"
MARK_ASSERT = "AssertionError: h1m sentinel 42 != 7"
MARK_TRACE = "h1m_module/core.py"


def synth_shallow_large(rounds: int = 34) -> list[dict]:
    """A SHALLOW (<90 msgs) but LARGE, highly-redundant agent transcript in the tagged
    format → parse_transcript → valid connector messages. Exercises harvest + dedup,
    and embeds protected markers (task instruction, failing test, assertion, traceback,
    file paths) both early and in the most-recent round."""
    big_log = ("Traceback (most recent call last):\n"
               "  File \"django/db/models/query.py\", line 1234, in execute\n"
               "    raise ValueError(x)\n" * 30)
    file_read = ("def handle(self, *args, **opts):\n    return process(opts)\n"
                 "# module: django/core/management/base.py\n" * 25)
    parts = [f'<message role="user"><text>{MARK_TASK}: fix the failing test in '
             f'django/utils/html.py so escape() handles None. Problem: escape(None) raises.'
             f'</text></message>']
    for k in range(1, rounds + 1):
        # repeated/near-duplicate tool outputs (same read, traces differing only by line no.)
        body = file_read if k % 2 else big_log.replace("1234", str(1200 + k))
        parts.append(f'<message role="assistant"><thinking>step {k}: inspect and edit'
                     f'</thinking><tool_call name="read_file" id="c{k}">'
                     f'{{"path":"django/utils/html.py"}}</tool_call></message>')
        parts.append(f'<tool_result tool="read_file" tool_call_id="c{k}">{body}</tool_result>')
    # most-recent round carries the live ground truth that MUST survive intact
    parts.append('<message role="assistant"><thinking>run the tests</thinking>'
                 '<tool_call name="run_tests" id="cfinal">{"k":"html"}</tool_call></message>')
    parts.append(f'<tool_result tool="run_tests" tool_call_id="cfinal">'
                 f'FAILED utils/test_html.py::{MARK_TEST}\n{MARK_ASSERT}\n'
                 f'Traceback (most recent call last):\n  File "{MARK_TRACE}", line 88, in escape\n'
                 f'    return mark_safe(s)\n</tool_result>')
    return parse_transcript("\n".join(parts))


def synth_clean_large(rounds: int = 34) -> list[dict]:
    """SHALLOW, LARGE, redundant but CLEAN/RESOLVING transcript (no error markers in the
    recent window) → stays in HARVEST for both m7 and H1M, so we measure harvest deepening
    apples-to-apples. Embeds protected markers (task instruction, file path, test name)."""
    file_read = ("def handle(self, *args, **opts):\n    return process(opts)\n"
                 "# module: django/core/management/base.py helper\n" * 26)
    docs = ("The escape function converts characters to safe sequences. "
            "See django/utils/html.py for the implementation details and notes. " * 30)
    parts = [f'<message role="user"><text>{MARK_TASK}: make escape() handle None in '
             f'django/utils/html.py.</text></message>']
    for k in range(1, rounds + 1):
        body = file_read if k % 2 else docs
        parts.append(f'<message role="assistant"><thinking>step {k} review</thinking>'
                     f'<tool_call name="read_file" id="c{k}">{{"path":"django/utils/html.py"}}'
                     f'</tool_call></message>')
        parts.append(f'<tool_result tool="read_file" tool_call_id="c{k}">{body}</tool_result>')
    parts.append('<message role="assistant"><thinking>run tests</thinking>'
                 '<tool_call name="run_tests" id="cok">{"k":"html"}</tool_call></message>')
    parts.append(f'<tool_result tool="run_tests" tool_call_id="cok">Ran 1 test in 0.2s OK\n'
                 f'utils/test_html.py::{MARK_TEST} PASSED\nfile: {MARK_TRACE}</tool_result>')
    return parse_transcript("\n".join(parts))


def call(miner: Path, messages: list[dict], env_profile: str | None) -> dict:
    with tempfile.TemporaryDirectory() as d:
        payload = {"pluginId": "soma-miner", "pluginName": "SOMA", "pluginDir": d,
                   "params": {"messages": messages, "sessionId": "h1m-eval",
                              "sessionKey": None, "currentTokenCount": est_tokens(messages)},
                   "sourceHook": "assemble"}
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        if env_profile:
            env["H1M_PROFILE"] = env_profile
        try:
            proc = subprocess.run([sys.executable, str(miner), "assemble"],
                                  input=json.dumps(payload, ensure_ascii=False),
                                  capture_output=True, text=True, encoding="utf-8",
                                  timeout=120, env=env)
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "timeout"}
        if proc.returncode != 0:
            return {"ok": False, "error": (proc.stderr or "")[-300:]}
        if not proc.stdout:
            return {"ok": False, "error": "empty stdout; stderr=" + (proc.stderr or "")[-200:]}
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError as e:
            return {"ok": False, "error": f"bad json: {e}; head={proc.stdout[:120]!r}"}


def safety(inp: list[dict], out_msgs: list[dict]) -> dict:
    in_text = "\n".join(text_of(m.get("content")) for m in inp if isinstance(m, dict))
    out_text = "\n".join(text_of(m.get("content")) for m in out_msgs if isinstance(m, dict))
    in_users = [text_of(m.get("content")) for m in inp if isinstance(m, dict) and str(m.get("role", "")).lower() == "user"]
    users_kept = all(u[:60] in out_text for u in in_users if u.strip())
    in_res, in_call = tool_ids(inp)
    out_res, out_call = tool_ids(out_msgs)
    orphans_ok = out_res <= in_res and out_call <= in_call
    # only require preservation for markers that were actually IN the input
    protected = {m: (m in out_text) for m in (MARK_TASK, MARK_TEST, MARK_ASSERT, MARK_TRACE) if m in in_text}
    return {"users_kept": users_kept, "orphans_ok": orphans_ok,
            "protected": protected, "all_protected": all(protected.values()) if protected else None}


def run_variant(label, miner, env_profile, cases):
    rows = []
    for name, msgs in cases:
        tin = est_tokens(msgs)
        r = call(miner, msgs, env_profile)
        if not r.get("ok"):
            rows.append({"case": name, "ok": False, "error": r.get("error")}); continue
        res = r["result"]
        out = res["messages"]
        tout = est_tokens(out)
        meta = res.get("baseMiner", {})
        s = safety(msgs, out) if name.startswith("synth") else {"all_protected": None, "orphans_ok": None, "users_kept": None}
        rows.append({"case": name, "ok": True, "tokens_in": tin, "tokens_out": tout,
                     "ratio": round(tin / tout, 3) if tout else None, "mode": meta.get("mode"),
                     "changed": res.get("baseMiner", {}).get("changed"),
                     "all_protected": s["all_protected"], "orphans_ok": s["orphans_ok"],
                     "users_kept": s["users_kept"]})
    return {"label": label, "cases": rows}


def main() -> int:
    samples = [parse_transcript(json.loads(l)["source_text"])
               for l in SAMPLES.read_text(encoding="utf-8").splitlines() if l.strip()]
    cases = [(f"sample-{i}", m) for i, m in enumerate(samples, 1)]
    cases += [("synth-clean-large", synth_clean_large(34)),       # safe harvest regime
              ("synth-clean-big", synth_clean_large(42)),         # safe harvest regime, larger
              ("synth-errdense-fragile", synth_shallow_large())]  # fragile signature (guard test)

    variants = [("m7/v11.1", M7, None),
                ("h1m@m7", H1M, "m7"),
                ("h1m@light", H1M, "light"),
                ("h1m@medium", H1M, "medium"),
                ("h1m@deep", H1M, "deep")]
    out = {"computed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "note": "RATIO + STRUCTURAL SAFETY measured offline on sample+synthetic transcripts. "
                   "Platform pass/neg-run/broke = PENDING_EVAL (needs SOMA SWE-bench). Score lift = "
                   "estimate via 1+0.5ln(ratio).",
           "variants": [run_variant(*v, cases) for v in variants]}

    # score harvest-vs-harvest ONLY (apples-to-apples deepening); track guard separately
    m7c = {c["case"]: c for c in next(v for v in out["variants"] if v["label"] == "m7/v11.1")["cases"]}
    summ = {}
    for v in out["variants"]:
        cc = {c["case"]: c for c in v["cases"]}
        deep = [k for k, a in m7c.items()
                if a.get("mode") == "harvest" and (a.get("ratio") or 0) > 1.05
                and cc.get(k, {}).get("mode") == "harvest" and cc[k].get("ratio")]
        # magnitude-independent per-case metrics (avoid big-synth dominating a mean)
        per_lift = [0.5 * math.log(cc[k]["ratio"] / m7c[k]["ratio"]) for k in deep]
        per_pct = [cc[k]["ratio"] / m7c[k]["ratio"] - 1 for k in deep]
        improved = [k for k in deep if cc[k]["ratio"] > m7c[k]["ratio"] * 1.005]
        regressed = [k for k in deep if cc[k]["ratio"] < m7c[k]["ratio"] * 0.995]
        guard = [k for k, a in m7c.items()
                 if a.get("mode") == "harvest" and cc.get(k, {}).get("mode") == "rich"]
        prot = [cc[k]["all_protected"] for k in cc if cc[k].get("all_protected") is not None]
        orph = [cc[k]["orphans_ok"] for k in cc if cc[k].get("orphans_ok") is not None]
        summ[v["label"]] = {
            "n_harvest_cases": len(deep), "harvest_cases": deep,
            "mean_pct_vs_m7": round(sum(per_pct) / len(per_pct), 3) if per_pct else None,
            "mean_est_lift_vs_m7": round(sum(per_lift) / len(per_lift), 3) if per_lift else None,
            "improved": improved, "regressed": regressed,
            "fragile_guard_fired_on": guard,
            "all_protected": all(prot) if prot else None, "orphans_ok": all(orph) if orph else None,
            "ok_cases": sum(1 for c in v["cases"] if c.get("ok")), "n_cases": len(v["cases"])}
    out["summary"] = summ

    res_path = ROOT / "data" / "latest" / "h1m_candidate_results.json"
    res_path.parent.mkdir(parents=True, exist_ok=True)
    res_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"harvest-deepening cases (both in harvest): {summ['h1m@deep']['harvest_cases']}")
    print(f"{'variant':>12} {'meanPct':>8} {'~liftVsM7':>9} {'improved':>8} {'regress':>7} "
          f"{'protected':>9} {'orphans':>8} {'guard':>5}")
    for lab in ["m7/v11.1", "h1m@m7", "h1m@light", "h1m@medium", "h1m@deep"]:
        s = summ[lab]
        pct = f"{s['mean_pct_vs_m7']*100:+.1f}%" if s['mean_pct_vs_m7'] is not None else "—"
        print(f"{lab:>12} {pct:>8} {str(s.get('mean_est_lift_vs_m7')):>9} {len(s['improved']):>8} "
              f"{len(s['regressed']):>7} {str(s['all_protected']):>9} {str(s['orphans_ok']):>8} "
              f"{len(s['fragile_guard_fired_on']):>5}")
    print(f"\nwrote {res_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
