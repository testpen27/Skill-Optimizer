# Research gaps (Summary sheet)

Two different things, kept apart:

- **The LRM column "Limitations and future research"** is what the authors of
  each paper say: their stated limitations and the future work they propose.
  It is read like every other column (`reading-and-writing.md`): the `haiku`
  reader quotes it, the cell is written only from the quotes, the script checks
  the quotes, the `opus` verifier checks the sentences. A paper that states
  neither prints "Not explicitly stated". Discussion keeps the authors'
  conclusion and implications; limitations go in this column only.
- **The gap list on the Summary sheet** is the reviewer's reading across the
  papers. It is interpretation, so it is labelled that way in the workbook. It
  is written by a `sonnet` helper and checked by a separate `opus` helper.

The gap list is always scoped to the papers in the matrix. "Among these 12
papers, none follows pupils beyond one school year" is a finding about the set;
"nobody has studied this" is a claim about the whole literature that a set of
papers can never prove. The build warns about wording that sounds like the
latter.

## What the writer sees

Never the papers. One call for the whole set (split into batches of about 25
papers if the set is larger), with:

```
{"title": "<the user's research title or aim>",
 "papers": [{"id": "tan2024", "year": 2024, "type": "Quantitative",
             "methodology": "<the methodology cell>",
             "limitations": "<the verified limitations cell>"}]}
```

Pass only cells that passed `check_evidence.py` and the verifier.

## Writer prompt (`sonnet`)

```
You write the research-gap list for a literature review matrix. You have the
user's research title and, for each paper, its type, its methodology cell and
its limitations-and-future-research cell. You do NOT have the papers and you
must not use anything you know about the field: use only these cells.

Write between 3 and 8 gaps (fewer if the cells support fewer). Each gap is ONE
sentence of at most 35 words, in the third person, and has:
- "kind": "stated by authors" when the authors of at least one paper say it
  themselves (a limitation or a direction for future work), or "across papers"
  when it is a pattern visible only by comparing the rows (for example, every
  sample is from one country, or every outcome is self-reported);
- "papers": the ids of every paper whose cell shows it. Never a code like P01;
- "basis": which cells it rests on, for example "limitation cells of tan2024 and lee2023".

Rules:
1. Scope every gap to this set: "Among these N papers, ..." or "The authors of
   tan2024 and lee2023 call for ...". Never write "no study", "nobody", "the
   literature lacks" about the whole field.
2. A gap must be visible in the cells you were given. Do not add a gap because it
   is a usual gap in this field. Do not add a cause, a remedy or a study design.
3. If you say "most", "several", "all" or "none", the ids you list must show it.
4. Prefer gaps that two or more papers show. Write a gap that rests on one paper
   only when it bears directly on the user's title, and then do not just repeat
   that paper's limitation: the paper's own cell already says it. Prefer gaps
   that matter for the user's title, but only when the cells show the link. Do not
   invent relevance.
5. Plain academic wording, no "I", no "we".
6. Describe a paper with the words its own cell uses. Do not relabel it: do not
   call a study "self-reported", "quasi-experimental" or "single-site" unless
   its cell says so.
7. Do not use "only", "single", "all", "each", "every" or "none" unless every
   paper in the input supports it. If unsure, name the papers instead.
8. One limitation or one direction per gap. Do not join two different
   limitations into one statement, and add no clause that explains or draws a
   consequence ("because", "since", "which", "so").
9. "Call for" needs a call in the cell ("future studies should", "is needed").
   A limitation alone is not a call for anything.

Reply with ONE JSON object only, no fence:
{"gaps":[{"gap":"","kind":"stated by authors|across papers","papers":["id"],"basis":""}]}

INPUT
```

## Checker prompt (`opus`, a different helper from the writer)

```
You check a research-gap list written by another model for a literature review
matrix. You have the same input it had (the user's title and each paper's type,
methodology cell and limitations cell) and its gaps. You do NOT have the papers.

For each gap, in order (ids gap.1, gap.2, ...), decide:
1. Do the cited papers' cells show it? Check every cited id.
2. Is it scoped to this set of papers, with no claim about the whole field?
3. If it says "most", "several", "all", "none" or gives a count, is that true of
   the cells you have? Look at the papers it does NOT cite: does any of them
   contradict "none" or "all"?
4. Is "kind" right? "stated by authors" needs a cell where the authors themselves
   say it; otherwise it is "across papers".
5. Does it add a cause, remedy, study design or relevance the cells do not show?

Verdict per gap: "keep", "narrow" (give the rewritten gap in "narrowed", closer
to what the cells show, with kind and papers unchanged) or "cut". You never add
a gap and never add words that the cells do not support.

Reply with ONE JSON object only, no fence:
{"verdicts":[{"id":"gap.1","verdict":"keep|narrow|cut","reason":"one short sentence","narrowed":""}]}

INPUT
```

Append the same input JSON and then `{"gaps": ...}` (the writer's gaps) to the
checker prompt. Write the replies to `gaps_out/gaps.json` and
`gaps_check/verdicts.json`, then:

```
python3 scripts/apply_gaps.py lrm.json --gaps gaps_out/gaps.json --verdicts gaps_check/verdicts.json
```

`apply_gaps.py` writes only what the checker kept or narrowed, drops any paper
id that is not in `lrm.json`, and refuses to write without verdicts.

## What to expect and what it cannot do

The checker can only keep, narrow or cut. It cannot add a gap the writer missed,
so the list can be thin. If the user wants a deeper list, say so and offer a
second pass with `opus` as the writer (and a separate `opus` check), at higher
cost. The list is a set of proposals for the user to judge against their own
study, not a finding.
