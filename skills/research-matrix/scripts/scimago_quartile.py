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

Nothing is guessed. If the journal, year or category is not found it prints
"Unranked/Unavailable" and says why on stderr.
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request

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
    """Return (cell, note). note says when the year had to be adjusted."""
    cats = {c: ys for c, ys in table.items() if not category or fold(category) in fold(c)}
    if not cats:
        return "Unranked/Unavailable", (f"no category containing {category!r}; "
                                        f"categories are: {', '.join(sorted(table))}")
    latest = max(max(ys) for ys in cats.values())
    use = year if isinstance(year, int) else latest
    note = None
    if use > latest:
        note, use = f"{year} is newer than Scimago's data; used {latest}", latest
    parts = []
    for cat in sorted(cats, key=lambda c: (cats[c].get(use, "Q9"), c)):
        q = cats[cat].get(use)
        if q:
            parts.append(f"{q} (SJR {use}, {cat})")
    if not parts:
        return "Unranked/Unavailable", f"no quartile for {use} in {', '.join(sorted(cats))}"
    return " / ".join(parts), note


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
            print("Unranked/Unavailable")
            print(f"cannot reach Scimago ({e}); scrape the page another way and pass --journal-page",
                  file=sys.stderr)
            return 0

    title, table = parse_journal(text)
    if not table:
        print("Unranked/Unavailable")
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
