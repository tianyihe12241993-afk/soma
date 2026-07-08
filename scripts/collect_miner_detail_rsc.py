#!/usr/bin/env python3
"""comp-110 miner-detail collector (RSC-flight method; dashboard went client-rendered 2026-07-08).
The detail page streams its data via GET {page}?_rsc=<token> with RSC:1 + Next-Router-State-Tree headers.
Fetch that, extract the task array (contains tokens_without/with_compression + input/cached/output splits),
write an immutable snapshot, and print raw+weighted footprints. _rsc token is discovered from the page HTML."""
from __future__ import annotations
import json, re, sys, urllib.parse, urllib.request, gzip, io, time
from pathlib import Path

RAW = Path("/Users/eric.xiao/joshua-work/soma/data/raw/dashboard")
BASE = "https://thesoma.ai/dashboard/miner/110/{hk}"

def _get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    r = urllib.request.urlopen(req, timeout=25); data = r.read()
    if r.headers.get("content-encoding") == "gzip":
        data = gzip.GzipFile(fileobj=io.BytesIO(data)).read()
    return data.decode("utf-8", "ignore")

def _rsc_token(html):
    m = re.search(r'"(?:_rsc|rsc)":"([A-Za-z0-9_-]{6,})"', html) or re.search(r'\?_rsc=([A-Za-z0-9_-]{6,})', html)
    return m.group(1) if m else None

def _state_tree(hk):
    inner = ["", {"children": ["dashboard", {"children": ["miner", {"children": [
        ["comp_id", "110", "d"], {"children": [["hotkey", hk, "d"], {"children": ["__PAGE__", {}, None, None]},
        None, None]}, None, None]}, None, None]}, None, None]}, None, "refetch"]
    return urllib.parse.quote(json.dumps(inner, separators=(",", ":")), safe="")

def _extract_tasks(flight):
    """Extract ALL task arrays (every benchmark type-group), dedup by (task_id, benchmark_type)."""
    rows, seen, pos = [], set(), 0
    while True:
        i = flight.find('"task_name"', pos)
        if i < 0: break
        j = flight.rfind("[", 0, i)
        depth = 0; arr = None
        for k in range(j, min(len(flight), j + 400000)):
            if flight[k] == "[": depth += 1
            elif flight[k] == "]":
                depth -= 1
                if depth == 0:
                    try: arr = json.loads(flight[j:k+1])
                    except Exception: arr = None
                    pos = k
                    break
        if pos <= i: pos = i + 10
        if isinstance(arr, list):
            for t in arr:
                if isinstance(t, dict) and t.get("task_name"):
                    key = (t.get("task_id"), t.get("benchmark_type"), t.get("task_name"))
                    if key not in seen:
                        seen.add(key); rows.append(t)
        pos = max(pos, i + 10)
    return rows

def fetch(hk):
    page = BASE.format(hk=hk)
    html = _get(page)
    tok = _rsc_token(html)
    url = page + (f"?_rsc={tok}" if tok else "?_rsc=1")
    flight = _get(url, {"User-Agent": "Mozilla/5.0", "RSC": "1", "Next-Router-State-Tree": _state_tree(hk), "Accept": "*/*"})
    return _extract_tasks(flight)

def foot(hk, tasks):
    ts = tasks
    TB = sum(t["tokens_without_compression"] for t in ts)
    TW = sum(t.get("tokens_with_compression") or 0 for t in ts)
    I = sum(t.get("input_tokens_with_compression") or 0 for t in ts)
    C = sum(t.get("cached_input_tokens_with_compression") or 0 for t in ts)
    O = sum(t.get("output_tokens_with_compression") or 0 for t in ts)
    Wm = I + 0.1 * C + 3 * O
    print(f"\n=== {hk[:12]} — {len(ts)} screener rows ===")
    print(f"  RAW savings   = {100*(1-TW/TB):.1f}%   (base {TB:,} -> miner {TW:,})")
    print(f"  splits: input {I:,} cached {C:,} output {O:,} | input-frac {100*I/(I+C):.1f}% | out/row {O/len(ts):.0f}")
    print(f"  miner weighted (1/.1/3) = {Wm:,.0f}   (baseline weighted UNKNOWN — no base split served)")
    pw = sum(1 for t in ts if t.get("pass_with_compression"))
    neg = sum(1 for t in ts if (t.get('tokens_with_compression') or 0) > t['tokens_without_compression'])
    print(f"  pass_with = {pw}/{len(ts)} | negative-savings tasks = {neg}/{len(ts)}")
    for t in ts:
        b, w = t["tokens_without_compression"], t.get("tokens_with_compression") or 0
        print(f"    {str(t.get('task_name'))[-9:]:9s} sav {100*(1-w/b):5.1f}%  pass_w/o={t.get('pass_without_compression')} pass_w={t.get('pass_with_compression')} scr={t.get('is_screener')}")
    return ts

if __name__ == "__main__":
    hks = sys.argv[1:]
    stamp = time.strftime("%H%M%S")
    out = {}
    for hk in hks:
        try:
            tasks = fetch(hk); out[hk] = tasks; foot(hk, tasks)
        except Exception as e:
            print(f"{hk[:12]}: FETCH FAILED {e}", file=sys.stderr)
    day = time.strftime("%Y-%m-%d"); (RAW / day).mkdir(parents=True, exist_ok=True)
    p = RAW / day / f"{stamp}_miner_detail_rsc.json"
    p.write_text(json.dumps(out, indent=1)); print(f"\nsnapshot -> {p}")
