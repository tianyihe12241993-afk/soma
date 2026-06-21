#!/usr/bin/env python3
"""Layer-based incentive computation (per INCENTIVE_MECHANISM.md).

Layers / weights:
  L0 {(E,M,H)}                 W=1       -> element weight 1
  L1 {(E,M),(E,H),(M,H)}       W=1/2     -> each element 1/6
  L2 {(E),(M),(H)}             W=1/4     -> each element 1/12
Element winner = miner with the highest AVERAGE score over that category subset
(category-score average proxy; failed-review miners excluded).

Outputs:
  data/latest/category_winners.json
  reports/reward_projection.md
Flags whether any of OUR miners (config/miners.yaml) win an element.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (LATEST, REPORTS, utc_now, hotkey_to_name,  # noqa: E402
                     latest_processed_rows, latest_raw_snapshot)

ELEMENTS = [
    ("Overall (E,M,H)", ("easy", "medium", "hard"), 1.0),
    ("Pair (E,M)",      ("easy", "medium"),         1/6),
    ("Pair (E,H)",      ("easy", "hard"),           1/6),
    ("Pair (M,H)",      ("medium", "hard"),         1/6),
    ("Single (E)",      ("easy",),                  1/12),
    ("Single (M)",      ("medium",),                1/12),
    ("Single (H)",      ("hard",),                  1/12),
]


def _load_rows() -> list:
    rows = latest_processed_rows()
    if rows:
        return rows
    snap = latest_raw_snapshot()                          # fall back to newest raw
    if not snap:
        return []
    names = hotkey_to_name()
    return [{"hotkey": m["hotkey"], "display_name": names.get(m["hotkey"], ""),
             "easy": m.get("easy"), "medium": m.get("medium"), "hard": m.get("hard"),
             "review_status": m.get("review_status", ""), "eval_status": m.get("eval_status", "")}
            for m in json.loads(snap.read_text()).get("miners", [])]


def _is_failed(r: dict) -> bool:
    return "fail" in str(r.get("review_status", "")).lower()


def main() -> int:
    rows = _load_rows()
    names = hotkey_to_name()
    ours = set(names)
    # eligible = scored (numbers present) and not failed-review
    elig = [r for r in rows if not _is_failed(r)
            and all(isinstance(r.get(c), (int, float)) for c in ("easy", "medium", "hard"))]

    winners = {}
    weights = {}                                          # hotkey -> accumulated W_total
    for label, cats, w in ELEMENTS:
        def score(r):
            return sum(r[c] for c in cats) / len(cats)
        if not elig:
            continue
        best = max(score(r) for r in elig)
        win = [r for r in elig if abs(score(r) - best) < 1e-9]
        winners[label] = {"score": round(best, 4), "weight": round(w, 6),
                          "winners": [{"hotkey": r["hotkey"], "name": names.get(r["hotkey"], "")}
                                      for r in win]}
        for r in win:
            weights[r["hotkey"]] = weights.get(r["hotkey"], 0.0) + w / len(win)

    total_w = sum(weights.values()) or 1.0
    incentive = {hk: round(w / total_w, 4) for hk, w in weights.items()}
    our_wins = {lab: w for lab, w in winners.items()
                if any(x["hotkey"] in ours for x in w["winners"])}

    LATEST.mkdir(parents=True, exist_ok=True)
    out = {"computed_at": utc_now(), "eligible_miners": len(elig),
           "excluded_failed_review": [r["hotkey"] for r in rows if _is_failed(r)],
           "elements": winners,
           "incentive_share_of_pool": dict(sorted(incentive.items(), key=lambda kv: -kv[1])),
           "our_element_wins": list(our_wins.keys())}
    (LATEST / "category_winners.json").write_text(json.dumps(out, indent=2))

    # ---- markdown report ----
    L = [f"# Reward Projection", f"_computed {utc_now()} — {len(elig)} eligible miners "
         f"(failed-review excluded)_", ""]
    L.append("## Element winners")
    L.append("| element | weight | winner | score |")
    L.append("|---------|--------|--------|-------|")
    for label, _, _ in ELEMENTS:
        w = winners.get(label)
        if not w:
            continue
        who = ", ".join((x["name"] or x["hotkey"][:8]) + ("**(OURS)**" if x["hotkey"] in ours else "")
                        for x in w["winners"])
        L.append(f"| {label} | {w['weight']:.4f} | {who} | {w['score']:.4f} |")
    L += ["", "## Incentive share of the miner pool"]
    L.append("| miner | share |")
    L.append("|-------|-------|")
    for hk, sh in sorted(incentive.items(), key=lambda kv: -kv[1]):
        tag = names.get(hk, "")
        L.append(f"| {(tag+' ' if tag else '')}{hk[:10]}…{' (OURS)' if hk in ours else ''} | {sh*100:.1f}% |")
    L += ["", "## Do WE win anything?"]
    if our_wins:
        for lab in our_wins:
            L.append(f"- ✅ **{lab}** — element won by our miner.")
    else:
        L.append("- ❌ **No** — none of our miners currently wins any of the 7 elements.")
        # show our best gap on Single (M), usually our closest
        m_elig = sorted(elig, key=lambda r: -r["medium"])
        ours_rows = [r for r in elig if r["hotkey"] in ours]
        if m_elig and ours_rows:
            best_ours_m = max(ours_rows, key=lambda r: r["medium"])
            L.append(f"  - Closest = Medium: our best {best_ours_m.get('display_name','?')} "
                     f"{best_ours_m['medium']:.3f} vs winner {m_elig[0]['medium']:.3f} "
                     f"(gap {m_elig[0]['medium']-best_ours_m['medium']:+.3f}).")
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "reward_projection.md").write_text("\n".join(L) + "\n")
    print(f"wrote {LATEST/'category_winners.json'} and {REPORTS/'reward_projection.md'}")
    print("our element wins:", our_wins or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
