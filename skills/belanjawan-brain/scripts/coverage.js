/* Coverage check: every unit of the source text has a decision, and every brain item has a source.
 *
 *   node scripts/coverage.js <speech.md> <ledger.tsv> [--brain <brain.js>] [--final]
 *
 * Ledger: tab-separated `unit <TAB> decision <TAB> note`, one row per unit from split-source.js.
 * Lines starting with # are comments. Decisions:
 *   item:<id>[,<id>]     the unit is the source (or a restatement) of these brain items
 *   gap                  a person-level measure the brain doesn't have yet (not allowed with --final)
 *   ask                  borderline; put to the user in step 5 (not allowed with --final)
 *   exclude:<reason>     reason is one of EXCLUDE_REASONS; `user` needs the user's words in the note
 *   bulk                 read at speed, nothing for a person. Only allowed for units NOT flagged
 *                        by text-signals.js; a flagged unit needs a real decision.
 * Pseudo-units `prev:<itemId>` record items from last year's brain that the new text doesn't
 * mention: decision `carried`, `dropped` or `ask`, with a note.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const { split } = require('./split-source.js');

const EXCLUDE_REASONS = {
  allocation: 'government spending total or beneficiary count, nothing one person receives',
  business: 'company, investor or employer incentive',
  infra: 'infrastructure, buildings, public works',
  institution: 'goes to an agency, NGO, school or mosque, not to a person',
  governance: 'law, enforcement, administration, fiscal policy',
  rhetoric: 'speech framing, history, thanks, verses',
  'non-citizen': 'applies to non-citizens or foreign companies',
  past: 'one-off that ended before the Q&A goes live',
  heading: 'a heading or lead-in with no measure of its own',
  user: 'the user decided to exclude it (quote them in the note)',
};

function readLedger(file) {
  const rows = [];
  fs.readFileSync(file, 'utf8').split('\n').forEach((line, i) => {
    if (!line.trim() || line.startsWith('#')) return;
    const [unit, decision, note = ''] = line.split('\t');
    rows.push({ unit: (unit || '').trim(), decision: (decision || '').trim(), note: note.trim(), line: i + 1 });
  });
  return rows;
}

function check(speech, ledgerFile, opts = {}) {
  const src = split(speech);
  const units = new Map(src.units.map(u => [u.id, u]));
  const rows = readLedger(ledgerFile);
  const errors = [], warnings = [];
  const seen = new Map();
  const itemRefs = new Map();
  const tally = {};

  for (const r of rows) {
    const where = `${path.basename(ledgerFile)}:${r.line} ${r.unit}`;
    if (seen.has(r.unit)) { errors.push(`${where}: duplicate row (first at line ${seen.get(r.unit)})`); continue; }
    seen.set(r.unit, r.line);
    const isPrev = r.unit.startsWith('prev:');
    const u = units.get(r.unit);
    if (!u && !isPrev) { errors.push(`${where}: no such unit in ${src.source} (text changed? re-split)`); continue; }
    const [kind, arg = ''] = r.decision.split(':');
    tally[kind] = (tally[kind] || 0) + 1;

    if (isPrev) {
      if (!['carried', 'dropped', 'ask'].includes(kind)) errors.push(`${where}: prev: rows take carried|dropped|ask`);
      if (!r.note) errors.push(`${where}: prev: rows need a note`);
      if (kind === 'ask' && opts.final) errors.push(`${where}: still waiting on the user`);
      continue;
    }
    switch (kind) {
      case 'item':
        if (!arg) { errors.push(`${where}: item: needs an id`); break; }
        arg.split(',').forEach(id => { id = id.trim(); if (!itemRefs.has(id)) itemRefs.set(id, []); itemRefs.get(id).push(r.unit); });
        break;
      case 'exclude':
        if (!EXCLUDE_REASONS[arg]) errors.push(`${where}: unknown exclude reason "${arg}" (use: ${Object.keys(EXCLUDE_REASONS).join(', ')})`);
        if (arg === 'user' && !r.note) errors.push(`${where}: exclude:user needs the user's words in the note`);
        break;
      case 'bulk':
        if (u.flagged) errors.push(`${where}: flagged unit (score ${u.score}: ${u.signals.join(' ')}) can't be bulk-excluded — give it a decision`);
        break;
      case 'gap':
      case 'ask':
        if (!r.note) errors.push(`${where}: ${kind} needs a note saying what the measure is`);
        if (opts.final) errors.push(`${where}: ${kind} left open — resolve it with the user before hand-over`);
        break;
      default:
        errors.push(`${where}: unknown decision "${r.decision}"`);
    }
  }

  const missing = src.units.filter(u => !seen.has(u.id));
  missing.slice(0, 25).forEach(u => errors.push(`missing: ${u.id} (${u.ref})${u.flagged ? ' FLAGGED' : ''} — ${u.text.slice(0, 80)}`));
  if (missing.length > 25) errors.push(`… and ${missing.length - 25} more units with no ledger row`);

  if (opts.brain) {
    const B = require(path.resolve(opts.brain));
    const ids = new Set(B.BENEFITS.map(b => b.id));
    for (const id of itemRefs.keys()) if (!ids.has(id)) errors.push(`ledger names item "${id}" that isn't in the brain`);
    for (const id of ids) if (!itemRefs.has(id)) errors.push(`brain item "${id}" has no source unit in the ledger`);
  }

  return { src, rows, errors, warnings, tally, missing: missing.length, itemRefs };
}

if (require.main === module) {
  const args = process.argv.slice(2);
  const flag = n => { const i = args.indexOf(n); if (i < 0) return undefined; const v = args[i + 1]; args.splice(i, v && !v.startsWith('--') ? 2 : 1); return v && !v.startsWith('--') ? v : true; };
  const brain = flag('--brain'), final = flag('--final');
  const [speech, ledger] = args;
  if (!speech || !ledger) { console.error('usage: node coverage.js <speech.md> <ledger.tsv> [--brain brain.js] [--final]'); process.exit(2); }
  const r = check(speech, ledger, { brain, final: !!final });
  const flagged = r.src.units.filter(u => u.flagged).length;
  console.log(`${r.src.source}: ${r.src.units.length} units (${flagged} flagged), ${r.rows.length} ledger rows, ${r.missing} missing`);
  console.log('decisions: ' + Object.entries(r.tally).map(([k, v]) => `${k} ${v}`).join(', '));
  if (r.tally.gap || r.tally.ask) console.log(`open: ${r.tally.gap || 0} gap, ${r.tally.ask || 0} ask — take these to the user (step 5)`);
  if (r.errors.length) { console.error(`\nCOVERAGE FAILED (${r.errors.length}):\n  ` + r.errors.join('\n  ')); process.exit(1); }
  console.log('coverage OK');
}

module.exports = { check, readLedger, EXCLUDE_REASONS };
