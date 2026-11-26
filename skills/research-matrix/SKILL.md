---
name: research-matrix
description: Build an academic literature review matrix (LRM, review matrix, literature matrix, RRL or IMRAD table) in Excel from scholarly papers the user already has, with one row per paper and an APA 7 citation checked against Crossref (retractions flagged), introduction, methodology, theory, results, discussion and Scimago (SJR) journal quartile, sorted A-Z. Also tabulates the user's papers by quartile or method. Builds a synthesis matrix (themes by sources) or a Webster and Watson concept matrix only when the user asks for that exact matrix. Not for finding papers (search strings, PRISMA, database searches, downloads), writing the review chapter, summarising one paper or formatting references; never for SWOT, competitor, risk, decision or other non-academic matrices.
---

# research-matrix

Builds one academic matrix per request, as a sheet in an Excel workbook, from
papers the user supplies (a list, DOIs, an export or PDFs). Finding the papers
is a different job (search strings, PRISMA, downloads); say so if asked.

## Which matrix

| The user asks for | Build | Read |
|---|---|---|
| A literature review matrix, review matrix, literature matrix, "LRM", or just "a matrix" for their papers | **LRM** (the default and the main job) | `references/lrm.md` |
| A **synthesis matrix** | Synthesis matrix, themes by sources | `references/synthesis-matrix.md` |
| A **concept matrix** | Concept matrix, papers by concepts | `references/concept-matrix.md` |

- One matrix per request. Never build the synthesis or concept matrix unless
  the user asks for it by name; offer it in one line after the LRM at most.
- Synthesis and concept matrices reuse the LRM's paper codes (P01, P02, ...),
  so build or load the LRM first when both are wanted. They are added as
  extra sheets to the same workbook, never as separate files.
- Give every paper in `lrm.json` a short stable `id` (for example `tufekci2013`)
  and key synthesis and concept content by that `id` or the DOI, **never by a
  P-code**: the codes renumber whenever a paper is added or removed, and
  content keyed by a code would silently move to a different paper. If the LRM
  is rebuilt after the paper list changes, rebuild the synthesis and concept
  sheets from their JSON too.
- Anything that is not academic literature review work (SWOT, competitor or
  marketing comparison, risk, decision, feature or pricing matrices): say it
  is outside this skill and stop.

## Before you start

Say in one line what you understood. Ask only what blocks you, in one short
message: the user's field (it picks the Scimago subject area for quartiles),
the papers (if none are attached), and the year range if they want papers
flagged outside it. If the user brings a template from their lecturer or
supervisor, show it back and say how it maps: the LRM columns are fixed, so a
template's extra columns can only become themes in a synthesis matrix, and only
if the user asks for one.

## Rules that hold for every matrix

- **Quote, then write; never complete the pattern.** Every cell is written
  only from verbatim quotes of that paper, checked by
  `scripts/check_evidence.py` and then by a second reader. If the paper says
  A and B, the cell says A and B, not the C that usually comes with them.
  Read `references/reading-and-writing.md` before reading any paper.
- **Run each step on its planned model** (`references/model-routing.md`):
  scripts for anything with one right answer, `haiku` to read, `sonnet` to pair
  abstract claims with the body, `opus` to verify and synthesise. From 2
  papers the reading and pairing run as helpers; with 1 paper the chat does
  them itself. The `opus` verification always runs separately from the reader. **If this session has no `Agent` tool, tell the user in one line
  that no helpers or per-step models are available here and that every step
  runs on their chat's model**, then run the same steps in the session.
- **Never invent.** A cell traces to something actually retrieved: a PDF, a
  fetched page, a real record. If it cannot be traced, write "Not retrieved",
  "Not explicitly stated" or "Unranked/Unavailable".
- **Citations come from Crossref**, quartiles from **Scimago (SJR)**. Never
  assign a quartile from a journal's reputation.
- **Write about the paper, not about yourself.** The reader is reading other
  people's research: use "the authors", "the researchers", "the study", "the
  team", varied so that no cell reads as a repeat. No "I", "my" or "we".
- **Paraphrase**; quote only a short phrase worth quoting, with its page.
- **Stop at bot checks and paywalls.** Never use Sci-Hub, LibGen or similar.
- Show disagreements between sources (two quartiles, two numbers) in the cell.
- Every matrix goes into one Excel workbook for the project (`Summary`, `LRM`,
  then `Synthesis matrix` or `Concept matrix` if asked for). There is no PDF
  output. Open or render the workbook and look at it before sharing.

## Files

- `references/reading-and-writing.md`, `references/model-routing.md`: read
  first for any matrix; `references/overclaim-pairing.md` for the abstract-vs-body
  check
- `scripts/build_lrm.py`, `crossref_check.py`, `scimago_quartile.py`,
  `check_evidence.py`, `merge_papers.py`, `apply_overclaims.py`
- `scripts/build_synthesis.py`, `build_concept.py` (only on request)
- `examples/`: illustrative inputs. The made-up rows are labelled as such;
  never copy them into a user's matrix.
- Needs Python 3 and `openpyxl` (`pip install openpyxl`).
