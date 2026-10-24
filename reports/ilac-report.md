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

The three tasks were rerun with the revised skill after the word-budget
change (mechanical checks only; no blind grading this round). Viewer:
`results/behavior-comparison/review-iteration-2.html`.

| Task | Iteration 1 (mechanical) | Iteration 2 (mechanical) |
|---|---|---|
| Case report, Azmi Sharom | 9/10 (Discussion 26%) | 9/10 (Discussion 29%, body ~2,020 words) |
| Incident report, Fahmi Reza | 10/11 (Discussion 26%) | 9/11 (Discussion 25%; ~3,300 words; no heading named "current status", though section 3 gives the position as checked) |
| TikTok scenario | 8/11 (1,543 words; Law longer than Application) | 11/11 (~1,420 words; Application longer than Law in every block; Discussion 35%) |
| Total | 27/32 | 29/32 |

The word limit and the Law/Application balance are fixed. The Discussion
share is still under target in the two longer reports: the case-report run
said it held the Discussion at about 600 words to keep the 2,000 total, i.e.
it cut the Discussion rather than the ILAC blocks. SKILL.md now says to cut
Law and background first, not the Discussion.

### Iteration 3 (case report only, after the cut-order sentence)

The case-report task was rerun once more with the current skill
(`results/behavior-comparison/iteration-3/`). 10/10 on the mechanical checks:
1,952 words excluding references, Discussion 35% (about 700 words, up from
26% and 29%), Application longer than Law in all three blocks (153/75,
130/58, 182/77 words). This run also read the full judgment text (a CLJ copy)
and quoted the court directly. One point a marker might query: it calls the
departure from *Sivarasa* "arguably obiter", reasoning that the case would
have ended the same way had *Sivarasa* stood; that is a defensible reading
but contestable, and the report flags it as such. The incident-report task,
where the Discussion was also short, was not rerun. The incident report had no length set by the user and ran well over
the 2,200-word default.

Notable in the reruns: all three found and used the Federal Court's 2026
*Heidy Quah* ruling from the updated status file, and the case report now
names a ratio as a rule, distinguishes *Nordin Salleh*, and traces later
treatment (*Mat Shuhaimi*).

## 5. Trigger accuracy (description optimizer)

Harness: `scripts/run_loop_resilient.py` with the corrected probe, real
`claude -p` turns on Sonnet 5.5 (the model the session is advised to run on),
rewrites on Opus 5.5, user-level skills excluded (`PROBE_SETTING_SOURCES=project`;
the account syncs an older copy of this skill), and nine synced skills copied
in as competitors (`deep-research`, `docx`, `pdf`, `pptx`, `xlsx`, `learn`,
`docs`, `firecrawl`, `pre-research`). Control first: an obviously matching
description fired 2/2 on a clear positive and 0/2 on a clear negative.

**Eval set** (`evals/trigger-eval.json`): 22 queries, 10 positive (case
reports, incident reports, a lecturer's scenario, a comparative report) and
12 near-miss negatives (legal advice to a worried friend, a literature
review, a news summary, a letter of demand, IRAC-vs-CREAC explainer, fixing
references only, a Hallin & Mancini essay, slides from a finished report, a
contract-law problem question, an Excel timeline, a news article on a
judgment, a status question). 3 runs per query (lowered from 5 after two
runs were cut off by the account's usage limit).

| Description | Train (14) | Held-out (8) |
|---|---|---|
| Original (kept) | 14/14 (42/42 runs) | 8/8 (24/24 runs) |

Every run was correct, so the optimizer stopped after one iteration and
proposed no change (`results/description-optimization/2026-10-23_181429/`).

**Fresh hard hold-out** (`evals/trigger-holdout.json`, 12 queries never seen by
the optimizer, 3 runs each, `results/holdout-original.json`): positives that
avoid "ILAC" and the course code (a case comment on *Heidy Quah*; "identify
each legal issue, state the law, apply it"; a request in Malay; a deepfake
tutorial hypothetical) and near-misses (an IRAC brief for a tort case, a
policy brief on s. 233, an NGO summary, a ratio/obiter explainer, an exam
timetable, translating a finished report). 12/12, every run unanimous.

The description stays as the owner wrote it. Its precision comes from naming
the deliverable (a case or incident report in ILAC with a comparative
Discussion) and the domain (media law); a "pushier" rewrite would risk
pulling in the IRAC-for-tort and policy-brief near-misses, which it
currently rejects. The probe sees only name and description, so the rename
was in place for both trigger runs.

## 6. Limits

- One run per task per version: this shows differences exist, not how often.
- Trigger runs used 3 runs per query, below the README's 10; with every run
  unanimous the margin is wide, but borderline wording was not stress-tested.
- Several test runs could not open the judgments (WebFetch DNS failures,
  Firecrawl rate limits) and worked from law reports or summaries; the blind
  grader noticed the difference this made.
- The Heidy Quah reasoning in the status file comes from law-firm summaries;
  the file says to read the judgment before relying on it.
- The model routing has not been exercised.
- Scope: ILAC tasks outside media law (e.g. a contract-law tutorial problem)
  are treated as out of scope in the trigger eval set. If the owner wants the
  skill for any ILAC assignment, the description and the negatives change.

## 7. Packaging

`dist/ilac-report.skill` (SKILL.md and both reference files), built with
skill-creator's `package_skill.py`. The owner's upload also carried a
`.claude-plugin/plugin.json` naming `ilac-legal-report`
(`evals/original-plugin.json`); if the skill is distributed as a plugin, that
name needs changing to `ilac-report` too. The account still syncs the old
`ilac-legal-report`; installing the new one alongside it would put two
competing skills in front of Claude, so remove the old one when installing.
