# Evaluation: `social-media-report`

Status: **complete.** Description changed to candidate C below (a one-clause
patch to the original); chart-axis bugs in the report template fixed after
the output evals (see "Output evals" below). Model under test: `claude-sonnet-5`, 10 runs per
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

## Output evals: the PDF reports themselves

The trigger work above only measures when the skill loads. Its own three
evals (`skills/social-media-report/evals/evals.json`) were then run end to
end: one real `claude -p` turn each (`claude-sonnet-5`, the updated skill in
`.claude/skills/`, fixtures in `uploads/`). Where the skill correctly stopped
to ask, a second turn gave the answers. PDFs and transcripts are in
`results/social-media-report/output-evals/`.

| Eval | Critical assertions | Other assertions | Result |
|---|---|---|---|
| 1. FB monthly, Visits column missing in Aug | 6/6 | 3/3 | 8-page PDF; Aug vs Jul vs Jun; Page Visits "Unavailable" for Aug; per-day beside every total; per-day reasoning for June's 30 days in a finding and a recommendation; full glossary; 17/17 internal links resolve; no ROI |
| 2. IG yearly, Apr/Jul/Sep missing* | 4/4 | n/a† | Month-by-month inventory shown and confirmed before computing; missing months "Unavailable" in the table and shaded gaps (no connecting lines) in every trend chart; totals labelled "6-mo total" |
| 3. TikTok, non-standard columns | 4/4 | 2/2 | Mapped Vid Plays/Hearts silently; asked specifically about Reposts vs Shares; flagged Engagement Score as unused; Shares "Unavailable", nothing fabricated |

\* The eval lists no files; it was given six generated Instagram months
(Jan, Feb, Mar, May, Jun, Aug) so the gap handling had something to act on.
† Its one non-critical assertion (carrying forward a prior PDF's
Unavailable markings) needs prior PDF reports as input, and none were given.

Every assertion passed. The runs did find real bugs in the template:

- **Chart y-axes collapsed to repeated labels.** `_fmt_value` chose decimals
  from each value's size, not the tick spacing: engagement rates of
  1.83–1.96 all read "1.9", interactions of 2.9K–4.1K all read "3K", and a
  single data point read "1.2M" five times. All three runs hit this. Eval 1
  and eval 2 each patched their own copy of the template differently, and eval 2's
  delivered PDF still has a "4K 4K 3K 3K" axis. Eval 3 dropped a chart
  to avoid it.
- **31 daily x labels overlapped.** The "rotate long label lists" branch
  set `rotation=0`, which does nothing.
- **Legend on top of the data** in a multi-series trend chart (eval 2).

Fixed in `skills/social-media-report/scripts/generate_report.py`: one unit
per axis and just enough decimals to separate adjacent ticks; flat or
single-point series get a real range; long label lists thin to about 10 ticks,
angled only when the labels are long; legend placed with `loc="best"`.
`scripts/check_report_axes.py` reproduces all four axis failures against
the original template and passes on the fixed one. The eval 1 and eval 3 report
data were re-rendered with the fixed template
(`output-evals/rerendered-with-fixed-template/`). Eval 2's data file was not
kept by its run.

### Second round: the remaining four

- **Charts exaggerated small changes.** Autoscaling stretched a +0.13pt rise
  on a 1.9% rate into a spike, and a −9% dip in views into a crash. Trend
  charts now keep a y-range of at least 30% of the top value, centred on
  the data, and any axis that does not start at zero says so above the plot
  ("Axis starts at 1.6, not zero"). The "data not supplied" note moved up
  there too, so neither note can cover a point.
- **Lowercase title.** Known platforms are printed under their own spelling
  (Facebook, Instagram, TikTok, YouTube) whatever case the data uses.
- **Near-empty pages.** The hard page breaks before Analysis and the Glossary
  are now conditional: a section starts on the same page when at least 3.5in
  is left. The Glossary is still the last section. Headings keep with the
  content after them, which fixes TikTok's "Derived measures" heading that
  had been stranded at the foot of a page. Re-renders: Facebook 8 → 7 pages,
  TikTok 7 → 6, every internal link still resolves.
- **The Facebook benchmark was mislabelled.** `benchmarks.md` called the ~0.15%
  Quid/Rival IQ figure "interactions ÷ reach". Rival IQ defines its rate as
  "all these interactions divided by total follower count". So eval 1
  compared a reach-based 1.96% with a follower-based 0.15% and called the
  account "well above" benchmark. The row is now labelled follower-based. A
  new "interactions ÷ reach: no sourced default" row and a note explain the
  mix-up. The 0.15% value itself was not re-verified, because Rival IQ publishes
  its figures as images. SKILL.md step 5 now requires a benchmark with the
  same denominator and no verdict across different ones. Benchmark charts take
  optional `account_basis` / `benchmark_basis` fields; on a mismatch the
  benchmark bar is drawn hollow and the chart reads "Different denominators:
  not a like-for-like comparison" (`facebook_2026-08_with-basis-fields.pdf`
  shows this on eval 1's data).

### Confirmation run, and one more template bug

Eval 1 was re-run end to end with the updated skill
(`output-evals/eval-1b-facebook-monthly-after-fixes/`). Every assertion still
passes (8 pages, 26/26 internal links resolve), and the new rules held in a real
run. The benchmark chart set `account_basis: reach` / `benchmark_basis:
followers`, the takeaway says the 1.96% "isn't comparable" to the 0.15%
follower-based default, and nothing in the report claims the account is above
benchmark. Its own PDF shows the axis notes and the title fix too.

That run found one more template bug. Two series on one chart (Views/day and
Reach/day; Photos and Reels) were drawn in the same blue. The Facebook theme
replaced only the first palette color with #1877F2, leaving the base #2563EB
second. The palette is now rebuilt for every report: brand colors first, then base
colors that are clearly distinct from those already chosen. It is no longer patched
in place, so one platform's colors cannot leak into the next build. The run's data
re-rendered with this fix is `page_facebook_2026-08_report_rerendered-palette-fix.pdf`.
`generate_report.py` also no longer leaves a `.chart_tmp/` folder next to every
report.

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
