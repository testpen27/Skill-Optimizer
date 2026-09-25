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
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.B26Brain = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var VERSION = '2026.3';
  var DATA_AS_OF = '2026-09-25';
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
      summary: 'Melalui HRD Corp, pembiayaan PTPK (terutamanya bidang AI, kenderaan elektrik dan semikonduktor), GiatMARA (termasuk untuk pekerja gig) dan Kolej Komuniti (program pembelajaran sepanjang hayat untuk OKU, warga emas, ibu tunggal dan Orang Asli).',
      who: 'Pencari kerja, pekerja gig, mereka yang bekerja sendiri dan golongan rentan.',
      action: 'Mohon melalui HRD Corp, PTPK, GiatMARA atau Kolej Komuniti.',
      when: { any: [{ f: 'employment', in: ['jobseeker', 'gig_ehailing', 'self_employed', 'retired_other', 'housewife'], why: 'Mencari kerja atau bekerja sendiri' },
        C.okuSelf, { f: 'marital', eq: 'single_parent', why: 'Ibu atau bapa tunggal' }, { f: 'status', has: 'orang_asli', why: 'Orang Asli' }] },
      certainty: 'check', src: 'Perenggan 65, ms 50–51' },

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
      src: 'Lampiran II — Lampiran 7, ms 321–322' }
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
