#!/usr/bin/env python3
"""Collect DETAILED per-task scores from each miner's dashboard detail page.

The leaderboard collector (collect_dashboard.py) captures only total + the three
category scores. This one fetches each miner's detail page
    https://thesoma.ai/dashboard/miner/107/<hotkey>
and extracts the full per-task SWE-bench breakdown the platform exposes:

  sweTasks[]    task_id, task_name, is_screener, pass_without_compression,
                pass_with_compression, tokens_without_compression,
                tokens_with_compression, platform_score, run_count
  sweSummary    total_score, screener_passed, category_scores{Easy,Medium,Hard},
                task_count, screener_task_count
  swePenalties  categories{Easy,Medium,Hard}, total
  profile       registered_at, contests, status; last_contest{rank,...};
                source_code.available

Writes an IMMUTABLE raw snapshot (never overwritten):
    data/raw/dashboard/YYYY-MM-DD/HHMMSS_miner_detail.json
and derived, regenerable artifacts:
    data/latest/miner_detail.json   (full machine record, all fetched miners)
    data/latest/task_scores.csv     (flat one-row-per-task table for analysis)
    reports/task_detail.md          (human summary + our per-task breakdown)

Targets (default = OURS + current element leaders):
    (default)          our miners (config/miners.yaml)
                       + element winners (data/latest/category_winners.json)
    --all              every SCORED hotkey in the latest leaderboard snapshot
    --hotkey HK [..]   explicit hotkey(s)
    --no-report        skip the derived report/csv (raw snapshot only)
    --sleep SECONDS    delay between requests (default 0.3, be polite)
"""
from __future__ import annotations
import argparse
import csv
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (RAW, LATEST, REPORTS, CONFIG, utc_now, utc_stamp,  # noqa: E402
                     read_text, hotkey_to_name, latest_raw_snapshot)

CFG = read_text(CONFIG / "dashboard.yaml")
COMP_ID = (re.search(r'competition_id:\s*(\d+)', CFG) or [None, "107"])[1]
MINER_URL = (re.search(r'miner_page_url:\s*"([^"]+)"', CFG)
             or [None, "https://thesoma.ai/dashboard/miner/{comp}/{hotkey}"])[1]
# back-compat: tolerate an older config that hard-coded the competition id.
MINER_URL = re.sub(r'/miner/\d+/', "/miner/{comp}/", MINER_URL)
HK_RX = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{48}$')


# ----------------------------- parsing -------------------------------------
def _balanced(s: str, i: int) -> str | None:
    """Return s[i:j] where s[i] is '[' or '{' and j closes it (string-aware)."""
    open_ch = s[i]
    close_ch = "]" if open_ch == "[" else "}"
    depth = 0
    in_str = esc = False
    for j in range(i, len(s)):
        c = s[j]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return s[i:j + 1]
    return None


def _block(h: str, key: str):
    """json.loads the array/object that follows `"key":` in unescaped html."""
    m = re.search(r'"%s":\s*([\[{])' % re.escape(key), h)
    if not m:
        return None
    blob = _balanced(h, m.end() - 1)
    if not blob:
        return None
    try:
        return json.loads(blob)
    except (ValueError, json.JSONDecodeError):
        return None


def parse_detail(html: str, hotkey: str) -> dict:
    """Extract the detail record from a per-miner page's RSC stream."""
    h = html.replace('\\"', '"')
    summary = _block(h, "sweSummary") or {}
    penalties = _block(h, "swePenalties") or {}
    tasks = _block(h, "sweTasks") or []
    miner = _block(h, "miner") or {}
    last_contest = _block(h, "last_contest") or {}
    src = re.search(r'"source_code":\{"available":(true|false)', h)
    cat = summary.get("category_scores") or {}
    return {
        "hotkey": hotkey,
        "total_score": summary.get("total_score"),
        "screener_passed": summary.get("screener_passed"),
        "category_scores": cat,
        "task_count": summary.get("task_count"),
        "screener_task_count": summary.get("screener_task_count"),
        "penalty_total": (penalties or {}).get("total"),
        "penalty_categories": (penalties or {}).get("categories"),
        "rank": last_contest.get("rank"),
        "registered_at": miner.get("registered_at"),
        "contests": miner.get("contests"),
        "status": miner.get("status") or last_contest.get("status"),
        "source_code_available": (src.group(1) == "true") if src else None,
        "tasks": tasks,
    }


# ----------------------------- fetching ------------------------------------
def fetch(hotkey: str, timeout: int = 40) -> str:
    url = MINER_URL.format(comp=COMP_ID, hotkey=hotkey)
    req = urllib.request.Request(url, headers={"User-Agent": "soma-ops-collector/1.0"})
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")


def _target_hotkeys(args) -> list:
    if args.hotkey:
        return [hk for hk in args.hotkey if HK_RX.match(hk)]
    if args.all:
        snap = latest_raw_snapshot()
        if not snap:
            print("No leaderboard snapshot — run collect_dashboard.py first.", file=sys.stderr)
            return []
        miners = json.loads(snap.read_text(encoding="utf-8")).get("miners", [])
        return [m["hotkey"] for m in miners if m.get("easy") is not None]   # scored only
    # default: ours + current element leaders
    ours = list(hotkey_to_name())
    leaders: list = []
    cw = LATEST / "category_winners.json"
    if cw.exists():
        data = json.loads(cw.read_text(encoding="utf-8"))
        for el in data.get("elements", {}).values():
            leaders += [w["hotkey"] for w in el.get("winners", [])]
    seen, ordered = set(), []
    for hk in ours + leaders:
        if hk not in seen and HK_RX.match(hk):
            seen.add(hk)
            ordered.append(hk)
    return ordered


# ----------------------------- derived report ------------------------------
def _ratio(t: dict):
    a, b = t.get("tokens_without_compression"), t.get("tokens_with_compression")
    return (a / b) if (a and b) else None


def write_derived(records: list, names: dict) -> None:
    LATEST.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (LATEST / "miner_detail.json").write_text(
        json.dumps({"computed_at": utc_now(), "miners": records}, indent=2), encoding="utf-8")

    # flat per-task CSV
    with (LATEST / "task_scores.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name", "hotkey", "task_id", "task_name", "is_screener",
                    "pass_without", "pass_with", "tokens_without", "tokens_with",
                    "comp_ratio", "platform_score", "run_count"])
        for r in records:
            nm = names.get(r["hotkey"], "")
            for t in r.get("tasks", []):
                rt = _ratio(t)
                w.writerow([nm, r["hotkey"], t.get("task_id"), t.get("task_name"),
                            t.get("is_screener"), t.get("pass_without_compression"),
                            t.get("pass_with_compression"), t.get("tokens_without_compression"),
                            t.get("tokens_with_compression"), round(rt, 3) if rt else "",
                            t.get("platform_score"), t.get("run_count")])

    # markdown report
    L = [f"# Per-task detail", f"_computed {utc_now()} — {len(records)} miners "
         f"(machine: data/latest/miner_detail.json, data/latest/task_scores.csv)_", ""]
    L.append("## Summary (fetched miners)")
    L.append("| miner | total | Easy | Medium | Hard | tasks | pass w/ | pass w/o | mean ratio | penalty |")
    L.append("|-------|-------|------|--------|------|-------|---------|----------|-----------|---------|")
    for r in sorted(records, key=lambda r: -(r["total_score"] or -9)):
        nm = names.get(r["hotkey"], r["hotkey"][:8])
        tag = nm if r["hotkey"] not in names else f"**{nm}**"
        cat = r.get("category_scores") or {}
        evald = [t for t in r["tasks"] if not t.get("is_screener")]
        pw = sum(1 for t in evald if t.get("pass_with_compression"))
        pwo = sum(1 for t in evald if t.get("pass_without_compression"))
        ratios = [x for x in (_ratio(t) for t in evald) if x]
        mr = sum(ratios) / len(ratios) if ratios else 0
        def fmt(v): return f"{v:.3f}" if isinstance(v, (int, float)) else "—"
        L.append(f"| {tag} | {fmt(r['total_score'])} | {fmt(cat.get('Easy'))} | "
                 f"{fmt(cat.get('Medium'))} | {fmt(cat.get('Hard'))} | {len(evald)} | "
                 f"{pw} | {pwo} | {mr:.2f}× | {fmt(r.get('penalty_total'))} |")

    # per-task table for OUR best fetched miner (highest total among ours)
    ours_recs = [r for r in records if r["hotkey"] in names and r.get("tasks")]
    if ours_recs:
        best = max(ours_recs, key=lambda r: r["total_score"] or -9)
        L += ["", f"## Per-task breakdown — {names[best['hotkey']]} "
              f"(total {best['total_score']:.3f})"]
        L.append("| task | pass w/o→w/ | tok w/o | tok w/ | ratio | score |")
        L.append("|------|------------|---------|--------|-------|-------|")
        for t in sorted(best["tasks"], key=lambda t: -(t.get("platform_score") or -9)):
            if t.get("is_screener"):
                continue
            rt = _ratio(t)
            pf = f"{'✓' if t.get('pass_without_compression') else '✗'}→{'✓' if t.get('pass_with_compression') else '✗'}"
            L.append(f"| {t.get('task_name')} | {pf} | {t.get('tokens_without_compression')} | "
                     f"{int(t.get('tokens_with_compression') or 0)} | "
                     f"{rt:.2f}× | {t.get('platform_score'):.3f} |"
                     if rt else
                     f"| {t.get('task_name')} | {pf} | — | — | — | "
                     f"{(t.get('platform_score') or 0):.3f} |")
    (REPORTS / "task_detail.md").write_text("\n".join(L) + "\n", encoding="utf-8")


# ----------------------------- main ----------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="all scored hotkeys in latest leaderboard")
    ap.add_argument("--hotkey", nargs="+", help="explicit hotkey(s)")
    ap.add_argument("--no-report", action="store_true", help="raw snapshot only")
    ap.add_argument("--sleep", type=float, default=0.3, help="delay between requests")
    args = ap.parse_args()

    targets = _target_hotkeys(args)
    if not targets:
        print("No target hotkeys resolved.", file=sys.stderr)
        return 1
    names = hotkey_to_name()
    print(f"fetching detail for {len(targets)} miners (comp {COMP_ID})…")

    records, failed = [], []
    for i, hk in enumerate(targets, 1):
        tag = names.get(hk, hk[:8])
        try:
            rec = parse_detail(fetch(hk), hk)
            records.append(rec)
            n = len([t for t in rec["tasks"] if not t.get("is_screener")])
            print(f"  [{i}/{len(targets)}] {tag:>6} {hk[:10]}… "
                  f"total={rec['total_score']} tasks={n} status={rec.get('status')}")
        except Exception as e:                                 # noqa: BLE001
            failed.append(hk)
            print(f"  [{i}/{len(targets)}] {tag:>6} {hk[:10]}… FAILED ({e})", file=sys.stderr)
        if args.sleep and i < len(targets):
            time.sleep(args.sleep)

    if not records:
        print("No detail records parsed — refusing to write empty snapshot.", file=sys.stderr)
        return 1

    snap = {"observed_at": utc_now(), "source": MINER_URL.format(comp=COMP_ID, hotkey="<hotkey>"),
            "competition_id": int(COMP_ID), "miner_count": len(records),
            "failed": failed, "miners": records}
    day = utc_now()[:10]
    out_dir = RAW / day
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = utc_stamp().split("_")[1]
    out_path = out_dir / f"{stamp}_miner_detail.json"
    if out_path.exists():                                      # never overwrite raw
        out_path = out_dir / f"{stamp}_{len(list(out_dir.glob('*')))}_miner_detail.json"
    out_path.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    print(f"wrote {out_path}  ({len(records)} miners, {len(failed)} failed)")

    if not args.no_report:
        write_derived(records, names)
        print(f"wrote {LATEST/'miner_detail.json'}, {LATEST/'task_scores.csv'}, "
              f"{REPORTS/'task_detail.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
