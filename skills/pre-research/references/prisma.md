# Branch: conduct the PRISMA

Run a systematic search from strings to a PRISMA 2020 flow diagram. **The reviewer (the user) makes every screening decision; Claude shows the records, records each decision with its reason, and does the counting.** If the user asks what you think about a record, you may say so as an opinion, but record only what they decide, because the report states that the screening was the reviewer's.

## 1. Search and records

1. Strings: `references/strings.md`.
2. Run them, record the hits, choose the search, get the exports and de-duplicate: `references/systematic-search.md`. `records.json` now holds the records after duplicates were removed, with abstracts where the exports had them.

## 2. Ask for the eligibility criteria

Before screening, ask the reviewer for inclusion and exclusion criteria (population, concept, context, study design, language, publication type, years) and write them into the log as `"criteria": {...}`. Read them back when showing records, so each decision is made against the same rules.

## 3. Title-and-abstract screening

Offer two ways and let the reviewer pick:
- **In the chat**: show records in batches of 10 to 20:
  ```
  python3 scripts/screening.py batch records.json --stage ta --size 15
  ```
  The reviewer replies, for example, "include R001-R004, exclude R005 wrong population, maybe R006". Record exactly that:
  ```
  python3 scripts/screening.py record records.json --stage ta --ids R001-R004 --decision include
  python3 scripts/screening.py record records.json --stage ta --ids R005 --decision exclude --reason "wrong population"
  ```
- **In a spreadsheet**: `python3 scripts/screening.py sheet records.json --stage ta --out "<project>/screening_ta.csv"`. They fill the decision and reason columns in Excel, then `python3 scripts/screening.py load records.json --stage ta "<project>/screening_ta.csv"`.

`python3 scripts/screening.py status records.json` shows progress at any time. Never fill in a decision the reviewer did not give.

## 4. Retrieve the full texts

```
python3 scripts/screening.py included records.json --stage ta --out to_retrieve.json
```
Then follow `references/access-download.md` with `to_retrieve.json`. "maybe" records go on to full text, as is usual.

## 5. Full-text screening

The same two ways, with `--stage ft`. A full-text exclusion needs a reason (PRISMA reports them by reason); suggest the reviewer reuse a short fixed list (wrong population, wrong outcome, wrong study design, not peer reviewed, full text not in English) so the counts group cleanly. Resolve every "maybe" before the final diagram.

## 6. PRISMA numbers and the report

```
python3 scripts/screening.py prisma records.json --log search_log.json --manifest "<project>/papers/manifest.json"
python3 scripts/build_report.py --log search_log.json --records records.json --manifest "<project>/papers/manifest.json" --out "<project>/search_report.pdf"
```
`screening.py prisma` fills the screening boxes from the recorded decisions and leaves anything unfinished as "to be completed". The report says the reviewer made every screening decision. Records without a DOI cannot be matched to a downloaded file, so check the "not retrieved" count against the papers folder if many records lack DOIs.
