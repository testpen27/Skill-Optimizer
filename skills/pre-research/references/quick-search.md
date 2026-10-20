# Quick search: 15 to 20 strong papers without database access

The fast way to gather literature, used for the LRM when nobody needs a full database search. It reaches Scopus, Web of Science and Google Scholar only through open web search, so tell the user once, near the start, that it cannot confirm a paper is indexed in Scopus or Web of Science; that needs their own login and the systematic search.

## Keywords

From the intake, pull out the main constructs, the population or context, and the relationship studied. Build 5 to 10 keyword combinations with the field name in each, so it filters out same-word-different-discipline noise (engagement in education is not engagement in marketing). Vary them using:
- **Phrases** in quotes: `"student engagement"`.
- **AND / OR / NOT**: `("gamification" OR "game-based learning") AND "student motivation"`, and `-"video games"` to push out a sense you do not want.
- **Truncation** (`educat*`) only where the engine supports it: library databases do; Google and Google Scholar do not reliably, so spell the variants out there.

## Where to search

**Firecrawl paper tools first, when connected** (`firecrawl_research_search_papers`, `firecrawl_research_related_papers`, `firecrawl_research_read_paper`, `firecrawl_research_inspect_paper`):
- `firecrawl_research_search_papers` is semantic, not keyword search: it does not read quotes, Boolean operators or `*`. Give it a plain sentence ("gamification and student motivation in higher education") and vary the wording instead.
- `firecrawl_research_related_papers` snowballs from 1 or 2 strong seed papers through the citation graph.
- `firecrawl_research_read_paper` pulls real methods and results passages; when it returns nothing, fall back to the paper's own page instead of writing from memory.
- `firecrawl_research_inspect_paper` confirms authors, dates and identifiers.
- Coverage is strong for biomedical and arXiv fields and thin for education, business, psychology, humanities and most social science. For those, go straight to web search.

**Web search**: Google Scholar, Scopus and Web of Science first (`site:scholar.google.com [keywords] [field]`, `[keywords] [field] scopus`, `[keywords] [field] "web of science"`), then the fallback tier only if needed: Semantic Scholar, ScienceDirect, SpringerLink, Wiley, MDPI, IEEE Xplore, JSTOR, ERIC, DOAJ, PubMed for health topics, and university repositories for theses.

## Gather, then narrow

- Gather at least 15 to 20 candidates before filtering. For each, record title, authors, year, journal or repository, DOI or link, and the abstract.
- Keep only papers inside the year range(s) from the intake. Compare by calendar year. Older foundational papers only when the user asks for them.
- If highly relevant hits run well past what one review can cover, propose a narrower niche (country, population, sector, intervention variant or a tighter year range) and let the user choose; do not silently drop papers.

## Write it down as you go

- Save the candidates as `records.json` (format in `references/access-download.md`) in the project folder, so the download and LRM branches can use them.
- Log every query in `search_log.json` under `"runs"`: `{"database": "Google Scholar (web search)", "string": "<exact query>", "hits": <results returned>, "source": "web search", "date": "YYYY-MM-DD", "note": "phrase, Boolean, truncation used: ..."}`. Be literal: Firecrawl's semantic search gets "none" for every technique. This log becomes the search section of the report.
