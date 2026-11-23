#!/usr/bin/env python3
"""Build the Literature Review Matrix (LRM) PDF from lrm.json.

    python3 build_lrm.py lrm.json --out LRM.pdf [--check]

Columns, left to right: Code | Type | Authors | Title | Introduction |
Methodology | Theory | Results | Discussion | Quartile | Access.
Rows are sorted A-Z by the first author's family name and coded P01, P02, ...
in that order (add a paper and the codes renumber).

lrm.json:
{
  "title": "Research title", "field": "Education", "years": "2021-2026",
  "papers": [
    {"authors": ["Tan, A. B.", "Lee, C. D."], "year": 2024,
     "title": "Paper title in sentence case",
     "journal": "Journal of Examples", "volume": "12", "issue": "3",
     "pages": "101-118", "doi": "10.1000/xyz123", "issn": "1234-5678",
     "type": "Quantitative", "access": "Free",
     "quartile": "Q1 (SJR 2024, Education)",
     "introduction": "...", "methodology": "...", "theory": "...",
     "results": "...", "discussion": "...",
     "crossref": "verified"}
  ],
  "synthesis": "A few sentences: recurring theories, dominant methods, quartile balance, gaps."
}

Every cell must come from something actually retrieved. Empty cells print as
"Not retrieved"; a missing theory prints as "Not explicitly stated".
"crossref" is "verified" | "mismatch" | "unchecked" (written by crossref_check.py).
--check validates the file and prints problems and style warnings without
building the PDF. Needs reportlab (`pip install reportlab`).
"""

import argparse
import json
import re
import sys

from common import (apa_authors, build_doc, clean_doi, dash, escape, make_styles, pdf_parts,
                    sort_key, table_style)

# A note in brackets may itself hold one bracket pair: "Social Sciences (miscellaneous)".
_NOTE = r"\((?:[^()]|\([^()]*\))*\)"
QUARTILE_OK = re.compile(rf"^(Q[1-4](\s*{_NOTE})?(\s*/\s*Q[1-4](\s*{_NOTE})?)*"
                         r"|N/A \(thesis/preprint/conference\)|Unranked/Unavailable)$")
TYPES = {"Quantitative", "Qualitative", "Mixed-methods", "Theoretical/Review"}
ACCESS = {"Free", "Paid", "Unclear"}
CROSSREF = {"verified", "mismatch", "unchecked"}
TEXT_FIELDS = ["introduction", "methodology", "theory", "results", "discussion"]
# Soft length limits (words). Over the limit is a warning, not an error: the
# aim is cells a person can read, not a wall of text.
WORD_LIMITS = {"introduction": 40, "methodology": 50, "theory": 25, "results": 60, "discussion": 60}
FIRST_PERSON = re.compile(r"\b(I|my|me|we|our|us)\b")


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
        if (p.get("quartile") or "").startswith("Q") and not p.get("issn"):
            out.append(f"{tag}: has a quartile but no issn on record to trace it to")
    if len(papers) >= 4:
        for f in TEXT_FIELDS:
            starts = [" ".join((p.get(f) or "").split()[:2]).lower() for p in papers if p.get(f)]
            if starts:
                top = max(set(starts), key=starts.count)
                if starts.count(top) / len(starts) > 0.5:
                    out.append(f'{f}: {starts.count(top)} of {len(starts)} cells start with "{top}"; '
                               f"vary the wording (the authors, the researchers, the study, the team)")
    return out


def ordered(data):
    papers = sorted(data["papers"], key=sort_key)
    return [(f"P{i:02d}", p) for i, p in enumerate(papers, 1)]


def citation_cells(p):
    authors = apa_authors(p.get("authors") or [])
    year = p.get("year") or "n.d."
    authors_cell = escape(f"{authors} ({year})")

    title = (p.get("title") or "").strip()
    title = title if title.endswith((".", "?", "!")) else title + "."
    lines = [escape(title)]
    j = (p.get("journal") or "").strip()
    if j:
        src = f"<i>{escape(j)}"
        if p.get("volume"):
            src += f", {escape(str(p['volume']))}"
        src += "</i>"
        if p.get("issue"):
            src += f"({escape(str(p['issue']))})"
        if p.get("pages"):
            src += f", {escape(dash(str(p['pages'])))}"
        lines.append(src + ".")
    doi = clean_doi(p.get("doi"))
    if doi:
        url = f"https://doi.org/{doi}"
        lines.append(f"<link href='{escape(url, {chr(39): '&apos;'})}' color='#0563C1'>{escape(url)}</link>")
    return authors_cell, "<br/>".join(lines)


def build(data, out):
    pp = pdf_parts()
    Paragraph, Spacer, Table = pp["Paragraph"], pp["Spacer"], pp["Table"]
    cell, head, h1, body = make_styles(pp)
    margin = 0.4 * pp["inch"]
    page = pp["landscape"](pp["A4"])
    frame_w = page[0] - 2 * margin
    # Short labels narrow, text columns wide; scaled to the frame so the table
    # can never be wider than the page.
    rel = [3.6, 5.4, 7.8, 12.6, 11.3, 12.3, 8.5, 12.3, 12.3, 7, 3.9]
    widths = [frame_w * r / sum(rel) for r in rel]

    cols = ["Code", "Type", "Authors", "Title", "Introduction", "Methodology", "Theory",
            "Results", "Discussion", "Quartile", "Access"]
    rows = [[Paragraph(c, head) for c in cols]]
    # Let narrow label cells wrap at a slash ("Unranked/ Unavailable"), but keep "N/A" whole.
    label = lambda v: re.sub(r"(?<!N)/(?!A\b)", "/ ", escape(v or ""))
    unverified = []
    for code, p in ordered(data):
        authors_cell, title_cell = citation_cells(p)
        if p.get("crossref", "unchecked") != "verified":
            unverified.append(code)
        vals = [code, label(p.get("type")), authors_cell, title_cell]
        for f in TEXT_FIELDS:
            empty = "Not explicitly stated" if f == "theory" else "Not retrieved"
            vals.append(escape((p.get(f) or "").strip() or empty))
        vals += [label(p.get("quartile")), escape(p.get("access") or "")]
        rows.append([Paragraph(v, cell) for v in vals])

    t = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(table_style(pp))
    n = len(data["papers"])
    story = [Paragraph(escape(data.get("title") or "Literature Review Matrix"), h1)]
    meta = " | ".join(x for x in [f"Field: {data['field']}" if data.get("field") else "",
                                  f"Years: {data['years']}" if data.get("years") else "",
                                  f"{n} papers, A-Z by first author"] if x)
    story += [Paragraph(escape(meta), body), Spacer(1, 6), t, Spacer(1, 6)]
    foot = ("Citations checked against Crossref: "
            f"{n - len(unverified)} of {n}." + (f" Not checked: {', '.join(unverified)}." if unverified else "")
            + " Quartiles are SJR (Scimago) quartiles for the year and subject area shown.")
    story.append(Paragraph(escape(foot), ParagraphStyleSmall(pp)))
    if data.get("synthesis"):
        story += [Spacer(1, 10), Paragraph("<b>Synthesis</b>", body), Paragraph(escape(data["synthesis"]), body)]
    build_doc(pp, out, story, data.get("title") or "LRM", margin)


def ParagraphStyleSmall(pp):
    return pp["ParagraphStyle"]("small", parent=pp["getSampleStyleSheet"]()["BodyText"],
                                fontSize=7, leading=9, textColor=pp["colors"].grey)


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
    warns = warnings_in(data)
    if warns:
        print("Warnings (the PDF still builds):\n- " + "\n- ".join(warns), file=sys.stderr)
    if a.check:
        print(f"OK: {len(data['papers'])} papers")
        return 0
    if not a.out:
        print("Error: give --out LRM.pdf", file=sys.stderr)
        return 1
    build(data, a.out)
    print(f"Wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
