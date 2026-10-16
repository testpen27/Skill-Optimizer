# search-string: robustness pass

Skill: `search-string` (Boolean search strings for Scopus, Web of Science and
Google Scholar). Input was the uploaded `search-string.skill`. Output is
`skills/search-string/` and `dist/search-string.skill`.

## Summary

| Area | Before | After |
|---|---|---|
| Script on bad input | Stack traces; silently emitted reversed years, empty `()` groups | One-line errors, exit 1; years swapped with a note |
| Syntax advice | Said never to put `*`/`?` in quoted phrases (wrong for Scopus and WoS) and that leading wildcards are rejected (wrong) | Corrected; plural and spelling handling inside phrases explained |
| Web of Science phrases | `"streaming service"` misses "streaming services" | Skill and checker steer to `"streaming service*"` |
| Pasted-string repair | Described, no tooling | `check` mode lints a pasted string |
| Local language | Label hard-coded to "Malay" | `local` + `localLanguage`; Word file labels the row correctly |
| Description trigger accuracy (26-query set) | 92% held-out, recall 84% | 100% held-out, recall 100% |

## 1. Syntax claims checked against the databases

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

## 2. Script hardening (`scripts/search_tool.js`)

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
`localLanguage` keys. `scripts/test_search_tool.py` holds 20 regression cases
and passes.

## 3. Behavior comparison (skill-creator workflow)

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

## 4. Description optimization

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

## 5. Interruptions

Three optimizer runs were cut off by account usage limits (the probe aborted
instead of recording zeros, as designed). `results/description-optimization-v2-aborted/`
holds the log of one. Later runs used 5 runs per query and 3 iterations to
fit the budget. Set 1 used 8 runs per query; set 2 used 5.

## Files

- `skills/search-string/`: the skill. `dist/search-string.skill`: package.
- `evals/trigger-eval.json`, `trigger-eval-v2.json`, `trigger-holdout.json`:
  trigger sets. `evals/evals.json`: behavior tasks and assertions.
  `evals/original-description.txt`, `optimized-description.txt`.
- `results/`: raw loop output, hold-out validation, behavior-comparison outputs.
- `scripts/test_search_tool.py`: regression tests for the script.
