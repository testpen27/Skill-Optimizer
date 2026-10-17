---
name: research-search-string
description: 'Build, run and document Boolean literature searches for Scopus (users may say "Opus"), Web of Science (WoS) and Google Scholar. Use it whenever someone gives a research title, topic, question or systematic, scoping or bibliometric review and wants search strings, keywords or a concept table; wants the strings run and the hit counts recorded; wants the free or full-text papers a search finds downloaded into a folder; or wants a search strategy report or PRISMA flow diagram for their database search. Also use it to debug, fix, shorten, widen or narrow a search they already wrote, including an "invalid query", zero results, or too many or too few hits. Handles field tags (TS=, TITLE-ABS-KEY, PY=), AND/OR/NOT, truncation (*), wildcards (?), phrase quotes, country niches, several year ranges, broad to narrow tiers, and Malay or other local-language strings. Not for screening abstracts, writing the review itself, a literature review matrix, or general Boolean or SQL help.'
---

# research-search-string

Turn a research topic into tested search strings for Scopus, Web of Science and Google Scholar, run them, record how many hits each one gets, collect the papers that are legally free, and hand over a PDF report with every string, its hit count and a PRISMA 2020 flow diagram.

"Opus" almost always means Scopus. Use Scopus without correcting the user.

The whole job has nine steps. Not every request needs all of them: someone who pastes a broken string only needs the checker (see "When the user brings their own string"). Ask before moving from strings (steps 1 to 4) to collecting papers (steps 5 to 9), because that part takes their time in the browser.

## Step 0: know what you can do here

Check once, at the start, and say plainly what will not be possible.

- **Browser.** The built-in browser in the Claude desktop app (tools `mcp__Claude_Browser__*` or `mcp__remote-devices__Claude_Browser__*`) keeps the user's university sign-ins between sessions. Load the `built-in-browser` skill before its first use. Claude in Chrome (`mcp__claude-in-chrome__*`, `chrome-browser` skill) works too. With neither, the user runs the searches and tells you the counts.
- **Firecrawl** (`mcp__Firecrawl__*` or the `firecrawl` skill) finds free copies on the open web. Without it, rely on OpenAlex alone.
- **Where files go.** If you are working on the user's own computer (Claude desktop app, Claude Code or Cowork with access to their home folder), you can save into a folder they choose. In claude.ai on the web you work in a sandbox: save to `/mnt/user-data/outputs/` and share with `present_files`; their browser puts the files in Downloads when they click.
- **Scripts** need Node (strings), Python 3 (everything else) and `reportlab` for the PDF (`pip install reportlab` if missing).

## Step 1: ask first

Do not write a string until you know the niche. Ask everything in one short message, filling in what the user already told you so they only correct it:

1. Field or discipline.
2. Working title or research question.
3. Population or context (who or what is studied).
4. Niche: country, region, sector or platform, if any.
5. Year range or ranges. Ask outright; several are fine (for example 2016 to 2020 and 2021 to 2026, to compare before and after an event). If they have no preference, suggest the last five calendar years including the current one, and say which years that is.
6. Review type: systematic, scoping, bibliometric or narrative.
7. Document types and languages (journal articles only? conference papers? English only?).
8. Which databases their university gives them: Scopus, Web of Science, or neither.
9. Roughly how many papers they hope to end up screening.

Keep the answers; they go in the report as the search profile.

## Step 2: build the strings

1. **Split the topic into 3 or 4 concepts**: Concept 1 the main subject, Concept 2 the action or outcome (many synonyms), Concept 3 the population or context, Concept 4 the niche.
2. **Choose 6 to 14 terms per concept.**
   - Quote multi-word terms: `"video on demand"`.
   - Truncate word families: `adopt*`. Keep at least 3 characters before `*`.
   - Use `*` for spelling variants inside a word: `behavio*r`. `?` is exactly one character, so `behavio?r` misses "behavior".
   - In Web of Science a quoted phrase does not match plurals or UK/US spellings, so truncate the last word (`"streaming service*"`) or use `?` (`"news organi?ation*"`). Scopus and Web of Science both accept `*` and `?` inside quotes; `$` is Web of Science only. Google Scholar accepts none of these.
   - When the niche is a country, add place, brand and outlet names: studies often name the outlet, not the country.
3. **Write the spec** (see `examples/example_spec.json`) with `ranges` for the year ranges and, if the default does not fit, `tiers`:
   - `broad`: subject and outcome only (concepts 1 and 2).
   - `balanced`: adds the niche or the population.
   - `narrow`: every concept.
4. **Run the checker and fix every warning** you cannot explain away:
   ```
   node scripts/search_tool.js strings spec.json
   ```
5. **Write two Google Scholar strings by hand** under `scholar` (no truncation, 256 characters or fewer): A with the core terms, B swapping in the niche, brand and outlet names. Rerun the checker.
6. **Add a local-language string** under `local` with `localLanguage` (for Malaysia, Malay) when local journals publish in that language. It runs as its own search and is merged afterwards, never joined to the English string with AND.
7. **Make the search log**, the one file that records every search from here on:
   ```
   node scripts/search_tool.js plan spec.json > search_log.json
   ```
   Add the interview answers to it as `"profile": {"Field": "...", ...}`.

Show the user the strings now (format below), before running anything.

## Step 3: run the searches and record the hits

Read `references/browser-runs.md` first. In short: ask the user to open the browser pane and sign in through their university, then run each Scopus and Web of Science string yourself in Advanced Search, one at a time, while they watch, and read the result count off the page. Stop at any CAPTCHA, "unusual traffic" or access-denied page and hand that search to the user; never try to get past a bot check.

After each search, write the count into its row in `search_log.json`: `"hits"`, `"source": "browser"` (or `"user"` if they told you), `"date"`. A count nobody read stays `null`. Never fill in an estimate, because the report presents these numbers as facts.

For a free cross-check that needs no login, also run:
```
python3 scripts/openalex.py count search_log.json
```
It adds an OpenAlex row per tier and year range, labelled as an approximation. OpenAlex is free, but without a key every user on one network shares a small daily budget; if it says the budget is used up, suggest a free key (`OPENALEX_API_KEY`, from openalex.org/settings/api).

## Step 4: choose the search with the user

Show a small table of hits per tier and range. As a guide, 100 to 2,000 records in Scopus or Web of Science is workable for a review. Over that, use a narrower tier or tighten Concept 2; under about 50, use a broader tier or widen the niche terms. Re-run only the strings you changed. Record the decision in the log as `"chosen": {"tier": "...", "range": "...", "reason": "..."}`.

## Step 5: get the records

The reliable source is the database's own export. Ask the user to click Export in Scopus (CSV, with DOI) and Web of Science (tab-delimited or plain text, full record) for the chosen search; an export is a bulk download, so it is theirs to click. Then:
```
python3 scripts/openalex.py import scopus.csv savedrecs.txt --out records.json
```
It merges the files and removes duplicates by DOI, then by title and year; the counts feed the PRISMA diagram. If the user has no Scopus or Web of Science access, use OpenAlex instead:
```
python3 scripts/openalex.py list search_log.json --tier balanced --range 2021-2026 --out records.json
```

## Step 6: find the free copies

1. `python3 scripts/openalex.py enrich records.json` marks every DOI with a legal open-access copy (OpenAlex includes Unpaywall's data).
2. For records still without one, use Firecrawl to look for the paper's title as a PDF on university repositories, the author's page, arXiv or other preprint servers, and the journal's own site if it is open access. Put any direct PDF link you find into that record's `pdf_url` and set `"is_oa": true`.
3. If the user ran a Google Scholar search in the browser, the `[PDF]` links on that results page are fair to collect the same way. Do not send Firecrawl to Google Scholar: it blocks automated access.

Never use Sci-Hub, LibGen, Anna's Archive or similar sites, and never scrape ResearchGate or Academia.edu.

## Step 7: download

Ask where to put the papers:
- **On the user's computer**: a folder they name, or their Downloads folder (default a subfolder named after the review).
- **In claude.ai on the web**: say the files will arrive through the download links, so their browser saves them to Downloads.

If more than 50 papers are free, say how many and confirm before starting. Then:
```
python3 scripts/retrieve.py download records.json --dest "<folder>" --max 50
```
It only fetches free copies, obeys each site's robots.txt, waits between requests to the same site, and keeps a file only if it is a complete PDF. A "failed" row usually means the link was a landing page or a bot check; try the next source for that paper or leave it for the user. On the web, zip the folder and share it.

## Step 8: paywalled papers

These are fetched through the user's own library access, and the publisher's terms decide who clicks. Read `references/publisher-terms.md`. In short:

- **Elsevier (ScienceDirect)** forbids automation: open each article in a new tab and ask the user to click Download.
- **Other publishers**: check the terms first, as that file describes. Only where the terms clearly allow automated downloading may you click Download yourself, one paper at a time. Otherwise the user clicks.

After each download, file it:
```
python3 scripts/retrieve.py adopt "<folder>/manifest.json" --file "<downloaded file>" --doi <doi> --move
```

## Step 9: the PDF report

Ask whether they have screening numbers yet (records excluded at title and abstract, reports assessed, excluded with reasons, studies included). Put any they give under `"prisma"` in the log; the rest print as "to be completed", never as a guess. Then:
```
python3 scripts/build_report.py --log search_log.json --records records.json --manifest "<folder>/manifest.json" --out search_report.pdf
```
The report holds the search profile, the concepts and tiers, every string with its hit count, how and when the count was recorded, the PRISMA 2020 flow diagram, and the retrieved and not-retrieved papers. Save it next to the papers and share it.

## Reply format for the strings

Easy to copy on a phone:
- One line with the concepts, tiers and year ranges.
- A code block per string: Scopus and Web of Science per tier, Scholar A and B, and the local-language string.
- Two or three lines on what happens next.

## When the user brings their own string

Run the checker before changing anything, so you fix what is broken, not what looks odd:
```
node scripts/search_tool.js check "their string" [scopus|wos|scholar]
```
- **Too many results**: narrower tier, tighter Concept 2 or dates, or drop broad stems such as `innovat*`.
- **Too few**: drop Concept 3 first, then widen the niche terms, then the dates.
- **Shorten it**: cut the weakest terms from the longest concept, keeping every concept.
- **Mixed-up databases**: a Scopus string in Scholar, or `TS=` in Scopus, is the usual cause of zero results.

Say what you changed in one or two lines, then give the new string in a code block.

## Other databases

PubMed, IEEE Xplore, ProQuest and EBSCO use different field tags and wildcard rules that this skill has not verified. Build the concept table and the Boolean skeleton, and tell the user to adapt the field tags from that database's help page. Do not invent field codes.

## Things that went wrong before

- **Scholar's "Review articles" filter** (`as_rr=1` in the link) hides most primary studies. Check shared links for it.
- **Identical Scholar counts for different versions** usually mean English and local-language terms were joined with AND.
- **Concept 4 is a topic filter**, not an affiliation-country filter.
- **Curly quotes** from phones, Word or chat apps stop Scopus and Web of Science reading a phrase as a phrase. The checker flags and converts them.
- **Lower-case `or`**: Scholar only reads `OR` in capitals.
- **Scholar shows at most 1,000 results** per query, and its counts are approximate ("About 12,300").
- **A "PDF" link that is really a web page** is the most common download failure. The downloader rejects anything that is not a complete PDF.
