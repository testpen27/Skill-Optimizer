---
name: research-matrix
description: Build an academic literature review matrix (LRM) from scholarly papers the user already has, with one row per paper (APA 7 authors and title, introduction, methodology, theory, results, discussion, journal quartile checked on Scimago, citation checked against Crossref, retractions flagged), sorted A-Z and delivered as an Excel workbook (.xlsx). Use for a literature review matrix, review matrix or literature matrix for a thesis, dissertation, proposal or academic review. Build a synthesis matrix (themes by sources) or a concept matrix (papers by concepts) only when the user asks for that exact matrix. Academic research only; never for SWOT, competitor, marketing, product, risk or decision matrices.
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
- Anything that is not academic literature review work (SWOT, competitor or
  marketing comparison, risk, decision, feature or pricing matrices): say it
  is outside this skill and stop.

## Before you start

Say in one line what you understood. Ask only what blocks you, in one short
message: the user's field (it picks the Scimago subject area for quartiles),
the papers (if none are attached), and the year range if they want papers
flagged outside it. If the user brings a template from their lecturer or
supervisor, show it back and follow its headings where the scripts allow.

## Rules that hold for every matrix

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

- `scripts/build_lrm.py`, `crossref_check.py`, `scimago_quartile.py`
- `scripts/build_synthesis.py`, `build_concept.py` (only on request)
- `examples/`: illustrative inputs. The made-up rows are labelled as such;
  never copy them into a user's matrix.
- Needs Python 3 and `openpyxl` (`pip install openpyxl`).
