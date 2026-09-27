# ai-audit: evaluation

## The skill

`skills/ai-audit/` merges two sources into one skill:

- the `ai-tell-audit` bundle: `SKILL.md`, the tiered catalogue
  (`references/tells.md`), vocabulary by model era (`references/dated.md`),
  human markers not to flag (`references/human-signals.md`), and
  `scripts/fingerprints.py`, a regex scan for tool markup;
- a section-by-section summary of Wikipedia's *Signs of AI writing*, now
  `references/wikipedia-signs.md`. `SKILL.md` points to it for wiki content,
  edit summaries and review comments, whose tells only it covers.

The skill was renamed from `ai-tell-audit` to `ai-audit`. The two uploaded
copies of `SKILL.md` were identical.

## Trigger evaluation

Eval set: `evals/ai-audit-trigger-eval.json`, 20 queries (10 should trigger,
10 near-misses such as grammar-only proofreading, fiction dialogue, a
detector script, DOI checking, an AI-use policy). The loop splits it into
12 train and 8 held-out queries. 5 runs per query; counts below are runs.

| Description | Train | Held-out | False fires |
|---|---|---|---|
| Original | 54/60 | 35/40 | 0 |
| Iteration 2 (applied) | 57/60 | 35/40 | 0 |
| Iteration 3 | 60/60 | 35/40 | 0 |
| Applied, confirmation run | 59/60 | 35/40 | 0 |

The held-out scores tie, so the loop keeps iteration 2. Iteration 3 reached
60/60 by quoting the em-dash training query nearly verbatim, which is
overfitting. The gain is on training queries only. The clearest one is the
"I use em dashes a lot in my newsletter" query: 0/5 under the original,
2/5 and 4/5 in two runs of the applied description. That spread is also a
reminder of how noisy 5 runs per query is.

The one held-out miss for every description asks Claude to "look back at
the product announcement you wrote earlier in this chat". A fresh `claude -p`
session has no such draft, so the query is probably unfair and should be
rewritten with the draft pasted in, or dropped.

## Measurement problems and fixes

- **Spend limit scored as zeros.** The first run hit the org spend limit.
  Upstream `run_eval` records any failed run as "did not trigger", so every
  should-trigger query scored 0/10. `trigger_probe.py` now retries a failed
  run and then raises an exception that stops the pass. Logs of that run
  were discarded; `results/ai-audit/run1-original-desc.log` is the clean rerun.
- **Old copy of the skill competing.** `ai-tell-audit` was synced into the
  container from the account and re-created on each `claude` start, so
  moving it aside did not hold. Runs used `PROBE_SETTING_SOURCES=project`
  (no user-level skills) and `PROBE_COMPETITORS` pointing at a copy of the
  synced skills minus `ai-tell-audit`, so the model still had realistic
  alternatives.
- 5 runs per query rather than the recommended 10, to stay under the spend
  limit.

## Files

- `results/ai-audit/run1-original-desc.log`: iterations 1-2 until the spend
  limit stopped the second test pass.
- `results/ai-audit/run2-resumed.log`, `results.json`: resumed from
  iteration 2; picks the applied description.
- `results/ai-audit/run3-confirm.log`, `results-run3.json`: confirmation run.
- `dist/ai-audit.skill`: packaged skill with the applied description.
