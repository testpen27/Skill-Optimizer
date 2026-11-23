"""Shared helpers for the research-matrix scripts: APA 7 author formatting,
sorting, robust loading of saved web responses, and PDF page furniture."""

import json
import re
import sys
import unicodedata
from xml.sax.saxutils import escape  # noqa: F401  (re-exported)


# ---------------------------------------------------------------- APA 7 -----

def initials(given):
    """'Zeynep' -> 'Z.'   'Jean-Pierre' -> 'J.-P.'   'Anna B.' -> 'A. B.'"""
    out = []
    for word in (given or "").replace(".", ". ").split():
        parts = [p for p in word.split("-") if p.strip(". ")]
        if not parts:
            continue
        out.append("-".join(p.strip(". ")[0].upper() + "." for p in parts))
    return " ".join(out)


def author_string(family, given):
    """One author as APA 7 prints it in a reference list: 'Tufekci, Z.'"""
    family = (family or "").strip()
    ini = initials(given)
    return f"{family}, {ini}" if ini else family


def apa_authors(authors):
    """Join author strings the APA 7 way (up to 20 names; 21+ gets an ellipsis)."""
    a = [x.strip() for x in authors if x and x.strip()]
    if not a:
        return ""
    if len(a) == 1:
        return a[0]
    if len(a) == 2:
        return f"{a[0]}, & {a[1]}"
    if len(a) <= 20:
        return ", ".join(a[:-1]) + f", & {a[-1]}"
    return ", ".join(a[:19]) + f", . . . {a[-1]}"


def fold(s):
    """Lowercase, accent-free, punctuation-free form used to compare and sort."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^\w\s]", " ", s.casefold())
    return re.sub(r"\s+", " ", s).strip()


def first_family(author):
    return (author or "").split(",")[0].strip()


def sort_key(paper):
    a = (paper.get("authors") or [""])[0]
    return (fold(first_family(a)), str(paper.get("year") or ""), fold(paper.get("title") or ""))


def dash(pages):
    """APA prints page ranges with an en dash."""
    return re.sub(r"\s*[-‐-‒−]\s*", "–", (pages or "").strip())


def clean_doi(doi):
    d = (doi or "").strip()
    d = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", d, flags=re.I)
    return d


# ------------------------------------------------- saved web responses ------

def load_json_loose(text):
    """Read JSON from a saved response: plain JSON, a Firecrawl wrapper
    ({"markdown": "..."}), or JSON inside a ```json fence."""
    text = text.strip()
    for _ in range(3):
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            i, j = text.find("{"), text.rfind("}")
            if i < 0 or j <= i:
                return None
            try:
                data = json.loads(text[i:j + 1])
            except json.JSONDecodeError:
                return None
        if isinstance(data, dict) and "markdown" in data and "message" not in data:
            text = data["markdown"]
            continue
        return data
    return None


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


# ------------------------------------------------------------- PDF ----------

def pdf_parts():
    """Import reportlab lazily so --check works without it."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate,
                                        Spacer, Table, TableStyle)
    except ImportError:
        die("Error: reportlab is not installed. Run: pip install reportlab")
    return dict(colors=colors, A4=A4, landscape=landscape, ParagraphStyle=ParagraphStyle,
                getSampleStyleSheet=getSampleStyleSheet, inch=inch, KeepTogether=KeepTogether,
                Paragraph=Paragraph, SimpleDocTemplate=SimpleDocTemplate, Spacer=Spacer,
                Table=Table, TableStyle=TableStyle)


def make_styles(p):
    ss = p["getSampleStyleSheet"]()
    PS, colors = p["ParagraphStyle"], p["colors"]
    cell = PS("cell", parent=ss["BodyText"], fontSize=7, leading=8.6)
    head = PS("head", parent=cell, textColor=colors.white, fontName="Helvetica-Bold")
    h1 = PS("h1", parent=ss["Heading1"], fontSize=14, textColor=colors.HexColor("#1F3864"))
    body = PS("body", parent=ss["BodyText"], fontSize=9, leading=12)
    return cell, head, h1, body


def build_doc(p, out, story, title, margin):
    colors = p["colors"]
    page = p["landscape"](p["A4"])

    def footer(c, doc):
        c.saveState()
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.grey)
        c.drawRightString(page[0] - margin, 14, f"Page {doc.page}")
        c.restoreState()

    doc = p["SimpleDocTemplate"](out, pagesize=page, leftMargin=margin, rightMargin=margin,
                                 topMargin=margin, bottomMargin=margin, title=title)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def table_style(p, header_rows=1):
    colors = p["colors"]
    return p["TableStyle"]([
        ("BACKGROUND", (0, 0), (-1, header_rows - 1), colors.HexColor("#1F3864")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BFBFBF")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, header_rows), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ])
