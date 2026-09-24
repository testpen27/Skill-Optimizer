# House look and how the earlier embed reached the page

Source: the user's own file DERMA_DARAH.HTML (World Blood Donor Day slide deck). Use it as the pointer for new embeds: same family, fewer problems.

## Measured article width

Desktop article column, confirmed 2026-09-21 across three separate readings:

1. **810.674px** — first reading, 100% zoom, likely the whole article-body container.
2. **642.664px** — a decoy: DevTools was docked to the side of the window, which shrank the available page width during that reading. Not a real layout value; discard readings taken with docked DevTools.
3. **823.984 × 432.594px** — DevTools undocked, this time measuring the featured `<img>` itself. Its ratio (823.984 ÷ 432.594 = 1.905) exactly matches the source file's own ratio (1200 ÷ 630 = 1.905), proving the browser scaled the 1200px-wide file down to fit an ~824px container rather than rendering it at full size. This is the most trustworthy reading, since it's cross-checked against a known quantity (the file's own dimensions).

Readings 1 and 3 agree within 13px (810.674 vs 823.984) — well inside the noise you'd expect from scrollbar width or minor window-size differences between sessions. **Working number: ~820px.**

**1200px was never actually observed rendering on the page.** It only ever appears as: the uploaded image file's own dimensions, the `sizes` attribute's resolution-selection hint, and the `wp-caption` figure's inline `style="width:1200px"` (which WordPress copies from the source file at upload time, not from live layout). The image's own class is `alignnone` (constrained to the text column), not `alignwide`/`alignfull` (which would break out to the full 1200px container) — consistent with everything above.

The user plans to widen the article's text column to make use of the full 1200px later. Until then, build fluid (`width:100%; max-width:1200px`) so the embed already fills whatever the column is, and preview both the current text width and the 1200px target so the user can compare (`scripts/make_preview.py ... --widths 820:"Artikel sekarang" 1200:"Artikel akan datang"`).

## Look
- **Frame:** `width:100%; max-width:1200px`, centred. Cream `#FFFDF7` background with a pink dot pattern (`radial-gradient(#FFC4D0 1.5px, transparent 1.5px)`, 30px grid), 4px solid `#3D3033` border, radius 1.5rem (1rem on phones), shadow `0 10px 25px rgba(61,48,51,.15)`, margin 2rem auto (1rem on phones), `touch-action: pan-y`.
- **Card ("sticker"):** white, 4px `#3D3033` border, radius 1.5rem, hard shadow `6px 6px 0 rgba(61,48,51,.15)`, max-width 1050px, centred.
- **Buttons ("bouncy"):** 3px dark border, `0 4px 0` dark shadow; pressed state moves down 4px and drops the shadow.
- **Palette:** cream `#FFFDF7`, pink `#FF6B8B`, pink-light `#FFE3E8`, red `#DC2626`, red-light `#FEE2E2`, blue `#74C2F2`, blue-light `#E0F4FF`, yellow `#FFD56B`, green `#77D9A5`, green-light `#D1F2DF`, dark text `#3D3033`.
- **Extras seen:** a pill badge top-left with the event and date, drifting decorative particles (keep them `pointer-events:none` and off under `prefers-reduced-motion`), prev/next buttons plus pagination dots plus swipe.
- **Slide types seen:** hero, info, status, compatibility matrix, eligibility checklist, mini-game.
- **Type:** the file names Fredoka (headings) and Quicksand (body) but never loads them. Use the system stack unless the user approves Google Fonts through the gate.

## Contrast (computed against WCAG AA, 4.5:1 for normal text)
Fails: white text on pink 2.72, pink text on cream 2.67. Passes: dark on pink 4.63, white on red 4.83, red on cream 4.75, dark on yellow 8.98, dark on blue 6.44, dark on green 7.34, dark on cream 12.37. So use pink for fills, borders and decoration with dark text on top, and red for primary buttons with white text.

## How the earlier embed reached the page (lessons)
- The CMS accepts pasted raw HTML with inline `<style>` and `<script>`, so no build step is needed.
- The editor wrapped every `<script>` in `<p>` and appended `<hr />`. It still ran, but keep markup free of blank lines so it stays clean.
- The `important: '#app-wrapper'` Tailwind trick was there to beat theme CSS. ID-prefixed plain CSS does the same job without the Tailwind CDN.
- Generic names (`#slider-track`, `.slide-item`, `.sticker-card`, `#main-container`) would collide if two embeds sit on one page. Prefix everything with the embed's slug and look elements up from the root.
- Fixed 600/550px height with hidden overflow and 8-9px text will clip on small phones.

## Slides without a fixed height
Stack the slides in one grid cell so the stage is as tall as the tallest slide:
```css
#emb-x .track { display: grid; }
#emb-x .slide { grid-area: 1 / 1; visibility: hidden; }
#emb-x .slide[data-on] { visibility: visible; }
```
Toggle `data-on` from script. `visibility:hidden` also takes inactive slides out of the tab order and away from screen readers.
