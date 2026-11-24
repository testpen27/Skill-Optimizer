"""Shared helpers for the research-matrix scripts: APA 7 author formatting,
sorting, robust loading of saved web responses, and Excel styling."""

import json
import re
import sys
import unicodedata
from xml.sax.saxutils import escape  # noqa: F401  (re-exported)


# ---------------------------------------------------------------- APA 7 -----

def initials(given):
    """'Zeynep' -> 'Z.'   'Jean-Pierre' -> 'J.-P.'   'Anna B.' -> 'A. B.'"""
    out = []
    # A dot before a hyphen stays attached ("J.-P."); any other dot ends the initial.
    for word in re.sub(r"\.(?!-)", ". ", given or "").split():
        # Crossref often gives bare initials as one capitalised token ("AJ", "SH"): one initial per letter.
        if word.isalpha() and word.isupper() and 2 <= len(word) <= 3:
            out.extend(ch + "." for ch in word)
            continue
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


def given_part(author):
    return (author or "").partition(",")[2].strip()


def year_num(paper):
    """Year for ordering: APA 7 puts 'n.d.' works first."""
    y = str(paper.get("year") or "").strip()
    return int(y) if y.isdigit() else -1


def sort_key(paper):
    """APA 7 reference-list order: first author's family name, then initials;
    a single-author work before multi-author works with the same first author;
    then the remaining authors, the year (n.d. first) and the title."""
    au = paper.get("authors") or [""]
    return (fold(first_family(au[0])), fold(given_part(au[0])), len(au) > 1,
            fold(" ".join(au[1:])), year_num(paper), fold(paper.get("title") or ""))


def dash(pages):
    """APA prints page ranges with an en dash."""
    return re.sub(r"\s*[-‐-‒−]\s*", "–", (pages or "").strip())


def clean_doi(doi):
    d = (doi or "").strip()
    d = re.sub(r"^(?:https?://)?(?:www\.|dx\.)?doi\.org/|^doi:\s*", "", d, flags=re.I)
    return d


def resolve_paper(key, sources):
    """Match a synthesis/concept key to a source by P-code, id or DOI. -> code or None.
    P-codes renumber when the LRM changes, so ids and DOIs are the safe keys."""
    k = str(key or "").strip()
    for s in sources:
        if k.upper() == s["code"].upper():
            return s["code"]
    kd = fold(clean_doi(k))
    for s in sources:
        for ident in (s.get("id"), s.get("doi")):
            if ident and (k == ident or kd == fold(clean_doi(ident))):
                return s["code"]
    return None


def is_pcode(key):
    return bool(re.fullmatch(r"[Pp]\d{2,}", str(key or "").strip()))


# --------------------------------------------- text from PDFs and the web -----

_ILLEGAL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f]")
_TAG = re.compile(r"<[^>]+>")


def clean_text(s):
    """Drop control characters that PDF text brings and Excel cannot store."""
    return _ILLEGAL.sub("", s) if isinstance(s, str) else s


def scrub(obj):
    """clean_text applied to every string in a loaded JSON structure."""
    if isinstance(obj, str):
        return clean_text(obj)
    if isinstance(obj, list):
        return [scrub(x) for x in obj]
    if isinstance(obj, dict):
        return {k: scrub(v) for k, v in obj.items()}
    return obj


def strip_markup(s):
    """Crossref titles carry JATS/HTML tags and entities ('<i>Drosophila</i>', '&amp;')."""
    import html
    return html.unescape(_TAG.sub("", s or "")).strip()


def protect_text(ws, skip=()):
    """Make sure text that starts with '=' stays text. openpyxl would store it as a
    live formula, so text pasted from a paper could run in the user's Excel.
    `skip` holds (row, column) cells that are deliberate formulas."""
    for row in ws.iter_rows():
        for c in row:
            if (c.row, c.column) in skip:
                continue
            if isinstance(c.value, str) and c.value.startswith("="):
                c.data_type = "s"


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


# ------------------------------------------------------------ Excel --------

FONT = "Arial"
NAVY = "1F3864"
GREY_FILL = "F2F2F2"
AMBER_FILL = "FFF2CC"
RED = "C00000"


def xl():
    """Import openpyxl lazily so --check works without it."""
    try:
        import openpyxl
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    except ImportError:
        die("Error: openpyxl is not installed. Run: pip install openpyxl")
    return openpyxl, Alignment, Border, Font, PatternFill, Side


def open_workbook(path):
    """Load the workbook at path, or start a new one (its default sheet removed)."""
    import os
    openpyxl = xl()[0]
    if os.path.exists(path):
        return openpyxl.load_workbook(path, rich_text=True)
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    return wb


def fresh_sheet(wb, name, index=None):
    """Create sheet `name`, replacing any sheet of that name (so a rebuild is clean)."""
    if name in wb.sheetnames:
        del wb[name]
    ws = wb.create_sheet(name, index)
    return ws


def style_header(ws, row, ncols, height=None):
    _, Alignment, Border, Font, PatternFill, Side = xl()
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="left")
    if height:
        ws.row_dimensions[row].height = height


def style_body(ws, first_row, last_row, ncols, size=9):
    _, Alignment, Border, Font, PatternFill, Side = xl()
    thin = Side(style="thin", color="BFBFBF")
    for r in range(first_row, last_row + 1):
        for c in range(1, ncols + 1):
            cell = ws.cell(row=r, column=c)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)
            if cell.font is None or cell.font.name != FONT:
                cell.font = Font(name=FONT, size=size)
            if (r - first_row) % 2 == 1:
                cell.fill = PatternFill("solid", fgColor=GREY_FILL)


def set_widths(ws, widths):
    from openpyxl.utils import get_column_letter
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def print_setup(ws):
    """Landscape, one page wide, header row repeated: prints legibly from Excel."""
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:1"
    ws.page_margins.left = ws.page_margins.right = 0.4


def save(wb, path, order=None):
    """Save, putting the sheets named in `order` first."""
    if order:
        names = [n for n in order if n in wb.sheetnames] + [n for n in wb.sheetnames if n not in order]
        wb._sheets = [wb[n] for n in names]
    wb.active = 0
    wb.save(path)
