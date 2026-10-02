/* Export the brain as one Markdown hand-over: everything a developer (or another skill, such as
 * tv3-interactive-embed in Claude Code) needs to build the checker, and nothing to build beyond it.
 *
 *   node scripts/export-brain-md.js [--brain scripts/belanjawan2026-brain.js]
 *        [--excluded references/excluded-2026.md] [--out BRAIN-2026.md]
 *   (defaults: the 2026 brain and exclusions; out = BRAIN-<year>.md next to SKILL.md)
 *
 * The file is generated from scripts/belanjawan2026-brain.js, the verified engine (test.js,
 * verify2.js), so the questions, rules, rates and Malay wording in it are exactly what the tests
 * check. Rates, reasons and advisory texts are produced by running the engine, not retyped.
 * The "not to be built" list comes from references/excluded-2026.md (annotate-source.js).
 */
'use strict';
const fs = require('fs');
const path = require('path');
const ROOT = path.join(__dirname, '..');
const arg = name => { const i = process.argv.indexOf(name); return i > -1 ? process.argv[i + 1] : undefined; };
const brainFile = path.resolve(arg('--brain') || path.join(__dirname, 'belanjawan2026-brain.js'));
const B = require(brainFile);
const YEAR = String(B.VERSION).slice(0, 4);
const out = path.resolve(arg('--out') || path.join(ROOT, `BRAIN-${YEAR}.md`));
const controlsFile = path.join(ROOT, 'references', 'output-controls.md');
const engineSrc = fs.readFileSync(brainFile, 'utf8');
const excludedFile = path.resolve(arg('--excluded') || path.join(ROOT, 'references', `excluded-${YEAR}.md`));

const opName = { eq: '=', ne: '≠', in: 'is one of', nin: 'is not one of', gte: '≥', gt: '>', lte: '≤', lt: '<', has: 'includes', hasAny: 'includes any of' };
function expr(c) {
  if (c.all) return c.all.map(x => (x.any ? `(${expr(x)})` : expr(x))).join(' AND ');
  if (c.any) return c.any.map(x => (x.all ? `(${expr(x)})` : expr(x))).join(' OR ');
  if (c.not) return `NOT (${expr(c.not)})`;
  const op = Object.keys(opName).find(k => k in c);
  let v = c[op];
  v = Array.isArray(v) ? '[' + v.map(x => `\`${x}\``).join(', ') + ']' : (typeof v === 'string' ? `\`${v}\`` : v);
  return `\`${c.f}\` ${opName[op]} ${v}`;
}
function whys(c, acc = []) {
  if (c.all) c.all.forEach(x => whys(x, acc)); else if (c.any) c.any.forEach(x => whys(x, acc));
  else if (c.not) whys(c.not, acc); else if (c.why) acc.push(c.why);
  return [...new Set(acc)];
}
function factsUsed(c, acc = new Set()) {
  if (c.all) c.all.forEach(x => factsUsed(x, acc)); else if (c.any) c.any.forEach(x => factsUsed(x, acc));
  else if (c.not) factsUsed(c.not, acc); else acc.add(c.f);
  return acc;
}
const cell = s => String(s == null ? '' : s).replace(/\|/g, '\\|').replace(/\n/g, ' ');
const rm = n => 'RM' + Number(n).toLocaleString('en-US', { maximumFractionDigits: 2 });

/* ---- derived facts: how each fact used by a rule or a question comes from the answers ---- */
const FACTS = {
  age: 'The `age` answer as a number.',
  adult: '`age` ≥ 18.',
  region: 'The `region` answer.',
  eastMalaysia: '`region` is not `semenanjung` (Sabah, Sarawak or Labuan).',
  marital: 'The `marital` answer. Skipped → unknown.',
  minorChildren: '`has_minor_children` = `yes` (has children aged 17 and below). `no`, or not asked → false. Skipped → unknown.',
  childCount: 'Number of children aged 17 and below: 0 when `minorChildren` is false; otherwise the `children` answer as a number (`1-2` → 1, `3-4` → 3, `5+` → 5). Skipped (either question) → unknown. STR uses this count.',
  hasChildren: 'true when `minorChildren` is true or any `child_stages` is chosen; false when `minorChildren` is false. Skipped `has_minor_children` → unknown.',
  childrenSkipped: '`has_minor_children` was skipped, or it was `yes` and `children` was skipped.',
  childStages: 'The `child_stages` answers, without `none`/`skip`.',
  isSchoolPupil: '`child_stages` includes `primary` or `secondary`, or the person is under 18 and answered `self_school` = `yes`.',
  income: 'The `income` band value. Skipped → unknown.',
  incomeSkipped: '`income` was skipped.',
  incomeMax: 'Upper end of the `income` band in RM: `lt2500` 2,500; `2501_5000` 5,000; `5001_6000` 6,000; `6001_12000` 12,000; `gt12000` no limit. Skipped → unknown.',
  b40: 'Income band upper end ≤ RM5,000 (approximates B40). Skipped income → unknown.',
  b40m40: 'Income band upper end ≤ RM12,000 (approximates B40 + M40). Skipped income → unknown.',
  ekasih: 'false if income is above RM5,000; otherwise the `ekasih` answer (`yes` → true, `no` → false). `unsure` or skipped → unknown. Not asked and income skipped → unknown.',
  employment: 'The `employment` answer. Skipped → unknown.',
  farmType: 'The `farm_type` answer. Skipped → unknown.',
  gender: 'The `gender` answer. Skipped → unknown.',
  assets: 'The `assets` answers, without `none`/`skip`.',
  status: 'The `status` answers, without `none`/`skip`.',
  lifestyle: 'The `lifestyle` answers, without `none`/`skip`.',
  smoker: '`lifestyle` includes any of `cigarette`, `cigar`, `heated_tobacco`, `vape`.',
  ipt: 'true if `status` includes `child_ipt` or `employment` = `student_ipt`; unknown if employment was skipped; otherwise false.',
  kwspMember: 'The `kwsp` answer (`yes` → true, `no` → false). If `kwsp` was skipped or not asked: guessed from `employment` (true for `employed_private`, `gig_ehailing`, `self_employed`, `housewife`, `jobseeker`, `fisher`, `farmer`); unknown if employment was also skipped.',
  oku: 'The `oku` answer: `yes` → true, `no` or not asked → false, skipped → unknown.',
  license: 'The `license` answer: `yes` → true, `no` or not asked → false, skipped → unknown.',
  ptptnBorrower: 'The `ptptn` answer: `yes` → true, `no` or not asked → false, skipped → unknown.',
  strRecipient: '`str_status` = `yes` (the reader says they receive STR or SARA). Used with `strEligible` for the cards meant for STR recipients.',
  strEligible: 'Result of the STR calculator below: true, false, or unknown when the calculator cannot decide.',
  strCategory: 'STR category from the calculator: `isi_rumah`, `warga_emas` or `bujang`.',
};
const used = new Set();
B.BENEFITS.forEach(b => factsUsed(b.when, used));
B.QUESTIONS.forEach(q => q.showIf && factsUsed(q.showIf, used));
const undocumented = [...used].filter(f => !FACTS[f]);
if (undocumented.length) { console.error('export-brain-md: facts used by rules but not documented: ' + undocumented.join(', ')); process.exit(1); }

/* ---- STR/SARA rates and reasons, produced by running the calculator ---- */
const facts = o => Object.assign(B.deriveFacts({ age: 35, region: 'semenanjung', marital: 'married', children: '0', income: 'lt2500', ekasih: 'no' }), o);
const strRows = [];
for (const income of ['lt2500', '2501_5000']) {
  const band = income === 'lt2500' ? 'RM2,500 dan ke bawah' : 'RM2,501 hingga RM5,000';
  for (const [children, label] of [['0', 'Tiada anak'], ['1-2', '1–2 anak'], ['3-4', '3–4 anak'], ['5+', '5 anak atau lebih']]) {
    const s = B.calcStrSara(B.deriveFacts({ age: 35, region: 'semenanjung', marital: 'married', has_minor_children: children === '0' ? 'no' : 'yes', children, income, ekasih: 'no' }));
    strRows.push(`| Isi Rumah | ${band} | ${label} | ${rm(s.str)} | ${rm(s.sara)} (${rm(s.saraMonthly)} sebulan) | ${rm(s.total)} |`);
  }
}
for (const income of ['lt2500', '2501_5000']) {
  const s = B.calcStrSara(B.deriveFacts({ age: 65, region: 'semenanjung', marital: 'single', children: '0', income, ekasih: 'no' }));
  strRows.push(`| Warga Emas Tiada Pasangan (60+) | ${income === 'lt2500' ? 'RM2,500 dan ke bawah' : 'RM2,501 hingga RM5,000'} | — | ${rm(s.str)} | ${rm(s.sara)} (${rm(s.saraMonthly)} sebulan) | ${rm(s.total)} |`);
}
{
  const s = B.calcStrSara(B.deriveFacts({ age: 30, region: 'semenanjung', marital: 'single', children: '0', income: 'lt2500', ekasih: 'no' }));
  strRows.push(`| Bujang (21–59) | RM2,500 dan ke bawah | — | ${rm(s.str)} | ${rm(s.sara)} (${rm(s.saraMonthly)} sebulan) | ${rm(s.total)} |`);
}
const topup = {};
for (const [cat, a] of [['Isi Rumah', { age: 35, marital: 'married', children: '0' }], ['Warga Emas Tiada Pasangan', { age: 65, marital: 'single', children: '0' }], ['Bujang', { age: 30, marital: 'single', children: '0' }]]) {
  const base = { region: 'semenanjung', income: 'lt2500', ...a };
  const no = B.calcStrSara(B.deriveFacts({ ...base, ekasih: 'no' })), yes = B.calcStrSara(B.deriveFacts({ ...base, ekasih: 'yes' }));
  topup[cat] = { add: yes.sara - no.sara, monthly: yes.saraMonthly };
}
const reasons = [
  ['Under 18', facts({ age: 15 })],
  ['Marital status skipped', B.deriveFacts({ age: 35, region: 'semenanjung', marital: 'skip', children: '0', income: 'lt2500' })],
  ['Income skipped', B.deriveFacts({ age: 35, region: 'semenanjung', marital: 'married', children: '0', income: 'skip' })],
  ['Single, children question skipped', B.deriveFacts({ age: 35, region: 'semenanjung', marital: 'single', has_minor_children: 'skip', income: 'lt2500' })],
  ['Single, no children, aged 18–20', B.deriveFacts({ age: 19, region: 'semenanjung', marital: 'single', children: '0', income: 'lt2500' })],
  ['Household income above RM5,000', B.deriveFacts({ age: 35, region: 'semenanjung', marital: 'married', children: '0', income: '5001_6000' })],
  ['Single 60+, income above RM5,000', B.deriveFacts({ age: 65, region: 'semenanjung', marital: 'single', children: '0', income: '5001_6000' })],
  ['Single 21–59, income above RM2,500', B.deriveFacts({ age: 30, region: 'semenanjung', marital: 'single', children: '0', income: '2501_5000' })],
].map(([when, f]) => { const s = B.calcStrSara(f); return `| ${when} | ${s.eligible === null ? 'unknown' : 'not eligible'} | ${cell(s.reason)} |`; });

/* ---- advisories, texts taken from the engine ---- */
const adv = a => B.evaluate(a).advisories;
const base = { age: 35, region: 'semenanjung', marital: 'married', has_minor_children: 'yes', children: '1-2', child_stages: ['primary'], income: 'lt2500', ekasih: 'no', employment: 'employed_private', gender: 'male', assets: ['none'], status: ['none'], lifestyle: ['none'] };
const pick = (list, type, i = 0) => (list.filter(x => x.type === type)[i] || {}).text;
const advRows = [
  ['STR likely but the person said they don\'t receive it (`str_status` = `no`)', pick(adv({ ...base, str_status: 'no' }), 'action')],
  ['STR likely and `str_status` is `unsure` or skipped', pick(adv({ ...base, str_status: 'unsure' }), 'action')],
  ['`ekasih` answered `unsure`', pick(adv({ ...base, ekasih: 'unsure', str_status: 'yes' }), 'info')],
  ['Any question skipped. The text lists the skipped topics, joined with ", " (example: gender skipped; names below)', pick(adv({ ...base, gender: 'skip', str_status: 'yes' }), 'info')],
  ['Income above RM5,000, `taxpayer` not ticked and `assets` not skipped', pick(adv({ ...base, income: '6001_12000', str_status: 'yes' }), 'info')],
  ['Always, shown last', pick(adv({ ...base, str_status: 'yes' }), 'disclaimer')],
].map(([when, text]) => `| ${when} | ${cell(text)} |`);

// topic name used in that advisory for each skipped question, read back from the engine
const skipNames = B.QUESTIONS.filter(q => q.options && q.options.some(o => o.skip)).map(q => {
  const t = (adv({ ...base, str_status: 'yes', [q.id]: q.type === 'multi' ? ['skip'] : 'skip' }).find(x => /tidak menyatakan:/.test(x.text)) || {}).text;
  const m = t && t.match(/menyatakan: (.*?)\. Faedah/);
  return m ? `\`${q.id}\` → ${m[1]}` : null;
}).filter(Boolean);

/* ---- worked examples: expected results the build must reproduce ---- */
const EXAMPLES = [
  ['Ibu tunggal, 45, dua anak sekolah, pendapatan bawah RM2,500, eKasih tidak pasti, bekerja sendiri, merokok',
    { age: 45, region: 'semenanjung', gender: 'female', employment: 'self_employed', marital: 'single_parent', has_minor_children: 'yes', children: '3-4', child_stages: ['primary', 'secondary'], oku: 'no', license: 'yes', income: 'lt2500', ekasih: 'unsure', str_status: 'no', ptptn: 'no', kwsp: 'yes', assets: ['none'], status: ['none'], lifestyle: ['cigarette'] }],
  ['Penjawat awam, 34, berkahwin, anak bawah 6 tahun, RM2,501–5,000, peminjam PTPTN, pembayar cukai, rumah pertama, haji',
    { age: 34, region: 'semenanjung', gender: 'male', employment: 'civil_servant', marital: 'married', has_minor_children: 'yes', children: '1-2', child_stages: ['under6'], oku: 'no', license: 'yes', income: '2501_5000', ekasih: 'no', str_status: 'yes', ptptn: 'yes', kwsp: 'no', assets: ['first_home', 'taxpayer', 'haji_plan'], status: ['none'], lifestyle: ['skip'] }],
  ['Pesara Kerajaan, 67, Sabah, bujang, veteran',
    { age: 67, region: 'sabah', gender: 'male', employment: 'retired_gov', marital: 'single', has_minor_children: 'no', oku: 'no', license: 'yes', income: '2501_5000', ekasih: 'no', str_status: 'yes', ptptn: 'no', kwsp: 'no', assets: ['old_car'], status: ['veteran', 'pjm'], lifestyle: ['none'] }],
  ['Murid, 17, Sarawak',
    { age: 17, region: 'sarawak', self_school: 'yes', oku: 'no', license: 'no', assets: ['none'], status: ['none'] }],
  ['Pemandu e-hailing, 28, bujang, bawah RM2,500, peminjam PTPTN, vape dan alkohol',
    { age: 28, region: 'semenanjung', gender: 'male', employment: 'gig_ehailing', marital: 'single', has_minor_children: 'no', oku: 'no', license: 'yes', income: 'lt2500', ekasih: 'no', str_status: 'yes', ptptn: 'yes', kwsp: 'yes', assets: ['first_home', 'invest_bursa'], status: ['none'], lifestyle: ['vape', 'alcohol'] }],
  ['Petani, 50, pendapatan, jantina, OKU dan KWSP dilangkau',
    { age: 50, region: 'semenanjung', gender: 'skip', employment: 'farmer', farm_type: 'smallholder', marital: 'married', has_minor_children: 'no', oku: 'skip', license: 'yes', income: 'skip', str_status: 'unsure', ptptn: 'no', kwsp: 'skip', assets: ['none'], status: ['none'], lifestyle: ['none'] }],
  ['OKU, 30, pekerja swasta, pendapatan RM5,001–6,000, menyatakan dirinya penerima STR atau SARA',
    { age: 30, region: 'semenanjung', gender: 'female', employment: 'employed_private', marital: 'single', has_minor_children: 'no', oku: 'yes', license: 'no', income: '5001_6000', str_status: 'yes', ptptn: 'yes', kwsp: 'yes', assets: ['none'], status: ['none'], lifestyle: ['none'] }],
];
function exampleBlock([title, answers], i) {
  const r = B.evaluate(answers);
  const s = r.strSara;
  const lines = [`### Contoh ${i + 1}: ${title}`, '', '**Answers:** `' + JSON.stringify(answers) + '`', ''];
  if (s.eligible === true) {
    let t = `**STR + SARA:** ${s.label}. STR ${rm(s.str)}, SARA ${rm(s.sara)} (${rm(s.saraMonthly)} sebulan), jumlah ${rm(s.total)}`;
    if (s.totalRange) t += `; julat jumlah ${rm(s.totalRange[0])}–${rm(s.totalRange[1])}`;
    if (s.totalIfEkasih) t += `; jika berdaftar eKasih ${rm(s.totalIfEkasih)}`;
    lines.push(t + '.');
  } else lines.push(`**STR + SARA:** ${s.eligible === null ? 'unknown' : 'not eligible'}. "${s.reason}"`);
  lines.push('');
  for (const g of r.groups) lines.push(`- **${g.label}** (${g.count} cards, in this order): ${g.items.map(x => '`' + x.id + '`').join(', ')}`);
  lines.push(`- **Cards in the grid:** ${r.groups.reduce((n, g) => n + g.count, 0)} (plus the STR + SARA panel on top${r.results.some(x => x.id === 'str_sara') ? '' : ', which here shows the reason instead of amounts'})`, '');
  return lines.join('\n');
}

/* ---- assemble ---- */
const md = [];
md.push(`# Semak Faedah Belanjawan ${YEAR}: build spec (v${B.VERSION})`, '');
md.push(`> Generated from \`scripts/${path.basename(brainFile)}\` by \`scripts/export-brain-md.js\` (brain data as of ${B.DATA_AS_OF}). Don't edit this file by hand: change the brain, run the tests, and regenerate.`, '');
md.push('## How to use this file', '');
md.push(`This is the complete specification of the citizen-benefits checker for Ucapan Belanjawan ${YEAR}. Hand it to Claude Code (for example with the \`tv3-interactive-embed\` skill) to build the checker.`, '');
md.push('- **Run the engine; don\'t rewrite it.** The tested engine is included in full in the appendix. Put it in the page as-is, inside a `<script>`, and drive the questions and results from its API ("Using the engine" below). Sections 1 to 7 describe what the engine does, to help you design the screens and check the result. Don\'t re-implement them.');
md.push('- **Follow the output controls.** They say which parts of the results screen are fixed and which are yours to design.');
md.push('- **Use the Malay text as written.** Every question, rule, rate and sentence comes from the speech and its annexes and has passed the engine\'s tests.');
md.push('- **Never invent or approximate a figure.** If something you need is not in this file, ask the user.');
md.push('- **Build nothing from "Not to be built"** at the end of the file. Each item there was read in the speech and left out on purpose.');
md.push('- **Check your build with the worked examples.** Enter each example\'s answers through your screens; the results must match.');
md.push(`- **Size:** ${B.QUESTIONS.length} questions, ${B.THEMES.length} themes, ${B.BENEFITS.length} result cards, one STR + SARA calculator.`, '');

md.push('## Using the engine', '');
md.push('The engine is plain ES5 JavaScript with no dependencies (about ' + Math.round(engineSrc.length / 1024) + ' KB). Paste the appendix code into a `<script>` before your own script; it defines `window.B26Brain` (in Node, `require()` returns the same object).', '');
md.push('| Call | Returns |', '|---|---|');
md.push('| `B26Brain.getVisibleQuestions(answers)` | The questions to show now, in order, with branching applied. Each has `id`, `type` (`number`, `single`, `multi`), `text`, `help`, `options` (`v`, `l`, `exclusive`, `skip`). |');
md.push('| `B26Brain.pruneAnswers(answers)` | The answers with those to now-hidden questions removed. Call it after every answer. |');
md.push('| `B26Brain.evaluate(answers)` | The result: `strSara`, `byTheme`, `advisories`, `counts` (below). |');
md.push('| `B26Brain.GROUPS`, `B26Brain.TIERS`, `B26Brain.VERSION`, `B26Brain.DATA_AS_OF` | Results group headings, tier labels, version and data date. |', '');
md.push('Question loop:', '');
md.push('```js', 'let answers = {};', 'function next() {', '  const q = B26Brain.getVisibleQuestions(answers).find(q => answers[q.id] === undefined);', '  if (!q) return renderResults(B26Brain.evaluate(answers));', '  renderQuestion(q);', '}', 'function onAnswer(id, value) {            // value: number | string | string[]', '  answers = B26Brain.pruneAnswers({ ...answers, [id]: value });', '  next();', '}', '// Back: delete answers[lastId], then next().', '```', '');
md.push('Result of `evaluate()`:', '');
md.push('```js', '{', '  version, dataAsOf,', '  strSara: { eligible: true | false | null, category, label, str, sara, saraMonthly, total,', '            totalRange?, totalIfEkasih?, reason },      // reason: Malay sentence when not eligible / unknown', '  groups: [ { id: "layak" | "mungkin", label, count, items: [ card, ... ] } ],   // the results grid, in order; STR + SARA is not in it',
  '  // card: { id, title, value, summary, reasons: [...], needsConfirm: [...], timing, tier, kind, theme, who, action, src, portal }',
  '  byTheme: [ ... ],                     // the same cards grouped by theme; not used on the results screen', '  advisories: [ { type: "action" | "info" | "disclaimer", text } ],   // disclaimer is last', '  counts: { total, layak, semak, mungkin }', '}', '```', '');

if (fs.existsSync(controlsFile)) {
  md.push('## Output controls', '');
  md.push(fs.readFileSync(controlsFile, 'utf8').replace(/^# .*\n+/, '').replace(/ This file is copied into[^\n]*/, '').replace(/^## /gm, '### ').replace(/\{\{YEAR\}\}/g, YEAR).trim(), '');
}

md.push('## 1. Question flow', '');
md.push('- Ask the questions in the order listed. Show a question only when its "Shown when" condition is true (conditions use the derived facts in section 3, computed from the answers so far).');
md.push(`- Every question except those marked required and the age question gets an extra option \`skip\` "${B.QUESTIONS.find(q => q.options && q.options.some(o => o.skip)).options.find(o => o.skip).l}", which can be shown as a separate "Langkau" link.`);
md.push('- In a multi-select, an option marked *exclusive* clears every other selection.');
md.push('- When a change of answer hides a question, drop that question\'s answer.');
md.push('- Back navigation: remove the last answer and show that question again.', '');

md.push(`## 2. Questions (${B.QUESTIONS.length})`, '');
md.push('| # | id | Type | Question (Malay, as shown) | Shown when | Options: value → label |', '|---|---|---|---|---|---|');
B.QUESTIONS.forEach((q, i) => {
  const opts = q.options ? q.options.map(o => `\`${o.v}\` → ${cell(o.l)}${o.exclusive ? ' *(exclusive)*' : ''}`).join('<br>') : `number, ${q.min} to ${q.max}`;
  const text = cell(q.text) + (q.help ? `<br>*Help:* ${cell(q.help)}` : '') + (q.required ? '<br>*(required)*' : '');
  md.push(`| ${i + 1} | \`${q.id}\` | ${q.type} | ${text} | ${q.showIf ? expr(q.showIf) : 'always'} | ${opts} |`);
});
md.push('');

md.push('## 3. Derived facts', '');
md.push('Rules and "Shown when" conditions test these facts, not the raw answers. A fact is **unknown** when the answer it depends on was skipped (or answered "Tidak pasti"); a fact that simply does not apply (for example, `ekasih` for someone earning above RM5,000) is **false**, not unknown.', '');
md.push('| Fact | How it is worked out |', '|---|---|');
Object.keys(FACTS).forEach(k => md.push(`| \`${k}\` | ${FACTS[k]} |`));
md.push('');

md.push('## 4. How a rule becomes a card', '');
md.push('Each card has a rule (`when`). Evaluate it with three-valued logic:', '');
md.push('- A test on a known fact is true or false. A test on an unknown fact is **unknown**. A test on a missing fact that is not unknown is false.');
md.push('- `AND`: false if any part is false; otherwise unknown if any part is unknown; otherwise true.');
md.push('- `OR`: true if any part is true; otherwise unknown if any part is unknown; otherwise false.');
md.push('- `NOT`: swaps true and false; unknown stays unknown.', '');
md.push('Then:', '');
md.push('| Rule result | Certainty | Card tier | Results group |', '|---|---|---|---|');
md.push(`| false | any | not shown | — |`);
md.push(`| true | \`high\` | \`layak\` | ${B.GROUPS[0].label} |`);
md.push(`| true | \`check\` | \`semak\` | ${B.GROUPS[1].label} |`);
md.push(`| unknown | any | \`mungkin\` | ${B.GROUPS[1].label} |`, '');
md.push('Cost changes (cards of kind `kesan`, such as tobacco or alcohol duty) follow the same table and are shown like any other card, with no warning label.', '');
md.push('- **"Kenapa anda layak":** list the `why` labels of the conditions that were true (shown with each rule below).');
md.push('- **"Perlu disahkan":** for a `mungkin` card, list the `why` labels of the conditions that were unknown.');
md.push(`- **Groups:** \`evaluate().groups\` gives the results grid ready to show: "${B.GROUPS[0].label}" (layak cards), then "${B.GROUPS[1].label}" (semak cards, then mungkin cards), each in catalogue order. The STR + SARA card is not in the groups; it is the panel on top. Themes are not shown.`, '');

md.push('## 5. STR + SARA calculator', '');
md.push('Shown as its own card first, and also as the `str_sara` card in the cash theme. Source: Perenggan 158–161; Lampiran I Bil. 29.', '');
md.push('**Category:**', '');
md.push('1. Under 18: not eligible (counted as a dependant).');
md.push('2. `marital` = `married` or `single_parent` → **Isi Rumah**.');
md.push('3. Otherwise, any children → **Isi Rumah**; no children and aged 60+ → **Warga Emas Tiada Pasangan**; no children and aged 21–59 → **Bujang**; aged 18–20 → not eligible.', '');
md.push('**Rates (per year, before the eKasih top-up):**', '');
md.push('| Category | Monthly household income | Children | STR | SARA | Total |', '|---|---|---|---|---|---|');
strRows.forEach(r => md.push(r));
md.push('');
md.push('Income above these bands → not eligible for that category.', '');
md.push(`**eKasih top-up** (when \`ekasih\` is true): SARA rises by ${rm(topup['Isi Rumah'].add)} a year for Isi Rumah (to ${rm(topup['Isi Rumah'].monthly)} a month), ${rm(topup['Warga Emas Tiada Pasangan'].add)} for Warga Emas (to ${rm(topup['Warga Emas Tiada Pasangan'].monthly)} a month) and ${rm(topup.Bujang.add)} for Bujang (to ${rm(topup.Bujang.monthly)} a month). When \`ekasih\` is unknown, show the total without the top-up and also the total "jika berdaftar eKasih".`, '');
md.push('**Children question skipped** (Isi Rumah): show a range from the 0-children rate to the 5+ rate. Children means children aged 17 and below (the `has_minor_children` question); answering "Tidak" uses the 0-children rate.', '');
md.push('**When not eligible or unknown, show this reason (Malay, as written):**', '');
md.push('| Situation | Result | Reason shown |', '|---|---|---|');
reasons.forEach(r => md.push(r));
md.push('');

md.push('## 6. Advisories', '');
md.push('Shown above or below the results, in this order. The disclaimer is always last.', '');
md.push('| When | Text (Malay, as written) |', '|---|---|');
advRows.forEach(r => md.push(r));
md.push('', '**Topic names in the skipped-questions advisory:** ' + skipNames.join('; ') + '.', '');

md.push(`## 7. Result cards (${B.BENEFITS.length})`, '');
md.push('What each card shows, and when, is set by the output controls ("Results screen"). This list is the full content of every card, for reference. Themes are listed here only to organise the catalogue; they are not shown to the reader.', '');
B.THEMES.forEach(t => {
  const items = B.BENEFITS.filter(b => b.theme === t.id);
  md.push(`### ${t.label} (\`${t.id}\`, ${items.length})`, '');
  items.forEach(b => {
    md.push(`#### \`${b.id}\`: ${b.title}`, '');
    md.push(`- **Kind:** \`${b.kind}\`${b.kind === 'kesan' ? ' (a cost change; shown like any other card)' : ''}; **certainty:** \`${b.certainty}\``);
    if (b.compute) md.push(`- **Value:** computed by the STR + SARA calculator (section 5)`);
    else md.push(`- **Value:** ${b.value}`);
    md.push(`- **Summary:** ${b.summary}`);
    md.push(`- **Who:** ${b.who}`);
    md.push(`- **Action:** ${b.action}`);
    md.push(`- **Rule:** ${expr(b.when)}`);
    const w = whys(b.when); if (w.length) md.push(`- **Why labels:** ${w.map(x => `"${x}"`).join('; ')}`);
    if (b.timing) md.push(`- **Timing:** ${b.timing}`);
    md.push(`- **Source:** ${b.src}${b.web ? ` (some figures on this card come from ${b.web}, checked before the brain moved to text-only sources)` : ''}`);
    if (b.portal) md.push(`- **Link:** ${b.portal}`);
    md.push('');
  });
});

md.push('## 8. Worked examples (acceptance tests)', '');
md.push('Your build must produce exactly these results for these answers. They are computed by the engine.', '');
EXAMPLES.forEach((e, i) => md.push(exampleBlock(e, i)));

md.push('## 9. Known limits (tell the reader where relevant)', '');
md.push('- Income bands approximate B40 (up to RM5,000) and M40 (up to RM12,000).');
md.push('- The spouse\'s age is not asked, so a spouse aged 40+ does not trigger PeKa B40.');
md.push('- Bumiputera-only programmes are folded into broader cards, with the restriction stated in the text.');
md.push('- Langkawi residents can\'t be targeted (the region question has no Langkawi option); the vehicle-exemption cap is shown to Labuan residents and names Langkawi.');
md.push('- This is general guidance, not an official eligibility decision. Budget 2027 will supersede it.', '');

if (fs.existsSync(excludedFile)) {
  const ex = fs.readFileSync(excludedFile, 'utf8')
    .replace(/^# .*\n+/, '')
    .replace(/^Generated by .*\n+/m, '')
    .replace(/^### /gm, '#### ').replace(/^## /gm, '### ')
    .replace('Only the items in the brain file are to be built.', 'Only the cards in this file are to be built.');
  md.push('## 10. Not to be built', '');
  md.push(ex.trim(), '');
}

md.push('## Appendix: engine code', '');
md.push(`The complete engine, \`${path.basename(brainFile)}\` v${B.VERSION}, exactly as tested. Copy it unchanged.`, '');
let body = md.join('\n').replace(/\n{3,}/g, '\n\n');
body += '\n````js\n' + engineSrc.replace(/\s+$/, '') + '\n````\n';
fs.writeFileSync(out, body);
console.log(`wrote ${path.relative(process.cwd(), out)} (${B.QUESTIONS.length} questions, ${B.BENEFITS.length} cards, ${EXAMPLES.length} worked examples)`);
