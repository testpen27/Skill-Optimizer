# Semak Faedah Belanjawan 2026: build spec (v2026.5)

> Generated from `scripts/belanjawan2026-brain.js` by `scripts/export-brain-md.js` (brain data as of 2026-09-27). Don't edit this file by hand: change the brain, run the tests, and regenerate.

## How to use this file

This is the complete specification of the citizen-benefits checker for Ucapan Belanjawan 2026. Hand it to Claude Code (for example with the `tv3-interactive-embed` skill) to build the checker.

- **Run the engine; don't rewrite it.** The tested engine is included in full in the appendix. Put it in the page as-is, inside a `<script>`, and drive the questions and results from its API ("Using the engine" below). Sections 1 to 7 describe what the engine does, to help you design the screens and check the result. Don't re-implement them.
- **Follow the output controls.** They say which parts of the results screen are fixed and which are yours to design.
- **Use the Malay text as written.** Every question, rule, rate and sentence comes from the speech and its annexes and has passed the engine's tests.
- **Never invent or approximate a figure.** If something you need is not in this file, ask the user.
- **Build nothing from "Not to be built"** at the end of the file. Each item there was read in the speech and left out on purpose.
- **Check your build with the worked examples.** Enter each example's answers through your screens; the results must match.
- **Size:** 15 questions, 13 themes, 115 result cards, one STR + SARA calculator.

## Using the engine

The engine is plain ES5 JavaScript with no dependencies (about 99 KB). Paste the appendix code into a `<script>` before your own script; it defines `window.B26Brain` (in Node, `require()` returns the same object).

| Call | Returns |
|---|---|
| `B26Brain.getVisibleQuestions(answers)` | The questions to show now, in order, with branching applied. Each has `id`, `type` (`number`, `single`, `multi`), `text`, `help`, `options` (`v`, `l`, `exclusive`, `skip`). |
| `B26Brain.pruneAnswers(answers)` | The answers with those to now-hidden questions removed. Call it after every answer. |
| `B26Brain.evaluate(answers)` | The result: `strSara`, `byTheme`, `advisories`, `counts` (below). |
| `B26Brain.TIERS`, `B26Brain.THEMES`, `B26Brain.VERSION`, `B26Brain.DATA_AS_OF` | Tier labels, theme order, version and data date. |

Question loop:

```js
let answers = {};
function next() {
  const q = B26Brain.getVisibleQuestions(answers).find(q => answers[q.id] === undefined);
  if (!q) return renderResults(B26Brain.evaluate(answers));
  renderQuestion(q);
}
function onAnswer(id, value) {            // value: number | string | string[]
  answers = B26Brain.pruneAnswers({ ...answers, [id]: value });
  next();
}
// Back: delete answers[lastId], then next().
```

Result of `evaluate()`:

```js
{
  version, dataAsOf,
  strSara: { eligible: true | false | null, category, label, str, sara, saraMonthly, total,
            totalRange?, totalIfEkasih?, reason },      // reason: Malay sentence when not eligible / unknown
  byTheme: [ { id, label, count, items: [
    { id, kind, tier, tierLabel, title, value, summary, who, action,
      reasons: [...], needsConfirm: [...], timing, src, portal } ] } ],
  advisories: [ { type: "action" | "info" | "disclaimer", text } ],   // disclaimer is last
  counts: { total, layak, semak, mungkin, kesan }
}
```

## Output controls

How the results screen must look and read.

Each control has a status:

- **locked**: the build must follow the rule exactly.
- **undecided**: the user hasn't chosen yet. Claude Code may design this part freely, but should keep to the rule if it has no better reason.

### Always required

These come from the user's earlier decisions and are not optional.

- Show the Malay text exactly as the engine returns it: titles, values, summaries, reasons, tier labels, advisories. Don't reword, shorten or translate it.
- Always show the disclaimer advisory.
- Every question except age and region can be skipped. Show the skip option ("Tidak mahu menyatakan"), or a "Langkau" link that sends it.
- In a multi-select, an exclusive option ("Tiada yang berkaitan", "Tidak mahu menyatakan") clears the other selections.
- Build nothing from the "Not to be built" list.

### Front page (locked)

The page the reader sees first. The text below is exact; don't change, translate or restyle the wording (the casing is part of it).

```
KALKULATOR BELANJAWAN 2026      <- heading (H)

KETAHUI MANFAAT ANDA!               <- tagline (T)

[ MULA ]                            <- button
```

- Only these three elements are on the front page: the heading, the tagline and the **MULA** button. Nothing else is added: no questions, no summary, no extra copy.
- **Clicking MULA opens the calculator in an in-page modal:** a dialog over the same page, with the page behind it dimmed. It is not a new browser window (`window.open`), because popup blockers and phones make that unreliable, and the embed has to stay one self-contained block.
- The modal contains the whole calculator: the question flow first, then the results screen. Nothing of the calculator shows on the front page itself.
- The modal has a visible close button labelled "Tutup" that returns to the front page. Standard modal behaviour applies: `role="dialog"` with `aria-modal="true"`, focus moves into the dialog on open and back to MULA on close, Esc closes it, and the page behind doesn't scroll while it's open.
- On a phone the modal fills the screen. Its content must fit and scroll inside it, with no clipped text and no horizontal scrolling.
- Colours, fonts, imagery and spacing of the front page and modal are not decided yet; the builder designs them (see "Look and feel" below).

### Look and feel (undecided)

No style has been chosen. The builder may use a design skill or the house style of the skill it's working with, as long as every rule above is followed.

### Controls the user will decide

| # | Control | Status | Rule when locked |
|---|---|---|---|
| 1 | Results order | undecided | The STR + SARA card comes first. Then themes in the engine's order (`byTheme`), and within a theme layak, semak, mungkin, kesan (the engine already sorts them). Hide empty themes. Style `kesan` cards apart from benefits. |
| 2 | Card fields | undecided | Every card shows, in this order: tier label, title, value, summary, "Kenapa anda layak" (`reasons`), "Perlu disahkan" (`needsConfirm`, `mungkin` cards only), who, action, timing note, source line (`src`). |
| 3 | Fixed wording | undecided | Tier labels exactly as `B26Brain.TIERS`. The disclaimer is the last thing on the results screen. No extra marketing or summary copy written by the builder. |
| 4 | Summary line | undecided | Above the cards, one line with the number of cards and the STR + SARA total, plus counts per tier, built only from `counts` and `strSara`. |

To lock a control, change its status to `locked` (and edit its rule if needed). To add a control, add a row.

## 1. Question flow

- Ask the questions in the order listed. Show a question only when its "Shown when" condition is true (conditions use the derived facts in section 3, computed from the answers so far).
- Every question except those marked required and the age question gets an extra option `skip` "Tidak mahu menyatakan", which can be shown as a separate "Langkau" link.
- In a multi-select, an option marked *exclusive* clears every other selection.
- When a change of answer hides a question, drop that question's answer.
- Back navigation: remove the last answer and show that question again.

## 2. Questions (15)

| # | id | Type | Question (Malay, as shown) | Shown when | Options: value → label |
|---|---|---|---|---|---|
| 1 | `age` | number | Berapakah umur anda?<br>*Help:* Umur menentukan kelayakan program seperti STR, PeKa B40, bantuan warga emas dan pembiayaan rumah untuk golongan muda.<br>*(required)* | always | number, 0 to 120 |
| 2 | `region` | single | Di manakah anda menetap?<br>*(required)* | always | `semenanjung` → Semenanjung Malaysia<br>`sabah` → Sabah<br>`sarawak` → Sarawak<br>`labuan` → Wilayah Persekutuan Labuan |
| 3 | `self_school` | single | Adakah anda murid sekolah Kerajaan? | `age` < 18 | `yes` → Ya<br>`no` → Tidak<br>`skip` → Tidak mahu menyatakan *(exclusive)* |
| 4 | `marital` | single | Apakah status perkahwinan anda? | `age` ≥ 18 | `married` → Berkahwin<br>`single_parent` → Ibu atau bapa tunggal yang mempunyai anak tanggungan<br>`single` → Tiada pasangan (belum berkahwin, bercerai atau kematian pasangan)<br>`skip` → Tidak mahu menyatakan *(exclusive)* |
| 5 | `children` | single | Berapakah bilangan anak tanggungan anda?<br>*Help:* Anak berumur bawah 18 tahun, atau anak berumur 18 tahun ke atas yang masih belajar sepenuh masa atau OKU. | `age` ≥ 18 | `0` → Tiada<br>`1-2` → 1 hingga 2 orang<br>`3-4` → 3 hingga 4 orang<br>`5+` → 5 orang atau lebih<br>`skip` → Tidak mahu menyatakan *(exclusive)* |
| 6 | `child_stages` | multi | Di peringkat manakah anak anda sekarang? (pilih semua yang berkaitan) | `hasChildren` = true OR `childrenSkipped` = true | `under6` → Belum bersekolah atau prasekolah (bawah 6 tahun)<br>`primary` → Sekolah rendah Kerajaan<br>`secondary` → Sekolah menengah Kerajaan<br>`ipt` → Institusi pengajian tinggi (universiti, politeknik atau kolej)<br>`other` → Lain-lain (sudah bekerja, sekolah swasta dan sebagainya)<br>`none` → Tiada anak tanggungan *(exclusive)*<br>`skip` → Tidak mahu menyatakan *(exclusive)* |
| 7 | `income` | single | Berapakah anggaran pendapatan kasar bulanan isi rumah anda?<br>*Help:* Jumlah pendapatan semua ahli isi rumah yang bekerja. Jika anda tinggal seorang diri, masukkan pendapatan anda sendiri. | `age` ≥ 18 | `lt2500` → RM2,500 dan ke bawah<br>`2501_5000` → RM2,501 hingga RM5,000<br>`5001_6000` → RM5,001 hingga RM6,000<br>`6001_12000` → RM6,001 hingga RM12,000<br>`gt12000` → Melebihi RM12,000<br>`skip` → Tidak mahu menyatakan *(exclusive)* |
| 8 | `ekasih` | single | Adakah isi rumah anda berdaftar sebagai Miskin atau Miskin Tegar dalam sistem eKasih? | `age` ≥ 18 AND (`incomeMax` ≤ 5000 OR `incomeSkipped` = true) | `yes` → Ya<br>`no` → Tidak<br>`unsure` → Tidak pasti<br>`skip` → Tidak mahu menyatakan *(exclusive)* |
| 9 | `str_status` | single | Adakah anda sudah menerima Sumbangan Tunai Rahmah (STR) 2026? | `strEligible` = true | `yes` → Ya, sudah menerima<br>`no` → Belum menerima atau tidak memohon<br>`unsure` → Tidak pasti<br>`skip` → Tidak mahu menyatakan *(exclusive)* |
| 10 | `employment` | single | Apakah status pekerjaan anda sekarang? | `age` ≥ 18 | `employed_private` → Pekerja sektor swasta<br>`civil_servant` → Penjawat awam<br>`gig_ehailing` → Pemandu e-hailing atau penghantar p-hailing<br>`self_employed` → Bekerja sendiri, pekerja bebas atau peniaga kecil<br>`fisher` → Nelayan<br>`farmer` → Pesawah, petani, penternak atau pekebun kecil<br>`housewife` → Suri rumah sepenuh masa<br>`student_ipt` → Pelajar institusi pengajian tinggi<br>`jobseeker` → Graduan baharu atau sedang mencari pekerjaan<br>`retired_gov` → Pesara Kerajaan (berpencen)<br>`retired_other` → Bersara atau tidak bekerja<br>`skip` → Tidak mahu menyatakan *(exclusive)* |
| 11 | `farm_type` | single | Apakah jenis kegiatan pertanian utama anda? | `employment` = `farmer` | `padi` → Menanam padi<br>`smallholder` → Pekebun kecil getah atau sawit<br>`other` → Tanaman lain, ternakan atau akuakultur<br>`skip` → Tidak mahu menyatakan *(exclusive)* |
| 12 | `gender` | single | Apakah jantina anda?<br>*Help:* Digunakan untuk memaparkan program khusus wanita seperti i-Suri dan pembiayaan usahawan wanita. | `age` ≥ 18 | `female` → Perempuan<br>`male` → Lelaki<br>`skip` → Tidak mahu menyatakan *(exclusive)* |
| 13 | `assets` | multi | Perkara manakah yang berkaitan dengan anda? (pilih semua yang berkaitan) | always | `license` → Mempunyai lesen memandu yang masih sah<br>`diesel_vehicle` → Memiliki kenderaan persendirian berenjin diesel<br>`old_car` → Memiliki kereta berusia lebih 20 tahun<br>`first_home` → Merancang untuk membeli rumah pertama<br>`taxpayer` → Membayar cukai pendapatan atau mengisi e-Filing<br>`invest_bursa` → Melabur di Bursa Malaysia (saham, ETF atau waran)<br>`llp_partner` → Pekongsi dalam Perkongsian Liabiliti Terhad (PLT)<br>`ptptn_loan` → Mempunyai pinjaman PTPTN<br>`haji_plan` → Merancang untuk menunaikan haji<br>`none` → Tiada yang berkaitan *(exclusive)*<br>`skip` → Tidak mahu menyatakan *(exclusive)* |
| 14 | `status` | multi | Adakah mana-mana keadaan ini berkaitan dengan anda? (pilih semua yang berkaitan) | always | `oku_self` → Saya OKU berdaftar<br>`oku_child` → Anak saya OKU atau kurang upaya pembelajaran (seperti autisme atau ADHD)<br>`pregnant` → Saya atau pasangan sedang hamil<br>`veteran` → Veteran Angkatan Tentera Malaysia<br>`pjm` → Penerima Pingat Jasa Malaysia<br>`religious_staff` → Guru KAFA, guru takmir, imam, bilal, tok siak, noja atau marbut<br>`taxi` → Pemandu atau pemilik teksi, termasuk kereta sewa<br>`orang_asli` → Orang Asli<br>`bankrupt` → Sedang berstatus bankrap<br>`none` → Tiada yang berkaitan *(exclusive)*<br>`skip` → Tidak mahu menyatakan *(exclusive)* |
| 15 | `lifestyle` | multi | Soalan pilihan: adakah mana-mana perkara ini berkaitan dengan anda?<br>*Help:* Belanjawan 2026 menaikkan duti ke atas produk tembakau dan minuman beralkohol, serta mengecualikan cukai ke atas produk bantuan berhenti merokok. Jawapan ini hanya digunakan untuk memaparkan perubahan yang berkaitan. | `age` ≥ 18 | `cigarette` → Merokok<br>`cigar` → Menghisap cerut atau cerut kecil (cigarillo)<br>`heated_tobacco` → Menggunakan produk tembakau yang dipanaskan (heated tobacco)<br>`vape` → Menggunakan vape atau rokok elektronik<br>`alcohol` → Mengambil minuman beralkohol<br>`none` → Tiada yang berkaitan *(exclusive)*<br>`skip` → Tidak mahu menyatakan *(exclusive)* |

## 3. Derived facts

Rules and "Shown when" conditions test these facts, not the raw answers. A fact is **unknown** when the answer it depends on was skipped (or answered "Tidak pasti"); a fact that simply does not apply (for example, `ekasih` for someone earning above RM5,000) is **false**, not unknown.

| Fact | How it is worked out |
|---|---|
| `age` | The `age` answer as a number. |
| `adult` | `age` ≥ 18. |
| `region` | The `region` answer. |
| `eastMalaysia` | `region` is not `semenanjung` (Sabah, Sarawak or Labuan). |
| `marital` | The `marital` answer. Skipped → unknown. |
| `childCount` | `children` answer as a number: `0` → 0, `1-2` → 1, `3-4` → 3, `5+` → 5. Skipped → unknown. |
| `hasChildren` | `childCount` > 0, or any `child_stages` chosen. Skipped `children` → unknown. |
| `childrenSkipped` | `children` was skipped. |
| `childStages` | The `child_stages` answers, without `none`/`skip`. |
| `isSchoolPupil` | `child_stages` includes `primary` or `secondary`, or the person is under 18 and answered `self_school` = `yes`. |
| `income` | The `income` band value. Skipped → unknown. |
| `incomeSkipped` | `income` was skipped. |
| `incomeMax` | Upper end of the `income` band in RM: `lt2500` 2,500; `2501_5000` 5,000; `5001_6000` 6,000; `6001_12000` 12,000; `gt12000` no limit. Skipped → unknown. |
| `b40` | Income band upper end ≤ RM5,000 (approximates B40). Skipped income → unknown. |
| `b40m40` | Income band upper end ≤ RM12,000 (approximates B40 + M40). Skipped income → unknown. |
| `ekasih` | false if income is above RM5,000; otherwise the `ekasih` answer (`yes` → true, `no` → false). `unsure` or skipped → unknown. Not asked and income skipped → unknown. |
| `employment` | The `employment` answer. Skipped → unknown. |
| `farmType` | The `farm_type` answer. Skipped → unknown. |
| `gender` | The `gender` answer. Skipped → unknown. |
| `assets` | The `assets` answers, without `none`/`skip`. |
| `status` | The `status` answers, without `none`/`skip`. |
| `lifestyle` | The `lifestyle` answers, without `none`/`skip`. |
| `smoker` | `lifestyle` includes any of `cigarette`, `cigar`, `heated_tobacco`, `vape`. |
| `ipt` | true if `child_stages` includes `ipt` or `employment` = `student_ipt`; unknown if employment was skipped; otherwise false. |
| `kwspMember` | `employment` is one of `employed_private`, `gig_ehailing`, `self_employed`, `housewife`, `jobseeker`, `fisher`, `farmer`. Skipped → unknown. |
| `strEligible` | Result of the STR calculator below: true, false, or unknown when the calculator cannot decide. |
| `strCategory` | STR category from the calculator: `isi_rumah`, `warga_emas` or `bujang`. |

## 4. How a rule becomes a card

Each card has a rule (`when`). Evaluate it with three-valued logic:

- A test on a known fact is true or false. A test on an unknown fact is **unknown**. A test on a missing fact that is not unknown is false.
- `AND`: false if any part is false; otherwise unknown if any part is unknown; otherwise true.
- `OR`: true if any part is true; otherwise unknown if any part is unknown; otherwise false.
- `NOT`: swaps true and false; unknown stays unknown.

Then:

| Rule result | Card kind | Certainty | Card tier | Tier label (Malay) |
|---|---|---|---|---|
| false | any | any | not shown | — |
| true or unknown | `kesan` (a cost or obligation) | any | `kesan` | Perubahan yang menjejaskan anda |
| unknown | `manfaat` | any | `mungkin` | Mungkin layak |
| true | `manfaat` | `check` | `semak` | Semak kelayakan |
| true | `manfaat` | `high` | `layak` | Berkemungkinan layak |

- **"Kenapa anda layak":** list the `why` labels of the conditions that were true (shown with each rule below).
- **"Perlu disahkan":** for a `mungkin` card, list the `why` labels of the conditions that were unknown.
- **Order:** group cards by theme in this order: Bantuan Tunai & Kos Sara Hidup (`cash`); Subsidi Bahan Api & Tenaga (`subsidy`); Kesihatan & Insurans (`health`); Pendidikan (`education`); Perumahan (`housing`); Perlindungan Sosial & Simpanan Persaraan (`protection`); Keluarga & Wanita (`family`); Belia, Latihan & Pekerjaan (`youth`); OKU, Warga Emas & Golongan Rentan (`vulnerable`); Mengikut Pekerjaan (Penjawat Awam, Veteran, Nelayan, Petani, Teksi) (`sector`); Pengangkutan & Mobiliti (`mobility`); Pelepasan Cukai Individu (`tax`); Kes Khas: Gaya Hidup, Pelaburan & Perubahan Harga (`special`). Within a theme, order by tier: layak, semak, mungkin, kesan. Hide empty themes.
- Style `kesan` cards differently from benefits.

## 5. STR + SARA calculator

Shown as its own card first, and also as the `str_sara` card in the cash theme. Source: Perenggan 158–161; Lampiran I Bil. 29.

**Category:**

1. Under 18: not eligible (counted as a dependant).
2. `marital` = `married` or `single_parent` → **Isi Rumah**.
3. Otherwise, any children → **Isi Rumah**; no children and aged 60+ → **Warga Emas Tiada Pasangan**; no children and aged 21–59 → **Bujang**; aged 18–20 → not eligible.

**Rates (per year, before the eKasih top-up):**

| Category | Monthly household income | Children | STR | SARA | Total |
|---|---|---|---|---|---|
| Isi Rumah | RM2,500 dan ke bawah | Tiada anak | RM700 | RM1,200 (RM100 sebulan) | RM1,900 |
| Isi Rumah | RM2,500 dan ke bawah | 1–2 anak | RM1,200 | RM1,200 (RM100 sebulan) | RM2,400 |
| Isi Rumah | RM2,500 dan ke bawah | 3–4 anak | RM1,700 | RM1,200 (RM100 sebulan) | RM2,900 |
| Isi Rumah | RM2,500 dan ke bawah | 5 anak atau lebih | RM2,200 | RM1,200 (RM100 sebulan) | RM3,400 |
| Isi Rumah | RM2,501 hingga RM5,000 | Tiada anak | RM200 | RM1,200 (RM100 sebulan) | RM1,400 |
| Isi Rumah | RM2,501 hingga RM5,000 | 1–2 anak | RM450 | RM1,200 (RM100 sebulan) | RM1,650 |
| Isi Rumah | RM2,501 hingga RM5,000 | 3–4 anak | RM700 | RM1,200 (RM100 sebulan) | RM1,900 |
| Isi Rumah | RM2,501 hingga RM5,000 | 5 anak atau lebih | RM950 | RM1,200 (RM100 sebulan) | RM2,150 |
| Warga Emas Tiada Pasangan (60+) | RM2,500 dan ke bawah | — | RM600 | RM600 (RM50 sebulan) | RM1,200 |
| Warga Emas Tiada Pasangan (60+) | RM2,501 hingga RM5,000 | — | RM600 | RM600 (RM50 sebulan) | RM1,200 |
| Bujang (21–59) | RM2,500 dan ke bawah | — | RM0 | RM600 (RM50 sebulan) | RM600 |

Income above these bands → not eligible for that category.

**eKasih top-up** (when `ekasih` is true): SARA rises by RM1,200 a year for Isi Rumah (to RM200 a month), RM1,200 for Warga Emas (to RM150 a month) and RM600 for Bujang (to RM100 a month). When `ekasih` is unknown, show the total without the top-up and also the total "jika berdaftar eKasih".

**Number of children skipped** (Isi Rumah): show a range from the 0-children rate to the 5+ rate.

**When not eligible or unknown, show this reason (Malay, as written):**

| Situation | Result | Reason shown |
|---|---|---|
| Under 18 | not eligible | Anda berumur bawah 18 tahun, jadi anda dikira sebagai anak tanggungan dalam permohonan STR ibu bapa anda. |
| Marital status skipped | unknown | Anda memilih untuk tidak menyatakan status perkahwinan, jadi kategori STR tidak dapat ditentukan. Semak kelayakan di portal MySTR. |
| Income skipped | unknown | Anda memilih untuk tidak menyatakan pendapatan, jadi amaun STR tidak dapat dianggarkan. Semak kelayakan di portal MySTR. |
| Single, number of children skipped | unknown | Bilangan anak tidak dinyatakan, jadi kategori STR tidak dapat ditentukan. |
| Single, no children, aged 18–20 | not eligible | STR kategori Bujang hanya untuk mereka yang berumur 21 hingga 59 tahun. |
| Household income above RM5,000 | not eligible | STR kategori Isi Rumah untuk isi rumah berpendapatan RM5,000 dan ke bawah sebulan. |
| Single 60+, income above RM5,000 | not eligible | STR kategori Warga Emas Tiada Pasangan untuk pendapatan RM5,000 dan ke bawah sebulan. |
| Single 21–59, income above RM2,500 | not eligible | STR kategori Bujang untuk pendapatan RM2,500 dan ke bawah sebulan. |

## 6. Advisories

Shown above or below the results, in this order. The disclaimer is always last.

| When | Text (Malay, as written) |
|---|---|
| STR likely but the person said they don't receive it (`str_status` = `no`) | Anda berkemungkinan layak menerima STR tetapi belum menerimanya. Mohon di bantuantunai.hasil.gov.my. Permohonan STR juga membuka akses kepada SARA, mySalam, PeKa B40 dan Skim Perubatan MADANI. |
| STR likely and `str_status` is `unsure` or skipped | Semak status STR anda di bantuantunai.hasil.gov.my dan status SARA di sara.gov.my. |
| `ekasih` answered `unsure` | Status eKasih anda tidak pasti. Jika isi rumah anda berdaftar, kadar SARA lebih tinggi dan beberapa bantuan lain mungkin terpakai. Semak dengan Pejabat Daerah. |
| Any question skipped. The text lists the skipped topics, joined with ", " (example: gender skipped; names below) | Anda memilih untuk tidak menyatakan: jantina. Faedah yang bergantung pada maklumat ini dipaparkan sebagai "Mungkin layak" atau tidak dipaparkan. |
| Income above RM5,000, `taxpayer` not ticked and `assets` not skipped | Dengan pendapatan ini, anda mungkin perlu membayar cukai pendapatan. Beberapa pelepasan cukai baharu bagi Tahun Taksiran 2026 mungkin berkaitan dengan anda. |
| Always, shown last | Panduan umum berdasarkan Ucapan Belanjawan 2026 (maklumat setakat 2026-09-27). Ini bukan penentuan kelayakan rasmi. Sila sahkan dengan agensi yang berkaitan. |

**Topic names in the skipped-questions advisory:** `marital` → status perkahwinan; `children` → bilangan anak; `child_stages` → peringkat anak; `income` → pendapatan; `ekasih` → status eKasih; `str_status` → status STR; `employment` → pekerjaan; `gender` → jantina; `assets` → aset dan rancangan; `status` → keadaan khas; `lifestyle` → gaya hidup.

## 7. Result cards (115)

Each card shows: title, value, summary, who, action, the tier label, "Kenapa anda layak", and the source. Show `timing` as a time-sensitive note. Write all of it in Malay exactly as given.

### Bantuan Tunai & Kos Sara Hidup (`cash`, 10)

#### `str_sara`: Sumbangan Tunai Rahmah (STR) dan Sumbangan Asas Rahmah (SARA)

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** computed by the STR + SARA calculator (section 5)
- **Summary:** STR ialah bantuan tunai yang dibayar berperingkat sepanjang tahun. SARA pula ialah kredit bulanan dalam MyKad untuk membeli barangan keperluan asas di kedai yang menyertai program ini.
- **Who:** Isi rumah berpendapatan RM5,000 dan ke bawah; warga emas tiada pasangan berumur 60 tahun ke atas (RM5,000 dan ke bawah); bujang berumur 21 hingga 59 tahun (RM2,500 dan ke bawah).
- **Action:** Mohon atau kemas kini maklumat di portal MySTR. SARA dikreditkan secara automatik ke MyKad penerima STR.
- **Rule:** `strEligible` = true
- **Why labels:** "Dianggarkan layak menerima STR 2026"
- **Source:** Perenggan 158–161, ms 92–94; Lampiran I Bil. 29, ms 258–259 (some figures on this card come from https://www.bharian.com.my/amp/berita/nasional/2026/03/1515524/bhplus, checked before the brain moved to text-only sources)
- **Link:** https://bantuantunai.hasil.gov.my

#### `penghargaan_sara`: Penghargaan SARA

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** RM100 (sekali sahaja)
- **Summary:** Kredit SARA ke dalam MyKad untuk semua rakyat Malaysia berumur 18 tahun ke atas, bagi persiapan Ramadan dan Tahun Baru Cina.
- **Who:** Semua warganegara pemegang MyKad berumur 18 tahun ke atas.
- **Action:** Dikreditkan secara automatik ke MyKad.
- **Rule:** `age` ≥ 18
- **Why labels:** "Berumur 18 tahun ke atas"
- **Timing:** Telah disalurkan pada pertengahan Februari 2026.
- **Source:** Perenggan 160, ms 93

#### `bkk_penjawat`: Bantuan Khas Kewangan penjawat awam

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** RM500 (sekali sahaja)
- **Summary:** Untuk penjawat awam gred 15 dan ke bawah, termasuk yang dilantik secara kontrak.
- **Who:** Penjawat awam gred 15 dan ke bawah (lantikan tetap atau kontrak).
- **Action:** Dibayar secara automatik bersama gaji.
- **Rule:** `employment` = `civil_servant`
- **Why labels:** "Penjawat awam"
- **Timing:** Telah disalurkan pada awal Mac 2026 sempena Aidilfitri.
- **Source:** Perenggan 246, ms 127

#### `bkk_pesara`: Bantuan Khas Kewangan pesara dan veteran

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** RM250 (sekali sahaja)
- **Summary:** Untuk semua pesara Kerajaan, termasuk veteran yang berpencen dan yang tidak berpencen.
- **Who:** Pesara Kerajaan dan veteran Angkatan Tentera Malaysia.
- **Action:** Dibayar secara automatik.
- **Rule:** `employment` = `retired_gov` OR `status` includes `veteran`
- **Why labels:** "Pesara Kerajaan"; "Veteran Angkatan Tentera Malaysia"
- **Timing:** Telah disalurkan pada awal Mac 2026.
- **Source:** Perenggan 246, ms 127

#### `pjm`: Bayaran khas penerima Pingat Jasa Malaysia

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** RM500
- **Summary:** Sebagai penghargaan kepada anggota tentera yang menerima Pingat Jasa Malaysia.
- **Who:** Penerima Pingat Jasa Malaysia.
- **Action:** Semak dengan Jabatan Hal Ehwal Veteran (JHEV).
- **Rule:** `status` includes `pjm`
- **Why labels:** "Penerima Pingat Jasa Malaysia"
- **Source:** Perenggan 239, ms 125

#### `sumbangan_agama`: Sumbangan khas guru KAFA dan petugas masjid

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** RM500
- **Summary:** Penghargaan kepada guru KAFA, guru takmir, imam, bilal, tok siak, noja dan marbut.
- **Who:** Guru KAFA, guru takmir, imam, bilal, tok siak, noja dan marbut.
- **Action:** Melalui JAKIM atau Majlis Agama Islam Negeri.
- **Rule:** `status` includes `religious_staff`
- **Why labels:** "Guru KAFA atau petugas masjid"
- **Source:** Perenggan 247, ms 127

#### `jkm_bantuan`: Bantuan bulanan Jabatan Kebajikan Masyarakat (JKM)

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Bantuan bulanan mengikut kategori
- **Summary:** Antaranya Bantuan Warga Emas, Bantuan Kanak-kanak, Bantuan OKU Tidak Berupaya Bekerja serta Bantuan Penjagaan OKU dan Pesakit Kronik Terlantar.
- **Who:** Isi rumah miskin, OKU, warga emas dan kanak-kanak yang memerlukan, tertakluk kepada siasatan JKM.
- **Action:** Mohon di Pejabat Kebajikan Masyarakat Daerah atau portal JKM.
- **Rule:** `b40` = true AND (`ekasih` = true OR `age` ≥ 60 OR `status` includes `oku_self` OR `status` includes `oku_child` OR `marital` = `single_parent`)
- **Why labels:** "Pendapatan isi rumah RM5,000 dan ke bawah"; "Berdaftar sebagai Miskin atau Miskin Tegar dalam eKasih"; "Berumur 60 tahun ke atas"; "OKU berdaftar"; "Anak OKU atau kurang upaya pembelajaran"; "Ibu atau bapa tunggal"
- **Source:** Perenggan 162, ms 94; Lampiran I Bil. 29, ms 260
- **Link:** https://www.jkm.gov.my

#### `rebat_elektrik`: Rebat bil elektrik

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Sehingga RM40 sebulan
- **Summary:** Program rebat bil elektrik diteruskan untuk isi rumah miskin tegar.
- **Who:** Isi rumah miskin tegar yang berdaftar dalam eKasih.
- **Action:** Diberikan secara automatik berdasarkan data eKasih.
- **Rule:** `ekasih` = true
- **Why labels:** "Berdaftar sebagai Miskin atau Miskin Tegar dalam eKasih"
- **Source:** Lampiran I Bil. 29, ms 261

#### `payung_rahmah`: Jualan RAHMAH MADANI

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Barangan keperluan asas pada harga lebih rendah
- **Summary:** Jualan RAHMAH diadakan di semua kawasan DUN, termasuk berhampiran kem tentera dan kuarters polis.
- **Who:** Semua rakyat.
- **Action:** Semak jadual Jualan RAHMAH di kawasan anda (KPDN).
- **Rule:** `age` ≥ 18
- **Why labels:** "Berumur 18 tahun ke atas"
- **Source:** Perenggan 163, ms 94; Lampiran I Bil. 29, ms 261

#### `harga_sabah_sarawak`: Harga barangan asas setara Semenanjung

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Harga barangan asas sama seperti di Semenanjung
- **Summary:** Kerajaan menanggung kos pengangkutan dan pengedaran supaya barangan keperluan asas di Sabah, Sarawak dan Labuan, termasuk kawasan pedalaman, dijual pada harga yang sama dengan Semenanjung Malaysia.
- **Who:** Penduduk Sabah, Sarawak dan Labuan.
- **Action:** Tiada permohonan diperlukan; harga dikawal di kedai yang terlibat.
- **Rule:** `eastMalaysia` = true
- **Why labels:** "Menetap di Sabah, Sarawak atau Labuan"
- **Source:** Perenggan 164, ms 95; Lampiran I Bil. 29, ms 261

### Subsidi Bahan Api & Tenaga (`subsidy`, 6)

#### `budi95`: BUDI95: petrol RON95 bersubsidi

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** RM1.99 seliter
- **Summary:** Untuk warganegara berumur 16 tahun ke atas yang mempunyai lesen memandu yang sah. Kuota diselaraskan daripada 300 liter kepada 200 liter sebulan mulai 1 April 2026 sebagai langkah sementara.
- **Who:** Warganegara berumur 16 tahun ke atas dengan lesen memandu yang sah.
- **Action:** Imbas MyKad di pam atau kaunter stesen minyak yang terlibat.
- **Rule:** `age` ≥ 16 AND `assets` includes `license`
- **Why labels:** "Berumur 16 tahun ke atas"; "Mempunyai lesen memandu yang sah"
- **Timing:** Kuota 200 liter sebulan berkuat kuasa 1 April 2026. Semak kuota terkini.
- **Source:** Perenggan 40, ms 26–27 (some figures on this card come from https://says.com/my/seismik/budi95-kerajaan-umum-turunkan-kuota-ron95-ke-200-liter-sebulan-bermula-1-april-ini, checked before the brain moved to text-only sources)

#### `budi95_ehailing`: Kuota tambahan BUDI95 untuk pemandu e-hailing

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Sehingga 800 liter sebulan
- **Summary:** Kuota bergantung pada jarak perjalanan bulan sebelumnya: kurang daripada 2,000 km kekal pada kuota asas; 2,000 hingga 5,000 km layak 600 liter; lebih daripada 5,000 km layak 800 liter.
- **Who:** Pemandu e-hailing aktif yang mempunyai lesen memandu.
- **Action:** Diberikan secara automatik berdasarkan data syarikat e-hailing.
- **Rule:** `employment` = `gig_ehailing` AND `assets` includes `license`
- **Why labels:** "Pemandu e-hailing atau penghantar p-hailing"; "Mempunyai lesen memandu yang sah"
- **Source:** Perenggan 40, ms 27 (some figures on this card come from https://says.com/my/berita/pemandu-e-hailing-bawah-2000km-sebulan-tidak-layak-terima-kuota-tambahan-budi95, checked before the brain moved to text-only sources)

#### `diesel_rm200`: Bantuan diesel bersasar (BUDI MADANI)

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** RM200 sebulan
- **Summary:** Selepas subsidi diesel disasarkan, bantuan RM200 sebulan diberikan kepada pemilik individu kenderaan diesel, petani dan pekebun kecil.
- **Who:** Pemilik individu kenderaan persendirian berenjin diesel, petani dan pekebun kecil di Semenanjung Malaysia, tertakluk kepada syarat BUDI MADANI.
- **Action:** Semak kelayakan dan mohon melalui portal BUDI MADANI.
- **Rule:** `region` = `semenanjung` AND (`assets` includes `diesel_vehicle` OR `employment` = `farmer`)
- **Why labels:** "Menetap di Semenanjung Malaysia"; "Memiliki kenderaan diesel"; "Petani atau pekebun"
- **Source:** Perenggan 40, ms 26

#### `diesel_nelayan`: Diesel bersubsidi untuk nelayan

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** RM1.65 seliter
- **Summary:** Kerajaan mengekalkan harga diesel bersubsidi khusus untuk nelayan.
- **Who:** Nelayan berdaftar.
- **Action:** Melalui Lembaga Kemajuan Ikan Malaysia (LKIM).
- **Rule:** `employment` = `fisher`
- **Why labels:** "Nelayan"
- **Source:** Perenggan 111, ms 73

#### `rebat_cekap_tenaga`: Rebat pembelian peralatan cekap tenaga (Nur@PETRA)

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Rebat untuk peralatan elektrik cekap tenaga
- **Summary:** Rebat bagi menggalakkan pengguna domestik membeli peralatan elektrik yang cekap tenaga, sekali gus mengurangkan bil elektrik.
- **Who:** Pengguna domestik, tertakluk kepada syarat program.
- **Action:** Pantau pengumuman Kementerian Peralihan Tenaga dan Transformasi Air (PETRA).
- **Rule:** `age` ≥ 18
- **Why labels:** "Berumur 18 tahun ke atas"
- **Source:** Lampiran I, ms 222

#### `solar_atap`: Solar ATAP: jana elektrik sendiri di rumah

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Lebihan tenaga boleh dijual sebagai pengimbangan (offset) bil elektrik
- **Summary:** Melalui Solar Accelerated Transition Action Programme (Solar ATAP), pengguna elektrik domestik boleh memasang sistem solar PV untuk kegunaan sendiri dan menjual lebihan tenaga kepada syarikat utiliti sebagai pengimbangan dalam bil elektrik.
- **Who:** Pengguna elektrik domestik yang boleh memasang sistem solar PV.
- **Action:** Semak syarat penyertaan dengan syarikat utiliti anda.
- **Rule:** `age` ≥ 18
- **Why labels:** "Berumur 18 tahun ke atas"
- **Source:** Perenggan 104; Lampiran I Bil. 19

### Kesihatan & Insurans (`health`, 8)

#### `peka_b40`: PeKa B40

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Saringan kesihatan percuma dan bantuan alat perubatan sehingga RM20,000
- **Summary:** Termasuk insentif RM1,000 untuk melengkapkan rawatan kanser dan bantuan tambang pengangkutan ke hospital (sehingga RM500 di Semenanjung; RM1,000 di Sabah, Sarawak dan Labuan).
- **Who:** Warganegara berumur 40 tahun ke atas yang menerima STR, serta pasangan mereka.
- **Action:** Diberikan secara automatik kepada penerima STR. Bawa MyKad ke klinik panel PeKa B40.
- **Rule:** `age` ≥ 40 AND `strEligible` = true
- **Why labels:** "Berumur 40 tahun ke atas"; "Dianggarkan layak menerima STR 2026"
- **Source:** Lampiran I Bil. 32, ms 273 (some figures on this card come from https://www.malaysia.gov.my/my/topics/peka-b40, checked before the brain moved to text-only sources)
- **Link:** https://www.protecthealth.com.my

#### `mysalam`: mySalam

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** RM8,000 jika disahkan menghidap penyakit kritikal, serta RM50 sehari ketika dimasukkan ke wad
- **Summary:** Perlindungan takaful percuma untuk penyakit kritikal dan elaun harian ketika dimasukkan ke wad hospital Kerajaan (sehingga 14 hari setahun). Diteruskan pada tahun 2026.
- **Who:** Penerima STR dan pasangan mereka, tertakluk kepada had umur skim.
- **Action:** Diberikan secara automatik kepada penerima STR. Semak status di portal mySalam.
- **Rule:** `age` ≥ 18 AND `strEligible` = true
- **Why labels:** "Berumur 18 tahun ke atas"; "Dianggarkan layak menerima STR 2026"
- **Source:** Perenggan 181, ms 100–101; Lampiran I Bil. 32, ms 269 (some figures on this card come from https://bernama.com/bm/news.php?id=2574921, checked before the brain moved to text-only sources)
- **Link:** https://www.mysalam.com.my

#### `skim_perubatan_madani`: Skim Perubatan MADANI

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Rawatan di klinik swasta panel: RM250 setahun (keluarga), RM125 (warga emas), RM75 (bujang)
- **Summary:** Untuk rawatan penyakit ringan seperti demam, selesema, batuk dan kecederaan ringan.
- **Who:** Isi rumah penerima STR, termasuk anak berumur bawah 18 tahun.
- **Action:** Diberikan secara automatik kepada penerima STR. Bawa MyKad ke klinik panel.
- **Rule:** `strEligible` = true
- **Why labels:** "Dianggarkan layak menerima STR 2026"
- **Source:** Lampiran I Bil. 32, ms 272 (some figures on this card come from https://ringgitplus.com/ms/blog/sudut-pakar/str-cara-dapatkan-perlindungan-perubatan-percuma-jika-pendapatan-isi-rumah-anda-di-bawah-rm5000.html, checked before the brain moved to text-only sources)

#### `tdap_ibu`: Vaksin Tdap percuma untuk ibu hamil

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Suntikan vaksin percuma
- **Summary:** Melindungi bayi daripada jangkitan batuk kokol (pertusis) yang serius.
- **Who:** Ibu hamil.
- **Action:** Dapatkan di klinik kesihatan Kerajaan semasa pemeriksaan kehamilan.
- **Rule:** `status` includes `pregnant`
- **Why labels:** "Anda atau pasangan sedang hamil"
- **Source:** Lampiran I Bil. 26, ms 250

#### `saringan_wanita`: Ujian mamogram dan saringan kanser serviks bersubsidi

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Ujian saringan pada kos lebih rendah
- **Summary:** Subsidi untuk ujian mamogram (kanser payudara) dan saringan kanser serviks.
- **Who:** Wanita, tertakluk kepada syarat umur dan pendapatan program LPPKN atau KKM.
- **Action:** Semak dengan LPPKN atau klinik kesihatan berhampiran.
- **Rule:** `gender` = `female` AND `age` ≥ 20
- **Why labels:** "Wanita"; "Berumur 20 tahun ke atas"
- **Source:** Lampiran I Bil. 26, ms 247

#### `mhit_kwsp`: Akaun Sejahtera KWSP boleh digunakan untuk insurans perubatan asas

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Bayar premium menggunakan simpanan KWSP
- **Summary:** Pencarum boleh menggunakan simpanan Akaun Sejahtera untuk melanggan pelan asas insurans atau takaful perubatan dan kesihatan melalui platform i-Lindung.
- **Who:** Ahli KWSP.
- **Action:** Melalui i-Lindung dalam aplikasi KWSP i-Akaun.
- **Rule:** `kwspMember` = true
- **Why labels:** "Ahli KWSP"
- **Source:** Perenggan 181, ms 100; Lampiran I Bil. 32, ms 269
- **Link:** https://www.kwsp.gov.my

#### `duti_insurans_kecil`: Tiada duti setem untuk polisi insurans bernilai kecil

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Dikecualikan duti setem sehingga 2028
- **Summary:** Polisi insurans atau takaful dengan premium tahunan RM150 dan ke bawah (seperti insurans kebakaran, perjalanan dan kemalangan diri) serta produk Perlindungan Tenang.
- **Who:** Semua individu yang membeli polisi tersebut.
- **Action:** Diberikan secara automatik semasa membeli polisi.
- **Rule:** `age` ≥ 18
- **Why labels:** "Berumur 18 tahun ke atas"
- **Source:** Perenggan 181, ms 100; Lampiran II — Lampiran 16 dan 17, ms 332–333

#### `perkeso_dialisis`: Kadar bayaran rawatan hemodialisis PERKESO dinaikkan

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Sehingga RM170 bagi setiap rawatan (sebelum ini RM150)
- **Summary:** PERKESO menaikkan kadar maksimum yang dibayar bagi setiap rawatan hemodialisis.
- **Who:** Pencarum PERKESO yang menerima rawatan hemodialisis.
- **Action:** Semak kelayakan dengan PERKESO.
- **Rule:** `employment` is one of [`employed_private`, `gig_ehailing`, `self_employed`]
- **Why labels:** "Pekerja yang dilindungi PERKESO"
- **Source:** Perenggan 170; Lampiran I Bil. 30

### Pendidikan (`education`, 13)

#### `bap`: Bantuan Awal Persekolahan

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** RM150 bagi setiap murid
- **Summary:** Untuk semua murid sekolah Kerajaan. Mulai 2026, bantuan disalurkan di sekolah melalui guru kepada ibu bapa.
- **Who:** Semua murid sekolah Kerajaan.
- **Action:** Diterima di sekolah tanpa perlu memohon.
- **Rule:** `isSchoolPupil` = true
- **Why labels:** "Ada murid sekolah Kerajaan dalam keluarga"
- **Source:** Perenggan 192, ms 106

#### `bantuan_am`: Bantuan Am Persekolahan

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Kini diberikan sehingga Tingkatan 5
- **Summary:** Sebelum ini hanya sehingga Tingkatan 3. Kini diperluas kepada murid miskin sehingga Tingkatan 5.
- **Who:** Murid daripada keluarga miskin.
- **Action:** Melalui sekolah.
- **Rule:** `isSchoolPupil` = true AND (`ekasih` = true OR `income` = `lt2500`)
- **Why labels:** "Ada murid sekolah Kerajaan dalam keluarga"; "Berdaftar sebagai Miskin atau Miskin Tegar dalam eKasih"; "Pendapatan isi rumah RM2,500 dan ke bawah"
- **Source:** Perenggan 192, ms 106

#### `rmt_biasiswa`: Rancangan Makanan Tambahan dan Biasiswa Kecil Persekutuan

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Makanan berkhasiat percuma dan biasiswa
- **Summary:** Makanan berkhasiat di sekolah serta biasiswa untuk murid daripada keluarga berpendapatan rendah.
- **Who:** Murid daripada keluarga berpendapatan rendah, dipilih oleh pihak sekolah.
- **Action:** Melalui sekolah.
- **Rule:** `isSchoolPupil` = true AND `b40` = true
- **Why labels:** "Ada murid sekolah Kerajaan dalam keluarga"; "Pendapatan isi rumah RM5,000 dan ke bawah"
- **Source:** Perenggan 192, ms 105

#### `tuisyen_madani`: Tuisyen MADANI percuma

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Kelas tuisyen percuma
- **Summary:** Disediakan di sekolah yang menyertai program Sekolah Angkat MADANI.
- **Who:** Murid di sekolah yang menyertai program Sekolah Angkat MADANI.
- **Action:** Semak dengan pihak sekolah.
- **Rule:** `isSchoolPupil` = true AND `b40` = true
- **Why labels:** "Ada murid sekolah Kerajaan dalam keluarga"; "Pendapatan isi rumah RM5,000 dan ke bawah"
- **Source:** Perenggan 43, ms 28; Lampiran I, ms 143

#### `elaun_mbk`: Elaun Murid Berkeperluan Khas

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** RM150 sebulan
- **Summary:** Untuk semua murid OKU di sekolah Kerajaan.
- **Who:** Murid OKU berdaftar di sekolah Kerajaan.
- **Action:** Melalui sekolah. Murid perlu berdaftar sebagai OKU dengan JKM.
- **Rule:** `isSchoolPupil` = true AND (`status` includes `oku_child` OR (`status` includes `oku_self` AND `age` < 18))
- **Why labels:** "Ada murid sekolah Kerajaan dalam keluarga"; "Anak OKU atau kurang upaya pembelajaran"; "OKU berdaftar"
- **Source:** Perenggan 194, ms 107

#### `autisme`: Sokongan untuk anak autisme

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Kelas khas dan bantuan yuran pembelajaran
- **Summary:** Kelas Tunas Istimewa di TABIKA KEMAS untuk kanak-kanak autisme ringan, Pusat Perkhidmatan Autisme kini diperluas ke Labuan, Sabah dan Sarawak, serta Bantuan Yuran Pembelajaran Anak Autisme.
- **Who:** Ibu bapa kepada anak autisme.
- **Action:** Hubungi TABIKA KEMAS atau Pejabat Kebajikan Masyarakat Daerah.
- **Rule:** `status` includes `oku_child`
- **Why labels:** "Anak OKU atau kurang upaya pembelajaran"
- **Source:** Perenggan 149 dan 194, ms 87–88, 107; Lampiran I Bil. 29, ms 260

#### `ptptn_percuma`: Pendidikan Percuma PTPTN

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Pengajian percuma di IPTA
- **Summary:** Untuk anak keluarga miskin dan miskin tegar (berdasarkan data eKasih) yang belajar di institusi pengajian tinggi awam.
- **Who:** Pelajar IPTA daripada keluarga miskin atau miskin tegar dalam eKasih.
- **Action:** Mohon melalui PTPTN.
- **Rule:** `ipt` = true AND `ekasih` = true
- **Why labels:** "Anda atau anak anda belajar di institusi pengajian tinggi"; "Berdaftar sebagai Miskin atau Miskin Tegar dalam eKasih"
- **Source:** Perenggan 202, ms 109; Lampiran I Bil. 33, ms 280
- **Link:** https://www.ptptn.gov.my

#### `ptptn_kelas_pertama`: Pengecualian bayaran balik PTPTN untuk Kelas Pertama

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Tidak perlu membayar balik pinjaman
- **Summary:** Untuk peminjam daripada keluarga berpendapatan rendah dan sederhana yang memperoleh Ijazah Sarjana Muda Kepujian Kelas Pertama di IPTA.
- **Who:** Peminjam PTPTN di IPTA (B40 atau M40) yang lulus dengan Kelas Pertama.
- **Action:** Mohon pengecualian melalui PTPTN selepas bergraduat.
- **Rule:** `ipt` = true AND `b40m40` = true
- **Why labels:** "Anda atau anak anda belajar di institusi pengajian tinggi"; "Pendapatan isi rumah RM12,000 dan ke bawah"
- **Source:** Perenggan 202, ms 109
- **Link:** https://www.ptptn.gov.my

#### `gapai`: Geran Padanan Ihsan (GAPAI) SSPN

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Geran sehingga RM5,000
- **Summary:** Geran padanan atas simpanan SSPN untuk pelajar yang melanjutkan pengajian ke IPTA.
- **Who:** Keluarga berpendapatan sehingga RM6,000 sebulan yang mempunyai anak di IPTA.
- **Action:** Melalui akaun SSPN (PTPTN).
- **Rule:** `ipt` = true AND `incomeMax` ≤ 6000
- **Why labels:** "Anda atau anak anda belajar di institusi pengajian tinggi"; "Pendapatan isi rumah RM6,000 dan ke bawah"
- **Source:** Lampiran I Bil. 33, ms 280
- **Link:** https://www.ptptn.gov.my

#### `dapur_madani`: Ikhtiar Dapur MADANI

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Bantuan makanan dan peralatan memasak
- **Summary:** Bantuan makanan dan bahan mentah untuk mahasiswa berpendapatan rendah di universiti awam dan politeknik.
- **Who:** Mahasiswa B40 di universiti awam dan politeknik.
- **Action:** Melalui Bahagian Hal Ehwal Pelajar universiti atau politeknik.
- **Rule:** `employment` = `student_ipt` AND `b40` = true
- **Why labels:** "Pelajar institusi pengajian tinggi"; "Pendapatan isi rumah RM5,000 dan ke bawah"
- **Source:** Perenggan 200, ms 108

#### `job_on_campus`: MySiswa Job on Campus

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Kerja sambilan di dalam kampus
- **Summary:** Peluang menjana pendapatan sambil belajar dan mengasah kemahiran keusahawanan.
- **Who:** Mahasiswa B40 dan M40.
- **Action:** Melalui universiti.
- **Rule:** `employment` = `student_ipt` AND `b40m40` = true
- **Why labels:** "Pelajar institusi pengajian tinggi"; "Pendapatan isi rumah RM12,000 dan ke bawah"
- **Source:** Perenggan 200, ms 108

#### `celik_madani`: Program Celik MADANI (PNB)

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Pelaburan permulaan RM50 dalam ASB atau ASM
- **Summary:** Pelajar terpilih menerima pelaburan permulaan dalam ASB atau ASM bagi memupuk budaya menyimpan.
- **Who:** Pelajar terpilih.
- **Action:** Pantau pengumuman PNB.
- **Rule:** `isSchoolPupil` = true OR `ipt` = true
- **Why labels:** "Ada murid sekolah Kerajaan dalam keluarga"; "Anda atau anak anda belajar di institusi pengajian tinggi"
- **Source:** Perenggan 199, ms 108

#### `tahfiz_kemahiran`: Latihan kemahiran dan teknologi untuk pelajar tahfiz dan pondok

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Kursus teknologi digital dan AI serta latihan kemahiran profesional
- **Summary:** Pelajar tahfiz dan pondok didedahkan kepada teknologi digital dan AI melalui Program IPT@Komuniti oleh Majlis TVET Negara. Pelajar tahfiz juga dibekalkan latihan kemahiran profesional melalui GiatMARA untuk dimanfaatkan selepas tamat pengajian.
- **Who:** Pelajar sekolah tahfiz dan pondok.
- **Action:** Tanya pihak sekolah tahfiz atau pondok, atau pusat GiatMARA berhampiran.
- **Rule:** `age` ≥ 15 AND `age` ≤ 30 AND (`employment` = `student_ipt` OR (`adult` = false AND `isSchoolPupil` = true))
- **Why labels:** "Berumur 15 hingga 30 tahun"; "Pelajar"; "Pelajar sekolah"
- **Source:** Perenggan 65, 223; Lampiran I Bil. 11

### Perumahan (`housing`, 9)

#### `duti_rumah_pertama`: Tiada duti setem untuk rumah pertama

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Pengecualian penuh bagi rumah berharga sehingga RM500,000
- **Summary:** Pengecualian duti setem ke atas surat cara pindah milik dan perjanjian pinjaman, bagi perjanjian jual beli yang ditandatangani dari 1 Januari 2026 hingga 31 Disember 2027.
- **Who:** Warganegara yang membeli rumah kediaman pertama berharga RM500,000 dan ke bawah.
- **Action:** Dituntut semasa urusan penyeteman dokumen (melalui peguam atau LHDN).
- **Rule:** `assets` includes `first_home`
- **Why labels:** "Merancang membeli rumah pertama"
- **Source:** Perenggan 217, ms 116; Lampiran II — Lampiran 15, ms 331

#### `sjkp_akses`: SJKP MADANI: Akses Pemilikan Rumah Mampu Milik

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Jaminan pinjaman sehingga 120%, had RM360,000
- **Summary:** Jaminan Kerajaan untuk pembeli rumah pertama yang tidak mempunyai slip gaji tetap. Fi jaminan 0.25%.
- **Who:** Pembeli rumah pertama B40 dan M40, termasuk pekerja gig, pekerja bebas, bekerja sendiri dan usahawan mikro.
- **Action:** Mohon melalui bank yang menyertai SJKP.
- **Rule:** `assets` includes `first_home` AND `b40m40` = true
- **Why labels:** "Merancang membeli rumah pertama"; "Pendapatan isi rumah RM12,000 dan ke bawah"
- **Source:** Perenggan 216, ms 115; Lampiran I Bil. 35, ms 293–294

#### `sjkp_inklusif`: SJKP: Pembiayaan Rumah Inklusif

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Jaminan pinjaman sehingga 110%, had RM500,000
- **Summary:** Untuk pembeli rumah pertama yang berpendapatan tidak tetap. Fi jaminan 0.25% (pinjaman sehingga RM300,000) atau 0.50% (RM300,000 hingga RM500,000).
- **Who:** Pembeli rumah pertama berpendapatan tidak tetap, golongan belia dan kakitangan kontrak perkhidmatan awam.
- **Action:** Mohon melalui bank yang menyertai SJKP.
- **Rule:** `assets` includes `first_home` AND (`employment` is one of [`gig_ehailing`, `self_employed`, `fisher`, `farmer`] OR `employment` = `civil_servant` OR `age` ≤ 35)
- **Why labels:** "Merancang membeli rumah pertama"; "Bekerja sendiri atau berpendapatan tidak tetap"; "Penjawat awam"; "Berumur 35 tahun dan ke bawah"
- **Source:** Lampiran I Bil. 35, ms 293–294

#### `step_up`: Step-Up Financing

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Ansuran bulanan lebih rendah pada lima tahun pertama
- **Summary:** Jaminan Kerajaan untuk golongan muda membeli rumah pertama dengan bayaran balik yang lebih rendah pada lima tahun pertama.
- **Who:** Pembeli rumah pertama berumur 21 hingga 35 tahun.
- **Action:** Mohon melalui bank yang menyertai SJKP.
- **Rule:** `assets` includes `first_home` AND `age` ≥ 21 AND `age` ≤ 35
- **Why labels:** "Merancang membeli rumah pertama"; "Berumur 21 hingga 35 tahun"
- **Source:** Lampiran I Bil. 26, ms 249; Bil. 35, ms 294

#### `rumah_kontrak_awam`: Pinjaman rumah pertama untuk kakitangan kontrak Kerajaan

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Jaminan pinjaman sehingga 120%
- **Summary:** SJKP menjamin pinjaman sehingga 120% dan BSN menyediakan pembiayaan khas, termasuk untuk guru TABIKA dan TASKA KEMAS.
- **Who:** Penjawat awam lantikan kontrak yang membeli rumah pertama.
- **Action:** Mohon melalui BSN atau bank yang menyertai SJKP.
- **Rule:** `assets` includes `first_home` AND `employment` = `civil_servant`
- **Why labels:** "Merancang membeli rumah pertama"; "Penjawat awam"
- **Source:** Perenggan 237, ms 124

#### `lppsa`: Pembiayaan perumahan LPPSA

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Had pembiayaan dinaikkan kepada RM1 juta
- **Summary:** Pembiayaan kali kedua dipermudah mulai suku keempat 2026. Skim Pembiayaan Perumahan Muda (bawah 30 tahun) dilanjutkan hingga 31 Disember 2026.
- **Who:** Penjawat awam lantikan tetap.
- **Action:** Mohon melalui portal LPPSA.
- **Rule:** `employment` = `civil_servant`
- **Why labels:** "Penjawat awam"
- **Timing:** Skim Pembiayaan Perumahan Muda tamat pada 31 Disember 2026.
- **Source:** Perenggan 237, ms 125

#### `rumah_mampu_milik`: Rumah mampu milik Kerajaan (PRR, RMR, Residensi MADANI, PR1MA)

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Peluang memiliki rumah mampu milik
- **Summary:** Beberapa projek Program Residensi Rakyat, Rumah Mesra Rakyat, Residensi MADANI dan PR1MA dijangka siap pada tahun 2026.
- **Who:** Isi rumah B40 dan M40 yang belum memiliki rumah.
- **Action:** Daftar melalui portal perumahan KPKT, PR1MA atau kerajaan negeri.
- **Rule:** `assets` includes `first_home` AND `b40m40` = true
- **Why labels:** "Merancang membeli rumah pertama"; "Pendapatan isi rumah RM12,000 dan ke bawah"
- **Source:** Perenggan 216, ms 115; Lampiran I Bil. 35, ms 289

#### `rumah_daif`: Baik pulih atau bina semula rumah daif

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Rumah dibaiki atau dibina semula
- **Summary:** Termasuk rumah nelayan, melalui Program Perumahan Rakyat Sejahtera, Program Pembasmian Kemiskinan Bandar dan Bantuan Rumah Nelayan Laut B40.
- **Who:** Isi rumah miskin dalam eKasih dan nelayan B40 yang tinggal di rumah daif.
- **Action:** Mohon melalui Pejabat Daerah, KPKT atau Jabatan Perikanan.
- **Rule:** `ekasih` = true OR (`employment` = `fisher` AND `b40` = true)
- **Why labels:** "Berdaftar sebagai Miskin atau Miskin Tegar dalam eKasih"; "Nelayan"; "Pendapatan isi rumah RM5,000 dan ke bawah"
- **Source:** Perenggan 216, ms 115; Lampiran I Bil. 35, ms 290

#### `kota_madani`: Rumah di Kota MADANI Presint 19

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** 80% daripada rumah dikhaskan untuk penjawat awam
- **Summary:** Kota MADANI Presint 19 ialah bandar pintar dan hijau yang menyediakan rumah kediaman, kebanyakannya untuk penjawat awam.
- **Who:** Penjawat awam.
- **Action:** Pantau pengumuman permohonan.
- **Rule:** `employment` = `civil_servant`
- **Why labels:** "Penjawat awam"
- **Source:** Perenggan 214

### Perlindungan Sosial & Simpanan Persaraan (`protection`, 8)

#### `i_saraan`: i-Saraan KWSP

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Padanan 20% caruman, sehingga RM500 setahun (RM5,000 seumur hidup)
- **Summary:** Kerajaan memadankan caruman sukarela KWSP bagi mereka yang bekerja sendiri atau berpendapatan tidak tetap.
- **Who:** Mereka yang bekerja sendiri atau berpendapatan tidak tetap, berumur bawah 60 tahun.
- **Action:** Daftar melalui KWSP i-Akaun dan mula mencarum.
- **Rule:** `employment` is one of [`self_employed`, `fisher`, `farmer`] AND `age` < 60
- **Why labels:** "Bekerja sendiri atau berpendapatan tidak tetap"; "Berumur bawah 60 tahun"
- **Source:** Perenggan 165, ms 95; Lampiran I Bil. 30, ms 262
- **Link:** https://www.kwsp.gov.my

#### `i_saraan_plus`: i-Saraan Plus (baharu)

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Padanan 20% caruman, sehingga RM600 setahun (RM6,000 seumur hidup)
- **Summary:** Insentif padanan khas untuk pemandu e-hailing dan penghantar p-hailing sepenuh masa.
- **Who:** Pemandu e-hailing dan penghantar p-hailing sepenuh masa, berumur bawah 60 tahun.
- **Action:** Daftar melalui KWSP i-Akaun.
- **Rule:** `employment` = `gig_ehailing` AND `age` < 60
- **Why labels:** "Pemandu e-hailing atau penghantar p-hailing"; "Berumur bawah 60 tahun"
- **Source:** Perenggan 165, ms 95; Lampiran I Bil. 30, ms 262
- **Link:** https://www.kwsp.gov.my

#### `i_suri`: i-Suri KWSP

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Padanan 50% caruman, sehingga RM300 setahun (RM3,000 seumur hidup)
- **Summary:** Had umur kelayakan dinaikkan kepada 60 tahun, selaras dengan umur persaraan minimum.
- **Who:** Suri rumah berumur bawah 60 tahun yang berdaftar dalam eKasih.
- **Action:** Daftar di kaunter KWSP atau melalui i-Akaun.
- **Rule:** `gender` = `female` AND `employment` = `housewife` AND `age` < 60 AND `ekasih` = true
- **Why labels:** "Wanita"; "Suri rumah"; "Berumur bawah 60 tahun"; "Berdaftar sebagai Miskin atau Miskin Tegar dalam eKasih"
- **Source:** Perenggan 168, ms 95; Lampiran I Bil. 30, ms 262–263 (some figures on this card come from https://www.kosmo.com.my/?p=736588, checked before the brain moved to text-only sources)
- **Link:** https://www.kwsp.gov.my

#### `lindung_kendiri`: PERKESO Lindung Kendiri

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Kerajaan menanggung 70% caruman bagi tahun pertama dan 50% bagi tahun kedua
- **Summary:** Perlindungan kemalangan dan hilang upaya ketika bekerja untuk pekerja gig dan mereka yang bekerja sendiri dalam sektor yang belum diwajibkan, bagi pendaftaran kali pertama.
- **Who:** Pekerja gig dan mereka yang bekerja sendiri yang mendaftar buat kali pertama.
- **Action:** Daftar melalui portal PERKESO.
- **Rule:** `employment` is one of [`gig_ehailing`, `self_employed`, `fisher`, `farmer`]
- **Why labels:** "Bekerja sendiri atau berpendapatan tidak tetap"
- **Source:** Perenggan 166, ms 95; Lampiran I Bil. 30, ms 263
- **Link:** https://www.perkeso.gov.my

#### `perkeso_pindah`: Insentif berpindah tempat kerja (PERKESO)

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Sehingga RM1,000
- **Summary:** Untuk pencari kerja atau graduan baharu yang menerima tawaran kerja yang memerlukan mereka berpindah ke lokasi lain.
- **Who:** Pencari kerja dan graduan baharu.
- **Action:** Mohon melalui PERKESO (MYFutureJobs).
- **Rule:** `employment` = `jobseeker`
- **Why labels:** "Sedang mencari pekerjaan"
- **Source:** Perenggan 167, ms 95
- **Link:** https://www.perkeso.gov.my

#### `kwsp_auto`: Akaun KWSP dibuka secara automatik pada umur 18 tahun

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Akaun dibuka secara automatik
- **Summary:** Semua warganegara Malaysia akan didaftarkan sebagai ahli KWSP secara automatik apabila mencapai umur 18 tahun.
- **Who:** Warganegara yang mencapai umur 18 tahun.
- **Action:** Tiada tindakan diperlukan.
- **Rule:** `age` ≥ 17 AND `age` ≤ 19
- **Why labels:** "Berumur 17 hingga 19 tahun"
- **Source:** Lampiran I Bil. 30, ms 264

#### `kwsp_haji`: Pengeluaran KWSP untuk menunaikan haji

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Had pengeluaran dinaikkan kepada RM10,000 (sebelum ini RM3,000)
- **Summary:** Ahli KWSP boleh mengeluarkan simpanan yang lebih tinggi untuk menampung kos menunaikan haji.
- **Who:** Ahli KWSP yang akan menunaikan haji.
- **Action:** Mohon pengeluaran melalui KWSP.
- **Rule:** `assets` includes `haji_plan` AND `kwspMember` = true
- **Why labels:** "Merancang untuk menunaikan haji"; "Ahli KWSP"
- **Source:** Perenggan 228, ms 120; Lampiran I, ms 296
- **Link:** https://www.kwsp.gov.my

#### `gcr_haji`: Penebusan awal GCR untuk menunaikan haji

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Penebusan sehingga RM10,000
- **Summary:** Penjawat awam boleh menebus Gantian Cuti Rehat (GCR) lebih awal untuk menunaikan haji.
- **Who:** Penjawat awam yang akan menunaikan haji.
- **Action:** Mohon melalui jabatan masing-masing.
- **Rule:** `assets` includes `haji_plan` AND `employment` = `civil_servant`
- **Why labels:** "Merancang untuk menunaikan haji"; "Penjawat awam"
- **Source:** Perenggan 228, ms 120

### Keluarga & Wanita (`family`, 4)

#### `kasihnita`: KasihnITA: bantuan guaman untuk ibu tunggal

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Bantuan guaman
- **Summary:** Membantu ibu tunggal berpendapatan rendah dalam kes mahkamah seperti perceraian dan hak penjagaan anak.
- **Who:** Ibu tunggal berpendapatan rendah.
- **Action:** Mohon melalui Jabatan Pembangunan Wanita (KPWKM).
- **Rule:** `gender` = `female` AND `marital` = `single_parent` AND `b40` = true
- **Why labels:** "Wanita"; "Ibu tunggal"; "Pendapatan isi rumah RM5,000 dan ke bawah"
- **Source:** Perenggan 142, ms 85; Lampiran I Bil. 26, ms 247

#### `pembiayaan_wanita`: Pembiayaan untuk usahawan wanita

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Pembiayaan daripada RM30,000 hingga RM3 juta
- **Summary:** AIM Skim Paduri MADANI (sehingga RM30,000), BSN Mikro MADANI Wanita (sehingga RM100,000 pada kadar 4%), MARA DANANITA (sehingga RM150,000 pada kadar 3.5%, untuk Bumiputera), SME Bank MySMELady 2.0 (sehingga RM3 juta) dan Bank Rakyat BizLady.
- **Who:** Usahawan wanita, daripada perniagaan mikro hingga PMKS.
- **Action:** Mohon terus kepada AIM, BSN, MARA, SME Bank atau Bank Rakyat.
- **Rule:** `gender` = `female` AND `employment` is one of [`self_employed`, `gig_ehailing`, `housewife`, `farmer`, `fisher`]
- **Why labels:** "Wanita"; "Berniaga atau bekerja sendiri"
- **Source:** Perenggan 142, ms 84; Lampiran I Bil. 26, ms 247, 251–252

#### `subsidi_taska`: Subsidi yuran taska

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Yuran taska lebih rendah
- **Summary:** Subsidi yuran di taska institusi (mengikut pendapatan) dan taska komuniti untuk keluarga berpendapatan RM5,000 dan ke bawah.
- **Who:** Ibu bapa yang menghantar anak ke taska, berpendapatan RM5,000 dan ke bawah.
- **Action:** Mohon melalui taska atau JKM.
- **Rule:** `childStages` includes `under6` AND `b40` = true
- **Why labels:** "Ada anak bawah 6 tahun"; "Pendapatan isi rumah RM5,000 dan ke bawah"
- **Source:** Lampiran I Bil. 26, ms 250

#### `buai`: Bantuan Rawatan Kesuburan (BuAI)

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Bantuan kos rawatan kesuburan
- **Summary:** Bantuan untuk pasangan yang memerlukan rawatan bagi mendapatkan zuriat.
- **Who:** Pasangan suami isteri yang memerlukan rawatan kesuburan, tertakluk kepada syarat LPPKN.
- **Action:** Mohon melalui LPPKN.
- **Rule:** `marital` = `married` AND `age` ≥ 21 AND `age` ≤ 49
- **Why labels:** "Berkahwin"; "Berumur 21 hingga 49 tahun"
- **Source:** Lampiran I Bil. 26, ms 250

### Belia, Latihan & Pekerjaan (`youth`, 6)

#### `mylesen_b2`: MyLesen B2

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Lesen motosikal B2 secara percuma atau bersubsidi
- **Summary:** Diperluas kepada pelajar sekolah menengah, penuntut institusi pengajian tinggi dan belia daripada keluarga kurang berkemampuan.
- **Who:** Mereka yang berumur 16 tahun ke atas daripada keluarga B40 dan belum mempunyai lesen.
- **Action:** Mohon melalui JPJ negeri atau pihak sekolah.
- **Rule:** `age` ≥ 16 AND NOT (`assets` includes `license`) AND (`b40` = true OR `age` < 18)
- **Why labels:** "Berumur 16 tahun ke atas"; "Pendapatan isi rumah RM5,000 dan ke bawah"; "Pelajar sekolah"
- **Timing:** Pelaksanaan bagi 2026 disasarkan selesai pada Julai 2026. Semak pengambilan seterusnya.
- **Source:** Perenggan 143, ms 86; Lampiran I Bil. 26, ms 249 (some figures on this card come from https://bernama.com/en/news.php?id=2569073, checked before the brain moved to text-only sources)

#### `plkn`: Program Latihan Khidmat Negara (PLKN) 2026

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Latihan jati diri dan kenegaraan
- **Summary:** Membina jati diri, semangat kenegaraan dan kesukarelawanan. Dirintis di institusi pengajian tinggi sebelum dilaksanakan sepenuhnya pada 2027.
- **Who:** Belia yang dipilih (lepasan sekolah dan mahasiswa).
- **Action:** Semak status pemilihan melalui portal PLKN.
- **Rule:** `age` ≥ 17 AND `age` ≤ 20
- **Why labels:** "Berumur 17 hingga 20 tahun"
- **Source:** Perenggan 143, ms 85; Lampiran I Bil. 26, ms 248

#### `k_youth`: Program K-Youth (Khazanah)

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Latihan sambil bekerja
- **Summary:** Untuk belia tanpa ijazah dalam sektor semikonduktor, jentera, penyelenggaraan pesawat, digital dan teknologi.
- **Who:** Belia berumur 30 tahun dan ke bawah yang tidak mempunyai ijazah.
- **Action:** Mohon melalui laman Khazanah atau rakan industri.
- **Rule:** `age` ≥ 18 AND `age` ≤ 30 AND `employment` is one of [`jobseeker`, `gig_ehailing`, `self_employed`, `employed_private`, `retired_other`]
- **Why labels:** "Berumur 30 tahun dan ke bawah"; "Mencari atau ingin menukar pekerjaan"
- **Source:** Perenggan 143, ms 85; Lampiran I Bil. 26, ms 248

#### `latihan_tvet`: Latihan kemahiran dan TVET

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Latihan dan pensijilan kemahiran
- **Summary:** Melalui HRD Corp, pembiayaan PTPK (terutamanya bidang AI, kenderaan elektrik dan semikonduktor), GiatMARA (termasuk untuk pekerja gig), Kolej Komuniti (program pembelajaran sepanjang hayat untuk OKU, warga emas, ibu tunggal dan Orang Asli) serta kursus TVET untuk pekerja penjagaan (care workers) oleh KPWKM.
- **Who:** Pencari kerja, pekerja gig, mereka yang bekerja sendiri dan golongan rentan.
- **Action:** Mohon melalui HRD Corp, PTPK, GiatMARA, Kolej Komuniti atau KPWKM.
- **Rule:** `employment` is one of [`jobseeker`, `gig_ehailing`, `self_employed`, `retired_other`, `housewife`] OR `status` includes `oku_self` OR `marital` = `single_parent` OR `status` includes `orang_asli`
- **Why labels:** "Mencari kerja atau bekerja sendiri"; "OKU berdaftar"; "Ibu atau bapa tunggal"; "Orang Asli"
- **Source:** Perenggan 65, ms 50–51; Perenggan 174

#### `pembiayaan_belia`: Pembiayaan untuk usahawan belia

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Pembiayaan mikro dan bantuan perniagaan
- **Summary:** Pembiayaan mikro BSN untuk usahawan berumur 30 tahun dan ke bawah, serta program Tunas Usahawan Belia Bumiputera (TUBE) oleh SME Corp untuk latihan dan bantuan perniagaan.
- **Who:** Usahawan belia berumur 30 tahun dan ke bawah.
- **Action:** Mohon melalui BSN atau SME Corp.
- **Rule:** `age` ≥ 18 AND `age` ≤ 30 AND `employment` is one of [`self_employed`, `gig_ehailing`, `jobseeker`, `student_ipt`]
- **Why labels:** "Berumur 30 tahun dan ke bawah"; "Berniaga atau berminat untuk berniaga"
- **Source:** Perenggan 143, ms 86; Lampiran I Bil. 26, ms 249

#### `rakan_muda`: Rakan Muda

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Program pembangunan belia
- **Summary:** Program membina jati diri, pendidikan demokrasi dan kempen anti-buli, termasuk untuk belia luar bandar yang tercicir daripada pendidikan atau pekerjaan.
- **Who:** Belia berumur 15 hingga 30 tahun.
- **Action:** Sertai melalui portal atau aplikasi Rakan Muda.
- **Rule:** `age` ≥ 15 AND `age` ≤ 30
- **Why labels:** "Berumur 15 hingga 30 tahun"
- **Source:** Perenggan 143, ms 86; Lampiran I Bil. 26, ms 248

### OKU, Warga Emas & Golongan Rentan (`vulnerable`, 6)

#### `bantuan_oku`: Bantuan untuk OKU (JKM)

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Elaun bulanan mengikut kategori
- **Summary:** Antaranya Elaun OKU Tidak Berupaya Bekerja, Elaun Pekerja OKU, serta bantuan penjagaan OKU dan pesakit kronik terlantar.
- **Who:** OKU berdaftar dengan JKM, mengikut kategori bantuan.
- **Action:** Mohon di Pejabat Kebajikan Masyarakat Daerah.
- **Rule:** `status` includes `oku_self`
- **Why labels:** "OKU berdaftar"
- **Source:** Perenggan 149, ms 87; Lampiran I Bil. 27, ms 253
- **Link:** https://www.jkm.gov.my

#### `warga_emas`: Bantuan kebajikan warga emas

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Bantuan sosioekonomi dan pusat aktiviti
- **Summary:** Bantuan Sosioekonomi Warga Emas, Pusat Aktiviti Warga Emas (PAWE) dan Unit Penyayang Warga Emas.
- **Who:** Warga emas berumur 60 tahun ke atas yang berpendapatan rendah, tertakluk kepada syarat JKM.
- **Action:** Mohon di Pejabat Kebajikan Masyarakat Daerah.
- **Rule:** `age` ≥ 60 AND `b40` = true
- **Why labels:** "Berumur 60 tahun ke atas"; "Pendapatan isi rumah RM5,000 dan ke bawah"
- **Source:** Perenggan 173, ms 96; Lampiran I Bil. 31, ms 266

#### `rumah_warga_emas`: Rumah warga emas mandiri (KWAP)

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Kediaman khas untuk warga emas
- **Summary:** Projek rintis di Kepala Batas, Pulau Pinang untuk pesara dan golongan asnaf berpendapatan rendah. Lokasi lain sedang dinilai.
- **Who:** Pesara dan warga emas asnaf berpendapatan rendah.
- **Action:** Pantau pengumuman KWAP.
- **Rule:** `age` ≥ 60 AND `b40` = true
- **Why labels:** "Berumur 60 tahun ke atas"; "Pendapatan isi rumah RM5,000 dan ke bawah"
- **Source:** Perenggan 174, ms 97; Lampiran I Bil. 31, ms 266

#### `peluang_kedua`: Dasar Peluang Kedua Fast Track

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Proses pelepasan bankrap dipercepat
- **Summary:** Untuk ibu atau bapa tunggal, usahawan mikro yang terjejas akibat krisis, mangsa penipuan dan mangsa projek perumahan terbengkalai.
- **Who:** Individu bankrap dalam kategori yang disasarkan.
- **Action:** Hubungi Jabatan Insolvensi Malaysia (MdI).
- **Rule:** `status` includes `bankrupt`
- **Why labels:** "Sedang berstatus bankrap"
- **Source:** Perenggan 150, ms 88; Lampiran I Bil. 27, ms 254

#### `orang_asli`: Program untuk komuniti Orang Asli

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Jalan kampung, TABIKA dan program pendidikan anak
- **Summary:** Jalan ke kampung Orang Asli dinaik taraf, TABIKA dibaiki di semua kampung Orang Asli, Sekolah Terapung di Hulu Perak diperluas dan program makanan komuniti diteruskan. Akta Orang Asli 1954 akan dipinda untuk memperkukuh hak berkaitan tanah dan kebajikan.
- **Who:** Komuniti Orang Asli.
- **Action:** Melalui Jabatan Kemajuan Orang Asli (JAKOA).
- **Rule:** `status` includes `orang_asli`
- **Why labels:** "Orang Asli"
- **Source:** Perenggan 144–148, ms 86–87

#### `itekad`: Geran padanan iTEKAD

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Geran padanan untuk kemahiran, keusahawanan dan perlindungan
- **Summary:** iTEKAD diperluas untuk menyediakan geran padanan kepada penerima yang ingin meningkatkan kemahiran bagi pekerjaan dan pendapatan yang lebih stabil. Dana disumbangkan bersama oleh sektor swasta, termasuk institusi kewangan.
- **Who:** Golongan rentan, termasuk usahawan kecil dan pencari kerja.
- **Action:** Semak kelayakan melalui program iTEKAD.
- **Rule:** `b40` = true AND `employment` is one of [`self_employed`, `jobseeker`, `gig_ehailing`]
- **Why labels:** "Pendapatan isi rumah RM5,000 dan ke bawah"; "Bekerja sendiri atau mencari pekerjaan"
- **Source:** Perenggan 67; Lampiran I Bil. 12

### Mengikut Pekerjaan (Penjawat Awam, Veteran, Nelayan, Petani, Teksi) (`sector`, 22)

#### `nelayan_elaun`: Elaun Sara Hidup Nelayan

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Sehingga RM300 sebulan
- **Summary:** Serta insentif hasil tangkapan. Bantuan turut disediakan untuk menaik taraf vesel.
- **Who:** Nelayan berdaftar dengan LKIM atau Jabatan Perikanan.
- **Action:** Melalui LKIM.
- **Rule:** `employment` = `fisher`
- **Why labels:** "Nelayan"
- **Source:** Perenggan 111, ms 73

#### `pesawah`: Subsidi dan insentif pesawah

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Bantuan kira-kira RM4,300 sehektar bagi setiap musim
- **Summary:** Termasuk subsidi harga padi, baja dan benih; insentif membajak RM160 dan insentif racun RM300 sehektar semusim; serta Insentif Penuaian Padi baharu RM50 sehektar semusim.
- **Who:** Pesawah padi berdaftar.
- **Action:** Melalui Pejabat Pertanian, Pertubuhan Peladang, MADA atau KADA.
- **Rule:** `employment` = `farmer` AND `farmType` = `padi`
- **Why labels:** "Petani atau pekebun"; "Menanam padi"
- **Source:** Perenggan 106 dan 110, ms 70–72

#### `pekebun_kecil`: Insentif pekebun kecil getah dan sawit

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Geran tanam semula sawit dan insentif pengeluaran getah
- **Summary:** Insentif tanam semula untuk pokok sawit berusia 25 tahun (50% geran dan 50% pinjaman mudah pada kadar serendah 2%), Insentif Pengeluaran Getah, Insentif Pengeluaran Lateks serta Bantuan Musim Tengkujuh.
- **Who:** Pekebun kecil getah dan sawit.
- **Action:** Melalui RISDA, FELDA, FELCRA atau Agrobank.
- **Rule:** `employment` = `farmer` AND `farmType` = `smallholder`
- **Why labels:** "Petani atau pekebun"; "Pekebun kecil getah atau sawit"
- **Source:** Lampiran I Bil. 18, ms 218–219

#### `agro`: Pembiayaan dan geran usahawan tani

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Pembiayaan Agrobank dan geran Agropreneur NextGen
- **Summary:** Pembiayaan untuk mengembangkan, mengautomasikan dan memekanisasikan projek pertanian, serta geran permulaan dan geran pengembangan Agropreneur NextGen.
- **Who:** Petani, penternak dan pengusaha akuakultur. Agropreneur NextGen untuk golongan muda.
- **Action:** Mohon melalui Agrobank atau Kementerian Pertanian dan Keterjaminan Makanan.
- **Rule:** `employment` = `farmer`
- **Why labels:** "Petani atau pekebun"
- **Source:** Perenggan 108, ms 71

#### `bkht`: Bantuan kerugian akibat serangan hidupan liar

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Pampasan kerosakan harta benda dan tanaman
- **Summary:** Bantuan Kerugian Harta Benda dan Tanaman Akibat Serangan Hidupan Liar (BKHT) untuk mangsa yang terjejas.
- **Who:** Mangsa yang mengalami kerugian akibat konflik hidupan liar.
- **Action:** Laporkan kepada PERHILITAN.
- **Rule:** `employment` = `farmer`
- **Why labels:** "Petani atau pekebun"
- **Source:** Lampiran I, ms 238

#### `penjawat_sspa`: Penambahbaikan saraan penjawat awam

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Kenaikan gaji SSPA Fasa 2 mulai Januari 2026
- **Summary:** Sistem Saraan Perkhidmatan Awam (SSPA) Fasa 2 berkuat kuasa Januari 2026. Elaun Sara Hidup RM900 sebulan untuk penerima Hadiah Latihan Persekutuan Separa Biasiswa, dan Bantuan Insentif Berasaskan Prestasi diperluas kepada Kumpulan Pengurusan dan Profesional.
- **Who:** Penjawat awam Persekutuan.
- **Action:** Secara automatik atau melalui jabatan masing-masing.
- **Rule:** `employment` = `civil_servant`
- **Why labels:** "Penjawat awam"
- **Source:** Perenggan 240–245, ms 125–126

#### `veteran`: Peluang pekerjaan untuk veteran

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Keutamaan dalam pengambilan pekerja
- **Summary:** Kontraktor MINDEF menyediakan peluang pekerjaan untuk veteran melalui skim PROTÉGÉ-Veteran, dan Agensi Kawalan dan Perlindungan Sempadan (AKPS) mengutamakan veteran dalam pengambilan.
- **Who:** Veteran Angkatan Tentera Malaysia.
- **Action:** Hubungi JHEV atau PERHEBAT.
- **Rule:** `status` includes `veteran`
- **Why labels:** "Veteran Angkatan Tentera Malaysia"
- **Source:** Perenggan 119–120, ms 75

#### `teksi`: Insentif untuk pemandu teksi

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Tiada duti eksais dan cukai jualan untuk kereta nasional baharu
- **Summary:** Pengecualian penuh duti eksais dan cukai jualan bagi pembelian kereta Proton atau Perodua baharu oleh pemilik teksi dan kereta sewa. HRD Corp juga menanggung kos kursus dan elaun untuk pemandu teksi berlesen yang mencarum.
- **Who:** Pemilik dan pemandu teksi serta kereta sewa persendirian.
- **Action:** Melalui APAD atau HRD Corp.
- **Rule:** `status` includes `taxi`
- **Why labels:** "Pemandu atau pemilik teksi"
- **Source:** Perenggan 76, ms 56

#### `saringan_pemandu`: Pemeriksaan kesihatan percuma untuk pemandu

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Pemeriksaan kesihatan percuma oleh PERKESO
- **Summary:** Untuk pemandu kenderaan pengangkutan awam dan barangan berumur 40 hingga 59 tahun.
- **Who:** Pemandu kenderaan awam dan barangan berumur 40 hingga 59 tahun.
- **Action:** Melalui PERKESO.
- **Rule:** `status` includes `taxi` AND `age` ≥ 40 AND `age` ≤ 59
- **Why labels:** "Pemandu pengangkutan awam"; "Berumur 40 hingga 59 tahun"
- **Source:** Perenggan 212, ms 114; Lampiran I Bil. 30, ms 264

#### `penghargaan_pesara`: Bayaran penghargaan khas pesara dilanjutkan

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Diteruskan dari Januari hingga Disember
- **Summary:** Bayaran penghargaan khas kepada pesara dan penerima pencen terbitan dilanjutkan. Kadar bayaran tidak dinyatakan dalam teks Belanjawan.
- **Who:** Pesara Kerajaan dan penerima pencen terbitan.
- **Action:** Semak dengan Jabatan Perkhidmatan Awam (JPA).
- **Rule:** `employment` = `retired_gov`
- **Why labels:** "Pesara Kerajaan"
- **Source:** Lampiran I Bil. 40

#### `bsh_pesara_kemas`: Bayaran Sara Hidup pesara kontrak KEMAS dinaikkan

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** RM500 sebulan (sebelum ini RM300)
- **Summary:** Kadar Bayaran Sara Hidup (BSH) bagi pesara kakitangan kontrak KEMAS dinaikkan daripada RM300 kepada RM500 sebulan.
- **Who:** Pesara kakitangan kontrak KEMAS.
- **Action:** Semak dengan KEMAS.
- **Rule:** `employment` is one of [`retired_gov`, `retired_other`]
- **Why labels:** "Pesara"
- **Source:** Perenggan 238; Lampiran I Bil. 40

#### `apel_q`: Program APEL.Q INTAN untuk penjawat awam

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Kerajaan menanggung 50% kos pengajian, sehingga RM15,000
- **Summary:** Untuk penjawat awam yang telah berkhidmat melebihi 15 tahun dan ingin melanjutkan pengajian ke peringkat yang lebih tinggi.
- **Who:** Penjawat awam yang telah berkhidmat melebihi 15 tahun.
- **Action:** Semak dengan INTAN atau bahagian sumber manusia jabatan anda.
- **Rule:** `employment` = `civil_servant`
- **Why labels:** "Penjawat awam"
- **Source:** Lampiran I Bil. 40

#### `etap_perubatan`: Elaun Tugas Atas Panggilan (ETAP) pegawai perubatan dinaikkan

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Naik antara 33% hingga 43% mengikut kelayakan
- **Summary:** Kadar ETAP yang tidak dikaji sejak 2011 dinaikkan. Contohnya, pegawai perubatan pakar yang bertugas atas panggilan aktif pada hari cuti menerima RM350 (sebelum ini RM250).
- **Who:** Pegawai perubatan, pegawai perubatan pakar dan pegawai pergigian.
- **Action:** Semak dengan jabatan anda.
- **Rule:** `employment` = `civil_servant`
- **Why labels:** "Penjawat awam"
- **Timing:** Berkuat kuasa 1 Oktober 2025.
- **Source:** Perenggan 182; Lampiran I Bil. 32

#### `lantikan_tetap_kkm`: Lantikan tetap untuk doktor, jururawat dan graduan kontrak KKM

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Tawaran lantikan tetap mulai 2026
- **Summary:** Doktor kontrak dan graduan Institut Latihan KKM akan ditawarkan jawatan tetap mulai 2026. Jururawat kontrak turut ditawarkan lantikan tetap.
- **Who:** Doktor kontrak, jururawat kontrak dan graduan Institut Latihan KKM.
- **Action:** Semak dengan Kementerian Kesihatan Malaysia (KKM).
- **Rule:** `employment` = `civil_servant`
- **Why labels:** "Penjawat awam"
- **Source:** Perenggan 182; Lampiran I Bil. 32

#### `bipk_bipac`: Bayaran insentif pasukan khas (BIPK dan BIPAC) dinaikkan

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Kadar bayaran dinaikkan
- **Summary:** Bayaran Insentif Pasukan Khas (BIPK) dan Bayaran Insentif Pasukan Atur Cara (BIPAC) ditambah baik melalui kenaikan kadar bayaran dan pelarasan syarat tempoh perkhidmatan.
- **Who:** Pegawai dan anggota pasukan khas.
- **Action:** Semak dengan pasukan atau jabatan anda.
- **Rule:** `employment` = `civil_servant`
- **Why labels:** "Penjawat awam"
- **Source:** Lampiran I Bil. 40

#### `geran_bsn`: Geran perniagaan BSN untuk usahawan mikro

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Sehingga RM10,000 untuk membeli peralatan perniagaan
- **Summary:** BSN menyediakan geran perniagaan kepada usahawan mikro yang berpotensi, sebagai modal untuk membeli peralatan perniagaan.
- **Who:** Usahawan mikro.
- **Action:** Semak dengan cawangan BSN.
- **Rule:** `employment` = `self_employed`
- **Why labels:** "Bekerja sendiri atau peniaga kecil"
- **Source:** Perenggan 156; Lampiran I Bil. 28

#### `pinjaman_mikro`: Pinjaman mikro BSN dan TEKUN

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Pinjaman kecil untuk modal perniagaan
- **Summary:** BSN dan TEKUN Nasional menyediakan pinjaman mikro kepada usahawan mikro dan peniaga kecil untuk modal dan keperluan perniagaan.
- **Who:** Usahawan mikro dan peniaga kecil.
- **Action:** Mohon di cawangan BSN atau TEKUN Nasional.
- **Rule:** `employment` = `self_employed`
- **Why labels:** "Bekerja sendiri atau peniaga kecil"
- **Source:** Perenggan 98

#### `kwap_mikro`: Pembiayaan mikro KWAP untuk pesara

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Pembiayaan mikro untuk memulakan perniagaan komuniti
- **Summary:** KWAP menyediakan program pembiayaan mikro bagi pesara untuk memperkasa keusahawanan di peringkat komuniti.
- **Who:** Pesara Kerajaan.
- **Action:** Semak dengan KWAP.
- **Rule:** `employment` = `retired_gov`
- **Why labels:** "Pesara Kerajaan"
- **Source:** Perenggan 138

#### `tamu_desa`: Ruang niaga Tamu Desa di Sabah dan Sarawak

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Tapak dan ruang niaga baharu dengan kemudahan asas
- **Summary:** Tapak dan ruang niaga yang dilengkapi kemudahan asas ditambah untuk peniaga kecil Tamu Desa di Sabah dan Sarawak.
- **Who:** Peniaga kecil Tamu Desa di Sabah dan Sarawak.
- **Action:** Semak dengan pihak berkuasa tempatan.
- **Rule:** `region` is one of [`sabah`, `sarawak`] AND `employment` = `self_employed`
- **Why labels:** "Menetap di Sabah atau Sarawak"; "Bekerja sendiri atau peniaga kecil"
- **Source:** Perenggan 46; Lampiran I Bil. 8

#### `buah_buahan`: Insentif pengusaha buah-buahan tempatan

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Insentif tanaman dan prasarana ladang
- **Summary:** Untuk pengusaha buah-buahan tempatan, antaranya ladang nanas termasuk di Sarawak, serta tanaman durian belanda, jambu air dan limau besar.
- **Who:** Pengusaha buah-buahan tempatan.
- **Action:** Semak dengan pejabat pertanian berhampiran.
- **Rule:** `employment` = `farmer` AND `farmType` = `other`
- **Why labels:** "Petani atau pekebun"; "Tanaman lain, ternakan atau akuakultur"
- **Source:** Perenggan 112; Lampiran I Bil. 20

#### `penternak`: Insentif penternak ruminan kecil dan lembu pedaging

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Insentif bagi penternak yang mencapai kadar kelahiran ternakan yang ditetapkan
- **Summary:** Penternak ruminan kecil dengan kadar kelahiran ternakan sedia ada sekurang-kurangnya 100%, dan penternak lembu pedaging dengan kadar sekurang-kurangnya 60%, layak menerima insentif.
- **Who:** Penternak ruminan kecil dan lembu pedaging.
- **Action:** Semak dengan pejabat pertanian atau veterinar berhampiran.
- **Rule:** `employment` = `farmer` AND `farmType` = `other`
- **Why labels:** "Petani atau pekebun"; "Tanaman lain, ternakan atau akuakultur"
- **Source:** Lampiran I Bil. 20

#### `elaun_imam_kafa`: Elaun bulanan imam, guru KAFA dan guru takmir

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Elaun bulanan diteruskan
- **Summary:** Elaun bulanan kepada imam, guru KAFA dan guru takmir diteruskan pada tahun 2026. Kadar elaun tidak dinyatakan dalam teks Belanjawan.
- **Who:** Imam, guru KAFA dan guru takmir.
- **Action:** Semak dengan majlis agama Islam negeri.
- **Rule:** `status` includes `religious_staff`
- **Why labels:** "Petugas institusi agama Islam"
- **Source:** Lampiran I Bil. 36

### Pengangkutan & Mobiliti (`mobility`, 4)

#### `myraillife`: Pas MyRailLife percuma

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Perjalanan percuma tanpa had dengan KTM Komuter dan Shuttle DMU
- **Summary:** Untuk komuniti OKU dan semua murid sekolah, kini diperluas kepada kanak-kanak berumur bawah 6 tahun.
- **Who:** OKU, murid sekolah dan kanak-kanak berumur bawah 6 tahun.
- **Action:** Mohon pas melalui KTMB.
- **Rule:** `status` includes `oku_self` OR `status` includes `oku_child` OR `isSchoolPupil` = true OR `childStages` includes `under6`
- **Why labels:** "OKU berdaftar"; "Anak OKU atau kurang upaya pembelajaran"; "Ada murid sekolah Kerajaan dalam keluarga"; "Ada anak bawah 6 tahun"
- **Source:** Perenggan 208, ms 111; Lampiran I Bil. 34, ms 284

#### `van_oku`: Van mobiliti khas untuk OKU

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Perkhidmatan van yang boleh membawa kerusi roda
- **Summary:** Setiap van boleh membawa sehingga tiga penumpang berkerusi roda dan dilengkapi sistem pengangkat kerusi roda.
- **Who:** OKU, terutamanya pengguna kerusi roda.
- **Action:** Tempah melalui Prasarana (Rapid).
- **Rule:** `status` includes `oku_self` OR `status` includes `oku_child`
- **Why labels:** "OKU berdaftar"; "Anak OKU atau kurang upaya pembelajaran"
- **Source:** Perenggan 149, ms 88

#### `lupus_kenderaan`: Geran menukar kereta lama

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Geran RM2,000 dan padanan RM2,000 daripada pengeluar (kira-kira RM4,000)
- **Summary:** Untuk pemilik yang melupuskan kereta berusia lebih 20 tahun dan membeli kereta nasional baharu.
- **Who:** Pemilik kereta berusia lebih 20 tahun.
- **Action:** Melalui pengeluar kereta nasional (Proton atau Perodua).
- **Rule:** `assets` includes `old_car`
- **Why labels:** "Memiliki kereta berusia lebih 20 tahun"
- **Source:** Perenggan 213, ms 114; Lampiran I Bil. 34, ms 287–288

#### `ras`: Subsidi penerbangan luar bandar (RAS)

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Tambang penerbangan bersubsidi
- **Summary:** Subsidi Perkhidmatan Udara Luar Bandar untuk penduduk desa dan pedalaman Sabah dan Sarawak.
- **Who:** Penduduk pedalaman Sabah dan Sarawak.
- **Action:** Harga bersubsidi terpakai secara automatik pada laluan RAS.
- **Rule:** `region` is one of [`sabah`, `sarawak`]
- **Why labels:** "Menetap di Sabah atau Sarawak"
- **Source:** Perenggan 208, ms 111

### Pelepasan Cukai Individu (`tax`, 7)

#### `tax_vaksin`: Pelepasan cukai pemvaksinan, kini untuk semua vaksin berdaftar

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Sehingga RM1,000
- **Summary:** Sebelum ini terhad kepada lapan jenis vaksin. Kini meliputi semua vaksin yang berdaftar dengan KKM, untuk diri sendiri, pasangan atau anak.
- **Who:** Pembayar cukai pendapatan.
- **Action:** Tuntut semasa mengisi e-Filing bagi Tahun Taksiran 2026. Simpan resit.
- **Rule:** `assets` includes `taxpayer`
- **Why labels:** "Pembayar cukai pendapatan"
- **Source:** Perenggan 184, ms 103; Lampiran II — Lampiran 1, ms 315

#### `tax_insurans`: Pelepasan cukai insurans nyawa, kini termasuk untuk anak

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Sehingga RM3,000
- **Summary:** Pelepasan cukai premium insurans nyawa atau takaful hayat diperluas kepada anak (bawah 18 tahun, sedang belajar di institusi pengajian tinggi, atau OKU tanpa had umur).
- **Who:** Pembayar cukai yang membayar premium untuk anak.
- **Action:** Tuntut semasa mengisi e-Filing bagi Tahun Taksiran 2026.
- **Rule:** `assets` includes `taxpayer` AND `hasChildren` = true
- **Why labels:** "Pembayar cukai pendapatan"; "Mempunyai anak tanggungan"
- **Source:** Perenggan 181, ms 100; Lampiran II — Lampiran 4, ms 318

#### `tax_taska`: Pelepasan cukai yuran taska, tadika dan pusat jagaan

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** RM3,000 (kekal)
- **Summary:** Digabungkan menjadi RM3,000 secara kekal dan diperluas kepada pusat jagaan harian atau pusat transit berdaftar JKM untuk anak sehingga 12 tahun.
- **Who:** Ibu atau bapa (salah seorang sahaja) yang menghantar anak berumur 12 tahun dan ke bawah ke pusat jagaan berdaftar.
- **Action:** Tuntut semasa mengisi e-Filing bagi Tahun Taksiran 2026.
- **Rule:** `assets` includes `taxpayer` AND `childStages` includes any of [`under6`, `primary`]
- **Why labels:** "Pembayar cukai pendapatan"; "Mempunyai anak berumur 12 tahun dan ke bawah"
- **Source:** Perenggan 142, ms 84; Lampiran II — Lampiran 2, ms 316

#### `tax_kurang_upaya`: Pelepasan cukai intervensi awal anak kurang upaya pembelajaran

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Dinaikkan daripada RM6,000 kepada RM10,000
- **Summary:** Untuk pemeriksaan, program intervensi awal dan rawatan pemulihan anak berumur bawah 18 tahun (seperti autisme, ADHD, lewat perkembangan global dan sindrom Down).
- **Who:** Pembayar cukai yang mempunyai anak kurang upaya pembelajaran.
- **Action:** Tuntut semasa mengisi e-Filing bagi Tahun Taksiran 2026.
- **Rule:** `assets` includes `taxpayer` AND `status` includes `oku_child`
- **Why labels:** "Pembayar cukai pendapatan"; "Anak OKU atau kurang upaya pembelajaran"
- **Source:** Perenggan 149, ms 88; Lampiran II — Lampiran 3, ms 317

#### `tax_lestari`: Pelepasan cukai peralatan hijau dan keselamatan rumah

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Sehingga RM2,500
- **Summary:** Pengecas kenderaan elektrik, mesin kompos, dan kini mesin pengisar sisa makanan serta CCTV untuk kegunaan rumah (Tahun Taksiran 2026 dan 2027).
- **Who:** Pembayar cukai pendapatan.
- **Action:** Tuntut semasa mengisi e-Filing. CCTV dan mesin pengisar sisa makanan boleh dituntut sekali dalam tempoh dua tahun.
- **Rule:** `assets` includes `taxpayer`
- **Why labels:** "Pembayar cukai pendapatan"
- **Source:** Lampiran II — Lampiran 5, ms 319

#### `tax_pelancongan`: Pelepasan cukai tiket masuk tempat pelancongan dan program budaya

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Sehingga RM1,000 (Tahun Taksiran 2026 sahaja)
- **Summary:** Untuk fi masuk ke muzium, taman tema, taman negara, taman laut, zoo, geopark dan program kebudayaan, sempena Tahun Melawat Malaysia 2026.
- **Who:** Pembayar cukai pendapatan.
- **Action:** Simpan resit atau tiket dan tuntut semasa mengisi e-Filing bagi Tahun Taksiran 2026.
- **Rule:** `assets` includes `taxpayer`
- **Why labels:** "Pembayar cukai pendapatan"
- **Source:** Perenggan 75, ms 56; Lampiran II — Lampiran 6, ms 320

#### `potongan_derma`: Potongan cukai untuk sumbangan tunai

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Potongan cukai pendapatan bagi sumbangan yang layak
- **Summary:** Sumbangan tunai kepada program pencegahan rasuah yang diiktiraf SPRM, tabung endowmen hospital pengajar universiti awam, Akaun Amanah Jabatan Muzium Malaysia, serta projek komuniti, amal atau infrastruktur seperti hentian bas layak mendapat potongan cukai pendapatan.
- **Who:** Pembayar cukai yang membuat sumbangan tunai.
- **Action:** Simpan resit dan tuntut semasa mengisi e-Filing.
- **Rule:** `assets` includes `taxpayer`
- **Why labels:** "Pembayar cukai pendapatan"
- **Timing:** Tabung endowmen hospital pengajar: mulai Tahun Taksiran 2026. Program pencegahan rasuah: bagi program yang dilaksanakan dari 1 Januari 2026 hingga 31 Disember 2028.
- **Source:** Perenggan 28, 82, 205; Lampiran I Bil. 34; Lampiran II — Lampiran 12 dan 13

### Kes Khas: Gaya Hidup, Pelaburan & Perubahan Harga (`special`, 12)

#### `duti_rokok`: Harga rokok naik

- **Kind:** `kesan` (a cost or obligation); **certainty:** `high`
- **Value:** Naik 40 sen sepaket (2 sen sebatang)
- **Summary:** Duti eksais rokok dinaikkan secara berperingkat mulai 1 November 2025. Hasil tambahan disalurkan kepada KKM untuk program kesihatan paru-paru serta rawatan diabetes dan penyakit jantung.
- **Who:** Perokok.
- **Action:** Pertimbangkan bantuan berhenti merokok (lihat di bawah).
- **Rule:** `lifestyle` includes `cigarette`
- **Why labels:** "Merokok"
- **Source:** Perenggan 184, ms 102; Lampiran II — Lampiran 36, ms 356

#### `duti_cerut`: Harga cerut naik

- **Kind:** `kesan` (a cost or obligation); **certainty:** `high`
- **Value:** Duti eksais naik RM40 sekilogram
- **Summary:** Berkuat kuasa mulai 1 November 2025 sebagai kenaikan berperingkat.
- **Who:** Pengguna cerut dan cerut kecil (cigarillo).
- **Action:** Pertimbangkan bantuan berhenti merokok (lihat di bawah).
- **Rule:** `lifestyle` includes `cigar`
- **Why labels:** "Menghisap cerut atau cerut kecil (cigarillo)"
- **Source:** Perenggan 184, ms 102; Lampiran II — Lampiran 37, ms 357

#### `duti_heated_tobacco`: Harga produk tembakau yang dipanaskan naik

- **Kind:** `kesan` (a cost or obligation); **certainty:** `high`
- **Value:** Duti eksais naik RM20 sekilogram kandungan tembakau
- **Summary:** Berkuat kuasa mulai 1 November 2025 sebagai kenaikan berperingkat.
- **Who:** Pengguna produk tembakau yang dipanaskan.
- **Action:** Pertimbangkan bantuan berhenti merokok (lihat di bawah).
- **Rule:** `lifestyle` includes `heated_tobacco`
- **Why labels:** "Menggunakan produk tembakau yang dipanaskan"
- **Source:** Perenggan 184, ms 102; Lampiran II — Lampiran 38, ms 358

#### `vape`: Rokok elektronik mungkin diharamkan

- **Kind:** `kesan` (a cost or obligation); **certainty:** `high`
- **Value:** Kerajaan sedang meneliti larangan penggunaan
- **Summary:** Kerajaan sedang meneliti cadangan untuk mengharamkan penggunaan rokok elektronik (vape).
- **Who:** Pengguna vape atau rokok elektronik.
- **Action:** Pantau pengumuman KKM. Pertimbangkan bantuan berhenti merokok.
- **Rule:** `lifestyle` includes `vape`
- **Why labels:** "Menggunakan vape atau rokok elektronik"
- **Source:** Lampiran I Bil. 32, ms 271

#### `berhenti_merokok`: Produk bantuan berhenti merokok lebih murah

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Dikecualikan duti import dan cukai jualan hingga 31 Disember 2027
- **Summary:** Gula-gula getah nikotin dan tampalan nikotin kekal dikecualikan, dan kini diperluas kepada semburan nikotin dan lozeng nikotin. Sokongan berhenti merokok percuma juga tersedia melalui program mQuit KKM.
- **Who:** Sesiapa yang ingin berhenti merokok atau vape.
- **Action:** Dapatkan nasihat di klinik kesihatan atau farmasi. Sertai program mQuit KKM.
- **Rule:** `smoker` = true
- **Why labels:** "Merokok atau menggunakan produk nikotin"
- **Source:** Perenggan 184, ms 102; Lampiran II — Lampiran 39, ms 359

#### `duti_alkohol`: Harga minuman beralkohol naik

- **Kind:** `kesan` (a cost or obligation); **certainty:** `high`
- **Value:** Duti eksais naik 10%
- **Summary:** Berkuat kuasa mulai 1 November 2025. Hasil tambahan disalurkan kepada KKM.
- **Who:** Pengguna minuman beralkohol.
- **Action:** Tiada tindakan diperlukan.
- **Rule:** `lifestyle` includes `alcohol`
- **Why labels:** "Mengambil minuman beralkohol"
- **Source:** Perenggan 184, ms 102; Lampiran II — Lampiran 40, ms 360

#### `fi_klinik_swasta`: Fi rundingan klinik swasta disemak semula

- **Kind:** `kesan` (a cost or obligation); **certainty:** `high`
- **Value:** Kini antara RM10 hingga RM80 (sebelum ini RM10 hingga RM35)
- **Summary:** Kadar fi rundingan doktor di klinik swasta ditetapkan semula buat kali pertama sejak 2006, bergantung pada jenis perkhidmatan. Kadar minimum RM10 dikekalkan.
- **Who:** Semua pesakit yang mendapatkan rawatan di klinik swasta.
- **Action:** Tanya kadar fi sebelum mendapatkan rawatan. Klinik kesihatan Kerajaan kekal sebagai pilihan.
- **Rule:** `age` ≥ 18
- **Why labels:** "Berumur 18 tahun ke atas"
- **Source:** Perenggan 182, ms 101; Lampiran I Bil. 32, ms 270

#### `duti_kontrak_kerja`: Tiada duti setem untuk kontrak pekerjaan bergaji rendah

- **Kind:** `manfaat` (benefit); **certainty:** `check`
- **Value:** Dikecualikan jika gaji RM3,000 dan ke bawah sebulan
- **Summary:** Had gaji untuk pengecualian duti setem RM10 ke atas kontrak pekerjaan dinaikkan daripada RM300 kepada RM3,000 sebulan, bagi kontrak yang ditandatangani mulai 1 Januari 2026.
- **Who:** Pekerja yang menandatangani kontrak pekerjaan baharu dengan gaji RM3,000 dan ke bawah sebulan.
- **Action:** Tiada tindakan diperlukan.
- **Rule:** `employment` is one of [`employed_private`, `jobseeker`]
- **Why labels:** "Pekerja atau bakal pekerja"
- **Source:** Lampiran II — Lampiran 20, ms 336

#### `pelabur_runcit`: Tiada duti setem untuk urus niaga ETF dan waran berstruktur

- **Kind:** `manfaat` (benefit); **certainty:** `high`
- **Value:** Dikecualikan duti setem nota kontrak hingga 31 Disember 2028
- **Summary:** Pengecualian untuk jual beli dana dagangan bursa (ETF) dilanjutkan, dan pengecualian baharu untuk pembelian waran berstruktur.
- **Who:** Pelabur runcit di Bursa Malaysia.
- **Action:** Diberikan secara automatik melalui broker.
- **Rule:** `assets` includes `invest_bursa`
- **Why labels:** "Melabur di Bursa Malaysia"
- **Source:** Lampiran II — Lampiran 18 dan 19, ms 334–335

#### `cukai_plt`: Cukai ke atas agihan keuntungan Perkongsian Liabiliti Terhad (PLT)

- **Kind:** `kesan` (a cost or obligation); **certainty:** `check`
- **Value:** Cukai 2% ke atas agihan keuntungan melebihi RM100,000 setahun
- **Summary:** Bermula Tahun Taksiran 2026, agihan keuntungan PLT yang diterima oleh pekongsi individu melebihi RM100,000 setahun dikenakan cukai 2% dan perlu dilaporkan dalam borang nyata cukai.
- **Who:** Pekongsi individu dalam PLT.
- **Action:** Laporkan agihan keuntungan PLT dalam e-Filing.
- **Rule:** `assets` includes `llp_partner`
- **Why labels:** "Pekongsi dalam PLT"
- **Source:** Lampiran II — Lampiran 7, ms 321–322

#### `ptptn_sekatan_perjalanan`: Sekatan perjalanan ke luar negara bagi peminjam PTPTN yang culas

- **Kind:** `kesan` (a cost or obligation); **certainty:** `check`
- **Value:** Boleh disekat daripada ke luar negara
- **Summary:** Kerajaan akan mengenakan sekatan perjalanan ke luar negara kepada peminjam PTPTN yang mampu membayar dan bekerja di luar negara, tetapi culas membuat bayaran balik.
- **Who:** Peminjam PTPTN yang mampu membayar tetapi tidak membuat bayaran balik.
- **Action:** Semak baki pinjaman dan jadual bayaran balik melalui PTPTN.
- **Rule:** `age` ≥ 18 AND `assets` includes `ptptn_loan`
- **Why labels:** "Berumur 18 tahun ke atas"; "Mempunyai pinjaman PTPTN"
- **Source:** Perenggan 202, ms 109
- **Link:** https://www.ptptn.gov.my

#### `cukai_kenderaan_labuan`: Pengecualian cukai kenderaan di Labuan dan Langkawi dihadkan

- **Kind:** `kesan` (a cost or obligation); **certainty:** `high`
- **Value:** Hanya bagi kenderaan bernilai sehingga RM300,000
- **Summary:** Pengecualian cukai kenderaan di Labuan dan Langkawi dihadkan kepada kenderaan yang bernilai tidak melebihi RM300,000, bagi menangani ketirisan oleh pemilik kenderaan mewah.
- **Who:** Pemilik kenderaan di Labuan dan Langkawi.
- **Action:** Semak nilai kenderaan sebelum membeli kenderaan baharu.
- **Rule:** `age` ≥ 18 AND `region` = `labuan` AND `assets` includes `license`
- **Why labels:** "Berumur 18 tahun ke atas"; "Menetap di Wilayah Persekutuan Labuan"; "Mempunyai lesen memandu"
- **Timing:** Berkuat kuasa 1 Januari 2026.
- **Source:** Perenggan 27

## 8. Worked examples (acceptance tests)

Your build must produce exactly these results for these answers. They are computed by the engine.

### Contoh 1: Ibu tunggal, 45, dua anak sekolah, pendapatan bawah RM2,500, eKasih tidak pasti, bekerja sendiri, merokok

**Answers:** `{"age":45,"region":"semenanjung","marital":"single_parent","children":"3-4","child_stages":["primary","secondary"],"income":"lt2500","ekasih":"unsure","str_status":"no","employment":"self_employed","gender":"female","assets":["license"],"status":["none"],"lifestyle":["cigarette"]}`

**STR + SARA:** Isi Rumah. STR RM1,700, SARA RM1,200 (RM100 sebulan), jumlah RM2,900; jika berdaftar eKasih RM4,100.

- **Berkemungkinan layak** (`layak`, 13): `str_sara`, `penghargaan_sara`, `payung_rahmah`, `budi95`, `peka_b40`, `mysalam`, `skim_perubatan_madani`, `mhit_kwsp`, `duti_insurans_kecil`, `bap`, `i_saraan`, `myraillife`, `berhenti_merokok`
- **Semak kelayakan** (`semak`, 16): `jkm_bantuan`, `rebat_cekap_tenaga`, `solar_atap`, `saringan_wanita`, `perkeso_dialisis`, `bantuan_am`, `rmt_biasiswa`, `tuisyen_madani`, `celik_madani`, `lindung_kendiri`, `kasihnita`, `pembiayaan_wanita`, `latihan_tvet`, `itekad`, `geran_bsn`, `pinjaman_mikro`
- **Mungkin layak** (`mungkin`, 2): `rebat_elektrik`, `rumah_daif`
- **Perubahan yang menjejaskan anda** (`kesan`, 2): `duti_rokok`, `fi_klinik_swasta`
- **Total cards:** 33

### Contoh 2: Penjawat awam, 34, berkahwin, anak bawah 6 tahun, RM2,501–5,000, pembayar cukai, rumah pertama, haji

**Answers:** `{"age":34,"region":"semenanjung","marital":"married","children":"1-2","child_stages":["under6"],"income":"2501_5000","ekasih":"no","str_status":"yes","employment":"civil_servant","gender":"male","assets":["license","first_home","taxpayer","haji_plan"],"status":["none"],"lifestyle":["skip"]}`

**STR + SARA:** Isi Rumah. STR RM450, SARA RM1,200 (RM100 sebulan), jumlah RM1,650.

- **Berkemungkinan layak** (`layak`, 17): `str_sara`, `penghargaan_sara`, `payung_rahmah`, `budi95`, `mysalam`, `skim_perubatan_madani`, `duti_insurans_kecil`, `duti_rumah_pertama`, `step_up`, `penjawat_sspa`, `myraillife`, `tax_vaksin`, `tax_insurans`, `tax_taska`, `tax_lestari`, `tax_pelancongan`, `potongan_derma`
- **Semak kelayakan** (`semak`, 16): `bkk_penjawat`, `rebat_cekap_tenaga`, `solar_atap`, `sjkp_akses`, `sjkp_inklusif`, `rumah_kontrak_awam`, `lppsa`, `rumah_mampu_milik`, `kota_madani`, `gcr_haji`, `subsidi_taska`, `buai`, `apel_q`, `etap_perubatan`, `lantikan_tetap_kkm`, `bipk_bipac`
- **Perubahan yang menjejaskan anda** (`kesan`, 1): `fi_klinik_swasta`
- **Total cards:** 34

### Contoh 3: Pesara Kerajaan, 67, Sabah, bujang, veteran

**Answers:** `{"age":67,"region":"sabah","marital":"single","children":"0","income":"2501_5000","ekasih":"no","str_status":"yes","employment":"retired_gov","gender":"male","assets":["license","old_car"],"status":["veteran","pjm"],"lifestyle":["none"]}`

**STR + SARA:** Warga Emas Tiada Pasangan (60 tahun ke atas). STR RM600, SARA RM600 (RM50 sebulan), jumlah RM1,200.

- **Berkemungkinan layak** (`layak`, 12): `str_sara`, `penghargaan_sara`, `bkk_pesara`, `pjm`, `payung_rahmah`, `harga_sabah_sarawak`, `budi95`, `peka_b40`, `mysalam`, `skim_perubatan_madani`, `duti_insurans_kecil`, `ras`
- **Semak kelayakan** (`semak`, 10): `jkm_bantuan`, `rebat_cekap_tenaga`, `solar_atap`, `warga_emas`, `rumah_warga_emas`, `veteran`, `penghargaan_pesara`, `bsh_pesara_kemas`, `kwap_mikro`, `lupus_kenderaan`
- **Perubahan yang menjejaskan anda** (`kesan`, 1): `fi_klinik_swasta`
- **Total cards:** 23

### Contoh 4: Murid, 17, Sarawak

**Answers:** `{"age":17,"region":"sarawak","self_school":"yes","assets":["none"],"status":["none"]}`

**STR + SARA:** not eligible. "Anda berumur bawah 18 tahun, jadi anda dikira sebagai anak tanggungan dalam permohonan STR ibu bapa anda."

- **Berkemungkinan layak** (`layak`, 6): `harga_sabah_sarawak`, `bap`, `kwsp_auto`, `rakan_muda`, `myraillife`, `ras`
- **Semak kelayakan** (`semak`, 4): `celik_madani`, `tahfiz_kemahiran`, `mylesen_b2`, `plkn`
- **Total cards:** 10

### Contoh 5: Pemandu e-hailing, 28, bujang, bawah RM2,500, ada pinjaman PTPTN, vape dan alkohol

**Answers:** `{"age":28,"region":"semenanjung","marital":"single","children":"0","income":"lt2500","ekasih":"no","str_status":"yes","employment":"gig_ehailing","gender":"male","assets":["license","first_home","invest_bursa","ptptn_loan"],"status":["none"],"lifestyle":["vape","alcohol"]}`

**STR + SARA:** Bujang (21 hingga 59 tahun). STR RM0, SARA RM600 (RM50 sebulan), jumlah RM600.

- **Berkemungkinan layak** (`layak`, 14): `str_sara`, `penghargaan_sara`, `payung_rahmah`, `budi95`, `mysalam`, `skim_perubatan_madani`, `mhit_kwsp`, `duti_insurans_kecil`, `duti_rumah_pertama`, `step_up`, `i_saraan_plus`, `rakan_muda`, `berhenti_merokok`, `pelabur_runcit`
- **Semak kelayakan** (`semak`, 12): `budi95_ehailing`, `rebat_cekap_tenaga`, `solar_atap`, `perkeso_dialisis`, `sjkp_akses`, `sjkp_inklusif`, `rumah_mampu_milik`, `lindung_kendiri`, `k_youth`, `latihan_tvet`, `pembiayaan_belia`, `itekad`
- **Perubahan yang menjejaskan anda** (`kesan`, 4): `vape`, `duti_alkohol`, `fi_klinik_swasta`, `ptptn_sekatan_perjalanan`
- **Total cards:** 30

### Contoh 6: Petani, 50, pendapatan dilangkau

**Answers:** `{"age":50,"region":"semenanjung","marital":"married","children":"0","income":"skip","employment":"farmer","farm_type":"smallholder","gender":"skip","assets":["none"],"status":["none"],"lifestyle":["none"]}`

**STR + SARA:** unknown. "Anda memilih untuk tidak menyatakan pendapatan, jadi amaun STR tidak dapat dianggarkan. Semak kelayakan di portal MySTR."

- **Berkemungkinan layak** (`layak`, 5): `penghargaan_sara`, `payung_rahmah`, `mhit_kwsp`, `duti_insurans_kecil`, `i_saraan`
- **Semak kelayakan** (`semak`, 7): `diesel_rm200`, `rebat_cekap_tenaga`, `solar_atap`, `lindung_kendiri`, `pekebun_kecil`, `agro`, `bkht`
- **Mungkin layak** (`mungkin`, 10): `str_sara`, `jkm_bantuan`, `rebat_elektrik`, `peka_b40`, `mysalam`, `skim_perubatan_madani`, `saringan_wanita`, `rumah_daif`, `pembiayaan_wanita`, `mylesen_b2`
- **Perubahan yang menjejaskan anda** (`kesan`, 1): `fi_klinik_swasta`
- **Total cards:** 23

## 9. Known limits (tell the reader where relevant)

- Income bands approximate B40 (up to RM5,000) and M40 (up to RM12,000).
- The spouse's age is not asked, so a spouse aged 40+ does not trigger PeKa B40.
- Bumiputera-only programmes are folded into broader cards, with the restriction stated in the text.
- Langkawi residents can't be targeted (the region question has no Langkawi option); the vehicle-exemption cap is shown to Labuan residents and names Langkawi.
- This is general guidance, not an official eligibility decision. Budget 2027 will supersede it.

## 10. Not to be built

**For whoever develops the calculator:** do not implement anything on this list. Each unit was read in the speech and left out on purpose. Only the cards in this file are to be built. If you think something here should be included, ask the user; don't add it on your own.

Of 1279 units, 232 are used by the brain and 1047 are excluded.

### 1. Measures that reach people but are not built (29)

These are the ones a developer might be tempted to add.

#### Excluded by the user (18)

| Unit | Source | What the text says | Note |
|---|---|---|---|
| P39 | Perenggan 39 | Setelah penggubalan Akta Kredit Pengguna, Kerajaan akan meminda Akta Perlindungan Pengguna untuk memasukkan elemen Lemon Law bagi melindungi hak pengguna yang sering tertindas. | pengguna 2026-09-26: Lemon Law dikecualikan (tiada wang lagi) |
| P40.3 | Perenggan 40 (butiran 3) | Penyasaran subsidi dan penstrukturan tarif elektrik purata jimat 6 bilion ringgit. Malah, 85 peratus pengguna tidak dikenakan kenaikan tarif dan ada yang menikmati penurunan bil. | pengguna 2026-09-26: tarif elektrik tidak dipilih |
| P46.3 | Perenggan 46 (butiran 3) | Kendatipun kawal selia bekalan elektrik diserah sepenuhnya kepada Sabah Januari tahun lalu, Kerajaan Persekutuan tetap menyediakan 1.2 bilion ringgit untuk menjamin kelangsungan bekalan. | pengguna 2026-09-26: subsidi elektrik Sabah/Labuan tidak dipilih |
| P98.2 | Perenggan 98 (butiran 2) | Jumlah jaminan Kerajaan di bawah SJPP ditingkatkan kepada 30 bilion ringgit, ketimbang 20 bilion ringgit. Selain menjamin syarikat sektor bernilai tinggi, skop SJPP turut diperluas bagi menjamin usahawan mikro. | pengguna 2026-09-26: SJPP usahawan mikro tidak dipilih |
| P156.2 | Perenggan 156 (butiran 2) | menyediakan khemah penjaja, peranti sound box dan sistem QR kepada peniaga pasar malam di Pangkor, Perak dan Kuala Tahan, Pahang; | pengguna 2026-09-27: tidak dipilih |
| P181.1 | Perenggan 181 (butiran 1) | Sebanyak 60 juta ringgit dana bersama Kerajaan dan industri disediakan bagi memperkenalkan produk insurans asas mampu milik untuk semua dan melaksanakan Diagnosis Related Group (DRG). | same measure as L1.32.9 (RESET basic insurance product), which the user excluded on 2026-09-26 |
| L1.5.4 | Lampiran I Bil. 5 (butiran 4) | Penjimatan tahunan melalui penyasaran RM6b subsidi elektrik di mana 85% pengguna tidak dikenakan kenaikan tarif malahan ada yang menikmati penurunan bil Nilai | pengguna 2026-09-26: tarif elektrik tidak dipilih |
| L1.8.71 | Lampiran I Bil. 8 (butiran 71) | Meneruskan komitmen kelangsungan RM1.2b bekalan elektrik di Sabah dan Wilayah Persekutuan Labuan, antaranya: a) Subsidi bekalan elektrik merangkumi subsidi sokongan tarif, subsidi bahan api dan subsidi solar berskala … | pengguna 2026-09-26: subsidi elektrik Sabah/Labuan tidak dipilih |
| L1.11.4 | Lampiran I Bil. 11 (butiran 4) | Penerusan Program Latihan Industri Untuk RM10j Perusahaan Kecil dan Sederhana (LiKES) oleh TalentCorp menyediakan latihan kepada bakat muda dengan tempoh latihan industri dilanjutkan kepada 12 bulan dan jumlah geran … | pengguna 2026-09-26: LiKES tidak dipilih |
| L1.25.8 | Lampiran I Bil. 25 (butiran 8) | Yayasan Peneraju membangunkan 12,000 RM139j bakat Bumiputera dalam bidang profesional dan teknologi, merintis laluan pensijilan dalam bidang kritikal seperti keselamatan siber, kecerdasan buatan dan Enterprise Resource … | pengguna 2026-09-27: tidak dipilih |
| L1.28.4 | Lampiran I Bil. 28 (butiran 4) | Program 2 Years Exit Program (2YEP) RM2j | pengguna 2026-09-27: tidak dipilih |
| L1.30.5 | Lampiran I Bil. 30 (butiran 5) | Kajian semula skim KWSP bagi - memperkukuh pendekatan pemindahan antara generasi iaitu sebahagian simpanan KWSP ahli boleh dipindahkan terus ke dalam akaun KWSP ahli keluarga terdekat, terutamanya pemindahan simpanan … | pengguna 2026-09-26: kajian pemindahan KWSP dikecualikan (masih dikaji) |
| L1.32.9 | Lampiran I Bil. 32 (butiran 9) | Inisiatif RESET diperkenal bagi menangani RM60j peningkatan kadar inflasi perubatan serta meningkatkan kualiti perkhidmatan kesihatan termasuk: a) Membangunkan produk asas Insurans/Takaful Perubatan dan Kesihatan (Base … | pengguna 2026-09-26: RESET tidak dipilih |
| L1.32.20 | Lampiran I Bil. 32 (butiran 20) | Peruntukan untuk rawatan penyakit jarang RM25j jumpa Nilai | pengguna 2026-09-27: tidak dipilih |
| L1.34.14 | Lampiran I Bil. 34 (butiran 14) | Meneruskan pengedaran topi keledar secara - percuma bagi tujuan keselamatan jalan raya pada tahun 2026 sebanyak 70,000 unit menggunakan sebahagian daripada hasil penjualan nombor plat khas | pengguna 2026-09-27: tidak dipilih |
| L1.35.8 | Lampiran I Bil. 35 (butiran 8) | Program kaum India bagi memperkasa RM100j sosioekonomi komuniti (MITRA) Nilai | pengguna 2026-09-27: tidak dipilih |
| L1.35.16 | Lampiran I Bil. 35 (butiran 16) | Pelaksanaan inisiatif mendaftar skim RM2j perumahan berstrata kos rendah yang belum mempunyai hak milik strata, bagi membantu golongan B40 memiliki dokumen hak milik yang sah Nilai | pengguna 2026-09-26: hak milik strata tidak dipilih |
| L1.40.5 | Lampiran I Bil. 40 (butiran 5) | Pembinaan baru 2,586 Program Perumahan RM150j Penjawat Awam Malaysia MADANI yang sebahagiannya dijangka siap pada penghujung 2026 | pengguna 2026-09-27: tidak dipilih |

#### For non-citizens (5)

| Unit | Source | What the text says | Note |
|---|---|---|---|
| P49.3 | Perenggan 49 (butiran 3) | Investor Pass yang diterajui MIDA menyediakan kemudahan Multiple Entry Visa sehingga 12 bulan kepada pelabur asing. MIDA akan lebih proaktif untuk tidak hanya menunggu permohonan tetapi menawarkan Investor Pass kepada … |  |
| P49.4 | Perenggan 49 (butiran 4) | Residence Pass–Talent Fast Track diteruskan untuk memastikan bakat-bakat yang dibawa masuk oleh pelabur strategik diuruskan secara pantas dan teratur, termasuk mengecualikan syarat Pas Penggajian selama tiga tahun. |  |
| P218 | Perenggan 218 | Kerajaan bercadang mengenakan duti setem pada kadar rata daripada empat kepada lapan peratus ke atas surat cara pindah milik rumah kediaman oleh individu bukan warganegara dan syarikat asing, kecuali individu … | pengguna 2026-09-26: duti setem 8% bukan warganegara; dikecualikan |
| L1.27.11 | Lampiran I Bil. 27 (butiran 11) | Pelaksanaan Program Dokumen RM10j Pendaftaran Pelarian (DPP) serta menaik taraf 3 Depot Tahanan Imigresen dan 3 Baitul Mahabbah untuk dijadikan Pusat Pengasingan Khas Pelarian dan Pemohon Suaka Dewasa dan Kanak-Kanak |  |
| L2.14 | Lampiran II — Lampiran 14 | SEMAKAN SEMULA DUTI SETEM BAGI PEMILIKAN RUMAH KEDIAMAN OLEH BUKAN WARGANEGARA — Kedudukan Semasa Duti setem ke atas surat cara pindah milik harta tanah yang disempurnakan oleh individu bukan warganegara (tidak … | pengguna 2026-09-26: duti setem 8% bukan warganegara; dikecualikan |

#### Already over (6)

| Unit | Source | What the text says | Note |
|---|---|---|---|
| P40.1 | Perenggan 40 (butiran 1) | Pengapungan harga ayam jimat 1 bilion ringgit dan harga ayam terkawal. |  |
| P40.2 | Perenggan 40 (butiran 2) | Pengapungan harga telur menjimatkan 1 bilion ringgit. |  |
| L1.5.2 | Lampiran I Bil. 5 (butiran 2) | Penjimatan daripada pengapungan harga RM1b ayam dan memastikan harga ayam terkawal |  |
| L1.5.3 | Lampiran I Bil. 5 (butiran 3) | Penjimatan pengapungan harga telur RM1b |  |
| L1.29.4 | Lampiran I Bil. 29 (butiran 4) | Bayaran STR Fasa 4 2025 diawalkan dan disalurkan mulai 18 Oktober 2025 sempena Deepavali Nilai Sumbangan Tunai Rahmah & Sumbangan Asas Rahmah bagi Tahun 2026 Tambahan Pendapatan # STR SARA JUMLAH Kategori Bulanan Anak … | STR Fasa 4 2025 diawalkan (Okt 2025) |
| L1.29.6 | Lampiran I Bil. 29 (butiran 6) | Sempena Deepavali, diskaun tol 50% untuk dua - hari akan diberikan | Diskaun tol 50% dua hari sempena Deepavali 2025 |

### 2. Everything else excluded (1018)

Out of scope by design: the brain states what a person gets or pays, never government totals, projects or company incentives. The full text of each unit is in the annotated speech (yellow).

| Reason | Units | Examples |
|---|---|---|
| infrastructure, buildings or public works | 354 | P34, P42.2, P43.3, P45.1, P45.2, P45.3, … |
| a company, investor or employer incentive | 178 | P8, P40, P41, P42, P43.5, P45.31, … |
| law, enforcement, administration or fiscal policy | 150 | P11, P12, P17, P21, P22, P25, … |
| a heading or lead-in with no measure of its own | 94 | P36, P45, P49, P50, P51, P52, … |
| money to an agency, NGO, school or mosque, not to a person | 86 | P85.1, P85.2, P87.2, P87.5, P87.7, P100.2, … |
| speech framing, history or thanks | 82 | P1, P2, P3, P4, P5, P6, … |
| a government spending total or beneficiary count | 74 | P16.1, P16.2, P16.3, P16.4, P16.5, P24, … |

## Appendix: engine code

The complete engine, `belanjawan2026-brain.js` v2026.5, exactly as tested. Copy it unchanged.

````js
/**
 * BELANJAWAN 2026 — OTAK SOAL JAWAB FAEDAH RAKYAT (Citizen Benefits Brain)
 * ------------------------------------------------------------------------
 * UI-free logic module. Plug into any front end (WordPress, React, vanilla).
 *
 *   B26Brain.getVisibleQuestions(answers)   -> questions to show now (branching applied)
 *   B26Brain.pruneAnswers(answers)          -> drop answers to questions that became hidden
 *   B26Brain.evaluate(answers)              -> { strSara, byTheme, results, advisories, counts }
 *
 * Primary source : Ucapan Belanjawan 2026 (MOF). "Perenggan" / "ms" refer to that document.
 * Secondary      : implementation updates found on the web (field `web`).
 * Citizen-facing text: Bahasa Melayu. Code comments: English.
 *
 * Design rules
 *  - Output describes what the PERSON gets or pays; never government allocation totals.
 *  - Personal questions are optional: every non-core question offers "Tidak mahu menyatakan" (value 'skip').
 *  - A skipped single-choice answer becomes UNKNOWN (tri-state), so dependent results show as "mungkin".
 *  - A skipped multi-choice answer is treated as "none selected", with an advisory telling the user.
 *  - Scope: build only the items in BENEFITS. Measures read in the speech and deliberately left
 *    out are listed in references/excluded-2026.md; don't implement them without asking the user.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.B26Brain = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var VERSION = '2026.5';
  var DATA_AS_OF = '2026-09-27';
  var SKIP = 'skip';
  var SKIP_LABEL = 'Tidak mahu menyatakan';

  /* ================================================================
   * 1. QUESTIONS
   *    type: 'number' | 'single' | 'multi'
   *    required: true => no skip option (only age & region)
   *    showIf: condition in the rule DSL (unknown => hidden unless noted)
   * ================================================================ */
  var QUESTIONS = [
    { id: 'age', type: 'number', min: 0, max: 120, required: true,
      text: 'Berapakah umur anda?',
      help: 'Umur menentukan kelayakan program seperti STR, PeKa B40, bantuan warga emas dan pembiayaan rumah untuk golongan muda.' },

    { id: 'region', type: 'single', required: true,
      text: 'Di manakah anda menetap?',
      options: [
        { v: 'semenanjung', l: 'Semenanjung Malaysia' },
        { v: 'sabah', l: 'Sabah' },
        { v: 'sarawak', l: 'Sarawak' },
        { v: 'labuan', l: 'Wilayah Persekutuan Labuan' }
      ] },

    { id: 'self_school', type: 'single',
      showIf: { f: 'age', lt: 18 },
      text: 'Adakah anda murid sekolah Kerajaan?',
      options: [{ v: 'yes', l: 'Ya' }, { v: 'no', l: 'Tidak' }] },

    { id: 'marital', type: 'single',
      showIf: { f: 'age', gte: 18 },
      text: 'Apakah status perkahwinan anda?',
      options: [
        { v: 'married', l: 'Berkahwin' },
        { v: 'single_parent', l: 'Ibu atau bapa tunggal yang mempunyai anak tanggungan' },
        { v: 'single', l: 'Tiada pasangan (belum berkahwin, bercerai atau kematian pasangan)' }
      ] },

    { id: 'children', type: 'single',
      showIf: { f: 'age', gte: 18 },
      text: 'Berapakah bilangan anak tanggungan anda?',
      help: 'Anak berumur bawah 18 tahun, atau anak berumur 18 tahun ke atas yang masih belajar sepenuh masa atau OKU.',
      options: [
        { v: '0', l: 'Tiada' }, { v: '1-2', l: '1 hingga 2 orang' },
        { v: '3-4', l: '3 hingga 4 orang' }, { v: '5+', l: '5 orang atau lebih' }
      ] },

    { id: 'child_stages', type: 'multi',
      showIf: { any: [{ f: 'hasChildren', eq: true }, { f: 'childrenSkipped', eq: true }] },
      text: 'Di peringkat manakah anak anda sekarang? (pilih semua yang berkaitan)',
      options: [
        { v: 'under6', l: 'Belum bersekolah atau prasekolah (bawah 6 tahun)' },
        { v: 'primary', l: 'Sekolah rendah Kerajaan' },
        { v: 'secondary', l: 'Sekolah menengah Kerajaan' },
        { v: 'ipt', l: 'Institusi pengajian tinggi (universiti, politeknik atau kolej)' },
        { v: 'other', l: 'Lain-lain (sudah bekerja, sekolah swasta dan sebagainya)' },
        { v: 'none', l: 'Tiada anak tanggungan', exclusive: true }
      ] },

    { id: 'income', type: 'single',
      showIf: { f: 'age', gte: 18 },
      text: 'Berapakah anggaran pendapatan kasar bulanan isi rumah anda?',
      help: 'Jumlah pendapatan semua ahli isi rumah yang bekerja. Jika anda tinggal seorang diri, masukkan pendapatan anda sendiri.',
      options: [
        { v: 'lt2500', l: 'RM2,500 dan ke bawah' },
        { v: '2501_5000', l: 'RM2,501 hingga RM5,000' },
        { v: '5001_6000', l: 'RM5,001 hingga RM6,000' },
        { v: '6001_12000', l: 'RM6,001 hingga RM12,000' },
        { v: 'gt12000', l: 'Melebihi RM12,000' }
      ] },

    { id: 'ekasih', type: 'single',
      showIf: { all: [{ f: 'age', gte: 18 }, { any: [{ f: 'incomeMax', lte: 5000 }, { f: 'incomeSkipped', eq: true }] }] },
      text: 'Adakah isi rumah anda berdaftar sebagai Miskin atau Miskin Tegar dalam sistem eKasih?',
      options: [{ v: 'yes', l: 'Ya' }, { v: 'no', l: 'Tidak' }, { v: 'unsure', l: 'Tidak pasti' }] },

    { id: 'str_status', type: 'single',
      showIf: { f: 'strEligible', eq: true },
      text: 'Adakah anda sudah menerima Sumbangan Tunai Rahmah (STR) 2026?',
      options: [{ v: 'yes', l: 'Ya, sudah menerima' }, { v: 'no', l: 'Belum menerima atau tidak memohon' }, { v: 'unsure', l: 'Tidak pasti' }] },

    { id: 'employment', type: 'single',
      showIf: { f: 'age', gte: 18 },
      text: 'Apakah status pekerjaan anda sekarang?',
      options: [
        { v: 'employed_private', l: 'Pekerja sektor swasta' },
        { v: 'civil_servant', l: 'Penjawat awam' },
        { v: 'gig_ehailing', l: 'Pemandu e-hailing atau penghantar p-hailing' },
        { v: 'self_employed', l: 'Bekerja sendiri, pekerja bebas atau peniaga kecil' },
        { v: 'fisher', l: 'Nelayan' },
        { v: 'farmer', l: 'Pesawah, petani, penternak atau pekebun kecil' },
        { v: 'housewife', l: 'Suri rumah sepenuh masa' },
        { v: 'student_ipt', l: 'Pelajar institusi pengajian tinggi' },
        { v: 'jobseeker', l: 'Graduan baharu atau sedang mencari pekerjaan' },
        { v: 'retired_gov', l: 'Pesara Kerajaan (berpencen)' },
        { v: 'retired_other', l: 'Bersara atau tidak bekerja' }
      ] },

    { id: 'farm_type', type: 'single',
      showIf: { f: 'employment', eq: 'farmer' },
      text: 'Apakah jenis kegiatan pertanian utama anda?',
      options: [
        { v: 'padi', l: 'Menanam padi' },
        { v: 'smallholder', l: 'Pekebun kecil getah atau sawit' },
        { v: 'other', l: 'Tanaman lain, ternakan atau akuakultur' }
      ] },

    { id: 'gender', type: 'single',
      showIf: { f: 'age', gte: 18 },
      text: 'Apakah jantina anda?',
      help: 'Digunakan untuk memaparkan program khusus wanita seperti i-Suri dan pembiayaan usahawan wanita.',
      options: [{ v: 'female', l: 'Perempuan' }, { v: 'male', l: 'Lelaki' }] },

    { id: 'assets', type: 'multi',
      text: 'Perkara manakah yang berkaitan dengan anda? (pilih semua yang berkaitan)',
      options: [
        { v: 'license', l: 'Mempunyai lesen memandu yang masih sah' },
        { v: 'diesel_vehicle', l: 'Memiliki kenderaan persendirian berenjin diesel' },
        { v: 'old_car', l: 'Memiliki kereta berusia lebih 20 tahun' },
        { v: 'first_home', l: 'Merancang untuk membeli rumah pertama' },
        { v: 'taxpayer', l: 'Membayar cukai pendapatan atau mengisi e-Filing' },
        { v: 'invest_bursa', l: 'Melabur di Bursa Malaysia (saham, ETF atau waran)' },
        { v: 'llp_partner', l: 'Pekongsi dalam Perkongsian Liabiliti Terhad (PLT)' },
        { v: 'ptptn_loan', l: 'Mempunyai pinjaman PTPTN' },
        { v: 'haji_plan', l: 'Merancang untuk menunaikan haji' },
        { v: 'none', l: 'Tiada yang berkaitan', exclusive: true }
      ] },

    { id: 'status', type: 'multi',
      text: 'Adakah mana-mana keadaan ini berkaitan dengan anda? (pilih semua yang berkaitan)',
      options: [
        { v: 'oku_self', l: 'Saya OKU berdaftar' },
        { v: 'oku_child', l: 'Anak saya OKU atau kurang upaya pembelajaran (seperti autisme atau ADHD)' },
        { v: 'pregnant', l: 'Saya atau pasangan sedang hamil' },
        { v: 'veteran', l: 'Veteran Angkatan Tentera Malaysia' },
        { v: 'pjm', l: 'Penerima Pingat Jasa Malaysia' },
        { v: 'religious_staff', l: 'Guru KAFA, guru takmir, imam, bilal, tok siak, noja atau marbut' },
        { v: 'taxi', l: 'Pemandu atau pemilik teksi, termasuk kereta sewa' },
        { v: 'orang_asli', l: 'Orang Asli' },
        { v: 'bankrupt', l: 'Sedang berstatus bankrap' },
        { v: 'none', l: 'Tiada yang berkaitan', exclusive: true }
      ] },

    { id: 'lifestyle', type: 'multi',
      showIf: { f: 'age', gte: 18 },
      text: 'Soalan pilihan: adakah mana-mana perkara ini berkaitan dengan anda?',
      help: 'Belanjawan 2026 menaikkan duti ke atas produk tembakau dan minuman beralkohol, serta mengecualikan cukai ke atas produk bantuan berhenti merokok. Jawapan ini hanya digunakan untuk memaparkan perubahan yang berkaitan.',
      options: [
        { v: 'cigarette', l: 'Merokok' },
        { v: 'cigar', l: 'Menghisap cerut atau cerut kecil (cigarillo)' },
        { v: 'heated_tobacco', l: 'Menggunakan produk tembakau yang dipanaskan (heated tobacco)' },
        { v: 'vape', l: 'Menggunakan vape atau rokok elektronik' },
        { v: 'alcohol', l: 'Mengambil minuman beralkohol' },
        { v: 'none', l: 'Tiada yang berkaitan', exclusive: true }
      ] }
  ];

  // Every non-required question gets a skip option appended.
  QUESTIONS.forEach(function (q) {
    if (q.required || q.type === 'number') return;
    q.options = q.options.concat([{ v: SKIP, l: SKIP_LABEL, exclusive: true, skip: true }]);
  });

  /* ================================================================
   * 2. THEMES & TIERS
   * ================================================================ */
  var THEMES = [
    { id: 'cash',       label: 'Bantuan Tunai & Kos Sara Hidup' },
    { id: 'subsidy',    label: 'Subsidi Bahan Api & Tenaga' },
    { id: 'health',     label: 'Kesihatan & Insurans' },
    { id: 'education',  label: 'Pendidikan' },
    { id: 'housing',    label: 'Perumahan' },
    { id: 'protection', label: 'Perlindungan Sosial & Simpanan Persaraan' },
    { id: 'family',     label: 'Keluarga & Wanita' },
    { id: 'youth',      label: 'Belia, Latihan & Pekerjaan' },
    { id: 'vulnerable', label: 'OKU, Warga Emas & Golongan Rentan' },
    { id: 'sector',     label: 'Mengikut Pekerjaan (Penjawat Awam, Veteran, Nelayan, Petani, Teksi)' },
    { id: 'mobility',   label: 'Pengangkutan & Mobiliti' },
    { id: 'tax',        label: 'Pelepasan Cukai Individu' },
    { id: 'special',    label: 'Kes Khas: Gaya Hidup, Pelaburan & Perubahan Harga' }
  ];

  var TIERS = {
    layak:   { label: 'Berkemungkinan layak', rank: 0 },
    semak:   { label: 'Semak kelayakan',       rank: 1 },
    mungkin: { label: 'Mungkin layak',         rank: 2 },
    kesan:   { label: 'Perubahan yang menjejaskan anda', rank: 3 }
  };

  /* ================================================================
   * 3. FACT DERIVATION
   *    Scalar facts may be null. A null fact is UNKNOWN only if listed in facts._unknown
   *    (user skipped / answered "Tidak pasti"); otherwise it simply doesn't apply (= false).
   * ================================================================ */
  var INCOME_BANDS = {
    lt2500:       { min: 0,     max: 2500 },
    '2501_5000':  { min: 2501,  max: 5000 },
    '5001_6000':  { min: 5001,  max: 6000 },
    '6001_12000': { min: 6001,  max: 12000 },
    gt12000:      { min: 12001, max: Infinity }
  };
  var CHILD_COUNT = { '0': 0, '1-2': 1, '3-4': 3, '5+': 5 };

  function arr(v) { return Array.isArray(v) ? v : (v == null ? [] : [v]); }
  function cleanMulti(v) { return arr(v).filter(function (x) { return x !== 'none' && x !== SKIP; }); }

  function deriveFacts(a) {
    var f = { _unknown: [], _skipped: [] };
    function unknown(name) { if (f._unknown.indexOf(name) === -1) f._unknown.push(name); }
    Object.keys(a).forEach(function (k) { if (arr(a[k]).indexOf(SKIP) > -1) f._skipped.push(k); });

    f.age = (a.age === '' || a.age == null) ? null : Number(a.age);
    f.adult = f.age == null ? null : f.age >= 18;
    f.region = a.region || null;
    f.eastMalaysia = f.region == null ? null : f.region !== 'semenanjung';

    // marital
    if (a.marital === SKIP) { f.marital = null; unknown('marital'); } else f.marital = a.marital || null;

    // children
    f.childrenSkipped = a.children === SKIP;
    if (f.childrenSkipped) { f.childCount = null; f.hasChildren = null; unknown('childCount'); unknown('hasChildren'); }
    else { f.childCount = CHILD_COUNT[a.children || '0']; f.hasChildren = f.childCount > 0; }
    f.childStages = cleanMulti(a.child_stages);
    if (f.childStages.length) f.hasChildren = true;
    f.hasSchoolChild = f.childStages.indexOf('primary') > -1 || f.childStages.indexOf('secondary') > -1;
    f.isSchoolPupil = f.hasSchoolChild || (f.adult === false && a.self_school === 'yes');

    // income
    var band = INCOME_BANDS[a.income];
    f.incomeSkipped = a.income === SKIP;
    f.income = band ? a.income : null;
    f.incomeMin = band ? band.min : null;
    f.incomeMax = band ? band.max : null;
    f.b40 = band ? band.max <= 5000 : null;       // approximation of DOSM B40 line (~RM5,249)
    f.b40m40 = band ? band.max <= 12000 : null;   // approximation of M40 ceiling (~RM11,819)
    if (f.incomeSkipped) ['income', 'incomeMin', 'incomeMax', 'b40', 'b40m40'].forEach(unknown);

    // eKasih
    if (band && band.max > 5000) f.ekasih = false;
    else if (a.ekasih === 'yes') f.ekasih = true;
    else if (a.ekasih === 'no') f.ekasih = false;
    else if (a.ekasih === 'unsure' || a.ekasih === SKIP) { f.ekasih = null; unknown('ekasih'); }
    else if (f.incomeSkipped) { f.ekasih = null; unknown('ekasih'); }
    else f.ekasih = false;

    // employment
    if (a.employment === SKIP) { f.employment = null; unknown('employment'); } else f.employment = a.employment || null;
    if (a.farm_type === SKIP) { f.farmType = null; unknown('farmType'); } else f.farmType = a.farm_type || null;
    if (a.gender === SKIP) { f.gender = null; unknown('gender'); } else f.gender = a.gender || null;

    f.assets = cleanMulti(a.assets);
    f.status = cleanMulti(a.status);
    f.lifestyle = cleanMulti(a.lifestyle);
    f.smoker = ['cigarette', 'cigar', 'heated_tobacco', 'vape'].some(function (x) { return f.lifestyle.indexOf(x) > -1; });

    if (f.childStages.indexOf('ipt') > -1 || f.employment === 'student_ipt') f.ipt = true;
    else if (f.employment === null && a.employment === SKIP) { f.ipt = null; unknown('ipt'); }
    else f.ipt = false;

    if (a.employment === SKIP) { f.kwspMember = null; unknown('kwspMember'); }
    else f.kwspMember = ['employed_private', 'gig_ehailing', 'self_employed', 'housewife', 'jobseeker', 'fisher', 'farmer'].indexOf(f.employment) > -1;

    var s = calcStrSara(f);
    f.strEligible = s.eligible;
    if (s.eligible === null) unknown('strEligible');
    f.strCategory = s.category || null;
    f.strStatus = a.str_status || null;
    return f;
  }

  /* ================================================================
   * 4. STR + SARA CALCULATOR
   *    Source: Ucapan perenggan 158–161 (ms 92–94); Lampiran I Bil. 29 (ms 258–259).
   *    Monthly SARA split confirmed by MOF (BH, Mac 2026).
   * ================================================================ */
  var STR_TABLE = { // [STR setahun, SARA asas setahun]
    lt2500:      { 0: [700, 1200], 1: [1200, 1200], 3: [1700, 1200], 5: [2200, 1200] },
    '2501_5000': { 0: [200, 1200], 1: [450, 1200],  3: [700, 1200],  5: [950, 1200] }
  };
  var EKASIH_TOPUP = { isi_rumah: 1200, warga_emas: 1200, bujang: 600 };
  var SARA_MONTHLY = { isi_rumah: 100, warga_emas: 50, bujang: 50 };
  var CAT_LABEL = { isi_rumah: 'Isi Rumah', warga_emas: 'Warga Emas Tiada Pasangan (60 tahun ke atas)', bujang: 'Bujang (21 hingga 59 tahun)' };

  function calcStrSara(f) {
    function res(eligible, reason, extra) { var o = { eligible: eligible, reason: reason || null }; for (var k in extra) o[k] = extra[k]; return o; }
    if (f.age == null) return res(false, 'Umur belum diisi.');
    if (f.age < 18) return res(false, 'Anda berumur bawah 18 tahun, jadi anda dikira sebagai anak tanggungan dalam permohonan STR ibu bapa anda.');
    if (f.marital === null) return res(null, 'Anda memilih untuk tidak menyatakan status perkahwinan, jadi kategori STR tidak dapat ditentukan. Semak kelayakan di portal MySTR.');
    if (f.income === null) return res(null, 'Anda memilih untuk tidak menyatakan pendapatan, jadi amaun STR tidak dapat dianggarkan. Semak kelayakan di portal MySTR.');

    var cat;
    if (f.marital === 'married' || f.marital === 'single_parent') cat = 'isi_rumah';
    else if (f.childCount === null) return res(null, 'Bilangan anak tidak dinyatakan, jadi kategori STR tidak dapat ditentukan.');
    else if (f.childCount > 0) cat = 'isi_rumah';
    else if (f.age >= 60) cat = 'warga_emas';
    else if (f.age >= 21) cat = 'bujang';
    else return res(false, 'STR kategori Bujang hanya untuk mereka yang berumur 21 hingga 59 tahun.');

    var str, sara, strMin, strMax;
    if (cat === 'isi_rumah') {
      if (!STR_TABLE[f.income]) return res(false, 'STR kategori Isi Rumah untuk isi rumah berpendapatan RM5,000 dan ke bawah sebulan.');
      var t = STR_TABLE[f.income];
      if (f.childCount === null) { strMin = t[0][0]; strMax = t[5][0]; str = strMin; }
      else str = t[f.childCount][0];
      sara = 1200;
    } else if (cat === 'warga_emas') {
      if (!STR_TABLE[f.income]) return res(false, 'STR kategori Warga Emas Tiada Pasangan untuk pendapatan RM5,000 dan ke bawah sebulan.');
      str = 600; sara = 600;
    } else {
      if (f.income !== 'lt2500') return res(false, 'STR kategori Bujang untuk pendapatan RM2,500 dan ke bawah sebulan.');
      str = 0; sara = 600;
    }

    var topup = EKASIH_TOPUP[cat];
    var o = res(true, null, {
      category: cat, label: CAT_LABEL[cat],
      str: str, sara: sara, saraMonthly: SARA_MONTHLY[cat], total: str + sara,
      penghargaanSara: 100, ekasihApplied: 'no'
    });
    if (strMin != null) { o.strRange = [strMin, strMax]; o.totalRange = [strMin + sara, strMax + sara]; }
    if (f.ekasih === true) {
      o.sara += topup; o.saraMonthly += topup / 12; o.total += topup; o.ekasihApplied = 'yes';
      if (o.totalRange) o.totalRange = [o.totalRange[0] + topup, o.totalRange[1] + topup];
    } else if (f.ekasih === null) {
      o.ekasihApplied = 'unknown'; o.totalIfEkasih = o.total + topup; o.saraMonthlyIfEkasih = o.saraMonthly + topup / 12;
    }
    return o;
  }

  /* ================================================================
   * 5. CONDITION DSL + TRI-STATE EVALUATOR
   *    Leaf: { f, <op>: value, why }   ops: eq ne in nin gt gte lt lte has hasAny
   *    Group: { all:[...] } { any:[...] } { not:{...} }
   *    Returns { v: true|false|null, why:[...], unknown:[...] }
   * ================================================================ */
  function test(c, facts) {
    if (c.all) {
      var out = { v: true, why: [], unknown: [] };
      for (var i = 0; i < c.all.length; i++) {
        var r = test(c.all[i], facts);
        if (r.v === false) return { v: false, why: [], unknown: [] };
        if (r.v === null) { out.v = null; out.unknown = out.unknown.concat(r.unknown); }
        out.why = out.why.concat(r.why);
      }
      return out;
    }
    if (c.any) {
      var sawNull = false, unk = [];
      for (var j = 0; j < c.any.length; j++) {
        var r2 = test(c.any[j], facts);
        if (r2.v === true) return { v: true, why: r2.why, unknown: [] };
        if (r2.v === null) { sawNull = true; unk = unk.concat(r2.unknown); }
      }
      return sawNull ? { v: null, why: [], unknown: unk } : { v: false, why: [], unknown: [] };
    }
    if (c.not) {
      var r3 = test(c.not, facts);
      return { v: r3.v === null ? null : !r3.v, why: [], unknown: r3.unknown };
    }
    var val = facts[c.f];
    if (val === null || val === undefined) {
      if (facts._unknown && facts._unknown.indexOf(c.f) > -1) return { v: null, why: [], unknown: [c.why || c.f] };
      return { v: false, why: [], unknown: [] };
    }
    var ok;
    if ('eq' in c) ok = val === c.eq;
    else if ('ne' in c) ok = val !== c.ne;
    else if ('in' in c) ok = c.in.indexOf(val) > -1;
    else if ('nin' in c) ok = c.nin.indexOf(val) === -1;
    else if ('gte' in c) ok = val >= c.gte;
    else if ('gt' in c) ok = val > c.gt;
    else if ('lte' in c) ok = val <= c.lte;
    else if ('lt' in c) ok = val < c.lt;
    else if ('has' in c) ok = arr(val).indexOf(c.has) > -1;
    else if ('hasAny' in c) ok = c.hasAny.some(function (x) { return arr(val).indexOf(x) > -1; });
    else throw new Error('Unknown operator in condition: ' + JSON.stringify(c));
    return { v: ok, why: ok && c.why ? [c.why] : [], unknown: [] };
  }

  /* Reusable conditions */
  var C = {
    adult:     { f: 'age', gte: 18, why: 'Berumur 18 tahun ke atas' },
    b40:       { f: 'b40', eq: true, why: 'Pendapatan isi rumah RM5,000 dan ke bawah' },
    b40m40:    { f: 'b40m40', eq: true, why: 'Pendapatan isi rumah RM12,000 dan ke bawah' },
    str:       { f: 'strEligible', eq: true, why: 'Dianggarkan layak menerima STR 2026' },
    ekasih:    { f: 'ekasih', eq: true, why: 'Berdaftar sebagai Miskin atau Miskin Tegar dalam eKasih' },
    taxpayer:  { f: 'assets', has: 'taxpayer', why: 'Pembayar cukai pendapatan' },
    firstHome: { f: 'assets', has: 'first_home', why: 'Merancang membeli rumah pertama' },
    female:    { f: 'gender', eq: 'female', why: 'Wanita' },
    ipt:       { f: 'ipt', eq: true, why: 'Anda atau anak anda belajar di institusi pengajian tinggi' },
    school:    { f: 'isSchoolPupil', eq: true, why: 'Ada murid sekolah Kerajaan dalam keluarga' },
    okuSelf:   { f: 'status', has: 'oku_self', why: 'OKU berdaftar' },
    okuChild:  { f: 'status', has: 'oku_child', why: 'Anak OKU atau kurang upaya pembelajaran' },
    civil:     { f: 'employment', eq: 'civil_servant', why: 'Penjawat awam' },
    farmer:    { f: 'employment', eq: 'farmer', why: 'Petani atau pekebun' },
    irregular: { f: 'employment', in: ['gig_ehailing', 'self_employed', 'fisher', 'farmer'], why: 'Bekerja sendiri atau berpendapatan tidak tetap' }
  };

  /* ================================================================
   * 6. CATALOGUE
   *   kind: 'manfaat' (benefit) | 'kesan' (a change that costs the person more / new obligation)
   *   certainty: 'high' = rule reflects the real criterion; 'check' = means-tested, quota-based or partly unasked
   *   value/summary describe what the PERSON gets or pays — never government allocation totals.
   * ================================================================ */
  var BENEFITS = [
    /* ---------------- BANTUAN TUNAI & KOS SARA HIDUP ---------------- */
    { id: 'str_sara', theme: 'cash', kind: 'manfaat', compute: 'strSara',
      title: 'Sumbangan Tunai Rahmah (STR) dan Sumbangan Asas Rahmah (SARA)',
      value: 'Dianggarkan berdasarkan jawapan anda',
      summary: 'STR ialah bantuan tunai yang dibayar berperingkat sepanjang tahun. SARA pula ialah kredit bulanan dalam MyKad untuk membeli barangan keperluan asas di kedai yang menyertai program ini.',
      who: 'Isi rumah berpendapatan RM5,000 dan ke bawah; warga emas tiada pasangan berumur 60 tahun ke atas (RM5,000 dan ke bawah); bujang berumur 21 hingga 59 tahun (RM2,500 dan ke bawah).',
      action: 'Mohon atau kemas kini maklumat di portal MySTR. SARA dikreditkan secara automatik ke MyKad penerima STR.',
      when: C.str, certainty: 'high',
      src: 'Perenggan 158–161, ms 92–94; Lampiran I Bil. 29, ms 258–259',
      web: 'https://www.bharian.com.my/amp/berita/nasional/2026/03/1515524/bhplus',
      portal: 'https://bantuantunai.hasil.gov.my' },

    { id: 'penghargaan_sara', theme: 'cash', kind: 'manfaat',
      title: 'Penghargaan SARA', value: 'RM100 (sekali sahaja)',
      summary: 'Kredit SARA ke dalam MyKad untuk semua rakyat Malaysia berumur 18 tahun ke atas, bagi persiapan Ramadan dan Tahun Baru Cina.',
      who: 'Semua warganegara pemegang MyKad berumur 18 tahun ke atas.',
      action: 'Dikreditkan secara automatik ke MyKad.',
      when: C.adult, certainty: 'high',
      timing: 'Telah disalurkan pada pertengahan Februari 2026.',
      src: 'Perenggan 160, ms 93' },

    { id: 'bkk_penjawat', theme: 'cash', kind: 'manfaat',
      title: 'Bantuan Khas Kewangan penjawat awam', value: 'RM500 (sekali sahaja)',
      summary: 'Untuk penjawat awam gred 15 dan ke bawah, termasuk yang dilantik secara kontrak.',
      who: 'Penjawat awam gred 15 dan ke bawah (lantikan tetap atau kontrak).',
      action: 'Dibayar secara automatik bersama gaji.',
      when: C.civil, certainty: 'check',
      timing: 'Telah disalurkan pada awal Mac 2026 sempena Aidilfitri.',
      src: 'Perenggan 246, ms 127' },

    { id: 'bkk_pesara', theme: 'cash', kind: 'manfaat',
      title: 'Bantuan Khas Kewangan pesara dan veteran', value: 'RM250 (sekali sahaja)',
      summary: 'Untuk semua pesara Kerajaan, termasuk veteran yang berpencen dan yang tidak berpencen.',
      who: 'Pesara Kerajaan dan veteran Angkatan Tentera Malaysia.',
      action: 'Dibayar secara automatik.',
      when: { any: [{ f: 'employment', eq: 'retired_gov', why: 'Pesara Kerajaan' }, { f: 'status', has: 'veteran', why: 'Veteran Angkatan Tentera Malaysia' }] },
      certainty: 'high',
      timing: 'Telah disalurkan pada awal Mac 2026.',
      src: 'Perenggan 246, ms 127' },

    { id: 'pjm', theme: 'cash', kind: 'manfaat',
      title: 'Bayaran khas penerima Pingat Jasa Malaysia', value: 'RM500',
      summary: 'Sebagai penghargaan kepada anggota tentera yang menerima Pingat Jasa Malaysia.',
      who: 'Penerima Pingat Jasa Malaysia.',
      action: 'Semak dengan Jabatan Hal Ehwal Veteran (JHEV).',
      when: { f: 'status', has: 'pjm', why: 'Penerima Pingat Jasa Malaysia' }, certainty: 'high',
      src: 'Perenggan 239, ms 125' },

    { id: 'sumbangan_agama', theme: 'cash', kind: 'manfaat',
      title: 'Sumbangan khas guru KAFA dan petugas masjid', value: 'RM500',
      summary: 'Penghargaan kepada guru KAFA, guru takmir, imam, bilal, tok siak, noja dan marbut.',
      who: 'Guru KAFA, guru takmir, imam, bilal, tok siak, noja dan marbut.',
      action: 'Melalui JAKIM atau Majlis Agama Islam Negeri.',
      when: { f: 'status', has: 'religious_staff', why: 'Guru KAFA atau petugas masjid' }, certainty: 'high',
      src: 'Perenggan 247, ms 127' },

    { id: 'jkm_bantuan', theme: 'cash', kind: 'manfaat',
      title: 'Bantuan bulanan Jabatan Kebajikan Masyarakat (JKM)', value: 'Bantuan bulanan mengikut kategori',
      summary: 'Antaranya Bantuan Warga Emas, Bantuan Kanak-kanak, Bantuan OKU Tidak Berupaya Bekerja serta Bantuan Penjagaan OKU dan Pesakit Kronik Terlantar.',
      who: 'Isi rumah miskin, OKU, warga emas dan kanak-kanak yang memerlukan, tertakluk kepada siasatan JKM.',
      action: 'Mohon di Pejabat Kebajikan Masyarakat Daerah atau portal JKM.',
      when: { all: [C.b40, { any: [C.ekasih, { f: 'age', gte: 60, why: 'Berumur 60 tahun ke atas' }, C.okuSelf, C.okuChild,
        { f: 'marital', eq: 'single_parent', why: 'Ibu atau bapa tunggal' }] }] },
      certainty: 'check',
      src: 'Perenggan 162, ms 94; Lampiran I Bil. 29, ms 260', portal: 'https://www.jkm.gov.my' },

    { id: 'rebat_elektrik', theme: 'cash', kind: 'manfaat',
      title: 'Rebat bil elektrik', value: 'Sehingga RM40 sebulan',
      summary: 'Program rebat bil elektrik diteruskan untuk isi rumah miskin tegar.',
      who: 'Isi rumah miskin tegar yang berdaftar dalam eKasih.',
      action: 'Diberikan secara automatik berdasarkan data eKasih.',
      when: C.ekasih, certainty: 'check',
      src: 'Lampiran I Bil. 29, ms 261' },

    { id: 'payung_rahmah', theme: 'cash', kind: 'manfaat',
      title: 'Jualan RAHMAH MADANI', value: 'Barangan keperluan asas pada harga lebih rendah',
      summary: 'Jualan RAHMAH diadakan di semua kawasan DUN, termasuk berhampiran kem tentera dan kuarters polis.',
      who: 'Semua rakyat.',
      action: 'Semak jadual Jualan RAHMAH di kawasan anda (KPDN).',
      when: C.adult, certainty: 'high',
      src: 'Perenggan 163, ms 94; Lampiran I Bil. 29, ms 261' },

    { id: 'harga_sabah_sarawak', theme: 'cash', kind: 'manfaat',
      title: 'Harga barangan asas setara Semenanjung', value: 'Harga barangan asas sama seperti di Semenanjung',
      summary: 'Kerajaan menanggung kos pengangkutan dan pengedaran supaya barangan keperluan asas di Sabah, Sarawak dan Labuan, termasuk kawasan pedalaman, dijual pada harga yang sama dengan Semenanjung Malaysia.',
      who: 'Penduduk Sabah, Sarawak dan Labuan.',
      action: 'Tiada permohonan diperlukan; harga dikawal di kedai yang terlibat.',
      when: { f: 'eastMalaysia', eq: true, why: 'Menetap di Sabah, Sarawak atau Labuan' }, certainty: 'high',
      src: 'Perenggan 164, ms 95; Lampiran I Bil. 29, ms 261' },

    /* ---------------- SUBSIDI BAHAN API & TENAGA ---------------- */
    { id: 'budi95', theme: 'subsidy', kind: 'manfaat',
      title: 'BUDI95: petrol RON95 bersubsidi', value: 'RM1.99 seliter',
      summary: 'Untuk warganegara berumur 16 tahun ke atas yang mempunyai lesen memandu yang sah. Kuota diselaraskan daripada 300 liter kepada 200 liter sebulan mulai 1 April 2026 sebagai langkah sementara.',
      who: 'Warganegara berumur 16 tahun ke atas dengan lesen memandu yang sah.',
      action: 'Imbas MyKad di pam atau kaunter stesen minyak yang terlibat.',
      when: { all: [{ f: 'age', gte: 16, why: 'Berumur 16 tahun ke atas' }, { f: 'assets', has: 'license', why: 'Mempunyai lesen memandu yang sah' }] },
      certainty: 'high',
      timing: 'Kuota 200 liter sebulan berkuat kuasa 1 April 2026. Semak kuota terkini.',
      src: 'Perenggan 40, ms 26–27',
      web: 'https://says.com/my/seismik/budi95-kerajaan-umum-turunkan-kuota-ron95-ke-200-liter-sebulan-bermula-1-april-ini' },

    { id: 'budi95_ehailing', theme: 'subsidy', kind: 'manfaat',
      title: 'Kuota tambahan BUDI95 untuk pemandu e-hailing', value: 'Sehingga 800 liter sebulan',
      summary: 'Kuota bergantung pada jarak perjalanan bulan sebelumnya: kurang daripada 2,000 km kekal pada kuota asas; 2,000 hingga 5,000 km layak 600 liter; lebih daripada 5,000 km layak 800 liter.',
      who: 'Pemandu e-hailing aktif yang mempunyai lesen memandu.',
      action: 'Diberikan secara automatik berdasarkan data syarikat e-hailing.',
      when: { all: [{ f: 'employment', eq: 'gig_ehailing', why: 'Pemandu e-hailing atau penghantar p-hailing' }, { f: 'assets', has: 'license', why: 'Mempunyai lesen memandu yang sah' }] },
      certainty: 'check',
      src: 'Perenggan 40, ms 27',
      web: 'https://says.com/my/berita/pemandu-e-hailing-bawah-2000km-sebulan-tidak-layak-terima-kuota-tambahan-budi95' },

    { id: 'diesel_rm200', theme: 'subsidy', kind: 'manfaat',
      title: 'Bantuan diesel bersasar (BUDI MADANI)', value: 'RM200 sebulan',
      summary: 'Selepas subsidi diesel disasarkan, bantuan RM200 sebulan diberikan kepada pemilik individu kenderaan diesel, petani dan pekebun kecil.',
      who: 'Pemilik individu kenderaan persendirian berenjin diesel, petani dan pekebun kecil di Semenanjung Malaysia, tertakluk kepada syarat BUDI MADANI.',
      action: 'Semak kelayakan dan mohon melalui portal BUDI MADANI.',
      when: { all: [{ f: 'region', eq: 'semenanjung', why: 'Menetap di Semenanjung Malaysia' },
        { any: [{ f: 'assets', has: 'diesel_vehicle', why: 'Memiliki kenderaan diesel' }, C.farmer] }] },
      certainty: 'check',
      src: 'Perenggan 40, ms 26' },

    { id: 'diesel_nelayan', theme: 'subsidy', kind: 'manfaat',
      title: 'Diesel bersubsidi untuk nelayan', value: 'RM1.65 seliter',
      summary: 'Kerajaan mengekalkan harga diesel bersubsidi khusus untuk nelayan.',
      who: 'Nelayan berdaftar.',
      action: 'Melalui Lembaga Kemajuan Ikan Malaysia (LKIM).',
      when: { f: 'employment', eq: 'fisher', why: 'Nelayan' }, certainty: 'high',
      src: 'Perenggan 111, ms 73' },

    { id: 'rebat_cekap_tenaga', theme: 'subsidy', kind: 'manfaat',
      title: 'Rebat pembelian peralatan cekap tenaga (Nur@PETRA)', value: 'Rebat untuk peralatan elektrik cekap tenaga',
      summary: 'Rebat bagi menggalakkan pengguna domestik membeli peralatan elektrik yang cekap tenaga, sekali gus mengurangkan bil elektrik.',
      who: 'Pengguna domestik, tertakluk kepada syarat program.',
      action: 'Pantau pengumuman Kementerian Peralihan Tenaga dan Transformasi Air (PETRA).',
      when: C.adult, certainty: 'check',
      src: 'Lampiran I, ms 222' },

    { id: 'solar_atap', theme: 'subsidy', kind: 'manfaat',
      title: 'Solar ATAP: jana elektrik sendiri di rumah', value: 'Lebihan tenaga boleh dijual sebagai pengimbangan (offset) bil elektrik',
      summary: 'Melalui Solar Accelerated Transition Action Programme (Solar ATAP), pengguna elektrik domestik boleh memasang sistem solar PV untuk kegunaan sendiri dan menjual lebihan tenaga kepada syarikat utiliti sebagai pengimbangan dalam bil elektrik.',
      who: 'Pengguna elektrik domestik yang boleh memasang sistem solar PV.', action: 'Semak syarat penyertaan dengan syarikat utiliti anda.',
      when: C.adult, certainty: 'check',
      src: 'Perenggan 104; Lampiran I Bil. 19' },

    /* ---------------- KESIHATAN & INSURANS ---------------- */
    { id: 'peka_b40', theme: 'health', kind: 'manfaat',
      title: 'PeKa B40', value: 'Saringan kesihatan percuma dan bantuan alat perubatan sehingga RM20,000',
      summary: 'Termasuk insentif RM1,000 untuk melengkapkan rawatan kanser dan bantuan tambang pengangkutan ke hospital (sehingga RM500 di Semenanjung; RM1,000 di Sabah, Sarawak dan Labuan).',
      who: 'Warganegara berumur 40 tahun ke atas yang menerima STR, serta pasangan mereka.',
      action: 'Diberikan secara automatik kepada penerima STR. Bawa MyKad ke klinik panel PeKa B40.',
      when: { all: [{ f: 'age', gte: 40, why: 'Berumur 40 tahun ke atas' }, C.str] }, certainty: 'high',
      src: 'Lampiran I Bil. 32, ms 273',
      web: 'https://www.malaysia.gov.my/my/topics/peka-b40', portal: 'https://www.protecthealth.com.my' },

    { id: 'mysalam', theme: 'health', kind: 'manfaat',
      title: 'mySalam', value: 'RM8,000 jika disahkan menghidap penyakit kritikal, serta RM50 sehari ketika dimasukkan ke wad',
      summary: 'Perlindungan takaful percuma untuk penyakit kritikal dan elaun harian ketika dimasukkan ke wad hospital Kerajaan (sehingga 14 hari setahun). Diteruskan pada tahun 2026.',
      who: 'Penerima STR dan pasangan mereka, tertakluk kepada had umur skim.',
      action: 'Diberikan secara automatik kepada penerima STR. Semak status di portal mySalam.',
      when: { all: [C.adult, C.str] }, certainty: 'high',
      src: 'Perenggan 181, ms 100–101; Lampiran I Bil. 32, ms 269',
      web: 'https://bernama.com/bm/news.php?id=2574921', portal: 'https://www.mysalam.com.my' },

    { id: 'skim_perubatan_madani', theme: 'health', kind: 'manfaat',
      title: 'Skim Perubatan MADANI', value: 'Rawatan di klinik swasta panel: RM250 setahun (keluarga), RM125 (warga emas), RM75 (bujang)',
      summary: 'Untuk rawatan penyakit ringan seperti demam, selesema, batuk dan kecederaan ringan.',
      who: 'Isi rumah penerima STR, termasuk anak berumur bawah 18 tahun.',
      action: 'Diberikan secara automatik kepada penerima STR. Bawa MyKad ke klinik panel.',
      when: C.str, certainty: 'high',
      src: 'Lampiran I Bil. 32, ms 272',
      web: 'https://ringgitplus.com/ms/blog/sudut-pakar/str-cara-dapatkan-perlindungan-perubatan-percuma-jika-pendapatan-isi-rumah-anda-di-bawah-rm5000.html' },

    { id: 'tdap_ibu', theme: 'health', kind: 'manfaat',
      title: 'Vaksin Tdap percuma untuk ibu hamil', value: 'Suntikan vaksin percuma',
      summary: 'Melindungi bayi daripada jangkitan batuk kokol (pertusis) yang serius.',
      who: 'Ibu hamil.',
      action: 'Dapatkan di klinik kesihatan Kerajaan semasa pemeriksaan kehamilan.',
      when: { f: 'status', has: 'pregnant', why: 'Anda atau pasangan sedang hamil' }, certainty: 'high',
      src: 'Lampiran I Bil. 26, ms 250' },

    { id: 'saringan_wanita', theme: 'health', kind: 'manfaat',
      title: 'Ujian mamogram dan saringan kanser serviks bersubsidi', value: 'Ujian saringan pada kos lebih rendah',
      summary: 'Subsidi untuk ujian mamogram (kanser payudara) dan saringan kanser serviks.',
      who: 'Wanita, tertakluk kepada syarat umur dan pendapatan program LPPKN atau KKM.',
      action: 'Semak dengan LPPKN atau klinik kesihatan berhampiran.',
      when: { all: [C.female, { f: 'age', gte: 20, why: 'Berumur 20 tahun ke atas' }] }, certainty: 'check',
      src: 'Lampiran I Bil. 26, ms 247' },

    { id: 'mhit_kwsp', theme: 'health', kind: 'manfaat',
      title: 'Akaun Sejahtera KWSP boleh digunakan untuk insurans perubatan asas', value: 'Bayar premium menggunakan simpanan KWSP',
      summary: 'Pencarum boleh menggunakan simpanan Akaun Sejahtera untuk melanggan pelan asas insurans atau takaful perubatan dan kesihatan melalui platform i-Lindung.',
      who: 'Ahli KWSP.',
      action: 'Melalui i-Lindung dalam aplikasi KWSP i-Akaun.',
      when: { f: 'kwspMember', eq: true, why: 'Ahli KWSP' }, certainty: 'high',
      src: 'Perenggan 181, ms 100; Lampiran I Bil. 32, ms 269', portal: 'https://www.kwsp.gov.my' },

    { id: 'duti_insurans_kecil', theme: 'health', kind: 'manfaat',
      title: 'Tiada duti setem untuk polisi insurans bernilai kecil', value: 'Dikecualikan duti setem sehingga 2028',
      summary: 'Polisi insurans atau takaful dengan premium tahunan RM150 dan ke bawah (seperti insurans kebakaran, perjalanan dan kemalangan diri) serta produk Perlindungan Tenang.',
      who: 'Semua individu yang membeli polisi tersebut.',
      action: 'Diberikan secara automatik semasa membeli polisi.',
      when: C.adult, certainty: 'high',
      src: 'Perenggan 181, ms 100; Lampiran II — Lampiran 16 dan 17, ms 332–333' },

    { id: 'perkeso_dialisis', theme: 'health', kind: 'manfaat',
      title: 'Kadar bayaran rawatan hemodialisis PERKESO dinaikkan', value: 'Sehingga RM170 bagi setiap rawatan (sebelum ini RM150)',
      summary: 'PERKESO menaikkan kadar maksimum yang dibayar bagi setiap rawatan hemodialisis.',
      who: 'Pencarum PERKESO yang menerima rawatan hemodialisis.', action: 'Semak kelayakan dengan PERKESO.',
      when: { f: 'employment', in: ['employed_private', 'gig_ehailing', 'self_employed'], why: 'Pekerja yang dilindungi PERKESO' }, certainty: 'check',
      src: 'Perenggan 170; Lampiran I Bil. 30' },

    /* ---------------- PENDIDIKAN ---------------- */
    { id: 'bap', theme: 'education', kind: 'manfaat',
      title: 'Bantuan Awal Persekolahan', value: 'RM150 bagi setiap murid',
      summary: 'Untuk semua murid sekolah Kerajaan. Mulai 2026, bantuan disalurkan di sekolah melalui guru kepada ibu bapa.',
      who: 'Semua murid sekolah Kerajaan.',
      action: 'Diterima di sekolah tanpa perlu memohon.',
      when: C.school, certainty: 'high',
      src: 'Perenggan 192, ms 106' },

    { id: 'bantuan_am', theme: 'education', kind: 'manfaat',
      title: 'Bantuan Am Persekolahan', value: 'Kini diberikan sehingga Tingkatan 5',
      summary: 'Sebelum ini hanya sehingga Tingkatan 3. Kini diperluas kepada murid miskin sehingga Tingkatan 5.',
      who: 'Murid daripada keluarga miskin.',
      action: 'Melalui sekolah.',
      when: { all: [C.school, { any: [C.ekasih, { f: 'income', eq: 'lt2500', why: 'Pendapatan isi rumah RM2,500 dan ke bawah' }] }] },
      certainty: 'check', src: 'Perenggan 192, ms 106' },

    { id: 'rmt_biasiswa', theme: 'education', kind: 'manfaat',
      title: 'Rancangan Makanan Tambahan dan Biasiswa Kecil Persekutuan', value: 'Makanan berkhasiat percuma dan biasiswa',
      summary: 'Makanan berkhasiat di sekolah serta biasiswa untuk murid daripada keluarga berpendapatan rendah.',
      who: 'Murid daripada keluarga berpendapatan rendah, dipilih oleh pihak sekolah.',
      action: 'Melalui sekolah.',
      when: { all: [C.school, C.b40] }, certainty: 'check',
      src: 'Perenggan 192, ms 105' },

    { id: 'tuisyen_madani', theme: 'education', kind: 'manfaat',
      title: 'Tuisyen MADANI percuma', value: 'Kelas tuisyen percuma',
      summary: 'Disediakan di sekolah yang menyertai program Sekolah Angkat MADANI.',
      who: 'Murid di sekolah yang menyertai program Sekolah Angkat MADANI.',
      action: 'Semak dengan pihak sekolah.',
      when: { all: [C.school, C.b40] }, certainty: 'check',
      src: 'Perenggan 43, ms 28; Lampiran I, ms 143' },

    { id: 'elaun_mbk', theme: 'education', kind: 'manfaat',
      title: 'Elaun Murid Berkeperluan Khas', value: 'RM150 sebulan',
      summary: 'Untuk semua murid OKU di sekolah Kerajaan.',
      who: 'Murid OKU berdaftar di sekolah Kerajaan.',
      action: 'Melalui sekolah. Murid perlu berdaftar sebagai OKU dengan JKM.',
      when: { all: [C.school, { any: [C.okuChild, { all: [C.okuSelf, { f: 'age', lt: 18 }] }] }] }, certainty: 'high',
      src: 'Perenggan 194, ms 107' },

    { id: 'autisme', theme: 'education', kind: 'manfaat',
      title: 'Sokongan untuk anak autisme', value: 'Kelas khas dan bantuan yuran pembelajaran',
      summary: 'Kelas Tunas Istimewa di TABIKA KEMAS untuk kanak-kanak autisme ringan, Pusat Perkhidmatan Autisme kini diperluas ke Labuan, Sabah dan Sarawak, serta Bantuan Yuran Pembelajaran Anak Autisme.',
      who: 'Ibu bapa kepada anak autisme.',
      action: 'Hubungi TABIKA KEMAS atau Pejabat Kebajikan Masyarakat Daerah.',
      when: C.okuChild, certainty: 'check',
      src: 'Perenggan 149 dan 194, ms 87–88, 107; Lampiran I Bil. 29, ms 260' },

    { id: 'ptptn_percuma', theme: 'education', kind: 'manfaat',
      title: 'Pendidikan Percuma PTPTN', value: 'Pengajian percuma di IPTA',
      summary: 'Untuk anak keluarga miskin dan miskin tegar (berdasarkan data eKasih) yang belajar di institusi pengajian tinggi awam.',
      who: 'Pelajar IPTA daripada keluarga miskin atau miskin tegar dalam eKasih.',
      action: 'Mohon melalui PTPTN.',
      when: { all: [C.ipt, C.ekasih] }, certainty: 'check',
      src: 'Perenggan 202, ms 109; Lampiran I Bil. 33, ms 280', portal: 'https://www.ptptn.gov.my' },

    { id: 'ptptn_kelas_pertama', theme: 'education', kind: 'manfaat',
      title: 'Pengecualian bayaran balik PTPTN untuk Kelas Pertama', value: 'Tidak perlu membayar balik pinjaman',
      summary: 'Untuk peminjam daripada keluarga berpendapatan rendah dan sederhana yang memperoleh Ijazah Sarjana Muda Kepujian Kelas Pertama di IPTA.',
      who: 'Peminjam PTPTN di IPTA (B40 atau M40) yang lulus dengan Kelas Pertama.',
      action: 'Mohon pengecualian melalui PTPTN selepas bergraduat.',
      when: { all: [C.ipt, C.b40m40] }, certainty: 'check',
      src: 'Perenggan 202, ms 109', portal: 'https://www.ptptn.gov.my' },

    { id: 'gapai', theme: 'education', kind: 'manfaat',
      title: 'Geran Padanan Ihsan (GAPAI) SSPN', value: 'Geran sehingga RM5,000',
      summary: 'Geran padanan atas simpanan SSPN untuk pelajar yang melanjutkan pengajian ke IPTA.',
      who: 'Keluarga berpendapatan sehingga RM6,000 sebulan yang mempunyai anak di IPTA.',
      action: 'Melalui akaun SSPN (PTPTN).',
      when: { all: [C.ipt, { f: 'incomeMax', lte: 6000, why: 'Pendapatan isi rumah RM6,000 dan ke bawah' }] }, certainty: 'check',
      src: 'Lampiran I Bil. 33, ms 280', portal: 'https://www.ptptn.gov.my' },

    { id: 'dapur_madani', theme: 'education', kind: 'manfaat',
      title: 'Ikhtiar Dapur MADANI', value: 'Bantuan makanan dan peralatan memasak',
      summary: 'Bantuan makanan dan bahan mentah untuk mahasiswa berpendapatan rendah di universiti awam dan politeknik.',
      who: 'Mahasiswa B40 di universiti awam dan politeknik.',
      action: 'Melalui Bahagian Hal Ehwal Pelajar universiti atau politeknik.',
      when: { all: [{ f: 'employment', eq: 'student_ipt', why: 'Pelajar institusi pengajian tinggi' }, C.b40] }, certainty: 'high',
      src: 'Perenggan 200, ms 108' },

    { id: 'job_on_campus', theme: 'education', kind: 'manfaat',
      title: 'MySiswa Job on Campus', value: 'Kerja sambilan di dalam kampus',
      summary: 'Peluang menjana pendapatan sambil belajar dan mengasah kemahiran keusahawanan.',
      who: 'Mahasiswa B40 dan M40.',
      action: 'Melalui universiti.',
      when: { all: [{ f: 'employment', eq: 'student_ipt', why: 'Pelajar institusi pengajian tinggi' }, C.b40m40] }, certainty: 'check',
      src: 'Perenggan 200, ms 108' },

    { id: 'celik_madani', theme: 'education', kind: 'manfaat',
      title: 'Program Celik MADANI (PNB)', value: 'Pelaburan permulaan RM50 dalam ASB atau ASM',
      summary: 'Pelajar terpilih menerima pelaburan permulaan dalam ASB atau ASM bagi memupuk budaya menyimpan.',
      who: 'Pelajar terpilih.',
      action: 'Pantau pengumuman PNB.',
      when: { any: [C.school, C.ipt] }, certainty: 'check',
      src: 'Perenggan 199, ms 108' },

    { id: 'tahfiz_kemahiran', theme: 'education', kind: 'manfaat',
      title: 'Latihan kemahiran dan teknologi untuk pelajar tahfiz dan pondok', value: 'Kursus teknologi digital dan AI serta latihan kemahiran profesional',
      summary: 'Pelajar tahfiz dan pondok didedahkan kepada teknologi digital dan AI melalui Program IPT@Komuniti oleh Majlis TVET Negara. Pelajar tahfiz juga dibekalkan latihan kemahiran profesional melalui GiatMARA untuk dimanfaatkan selepas tamat pengajian.',
      who: 'Pelajar sekolah tahfiz dan pondok.', action: 'Tanya pihak sekolah tahfiz atau pondok, atau pusat GiatMARA berhampiran.',
      when: { all: [{ f: 'age', gte: 15, why: 'Berumur 15 hingga 30 tahun' }, { f: 'age', lte: 30 },
        { any: [{ f: 'employment', eq: 'student_ipt', why: 'Pelajar' },
          { all: [{ f: 'adult', eq: false }, { f: 'isSchoolPupil', eq: true, why: 'Pelajar sekolah' }] }] }] },
      certainty: 'check',
      src: 'Perenggan 65, 223; Lampiran I Bil. 11' },

    /* ---------------- PERUMAHAN ---------------- */
    { id: 'duti_rumah_pertama', theme: 'housing', kind: 'manfaat',
      title: 'Tiada duti setem untuk rumah pertama', value: 'Pengecualian penuh bagi rumah berharga sehingga RM500,000',
      summary: 'Pengecualian duti setem ke atas surat cara pindah milik dan perjanjian pinjaman, bagi perjanjian jual beli yang ditandatangani dari 1 Januari 2026 hingga 31 Disember 2027.',
      who: 'Warganegara yang membeli rumah kediaman pertama berharga RM500,000 dan ke bawah.',
      action: 'Dituntut semasa urusan penyeteman dokumen (melalui peguam atau LHDN).',
      when: C.firstHome, certainty: 'high',
      src: 'Perenggan 217, ms 116; Lampiran II — Lampiran 15, ms 331' },

    { id: 'sjkp_akses', theme: 'housing', kind: 'manfaat',
      title: 'SJKP MADANI: Akses Pemilikan Rumah Mampu Milik', value: 'Jaminan pinjaman sehingga 120%, had RM360,000',
      summary: 'Jaminan Kerajaan untuk pembeli rumah pertama yang tidak mempunyai slip gaji tetap. Fi jaminan 0.25%.',
      who: 'Pembeli rumah pertama B40 dan M40, termasuk pekerja gig, pekerja bebas, bekerja sendiri dan usahawan mikro.',
      action: 'Mohon melalui bank yang menyertai SJKP.',
      when: { all: [C.firstHome, C.b40m40] }, certainty: 'check',
      src: 'Perenggan 216, ms 115; Lampiran I Bil. 35, ms 293–294' },

    { id: 'sjkp_inklusif', theme: 'housing', kind: 'manfaat',
      title: 'SJKP: Pembiayaan Rumah Inklusif', value: 'Jaminan pinjaman sehingga 110%, had RM500,000',
      summary: 'Untuk pembeli rumah pertama yang berpendapatan tidak tetap. Fi jaminan 0.25% (pinjaman sehingga RM300,000) atau 0.50% (RM300,000 hingga RM500,000).',
      who: 'Pembeli rumah pertama berpendapatan tidak tetap, golongan belia dan kakitangan kontrak perkhidmatan awam.',
      action: 'Mohon melalui bank yang menyertai SJKP.',
      when: { all: [C.firstHome, { any: [C.irregular, C.civil, { f: 'age', lte: 35, why: 'Berumur 35 tahun dan ke bawah' }] }] },
      certainty: 'check',
      src: 'Lampiran I Bil. 35, ms 293–294' },

    { id: 'step_up', theme: 'housing', kind: 'manfaat',
      title: 'Step-Up Financing', value: 'Ansuran bulanan lebih rendah pada lima tahun pertama',
      summary: 'Jaminan Kerajaan untuk golongan muda membeli rumah pertama dengan bayaran balik yang lebih rendah pada lima tahun pertama.',
      who: 'Pembeli rumah pertama berumur 21 hingga 35 tahun.',
      action: 'Mohon melalui bank yang menyertai SJKP.',
      when: { all: [C.firstHome, { f: 'age', gte: 21, why: 'Berumur 21 hingga 35 tahun' }, { f: 'age', lte: 35 }] },
      certainty: 'high',
      src: 'Lampiran I Bil. 26, ms 249; Bil. 35, ms 294' },

    { id: 'rumah_kontrak_awam', theme: 'housing', kind: 'manfaat',
      title: 'Pinjaman rumah pertama untuk kakitangan kontrak Kerajaan', value: 'Jaminan pinjaman sehingga 120%',
      summary: 'SJKP menjamin pinjaman sehingga 120% dan BSN menyediakan pembiayaan khas, termasuk untuk guru TABIKA dan TASKA KEMAS.',
      who: 'Penjawat awam lantikan kontrak yang membeli rumah pertama.',
      action: 'Mohon melalui BSN atau bank yang menyertai SJKP.',
      when: { all: [C.firstHome, C.civil] }, certainty: 'check',
      src: 'Perenggan 237, ms 124' },

    { id: 'lppsa', theme: 'housing', kind: 'manfaat',
      title: 'Pembiayaan perumahan LPPSA', value: 'Had pembiayaan dinaikkan kepada RM1 juta',
      summary: 'Pembiayaan kali kedua dipermudah mulai suku keempat 2026. Skim Pembiayaan Perumahan Muda (bawah 30 tahun) dilanjutkan hingga 31 Disember 2026.',
      who: 'Penjawat awam lantikan tetap.',
      action: 'Mohon melalui portal LPPSA.',
      when: C.civil, certainty: 'check',
      timing: 'Skim Pembiayaan Perumahan Muda tamat pada 31 Disember 2026.',
      src: 'Perenggan 237, ms 125' },

    { id: 'rumah_mampu_milik', theme: 'housing', kind: 'manfaat',
      title: 'Rumah mampu milik Kerajaan (PRR, RMR, Residensi MADANI, PR1MA)', value: 'Peluang memiliki rumah mampu milik',
      summary: 'Beberapa projek Program Residensi Rakyat, Rumah Mesra Rakyat, Residensi MADANI dan PR1MA dijangka siap pada tahun 2026.',
      who: 'Isi rumah B40 dan M40 yang belum memiliki rumah.',
      action: 'Daftar melalui portal perumahan KPKT, PR1MA atau kerajaan negeri.',
      when: { all: [C.firstHome, C.b40m40] }, certainty: 'check',
      src: 'Perenggan 216, ms 115; Lampiran I Bil. 35, ms 289' },

    { id: 'rumah_daif', theme: 'housing', kind: 'manfaat',
      title: 'Baik pulih atau bina semula rumah daif', value: 'Rumah dibaiki atau dibina semula',
      summary: 'Termasuk rumah nelayan, melalui Program Perumahan Rakyat Sejahtera, Program Pembasmian Kemiskinan Bandar dan Bantuan Rumah Nelayan Laut B40.',
      who: 'Isi rumah miskin dalam eKasih dan nelayan B40 yang tinggal di rumah daif.',
      action: 'Mohon melalui Pejabat Daerah, KPKT atau Jabatan Perikanan.',
      when: { any: [C.ekasih, { all: [{ f: 'employment', eq: 'fisher', why: 'Nelayan' }, C.b40] }] }, certainty: 'check',
      src: 'Perenggan 216, ms 115; Lampiran I Bil. 35, ms 290' },

    { id: 'kota_madani', theme: 'housing', kind: 'manfaat',
      title: 'Rumah di Kota MADANI Presint 19', value: '80% daripada rumah dikhaskan untuk penjawat awam',
      summary: 'Kota MADANI Presint 19 ialah bandar pintar dan hijau yang menyediakan rumah kediaman, kebanyakannya untuk penjawat awam.',
      who: 'Penjawat awam.', action: 'Pantau pengumuman permohonan.',
      when: C.civil, certainty: 'check',
      src: 'Perenggan 214' },

    /* ---------------- PERLINDUNGAN SOSIAL & SIMPANAN PERSARAAN ---------------- */
    { id: 'i_saraan', theme: 'protection', kind: 'manfaat',
      title: 'i-Saraan KWSP', value: 'Padanan 20% caruman, sehingga RM500 setahun (RM5,000 seumur hidup)',
      summary: 'Kerajaan memadankan caruman sukarela KWSP bagi mereka yang bekerja sendiri atau berpendapatan tidak tetap.',
      who: 'Mereka yang bekerja sendiri atau berpendapatan tidak tetap, berumur bawah 60 tahun.',
      action: 'Daftar melalui KWSP i-Akaun dan mula mencarum.',
      when: { all: [{ f: 'employment', in: ['self_employed', 'fisher', 'farmer'], why: 'Bekerja sendiri atau berpendapatan tidak tetap' }, { f: 'age', lt: 60, why: 'Berumur bawah 60 tahun' }] },
      certainty: 'high',
      src: 'Perenggan 165, ms 95; Lampiran I Bil. 30, ms 262', portal: 'https://www.kwsp.gov.my' },

    { id: 'i_saraan_plus', theme: 'protection', kind: 'manfaat',
      title: 'i-Saraan Plus (baharu)', value: 'Padanan 20% caruman, sehingga RM600 setahun (RM6,000 seumur hidup)',
      summary: 'Insentif padanan khas untuk pemandu e-hailing dan penghantar p-hailing sepenuh masa.',
      who: 'Pemandu e-hailing dan penghantar p-hailing sepenuh masa, berumur bawah 60 tahun.',
      action: 'Daftar melalui KWSP i-Akaun.',
      when: { all: [{ f: 'employment', eq: 'gig_ehailing', why: 'Pemandu e-hailing atau penghantar p-hailing' }, { f: 'age', lt: 60, why: 'Berumur bawah 60 tahun' }] },
      certainty: 'high',
      src: 'Perenggan 165, ms 95; Lampiran I Bil. 30, ms 262', portal: 'https://www.kwsp.gov.my' },

    { id: 'i_suri', theme: 'protection', kind: 'manfaat',
      title: 'i-Suri KWSP', value: 'Padanan 50% caruman, sehingga RM300 setahun (RM3,000 seumur hidup)',
      summary: 'Had umur kelayakan dinaikkan kepada 60 tahun, selaras dengan umur persaraan minimum.',
      who: 'Suri rumah berumur bawah 60 tahun yang berdaftar dalam eKasih.',
      action: 'Daftar di kaunter KWSP atau melalui i-Akaun.',
      when: { all: [C.female, { f: 'employment', eq: 'housewife', why: 'Suri rumah' }, { f: 'age', lt: 60, why: 'Berumur bawah 60 tahun' }, C.ekasih] },
      certainty: 'high',
      src: 'Perenggan 168, ms 95; Lampiran I Bil. 30, ms 262–263',
      web: 'https://www.kosmo.com.my/?p=736588', portal: 'https://www.kwsp.gov.my' },

    { id: 'lindung_kendiri', theme: 'protection', kind: 'manfaat',
      title: 'PERKESO Lindung Kendiri', value: 'Kerajaan menanggung 70% caruman bagi tahun pertama dan 50% bagi tahun kedua',
      summary: 'Perlindungan kemalangan dan hilang upaya ketika bekerja untuk pekerja gig dan mereka yang bekerja sendiri dalam sektor yang belum diwajibkan, bagi pendaftaran kali pertama.',
      who: 'Pekerja gig dan mereka yang bekerja sendiri yang mendaftar buat kali pertama.',
      action: 'Daftar melalui portal PERKESO.',
      when: C.irregular, certainty: 'check',
      src: 'Perenggan 166, ms 95; Lampiran I Bil. 30, ms 263', portal: 'https://www.perkeso.gov.my' },

    { id: 'perkeso_pindah', theme: 'protection', kind: 'manfaat',
      title: 'Insentif berpindah tempat kerja (PERKESO)', value: 'Sehingga RM1,000',
      summary: 'Untuk pencari kerja atau graduan baharu yang menerima tawaran kerja yang memerlukan mereka berpindah ke lokasi lain.',
      who: 'Pencari kerja dan graduan baharu.',
      action: 'Mohon melalui PERKESO (MYFutureJobs).',
      when: { f: 'employment', eq: 'jobseeker', why: 'Sedang mencari pekerjaan' }, certainty: 'check',
      src: 'Perenggan 167, ms 95', portal: 'https://www.perkeso.gov.my' },

    { id: 'kwsp_auto', theme: 'protection', kind: 'manfaat',
      title: 'Akaun KWSP dibuka secara automatik pada umur 18 tahun', value: 'Akaun dibuka secara automatik',
      summary: 'Semua warganegara Malaysia akan didaftarkan sebagai ahli KWSP secara automatik apabila mencapai umur 18 tahun.',
      who: 'Warganegara yang mencapai umur 18 tahun.',
      action: 'Tiada tindakan diperlukan.',
      when: { all: [{ f: 'age', gte: 17, why: 'Berumur 17 hingga 19 tahun' }, { f: 'age', lte: 19 }] }, certainty: 'high',
      src: 'Lampiran I Bil. 30, ms 264' },

    { id: 'kwsp_haji', theme: 'protection', kind: 'manfaat',
      title: 'Pengeluaran KWSP untuk menunaikan haji', value: 'Had pengeluaran dinaikkan kepada RM10,000 (sebelum ini RM3,000)',
      summary: 'Ahli KWSP boleh mengeluarkan simpanan yang lebih tinggi untuk menampung kos menunaikan haji.',
      who: 'Ahli KWSP yang akan menunaikan haji.',
      action: 'Mohon pengeluaran melalui KWSP.',
      when: { all: [{ f: 'assets', has: 'haji_plan', why: 'Merancang untuk menunaikan haji' }, { f: 'kwspMember', eq: true, why: 'Ahli KWSP' }] },
      certainty: 'high',
      src: 'Perenggan 228, ms 120; Lampiran I, ms 296', portal: 'https://www.kwsp.gov.my' },

    { id: 'gcr_haji', theme: 'protection', kind: 'manfaat',
      title: 'Penebusan awal GCR untuk menunaikan haji', value: 'Penebusan sehingga RM10,000',
      summary: 'Penjawat awam boleh menebus Gantian Cuti Rehat (GCR) lebih awal untuk menunaikan haji.',
      who: 'Penjawat awam yang akan menunaikan haji.',
      action: 'Mohon melalui jabatan masing-masing.',
      when: { all: [{ f: 'assets', has: 'haji_plan', why: 'Merancang untuk menunaikan haji' }, C.civil] }, certainty: 'check',
      src: 'Perenggan 228, ms 120' },

    /* ---------------- KELUARGA & WANITA ---------------- */
    { id: 'kasihnita', theme: 'family', kind: 'manfaat',
      title: 'KasihnITA: bantuan guaman untuk ibu tunggal', value: 'Bantuan guaman',
      summary: 'Membantu ibu tunggal berpendapatan rendah dalam kes mahkamah seperti perceraian dan hak penjagaan anak.',
      who: 'Ibu tunggal berpendapatan rendah.',
      action: 'Mohon melalui Jabatan Pembangunan Wanita (KPWKM).',
      when: { all: [C.female, { f: 'marital', eq: 'single_parent', why: 'Ibu tunggal' }, C.b40] }, certainty: 'check',
      src: 'Perenggan 142, ms 85; Lampiran I Bil. 26, ms 247' },

    { id: 'pembiayaan_wanita', theme: 'family', kind: 'manfaat',
      title: 'Pembiayaan untuk usahawan wanita', value: 'Pembiayaan daripada RM30,000 hingga RM3 juta',
      summary: 'AIM Skim Paduri MADANI (sehingga RM30,000), BSN Mikro MADANI Wanita (sehingga RM100,000 pada kadar 4%), MARA DANANITA (sehingga RM150,000 pada kadar 3.5%, untuk Bumiputera), SME Bank MySMELady 2.0 (sehingga RM3 juta) dan Bank Rakyat BizLady.',
      who: 'Usahawan wanita, daripada perniagaan mikro hingga PMKS.',
      action: 'Mohon terus kepada AIM, BSN, MARA, SME Bank atau Bank Rakyat.',
      when: { all: [C.female, { f: 'employment', in: ['self_employed', 'gig_ehailing', 'housewife', 'farmer', 'fisher'], why: 'Berniaga atau bekerja sendiri' }] },
      certainty: 'check',
      src: 'Perenggan 142, ms 84; Lampiran I Bil. 26, ms 247, 251–252' },

    { id: 'subsidi_taska', theme: 'family', kind: 'manfaat',
      title: 'Subsidi yuran taska', value: 'Yuran taska lebih rendah',
      summary: 'Subsidi yuran di taska institusi (mengikut pendapatan) dan taska komuniti untuk keluarga berpendapatan RM5,000 dan ke bawah.',
      who: 'Ibu bapa yang menghantar anak ke taska, berpendapatan RM5,000 dan ke bawah.',
      action: 'Mohon melalui taska atau JKM.',
      when: { all: [{ f: 'childStages', has: 'under6', why: 'Ada anak bawah 6 tahun' }, C.b40] }, certainty: 'check',
      src: 'Lampiran I Bil. 26, ms 250' },

    { id: 'buai', theme: 'family', kind: 'manfaat',
      title: 'Bantuan Rawatan Kesuburan (BuAI)', value: 'Bantuan kos rawatan kesuburan',
      summary: 'Bantuan untuk pasangan yang memerlukan rawatan bagi mendapatkan zuriat.',
      who: 'Pasangan suami isteri yang memerlukan rawatan kesuburan, tertakluk kepada syarat LPPKN.',
      action: 'Mohon melalui LPPKN.',
      when: { all: [{ f: 'marital', eq: 'married', why: 'Berkahwin' }, { f: 'age', gte: 21, why: 'Berumur 21 hingga 49 tahun' }, { f: 'age', lte: 49 }] },
      certainty: 'check',
      src: 'Lampiran I Bil. 26, ms 250' },

    /* ---------------- BELIA, LATIHAN & PEKERJAAN ---------------- */
    { id: 'mylesen_b2', theme: 'youth', kind: 'manfaat',
      title: 'MyLesen B2', value: 'Lesen motosikal B2 secara percuma atau bersubsidi',
      summary: 'Diperluas kepada pelajar sekolah menengah, penuntut institusi pengajian tinggi dan belia daripada keluarga kurang berkemampuan.',
      who: 'Mereka yang berumur 16 tahun ke atas daripada keluarga B40 dan belum mempunyai lesen.',
      action: 'Mohon melalui JPJ negeri atau pihak sekolah.',
      when: { all: [{ f: 'age', gte: 16, why: 'Berumur 16 tahun ke atas' }, { not: { f: 'assets', has: 'license' } },
        { any: [C.b40, { f: 'age', lt: 18, why: 'Pelajar sekolah' }] }] },
      certainty: 'check',
      timing: 'Pelaksanaan bagi 2026 disasarkan selesai pada Julai 2026. Semak pengambilan seterusnya.',
      src: 'Perenggan 143, ms 86; Lampiran I Bil. 26, ms 249', web: 'https://bernama.com/en/news.php?id=2569073' },

    { id: 'plkn', theme: 'youth', kind: 'manfaat',
      title: 'Program Latihan Khidmat Negara (PLKN) 2026', value: 'Latihan jati diri dan kenegaraan',
      summary: 'Membina jati diri, semangat kenegaraan dan kesukarelawanan. Dirintis di institusi pengajian tinggi sebelum dilaksanakan sepenuhnya pada 2027.',
      who: 'Belia yang dipilih (lepasan sekolah dan mahasiswa).',
      action: 'Semak status pemilihan melalui portal PLKN.',
      when: { all: [{ f: 'age', gte: 17, why: 'Berumur 17 hingga 20 tahun' }, { f: 'age', lte: 20 }] }, certainty: 'check',
      src: 'Perenggan 143, ms 85; Lampiran I Bil. 26, ms 248' },

    { id: 'k_youth', theme: 'youth', kind: 'manfaat',
      title: 'Program K-Youth (Khazanah)', value: 'Latihan sambil bekerja',
      summary: 'Untuk belia tanpa ijazah dalam sektor semikonduktor, jentera, penyelenggaraan pesawat, digital dan teknologi.',
      who: 'Belia berumur 30 tahun dan ke bawah yang tidak mempunyai ijazah.',
      action: 'Mohon melalui laman Khazanah atau rakan industri.',
      when: { all: [{ f: 'age', gte: 18 }, { f: 'age', lte: 30, why: 'Berumur 30 tahun dan ke bawah' },
        { f: 'employment', in: ['jobseeker', 'gig_ehailing', 'self_employed', 'employed_private', 'retired_other'], why: 'Mencari atau ingin menukar pekerjaan' }] },
      certainty: 'check', src: 'Perenggan 143, ms 85; Lampiran I Bil. 26, ms 248' },

    { id: 'latihan_tvet', theme: 'youth', kind: 'manfaat',
      title: 'Latihan kemahiran dan TVET', value: 'Latihan dan pensijilan kemahiran',
      summary: 'Melalui HRD Corp, pembiayaan PTPK (terutamanya bidang AI, kenderaan elektrik dan semikonduktor), GiatMARA (termasuk untuk pekerja gig), Kolej Komuniti (program pembelajaran sepanjang hayat untuk OKU, warga emas, ibu tunggal dan Orang Asli) serta kursus TVET untuk pekerja penjagaan (care workers) oleh KPWKM.',
      who: 'Pencari kerja, pekerja gig, mereka yang bekerja sendiri dan golongan rentan.',
      action: 'Mohon melalui HRD Corp, PTPK, GiatMARA, Kolej Komuniti atau KPWKM.',
      when: { any: [{ f: 'employment', in: ['jobseeker', 'gig_ehailing', 'self_employed', 'retired_other', 'housewife'], why: 'Mencari kerja atau bekerja sendiri' },
        C.okuSelf, { f: 'marital', eq: 'single_parent', why: 'Ibu atau bapa tunggal' }, { f: 'status', has: 'orang_asli', why: 'Orang Asli' }] },
      certainty: 'check', src: 'Perenggan 65, ms 50–51; Perenggan 174' },

    { id: 'pembiayaan_belia', theme: 'youth', kind: 'manfaat',
      title: 'Pembiayaan untuk usahawan belia', value: 'Pembiayaan mikro dan bantuan perniagaan',
      summary: 'Pembiayaan mikro BSN untuk usahawan berumur 30 tahun dan ke bawah, serta program Tunas Usahawan Belia Bumiputera (TUBE) oleh SME Corp untuk latihan dan bantuan perniagaan.',
      who: 'Usahawan belia berumur 30 tahun dan ke bawah.',
      action: 'Mohon melalui BSN atau SME Corp.',
      when: { all: [{ f: 'age', gte: 18 }, { f: 'age', lte: 30, why: 'Berumur 30 tahun dan ke bawah' },
        { f: 'employment', in: ['self_employed', 'gig_ehailing', 'jobseeker', 'student_ipt'], why: 'Berniaga atau berminat untuk berniaga' }] },
      certainty: 'check', src: 'Perenggan 143, ms 86; Lampiran I Bil. 26, ms 249' },

    { id: 'rakan_muda', theme: 'youth', kind: 'manfaat',
      title: 'Rakan Muda', value: 'Program pembangunan belia',
      summary: 'Program membina jati diri, pendidikan demokrasi dan kempen anti-buli, termasuk untuk belia luar bandar yang tercicir daripada pendidikan atau pekerjaan.',
      who: 'Belia berumur 15 hingga 30 tahun.',
      action: 'Sertai melalui portal atau aplikasi Rakan Muda.',
      when: { all: [{ f: 'age', gte: 15, why: 'Berumur 15 hingga 30 tahun' }, { f: 'age', lte: 30 }] }, certainty: 'high',
      src: 'Perenggan 143, ms 86; Lampiran I Bil. 26, ms 248' },

    /* ---------------- OKU, WARGA EMAS & GOLONGAN RENTAN ---------------- */
    { id: 'bantuan_oku', theme: 'vulnerable', kind: 'manfaat',
      title: 'Bantuan untuk OKU (JKM)', value: 'Elaun bulanan mengikut kategori',
      summary: 'Antaranya Elaun OKU Tidak Berupaya Bekerja, Elaun Pekerja OKU, serta bantuan penjagaan OKU dan pesakit kronik terlantar.',
      who: 'OKU berdaftar dengan JKM, mengikut kategori bantuan.',
      action: 'Mohon di Pejabat Kebajikan Masyarakat Daerah.',
      when: C.okuSelf, certainty: 'check',
      src: 'Perenggan 149, ms 87; Lampiran I Bil. 27, ms 253', portal: 'https://www.jkm.gov.my' },

    { id: 'warga_emas', theme: 'vulnerable', kind: 'manfaat',
      title: 'Bantuan kebajikan warga emas', value: 'Bantuan sosioekonomi dan pusat aktiviti',
      summary: 'Bantuan Sosioekonomi Warga Emas, Pusat Aktiviti Warga Emas (PAWE) dan Unit Penyayang Warga Emas.',
      who: 'Warga emas berumur 60 tahun ke atas yang berpendapatan rendah, tertakluk kepada syarat JKM.',
      action: 'Mohon di Pejabat Kebajikan Masyarakat Daerah.',
      when: { all: [{ f: 'age', gte: 60, why: 'Berumur 60 tahun ke atas' }, C.b40] }, certainty: 'check',
      src: 'Perenggan 173, ms 96; Lampiran I Bil. 31, ms 266' },

    { id: 'rumah_warga_emas', theme: 'vulnerable', kind: 'manfaat',
      title: 'Rumah warga emas mandiri (KWAP)', value: 'Kediaman khas untuk warga emas',
      summary: 'Projek rintis di Kepala Batas, Pulau Pinang untuk pesara dan golongan asnaf berpendapatan rendah. Lokasi lain sedang dinilai.',
      who: 'Pesara dan warga emas asnaf berpendapatan rendah.',
      action: 'Pantau pengumuman KWAP.',
      when: { all: [{ f: 'age', gte: 60, why: 'Berumur 60 tahun ke atas' }, C.b40] }, certainty: 'check',
      src: 'Perenggan 174, ms 97; Lampiran I Bil. 31, ms 266' },

    { id: 'peluang_kedua', theme: 'vulnerable', kind: 'manfaat',
      title: 'Dasar Peluang Kedua Fast Track', value: 'Proses pelepasan bankrap dipercepat',
      summary: 'Untuk ibu atau bapa tunggal, usahawan mikro yang terjejas akibat krisis, mangsa penipuan dan mangsa projek perumahan terbengkalai.',
      who: 'Individu bankrap dalam kategori yang disasarkan.',
      action: 'Hubungi Jabatan Insolvensi Malaysia (MdI).',
      when: { f: 'status', has: 'bankrupt', why: 'Sedang berstatus bankrap' }, certainty: 'check',
      src: 'Perenggan 150, ms 88; Lampiran I Bil. 27, ms 254' },

    { id: 'orang_asli', theme: 'vulnerable', kind: 'manfaat',
      title: 'Program untuk komuniti Orang Asli', value: 'Jalan kampung, TABIKA dan program pendidikan anak',
      summary: 'Jalan ke kampung Orang Asli dinaik taraf, TABIKA dibaiki di semua kampung Orang Asli, Sekolah Terapung di Hulu Perak diperluas dan program makanan komuniti diteruskan. Akta Orang Asli 1954 akan dipinda untuk memperkukuh hak berkaitan tanah dan kebajikan.',
      who: 'Komuniti Orang Asli.',
      action: 'Melalui Jabatan Kemajuan Orang Asli (JAKOA).',
      when: { f: 'status', has: 'orang_asli', why: 'Orang Asli' }, certainty: 'high',
      src: 'Perenggan 144–148, ms 86–87' },

    { id: 'itekad', theme: 'vulnerable', kind: 'manfaat',
      title: 'Geran padanan iTEKAD', value: 'Geran padanan untuk kemahiran, keusahawanan dan perlindungan',
      summary: 'iTEKAD diperluas untuk menyediakan geran padanan kepada penerima yang ingin meningkatkan kemahiran bagi pekerjaan dan pendapatan yang lebih stabil. Dana disumbangkan bersama oleh sektor swasta, termasuk institusi kewangan.',
      who: 'Golongan rentan, termasuk usahawan kecil dan pencari kerja.', action: 'Semak kelayakan melalui program iTEKAD.',
      when: { all: [C.b40, { f: 'employment', in: ['self_employed', 'jobseeker', 'gig_ehailing'], why: 'Bekerja sendiri atau mencari pekerjaan' }] }, certainty: 'check',
      src: 'Perenggan 67; Lampiran I Bil. 12' },

    /* ---------------- MENGIKUT PEKERJAAN ---------------- */
    { id: 'nelayan_elaun', theme: 'sector', kind: 'manfaat',
      title: 'Elaun Sara Hidup Nelayan', value: 'Sehingga RM300 sebulan',
      summary: 'Serta insentif hasil tangkapan. Bantuan turut disediakan untuk menaik taraf vesel.',
      who: 'Nelayan berdaftar dengan LKIM atau Jabatan Perikanan.',
      action: 'Melalui LKIM.',
      when: { f: 'employment', eq: 'fisher', why: 'Nelayan' }, certainty: 'high',
      src: 'Perenggan 111, ms 73' },

    { id: 'pesawah', theme: 'sector', kind: 'manfaat',
      title: 'Subsidi dan insentif pesawah', value: 'Bantuan kira-kira RM4,300 sehektar bagi setiap musim',
      summary: 'Termasuk subsidi harga padi, baja dan benih; insentif membajak RM160 dan insentif racun RM300 sehektar semusim; serta Insentif Penuaian Padi baharu RM50 sehektar semusim.',
      who: 'Pesawah padi berdaftar.',
      action: 'Melalui Pejabat Pertanian, Pertubuhan Peladang, MADA atau KADA.',
      when: { all: [C.farmer, { f: 'farmType', eq: 'padi', why: 'Menanam padi' }] }, certainty: 'high',
      src: 'Perenggan 106 dan 110, ms 70–72' },

    { id: 'pekebun_kecil', theme: 'sector', kind: 'manfaat',
      title: 'Insentif pekebun kecil getah dan sawit', value: 'Geran tanam semula sawit dan insentif pengeluaran getah',
      summary: 'Insentif tanam semula untuk pokok sawit berusia 25 tahun (50% geran dan 50% pinjaman mudah pada kadar serendah 2%), Insentif Pengeluaran Getah, Insentif Pengeluaran Lateks serta Bantuan Musim Tengkujuh.',
      who: 'Pekebun kecil getah dan sawit.',
      action: 'Melalui RISDA, FELDA, FELCRA atau Agrobank.',
      when: { all: [C.farmer, { f: 'farmType', eq: 'smallholder', why: 'Pekebun kecil getah atau sawit' }] }, certainty: 'check',
      src: 'Lampiran I Bil. 18, ms 218–219' },

    { id: 'agro', theme: 'sector', kind: 'manfaat',
      title: 'Pembiayaan dan geran usahawan tani', value: 'Pembiayaan Agrobank dan geran Agropreneur NextGen',
      summary: 'Pembiayaan untuk mengembangkan, mengautomasikan dan memekanisasikan projek pertanian, serta geran permulaan dan geran pengembangan Agropreneur NextGen.',
      who: 'Petani, penternak dan pengusaha akuakultur. Agropreneur NextGen untuk golongan muda.',
      action: 'Mohon melalui Agrobank atau Kementerian Pertanian dan Keterjaminan Makanan.',
      when: C.farmer, certainty: 'check',
      src: 'Perenggan 108, ms 71' },

    { id: 'bkht', theme: 'sector', kind: 'manfaat',
      title: 'Bantuan kerugian akibat serangan hidupan liar', value: 'Pampasan kerosakan harta benda dan tanaman',
      summary: 'Bantuan Kerugian Harta Benda dan Tanaman Akibat Serangan Hidupan Liar (BKHT) untuk mangsa yang terjejas.',
      who: 'Mangsa yang mengalami kerugian akibat konflik hidupan liar.',
      action: 'Laporkan kepada PERHILITAN.',
      when: C.farmer, certainty: 'check',
      src: 'Lampiran I, ms 238' },

    { id: 'penjawat_sspa', theme: 'sector', kind: 'manfaat',
      title: 'Penambahbaikan saraan penjawat awam', value: 'Kenaikan gaji SSPA Fasa 2 mulai Januari 2026',
      summary: 'Sistem Saraan Perkhidmatan Awam (SSPA) Fasa 2 berkuat kuasa Januari 2026. Elaun Sara Hidup RM900 sebulan untuk penerima Hadiah Latihan Persekutuan Separa Biasiswa, dan Bantuan Insentif Berasaskan Prestasi diperluas kepada Kumpulan Pengurusan dan Profesional.',
      who: 'Penjawat awam Persekutuan.',
      action: 'Secara automatik atau melalui jabatan masing-masing.',
      when: C.civil, certainty: 'high',
      src: 'Perenggan 240–245, ms 125–126' },

    { id: 'veteran', theme: 'sector', kind: 'manfaat',
      title: 'Peluang pekerjaan untuk veteran', value: 'Keutamaan dalam pengambilan pekerja',
      summary: 'Kontraktor MINDEF menyediakan peluang pekerjaan untuk veteran melalui skim PROTÉGÉ-Veteran, dan Agensi Kawalan dan Perlindungan Sempadan (AKPS) mengutamakan veteran dalam pengambilan.',
      who: 'Veteran Angkatan Tentera Malaysia.',
      action: 'Hubungi JHEV atau PERHEBAT.',
      when: { f: 'status', has: 'veteran', why: 'Veteran Angkatan Tentera Malaysia' }, certainty: 'check',
      src: 'Perenggan 119–120, ms 75' },

    { id: 'teksi', theme: 'sector', kind: 'manfaat',
      title: 'Insentif untuk pemandu teksi', value: 'Tiada duti eksais dan cukai jualan untuk kereta nasional baharu',
      summary: 'Pengecualian penuh duti eksais dan cukai jualan bagi pembelian kereta Proton atau Perodua baharu oleh pemilik teksi dan kereta sewa. HRD Corp juga menanggung kos kursus dan elaun untuk pemandu teksi berlesen yang mencarum.',
      who: 'Pemilik dan pemandu teksi serta kereta sewa persendirian.',
      action: 'Melalui APAD atau HRD Corp.',
      when: { f: 'status', has: 'taxi', why: 'Pemandu atau pemilik teksi' }, certainty: 'high',
      src: 'Perenggan 76, ms 56' },

    { id: 'saringan_pemandu', theme: 'sector', kind: 'manfaat',
      title: 'Pemeriksaan kesihatan percuma untuk pemandu', value: 'Pemeriksaan kesihatan percuma oleh PERKESO',
      summary: 'Untuk pemandu kenderaan pengangkutan awam dan barangan berumur 40 hingga 59 tahun.',
      who: 'Pemandu kenderaan awam dan barangan berumur 40 hingga 59 tahun.',
      action: 'Melalui PERKESO.',
      when: { all: [{ f: 'status', has: 'taxi', why: 'Pemandu pengangkutan awam' }, { f: 'age', gte: 40, why: 'Berumur 40 hingga 59 tahun' }, { f: 'age', lte: 59 }] },
      certainty: 'check', src: 'Perenggan 212, ms 114; Lampiran I Bil. 30, ms 264' },

    { id: 'penghargaan_pesara', theme: 'sector', kind: 'manfaat',
      title: 'Bayaran penghargaan khas pesara dilanjutkan', value: 'Diteruskan dari Januari hingga Disember',
      summary: 'Bayaran penghargaan khas kepada pesara dan penerima pencen terbitan dilanjutkan. Kadar bayaran tidak dinyatakan dalam teks Belanjawan.',
      who: 'Pesara Kerajaan dan penerima pencen terbitan.', action: 'Semak dengan Jabatan Perkhidmatan Awam (JPA).',
      when: { f: 'employment', eq: 'retired_gov', why: 'Pesara Kerajaan' }, certainty: 'check',
      src: 'Lampiran I Bil. 40' },

    { id: 'bsh_pesara_kemas', theme: 'sector', kind: 'manfaat',
      title: 'Bayaran Sara Hidup pesara kontrak KEMAS dinaikkan', value: 'RM500 sebulan (sebelum ini RM300)',
      summary: 'Kadar Bayaran Sara Hidup (BSH) bagi pesara kakitangan kontrak KEMAS dinaikkan daripada RM300 kepada RM500 sebulan.',
      who: 'Pesara kakitangan kontrak KEMAS.', action: 'Semak dengan KEMAS.',
      when: { f: 'employment', in: ['retired_gov', 'retired_other'], why: 'Pesara' }, certainty: 'check',
      src: 'Perenggan 238; Lampiran I Bil. 40' },

    { id: 'apel_q', theme: 'sector', kind: 'manfaat',
      title: 'Program APEL.Q INTAN untuk penjawat awam', value: 'Kerajaan menanggung 50% kos pengajian, sehingga RM15,000',
      summary: 'Untuk penjawat awam yang telah berkhidmat melebihi 15 tahun dan ingin melanjutkan pengajian ke peringkat yang lebih tinggi.',
      who: 'Penjawat awam yang telah berkhidmat melebihi 15 tahun.', action: 'Semak dengan INTAN atau bahagian sumber manusia jabatan anda.',
      when: C.civil, certainty: 'check',
      src: 'Lampiran I Bil. 40' },

    { id: 'etap_perubatan', theme: 'sector', kind: 'manfaat',
      title: 'Elaun Tugas Atas Panggilan (ETAP) pegawai perubatan dinaikkan', value: 'Naik antara 33% hingga 43% mengikut kelayakan',
      summary: 'Kadar ETAP yang tidak dikaji sejak 2011 dinaikkan. Contohnya, pegawai perubatan pakar yang bertugas atas panggilan aktif pada hari cuti menerima RM350 (sebelum ini RM250).',
      who: 'Pegawai perubatan, pegawai perubatan pakar dan pegawai pergigian.', action: 'Semak dengan jabatan anda.',
      when: C.civil, certainty: 'check', timing: 'Berkuat kuasa 1 Oktober 2025.',
      src: 'Perenggan 182; Lampiran I Bil. 32' },

    { id: 'lantikan_tetap_kkm', theme: 'sector', kind: 'manfaat',
      title: 'Lantikan tetap untuk doktor, jururawat dan graduan kontrak KKM', value: 'Tawaran lantikan tetap mulai 2026',
      summary: 'Doktor kontrak dan graduan Institut Latihan KKM akan ditawarkan jawatan tetap mulai 2026. Jururawat kontrak turut ditawarkan lantikan tetap.',
      who: 'Doktor kontrak, jururawat kontrak dan graduan Institut Latihan KKM.', action: 'Semak dengan Kementerian Kesihatan Malaysia (KKM).',
      when: C.civil, certainty: 'check',
      src: 'Perenggan 182; Lampiran I Bil. 32' },

    { id: 'bipk_bipac', theme: 'sector', kind: 'manfaat',
      title: 'Bayaran insentif pasukan khas (BIPK dan BIPAC) dinaikkan', value: 'Kadar bayaran dinaikkan',
      summary: 'Bayaran Insentif Pasukan Khas (BIPK) dan Bayaran Insentif Pasukan Atur Cara (BIPAC) ditambah baik melalui kenaikan kadar bayaran dan pelarasan syarat tempoh perkhidmatan.',
      who: 'Pegawai dan anggota pasukan khas.', action: 'Semak dengan pasukan atau jabatan anda.',
      when: C.civil, certainty: 'check',
      src: 'Lampiran I Bil. 40' },

    { id: 'geran_bsn', theme: 'sector', kind: 'manfaat',
      title: 'Geran perniagaan BSN untuk usahawan mikro', value: 'Sehingga RM10,000 untuk membeli peralatan perniagaan',
      summary: 'BSN menyediakan geran perniagaan kepada usahawan mikro yang berpotensi, sebagai modal untuk membeli peralatan perniagaan.',
      who: 'Usahawan mikro.', action: 'Semak dengan cawangan BSN.',
      when: { f: 'employment', eq: 'self_employed', why: 'Bekerja sendiri atau peniaga kecil' }, certainty: 'check',
      src: 'Perenggan 156; Lampiran I Bil. 28' },

    { id: 'pinjaman_mikro', theme: 'sector', kind: 'manfaat',
      title: 'Pinjaman mikro BSN dan TEKUN', value: 'Pinjaman kecil untuk modal perniagaan',
      summary: 'BSN dan TEKUN Nasional menyediakan pinjaman mikro kepada usahawan mikro dan peniaga kecil untuk modal dan keperluan perniagaan.',
      who: 'Usahawan mikro dan peniaga kecil.', action: 'Mohon di cawangan BSN atau TEKUN Nasional.',
      when: { f: 'employment', eq: 'self_employed', why: 'Bekerja sendiri atau peniaga kecil' }, certainty: 'check',
      src: 'Perenggan 98' },

    { id: 'kwap_mikro', theme: 'sector', kind: 'manfaat',
      title: 'Pembiayaan mikro KWAP untuk pesara', value: 'Pembiayaan mikro untuk memulakan perniagaan komuniti',
      summary: 'KWAP menyediakan program pembiayaan mikro bagi pesara untuk memperkasa keusahawanan di peringkat komuniti.',
      who: 'Pesara Kerajaan.', action: 'Semak dengan KWAP.',
      when: { f: 'employment', eq: 'retired_gov', why: 'Pesara Kerajaan' }, certainty: 'check',
      src: 'Perenggan 138' },

    { id: 'tamu_desa', theme: 'sector', kind: 'manfaat',
      title: 'Ruang niaga Tamu Desa di Sabah dan Sarawak', value: 'Tapak dan ruang niaga baharu dengan kemudahan asas',
      summary: 'Tapak dan ruang niaga yang dilengkapi kemudahan asas ditambah untuk peniaga kecil Tamu Desa di Sabah dan Sarawak.',
      who: 'Peniaga kecil Tamu Desa di Sabah dan Sarawak.', action: 'Semak dengan pihak berkuasa tempatan.',
      when: { all: [{ f: 'region', in: ['sabah', 'sarawak'], why: 'Menetap di Sabah atau Sarawak' }, { f: 'employment', eq: 'self_employed', why: 'Bekerja sendiri atau peniaga kecil' }] }, certainty: 'check',
      src: 'Perenggan 46; Lampiran I Bil. 8' },

    { id: 'buah_buahan', theme: 'sector', kind: 'manfaat',
      title: 'Insentif pengusaha buah-buahan tempatan', value: 'Insentif tanaman dan prasarana ladang',
      summary: 'Untuk pengusaha buah-buahan tempatan, antaranya ladang nanas termasuk di Sarawak, serta tanaman durian belanda, jambu air dan limau besar.',
      who: 'Pengusaha buah-buahan tempatan.', action: 'Semak dengan pejabat pertanian berhampiran.',
      when: { all: [C.farmer, { f: 'farmType', eq: 'other', why: 'Tanaman lain, ternakan atau akuakultur' }] }, certainty: 'check',
      src: 'Perenggan 112; Lampiran I Bil. 20' },

    { id: 'penternak', theme: 'sector', kind: 'manfaat',
      title: 'Insentif penternak ruminan kecil dan lembu pedaging', value: 'Insentif bagi penternak yang mencapai kadar kelahiran ternakan yang ditetapkan',
      summary: 'Penternak ruminan kecil dengan kadar kelahiran ternakan sedia ada sekurang-kurangnya 100%, dan penternak lembu pedaging dengan kadar sekurang-kurangnya 60%, layak menerima insentif.',
      who: 'Penternak ruminan kecil dan lembu pedaging.', action: 'Semak dengan pejabat pertanian atau veterinar berhampiran.',
      when: { all: [C.farmer, { f: 'farmType', eq: 'other', why: 'Tanaman lain, ternakan atau akuakultur' }] }, certainty: 'check',
      src: 'Lampiran I Bil. 20' },

    { id: 'elaun_imam_kafa', theme: 'sector', kind: 'manfaat',
      title: 'Elaun bulanan imam, guru KAFA dan guru takmir', value: 'Elaun bulanan diteruskan',
      summary: 'Elaun bulanan kepada imam, guru KAFA dan guru takmir diteruskan pada tahun 2026. Kadar elaun tidak dinyatakan dalam teks Belanjawan.',
      who: 'Imam, guru KAFA dan guru takmir.', action: 'Semak dengan majlis agama Islam negeri.',
      when: { f: 'status', has: 'religious_staff', why: 'Petugas institusi agama Islam' }, certainty: 'check',
      src: 'Lampiran I Bil. 36' },

    /* ---------------- PENGANGKUTAN & MOBILITI ---------------- */
    { id: 'myraillife', theme: 'mobility', kind: 'manfaat',
      title: 'Pas MyRailLife percuma', value: 'Perjalanan percuma tanpa had dengan KTM Komuter dan Shuttle DMU',
      summary: 'Untuk komuniti OKU dan semua murid sekolah, kini diperluas kepada kanak-kanak berumur bawah 6 tahun.',
      who: 'OKU, murid sekolah dan kanak-kanak berumur bawah 6 tahun.',
      action: 'Mohon pas melalui KTMB.',
      when: { any: [C.okuSelf, C.okuChild, C.school, { f: 'childStages', has: 'under6', why: 'Ada anak bawah 6 tahun' }] },
      certainty: 'high', src: 'Perenggan 208, ms 111; Lampiran I Bil. 34, ms 284' },

    { id: 'van_oku', theme: 'mobility', kind: 'manfaat',
      title: 'Van mobiliti khas untuk OKU', value: 'Perkhidmatan van yang boleh membawa kerusi roda',
      summary: 'Setiap van boleh membawa sehingga tiga penumpang berkerusi roda dan dilengkapi sistem pengangkat kerusi roda.',
      who: 'OKU, terutamanya pengguna kerusi roda.',
      action: 'Tempah melalui Prasarana (Rapid).',
      when: { any: [C.okuSelf, C.okuChild] }, certainty: 'check',
      src: 'Perenggan 149, ms 88' },

    { id: 'lupus_kenderaan', theme: 'mobility', kind: 'manfaat',
      title: 'Geran menukar kereta lama', value: 'Geran RM2,000 dan padanan RM2,000 daripada pengeluar (kira-kira RM4,000)',
      summary: 'Untuk pemilik yang melupuskan kereta berusia lebih 20 tahun dan membeli kereta nasional baharu.',
      who: 'Pemilik kereta berusia lebih 20 tahun.',
      action: 'Melalui pengeluar kereta nasional (Proton atau Perodua).',
      when: { f: 'assets', has: 'old_car', why: 'Memiliki kereta berusia lebih 20 tahun' }, certainty: 'check',
      src: 'Perenggan 213, ms 114; Lampiran I Bil. 34, ms 287–288' },

    { id: 'ras', theme: 'mobility', kind: 'manfaat',
      title: 'Subsidi penerbangan luar bandar (RAS)', value: 'Tambang penerbangan bersubsidi',
      summary: 'Subsidi Perkhidmatan Udara Luar Bandar untuk penduduk desa dan pedalaman Sabah dan Sarawak.',
      who: 'Penduduk pedalaman Sabah dan Sarawak.',
      action: 'Harga bersubsidi terpakai secara automatik pada laluan RAS.',
      when: { f: 'region', in: ['sabah', 'sarawak'], why: 'Menetap di Sabah atau Sarawak' }, certainty: 'high',
      src: 'Perenggan 208, ms 111' },

    /* ---------------- PELEPASAN CUKAI INDIVIDU (Tahun Taksiran 2026) ---------------- */
    { id: 'tax_vaksin', theme: 'tax', kind: 'manfaat',
      title: 'Pelepasan cukai pemvaksinan, kini untuk semua vaksin berdaftar', value: 'Sehingga RM1,000',
      summary: 'Sebelum ini terhad kepada lapan jenis vaksin. Kini meliputi semua vaksin yang berdaftar dengan KKM, untuk diri sendiri, pasangan atau anak.',
      who: 'Pembayar cukai pendapatan.', action: 'Tuntut semasa mengisi e-Filing bagi Tahun Taksiran 2026. Simpan resit.',
      when: C.taxpayer, certainty: 'high', src: 'Perenggan 184, ms 103; Lampiran II — Lampiran 1, ms 315' },

    { id: 'tax_insurans', theme: 'tax', kind: 'manfaat',
      title: 'Pelepasan cukai insurans nyawa, kini termasuk untuk anak', value: 'Sehingga RM3,000',
      summary: 'Pelepasan cukai premium insurans nyawa atau takaful hayat diperluas kepada anak (bawah 18 tahun, sedang belajar di institusi pengajian tinggi, atau OKU tanpa had umur).',
      who: 'Pembayar cukai yang membayar premium untuk anak.', action: 'Tuntut semasa mengisi e-Filing bagi Tahun Taksiran 2026.',
      when: { all: [C.taxpayer, { f: 'hasChildren', eq: true, why: 'Mempunyai anak tanggungan' }] }, certainty: 'high',
      src: 'Perenggan 181, ms 100; Lampiran II — Lampiran 4, ms 318' },

    { id: 'tax_taska', theme: 'tax', kind: 'manfaat',
      title: 'Pelepasan cukai yuran taska, tadika dan pusat jagaan', value: 'RM3,000 (kekal)',
      summary: 'Digabungkan menjadi RM3,000 secara kekal dan diperluas kepada pusat jagaan harian atau pusat transit berdaftar JKM untuk anak sehingga 12 tahun.',
      who: 'Ibu atau bapa (salah seorang sahaja) yang menghantar anak berumur 12 tahun dan ke bawah ke pusat jagaan berdaftar.',
      action: 'Tuntut semasa mengisi e-Filing bagi Tahun Taksiran 2026.',
      when: { all: [C.taxpayer, { f: 'childStages', hasAny: ['under6', 'primary'], why: 'Mempunyai anak berumur 12 tahun dan ke bawah' }] },
      certainty: 'high', src: 'Perenggan 142, ms 84; Lampiran II — Lampiran 2, ms 316' },

    { id: 'tax_kurang_upaya', theme: 'tax', kind: 'manfaat',
      title: 'Pelepasan cukai intervensi awal anak kurang upaya pembelajaran', value: 'Dinaikkan daripada RM6,000 kepada RM10,000',
      summary: 'Untuk pemeriksaan, program intervensi awal dan rawatan pemulihan anak berumur bawah 18 tahun (seperti autisme, ADHD, lewat perkembangan global dan sindrom Down).',
      who: 'Pembayar cukai yang mempunyai anak kurang upaya pembelajaran.', action: 'Tuntut semasa mengisi e-Filing bagi Tahun Taksiran 2026.',
      when: { all: [C.taxpayer, C.okuChild] }, certainty: 'high',
      src: 'Perenggan 149, ms 88; Lampiran II — Lampiran 3, ms 317' },

    { id: 'tax_lestari', theme: 'tax', kind: 'manfaat',
      title: 'Pelepasan cukai peralatan hijau dan keselamatan rumah', value: 'Sehingga RM2,500',
      summary: 'Pengecas kenderaan elektrik, mesin kompos, dan kini mesin pengisar sisa makanan serta CCTV untuk kegunaan rumah (Tahun Taksiran 2026 dan 2027).',
      who: 'Pembayar cukai pendapatan.', action: 'Tuntut semasa mengisi e-Filing. CCTV dan mesin pengisar sisa makanan boleh dituntut sekali dalam tempoh dua tahun.',
      when: C.taxpayer, certainty: 'high', src: 'Lampiran II — Lampiran 5, ms 319' },

    { id: 'tax_pelancongan', theme: 'tax', kind: 'manfaat',
      title: 'Pelepasan cukai tiket masuk tempat pelancongan dan program budaya', value: 'Sehingga RM1,000 (Tahun Taksiran 2026 sahaja)',
      summary: 'Untuk fi masuk ke muzium, taman tema, taman negara, taman laut, zoo, geopark dan program kebudayaan, sempena Tahun Melawat Malaysia 2026.',
      who: 'Pembayar cukai pendapatan.', action: 'Simpan resit atau tiket dan tuntut semasa mengisi e-Filing bagi Tahun Taksiran 2026.',
      when: C.taxpayer, certainty: 'high', src: 'Perenggan 75, ms 56; Lampiran II — Lampiran 6, ms 320' },

    { id: 'potongan_derma', theme: 'tax', kind: 'manfaat',
      title: 'Potongan cukai untuk sumbangan tunai', value: 'Potongan cukai pendapatan bagi sumbangan yang layak',
      summary: 'Sumbangan tunai kepada program pencegahan rasuah yang diiktiraf SPRM, tabung endowmen hospital pengajar universiti awam, Akaun Amanah Jabatan Muzium Malaysia, serta projek komuniti, amal atau infrastruktur seperti hentian bas layak mendapat potongan cukai pendapatan.',
      who: 'Pembayar cukai yang membuat sumbangan tunai.', action: 'Simpan resit dan tuntut semasa mengisi e-Filing.',
      when: C.taxpayer, certainty: 'high',
      timing: 'Tabung endowmen hospital pengajar: mulai Tahun Taksiran 2026. Program pencegahan rasuah: bagi program yang dilaksanakan dari 1 Januari 2026 hingga 31 Disember 2028.',
      src: 'Perenggan 28, 82, 205; Lampiran I Bil. 34; Lampiran II — Lampiran 12 dan 13' },

    /* ---------------- KES KHAS: GAYA HIDUP, PELABURAN & PERUBAHAN HARGA ---------------- */
    { id: 'duti_rokok', theme: 'special', kind: 'kesan',
      title: 'Harga rokok naik', value: 'Naik 40 sen sepaket (2 sen sebatang)',
      summary: 'Duti eksais rokok dinaikkan secara berperingkat mulai 1 November 2025. Hasil tambahan disalurkan kepada KKM untuk program kesihatan paru-paru serta rawatan diabetes dan penyakit jantung.',
      who: 'Perokok.', action: 'Pertimbangkan bantuan berhenti merokok (lihat di bawah).',
      when: { f: 'lifestyle', has: 'cigarette', why: 'Merokok' }, certainty: 'high',
      src: 'Perenggan 184, ms 102; Lampiran II — Lampiran 36, ms 356' },

    { id: 'duti_cerut', theme: 'special', kind: 'kesan',
      title: 'Harga cerut naik', value: 'Duti eksais naik RM40 sekilogram',
      summary: 'Berkuat kuasa mulai 1 November 2025 sebagai kenaikan berperingkat.',
      who: 'Pengguna cerut dan cerut kecil (cigarillo).', action: 'Pertimbangkan bantuan berhenti merokok (lihat di bawah).',
      when: { f: 'lifestyle', has: 'cigar', why: 'Menghisap cerut atau cerut kecil (cigarillo)' }, certainty: 'high',
      src: 'Perenggan 184, ms 102; Lampiran II — Lampiran 37, ms 357' },

    { id: 'duti_heated_tobacco', theme: 'special', kind: 'kesan',
      title: 'Harga produk tembakau yang dipanaskan naik', value: 'Duti eksais naik RM20 sekilogram kandungan tembakau',
      summary: 'Berkuat kuasa mulai 1 November 2025 sebagai kenaikan berperingkat.',
      who: 'Pengguna produk tembakau yang dipanaskan.', action: 'Pertimbangkan bantuan berhenti merokok (lihat di bawah).',
      when: { f: 'lifestyle', has: 'heated_tobacco', why: 'Menggunakan produk tembakau yang dipanaskan' }, certainty: 'high',
      src: 'Perenggan 184, ms 102; Lampiran II — Lampiran 38, ms 358' },

    { id: 'vape', theme: 'special', kind: 'kesan',
      title: 'Rokok elektronik mungkin diharamkan', value: 'Kerajaan sedang meneliti larangan penggunaan',
      summary: 'Kerajaan sedang meneliti cadangan untuk mengharamkan penggunaan rokok elektronik (vape).',
      who: 'Pengguna vape atau rokok elektronik.', action: 'Pantau pengumuman KKM. Pertimbangkan bantuan berhenti merokok.',
      when: { f: 'lifestyle', has: 'vape', why: 'Menggunakan vape atau rokok elektronik' }, certainty: 'high',
      src: 'Lampiran I Bil. 32, ms 271' },

    { id: 'berhenti_merokok', theme: 'special', kind: 'manfaat',
      title: 'Produk bantuan berhenti merokok lebih murah', value: 'Dikecualikan duti import dan cukai jualan hingga 31 Disember 2027',
      summary: 'Gula-gula getah nikotin dan tampalan nikotin kekal dikecualikan, dan kini diperluas kepada semburan nikotin dan lozeng nikotin. Sokongan berhenti merokok percuma juga tersedia melalui program mQuit KKM.',
      who: 'Sesiapa yang ingin berhenti merokok atau vape.', action: 'Dapatkan nasihat di klinik kesihatan atau farmasi. Sertai program mQuit KKM.',
      when: { f: 'smoker', eq: true, why: 'Merokok atau menggunakan produk nikotin' }, certainty: 'high',
      src: 'Perenggan 184, ms 102; Lampiran II — Lampiran 39, ms 359' },

    { id: 'duti_alkohol', theme: 'special', kind: 'kesan',
      title: 'Harga minuman beralkohol naik', value: 'Duti eksais naik 10%',
      summary: 'Berkuat kuasa mulai 1 November 2025. Hasil tambahan disalurkan kepada KKM.',
      who: 'Pengguna minuman beralkohol.', action: 'Tiada tindakan diperlukan.',
      when: { f: 'lifestyle', has: 'alcohol', why: 'Mengambil minuman beralkohol' }, certainty: 'high',
      src: 'Perenggan 184, ms 102; Lampiran II — Lampiran 40, ms 360' },

    { id: 'fi_klinik_swasta', theme: 'special', kind: 'kesan',
      title: 'Fi rundingan klinik swasta disemak semula', value: 'Kini antara RM10 hingga RM80 (sebelum ini RM10 hingga RM35)',
      summary: 'Kadar fi rundingan doktor di klinik swasta ditetapkan semula buat kali pertama sejak 2006, bergantung pada jenis perkhidmatan. Kadar minimum RM10 dikekalkan.',
      who: 'Semua pesakit yang mendapatkan rawatan di klinik swasta.', action: 'Tanya kadar fi sebelum mendapatkan rawatan. Klinik kesihatan Kerajaan kekal sebagai pilihan.',
      when: C.adult, certainty: 'high',
      src: 'Perenggan 182, ms 101; Lampiran I Bil. 32, ms 270' },

    { id: 'duti_kontrak_kerja', theme: 'special', kind: 'manfaat',
      title: 'Tiada duti setem untuk kontrak pekerjaan bergaji rendah', value: 'Dikecualikan jika gaji RM3,000 dan ke bawah sebulan',
      summary: 'Had gaji untuk pengecualian duti setem RM10 ke atas kontrak pekerjaan dinaikkan daripada RM300 kepada RM3,000 sebulan, bagi kontrak yang ditandatangani mulai 1 Januari 2026.',
      who: 'Pekerja yang menandatangani kontrak pekerjaan baharu dengan gaji RM3,000 dan ke bawah sebulan.', action: 'Tiada tindakan diperlukan.',
      when: { f: 'employment', in: ['employed_private', 'jobseeker'], why: 'Pekerja atau bakal pekerja' }, certainty: 'check',
      src: 'Lampiran II — Lampiran 20, ms 336' },

    { id: 'pelabur_runcit', theme: 'special', kind: 'manfaat',
      title: 'Tiada duti setem untuk urus niaga ETF dan waran berstruktur', value: 'Dikecualikan duti setem nota kontrak hingga 31 Disember 2028',
      summary: 'Pengecualian untuk jual beli dana dagangan bursa (ETF) dilanjutkan, dan pengecualian baharu untuk pembelian waran berstruktur.',
      who: 'Pelabur runcit di Bursa Malaysia.', action: 'Diberikan secara automatik melalui broker.',
      when: { f: 'assets', has: 'invest_bursa', why: 'Melabur di Bursa Malaysia' }, certainty: 'high',
      src: 'Lampiran II — Lampiran 18 dan 19, ms 334–335' },

    { id: 'cukai_plt', theme: 'special', kind: 'kesan',
      title: 'Cukai ke atas agihan keuntungan Perkongsian Liabiliti Terhad (PLT)', value: 'Cukai 2% ke atas agihan keuntungan melebihi RM100,000 setahun',
      summary: 'Bermula Tahun Taksiran 2026, agihan keuntungan PLT yang diterima oleh pekongsi individu melebihi RM100,000 setahun dikenakan cukai 2% dan perlu dilaporkan dalam borang nyata cukai.',
      who: 'Pekongsi individu dalam PLT.', action: 'Laporkan agihan keuntungan PLT dalam e-Filing.',
      when: { f: 'assets', has: 'llp_partner', why: 'Pekongsi dalam PLT' }, certainty: 'check',
      src: 'Lampiran II — Lampiran 7, ms 321–322' },

    { id: 'ptptn_sekatan_perjalanan', theme: 'special', kind: 'kesan',
      title: 'Sekatan perjalanan ke luar negara bagi peminjam PTPTN yang culas', value: 'Boleh disekat daripada ke luar negara',
      summary: 'Kerajaan akan mengenakan sekatan perjalanan ke luar negara kepada peminjam PTPTN yang mampu membayar dan bekerja di luar negara, tetapi culas membuat bayaran balik.',
      who: 'Peminjam PTPTN yang mampu membayar tetapi tidak membuat bayaran balik.', action: 'Semak baki pinjaman dan jadual bayaran balik melalui PTPTN.',
      when: { all: [C.adult, { f: 'assets', has: 'ptptn_loan', why: 'Mempunyai pinjaman PTPTN' }] }, certainty: 'check',
      src: 'Perenggan 202, ms 109', portal: 'https://www.ptptn.gov.my' },

    { id: 'cukai_kenderaan_labuan', theme: 'special', kind: 'kesan',
      title: 'Pengecualian cukai kenderaan di Labuan dan Langkawi dihadkan', value: 'Hanya bagi kenderaan bernilai sehingga RM300,000',
      summary: 'Pengecualian cukai kenderaan di Labuan dan Langkawi dihadkan kepada kenderaan yang bernilai tidak melebihi RM300,000, bagi menangani ketirisan oleh pemilik kenderaan mewah.',
      who: 'Pemilik kenderaan di Labuan dan Langkawi.', action: 'Semak nilai kenderaan sebelum membeli kenderaan baharu.',
      when: { all: [C.adult, { f: 'region', eq: 'labuan', why: 'Menetap di Wilayah Persekutuan Labuan' }, { f: 'assets', has: 'license', why: 'Mempunyai lesen memandu' }] },
      certainty: 'high', timing: 'Berkuat kuasa 1 Januari 2026.',
      src: 'Perenggan 27' }
  ];

  /* ================================================================
   * 7. PUBLIC API
   * ================================================================ */
  function getVisibleQuestions(answers) {
    var facts = deriveFacts(answers || {});
    return QUESTIONS.filter(function (q) {
      if (!q.showIf) return true;
      return test(q.showIf, facts).v === true;
    });
  }

  function pruneAnswers(answers) {
    // Iterate until stable: pruning one answer may hide further questions.
    var cur = answers || {};
    for (var n = 0; n < 5; n++) {
      var visible = getVisibleQuestions(cur).map(function (q) { return q.id; });
      var next = {};
      Object.keys(cur).forEach(function (k) { if (visible.indexOf(k) > -1) next[k] = cur[k]; });
      if (Object.keys(next).length === Object.keys(cur).length) return next;
      cur = next;
    }
    return cur;
  }

  function isComplete(answers) {
    return getVisibleQuestions(answers).every(function (q) {
      var v = answers[q.id];
      return q.type === 'multi' ? Array.isArray(v) && v.length > 0 : (v !== undefined && v !== null && v !== '');
    });
  }

  function evaluate(answers) {
    var a = pruneAnswers(answers || {});
    var facts = deriveFacts(a);
    var strSara = calcStrSara(facts);
    var results = [];

    BENEFITS.forEach(function (b) {
      var r = test(b.when, facts);
      if (r.v === false) return;
      var tier = b.kind === 'kesan' ? 'kesan' : (r.v === null ? 'mungkin' : (b.certainty === 'check' ? 'semak' : 'layak'));
      results.push({
        id: b.id, theme: b.theme, kind: b.kind, tier: tier, tierLabel: TIERS[tier].label,
        title: b.title, value: b.value, summary: b.summary, who: b.who, action: b.action,
        timing: b.timing || null, src: b.src, web: b.web || null, portal: b.portal || null,
        reasons: dedupe(r.why), needsConfirm: dedupe(r.unknown),
        compute: b.compute || null
      });
    });

    var byTheme = THEMES.map(function (t) {
      var items = results.filter(function (x) { return x.theme === t.id; })
        .sort(function (x, y) { return TIERS[x.tier].rank - TIERS[y.tier].rank; });
      return { id: t.id, label: t.label, count: items.length, items: items };
    }).filter(function (g) { return g.count > 0; });

    var counts = { total: results.length };
    Object.keys(TIERS).forEach(function (k) { counts[k] = results.filter(function (x) { return x.tier === k; }).length; });

    return {
      version: VERSION, dataAsOf: DATA_AS_OF,
      facts: facts, strSara: strSara,
      results: results, byTheme: byTheme,
      advisories: buildAdvisories(facts, strSara, a),
      counts: counts
    };
  }

  var SKIP_NAMES = { marital: 'status perkahwinan', children: 'bilangan anak', child_stages: 'peringkat anak', income: 'pendapatan',
    ekasih: 'status eKasih', employment: 'pekerjaan', farm_type: 'jenis pertanian', gender: 'jantina', assets: 'aset dan rancangan',
    status: 'keadaan khas', lifestyle: 'gaya hidup', self_school: 'status persekolahan', str_status: 'status STR' };

  function buildAdvisories(f, s, a) {
    var out = [];
    if (s.eligible === true && f.strStatus === 'no')
      out.push({ type: 'action', text: 'Anda berkemungkinan layak menerima STR tetapi belum menerimanya. Mohon di bantuantunai.hasil.gov.my. Permohonan STR juga membuka akses kepada SARA, mySalam, PeKa B40 dan Skim Perubatan MADANI.' });
    if (s.eligible === true && (f.strStatus === 'unsure' || f.strStatus === SKIP))
      out.push({ type: 'action', text: 'Semak status STR anda di bantuantunai.hasil.gov.my dan status SARA di sara.gov.my.' });
    if (a.ekasih === 'unsure')
      out.push({ type: 'info', text: 'Status eKasih anda tidak pasti. Jika isi rumah anda berdaftar, kadar SARA lebih tinggi dan beberapa bantuan lain mungkin terpakai. Semak dengan Pejabat Daerah.' });
    var skipped = f._skipped.map(function (k) { return SKIP_NAMES[k] || k; });
    if (skipped.length)
      out.push({ type: 'info', text: 'Anda memilih untuk tidak menyatakan: ' + skipped.join(', ') + '. Faedah yang bergantung pada maklumat ini dipaparkan sebagai "Mungkin layak" atau tidak dipaparkan.' });
    if (f.assets.indexOf('taxpayer') === -1 && f.incomeMin != null && f.incomeMin > 5000 && (!a.assets || a.assets.indexOf(SKIP) === -1))
      out.push({ type: 'info', text: 'Dengan pendapatan ini, anda mungkin perlu membayar cukai pendapatan. Beberapa pelepasan cukai baharu bagi Tahun Taksiran 2026 mungkin berkaitan dengan anda.' });
    out.push({ type: 'disclaimer', text: 'Panduan umum berdasarkan Ucapan Belanjawan 2026 (maklumat setakat ' + DATA_AS_OF + '). Ini bukan penentuan kelayakan rasmi. Sila sahkan dengan agensi yang berkaitan.' });
    return out;
  }

  function dedupe(xs) { var seen = {}; return xs.filter(function (x) { if (seen[x]) return false; seen[x] = 1; return true; }); }

  return {
    VERSION: VERSION, DATA_AS_OF: DATA_AS_OF, SKIP: SKIP,
    QUESTIONS: QUESTIONS, THEMES: THEMES, TIERS: TIERS, BENEFITS: BENEFITS,
    getVisibleQuestions: getVisibleQuestions, pruneAnswers: pruneAnswers, isComplete: isComplete,
    deriveFacts: deriveFacts, calcStrSara: calcStrSara, evaluate: evaluate,
    _test: test
  };
});
````
