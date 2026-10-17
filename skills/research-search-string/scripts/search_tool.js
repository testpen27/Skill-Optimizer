#!/usr/bin/env node
/*
 * search_tool.js: build and check Boolean search strings for Scopus,
 * Web of Science and Google Scholar, and optionally write a Word file.
 *
 * Usage:
 *   node search_tool.js strings spec.json          prints the strings and any warnings
 *   node search_tool.js docx spec.json out.docx    writes the Word file
 *   node search_tool.js check "query" [scopus|wos|scholar]   lints a pasted string
 *
 * spec.json is one object, or an array of objects (one per research title):
 * {
 *   "title": "OTT Streaming Adoption among Malaysian Consumers: A Systematic Literature Review",
 *   "field": "Communication & Media Studies",
 *   "years": [2022, 2026],
 *   "concepts": [ { "name": "OTT and streaming", "terms": ["\"video on demand\"", "OTT", "adopt*"] }, ... ],
 *   "scholar": ["short string A", "short string B"],      // no truncation, 256 characters or fewer
 *   "malay": "optional separate Malay-language string",   // or "local": "...", "localLanguage": "Indonesian"
 *   "searchDate": "6 Oct 2026",                             // optional
 *   "links": { "scopus": "url", "wos": "url", "scholar": "url", "scholarLocal": "url" }  // optional
 * }
 * Terms are written exactly as they should appear in the database,
 * so phrases carry their own double quotes.
 */
const fs = require('fs');
const path = require('path');

class SpecError extends Error {}
const fail = msg => { throw new SpecError(msg); };

const join = a => a.join(' OR ');

// Chat apps, Word and phone keyboards turn " into curly quotes. Databases read
// those as ordinary characters, so a phrase silently stops being a phrase.
const hasCurly = t => /[“”„‟″«»‘’‚‛]/.test(t);
const tidy = t => t.replace(/[“”„‟″«»]/g, '"').replace(/[‘’‚‛]/g, "'").replace(/\s+/g, ' ').trim();

/* Make a spec safe to build from, or throw a SpecError that says what to fix. */
function normalise(spec, label) {
  const at = label ? `${label}: ` : '';
  if (!spec || typeof spec !== 'object' || Array.isArray(spec)) fail(`${at}spec must be a JSON object.`);
  if (!Array.isArray(spec.concepts) || !spec.concepts.length) fail(`${at}"concepts" must be a non-empty array of {name, terms}.`);
  const notes = [];
  const concepts = spec.concepts.map((c, i) => {
    const n = `${at}concept ${i + 1}`;
    if (!c || typeof c !== 'object') fail(`${n} must be an object with "name" and "terms".`);
    if (!Array.isArray(c.terms) || !c.terms.length) fail(`${n} (${c.name || 'unnamed'}) needs "terms" as a non-empty array of strings.`);
    const terms = c.terms.map(t => {
      if (typeof t !== 'string') fail(`${n}: every term must be a string, got ${JSON.stringify(t)}.`);
      if (hasCurly(t)) notes.push(`${n}: replaced curly quotes in ${t}`);
      return tidy(t);
    }).filter(Boolean);
    if (!terms.length) fail(`${n} (${c.name || 'unnamed'}) has only empty terms.`);
    return { name: c.name || `Concept ${i + 1}`, terms };
  });
  const thisYear = new Date().getFullYear();
  let [y0, y1] = Array.isArray(spec.years) && spec.years.length === 2 ? spec.years.map(Number) : [thisYear - 4, thisYear];
  if (!Number.isInteger(y0) || !Number.isInteger(y1)) fail(`${at}"years" must be two whole years such as [2022, 2026].`);
  if (y0 > y1) { notes.push(`${at}years were reversed, swapped to ${y1}-${y0}`); [y0, y1] = [y1, y0]; }
  if (y0 < 1900 || y1 > thisYear + 1) fail(`${at}years ${y0}-${y1} look wrong; expected between 1900 and ${thisYear + 1}.`);
  let scholar = spec.scholar === undefined || spec.scholar === null ? [] : spec.scholar;
  if (typeof scholar === 'string') scholar = [scholar];
  if (!Array.isArray(scholar) || scholar.some(x => typeof x !== 'string')) fail(`${at}"scholar" must be an array of strings.`);
  // "malay" is the original key; "local" is the same thing for any other language.
  const localRaw = spec.local !== undefined && spec.local !== null ? spec.local : spec.malay;
  if (localRaw !== undefined && localRaw !== null && typeof localRaw !== 'string') fail(`${at}"local" (or "malay") must be a string.`);
  const language = typeof spec.localLanguage === 'string' && spec.localLanguage.trim()
    ? spec.localLanguage.trim() : (spec.local ? 'local-language' : 'Malay');
  return Object.assign({}, spec, {
    concepts, years: [y0, y1], notes, language,
    scholar: scholar.map(tidy).filter(Boolean), malay: tidy(localRaw || '')
  });
}

function buildStrings(spec) {
  const [y0, y1] = spec.years;
  const body = spec.concepts.map(c => '(' + join(c.terms) + ')').join(' AND ');
  return {
    y0, y1,
    scopus: `TITLE-ABS-KEY(${body}) AND PUBYEAR > ${y0 - 1} AND PUBYEAR < ${y1 + 1}`,
    wos: `TS=(${body}) AND PY=(${y0}-${y1})`,
    scholar: spec.scholar,
    malay: spec.malay
  };
}

// A bare AND / OR / NOT (outside quotes) as a whole term, or hiding inside a
// multi-word term, would be read as an operator and change the logic.
const OPERATOR = /(^|\s)(AND|OR|NOT|NEAR(\/\d+)?|W\/\d+|PRE\/\d+)(\s|$)/;
const outsideQuotes = t => t.replace(/"[^"]*"/g, '""');

/* Checks that apply to any single search string, wherever it came from. */
function lintString(str, kind, label) {
  const w = [];
  const bare = outsideQuotes(str);
  if ((str.match(/"/g) || []).length % 2) w.push(`${label}: unbalanced double quotes.`);
  let depth = 0, bad = false;
  for (const ch of bare) { if (ch === '(') depth++; if (ch === ')' && --depth < 0) bad = true; }
  if (depth !== 0 || bad) w.push(`${label}: unbalanced parentheses.`);
  if (hasCurly(str)) w.push(`${label}: contains curly quotes. Use straight " quotes or the database will not treat the phrase as a phrase.`);
  if (/\(\s*\)/.test(bare)) w.push(`${label}: empty brackets.`);
  if (/\b(AND|OR|NOT)\s+(AND|OR)\b|\(\s*(AND|OR)\b|\b(AND|OR|NOT)\s*\)/.test(bare)) w.push(`${label}: dangling Boolean operator.`);
  if (/\b(and|or|not)\b/.test(bare) && kind !== 'scholar') w.push(`${label}: lower-case and/or/not outside quotes. Scopus and Web of Science may treat it as a search word, not an operator. Capitalise it.`);
  if (kind === 'scholar') {
    if (str.length > 256) w.push(`${label}: ${str.length} characters. Google Scholar cuts queries at about 256, so the end is silently ignored.`);
    if (/[*$]|\?/.test(bare) || /[*$]|\?/.test(str)) w.push(`${label}: contains * ? or $. Google Scholar does not support truncation or wildcards.`);
    if (/\b(or)\b/.test(bare)) w.push(`${label}: lower-case "or". Scholar only reads OR in capitals.`);
    if (/TITLE-ABS-KEY|\bTS=|PUBYEAR|PY=/.test(str)) w.push(`${label}: contains Scopus or Web of Science field codes. Scholar will search for them as words.`);
  } else {
    if (kind === 'scopus' && /\bTS=|\bPY=/.test(str)) w.push(`${label}: contains Web of Science field codes (TS=, PY=). Scopus uses TITLE-ABS-KEY and PUBYEAR.`);
    if (kind === 'wos' && /TITLE-ABS-KEY|PUBYEAR/.test(str)) w.push(`${label}: contains Scopus field codes. Web of Science uses TS= and PY=.`);
    if (kind === 'scopus' && /\$/.test(bare)) w.push(`${label}: $ is a Web of Science wildcard; Scopus does not support it.`);
    (bare.match(/(?:^|[\s(])[*?]\S*/g) || []).forEach(m => {
      if (m.replace(/[\s(*?]/g, '').length < 3) w.push(`${label}: wildcard at the start of a word needs 3 or more characters after it (${m.trim()}).`);
    });
  }
  return w;
}

function validate(spec) {
  const w = [];
  const total = spec.concepts.reduce((n, c) => n + c.terms.length, 0);
  const plurals = [];
  spec.concepts.forEach((c, i) => {
    const label = `Concept ${i + 1} (${c.name})`;
    const seen = new Set();
    if (c.terms.length > 18) w.push(`${label}: ${c.terms.length} terms is a lot. Drop the weakest ones.`);
    if (c.terms.length < 3 && i < 3) w.push(`${label}: only ${c.terms.length} term(s). One concept with few synonyms is the usual reason a search misses good papers.`);
    c.terms.forEach(t => {
      const key = t.toLowerCase();
      if (seen.has(key)) w.push(`${label}: duplicate term ${t}`);
      seen.add(key);
      if ((t.match(/"/g) || []).length % 2) w.push(`${label}: unbalanced quotes in ${t}`);
      const quoted = /^".*"$/.test(t);
      const inner = quoted ? t.slice(1, -1) : t;
      if (quoted && !inner.trim()) w.push(`${label}: empty phrase ${t}`);
      if (quoted && /\s/.test(inner) && !/[*?$]/.test(inner.split(' ').pop()) && !/(s|ics|ia)$/i.test(inner)) plurals.push(t);
      if (quoted && /\$/.test(inner)) w.push(`${label}: $ inside the quoted phrase ${t}. Web of Science does not allow $ in quotes. Use ? or * instead.`);
      if (!quoted && /\s/.test(t)) w.push(`${label}: multi-word term without quotes (${t}). Add double quotes.`);
      if (!quoted && OPERATOR.test(t)) w.push(`${label}: ${t} contains an operator word. Remove it; each term should be one word or one quoted phrase.`);
      if (quoted && /^"(AND|OR|NOT)"$/i.test(t)) w.push(`${label}: ${t} is a stop word, not a search term.`);
      if (/[()]/.test(outsideQuotes(t))) w.push(`${label}: bracket inside term ${t}. It will break the grouping.`);
      if (/^(and|or|not)$/i.test(t)) w.push(`${label}: ${t} is a Boolean operator, not a search term.`);
      if (/\$/.test(t)) w.push(`${label}: ${t} uses $, which only Web of Science supports. Use * so the Scopus and WoS strings match.`);
      const star = t.indexOf('*');
      if (star > -1 && star < 3 && !quoted && !/^[*?]/.test(t)) w.push(`${label}: only ${star} character(s) before * in ${t}. Keep at least 3.`);
      if (/^[*?]/.test(t) && t.replace(/[*?]/g, '').length < 3) w.push(`${label}: ${t} starts with a wildcard and has fewer than 3 other characters.`);
      if (/^[*?]/.test(t)) w.push(`${label}: ${t} starts with a wildcard. Allowed in Scopus and Web of Science (3+ characters needed), but slow and noisy; prefer a stem such as ology* only if you need it.`);
      if (t.length === 1 || (!quoted && !t.includes('*') && /^[A-Za-z]{1,2}$/.test(t))) w.push(`${label}: ${t} is too short to be a useful term.`);
    });
  });
  if (plurals.length) w.push(`Web of Science does not match plurals inside quotes. If any of these can appear in the plural, truncate the last word, e.g. "streaming service*" (works in Scopus and Web of Science): ${plurals.slice(0, 6).join(', ')}${plurals.length > 6 ? ` and ${plurals.length - 6} more` : ''}.`);
  if (total > 80) w.push(`${total} terms in total. Scopus and Web of Science will run it, but a string this long is hard to debug and usually returns noise.`);
  const s = buildStrings(spec);
  w.push(...lintString(s.scopus, 'scopus', 'Scopus string'));
  w.push(...lintString(s.wos, 'wos', 'Web of Science string'));
  spec.scholar.forEach((g, i) => w.push(...lintString(g, 'scholar', `Scholar string ${String.fromCharCode(65 + i)}`)));
  if (spec.malay) w.push(...lintString(spec.malay, 'scholar', `${spec.language} string`));
  if (!spec.scholar.length) w.push('No Scholar strings yet. Scholar cannot take the long Scopus string, so write two short ones under "scholar".');
  return w.concat(spec.notes.map(n => 'Fixed: ' + n));
}

function printStrings(spec) {
  const s = buildStrings(spec);
  console.log(`# ${spec.title || 'Untitled'}\n`);
  console.log('## Scopus (Advanced search)\n' + s.scopus + `\n(${s.scopus.length} characters)\n`);
  console.log('## Web of Science (Advanced search, Core Collection)\n' + s.wos + `\n(${s.wos.length} characters)\n`);
  s.scholar.forEach((g, i) => console.log(`## Google Scholar, version ${String.fromCharCode(65 + i)}\n${g}\n(${g.length} characters)\n`));
  if (s.malay) console.log(`## Google Scholar, ${spec.language}-language (run separately)\n${s.malay}\n(${s.malay.length} characters)\n`);
  const w = validate(spec);
  console.log(w.length ? '## Warnings\n- ' + w.join('\n- ') : '## Warnings\nNone.');
}

/* ---------- Word output ---------- */
function writeDocx(specs, outPath) {
  let docx;
  try { docx = require('docx'); } catch (e) {
    fail('The "docx" module is not installed, so the Word file cannot be built. Run "npm install docx" (or use the docx skill with the same layout). The search strings themselves are unaffected: use "strings" mode.');
  }
  const {
    Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType,
    ShadingType, AlignmentType, BorderStyle, HeadingLevel, PageOrientation,
    VerticalAlign, ExternalHyperlink
  } = docx;
  const FONT = 'Calibri';
  const bd = { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF' };
  const borders = { top: bd, bottom: bd, left: bd, right: bd };

  const cell = (text, width, o = {}) => new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: o.fill || 'FFFFFF', color: 'auto' },
    margins: { top: 40, bottom: 40, left: 90, right: 90 },
    verticalAlign: o.top ? VerticalAlign.TOP : VerticalAlign.CENTER,
    borders,
    children: (Array.isArray(text) ? text : [text]).map(t => new Paragraph({
      alignment: o.align || AlignmentType.LEFT, spacing: { before: 0, after: 0 },
      children: [new TextRun({ text: t, bold: !!o.bold, color: o.color || '000000', size: o.size || 18, font: o.font || FONT })]
    }))
  });
  const linkCell = (label, url, width, fill) => new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: fill || 'FFFFFF', color: 'auto' },
    margins: { top: 40, bottom: 40, left: 90, right: 90 },
    verticalAlign: VerticalAlign.TOP, borders,
    children: [new Paragraph({ spacing: { before: 0, after: 0 }, children: url
      ? [new ExternalHyperlink({ link: url, children: [new TextRun({ text: label, color: '0563C1', underline: {}, size: 18, font: FONT })] })]
      : [new TextRun({ text: '', size: 18, font: FONT })] })]
  });

  function conceptTable(concepts) {
    const k = concepts.length;
    const andW = 700;
    const total = 14838;
    const cw = Math.floor((total - andW * (k - 1)) / k);
    const W = [];
    for (let i = 0; i < k; i++) { W.push(cw); if (i < k - 1) W.push(andW); }
    W[W.length - 1] += total - W.reduce((a, b) => a + b, 0);
    const n = Math.max(...concepts.map(c => c.terms.length));
    const cols = W.length;
    const rows = [new TableRow({ tableHeader: true, cantSplit: true, children: W.map((w, i) => i % 2 === 0
      ? cell(['Concept ' + (i / 2 + 1), concepts[i / 2].name], w, { bold: true, color: 'FFFFFF', fill: '595959', align: AlignmentType.CENTER })
      : cell('', w, { fill: '595959' })) })];
    for (let r = 0; r < 2 * n - 1; r++) {
      const isTerm = r % 2 === 0, fill = isTerm ? 'E7E6E6' : 'FFFFFF';
      rows.push(new TableRow({ cantSplit: true, children: W.map((w, i) => {
        if (i % 2 === 1) return cell(r === 0 ? 'AND' : '', w, { fill, bold: true, align: AlignmentType.CENTER });
        const c = concepts[i / 2];
        if (isTerm) return cell(c.terms[r / 2] || '', w, { fill, align: AlignmentType.CENTER });
        const showOr = Math.floor(r / 2) < c.terms.length - 1;
        return cell(showOr ? 'OR' : '', w, { fill, bold: true, color: '7F7F7F', align: AlignmentType.CENTER });
      }) }));
    }
    return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: W, rows });
  }

  function resultTable(spec, s) {
    const W = [1700, 1100, 2000, 7438, 2600];
    const L = spec.links || {};
    const yr = `${s.y0} to ${s.y1}`;
    const data = [
      { db: 'Scopus', filters: `TITLE-ABS-KEY; ${yr}`, syntax: s.scopus, label: 'Open Scopus results', url: L.scopus },
      { db: 'Web of Science (Core Collection)', filters: `Topic (TS); ${yr}`, syntax: s.wos, label: 'Open Web of Science results', url: L.wos }
    ];
    s.scholar.forEach((g, i) => data.push({ db: 'Google Scholar' + (s.scholar.length > 1 ? ' ' + String.fromCharCode(65 + i) : ''), filters: yr, syntax: g, label: 'Open Google Scholar search', url: i === 0 ? L.scholar : (L['scholar' + String.fromCharCode(65 + i)] || null) }));
    if (s.malay) data.push({ db: `Google Scholar (${spec.language})`, filters: yr, syntax: s.malay, label: 'Open Google Scholar search', url: L.scholarLocal || L.scholarMalay });
    const hdr = new TableRow({ tableHeader: true, cantSplit: true, children: ['Database', 'Date searched', 'Filters applied', 'Syntax used', 'Link'].map((h, i) => cell(h, W[i], { bold: true, color: 'FFFFFF', fill: '1F3864' })) });
    const body = data.map((r, ri) => {
      const fill = ri % 2 ? 'F2F2F2' : 'FFFFFF';
      return new TableRow({ cantSplit: true, children: [
        cell(r.db, W[0], { fill, bold: true, top: true }),
        cell(spec.searchDate || '', W[1], { fill, top: true }),
        cell(r.filters, W[2], { fill, top: true }),
        cell(r.syntax, W[3], { fill, top: true, font: 'Consolas', size: 15 }),
        linkCell(r.label, r.url, W[4], fill)
      ] });
    });
    return new Table({ width: { size: 14838, type: WidthType.DXA }, columnWidths: W, rows: [hdr, ...body] });
  }

  const h1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
  const p = t => new Paragraph({ spacing: { before: 40, after: 100 }, children: [new TextRun({ text: t, size: 21, font: FONT })] });
  const kv = (k, v) => new Paragraph({ spacing: { before: 0, after: 30 }, children: [new TextRun({ text: k + ': ', bold: true, size: 21, font: FONT }), new TextRun({ text: v, size: 21, font: FONT })] });

  const children = [];
  specs.forEach((spec, idx) => {
    const s = buildStrings(spec);
    children.push(new Paragraph({ heading: HeadingLevel.TITLE, pageBreakBefore: idx > 0, children: [new TextRun(spec.title || 'Search strategy')] }));
    if (spec.field) children.push(kv('Field', spec.field));
    children.push(kv('Date range', `${s.y0} to ${s.y1}`));
    children.push(h1('1. Search concept table'));
    children.push(p('Terms in the same column are joined with OR. The columns are joined with AND.'));
    children.push(conceptTable(spec.concepts));
    children.push(h1('2. Search result'));
    children.push(resultTable(spec, s));
  });

  const doc = new Document({
    creator: 'Claude', title: 'Search strategy',
    styles: {
      default: { document: { run: { font: FONT, size: 21 } } },
      paragraphStyles: [
        { id: 'Title', name: 'Title', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 36, bold: true, color: '1F3864', font: FONT }, paragraph: { spacing: { before: 0, after: 100 } } },
        { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 28, bold: true, color: '1F3864', font: FONT }, paragraph: { spacing: { before: 280, after: 100 }, outlineLevel: 0, keepNext: true } }
      ]
    },
    sections: [{ properties: { page: { size: { width: 11906, height: 16838, orientation: PageOrientation.LANDSCAPE }, margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } }, children }]
  });
  return Packer.toBuffer(doc).then(b => {
    fs.mkdirSync(path.dirname(path.resolve(outPath)), { recursive: true });
    fs.writeFileSync(outPath, b);
    console.log('Wrote ' + outPath);
  });
}

/* ---------- CLI ---------- */
function readSpecs(specPath) {
  let text;
  try { text = fs.readFileSync(specPath, 'utf8'); } catch (e) { fail(`Cannot read ${specPath}: ${e.code || e.message}.`); }
  let raw;
  try { raw = JSON.parse(text.replace(/^﻿/, '')); } catch (e) { fail(`${specPath} is not valid JSON (${e.message}). Check for a missing comma or an unescaped " inside a term: write \\" for a quote inside a JSON string.`); }
  const list = Array.isArray(raw) ? raw : [raw];
  if (!list.length) fail(`${specPath} holds an empty array.`);
  return list.map((sp, i) => normalise(sp, list.length > 1 ? `spec ${i + 1}` : ''));
}

function checkRaw(str, kind) {
  const kinds = ['scopus', 'wos', 'scholar'];
  if (!str) fail('Give the search string to check, in quotes.');
  if (!kind) kind = /TITLE-ABS-KEY|PUBYEAR/.test(str) ? 'scopus' : /\bTS=|\bPY=/.test(str) ? 'wos' : 'scholar';
  if (!kinds.includes(kind)) fail(`Unknown database "${kind}". Use scopus, wos or scholar.`);
  console.log(`Checking as ${kind} (${str.length} characters)`);
  const w = lintString(str, kind, 'String');
  console.log(w.length ? '## Warnings\n- ' + w.join('\n- ') : '## Warnings\nNone.');
}

function main() {
  const [mode, a, b] = process.argv.slice(2);
  if (!mode || !a) fail('Usage: node search_tool.js strings|docx spec.json [out.docx]  or  node search_tool.js check "query" [scopus|wos|scholar]');
  if (mode === 'check') return checkRaw(a, b);
  const specs = readSpecs(a);
  if (mode === 'strings') specs.forEach((s, i) => { if (i) console.log('\n----------------\n'); printStrings(s); });
  else if (mode === 'docx') { if (!b) fail('Give an output path, e.g. node search_tool.js docx spec.json out.docx'); return writeDocx(specs, b); }
  else fail('Unknown mode: ' + mode);
}

Promise.resolve().then(main).catch(e => {
  if (e instanceof SpecError) { console.error('Error: ' + e.message); process.exit(1); }
  throw e;
});
