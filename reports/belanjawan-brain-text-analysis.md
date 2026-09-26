# Text-only analysis: Ucapan Belanjawan 2024, 2025, 2026

Sources: the three speech texts supplied by the user (Markdown). No web lookups were made. The method and scripts are described in `skills/belanjawan-brain/references/text-signals.md`.

## What the texts contain

| Speech | Paragraphs | Lampiran I entries | Lampiran II entries | Units | Flagged |
|---|---|---|---|---|---|
| 2024 | 293 | — (speech only) | — | 463 | 171 |
| 2025 | 300 | 59 | 29 | 1,210 | 418 |
| 2026 | 251 | 40 | 40 | 1,279 | 432 |

All paragraph and Lampiran I numbering was complete, with no gaps.

## How well the text signals find person-level measures

The signals were tuned on the 2026 brain. Each of its items was matched to the unit it came from, giving 90 source units.

- The scorer flags about a third of units.
- 85 of the 90 source units are flagged. Two of the five unflagged are matching errors; the other three are announcements that name neither an amount nor a group.
- On 2025 and 2024, which were not used for tuning, units naming known programmes or the always-ask cases (tobacco, alcohol, Langkawi, Labuan) are mostly flagged. The unflagged ones are allocation totals, infrastructure and rhetoric.

The score only orders the reading. Completeness comes from the ledger: `references/ledger-2026.tsv` has a decision for all 1,279 units, and `coverage.js` fails if one is missing, bulk-excluded while flagged, or left open at hand-over.

## Measures in the 2026 text that the brain doesn't have (`gap`)

| Source | Measure |
|---|---|
| Perenggan 27 | **The Langkawi and Labuan vehicle tax exemption is limited to vehicles worth up to RM300,000 from 1 Jan 2026.** This is an area-based tax measure, the kind the user reported as skipped. |
| Perenggan 170; Lampiran I Bil. 30 | PERKESO's maximum haemodialysis payment rises from RM150 to RM170 per treatment |
| Perenggan 238; Lampiran I Bil. 40 | Living allowance for 4,000 KEMAS contract pensioners rises from RM300 to RM500 a month |
| Perenggan 104; Lampiran I Bil. 19 | Solar ATAP: households can install rooftop solar and offset their bill |
| Perenggan 182 | The ETAP on-call allowance for medical, specialist and dental officers rises about 40%; 4,500 contract doctors, 833 nurses and 935 KKM graduates are offered permanent posts |
| Lampiran I Bil. 32 | RESET: a basic medical insurance/takaful product |
| Lampiran I Bil. 40 *(not in the speech)* | Pensioners' special appreciation payment extended Jan–Dec; APEL.Q INTAN pays 50% of study costs (up to RM15,000) for civil servants with over 15 years' service; BIPK/BIPAC special-forces incentive rise |
| Lampiran I Bil. 11 *(not in the speech)* | LiKES industrial training for young talent extended to 12 months |

Four of these appear only in Lampiran I. A read of the speech alone would miss them.

## Borderline, for the user to decide (`ask`)

- **Non-citizens:** stamp duty on homes bought by non-citizens rises from 4% to 8% (Perenggan 218, Lampiran II — Lampiran 14).
- **Donor tax deductions:** individual donors to anti-corruption programmes (Perenggan 28), hospital endowment funds (Perenggan 205), the Muzium trust (Perenggan 82) and community projects (Lampiran I Bil. 34).
- **Area-limited:** Sabah and Labuan electricity subsidy (Perenggan 46), Tamu Desa stalls for small traders in Sabah and Sarawak (Perenggan 46).
- **Help through a small business:** BSN business grant up to RM10,000 (Perenggan 156), iTEKAD matching grant (Perenggan 67), SJPP guarantees for micro-entrepreneurs (Perenggan 98), KWAP microfinance for pensioners (Perenggan 138), incentives for livestock breeders and fruit growers.
- **Rule changes:** the youth age limit becomes 15–30 from January 2026, which changes eligibility for youth programmes (Perenggan 143); Lemon Law consumer protection (Perenggan 39); electricity tariff restructuring, under which 85% of users see no increase (Perenggan 40).
- **Other:** Kota MADANI homes, 80% of them for civil servants (Perenggan 214); strata titles for low-cost homes (Lampiran I Bil. 35); a study of transferring KWSP savings between generations (Lampiran I Bil. 30); monthly allowances for imams and KAFA teachers (Lampiran I Bil. 36); tahfiz skills training (Perenggan 65, 223).

## Programmes across the three years

- **In all three speeches (22):** STR, SARA, i-Suri, mySalam, i-Saraan, SKSPS, KAFA, PTPTN, SSPA, SJKP, RON95, TUBE, the paddy price subsidy (Skim Subsidi Harga Padi), the fishermen's catch incentive (Insentif Hasil Tangkapan Nelayan), and others.
- **In 2024 or 2025 but not in the 2026 text:** Inisiatif Pendapatan Rakyat (IPR), Program Latihan MADANI, Skim Ex-Gratia Bencana Kerja, the electric motorcycle incentive (Skim Galakan Penggunaan Motosikal Elektrik), Program Tahfiz TVET, Bantuan Kanak-kanak Keluarga Miskin, Skim Perlindungan Tenang, Skim Persaraan Swasta, and 15 others. The text doesn't say whether these continue. They are questions for the user, not items to drop or keep by assumption. The full list comes from `node scripts/learn-programmes.js`.

## What the skill learned from the texts

- **Read Lampiran I as a source.** It holds measures the speech never mentions.
- **Treat each bullet as its own unit.** One paragraph can hold five measures under a lead-in that names none of them (Perenggan 184).
- **Look for area-based tax measures in the governance sections.** The Langkawi cap sits among anti-leakage measures.
- **Criteria often live in earlier years' texts.** i-Suri's matching rule is in the 2025 Lampiran I. Some are in no speech at all: PeKa B40's age and STR rule and BUDI95's quota. Those become `semak` items plus a question for the user, never a web lookup.
- **Watch for name collisions.** "PEKA" in the speeches is a prison programme (Peluang Kedua Anda), not PeKa B40.
