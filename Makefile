.PHONY: collect reward checkpoint context status normalize
PY := python3
S  := scripts

# Collect an immutable raw dashboard snapshot (live fetch; or: make collect IMPORT=file)
collect:
	@$(PY) $(S)/collect_dashboard.py $(if $(IMPORT),--import $(IMPORT),)

# Normalize raw -> processed, then compute the 7 reward elements + projection report
reward: normalize
	@$(PY) $(S)/compute_reward_elements.py

normalize:
	@$(PY) $(S)/normalize_leaderboard.py

# Save a checkpoint:  make checkpoint NOTE="what changed"
checkpoint:
	@$(PY) $(S)/checkpoint_session.py --reason manual --note "$(NOTE)"

# Print the compact context block (what Claude should read at start/resume)
context:
	@$(PY) $(S)/context_for_claude.py

# Quick human status: latest pointer + reward projection + last checkpoint
status:
	@echo "==== state/latest.md ====" && cat state/latest.md 2>/dev/null || echo "(none)"
	@echo "" && echo "==== reports/reward_projection.md ====" && cat reports/reward_projection.md 2>/dev/null || echo "(run make reward)"
	@echo "" && echo "==== last checkpoint ====" && tail -n 1 sessions/index.jsonl 2>/dev/null || echo "(none)"
