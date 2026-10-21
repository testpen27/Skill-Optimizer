# AI checkers: what they measure and how to read their reports

Read this whenever the user brings a detector result (a Turnitin AI Writing
Report, a GPTZero scan, a percentage someone quoted at them), or asks how
AI checkers work, why their text was flagged, or what a score means.

Facts about Turnitin below come from Turnitin's own guides, read in October
2026: *Using the AI Writing Report*, *AI writing detection capabilities FAQs*,
the release notes, and the blog post on sentence-level false positives.
Detectors change often; when a detail matters to a decision, say what date
it is from.

## Contents

1. A detector is a different instrument from this audit
2. How Turnitin's AI detection works
3. Reading a Turnitin AI Writing Report
4. Other checkers
5. Why a passage gets flagged: what can and cannot be said
6. What the user can do, and what not to do
7. Worked case: a flagged postgraduate assignment

---

## 1. A detector is a different instrument from this audit

This skill's catalogue (`tells.md`) lists *surface* patterns a human reader
notices: puffery, "not just X but Y", "serves as", stock vocabulary. AI
detectors do not work from a list like that. Turnitin says its model "is
not explicitly programmed to evaluate specific signals such as burstiness,
perplexity, or other individual metrics"; it is a transformer classifier
trained on AI-generated and authentic academic writing, and it scores how
predictable each sentence's word choices are in the context of the text
around it. GPTZero likewise moved from perplexity-and-burstiness scoring to
an end-to-end deep-learning classifier in 2023.

Consequences to tell the user plainly:

- **Removing the tells does not reliably lower a detector score.** A text
  can be free of every pattern in `tells.md` and still be flagged, because
  fluent, generic, evenly built prose is predictable whether or not it
  contains "delve". In the worked case below, a sentence with a textbook
  negative parallelism went unflagged while plain definitional sentences
  with no tells at all were flagged.
- **A clean audit is not a forecast of a detector score**, and a high score
  is not a list of tells to fix. Never promise a score.
- The two do overlap: generic significance claims, summary conclusions and
  definitional filler are both tells *and* highly predictable text. That
  overlap is where revising for the reader and revising for the detector
  point the same way.

## 2. How Turnitin's AI detection works

- **Unit of scoring: the sentence, in context.** Each sentence gets a score
  from 0 to 1 based on the sentence and the text around it. Sentences above
  a threshold are labelled AI; the rest human. An October 2026 model update
  targeted accuracy at transitions between human and AI text.
- **The percentage** is the share of *evaluated* sentences labelled AI. It
  is not a probability that the document is AI-written, and it is not the
  share of all words in the file.
- **What is evaluated ("qualifying text")**: prose sentences in long-form
  writing. Removed before scoring: lists of short non-sentence items,
  headers, references, data tables, formulas and code. A bullet point that
  is a full sentence *is* evaluated. This is why the percentage and the
  amount of highlighted text can disagree.
- **Minimum length**: at least 300 words of qualifying prose, or no score.
  In documents of only a few hundred words the result is close to all or
  nothing, because there is one scoring segment and no overlap.
- **Low scores are hidden.** Since July 2024, 1-19% shows as `*%` with no
  highlights, because Turnitin found false positives more frequent there.
  0% and 20-100% are shown.
- **Accuracy claims (Turnitin's own)**: under 1% of fully human documents
  flagged, for documents scoring over 20%; about 4% of individual sentences
  falsely flagged, more often in documents that mix human and AI text, and
  54% of those false-positive sentences sit right next to actual AI text.
  To keep false positives low it deliberately misses some AI text: "if we
  identify that 50% of a document is likely written by an AI tool, it could
  contain as much as 65% AI writing."
- **Turnitin's own list of false-positive risks**: "content without a lot of
  structural variation, text that literally repeats itself, or text that has
  been paraphrased without developing new ideas."
- **Paraphrasers and humanizers are detected, not hidden.** Detection of
  AI-paraphrased text arrived in 2023-24, of "bypasser"/humanizer tools in
  August 2025. Since August 2026 both are folded into one "AI-generated"
  category with one highlight colour; older reports showed a separate purple
  category for AI-paraphrased text. English only.
- **Grammar checkers**: Turnitin says ordinary spelling and grammar fixes
  from Grammarly and similar tools were mostly not flagged in its tests, but
  text from their *generative* features (rewrite, paraphrase, draft,
  summarise) "will likely be flagged".
- **Training data** included second-language writers and less common
  subjects, to reduce bias. Independent research is less reassuring about
  detectors in general: Liang et al. (2023, *Patterns*) found seven popular
  detectors flagged over half of non-native speakers' TOEFL essays as AI
  (average false positive rate 61%). That study predates Turnitin's current
  model and did not test it; cite it as a reason for caution, not as a
  measured Turnitin error rate.
- **Turnitin makes no misconduct finding.** Its report says the score
  "should not be used as the sole basis for adverse actions against a
  student". The similarity (plagiarism) score is a separate, independent
  measurement.
- Students normally cannot see the AI report; an instructor can download it
  as a PDF and share it. A report in a student's hands has usually been
  shared on purpose, often as a "review this before final submission" step.

## 3. Reading a Turnitin AI Writing Report

With the PDF, run:

```
python scripts/checker_report.py REPORT.pdf
```

It prints the score and every prose sentence, split into highlighted and
not highlighted, with tables, headings and references removed. It reads the
report's own highlights; it does not re-score anything. Its sentence count
will differ slightly from Turnitin's, so quote Turnitin's percentage, not a
recount. If the user pasted text or a screenshot instead, work from what
they marked.

Then read it in this order:

1. **The state.** `--` (not processed: too short, wrong format, unsupported
   language), `*%` (1-19%, deliberately unreported), 0%, or 20-100%.
2. **Where the highlights cluster.** By section and by sentence function:
   definitions, topic sentences, list items, examples with data, the
   writer's own evaluation, the conclusion. Clusters say more than the
   number.
3. **What the unflagged sentences have that the flagged ones lack.** This
   comparison, on the user's own text, is the most useful thing to show
   them. See section 5 for what tends to separate the two.
4. **What the score can and cannot establish** (section 2). Say it once,
   plainly, then move on to the text.

## 4. Other checkers

- **GPTZero**: sentence-level highlighting plus a document classification
  that includes "mixed" human/AI. Deep-learning classifier since 2023; its
  public explanations still talk about perplexity and burstiness, which
  describe the intuition rather than the model.
- **Scores are not comparable across tools.** Each detector has its own
  training data, threshold and definition of what it scores. A 30% on one
  and 70% on another is normal, not a contradiction to resolve.
- Free online checkers frequently disagree with each other and with
  Turnitin. Running a text through several of them and "fixing" until all
  say human is chasing noise, and some of those sites keep the text.

## 5. Why a passage gets flagged: what can and cannot be said

The detector does not explain itself, and Turnitin says individual
predictions "may not always be explainable in simple feature-by-feature
terms." So never tell a user *the* reason a sentence was flagged. What can
be said is what the flagged sentences in *their* report have in common, and
what the documented false-positive risks are.

Sentence types that are predictable in academic prose, and that recur in
flagged passages (Turnitin's stated risks plus observation; not a rule):

- **Textbook definitions** restated in standard form ("An X is a market in
  which..."). Thousands of essays define the term the same way.
- **Signposting and topic sentences** that announce structure ("The answer
  is no, for five reasons", "Applying this test to four areas shows...").
- **Even, parallel structures**: a run of bullets each opening with a bold
  label and a full explanatory sentence; "First... Second... Third..." with
  matched lengths.
- **Generic conclusions** that restate the whole piece at a high level
  ("the same theme emerges: success comes from innovation and adapting").
- **Recommendation boilerplate** ("The author recommends X, structured in
  two parts").

Sentences that tend to stay unflagged:

- **Specific figures used in the writer's own working**: numbers combined,
  compared or qualified ("this growth may have happened even without the
  merger").
- **The writer's own qualifications of a source**, assumptions stated for
  this assignment, and judgements tied to the case.
- **Idiosyncratic phrasing**, including the writer's own grammar. Fixing
  real errors is fine, and Turnitin says grammar-only fixes are generally
  not flagged, but rewriting a clumsy-but-genuine sentence into smooth,
  generic prose moves it toward what detectors flag.

Two caveats to state when it matters:

- **Highlights work at segment level.** A sentence with an obvious human
  error can still be highlighted when the sentences around it are flagged;
  context feeds each score.
- **One report is one sample.** Patterns from a single document are
  hypotheses about that document, not laws of the detector.

## 6. What the user can do, and what not to do

**Be honest about the aim.** This skill helps a writer understand the report
and make the writing more specific and more their own. It does not help
disguise AI-generated text as human-written. If the user generated or
rewrote the text with AI, the fix is their institution's AI-use policy:
disclose as required, or redo the work. Say this once, without lecturing,
and keep helping with what is legitimate. If they say the work is their
own, believe them and help on that basis.

Revisions that improve the writing *and* address what the detector keys on:

- Replace a restated textbook definition with the definition applied to the
  case, in the writer's words, or cut it if the marker knows the term.
- Turn generic topic sentences into the claim itself.
- Add the writer's own reasoning where the text only reports: why this
  figure matters here, what it does not show, what they would check next.
- Break uniform structures where the content is not actually parallel.
- Cut or rewrite the generic conclusion so it says something specific to
  this piece.
- Keep the writer's voice, including the plain constructions in
  `human-signals.md`. Do not polish everything into uniform academic prose.

Every rule in SKILL.md's rewriting section still applies: subtract and
sharpen, never inject, never invent specifics.

What not to do, and why:

- **Humanizer, paraphraser and "bypass" tools.** Turnitin detects them and
  counts their output as AI-generated, and using one is itself an integrity
  breach under most policies.
- **Synonym swapping, inserted typos, odd spacing or hidden characters.**
  They make the text worse, and character tricks are easy to spot by eye.
- **Moving prose into tables or bullet fragments to shrink the evaluated
  text.** It changes what is scored, not who wrote it, and markers notice.
- **Iterating against free detectors until they all say human.** See
  section 4.
- **Promising a target score.** No revision can guarantee one, and the
  number moves when Turnitin updates its model and the work is resubmitted.

If the work is genuinely the user's and they expect to be questioned, the
evidence that helps is process evidence: drafts, version history (Word or
Google Docs), notes, the sources they read, and being able to explain their
own choices in a conversation. Turnitin and most institutions treat the
score as a reason for that conversation, not as a verdict.

## 7. Worked case: a flagged postgraduate assignment

Anonymised summary of a real report shared during development. No text,
names or identifiers from it are reproduced here.

A 3,500-word postgraduate business assignment scored **67%**. Five sections
answered five set questions with prose, bulleted reasoning and five tables.

- **Tables (about 600 words) carried no highlights**, consistent with
  Turnitin excluding them from scoring.
- **Bullets written as full sentences were scored and mostly flagged**: a
  "five reasons" list in which every item opened with a bold label and a
  two-to-three-sentence explanation of even length.
- **Flagged prose clustered in**: the definition of the central concept
  restated in textbook form, the topic sentences opening each answer, a
  recommendation opening "The author recommends...", a survey of four
  options in parallel sentences, and a conclusion summarising all five
  answers in generic terms.
- **Unflagged prose clustered in**: a long paragraph working through the
  financial figures of a merger (several estimates compared, one qualified
  as possibly not caused by the merger at all), the writer's stated
  assumptions for a hypothetical case, and an opening paragraph with
  non-native phrasing and a comma splice.
- **Tells versus flags**: `fingerprints.py` found no tool markup. An
  unflagged sentence used a "not separate from X, it is Y" contrast, a
  catalogue tell; flagged sentences included plain definitions with none.
  One flagged sentence contained an obvious grammatical slip, flagged with
  its neighbours.
- **Counted with `checker_report.py`** (tables and references excluded):
  83 highlighted and 48 unhighlighted prose sentences, both averaging about
  20 words, so sentence length did not separate them. 27% of highlighted
  sentences contained a figure other than a citation year, against 42% of
  unhighlighted ones. A modest difference in one document: a description of
  this report, not a law.

What to tell such a writer: the report points to the generic, structural
parts of the essay, not to the parts where they handled evidence. The
revisions most likely to help (and to earn marks) are the ones in section 6.
Whether the flagged passages came from an AI tool is something only the
writer knows; the report cannot settle it, and neither can this skill.
