# pre-research

Three rounds of work on one skill. Round 3 (first below) merged it with the
owner's `find-paper` skill into `pre-research`. Rounds 2 and 1 are kept as the
record of how the search side was built.

## Round 3: merge with find-paper into pre-research (October 2026)

### Why

Both skills began the same way (find the papers relevant to a topic and field)
and then diverged: `find-paper` built a Literature Review Matrix from about 15
to 20 papers found by web search; `research-search-string` ran a full database
search and documented it. They competed for the same requests, duplicated the
Boolean keyword work and the search log, and contradicted each other on years
(fixed five years against asking).

### Shape

- **SKILL.md** (71 lines): the shared intake (field always asked, year ranges
  always asked, what the user wants at the end, where to save), a choice of
  quick or systematic search, a table routing to four branches, and the rules
  that hold everywhere.
- **Branches**, each in its own reference file read only when reached:
  strings (`references/strings.md`), conduct PRISMA (`references/prisma.md`),
  access and download (`references/access-download.md`), LRM
  (`references/lrm.md`). The searches themselves: `references/quick-search.md`
  (find-paper's method) and `references/systematic-search.md`.
- **One project folder** per topic holds every file, so the branches chain:
  PRISMA, then download the included papers, then an LRM of them.

### Decisions by the owner

- **Screening: the reviewer screens, Claude records.** `scripts/screening.py`
  shows records in batches or writes a spreadsheet, records each decision
  with its reason and date, refuses invented ids and decisions, requires a
  reason for full-text exclusions, and computes the PRISMA screening numbers,
  leaving any unfinished stage as "to be completed". The report states that
  every screening decision was the reviewer's.
- **Year ranges are always asked**, including for the LRM. find-paper's fixed
  five-year cutoff is gone.

### New script for the LRM

`scripts/build_lrm.py` replaces find-paper's write-it-yourself PDF step. It
scales the 11 columns to the landscape page so the table cannot run off the
edge (a failure find-paper's own notes warned about), wraps every cell,
refuses a quartile that is not Q1 to Q4 from a lookup (or the two allowed
labels), a method outside the four types, or an access label outside
Free/Paid/Unclear, and prints "Not retrieved" or "Not explicitly stated" for
empty cells. Rendered and checked by eye.

Corrected from find-paper on the way: `$` truncation does not work in Scopus
(it is Web of Science only).

### Testing

`scripts/test_pre_research.py`: 61 checks, all passing (the 46 from round 2
plus screening, the LRM builder, and a report built from a quick-search log).
The same limits as round 2 apply: no live browser, Scopus, Web of Science or
OpenAlex in this environment.

### Trigger accuracy

Eval set `evals/trigger-eval-v4.json`: 34 queries, 20 positive across all four
branches (strings, PRISMA, download, LRM, classifying papers the user already
has) and 14 near-miss negatives. `find-paper` was removed from the competitor
set because the owner will uninstall it. Model Sonnet 5.5, 5 runs per query.

| Description | Eval set (34) | Fresh hold-out (20) |
|---|---|---|
| Draft | 33/34 (classify-my-papers query 0.4; three positives at 0.6) | not run |
| Revised (adopted) | 34/34 (classify-my-papers 0.8; pasted-string queries 1.0) | 20/20, every positive 5/5, every negative 0/5 |

The revision was written by hand after seeing the draft's weak queries (the
optimizer stopped after one iteration because every training query passed),
so its 34/34 is in-sample; the 20-query hold-out, 6 of them new LRM and
near-miss queries, is the independent check. One query stays at 0.6: asking
for the search strategy "as a Word document", which the skill now delivers
as a PDF.

Results: `results/description-optimization-v4/`,
`results/description-v4-revision.json`, `results/holdout-validation-v4.json`.

### Model routing

At the owner's request every step has a planned model
(`references/model-routing.md`): helpers on `opus` for the search strings and
the LRM synthesis, `sonnet` for reading publisher terms, relevance tagging and
IMRAD extraction, `haiku` for running quick-search queries, finding free
copies and the quartile/method/access labels. Intake, browser searches and
screening stay in the session, which the owner is advised to run on Sonnet.
The plan is fixed: user requests to change a model are declined, and the only
change allowed is moving a step to a stronger model when its output is
clearly not good enough, after asking the user. On claude.ai on the web there
are no helpers, so every step runs on the model chosen in the chat. Trigger
accuracy is unaffected (the description did not change). The routing itself
has not been exercised: this environment has no Claude desktop app.

### Behaviour test (skill-creator, final check before publishing)

Three tasks, each run once with `pre-research` and once with the skill it
replaces, by independent subagents with no browser or database access
(`results/behavior-comparison-v2/`, viewer `review-iteration-1.html`):

| Task | pre-research | Old skill |
|---|---|---|
| Strings for an SLR, two year ranges (old: research-search-string) | 6/6 | 6/6 |
| Record the reviewer's screening and give PRISMA numbers (old: research-search-string) | 6/6 | 6/6 |
| LRM PDF from four supplied papers (old: find-paper) | 7/7 | 7/7 |

Time and tokens were the same within noise (96 s against 99 s a task, about
90k tokens each). The checks do not tell the versions apart: both followed
the honesty rules (no invented hit counts, quartiles or screening decisions).
Four apparent failures in the first grading pass were grader errors (a "Q1/Q2"
in the synthesis advice, a cell split across lines by the PDF extractor, a
flat screening record, the phrase "your decision") and were fixed in
`grade.py` before the final scores. What differed was how the work was done:
pre-research used its scripts (screening recorder, LRM builder) where the old
skills improvised, and it asked all nine intake questions even when the user
only wanted an LRM of papers they already had, which is a candidate fix.

**Iteration 2: intake fix.** The intake now asks only what the chosen job
needs (a table in SKILL.md maps each job to its questions; answers already
given are shown back, not asked again). A new check measures it. Rerun with
the fix: the LRM-of-own-papers task asked 3 questions (field, year range,
where to save) instead of 7 and scored 8/8; the strings task asked 5 instead
of 7, with none about databases or saving, and scored 7/7. The rerun also
showed the strings branch dropping "rural" from a title to stay at four
concepts, so `references/strings.md` now allows a fifth concept when the title
needs it. That last change has not been rerun.

The description optimizer, rerun on the 34-query set with the adopted
description, scored every run correct (105/105 train, 65/65 held-out runs)
and proposed no change (`results/description-optimization-v5/`).

### Before installing

Uninstall `search-string`, `research-search-string` and `find-paper` from the
account, or they will compete with `pre-research` for the same requests.

## Round 2: from string writer to documented search (October 2026)

### What the skill now does

1. Asks for the niche first: field, title, population, country or sector,
   one or more year ranges, review type, document types, database access,
   target size.
2. Builds broad, balanced and narrow strings for every year range
   (`search_tool.js strings`, `plan`).
3. Runs the Scopus and Web of Science strings in the built-in browser while
   the user watches, records each hit count read off the page, and stops at
   any bot check. Optional OpenAlex counts as a free cross-check, labelled
   approximate.
4. Imports the user's Scopus CSV and Web of Science exports, de-duplicates by
   DOI then title and year (`openalex.py import`).
5. Finds legal free copies: OpenAlex (which carries Unpaywall's data), then
   Firecrawl for repositories and author pages, and Scholar `[PDF]` links the
   user's own search showed.
6. Asks where to save: a folder on the user's computer or Downloads; in
   claude.ai on the web the files arrive as downloads.
7. Downloads only free copies (`retrieve.py`): obeys robots.txt, waits
   between requests to one site, keeps a file only if it is a complete PDF,
   asks before more than 50.
8. Paywalled papers follow the publisher's terms. Elsevier forbids automation,
   so the user clicks Download in a new tab; other publishers are checked
   first, and the user clicks unless the terms clearly allow automation.
   `retrieve.py adopt` files what the user downloads.
9. Builds a PDF report (`build_report.py`): search profile, concepts and
   tiers, every string with its hit count and how and when it was recorded, a
   PRISMA 2020 flow diagram, and the retrieved and not-retrieved papers.
   PRISMA numbers that are not known print as "to be completed".

The Word output was dropped in favour of the PDF report.

### Decisions and the evidence behind them

- **No automated paywalled downloads by default.** Elsevier's support page says
  "the use of automation is strictly prohibited" and its firewall blocks
  automated-looking traffic. UC Davis Library's policy lists "use of
  automation (robots, scraping, spiders, AI agents, etc.)" as a breach that
  can lead to "denying access to the entire campus". An earlier draft of this
  work cited a 2008 Universiti Malaya ScienceDirect suspension as an example;
  that suspension was for unpaid fees, not downloading, and was removed.
- **OpenAlex details** were taken from its help pages (October 2026): the
  title-abstract-keywords search, wildcards only in the exact search, 3
  letters before a wildcard, no leading wildcards, a 4 KB URL limit, and a
  shared daily budget without an API key.

### Testing

`scripts/test_research_search_string.py`: 46 checks, all passing. They cover
the string builder (tiers, ranges, plan rows, bad input), OpenAlex query
conversion and counting against a recorded response, Scopus CSV and Web of
Science plain-text import with de-duplication, downloads against a local web
server (good PDF, robots.txt block, landing page posing as a PDF, truncated
PDF, paywalled record, the 50-file cap), filing a user download, and the PDF
report including the PRISMA box text. The report was also rendered to images
and checked by eye.

Not tested, because this environment cannot reach them: the live OpenAlex API
(its network policy blocks it; the code was written against a real response
fetched through Firecrawl), real Scopus and Web of Science pages in a browser,
and the Firecrawl step for free copies, which is an instruction rather than a
script. The first real run should be watched.

### Trigger accuracy

Eval set `evals/trigger-eval-v3.json`: 30 queries, adding requests to run
searches, download free papers and build the PDF report, and near-misses for
a literature review matrix and writing the methodology. Competitors in every
run: `find-paper`, `deep-research`, `docx`, `xlsx`, `pdf`, `learn`, `docs`,
`ai-audit`, `firecrawl`, `built-in-browser`, `chrome-browser`. Model:
Sonnet 5.5, 5 runs per query.

| Description | Train (19) | Held-out (11) | Fresh hold-out (14) |
|---|---|---|---|
| Hand-written draft | 18/19 | 11/11 | 14/14 |
| Optimizer's revision (adopted) | 19/19 | 11/11 | 14/14 |

On the fresh hold-out the revision was firmer where the draft wavered (5/5
against 3/5 on "convert my Scopus search into Web of Science syntax", 5/5
against 4/5 on identical Scholar counts), with no false fires, including
"download these DOIs through my EZproxy login" and a business "PRISMA-style"
funnel. Results: `results/description-optimization-v3/`,
`results/holdout-validation-v3.json`.

Limits: the queries were written by the agent, not users, and not reviewed by
the owner; one model; a 14-query hold-out cannot detect a small error rate.
Several runs were cut off by account usage limits and rerun; the probe aborts
rather than recording zeros.

## Round 1: robustness pass

Skill: `research-search-string`, renamed from `search-string` (Boolean search strings for Scopus, Web of Science and
Google Scholar). Input was the uploaded `search-string.skill`. Output is
`skills/research-search-string/` and `dist/research-search-string.skill`.

### Summary

| Area | Before | After |
|---|---|---|
| Script on bad input | Stack traces; silently emitted reversed years, empty `()` groups | One-line errors, exit 1; years swapped with a note |
| Syntax advice | Said never to put `*`/`?` in quoted phrases (wrong for Scopus and WoS) and that leading wildcards are rejected (wrong) | Corrected; plural and spelling handling inside phrases explained |
| Web of Science phrases | `"streaming service"` misses "streaming services" | Skill and checker steer to `"streaming service*"` |
| Pasted-string repair | Described, no tooling | `check` mode lints a pasted string |
| Local language | Label hard-coded to "Malay" | `local` + `localLanguage`; Word file labels the row correctly |
| Description trigger accuracy (26-query set) | 92% held-out, recall 84% | 100% held-out, recall 100% |

### 1. Syntax claims checked against the databases

Sources: Scopus Support Center, UCL and LSU Scopus guides, Clarivate's Web of
Science search rules, DCU's Web of Science guide (all read October 2026).

Corrected claims:

- `*` and `?` are allowed inside quoted phrases in Scopus (loose phrases) and
  Web of Science. Only `$` is barred from quotes. The old rule produced
  phrases that Web of Science could not match in the plural.
- Wildcards at the start of a word are allowed in both databases when 3 or
  more characters follow. The old checker called them rejected.
- Web of Science switches lemmatization off inside quotes and with wildcards,
  so `"news organisation"` does not find "news organization" there.
- Web of Science operator precedence is NEAR, SAME, NOT, AND, OR, which is why
  the brackets the script generates matter.
- Only an All Fields search in Web of Science is limited (100 operators).

Not verified, so left out or marked: Scholar's hyphen behavior, and the
syntax of PubMed, IEEE, ProQuest and EBSCO. The skill now says so and tells
the user to adapt field tags, instead of inventing them.

### 2. Script hardening (`scripts/search_tool.js`)

Failures found by feeding it bad input, all now fixed: invalid JSON, missing
`concepts`, `terms` as a string, empty terms, non-string terms, non-numeric or
reversed years, missing file, unwritable output folder, missing `docx`
module (now a clear message that points to `npm install docx`).

New checks: curly quotes (converted in specs, flagged in pasted strings),
unbalanced quotes and brackets, empty brackets, dangling operators, operator
words inside a term, lower-case `and`/`or`, `$` outside Web of Science,
Scopus and Web of Science field codes in the wrong database, field codes in a
Scholar string, and a plural note for Web of Science phrases.

New `check` mode for strings the user pastes in. New `local` and
`localLanguage` keys. `scripts/test_research_search_string.py (then test_search_tool.py)` holds 20 regression cases
and passes.

### 3. Behavior comparison (skill-creator workflow)

Three realistic tasks, run once each with the new skill and once with the
original snapshot. Raw outputs: `results/behavior-comparison/iteration-1/`.
Assertions are in `evals/evals.json`; mechanical ones were graded by script.

| Task | New | Original |
|---|---|---|
| 1. Full build for a telemedicine SLR | All assertions met; 7 of 16 multi-word phrases wildcarded for plurals | All structural assertions met; 0 of 26 phrases wildcarded |
| 2. Repair a broken pasted Scopus string | Fixed curly quotes, `or`, `behavio?r` | Same fix |
| 3. Word file with an Indonesian string | Row labelled "Indonesian" | Row labelled "Malay" |

Reading: the new skill is not better at everything. Task 2 is a tie. The two
real differences are plural handling in task 1 and the label bug in task 3.
One run per task per version is a small sample; this shows the differences
exist, not how often they occur. Nobody ran the strings in Scopus or Web of
Science, so recall of the strings themselves is unmeasured.

### 4. Description optimization

Harness: `scripts/run_loop_resilient.py` with the corrected probe, real
`claude -p` turns, user-level skills excluded
(`PROBE_SETTING_SOURCES=project`), and nine realistic competitors copied in
(`find-paper`, `deep-research`, `docx`, `xlsx`, `pdf`, `learn`, `docs`,
`ai-audit`, `firecrawl`). Control passed first: a clear positive fired and a
clear negative did not.

**Set 1 (20 queries, 8 runs each).** The original description passed every
query (12/12 train, 8/8 held-out). The optimizer made no change. That
set had no hard near-misses, so a perfect score proved little.

**Set 2 (26 queries; six harder ones added).** Original: 95% train, 92%
held-out, 100% precision, recall 90% and 84%. Weak spots: a pasted invalid
query (rate 0.2) and "is this too long for Scholar" (0.2). The optimizer's
second proposal scored 100% on train and held-out (80/80 and 50/50
runs correct at 5 per query).

**Fresh hold-out (10 queries never seen by the optimizer, 5 runs each).**
Both descriptions scored 10/10. The new one was firmer on the hardest query
(5/5 against 3/5 for "convert my Scopus search to Web of Science") and had
no false fires (0/25 on negatives).

Adopted description (802 characters, quoted in YAML because it contains
colons): `evals/optimized-description.txt`. It adds the debug path (invalid
query, syntax error, zero results), field tags, and an explicit "not for
screening abstracts, general Boolean or SQL help, or finding specific
papers".

Limits: the eval queries were written by the same agent that ran the
optimizer, not by users; the eval sets were not reviewed by the skill's owner
(skill-creator's step 2 was skipped); runs are Sonnet 5.5 only; and a
one-in-ten fresh set cannot detect a 5% error rate.

### 5. Interruptions

Three optimizer runs were cut off by account usage limits (the probe aborted
instead of recording zeros, as designed). `results/description-optimization-v2-aborted/`
holds the log of one. Later runs used 5 runs per query and 3 iterations to
fit the budget. Set 1 used 8 runs per query; set 2 used 5.

### Files

- `skills/research-search-string/`: the skill. `dist/research-search-string.skill`: package.
- `evals/trigger-eval.json`, `trigger-eval-v2.json`, `trigger-holdout.json`:
  trigger sets. `evals/evals.json`: behavior tasks and assertions.
  `evals/original-description.txt`, `optimized-description.txt`.
- `results/`: raw loop output, hold-out validation, behavior-comparison outputs.
- `scripts/test_research_search_string.py (then test_search_tool.py)`: regression tests for the script.

### Rename

Renamed from `search-string` to `research-search-string` at the owner's request. The
evaluation above was run under the old name; files in `results/` keep the old
name because they are the raw record of those runs.
