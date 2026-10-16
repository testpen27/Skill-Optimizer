Your brackets were actually balanced. The problem was two other things:

- **Curly quotes** (“ ”): Scopus does not read them as phrase marks, so that is the likely cause of the error. They usually come from Word or a phone. I replaced them with straight quotes.
- **Lower-case `or`** in `(adolescen* or teen*)`: I changed it to `OR`. Scopus can treat the lower-case word as a search term instead of an operator.

I also changed `behavio?r` to `behavio*r`. In Scopus, `?` means exactly one character, so `behavio?r` finds only "behavior" or "behaviour" if there is one letter between "o" and "r". It does not match both spellings. `*` matches both. I kept your date limit (`PUBYEAR > 2020` means 2021 onwards).

```
TITLE-ABS-KEY(("social media" OR facebook OR instagram) AND (adolescen* OR teen*) AND ("body image" OR behavio*r)) AND PUBYEAR > 2020
```

The checker found no warnings on this string, but I can't open Scopus, so you need to run it. Send me the hit count. If it is over about 2,000, I can tighten the "behavior" terms. If it is under about 50, I can widen the terms (for example add "social network*", tiktok, youth, "young people").
