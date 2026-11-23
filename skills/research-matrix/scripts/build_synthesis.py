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
  "sources": [{"code": "P01", "label": "Abdullah (2021)"}],   # optional with --lrm
  "themes": [
    {"name": "Theme text", "cells": {"P01": "what this source says about the theme"},
     "across": "optional: one or two sentences on how the sources agree or differ"}
  ]
}
--lrm lrm.json takes the codes and "Surname (year)" labels from the LRM, so the
matrices use the same P01, P02 ... codes. Needs openpyxl.
"""

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import argparse
import json
import sys

from build_lrm import ordered
from common import (print_setup, AMBER_FILL, FONT, first_family, fresh_sheet, open_workbook, save, set_widths,
                    style_body, style_header, xl)

SHEET = "Synthesis matrix"


def labels_from_lrm(path):
    data = json.load(open(path, encoding="utf-8"))
    out = []
    for code, p in ordered(data):
        fam = [first_family(a) for a in p.get("authors") or []]
        who = fam[0] if len(fam) == 1 else (f"{fam[0]} & {fam[1]}" if len(fam) == 2 else f"{fam[0]} et al.")
        out.append({"code": code, "label": f"{who} ({p.get('year') or 'n.d.'})"})
    return out


def problems_in(data, sources):
    out = []
    if not sources:
        out.append('no sources: list them in "sources" or pass --lrm')
    if not isinstance(data.get("themes"), list) or not data["themes"]:
        out.append('the file needs a non-empty "themes" list')
        return out
    codes = {s["code"] for s in sources}
    for i, t in enumerate(data["themes"], 1):
        if not t.get("name"):
            out.append(f"theme {i}: no name")
        for c in (t.get("cells") or {}):
            if c not in codes:
                out.append(f'theme {i}: cell for unknown source "{c}"')
    return out


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
        cells = t.get("cells") or {}
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
        data = json.load(open(a.synthesis, encoding="utf-8"))
        sources = labels_from_lrm(a.lrm) if a.lrm else data.get("sources") or []
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    probs = problems_in(data, sources)
    if probs:
        print("Fix these before building:\n- " + "\n- ".join(probs), file=sys.stderr)
        return 1
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
