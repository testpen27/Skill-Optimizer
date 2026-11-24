#!/usr/bin/env python3
"""Build a synthesis matrix sheet: themes down the side, sources across the top.

    python3 build_synthesis.py synthesis.json --out Matrix.xlsx [--lrm lrm.json] [--check]

Use only when the user asks for a synthesis matrix. --out is the same workbook
as the LRM: the sheet "Synthesis matrix" is added (or replaced) and the other
sheets are kept. Each cell holds what that source says about that theme
(paraphrased; add a page number only for a direct quotation). A cell left
empty means the source does not address the theme: it is shaded, and the
"Sources covering" column counts the filled cells with a live formula, so a
theme few sources cover reads as a gap.

synthesis.json:
{
  "title": "Synthesis matrix: <topic>",
  "sources": [{"code": "P01", "label": "Abdullah (2021)"}],   # only without --lrm
  "themes": [
    {"name": "Theme text", "cells": {"abdullah2021": "what this source says about the theme"},
     "across": "optional: one or two sentences on how the sources agree or differ"}
  ]
}
--lrm lrm.json takes the codes and "Surname (year)" labels from the LRM, so the
matrices use the same P01, P02 ... codes. Key each cell by the paper's "id" or DOI
as written in lrm.json, NOT by its P-code: the codes renumber whenever a paper is
added or removed, and a cell keyed by a code would silently move to another paper. Needs openpyxl.
"""

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import argparse
import json
import sys

from build_lrm import ordered
from common import (AMBER_FILL, FONT, clean_doi, first_family, fresh_sheet, is_pcode, open_workbook, print_setup,
                    protect_text, resolve_paper, save, scrub, set_widths, style_body, style_header, xl)

SHEET = "Synthesis matrix"


def labels_from_lrm(path):
    data = scrub(json.load(open(path, encoding="utf-8")))
    out = []
    for code, p in ordered(data):
        fam = [first_family(a) for a in p.get("authors") or []]
        who = fam[0] if len(fam) == 1 else (f"{fam[0]} & {fam[1]}" if len(fam) == 2 else f"{fam[0]} et al.")
        out.append({"code": code, "label": f"{who} ({p.get('year') or 'n.d.'}{p.get('_ysuffix', '')})",
                    "id": p.get("id") or "", "doi": clean_doi(p.get("doi"))})
    return out


def problems_in(data, sources):
    out = []
    if not sources:
        out.append('no sources: list them in "sources" or pass --lrm')
    for i, s in enumerate(sources, 1):
        if not s.get("code") or not s.get("label"):
            out.append(f'source {i}: each source needs a "code" and a "label"')
    if out:
        return out
    if not isinstance(data.get("themes"), list) or not data["themes"]:
        out.append('the file needs a non-empty "themes" list')
        return out
    names = [str(t.get("name") or "").strip().lower() for t in data["themes"]]
    for n in {x for x in names if x and names.count(x) > 1}:
        out.append(f'theme "{n}" appears twice')
    for i, t in enumerate(data["themes"], 1):
        if not t.get("name"):
            out.append(f"theme {i}: no name")
        seen = {}
        for key in (t.get("cells") or {}):
            code = resolve_paper(key, sources)
            if code is None:
                out.append(f'theme {i}: cell for "{key}", which is not a paper in the LRM '
                           f'(use the paper\'s "id" or DOI)')
            elif code in seen:
                out.append(f'theme {i}: "{key}" and "{seen[code]}" are the same paper')
            else:
                seen[code] = key
    return out


def pcode_warnings(data):
    keys = {k for t in data.get("themes") or [] for k in (t.get("cells") or {})}
    bad = sorted(k for k in keys if is_pcode(k))
    return ([f"cells are keyed by position codes ({', '.join(bad[:4])}...). These renumber when papers "
             f"change; key by the paper's id or DOI instead."] if bad else [])


def add_sheet(wb, data, sources):
    from openpyxl.formatting.rule import FormulaRule
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter as L

    themes = data["themes"]
    ns, nt = len(sources), len(themes)
    ws = fresh_sheet(wb, SHEET)
    last_src = 1 + ns
    cov_col, across_col = last_src + 1, last_src + 2
    ws.append(["Theme"] + [f"{s['code']}\n{s['label']}" for s in sources] + ["Sources covering", "Across the sources"])
    for t in themes:
        cells = {resolve_paper(k, sources): v for k, v in (t.get("cells") or {}).items()}
        ws.append([t["name"]] + [(cells.get(s["code"]) or "").strip() or None for s in sources] + [None, t.get("across") or None])
    ncols = across_col
    style_header(ws, 1, ncols, height=34)
    style_body(ws, 2, nt + 1, ncols)
    for r in range(2, nt + 2):
        ws.cell(row=r, column=1).font = Font(name=FONT, size=9, bold=True)
        ws.cell(row=r, column=cov_col, value=f"=COUNTA({L(2)}{r}:{L(last_src)}{r})")
    rng = f"{L(2)}2:{L(last_src)}{nt + 1}"
    ws.conditional_formatting.add(rng, FormulaRule(formula=["ISBLANK(B2)"], fill=PatternFill("solid", bgColor=AMBER_FILL)))
    ws.conditional_formatting.add(f"{L(cov_col)}2:{L(cov_col)}{nt + 1}",
                                  FormulaRule(formula=[f"{L(cov_col)}2<=1"], fill=PatternFill("solid", bgColor=AMBER_FILL)))
    note = ws.cell(row=nt + 3, column=1,
                   value="A shaded empty cell means the source does not address the theme. "
                         "'Sources covering' counts the filled cells; 0 or 1 is shaded as a gap.")
    note.font = Font(name=FONT, size=9, italic=True)
    set_widths(ws, [28] + [30] * ns + [11, 40])
    protect_text(ws, skip={(r, cov_col) for r in range(2, nt + 2)})
    ws.freeze_panes = "B2"
    print_setup(ws)
    return ws


def build(data, sources, out):
    wb = open_workbook(out)
    add_sheet(wb, data, sources)
    save(wb, out, order=["Summary", "LRM", SHEET])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("synthesis")
    ap.add_argument("--lrm")
    ap.add_argument("--out", help="the .xlsx workbook to create or update")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    try:
        data = scrub(json.load(open(a.synthesis, encoding="utf-8")))
        sources = labels_from_lrm(a.lrm) if a.lrm else data.get("sources") or []
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    probs = problems_in(data, sources)
    if probs:
        print("Fix these before building:\n- " + "\n- ".join(probs), file=sys.stderr)
        return 1
    for w in pcode_warnings(data):
        print("Warning: " + w, file=sys.stderr)
    if a.check:
        print(f"OK: {len(data['themes'])} themes x {len(sources)} sources")
        return 0
    if not a.out:
        print("Error: give --out Matrix.xlsx", file=sys.stderr)
        return 1
    build(data, sources, a.out)
    print(f"Wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
