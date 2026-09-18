# Event Object Reference

What each trigger actually hands your function. The recurring theme:
values arrive as strings, several fields vanish depending on how the edit
was made, and nothing errors when you read one that isn't there.

---

## `onEdit(e)` — simple and installable

| Field | Type | Behaviour |
|---|---|---|
| `e.range` | Range | Always present. The only fully reliable field |
| `e.value` | String | **Single-cell edits only.** `"TRUE"` / `"FALSE"` for checkboxes, `"42"` for numbers. `undefined` on multi-cell edits and when a cell is cleared |
| `e.oldValue` | String | Single-cell edits only. `undefined` if the cell was previously empty — indistinguishable from "not a single-cell edit" |
| `e.source` | Spreadsheet | The containing file |
| `e.user` | User | May be empty depending on the editor's permissions. Never rely on it for access control |
| `e.authMode` | AuthMode | `NONE` for simple triggers, `FULL` for installable |
| `e.triggerUid` | String | Installable only. Its presence is a reliable way to tell the two apart at runtime |

**Consequences worth internalising:**

- `e.value !== true` never passes for a checkbox. Use
  `e.range.getValue() === true`.
- Clearing a cell and editing a range both produce `undefined` for
  `e.value`, so guard on `e.range.getNumRows() === 1 &&
  e.range.getNumColumns() === 1` *before* reading it, not after.
- `e.oldValue === undefined` does not mean "unchanged."
- Dates come through as locale-formatted strings, not Date objects. Read
  `e.range.getValue()` for a real Date.
- Programmatic writes (`setValue`, formula recalculation, another
  script) **do not fire `onEdit` at all** — no event, not an empty one.
  This is also why writing from inside a handler can't cause a loop.

---

## `onChange(e)` — installable only

Fires for structural changes that `onEdit` ignores. There is **no
`e.range`** — this is the field people reach for first and it isn't
there.

| Field | Type | Behaviour |
|---|---|---|
| `e.changeType` | String | `EDIT`, `INSERT_ROW`, `REMOVE_ROW`, `INSERT_COLUMN`, `REMOVE_COLUMN`, `INSERT_GRID`, `REMOVE_GRID`, `FORMAT`, `OTHER` |
| `e.source` | Spreadsheet | The containing file |
| `e.user` | User | Same caveats as `onEdit` |

Use `SpreadsheetApp.getActiveSheet()` / `getActiveRange()` to find out
where it happened, and accept that this is approximate — by the time the
handler runs, the selection may have moved.

`REMOVE_ROW` fires *after* the row is gone, so anything you needed from
it has to have been captured earlier.

---

## `onFormSubmit(e)` — installable only

Two shapes, depending on whether the trigger is bound to the form or to
the destination spreadsheet. They are not interchangeable.

**Spreadsheet-bound** (the usual case):

| Field | Type | Behaviour |
|---|---|---|
| `e.range` | Range | The newly appended row |
| `e.values` | Array | Answers in column order, index 0 is the timestamp |
| `e.namedValues` | Object | Question title → **array of answers**, even for single-answer questions |

`e.namedValues['Email']` is `['a@b.com']`, not `'a@b.com'`. Forgetting
the `[0]` produces a string like `"a@b.com"` with brackets when
concatenated, which looks like a formatting bug rather than a type bug.

Question titles are the keys, so renaming a question in the form breaks
every handler referencing it, silently. Prefer `e.values` with named
column index constants if the form is likely to be edited.

**Form-bound:** `e.response` is a `FormResponse` object instead; there is
no `e.values` or `e.namedValues`. Use
`e.response.getItemResponses()`.

---

## Testing implications

The mock harness in `testing-with-mocks.md` builds events via
`makeEvent`. Keep it faithful to the above — in particular, have it
stringify `value` and `oldValue`. A harness that hands your code a real
boolean will happily pass a test for code that breaks in production,
which is worse than having no test.
