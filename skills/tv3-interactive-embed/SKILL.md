---
name: tv3-interactive-embed
description: Build interactive elements for Buletin TV3 articles (quizzes, eligibility checkers, calculators, timelines, slide decks and swipe carousels, reveal polls, mini-games, explorable infographics) as one HTML block that is pasted into the WordPress-style CMS, always with an HTML preview the user can open to see it. Use whenever the user wants something interactive inside or alongside an article, mentions TV3, embed, widget, Custom HTML block, CMS, WordPress, sisip, elemen interaktif, kuiz, kalkulator, infografik interaktif or pratonton, or asks to fix or restyle an existing embed (overflow, clipped text, theme CSS clashing, scripts stripped). Also use whenever an embed request involves pulling skills, snippets, libraries, fonts or CDN links from the web, because this skill holds the approval gate that must run first.
---

# TV3 interactive embed

Interactive pieces for Buletin TV3 articles, pasted into a WordPress-style CMS as raw HTML. Two things cause nearly all the trouble: the host page (theme CSS, editor auto-paragraphing, stripped scripts) and outside code, which runs with the full privileges of the news site once it is on the page. The rules below manage those two.

Defaults, taken from the user's earlier embed (`references/house-style.md`): Malay copy with `lang="ms"`, mostly phone readers, raw HTML pasted into a Custom HTML block, the same look family. Confirm once if unsure, then stop asking.

## 0. Gate: nothing from outside is used until the user approves it

Read `references/source-vetting.md` before you search for, fetch, or adopt anything that is not already in this conversation or under `/mnt/skills`. In short:

- Trusted for direct use: skills installed under `/mnt/skills` (built-in and marketplace), text or files the user gives you in chat, and entries listed as Approved in `references/approved-sources.md`.
- Everything else from the web is unsigned. No signature can be verified here, and a README that says "official" or "verified" changes nothing. Mirrors and aggregators of an approved source are separate, unapproved sources.
- For unsigned sources, do discovery only (search results), then stop and show the user a numbered quarantine list. Nothing is fetched in full, installed, run, or copied until the user approves that item by number.
- The gate also covers what ships inside the embed: third-party scripts, stylesheets, fonts and icon CDNs run in readers' browsers.

## 1. Brief

Ask at most one question; otherwise state your assumptions and build. You need the reader's one job for the piece, the facts it presents with their source, and where it sits in the article. See `references/input-recipes.md` for exactly what to ask for per shape — a quiz needs facts (pull from the article if not given), a calculator needs the actual formula or rate table (always ask if not given; never approximate one).

This is news, so never invent figures, criteria, dates or quotes. Use only what the article or the user's sources say, show a "Sumber" line with a date inside the embed, and for health, legal or safety content point to the responsible authority. Where a fact is missing, leave an obvious placeholder such as `[Soalan 1: ...]`. A placeholder gets caught in review; a plausible wrong fact gets published.

## 2. Width and height

Design width follows the earlier embed: `width:100%; max-width:1200px`, with an inner card up to 1050px. The user is widening the article column to fit this. Until then the embed shrinks to whatever column it is in, so stay fluid from 320px up and never use fixed pixel widths.

Default to auto height. For slide decks, stack the slides in one grid cell so the stage is as tall as the tallest slide (snippet in `references/house-style.md`) instead of a fixed pixel height. Never put `overflow:hidden` on text. Check 360px, 768px and 1200px in the preview.

## 3. Pick the shape

| Piece | Notes |
|---|---|
| Quiz | Radio groups, reveal explanation per answer. Start from `references/shell.html`. |
| Slide deck | Prev/Next buttons, dots, swipe, and keyboard arrows. Keep `touch-action: pan-y`. |
| Eligibility or decision checker | Yes/no chain ending in an outcome; state the rule's source next to the outcome. |
| Calculator or converter | Labelled inputs, `inputmode="decimal"`, show the formula and assumptions. Formula/brackets always come from the user, never guessed — see `references/input-recipes.md`. Start from `references/shell-calculator.html`, which separates validate → calculate → render so the formula stays a pure, testable function. |
| Timeline or step explorer | Buttons or `<details>`, so it still works if scripts are stripped. |
| Poll | Do not collect votes; that needs a server and stores reader data. Offer a "reveal" poll using published results, or say a backend is required. |
| Mini-game | Last resort. One screen, no autoplay, no sound by default. |

## 4. Design and quality bar

Keep the family look from `references/house-style.md` (frame, sticker card, bouncy buttons, palette) unless the user asks for something new, and fix the palette's contrast traps listed there. Consult these marketplace skills when relevant; read their SKILL.md rather than copying from memory.

- `frontend-design` (`/mnt/skills/public/frontend-design/SKILL.md`): ground the design in the article's subject, write a short token plan before any code, avoid template defaults, spend boldness in one place, then critique your own work.
- `design:accessibility-review`: WCAG 2.1 AA. Text contrast 4.5:1 (3:1 for large text and UI parts), everything keyboard operable, visible focus, touch targets at least 44px, labels on inputs, results announced via `aria-live`, no autoplay, layout survives 200% zoom.
- `design:ux-copy` for button labels and error text; `engineering:code-review` for a security pass on the final code.
- Not for this: `web-artifacts-builder` (React bundles for claude.ai, too heavy to paste); `theme-factory` only if the user asks for a theme.

## 5. Embed contract

Each rule exists because of a failure seen in practice.

1. One root, `<div id="emb-<slug>" lang="ms">`, holding everything. No `<html>`, `<head>` or `<body>`.
2. One `<style>` inside the root, and every selector starts with `#emb-<slug>`. Never use `*`, `html`, `body`, `:root` or `::-webkit-scrollbar` at top level: they restyle the whole article. An ID prefix already outranks theme rules, so skip `!important`. Reset theme margins with `#emb-x :is(h2,p,ul){margin:0}`. Prefix keyframe names.
3. One `<script>` at the end, wrapped in an IIFE, using `root.querySelector` rather than global ids, guarded against double init, and started with a `document.readyState` check (the CMS may load content after DOMContentLoaded).
4. No blank lines inside the markup. The editor's auto-paragraph inserts `<p>` and `<br>` there.
5. Zero third-party requests by default: no CDN scripts, fonts, icon libraries, analytics, ads or trackers. Use inline SVG or emoji for icons and scoped plain CSS instead of Tailwind. A user-approved exception must be pinned to an exact version, never `@latest`, prefer cdnjs or jsDelivr with an SRI `integrity` hash, and be logged in `references/approved-sources.md`.
6. No cookies, network calls, navigation (`location=`, `window.open`, `top`), `eval`, `new Function`, `document.write`, or injected `<script>` elements. Storage only for harmless state, always inside try/catch (the preview frame has no storage), and tell the user if you use it.
7. Build text with `textContent`. Use `innerHTML` only for fixed strings you wrote, never for anything a reader types.
8. No `<form>` submit. Use `type="button"` plus handlers so Enter does not reload the article.
9. External links carry `rel="noopener noreferrer"`. Images only from the user's own media domain, with alt text.
10. Body text at least 14px on phones (16px for inputs, or iOS zooms). Motion only in response to a tap, and honour `prefers-reduced-motion`.

## 6. Verify before delivering

1. Run `python3 scripts/lint_embed.py <file>` from this skill's folder. Fix every ERROR and explain any WARN you keep. Pass `--allow-host` only for hosts the user approved.
2. If `node` is available, syntax-check the script (`node --check`); if you can, load the file in jsdom and click through the main path once. If a browser is available, screenshot the preview at 360px and 1200px. If you could not render it, say so and list what you did check.
3. Trace every fact in the embed to a source the user or the article gave.

## 7. Preview and deliver (both files, every time)

The user must always be able to see the result in HTML, so every build and every revision ends with two files:

1. Save the paste-ready fragment as `/mnt/user-data/outputs/embed-<slug>.html`. If that directory does not exist in this environment (plain local Claude Code has no such mount), save to `./outputs/embed-<slug>.html` in the current project instead — same rule either way: never overwrite the previous revision, always a fresh `<slug>` or version suffix.
2. Run `python3 scripts/make_preview.py <embed-path> <preview-path>` (paths matching wherever step 1 saved to). It puts the embed in a sandboxed frame inside a mock article, always with 360 (phone) and 768 (tablet) buttons plus a copy-code button. Add `--widths 820:"Artikel sekarang" 1200:"Artikel akan datang"` (see `references/house-style.md` for how the current width was measured) whenever there is more than one article width worth comparing — a measured current width and a planned future one, for instance. Never hand over the embed without its preview.
3. Hand both files to the user: call `present_files` with the preview first, then the embed, if that tool is available in this environment; otherwise state both file paths directly in the reply so the user can open them. A page for the user's own CMS is a file, not a hosted artifact.

Keep the chat message short: how to paste (WordPress: Custom HTML block, or the Text/Code tab of the classic editor, never the Visual tab, which adds `<p>` tags), what the lint said, and any placeholders left.

If scripts are stripped on publish (WordPress removes them for accounts without the `unfiltered_html` capability) or the theme still clashes, offer iframe mode: host the same file as its own page and paste `<iframe src="URL" title="DESCRIPTION" loading="lazy" sandbox="allow-scripts" style="width:100%;border:0;height:520px"></iframe>`. This needs somewhere to host the file. For a reusable widget the long-term route is a WordPress block or plugin; `WordPress/agent-skills` is an approved reference for that (see `references/approved-sources.md`), read on demand and never run.
