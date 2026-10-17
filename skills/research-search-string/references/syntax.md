# Syntax reference

Checked against the Scopus Support Center, Clarivate's Web of Science search rules and library guides in October 2026. Interfaces change, so if a string behaves oddly, ask the user to check the database's own help page.

| Feature | Scopus | Web of Science | Google Scholar |
|---|---|---|---|
| Boolean | AND, OR, AND NOT | AND, OR, NOT (not case sensitive) | OR (capitals); AND is implied; minus sign excludes |
| Truncation `*` | Zero or more characters (`adopt*`) | Zero or more characters | Not supported |
| Wildcard `?` | Exactly one character (`digitali?ation`) | Exactly one character | Not supported |
| Wildcard `$` | Not supported | Zero or one character (`flavo$r`); not allowed inside quotes | Not supported |
| Wildcard inside a word | `behavio*r` works | `behavio*r` works | Not supported |
| Wildcard at the start of a word | Allowed; needs 3 or more other characters | Allowed in Topic and Title; needs 3 or more characters after it | Not supported |
| Phrase | `"loose phrase"` (words together, fixed order, wildcards and plurals allowed); `{exact phrase}` (no wildcards, no variants) | `"exact phrase"` (`*` and `?` allowed inside; no plurals or spelling variants) | `"exact phrase"` |
| Plurals and UK/US spelling | Added automatically for single words and loose phrases | Added automatically for single words only; switched off by quotes and by wildcards | Handled by Google, not controllable |
| Search field | `TITLE-ABS-KEY( )` | `TS=( )` (title, abstract, author keywords, Keywords Plus) | Full text by default; `intitle:` limits to title |
| Date limit | `PUBYEAR > 2021 AND PUBYEAR < 2027` | `PY=(2022-2026)` | Custom range in the left menu (`as_ylo`, `as_yhi` in the URL) |
| Proximity | `W/n` (within n words, either order); `PRE/n` (first term comes first) | `NEAR/n` | Not supported |
| Hyphens | Treated as spaces in loose phrases; kept in `{exact}` phrases | Treated as spaces; search the term with and without the hyphen | Not checked |
| Length | Long strings are fine | Long strings are fine; only an All Fields search is limited to 100 operators | Cut off at about 256 characters |

## Building the strings by hand

With concepts C1, C2, C3 and a year range y0 to y1, each concept is its terms joined with `OR` in brackets:

- Scopus: `TITLE-ABS-KEY((C1 terms) AND (C2 terms) AND (C3 terms)) AND PUBYEAR > y0-1 AND PUBYEAR < y1+1`
- Web of Science: `TS=((C1 terms) AND (C2 terms) AND (C3 terms)) AND PY=(y0-y1)`

Always keep the brackets. Web of Science resolves operators in the order NEAR, SAME, NOT, AND, OR when there are none, so a string without brackets does not mean what it looks like.

## Plurals and spelling inside phrases

A bare word such as `adoption` is lemmatized in Web of Science, so it finds adoptions too. A quoted phrase is not: `"streaming service"` will not find "streaming services", and `"news organisation"` will not find "news organization". Write `"streaming service*"` and `"news organi?ation*"`. Scopus is more forgiving with loose phrases, but the same strings work there, which keeps the two databases consistent.

## Why `behavio*r` and not `behavio?r`

`?` means exactly one character. "behaviour" has a character between the o and the r, but "behavior" does not, so `behavio?r` misses the American spelling. `behavio*r` matches both. In Web of Science only, `behavio$r` also works.

## Where to paste

- **Scopus:** Advanced search (the field code is already in the string).
- **Web of Science:** Advanced search, Core Collection.
- **Google Scholar:** the search box. Set the date range in the left menu. Scholar shows at most the first 1,000 results of any query, so record how many were screened.

## Tuning

- Too many results: tighten Concept 2, narrow the date range, or drop broad truncations such as `innovat*` and `user*`.
- Too few results: drop Concept 3 first (Concept 2 often implies it), then widen the niche terms, then widen the date range.
- Noisy acronyms (OTT, RTM): keep the AND with other concepts, review the first 50 records, and only then consider an AND NOT.
- Do not copy a Scopus or Web of Science phrase that contains `*` or `?` into a Scholar string. Write the variants out.

## Local-language supplement

For a country niche, a short second string in the local language catches papers in local journals. Keep it separate from the English string and merge the results. Example (Malaysia, streaming):
`(OTT OR penstriman OR Netflix) AND (pengguna OR penonton OR khalayak OR penerimaan OR penggunaan OR kepuasan) AND Malaysia`
