#!/usr/bin/env python3
"""Build a concept matrix sheet: papers down the side, concepts across the top.

    python3 build_concept.py concept.json --out Matrix.xlsx [--lrm lrm.json] [--check]

Use only when the user explicitly asks for a concept matrix. --out is the same
workbook as the LRM: the sheet "Concept matrix" is added (or replaced) and the
other sheets are kept. After Webster and Watson (2002): an X marks a paper that
deals with a concept. The counts under each column and the coverage table are
live Excel formulas over the X marks (edit a mark and they update), so they
show which concepts the literature has covered and where the gaps are.

concept.json:
{
  "title": "Concept matrix: <topic>",
  "concepts": ["Digital literacy", "Parental support", "Rural schools"],
  "units": ["Individual", "Group", "Organisation"],        # optional
  "papers": [
    {"id": "abdullah2021", "concepts": ["Digital literacy", "Parental support"]},
    {"id": "chen2020",
     "concepts": {"Digital literacy": ["Individual"], "Parental support": ["Group"]}}
  ]
}
With "units", write each paper's concepts as a map from concept to the units of
analysis it was studied at (the second paper above); the matrix then has one
column per concept and unit. Without "units", a plain list is enough.
--lrm lrm.json takes the codes and labels from the LRM. Key each paper by its "id"
or DOI as written in lrm.json (not its P-code: codes renumber when papers change).
Without --lrm, list each paper with its "code" and "label". Needs openpyxl.
"""

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import argparse
import json
import sys

from build_synthesis import labels_from_lrm
from common import (AMBER_FILL, FONT, fresh_sheet, is_pcode, open_workbook, print_setup, protect_text,
                    resolve_paper, save, scrub, set_widths, style_body, style_header)

SHEET = "Concept matrix"


def marks(paper):
    """-> set of (concept, unit-or-None) the paper is marked for."""
    c = paper.get("concepts")
    c = [] if c is None else c
    if isinstance(c, dict):
        return {(k, u) for k, us in c.items() for u in (us or [])}
    return {(k, None) for k in c}


def problems_in(data, papers):
    out = []
    concepts = data.get("concepts") or []
    units = data.get("units") or []
    if not concepts:
        out.append('the file needs a non-empty "concepts" list')
    if not papers:
        out.append('no papers: list them in "papers" or pass --lrm')
    for label, items in (("concept", concepts), ("unit", units)):
        low = [str(x).strip().lower() for x in items]
        for x in {v for v in low if low.count(v) > 1}:
            out.append(f'{label} "{x}" is listed twice')
    for i, p in enumerate(papers, 1):
        if not p.get("code") or p.get("label") is None:
            out.append(f'paper {i}: each paper needs a "code" and a "label"')
    if out:
        return out
    known = set(concepts)
    seen = {}
    for p in data.get("papers") or []:
        key = p.get("code") or p.get("id") or p.get("doi")
        code = resolve_paper(key, papers)
        if code is None:
            out.append(f'paper "{key}" is not in the LRM (use the paper\'s "id" or DOI); '
                       f'its marks would be dropped and show as a false gap')
            continue
        if code in seen:
            out.append(f'"{key}" and "{seen[code]}" are the same paper')
        seen[code] = key
        c = p.get("concepts")
        c = [] if c is None else c
        if units and not isinstance(c, dict):
            out.append(f'{key}: with "units", "concepts" must map each concept to its units')
        names = c.keys() if isinstance(c, dict) else c
        for n in names:
            if n not in known:
                out.append(f'{key}: concept "{n}" is not in the "concepts" list')
        if isinstance(c, dict):
            for n, us in c.items():
                for u in us or []:
                    if u not in units:
                        out.append(f'{key}: unit "{u}" is not in the "units" list')
    return out


def pcode_warnings(data):
    bad = sorted(p.get("code") for p in data.get("papers") or [] if is_pcode(p.get("code")))
    return ([f"papers are keyed by position codes ({', '.join(bad[:4])}...). These renumber when papers "
             f"change; key by the paper's id or DOI instead."] if bad else [])


def add_sheet(wb, data, papers):
    from openpyxl.formatting.rule import FormulaRule
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter as L

    concepts, units = data["concepts"], data.get("units") or []
    cols = [(c, u) for c in concepts for u in (units or [None])]
    by_code = {resolve_paper(p.get("code") or p.get("id") or p.get("doi"), papers): marks(p)
               for p in data.get("papers") or []}
    npap, ncol = len(papers), len(cols)
    ws = fresh_sheet(wb, SHEET)
    ws.append(["Paper"] + [c + (f"\n({u})" if u else "") for c, u in cols])
    for s in papers:
        ws.append([f"{s['code']}  {s['label']}"] + ["X" if (c, u) in by_code.get(s["code"], set()) else None
                                                    for c, u in cols])
    first, last = 2, npap + 1
    cnt = last + 1
    ws.cell(row=cnt, column=1, value="Papers covering")
    for j in range(ncol):
        col = L(j + 2)
        ws.cell(row=cnt, column=j + 2, value=f'=COUNTIF({col}{first}:{col}{last},"X")')
    style_header(ws, 1, ncol + 1, height=34)
    style_body(ws, first, cnt, ncol + 1)
    centre = Alignment(horizontal="center", vertical="top", wrap_text=True)
    for r in range(first, cnt + 1):
        ws.cell(row=r, column=1).font = Font(name=FONT, size=9, bold=(r == cnt))
        for c in range(2, ncol + 2):
            ws.cell(row=r, column=c).alignment = centre
            if r == cnt:
                ws.cell(row=r, column=c).font = Font(name=FONT, size=9, bold=True)
    for c in range(2, ncol + 2):
        ws.cell(row=1, column=c).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Coverage table: papers per concept (any unit) and a plain-words status, both formulas.
    top = cnt + 3
    ws.cell(row=top - 1, column=1, value="Coverage by concept (updates when marks change)").font = \
        Font(name=FONT, size=10, bold=True)
    for j, h in enumerate(["Concept", "Papers", "Status"], 1):
        ws.cell(row=top, column=j, value=h)
    style_header(ws, top, 3)
    for i, c in enumerate(concepts, top + 1):
        idx = [j for j, (cc, _) in enumerate(cols) if cc == c]
        parts = "+".join(f'({L(j + 2)}{first}:{L(j + 2)}{last}="X")' for j in idx)
        ws.cell(row=i, column=1, value=c)
        ws.cell(row=i, column=2, value=f"=SUMPRODUCT(--(({parts})>0))")
        ws.cell(row=i, column=3, value=f'=IF(B{i}=0,"no paper (gap)",IF(B{i}=1,"only one paper (gap)",B{i}&" papers"))')
    style_body(ws, top + 1, top + len(concepts), 3)
    ws.conditional_formatting.add(f"B{top + 1}:C{top + len(concepts)}",
                                  FormulaRule(formula=[f"$B{top + 1}<=1"], fill=PatternFill("solid", bgColor=AMBER_FILL)))
    skip = {(cnt, j) for j in range(2, ncol + 2)} | {(r, k) for r in range(top + 1, top + len(concepts) + 1) for k in (2, 3)}
    protect_text(ws, skip=skip)
    set_widths(ws, [34] + [14] * ncol)
    print_setup(ws)
    ws.column_dimensions["C"].width = max(ws.column_dimensions["C"].width or 14, 24)
    ws.freeze_panes = "B2"
    return ws


def build(data, papers, out):
    wb = open_workbook(out)
    add_sheet(wb, data, papers)
    save(wb, out, order=["Summary", "LRM", "Synthesis matrix", SHEET])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("concept")
    ap.add_argument("--lrm")
    ap.add_argument("--out", help="the .xlsx workbook to create or update")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    try:
        data = scrub(json.load(open(a.concept, encoding="utf-8")))
        papers = labels_from_lrm(a.lrm) if a.lrm else [
            {"code": p.get("code"), "label": p.get("label", ""), "id": p.get("id", "")} for p in data.get("papers") or []]
    except (OSError, json.JSONDecodeError, KeyError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    probs = problems_in(data, papers)
    if probs:
        print("Fix these before building:\n- " + "\n- ".join(probs), file=sys.stderr)
        return 1
    for w in pcode_warnings(data):
        print("Warning: " + w, file=sys.stderr)
    if a.check:
        print(f"OK: {len(papers)} papers x {len(data['concepts'])} concepts")
        return 0
    if not a.out:
        print("Error: give --out Matrix.xlsx", file=sys.stderr)
        return 1
    build(data, papers, a.out)
    print(f"Wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
