# Branch: search strings

Build database-ready Boolean strings for Scopus, Web of Science and Google Scholar, or fix a string the user already wrote. Every other branch that searches a database starts here.

## Building strings

Steps 1, 2, 5 and 6 below go to a helper on `opus` (see `references/model-routing.md`): give it the intake answers and these rules, and have it return the spec JSON. Then run the checker yourself and fix what it flags.

1. **Split the topic into concepts**, usually 3 or 4: Concept 1 the main subject, Concept 2 the action or outcome (many synonyms), Concept 3 the population or context, Concept 4 the niche. Add a fifth when the title names one more essential element (for example "rural" in "older adults in rural areas"); do not drop a part of the title to stay at four. Each extra concept narrows the search, so put it only in the narrow tier if it would cut the hits too far.
2. **Choose 6 to 14 terms per concept.**
   - Quote multi-word terms: `"video on demand"`.
   - Truncate word families: `adopt*`. Keep at least 3 characters before `*`.
   - Use `*` for spelling variants inside a word: `behavio*r`. `?` is exactly one character, so `behavio?r` misses "behavior".
   - In Web of Science a quoted phrase does not match plurals or UK/US spellings, so truncate the last word (`"streaming service*"`) or use `?` (`"news organi?ation*"`). Scopus and Web of Science both accept `*` and `?` inside quotes; `$` is Web of Science only. Google Scholar accepts none of these.
   - When the niche is a country, add place, brand and outlet names: studies often name the outlet, not the country.
3. **Write the spec** (see `examples/example_spec.json`) with `ranges` for the year ranges from the intake and, if the default does not fit, `tiers`:
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
   Add the intake answers to it as `"profile": {"Field": "...", ...}`.

Read `references/syntax.md` when unsure about a database feature.

## Reply format

Easy to copy on a phone:
- One line with the concepts, tiers and year ranges.
- A code block per string: Scopus and Web of Science per tier, Scholar A and B, and the local-language string.
- Two or three lines on what happens next (run them, or let Claude run them in the browser).

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
