#!/usr/bin/env python3
"""Split a Turnitin AI Writing Report PDF into flagged and unflagged sentences.

The report marks the sentences its detector scored as likely AI by drawing a
coloured box behind them. Reading those boxes by eye across ten pages is slow
and easy to get wrong, and the useful question is comparative: what do the
flagged sentences have in common that the unflagged ones lack? This script
recovers the two sets so that comparison can be made on the actual text.

Usage:
    python checker_report.py REPORT.pdf            # readable summary
    python checker_report.py REPORT.pdf --json     # machine-readable
    python checker_report.py --self-test

Needs PyMuPDF (`pip install pymupdf`). The report itself is the student's
work: read it, don't copy it anywhere it wasn't asked to go.

What it can and cannot tell you:
- It reads the highlights the report drew. It does not re-score anything,
  and it cannot say why the detector flagged a sentence; Turnitin states its
  model is a trained classifier whose individual predictions are not
  explainable feature by feature.
- Tables, headings and the reference list are excluded, as Turnitin excludes
  them from scoring. Words inside tables are counted separately so they do
  not pose as "unflagged prose".
- Highlights are grouped by colour. Since August 2026 Turnitin draws one
  colour (cyan). Older reports used a second colour (purple) for text it
  judged AI-generated and then AI-paraphrased; any second colour is reported
  separately rather than guessed at.
"""

import argparse
import json
import re
import sys

CYAN = (0.32, 0.78, 0.86)
BOILERPLATE = re.compile(
    r"^(Page \d+ of \d+ - .*|Submission ID.*|trn:oid:.*|turnitin)$", re.I
)
SCORE = re.compile(r"(\*|\d{1,3})%\s+detected as AI", re.I)
SENT_END = re.compile(r"[.?!]['\")\]]*$")


def _is_highlight(fill, rect):
    """A highlight is a saturated fill about one text line tall.

    Rules out hyperlink underlines (1pt tall), table-header shading (pale)
    and grid lines (grey).
    """
    if not fill or not (6 <= rect.height <= 22) or rect.width < 3:
        return False
    return max(fill) - min(fill) >= 0.3


def _colour_name(fill):
    if all(abs(a - b) < 0.06 for a, b in zip(fill, CYAN)):
        return "cyan (AI-generated)"
    return "other " + "#%02x%02x%02x" % tuple(int(c * 255) for c in fill)


def extract(path):
    import pymupdf

    doc = pymupdf.open(path)
    header_text = "\n".join(doc[i].get_text() for i in range(min(2, doc.page_count)))
    m = SCORE.search(header_text)
    score = m.group(1) + "%" if m else None

    # Running headers and footers of the submission itself (course name,
    # page numbers) repeat on most pages; they are not prose.
    from collections import Counter
    seen = Counter()
    for page in doc:
        seen.update({l.strip() for l in page.get_text().splitlines() if l.strip()})
    running = {l for l, n in seen.items() if n >= max(3, doc.page_count // 2)}

    stream = []          # (word, colour or None)
    table_words = 0
    in_references = False
    for page in doc:
        text = page.get_text()
        if "AI Writing Submission" not in text and "detected as AI" not in text:
            if page.number < 2:
                continue  # cover page
        if "detected as AI" in text and page.number < 2:
            continue      # overview page
        hl = []
        for d in page.get_drawings():
            f = d.get("fill")
            if f and _is_highlight(f, d["rect"]):
                hl.append((d["rect"], tuple(round(c, 2) for c in f)))
        try:
            tables = [pymupdf.Rect(t.bbox) for t in page.find_tables().tables]
        except Exception:
            tables = []
        lines = {}
        for x0, y0, x1, y1, w, b, ln, wn in page.get_text("words"):
            lines.setdefault((b, ln), []).append((x0, y0, x1, y1, w))
        for key in sorted(lines):
            words = lines[key]
            line_text = " ".join(w[4] for w in words).strip()
            if (BOILERPLATE.match(line_text) or re.fullmatch(r"\d+", line_text)
                    or line_text in running):
                continue
            if re.fullmatch(r"References|Reference list|Bibliography", line_text, re.I):
                in_references = True
            if in_references:
                continue
            for x0, y0, x1, y1, w in words:
                r = pymupdf.Rect(x0, y0, x1, y1)
                c = pymupdf.Point((x0 + x1) / 2, (y0 + y1) / 2)
                if any(t.contains(c) for t in tables):
                    table_words += 1
                    continue
                colour = next((col for R, col in hl if R.contains(c)), None)
                stream.append((w, colour))

    sentences = []
    buf = []
    for w, colour in stream:
        buf.append((w, colour))
        if SENT_END.search(w) and len(buf) >= 4:
            sentences.append(buf)
            buf = []
    if buf:
        sentences.append(buf)

    out = []
    for s in sentences:
        cols = [c for _, c in s if c]
        flagged = len(cols) * 2 > len(s)
        colour = max(set(cols), key=cols.count) if flagged else None
        text = " ".join(w for w, _ in s)
        if len(s) < 6:  # headings and fragments that slipped through
            continue
        out.append({"text": text, "words": len(s), "flagged": flagged,
                    "colour": _colour_name(colour) if colour else None})
    return {"score": score, "sentences": out, "table_words_excluded": table_words}


def summarise(result):
    s = result["sentences"]
    flagged = [x for x in s if x["flagged"]]
    clean = [x for x in s if not x["flagged"]]
    lines = [f"Reported score: {result['score'] or 'not found'}",
             f"Prose sentences recovered: {len(s)} "
             f"({len(flagged)} highlighted, {len(clean)} not)",
             f"Words in tables, excluded: {result['table_words_excluded']}"]
    by_colour = {}
    for x in flagged:
        by_colour.setdefault(x["colour"], []).append(x)
    for colour, xs in by_colour.items():
        lines.append(f"\n## Highlighted: {colour} ({len(xs)})")
        lines += ["- " + x["text"] for x in xs]
    lines.append(f"\n## Not highlighted ({len(clean)})")
    lines += ["- " + x["text"] for x in clean]
    lines.append(
        "\nThis is a reading of the report's highlights, not a re-score. Compare "
        "the two lists for what the flagged sentences share; see "
        "references/ai-checkers.md for how to read the result.")
    return "\n".join(lines)


def self_test():
    import pymupdf

    doc = pymupdf.open()
    p = doc.new_page()
    p.insert_text((72, 60), "45% detected as AI")
    p = doc.new_page()
    p.insert_text((72, 40), "Page 2 of 2 - AI Writing Submission")
    flagged = "Innovation drives success in every modern market today."
    plain = "Our churn rose from 1.9% to 2.4% in Q3, which I did not expect."
    p.draw_rect(pymupdf.Rect(70, 92, 400, 104), color=None, fill=CYAN)
    p.insert_text((72, 102), flagged, fontsize=9)
    p.insert_text((72, 130), plain, fontsize=9)
    p.draw_rect(pymupdf.Rect(70, 150, 400, 151), color=None, fill=(0.02, 0.39, 0.76))
    path = "/tmp/_checker_report_selftest.pdf" if sys.platform != "win32" else "_selftest.pdf"
    doc.save(path)
    r = extract(path)
    checks = [
        ("score read", r["score"] == "45%"),
        ("two sentences", len(r["sentences"]) == 2),
        ("cyan sentence flagged", r["sentences"][0]["flagged"]
         and r["sentences"][0]["colour"].startswith("cyan")),
        ("plain sentence not flagged", not r["sentences"][1]["flagged"]),
    ]
    failed = 0
    for name, ok in checks:
        print(f"[{'ok' if ok else 'FAIL'}] {name}")
        failed += not ok
    print("\nAll checks passed." if not failed else f"\n{failed} check(s) failed.")
    return 1 if failed else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", nargs="?")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    try:
        import pymupdf  # noqa: F401
    except ImportError:
        sys.exit("PyMuPDF is needed: pip install pymupdf")
    if args.self_test:
        sys.exit(self_test())
    if not args.pdf:
        ap.error("give a report PDF, or --self-test")
    result = extract(args.pdf)
    print(json.dumps(result, indent=2) if args.json else summarise(result))


if __name__ == "__main__":
    main()
