.PHONY: collect detail runs reward normalize context status \
        import compare gaps experiments summarize research checkpoint
PY := python3
S  := scripts

# ===================== data collection (competition snapshots) =====================
# Immutable raw leaderboard snapshot (live; or: make collect IMPORT=file)
collect:
	@$(PY) $(S)/collect_dashboard.py $(if $(IMPORT),--import $(IMPORT),)

# Detailed per-task RSC SCRAPE (fallback; per-task aggregate only, NO per-run)
detail:
	@$(PY) $(S)/collect_miner_detail.py $(ARGS)

# CORRECT detailed source: keyless PER-RUN scrape via the dashboard server action.
# ARGS="--all" / "--hotkey HK ..." / "--limit N"
runs:
	@$(PY) $(S)/collect_runs.py $(ARGS)

# Legacy reward-element computation (completed comp)
reward: normalize
	@$(PY) $(S)/compute_reward_elements.py
normalize:
	@$(PY) $(S)/normalize_leaderboard.py

# ===================== post-competition research pipeline =====================
# Ingest leaderboard + per-task results into data/processed/ (IMPORT=file optional)
import:
	@$(PY) $(S)/import_dashboard_snapshot.py $(if $(IMPORT),--import $(IMPORT),)
	@$(PY) $(S)/import_platform_results.py $(if $(RESULTS),--import $(RESULTS),)
	@$(PY) $(S)/normalize_run_scores.py

# Build the per-task matrix + comparison reports (scoreboard, top-miner, postmortem)
compare:
	@$(PY) $(S)/normalize_task_scores.py
	@$(PY) $(S)/compare_miners.py

# Evidence sets: shared-pass headroom, barely-compressed, fragile + m7 gap analysis
gaps:
	@$(PY) $(S)/normalize_task_scores.py
	@$(PY) $(S)/find_shared_pass_gaps.py
	@$(PY) $(S)/find_fragile_tasks.py
	@$(PY) $(S)/estimate_score_lift.py
	@$(PY) $(S)/per_category_gap.py
	@$(PY) $(S)/compression_depth_risk.py

# Run all experiment manifests (BASELINE only unless RESULTS=file for a single one)
experiments:
	@for m in experiments/manifests/*.yaml; do echo "== $$m =="; \
	  $(PY) $(S)/run_experiment_matrix.py --manifest $$m $(if $(RESULTS),--results $(RESULTS),); done

summarize:
	@$(PY) $(S)/summarize_experiments.py

# Full research refresh in dependency order
research: import gaps compare summarize

# ===================== state =====================
checkpoint:
	@$(PY) $(S)/checkpoint_session.py --reason manual --note "$(NOTE)"

context:
	@$(PY) $(S)/context_for_claude.py

status:
	@echo "==== state/latest.md ====" && cat state/latest.md 2>/dev/null || echo "(none)"
	@echo "" && echo "==== data/latest/research_summary.md ====" && cat data/latest/research_summary.md 2>/dev/null || echo "(run make research)"
	@echo "" && echo "==== last checkpoint ====" && tail -n 1 sessions/index.jsonl 2>/dev/null || echo "(none)"
