#!/usr/bin/env python3
"""Collect ALL detailed scores INCLUDING per-run, keyless, from the SOMA dashboard.

This is the CORRECT detailed collector. The dashboard's per-run rows (#1..#5: tokens /
time / steps / score / pass) are served by a Next.js Server Action
`getSweTaskRunsAction` which we replay over plain HTTP — no API key, no login. The
action-id is a per-build hash auto-discovered from the page JS bundle.
(Mechanism vendored from E:/extension-sb114/soma_scraper.py — proven 2026-06-16.)

Layers captured:
  leaderboard (sweMiners)  ->  per-miner sweSummary/swePenalties/sweTasks  ->  per-RUN
  per run: attempt_no, run_id, pass_with_compression, tokens_with_compression,
           platform_score, time_taken_seconds, agent_steps

Writes an IMMUTABLE raw snapshot (import-compatible: miners[].tasks[].runs[]):
  data/raw/platform_results/YYYY-MM-DD/HHMMSS_swe_runs.json

Targets (default = ours + top miners):  --all | --hotkey HK [..] | --limit N
Stdlib only. Politeness: global MIN_INTERVAL throttle + 429 backoff.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import threading
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import RAW, utc_now, utc_stamp, hotkey_to_name, load_top_miners  # noqa: E402

BASE = "https://thesoma.ai"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
PLATFORM_RESULTS = RAW.parent / "platform_results"
HK_RX = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{48}$')

_throttle_lock = threading.Lock()
_last = [0.0]
MIN_INTERVAL = 0.15


def _throttle():
    with _throttle_lock:
        wait = MIN_INTERVAL - (time.monotonic() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.monotonic()


def _req(url, *, data=None, headers=None, timeout=40, retries=5):
    h = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        h.update(headers)
    method = "POST" if data is not None else "GET"
    last = None
    for attempt in range(retries):
        _throttle()
        try:
            req = urllib.request.Request(url, data=data, headers=h, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 503):
                ra = e.headers.get("Retry-After")
                time.sleep((float(ra) if (ra and ra.isdigit()) else min(30, 2 ** attempt)) + 0.5)
                continue
            if 500 <= e.code < 600:
                time.sleep(1.5 * (attempt + 1)); continue
            raise RuntimeError(f"HTTP {e.code} for {url}")
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"request failed after {retries}: {url} :: {last}")


def extract_flight(html: str) -> str:
    out, dec, needle, i = [], json.JSONDecoder(), "self.__next_f.push([", 0
    while True:
        j = html.find(needle, i)
        if j < 0:
            break
        k = html.find(",", j + len(needle))
        q = html.find('"', k) if k >= 0 else -1
        if q < 0:
            break
        try:
            s, _ = dec.raw_decode(html[q:])
            if isinstance(s, str):
                out.append(s)
        except json.JSONDecodeError:
            pass
        i = j + len(needle)
    return "".join(out)


def balanced(text: str, key: str):
    m = re.search(r'"' + re.escape(key) + r'"\s*:\s*([\[{])', text)
    if not m:
        return None
    start = m.end() - 1
    open_ch = text[start]
    close_ch = "]" if open_ch == "[" else "}"
    depth = in_str = esc = 0
    for p in range(start, len(text)):
        c = text[p]
        if in_str:
            if esc: esc = 0
            elif c == "\\": esc = 1
            elif c == '"': in_str = 0
        elif c == '"': in_str = 1
        elif c == open_ch: depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:p + 1])
                except json.JSONDecodeError:
                    return None
    return None


def discover_action_id(comp_id, sample_hk):
    html = _req(f"{BASE}/dashboard/miner/{comp_id}/{sample_hk}")
    chunks = sorted(set(re.findall(r'/_next/static/chunks/[^"\\\s]+\.js', html)),
                    key=lambda c: (0 if "miner" in c else 1, c))
    pat = re.compile(r'\("([0-9a-f]{30,})",[^)]*?"getSweTaskRunsAction"')
    for c in chunks:
        try:
            m = pat.search(_req(BASE + c))
        except Exception:
            continue
        if m:
            return m.group(1)
    raise RuntimeError("could not auto-discover getSweTaskRunsAction id")


def parse_leaderboard():
    flight = extract_flight(_req(f"{BASE}/dashboard"))
    cm = re.search(r'"competition_id"\s*:\s*(\d+)', flight)
    comp_id = int(cm.group(1)) if cm else None
    rows = balanced(flight, "sweMiners") or balanced(flight, "miners") or []
    if comp_id is None:
        comp_id = next((r["competition_id"] for r in rows if r.get("competition_id")), None)
    return comp_id, rows


def parse_miner(comp_id, hk):
    flight = extract_flight(_req(f"{BASE}/dashboard/miner/{comp_id}/{hk}"))
    return {"summary": balanced(flight, "sweSummary") or {},
            "penalties": balanced(flight, "swePenalties") or {},
            "tasks": balanced(flight, "sweTasks") or [],
            # 2026-06-29: the dashboard now EMBEDS all per-run rows inline in the page RSC
            # flight under "sweRunsByTaskId" (keyed by task_id) instead of serving them via the
            # on-demand getSweTaskRunsAction server action (which was renamed/removed -> the old
            # action-id auto-discovery broke). Parse them straight from the page; no replay needed.
            "runs_by_task": balanced(flight, "sweRunsByTaskId") or {}}


def fetch_runs(comp_id, hk, task_id, action_id):
    txt = _req(f"{BASE}/dashboard/miner/{comp_id}/{hk}",
               data=json.dumps([comp_id, hk, task_id]).encode(),
               headers={"Next-Action": action_id, "Content-Type": "text/plain;charset=UTF-8"})
    for line in txt.splitlines():
        if line.startswith("1:"):
            try:
                return json.loads(line[2:])
            except json.JSONDecodeError:
                return None
    return None


def scrape_miner(comp_id, hk):
    info = parse_miner(comp_id, hk)
    runs_by_task = info.pop("runs_by_task", {}) or {}
    for t in info["tasks"]:
        tid = t.get("task_id")
        # sweRunsByTaskId keys are STRINGS ("267"); sweTasks task_id is an int -> try both.
        t["runs"] = runs_by_task.get(str(tid)) or runs_by_task.get(tid) or []
    return {"hotkey": hk, "competition_id": comp_id, **info}


def _targets(args, board):
    if args.hotkey:
        return [hk for hk in args.hotkey if HK_RX.match(hk)]
    if args.all:
        return [m["hotkey"] for m in board]
    ours = list(hotkey_to_name())
    leaders = [d["hotkey"] for d in load_top_miners().values() if HK_RX.match(d.get("hotkey", ""))]
    seen, out = set(), []
    for hk in ours + leaders:
        if hk not in seen and HK_RX.match(hk):
            seen.add(hk); out.append(hk)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--hotkey", nargs="+")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--comp-id", type=int)
    ap.add_argument("--workers", type=int, default=4, help="per-task run-fetch concurrency")
    ap.add_argument("--miner-workers", type=int, default=2)
    args = ap.parse_args()

    print("loading leaderboard…")
    comp_id, board = parse_leaderboard()
    if args.comp_id:
        comp_id = args.comp_id
    if comp_id is None:
        print("could not determine competition_id; pass --comp-id", file=sys.stderr)
        return 1
    print(f"  competition_id={comp_id} miners={len(board)}")

    targets = _targets(args, board)
    if args.limit:
        targets = targets[:args.limit]
    names = hotkey_to_name()
    miners_out = []

    def work(hk):
        return scrape_miner(comp_id, hk)

    with ThreadPoolExecutor(max_workers=args.miner_workers) as ex:
        futs = {ex.submit(work, hk): hk for hk in targets}
        for i, f in enumerate(as_completed(futs), 1):
            hk = futs[f]
            tag = names.get(hk, hk[:8])
            try:
                m = f.result()
            except Exception as e:
                print(f"  [{i}/{len(targets)}] {tag} FAILED: {e}", file=sys.stderr)
                continue
            nr = sum(len(t.get("runs", [])) for t in m.get("tasks", []))
            miners_out.append(m)
            print(f"  [{i}/{len(targets)}] {tag:>6} {hk[:10]}… tasks={len(m.get('tasks', []))} runs={nr}")

    if not miners_out:
        print("no miners scraped — refusing to write empty snapshot", file=sys.stderr)
        return 1
    snap = {"observed_at": utc_now(), "source": f"{BASE}/dashboard (inline sweRunsByTaskId in page RSC)",
            "competition_id": comp_id, "leaderboard": board,
            "miner_count": len(miners_out), "miners": miners_out}
    out_dir = PLATFORM_RESULTS / utc_now()[:10]
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = utc_stamp().split("_")[1]
    out_path = out_dir / f"{stamp}_swe_runs.json"
    if out_path.exists():
        out_path = out_dir / f"{stamp}_{len(list(out_dir.glob('*')))}_swe_runs.json"
    out_path.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    tot_runs = sum(sum(len(t.get("runs", [])) for t in m["tasks"]) for m in miners_out)
    print(f"wrote {out_path}  ({len(miners_out)} miners, {tot_runs} run rows)")
    print("next: python scripts/import_platform_results.py && python scripts/normalize_task_scores.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
