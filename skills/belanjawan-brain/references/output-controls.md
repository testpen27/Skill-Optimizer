# Output controls

How the results screen must look and read. This file is copied into `BRAIN-2026.md` by `scripts/export-brain-md.js`. Edit it here, then regenerate. `{{YEAR}}` is replaced with the brain's budget year on export.

Each control has a status:

- **locked**: the build must follow the rule exactly.
- **undecided**: the user hasn't chosen yet. Claude Code may design this part freely, but should keep to the rule if it has no better reason.

## Always required

These come from the user's earlier decisions and are not optional.

- Show the Malay text exactly as the engine returns it: titles, values, summaries, reasons, tier labels, advisories. Don't reword, shorten or translate it.
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

## Look and feel (undecided)

No style has been chosen. The builder may use a design skill or the house style of the skill it's working with, as long as every rule above is followed.

## Controls the user will decide

| # | Control | Status | Rule when locked |
|---|---|---|---|
| 1 | Results order | undecided | The STR + SARA card comes first. Then themes in the engine's order (`byTheme`), and within a theme layak, semak, mungkin, kesan (the engine already sorts them). Hide empty themes. Style `kesan` cards apart from benefits. |
| 2 | Card fields | undecided | Every card shows, in this order: tier label, title, value, summary, "Kenapa anda layak" (`reasons`), "Perlu disahkan" (`needsConfirm`, `mungkin` cards only), who, action, timing note, source line (`src`). |
| 3 | Fixed wording | undecided | Tier labels exactly as `B26Brain.TIERS`. The disclaimer is the last thing on the results screen. No extra marketing or summary copy written by the builder. |
| 4 | Summary line | undecided | Above the cards, one line with the number of cards and the STR + SARA total, plus counts per tier, built only from `counts` and `strSara`. |

To lock a control, change its status to `locked` (and edit its rule if needed). To add a control, add a row.
