#!/usr/bin/env python3
"""Collect an IMMUTABLE raw dashboard snapshot.

Stores: data/raw/dashboard/YYYY-MM-DD/HHMMSS_leaderboard.json  (never overwritten)

Modes:
  (default)            fetch the live dashboard HTML and extract the embedded leaderboard JSON.
  --import <file>      import a manually-saved leaderboard (raw HTML, JSON array, or CSV paste)
                       when browser/network automation isn't available.

The raw snapshot is a JSON object:
  {"observed_at": "...Z", "source": "...", "miners": [ {hotkey, total, easy, medium, hard,
   review_status, eval_status, rank}, ... ]}
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import RAW, utc_now, utc_stamp  # noqa: E402

CFG = (Path(__file__).resolve().parent.parent / "config" / "dashboard.yaml").read_text()
URL = (re.search(r'leaderboard_url:\s*"([^"]+)"', CFG) or [None, "https://thesoma.ai/dashboard"])[1]


def _extract_from_html(html: str) -> list:
    """Pull per-miner records out of the embedded JSON in the dashboard HTML.

    Records are concatenated objects: {"hotkey":..,"total_score":..,"screener_passed":..,
    "category_scores":{"Easy":..,"Medium":..,"Hard":..},"status":"scored|in queue|failed review"}.
    Splitting on the `"hotkey":"` delimiter bounds each record so its fields associate to the
    right hotkey (no fixed-window guessing). Queued/unevaluated rows have no category_scores.
    Deduped by hotkey, preferring the scored entry.
    """
    h = html.replace('\\"', '"')
    cs_rx = re.compile(r'"category_scores":\{"Easy":([\d.eE+-]+),"Medium":([\d.eE+-]+),"Hard":([\d.eE+-]+)\}')
    total_rx = re.compile(r'"total_score":(null|[\d.eE+-]+)')
    status_rx = re.compile(r'"status":"([^"]*)"')
    out: dict = {}
    for chunk in h.split('"hotkey":"')[1:]:
        hk = chunk[:48]
        if not re.fullmatch(r'[1-9A-HJ-NP-Za-km-z]{48}', hk):
            continue
        rec = chunk[:6000]                                   # this record (bounded by next hotkey)
        st = (status_rx.search(rec) or [None, ""])[1] if status_rx.search(rec) else ""
        cs = cs_rx.search(rec)
        if cs:
            E, M, H = float(cs.group(1)), float(cs.group(2)), float(cs.group(3))
            tm = total_rx.search(rec)
            total = float(tm.group(1)) if (tm and tm.group(1) != "null") else round((E + M + H) / 3, 6)
            entry = {"hotkey": hk, "total": total, "easy": E, "medium": M, "hard": H,
                     "review_status": st or "scored", "eval_status": st or "scored"}
        else:
            entry = {"hotkey": hk, "total": None, "easy": None, "medium": None, "hard": None,
                     "review_status": st, "eval_status": st or "pending"}
        if hk not in out or (entry["easy"] is not None and out[hk]["easy"] is None):
            out[hk] = entry
    return list(out.values())


def _extract_from_csv(text: str) -> list:
    """CSV/paste import. Accepts rows: hotkey,total,easy,hard,medium[,review][,eval]
    (matching the dashboard's displayed column order total/Easy/Hard/Medium)."""
    out = []
    for line in text.splitlines():
        parts = [p.strip() for p in re.split(r'[,\t]', line) if p.strip()]
        if not parts or not re.match(r'[1-9A-HJ-NP-Za-km-z]{6,48}', parts[0]):
            continue
        try:
            hk, total, easy, hard, medium = parts[0], float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
        except (IndexError, ValueError):
            continue
        review = parts[5] if len(parts) > 5 else "scored"
        out.append({"hotkey": hk, "total": total, "easy": easy, "medium": medium,
                    "hard": hard, "review_status": review, "eval_status": "scored"})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--import", dest="imp", help="path to saved leaderboard (html/json/csv)")
    args = ap.parse_args()

    source = URL
    if args.imp:
        raw = Path(args.imp).read_text(encoding="utf-8", errors="ignore")
        source = f"import:{args.imp}"
        if raw.lstrip().startswith(("{", "[")):
            obj = json.loads(raw)
            miners = obj.get("miners", obj) if isinstance(obj, dict) else obj
        elif "<html" in raw[:500].lower() or '"hotkey"' in raw[:5000]:
            miners = _extract_from_html(raw)
        else:
            miners = _extract_from_csv(raw)
    else:
        req = urllib.request.Request(URL, headers={"User-Agent": "soma-ops-collector/1.0"})
        try:
            html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
        except Exception as e:
            print(f"FETCH FAILED ({e}). Save the dashboard and use --import <file>.", file=sys.stderr)
            return 1
        miners = _extract_from_html(html)

    if not miners:
        print("No miner records parsed — refusing to write empty snapshot.", file=sys.stderr)
        return 1

    snap = {"observed_at": utc_now(), "source": source, "miner_count": len(miners), "miners": miners}
    day = utc_now()[:10]
    out_dir = RAW / day
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{utc_stamp().split('_')[1]}_leaderboard.json"
    if out_path.exists():                                  # never overwrite raw
        out_path = out_dir / f"{utc_stamp().split('_')[1]}_{len(list(out_dir.glob('*')))}_leaderboard.json"
    out_path.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    print(f"wrote {out_path}  ({len(miners)} miners)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
