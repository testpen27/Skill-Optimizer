---
name: pre-research
description: 'Pre-research for literature reviews, from topic to papers. Use it when someone gives a research title, topic or question and wants literature found or organised: Boolean search strings for Scopus (users may say "Opus"), Web of Science or Google Scholar; a systematic search run with hit counts; a PRISMA 2020 flow diagram, screening record or search strategy report; the papers downloaded (open access or via their library) into a folder; or a Literature Review Matrix (LRM, synthesis matrix, RRL) with IMRAD columns. Also use it whenever someone pastes a search string and asks about it (invalid query, syntax error, too long for Scholar, zero or too many results, convert to another database), or asks to classify, rank or tabulate papers they already have by journal quartile (Q1-Q4) or method. Covers field tags, AND/OR/NOT, truncation, country niches, year ranges and local-language strings. Not for writing the review, summarising one paper, citation formatting, or general Boolean, regex or SQL help.'
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
- **Models.** Each step runs on a planned model, mostly through helpers (subagents): read `references/model-routing.md` before the first step. The plan is fixed; the only change allowed is moving a step to a stronger model, and only after asking the user.

## 2. Ask first, but only what the job needs

Work out what the user wants before asking anything, then ask only the questions that job needs, in one short message. Anything their message already answers, fill in yourself and show it so they can correct it; do not ask it again. Long questionnaires put people off, and most answers are only needed for searching.

The questions:

- **A. Field or discipline.** The field name filters out same-word-different-discipline papers, and it picks the subject category for journal quartiles.
- **B. Working title or research question.**
- **C. Population or context.**
- **D. Niche**: country, region, sector or platform, if any.
- **E. Year range or ranges.** Several are fine (for example 2016 to 2020 and 2021 to 2026). If they have no preference, suggest the last five calendar years including the current one and say which years.
- **F. Review type**: systematic, scoping, bibliometric, narrative, or background for a proposal.
- **G. Databases** their university gives them: Scopus, Web of Science, or neither.
- **H. What they want at the end**, if it is not clear: strings, a PRISMA search, the papers downloaded, an LRM, or several.
- **I. Where to save** (on their computer only): a folder they name, or Downloads.

What each job needs:

| The user wants | Ask |
|---|---|
| A string they pasted checked or fixed | Nothing. Only ask which database it is for if the string does not show it |
| New search strings | A, B, C, D, E, and G only if they want the strings run |
| A PRISMA search | A to G and I |
| Papers downloaded from a list or export they already have | I |
| An LRM of papers they already have | A, E (to flag papers outside it, not to search) and I |
| An LRM from a new search | A to E and I |
| Unclear | H first, on its own |

When several jobs are chained, ask the union once, at the start.

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
