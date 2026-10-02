#!/usr/bin/env node
// Node port of make_preview.py, for machines without Python. Same output; the page template is read from make_preview.py
// itself so the two never drift. Usage below.
// Usage: node make_preview.js EMBED.html OUT.html [--title T] [--widths 820:"Artikel sekarang" 1200:"Artikel akan datang"] [--default-width W]
var fs = require('fs');
var argv = process.argv.slice(2), pos = [], title = null, widthsArg = [], defW = null;
for (var i = 0; i < argv.length; i++) {
  if (argv[i] === '--title') title = argv[++i];
  else if (argv[i] === '--default-width') defW = +argv[++i];
  else if (argv[i] === '--widths') { while (argv[i + 1] && argv[i + 1].indexOf('--') !== 0) widthsArg.push(argv[++i]); }
  else pos.push(argv[i]);
}
function esc(s, quote) {
  s = s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  return quote ? s.replace(/"/g, '&quot;').replace(/'/g, '&#x27;') : s;
}
var src = fs.readFileSync(pos[0], 'utf8');
if (!title) { var m = /aria-label\s*=\s*"([^"]+)"/.exec(src); title = m ? m[1] : 'Elemen interaktif'; }
function autoLabel(w) { return w <= 480 ? 'Telefon ' + w : w <= 900 ? 'Tablet ' + w : 'Artikel ' + w; }
var widths = [[360, 'Telefon 360'], [768, 'Tablet 768']];
(widthsArg.length ? widthsArg : ['1200']).forEach(function (it) {
  var k = it.indexOf(':'), w = Math.floor(parseFloat(k < 0 ? it : it.slice(0, k))), label = k < 0 ? null : it.slice(k + 1).replace(/^"|"$/g, '');
  widths.push([w, label || autoLabel(w)]);
});
defW = defW || widths[0][0];
var buttons = widths.map(function (w) { return '<button type="button" data-w="' + w[0] + '" aria-pressed="' + (w[0] === defW) + '">' + esc(w[1]) + '</button>'; }).join('\n');
var REPORTER = "<script>(function(){function s(){parent.postMessage({tv3PreviewH:Math.ceil(document.body.getBoundingClientRect().height)},'*');}" +
  "if(window.ResizeObserver){new ResizeObserver(s).observe(document.body);}addEventListener('load',s);s();})();</script>";
var doc = '<!doctype html><html lang="ms"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
  '<style>body{margin:0;display:flow-root;background:#fff;font-family:system-ui,sans-serif}</style></head><body>' + src + REPORTER + '</body></html>';
var py = fs.readFileSync(__dirname + '/make_preview.py', 'utf8'), a = py.indexOf('PAGE = """') + 10;
var PAGE = py.slice(a, py.indexOf('"""', a));
var page = PAGE.split('__TITLE__').join(esc(title)).replace('__BUTTONS__', function () { return buttons; })
  .replace('__W__', String(defW)).replace('__SRCDOC__', function () { return esc(doc, true); }).replace('__SRC__', function () { return esc(src, false); });
fs.writeFileSync(pos[1], page);
console.log('preview written: ' + pos[1] + ' (' + Math.floor(page.length / 1024) + ' KB) — widths: ' + widths.map(function (w) { return w[1] + ' (' + w[0] + 'px)'; }).join(', '));
