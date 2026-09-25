# Building a new brain from a new document

Use this when the user wants the same Q&A for a new source, such as Belanjawan 2027, a state budget or another policy text. The Belanjawan 2026 brain in `scripts/belanjawan2026-brain.js` is the reference implementation. Copy it and replace the data; keep the engine (DSL, evaluator, prune, tiers) unchanged.

## Contents
1. Read the source properly
2. Keep only end results for people
3. Verify eligibility on the web
4. Theme the items
5. Design the questions
6. Write the rules
7. Verify twice
8. Hand over

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

## 5. Design the questions

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

## 6. Write the rules

- Use facts, not raw answers. Add derived facts in `deriveFacts()` (e.g. `b40`, `ipt`, `smoker`).
- Give every leaf condition a `why` in Bahasa Melayu. It becomes the explanation shown to the user.
- Set `certainty: 'check'` when the programme is means-tested, quota-based or depends on something not asked.
- Any fact that can be skipped must be pushed into `facts._unknown` in `deriveFacts()`. Otherwise a skip silently reads as "no".

## 7. Verify twice (mandatory)

- **Round 1:** `node scripts/test.js`.
  - Update the STR/SARA figure tests to the new table.
  - Keep the language lint and the spending lint.
  - Mutation-test the lints: inject a known-bad string and confirm it is caught.
- **Round 2:** `node scripts/verify2.js`. This randomised simulation must show:
  - All items reachable.
  - 0 invariant violations.
  - If an item is "never shown", check the simulator before blaming the brain (in 2026 it was a harness bug).
- **Manual read:** dump every user-facing string and read it in full against `bm-style.md`. Add every error you fix to the lint's banned list.

## 8. Hand over

- Run `node scripts/gen-spec.js` to regenerate the tables in the spec.
- Bump `VERSION`.
- Tell the user the pass counts from both rounds.
