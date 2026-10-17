#!/usr/bin/env python3
"""Build the PDF search report: strategy, every string with its hit count,
a PRISMA 2020 flow diagram, and what was retrieved.

    python3 build_report.py --log search_log.json [--records records.json]
                            [--manifest DIR/manifest.json] --out report.pdf

Needs reportlab (`pip install reportlab`).

The search log is the file made by `node search_tool.js plan spec.json`, with
hits filled in as searches are run. Optional keys it reads:

  "profile": {"Field": "...", "Population": "...", ...}   the interview answers
  "chosen":  {"tier": "balanced", "range": "2021-2026", "reason": "..."}
  "prisma":  {"registers": 0, "automation_removed": 0, "other_removed": 0,
              "screened_excluded": 0, "sought": 0, "not_retrieved": 0,
              "assessed": 0, "excluded_reasons": {"Wrong population": 3},
              "included": 0, "included_reports": 0}

Any PRISMA number that is not known is printed as "to be completed", never guessed.
"""

import argparse
import json
import sys
import time
from xml.sax.saxutils import escape

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (Flowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                    TableStyle)
except ImportError:
    print("Error: reportlab is not installed. Run: pip install reportlab", file=sys.stderr)
    sys.exit(1)

SS = getSampleStyleSheet()
BODY = ParagraphStyle("body", parent=SS["BodyText"], fontSize=9, leading=12)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=7.5, leading=9.5)
MONO = ParagraphStyle("mono", parent=SMALL, fontName="Courier", fontSize=6.8, leading=8.5)
H1 = ParagraphStyle("h1", parent=SS["Heading1"], fontSize=16, textColor=colors.HexColor("#1F3864"))
H2 = ParagraphStyle("h2", parent=SS["Heading2"], fontSize=12, textColor=colors.HexColor("#1F3864"), spaceBefore=10)
BOX = ParagraphStyle("box", parent=BODY, fontSize=8, leading=10)
BAND = ParagraphStyle("band", parent=BODY, fontSize=8.5, textColor=colors.white, alignment=TA_CENTER,
                      fontName="Helvetica-Bold")
HEAD_BG = colors.HexColor("#1F3864")
GRID = colors.HexColor("#BFBFBF")
TBC = "to be completed"


def P(text, style=BODY):
    return Paragraph(escape(str(text)), style)


def n(v):
    return TBC if v is None else f"{v:,}" if isinstance(v, int) else str(v)


def hits_text(v):
    if v is None:
        return "not recorded"
    return f"{v:,}" if isinstance(v, int) else str(v)


def load(path, what):
    try:
        return json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"Error: cannot find the {what} file {path}")
    except json.JSONDecodeError as e:
        sys.exit(f"Error: {path} is not valid JSON ({e})")


def table(rows, widths, head=True, mono_col=None):
    data = []
    for i, r in enumerate(rows):
        cells = []
        for j, c in enumerate(r):
            if isinstance(c, Flowable):
                cells.append(c)
            elif i == 0 and head:
                cells.append(Paragraph(f"<b>{escape(str(c))}</b>", ParagraphStyle("th", parent=SMALL, textColor=colors.white)))
            else:
                cells.append(P(c, MONO if j == mono_col else SMALL))
        data.append(cells)
    t = Table(data, colWidths=widths, repeatRows=1 if head else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.4, GRID), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    if head:
        style.append(("BACKGROUND", (0, 0), (-1, 0), HEAD_BG))
    t.setStyle(TableStyle(style))
    return t


class PrismaFlow(Flowable):
    """PRISMA 2020 flow diagram for new reviews (databases and registers)."""

    def __init__(self, ident, removed, rows, included):
        super().__init__()
        self.ident, self.removed, self.rows, self.included = ident, removed, rows, included
        self.width, self.height = 515, 600

    def box(self, c, x, y, w, h, html):
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.white)
        c.rect(x, y, w, h, stroke=1, fill=1)
        p = Paragraph(html, BOX)
        _, ph = p.wrap(w - 8, h - 6)
        p.drawOn(c, x + 4, y + h - 4 - ph)

    def arrow(self, c, x1, y1, x2, y2):
        c.setStrokeColor(colors.black)
        c.line(x1, y1, x2, y2)
        size = 4
        p = c.beginPath()
        if x1 == x2:  # down
            p.moveTo(x2, y2); p.lineTo(x2 - size, y2 + size * 1.6); p.lineTo(x2 + size, y2 + size * 1.6)
        else:  # right
            p.moveTo(x2, y2); p.lineTo(x2 - size * 1.6, y2 - size); p.lineTo(x2 - size * 1.6, y2 + size)
        p.close()
        c.setFillColor(colors.black)
        c.drawPath(p, fill=1, stroke=0)

    def band(self, c, y, h, label):
        c.setFillColor(HEAD_BG)
        c.rect(0, y, 22, h, stroke=0, fill=1)
        c.saveState()
        c.translate(15, y + h / 2)
        c.rotate(90)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawCentredString(0, 0, label)
        c.restoreState()

    def draw(self):
        c = self.canv
        lx, lw, rx, rw = 32, 228, 290, 225
        top = self.height
        # Identification
        ih = 30 + 11 * max(len(self.ident), 1) + 12
        y = top - ih
        self.band(c, y, ih, "Identification")
        total = sum(v for v in self.ident.values() if isinstance(v, int)) if self.ident else None
        lines = "".join(f"<br/>&nbsp;&nbsp;{escape(k)} (n = {n(v)})" for k, v in self.ident.items())
        self.box(c, lx, y, lw, ih, f"<b>Records identified from:</b><br/>Databases (n = {n(total)}){lines}"
                                    f"<br/>Registers (n = {n(self.removed.get('registers'))})")
        self.box(c, rx, y, rw, ih, "<b>Records removed before screening:</b>"
                 f"<br/>Duplicate records removed (n = {n(self.removed.get('duplicates'))})"
                 f"<br/>Records marked as ineligible by automation tools (n = {n(self.removed.get('automation'))})"
                 f"<br/>Records removed for other reasons (n = {n(self.removed.get('other'))})")
        self.arrow(c, lx + lw, y + ih / 2, rx, y + ih / 2)
        # Screening rows
        gap, bh = 22, 46
        ys = y - gap
        start = None
        for i, (left, right) in enumerate(self.rows):
            rh = bh if i < 2 else max(bh, 28 + 11 * right.count("<br/>"))
            yy = ys - rh
            if start is None:
                start = ys
            self.arrow(c, lx + lw / 2, ys + gap, lx + lw / 2, ys)
            self.box(c, lx, yy, lw, rh, left)
            self.box(c, rx, yy, rw, rh, right)
            self.arrow(c, lx + lw, yy + rh / 2, rx, yy + rh / 2)
            ys = yy - gap
        self.band(c, ys + gap, start - ys - gap, "Screening")
        # Included
        ih2 = 46
        yi = ys - ih2
        self.arrow(c, lx + lw / 2, ys + gap, lx + lw / 2, ys)
        self.box(c, lx, yi, lw, ih2, self.included)
        self.band(c, yi, ih2, "Included")


def prisma(log, records):
    pr = log.get("prisma") or {}
    if records:
        ident = dict(records.get("identification") or {})
        dupes = records.get("duplicates_removed")
    else:
        ident, dupes = {}, None
        ch = log.get("chosen") or {}
        for r in log.get("runs", []):
            if r.get("tier") == ch.get("tier") and r.get("range") == ch.get("range") and r.get("database") in ("Scopus", "Web of Science"):
                ident[r["database"]] = r.get("hits")
    total = sum(v for v in ident.values() if isinstance(v, int)) if ident and all(isinstance(v, int) for v in ident.values()) else None
    removed = {"registers": pr.get("registers"), "duplicates": dupes, "automation": pr.get("automation_removed"),
               "other": pr.get("other_removed")}
    screened = None
    if total is not None and dupes is not None:
        screened = total - dupes - (pr.get("automation_removed") or 0) - (pr.get("other_removed") or 0)
    reasons = pr.get("excluded_reasons") or {}
    rlines = "".join(f"<br/>{escape(k)} (n = {n(v)})" for k, v in reasons.items()) or f"<br/>Reason 1 (n = {TBC})<br/>Reason 2 (n = {TBC})"
    rows = [
        (f"<b>Records screened</b><br/>(n = {n(screened)})", f"<b>Records excluded</b><br/>(n = {n(pr.get('screened_excluded'))})"),
        (f"<b>Reports sought for retrieval</b><br/>(n = {n(pr.get('sought'))})", f"<b>Reports not retrieved</b><br/>(n = {n(pr.get('not_retrieved'))})"),
        (f"<b>Reports assessed for eligibility</b><br/>(n = {n(pr.get('assessed'))})", f"<b>Reports excluded:</b>{rlines}"),
    ]
    included = (f"<b>Studies included in review</b><br/>(n = {n(pr.get('included'))})"
                f"<br/><b>Reports of included studies</b><br/>(n = {n(pr.get('included_reports'))})")
    return PrismaFlow(ident or {"(no database counts yet)": None}, removed, rows, included)


def build(log, records, manifest, out):
    story = []
    title = log.get("title") or "Search strategy"
    story += [Paragraph(escape(title), H1), P(f"Search strategy report, generated {time.strftime('%d %B %Y')}"), Spacer(1, 6)]

    prof = log.get("profile") or {}
    if prof:
        story.append(Paragraph("1. Search profile", H2))
        story.append(table([["Item", "Answer"]] + [[k, v if isinstance(v, str) else json.dumps(v)] for k, v in prof.items()], [130, 385]))

    story.append(Paragraph("2. Concepts and tiers", H2))
    story.append(P("Terms in one concept are joined with OR; concepts are joined with AND."))
    story.append(table([["#", "Concept", "Terms"]] + [[i + 1, c["name"], " OR ".join(c["terms"])] for i, c in enumerate(log.get("concepts", []))],
                       [18, 110, 387], mono_col=2))
    story.append(Spacer(1, 4))
    story.append(table([["Tier", "Concepts used"]] + [[t["name"], ", ".join(f"{k}. {log['concepts'][k - 1]['name']}" for k in t["concepts"])] for t in log.get("tiers", [])],
                       [70, 445]))

    story.append(Paragraph("3. Search strings and hit counts", H2))
    story.append(P("A count is shown only when it was read from the database, reported by the user, or returned by the "
                   "OpenAlex API. \"not recorded\" means nobody read a number; it is never estimated."))
    label = {"browser": "read in browser", "user": "reported by user", "OpenAlex API": "OpenAlex API (approx.)"}
    for rng in log.get("ranges", []):
        rows = [["Tier", "Database", "Search string", "Hits", "How recorded", "Date"]]
        for r in log.get("runs", []):
            if r.get("range") != rng:
                continue
            note = f" ({r['note']})" if r.get("note") and r.get("hits") is None else ""
            rows.append([r.get("tier", ""), r.get("database", ""), r.get("string", ""),
                         hits_text(r.get("hits")),
                         label.get(r.get("source"), r.get("source") or "") + note, r.get("date") or ""])
        story.append(Paragraph(f"Publication years {escape(rng)}", ParagraphStyle("h3", parent=BODY, fontName="Helvetica-Bold", spaceBefore=6)))
        story.append(table(rows, [44, 56, 241, 42, 78, 54], mono_col=2))
    ch = log.get("chosen")
    if ch:
        story.append(Spacer(1, 4))
        story.append(P(f"Search used for retrieval: tier \"{ch.get('tier')}\", {ch.get('range')}. {ch.get('reason', '')}"))

    story += [PageBreak(), Paragraph("4. PRISMA 2020 flow diagram", H2),
              P("Identification numbers come from the search exports. Screening and eligibility numbers come from the "
                "reviewer's own screening; any not yet supplied are marked \"to be completed\"."),
              Spacer(1, 8), prisma(log, records)]

    if manifest:
        items = manifest.get("items", [])
        story += [PageBreak(), Paragraph("5. Full-text retrieval", H2)]
        counts = {}
        for i in items:
            counts[i["status"]] = counts.get(i["status"], 0) + 1
        story.append(P("; ".join(f"{k}: {v}" for k, v in sorted(counts.items())) or "Nothing retrieved."))
        story.append(P("Downloaded files are legal open-access copies found through OpenAlex or repositories, or files the "
                       "user downloaded through their own library access. Retrieval happened before screening, so these "
                       "numbers are not the PRISMA \"reports sought\" figures."))
        got = [i for i in items if i["status"].startswith("downloaded")]
        if got:
            story.append(table([["File", "Title", "How"]] + [[i["file"], i["title"], "user" if "user" in i["status"] else "open access"] for i in got],
                               [170, 290, 55]))
        rest = [i for i in items if not i["status"].startswith("downloaded")]
        if rest:
            story.append(Spacer(1, 6))
            story.append(P("Not downloaded (fetch these through your library access):"))
            story.append(table([["Status", "Title", "Link"]] + [[i["status"], i["title"], ("https://doi.org/" + i["doi"]) if i.get("doi") else i.get("landing_url", "")] for i in rest],
                               [70, 285, 160]))

    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40,
                            title=title, author="research-search-string")
    doc.build(story, onLaterPages=footer, onFirstPage=footer)


def footer(c, doc):
    c.saveState()
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.grey)
    c.drawRightString(A4[0] - 40, 22, f"Page {doc.page}")
    c.restoreState()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--log", required=True)
    ap.add_argument("--records")
    ap.add_argument("--manifest")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    log = load(a.log, "search log")
    if "runs" not in log or "concepts" not in log:
        sys.exit("Error: the search log has no runs or concepts; make it with: node search_tool.js plan spec.json > search_log.json")
    build(log, load(a.records, "records") if a.records else None, load(a.manifest, "manifest") if a.manifest else None, a.out)
    print(f"Wrote {a.out}")


if __name__ == "__main__":
    main()
