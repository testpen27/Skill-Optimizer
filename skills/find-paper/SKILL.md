---
name: find-paper
description: Find, filter, group, and synthesize academic journals, papers, and theses for postgraduate/PhD-level research, ending in a Literature Review Matrix (LRM) with split Introduction/Methodology/Results/Discussion columns. Use this whenever the user gives a research title, thesis topic, or research question and wants related literature gathered — phrases like "find papers on...", "literature review for...", "related studies about...", "LR matrix", "LRM", "synthesis matrix", "review of related literature (RRL)", "sources for my thesis/dissertation", or asks to group papers by journal quartile (Q1-Q4), by qualitative/quantitative method, or by free/open-access vs paywalled. Also trigger if the user asks to classify or rank papers they already have by impact factor or methodology, even without asking for a fresh search.
---

# Find Paper

Helps a postgraduate/PhD-level researcher go from a research title to an organized, evidence-grounded literature base, ending in a **Literature Review Matrix (LRM)** delivered as a PDF they can drop straight into a thesis or paper. The LRM is the deliverable everything else in this skill exists to produce — the search, filtering, and labeling steps are all in service of that one table.

## Why this order matters

Grouping and labeling before writing the matrix keeps the final table honest — it forces every claim (quartile, method type, access) to be looked up individually rather than guessed once you're staring at a big table and want to fill cells quickly. Do not skip steps or collapse them into one pass.

## Rigor discipline (applies to every step)

This skill runs on the same discipline as the /f5 fact-checking standard, applied specifically to citations and literature data — it isn't a separate pass, it's how each step below should already be done:

- **Trace before you type.** Every cell in the eventual LRM must trace back to something actually retrieved in Steps 2–5 (a search snippet, a fetched page, a paper's real metadata). If you can't point to where a claim came from, it doesn't go in the table.
- **Flag uncertainty instead of smoothing over it.** A confident-sounding gap fill is worse than a visible "Not stated" or "Unranked/Unavailable" — the researcher needs to know what's genuinely missing, not a plausible guess dressed as fact.
- **Re-verify anything that looks too clean.** A quartile that seems off from the journal's general reputation, an effect size that looks suspiciously large, a theory that seems to fit too neatly — these are exactly the details worth a second lookup before they go in the matrix, not after a complaint.
- **Surface disagreements, don't silently pick one.** If two sources give different quartiles or different numbers for the same paper (common — SJR quartiles shift by year and by subject category), say so in the cell rather than choosing one and hiding the conflict.
- **When a paper tool returns nothing, say so and fall back — don't fill the gap from memory.** If a full-text tool comes back empty, note it and pull the detail from another real source (e.g., the paper's PubMed/PMC page) instead of writing a plausible-sounding summary from general knowledge of the topic.

## Step 1 — Ask the field, then build a keyword set

Always ask the user which field or discipline the research sits in (e.g., education, psychology, computer science, nursing, business) before searching — even if it seems obvious from the title. The same title can mean different things across fields (e.g., "engagement" means something different in education vs. marketing), and the field name itself becomes a search term that filters out same-keyword-different-discipline noise. Skip asking only if the user already stated the field earlier in the conversation.

If the user gave a full research title, pull out its core pieces: the main variables/constructs, the population or context, and the relationship being studied (e.g., "the effect of X on Y among Z"). If the title is genuinely too vague to search on (e.g., just "AI in education"), ask one quick clarifying question about scope (level of education? which aspect of AI?) — otherwise proceed with a reasonable interpretation.

From this, build 5–10 keyword combinations, including synonyms and both narrow and broad phrasings, with the field appended to each so it stays a filter rather than an afterthought (e.g., "student engagement" AND "gamification" AND "education"; "gamified learning" AND "motivation" AND "education"). Boolean-style variety matters more here than volume — each web_search call only returns ~10 results, so varied queries surface a wider net than repeating the same phrase.

## Step 2 — Search broadly and gather candidates

**Tool routing (check what's connected before choosing):**

If the Firecrawl connector is available, use it — but scoped strictly to its research/paper tool family. Don't reach for `firecrawl_search` or `firecrawl_developer_search`: those are general-purpose web/code search, outside what this skill needs, and mixing them in defeats the point of using a paper-specific index in the first place.

- `firecrawl_research_search_papers` — the primary search. It reaches PubMed, bioRxiv, medRxiv, arXiv, and adjacent scientific sources. Use it when the field is biomedical, life-science, clinical, physics, CS, math, or another arXiv-covered STEM area.
- `firecrawl_research_related_papers` — once you have 1–2 strong seed papers, use this to snowball outward via the citation graph and surface additional candidates you wouldn't find by keyword alone.
- `firecrawl_research_read_paper` — pull real full-text passages (methods, results) for a paper found via the tools above, instead of relying on the abstract alone. It'll say so if full text isn't indexed — don't treat that as a dead end, see the fallback below.
- `firecrawl_research_inspect_paper` — verify canonical metadata (authors, dates, IDs) for a paper before it goes in the LRM.

**Coverage gap to plan around:** this tool family is genuinely thin-to-empty for education, business, psychology, humanities, and most social-science fields — it's not a universal paper index. For those fields, or whenever the paper tools return little, go straight to web_search + web_fetch for the search itself (see Sources below); don't substitute `firecrawl_search` as a workaround, since that reintroduces the general-purpose tool this step is deliberately avoiding.

**When Firecrawl's own full-text lookup comes back empty** (`firecrawl_research_read_paper` returns no passages, which happens often), fall back to web_search + web_fetch on the paper's PubMed/PMC or journal page to get real Methods/Results — don't leave the LRM row thin when the actual data is one search away.

If Firecrawl isn't connected at all, skip straight to web_search + web_fetch for everything below.

**Sources, either way:** Scopus and Google Scholar first — via `site:scholar.google.com [keywords] [field]` and `[keywords] [field] scopus` — rounded out with Semantic Scholar, ScienceDirect, SpringerLink, Wiley, MDPI, IEEE Xplore, JSTOR, ERIC, DOAJ, PubMed (health-related), and university repositories (for theses/dissertations). Vary the query each time — don't repeat the same phrase.

Be upfront with the user about one real limitation that Firecrawl doesn't remove: there's no authenticated Scopus login here, and Google Scholar has no official public API — both are reached through search, the same way anyone without institutional access would find them. A paper's presence in Scopus specifically still can't be confirmed without the user's own Scopus login. Mention this once near the start of a search, not on every result.

For a proper matrix, aim to gather at least 15–20 candidate papers before filtering (postgrad-level literature reviews are thin below this). For each candidate, record: title, author(s), year, journal/publisher or repository, and link/DOI. Pull the abstract (and full text where the tools above allow it) to skim for methodology — this is also where you'll spot the journal name needed in Step 4.

Keep a running scratch list (plain text or a markdown table) of everything found before filtering — don't discard anything yet.

## Step 3 — Filter for relevance and recency

Compare each candidate's abstract/title against the research title's core constructs and tag each as:
- **Highly relevant** — directly addresses the same variables/relationship
- **Moderately relevant** — shares some constructs or context, useful for background/theory
- **Tangential** — only loosely connected

Drop tangential papers unless the user asks to keep the full list. Tell the user briefly how many were found vs. how many survived filtering — that count is itself useful information for them.

**Recency rule:** a paper must be published within the last 5 years to qualify for the LRM. Compare by **calendar year only, not exact date** — take the current year, subtract 5, and that's the cutoff year; anything published in the cutoff year or later qualifies, regardless of month. Don't compute day/month precision or treat a January publication differently from a December one in the same year. Drop anything older than the cutoff year, same as a tangential paper — note it was excluded for age if the user might wonder why an otherwise-relevant paper is missing. If the user explicitly asks to include an older foundational/seminal source (e.g., the paper that originated a theory being used), that's a fine exception to make on request — but it's opt-in, not the default.

## Step 4 — Group by journal quartile (Q1–Q4)

For each surviving paper, identify its journal and look up its Scimago Journal Rank (SJR) quartile — search "[journal name] Scimago quartile" via web_search, or fetch scimagojr.com directly. This lookup stays on plain web tools regardless of whether Firecrawl is connected — it's a journal-ranking lookup, not a paper search, so it's outside the paper-tool family Step 2 scopes Firecrawl to. Use the quartile for the subject category most relevant to the paper's topic if the journal spans multiple categories, and note the year if quartiles have shifted.

Be strict about not guessing:
- Thesis, dissertation, preprint, or conference paper with no journal → label **"N/A (thesis/preprint/conference)"**
- Journal exists but no quartile data turns up after searching → label **"Unranked/Unavailable"**
- Never assign a quartile from general impression of the publisher's reputation — only from an actual lookup.

## Step 5 — Label method type and access

For each paper, determine:
- **Method type**: Quantitative, Qualitative, Mixed-methods, or Theoretical/Review — based on what the abstract or methods section actually states, not the topic alone.
- **Access**: Free (open access, DOAJ-listed, or full text you could actually retrieve) or Paid (paywalled, abstract-only access). If genuinely unclear, label "Unclear" rather than guessing.

## Step 6 — Build the Literature Review Matrix (LRM)

Present it first as a markdown table inline in the chat — this is the reviewable draft, not the final deliverable (see Output below for the PDF export). IMRAD gets its own four columns rather than one combined summary, so each stage of a paper's structure is scannable on its own:

| # | Title | Author(s) & Year | Quartile | Method | Access | Introduction | Methodology | Results | Discussion | Theoretical Framework |
|---|-------|-------------------|----------|--------|--------|--------------|-------------|---------|------------|------------------------|

- **Title**: full paper title.
- **Author(s) & Year**: surname(s), publication year.
- **Quartile**: Q1/Q2/Q3/Q4, or the N/A / Unranked labels from Step 4.
- **Method**: from Step 5.
- **Access**: Free / Paid / Unclear.
- **Introduction**: the paper's stated aim/problem — one short clause.
- **Methodology**: design, sample size, key procedural detail — one short clause.
- **Results**: the key finding(s), with actual numbers where the source gives them — one short clause.
- **Discussion**: the stated implication, mechanism, or conclusion — one short clause.
- **Theoretical Framework**: the named theory/model the paper builds on. If none is explicitly stated, write "Not explicitly stated" — never invent one.

Each IMRAD cell should be condensed and paraphrased, not copied sentences from the abstract. If a stage genuinely wasn't retrievable (e.g., a truncated abstract snippet cut off before Results), write "Not retrieved" in that cell rather than inferring a plausible-sounding result — this is the rigor discipline above applied to the table itself.

Every cell must trace back to something actually found in the search/fetch steps. If a detail can't be verified, mark it as such rather than leaving a plausible-looking guess.

## Step 7 — Short synthesis

After the LRM, add a brief synthesis (not another table): recurring theories across papers, dominant methodologies, any quartile imbalance (e.g., mostly Q3/Q4 sources — worth flagging to the user), and visible gaps the user's own research could address. Keep this to a few sentences — the LRM is the deliverable, this is the "so what."

## Copyright note

When pulling abstracts or full-text passages (via web_fetch or Firecrawl's `firecrawl_research_read_paper`), paraphrase into the Introduction/Methodology/Results/Discussion cells rather than copying sentences — the LRM should reflect each paper's content in your own condensed words, not quoted text. Full-text access makes this more tempting, not less necessary.

## Output

The LRM is always exported as a **PDF** — not markdown, not a .md file. The inline markdown table in Step 6 is a review draft the user can flag corrections on before the PDF is generated; regenerating a markdown table costs nothing, regenerating a PDF does, so let the user confirm the content first.

Before generating the file, view `/mnt/skills/public/pdf/SKILL.md` for the current recommended method — this is a mandatory check, not an assumption, since the right library can change. As of writing, `reportlab` (Platypus) is the tool for building a new PDF from scratch, and a few things matter specifically for this table:

- **Landscape orientation.** Eleven columns of text-heavy cells won't fit in portrait without becoming unreadable.
- **Wrap cells in `Paragraph` objects, not raw strings.** A Platypus `Table` built from plain strings won't wrap long Methodology/Results/Discussion text — it'll overflow or force the column too wide. Every cell should be a `Paragraph` with a small body style.
- **Small font (7–8pt) and explicit column widths.** Give Title, Methodology, Results, and Discussion more width than Quartile, Method, or Access, which are short labels.
- **Sum your column widths and check them against the actual usable page width before building** — landscape letter is 11in wide; subtract both margins to get what's left (e.g., 0.35in margins each side leaves 10.3in). This isn't optional bookkeeping: `Table`'s default alignment is centered, so when total column width exceeds the frame, the overflow gets clipped symmetrically off *both* edges — the leftmost column can disappear entirely while the rightmost one looks merely cut off, which reads as a rendering bug rather than the width-math error it actually is. Set `hAlign='LEFT'` on the table as a second safeguard regardless.
- **Render the finished PDF to an image and look at it before presenting it.** Convert the first page (e.g., via `pdf2image`) and view it — this is the only reliable way to catch column overflow, awkward page breaks, or a table that silently ran off the edge. Don't skip this step because the code "looks right"; the bug above is invisible from the script alone and only shows up in the rendered output.

Save the finished PDF to `/mnt/user-data/outputs/` and present it — a file that's generated but never presented isn't reachable by the user. If the paper list is later revised (new papers added, filters changed, recency cutoff shifts with a new year), regenerate both the markdown draft and the PDF rather than patching either individually, so quartile/method/access/recency stay consistent across both.
