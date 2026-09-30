# Evaluation: `social-media-report`

Status: **complete.** Description changed to candidate C below (a one-clause
patch to the original). Model under test: `claude-sonnet-5`, 10 runs per
query, isolated project root per run, user-level skills off
(`PROBE_SETTING_SOURCES=project`) with the 17 other synced skills copied in
as competitors (`PROBE_COMPETITORS`), since the account's synced copy of
this same skill would otherwise take its triggers.

## Headline

The original description never fired on anything it shouldn't (0 false
triggers across every run in this evaluation), but it under-fires on
requests that hand over exports and ask a question about the numbers
without asking for a report. The fix widens the last clause of the
description to cover those; it did not cost any precision.

| Candidate | Comparison set (14 q) | Positive runs triggered | Fresh positives* | Negative runs triggered |
|---|---|---|---|---|
| A: original | 11/14 | 49/90 | 32/40 | 0/50 |
| B: `run_loop` iteration-2 proposal | 13/14 | 72/90 | **40/40** | 0/50 |
| **C: targeted patch (adopted)** | 12/14 | 72/90 | **40/40** | 0/50 |

\* The four validation positives no candidate was written from, excluding
the Q3 query discussed below. Raw output:
`results/social-media-report/comparison.json`.

## What changed

Only the final clause. Original:

> ...or uploads platform analytics exports and asks to analyze, compare, or
> summarize the numbers — even if they don't say the word "report."

Now:

> ...or shares platform analytics exports (Facebook or Instagram Insights,
> TikTok, YouTube Studio) and asks any question about the numbers —
> comparing periods, checking whether a change is real, or finding what
> drove it — even if they don't say the word "report" and want a quick
> answer rather than a PDF.

The original is kept in `evals/social-media-report-original-description.txt`,
all three candidates in `evals/social-media-report-candidates.json`.

## Why C and not the loop's B

B and C tie on everything neither was written from: 40/40 on the fresh
positives and 0/50 on the fresh negatives. B's lead is on the four weak
train queries it was generated from (30/40 vs 27/40), almost all of it on
"compare these two facebook insights csvs and tell me if reach actually went
down or if it's just because february is shorter" (B 6/10, C 3/10) — and B
contains a near-paraphrase of that exact query ("like reach 'dropping'
because February is shorter"). B also rewrites the whole description and
adds a "Not for ..." list that mirrors the eval set's negatives item by
item. Both are the overfitting pattern the `g-app-script` and
`fable-5-logic` evaluations warn about. C is a smaller change with the same
held-out result.

If that one "is this drop real?" comparison matters most, B is the
alternative; it is in the candidates file, tested.

## How the evaluation went

1. **First loop run, empty project roots** (`run1-no-fixtures.log`): 41%
   recall train, 43% test. A captured transcript showed this was the harness:
   queries like "attached are facebook page exports..." ran in an empty
   directory, so the model looked for the files, found nothing, and asked for
   them instead of loading the skill. Stopped after iteration 1.
2. **Sample exports in every run** (`scripts/run_loop_with_fixtures.py`): the
   same query went from 0/10 to 4/4. The wrapper copies `evals/trigger-fixtures/`
   into each probe's project root and stops a turn once the skill is invoked,
   using the toolkit's own `_invoked_this_skill` (so a triggered turn does not
   go on to run the whole analysis). Toolkit files are not modified.
3. **Second loop run with fixtures** (`run2-fixtures-aborted.log`): iteration
   1 (original description) scored 71% recall train, 100% test, 100%
   precision. The org's monthly spend limit stopped it during iteration 2,
   after the loop had proposed B. (That proposal's `improve_iter_1.json` was
   not kept; B's text is in the log and the candidates file.)
4. **Head-to-head instead of a re-run** (`scripts/compare_descriptions.py`):
   the spend limit had hit twice, so rather than re-run three loop iterations
   (~720 probes), A, B and C were scored on the four weak train queries plus
   a new 10-query validation set (`evals/social-media-report-validation.json`)
   that no candidate saw. 420 probes. Hit the spend limit once more partway
   through C; the script saves per candidate, so C was re-scored alone.

## Known test artifacts (not description problems)

- **"produce the Q3 youtube channel report as a pdf"** scored A 1/10, B 2/10,
  C 5/10. Transcripts show why, twice over: first the three YouTube fixtures
  were byte-identical copies, and the model stopped to flag that; after
  `scripts/make_trigger_fixtures.py` made them distinct (recheck: A 2/10,
  B 3/10, C 5/10, `comparison-q3-recheck.json`), it flagged instead that the
  files cover Aug–Oct while Q3 is Jul–Sep, and asked which the user meant.
  That is the behavior the skill itself asks for ("if the period is
  ambiguous, ask"), and it holds all three candidates back equally.
- The head-to-head for A, B and C used the earlier, copied fixtures; only the
  Q3 recheck used the regenerated ones. The comparison is like for like.
- skill-creator's `parse_skill_md` strips a trailing `"` from unquoted
  descriptions, so the loop tested the original as ending `word "report.`
  rather than `word "report."`. Cosmetic; the head-to-head passed
  descriptions directly and is unaffected.

## Packaging note

`dist/social-media-report.skill` is built with skill-creator's
`package_skill.py`, which leaves out the skill's `evals/` folder (its test
prompts and fixture CSVs). The uploaded `.skill` included them. They are
still in `skills/social-media-report/evals/` on this branch.

## Where to pick this up

- The "is this change real or a calendar artifact?" question is still the
  weakest positive (C 3/10). If it matters, test a C variant that names the
  day-count case in general terms, rather than adopting B's paraphrase.
- For future runs: give fixture files months that match what each query
  names, or phrase queries to match the fixtures; the model correctly asks
  when they disagree, and that reads as "did not trigger".
- `run_loop_with_fixtures.py` (fixtures plus early stop) is general, not
  specific to this skill. If other skills take attached files, it may be worth
  moving the idea into `trigger_probe.py` on `main`.
