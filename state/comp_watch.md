# COMP WATCH ALERT — 2026-06-30T12:08:50Z

_Auto-written by scripts/watch_comp_status.py. Monitor-only; verify on the platform before acting._

## What changed
- **King review_status: scored → failed review.**
- **King eval_status: scored → failed review.**
- **King no longer #1 eligible (now rank None).**

## Current readings
- README check exit=0  source_line=False  omit=False  removed=False
- King 5EeUAVZ…: present=True review=failed review eval=failed review total=0.8520186301179207 rank_eligible=None

## What to do
- **King 5EeUAVZ OR old-king 5DZLFZj dropped / failed-review** (oli's rule: both DQ'd for unapproved `#source line N`) → run `make reward`; with BOTH excluded we PROJECT **23.8%**: np2 reclaims **Pair(E,M) + Single(M)** (14.3%), np3 keeps **Pair(M,H)** (9.5%). DEFEND np2/np3/m26.
- **`#source line N` landed in README ALLOWED set** → it's now a compliant lever → build a line-number-annotation candidate (Codex audit first). Confirm ALLOWED, not a DISALLOWED example.
- **Karim omit-marker landed** → activate `upload_miner_uphard_omitcount.py` (set template, OMIT_COUNT_ENABLED=True, scanner + Codex).
- **Baseline string REMOVED** → our live miners may be NON-COMPLIANT → re-audit immediately.

Full context: `state/CURRENT.md` (top) + `reports/new_king_5EeUAVZ_analysis.md`.
