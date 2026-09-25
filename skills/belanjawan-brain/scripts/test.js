/* Verification round 1: unit tests, personas, catalogue integrity, language lint. Run: node test.js */
const B = require('./belanjawan2026-brain.js');
let pass = 0, fail = 0; const fails = [];
function ok(name, cond, extra) { if (cond) pass++; else { fail++; fails.push(name + (extra ? '  ' + extra : '')); } }
function eq(name, got, exp) { ok(name, JSON.stringify(got) === JSON.stringify(exp), `got=${JSON.stringify(got)} exp=${JSON.stringify(exp)}`); }
const find = (r, id) => r.results.find(x => x.id === id);
function has(name, r, id, tier) { const x = find(r, id); ok(name, !!x && (!tier || x.tier === tier), x ? 'tier=' + x.tier : 'missing'); }
function not(name, r, id) { ok(name, !find(r, id)); }

/* ---- A. STR/SARA figures vs speech ---- */
const base = { age: 35, region: 'semenanjung', marital: 'married', children: '5+', income: 'lt2500', employment: 'employed_private', gender: 'male', assets: ['none'], status: ['none'], lifestyle: ['none'] };
let r = B.evaluate({ ...base, ekasih: 'yes' });
eq('A1 max RM4,600 (perenggan 159)', [r.strSara.str, r.strSara.sara, r.strSara.total], [2200, 2400, 4600]);
eq('A2 same household non-eKasih RM3,400', B.evaluate({ ...base, ekasih: 'no' }).strSara.total, 3400);
eq('A3 RM2,501–5,000 1–2 anak RM1,650', B.evaluate({ ...base, children: '1-2', income: '2501_5000', ekasih: 'no' }).strSara.total, 1650);
r = B.evaluate({ ...base, marital: 'single', children: '0', ekasih: 'no', age: 25 });
eq('A4 bujang 25', [r.strSara.str, r.strSara.sara, r.strSara.saraMonthly], [0, 600, 50]);
eq('A5 bujang 19 not eligible', B.evaluate({ ...base, marital: 'single', children: '0', ekasih: 'no', age: 19 }).strSara.eligible, false);
r = B.evaluate({ ...base, marital: 'single', children: '0', income: '2501_5000', ekasih: 'yes', age: 66 });
eq('A6 warga emas eKasih RM150/mo', [r.strSara.str, r.strSara.sara, r.strSara.saraMonthly], [600, 1800, 150]);
eq('A7 married 66 -> isi rumah', B.evaluate({ ...base, children: '0', income: '2501_5000', ekasih: 'no', age: 66 }).strSara.category, 'isi_rumah');
r = B.evaluate({ ...base, ekasih: 'unsure' });
eq('A8 eKasih unsure -> 3,400 / 4,600', [r.strSara.total, r.strSara.totalIfEkasih], [3400, 4600]);
eq('A9 income >5k not eligible', B.evaluate({ ...base, income: '5001_6000' }).strSara.eligible, false);
r = B.evaluate({ ...base, children: 'skip', ekasih: 'no' });
eq('A10 children skipped (married) -> STR range 1,900–3,400', r.strSara.totalRange, [1900, 3400]);
r = B.evaluate({ ...base, income: 'skip' });
eq('A11 income skipped -> STR unknown', r.strSara.eligible, null);
has('A12 income skipped -> PeKa not shown (under 40) / mySalam mungkin', r, 'mysalam', 'mungkin');
eq('A13 marital skipped -> STR unknown', B.evaluate({ ...base, marital: 'skip', ekasih: 'no' }).strSara.eligible, null);

/* ---- B. Branching ---- */
const ids = a => B.getVisibleQuestions(a).map(q => q.id);
eq('B1 minor question set', ids({ age: 15 }), ['age', 'region', 'self_school', 'assets', 'status']);
ok('B2 high income hides eKasih', !ids({ age: 40, income: '6001_12000' }).includes('ekasih'));
ok('B3 income skipped still asks eKasih', ids({ age: 40, income: 'skip' }).includes('ekasih'));
ok('B4 children skipped still asks child_stages', ids({ age: 40, children: 'skip' }).includes('child_stages'));
ok('B5 no children hides child_stages', !ids({ age: 40, children: '0' }).includes('child_stages'));
ok('B6 no grade/appointment question exists', !B.QUESTIONS.some(q => q.id === 'cs_grade'));
ok('B7 lifestyle hidden for minors', !ids({ age: 16 }).includes('lifestyle'));
eq('B8 prune drops stale eKasih', B.pruneAnswers({ age: 40, income: 'gt12000', ekasih: 'yes' }).ekasih, undefined);
ok('B9 every non-required question has a skip option',
  B.QUESTIONS.filter(q => !q.required && q.type !== 'number').every(q => q.options.some(o => o.v === 'skip' && o.exclusive)));
ok('B10 required questions are only age and region', B.QUESTIONS.filter(q => q.required).map(q => q.id).join() === 'age,region');

/* ---- C. Personas ---- */
// Mak Timah
r = B.evaluate({ age: 45, region: 'semenanjung', marital: 'single_parent', children: '3-4', child_stages: ['primary', 'secondary'], income: 'lt2500', ekasih: 'unsure', str_status: 'no', employment: 'self_employed', gender: 'female', assets: ['license'], status: ['none'], lifestyle: ['cigarette'] });
has('C1 PeKa B40', r, 'peka_b40', 'layak'); has('C2 KasihnITA', r, 'kasihnita', 'semak'); has('C3 BAP', r, 'bap', 'layak');
has('C4 rebat elektrik mungkin', r, 'rebat_elektrik', 'mungkin'); has('C5 rokok kesan', r, 'duti_rokok', 'kesan');
has('C6 berhenti merokok', r, 'berhenti_merokok', 'layak'); not('C7 no alcohol', r, 'duti_alkohol'); not('C8 no tax', r, 'tax_vaksin');
ok('C9 apply-STR advisory', r.advisories.some(a => a.type === 'action'));
// Encik Razak, civil servant (no grade asked)
r = B.evaluate({ age: 34, region: 'semenanjung', marital: 'married', children: '1-2', child_stages: ['under6'], income: '2501_5000', ekasih: 'no', str_status: 'yes', employment: 'civil_servant', gender: 'male', assets: ['license', 'first_home', 'taxpayer', 'haji_plan'], status: ['none'], lifestyle: ['skip'] });
has('C10 BKK penjawat semak', r, 'bkk_penjawat', 'semak'); has('C11 LPPSA semak', r, 'lppsa', 'semak');
has('C12 kontrak awam semak', r, 'rumah_kontrak_awam', 'semak'); has('C13 Step-Up', r, 'step_up', 'layak');
has('C14 GCR haji', r, 'gcr_haji'); not('C15 no KWSP haji (civil servant not KWSP)', r, 'kwsp_haji');
ok('C16 lifestyle skip advisory', r.advisories.some(a => /gaya hidup/.test(a.text)));
// Pak Ali
r = B.evaluate({ age: 67, region: 'sabah', marital: 'single', children: '0', income: '2501_5000', ekasih: 'no', str_status: 'yes', employment: 'retired_gov', gender: 'male', assets: ['license', 'old_car'], status: ['veteran', 'pjm'], lifestyle: ['none'] });
eq('C17 warga emas RM1,200', [r.strSara.category, r.strSara.total], ['warga_emas', 1200]);
has('C18 PJM', r, 'pjm'); has('C19 RAS', r, 'ras'); not('C20 no diesel RM200 in Sabah', r, 'diesel_rm200');
// Student 17
r = B.evaluate({ age: 17, region: 'sarawak', self_school: 'yes', assets: ['none'], status: ['none'] });
has('C21 BAP', r, 'bap'); has('C22 MyLesen', r, 'mylesen_b2'); eq('C23 zero mungkin', r.counts.mungkin, 0);
not('C24 no fi klinik for minor', r, 'fi_klinik_swasta');
// e-hailing
r = B.evaluate({ age: 28, region: 'semenanjung', marital: 'single', children: '0', income: 'lt2500', ekasih: 'no', str_status: 'yes', employment: 'gig_ehailing', gender: 'male', assets: ['license', 'first_home', 'invest_bursa'], status: ['none'], lifestyle: ['vape', 'alcohol'] });
has('C25 i-Saraan Plus', r, 'i_saraan_plus'); not('C26 not plain i-Saraan', r, 'i_saraan');
has('C27 vape kesan', r, 'vape', 'kesan'); has('C28 alcohol kesan', r, 'duti_alkohol', 'kesan'); has('C29 ETF', r, 'pelabur_runcit');
// Housewife eKasih
r = B.evaluate({ age: 38, region: 'semenanjung', marital: 'married', children: '3-4', child_stages: ['under6', 'primary', 'ipt'], income: 'lt2500', ekasih: 'yes', str_status: 'yes', employment: 'housewife', gender: 'female', assets: ['haji_plan'], status: ['pregnant', 'oku_child'], lifestyle: ['none'] });
has('C30 i-Suri', r, 'i_suri', 'layak'); has('C31 PTPTN percuma', r, 'ptptn_percuma'); has('C32 KWSP haji', r, 'kwsp_haji');
eq('C33 SARA RM200/mo', r.strSara.saraMonthly, 200);
// Farmer skipped type
r = B.evaluate({ age: 50, region: 'semenanjung', marital: 'married', children: '0', income: 'lt2500', ekasih: 'no', str_status: 'yes', employment: 'farmer', farm_type: 'skip', gender: 'skip', assets: ['none'], status: ['none'], lifestyle: ['none'] });
has('C34 pesawah mungkin', r, 'pesawah', 'mungkin'); has('C35 pekebun kecil mungkin', r, 'pekebun_kecil', 'mungkin');
not('C36 gender skipped: no i-Suri etc. certain', r, 'kasihnita');

/* ---- D. Catalogue integrity ---- */
const themes = B.THEMES.map(t => t.id);
const idsAll = B.BENEFITS.map(b => b.id);
ok('D1 unique ids', new Set(idsAll).size === idsAll.length);
const factKeys = Object.keys(B.deriveFacts({ age: 30 }));
function leaves(c, out = []) { if (c.all) c.all.forEach(x => leaves(x, out)); else if (c.any) c.any.forEach(x => leaves(x, out)); else if (c.not) leaves(c.not, out); else out.push(c.f); return out; }
B.BENEFITS.forEach(b => {
  ok('D2 theme ' + b.id, themes.includes(b.theme));
  ok('D3 kind ' + b.id, ['manfaat', 'kesan'].includes(b.kind));
  ok('D4 certainty ' + b.id, ['high', 'check'].includes(b.certainty));
  ok('D5 fields ' + b.id, ['title', 'value', 'summary', 'who', 'action', 'src'].every(k => typeof b[k] === 'string' && b[k].length > 3));
  leaves(b.when).forEach(f => ok(`D6 fact exists ${b.id}.${f}`, factKeys.includes(f)));
});
B.QUESTIONS.forEach(q => q.showIf && leaves(q.showIf).forEach(f => ok(`D7 showIf fact ${q.id}.${f}`, factKeys.includes(f))));
ok('D8 every theme used', themes.every(t => B.BENEFITS.some(b => b.theme === t)));

/* ---- E. Language & content lint (citizen-facing strings) ---- */
const strings = [];
B.QUESTIONS.forEach(q => { strings.push(['Q:' + q.id, q.text], ['Q:' + q.id + ':help', q.help || '']); (q.options || []).forEach(o => strings.push(['Q:' + q.id + ':' + o.v, o.l])); });
B.BENEFITS.forEach(b => ['title', 'value', 'summary', 'who', 'action', 'timing'].forEach(k => b[k] && strings.push([b.id + '.' + k, b[k]])));
const banned = [/makan gaji/i, /\bfreelance\b/i, /\bdll\b/i, /\bTT ?2026\b/, /mahu nyatakan/i, /Dikira — lihat/, /strSara/, /\bskim tu\b/i, /\bkat\b/i, /\bnak\b/i, /\bdorang\b/i,
  /masalah pembelajaran/i, /\bdari RM/, /\bdari perniagaan/, /^Automatik untuk/, /teksi atau kereta sewa/, /(?<!tok )\bsiak\b/, /\b[2-9] (jenis|tahun pertama)\b/];
strings.forEach(([k, s]) => banned.forEach(re => ok(`E1 banned phrase ${re} in ${k}`, !re.test(s), s)));
// Government spending figures must not appear in what the person gets / reads as summary
const spend = [/bilion/i, /\bperuntukan\b/i, /\d[\d.,]* (ribu |juta )?(murid|penerima|peserta|pelajar|belia|unit|pesawah|pemandu|pemilik|isi rumah)\b/i, /RM\d+(\.\d+)? juta(?! ?\))/];
const allowJuta = { 'pembiayaan_wanita.value': 1, 'pembiayaan_wanita.summary': 1, 'lppsa.value': 1 }; // personal loan limits, not allocations
B.BENEFITS.forEach(b => ['value', 'summary', 'who'].forEach(k => spend.forEach(re => {
  if (allowJuta[b.id + '.' + k] && String(re).includes('juta')) return;
  ok(`E2 spending figure ${re} in ${b.id}.${k}`, !re.test(b[k]), b[k]);
})));

console.log(`Verification round 1: ${pass} passed, ${fail} failed.`);
fails.forEach(f => console.log('  FAIL ' + f));
console.log(`Catalogue: ${B.BENEFITS.length} items in ${B.THEMES.length} themes; ${B.QUESTIONS.length} questions.`);
process.exit(fail ? 1 : 0);
