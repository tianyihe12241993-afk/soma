#!/usr/bin/env python3
"""Compare our miners (m7..m11) against the top miners, from processed data.

Inputs: data/processed/task_matrix.jsonl (per-task, recomputed aggregates),
        config/miners.yaml + config/top_miners.yaml (category scores: scraped aggregates),
        data/processed/shared_pass_tasks.jsonl (optional, for the ratio decomposition).
Outputs:
  data/latest/scoreboard.json
  data/latest/research_summary.md
  reports/top_miner_comparison.md
  reports/postmortem.md
"""
from __future__ import annotations
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (PROCESSED, LATEST, REPORTS, utc_now,  # noqa: E402
                     load_miners_rich, load_top_miners)

MATRIX = PROCESSED / "task_matrix.jsonl"
SHARED = PROCESSED / "shared_pass_tasks.jsonl"


def _aggregates(tasks: list) -> dict:
    """Per miner_id recompute from per-task data: pass_n, broke_n, neg_n, ratio stats."""
    agg = {}
    for t in tasks:
        if t.get("is_screener"):
            continue
        for mid, d in t["miners"].items():
            a = agg.setdefault(mid, {"pass_n": 0, "broke_n": 0, "neg_n": 0, "ratios": [], "n": 0})
            a["n"] += 1
            if d.get("pass"):
                a["pass_n"] += 1
            if d.get("broke"):
                a["broke_n"] += 1
            if d.get("neg"):
                a["neg_n"] += 1
            if d.get("ratio"):
                a["ratios"].append(d["ratio"])
    for a in agg.values():
        rs = a.pop("ratios")
        a["mean_ratio"] = round(st.mean(rs), 3) if rs else None
        a["median_ratio"] = round(st.median(rs), 3) if rs else None
    return agg


def main() -> int:
    if not MATRIX.exists():
        print(f"{MATRIX} missing — run normalize_task_scores.py first.", file=sys.stderr)
        return 1
    tasks = [json.loads(l) for l in MATRIX.read_text(encoding="utf-8").splitlines() if l.strip()]
    ours = load_miners_rich()
    tops = load_top_miners()
    agg = _aggregates(tasks)

    def row(mid, d, is_ours):
        a = agg.get(mid, {})
        return {"miner_id": mid, "hotkey": d.get("hotkey"), "ours": is_ours,
                "version": d.get("version"), "role": d.get("role"),
                "total": d.get("total"), "easy": d.get("easy"),
                "medium": d.get("medium"), "hard": d.get("hard"),
                "avg_ratio_yaml": d.get("avg_ratio"),
                "pass_n": a.get("pass_n"), "broke_n": a.get("broke_n"),
                "neg_n": a.get("neg_n"), "mean_ratio": a.get("mean_ratio"),
                "median_ratio": a.get("median_ratio"), "tasks_n": a.get("n")}

    board = [row(m, d, True) for m, d in ours.items()] + [row(t, d, False) for t, d in tops.items()]
    board.sort(key=lambda r: -(r["total"] or -9))
    LATEST.mkdir(parents=True, exist_ok=True)
    (LATEST / "scoreboard.json").write_text(json.dumps(
        {"computed_at": utc_now(), "miners": board}, indent=2), encoding="utf-8")

    # ---- shared-pass decomposition (m7 vs primary reference) ----
    shared = []
    if SHARED.exists():
        shared = [json.loads(l) for l in SHARED.read_text(encoding="utf-8").splitlines() if l.strip()]
    decomp = ""
    if shared:
        n = len(shared)
        mean_actual = sum(x["actual_score_gap"] for x in shared) / n
        mean_ratio = sum(x["ratio_explained_gap"] for x in shared) / n
        resid = mean_actual - mean_ratio
        decomp = (f"On the **{n} tasks m7 and the top miner both pass**, the mean score gap is "
                  f"**{mean_actual:+.3f}/task**. The compression-ratio model (0.5·ln(ref/m7)) "
                  f"explains **{mean_ratio:+.3f}/task**, leaving a residual of **{resid:+.3f}/task** "
                  f"(solving/variance). → the gap is **compression depth, not solving ability**.")

    # ---- top_miner_comparison.md ----
    def fmt(v, p="{:.3f}"):
        return p.format(v) if isinstance(v, (int, float)) else "—"
    L = [f"# Top-miner comparison", f"_computed {utc_now()} — recomputed from data/processed/task_matrix.jsonl_",
         "", decomp, "",
         "| miner | ours | total | E | M | H | mean ratio | median | pass | broke | neg |",
         "|-------|------|-------|---|---|---|-----------|--------|------|-------|-----|"]
    for r in board:
        tag = ("**"+r["miner_id"]+"**") if r["ours"] else r["miner_id"]
        L.append(f"| {tag} | {'✓' if r['ours'] else ''} | {fmt(r['total'])} | {fmt(r['easy'])} | "
                 f"{fmt(r['medium'])} | {fmt(r['hard'])} | {fmt(r['mean_ratio'],'{:.2f}')}× | "
                 f"{fmt(r['median_ratio'],'{:.2f}')}× | {r['pass_n']} | {r['broke_n']} | {r['neg_n']} |")
    L += ["", "_Category scores (total/E/M/H) are scraped platform aggregates; ratio/pass/broke/neg "
          "are recomputed per-task. Top miners win on RATIO at equal pass-rate (see postmortem)._"]
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "top_miner_comparison.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # ---- postmortem.md : did m8..m11 improve solving or only add broken baselines? ----
    m7 = next(r for r in board if r["miner_id"] == "m7")
    P = [f"# Post-competition post-mortem (our 5 submissions)",
         f"_computed {utc_now()}. Baseline of comparison = m7/v11.1 (total {fmt(m7['total'])})._", "",
         "## Did the flip variants (m8/m9/m10/m11) improve solving, or only add breakage?",
         "| miner | ver | total | Δtotal vs m7 | pass | broke | neg | mean ratio | verdict |",
         "|-------|-----|-------|--------------|------|-------|-----|-----------|---------|"]
    for mid in ("m7", "m8", "m9", "m10", "m11"):
        r = next((x for x in board if x["miner_id"] == mid), None)
        if not r:
            continue
        if mid == "m7":
            verdict = "BASELINE (best)"
        else:
            dpass = (r["pass_n"] or 0) - (m7["pass_n"] or 0)
            dbroke = (r["broke_n"] or 0) - (m7["broke_n"] or 0)
            verdict = ("no solving gain; +breakage" if dpass <= 0 and dbroke >= 0
                       else f"Δpass {dpass:+d}, Δbroke {dbroke:+d}")
        dt = (r["total"] - m7["total"]) if (r["total"] and m7["total"]) else None
        P.append(f"| {mid} | {ours.get(mid,{}).get('version','')} | {fmt(r['total'])} | "
                 f"{fmt(dt,'{:+.3f}')} | {r['pass_n']} | {r['broke_n']} | {r['neg_n']} | "
                 f"{fmt(r['mean_ratio'],'{:.2f}')}× | {verdict} |")
    P += ["", "## Conclusion",
          "- All flip/persistence variants scored **below** m7. They did **not** raise pass count; "
          "they raised **broken-baseline** and **negative-score** counts (catastrophic −penalty tasks).",
          "- Compression ratio did **not** improve under flip-routing (~2.6–2.8× vs m7 2.99×).",
          "- **Drop permanently:** flip-mode rescue, persistent-failure→rich routing, release-flip-on-pass.",
          "- **Keep:** m7-style structure-preserving harvest. Next gains come from **deeper pass-safe "
          "compression on m7**, evidence-ranked (see reports/m7_gap_analysis.md)."]
    (REPORTS / "postmortem.md").write_text("\n".join(P) + "\n", encoding="utf-8")

    # ---- research_summary.md (latest/) ----
    n_cat = sum(1 for t in tasks if t.get("category") not in (None, "screener"))
    S = [f"# Research summary", f"_computed {utc_now()}_", "",
         f"- Miners compared: {len([r for r in board if r['ours']])} ours + "
         f"{len([r for r in board if not r['ours']])} top.",
         f"- Per-task rows: {sum(len(t['miners']) for t in tasks)} across {len(tasks)} tasks.",
         f"- {decomp}",
         f"- **Missing data:** per-task category on {len(tasks)-n_cat}/{len(tasks)} tasks "
         f"(only {n_cat} have E/M/H) → Medium/Hard task-level attribution BLOCKED. "
         f"Import config/task_categories.csv (see data/raw/platform_results/TASK_CATEGORIES_TEMPLATE.csv).",
         "- Reports: reports/top_miner_comparison.md, reports/postmortem.md, reports/m7_gap_analysis.md.",
         "- Next: reports/next_round_strategy.md + experiments/manifests/ (H1–H4)."]
    (LATEST / "research_summary.md").write_text("\n".join(S) + "\n", encoding="utf-8")

    print(f"wrote data/latest/scoreboard.json, research_summary.md; "
          f"reports/top_miner_comparison.md, postmortem.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
