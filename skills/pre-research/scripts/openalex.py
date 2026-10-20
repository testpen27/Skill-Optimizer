#!/usr/bin/env python3
"""OpenAlex counts, record lists, export import and open-access lookup.

Standard library only. Subcommands:

  count  LOG.json                 add an OpenAlex hit count for every tier x year
                                  range in the search log (made by `search_tool.js plan`)
  list   LOG.json --tier T --range 2021-2026 [--max 2000] --out records.json
                                  fetch the records of one search from OpenAlex
  import FILE [FILE ...] --out records.json
                                  read Scopus CSV and Web of Science exports
                                  (tab-delimited or plain text), merge, de-duplicate
  enrich records.json             look up open-access PDFs for every DOI

OpenAlex is free. Without a key all users on one network share a small daily
budget; set OPENALEX_API_KEY (free from https://openalex.org/settings/api) for
your own. OPENALEX_MAILTO is sent as a courtesy contact if set.

OpenAlex counts are an approximation of a Scopus or Web of Science search, not a
replacement: different coverage, and it searches title, abstract and keywords
with its own rules. The report labels them as such.
"""

import argparse
import csv
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = os.environ.get("OPENALEX_BASE", "https://api.openalex.org")
URL_LIMIT = 4000  # OpenAlex rejects request URLs over about 4 KB
SELECT = "id,doi,title,publication_year,authorships,open_access,best_oa_location,primary_location,abstract_inverted_index"


class Fail(Exception):
    pass


# ---------------------------------------------------------------- HTTP

def http_get(url, timeout=60):
    """GET a JSON document. Replaced in tests."""
    req = urllib.request.Request(url, headers={"User-Agent": "research-search-string/1.0"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:300]
            if e.code == 429 or e.code >= 500:
                time.sleep(2 ** attempt * 2)
                continue
            raise Fail(f"OpenAlex returned {e.code}: {body}")
        except urllib.error.URLError as e:
            if attempt == 3:
                raise Fail(f"cannot reach OpenAlex ({e.reason}). Check the internet connection.")
            time.sleep(2 ** attempt)
    raise Fail("OpenAlex kept returning errors (rate limit or outage). Try again later or set OPENALEX_API_KEY.")


def api_url(path, params):
    params = dict(params)
    if os.environ.get("OPENALEX_API_KEY"):
        params["api_key"] = os.environ["OPENALEX_API_KEY"]
    if os.environ.get("OPENALEX_MAILTO"):
        params["mailto"] = os.environ["OPENALEX_MAILTO"]
    return f"{API}{path}?{urllib.parse.urlencode(params, safe=':,|*?')}"


# ---------------------------------------------------------------- query conversion

def convert_term(term):
    """Turn one Scopus/WoS term into its OpenAlex form, or None with a reason."""
    t = term.strip()
    quoted = len(t) > 1 and t.startswith('"') and t.endswith('"')
    t = t.replace("$", "*")  # $ (zero or one character) has no equivalent; * is the superset
    words = re.split(r"[\s\-/]+", t.strip('"'))
    for w in words:
        if w.startswith(("*", "?")):
            return None, f"{term}: OpenAlex does not support a wildcard at the start of a word"
        m = re.search(r"[*?]", w)
        if m and m.start() < 3:
            return None, f"{term}: OpenAlex needs 3 letters before a wildcard"
    return (t if quoted else t), None


def openalex_query(concepts, tier_numbers):
    """Build the Boolean query for OpenAlex from concept blocks. Returns (query, uses_wildcards, notes)."""
    blocks, notes, wild = [], [], False
    for n in tier_numbers:
        terms = []
        for term in concepts[n - 1]["terms"]:
            conv, why = convert_term(term)
            if conv is None:
                notes.append(why)
                continue
            wild = wild or bool(re.search(r"[*?]", conv))
            terms.append(conv)
        if not terms:
            raise Fail(f"concept {n} has no terms OpenAlex can search")
        blocks.append("(" + " OR ".join(terms) + ")")
    return " AND ".join(blocks), wild, notes


def search_params(query, wild, y0, y1):
    # Wildcards only work in the exact (unstemmed) search; without them the
    # stemmed search is closer to how Scopus matches plurals.
    key = "search.title_abstract_keywords.exact" if wild else "search.title_abstract_keywords"
    return {key: query, "filter": f"publication_year:{y0}-{y1}"}


# ---------------------------------------------------------------- records

def norm_doi(doi):
    if not doi:
        return ""
    d = doi.strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    d = re.sub(r"^doi:\s*", "", d)
    return d


def norm_title(title):
    return re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()


def record_key(rec):
    return "doi:" + rec["doi"] if rec.get("doi") else f"title:{norm_title(rec.get('title'))}:{rec.get('year') or ''}"


def abstract_text(inv):
    """OpenAlex ships abstracts as {word: [positions]}; put the words back in order."""
    if not inv:
        return ""
    pos = sorted((p, word) for word, ps in inv.items() for p in ps)
    return " ".join(word for _, word in pos)


def from_openalex(w):
    loc = w.get("best_oa_location") or {}
    prim = w.get("primary_location") or {}
    src = prim.get("source") or {}
    oa = w.get("open_access") or {}
    return {
        "doi": norm_doi(w.get("doi")),
        "title": w.get("title") or "",
        "year": w.get("publication_year"),
        "authors": [a.get("author", {}).get("display_name", "") for a in w.get("authorships") or []],
        "abstract": abstract_text(w.get("abstract_inverted_index")),
        "venue": src.get("display_name") or "",
        "publisher": src.get("host_organization_name") or "",
        "landing_url": prim.get("landing_page_url") or (("https://doi.org/" + norm_doi(w["doi"])) if w.get("doi") else ""),
        "is_oa": bool(oa.get("is_oa")),
        "oa_status": oa.get("oa_status") or "",
        "pdf_url": loc.get("pdf_url") or "",
        "oa_url": oa.get("oa_url") or loc.get("landing_page_url") or "",
        "license": loc.get("license") or "",
        "openalex_id": w.get("id") or "",
        "sources": ["OpenAlex"],
    }


def merge(records):
    """De-duplicate by DOI, then by title + year. Keeps every source a record came from."""
    out, seen = [], {}
    for r in records:
        keys = [record_key(r)]
        if r.get("doi"):
            keys.append(f"title:{norm_title(r.get('title'))}:{r.get('year') or ''}")
        hit = next((seen[k] for k in keys if k in seen), None)
        if hit is None:
            out.append(r)
            for k in keys:
                seen[k] = r
            continue
        for s in r.get("sources", []):
            if s not in hit["sources"]:
                hit["sources"].append(s)
        for f in ("doi", "abstract", "venue", "publisher", "landing_url", "pdf_url", "oa_url", "license"):
            if not hit.get(f) and r.get(f):
                hit[f] = r[f]
        for k in keys:
            seen[k] = hit
    return out


# ---------------------------------------------------------------- export parsing

def read_text(path):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "utf-16", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise Fail(f"cannot read {path} as text")


def parse_scopus_csv(text):
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows or "Title" not in rows[0]:
        raise Fail("this does not look like a Scopus CSV export (no Title column)")
    out = []
    for r in rows:
        authors = r.get("Author full names") or r.get("Authors") or ""
        out.append({
            "doi": norm_doi(r.get("DOI")), "title": r.get("Title", "").strip(),
            "year": int(r["Year"]) if (r.get("Year") or "").strip().isdigit() else None,
            "authors": [a.strip() for a in re.split(r";", authors) if a.strip()],
            "abstract": "" if (r.get("Abstract") or "").strip() == "[No abstract available]" else (r.get("Abstract") or "").strip(),
            "venue": r.get("Source title", ""), "publisher": r.get("Publisher", ""),
            "landing_url": ("https://doi.org/" + norm_doi(r["DOI"])) if r.get("DOI") else r.get("Link", ""),
            "is_oa": None, "pdf_url": "", "oa_url": "", "license": "", "sources": ["Scopus"],
        })
    return out


def wos_record(tags):
    get = lambda k: " ".join(tags.get(k, [])).strip()
    year = get("PY")
    doi = get("DI")
    return {
        "doi": norm_doi(doi), "title": get("TI"), "year": int(year) if year.isdigit() else None,
        "authors": tags.get("AF") or tags.get("AU") or [], "abstract": get("AB"), "venue": get("SO"), "publisher": get("PU"),
        "landing_url": ("https://doi.org/" + norm_doi(doi)) if doi else "",
        "is_oa": None, "pdf_url": "", "oa_url": "", "license": "", "sources": ["Web of Science"],
    }


def parse_wos(text):
    lines = text.splitlines()
    if lines and lines[0].startswith("PT\t") or (lines and "\t" in lines[0] and "TI" in lines[0].split("\t")):
        head = lines[0].split("\t")
        out = []
        for line in lines[1:]:
            if not line.strip():
                continue
            vals = dict(zip(head, line.split("\t")))
            tags = {k: [v] for k, v in vals.items() if v}
            for k in ("AU", "AF"):
                if k in vals:
                    tags[k] = [a.strip() for a in vals[k].split(";") if a.strip()]
            out.append(wos_record(tags))
        return out
    # Plain-text format: two-letter tags, continuation lines indented, ER ends a record.
    out, tags, last = [], {}, None
    for line in lines:
        if line.startswith("ER"):
            if tags:
                out.append(wos_record(tags))
            tags, last = {}, None
        elif re.match(r"^[A-Z][A-Z0-9] ", line):
            last = line[:2]
            tags.setdefault(last, []).append(line[3:].strip())
        elif line.startswith("   ") and last:
            tags[last].append(line.strip())
    if not out:
        raise Fail("this does not look like a Web of Science export (tab-delimited or plain text)")
    return out


def parse_export(path):
    text = read_text(path)
    first = text.lstrip()[:200]
    if first.startswith("FN ") or first.startswith("PT") or first.startswith("PT\t"):
        return parse_wos(text)
    if "Title" in first and "," in first:
        return parse_scopus_csv(text)
    raise Fail(f"{path}: not a Scopus CSV or Web of Science export. Export Scopus as CSV and Web of Science as tab-delimited or plain text, with DOI included.")


# ---------------------------------------------------------------- commands

def load(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        raise Fail(f"cannot find {path}")
    except json.JSONDecodeError as e:
        raise Fail(f"{path} is not valid JSON ({e})")


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def tier_numbers(log, name):
    for t in log.get("tiers", []):
        if t["name"] == name:
            return t["concepts"]
    raise Fail(f'no tier "{name}" in the log; tiers are {[t["name"] for t in log.get("tiers", [])]}')


def cmd_count(args):
    log = load(args.log)
    if "concepts" not in log or "ranges" not in log:
        raise Fail("the log has no concepts or ranges; make it with: node search_tool.js plan spec.json > search_log.json")
    log["runs"] = [r for r in log.get("runs", []) if r.get("database") != "OpenAlex"]
    today = time.strftime("%Y-%m-%d")
    for rng in log["ranges"]:
        y0, y1 = rng.split("-")
        for t in log["tiers"]:
            row = {"tier": t["name"], "range": rng, "database": "OpenAlex", "string": "", "url": None,
                   "hits": None, "source": None, "date": today, "note": ""}
            try:
                q, wild, notes = openalex_query(log["concepts"], t["concepts"])
                row["string"] = q
                url = api_url("/works", dict(search_params(q, wild, y0, y1), **{"per-page": 1, "select": "id"}))
                if len(url) > URL_LIMIT:
                    row["note"] = "not counted: query is longer than OpenAlex's 4 KB limit"
                else:
                    row["hits"] = http_get(url)["meta"]["count"]
                    row["source"] = "OpenAlex API"
                    row["note"] = "; ".join(["approximation of the Scopus/WoS search"] + notes)
            except Fail as e:
                row["note"] = f"not counted: {e}"
            log["runs"].append(row)
            print(f"{rng} {t['name']:>9}: {row['hits'] if row['hits'] is not None else '-'}  {row['note']}")
    save(args.log, log)


def cmd_list(args):
    log = load(args.log)
    y0, y1 = args.range.split("-")
    q, wild, notes = openalex_query(log["concepts"], tier_numbers(log, args.tier))
    for n in notes:
        print("note:", n, file=sys.stderr)
    params = dict(search_params(q, wild, y0, y1), **{"per-page": 200, "select": SELECT, "cursor": "*"})
    recs = []
    while len(recs) < args.max:
        url = api_url("/works", params)
        if len(url) > URL_LIMIT:
            raise Fail("query is longer than OpenAlex's 4 KB limit; use a narrower tier or import the Scopus/WoS export instead")
        page = http_get(url)
        recs += [from_openalex(w) for w in page.get("results", [])]
        cursor = page.get("meta", {}).get("next_cursor")
        if not cursor or not page.get("results"):
            break
        params["cursor"] = cursor
    recs = merge(recs[: args.max])
    out = {"records": recs, "identification": {"OpenAlex": len(recs)}, "duplicates_removed": 0}
    save(args.out, out)
    print(f"{len(recs)} records from OpenAlex ({args.tier}, {args.range}) -> {args.out}")


def cmd_import(args):
    allrecs, ident = [], {}
    for path in args.files:
        recs = parse_export(path)
        src = recs[0]["sources"][0] if recs else "unknown"
        ident[src] = ident.get(src, 0) + len(recs)
        allrecs += recs
        print(f"{path}: {len(recs)} records from {src}")
    merged = merge(allrecs)
    dupes = len(allrecs) - len(merged)
    save(args.out, {"records": merged, "identification": ident, "duplicates_removed": dupes})
    no_doi = sum(1 for r in merged if not r["doi"])
    print(f"{len(merged)} unique records ({dupes} duplicates removed; {no_doi} without a DOI) -> {args.out}")


def cmd_enrich(args):
    data = load(args.records)
    recs = data["records"]
    todo = [r for r in recs if r.get("doi") and r.get("is_oa") is None]
    found = 0
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        url = api_url("/works", {"filter": "doi:" + "|".join(r["doi"] for r in batch), "per-page": 50, "select": SELECT})
        got = {norm_doi(w.get("doi")): from_openalex(w) for w in http_get(url).get("results", [])}
        for r in batch:
            g = got.get(r["doi"])
            if not g:
                r["is_oa"] = False
                r["note"] = "not in OpenAlex"
                continue
            for f in ("is_oa", "oa_status", "pdf_url", "oa_url", "license", "openalex_id"):
                r[f] = g[f]
            for f in ("publisher", "venue", "landing_url", "abstract"):
                r[f] = r.get(f) or g[f]
            found += bool(g["is_oa"])
    save(args.records, data)
    print(f"checked {len(todo)} DOIs; {found} have a free legal copy")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("count"); p.add_argument("log"); p.set_defaults(fn=cmd_count)
    p = sub.add_parser("list"); p.add_argument("log"); p.add_argument("--tier", required=True)
    p.add_argument("--range", required=True); p.add_argument("--max", type=int, default=2000)
    p.add_argument("--out", required=True); p.set_defaults(fn=cmd_list)
    p = sub.add_parser("import"); p.add_argument("files", nargs="+"); p.add_argument("--out", required=True)
    p.set_defaults(fn=cmd_import)
    p = sub.add_parser("enrich"); p.add_argument("records"); p.set_defaults(fn=cmd_enrich)
    args = ap.parse_args(argv)
    try:
        args.fn(args)
    except Fail as e:
        print("Error:", e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
