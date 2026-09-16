# Evaluation: `fable-5-logic`

Status: **incomplete, stopped mid-validation.** Read the measurement-reliability
section before using any number here.

## Correction first

An earlier version of this report led with "the skill never triggers -- 0/60."
**That was wrong.** It was an artifact of bugs in the measurement harness. The
best-powered clean run says close to the opposite: the original description
triggers most of the time on judgment-heavy queries, and *also* fires on
mechanical work it should ignore.

## What the harness got wrong

Three real bugs in the skill-creator trigger eval, found by running a control
(an `xlsx`-style description that should obviously trigger) and noticing it
scored zero too. Each one independently reports a healthy skill as 0%:

1. **The skill was registered as a slash command** in `.claude/commands/`. A
   command never reaches the `available_skills` list the model picks from, so
   there was nothing to invoke.
2. **The detector accepted the skill only as the first tool call** of the turn.
   Claude routinely looks around first -- a `Bash ls` to find the file the user
   named -- and invokes the skill a beat later. Those were scored as misses.
3. **Concurrent runs shared one `.claude/skills/` directory.** With N workers,
   every model turn saw N near-identical copies of the skill and would often
   invoke a sibling's copy, whose name did not match the one being watched. This
   is why parallel passes disagreed with serial ones: 0/3 vs 2/2 on the same
   query.

Fixes are in `scripts/trigger_probe.py`: register a real skill, count an
invocation anywhere in the turn, give every run its own project root, run the
turn to completion rather than early-exiting on a stream heuristic, and raise
`ProbeFailure` instead of silently scoring a crashed run as "did not trigger."

## The one measurement worth quoting

Original description, 6 queries x 10 runs, isolated roots, 875s of real model
turns:

| Query | Kind | Triggered |
|---|---|---|
| grant statistic needing a citation | should | 10/10 |
| risky foreign-key shortcut | should | 9/10 |
| grief, hard personal news | should | 3/10 |
| rename a variable across src/ | should NOT | 2/10 |
| build a bar chart | should NOT | 3/3 (7 runs failed) |
| add a ruff pre-commit hook | should NOT | 0/10 |

**Recall 22/30 (73%). False fires 5/23 (22%).**

So the real shape of the problem is not that the skill is invisible. It is that
it fires unevenly: near-perfectly where a claim is about to be asserted,
rarely on emotional messages (3/10, where the skill's wording guidance matters
most), and too often on mechanical work where it is pure context cost.

## Numbers you should not trust

Any pass that finished suspiciously fast. Real turns take 30-45s each; a
60-run pass should take ~10 minutes at 4 workers. Two passes returned in 29s
and 65s with zero reported failures and all-zero triggers. That is the same
signature as the bug in fix #2 above, and it is unexplained. Every "rewritten
description scores X" figure in this session came from such a pass, so the
rewritten description is **unvalidated** -- it is not known to be better or
worse than the original.

Sample size is the other problem. At 3 runs per query, borderline queries land
2/2 one way and 0/2 the other purely by chance; triggering on them is close to
a coin flip. The skill-creator default of 3 runs is under-powered here. Ten runs
per query is the minimum that separated signal from noise, which costs roughly
15 minutes per description on this box.

## Changes made to the skill (independent of measurement)

These are defensible on inspection and do not depend on any trigger number:

- **Progressive disclosure.** The body was ~2,200 words and loaded in full on
  every trigger. The stakes-gated epistemics moved to `references/rigor.md`;
  SKILL.md keeps the register rules that always apply. The description's claim
  that it "costs nothing on light messages" was not true -- the gating governed
  behavior, not loading -- and that claim is gone.
- **Removed the hardcoded cutoff.** The body asserted "reliable knowledge ends
  around mid-2026," a remembered fact stated as current, which is the exact
  failure the skill spends a section warning against. It now says to check the
  current date against your own cutoff.
- **Description rewritten** to promise the contents (checklist, calibration
  ladder, answer-shape patterns) and name concrete trigger conditions. Untested,
  per above.

## Where to pick this up

1. Re-run the powered comparison (10 runs/query, isolated roots) for the
   original and rewritten descriptions, and find out why fast-and-empty passes
   happen before trusting either result.
2. The 22% false-fire rate on the original is the clearest defect worth fixing,
   and the 3/10 on emotional messages the clearest gap.
3. The standing recommendation is unchanged and does not depend on any of this:
   content that should apply to *every* response belongs in `CLAUDE.md`, an
   output style, or `--append-system-prompt`, where it is always in context and
   no trigger decision can drop it. A skill is pull-based by construction.
