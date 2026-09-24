#!/usr/bin/env python3
"""Build a standalone HTML preview page for an embed fragment.

Usage:  python make_preview.py EMBED.html OUT.html [--title TEXT] [--width 1200]
        python make_preview.py EMBED.html OUT.html --widths 811:"Artikel sekarang" 1200:"Artikel akan datang"

The embed runs inside a sandboxed iframe (scripts allowed, no same-origin access), so its
media queries react to the chosen width exactly like a real viewport, and it is tested under
the strictest realistic conditions. The page always includes 360 (phone) and 768 (tablet)
buttons; --width adds one more (labelled "Artikel"), or --widths adds several named ones —
use this whenever the user has given more than one article-column measurement to compare
(e.g. a current width and a planned future width), a copy-code button, and placeholder
article text above and below the embed.
"""
import argparse, html, re

PAGE = """<!doctype html>
<html lang="ms"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pratonton: __TITLE__</title>
<style>
html{box-sizing:border-box}*,*:before,*:after{box-sizing:inherit}
body{margin:0;background:#ece9e4;color:#1f2933;font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.bar{position:sticky;top:0;z-index:5;display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:10px 12px;background:#1f2933;color:#fff}
.bar b{margin-right:auto;font-size:.95rem}
.bar button{min-height:40px;padding:6px 14px;border:1px solid #fff;border-radius:999px;background:transparent;color:#fff;font:inherit;font-size:.875rem;cursor:pointer}
.bar button[aria-pressed="true"]{background:#fff;color:#1f2933}
.bar button:focus-visible{outline:3px solid #ffd56b;outline-offset:2px}
.page{max-width:1280px;margin:0 auto;padding:16px 8px 40px}
.stage{max-width:100%;margin:0 auto;background:#fff;box-shadow:0 2px 14px rgba(0,0,0,.14)}
.art{padding:18px 20px;color:#555}
iframe{display:block;width:100%;height:480px;border:0;background:#fff}
.note{max-width:760px;margin:14px auto 0;font-size:.875rem;color:#444}
#srcbox{display:none;width:100%;max-width:760px;height:180px;margin:10px auto 0;font:12px/1.4 ui-monospace,Menlo,monospace}
</style></head>
<body>
<div class="bar" role="toolbar" aria-label="Saiz pratonton">
<b>Pratonton: __TITLE__</b>
__BUTTONS__
<button type="button" id="copy">Salin kod embed</button>
</div>
<div class="page">
<div class="stage" id="stage" style="width:__W__px">
<div class="art"><p>[Perenggan artikel sebelum elemen interaktif]</p></div>
<iframe id="frame" title="Pratonton elemen interaktif" sandbox="allow-scripts" srcdoc="__SRCDOC__"></iframe>
<div class="art"><p>[Perenggan artikel selepas elemen interaktif]</p></div>
</div>
<p class="note" id="note" role="status">Ini pratonton sahaja. Untuk menerbitkan, tampal kod dalam blok Custom HTML (atau tab Text/Code) dan jangan guna tab Visual.</p>
<textarea id="srcbox" readonly aria-label="Kod embed">
__SRC__</textarea>
</div>
<script>
(function () {
  var stage = document.getElementById('stage'), frame = document.getElementById('frame');
  var note = document.getElementById('note'), box = document.getElementById('srcbox');
  var base = note.textContent;
  document.querySelectorAll('[data-w]').forEach(function (b) {
    b.addEventListener('click', function () {
      var w = Number(b.getAttribute('data-w'));
      stage.style.width = w + 'px';
      document.querySelectorAll('[data-w]').forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); });
      note.textContent = window.innerWidth < w ? 'Skrin anda lebih sempit daripada ' + w + 'px, jadi pratonton dipaparkan pada lebar skrin. ' + base : base;
    });
  });
  window.addEventListener('message', function (e) {
    if (e.source === frame.contentWindow && e.data && typeof e.data.tv3PreviewH === 'number') {
      frame.style.height = Math.max(120, e.data.tv3PreviewH) + 'px';
    }
  });
  function say(t) { note.textContent = t; }
  function fallback() {
    box.style.display = 'block'; box.focus(); box.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (err) {}
    say(ok ? 'Kod disalin.' : 'Tekan lama pada kotak kod di bawah, kemudian pilih Salin.');
  }
  document.getElementById('copy').addEventListener('click', function () {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(box.value).then(function () { say('Kod disalin.'); }, fallback);
    } else { fallback(); }
  });
})();
</script>
</body></html>
"""

REPORTER = ("<script>(function(){function s(){parent.postMessage({tv3PreviewH:Math.ceil(document.body.getBoundingClientRect().height)},'*');}"
            "if(window.ResizeObserver){new ResizeObserver(s).observe(document.body);}addEventListener('load',s);s();})();</script>")

def auto_label(w):
    if w <= 480:
        return f"Telefon {w}"
    if w <= 900:
        return f"Tablet {w}"
    return f"Artikel {w}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("embed"); ap.add_argument("out")
    ap.add_argument("--title")
    ap.add_argument("--width", type=int, help="single extra width, labelled 'Artikel <W>'")
    ap.add_argument("--widths", nargs="+", default=[],
                     help='one or more WIDTH or WIDTH:"Label" (e.g. 811:"Artikel sekarang" 1200:"Artikel akan datang")')
    a = ap.parse_args()
    src = open(a.embed, encoding="utf-8").read()
    title = a.title
    if not title:
        m = re.search(r'aria-label\s*=\s*"([^"]+)"', src)
        title = m.group(1) if m else "Elemen interaktif"

    widths = [(360, "Telefon 360"), (768, "Tablet 768")]
    extra = list(a.widths) if a.widths else ([str(a.width)] if a.width else ["1200"])
    for item in extra:
        if ":" in item:
            w_str, label = item.split(":", 1)
            label = label.strip('"')
        else:
            w_str, label = item, None
        w = int(float(w_str))
        widths.append((w, label or auto_label(w)))
    default_w = widths[-1][0]

    buttons = "\n".join(
        f'<button type="button" data-w="{w}" aria-pressed="{"true" if w == default_w else "false"}">{html.escape(label)}</button>'
        for w, label in widths
    )

    doc = ('<!doctype html><html lang="ms"><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width,initial-scale=1">'
           '<style>body{margin:0;display:flow-root;background:#fff;font-family:system-ui,sans-serif}</style></head><body>'
           + src + REPORTER + '</body></html>')
    page = (PAGE.replace("__TITLE__", html.escape(title)).replace("__BUTTONS__", buttons)
            .replace("__W__", str(default_w))
            .replace("__SRCDOC__", html.escape(doc, quote=True)).replace("__SRC__", html.escape(src, quote=False)))
    open(a.out, "w", encoding="utf-8").write(page)
    labels = ", ".join(f"{label} ({w}px)" for w, label in widths)
    print(f"preview written: {a.out} ({len(page)//1024} KB) — widths: {labels}")

if __name__ == "__main__":
    main()
