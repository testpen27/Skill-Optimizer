#!/usr/bin/env python3
"""Build the Literature Review Matrix (LRM) as an Excel sheet from lrm.json.

    python3 build_lrm.py lrm.json --out Matrix.xlsx [--check]

--out is a workbook. If it exists the "Summary" and "LRM" sheets are replaced
and every other sheet (synthesis, concept ...) is kept; otherwise it is created.

Sheet "LRM", columns left to right: Code | Type | Authors | Title |
Introduction | Methodology | Theory | Results | Discussion | Quartile | Access.
Rows are sorted A-Z by the first author's family name and coded P01, P02 ...
in that order (add a paper and the codes renumber). The header row is filtered
and frozen so the matrix can be sorted and filtered in Excel.

lrm.json:
{
  "title": "Research title", "field": "Education", "years": "2021-2026",
  "papers": [
    {"id": "tan2024", "authors": ["Tan, A. B.", "Lee, C. D."], "year": 2024,
     "title": "Paper title in sentence case",
     "journal": "Journal of Examples", "volume": "12", "issue": "3",
     "pages": "101-118", "doi": "10.1000/xyz123", "issn": "1234-5678",
     "type": "Quantitative", "access": "Free",
     "quartile": "Q1 (SJR 2024, Education)",
     "introduction": "...", "methodology": "...", "theory": "...",
     "results": "...", "discussion": "...",
     "crossref": "verified",
     "notices": [{"type": "correction", "date": "2004-03-06"}],
     "source_basis": "full text",
     "evidence": {"results": [{"q": "verbatim quote from the paper", "loc": "Results, p. 7"}]}}
  ],
  "synthesis": "A few sentences: recurring theories, dominant methods, quartile balance, gaps."
}

"id" is optional but recommended: a short stable key (the DOI is used if there is
none). Synthesis and concept JSON refer to papers by id or DOI, never by P-code,
because the P-codes renumber whenever a paper is added or removed.

Every cell must come from something actually retrieved. Empty cells print as
"Not retrieved"; a missing theory prints as "Not explicitly stated".
"source_basis" is "full text" | "partial" | "abstract only" and "evidence" holds,
per column, the verbatim quotes the cell was written from (checked by
check_evidence.py; see references/reading-and-writing.md). Neither is shown in
the LRM sheet; source_basis is listed on the Summary sheet.
"crossref" is "verified" | "mismatch" | "unchecked" and "notices" lists
retractions and corrections; both are written by crossref_check.py.
--check validates the file and prints problems and style warnings without
building anything. Needs openpyxl.
"""

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import argparse
import json
import re
import sys

from common import (FONT, NAVY, RED, apa_authors, clean_doi, dash, fold, fresh_sheet, open_workbook,
                    print_setup, protect_text, save, scrub, set_widths, sort_key, style_body, style_header, xl)

# A note in brackets may itself hold one bracket pair: "Social Sciences (miscellaneous)".
_NOTE = r"\((?:[^()]|\([^()]*\))*\)"
QUARTILE_OK = re.compile(rf"^(Q[1-4](\s*{_NOTE})?(\s*/\s*Q[1-4](\s*{_NOTE})?)*"
                         r"|N/A \(thesis/preprint/conference\)|Unranked/Unavailable)$")
TYPES = {"Quantitative", "Qualitative", "Mixed-methods", "Theoretical/Review"}
ACCESS = {"Free", "Paid", "Unclear"}
CROSSREF = {"verified", "mismatch", "unchecked"}
BASES = {"full text", "partial", "abstract only"}
TEXT_FIELDS = ["introduction", "methodology", "theory", "results", "discussion"]
COLUMNS = ["Code", "Type", "Authors", "Title", "Introduction", "Methodology", "Theory",
           "Results", "Discussion", "Quartile", "Access"]
WIDTHS = [7, 13, 22, 42, 34, 36, 22, 36, 36, 22, 9]
# Soft length limits (words). Over the limit is a warning, not an error: the
# aim is cells a person can read, not a wall of text.
WORD_LIMITS = {"introduction": 40, "methodology": 50, "theory": 25, "results": 60, "discussion": 60}
FIRST_PERSON = re.compile(r"\b(?:[Ww]e|[Oo]ur|[Oo]urs|[Mm]y|[Mm]e|us)\b"
                          r"|\bI (?:found|argue|think|believe|show|suggest|propose|examine|conclude|used|did)\b")
RETRACTED = {"retraction", "withdrawal", "removal"}
CONCERN = {"expression_of_concern", "expression of concern"}
AMBER_TEXT = "9C5700"


def status_of(paper):
    """-> (level, text) for the paper's retraction/correction state, or (None, '').
    level is 'red' (retracted) or 'amber' (expression of concern or correction)."""
    notes = sorted(paper.get("notices") or [], key=lambda n: n.get("date") or "")
    retracted = None
    for n in notes:
        t = (n.get("type") or "").lower()
        if t in RETRACTED:
            retracted = n
        elif t == "reinstatement":
            retracted = None
    if retracted:
        return "red", "RETRACTED" + (f" {retracted['date'][:10]}" if retracted.get("date") else "")
    if re.match(r"\s*retracted\b", paper.get("title") or "", re.I):
        return "red", "RETRACTED (per the title)"
    for n in notes:
        if (n.get("type") or "").lower() in CONCERN:
            return "amber", "Expression of concern" + (f" {n['date'][:10]}" if n.get("date") else "")
    corr = [n for n in notes if (n.get("type") or "").lower() == "correction"]
    if corr:
        d = corr[-1].get("date")
        return "amber", "Correction issued" + (f" {d[:10]}" if d else "")
    return None, ""


def problems_in(data):
    out = []
    if not isinstance(data, dict) or not isinstance(data.get("papers"), list) or not data["papers"]:
        return ['the file needs a non-empty "papers" list']
    for i, p in enumerate(data["papers"], 1):
        tag = f"paper {i} ({(p.get('title') or 'untitled')[:40]})"
        if not p.get("title"):
            out.append(f"{tag}: no title")
        a = p.get("authors")
        if not isinstance(a, list) or not a or not all(isinstance(x, str) and x.strip() for x in a):
            out.append(f'{tag}: "authors" must be a list like ["Tan, A. B.", "Lee, C. D."]')
        if not p.get("year"):
            out.append(f'{tag}: no year (use "n.d." if the paper has none)')
        q = (p.get("quartile") or "").strip()
        if not QUARTILE_OK.match(q):
            out.append(f"{tag}: quartile {q!r} must be Q1-Q4 from a real Scimago (SJR) lookup, "
                       f"'N/A (thesis/preprint/conference)' or 'Unranked/Unavailable'")
        if p.get("type") not in TYPES:
            out.append(f"{tag}: type must be one of {sorted(TYPES)}")
        if p.get("access") not in ACCESS:
            out.append(f"{tag}: access must be Free, Paid or Unclear")
        if p.get("crossref", "unchecked") not in CROSSREF:
            out.append(f"{tag}: crossref must be one of {sorted(CROSSREF)}")
        if p.get("source_basis") is not None and p["source_basis"] not in BASES:
            out.append(f"{tag}: source_basis must be one of {sorted(BASES)}")
    ids = [fold(p.get("id") or clean_doi(p.get("doi"))) for p in data["papers"]]
    for k in {x for x in ids if x and ids.count(x) > 1}:
        out.append(f'two papers share the id/DOI "{k}"; give each paper its own "id"')
    return out


def warnings_in(data):
    """Style and trust warnings that do not stop the build."""
    out = []
    papers = data["papers"]
    for i, p in enumerate(papers, 1):
        tag = f"paper {i} ({(p.get('title') or 'untitled')[:40]})"
        for f, limit in WORD_LIMITS.items():
            n = len((p.get(f) or "").split())
            if n > limit:
                out.append(f"{tag}: {f} is {n} words (aim for {limit} or fewer)")
            if FIRST_PERSON.search(p.get(f) or ""):
                out.append(f"{tag}: {f} uses first person; write about what the authors report")
        if p.get("crossref", "unchecked") == "mismatch":
            out.append(f"{tag}: citation does not match Crossref; run crossref_check.py")
        if any((p.get(f) or "").strip() for f in TEXT_FIELDS) and not p.get("evidence"):
            out.append(f"{tag}: cells have no evidence quotes; run check_evidence.py before sharing")
        if (p.get("quartile") or "").startswith("Q") and not p.get("issn"):
            out.append(f"{tag}: has a quartile but no issn on record to trace it to")
        level, text = status_of(p)
        if level == "red":
            out.append(f"{tag}: {text}; do not cite it as sound evidence without saying so")
    if len(papers) >= 4:
        for f in TEXT_FIELDS:
            starts = [" ".join((p.get(f) or "").split()[:2]).lower() for p in papers if p.get(f)]
            if len(starts) >= 4:  # a repeat only means something across several filled cells
                top = max(set(starts), key=starts.count)
                if starts.count(top) / len(starts) > 0.5:
                    out.append(f'{f}: {starts.count(top)} of {len(starts)} cells start with "{top}"; '
                               f"vary the wording (the authors, the researchers, the study, the team)")
    return out


def _title_key(p):
    t = fold(p.get("title") or "")
    return re.sub(r"^(a|an|the) ", "", t)


def ordered(data):
    """[(code, paper)] in APA 7 order. Papers with the same authors and year get
    the a, b, c year suffix (p["_ysuffix"], in memory only)."""
    papers = sorted(data["papers"], key=sort_key)
    groups = {}
    for p in papers:
        groups.setdefault((tuple(fold(a) for a in p.get("authors") or []), str(p.get("year"))), []).append(p)
    for g in groups.values():
        for p in g:
            p.pop("_ysuffix", None)
        if len(g) > 1:
            for letter, p in zip("abcdefghijklmnopqrstuvwxyz", sorted(g, key=_title_key)):
                p["_ysuffix"] = letter
    return [(f"P{i:02d}", p) for i, p in enumerate(papers, 1)]


def doi_url(p):
    d = clean_doi(p.get("doi"))
    return f"https://doi.org/{d}" if d else ""


def authors_text(p):
    return f"{apa_authors(p.get('authors') or [])} ({p.get('year') or 'n.d.'}{p.get('_ysuffix', '')})"


def title_cell(p):
    """The Title cell as rich text: [flag] / title. / Journal, vol(issue), pages. / DOI."""
    from openpyxl.cell.rich_text import CellRichText, TextBlock
    from openpyxl.cell.text import InlineFont

    def font(**kw):
        return InlineFont(rFont=FONT, sz=9, **kw)

    parts = []
    level, text = status_of(p)
    if level:
        parts.append(TextBlock(font(b=True, color=RED if level == "red" else AMBER_TEXT), text + "\n"))
    title = (p.get("title") or "").strip()
    parts.append(TextBlock(font(), title if title.endswith((".", "?", "!")) else title + "."))
    j = (p.get("journal") or "").strip()
    if j:
        parts.append(TextBlock(font(), "\n"))
        parts.append(TextBlock(font(i=True), j + (f", {p['volume']}" if p.get("volume") else "")))
        tail = (f"({p['issue']})" if p.get("issue") else "") + \
               (f", {dash(str(p['pages']))}" if p.get("pages") else "") + "."
        parts.append(TextBlock(font(), tail))
    if doi_url(p):
        parts.append(TextBlock(font(color="0563C1"), "\n" + doi_url(p)))
    return CellRichText(*parts)


def add_sheets(wb, data):
    _, Alignment, Border, Font, PatternFill, Side = xl()
    rows = ordered(data)
    n = len(rows)

    # ---- LRM sheet ------------------------------------------------------
    ws = fresh_sheet(wb, "LRM", 0)
    ws.append(COLUMNS)
    for code, p in rows:
        vals = [code, p.get("type") or "", authors_text(p), None]
        for f in TEXT_FIELDS:
            empty = "Not explicitly stated" if f == "theory" else "Not retrieved"
            vals.append((p.get(f) or "").strip() or empty)
        vals += [p.get("quartile") or "", p.get("access") or ""]
        ws.append(vals)
    style_header(ws, 1, len(COLUMNS), height=22)
    style_body(ws, 2, n + 1, len(COLUMNS))
    for r, (code, p) in enumerate(rows, 2):
        cell = ws.cell(row=r, column=4)
        cell.value = title_cell(p)  # rich text; the DOI link is shown as text (a cell hyperlink flattens it)
        code_cell = ws.cell(row=r, column=1)
        level, _ = status_of(p)
        if level:
            code_cell.fill = PatternFill("solid", fgColor=RED if level == "red" else "BF8F00")
            code_cell.font = Font(name=FONT, size=9, bold=True, color="FFFFFF")
        else:
            code_cell.font = Font(name=FONT, size=9, bold=True)
    protect_text(ws)
    set_widths(ws, WIDTHS)
    ws.freeze_panes = "D2"
    print_setup(ws)
    ws.auto_filter.ref = f"A1:K{n + 1}"

    # ---- Summary sheet --------------------------------------------------
    sm = fresh_sheet(wb, "Summary", 0)
    first, last = 12, 11 + n
    sm["A1"] = data.get("title") or "Literature Review Matrix"
    sm["A1"].font = Font(name=FONT, size=14, bold=True, color=NAVY)
    labels = [(3, "Field", data.get("field") or ""), (4, "Years", data.get("years") or ""),
              (5, "Papers", f"=COUNTA(A{first}:A{last})"),
              (6, "Order", "A-Z by first author's family name; codes assigned in that order"),
              (7, "Crossref verified", f'=COUNTIF(B{first}:B{last},"verified")&" of "&COUNTA(A{first}:A{last})'),
              (8, "Retracted or corrected", f'=COUNTIF(D{first}:D{last},"?*")'),
              (9, "Quartiles", "SJR (Scimago) quartile for the year and subject area shown in each LRM row")]
    for r, k, v in labels:
        sm.cell(row=r, column=1, value=k).font = Font(name=FONT, size=10, bold=True)
        sm.cell(row=r, column=2, value=v).font = Font(name=FONT, size=10)
    hdr = ["Code", "Crossref check", "Quartile source", "Retraction / correction notice", "Read from"]
    for j, h in enumerate(hdr, 1):
        sm.cell(row=11, column=j, value=h)
    style_header(sm, 11, len(hdr))
    for i, (code, p) in enumerate(rows, first):
        level, text = status_of(p)
        q = p.get("quartile") or ""
        sm.cell(row=i, column=1, value=code)
        sm.cell(row=i, column=2, value=p.get("crossref", "unchecked"))
        sm.cell(row=i, column=3, value="Scimago (SJR)" if q.startswith("Q") else q)
        sm.cell(row=i, column=4, value=text)
        sm.cell(row=i, column=5, value=p.get("source_basis") or "not recorded")
    style_body(sm, first, last, len(hdr))
    for i, (code, p) in enumerate(rows, first):
        level, _ = status_of(p)
        if level:
            sm.cell(row=i, column=4).font = Font(name=FONT, size=9, bold=True,
                                                 color=RED if level == "red" else AMBER_TEXT)
    if data.get("synthesis"):
        row = last + 2
        sm.cell(row=row, column=1, value="Synthesis").font = Font(name=FONT, size=11, bold=True, color=NAVY)
        sm.merge_cells(start_row=row + 1, start_column=1, end_row=row + 1, end_column=5)
        c = sm.cell(row=row + 1, column=1, value=data["synthesis"])
        c.font = Font(name=FONT, size=10)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        sm.row_dimensions[row + 1].height = max(60, 15 * (len(data["synthesis"]) // 100 + 1))
    protect_text(sm, skip={(5, 2), (7, 2), (8, 2)})  # the three count formulas
    set_widths(sm, [24, 24, 24, 44, 16])
    print_setup(sm)
    sm.print_title_rows = None
    return rows


def build(data, out):
    wb = open_workbook(out)
    stale = [n for n in ("Synthesis matrix", "Concept matrix") if n in wb.sheetnames]
    if stale:
        print(f"WARNING: {', '.join(stale)} was built from the previous LRM's codes (P01, P02 ...). "
              f"Codes renumber when papers change, so rebuild {'it' if len(stale) == 1 else 'them'} "
              f"from the same JSON with --lrm.", file=sys.stderr)
    add_sheets(wb, data)
    save(wb, out, order=["Summary", "LRM"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lrm")
    ap.add_argument("--out", help="the .xlsx workbook to create or update")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    try:
        data = json.load(open(a.lrm, encoding="utf-8"))
    except FileNotFoundError:
        print(f"Error: cannot find {a.lrm}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: {a.lrm} is not valid JSON ({e})", file=sys.stderr)
        return 1
    data = scrub(data)  # drop control characters that PDF text brings
    probs = problems_in(data)
    if probs:
        print("Fix these before building:\n- " + "\n- ".join(probs), file=sys.stderr)
        return 1
    warns = warnings_in(data)
    if warns:
        print("Warnings (the workbook still builds):\n- " + "\n- ".join(warns), file=sys.stderr)
    if a.check:
        print(f"OK: {len(data['papers'])} papers")
        return 0
    if not a.out:
        print("Error: give --out Matrix.xlsx", file=sys.stderr)
        return 1
    build(data, a.out)
    print(f"Wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
