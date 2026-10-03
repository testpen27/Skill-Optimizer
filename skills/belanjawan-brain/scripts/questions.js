#!/usr/bin/env node
/* Question-set approval: the user approves every question, its wording and its options before a hand-over.
 *
 *   node scripts/questions.js                        print the question set for review (Markdown), marking
 *                                                    what changed since the last approval
 *   node scripts/questions.js --out review.md        the same, written to a file
 *   node scripts/questions.js --set <id> "text"      reword a question
 *   node scripts/questions.js --set <id>.help "text" reword its help line
 *   node scripts/questions.js --set <id>.<v> "text"  reword one option label (v = the option value, e.g. kwsp.yes)
 *   node scripts/questions.js --approve [--note "…"] record the current set as approved by the user
 *   node scripts/questions.js --check                exit 1 unless the current set is the approved one
 *
 * --set edits the engine (scripts/belanjawan2026-brain.js) in place. Rewording only changes text; to add,
 * remove or reorder questions or options, edit the engine and run the tests.
 * Approvals are kept in references/questions-approved.json. Run --approve only after the user has said yes.
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const args = process.argv.slice(2);
const arg = k => { const i = args.indexOf(k); return i > -1 ? args[i + 1] : undefined; };
const brainFile = path.resolve(arg('--brain') || path.join(__dirname, 'belanjawan2026-brain.js'));
const approvedFile = path.resolve(arg('--approved') || path.join(ROOT, 'references', 'questions-approved.json'));

function load() { delete require.cache[require.resolve(brainFile)]; return require(brainFile); }

// The part of a question the user approves: wording, options and when it is shown.
function snapshot(B) {
  return B.QUESTIONS.map(q => {
    const o = { id: q.id, type: q.type, text: q.text };
    if (q.help) o.help = q.help;
    if (q.options) o.options = q.options.map(x => x.exclusive ? { v: x.v, l: x.l, exclusive: true } : { v: x.v, l: x.l });
    else { o.min = q.min; o.max = q.max; }
    if (q.showIf) o.showIf = q.showIf;
    return o;
  });
}
const readApproved = () => fs.existsSync(approvedFile) ? JSON.parse(fs.readFileSync(approvedFile, 'utf8')) : null;
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

function expr(c) {
  if (c.all) return c.all.map(x => (x.any ? '(' + expr(x) + ')' : expr(x))).join(' AND ');
  if (c.any) return c.any.map(expr).join(' OR ');
  if (c.not) return 'NOT (' + expr(c.not) + ')';
  const op = ['eq', 'ne', 'in', 'nin', 'gt', 'gte', 'lt', 'lte', 'has', 'hasAny'].find(k => k in c);
  const sym = { eq: '=', ne: '≠', in: 'in', nin: 'not in', gt: '>', gte: '≥', lt: '<', lte: '≤', has: 'includes', hasAny: 'includes any of' }[op];
  return `${c.f} ${sym} ${JSON.stringify(c[op])}`;
}

/* ---- review: the question set as the user sees it, with changes since the last approval ---- */
function review() {
  const B = load(), cur = snapshot(B), appr = readApproved();
  const old = appr ? Object.fromEntries(appr.questions.map(q => [q.id, q])) : {};
  const md = [];
  md.push(`# Question set for approval (v${B.VERSION})`, '');
  md.push(appr
    ? `Last approved: ${appr.date} (v${appr.version})${appr.note ? ': ' + appr.note : ''}. Changes since then are marked **BAHARU** (new) or **BERUBAH** (changed), with the approved wording shown as "Sebelum".`
    : 'This set has never been approved.', '');
  md.push(`${cur.length} questions. Every question shown must be answered; there is no skip option. Reply "lulus" to approve, or reword any line, e.g. \`S5: …\` for a question or \`S5 pilihan 2: …\` for an option.`, '');
  cur.forEach((q, i) => {
    const o = old[q.id];
    const tag = !appr ? '' : !o ? ' **BAHARU**' : same(o, q) ? '' : ' **BERUBAH**';
    md.push(`## S${i + 1}. ${q.text}${tag}`, '');
    if (o && o.text !== q.text) md.push(`Sebelum: ${o.text}`, '');
    if (q.help) md.push(`*Penerangan:* ${q.help}`, '');
    if (o && (o.help || '') !== (q.help || '')) md.push(`Sebelum: ${o.help || '(tiada penerangan)'}`, '');
    md.push(`- Id: \`${q.id}\`; ${q.type === 'number' ? `nombor ${q.min} hingga ${q.max}` : q.type === 'multi' ? 'pilih semua yang berkaitan' : 'pilih satu'}`);
    md.push(`- Ditanya: ${q.showIf ? '`' + expr(q.showIf) + '`' : 'semua orang'}${o && !same(o.showIf, q.showIf) ? ` (sebelum: ${o.showIf ? '`' + expr(o.showIf) + '`' : 'semua orang'})` : ''}`);
    if (q.options) {
      md.push('', '| # | Pilihan | Nilai |', '|---|---|---|');
      const prev = o && o.options ? Object.fromEntries(o.options.map(x => [x.v, x.l])) : null;
      q.options.forEach((x, j) => {
        let l = x.l + (x.exclusive ? ' *(membatalkan pilihan lain)*' : '');
        if (prev && !(x.v in prev)) l += ' **BAHARU**';
        else if (prev && prev[x.v] !== x.l) l += ` **BERUBAH** (sebelum: ${prev[x.v]})`;
        md.push(`| ${j + 1} | ${l} | \`${x.v}\` |`);
      });
      if (prev) Object.keys(prev).filter(v => !q.options.some(x => x.v === v)).forEach(v => md.push(`| – | ~~${prev[v]}~~ **DIBUANG** | \`${v}\` |`));
    }
    md.push('');
  });
  const gone = appr ? appr.questions.filter(q => !cur.some(x => x.id === q.id)) : [];
  if (gone.length) { md.push('## Soalan yang dibuang', ''); gone.forEach(q => md.push(`- ~~${q.text}~~ (\`${q.id}\`)`)); md.push(''); }
  return md.join('\n');
}

/* ---- reword: replace one string literal inside one question's block in the engine source ---- */
const lit = s => "'" + s.replace(/\\/g, '\\\\').replace(/'/g, "\\'") + "'";
function reword(target, value) {
  const [id, part] = target.split('.');
  const B = load();
  const q = B.QUESTIONS.find(x => x.id === id);
  if (!q) throw new Error(`No question with id "${id}". Ids: ${B.QUESTIONS.map(x => x.id).join(', ')}`);
  let src = fs.readFileSync(brainFile, 'utf8');
  const start = src.indexOf(`{ id: '${id}',`);
  const nextQ = src.indexOf('{ id: \'', start + 1);
  const listEnd = src.indexOf('\n  ];', start);
  const end = nextQ > -1 && nextQ < listEnd ? nextQ : listEnd;
  if (start < 0 || end < 0) throw new Error(`Couldn't find the block for "${id}" in ${brainFile}`);
  let block = src.slice(start, end), from, to;
  if (!part) { from = `text: ${lit(q.text)}`; to = `text: ${lit(value)}`; }
  else if (part === 'help') {
    if (!q.help) throw new Error(`"${id}" has no help line to reword; add one in the engine.`);
    from = `help: ${lit(q.help)}`; to = `help: ${lit(value)}`;
  } else {
    const o = (q.options || []).find(x => x.v === part);
    if (!o) throw new Error(`"${id}" has no option "${part}". Options: ${(q.options || []).map(x => x.v).join(', ')}`);
    from = `{ v: ${lit(o.v)}, l: ${lit(o.l)}`; to = `{ v: ${lit(o.v)}, l: ${lit(value)}`;
  }
  const n = block.split(from).length - 1;
  if (n !== 1) throw new Error(`Expected the old wording once in the "${id}" block, found it ${n} times: ${from}`);
  block = block.replace(from, () => to);
  fs.writeFileSync(brainFile, src.slice(0, start) + block + src.slice(end));
  const after = load().QUESTIONS.find(x => x.id === id);
  const got = !part ? after.text : part === 'help' ? after.help : after.options.find(x => x.v === part).l;
  if (got !== value) throw new Error('Reword did not take effect; check the engine source.');
  console.log(`${target}: "${!part ? q.text : part === 'help' ? q.help : q.options.find(x => x.v === part).l}" → "${value}"`);
}

/* ---- main ---- */
if (require.main === module) try {
  if (args.includes('--set')) {
    const i = args.indexOf('--set');
    if (args[i + 2] === undefined) throw new Error('Usage: --set <id>[.help|.<option>] "new text"');
    reword(args[i + 1], args[i + 2]);
    console.log('Now run: node scripts/test.js && node scripts/questions.js (show the user the set again)');
  } else if (args.includes('--approve')) {
    const B = load();
    const rec = { version: B.VERSION, date: new Date().toISOString().slice(0, 10), note: arg('--note') || '', questions: snapshot(B) };
    fs.writeFileSync(approvedFile, JSON.stringify(rec, null, 2) + '\n');
    console.log(`Recorded approval of ${rec.questions.length} questions (v${rec.version}, ${rec.date}) in ${path.relative(ROOT, approvedFile)}`);
  } else if (args.includes('--check')) {
    const appr = readApproved();
    if (!appr) { console.log('Question set has never been approved.'); process.exit(1); }
    if (!same(appr.questions, snapshot(load()))) { console.log(`Question set changed since the approval of ${appr.date}. Show it to the user (node scripts/questions.js) and record their approval.`); process.exit(1); }
    console.log(`Question set approved on ${appr.date}.`);
  } else {
    const out = review();
    if (arg('--out')) { fs.writeFileSync(arg('--out'), out + '\n'); console.log('wrote ' + arg('--out')); } else console.log(out);
  }
} catch (e) { console.error('questions.js: ' + e.message); process.exit(1); }

module.exports = { snapshot, readApproved, same };
