---
name: pre-research
description: 'Pre-research for literature reviews, from topic to papers. Use this whenever someone gives a research title, thesis topic or research question and wants related literature found, or wants any of: Boolean search strings or keywords for Scopus (users may say "Opus"), Web of Science or Google Scholar; a broken, too-long or zero-result search string fixed; a systematic search run with hit counts recorded; a PRISMA 2020 flow diagram or search strategy report; title and abstract screening recorded; the papers downloaded (open access or via their library) into a folder; or a Literature Review Matrix (LRM, synthesis matrix, RRL) with IMRAD columns, journal quartiles (Q1-Q4) and method types. Also use it to classify or rank papers the user already has by quartile or methodology. Covers field tags, AND/OR/NOT, truncation, country niches, year ranges and Malay or other local-language strings. Not for writing the review itself, summarising a single paper, citation formatting, or general Boolean, regex or SQL help.'
---

# pre-research

Everything a researcher does before writing the review starts the same way: find the papers that matter for their topic and field. From there the request branches: some want search strings, some want a PRISMA systematic search conducted, some want the papers downloaded, some want a Literature Review Matrix (LRM). This skill does the shared start once and then runs whichever branches the user asked for, keeping everything in one project folder so the branches can feed each other.

"Opus" almost always means Scopus. Use Scopus without correcting the user.

## 1. Know what you can do here

Check once, at the start, and say plainly what will not be possible.

- **Browser.** The built-in browser in the Claude desktop app (tools `mcp__Claude_Browser__*` or `mcp__remote-devices__Claude_Browser__*`) keeps the user's university sign-ins. Load the `built-in-browser` skill before its first use; Claude in Chrome (`chrome-browser` skill) works too. Without a browser, the user runs database searches and tells you the counts.
- **Firecrawl** (`mcp__Firecrawl__*`): its research tools search papers; its web search finds free copies. Without it, use web search and OpenAlex.
- **Where files go.** On the user's own computer (Claude desktop app, Claude Code, Cowork), ask whether to use a folder they name or their Downloads folder. In claude.ai on the web, save to `/mnt/user-data/outputs/` and share with `present_files`; their browser saves the files to Downloads.
- **Scripts** need Node (strings), Python 3 and `reportlab` for the PDFs (`pip install reportlab` if missing).

## 2. Ask first

Ask in one short message, filling in what the user already said so they only correct it. Skip what their branch does not need (a string fix needs none of this):

1. Field or discipline. Always ask, even when the title seems clear: the field name filters out same-word-different-discipline papers.
2. Working title or research question.
3. Population or context.
4. Niche: country, region, sector or platform, if any.
5. Year range or ranges. Always ask; several are fine (for example 2016 to 2020 and 2021 to 2026). If they have no preference, suggest the last five calendar years including the current one and say which years.
6. Review type: systematic, scoping, bibliometric, narrative, or just background for a proposal.
7. Which databases their university gives them: Scopus, Web of Science, or neither.
8. What they want at the end, if they have not said: strings, a PRISMA search, the papers downloaded, an LRM, or several.
9. Where to save (on their computer only): a folder they name, or Downloads.

Make a project folder named after the topic (for example `pre-research/ott-adoption-malaysia/`) and keep every file from every branch there. Keep the answers: they go into the reports.

## 3. Find the papers: quick or systematic

Pick the depth from what they want, and say which you chose:

- **Quick** (about 15 to 20 strong papers from open web and paper search): enough for an LRM, a proposal or background reading. Read `references/quick-search.md`.
- **Systematic** (database strings run in Scopus and Web of Science, full exports, duplicates removed): needed for PRISMA, a systematic or scoping review, or when they ask for hit counts. Read `references/strings.md`, then `references/systematic-search.md`.

## 4. Branches

Run the ones the user asked for, in this order when several apply. Read each branch's file when you reach it.

| The user wants | Branch | Read |
|---|---|---|
| Search strings, keywords, a concept table, or a broken string fixed | Strings | `references/strings.md` |
| A PRISMA systematic search conducted, with screening and the flow diagram | PRISMA | `references/prisma.md` |
| The papers' full text, free or through their library | Access and download | `references/access-download.md` |
| A Literature Review Matrix, quartiles, or their papers classified | LRM | `references/lrm.md` |

Common chains: PRISMA, then download the included papers, then an LRM of them. Quick search, then download, then LRM. When one branch finishes, offer the next one that fits instead of stopping.

## 5. Deliver

Every PDF goes into the project folder and is shared:
- **Search report** (strings, hit counts, how and when each was recorded, PRISMA 2020 diagram, retrieval list): `scripts/build_report.py`, described in `references/prisma.md`. Also useful after a quick search, as a record of what was searched.
- **LRM**: `scripts/build_lrm.py`, described in `references/lrm.md`.

End with what is done, what is still missing (with the list), and where the folder is.

## Rules that hold in every branch

- **Never invent a number.** A hit count nobody read, a quartile nobody looked up, a result the paper did not report: leave it as "not recorded", "Unranked/Unavailable" or "Not retrieved".
- **Screening decisions are the reviewer's.** Claude shows records and records decisions; it never decides inclusion or exclusion.
- **Stop at bot checks.** Never get past a CAPTCHA, "unusual traffic" page or paywall.
- **Respect publisher terms.** Free copies are downloaded automatically; paywalled ones follow `references/publisher-terms.md` (Elsevier: the user clicks). Never use Sci-Hub, LibGen, Anna's Archive or similar sites.
- **Paraphrase, do not copy**, when summarising papers.
