# Verification helper (`opus`)

One helper does the whole check, in **one call with two passes**: it verifies
every sentence against the quotes, then attacks its own "keep" verdicts. There
is no separate challenger step. Measured on four papers
(`results/2026-11-26-overclaim-pipeline-and-verifier-test/`):

- Planted errors, blatant (20) and subtle (48, such as a dropped qualifier or a
  number moved to the wrong group): the combined call and a plain Opus verifier
  caught the same ones (98 percent of the subtle ones, both). One subtle error
  was missed by every run: a qualifier dropped from a theory sentence
  ("prospective teacher knowledge" became "teacher knowledge").
- One real, unplanted error (a sub-result stretched to the whole): the
  combined call found it in 6 of 6 runs, the plain verifier in 1 of 5.
- Cost: about 27 percent more output than the plain verifier, and about half the
  price of verifying and then challenging in a second call.

## Input

Give the helper, in its prompt (it cannot see the conversation), one JSON
object per paper and nothing else about the paper:

```
{"sentences":[{"id":"methodology.1","sentence":"..."}],
 "quotes":{"introduction":["..."],"methodology":["..."],"theory":["..."],
           "results":["..."],"discussion":["..."]},
 "overclaims":[{"field":"results","abstract":"...","body":"...","cell_text":"..."}]}
```

Split each cell into sentences with `split_sentences` (`scripts/common.py`) so
ids match the pairing step. About 10 papers per helper. Never include the
reader's reasoning. Write the verdicts to `verify_out/<id>.json`; the session
applies them (cut, or narrow towards the quote) and reruns
`check_evidence.py`.

## Prompt

```
You are the verifier in a literature-review tool, and you also act as your own challenger, in one reply. A reader wrote the sentences of one matrix row from the verbatim quotes of one paper. You have the sentences and the quotes; you do NOT have the paper. Check every sentence against the quotes of its own column (and any other column's quotes if the sentence is clearly about the same fact).

Do two passes before you answer.

PASS 1, verify. For each sentence decide:
1. Is every part of it stated in the quotes?
2. Does it add anything the quotes do not state (a cause, scope, population, setting, instrument property such as "validated" or "random", number, theory, recommendation or implication)?
3. Is it stronger than the quotes (a dropped hedge, association worded as cause, wider scope)?
4. Are all numbers identical to the quotes, with the same statistic, outcome, group and time point?
5. Is the scope the same (sample, setting, time)?

PASS 2, argue against yourself. Take every sentence you marked "keep" and attack it as a hostile reviewer would: find the word, number, qualifier or scope that no quote contains, a quote about one sub-result stretched to the whole, a statistic that belongs to a different outcome, group or time point, a hedge that was dropped. A "keep" stands only if the attack fails. Also re-read every "cut" or "narrow": if the quotes do fully support the sentence, change it back to "keep".

Verdict per sentence: "keep" (fully supported), "cut" (not supported, or contradicted), or "narrow" (partly supported: say what to remove). The fix is only ever to remove or narrow, never to add. A theory sentence is supported only if a quote names that theory as the paper's own. Every dispute you make must rest on an exact quote or exact words of the sentence; if you cannot cite them, the sentence stays "keep".

Reply with ONE JSON object only, no fence, no extra text:
{"verdicts":[{"id":"methodology.1","verdict":"keep|cut|narrow","reason":"one short sentence","support":"for keep: the exact quote that supports it; for cut or narrow: the exact words of the sentence that are unsupported","attack":"for keep: the strongest objection you tried and why it failed (one short sentence); otherwise empty"}]}
Give one verdict for every sentence id.
```

Append the JSON after the prompt. Parse the last JSON object with a
`verdicts` key. Overclaim pairs go in the same call: add to the prompt "Also
check each overclaim: does the abstract quote really claim more than the body
quote, and do the cell_text words follow the body? Add an entry with
`id` `overclaim.N` and verdict `keep` or `cut`." (a `cut` removes the yellow
flag). The overclaim part of the prompt was not in the measured combined run.

## What to expect

About one in five of the untouched sentences get a "narrow" or "cut" verdict
(11 of 50 in the test). Mostly the content is true to the paper but no quote
backs it, which is the right outcome: the sentence is narrowed to what the
quotes show, or the reader quotes more. Do not argue these back to "keep"
without a quote.
