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
