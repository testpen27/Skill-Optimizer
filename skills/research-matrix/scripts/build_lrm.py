#!/usr/bin/env python3
"""Build the Literature Review Matrix (LRM) PDF from lrm.json.

    python3 build_lrm.py lrm.json --out lrm.pdf [--check]

lrm.json:
{
  "title": "Research title", "field": "Education", "years": "2021-2026",
  "papers": [
    {"title": "...", "authors_year": "Tan & Lee (2024)", "doi": "10.xxx/yyy",
     "quartile": "Q1", "method": "Quantitative", "access": "Free",
     "introduction": "...", "methodology": "...", "results": "...",
     "discussion": "...", "framework": "Technology Acceptance Model"}
  ],
  "synthesis": "A few sentences: recurring theories, dominant methods, quartile balance, gaps."
}

Every cell must come from something actually retrieved. Empty cells print as
"Not retrieved"; a missing framework prints as "Not explicitly stated".
--check validates the file and prints problems without building the PDF.
Needs reportlab (`pip install reportlab`).
"""

import argparse
import json
import re
import sys
from xml.sax.saxutils import escape

# A looked-up quartile, optionally with a note in brackets, and optionally a second
# one after "/" when sources disagree: "Q1 (SJR 2024, Education) / Q2 (Communication)".
QUARTILE_OK = re.compile(r"^(Q[1-4](\s*\([^()]*\))?(\s*/\s*Q[1-4](\s*\([^()]*\))?)*"
                         r"|N/A \(thesis/preprint/conference\)|Unranked/Unavailable)$")
METHODS = {"Quantitative", "Qualitative", "Mixed-methods", "Theoretical/Review"}
ACCESS = {"Free", "Paid", "Unclear"}
TEXT_FIELDS = ["introduction", "methodology", "results", "discussion"]


def problems_in(data):
    out = []
    if not isinstance(data, dict) or not isinstance(data.get("papers"), list) or not data["papers"]:
        return ['the file needs a non-empty "papers" list']
    for i, p in enumerate(data["papers"], 1):
        tag = f"paper {i} ({(p.get('title') or 'untitled')[:40]})"
        if not p.get("title"):
            out.append(f"{tag}: no title")
        if not p.get("authors_year"):
            out.append(f"{tag}: no authors_year")
        q = (p.get("quartile") or "").strip()
        if not QUARTILE_OK.match(q):
            out.append(f"{tag}: quartile {q!r} must be Q1-Q4 from a real SJR lookup, "
                       f"'N/A (thesis/preprint/conference)' or 'Unranked/Unavailable'")
        if p.get("method") not in METHODS:
            out.append(f"{tag}: method must be one of {sorted(METHODS)}")
        if p.get("access") not in ACCESS:
            out.append(f"{tag}: access must be Free, Paid or Unclear")
    return out


def build(data, out):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError:
        sys.exit("Error: reportlab is not installed. Run: pip install reportlab")

    ss = getSampleStyleSheet()
    cell = ParagraphStyle("cell", parent=ss["BodyText"], fontSize=7, leading=8.6)
    head = ParagraphStyle("head", parent=cell, textColor=colors.white, fontName="Helvetica-Bold")
    h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontSize=14, textColor=colors.HexColor("#1F3864"))
    body = ParagraphStyle("body", parent=ss["BodyText"], fontSize=9, leading=12)

    page = landscape(A4)
    margin = 0.4 * inch
    frame_w = page[0] - 2 * margin
    # Relative widths: short labels narrow, IMRAD text wide. Scaled to the frame
    # so the table can never be wider than the page.
    rel = [2.2, 11, 7, 7.2, 7.6, 4, 12.3, 12.3, 12.3, 12.3, 8]
    widths = [frame_w * r / sum(rel) for r in rel]
    assert abs(sum(widths) - frame_w) < 0.5

    cols = ["#", "Title", "Author(s) & Year", "Quartile", "Method", "Access",
            "Introduction", "Methodology", "Results", "Discussion", "Theoretical Framework"]
    rows = [[Paragraph(c, head) for c in cols]]
    for i, p in enumerate(data["papers"], 1):
        title = escape(p.get("title") or "")
        if p.get("doi"):
            title += f"<br/><font color='#0563C1'>doi:{escape(p['doi'])}</font>"
        # Let narrow label cells wrap at a slash ("Unranked/ Unavailable"), but keep "N/A" whole.
        label = lambda v: re.sub(r"(?<!N)/(?!A\b)", "/ ", escape(v or ""))
        vals = [str(i), title, escape(p.get("authors_year") or ""), label(p.get("quartile")),
                label(p.get("method")), escape(p.get("access") or "")]
        vals += [escape((p.get(f) or "").strip() or "Not retrieved") for f in TEXT_FIELDS]
        vals.append(escape((p.get("framework") or "").strip() or "Not explicitly stated"))
        rows.append([Paragraph(v, cell) for v in vals])

    t = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3864")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BFBFBF")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    story = [Paragraph(escape(data.get("title") or "Literature Review Matrix"), h1)]
    meta = " | ".join(x for x in [f"Field: {data['field']}" if data.get("field") else "",
                                  f"Years: {data['years']}" if data.get("years") else "",
                                  f"{len(data['papers'])} papers"] if x)
    story += [Paragraph(escape(meta), body), Spacer(1, 6), t]
    if data.get("synthesis"):
        story += [Spacer(1, 10), Paragraph("<b>Synthesis</b>", body), Paragraph(escape(data["synthesis"]), body)]

    def footer(c, doc):
        c.saveState()
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.grey)
        c.drawRightString(page[0] - margin, 14, f"Page {doc.page}")
        c.restoreState()

    doc = SimpleDocTemplate(out, pagesize=page, leftMargin=margin, rightMargin=margin,
                            topMargin=margin, bottomMargin=margin, title=data.get("title") or "LRM")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lrm")
    ap.add_argument("--out")
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
    probs = problems_in(data)
    if probs:
        print("Fix these before building:\n- " + "\n- ".join(probs), file=sys.stderr)
        return 1
    if a.check:
        print(f"OK: {len(data['papers'])} papers")
        return 0
    if not a.out:
        print("Error: give --out lrm.pdf", file=sys.stderr)
        return 1
    build(data, a.out)
    print(f"Wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
