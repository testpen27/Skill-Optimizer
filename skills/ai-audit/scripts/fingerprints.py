#!/usr/bin/env python3
"""Scan text for AI tool fingerprints, placeholders, and chat wrappers.

These patterns are checkable, unlike the rest of the catalogue, so they are
handled by regex rather than by reading. Missing one by eye is easy: some
markers hide inside Unicode private-use characters, and a tracking parameter
sits at the end of a long URL.

Usage:
    python fingerprints.py FILE
    cat draft.md | python fingerprints.py
    python fingerprints.py --self-test

Findings carry a confidence label:
    fingerprint  the tool's own markup or tracking; no human writes it
    residue      chat wrappers and placeholders; strong, occasionally innocent
"""

import argparse
import re
import sys

# (label, confidence, compiled pattern, note)
PATTERNS = [
    ("OpenAI citation markup", "fingerprint",
     r":contentReference\[oaicite:\d+\]|\{index=\d+\}|cite\s*turn\d+(search|news|image|view)\d+|iturn\d+image\d+|\"attributableIndex\"",
     "ChatGPT rendering-layer markers."),
    ("Gemini citation markup", "fingerprint",
     r"\[cite:\s*\d+(\s*,\s*\d+)*\]|\[span_\d+\]\((start|end)_span\)|\((start|end)_span\)",
     "Gemini citation and span markers."),
    ("Grok markup", "fingerprint",
     r"<grok-card\b|grok_render_citation_card_json",
     "Grok card markup."),
    ("DeepSeek citation markup", "fingerprint",
     r"\u3010\d+\u2020[^\u3011]*\u3011",
     "DeepSeek lenticular-bracket citations."),
    ("Perplexity markup", "fingerprint",
     r"\[(web|attached_file):\d+\]|ppl-ai-file-upload",
     "Perplexity source tags and upload URLs."),
    ("Unclassified writing directive", "fingerprint",
     r":::\s*(writing|\u00e9criture)\{[^}]*\}",
     "Document-variant markers seen since mid-2026."),
    ("Tool tracking parameter", "fingerprint",
     r"utm_source=(openai|chatgpt\.com|copilot\.com)|referrer=grok\.com",
     "Shows the tool found the source. The prose may still be human; check separately."),
    ("Private-use characters", "fingerprint",
     r"[\ue000-\uf8ff]",
     "Invisible glyphs that often wrap hidden citation markers."),
    ("Chat wrapper", "residue",
     r"(?i)\b(i hope this helps|hope this helps!|would you like me to|let me know if you('| wa)nt|is there anything else|here'?s a (draft|summary|rewrite) (of|for) your|certainly!|of course!|great question!|you'?re absolutely right)",
     "Text addressed to whoever ran the prompt."),
    ("Knowledge-gap disclaimer", "residue",
     r"(?i)(as of my (last )?(knowledge|training) (update|cutoff)|up to my last training|while (specific )?details (are|remain) (limited|scarce)|not widely (documented|available|disclosed)|based on (the )?available (information|sources)|in the provided sources)",
     "Often followed by speculation presented as fact. Check the next sentence."),
    ("Unfilled placeholder", "residue",
     r"(?i)\[(your name|insert[^\]]*|describe[^\]]*|add if[^\]]*|company name)\]|INSERT_[A-Z_]+|PASTE_[A-Z_]+|\b\d{4}-XX-XX\b",
     "A fill-in-the-blank slot nobody filled."),
]

COMPILED = [(label, conf, re.compile(pat), note) for label, conf, pat, note in PATTERNS]


def scan(text):
    """Return a list of (line_number, label, confidence, matched_text, note)."""
    findings = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for label, confidence, pattern, note in COMPILED:
            for match in pattern.finditer(line):
                snippet = match.group(0)
                if len(snippet) > 60:
                    snippet = snippet[:57] + "..."
                findings.append((lineno, label, confidence, snippet, note))
    return findings


def report(findings):
    if not findings:
        print("No fingerprints or residue found.")
        print("This rules nothing out: the catalogue's other tells are not checkable by regex.")
        return
    seen_notes = set()
    for lineno, label, confidence, snippet, note in findings:
        print(f"line {lineno}: [{confidence}] {label} -> {snippet!r}")
        if note not in seen_notes:
            print(f"    {note}")
            seen_notes.add(note)
    fps = sum(1 for f in findings if f[2] == "fingerprint")
    print(f"\n{len(findings)} finding(s), {fps} of them tool fingerprints.")
    if fps:
        print("A fingerprint identifies the tool, not the author's intent. Lead the audit with it,")
        print("say which tool, and say what it does and does not establish.")


SELF_TEST_CASES = [
    # (text, expected number of findings, description)
    ("The bridge opened in 1932 and now carries 40,000 vehicles a day.", 0,
     "clean prose"),
    ("Revenue grew 12% :contentReference[oaicite:3]{index=3} last year.", 2,
     "ChatGPT markup (marker plus index)"),
    ("See the report [cite: 4, 12] for detail.", 1, "Gemini citation"),
    ("Source: https://example.com/article?utm_source=chatgpt.com", 1,
     "tracking parameter"),
    ("Certainly! Here's a draft of your article on rail freight.", 2,
     "two chat wrappers in one line"),
    ("While specific details are limited, she likely studied abroad.", 1,
     "knowledge-gap disclaimer"),
    ("Contact [Your Name] before 2026-XX-XX.", 2, "two placeholders"),
    ("The em dash — used well — is not a fingerprint.", 0,
     "weak tells are out of scope for this script"),
    ("The study citeturn0search0 reports the opposite.", 1,
     "citeturn marker"),
    ("Payment is due in order to keep the account open.", 0,
     "human filler must not be flagged"),
]


def self_test():
    failures = 0
    for text, expected, description in SELF_TEST_CASES:
        got = len(scan(text))
        status = "ok" if got == expected else "FAIL"
        if got != expected:
            failures += 1
        print(f"[{status}] {description}: expected {expected}, got {got}")
    print()
    if failures:
        print(f"{failures} case(s) failed.")
        return 1
    print(f"All {len(SELF_TEST_CASES)} cases passed.")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", nargs="?", help="file to scan; omit to read stdin")
    parser.add_argument("--self-test", action="store_true",
                        help="run the built-in test cases")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(self_test())

    if args.file:
        with open(args.file, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    else:
        text = sys.stdin.read()

    report(scan(text))


if __name__ == "__main__":
    main()
