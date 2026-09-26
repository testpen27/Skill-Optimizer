---
name: belanjawan-brain
description: |
  UI-free "brain" (JS logic engine) for an interactive Malaysian Budget 2026 citizen-benefits Q&A ("Semak faedah Belanjawan", `B26Brain`, `brain.js`). Trigger when the user wants to touch this engine's code: wire its `evaluate()` output into a front end (WordPress, React, vanilla HTML); add, change or re-theme its questions, benefits, tiers or rules; edit or fix its Bahasa Melayu wording; run or extend `test.js`/`verify2.js` verification; inspect its output fields or files; or rebuild the same rule-based Q&A engine for a new source document (Belanjawan 2027, a state budget, another policy text). Also trigger on mentions of "belanjawan-brain", "B26Brain", "kalkulator faedah", or "soal jawab belanjawan", even unnamed.

  Do NOT trigger for someone just asking what's in Budget 2026, wanting a plain-language summary of tax reliefs/benefits/prices, or any question answerable by reading the budget speech itself -- that's a content question, not a tool-building one.
---

# Belanjawan Brain — Belanjawan 2026 Q&A

A self-contained logic engine (no UI, no dependencies) that turns a person's answers into a personalised, themed list of what Budget 2026 means for them. The UI is built separately; this skill is the brain.

---

## ⭐ OUTPUTS — what this skill gives you

### A. Files in this skill

| File | What it is | When to use it |
|---|---|---|
| **`scripts/belanjawan2026-brain.js`** | **The brain.** Questions, 13 themes, 94 items, STR/SARA calculator, rule engine. UMD: `window.B26Brain` in the browser, `require()` in Node. | Load it in the front end. This is the only file the UI needs. |
| `scripts/test.js` | Verification round 1: 12,362 checks (speech figures, branching, personas, integrity, Bahasa Melayu lint, "no government-spending figures" lint) | After any edit: `node scripts/test.js` |
| `scripts/verify2.js` | Verification round 2: 30,000 simulated users walking the real question flow and checking invariants | After any edit: `node scripts/verify2.js` |
| `scripts/gen-spec.js` | Regenerates the question and rule tables from the code | After any edit: run it, then paste `_generated.md` into the spec |
| `references/LOGIK-BELANJAWAN-2026.md` | Full spec: design, tiers, STR table, every question and rule with sources, verification record | Read before changing logic |
| `references/sample-output.json` | A real `evaluate()` result (single mother, 45) | Read before building the results screen |
| `references/bm-style.md` | Bahasa Melayu style guide (incl. user corrections such as no "makan gaji") | Read before writing or editing any user-facing text |
| `references/building-a-new-brain.md` | Method for rebuilding the brain for a new document (e.g. Belanjawan 2027) | Read when the source document changes |
| `scripts/split-source.js` | Splits a speech (Markdown or `pdftotext` output) into numbered units (paragraph bullets, Lampiran I items, Lampiran II entries) and flags the ones likely to affect a person | First step of any rebuild or source check: `node scripts/split-source.js ub27.md units27.json` |
| `scripts/text-signals.js` | The word signals behind the flags, learned from the 2024–2026 speeches | Extend when a rebuild finds a measure it didn't flag |
| `scripts/learn-programmes.js` | Learns citizen programme names across years; lists programmes missing from the newest speech | Rebuild step 1, with all past speeches |
| `scripts/coverage.js` | Fails unless every unit has a ledger decision and every brain item traces to a unit | After any edit that touches items: `node scripts/coverage.js ub26.md references/ledger-2026.tsv --brain scripts/belanjawan2026-brain.js` |
| `references/ledger-2026.tsv` | One decision per unit of Ucapan Belanjawan 2026, built from the text only; open `gap`/`ask` rows are questions for the user | Read before adding items; update it with every item change |
| `references/programmes.json` | Citizen programmes learned from past speeches, with the years each appears | Used by the scorer; read for the cross-year view |
| `references/text-signals.md` | How the text-only method works, its measured recall, and what three years of speeches taught | Read before a rebuild or when extending the signals |

### B. What the brain returns at runtime — `B26Brain.evaluate(answers)`

```js
{
  version: '2026.3', dataAsOf: '2026-09-25',
  strSara: {                       // cash estimate card
    eligible: true | false | null, // null = user skipped something needed
    category, label, str, sara, saraMonthly, total,
    totalRange?,                   // when number of children was skipped
    totalIfEkasih?,                // when eKasih answered "Tidak pasti"
    reason                         // BM sentence when not eligible / unknown
  },
  byTheme: [                       // ← render this: themes in display order, items pre-sorted
    { id, label, count, items: [
      { id, kind: 'manfaat' | 'kesan',
        tier: 'layak' | 'semak' | 'mungkin' | 'kesan', tierLabel,
        title, value, summary, who, action,  // all in Bahasa Melayu, ready to display
        reasons: [...],                      // why it matched ("Berumur 40 tahun ke atas")
        needsConfirm: [...],                 // what the user skipped (for 'mungkin')
        timing, src, web, portal }           // date note, speech reference, links
    ]}
  ],
  advisories: [{ type: 'action' | 'info' | 'disclaimer', text }], // show above or below results; disclaimer is always last
  counts: { total, layak, semak, mungkin, kesan }
}
```

**Tiers to show the user** (labels in `B26Brain.TIERS`):

| Tier | Label | Meaning |
|---|---|---|
| `layak` | Berkemungkinan layak | Likely eligible |
| `semak` | Semak kelayakan | Means-tested or selective; the person should check with the agency |
| `mungkin` | Mungkin layak | Depends on something the person skipped; show `needsConfirm` |
| `kesan` | Perubahan yang menjejaskan anda | A cost increase or new obligation (tobacco, alcohol, clinic fees, LLP tax). Style it differently from benefits. |

---

## Integrating into a front end (the usual Claude Code task)

The UI must **only call the API** and never re-implement eligibility logic, because the rules are verified and duplicating them breaks that guarantee.

```js
let answers = {};
function next() {
  const q = B26Brain.getVisibleQuestions(answers).find(q => answers[q.id] === undefined);
  if (!q) return renderResults(B26Brain.evaluate(answers));
  renderQuestion(q);
}
function onAnswer(id, value) {                         // value: number | string | string[]
  answers = B26Brain.pruneAnswers({ ...answers, [id]: value });   // drops answers to questions that became hidden
  next();
}
```

Rendering rules:

- **`q.type`** is `number` (age), `single` or `multi`.
- **Exclusive options:** an option with `exclusive: true` ("Tiada yang berkaitan", "Tidak mahu menyatakan") must clear the other selections in a multi-select.
- **Skip:** the option with `skip: true` (value `'skip'`) can be shown as a separate "Langkau" link instead of a normal button. Only `age` and `region` have no skip.
- **Help text:** show `q.help` as small text under the question when present.
- **Back navigation:** remove the answer from `answers`, then call `next()`.
- **Results screen:**
  - Show the STR/SARA card first. Show a range when `totalRange` or `totalIfEkasih` is present.
  - Then show `byTheme`, and each item's `reasons` as "Kenapa anda layak".
  - Label `timing` items as time-sensitive. Several are already past, e.g. Penghargaan SARA (Feb 2026).
  - Always show the disclaimer advisory.
- **WordPress:** load the brain with `<script src=".../belanjawan2026-brain.js"></script>` before the UI script, or inline it in a Custom HTML block. It is plain ES5 with no build step.
- **Don't rewrite the Bahasa Melayu text in the UI.** It has been reviewed. Edit it in the brain, following `references/bm-style.md`, then re-run verification.

## Changing the logic

1. Edit `QUESTIONS`, `deriveFacts()` or `BENEFITS` in `scripts/belanjawan2026-brain.js`. Rules are declarative JSON, e.g. `{ all: [{ f:'age', gte:40, why:'Berumur 40 tahun ke atas' }, { f:'strEligible', eq:true, why:'…' }] }`, with operators `eq ne in nin gt gte lt lte has hasAny` and groups `all any not`.
2. Follow the user's standing requirements:
   - Output states **what the person gets or pays**, never government allocation totals or beneficiary counts. The lint fails otherwise.
   - **Don't add overly personal questions** unless a rule truly needs them, and every question except age and region must be skippable (appended automatically).
   - **Special cases** (smokers, alcohol, investors and similar) belong in the `special` theme, as `kind: 'kesan'` when they cost the person more.
   - **Work from the text only.** Every item needs a `src` reference to a unit of the speech or its annexes. Take amounts, criteria and dates from the text, not the web; where the text is silent, use `certainty: 'check'` and ask the user. Put date-sensitive facts in `timing`. Leave `web` empty on new items.
   - Record every item change in `references/ledger-2026.tsv` (the unit's decision becomes `item:<id>`), then run `scripts/coverage.js`.
   - **When you're unsure whether an item belongs in the brain, or in which theme, ask the user.** Don't decide silently. Use the Q&A format in step 5 of `references/building-a-new-brain.md`, and always leave room for the user to say something else.
3. **Run verification twice, every time:** `node scripts/test.js && node scripts/verify2.js`. Both must pass with 0 failures and all items reachable. Add a persona test for any new rule, and add any new wording mistake you fix to the lint's banned list.
4. Run `node scripts/gen-spec.js` and update the tables in `references/LOGIK-BELANJAWAN-2026.md`. Bump `VERSION` and `DATA_AS_OF`.

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
9. Hand over.

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
- **The 2026 ledger has open questions.** A text-only read of Ucapan Belanjawan 2026 found measures the brain doesn't have yet, such as the Langkawi and Labuan vehicle tax exemption cap, PERKESO dialysis rates and the KEMAS contract-pensioner allowance. These are `gap` rows, and borderline cases are `ask` rows. Resolve them with the user before calling the 2026 data complete.
- **Budget 2027** (due Oct 2026) will supersede this data.
