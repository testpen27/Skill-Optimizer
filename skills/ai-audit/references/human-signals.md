# Human signals, ineffective indicators, and what never to inject

Three lists. The first is evidence pointing away from AI, which belongs in every audit. The second is patterns that look like evidence and aren't. The third is the failure mode of the revision itself.

## Signs of human writing

From Wikipedia's *Signs of AI writing*, drawn from roughly twenty-five years of observed editing. LLM prose defaults to a stiffly formal, neutral register and avoids these constructions, even though they are ordinary and sometimes preferred by style guides. Their presence is evidence; their absence across a long piece is worth noting.

- **Plain copulatives.** "There is a", "it has a" — where a model would write "serves as" or "features".
- **Plain verbs over stiff ones.** Wrote rather than authored, moved rather than relocated, used rather than utilized, died rather than passed away.
- **Superlative or definitive claims.** "One of the best", "was the first". Models hedge these away.
- **Hedging qualifiers and intensifiers.** "Very", "perhaps", "tends to".
- **Wordy filler constructions.** "As a result of", "in order to", "the fact that".

Also evidence:

- **Age.** Text that existed before 30 November 2022 can be ruled out. If a document has version history, use it.
- **A writer who can explain their own choices.** Someone who made a real mistake can usually say how it happened.
- **Specific, checkable, slightly odd detail** — a street name, an exact figure, an aside about the lawyer upstairs from the dentist.
- **Unresolved tension or mixed feelings**, an argument that undercuts itself, a self-correction mid-sentence.
- **Era-bound references** — slang, memes, in-jokes that map to a particular year and subculture.

This list is the reason the rewriting rules forbid a mechanical de-AI pass. Cutting "in order to" to "to", deleting hedges, and flattening superlatives removes exactly the markers that distinguish a human draft, which is worth knowing whether the goal is to pass as human or simply to write well.

## Ineffective indicators

Wikipedia lists these explicitly as unreliable, in some cases backwards. False accusations drive people away, and this is where confirmation bias operates, so do not build an audit on them.

- **Perfect grammar.** Plenty of writers are professionals.
- **Mixed casual and formal register**, or clinical prose next to emotional prose. Can indicate a technical writer, a young writer, playfulness, neurodivergence, or several authors.
- **"Bland" or "robotic" prose.** The impression is unreliable, and the actual tells don't always read as robotic to people who don't know them.
- **Formal or academic prose generally.** Models overuse specific words, not formality as such.
- **Transition words in isolation.** Only a few are AI-associated, and essay writing has used them forever.
- **Missing citations.** Most unsourced text predates LLMs, and current chatbots often do add citations, just not always accurate ones.
- **Odd markup**, which more often comes from editor bugs and extensions than from a model.
- **Correct markup**, which is normal for anyone using a visual editor or previewing their work.

Two further cautions on detection:

- **Automated detectors** beat chance but have real error rates, are defeated by light paraphrasing, and misfire on writers using a second language. A detector's verdict is not a finding.
- **Human judgment** splits: some studies put unaided readers at chance, one on German theses found about 57% on AI text and 64% on human text, and a 2025 preprint found frequent LLM users right about 90% of the time. Even the optimistic number means one false positive in ten.

## Never inject

The rewrite has its own failure mode: reaching for a stock kit of "human" moves and installing a personality the author never had. That trades one detectable register for a louder one. A stress test of a widely used de-AI skill found exactly this, with generic phrasing replaced by a recognizable fragments-and-staccato voice.

None of the following may be added to a text that did not already contain it, even when the result scores clean:

- **First person the author never used.** "In my experience", "I'll admit". If the source has no *I*, the rewrite has no *I*.
- **Manufactured stakes.** "In a world where", "now more than ever".
- **Invented contrarianism.** "Everyone says X, but they're wrong" — unless the source argued it.
- **Performed candor.** "Let's be honest", "real talk", "here's the thing".
- **Added em dashes** for drama the content hasn't earned.
- **Staccato conversion.** Chopping ordinary sentences into fragments to manufacture rhythm. Vary sentence length by varying the sentences.
- **Invented specifics.** A number, name, date, tool, or mechanism the source never contained. This is the most tempting fix, because a concrete detail always reads better, and a fabricated one is worse than the vagueness it replaced. Flag the gap and leave it.

The test for any edit: did the information come from the source? Subtraction and sharpening are in scope — cutting filler, making an existing claim concrete, surfacing a buried point. Adding stance, personality, or fact is not.
