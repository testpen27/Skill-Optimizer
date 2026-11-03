You want your Web of Science string for "mobile learning" with nursing/midwifery terms, 2020 to 2024, fixed so it runs.

Three things were wrong:
- Curly quotes around "mobile learning" (common when pasting from Word or a phone). Web of Science does not read them as a phrase.
- No AND between the topic part and PY=.
- The year range needs brackets: PY=(2020-2024).

Corrected string (paste into Web of Science Advanced search, Core Collection):

```
TS=("mobile learning" AND (nurs* OR midwi*)) AND PY=(2020-2024)
```

I ran it through the syntax checker and it reports no warnings. I changed only the syntax, not your terms or years. If you want more or fewer results, I can widen or narrow it.
