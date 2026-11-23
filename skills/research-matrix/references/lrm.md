# Literature review matrix (LRM)

One row per paper. Columns, left to right:

| Code | Type | Authors | Title | Introduction | Methodology | Theory | Results | Discussion | Quartile | Access |
|---|---|---|---|---|---|---|---|---|---|---|

- **Code**: P01, P02 ... assigned by the script after sorting A-Z by the first
  author's family name. Adding a paper renumbers the codes.
- **Type**: Quantitative, Qualitative, Mixed-methods or Theoretical/Review,
  from what the paper itself states.
- **Authors**: APA 7 names with the year, `Tan, A. B., & Lee, C. D. (2024)`.
  The script builds this from the `authors` list and `year`.
- **Title**: the paper title, then the journal, volume(issue), pages and DOI
  link, in APA 7 form. Write the title in sentence case (capital after a
  colon, keep proper nouns and acronyms); Crossref keeps the publisher's
  capitals, so do not copy a Title Case title as it is.
- **Quartile**: the Scimago (SJR) quartile, with year and subject area.
- **Access**: Free if you opened the full text without paying, Paid if it sat
  behind a paywall, otherwise Unclear.

## Steps

1. **Collect the papers.** Take what the user gives you. Every journal paper
   should have a DOI; ask for it if missing. Thesis, preprint and conference
   papers get "N/A (thesis/preprint/conference)" as quartile.
2. **Start `lrm.json`.** Format at the top of `scripts/build_lrm.py`. Put the
   DOI in each paper. Authors are `"Family, I. I."` strings.
3. **Check the citations against Crossref.**
   ```
   python3 scripts/crossref_check.py lrm.json --apply --write
   ```
   `--apply` copies Crossref's authors, year, journal, volume, issue, pages and
   ISSN into the file and reports what changed; without it, mismatches are
   only reported. The title is never overwritten. If the sandbox blocks
   `api.crossref.org`, scrape `https://api.crossref.org/works/<doi>` with
   Firecrawl, save each result as `<doi with / replaced by _>.json` in a
   folder, and add `--offline <folder>`.
4. **Look up the quartile.** For each journal paper:
   ```
   python3 scripts/scimago_quartile.py --issn <issn> --year <publication year> --category "<user's field>"
   ```
   Paste the printed line into `quartile`. It uses the paper's publication
   year, so say that to the user (Scimago quartiles move between years). If
   the sandbox blocks scimagojr.com, scrape
   `https://www.scimagojr.com/journalsearch.php?q=<issn without hyphen>&tip=iss`
   to find the journal id, scrape the journal page it links to
   (`journalsearch.php?q=<id>&tip=sid&clean=0`), save it, and pass it with
   `--journal-page`. If no category contains the user's field, the script says
   which categories exist: pick the closest only with the user's agreement, or
   list all. "Unranked/Unavailable" is a valid answer.
5. **Read each paper** for its introduction, methodology, theory, results and
   discussion: the full text where you have it, not only the abstract. If you
   only have an abstract, fill what it supports and leave the rest "Not
   retrieved" (leave the cell empty in the JSON).
6. **Draft in chat first** as a markdown table with the same columns, so the
   user can correct it. A table in chat is cheap to redo; a PDF is not.
7. **Synthesis paragraph** after the table: recurring theories, dominant
   methods, quartile balance (flag a set that is mostly Q3/Q4), gaps the
   user's study could fill. Write it from the rows, not from memory.
8. **Build and look.**
   ```
   python3 scripts/build_lrm.py lrm.json --check
   python3 scripts/build_lrm.py lrm.json --out "<folder>/LRM.pdf"
   ```
   `--check` refuses a bad quartile, type or access label and warns about long
   cells, first-person wording and repeated openers. Render page 1 to an image
   and look at it before sharing. If the paper list changes, rebuild the
   draft and the PDF together.

## Writing the cells

The reader is a student reading other people's research. The cells must be
short enough to scan and never read like a copy of the abstract.

- Say what the authors report, in your own words, in the third person. Rotate
  the subject: the authors, the researchers, the study, the team, or lead with
  the finding itself ("Attention is treated as...", "A survey of 312 teachers
  found..."). Do not start every cell the same way.
- Length: introduction up to about 40 words, methodology 50, theory 25,
  results 60, discussion 60. Over that is a warning from `--check`.
- **Introduction**: the problem and the aim. **Methodology**: design, sample
  size and setting, instruments or data, analysis. **Theory**: the named
  theory or framework as the paper states it; leave empty if there is none.
  **Results**: the main findings with the real numbers the paper gives.
- **Discussion**: for long discussions, give the authors' conclusion and what
  they say it implies, condensed in your own academic words, including a
  stated limitation if the paper makes one. This is the authors' view, not
  your evaluation.
- No page numbers, except a short direct quote kept in quotation marks with
  its page, e.g. "pivotal step" (p. 112).
- Numbers only as the paper reports them. A result that looks too clean, or a
  quartile that does not fit the journal, gets a second look at the source.

## What the PDF states about itself

The footer line under the table says how many citations were checked against
Crossref and lists the codes that were not, and that quartiles are SJR
quartiles for the year and subject area shown. Do not hand-edit the PDF; fix
`lrm.json` and rebuild.
