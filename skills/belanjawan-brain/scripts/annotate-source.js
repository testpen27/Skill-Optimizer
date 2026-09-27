/* Hand-over outputs from the ledger: the speech with every unit highlighted, and the list of
 * measures the calculator must not build.
 *
 *   node scripts/annotate-source.js <speech.md> <ledger.tsv> [--brain <brain.js>]
 *        [--out <dir>] [--pdf] [--excluded <excluded.md>]
 *
 * --out       writes <dir>/<speech>-annotated.html: the speech text, each unit shaded
 *             light green if the brain uses it (ledger item:…) and yellow if it was excluded,
 *             with the unit id and the decision in a tag. Text outside any unit (cover
 *             pages, headings) stays unshaded.
 * --pdf       also prints that page to <dir>/<speech>-annotated.pdf (Playwright + Chromium).
 * --excluded  writes the "do not build" list for whoever develops the calculator: every
 *             person-level measure that was read and left out (user decision, non-citizen,
 *             already past), then a count of everything else excluded, by reason.
 *
 * Text only, like the rest of the rebuild: it reads the speech file and the ledger, nothing else.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const { split } = require('./split-source.js');
const { readLedger } = require('./coverage.js');

const REASONS = {
  user: 'the user decided to leave it out',
  'non-citizen': 'for non-citizens or foreign companies',
  past: 'a one-off that has already ended',
  rhetoric: 'speech framing, history or thanks',
  heading: 'a heading or lead-in with no measure of its own',
  governance: 'law, enforcement, administration or fiscal policy',
  allocation: 'a government spending total or beneficiary count',
  infra: 'infrastructure, buildings or public works',
  business: 'a company, investor or employer incentive',
  institution: 'money to an agency, NGO, school or mosque, not to a person',
};
const PERSON_LEVEL = ['user', 'non-citizen', 'past'];

const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const clip = (s, n) => (s.length > n ? s.slice(0, n - 1).replace(/\s+\S*$/, '') + ' …' : s);

function load(speech, ledgerFile, brainFile) {
  const src = split(speech);
  const rows = new Map(readLedger(ledgerFile).filter(r => !r.unit.startsWith('prev:')).map(r => [r.unit, r]));
  let titles = new Map();
  if (brainFile) {
    const B = require(path.resolve(brainFile));
    titles = new Map(B.BENEFITS.map(b => [b.id, b.title]));
  }
  const units = src.units.map(u => {
    const r = rows.get(u.id) || { decision: '', note: '' };
    const [kind, arg = ''] = r.decision.split(':');
    const status = kind === 'item' ? 'used' : kind === 'exclude' || kind === 'bulk' ? 'excluded' : 'open';
    return { ...u, decision: r.decision, note: r.note, kind, arg, status,
      items: kind === 'item' ? arg.split(',').map(s => s.trim()).filter(Boolean) : [] };
  });
  return { src, units, titles };
}

function tagFor(u, titles) {
  if (u.status === 'used') {
    const names = u.items.map(id => titles.has(id) ? `${id} (${titles.get(id)})` : id);
    return `${u.id} · USED → ${names.join('; ')}`;
  }
  if (u.status === 'excluded') {
    const why = u.kind === 'bulk' ? 'not read closely (bulk)' : (REASONS[u.arg] || u.arg);
    return `${u.id} · EXCLUDED — ${why}${u.note && u.arg === 'user' ? ': ' + u.note : ''}`;
  }
  return `${u.id} · OPEN — ${u.decision || 'no ledger decision'}`;
}

function renderHtml(speech, units, titles, src) {
  const lines = fs.readFileSync(speech, 'utf8').replace(/\r/g, '').split('\n');
  const startAt = new Map(units.map(u => [u.line, u]));
  const out = [];
  let plain = [];
  const flushPlain = () => {
    const t = plain.join(' ').replace(/\s+/g, ' ').trim();
    if (t) out.push(`<p class="plain">${esc(t)}</p>`);
    plain = [];
  };
  for (let i = 1; i <= lines.length; i++) {
    const u = startAt.get(i);
    if (u) {
      flushPlain();
      const chunks = [[]];
      for (let k = u.line; k <= u.end; k++) {
        const l = lines[k - 1].replace(/^#{1,6}\s+/, '');
        if (!l.trim()) { if (chunks[chunks.length - 1].length) chunks.push([]); continue; }
        chunks[chunks.length - 1].push(l.trim());
      }
      const body = chunks.filter(c => c.length).map(c => esc(c.join(' '))).join('<br>');
      out.push(`<div class="u ${u.status}" id="${esc(u.id)}"><span class="tag">${esc(tagFor(u, titles))}</span>${body}</div>`);
      i = u.end;
      continue;
    }
    const h = lines[i - 1].match(/^(#{1,6})\s+(.*)$/);
    if (h) { flushPlain(); const n = Math.min(h[1].length + 1, 4); out.push(`<h${n}>${esc(h[2])}</h${n}>`); continue; }
    if (!lines[i - 1].trim()) { flushPlain(); continue; }
    plain.push(lines[i - 1].trim());
  }
  flushPlain();

  const n = s => units.filter(u => u.status === s).length;
  const title = `${src.year ? 'Ucapan Belanjawan ' + src.year : src.source.replace(/\.md$/, '')} — annotated`;
  return `<!doctype html>
<html lang="ms"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
<style>
  :root { --used: #c6efce; --used-edge: #6aa84f; --excl: #fff59d; --excl-edge: #d4b000; --open: #ffd8a8; }
  * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  body { font: 15px/1.55 Georgia, 'Times New Roman', serif; color: #1a1a1a; background: #fff; max-width: 820px; margin: 0 auto; padding: 24px 16px 64px; }
  h1, h2, h3, h4 { font-family: Arial, Helvetica, sans-serif; line-height: 1.25; margin: 1.4em 0 .5em; }
  .legend { font: 13px/1.5 Arial, Helvetica, sans-serif; border: 1px solid #ccc; border-radius: 6px; padding: 12px 14px; margin-bottom: 24px; }
  .legend span.sw { display: inline-block; width: 14px; height: 14px; border-radius: 3px; vertical-align: -2px; margin-right: 6px; }
  .u { border-left: 4px solid; border-radius: 3px; padding: 6px 10px; margin: 8px 0; break-inside: avoid; }
  .u.used { background: var(--used); border-color: var(--used-edge); }
  .u.excluded { background: var(--excl); border-color: var(--excl-edge); }
  .u.open { background: var(--open); border-color: #e8590c; }
  .tag { display: block; font: 11px/1.4 Arial, Helvetica, sans-serif; color: #444; margin-bottom: 3px; }
  p.plain { color: #555; }
  @media print { body { max-width: none; padding: 0; } @page { size: A4; margin: 16mm 14mm; } }
</style></head><body>
<h1>${esc(title)}</h1>
<div class="legend">
  <div><span class="sw" style="background:var(--used)"></span><b>Light green: used.</b> The brain has an item for this unit. The tag names the item.</div>
  <div><span class="sw" style="background:var(--excl)"></span><b>Yellow: excluded.</b> Read and left out of the brain. The tag gives the reason.</div>
  ${n('open') ? '<div><span class="sw" style="background:var(--open)"></span><b>Orange: still open.</b> Waiting on a decision.</div>' : ''}
  <div>No shading: text outside any numbered unit (cover pages, headings).</div>
  <div style="margin-top:6px">${units.length} units: ${n('used')} used, ${n('excluded')} excluded${n('open') ? `, ${n('open')} open` : ''}. Decisions from the ledger; the text is the speech as supplied.</div>
</div>
${out.join('\n')}
</body></html>
`;
}

function renderExcluded(units, src, ledgerFile) {
  const excl = units.filter(u => u.status === 'excluded');
  const personal = excl.filter(u => PERSON_LEVEL.includes(u.arg));
  const other = excl.filter(u => !PERSON_LEVEL.includes(u.arg));
  const md = [];
  md.push(`# Not to be built: measures left out of the brain (${src.year ? 'Ucapan Belanjawan ' + src.year : src.source})`);
  md.push('');
  md.push(`Generated by \`scripts/annotate-source.js\` from \`${path.basename(ledgerFile)}\`. Don't edit by hand; change the ledger and regenerate.`);
  md.push('');
  md.push('**For whoever develops the calculator:** do not implement anything on this list. Each unit was read in the speech and left out on purpose. Only the items in the brain file are to be built. If you think something here should be included, ask the user; don\'t add it on your own.');
  md.push('');
  md.push(`Of ${units.length} units, ${units.filter(u => u.status === 'used').length} are used by the brain and ${excl.length} are excluded.`);
  md.push('');
  md.push(`## 1. Measures that reach people but are not built (${personal.length})`);
  md.push('');
  md.push('These are the ones a developer might be tempted to add.');
  for (const reason of PERSON_LEVEL) {
    const list = personal.filter(u => u.arg === reason);
    if (!list.length) continue;
    md.push('');
    md.push(`### ${reason === 'user' ? 'Excluded by the user' : reason === 'non-citizen' ? 'For non-citizens' : 'Already over'} (${list.length})`);
    md.push('');
    md.push('| Unit | Source | What the text says | Note |');
    md.push('|---|---|---|---|');
    for (const u of list) md.push(`| ${u.id} | ${u.ref} | ${clip(u.text, 220).replace(/\|/g, '\\|')} | ${(u.note || '').replace(/\|/g, '\\|')} |`);
  }
  md.push('');
  md.push(`## 2. Everything else excluded (${other.length})`);
  md.push('');
  md.push('Out of scope by design: the brain states what a person gets or pays, never government totals, projects or company incentives. The full text of each unit is in the annotated speech (yellow).');
  md.push('');
  md.push('| Reason | Units | Examples |');
  md.push('|---|---|---|');
  const reasons = [...new Set(other.map(u => u.arg || u.kind))];
  reasons.sort((a, b) => other.filter(u => (u.arg || u.kind) === b).length - other.filter(u => (u.arg || u.kind) === a).length);
  for (const r of reasons) {
    const list = other.filter(u => (u.arg || u.kind) === r);
    md.push(`| ${REASONS[r] || r} | ${list.length} | ${list.slice(0, 6).map(u => u.id).join(', ')}${list.length > 6 ? ', …' : ''} |`);
  }
  md.push('');
  return md.join('\n');
}

async function toPdf(htmlFile, pdfFile) {
  let pw;
  try { pw = require('playwright'); } catch (e) {
    const root = require('child_process').execSync('npm root -g').toString().trim();
    pw = require(path.join(root, 'playwright'));
  }
  const browser = await pw.chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve(htmlFile), { waitUntil: 'load' });
  await page.pdf({ path: pdfFile, format: 'A4', printBackground: true, margin: { top: '16mm', bottom: '16mm', left: '14mm', right: '14mm' },
    displayHeaderFooter: true, headerTemplate: '<span></span>',
    footerTemplate: '<div style="font:9px Arial;width:100%;text-align:center;color:#666"><span class="pageNumber"></span> / <span class="totalPages"></span></div>' });
  await browser.close();
}

async function main() {
  const args = process.argv.slice(2);
  const opt = name => { const i = args.indexOf(name); if (i < 0) return undefined; const v = args[i + 1]; args.splice(i, 2); return v; };
  const flag = name => { const i = args.indexOf(name); if (i < 0) return false; args.splice(i, 1); return true; };
  const brain = opt('--brain'), outDir = opt('--out'), excludedFile = opt('--excluded'), pdf = flag('--pdf');
  const [speech, ledger] = args;
  if (!speech || !ledger || (!outDir && !excludedFile)) {
    console.error('usage: node scripts/annotate-source.js <speech.md> <ledger.tsv> [--brain brain.js] [--out dir] [--pdf] [--excluded file.md]');
    process.exit(2);
  }
  const { src, units, titles } = load(speech, ledger, brain);
  const missing = units.filter(u => !u.decision).length;
  if (missing) console.error(`warning: ${missing} units have no ledger decision (run coverage.js)`);
  if (outDir) {
    fs.mkdirSync(outDir, { recursive: true });
    const base = path.join(outDir, src.source.replace(/\.md$/, '') + '-annotated');
    fs.writeFileSync(base + '.html', renderHtml(speech, units, titles, src));
    console.log('wrote ' + base + '.html');
    if (pdf) { await toPdf(base + '.html', base + '.pdf'); console.log('wrote ' + base + '.pdf'); }
  }
  if (excludedFile) { fs.writeFileSync(excludedFile, renderExcluded(units, src, ledger)); console.log('wrote ' + excludedFile); }
  const c = s => units.filter(u => u.status === s).length;
  console.log(`${src.source}: ${units.length} units — ${c('used')} used (green), ${c('excluded')} excluded (yellow), ${c('open')} open`);
}

if (require.main === module) main().catch(e => { console.error(e); process.exit(1); });
module.exports = { load, renderHtml, renderExcluded };
