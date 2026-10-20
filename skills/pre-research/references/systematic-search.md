# Systematic search: run the strings, record the hits, get the records

Used by the PRISMA branch and whenever the user wants the strings run for real. Needs the strings and `search_log.json` from `references/strings.md` first.

## Run the searches and record the hits

Read `references/browser-runs.md` first. In short: ask the user to open the browser pane and sign in through their university, then run each Scopus and Web of Science string yourself in Advanced Search, one at a time, while they watch, and read the result count off the page. Stop at any CAPTCHA, "unusual traffic" or access-denied page and hand that search to the user; never try to get past a bot check.

After each search, write the count into its row in `search_log.json`: `"hits"`, `"source": "browser"` (or `"user"` if they told you), `"date"`. A count nobody read stays `null`. Never fill in an estimate, because the report presents these numbers as facts.

For a free cross-check that needs no login, also run:
```
python3 scripts/openalex.py count search_log.json
```
It adds an OpenAlex row per tier and year range, labelled as an approximation. OpenAlex is free, but without a key every user on one network shares a small daily budget; if it says the budget is used up, suggest a free key (`OPENALEX_API_KEY`, from openalex.org/settings/api).

## Choose the search with the user

Show a small table of hits per tier and range. As a guide, 100 to 2,000 records in Scopus or Web of Science is workable for a review. Over that, use a narrower tier or tighten Concept 2; under about 50, use a broader tier or widen the niche terms. Re-run only the strings you changed. Record the decision in the log as `"chosen": {"tier": "...", "range": "...", "reason": "..."}`.

## Get the records

The reliable source is the database's own export. Ask the user to click Export in Scopus (CSV, with DOI and abstract) and Web of Science (tab-delimited or plain text, full record with abstract) for the chosen search; an export is a bulk download, so it is theirs to click. Then:
```
python3 scripts/openalex.py import scopus.csv savedrecs.txt --out records.json
```
It merges the files and removes duplicates by DOI, then by title and year; the counts feed the PRISMA diagram. If the user has no Scopus or Web of Science access, use OpenAlex instead (abstracts included where OpenAlex has them):
```
python3 scripts/openalex.py list search_log.json --tier balanced --range 2021-2026 --out records.json
```
