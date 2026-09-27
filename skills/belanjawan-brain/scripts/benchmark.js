/* Benchmark the text-signal scorer against a hand-made answer key, learning only from past years.
 *
 *   node scripts/benchmark.js <speech.md> <answers.tsv> [--learn-from past1.md past2.md …]
 *   node scripts/benchmark.js <speech.md> --draw <n> --seed <s>          # sample ids for a sampled key
 *   node scripts/benchmark.js <speech.md> --blind [--ids ids.txt] [--from i] [--to j]
 *
 * The answer key is a ledger (see coverage.js). A unit counts as person-level when its decision is
 * item:*, gap, ask, exclude:user, exclude:non-citizen or exclude:past — a measure that reaches a
 * person, whether or not it ended up in the brain. Label the key with --blind, which prints id and
 * text only: seeing the score while labelling would copy the scorer's judgement into the key.
 *
 * A key that covers only some units (a sample drawn with --draw: every flagged unit plus n random
 * unflagged ones) is detected automatically; the miss rate among unflagged units is then estimated
 * from the sample, with a Wilson 95% interval.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const T = require('./text-signals.js');
const { learn } = require('./learn-programmes.js');   // note: disables the stored list on load
const { split } = require('./split-source.js');
const { readLedger } = require('./coverage.js');

const PERSON = /^(item:|gap$|ask$|exclude:(user|non-citizen|past)$)/;

function rng(seed) { let x = seed >>> 0 || 1; return () => ((x = (x * 1664525 + 1013904223) >>> 0) / 2 ** 32); }
function shuffle(a, r) { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }
function wilson(k, n, z = 1.96) {
  if (!n) return [0, 1];
  const p = k / n, d = 1 + z * z / n, c = p + z * z / (2 * n), m = z * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n));
  return [(c - m) / d, (c + m) / d];
}
const pct = x => (100 * x).toFixed(0) + '%';

function scoreYear(speech, learnFrom) {
  if (learnFrom && learnFrom.length) T.setProgrammes(learn(learnFrom).programmes.map(p => p.name));
  else T.setProgrammes([]);
  return split(speech);
}

function benchmark(speech, keyFile, learnFrom) {
  const src = scoreYear(speech, learnFrom);
  const key = new Map(readLedger(keyFile).filter(r => !r.unit.startsWith('prev:')).map(r => [r.unit, r.decision]));
  const units = src.units.filter(u => key.has(u.id));
  const unknown = [...key.keys()].filter(id => !src.units.some(u => u.id === id));
  const sampled = units.length < src.units.length;
  const person = u => PERSON.test(key.get(u.id));

  const F = src.units.filter(u => u.flagged), U = src.units.filter(u => !u.flagged);
  const fKey = F.filter(u => key.has(u.id)), uKey = U.filter(u => key.has(u.id));
  if (sampled && fKey.length < F.length) throw new Error(`sampled key must label every flagged unit (${fKey.length}/${F.length})`);
  const fp = fKey.filter(person).length, up = uKey.filter(person).length;

  const res = {
    source: src.source, year: src.year, learnedFrom: (learnFrom || []).map(f => path.basename(f)),
    units: src.units.length, labelled: units.length, flagged: F.length, flaggedShare: F.length / src.units.length,
    precision: fKey.length ? fp / fKey.length : null, unknown,
    misses: uKey.filter(person).map(u => ({ id: u.id, decision: key.get(u.id), score: u.score, signals: u.signals.join(' '), text: u.text.slice(0, 220) })),
  };
  if (!sampled) {
    res.personUnits = fp + up; res.recallUnits = (fp + up) ? fp / (fp + up) : null;
    const measures = new Map();
    units.filter(person).forEach(u => { const m = key.get(u.id); if (!measures.has(m)) measures.set(m, false); if (u.flagged) measures.set(m, true); });
    // gap/ask/exclude rows each stand for their own measure; item:<slug> rows group by slug
    let caught = 0, total = 0;
    for (const [m, hit] of measures) {
      if (m.startsWith('item:')) { total++; if (hit) caught++; }
    }
    const other = units.filter(u => person(u) && !key.get(u.id).startsWith('item:'));
    total += other.length; caught += other.filter(u => u.flagged).length;
    res.measures = total; res.recallMeasures = total ? caught / total : null;
    res.missedMeasures = [...[...measures].filter(([m, hit]) => m.startsWith('item:') && !hit).map(([m]) => m),
      ...other.filter(u => !u.flagged).map(u => `${key.get(u.id)} ${u.id}`)];
  } else {
    const [lo, hi] = wilson(up, uKey.length);
    const est = r => fp / (fp + r * U.length);
    res.sample = { unflaggedLabelled: uKey.length, unflaggedPerson: up, missRate: up / uKey.length, missRateCI: [lo, hi] };
    res.recallUnits = est(up / uKey.length); res.recallUnitsCI = [est(hi), est(lo)];
    res.personUnitsEstimate = fp + (up / uKey.length) * U.length;
  }
  return res;
}

function print(r) {
  console.log(`\n${r.source} (${r.year}) — programme names learned from: ${r.learnedFrom.length ? r.learnedFrom.join(', ') : 'nothing (cold start)'}`);
  console.log(`  units ${r.units}, labelled ${r.labelled}, flagged ${r.flagged} (${pct(r.flaggedShare)})`);
  if (r.sample) {
    console.log(`  person-level among flagged: ${pct(r.precision)}`);
    console.log(`  unflagged sample: ${r.sample.unflaggedPerson}/${r.sample.unflaggedLabelled} person-level (miss rate ${pct(r.sample.missRate)}, 95% CI ${pct(r.sample.missRateCI[0])}–${pct(r.sample.missRateCI[1])})`);
    console.log(`  estimated catch rate by piece: ${pct(r.recallUnits)} (95% CI ${pct(r.recallUnitsCI[0])}–${pct(r.recallUnitsCI[1])}) of ~${Math.round(r.personUnitsEstimate)} person-level pieces`);
  } else {
    console.log(`  person-level pieces: ${r.personUnits}; caught (flagged): ${pct(r.recallUnits)}`);
    console.log(`  measures: ${r.measures}; caught (any piece flagged): ${pct(r.recallMeasures)}`);
    console.log(`  person-level among flagged: ${pct(r.precision)}`);
  }
  if (r.unknown.length) console.log(`  WARNING: ${r.unknown.length} key rows name units not in the text: ${r.unknown.slice(0, 5).join(', ')}`);
  if (r.missedMeasures) console.log(`  measures with no piece flagged (${r.missedMeasures.length}): ${r.missedMeasures.join(', ')}`);
  console.log(`  missed pieces (${r.misses.length}):`);
  r.misses.forEach(m => console.log(`    ${m.id.padEnd(9)} ${m.decision.padEnd(28)} [${m.score}: ${m.signals}] ${m.text.slice(0, 120)}`));
}

if (require.main === module) {
  const args = process.argv.slice(2);
  const take = (name, n = 1) => { const i = args.indexOf(name); if (i < 0) return undefined; return args.splice(i, n + 1).slice(1); };
  const learnIdx = args.indexOf('--learn-from');
  let learnFrom = [];
  if (learnIdx > -1) { learnFrom = args.splice(learnIdx).slice(1); }
  const draw = take('--draw'), seed = take('--seed'), blind = take('--blind', 0), ids = take('--ids'), from = take('--from'), to = take('--to');
  const [speech, keyFile] = args;
  if (!speech) { console.error('usage: see header of benchmark.js'); process.exit(2); }

  if (draw) {
    const src = scoreYear(speech, learnFrom);
    const r = rng(+(seed || [1])[0]);
    const flagged = src.units.filter(u => u.flagged).map(u => u.id);
    const pick = shuffle(src.units.filter(u => !u.flagged).map(u => u.id), r).slice(0, +draw[0]);
    shuffle(flagged.concat(pick), r).forEach(id => console.log(id));   // shuffled so the flag isn't visible
  } else if (blind) {
    const src = split(speech);
    let units = src.units;
    if (ids) { const want = fs.readFileSync(ids[0], 'utf8').split('\n').map(s => s.trim()).filter(Boolean); const set = new Map(want.map((w, i) => [w, i])); units = units.filter(u => set.has(u.id)).sort((a, b) => set.get(a.id) - set.get(b.id)); }
    units.slice(from ? +from[0] : 0, to ? +to[0] : undefined).forEach(u => {
      const t = u.part === 'lampiran2' ? (u.title + ' — ' + (u.text.includes('Cadangan') ? u.text.slice(u.text.indexOf('Cadangan'), u.text.indexOf('Cadangan') + 700) : u.text.slice(0, 700))) : u.text.slice(0, 1200);
      console.log(`[${u.id}] ${u.section ? '(' + u.section.slice(-60) + ') ' : ''}${t}`);
    });
  } else {
    if (!keyFile) { console.error('need an answer-key ledger'); process.exit(2); }
    print(benchmark(speech, keyFile, learnFrom));
  }
}

module.exports = { benchmark, wilson };
