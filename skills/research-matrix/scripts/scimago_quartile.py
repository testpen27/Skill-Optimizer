#!/usr/bin/env python3
"""Look up a journal's SJR quartile on Scimago (scimagojr.com) by ISSN.

    python3 scimago_quartile.py --issn 0002-7642 --year 2013 [--category Education]
    python3 scimago_quartile.py --journal-page page.md --year 2013      # offline

Scimago lists a quartile for every subject category and year, and the same
journal can be Q1 in one category and Q2 in another. This prints the cell text
for the LRM, for the chosen year (use the paper's publication year; the latest
year available is used, and said so, if the paper is newer than the data).

  --issn         the journal's ISSN (print or electronic; from Crossref).
  --journal-page a saved copy of the Scimago journal page (the page whose
                 URL looks like journalsearch.php?q=<id>&tip=sid), e.g. from a
                 Firecrawl scrape. Use this where the network is blocked.
  --search-page  a saved copy of journalsearch.php?q=<issn>&tip=iss, used to
                 find the journal id when only the ISSN is known.
  --category     only report categories whose name contains this text
                 (the user's field, e.g. Education).

Nothing is guessed. Order of answers:
  1. a category that matches --category (the user's field), as it is;
  2. if there is none for that year, the journal's best quartile that year with its
     category named and "not in <field>", for example
     "Q1 (SJR 2025, Health Informatics; not in Education)";
  3. "Unranked/Unavailable" if Scimago has no such journal or no quartile that year;
  4. "Unavailable (Scimago page not retrieved)" if the page could not be fetched or has
     no quartile table: that is a failed lookup, not a ranking.
Each case says why on stderr.
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request

import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from common import fold, read_text

UA = "research-matrix/1.0 (academic quartile lookup)"
BASE = "https://www.scimagojr.com/journalsearch.php"
ROW = re.compile(r"^\|\s*(.+?)\s*\|\s*(\d{4})\s*\|\s*(Q[1-4])\s*\|\s*$", re.M)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def journal_id(search_text):
    m = re.search(r"journalsearch\.php\?q=(\d+)&(?:amp;)?tip=sid", search_text)
    return m.group(1) if m else None


def parse_journal(text):
    """-> (title, {category: {year: 'Q1'}})"""
    m = re.search(r"^#\s+(.+)$", text, re.M)
    title = m.group(1).strip() if m else None
    table = {}
    for cat, year, q in ROW.findall(text):
        table.setdefault(cat, {})[int(year)] = q
    return title, table


def cell_text(table, year, category=None):
    """Return (cell, note). note says when the year had to be adjusted or the field did not match.

    1. A category that matches the user's field is reported as it is (the most defensible answer).
    2. If the journal has no such category, or none with a quartile in that year, the journal's
       BEST quartile that year is reported with its category named and "not in <field>".
    3. "Unranked/Unavailable" only when the journal has no quartile at all in that year."""
    latest = max((max(ys) for ys in table.values() if ys), default=None)
    if latest is None:
        return "Unranked/Unavailable", "the page holds no quartile data"
    use = year if isinstance(year, int) else latest
    note = None
    if use > latest:  # newer than anything Scimago has for this journal in any category
        note, use = f"{year} is newer than Scimago's data; used {latest}", latest
    cats = {c: ys for c, ys in table.items() if not category or fold(category) in fold(c)}
    parts = []
    for cat in sorted(cats, key=lambda c: (cats[c].get(use, "Q9"), c)):
        q = cats[cat].get(use)
        if q:
            parts.append(f"{q} (SJR {use}, {cat})")
    if parts:
        return " / ".join(parts), note
    # The field did not match: fall back to the journal's best quartile that year, named.
    ranked = {c: ys[use] for c, ys in table.items() if ys.get(use)}
    if not ranked:
        return "Unranked/Unavailable", f"no quartile for {use} in any category of this journal"
    best = min(ranked.values())
    names = sorted(c for c, q in ranked.items() if q == best)
    why = (f"not in {category}" if not cats else f"{category} not ranked in {use}")
    extra = f"; {len(names) - 1} other categor{'y' if len(names) == 2 else 'ies'} also {best}" if len(names) > 1 else ""
    n = (f"no category containing {category!r} had a quartile for {use}; reported the journal's best quartile, "
         f"in {names[0]}") + (f". Categories: {', '.join(sorted(table))}" if not cats else "")
    return f"{best} (SJR {use}, {names[0]}{extra}; {why})", (note + "; " if note else "") + n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--issn")
    ap.add_argument("--year", type=int)
    ap.add_argument("--category")
    ap.add_argument("--journal-page")
    ap.add_argument("--search-page")
    ap.add_argument("--json", action="store_true", help="print all categories and years as JSON")
    a = ap.parse_args(argv)

    if a.journal_page:
        text = read_text(a.journal_page)
    else:
        if not a.issn:
            ap.error("give --issn, or --journal-page for a saved page")
        issn = re.sub(r"[^0-9Xx]", "", a.issn).upper()
        try:
            if a.search_page:
                found = journal_id(read_text(a.search_page))
            else:
                found = journal_id(get(f"{BASE}?q={issn}&tip=iss"))
            if not found:
                print("Unranked/Unavailable")
                print(f"Scimago has no journal for ISSN {a.issn}", file=sys.stderr)
                return 0
            text = get(f"{BASE}?q={found}&tip=sid&clean=0")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            print("Unavailable (Scimago page not retrieved)")
            print(f"cannot reach Scimago ({e}); scrape the page another way and pass --journal-page",
                  file=sys.stderr)
            return 0

    title, table = parse_journal(text)
    if not table:
        print("Unavailable (Scimago page not retrieved)")
        print("no Category / Year / Quartile table found on that page", file=sys.stderr)
        return 0
    if a.json:
        print(json.dumps({"journal": title, "quartiles": table}, indent=2))
        return 0
    cell, note = cell_text(table, a.year, a.category)
    print(cell)
    if note:
        print(f"note: {note}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
