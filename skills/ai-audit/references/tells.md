# Catalogue of tells

Tiered by signal strength. **Near-proof** tells identify a specific tool. **Strong** tells are rare in unassisted prose and carry the audit. **Moderate** tells are common in bad human writing too and count when they cluster. **Weak** tells prove nothing alone and should never lead.

Each entry carries a currency note. *Current* means observed in 2026 output. *Dated* means it marks older output and belongs in `dated.md`. *Community* means the entry comes from the community de-AI skills rather than Wikipedia's page, usually because it covers a genre Wikipedia does not.

Before flagging anything, check two things: whether the pattern is a convention of the genre in front of you, and whether `human-signals.md` lists it as something not to flag.

## Contents

**Near-proof**
1. Tool markup and tracking fingerprints

**Strong**
2. Collaborative communication left in the deliverable
3. Knowledge-cutoff disclaimers and gap speculation
4. Placeholders and unfilled templates
5. Fabricated specifics and citation integrity
6. Editorializing tail
7. Significance inflation
8. Notability padding
9. Negative parallelism
10. Vague attribution
11. The faces-challenges template
12. Canned compliance assurance

**Moderate**
13. Copula avoidance
14. Vague association
15. Rule-of-three rhythm
16. Formatting by rule
17. Format-environment mismatch
18. List-where-prose-belongs
19. Stock section names
20. Definitional leads
21. Content-free both-sidesing
22. Staged run-ups and performed insight
23. One-line closers and negation chains
24. Claudish
25. Register inflation

**Weak**
26. Em dash frequency
27. Curly quotes and typography
28. Mechanical transitions
29. Individual vocabulary items
30. Cross-cutting: uniformity

---

## Near-proof

### 1. Tool markup and tracking fingerprints

*Current.* Chatbot-internal citation markers and tracking parameters pasted along with the text. Each belongs to one tool: OpenAI's `:contentReference[oaicite:N]` and `citeturn…` markers, Gemini's `[cite: 1]` and `[span_N](start_span)`, Grok's `<grok-card>` tags, DeepSeek's `【85†L261-269】`, Perplexity's `[web:1]` and `ppl-ai-file-upload` URLs, and `utm_source=openai`, `utm_source=chatgpt.com`, `utm_source=copilot.com`, `referrer=grok.com` on cited links.

**Why:** no human writes these. They come from the tool's own rendering layer.

**What it proves and doesn't:** that the tool touched this text. A tracking parameter on a citation shows the tool found the source, which is compatible with a human writing the prose. Say which, rather than letting one hit carry the whole audit.

**Fix:** delete the markup; strip the tracking parameter from the URL. Run `scripts/fingerprints.py` rather than scanning by eye, since Unicode private-use characters can hide some of these.

---

## Strong

### 2. Collaborative communication left in the deliverable

*Current.* Text addressed to whoever ran the prompt, surviving into the finished piece. Two shapes:

- Wrappers: "Certainly! Here's a draft of your article", "I hope this helps", "Would you like me to expand on any of these points?"
- Advice: instructions, checklists, or coaching aimed at the requester rather than the reader. A draft article that pauses to tell the author what a page needs before submission; a report that explains how to present its own findings; a bio that advises on what to add once it's available.

**Why:** conclusive for AI involvement when present, though not proof about any particular person's honesty. The advice shape is easier to miss than the wrapper, because it reads as content until you notice it is talking to the wrong person.

**Fix:** delete. If the advice contains a real requirement the piece should meet, hand it back to the author separately.

### 3. Knowledge-cutoff disclaimers and gap speculation

*Current, with a dated ancestor.* Older models announced a training cutoff outright. Current retrieval-based models produce the same shape when a search comes up empty: "while specific details are limited", "not widely documented", "based on the available sources" — often followed by a guess dressed as inference. About people, the stock guess is that the subject "maintains a low profile" or "likely grew up" somewhere.

**Why:** the claim that something is undocumented is itself unverified, and the speculation that follows is invented. This is the tell that most often precedes a fabrication.

**Fix:** state what the sources do not show, or cut the sentence. Never let a guess stand as a fact, and flag the surrounding claims for checking.

### 4. Placeholders and unfilled templates

*Current.* Bracketed slots the user never filled: `[Your Name]`, `[Describe the specific section]`, `INSERT_SOURCE_URL`, access dates like `2025-XX-XX`, or comments suggesting information be added later.

**Why:** the model produced a fill-in-the-blank template and the user pasted it whole.

**Careful:** some document templates ship with their own bracketed prompts. Check whether the placeholder came from the tool or from the form before flagging it.

**Fix:** delete or fill, and ask the author which.

### 5. Fabricated specifics and citation integrity

*Current.* Confident, precise, unverifiable detail: citations that look right but don't resolve, invalid ISBN checksums, DOIs that lead to unrelated papers, dead links absent from web archives, page-numbered citations to real books where the cited page says nothing of the kind, statistics with no source, quotations attributed to real people who never said them.

**Why:** models generate the shape of evidence fluently. This is the tell with actual stakes — the others are aesthetic, this one is a correction or a retraction.

**Careful:** broken links and wrong-target citations also come from mangled copy-paste, institutional proxies, and editing-tool bugs. They are worth fixing either way.

**Fix:** never silently delete or "correct" these. Flag every one for verification, say explicitly which claims you could not confirm, and keep those flags in the output of a revision.

### 6. Editorializing tail

*Current.* A sentence states a fact, then appends a participial clause explaining what the fact means or represents.

> The bridge opened in 1932, **connecting the two boroughs and transforming commuter patterns across the region.**
> She published four novels in the decade, **cementing her reputation as a leading voice of the movement.**

Watch for: *highlighting, underscoring, reflecting, symbolizing, ensuring, contributing to, cultivating, fostering, encompassing, showcasing, enhancing.*

**Why:** the construction manufactures consequence without adding information, and the claim is usually unfalsifiable and unsourced. Retrieval-based models now attach these tails to a named real source, which makes them look attributed without being true.

**Fix:** cut at the comma. If the significance is real, it deserves its own sentence with evidence attached. Where a source is named, check whether the source said it.

### 7. Significance inflation

*Current, with dated vocabulary.* Every subject plays a vital role, serves as a testament, marks a turning point, leaves an indelible mark, reflects a broader shift, or is deeply rooted in something.

> Its architecture stands as a testament to the city's industrial heritage.
> This marked a watershed moment in the history of the sport.

**Why:** regression to the mean. Specific facts get smoothed into generic claims that would fit almost any subject. Swap the subject noun and the sentence still works; that substitutability is the diagnostic. Newer models do this more quietly than 2023 models did — less "the best", more "a key part of" — so calibrate to current output rather than to blatant superlatives.

**Fix:** delete. Test by substitution.

### 8. Notability padding

*Current, and rising.* The text catalogues *what kind* of sources covered the subject instead of what they said: "independent coverage", "featured in regional media", "profiled in trade publications", "written by a leading expert", "maintains an active social media presence".

**Why:** the model is trying to prove the subject deserves an entry rather than writing the entry. The focus lands on the sources' characteristics rather than the subject's. Wikipedia's page ties this to current-generation output specifically, where it has partly displaced the older ornamental vocabulary. Outside Wikipedia it shows up in bios, About pages, grant applications, and pitch decks.

**Fix:** say what the coverage found, or cut it. A list of outlet types is not a claim.

### 9. Negative parallelism

*Current.* Three variants:

- *Not just X, but Y* — "it's not only a tool, it's a platform"
- *Not X, but Y* — the flat denial: "it's not a restaurant, it's an experience"
- *Y rather than X* — the reversal, notably common in Grok output

Also appears split across sentences: "This does not mean every choice is equal. It means…"

**Why:** the negative half names something nobody claimed, so the positive half sounds larger. Humans use "but" for real contrast.

**Fix:** assert the second half and drop the first.

**Careful:** one instance in persuasive copy is legitimate rhetoric. Flag at three or more, or when it appears in reference writing, documentation, or reportage, where it has no business.

### 10. Vague attribution

*Current.* Claims sourced to an unnamed collective: "some critics argue", "many experts believe", "observers note", "industry reports suggest", "described in scholarship". Also counts when "several sources" turn out to be one or two.

**Why:** the model needs a citation-shaped object and has none, so it produces the grammar of sourcing without the content. Distinct from a journalist's signposted anonymity.

**Fix:** name the source or cut the claim. This is frequently where the piece's factual weak points are.

### 11. The faces-challenges template

*Current.* A section that opens "Despite its [positive traits], [subject] faces several challenges…", names generic obstacles, and closes on cautious optimism or speculation about future initiatives. Often paired with a "Future Prospects" or "Challenges and Legacy" heading.

**Why:** the tell is the rigid template, not the discussion of challenges. Real constraints described specifically are just content.

**Careful:** Wikipedia editors note this phrasing produces many false positives, because the shape is also taught in school and standard in consulting and grant writing. Weigh the whole template, not the phrase.

**Fix:** cut sections with no content; move grounded constraints into the body.

### 12. Canned compliance assurance

*Current.* A note attached to the work reassuring the reader that it follows the rules: "ensured the text adheres to the style guide", "refined for clarity, flow, and neutrality", "revised in compliance with your brief". Wikipedia documents this in edit summaries; the same habit appears in commit messages, pull request descriptions, cover emails, and submission notes.

**Why:** a human describing an edit is brief and specific, and cites the one rule they applied. The AI version is verbose but vague, stacking generic improvements nobody bundles into one pass. A related shape describes what was *not* changed — "preserved the original structure", "retained all citations" — which is natural for a model following instructions and odd for a person.

**Fix:** replace with what actually changed, or delete.

---

## Moderate

### 13. Copula avoidance

*Current.* Simple *is*, *are*, and *has* replaced by fancier verbs: *serves as, stands as, functions as, operates as, represents, marks*; and the marketing set, *boasts, features, offers, maintains*. In an opening sentence, "refers to" treats the piece as being about the term rather than the thing.

**Why:** measured, not impressionistic. Use of "is" and "are" dropped over 10% in academic writing from 2023, with a similar decline on Wikipedia. It also runs directly against a human marker, so each instance costs the text twice.

**Fix:** *is*, *are*, *has*.

### 14. Vague association

*Current.* "Associated with", "in connection with", "linked to", "tied to" standing in for the actual relationship. "He was associated with the leadership of the company" hides whether he was the CEO, a board member, or a contractor.

**Why:** the model knows two things co-occur and does not know how.

**Fix:** name the relationship the source gives. If the source doesn't give one, keep the vague wording rather than inventing a role, and flag it.

### 15. Rule-of-three rhythm

*Current.* Triads as the default unit: three adjectives, three examples, three clauses, three bullets, repeatedly. A colon opening onto exactly three items is the most common shape.

**Why:** a real rhetorical device overused to the point of metronome. The tell is the consistency. It is a stronger signal in places where humans don't bother with flourishes, like a commit message or an edit summary.

**Fix:** break the pattern, not the device. Make some lists two items, some four. Keep the triads that earn their rhythm.

### 16. Formatting by rule

*Current.* Bold applied mid-paragraph for emphasis rather than scanning, and to every repeated key term. Title Case On Ordinary Headings. Emoji as section markers. Bulleted lists where every item is a bold label, a colon, then a sentence. Headings whose only content is more headings. A heading at the top repeating the document's own title. Thin two-column tables that should be sentences.

**Why:** habits inherited from readmes, listicles, and sales decks, applied mechanically. The tell is decoration on every item, not decoration anywhere.

**Fix:** reserve bold for genuine scanning aids; sentence case unless house style says otherwise; convert label lists to prose when the labels carry no information.

### 17. Format-environment mismatch

*Current.* Markup that the destination doesn't render: raw `**bold**` or `##` headings in an email, a Word document, a CMS field, or a wiki; `---` rules between sections; stray triple-backtick fences; heading levels that skip from the title straight to a sub-sub-heading.

**Why:** models emit Markdown by default because their instructions tell them to. Somebody pasted it somewhere Markdown is not the format.

**Careful:** Markdown alone is weak. Developers, researchers, and anyone who lives in Slack, Discord, Obsidian, or GitHub write it by hand.

**Fix:** convert to the destination's formatting.

### 18. List-where-prose-belongs

*Current.* An argument fragmented into bullets that should have been three connected sentences. Bullets that are full paragraphs. Nesting two or three deep for simple material.

**Why:** lists are easy to generate and look organized, but they drop the connective reasoning between points, which is the argument.

**Fix:** convert to prose where items relate logically. Keep lists for enumerations, steps, and reference material.

### 19. Stock section names

*Current.* "Awards and recognition", "Challenges and Opportunities", "Impact and Legacy", "Key Takeaways" — the generic "X and Y" heading pattern, often over thin content.

**Why:** the template demands the section, so the section appears, and its contents are assembled to fill it.

**Fix:** cut sections with no material; name the remaining ones after what they contain.

### 20. Definitional leads

*Current.* The opening sentence defines the title as though it were a standalone entity: "Quarterly revenue analysis refers to…", "Team offsite planning is the process by which…".

**Why:** the model treats a document title as a term to gloss. Human writers start with the thing.

**Fix:** start with the content.

### 21. Content-free both-sidesing

*Current.* "While the technology offers significant benefits, it also presents notable challenges." "Critics and supporters alike have raised important points."

**Why:** models are tuned toward evenhandedness and produce its grammatical form even with nothing to balance. The sentence conveys nothing.

**Fix:** delete, or say what each side actually holds.

### 22. Staged run-ups and performed insight

*Community, current.* Announcing a point instead of making it: "Let's dive in", "Here's the thing", "Honestly?", "The real question is", "at its core", "what really matters". Also the version that argues with nobody: "This isn't about X", "To be clear, I'm not saying", "A tempting approach would be…", where the objection or alternative appears nowhere else.

**Why:** the run-up stages candor or depth; the phantom objection stages rigor. Neither adds a claim. Not on Wikipedia's page, because encyclopedic writing rarely offers the opportunity — these dominate blogs, LinkedIn, and essays.

**Fix:** delete the run-up and state the point. If the rejected alternative is one a reader would actually weigh, keep it and answer it properly.

### 23. One-line closers and negation chains

*Community, current.* A one-sentence paragraph restating the paragraph above it: "That's the real win." "Let that sink in." A row of fragments engineered as a drumroll: "No shortcuts. No magic. Just showing up." A reversal landed on a bare auxiliary: "The tool died; the data didn't."

**Why:** each asks the reader to pause on a claim instead of adding to it. One short sentence that carries a new fact is good writing; three same-shape beats in a row are a rhythm applied by rule.

**Fix:** cut the closer that repeats. Fold a chain of fragments into a sentence that states the claim. Keep the one that earns its emphasis.

### 24. Claudish

*Community, current, and relevant when auditing your own output.* A cluster of habits in current Claude prose:

- Colon-hinged sentences where the left side labels what the right side does: "The honest construction: …"
- Verbless fragments as paragraph openers: "Two things worth watching." "One caution."
- Stacked compression — a metaphor, a nominalized verb, and a packed phrase adjacent in one clause, so the reader decodes rather than reads.
- A tone of proving its reasoning rather than informing the reader: "the single most important correction", "that doesn't survive contact with the data".

**Why:** these are Claude's own defaults rather than generic LLM habits, and they are invisible if you are auditing with a ChatGPT-shaped checklist. Wikipedia's page notes that models have distinct idiolects; Claude and Gemini run more concise, ChatGPT and Grok lean on broader-context framing.

**Fix:** fold the label into the sentence that does the work. Turn the fragment into a clause. Unpack one compressed unit per sentence.

### 25. Register inflation

*Current in shape, dated in vocabulary.* *Utilize* for use, *delve into* for examine, *leverage* for use, *navigate the complexities of*, *in today's rapidly evolving landscape*, *foster*, *robust*, *seamless*, *myriad*, *pivotal*, *comprehensive*.

**Why:** individually ordinary words. The tell is density plus mismatch with genre — "delve" in a doctoral thesis is unremarkable, "delve" in a text to a friend is not. Which words carry signal has changed with each model generation, so read `dated.md` before leaning on any list, and watch for the literal word rather than its synonyms.

**Fix:** plainer word, chosen against the register of the surrounding piece rather than from a blocklist.

---

## Weak

Use these only as corroboration. Never open an audit with one.

### 26. Em dash frequency

*Model-dependent, and reversing.* Wikipedia's page now flags its own em-dash section as possibly outdated. A July 2026 study found Claude was the only current model using em dashes more than professional human writers, while ChatGPT by then used fewer, and some vendors have tuned the habit out deliberately.

So the direction of this signal depends on which model you are thinking of, which is exactly why it cannot carry an audit. What still means something: the dash used as an all-purpose connector several times a paragraph, replacing colons, parentheses, and commas indiscriminately, often with spaces around it. What means nothing: a dash used correctly.

**Never** strip em dashes mechanically. Plenty of good writers love them, and de-dashed prose reads conspicuously de-dashed.

### 27. Curly quotes and typography

*Model-dependent.* ChatGPT and DeepSeek typically emit curly quotes and apostrophes, sometimes mixed inconsistently within one passage. Claude and Gemini typically do not.

This only matters where the authoring environment wouldn't produce them. Word, macOS, iOS, and most CMSs curl quotes for everyone, and Chicago style requires them.

### 28. Mechanical transitions

*Weak — demoted.* *Moreover, Furthermore, Additionally, However, That said, Notably, Importantly* at the head of sentences.

Wikipedia's page lists transition words in isolation among its ineffective indicators: only a few are genuinely AI-associated, and the habit has a long history in ordinary essay writing. Treat a pile of them as a clarity problem rather than as evidence.

**Diagnostic:** delete the transition. If the meaning is unchanged, it was filler. Cut the decorative ones, keep the load-bearing ones, and don't swap in different transitions.

### 29. Individual vocabulary items

*Weak, and dated.* *Delve, tapestry, boasts, testament, showcase, underscore, realm, landscape, journey, unlock, harness.* Single-word detection was always thin. Human writing is measurably converging on LLM style, and each word's peak era has passed at a different time — see `dated.md`. Treat vocabulary as texture supporting a structural finding, never as evidence on its own.

### 30. Cross-cutting: uniformity

*Weak as evidence, useful as an edit.* Paragraphs of near-identical length, sentences clustered around one length, every section the same depth, every example the same weight.

Human writing is lumpy. Writers over-attend to what interests them, run short when bored, digress, put a two-word sentence after a forty-word one.

**Careful:** Wikipedia's page lists "bland" or "robotic" prose among its ineffective indicators, because that impression is unreliable and is where confirmation bias does its work. Measured uniformity across a long piece is worth noting; a feeling that prose sounds robotic is not a finding.

**Fix:** find the part the author cares about and let it run long. Cut the parts they don't. Uneven attention is what makes prose sound like a person.
