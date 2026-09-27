# Benchmark: does the text-only scorer find person-level measures in 2024, 2025 and 2026?

Sources: the three speech texts supplied by the user. No web lookups were made. The scripts are `skills/belanjawan-brain/scripts/benchmark.js` and its helpers. The raw output of every run is in `reports/benchmark/`.

## Short answer

Before this pass, only 2026 had been measured, and that number was flattering: **96% of person-level pieces flagged**. Three things inflated it. The scorer was tuned on 2026. Its programme list had seen 2026. And 838 unflagged 2026 pieces had been marked "nothing for a person" without being read.

Measured fairly, each year learning only from earlier years:

| Year | Answer key | Programme names learned from | Pieces flagged | Person-level pieces caught | Measures caught | Flagged pieces that are person-level |
|---|---|---|---|---|---|---|
| 2024 | sample: all 165 flagged + 150 random unflagged | nothing (cold start) | 36% | **74%** (95% CI 63–82%), estimated | — | 47% |
| 2025 | all 1,210 pieces | 2024 | 33% | **77%** (217 of 282) | **79%** (144 of 183) | 55% |
| 2026 | all 1,279 pieces, after re-reading the 838 | 2024 + 2025 | 33% | **84%** (218 of 261) | **86%** (127 of 147) | 52% |

A measure counts as caught if any of its pieces is flagged. One brain item often appears in both the speech and Lampiran I.

**What this means:** the score catches about three-quarters to four-fifths of what matters. That isn't enough to rely on alone, and it was never meant to be. What guarantees completeness is the ledger, a decision recorded for every piece. This benchmark shows why the ledger rule "read unflagged pieces too" is needed: about 1 in 5 person-level pieces sits among them.

## Comparisons

| Run | Pieces caught | Measures caught |
|---|---|---|
| 2026, earlier claim (tuned on 2026, 838 pieces unread) | 96% | 98% |
| 2026, list learned from all three years (includes 2026) | 85% | 87% |
| 2026, fair (list learned from 2024 + 2025) | 84% | 86% |
| 2026, cold start (no programme list) | 81% | 84% |
| 2025, fair (list learned from 2024) | 77% | 79% |
| 2025, cold start | 76% | 78% |

- **Leakage through the programme list was small.** Learning names from 2026 itself adds only one point. Almost all of the drop from 96% comes from reading the 838 unread pieces.
- **The learned programme list helps little.** A cold start is only 1–2 points worse (see fix 1).
- **2025 is harder than 2026 because of its Lampiran I.** 2025's Lampiran I has 557 pieces, many of them one-line allocations such as "Peruntukan Skim Perubatan MADANI RM100j" with no signal words.

## Where the misses are

| Year | Speech | Lampiran I | Lampiran II (tax) |
|---|---|---|---|
| 2025 | 110 of 137 caught (80%) | 91 of 129 (71%) | 16 of 16 (100%) |
| 2026 | 97 of 116 (84%) | 104 of 128 (81%) | 17 of 17 (100%) |

Tax entries are never missed. The misses fall into three groups:

1. **A programme line with only an allocation.** Most misses are of this kind, and most are in Lampiran I. Examples:
   - "Peruntukan Skim Perubatan MADANI RM100j", "Program Residensi Rakyat (PRR) … RM405j", "Pembiayaan oleh PTPK untuk manfaat lebih 20,000 pelatih", "Program 2 Years Exit Program (2YEP) RM2j" (2025/2026 Lampiran I);
   - "Kerajaan menyediakan 200 juta ringgit untuk meneruskan pelaksanaan Payung Rahmah" (2024 Perenggan 177).

   The programme is plainly for people, but the line names no person-level amount or group.
2. **Words the signal groups don't know.** Examples:
   - *pelatih*, *peserta*, *pekebun kecil*, *pelaut*;
   - *percuma* ("pengedaran topi keledar secara percuma", 2026 L1.34.14);
   - obligations such as *sekatan perjalanan* (PTPTN defaulters' travel ban, 2026 P202.3);
   - rule changes worded as policy ("RUU Kredit Pengguna", 2025 P77; "Dasar Gaji Progresif", 2025 P189).
3. **Things the key counts as person-level that aren't new measures.** These are chicken and egg price floating reported as savings (`exclude:past`), and non-citizen measures (`exclude:non-citizen`). In 2026 they are 7 of the 20 measures with no piece flagged. If these are left out of the key, 2026's measure catch rate rises to about 91%.

Every miss is listed with its text in `reports/benchmark/run-2024.txt`, `run-2025.txt` and `run-2026.txt`.

## Fixes the misses suggest (not applied)

The scorer was **not changed** in this pass. Changing it after seeing the test answers would turn the numbers back into a tuning score. Next year's speech (2027) is the fair test for any of these.

1. **Let the programme learner keep one-word names.** `learn-programmes.js` keeps only names of two or more words (`k.split(' ').length >= 2`). So mySalam, PTPK, PRR, RMR, PLKN, KWAPM, MITRA and 2YEP are never learned. It also needs a name in two speeches, so learning from 2024 alone gives 11 names, against 128 from 2024 + 2025.
2. **Flag every Lampiran I line that names a scheme** (*Skim*, *Program*, *Bantuan*, *Insentif*, *Elaun* followed by a proper name) in a person-facing section. Lampiran I lines are short, so the cost is small.
3. **Add the missing words** from group 2 to `recipient`, `benefit` and a new "obligation" group.
4. **Keep the rule that every unflagged unit is read.** Even with all three fixes, the score will not reach 100%.

## The 2026 re-read: new questions for the user

The blind re-read of the 838 former `bulk` rows in `references/ledger-2026.tsv` found:

- **811 correct exclusions.** They are now recorded by reason: infrastructure 338, business 110, heading 83, governance 82, rhetoric 79, institution 71, allocation 40, past 4, non-citizen 3 and user 1.
- **17 restatements** of items the brain already has, such as PTPK under `latihan_tvet`, the latex incentive and Bantuan Musim Tengkujuh under `pekebun_kecil`, and fishing-vessel grants under `nelayan_elaun`.
- **One piece that repeats something the user already excluded.** P181.1, the basic insurance product, is the same measure as RESET.
- **10 person-level measures the brain doesn't have.** They are recorded as `gap`: P98.1, P156.2, P174.1, P202.3, L1.25.8, L1.28.4, L1.32.20, L1.34.14, L1.35.8 and L1.40.5. The user decided them on 27 Sep 2026. Three were added in brain v2026.5: BSN/TEKUN micro loans (`pinjaman_mikro`), care-worker TVET courses (in `latihan_tvet`) and the PTPTN travel ban (`ptptn_sekatan_perjalanan`, `kesan`). The other seven were excluded. Once care-worker courses joined an existing item, 2026 counts 147 measures instead of 148; the catch rates don't change.

## Answer keys and their limits

| Key | File | How it was made |
|---|---|---|
| 2024 | `reports/benchmark/sample-2024.tsv` | 315 pieces drawn with `benchmark.js ub24.md --draw 150 --seed 2024` (every cold-start flagged piece plus 150 random unflagged ones), labelled blind. |
| 2025 | `skills/belanjawan-brain/references/ledger-2025.tsv` | All 1,210 pieces labelled blind: each piece seen with its id and text only, never its score or flag. There is no 2025 brain, so `item:<slug>` names a measure. |
| 2026 | `skills/belanjawan-brain/references/ledger-2026.tsv` | The existing ledger. The 838 former `bulk` rows were re-read blind. |

- **One reader.** All labels were made by one reader in one pass. On a second blind read of 20 random 2025 pieces, the person-level call agreed on **19 of 20**, and the exact exclusion reason on 15 of 20. The disagreement was 2025 P58, a conditional remark about cutting education subsidies for the top 15%.
- **2026's flagged pieces weren't labelled blind.** They were decided in the earlier pass, when the flags were visible. That can affect the share of flagged pieces that are person-level. It doesn't affect the catch rate, which depends on the unflagged pieces, and those are now all blind.
- **Tuning direction.** The scorer's weights were tuned on 2026. For 2024 and 2025 that means tuning on a later year, and those two numbers are still the fairest of the three.
- **Two 2025 labels were aligned after the first run.** The Lampiran I restatements of Rakan Muda (L1.47.2) and Program Belia Kreatif (L1.56.5) now match their speech pieces. Both changes added misses; neither removed any.
- **Where "person-level" stops is a judgement.** Micro-loans, training programmes and housing schemes count. Employer incentives and grants to schools or NGOs don't. The conventions are written in the header of `ledger-2025.tsv`, and a different line would move the numbers by a few points.

## How to reproduce

```bash
cd skills/belanjawan-brain
node scripts/coverage.js ub25.md references/ledger-2025.tsv --final
node scripts/benchmark.js ub24.md ../../reports/benchmark/sample-2024.tsv
node scripts/benchmark.js ub25.md references/ledger-2025.tsv --learn-from ub24.md
node scripts/benchmark.js ub26.md references/ledger-2026.tsv --learn-from ub24.md ub25.md
```

**Correction, 27 Sep 2026:** checking the annotated speech (`reports/annotated/`) showed that Lampiran I Bil. 32 (butiran 11), "Meneruskan inisiatif mySalam pada tahun 2026", had been excluded as governance in the first ledger pass. It is now `item:mysalam`. The 2026 figures above include this fix. The unit was already flagged, so the catch rate went up slightly: 218 of 261 pieces, against 217 of 260 before.
