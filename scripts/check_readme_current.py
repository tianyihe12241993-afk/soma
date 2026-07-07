#!/usr/bin/env python3
"""Standing PRE-UPLOAD rules gate: is the live README_prompting.md still the set we're compliant with?

Rebuilt 2026-07-07 (the comp-108 original was never committed — scripts/ was gitignored).

Fetches the LIVE miner/README_prompting.md from DendriteHQ/SOMA@main, extracts the allowed
exact strings (§5.1 Markers + §5.2 Loop Detection), snapshots it to data/raw/readme_prompting/,
and compares against the BASELINE set our miners were verified against (comp-108, re-verified
for comp-110 on 2026-07-07). Optionally verifies that a candidate file's emitted marker/loop
strings are a subset of the live allowed set.

Exit codes (contract from comp-108 ops):
  0 = allowed set unchanged (safe to proceed to the next gate)
  2 = NEW allowed string(s) landed (review — possible new lever; not a block)
  3 = a BASELINE string was REMOVED (BLOCK uploads — our miners may now be non-compliant)
  1 = fetch/parse failure (treat as unknown; retry before uploading)

Usage:
  python3 scripts/check_readme_current.py                      # gate only
  python3 scripts/check_readme_current.py --check-file PATH    # + verify a miner file's strings
"""
from __future__ import annotations
import argparse
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import RAW, utc_now, utc_stamp  # noqa: E402

RAW_URL = "https://raw.githubusercontent.com/DendriteHQ/SOMA/main/miner/README_prompting.md"
SNAP_DIR = RAW.parent / "readme_prompting"

# The allowed set our candidates are verified against (README §5.1 + §5.2).
# ⚠ 2026-07-07 ~07:36Z: the owners MERGED the comp-110 prompt PR — 6 NEW markers landed (was 9→15).
# New: omission markers [[Omitted]]/[[/Omitted]] + [[deleted]]/[[/deleted]] (may replace [[CMP]]),
# and SOURCE-LINE-REFERENCE markers `[[CMP]] source line N [[/CMP]]` /
# `[[CMP]] source line N ~ source line M Omitted [[/CMP]]` — README §1: "when compressing code,
# include a source line reference inside the marker so omitted lines remain locatable."
# = line-number provenance is now LEGAL (it was the DQ'd comp-108 king's Hard edge). NEW LEVER.
# Our uploaded miners emit only a SUBSET (still compliant). Baseline updated to the live 15.
BASELINE = {
    "Compressed text starts here",
    "Compressed text ends here",
    "[[CMP]]",
    "[[/CMP]]",
    "[[Omitted]]",
    "[[/Omitted]]",
    "[[deleted]]",
    "[[/deleted]]",
    "[[BLOCK X]]",
    "[[/BLOCK X]]",
    "Same response as in [[BLOCK X]].",
    "[[CMP]] source line N [[/CMP]]",
    "[[CMP]] source line N ~ source line M Omitted [[/CMP]]",
    "loop_detected: repeated assistant response",
    "loop_detected: repeated tool call signature",
}


def fetch_readme() -> str:
    req = urllib.request.Request(RAW_URL, headers={"User-Agent": "soma-ops-collector/1.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")


def extract_allowed(md: str) -> set[str]:
    """Pull the backticked exact strings from the '## 5) Allowed Prompts' section."""
    m = re.search(r"##\s*5\)\s*Allowed Prompts(.*?)(?:\n##[^#]|\Z)", md, re.S)
    section = m.group(1) if m else md
    return set(re.findall(r"^\s*-\s*`([^`]+)`\s*$", section, re.M))


def file_strings(path: Path) -> set[str]:
    """Marker/loop strings a miner file can emit (patterns from the comp-108 audit + the comp-110
    source-line templates). Captures the FULL `[[CMP]] source line ... [[/CMP]]` span so its content
    is verified against the allowed template — not just the bare [[CMP]]/[[/CMP]] tokens."""
    src = path.read_text(encoding="utf-8", errors="ignore")
    pats = re.findall(
        r"\[\[CMP\]\][^\[]*?source line[^\[]*?\[\[/CMP\]\]"   # full source-line omission templates
        r"|\[\[[^\]]*\]\]|loop_detected: [a-z_ ]+|Compressed text (?:starts|ends) here"
        r"|Same response as in[^\"'\n]*", src)
    return {p.strip() for p in pats}


def normalize(s: str) -> str:
    """Fold placeholder/number variants onto the README's canonical N/M/X forms so a filled-in
    marker (e.g. `[[CMP]] source line 42 ~ source line 99 Omitted [[/CMP]]`) matches its §5.1
    template. Lazy [[BLOCK ...]] match tolerates f-string placeholders like [[BLOCK {seen[h]}]]."""
    s = re.sub(r"\[\[(/?)BLOCK .*?\]\]", r"[[\1BLOCK X]]", s)
    # source-line omission markers: real ints OR f-string placeholders ({N}, {start}) -> N / M
    s = re.sub(r"(\[\[CMP\]\] source line )\S+?( ~ source line )\S+?( Omitted \[\[/CMP\]\])",
               r"\1N\2M\3", s)
    s = re.sub(r"(\[\[CMP\]\] source line )\S+?( \[\[/CMP\]\])", r"\1N\2", s)
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-file", type=Path, help="also verify this miner file's strings vs the live set")
    args = ap.parse_args()

    try:
        md = fetch_readme()
        live = extract_allowed(md)
        if not live:
            raise ValueError("parsed 0 allowed strings — README format changed, update extract_allowed()")
    except Exception as e:
        print(f"GATE=UNKNOWN fetch/parse failed: {e}", file=sys.stderr)
        return 1

    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    snap = SNAP_DIR / f"{utc_stamp()}_README_prompting.md"
    snap.write_text(f"<!-- fetched {utc_now()} from {RAW_URL} -->\n" + md, encoding="utf-8")

    removed = BASELINE - live
    added = live - BASELINE
    print(f"live allowed strings: {len(live)}  (snapshot: {snap.relative_to(snap.parents[3])})")

    rc = 0
    if removed:
        print(f"GATE=BLOCK — baseline string(s) REMOVED from the README: {sorted(removed)}")
        rc = 3
    elif added:
        print(f"GATE=REVIEW — new allowed string(s) landed (possible new lever): {sorted(added)}")
        rc = 2
    else:
        print("GATE=PASS — allowed set unchanged vs baseline.")

    if args.check_file:
        emitted = {normalize(s) for s in file_strings(args.check_file)}
        extra = {s for s in emitted if s not in live and not s.startswith("[[BLOCK")}
        extra |= {s for s in emitted if s.startswith("[[") and s not in live}
        if extra:
            print(f"FILE=FAIL — {args.check_file} emits strings NOT in the live allowed set: {sorted(extra)}")
            rc = max(rc, 3)
        else:
            print(f"FILE=PASS — every string {args.check_file.name} emits is in the live allowed set.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
