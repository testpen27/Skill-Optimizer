# Literature review matrix (LRM)

One row per paper, on the `LRM` sheet of the project workbook (`Matrix.xlsx`,
named after the topic). Columns, left to right:

| Code | Type | Authors | Title | Introduction | Methodology | Theory | Results | Discussion | Quartile | Access |
|---|---|---|---|---|---|---|---|---|---|---|

- **Code**: P01, P02 ... assigned by the script after sorting in APA 7 order
  (first author's family name, then initials; a single-author work before
  multi-author works; undated first). Adding a paper renumbers the codes, so
  nothing else may refer to a paper by its code: use the paper's `id` or DOI.
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
   DOI in each paper, and a short stable `id` (`tufekci2013`). Authors are
   `"Family, I. I."` strings. Two papers by the same authors in the same year
   get the APA 7 a/b suffix automatically.
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
   The same lookup reads the record's **retraction and correction notices**
   (Crossref's `updated-by` field, fed by the Retraction Watch database) into
   `notices`. A retracted paper gets a red code cell and a red "RETRACTED
   <date>" line in its Title cell; a correction or expression of concern gets
   an amber line. Tell the user straight away if a paper is retracted and let
   them decide what to do with it. No notice means none was found, not a
   guarantee: Retraction Watch is most complete for retractions and less so
   for corrections.
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
5. **Read each paper, quotes first.** Follow `reading-and-writing.md`: save
   the text you read to `papers/<id>.txt`, record `source_basis`, collect
   verbatim quotes per column into `evidence`, then write each cell only from
   its quotes. Models per step are in `model-routing.md` (readers on
   `sonnet`, 3 papers each).
6. **Check, then verify.**
   ```
   python3 scripts/check_evidence.py lrm.json --papers papers
   ```
   Fix every ERROR by cutting or narrowing the cell. Then a second reader
   (`opus`) checks every sentence against its quotes and returns keep / cut /
   narrow; apply the verdicts and rerun the script. Only then draft the table
   in chat for the user (same columns), so they can correct it before the
   workbook is built.
7. **Synthesis paragraph** after the table (`opus`): recurring theories,
   dominant methods, quartile balance (flag a set that is mostly Q3/Q4), gaps
   the user's study could fill. Write it from the verified rows, not from
   memory, and word it as the reviewer's synthesis, not as any paper's claim.
8. **Build and look.**
   ```
   python3 scripts/build_lrm.py lrm.json --check
   python3 scripts/build_lrm.py lrm.json --out "<folder>/Matrix.xlsx"
   ```
   `--check` refuses a bad quartile, type or access label and warns about long
   cells, first-person wording, repeated openers and retracted papers. The
   workbook has a `Summary` sheet (field, years, counts, the Crossref status of
   each paper, retraction notices and the synthesis paragraph) and the `LRM`
   sheet, with a frozen header and filters so the user can sort and filter. If
   the `xlsx` skill's `recalc.py` is available, run it on the file so the
   formula cells (the counts on `Summary`) carry values for previewers. Render
   or open the `LRM` sheet and look at it before sharing. If the paper list
   changes, rebuild the draft and the workbook together; the build replaces the
   `Summary` and `LRM` sheets and keeps any other sheets.

## Writing the cells

`reading-and-writing.md` is the authority: what each column takes, where to
look in the paper, and the "compress, never complete" rules. In short: every
sentence traces to a quote; nothing is added that the quotes do not state
(no cause, scope, population, property, number or theory); hedges are kept;
numbers are copied, never computed; thin evidence means a shorter cell.
Style comes second: third person with a varied subject, about 40 words for
introduction, 50 methodology, 25 theory, 60 results and discussion.

## What the workbook states about itself

The `Summary` sheet says how many citations were checked against Crossref and
which were not, lists any retraction or correction notices, shows what each
row was read from (full text, partial or abstract only), counts the papers
whose abstract claims more than their body (those words appear in dark-yellow
text in the LRM, with a hover note quoting both), and says that
quartiles are SJR quartiles for the year and subject area shown. Do not edit
the numbers by hand; fix `lrm.json` and rebuild. The DOI is shown as text in
the Title cell (a cell hyperlink would flatten the italic journal name).
