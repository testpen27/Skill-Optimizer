# Reading a paper and writing its cells

The failure this file exists to stop: **the paper says A and B, and the cell
says A, B and C.** C is usually not invented from nothing. It is the part that
"normally" comes with A and B: the questionnaire that is usually validated,
the effect that is usually significant, the students who are usually
secondary-school, the theory that is usual in the field. Filling that gap
makes a cell read well and makes it false.

The defence is order: **save the text, quote it, write only from the quotes,
check the quotes by script, then check the writing by a second reader.**
Nothing is written from memory of the paper, of the field or of the authors'
other work.

## 1. Get the text and save it unedited

- Use the full text where there is one (a PDF the user gives, an open-access
  copy, `firecrawl_research_read_paper`). Save the text you read to
  `papers/<id>.txt` (or `.md`) exactly as extracted. This file is what the
  quotes are checked against.
- Record `source_basis` for the paper: `full text`, `partial` (some sections
  missing, e.g. a preview) or `abstract only`. It appears in the workbook's
  Summary sheet, so the reader knows how much each row can be trusted.
- PDF text can garble tables, superscripts and hyphenated line breaks. If a
  number you need sits in a garbled table, look at the page itself (render it
  as an image) before quoting it, and quote the number as the page shows it.
- Abstract only: fill only what the abstract states. Results and discussion
  are usually "Not retrieved" from an abstract; say so rather than stretch it.

## 2. Reading: collect quotes before writing anything

For each column, find the passage that answers it and copy it **verbatim**
into `evidence`, with its location (section heading, page if known). Keep
each quote short (a phrase to two sentences); use `...` to skip words inside
one passage. Where to look:

| Column | Look in | Quote |
|---|---|---|
| Introduction | End of the introduction: aim, research question, hypotheses; the problem statement | The stated aim, question or hypothesis |
| Methodology | Methods: design, participants (who, how many, where, when), instruments, procedure, analysis | Each of those the paper reports |
| Theory | Where the paper says what frames or guides **this** study ("drawing on", "guided by", "our framework") | The sentence naming the framework. A theory only cited in the literature review is **not** the paper's theory |
| Results | The Results section and its tables, not the abstract or the discussion | Findings with the statistic exactly as printed (n, %, M, SD, β, r, OR, p, CI), including null results that are main findings |
| Discussion | Discussion and conclusion: the authors' interpretation, stated limitations, stated implications | The authors' own claims |
| Type | Methods | The sentence that shows the design; "Mixed-methods" only if both strands are reported |

Rules while reading:
- **Absence is a finding.** If the paper does not report a sample size, a
  setting or a theory, record that it is not reported. Do not infer it.
- **The body beats the abstract. Write every cell from the body, and quote
  for the overclaim check.** Besides the column quotes, collect two more lists
  of verbatim quotes, exhaustively, because the next step sees only these and
  can use only what you quote:
  - `abstract_claims`: every abstract sentence that states a finding, effect,
    conclusion or recommendation;
  - `caveats`: every sentence anywhere in the body that restricts or weakens a
    claim: limitations, null or non-significant results, partial or mixed
    effects, scope restrictions (a subgroup, a time point, "only"), "cannot",
    "not", "although", "albeit", "however", differences from what the abstract
    or aims say (another age range, sample size or number of sites), and
    statements that an effect cannot be attributed to the intervention alone.
  Do not judge overclaims yourself and leave `overclaims` out: a separate
  pairing step (`overclaim-pairing.md`) matches each abstract claim to a body
  quote that shows the gap, and the workbook then shows the matching sentence
  of the cell in dark-yellow text with a hover note quoting both.
- **Keep the paper's words for claims.** Quote "associated with", not your
  reading of it as "caused".
- One paper at a time. Never carry a detail from one paper into another's row.

## 3. Writing: compress, never complete

Each cell is written **only** from that paper's quotes. Every sentence must be
traceable to at least one quote.

Allowed: shortening; merging two quotes from the same paper; reordering;
replacing jargon with a plain word of the same meaning; changing active to
passive; rotating the subject ("the authors", "the researchers", "the study",
"the team", or the finding itself) so cells do not all start alike.

**Not allowed, because each one is the ABC failure:**
- adding a cause, mechanism, consequence, implication, comparison or
  recommendation the quotes do not state;
- adding a population, setting, country, date, instrument property
  ("validated", "reliable"), sample feature or design label the quotes do
  not state;
- strengthening a claim: dropping a hedge ("may", "suggests", "appears"),
  turning "associated with" into "leads to", "some" into "most", a
  non-significant trend into a finding;
- generalising beyond the sample ("teachers" when the paper studied 12
  teachers in one district);
- any number not in the quotes, and any number computed, rounded or converted
  from them (no percentages from counts, no averages);
- a theory the paper does not name as its own;
- the reviewer's opinion. The Discussion cell condenses **the authors'**
  conclusion; the reviewer's own reading belongs only in the synthesis
  paragraph, worded as the synthesis.

When the quotes are thin, **write less**. A short true cell beats a full
guessed one; an empty cell prints as "Not retrieved" (or "Not explicitly
stated" for theory), which is a correct answer.

Style, after accuracy: third person; about 40 words for introduction, 50 for
methodology, 25 for theory, 60 for results and discussion; no page numbers
except a short direct quote kept in quotation marks with its page.

## 4. Checking by script

```
python3 scripts/check_evidence.py lrm.json --papers <folder with papers/<id>.txt>
```

It fails the run when a quote is not found in the saved text (a misquote or
an invented quote), when a cell contains a number that none of the paper's
quotes contains, or when a filled cell has no quotes at all. It warns when a
quote is hedged and the cell is not, and when a cell uses causal wording
("leads to", "improves", "impact on") that the quotes do not. Fix every
failure by cutting or narrowing the cell, never by adding.

## 5. Verifying: a second reader checks every sentence

After the script passes, a second reader (a different model, see
`model-routing.md`) gets only the quotes and the cells, never the drafter's
reasoning, and checks each sentence:

1. Is every part of it stated in the cited quotes?
2. Does it add anything (cause, scope, population, property, number, theory)?
3. Is it stronger than the quote (hedge dropped, association made causal)?
4. Are the numbers identical, with the same statistic?
5. Is the scope the same (sample, setting, time)?

Verdict per sentence: **keep**, **cut**, or **narrow** (rewrite closer to the
quote's own wording). The verifier also checks each recorded overclaim: the
abstract's quote really claims more than the body's quote, and the cell's
yellow words follow the body. An overclaim that is not one is removed. The fix is always to remove or narrow, never to add.
The session applies the verdicts, reruns `check_evidence.py`, then drafts the
chat table for the user.

## Synthesis and concept matrices

The same discipline applies. A synthesis-matrix cell is written only from
that paper's quotes about that theme. A concept-matrix X needs one quote
showing the paper actually deals with the concept (a passing mention is not
enough). Both are verified like LRM cells.
