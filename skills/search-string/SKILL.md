---
name: search-string
description: 'Use this skill for anything involving Boolean search queries for academic literature databases: Scopus (users may say "Opus"), Web of Science (WoS) and Google Scholar. Build ready-to-paste search strings, keywords or a concept table from a research title, topic, question or SLR title. Also use it to debug, fix, shorten, widen or narrow a search the user already wrote, including when a database rejects it with "invalid query", a syntax error, zero results, or too many or too few hits. Handles field tags (TS=, TITLE-ABS-KEY, PY=), AND/OR/NOT logic, truncation (*), wildcards (?), phrase quotes, country niches, date limits, Malay or other local-language strings, and exporting the search strategy as a Word file. Not for screening abstracts, general Boolean or SQL help, or finding specific papers.'
---

# search-string

Turn a research title or topic into search strings that can be pasted straight into Scopus, Web of Science and Google Scholar. The three databases use different syntax, so each gets its own version of the same logic.

"Opus" almost always means Scopus. Use Scopus without correcting the user.

## What you need from the user

Take it from the message and the conversation first. Ask at most one short question, and only if something essential is missing. A title that is vague but usable is not missing: make sensible choices, say what you assumed, and let the hit counts steer the next round.

- **Topic or title** (required).
- **Niche** such as a country or sector (optional, e.g. "Malaysia only"). It becomes its own concept.
- **Date range** (optional). Default to the last five calendar years including the current one, working from today's date (in 2026 that is 2022 to 2026). The script does this when `years` is left out. Say which range you used.
- **Field** (optional). Infer it from the topic. It only affects which synonyms and journal vocabulary you choose.

## Workflow

1. **Split the topic into 3 or 4 concepts.** Mirror the lecturer-style table: Concept 1 AND Concept 2 AND Concept 3 (AND Concept 4 for the niche).
   - Concept 1: the main subject (e.g. OTT streaming, newsrooms).
   - Concept 2: the action, outcome or process (e.g. adoption, continuance, transformation). Use many synonyms here, the way a verb list like enhance / improve / strengthen / boost works.
   - Concept 3: the population or context (e.g. consumers, journalists).
   - Concept 4: the niche, if any.
2. **Choose 6 to 14 terms per concept.** Every term should earn its place.
   - Put multi-word terms in double quotes: `"video on demand"`.
   - Use truncation for word families: `adopt*` finds adopt, adoption, adopting. Keep at least 3 characters before the `*`.
   - Use `*` for spelling variants inside a word: `behavio*r` matches behavior and behaviour in both Scopus and Web of Science. `?` means exactly one character, so `digitali?ation` works but `behavio?r` misses the American spelling.
   - Quoted phrases need care in Web of Science, because it does not match plurals or UK/US spellings inside quotes. Truncate the last word (`"streaming service*"`) or use `?` for spelling (`"news organi?ation*"`). Both Scopus and Web of Science accept `*` and `?` inside quotes; `$` is Web of Science only and is not allowed in quotes. Google Scholar accepts none of these, so write the variants out there.
   - Add acronyms, brand names and local outlet names when the niche is a country. Studies often name the outlet or place instead of the country.
3. **Write a spec file and run the script.** Save the concepts as JSON (see `examples/example_spec.json`) and run:
   ```
   node scripts/search_tool.js strings spec.json
   ```
   It builds the Scopus and Web of Science strings, prints character counts and flags common mistakes (unbalanced quotes or brackets, curly quotes pasted from a phone or Word, operator words inside a term, wildcards that are too short, Scholar strings that are too long or use `*`). Read the warnings and fix the spec until they are gone or you can say why one does not apply. If the script reports an error instead, it is telling you what is wrong with the spec file; fix that and rerun. If Node is not available, build the strings by hand with the formula in `references/syntax.md` and check them against the same rules.
4. **Write the Google Scholar versions by hand.** Scholar has no truncation or wildcards and cuts queries at about 256 characters, so write two short versions that each pick the strongest spelled-out terms. Version A uses the core subject, outcome and population terms. Version B swaps in the niche, brand and outlet names so that it finds papers that name the place or platform but not the general concept. Put them in the spec under `scholar` and rerun the script to check the length.
5. **Add a separate local-language string** when the niche is a country whose research is often published in its own language (for Malaysia, many Jurnal Komunikasi papers have Malay titles). Put it under `malay`, or under `local` with `localLanguage` set (for example `"Indonesian"`) for any other language. Tell the user to run it as its own search and merge the results. Do not join it to the English string with AND, because then every record must contain both English and local terms and most good papers drop out.
6. **Give the user the result.** Read `references/syntax.md` if you are unsure about a database feature.

## When the user brings their own string

Run it through the checker before you change anything, so you fix what is actually broken and not what looks odd:

```
node scripts/search_tool.js check "their string here" [scopus|wos|scholar]
```

It guesses the database from the field codes when you leave it out. Then:

- **Too many results:** tighten Concept 2 or the date range, or drop broad stems such as `innovat*` and `user*`.
- **Too few results:** drop Concept 3 first, then widen the niche terms, then the date range.
- **Shorten it:** cut the weakest terms from the longest concept, not the shortest. Keep all the concepts.
- **Mixed up databases:** a Scopus string pasted into Scholar, or `TS=` inside Scopus, is the most common reason for zero results.

Show what you changed and why in one or two lines, then give the new string in a code block.

## Other databases

PubMed, IEEE Xplore, ProQuest, EBSCO and similar use different field tags and wildcard rules, and this skill has not verified them. Still build the concept table, since the logic carries over, then give the Boolean skeleton and say the user needs to adapt the field tags and wildcards to that database's help page. Do not invent field codes.

## Reply format

Keep it short and easy to copy on a phone:

- One line listing the concepts and the date range used.
- A separate code block for each: Scopus, Web of Science, Google Scholar A, Google Scholar B, and the local-language string if there is one.
- Two or three lines on what to do next. Always include: run the strings, then send back the hit counts so you can tighten or widen them.

Do not claim the strings were tested. You cannot open Scopus or Web of Science, so say the user has to run them. As a rough guide, Scopus or Web of Science returning between about 100 and 2,000 records is workable for a literature review. Above that, tighten Concept 2 or the date range. Below about 50, drop Concept 3 first, then widen the niche terms.

## Word file (only when asked)

If the user asks for a Word file, a table, or "the document", build it with:
```
node scripts/search_tool.js docx spec.json output.docx
```
Pass an array of specs to put several titles in one file. The file has, per title, the concept table in lecturer-slide format and a Search result table (database, date searched, filters, syntax used, link). Fill `searchDate` and `links` in the spec if the user gives search links. The script creates the output folder if it is missing.

Where to save it depends on where you are running. In claude.ai, save to `/mnt/user-data/outputs/` and share it with `present_files`. In Claude Code or Cowork, save it in the working folder (or wherever the user said) and give the path. If the `docx` module is missing the script says so; install it with `npm install docx`, or follow the docx skill and keep the same layout. The strings in the reply do not depend on the Word file, so give them either way.

## Things that went wrong before, so check for them

- **Google Scholar "Review articles" filter.** A Scholar link containing `as_rr=1` has the Review articles filter on, which hides most primary studies. If the user shares a Scholar link, check for it and tell them to switch it off.
- **Identical results for different Scholar versions** usually mean one block is limiting the search, often because English and local-language strings were joined with AND.
- **Scopus and Web of Science links from a university proxy** only open while logged in, so you cannot read the result counts. Ask the user for the counts.
- **Concept 4 is a topic filter.** Do not replace it with an affiliation-country filter, which finds local authors writing about other countries and misses foreign authors writing about the niche.
- **Curly quotes.** Text copied from a phone, Word or a chat app often carries curly quotes. Scopus and Web of Science do not read them as phrase marks, so the phrase turns into loose words. The script converts them in a spec and the `check` mode flags them in a pasted string.
- **Lower-case `or` and `and`.** Scholar only reads `OR` in capitals, and the other two databases are safest with capitals too.
- **Scholar shows at most the first 1,000 results** of any query, so record how many were screened.
