---
name: g-app-script
description: Build and harden Google Apps Script automation for Google Sheets — custom menus, onEdit/time-driven triggers, dialogs, dropdowns, PropertiesService state, batch operations. Use whenever the user wants to automate a Google Sheet, add a menu/trigger/dropdown to a spreadsheet, schedule a Sheets workflow, or asks "how do I script this in Sheets" — even if they never say "Apps Script." Also use this whenever debugging a script that silently isn't running, isn't firing at the expected time, or isn't clearing/updating as expected, and whenever testing Apps Script code without a live Google Sheets environment available. Not for Gmail, Drive, Docs, Forms, or Calendar automation with no spreadsheet involved — those need Workspace-specific quotas and patterns this skill doesn't cover.
---

# g-app-script

Build Google Apps Script automation for Google Sheets. Scripts run
server-side on Google's infrastructure with a generous free tier. This skill
combines the general Apps Script playbook with hardening lessons learned from
shipping a real multi-trigger production script that users depended on daily —
the rules below exist because each one traces back to an actual bug. For
Gmail, Drive, Docs, Forms, or Calendar scripting with no spreadsheet
involved, the trigger and quota specifics here don't transfer — treat that
as a separate build.

## What You Produce

- Apps Script code pasted into Extensions > Apps Script
- Custom menus, dialogs, sidebars, dropdown validation
- Triggers: onEdit (simple), time-driven, form submit (installable)
- A way to test the logic before it ever touches the user's real sheet

## Workflow

1. **Understand the automation.** Ask what should happen and on what
   trigger (menu click, edit, schedule). If it's destructive (clears
   content, deletes rows, sends email), plan for a manual "run now" path
   with a confirm dialog *before* wiring it to an automatic trigger.
2. **Generate the script** using the structure template below.
3. **Test it** — see "Testing Without a Live Environment." Don't skip this
   for anything involving triggers or date/time logic; both fail in ways
   that are invisible until a specific moment in the future.
4. **Give install + first-run instructions** (below) — the OAuth consent
   step trips people up if you don't mention it.

## Script Structure Template

```javascript
/**
 * [Project Name] - [Brief Description]
 * INSTALL: Extensions > Apps Script > paste this > Save > Reload sheet
 */

// --- CONFIGURATION --- (constants at top, not buried in functions)
const SOME_SETTING = 'value';

// --- MAIN TRIGGER ---
function onOpen() {
  SpreadsheetApp.getUi().createMenu('My Menu')
    .addItem('Do Something', 'myFunction')
    .addToUi();
}

function onEdit(e) {
  if (!e || !e.range) return;
  // See "Wrap Every Handler Independently" below — don't put multiple
  // unrelated behaviors in one shared try/catch.
}
```

Install steps are always the same: Extensions > Apps Script, paste, Save,
reload the spreadsheet (onOpen only runs on page load). **First run**: each
user hits a Google OAuth consent screen. For unverified internal scripts
they must click **Advanced > Go to [Project Name] (unsafe) > Allow** —
warn users about this up front or they'll assume it's broken.

---

## Critical Rules

### Public vs Private Functions

Functions ending in `_` are **private** — they cannot be called from
client-side HTML via `google.script.run`. Fails silently, no error.

```javascript
function doWork_() { return 'done'; }  // dialog call fails silently
function doWork()  { return 'done'; }  // dialog can call this
```

This also means: if you use trailing-`_` as your own "internal helper"
naming convention (reasonable, and this skill does), double-check none of
those functions ever need to be invoked from `google.script.run` later.

### Batch Operations (70x performance difference)

Read/write in bulk, never cell-by-cell.

```javascript
// SLOW — one round trip per cell
for (let i = 1; i <= 100; i++) sheet.getRange(i, 1).getValue();
// FAST — one round trip total
const all = sheet.getRange(1, 1, 100, 1).getValues();
```

At small scale (a handful of rows, like a fixed "dateline" block) a
per-row loop of individual `getRange()` calls is fine — the 70x claim
matters at hundreds/thousands of rows. Don't over-optimize what's already
fast, but don't let a small-scale loop get copy-pasted into a large-scale
job without batching it first.

### V8 Runtime

V8 is the only runtime (Rhino was removed). Modern JS works: `const`,
arrow functions, template literals, destructuring, classes. **Not
available** — use the Apps Script alternative instead:

| Missing | Use instead |
|---|---|
| `setTimeout`/`setInterval` | `Utilities.sleep(ms)` (blocking) |
| `fetch` | `UrlFetchApp.fetch()` |
| `crypto` | `Utilities.computeDigest()` / `getUuid()` |

### Never Trust an Unverified Format Pattern

`Utilities.formatDate(date, tz, pattern)` takes Java SimpleDateFormat
pattern letters. Some are certain (`yyyy`, `MM`, `dd`) and some are easy
to half-remember wrong (`u` for ISO day-of-week is real, but confirm it
before depending on it). **An uncaught exception on the first line of a
scheduled function silently aborts everything after it** — including the
actual clearing/writing logic — which looks identical to "the trigger
just isn't running." If you're not fully certain a pattern is supported,
derive it a safer way instead:

```javascript
// Safer: only "yyyy-MM-dd" (totally unambiguous) + native getUTCDay()
const dateStr = Utilities.formatDate(now, tz, "yyyy-MM-dd");
const midnight = new Date(dateStr + "T00:00:00Z");
const isoDayIndex = (midnight.getUTCDay() + 6) % 7; // 0=Mon..6=Sun
```

### Detect Structure Dynamically, Don't Hardcode Row/Column Numbers

Real sheets get restructured by real users — a column gets inserted, a
section grows, a header moves. A hardcoded "entries start at row 8" will
go stale the first time someone edits the sheet's layout, and it'll fail
silently (wrong rows processed, or none). Prefer detecting structure from
content that's actually there:

```javascript
// Find a section by its own marker text, not a row number you memorized
function findSectionBoundary_(sheet, markerText) {
  const values = sheet.getRange(1, 1, sheet.getMaxRows(), sheet.getMaxColumns()).getValues();
  for (let i = 0; i < values.length; i++) {
    if (values[i].some(v => typeof v === "string" && v.toLowerCase().includes(markerText))) return i;
  }
  return null; // caller decides the fallback
}
```

Cache the result (`CacheService`, a few hours) since scanning the whole
sheet on every edit is wasteful — but give the user a manual "rebuild
cache" menu item, because a cached wrong answer is worse than a slow
right one.

### Track Tabs by Stable ID, Never by Name

If anything renames a sheet tab (including your own script), any state
keyed by `sheet.getName()` — `PropertiesService` keys, a lookup table —
silently orphans itself the moment the name changes. Use
`sheet.getSheetId()` (a numeric ID that survives renames) for anything
that needs to persist across edits:

```javascript
props.setProperty("lastEdit_" + sheet.getSheetId(), String(Date.now()));
```

Sheet *names* are fine for one-shot decisions made fresh each time
(pattern-matching which tabs to include in a job), just never for a
durable key.

### Wrap Every Handler Independently

If several unrelated behaviors share one `try/catch` inside `onEdit`, one
failing silently blocks everything listed after it — including something
as important as recording that an edit happened at all.

```javascript
function onEdit(e) {
  if (!e || !e.range) return;
  safeRun_(e, () => handleThingOne(e));
  safeRun_(e, () => handleThingTwo(e));   // still runs even if ThingOne throws
  safeRun_(e, () => recordLastEdit(e));   // ESPECIALLY this one
}
function safeRun_(e, fn) {
  try { fn(); } catch (err) { logError_(e, err); }
}
```

The same applies to time-driven trigger entry points — they have *no*
wrapping by default. An uncaught error there fails with zero visible
trace anywhere except the Apps Script Executions log, which most users
never think to check. Wrap each one and log failures somewhere visible
(see "Log Every Automated Action" below).

### Trigger-Enable Guards Must Check Each Handler Independently

If a feature installs more than one trigger, don't guard installation
with "if *any* of them exist, skip all of them" — that blocks a later
code update from ever backfilling a trigger that didn't exist yet when
the feature was first enabled.

```javascript
// WRONG: an old single-trigger install blocks the new one forever
if (triggers.some(t => t.getHandlerFunction() === "jobA" || t.getHandlerFunction() === "jobB")) return;

// RIGHT: install whichever is actually missing
if (!hasJobA) ScriptApp.newTrigger("jobA")...create();
if (!hasJobB) ScriptApp.newTrigger("jobB")...create();
```

### Flush Before Returning

Call `SpreadsheetApp.flush()` before returning from a function that
modifies the sheet and is called synchronously from an HTML dialog —
without it, the dialog may show "Done" before the change is visible.
Not needed for ordinary menu-triggered functions that just run to
completion; Apps Script flushes automatically at the end of those.

### Simple vs Installable Triggers

| | Simple (`onEdit`) | Installable |
|---|---|---|
| Auth required | No | Yes |
| Send email / fetch URL | No | Yes |
| Open dialogs from the trigger | No | Yes |
| Runs as | Active user | Trigger creator |

Use simple `onEdit` for lightweight reactions. You need an installable
trigger the moment the job does any of these:

- sends email, or calls `UrlFetchApp` / any external API
- touches a file other than the one the script is bound to
- runs on a schedule, on form submit, or on `onChange`
- opens a dialog, sidebar, or prompt from the trigger itself
- takes longer than 30 seconds (simple triggers are capped there)

A simple trigger that tries any of these doesn't error — it just does
nothing, because it never had authorization to begin with. The fix is to
rename the function (a function literally named `onEdit` is *always*
treated as simple) and install it with `ScriptApp.newTrigger()`.

Two tells worth knowing when you're diagnosing rather than building:
simple triggers never appear in `getProjectTriggers()`, so an absent
`onEdit` there is expected and not evidence of anything; and simple
triggers don't fire on programmatic changes, so a value written by
another script or by a formula recalculating won't wake them.

### The Event Object Lies About Types

`e.value` is a **string**, always, regardless of what the cell holds. A
ticked checkbox arrives as `"TRUE"`, the number 42 arrives as `"42"`.
This is the single most common source of silently-dead handlers, because
the natural-looking guard is wrong in a way that no error surfaces:

```javascript
if (e.value !== true) return;              // never passes — bails every time
if (e.range.getValue() !== true) return;   // real boolean from the cell
```

`e.value` is also **absent entirely on multi-cell edits** and when a cell
is cleared, so any handler that reads it without first confirming a
single-cell edit is reading `undefined` in normal use.

The rule that avoids all of this: use `e.value` only for cheap string
comparisons and early exits, and read `e.range.getValue()` whenever the
type matters. `e.range` is the one field that behaves the way you'd
expect, which is why the guards throughout this skill are built on it.

Full field-by-field behaviour for `onEdit`, `onChange`, and form-submit
events — including which fields exist under which trigger type — is in
`references/event-objects.md`. Read it before writing a handler that
branches on anything other than position.

---

### A Trigger Belongs to Whoever Installed It

This applies to installable triggers only — a simple `onEdit` or
`onOpen` has no owner and no stored authorization, so none of the
failures below can happen to one. Establish which kind you're looking at
before spending time here.

Installable triggers aren't attached to the spreadsheet — they're
attached to the *account that created them*, running under that person's
authorization. This is the usual explanation for "it worked for months,
then quietly stopped," and it produces symptoms that look nothing like an
ownership problem:

- **The owner lost access.** They left the organization, their account
  was suspended, or someone tightened sharing on the file. The trigger
  keeps its schedule and fails every time. Nobody else sees anything.
- **A code update added a new API.** A script that only touched
  `SpreadsheetApp` and now calls `MailApp` or `UrlFetchApp` needs a
  broader OAuth scope than the trigger was authorized for. The trigger
  fails with an authorization error until the owner opens the editor,
  runs the function manually once, and re-consents. Editing the code does
  not re-prompt on its own — this is the single most common way a working
  automation dies immediately after a "small" feature addition.
- **Google gives up on it.** After repeated failures the trigger gets
  disabled outright, and the failure notification emails go only to the
  owner — often an inbox nobody reads anymore.

Two things follow for diagnosis, and both matter because they make a
broken setup look like an empty one:

```javascript
// Returns ONLY triggers created by whoever is running this right now.
// An empty result means "you have none," NOT "the script has none."
ScriptApp.getProjectTriggers().forEach(t =>
  Logger.log(t.getHandlerFunction() + " / " + t.getEventType()));
```

The Executions tab is scoped the same way — you see your own runs, not a
colleague's. So when someone reports a dead trigger, establish *who
installed it* before concluding it was never installed, and have that
person check their own Executions view.

For anything a team depends on, install triggers from a shared or service
account rather than an individual's, and record the installing account in
the `_LOG` sheet so the answer to "whose trigger is this?" survives that
person's departure.

---

## Common Patterns

**Toast / alert / confirm:**
```javascript
SpreadsheetApp.getActive().toast('Done!', 'Title', 5); // 5s, or -1 = until dismissed
const ui = SpreadsheetApp.getUi();
const resp = ui.alert('Delete this?', 'Cannot be undone.', ui.ButtonSet.YES_NO);
if (resp !== ui.Button.YES) return;
```

**Searchable dropdown from a range** (native "type to filter" once the
list is long enough — no custom UI needed):
```javascript
const rule = SpreadsheetApp.newDataValidation()
  .requireValueInRange(ss.getSheetByName('Lookups').getRange('A2:A100'))
  .setAllowInvalid(true).build();
sheet.getRange('B2:B50').setDataValidation(rule);
```

**PropertiesService** — three scopes, 500 KB limit each:
`getScriptProperties()` (shared across all users), `getUserProperties()`
(per user), `getDocumentProperties()` (per spreadsheet — usually the
right one for per-sheet state).

**Installable time-driven trigger, specific hour + timezone:**
```javascript
ScriptApp.newTrigger('dailyJob').timeBased()
  .atHour(8).everyDays(1).inTimezone('Asia/Kuala_Lumpur').create();
```
Fires *sometime within* that hour, not to the exact minute — that's a
platform limit, not a bug in your code.

**Manual "force run now" beside every automated/destructive job** — lets
the user see exactly what it does before trusting the schedule:
```javascript
function forceRunNow() {
  const ui = SpreadsheetApp.getUi();
  const resp = ui.alert('Run now?', 'Describe exactly what will change. Cannot be undone.', ui.ButtonSet.YES_NO);
  if (resp !== ui.Button.YES) return;
  doTheActualWork();
  SpreadsheetApp.getActive().toast('Done.');
}
```

**Log every automated action to a visible sheet** — Apps Script's own
Executions log isn't something most users know exists. A hidden `_LOG`
sheet the script writes to (timestamp, what happened, why) turns "is
this even working?" into something answerable in ten seconds:
```javascript
function logAction_(sheetName, reason) {
  const ss = SpreadsheetApp.getActive();
  let log = ss.getSheetByName('_LOG');
  if (!log) { log = ss.insertSheet('_LOG'); log.appendRow(['Timestamp','Sheet','Reason']); log.hideSheet(); }
  log.appendRow([new Date(), sheetName, reason]);
}
```
Log both success *and* failure paths — an empty log after the expected
run time is itself a useful signal.

---

## Testing Without a Live Environment

You often can't run Apps Script directly against the user's real sheet.
See `references/testing-with-mocks.md` for a reusable Node.js mock of the
`SpreadsheetApp`/`Session`/`PropertiesService`/`ScriptApp`/`Utilities`
surface, run against the *actual* `.gs` file text via `vm.Script` — not a
reimplementation, the real file. This caught real bugs before deployment
on the project this skill was built from, including a column-index typo
in test setup and a missing mock method that pointed at a real API
mismatch. Reach for it any time you're asked to build or fix
trigger-based or date/time logic — those are exactly the categories that
"looks right, fails in three weeks" without it.

---

## Quotas and Limits

| Resource | Free | Workspace |
|---|---|---|
| Script runtime | 6 min/execution | 6 min/execution |
| Time-driven trigger runtime | 30 min | 30 min |
| Triggers total daily runtime | 90 min | 6 hours |
| Triggers total | 20/user/script | 20/user/script |
| Properties storage | 500 KB | 500 KB |
| Simultaneous executions | 30 | 30 |

## Error Prevention

| Mistake | Fix |
|---|---|
| Dialog can't call a function | Remove trailing `_` |
| Large-data script is slow | Batch with `getValues()`/`setValues()` |
| Dialog shows "Done" too early | `SpreadsheetApp.flush()` before return |
| `onEdit` can't send email | Use an installable trigger |
| Trigger "just isn't firing" | Check for an uncaught error on an unverified date pattern first |
| A previously-working feature silently stopped after a code update | Check whether a trigger-enable guard is blocking a newly-added trigger (see above) |
| Worked for months, then stopped, nothing changed | Check whether the installing account still has file access, or was disabled/offboarded |
| Trigger died right after you added email or an API call | New OAuth scope — owner must run the function manually once and re-consent |
| `getProjectTriggers()` returns nothing but the job clearly ran before | You're not the account that installed it; triggers and Executions are per-user. Simple triggers are never listed there at all |
| Checkbox handler never runs, no error anywhere | `e.value` is the string `"TRUE"` — compare `e.range.getValue() === true` |
| Handler works on single edits, breaks on paste or fill-down | `e.value` and `e.oldValue` are `undefined` on multi-cell edits |
| `onChange` handler throws on `e.range` | `onChange` has no `e.range` — use `getActiveRange()` |
| Form value renders with brackets | `e.namedValues[...]` is an array; take `[0]` |
| `onEdit` doesn't fire when another script or a formula writes the cell | Simple triggers only respond to human edits — use `onChange` (installable) |
| Auth popup doesn't appear | User must click Advanced > Go to (unsafe) > Allow |
| Script exceeds 6 min | Chunk the work, drive it with a time-driven trigger |

## Deployment Checklist

- [ ] Every `onEdit` handler wrapped independently, not sharing one `try/catch`
- [ ] Every time-driven trigger entry point wrapped in its own `try/catch`, logging failures somewhere visible
- [ ] Any date/time pattern letter you weren't 100% sure about, verified or replaced
- [ ] Structural assumptions (row/column boundaries) detected from content, not hardcoded, wherever the layout could plausibly change
- [ ] Anything persisted across edits is keyed by sheet ID, not name
- [ ] Trigger-enable functions check each handler independently
- [ ] Triggers for anything a team depends on installed from a shared/service account, with the installing account recorded somewhere durable
- [ ] Every destructive/automated action has a manual "run now" + confirm dialog, tested before the schedule is trusted
- [ ] Configuration constants at the top, no magic numbers buried in functions
- [ ] Tested against a mock harness (see above) and/or a copy of the real sheet
- [ ] Considered multi-user behavior — different active sheet, different permissions, `Session.getActiveUser()` unreliable for accounts outside the owner's domain

## Debugging

- **Logger.log() / console.log()** — View > Execution Log in the editor
- **Executions tab** (script.google.com > My Projects > Executions) — the *only* way to see a time-driven trigger's actual run history and errors; there's no API to query this from inside a script. Scoped to the signed-in account, so an empty history may just mean the trigger belongs to someone else
- **Run manually** — select the function in the editor dropdown, click Run
- Always test on a copy of the real sheet before trusting a trigger with it
