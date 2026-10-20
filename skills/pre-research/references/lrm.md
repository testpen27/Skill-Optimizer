# Branch: Literature Review Matrix (LRM)

Turn a set of papers into an LRM with split Introduction, Methodology, Results and Discussion columns, delivered as a PDF, plus a short synthesis. The papers can come from a quick search (`references/quick-search.md`), from the papers included after PRISMA screening, from the downloaded folder, or from papers the user already has and wants classified or ranked.

## Rigor discipline (applies to every cell)

- **Trace before you type.** Every cell traces back to something actually retrieved: a fetched page, a PDF, real metadata. If you cannot point to where a claim came from, it does not go in.
- **Flag gaps, do not fill them.** "Not retrieved", "Not explicitly stated" or "Unranked/Unavailable" is better than a plausible guess.
- **Re-check anything too clean**: a quartile that does not match the journal's reputation, an unusually large effect size, a theory that fits too neatly.
- **Show disagreements.** If two sources give different quartiles or numbers, say so in the cell.
- **When a tool returns nothing, say so and use another real source**, never memory.

## Steps

1. **Relevance.** Tag each paper highly, moderately or tangentially relevant to the title's constructs. Drop tangential ones unless the user wants the full list, and tell them how many were found and how many remain. Apply the year range(s) from the intake. Skip this for papers that already passed PRISMA screening: the reviewer has decided.
2. **Quartile.** Look up each journal's Scimago (SJR) quartile: search "[journal] Scimago quartile" or open scimagojr.com. Use the subject category closest to the paper, and note the year if quartiles moved. A thesis, preprint or conference paper is "N/A (thesis/preprint/conference)"; a journal with no quartile found is "Unranked/Unavailable". Never assign a quartile from reputation.
3. **Method and access.** Method is Quantitative, Qualitative, Mixed-methods or Theoretical/Review, from what the paper states. Access is Free or Paid; if `openalex.py enrich` or the download manifest already says, use that; otherwise "Unclear".
4. **Read for IMRAD.** Use the full text where there is one: the PDFs in the project's `papers/` folder, or `firecrawl_research_read_paper`. Abstracts alone often stop before the results. Paraphrase; do not copy sentences.
5. **Draft in chat first.** Show the matrix as a markdown table (Title, Author(s) & Year, Quartile, Method, Access, Introduction, Methodology, Results, Discussion, Theoretical Framework). Each IMRAD cell is one short clause, with real numbers where the paper gives them. Let the user correct it; a markdown table is cheap to redo, a PDF less so.
6. **Synthesis.** A few sentences after the table: recurring theories, dominant methods, quartile balance (flag a set that is mostly Q3/Q4), and gaps the user's study could fill.
7. **PDF.** Write the confirmed rows to `lrm.json` (format at the top of `scripts/build_lrm.py`), then:
   ```
   python3 scripts/build_lrm.py lrm.json --check
   python3 scripts/build_lrm.py lrm.json --out "<project>/LRM.pdf"
   ```
   The script lays out the landscape table so it always fits the page and refuses invalid quartile, method or access labels. Render the first page to an image and look at it before sharing.

If the paper list changes later, rebuild both the markdown draft and the PDF so they stay consistent.

## Working faster with subagents (optional)

When the `Agent` tool is available, the quartile, method and access lookups (steps 2 and 3) are mechanical and can go to one subagent with `model: "haiku"`, given the paper list and the rules above. Steps 4 to 6 are where quality shows; delegate them to `model: "opus"` only if the default model's paraphrasing falls short. Without subagents, do everything directly.
