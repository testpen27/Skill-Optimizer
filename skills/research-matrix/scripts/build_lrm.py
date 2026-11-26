#!/usr/bin/env python3
"""Build the Literature Review Matrix (LRM) as an Excel sheet from lrm.json.

    python3 build_lrm.py lrm.json --out Matrix.xlsx [--check]

--out is a workbook. If it exists the "Summary" and "LRM" sheets are replaced
and every other sheet (synthesis, concept ...) is kept; otherwise it is created.

Sheet "LRM", columns left to right: Code | Type | Authors | Title |
Introduction | Methodology | Theory | Results | Discussion | Limitations and future
research | Quartile.
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
     "type": "Quantitative",
     "quartile": "Q1 (SJR 2024, Education)",
     "introduction": "...", "methodology": "...", "theory": "...",
     "results": "...", "discussion": "...", "limitations": "...",
     "crossref": "verified",
     "notices": [{"type": "correction", "date": "2004-03-06"}],
     "source_basis": "full text",
     "overclaims": [{"field": "results", "text": "the exact words in the cell written from the body",
                     "abstract": "the abstract's verbatim claim", "body": "the body's verbatim finding",
                     "body_loc": "Results, p. 7"}],
     "evidence": {"results": [{"q": "verbatim quote from the paper", "loc": "Results, p. 7"}]}}
  ],
  "synthesis": "A few sentences: recurring theories, dominant methods, quartile balance.",
  "gaps": [{"gap": "Among these 12 papers, none follows pupils beyond one school year.",
            "kind": "across papers", "papers": ["tan2024", "10.1000/abc"],
            "basis": "the limitation cells of both papers"}]
}

"id" is optional but recommended: a short stable key (the DOI is used if there is
none). Synthesis and concept JSON refer to papers by id or DOI, never by P-code,
because the P-codes renumber whenever a paper is added or removed.

Every cell must come from something actually retrieved. Empty cells print as
"Not retrieved"; a missing theory or a paper that states no limitation prints as
"Not explicitly stated". "limitations" holds only what the authors themselves say
limits the study or should be done next. "gaps" (Summary sheet) are the
reviewer's reading across the papers, each tied to the papers it rests on by id or
DOI (never a P-code); see references/gap-list.md.
"overclaims" marks a finding where the abstract claims more than (or differently
from) the body: the cell is written from the body, and those words are shown in
dark-yellow text with a hover note quoting both. Other words stay black.
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

from common import (FONT, NAVY, RED, apa_authors, is_pcode, resolve_paper, clean_doi, dash, fold, fresh_sheet, open_workbook,
                    print_setup, protect_text, save, scrub, set_widths, sort_key, style_body, style_header, xl)

# A note in brackets may itself hold one bracket pair: "Social Sciences (miscellaneous)".
_NOTE = r"\((?:[^()]|\([^()]*\))*\)"
QUARTILE_OK = re.compile(rf"^(Q[1-4](\s*{_NOTE})?(\s*/\s*Q[1-4](\s*{_NOTE})?)*"
                         r"|N/A \(thesis/preprint/conference\)|Unranked/Unavailable)$")
TYPES = {"Quantitative", "Qualitative", "Mixed-methods", "Theoretical/Review"}
CROSSREF = {"verified", "mismatch", "unchecked"}
BASES = {"full text", "partial", "abstract only"}
TEXT_FIELDS = ["introduction", "methodology", "theory", "results", "discussion", "limitations"]
COLUMNS = ["Code", "Type", "Authors", "Title", "Introduction", "Methodology", "Theory",
           "Results", "Discussion", "Limitations and future research", "Quartile"]
WIDTHS = [7, 13, 22, 42, 34, 36, 22, 36, 36, 36, 22]
# Soft length limits (words). Over the limit is a warning, not an error: the
# aim is cells a person can read, not a wall of text.
WORD_LIMITS = {"introduction": 40, "methodology": 50, "theory": 25, "results": 60, "discussion": 60, "limitations": 60}
FIRST_PERSON = re.compile(r"\b(?:[Ww]e|[Oo]ur|[Oo]urs|[Mm]y|[Mm]e|us)\b"
                          r"|\bI (?:found|argue|think|believe|show|suggest|propose|examine|conclude|used|did)\b")
RETRACTED = {"retraction", "withdrawal", "removal"}
CONCERN = {"expression_of_concern", "expression of concern"}
AMBER_TEXT = "9C5700"
# Text colour for a finding where the abstract claims more than the body reports.
# A dark gold: pure yellow (FFFF00) is close to invisible on white and grey rows.
OVERCLAIM_TEXT = "BF9000"


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


GAP_KINDS = {"stated by authors", "across papers"}
EXPLAINS = re.compile(r"\b(because|since|so that|which means|as a result|therefore|thus)\b", re.I)
ABSOLUTE = re.compile(r"\b(no|none|nobody|never|nothing|all|every|always)\b|\blacks?\b|has not been|have not been", re.I)
SCOPED = re.compile(r"\b(among|within|in) (these|this|the) (\d+ )?(papers|studies|set|sample)|\bof these\b|\bthe authors?\b", re.I)


def gap_problems(data):
    """Errors in data["gaps"]: each must say what it is, name papers by id or DOI, and resolve."""
    gaps = data.get("gaps")
    if gaps is None:
        return []
    if not isinstance(gaps, list):
        return ['"gaps" must be a list of {"gap", "kind", "papers", "basis"}']
    out = []
    try:
        sources = [{"code": c, "id": p.get("id"), "doi": p.get("doi")} for c, p in ordered(data)]
    except Exception:
        sources = []
    for i, g in enumerate(gaps, 1):
        tag = f"gap {i}"
        if not isinstance(g, dict) or not (g.get("gap") or "").strip():
            out.append(f"{tag}: needs a non-empty \"gap\" text")
            continue
        if g.get("kind") not in GAP_KINDS:
            out.append(f"{tag}: kind must be one of {sorted(GAP_KINDS)}")
        keys = g.get("papers")
        if not isinstance(keys, list) or not keys:
            out.append(f"{tag}: must name the papers it rests on (ids or DOIs)")
            continue
        for k in keys:
            if is_pcode(k):
                out.append(f"{tag}: {k!r} is a P-code; refer to papers by id or DOI, because codes renumber")
            elif not resolve_paper(k, sources):
                out.append(f"{tag}: {k!r} is not the id or DOI of any paper in the file")
    return out


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
        if p.get("crossref", "unchecked") not in CROSSREF:
            out.append(f"{tag}: crossref must be one of {sorted(CROSSREF)}")
        for k, oc in enumerate(p.get("overclaims") or [], 1):
            f, txt = oc.get("field"), (oc.get("text") or "").strip()
            if f not in TEXT_FIELDS:
                out.append(f"{tag}: overclaim {k}: field must be one of {TEXT_FIELDS}")
            elif not txt or txt not in (p.get(f) or ""):
                out.append(f"{tag}: overclaim {k}: \"text\" must be the exact words of the {f} cell to colour")
            if not (oc.get("abstract") or "").strip() or not (oc.get("body") or "").strip():
                out.append(f"{tag}: overclaim {k}: needs both the abstract's quote and the body's quote")
        if p.get("source_basis") is not None and p["source_basis"] not in BASES:
            out.append(f"{tag}: source_basis must be one of {sorted(BASES)}")
    ids = [fold(p.get("id") or clean_doi(p.get("doi"))) for p in data["papers"]]
    for k in {x for x in ids if x and ids.count(x) > 1}:
        out.append(f'two papers share the id/DOI "{k}"; give each paper its own "id"')
    out += gap_problems(data)
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
    for i, g in enumerate(data.get("gaps") or [], 1):
        if isinstance(g, dict):
            t = g.get("gap") or ""
            if ABSOLUTE.search(t) and not SCOPED.search(t):
                out.append(f"gap {i}: sounds like a claim about the whole field; scope it to these papers "
                           f'("Among these N papers, ...") because absence here is not absence in the literature')
            if FIRST_PERSON.search(t):
                out.append(f"gap {i}: uses first person")
            m = EXPLAINS.search(t)
            if m:
                out.append(f'gap {i}: "{m.group(0)}" explains or draws a consequence the cells may not state; '
                           f"state the limitation or the call for future work and stop")
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


def overclaim_cell(text, spans):
    """Rich text: the overclaimed spans in OVERCLAIM_TEXT colour, the rest plain."""
    from openpyxl.cell.rich_text import CellRichText, TextBlock
    from openpyxl.cell.text import InlineFont
    marks = []
    for sp in spans:
        i = text.find(sp)
        if i >= 0:
            marks.append((i, i + len(sp)))
    marks.sort()
    merged = []
    for a, b in marks:
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else:
            merged.append((a, b))
    plain, flagged = InlineFont(rFont=FONT, sz=9), InlineFont(rFont=FONT, sz=9, color=OVERCLAIM_TEXT)
    parts, pos = [], 0
    for a, b in merged:
        if a > pos:
            parts.append(TextBlock(plain, text[pos:a]))
        parts.append(TextBlock(flagged, text[a:b]))
        pos = b
    if pos < len(text):
        parts.append(TextBlock(plain, text[pos:]))
    return CellRichText(*parts)


def overclaim_note(ocs):
    lines = ["The abstract claims more than the body reports. The cell follows the body."]
    for oc in ocs:
        lines.append(f'\nAbstract: "{oc["abstract"].strip()}"')
        lines.append(f'Body{" (" + oc["body_loc"] + ")" if oc.get("body_loc") else ""}: "{oc["body"].strip()}"')
    return "\n".join(lines)


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
            empty = "Not explicitly stated" if f in ("theory", "limitations") else "Not retrieved"
            vals.append((p.get(f) or "").strip() or empty)
        vals.append(p.get("quartile") or "")
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
        for j, f in enumerate(TEXT_FIELDS, 5):
            ocs = [oc for oc in p.get("overclaims") or [] if oc.get("field") == f]
            if ocs and (p.get(f) or "").strip():
                from openpyxl.comments import Comment
                c = ws.cell(row=r, column=j)
                c.value = overclaim_cell(p[f].strip(), [oc["text"].strip() for oc in ocs])
                note = Comment(overclaim_note(ocs), "research-matrix")
                note.width, note.height = 320, 160
                c.comment = note
    protect_text(ws)
    set_widths(ws, WIDTHS)
    ws.freeze_panes = "D2"
    print_setup(ws)
    ws.auto_filter.ref = f"A1:{chr(64 + len(COLUMNS))}{n + 1}"

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
    n_over = sum(1 for _, p in rows if p.get("overclaims"))
    n_side = sum(1 for _, p in rows if p.get("overclaims_unplaced") or p.get("overclaims_unsettled"))
    sm.cell(row=10, column=1, value="Yellow text").font = Font(name=FONT, size=10, bold=True, color=OVERCLAIM_TEXT)
    sm.cell(row=10, column=2, value=f"{n_over} paper(s): the abstract claims more than the body reports; the cell "
                                    f"follows the body. Hover over the cell for both quotes."
                                    + (f" {n_side} paper(s) have further abstract-vs-body notes in the last column below." if n_side else "")).font = \
        Font(name=FONT, size=10, color=OVERCLAIM_TEXT)
    hdr = ["Code", "Crossref check", "Quartile source", "Retraction / correction notice", "Read from",
           "Abstract vs body, not shown in the LRM"]
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
        side = [f'Abstract: "{o["abstract"]}" / Body: "{o["body"]}"' for o in p.get("overclaims_unplaced") or []]
        side += [f'To check (no quote settles it): "{u}"' for u in p.get("overclaims_unsettled") or []]
        sm.cell(row=i, column=6, value="\n".join(side) or None)
    style_body(sm, first, last, len(hdr))
    for i, (code, p) in enumerate(rows, first):
        level, _ = status_of(p)
        if level:
            sm.cell(row=i, column=4).font = Font(name=FONT, size=9, bold=True,
                                                 color=RED if level == "red" else AMBER_TEXT)
    if data.get("synthesis"):
        row = last + 2
        sm.cell(row=row, column=1, value="Synthesis").font = Font(name=FONT, size=11, bold=True, color=NAVY)
        sm.merge_cells(start_row=row + 1, start_column=1, end_row=row + 1, end_column=6)
        c = sm.cell(row=row + 1, column=1, value=data["synthesis"])
        c.font = Font(name=FONT, size=10)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        sm.row_dimensions[row + 1].height = max(60, 15 * (len(data["synthesis"]) // 100 + 1))
    gaps = [g for g in data.get("gaps") or [] if isinstance(g, dict) and (g.get("gap") or "").strip()]
    gap_formula_cells = set()
    if gaps:
        src = [{"code": c, "id": p.get("id"), "doi": p.get("doi")} for c, p in rows]
        row = (last + 2 + (3 if data.get("synthesis") else 0))
        sm.cell(row=row, column=1, value="Research gaps").font = Font(name=FONT, size=11, bold=True, color=NAVY)
        sm.merge_cells(start_row=row + 1, start_column=1, end_row=row + 1, end_column=6)
        note = sm.cell(row=row + 1, column=1, value=(
            "The reviewer's reading of these papers, not claims of the papers themselves: absence among "
            f"these {n} papers is not absence in the literature. 'Stated by authors' gaps come from the "
            "limitation and future-research cells."))
        note.font = Font(name=FONT, size=9, italic=True)
        note.alignment = Alignment(wrap_text=True, vertical="top")
        sm.row_dimensions[row + 1].height = 28
        for j, h in enumerate(["Kind", "Gap", None, "Papers", "How many", "Basis"], 1):
            sm.cell(row=row + 2, column=j, value=h)
        sm.merge_cells(start_row=row + 2, start_column=2, end_row=row + 2, end_column=3)
        style_header(sm, row + 2, 6)
        for k, g in enumerate(gaps, row + 3):
            cs = []
            for key in g.get("papers") or []:
                c = resolve_paper(key, src)
                if c and c not in cs:
                    cs.append(c)
            sm.cell(row=k, column=1, value=(g.get("kind") or "").capitalize())
            sm.cell(row=k, column=2, value=g["gap"].strip())
            sm.merge_cells(start_row=k, start_column=2, end_row=k, end_column=3)
            sm.cell(row=k, column=4, value=", ".join(sorted(cs)))
            sm.cell(row=k, column=5, value=f'=IF(D{k}="",0,LEN(D{k})-LEN(SUBSTITUTE(D{k},",",""))+1)')
            gap_formula_cells.add((k, 5))
            sm.cell(row=k, column=6, value=(g.get("basis") or "").strip() or None)
            sm.row_dimensions[k].height = max(32, 15 * (len(g["gap"]) // 55 + 1))
        style_body(sm, row + 3, row + 2 + len(gaps), 6)
    protect_text(sm, skip={(5, 2), (7, 2), (8, 2)} | gap_formula_cells)  # the count formulas
    set_widths(sm, [24, 24, 24, 44, 16, 70])
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
