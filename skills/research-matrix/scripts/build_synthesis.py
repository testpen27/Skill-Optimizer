#!/usr/bin/env python3
"""Build a synthesis matrix PDF: themes down the side, sources across the top.

    python3 build_synthesis.py synthesis.json --out Synthesis.pdf [--lrm lrm.json] [--check]

Use only when the user asks for a synthesis matrix. Each cell holds what that
source says about that theme (paraphrased; add a page number only for a direct
quotation). An empty cell is shown as a dash: a theme that few sources cover is
a gap in the literature, and the gaps are listed under the table.

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
two matrices use the same P01, P02 ... codes. Needs reportlab.
"""

import argparse
import json
import sys

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from build_lrm import ordered
from common import build_doc, escape, first_family, make_styles, pdf_parts, table_style

PER_TABLE = 5


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


def gaps(data, sources):
    lines = []
    for t in data["themes"]:
        missing = [s["code"] for s in sources if not (t.get("cells") or {}).get(s["code"], "").strip()]
        if missing:
            lines.append(f"{t['name']}: no entry from {', '.join(missing)}"
                         + (" (no source covers it)" if len(missing) == len(sources) else ""))
    return lines


def build(data, sources, out):
    pp = pdf_parts()
    Paragraph, Spacer, Table = pp["Paragraph"], pp["Spacer"], pp["Table"]
    cell, head, h1, body = make_styles(pp)
    margin = 0.4 * pp["inch"]
    frame_w = pp["landscape"](pp["A4"])[0] - 2 * margin
    story = [Paragraph(escape(data.get("title") or "Synthesis matrix"), h1),
             Paragraph(escape(f"{len(data['themes'])} themes, {len(sources)} sources"), body), Spacer(1, 6)]
    for start in range(0, len(sources), PER_TABLE):
        chunk = sources[start:start + PER_TABLE]
        rel = [2.2] + [3.0] * len(chunk)
        widths = [frame_w * r / sum(rel) for r in rel]
        rows = [[Paragraph("Theme", head)] + [Paragraph(f"{escape(s['code'])}<br/>{escape(s['label'])}", head)
                                              for s in chunk]]
        for t in data["themes"]:
            row = [Paragraph(f"<b>{escape(t['name'])}</b>", cell)]
            for s in chunk:
                txt = ((t.get("cells") or {}).get(s["code"]) or "").strip()
                row.append(Paragraph(escape(txt) if txt else "–", cell))
            rows.append(row)
        tb = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
        tb.setStyle(table_style(pp))
        story += [tb, Spacer(1, 10)]
    across = [t for t in data["themes"] if t.get("across")]
    if across:
        rows = [[Paragraph("Theme", head), Paragraph("Across the sources", head)]]
        rows += [[Paragraph(f"<b>{escape(t['name'])}</b>", cell), Paragraph(escape(t["across"]), cell)]
                 for t in across]
        tb = Table(rows, colWidths=[frame_w * 0.25, frame_w * 0.75], repeatRows=1, hAlign="LEFT")
        tb.setStyle(table_style(pp))
        story += [Paragraph("<b>Reading across the rows</b>", body), Spacer(1, 3), tb, Spacer(1, 8)]
    g = gaps(data, sources)
    if g:
        story += [Paragraph("<b>Gaps</b> (a dash in the table)", body)]
        story += [Paragraph(escape(line), body) for line in g]
    build_doc(pp, out, story, data.get("title") or "Synthesis matrix", margin)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("synthesis")
    ap.add_argument("--lrm")
    ap.add_argument("--out")
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
        print("Error: give --out Synthesis.pdf", file=sys.stderr)
        return 1
    build(data, sources, a.out)
    print(f"Wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
