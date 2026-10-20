# Branch: access and download

Get the full text of papers into a folder: legally free copies automatically, paywalled ones through the user's own library access. Works on any records file: from a database export (`references/systematic-search.md`), from a quick search (`references/quick-search.md`), or the papers kept after title-and-abstract screening (`references/prisma.md`).

A records file is JSON: `{"records": [{"doi": "10.xxx/yyy", "title": "...", "year": 2024, "authors": ["Surname, Given"], "venue": "...", "publisher": "...", "landing_url": "..."}]}`. Only `title` is required; give a DOI wherever there is one, because everything below keys on it.

## 1. Find the free copies

1. `python3 scripts/openalex.py enrich records.json` marks every DOI with a legal open-access copy (OpenAlex includes Unpaywall's data).
2. For records still without one, use Firecrawl (`firecrawl_search` or `firecrawl_scrape`) to look for the paper's title as a PDF on university repositories, the author's page, arXiv or other preprint servers, and the journal's own site if it is open access. Put any direct PDF link you find into that record's `pdf_url` and set `"is_oa": true`.
3. If the user ran a Google Scholar search in the browser, the `[PDF]` links on that results page are fair to collect the same way. Do not send Firecrawl to Google Scholar: it blocks automated access.

Never use Sci-Hub, LibGen, Anna's Archive or similar sites, and never scrape ResearchGate or Academia.edu.

## 2. Download the free ones

Use the project folder from the intake (a folder the user named or Downloads on their computer; on the web, the outputs folder, which reaches their Downloads when they click). Papers go in its `papers/` subfolder.

If more than 50 papers are free, say how many and confirm before starting. Then:
```
python3 scripts/retrieve.py download records.json --dest "<project>/papers" --max 50
```
It only fetches free copies, obeys each site's robots.txt, waits between requests to the same site, and keeps a file only if it is a complete PDF. A "failed" row usually means the link was a landing page or a bot check; try the next source for that paper or leave it for the user. On the web, zip the folder and share it.

## 3. Paywalled papers

These come through the user's own library access, and the publisher's terms decide who clicks. Read `references/publisher-terms.md`. In short:

- **Elsevier (ScienceDirect)** forbids automation: open each article in a new tab and ask the user to click Download.
- **Other publishers**: check the terms first, as that file describes. Only where the terms clearly allow automated downloading may you click Download yourself, one paper at a time. Otherwise the user clicks.

After each download, file it:
```
python3 scripts/retrieve.py adopt "<project>/papers/manifest.json" --file "<downloaded file>" --doi <doi> --move
```
`python3 scripts/retrieve.py status "<project>/papers/manifest.json"` lists what is still missing, with DOI links.

## 4. Tell the user

How many downloaded, how many they fetched, how many are still missing (with the list), and where the folder is. If the PRISMA branch is running, the not-retrieved count feeds the "Reports not retrieved" box.
