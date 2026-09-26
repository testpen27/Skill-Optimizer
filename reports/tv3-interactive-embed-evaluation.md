# Evaluation: `tv3-interactive-embed`

Method: skill-creator's description-optimization loop (`scripts/run_loop_resilient.py`,
which patches in the corrected trigger detector from `scripts/trigger_probe.py` —
see `reports/fable-5-logic-evaluation.md` on the `skill/fable-5-logic` branch for why the stock detector reports a
healthy skill as 0%). 4 iterations, 3 runs/query, 40% holdout, model
`claude-sonnet-5`, real `claude -p` turns end to end.

Eval set: `evals/tv3-interactive-embed-trigger-eval.json`, 31 queries — 18
positives spanning every embed shape the skill supports (quiz, calculator,
eligibility checker, timeline, restyle/fix, stripped scripts, reveal poll,
mini-game, slide deck/carousel, infographic, CDN-pull gate) in both Malay and
English, and 13 negatives that sound adjacent but are out of scope (generic
web dev, journalism writing, translation, PPTX decks, unrelated debugging).
Split 19 train / 12 test.

## Result: the original description is already the best one found

| Iteration | Train | Test | Description |
|---|---|---|---|
| **1 (original)** | **17/19** | **12/12** | unchanged |
| 2 | 14/19 | 11/12 | rewrite attempt |
| 3 | 18/19 | 11/12 | rewrite attempt |
| 4 (final) | 17/19 | 11/12 | rewrite attempt |

Every rewrite the loop proposed scored *worse* on the held-out test set than
the description you shipped with, even iteration 3, which improved the
in-sample (train) score to 18/19 by tuning wording the model had already seen
fail. That's the textbook overfitting signature the holdout split exists to
catch. **Recommendation: keep the original description as written.** No
change has been applied to `skills/tv3-interactive-embed/SKILL.md`.

## Aggregate numbers for the original description

Across all 31 queries (93 runs total):

- **Recall: 87% (47/54 positive runs triggered)**
- **False-fire rate: 0% (0/39 negative runs triggered)**

Precision is effectively perfect in this sample — nothing out-of-scope caused
a false trigger, including deliberately close negatives like "write a quiz
question bank in a spreadsheet" and "build me a React SPA quiz app... not
related to any news site or CMS."

## The two soft misses

1. `"add a BMI calculator widget to this health article, it needs to go
   straight into the WordPress Custom HTML block"` — 0-1/3 across iterations,
   despite literally containing "WordPress" and "Custom HTML block," both
   listed trigger words.
2. `"make a swipeable photo slide deck for the article, needs to be
   embed-friendly HTML I can paste into the CMS"` — 1/3 in most iterations
   (3/3 only in the iteration that then lost ground elsewhere).

Both are probabilistic misses, not hard failures — each has fired
successfully in some runs. The likely cause: a bare "calculator" or "slide
deck" request reads to the model as a generic dev task unless something
anchors it to *this specific* skill rather than to general web-dev
competence, even with the CMS/WordPress vocabulary present. No description
rewrite in this run fixed either one without trading away held-out accuracy
elsewhere, so this is a known, minor gap rather than something chased further
here.

## Where to pick this up

If these two patterns matter in practice (you actually ask for bare
"calculator" or "slide deck" requests without saying "TV3" or "embed"), the
safer fix is not another blind rewrite pass but a targeted one: add the two
literal failing phrasings as explicit examples in the description, then
re-run just those two queries at higher `runs-per-query` (8-10) to confirm
the change helps before trusting it — same lesson as the fable-5-logic
session: a number from one pass without holdout validation isn't trustworthy.

Full run artifacts: `results/tv3-interactive-embed/2026-09-24_054024/`
(`results.json` has every query/run, `report.html` is the interactive
skill-creator report, `logs/improve_iter_*.json` has each rewrite attempt's
full prompt/response).
