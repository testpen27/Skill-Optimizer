---
name: research-matrix
description: Build an academic literature review matrix (LRM) from a set of scholarly papers the user already has or has found, with rows per paper and IMRAD-style columns, journal quartile, method and access, plus a short synthesis, delivered as a PDF. Use for literature review matrices, review matrices, synthesis matrices and concept matrices in academic research (thesis, dissertation, proposal, systematic or narrative review). Do not use for SWOT, competitor, marketing, product comparison, risk, decision or any other non-academic matrix.
---

# research-matrix

Status: **baseline (v0)**. This is the Literature Review Matrix part of
`pre-research`, extracted unchanged in behaviour so it can be improved on its
own. The new matrix design is agreed with the user before it is implemented;
see `reports/official-matrices.md` on this branch for the sources read.

## Scope

Academic literature review matrices only. If the request is a SWOT, a
competitor or marketing comparison, a risk matrix, a decision matrix or any
other kind of matrix, say it is outside this skill and stop.

Finding papers (search strings, PRISMA, downloads) is not part of this
skill. It starts from papers the user supplies: a list, DOIs, exports or
PDFs.

## How to work

Read `references/lrm-baseline.md` for the steps and `scripts/build_lrm.py`
for the `lrm.json` format and the PDF build.

Rules that hold in every cell:

- Never invent a number, quartile or result. Use "Not retrieved",
  "Not explicitly stated" or "Unranked/Unavailable".
- Every cell traces to something actually retrieved (a fetched page, a PDF,
  real metadata).
- Paraphrase; do not copy sentences.
- Show disagreements between sources instead of choosing silently.
- Stop at bot checks and paywalls; never use shadow libraries.
