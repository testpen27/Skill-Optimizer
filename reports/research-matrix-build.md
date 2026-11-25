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
