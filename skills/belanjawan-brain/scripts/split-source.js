/* Split a budget speech (Markdown or pdftotext output) into numbered units, so every
 * part of the source can be accounted for in the ledger. Text only: no network.
 *
 *   node scripts/split-source.js <speech.md> [out.json]
 *
 * Units:
 *   P184      speech paragraph 184, its opening text
 *   P184.2    the 2nd bullet (● or -) inside paragraph 184
 *   L1.29     Lampiran I entry (Bil.) 29, its title/opening text
 *   L1.29.3   the 3rd item inside Lampiran I Bil. 29
 *   L2.36     Lampiran II entry 36 (tax measure), whole entry
 *
 * Exits non-zero if the speech or Lampiran I numbering has a gap, because a gap means the
 * extraction lost text and the ledger would silently miss it.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const { scoreUnit } = require('./text-signals.js');

const BULLET = /^\s*(?:●|•|▪|-)\s+/;
const NUMBERED = /^\s*(\d{1,3})\.\s+/;

function isHeading(line) {
  const m = line.match(/^(#{1,6})\s+(.*)$/);
  if (!m) return null;
  const text = m[2].trim();
  // Conversion artefacts: "### TNB.", "### (SARA)" are sentence fragments, not headings.
  if (m[1].length >= 3 && (/\.$/.test(text) || /^\(/.test(text))) return null;
  return { level: m[1].length, text };
}

const norm = s => s.replace(/\s+/g, ' ').trim();

function split(file) {
  const raw = fs.readFileSync(file, 'utf8').replace(/\r/g, '');
  const lines = raw.split('\n');
  const yearM = raw.match(/(?:Ucapan\s+)?(?:Belanjawan|Bajet)\s+(20\d\d)/i);
  const year = yearM ? +yearM[1] : null;

  // ---- locate the parts ----
  const h1 = [];
  lines.forEach((l, i) => { const h = isHeading(l); if (h && h.level <= 2) h1.push({ i, ...h }); });
  const mukadimah = h1.filter(h => /^MUKADIMAH/i.test(h.text)).pop();
  const penutup = h1.filter(h => /^PENUTUP/i.test(h.text)).pop();
  const speechStart = mukadimah ? mukadimah.i : 0;
  let speechEnd = lines.length;
  if (penutup) {
    const after = h1.find(h => h.i > penutup.i && h.level === 1);
    if (after) speechEnd = after.i;
  }
  // Lampiran II: the last run of "# LAMPIRAN <n>" headings with no title on the line (the
  // content pages; the index lines carry titles). Fallback: any "# LAMPIRAN <n>".
  const l2Heads = [];
  lines.forEach((l, i) => {
    const m = l.match(/^#\s*LAMPIRAN\s+(\d{1,3})\s*(.*)$/i);
    if (m && i >= speechEnd) l2Heads.push({ i, n: +m[1], title: m[2].trim() });
  });
  const bare = l2Heads.filter(h => !h.title);
  const l2 = (bare.length ? bare : l2Heads);
  const l2Start = l2.length ? l2[0].i : lines.length;
  // Lampiran I is whatever sits between the speech and Lampiran II (2026: "# LAMPIRAN I";
  // 2025: the "TUMPUAN" pages). Skip a Lampiran II index block if it sits in that gap.
  const l2Index = lines.findIndex((l, i) => i >= speechEnd && /^#\s*LAMPIRAN\s+II\b/i.test(l));
  const l1End = l2Index > -1 ? l2Index : l2Start;

  const units = [];
  const problems = [];
  let section = [];
  const setSection = h => { section = section.slice(0, h.level - 1); section[h.level - 1] = h.text; };
  const sec = () => section.filter(Boolean).join(' › ');

  function push(u) {
    u.text = norm(u.text);
    if (!u.text) return;
    u.section = u.section || sec();
    units.push(u);
  }

  // ---- speech: paragraphs and their bullets ----
  let para = 0, bullet = 0, cur = null;
  for (let i = speechStart; i < speechEnd; i++) {
    const line = lines[i];
    const h = isHeading(line);
    if (h) { if (cur) { push(cur); cur = null; } setSection(h); continue; }
    const n = line.match(NUMBERED);
    if (n && +n[1] === para + 1) {
      if (cur) push(cur);
      para = +n[1]; bullet = 0;
      cur = { id: 'P' + para, part: 'ucapan', ref: `Perenggan ${para}`, text: line.replace(NUMBERED, ''), line: i + 1 };
      continue;
    }
    if (para && BULLET.test(line)) {
      if (cur) push(cur);
      bullet++;
      cur = { id: `P${para}.${bullet}`, part: 'ucapan', ref: `Perenggan ${para} (butiran ${bullet})`, text: line.replace(BULLET, ''), line: i + 1 };
      continue;
    }
    if (cur) cur.text += ' ' + line;
  }
  if (cur) push(cur);
  if (para === 0) problems.push('no numbered speech paragraphs found');

  // ---- Lampiran I: continuously numbered entries (Bil.), items inside ----
  let bil = 0, item = 0; cur = null; section = [];
  for (let i = speechEnd; i < l1End; i++) {
    const line = lines[i];
    const h = isHeading(line);
    if (h) { if (cur) { push(cur); cur = null; } setSection(h); continue; }
    const n = line.match(NUMBERED);
    if (n && +n[1] === bil + 1) {   // inner lists restart at 1, so only the next Bil counts
      if (cur) push(cur);
      bil = +n[1]; item = 0;
      cur = { id: 'L1.' + bil, part: 'lampiran1', ref: `Lampiran I Bil. ${bil}`, text: line.replace(NUMBERED, ''), line: i + 1 };
      continue;
    }
    if (bil && BULLET.test(line)) {
      if (cur) push(cur);
      item++;
      cur = { id: `L1.${bil}.${item}`, part: 'lampiran1', ref: `Lampiran I Bil. ${bil} (butiran ${item})`, text: line.replace(BULLET, ''), line: i + 1 };
      continue;
    }
    if (cur) cur.text += ' ' + line;
  }
  if (cur) push(cur);

  // ---- Lampiran II: one unit per entry ----
  l2.forEach((h, k) => {
    const end = k + 1 < l2.length ? l2[k + 1].i : lines.length;
    const body = lines.slice(h.i + 1, end);
    const titleLines = [];
    for (const l of body) { const hh = isHeading(l); if (hh) titleLines.push(hh.text); else if (l.trim()) break; }
    const title = norm(h.title || titleLines.join(' '));
    push({ id: 'L2.' + h.n, part: 'lampiran2', ref: `Lampiran II — Lampiran ${h.n}`, title, section: 'Lampiran II',
      text: title + ' — ' + body.filter(l => !isHeading(l)).join(' '), line: h.i + 1 });
  });
  const l2nums = l2.map(h => h.n);
  l2nums.forEach((n, k) => { if (n !== k + 1) problems.push(`Lampiran II numbering jumps at ${n} (expected ${k + 1})`); });

  units.forEach(u => Object.assign(u, scoreUnit(u.text, u.part)));

  return {
    source: path.basename(file), year,
    counts: {
      paragraphs: para,
      speechUnits: units.filter(u => u.part === 'ucapan').length,
      lampiran1Entries: bil,
      lampiran1Units: units.filter(u => u.part === 'lampiran1').length,
      lampiran2Entries: l2.length,
    },
    problems, units,
  };
}

if (require.main === module) {
  const [file, out] = process.argv.slice(2);
  if (!file) { console.error('usage: node split-source.js <speech.md> [out.json]'); process.exit(2); }
  const r = split(file);
  if (out) fs.writeFileSync(out, JSON.stringify(r, null, 1));
  console.log(`${r.source} (${r.year}): ${r.counts.paragraphs} paragraphs → ${r.counts.speechUnits} units; ` +
    `Lampiran I ${r.counts.lampiran1Entries} entries → ${r.counts.lampiran1Units} units; Lampiran II ${r.counts.lampiran2Entries} entries`);
  const flagged = r.units.filter(u => u.flagged).length;
  console.log(`flagged for close reading: ${flagged} of ${r.units.length} units`);
  if (r.problems.length) { console.error('PROBLEMS:\n  ' + r.problems.join('\n  ')); process.exit(1); }
}

module.exports = { split };
