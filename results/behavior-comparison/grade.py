#!/usr/bin/env python3
"""Mechanical checks for the ilac-report behaviour comparison.

    python3 grade.py <iteration-dir>

Reads <eval>/<config>/run-1/outputs/report.md and writes the mechanical part of
grading.json next to it. Judgement checks (ratio stated as a rule, both
sides argued, one theory only) come from the grader agent and are merged in
when <eval>/<config>/run-1/judgements.json exists.
"""

import json
import re
import sys
from pathlib import Path

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


def sections(text):
    """[(level, title, body_words)] for every markdown heading."""
    out, cur = [], None
    for line in text.splitlines():
        m = HEADING.match(line)
        if m:
            cur = [len(m.group(1)), m.group(2).strip(), 0]
            out.append(cur)
        elif cur is not None:
            cur[2] += len(line.split())
    return out


def subtree_words(secs, i):
    level, total = secs[i][0], secs[i][2]
    for lvl, _, w in secs[i + 1:]:
        if lvl <= level:
            break
        total += w
    return total


def body_words(text):
    """Words before the References heading."""
    cut = re.split(r"^#{1,6}\s+(References|Reference list|Bibliography)\b.*$", text, flags=re.M | re.I)
    return len(cut[0].split())


def issue_statements(text):
    """The sentence that follows each Issue label or heading."""
    found = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        h = HEADING.match(line)
        label = re.match(r"^\s*\*\*(I\d*\s*[—–:-]|Issue\b)[^*]*\*\*[:.]?\s*(.*)$", line)
        if h and re.search(r"\bIssue\b|^I\d*\b|\bI\d+\s*[—–:-]", h.group(2)) and not re.search(r"issues\b", h.group(2), re.I):
            rest = next((l for l in lines[i + 1:] if l.strip()), "")
            found.append(rest)
        elif label:
            found.append(label.group(2) or next((l for l in lines[i + 1:] if l.strip()), ""))
    return found


def law_application_pairs(secs):
    """Pair each Law heading with the next Application heading."""
    pairs, law = [], None
    for i, (lvl, title, _) in enumerate(secs):
        t = title.lower()
        if re.search(r"\blaw\b|^l\d*\b|\bl\d+\s*[—–:-]", t) and "media law" not in t and "case law" not in t:
            law = subtree_words(secs, i)
        elif re.search(r"\bapplication\b|^a\d*\b|\ba\d+\s*[—–:-]", t) and law is not None:
            pairs.append((law, subtree_words(secs, i)))
            law = None
    return pairs


def discussion_share(secs, text):
    total = body_words(text)
    for i, (_, title, _) in enumerate(secs):
        if re.match(r"^(\d+\.?\s*|[ivx]+\.\s*)?(Step 3:\s*)?Discussion\b", title, re.I):
            return subtree_words(secs, i) / max(total, 1)
    return 0.0


def check(name, passed, evidence):
    return {"text": name, "passed": bool(passed), "evidence": evidence}


def grade(eval_name, text):
    secs = sections(text)
    words = body_words(text)
    issues = issue_statements(text)
    pairs = law_application_pairs(secs)
    share = discussion_share(secs, text)
    refs = re.split(r"^#{1,6}\s+(?:References|Reference list)\b.*$", text, flags=re.M | re.I)
    ref_entries = [l for l in refs[-1].splitlines() if l.strip() and not l.startswith("#")] if len(refs) > 1 else []

    out = [
        check("At least two separate ILAC blocks (Law and Application headings)", len(pairs) >= 2,
              f"{len(pairs)} Law/Application pairs found"),
        check("Every Issue is framed as a question (\"Whether ...\" or ends with ?)",
              issues and all(re.search(r"\bwhether\b|\?", s, re.I) for s in issues),
              f"{len(issues)} issue statements; first: {issues[0][:120] if issues else 'none'}"),
        check("Application is longer than Law in every ILAC block",
              pairs and all(a > l for l, a in pairs), f"(law, application) words: {pairs}"),
        check("Discussion has a comparison table with an ICCPR column",
              re.search(r"^\|.*ICCPR.*\|", text, re.M | re.I), "table header row with ICCPR"),
        check("Discussion is 30-45% of the body", 0.30 <= share <= 0.45, f"discussion share {share:.0%}"),
        check("Study-only, not-legal-advice note", re.search(r"not (constitute )?legal advice", text, re.I),
              "regex 'not legal advice'"),
        check("Reference list with at least 6 entries", len(ref_entries) >= 6, f"{len(ref_entries)} entries"),
        check("Status of laws flagged (in force / amended / repealed)",
              re.search(r"\bin force\b", text, re.I) and re.search(r"\b(amend|repeal)", text, re.I),
              "mentions 'in force' and amend/repeal"),
    ]
    if eval_name == "case-report-azmi-sharom":
        out += [
            check("Ratio decidendi and obiter dicta both identified",
                  re.search(r"ratio", text, re.I) and re.search(r"obiter", text, re.I), "ratio + obiter"),
            check("Length 1,800-2,500 words (excluding references)", 1800 <= words <= 2500, f"{words} words"),
        ]
    if eval_name == "incident-report-fahmi-reza":
        out += [
            check("Flags the 2025 amendment to s.233 ('grossly offensive')",
                  re.search(r"grossly offensive", text, re.I), "'grossly offensive'"),
            check("Separates confirmed facts from allegations",
                  re.search(r"\bconfirmed\b", text, re.I) and re.search(r"\balleg", text, re.I), "confirmed + alleg*"),
            check("Has a current-status section", any(re.search(r"status", t, re.I) for _, t, _ in secs),
                  "heading containing 'status'"),
        ]
    if eval_name == "scenario-tiktok-religion-osa":
        out += [
            check("Within the 1,500-word limit (excluding references)", words <= 1500, f"{words} words"),
            check("Applies the Online Safety Act 2025 to TikTok", re.search(r"Online Safety Act 2025", text),
                  "'Online Safety Act 2025'"),
            check("Uses the current s.233 threshold ('grossly offensive')",
                  re.search(r"grossly offensive", text, re.I), "'grossly offensive'"),
        ]
    return out


def main(iteration):
    for report in sorted(Path(iteration).glob("eval-*/*/run-*/outputs/report.md")):
        run_dir = report.parent.parent
        eval_name = run_dir.parent.parent.name[len("eval-"):]
        expectations = grade(eval_name, report.read_text(encoding="utf-8"))
        judged = run_dir / "judgements.json"
        if judged.exists():
            expectations += json.loads(judged.read_text())
        passed = sum(e["passed"] for e in expectations)
        grading = {
            "expectations": expectations,
            "summary": {"passed": passed, "failed": len(expectations) - passed,
                        "total": len(expectations), "pass_rate": round(passed / len(expectations), 2)},
        }
        (run_dir / "grading.json").write_text(json.dumps(grading, indent=2))
        print(f"{eval_name:32} {run_dir.parent.name:10} {passed}/{len(expectations)}")
        for e in expectations:
            if not e["passed"]:
                print(f"    FAIL {e['text']}: {e['evidence']}")


if __name__ == "__main__":
    main(sys.argv[1])
