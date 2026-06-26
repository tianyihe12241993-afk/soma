# Wide research: flips + pass-fail breaks lever (2026-06-24, user-directed)

User asked to focus on flipping + fixing pass-fail (run-variance) breaks, esp. Easy, and research widely for an
alternative even-slight improvement. Result: NO compliant lever exists — pass and fail runs are observably
indistinguishable.

## Behavioral lever (loop / forced-stop) — CLOSED
- Policy (reports/prompting_policy_and_compliance.md): force-stop is BANNED next round; loop-detection allowed
  but only the 2 fixed "repeated assistant/tool-call" strings, no steering, must not change successful behavior.
- m12 already implements both exact-repeat loop signals (LOOP_THRESHOLD=3, window=12).
- Forensics suggested fails = file-thrashing (13810: edit base.py 8x; 12039: read schema.py 6x) that m12's
  EXACT-arg match misses. BUT cross-run check KILLS a coarse trigger: PASS runs re-touch one file 8-14x (13810
  r3 read base.py 14x = PASS; 14122 r3 read compiler 14x = PASS; 12039 r4 write 11x = PASS) — MORE than fails
  (5-8x). So heavy iteration is normal winning behavior; a coarse loop trigger would fire on passes → disrupt
  successful runs (policy-violating + score-lowering). No discriminator exists.

## Flip lever — CLOSED
- Rich path (base-fail/hard tasks) already pins error/test/diff/path/signature via extractive_message.
- Convertible flips differ per-miner (sympy-14976: 5DtEz 3/5, king 0/5) = trajectory luck, not a stable property.
- 5 fail-fails (django-11333/13121, sympy-13757/19040/23413) solved by NOBODY = capability-bound.

## Root cause (final): pass/fail is decided by edit CORRECTNESS, not an observable signal
Same compressor, same window, same tool-use patterns — the only difference is whether the agent's edits are
right. That is qwen3-coder sampling/capability, which a compliant compression miner cannot observe-and-act-on
(can't steer, can't add attempts, context isn't missing). Easy's low 0.412 is the same sampling variance on
easy pass-pass tasks.

## Strategic answers to the user's two goals
1. Beat the king (0.780 vs 0.768): the 0.012 gap is window/sampling noise (we're tied on every controllable
   factor). Path to #1 = a favorable re-eval window (the king's #1 is partly luck), NOT a code change.
   Re-submitting m12 to a fresh hotkey is a legitimate variance gamble (could land better OR worse).
2. Future defense (STRONG): m12 Hard 0.919 is field-best by a mile; profile is penalty/gate/multiplier-robust
   (all categories positive, 43% savings margin). No rival beats M+H without collapsing elsewhere (king weak-H
   0.60, 5DAh dead-H -3.6, 5DtEz dead-M 0.50). Hold m12, monitor finalized rivals + the dormant
   llm-semantic-scoring branch. Portfolio (2nd-hotkey specialist) = only structural growth, blocked on the
   agent-stochasticity wall.

VERDICT: HOLD m12 (true ceiling). No compliant flip/pass-fail lever. Defense is solid via the M+H moat.
