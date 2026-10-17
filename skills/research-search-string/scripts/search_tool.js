#!/usr/bin/env node
/*
 * search_tool.js: build and check Boolean search strings for Scopus,
 * Web of Science and Google Scholar, in tiers (broad / balanced / narrow)
 * and for one or more year ranges.
 *
 * Usage:
 *   node search_tool.js strings spec.json     prints every string and any warnings
 *   node search_tool.js plan spec.json        prints the search log skeleton (JSON):
 *                                             one row per tier x year range x database,
 *                                             with the string and a ready search URL
 *   node search_tool.js check "query" [scopus|wos|scholar]   lints a pasted string
 *
 * spec.json is one object:
 * {
 *   "title": "OTT Streaming Adoption among Malaysian Consumers: A Systematic Literature Review",
 *   "field": "Communication & Media Studies",
 *   "ranges": [[2016, 2020], [2021, 2026]],      // or "years": [2022, 2026] for one range
 *   "concepts": [ { "name": "OTT and streaming", "terms": ["\"video on demand\"", "OTT"] }, ... ],
 *   "tiers": { "broad": [1, 2], "balanced": [1, 2, 3], "narrow": [1, 2, 3, 4] },   // optional; concept numbers
 *   "scholar": ["short string A", "short string B"],   // no truncation, 256 characters or fewer
 *   "local": "optional separate local-language string", "localLanguage": "Malay"   // "malay" also accepted
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
  const rawRanges = Array.isArray(spec.ranges) && spec.ranges.length ? spec.ranges
    : Array.isArray(spec.years) && spec.years.length === 2 ? [spec.years] : [[thisYear - 4, thisYear]];
  const ranges = rawRanges.map((r, i) => {
    const what = rawRanges.length > 1 ? `year range ${i + 1}` : 'years';
    if (!Array.isArray(r) || r.length !== 2) fail(`${at}${what} must be two whole years such as [2022, 2026].`);
    let [y0, y1] = r.map(Number);
    if (!Number.isInteger(y0) || !Number.isInteger(y1)) fail(`${at}${what} must be two whole years such as [2022, 2026].`);
    if (y0 > y1) { notes.push(`${at}${what} were reversed, swapped to ${y1}-${y0}`); [y0, y1] = [y1, y0]; }
    if (y0 < 1900 || y1 > thisYear + 1) fail(`${at}${what} ${y0}-${y1} look wrong; expected between 1900 and ${thisYear + 1}.`);
    return [y0, y1];
  });
  const k = concepts.length;
  let tiers = spec.tiers;
  if (tiers === undefined || tiers === null) {
    // Broad drops the population and niche blocks; narrow keeps every block.
    tiers = k >= 4 ? { broad: [1, 2], balanced: [1, 2, 3], narrow: concepts.map((_, i) => i + 1) }
      : k === 3 ? { broad: [1, 2], balanced: [1, 2, 3] }
      : { main: concepts.map((_, i) => i + 1) };
  }
  if (typeof tiers !== 'object' || Array.isArray(tiers) || !Object.keys(tiers).length) fail(`${at}"tiers" must map a tier name to concept numbers, e.g. {"broad": [1, 2]}.`);
  const tierList = Object.entries(tiers).map(([name, nums]) => {
    if (!Array.isArray(nums) || !nums.length || nums.some(n => !Number.isInteger(n) || n < 1 || n > k)) fail(`${at}tier "${name}" must list concept numbers from 1 to ${k}.`);
    return { name, concepts: [...new Set(nums)].sort((a, b) => a - b) };
  });
  let scholar = spec.scholar === undefined || spec.scholar === null ? [] : spec.scholar;
  if (typeof scholar === 'string') scholar = [scholar];
  if (!Array.isArray(scholar) || scholar.some(x => typeof x !== 'string')) fail(`${at}"scholar" must be an array of strings.`);
  // "malay" is the original key; "local" is the same thing for any other language.
  const localRaw = spec.local !== undefined && spec.local !== null ? spec.local : spec.malay;
  if (localRaw !== undefined && localRaw !== null && typeof localRaw !== 'string') fail(`${at}"local" (or "malay") must be a string.`);
  const language = typeof spec.localLanguage === 'string' && spec.localLanguage.trim()
    ? spec.localLanguage.trim() : (spec.local ? 'local-language' : 'Malay');
  return Object.assign({}, spec, {
    concepts, ranges, years: ranges[0], tiers: tierList, notes, language,
    scholar: scholar.map(tidy).filter(Boolean), malay: tidy(localRaw || '')
  });
}

function buildStrings(spec, tier, range) {
  const [y0, y1] = range || spec.ranges[0];
  const nums = tier ? tier.concepts : spec.concepts.map((_, i) => i + 1);
  const body = nums.map(n => '(' + join(spec.concepts[n - 1].terms) + ')').join(' AND ');
  return {
    y0, y1, body,
    scopus: `TITLE-ABS-KEY(${body}) AND PUBYEAR > ${y0 - 1} AND PUBYEAR < ${y1 + 1}`,
    wos: `TS=(${body}) AND PY=(${y0}-${y1})`,
    scholar: spec.scholar,
    malay: spec.malay
  };
}

const scholarUrl = (q, y0, y1) => 'https://scholar.google.com/scholar?' +
  `q=${encodeURIComponent(q)}&as_ylo=${y0}&as_yhi=${y1}&hl=en`;

/* One row per tier x year range x database: the skeleton of the search log. */
function plan(spec) {
  const runs = [];
  spec.ranges.forEach(range => {
    const [y0, y1] = range;
    spec.tiers.forEach(tier => {
      const s = buildStrings(spec, tier, range);
      const row = (database, string, url) => runs.push({
        tier: tier.name, range: `${y0}-${y1}`, database, string, url: url || null,
        hits: null, source: null, date: null, note: ''
      });
      row('Scopus', s.scopus, 'https://www.scopus.com/search/form.uri?display=advanced');
      row('Web of Science', s.wos, 'https://www.webofscience.com/wos/woscc/advanced-search');
    });
    // Scholar strings are written by hand and shared by every tier; only the dates change.
    spec.scholar.forEach((g, i) => runs.push({
      tier: 'all', range: `${y0}-${y1}`, database: `Google Scholar ${String.fromCharCode(65 + i)}`,
      string: g, url: scholarUrl(g, y0, y1), hits: null, source: null, date: null, note: ''
    }));
    if (spec.malay) runs.push({
      tier: 'all', range: `${y0}-${y1}`, database: `Google Scholar (${spec.language})`,
      string: spec.malay, url: scholarUrl(spec.malay, y0, y1), hits: null, source: null, date: null, note: ''
    });
  });
  return runs;
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
  spec.tiers.forEach(tier => {
    const s = buildStrings(spec, tier, spec.ranges[0]);
    w.push(...lintString(s.scopus, 'scopus', `Scopus string (${tier.name})`));
    w.push(...lintString(s.wos, 'wos', `Web of Science string (${tier.name})`));
  });
  spec.scholar.forEach((g, i) => w.push(...lintString(g, 'scholar', `Scholar string ${String.fromCharCode(65 + i)}`)));
  if (spec.malay) w.push(...lintString(spec.malay, 'scholar', `${spec.language} string`));
  if (!spec.scholar.length) w.push('No Scholar strings yet. Scholar cannot take the long Scopus string, so write two short ones under "scholar".');
  return [...new Set(w)].concat(spec.notes.map(n => 'Fixed: ' + n));
}

function printStrings(spec) {
  console.log(`# ${spec.title || 'Untitled'}\n`);
  spec.concepts.forEach((c, i) => console.log(`Concept ${i + 1}: ${c.name}`));
  console.log('Tiers: ' + spec.tiers.map(t => `${t.name} = concepts ${t.concepts.join(', ')}`).join('; ') + '\n');
  spec.ranges.forEach(range => {
    const [y0, y1] = range;
    console.log(`=============== ${y0} to ${y1} ===============\n`);
    spec.tiers.forEach(tier => {
      const s = buildStrings(spec, tier, range);
      console.log(`## Scopus, ${tier.name} (Advanced search)\n${s.scopus}\n(${s.scopus.length} characters)\n`);
      console.log(`## Web of Science, ${tier.name} (Advanced search, Core Collection)\n${s.wos}\n(${s.wos.length} characters)\n`);
    });
    spec.scholar.forEach((g, i) => console.log(`## Google Scholar, version ${String.fromCharCode(65 + i)} (set ${y0} to ${y1} in the left menu)\n${g}\n(${g.length} characters)\n${scholarUrl(g, y0, y1)}\n`));
    if (spec.malay) console.log(`## Google Scholar, ${spec.language}-language (run separately)\n${spec.malay}\n(${spec.malay.length} characters)\n${scholarUrl(spec.malay, y0, y1)}\n`);
  });
  const w = validate(spec);
  console.log(w.length ? '## Warnings\n- ' + w.join('\n- ') : '## Warnings\nNone.');
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
  if (!mode || !a) fail('Usage: node search_tool.js strings|plan spec.json  or  node search_tool.js check "query" [scopus|wos|scholar]');
  if (mode === 'check') return checkRaw(a, b);
  const specs = readSpecs(a);
  if (mode === 'strings') specs.forEach((s, i) => { if (i) console.log('\n----------------\n'); printStrings(s); });
  else if (mode === 'plan') {
    const out = specs.map(s => ({
      title: s.title || '', ranges: s.ranges.map(([y0, y1]) => `${y0}-${y1}`),
      tiers: s.tiers, concepts: s.concepts, runs: plan(s)
    }));
    console.log(JSON.stringify(out.length === 1 ? out[0] : out, null, 2));
  } else fail('Unknown mode: ' + mode + ' (use strings, plan or check)');
}

Promise.resolve().then(main).catch(e => {
  if (e instanceof SpecError) { console.error('Error: ' + e.message); process.exit(1); }
  throw e;
});
