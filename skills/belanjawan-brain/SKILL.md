---
name: belanjawan-brain
description: UI-free "brain" for an interactive citizen-benefits Q&A ("Semak faedah Belanjawan"). It asks a person branching questions (age, region, household, income, work, situation, lifestyle) and returns the Malaysian Budget 2026 benefits, tax reliefs and price changes that apply to them, themed and tiered, with STR/SARA cash estimates and page references to the budget speech. Use this skill whenever the user wants to plug the Belanjawan 2026 Q&A logic into a front end (WordPress, React, vanilla HTML, Claude Code); change, add or re-theme benefits, questions or rules; fix Bahasa Melayu wording in the Q&A; run or extend its verification; or rebuild the same kind of Q&A for a new document such as Belanjawan 2027, a state budget or another policy text. Also use it when the user mentions "belanjawan-brain", "belanjawan brain", "brain.js", "B26Brain", "kalkulator faedah", "soal jawab belanjawan" or "benefits calculator in text", even without naming the skill.
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
   - Every item needs a `src` reference to the speech. Web-verified details go in `web`, and date-sensitive facts in `timing`.
3. **Run verification twice, every time:** `node scripts/test.js && node scripts/verify2.js`. Both must pass with 0 failures and all items reachable. Add a persona test for any new rule, and add any new wording mistake you fix to the lint's banned list.
4. Run `node scripts/gen-spec.js` and update the tables in `references/LOGIK-BELANJAWAN-2026.md`. Bump `VERSION` and `DATA_AS_OF`.

## Rebuilding for a new document (e.g. Belanjawan 2027)

Read `references/building-a-new-brain.md` and follow its eight steps: read the speech and both annexes, keep only citizen end results, web-verify eligibility, theme, design minimal skippable questions, write rules, verify twice, then hand over. Keep the engine and replace the data. Keep 2026 as its own versioned file, not overwritten.

## Known limits (tell the user when relevant)

- **Income bands approximate B40/M40** (≤ RM5,000 / ≤ RM12,000).
- **Spouse's age isn't asked**, so a 40+ spouse doesn't trigger PeKa B40.
- **Bumiputera-only programmes** are folded into broader cards, with the restriction in the text.
- **Portal links should be verified** before launch.
- **Budget 2027** (due Oct 2026) will supersede this data.
