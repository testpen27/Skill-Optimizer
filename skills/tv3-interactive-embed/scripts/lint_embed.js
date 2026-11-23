#!/usr/bin/env node
// Node port of lint_embed.py, for machines without Python. Keep the two in step: same checks, same levels.
// Same checks, same levels. Usage: node lint_embed.js FILE [--root ID] [--allow-host HOST ...]
var fs = require('fs');
var args = process.argv.slice(2), file = null, rootArg = null, allow = {};
for (var i = 0; i < args.length; i++) {
  if (args[i] === '--root') rootArg = args[++i];
  else if (args[i] === '--allow-host') allow[args[++i]] = 1;
  else file = args[i];
}
var html = fs.readFileSync(file, 'utf8');
var findings = [];
// buletintv3.my's theme is Bootstrap: these classes on embed elements pick up theme rules (see lint_embed.py).
var BOOTSTRAP = ['card','badge','btn','lead','small','progress','nav','alert','row','col','container','table','collapse','modal','dropdown','active','show','fade','close','visually-hidden','list-group','form-control','form-check','form-label','input-group','carousel','toast','tooltip','popover','accordion','spinner-border','placeholder','ratio','sticky-top','h1','h2','h3','h4','h5','h6','display-1','fw-bold','mb-3','border','rounded','shadow'];
function lineOf(pos) { return html.slice(0, pos).split('\n').length; }
function add(level, pos, msg, withLine) { findings.push([level, withLine === false || pos == null ? 0 : lineOf(Math.max(0, pos)), msg]); }
function blankBlocks(h) {
  return h.replace(/(<(?:script|style)\b[^>]*>)([\s\S]*?)(<\/(?:script|style)>)/gi, function (_, a, body, c) {
    return a + body.split('\n').map(function (ln) { return new Array(Math.max(1, ln.length) + 1).join('x'); }).join('\n') + c;
  });
}
function cssRules(css, out) {
  out = out || []; css = css.replace(/\/\*[\s\S]*?\*\//g, '');
  var i = 0, n = css.length;
  while (i < n) {
    var j = css.indexOf('{', i); if (j === -1) break;
    var prelude = css.slice(i, j).trim(), depth = 1, k = j + 1;
    while (k < n && depth) { depth += (css[k] === '{') - (css[k] === '}'); k++; }
    var body = css.slice(j + 1, k - 1); i = k;
    if (prelude[0] === '@') {
      var name = prelude.split(/\s+/)[0].toLowerCase();
      if (['@media', '@supports', '@layer', '@container'].indexOf(name) !== -1) cssRules(body, out);
      else if (name.indexOf('keyframes') !== -1) out.push(['keyframes', prelude, body]);
      else out.push(['other', prelude, body]);
    } else out.push(['rule', prelude, body]);
  }
  return out;
}
function splitSelectors(sel) {
  var out = [], depth = 0, cur = '';
  for (var i = 0; i < sel.length; i++) {
    var ch = sel[i]; if ('(['.indexOf(ch) !== -1) depth++; if (')]'.indexOf(ch) !== -1) depth--;
    if (ch === ',' && depth === 0) { out.push(cur.trim()); cur = ''; } else cur += ch;
  }
  out.push(cur.trim()); return out.filter(Boolean);
}
function each(re, s, fn) { var m; re.lastIndex = 0; while ((m = re.exec(s))) { fn(m); if (m[0] === '') re.lastIndex++; } }
function esc(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

var markup = blankBlocks(html);
var bytes = Buffer.byteLength(html);
if (bytes > 150000) add('WARN', null, 'file is ' + Math.floor(html.length / 1000) + ' KB; large pastes can be truncated or slow the article', false);
each(/<(html|head|body)\b/gi, markup, function (m) { add('WARN', m.index, '<' + m[1] + '> tag in a fragment; CMS strips or nests it badly'); });
each(/<script\b[^>]*\bsrc\s*=\s*["']([^"']+)/gi, html, function (m) {
  var host = (/^(?:https?:)?\/\/([^\/]+)/.exec(m[1]) || [])[1] || '';
  if (allow[host]) { if (m[1].indexOf('@latest') !== -1 || !/@\d+\.\d+/.test(m[1])) add('ERROR', m.index, 'approved host ' + host + ' but script version is not pinned: ' + m[1]); }
  else add('ERROR', m.index, 'third-party script needs user approval: ' + m[1]);
});
each(/<link\b[^>]*\bhref\s*=\s*["'](https?:)?\/\/([^"'\/]+)[^"']*/gi, html, function (m) { if (!allow[m[2]]) add('ERROR', m.index, 'third-party stylesheet/font needs user approval: ' + m[2]); });
each(/@import[^;]+;|url\(\s*["']?https?:\/\/[^)]+\)/gi, html, function (m) { add('ERROR', m.index, 'remote CSS resource: ' + m[0].slice(0, 80)); });
each(/<(iframe|object|embed)\b[^>]*>/gi, markup, function (m) {
  var hidden = /display\s*:\s*none|width\s*=\s*["']?0|height\s*=\s*["']?0/i.test(m[0]);
  add(hidden ? 'ERROR' : 'WARN', m.index, '<' + m[1] + '> present' + (hidden ? ' and hidden' : '; confirm it is approved'));
});
each(/<form\b[^>]*\baction\s*=/gi, markup, function (m) { add('WARN', m.index, 'form with action: data leaves the page; confirm destination'); });
each(/javascript:|data:text\/html/gi, markup, function (m) { add('ERROR', m.index, 'javascript:/data:text/html URL'); });
each(/<a\b[^>]*target\s*=\s*["']_blank["'][^>]*>/gi, markup, function (m) { if (m[0].toLowerCase().indexOf('noopener') === -1) add('WARN', m.index, 'target="_blank" without rel="noopener noreferrer"'); });
each(/<p>\s*<script/gi, html, function (m) { add('WARN', m.index, '<script> wrapped in <p> (editor auto-paragraph damage)'); });
var blanks = []; each(/\n[ \t\r]*\n/g, markup, function (m) { blanks.push(m.index); });
if (blanks.length) add('WARN', blanks[0], blanks.length + ' blank line(s) inside markup; WordPress may insert <p>/<br> there');

var root = rootArg;
if (!root) { var rm = /<[a-z][^>]*\bid\s*=\s*["']([^"']+)/i.exec(markup); root = rm ? rm[1] : null; }
if (!root) add('ERROR', null, 'no root element id found; wrap everything in one <div id="emb-...">', false);
each(/<style\b[^>]*>([\s\S]*?)<\/style>/gi, html, function (sm) {
  cssRules(sm[1]).forEach(function (r) {
    var kind = r[0], prelude = r[1], body = r[2];
    if (kind === 'other' && prelude.toLowerCase().indexOf('@font-face') === 0) add('WARN', html.indexOf(prelude), '@font-face: confirm the font file is approved and licensed');
    if (kind !== 'rule') return;
    var pos = html.indexOf(prelude.slice(0, 40));
    splitSelectors(prelude).forEach(function (s) {
      if (root && !new RegExp('^#' + esc(root) + '(?![\\w-])').test(s)) add('ERROR', pos, 'selector leaks into the host page: `' + s.slice(0, 60) + '`');
      each(/\.(-?[A-Za-z_][\w-]*)/g, s, function (c) {
        if (BOOTSTRAP.indexOf(c[1]) !== -1 || /^(?:col|d|text|bg|m[trblxy]?|p[trblxy]?|g[xy]?)-/.test(c[1]))
          add('WARN', pos, 'class `.' + c[1] + '` is also a Bootstrap class on buletintv3.my; theme rules leak in (any property you don\'t set). Prefix it, e.g. `.emb-' + c[1] + '`');
      });
    });
    if (/(^|;)\s*height\s*:\s*\d+px/.test(body) && /overflow\s*:\s*hidden/.test(body)) add('WARN', pos, 'fixed height + overflow:hidden: `' + prelude.slice(0, 50) + '`');
  });
});
each(/(?:^|[;{])\s*width\s*:\s*(\d+)px/gm, html, function (m) { if (+m[1] >= 300) add('WARN', m.index, 'fixed width:' + m[1] + 'px; a 320-360px phone viewport can\'t shrink this'); });
each(/<(input|textarea|select)\b[^>]*\bstyle\s*=\s*["'][^"']*font-size\s*:\s*(\d+(?:\.\d+)?)px/gi, html, function (m) { if (+m[2] < 16) add('ERROR', m.index, '<' + m[1] + '> font-size ' + m[2] + 'px; use >= 16px or iOS auto-zooms'); });
each(/font-size\s*:\s*(\d+(?:\.\d+)?)px/g, html, function (m) { if (+m[1] < 14) add('ERROR', m.index, 'font-size ' + m[1] + 'px; body text must be >= 14px'); });
var small = []; each(/text-\[(\d+(?:\.\d+)?)px\]/g, html, function (m) { if (+m[1] < 14) small.push(m[1]); });
if (small.length) add('ERROR', null, small.length + ' Tailwind classes set text below 14px', false);

var hard = [[/\beval\s*\(/g, 'eval()'], [/\bnew\s+Function\b/g, 'new Function()'], [/document\.write\s*\(/g, 'document.write()'],
  [/document\.cookie/g, 'cookie access'], [/sendBeacon|new\s+WebSocket|importScripts/g, 'beacon/websocket/importScripts'],
  [/\b(?:window\.)?top\.(?:location|document)|window\.top\b|document\.domain/g, 'reaches the host page/top window'],
  [/createElement\(\s*["']script["']\s*\)/g, 'injects a <script> element (remote code)'], [/\.src\s*=\s*["']https?:/g, 'assigns a remote src']];
var soft = [[/localStorage|sessionStorage|indexedDB/g, 'browser storage: fine for harmless state only; disclose to user'],
  [/\bfetch\s*\(|XMLHttpRequest/g, 'network request: confirm destination is approved'],
  [/window\.open|location\.(?:href|assign|replace)\s*=/g, 'navigation from script'],
  [/\b(?:atob|btoa)\s*\(|String\.fromCharCode/g, 'encoding helpers (check for obfuscation)'],
  [/\bon(?:click|load|error|mouse\w+|touch\w+)\s*=/g, 'inline event handler (prefer addEventListener)']];
each(/<script\b(?![^>]*\bsrc\b)[^>]*>([\s\S]*?)<\/script>/gi, html, function (m) {
  var code = m[1], off = m.index + m[0].indexOf(code);
  hard.forEach(function (h) { each(h[0], code, function (x) { add('ERROR', off + x.index, 'script: ' + h[1]); }); });
  soft.forEach(function (s) { s[0].lastIndex = 0; var x = s[0].exec(code); if (x) add('WARN', off + x.index, 'script: ' + s[1]); });
  var ih = /(?:innerHTML|outerHTML|insertAdjacentHTML)[^\n;]*\$\{/.exec(code);
  if (ih) add('WARN', off + ih.index, 'script: HTML built with ${...}; make sure no user-typed text is interpolated');
  var amps = code.split('&').length - 1;
  if (amps) add('ERROR', off + code.indexOf('&'), 'script contains ' + amps + ' `&` character(s). WordPress rewrites `&` inside pasted content (seen live on buletintv3.my: `&&` -> `&#038;&#038;`), a SyntaxError, so the script never runs. Use nested if/ternary instead of `&&`, \\u0026 inside strings, and no `&` in comments');
  var longLine = code.split('\n').some(function (l) { return l.length > 1500; });
  if (/[A-Za-z0-9+\/=]{200,}/.test(code) || /(?:\\x[0-9a-fA-F]{2}){10,}/.test(code) || longLine) add('ERROR', off, 'script: possible obfuscated/encoded payload (very long line or base64/hex blob)');
});
var ie = /\bon(?:click|load|error|mouse\w+|touch\w+)\s*=/i.exec(markup);
if (ie) add('WARN', ie.index, 'inline event handler attribute (prefer addEventListener)');

findings.sort(function (a, b) { return ((a[0] !== 'ERROR') - (b[0] !== 'ERROR')) || (a[1] - b[1]); });
var seen = {}, errs = 0;
findings.forEach(function (f) {
  if (f[0] === 'ERROR') errs++;
  var key = f[0] + f[2]; if (seen[key]) return; seen[key] = 1;
  console.log((f[0] + '     ').slice(0, 5) + (f[1] ? ' line ' + ('    ' + f[1]).slice(-4) + '  ' : '            ') + f[2]);
});
console.log('\n' + errs + ' error(s), ' + (findings.length - errs) + ' warning(s) [root: #' + root + '] (' + Math.round(bytes / 1024) + ' KB)');
process.exit(errs ? 1 : 0);
