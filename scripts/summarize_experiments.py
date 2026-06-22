#!/usr/bin/env python3
"""Aggregate experiments/runs/*/metrics.json into a backlog-status table.

Writes experiments/reports/summary.md and refreshes the status block at the top of
reports/experiment_backlog.md. Applies the decision gate verdict recorded per run.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ROOT, REPORTS, utc_now  # noqa: E402

RUNS = ROOT / "experiments" / "runs"
EREPORTS = ROOT / "experiments" / "reports"


def main() -> int:
    runs = []
    for mpath in sorted(RUNS.glob("*/metrics.json")):
        try:
            runs.append((mpath.parent.name, json.loads(mpath.read_text(encoding="utf-8"))))
        except Exception:
            continue

    L = [f"# Experiment summary", f"_computed {utc_now()} — {len(runs)} run(s)_", ""]
    if not runs:
        L.append("_No experiment runs yet. Create candidates in experiments/candidates/, then "
                 "`python scripts/run_experiment_matrix.py --manifest experiments/manifests/H1_*.yaml`._")
    else:
        L += ["| run | exp | cand status | base ratio | cand ratio | base broke | cand broke | gate |",
              "|-----|-----|-------------|-----------|-----------|-----------|-----------|------|"]
        for name, m in runs:
            b, c = m.get("baseline_m7", {}), m.get("candidate", {})
            L.append(f"| {name} | {m.get('experiment_id')} | {c.get('status','?')} | "
                     f"{b.get('avg_compression_ratio')}× | {c.get('avg_compression_ratio','—')}× | "
                     f"{b.get('broke_baseline')} | {c.get('broke_baseline','—')} | "
                     f"{'; '.join(m.get('gate', []))} |")
    EREPORTS.mkdir(parents=True, exist_ok=True)
    (EREPORTS / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # refresh a status block in experiment_backlog.md (between markers, if present)
    bl = REPORTS / "experiment_backlog.md"
    if bl.exists():
        txt = bl.read_text(encoding="utf-8")
        block = "<!--STATUS-->\n" + "\n".join(L) + "\n<!--/STATUS-->"
        import re
        if "<!--STATUS-->" in txt:
            txt = re.sub(r"<!--STATUS-->.*<!--/STATUS-->", block, txt, flags=re.S)
        else:
            txt = txt.rstrip() + "\n\n## Live status\n" + block + "\n"
        bl.write_text(txt, encoding="utf-8")
    print(f"wrote {EREPORTS/'summary.md'} ({len(runs)} runs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
