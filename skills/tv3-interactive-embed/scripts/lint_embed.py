#!/usr/bin/env python3
"""Lint a paste-into-CMS HTML embed for safety and CMS-compatibility problems.

Usage:  python lint_embed.py FILE [--root ROOT_ID] [--allow-host HOST ...]
Exit code 1 if any ERROR is found (WARN never fails the run).
Heuristic, regex-based: it catches the common problems, it is not a security proof.
"""
import argparse, re, sys
from urllib.parse import urlparse

findings = []
def add(level, pos, msg, text=""):
    line = text.count("\n", 0, pos) + 1 if text else 0
    findings.append((level, line, msg))

def blank_blocks(html):
    """Replace <script>/<style> bodies with 'x' lines so markup checks ignore them."""
    def rep(m):
        body = "\n".join("x" * max(1, len(ln)) for ln in m.group(2).split("\n"))
        return m.group(1) + body + m.group(3)
    return re.sub(r"(<(?:script|style)\b[^>]*>)(.*?)(</(?:script|style)>)", rep, html, flags=re.S | re.I)

def css_rules(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    i, n = 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j == -1:
            break
        prelude = css[i:j].strip()
        depth, k = 1, j + 1
        while k < n and depth:
            depth += (css[k] == "{") - (css[k] == "}")
            k += 1
        body, i = css[j + 1:k - 1], k
        if prelude.startswith("@"):
            name = prelude.split()[0].lower()
            if name in ("@media", "@supports", "@layer", "@container"):
                yield from css_rules(body)
            elif "keyframes" in name:
                yield ("keyframes", prelude, body)
            else:
                yield ("other", prelude, body)
        else:
            yield ("rule", prelude, body)

def split_selectors(sel):
    out, depth, cur = [], 0, ""
    for ch in sel:
        depth += ch in "([" ; depth -= ch in ")]"
        if ch == "," and depth == 0:
            out.append(cur.strip()); cur = ""
        else:
            cur += ch
    out.append(cur.strip())
    return [s for s in out if s]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--root", help="root element id (auto-detected if omitted)")
    ap.add_argument("--allow-host", action="append", default=[],
                    help="third-party host the USER has approved (repeatable)")
    a = ap.parse_args()
    html = open(a.file, encoding="utf-8", errors="replace").read()
    allow = set(a.allow_host)
    markup = blank_blocks(html)

    # size
    if len(html.encode()) > 150_000:
        add("WARN", 0, f"file is {len(html)//1000} KB; large pastes can be truncated or slow the article")

    # document-level tags
    for m in re.finditer(r"<(html|head|body)\b", markup, re.I):
        add("WARN", m.start(), f"<{m.group(1)}> tag in a fragment; CMS strips or nests it badly", html)

    # third-party loads
    for m in re.finditer(r"<script\b[^>]*\bsrc\s*=\s*[\"']([^\"']+)", html, re.I):
        host = urlparse(m.group(1)).netloc
        if host in allow:
            if "@latest" in m.group(1) or not re.search(r"@\d+\.\d+", m.group(1)):
                add("ERROR", m.start(), f"approved host {host} but script version is not pinned: {m.group(1)}", html)
        else:
            add("ERROR", m.start(), f"third-party script needs user approval: {m.group(1)}", html)
    for m in re.finditer(r"<link\b[^>]*\bhref\s*=\s*[\"'](https?:)?//([^\"'/]+)[^\"']*", html, re.I):
        if m.group(2) not in allow:
            add("ERROR", m.start(), f"third-party stylesheet/font needs user approval: {m.group(2)}", html)
    for m in re.finditer(r"@import[^;]+;|url\(\s*[\"']?https?://[^)]+\)", html, re.I):
        add("ERROR", m.start(), f"remote CSS resource: {m.group(0)[:80]}", html)
    for m in re.finditer(r"<(iframe|object|embed)\b[^>]*>", markup, re.I):
        hidden = re.search(r"display\s*:\s*none|width\s*=\s*[\"']?0|height\s*=\s*[\"']?0", m.group(0), re.I)
        add("ERROR" if hidden else "WARN", m.start(), f"<{m.group(1)}> present" + (" and hidden" if hidden else "; confirm it is approved"), html)
    for m in re.finditer(r"<form\b[^>]*\baction\s*=", markup, re.I):
        add("WARN", m.start(), "form with action: data leaves the page; confirm destination", html)
    for m in re.finditer(r"javascript:|data:text/html", markup, re.I):
        add("ERROR", m.start(), "javascript:/data:text/html URL", html)
    for m in re.finditer(r"<a\b[^>]*target\s*=\s*[\"']_blank[\"'][^>]*>", markup, re.I):
        if "noopener" not in m.group(0).lower():
            add("WARN", m.start(), 'target="_blank" without rel="noopener noreferrer"', html)

    # WordPress autop residue
    for m in re.finditer(r"<p>\s*<script", html, re.I):
        add("WARN", m.start(), "<script> wrapped in <p> (editor auto-paragraph damage)", html)
    blanks = [m.start() for m in re.finditer(r"\n[ \t\r]*\n", markup)]
    if blanks:
        add("WARN", blanks[0], f"{len(blanks)} blank line(s) inside markup; WordPress may insert <p>/<br> there", html)

    # root + CSS scoping
    root = a.root
    if not root:
        m = re.search(r"<[a-z][^>]*\bid\s*=\s*[\"']([^\"']+)", markup, re.I)
        root = m.group(1) if m else None
    if not root:
        add("ERROR", 0, "no root element id found; wrap everything in one <div id=\"emb-...\">")
    styles = re.findall(r"<style\b[^>]*>(.*?)</style>", html, re.S | re.I)
    for css in styles:
        for kind, prelude, body in css_rules(css):
            if kind == "other" and prelude.lower().startswith("@font-face"):
                add("WARN", html.find(prelude), "@font-face: confirm the font file is approved and licensed", html)
            if kind != "rule":
                continue
            pos = html.find(prelude[:40])
            for s in split_selectors(prelude):
                if root and not re.match(rf"#{re.escape(root)}(?![\w-])", s):
                    add("ERROR", pos, f"selector leaks into the host page: `{s[:60]}`", html)
            if re.search(r"(^|;)\s*height\s*:\s*\d+px", body) and re.search(r"overflow\s*:\s*hidden", body):
                add("WARN", pos, f"fixed height + overflow:hidden can clip text on small phones: `{prelude[:50]}`", html)
    for m in re.finditer(r"font-size\s*:\s*(\d+(?:\.\d+)?)px", html):
        if float(m.group(1)) < 12:
            add("WARN", m.start(), f"tiny font-size {m.group(1)}px (readers on phones); use >= 14px for body text", html)
    tiny = re.findall(r"text-\[(\d+(?:\.\d+)?)px\]", html)
    small = [t for t in tiny if float(t) < 12]
    if small:
        add("WARN", 0, f"{len(small)} Tailwind classes set text below 12px (e.g. text-[{small[0]}px])")

    # script risk patterns
    scripts = [(m.start(1), m.group(1)) for m in re.finditer(r"<script\b(?![^>]*\bsrc\b)[^>]*>(.*?)</script>", html, re.S | re.I)]
    hard = [
        (r"\beval\s*\(", "eval()"), (r"\bnew\s+Function\b", "new Function()"),
        (r"document\.write\s*\(", "document.write()"), (r"document\.cookie", "cookie access"),
        (r"sendBeacon|new\s+WebSocket|importScripts", "beacon/websocket/importScripts"),
        (r"\b(?:window\.)?top\.(?:location|document)|window\.top\b|document\.domain", "reaches the host page/top window"),
        (r"createElement\(\s*[\"']script[\"']\s*\)", "injects a <script> element (remote code)"),
        (r"\.src\s*=\s*[\"']https?:", "assigns a remote src"),
    ]
    soft = [
        (r"localStorage|sessionStorage|indexedDB", "browser storage: fine for harmless state only; disclose to user"),
        (r"\bfetch\s*\(|XMLHttpRequest", "network request: confirm destination is approved"),
        (r"window\.open|location\.(?:href|assign|replace)\s*=", "navigation from script"),
        (r"\b(?:atob|btoa)\s*\(|String\.fromCharCode", "encoding helpers (check for obfuscation)"),
        (r"\bon(?:click|load|error|mouse\w+|touch\w+)\s*=", "inline event handler (breaks under strict CSP; prefer addEventListener)"),
    ]
    for off, code in scripts:
        for pat, label in hard:
            for m in re.finditer(pat, code):
                add("ERROR", off + m.start(), f"script: {label}", html)
        for pat, label in soft:
            for m in re.finditer(pat, code):
                add("WARN", off + m.start(), f"script: {label}", html)
                break
        for m in re.finditer(r"(?:innerHTML|outerHTML|insertAdjacentHTML)[^\n;]*\$\{", code):
            add("WARN", off + m.start(), "script: HTML built with ${...}; make sure no user-typed text is interpolated", html)
            break
        if re.search(r"[A-Za-z0-9+/=]{200,}", code) or re.search(r"(?:\\x[0-9a-fA-F]{2}){10,}", code) or any(len(l) > 1500 for l in code.split("\n")):
            add("ERROR", off, "script: possible obfuscated/encoded payload (very long line or base64/hex blob)", html)
    for m in re.finditer(r"\bon(?:click|load|error|mouse\w+|touch\w+)\s*=", markup, re.I):
        add("WARN", m.start(), "inline event handler attribute (prefer addEventListener)", html)
        break

    findings.sort(key=lambda f: (f[0] != "ERROR", f[1]))
    seen = set()
    for level, line, msg in findings:
        key = (level, msg)
        if key in seen:
            continue
        seen.add(key)
        print(f"{level:5} line {line:>4}  {msg}" if line else f"{level:5}            {msg}")
    errs = sum(1 for f in findings if f[0] == "ERROR")
    print(f"\n{errs} error(s), {len(findings) - errs} warning(s) [root: #{root}]")
    sys.exit(1 if errs else 0)

if __name__ == "__main__":
    main()
