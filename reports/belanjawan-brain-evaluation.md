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

Train 11/12, test 7/8 (36 real runs total; 6 timed out at 90s -- upstream
`run_eval.py` silently records a timeout as "did not trigger" rather than
excluding it, a measurement gap fixed in the confirmation pass below).
Recall was perfect (6/6 and 3/3 positives all triggered 3/3), but it
over-fired on two negatives:

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

## Confirmation pass -- 10 runs/query, full 20-query set

The 7/8-vs-7/8 tie above was flagged as low-confidence (3 runs/query, 8-query
test set). Re-ran both candidates head to head with `scripts/powered_compare.py`
at 10 runs/query across all 20 queries (400 real `claude -p` turns total,
150s timeout, failed/timed-out runs retried up to twice rather than counted
as non-triggers). Full data: `results/belanjawan-run/powered-10runs/results.json`.

| | Original | Rewritten (applied) |
|---|---|---|
| Recall (10 positive queries x 10 runs) | 100/100 (100%) | 100/100 (100%) |
| False fires (10 negative queries x 10 runs, minus unrecoverable) | 14/93 (15.1%) | 7/95 (7.4%) |
| Unrecoverable timeouts | 7 | 5 |

**The rewrite is confirmed better, roughly halving the false-fire rate --
this was not noise.** Per-negative-query breakdown (triggers/runs):

| Query | Original | Rewritten |
|---|---|---|
| "what's actually in Budget 2026 for the average household..." | 9/10 | 1/10 |
| "explain in plain terms what STR and SARA cash aid are..." | 3/10 | 0/10 |
| "tax calculator for Singapore's Budget 2026..." | 2/10 | **6/10** |
| all 7 other negatives | 0/10 each | 0/10 each |

This sharpens, and partly revises, the iteration-2 analysis above: the
Budget-2026-summary false fire was far worse than the 3-run sample showed
(90% of runs, not "3/3 on a small sample" -- though that was already at
ceiling) and the rewrite's fix for it is real and large. But the Singapore
near-miss it trades in is also worse than the earlier 1/3-to-3/3 jump
suggested: it's a genuine 60% false-fire rate, not an edge case. Net effect
is still a clear win (14/93 -> 7/95 overall), but the Singapore-calculator
case is a real, sizeable remaining gap worth a follow-up description
iteration if that query pattern matters in practice -- e.g. explicitly
naming "Malaysia" / "Belanjawan" as the trigger condition rather than the
STR/SARA-style-calculator concept generally.

One harness note: the `"BrainBudget" B2B app` negative query timed out on
7/10 (original) and 5/10 (rewritten) runs even at 150s and produced 0/10
triggers on every run that did complete, on both descriptions. That looks
like the query itself being expensive to execute in the probe harness
(Claude doing more exploratory work before answering), not a triggering
signal -- it is not a false fire either way, just an unreliable data point
that needed a larger timeout budget or more retries than this run had.

## Caveat

Even 10 runs/query and 20 queries is still a modest sample by classical
standards, especially for the single most consequential remaining number
here (Singapore-calculator false-fire rate, n=10 -> n=16 after retries).
Treat directional conclusions (rewrite has fewer false fires, Singapore case
is a real gap) as solid; treat exact percentages as approximate.
