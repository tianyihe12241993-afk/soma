# RISKS

- **Funding (HIGH):** m9/m10/m11 + KEY_D share one OpenRouter account with ~$28.59 left; 3 evals need ~$100+.
  Drain mid-eval → incomplete runs → low/zero scores. Mitigation: top up the account now (user action).
  (My validation runs on KEY_D depleted ~$47 of this account — use a separate testing key next cycle.)
- **m9/m10/m11 likely underperform m7** (flip-routing leaks Medium per v15 evidence; Hard gain unmeasurable).
  They may not beat our own m7 floor, and won't win any reward element.
- **No reward projected** under current standings (we lead no element; Medium leader 5Dk5CXJq at 1.557 >> our 1.421).
- **Scores are mid-eval / provisional** — the board can still shift through ~22 Jun. Re-collect to confirm.
- **Measurement reliability:** gold-patch proxy under-counts; local test-env broken; high run variance. Don't
  treat a single local run as signal.
- **Compliance:** coach must stay loop-detection + forced-stop ONLY (organizer ruling). m7/m8 passed review;
  keep any future coach within that bound (no workflow steering).
