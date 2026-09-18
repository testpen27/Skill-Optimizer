# Testing Apps Script Without a Live Environment

Apps Script has no local runtime and no unit-test framework of its own.
When you can't run against the user's real sheet — building/fixing
trigger logic, date/time math, or anything destructive — mock the small
slice of the `SpreadsheetApp` API surface the script actually uses, load
the *real* `.gs` file text into a Node.js `vm` context, and drive it with
plain `assert`-style checks. This tests the actual file the user will
paste in, not a reimplementation of its logic.

## Why this over just reading the code carefully

Reading code catches logic errors you already suspect. It doesn't catch:
a test fixture's own column-index typo (caught by an assertion failing
unexpectedly), a real API call the mock doesn't support yet (caught by
`TypeError: sheet.getMaxColumns is not a function` — which is itself
useful signal about what the real script needs), or a day-of-week
computation that's subtly wrong (caught by cross-checking against an
*independent* computation path in the test, not the same logic twice).

## Minimal harness skeleton

```javascript
const fs = require('fs');
const vm = require('vm');

class MockRange {
  constructor(sheet, row, col, numRows = 1, numCols = 1) {
    this.sheet = sheet; this.row = row; this.col = col;
    this.numRows = numRows; this.numCols = numCols;
  }
  getRow() { return this.row; }
  getColumn() { return this.col; }
  getNumRows() { return this.numRows; }
  getNumColumns() { return this.numCols; }
  getValue() { return this.sheet._cell(this.row, this.col).value; }
  setValue(v) { this.sheet._cell(this.row, this.col).value = v; }
  getValues() {
    const out = [];
    for (let r = 0; r < this.numRows; r++) {
      const row = [];
      for (let c = 0; c < this.numCols; c++) row.push(this.sheet._cell(this.row + r, this.col + c).value);
      out.push(row);
    }
    return out;
  }
  setValues(grid) {
    for (let r = 0; r < this.numRows; r++)
      for (let c = 0; c < this.numCols; c++) this.sheet._cell(this.row + r, this.col + c).value = grid[r][c];
  }
  getDisplayValues() { return this.getValues().map(row => row.map(v => v == null ? '' : String(v))); }
  clearContent() {
    for (let r = 0; r < this.numRows; r++)
      for (let c = 0; c < this.numCols; c++) { const cell = this.sheet._cell(this.row + r, this.col + c); cell.value = null; cell.formula = null; }
  }
  getDataValidation() { const c = this.sheet._cell(this.row, this.col); return c.isCheckbox ? { getCriteriaType: () => 'CHECKBOX' } : null; }
  getDataValidations() {
    const out = [];
    for (let r = 0; r < this.numRows; r++) {
      const row = [];
      for (let c = 0; c < this.numCols; c++) { const cell = this.sheet._cell(this.row + r, this.col + c); row.push(cell.isCheckbox ? { getCriteriaType: () => 'CHECKBOX' } : null); }
      out.push(row);
    }
    return out;
  }
  getFormula() { return this.sheet._cell(this.row, this.col).formula || ''; }
  setFormula(f) { this.sheet._cell(this.row, this.col).formula = f; }
  setFontColor(c) { this.sheet._cell(this.row, this.col).fontColor = c; }
  setFontSize(s) { for (let r=0;r<this.numRows;r++) for (let c=0;c<this.numCols;c++) this.sheet._cell(this.row+r,this.col+c).fontSize = s; return this; }
  setVerticalAlignment(a) { for (let r=0;r<this.numRows;r++) for (let c=0;c<this.numCols;c++) this.sheet._cell(this.row+r,this.col+c).vAlign = a; return this; }
  setHorizontalAlignment(a) { for (let r=0;r<this.numRows;r++) for (let c=0;c<this.numCols;c++) this.sheet._cell(this.row+r,this.col+c).hAlign = a; return this; }
}

class MockSheet {
  constructor(name, rows, cols, ss, sheetId) {
    this.name = name; this.ss = ss; this.sheetId = sheetId;
    this.rows = rows; this.cols = cols; this._grid = {}; this.hidden = false;
  }
  _cell(r, c) { const k = r + '_' + c; return this._grid[k] || (this._grid[k] = { value: null, isCheckbox: false }); }
  setHeader([r, c], value) { this._cell(r, c).value = value; }
  setCheckbox(r, c, value) { const cell = this._cell(r, c); cell.isCheckbox = true; cell.value = value; }
  getName() { return this.name; }
  setName(n) { if (this.ss?.sheets[this.name] === this) delete this.ss.sheets[this.name]; this.name = n; if (this.ss) this.ss.sheets[n] = this; }
  getParent() { return this.ss; }
  getSheetId() { return this.sheetId; }
  getLastColumn() { return this.cols; }
  getMaxColumns() { return this.cols; }
  getMaxRows() { return this.rows; }
  getRange(row, col, numRows = 1, numCols = 1) { return new MockRange(this, row, col, numRows, numCols); }
  getDataRange() { return new MockRange(this, 1, 1, this.rows, this.cols); }
  isSheetHidden() { return this.hidden; }
  hideSheet() { this.hidden = true; }
}

class MockSpreadsheet {
  constructor(id) { this.id = id; this.sheets = {}; this._active = null; }
  getId() { return this.id; }
  getSheetByName(n) { return this.sheets[n] || null; }
  getSheets() { return Object.values(this.sheets); }
  addSheet(s) { this.sheets[s.name] = s; if (!this._active) this._active = s; }
  getActiveSheet() { return this._active; }
  setActiveSheet(s) { this._active = s; }
  toast() {}
}

// --- wire up the sandbox, then load the REAL file ---
let ACTIVE_SS, ACTIVE_USER_EMAIL = '';
const cacheStore = {}, docPropsStore = {};
const sandbox = {
  console,
  SpreadsheetApp: {
    getActive: () => ACTIVE_SS,
    DataValidationCriteria: { CHECKBOX: 'CHECKBOX' },
    getUi: () => ({
      alert: () => sandbox.__nextAlertResponse || 'YES',
      ButtonSet: { YES_NO: 'YES_NO' }, Button: { YES: 'YES', NO: 'NO' },
      createMenu: () => ({ addItem(){return this;}, addSeparator(){return this;}, addToUi(){} })
    })
  },
  Session: { getActiveUser: () => ({ getEmail: () => ACTIVE_USER_EMAIL }) },
  CacheService: { getScriptCache: () => ({
    get: k => (k in cacheStore ? cacheStore[k] : null),
    put: (k, v) => { cacheStore[k] = v; }, remove: k => { delete cacheStore[k]; }
  })},
  PropertiesService: { getDocumentProperties: () => ({
    getProperty: k => (k in docPropsStore ? docPropsStore[k] : null),
    setProperty: (k, v) => { docPropsStore[k] = v; }, deleteProperty: k => { delete docPropsStore[k]; }
  })},
  Utilities: { formatDate: (date, tz, pattern) => {
    const parts = new Intl.DateTimeFormat('en-US', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(date);
    const m = {}; parts.forEach(p => m[p.type] = p.value);
    if (pattern === 'yyyy-MM-dd') return `${m.year}-${m.month}-${m.day}`;
    throw new Error('unsupported pattern "' + pattern + '" — add it deliberately, don\'t guess');
  }}
};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync('./onEdit.gs', 'utf8'), sandbox, { filename: 'onEdit.gs' });

// --- drive it ---
function makeEvent(sheet, row, col, numRows, numCols, oldValue) {
  const single = numRows === 1 && numCols === 1;
  const raw = single ? sheet.getRange(row, col).getValue() : undefined;
  // The real API stringifies, and omits both fields on multi-cell edits.
  // Modelling that is the point — a mock that hands back a real boolean
  // will pass tests for code that dies in production.
  const str = v => (v === null || v === undefined) ? undefined
    : (typeof v === 'boolean' ? String(v).toUpperCase() : String(v));
  return {
    range: sheet.getRange(row, col, numRows, numCols),
    source: { getActiveSheet: () => sheet },
    value: single ? str(raw) : undefined,
    oldValue: single ? str(oldValue) : undefined
  };
}
```

## Key techniques worth keeping

- **`Utilities.formatDate` throws on any pattern you haven't explicitly
  supported**, rather than silently returning `''`. If the real script
  ever adds a new pattern letter, the test suite fails loudly instead of
  quietly returning wrong dates — forcing you to add it *deliberately*.
- **Cross-check computed values against an independently-computed
  expectation** in the test (e.g. `Intl.DateTimeFormat` with the same
  timezone), not the same formula reused. Two different paths agreeing
  is real evidence; one path checked against itself is not.
- **Load the literal file text** (`fs.readFileSync` + `vm.runInContext`),
  never copy-paste the logic into the test file. You want to know the
  file that gets pasted into Apps Script actually works.
- **`sandbox.__nextAlertResponse`** lets a test simulate the user
  clicking Yes or No on a confirm dialog without any real UI.
- Add mock methods **as the real script needs them**, not preemptively —
  a `TypeError: X is not a function` from the mock is a legitimate,
  useful signal that you haven't modeled that API surface yet, not
  noise to suppress.
