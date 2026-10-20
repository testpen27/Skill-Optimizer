# research-search-string

Two rounds of work. Round 2 (below first) redesigned the skill at the owner's
request; round 1 (after it) is the original robustness pass, kept as the record.

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
