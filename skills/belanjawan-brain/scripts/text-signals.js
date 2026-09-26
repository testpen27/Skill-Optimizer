/* Text signals that a unit of a budget speech describes something a PERSON gets or pays.
 * Pure text matching, no network. Derived from Ucapan Belanjawan 2024–2026: the 2026 brain's
 * items were matched to the unit they came from, and these are the word groups that separate
 * those units from the rest (see references/text-signals.md for the numbers and how to extend).
 *
 * The score only orders the reading and flags risky exclusions. It never decides inclusion:
 * every unit still gets a ledger decision.
 */
'use strict';

const RECIPIENT_WORDS = 'individu|rakyat|isi rumah|keluarga|ibu bapa|ibu|bapa|anak|warga emas|pesara|OKU|kurang upaya|ibu tunggal|wanita|suri rumah|belia|anak muda|graduan|pelajar|murid|mahasiswa|penuntut|kanak-kanak|bayi|pekerja|pencari kerja|penjawat awam|kakitangan|anggota|veteran|nelayan|petani|pesawah|pekebun kecil|penoreh|peneroka|penternak|penjaja|peniaga kecil|usahawan|pemandu|gig|asnaf|miskin|B40|M40|golongan|Orang Asli|pembeli|pembayar cukai|pengguna|perokok|pesakit|pencarum|penerima|komuniti rentan|warganegara';
const RECIPIENT = new RegExp('\\b(' + RECIPIENT_WORDS + ')\\b', 'i');

const GROUPS = {
  // An amount one person receives or pays. "150 ringgit" (digits right before ringgit/sen) is
  // per-person; "13 bilion ringgit" is not.
  amount: /(\b\d[\d,.]*\s+(ringgit|sen)\b|\bRM\s?\d[\d,.]*(?![\d,.])(?!\s?(b|bil|bilion|j|juta)\b))/i,
  perPeriod: /\b(sebulan|setahun|seorang|sekali|setiap (bulan|tahun|orang|isi rumah|penerima|murid|pelajar|keluarga|batang|liter)|per (orang|isi rumah|batang|liter|kilogram|bulan|unit))\b/i,
  cap: /\bsehingga\s+(RM\s?\d|\d[\d,.]*\s+(ringgit|peratus|tahun))/i,
  // Tax and duty measures that land on individuals (and area-based exemptions).
  tax: /\b(pelepasan cukai|potongan cukai|cukai pendapatan individu|pengecualian (cukai|duti)|dikecualikan|duti setem|duti import|duti eksais|cukai jualan|cukai perkhidmatan|bebas cukai|bebas duti|tahun taksiran|taksiran)\b/i,
  // Who receives it.
  recipient: RECIPIENT,
  // Help pointed at a named group: "kepada 5,000 ibu tunggal", "untuk anak muda".
  targeted: new RegExp('\\b(untuk|kepada|bagi|buat|khusus)\\s+(\\S+\\s+){0,3}?(' + RECIPIENT_WORDS + ')\\b', 'i'),
  // How eligibility or delivery is described.
  eligibility: /\b(layak|kelayakan|yang layak|terhad|had|berumur|berusia|ke atas|ke bawah|berpendapatan|tidak melebihi|berdaftar|pemegang|menerima|diberikan|diberi|pemberian|bayaran|memohon|permohonan|mulai)\b/i,
  // Help going to people.
  benefit: /\b(bantuan|elaun|insentif|geran|rebat|diskaun|subsidi|bersubsidi|percuma|kebajikan|penyeragaman harga|harga sama|perlindungan|pengecualian|biasiswa|baucar|sumbangan|tunai|pinjaman|pembiayaan|jaminan|menjamin|saringan|rawatan|dibekalkan|harga lebih murah|peluang pekerjaan|latihan|khidmat guaman)\b/i,
  // An announcement of change (weak, but most citizen measures are phrased this way).
  change: /\b(dinaikkan|ditingkatkan|diperluas|dilanjutkan|diteruskan|dicadangkan|bersetuju|sukacita|diumumkan|diperkenalkan)\b/i,
  // A cost or new obligation for the person (kesan items). "naik taraf" (upgrade) is excluded.
  cost: /\b(dinaikkan sebanyak|kenaikan|naik \d|naik sebanyak|dikenakan|pengenaan|larangan|mengharamkan|diharamkan|cukai baharu|tidak lagi (layak|diberi))\b/i,
  // Lifestyle items the user always wants covered; always reviewed.
  lifestyle: /\b(rokok|merokok|perokok|tembakau|cerut|cigar\w*|vape|rokok elektronik|nikotin|alkohol|beralkohol|minuman keras|minuman bergula|judi|loteri)\b/i,
  // Where a measure is limited to a place. Tagged, not scored on its own.
  area: /\b(Sabah|Sarawak|Labuan|Langkawi|Tioman|Pangkor|Kelantan|Terengganu|Pahang|Perlis|Kedah|Johor|Melaka|Pulau Pinang|Perak|Selangor|Negeri Sembilan|Putrajaya|Kuala Lumpur|pedalaman|luar bandar|pulau|sempadan|zon bebas)\b/i,
};

// Government-side or non-person language. Each lowers the score by one.
const NEGATIVE = {
  infra: /\b(naik taraf|jalan|sungai|bekalan air|lapangan terbang|pelabuhan|pembinaan|projek|jambatan|empangan|loji)\b/i,
  corporate: /\b(syarikat|pelaburan|pelabur institusi|dana|industri|sektor|GLIC|FDI|eksport|pengeluar)\b/i,
  macro: /\b(bilion|KDNK|defisit|hasil kerajaan|hutang|fiskal|unjuran)\b/i,
};

// Programme names learned from past speeches (scripts/learn-programmes.js). A unit that names
// a known citizen programme is flagged even when it says nothing else ("mySalam diperluas …").
let PROGRAMMES = null;
function programmeRegex() {
  if (PROGRAMMES !== null) return PROGRAMMES;
  try {
    const list = require('../references/programmes.json').programmes.map(p => p.name)
      .filter(n => n.length >= 3).sort((a, b) => b.length - a.length)
      .map(n => n.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    PROGRAMMES = list.length ? new RegExp('\\b(' + list.join('|') + ')\\b') : false;
  } catch (e) { PROGRAMMES = false; }
  return PROGRAMMES;
}

const WEIGHT = { programme: 1, targeted: 1, amount: 2, perPeriod: 2, cap: 1, tax: 2, lifestyle: 3, recipient: 1, eligibility: 1, benefit: 1, change: 1, cost: 1, area: 0 };

// Units at or above this score are "flagged": read them closely, and an exclusion needs a
// written reason. See references/text-signals.md for the recall this gives on the 2026 brain.
const FLAG_AT = 2;

function scoreUnit(text, part) {
  const signals = [];
  let score = 0;
  for (const k of Object.keys(GROUPS)) if (GROUPS[k].test(text)) { signals.push(k); score += WEIGHT[k]; }
  const prog = programmeRegex();
  const pm = prog && text.match(prog);
  if (pm) { signals.push('programme'); score += WEIGHT.programme; }
  const personal = signals.includes('amount') || signals.includes('perPeriod') || signals.includes('tax');
  for (const k of Object.keys(NEGATIVE)) if (NEGATIVE[k].test(text)) {
    signals.push('-' + k);
    if (personal && k === 'macro') continue;          // "RM13b for STR … RM100 a month each" is still personal
    if (signals.includes('targeted')) continue;       // help aimed at a named group outweighs a "projek"/"dana" mention
    score -= 1;   // "RM13b for STR … RM100 a month each" is still personal
  }
  if (signals.includes('area') && signals.includes('tax')) score += 2;       // area-based tax/duty exemption
  else if (signals.includes('area') && !signals.includes('-infra') &&
    (signals.includes('benefit') || signals.includes('targeted'))) score += 1; // help limited to a place
  if (part === 'lampiran2' && signals.includes('tax')) score += 1;           // every tax entry deserves a read
  return { signals, score, programme: pm ? pm[1] : undefined,
    flagged: score >= FLAG_AT || signals.includes('lifestyle') || (!!pm && score >= 1) };
}

// learn-programmes.js calls this so the list is learned from the other signals only, not from
// its own previous output.
function disableProgrammes() { PROGRAMMES = false; }

module.exports = { GROUPS, NEGATIVE, WEIGHT, FLAG_AT, scoreUnit, disableProgrammes };
