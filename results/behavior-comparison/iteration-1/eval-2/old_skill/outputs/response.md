Fixed. Two things were wrong, and neither was the brackets (they were already balanced).

1. The curly quotes. Your string has “social media” and “body image” in Word-style curly quotes. Scopus only recognises straight quotes ("). Curly quotes cause the error, and when they are left in, they are searched as odd characters or split the phrase, which gives 0 results.
2. `behavio?r`. In Scopus, `?` means exactly one character, so it matches "behaviour" but not "behavior". Use `*` instead: `behavio*r` matches both.

I also changed `or` to `OR` and wrote `AND PUBYEAR` the same way. Scopus accepts lowercase, but capitals are safer.

Scopus (paste as plain text):

```
TITLE-ABS-KEY(("social media" OR facebook OR instagram) AND (adolescen* OR teen*) AND ("body image" OR behavio*r)) AND PUBYEAR > 2020
```

Notes:
- `PUBYEAR > 2020` means 2021 to now. I kept your range. For the last five calendar years including 2026, use `PUBYEAR > 2021`.
- If you paste from Word or Google Docs, it will turn the quotes curly again. Paste into Notepad first, or retype the quotes in Scopus.
- Your concepts are narrow on the third block. "behavior" is very broad, so you may get thousands of records. If so, tighten it, for example "body image" OR "body dissatisfaction" OR "self-esteem".

I can't open Scopus, so I haven't run it. Please run it and send back the hit count. About 100 to 2,000 records is workable, and I can tighten or widen it from there.
