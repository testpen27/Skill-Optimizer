# Belanjawan 2026 — Citizen Benefits Q&A: Logic Spec (v2026.7)

**Engine:** `belanjawan2026-brain.js` (UI-free, no dependencies, works in browser and Node)
**Verification:** `test.js` (round 1) and `verify2.js` (round 2). Both pass; see §8.
**Source:** Ucapan Belanjawan 2026 (MOF). "Perenggan / ms" refer to that document. Items added in v2026.4 and v2026.5 come from the speech text only and cite paragraph and Lampiran numbers (no page numbers). Items from earlier versions that were checked on the web keep their `web` field.
**Data as of:** 2 Oct 2026

## What changed in v2026.7

The user's eight mandatory questions (2 Oct 2026). They are always asked and, like every question except age and region, can be skipped. The cards and amounts didn't change; only how some facts are found out did.

| Question (as shown) | id | Asked of | Before |
|---|---|---|---|
| Apakah jantina anda? | `gender` | adults | unchanged |
| Pekerjaan anda? | `employment` | adults | reworded |
| Adakah anda mempunyai anak berusia 17 tahun ke bawah? | `has_minor_children` | adults | new; "Ya" then asks the number and stages of children |
| Adakah anda Orang Kurang Upaya (OKU)? | `oku` | everyone | was the option "OKU" in `status` |
| Adakah lesen memandu anda aktif? | `license` | everyone | was the option "Ada lesen memandu" in `assets` |
| Adakah anda penerima STR atau SARA? | `str_status` | adults | reworded |
| Adakah anda peminjam PTPTN? | `ptptn` | adults | was the option "Mempunyai pinjaman PTPTN" in `assets` |
| Adakah anda pencarum KWSP? | `kwsp` | adults | new; was guessed from the job |

- **Children.** "Tidak" counts as no children: the number and stages questions are skipped and STR uses the 0-children rate. A skip makes the STR amount a range, as a skipped number of children did before. The number question no longer has a "0" option. Parents of students at a university, polytechnic or college now tick "Anak saya belajar di institusi pengajian tinggi" in `status` (it was a stage in `child_stages`).
- **STR or SARA recipient.** A "Ya" counts as receiving STR for the cards meant for STR recipients (PeKa B40, mySalam, Skim Perubatan MADANI), even when the estimate says the household isn't eligible. The STR + SARA panel still shows the estimate.
- **KWSP.** The reader's answer is used; only when it is skipped does the brain fall back to the guess from the job.
- **OKU, licence and PTPTN.** "Ya" counts, "Tidak" doesn't, and a skip shows the related cards as `mungkin`.

## What changed in v2026.6

The user's results-screen decisions (2 Oct 2026). The data and rules didn't change.

- **No "kesan" tier.** The label "Perubahan yang menjejaskan anda" is gone. Cost changes (`kind: 'kesan'`: tobacco, vape, alcohol, clinic fees and similar) are tiered like any other card (`layak`, `semak` or `mungkin`) and shown as they are, with no warning.
- **Results in two groups, no themes.** `evaluate()` now also returns `groups`: "Berkemungkinan layak" (`layak` cards), then "Mungkin layak" (`semak` cards, then `mungkin` cards). The STR + SARA card isn't in the groups; it stays as the main panel on top. `byTheme` is still returned but the results screen doesn't use it.
- **Output controls** (`references/output-controls.md`): cards show the title only, in a five-wide grid; hovering (or tapping, on touch screens) shows the amount, description, timing note and "Kenapa anda layak" (plus "Perlu disahkan" for `mungkin` cards). Who is eligible, what to do next, the source and the tier aren't shown.

## What changed in v2026.5

A blind re-read of the 838 speech units that had been set aside unread (done for the benchmark in `reports/belanjawan-brain-benchmark.md`) found 10 more person-level measures. The user decided them on 27 Sep 2026 (see §9). This version adds **2 items** and extends one, taking the brain from 113 to 115:

- **New `pinjaman_mikro`:** BSN and TEKUN micro loans for micro-entrepreneurs and small traders (`semak`, self-employed).
- **New `ptptn_sekatan_perjalanan`:** travel ban on PTPTN borrowers who can pay but default (`kesan`). It is shown only to adults who tick the new option "Mempunyai pinjaman PTPTN" in the existing `assets` question. No new question was added.
- **Extended `latihan_tvet`:** now also names KPWKM's TVET courses for care workers.

**Hand-over format (1 Oct 2026):** the skill's deliverable is now one Markdown build spec, `BRAIN-2026.md`, generated from the engine by `scripts/export-brain-md.js`. Claude Code or another skill (such as `tv3-interactive-embed`) builds the checker from it. The engine and its tests stay inside the skill, and `test.js` fails if the spec is out of date. `references/sample-output.json` was removed.

## What changed in v2026.4

A text-only read of the whole speech (1,279 units, every one given a ledger decision in `ledger-2026.tsv`) found measures the brain lacked. The user decided each one in three question rounds on 26 Sep 2026 (see §9). This version adds **19 items**, taking the brain from 94 to 113:

- **Costs:** the Langkawi and Labuan vehicle tax exemption is capped at vehicles worth up to RM300,000 (`kesan`, Labuan residents with a driving licence).
- **Health and protection:** PERKESO haemodialysis payment up to RM170; iTEKAD matching grant.
- **Civil service and pensioners:** pensioners' special appreciation payment extended; KEMAS contract pensioners' allowance RM500 a month; APEL.Q INTAN; ETAP rise; permanent posts for contract doctors, nurses and KKM graduates; BIPK/BIPAC; Kota MADANI homes.
- **Households:** Solar ATAP.
- **Small business:** BSN business grant up to RM10,000; KWAP microfinance for pensioners; Tamu Desa stalls in Sabah and Sarawak.
- **Farming and religious community:** fruit-grower incentives; livestock-breeder incentives; imam/KAFA/takmir monthly allowance; skills and AI training for tahfiz and pondok students.
- **Tax:** one combined item for donation deductions (anti-corruption programmes, hospital endowment funds, the Muzium trust account, community projects).

## What changed in v2026.3

1. **Bahasa Melayu corrected throughout.** Every question, option, result and advisory was re-read in full, and 16 wording fixes plus the fixes below were made. Examples:
   - "Makan gaji" → "Pekerja sektor swasta".
   - "freelance" → "pekerja bebas".
   - "siak" → "tok siak", as in the speech.
   - "masalah pembelajaran" → "kurang upaya pembelajaran", the official term.
   - "dari RM…" → "daripada RM…".
   - Verbless fragments ("Automatik untuk…") rewritten as full sentences.
   - All fixes are now enforced by a lint, so they can't return.
2. **Less personal questioning.**
   - The grade and appointment-type question is removed. Civil-servant items now say who qualifies in the text and are shown as "Semak kelayakan".
   - The fertility question is removed.
   - Only age and region are compulsory. Every other question has **"Tidak mahu menyatakan"**, and results that depend on a skipped answer show as "Mungkin layak" rather than disappearing silently.
3. **New theme — Kes Khas: Gaya Hidup, Pelaburan & Perubahan Harga.** This covers the cigarette, cigar, heated-tobacco and alcohol duty rises; the review of a possible e-cigarette ban; cheaper quit-smoking aids (NRT); the private clinic fee change (RM10–RM80); stamp-duty relief for retail investors and low-salary employment contracts; and the new 2% LLP tax. These are marked `kind: 'kesan'` when they cost the person more.
4. **People-facing values only.** All government allocation totals and beneficiary counts ("RM3.1 bilion", "560,000 penerima", "5.2 juta murid") are removed. Each item now states what the person gets or pays, and a lint enforces this.
5. **New items found:**
   - KWSP Haji withdrawal limit raised to RM10,000.
   - GCR Haji redemption for civil servants.
   - Nur@PETRA appliance rebate.
   - Smallholder replanting and rubber incentives.
   - Free Tuisyen MADANI.
   - Wildlife-damage compensation.

---

## 1. How the brain works

```
answers ──► deriveFacts() ──► facts ──┬──► calcStrSara()   ──► STR + SARA estimate (or range)
                                      └──► BENEFITS[].when  ──► tri-state test ──► tiered results
```

- **Branching:** `getVisibleQuestions(answers)` returns the questions to show now. `pruneAnswers()` removes answers to questions that became hidden, repeating until nothing more changes.
- **Facts:** answers are turned into facts such as `b40`, `strEligible`, `isSchoolPupil`, `ipt`, `kwspMember` and `smoker`. Rules test facts, not raw answers.
- **Rules:** written as declarative JSON (`{ f:'age', gte:40, why:'…' }` with `all` / `any` / `not`). Each `why` label becomes the plain-language explanation shown to the user.

**Tiers**

| Tier | Label shown | When |
|---|---|---|
| `layak` | Berkemungkinan layak | Rule true and it is the real criterion |
| `semak` | Semak kelayakan | Rule true, but the programme is means-tested, quota-based or depends on something we deliberately don't ask (e.g. grade) |
| `mungkin` | Mungkin layak | Rule depends on a skipped answer or "Tidak pasti"; `needsConfirm[]` lists what's missing |

Cost changes (`kind: 'kesan'`) follow the same three tiers since v2026.6; there is no separate tier or warning label.

**How skipping works**

- **Single-choice skip:** the answer becomes an unknown fact, so dependent items show as `mungkin`.
- **Multi-choice skip:** treated as "none selected". An advisory tells the user that some items may be hidden.
- **Unasked questions** (e.g. employment for a minor) count as false, so they never produce `mungkin`.

---

## 2. Theme taxonomy (13 themes, 115 items)

| Theme | What citizens get or pay | Items |
|---|---|---|
| `cash` Bantuan Tunai & Kos Sara Hidup | STR, SARA, one-off payments, JKM aid, Jualan RAHMAH, Sabah/Sarawak price parity | 10 |
| `subsidy` Subsidi Bahan Api & Tenaga | BUDI95, e-hailing quota, diesel RM200, fishermen's diesel, appliance rebate, Solar ATAP | 6 |
| `health` Kesihatan & Insurans | PeKa B40, mySalam, Skim Perubatan MADANI, Tdap, screening, MHIT, small-policy stamp duty, PERKESO dialysis | 8 |
| `education` Pendidikan | BAP RM150, Bantuan Am, RMT, Tuisyen MADANI, Elaun MBK, autism support, PTPTN, GAPAI, campus aid, tahfiz/pondok skills training | 13 |
| `housing` Perumahan | Stamp duty, SJKP ×2, Step-Up, contract-staff loans, LPPSA, affordable homes, home repair, Kota MADANI | 9 |
| `protection` Perlindungan Sosial & Simpanan Persaraan | i-Saraan, i-Saraan Plus, i-Suri, Lindung Kendiri, PERKESO, KWSP auto-account, Haji withdrawals | 8 |
| `family` Keluarga & Wanita | KasihnITA, women's financing, taska subsidy, BuAI | 4 |
| `youth` Belia, Latihan & Pekerjaan | MyLesen B2, PLKN, K-Youth, TVET (incl. care-worker courses), youth financing, Rakan Muda | 6 |
| `vulnerable` OKU, Warga Emas & Golongan Rentan | OKU aid, elderly welfare, KWAP homes, Second Chance, Orang Asli, iTEKAD | 6 |
| `sector` Mengikut Pekerjaan | Fishermen, padi, smallholders, agro, wildlife damage, civil servants, veterans, taxis, driver screening, pensioners' appreciation payment, KEMAS contract pensioners, APEL.Q, ETAP, KKM permanent posts, BIPK/BIPAC, BSN grant, BSN/TEKUN micro loans, KWAP microfinance, Tamu Desa, fruit growers, livestock breeders, imam/KAFA allowance | 22 |
| `mobility` Pengangkutan & Mobiliti | MyRailLife, OKU vans, old-car grant, RAS | 4 |
| `tax` Pelepasan Cukai Individu | Six new or expanded reliefs for YA2026; donation deductions | 7 |
| `special` Kes Khas | Tobacco, cigar, heated tobacco, vape, NRT, alcohol, clinic fees, employment-contract duty, ETF/warrants, LLP tax, Langkawi/Labuan vehicle exemption cap, PTPTN travel ban | 12 |

---

## 3. STR + SARA calculator

Category is decided in this order:

1. **Isi rumah:** married, OR single parent, OR has children.
2. **Warga emas tiada pasangan:** otherwise, age ≥ 60.
3. **Bujang:** otherwise, age 21–59.
4. **Not eligible:** otherwise.

| Category | Income | Children | STR/yr | SARA/yr | Total | + eKasih top-up (SARA) |
|---|---|---|---|---|---|---|
| Isi rumah | ≤ RM2,500 | 0 / 1–2 / 3–4 / 5+ | 700 / 1,200 / 1,700 / 2,200 | 1,200 | 1,900 / 2,400 / 2,900 / 3,400 | +1,200 (RM100 → RM200/month) |
| Isi rumah | RM2,501–5,000 | 0 / 1–2 / 3–4 / 5+ | 200 / 450 / 700 / 950 | 1,200 | 1,400 / 1,650 / 1,900 / 2,150 | +1,200 |
| Warga emas tiada pasangan (60+) | < RM5,000 | — | 600 | 600 | 1,200 | +1,200 (RM50 → RM150/month) |
| Bujang (21–59) | ≤ RM2,500 | — | 0 | 600 | 600 | +600 (RM50 → RM100/month) |

How skipped or uncertain answers change the output:

- **"Adakah anda mempunyai anak berusia 17 tahun ke bawah?" answered "Tidak":** counts as 0 children.
- **That question, or the number of children, skipped (married or single parent):** returns `totalRange`, e.g. RM1,900–3,400.
- **"Adakah anda penerima STR atau SARA?" answered "Ya":** the panel still shows the estimate, but the STR-linked items count the person as a recipient.
- **eKasih "Tidak pasti":** returns `totalIfEkasih`.
- **Marital status or income skipped:** returns `eligible: null`, and STR-linked items (mySalam, PeKa B40, Skim Perubatan MADANI) show as `mungkin`.

---

## 4. Timing flags

These are still returned, with a `timing` note, so the UI can label or grey them out:

- **Already paid:** Penghargaan SARA (mid-Feb 2026) and Bantuan Khas Kewangan for civil servants and pensioners (early Mar 2026).
- **BUDI95:** the quota is 200L a month from 1 Apr 2026.
- **MyLesen B2:** the 2026 intake was targeted to finish by July 2026.
- **LPPSA:** Skim Perumahan Muda ends 31 Dec 2026.

⚠️ **Budget 2027 is due in October 2026.** Keep this file as the 2026 dataset (`VERSION`, `DATA_AS_OF`).

---
## Questions (20)

| # | id | Type | Question | Shown when | Options (value → label) |
|---|---|---|---|---|---|
| 1 | `age` | number | Berapakah umur anda? | always | number 0–120 |
| 2 | `region` | single | Di manakah anda menetap? | always | `semenanjung` Semenanjung Malaysia<br>`sabah` Sabah<br>`sarawak` Sarawak<br>`labuan` Wilayah Persekutuan Labuan |
| 3 | `self_school` | single | Adakah anda murid sekolah Kerajaan? | `age < 18` | `yes` Ya<br>`no` Tidak<br>`skip` Tidak mahu menyatakan *(exclusive)* |
| 4 | `gender` | single | Apakah jantina anda? | `age ≥ 18` | `female` Perempuan<br>`male` Lelaki<br>`skip` Tidak mahu menyatakan *(exclusive)* |
| 5 | `employment` | single | Pekerjaan anda? | `age ≥ 18` | `employed_private` Pekerja sektor swasta<br>`civil_servant` Penjawat awam<br>`gig_ehailing` Pemandu e-hailing atau penghantar p-hailing<br>`self_employed` Bekerja sendiri, pekerja bebas atau peniaga kecil<br>`fisher` Nelayan<br>`farmer` Pesawah, petani, penternak atau pekebun kecil<br>`housewife` Suri rumah sepenuh masa<br>`student_ipt` Pelajar institusi pengajian tinggi<br>`jobseeker` Graduan baharu atau sedang mencari pekerjaan<br>`retired_gov` Pesara Kerajaan (berpencen)<br>`retired_other` Bersara atau tidak bekerja<br>`skip` Tidak mahu menyatakan *(exclusive)* |
| 6 | `farm_type` | single | Apakah jenis kegiatan pertanian utama anda? | `employment = farmer` | `padi` Menanam padi<br>`smallholder` Pekebun kecil getah atau sawit<br>`other` Tanaman lain, ternakan atau akuakultur<br>`skip` Tidak mahu menyatakan *(exclusive)* |
| 7 | `marital` | single | Apakah status perkahwinan anda? | `age ≥ 18` | `married` Berkahwin<br>`single_parent` Ibu atau bapa tunggal yang mempunyai anak tanggungan<br>`single` Tiada pasangan (belum berkahwin, bercerai atau kematian pasangan)<br>`skip` Tidak mahu menyatakan *(exclusive)* |
| 8 | `has_minor_children` | single | Adakah anda mempunyai anak berusia 17 tahun ke bawah? | `age ≥ 18` | `yes` Ya<br>`no` Tidak<br>`skip` Tidak mahu menyatakan *(exclusive)* |
| 9 | `children` | single | Berapakah bilangan anak anda yang berusia 17 tahun ke bawah? | `minorChildren = true` | `1-2` 1 hingga 2 orang<br>`3-4` 3 hingga 4 orang<br>`5+` 5 orang atau lebih<br>`skip` Tidak mahu menyatakan *(exclusive)* |
| 10 | `child_stages` | multi | Di peringkat manakah anak anda sekarang? (pilih semua yang berkaitan) | `minorChildren = true` | `under6` Belum bersekolah atau prasekolah (bawah 6 tahun)<br>`primary` Sekolah rendah Kerajaan<br>`secondary` Sekolah menengah Kerajaan<br>`other` Lain-lain (contohnya sekolah swasta)<br>`skip` Tidak mahu menyatakan *(exclusive)* |
| 11 | `oku` | single | Adakah anda Orang Kurang Upaya (OKU)? | always | `yes` Ya<br>`no` Tidak<br>`skip` Tidak mahu menyatakan *(exclusive)* |
| 12 | `license` | single | Adakah lesen memandu anda aktif? | always | `yes` Ya<br>`no` Tidak, atau tiada lesen memandu<br>`skip` Tidak mahu menyatakan *(exclusive)* |
| 13 | `income` | single | Berapakah anggaran pendapatan kasar bulanan isi rumah anda? | `age ≥ 18` | `lt2500` RM2,500 dan ke bawah<br>`2501_5000` RM2,501 hingga RM5,000<br>`5001_6000` RM5,001 hingga RM6,000<br>`6001_12000` RM6,001 hingga RM12,000<br>`gt12000` Melebihi RM12,000<br>`skip` Tidak mahu menyatakan *(exclusive)* |
| 14 | `ekasih` | single | Adakah isi rumah anda berdaftar sebagai Miskin atau Miskin Tegar dalam sistem eKasih? | `age ≥ 18 AND (incomeMax ≤ 5000 OR incomeSkipped = true)` | `yes` Ya<br>`no` Tidak<br>`unsure` Tidak pasti<br>`skip` Tidak mahu menyatakan *(exclusive)* |
| 15 | `str_status` | single | Adakah anda penerima STR atau SARA? | `age ≥ 18` | `yes` Ya<br>`no` Tidak<br>`unsure` Tidak pasti<br>`skip` Tidak mahu menyatakan *(exclusive)* |
| 16 | `ptptn` | single | Adakah anda peminjam PTPTN? | `age ≥ 18` | `yes` Ya<br>`no` Tidak<br>`skip` Tidak mahu menyatakan *(exclusive)* |
| 17 | `kwsp` | single | Adakah anda pencarum KWSP? | `age ≥ 18` | `yes` Ya<br>`no` Tidak<br>`skip` Tidak mahu menyatakan *(exclusive)* |
| 18 | `assets` | multi | Perkara manakah yang berkaitan dengan anda? (pilih semua yang berkaitan) | always | `diesel_vehicle` Memiliki kenderaan persendirian berenjin diesel<br>`old_car` Memiliki kereta berusia lebih 20 tahun<br>`first_home` Merancang untuk membeli rumah pertama<br>`taxpayer` Membayar cukai pendapatan atau mengisi e-Filing<br>`invest_bursa` Melabur di Bursa Malaysia (saham, ETF atau waran)<br>`llp_partner` Pekongsi dalam Perkongsian Liabiliti Terhad (PLT)<br>`haji_plan` Merancang untuk menunaikan haji<br>`none` Tiada yang berkaitan *(exclusive)*<br>`skip` Tidak mahu menyatakan *(exclusive)* |
| 19 | `status` | multi | Adakah mana-mana keadaan ini berkaitan dengan anda? (pilih semua yang berkaitan) | always | `oku_child` Anak saya OKU atau kurang upaya pembelajaran (seperti autisme atau ADHD)<br>`child_ipt` Anak saya belajar di institusi pengajian tinggi (universiti, politeknik atau kolej)<br>`pregnant` Saya atau pasangan sedang hamil<br>`veteran` Veteran Angkatan Tentera Malaysia<br>`pjm` Penerima Pingat Jasa Malaysia<br>`religious_staff` Guru KAFA, guru takmir, imam, bilal, tok siak, noja atau marbut<br>`taxi` Pemandu atau pemilik teksi, termasuk kereta sewa<br>`orang_asli` Orang Asli<br>`bankrupt` Sedang berstatus bankrap<br>`none` Tiada yang berkaitan *(exclusive)*<br>`skip` Tidak mahu menyatakan *(exclusive)* |
| 20 | `lifestyle` | multi | Soalan pilihan: adakah mana-mana perkara ini berkaitan dengan anda? | `age ≥ 18` | `cigarette` Merokok<br>`cigar` Menghisap cerut atau cerut kecil (cigarillo)<br>`heated_tobacco` Menggunakan produk tembakau yang dipanaskan (heated tobacco)<br>`vape` Menggunakan vape atau rokok elektronik<br>`alcohol` Mengambil minuman beralkohol<br>`none` Tiada yang berkaitan *(exclusive)*<br>`skip` Tidak mahu menyatakan *(exclusive)* |

## Rule matrix (115 items)

### Bantuan Tunai & Kos Sara Hidup (`cash`, 10)

| id | Item | Kind | What the person gets / pays | Rule (`when`) | Certainty | Source | Timing |
|---|---|---|---|---|---|---|---|
| `str_sara` | Sumbangan Tunai Rahmah (STR) dan Sumbangan Asas Rahmah (SARA) | manfaat | Dianggarkan berdasarkan jawapan anda | `strEligible = true` | high | Perenggan 158–161, ms 92–94; Lampiran I Bil. 29, ms 258–259 · [web](https://www.bharian.com.my/amp/berita/nasional/2026/03/1515524/bhplus) | — |
| `penghargaan_sara` | Penghargaan SARA | manfaat | RM100 (sekali sahaja) | `age ≥ 18` | high | Perenggan 160, ms 93 | Telah disalurkan pada pertengahan Februari 2026. |
| `bkk_penjawat` | Bantuan Khas Kewangan penjawat awam | manfaat | RM500 (sekali sahaja) | `employment = civil_servant` | check | Perenggan 246, ms 127 | Telah disalurkan pada awal Mac 2026 sempena Aidilfitri. |
| `bkk_pesara` | Bantuan Khas Kewangan pesara dan veteran | manfaat | RM250 (sekali sahaja) | `employment = retired_gov OR status includes veteran` | high | Perenggan 246, ms 127 | Telah disalurkan pada awal Mac 2026. |
| `pjm` | Bayaran khas penerima Pingat Jasa Malaysia | manfaat | RM500 | `status includes pjm` | high | Perenggan 239, ms 125 | — |
| `sumbangan_agama` | Sumbangan khas guru KAFA dan petugas masjid | manfaat | RM500 | `status includes religious_staff` | high | Perenggan 247, ms 127 | — |
| `jkm_bantuan` | Bantuan bulanan Jabatan Kebajikan Masyarakat (JKM) | manfaat | Bantuan bulanan mengikut kategori | `b40 = true AND (ekasih = true OR age ≥ 60 OR oku = true OR status includes oku_child OR marital = single_parent)` | check | Perenggan 162, ms 94; Lampiran I Bil. 29, ms 260 | — |
| `rebat_elektrik` | Rebat bil elektrik | manfaat | Sehingga RM40 sebulan | `ekasih = true` | check | Lampiran I Bil. 29, ms 261 | — |
| `payung_rahmah` | Jualan RAHMAH MADANI | manfaat | Barangan keperluan asas pada harga lebih rendah | `age ≥ 18` | high | Perenggan 163, ms 94; Lampiran I Bil. 29, ms 261 | — |
| `harga_sabah_sarawak` | Harga barangan asas setara Semenanjung | manfaat | Harga barangan asas sama seperti di Semenanjung | `eastMalaysia = true` | high | Perenggan 164, ms 95; Lampiran I Bil. 29, ms 261 | — |

### Subsidi Bahan Api & Tenaga (`subsidy`, 6)

| id | Item | Kind | What the person gets / pays | Rule (`when`) | Certainty | Source | Timing |
|---|---|---|---|---|---|---|---|
| `budi95` | BUDI95: petrol RON95 bersubsidi | manfaat | RM1.99 seliter | `age ≥ 16 AND license = true` | high | Perenggan 40, ms 26–27 · [web](https://says.com/my/seismik/budi95-kerajaan-umum-turunkan-kuota-ron95-ke-200-liter-sebulan-bermula-1-april-ini) | Kuota 200 liter sebulan berkuat kuasa 1 April 2026. Semak kuota terkini. |
| `budi95_ehailing` | Kuota tambahan BUDI95 untuk pemandu e-hailing | manfaat | Sehingga 800 liter sebulan | `employment = gig_ehailing AND license = true` | check | Perenggan 40, ms 27 · [web](https://says.com/my/berita/pemandu-e-hailing-bawah-2000km-sebulan-tidak-layak-terima-kuota-tambahan-budi95) | — |
| `diesel_rm200` | Bantuan diesel bersasar (BUDI MADANI) | manfaat | RM200 sebulan | `region = semenanjung AND (assets includes diesel_vehicle OR employment = farmer)` | check | Perenggan 40, ms 26 | — |
| `diesel_nelayan` | Diesel bersubsidi untuk nelayan | manfaat | RM1.65 seliter | `employment = fisher` | high | Perenggan 111, ms 73 | — |
| `rebat_cekap_tenaga` | Rebat pembelian peralatan cekap tenaga (Nur@PETRA) | manfaat | Rebat untuk peralatan elektrik cekap tenaga | `age ≥ 18` | check | Lampiran I, ms 222 | — |
| `solar_atap` | Solar ATAP: jana elektrik sendiri di rumah | manfaat | Lebihan tenaga boleh dijual sebagai pengimbangan (offset) bil elektrik | `age ≥ 18` | check | Perenggan 104; Lampiran I Bil. 19 | — |

### Kesihatan & Insurans (`health`, 8)

| id | Item | Kind | What the person gets / pays | Rule (`when`) | Certainty | Source | Timing |
|---|---|---|---|---|---|---|---|
| `peka_b40` | PeKa B40 | manfaat | Saringan kesihatan percuma dan bantuan alat perubatan sehingga RM20,000 | `age ≥ 40 AND (strRecipient = true OR strEligible = true)` | high | Lampiran I Bil. 32, ms 273 · [web](https://www.malaysia.gov.my/my/topics/peka-b40) | — |
| `mysalam` | mySalam | manfaat | RM8,000 jika disahkan menghidap penyakit kritikal, serta RM50 sehari ketika dimasukkan ke wad | `age ≥ 18 AND (strRecipient = true OR strEligible = true)` | high | Perenggan 181, ms 100–101; Lampiran I Bil. 32, ms 269 · [web](https://bernama.com/bm/news.php?id=2574921) | — |
| `skim_perubatan_madani` | Skim Perubatan MADANI | manfaat | Rawatan di klinik swasta panel: RM250 setahun (keluarga), RM125 (warga emas), RM75 (bujang) | `strRecipient = true OR strEligible = true` | high | Lampiran I Bil. 32, ms 272 · [web](https://ringgitplus.com/ms/blog/sudut-pakar/str-cara-dapatkan-perlindungan-perubatan-percuma-jika-pendapatan-isi-rumah-anda-di-bawah-rm5000.html) | — |
| `tdap_ibu` | Vaksin Tdap percuma untuk ibu hamil | manfaat | Suntikan vaksin percuma | `status includes pregnant` | high | Lampiran I Bil. 26, ms 250 | — |
| `saringan_wanita` | Ujian mamogram dan saringan kanser serviks bersubsidi | manfaat | Ujian saringan pada kos lebih rendah | `gender = female AND age ≥ 20` | check | Lampiran I Bil. 26, ms 247 | — |
| `mhit_kwsp` | Akaun Sejahtera KWSP boleh digunakan untuk insurans perubatan asas | manfaat | Bayar premium menggunakan simpanan KWSP | `kwspMember = true` | high | Perenggan 181, ms 100; Lampiran I Bil. 32, ms 269 | — |
| `duti_insurans_kecil` | Tiada duti setem untuk polisi insurans bernilai kecil | manfaat | Dikecualikan duti setem sehingga 2028 | `age ≥ 18` | high | Perenggan 181, ms 100; Lampiran II — Lampiran 16 dan 17, ms 332–333 | — |
| `perkeso_dialisis` | Kadar bayaran rawatan hemodialisis PERKESO dinaikkan | manfaat | Sehingga RM170 bagi setiap rawatan (sebelum ini RM150) | `employment ∈ [employed_private, gig_ehailing, self_employed]` | check | Perenggan 170; Lampiran I Bil. 30 | — |

### Pendidikan (`education`, 13)

| id | Item | Kind | What the person gets / pays | Rule (`when`) | Certainty | Source | Timing |
|---|---|---|---|---|---|---|---|
| `bap` | Bantuan Awal Persekolahan | manfaat | RM150 bagi setiap murid | `isSchoolPupil = true` | high | Perenggan 192, ms 106 | — |
| `bantuan_am` | Bantuan Am Persekolahan | manfaat | Kini diberikan sehingga Tingkatan 5 | `isSchoolPupil = true AND (ekasih = true OR income = lt2500)` | check | Perenggan 192, ms 106 | — |
| `rmt_biasiswa` | Rancangan Makanan Tambahan dan Biasiswa Kecil Persekutuan | manfaat | Makanan berkhasiat percuma dan biasiswa | `isSchoolPupil = true AND b40 = true` | check | Perenggan 192, ms 105 | — |
| `tuisyen_madani` | Tuisyen MADANI percuma | manfaat | Kelas tuisyen percuma | `isSchoolPupil = true AND b40 = true` | check | Perenggan 43, ms 28; Lampiran I, ms 143 | — |
| `elaun_mbk` | Elaun Murid Berkeperluan Khas | manfaat | RM150 sebulan | `isSchoolPupil = true AND (status includes oku_child OR (oku = true AND age < 18))` | high | Perenggan 194, ms 107 | — |
| `autisme` | Sokongan untuk anak autisme | manfaat | Kelas khas dan bantuan yuran pembelajaran | `status includes oku_child` | check | Perenggan 149 dan 194, ms 87–88, 107; Lampiran I Bil. 29, ms 260 | — |
| `ptptn_percuma` | Pendidikan Percuma PTPTN | manfaat | Pengajian percuma di IPTA | `ipt = true AND ekasih = true` | check | Perenggan 202, ms 109; Lampiran I Bil. 33, ms 280 | — |
| `ptptn_kelas_pertama` | Pengecualian bayaran balik PTPTN untuk Kelas Pertama | manfaat | Tidak perlu membayar balik pinjaman | `ipt = true AND b40m40 = true` | check | Perenggan 202, ms 109 | — |
| `gapai` | Geran Padanan Ihsan (GAPAI) SSPN | manfaat | Geran sehingga RM5,000 | `ipt = true AND incomeMax ≤ 6000` | check | Lampiran I Bil. 33, ms 280 | — |
| `dapur_madani` | Ikhtiar Dapur MADANI | manfaat | Bantuan makanan dan peralatan memasak | `employment = student_ipt AND b40 = true` | high | Perenggan 200, ms 108 | — |
| `job_on_campus` | MySiswa Job on Campus | manfaat | Kerja sambilan di dalam kampus | `employment = student_ipt AND b40m40 = true` | check | Perenggan 200, ms 108 | — |
| `celik_madani` | Program Celik MADANI (PNB) | manfaat | Pelaburan permulaan RM50 dalam ASB atau ASM | `isSchoolPupil = true OR ipt = true` | check | Perenggan 199, ms 108 | — |
| `tahfiz_kemahiran` | Latihan kemahiran dan teknologi untuk pelajar tahfiz dan pondok | manfaat | Kursus teknologi digital dan AI serta latihan kemahiran profesional | `age ≥ 15 AND age ≤ 30 AND (employment = student_ipt OR (adult = false AND isSchoolPupil = true))` | check | Perenggan 65, 223; Lampiran I Bil. 11 | — |

### Perumahan (`housing`, 9)

| id | Item | Kind | What the person gets / pays | Rule (`when`) | Certainty | Source | Timing |
|---|---|---|---|---|---|---|---|
| `duti_rumah_pertama` | Tiada duti setem untuk rumah pertama | manfaat | Pengecualian penuh bagi rumah berharga sehingga RM500,000 | `assets includes first_home` | high | Perenggan 217, ms 116; Lampiran II — Lampiran 15, ms 331 | — |
| `sjkp_akses` | SJKP MADANI: Akses Pemilikan Rumah Mampu Milik | manfaat | Jaminan pinjaman sehingga 120%, had RM360,000 | `assets includes first_home AND b40m40 = true` | check | Perenggan 216, ms 115; Lampiran I Bil. 35, ms 293–294 | — |
| `sjkp_inklusif` | SJKP: Pembiayaan Rumah Inklusif | manfaat | Jaminan pinjaman sehingga 110%, had RM500,000 | `assets includes first_home AND (employment ∈ [gig_ehailing, self_employed, fisher, farmer] OR employment = civil_servant OR age ≤ 35)` | check | Lampiran I Bil. 35, ms 293–294 | — |
| `step_up` | Step-Up Financing | manfaat | Ansuran bulanan lebih rendah pada lima tahun pertama | `assets includes first_home AND age ≥ 21 AND age ≤ 35` | high | Lampiran I Bil. 26, ms 249; Bil. 35, ms 294 | — |
| `rumah_kontrak_awam` | Pinjaman rumah pertama untuk kakitangan kontrak Kerajaan | manfaat | Jaminan pinjaman sehingga 120% | `assets includes first_home AND employment = civil_servant` | check | Perenggan 237, ms 124 | — |
| `lppsa` | Pembiayaan perumahan LPPSA | manfaat | Had pembiayaan dinaikkan kepada RM1 juta | `employment = civil_servant` | check | Perenggan 237, ms 125 | Skim Pembiayaan Perumahan Muda tamat pada 31 Disember 2026. |
| `rumah_mampu_milik` | Rumah mampu milik Kerajaan (PRR, RMR, Residensi MADANI, PR1MA) | manfaat | Peluang memiliki rumah mampu milik | `assets includes first_home AND b40m40 = true` | check | Perenggan 216, ms 115; Lampiran I Bil. 35, ms 289 | — |
| `rumah_daif` | Baik pulih atau bina semula rumah daif | manfaat | Rumah dibaiki atau dibina semula | `ekasih = true OR (employment = fisher AND b40 = true)` | check | Perenggan 216, ms 115; Lampiran I Bil. 35, ms 290 | — |
| `kota_madani` | Rumah di Kota MADANI Presint 19 | manfaat | 80% daripada rumah dikhaskan untuk penjawat awam | `employment = civil_servant` | check | Perenggan 214 | — |

### Perlindungan Sosial & Simpanan Persaraan (`protection`, 8)

| id | Item | Kind | What the person gets / pays | Rule (`when`) | Certainty | Source | Timing |
|---|---|---|---|---|---|---|---|
| `i_saraan` | i-Saraan KWSP | manfaat | Padanan 20% caruman, sehingga RM500 setahun (RM5,000 seumur hidup) | `employment ∈ [self_employed, fisher, farmer] AND age < 60` | high | Perenggan 165, ms 95; Lampiran I Bil. 30, ms 262 | — |
| `i_saraan_plus` | i-Saraan Plus (baharu) | manfaat | Padanan 20% caruman, sehingga RM600 setahun (RM6,000 seumur hidup) | `employment = gig_ehailing AND age < 60` | high | Perenggan 165, ms 95; Lampiran I Bil. 30, ms 262 | — |
| `i_suri` | i-Suri KWSP | manfaat | Padanan 50% caruman, sehingga RM300 setahun (RM3,000 seumur hidup) | `gender = female AND employment = housewife AND age < 60 AND ekasih = true` | high | Perenggan 168, ms 95; Lampiran I Bil. 30, ms 262–263 · [web](https://www.kosmo.com.my/?p=736588) | — |
| `lindung_kendiri` | PERKESO Lindung Kendiri | manfaat | Kerajaan menanggung 70% caruman bagi tahun pertama dan 50% bagi tahun kedua | `employment ∈ [gig_ehailing, self_employed, fisher, farmer]` | check | Perenggan 166, ms 95; Lampiran I Bil. 30, ms 263 | — |
| `perkeso_pindah` | Insentif berpindah tempat kerja (PERKESO) | manfaat | Sehingga RM1,000 | `employment = jobseeker` | check | Perenggan 167, ms 95 | — |
| `kwsp_auto` | Akaun KWSP dibuka secara automatik pada umur 18 tahun | manfaat | Akaun dibuka secara automatik | `age ≥ 17 AND age ≤ 19` | high | Lampiran I Bil. 30, ms 264 | — |
| `kwsp_haji` | Pengeluaran KWSP untuk menunaikan haji | manfaat | Had pengeluaran dinaikkan kepada RM10,000 (sebelum ini RM3,000) | `assets includes haji_plan AND kwspMember = true` | high | Perenggan 228, ms 120; Lampiran I, ms 296 | — |
| `gcr_haji` | Penebusan awal GCR untuk menunaikan haji | manfaat | Penebusan sehingga RM10,000 | `assets includes haji_plan AND employment = civil_servant` | check | Perenggan 228, ms 120 | — |

### Keluarga & Wanita (`family`, 4)

| id | Item | Kind | What the person gets / pays | Rule (`when`) | Certainty | Source | Timing |
|---|---|---|---|---|---|---|---|
| `kasihnita` | KasihnITA: bantuan guaman untuk ibu tunggal | manfaat | Bantuan guaman | `gender = female AND marital = single_parent AND b40 = true` | check | Perenggan 142, ms 85; Lampiran I Bil. 26, ms 247 | — |
| `pembiayaan_wanita` | Pembiayaan untuk usahawan wanita | manfaat | Pembiayaan daripada RM30,000 hingga RM3 juta | `gender = female AND employment ∈ [self_employed, gig_ehailing, housewife, farmer, fisher]` | check | Perenggan 142, ms 84; Lampiran I Bil. 26, ms 247, 251–252 | — |
| `subsidi_taska` | Subsidi yuran taska | manfaat | Yuran taska lebih rendah | `childStages includes under6 AND b40 = true` | check | Lampiran I Bil. 26, ms 250 | — |
| `buai` | Bantuan Rawatan Kesuburan (BuAI) | manfaat | Bantuan kos rawatan kesuburan | `marital = married AND age ≥ 21 AND age ≤ 49` | check | Lampiran I Bil. 26, ms 250 | — |

### Belia, Latihan & Pekerjaan (`youth`, 6)

| id | Item | Kind | What the person gets / pays | Rule (`when`) | Certainty | Source | Timing |
|---|---|---|---|---|---|---|---|
| `mylesen_b2` | MyLesen B2 | manfaat | Lesen motosikal B2 secara percuma atau bersubsidi | `age ≥ 16 AND NOT(license = true) AND (b40 = true OR age < 18)` | check | Perenggan 143, ms 86; Lampiran I Bil. 26, ms 249 · [web](https://bernama.com/en/news.php?id=2569073) | Pelaksanaan bagi 2026 disasarkan selesai pada Julai 2026. Semak pengambilan seterusnya. |
| `plkn` | Program Latihan Khidmat Negara (PLKN) 2026 | manfaat | Latihan jati diri dan kenegaraan | `age ≥ 17 AND age ≤ 20` | check | Perenggan 143, ms 85; Lampiran I Bil. 26, ms 248 | — |
| `k_youth` | Program K-Youth (Khazanah) | manfaat | Latihan sambil bekerja | `age ≥ 18 AND age ≤ 30 AND employment ∈ [jobseeker, gig_ehailing, self_employed, employed_private, retired_other]` | check | Perenggan 143, ms 85; Lampiran I Bil. 26, ms 248 | — |
| `latihan_tvet` | Latihan kemahiran dan TVET | manfaat | Latihan dan pensijilan kemahiran | `employment ∈ [jobseeker, gig_ehailing, self_employed, retired_other, housewife] OR oku = true OR marital = single_parent OR status includes orang_asli` | check | Perenggan 65, ms 50–51; Perenggan 174 | — |
| `pembiayaan_belia` | Pembiayaan untuk usahawan belia | manfaat | Pembiayaan mikro dan bantuan perniagaan | `age ≥ 18 AND age ≤ 30 AND employment ∈ [self_employed, gig_ehailing, jobseeker, student_ipt]` | check | Perenggan 143, ms 86; Lampiran I Bil. 26, ms 249 | — |
| `rakan_muda` | Rakan Muda | manfaat | Program pembangunan belia | `age ≥ 15 AND age ≤ 30` | high | Perenggan 143, ms 86; Lampiran I Bil. 26, ms 248 | — |

### OKU, Warga Emas & Golongan Rentan (`vulnerable`, 6)

| id | Item | Kind | What the person gets / pays | Rule (`when`) | Certainty | Source | Timing |
|---|---|---|---|---|---|---|---|
| `bantuan_oku` | Bantuan untuk OKU (JKM) | manfaat | Elaun bulanan mengikut kategori | `oku = true` | check | Perenggan 149, ms 87; Lampiran I Bil. 27, ms 253 | — |
| `warga_emas` | Bantuan kebajikan warga emas | manfaat | Bantuan sosioekonomi dan pusat aktiviti | `age ≥ 60 AND b40 = true` | check | Perenggan 173, ms 96; Lampiran I Bil. 31, ms 266 | — |
| `rumah_warga_emas` | Rumah warga emas mandiri (KWAP) | manfaat | Kediaman khas untuk warga emas | `age ≥ 60 AND b40 = true` | check | Perenggan 174, ms 97; Lampiran I Bil. 31, ms 266 | — |
| `peluang_kedua` | Dasar Peluang Kedua Fast Track | manfaat | Proses pelepasan bankrap dipercepat | `status includes bankrupt` | check | Perenggan 150, ms 88; Lampiran I Bil. 27, ms 254 | — |
| `orang_asli` | Program untuk komuniti Orang Asli | manfaat | Jalan kampung, TABIKA dan program pendidikan anak | `status includes orang_asli` | high | Perenggan 144–148, ms 86–87 | — |
| `itekad` | Geran padanan iTEKAD | manfaat | Geran padanan untuk kemahiran, keusahawanan dan perlindungan | `b40 = true AND employment ∈ [self_employed, jobseeker, gig_ehailing]` | check | Perenggan 67; Lampiran I Bil. 12 | — |

### Mengikut Pekerjaan (Penjawat Awam, Veteran, Nelayan, Petani, Teksi) (`sector`, 22)

| id | Item | Kind | What the person gets / pays | Rule (`when`) | Certainty | Source | Timing |
|---|---|---|---|---|---|---|---|
| `nelayan_elaun` | Elaun Sara Hidup Nelayan | manfaat | Sehingga RM300 sebulan | `employment = fisher` | high | Perenggan 111, ms 73 | — |
| `pesawah` | Subsidi dan insentif pesawah | manfaat | Bantuan kira-kira RM4,300 sehektar bagi setiap musim | `employment = farmer AND farmType = padi` | high | Perenggan 106 dan 110, ms 70–72 | — |
| `pekebun_kecil` | Insentif pekebun kecil getah dan sawit | manfaat | Geran tanam semula sawit dan insentif pengeluaran getah | `employment = farmer AND farmType = smallholder` | check | Lampiran I Bil. 18, ms 218–219 | — |
| `agro` | Pembiayaan dan geran usahawan tani | manfaat | Pembiayaan Agrobank dan geran Agropreneur NextGen | `employment = farmer` | check | Perenggan 108, ms 71 | — |
| `bkht` | Bantuan kerugian akibat serangan hidupan liar | manfaat | Pampasan kerosakan harta benda dan tanaman | `employment = farmer` | check | Lampiran I, ms 238 | — |
| `penjawat_sspa` | Penambahbaikan saraan penjawat awam | manfaat | Kenaikan gaji SSPA Fasa 2 mulai Januari 2026 | `employment = civil_servant` | high | Perenggan 240–245, ms 125–126 | — |
| `veteran` | Peluang pekerjaan untuk veteran | manfaat | Keutamaan dalam pengambilan pekerja | `status includes veteran` | check | Perenggan 119–120, ms 75 | — |
| `teksi` | Insentif untuk pemandu teksi | manfaat | Tiada duti eksais dan cukai jualan untuk kereta nasional baharu | `status includes taxi` | high | Perenggan 76, ms 56 | — |
| `saringan_pemandu` | Pemeriksaan kesihatan percuma untuk pemandu | manfaat | Pemeriksaan kesihatan percuma oleh PERKESO | `status includes taxi AND age ≥ 40 AND age ≤ 59` | check | Perenggan 212, ms 114; Lampiran I Bil. 30, ms 264 | — |
| `penghargaan_pesara` | Bayaran penghargaan khas pesara dilanjutkan | manfaat | Diteruskan dari Januari hingga Disember | `employment = retired_gov` | check | Lampiran I Bil. 40 | — |
| `bsh_pesara_kemas` | Bayaran Sara Hidup pesara kontrak KEMAS dinaikkan | manfaat | RM500 sebulan (sebelum ini RM300) | `employment ∈ [retired_gov, retired_other]` | check | Perenggan 238; Lampiran I Bil. 40 | — |
| `apel_q` | Program APEL.Q INTAN untuk penjawat awam | manfaat | Kerajaan menanggung 50% kos pengajian, sehingga RM15,000 | `employment = civil_servant` | check | Lampiran I Bil. 40 | — |
| `etap_perubatan` | Elaun Tugas Atas Panggilan (ETAP) pegawai perubatan dinaikkan | manfaat | Naik antara 33% hingga 43% mengikut kelayakan | `employment = civil_servant` | check | Perenggan 182; Lampiran I Bil. 32 | Berkuat kuasa 1 Oktober 2025. |
| `lantikan_tetap_kkm` | Lantikan tetap untuk doktor, jururawat dan graduan kontrak KKM | manfaat | Tawaran lantikan tetap mulai 2026 | `employment = civil_servant` | check | Perenggan 182; Lampiran I Bil. 32 | — |
| `bipk_bipac` | Bayaran insentif pasukan khas (BIPK dan BIPAC) dinaikkan | manfaat | Kadar bayaran dinaikkan | `employment = civil_servant` | check | Lampiran I Bil. 40 | — |
| `geran_bsn` | Geran perniagaan BSN untuk usahawan mikro | manfaat | Sehingga RM10,000 untuk membeli peralatan perniagaan | `employment = self_employed` | check | Perenggan 156; Lampiran I Bil. 28 | — |
| `pinjaman_mikro` | Pinjaman mikro BSN dan TEKUN | manfaat | Pinjaman kecil untuk modal perniagaan | `employment = self_employed` | check | Perenggan 98 | — |
| `kwap_mikro` | Pembiayaan mikro KWAP untuk pesara | manfaat | Pembiayaan mikro untuk memulakan perniagaan komuniti | `employment = retired_gov` | check | Perenggan 138 | — |
| `tamu_desa` | Ruang niaga Tamu Desa di Sabah dan Sarawak | manfaat | Tapak dan ruang niaga baharu dengan kemudahan asas | `region ∈ [sabah, sarawak] AND employment = self_employed` | check | Perenggan 46; Lampiran I Bil. 8 | — |
| `buah_buahan` | Insentif pengusaha buah-buahan tempatan | manfaat | Insentif tanaman dan prasarana ladang | `employment = farmer AND farmType = other` | check | Perenggan 112; Lampiran I Bil. 20 | — |
| `penternak` | Insentif penternak ruminan kecil dan lembu pedaging | manfaat | Insentif bagi penternak yang mencapai kadar kelahiran ternakan yang ditetapkan | `employment = farmer AND farmType = other` | check | Lampiran I Bil. 20 | — |
| `elaun_imam_kafa` | Elaun bulanan imam, guru KAFA dan guru takmir | manfaat | Elaun bulanan diteruskan | `status includes religious_staff` | check | Lampiran I Bil. 36 | — |

### Pengangkutan & Mobiliti (`mobility`, 4)

| id | Item | Kind | What the person gets / pays | Rule (`when`) | Certainty | Source | Timing |
|---|---|---|---|---|---|---|---|
| `myraillife` | Pas MyRailLife percuma | manfaat | Perjalanan percuma tanpa had dengan KTM Komuter dan Shuttle DMU | `oku = true OR status includes oku_child OR isSchoolPupil = true OR childStages includes under6` | high | Perenggan 208, ms 111; Lampiran I Bil. 34, ms 284 | — |
| `van_oku` | Van mobiliti khas untuk OKU | manfaat | Perkhidmatan van yang boleh membawa kerusi roda | `oku = true OR status includes oku_child` | check | Perenggan 149, ms 88 | — |
| `lupus_kenderaan` | Geran menukar kereta lama | manfaat | Geran RM2,000 dan padanan RM2,000 daripada pengeluar (kira-kira RM4,000) | `assets includes old_car` | check | Perenggan 213, ms 114; Lampiran I Bil. 34, ms 287–288 | — |
| `ras` | Subsidi penerbangan luar bandar (RAS) | manfaat | Tambang penerbangan bersubsidi | `region ∈ [sabah, sarawak]` | high | Perenggan 208, ms 111 | — |

### Pelepasan Cukai Individu (`tax`, 7)

| id | Item | Kind | What the person gets / pays | Rule (`when`) | Certainty | Source | Timing |
|---|---|---|---|---|---|---|---|
| `tax_vaksin` | Pelepasan cukai pemvaksinan, kini untuk semua vaksin berdaftar | manfaat | Sehingga RM1,000 | `assets includes taxpayer` | high | Perenggan 184, ms 103; Lampiran II — Lampiran 1, ms 315 | — |
| `tax_insurans` | Pelepasan cukai insurans nyawa, kini termasuk untuk anak | manfaat | Sehingga RM3,000 | `assets includes taxpayer AND hasChildren = true` | high | Perenggan 181, ms 100; Lampiran II — Lampiran 4, ms 318 | — |
| `tax_taska` | Pelepasan cukai yuran taska, tadika dan pusat jagaan | manfaat | RM3,000 (kekal) | `assets includes taxpayer AND childStages includes any of [under6, primary]` | high | Perenggan 142, ms 84; Lampiran II — Lampiran 2, ms 316 | — |
| `tax_kurang_upaya` | Pelepasan cukai intervensi awal anak kurang upaya pembelajaran | manfaat | Dinaikkan daripada RM6,000 kepada RM10,000 | `assets includes taxpayer AND status includes oku_child` | high | Perenggan 149, ms 88; Lampiran II — Lampiran 3, ms 317 | — |
| `tax_lestari` | Pelepasan cukai peralatan hijau dan keselamatan rumah | manfaat | Sehingga RM2,500 | `assets includes taxpayer` | high | Lampiran II — Lampiran 5, ms 319 | — |
| `tax_pelancongan` | Pelepasan cukai tiket masuk tempat pelancongan dan program budaya | manfaat | Sehingga RM1,000 (Tahun Taksiran 2026 sahaja) | `assets includes taxpayer` | high | Perenggan 75, ms 56; Lampiran II — Lampiran 6, ms 320 | — |
| `potongan_derma` | Potongan cukai untuk sumbangan tunai | manfaat | Potongan cukai pendapatan bagi sumbangan yang layak | `assets includes taxpayer` | high | Perenggan 28, 82, 205; Lampiran I Bil. 34; Lampiran II — Lampiran 12 dan 13 | Tabung endowmen hospital pengajar: mulai Tahun Taksiran 2026. Program pencegahan rasuah: bagi program yang dilaksanakan dari 1 Januari 2026 hingga 31 Disember 2028. |

### Kes Khas: Gaya Hidup, Pelaburan & Perubahan Harga (`special`, 12)

| id | Item | Kind | What the person gets / pays | Rule (`when`) | Certainty | Source | Timing |
|---|---|---|---|---|---|---|---|
| `duti_rokok` | Harga rokok naik | kesan | Naik 40 sen sepaket (2 sen sebatang) | `lifestyle includes cigarette` | high | Perenggan 184, ms 102; Lampiran II — Lampiran 36, ms 356 | — |
| `duti_cerut` | Harga cerut naik | kesan | Duti eksais naik RM40 sekilogram | `lifestyle includes cigar` | high | Perenggan 184, ms 102; Lampiran II — Lampiran 37, ms 357 | — |
| `duti_heated_tobacco` | Harga produk tembakau yang dipanaskan naik | kesan | Duti eksais naik RM20 sekilogram kandungan tembakau | `lifestyle includes heated_tobacco` | high | Perenggan 184, ms 102; Lampiran II — Lampiran 38, ms 358 | — |
| `vape` | Rokok elektronik mungkin diharamkan | kesan | Kerajaan sedang meneliti larangan penggunaan | `lifestyle includes vape` | high | Lampiran I Bil. 32, ms 271 | — |
| `berhenti_merokok` | Produk bantuan berhenti merokok lebih murah | manfaat | Dikecualikan duti import dan cukai jualan hingga 31 Disember 2027 | `smoker = true` | high | Perenggan 184, ms 102; Lampiran II — Lampiran 39, ms 359 | — |
| `duti_alkohol` | Harga minuman beralkohol naik | kesan | Duti eksais naik 10% | `lifestyle includes alcohol` | high | Perenggan 184, ms 102; Lampiran II — Lampiran 40, ms 360 | — |
| `fi_klinik_swasta` | Fi rundingan klinik swasta disemak semula | kesan | Kini antara RM10 hingga RM80 (sebelum ini RM10 hingga RM35) | `age ≥ 18` | high | Perenggan 182, ms 101; Lampiran I Bil. 32, ms 270 | — |
| `duti_kontrak_kerja` | Tiada duti setem untuk kontrak pekerjaan bergaji rendah | manfaat | Dikecualikan jika gaji RM3,000 dan ke bawah sebulan | `employment ∈ [employed_private, jobseeker]` | check | Lampiran II — Lampiran 20, ms 336 | — |
| `pelabur_runcit` | Tiada duti setem untuk urus niaga ETF dan waran berstruktur | manfaat | Dikecualikan duti setem nota kontrak hingga 31 Disember 2028 | `assets includes invest_bursa` | high | Lampiran II — Lampiran 18 dan 19, ms 334–335 | — |
| `cukai_plt` | Cukai ke atas agihan keuntungan Perkongsian Liabiliti Terhad (PLT) | kesan | Cukai 2% ke atas agihan keuntungan melebihi RM100,000 setahun | `assets includes llp_partner` | check | Lampiran II — Lampiran 7, ms 321–322 | — |
| `ptptn_sekatan_perjalanan` | Sekatan perjalanan ke luar negara bagi peminjam PTPTN yang culas | kesan | Boleh disekat daripada ke luar negara | `age ≥ 18 AND ptptnBorrower = true` | check | Perenggan 202, ms 109 | — |
| `cukai_kenderaan_labuan` | Pengecualian cukai kenderaan di Labuan dan Langkawi dihadkan | kesan | Hanya bagi kenderaan bernilai sehingga RM300,000 | `age ≥ 18 AND region = labuan AND license = true` | high | Perenggan 27 | Berkuat kuasa 1 Januari 2026. |

---

## 5. Assumptions and known limits

- **Income bands approximate B40/M40:** ≤ RM5,000 and ≤ RM12,000. The DOSM lines are about RM5,249 and RM11,819.
- **Spouse's age isn't asked.** PeKa B40 also covers a spouse aged 40+.
- **Salary isn't asked** (only household income). The employment-contract stamp duty item is therefore `semak`.
- **Bumiputera-only programmes** are folded into broader cards, with the restriction stated in the text, rather than asking about ethnicity.
- **The clinic-fee change is shown to every adult** because it affects anyone using a private GP.
- **Portal links** are suggested official sites; verify them before launch.
- **Langkawi residents can't be targeted.** The region question has no Langkawi option, so the vehicle-exemption cap is shown to Labuan residents and names Langkawi in its text.
- **Some amounts aren't in the text.** The pensioners' special appreciation payment and the imam/KAFA/takmir monthly allowance have no per-person amount in the speech, so both are `semak`.
- **KEMAS contract pensioners** aren't a separate answer, so their allowance is shown as `semak` to all retirees, with KEMAS named in the text.

## 6. Integration

```js
let answers = {};
function next() {
  const q = B26Brain.getVisibleQuestions(answers).find(q => answers[q.id] === undefined);
  if (!q) return showResults(B26Brain.evaluate(answers));
  render(q);   // q.type: 'number' | 'single' | 'multi'; options with exclusive:true clear other picks
}
function onAnswer(id, value) { answers = B26Brain.pruneAnswers({ ...answers, [id]: value }); next(); }
```

- **Skip button:** each skippable question's last option has `skip: true` and value `'skip'`. It can be rendered as a separate "Langkau" link.
- **Tier labels:** read them from `B26Brain.TIERS`.

**`evaluate()` returns:**

| Key | Contents |
|---|---|
| `strSara` | `{ eligible: true\|false\|null, category, label, str, sara, saraMonthly, total, totalRange?, totalIfEkasih?, reason }` |
| `groups[]` | `{ id: 'layak'\|'mungkin', label, count, items[] }`: the results grid, "Berkemungkinan layak" then "Mungkin layak" (semak then mungkin); STR + SARA excluded |
| `byTheme[]` | `{ id, label, count, items[] }`; items sorted layak → semak → mungkin (not used on the results screen) |
| `items[]` | `{ id, kind, tier, tierLabel, title, value, summary, who, action, reasons[], needsConfirm[], timing, src, web, portal }` |
| `advisories[]` | `{ type: 'action' \| 'info' \| 'disclaimer', text }`, including a note listing skipped questions |
| `counts` | `{ total, layak, semak, mungkin }` |

## 7. Maintenance

1. Edit `BENEFITS`.
2. Run `node test.js && node verify2.js`.
3. Run `node gen-spec.js` to regenerate the tables in this document.

## 8. Verification record

**2 Oct 2026 (v2026.7):**
- `test.js`: 15,167 checks, 0 failures. New checks: the eight mandatory questions exist with the user's wording, can be skipped and are shown to every adult (OKU and licence to minors too); licence, PTPTN and OKU are gone from the multi-selects; children "Tidak" hides the follow-ups and uses the 0-children STR rate; an STR/SARA "Ya" shows mySalam and PeKa B40 at RM5,001–6,000 while the panel keeps the estimate; the KWSP answer beats the job guess; OKU, licence and PTPTN skips give `mungkin` cards.
- `verify2.js`: 30,000 users, all 115 items and 13 themes reachable, 0 invariant violations.
- `coverage.js --final`: passes, unchanged.

**2 Oct 2026 (v2026.6):**
- `test.js`: 14,755 checks, 0 failures. New checks: no "kesan" tier or warning label; the two groups hold every card except STR + SARA exactly once, eligible group first; a smoker's tobacco-duty card sits in the eligible group with no label; the spec contains the locked front-page text.
- `verify2.js`: 30,000 users, all 115 items and 13 themes reachable, 0 invariant violations (V5 now checks the groups instead of the old kesan tier).

**27 Sep 2026 (v2026.5):**
- `test.js`: 14,740 checks, 0 failures. New persona checks: micro loans for the self-employed only; the PTPTN travel ban only for adults who tick the PTPTN option (not for minors, and not without the option); TVET card for job seekers.
- `verify2.js`: 30,000 users, all 115 items and 13 themes reachable, 0 invariant violations.
- `coverage.js --final`: all 1,279 units decided (the 838 former bulk rows re-read blind), every item traces to a unit, and no question is left open.

**26 Sep 2026 (v2026.4):**
- `test.js`: 14,501 checks, 0 failures, including 42 new checks for the added items (one persona per item, plus guards: Labuan-only vehicle cap, taxpayer-only donation deduction, Sabah/Sarawak-only Tamu Desa, no civil-service or pensioner items for private employees).
- `verify2.js`: 30,000 users, all 113 items and 13 themes reachable, 0 invariant violations.
- `coverage.js --final`: all 1,279 units of the speech have a decision, every item traces to a unit, and no question is left open.

**25 Sep 2026 (v2026.3):**

**Round 1 — `test.js`: 12,362 checks, 0 failures**

- **STR/SARA:** every figure matches the speech and annex table (e.g. the RM4,600 maximum in perenggan 159).
- **Branching:** covers minors, eKasih visibility, skip paths and pruning. It also confirms there is no grade question and that every non-required question has a skip option.
- **Personas:** seven profiles — single mother, contract civil servant, Sabah pensioner-veteran, student, e-hailing driver, eKasih housewife, and a farmer who skipped questions.
- **Catalogue integrity:** ids, themes and fields are valid, and every rule refers to a fact that exists.
- **Language lint:** checks for banned or incorrect phrases. It was mutation-tested: injected "Makan gaji" and "RM3.1 bilion" were both caught.
- **Spending lint:** no allocation totals or beneficiary counts appear in what users read.

**Round 2 — `verify2.js`: 30,000 randomised users walking the real question flow, 0 invariant violations**

- **Reachability:** all 94 items and all 13 themes appear at least once.
- **Invariants checked:**
  - No `mungkin` result unless something was skipped or answered "Tidak pasti".
  - Every shown item re-tests true and every hidden item re-tests false.
  - STR totals come only from the speech's table, never exceed RM4,600, and respect the category rules.
  - Minors never see adult-only or lifestyle items.
  - Tax items appear only for taxpayers.
  - Tier sorting is correct and every result has an explanation.
- **Simulator bug found and fixed:** the first run exposed a bug in the *simulator* (multi-select answers were stored as objects). It was a harness bug, not a brain bug, and was fixed before the final run.
- **Manual review:** a full read-through of all 745 lines of Malay text found 16 wording issues, all fixed and added to the lint.

## 9. Keputusan pengguna (26 Sep 2026)

Decisions from the step-5 question rounds, recorded in `ledger-2026.tsv`. Don't re-ask these unless the source text changes.

| Measure (source) | Decision |
|---|---|
| Langkawi/Labuan vehicle tax exemption capped at RM300,000 (Perenggan 27) | Include as `kesan` for Labuan residents with a driving licence; name Langkawi in the text |
| PERKESO haemodialysis up to RM170 (Perenggan 170) | Include as `semak` for workers with PERKESO cover; no health question |
| Pensioners' special appreciation payment (Lampiran I Bil. 40) | Include |
| KEMAS contract pensioners' allowance RM500 a month (Perenggan 238) | Include |
| APEL.Q INTAN (Lampiran I Bil. 40) | Include |
| ETAP rise; permanent posts for contract medical staff (Perenggan 182) | Include |
| BIPK/BIPAC (Lampiran I Bil. 40) | Include |
| Solar ATAP (Perenggan 104) | Include |
| RESET insurance product (Lampiran I Bil. 32) | Exclude |
| LiKES internships (Lampiran I Bil. 11) | Exclude |
| Stamp duty 8% on homes bought by non-citizens (Perenggan 218) | Exclude (not for citizens) |
| Donation tax deductions (Perenggan 28, 82, 205; Lampiran I Bil. 34) | Include as one item for taxpayers |
| BSN business grant, iTEKAD, KWAP microfinance, Tamu Desa stalls | Include all four |
| SJPP guarantees for micro-entrepreneurs (Perenggan 98) | Exclude |
| Youth age limit 15–30 (Perenggan 143) | Already covered by the youth items |
| Fruit growers, livestock breeders, imam/KAFA allowance, tahfiz skills training | Include all four |
| Electricity tariff change; Sabah/Labuan power subsidy; strata titles | Exclude |
| Kota MADANI homes (Perenggan 214) | Include |
| Lemon Law (Perenggan 39); KWSP transfer study (Lampiran I Bil. 30) | Exclude (no money yet); check again next year |

### 27 Sep 2026: the benchmark re-read

The blind re-read of the 838 unread units found these 10 measures. Recorded in `ledger-2026.tsv`.

| Measure (source) | Decision |
|---|---|
| BSN and TEKUN micro loans (Perenggan 98) | Include (`pinjaman_mikro`, self-employed, `semak`) |
| KPWKM TVET courses for care workers (Perenggan 174) | Include in the existing TVET card |
| Travel ban on PTPTN borrowers who can pay but default (Perenggan 202) | Include as `kesan`, targeted by a new "Mempunyai pinjaman PTPTN" option in the `assets` question |
| Hawker tents, sound boxes and QR for night-market traders in Pangkor and Kuala Tahan (Perenggan 156) | Exclude |
| Yayasan Peneraju talent and certification programme (Lampiran I Bil. 25) | Exclude |
| 2 Years Exit Program, 2YEP (Lampiran I Bil. 28) | Exclude |
| Rare-disease treatment allocation (Lampiran I Bil. 32) | Exclude |
| Free helmets, 70,000 units (Lampiran I Bil. 34) | Exclude |
| MITRA Indian community programme (Lampiran I Bil. 35) | Exclude |
| Program Perumahan Penjawat Awam Malaysia MADANI, 2,586 homes (Lampiran I Bil. 40) | Exclude |
