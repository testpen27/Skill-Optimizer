# research-matrix: build notes

Decisions agreed with the user (2026-11-23), after reading the official matrices
in `official-matrices.md`:

- One matrix per request. The LRM is the default and main job. Synthesis and
  concept matrices are built only when asked for by name.
- LRM columns, left to right: Code, Type, Authors, Title, Introduction,
  Methodology, Theory, Results, Discussion, Quartile, Access. Rows sorted A-Z by
  first author and coded P01.. after sorting.
- Authors and title in APA 7. Citations checked against Crossref. Quartiles
  from Scimago (SJR) only, with the year and subject area stated. Crossref has
  no quartile data; it supplies the ISSN used to find the journal on Scimago.
- Cells are written about the paper in the third person with varied subjects
  ("the authors", "the researchers", "the study"), no first person, no page
  numbers except for short direct quotes.

Assumptions to confirm with the user:

- "Type" is read as the study type (Quantitative / Qualitative / Mixed-methods /
  Theoretical/Review).
- Access (Free / Paid / Unclear) sits after Quartile, because the user asked for
  Quartile to be last of the content columns and wanted Access kept.
- The quartile uses the paper's publication year, not the current year.

Verified in the build session:

- Crossref and Scimago are blocked from the sandbox's own network but readable
  through Firecrawl; the scripts accept saved responses (`--offline`,
  `--journal-page`).
- Crossref check against the real record for 10.1177/0002764213479369 passes;
  with a misspelled surname, wrong year and wrong pages it reports all three.
  The SJSU handout itself misspells this author as "Tufecki".
- The Scimago parser reads the real journal page for ISSN 0002-7642: Q1 in
  Cultural Studies, Q2 in Education for 2013.
- All three matrices were rebuilt as Excel sheets (PDF output removed at the
  user's request), recalculated with the xlsx skill's recalc.py (18 formulas,
  0 errors) and rendered through LibreOffice and looked at.

Not yet done:

- The trigger eval set (`evals/trigger-eval.json`, 14 positive, 16 negative)
  has not been run, so the description has not been optimized.
- No full-text paper has been run through the whole workflow with the user's
  own papers.

## Update 2026-11-23 (second round)

- Output is now one Excel workbook per project (Summary, LRM, then Synthesis
  matrix or Concept matrix on request). The PDF builders and reportlab are gone.
- Retraction flag added to crossref_check.py. Correction to an earlier note:
  Crossref puts the notices in `updated-by` on the paper's own record
  (`update-to` is the field on the notice's record). Tested on the real record
  of the Lancet 1998 paper: a 2004 correction and a 2010 retraction, both from
  Retraction Watch, and a "RETRACTED:" title prefix, which the title comparison
  now ignores.
- Cell hyperlinks flatten rich text in LibreOffice, so the DOI is plain text.
- TCCM attribution corrected: Paul and Rosado-Serrano (2019, International
  Marketing Review) define it as a framework for the research-agenda part of a
  review (theory, context, characteristics, methodology). Paul and Criado
  (2020) only describe it as one example of a framework-based review.

Proposed, not built (awaiting the user's decision): gap map, quality appraisal,
TCCM, scoping-review charting, PICO.

## Test round 2026-11-24/25 (Opus 5.5)

### Independent review
An Opus 5.5 reviewer read the whole skill and reported 11 defects. Six were
reproduced directly, the rest by the regression tests; all 11 are fixed:

1. Synthesis/concept content was keyed by P-code, which renumbers when papers
   change, so text could land on the wrong paper. Now keyed by `id` or DOI;
   rebuilding the LRM warns that those sheets need rebuilding.
2. Text starting with `=` became a live Excel formula. Now forced to text.
3. PDF control characters passed `--check` and then crashed the build. Now
   stripped on load.
4. A concept-matrix paper missing from the LRM was dropped silently (a false
   gap); duplicate concepts were accepted. Both now rejected.
5. The first-person warning missed "We", "Our" and flagged "Phase I". Fixed.
6. Crossref JATS tags and HTML entities caused permanent mismatches and were
   copied into lrm.json by `--apply`. Now stripped.
7. Hyphenated initials (J.-P.) were split. Fixed; bare Crossref initials
   ("AJ") now give "A. J.".
8. DOI prefixes such as `doi.org/` and DOI case broke offline lookups. Fixed.
9. A-Z order ignored initials and put n.d. last; same-author same-year works
   had no a/b suffix. Now APA 7 order with suffixes.
10. Scimago fell back to an older year when a journal had left the user's
    category. Now reports Unranked/Unavailable.
11. A synthesis source without a code crashed with a traceback. Now a clear error.

Also fixed while testing: the rewritten description contained ": ", which is
invalid YAML in an unquoted value; the packager caught it.

`scripts/research_matrix_tests.py`: 29/29 checks pass.

### Trigger test
Probe model claude-opus-5-5, 5 runs per query, competing skills installed
(pre-research, xlsx, docx, pdf, deep-research). Scored with
`scripts/score_trigger_parts.py`; raw results in `results/`.

| Part | Queries | Runs correct |
|---|---|---|
| LRM (should trigger) | 10/10 | 50/50 (100%) |
| Synthesis matrix (should trigger) | 5/5 | 25/25 (100%) |
| Concept matrix (should trigger) | 5/5 | 25/25 (100%) |
| Non-academic matrices (should not) | 10/10 | 50/50 (100%) |
| Adjacent academic jobs (should not) | 7/7 | 35/35 (100%) |

Notes:
- Control run first: an "always use" description triggered 3/4 with no
  competitors, so the harness works. With pre-research installed the same
  control lost to pre-research, which also claims LRMs; the final description
  wins all LRM runs against it.
- Several passes aborted on the account's 5-hour usage limit; the harness
  records nothing for an aborted pass, so the parts were run as separate
  batches. One adjacent-job query ran past 240 s (another skill doing real
  work); that batch was re-run with a 600 s timeout.
- 5 runs per query rather than the README's 10, to stay inside the usage
  limit. All 185 runs went the right way.
- Isolated check (no competing skills, so nothing else could take the job):
  adjacent academic jobs 7/7 queries, 35/35 runs not triggered (100%).
  Results in `results/2026-11-25-isolated-opus-5-5/`.

## Cost model, first version (2026-11-26) - SUPERSEDED by the measured version below

`scripts/helper_cost_model.py`, output in `results/2026-11-26-cost-model/`.
Anthropic list prices per million tokens (cached 2026-11-03): Haiku 5.5
$0.10/$0.50 (over 100K prompt tokens $0.50/$2.50), Sonnet 5.5 $2/$10, Opus 5.5
$4/$20, Fable 5.2 $8/$40; cache reads $0.10 / $0.20 / $0.20 for the last
three. ASSUMED, not measured: Haiku cache reads at 5% of input, cache writes
at 1.25x input, a 12,000-token paper (8,000 and 25,000 also run), 3,000 output
tokens per paper while reading, 5,000 tokens of fixed overhead per helper,
3 papers per reading helper, 10 per verifier. The skill's own instructions
measure about 6,600 tokens.

Findings (12,000-token papers, chat on the model shown):

| Chat on | Reading helpers vs reading in the chat |
|---|---|
| Opus / Fable | cheaper from the first paper (36 percent at 3 papers, 45 percent at 20 with Opus) |
| Sonnet | within a few percent up to 3 papers; cheaper from 4; about 23 percent cheaper at 20 |
| Haiku | never cheaper |

Against running the whole job on one model with no helpers: helpers (Sonnet
reads, Opus checks and synthesises) cost less than Opus-only from 1 paper and
less than Sonnet-only from about 17 papers (9 for 25,000-token papers); they
cost more than Haiku-only always. The Sonnet-only comparison buys the
independent Opus check, so the extra cost is for quality, not waste.
A typical 4-10 paper job costs roughly $0.60 to $1.25 with helpers.
To replace the estimates with measurements, run one real job both ways and
compare `usage` totals.

## Reading helper comparison: Haiku 5.5 vs Sonnet 5.5 (2026-11-26)

Raw outputs, prompts and per-run costs: `results/2026-11-26-reading-comparison/`.

Papers (open access, full text): PMC11984724 (10.1371/journal.pdig.0000617,
quasi-experiment, rural India), 10.3389/fpsyg.2026.1934152 (quasi-experiment,
problematic internet use), 10.1007/s10798-021-09659-5 (phenomenological
interviews), 10.3390/ejihpe14090162 (mixed methods). 18,000 to 22,000 tokens
each, not the 12,000 first assumed. Each model read each paper once (4 papers,
one run each) with the skill's Reading and Writing rules, through `claude -p`.

### Measured cost (billed, one paper per run)
| | Haiku 5.5 | Sonnet 5.5 |
|---|---|---|
| Cost per paper | $0.018 (0.015 to 0.021) | $0.196 (0.175 to 0.210) |
| Time per paper | 72 s | 22 s |
| Output tokens (incl. reasoning) | 18,461 | 3,362 |
Sonnet cost 10.8 times as much. Haiku writes five times the output but at a
twentieth of the price, and takes about three times as long.

### Accuracy
| | Haiku | Sonnet |
|---|---|---|
| Blind Opus grader: claims supported (of all claims audited) | 90 of 91 | 98 of 98 |
| Added / strengthened / wrong claims | 0 / 0 / 0 | 0 / 0 / 0 |
| `check_evidence.py` errors | 1 (two numbers in a cell, in the paper's table, not in its quotes) | 0 (1 warning: hedge) |
| Numbers in cells that appear nowhere in the paper | 0 of 69 | 0 of 61 |
| Key findings covered (grader's 5 per paper) | 15 of 20 | 16 of 20 |
| Study type correct / theory correct | 4 of 4 / 4 of 4 | 4 of 4 / 3 of 4 |
| Overclaims: abstract sentence found, body passage that shows the gap paired with it (my reading of 5 real cases) | 2 clean, 2 right abstract but wrong body quote, 1 missed | 4 clean, 1 missed |

Both missed the same real overclaim (abstract says several outcomes increased,
the body says some were not significant at midline). Sonnet left one theory cell
empty where the paper names its guiding framework; Haiku named it.

### Reading of the results
- Faithfulness: no difference measurable on this sample. Zero added,
  strengthened or wrong claims in about 90 claims each means the error rate is
  below about 3 percent per claim (rule of three, 95 percent) for both; the
  sample cannot separate the models below that.
- Haiku's weak spot was pairing an abstract overclaim with the body text that
  actually contradicts it. The Opus verifier would cut such a flag, which turns
  it into a silently missed overclaim, not a wrong yellow flag.
- Limits: 4 papers, one run each, one judge (Opus) that I spot-checked against
  the paper text, education and social-science papers only. The overclaim
  difference rests on 5 real cases.

### Corrected cost model
Calibration against the 8 measured runs gave two corrections: cache writes cost
2 times the input price (not 1.25), and Haiku cache reads cost $0.01 per million.
The model now reproduces the measured per-paper cost to -4 percent (Haiku) and
0 percent (Sonnet). With 20,000-token papers and 17,000 tokens of helper
overhead (measured), Opus checking and synthesising in every plan:

| Papers | Chat reads (Sonnet chat) | Chat reads (Opus chat) | Sonnet helpers | Haiku helpers |
|---|---|---|---|---|
| 4 | $1.16 | $1.85 | $1.22 | $0.64 |
| 8 | $1.99 | $3.35 | $1.95 | $0.85 |
| 20 | $5.11 | $9.02 | $4.39 | $1.66 |
(cautious case: the helper start-up billed in full. If later helpers share the
cached system prompt, Sonnet helpers are cheaper than reading in the chat from
the first paper, e.g. $1.49 vs $1.72 for 8 papers, and Haiku helpers cost $0.58.)

So: Haiku helpers cut a whole job's cost by 45 to 70 percent against Sonnet
helpers (8 papers: $0.85 vs $1.95), because reading is most of the spend and
the Opus verification is a fixed cost. Sonnet helpers beat the chat reading for
itself from the first paper on an Opus or Fable chat, and from about 6 papers
on a Sonnet chat. The experiment itself cost about $2.6 (readers $0.85, Opus
grading $1.73).

Open decision for the user: keep Sonnet as the reading helper (current), or
switch to Haiku. See the chat summary for the recommendation.

## Overclaim pipeline D and a test of the verification step (2026-11-26)

Raw prompts, outputs and per-run costs:
`results/2026-11-26-overclaim-pipeline-and-verifier-test/`. Same four papers.

### Pipeline D: Haiku reads with exhaustive quoting, Sonnet pairs overclaims from quotes only
Stage 1 (Haiku, measured): reads the paper, writes the cells and also quotes
every abstract claim and every caveat, null result or scope restriction:
$0.021 to $0.032 per paper (mean $0.026), 89 to 173 s. Its cells: 0
`check_evidence.py` errors, 2 warnings, 0 of 50 numbers missing from the paper.
Stage 2 (Sonnet, measured): given only those quotes (never the paper), pairs
each abstract claim with the body quote that shows the gap: $0.041 to $0.056
per paper (mean $0.045), 5 to 12 s. D total $0.072 per paper before
verification, against $0.196 for Sonnet reading the whole paper.

Overclaims, against the 5 real cases the blind grader found (3 India, 2 tpack):
| | Real cases | Extra flags |
|---|---|---|
| Haiku alone | 2 clean, 2 wrong body pairing, 1 missed | |
| Sonnet reading the paper | 4 clean, 1 missed | |
| D | 3 flagged correctly (all 3 India, including the one both earlier runs missed); the 2 tpack cases were listed as "unsettled" (Haiku had quoted the right passages, Sonnet declined to pair them) | 2 further India discrepancies that are real (abstract says 8 blocks, body 6 intervention blocks; "bridge economic gaps" vs "could not verify"), and 3 doubtful flags on papers where the grader found none (piu 2 where the abstract already hedges, brink 1 "differ" vs "may differ") |
Sonnet once answered, then wrote "Correction: that entry is invalid" and a
second JSON object: parse the last valid object, not the first.

### Does the verification step miss things? Planted-error test
20 errors planted into the Sonnet cells (5 per paper: added property or
setting, changed number, strengthened claim, theory not the paper's, widened
scope), 50 untouched sentences. Verifiers saw only the quotes and the
sentences, as in the skill.
| Setup | Planted caught | Untouched sentences flagged | Cost per paper |
|---|---|---|---|
| Free script (`check_evidence.py`) | 9 of 20 (numbers, causal wording, unquoted theory) | n/a | 0 |
| Sonnet verifier | 20 of 20 | 14 of 50 | $0.056 |
| Opus verifier | 20 of 20 | 10 of 50 | $0.122 |
| Sonnet verifier, then Opus challenges it | 20 of 20 | 11 of 50 | $0.171 |
All three model setups caught every planted error, so recall cannot be
separated on blatant errors (20 of 20 means at least about 86 percent with
95 percent confidence). The planted errors were obvious by design; subtler ones
might separate them.
Flags on untouched sentences are mostly quote-coverage gaps: the content is
true to the paper but no quote backs it (checked: tpack "paired t-tests" is in
the paper's methods; piu wait-list PIU decrease is true). One was a real find:
the challenger flagged India's "Computational thinking ... p 0.38" because
0.38 belongs only to the knowledge aspect of computational thinking (the
midline result was significant, p = 0.03). Neither the Opus verifier nor the
blind full-paper grader had flagged it. The challenger also overturned 5 of
Sonnet's flags and added 3 new ones.

Not measured: the cells of pipeline D were not re-graded claim by claim, only
script-checked; the verification costs are single-paper runs dominated by helper
start-up, so batches of 10 cost much less per paper; one run per setup.

## Pipeline D built into the skill; when helpers pay off (2026-11-26)

Approved by the user. Added: `references/overclaim-pairing.md` (the Sonnet pairing
prompt), `scripts/apply_overclaims.py`, the exhaustive `abstract_claims` and
`caveats` quote lists in `reading-and-writing.md`, new routing in
`model-routing.md`, a Summary-sheet column for abstract-vs-body notes, and
`check_evidence.py` now also verifies those two lists (body caveats back a
cell's numbers; the abstract's claims never do). 50 of 50 tests pass.

The pairing helper now also returns `cell_sentence_id`, so the workbook knows
which sentence to colour (`split_sentences` in `common.py`). Tested on the four
papers (`results/.../pipeline_D/stage2_v2/`, $0.049 per paper): it flagged all 5
real overclaims the grader had found (the first version found 3 and listed the
other 2 as unsettled), plus real extra discrepancies, and about 5 of 14 flags
were doubtful (an abstract that already hedges). Fed through
`apply_overclaims.py` and `build_lrm.py`: 13 flags placed, 0 dropped (every
quote verified in the paper text), 5 unsettled claims and 1 unplaced pair on the
Summary sheet.

### When reading helpers pay off, pipeline D
Cost model extended (`helpers_D`, `chat_reads`), calibrated: stage 1 predicted
$0.0257 vs measured $0.0263; stage 2 predicted $0.0367 vs measured $0.0455
(-19 percent, which flatters helpers by about $0.01 per paper, small against
the gaps below). Chat on Sonnet, 20,000-token papers, helper start-up billed in
full (cautious), Opus verification and synthesis in both:
| Papers | Chat reads | Pipeline D helpers |
|---|---|---|
| 1 | $0.60 | $0.59 |
| 2 | $0.79 | $0.68 |
| 4 | $1.20 | $0.96 |
| 8 | $2.06 | $1.43 |
| 20 | $5.31 | $3.06 |
A chat on Opus or Fable saves more. The break-even is 1 paper (a tie), so the
rule is: 1 paper, the chat reads and checks overclaims itself; 2 or more,
helpers. This supersedes the earlier "6 papers on a Sonnet chat" rule, which
assumed Sonnet reading helpers.

A chat set to Haiku reading the papers itself: $0.02 (1 paper) to $0.67 (8
papers), cheaper than helpers up to about 9 papers, because Haiku is the
cheapest model; its context passes 100,000 tokens at about 5 papers, where
Haiku's price rises fivefold. Not recommended: the whole conversation and the
instruction-following would run on Haiku (untested), and the check would not be
independent.
