# Output controls

How the results screen must look and read. This file is copied into `BRAIN-2026.md` by `scripts/export-brain-md.js`. Edit it here, then regenerate. `{{YEAR}}` is replaced with the brain's budget year on export.

Each control has a status:

- **locked**: the build must follow the rule exactly.
- **undecided**: the user hasn't chosen yet. Claude Code may design this part freely, but should keep to the rule if it has no better reason.

## Always required

These come from the user's earlier decisions and are not optional.

- Show the Malay text exactly as the engine returns it: titles, values, summaries, reasons, group headings, advisories. Don't reword, shorten or translate it.
- Always show the disclaimer advisory.
- Every question except age and region can be skipped. Show the skip option ("Tidak mahu menyatakan"), or a "Langkau" link that sends it.
- In a multi-select, an exclusive option ("Tiada yang berkaitan", "Tidak mahu menyatakan") clears the other selections.
- Build nothing from the "Not to be built" list.

## Front page (locked)

The page the reader sees first. The text below is exact; don't change, translate or restyle the wording (the casing is part of it).

```
KALKULATOR BELANJAWAN {{YEAR}}      <- heading (H)

KETAHUI MANFAAT ANDA!               <- tagline (T)

[ MULA ]                            <- button
```

- Only these three elements are on the front page: the heading, the tagline and the **MULA** button. Nothing else is added: no questions, no summary, no extra copy.
- **Clicking MULA opens the calculator in an in-page modal:** a dialog over the same page, with the page behind it dimmed. It is not a new browser window (`window.open`), because popup blockers and phones make that unreliable, and the embed has to stay one self-contained block.
- The modal contains the whole calculator: the question flow first, then the results screen. Nothing of the calculator shows on the front page itself.
- The modal has a visible close button labelled "Tutup" that returns to the front page. Standard modal behaviour applies: `role="dialog"` with `aria-modal="true"`, focus moves into the dialog on open and back to MULA on close, Esc closes it, and the page behind doesn't scroll while it's open.
- On a phone the modal fills the screen. Its content must fit and scroll inside it, with no clipped text and no horizontal scrolling.
- Colours, fonts, imagery and spacing of the front page and modal are not decided yet; the builder designs them (see "Look and feel" below).

## Results screen (locked)

Shown inside the modal after the last question. From top to bottom:

1. **STR + SARA panel.** The main result, on top, as one panel: `strSara.label`, STR, SARA (with the monthly amount) and the total. Add the range when `totalRange` is present, and the "jika berdaftar eKasih" total when `totalIfEkasih` is present. When the person is not eligible or it can't be worked out, show `strSara.reason` instead of amounts.
2. **The cards, in two groups.** Take them from `evaluate().groups` and keep its order:
   - first **"Berkemungkinan layak"**: cards the person clearly qualifies for;
   - then **"Mungkin layak"**: means-tested cards, then cards that depend on a skipped answer.

   Show each group's heading exactly as `group.label`. Hide a group with no cards. No theme categories anywhere.
3. **Advisories** below the cards, in the engine's order. The disclaimer is last.

**Grid.** Five cards per row on a wide screen, with as many rows as needed. All cards are on one scrolling screen; there are no pages. As the screen narrows, show fewer per row: one or two on a phone.

**Card face: the title only.** No amount, tier label, theme, icon or colour that marks a card as different. Cost changes for the person (tobacco, vape, alcohol, and similar) look exactly like every other card. No warning label of any kind, including the old "Perubahan yang menjejaskan anda".

**Details on hover.** Hovering over a card shows, in this order:

- the amount (`value`);
- the description (`summary`);
- the timing note (`timing`), when there is one;
- "Kenapa anda layak", followed by `reasons`;
- for cards with `tier` = `mungkin` only: "Perlu disahkan", followed by `needsConfirm`.

Nothing else is shown: not who is eligible (`who`), not what to do next (`action`), not the source, not the tier. On a phone or tablet, where there is no hover, a tap shows the same details and a second tap (or a tap elsewhere) hides them. Cards are focusable, and keyboard focus shows the details too.

## Look and feel (undecided)

No style has been chosen. The builder may use a design skill or the house style of the skill it's working with, as long as every rule above is followed.

## Still undecided

| # | Control | Status | Rule when locked |
|---|---|---|---|
| 1 | Summary line | undecided | Above the cards, one line with the number of cards and the STR + SARA total, built only from `counts`, `groups` and `strSara`. |
| 2 | Extra copy | undecided | No text written by the builder beyond what these controls and the engine provide (no intro paragraph, no marketing lines). |

To lock a control, change its status to `locked` (and edit its rule if needed). To add a control, add a row.
