# Pairing overclaims (a Sonnet helper, quotes only)

An overclaim here means the abstract claims more than, or something different
from, what the body reports. The pairing helper decides this from quotes. It
never sees the paper, so it can only use what the reading helper quoted, and it
must not use outside knowledge.

## Input, per paper (the session builds it from the reading helper's file)

```
{"abstract_claims": ["verbatim abstract sentences"],
 "body_quotes": {"caveats": [...], "results_evidence": [...], "discussion_evidence": [...]},
 "cell_sentences": [{"id": "results.2", "sentence": "..."}, ...]}
```

`cell_sentences` are the sentences of the paper's introduction, methodology,
theory, results and discussion cells, split with
`split_sentences` in `scripts/common.py` (ids are `<column>.<number from 1>`).

## Prompt for the helper

> You check whether a paper's abstract claims more than its body reports. You
> do NOT have the paper. You have (1) the abstract's claim sentences and (2)
> verbatim quotes from the paper's body: caveats, results and discussion
> evidence. Use only these.
>
> For each abstract claim, decide whether one of the provided BODY quotes
> clearly shows that the paper reports less than, or something different from,
> the claim: a smaller or narrower effect, a non-significant or partial result,
> a restricted subgroup or time point, a statement that the effect cannot be
> attributed to the intervention alone, or a different number, age range or
> sample than the abstract states. Flag only when a provided body quote shows
> the gap. Never flag on suspicion, and never use outside knowledge. The body
> text you cite must be copied exactly from the provided quotes.
>
> You are also given the sentences of the matrix cells (cell_sentences, each
> with an id). For every overclaim you flag, give "cell_sentence_id": the id of
> the cell sentence that reports the finding the body quote describes (that
> sentence will be coloured for the reader), or null if no cell sentence
> reports it. Never invent an id.
>
> Reply with ONE JSON object only, no fence, no text before or after it:
> `{"overclaims":[{"abstract":"exact abstract sentence","body":"exact provided
> body quote","body_loc":"","cell_sentence_id":"results.2","why":"one
> sentence"}], "unsettled":["abstract sentences that might overclaim but no
> provided body quote settles it"]}`

The helper writes its reply to `pairing_out/<id>.json` and returns a one-line
status. Replies sometimes add text or correct themselves with a second JSON
object; `apply_overclaims.py` uses the last object that has an `overclaims` key.

## After the helper

```
python3 scripts/apply_overclaims.py lrm.json --from pairing_out/ --papers papers/
```

It drops a pair whose quote is not in the saved paper text, finds the cell
sentence to colour, keeps pairs without a usable sentence as notes on the
Summary sheet, and lists the `unsettled` claims there too. Then run
`check_evidence.py`, and let the `opus` verifier check each remaining pair: the
abstract's quote really claims more than the body's quote, and the coloured
sentence follows the body. A pair that is not a real overclaim is removed.

## What to expect (four papers, one run each)

All 5 real overclaims were flagged. About 5 of the 14 flags were doubtful
(typically an abstract that already hedges its claim), which is why the verifier
checks them and the hover note always shows both quotes. The doubtful flags are
a cost of recall; a missed overclaim is the worse error.
