# Building a new brain from a new document

Use this when the user wants the same Q&A for a new source, such as Belanjawan 2027, a state budget or another policy text. The Belanjawan 2026 brain in `scripts/belanjawan2026-brain.js` is the reference implementation. Copy it and replace the data; keep the engine (DSL, evaluator, prune, tiers) unchanged.

## Contents
1. Read the source properly
2. Keep only end results for people
3. Verify eligibility on the web
4. Theme the items
5. Check with the user (Q&A)
6. Design the questions
7. Write the rules
8. Verify twice
9. Hand over

## 1. Read the source properly

- Budget PDFs are long (the 2026 speech is 362 pages). Extract text with `pdftotext -layout`, then read three layers:
  1. The **speech body**, for announcements and wording.
  2. **Lampiran I** (Ringkasan), for the exact amounts, criteria and tables. The STR/SARA matrix lives here.
  3. **Lampiran II** (Langkah Cukai), for tax reliefs, duty changes and effective dates.
- Search the text for items that affect people, including costs as well as benefits: `grep -i "percuma|diskaun|rebat|elaun|bantuan|geran|pengecualian|pelepasan|duti|naik|haji|KWSP"`.
- Record a source (`perenggan` + `ms`, or `Lampiran X, ms Y`) for every item as you go.

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

## 3. Verify eligibility on the web

Speeches give amounts but rarely criteria, and implementation often changes after tabling. For each programme, search for the current criteria and any later change. Examples found for 2026:

- **BUDI95:** the quota was cut from 300L to 200L a month from 1 Apr 2026.
- **i-Suri:** requires eKasih registration.
- **PeKa B40:** requires age 40+ and STR recipient status.
- **MyLesen B2:** the intake had an end date.

Put the confirming URL in `web`, and date-sensitive facts in `timing`. Update `DATA_AS_OF`.

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

Sweep the text for them before asking:

```bash
grep -inE "tembakau|rokok|cerut|vape|alkohol|minuman bergula|judi|bebas cukai|bebas duti|pulau|langkawi|labuan|tioman|pangkor|zon |koridor|pedalaman|luar bandar|dikaji|akan diperkenal" speech.txt lampiran*.txt
```

Give each item these options: **Include** (as `layak` or `kesan`), **Include as `semak`** (the person checks with the agency), or **Exclude**. "Other" comes on top of these.

Example round:

> **Q1. Cigarette duty goes up 40 sen a pack (Perenggan 184, ms 102). Include it?**
> - Include as `kesan` in `special`, shown only to smokers (Recommended: you asked for smokers to be covered)
> - Include as general information for everyone
> - Exclude
>
> **Q2. Duty-free shopping in Langkawi, Labuan and Tioman is extended (Lampiran II, ms …). Include it?**
> - Include as `semak`, with the islands named in `who` (Recommended: the region question can't identify island residents)
> - Include, and add a way to identify island residents (see check 2)
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

## 9. Hand over

- Run `node scripts/gen-spec.js` to regenerate the tables in the spec.
- Bump `VERSION`.
- Tell the user the pass counts from both rounds.
- List the step 5 decisions in a few lines so the user can see their choices were applied.
