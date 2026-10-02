---
name: belanjawan-brain
description: |
  The "brain" of an interactive Malaysian Budget 2026 citizen-benefits Q&A ("Semak faedah Belanjawan", `B26Brain`, `brain.js`): a verified rule engine handed over as one Markdown build spec, `BRAIN-2026.md`, for Claude Code to build the checker from (WordPress, React, vanilla HTML). Trigger when the user wants the brain or its spec; wants to add, change or re-theme its questions, benefits, tiers or rules; edit or fix its Bahasa Melayu wording; run or extend `test.js`/`verify2.js` verification; check what it covers or excludes; or rebuild the same rule-based Q&A brain for a new source document (Belanjawan 2027, a state budget, another policy text). Also trigger on mentions of "belanjawan-brain", "B26Brain", "kalkulator faedah", or "soal jawab belanjawan", even unnamed.

  Do NOT trigger for someone just asking what's in Budget 2026, wanting a plain-language summary of tax reliefs/benefits/prices, or any question answerable by reading the budget speech itself -- that's a content question, not a tool-building one.
---

# Belanjawan Brain — Belanjawan 2026 Q&A

Builds and maintains the "brain" of an interactive Budget 2026 citizen-benefits checker: the questions, the rules that turn answers into a personalised list of what the budget means for a person, the STR/SARA rates, and the Malay wording. The rules live in a verified JavaScript engine inside this skill. **What the skill hands over is one Markdown file, `BRAIN-2026.md`**, which another session or skill (for example `tv3-interactive-embed` in Claude Code) uses to build the actual checker.

---

## ⭐ OUTPUT — what to hand over

**`BRAIN-2026.md`** (next to this file) is the deliverable. It is the complete build spec:

- the question flow and all 20 questions, with options and when each is shown;
- the derived facts the rules use, and the three-valued rule logic;
- the STR + SARA calculator with its full rate table and reasons;
- every result card (115), with its rule, Malay text and speech source;
- advisories, seven worked examples with the exact results a build must reproduce, known limits;
- the **"Not to be built"** list: measures read in the speech and left out on purpose;
- the **output controls** (`references/output-controls.md`): which parts of the results screen are fixed and which the builder may design;
- the **engine code itself**, in full, as an appendix. The builder pastes it into the page and calls its API instead of re-implementing the rules, so the checker runs exactly the tested logic.

**Hand over only `BRAIN-2026.md`.** When the user asks for the brain, the spec, or something to give Claude Code, send that one file. The engine travels inside it; don't send the `.js` file, JSON files or other working files separately. The user builds the checker from the Markdown in a separate step.

`BRAIN-2026.md` is generated, never edited by hand: `node scripts/export-brain-md.js`. Round 1 of verification (`test.js`) fails if it is out of date with the engine.

### Files in this skill (internal)

| File | What it is | When to use it |
|---|---|---|
| **`BRAIN-2026.md`** | **The hand-over spec**, generated from the engine | Send this to the user |
| `references/output-controls.md` | Which parts of the results screen are fixed (`locked`) and which the builder may design (`undecided`). Copied into `BRAIN-2026.md` | When the user decides how the output must look: edit the status or rule, then regenerate |
| `scripts/export-brain-md.js` | Writes `BRAIN-2026.md` from the engine, running it for rates, reasons, advisories and worked examples | After any change to the engine or the ledger's exclusions |
| `scripts/belanjawan2026-brain.js` | The engine: questions, 13 themes, 115 items, STR/SARA calculator, rule evaluator. Source of truth for the spec | Edit here when logic or wording changes |
| `references/excluded-2026.md` | The "not to be built" list on its own (also the last section of `BRAIN-2026.md`). Generated from the ledger | Regenerate when exclusions change |
| `scripts/test.js` | Verification round 1: 15,169 checks (speech figures, branching, personas, results groups, integrity, Bahasa Melayu lint, "no government-spending figures" lint, spec up to date) | After any edit: `node scripts/test.js` |
| `scripts/verify2.js` | Verification round 2: 30,000 simulated users walking the real question flow and checking invariants | After any edit: `node scripts/verify2.js` |
| `scripts/gen-spec.js` | Regenerates the question and rule tables for the design spec below | After any edit: run it, then paste `_generated.md` into the spec |
| `references/LOGIK-BELANJAWAN-2026.md` | Design record: decisions, tiers, every question and rule with sources, verification record, the user's decisions (§9) | Read before changing logic |
| `references/bm-style.md` | Bahasa Melayu style guide (incl. user corrections such as no "makan gaji") | Read before writing or editing any user-facing text |
| `references/building-a-new-brain.md` | Method for rebuilding the brain for a new document (e.g. Belanjawan 2027) | Read when the source document changes |
| `scripts/split-source.js` | Splits a speech (Markdown or `pdftotext` output) into numbered units (paragraph bullets, Lampiran I items, Lampiran II entries) and flags the ones likely to affect a person | First step of any rebuild or source check: `node scripts/split-source.js ub27.md` |
| `scripts/text-signals.js` | The word signals behind the flags, learned from the 2024–2026 speeches | Extend when a rebuild finds a measure it didn't flag |
| `scripts/learn-programmes.js` | Learns citizen programme names across years; lists programmes missing from the newest speech | Rebuild step 1, with all past speeches |
| `scripts/coverage.js` | Fails unless every unit has a ledger decision and every brain item traces to a unit | After any edit that touches items: `node scripts/coverage.js ub26.md references/ledger-2026.tsv --brain scripts/belanjawan2026-brain.js` |
| `references/ledger-2026.tsv` | One decision per unit of Ucapan Belanjawan 2026, built from the text only; open `gap`/`ask` rows are questions for the user | Read before adding items; update it with every item change |
| `references/programmes.json` | Citizen programmes learned from past speeches (data file for the scorer) | Internal; read for the cross-year view |
| `references/text-signals.md` | How the text-only method works, its measured recall, and what three years of speeches taught | Read before a rebuild or when extending the signals |
| `scripts/benchmark.js` | Scores the flagging against a blind answer key, learning programme names only from earlier years | After changing `text-signals.js` or `learn-programmes.js`: `node scripts/benchmark.js ub26.md references/ledger-2026.tsv --learn-from ub24.md ub25.md` |
| `scripts/annotate-source.js` | Writes `excluded-<year>.md`, and the speech as HTML/PDF with used units shaded light green and excluded units yellow | Hand-over (rebuild step 9). Send the user the PDF as a review aid |
| `references/ledger-2025.tsv` | Blind answer key for all 1,210 units of Ucapan Belanjawan 2025 (labels only; there is no 2025 brain) | Benchmark key, and last year's baseline when rebuilding for 2027 |

**Build only what the brain contains.** The "Not to be built" section lists measures that were read and left out on purpose: the Lemon Law, the electricity tariff change, the non-citizen stamp duty, rare-disease funding, free helmets and others. If the user wants one, it goes through step 5 and into the engine first, then the spec is regenerated.

**Card tiers** (defined in the spec, section 4): `layak` Berkemungkinan layak; `semak` Semak kelayakan (means-tested, check with the agency); `mungkin` Mungkin layak (depends on something skipped). The results screen shows two groups (`evaluate().groups`): "Berkemungkinan layak" (layak), then "Mungkin layak" (semak, then mungkin). Cost changes are tiered the same way and shown with no warning label (the user's decision).

## Changing the logic

1. Edit `QUESTIONS`, `deriveFacts()` or `BENEFITS` in `scripts/belanjawan2026-brain.js`. Rules are declarative JSON, e.g. `{ all: [{ f:'age', gte:40, why:'Berumur 40 tahun ke atas' }, { f:'strEligible', eq:true, why:'…' }] }`, with operators `eq ne in nin gt gte lt lte has hasAny` and groups `all any not`.
2. Follow the user's standing requirements:
   - Output states **what the person gets or pays**, never government allocation totals or beneficiary counts. The lint fails otherwise.
   - **Don't add overly personal questions** unless a rule truly needs them, and every question except age and region must be skippable (appended automatically).
   - **Eight questions are mandatory** (the user's decision): always asked, with this wording, and skippable like the rest. Gender, job, children aged 17 or under, OKU, active driving licence, STR or SARA recipient, PTPTN borrower and KWSP contributor (`gender`, `employment`, `has_minor_children`, `oku`, `license`, `str_status`, `ptptn`, `kwsp`). They go to every adult; OKU and licence also go to minors. Don't remove them, fold them into a multi-select, or hide them behind another answer. `test.js` section M checks this.
   - **Special cases** (smokers, alcohol, investors and similar) belong in the `special` theme, as `kind: 'kesan'` when they cost the person more. They are shown like any other card, with no warning label.
   - **Work from the text only.** Every item needs a `src` reference to a unit of the speech or its annexes. Take amounts, criteria and dates from the text, not the web; where the text is silent, use `certainty: 'check'` and ask the user. Put date-sensitive facts in `timing`. Leave `web` empty on new items.
   - Record every item change in `references/ledger-2026.tsv` (the unit's decision becomes `item:<id>`), then run `scripts/coverage.js`.
   - **When you're unsure whether an item belongs in the brain, or in which theme, ask the user.** Don't decide silently. Use the Q&A format in step 5 of `references/building-a-new-brain.md`, and always leave room for the user to say something else.
3. **Run verification twice, every time:** `node scripts/test.js && node scripts/verify2.js`. Both must pass with 0 failures and all items reachable. Add a persona test for any new rule, and add any new wording mistake you fix to the lint's banned list.
4. Run `node scripts/gen-spec.js` and update the tables in `references/LOGIK-BELANJAWAN-2026.md`. Bump `VERSION` and `DATA_AS_OF`.
5. Regenerate the hand-over: `node scripts/export-brain-md.js`. Test round 1 fails until you do.

## Rebuilding for a new document (e.g. Belanjawan 2027)

Read `references/building-a-new-brain.md` and follow its nine steps:

1. Split the source into units and start the ledger.
2. Keep only citizen end results.
3. Take eligibility from the text (this year's, then past years').
4. Theme the items.
5. **Check with the user.**
6. Design minimal skippable questions.
7. Write the rules.
8. Verify twice, plus the coverage check.
9. Hand over. This includes `excluded-<year>.md`, the "not to be built" list, and the annotated speech PDF for the user: light green for what the brain uses, yellow for what was excluded.

**Text only.** The user wants the brain pulled from the speech, Lampiran I and Lampiran II, not the web. Coverage comes from the ledger, not from keywords: every unit of the text gets a decision, and `coverage.js --final` fails if one is missing or still open. Lampiran I carries measures the speech never mentions, so read it as a source, not only for amounts. `references/text-signals.md` explains the method.

Step 5 isn't optional. Before writing any questions, put the item list to the user as questions and answers in the conversation. Use `AskUserQuestion` where it's available; its "Other" choice lets the user say something else. Cover:

- borderline include/exclude items;
- how to target area-specific items;
- theme placement;
- excluded items worth restoring;
- any new personal question.

Always raise lifestyle costs (smokers, vape, alcohol) and area-specific tax or duty exemptions (e.g. duty-free islands). Earlier rebuilds dropped both without a word. Record the answers in the spec's **Keputusan pengguna** section.

Keep the engine and replace the data. Keep 2026 as its own versioned file, not overwritten.

## Known limits (tell the user when relevant)

- **Income bands approximate B40/M40** (≤ RM5,000 / ≤ RM12,000).
- **Spouse's age isn't asked**, so a 40+ spouse doesn't trigger PeKa B40.
- **Bumiputera-only programmes** are folded into broader cards, with the restriction in the text.
- **Portal links should be verified** before launch.
- **2026 decisions are recorded.** Every unit of the 2026 speech has a ledger decision, and the user's step-5 choices are in the spec's **Keputusan pengguna** section. A blind re-read of the unflagged units (27 Sep 2026) found 10 more measures; the user decided them the same day (micro loans, care-worker courses and the PTPTN travel ban added; seven excluded). The text gives no per-person amount for the pensioners' special appreciation payment or the imam/KAFA/takmir allowance, so those items are `semak`.
- **Langkawi residents can't be targeted.** The region question has no Langkawi option, so the vehicle-exemption cap is shown to Labuan residents and names Langkawi in its text.
- **Budget 2027** (due Oct 2026) will supersede this data.
