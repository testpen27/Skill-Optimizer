# Evaluation: `belanjawan-brain`

Status: **complete.** `scripts/run_loop_resilient.py` (5 max iterations, 3
runs/query, 90s timeout, 60/40 train/test split) exited early at iteration 2
because the train set hit 12/12. Full run data:
`results/belanjawan-run/2026-09-25_063307/results.json`.

## Eval set

20 queries (`evals/trigger-eval-belanjawan.json`), 10 should-trigger / 10
should-not-trigger, split 12 train / 8 test. The negatives were built as
near-misses on purpose: a same-domain calculator for Singapore's budget
instead of Malaysia's, a plain "what's in Budget 2026" summary question with
no code involved, a same-named `BrainBudget` app that shares no logic, a PDF
table-extraction task on the actual budget speech, etc.

## Iteration 1 -- original description

Train 11/12, test 7/8 (36 real runs total, 6 timed out at 90s and were
retried by the eval loop, not counted as failures). Recall was perfect
(6/6 and 3/3 positives all triggered 3/3), but it over-fired on two negatives:

- `"what's actually in Budget 2026 for the average Malaysian household? ..."`
  -- triggered 3/3, should not have. A pure content question, no code/build
  intent.
- `"can you just explain in plain terms what STR and SARA cash aid are ..."`
  -- triggered 2/3.

## Iteration 2 -- rewritten description

Train 12/12 (all pass), test 7/8. The rewrite fixed both iteration-1 false
fires (the Budget-2026-summary question now triggers 0/3, the STR/SARA
explainer 0/3) by adding an explicit negative clause: "Do NOT trigger for
someone just asking what's in Budget 2026 ... that's a content question, not
a tool-building one." It introduced one new false fire in exchange:

- `"I need a tax calculator for Singapore's Budget 2026 announcement ..."`
  -- went from 1/3 (iteration 1) to 3/3 (iteration 2). This is a genuinely
  hard near-miss: same STR/SARA-style benefits-calculator concept, wrong
  country, and the rewrite's "Trigger when the user wants to touch this
  engine's code" framing reads as covering "build me a similar calculator"
  even for a different country's budget.

Because both iterations score 7/8 on the 8-query test set, `run_loop`'s
tie-break (`max()` on test score, first match wins) reported iteration 1
(the *original* description) as `best_description`. That is an artifact of
the tie, not a signal that the original is actually better -- iteration 2's
train score is a full 36/36 correct across both positives and negatives
combined, against iteration 1's 34/36, and it removes two failure modes
(a generic policy question, an explainer question) that are far more likely
in practice than the Singapore-budget edge case it introduces.

## Decision

Applied iteration 2's description to `skills/belanjawan-brain/SKILL.md`. It
adds a `Do NOT trigger` clause the original lacked and tightens the "when to
use" framing around touching the engine's code/files rather than the topic
of Malaysian budgets generally. The Singapore-calculator false fire is a
known remaining gap -- worth another eval round if it turns out to matter in
practice, but not worth reverting to a description with two worse, more
common failure modes over it.

## Caveat

8-query held-out test sets at 3 runs/query are small; per the fable-5-logic
report, borderline queries can flip on sample noise alone. Treat the "7/8
either way" tie as low-confidence, not as proof the two descriptions are
truly equivalent.
