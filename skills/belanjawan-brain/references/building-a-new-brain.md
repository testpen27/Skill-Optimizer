# Building a new brain from a new document

Use this when the user wants the same Q&A for a new source, such as Belanjawan 2027, a state budget or another policy text. The Belanjawan 2026 brain in `scripts/belanjawan2026-brain.js` is the reference implementation. Copy it and replace the data; keep the engine (DSL, evaluator, prune, tiers) unchanged.

**Work from the text only.** The user wants the brain built from the speech and its annexes, not from the web. Don't search online for criteria, amounts or updates. What the text doesn't say becomes a `semak` item or a question for the user (step 5). `references/text-signals.md` explains the method and what three years of speeches taught.

## Contents
1. Split the source and start the ledger
2. Keep only end results for people
3. Take eligibility from the text
4. Theme the items
5. Check with the user (Q&A)
6. Design the questions
7. Write the rules
8. Verify twice
9. Hand over

## 1. Split the source and start the ledger

- Get the text: a Markdown export of the speech, or `pdftotext -layout` on the PDF. It must include the speech, **Lampiran I** (Ringkasan) and **Lampiran II** (Langkah Cukai).
- Split it into numbered units:
  ```bash
  node scripts/split-source.js ub27.md units27.json
  ```
  It fails if paragraph or Lampiran I numbering has a gap. Fix the extraction before going on, because a gap is lost text. Each unit gets a reference (`Perenggan 184 (butiran 2)`, `Lampiran I Bil. 29`, `Lampiran II — Lampiran 36`), the signals it contains, and `flagged: true` if it is likely to affect a person.
- Update what past speeches taught, then see the cross-year view:
  ```bash
  node scripts/learn-programmes.js ub25.md ub26.md ub27.md --out references/programmes.json
  ```
  It prints programmes in every year, programmes **missing from the new speech** (add each as a `prev:` ledger row and ask the user in step 5 whether it continues), and new programmes.
- Start `references/ledger-<year>.tsv` with one row per unit (see `references/ledger-2026.tsv` for the format and `scripts/coverage.js` for the decisions). Read flagged units closely: each needs `item:<id>`, `gap`, `ask` or `exclude:<reason>`. Unflagged units may be `bulk`, but still skim them. The score only orders the reading; it doesn't decide anything.
- Read all three layers as sources:
  1. The **speech body**. One paragraph often holds several measures. Perenggan 184 (2026) holds five, and its lead-in names none of them.
  2. **Lampiran I**. It has measures the speech never mentions; in 2026 these include the pensioners' special appreciation payment, APEL.Q and LiKES. It is not only a table of amounts.
  3. **Lampiran II**. Each entry gives *Kedudukan Semasa* (current rule), *Cadangan* (the change) and *Tarikh Kuat Kuasa* (when it starts). That is enough for a tax item without any other source.
- Record the unit reference in each item's `src` as you go. A Markdown export has no page numbers, so cite paragraph and Lampiran numbers.

## 2. Keep only end results for people

The user's rule: **focus on what the citizen gets or pays, not how much the government spends.**

- **Include:**
  - Cash, credits and allowances.
  - Subsidised prices, free services and loans or guarantees open to individuals.
  - Tax reliefs.
  - Duty or price *increases* (e.g. tobacco, alcohol) and new obligations (e.g. a new tax), as `kind: 'kesan'`.
  - One-offs, with a `timing` note.
- **Exclude:** allocation totals, beneficiary counts, corporate or investment incentives, state infrastructure lists, defence procurement and fiscal statistics.
- **Not the same as excluded:** tax or duty exemptions tied to an area (e.g. duty-free islands) are not "state infrastructure", and tobacco or alcohol duty rises are not "fiscal statistics". Keep them, and put them on the borderline list for step 5 if you're unsure.
- **Rewrite rule:** "RM3.1 bilion untuk 560,000 penerima JKM" becomes "Bantuan bulanan mengikut kategori". The `value` field says what *one person* receives.

## 3. Take eligibility from the text

Speeches state amounts more often than criteria. Look for the criteria in this order, and stop at the first that answers:

1. **The same unit and its paragraph.** Read the whole paragraph, not just the bullet, because the condition often sits in the lead-in.
2. **The matching Lampiran I entry.** It often states who qualifies. In 2026, Lampiran I Bil. 26 says MyLesen B2 covers secondary pupils, students and youth from low-income families.
3. **Lampiran II's *Kedudukan Semasa*** for tax items, which states the rule being changed.
4. **Past years' speeches.** A continuing programme's criteria are often stated in the year it started or changed. For example, the 2025 Lampiran I gives i-Suri's 50% government match (up to RM300 a year and RM3,000 lifetime), and the 2026 speech only adds the age limit of 60. Use `references/programmes.json` to find the years a programme appears in.

If no text states the criteria:

- Make the item `certainty: 'check'` (tier `semak`).
- Say in `who` only what the text supports.
- Add it to the step 5 questions: "The text doesn't say who qualifies for X. Show it as *semak*, or do you want to state the criteria?"

In the three speeches from 2024 to 2026, for example, PeKa B40's rule (age 40 and above, STR recipient) and BUDI95's monthly quota are never stated. Don't fill such gaps from memory or the web.

Watch for **name collisions**: "PEKA" in the 2024–2026 speeches is *Peluang Kedua Anda* (prisons), not PeKa B40. Match programme names with their capitalisation and read the unit.

Put date-sensitive facts from the text in `timing` (e.g. *Tarikh Kuat Kuasa*). Leave `web` empty for new items; the field is kept only for the 2026 data. Update `DATA_AS_OF` to the date of the speech text.

## 4. Theme the items

Group by the citizen's point of view, not by ministry. The 2026 themes (13):

| Theme | Covers |
|---|---|
| `cash` | Cash aid and cost of living |
| `subsidy` | Fuel and energy subsidies |
| `health` | Health and insurance |
| `education` | Education |
| `housing` | Housing |
| `protection` | Social protection and retirement savings |
| `family` | Family and women |
| `youth` | Youth, training and jobs |
| `vulnerable` | OKU, elderly and vulnerable groups |
| `sector` | By occupation: civil servants, veterans, fishermen, farmers, taxis |
| `mobility` | Transport and mobility |
| `tax` | Individual tax reliefs |
| `special` | **Kes Khas:** lifestyle (tobacco, alcohol, vape), investing, price changes |

The `special` theme exists because the user explicitly wants cases like smokers covered. Always look for such items in Lampiran II's duty changes.

## 5. Check with the user (Q&A)

Once the text is analysed and the items are themed, stop. Check the item list with the user before designing any questions or rules. What goes in the brain, and under which theme, is the user's call. Past rebuilds went wrong at this point: the smokers section and area-specific tax exemptions were dropped without a word because they looked niche. Verification can't catch a dropped item. `verify2.js` proves the items you wrote are reachable, not that you wrote the right items.

### How to ask

- Ask as questions and answers in the conversation, not in a file or an HTML page.
- In Claude Code, use the `AskUserQuestion` tool: up to 4 questions per call, 2–4 options each. It adds an "Other" choice automatically, which is how the user says something else, so don't add your own.
- Where that tool isn't available, number the questions and letter the options. Always end each question with "(x) Something else: tell me in your own words". Then wait for the reply before going on.
- Put your recommended option first, labelled "(Recommended)", with a one-line reason. In each option's description, say what it does to the brain, e.g. "Adds a `kesan` item in `special`, shown only to smokers".
- Quote the source (`perenggan` / `ms`) in the question so the user can check it.
- Ask in rounds, most important first. A typical rebuild takes 3–5 rounds.
- When the user answers with "Other", do what they wrote. If it's unclear, ask a follow-up before moving on.

### What to check, in this order

**1. Borderline items: include or not?** List every item you hesitated over. Also list every item in the categories below, even if you didn't hesitate, because these are the ones that get dropped:

| Always ask about | Why it gets dropped | Where to look |
|---|---|---|
| Lifestyle costs: cigarettes, cigars, heated tobacco, vape, alcohol, sugary drinks, gambling | It reads as a tax, not a benefit | Lampiran II duty changes |
| Area-specific tax or duty exemptions: duty-free islands (Langkawi, Labuan, Tioman, Pangkor), special zones and corridors, Sabah/Sarawak-only measures, interior or rural areas | It only applies in some places, and the region question may be too coarse to target it | Lampiran II; the speech's sections on the states |
| Help that reaches individuals through a small business (sole proprietor, hawker, gig worker, micro-SME) | It looks like a corporate incentive | Speech business section, Lampiran I |
| Measures announced but not decided ("dikaji", "akan diperkenalkan") | There is no firm amount | Speech body |
| One-offs that have passed or are about to expire | They look stale | `timing` notes |
| Restricted groups (Bumiputera-only, one state, one occupation) | They look too narrow | Lampiran I |

**Where the list comes from:** every `gap` and `ask` row in the ledger, and every `prev:` row (programmes or items from last year that the new text doesn't mention). The ledger covers every unit, so this list is complete in a way a keyword search isn't. As a cross-check, sweep for the categories above and confirm each hit has a ledger decision:

```bash
grep -inE "tembakau|rokok|cerut|vape|alkohol|minuman bergula|judi|bebas cukai|bebas duti|pengecualian cukai kenderaan|langkawi|labuan|tioman|pangkor|zon |koridor|pedalaman|luar bandar|dikaji|akan diperkenal" ub27.md
```

Give each item these options: **Include** (as `layak` or `kesan`), **Include as `semak`** (the person checks with the agency), or **Exclude**. "Other" comes on top of these.

Example round:

> **Q1. Cigarette duty goes up 40 sen a pack (Perenggan 184, ms 102). Include it?**
> - Include as `kesan` in `special`, shown only to smokers (Recommended: you asked for smokers to be covered)
> - Include as general information for everyone
> - Exclude
>
> **Q2. The vehicle tax exemption in Langkawi and Labuan is limited to vehicles worth up to RM300,000 from 1 January 2026 (Perenggan 27). Include it?**
> - Include as `kesan` for Labuan residents and as `semak` with Langkawi named in `who` (Recommended: the region question has Labuan but can't identify Langkawi residents)
> - Include, and add a way to identify Langkawi residents (see check 2)
> - Exclude

**2. Targeting area-specific items.** An included item may apply only in places the current questions can't identify. For example, the 2026 region question offers only Semenanjung, Sabah, Sarawak and Labuan, so a Langkawi resident can't be picked out. Ask how to handle it:
- show it to everyone as `semak` and name the area in `who`;
- add an option to the region question;
- add a follow-up question shown only in that region.

Remind the user of their own rule against unnecessary questions.

**3. Themes.** Show the theme table with the item count for each theme, then list the items whose theme could go either way. For each one, ask whether to keep your proposed theme or move it to the alternative. Also ask whether a new theme is needed or an existing one should go.

**4. Excluded items: bring any back?** Show everything step 2 dropped, grouped by reason. Ask one multi-select question listing the likeliest items to restore. The user can name any other item through "Other".

**5. New questions that may feel personal.** An included item may need a fact the brain doesn't ask for yet, such as a health condition, religion, disability or debt. Confirm the wording with the user and check the question is worth asking. The alternative is to show the item as `semak` without asking.

### Record the answers

- Update the ledger row for each question: `ask`/`gap` becomes `item:<id>` or `exclude:user` with the user's words in the note. `prev:` rows become `carried` or `dropped`.
- Add a **Keputusan pengguna** (user decisions) section to the new spec, with one row per decision: the item, the decision, the user's own words if they chose "Other", and the date.
- Give every item the user chose to include a persona test in `test.js`, so a later edit can't drop it silently. Keep every exclusion listed in the spec so it isn't asked again.
- Don't re-ask a decision recorded in the previous year's spec unless the new source changes it. Tell the user it has been carried over.

## 6. Design the questions

- **Ask only what a rule needs.** If no rule tests a fact, don't ask for it.
- **Don't ask overly personal questions** unless a rule truly needs them. Examples the user rejected:
  - Civil-service grade and appointment type. Instead, show those items as `semak` and put the grade in the `who` text.
  - Fertility status.
- **Only age and region are required.** Every other question gets the auto-appended "Tidak mahu menyatakan" (`skip`).
- **Handle skips honestly:**
  - A skipped single-choice answer becomes an unknown fact, so results show as `mungkin`.
  - A skipped multi-choice answer means none were selected, and an advisory lists what was skipped.
- **Use branching (`showIf`)** so people only see relevant questions. For example, `farm_type` appears only for farmers, and `lifestyle` only for adults.
- **Match income bands to real cut-offs.** In 2026 these were RM2,500 / RM5,000 / RM6,000 / RM12,000, and ages 16 / 18 / 21 / 30 / 35 / 40 / 60.

## 7. Write the rules

- Use facts, not raw answers. Add derived facts in `deriveFacts()` (e.g. `b40`, `ipt`, `smoker`).
- Give every leaf condition a `why` in Bahasa Melayu. It becomes the explanation shown to the user.
- Set `certainty: 'check'` when the programme is means-tested, quota-based or depends on something not asked.
- Any fact that can be skipped must be pushed into `facts._unknown` in `deriveFacts()`. Otherwise a skip silently reads as "no".

## 8. Verify twice (mandatory)

- **Round 1:** `node scripts/test.js`.
  - Update the STR/SARA figure tests to the new table.
  - Keep the language lint and the spending lint.
  - Mutation-test the lints: inject a known-bad string and confirm it is caught.
- **Round 2:** `node scripts/verify2.js`. This randomised simulation must show:
  - All items reachable.
  - 0 invariant violations.
  - If an item is "never shown", check the simulator before blaming the brain (in 2026 it was a harness bug).
- **Manual read:** dump every user-facing string and read it in full against `bm-style.md`. Add every error you fix to the lint's banned list.
- **Decision check:** every "include" row in **Keputusan pengguna** must have an item in `BENEFITS` and a persona test that shows it. Every "exclude" row must have no item.
- **Coverage check:** `node scripts/coverage.js ub27.md references/ledger-2027.tsv --brain scripts/belanjawan2027-brain.js --final`. It must pass: every unit decided, no flagged unit bulk-excluded, every brain item traced to a unit, and no `gap`/`ask` left open.
- **Signal check:** if you found a person-level measure the scorer didn't flag, add the phrase that should have caught it to `scripts/text-signals.js` (see `references/text-signals.md`).

## 9. Hand over

- Run `node scripts/gen-spec.js` to regenerate the tables in the spec.
- Bump `VERSION`.
- Tell the user the pass counts from both rounds.
- List the step 5 decisions in a few lines so the user can see their choices were applied.
