const B = require('./belanjawan2026-brain.js');
const fs = require('fs');
const opName = {eq:'=',ne:'≠',in:'∈',nin:'∉',gte:'≥',gt:'>',lte:'≤',lt:'<',has:'includes',hasAny:'includes any of'};
function expr(c){
  if(c.all) return c.all.map(x=>{const s=expr(x);return (x.any)?`(${s})`:s;}).join(' AND ');
  if(c.any) return c.any.map(x=>{const s=expr(x);return (x.all)?`(${s})`:s;}).join(' OR ');
  if(c.not) return `NOT(${expr(c.not)})`;
  const op = Object.keys(opName).find(k=>k in c);
  let v = c[op]; v = Array.isArray(v)? '['+v.join(', ')+']' : (v===Infinity?'∞':v);
  return `${c.f} ${opName[op]} ${v}`;
}
const esc = s => String(s).replace(/\|/g,'\\|').replace(/\n/g,' ');
let md = '';
md += `## Questions (${B.QUESTIONS.length})\n\n| # | id | Type | Question | Shown when | Options (value → label) |\n|---|---|---|---|---|---|\n`;
B.QUESTIONS.forEach((q,i)=>{
  const opts = q.options ? q.options.map(o=>`\`${o.v}\` ${esc(o.l)}${o.exclusive?' *(exclusive)*':''}`).join('<br>') : `number ${q.min}–${q.max}`;
  md += `| ${i+1} | \`${q.id}\` | ${q.type} | ${esc(q.text)} | ${q.showIf?'`'+expr(q.showIf)+'`':'always'} | ${opts} |\n`;
});
md += `\n## Rule matrix (${B.BENEFITS.length} items)\n\n`;
B.THEMES.forEach(t=>{
  const items = B.BENEFITS.filter(b=>b.theme===t.id);
  md += `### ${t.label} (\`${t.id}\`, ${items.length})\n\n| id | Item | Kind | What the person gets / pays | Rule (\`when\`) | Certainty | Source | Timing |\n|---|---|---|---|---|---|---|---|\n`;
  items.forEach(b=>{
    md += `| \`${b.id}\` | ${esc(b.title)} | ${b.kind} | ${esc(b.value)} | \`${esc(expr(b.when))}\` | ${b.certainty} | ${esc(b.src)}${b.web?` · [web](${b.web})`:''} | ${b.timing?esc(b.timing):'—'} |\n`;
  });
  md += '\n';
});
fs.writeFileSync('_generated.md', md);
console.log('generated', md.length, 'chars');
