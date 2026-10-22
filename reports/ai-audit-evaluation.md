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

## Version 2: explaining AI checker reports

### What changed

The skill now also helps a writer understand an AI checker's verdict, not
only whether their prose sounds machine-made. Added:

- `references/ai-checkers.md`: how Turnitin's detector works (sentence
  scores in context, qualifying text, the `*%` band for 1-19%, Turnitin's
  own false-positive figures, paraphraser and bypasser detection, the
  August 2026 merge into a single "AI-generated" category), how to read a
  report, how GPTZero differs, what can and cannot be said about why a
  sentence was flagged, and which revisions help versus what to avoid.
  Sourced from Turnitin's guides, FAQ, release notes and false-positive post
  (read October 2026), GPTZero's technology pages, and Liang et al. (2023).
- `scripts/checker_report.py`: splits a Turnitin AI Writing Report PDF into
  highlighted and unhighlighted prose sentences, excluding tables, headings,
  references and running headers. Self-test on a synthetic PDF.
- `SKILL.md`: a Checker mode, its workflow and output format, and two
  principles: a detector score is a different measurement from this audit,
  and the skill helps the writer, not the disguise (no humanizer tactics).
- Description: now covers detector results; excludes plagiarism and
  similarity reports. 1,005 characters.

### Grounding: one real report

Built from a Turnitin AI Writing Report a user shared (67% on a 3,500-word
postgraduate assignment). The PDF is not in this repo; an anonymised summary
is the worked case in `ai-checkers.md`. Findings that shaped the skill:

- Tables carried no highlights; full-sentence bullets were scored and
  mostly flagged.
- Highlights clustered on textbook definitions, signposting topic
  sentences, evenly built parallel bullets, recommendation openers and the
  generic conclusion. Unhighlighted prose clustered on the writer's own
  working with figures, their qualifications of sources, stated
  assumptions, and plain non-native phrasing.
- The tell catalogue did not predict the highlights: an unflagged sentence
  used a catalogue tell, while flagged definitions had none. This is why
  the skill now treats detector scores as a separate measurement.
- With tables excluded, flagged and unflagged sentences averaged the same
  length (about 20 words). An earlier count that included table text had
  suggested otherwise; the reference uses the corrected figure.

An end-to-end run (fresh `claude -p` session, only this skill installed,
the PDF and a plain "what does my Turnitin result mean" prompt) loaded the
skill, read `ai-checkers.md`, ran `checker_report.py`, and produced a
correct reading of the report, revision advice and the do-not list. It
promised no score.

### Trigger evaluation

The eval set gained five queries and one flip
(`evals/ai-audit-trigger-eval.json`; the previous set is kept as
`ai-audit-trigger-eval-v1.json`). The flip: "how do GPTZero and Turnitin's
detector work" was a should-not-trigger near-miss and is now in scope. New
near-misses: a plagiarism similarity score, and a script to bulk-download
reports.

Old and new descriptions on those six queries
(`evals/ai-audit-trigger-eval-checker-subset.json`), 5 runs each:

| Query | New | Old |
|---|---|---|
| Turnitin report PDF, "what does 67% mean" | 5/5 | 2/5 |
| GPTZero "mixed" on a personal statement | 5/5 | 5/5 |
| 45% on Turnitin after Grammarly, what to revise | 5/5 | 5/5 |
| How do GPTZero and Turnitin work (should trigger) | 0/5 | 0/5 |
| Turnitin similarity score (should not) | 0/5 | 0/5 |
| Bulk-download script (should not) | 0/5 | 0/5 |
| **Correct runs** | **25/30** | **22/30** |

The gain is on the core case, a user bringing an actual report. The general
"how do detectors work" question fires under neither description: Claude
answers such questions directly, and the `learn` skill covers explanations.
Left as is rather than tuned to one query.

Three earlier attempts at a full 25-query run stopped on the account's
session limit; the probe aborted each cleanly rather than recording zeros,
and none of those partial runs are reported here. Results:
`results/ai-audit/checker-v2/`.
