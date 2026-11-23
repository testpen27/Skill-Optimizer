#!/usr/bin/env python3
"""Build a concept matrix PDF: papers down the side, concepts across the top.

    python3 build_concept.py concept.json --out Concept.pdf [--lrm lrm.json] [--check]

Use only when the user explicitly asks for a concept matrix. After Webster and
Watson (2002): an X marks a paper that deals with a concept. The counts under
each column and the list of rarely covered concepts are computed from the
marks, never typed, so they show which concepts the literature has covered and
where the gaps are.

concept.json:
{
  "title": "Concept matrix: <topic>",
  "concepts": ["Digital literacy", "Parental support", "Rural schools"],
  "units": ["Individual", "Group", "Organisation"],        # optional
  "papers": [
    {"code": "P01", "label": "Abdullah (2021)", "concepts": ["Digital literacy", "Parental support"]},
    {"code": "P02", "label": "Chen (2020)",
     "concepts": {"Digital literacy": ["Individual"], "Parental support": ["Group"]}}
  ]
}
With "units", write each paper's concepts as a map from concept to the units of
analysis it was studied at (the second paper above); the matrix then has one
column per concept and unit. Without "units", a plain list is enough.
--lrm lrm.json takes the codes and labels from the LRM. Needs reportlab.
"""

import argparse
import json
import sys

from build_synthesis import labels_from_lrm
from common import build_doc, escape, make_styles, pdf_parts, table_style

MAX_COLS = 10


def marks(paper, units):
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
    known = set(concepts)
    for p in data.get("papers") or []:
        c = p.get("concepts")
        c = [] if c is None else c
        if units and not isinstance(c, dict):
            out.append(f'{p.get("code")}: with "units", "concepts" must map each concept to its units')
        names = c.keys() if isinstance(c, dict) else c
        for n in names:
            if n not in known:
                out.append(f'{p.get("code")}: concept "{n}" is not in the "concepts" list')
        if isinstance(c, dict):
            for n, us in c.items():
                for u in us or []:
                    if u not in units:
                        out.append(f'{p.get("code")}: unit "{u}" is not in the "units" list')
    return out


def build(data, papers, out):
    pp = pdf_parts()
    Paragraph, Spacer, Table = pp["Paragraph"], pp["Spacer"], pp["Table"]
    cell, head, h1, body = make_styles(pp)
    margin = 0.4 * pp["inch"]
    frame_w = pp["landscape"](pp["A4"])[0] - 2 * margin
    concepts, units = data["concepts"], data.get("units") or []
    cols = [(c, u) for c in concepts for u in (units or [None])]
    by_code = {p["code"]: marks(p, units) for p in data.get("papers") or []}
    centre = pp["ParagraphStyle"]("c", parent=cell, alignment=1)
    centre_head = pp["ParagraphStyle"]("ch", parent=head, alignment=1)

    story = [Paragraph(escape(data.get("title") or "Concept matrix"), h1),
             Paragraph(escape(f"{len(papers)} papers, {len(concepts)} concepts"
                              + (f", by unit of analysis ({', '.join(units)})" if units else "")), body),
             Spacer(1, 6)]
    for start in range(0, len(cols), MAX_COLS):
        chunk = cols[start:start + MAX_COLS]
        rel = [4.2] + [1.6] * len(chunk)
        widths = [frame_w * r / sum(rel) for r in rel]
        hdr = [Paragraph("Paper", head)]
        for c, u in chunk:
            hdr.append(Paragraph(escape(c) + (f"<br/>({escape(u)})" if u else ""), centre_head))
        rows = [hdr]
        for s in papers:
            row = [Paragraph(f"{escape(s['code'])}  {escape(s['label'])}", cell)]
            row += [Paragraph("X" if (c, u) in by_code.get(s["code"], set()) else "", centre) for c, u in chunk]
            rows.append(row)
        total = [Paragraph("<b>Papers</b>", cell)]
        total += [Paragraph(f"<b>{sum(1 for s in papers if (c, u) in by_code.get(s['code'], set()))}</b>", centre)
                  for c, u in chunk]
        rows.append(total)
        tb = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
        tb.setStyle(table_style(pp))
        story += [tb, Spacer(1, 10)]

    story.append(Paragraph("<b>Coverage</b> (computed from the marks above)", body))
    for c in concepts:
        n = sum(1 for s in papers if any(k == c for k, _ in by_code.get(s["code"], set())))
        note = "no paper" if n == 0 else "only one paper" if n == 1 else f"{n} papers"
        flag = "  <- gap" if n <= 1 else ""
        story.append(Paragraph(escape(f"{c}: {note}{flag}"), body))
    build_doc(pp, out, story, data.get("title") or "Concept matrix", margin)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("concept")
    ap.add_argument("--lrm")
    ap.add_argument("--out")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    try:
        data = json.load(open(a.concept, encoding="utf-8"))
        papers = labels_from_lrm(a.lrm) if a.lrm else [
            {"code": p["code"], "label": p.get("label", "")} for p in data.get("papers") or []]
    except (OSError, json.JSONDecodeError, KeyError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    probs = problems_in(data, papers)
    if probs:
        print("Fix these before building:\n- " + "\n- ".join(probs), file=sys.stderr)
        return 1
    if a.check:
        print(f"OK: {len(papers)} papers x {len(data['concepts'])} concepts")
        return 0
    if not a.out:
        print("Error: give --out Concept.pdf", file=sys.stderr)
        return 1
    build(data, papers, a.out)
    print(f"Wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
