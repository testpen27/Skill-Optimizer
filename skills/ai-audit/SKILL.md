---
name: ai-audit
description: Audit prose for the stylistic tells of LLM-generated writing, then revise them out while preserving the author's voice. Use this skill whenever the user asks whether something "sounds like AI" or "reads like ChatGPT", asks to make text sound more human or less AI-generated, asks to strip AI slop from a draft, mentions em dashes or "delve" as giveaways, asks whether a student, applicant, or colleague used AI, wants a piece checked before publishing, or asks for an edit pass where sounding machine-generated is a worry — even if they never say the words "AI writing". Also use it when the user asks you to check your own draft output for these patterns.
---

# AI Audit

Find the patterns that make prose read as machine-generated, explain why each one reads that way, and revise them out without flattening the writing.

Based on Wikipedia's *Signs of AI writing* (WikiProject AI Cleanup), read from the page's own wikitext in September 2026, with additions from community de-AI skills where they cover non-encyclopedic genres. Sources are listed at the end.

## Governing principles

**No single tell proves anything. Density does.** LLMs were trained on human writing, so every pattern in the catalogue appears in human prose too. A lone em dash means nothing. Four significance-inflation clauses in two paragraphs mean something.

**Tells are dated and model-specific.** The vocabulary that marked 2023 output is not the vocabulary that marks 2026 output, and models differ from each other: em dashes now point toward Claude and away from ChatGPT, curly quotes the reverse. Check `references/dated.md` before treating any word list or typographic habit as current, so the audit describes the text in front of you rather than a 2023 memory of ChatGPT.

**Counter-evidence counts as much as flags.** Certain ordinary constructions — plain *is*/*has* phrasing, wordy filler, hedges, definite claims — are markers of human writing that LLM prose avoids. They belong in the audit alongside the tells, and they must survive the revision. See `references/human-signals.md`.

**Report density and location, never a verdict on authorship** — in either direction. Research runs both ways: some studies put unaided human judgment at chance, while a 2025 preprint found frequent LLM users right about 90% of the time, which still means roughly one false accusation in ten. If the user is trying to determine whether a student, employee, or applicant used AI, give them the pattern analysis, tell them plainly that stylistic analysis cannot establish authorship, and point them to evidence that can: drafts, version history, and a conversation with the writer about their own choices. Avoid "this reads as human" too — it is the same claim with the sign flipped. Describe the text.

**Cleaning the tells does not fix what they point at.** Surface signs often sit on top of fabricated citations or invented specifics. A revision that removes the tells and leaves the fabrication makes the real problem harder to find, so fabrication flags must survive into the output.

If the user is auditing their own work, skip the epistemics and get to the edit.

## Modes

Read what the user is asking for and pick one. Default to **Both** when the request is ambiguous.

| Mode | Trigger | Output |
|---|---|---|
| **Audit** | "Does this sound like AI?", "check this before I publish" | Flagged passages, counter-evidence, density read, no rewrite |
| **Revise** | "make this sound human", "clean this up" | Rewritten text plus a short note on what changed |
| **Both** | Ambiguous, or user wants to learn the patterns | Audit, then revision, then what was deliberately left alone |

## Workflow

1. **Read the whole piece first.** Note genre, register, intended reader, and where it was written — a Word document, a wiki, an email, a CMS. Several tells depend on the authoring environment rather than the prose.
2. **Run the deterministic pass.** `python scripts/fingerprints.py <file>` scans for tool markup leaks, tracking parameters, placeholders, and chat wrappers. These are the only near-proof category, they are trivial to miss by eye, and a hit changes how you frame everything else. Run it on pasted text too, via stdin.
3. **Consult the references. Do not work from memory** — the catalogue tiers each pattern by signal strength and dates it, which is what keeps the audit honest.
   - `references/tells.md` — the current catalogue, tiered.
   - `references/dated.md` — vocabulary by model era, retired tells, per-model habits.
   - `references/human-signals.md` — what not to flag, and what to preserve.
   - `references/wikipedia-signs.md` — the full section-by-section summary of Wikipedia's page, which the three files above distil. Read it when the text is wiki content, an edit summary, or a talk-page or review comment (wikitext markup, edit-summary templates, and comment-specific tells live only here), or when you need a pattern's original context or caveats.
4. **Flag by tier.** Strong tells carry the analysis. Moderate tells count when they cluster. Weak tells never lead.
5. **Collect counter-evidence** as you go. A piece with three moderate tells and four human markers is a different finding from one with three tells and none.
6. **Revise surgically.** See the rules below.
7. **Say what you left alone and why.** Users find this the most useful part, and it is the guardrail against over-correction.

## Rewriting rules

The goal is not "sounds less like AI". The goal is prose that says something specific. Most tells are symptoms of one problem — generic content padded with the appearance of significance — so the fix is almost always to cut the padding rather than swap in different padding.

**Cut, don't substitute.** The editorializing tail ("..., highlighting the region's growing influence") should be deleted, not reworded into a more natural-sounding editorializing tail. If a sentence loses nothing when the clause is removed, the clause was the tell.

**Never fill a gap you cut open.** If a paragraph collapses to nothing once the puffery is gone, that paragraph had no content. Flag it for the author. Inventing a number, a name, a date, or a mechanism to replace vague phrasing is worse than the vagueness, because a fabricated specific reads better and is harder to catch.

**Preserve voice, including the parts that look like flaws.** Match the author's sentence rhythm, vocabulary level, and contraction habits. Read three or four sentences you are *not* changing and let them set the register. Keep the human markers in `references/human-signals.md`: the plain *is* and *has* constructions, the "in order to", the "very" and "perhaps", the flat superlative. Community de-AI skills delete all of these, which strips the strongest evidence of human authorship out of the text.

**Never inject.** Do not add first person to prose that had none, manufactured stakes, invented contrarianism, performed candor, or staccato fragments chopped out of ordinary sentences. Every one of these swaps a recognizable machine register for a recognizable de-AI register, which is a new fingerprint rather than the absence of one. You may subtract and sharpen; you may not add.

**Vary structure rather than sanitizing it.** If every sentence is the same length, the fix is unequal sentences, not shorter ones. If every list has three items, make one of them two.

**Do not overcorrect.** These are all legitimate and should survive an audit: em dashes used well, occasional "however", genuine three-item lists, bulleted lists in documentation, formal register in formal genres, a conclusion in a piece that structurally needs one, and any tell that is a convention of the genre the author is writing in. School essays, cover letters, grant applications, and press releases teach several of the patterns in this catalogue.

**Leave facts alone.** Do not change claims, numbers, names, or citations while editing for style. Flag suspect ones for checking instead of silently deleting or "fixing" them.

## Output format

### Audit

Open with a one-line density read: **Low / Moderate / High**, plus the count of strong-tier tells and the dominant pattern. If any fingerprint hit, lead with that instead — it is a different kind of finding. Then:

```
**[Tell name]** (strong, current) — 4 instances
> "...cementing his status as one of the region's most influential figures."
Why: the sentence states a fact, then appends an interpretation of that fact's importance. Cut at the comma.
```

Mark each tell with its tier and whether it is current, dated, or genre-normal for this piece. A tell that a teacher, a grant office, or a style guide asks for is not evidence, and saying so prevents the reader from double-counting it.

Close with **Pointing the other way**: the human markers and specifics you found. Then, if the user is asking about someone else's text, the authorship paragraph from the governing principles.

Quote only the fragment needed — a few words — not whole paragraphs. Group by tell, not by paragraph, so the user sees the pattern.

If density is genuinely low, say so and stop. Do not manufacture findings to fill out a report.

### Revision

Give the revised text in full, then a compact note:

```
**Changed:** removed 6 significance-inflation clauses; broke up the three-item rhythm in ¶2–4; cut the summary paragraph.
**Left alone:** the em dashes (used for genuine interruption); "in order to" and the two hedges in ¶3 (human markers, and the register carries them); the bulleted list in ¶5 (a genuine enumeration).
**Needs you:** ¶4 has no content once the puffery is out — what actually happened there? The two statistics in ¶6 are unsourced; I have not touched them.
```

## Scope

This catalogue is built for informational and persuasive nonfiction. Fiction has a separate set of tells and is out of scope; say so rather than applying these rules to a short story.

The skill flags citation problems but does not resolve them. Checking whether a DOI leads to the right paper, or whether a quoted page contains the quote, needs network access and is a fact-checking job.

## Worked example

**Input:**
> The initiative, launched in 2019, has since expanded to twelve countries, underscoring its growing global significance. It's not merely a funding program — it's a movement. Moreover, observers note that its influence continues to shape the broader philanthropic landscape.

**Audit:** High density. Editorializing tail ("underscoring its growing global significance"), negative parallelism ("not merely X — it's Y"), vague attribution ("observers note"), significance inflation ("shape the broader landscape"). Four strong tells in three sentences. Nothing points the other way: no specific detail, no plain construction, no hedge.

**Revision:**
> The initiative launched in 2019 and now runs in twelve countries.

**Note:** Sentences two and three contained no verifiable claim once the interpretation was removed. If the program's influence on other funders is real, it needs a specific example — a copycat program, a policy change, a named foundation that followed suit.

The example is deliberately brutal to make the point: most AI padding deletes to nothing. Real edits are gentler, but the test is the same — does the sentence survive losing its interpretive clause?

## Sources

- Wikipedia, *Signs of AI writing* (WP:AISIGNS), WikiProject AI Cleanup, read September 2026. The catalogue's backbone, including the model-era vocabulary table, the signs-of-human-writing section, and the ineffective-indicators list. Summarized in full in `references/wikipedia-signs.md`.
- `blader/humanizer`, `conorbronsdon/avoid-ai-writing`, `brandonwise/humanizer` — community skills covering genres Wikipedia's page does not, such as marketing and personal essays. Entries taken from these are marked in the catalogue.
- `andrewroxby/claude-style-patch` and slhck's "Claudish" write-up, for Claude's own current habits.
