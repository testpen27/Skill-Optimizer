# ilac-report

The owner's `ilac-legal-report` skill (COM741 Media Law), renamed `ilac-report`
at the owner's request, revised from research on how ILAC is taught and
assessed, behaviour-tested against the original with skill-creator, given a
per-step model plan, and put through the description optimizer.

Original files: `evals/original-SKILL.md`, `evals/original-plugin.json`.

## 1. Research: how ILAC is done in academic work

Sources: Southern Cross University's IRAC/ILAC quick guide; RMIT Learning
Lab, "Writing case notes"; York St John's case note fact sheet; Columbia Law's
IRAC/CRAC/CREAC handout; University of London exam FAQs; Thilakarathna and
Mathotaarachchi (2025) on doctrinal legal research.

What changed the skill:

- ILAC is IRAC with "Law" for "Rule"; same method.
- Weak answers fail on a thin Application, not on the Law. Application should
  be the heaviest part, and should reason from precedent ("Similar to... /
  Unlike...") as well as from the statute.
- One ILAC per discrete issue; sub-issues under subheadings; several parties
  each get their own Law, Application and short conclusion.
- Issue spotting: list the parties and acts, then ask which fact has not been
  used.
- Case notes: the ratio is a rule, not the order ("appeal dismissed" is not a
  ratio); test obiter by asking whether the case would have been decided the
  same way without the passage; read the judgment, not the headnote; check
  how later cases treated it.
- ILAC is doctrinal ("law in the books"). The literature pairs it with
  socio-legal analysis ("law in action"), which is the role the skill's
  Discussion already played; the report now says so.
- The brief, rubric and word count govern.

Status checks of the Malaysian laws the skill cites (CMA amendment in force
11 Feb 2025 with "grossly offensive"; Online Safety Act 2025 in force 1 Jan
2026; Malaysian Media Council Act 2025 in force 14 Jun 2025; the Federal
Court's 6 Feb 2026 *Heidy Quah* ruling upholding s. 233(1)(a)) went into
`references/malaysia-law-status.md`, dated, with the instruction to confirm
anything after that date.

## 2. Changes to the skill

- **Name:** `ilac-legal-report` became `ilac-report` (frontmatter, folder,
  package).
- **SKILL.md body:** ILAC framed as doctrinal with the Discussion as law in
  action; Step 0 (the brief overrides the defaults; set a word budget; a word
  limit is a ceiling on everything but references); issue-spotting check;
  read the judgment and its later treatment; Application weighted heaviest,
  with precedent analogy; ratio/obiter tests; s. 233 example updated to
  "grossly offensive"; checklist items for Law/Application balance and word
  count. Structure, modes, Discussion method and style rules are the owner's,
  unchanged.
- **`references/malaysia-law-status.md`:** dated status snapshot with sources.
- **`references/model-routing.md`:** which model runs each step (below).

## 3. Model routing

| Step | Model |
|---|---|
| Brief, mode, delivery | Session |
| Issue spotting | Helper, Opus |
| Status of each law cited | Helpers, Haiku, one per law (conflicts to Sonnet) |
| Reading the judgment / incident sources | Helper, Sonnet |
| Comparator jurisdictions | Helpers, Sonnet, one per country |
| Drafting ILAC blocks and Discussion | Helper, Opus |
| Citation check | Helpers, Haiku, ~10 citations each |
| APA 7 formatting | Helper, Haiku |
| Final checklist review | Helper, Sonnet |

Session on Sonnet is enough. The owner can override any step; Claude only
proposes moving a step to a stronger model, and asks first. On claude.ai on
the web there are no helpers, so every step runs on the chat model. The
routing itself was not exercised in testing (the test runs were told to do
every step themselves, to keep the comparison with the original fair).

## 4. Behaviour test (skill-creator)

Three tasks (`evals/evals.json`), each run once with the revised skill and
once with the original, by independent Sonnet subagents with web access:
a case report on *PP v Azmi Sharom* [2015] 6 MLJ 751 (FC); an incident report
on Fahmi Reza's s. 233 prosecution; a lecturer's TikTok/religion scenario with
a 1,500-word cap and a one-theory rule. Grading: `results/behavior-comparison/
grade.py` (mechanical checks) plus a blind grader that saw the reports as A/B
without knowing which skill wrote which (`iteration-1/blind-grader-verdicts.json`).
Viewer: `results/behavior-comparison/review-iteration-1.html`.

### Iteration 1

| Task | Original | Revised | Blind grader preferred |
|---|---|---|---|
| Case report, Azmi Sharom | 17/18 | 17/18 | Revised |
| Incident report, Fahmi Reza | 17/19 | 18/19 | Revised (close) |
| TikTok scenario | 18/20 | 17/20 | Revised |
| Total | 52/57 (91%) | 52/57 (91%) | |

Time and tokens per report: original 220 s / 130k, revised 263 s / 155k.

The checks did not separate the versions; the blind reading did. The grader
preferred the revised reports for reading the judgment itself (paragraph
cites) and stating the ratio as a rule apart from the order (task 1), for a
"comparison with decided cases" passage and a clear answer on how a similar
caricature would fare today (task 2), and for spotting the s. 298A threshold
problem (*Mamat Daud*, *Alvivi*) that the original missed (task 3). The
original's one clear win was a better-fitting single theory in task 3.

Where the revised skill lost marks: its Discussion was 26-30% of the body in
all three runs (target 35-40%), and the scenario ran 1,543 words against a
1,500 cap. Fix: a word budget set before drafting, the cap counted on
everything but references, and checklist items to count Law against
Application and the total.

A grader bug found on the way: the first pass only recognised Law and
Application as headings, but every report used bold run-in labels, so it
failed all six on structure. Fixed before the scores above.

### Iteration 2 (revised skill with the word-budget fix)

ITERATION2_PLACEHOLDER

## 5. Trigger accuracy (description optimizer)

TRIGGER_PLACEHOLDER

## 6. Limits

- One run per task per version: this shows differences exist, not how often.
- Several test runs could not open the judgments (WebFetch DNS failures,
  Firecrawl rate limits) and worked from law reports or summaries; the blind
  grader noticed the difference this made.
- The Heidy Quah reasoning in the status file comes from law-firm summaries;
  the file says to read the judgment before relying on it.
- The model routing has not been exercised.
- Scope: ILAC tasks outside media law (e.g. a contract-law tutorial problem)
  are treated as out of scope in the trigger eval set. If the owner wants the
  skill for any ILAC assignment, the description and the negatives change.
