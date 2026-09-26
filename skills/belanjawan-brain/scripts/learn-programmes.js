/* Learn the names of citizen programmes from past speeches, text only.
 *
 *   node scripts/learn-programmes.js ub24.md ub25.md ub26.md [--out references/programmes.json]
 *
 * A name (acronym, my-/i-/e- name, or "Program|Skim|Bantuan|Elaun|… <Capitalised words>") counts
 * as a citizen programme when it is mentioned at least twice and at least half of the units
 * that mention it are already flagged by text-signals.js. The strong mentions teach the list;
 * the list then flags the weak mentions ("mySalam juga diperluas …") in the next speech.
 *
 * Also prints the cross-year view: which programmes run through every year, which appear in
 * earlier years but not in the latest one (ask the user; don't assume it ended), and which
 * are new in the latest year.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const { split } = require('./split-source.js');
require('./text-signals.js').disableProgrammes();

const NOT_PROGRAMMES = new Set(('MADANI RM YAB YB DUN GLC GLIC FDI ASEAN SME MOF LHDN LHDNM JKDM KPDN KKM KPM KPT KPKM ' +
  'KPWKM KPKT PDRM SPRM ATM APMM JPA JPM JPN KDN MINDEF TNB PETRONAS KWAP BNM KDNK COVID COVID-19 AI ICT TVET RMK UKM UM ' +
  'USM UPM UiTM PBB PPP ESG EV LNG LPG CCTV USD GST SST NRW MOU OKU B40 M40 T20 IKS PKS PMKS KL WP LRT MRT ECRL HSR KTM ' +
  'KTMB ETF LLP SEZ IBFC NGO RUU SMK IPT IPTA IPTS PBT STEM SWT UNESCO UNDP WHO FCTC SDG DBKL PdP IPO CSR CSO SOP BURSA ' +
  'KWSP PERKESO MARA JKM KEMAS PNB BSN TEKUN AIM HRD EPF SOCSO MALAYSIA MIDA MITI MATRADE CIDB INTAN DBP MPOB').split(' '));

function candidates(text) {
  const out = new Set();
  for (const m of text.matchAll(/\b([A-Z][A-Za-z]*[A-Z][A-Za-z0-9-]*|[A-Z]{2,}[0-9]*)\b/g)) out.add(m[1]);
  for (const m of text.matchAll(/\b((?:my|i-|e-)[A-Z][A-Za-z0-9]+|My[A-Z][A-Za-z0-9]+)\b/g)) out.add(m[1]);
  for (const m of text.matchAll(/\b((?:Program|Skim|Bantuan|Elaun|Inisiatif|Geran|Insentif|Jualan|Payung|Sumbangan|Rebat|Baucar|Kredit|Pelepasan)(?:\s+(?:[A-Z][\w-]*|dan|untuk|bagi)){1,4})/g)) {
    const k = m[1].replace(/\s+(dan|untuk|bagi)$/, '').replace(/\s+RM\S*$/, '');
    if (k.split(' ').length >= 2) out.add(k);
  }
  return out;
}

const initials = name => name.split(/\s+/).filter(w => /^[A-Z]/.test(w)).map(w => w[0]).join('');

function learn(files) {
  const years = [], lowerWords = new Map(), names = new Map(), rawByYear = {};
  for (const f of files) {
    const r = split(f);
    years.push(r.year);
    rawByYear[r.year] = r.units.map(u => u.text).join(' ').replace(/\s*RM[\d.,]+[jb]?(?=\s)/g, ''); // Lampiran I puts amounts mid-name
    for (const u of r.units) {
      for (const w of u.text.match(/\b[a-z][a-z-]{2,}\b/g) || []) lowerWords.set(w, (lowerWords.get(w) || 0) + 1);
      for (const k of candidates(u.text)) {
        if (!names.has(k)) names.set(k, { name: k, years: new Set(), mentions: 0, flagged: 0, refs: [] });
        const e = names.get(k);
        e.years.add(r.year); e.mentions++; if (u.flagged) e.flagged++;
        if (e.refs.length < 4) e.refs.push(`${r.year} ${u.ref}`);
      }
    }
  }
  const keep = [...names.values()].filter(e => {
    const k = e.name;
    if (/^RM\d/.test(k) || NOT_PROGRAMMES.has(k)) return false;
    if (/^[A-Z-]+$/.test(k) && lowerWords.has(k.toLowerCase())) return false;  // CUKAI, ASUHAN, KANAK-KANAK
    return e.mentions >= 2 && e.flagged / e.mentions >= 0.5;
  }).map(e => ({ name: e.name, years: [...e.years].sort(), mentions: e.mentions, flaggedShare: +(e.flagged / e.mentions).toFixed(2), refs: e.refs }))
    .sort((a, b) => b.years.length - a.years.length || b.mentions - a.mentions);
  // A programme "missing" from the latest year may still be there under another form: a single
  // unflagged mention, or its acronym (Skim Simpanan Pendidikan Nasional → SSPN).
  const latest = Math.max(...years);
  const latestText = rawByYear[latest] || '';
  keep.forEach(p => {
    if (p.years.includes(latest)) return;
    const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const asName = new RegExp('\\b' + esc(p.name) + '\\b', 'i').test(latestText);
    const ini = p.name.includes(' ') ? initials(p.name) : '';
    const asAcronym = ini.length >= 3 && new RegExp('\\b' + ini + '\\b').test(latestText);
    if (asName || asAcronym) p.alsoIn = { year: latest, as: asName ? p.name : ini };
  });
  return { learnedFrom: files.map(f => path.basename(f)), years: years.sort(), programmes: keep };
}

if (require.main === module) {
  const args = process.argv.slice(2);
  const oi = args.indexOf('--out');
  const out = oi > -1 ? args.splice(oi, 2)[1] : null;
  if (!args.length) { console.error('usage: node learn-programmes.js <speech.md>... [--out programmes.json]'); process.exit(2); }
  const r = learn(args);
  const latest = r.years[r.years.length - 1];
  const all = r.programmes.filter(p => p.years.length === r.years.length);
  // Only named schemes or names seen in 2+ years: a one-off acronym is too noisy to chase.
  const dropped = r.programmes.filter(p => !p.years.includes(latest) && !p.alsoIn &&
    (p.years.length >= 2 || p.name.includes(' ')));
  const fresh = r.programmes.filter(p => p.years.length === 1 && p.years[0] === latest);
  console.log(`${r.programmes.length} citizen programmes learned from ${r.years.join(', ')}`);
  console.log(`\nIn every year (${all.length}): ${all.map(p => p.name).join(' · ')}`);
  console.log(`\nIn earlier years but NOT in ${latest} (${dropped.length}) — ask the user whether each continues:\n  ` +
    dropped.map(p => `${p.name} [${p.years.join(',')}]`).join('\n  '));
  console.log(`\nNew in ${latest} (${fresh.length}): ${fresh.map(p => p.name).join(' · ')}`);
  if (out) { fs.writeFileSync(out, JSON.stringify(r, null, 1) + '\n'); console.log(`\nwritten ${out}`); }
}

module.exports = { learn, candidates };
