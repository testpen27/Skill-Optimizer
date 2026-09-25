/* Verification round 2: randomised simulation of 30,000 users walking the real question flow.
   Checks invariants independently of the hand-written tests. Run: node verify2.js */
const B = require('./belanjawan2026-brain.js');
let seed = 20260925; const rnd = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648;
const pick = a => a[Math.floor(rnd() * a.length)];
const violations = {}; const bump = (k, ex) => { violations[k] = violations[k] || { n: 0, ex }; violations[k].n++; };
const ALLOWED_TOTALS = new Set([600, 1200, 1400, 1650, 1900, 2150, 2400, 2900, 3400, 1800, 2600, 2850, 3100, 3350, 3600, 4100, 4600]);

function simulate() {
  let a = {};
  for (let guard = 0; guard < 30; guard++) {
    const q = B.getVisibleQuestions(a).find(q => a[q.id] === undefined);
    if (!q) break;
    if (q.type === 'number') a[q.id] = Math.floor(rnd() * 90) + 5;
    else if (q.type === 'single') a[q.id] = pick(q.options).v;
    else {
      const excl = q.options.filter(o => o.exclusive), normal = q.options.filter(o => !o.exclusive);
      a[q.id] = rnd() < 0.3 ? [pick(excl).v] : normal.filter(() => rnd() < 0.3).map(o => o.v);
      if (!a[q.id].length) a[q.id] = ['none'];
    }
    a = B.pruneAnswers(a);
  }
  return a;
}

const N = 30000; let totalResults = 0; const seen = new Set(); const themeSeen = new Set();
for (let i = 0; i < N; i++) {
  const a = simulate();
  let r; try { r = B.evaluate(a); } catch (e) { bump('V0 evaluate threw', e.message); continue; }
  const f = r.facts, s = r.strSara;
  totalResults += r.results.length; r.results.forEach(x => { seen.add(x.id); themeSeen.add(x.theme); });

  // V1 flow completes and prune is idempotent
  if (!B.isComplete(a)) bump('V1 flow incomplete', a);
  if (JSON.stringify(B.pruneAnswers(a)) !== JSON.stringify(a)) bump('V2 prune not idempotent', a);
  // V3 no "mungkin" unless the user skipped something or answered "Tidak pasti"
  const uncertain = Object.values(a).some(v => [].concat(v).includes('skip') || v === 'unsure');
  if (!uncertain && r.counts.mungkin > 0) bump('V3 mungkin without skip/unsure', { a, m: r.results.filter(x => x.tier === 'mungkin').map(x => x.id) });
  // V4 every shown item re-tests as not-false; every hidden item re-tests false
  const shown = new Set(r.results.map(x => x.id));
  B.BENEFITS.forEach(b => { const v = B._test(b.when, f).v; if (shown.has(b.id) === (v === false)) bump('V4 result/rule mismatch ' + b.id, a); });
  // V5 kesan items always tier kesan; manfaat never kesan
  r.results.forEach(x => { if ((x.kind === 'kesan') !== (x.tier === 'kesan')) bump('V5 kind/tier mismatch', x.id); });
  // V6 STR invariants
  if (s.eligible === true) {
    if (s.total !== s.str + s.sara) bump('V6a total != str+sara', s);
    if (!ALLOWED_TOTALS.has(s.total)) bump('V6b total not in speech table', { total: s.total, cat: s.category, e: f.ekasih });
    if (s.total > 4600) bump('V6c total > 4600', s);
    if (!(f.incomeMax <= 5000)) bump('V6d eligible above RM5k', a);
    if (s.category === 'bujang' && !(f.age >= 21 && f.age <= 59 && f.income === 'lt2500')) bump('V6e bujang rule', a);
    if (s.category === 'warga_emas' && !(f.age >= 60 && f.marital === 'single' && f.childCount === 0)) bump('V6f warga emas rule', a);
    if (!shown.has('str_sara')) bump('V6g STR card missing', a);
  }
  if (f.age < 18 && s.eligible !== false) bump('V6h minor STR', a);
  // V7 minors: nothing adult-only, nothing lifestyle, no tax unless taxpayer ticked
  if (f.age < 18) ['penghargaan_sara', 'fi_klinik_swasta', 'duti_rokok', 'duti_alkohol', 'payung_rahmah'].forEach(id => shown.has(id) && bump('V7 minor got ' + id, a));
  r.results.filter(x => x.theme === 'tax').forEach(x => { if (!f.assets.includes('taxpayer')) bump('V8 tax without taxpayer', x.id); });
  // V9 grouped output covers all results, sorted by tier rank
  const flat = r.byTheme.flatMap(g => g.items); if (flat.length !== r.results.length) bump('V9 byTheme count', a);
  r.byTheme.forEach(g => g.items.forEach((x, k) => { if (k && B.TIERS[g.items[k - 1].tier].rank > B.TIERS[x.tier].rank) bump('V9b sort order', g.id); }));
  // V10 every "mungkin" item explains what needs confirming
  r.results.filter(x => x.tier === 'mungkin').forEach(x => { if (!x.needsConfirm.length) bump('V10 mungkin without needsConfirm', x.id); });
  // V11 every layak/semak item has at least one reason (except universal items)
  r.results.filter(x => x.tier !== 'mungkin').forEach(x => { if (!x.reasons.length) bump('V11 no reason ' + x.id, a); });
  // V12 advisories always end with disclaimer
  if (r.advisories[r.advisories.length - 1].type !== 'disclaimer') bump('V12 disclaimer', a);
}
const never = B.BENEFITS.map(b => b.id).filter(id => !seen.has(id));
console.log(`Verification round 2: ${N} simulated users, avg ${(totalResults / N).toFixed(1)} results each.`);
console.log(`Items reachable: ${seen.size}/${B.BENEFITS.length}${never.length ? '  NEVER SHOWN: ' + never.join(', ') : ''}`);
console.log(`Themes reachable: ${themeSeen.size}/${B.THEMES.length}`);
const keys = Object.keys(violations);
if (!keys.length) console.log('Invariant violations: 0');
else keys.forEach(k => console.log(`  VIOLATION ${k}  x${violations[k].n}  e.g. ${JSON.stringify(violations[k].ex).slice(0, 300)}`));
process.exit(keys.length || never.length ? 1 : 0);
